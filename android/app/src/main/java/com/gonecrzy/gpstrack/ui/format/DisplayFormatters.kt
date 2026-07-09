package com.gonecrzy.gpstrack.ui.format

import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter

private val dateTimeFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("MM/dd/yy HH:mm")
    .withZone(ZoneId.systemDefault())
private val dateFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("MM/dd/yy")

fun formatPhoneDateTime(value: String?): String {
    if (value == null) {
        return "No recent update"
    }
    return runCatching {
        dateTimeFormatter.format(Instant.parse(value))
    }.getOrDefault(value)
}

fun formatPhoneDateTimeRange(start: String?, end: String?): String {
    val startLabel = formatPhoneDateTime(start)
    val endLabel = end?.let(::formatPhoneDateTime) ?: "In progress"
    return "$startLabel to $endLabel"
}

fun formatDisplayDate(value: LocalDate): String {
    return dateFormatter.format(value)
}

fun formatDurationSeconds(durationSeconds: Int): String {
    val duration = Duration.ofSeconds(durationSeconds.toLong())
    val hours = duration.toHours()
    val minutes = duration.minusHours(hours).toMinutes()

    return when {
        hours > 0 && minutes > 0 -> "${hours}h ${minutes}m"
        hours > 0 -> "${hours}h"
        minutes > 0 -> "${minutes}m"
        else -> "${durationSeconds}s"
    }
}
