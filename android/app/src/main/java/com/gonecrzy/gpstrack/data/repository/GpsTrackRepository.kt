package com.gonecrzy.gpstrack.data.repository

import android.content.Context
import com.gonecrzy.gpstrack.data.local.GpsTrackDatabase
import com.gonecrzy.gpstrack.data.local.MemberEntity
import com.gonecrzy.gpstrack.data.local.PlaceEntity
import com.gonecrzy.gpstrack.data.model.DailySummary
import com.gonecrzy.gpstrack.data.model.DeviceSummary
import com.gonecrzy.gpstrack.data.model.MemberSummary
import com.gonecrzy.gpstrack.data.model.PlaceSummary
import com.gonecrzy.gpstrack.data.model.TimelineItem
import com.gonecrzy.gpstrack.data.model.TripRoute
import com.gonecrzy.gpstrack.data.model.TripRoutePoint
import com.gonecrzy.gpstrack.data.model.TripSummary
import com.gonecrzy.gpstrack.data.network.DeviceDto
import com.gonecrzy.gpstrack.data.network.DeviceUpdateRequestDto
import com.gonecrzy.gpstrack.data.network.GpsTrackApiFactory
import com.gonecrzy.gpstrack.data.network.MemberDto
import com.gonecrzy.gpstrack.data.network.MemberUpdateRequestDto
import com.gonecrzy.gpstrack.data.network.PlaceDto
import com.gonecrzy.gpstrack.data.network.PlaceUpsertRequestDto
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.squareup.moshi.JsonAdapter
import com.squareup.moshi.Moshi
import com.squareup.moshi.Types
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

class GpsTrackRepository(
    private val database: GpsTrackDatabase,
    private val preferences: AppPreferences,
    private val moshi: Moshi,
) {
    private val memberDevicesAdapter: JsonAdapter<List<DeviceSummary>> = moshi.adapter(
        Types.newParameterizedType(List::class.java, DeviceSummary::class.java),
    )

    fun observeMembers(): Flow<List<MemberSummary>> {
        return database.memberDao().observeMembers().map { entities ->
            entities.map { entity ->
                MemberSummary(
                    id = entity.id,
                    displayName = entity.displayName,
                    isChild = entity.isChild,
                    lastSeenAt = entity.lastSeenAt,
                    devices = memberDevicesAdapter.fromJson(entity.devicesJson).orEmpty(),
                )
            }
        }
    }

    fun observePlaces(): Flow<List<PlaceSummary>> {
        return database.placeDao().observePlaces().map { entities ->
            entities.map { entity ->
                PlaceSummary(
                    id = entity.id,
                    name = entity.name,
                    placeType = entity.placeType,
                    latitude = entity.latitude,
                    longitude = entity.longitude,
                    radiusM = entity.radiusM,
                    isSafeZone = entity.isSafeZone,
                )
            }
        }
    }

    suspend fun refreshMembers() {
        val api = api()
        val members = api.listMembers().items
        database.memberDao().upsertAll(members.map(::memberEntity))
    }

    suspend fun refreshPlaces() {
        val api = api()
        val places = api.listPlaces().items
        database.placeDao().upsertAll(places.map(::placeEntity))
    }

    suspend fun updateMember(memberId: String, displayName: String?, isChild: Boolean?) {
        val member = api().updateMember(
            memberId,
            MemberUpdateRequestDto(displayName = displayName, isChild = isChild),
        )
        database.memberDao().upsertAll(listOf(memberEntity(member)))
    }

    suspend fun updateDevice(memberId: String, deviceId: String, label: String?, ignored: Boolean?) {
        val currentMember = observeMembers().first().firstOrNull { it.id == memberId } ?: return
        val updatedDevice = api().updateDevice(
            memberId,
            deviceId,
            DeviceUpdateRequestDto(label = label, ignored = ignored),
        )
        val mergedDevices = currentMember.devices.map { device ->
            if (device.id == updatedDevice.id) updatedDevice.toDomain() else device
        }
        database.memberDao().upsertAll(
            listOf(
                MemberEntity(
                    id = currentMember.id,
                    displayName = currentMember.displayName,
                    isChild = currentMember.isChild,
                    lastSeenAt = currentMember.lastSeenAt,
                    devicesJson = memberDevicesAdapter.toJson(mergedDevices),
                ),
            ),
        )
    }

    suspend fun createPlace(
        name: String,
        placeType: String?,
        latitude: Double,
        longitude: Double,
        radiusM: Double,
        isSafeZone: Boolean,
    ) {
        val place = api().createPlace(
            PlaceUpsertRequestDto(name, placeType, latitude, longitude, radiusM, isSafeZone),
        )
        database.placeDao().upsertAll(listOf(placeEntity(place)))
    }

    suspend fun updatePlace(
        placeId: String,
        name: String,
        placeType: String?,
        latitude: Double,
        longitude: Double,
        radiusM: Double,
        isSafeZone: Boolean,
    ) {
        val place = api().updatePlace(
            placeId,
            PlaceUpsertRequestDto(name, placeType, latitude, longitude, radiusM, isSafeZone),
        )
        database.placeDao().upsertAll(listOf(placeEntity(place)))
    }

    suspend fun deletePlace(placeId: String) {
        api().deletePlace(placeId)
        database.placeDao().deleteById(placeId)
    }

    suspend fun loadTimeline(memberId: String, start: String, end: String): List<TimelineItem> {
        return api().getTimeline(memberId, start, end).items.map { item ->
            TimelineItem(
                kind = item.kind,
                observedAt = item.observedAt,
                tripId = item.tripId,
                startedAt = item.startedAt,
                endedAt = item.endedAt,
                latitude = item.latitude,
                longitude = item.longitude,
                batteryLevel = item.batteryLevel,
                sourceEntityId = item.sourceEntityId,
                distanceM = item.distanceM,
                pointCount = item.pointCount,
                startLabel = item.startLabel,
                endLabel = item.endLabel,
                eventType = item.eventType,
                severity = item.severity,
                placeId = item.placeId,
                payload = item.payload,
            )
        }
    }

    suspend fun loadTrips(memberId: String, date: String): List<TripSummary> {
        return api().getTrips(memberId, date).items.map { trip ->
            TripSummary(
                id = trip.id,
                startedAt = trip.startedAt,
                endedAt = trip.endedAt,
                pointCount = trip.pointCount,
                distanceM = trip.distanceM,
                startLabel = trip.startLabel,
                endLabel = trip.endLabel,
            )
        }
    }

    suspend fun loadDailySummary(memberId: String, date: String): DailySummary {
        val summary = api().getDailySummary(memberId, date)
        return DailySummary(
            summaryDate = summary.summaryDate,
            firstSeenAt = summary.firstSeenAt,
            lastSeenAt = summary.lastSeenAt,
            tripCount = summary.tripCount,
            totalDistanceM = summary.totalDistanceM,
        )
    }

    suspend fun loadTripRoute(memberId: String, tripId: String): TripRoute {
        val route = api().getTripRoute(memberId, tripId)
        return TripRoute(
            id = route.id,
            memberId = route.memberId,
            startedAt = route.startedAt,
            endedAt = route.endedAt,
            distanceM = route.distanceM,
            pointCount = route.pointCount,
            points = route.points.map { point ->
                TripRoutePoint(
                    memberId = point.memberId,
                    observedAt = point.observedAt,
                    latitude = point.latitude,
                    longitude = point.longitude,
                    accuracyM = point.accuracyM,
                    batteryLevel = point.batteryLevel,
                    sourceEntityId = point.sourceEntityId,
                )
            },
        )
    }

    suspend fun currentBaseUrl(): String = preferences.baseUrl.first()

    suspend fun currentMapStyleUrl(): String = preferences.mapStyleUrl.first()

    companion object {
        fun create(context: Context): GpsTrackRepository {
            val moshi = Moshi.Builder()
                .addLast(KotlinJsonAdapterFactory())
                .build()
            return GpsTrackRepository(
                database = GpsTrackDatabase.build(context),
                preferences = AppPreferences(context),
                moshi = moshi,
            )
        }
    }

    private suspend fun api() = GpsTrackApiFactory.create(preferences.baseUrl.first())

    private fun memberEntity(dto: MemberDto): MemberEntity {
        return MemberEntity(
            id = dto.id,
            displayName = dto.displayName,
            isChild = dto.isChild,
            lastSeenAt = dto.lastSeenAt,
            devicesJson = memberDevicesAdapter.toJson(dto.devices.map(DeviceDto::toDomain)),
        )
    }

    private fun placeEntity(dto: PlaceDto): PlaceEntity {
        return PlaceEntity(
            id = dto.id,
            name = dto.name,
            placeType = dto.placeType,
            latitude = dto.latitude,
            longitude = dto.longitude,
            radiusM = dto.radiusM,
            isSafeZone = dto.isSafeZone,
        )
    }
}

private fun DeviceDto.toDomain(): DeviceSummary {
    return DeviceSummary(
        id = id,
        provider = provider,
        externalId = externalId,
        label = label,
        ignored = ignored,
        lastSeenAt = lastSeenAt,
    )
}
