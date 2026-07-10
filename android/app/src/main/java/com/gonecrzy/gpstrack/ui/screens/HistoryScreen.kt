package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.gonecrzy.gpstrack.ui.components.EmptyState
import com.gonecrzy.gpstrack.ui.theme.spacing

@Composable
fun HistoryScreen(
    contentPadding: PaddingValues = PaddingValues(),
) {
    val spacing = MaterialTheme.spacing
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
                verticalArrangement = Arrangement.spacedBy(spacing.xSmall),
            ) {
                Text("History", style = MaterialTheme.typography.headlineMedium)
                Text(
                    text = "Route playback and timeline filtering are coming next.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        item {
            EmptyState(
                title = "History is being redesigned.",
                message = "Use a family member's detail screen for today's timeline until the dedicated history view is finished.",
            )
        }
    }
}
