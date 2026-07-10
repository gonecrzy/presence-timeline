package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.components.AutoRefreshEffect
import com.gonecrzy.gpstrack.ui.components.EmptyState
import com.gonecrzy.gpstrack.ui.components.ErrorState
import com.gonecrzy.gpstrack.ui.components.FamilyMemberCard
import com.gonecrzy.gpstrack.ui.components.LoadingState
import com.gonecrzy.gpstrack.ui.components.PresenceStatus
import com.gonecrzy.gpstrack.ui.model.PresenceState
import com.gonecrzy.gpstrack.ui.theme.appColors
import com.gonecrzy.gpstrack.ui.theme.spacing
import com.gonecrzy.gpstrack.ui.viewmodel.FamilyViewModel
import com.gonecrzy.gpstrack.ui.viewmodel.simpleViewModelFactory

@Composable
fun MembersScreen(
    repository: GpsTrackRepository,
    onMemberSelected: (String) -> Unit,
    contentPadding: PaddingValues = PaddingValues(),
) {
    val factory = remember(repository) {
        simpleViewModelFactory { FamilyViewModel(repository) }
    }
    val viewModel: FamilyViewModel = viewModel(factory = factory)
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val spacing = MaterialTheme.spacing
    val staleCount = uiState.members.count { member ->
        member.presenceState == PresenceState.STALE || member.presenceState == PresenceState.OFFLINE
    }

    AutoRefreshEffect(onRefresh = { viewModel.refresh() })

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding(),
        contentPadding = PaddingValues(
            start = spacing.large,
            top = spacing.medium,
            end = spacing.large,
            bottom = contentPadding.calculateBottomPadding() + spacing.xxLarge,
        ),
        verticalArrangement = Arrangement.spacedBy(spacing.medium),
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(spacing.xSmall)) {
                    Text("Family", style = MaterialTheme.typography.headlineMedium)
                    Text(
                        text = "${uiState.members.size} members",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.appColors.textSecondary,
                    )
                }
                IconButton(
                    onClick = viewModel::refresh,
                ) {
                    Icon(Icons.Outlined.Refresh, contentDescription = "Refresh family locations")
                }
            }
        }
        if (staleCount > 0 && uiState.members.isNotEmpty()) {
            item {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.appColors.surfacePrimary,
                    shape = MaterialTheme.shapes.medium,
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = spacing.large, vertical = spacing.medium),
                        horizontalArrangement = Arrangement.spacedBy(spacing.small),
                    ) {
                        PresenceStatus(presenceState = PresenceState.STALE)
                        Text(
                            text = "$staleCount family locations may be outdated.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.appColors.textSecondary,
                        )
                    }
                }
            }
        }
        when {
            uiState.isLoading && uiState.members.isEmpty() -> item {
                LoadingState(label = "Loading family locations")
            }

            uiState.errorMessage != null && uiState.members.isEmpty() -> item {
                ErrorState(
                    title = "Unable to load family members.",
                    message = "Check the family configuration or refresh.",
                    onRetry = viewModel::refresh,
                )
            }

            uiState.members.isEmpty() -> item {
                EmptyState(
                    title = "No family members are available.",
                    message = "Check the family configuration or refresh.",
                    actionLabel = "Refresh",
                    onAction = viewModel::refresh,
                )
            }

            else -> {
                uiState.errorMessage?.let {
                    item {
                        ErrorState(
                            title = "Refresh incomplete",
                            message = "Showing the last known family locations.",
                            onRetry = viewModel::refresh,
                        )
                    }
                }
                items(uiState.members, key = { member -> member.id }) { member ->
                    FamilyMemberCard(
                        member = member,
                        onClick = { onMemberSelected(member.id) },
                    )
                }
            }
        }
    }
}
