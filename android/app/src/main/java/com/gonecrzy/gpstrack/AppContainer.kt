package com.gonecrzy.gpstrack

import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences

data class AppContainer(
    val repository: GpsTrackRepository,
    val preferences: AppPreferences,
)
