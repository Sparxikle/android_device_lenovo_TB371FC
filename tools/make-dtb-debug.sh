#!/bin/bash
# Bring-up only: build prebuilt/dtb-debug from the stock DTB plus a ramoops
# region, so a hang caught by the watchdog leaves its log in /sys/fs/pstore.
# The Xiaomi-style ramoops_memreserve at 0xb0000000 can't work here: stock
# reserves that address (bootlog_mem, 512K, owned by cnss_pci).
set -e
cd "$(dirname "$0")/../prebuilt"

# dtb/kona.dtb is several DTBs back to back (the ABL picks one by board id;
# TB371FC boots index 0). fdtput only handles one, so patch each piece.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
python3 -I - dtb/kona.dtb "$tmp" <<'PY'
import struct, sys
data = open(sys.argv[1], 'rb').read()
off = i = 0
while off < len(data):
    magic, size = struct.unpack('>II', data[off:off + 8])
    assert magic == 0xd00dfeed, hex(off)
    open('%s/%02d.dtb' % (sys.argv[2], i), 'wb').write(data[off:off + size])
    off += size
    i += 1
PY

patch_dtb() {
    d=$1
    n=/reserved-memory/ramoops@b0800000

    # 1 MiB at 0xb0800000: free RAM in the stock memory map.
    fdtput -c "$d" "$n"
    fdtput -t s "$d" "$n" compatible ramoops
    fdtput -t x "$d" "$n" reg 0 0xb0800000 0 0x100000
    fdtput -t x "$d" "$n" record-size 0x10000
    fdtput -t x "$d" "$n" console-size 0x80000
    fdtput -t x "$d" "$n" pmsg-size 0x40000
    fdtput -t s "$d" "$n" no-map ""

    # Hang test: on Android the board dies ~1 s after msm_cvp's hyp_assign fails
    # (when the camera provider starts). Keep CVP out of the picture.
    fdtput -t s "$d" /soc/qcom,cvp@ab00000 status disabled
}

for d in "$tmp"/*.dtb; do
    # Skip pieces without the nodes we touch (the tail one is tiny).
    fdtget "$d" /soc/qcom,cvp@ab00000 compatible >/dev/null 2>&1 || continue
    patch_dtb "$d"
done
mkdir -p dtb-debug
cat "$tmp"/*.dtb > dtb-debug/kona.dtb
