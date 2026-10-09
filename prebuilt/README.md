# Prebuilts

All of these come from the stock ZUI 16.0.474 (Android 14) firmware.

| File            | Source                                                        |
|-----------------|---------------------------------------------------------------|
| `kernel`        | `boot.img` -> unpack -> kernel (4.19.157, built 2024-11-29)    |
| `dtb/kona.dtb`  | `boot.img` -> unpack -> dtb (concatenated dtbs are fine)       |
| `dtbo.img`      | `dtbo` partition                                              |

Unpack with `unpack_bootimg --boot_img boot.img --out boot/` (header v2).

Since lineage-24.0 the vendor and odm partitions are built from source. The
stock vendor only contributes blobs (incl. the kernel modules matching `kernel`)
through `proprietary-files.txt` and `extract-files.py`; it must come from the same
firmware build as the kernel and dtbo.
