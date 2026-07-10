package com.gonecrzy.gpstrack.ui.navigation

sealed class AppDestination(
    val route: String,
    val rootRoute: String,
    val label: String,
) {
    data object Members : AppDestination("members", "members", "Family")
    data object Map : AppDestination("map", "map", "Map")
    data object Places : AppDestination("places", "places", "Places")
    data object History : AppDestination(
        "history?memberId={memberId}&period={period}&date={date}",
        "history",
        "History",
    ) {
        fun build(
            memberId: String? = null,
            period: String? = null,
            date: String? = null,
        ): String {
            val query = buildList {
                memberId?.let { add("memberId=$it") }
                period?.let { add("period=$it") }
                date?.let { add("date=$it") }
            }.joinToString("&")
            return if (query.isBlank()) rootRoute else "$rootRoute?$query"
        }
    }
    data object Settings : AppDestination("settings", "settings", "Settings")
    data object MemberDetail : AppDestination("members/{memberId}", "members", "Member") {
        fun build(memberId: String): String = "members/$memberId"
    }
}
