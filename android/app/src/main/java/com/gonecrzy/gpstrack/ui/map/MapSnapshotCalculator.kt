package com.gonecrzy.gpstrack.ui.map

import com.gonecrzy.gpstrack.data.model.LocationPoint
import java.time.Instant
import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt

object MapSnapshotCalculator {
    private const val MaximumDisplayAccuracyMeters = 50.0

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
        val filteredPoints = filterDisplayPoints(points)
        if (filteredPoints.size < 2) {
            return filteredPoints
        }

        if (filteredPoints.all { point ->
                distanceMeters(
                    filteredPoints.last().latitude,
                    filteredPoints.last().longitude,
                    point.latitude,
                    point.longitude,
                ) <= dwellRadiusMeters
            }
        ) {
            return listOf(filteredPoints.last())
        }

        val dwellStart = findDwellStart(filteredPoints, dwellRadiusMeters)
        val dwellStartIndex = if (dwellStart == null) {
            filteredPoints.lastIndex
        } else {
            filteredPoints.indexOfFirst { it.observedAt == dwellStart.toString() }.coerceAtLeast(0)
        }

        val preDwellPoints = filteredPoints.subList(0, dwellStartIndex + 1)
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

        val latestPoint = filteredPoints.last()
        if (simplified.lastOrNull()?.observedAt != latestPoint.observedAt) {
            simplified += latestPoint
        }

        return simplified
    }

    fun clampAutoZoom(
        proposedZoom: Double,
        maximumAutoZoom: Double,
    ): Double {
        return min(proposedZoom, maximumAutoZoom)
    }

    fun buildInitials(displayName: String): String {
        val words = displayName
            .trim()
            .split(Regex("\\s+"))
            .filter(String::isNotBlank)
        if (words.isEmpty()) {
            return "?"
        }
        return words
            .take(2)
            .mapNotNull { word -> word.firstOrNull()?.uppercaseChar() }
            .joinToString("")
    }

    private fun filterDisplayPoints(points: List<LocationPoint>): List<LocationPoint> {
        if (points.isEmpty()) {
            return emptyList()
        }

        val filtered = points.filterIndexed { index, point ->
            val accuracy = point.accuracyM
            index == 0 || index == points.lastIndex || accuracy == null || accuracy <= MaximumDisplayAccuracyMeters
        }

        return filtered.fold(mutableListOf<LocationPoint>()) { deduped, point ->
            val previous = deduped.lastOrNull()
            if (
                previous == null ||
                previous.latitude != point.latitude ||
                previous.longitude != point.longitude ||
                previous.observedAt != point.observedAt
            ) {
                deduped += point
            }
            deduped
        }
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
