package com.gonecrzy.gpstrack.ui.screens

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
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
import com.gonecrzy.gpstrack.data.model.LocationStop
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.gonecrzy.gpstrack.ui.map.MapSnapshotCalculator
import java.time.Duration
import java.time.Instant
import java.time.temporal.ChronoUnit
import org.maplibre.android.MapLibre
import org.maplibre.android.annotations.IconFactory
import org.maplibre.android.annotations.MarkerOptions
import org.maplibre.android.annotations.PolylineOptions
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView

private const val RouteWindowHours = 24L
private const val DwellRadiusMeters = 250.0
private const val MinimumDisplaySegmentMeters = 25.0
private const val MaximumAutoZoom = 12.0

@Composable
fun MapScreen(
    repository: GpsTrackRepository,
    preferences: AppPreferences,
    onMemberSelected: (String) -> Unit,
) {
    val context = LocalContext.current
    val members by repository.observeMembers().collectAsState(initial = emptyList())
    val mapStyleUrl by preferences.mapStyleUrl.collectAsState(
        initial = com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL,
    )
    var selectedMemberId by rememberSaveable { mutableStateOf<String?>(null) }
    val iconFactory = remember(context) {
        IconFactory.getInstance(context)
    }

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

    LaunchedEffect(members, selectedMemberId) {
        if (selectedMemberId != null && members.none { it.id == selectedMemberId }) {
            selectedMemberId = null
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
    val selectedStops by produceState(
        initialValue = emptyList<LocationStop>(),
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
            repository.loadMemberStops(activeMemberId, start.toString(), end.toString())
        }.getOrDefault(emptyList()).sortedBy { it.startedAt }
    }

    val selectedLatestLocation = selectedMemberId?.let(latestLocations::get)
    val dwellStart = remember(routePoints) {
        MapSnapshotCalculator.findDwellStart(routePoints, DwellRadiusMeters)
    }
    val displayRoutePoints = remember(routePoints) {
        MapSnapshotCalculator.buildDisplayRoute(
            points = routePoints,
            dwellRadiusMeters = DwellRadiusMeters,
            minimumSegmentMeters = MinimumDisplaySegmentMeters,
        )
    }
    val selectedMemberStates = members.map { member ->
        MapMemberState(member = member, latestLocation = latestLocations[member.id])
    }
    val currentStop = selectedStops.lastOrNull()

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
                            "Showing current family positions. Tap a family member to load their last $RouteWindowHours hours."
                        },
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    if (selectedMember != null && selectedLatestLocation != null) {
                        Text(
                            "Arrived ${formatRelativeDuration(dwellStart)}",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        currentStop?.let { stop ->
                            Text(
                                formatStopLabel(stop),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                        Text(
                            "Last update ${selectedLatestLocation.observedAt}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        TextButton(onClick = { selectedMemberId = null }) {
                            Text("Show Family Overview")
                        }
                    }
                }
            }
        }
        item {
            MapSurface(
                context = context,
                iconFactory = iconFactory,
                mapStyleUrl = mapStyleUrl,
                members = selectedMemberStates,
                selectedMemberId = selectedMemberId,
                routePoints = displayRoutePoints,
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
                            if (isSelected) {
                                val currentLabel = currentStop?.let(::formatStopLabel)
                                    ?: formatCoordinates(latest.latitude, latest.longitude)
                                "Current: $currentLabel · Arrived ${formatRelativeDuration(dwellStart)}"
                            } else {
                                "Current: ${formatCoordinates(latest.latitude, latest.longitude)} · Tap to load route"
                            }
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
        if (selectedMember != null && selectedStops.isNotEmpty()) {
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text("Recent Stops", style = MaterialTheme.typography.titleMedium)
                        selectedStops.asReversed().take(5).forEach { stop ->
                            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                Text(formatStopLabel(stop), style = MaterialTheme.typography.bodyLarge)
                                Text(
                                    "Stayed ${formatDurationSeconds(stop.durationSeconds)} · Arrived ${formatRelativeDuration(stop.startedAt)}",
                                    style = MaterialTheme.typography.bodySmall,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun MapSurface(
    context: Context,
    iconFactory: IconFactory,
    mapStyleUrl: String,
    members: List<MapMemberState>,
    selectedMemberId: String?,
    routePoints: List<LocationPoint>,
    onMarkerSelected: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val lifecycleOwner = LocalLifecycleOwner.current
    val mapView = remember {
        MapLibre.getInstance(context)
        MapView(context).apply {
            onCreate(Bundle())
        }
    }

    // Handle Map Style updates
    LaunchedEffect(mapStyleUrl) {
        mapView.getMapAsync { map ->
            map.setMinZoomPreference(0.0)
            if (map.style?.url != mapStyleUrl) {
                map.setStyle(mapStyleUrl)
            }
        }
    }

    DisposableEffect(lifecycleOwner, mapView) {
        mapView.getMapAsync { map ->
            map.setOnMarkerClickListener { marker ->
                marker.snippet?.let(onMarkerSelected)
                false
            }
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
                        context = context,
                        iconFactory = iconFactory,
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
    context: Context,
    iconFactory: IconFactory,
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
                .icon(
                    createMemberMarkerIcon(
                        context = context,
                        iconFactory = iconFactory,
                        displayName = state.member.displayName,
                        isSelected = state.member.id == selectedMemberId,
                        isChild = state.member.isChild,
                    ),
                )
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
                .target(LatLng(20.0, 0.0))
                .zoom(1.0)
                .build()
        }

        pointCount == 1 -> {
            val target = members.firstNotNullOfOrNull { state ->
                state.latestLocation?.let { LatLng(it.latitude, it.longitude) }
            } ?: routePoints.lastOrNull()?.let { LatLng(it.latitude, it.longitude) }
            if (target != null) {
                map.cameraPosition = CameraPosition.Builder()
                    .target(target)
                    .zoom(MaximumAutoZoom)
                    .build()
            }
        }

        else -> {
            runCatching {
                map.getCameraForLatLngBounds(
                    boundsBuilder.build(),
                    intArrayOf(128, 128, 128, 128),
                    0.0,
                    0.0,
                )?.let { cameraPosition ->
                    map.cameraPosition = CameraPosition.Builder(cameraPosition)
                        .zoom(MapSnapshotCalculator.clampAutoZoom(cameraPosition.zoom, MaximumAutoZoom))
                        .build()
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

private fun formatRelativeDuration(start: String): String {
    return runCatching { formatRelativeDuration(Instant.parse(start)) }.getOrDefault("just now")
}

private fun formatDurationSeconds(durationSeconds: Int): String {
    val duration = Duration.ofSeconds(durationSeconds.toLong())
    val hours = duration.toHours()
    val minutes = duration.minusHours(hours).toMinutes()

    return when {
        hours > 0 && minutes > 0 -> "${hours}h ${minutes}m"
        hours > 0 -> "${hours}h"
        minutes > 0 -> "${minutes}m"
        else -> "${durationSeconds}s"
    }
}

private fun formatStopLabel(stop: LocationStop): String {
    return stop.label ?: formatCoordinates(stop.latitude, stop.longitude)
}

private fun formatCoordinates(latitude: Double, longitude: Double): String {
    return "${"%.4f".format(latitude)}, ${"%.4f".format(longitude)}"
}

private fun createMemberMarkerIcon(
    context: Context,
    iconFactory: IconFactory,
    displayName: String,
    isSelected: Boolean,
    isChild: Boolean,
) = iconFactory.fromBitmap(
    Bitmap.createBitmap(96, 96, Bitmap.Config.ARGB_8888).apply {
        val canvas = Canvas(this)
        val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = when {
                isSelected -> Color.parseColor("#1794C8")
                isChild -> Color.parseColor("#D66B2D")
                else -> Color.parseColor("#2F6A9A")
            }
        }
        val outlinePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = Paint.Style.STROKE
            strokeWidth = context.resources.displayMetrics.density * 3f
        }
        val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textAlign = Paint.Align.CENTER
            textSize = context.resources.displayMetrics.density * 16f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        val centerX = width / 2f
        val centerY = height / 2f
        val radius = width * 0.32f
        canvas.drawCircle(centerX, centerY, radius, fillPaint)
        canvas.drawCircle(centerX, centerY, radius, outlinePaint)
        val baseline = centerY - (textPaint.descent() + textPaint.ascent()) / 2f
        canvas.drawText(MapSnapshotCalculator.buildInitials(displayName), centerX, baseline, textPaint)
    },
)

private data class MapMemberState(
    val member: MemberSummary,
    val latestLocation: LocationPoint?,
)
