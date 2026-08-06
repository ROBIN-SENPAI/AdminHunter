from core.recon import gather_recon


def test_recon_detects_wordpress_and_ip(server_url):
    info = gather_recon(server_url)
    assert info['ip'] == '127.0.0.1'
    assert any('wordpress' in t.lower() for t in info['tech'])


def test_recon_with_port_does_not_crash(server_url):
    # Regression: gethostbyname must receive the hostname, not the full netloc
    info = gather_recon(server_url)
    assert info['ip'] == '127.0.0.1'


def test_recon_returns_all_keys(server_url):
    info = gather_recon(server_url)
    assert {'ip', 'server', 'powered_by', 'tech'} <= set(info.keys())
