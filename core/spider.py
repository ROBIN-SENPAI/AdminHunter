"""Link/endpoint extraction from HTML, CSS, and JavaScript.

Used by the scanner to discover additional scan targets (phase 3).
"""
import re
from urllib.parse import urljoin, urlparse

ATTR_URL_RE = re.compile(r'''(?i)(?:src|href|action|data-src|poster)\s*=\s*["']([^"']+)["']''')
CSS_URL_RE = re.compile(r'''url\(\s*["']?([^"')]+)["']?\s*\)''', re.IGNORECASE)
JS_PATH_RE = re.compile(r'''["'](/[A-Za-z0-9_\-./{}?=&%:@]{2,})["']''')
JS_FULL_URL_RE = re.compile(r'''["'](https?://[^"'\s)]{4,})["']''')
JS_API_RE = re.compile(r'''(?<![A-Za-z0-9_/])(?:/api/|/rest/|/graphql|/v\d+/|/admin/|/dashboard/)''')

# File types not worth scanning as targets
SKIP_EXTS = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
             '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.webp', '.avif', '.map',
             '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.gz', '.tar', '.7z', '.rar'}


def _clean(base, raw):
    raw = raw.strip().strip('"\'')
    if not raw or raw.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:', 'about:')):
        return None
    u = urljoin(base, raw)
    if u.startswith(('http://', 'https://')):
        u = u.split('?', 1)[0].split('#', 1)[0]
    return u


def _cap(urls, cap):
    return urls if len(urls) <= cap else set(list(urls)[:cap])


def extract_from_html(html, base_url, cap=200):
    """Extract all src/href/action URLs plus CSS url() references from an HTML page."""
    out = set()
    for m in ATTR_URL_RE.findall(html):
        u = _clean(base_url, m)
        if u:
            out.add(u)
    for m in CSS_URL_RE.findall(html):
        u = _clean(base_url, m)
        if u:
            out.add(u)
    return _cap(out, cap)


def extract_from_js(js, base_url, cap=100):
    """Extract path-like strings, API endpoints, and CSS url() from a JS file."""
    out = set()
    for m in JS_PATH_RE.findall(js):
        u = _clean(base_url, m)
        if u:
            out.add(u)
    for m in JS_FULL_URL_RE.findall(js):
        u = _clean(base_url, m)
        if u:
            out.add(u)
    for m in CSS_URL_RE.findall(js):
        u = _clean(base_url, m)
        if u:
            out.add(u)
    existing_paths = [urlparse(u).path for u in out]
    for m in JS_API_RE.finditer(js):
        frag = m.group(0)
        if not any(p.startswith(frag) for p in existing_paths):
            out.add(frag)
    return _cap(out, cap)


def is_skippable(url):
    """True if the URL points to a static asset or a non-HTTP scheme."""
    parsed = urlparse(url)
    if parsed.scheme not in ('', 'http', 'https'):
        return True
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in SKIP_EXTS)
