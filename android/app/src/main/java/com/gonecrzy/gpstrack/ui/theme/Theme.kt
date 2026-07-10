package com.gonecrzy.gpstrack.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider

private val AppDarkColorScheme = darkColorScheme(
    primary = DarkThemeColors.accentPrimary,
    onPrimary = DarkThemeColors.backgroundPrimary,
    primaryContainer = DarkThemeColors.accentPrimary.copy(alpha = 0.18f),
    onPrimaryContainer = DarkThemeColors.textPrimary,
    secondary = DarkThemeColors.surfaceElevated,
    onSecondary = DarkThemeColors.textPrimary,
    tertiary = DarkThemeColors.warning,
    onTertiary = DarkThemeColors.backgroundPrimary,
    background = DarkThemeColors.backgroundPrimary,
    onBackground = DarkThemeColors.textPrimary,
    surface = DarkThemeColors.surfacePrimary,
    onSurface = DarkThemeColors.textPrimary,
    surfaceVariant = DarkThemeColors.backgroundSecondary,
    onSurfaceVariant = DarkThemeColors.textSecondary,
    outline = DarkThemeColors.divider,
    error = DarkThemeColors.error,
    onError = DarkThemeColors.textPrimary,
)

@Composable
fun GpsTrackTheme(content: @Composable () -> Unit) {
    CompositionLocalProvider(
        LocalAppThemeColors provides DarkThemeColors,
        LocalAppSpacing provides AppSpacing(),
    ) {
        MaterialTheme(
            colorScheme = AppDarkColorScheme,
            typography = AppTypography,
            shapes = AppShapes,
            content = content,
        )
    }
}

val MaterialTheme.appColors: AppThemeColors
    @Composable
    get() = LocalAppThemeColors.current

val MaterialTheme.spacing: AppSpacing
    @Composable
    get() = LocalAppSpacing.current
