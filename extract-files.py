#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024-2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from functools import partial

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

def _readelf() -> str:
    from glob import glob
    from shutil import which

    from extract_utils.tools import android_root

    found = sorted(glob(f'{android_root}/prebuilts/clang/host/linux-x86/clang-r*/bin/llvm-readelf'))
    tool = found[-1] if found else which('llvm-readelf') or which('readelf')
    assert tool, 'need llvm-readelf or readelf'
    return tool


def blob_fixup_clear_versions_impl(versions, ctx, file, file_path, *args, **kwargs):
    import re
    import subprocess

    out = subprocess.run(
        [_readelf(), '--dyn-syms', '-W', file_path], capture_output=True, text=True, check=True
    ).stdout
    syms = set()
    for line in out.splitlines():
        if ' UND ' not in line:
            continue
        m = re.search(r'(\S+)@(' + '|'.join(versions) + r')\b', line)
        if m:
            syms.add(m.group(1))
    for sym in sorted(syms):
        blob_fixup().clear_symbol_version_impl(sym, ctx, file, file_path)


# Blobs linked against an older libnativewindow whose versioned AHardwareBuffer
# symbols no longer match the vendor stub.
NATIVEWINDOW_USERS = (
    'vendor/lib/libface3d_dev.so',
    'vendor/lib64/camera/components/com.hq.node.snapshotalgo.so',
    'vendor/lib64/camera/components/com.qti.node.hqpreviewalgo.so',
    'vendor/lib64/libface3d_dev.so',
    'vendor/lib64/libmorpho_Ldc.so',
    'vendor/lib64/unnhal-acc-common.so',
)


blob_fixups: blob_fixups_user_type = {
    # Blob-only HIDL interface; host_init_verifier rejects it. The service is
    # class hal and also started on boot_completed, so no lazy start is lost.
    'vendor/etc/init/vendor.qti.hardware.tinno_keyboard@1.0-service.rc': blob_fixup()
        .regex_replace(r'.*interface vendor\.qti\.hardware\.tinno_keyboard@1\.0::.*\n', ''),
    # CBS_* symbols were dropped from the platform libcrypto.
    ('vendor/lib64/libwvhidl.so', 'vendor/lib64/mediadrm/libwvdrmengine.so'): blob_fixup()
        .add_needed('libcrypto_shim.so'),
    ('vendor/lib/libtinycompress-qti.so', 'vendor/lib64/libtinycompress-qti.so'): blob_fixup()
        .fix_soname(),
    # Stock SONAME is libfingerprint.default.so; libhardware dlopens it by path.
    'vendor/lib64/hw/fingerprint.default.so': blob_fixup()
        .fix_soname(),
    (
        'vendor/lib/hw/audio.primary.kona.so',
        'vendor/lib/liba2dpoffload.so',
        'vendor/lib/libbatterylistener.so',
        'vendor/lib/libcomprcapture.so',
        'vendor/lib/libexthwplugin.so',
        'vendor/lib/libhdmiedid.so',
        'vendor/lib/libhdmipassthru.so',
        'vendor/lib/libhfp.so',
        'vendor/lib/libsndmonitor.so',
        'vendor/lib/libspkrprot.so',
        'vendor/lib/libssrec.so',
        'vendor/lib64/hw/audio.primary.kona.so',
        'vendor/lib64/liba2dpoffload.so',
        'vendor/lib64/libbatterylistener.so',
        'vendor/lib64/libcomprcapture.so',
        'vendor/lib64/libexthwplugin.so',
        'vendor/lib64/libhdmiedid.so',
        'vendor/lib64/libhdmipassthru.so',
        'vendor/lib64/libhfp.so',
        'vendor/lib64/libsndmonitor.so',
        'vendor/lib64/libspkrprot.so',
        'vendor/lib64/libssrec.so',
    ): blob_fixup()
        .replace_needed('libtinycompress.so', 'libtinycompress-qti.so'),
    # Loaded into the running camera provider, which already started its
    # binder threadpool; configureRpcThreadpool(4, true) would shrink it and
    # libhidlbase aborts. Drop the call.
    'vendor/lib64/vendor.qti.hardware.camera.postproc@1.0-service-impl.so': blob_fixup()
        .binary_regex_replace(b'\x21\x00\x80\x52\x13\x0a\x00\x94', b'\x21\x00\x80\x52\x1f\x20\x03\xd5'),
    # Built against R, where sizeof(android::GraphicBuffer) was 0x100; they
    # allocate that much and run libui's constructor in it, which now writes
    # 0xd30 bytes and corrupts the heap. Allocate 0x1000 instead.
    (
        'vendor/lib64/camera/components/com.hq.node.snapshotalgo.so',
        'vendor/lib64/camera/components/com.qti.node.hqpreviewalgo.so',
    ): blob_fixup()
        .binary_regex_replace(b'\x01\x01\x80\x52\x02\x20\x80\x52', b'\x01\x01\x80\x52\x02\x00\x82\x52'),
    'vendor/bin/hw/android.hardware.neuralnetworks@1.3-service-qti': blob_fixup()
        .binary_regex_replace(b'\xf6\x03\x00\xaa\x00\x20\x80\x52\x15\x11\x40\xb9', b'\xf6\x03\x00\xaa\x00\x00\x82\x52\x15\x11\x40\xb9'),
    NATIVEWINDOW_USERS: blob_fixup()
        .call(partial(blob_fixup_clear_versions_impl, ('LIBNATIVEWINDOW',)), need_tmp_dir=False),
}  # fmt: skip


def lib_fixup_vendor_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_{partition}' if partition == 'vendor' else None


lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'libmmosal',
    ): lib_fixup_vendor_suffix,
}

namespace_imports = [
    'hardware/qcom-caf/sm8250',
    'hardware/qcom-caf/wlan',
    'vendor/qcom/opensource/commonsys-intf/display',
    'vendor/qcom/opensource/commonsys/display',
    'vendor/qcom/opensource/dataservices',
    'vendor/qcom/opensource/display',
]

module = ExtractUtilsModule(
    'TB371FC',
    'lenovo',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
