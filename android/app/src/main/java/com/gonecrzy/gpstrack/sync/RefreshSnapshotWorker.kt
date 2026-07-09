package com.gonecrzy.gpstrack.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.gonecrzy.gpstrack.GpsTrackApplication

class RefreshSnapshotWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val repository = (applicationContext as GpsTrackApplication).appContainer.repository
        return runCatching {
            repository.refreshMembers()
            repository.refreshPlaces()
        }.fold(
            onSuccess = { Result.success() },
            onFailure = { Result.retry() },
        )
    }

    companion object {
        const val WORK_NAME = "gpstrack-refresh-snapshot"
    }
}
