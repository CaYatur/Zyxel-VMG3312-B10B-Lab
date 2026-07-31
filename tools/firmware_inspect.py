from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import re
import struct
from collections import Counter
from pathlib import Path
from typing import Any

JFFS2_MAGIC_LE = b"\x85\x19"
JFFS2_MAGIC_BE = b"\x19\x85"
JFFS2_NODETYPE_NAMES = {
    0x2001: "dirent",
    0x2002: "inode",
    0x2003: "cleanmarker",
    0x2004: "padding",
    0x2006: "summary",
    0xE001: "dirent_accurate",
    0xE002: "inode_accurate",
    0xE008: "xattr",
    0xE009: "xref",
}

SIGNATURES: list[tuple[str, bytes]] = [
    ("gzip", b"\x1f\x8b\x08"),
    ("bzip2", b"BZh"),
    ("xz", b"\xfd7zXZ\x00"),
    ("lzma_alone", b"\x5d\x00\x00"),
    ("uImage", b"\x27\x05\x19\x56"),
    ("squashfs_le", b"hsqs"),
    ("squashfs_be", b"sqsh"),
    ("cramfs_le", b"\x45\x3d\xcd\x28"),
    ("cramfs_be", b"\x28\xcd\x3d\x45"),
    ("ubifs", b"\x31\x18\x10\x06"),
    ("ubi_ec", b"UBI#"),
    ("jffs2_le", JFFS2_MAGIC_LE),
    ("jffs2_be", JFFS2_MAGIC_BE),
    ("elf_le", b"\x7fELF\x01\x01"),
    ("elf_be", b"\x7fELF\x01\x02"),
]

ASCII_MARKERS = [
    b"VMG3312",
    b"963168VX",
    b"MSTC_400e",
    b"AAPP",
    b"Broadcom",
    b"Linux version",
    b"JFFS2",
    b"CFE",
    b"micro_httpd",
    b"/webs",
    b"/pages/",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(block: bytes) -> float:
    if not block:
        return 0.0
    counts = Counter(block)
    n = len(block)
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def find_all(data: bytes, needle: bytes, limit: int = 10000) -> list[int]:
    offsets: list[int] = []
    start = 0
    while len(offsets) < limit:
        pos = data.find(needle, start)
        if pos < 0:
            break
        offsets.append(pos)
        start = pos + 1
    return offsets


def printable_strings(data: bytes, minimum: int = 5, limit: int = 300) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    pattern = re.compile(rb"[\x20-\x7e]{%d,}" % minimum)
    for match in pattern.finditer(data):
        results.append({"offset": match.start(), "text": match.group().decode("ascii", "replace")})
        if len(results) >= limit:
            break
    return results


def parse_jffs2_nodes(data: bytes, start: int, max_nodes: int = 250000) -> dict[str, Any]:
    # Broadcom/MIPS image appears to use big-endian JFFS2. Validate both endiannesses.
    candidates: dict[str, dict[str, Any]] = {}
    for endian_name, endian, magic in (("big", ">", 0x1985), ("little", "<", 0x1985)):
        pos = start
        valid = 0
        invalid = 0
        node_types: Counter[str] = Counter()
        first_nodes: list[dict[str, Any]] = []
        last_end = start
        while pos + 12 <= len(data) and valid + invalid < max_nodes:
            # Nodes are 4-byte aligned. Search forward if this location is padding/noise.
            raw_magic = struct.unpack_from(endian + "H", data, pos)[0]
            if raw_magic != magic:
                pos += 4
                continue
            nodetype, totlen, hdr_crc = struct.unpack_from(endian + "HII", data, pos + 2)
            if totlen < 12 or pos + totlen > len(data) or totlen > 32 * 1024 * 1024:
                invalid += 1
                pos += 4
                continue
            header = data[pos : pos + 8]
            # JFFS2 uses the Linux CRC32 convention: initialize with all
            # ones and invert the final value.
            calc_crc = (binascii.crc32(header, 0xFFFFFFFF) ^ 0xFFFFFFFF) & 0xFFFFFFFF
            crc_ok = calc_crc == hdr_crc
            if not crc_ok:
                invalid += 1
                pos += 4
                continue
            valid += 1
            name = JFFS2_NODETYPE_NAMES.get(nodetype, f"0x{nodetype:04x}")
            node_types[name] += 1
            if len(first_nodes) < 30:
                first_nodes.append(
                    {
                        "offset": pos,
                        "nodetype": f"0x{nodetype:04x}",
                        "type_name": name,
                        "totlen": totlen,
                        "header_crc_ok": True,
                    }
                )
            aligned = (totlen + 3) & ~3
            last_end = max(last_end, pos + aligned)
            pos += aligned
        candidates[endian_name] = {
            "valid_nodes": valid,
            "invalid_magic_candidates": invalid,
            "node_types": dict(node_types),
            "first_nodes": first_nodes,
            "last_valid_node_end": last_end,
        }
    selected = max(candidates, key=lambda key: candidates[key]["valid_nodes"])
    return {"selected_endianness": selected, "candidates": candidates}


def inspect(path: Path, block_size: int = 0x10000) -> dict[str, Any]:
    data = path.read_bytes()
    signatures: dict[str, list[int]] = {}
    for name, sig in SIGNATURES:
        matches = find_all(data, sig)
        if matches:
            signatures[name] = matches[:200]

    markers: dict[str, list[int]] = {}
    for marker in ASCII_MARKERS:
        matches = find_all(data, marker)
        if matches:
            markers[marker.decode("ascii", "replace")] = matches[:100]

    # The first dense run of JFFS2 magic usually identifies the rootfs boundary.
    jffs_candidates = sorted(set(signatures.get("jffs2_be", []) + signatures.get("jffs2_le", [])))
    dense_start = None
    for off in jffs_candidates:
        nearby = sum(1 for candidate in jffs_candidates if off <= candidate < off + 0x10000)
        if nearby >= 4:
            dense_start = off
            break

    entropy_blocks = []
    for offset in range(0, len(data), block_size):
        block = data[offset : offset + block_size]
        entropy_blocks.append(
            {
                "offset": offset,
                "size": len(block),
                "entropy": round(entropy(block), 5),
                "sha256": sha256(block),
                "all_ff": bool(block and all(byte == 0xFF for byte in block)),
                "all_00": bool(block and all(byte == 0x00 for byte in block)),
            }
        )

    report: dict[str, Any] = {
        "file": str(path),
        "size": len(data),
        "sha256": sha256(data),
        "md5": hashlib.md5(data).hexdigest(),
        "header": {
            "first_256_hex": data[:256].hex(),
            "first_256_ascii": "".join(chr(b) if 32 <= b < 127 else "." for b in data[:256]),
            "strings_first_128k": printable_strings(data[:0x20000], minimum=4, limit=180),
        },
        "signatures": signatures,
        "ascii_markers": markers,
        "detected_boundaries": {
            "first_dense_jffs2_magic": dense_start,
            "common_header_boundary_128k": 0x20000 if len(data) > 0x20000 else None,
        },
        "entropy_blocks": entropy_blocks,
    }

    if dense_start is not None:
        report["jffs2"] = parse_jffs2_nodes(data, dense_start)
        report["regions"] = [
            {
                "name": "vendor_header_or_boot_payload",
                "offset": 0,
                "length": dense_start,
                "sha256": sha256(data[:dense_start]),
            },
            {
                "name": "jffs2_candidate",
                "offset": dense_start,
                "length": len(data) - dense_start,
                "sha256": sha256(data[dense_start:]),
            },
        ]
    else:
        report["regions"] = [
            {"name": "whole_image", "offset": 0, "length": len(data), "sha256": sha256(data)}
        ]
    return report


def write_markdown(report: dict[str, Any], output: Path) -> None:
    boundaries = report["detected_boundaries"]
    lines = [
        "# VMG3312-B10B AAPP7 firmware layout",
        "",
        "> Generated by `tools/firmware_inspect.py`. No firmware was written to the device.",
        "",
        "## Image identity",
        "",
        f"- Size: `{report['size']}` bytes (`0x{report['size']:x}`)",
        f"- SHA-256: `{report['sha256']}`",
        f"- MD5: `{report['md5']}`",
        "",
        "## Detected layout",
        "",
    ]
    for region in report.get("regions", []):
        lines.append(
            f"- `{region['name']}`: offset `0x{region['offset']:x}`, length `0x{region['length']:x}`, SHA-256 `{region['sha256']}`"
        )
    lines.extend(["", "## Identifiers", ""])
    for marker, offsets in report.get("ascii_markers", {}).items():
        formatted = ", ".join(f"0x{offset:x}" for offset in offsets[:12])
        lines.append(f"- `{marker}`: {formatted}")
    lines.extend(["", "## Filesystem analysis", ""])
    if "jffs2" in report:
        selected = report["jffs2"]["selected_endianness"]
        info = report["jffs2"]["candidates"][selected]
        lines.append(f"- Selected JFFS2 byte order: **{selected}-endian**")
        lines.append(f"- Valid node headers: `{info['valid_nodes']}`")
        lines.append(f"- Last valid node end: `0x{info['last_valid_node_end']:x}`")
        lines.append("- Node types:")
        for name, count in sorted(info["node_types"].items()):
            lines.append(f"  - `{name}`: {count}")
    else:
        lines.append("No dense JFFS2 region was detected.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The image contains a vendor-specific prefix followed by a JFFS2 candidate region. Exact flash partition names and write targets must still be confirmed from the build profile, CFE boot log, or `/proc/mtd` before any flashing experiment.",
            "",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Zyxel/Broadcom firmware image offline")
    parser.add_argument("image", type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args()

    report = inspect(args.image)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        write_markdown(report, args.markdown)
    print(
        json.dumps(
            {
                "ok": True,
                "image": str(args.image),
                "json": str(args.json),
                "markdown": str(args.markdown) if args.markdown else None,
                "size": report["size"],
                "sha256": report["sha256"],
                "first_dense_jffs2_magic": report["detected_boundaries"]["first_dense_jffs2_magic"],
                "jffs2_endianness": report.get("jffs2", {}).get("selected_endianness"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
