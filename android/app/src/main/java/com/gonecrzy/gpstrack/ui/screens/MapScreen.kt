package com.gonecrzy.gpstrack.ui.screens

import android.graphics.Color
import android.os.Bundle
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.gonecrzy.gpstrack.ui.map.MapSnapshotCalculator
import java.time.Duration
import java.time.Instant
import java.time.temporal.ChronoUnit
import org.maplibre.android.MapLibre
import org.maplibre.android.annotations.MarkerOptions
import org.maplibre.android.annotations.PolylineOptions
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView

private const val RouteWindowHours = 24L
private const val DwellRadiusMeters = 250.0

@Composable
fun MapScreen(
    repository: GpsTrackRepository,
    preferences: AppPreferences,
    onMemberSelected: (String) -> Unit,
) {
    val members by repository.observeMembers().collectAsState(initial = emptyList())
    val mapStyleUrl by preferences.mapStyleUrl.collectAsState(
        initial = com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL,
    )
    var selectedMemberId by rememberSaveable { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { repository.refreshMembers() }
    }

    val latestLocations by produceState(
        initialValue = emptyMap<String, LocationPoint>(),
        key1 = members.map { it.id to it.lastSeenAt },
    ) {
        value = members.mapNotNull { member ->
            runCatching { repository.loadLatestLocation(member.id) }.getOrNull()?.let { member.id to it }
        }.toMap()
    }

    LaunchedEffect(members, latestLocations, selectedMemberId) {
        if (selectedMemberId == null || members.none { it.id == selectedMemberId }) {
            selectedMemberId = members.firstOrNull { latestLocations[it.id] != null }?.id ?: members.firstOrNull()?.id
        }
    }

    val selectedMember = members.firstOrNull { it.id == selectedMemberId }
    val routePoints by produceState(
        initialValue = emptyList<LocationPoint>(),
        key1 = selectedMemberId,
        key2 = selectedMember?.lastSeenAt,
    ) {
        val activeMemberId = selectedMemberId
        if (activeMemberId == null) {
            value = emptyList()
            return@produceState
        }

        val end = Instant.now()
        val start = end.minus(RouteWindowHours, ChronoUnit.HOURS)
        value = runCatching {
            repository.loadMemberHistory(activeMemberId, start.toString(), end.toString())
        }.getOrDefault(emptyList()).sortedBy { it.observedAt }
    }

    val selectedLatestLocation = selectedMemberId?.let(latestLocations::get)
    val dwellStart = remember(routePoints) {
        MapSnapshotCalculator.findDwellStart(routePoints, DwellRadiusMeters)
    }
    val selectedMemberStates = members.map { member ->
        MapMemberState(member = member, latestLocation = latestLocations[member.id])
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Live Map", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        if (selectedMember != null) {
                            "Showing ${selectedMember.displayName}'s last $RouteWindowHours hours with current family positions."
                        } else {
                            "Current family positions appear here when location history is available."
                        },
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    if (selectedMember != null && selectedLatestLocation != null) {
                        Text(
                            "Arrived ${formatRelativeDuration(dwellStart)}",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            "Last update ${selectedLatestLocation.observedAt}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
        }
        item {
            MapSurface(
                mapStyleUrl = mapStyleUrl,
                members = selectedMemberStates,
                selectedMemberId = selectedMemberId,
                routePoints = routePoints,
                onMarkerSelected = { selectedMemberId = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(360.dp),
            )
        }
        items(selectedMemberStates, key = { it.member.id }) { state ->
            val isSelected = state.member.id == selectedMemberId
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { selectedMemberId = state.member.id },
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(
                        text = buildString {
                            append(state.member.displayName)
                            if (isSelected) append(" · selected")
                        },
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(
                        state.latestLocation?.let { latest ->
                            val arrived = if (isSelected) formatRelativeDuration(dwellStart) else "Tap to load route"
                            "Current: ${formatCoordinates(latest.latitude, latest.longitude)} · Arrived $arrived"
                        } ?: "No current location available",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { selectedMemberId = state.member.id }) {
                            Text(if (isSelected) "Viewing Route" else "View Route")
                        }
                        TextButton(onClick = { onMemberSelected(state.member.id) }) {
                            Text("Open Details")
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MapSurface(
    mapStyleUrl: String,
    members: List<MapMemberState>,
    selectedMemberId: String?,
    routePoints: List<LocationPoint>,
    onMarkerSelected: (String) -> Unit,
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

    DisposableEffect(lifecycleOwner, mapView, mapStyleUrl, onMarkerSelected) {
        mapView.getMapAsync { map ->
            map.setOnMarkerClickListener { marker ->
                marker.snippet?.let(onMarkerSelected)
                false
            }
            map.setStyle(mapStyleUrl)
        }

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

    Box(modifier = modifier) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { mapView },
            update = {
                it.getMapAsync { map ->
                    renderMap(
                        map = map,
                        members = members,
                        selectedMemberId = selectedMemberId,
                        routePoints = routePoints,
                    )
                }
            },
        )
    }
}

private fun renderMap(
    map: MapLibreMap,
    members: List<MapMemberState>,
    selectedMemberId: String?,
    routePoints: List<LocationPoint>,
) {
    map.clear()

    val boundsBuilder = LatLngBounds.Builder()
    var pointCount = 0

    members.forEach { state ->
        val latest = state.latestLocation ?: return@forEach
        val position = LatLng(latest.latitude, latest.longitude)
        map.addMarker(
            MarkerOptions()
                .position(position)
                .title(
                    buildString {
                        append(state.member.displayName)
                        if (state.member.id == selectedMemberId) append(" · active")
                    },
                )
                .snippet(state.member.id),
        )
        boundsBuilder.include(position)
        pointCount += 1
    }

    if (routePoints.size >= 2) {
        val path = routePoints.map { LatLng(it.latitude, it.longitude) }
        map.addPolyline(
            PolylineOptions()
                .addAll(path)
                .color(Color.parseColor("#58C4DD"))
                .width(5f),
        )
        path.forEach(boundsBuilder::include)
        pointCount += path.size
    }

    when {
        pointCount == 0 -> {
            map.cameraPosition = CameraPosition.Builder()
                .target(LatLng(37.42, -122.08))
                .zoom(4.0)
                .build()
        }

        pointCount == 1 -> {
            val target = members.firstNotNullOfOrNull { state ->
                state.latestLocation?.let { LatLng(it.latitude, it.longitude) }
            } ?: routePoints.lastOrNull()?.let { LatLng(it.latitude, it.longitude) }
            if (target != null) {
                map.cameraPosition = CameraPosition.Builder()
                    .target(target)
                    .zoom(14.0)
                    .build()
            }
        }

        else -> {
            runCatching {
                map.getCameraForLatLngBounds(
                    boundsBuilder.build(),
                    intArrayOf(96, 96, 96, 96),
                    0.0,
                    0.0,
                )?.let { cameraPosition ->
                    map.cameraPosition = cameraPosition
                }
            }
        }
    }
}

private fun formatRelativeDuration(start: Instant?): String {
    if (start == null) {
        return "just now"
    }

    val duration = Duration.between(start, Instant.now()).coerceAtLeast(Duration.ZERO)
    val hours = duration.toHours()
    val minutes = duration.minusHours(hours).toMinutes()

    return when {
        hours > 0 && minutes > 0 -> "${hours}h ${minutes}m ago"
        hours > 0 -> "${hours}h ago"
        minutes > 0 -> "${minutes}m ago"
        else -> "just now"
    }
}

private fun formatCoordinates(latitude: Double, longitude: Double): String {
    return "${"%.4f".format(latitude)}, ${"%.4f".format(longitude)}"
}

private data class MapMemberState(
    val member: MemberSummary,
    val latestLocation: LocationPoint?,
)
