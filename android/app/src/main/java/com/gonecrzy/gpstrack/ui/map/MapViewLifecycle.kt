package com.gonecrzy.gpstrack.ui.map

import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import org.maplibre.android.maps.MapView

fun bindMapViewLifecycle(
    lifecycle: Lifecycle,
    mapView: MapView,
): LifecycleEventObserver {
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

    lifecycle.addObserver(observer)
    when {
        lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED) -> {
            mapView.onStart()
            mapView.onResume()
        }

        lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED) -> {
            mapView.onStart()
        }

        lifecycle.currentState == Lifecycle.State.DESTROYED -> {
            mapView.onDestroy()
        }

        else -> Unit
    }
    return observer
}

fun unbindMapViewLifecycle(
    lifecycle: Lifecycle,
    observer: LifecycleEventObserver,
    mapView: MapView,
) {
    lifecycle.removeObserver(observer)
    mapView.onPause()
    mapView.onStop()
    mapView.onDestroy()
}
