package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.clickable
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gonecrzy.gpstrack.data.model.DailySummary
import com.gonecrzy.gpstrack.data.model.TimelineItem
import com.gonecrzy.gpstrack.data.model.TripRoute
import com.gonecrzy.gpstrack.data.model.TripSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.ZonedDateTime
import kotlinx.coroutines.launch

@Composable
fun MemberDetailScreen(
    memberId: String,
    repository: GpsTrackRepository,
) {
    val scope = rememberCoroutineScope()
    val members by repository.observeMembers().collectAsState(initial = emptyList())
    val member = members.firstOrNull { it.id == memberId }
    val today = LocalDate.now(ZoneOffset.UTC).toString()
    val timelineRangeStart = ZonedDateTime.now(ZoneOffset.UTC).minusHours(6).toString()
    val timelineRangeEnd = ZonedDateTime.now(ZoneOffset.UTC).toString()
    var tripRoute by remember { mutableStateOf<TripRoute?>(null) }

    val trips by produceState(initialValue = emptyList<TripSummary>(), key1 = memberId) {
        value = runCatching { repository.loadTrips(memberId, today) }.getOrDefault(emptyList())
    }
    val summary by produceState<DailySummary?>(initialValue = null, key1 = memberId) {
        value = runCatching { repository.loadDailySummary(memberId, today) }.getOrNull()
    }
    val timeline by produceState(initialValue = emptyList<TimelineItem>(), key1 = memberId) {
        value = runCatching {
            repository.loadTimeline(memberId, timelineRangeStart, timelineRangeEnd)
        }.getOrDefault(emptyList())
    }

    LaunchedEffect(memberId) {
        runCatching { repository.refreshMembers() }
    }

    tripRoute?.let { route ->
        AlertDialog(
            onDismissRequest = { tripRoute = null },
            confirmButton = {
                Button(onClick = { tripRoute = null }) {
                    Text("Close")
                }
            },
            title = { Text("Trip Route") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("${route.distanceM.toInt()} m across ${route.pointCount} points")
                    Text("Started: ${route.startedAt}")
                    Text("Ended: ${route.endedAt ?: "In progress"}")
                }
            },
        )
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(member?.displayName ?: "Member", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        if (member?.isChild == true) "Child profile" else "Parent profile",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Text(member?.lastSeenAt ?: "No recent update", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        summary?.let { daySummary ->
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.padding(16.dp).fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text("Trips today: ${daySummary.tripCount}")
                        Text("Distance: ${daySummary.totalDistanceM.toInt()} m")
                    }
                }
            }
        }
        if (trips.isNotEmpty()) {
            item {
                Text("Trips", style = MaterialTheme.typography.titleMedium)
            }
            items(trips, key = { it.id }) { trip ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 4.dp)
                        .clickable {
                        scope.launch {
                            tripRoute = runCatching {
                                repository.loadTripRoute(memberId, trip.id)
                            }.getOrNull()
                        }
                    },
                ) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("${trip.distanceM.toInt()} m", style = MaterialTheme.typography.titleMedium)
                        Text("${trip.startedAt} -> ${trip.endedAt ?: "In progress"}", style = MaterialTheme.typography.bodySmall)
                        Text("Tap for route payload", style = MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
        item {
            Text("Timeline", style = MaterialTheme.typography.titleMedium)
        }
        items(timeline, key = { "${it.kind}-${it.observedAt}-${it.tripId ?: ""}" }) { item ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(item.kind.replace('_', ' '), style = MaterialTheme.typography.titleSmall)
                    Text(item.observedAt, style = MaterialTheme.typography.bodySmall)
                    when (item.kind) {
                        "trip" -> Text("${item.distanceM?.toInt() ?: 0} m over ${item.pointCount ?: 0} points")
                        "safety_event" -> Text(item.eventType ?: "Safety event")
                        else -> Text("${item.latitude ?: 0.0}, ${item.longitude ?: 0.0}")
                    }
                }
            }
        }
    }
}
