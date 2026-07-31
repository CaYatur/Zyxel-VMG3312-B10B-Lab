# CaYaRouter custom firmware build status

## Goal

Build a VMG3312-B10B `ras.bin` candidate that keeps the original Zyxel UI at
`/` and adds the CaYaRouter UI at `/caya/`.

## Confirmed base parameters

- Model: Zyxel VMG3312-B10B
- Chip: Broadcom 63268
- Board: 963168VX
- Model ID / custom model ID: 400e
- Base firmware: 1.00(AAPP.7)
- JFFS2 erase block: 128 KiB
- Firmware JFFS2 offset: `0x20000`
- Firmware JFFS2 end: `0x1100000`

## Safe scope

The custom build targets only the firmware `fs+kernel` image. It must not call
`createZyNandimg`, create SMT/full-flash images, or include device-specific
PSI/NVRAM, calibration, MAC, serial, CFE, or partition-table changes.

The stock web UI remains in `/webs/Brick/`. The custom files are copied to:

```text
/webs/Brick/caya/index.html
/webs/Brick/caya/full-styles.css
/webs/Brick/caya/full-app.js
```

## Tools

```text
tools/prepare_custom_firmware_workspace.py
tools/build_caya_firmware_linux.sh
tools/firmware_candidate_guard.py
```

The Linux build script follows the vendor sequence:

```text
mkfs.jffs2 -> bcmZyNandImageBuilder -> fs+kernel candidate
```

It intentionally skips `createZyNandimg` and `addvtoken` full-flash workflows.

## Required validation before upload

1. Build completes without warnings or missing files.
2. Candidate opens as big-endian JFFS2 with zero node CRC failures.
3. `/webs/Brick/index.html` remains present.
4. `/webs/Brick/caya/` contains the three UI assets and build marker.
5. Vendor header/model/board fields match AAPP7.
6. Candidate differs from stock only in the firmware payload region.
7. Stock recovery image hash is rechecked.
8. Candidate is never uploaded automatically by the build scripts.

Passing `firmware_candidate_guard.py` is necessary but not sufficient. A
successful offline extraction and file-by-file manifest comparison are also
required before a controlled device test.

## Recovery package

A local, git-ignored recovery package is stored under:

```text
.caya-agent/recovery/VMG3312-B10B-AAPP7/
```

Expected stock SHA-256:

```text
407fef65a84ae6fce1cfcfc5ef03c298abe6503b998930d32da9a02b4f108898
```

Only the unchanged `100AAPP7D0.bin` file is used for recovery. Full-flash/SMT
images are excluded.

## Current limitation

The vendor host tools are Linux ELF programs. The connected Windows agent does
not allow WSL execution, so the final binary candidate has not yet been built
or declared flash-ready in this workspace. No custom firmware has been sent to
the modem.
