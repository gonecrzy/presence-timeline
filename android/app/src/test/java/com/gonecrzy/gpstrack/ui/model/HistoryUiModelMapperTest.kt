package com.gonecrzy.gpstrack.ui.model

import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.TimelineItem
import java.time.ZoneId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HistoryUiModelMapperTest {
    @Test
    fun `week summary groups location stays by date and label`() {
        val items = listOf(
            stay(
                observedAt = "2026-07-10T15:00:00Z",
                startedAt = "2026-07-10T14:00:00Z",
                endedAt = "2026-07-10T15:00:00Z",
                label = "Home",
                durationSeconds = 3600,
                latitude = 32.77,
                longitude = -79.92,
            ),
            stay(
                observedAt = "2026-07-10T18:00:00Z",
                startedAt = "2026-07-10T17:00:00Z",
                endedAt = "2026-07-10T18:00:00Z",
                label = "Home",
                durationSeconds = 3600,
                latitude = 32.77,
                longitude = -79.92,
            ),
        )

        val result = buildRangeSummaryTimelineItems(
            period = HistoryPeriod.WEEK,
            timeline = items,
            zoneId = ZoneId.of("UTC"),
        )

        assertEquals(1, result.size)
        assertEquals("Home", result.first().title)
        assertEquals("2 visits · 2h", result.first().metaLabel)
    }

    @Test
    fun `day map model includes route and selected timeline markers`() {
        val historyPoints = listOf(
            point("2026-07-10T10:00:00Z", 32.7700, -79.9200),
            point("2026-07-10T10:15:00Z", 32.7710, -79.9210),
            point("2026-07-10T10:30:00Z", 32.7720, -79.9220),
        )
        val timeline = listOf(
            HistoryTimelineItemUiModel(
                id = "stay-1",
                title = "School",
                subtitle = null,
                timeLabel = "10:30",
                metaLabel = "Stayed for 20m",
                latitude = 32.7720,
                longitude = -79.9220,
                isSelected = true,
                kind = HistoryTimelineKind.STAY,
            ),
        )

        val map = buildHistoryMapUiModel(
            period = HistoryPeriod.DAY,
            historyPoints = historyPoints,
            timelineItems = timeline,
        )

        assertEquals(3, map.routePoints.size)
        assertEquals(3, map.markers.size)
        assertTrue(map.markers.any { it.id == "stay-1" && it.isSelected })
    }

    @Test
    fun `day map model adds waypoint markers only for stay timeline items`() {
        val historyPoints = listOf(
            point("2026-07-10T10:00:00Z", 32.7700, -79.9200),
            point("2026-07-10T10:15:00Z", 32.7710, -79.9210),
            point("2026-07-10T10:30:00Z", 32.7720, -79.9220),
        )
        val timeline = listOf(
            HistoryTimelineItemUiModel(
                id = "stay-1",
                title = "School",
                subtitle = null,
                timeLabel = "10:30",
                metaLabel = "Stayed for 20m",
                latitude = 32.7720,
                longitude = -79.9220,
                isSelected = true,
                kind = HistoryTimelineKind.STAY,
            ),
            HistoryTimelineItemUiModel(
                id = "trip-1",
                title = "Trip",
                subtitle = "School to Home",
                timeLabel = "10:30 to 10:45",
                metaLabel = "3 mi",
                latitude = 32.7730,
                longitude = -79.9230,
                isSelected = false,
                kind = HistoryTimelineKind.TRIP,
            ),
            HistoryTimelineItemUiModel(
                id = "event-1",
                title = "Arrived Home",
                subtitle = "Home",
                timeLabel = "10:45",
                metaLabel = null,
                latitude = 32.7740,
                longitude = -79.9240,
                isSelected = false,
                kind = HistoryTimelineKind.EVENT,
            ),
        )

        val map = buildHistoryMapUiModel(
            period = HistoryPeriod.DAY,
            historyPoints = historyPoints,
            timelineItems = timeline,
        )

        assertEquals(3, map.markers.size)
        assertTrue(map.markers.any { it.id == "stay-1" && it.kind == HistoryMapMarkerKind.STOP })
        assertTrue(map.markers.none { it.id == "trip-1" })
        assertTrue(map.markers.none { it.id == "event-1" })
    }

    private fun stay(
        observedAt: String,
        startedAt: String,
        endedAt: String,
        label: String,
        durationSeconds: Int,
        latitude: Double,
        longitude: Double,
    ) = TimelineItem(
        kind = "location_stay",
        observedAt = observedAt,
        startedAt = startedAt,
        endedAt = endedAt,
        durationSeconds = durationSeconds,
        latitude = latitude,
        longitude = longitude,
        label = label,
    )

    private fun point(
        observedAt: String,
        latitude: Double,
        longitude: Double,
    ) = LocationPoint(
        memberId = "member-1",
        observedAt = observedAt,
        latitude = latitude,
        longitude = longitude,
        accuracyM = 10.0,
        batteryLevel = 80,
        sourceEntityId = null,
    )
}
