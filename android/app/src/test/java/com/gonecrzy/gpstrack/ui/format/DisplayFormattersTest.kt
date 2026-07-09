package com.gonecrzy.gpstrack.ui.format

import java.time.LocalDate
import java.time.ZoneId
import org.junit.Assert.assertEquals
import org.junit.Test

class DisplayFormattersTest {
    @Test
    fun `distance formatter uses feet under one mile`() {
        assertEquals("3120 ft", formatDistanceImperial(950.0))
    }

    @Test
    fun `distance formatter uses rounded miles for long trips`() {
        assertEquals("33 mi", formatDistanceImperial(53106.0))
    }

    @Test
    fun `history timestamp drops date when entry is today`() {
        val value = formatHistoryDateTime(
            value = "2026-07-09T18:03:00Z",
            today = LocalDate.of(2026, 7, 9),
            zoneId = ZoneId.of("UTC"),
        )

        assertEquals("18:03", value)
    }

    @Test
    fun `history timestamp keeps date when entry is not today`() {
        val value = formatHistoryDateTime(
            value = "2026-07-08T20:14:00Z",
            today = LocalDate.of(2026, 7, 9),
            zoneId = ZoneId.of("UTC"),
        )

        assertEquals("07/08/26 20:14", value)
    }

    @Test
    fun `history safety event formats place arrival language`() {
        val value = formatSafetyEventSummary(
            eventType = "safe_zone_entered",
            placeName = "Home",
            observedAt = "2026-07-09T16:20:00Z",
            today = LocalDate.of(2026, 7, 9),
            zoneId = ZoneId.of("UTC"),
        )

        assertEquals("Arrived Home at 16:20", value)
    }

    @Test
    fun `history safety event formats place departure language`() {
        val value = formatSafetyEventSummary(
            eventType = "safe_zone_exited",
            placeName = "Home",
            observedAt = "2026-07-08T16:20:00Z",
            today = LocalDate.of(2026, 7, 9),
            zoneId = ZoneId.of("UTC"),
        )

        assertEquals("Left Home at 07/08/26 16:20", value)
    }
}
