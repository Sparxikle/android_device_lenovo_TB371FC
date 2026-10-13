#!/bin/bash
# Add to the stock DTB (prebuilt/dtb) what the source-built kernel takes from
# the DT where Lenovo's kernel hardcodes it. Idempotent: only sets properties.
# Run tools/make-dtb-debug.sh afterwards, it is built from this DTB.
set -e
cd "$(dirname "$0")/../prebuilt"

# dtb/kona.dtb is several DTBs back to back (the ABL picks one by board id).
# fdtput only handles one, so patch each piece.
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

# TFA9894 speaker amplifiers on qupv3_se15_i2c, as <address> <rotation slots>.
# Rotation slots: <speaker DCS> TDM slots for TFA9894_CHAN_SELECTOR 0..3, the
# table of the stock audio_tfa98xx.ko (indexed there by container device:
# 0x34, 0x37, 0x36, 0x35).
amps=(
    "34 0 1 1 0 3 2 2 3"
    "35 2 3 3 2 1 0 0 1"
    "36 2 3 0 1 1 0 3 2"
    "37 0 1 2 3 3 2 1 0"
)

patch_dtb() {
    d=$1
    tlmm=$(fdtget -t x "$d" /soc/pinctrl@f000000 phandle)
    # New phandles go above the highest one in use. The DTBO is applied on
    # top by the bootloader, which renumbers its own phandles past ours.
    next=$(dtc -I dtb -O dts -q "$d" | sed -n 's/.*phandle = <0x\([0-9a-f]*\)>.*/\1/p' |
        sort -u | while read -r p; do echo $((16#$p)); done | sort -n | tail -1)
    codecs=()

    for amp in "${amps[@]}"; do
        set -- $amp
        n=/soc/i2c@884000/tfa98xx@$1
        shift

        # Speaker ID (TLMM 71) selects the tuning: low YC, high QS speakers.
        fdtput -t x "$d" "$n" spk-id-gpios "$tlmm" 0x47 0
        fdtput -t s "$d" "$n" firmware-name tfa98xx_YC.cnt tfa98xx_QS.cnt
        fdtput -t u "$d" "$n" tfa,rotation-tdm-slots "$@"

        ph=$(fdtget -t x "$d" "$n" phandle 2>/dev/null) || {
            next=$((next + 1))
            ph=$(printf %x $next)
            fdtput -t x "$d" "$n" phandle "$ph"
        }
        fdtput -t x "$d" "$n" "#sound-dai-cells" 0
        codecs+=("$ph")
    done

    # The amplifiers are the codecs of the speaker back end (PRI TDM RX).
    snd=$(fdtget "$d" /__symbols__ kona_snd)
    fdtget "$d" "$snd/pri-tdm-rx-0" link-name >/dev/null 2>&1 ||
        fdtput -c -p "$d" "$snd/pri-tdm-rx-0/codec"
    fdtput -t s "$d" "$snd/pri-tdm-rx-0" link-name PRI_TDM_RX_0
    fdtput -t x "$d" "$snd/pri-tdm-rx-0/codec" sound-dai "${codecs[@]}"
}

for d in "$tmp"/*.dtb; do
    # Skip pieces without the amplifiers (the tail one is tiny).
    fdtget "$d" /soc/i2c@884000/tfa98xx@34 compatible >/dev/null 2>&1 || continue
    patch_dtb "$d"
done
cat "$tmp"/*.dtb > dtb/kona.dtb
