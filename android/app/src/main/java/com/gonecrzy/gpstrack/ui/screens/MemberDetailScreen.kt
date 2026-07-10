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
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.components.AutoRefreshEffect
import com.gonecrzy.gpstrack.ui.components.BatteryIndicator
import com.gonecrzy.gpstrack.ui.components.EmptyState
import com.gonecrzy.gpstrack.ui.components.ErrorState
import com.gonecrzy.gpstrack.ui.components.LastUpdatedText
import com.gonecrzy.gpstrack.ui.components.LoadingState
import com.gonecrzy.gpstrack.ui.components.MemberAvatar
import com.gonecrzy.gpstrack.ui.components.PresenceStatus
import com.gonecrzy.gpstrack.ui.components.SectionHeader
import com.gonecrzy.gpstrack.ui.components.TimelineItemRow
import com.gonecrzy.gpstrack.ui.theme.appColors
import com.gonecrzy.gpstrack.ui.theme.spacing
import com.gonecrzy.gpstrack.ui.viewmodel.MemberDetailViewModel
import com.gonecrzy.gpstrack.ui.viewmodel.simpleViewModelFactory

@Composable
fun MemberDetailScreen(
    memberId: String,
    repository: GpsTrackRepository,
    onViewMap: () -> Unit,
    onViewHistory: (String) -> Unit,
) {
    val factory = remember(repository, memberId) {
        simpleViewModelFactory { MemberDetailViewModel(repository, memberId) }
    }
    val viewModel: MemberDetailViewModel = viewModel(factory = factory)
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val spacing = MaterialTheme.spacing

    AutoRefreshEffect(onRefresh = { viewModel.refresh() })

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding(),
        contentPadding = PaddingValues(
            start = spacing.large,
            top = spacing.medium,
            end = spacing.large,
            bottom = spacing.xxxLarge,
        ),
        verticalArrangement = Arrangement.spacedBy(spacing.large),
    ) {
        when {
            uiState.isLoading && uiState.member == null -> item {
                LoadingState(label = "Loading family member")
            }

            uiState.errorMessage != null && uiState.member == null -> item {
                ErrorState(
                    title = "Unable to load this family member.",
                    message = "Try refreshing or return to the family list.",
                    onRetry = viewModel::refresh,
                )
            }

            uiState.member != null -> {
                val member = requireNotNull(uiState.member)
                item {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = MaterialTheme.appColors.surfacePrimary,
                        shape = MaterialTheme.shapes.large,
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(spacing.xxLarge),
                            verticalArrangement = Arrangement.spacedBy(spacing.medium),
                        ) {
                            Row(
                                horizontalArrangement = Arrangement.spacedBy(spacing.large),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                MemberAvatar(
                                    displayName = member.displayName,
                                    initials = member.initials,
                                    photoUrl = member.photoUrl,
                                    presenceState = member.presenceState,
                                    modifier = Modifier,
                                )
                                Column(
                                    modifier = Modifier.weight(1f),
                                    verticalArrangement = Arrangement.spacedBy(spacing.xSmall),
                                ) {
                                    Text(member.displayName, style = MaterialTheme.typography.headlineMedium)
                                    Row(
                                        horizontalArrangement = Arrangement.spacedBy(spacing.small),
                                        verticalAlignment = Alignment.CenterVertically,
                                    ) {
                                        PresenceStatus(member.presenceState)
                                        member.batteryPercent?.let { BatteryIndicator(it) }
                                    }
                                }
                            }
                            Text(member.locationLabel, style = MaterialTheme.typography.titleMedium)
                            member.secondaryLocationLabel?.let {
                                Text(
                                    text = it,
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.appColors.textSecondary,
                                )
                            }
                            LastUpdatedText(member.lastUpdatedLabel)
                            member.accuracyMeters?.let {
                                Text(
                                    text = "Accuracy ${it.toInt()} m",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.appColors.textSecondary,
                                )
                            }
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                TextButton(onClick = onViewMap) {
                                    Icon(Icons.Outlined.LocationOn, contentDescription = null)
                                    Text("View on Map")
                                }
                                TextButton(onClick = { onViewHistory(member.id) }) {
                                    Icon(Icons.Outlined.Schedule, contentDescription = null)
                                    Text("View Full History")
                                }
                                TextButton(onClick = viewModel::refresh) {
                                    Icon(Icons.Outlined.Refresh, contentDescription = null)
                                    Text("Refresh")
                                }
                            }
                        }
                    }
                }
                uiState.summaryLabel?.let {
                    item {
                        SectionHeader(
                            title = "Today",
                            subtitle = it,
                        )
                    }
                }
                when {
                    uiState.timeline.isEmpty() -> item {
                        EmptyState(
                            title = "No timeline events for today.",
                            message = "This family member has not reported movement or location stays yet.",
                        )
                    }

                    else -> {
                        items(uiState.timeline, key = { it.id }) { item ->
                            TimelineItemRow(
                                item = item,
                                onClick = {},
                            )
                        }
                    }
                }
            }
        }
    }
}
