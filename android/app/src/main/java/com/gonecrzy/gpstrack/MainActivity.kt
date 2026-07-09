package com.gonecrzy.gpstrack

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.gonecrzy.gpstrack.ui.GpsTrackApp
import com.gonecrzy.gpstrack.ui.theme.GpsTrackTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val container = (application as GpsTrackApplication).appContainer
        setContent {
            GpsTrackTheme {
                GpsTrackApp(container = container)
            }
        }
    }
}
