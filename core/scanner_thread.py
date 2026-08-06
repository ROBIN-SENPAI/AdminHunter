import re
import time
import sys
import random
import urllib3
import requests
from threading import Thread, Lock, Event
from queue import Queue, Empty
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.waf import get_advanced_headers
from utils.ui import log_found, Colors

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────── DETECTION RULES ───────────────────────────
# Strong signals (high score) → the page is almost certainly a login/admin panel.
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

ADMIN_THRESHOLD = 4  # minimum score before a page is classified as an admin panel


class Scanner:
    def __init__(self, target, paths, threads=30, timeout=10, stop_on_found=True,
                 proxy=None, delay=0.0):
        self.target = target
        self.paths = paths
        self.threads_count = max(1, threads)
        self.timeout = timeout
        self.stop_on_found = stop_on_found
        self.proxy = proxy
        self.delay = max(0.0, delay)

        self.q = Queue()
        for p in paths:
            self.q.put(p)

        self.total_paths = len(paths)
        self.stats = {
            'total_requests': 0,
            'found_panels': 0,
            'sensitive_files': 0,
            'failed': 0
        }
        self.stats_lock = Lock()
        self.stop_event = Event()
        self.results = []
        self.results_lock = Lock()
        self.current_path = ""
        self.baseline = None  # (content_length, content_lowercase) of the root page

        self.session = self._build_session()
        self._fetch_baseline()

    # ─────────────────────────── SETUP ───────────────────────────

    def _build_session(self):
        session = requests.Session()
        retries = Retry(total=1, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=self.threads_count,
                              max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        if self.proxy:
            session.proxies = {"http": self.proxy, "https": self.proxy}
        return session

    def _fetch_baseline(self):
        """Fetch the root page once and remember its shape to detect soft 404s."""
        try:
            response = self.session.get(self.target, headers=get_advanced_headers(),
                                        timeout=self.timeout, verify=False,
                                        allow_redirects=True)
            text = response.text.lower()
            self.baseline = (len(text), text)
        except Exception:
            self.baseline = None

    # ─────────────────────────── DETECTION ───────────────────────────

    @staticmethod
    def extract_title(html):
        title = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return title.group(1).strip()[:80] if title else "N/A"

    def is_soft_404(self, response):
        text = response.text.lower()
        if len(text) < 200 and any(k in text for k in ('not found', '404', "doesn't exist", 'does not exist')):
            return True
        title = self.extract_title(response.text).lower()
        if '404' in title or 'not found' in title:
            return True
        if self.baseline:
            base_len, base_text = self.baseline
            # Same body as the root page → custom 404 page, or near-identical size
            if text == base_text:
                return True
            if base_len > 0 and abs(len(text) - base_len) / base_len < 0.02:
                return True
        return False

    def score_admin_page(self, response):
        """Return (score, reasons) based on page title, content, and final URL."""
        score = 0
        reasons = []
        title = self.extract_title(response.text).lower()
        content = response.text.lower()
        final_url = response.url.lower()

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

    # ─────────────────────────── WORKER ───────────────────────────

    def worker(self):
        while not self.stop_event.is_set():
            try:
                path = self.q.get_nowait()
            except Empty:
                break

            self.current_path = path
            url = urljoin(self.target, path)

            if self.delay > 0:
                time.sleep(random.uniform(self.delay * 0.5, self.delay * 1.5))

            try:
                response = self.session.get(url, headers=get_advanced_headers(),
                                            timeout=self.timeout, verify=False,
                                            allow_redirects=True)

                with self.stats_lock:
                    self.stats['total_requests'] += 1

                if response.status_code == 200 and not self.is_soft_404(response):
                    is_sensitive = any(ext in url for ext in SENSITIVE_EXTS)

                    if is_sensitive:
                        type_label = "SENSITIVE"
                        score, reasons = 0, []
                    else:
                        score, reasons = self.score_admin_page(response)
                        type_label = "ADMIN" if score >= ADMIN_THRESHOLD else None

                    if type_label:
                        title = self.extract_title(response.text)
                        log_found(url, response.status_code, type_label, title)
                        result = {
                            'url': url,
                            'code': response.status_code,
                            'type': type_label,
                            'title': title,
                            'score': score,
                            'reasons': reasons
                        }
                        with self.results_lock:
                            self.results.append(result)
                        with self.stats_lock:
                            if type_label == "ADMIN":
                                self.stats['found_panels'] += 1
                            else:
                                self.stats['sensitive_files'] += 1

                        if type_label == "ADMIN" and self.stop_on_found:
                            self.stop_event.set()

            except Exception:
                with self.stats_lock:
                    self.stats['failed'] += 1
            finally:
                self.q.task_done()

    # ─────────────────────────── RUN ───────────────────────────

    def run(self):
        threads = []
        for _ in range(self.threads_count):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)

        try:
            while any(t.is_alive() for t in threads) and not self.stop_event.is_set():
                with self.stats_lock:
                    progress = (self.stats['total_requests'] / self.total_paths) * 100 if self.total_paths > 0 else 0
                    bar_len = 30
                    filled_len = int(bar_len * progress / 100)
                    bar = '█' * filled_len + '░' * (bar_len - filled_len)

                    sys.stdout.write(f"\r{Colors.BOLD}{Colors.CYAN}[SCANNING] {Colors.WHITE}|{bar}| {progress:.1f}% {Colors.YELLOW}Testing: {Colors.GRAY}{self.current_path[:30].ljust(30)}{Colors.RESET}")
                    sys.stdout.flush()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_event.set()

        sys.stdout.write("\n")
        sys.stdout.flush()
        return self.results
