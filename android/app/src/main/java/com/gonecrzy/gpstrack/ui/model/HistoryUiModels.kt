package com.gonecrzy.gpstrack.ui.model

import androidx.compose.runtime.Immutable
import java.time.LocalDate

enum class HistoryPeriod {
    DAY,
    WEEK,
    MONTH,
}

@Immutable
data class HistoryTimelineItemUiModel(
    val id: String,
    val title: String,
    val subtitle: String?,
    val timeLabel: String,
    val metaLabel: String?,
    val latitude: Double?,
    val longitude: Double?,
    val isSelected: Boolean,
    val kind: HistoryTimelineKind,
)

enum class HistoryTimelineKind {
    STAY,
    TRIP,
    EVENT,
    SUMMARY,
}

@Immutable
data class HistoryMapMarkerUiModel(
    val id: String,
    val label: String,
    val latitude: Double,
    val longitude: Double,
    val isSelected: Boolean,
    val kind: HistoryMapMarkerKind,
)

enum class HistoryMapMarkerKind {
    START,
    END,
    STOP,
    SUMMARY,
}

@Immutable
data class HistoryMapUiModel(
    val routePoints: List<HistoryRoutePointUiModel>,
    val markers: List<HistoryMapMarkerUiModel>,
)

@Immutable
data class HistoryRoutePointUiModel(
    val id: String,
    val latitude: Double,
    val longitude: Double,
)

@Immutable
data class HistoryMemberOptionUiModel(
    val id: String,
    val label: String,
)

@Immutable
data class HistoryScreenUiState(
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val members: List<HistoryMemberOptionUiModel> = emptyList(),
    val selectedMemberId: String? = null,
    val period: HistoryPeriod = HistoryPeriod.DAY,
    val selectedDate: LocalDate = LocalDate.now(),
    val summaryLabel: String? = null,
    val map: HistoryMapUiModel = HistoryMapUiModel(emptyList(), emptyList()),
    val timeline: List<HistoryTimelineItemUiModel> = emptyList(),
    val errorMessage: String? = null,
)

@Immutable
data class MemberDetailUiState(
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val member: FamilyMemberUiModel? = null,
    val selectedDate: LocalDate = LocalDate.now(),
    val summaryLabel: String? = null,
    val timeline: List<HistoryTimelineItemUiModel> = emptyList(),
    val errorMessage: String? = null,
)
