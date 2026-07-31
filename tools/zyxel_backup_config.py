from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import time
import urllib.parse
from pathlib import Path

from windows_dpapi_store import load_credentials

HOST = "192.168.1.1"
PORT = 80
SOURCE_IP = "192.168.1.2"
USER_AGENT = "CaYa-Zyxel-Config-Backup/0.1"
BACKUP_PATH = "/pages/tabFW/configuration-backupsettings.conf"


class Session:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.cookies: dict[str, str] = {}

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, list[tuple[str, str]], bytes]:
        request_headers = {
            "User-Agent": USER_AGENT,
            "Connection": "close",
        }
        if self.cookies:
            request_headers["Cookie"] = "; ".join(
                f"{name}={value}" for name, value in self.cookies.items()
            )
        if headers:
            request_headers.update(headers)

        conn = http.client.HTTPConnection(
            HOST,
            PORT,
            timeout=15,
            source_address=(SOURCE_IP, 0),
        )
        try:
            conn.request(method, path, body=body, headers=request_headers)
            response = conn.getresponse()
            data = response.read(8_000_000)
            response_headers = response.getheaders()
            for key, value in response_headers:
                if key.lower() != "set-cookie":
                    continue
                pair = value.split(";", 1)[0]
                if "=" in pair:
                    name, cookie_value = pair.split("=", 1)
                    self.cookies[name.strip()] = cookie_value.strip()
            return response.status, response_headers, data
        finally:
            conn.close()

    def login(self) -> None:
        form = urllib.parse.urlencode(
            {"AuthName": self.username, "AuthPassword": self.password}
        ).encode("ascii")
        status, _, body = self.request(
            "POST",
            "/login/login-page.cgi",
            form,
            {"Content-Type": "application/x-www-form-urlencoded"},
        )
        text = body.decode("iso-8859-1", "replace").lower()
        if status != 200 or not self.cookies:
            raise RuntimeError("Login failed: no authenticated session")
        if "yanlıştır" in text or "incorrect" in text or "invalid password" in text:
            raise RuntimeError("Login rejected")


def header_value(headers: list[tuple[str, str]], name: str) -> str | None:
    name_lower = name.lower()
    return next((value for key, value in headers if key.lower() == name_lower), None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    credentials = load_credentials(args.credentials)
    session = Session(credentials["username"], credentials["password"])
    session.login()

    status, headers, data = session.request("GET", BACKUP_PATH)
    content_type = header_value(headers, "Content-Type") or ""
    content_disposition = header_value(headers, "Content-Disposition") or ""

    lower_prefix = data[:8192].lower()
    looks_like_login = (
        b"authname" in lower_prefix
        and b"authpassword" in lower_prefix
        and b"login-page.cgi" in lower_prefix
    )

    if status != 200:
        raise RuntimeError(f"Backup endpoint returned HTTP {status}")
    if looks_like_login:
        raise RuntimeError("Backup endpoint returned the login page, not a backup")
    if not data:
        raise RuntimeError("Backup endpoint returned an empty file")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"VMG3312-B10B_config_{timestamp}.conf"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / filename
    output_path.write_bytes(data)

    digest = hashlib.sha256(data).hexdigest()
    metadata = {
        "model": "VMG3312-B10B",
        "source": BACKUP_PATH,
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file": filename,
        "bytes": len(data),
        "sha256": digest,
        "content_type": content_type,
        "content_disposition": content_disposition,
        "contains_credentials_or_network_secrets": True,
        "commit_to_git": False,
    }
    metadata_path = output_path.with_suffix(output_path.suffix + ".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "backup": str(output_path),
                "metadata": str(metadata_path),
                "bytes": len(data),
                "sha256": digest,
                "content_type": content_type,
                "content_disposition": content_disposition,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
