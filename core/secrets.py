"""Secrets detection: scans response bodies for high-confidence credentials.

Patterns cover cloud provider keys, tokens, private keys, database URLs,
and generic password/API-key assignments. A cheap trigger pre-filter skips
the heavy regex pass for the vast majority of ordinary pages.
"""
import re

# Substrings that make a body worth scanning (checked case-insensitively).
# Ordinary HTML pages almost never contain these, so this filter avoids
# paying regex cost on every response of a 100k+ path scan.
TRIGGERS = (
    '-----begin', 'sk_live', 'sk_test', 'pk_live', 'whsec_', 'ghp_', 'ghu_',
    'github_pat', 'xoxb-', 'xoxp-', 'xoxa-', 'xoxr-', 'akia', 'asia', 'aida',
    'aroa', 'aiza', 'eyj', 'sg.', 'sk-', 'aws_', 'api_key', 'apikey', 'api-key',
    'apisecret', 'api_secret', 'client_secret', 'access_key', 'secret_key',
    'password', 'passwd', 'pwd', 'db_pass', 'db_password', '://', 'token',
)

# (label, compiled regex). When the regex has capture groups, the last
# captured group is used as the secret value.
SECRET_PATTERNS = [
    ("AWS Access Key ID", re.compile(r'\b(?:AKIA|ASIA|AIDA|AROA)[A-Z0-9]{16}\b')),
    ("AWS Secret Access Key", re.compile(r'(?i)\baws[_-]?secret[_-]?access[_-]?key\b[\s=:]+["\']?([A-Za-z0-9/+=]{40})')),
    ("Google API Key", re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')),
    ("Stripe Secret Key", re.compile(r'\bsk_live_[0-9A-Za-z]{16,}\b')),
    ("Stripe Webhook Secret", re.compile(r'\bwhsec_[0-9A-Za-z]{16,}\b')),
    ("GitHub Token", re.compile(r'\bghp_[0-9A-Za-z]{36}\b')),
    ("GitHub OAuth Token", re.compile(r'\bgho_[0-9A-Za-z]{36}\b')),
    ("GitHub App Token", re.compile(r'\bghu_[0-9A-Za-z]{36}\b')),
    ("GitHub Fine-grained Token", re.compile(r'\bgithub_pat_[0-9A-Za-z_]{22,}\b')),
    ("Slack Token", re.compile(r'\bxox[baprs]-[0-9A-Za-z-]{10,}\b')),
    ("Telegram Bot Token", re.compile(r'\b\d{8,10}:[A-Za-z0-9_-]{35}\b')),
    ("OpenAI API Key", re.compile(r'\bsk-[A-Za-z0-9]{20,}\b')),
    ("SendGrid API Key", re.compile(r'\bSG\.[A-Za-z0-9_-]{22,}\.[A-Za-z0-9_-]{22,}\b')),
    ("Twilio API Key", re.compile(r'\bSK[0-9a-fA-F]{32}\b')),
    ("JWT Token", re.compile(r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b')),
    ("Private Key Block", re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----')),
    ("Database URL", re.compile(r'(?i)\b(?:mysql|postgres|postgresql|mongodb(?:\+srv)?|redis|amqp)://[^\s"\'<>]{8,}')),
    ("Password Assignment", re.compile(r'(?i)\b(?:password|passwd|pwd|db_pass|db_password|db_passwd)\b\s*[=:]\s*["\']?([A-Za-z0-9!@#$%^&*_.\-]{8,})["\']?')),
    ("API Key Assignment", re.compile(r'(?i)\b(?:api[_-]?key|apikey|api[_-]?secret|client[_-]?secret|access[_-]?key|secret[_-]?key|auth[_-]?token)\b\s*[=:]\s*["\']?([A-Za-z0-9_\-./+]{12,})["\']?')),
]

# Values that look like documentation placeholders, not real secrets.
PLACEHOLDER_RE = re.compile(r'(?i)(your[_-]|example|sample|changeme|changethis|placeholder|'
                            r'dummy|<[^>]*>|x{4,}|\.{4,}|redacted|hidden|remove[-_ ]?me|'
                            r'^(?:password|secret|token|key|pass|pwd|test|demo|true|false|null|none)$)')

MAX_PER_PAGE = 20
VALUE_MAX = 120
CONTEXT_RADIUS = 48


def _looks_suspicious(body):
    """Cheap pre-filter: skip the regex pass unless the body hints at secrets."""
    lower = body.lower()
    return any(t in lower for t in TRIGGERS)


def _is_placeholder(value):
    if len(value) < 8:
        return True
    return bool(PLACEHOLDER_RE.search(value))


def _snippet(body, start, end):
    a = max(0, start - CONTEXT_RADIUS)
    b = min(len(body), end + CONTEXT_RADIUS)
    snippet = body[a:b].replace('\n', ' ').replace('\r', '').strip()
    if a > 0:
        snippet = '...' + snippet
    if b < len(body):
        snippet = snippet + '...'
    return snippet[:180]


def scan_secrets(body, url=None):
    """Return a list of {secret_type, value, context} dicts found in body.

    Results are deduplicated per (type, value). Returns [] fast for
    ordinary pages thanks to the trigger pre-filter.
    """
    if not body or not _looks_suspicious(body):
        return []
    found = []
    seen = set()
    for name, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(body):
            if m.lastindex:
                value = m.group(m.lastindex)
            else:
                value = m.group(0)
            value = value.strip('\'" ')
            if _is_placeholder(value):
                continue
            key = (name, value)
            if key in seen:
                continue
            seen.add(key)
            found.append({
                'secret_type': name,
                'value': value[:VALUE_MAX],
                'context': _snippet(body, m.start(), m.end()),
            })
            if len(found) >= MAX_PER_PAGE:
                return found
    return found
