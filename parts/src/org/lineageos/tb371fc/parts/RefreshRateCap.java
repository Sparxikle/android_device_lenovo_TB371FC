/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.tb371fc.parts;

import android.content.ContentResolver;
import android.content.Context;
import android.database.ContentObserver;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.Log;

/**
 * The Novatek touch controller only reports stylus contact at <= 120 Hz (hover still
 * works at 144 Hz), so the pen stops writing whenever the panel runs at 144 Hz.
 * config_defaultPeakRefreshRate only sets the initial value; "Smooth display" and
 * apps writing the setting raise the peak to the panel maximum. Clamp both the peak
 * and the minimum refresh-rate settings to 120 Hz whenever anything changes them.
 * DisplayModeDirector applies the user peak as a cap above app frame-rate requests.
 */
public final class RefreshRateCap extends ContentObserver {
    private static final String TAG = "TB371FCParts";
    private static final float MAX_HZ = 120f;
    private static final String[] KEYS = {
            Settings.System.PEAK_REFRESH_RATE,
            Settings.System.MIN_REFRESH_RATE,
    };

    private final ContentResolver mResolver;

    public RefreshRateCap(Context context) {
        super(new Handler(Looper.getMainLooper()));
        mResolver = context.getContentResolver();
    }

    public void start() {
        for (String key : KEYS) {
            mResolver.registerContentObserver(Settings.System.getUriFor(key), false, this);
        }
        clampAll();
    }

    @Override
    public void onChange(boolean selfChange, Uri uri) {
        clampAll();
    }

    private void clampAll() {
        for (String key : KEYS) {
            // Unset means "use the config default", which is already 120 for the peak.
            float value = Settings.System.getFloat(mResolver, key, 0f);
            if (value > MAX_HZ) {
                Settings.System.putFloat(mResolver, key, MAX_HZ);
                Log.i(TAG, key + "=" + value + " capped to " + MAX_HZ);
            }
        }
    }
}
