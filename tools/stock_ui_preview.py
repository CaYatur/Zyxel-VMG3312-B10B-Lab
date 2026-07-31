from __future__ import annotations

import argparse
import html
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

MODEL = "VMG3312-B10B"

TRANSLATIONS = {
    "MLG_Common_Login_Str1": "Login - ",
    "MLG_Common_Login_Str2": "Welcome",
    "MLG_Common_Login_Str3": "Welcome to {{1}} configuration interface.",
    "MLG_Common_Login_Str5": "Enter your administrator credentials.",
    "MLG_Common_Username": "Username",
    "MLG_Common_Password": "Password",
    "MLG_Common_Login": "Login",
    "MLG_Common_Login_AlertMsg_Str1": "Username is required.",
    "MLG_Common_Login_AlertMsg_Str2": "Password is required.",
    "MLG_Common_Login_AlertMsg_Str3": "Invalid username or password.",
    "MLG_Common_Login_AlertMsg_Str4": "The value is too long.",
    "MLG_Common_Login_AlertMsg_Str14": "The account is locked.",
}

TEMPLATE_RE = re.compile(r"<%(.*?)%>", re.S)
FORM_ACTION_RE = re.compile(
    r"(<form\b[^>]*?\saction\s*=\s*)([\"'])(.*?)(\2)", re.I | re.S
)


def render_expression(expression: str) -> str:
    expr = re.sub(r"\s+", " ", expression).strip()

    ml = re.fullmatch(r"ejGetML\(([^)]+)\)", expr)
    if ml:
        key = ml.group(1).strip()
        return html.escape(TRANSLATIONS.get(key, key.replace("MLG_", "").replace("_", " ")))

    get_value = re.fullmatch(r"ejGet\(([^)]+)\)", expr)
    if get_value:
        key = get_value.group(1).strip()
        values = {
            "modelName": MODEL,
            "loginStatus": "0",
            "wpakeyLoginMsg": "0",
            "currUserName": "preview",
            "pageIndex": "0",
        }
        return html.escape(values.get(key, "0"))

    other = re.fullmatch(r"ejGetOther\(([^,]+),\s*([^)]+)\)", expr)
    if other:
        key = other.group(2).strip()
        values = {
            "forEircom": "0",
            "checkloginlength": "0",
            "TTNETfeature": "1",
        }
        return html.escape(values.get(key, "0"))

    if expr.startswith(("if ", "else", "endif", "ejSet", "ejExec")):
        return ""

    return "0"


def transform_html(data: bytes) -> bytes:
    text = data.decode("iso-8859-1", "replace")
    text = TEMPLATE_RE.sub(lambda match: render_expression(match.group(1)), text)
    text = FORM_ACTION_RE.sub(r"\1\2/__preview_blocked__\4", text)

    notice = """
<div id="caya-preview-banner" style="position:fixed;z-index:999999;left:0;right:0;bottom:0;padding:8px 12px;background:#fff3cd;color:#664d03;border-top:1px solid #ffecb5;font:13px Arial,sans-serif;text-align:center">
CaYaRouter Lab offline preview — forms and configuration changes are disabled.
</div>
<script>
document.addEventListener('submit', function (event) {
  event.preventDefault();
  alert('Offline preview: configuration changes are disabled.');
}, true);
</script>
"""
    body_end = text.lower().rfind("</body>")
    if body_end >= 0:
        text = text[:body_end] + notice + text[body_end:]
    else:
        text += notice
    return text.encode("utf-8")


def safe_file(root: Path, request_path: str) -> Path | None:
    parsed = urlparse(request_path)
    decoded = unquote(parsed.path)
    pure = PurePosixPath(decoded)
    if pure.is_absolute():
        pure = PurePosixPath(*pure.parts[1:])
    if any(part in {"", ".", ".."} for part in pure.parts):
        return None
    candidate = root.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve()
        root_resolved = root.resolve()
    except OSError:
        return None
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return None
    return resolved


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = "CaYaStockUIPreview/0.1"

    @property
    def root(self) -> Path:
        return self.server.root  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/login/login.html")
            self.end_headers()
            return

        if parsed.path == "/__preview_blocked__":
            self.send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Offline preview is read-only")
            return

        target = safe_file(self.root, self.path)
        if target is None or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Preview resource not found")
            return

        data = target.read_bytes()
        suffix = target.suffix.lower()
        if suffix in {".html", ".htm"}:
            data = transform_html(data)
            content_type = "text/html; charset=utf-8"
        else:
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_POST(self) -> None:
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED, "Offline preview is read-only")

    def do_PUT(self) -> None:
        self.do_POST()

    def do_DELETE(self) -> None:
        self.do_POST()

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} - {fmt % args}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a read-only preview of the extracted Zyxel UI")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8090, type=int)
    args = parser.parse_args()

    if not args.root.is_dir():
        parser.error(f"UI root does not exist: {args.root}")

    server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
    server.root = args.root.resolve()  # type: ignore[attr-defined]
    print(
        f"Read-only stock UI preview: http://{args.host}:{args.port}/ "
        f"(root={server.root})",
        flush=True,
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
