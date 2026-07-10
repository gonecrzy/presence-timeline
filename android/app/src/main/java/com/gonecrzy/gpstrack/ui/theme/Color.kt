package com.gonecrzy.gpstrack.ui.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

@Immutable
data class AppThemeColors(
    val backgroundPrimary: Color,
    val backgroundSecondary: Color,
    val surfacePrimary: Color,
    val surfaceElevated: Color,
    val accentPrimary: Color,
    val textPrimary: Color,
    val textSecondary: Color,
    val success: Color,
    val warning: Color,
    val error: Color,
    val divider: Color,
)

val DarkThemeColors = AppThemeColors(
    backgroundPrimary = Color(0xFF07111F),
    backgroundSecondary = Color(0xFF0E1A2B),
    surfacePrimary = Color(0xFF102132),
    surfaceElevated = Color(0xFF162B40),
    accentPrimary = Color(0xFF58B8FF),
    textPrimary = Color(0xFFF5F8FC),
    textSecondary = Color(0xFFA7B6C8),
    success = Color(0xFF3DDC97),
    warning = Color(0xFFFFB84D),
    error = Color(0xFFFF6B6B),
    divider = Color(0x24FFFFFF),
)

internal val LocalAppThemeColors = staticCompositionLocalOf { DarkThemeColors }
