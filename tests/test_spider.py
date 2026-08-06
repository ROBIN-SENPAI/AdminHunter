from core.spider import extract_from_html, extract_from_js, is_skippable

BASE = "http://example.com"


def test_html_hrefs_and_actions():
    html = ("<html><a href='/admin/'>A</a><a href='https://example.com/api'>B</a>"
            "<form action='/login'></form><script src='/js/app.js'></script></html>")
    urls = extract_from_html(html, BASE)
    assert 'http://example.com/admin/' in urls
    assert 'https://example.com/api' in urls
    assert 'http://example.com/login' in urls
    assert 'http://example.com/js/app.js' in urls


def test_html_external_link_kept_for_caller_side_filtering():
    html = "<a href='https://other-site.com/x'>ext</a>"
    urls = extract_from_html(html, BASE)
    assert 'https://other-site.com/x' in urls


def test_html_relative_and_protocol_relative():
    html = "<a href='sub/page'>rel</a><a href='//cdn.example.com/lib.js'>cdn</a>"
    urls = extract_from_html(html, BASE)
    assert 'http://example.com/sub/page' in urls
    assert 'http://cdn.example.com/lib.js' in urls


def test_js_endpoints_extracted():
    js = 'var a = "/api/v1/login"; fetch("/api/v2/user?id=1"); url("/img/logo.png");'
    urls = extract_from_js(js, "http://example.com/app.js")
    assert 'http://example.com/api/v1/login' in urls
    assert 'http://example.com/api/v2/user' in urls
    assert 'http://example.com/img/logo.png' in urls
    # bare /api/ fragment must not be added when /api/* paths already cover it
    assert '/api/' not in urls


def test_js_full_urls_and_relative():
    js = 'connect("https://api.example.com/ws"); xhr("/data");'
    urls = extract_from_js(js, "http://example.com/main.js")
    assert 'https://api.example.com/ws' in urls
    assert 'http://example.com/data' in urls


def test_js_bare_api_fragment_when_no_quoted_match():
    js = 'fetch("/api/" + path + "/items");'
    urls = extract_from_js(js, "http://example.com/main.js")
    assert 'http://example.com/api/' in urls


def test_is_skippable():
    assert is_skippable("https://example.com/css/style.css")
    assert is_skippable("https://example.com/images/logo.png")
    assert is_skippable("https://example.com/fonts/f.woff2")
    assert is_skippable("https://example.com/img/bg.jpg")
    assert is_skippable("https://example.com/file.pdf")
    assert is_skippable("https://example.com/archive.zip")
    assert is_skippable("javascript:void(0)")
    assert is_skippable("mailto:x@y.com")
    assert not is_skippable("https://example.com/admin/login")
    assert not is_skippable("https://example.com/api/v2/user")
