package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.AlertDialog
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gonecrzy.gpstrack.data.model.PlaceSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import kotlinx.coroutines.launch

@Composable
fun PlacesScreen(repository: GpsTrackRepository) {
    val places by repository.observePlaces().collectAsState(initial = emptyList())
    val scope = rememberCoroutineScope()
    var editingPlace by remember { mutableStateOf<PlaceSummary?>(null) }
    var showCreate by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        runCatching { repository.refreshPlaces() }
    }

    if (showCreate) {
        PlaceEditorDialog(
            title = "Add Place",
            initial = null,
            onDismiss = { showCreate = false },
            onSubmit = { name, type, lat, lon, radius, safe ->
                scope.launch {
                    repository.createPlace(name, type, lat, lon, radius, safe)
                }
                showCreate = false
            },
        )
    }
    editingPlace?.let { place ->
        PlaceEditorDialog(
            title = "Edit Place",
            initial = place,
            onDismiss = { editingPlace = null },
            onSubmit = { name, type, lat, lon, radius, safe ->
                scope.launch {
                    repository.updatePlace(place.id, name, type, lat, lon, radius, safe)
                }
                editingPlace = null
            },
        )
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Places", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        "Family places and safe zones are managed here. Safe-zone switching stays on the place itself.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Button(onClick = { showCreate = true }) {
                        Text("Add Place")
                    }
                }
            }
        }
        items(places, key = { it.id }) { place ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(place.name, style = MaterialTheme.typography.titleMedium)
                    Text("${place.latitude}, ${place.longitude}", style = MaterialTheme.typography.bodySmall)
                    Text("Radius ${place.radiusM.toInt()} m", style = MaterialTheme.typography.bodySmall)
                    Text(if (place.isSafeZone) "Safe zone enabled" else "Safe zone disabled")
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        TextButton(onClick = { editingPlace = place }) {
                            Text("Edit")
                        }
                        TextButton(
                            onClick = {
                                scope.launch {
                                    repository.deletePlace(place.id)
                                }
                            },
                        ) {
                            Text("Delete")
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PlaceEditorDialog(
    title: String,
    initial: PlaceSummary?,
    onDismiss: () -> Unit,
    onSubmit: (String, String?, Double, Double, Double, Boolean) -> Unit,
) {
    var name by remember(initial) { mutableStateOf(initial?.name ?: "") }
    var type by remember(initial) { mutableStateOf(initial?.placeType ?: "") }
    var latitude by remember(initial) { mutableStateOf(initial?.latitude?.toString() ?: "37.42") }
    var longitude by remember(initial) { mutableStateOf(initial?.longitude?.toString() ?: "-122.08") }
    var radius by remember(initial) { mutableStateOf(initial?.radiusM?.toString() ?: "150") }
    var isSafeZone by remember(initial) { mutableStateOf(initial?.isSafeZone ?: true) }

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            Button(
                onClick = {
                    onSubmit(
                        name.trim(),
                        type.trim().ifBlank { null },
                        latitude.toDoubleOrNull() ?: 37.42,
                        longitude.toDoubleOrNull() ?: -122.08,
                        radius.toDoubleOrNull() ?: 150.0,
                        isSafeZone,
                    )
                },
            ) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Name") })
                OutlinedTextField(value = type, onValueChange = { type = it }, label = { Text("Type") })
                OutlinedTextField(value = latitude, onValueChange = { latitude = it }, label = { Text("Latitude") })
                OutlinedTextField(value = longitude, onValueChange = { longitude = it }, label = { Text("Longitude") })
                OutlinedTextField(value = radius, onValueChange = { radius = it }, label = { Text("Radius (m)") })
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                    Text("Safe zone", modifier = Modifier.weight(1f))
                    Switch(checked = isSafeZone, onCheckedChange = { isSafeZone = it })
                }
            }
        },
    )
}
