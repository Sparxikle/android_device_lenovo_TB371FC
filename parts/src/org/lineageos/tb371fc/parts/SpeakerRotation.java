/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.tb371fc.parts;

import android.content.Context;
import android.hardware.display.DisplayManager;
import android.media.AudioManager;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;

/**
 * Tells the stock audio HAL how the tablet is rotated, the way ZUI did. The HAL turns
 * "gsensor_rotation=<deg>" into TFA9894_CHAN_SELECTOR, which picks which corner amps
 * play the left and which the right channel, so stereo follows the screen.
 */
public class SpeakerRotation implements DisplayManager.DisplayListener {
    private static final String TAG = "TB371FCParts";

    private final AudioManager mAudioManager;
    private final DisplayManager mDisplayManager;
    private int mLastRotation = -1;

    public SpeakerRotation(Context context) {
        mAudioManager = context.getSystemService(AudioManager.class);
        mDisplayManager = context.getSystemService(DisplayManager.class);
    }

    public void start() {
        mDisplayManager.registerDisplayListener(this, new Handler(Looper.getMainLooper()));
        update();
    }

    @Override
    public void onDisplayAdded(int displayId) {}

    @Override
    public void onDisplayRemoved(int displayId) {}

    @Override
    public void onDisplayChanged(int displayId) {
        if (displayId == Display.DEFAULT_DISPLAY) {
            update();
        }
    }

    private void update() {
        Display display = mDisplayManager.getDisplay(Display.DEFAULT_DISPLAY);
        if (display == null) {
            return;
        }
        int degrees = display.getRotation() * 90;
        if (degrees == mLastRotation) {
            return;
        }
        mLastRotation = degrees;
        mAudioManager.setParameters("gsensor_rotation=" + degrees);
        Log.d(TAG, "gsensor_rotation=" + degrees);
    }
}
