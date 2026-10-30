"""Season Book server: 127.0.0.1:4246, stdlib only. Serves dist/ (offline snapshot + print pages) and data/season.json."""
import http.server, json, os, socketserver
HERE = os.path.dirname(os.path.abspath(__file__)); PORT = int(os.environ.get("SB_PORT", 4246))
ROUTES = {"/": "dist/season-book-snapshot.html", "/index.html": "dist/season-book-snapshot.html",
          "/kida": "dist/print-kida.html", "/kidb": "dist/print-kidb.html", "/api/season.json": "data/season.json",
          "/season-book-kida.pdf": "dist/season-book-kida.pdf", "/season-book-kidb.pdf": "dist/season-book-kidb.pdf"}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        rel = ROUTES.get(path) or (path.lstrip("/") if path.startswith("/screenshots/") and ".." not in path else None)
        if path == "/healthz":
            return self._send(200, b'{"ok":true}', "application/json")
        if not rel or not os.path.exists(os.path.join(HERE, rel)):
            return self._send(404, b"not found", "text/plain")
        ct = {".html": "text/html; charset=utf-8", ".json": "application/json", ".pdf": "application/pdf", ".png": "image/png"}[os.path.splitext(rel)[1]]
        self._send(200, open(os.path.join(HERE, rel), "rb").read(), ct)

    def _send(self, code, body, ct):
        self.send_response(code); self.send_header("Content-Type", ct); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, *a): pass


class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True


if __name__ == "__main__":
    print(f"Season Book on http://127.0.0.1:{PORT}", flush=True)
    S(("127.0.0.1", PORT), H).serve_forever()
