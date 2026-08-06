# AdminHunter Elite Pro v5.0 - Enhanced Architecture

## 1. Modular Structure
- `main.py`: Entry point, argument parsing, and UI initialization.
- `core/scanner.py`: **Async engine** (asyncio + aiohttp) with connection pooling, retries, proxy failover, scoring-based detection, recursion, and endpoint discovery.
- `core/scanner_thread.py`: Previous threaded engine, kept as a fallback/backup.
- `core/recon.py`: Initial server fingerprinting and technology detection.
- `core/spider.py`: Link/endpoint extraction from HTML, CSS, and JavaScript (phase 3).
- `core/secrets.py`: Credential detection patterns with trigger pre-filter (phase 5).
- `utils/waf.py`: Sophisticated header and User-Agent rotation for WAF evasion.
- `utils/ui.py`: Professional terminal interface components.
- `utils/logger.py`: Result logging and export (JSON/TXT/HTML).
- `tests/`: pytest suite (spider, detection, recon, secrets, logger, end-to-end).

## 2. Key Enhancements
### A. Advanced Detection Logic
- **Scoring System**: Page title, password fields, login forms, auth hints, and final URL each add points; only pages scoring `>= 4` are classified as admin panels.
- **Soft 404 Detection**: Compares against the root page baseline (content and length) to filter false positives.
- **Sensitive Files**: `.env`, `.git`, `.sql`, `.zip`, `.bak`, `phpinfo.php`, `.htaccess`, etc.
- **Auth Detection**: HTTP 401 responses are reported as `AUTH` endpoints with their `WWW-Authenticate` scheme.

### B. Performance (Phase 2 - Async Engine)
- **Asyncio + aiohttp**: One event loop handles hundreds of concurrent requests instead of OS threads.
- **Semaphore**: Configurable concurrency cap (default 50) to protect both the scanner and the target.
- **Connection Pooling**: `TCPConnector` with per-host limits and a 5-minute DNS cache.
- **Smart Retries**: Exponential backoff on `429`/`5xx` and network errors (up to 2 retries).
- **Adaptive Timeout**: Timeouts self-raise (up to 30s) on slow networks instead of failing.
- **Rate Limiting**: `--delay` with randomized jitter between requests.
- **Proxy Pool**: `--proxies` file rotates proxies round-robin; failed proxies are blacklisted for the session.
- **Live Metrics**: Progress bar shows requests/second and ETA.

### C. Intelligence (Phase 3)
- **Technology-Aware Wordlists**: `data/tech/*.txt` loaded per detected platform (WordPress, Laravel, Django, Drupal, Joomla, ASP.NET) and scanned first.
- **Endpoint Discovery**: Extracts `src`/`href`/`action` links and CSS `url()` from the root page, then crawls up to 10 JS files extracting API/path strings.
- **Recursive Scanning**: `--recursive` re-scans discovered directories (trailing-slash paths or redirects to them) with the wordlist, up to `--depth` levels, deduplicated.
- **Same-Host Filtering**: Extracted external links are skipped; only same-host paths are enqueued.

### C2. Secrets Detection (Phase 5)
- **Scope**: every `200 OK` body (worker responses, JS files, root page) is scanned live; findings stream in magenta boxes with type, value, and context snippet.
- **Patterns**: cloud keys (AWS/Google), payment (Stripe), VCS tokens (GitHub), chat (Slack/Telegram), AI (OpenAI), email/SMS (SendGrid/Twilio), JWTs, private key blocks, database URLs, generic password/API-key assignments.
- **Noise control**: trigger pre-filter skips ordinary pages before regex; placeholder values (`your_...`, `changeme`, `xxxx`, `<fill in>`) and short values (< 8 chars) are ignored; dedup by `(url, type, value)`; capped at 20 findings per page.
- **Reporting**: new `SECRET` type with stats counter, JSON fields (`secret_type`, `value`, `context`), TXT/HTML sections, and Telegram count.

### D. Stealth & WAF Evasion
- **Header Rotation**: Inject `X-Forwarded-For`, `X-Real-IP`, etc., with randomized IPs.
- **User-Agent Rotation**: Use a massive, up-to-date list of browsers.

### E. Usability
- **Argument Parsing**: `--target`, `--concurrency` (alias `--threads`), `--timeout`, `--delay`, `--proxy`, `--proxies`, `--recursive`, `--depth`, `--no-extract`, `--no-stop`, `--output`.
- **Exporting**: Save results to JSON, plain text, and a self-contained styled HTML report (XSS-safe escaping).
- **Progress Bar**: Real-time scan progress with requests/sec + ETA.

### F. Integration (Phase 4)
- **HTML Reports**: `save_html_report()` renders cards with per-category counts, a findings table (type badges, auth scheme, score, reasons), and works with empty results.
- **Cross-platform**: no OS-specific dependencies in the engine; terminal init guards Windows VT handling and UTF-8 reconfiguration; the CLI, scanner, and exports run identically on Linux and Windows.
- **Docker**: slim `python:3.12` image, compose service mounting `./output`.
- **Testing**: pytest suite boots a local `http.server` fixture (WordPress-style root, JS endpoints, 401 Basic, directory index) for end-to-end validation of the whole pipeline.

## 3. Data Management
- `data/magic_admin_paths.txt`: generic wordlist (114k+ paths).
- `data/tech/`: per-platform wordlists loaded automatically by detected technology.
- Support for custom wordlists via CLI.
