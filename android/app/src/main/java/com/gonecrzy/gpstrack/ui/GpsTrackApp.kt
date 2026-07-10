package com.gonecrzy.gpstrack.ui

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.History
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.People
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.gonecrzy.gpstrack.AppContainer
import com.gonecrzy.gpstrack.ui.navigation.AppDestination
import com.gonecrzy.gpstrack.ui.model.currentHistoryDate
import com.gonecrzy.gpstrack.ui.model.HistoryPeriod
import com.gonecrzy.gpstrack.ui.screens.HistoryScreen
import com.gonecrzy.gpstrack.ui.screens.MapScreen
import com.gonecrzy.gpstrack.ui.screens.MemberDetailScreen
import com.gonecrzy.gpstrack.ui.screens.MembersScreen
import com.gonecrzy.gpstrack.ui.screens.PlacesScreen
import com.gonecrzy.gpstrack.ui.screens.SettingsScreen
import com.gonecrzy.gpstrack.ui.theme.appColors

@Composable
fun GpsTrackApp(container: AppContainer) {
    val navController = rememberNavController()
    val destinations = listOf(
        AppDestination.Members,
        AppDestination.Map,
        AppDestination.Places,
        AppDestination.History,
        AppDestination.Settings,
    )
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = backStackEntry?.destination

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        contentWindowInsets = WindowInsets(0, 0, 0, 0),
        bottomBar = {
            NavigationBar(
                containerColor = androidx.compose.material3.MaterialTheme.appColors.surfacePrimary.copy(alpha = 0.98f),
            ) {
                destinations.forEach { destination ->
                    NavigationBarItem(
                        selected = currentDestination.isTopLevelSelected(destination),
                        onClick = {
                            navController.navigate(destination.rootRoute) {
                                popUpTo(navController.graph.startDestinationId) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        colors = NavigationBarItemDefaults.colors(
                            indicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                            selectedIconColor = androidx.compose.material3.MaterialTheme.appColors.accentPrimary,
                            selectedTextColor = androidx.compose.material3.MaterialTheme.appColors.accentPrimary,
                            unselectedIconColor = androidx.compose.material3.MaterialTheme.appColors.textSecondary,
                            unselectedTextColor = androidx.compose.material3.MaterialTheme.appColors.textSecondary,
                        ),
                        icon = {
                            when (destination) {
                                AppDestination.Members -> Icon(Icons.Outlined.People, contentDescription = null)
                                AppDestination.Map -> Icon(Icons.Outlined.Map, contentDescription = null)
                                AppDestination.Places -> Icon(Icons.Outlined.Place, contentDescription = null)
                                AppDestination.History -> Icon(Icons.Outlined.History, contentDescription = null)
                                AppDestination.Settings -> Icon(Icons.Outlined.Settings, contentDescription = null)
                                AppDestination.MemberDetail -> Unit
                            }
                        },
                        label = { Text(destination.label) },
                    )
                }
            }
        },
    ) { innerPadding ->
        val screenPadding = PaddingValues(bottom = innerPadding.calculateBottomPadding())
        NavHost(
            navController = navController,
            startDestination = AppDestination.Members.route,
            modifier = Modifier.fillMaxSize(),
        ) {
            composable(AppDestination.Members.route) {
                MembersScreen(
                    repository = container.repository,
                    contentPadding = screenPadding,
                    onMemberSelected = { navController.navigate(AppDestination.MemberDetail.build(it)) },
                )
            }
            composable(AppDestination.Map.route) {
                MapScreen(
                    repository = container.repository,
                    preferences = container.preferences,
                    contentPadding = screenPadding,
                    onFamilySelected = {
                        navController.navigate(AppDestination.Members.rootRoute) {
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                    onViewToday = { memberId, date ->
                        navController.navigate(
                            AppDestination.History.build(
                                memberId = memberId,
                                period = HistoryPeriod.DAY.name,
                                date = date,
                            ),
                        ) {
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                    onMemberSelected = { navController.navigate(AppDestination.MemberDetail.build(it)) },
                )
            }
            composable(AppDestination.Places.route) {
                PlacesScreen(
                    repository = container.repository,
                    contentPadding = screenPadding,
                )
            }
            composable(
                route = AppDestination.History.route,
                arguments = listOf(
                    navArgument("memberId") {
                        type = NavType.StringType
                        nullable = true
                        defaultValue = null
                    },
                    navArgument("period") {
                        type = NavType.StringType
                        nullable = true
                        defaultValue = null
                    },
                    navArgument("date") {
                        type = NavType.StringType
                        nullable = true
                        defaultValue = null
                    },
                ),
            ) { entry ->
                HistoryScreen(
                    repository = container.repository,
                    preferences = container.preferences,
                    contentPadding = screenPadding,
                    initialMemberId = entry.arguments?.getString("memberId"),
                    initialPeriod = entry.arguments?.getString("period"),
                    initialDate = entry.arguments?.getString("date"),
                    onMemberSelected = { memberId ->
                        navController.navigate(AppDestination.MemberDetail.build(memberId))
                    },
                )
            }
            composable(AppDestination.Settings.route) {
                SettingsScreen(
                    preferences = container.preferences,
                    contentPadding = screenPadding,
                )
            }
            composable(
                route = AppDestination.MemberDetail.route,
                arguments = listOf(navArgument("memberId") { type = NavType.StringType }),
            ) { entry ->
                MemberDetailScreen(
                    memberId = entry.arguments?.getString("memberId").orEmpty(),
                    repository = container.repository,
                    onViewMap = {
                        navController.navigate(AppDestination.Map.rootRoute) {
                            launchSingleTop = true
                            restoreState = true
                        }
                    },
                    onViewHistory = { selectedMemberId ->
                        navController.navigate(
                            AppDestination.History.build(
                                memberId = selectedMemberId,
                                period = HistoryPeriod.DAY.name,
                                date = currentHistoryDate().toString(),
                            ),
                        )
                    },
                )
            }
        }
    }
}

private fun NavDestination?.isTopLevelSelected(destination: AppDestination): Boolean {
    return this?.hierarchy?.any { navDestination ->
        navDestination.route?.startsWith(destination.rootRoute) == true
    } == true
}
