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

run_tool() {
  if [[ -n "${CAYA_I386_RUNTIME:-}" ]]; then
    "$CAYA_I386_RUNTIME/usr/lib/i386-linux-gnu/ld-linux.so.2" \
      --library-path "$CAYA_I386_RUNTIME/usr/lib/i386-linux-gnu" \
      "$@"
  else
    "$@"
  fi
}

required=(
  "$HOSTTOOLS/mkfs.jffs2"
  "$HOSTTOOLS/bcmZyNandImageBuilder"
  "$TARGET_FS/webs/Brick/index.html"
  "$TARGET_FS/webs/Brick/caya/index.html"
  "$TARGET_FS/webs/Brick/caya/full-styles.css"
  "$TARGET_FS/webs/Brick/caya/live-styles.css"
  "$TARGET_FS/webs/Brick/caya/live-modules.js"
  "$TARGET_FS/webs/Brick/caya/caya-loader.js"
  "$TARGET_FS/webs/Brick/caya/full-app.js"
  "$PROFILE/vmlinux.lz"
  "$ROOT/targets/cfe/cfe63268nand128.bin"
)
for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "Missing required path: $path" >&2; exit 2; }
done

printf '/vmlinux.lz\n' > "$HOSTTOOLS/nocomprlist.caya"
cp "$PROFILE/vmlinux.lz" "$TARGET_FS/vmlinux.lz"

DEVICE_ARGS=()
if [[ -n "${CAYA_DEVICE_TABLE:-}" ]]; then
  [[ -f "$CAYA_DEVICE_TABLE" ]] || { echo "Missing device table: $CAYA_DEVICE_TABLE" >&2; exit 2; }
  DEVICE_ARGS=(-D "$CAYA_DEVICE_TABLE")
fi

COMPR_ARGS=()
if [[ -n "${CAYA_COMPR_MODE:-}" ]]; then
  COMPR_ARGS=(-m "$CAYA_COMPR_MODE")
fi

IMGDEFAULT_ARGS=()
if [[ -n "${CAYA_IMGDEFAULT_FILE:-}" ]]; then
  [[ -f "$CAYA_IMGDEFAULT_FILE" ]] || { echo "Missing image-default file: $CAYA_IMGDEFAULT_FILE" >&2; exit 2; }
  IMGDEFAULT_ARGS=(--imgdefaultfile="$CAYA_IMGDEFAULT_FILE")
fi

run_tool "$HOSTTOOLS/mkfs.jffs2" \
  -b -p -n -e 131072 \
  -r "$TARGET_FS" \
  -o "$OUTDIR/rootfs128kb-caya.img" \
  -N "$HOSTTOOLS/nocomprlist.caya" \
  "${COMPR_ARGS[@]}" \
  "${DEVICE_ARGS[@]}"

run_tool "$HOSTTOOLS/bcmZyNandImageBuilder" \
  --output "$OUT" \
  --chip 63268 \
  --board 963168VX \
  --internalversion='1.00(AAPP.7)' \
  --externalversion='1.00(AAPP.7)' \
  --modelid=400e \
  --cmodelid=400e \
  --cfefile "$ROOT/targets/cfe/cfe63268nand128.bin" \
  --rootfsfile "$OUTDIR/rootfs128kb-caya.img" \
  "${IMGDEFAULT_ARGS[@]}"

rm -f "$HOSTTOOLS/nocomprlist.caya"
sha256sum "$OUT" | tee "$OUT.sha256"
echo "Candidate created: $OUT"
echo "Run tools/firmware_candidate_guard.py before any upload."
