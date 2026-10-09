#!/system/bin/sh
# Copyright (C) 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
# The four TFA9894 amps sit on a 4-slot TDM link (PRI_TDM_RX_0), but the stock HAL
# only programs a stereo output, so slots 3/4 stay silent. On ZUI something outside
# the HAL fed all four; here we set the DSP's per-stream channel mixer once so every
# playback stream is expanded L,R -> L,R,L,R. Values are latched by the kernel and
# applied whenever a stream opens; the HAL never touches them (it only writes these
# controls when its own custom_mtmx lookup matches, which needs a 4ch backend).
# Which corners get L and R is chosen per rotation by TFA9894_CHAN_SELECTOR, driven
# through the HAL's gsensor_rotation parameter by the TB371FCParts app.

TINYMIX=/system/bin/tinymix
ONE=16384  # 1.0 in Q14

for id in 0 1 4 7 9 11 12 13 24 25 26 27 28 29; do
    $TINYMIX "AudStr $id ChMixer Cfg" >/dev/null 2>&1 || continue
    $TINYMIX "AudStr $id ChMixer Weight Ch 1" $ONE 0
    $TINYMIX "AudStr $id ChMixer Weight Ch 2" 0 $ONE
    $TINYMIX "AudStr $id ChMixer Weight Ch 3" $ONE 0
    $TINYMIX "AudStr $id ChMixer Weight Ch 4" 0 $ONE
    # enable, rule 0, 2 in, 4 out, speaker backend (HAL backend index 0, +1)
    $TINYMIX "AudStr $id ChMixer Cfg" 1 0 2 4 1
done
