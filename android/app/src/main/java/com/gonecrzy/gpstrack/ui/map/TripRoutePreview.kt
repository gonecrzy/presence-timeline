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
import com.gonecrzy.gpstrack.ui.map.ensureLineLayer
import com.gonecrzy.gpstrack.ui.map.upsertGeoJsonSource
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.geojson.Feature
import org.maplibre.geojson.FeatureCollection
import org.maplibre.geojson.LineString
import org.maplibre.geojson.Point

private const val TripPreviewSourceId = "gpstrack-trip-preview"
private const val TripPreviewLayerId = "gpstrack-trip-preview-layer"

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
                if (map.style?.uri != BuildConfig.DEFAULT_MAP_STYLE_URL) {
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
    val style = map.style ?: return
    if (route.points.isEmpty()) {
        style.upsertGeoJsonSource(
            TripPreviewSourceId,
            FeatureCollection.fromFeatures(emptyList()),
        )
        style.ensureLineLayer(
            layerId = TripPreviewLayerId,
            sourceId = TripPreviewSourceId,
            color = Color.parseColor("#58C4DD"),
            width = context.resources.displayMetrics.density * 3f,
        )
        map.cameraPosition = CameraPosition.Builder()
            .target(LatLng(20.0, 0.0))
            .zoom(1.0)
            .build()
        return
    }

    val path = route.points.map { LatLng(it.latitude, it.longitude) }
    val linePoints = route.points.map { Point.fromLngLat(it.longitude, it.latitude) }
    val boundsBuilder = LatLngBounds.Builder()
    path.forEach(boundsBuilder::include)

    style.upsertGeoJsonSource(
        TripPreviewSourceId,
        FeatureCollection.fromFeature(
            Feature.fromGeometry(LineString.fromLngLats(linePoints)),
        ),
    )
    style.ensureLineLayer(
        layerId = TripPreviewLayerId,
        sourceId = TripPreviewSourceId,
        color = Color.parseColor("#58C4DD"),
        width = context.resources.displayMetrics.density * 3f,
    )

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
