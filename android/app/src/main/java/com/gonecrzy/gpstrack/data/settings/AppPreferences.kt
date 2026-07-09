package com.gonecrzy.gpstrack.data.settings

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.gonecrzy.gpstrack.BuildConfig
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "gpstrack-settings")

class AppPreferences(private val context: Context) {
    val baseUrl: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[Keys.baseUrl] ?: BuildConfig.DEFAULT_BASE_URL
    }

    val mapStyleUrl: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[Keys.mapStyleUrl] ?: BuildConfig.DEFAULT_MAP_STYLE_URL
    }

    suspend fun updateBaseUrl(value: String) {
        context.dataStore.edit { preferences ->
            preferences[Keys.baseUrl] = value
        }
    }

    suspend fun updateMapStyleUrl(value: String) {
        context.dataStore.edit { preferences ->
            preferences[Keys.mapStyleUrl] = value
        }
    }

    private object Keys {
        val baseUrl = stringPreferencesKey("base_url")
        val mapStyleUrl = stringPreferencesKey("map_style_url")
    }
}
