from __future__ import annotations

import argparse
import ast
import html
import http.client
import json
import re
import urllib.parse
from pathlib import Path

from windows_dpapi_store import load_credentials

HOST = "192.168.1.1"
SOURCE_IP = "192.168.1.2"
UA = "CaYa-Zyxel-Tab-Mapper/0.1"

BLOCKED_PAGE = re.compile(
    r"(?:firmware|upgrade|configuration|reboot|restart|reset|diagnostic|disagnostic|"
    r"backup|restore|upload|logout|apply|save|delete|remove|commit|write)",
    re.I,
)


class Session:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.cookies: dict[str, str] = {}

    def request(self, method: str, path: str, body: bytes | None = None, headers: dict[str, str] | None = None):
        h = {"User-Agent": UA, "Connection": "close"}
        if self.cookies:
            h["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if headers:
            h.update(headers)
        conn = http.client.HTTPConnection(HOST, 80, timeout=10, source_address=(SOURCE_IP, 0))
        try:
            conn.request(method, path, body=body, headers=h)
            r = conn.getresponse()
            data = r.read(2_000_000)
            hs = r.getheaders()
            for k, v in hs:
                if k.lower() == "set-cookie":
                    pair = v.split(";", 1)[0]
                    if "=" in pair:
                        n, val = pair.split("=", 1)
                        self.cookies[n.strip()] = val.strip()
            return r.status, hs, data
        finally:
            conn.close()

    def login(self) -> None:
        payload = urllib.parse.urlencode({"AuthName": self.username, "AuthPassword": self.password}).encode()
        status, _, body = self.request(
            "POST", "/login/login-page.cgi", payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        if status != 200 or not self.cookies:
            raise RuntimeError("Login failed")
        low = body.decode("iso-8859-1", "replace").lower()
        if "yanlıştır" in low or "incorrect" in low:
            raise RuntimeError("Login rejected")


def parse_legacy_object(text: str):
    cleaned = text.lstrip("\ufeff").strip()
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.S)
    cleaned = re.sub(r"//.*?$", "", cleaned, flags=re.M)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    try:
        return ast.literal_eval(cleaned)
    except Exception:
        pass
    normalized = re.sub(r"'([^']*)'", lambda m: json.dumps(m.group(1)), cleaned)
    normalized = re.sub(r",\s*([}\]])", r"\1", normalized)
    return json.loads(normalized)


def collect_tab_paths(obj) -> list[str]:
    paths: list[str] = []
    def walk(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k == "url" and isinstance(v, str) and "tabJson=" in v:
                    q = urllib.parse.parse_qs(urllib.parse.urlparse(v).query)
                    for item in q.get("tabJson", []):
                        absolute = urllib.parse.urljoin("/pages/tabFW/", item)
                        paths.append(absolute)
                walk(v)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(obj)
    return sorted(set(paths))


def collect_page_urls(value, base: str) -> set[str]:
    result: set[str] = set()
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "url" and isinstance(v, str):
                    absolute = urllib.parse.urljoin(base, v)
                    parsed = urllib.parse.urlparse(absolute)
                    path = parsed.path
                    if parsed.query:
                        path += "?" + parsed.query
                    if path.startswith("/"):
                        result.add(path)
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    walk(value)
    return result


def visible_text(body: bytes) -> str:
    text = body.decode("iso-8859-1", "replace")
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    text = re.sub(r"(?i)(password|parola|şifre|secret|psk|key)\s*[:=]\s*\S+", r"\1: [REDACTED]", text)
    return text[:3500]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--credentials", required=True, type=Path)
    ap.add_argument("--menu", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    creds = load_credentials(args.credentials)
    session = Session(creds["username"], creds["password"])
    session.login()

    menu = parse_legacy_object(args.menu.read_text(encoding="utf-8"))
    tab_paths = collect_tab_paths(menu)
    tabs = []
    page_paths: set[str] = {"/pages/connectionStatus/naviView_partialLoad.html"}

    for path in tab_paths:
        status, headers, body = session.request("GET", path)
        text = body.decode("utf-8", "replace")
        record = {"path": path, "status": status, "bytes": len(body), "parsed": None, "error": None}
        if status == 200:
            try:
                parsed = parse_legacy_object(text)
                record["parsed"] = parsed
                # Tab item URLs are resolved by the browser from tabFW.html,
                # not from the tab.json file's own directory.
                page_paths |= collect_page_urls(parsed, "/pages/tabFW/tabFW.html")
            except Exception as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
                record["preview"] = text[:1000]
        tabs.append(record)

    pages = []
    blocked = []
    for path in sorted(page_paths):
        if BLOCKED_PAGE.search(path):
            blocked.append(path)
            continue
        try:
            status, headers, body = session.request("GET", path)
            ctype = next((v for k, v in headers if k.lower() == "content-type"), "")
            text = body.decode("iso-8859-1", "replace")
            title_m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
            forms = []
            for m in re.finditer(r"<form\b([^>]*)>", text, re.I):
                attrs = m.group(1)
                mm = re.search(r"method\s*=\s*[\"']([^\"']+)", attrs, re.I)
                am = re.search(r"action\s*=\s*[\"']([^\"']+)", attrs, re.I)
                forms.append({"method": (mm.group(1) if mm else "GET").upper(), "action": am.group(1) if am else None})
            input_names = sorted(set(re.findall(r"<(?:input|select|textarea)[^>]+name=[\"']([^\"']+)", text, re.I)))
            pages.append({
                "path": path,
                "status": status,
                "content_type": ctype,
                "bytes": len(body),
                "title": html.unescape(re.sub(r"\s+", " ", title_m.group(1)).strip()) if title_m else None,
                "forms": forms,
                "input_names": input_names,
                "text_preview": visible_text(body),
            })
        except Exception as exc:
            pages.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})

    report = {
        "summary": {
            "tab_json_files": len(tab_paths),
            "discovered_page_paths": len(page_paths),
            "safe_pages_fetched": len(pages),
            "blocked_pages": len(blocked),
        },
        "tab_paths": tab_paths,
        "tabs": tabs,
        "blocked_pages": blocked,
        "pages": pages,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
