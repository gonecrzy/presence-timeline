package com.gonecrzy.gpstrack.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.gonecrzy.gpstrack.data.model.DailySummary
import com.gonecrzy.gpstrack.data.model.DeviceSummary
import com.gonecrzy.gpstrack.data.model.LocationStop
import com.gonecrzy.gpstrack.data.model.TimelineItem
import com.gonecrzy.gpstrack.data.model.TripRoute
import com.gonecrzy.gpstrack.data.model.TripSummary
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import com.gonecrzy.gpstrack.ui.format.formatDisplayDate
import com.gonecrzy.gpstrack.ui.format.formatDistanceImperial
import com.gonecrzy.gpstrack.ui.format.formatDurationSeconds
import com.gonecrzy.gpstrack.ui.format.formatHistoryDateTime
import com.gonecrzy.gpstrack.ui.format.formatHistoryDateTimeRange
import com.gonecrzy.gpstrack.ui.format.formatPhoneDateTime
import com.gonecrzy.gpstrack.ui.format.formatSafetyEventSummary
import com.gonecrzy.gpstrack.ui.map.TripRoutePreview
import kotlinx.coroutines.launch

@Composable
fun MemberDetailScreen(
    memberId: String,
    repository: GpsTrackRepository,
) {
    val scope = rememberCoroutineScope()
    val members by repository.observeMembers().collectAsState(initial = emptyList())
    val member = members.firstOrNull { it.id == memberId }
    val today = LocalDate.now(ZoneOffset.UTC)
    val earliestDate = remember(today) { today.minusDays(6) }
    var selectedDate by rememberSaveable { mutableStateOf(today.toString()) }
    val activeDate = remember(selectedDate) { LocalDate.parse(selectedDate) }
    val timelineRangeStart = remember(activeDate) {
        activeDate.atStartOfDay(ZoneOffset.UTC).toInstant().toString()
    }
    val timelineRangeEnd = remember(activeDate) {
        activeDate.plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant().toString()
    }
    var tripPreview by remember { mutableStateOf<TripPreviewState?>(null) }
    var selectedStopIndex by remember { mutableStateOf<Int?>(null) }
    var editingProfile by remember { mutableStateOf(false) }
    var editingDevice by remember { mutableStateOf<DeviceSummary?>(null) }
    var isSaving by remember { mutableStateOf(false) }
    var feedbackMessage by remember { mutableStateOf<String?>(null) }

    val trips by produceState(initialValue = emptyList<TripSummary>(), key1 = memberId, key2 = selectedDate) {
        value = runCatching { repository.loadTrips(memberId, activeDate.toString()) }.getOrDefault(emptyList())
    }
    val summary by produceState<DailySummary?>(initialValue = null, key1 = memberId, key2 = selectedDate) {
        value = runCatching { repository.loadDailySummary(memberId, activeDate.toString()) }.getOrNull()
    }
    val timeline by produceState(initialValue = emptyList<TimelineItem>(), key1 = memberId, key2 = selectedDate) {
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

    tripPreview?.let { preview ->
        val route = preview.route
        val selectedStop = selectedStopIndex?.let(preview.stops::getOrNull)
        AlertDialog(
            onDismissRequest = {
                tripPreview = null
                selectedStopIndex = null
            },
            confirmButton = {
                Button(onClick = {
                    tripPreview = null
                    selectedStopIndex = null
                }) {
                    Text("Close")
                }
            },
            title = { Text("Trip Route") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Travelled ${formatDistanceImperial(route.distanceM)}")
                    Text("Started: ${formatPhoneDateTime(route.startedAt)}")
                    Text("Ended: ${route.endedAt?.let(::formatPhoneDateTime) ?: "In progress"}")
                    TripRoutePreview(
                        route = route,
                        stops = preview.stops,
                        onStopSelected = { index -> selectedStopIndex = index },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(220.dp),
                    )
                    when {
                        preview.stops.isEmpty() -> Text(
                            "No stop waypoints were found for this trip window.",
                            style = MaterialTheme.typography.bodySmall,
                        )

                        selectedStop != null -> {
                            Text(selectedStop.label ?: formatTimelineCoordinates(selectedStop), style = MaterialTheme.typography.bodyMedium)
                            Text(
                                formatHistoryDateTimeRange(selectedStop.startedAt, selectedStop.endedAt),
                                style = MaterialTheme.typography.bodySmall,
                            )
                            Text(
                                "Stayed for ${formatDurationSeconds(selectedStop.durationSeconds)}",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }

                        else -> Text(
                            "Tap a waypoint on the map to view stop details.",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
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
                    member?.currentLocationLabel?.let { locationLabel ->
                        Text(locationLabel, style = MaterialTheme.typography.bodyMedium)
                    }
                    Text("Last Update: ${formatPhoneDateTime(member?.lastSeenAt)}", style = MaterialTheme.typography.bodySmall)
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
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            TextButton(
                                onClick = {
                                    if (activeDate.isAfter(earliestDate)) {
                                        selectedDate = activeDate.minusDays(1).toString()
                                    }
                                },
                                enabled = activeDate.isAfter(earliestDate),
                            ) {
                                Text("Previous")
                            }
                            Text(
                                if (activeDate == today) "Today · ${formatDisplayDate(activeDate)}" else formatDisplayDate(activeDate),
                                style = MaterialTheme.typography.titleMedium,
                            )
                            TextButton(
                                onClick = {
                                    if (activeDate.isBefore(today)) {
                                        selectedDate = activeDate.plusDays(1).toString()
                                    }
                                },
                                enabled = activeDate.isBefore(today),
                            ) {
                                Text("Next")
                            }
                        }
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            Text("Trips: ${daySummary.tripCount}")
                            Text("Distance: ${formatDistanceImperial(daySummary.totalDistanceM)}")
                        }
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
                        Text("Last Update: ${formatPhoneDateTime(device.lastSeenAt)}", style = MaterialTheme.typography.bodySmall)
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
                            selectedStopIndex = null
                            tripPreview = runCatching {
                                val route = repository.loadTripRoute(memberId, trip.id)
                                val routeEnd = route.endedAt ?: route.startedAt
                                val stops = repository.loadMemberStops(memberId, route.startedAt, routeEnd)
                                    .filter { stop -> stopOverlapsRouteWindow(stop, route.startedAt, routeEnd) }
                                TripPreviewState(route = route, stops = stops)
                            }.getOrNull()
                        }
                    },
                ) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("Travelled ${formatDistanceImperial(trip.distanceM)}", style = MaterialTheme.typography.titleMedium)
                        Text(formatHistoryDateTimeRange(trip.startedAt, trip.endedAt), style = MaterialTheme.typography.bodySmall)
                        Text("Tap for route preview", style = MaterialTheme.typography.labelSmall)
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
                    formatTimelineWhen(item)?.let { line ->
                        Text(line, style = MaterialTheme.typography.bodySmall)
                    }
                    when (item.kind) {
                        "trip" -> Text("Travelled ${formatDistanceImperial(item.distanceM)}")
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
                        "safety_event" -> Unit
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
        "safety_event" -> formatSafetyEventSummary(
            eventType = item.eventType,
            placeName = item.payload?.get("place_name") as? String,
            observedAt = item.observedAt,
        )
        "trip" -> "Trip"
        else -> item.kind.replace('_', ' ')
    }
}

private fun formatTimelineWhen(item: TimelineItem): String? {
    return when (item.kind) {
        "location_stay" -> {
            val start = item.startedAt ?: item.observedAt
            val end = item.endedAt
            if (item.isCurrent == true) {
                "Since ${formatHistoryDateTime(start)}"
            } else {
                formatHistoryDateTimeRange(start, end)
            }
        }
        "trip" -> {
            val start = item.startedAt ?: item.observedAt
            val end = item.endedAt
            formatHistoryDateTimeRange(start, end)
        }
        "safety_event" -> null
        else -> formatHistoryDateTime(item.observedAt)
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

private fun formatTimelineCoordinates(stop: LocationStop): String {
    return "${"%.4f".format(stop.latitude)}, ${"%.4f".format(stop.longitude)}"
}

private fun stopOverlapsRouteWindow(
    stop: LocationStop,
    routeStartedAt: String,
    routeEndedAt: String,
): Boolean {
    val stopStartedAt = runCatching { Instant.parse(stop.startedAt) }.getOrNull() ?: return false
    val stopEndedAt = runCatching { Instant.parse(stop.endedAt) }.getOrNull() ?: return false
    val tripStartedAt = runCatching { Instant.parse(routeStartedAt) }.getOrNull() ?: return false
    val tripEndedAt = runCatching { Instant.parse(routeEndedAt) }.getOrNull() ?: return false
    return stopEndedAt >= tripStartedAt && stopStartedAt <= tripEndedAt
}

private data class TripPreviewState(
    val route: TripRoute,
    val stops: List<LocationStop>,
)

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
