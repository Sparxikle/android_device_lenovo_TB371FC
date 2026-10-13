#!/usr/bin/env python3
"""Generate TB371FC lineage-24.0 proprietary-files.txt from the stock vendor listing.

Base: LineageOS xiaomi/sm8250-common (lineage-24.0) blob list, keeping only entries
that exist in the Lenovo vendor and only the sections a Wi-Fi tablet needs; then
Lenovo-specific sections selected by path rules.
"""
import re, sys
VENDOR_LIST, XIAOMI_LIST, OUT = sys.argv[1:4]
NEEDED_LIST = sys.argv[4] if len(sys.argv) > 4 else None  # 'path lib' lines from readelf

files, links = set(), {}
for l in open(VENDOR_LIST):
    p = l.rstrip('\n').split(' ')
    if len(p) < 2: continue
    path = 'vendor/' + p[1]
    if p[0] == 'f': files.add(path)
    elif p[0] == 'l': links[path] = p[2] if len(p) > 2 else ''

DROP_SECTIONS = {
    'Camera motor (sound) - from lmi', 'CNE', 'DPM', 'GNSS', 'GNSS configs', 'IMS',
    'Mink-Lowi Interface daemon', 'NVRAM', 'Power-off alarm', 'RIL', 'Secure element',
    'Thermal', 'WiFi Display (system) - from marvel', 'WiFi Display (vendor)',
    'Keymaster',  # Lenovo ships keymaster 4.1, listed below
}
taken = set()
# Never shipped. 32-bit mm-camera face detection: only the 64-bit camx stack
# dlopens it (the provider is 64-bit only), and it imports LIBC_PRIVATE symbols.
taken.update({'vendor/lib/libmmcamera_faceproc.so', 'vendor/lib/libmmcamera_faceproc2.so'})
out = []

# Libraries the source tree builds as vendor modules; shipping the stock copy clashes.
BUILT_FROM_SOURCE = {'libalsautils.so', 'libnbaio_mono.so', 'libwebrtc_audio_preprocessing.so',
                     'libcamera2ndk_vendor.so', 'libsensorndkbridge.so',
                     # HIDL interface libs from vendor/qcom/opensource/interfaces (system_ext + vendor_available)
                     'vendor.qti.hardware.camera.device@1.0.so', 'vendor.qti.hardware.camera.postproc@1.0.so',
                     # hardware/lineage/compat *-vendorcompat, pulled in by qcom-caf common
                     'libprotobuf-cpp-full-3.9.1.so', 'libprotobuf-cpp-lite-3.9.1.so',
                     # sh_binary modules in the qcom display / media repos
                     'init.qti.display_boot.sh', 'init.qti.media.sh'}

# Stock files whose path is also installed by an AOSP source module.
# The stock camera provider rc has `override`, so a later-parsed name wins over AOSP's rc.
RENAME = {
    # Qualcomm's tinycompress has the metadata/gapless API the audio blobs use;
    # AOSP's libtinycompress doesn't. Ship it under its own name.
    'vendor/lib/libtinycompress.so': 'vendor/lib/libtinycompress.so:vendor/lib/libtinycompress-qti.so',
    'vendor/lib64/libtinycompress.so': 'vendor/lib64/libtinycompress.so:vendor/lib64/libtinycompress-qti.so',
    'vendor/etc/init/android.hardware.camera.provider@2.4-service_64.rc':
        'vendor/etc/init/android.hardware.camera.provider@2.4-service_64.rc:'
        'vendor/etc/init/vendor.qti.camera.provider@2.4-service_64.rc',
}

def emit_section(name, entries):
    entries = [e for e in entries if e.split(';')[0].split(':')[0].split('|')[0].lstrip('-') not in taken
               and e.split(';')[0].split('/')[-1] not in BUILT_FROM_SOURCE]
    if not entries: return
    out.append(f'\n# {name}')
    for e in sorted(entries, key=lambda s: s.lstrip('-')):
        src = e.split(';')[0].split(':')[0].split('|')[0].lstrip('-')
        taken.add(src)
        out.append(RENAME.get(e, e))

# --- 1. common kona blobs from the xiaomi list
sec, buf = None, {}
for l in open(XIAOMI_LIST):
    l = l.rstrip('\n')
    if l.startswith('# '):
        sec = l[2:]; continue
    if not l.strip() or l.startswith('#') or sec is None: continue
    if sec in DROP_SECTIONS: continue
    entry = re.sub(r'\|[0-9a-f]{40}', '', l)           # drop xiaomi hash pins
    src = entry.split(';')[0].split(':')[0].lstrip('-')
    if src not in files: continue
    buf.setdefault(sec, []).append(entry)
for s, e in buf.items(): emit_section(s, e)

# --- 2. Lenovo / device-specific sections, by rule
def pick(pred): return [f for f in sorted(files) if pred(f)]
def under(*prefixes): return lambda f: f.startswith(prefixes)
def names(dirs, *ns): return lambda f: any(f == f'{d.rstrip("/")}/{n}' for d in dirs for n in ns)
LIBS = ('vendor/lib/', 'vendor/lib64/')

emit_section('ACDB', pick(under('vendor/etc/acdbdata/')))
# lib64/rfsa only duplicates two skels from lib/rfsa, and extract-utils can't package it
emit_section('ADSP modules', pick(under('vendor/lib/rfsa/adsp/')))
emit_section('Audio (HAL)', pick(names(('vendor/lib/hw', 'vendor/lib64/hw'),
        'audio.primary.kona.so', 'sound_trigger.primary.kona.so')) +
    pick(names(LIBS, 'libaudio_log_utils.so', 'libaudioparsers.so', 'libaudioconfigstore.so',
        'libhdmipassthru.so', 'liba2dpoffload.so', 'libsndmonitor.so', 'libspkrprot.so',
        'libcirrusspkrprot.so', 'libcomprcapture.so', 'libssrec.so', 'libhdmiedid.so', 'libhfp.so',
        'libexthwplugin.so', 'libbatterylistener.so', 'libqtigef.so', 'libaudioalsa.so',
        'libacdbloader.so', 'libacdb-fts.so', 'libaudcal.so', 'libacdbrtac.so', 'libadiertac.so',
        'libbluetooth_audio_session_qti.so', 'libbluetooth_audio_session_qti_2_1.so',
        'btaudio_offload_if.so', 'libalsautils.so', 'libaudioroute_ext.so', 'libresampler.so',
        'libnbaio_mono.so', 'libwebrtc_audio_preprocessing.so')))
emit_section('Audio configs', pick(lambda f: re.fullmatch(
    r'vendor/etc/(mixer_paths\w*\.xml|audio_platform_info\w*\.xml|sound_trigger_\w+\.xml|'
    r'audio_tuning_mixer\.txt|ftm_test_config\S*)', f) is not None))
emit_section('Audio FX modules (stock)', [f for f in pick(under('vendor/lib/soundfx/', 'vendor/lib64/soundfx/'))
    if not re.search(r'/lib(sw(dap|gamedap|vqe)|dlbvol|bundlewrapper|reverbwrapper|visualizer|downmix|'
                     r'ldnhncr|dynproc|effectproxy|audiopreprocessing)\.so$', f)])  # Dolby DAP out, AOSP ones built
emit_section('Audio firmware', pick(lambda f: re.fullmatch(r'vendor/firmware/tfa98xx_\w+\.cnt', f) is not None))
emit_section('Camera', pick(under('vendor/lib/camera/', 'vendor/lib64/camera/')) +
    pick(names(('vendor/lib/hw', 'vendor/lib64/hw'), 'camera.qcom.so', 'com.qti.chi.override.so')) +
    pick(lambda f: f.startswith(LIBS) and re.search(
        r'/(libcamx\w*|libchilog|libcom\.qti\.chinodeutils|com\.qti\.feature2\.\w+|libcamerapostproc|'
        r'libmmcamera\w*|libcamera_nn_stub|libipebpsstriping|libswregistrationalgo|libStereoRectifyWrapper|'
        r'libScenescape|libmorpho_Ldc|libFace3D\w*|libface3d_dev|libcvp\w*|libsynx|libhalide_hexagon_host|'
        r'libcamera2ndk_vendor|libos|libqcodec2\w*|vendor\.qti\.hardware\.camera\.\S+|vendor\.qti\.hardware\.cvp@\S+|'
        r'camera\.device@\S+|libtracker_6dof_impl|libjson|libtinyxml)\.so$', f) is not None))
# AOSP's HIDL camera provider/device defaults no longer build on 17; ship the stock ones.
emit_section('Audio (QTI tinycompress)', ['vendor/lib/libtinycompress.so', 'vendor/lib64/libtinycompress.so'])
emit_section('Camera provider', pick(lambda f: re.search(
    r'(bin/hw/android\.hardware\.camera\.provider@2\.4-service_64|'
    r'etc/init/android\.hardware\.camera\.provider@2\.4-service_64\.rc|'
    r'lib(64)?/(hw/)?android\.hardware\.camera\.provider@2\.4-(impl|legacy|external)\.so)$', f) is not None))
emit_section('Camera configs', pick(lambda f: f in ('vendor/etc/morpho_ldc.bin',)) + pick(under('vendor/etc/face3d/')) +
    pick(lambda f: f == 'vendor/bin/init.dtab.camera.sh'))
emit_section('Camera firmware', pick(lambda f: f == 'vendor/firmware/CAMERA_ICP.elf'))
emit_section('Display calibration', pick(lambda f: re.fullmatch(r'vendor/etc/qdcm_calib_data_nt36532\w+\.xml', f) is not None))
# Goodix TEE fingerprint: legacy fingerprint.default HAL behind the AOSP
# IBiometricsFingerprint@2.1 service, which is built from source.
emit_section('Fingerprint', pick(names(('vendor/lib64',), 'libgf_ca.so', 'libgf_hal.so',
        'libgoodixhwfingerprint.so', 'libvendor.goodix.hardware.biometrics.fingerprint@2.1.so')) +
    pick(lambda f: f == 'vendor/lib64/hw/fingerprint.default.so'))
emit_section('Firmware', [f for f in pick(under('vendor/firmware/'))
    if f.count('/') == 2 and not f.endswith(('.cnt',)) and f != 'vendor/firmware/CAMERA_ICP.elf'] +
    pick(under('vendor/firmware/wlan/')))
emit_section('Init scripts', [f for f in pick(lambda f: re.fullmatch(r'vendor/bin/init\.(qcom|qti|class_main|mdm|crda)\S*\.sh', f) is not None)
    if f != 'vendor/bin/init.qcom.usb.sh'])  # built from vendor/qcom/opensource/usb
emit_section('Input (keyboard cover)', pick(lambda f: 'tinno_keyboard' in f or 'motorola.hardware.input' in f))
# Kernel modules: not shipped. The kernel is built from source and stock .ko files are
# signed with Lenovo's key (MODULE_SIG_FORCE), so mark them taken to keep them out.
taken.update(pick(under('vendor/lib/modules/')))
emit_section('Keymaster', pick(lambda f: 'keymaster@4.1' in f and not f.endswith('.xml')) +
    pick(names(('vendor/lib64',), 'libkeymasterdeviceutils.so', 'libkeymasterprovision.so',
        'libkeymasterutils.so', 'libqtikeymaster4.so', 'libspcom.so')))
emit_section('Sensors', pick(lambda f: f in (
        'vendor/bin/sensors.qti', 'vendor/bin/sscrpcd', 'vendor/bin/init.qcom.sensors.sh',
        'vendor/bin/hw/vendor.qti.hardware.sensorscalibrate@1.0-service',
        'vendor/etc/init/init.vendor.sensors.rc', 'vendor/etc/init/vendor.sensors.qti.rc',
        'vendor/etc/init/vendor.sensors.sscrpcd.rc',
        'vendor/etc/init/vendor.qti.hardware.sensorscalibrate@1.0-service.rc')) +
    pick(lambda f: f.startswith(LIBS) and '/rfsa/' not in f and re.search(
        r'/(sensors\.\w+|libssc\w*|libsns\w*|libsensor\w*|libsensorslog|libnotifyaudiohal|'
        r'vendor\.qti\.hardware\.sensorscalibrate@1\.0(-impl)?|libprotobuf-cpp-(full|lite)-3\.9\.1)\.so$', f) is not None))
emit_section('Sensors configs', pick(under('vendor/etc/sensors/')))
emit_section('Media configs (stock)', pick(lambda f: f == 'vendor/etc/media_profiles_vendor.xml'))
emit_section('Public libraries', pick(lambda f: f == 'vendor/etc/public.libraries.txt'))
emit_section('Ueventd', pick(lambda f: f == 'vendor/etc/ueventd.rc'))
emit_section('Thermal configs', pick(lambda f: f == 'vendor/etc/thermal-engine.conf'))
emit_section('Wi-Fi configs', pick(under('vendor/etc/wifi/qca6390/', 'vendor/etc/wifi/qca6490/')) +
    pick(lambda f: f == 'vendor/etc/wifi/WCNSS_qcom_cfg.ini'))

# --- 3. dependency closure: stock-only libraries that the blobs above link against
# Provided by the platform or built from source (vendor variants), never shipped from stock.
PLATFORM_PROVIDED = {
    'libEGL_adreno.so', 'libGLESv2_adreno.so', 'libq3dtools_adreno.so',  # SYMLINK= of egl/ blobs
    'libhidltransport.so', 'libhwbinder.so', 'libtinycompress.so', 'libdrm.so',
    'libcodec2_vndk.so', 'libcodec2_hidl@1.0.so', 'libstagefright_bufferpool@2.0.1.so',
    'libavservices_minijail.so', 'android.hardware.sensors@2.0-ScopedWakelock.so',
    'libbluetooth_audio_session.so',
    'com.dsi.ant@1.0.so',  # external/ant-wireless
} | BUILT_FROM_SOURCE
# Module names defined by the qcom source repos (display, media, audio, interfaces, ...),
# collected with tools/README.md; their vendor variants are built, not extracted.
import os
_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source-modules.txt')
SOURCE_MODULES = set(open(_src).read().split()) if os.path.exists(_src) else set()
if NEEDED_LIST:
    import collections
    needed = collections.defaultdict(set)
    for l in open(NEEDED_LIST):
        p = l.split()
        if len(p) == 2: needed['vendor/' + p[0]].add(p[1])
    deps, queue = {}, list(taken)
    while queue:
        b = queue.pop()
        for n in needed.get(b, ()):
            if n in PLATFORM_PROVIDED or n[:-3] in SOURCE_MODULES: continue
            cands = (['vendor/lib64/' + n] if '/lib64/' in b else ['vendor/lib/' + n] if '/lib/' in b
                     else ['vendor/lib64/' + n, 'vendor/lib/' + n])
            for c in cands:
                if c in files:
                    if c not in taken and c not in deps:
                        deps[c] = b; queue.append(c)
                    break
    emit_section('Dependencies (stock-only libraries the blobs above link against)', list(deps))

hdr = ['# All unpinned blobs are extracted from TB371FC stock (ZUI, Android 14, vendor frozen at R).',
       '# Generated by gen_blobs.py from the stock vendor listing; edit the generator, not this file.']
open(OUT, 'w').write('\n'.join(hdr + out) + '\n')

# Symlinks that point outside the extracted blobs (rfs, persist, data) become install_symlink modules.
# vendor/rfs/* links are already installed by the qcom-caf common tree.
sym = {k: v for k, v in links.items() if v.startswith('/') and not v.startswith('/vendor/lib')
       and k != 'vendor/odm' and not k.startswith('vendor/rfs/')}
with open(OUT + '.symlinks', 'w') as f:
    for k, v in sorted(sym.items()): f.write(f'{k} {v}\n')
print(f'{len(taken)} blobs, {len(sym)} symlinks')
