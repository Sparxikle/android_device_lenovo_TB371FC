/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.tb371fc.parts;

import android.content.Context;
import android.content.SharedPreferences;
import android.provider.Settings;
import android.util.Log;
import android.view.Surface;

/**
 * The panel is portrait-native but the tablet is used in landscape with the USB-C
 * port on the right (ROTATION_90), which is what ZUI started in. Seed that as the
 * locked rotation once, on first boot; after that the user's choice is left alone.
 */
public final class DefaultRotation {
    private static final String TAG = "TB371FCParts";
    private static final String KEY_DONE = "default_rotation_set";

    private DefaultRotation() {}

    public static void applyOnce(Context context) {
        SharedPreferences prefs = context.getSharedPreferences("parts", Context.MODE_PRIVATE);
        if (prefs.getBoolean(KEY_DONE, false)) {
            return;
        }
        Settings.System.putInt(context.getContentResolver(),
                Settings.System.USER_ROTATION, Surface.ROTATION_90);
        prefs.edit().putBoolean(KEY_DONE, true).apply();
        Log.i(TAG, "Default rotation set to landscape (port on the right)");
    }
}
