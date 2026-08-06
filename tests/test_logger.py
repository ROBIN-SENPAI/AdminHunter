import json
from pathlib import Path

from utils.logger import save_results, save_html_report

RESULTS = [
    {'url': 'http://x.test/admin/login', 'code': 200, 'type': 'ADMIN',
     'title': 'Admin Login', 'score': 10, 'reasons': ['password field']},
    {'url': 'http://x.test/.env', 'code': 200, 'type': 'SENSITIVE',
     'title': 'N/A', 'score': 0, 'reasons': []},
    {'url': 'http://x.test/secure', 'code': 401, 'type': 'AUTH',
     'title': 'Restricted', 'score': 0, 'reasons': [], 'auth': 'Basic'},
]

STATS = {'total_requests': 42, 'found_panels': 1, 'sensitive_files': 1, 'auth': 1,
         'failed': 0, 'retries': 1}


def test_json_and_txt_export(tmp_path):
    base = str(tmp_path / "scan")
    json_path, txt_path = save_results(RESULTS, base)
    assert Path(json_path).exists()
    assert Path(txt_path).exists()
    data = json.loads(Path(json_path).read_text(encoding='utf-8'))
    assert len(data) == 3
    assert data[2]['auth'] == 'Basic'
    txt = Path(txt_path).read_text(encoding='utf-8')
    assert 'http://x.test/admin/login' in txt


def test_html_report_contains_results_and_escapes(tmp_path):
    results = [{'url': 'http://x.test/<script>alert(1)</script>', 'code': 200, 'type': 'ADMIN',
                'title': 'A&B <i>x</i>', 'score': 5, 'reasons': ['r1', 'r2']}]
    base = str(tmp_path / "scan")
    html_path = save_html_report(results, base, target='http://x.test', stats=STATS, version='test')
    assert Path(html_path).exists()
    html = Path(html_path).read_text(encoding='utf-8')
    assert 'AdminHunter' in html
    assert '<script>alert(1)</script>' not in html  # escaped
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert 'A&amp;B &lt;i&gt;x&lt;/i&gt;' in html
    assert 'Admin Panels' in html
    assert '42' in html


def test_html_report_empty_results(tmp_path):
    html_path = save_html_report([], str(tmp_path / "empty"), target='http://x.test')
    html = Path(html_path).read_text(encoding='utf-8')
    assert 'No findings detected' in html
