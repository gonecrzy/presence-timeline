package com.gonecrzy.gpstrack.ui.map

import com.gonecrzy.gpstrack.data.model.LocationPoint
import java.time.Instant
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

object MapSnapshotCalculator {
    fun findDwellStart(
        points: List<LocationPoint>,
        radiusMeters: Double,
    ): Instant? {
        val latestPoint = points.lastOrNull() ?: return null
        val latestInstant = Instant.parse(latestPoint.observedAt)
        var dwellStart = latestInstant

        for (index in points.lastIndex - 1 downTo 0) {
            val candidate = points[index]
            if (distanceMeters(
                    latestPoint.latitude,
                    latestPoint.longitude,
                    candidate.latitude,
                    candidate.longitude,
                ) > radiusMeters
            ) {
                break
            }
            dwellStart = Instant.parse(candidate.observedAt)
        }

        return dwellStart
    }

    fun buildDisplayRoute(
        points: List<LocationPoint>,
        dwellRadiusMeters: Double,
        minimumSegmentMeters: Double,
    ): List<LocationPoint> {
        if (points.size < 2) {
            return points
        }

        val dwellStart = findDwellStart(points, dwellRadiusMeters)
        val dwellStartIndex = if (dwellStart == null) {
            points.lastIndex
        } else {
            points.indexOfFirst { it.observedAt == dwellStart.toString() }.coerceAtLeast(0)
        }

        val preDwellPoints = points.subList(0, dwellStartIndex + 1)
        val simplified = mutableListOf<LocationPoint>()

        preDwellPoints.forEach { point ->
            val lastKept = simplified.lastOrNull()
            if (lastKept == null || distanceMeters(
                    lastKept.latitude,
                    lastKept.longitude,
                    point.latitude,
                    point.longitude,
                ) >= minimumSegmentMeters
            ) {
                simplified += point
            } else {
                simplified[simplified.lastIndex] = point
            }
        }

        val latestPoint = points.last()
        if (simplified.lastOrNull()?.observedAt != latestPoint.observedAt) {
            simplified += latestPoint
        }

        return simplified
    }

    private fun distanceMeters(
        startLatitude: Double,
        startLongitude: Double,
        endLatitude: Double,
        endLongitude: Double,
    ): Double {
        val earthRadiusMeters = 6_371_000.0
        val latitudeDelta = Math.toRadians(endLatitude - startLatitude)
        val longitudeDelta = Math.toRadians(endLongitude - startLongitude)
        val startLatitudeRadians = Math.toRadians(startLatitude)
        val endLatitudeRadians = Math.toRadians(endLatitude)

        val haversine = sin(latitudeDelta / 2).pow(2) +
            cos(startLatitudeRadians) * cos(endLatitudeRadians) * sin(longitudeDelta / 2).pow(2)
        val angularDistance = 2 * asin(sqrt(haversine))
        return earthRadiusMeters * angularDistance
    }
}
