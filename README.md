<p align="center">
  <img src="AdminHunter.png" width="650">
</p>

<h1 align="center">AdminHunter Elite Pro v5.0</h1>
<h3 align="center">The Ultimate Sensitive Information Gathering Framework</h3>

<p align="center">
  <b>Version:</b> 5.0 Elite Pro &nbsp;|&nbsp; <b>Developer:</b> ROBIN ABU IBRAHIM &nbsp;|&nbsp; <b>Telegram:</b> @xFFBI
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Line Arguments](#command-line-arguments)
- [Usage Examples](#usage-examples)
- [How Detection Works](#how-detection-works)
  - [Scoring System](#scoring-system)
  - [Soft 404 Filtering](#soft-404-filtering)
  - [Auth Detection](#auth-detection)
- [Reconnaissance & Technology Fingerprinting](#reconnaissance--technology-fingerprinting)
- [Endpoint Discovery](#endpoint-discovery)
- [Recursive Scanning](#recursive-scanning)
- [Proxies & Evasion](#proxies--evasion)
- [Output & Reports](#output--reports)
  - [JSON Report](#json-report)
  - [HTML Report](#html-report)
- [Docker](#docker)
- [Automated Testing](#automated-testing)
- [Project Structure](#project-structure)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Disclaimer](#disclaimer)

---

## Overview

AdminHunter Elite Pro is a professional-grade reconnaissance framework designed for identifying administrative panels and sensitive file exposures on web applications. It combines a high-throughput asynchronous scanning engine with an intelligent detection layer that analyzes page content rather than relying on raw HTTP status codes, dramatically reducing false positives.

The tool performs automated reconnaissance, fingerprints the target's technology stack, loads platform-specific wordlists, discovers hidden endpoints from HTML and JavaScript, and recursively explores discovered directories - all while rotating proxies, evading WAF filters, and streaming live statistics.

---

## Key Features

**Scanning Engine**
- Fully asynchronous engine built on `asyncio` + `aiohttp` with a persistent connection pool.
- Configurable concurrency (default 50) with per-host connection limits.
- Smart retry logic with exponential backoff on `429`/`5xx` responses and network errors.
- Adaptive timeout that self-raises (up to 30 seconds) on slow networks.
- Randomized delay jitter for rate limiting.
- Live progress bar with percent, requests/sec, ETA, elapsed time, and running find counter.

**Detection Intelligence**
- Content-aware scoring system (title keywords, password fields, login forms, auth hints, final URL).
- Custom soft-404 filtering using a root-page baseline (length + title comparison).
- HTTP 401 endpoints reported as `AUTH` with their `WWW-Authenticate` scheme.
- Sensitive file classification (`.env`, `.git/config`, `phpinfo.php`, `wp-config.php`, backups, etc.).
- **Live secrets detection**: every fetched body is scanned for credentials and keys (AWS, Google, Stripe, GitHub, Slack, Telegram, OpenAI, SendGrid, Twilio, JWTs, private keys, database URLs, password/API-key assignments) and reported instantly with the actual value and surrounding context.

**Reconnaissance**
- Automatic server fingerprinting: IP, web server, `X-Powered-By`, cookies, and content markers.
- Technology detection for WordPress, Drupal, Joomla, Laravel, Django, ASP.NET, Express, Rails, PHP, nginx, Apache, and Cloudflare.
- Platform-specific wordlists loaded and scanned with priority.

**Discovery**
- Endpoint extraction from HTML (`src`/`href`/`action`, CSS `url()`).
- JavaScript crawling (up to 10 files) to extract API paths and endpoint strings.
- Same-host filtering of extracted links.
- Recursive directory scanning with configurable depth.
- Query-string and fragment stripping from discovered endpoints.

**Operational**
- Proxy pool with automatic rotation and failover (dead proxies blacklisted per session).
- User-Agent rotation and stealth headers for WAF evasion.
- Triple export format: JSON, plain text, and a styled self-contained HTML report.
- Docker support.
- Cross-platform: runs identically on Windows, Linux, and macOS (Python 3.8+).
- 38 automated pytest tests covering the full pipeline.

---

## Architecture

The project follows a modular design where each concern is isolated in its own module:

```
┌────────────────────────────────────────────────────────────────┐
│                           main.py                              │
│          Entry point, CLI parsing, orchestration, output       │
└──────────────┬─────────────────────────────────────────────────┘
               │
   ┌───────────┼───────────────────────────────────────────────┐
   │           │                                               │
┌──▼─────┐  ┌──▼────────┐  ┌──────────────┐  ┌──────────────┐  │
│ recon  │  │  scanner  │  │   spider     │  │  tech paths  │  │
│ (sync) │──▶  (async)  │──▶  (extract)   │  │ (wordlists)  │  │
└────────┘  └──┬────────┘  └──────────────┘  └──────────────┘  │
               │                                               │
   ┌───────────┼───────────────┬───────────────────────────────┘
   │           │               │
┌──▼─────┐  ┌──▼─────────┐  ┌──▼───────────┐
│  ui    │  │  logger    │  │  (export)    │
│ (tui)  │  │ (json/txt) │  │  (html)      │
└────────┘  └────────────┘  └──────────────┘
```

Pipeline stages:

1. **Recon** (`core/recon.py`) - synchronous fingerprinting using the `requests` library.
2. **Baseline** - the root page is fetched and stored as a soft-404 comparison baseline.
3. **Discovery** (`core/spider.py`) - links and JS endpoints are extracted and enqueued.
4. **Scan** (`core/scanner.py`) - the async engine drains the queue with bounded concurrency.
5. **Classification** - each response is scored and labeled `ADMIN`, `SENSITIVE`, or `AUTH`.
6. **Recursion** - discovered directories are re-scanned with the wordlist.
7. **Report** - results are exported to JSON, TXT, and HTML, then optionally pushed to Telegram.

---

## Installation

**Requirements:** Python 3.8+ (tested on 3.14), pip.

```bash
git clone https://your-repository/adminhunter.git
cd AdminHunter
pip install -r requirements.txt
```

`requirements.txt`:

| Package | Minimum Version | Purpose |
|---------|----------------|---------|
| `aiohttp` | 3.9.0 | Async HTTP engine |
| `requests` | 2.31.0 | Synchronous recon phase |
| `urllib3` | 2.0.0 | TLS handling (suppresses insecure warnings) |
| `colorama` | 0.4.6 | Cross-platform ANSI color support |

---

## Quick Start

Interactive mode (simplest):

```bash
python main.py
```

Enter the target URL when prompted. Everything else is automatic.

Direct mode:

```bash
python main.py -t https://example.com
```

The tool will:

1. Print the banner and scan configuration.
2. Fingerprint the server (IP, software, technologies).
3. Load the generic wordlist (114,000+ paths) plus any tech-specific wordlists.
4. Scan all paths concurrently with live progress.
5. Display every finding with reasons and score.
6. Export results to `scan_<timestamp>.json`, `.txt`, and `.html`.

---

## Command Line Arguments

| Argument | Alias | Default | Description |
|----------|-------|---------|-------------|
| `-t, --target` | - | required | Target URL. `http://`/`https://` scheme optional (https is assumed). |
| `-w, --wordlist` | - | `data/magic_admin_paths.txt` | Path to a custom wordlist (one path per line, `#` comments allowed, `{ext}` placeholders expand to `.php/.asp/.aspx/.jsp/.html`). |
| `--threads` | `--concurrency` | `50` | Maximum concurrent requests. |
| `--timeout` | - | `10` | Request timeout in seconds (auto-raises up to 30s on slow networks). |
| `--no-stop` | - | `False` | Continue scanning after the first admin panel is found. By default the scan stops at the first `ADMIN` finding. |
| `--delay` | - | `0.0` | Minimum delay between requests; randomized jitter is applied (`0.5x`-`1.5x`). |
| `--proxy` | - | `None` | Single proxy URL, e.g. `http://user:pass@host:port`. |
| `--proxies` | - | `None` | File of proxies (one per line); rotated round-robin with failover. |
| `--recursive` | - | `False` | Recursively scan discovered directories. |
| `--depth` | - | `2` | Maximum recursion depth (used with `--recursive`). |
| `--no-extract` | - | `False` | Disable automatic link/JS endpoint discovery. |
| `-o, --output` | - | `scan_<time>` | Base name for result files (saves `.json`, `.txt`, `.html`). |

---

## Usage Examples

Basic scan, stopping at the first admin panel:

```bash
python main.py -t https://example.com
```

Full sweep with 100 concurrency, continuing past findings, 2-second delay:

```bash
python main.py -t https://example.com --concurrency 100 --no-stop --delay 2
```

Custom wordlist:

```bash
python main.py -t https://example.com -w my-paths.txt --no-stop
```

Recursive directory scanning with deeper recursion:

```bash
python main.py -t https://example.com --recursive --depth 3
```

Routing through a proxy pool:

```bash
python main.py -t https://example.com --proxies proxies.txt --no-stop
```

Disabling JS/link discovery (pure wordlist scan):

```bash
python main.py -t https://example.com --no-extract
```

Custom output naming:

```bash
python main.py -t https://example.com -o /path/to/reports/corp1
```

Producing all three report formats with custom naming:

```bash
python main.py -t https://example.com -o corp1
```

---

## How Detection Works

### Scoring System

Every `200 OK` response (that passes soft-404 filtering) is scored. Points accumulate from:

| Signal | Points |
|--------|--------|
| Strong title keyword (`login`, `admin`, `sign in`, `control panel`, ...) | +3 |
| Weak title keyword (e.g. generic `login` references) | +1 |
| Password input field (`type="password"`) | +4 |
| Login form with submit | +2 |
| Auth keywords in content (`authenticate`, `session`, `logout`, ...) | +1 |
| URL hint (`/admin`, `/login`, `/dashboard`, ...) | +1 |

Pages scoring **4 or higher** are classified as `ADMIN` panels. Everything below is ignored, which prevents generic pages (blogs with a footer login link, marketing sites, etc.) from flooding results.

### Secrets Detection

Every fetched body (scan responses, JavaScript files, the root page) is scanned for high-confidence credentials. A cheap trigger pre-filter skips ordinary pages, so the regex pass only runs on suspicious content. Recognized secret types:

| Category | Examples |
|----------|----------|
| Cloud keys | AWS Access Key ID / Secret, Google API Key |
| Payment | Stripe Secret Key, Stripe Webhook Secret |
| VCS tokens | GitHub (classic, OAuth, App, fine-grained) |
| Chat | Slack tokens, Telegram bot tokens |
| AI | OpenAI API keys (`sk-...`) |
| Email / SMS | SendGrid API keys, Twilio API keys |
| Auth | JWT tokens, private key blocks (`-----BEGIN ... PRIVATE KEY-----`) |
| Infrastructure | Database URLs (`mysql://`, `postgres://`, `mongodb://`, ...) |
| Generic | `password=`, `api_key=`, `client_secret=` assignments |

Findings appear instantly in magenta `SECRET DISCOVERED` boxes with the URL, secret type, the actual value, and a context snippet. Documentation placeholders (`your_...`, `changeme`, `xxxx`, `<fill in>`) and values shorter than 8 characters are ignored to avoid noise. Secrets are deduplicated by `(URL, type, value)`.

### Soft 404 Filtering

Many applications return `200 OK` for missing pages. To counter this, the scanner:

1. Fetches the root page first and stores `(length, body, title)` as the baseline.
2. Filters responses whose body contains `not found`/`404`/`does not exist` keywords (under 200 chars).
3. Filters responses with `404`/`not found` in the title.
4. Filters responses identical to the baseline body.
5. Filters responses with the **same title as the root** and **length within 15%** of it (custom 404 pages).

### Auth Detection

Responses with `401 Unauthorized` are classified as `AUTH` endpoints. The `WWW-Authenticate` header is parsed (e.g. `Basic`, `Digest`, `NTLM`) and stored in the results so you know which authentication scheme protects the resource.

### Classification Summary

| Label | Condition | Reported Data |
|-------|-----------|---------------|
| `ADMIN` | 200, not soft-404, score >= 4 | URL, code, title, score, reasons |
| `SENSITIVE` | 200, not soft-404, sensitive extension | URL, code, title |
| `AUTH` | 401 | URL, code, title, auth scheme |
| `SECRET` | 200 body contains credentials/keys | URL, secret type, value, context |

---

## Reconnaissance & Technology Fingerprinting

Before scanning, `core/recon.py` gathers:

- **IP address** (DNS resolution of the hostname, port-safe).
- **Web server** (`Server` header, e.g. nginx, Apache, cloudflare).
- **Powered-by** (`X-Powered-By` header).
- **Technologies** detected from content markers, header values, and cookie names.

Supported platforms and their wordlists:

| Platform | Content Markers | Wordlist |
|----------|----------------|----------|
| WordPress | `wp-content`, `wp-includes`, `wp-json`, `wp-login` | `data/tech/wordpress.txt` |
| Drupal | `drupal`, `drupal.js` | `data/tech/drupal.txt` |
| Joomla | `joomla`, `com_content` | `data/tech/joomla.txt` |
| Laravel | `laravel`, `csrf-token` | `data/tech/laravel.txt` |
| Django | `django`, `csrftoken` | `data/tech/django.txt` |
| ASP.NET | `asp.net`, `__viewstate` | `data/tech/aspnet.txt` |

Detected platforms cause their wordlists to be loaded and scanned first (highest probability paths first), followed by the generic 114,000+ path wordlist.

---

## Endpoint Discovery

When enabled (default), `core/spider.py` extracts targets from the live application:

1. The root page's HTML is parsed for `src`, `href`, `action`, `data-src`, `poster` attributes and CSS `url()` references.
2. JavaScript files linked from the root page are downloaded (up to 10 files) and parsed for:
   - Quoted path strings (`"/api/v1/login"`).
   - Full `http(s)://` URLs.
   - Bare API fragments (`/api/`, `/rest/`, `/graphql`, `/v1/`, `/admin/`, `/dashboard/`).
3. All extracted URLs are resolved to absolute form, stripped of query strings and fragments, and enqueued for scanning.

Only same-host URLs are scanned; external links are discarded. Static assets (images, fonts, media, archives, documents) are filtered out.

---

## Recursive Scanning

With `--recursive`, a directory is detected when:

- A path ends with `/`, or
- The final URL (after redirects) ends with `/`.

Each discovered directory is re-scanned with the full wordlist (deduplicated per depth), up to `--depth` levels. This surfaces nested panels like `/admin/settings/login` that flat wordlists miss.

---

## Proxies & Evasion

**Single proxy**

```bash
python main.py -t https://example.com --proxy http://127.0.0.1:8080
```

**Proxy pool**

```bash
# proxies.txt (http/https only)
http://user:pass@proxy1.example:8080
http://proxy2.example:3128
https://proxy3.example:443
```

```bash
python main.py -t https://example.com --proxies proxies.txt
```

Proxies are rotated round-robin. A proxy that fails (connection error) is blacklisted for the rest of the session and the request is retried on the next live proxy.

**WAF evasion** is built in: every request uses a rotated realistic User-Agent and injected headers such as `X-Forwarded-For`, `X-Real-IP`, and `X-Requested-With` with randomized values.

---

## Output & Reports

Results are saved under the output base name in three formats:

### JSON Report

`scan.json` - machine-readable, one object per finding:

```json
[
  {
    "url": "https://example.com/wp-login.php",
    "code": 200,
    "type": "ADMIN",
    "title": "WordPress Login",
    "score": 10,
    "reasons": ["password field", "title: wp-login.php"]
  },
  {
    "url": "https://example.com/admin/secure",
    "code": 401,
    "type": "AUTH",
    "title": "Restricted Area",
    "score": 0,
    "reasons": [],
    "auth": "Basic"
  }
]
```

### Text Report

`scan.txt` - human-readable summary with timestamps, titles, scores, and reasons for each finding.

### HTML Report

`scan.html` - a self-contained, dark-themed report with:

- Summary cards (Admin Panels, Sensitive Files, Auth Endpoints, Secrets, Total Requests, Retries, Failed).
- A findings table with color-coded type badges, HTTP code, title, auth scheme, score, and reasons (including extracted secret values).
- XSS-safe HTML escaping of all values.
- Zero external dependencies - open it anywhere, even offline.

---

## Docker

Build and run in a container:

```bash
docker build -t adminhunter:5.0 .
```

Single scan, storing reports on the host:

```bash
docker run --rm -v "$PWD/output:/out" adminhunter:5.0 -t https://example.com -o /out/scan
```

With docker compose (configure via `.env`):

```env
TARGET=https://example.com
```

```bash
docker compose run --rm adminhunter
```

The image is based on `python:3.12-slim` and installs only the runtime dependencies.

---

## Automated Testing

The project ships with a pytest suite (38 tests) covering every layer:

| File | Coverage |
|------|----------|
| `test_detection.py` | Scoring system, soft-404 variants, sensitive classification |
| `test_spider.py` | HTML/JS extraction, URL resolution, asset filtering |
| `test_recon.py` | Technology detection, port-safe IP resolution |
| `test_logger.py` | JSON/TXT/HTML export, HTML escaping |
| `test_secrets.py` | Credential pattern detection, placeholder filtering, deduplication |
| `test_e2e.py` | Full pipeline against a local HTTP server (recon -> wordlists -> discovery -> recursion -> auth -> secrets -> results) |

Run:

```bash
pip install -r requirements-dev.txt
python -m pytest tests -v
```

The end-to-end tests boot a real local HTTP server fixture (WordPress-style root, JS endpoints, a 401-protected area, and a directory index) so the entire pipeline is validated against live traffic.

---

## Project Structure

```
AdminHunter/
├── main.py                    # Entry point, CLI, orchestration
├── requirements.txt           # Runtime dependencies
├── requirements-dev.txt       # Test dependencies (pytest)
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # Compose service (output volume, env passthrough)
├── .dockerignore
├── README.md
├── core/
│   ├── scanner.py             # Async scanning engine (asyncio + aiohttp)
│   ├── scanner_thread.py      # Legacy threaded engine (backup)
│   ├── recon.py               # Server fingerprinting & tech detection
│   ├── secrets.py             # Credential/key detection patterns
│   └── spider.py              # HTML/CSS/JS endpoint extraction
├── utils/
│   ├── ui.py                  # Terminal UI (banner, boxes, progress, colors)
│   ├── logger.py              # JSON/TXT/HTML report generation
│   └── waf.py                 # User-Agent rotation & stealth headers
├── data/
│   ├── magic_admin_paths.txt  # Generic wordlist (114,000+ paths)
│   └── tech/                  # Platform-specific wordlists
│       ├── wordpress.txt
│       ├── drupal.txt
│       ├── joomla.txt
│       ├── laravel.txt
│       ├── django.txt
│       └── aspnet.txt
├── docs/
│   └── DESIGN.md              # Architecture & design notes
└── tests/
    ├── conftest.py            # Fixtures (local HTTP server, wordlist)
    ├── test_server.py         # Reusable test server
    ├── test_detection.py
    ├── test_spider.py
    ├── test_recon.py
    ├── test_logger.py
    ├── test_secrets.py
    └── test_e2e.py
```

---

## Performance

The asynchronous engine was benchmarked against a local test server:

| Engine | Throughput |
|--------|-----------|
| Legacy threaded engine | ~434 req/s |
| Async engine (aiohttp) | ~545-590 req/s |

Measured with 1,000-path wordlists. Real-world throughput varies with network latency, target responsiveness, proxy speed, and concurrency settings. Increase `--concurrency` for latency-bound targets; decrease it for fragile ones.

---

## Troubleshooting

**Windows console shows garbled colors or boxes**

Run with Windows Terminal or enable VT processing in your terminal settings. The tool auto-detects and enables VT mode on Windows 10+.

**"No admin panels found" on a target you expect to have them**

The target may be returning soft-404s (custom 404 pages with `200 OK`), behind a WAF that blocks the scanner, or the admin panel may be on a subdomain (out of scope). Try `--no-extract` off/on, lower concurrency (`--concurrency 20`), add `--recursive`, or extend the wordlist.

**Slow scanning against a remote target**

Raise `--concurrency`, or the target is rate-limiting you (watch the `Retries` counter). Consider `--delay 0` (default) only if you are authorized for aggressive scanning.

**Proxies not working**

Verify proxy URLs include the scheme (`http://`/`socks5://`) and credentials if required. Dead proxies are automatically blacklisted per session.

**Scan stops immediately**

This is default behavior - `--no-stop` is disabled by default for safety. Add `--no-stop` to keep scanning after the first admin panel.

**Results appear as files in the current directory**

Use `-o /absolute/path/name` to control where reports are written.

---

## Disclaimer

This tool is strictly for educational purposes and authorized security assessments only. Unauthorized use against systems without explicit written consent is illegal. The developer assumes no liability for misuse.

---

**AdminHunter Elite Pro v5.0** - Developed by ROBIN ABU IBRAHIM - Telegram: [@xFFBI](https://t.me/xFFBI)
