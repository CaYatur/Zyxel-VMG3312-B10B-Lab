from __future__ import annotations

import http.client
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8081
MODEM_HOST = "192.168.1.1"
MODEM_PORT = 80
SOURCE_IP = "192.168.1.2"

SESSION_LOCK = threading.Lock()
SESSION_COOKIE = ""

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


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _proxy(self) -> None:
        global SESSION_COOKIE

        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None

        incoming_cookie = self.headers.get("Cookie", "").strip()
        if incoming_cookie:
            with SESSION_LOCK:
                SESSION_COOKIE = incoming_cookie

        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            if key.lower() not in HOP_BY_HOP and key.lower() != "host":
                headers[key] = value
        if "Cookie" not in headers:
            with SESSION_LOCK:
                if SESSION_COOKIE:
                    headers["Cookie"] = SESSION_COOKIE
        headers["Host"] = MODEM_HOST
        headers["Connection"] = "close"

        conn = http.client.HTTPConnection(
            MODEM_HOST,
            MODEM_PORT,
            timeout=15,
            source_address=(SOURCE_IP, 0),
        )

        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            response = conn.getresponse()
            response_body = response.read()
            response_headers = response.getheaders()

            content_type = response.getheader("Content-Type", "").lower()
            content_encoding = response.getheader("Content-Encoding", "").lower()
            if not content_encoding and any(
                kind in content_type
                for kind in ("text/html", "text/css", "javascript", "application/json")
            ):
                response_body = response_body.replace(
                    b"http://192.168.1.1", b"http://127.0.0.1:8081"
                )
                response_body = response_body.replace(
                    b"https://192.168.1.1", b"http://127.0.0.1:8081"
                )

            self.send_response(response.status, response.reason)
            for key, value in response_headers:
                key_lower = key.lower()
                if key_lower in HOP_BY_HOP or key_lower == "content-length":
                    continue
                if key_lower == "location":
                    value = value.replace(
                        "http://192.168.1.1", "http://127.0.0.1:8081"
                    ).replace("https://192.168.1.1", "http://127.0.0.1:8081")
                elif key_lower == "set-cookie":
                    # Keep the modem session only in memory so read-only helper
                    # requests can reuse the browser-authenticated session.
                    cookie_pair = value.split(";", 1)[0].strip()
                    if cookie_pair:
                        with SESSION_LOCK:
                            SESSION_COOKIE = cookie_pair

                    # The modem may bind its session cookie to 192.168.1.1 and
                    # mark it Secure. The browser is talking to our local HTTP
                    # endpoint, so remove those attributes while preserving the
                    # actual session value and path.
                    parts = [part.strip() for part in value.split(";")]
                    kept = []
                    for part in parts:
                        lower = part.lower()
                        if lower.startswith("domain=") or lower == "secure":
                            continue
                        kept.append(part)
                    value = "; ".join(kept)
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(response_body)
        except Exception as exc:
            message = f"Zyxel proxy error: {type(exc).__name__}: {exc}\n".encode()
            self.send_response(502, "Bad Gateway")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(message)
        finally:
            conn.close()

    do_GET = _proxy
    do_POST = _proxy
    do_HEAD = _proxy

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} - {fmt % args}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    print(
        f"Zyxel local proxy: http://{LISTEN_HOST}:{LISTEN_PORT} -> "
        f"{MODEM_HOST}:{MODEM_PORT} via {SOURCE_IP}",
        flush=True,
    )
    server.serve_forever()
