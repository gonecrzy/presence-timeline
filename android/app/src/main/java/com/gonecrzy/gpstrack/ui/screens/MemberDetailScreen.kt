package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import com.gonecrzy.gpstrack.data.model.DeviceSummary
import com.gonecrzy.gpstrack.data.model.TimelineItem
import com.gonecrzy.gpstrack.data.model.TripRoute
import com.gonecrzy.gpstrack.data.model.TripSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.ZonedDateTime
import java.time.format.DateTimeFormatter
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
    var editingProfile by remember { mutableStateOf(false) }
    var editingDevice by remember { mutableStateOf<DeviceSummary?>(null) }
    var isSaving by remember { mutableStateOf(false) }
    var feedbackMessage by remember { mutableStateOf<String?>(null) }

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

    if (editingProfile && member != null) {
        MemberEditorDialog(
            initialName = member.displayName,
            initialIsChild = member.isChild,
            onDismiss = { editingProfile = false },
            onSubmit = { displayName, isChild ->
                scope.launch {
                    isSaving = true
                    feedbackMessage = null
                    runCatching {
                        repository.updateMember(memberId, displayName, isChild)
                        repository.refreshMembers()
                    }.fold(
                        onSuccess = {
                            editingProfile = false
                            feedbackMessage = "Profile updated"
                        },
                        onFailure = {
                            feedbackMessage = it.message ?: "Failed to update profile"
                        },
                    )
                    isSaving = false
                }
            },
        )
    }

    editingDevice?.let { device ->
        DeviceEditorDialog(
            device = device,
            onDismiss = { editingDevice = null },
            onSubmit = { label, ignored ->
                scope.launch {
                    isSaving = true
                    feedbackMessage = null
                    runCatching {
                        repository.updateDevice(memberId, device.id, label, ignored)
                        repository.refreshMembers()
                    }.fold(
                        onSuccess = {
                            editingDevice = null
                            feedbackMessage = "Device updated"
                        },
                        onFailure = {
                            feedbackMessage = it.message ?: "Failed to update device"
                        },
                    )
                    isSaving = false
                }
            },
        )
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
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = { editingProfile = true },
                            enabled = member != null && !isSaving,
                        ) {
                            Text(if (isSaving) "Saving..." else "Edit Profile")
                        }
                    }
                }
            }
        }
        feedbackMessage?.let { message ->
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = message,
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.primary,
                    )
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
        member?.devices?.takeIf { it.isNotEmpty() }?.let { devices ->
            item {
                Text("Devices", style = MaterialTheme.typography.titleMedium)
            }
            items(devices, key = { it.id }) { device ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(device.label ?: device.externalId, style = MaterialTheme.typography.titleSmall)
                        Text("Provider: ${device.provider}", style = MaterialTheme.typography.bodySmall)
                        Text(
                            if (device.ignored) "Ignored for tracking" else "Tracked in family view",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        Text(device.lastSeenAt ?: "No recent device update", style = MaterialTheme.typography.bodySmall)
                        TextButton(
                            onClick = { editingDevice = device },
                            enabled = !isSaving,
                        ) {
                            Text("Edit Device")
                        }
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
        itemsIndexed(timeline, key = { index, item -> "${item.kind}-${item.observedAt}-${item.tripId ?: ""}-$index" }) { _, item ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(formatTimelineTitle(item), style = MaterialTheme.typography.titleSmall)
                    Text(formatTimelineWhen(item), style = MaterialTheme.typography.bodySmall)
                    when (item.kind) {
                        "trip" -> Text("${item.distanceM?.toInt() ?: 0} m over ${item.pointCount ?: 0} points")
                        "location_stay" -> {
                            Text(
                                item.label ?: formatTimelineCoordinates(item),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Text(
                                formatStaySummary(item),
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                        "safety_event" -> Text(item.eventType ?: "Safety event")
                        else -> Text(formatTimelineCoordinates(item))
                    }
                }
            }
        }
    }
}

private fun formatTimelineTitle(item: TimelineItem): String {
    return when (item.kind) {
        "location_stay" -> if (item.isCurrent == true) "Current location" else "Location stay"
        "safety_event" -> "Safety event"
        "trip" -> "Trip"
        else -> item.kind.replace('_', ' ')
    }
}

private fun formatTimelineWhen(item: TimelineItem): String {
    return when (item.kind) {
        "location_stay" -> {
            val start = item.startedAt ?: item.observedAt
            val end = item.endedAt
            if (item.isCurrent == true) {
                "Since ${formatTimelineTimestamp(start)}"
            } else {
                "${formatTimelineTimestamp(start)} to ${formatTimelineTimestamp(end)}"
            }
        }
        "trip" -> {
            val start = item.startedAt ?: item.observedAt
            val end = item.endedAt
            "${formatTimelineTimestamp(start)} to ${formatTimelineTimestamp(end)}"
        }
        else -> formatTimelineTimestamp(item.observedAt)
    }
}

private fun formatStaySummary(item: TimelineItem): String {
    val duration = item.durationSeconds?.let(::formatDurationSeconds) ?: "a short time"
    return if (item.isCurrent == true) {
        "At this location for $duration"
    } else {
        "Stayed for $duration"
    }
}

private fun formatTimelineCoordinates(item: TimelineItem): String {
    val latitude = item.latitude ?: 0.0
    val longitude = item.longitude ?: 0.0
    return "${"%.4f".format(latitude)}, ${"%.4f".format(longitude)}"
}

private fun formatTimelineTimestamp(value: String?): String {
    if (value == null) {
        return "Unknown time"
    }
    return runCatching {
        TimelineFormatter.format(Instant.parse(value))
    }.getOrDefault(value)
}

private fun formatDurationSeconds(durationSeconds: Int): String {
    val duration = Duration.ofSeconds(durationSeconds.toLong())
    val hours = duration.toHours()
    val minutes = duration.minusHours(hours).toMinutes()

    return when {
        hours > 0 && minutes > 0 -> "${hours}h ${minutes}m"
        hours > 0 -> "${hours}h"
        minutes > 0 -> "${minutes}m"
        else -> "${durationSeconds}s"
    }
}

private object TimelineFormatter {
    private val formatter = DateTimeFormatter.ofPattern("MMM d, h:mm a")
        .withZone(ZoneId.systemDefault())

    fun format(value: Instant): String = formatter.format(value)
}

@Composable
private fun MemberEditorDialog(
    initialName: String,
    initialIsChild: Boolean,
    onDismiss: () -> Unit,
    onSubmit: (String, Boolean) -> Unit,
) {
    var displayName by remember(initialName) { mutableStateOf(initialName) }
    var isChild by remember(initialIsChild) { mutableStateOf(initialIsChild) }

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            Button(
                onClick = { onSubmit(displayName.trim(), isChild) },
                enabled = displayName.isNotBlank(),
            ) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        title = { Text("Edit Profile") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                OutlinedTextField(
                    value = displayName,
                    onValueChange = { displayName = it },
                    label = { Text("Display name") },
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        text = if (isChild) "Child profile" else "Parent profile",
                        modifier = Modifier.weight(1f),
                    )
                    Switch(checked = isChild, onCheckedChange = { isChild = it })
                }
            }
        },
    )
}

@Composable
private fun DeviceEditorDialog(
    device: DeviceSummary,
    onDismiss: () -> Unit,
    onSubmit: (String?, Boolean) -> Unit,
) {
    var label by remember(device.id, device.label) { mutableStateOf(device.label.orEmpty()) }
    var ignored by remember(device.id, device.ignored) { mutableStateOf(device.ignored) }

    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            Button(
                onClick = { onSubmit(label.trim().ifBlank { null }, ignored) },
            ) {
                Text("Save")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        title = { Text("Edit Device") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(device.externalId, style = MaterialTheme.typography.bodySmall)
                OutlinedTextField(
                    value = label,
                    onValueChange = { label = it },
                    label = { Text("Device label") },
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        text = if (ignored) "Ignored in family tracking" else "Shown in family tracking",
                        modifier = Modifier.weight(1f),
                    )
                    Switch(checked = ignored, onCheckedChange = { ignored = it })
                }
            }
        },
    )
}
