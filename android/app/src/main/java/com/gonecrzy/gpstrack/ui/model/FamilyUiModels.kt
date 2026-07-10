package com.gonecrzy.gpstrack.ui.model

import androidx.compose.runtime.Immutable

@Immutable
data class FamilyScreenUiState(
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val members: List<FamilyMemberUiModel> = emptyList(),
    val errorMessage: String? = null,
)

@Immutable
data class MapScreenUiState(
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val members: List<FamilyMemberUiModel> = emptyList(),
    val selectedMemberId: String? = null,
    val errorMessage: String? = null,
)

@Immutable
data class FamilyMemberUiModel(
    val id: String,
    val displayName: String,
    val initials: String,
    val photoUrl: String?,
    val role: MemberRole,
    val locationLabel: String,
    val secondaryLocationLabel: String?,
    val lastUpdatedLabel: String,
    val presenceState: PresenceState,
    val batteryPercent: Int?,
    val latitude: Double?,
    val longitude: Double?,
    val accuracyMeters: Double?,
)

enum class MemberRole {
    PARENT,
    CHILD,
}

enum class PresenceState {
    LIVE,
    STALE,
    OFFLINE,
    UNKNOWN,
}
