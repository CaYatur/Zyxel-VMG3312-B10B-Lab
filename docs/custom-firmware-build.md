# CaYaRouter custom firmware build status

## Goal

Build a VMG3312-B10B `ras.bin` candidate whose main `/index.html` and login
screen use CaYaRouter. Stock Zyxel pages remain reachable only by direct URL;
the visible CaYaRouter interface renders their live controls and tables as its
own native components through a hidden same-origin bridge.

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

The stock settings pages remain under `/webs/Brick/pages/`. The main index and
login page are intentionally replaced, and the live-only CaYaRouter assets are:

```text
/webs/Brick/caya/caya-app.html
/webs/Brick/caya/caya-app.css
/webs/Brick/caya/caya-app.js
/webs/Brick/caya/caya-login.css
/webs/Brick/caya/live-modules.js
/webs/Brick/caya/caya-loader.js
/webs/Brick/caya/firmware-build.json
```

The previous demo files (`full-app.js`, `full-styles.css`, and
`live-styles.css`) are forbidden in release images.

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

The CaYaRouter shell maps 31 verified stock modules and 68 stock pages. The
native adapter verified all 68 pages against the real modem and identified 63
forms, 472 live controls, 115 action buttons, and 25 information tables. The
34 pages that depend on stock `parent`/dialog helpers run inside a hidden
same-origin `tabFW` bridge; the stock UI itself is never shown in CaYaRouter.

The current corrected, git-ignored release candidate is:

```text
.caya-agent/build/release-native/CaYaRouter-VMG3312-B10B-AAPP7.bin
```

Release SHA-256:

```text
36646b3a04778e032148d6a207c5022d5ef85bd90479385c732279654571ec84
```

The default management accounts are intentionally configured as requested:

```text
admin / 1234
root  / 1234
```

The existing first-login password warning and Skip behavior remain unchanged.
TR-069, PPPoE, and other service credentials are not modified.

The strict release guard passes every required check: zero JFFS2 CRC failures,
1,154 files, 225 symlinks, 202 preserved special entries, an identical kernel,
four intentional changed stock files (`/etc/default.cfg`, the main index, the
login page, and the authorized tab shell), seven expected CaYaRouter files, and
28 expected unrelated web assets removed to remain inside the stock JFFS2
partition. UI validation also proves that fake speed values, demo localStorage,
and the previous `full-app.js` are absent.

The currently installed live-only firmware remains operational, but this newer
native-adapter candidate has not been sent to the modem. Another controlled
device test requires separate, explicit final approval. Passing the offline and
live tests is not a recovery guarantee; stock recovery still depends on the
bootloader and recovery web path remaining intact.
