from __future__ import annotations

import argparse
import hashlib
import html
import http.client
import json
import re
import time
import urllib.parse
from collections import deque
from pathlib import Path
from typing import Any

from windows_dpapi_store import load_credentials

HOST = "192.168.1.1"
PORT = 80
SOURCE_IP = "192.168.1.2"
USER_AGENT = "CaYa-Zyxel-ReadOnly-Inventory/0.1"

DENY_TOKENS = {
    "logout",
    "reboot",
    "restart",
    "reset",
    "factory",
    "upgrade",
    "firmware",
    "upload",
    "restore",
    "delete",
    "remove",
    "apply",
    "save",
    "commit",
    "write",
    "backup",
    "downloadconfig",
    "diagnostic",
    "pingtest",
    "traceroute",
    "wol",
}

SENSITIVE_NAMES = re.compile(
    r"(?:pass|password|passwd|secret|key|psk|pin|token|cookie|credential|"
    r"pppoe|username|auth|serial|mac|imei)",
    re.I,
)

TEXT_SECRET_PATTERNS = [
    re.compile(r"(?i)(password|parola|şifre|secret|psk|wpa key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)(pppoe\s*(?:user(?:name)?|password))\s*[:=]\s*\S+"),
]


def redact_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    for pattern in TEXT_SECRET_PATTERNS:
        value = pattern.sub(lambda m: f"{m.group(1)}: [REDACTED]", value)
    return value


def safe_path(raw: str, base: str = "/") -> str | None:
    if not raw or raw.startswith(("#", "javascript:", "mailto:", "data:")):
        return None
    absolute = urllib.parse.urljoin(base, html.unescape(raw))
    parsed = urllib.parse.urlparse(absolute)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc and parsed.hostname not in {HOST, "127.0.0.1", "localhost"}:
        return None
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    lowered = path.lower()
    if any(token in lowered for token in DENY_TOKENS):
        return None
    if path.startswith("//"):
        return None
    return path


class ModemSession:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.cookies: dict[str, str] = {}

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def request(
        self, method: str, path: str, body: bytes | None = None, extra_headers: dict[str, str] | None = None
    ) -> tuple[int, list[tuple[str, str]], bytes]:
        headers = {"User-Agent": USER_AGENT, "Connection": "close"}
        if self.cookies:
            headers["Cookie"] = self._cookie_header()
        if extra_headers:
            headers.update(extra_headers)
        conn = http.client.HTTPConnection(
            HOST, PORT, timeout=10, source_address=(SOURCE_IP, 0)
        )
        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            data = response.read(2_000_000)
            response_headers = response.getheaders()
            for key, value in response_headers:
                if key.lower() == "set-cookie":
                    pair = value.split(";", 1)[0]
                    if "=" in pair:
                        name, cookie_value = pair.split("=", 1)
                        self.cookies[name.strip()] = cookie_value.strip()
            return response.status, response_headers, data
        finally:
            conn.close()

    def login(self) -> dict[str, Any]:
        form = urllib.parse.urlencode(
            {"AuthName": self.username, "AuthPassword": self.password}
        ).encode("ascii")
        status, headers, body = self.request(
            "POST",
            "/login/login-page.cgi",
            form,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        text = body.decode("iso-8859-1", "replace")
        visible = redact_text(re.sub(r"<[^>]+>", " ", text))
        failed = any(
            marker in visible.lower()
            for marker in ("yanlıştır", "yanlistir", "incorrect", "invalid password")
        )
        location = next(
            (value for key, value in headers if key.lower() == "location"), None
        )
        return {
            "status": status,
            "location": location,
            "cookie_names": sorted(self.cookies),
            "success": bool(self.cookies) and not failed,
        }


def extract_page(path: str, status: int, headers: list[tuple[str, str]], body: bytes) -> dict[str, Any]:
    content_type = next(
        (value for key, value in headers if key.lower() == "content-type"), ""
    )
    record: dict[str, Any] = {
        "path": path,
        "status": status,
        "content_type": content_type,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "links": [],
        "script_paths": [],
        "forms": [],
        "field_names": [],
        "title": None,
        "text_preview": "",
    }
    if not any(kind in content_type.lower() for kind in ("text", "html", "javascript", "json", "xml")):
        return record

    text = body.decode("iso-8859-1", "replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if title_match:
        record["title"] = redact_text(re.sub(r"<[^>]+>", " ", title_match.group(1)))

    extracted_links: set[str] = set()
    for match in re.finditer(
        r"(?:href|src|action)\s*=\s*[\"']([^\"']+)", text, re.I
    ):
        candidate = safe_path(match.group(1), path)
        if candidate:
            extracted_links.add(candidate)
    for match in re.finditer(
        r"[\"']((?:/|\.\.?/)[^\"']+\.(?:html?|cgi|js|css|json|xml)(?:\?[^\"']*)?)[\"']",
        text,
        re.I,
    ):
        candidate = safe_path(match.group(1), path)
        if candidate:
            extracted_links.add(candidate)
    record["links"] = sorted(extracted_links)

    script_paths = re.findall(r"<script[^>]+src=[\"']([^\"']+)", text, re.I)
    record["script_paths"] = sorted(
        candidate
        for candidate in {safe_path(item, path) for item in script_paths}
        if candidate
    )

    forms: list[dict[str, Any]] = []
    fields: set[str] = set()
    for form_match in re.finditer(r"<form\b([^>]*)>(.*?)</form>", text, re.I | re.S):
        attrs, content = form_match.groups()
        action_match = re.search(r"action\s*=\s*[\"']([^\"']*)", attrs, re.I)
        method_match = re.search(r"method\s*=\s*[\"']([^\"']*)", attrs, re.I)
        action = action_match.group(1) if action_match else None
        method = (method_match.group(1) if method_match else "GET").upper()
        field_records: list[dict[str, Any]] = []
        for input_match in re.finditer(
            r"<(?:input|select|textarea)\b([^>]*)>", content, re.I
        ):
            input_attrs = input_match.group(1)
            name_match = re.search(r"name\s*=\s*[\"']([^\"']*)", input_attrs, re.I)
            type_match = re.search(r"type\s*=\s*[\"']([^\"']*)", input_attrs, re.I)
            name = name_match.group(1) if name_match else None
            field_type = type_match.group(1) if type_match else None
            if name:
                fields.add(name)
            field_records.append(
                {
                    "name": name,
                    "type": field_type,
                    "sensitive": bool(name and SENSITIVE_NAMES.search(name)),
                }
            )
        forms.append(
            {
                "method": method,
                "action": action,
                "safe_to_fetch": method == "GET" and bool(safe_path(action or "", path)),
                "fields": field_records,
            }
        )
    record["forms"] = forms
    record["field_names"] = sorted(fields)

    visible = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    visible = re.sub(r"<style\b.*?</style>", " ", visible, flags=re.I | re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    record["text_preview"] = redact_text(html.unescape(visible))[:3000]
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-pages", type=int, default=220)
    args = parser.parse_args()

    credentials = load_credentials(args.credentials)
    session = ModemSession(credentials["username"], credentials["password"])
    login_result = session.login()
    if not login_result["success"]:
        print(json.dumps({"login": login_result}, ensure_ascii=False))
        return 2

    queue: deque[str] = deque(["/index.html", "/"])
    seen: set[str] = set()
    pages: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    while queue and len(seen) < args.max_pages:
        path = queue.popleft()
        if path in seen:
            continue
        seen.add(path)
        try:
            status, headers, body = session.request("GET", path)
            page = extract_page(path, status, headers, body)
            pages.append(page)
            for link in page["links"]:
                if link not in seen and link not in queue:
                    queue.append(link)
            time.sleep(0.08)
        except Exception as exc:
            errors.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})

    categories = {
        "system": [],
        "firmware": [],
        "network": [],
        "dsl_wan": [],
        "wifi": [],
        "lan_dhcp": [],
        "security_nat": [],
        "usb": [],
        "maintenance": [],
        "unknown": [],
    }
    category_tokens = {
        "system": ("system", "status", "deviceinfo", "networkmap", "monitor"),
        "firmware": ("firmware", "software", "version"),
        "network": ("network", "interface", "route", "arp"),
        "dsl_wan": ("dsl", "wan", "adsl", "vdsl", "ppp"),
        "wifi": ("wireless", "wifi", "wlan", "ssid"),
        "lan_dhcp": ("lan", "dhcp", "client"),
        "security_nat": ("firewall", "nat", "port", "security", "filter"),
        "usb": ("usb", "samba", "storage", "printer", "dlna"),
        "maintenance": ("maintenance", "log", "time", "user", "account"),
    }
    for page in pages:
        lowered = page["path"].lower()
        assigned = False
        for category, tokens in category_tokens.items():
            if any(token in lowered for token in tokens):
                categories[category].append(page["path"])
                assigned = True
        if not assigned:
            categories["unknown"].append(page["path"])

    report = {
        "generated_at_unix": int(time.time()),
        "target": {"model_hint": "VMG3312-B10B", "host": HOST, "source_ip": SOURCE_IP},
        "safety": {
            "login_post_only": True,
            "other_requests": "GET only",
            "blocked_tokens": sorted(DENY_TOKENS),
            "credentials_stored_in_report": False,
            "cookies_stored_in_report": False,
        },
        "login": login_result,
        "summary": {
            "pages_fetched": len(pages),
            "errors": len(errors),
            "discovered_unique_paths": len(seen),
            "queued_remaining": len(queue),
        },
        "categories": {key: sorted(set(value)) for key, value in categories.items()},
        "pages": pages,
        "errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
