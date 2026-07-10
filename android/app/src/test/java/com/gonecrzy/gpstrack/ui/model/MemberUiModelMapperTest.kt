package com.gonecrzy.gpstrack.ui.model

import com.gonecrzy.gpstrack.data.model.DeviceSummary
import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.MemberSummary
import java.time.Instant
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MemberUiModelMapperTest {
    private val now: Instant = Instant.parse("2026-07-10T20:00:00Z")

    @Test
    fun `maps recent member snapshot to live ui model`() {
        val member = memberSummary(
            displayName = "Kristi Lane",
            isChild = false,
            lastSeenAt = "2026-07-10T19:58:00Z",
            currentLocationLabel = "Near Broad Street, King Street District",
        )
        val latestLocation = latestLocation(
            observedAt = "2026-07-10T19:58:00Z",
            batteryLevel = 82,
            accuracyM = 14.0,
        )

        val uiModel = member.toFamilyMemberUiModel(
            latestLocation = latestLocation,
            now = now,
        )

        assertEquals(PresenceState.LIVE, uiModel.presenceState)
        assertEquals("Kristi Lane", uiModel.displayName)
        assertEquals("KL", uiModel.initials)
        assertEquals("Near Broad Street", uiModel.locationLabel)
        assertEquals("King Street District", uiModel.secondaryLocationLabel)
        assertEquals("Updated 2 min ago", uiModel.lastUpdatedLabel)
        assertEquals(82, uiModel.batteryPercent)
        assertEquals(37.7749, uiModel.latitude)
        assertEquals(-122.4194, uiModel.longitude)
        assertEquals(14.0, uiModel.accuracyMeters)
    }

    @Test
    fun `maps older but still recent member snapshot to live ui model`() {
        val member = memberSummary(
            displayName = "Riley Stone",
            isChild = true,
            lastSeenAt = "2026-07-10T19:48:00Z",
            currentLocationLabel = "School",
        )

        val uiModel = member.toFamilyMemberUiModel(
            latestLocation = latestLocation(observedAt = "2026-07-10T19:48:00Z"),
            now = now,
        )

        assertEquals(PresenceState.LIVE, uiModel.presenceState)
        assertEquals(MemberRole.CHILD, uiModel.role)
        assertEquals("School", uiModel.locationLabel)
        assertNull(uiModel.secondaryLocationLabel)
        assertEquals("Updated 12 min ago", uiModel.lastUpdatedLabel)
    }

    @Test
    fun `maps moderately old member snapshot to stale ui model`() {
        val member = memberSummary(
            displayName = "Mason Lee",
            isChild = true,
            lastSeenAt = "2026-07-10T18:45:00Z",
            currentLocationLabel = null,
        )

        val uiModel = member.toFamilyMemberUiModel(
            latestLocation = null,
            now = now,
        )

        assertEquals(PresenceState.STALE, uiModel.presenceState)
        assertEquals("Location unavailable", uiModel.locationLabel)
        assertEquals("Updated 1 hr 15 min ago", uiModel.lastUpdatedLabel)
    }

    @Test
    fun `maps very old member snapshot to offline ui model`() {
        val member = memberSummary(
            displayName = "Mason Lee",
            isChild = true,
            lastSeenAt = "2026-07-09T20:14:00Z",
            currentLocationLabel = null,
        )

        val uiModel = member.toFamilyMemberUiModel(
            latestLocation = null,
            now = now,
        )

        assertEquals(PresenceState.OFFLINE, uiModel.presenceState)
        assertEquals("Location unavailable", uiModel.locationLabel)
        assertEquals("Last seen 07/09/26 20:14", uiModel.lastUpdatedLabel)
    }

    private fun memberSummary(
        displayName: String,
        isChild: Boolean,
        lastSeenAt: String?,
        currentLocationLabel: String?,
    ) = MemberSummary(
        id = "member-1",
        displayName = displayName,
        isChild = isChild,
        lastSeenAt = lastSeenAt,
        currentLocationLabel = currentLocationLabel,
        devices = listOf(
            DeviceSummary(
                id = "device-1",
                provider = "ha",
                externalId = "phone",
                label = "Phone",
                ignored = false,
                lastSeenAt = lastSeenAt,
            ),
        ),
    )

    private fun latestLocation(
        observedAt: String,
        batteryLevel: Int? = null,
        accuracyM: Double? = null,
    ) = LocationPoint(
        memberId = "member-1",
        observedAt = observedAt,
        latitude = 37.7749,
        longitude = -122.4194,
        accuracyM = accuracyM,
        batteryLevel = batteryLevel,
        sourceEntityId = null,
    )
}
