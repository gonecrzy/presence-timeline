package com.gonecrzy.gpstrack.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val AppColors = darkColorScheme(
    primary = Sky,
    onPrimary = Ink,
    secondary = Ocean,
    onSecondary = Sand,
    tertiary = Alert,
    background = Ink,
    onBackground = Sand,
    surface = Ocean,
    onSurface = Sand,
)

@Composable
fun GpsTrackTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = AppColors,
        typography = AppTypography,
        content = content,
    )
}
