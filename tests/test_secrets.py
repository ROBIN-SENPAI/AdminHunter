from core.secrets import scan_secrets, _is_placeholder, _looks_suspicious


def types(found):
    return [s['secret_type'] for s in found]


def values(found):
    return [s['value'] for s in found]


def test_aws_access_key_detected():
    found = scan_secrets('var cred = "AKIA6L7Q2X4Z9K8F3W1E";')
    assert 'AWS Access Key ID' in types(found)


def test_aws_secret_key_assignment_detected():
    body = 'aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYAbCdEfGhXyZq"'
    found = scan_secrets(body)
    assert 'AWS Secret Access Key' in types(found)


def test_google_api_key_detected():
    found = scan_secrets('key: "AIza' + 'C' * 35 + '"')
    assert 'Google API Key' in types(found)


def test_stripe_and_github_detected():
    body = ('sk_live_' + 'A' * 24 + '\n'
            'ghp_' + '1' * 36)
    found = scan_secrets(body)
    assert 'Stripe Secret Key' in types(found)
    assert 'GitHub Token' in types(found)


def test_telegram_bot_token_detected():
    found = scan_secrets('token = "8126103859:AAH6kUxV2dE8qW4rT9yZ7bC1fG3jL5mN8pQ"')
    assert 'Telegram Bot Token' in types(found)


def test_private_key_block_detected():
    body = ('-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA7d+j\n'
            '-----END RSA PRIVATE KEY-----')
    found = scan_secrets(body)
    assert 'Private Key Block' in types(found)


def test_database_url_detected():
    found = scan_secrets('postgres://admin:pass123@db.internal:5432/prod')
    assert 'Database URL' in types(found)


def test_password_assignment_detected():
    found = scan_secrets('DB_PASSWORD=supersecret')
    assert 'Password Assignment' in types(found)
    assert 'supersecret' in values(found)


def test_placeholders_ignored():
    body = ('API_KEY = "your_api_key_here"\npassword = "changeme"\n'
            'secret_key = "xxxxxxxx"\nclient_secret = "<fill in>"')
    assert scan_secrets(body) == []


def test_short_values_ignored():
    found = scan_secrets('password = "abc"')
    assert found == []


def test_deduplication_within_page():
    body = 'key = "ghp_' + '2' * 36 + '" and again ghp_' + '2' * 36
    found = scan_secrets(body)
    gh = [s for s in found if s['secret_type'] == 'GitHub Token']
    assert len(gh) == 1


def test_plain_html_skipped_fast():
    html = '<html><head><title>Home</title></head><body><h1>Welcome</h1><a href="/about">About</a></body></html>'
    assert _looks_suspicious(html) is False
    assert scan_secrets(html) == []


def test_context_snippet_included():
    found = scan_secrets('const G = "AIza' + 'D' * 35 + '";')
    assert found
    assert 'const G' in found[0]['context']
