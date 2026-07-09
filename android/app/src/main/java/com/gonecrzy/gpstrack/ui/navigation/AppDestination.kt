package com.gonecrzy.gpstrack.ui.navigation

sealed class AppDestination(
    val route: String,
    val label: String,
) {
    data object Members : AppDestination("members", "Family")
    data object Map : AppDestination("map", "Map")
    data object Places : AppDestination("places", "Places")
    data object Settings : AppDestination("settings", "Settings")
    data object MemberDetail : AppDestination("members/{memberId}", "Member") {
        fun build(memberId: String): String = "members/$memberId"
    }
}
