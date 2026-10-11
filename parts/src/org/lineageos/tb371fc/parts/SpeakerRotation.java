/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.tb371fc.parts;

import android.content.Context;
import android.hardware.display.DisplayManager;
import android.media.AudioManager;
import android.media.AudioPlaybackConfiguration;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.Display;

import java.util.List;

/**
 * Tells the stock audio HAL how the tablet is rotated, the way ZUI did. The HAL turns
 * "gsensor_rotation=<deg>" into TFA9894_CHAN_SELECTOR, which picks the edge pair that
 * gets L/R from TDM slots 0/1, so stereo follows the screen.
 *
 * The HAL stores the rotation but only applies it to speaker playback usecases that are
 * active when the parameter arrives, and never re-applies it on stream start. So the
 * rotation is re-sent whenever playback starts, not just when the display rotates.
 *
 * The HAL's angles assume landscape (USB-C on the right) is 0 degrees, while this
 * panel is portrait-native and that pose is ROTATION_90 here, so shift by 90.
 * Measured: selector 0 = port right, 1 = port down, 2 = port left, 3 = port up,
 * each putting FL/FR on the top pair and BL/BR on the bottom pair.
 */
public class SpeakerRotation implements DisplayManager.DisplayListener {
    private static final String TAG = "TB371FCParts";
    // The HAL usecase can come up a little after the player reports started.
    private static final long RESEND_DELAY_MS = 250;

    private final AudioManager mAudioManager;
    private final DisplayManager mDisplayManager;
    private final Handler mHandler = new Handler(Looper.getMainLooper());
    private int mLastRotation = -1;

    private final Runnable mResend = () -> push(true);

    private final AudioManager.AudioPlaybackCallback mPlaybackCallback =
            new AudioManager.AudioPlaybackCallback() {
        @Override
        public void onPlaybackConfigChanged(List<AudioPlaybackConfiguration> configs) {
            push(true);
            mHandler.removeCallbacks(mResend);
            mHandler.postDelayed(mResend, RESEND_DELAY_MS);
        }
    };

    public SpeakerRotation(Context context) {
        mAudioManager = context.getSystemService(AudioManager.class);
        mDisplayManager = context.getSystemService(DisplayManager.class);
    }

    public void start() {
        mDisplayManager.registerDisplayListener(this, mHandler);
        mAudioManager.registerAudioPlaybackCallback(mPlaybackCallback, mHandler);
        push(true);
    }

    @Override
    public void onDisplayAdded(int displayId) {}

    @Override
    public void onDisplayRemoved(int displayId) {}

    @Override
    public void onDisplayChanged(int displayId) {
        if (displayId == Display.DEFAULT_DISPLAY) {
            push(false);
        }
    }

    private void push(boolean force) {
        Display display = mDisplayManager.getDisplay(Display.DEFAULT_DISPLAY);
        if (display == null) {
            return;
        }
        int degrees = (display.getRotation() * 90 + 270) % 360;
        if (!force && degrees == mLastRotation) {
            return;
        }
        mLastRotation = degrees;
        mAudioManager.setParameters("gsensor_rotation=" + degrees);
        Log.d(TAG, "gsensor_rotation=" + degrees);
    }
}
