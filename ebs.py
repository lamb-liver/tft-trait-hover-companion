#!/usr/bin/env python3
"""Broadcast ids and boxes. No screenshots, no descriptions.

/frame is the viewer path: the Chrome extension POSTs one PNG of the player it
is showing, this process matches it and answers ids and boxes. The PNG is read
in memory and dropped; nothing is written or forwarded. /push and /live stay for
the streamer relay; the viewer path does not use them.

The companion POSTs. Viewers subscribe on /live and cannot change boxes.
Loopback only. ponytail: plain HTTP and WebSocket on 127.0.0.1. Upgrade:
terminate TLS in front of this process; /push and /live stay the same.
"""

import base64
import concurrent.futures
import hashlib
import json
import os
import re
import queue
import secrets
import select
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# The batched shortlist runs inside our own thread pools; a second layer of BLAS threads
# oversubscribes the cores and is slower (0.65 s vs 0.40 s per frame on 8 cores).
for _blas in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_blas, "1")

from relay import _offer, clean_hits

ROOT = Path(__file__).resolve().parent
EXT = ROOT / "extension"
DATA = ROOT / "data"
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
MAX_BODY = 64 * 1024
# A 1920-wide PNG of a busy frame is 3-5 MB.
MAX_FRAME = 12 * 1024 * 1024
MAX_WIDTH = 1920
# Decoded size cap, read from the PNG header before decoding: a small PNG can
# claim a huge canvas (decompression bomb). 8K is far above any player picture.
MAX_PIXELS = 7680 * 4320
MAX_T = 10_000_000_000_000
# Trait scales were measured on 3840x2160 captures. A 1920 frame scaled back up
# with cubic finds all 13 fixture badges; matching it at 1920 finds none.
TRAIT_WIDTH = 3840
MAX_CLIENTS = 32
LOOPBACK = ("127.0.0.1", "::1", "localhost")

state = {"type": "update", "t": 0, "boxes": []}
clients = []
lock = threading.Lock()


def clean_update(body):
    if not isinstance(body, dict) or body.get("type") != "update":
        raise ValueError("type")
    when = body.get("t")
    if isinstance(when, bool) or not isinstance(when, int) or when < 0 or when > MAX_T:
        raise ValueError("t")
    return {"type": "update", "t": when, "boxes": clean_hits(body.get("boxes"))}


def publish(message):
    text = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    with lock:
        state.clear()
        state.update(message)
        for client in clients:
            _offer(client["queue"], text)
    return message


def _recvn(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _read_frame(sock):
    head = _recvn(sock, 2)
    if head is None:
        return None
    opcode = head[0] & 0x0F
    length = head[1] & 0x7F
    if length == 126:
        got = _recvn(sock, 2)
        if got is None:
            return None
        length = struct.unpack("!H", got)[0]
    elif length == 127:
        got = _recvn(sock, 8)
        if got is None:
            return None
        length = struct.unpack("!Q", got)[0]
    if length > MAX_BODY:
        return None
    mask = _recvn(sock, 4) if head[1] & 0x80 else b""
    if mask is None:
        return None
    data = _recvn(sock, length) if length else b""
    if data is None:
        return None
    if mask:
        data = bytes(byte ^ mask[i % 4] for i, byte in enumerate(data))
    return opcode, data


def _send_frame(wfile, opcode, data):
    # Write through the request buffer. A raw send on the socket races that buffer.
    n = len(data)
    if n < 126:
        header = bytes([0x80 | opcode, n])
    elif n < 65536:
        header = bytes([0x80 | opcode, 126]) + struct.pack("!H", n)
    else:
        return False
    try:
        with lock:
            wfile.write(header + data)
            wfile.flush()
    except OSError:
        return False
    return True


# ponytail: matching stays in Python. 36 traits x 2 polarities x 6 sizes plus
# 590 augment glyphs is OpenCV work; in extension JS it would take tens of
# seconds and become a second threshold. Move it only after a measurement shows
# the extension can match a frame inside the same gate (0.72).
_frame_lock = threading.Lock()
_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
_templates = {}


def templates():
    import companion

    if not _templates:
        _templates["traits"] = companion.load_templates()
        _templates["augments"] = companion.load_augment_templates()
    return _templates["traits"], _templates["augments"]


def png_size(data):
    """(width, height) from a PNG's IHDR, or None if it is not a PNG."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack("!II", data[16:24])


RAW_MAGIC = b"RGBA"
RAW_HEADER = 12


def raw_size(data):
    """(width, height) of b"RGBA" + u32 width + u32 height + RGBA rows, or None."""
    if len(data) < RAW_HEADER or data[:4] != RAW_MAGIC:
        return None
    width, height = struct.unpack("!II", data[4:12])
    if width < 2 or height < 2 or width * height > MAX_PIXELS or len(data) != RAW_HEADER + width * height * 4:
        raise ValueError("raw")
    return width, height


# A paused stream or a still scene sends the same picture every tick. A 160x90
# gray thumbnail, quantized to 64 levels, stands for the frame: if it is equal to
# the last matched frame's, reuse those boxes instead of matching again. Any
# change the matcher could see (a 40 px badge at 1080 is ~3 thumbnail cells)
# changes the thumbnail. REUSE_SECONDS bounds how long one result is reused.
DIGEST_SIZE = (160, 90)
REUSE_SECONDS = 2.0
_last_frame = {}
# The live /frame stream is one player in order: carry the trait band between
# frames (companion.match). Tools and tests call match_frame without it.
# Off by default: 2026-10-22 it gave no speed-up at zero difference (ADR-0002).
_track = {} if os.environ.get("TFT_TRACK") == "1" else None


def frame_digest(frame):
    import cv2

    gray = cv2.cvtColor(cv2.resize(frame, DIGEST_SIZE, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    return hashlib.sha1(str(frame.shape).encode() + (gray >> 2).tobytes()).hexdigest()


def match_frame(png, track=None):
    """PNG bytes of the player picture -> boxes on that picture. The image stays in memory."""
    import cv2
    import numpy as np

    import companion

    raw = raw_size(png)
    if raw is not None:
        # Uncompressed RGBA from the extension: same pixels as the PNG, without
        # ~63 ms of canvas PNG encode in Chrome and ~22 ms of decode here.
        w, h = raw
        rgba = np.frombuffer(png, np.uint8, count=w * h * 4, offset=RAW_HEADER).reshape(h, w, 4)
        frame = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
    else:
        size = png_size(png)
        if size is None or size[0] * size[1] > MAX_PIXELS:
            raise ValueError("png")
        frame = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
    if frame is None or frame.shape[0] < 2 or frame.shape[1] < 2:
        raise ValueError("png")
    height, width = frame.shape[:2]
    if width > MAX_WIDTH:
        frame = cv2.resize(frame, (MAX_WIDTH, max(1, round(height * MAX_WIDTH / width))), interpolation=cv2.INTER_AREA)
        height, width = frame.shape[:2]
    digest = frame_digest(frame)
    now = time.monotonic()
    last = _last_frame
    if last and last["digest"] == digest and now - last["at"] <= REUSE_SECONDS:
        return [dict(box) for box in last["boxes"]]
    traits, augments = templates()
    scale = TRAIT_WIDTH / width
    big = cv2.resize(frame, (TRAIT_WIDTH, max(1, round(height * scale))), interpolation=cv2.INTER_CUBIC)
    # Traits and augment cards read different crops of the same frame; OpenCV drops
    # the GIL, so run them side by side. Same calls, same results, less wait.
    slots = _pool.submit(companion.match_slots, frame, augments)
    hits = companion.one_per_slot(companion.one_column(companion.match(big, traits, track), width / height))
    # Internal only: a trait hit must sit on a badge fill (tier never leaves ebs).
    hits = [hit for hit in hits if companion.badge_tier(big, hit) is not None]
    hits = companion.tight_column(hits, width / height)
    hits = companion.verify_slots(big, companion.list_from_top(hits, width / height), traits)
    hits.extend(slots.result())
    boxes = clean_hits(hits)
    _last_frame.clear()
    _last_frame.update(digest=digest, at=now, boxes=[dict(box) for box in boxes])
    return boxes


# /version answers this; the extension refuses a matcher whose protocol differs.
APP_VERSION = "0.4.6"
PROTOCOL = 1
EXTENSION_ID = re.compile(r"^[a-p]{32}$")


def pinned_origin(extension_id="", origin=""):
    """--extension-id / TFT_EXTENSION_ID / data/extension_id -> chrome-extension://<id>.
    An explicit --origin still wins. Empty means unpinned (development only)."""
    if origin:
        return origin
    extension_id = (extension_id or os.environ.get("TFT_EXTENSION_ID", "")).strip()
    if not extension_id:
        path = DATA / "extension_id"
        if path.is_file():
            extension_id = path.read_text(encoding="utf-8").strip()
    if not extension_id:
        return ""
    if not EXTENSION_ID.match(extension_id):
        raise SystemExit("extension id 應該是 32 個 a-p 小寫字母（chrome://extensions 上那串）。")
    return "chrome-extension://" + extension_id


def allowed_origin(origin, pinned):
    """Pinned: only that extension, and a request without Origin (any local
    program) is refused too. Unpinned: any extension or no Origin (development)."""
    if pinned:
        return origin == pinned
    if not origin:
        return True
    return origin.startswith("chrome-extension://")


class Handler(BaseHTTPRequestHandler):
    token = ""
    origin = ""
    protocol_version = "HTTP/1.1"
    # A client that stalls mid-body must not hold a thread forever.
    timeout = 30

    def log_message(self, fmt, *args):
        return

    def _send(self, code, body, content_type):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.send_header("Connection", "close")
        try:
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            # The viewer stopped capture or reloaded mid-frame; nothing to answer.
            pass

    def _cors(self):
        origin = self.headers.get("Origin", "")
        if origin and allowed_origin(origin, self.origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def do_OPTIONS(self):
        origin = self.headers.get("Origin", "")
        if self.path.split("?", 1)[0] != "/frame" or not allowed_origin(origin, self.origin):
            self._send(403, "origin", "text/plain")
            return
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()

    def _frame(self):
        from urllib.parse import parse_qs, urlsplit

        if not allowed_origin(self.headers.get("Origin", ""), self.origin):
            self._send(403, "origin", "text/plain")
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send(411, "length", "text/plain")
            return
        if length <= 0 or length > MAX_FRAME:
            self._send(413, "too big", "text/plain")
            return
        body = self.rfile.read(length)
        try:
            when = min(MAX_T, max(0, int(parse_qs(urlsplit(self.path).query).get("t", ["0"])[0])))
        except ValueError:
            when = 0
        if not _frame_lock.acquire(blocking=False):
            self._send(429, "busy", "text/plain")
            return
        try:
            boxes = match_frame(body, _track)
        except Exception:  # noqa: BLE001 - bad or truncated image (ValueError, cv2.error): answer, do not drop
            self._send(400, "bad", "text/plain")
            return
        finally:
            _frame_lock.release()
        reply = json.dumps({"type": "update", "t": when, "boxes": boxes}, separators=(",", ":"))
        self._send(200, reply, "application/json; charset=utf-8")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/frame":
            self._frame()
            return
        if path != "/push":
            self._send(404, "no", "text/plain")
            return
        if self.headers.get("Authorization", "") != f"Bearer {self.token}":
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
            message = clean_update(json.loads(self.rfile.read(length) or b"{}"))
        except (json.JSONDecodeError, ValueError, TypeError):
            self._send(400, "bad", "text/plain")
            return
        publish(message)
        self._send(204, b"", "text/plain")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            with lock:
                body = json.dumps(state, ensure_ascii=False)
            self._send(200, body, "application/json; charset=utf-8")
            return
        if path == "/live":
            self._live()
            return
        if path == "/version":
            if not allowed_origin(self.headers.get("Origin", ""), self.origin):
                self._send(403, "origin", "text/plain")
                return
            body = json.dumps({"app": "tft-trait-hover", "version": APP_VERSION, "protocol": PROTOCOL})
            self._send(200, body, "application/json; charset=utf-8")
            return
        if path == "/catalog.json":
            body = json.dumps(trait_catalog(), ensure_ascii=False)
            self._send(200, body, "application/json; charset=utf-8")
            return
        file_map = {
            "/": EXT / "video_overlay.html",
            "/video_overlay.html": EXT / "video_overlay.html",
            "/video_overlay.js": EXT / "video_overlay.js",
            "/config.html": EXT / "config.html",
        }
        target = file_map.get(path)
        if target is None or not target.is_file():
            self._send(404, "no", "text/plain")
            return
        kind = {
            ".html": "text/html; charset=utf-8",
            ".js": "text/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }[target.suffix]
        self._send(200, target.read_bytes(), kind)

    def _live(self):
        key = self.headers.get("Sec-WebSocket-Key", "")
        upgrade = self.headers.get("Upgrade", "")
        if "websocket" not in upgrade.lower() or not key:
            self._send(400, "upgrade", "text/plain")
            return
        accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        client_queue = queue.Queue(1)
        with lock:
            if len(clients) >= MAX_CLIENTS:
                self._send(503, "busy", "text/plain")
                return
            clients.append({"queue": client_queue})
            current = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
        self.close_connection = True
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()
        self.wfile.flush()
        sock = self.connection
        try:
            if not _send_frame(self.wfile, 1, current.encode()):
                return
            while True:
                ready, _, _ = select.select([sock], [], [], 0.2)
                if ready:
                    frame = _read_frame(sock)
                    if frame is None or frame[0] == 8:
                        break
                    if frame[0] == 9 and not _send_frame(self.wfile, 0xA, frame[1]):
                        break
                try:
                    text = client_queue.get_nowait()
                except queue.Empty:
                    continue
                if not _send_frame(self.wfile, 1, text.encode()):
                    break
        except OSError:
            pass
        finally:
            with lock:
                clients[:] = [client for client in clients if client["queue"] is not client_queue]


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def trait_catalog():
    """Traits only, for the Twitch overlay page this process serves."""
    payload = json.loads((ROOT / "viewer" / "catalog.json").read_text(encoding="utf-8"))
    return {
        "version": payload.get("version"),
        "patch": payload.get("patch"),
        "set": payload.get("set"),
        "traits": payload.get("traits") or {},
    }


def extension_catalog():
    """The Chrome extension's own copy: traits and augments, names and public lines."""
    payload = json.loads((ROOT / "viewer" / "catalog.json").read_text(encoding="utf-8"))
    out = trait_catalog()
    out["augments"] = payload.get("augments") or {}
    try:
        import companion

        same = companion.same_icon_groups()
    except Exception:
        same = {}
    out["sameIcon"] = {rep: members for rep, members in same.items() if len(members) > 1}
    return out


def publish_traits():
    path = EXT / "catalog.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(extension_catalog(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def serve(host="127.0.0.1", port=8766, token=None, origin=""):
    if host not in LOOPBACK:
        raise SystemExit("廣播只聽 127.0.0.1。遠端走 Twitch，不連實況主機器。")
    global state, clients
    with lock:
        state = {"type": "update", "t": 0, "boxes": []}
        clients = []
    if token is None:
        token = secrets.token_urlsafe(16)
        path = DATA / "ebs.token"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token + "\n", encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    Handler.token = token
    Handler.origin = origin
    httpd = Server((host, port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    httpd.token = token
    return httpd


def main():
    import sys

    origin = ""
    if "--origin" in sys.argv:
        origin = sys.argv[sys.argv.index("--origin") + 1]
    extension_id = ""
    if "--extension-id" in sys.argv:
        extension_id = sys.argv[sys.argv.index("--extension-id") + 1]
    origin = pinned_origin(extension_id, origin)
    if not origin:
        print("注意：沒有鎖定擴充功能 ID，任何擴充功能都能送畫面。上架版請加 --extension-id <id>。", flush=True)
    missing = [p for p in (ROOT / "viewer" / "catalog.json", DATA / "set.json") if not p.is_file()]
    if missing or not any((DATA / "augments").glob("*.png")):
        print("找不到圖示目錄。請先執行一次：python companion.py fetch（Windows：.venv\\Scripts\\python companion.py fetch）", flush=True)
        print("Catalog missing. Run once first: python companion.py fetch", flush=True)
        sys.exit(1)
    httpd = serve(origin=origin)
    templates()
    port = httpd.server_address[1]
    print(f"frame http://127.0.0.1:{port}/frame", flush=True)
    print(f"ebs ws://127.0.0.1:{port}/live", flush=True)
    print("token 寫在 data/ebs.token", flush=True)
    threading.Event().wait()


if __name__ == "__main__":
    main()
