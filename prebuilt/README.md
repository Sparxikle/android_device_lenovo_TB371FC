# Prebuilts

All of these come from the stock ZUI 16.0.474 (Android 14) firmware. Replace the
copies in git (they are from an older build) before building.

| File            | Source                                                        |
|-----------------|---------------------------------------------------------------|
| `kernel`        | `boot.img` -> unpack -> kernel (4.19.157, built 2024-11-29)    |
| `dtb/kona.dtb`  | `boot.img` -> unpack -> dtb (concatenated dtbs are fine)       |
| `dtbo.img`      | `dtbo` partition                                              |
| `vendor.img`    | `vendor` logical partition (not tracked in git)               |
| `odm.img`       | `odm` logical partition                                       |

Unpack with `unpack_bootimg --boot_img boot.img --out boot/` (header v2).
The vendor and odm images must come from the same build as the kernel and dtbo.
