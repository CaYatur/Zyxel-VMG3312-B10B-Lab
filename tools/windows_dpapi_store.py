from __future__ import annotations

import argparse
import base64
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path

CRYPTPROTECT_UI_FORBIDDEN = 0x01
APP_ENTROPY = b"CaYaRouter-Zyxel-VMG3312-B10B-v1"


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> tuple[DATA_BLOB, ctypes.Array[ctypes.c_char]]:
    buffer = ctypes.create_string_buffer(data)
    return (
        DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))),
        buffer,
    )


def protect(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI is available only on Windows")

    in_blob, in_buffer = _blob(data)
    entropy_blob, entropy_buffer = _blob(APP_ENTROPY)
    out_blob = DATA_BLOB()

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        "CaYaRouter modem credentials",
        ctypes.byref(entropy_blob),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise ctypes.WinError()

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)
        del in_buffer, entropy_buffer


def unprotect(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI is available only on Windows")

    in_blob, in_buffer = _blob(data)
    entropy_blob, entropy_buffer = _blob(APP_ENTROPY)
    out_blob = DATA_BLOB()

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob),
    )
    if not ok:
        raise ctypes.WinError()

    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        kernel32.LocalFree(out_blob.pbData)
        del in_buffer, entropy_buffer


def save_credentials(path: Path, username: str, password: str) -> None:
    payload = json.dumps(
        {"username": username, "password": password},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    encrypted = protect(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "format": "caya-dpapi-v1",
        "scope": "current-windows-user",
        "ciphertext": base64.b64encode(encrypted).decode("ascii"),
    }
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")


def load_credentials(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("format") != "caya-dpapi-v1":
        raise ValueError("Unsupported credential store format")
    encrypted = base64.b64decode(document["ciphertext"])
    payload = json.loads(unprotect(encrypted).decode("utf-8"))
    if not isinstance(payload.get("username"), str) or not isinstance(
        payload.get("password"), str
    ):
        raise ValueError("Credential store is invalid")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["save", "check"])
    parser.add_argument("--path", required=True, type=Path)
    parser.add_argument("--username")
    parser.add_argument("--password")
    args = parser.parse_args()

    if args.command == "save":
        if args.username is None or args.password is None:
            parser.error("save requires --username and --password")
        save_credentials(args.path, args.username, args.password)
        print(json.dumps({"saved": True, "path": str(args.path)}))
        return 0

    credentials = load_credentials(args.path)
    print(
        json.dumps(
            {
                "ok": True,
                "username": credentials["username"],
                "password_length": len(credentials["password"]),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
