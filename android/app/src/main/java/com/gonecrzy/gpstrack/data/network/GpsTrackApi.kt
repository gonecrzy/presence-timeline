package com.gonecrzy.gpstrack.data.network

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface GpsTrackApi {
    @GET("api/v1/members")
    suspend fun listMembers(): MemberListResponseDto

    @GET("api/v1/members/{memberId}/latest-location")
    suspend fun getLatestLocation(@Path("memberId") memberId: String): LocationPointDto

    @GET("api/v1/members/{memberId}/history")
    suspend fun getMemberHistory(
        @Path("memberId") memberId: String,
        @Query("start") start: String,
        @Query("end") end: String,
    ): LocationHistoryResponseDto

    @PATCH("api/v1/members/{memberId}")
    suspend fun updateMember(
        @Path("memberId") memberId: String,
        @Body payload: MemberUpdateRequestDto,
    ): MemberDto

    @PATCH("api/v1/members/{memberId}/devices/{deviceId}")
    suspend fun updateDevice(
        @Path("memberId") memberId: String,
        @Path("deviceId") deviceId: String,
        @Body payload: DeviceUpdateRequestDto,
    ): DeviceDto

    @GET("api/v1/members/{memberId}/timeline")
    suspend fun getTimeline(
        @Path("memberId") memberId: String,
        @Query("start") start: String,
        @Query("end") end: String,
    ): TimelineResponseDto

    @GET("api/v1/members/{memberId}/trips")
    suspend fun getTrips(
        @Path("memberId") memberId: String,
        @Query("date") date: String,
    ): TripListResponseDto

    @GET("api/v1/members/{memberId}/daily-summary")
    suspend fun getDailySummary(
        @Path("memberId") memberId: String,
        @Query("date") date: String,
    ): DailySummaryDto

    @GET("api/v1/members/{memberId}/trips/{tripId}/route")
    suspend fun getTripRoute(
        @Path("memberId") memberId: String,
        @Path("tripId") tripId: String,
    ): TripRouteDto

    @GET("api/v1/places")
    suspend fun listPlaces(): PlaceListResponseDto

    @POST("api/v1/places")
    suspend fun createPlace(@Body payload: PlaceUpsertRequestDto): PlaceDto

    @PATCH("api/v1/places/{placeId}")
    suspend fun updatePlace(
        @Path("placeId") placeId: String,
        @Body payload: PlaceUpsertRequestDto,
    ): PlaceDto

    @DELETE("api/v1/places/{placeId}")
    suspend fun deletePlace(@Path("placeId") placeId: String)
}

object GpsTrackApiFactory {
    fun create(baseUrl: String): GpsTrackApi {
        val moshi = Moshi.Builder()
            .addLast(KotlinJsonAdapterFactory())
            .build()
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()

        return Retrofit.Builder()
            .baseUrl(normalizeBaseUrl(baseUrl))
            .client(client)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()
            .create(GpsTrackApi::class.java)
    }

    private fun normalizeBaseUrl(baseUrl: String): String {
        return if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
    }
}
