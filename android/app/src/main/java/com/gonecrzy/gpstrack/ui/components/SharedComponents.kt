package com.gonecrzy.gpstrack.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.KeyboardArrowRight
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.PersonOutline
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalInspectionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.gonecrzy.gpstrack.ui.model.FamilyMemberUiModel
import com.gonecrzy.gpstrack.ui.model.MemberRole
import com.gonecrzy.gpstrack.ui.model.PresenceState
import com.gonecrzy.gpstrack.ui.theme.GpsTrackTheme
import com.gonecrzy.gpstrack.ui.theme.appColors
import com.gonecrzy.gpstrack.ui.theme.spacing

@Composable
fun FamilyMemberCard(
    member: FamilyMemberUiModel,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = MaterialTheme.spacing
    ElevatedCard(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .semantics {
                contentDescription = buildString {
                    append(member.displayName)
                    append(", ")
                    append(member.locationLabel)
                    append(", ")
                    append(member.lastUpdatedLabel)
                }
            },
        colors = CardDefaults.elevatedCardColors(
            containerColor = MaterialTheme.appColors.surfaceElevated,
            contentColor = MaterialTheme.appColors.textPrimary,
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(spacing.large),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            MemberAvatar(
                displayName = member.displayName,
                initials = member.initials,
                photoUrl = member.photoUrl,
                presenceState = member.presenceState,
            )
            Spacer(modifier = Modifier.width(spacing.large))
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(spacing.xSmall),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(spacing.small),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = member.displayName,
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.weight(1f),
                    )
                    PresenceStatus(presenceState = member.presenceState)
                }
                if (member.role == MemberRole.CHILD) {
                    RolePill(text = "Child")
                }
                Text(
                    text = member.locationLabel,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.appColors.textPrimary,
                )
                member.secondaryLocationLabel?.let { secondaryLabel ->
                    Text(
                        text = secondaryLabel,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.appColors.textSecondary,
                    )
                }
                Row(
                    horizontalArrangement = Arrangement.spacedBy(spacing.small),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    LastUpdatedText(text = member.lastUpdatedLabel)
                    member.batteryPercent?.let { batteryPercent ->
                        BatteryIndicator(batteryPercent = batteryPercent)
                    }
                }
            }
            Spacer(modifier = Modifier.width(spacing.small))
            Icon(
                imageVector = Icons.AutoMirrored.Outlined.KeyboardArrowRight,
                contentDescription = null,
                tint = MaterialTheme.appColors.textSecondary,
            )
        }
    }
}

@Composable
fun MemberAvatar(
    displayName: String,
    initials: String,
    photoUrl: String?,
    presenceState: PresenceState,
    modifier: Modifier = Modifier,
) {
    val colors = MaterialTheme.appColors
    val borderColor = when (presenceState) {
        PresenceState.LIVE -> colors.accentPrimary
        PresenceState.STALE -> colors.warning
        PresenceState.OFFLINE -> colors.divider
        PresenceState.UNKNOWN -> colors.textSecondary
    }
    val inspectionMode = LocalInspectionMode.current
    Box(
        modifier = modifier
            .size(52.dp)
            .clip(CircleShape)
            .background(colors.backgroundSecondary)
            .border(width = 2.dp, color = borderColor, shape = CircleShape),
        contentAlignment = Alignment.Center,
    ) {
        if (!photoUrl.isNullOrBlank() && !inspectionMode) {
            Icon(
                imageVector = Icons.Outlined.PersonOutline,
                contentDescription = displayName,
                tint = colors.textSecondary,
            )
        } else {
            Text(
                text = initials,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.SemiBold,
            )
        }
    }
}

@Composable
fun PresenceStatus(
    presenceState: PresenceState,
    modifier: Modifier = Modifier,
) {
    val colors = MaterialTheme.appColors
    val (label, color) = when (presenceState) {
        PresenceState.LIVE -> "Live" to colors.success
        PresenceState.STALE -> "Stale" to colors.warning
        PresenceState.OFFLINE -> "Offline" to colors.error
        PresenceState.UNKNOWN -> "Unknown" to colors.textSecondary
    }
    Surface(
        modifier = modifier.heightIn(min = 28.dp),
        shape = CircleShape,
        color = color.copy(alpha = 0.14f),
        contentColor = color,
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(color),
            )
            Text(text = label, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
fun LastUpdatedText(
    text: String,
    modifier: Modifier = Modifier,
) {
    Text(
        text = text,
        modifier = modifier,
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.appColors.textSecondary,
    )
}

@Composable
fun BatteryIndicator(
    batteryPercent: Int,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.heightIn(min = 24.dp),
        shape = CircleShape,
        color = MaterialTheme.appColors.backgroundSecondary,
        contentColor = MaterialTheme.appColors.textSecondary,
    ) {
        Text(
            text = "$batteryPercent%",
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelMedium,
        )
    }
}

@Composable
fun MapControlButton(
    icon: @Composable () -> Unit,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = CircleShape,
        color = MaterialTheme.appColors.surfacePrimary.copy(alpha = 0.94f),
        shadowElevation = 8.dp,
    ) {
        IconButton(
            modifier = Modifier.semantics { this.contentDescription = contentDescription },
            onClick = onClick,
        ) {
            icon()
        }
    }
}

@Composable
fun MemberPreviewSheet(
    member: FamilyMemberUiModel,
    onViewToday: () -> Unit,
    onOpenDetails: () -> Unit,
    onRecenter: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val spacing = MaterialTheme.spacing
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.appColors.surfacePrimary,
        shape = MaterialTheme.shapes.large,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = spacing.xxLarge, vertical = spacing.xLarge),
            verticalArrangement = Arrangement.spacedBy(spacing.medium),
        ) {
            Box(
                modifier = Modifier
                    .align(Alignment.CenterHorizontally)
                    .width(36.dp)
                    .heightIn(min = 4.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.appColors.divider),
            )
            Row(
                horizontalArrangement = Arrangement.spacedBy(spacing.medium),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                MemberAvatar(
                    displayName = member.displayName,
                    initials = member.initials,
                    photoUrl = member.photoUrl,
                    presenceState = member.presenceState,
                    modifier = Modifier.size(60.dp),
                )
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(spacing.xSmall),
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(member.displayName, style = MaterialTheme.typography.titleLarge)
                        PresenceStatus(presenceState = member.presenceState)
                    }
                    Text(member.locationLabel, style = MaterialTheme.typography.bodyLarge)
                    member.secondaryLocationLabel?.let { secondaryLabel ->
                        Text(
                            text = secondaryLabel,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.appColors.textSecondary,
                        )
                    }
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(spacing.small),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        LastUpdatedText(text = member.lastUpdatedLabel)
                        member.batteryPercent?.let { BatteryIndicator(batteryPercent = it) }
                    }
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                TextButton(onClick = onViewToday) {
                    Text("View Today")
                }
                TextButton(onClick = onOpenDetails) {
                    Text("Open Details")
                }
                TextButton(onClick = onRecenter) {
                    Text("Recenter")
                }
            }
        }
    }
}

@Composable
fun SectionHeader(
    title: String,
    subtitle: String? = null,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(title, style = MaterialTheme.typography.titleMedium)
        subtitle?.let {
            Text(
                text = it,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.appColors.textSecondary,
            )
        }
    }
}

@Composable
fun EmptyState(
    title: String,
    message: String,
    modifier: Modifier = Modifier,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.appColors.surfacePrimary,
            contentColor = MaterialTheme.appColors.textPrimary,
        ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(MaterialTheme.spacing.xxLarge),
            verticalArrangement = Arrangement.spacedBy(MaterialTheme.spacing.small),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(title, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.appColors.textSecondary,
                textAlign = TextAlign.Center,
            )
            if (actionLabel != null && onAction != null) {
                TextButton(onClick = onAction) {
                    Text(actionLabel)
                }
            }
        }
    }
}

@Composable
fun ErrorState(
    title: String,
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.appColors.surfacePrimary,
            contentColor = MaterialTheme.appColors.textPrimary,
        ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(MaterialTheme.spacing.xxLarge),
            verticalArrangement = Arrangement.spacedBy(MaterialTheme.spacing.small),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Icon(
                imageVector = Icons.Outlined.ErrorOutline,
                contentDescription = null,
                tint = MaterialTheme.appColors.warning,
            )
            Text(title, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.appColors.textSecondary,
                textAlign = TextAlign.Center,
            )
            TextButton(onClick = onRetry) {
                Text("Try Again")
            }
        }
    }
}

@Composable
fun LoadingState(
    label: String,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(MaterialTheme.spacing.xxLarge),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(MaterialTheme.spacing.medium),
    ) {
        CircularProgressIndicator()
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.appColors.textSecondary,
        )
    }
}

@Composable
private fun RolePill(text: String) {
    Surface(
        shape = CircleShape,
        color = MaterialTheme.appColors.backgroundSecondary,
        contentColor = MaterialTheme.appColors.textSecondary,
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelSmall,
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF07111F)
@Composable
private fun FamilyMemberCardLivePreview() {
    GpsTrackTheme {
        FamilyMemberCard(member = previewMember(PresenceState.LIVE), onClick = {})
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF07111F)
@Composable
private fun FamilyMemberCardStalePreview() {
    GpsTrackTheme {
        FamilyMemberCard(member = previewMember(PresenceState.STALE), onClick = {})
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF07111F)
@Composable
private fun FamilyMemberCardOfflinePreview() {
    GpsTrackTheme {
        FamilyMemberCard(
            member = previewMember(PresenceState.OFFLINE).copy(
                locationLabel = "Location unavailable",
                secondaryLocationLabel = null,
                batteryPercent = null,
                lastUpdatedLabel = "Last seen 07/09/26 20:14",
            ),
            onClick = {},
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF07111F)
@Composable
private fun MemberPreviewSheetPreview() {
    GpsTrackTheme {
        MemberPreviewSheet(
            member = previewMember(PresenceState.LIVE),
            onViewToday = {},
            onOpenDetails = {},
            onRecenter = {},
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF07111F)
@Composable
private fun EmptyStatePreview() {
    GpsTrackTheme {
        EmptyState(
            title = "No family members are available.",
            message = "Check the family configuration or refresh.",
        )
    }
}

private fun previewMember(presenceState: PresenceState) = FamilyMemberUiModel(
    id = "member-1",
    displayName = "Kristi",
    initials = "K",
    photoUrl = null,
    role = MemberRole.PARENT,
    locationLabel = "Near Broad Street",
    secondaryLocationLabel = "King Street District",
    lastUpdatedLabel = when (presenceState) {
        PresenceState.LIVE -> "Updated 2 min ago"
        PresenceState.STALE -> "Updated 18 min ago"
        PresenceState.OFFLINE -> "Last seen 07/09/26 20:14"
        PresenceState.UNKNOWN -> "Last seen unavailable"
    },
    presenceState = presenceState,
    batteryPercent = if (presenceState == PresenceState.OFFLINE) null else 82,
    latitude = 37.7749,
    longitude = -122.4194,
    accuracyMeters = 12.0,
)
