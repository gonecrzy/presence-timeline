package com.gonecrzy.gpstrack.ui.map

import android.graphics.Color
import android.graphics.PointF
import android.os.Bundle
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import com.gonecrzy.gpstrack.ui.model.HistoryMapMarkerUiModel
import com.gonecrzy.gpstrack.ui.model.HistoryMapUiModel
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.style.expressions.Expression.all
import org.maplibre.android.style.expressions.Expression.any
import org.maplibre.android.style.expressions.Expression.eq
import org.maplibre.android.style.expressions.Expression.get
import org.maplibre.android.style.expressions.Expression.literal
import org.maplibre.geojson.Feature
import org.maplibre.geojson.FeatureCollection
import org.maplibre.geojson.LineString
import org.maplibre.geojson.Point

private const val HistoryRouteSourceId = "gpstrack-history-route"
private const val HistoryRouteLayerId = "gpstrack-history-route-layer"
private const val HistoryMarkerSourceId = "gpstrack-history-markers"
private const val HistoryEndpointMarkerLayerId = "gpstrack-history-markers-endpoints-layer"
private const val HistoryWaypointMarkerLayerId = "gpstrack-history-markers-waypoints-layer"
private const val HistorySelectedMarkerLayerId = "gpstrack-history-markers-selected-layer"

@Composable
fun HistoryRouteMap(
    mapStyleUrl: String,
    model: HistoryMapUiModel,
    onMarkerSelected: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val currentOnMarkerSelected = rememberUpdatedState(onMarkerSelected)
    val mapView = remember {
        MapLibre.getInstance(context)
        MapView(context).apply { onCreate(Bundle()) }
    }

    DisposableEffect(lifecycleOwner, mapView) {
        var mapReference: MapLibreMap? = null
        val clickListener = MapLibreMap.OnMapClickListener { latLng ->
            val map = mapReference ?: return@OnMapClickListener false
            val screenPoint = map.projection.toScreenLocation(latLng)
            val selectedId = map.queryRenderedFeatures(
                PointF(screenPoint.x, screenPoint.y),
                HistorySelectedMarkerLayerId,
                HistoryWaypointMarkerLayerId,
                HistoryEndpointMarkerLayerId,
            ).firstOrNull { it.hasNonNullValueForProperty("itemId") }
                ?.getStringProperty("itemId")
            if (selectedId != null) {
                currentOnMarkerSelected.value(selectedId)
                true
            } else {
                false
            }
        }

        mapView.getMapAsync { map ->
            mapReference = map
            map.addOnMapClickListener(clickListener)
        }

        val observer = bindMapViewLifecycle(lifecycleOwner.lifecycle, mapView)
        onDispose {
            mapReference?.removeOnMapClickListener(clickListener)
            unbindMapViewLifecycle(lifecycleOwner.lifecycle, observer, mapView)
        }
    }

    AndroidView(
        modifier = modifier,
        factory = { mapView },
        update = { view ->
            view.getMapAsync { map ->
                map.uiSettings.isCompassEnabled = false
                if (map.style?.uri != mapStyleUrl) {
                    map.setStyle(mapStyleUrl) {
                        renderHistoryRouteMap(map, model)
                    }
                } else {
                    renderHistoryRouteMap(map, model)
                }
            }
        },
    )
}

private fun renderHistoryRouteMap(
    map: MapLibreMap,
    model: HistoryMapUiModel,
) {
    val style = map.style ?: return

    val routeFeatureCollection = if (model.routePoints.size >= 2) {
        FeatureCollection.fromFeature(
            Feature.fromGeometry(
                LineString.fromLngLats(
                    model.routePoints.map { point -> Point.fromLngLat(point.longitude, point.latitude) },
                ),
            ),
        )
    } else {
        FeatureCollection.fromFeatures(emptyList())
    }
    style.upsertGeoJsonSource(HistoryRouteSourceId, routeFeatureCollection)
    style.ensureLineLayer(
        layerId = HistoryRouteLayerId,
        sourceId = HistoryRouteSourceId,
        color = Color.parseColor("#58B8FF"),
        width = 4f,
    )

    val markerFeatures = model.markers.map { marker ->
        Feature.fromGeometry(Point.fromLngLat(marker.longitude, marker.latitude)).apply {
            addStringProperty("itemId", marker.id)
            addBooleanProperty("selected", marker.isSelected)
            addStringProperty("label", marker.label.take(1))
            addStringProperty("kind", marker.kind.name)
        }
    }
    style.upsertGeoJsonSource(
        HistoryMarkerSourceId,
        FeatureCollection.fromFeatures(markerFeatures),
    )
    style.ensureCircleLayer(
        layerId = HistoryEndpointMarkerLayerId,
        sourceId = HistoryMarkerSourceId,
        color = Color.parseColor("#17324A"),
        radius = 6.5f,
        strokeColor = Color.WHITE,
        strokeWidth = 2f,
        filter = all(
            eq(get("selected"), literal(false)),
            any(
                eq(get("kind"), literal("START")),
                eq(get("kind"), literal("END")),
            ),
        ),
    )
    style.ensureCircleLayer(
        layerId = HistoryWaypointMarkerLayerId,
        sourceId = HistoryMarkerSourceId,
        color = Color.parseColor("#F5B342"),
        radius = 5.5f,
        strokeColor = Color.WHITE,
        strokeWidth = 2f,
        belowLayerId = HistorySelectedMarkerLayerId,
        filter = all(
            eq(get("selected"), literal(false)),
            any(
                eq(get("kind"), literal("STOP")),
                eq(get("kind"), literal("SUMMARY")),
            ),
        ),
    )
    style.ensureCircleLayer(
        layerId = HistorySelectedMarkerLayerId,
        sourceId = HistoryMarkerSourceId,
        color = Color.parseColor("#58B8FF"),
        radius = 8f,
        strokeColor = Color.WHITE,
        strokeWidth = 2f,
        filter = eq(get("selected"), literal(true)),
    )

    val boundsBuilder = LatLngBounds.Builder()
    var pointCount = 0
    model.routePoints.forEach { point ->
        boundsBuilder.include(LatLng(point.latitude, point.longitude))
        pointCount += 1
    }
    model.markers.forEach { marker: HistoryMapMarkerUiModel ->
        boundsBuilder.include(LatLng(marker.latitude, marker.longitude))
        pointCount += 1
    }

    when {
        pointCount == 0 -> {
            map.cameraPosition = CameraPosition.Builder()
                .target(LatLng(20.0, 0.0))
                .zoom(1.2)
                .build()
        }

        pointCount == 1 -> {
            val point = model.markers.firstOrNull()?.let { LatLng(it.latitude, it.longitude) }
                ?: model.routePoints.firstOrNull()?.let { LatLng(it.latitude, it.longitude) }
            if (point != null) {
                map.cameraPosition = CameraPosition.Builder()
                    .target(point)
                    .zoom(13.0)
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
                )?.let { map.cameraPosition = it }
            }
        }
    }
}
