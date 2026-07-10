package com.gonecrzy.gpstrack.ui.model

import java.time.Clock
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId

data class HistoryQueryRange(
    val start: Instant,
    val end: Instant,
)

fun currentHistoryDate(
    clock: Clock = Clock.system(ZoneId.systemDefault()),
): LocalDate = LocalDate.now(clock)

fun historyQueryRange(
    period: HistoryPeriod,
    selectedDate: LocalDate,
    zoneId: ZoneId = ZoneId.systemDefault(),
): HistoryQueryRange {
    val startDate = when (period) {
        HistoryPeriod.DAY -> selectedDate
        HistoryPeriod.WEEK -> selectedDate.minusDays(6)
        HistoryPeriod.MONTH -> selectedDate.minusDays(29)
    }
    val start = startDate.atStartOfDay(zoneId).toInstant()
    val end = selectedDate.plusDays(1).atStartOfDay(zoneId).toInstant()
    return HistoryQueryRange(start = start, end = end)
}
