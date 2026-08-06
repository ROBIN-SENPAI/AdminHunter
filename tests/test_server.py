import http.server
import threading

HOME = ("<html><head><title>Home</title><meta name='generator' content='WordPress 6.4'></head>"
        "<body><h1>Welcome</h1><script src='/app.js'></script><a href='/admin/'>Admin</a></body></html>")

# "AIza" + 35 chars = a valid-looking Google API key
GOOGLE_KEY = "AIza" + "B" * 35
GITHUB_TOKEN = "ghp_" + "1" * 36

PAGES = {
    '/': HOME,
    '/app.js': ('var api = "/api/v2/login"; var sec = "/secure"; var x = "/blog"; url("bg.png");\n'
                f'var mapsKey = "{GOOGLE_KEY}";'),
    '/api/v2/login': ("<html><head><title>API Login</title></head><body><form action='/api/v2/login'>"
                      "<input type='text' name='username'><input type='password' name='password'>"
                      "<input type='submit' value='Sign in'></form></body></html>"),
    '/secure': '<html><head><title>Restricted Area</title></head><body>Auth required</body></html>',
    '/admin/': ("<html><head><title>Directory Index</title></head><body><ul><li>"
                "<a href='/admin/settings'>settings</a></li></ul></body></html>"),
    '/admin/settings': ("<html><head><title>Settings Login</title></head><body><form action='/admin/settings'>"
                        "<input type='password' name='password'><input type='submit'></form></body></html>"),
    '/wp-login.php': ("<html><head><title>WordPress Login</title></head><body><form>"
                      "<input type='text' name='log'><input type='password' name='pwd'>"
                      "<input type='submit' value='Log In'></form></body></html>"),
    '/blog': ("<html><head><title>My Awesome Blog</title></head><body><h1>Posts</h1>"
              "<a href='/login'>login</a></body></html>"),
    '/.env': (f'DB_PASSWORD=supersecret\nAPI_KEY=abc123\nGITHUB_TOKEN={GITHUB_TOKEN}\n'),
    '/phpinfo.php': '<html><head><title>phpinfo()</title></head><body>PHP Version 8.2</body></html>',
}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/does-not-exist':
            body = '<html><head><title>404 Not Found</title></head><body>not found</body></html>'
        else:
            body = PAGES.get(path, HOME)  # unknown paths return home (SPA-style)
        if path == '/secure':
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Restricted"')
        else:
            self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())


def start_server():
    """Start the test server on an ephemeral port. Returns the base URL."""
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}", srv


if __name__ == "__main__":
    import time
    import sys

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    url, srv = start_server()
    print(f"Test server: {url}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.shutdown()
