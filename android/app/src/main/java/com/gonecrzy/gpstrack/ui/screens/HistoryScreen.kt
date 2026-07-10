package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.gonecrzy.gpstrack.BuildConfig
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.gonecrzy.gpstrack.ui.components.AutoRefreshEffect
import com.gonecrzy.gpstrack.ui.components.EmptyState
import com.gonecrzy.gpstrack.ui.components.ErrorState
import com.gonecrzy.gpstrack.ui.components.LoadingState
import com.gonecrzy.gpstrack.ui.components.SectionHeader
import com.gonecrzy.gpstrack.ui.components.TimelineItemRow
import com.gonecrzy.gpstrack.ui.map.HistoryRouteMap
import com.gonecrzy.gpstrack.ui.model.HistoryPeriod
import com.gonecrzy.gpstrack.ui.theme.appColors
import com.gonecrzy.gpstrack.ui.theme.spacing
import com.gonecrzy.gpstrack.ui.viewmodel.HistoryViewModel
import com.gonecrzy.gpstrack.ui.viewmodel.simpleViewModelFactory
import java.time.LocalDate

@Composable
fun HistoryScreen(
    repository: GpsTrackRepository,
    preferences: AppPreferences,
    initialMemberId: String?,
    initialPeriod: String?,
    initialDate: String?,
    onMemberSelected: (String) -> Unit,
    contentPadding: PaddingValues = PaddingValues(),
) {
    val period = remember(initialPeriod) {
        runCatching { HistoryPeriod.valueOf(initialPeriod.orEmpty()) }.getOrDefault(HistoryPeriod.DAY)
    }
    val date = remember(initialDate) {
        runCatching { LocalDate.parse(initialDate) }.getOrDefault(LocalDate.now())
    }
    val factory = remember(repository, initialMemberId, period, date) {
        simpleViewModelFactory { HistoryViewModel(repository, initialMemberId, period, date) }
    }
    val viewModel: HistoryViewModel = viewModel(factory = factory)
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val mapStyleUrl by preferences.mapStyleUrl.collectAsStateWithLifecycle(
        initialValue = BuildConfig.DEFAULT_MAP_STYLE_URL,
    )
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
            bottom = contentPadding.calculateBottomPadding() + spacing.xxLarge,
        ),
        verticalArrangement = Arrangement.spacedBy(spacing.large),
    ) {
        item {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(spacing.small),
            ) {
                Text("History", style = MaterialTheme.typography.headlineMedium)
                uiState.summaryLabel?.let {
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.appColors.textSecondary,
                    )
                }
            }
        }
        item {
            FilterRow(
                members = uiState.members.map { it.id to it.label },
                selectedMemberId = uiState.selectedMemberId,
                onMemberSelected = viewModel::selectMember,
                periods = HistoryPeriod.entries,
                selectedPeriod = uiState.period,
                onPeriodSelected = viewModel::selectPeriod,
            )
        }
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
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = { viewModel.moveDate(-dateStepFor(uiState.period)) }) {
                        Text("Previous")
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(uiState.period.name.lowercase().replaceFirstChar(Char::uppercase))
                        Text(
                            uiState.selectedDate.toString(),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.appColors.textSecondary,
                        )
                    }
                    TextButton(
                        onClick = { viewModel.moveDate(dateStepFor(uiState.period)) },
                    ) {
                        Text("Next")
                    }
                }
            }
        }
        when {
            uiState.isLoading && uiState.timeline.isEmpty() -> item {
                LoadingState(label = "Loading history")
            }

            uiState.errorMessage != null && uiState.timeline.isEmpty() -> item {
                ErrorState(
                    title = "Unable to load history.",
                    message = "Try refreshing or pick another family member.",
                    onRetry = viewModel::refresh,
                )
            }

            else -> {
                item {
                    HistoryRouteMap(
                        mapStyleUrl = mapStyleUrl,
                        model = uiState.map,
                        onMarkerSelected = viewModel::selectTimelineItem,
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 260.dp),
                    )
                }
                item {
                    SectionHeader(
                        title = if (uiState.period == HistoryPeriod.DAY) "Timeline" else "Summary",
                        subtitle = when (uiState.period) {
                            HistoryPeriod.DAY -> "Select an event to highlight it on the map."
                            HistoryPeriod.WEEK -> "Weekly stays are summarized by day and place."
                            HistoryPeriod.MONTH -> "Monthly stays are summarized by day and place."
                        },
                    )
                }
                if (uiState.timeline.isEmpty()) {
                    item {
                        EmptyState(
                            title = "No history is available.",
                            message = "Try another date range or refresh after new locations arrive.",
                            actionLabel = "Refresh",
                            onAction = viewModel::refresh,
                        )
                    }
                } else {
                    items(uiState.timeline, key = { it.id }) { item ->
                        TimelineItemRow(
                            item = item,
                            onClick = { viewModel.selectTimelineItem(item.id) },
                        )
                    }
                }
            }
        }
        val selectedMemberId = uiState.selectedMemberId
        if (selectedMemberId != null) {
            item {
                TextButton(onClick = { onMemberSelected(selectedMemberId) }) {
                    Text("Open member details")
                }
            }
        }
    }
}

@Composable
private fun FilterRow(
    members: List<Pair<String, String>>,
    selectedMemberId: String?,
    onMemberSelected: (String) -> Unit,
    periods: List<HistoryPeriod>,
    selectedPeriod: HistoryPeriod,
    onPeriodSelected: (HistoryPeriod) -> Unit,
) {
    val spacing = MaterialTheme.spacing
    Column(verticalArrangement = Arrangement.spacedBy(spacing.medium)) {
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(spacing.small),
        ) {
            members.forEach { (id, label) ->
                FilterChip(
                    selected = id == selectedMemberId,
                    onClick = { onMemberSelected(id) },
                    label = { Text(label) },
                )
            }
        }
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(spacing.small),
        ) {
            periods.forEach { period ->
                FilterChip(
                    selected = period == selectedPeriod,
                    onClick = { onPeriodSelected(period) },
                    label = { Text(period.name.lowercase().replaceFirstChar(Char::uppercase)) },
                )
            }
        }
    }
}

private fun dateStepFor(period: HistoryPeriod): Long {
    return when (period) {
        HistoryPeriod.DAY -> 1L
        HistoryPeriod.WEEK -> 7L
        HistoryPeriod.MONTH -> 30L
    }
}
