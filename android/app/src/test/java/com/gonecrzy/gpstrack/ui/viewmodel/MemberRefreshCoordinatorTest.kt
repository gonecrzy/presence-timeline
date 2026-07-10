package com.gonecrzy.gpstrack.ui.viewmodel

import com.gonecrzy.gpstrack.data.model.DeviceSummary
import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.ui.model.PresenceState
import java.time.Instant
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MemberRefreshCoordinatorTest {
    private val now: Instant = Instant.parse("2026-07-10T20:00:00Z")

    @Test
    fun `keeps cached members and clears blocking error when refresh fails`() = runBlocking {
        val coordinator = MemberRefreshCoordinator(nowProvider = { now })
        val members = listOf(
            memberSummary(
                id = "member-1",
                displayName = "Kristi",
                currentLocationLabel = "Near Broad Street, King Street District",
                lastSeenAt = "2026-07-10T19:20:00Z",
            ),
        )

        val result = coordinator.load(
            refreshMembers = { error("timeout") },
            currentMembers = { members },
            loadLatestLocation = { memberId ->
                LocationPoint(
                    memberId = memberId,
                    observedAt = "2026-07-10T19:58:00Z",
                    latitude = 37.7749,
                    longitude = -122.4194,
                    accuracyM = 12.0,
                    batteryLevel = 82,
                    sourceEntityId = "device_tracker.kristi_phone",
                )
            },
            emptyStateErrorMessage = "Unable to refresh family locations right now.",
        )

        assertNull(result.errorMessage)
        assertEquals(1, result.members.size)
        assertEquals(82, result.members.first().batteryPercent)
        assertEquals(PresenceState.LIVE, result.members.first().presenceState)
    }

    @Test
    fun `returns blocking error when refresh fails and no cached members exist`() = runBlocking {
        val coordinator = MemberRefreshCoordinator(nowProvider = { now })

        val result = coordinator.load(
            refreshMembers = { error("timeout") },
            currentMembers = { emptyList() },
            loadLatestLocation = { error("should not load locations without members") },
            emptyStateErrorMessage = "Unable to refresh family locations right now.",
        )

        assertEquals("Unable to refresh family locations right now.", result.errorMessage)
        assertEquals(emptyList<com.gonecrzy.gpstrack.ui.model.FamilyMemberUiModel>(), result.members)
    }

    private fun memberSummary(
        id: String,
        displayName: String,
        currentLocationLabel: String?,
        lastSeenAt: String?,
    ) = MemberSummary(
        id = id,
        displayName = displayName,
        isChild = false,
        lastSeenAt = lastSeenAt,
        currentLocationLabel = currentLocationLabel,
        devices = listOf(
            DeviceSummary(
                id = "$id-device",
                provider = "home_assistant",
                externalId = "$id-phone",
                label = "$displayName Phone",
                ignored = false,
                lastSeenAt = lastSeenAt,
            ),
        ),
    )
}
