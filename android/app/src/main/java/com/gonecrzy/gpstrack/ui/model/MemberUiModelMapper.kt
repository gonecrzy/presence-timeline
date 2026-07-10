package com.gonecrzy.gpstrack.ui.model

import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.ui.format.formatPhoneDateTime
import com.gonecrzy.gpstrack.ui.map.MapSnapshotCalculator
import java.time.Duration
import java.time.Instant

private val LiveThreshold: Duration = Duration.ofMinutes(15)
private val OfflineThreshold: Duration = Duration.ofMinutes(90)

fun MemberSummary.toFamilyMemberUiModel(
    latestLocation: LocationPoint?,
    now: Instant = Instant.now(),
): FamilyMemberUiModel {
    val observedAt = latestLocation?.observedAt ?: lastSeenAt
    val observedInstant = observedAt?.let { value -> runCatching { Instant.parse(value) }.getOrNull() }
    val presenceState = when {
        observedInstant == null && latestLocation == null -> PresenceState.UNKNOWN
        observedInstant == null -> PresenceState.UNKNOWN
        Duration.between(observedInstant, now) <= LiveThreshold -> PresenceState.LIVE
        Duration.between(observedInstant, now) <= OfflineThreshold -> PresenceState.STALE
        else -> PresenceState.OFFLINE
    }
    val (locationLabel, secondaryLocationLabel) = splitLocationLabel(currentLocationLabel)

    return FamilyMemberUiModel(
        id = id,
        displayName = displayName,
        initials = MapSnapshotCalculator.buildInitials(displayName),
        photoUrl = null,
        role = if (isChild) MemberRole.CHILD else MemberRole.PARENT,
        locationLabel = locationLabel ?: "Location unavailable",
        secondaryLocationLabel = secondaryLocationLabel,
        lastUpdatedLabel = buildLastUpdatedLabel(observedAt, observedInstant, now, presenceState),
        presenceState = presenceState,
        batteryPercent = latestLocation?.batteryLevel,
        latitude = latestLocation?.latitude,
        longitude = latestLocation?.longitude,
        accuracyMeters = latestLocation?.accuracyM,
    )
}

private fun splitLocationLabel(rawLabel: String?): Pair<String?, String?> {
    val value = rawLabel?.trim().orEmpty()
    if (value.isBlank()) {
        return null to null
    }

    val delimiterIndex = value.indexOf(',')
    if (delimiterIndex < 0) {
        return value to null
    }

    val primary = value.substring(0, delimiterIndex).trim()
    val secondary = value.substring(delimiterIndex + 1).trim().ifBlank { null }
    return primary.ifBlank { value } to secondary
}

private fun buildLastUpdatedLabel(
    observedAt: String?,
    observedInstant: Instant?,
    now: Instant,
    presenceState: PresenceState,
): String {
    if (observedAt == null || observedInstant == null) {
        return "Last seen unavailable"
    }

    if (presenceState == PresenceState.OFFLINE) {
        return "Last seen ${formatPhoneDateTime(observedAt)}"
    }

    val elapsed = Duration.between(observedInstant, now).coerceAtLeast(Duration.ZERO)
    val hours = elapsed.toHours()
    val minutes = elapsed.minusHours(hours).toMinutes()
    val relativeLabel = when {
        hours > 0 -> {
            if (minutes > 0) "${hours} hr ${minutes} min ago" else "${hours} hr ago"
        }

        minutes > 0 -> "${minutes} min ago"
        else -> "just now"
    }
    return "Updated $relativeLabel"
}
