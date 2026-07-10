package com.gonecrzy.gpstrack.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.model.HistoryMapUiModel
import com.gonecrzy.gpstrack.ui.model.HistoryMemberOptionUiModel
import com.gonecrzy.gpstrack.ui.model.HistoryPeriod
import com.gonecrzy.gpstrack.ui.model.HistoryScreenUiState
import com.gonecrzy.gpstrack.ui.model.HistoryTimelineItemUiModel
import com.gonecrzy.gpstrack.ui.model.buildDayTimelineItems
import com.gonecrzy.gpstrack.ui.model.buildHistoryMapUiModel
import com.gonecrzy.gpstrack.ui.model.buildHistorySummaryLabel
import com.gonecrzy.gpstrack.ui.model.buildRangeSummaryTimelineItems
import java.time.LocalDate
import java.time.ZoneOffset
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class HistoryViewModel(
    private val repository: GpsTrackRepository,
    initialMemberId: String?,
    initialPeriod: HistoryPeriod,
    initialDate: LocalDate,
) : ViewModel() {
    private val _uiState = MutableStateFlow(
        HistoryScreenUiState(
            selectedMemberId = initialMemberId,
            period = initialPeriod,
            selectedDate = initialDate,
        ),
    )
    val uiState = _uiState.asStateFlow()

    private var members: List<MemberSummary> = emptyList()
    private var loadJob: Job? = null
    private var selectedTimelineId: String? = null
    private var refreshJob: Job? = null

    init {
        observeMembers()
        refresh()
    }

    fun refresh() {
        if (refreshJob?.isActive == true) {
            return
        }
        refreshJob = viewModelScope.launch {
            _uiState.update { state ->
                state.copy(
                    isLoading = state.timeline.isEmpty(),
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
                            errorMessage = "Unable to refresh history right now.",
                        )
                    }
                }
            loadCurrent()
        }
    }

    fun selectMember(memberId: String) {
        selectedTimelineId = null
        _uiState.update { it.copy(selectedMemberId = memberId) }
        loadCurrent()
    }

    fun selectPeriod(period: HistoryPeriod) {
        selectedTimelineId = null
        _uiState.update { it.copy(period = period) }
        loadCurrent()
    }

    fun moveDate(days: Long) {
        selectedTimelineId = null
        _uiState.update { it.copy(selectedDate = it.selectedDate.plusDays(days)) }
        loadCurrent()
    }

    fun selectTimelineItem(itemId: String) {
        selectedTimelineId = itemId
        val state = _uiState.value
        val timeline = applySelection(state.timeline, itemId)
        _uiState.update {
            it.copy(
                timeline = timeline,
                map = buildHistoryMapUiModel(
                    period = it.period,
                    historyPoints = emptyList(),
                    timelineItems = timeline,
                ).mergeRoutePointsFrom(it.map),
            )
        }
    }

    private fun observeMembers() {
        viewModelScope.launch {
            repository.observeMembers().collectLatest { observedMembers ->
                members = observedMembers
                val selectedMemberId = resolveSelectedMemberId(observedMembers)
                _uiState.update { state ->
                    state.copy(
                        members = observedMembers.map { member ->
                            HistoryMemberOptionUiModel(
                                id = member.id,
                                label = member.displayName,
                            )
                        },
                        selectedMemberId = selectedMemberId,
                    )
                }
                loadCurrent()
            }
        }
    }

    private fun resolveSelectedMemberId(observedMembers: List<MemberSummary>): String? {
        val current = _uiState.value.selectedMemberId
        return when {
            current != null && observedMembers.any { it.id == current } -> current
            observedMembers.isNotEmpty() -> observedMembers.first().id
            else -> null
        }
    }

    private fun loadCurrent() {
        val state = _uiState.value
        val memberId = state.selectedMemberId ?: return
        val period = state.period
        val date = state.selectedDate
        val (start, end) = when (period) {
            HistoryPeriod.DAY -> date.atStartOfDay(ZoneOffset.UTC).toInstant() to date.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant()
            HistoryPeriod.WEEK -> date.minusDays(6).atStartOfDay(ZoneOffset.UTC).toInstant() to date.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant()
            HistoryPeriod.MONTH -> date.minusDays(29).atStartOfDay(ZoneOffset.UTC).toInstant() to date.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant()
        }
        loadJob?.cancel()
        loadJob = viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, isRefreshing = false, errorMessage = null) }
            val timelineRaw = runCatching { repository.loadTimeline(memberId, start.toString(), end.toString()) }.getOrElse {
                _uiState.update { state ->
                    state.copy(
                        isLoading = false,
                        isRefreshing = false,
                        errorMessage = "Unable to load location history.",
                    )
                }
                return@launch
            }
            val historyPoints = if (period == HistoryPeriod.DAY) {
                runCatching { repository.loadMemberHistory(memberId, start.toString(), end.toString()) }.getOrDefault(emptyList())
            } else {
                emptyList()
            }
            val summary = if (period == HistoryPeriod.DAY) {
                runCatching { repository.loadDailySummary(memberId, date.toString()) }.getOrNull()
            } else {
                null
            }

            val baseTimeline = when (period) {
                HistoryPeriod.DAY -> buildDayTimelineItems(timelineRaw)
                HistoryPeriod.WEEK,
                HistoryPeriod.MONTH,
                -> buildRangeSummaryTimelineItems(period, timelineRaw)
            }
            val effectiveSelectedId = selectedTimelineId?.takeIf { selected ->
                baseTimeline.any { it.id == selected }
            }
            val selectedTimeline = applySelection(baseTimeline, effectiveSelectedId)
            val map = buildHistoryMapUiModel(period, historyPoints, selectedTimeline)
            _uiState.update {
                it.copy(
                    isLoading = false,
                    isRefreshing = false,
                    summaryLabel = buildHistorySummaryLabel(
                        period = period,
                        tripCount = summary?.tripCount,
                        distanceMeters = summary?.totalDistanceM,
                        timelineCount = selectedTimeline.size,
                    ),
                    map = map,
                    timeline = selectedTimeline,
                    errorMessage = null,
                )
            }
        }
    }

    private fun applySelection(
        items: List<HistoryTimelineItemUiModel>,
        selectedId: String?,
    ): List<HistoryTimelineItemUiModel> {
        return items.map { item -> item.copy(isSelected = item.id == selectedId) }
    }

    private fun HistoryMapUiModel.mergeRoutePointsFrom(
        existing: HistoryMapUiModel,
    ): HistoryMapUiModel {
        return copy(routePoints = existing.routePoints)
    }
}
