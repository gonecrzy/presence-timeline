package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import kotlinx.coroutines.launch

@Composable
fun SettingsScreen(
    preferences: AppPreferences,
    contentPadding: PaddingValues = PaddingValues(),
) {
    val baseUrl by preferences.baseUrl.collectAsState(initial = com.gonecrzy.gpstrack.BuildConfig.DEFAULT_BASE_URL)
    val mapStyleUrl by preferences.mapStyleUrl.collectAsState(initial = com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL)
    val scope = rememberCoroutineScope()

    var baseUrlDraft by remember(baseUrl) { mutableStateOf(baseUrl) }
    var mapStyleDraft by remember(mapStyleUrl) { mutableStateOf(mapStyleUrl) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding(),
        contentPadding = PaddingValues(
            start = 16.dp,
            top = 12.dp,
            end = 16.dp,
            bottom = contentPadding.calculateBottomPadding() + 24.dp,
        ),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Settings", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        "Development mode is intentionally open. Change the backend base URL here when you move from LAN-only to a public domain later.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
        item {
            OutlinedTextField(
                value = baseUrlDraft,
                onValueChange = { baseUrlDraft = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Backend Base URL") },
            )
        }
        item {
            OutlinedTextField(
                value = mapStyleDraft,
                onValueChange = { mapStyleDraft = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Map Style URL") },
            )
        }
        item {
            Button(
                onClick = {
                    scope.launch {
                        preferences.updateBaseUrl(baseUrlDraft)
                        preferences.updateMapStyleUrl(mapStyleDraft)
                    }
                },
            ) {
                Text("Save Local Settings")
            }
        }
    }
}
