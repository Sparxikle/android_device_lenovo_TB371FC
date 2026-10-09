`gen_blobs.py` regenerates `proprietary-files.txt` from listings of the stock vendor:

    cd /mnt/stock-vendor
    find . -printf '%y %P %l\n' | sort > stock-vendor-files.txt
    find . -type f \( -name '*.so' -o -path './bin/*' \) | while read f; do
      readelf -d "$f" | awk -v f="${f#./}" '/NEEDED/{gsub(/[][]/,"",$5); print f, $5}'
    done > stock-needed.txt

    python3 tools/gen_blobs.py tools/stock-vendor-files.txt \
        <xiaomi sm8250-common lineage-24.0>/proprietary-files.txt proprietary-files.txt \
        tools/stock-needed.txt

1. The xiaomi sm8250-common entries that exist in the Lenovo vendor, minus the radio /
   GNSS / IMS / WFD sections a Wi-Fi tablet doesn't need.
2. Lenovo sections by path rules.
3. The dependency closure: stock-only libraries those blobs link against. Libraries the
   platform or the qcom source repos provide (`source-modules.txt`) are skipped.

Symlinks pointing outside the blobs go to `proprietary-files.txt.symlinks`;
`symlinks/Android.bp` is generated from it.
