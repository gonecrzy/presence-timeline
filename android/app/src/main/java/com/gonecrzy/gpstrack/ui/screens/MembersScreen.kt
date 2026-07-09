package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.ui.format.formatPhoneDateTime

@Composable
fun MembersScreen(
    repository: GpsTrackRepository,
    onMemberSelected: (String) -> Unit,
) {
    val members by repository.observeMembers().collectAsState(initial = emptyList())

    LaunchedEffect(Unit) {
        runCatching { repository.refreshMembers() }
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Family Tracking", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        "Parents-only local client for live location, trips, and places.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
        items(members, key = { it.id }) { member ->
            MemberCard(member = member, onClick = { onMemberSelected(member.id) })
        }
    }
}

@Composable
private fun MemberCard(
    member: MemberSummary,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(member.displayName, style = MaterialTheme.typography.titleLarge)
            Text(
                if (member.isChild) "Child profile" else "Parent profile",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Text(
                "Last Update: ${formatPhoneDateTime(member.lastSeenAt)}",
                style = MaterialTheme.typography.bodyMedium,
            )
            member.currentLocationLabel?.let { currentLocation ->
                Text(
                    "Current: $currentLocation",
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}
