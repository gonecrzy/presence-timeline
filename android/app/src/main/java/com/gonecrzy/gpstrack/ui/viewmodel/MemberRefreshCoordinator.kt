package com.gonecrzy.gpstrack.ui.viewmodel

import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.ui.model.FamilyMemberUiModel
import com.gonecrzy.gpstrack.ui.model.toFamilyMemberUiModel
import java.time.Instant
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope

data class MemberRefreshResult(
    val members: List<FamilyMemberUiModel>,
    val errorMessage: String?,
)

class MemberRefreshCoordinator(
    private val nowProvider: () -> Instant = { Instant.now() },
) {
    suspend fun load(
        refreshMembers: suspend () -> Unit,
        currentMembers: suspend () -> List<MemberSummary>,
        loadLatestLocation: suspend (String) -> LocationPoint?,
        emptyStateErrorMessage: String,
    ): MemberRefreshResult {
        val refreshFailed = runCatching { refreshMembers() }.isFailure
        val members = currentMembers()
        if (members.isEmpty()) {
            return MemberRefreshResult(
                members = emptyList(),
                errorMessage = emptyStateErrorMessage.takeIf { refreshFailed },
            )
        }

        return MemberRefreshResult(
            members = mapMembers(members, loadLatestLocation),
            errorMessage = null,
        )
    }

    suspend fun mapMembers(
        members: List<MemberSummary>,
        loadLatestLocation: suspend (String) -> LocationPoint?,
    ): List<FamilyMemberUiModel> {
        if (members.isEmpty()) {
            return emptyList()
        }

        val latestLocations = coroutineScope {
            members.map { member ->
                async {
                    member.id to runCatching { loadLatestLocation(member.id) }.getOrNull()
                }
            }.awaitAll().toMap()
        }
        val now = nowProvider()
        return members.map { member ->
            member.toFamilyMemberUiModel(
                latestLocation = latestLocations[member.id],
                now = now,
            )
        }
    }
}
