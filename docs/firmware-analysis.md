# Stock AAPP7 Firmware Analysis

This document summarizes an offline inspection of the official Zyxel VMG3312-B10B Türk Telekom recovery image.

No data was written to the modem during this analysis.

## Image identity

- File name: `100AAPP7D0.bin`
- Size: `17,844,549` bytes (`0x1104945`)
- SHA-256: `407fef65a84ae6fce1cfcfc5ef03c298abe6503b998930d32da9a02b4f108898`
- MD5: `ce53868c209a098ffb25cd11f70931cc`

Detected identifiers include:

- `MSTC_400e`
- `963168VX`
- `AAPP`
- `VMG3312`

## High-level layout

The first dense and CRC-valid JFFS2 node starts at offset `0x20000`.

```text
0x00000000 .. 0x0001ffff  Vendor-specific header or boot payload
0x00020000 .. 0x010fffff  Big-endian JFFS2 filesystem data
0x01100000 .. EOF         Trailing vendor image data / metadata
```

The exact meaning of the first 128 KiB and the trailing bytes must still be matched against the Broadcom/Zyxel image-building tools before repacking.

## JFFS2 validation

- Byte order: big-endian
- Valid JFFS2 node headers: `12,769`
- Last valid aligned node end: `0x1100000`
- Directory entry nodes: `1,772`
- Inode nodes: `10,996`
- Padding nodes: `1`
- Header CRC failures: `0`
- Directory name CRC failures: `0`
- Inode node CRC failures: `0`

Reconstructed active filesystem entries:

- Directories: `170`
- Regular files: `1,175`
- Symbolic links: `225`
- Total active paths: `1,772`

## Important filesystem locations

The stock web interface is stored under:

```text
/webs/Brick/
/webs/Brick/menu.json
/webs/Brick/login/
/webs/Brick/js/
/webs/Brick/pages/
```

Device-specific assets exist under:

```text
/webs/Brick/pages/VMG3312-B10B/
```

The main initialization files include:

```text
/etc/inittab
/etc/init.d/rcS
/linuxrc
```

Relevant services and tools include:

```text
/bin/httpd
/bin/telnetd
/bin/busybox
/usr/sbin/httpd
/usr/sbin/telnetd
/usr/sbin/flash_eraseall
/lib/private/libcms_cli.so
```

Flash device nodes present in the filesystem include:

```text
/dev/mtd0 .. /dev/mtd3
/dev/mtdblock0 .. /dev/mtdblock7
```

The root filesystem also contains USB, DSL, NAT, firewall, QoS, VPN, remote-management, firmware-upgrade, backup/restore, and system-monitoring pages.

## Filesystem extraction

The filesystem was extracted locally with CRC validation and without modifying the source image.

- Regular files extracted: `1,175`
- Directories created: `170`
- Symbolic links recorded in the manifest: `225`
- Special device entries recorded in the manifest: `202`
- Extraction errors: `0`
- Total regular-file bytes: `38,833,727`
- Compression types used by inode fragments: uncompressed (`0`) and zlib (`6`)

The stock UI contains `297` HTML/HTM files and approximately `9,832` embedded Zyxel template expressions such as `ejGet(...)`, `ejGetOther(...)`, and `ejGetML(...)`. Therefore, the extracted HTML is not a completely static application: the stock `httpd` and CMS runtime normally render values and execute CGI/CMD/WL handlers.

A read-only preview server was added to render common template expressions with mock values, serve the extracted assets locally, and block every form submission. This is suitable for visual inspection and interface prototyping, not for emulating modem behavior.

## Current interpretation

The firmware is suitable for controlled offline analysis and web-interface prototyping. The first test build should modify only non-critical web assets inside the JFFS2 filesystem.

Before producing a flashable image, the project still needs to determine:

1. The exact vendor header structure.
2. Image length and checksum fields.
3. Model and board-ID validation fields.
4. The role of the trailing bytes after `0x1100000`.
5. Whether deterministic JFFS2 repacking is accepted by the recovery loader.
6. The exact flash target used by the stock recovery process.

Bootloader, calibration, NVRAM, MAC-address, partition-table, and device-identity regions must remain untouched.
