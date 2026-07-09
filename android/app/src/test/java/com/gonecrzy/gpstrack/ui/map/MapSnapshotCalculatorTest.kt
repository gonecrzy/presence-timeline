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

    private fun point(observedAt: String, latitude: Double, longitude: Double): LocationPoint {
        return LocationPoint(
            memberId = "member-1",
            observedAt = observedAt,
            latitude = latitude,
            longitude = longitude,
            accuracyM = null,
            batteryLevel = null,
            sourceEntityId = null,
        )
    }
}
