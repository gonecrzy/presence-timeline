package com.gonecrzy.gpstrack.ui.map

import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import org.maplibre.android.geometry.LatLng

fun buildRadiusRing(
    latitude: Double,
    longitude: Double,
    radiusMeters: Double,
    steps: Int = 36,
): List<LatLng> {
    val earthRadiusMeters = 6_371_000.0
    val latitudeRadians = Math.toRadians(latitude)
    return (0..steps).map { step ->
        val angle = 2 * PI * step / steps
        val latitudeOffset = (radiusMeters / earthRadiusMeters) * (180 / PI) * sin(angle)
        val longitudeOffset = (radiusMeters / earthRadiusMeters) * (180 / PI) * cos(angle) / cos(latitudeRadians)
        LatLng(latitude + latitudeOffset, longitude + longitudeOffset)
    }
}
