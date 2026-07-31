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
/webs/Brick/caya/live-styles.css
/webs/Brick/caya/live-modules.js
/webs/Brick/caya/full-app.js
/webs/Brick/caya/firmware-build.json
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
4. `/webs/Brick/caya/` contains the five UI assets and build marker.
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

## Live integration and release status

The CaYaRouter shell maps 31 verified stock modules and 68 stock pages. A local
same-origin gateway authenticated against the real modem and verified all 61
safe inventory pages. It found 52 form actions; all 52 remain same-origin and
therefore submit to the original Zyxel CGI, CMD, and WL handlers.

The final local, git-ignored release candidate is:

```text
.caya-agent/build/release-ready/CaYaRouter-VMG3312-B10B-AAPP7.bin
```

Release SHA-256:

```text
41b27ea9f1e4d7db0e349cdbce7b68c75385281e66fa4be3b76d4faaba0103d2
```

The strict release guard passes every required check: zero JFFS2 CRC failures,
1,153 files, 225 symlinks, 202 preserved special entries, an identical kernel,
zero changed files among 1,147 common stock files, the six expected CaYaRouter
files, and the 28 expected unrelated web assets removed to remain inside the
stock JFFS2 partition.

No custom firmware has been sent to the modem. A controlled device test still
requires separate, explicit final approval. Passing the offline and live tests
is not a recovery guarantee; stock recovery still depends on the bootloader and
recovery web path remaining intact.
