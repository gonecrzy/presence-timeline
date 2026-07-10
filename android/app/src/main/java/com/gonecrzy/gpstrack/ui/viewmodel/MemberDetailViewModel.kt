package com.gonecrzy.gpstrack.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.model.MemberDetailUiState
import com.gonecrzy.gpstrack.ui.model.buildDayTimelineItems
import com.gonecrzy.gpstrack.ui.model.buildHistorySummaryLabel
import com.gonecrzy.gpstrack.ui.model.currentHistoryDate
import com.gonecrzy.gpstrack.ui.model.historyQueryRange
import com.gonecrzy.gpstrack.ui.model.toFamilyMemberUiModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class MemberDetailViewModel(
    private val repository: GpsTrackRepository,
    private val memberId: String,
) : ViewModel() {
    private val _uiState = MutableStateFlow(
        MemberDetailUiState(selectedDate = currentHistoryDate()),
    )
    val uiState = _uiState.asStateFlow()

    private var currentMember: MemberSummary? = null
    private var refreshJob: Job? = null

    init {
        observeMember()
        refresh()
    }

    fun refresh() {
        if (refreshJob?.isActive == true) {
            return
        }
        refreshJob = viewModelScope.launch {
            _uiState.update { state ->
                state.copy(
                    isLoading = state.member == null,
                    isRefreshing = true,
                    errorMessage = null,
                )
            }
            runCatching { repository.refreshMembers() }
                .onFailure {
                    _uiState.update { state ->
                        state.copy(
                            isLoading = false,
                            isRefreshing = false,
                            errorMessage = "Unable to refresh this family member right now.",
                        )
                    }
                }
            loadToday()
        }
    }

    private fun observeMember() {
        viewModelScope.launch {
            repository.observeMembers().collectLatest { members ->
                currentMember = members.firstOrNull { it.id == memberId }
                loadToday()
            }
        }
    }

    private fun loadToday() {
        val member = currentMember ?: run {
            _uiState.update { state ->
                state.copy(
                    isLoading = false,
                    isRefreshing = false,
                    errorMessage = "This family member is unavailable.",
                )
            }
            return
        }
        val date = _uiState.value.selectedDate
        val range = historyQueryRange(
            period = com.gonecrzy.gpstrack.ui.model.HistoryPeriod.DAY,
            selectedDate = date,
        )
        viewModelScope.launch {
            _uiState.update { state -> state.copy(isLoading = state.member == null) }
            val latestLocation = runCatching { repository.loadLatestLocation(member.id) }.getOrNull()
            val timelineRaw = runCatching {
                repository.loadTimeline(member.id, range.start.toString(), range.end.toString())
            }.getOrDefault(emptyList())
            val summary = runCatching { repository.loadDailySummary(member.id, date.toString()) }.getOrNull()
            _uiState.update {
                it.copy(
                    isLoading = false,
                    isRefreshing = false,
                    member = member.toFamilyMemberUiModel(latestLocation = latestLocation),
                    summaryLabel = buildHistorySummaryLabel(
                        period = com.gonecrzy.gpstrack.ui.model.HistoryPeriod.DAY,
                        tripCount = summary?.tripCount,
                        distanceMeters = summary?.totalDistanceM,
                        timelineCount = timelineRaw.size,
                    ),
                    timeline = buildDayTimelineItems(timelineRaw),
                    errorMessage = null,
                )
            }
        }
    }
}
