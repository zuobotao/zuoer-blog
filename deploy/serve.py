"""Serve the built blog on a trusted LAN without runtime dependencies."""

import argparse
import json
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from analytics import Analytics, client_ip, canonical_path


class BlogHandler(SimpleHTTPRequestHandler):
    analytics = None

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):
        # Access logs otherwise retain complete IPs and search query strings.
        return

    def json_response(self, code, data):
        content = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/api/analytics/counts':
            try:
                return self.json_response(200, self.analytics.counts(parse_qs(url.query).get('path', ['/'])[0]))
            except Exception:
                return self.json_response(503, {'error': 'unavailable'})
        if url.path.startswith('/api/'):
            return self.json_response(404, {'error': 'not_found'})
        return super().do_GET()

    def do_POST(self):
        if self.path != '/api/analytics/view':
            return self.json_response(404, {'error': 'not_found'})
        origin = self.headers.get('Origin')
        try:
            origin_host = urlsplit(origin or '').netloc
        except ValueError:
            origin_host = None
        if (not origin or origin_host != self.headers.get('Host') or
                self.headers.get('Sec-Fetch-Site') not in (None, 'same-origin')):
            return self.json_response(403, {'error': 'origin'})
        if self.headers.get('DNT') == '1' or self.headers.get('Sec-GPC') == '1':
            return self.json_response(200, {'recorded': False})
        agent = self.headers.get('User-Agent', '')
        if re.search(r'bot|crawler|spider|headless|curl|wget|python', agent, re.I):
            return self.json_response(200, {'recorded': False})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 2048:
                return self.json_response(413, {'error': 'size'})
            data = json.loads(self.rfile.read(size))
            path = data.get('path', '')
            if not isinstance(path, str) or path.startswith('//') or not re.fullmatch(r'/[A-Za-z0-9/_-]*', path):
                return self.json_response(400, {'error': 'path'})
            path = canonical_path(path)
            if not (Path(self.directory) / path.lstrip('/') / 'index.html').is_file():
                return self.json_response(400, {'error': 'path'})
            source = data.get('source', '')
            if not isinstance(source, str):
                return self.json_response(400, {'error': 'source'})
            recorded = self.analytics.record(path, client_ip(self.client_address[0], self.headers), source, agent)
            return self.json_response(200, {'recorded': recorded})
        except (ValueError, TypeError, AttributeError):
            return self.json_response(400, {'error': 'invalid'})
        except Exception:
            return self.json_response(503, {'error': 'unavailable'})
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript",
        ".css": "text/css",
        ".xml": "application/xml",
        ".svg": "image/svg+xml",
    }

    def list_directory(self, path):
        self.send_error(404)
        return None

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        page = Path(self.directory) / "404.html"
        if code != 404 or not page.is_file():
            return super().send_error(code, message, explain)
        content = page.read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / "index.html").is_file():
        parser.error(f"Missing blog index: {directory}")
    BlogHandler.analytics = Analytics(Path(__file__).resolve().parent / 'data')
    server = ThreadingHTTPServer(
        (args.host, args.port), partial(BlogHandler, directory=str(directory))
    )
    print(f"Serving {directory} on {args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
