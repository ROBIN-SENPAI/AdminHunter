import pytest

from core.scanner import Scanner, ADMIN_THRESHOLD

LOGIN_BODY = ("<html><head><title>Admin Login</title></head><body>"
              "<form><input type='text' name='user'><input type='password' name='pass'>"
              "<button>Sign in</button></form></body></html>")
BLOG_BODY = ("<html><head><title>My Blog</title></head><body><h1>Latest Posts</h1>"
             "<a href='/login'>login</a></body></html>")
HOME_BODY = ("<html><head><title>Home</title></head><body><h1>Welcome</h1>"
             "<a href='/admin/'>Admin</a></body></html>")
PLAIN = "<html><head><title>About</title></head><body><p>About us</p></body></html>"


@pytest.fixture
def scanner():
    s = Scanner(target="http://test.local", paths=["/x"], concurrency=2)
    return s


def test_login_page_scored_above_threshold(scanner):
    score, reasons = scanner.score_admin_page("http://test.local/admin/login", LOGIN_BODY)
    assert score >= ADMIN_THRESHOLD
    assert any("password" in r for r in reasons)


def test_blog_page_scored_below_threshold(scanner):
    score, _ = scanner.score_admin_page("http://test.local/blog", BLOG_BODY)
    assert score < ADMIN_THRESHOLD


def test_plain_page_scored_zero(scanner):
    score, reasons = scanner.score_admin_page("http://test.local/about", PLAIN)
    assert score == 0
    assert reasons == []


def test_soft_404_keyword_body(scanner):
    assert scanner.is_soft_404("<html><title>Not Found</title><body>404</body></html>")
    assert scanner.is_soft_404("<html><body>Page does not exist</body></html>")


def test_soft_404_identical_to_baseline(scanner):
    scanner.baseline = (len(HOME_BODY), HOME_BODY.lower(), 'home')
    assert scanner.is_soft_404(HOME_BODY)


def test_real_page_not_soft_404_when_same_length_diff_title(scanner):
    # Same length as baseline but different title → must NOT be filtered
    different = HOME_BODY.replace('<title>Home</title>', '<title>Admin</title>')
    scanner.baseline = (len(HOME_BODY), HOME_BODY.lower(), 'home')
    assert not scanner.is_soft_404(different)


def test_soft_404_same_title_similar_length(scanner):
    # Same title as root + similar length → custom 404, must be filtered
    variant = HOME_BODY.replace('<h1>Welcome</h1>', '<h1>Nothing here</h1>')
    scanner.baseline = (len(HOME_BODY), HOME_BODY.lower(), 'home')
    assert scanner.is_soft_404(variant)


def test_soft_404_without_baseline_scans_plain_pages(scanner):
    assert not scanner.is_soft_404(PLAIN)


def test_sensitive_ext_never_scored_as_admin():
    scanner = Scanner(target="http://test.local", paths=["/.env"], concurrency=2)
    assert scanner.stats['found_panels'] == 0
