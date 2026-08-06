import socket
import re
import requests
import urllib3
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# (technology, content markers, header value markers, cookie markers)
TECH_RULES = [
    ("WordPress", ["wp-content", "wp-includes", "wp-json", "wp-login"], ["x-pingback"], ["wordpress", "wp-settings"]),
    ("Drupal", ["drupal", "drupal.js"], ["x-generator:drupal"], ["drupal"]),
    ("Joomla", ["joomla", "com_content"], ["x-generator:joomla"], ["joomla"]),
    ("Laravel", ["laravel", "csrf-token"], ["x-powered-by:laravel"], ["laravel_session"]),
    ("Django", ["django", "csrftoken", "__admin__"], ["x-powered-by:django"], ["csrftoken", "django"]),
    ("Express/Node.js", ["express", "powered by express"], ["x-powered-by:express"], ["connect.sid"]),
    ("ASP.NET", ["asp.net", "__viewstate"], ["x-aspnet-version", "x-powered-by:asp.net"], ["asp.net_sessionid", ".aspx"]),
    ("Ruby on Rails", ["rails", "csrf-param"], ["x-powered-by:ruby", "x-runtime"], ["_session", "rack.session"]),
    ("PHP", ["php", "php7"], ["x-powered-by:php"], ["phpsessid"]),
    ("nginx", [], ["server:nginx"], []),
    ("Apache", [], ["server:apache"], []),
    ("Cloudflare", [], ["server:cloudflare"], ["__cfduid"]),
]


def _detect_tech(content, headers, cookies):
    tech = []
    header_text = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
    cookie_text = " ".join(cookies).lower()

    for name, content_markers, header_markers, cookie_markers in TECH_RULES:
        hit = any(m in content for m in content_markers)
        if not hit:
            hit = any(m in header_text for m in header_markers)
        if not hit:
            hit = any(m in cookie_text for m in cookie_markers)
        if hit:
            tech.append(name)

    generator = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)',
                          content, re.IGNORECASE)
    if generator and generator.group(1).strip():
        tech.append(generator.group(1).strip())
    return tech


def gather_recon(target):
    info = {
        'ip': 'Unknown',
        'server': 'Unknown',
        'powered_by': 'Unknown',
        'tech': []
    }
    try:
        parsed = urlparse(target)
        domain = parsed.hostname or parsed.netloc  # hostname excludes the port
        if domain:
            info['ip'] = socket.gethostbyname(domain)
        else:
            info['ip'] = 'Unknown'

        response = requests.get(target, verify=False, timeout=10)
        headers = response.headers

        info['server'] = headers.get('Server', 'Unknown')
        info['powered_by'] = headers.get('X-Powered-By', 'Unknown')

        content = response.text.lower()
        cookies = list(response.cookies.get_dict().keys())
        info['tech'] = _detect_tech(content, headers, cookies)

    except Exception:
        pass
    return info
