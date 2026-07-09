package com.gonecrzy.gpstrack.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.People
import androidx.compose.material.icons.outlined.Place
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.gonecrzy.gpstrack.AppContainer
import com.gonecrzy.gpstrack.ui.navigation.AppDestination
import com.gonecrzy.gpstrack.ui.screens.MapScreen
import com.gonecrzy.gpstrack.ui.screens.MemberDetailScreen
import com.gonecrzy.gpstrack.ui.screens.MembersScreen
import com.gonecrzy.gpstrack.ui.screens.PlacesScreen
import com.gonecrzy.gpstrack.ui.screens.SettingsScreen

@Composable
fun GpsTrackApp(container: AppContainer) {
    val navController = rememberNavController()
    val destinations = listOf(
        AppDestination.Members,
        AppDestination.Map,
        AppDestination.Places,
        AppDestination.Settings,
    )
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = backStackEntry?.destination

    Scaffold(
        bottomBar = {
            NavigationBar {
                destinations.forEach { destination ->
                    NavigationBarItem(
                        selected = currentDestination?.hierarchy?.any { it.route == destination.route } == true,
                        onClick = {
                            navController.navigate(destination.route) {
                                popUpTo(navController.graph.startDestinationId) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = {
                            when (destination) {
                                AppDestination.Members -> Icon(Icons.Outlined.People, contentDescription = null)
                                AppDestination.Map -> Icon(Icons.Outlined.Map, contentDescription = null)
                                AppDestination.Places -> Icon(Icons.Outlined.Place, contentDescription = null)
                                AppDestination.Settings -> Icon(Icons.Outlined.Settings, contentDescription = null)
                                AppDestination.MemberDetail -> Unit
                            }
                        },
                        label = { androidx.compose.material3.Text(destination.label) },
                    )
                }
            }
        },
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = AppDestination.Members.route,
            modifier = Modifier.padding(innerPadding),
        ) {
            composable(AppDestination.Members.route) {
                MembersScreen(
                    repository = container.repository,
                    onMemberSelected = { navController.navigate(AppDestination.MemberDetail.build(it)) },
                )
            }
            composable(AppDestination.Map.route) {
                MapScreen(
                    repository = container.repository,
                    preferences = container.preferences,
                    onMemberSelected = { navController.navigate(AppDestination.MemberDetail.build(it)) },
                )
            }
            composable(AppDestination.Places.route) {
                PlacesScreen(repository = container.repository)
            }
            composable(AppDestination.Settings.route) {
                SettingsScreen(preferences = container.preferences)
            }
            composable(
                route = AppDestination.MemberDetail.route,
                arguments = listOf(navArgument("memberId") { type = NavType.StringType }),
            ) { entry ->
                MemberDetailScreen(
                    memberId = entry.arguments?.getString("memberId").orEmpty(),
                    repository = container.repository,
                )
            }
        }
    }
}
