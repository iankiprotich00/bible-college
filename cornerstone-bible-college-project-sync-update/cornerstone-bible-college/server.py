#!/usr/bin/env python3
"""Cornerstone Bible College portal server.

Serves the portal web page and a small JSON API backed by portal.db (SQLite).
Standard library only (Python 3.8+). Run:  python3 server.py
Then open http://localhost:8000
"""
import argparse, html, json, mimetypes, os, re, socket, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse
import portal_api
import portal_data
import portal_db as p

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
DOWNLOADS = os.path.join(HERE, "downloads")
MAX_BODY = 16 * 1024
UPLOAD_BODY = 42 * 1024 * 1024        # a submission may carry up to 30 MB of files, sent as base64
RATE_LIMIT, RATE_WINDOW = 30, 60          # max login/register calls per IP per minute
_hits = {}

def too_many(ip):
    now = time.time()
    hits = [t for t in _hits.get(ip, []) if now - t < RATE_WINDOW]
    hits.append(now); _hits[ip] = hits
    return len(hits) > RATE_LIMIT

class Handler(BaseHTTPRequestHandler):
    server_version = "CornerstonePortal/1.0"

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]}  {self.command} {self.path}  ->  {args[1] if len(args) > 1 else ''}")

    def send(self, code, obj=None, raw=None, ctype="application/json", extra=None):
        body = raw if raw is not None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def body(self, limit=MAX_BODY):
        n = int(self.headers.get("Content-Length") or 0)
        if n > limit: raise ValueError("request too large")
        data = json.loads(self.rfile.read(n) or b"{}")
        if not isinstance(data, dict): raise ValueError("bad request")
        return data

    def token(self):
        a = self.headers.get("Authorization", "")
        return a[7:] if a.startswith("Bearer ") else ""

    # ---- routing ----
    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"): return self.api("GET", path[5:], urlparse(self.path).query)
        if path.rstrip("/") == "/download": return self.download_page()
        if path.startswith("/downloads/"): return self.serve_apk(path)
        self.static(path)
    do_HEAD = do_GET

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"): return self.api("POST", path[5:], urlparse(self.path).query)
        self.send(404, {"ok": False, "message": "Not found."})

    def static(self, path):
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        full = os.path.realpath(os.path.join(WEB, rel))
        if os.path.commonpath([full, os.path.realpath(WEB)]) != os.path.realpath(WEB) or not os.path.isfile(full):
            return self.send(404, {"ok": False, "message": "Not found."})
        with open(full, "rb") as f: data = f.read()
        self.send(200, raw=data, ctype=mimetypes.guess_type(full)[0] or "application/octet-stream")

    # ---- test app download ----
    def apk_files(self):
        if not os.path.isdir(DOWNLOADS): return []
        return sorted(f for f in os.listdir(DOWNLOADS) if f.lower().endswith(".apk") and re.fullmatch(r"[A-Za-z0-9._-]+", f))

    def serve_apk(self, path):
        name = os.path.basename(unquote(path[len("/downloads/"):]))
        full = os.path.join(DOWNLOADS, name)
        if name not in self.apk_files() or not os.path.isfile(full):
            return self.send(404, {"ok": False, "message": "Not found."})
        with open(full, "rb") as f: data = f.read()
        self.send(200, raw=data, ctype="application/vnd.android.package-archive",
                  extra={"Content-Disposition": f'attachment; filename="{name}"'})

    def download_page(self):
        host = self.headers.get("Host", "localhost:8000")
        address = "http://" + host
        local_only = host.startswith(("localhost", "127.0.0.1"))
        items = ""
        for f in self.apk_files():
            size = os.path.getsize(os.path.join(DOWNLOADS, f)) / 1048576
            items += f'<a class="dl" href="/downloads/{quote(f)}"><b>Download {html.escape(f)}</b><span>{size:.1f} MB &middot; test build</span></a>'
        if not items:
            items = '<p class="warn">No app file has been added yet. Build the test app (see README_ANDROID.md) and copy the <code>.apk</code> into the <code>downloads</code> folder next to <code>server.py</code>. Then refresh this page.</p>'
        hint = ('<p class="warn">You opened this page as <code>%s</code>. A phone can\u2019t reach that. Open this page on the phone using your computer\u2019s Wi-Fi address instead (the server prints it when started with <code>--host 0.0.0.0</code>).</p>' % html.escape(host)) if local_only else ""
        page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Install the Cornerstone test app</title>
<style>:root{{color-scheme:light dark}}body{{font:16px/1.55 system-ui,sans-serif;max-width:560px;margin:0 auto;padding:1.5rem 1.2rem 3rem}}
h1{{font-size:1.5rem}}.dl{{display:block;background:#1f5f55;color:#fff;text-decoration:none;border-radius:10px;padding:1rem 1.2rem;margin:1rem 0}}
.dl b{{display:block;font-size:1.1rem}}.dl span{{opacity:.85;font-size:.9rem}}.warn{{background:rgba(241,199,91,.25);border-radius:8px;padding:.7rem .9rem}}
code{{background:rgba(128,128,128,.2);padding:.1rem .35rem;border-radius:4px;word-break:break-all}}li{{margin:.5rem 0}}.addr{{font-size:1.15rem}}</style></head><body>
<h1>Cornerstone Bible College<br>Test app</h1>
{hint}{items}
<h2>Install</h2><ol>
<li>Tap the download button above on your Android phone.</li>
<li>Open the downloaded file. If asked, allow your browser to <b>install unknown apps</b>.</li>
<li>Open <b>Cornerstone Portal (test)</b>. When it asks for the server address, enter:<br><code class="addr">{html.escape(address)}</code></li></ol>
<p>This is a test build for people on the same Wi-Fi as the server. Your phone may warn that the app isn't from the Play Store. That's expected for a test.</p>
</body></html>"""
        self.send(200, raw=page.encode(), ctype="text/html; charset=utf-8")

    def serve_file(self, conn, file_id):
        user = p.check_session(conn, self.token())
        if not user:
            return self.send(401, {"ok": False, "message": "Session expired. Please log in again."})
        try:
            name, full = portal_data.get_file(conn, user, int(file_id))
        except ValueError:
            return self.send(404, {"ok": False, "message": "File not found."})
        except portal_data.ApiError as e:
            return self.send(e.status, {"ok": False, "message": e.message})
        with open(full, "rb") as f: data = f.read()
        self.send(200, raw=data, ctype="application/octet-stream",
                  extra={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(name)})

    # ---- API ----
    def api(self, verb, name, query=""):
        conn = p.connect()
        try:
            if verb == "GET" and name == "ping":
                return self.send(200, {"ok": True, "server": "cornerstone"})
            if verb == "GET" and name == "me":
                u = p.check_session(conn, self.token())
                if not u: return self.send(401, {"ok": False, "message": "Session expired. Please log in again."})
                return self.send(200, {"ok": True, "profile": p.profile(conn, u)})
            if verb == "GET" and name.startswith("files/"):                  # a submitted file (not JSON)
                return self.serve_file(conn, name[6:])
            if name not in ("register", "login", "logout", "profile"):      # every other page: see portal_api.py
                data = self.body(UPLOAD_BODY if name == "submissions" else MAX_BODY) if verb == "POST" else {}
                status, obj = portal_api.route(conn, verb, name, parse_qs(query), data, self.token())
                return self.send(status, obj)
            if verb != "POST": return self.send(405, {"ok": False, "message": "Method not allowed."})
            d = self.body()
            ip = self.client_address[0]
            if name == "register":
                if too_many(ip): return self.send(429, {"ok": False, "message": "Too many requests. Wait a minute and try again."})
                try: year = int(d.get("year", 1))
                except (TypeError, ValueError): year = 0
                ok, msg = p.register_student(conn, str(d.get("name", "")), str(d.get("email", "")), str(d.get("idNumber", "")),
                                             str(d.get("regNumber", "")), year, str(d.get("password", "")))
                return self.send(200 if ok else 400, {"ok": ok, "message": msg})
            if name == "login":
                if too_many(ip): return self.send(429, {"ok": False, "message": "Too many requests. Wait a minute and try again."})
                portal = d.get("portal") if d.get("portal") in ("student", "tutor") else "student"
                method = d.get("method") if d.get("method") in ("email", "id_number", "registration_number") else "email"
                ok, msg, tok = p.login(conn, portal, method, str(d.get("identifier", "")), str(d.get("password", "")),
                                       ip, self.headers.get("User-Agent", "")[:200])
                if not ok: return self.send(401, {"ok": False, "message": msg})
                u = p.check_session(conn, tok)
                return self.send(200, {"ok": True, "message": msg, "token": tok, "profile": p.profile(conn, u)})
            if name == "logout":
                p.logout(conn, self.token()); return self.send(200, {"ok": True})
            if name == "profile":
                u = p.check_session(conn, self.token())
                if not u or u["role"] != "student": return self.send(401, {"ok": False, "message": "Please log in again."})
                try: year = int(d.get("year"))
                except (TypeError, ValueError): year = 0
                ok = p.set_year(conn, u["id"], year)
                return self.send(200 if ok else 400, {"ok": ok})
            return self.send(404, {"ok": False, "message": "Not found."})
        except (ValueError, json.JSONDecodeError):
            return self.send(400, {"ok": False, "message": "Bad request."})
        except Exception as e:                                               # never leak internals to the browser
            print("Server error:", repr(e))
            return self.send(500, {"ok": False, "message": "Something went wrong on the server."})
        finally:
            conn.close()

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("10.255.255.255", 1)); ip = s.getsockname()[0]; s.close(); return ip
    except OSError: return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to let phones on your Wi-Fi connect")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    if not os.path.exists(p.DB):
        print("portal.db not found, building it with demo data..."); p.demo(p.build()).close()
    else:                                                                    # bring an older database up to date, keeping its data
        _c = p.connect()
        if p.needs_upgrade(_c):
            print("Upgrading portal.db to the latest design. Backup saved as", os.path.basename(p.backup_database()))
        p.migrate(_c); _c.close()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f"Portal running at http://localhost:{a.port}")
    if a.host == "0.0.0.0" and lan_ip():
        print(f"On your phone (same Wi-Fi): http://{lan_ip()}:{a.port}")
        print(f"Test app download page:      http://{lan_ip()}:{a.port}/download")
    else:
        print(f"Test app download page:      http://localhost:{a.port}/download  (use --host 0.0.0.0 for phones)")
    print("Press Ctrl+C to stop.")
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\nStopped.")
