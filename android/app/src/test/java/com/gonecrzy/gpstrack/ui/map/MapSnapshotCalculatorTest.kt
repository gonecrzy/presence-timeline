package com.gonecrzy.gpstrack.ui.map

import com.gonecrzy.gpstrack.data.model.LocationPoint
import java.time.Instant
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MapSnapshotCalculatorTest {
    @Test
    fun `dwell start stays at earliest trailing point within threshold`() {
        val points = listOf(
            point("2026-07-09T08:00:00Z", 37.4000, -122.0800),
            point("2026-07-09T08:20:00Z", 37.4210, -122.0840),
            point("2026-07-09T08:40:00Z", 37.4212, -122.0842),
            point("2026-07-09T09:00:00Z", 37.4211, -122.0841),
        )

        val dwellStart = MapSnapshotCalculator.findDwellStart(points, radiusMeters = 250.0)

        assertEquals(Instant.parse("2026-07-09T08:20:00Z"), dwellStart)
    }

    @Test
    fun `dwell start is latest point when previous point is outside threshold`() {
        val points = listOf(
            point("2026-07-09T08:00:00Z", 37.4100, -122.0900),
            point("2026-07-09T09:00:00Z", 37.4211, -122.0841),
        )

        val dwellStart = MapSnapshotCalculator.findDwellStart(points, radiusMeters = 250.0)

        assertEquals(Instant.parse("2026-07-09T09:00:00Z"), dwellStart)
    }

    @Test
    fun `dwell start is null without any points`() {
        assertNull(MapSnapshotCalculator.findDwellStart(emptyList(), radiusMeters = 250.0))
    }

    @Test
    fun `display route collapses current dwell cluster`() {
        val points = listOf(
            point("2026-07-09T08:00:00Z", 37.4000, -122.0800),
            point("2026-07-09T08:20:00Z", 37.4210, -122.0840),
            point("2026-07-09T08:40:00Z", 37.4212, -122.0842),
            point("2026-07-09T09:00:00Z", 37.4211, -122.0841),
        )

        val displayRoute = MapSnapshotCalculator.buildDisplayRoute(
            points = points,
            dwellRadiusMeters = 250.0,
            minimumSegmentMeters = 25.0,
        )

        assertEquals(
            listOf(
                "2026-07-09T08:00:00Z",
                "2026-07-09T08:20:00Z",
                "2026-07-09T09:00:00Z",
            ),
            displayRoute.map(LocationPoint::observedAt),
        )
    }

    @Test
    fun `display route keeps meaningful movement points`() {
        val points = listOf(
            point("2026-07-09T08:00:00Z", 37.4000, -122.0800),
            point("2026-07-09T08:05:00Z", 37.4000, -122.0795),
            point("2026-07-09T08:10:00Z", 37.4010, -122.0810),
            point("2026-07-09T08:15:00Z", 37.4020, -122.0820),
        )

        val displayRoute = MapSnapshotCalculator.buildDisplayRoute(
            points = points,
            dwellRadiusMeters = 250.0,
            minimumSegmentMeters = 25.0,
        )

        assertEquals(points.map(LocationPoint::observedAt), displayRoute.map(LocationPoint::observedAt))
    }

    @Test
    fun `display route collapses all-day dwell jitter to the current point`() {
        val points = listOf(
            point("2026-07-09T08:00:00Z", 33.03113, -80.13135, accuracyM = 11.0),
            point("2026-07-09T08:30:00Z", 33.03117, -80.13131, accuracyM = 26.0),
            point("2026-07-09T09:00:00Z", 33.03107, -80.13138, accuracyM = 17.0),
            point("2026-07-09T09:30:00Z", 33.03114, -80.13134, accuracyM = 12.0),
        )

        val displayRoute = MapSnapshotCalculator.buildDisplayRoute(
            points = points,
            dwellRadiusMeters = 250.0,
            minimumSegmentMeters = 25.0,
        )

        assertEquals(listOf("2026-07-09T09:30:00Z"), displayRoute.map(LocationPoint::observedAt))
    }

    @Test
    fun `display route drops poor accuracy outliers before simplifying`() {
        val points = listOf(
            point("2026-07-09T08:00:00Z", 37.4000, -122.0800, accuracyM = 12.0),
            point("2026-07-09T08:15:00Z", 37.4010, -122.0810, accuracyM = 98.0),
            point("2026-07-09T08:30:00Z", 37.4020, -122.0820, accuracyM = 13.0),
        )

        val displayRoute = MapSnapshotCalculator.buildDisplayRoute(
            points = points,
            dwellRadiusMeters = 250.0,
            minimumSegmentMeters = 25.0,
        )

        assertEquals(
            listOf("2026-07-09T08:00:00Z", "2026-07-09T08:30:00Z"),
            displayRoute.map(LocationPoint::observedAt),
        )
    }

    @Test
    fun `auto zoom is capped for tight bounds`() {
        val zoom = MapSnapshotCalculator.clampAutoZoom(proposedZoom = 16.2, maximumAutoZoom = 13.0)

        assertEquals(13.0, zoom, 0.0)
    }

    @Test
    fun `auto zoom keeps wider fit when already zoomed out`() {
        val zoom = MapSnapshotCalculator.clampAutoZoom(proposedZoom = 10.4, maximumAutoZoom = 13.0)

        assertEquals(10.4, zoom, 0.0)
    }

    @Test
    fun `initials use the first letter of up to two words`() {
        val initials = MapSnapshotCalculator.buildInitials("Kristi Parker")

        assertEquals("KP", initials)
    }

    @Test
    fun `initials fall back to single word names`() {
        val initials = MapSnapshotCalculator.buildInitials("RileyPhone")

        assertEquals("R", initials)
    }

    @Test
    fun `marker grouping merges nearby family members into one cluster`() {
        val clusters = MapSnapshotCalculator.groupMarkerPoints(
            points = listOf(
                MapSnapshotCalculator.MarkerPoint("member-a", 33.03110, -80.13130),
                MapSnapshotCalculator.MarkerPoint("member-b", 33.03111, -80.13131),
                MapSnapshotCalculator.MarkerPoint("member-c", 33.04110, -80.14130),
            ),
            groupingRadiusMeters = 40.0,
        )

        assertEquals(2, clusters.size)
        assertEquals(listOf("member-a", "member-b"), clusters[0].items)
        assertEquals(listOf("member-c"), clusters[1].items)
    }

    private fun point(
        observedAt: String,
        latitude: Double,
        longitude: Double,
        accuracyM: Double? = null,
    ): LocationPoint {
        return LocationPoint(
            memberId = "member-1",
            observedAt = observedAt,
            latitude = latitude,
            longitude = longitude,
            accuracyM = accuracyM,
            batteryLevel = null,
            sourceEntityId = null,
        )
    }
}
