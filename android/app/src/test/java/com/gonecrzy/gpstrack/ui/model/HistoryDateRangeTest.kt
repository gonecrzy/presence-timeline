package com.gonecrzy.gpstrack.ui.model

import java.time.Clock
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import org.junit.Assert.assertEquals
import org.junit.Test

class HistoryDateRangeTest {
    @Test
    fun `current history date uses local timezone instead of utc rollover`() {
        val zoneId = ZoneId.of("America/New_York")
        val clock = Clock.fixed(Instant.parse("2026-07-10T00:30:00Z"), zoneId)

        val date = currentHistoryDate(clock)

        assertEquals(LocalDate.of(2026, 7, 9), date)
    }

    @Test
    fun `day range converts local midnight boundaries to utc instants`() {
        val zoneId = ZoneId.of("America/New_York")

        val range = historyQueryRange(
            period = HistoryPeriod.DAY,
            selectedDate = LocalDate.of(2026, 7, 9),
            zoneId = zoneId,
        )

        assertEquals("2026-07-09T04:00:00Z", range.start.toString())
        assertEquals("2026-07-10T04:00:00Z", range.end.toString())
    }

    @Test
    fun `week range keeps local end of selected day`() {
        val zoneId = ZoneId.of("America/New_York")

        val range = historyQueryRange(
            period = HistoryPeriod.WEEK,
            selectedDate = LocalDate.of(2026, 7, 9),
            zoneId = zoneId,
        )

        assertEquals("2026-07-03T04:00:00Z", range.start.toString())
        assertEquals("2026-07-10T04:00:00Z", range.end.toString())
    }
}
