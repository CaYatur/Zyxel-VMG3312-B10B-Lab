#!/usr/bin/env python3
"""Reconstruct the extracted AAPP7 rootfs for a reproducible JFFS2 build.

Run this under Linux/WSL so symlinks can be created faithfully. Device nodes
are emitted as an mkfs.jffs2 device-table; no root privileges are required.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
from pathlib import Path


def parse_device_map(make_devs: Path) -> dict[str, tuple[str, int, int]]:
    text = make_devs.read_text(encoding="utf-8", errors="ignore")
    mapping: dict[str, tuple[str, int, int]] = {}
    pattern = re.compile(r"mknod\s+\$ROOTFS(/\S+)\s+([cbp])(?:\s+(\d+)\s+(\d+))?")
    for match in pattern.finditer(text):
        path, kind, major, minor = match.groups()
        mapping[path] = (kind, int(major or 0), int(minor or 0))

    xs = list("pqrstuvwxyzabcde")
    ys = list("0123456789abcdef")
    index = 0
    for x in xs:
        for y in ys:
            mapping[f"/dev/pty{x}{y}"] = ("c", 2, index)
            mapping[f"/dev/tty{x}{y}"] = ("c", 3, index)
            index += 1
    return mapping


def clean_mode(mode_octal: str) -> int:
    return int(mode_octal, 8) & 0o7777


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--make-devs", type=Path, required=True)
    parser.add_argument("--ui", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device-table", type=Path, required=True)
    parser.add_argument(
        "--prune-unrelated-web-assets",
        action="store_true",
        help="Remove unreferenced assets for other router models and Thumbs.db files",
    )
    args = parser.parse_args()

    source = args.extracted.resolve()
    output = args.output.resolve()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(source, output, symlinks=False)

    for item in manifest["files"]:
        path = output / item["path"].lstrip("/")
        if not path.is_file():
            raise FileNotFoundError(f"Missing extracted regular file: {item['path']}")
        os.chmod(path, clean_mode(item["mode_octal"]))

    for item in manifest["symlinks"]:
        path = output / item["path"].lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink():
            path.unlink()
        os.symlink(item["target"], path)

    pruned: list[str] = []
    if args.prune_unrelated_web_assets:
        brick = output / "webs" / "Brick"
        for relative in (
            "pages/VMG3312-B10A",
            "pages/DSL-491HNU-B1Bv2",
        ):
            target = brick / relative
            if target.exists():
                shutil.rmtree(target)
                pruned.append(relative + "/")
        for target in brick.rglob("Thumbs.db"):
            target.unlink()
            pruned.append(str(target.relative_to(brick)).replace(os.sep, "/"))

    caya_dir = output / "webs" / "Brick" / "caya"
    caya_dir.mkdir(parents=True, exist_ok=True)
    ui_files = (
        "index.html",
        "full-styles.css",
        "live-styles.css",
        "live-modules.js",
        "full-app.js",
    )
    for name in ui_files:
        shutil.copy2(args.ui / name, caya_dir / name)
        os.chmod(caya_dir / name, 0o644)
    (caya_dir / "firmware-build.json").write_text(
        json.dumps(
            {
                "project": "CaYaRouter Lab",
                "model": "VMG3312-B10B",
                "board": "963168VX",
                "base_firmware": "1.00(AAPP.7)",
                "path": "/caya/",
                "stock_ui_preserved": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    os.chmod(caya_dir / "firmware-build.json", 0o644)

    device_map = parse_device_map(args.make_devs)
    lines = ["# name type mode uid gid major minor start inc count"]
    missing: list[str] = []
    for item in manifest["special_entries"]:
        path = item["path"]
        if path not in device_map:
            missing.append(path)
            continue
        kind, major, minor = device_map[path]
        mode = clean_mode(item["mode_octal"])
        lines.append(f"{path} {kind} {mode:04o} 0 0 {major} {minor} 0 0 -")

    if missing:
        raise RuntimeError(f"Missing device mappings: {missing}")

    args.device_table.parent.mkdir(parents=True, exist_ok=True)
    args.device_table.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = {
        "ok": True,
        "regular_files": len(manifest["files"]),
        "symlinks": len(manifest["symlinks"]),
        "special_entries": len(manifest["special_entries"]),
        "output": str(output),
        "device_table": str(args.device_table.resolve()),
        "pruned_web_assets": pruned,
        "stock_ui_preserved": (output / "webs" / "Brick" / "index.html").is_file(),
        "caya_ui_present": all((caya_dir / name).is_file() for name in ui_files),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
