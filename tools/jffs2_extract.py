from __future__ import annotations

import argparse
import binascii
import json
import os
import stat
import struct
import zlib
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

from jffs2_path_mapper import (
    JFFS2_MAGIC,
    NODE_DIRENT,
    NODE_INODE,
    RAW_DIRENT_SIZE,
    RAW_INODE_SIZE,
    build_paths,
    iter_nodes,
    parse_dirent,
)

COMPR_NONE = 0
COMPR_ZERO = 1
COMPR_ZLIB = 6
SUPPORTED_COMPRESSIONS = {COMPR_NONE, COMPR_ZERO, COMPR_ZLIB}


def jffs2_crc(data: bytes) -> int:
    return (binascii.crc32(data, 0xFFFFFFFF) ^ 0xFFFFFFFF) & 0xFFFFFFFF


def safe_output_path(root: Path, posix_path: str) -> Path:
    pure = PurePosixPath(posix_path)
    if pure.is_absolute():
        pure = PurePosixPath(*pure.parts[1:])
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"Unsafe path: {posix_path!r}")
    candidate = root.joinpath(*pure.parts)
    resolved_root = root.resolve()
    resolved_parent = candidate.parent.resolve()
    if resolved_root != resolved_parent and resolved_root not in resolved_parent.parents:
        raise ValueError(f"Path escapes output root: {posix_path!r}")
    return candidate


def parse_inode_fragment(offset: int, node: bytes) -> dict[str, Any] | None:
    if len(node) < RAW_INODE_SIZE:
        return None
    (
        ino,
        version,
        mode,
        uid,
        gid,
        isize,
        atime,
        mtime,
        ctime,
        data_offset,
        csize,
        dsize,
        compr,
        usercompr,
        flags,
        data_crc,
        node_crc,
    ) = struct.unpack_from(">IIIHHIIIIIIIBBHII", node, 12)

    compressed = node[RAW_INODE_SIZE : RAW_INODE_SIZE + csize]
    node_crc_ok = jffs2_crc(node[: RAW_INODE_SIZE - 8]) == node_crc
    data_crc_ok = jffs2_crc(compressed) == data_crc

    return {
        "node_offset": offset,
        "ino": ino,
        "version": version,
        "mode": mode,
        "uid": uid,
        "gid": gid,
        "isize": isize,
        "atime": atime,
        "mtime": mtime,
        "ctime": ctime,
        "data_offset": data_offset,
        "csize": csize,
        "dsize": dsize,
        "compression": compr,
        "user_compression": usercompr,
        "flags": flags,
        "node_crc_ok": node_crc_ok,
        "data_crc_ok": data_crc_ok,
        "compressed": compressed,
    }


def decompress_fragment(fragment: dict[str, Any]) -> bytes:
    compr = fragment["compression"]
    compressed: bytes = fragment["compressed"]
    dsize = fragment["dsize"]

    if compr == COMPR_NONE:
        data = compressed
    elif compr == COMPR_ZERO:
        data = b"\x00" * dsize
    elif compr == COMPR_ZLIB:
        data = zlib.decompress(compressed)
    else:
        raise ValueError(f"Unsupported JFFS2 compression type {compr}")

    if len(data) != dsize:
        raise ValueError(
            f"Decompressed size mismatch: expected {dsize}, got {len(data)}"
        )
    return data


def reconstruct_inode(fragments: list[dict[str, Any]]) -> tuple[bytes, dict[str, Any]]:
    if not fragments:
        return b"", {}

    ordered = sorted(fragments, key=lambda item: (item["version"], item["node_offset"]))
    latest = ordered[-1]
    current = bytearray()
    final_size = 0

    for fragment in ordered:
        final_size = fragment["isize"]
        if len(current) > final_size:
            del current[final_size:]
        elif len(current) < final_size:
            current.extend(b"\x00" * (final_size - len(current)))

        if fragment["dsize"] == 0:
            continue
        if not fragment["node_crc_ok"] or not fragment["data_crc_ok"]:
            raise ValueError(
                f"CRC failure in inode {fragment['ino']} at 0x{fragment['node_offset']:x}"
            )
        data = decompress_fragment(fragment)
        start = fragment["data_offset"]
        end = start + len(data)
        if end > len(current):
            current.extend(b"\x00" * (end - len(current)))
        current[start:end] = data

    if len(current) > final_size:
        del current[final_size:]
    elif len(current) < final_size:
        current.extend(b"\x00" * (final_size - len(current)))

    metadata = {
        "ino": latest["ino"],
        "version": latest["version"],
        "mode": latest["mode"],
        "mode_octal": oct(latest["mode"]),
        "uid": latest["uid"],
        "gid": latest["gid"],
        "isize": final_size,
        "mtime": latest["mtime"],
        "fragment_count": len(ordered),
        "compression_types": sorted({item["compression"] for item in ordered}),
    }
    return bytes(current), metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely extract regular files from a big-endian JFFS2 image"
    )
    parser.add_argument("image", type=Path)
    parser.add_argument("--offset", type=lambda value: int(value, 0), default=0x20000)
    parser.add_argument("--end", type=lambda value: int(value, 0), default=0x1100000)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    image = args.image.read_bytes()
    dirents: list[dict[str, Any]] = []
    inode_fragments: dict[int, list[dict[str, Any]]] = defaultdict(list)
    unsupported: dict[int, int] = defaultdict(int)

    for offset, nodetype, _totlen, node in iter_nodes(image, args.offset, args.end):
        if nodetype == NODE_DIRENT:
            parsed = parse_dirent(offset, node)
            if parsed:
                dirents.append(parsed)
        elif nodetype == NODE_INODE:
            parsed = parse_inode_fragment(offset, node)
            if parsed:
                inode_fragments[parsed["ino"]].append(parsed)
                if parsed["compression"] not in SUPPORTED_COMPRESSIONS:
                    unsupported[parsed["compression"]] += 1

    if unsupported:
        raise RuntimeError(f"Unsupported compression types found: {dict(unsupported)}")

    _inode_paths, entries = build_paths(dirents)
    output_root = args.output
    output_root.mkdir(parents=True, exist_ok=True)

    extracted: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    symlinks: list[dict[str, Any]] = []
    special: list[dict[str, Any]] = []

    for entry in entries:
        path = entry["path"]
        try:
            destination = safe_output_path(output_root, path)
            type_name = entry["type_name"]

            if type_name == "directory":
                destination.mkdir(parents=True, exist_ok=True)
                continue

            fragments = inode_fragments.get(entry["ino"], [])
            data, metadata = reconstruct_inode(fragments)

            if type_name == "file":
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                try:
                    os.utime(destination, (metadata.get("mtime", 0), metadata.get("mtime", 0)))
                except (OSError, OverflowError, ValueError):
                    pass
                extracted.append(
                    {
                        "path": path,
                        "ino": entry["ino"],
                        "bytes": len(data),
                        "mode_octal": metadata.get("mode_octal"),
                        "fragment_count": metadata.get("fragment_count"),
                        "compression_types": metadata.get("compression_types"),
                    }
                )
            elif type_name == "symlink":
                target = data.decode("utf-8", "replace")
                symlinks.append({"path": path, "target": target, "ino": entry["ino"]})
            else:
                special.append(
                    {
                        "path": path,
                        "type": type_name,
                        "ino": entry["ino"],
                        "mode_octal": metadata.get("mode_octal"),
                    }
                )
        except Exception as exc:
            errors.append({"path": path, "error": f"{type(exc).__name__}: {exc}"})

    manifest = {
        "image": str(args.image),
        "offset": args.offset,
        "end": args.end,
        "output": str(args.output),
        "summary": {
            "regular_files_extracted": len(extracted),
            "directories_created": sum(1 for item in entries if item["type_name"] == "directory"),
            "symlinks_recorded": len(symlinks),
            "special_entries_recorded": len(special),
            "errors": len(errors),
            "total_regular_file_bytes": sum(item["bytes"] for item in extracted),
        },
        "files": extracted,
        "symlinks": symlinks,
        "special_entries": special,
        "errors": errors,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": not errors,
                "output": str(args.output),
                "manifest": str(args.manifest),
                "summary": manifest["summary"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
