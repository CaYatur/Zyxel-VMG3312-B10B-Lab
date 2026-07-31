from __future__ import annotations

import argparse
import http.client
import json
import re
import urllib.parse
from pathlib import Path

from windows_dpapi_store import load_credentials

HOST = "192.168.1.1"
PORT = 80
SOURCE_IP = "192.168.1.2"
UA = "CaYa-Zyxel-Endpoint-Mapper/0.1"

DANGEROUS = re.compile(
    r"(?:logout|reboot|restart|reset|factory|upgrade|firmware|upload|restore|"
    r"delete|remove|apply|save|commit|write|backup|diagnostic|pingtest|"
    r"traceroute|wol|restart|reload)",
    re.I,
)


def safe_get_path(path: str) -> bool:
    if not path.startswith("/"):
        return False
    if DANGEROUS.search(path):
        return False
    return True


class Session:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.cookies: dict[str, str] = {}

    def request(self, method: str, path: str, body: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, list[tuple[str, str]], bytes]:
        h = {"User-Agent": UA, "Connection": "close"}
        if self.cookies:
            h["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if headers:
            h.update(headers)
        conn = http.client.HTTPConnection(HOST, PORT, timeout=10, source_address=(SOURCE_IP, 0))
        try:
            conn.request(method, path, body=body, headers=h)
            resp = conn.getresponse()
            data = resp.read(2_000_000)
            rh = resp.getheaders()
            for k, v in rh:
                if k.lower() == "set-cookie":
                    pair = v.split(";", 1)[0]
                    if "=" in pair:
                        n, value = pair.split("=", 1)
                        self.cookies[n.strip()] = value.strip()
            return resp.status, rh, data
        finally:
            conn.close()

    def login(self) -> None:
        payload = urllib.parse.urlencode({"AuthName": self.username, "AuthPassword": self.password}).encode()
        status, _, body = self.request(
            "POST",
            "/login/login-page.cgi",
            payload,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        if status != 200 or not self.cookies:
            raise RuntimeError("Login failed")
        text = body.decode("iso-8859-1", "replace").lower()
        if "yanlıştır" in text or "incorrect" in text:
            raise RuntimeError("Login rejected")


def extract_paths(text: str, base: str) -> set[str]:
    found: set[str] = set()
    patterns = [
        r"[\"']((?:/|\.\.?/)[^\"']+\.(?:html?|cgi|js|css|json|xml)(?:\?[^\"']*)?)[\"']",
        r"url\s*:\s*[\"']([^\"']+)[\"']",
        r"(?:href|src|action)\s*=\s*[\"']([^\"']+)[\"']",
        r"(?:open|load|get|post)\s*\(\s*[\"']([^\"']+)[\"']",
    ]
    for pattern in patterns:
        for raw in re.findall(pattern, text, re.I):
            absolute = urllib.parse.urljoin(base, raw)
            parsed = urllib.parse.urlparse(absolute)
            if parsed.hostname and parsed.hostname not in {HOST, "127.0.0.1", "localhost"}:
                continue
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            if path.startswith("/"):
                found.add(path)
    return found


def clean_text(body: bytes) -> str:
    text = body.decode("iso-8859-1", "replace")
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?i)(password|parola|şifre|secret|psk)\s*[:=]\s*\S+", r"\1: [REDACTED]", text)
    return text[:4000]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--credentials", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    creds = load_credentials(args.credentials)
    session = Session(creds["username"], creds["password"])
    session.login()

    seed_paths = ["/index.html"]
    fetched_sources: dict[str, str] = {}
    discovered: set[str] = set(seed_paths)

    status, _, body = session.request("GET", "/index.html")
    index_text = body.decode("iso-8859-1", "replace")
    fetched_sources["/index.html"] = index_text
    discovered |= extract_paths(index_text, "/index.html")

    script_paths = sorted(p for p in discovered if p.lower().endswith(".js"))
    for path in script_paths:
        if not safe_get_path(path):
            continue
        status, _, body = session.request("GET", path)
        if status == 200:
            text = body.decode("iso-8859-1", "replace")
            fetched_sources[path] = text
            discovered |= extract_paths(text, path)

    paths = sorted(discovered)
    probed: list[dict[str, object]] = []
    blocked: list[str] = []

    for path in paths:
        if path.endswith(('.js', '.css', '.gif', '.jpg', '.jpeg', '.png', '.ico')):
            continue
        if not safe_get_path(path):
            blocked.append(path)
            continue
        try:
            status, headers, body = session.request("GET", path)
            content_type = next((v for k, v in headers if k.lower() == "content-type"), "")
            title_match = re.search(r"<title[^>]*>(.*?)</title>", body.decode("iso-8859-1", "replace"), re.I | re.S)
            title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None
            forms = []
            text = body.decode("iso-8859-1", "replace")
            for match in re.finditer(r"<form\b([^>]*)>", text, re.I):
                attrs = match.group(1)
                method_m = re.search(r"method\s*=\s*[\"']([^\"']+)", attrs, re.I)
                action_m = re.search(r"action\s*=\s*[\"']([^\"']+)", attrs, re.I)
                forms.append({
                    "method": (method_m.group(1) if method_m else "GET").upper(),
                    "action": action_m.group(1) if action_m else None,
                })
            probed.append({
                "path": path,
                "status": status,
                "content_type": content_type,
                "bytes": len(body),
                "title": title,
                "forms": forms,
                "text_preview": clean_text(body),
            })
        except Exception as exc:
            probed.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})

    source_summary = []
    for path, text in fetched_sources.items():
        menu_terms = sorted(set(re.findall(r"['\"]([A-Za-z][A-Za-z0-9 _-]{2,40})['\"]", text)))
        source_summary.append({
            "path": path,
            "bytes": len(text.encode("iso-8859-1", "replace")),
            "extracted_path_count": len(extract_paths(text, path)),
            "menu_term_samples": menu_terms[:120],
        })

    report = {
        "target": {"host": HOST, "model": "VMG3312-B10B"},
        "safety": {"login_post_only": True, "all_probe_requests": "GET", "blocked_count": len(blocked)},
        "summary": {
            "source_files": len(fetched_sources),
            "discovered_paths": len(paths),
            "probed_paths": len(probed),
            "blocked_paths": len(blocked),
        },
        "blocked_paths": sorted(blocked),
        "source_summary": source_summary,
        "probed": probed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
