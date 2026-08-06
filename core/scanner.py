import asyncio
import random
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import aiohttp
from utils.waf import get_advanced_headers
from utils.ui import log_found, Colors
from core.spider import extract_from_html, extract_from_js, is_skippable
from core.secrets import scan_secrets

# ─────────────────────────── DETECTION RULES ───────────────────────────
STRONG_TITLE_KEYS = ['login', 'log in', 'sign in', 'signin', 'admin panel', 'control panel',
                     'administrator', 'authentication', 'authorization', 'dashboard', 'cpanel', 'plesk']
WEAK_TITLE_KEYS = ['admin', 'panel']
STRONG_URL_KEYS = ['/login', '/signin', '/sign-in', '/log-in', '/auth', '/wp-login',
                   '/admin', '/dashboard', '/controlpanel', '/user/login', '/administrator']
FORM_HINTS = ['type="password"', "type='password'", 'type="submit"', 'name="username"',
              "name='username'", 'name="user"', 'name="login"', 'name="email"', 'name="pass"']
BODY_HINTS = ['forgot password', 'forgot your password', 'remember me', 'create an account',
              'sign in to continue', 'enter your password']

SENSITIVE_EXTS = ['.env', '.git', '.sql', '.zip', '.bak', 'config.php', 'phpinfo.php',
                  '.htaccess', '.htpasswd', '.log', '.json', '.yml', '.yaml', '.bak.php']

ADMIN_THRESHOLD = 4      # minimum score before a page is classified as an admin panel
MAX_RETRIES = 2          # retry attempts for transient failures / 429 / 5xx
BACKOFF = 1.0            # base backoff seconds (doubles per attempt)
MAX_TIMEOUT = 30.0       # adaptive timeout ceiling


class Scanner:
    def __init__(self, target, paths, concurrency=50, timeout=10, stop_on_found=True,
                 proxy=None, proxies=None, delay=0.0, recursive=False, max_depth=2,
                 extract_links=True, max_js=10):
        self.target = target.rstrip('/')
        self.paths = paths
        self.concurrency = max(1, concurrency)
        self.timeout = max(1.0, float(timeout))
        self.stop_on_found = stop_on_found
        self.delay = max(0.0, delay)
        self.recursive = recursive
        self.max_depth = max(1, max_depth)
        self.extract_links = extract_links
        self.max_js = max(0, max_js)

        if proxies:
            self.proxies = [p if '://' in p else f'http://{p}' for p in proxies]
        elif proxy:
            self.proxies = [proxy if '://' in proxy else f'http://{proxy}']
        else:
            self.proxies = []
        self._proxy_idx = 0
        self._bad_proxies = set()

        self.q = asyncio.Queue()
        self._seen = set()          # (path, depth) deduplication
        self._recurse_dirs = set()  # (dir_url, depth) deduplication
        self.total_paths = 0
        for p in paths:
            self._enqueue(p, 0)
        self.started_at = time.time()
        self.stats = {
            'total_requests': 0,
            'found_panels': 0,
            'sensitive_files': 0,
            'auth': 0,
            'secrets': 0,
            'failed': 0,
            'retries': 0
        }
        self.stop_event = asyncio.Event()
        self.results = []
        self.current_path = ""
        self._secret_seen = set()  # (url, secret_type, value) deduplication
        self.baseline = None          # (content_length, content_lowercase, title_lowercase) of the root page
        self.semaphore = None         # created in run()

    # ─────────────────────────── QUEUE HELPERS ───────────────────────────

    def _enqueue(self, path, depth):
        if not path or path == '/' or is_skippable(path):
            return
        key = (path, depth)
        if key in self._seen:
            return
        self._seen.add(key)
        self.q.put_nowait(key)
        self.total_paths += 1

    def _enqueue_path_from_url(self, url, depth):
        """Convert an absolute URL into a same-host scan path and enqueue it."""
        try:
            parsed = urlparse(url)
            host = urlparse(self.target).hostname
            if parsed.hostname and host and parsed.hostname.lower() != host.lower():
                return  # external link
            self._enqueue(parsed.path, depth)
        except Exception:
            pass

    def _recurse_into(self, dir_url, depth):
        """Enqueue the wordlist under a discovered directory (once per depth)."""
        key = (dir_url, depth)
        if key in self._recurse_dirs:
            return
        self._recurse_dirs.add(key)
        for p in self.paths:
            self._enqueue(urljoin(dir_url, p), depth + 1)

    # ─────────────────────────── SECRETS ───────────────────────────

    def _scan_for_secrets(self, url, body):
        """Scan a fetched body for credentials/keys and report them live."""
        if not body or self.is_soft_404(body):
            return
        for s in scan_secrets(body, url):
            key = (url, s['secret_type'], s['value'])
            if key in self._secret_seen:
                continue
            self._secret_seen.add(key)
            self.stats['secrets'] += 1
            log_found(url, 200, "SECRET", title=s['secret_type'],
                      details=[('Value', s['value']), ('Context', s['context'])])
            self.results.append({
                'url': url,
                'code': 200,
                'type': 'SECRET',
                'title': s['secret_type'],
                'score': 0,
                'reasons': [],
                'secret_type': s['secret_type'],
                'value': s['value'],
                'context': s['context'],
            })

    # ─────────────────────────── DETECTION ───────────────────────────

    @staticmethod
    def extract_title(html):
        title = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return title.group(1).strip()[:80] if title else "N/A"

    def is_soft_404(self, body):
        text = body.lower()
        if len(text) < 200 and any(k in text for k in ('not found', '404', "doesn't exist", 'does not exist')):
            return True
        title = self.extract_title(body).lower()
        if '404' in title or 'not found' in title:
            return True
        if self.baseline:
            base_len, base_text, base_title = self.baseline
            if text == base_text:
                return True
            # Similar length AND the same title as the root page → likely a custom 404
            if title == base_title and base_len > 0 and abs(len(text) - base_len) / base_len < 0.15:
                return True
        return False

    def score_admin_page(self, final_url, body):
        """Return (score, reasons) based on page title, content, and final URL."""
        score = 0
        reasons = []
        title = self.extract_title(body).lower()
        content = body.lower()
        final_url = final_url.lower()

        if any(k in title for k in STRONG_TITLE_KEYS):
            score += 3
            reasons.append(f"title: {title}")
        elif any(k in title for k in WEAK_TITLE_KEYS):
            score += 1

        if any(k in content for k in ('type="password"', "type='password'")):
            score += 4
            reasons.append("password field")
        if any(k in content for k in FORM_HINTS):
            score += 1
            reasons.append("login form")
        if any(k in content for k in BODY_HINTS):
            score += 1
            reasons.append("auth hints")
        if any(k in final_url for k in STRONG_URL_KEYS):
            score += 2
            reasons.append(f"url: {final_url}")

        return score, reasons

    def _is_directory(self, url, final_url, path):
        if path.endswith('/'):
            return True
        return final_url != url and final_url.rstrip('/').endswith('/')

    def _classify(self, url, path, depth, final_url, status, body, auth_scheme):
        if status == 401:
            type_label = "AUTH"
            score, reasons = 0, []
            self.stats['auth'] += 1
            extra = {'auth': auth_scheme or 'unknown'}
            title = self.extract_title(body)
        elif status == 200 and not self.is_soft_404(body):
            is_sensitive = any(ext in url for ext in SENSITIVE_EXTS)
            if is_sensitive:
                type_label = "SENSITIVE"
                score, reasons, extra = 0, [], {}
            else:
                score, reasons = self.score_admin_page(final_url, body)
                if score < ADMIN_THRESHOLD:
                    return
                type_label = "ADMIN"
                extra = {}
            title = self.extract_title(body)
        else:
            return

        log_found(url, status, type_label, title, reasons, score)
        self.results.append({
            'url': url,
            'code': status,
            'type': type_label,
            'title': title,
            'score': score if type_label != "AUTH" else 0,
            'reasons': reasons if type_label != "AUTH" else [],
            **extra
        })

        if type_label == "ADMIN":
            self.stats['found_panels'] += 1
            if self.stop_on_found:
                self.stop_event.set()
        elif type_label == "SENSITIVE":
            self.stats['sensitive_files'] += 1

    # ─────────────────────────── NETWORKING ───────────────────────────

    def _next_proxy(self):
        live = [p for p in self.proxies if p not in self._bad_proxies]
        if not live:
            return None
        proxy = live[self._proxy_idx % len(live)]
        self._proxy_idx += 1
        return proxy

    async def _fetch_baseline(self, session):
        try:
            async with session.get(self.target, headers=get_advanced_headers(),
                                   timeout=aiohttp.ClientTimeout(total=self.timeout),
                                   ssl=False) as resp:
                text = (await resp.text(errors='replace')).lower()
                self.baseline = (len(text), text, self.extract_title(text).lower())
        except Exception:
            self.baseline = None

    async def _discover(self, session):
        """Spider the root page: extract links, then crawl a few JS files for endpoints."""
        if not self.extract_links or not self.baseline:
            return
        try:
            async with session.get(self.target, headers=get_advanced_headers(),
                                   timeout=aiohttp.ClientTimeout(total=self.timeout),
                                   ssl=False) as resp:
                html = await resp.text(errors='replace')
        except Exception:
            return

        self._scan_for_secrets(self.target, html)
        urls = extract_from_html(html, self.target)
        js_urls = [u for u in urls if u.lower().endswith('.js')][:self.max_js]
        for u in urls:
            if not is_skippable(u):
                self._enqueue_path_from_url(u, 1)

        for js_url in js_urls:
            try:
                async with session.get(js_url, headers=get_advanced_headers(),
                                       timeout=aiohttp.ClientTimeout(total=self.timeout),
                                       ssl=False) as resp:
                    js = await resp.text(errors='replace')
                self._scan_for_secrets(js_url, js)
                for u in extract_from_js(js, js_url):
                    if not is_skippable(u):
                        self._enqueue_path_from_url(u, 1)
            except Exception:
                continue

    async def _request(self, session, url):
        """GET with retries, proxy failover, and adaptive timeout.

        Returns (status, final_url, body, auth_scheme).
        """
        headers = get_advanced_headers()
        proxy = self._next_proxy()

        for attempt in range(MAX_RETRIES + 1):
            try:
                async with session.get(url, headers=headers, ssl=False,
                                       timeout=aiohttp.ClientTimeout(total=self.timeout),
                                       proxy=proxy) as resp:
                    body = await resp.text(errors='replace')
                    status = resp.status
                    final_url = str(resp.url)
                    auth = resp.headers.get('WWW-Authenticate', '').split(' ', 1)[0]

                    if status == 429 or status >= 500:
                        if attempt < MAX_RETRIES:
                            self.stats['retries'] += 1
                            await asyncio.sleep(BACKOFF * (2 ** attempt))
                            continue
                    return status, final_url, body, auth

            except asyncio.TimeoutError:
                self.timeout = min(self.timeout * 1.5, MAX_TIMEOUT)
                if attempt < MAX_RETRIES:
                    self.stats['retries'] += 1
                    await asyncio.sleep(BACKOFF * (2 ** attempt))
                    continue
                raise

            except aiohttp.ClientError:
                if proxy:
                    self._bad_proxies.add(proxy)
                    proxy = self._next_proxy()
                if attempt < MAX_RETRIES:
                    self.stats['retries'] += 1
                    await asyncio.sleep(BACKOFF * (2 ** attempt))
                    continue
                raise

        return None

    async def _worker(self, session):
        while not self.stop_event.is_set():
            try:
                path, depth = self.q.get_nowait()
            except asyncio.QueueEmpty:
                return

            self.current_path = path
            async with self.semaphore:
                if self.delay > 0:
                    await asyncio.sleep(random.uniform(self.delay * 0.5, self.delay * 1.5))

                url = urljoin(self.target, path)
                self.stats['total_requests'] += 1
                try:
                    status, final_url, body, auth = await self._request(session, url)
                    self._classify(url, path, depth, final_url, status, body, auth)
                    if status == 200:
                        self._scan_for_secrets(url, body)

                    # Recursive scan of discovered directories (independent of classification)
                    if (self.recursive and depth < self.max_depth and status == 200
                            and not self.is_soft_404(body) and self._is_directory(url, final_url, path)):
                        self._recurse_into(final_url if final_url.rstrip('/').endswith('/') else url, depth)
                except Exception:
                    self.stats['failed'] += 1
            self.q.task_done()

    # ─────────────────────────── PROGRESS ───────────────────────────

    async def _progress_loop(self):
        try:
            while True:
                elapsed = time.time() - self.started_at
                done = self.stats['total_requests']
                remaining = max(0, self.total_paths - done)
                rate = done / elapsed if elapsed > 0 else 0
                eta = remaining / rate if rate > 0 else 0
                progress = (done / self.total_paths) * 100 if self.total_paths > 0 else 0

                bar_len = 30
                filled = int(bar_len * progress / 100)
                bar = '█' * filled + '░' * (bar_len - filled)
                eta_str = time.strftime('%H:%M:%S', time.gmtime(eta))
                elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
                found = (self.stats['found_panels'] + self.stats['sensitive_files']
                         + self.stats['auth'] + self.stats['secrets'])

                sys.stdout.write(
                    f"\r{Colors.BOLD}{Colors.CYAN}[SCANNING]{Colors.RESET} {Colors.WHITE}|{bar}| "
                    f"{Colors.BOLD}{progress:5.1f}%{Colors.RESET} "
                    f"{Colors.YELLOW}{rate:5.0f} req/s{Colors.RESET} "
                    f"{Colors.WHITE}ETA{Colors.RESET} {Colors.CYAN}{eta_str}{Colors.RESET} "
                    f"{Colors.GRAY}Elapsed {elapsed_str}{Colors.RESET} "
                    f"{Colors.GREEN}Found: {found}{Colors.RESET} "
                    f"{Colors.GRAY}{self.current_path[:24]}{Colors.RESET}")
                sys.stdout.flush()
                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            pass

    # ─────────────────────────── RUN ───────────────────────────

    async def _run_async(self):
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=self.concurrency,
                                         ttl_dns_cache=300, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            await self._fetch_baseline(session)
            await self._discover(session)
            self.semaphore = asyncio.Semaphore(self.concurrency)

            workers = [asyncio.create_task(self._worker(session)) for _ in range(self.concurrency)]
            progress = asyncio.create_task(self._progress_loop())

            try:
                await asyncio.gather(*workers)
            except (KeyboardInterrupt, asyncio.CancelledError):
                self.stop_event.set()
                for w in workers:
                    w.cancel()
            finally:
                progress.cancel()
                sys.stdout.write("\n")
                sys.stdout.flush()

        return self.results

    def run(self):
        return asyncio.run(self._run_async())
