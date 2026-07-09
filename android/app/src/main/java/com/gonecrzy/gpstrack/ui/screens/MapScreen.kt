package com.gonecrzy.gpstrack.ui.screens

import android.os.Bundle
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapView

@Composable
fun MapScreen(
    repository: GpsTrackRepository,
    preferences: AppPreferences,
    onMemberSelected: (String) -> Unit,
) {
    val members by repository.observeMembers().collectAsState(initial = emptyList())
    val mapStyleUrl by preferences.mapStyleUrl.collectAsState(initial = com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL)

    LaunchedEffect(Unit) {
        runCatching { repository.refreshMembers() }
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
                        "The scaffold uses a configurable MapLibre style URL. Markers and route overlays are the next Android pass.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
        item {
            MapSurface(
                mapStyleUrl = mapStyleUrl,
                members = members,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(320.dp),
            )
        }
        items(members, key = { it.id }) { member ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onMemberSelected(member.id) },
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(member.displayName, style = MaterialTheme.typography.titleMedium)
                    Text(member.lastSeenAt ?: "No recent location", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
}

@Composable
private fun MapSurface(
    mapStyleUrl: String,
    members: List<MemberSummary>,
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

    DisposableEffect(lifecycleOwner, mapView, mapStyleUrl, members) {
        mapView.getMapAsync { map ->
            map.setStyle(mapStyleUrl)
            map.cameraPosition = CameraPosition.Builder()
                .target(LatLng(37.42, -122.08))
                .zoom(10.0)
                .build()
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
                    map.setStyle(mapStyleUrl)
                    map.cameraPosition = CameraPosition.Builder()
                        .target(LatLng(37.42, -122.08))
                        .zoom(if (members.isEmpty()) 4.0 else 10.0)
                        .build()
                }
            },
        )
    }
}
