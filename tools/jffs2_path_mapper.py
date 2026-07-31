from __future__ import annotations

import argparse
import binascii
import json
import stat
import struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

COMMON_HEADER_SIZE = 12
RAW_DIRENT_SIZE = 40
RAW_INODE_SIZE = 68
JFFS2_MAGIC = 0x1985
NODE_DIRENT = 0xE001
NODE_INODE = 0xE002

DIRENT_TYPES = {
    0: "unknown",
    1: "fifo",
    2: "char",
    4: "directory",
    6: "block",
    8: "file",
    10: "symlink",
    12: "socket",
}


def jffs2_crc(data: bytes) -> int:
    return (binascii.crc32(data, 0xFFFFFFFF) ^ 0xFFFFFFFF) & 0xFFFFFFFF


def iter_nodes(data: bytes, start: int, end: int | None = None):
    limit = len(data) if end is None else min(end, len(data))
    pos = start
    while pos + COMMON_HEADER_SIZE <= limit:
        magic = struct.unpack_from(">H", data, pos)[0]
        if magic != JFFS2_MAGIC:
            pos += 4
            continue
        nodetype, totlen, hdr_crc = struct.unpack_from(">HII", data, pos + 2)
        if totlen < COMMON_HEADER_SIZE or pos + totlen > limit:
            pos += 4
            continue
        if jffs2_crc(data[pos : pos + 8]) != hdr_crc:
            pos += 4
            continue
        yield pos, nodetype, totlen, data[pos : pos + totlen]
        pos += (totlen + 3) & ~3


def parse_dirent(offset: int, node: bytes) -> dict[str, Any] | None:
    if len(node) < RAW_DIRENT_SIZE:
        return None
    (
        pino,
        version,
        ino,
        mctime,
        nsize,
        dtype,
        _unused,
        node_crc,
        name_crc,
    ) = struct.unpack_from(">IIIIBBHII", node, COMMON_HEADER_SIZE)
    if RAW_DIRENT_SIZE + nsize > len(node):
        return None
    name_bytes = node[RAW_DIRENT_SIZE : RAW_DIRENT_SIZE + nsize]
    fixed_without_crcs = node[: RAW_DIRENT_SIZE - 8]
    calc_node_crc = jffs2_crc(fixed_without_crcs)
    calc_name_crc = jffs2_crc(name_bytes)
    try:
        name = name_bytes.decode("utf-8")
    except UnicodeDecodeError:
        name = name_bytes.decode("latin-1", "replace")
    return {
        "node_offset": offset,
        "pino": pino,
        "version": version,
        "ino": ino,
        "mctime": mctime,
        "nsize": nsize,
        "dtype": dtype,
        "type_name": DIRENT_TYPES.get(dtype, f"type_{dtype}"),
        "name": name,
        "node_crc_ok": node_crc == calc_node_crc,
        "name_crc_ok": name_crc == calc_name_crc,
        "deleted": ino == 0,
    }


def parse_inode(offset: int, node: bytes) -> dict[str, Any] | None:
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
    ) = struct.unpack_from(">IIIHHIIIIIIIBBHII", node, COMMON_HEADER_SIZE)
    fixed_without_node_crc = node[: RAW_INODE_SIZE - 8]
    calc_node_crc = jffs2_crc(fixed_without_node_crc)
    data_bytes = node[RAW_INODE_SIZE : RAW_INODE_SIZE + csize]
    return {
        "node_offset": offset,
        "ino": ino,
        "version": version,
        "mode": mode,
        "mode_octal": oct(mode),
        "file_kind": (
            "directory"
            if stat.S_ISDIR(mode)
            else "file"
            if stat.S_ISREG(mode)
            else "symlink"
            if stat.S_ISLNK(mode)
            else "other"
        ),
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
        "data_crc_ok": jffs2_crc(data_bytes) == data_crc if len(data_bytes) == csize else False,
        "node_crc_ok": node_crc == calc_node_crc,
    }


def build_paths(dirents: list[dict[str, Any]]) -> tuple[dict[int, str], list[dict[str, Any]]]:
    latest: dict[tuple[int, str], dict[str, Any]] = {}
    for item in dirents:
        key = (item["pino"], item["name"])
        previous = latest.get(key)
        if previous is None or item["version"] > previous["version"]:
            latest[key] = item

    active = [item for item in latest.values() if not item["deleted"]]
    by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in active:
        by_parent[item["pino"]].append(item)

    inode_paths: dict[int, str] = {1: "/"}
    entries: list[dict[str, Any]] = []
    queue = [1]
    visited_parents: set[int] = set()
    while queue:
        parent = queue.pop(0)
        if parent in visited_parents:
            continue
        visited_parents.add(parent)
        parent_path = inode_paths.get(parent, f"/__orphan_parent_{parent}")
        for item in sorted(by_parent.get(parent, []), key=lambda x: x["name"]):
            path = (parent_path.rstrip("/") + "/" + item["name"]) or "/"
            inode_paths.setdefault(item["ino"], path)
            record = dict(item)
            record["path"] = path
            entries.append(record)
            if item["type_name"] == "directory":
                queue.append(item["ino"])

    known_keys = {(item["pino"], item["name"]) for item in entries}
    for item in active:
        if (item["pino"], item["name"]) in known_keys:
            continue
        path = f"/__orphan_parent_{item['pino']}/{item['name']}"
        inode_paths.setdefault(item["ino"], path)
        record = dict(item)
        record["path"] = path
        entries.append(record)
    return inode_paths, sorted(entries, key=lambda x: x["path"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Map paths from a big-endian JFFS2 image")
    parser.add_argument("image", type=Path)
    parser.add_argument("--offset", type=lambda x: int(x, 0), default=0x20000)
    parser.add_argument("--end", type=lambda x: int(x, 0), default=None)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--paths", required=True, type=Path)
    args = parser.parse_args()

    data = args.image.read_bytes()
    dirents: list[dict[str, Any]] = []
    inodes: list[dict[str, Any]] = []
    node_counts: Counter[str] = Counter()
    for offset, nodetype, _totlen, node in iter_nodes(data, args.offset, args.end):
        if nodetype == NODE_DIRENT:
            parsed = parse_dirent(offset, node)
            if parsed:
                dirents.append(parsed)
                node_counts["dirent"] += 1
        elif nodetype == NODE_INODE:
            parsed = parse_inode(offset, node)
            if parsed:
                inodes.append(parsed)
                node_counts["inode"] += 1
        else:
            node_counts[f"0x{nodetype:04x}"] += 1

    inode_paths, entries = build_paths(dirents)
    latest_inode: dict[int, dict[str, Any]] = {}
    for inode in inodes:
        previous = latest_inode.get(inode["ino"])
        if previous is None or inode["version"] > previous["version"]:
            latest_inode[inode["ino"]] = inode

    enriched_entries = []
    for entry in entries:
        enriched = dict(entry)
        inode = latest_inode.get(entry["ino"])
        if inode:
            enriched["inode_summary"] = inode
        enriched_entries.append(enriched)

    interesting_prefixes = (
        "/webs",
        "/www",
        "/pages",
        "/etc",
        "/opt/scripts",
        "/bin",
        "/sbin",
        "/usr/bin",
        "/usr/sbin",
        "/lib/modules",
    )
    interesting = [
        item for item in enriched_entries if item["path"].startswith(interesting_prefixes)
    ]

    report = {
        "image": str(args.image),
        "offset": args.offset,
        "end": args.end,
        "summary": {
            "raw_dirent_nodes": len(dirents),
            "raw_inode_nodes": len(inodes),
            "active_paths": len(enriched_entries),
            "directories": sum(1 for item in enriched_entries if item["type_name"] == "directory"),
            "files": sum(1 for item in enriched_entries if item["type_name"] == "file"),
            "symlinks": sum(1 for item in enriched_entries if item["type_name"] == "symlink"),
            "deleted_latest_dirents": sum(
                1
                for item in {
                    (d["pino"], d["name"]): d for d in sorted(dirents, key=lambda x: x["version"])
                }.values()
                if item["deleted"]
            ),
            "node_counts": dict(node_counts),
            "dirent_node_crc_failures": sum(1 for item in dirents if not item["node_crc_ok"]),
            "dirent_name_crc_failures": sum(1 for item in dirents if not item["name_crc_ok"]),
            "inode_node_crc_failures": sum(1 for item in inodes if not item["node_crc_ok"]),
        },
        "interesting_paths": interesting,
        "entries": enriched_entries,
    }

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.paths.parent.mkdir(parents=True, exist_ok=True)
    args.paths.write_text(
        "\n".join(
            f"{item['type_name']:<10} ino={item['ino']:<8} {item['path']}"
            for item in enriched_entries
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "json": str(args.json),
                "paths": str(args.paths),
                "summary": report["summary"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
