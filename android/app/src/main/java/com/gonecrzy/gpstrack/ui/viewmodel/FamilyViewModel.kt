package com.gonecrzy.gpstrack.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.model.FamilyScreenUiState
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class FamilyViewModel(
    private val repository: GpsTrackRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(FamilyScreenUiState())
    val uiState = _uiState.asStateFlow()
    private var refreshJob: Job? = null
    private val refreshCoordinator = MemberRefreshCoordinator()

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
                    isLoading = state.members.isEmpty(),
                    isRefreshing = true,
                    errorMessage = null,
                )
            }
            val result = refreshCoordinator.load(
                refreshMembers = repository::refreshMembers,
                currentMembers = repository::currentMembers,
                loadLatestLocation = { memberId -> repository.loadLatestLocation(memberId) },
                emptyStateErrorMessage = "Unable to refresh family locations right now.",
            )
            _uiState.update { state ->
                state.copy(
                    isLoading = false,
                    isRefreshing = false,
                    members = result.members,
                    errorMessage = result.errorMessage,
                )
            }
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
                    state.copy(
                        isLoading = false,
                        isRefreshing = false,
                        members = uiMembers,
                        errorMessage = state.errorMessage.takeUnless { uiMembers.isNotEmpty() },
                    )
                }
            }
        }
    }
}
