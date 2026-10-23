#!/usr/bin/env python3
"""Local debug page. Not the viewer path.

The companion POSTs ids and boxes, and this process serves the capture so
the streamer can check alignment on this machine. Remote viewers use ebs.py
and the Twitch overlay. They never open this port.

GET /state, the event stream, and the static files are not authenticated.
Only a Bearer token can change boxes. The bind stays on loopback.
"""

import json
import queue
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VIEWER = ROOT / "viewer"
DATA = ROOT / "data"
MAX_BODY = 64 * 1024
MAX_CLIENTS = 32
MAX_PER_IP = 4

state = {"hits": []}
clients = []
lock = threading.Lock()


def client_count():
    with lock:
        return len(clients)


def clean_hits(raw):
    if not isinstance(raw, list) or len(raw) > 64:
        raise ValueError("hits")
    out = []
    for hit in raw:
        if not isinstance(hit, dict) or not isinstance(hit.get("id"), str) or not hit["id"]:
            raise ValueError("hit")
        box = {"id": hit["id"]}
        for key in ("x", "y", "w", "h"):
            number = hit.get(key)
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise ValueError(key)
            box[key] = float(number)
        if not (
            0 <= box["x"] <= 1
            and 0 <= box["y"] <= 1
            and 0 < box["w"] <= 1
            and 0 < box["h"] <= 1
            and box["x"] + box["w"] <= 1.01
            and box["y"] + box["h"] <= 1.01
        ):
            raise ValueError("box")
        # exact: a same-icon augment narrowed to one variant (pick round). Only True passes.
        if hit.get("exact") is True:
            box["exact"] = True
        out.append(box)
    return out


def _offer(client_queue, text):
    try:
        client_queue.put_nowait(text)
        return
    except queue.Full:
        pass
    try:
        client_queue.get_nowait()
    except queue.Empty:
        pass
    try:
        client_queue.put_nowait(text)
    except queue.Full:
        pass


def publish(hits):
    payload = {"hits": clean_hits(hits)}
    text = json.dumps(payload, ensure_ascii=False)
    with lock:
        state.clear()
        state.update(payload)
        for client in clients:
            _offer(client["queue"], text)
    return payload


class Handler(BaseHTTPRequestHandler):
    token = ""
    heartbeat = 5.0
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    def _send(self, code, body, content_type):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self):
        return self.headers.get("Authorization", "") == f"Bearer {self.token}"

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/state":
            self._send(404, "no", "text/plain")
            return
        if not self._authorized():
            self._send(401, "unauthorized", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send(411, "length", "text/plain")
            return
        if length < 0 or length > MAX_BODY:
            self._send(413, "too big", "text/plain")
            return
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            hits = clean_hits(body.get("hits") if isinstance(body, dict) else None)
        except (json.JSONDecodeError, ValueError, TypeError):
            self._send(400, "bad", "text/plain")
            return
        publish(hits)
        self._send(204, b"", "text/plain")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            with lock:
                body = json.dumps(state, ensure_ascii=False)
            self._send(200, body, "application/json; charset=utf-8")
            return
        if path == "/events":
            self._stream()
            return
        file_map = {
            "/": VIEWER / "index.html",
            "/overlay.js": VIEWER / "overlay.js",
            "/catalog.json": VIEWER / "catalog.json",
            "/frame.png": DATA / "frame.png",
        }
        target = file_map.get(path)
        if target is None or not target.is_file():
            self._send(404, "no", "text/plain")
            return
        kind = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
        }[target.suffix]
        self._send(200, target.read_bytes(), kind)

    def _stream(self):
        ip = self.client_address[0]
        client_queue = queue.Queue(1)
        with lock:
            same_ip = sum(client["ip"] == ip for client in clients)
            if len(clients) >= MAX_CLIENTS or same_ip >= MAX_PER_IP:
                self._send(503, "busy", "text/plain")
                return
            clients.append({"ip": ip, "queue": client_queue})
            current = json.dumps(state, ensure_ascii=False)
        # No Content-Length: stay on HTTP/1.0 so the client reads the stream
        # instead of waiting for a length.
        self.protocol_version = "HTTP/1.0"
        self.close_connection = True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(f"data: {current}\n\n".encode())
            self.wfile.flush()
            while True:
                try:
                    message = client_queue.get(timeout=self.heartbeat)
                    chunk = f"data: {message}\n\n".encode()
                except queue.Empty:
                    chunk = b":\n\n"
                self.wfile.write(chunk)
                self.wfile.flush()
        except OSError:
            pass
        finally:
            with lock:
                clients[:] = [client for client in clients if client["queue"] is not client_queue]


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(host="127.0.0.1", port=8765, token=None, heartbeat=5.0):
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise SystemExit("本機除錯只聽 127.0.0.1。遠端走 Twitch，不連實況主機器。")
    if token is None:
        token = secrets.token_urlsafe(16)
    Handler.token = token
    Handler.heartbeat = heartbeat
    httpd = Server((host, port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    httpd.token = token
    return httpd
