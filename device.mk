#
# Copyright (C) 2018-2021 ArrowOS
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/lenovo/TB371FC

# Enable updating of APEXes
$(call inherit-product, $(SRC_TARGET_DIR)/product/updatable_apex.mk)

# Setup dalvik vm configs
$(call inherit-product, frameworks/native/build/phone-xhdpi-6144-dalvik-heap.mk)

# Installs gsi keys into ramdisk, to boot a GSI with verified boot.
$(call inherit-product, $(SRC_TARGET_DIR)/product/developer_gsi_keys.mk)

# Virtual A/B (stock lpdump: virtual_ab_device, uncompressed COW)
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/launch.mk)

# Recovery
# Touch reports in the panel's native portrait axes (X 0-18400, Y 0-29440) while
# recovery draws landscape: swap X/Y and flip Y, like TWRP's SWAP_XY + FLIP_Y.
# The panel uses a dual layer mixer DSC topology; minui has to drive it with one
# plane per mixer through atomic commits (needs the bootable/recovery minui change).
# The generated vendor build.prop only reaches recovery's prop.default here, since
# the real vendor image is the stock prebuilt.
PRODUCT_VENDOR_PROPERTIES += \
    ro.minui.default_touch_rotation=ROTATION_RIGHT \
    ro.minui.drm_sde_split=true

# The Novatek touch IC runs firmware from RAM; the driver requests it on resume.
# Recovery doesn't mount /vendor, so ship it in the ramdisk where the kernel's direct
# loader (/lib/firmware) and ueventd's fallback (/vendor/firmware) both find it.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/prebuilt/firmware/novatek_ts_tm_fw_6.bin:$(TARGET_COPY_OUT_RECOVERY)/root/lib/firmware/novatek_ts_tm_fw_6.bin \
    $(DEVICE_PATH)/prebuilt/firmware/novatek_ts_tm_fw_6.bin:$(TARGET_COPY_OUT_RECOVERY)/root/vendor/firmware/novatek_ts_tm_fw_6.bin

# Shipping API level
# Stock reports ro.product.first_api_level=33, but the vendor is R-frozen
# (ro.board.api_level=30, FCM 5). Stay at 30 so build-time VINTF/shipping
# checks are evaluated against the vendor we actually ship.
PRODUCT_SHIPPING_API_LEVEL := 30

# VNDK
# Stock vendor is frozen at R (ro.vndk.version=30). BOARD_VNDK_VERSION and
# PRODUCT_TARGET_VNDK_VERSION are gone since V; ship the v30 VNDK APEX instead.
PRODUCT_EXTRA_VNDK_VERSIONS := 30

# A/B
AB_OTA_POSTINSTALL_CONFIG += \
    RUN_POSTINSTALL_system=true \
    POSTINSTALL_PATH_system=system/bin/otapreopt_script \
    FILESYSTEM_TYPE_system=ext4 \
    POSTINSTALL_OPTIONAL_system=true

# Audio
PRODUCT_PACKAGES += \
    TB371FCParts \
    tinymix

# Four speakers: the speaker deep-buffer output is opened as quad (see the policy
# file), and ro.audio.remix_stereo_to_rear makes AudioFlinger feed the rear pair
# from stereo tracks. product/vendor_overlay is never mounted on this build, so
# the policy is bind-mounted over the stock one from init.tb371fc.rc instead.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/audio/audio_policy_configuration.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/tb371fc/audio_policy_configuration.xml

# Boot animation
TARGET_SCREEN_HEIGHT := 1840
TARGET_SCREEN_WIDTH := 2944

# The panel is portrait-native; draw the boot animation in landscape with the
# USB-C port on the right, like ZUI. The suffix is the internal panel's display id.
PRODUCT_PRODUCT_PROPERTIES += \
    ro.bootanim.set_orientation_4630947161651687041=ORIENTATION_90

# Boot control
# Normal boot uses the stock vendor's bootctrl; recovery gets the AIDL one from qcom-caf.
PRODUCT_PACKAGES += \
    android.hardware.boot-service.qti.recovery

# 4.19 has no UFS BSG node; gpt-utils must switch the XBL boot LUN via /dev/sg*
$(call soong_config_set,QTI_GPT_UTILS,USE_BSG_FRAMEWORK,false)

PRODUCT_PACKAGES_DEBUG += \
    bootctl

# Dynamic partitions
PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_BUILD_SUPER_PARTITION := false

# fastbootd
PRODUCT_PACKAGES += \
    android.hardware.fastboot@1.0-impl-mock \
    fastbootd

# F2FS utilities
PRODUCT_PACKAGES += \
    sg_write_buffer \
    f2fs_io \
    check_f2fs

# Face unlock
# Stock has no face HAL (ZUI's was app-side). Use the software sense provider:
# packages/apps/FaceUnlock plus the frameworks/base sense provider patch.
PRODUCT_PACKAGES += \
    FaceUnlock

PRODUCT_SYSTEM_EXT_PROPERTIES += \
    ro.face.sense_service=true

PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.biometrics.face.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/android.hardware.biometrics.face.xml

# Input
PRODUCT_COPY_FILES += \
    $(call find-copy-subdir-files,*,$(DEVICE_PATH)/configs/idc,$(TARGET_COPY_OUT_PRODUCT)/usr/idc) \
    $(call find-copy-subdir-files,*,$(DEVICE_PATH)/configs/keylayout,$(TARGET_COPY_OUT_PRODUCT)/usr/keylayout)

# Init
PRODUCT_PACKAGES += \
    init.recovery.qcom.rc \
    init.tb371fc.rc \
    fstab.qcom.ramdisk

# Overlay
DEVICE_PACKAGE_OVERLAYS += \
    $(DEVICE_PATH)/overlay \
    $(DEVICE_PATH)/overlay-lineage

# Properties
include $(DEVICE_PATH)/properties/default.mk

# Soong namespaces
PRODUCT_SOONG_NAMESPACES += \
    $(DEVICE_PATH) \
    hardware/qcom-caf/bootctrl

# Update engine
PRODUCT_PACKAGES += \
    checkpoint_gc \
    otapreopt_script \
    update_engine \
    update_engine_sideload \
    update_verifier

PRODUCT_PACKAGES_DEBUG += \
    update_engine_client

#DolbyManager
PRODUCT_SOONG_NAMESPACES += hardware/dolby
PRODUCT_PACKAGES += DolbyManager
