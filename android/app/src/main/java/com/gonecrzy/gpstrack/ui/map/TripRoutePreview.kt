package com.gonecrzy.gpstrack.ui.map

import android.content.Context
import android.graphics.Color
import android.os.Bundle
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.gonecrzy.gpstrack.BuildConfig
import com.gonecrzy.gpstrack.data.model.TripRoute
import org.maplibre.android.MapLibre
import org.maplibre.android.annotations.MarkerOptions
import org.maplibre.android.annotations.PolylineOptions
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView

@Composable
fun TripRoutePreview(
    route: TripRoute,
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
                if (map.style?.url != BuildConfig.DEFAULT_MAP_STYLE_URL) {
                    map.setStyle(BuildConfig.DEFAULT_MAP_STYLE_URL) {
                        renderTripRoutePreview(context, map, route)
                    }
                } else {
                    renderTripRoutePreview(context, map, route)
                }
            }
        },
    )
}

private fun renderTripRoutePreview(
    context: Context,
    map: MapLibreMap,
    route: TripRoute,
) {
    map.clear()
    if (route.points.isEmpty()) {
        map.cameraPosition = CameraPosition.Builder()
            .target(LatLng(20.0, 0.0))
            .zoom(1.0)
            .build()
        return
    }

    val path = route.points.map { LatLng(it.latitude, it.longitude) }
    val boundsBuilder = LatLngBounds.Builder()
    path.forEach(boundsBuilder::include)

    map.addPolyline(
        PolylineOptions()
            .addAll(path)
            .color(Color.parseColor("#58C4DD"))
            .width(context.resources.displayMetrics.density * 3f),
    )
    map.addMarker(MarkerOptions().position(path.first()).title("Start"))
    if (path.size > 1) {
        map.addMarker(MarkerOptions().position(path.last()).title("End"))
    }

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
