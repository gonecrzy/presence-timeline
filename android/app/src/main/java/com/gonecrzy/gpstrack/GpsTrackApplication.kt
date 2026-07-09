package com.gonecrzy.gpstrack

import android.app.Application
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.gonecrzy.gpstrack.sync.RefreshSnapshotWorker
import java.util.concurrent.TimeUnit

class GpsTrackApplication : Application() {
    lateinit var appContainer: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        appContainer = AppContainer(
            repository = GpsTrackRepository.create(this),
            preferences = AppPreferences(this),
        )
        enqueueRefreshWork()
    }

    private fun enqueueRefreshWork() {
        val request = PeriodicWorkRequestBuilder<RefreshSnapshotWorker>(15, TimeUnit.MINUTES).build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            RefreshSnapshotWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }
}
