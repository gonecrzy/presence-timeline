package com.gonecrzy.gpstrack.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "members")
data class MemberEntity(
    @PrimaryKey val id: String,
    val displayName: String,
    val isChild: Boolean,
    val lastSeenAt: String?,
    val currentLocationLabel: String?,
    val devicesJson: String,
)

@Entity(tableName = "places")
data class PlaceEntity(
    @PrimaryKey val id: String,
    val name: String,
    val placeType: String?,
    val latitude: Double,
    val longitude: Double,
    val radiusM: Double,
    val isSafeZone: Boolean,
)
