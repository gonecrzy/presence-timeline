package com.gonecrzy.gpstrack.ui.format

import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale
import kotlin.math.roundToInt

private val dateTimeFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("MM/dd/yy HH:mm")
    .withZone(ZoneId.systemDefault())
private val dateFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("MM/dd/yy")
private val timeFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("HH:mm")
    .withZone(ZoneId.systemDefault())
private const val FeetPerMeter = 3.28084
private const val MetersPerMile = 1609.344

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

fun formatHistoryDateTime(value: String?): String {
    return formatHistoryDateTime(
        value = value,
        today = LocalDate.now(ZoneId.systemDefault()),
        zoneId = ZoneId.systemDefault(),
    )
}

fun formatHistoryDateTimeRange(start: String?, end: String?): String {
    val startLabel = formatHistoryDateTime(start)
    val endLabel = end?.let(::formatHistoryDateTime) ?: "In progress"
    return "$startLabel to $endLabel"
}

fun formatSafetyEventSummary(
    eventType: String?,
    placeName: String?,
    observedAt: String?,
): String {
    return formatSafetyEventSummary(
        eventType = eventType,
        placeName = placeName,
        observedAt = observedAt,
        today = LocalDate.now(ZoneId.systemDefault()),
        zoneId = ZoneId.systemDefault(),
    )
}

internal fun formatHistoryDateTime(
    value: String?,
    today: LocalDate,
    zoneId: ZoneId,
): String {
    if (value == null) {
        return "Unknown time"
    }
    return runCatching {
        val instant = Instant.parse(value)
        val localDate = instant.atZone(zoneId).toLocalDate()
        if (localDate == today) {
            timeFormatter.withZone(zoneId).format(instant)
        } else {
            dateTimeFormatter.withZone(zoneId).format(instant)
        }
    }.getOrDefault(value)
}

internal fun formatSafetyEventSummary(
    eventType: String?,
    placeName: String?,
    observedAt: String?,
    today: LocalDate,
    zoneId: ZoneId,
): String {
    val action = when (eventType) {
        "safe_zone_entered" -> "Arrived"
        "safe_zone_exited" -> "Left"
        else -> "Updated"
    }
    val target = placeName ?: "place"
    val atTime = formatHistoryDateTime(observedAt, today, zoneId)
    return "$action $target at $atTime"
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

fun formatDistanceImperial(distanceMeters: Double?): String {
    val safeDistance = (distanceMeters ?: 0.0).coerceAtLeast(0.0)
    return when {
        safeDistance < MetersPerMile -> {
            val roundedFeet = ((safeDistance * FeetPerMeter) / 10.0).roundToInt() * 10
            "${roundedFeet} ft"
        }

        safeDistance < MetersPerMile * 10 -> {
            String.format(Locale.US, "%.1f mi", safeDistance / MetersPerMile)
        }

        else -> "${(safeDistance / MetersPerMile).roundToInt()} mi"
    }
}
