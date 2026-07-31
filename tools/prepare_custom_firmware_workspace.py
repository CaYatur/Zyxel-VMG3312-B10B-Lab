#!/usr/bin/env python3
"""Prepare a safe CaYaRouter firmware overlay and build manifest.

This tool never flashes a device and never modifies CFE, NVRAM, calibration,
MAC, serial, or partition metadata. It copies the web UI into a separate
/webs/Brick/caya/ directory under a chosen rootfs staging tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

UI_FILES = ("index.html", "full-styles.css", "full-app.js")
EXPECTED_MODEL = "VMG3312-B10B"
EXPECTED_BOARD = "963168VX"
EXPECTED_VERSION = "1.00(AAPP.7)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rootfs", type=Path, required=True, help="Rootfs staging directory")
    parser.add_argument("--ui", type=Path, default=Path("ui-prototype"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Actually copy files")
    args = parser.parse_args()

    rootfs = args.rootfs.resolve()
    ui = args.ui.resolve()
    stock_root = rootfs / "webs" / "Brick"
    target = stock_root / "caya"

    checks = {
        "rootfs_exists": rootfs.is_dir(),
        "stock_web_root_exists": stock_root.is_dir(),
        "stock_index_exists": (stock_root / "index.html").is_file(),
        "ui_files_exist": all((ui / name).is_file() for name in UI_FILES),
    }
    if not all(checks.values()):
        print(json.dumps({"ok": False, "checks": checks}, indent=2))
        return 2

    files = []
    for name in UI_FILES:
        source = ui / name
        files.append({"name": name, "bytes": source.stat().st_size, "sha256": sha256(source)})

    if args.apply:
        target.mkdir(parents=True, exist_ok=True)
        for name in UI_FILES:
            shutil.copy2(ui / name, target / name)
        marker = target / "firmware-build.json"
        marker.write_text(
            json.dumps(
                {
                    "project": "CaYaRouter Lab",
                    "model": EXPECTED_MODEL,
                    "board": EXPECTED_BOARD,
                    "base_firmware": EXPECTED_VERSION,
                    "path": "/caya/",
                    "stock_ui_preserved": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    manifest = {
        "ok": True,
        "applied": args.apply,
        "model": EXPECTED_MODEL,
        "board": EXPECTED_BOARD,
        "base_firmware": EXPECTED_VERSION,
        "rootfs": str(rootfs),
        "stock_ui": str(stock_root),
        "overlay_target": str(target),
        "stock_ui_preserved": True,
        "forbidden_regions_touched": False,
        "files": files,
        "checks": checks,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
