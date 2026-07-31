#!/usr/bin/env bash
set -euo pipefail

# Build a VMG3312-B10B fs+kernel firmware candidate from the vendor source tree.
# This intentionally does NOT call createZyNandimg and therefore does not build
# a full-flash image containing board-specific PSI/NVRAM/calibration data.

ROOT="${1:-.caya-agent/source-cache/zyxel-vmg3312}"
PROFILE="$ROOT/targets/VMG3312-B10B"
HOSTTOOLS="$ROOT/hostTools"
TARGET_FS="$PROFILE/fs"
OUTDIR="${2:-.caya-agent/build/output}"
OUT="$OUTDIR/CaYaRouter-VMG3312-B10B-AAPP7.bin"

mkdir -p "$OUTDIR"

required=(
  "$HOSTTOOLS/mkfs.jffs2"
  "$HOSTTOOLS/bcmZyNandImageBuilder"
  "$TARGET_FS/webs/Brick/index.html"
  "$TARGET_FS/webs/Brick/caya/index.html"
  "$TARGET_FS/webs/Brick/caya/full-styles.css"
  "$TARGET_FS/webs/Brick/caya/full-app.js"
  "$PROFILE/vmlinux.lz"
  "$ROOT/targets/cfe/cfe63268nand128.bin"
)
for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "Missing required path: $path" >&2; exit 2; }
done

printf '/vmlinux.lz\n' > "$HOSTTOOLS/nocomprlist.caya"
cp "$PROFILE/vmlinux.lz" "$TARGET_FS/vmlinux.lz"
printf '%s\n' '1.00(AAPP.7)' > "$TARGET_FS/etc/image_version"

"$HOSTTOOLS/mkfs.jffs2" \
  -b -p -n -e 131072 \
  -r "$TARGET_FS" \
  -o "$OUTDIR/rootfs128kb-caya.img" \
  -N "$HOSTTOOLS/nocomprlist.caya"

"$HOSTTOOLS/bcmZyNandImageBuilder" \
  --output "$OUT" \
  --chip 63268 \
  --board 963168VX \
  --internalversion='1.00(AAPP.7)' \
  --externalversion='1.00(AAPP.7)' \
  --modelid=400e \
  --cmodelid=400e \
  --cfefile "$ROOT/targets/cfe/cfe63268nand128.bin" \
  --rootfsfile "$OUTDIR/rootfs128kb-caya.img"

rm -f "$HOSTTOOLS/nocomprlist.caya"
sha256sum "$OUT" | tee "$OUT.sha256"
echo "Candidate created: $OUT"
echo "Run tools/firmware_candidate_guard.py before any upload."
