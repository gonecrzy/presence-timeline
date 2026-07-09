package com.gonecrzy.gpstrack.data.network

import com.squareup.moshi.Json

data class MemberListResponseDto(val items: List<MemberDto>)

data class MemberDto(
    val id: String,
    @Json(name = "display_name") val displayName: String,
    @Json(name = "is_child") val isChild: Boolean,
    @Json(name = "last_seen_at") val lastSeenAt: String?,
    val devices: List<DeviceDto>,
)

data class DeviceDto(
    val id: String,
    val provider: String,
    @Json(name = "external_id") val externalId: String,
    val label: String?,
    val ignored: Boolean,
    @Json(name = "last_seen_at") val lastSeenAt: String?,
)

data class LocationPointDto(
    @Json(name = "member_id") val memberId: String,
    @Json(name = "observed_at") val observedAt: String,
    val latitude: Double,
    val longitude: Double,
    @Json(name = "accuracy_m") val accuracyM: Double?,
    @Json(name = "battery_level") val batteryLevel: Int?,
    @Json(name = "source_entity_id") val sourceEntityId: String?,
)

data class LocationHistoryResponseDto(val items: List<LocationPointDto>)

data class MemberUpdateRequestDto(
    @Json(name = "display_name") val displayName: String?,
    @Json(name = "is_child") val isChild: Boolean?,
    @Json(name = "avatar_color") val avatarColor: String? = null,
)

data class DeviceUpdateRequestDto(
    val label: String?,
    val ignored: Boolean?,
)

data class PlaceListResponseDto(val items: List<PlaceDto>)

data class PlaceDto(
    val id: String,
    val name: String,
    @Json(name = "place_type") val placeType: String?,
    val latitude: Double,
    val longitude: Double,
    @Json(name = "radius_m") val radiusM: Double,
    @Json(name = "is_safe_zone") val isSafeZone: Boolean,
)

data class PlaceUpsertRequestDto(
    val name: String,
    @Json(name = "place_type") val placeType: String?,
    val latitude: Double,
    val longitude: Double,
    @Json(name = "radius_m") val radiusM: Double,
    @Json(name = "is_safe_zone") val isSafeZone: Boolean,
)

data class TimelineResponseDto(val items: List<TimelineItemDto>)

data class TimelineItemDto(
    val kind: String,
    @Json(name = "observed_at") val observedAt: String,
    @Json(name = "trip_id") val tripId: String? = null,
    @Json(name = "started_at") val startedAt: String? = null,
    @Json(name = "ended_at") val endedAt: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    @Json(name = "battery_level") val batteryLevel: Int? = null,
    @Json(name = "source_entity_id") val sourceEntityId: String? = null,
    @Json(name = "distance_m") val distanceM: Double? = null,
    @Json(name = "point_count") val pointCount: Int? = null,
    @Json(name = "start_label") val startLabel: String? = null,
    @Json(name = "end_label") val endLabel: String? = null,
    @Json(name = "event_type") val eventType: String? = null,
    val severity: String? = null,
    @Json(name = "place_id") val placeId: String? = null,
    val payload: Map<String, Any?>? = null,
)

data class TripListResponseDto(val items: List<TripDto>)

data class TripDto(
    val id: String,
    @Json(name = "started_at") val startedAt: String,
    @Json(name = "ended_at") val endedAt: String?,
    @Json(name = "point_count") val pointCount: Int,
    @Json(name = "distance_m") val distanceM: Double,
    @Json(name = "start_label") val startLabel: String?,
    @Json(name = "end_label") val endLabel: String?,
)

data class DailySummaryDto(
    @Json(name = "summary_date") val summaryDate: String,
    @Json(name = "first_seen_at") val firstSeenAt: String?,
    @Json(name = "last_seen_at") val lastSeenAt: String?,
    @Json(name = "trip_count") val tripCount: Int,
    @Json(name = "total_distance_m") val totalDistanceM: Double,
)

data class TripRouteDto(
    val id: String,
    @Json(name = "member_id") val memberId: String,
    @Json(name = "started_at") val startedAt: String,
    @Json(name = "ended_at") val endedAt: String?,
    @Json(name = "distance_m") val distanceM: Double,
    @Json(name = "point_count") val pointCount: Int,
    val points: List<TripRoutePointDto>,
)

data class TripRoutePointDto(
    @Json(name = "member_id") val memberId: String,
    @Json(name = "observed_at") val observedAt: String,
    val latitude: Double,
    val longitude: Double,
    @Json(name = "accuracy_m") val accuracyM: Double?,
    @Json(name = "battery_level") val batteryLevel: Int?,
    @Json(name = "source_entity_id") val sourceEntityId: String?,
)
