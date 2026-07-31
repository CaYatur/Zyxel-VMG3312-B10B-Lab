from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from windows_dpapi_store import load_credentials
from zyxel_backup_config import Session

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8092
MODEM_HOST = "192.168.1.1"
MODEM_PORT = 80
SOURCE_IP = "192.168.1.2"
UI_ROOT = Path("ui-prototype")
CREDENTIALS = Path(".caya-agent/zyxel_credentials.dpapi.json")

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

# These endpoints can erase settings, reboot the router, or replace firmware.
# They remain blocked until the user gives a separate final upload approval.
BLOCKED_PATH_FRAGMENTS = (
    "firmwareupgrade-upload.cgi",
    "firmwareupgrade-uploadpost.cgi",
    "configuration-restore.cgi",
    "configuration-reset.cgi",
    "reboot-reboot.cgi",
    "factorydefault",
)

SESSION_LOCK = threading.RLock()
SESSION_COOKIE = ""
LAST_LOGIN = 0.0


def _cookie_header(cookies: dict[str, str]) -> str:
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def refresh_session(force: bool = False) -> str:
    global SESSION_COOKIE, LAST_LOGIN
    with SESSION_LOCK:
        if not force and SESSION_COOKIE and time.time() - LAST_LOGIN < 300:
            return SESSION_COOKIE
        credentials = load_credentials(CREDENTIALS)
        session = Session(credentials["username"], credentials["password"])
        session.login()
        SESSION_COOKIE = _cookie_header(session.cookies)
        LAST_LOGIN = time.time()
        return SESSION_COOKIE


def is_blocked(path: str) -> bool:
    normalized = path.lower()
    return any(fragment in normalized for fragment in BLOCKED_PATH_FRAGMENTS)


class GatewayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _serve_ui(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/caya":
            self.send_response(HTTPStatus.PERMANENT_REDIRECT)
            self.send_header("Location", "/caya/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if parsed.path == "/caya/api/health":
            try:
                cookie = refresh_session()
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "model": "VMG3312-B10B",
                        "firmware": "1.00(AAPP.7)",
                        "modem": f"{MODEM_HOST}:{MODEM_PORT}",
                        "source_ip": SOURCE_IP,
                        "authenticated": bool(cookie),
                        "dangerous_writes_blocked": True,
                    },
                )
            except Exception as exc:
                self._send_json(
                    HTTPStatus.BAD_GATEWAY,
                    {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
                )
            return

        relative = unquote(parsed.path[len("/caya/") :]) or "index.html"
        candidate = (UI_ROOT / relative).resolve()
        root = UI_ROOT.resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "application/json",
        }:
            content_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _proxy(self, retry: bool = True) -> None:
        global SESSION_COOKIE
        parsed = urlsplit(self.path)
        if is_blocked(parsed.path):
            self._send_json(
                HTTPStatus.LOCKED,
                {
                    "ok": False,
                    "blocked": True,
                    "path": parsed.path,
                    "reason": "Riskli bakım işlemi son kullanıcı onayına kadar kilitli.",
                },
            )
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            key_lower = key.lower()
            if key_lower not in HOP_BY_HOP and key_lower not in {"host", "cookie", "content-length"}:
                headers[key] = value
        try:
            headers["Cookie"] = refresh_session()
        except Exception:
            pass
        headers["Host"] = MODEM_HOST
        headers["Connection"] = "close"
        if body is not None:
            headers["Content-Length"] = str(len(body))

        connection = http.client.HTTPConnection(
            MODEM_HOST,
            MODEM_PORT,
            timeout=30,
            source_address=(SOURCE_IP, 0),
        )
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            response_body = response.read()
            response_headers = response.getheaders()

            # An expired modem session usually returns the login page. Refresh
            # the server-side session once and repeat the original request.
            looks_like_login = b"login-page.cgi" in response_body.lower() or b"login/login.html" in response_body.lower()
            if retry and looks_like_login and self.command in {"GET", "HEAD"}:
                refresh_session(force=True)
                self._proxy(retry=False)
                return

            for key, value in response_headers:
                if key.lower() == "set-cookie":
                    cookie_pair = value.split(";", 1)[0].strip()
                    if cookie_pair:
                        with SESSION_LOCK:
                            existing = {
                                item.split("=", 1)[0]: item
                                for item in SESSION_COOKIE.split("; ")
                                if "=" in item
                            }
                            existing[cookie_pair.split("=", 1)[0]] = cookie_pair
                            SESSION_COOKIE = "; ".join(existing.values())

            content_type = response.getheader("Content-Type", "").lower()
            content_encoding = response.getheader("Content-Encoding", "").lower()
            if not content_encoding and any(
                kind in content_type
                for kind in ("text/html", "text/css", "javascript", "application/json")
            ):
                response_body = response_body.replace(
                    b"http://192.168.1.1", f"http://{LISTEN_HOST}:{LISTEN_PORT}".encode()
                ).replace(
                    b"https://192.168.1.1", f"http://{LISTEN_HOST}:{LISTEN_PORT}".encode()
                )

            self.send_response(response.status, response.reason)
            for key, value in response_headers:
                key_lower = key.lower()
                if key_lower in HOP_BY_HOP or key_lower in {"content-length", "set-cookie", "x-frame-options"}:
                    continue
                if key_lower == "location":
                    value = value.replace(
                        "http://192.168.1.1", f"http://{LISTEN_HOST}:{LISTEN_PORT}"
                    ).replace(
                        "https://192.168.1.1", f"http://{LISTEN_HOST}:{LISTEN_PORT}"
                    )
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(response_body)
        except Exception as exc:
            self._send_json(
                HTTPStatus.BAD_GATEWAY,
                {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
            )
        finally:
            connection.close()

    def _dispatch(self) -> None:
        if urlsplit(self.path).path.startswith("/caya"):
            self._serve_ui()
        else:
            self._proxy()

    do_GET = _dispatch
    do_POST = _dispatch
    do_HEAD = _dispatch
    do_PUT = _dispatch
    do_PATCH = _dispatch
    do_DELETE = _dispatch

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} - {fmt % args}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=LISTEN_HOST)
    parser.add_argument("--port", type=int, default=LISTEN_PORT)
    args = parser.parse_args()

    globals()["LISTEN_HOST"] = args.host
    globals()["LISTEN_PORT"] = args.port
    refresh_session(force=True)
    server = ThreadingHTTPServer((args.host, args.port), GatewayHandler)
    print(
        f"CaYa live gateway: http://{args.host}:{args.port}/caya/ -> "
        f"{MODEM_HOST}:{MODEM_PORT} via {SOURCE_IP}",
        flush=True,
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
