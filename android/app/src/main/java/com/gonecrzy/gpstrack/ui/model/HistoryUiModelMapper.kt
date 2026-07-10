package com.gonecrzy.gpstrack.ui.model

import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.TimelineItem
import com.gonecrzy.gpstrack.ui.format.formatDistanceImperial
import com.gonecrzy.gpstrack.ui.format.formatDurationSeconds
import com.gonecrzy.gpstrack.ui.format.formatHistoryDateTime
import com.gonecrzy.gpstrack.ui.format.formatHistoryDateTimeRange
import com.gonecrzy.gpstrack.ui.format.formatSafetyEventSummary
import com.gonecrzy.gpstrack.ui.map.MapSnapshotCalculator
import java.time.LocalDate
import java.time.ZoneId

fun buildDayTimelineItems(
    timeline: List<TimelineItem>,
    selectedItemId: String? = null,
): List<HistoryTimelineItemUiModel> {
    return timeline.mapIndexed { index, item ->
        val id = item.timelineItemStableId(index)
        HistoryTimelineItemUiModel(
            id = id,
            title = formatTimelineTitle(item),
            subtitle = when (item.kind) {
                "location_stay" -> item.label ?: formatTimelineCoordinates(item)
                "trip" -> tripSubtitle(item)
                else -> item.label
            },
            timeLabel = formatTimelineWhen(item),
            metaLabel = when (item.kind) {
                "location_stay" -> formatStaySummary(item)
                "trip" -> tripMetaLabel(item)
                "safety_event" -> item.payload?.get("place_name") as? String
                else -> null
            },
            latitude = item.latitude,
            longitude = item.longitude,
            isSelected = id == selectedItemId,
            kind = when (item.kind) {
                "location_stay" -> HistoryTimelineKind.STAY
                "trip" -> HistoryTimelineKind.TRIP
                "safety_event" -> HistoryTimelineKind.EVENT
                else -> HistoryTimelineKind.EVENT
            },
        )
    }
}

fun buildRangeSummaryTimelineItems(
    period: HistoryPeriod,
    timeline: List<TimelineItem>,
    zoneId: ZoneId = ZoneId.systemDefault(),
): List<HistoryTimelineItemUiModel> {
    require(period != HistoryPeriod.DAY)
    val grouped = timeline
        .filter { it.kind == "location_stay" }
        .groupBy { item ->
            val title = item.label ?: formatTimelineCoordinates(item)
            val day = item.startedAt ?: item.observedAt
            val localDate = parseLocalDate(day, zoneId)
            localDate to title
        }

    return grouped.entries
        .sortedByDescending { it.key.first }
        .mapIndexed { index, (key, items) ->
            val totalDurationSeconds = items.sumOf { it.durationSeconds ?: 0 }
            val representative = items.maxByOrNull { it.durationSeconds ?: 0 } ?: items.first()
            val visits = items.size
            HistoryTimelineItemUiModel(
                id = "summary-${key.first}-$index",
                title = key.second,
                subtitle = key.first.toString(),
                timeLabel = key.first.toString(),
                metaLabel = buildString {
                    append("$visits visit")
                    if (visits != 1) append("s")
                    if (totalDurationSeconds > 0) {
                        append(" · ${formatDurationSeconds(totalDurationSeconds)}")
                    }
                },
                latitude = representative.latitude,
                longitude = representative.longitude,
                isSelected = false,
                kind = HistoryTimelineKind.SUMMARY,
            )
        }
}

fun buildHistoryMapUiModel(
    period: HistoryPeriod,
    historyPoints: List<LocationPoint>,
    timelineItems: List<HistoryTimelineItemUiModel>,
): HistoryMapUiModel {
    val routePoints = if (period == HistoryPeriod.DAY) {
        MapSnapshotCalculator.buildDisplayRoute(
            points = historyPoints,
            dwellRadiusMeters = 250.0,
            minimumSegmentMeters = 25.0,
        ).map { point ->
            HistoryRoutePointUiModel(
                id = point.observedAt,
                latitude = point.latitude,
                longitude = point.longitude,
            )
        }
    } else {
        emptyList()
    }

    val markers = buildList {
        if (routePoints.isNotEmpty()) {
            routePoints.firstOrNull()?.let { start ->
                add(
                    HistoryMapMarkerUiModel(
                        id = "start-${start.id}",
                        label = "Start",
                        latitude = start.latitude,
                        longitude = start.longitude,
                        isSelected = false,
                        kind = HistoryMapMarkerKind.START,
                    ),
                )
            }
            routePoints.lastOrNull()?.let { end ->
                add(
                    HistoryMapMarkerUiModel(
                        id = "end-${end.id}",
                        label = "End",
                        latitude = end.latitude,
                        longitude = end.longitude,
                        isSelected = false,
                        kind = HistoryMapMarkerKind.END,
                    ),
                )
            }
        }
        timelineItems.forEach { item ->
            val latitude = item.latitude ?: return@forEach
            val longitude = item.longitude ?: return@forEach
            add(
                HistoryMapMarkerUiModel(
                    id = item.id,
                    label = item.title,
                    latitude = latitude,
                    longitude = longitude,
                    isSelected = item.isSelected,
                    kind = if (period == HistoryPeriod.DAY) HistoryMapMarkerKind.STOP else HistoryMapMarkerKind.SUMMARY,
                ),
            )
        }
    }

    return HistoryMapUiModel(
        routePoints = routePoints,
        markers = markers,
    )
}

fun buildHistorySummaryLabel(
    period: HistoryPeriod,
    tripCount: Int?,
    distanceMeters: Double?,
    timelineCount: Int,
): String {
    return when (period) {
        HistoryPeriod.DAY -> buildString {
            tripCount?.let { append("$it trip") ; if (it != 1) append("s") }
            distanceMeters?.let {
                if (isNotEmpty()) append(" · ")
                append(formatDistanceImperial(it))
            }
            if (timelineCount > 0) {
                if (isNotEmpty()) append(" · ")
                append("$timelineCount timeline events")
            }
        }.ifBlank { "No activity recorded" }

        HistoryPeriod.WEEK,
        HistoryPeriod.MONTH,
        -> if (timelineCount > 0) "$timelineCount summarized stops" else "No activity recorded"
    }
}

private fun TimelineItem.timelineItemStableId(index: Int): String {
    return "${kind}-${observedAt}-${tripId ?: ""}-${startedAt ?: ""}-${index}"
}

private fun formatTimelineTitle(item: TimelineItem): String {
    return when (item.kind) {
        "location_stay" -> if (item.isCurrent == true) "Current location" else "Location stay"
        "safety_event" -> formatSafetyEventSummary(
            eventType = item.eventType,
            placeName = item.payload?.get("place_name") as? String,
            observedAt = item.observedAt,
        )
        "trip" -> "Trip"
        else -> item.kind.replace('_', ' ')
    }
}

private fun formatTimelineWhen(item: TimelineItem): String {
    return when (item.kind) {
        "location_stay" -> {
            val start = item.startedAt ?: item.observedAt
            val end = item.endedAt
            if (item.isCurrent == true) {
                "Since ${formatHistoryDateTime(start)}"
            } else {
                formatHistoryDateTimeRange(start, end)
            }
        }

        "trip" -> {
            val start = item.startedAt ?: item.observedAt
            val end = item.endedAt
            formatHistoryDateTimeRange(start, end)
        }

        else -> formatHistoryDateTime(item.observedAt)
    }
}

private fun formatStaySummary(item: TimelineItem): String {
    val duration = item.durationSeconds?.let(::formatDurationSeconds) ?: "a short time"
    return if (item.isCurrent == true) {
        "At this location for $duration"
    } else {
        "Stayed for $duration"
    }
}

private fun tripSubtitle(item: TimelineItem): String? {
    val start = item.startLabel
    val end = item.endLabel
    return when {
        !start.isNullOrBlank() && !end.isNullOrBlank() -> "$start to $end"
        !end.isNullOrBlank() -> end
        !start.isNullOrBlank() -> start
        else -> null
    }
}

private fun tripMetaLabel(item: TimelineItem): String? {
    return item.distanceM?.let(::formatDistanceImperial)
}

private fun formatTimelineCoordinates(item: TimelineItem): String {
    val latitude = item.latitude ?: 0.0
    val longitude = item.longitude ?: 0.0
    return "${"%.4f".format(latitude)}, ${"%.4f".format(longitude)}"
}

private fun parseLocalDate(value: String, zoneId: ZoneId): LocalDate {
    return java.time.Instant.parse(value).atZone(zoneId).toLocalDate()
}
