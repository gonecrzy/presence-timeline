package com.gonecrzy.gpstrack.data.model

data class DeviceSummary(
    val id: String,
    val provider: String,
    val externalId: String,
    val label: String?,
    val ignored: Boolean,
    val lastSeenAt: String?,
)

data class MemberSummary(
    val id: String,
    val displayName: String,
    val isChild: Boolean,
    val lastSeenAt: String?,
    val devices: List<DeviceSummary>,
)

data class LocationPoint(
    val memberId: String,
    val observedAt: String,
    val latitude: Double,
    val longitude: Double,
    val accuracyM: Double?,
    val batteryLevel: Int?,
    val sourceEntityId: String?,
)

data class LocationStop(
    val startedAt: String,
    val endedAt: String,
    val durationSeconds: Int,
    val latitude: Double,
    val longitude: Double,
    val pointCount: Int,
    val placeId: String?,
    val placeName: String?,
    val address: String?,
    val label: String?,
)

data class PlaceSummary(
    val id: String,
    val name: String,
    val placeType: String?,
    val latitude: Double,
    val longitude: Double,
    val radiusM: Double,
    val isSafeZone: Boolean,
)

data class TimelineItem(
    val kind: String,
    val observedAt: String,
    val tripId: String? = null,
    val startedAt: String? = null,
    val endedAt: String? = null,
    val durationSeconds: Int? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val label: String? = null,
    val isCurrent: Boolean? = null,
    val batteryLevel: Int? = null,
    val sourceEntityId: String? = null,
    val distanceM: Double? = null,
    val pointCount: Int? = null,
    val startLabel: String? = null,
    val endLabel: String? = null,
    val eventType: String? = null,
    val severity: String? = null,
    val placeId: String? = null,
    val payload: Map<String, Any?>? = null,
)

data class TripSummary(
    val id: String,
    val startedAt: String,
    val endedAt: String?,
    val pointCount: Int,
    val distanceM: Double,
    val startLabel: String?,
    val endLabel: String?,
)

data class DailySummary(
    val summaryDate: String,
    val firstSeenAt: String?,
    val lastSeenAt: String?,
    val tripCount: Int,
    val totalDistanceM: Double,
)

data class TripRoutePoint(
    val memberId: String,
    val observedAt: String,
    val latitude: Double,
    val longitude: Double,
    val accuracyM: Double?,
    val batteryLevel: Int?,
    val sourceEntityId: String?,
)

data class TripRoute(
    val id: String,
    val memberId: String,
    val startedAt: String,
    val endedAt: String?,
    val distanceM: Double,
    val pointCount: Int,
    val points: List<TripRoutePoint>,
)
