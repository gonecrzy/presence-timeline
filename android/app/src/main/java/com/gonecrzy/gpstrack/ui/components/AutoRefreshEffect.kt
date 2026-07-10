package com.gonecrzy.gpstrack.ui.components

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.repeatOnLifecycle
import kotlin.coroutines.coroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

private const val DefaultRefreshIntervalMillis = 60_000L

@Composable
fun AutoRefreshEffect(
    enabled: Boolean = true,
    refreshIntervalMillis: Long = DefaultRefreshIntervalMillis,
    onRefresh: suspend () -> Unit,
) {
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val currentOnRefresh by rememberUpdatedState(onRefresh)

    LaunchedEffect(lifecycle, enabled, refreshIntervalMillis) {
        if (!enabled) {
            return@LaunchedEffect
        }
        lifecycle.repeatOnLifecycle(Lifecycle.State.STARTED) {
            while (coroutineContext.isActive) {
                delay(refreshIntervalMillis)
                currentOnRefresh()
            }
        }
    }
}
