package com.gonecrzy.gpstrack.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.model.MapPlaceUiModel
import com.gonecrzy.gpstrack.ui.model.MapScreenUiState
import kotlinx.coroutines.Job
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
    private var refreshJob: Job? = null
    private val refreshCoordinator = MemberRefreshCoordinator()

    init {
        observeMembers()
        observePlaces()
        refresh()
    }

    fun refresh() {
        if (refreshJob?.isActive == true) {
            return
        }
        refreshJob = viewModelScope.launch {
            _uiState.update { state ->
                state.copy(
                    isLoading = state.members.isEmpty(),
                    isRefreshing = true,
                    errorMessage = null,
                )
            }
            runCatching { repository.refreshPlaces() }
            val result = refreshCoordinator.load(
                refreshMembers = repository::refreshMembers,
                currentMembers = repository::currentMembers,
                loadLatestLocation = { memberId -> repository.loadLatestLocation(memberId) },
                emptyStateErrorMessage = "Unable to refresh the live map right now.",
            )
            _uiState.update { state ->
                val selectedMemberId = state.selectedMemberId
                    ?.takeIf { selectedId -> result.members.any { member -> member.id == selectedId } }
                state.copy(
                    isLoading = false,
                    isRefreshing = false,
                    members = result.members,
                    selectedMemberId = selectedMemberId,
                    errorMessage = result.errorMessage,
                )
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
                val uiMembers = refreshCoordinator.mapMembers(
                    members = members,
                    loadLatestLocation = { memberId -> repository.loadLatestLocation(memberId) },
                )
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

    private fun observePlaces() {
        viewModelScope.launch {
            repository.observePlaces().collectLatest { places ->
                _uiState.update { state ->
                    state.copy(
                        places = places.map { place ->
                            MapPlaceUiModel(
                                id = place.id,
                                name = place.name,
                                latitude = place.latitude,
                                longitude = place.longitude,
                                radiusMeters = place.radiusM,
                                isSafeZone = place.isSafeZone,
                            )
                        },
                    )
                }
            }
        }
    }
}
