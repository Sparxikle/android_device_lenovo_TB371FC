/*
 * Copyright (C) 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.tb371fc.parts;

import android.app.Application;

public class PartsApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        DefaultRotation.applyOnce(this);
        new SpeakerRotation(this).start();
    }
}
