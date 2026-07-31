#!/usr/bin/env python3
"""Strict offline release guard for VMG3312-B10B CaYaRouter candidates.

The guard requires structural JFFS2 validation and a byte-for-byte comparison
report against the official AAPP7 rootfs. It never uploads firmware.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

STOCK_SHA256 = "407fef65a84ae6fce1cfcfc5ef03c298abe6503b998930d32da9a02b4f108898"
JFFS2_OFFSET = 0x20000
JFFS2_END = 0x1100000
EXPECTED_PREFIX = bytes.fromhex("360000004d5354435f343030650034303065")
EXPECTED_FILES = 1153
EXPECTED_SYMLINKS = 225
EXPECTED_ACTIVE_PATHS = 1737
EXPECTED_COMMON_FILES = 1147
EXPECTED_REMOVED = 28
EXPECTED_ADDED = 6
REQUIRED_PATHS = {
    "/webs/Brick/index.html",
    "/webs/Brick/caya/index.html",
    "/webs/Brick/caya/full-styles.css",
    "/webs/Brick/caya/live-styles.css",
    "/webs/Brick/caya/live-modules.js",
    "/webs/Brick/caya/full-app.js",
    "/webs/Brick/caya/firmware-build.json",
    "/vmlinux.lz",
}
FORBIDDEN_MARKERS = (b"CFE CUSTOM", b"calibration override", b"partition rewrite")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--stock", type=Path, default=Path("research/100AAPP7D0.bin"))
    parser.add_argument("--paths-report", type=Path)
    parser.add_argument("--tree-report", type=Path)
    parser.add_argument("--paths-list", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    candidate_path = args.candidate.resolve()
    candidate_dir = candidate_path.parent
    paths_report_path = (args.paths_report or candidate_dir / "jffs2-paths.json").resolve()
    tree_report_path = (args.tree_report or candidate_dir / "tree-comparison.json").resolve()
    paths_list_path = (args.paths_list or candidate_dir / "all-paths.txt").resolve()

    candidate = candidate_path.read_bytes()
    stock = args.stock.read_bytes()
    paths_report = read_json(paths_report_path)
    tree_report = read_json(tree_report_path)
    summary = paths_report.get("summary") if isinstance(paths_report.get("summary"), dict) else {}
    paths = {
        line.split()[-1]
        for line in paths_list_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and line.split()[-1].startswith("/")
    } if paths_list_path.is_file() else set()

    crc_keys = (
        "dirent_node_crc_failures",
        "dirent_name_crc_failures",
        "inode_node_crc_failures",
    )
    tail = candidate[JFFS2_END:] if len(candidate) >= JFFS2_END else b""
    candidate_sha256 = digest(candidate)
    sidecar = candidate_path.with_suffix(candidate_path.suffix + ".sha256")
    sidecar_matches = True
    if sidecar.is_file():
        sidecar_matches = sidecar.read_text(encoding="utf-8", errors="replace").split()[0] == candidate_sha256

    checks = {
        "stock_sha256_matches_known_aapp7": digest(stock) == STOCK_SHA256,
        "candidate_not_identical_to_stock": candidate_sha256 != STOCK_SHA256,
        "candidate_size_reasonable": 17_800_000 <= len(candidate) <= 17_900_000,
        "vendor_header_prefix_matches": candidate.startswith(EXPECTED_PREFIX),
        "jffs2_magic_at_0x20000": candidate[JFFS2_OFFSET:JFFS2_OFFSET + 2] == b"\x19\x85",
        "contains_board_id": b"963168VX" in candidate[:JFFS2_OFFSET],
        "contains_model_family": b"AAPP" in candidate[:JFFS2_OFFSET] and b"400e" in candidate[:4096],
        "contains_no_forbidden_markers": not any(marker in candidate for marker in FORBIDDEN_MARKERS),
        "jffs2_partition_present": len(candidate) >= JFFS2_END,
        "image_default_tail_length_valid": 18_000 <= len(tail) <= 20_000,
        "image_default_tail_nonempty": bool(tail) and any(byte != 0 for byte in tail),
        "paths_report_present": bool(paths_report),
        "tree_report_present": bool(tree_report),
        "paths_list_present": bool(paths),
        "all_jffs2_crcs_zero": all(summary.get(key) == 0 for key in crc_keys),
        "expected_file_count": summary.get("files") == EXPECTED_FILES,
        "expected_symlink_count": summary.get("symlinks") == EXPECTED_SYMLINKS,
        "expected_active_path_count": summary.get("active_paths") == EXPECTED_ACTIVE_PATHS,
        "required_paths_present": REQUIRED_PATHS.issubset(paths),
        "tree_comparison_ok": tree_report.get("ok") is True,
        "only_default_cfg_changed": (
            tree_report.get("changed_common_count") == 1
            and tree_report.get("only_expected_common_file_changed") is True
        ),
        "default_cfg_only_password_fields_changed": (
            tree_report.get("default_cfg_only_password_fields_changed") is True
        ),
        "admin_root_default_to_1234": tree_report.get("admin_root_are_1234") is True,
        "expected_common_file_count": tree_report.get("common_files") == EXPECTED_COMMON_FILES,
        "expected_removed_count": tree_report.get("removed_count") == EXPECTED_REMOVED,
        "expected_added_count": tree_report.get("added_count") == EXPECTED_ADDED,
        "symlinks_identical": tree_report.get("symlinks_identical") is True,
        "special_entries_identical": tree_report.get("special_paths_types_identical") is True,
        "kernel_identical": tree_report.get("vmlinux_identical") is True,
        "sha256_sidecar_matches": sidecar_matches,
    }

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "ok": not failed,
        "candidate": str(candidate_path),
        "candidate_bytes": len(candidate),
        "candidate_sha256": candidate_sha256,
        "stock_sha256": digest(stock),
        "image_default_tail_bytes": len(tail),
        "paths_report": str(paths_report_path),
        "tree_report": str(tree_report_path),
        "paths_list": str(paths_list_path),
        "layout": {
            "vendor_header_end": hex(JFFS2_OFFSET),
            "jffs2_end": hex(JFFS2_END),
        },
        "checks": checks,
        "failed_checks": failed,
        "warning": "Passing this guard is required before requesting final flash approval; it is not a recovery guarantee.",
    }
    rendered = json.dumps(report, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
