package com.gonecrzy.gpstrack.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.model.MapScreenUiState
import com.gonecrzy.gpstrack.ui.model.toFamilyMemberUiModel
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class MapViewModel(
    private val repository: GpsTrackRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(MapScreenUiState())
    val uiState = _uiState.asStateFlow()

    init {
        observeMembers()
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.update { state ->
                state.copy(
                    isLoading = state.members.isEmpty(),
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
                            errorMessage = "Unable to refresh the live map right now.",
                        )
                    }
                }
        }
    }

    fun selectMember(memberId: String?) {
        _uiState.update { state ->
            state.copy(selectedMemberId = memberId)
        }
    }

    private fun observeMembers() {
        viewModelScope.launch {
            repository.observeMembers().collectLatest { members ->
                val latestLocations = loadLatestLocations(members)
                val uiMembers = members.map { member ->
                    member.toFamilyMemberUiModel(latestLocation = latestLocations[member.id])
                }
                _uiState.update { state ->
                    val selectedMemberId = state.selectedMemberId
                        ?.takeIf { selectedId -> uiMembers.any { member -> member.id == selectedId } }
                    state.copy(
                        isLoading = false,
                        isRefreshing = false,
                        members = uiMembers,
                        selectedMemberId = selectedMemberId,
                        errorMessage = state.errorMessage.takeUnless { uiMembers.isNotEmpty() },
                    )
                }
            }
        }
    }

    private suspend fun loadLatestLocations(
        members: List<MemberSummary>,
    ): Map<String, LocationPoint?> {
        if (members.isEmpty()) {
            return emptyMap()
        }
        return coroutineScope {
            members.map { member ->
                async { member.id to runCatching { repository.loadLatestLocation(member.id) }.getOrNull() }
            }.awaitAll().toMap()
        }
    }
}
