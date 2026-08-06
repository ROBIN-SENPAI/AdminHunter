from core.scanner import Scanner


def _type_map(results):
    return {r['url']: r for r in results}


def _build_paths(wordlist_path, server_url):
    from main import load_paths, load_tech_paths, merge_unique
    from core.recon import gather_recon
    recon = gather_recon(server_url)
    return merge_unique(load_tech_paths(recon['tech']) + load_paths(wordlist_path))


def test_full_scan_detects_all_categories(server_url, wordlist_path):
    paths = _build_paths(wordlist_path, server_url)
    assert any(p == 'wp-login.php' for p in paths)  # tech wordlist loaded via recon

    scanner = Scanner(target=server_url, paths=paths, concurrency=15, timeout=10,
                      stop_on_found=False, recursive=True, max_depth=1, extract_links=True)
    results = scanner.run()

    by_url = _type_map(results)
    found = {r['type'] for r in results}

    assert 'ADMIN' in found
    assert 'SENSITIVE' in found
    assert 'AUTH' in found

    # Admin panels discovered through all three phase-3 channels
    admin_urls = [u for u, r in by_url.items() if r['type'] == 'ADMIN']
    assert any(u.endswith('/wp-login.php') for u in admin_urls)          # tech wordlist
    assert any(u.endswith('/api/v2/login') for u in admin_urls)          # JS extraction
    assert any(u.endswith('/admin/settings') for u in admin_urls)        # recursion

    # Auth endpoint carries the scheme
    auth = [r for r in results if r['type'] == 'AUTH']
    assert any(r.get('auth') == 'Basic' for r in auth)

    # Sensitive files
    assert any(u.endswith('/.env') for u in by_url)
    assert any(u.endswith('/phpinfo.php') for u in by_url)

    # No false positives: blog page must not be flagged
    assert not any('blog' in u for u in by_url)

    # Secrets detected live from page bodies and JS files
    secrets = [r for r in results if r['type'] == 'SECRET']
    assert any(r['secret_type'] == 'Google API Key' for r in secrets)      # from app.js
    assert any(r['secret_type'] == 'GitHub Token' for r in secrets)        # from .env
    assert any(r['secret_type'] == 'Password Assignment' for r in secrets)  # from .env
    assert scanner.stats['secrets'] >= 3

    assert scanner.stats['failed'] == 0


def test_scan_without_extraction_skips_js_discovery(server_url, wordlist_path):
    paths = _build_paths(wordlist_path, server_url)
    scanner = Scanner(target=server_url, paths=paths, concurrency=15, timeout=10,
                      stop_on_found=False, recursive=False, extract_links=False)
    results = scanner.run()
    urls = [r['url'] for r in results]
    assert not any('api/v2/login' in u for u in urls)
    assert not any('secure' in u for u in urls)
    # app.js is never fetched without extraction -> no Google key from JS
    assert not any(r.get('secret_type') == 'Google API Key' for r in results)


def test_stop_on_found_stops_early(server_url, wordlist_path):
    paths = _build_paths(wordlist_path, server_url)
    scanner = Scanner(target=server_url, paths=paths, concurrency=10, timeout=10,
                      stop_on_found=True, recursive=False, extract_links=True)
    scanner.run()
    assert scanner.stats['found_panels'] >= 1
    assert scanner.stop_event.is_set()
