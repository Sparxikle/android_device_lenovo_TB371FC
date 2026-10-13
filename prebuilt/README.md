# Prebuilts

All of these come from the stock ZUI 16.0.474 (Android 14) firmware.

| File            | Source                                                        |
|-----------------|---------------------------------------------------------------|
| `dtb/kona.dtb`  | `boot.img` -> unpack -> dtb (concatenated dtbs are fine)       |
| `dtbo.img`      | `dtbo` partition, cut to the DT table's `total_size`          |

Unpack with `unpack_bootimg --boot_img boot.img --out boot/` (header v2).

The dtbo must be the one dumped from the device: an earlier copy here (same
16.0.474 label) had a 22-command Tianma panel init without the CABC/PWM and
backlight-control commands, so after the first panel power cycle the KTZ8866s
(PWM-dimmed on Tianma) never saw PWM and the screen stayed black.

Since lineage-24.0 the vendor and odm partitions are built from source. The
stock vendor only contributes blobs (incl. the kernel modules matching `kernel`)
through `proprietary-files.txt` and `extract-files.py`; it must come from the same
firmware build as the kernel and dtbo.

The kernel itself is built from source (kernel/lenovo/sm8250); only the
stock DTB and DTBO are still used.

`dtb-debug/kona.dtb` is the stock DTB plus a `simple-framebuffer` node at the
bootloader splash buffer (0x9c000000, 2944x1840 x8r8g8b8) and the msm watchdog
disabled, added with fdtput so nothing else changes. Only used when
TB371FC_KERNEL_DEBUG=true.
