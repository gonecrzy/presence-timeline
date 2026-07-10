package com.gonecrzy.gpstrack.ui.screens

import android.content.Context
import android.graphics.Color
import android.os.Bundle
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.gonecrzy.gpstrack.data.model.PlaceSearchCandidate
import com.gonecrzy.gpstrack.data.model.PlaceSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.components.AutoRefreshEffect
import com.gonecrzy.gpstrack.ui.map.buildRadiusRing
import com.gonecrzy.gpstrack.ui.map.ensureCircleLayer
import com.gonecrzy.gpstrack.ui.map.ensureLineLayer
import com.gonecrzy.gpstrack.ui.map.upsertGeoJsonSource
import kotlinx.coroutines.launch
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.style.expressions.Expression.eq
import org.maplibre.android.style.expressions.Expression.get
import org.maplibre.geojson.Feature
import org.maplibre.geojson.FeatureCollection
import org.maplibre.geojson.LineString
import org.maplibre.geojson.Point

private const val PlacePreviewSourceId = "gpstrack-place-preview"
private const val PlacePreviewRingLayerId = "gpstrack-place-preview-ring"
private const val PlacePreviewCenterLayerId = "gpstrack-place-preview-center"

@Composable
fun PlacesScreen(
    repository: GpsTrackRepository,
    contentPadding: PaddingValues = PaddingValues(),
) {
    val places by repository.observePlaces().collectAsState(initial = emptyList())
    val scope = rememberCoroutineScope()
    var editingPlace by remember { mutableStateOf<PlaceSummary?>(null) }
    var showCreate by remember { mutableStateOf(false) }
    var isRefreshing by remember { mutableStateOf(false) }

    fun refreshPlaces() {
        if (isRefreshing) {
            return
        }
        scope.launch {
            isRefreshing = true
            runCatching { repository.refreshPlaces() }
            isRefreshing = false
        }
    }

    LaunchedEffect(Unit) {
        refreshPlaces()
    }

    AutoRefreshEffect(onRefresh = { refreshPlaces() })

    if (showCreate) {
        PlaceEditorDialog(
            repository = repository,
            title = "Add Place",
            initial = null,
            onDismiss = { showCreate = false },
            onSubmit = { name, type, lat, lon, radius, safe ->
                scope.launch {
                    repository.createPlace(name, type, lat, lon, radius, safe)
                    refreshPlaces()
                }
                showCreate = false
            },
        )
    }
    editingPlace?.let { place ->
        PlaceEditorDialog(
            repository = repository,
            title = "Edit Place",
            initial = place,
            onDismiss = { editingPlace = null },
            onSubmit = { name, type, lat, lon, radius, safe ->
                scope.launch {
                    repository.updatePlace(place.id, name, type, lat, lon, radius, safe)
                    refreshPlaces()
                }
                editingPlace = null
            },
        )
    }

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
                    Text("Places", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        "Search an address, preview the radius, and save family places or safe zones here.",
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
                    Text("Center: ${"%.5f".format(place.latitude)}, ${"%.5f".format(place.longitude)}", style = MaterialTheme.typography.bodySmall)
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
    repository: GpsTrackRepository,
    title: String,
    initial: PlaceSummary?,
    onDismiss: () -> Unit,
    onSubmit: (String, String?, Double, Double, Double, Boolean) -> Unit,
) {
    val scope = rememberCoroutineScope()
    var name by remember(initial) { mutableStateOf(initial?.name ?: "") }
    var type by remember(initial) { mutableStateOf(initial?.placeType ?: "") }
    var addressQuery by remember(initial) { mutableStateOf("") }
    val searchResults = remember(initial) { mutableStateListOf<PlaceSearchCandidate>() }
    var isSearching by remember { mutableStateOf(false) }
    var latitude by remember(initial) { mutableStateOf(initial?.latitude?.toString() ?: "37.42") }
    var longitude by remember(initial) { mutableStateOf(initial?.longitude?.toString() ?: "-122.08") }
    var radius by remember(initial) { mutableStateOf(initial?.radiusM?.toString() ?: "150") }
    var isSafeZone by remember(initial) { mutableStateOf(initial?.isSafeZone ?: true) }

    val previewLatitude = latitude.toDoubleOrNull()
    val previewLongitude = longitude.toDoubleOrNull()
    val previewRadius = radius.toDoubleOrNull() ?: 150.0

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
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = addressQuery,
                        onValueChange = { addressQuery = it },
                        label = { Text("Search address") },
                        modifier = Modifier.weight(1f),
                    )
                    Button(
                        onClick = {
                            scope.launch {
                                isSearching = true
                                searchResults.clear()
                                searchResults.addAll(repository.searchPlaces(addressQuery.trim()))
                                isSearching = false
                            }
                        },
                        enabled = addressQuery.trim().length >= 2 && !isSearching,
                    ) {
                        Text(if (isSearching) "..." else "Find")
                    }
                }
                searchResults.take(3).forEach { candidate ->
                    TextButton(
                        onClick = {
                            latitude = candidate.latitude.toString()
                            longitude = candidate.longitude.toString()
                            addressQuery = candidate.label
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(candidate.label)
                    }
                }
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Name") },
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = type,
                    onValueChange = { type = it },
                    label = { Text("Type") },
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = latitude,
                    onValueChange = { latitude = it },
                    label = { Text("Latitude") },
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = longitude,
                    onValueChange = { longitude = it },
                    label = { Text("Longitude") },
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = radius,
                    onValueChange = { radius = it },
                    label = { Text("Radius (m)") },
                    modifier = Modifier.fillMaxWidth(),
                )
                if (previewLatitude != null && previewLongitude != null) {
                    Text("Preview", style = MaterialTheme.typography.titleSmall)
                    PlacePreviewMap(
                        latitude = previewLatitude,
                        longitude = previewLongitude,
                        radiusMeters = previewRadius,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(180.dp),
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                    Text("Safe zone", modifier = Modifier.weight(1f))
                    Switch(checked = isSafeZone, onCheckedChange = { isSafeZone = it })
                }
            }
        },
    )
}

@Composable
private fun PlacePreviewMap(
    latitude: Double,
    longitude: Double,
    radiusMeters: Double,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val mapView = remember {
        MapLibre.getInstance(context)
        MapView(context).apply {
            onCreate(Bundle())
        }
    }

    DisposableEffect(lifecycleOwner, mapView) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> mapView.onStart()
                Lifecycle.Event.ON_RESUME -> mapView.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView.onPause()
                Lifecycle.Event.ON_STOP -> mapView.onStop()
                Lifecycle.Event.ON_DESTROY -> mapView.onDestroy()
                else -> Unit
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    AndroidView(
        modifier = modifier,
        factory = { mapView },
        update = {
            it.getMapAsync { map ->
                if (map.style?.uri != com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL) {
                    map.setStyle(com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL) {
                        renderPlacePreview(map, latitude, longitude, radiusMeters)
                    }
                } else {
                    renderPlacePreview(map, latitude, longitude, radiusMeters)
                }
            }
        },
    )
}

private fun renderPlacePreview(
    map: MapLibreMap,
    latitude: Double,
    longitude: Double,
    radiusMeters: Double,
) {
    val style = map.style ?: return
    val center = LatLng(latitude, longitude)
    val ring = buildRadiusRing(latitude, longitude, radiusMeters)
    val previewFeatures = buildList {
        add(
            Feature.fromGeometry(Point.fromLngLat(longitude, latitude)).apply {
                addStringProperty("kind", "center")
            },
        )
        add(
            Feature.fromGeometry(
                LineString.fromLngLats(
                    ring.map { point -> Point.fromLngLat(point.longitude, point.latitude) },
                ),
            ).apply {
                addStringProperty("kind", "ring")
            },
        )
    }

    style.upsertGeoJsonSource(
        PlacePreviewSourceId,
        FeatureCollection.fromFeatures(previewFeatures),
    )
    style.ensureLineLayer(
        layerId = PlacePreviewRingLayerId,
        sourceId = PlacePreviewSourceId,
        color = Color.parseColor("#1794C8"),
        width = 4f,
        filter = eq(get("kind"), "ring"),
    )
    style.ensureCircleLayer(
        layerId = PlacePreviewCenterLayerId,
        sourceId = PlacePreviewSourceId,
        color = Color.parseColor("#1794C8"),
        radius = 6f,
        strokeColor = Color.WHITE,
        strokeWidth = 2f,
        filter = eq(get("kind"), "center"),
    )

    val boundsBuilder = LatLngBounds.Builder().include(center)
    ring.forEach(boundsBuilder::include)
    runCatching {
        map.getCameraForLatLngBounds(
            boundsBuilder.build(),
            intArrayOf(80, 80, 80, 80),
            0.0,
            0.0,
        )?.let { position ->
            map.cameraPosition = CameraPosition.Builder(position).build()
        }
    }
}
