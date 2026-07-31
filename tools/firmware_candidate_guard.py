#!/usr/bin/env python3
"""Conservative offline guard for VMG3312-B10B firmware candidates.

The guard does not prove that an image is safe to flash. It rejects obvious
format/model/layout mistakes and requires explicit CaYaRouter markers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

STOCK_SHA256 = "407fef65a84ae6fce1cfcfc5ef03c298abe6503b998930d32da9a02b4f108898"
JFFS2_OFFSET = 0x20000
JFFS2_END = 0x1100000
EXPECTED_PREFIX = bytes.fromhex("360000004d5354435f343030650034303065")
REQUIRED_MARKERS = (b"CaYaRouter Lab", b"/caya/", b"VMG3312-B10B")
FORBIDDEN_MARKERS = (b"CFE CUSTOM", b"calibration override", b"partition rewrite")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--stock", type=Path, default=Path("research/100AAPP7D0.bin"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    candidate = args.candidate.read_bytes()
    stock = args.stock.read_bytes()

    checks = {
        "stock_sha256_matches_known_aapp7": digest(stock) == STOCK_SHA256,
        "candidate_not_identical_to_stock": digest(candidate) != STOCK_SHA256,
        "candidate_size_reasonable": 16_000_000 <= len(candidate) <= 20_000_000,
        "vendor_header_prefix_matches": candidate.startswith(EXPECTED_PREFIX),
        "jffs2_magic_at_0x20000": candidate[JFFS2_OFFSET:JFFS2_OFFSET + 2] == b"\x19\x85",
        "contains_board_id": b"963168VX" in candidate,
        "contains_model_family": b"AAPP" in candidate and b"400e" in candidate[:4096],
        "contains_all_caya_markers": all(marker in candidate for marker in REQUIRED_MARKERS),
        "contains_no_forbidden_markers": not any(marker in candidate for marker in FORBIDDEN_MARKERS),
        "stock_header_region_preserved": candidate[:JFFS2_OFFSET] == stock[:JFFS2_OFFSET],
        "stock_trailing_vendor_region_preserved": (
            len(candidate) >= JFFS2_END
            and len(stock) >= JFFS2_END
            and candidate[JFFS2_END:] == stock[JFFS2_END:]
        ),
    }

    hard_fail = [name for name, ok in checks.items() if not ok]
    report = {
        "ok": not hard_fail,
        "candidate": str(args.candidate),
        "candidate_bytes": len(candidate),
        "candidate_sha256": digest(candidate),
        "stock_sha256": digest(stock),
        "layout": {
            "vendor_header_end": hex(JFFS2_OFFSET),
            "jffs2_end": hex(JFFS2_END),
        },
        "checks": checks,
        "failed_checks": hard_fail,
        "warning": "Passing this guard is necessary but not sufficient for safe flashing.",
    }
    rendered = json.dumps(report, indent=2)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
