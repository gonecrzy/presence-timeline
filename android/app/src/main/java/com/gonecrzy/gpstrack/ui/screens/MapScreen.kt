package com.gonecrzy.gpstrack.ui.screens

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.PointF
import android.graphics.Typeface
import android.os.Bundle
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.MyLocation
import androidx.compose.material.icons.outlined.People
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.gonecrzy.gpstrack.data.model.LocationPoint
import com.gonecrzy.gpstrack.data.repository.GpsTrackRepository
import com.gonecrzy.gpstrack.data.settings.AppPreferences
import com.gonecrzy.gpstrack.ui.components.EmptyState
import com.gonecrzy.gpstrack.ui.components.ErrorState
import com.gonecrzy.gpstrack.ui.components.LoadingState
import com.gonecrzy.gpstrack.ui.components.AutoRefreshEffect
import com.gonecrzy.gpstrack.ui.components.MapControlButton
import com.gonecrzy.gpstrack.ui.components.MemberPreviewSheet
import com.gonecrzy.gpstrack.ui.model.FamilyMemberUiModel
import com.gonecrzy.gpstrack.ui.model.MapPlaceUiModel
import com.gonecrzy.gpstrack.ui.model.PresenceState
import com.gonecrzy.gpstrack.ui.model.currentHistoryDate
import com.gonecrzy.gpstrack.ui.theme.appColors
import com.gonecrzy.gpstrack.ui.theme.spacing
import com.gonecrzy.gpstrack.ui.viewmodel.MapViewModel
import com.gonecrzy.gpstrack.ui.viewmodel.simpleViewModelFactory
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.geometry.LatLngBounds
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.style.expressions.Expression.eq
import org.maplibre.android.style.expressions.Expression.get
import org.maplibre.geojson.Feature
import org.maplibre.geojson.FeatureCollection
import org.maplibre.geojson.LineString
import org.maplibre.geojson.Point
import com.gonecrzy.gpstrack.ui.map.MapSnapshotCalculator
import com.gonecrzy.gpstrack.ui.map.buildRadiusRing
import com.gonecrzy.gpstrack.ui.map.ensureSymbolLayer
import com.gonecrzy.gpstrack.ui.map.ensureCircleLayer
import com.gonecrzy.gpstrack.ui.map.ensureLineLayer
import com.gonecrzy.gpstrack.ui.map.labelProperties
import com.gonecrzy.gpstrack.ui.map.markerIconProperties
import com.gonecrzy.gpstrack.ui.map.upsertGeoJsonSource

private const val MarkerGroupingRadiusMeters = 40.0
private const val MarkerSourceId = "gpstrack-family-markers"
private const val MarkerLayerId = "gpstrack-family-marker-layer"
private const val SavedPlaceSourceId = "gpstrack-saved-places"
private const val SavedPlaceRingLayerId = "gpstrack-saved-place-rings"
private const val SavedPlaceCenterLayerId = "gpstrack-saved-place-centers"
private const val SavedPlaceLabelLayerId = "gpstrack-saved-place-labels"
private const val SelectedMemberZoom = 14.0
private const val MaximumAutoZoom = 12.5

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MapScreen(
    repository: GpsTrackRepository,
    preferences: AppPreferences,
    onFamilySelected: () -> Unit,
    onViewToday: (String, String) -> Unit,
    onMemberSelected: (String) -> Unit,
    contentPadding: PaddingValues = PaddingValues(),
) {
    val factory = remember(repository) {
        simpleViewModelFactory { MapViewModel(repository) }
    }
    val viewModel: MapViewModel = viewModel(factory = factory)
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val mapStyleUrl by preferences.mapStyleUrl.collectAsStateWithLifecycle(
        initialValue = com.gonecrzy.gpstrack.BuildConfig.DEFAULT_MAP_STYLE_URL,
    )
    val colors = MaterialTheme.appColors
    val spacing = MaterialTheme.spacing
    val selectedMember = uiState.members.firstOrNull { member -> member.id == uiState.selectedMemberId }
    var recenterToken by rememberSaveable { mutableIntStateOf(0) }
    val staleCount = uiState.members.count { member ->
        member.presenceState == PresenceState.STALE || member.presenceState == PresenceState.OFFLINE
    }
    val mapVisualColors = remember(colors) {
        MapVisualColors(
            background = colors.surfacePrimary.toArgb(),
            markerFill = colors.surfaceElevated.toArgb(),
            accent = colors.accentPrimary.toArgb(),
            live = colors.success.toArgb(),
            stale = colors.warning.toArgb(),
            offline = colors.textSecondary.toArgb(),
            text = colors.textPrimary.toArgb(),
            placeRing = colors.accentPrimary.copy(alpha = 0.62f).toArgb(),
            placeCenter = colors.accentPrimary.toArgb(),
            white = android.graphics.Color.WHITE,
        )
    }

    AutoRefreshEffect(onRefresh = { viewModel.refresh() })

    LaunchedEffect(selectedMember?.id) {
        if (selectedMember != null) {
            recenterToken += 1
        }
    }

    BackHandler(enabled = selectedMember != null) {
        viewModel.selectMember(null)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(colors.backgroundPrimary),
    ) {
        MapSurface(
            context = LocalContext.current,
            mapStyleUrl = mapStyleUrl,
            members = uiState.members,
            places = uiState.places,
            selectedMemberId = uiState.selectedMemberId,
            recenterToken = recenterToken,
            visualColors = mapVisualColors,
            onMarkerSelected = { memberId -> viewModel.selectMember(memberId) },
            onMapTapped = { viewModel.selectMember(null) },
            modifier = Modifier.fillMaxSize(),
        )

        when {
            uiState.isLoading && uiState.members.isEmpty() -> {
                LoadingOverlay(label = "Loading live map")
            }

            uiState.errorMessage != null && uiState.members.isEmpty() -> {
                CenterOverlay(
                    contentPadding = contentPadding,
                    content = {
                        ErrorState(
                            title = "Unable to load the live map.",
                            message = "Current family locations could not be loaded. Try refreshing.",
                            onRetry = viewModel::refresh,
                        )
                    },
                )
            }

            uiState.members.isEmpty() -> {
                CenterOverlay(
                    contentPadding = contentPadding,
                    content = {
                        EmptyState(
                            title = "No family members are available.",
                            message = "Check the family configuration or refresh.",
                            actionLabel = "Refresh",
                            onAction = viewModel::refresh,
                        )
                    },
                )
            }
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding()
                .padding(horizontal = spacing.large, vertical = spacing.medium),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(spacing.medium)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    MapControlButton(
                        contentDescription = "Open family list",
                        onClick = onFamilySelected,
                        icon = {
                            androidx.compose.material3.Icon(
                                imageVector = Icons.Outlined.People,
                                contentDescription = null,
                                tint = colors.textPrimary,
                            )
                        },
                    )
                    MapControlButton(
                        contentDescription = "Refresh live map",
                        onClick = viewModel::refresh,
                        icon = {
                            androidx.compose.material3.Icon(
                                imageVector = Icons.Outlined.Refresh,
                                contentDescription = null,
                                tint = colors.textPrimary,
                            )
                        },
                    )
                }
                if (uiState.errorMessage != null && uiState.members.isNotEmpty()) {
                    Surface(
                        color = colors.surfacePrimary.copy(alpha = 0.94f),
                        shape = MaterialTheme.shapes.medium,
                    ) {
                        Text(
                            text = "Showing the last known family locations.",
                            modifier = Modifier.padding(horizontal = spacing.large, vertical = spacing.medium),
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.textSecondary,
                        )
                    }
                }
            }

            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(spacing.medium),
                horizontalAlignment = Alignment.Start,
            ) {
                MapControlButton(
                    contentDescription = "Recenter family map",
                    onClick = { recenterToken += 1 },
                    icon = {
                        androidx.compose.material3.Icon(
                            imageVector = Icons.Outlined.MyLocation,
                            contentDescription = null,
                            tint = colors.textPrimary,
                        )
                    },
                )
                Surface(
                    color = colors.surfacePrimary.copy(alpha = 0.94f),
                    shape = CircleShape,
                ) {
                    Text(
                        text = buildStatusPillLabel(uiState.members.size, staleCount, uiState.isRefreshing),
                        modifier = Modifier.padding(horizontal = spacing.large, vertical = spacing.small),
                        style = MaterialTheme.typography.labelLarge,
                        color = colors.textPrimary,
                    )
                }
            }
        }
    }

    if (selectedMember != null) {
        ModalBottomSheet(
            onDismissRequest = { viewModel.selectMember(null) },
            containerColor = colors.surfacePrimary,
            dragHandle = null,
            contentColor = colors.textPrimary,
            tonalElevation = 0.dp,
        ) {
            MemberPreviewSheet(
                member = selectedMember,
                onViewToday = {
                    onViewToday(
                        selectedMember.id,
                        currentHistoryDate().toString(),
                    )
                },
                onOpenDetails = { onMemberSelected(selectedMember.id) },
                onRecenter = { recenterToken += 1 },
                modifier = Modifier.navigationBarsPadding(),
            )
        }
    }
}

@Composable
private fun LoadingOverlay(label: String) {
    CenterOverlay(contentPadding = PaddingValues(), content = { LoadingState(label = label) })
}

@Composable
private fun CenterOverlay(
    contentPadding: PaddingValues,
    content: @Composable () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .safeDrawingPadding()
            .padding(
                start = 16.dp,
                top = 16.dp,
                end = 16.dp,
                bottom = contentPadding.calculateBottomPadding() + 16.dp,
            ),
        contentAlignment = Alignment.Center,
    ) {
        content()
    }
}

@Composable
private fun MapSurface(
    context: Context,
    mapStyleUrl: String,
    members: List<FamilyMemberUiModel>,
    places: List<MapPlaceUiModel>,
    selectedMemberId: String?,
    recenterToken: Int,
    visualColors: MapVisualColors,
    onMarkerSelected: (String) -> Unit,
    onMapTapped: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val lifecycleOwner = LocalLifecycleOwner.current
    val mapView = remember {
        MapLibre.getInstance(context)
        MapView(context).apply {
            onCreate(Bundle())
        }
    }
    val lastAppliedRecenterToken = remember { mutableIntStateOf(Int.MIN_VALUE) }
    val lastHadLocations = remember { mutableIntStateOf(0) }

    DisposableEffect(lifecycleOwner, mapView, onMarkerSelected, onMapTapped) {
        var mapReference: MapLibreMap? = null
        val clickListener = MapLibreMap.OnMapClickListener { latLng ->
            val map = mapReference ?: return@OnMapClickListener false
            val screenPoint = map.projection.toScreenLocation(latLng)
            val feature = map.queryRenderedFeatures(
                PointF(screenPoint.x, screenPoint.y),
                MarkerLayerId,
            ).firstOrNull()

            when {
                feature?.hasNonNullValueForProperty("memberId") == true -> {
                    onMarkerSelected(feature.getStringProperty("memberId"))
                    true
                }

                feature?.hasNonNullValueForProperty("clusterCount") == true -> {
                    map.animateCamera(
                        CameraUpdateFactory.newLatLngZoom(
                            latLng,
                            (map.cameraPosition.zoom + 1.5).coerceAtMost(16.0),
                        ),
                    )
                    true
                }

                else -> {
                    onMapTapped()
                    false
                }
            }
        }

        mapView.getMapAsync { map ->
            mapReference = map
            map.addOnMapClickListener(clickListener)
        }

        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> mapView.onStart()
                Lifecycle.Event.ON_RESUME -> mapView.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView.onPause()
                Lifecycle.Event.ON_STOP -> mapView.onStop()
                Lifecycle.Event.ON_DESTROY -> mapView.onDestroy()
                else -> Unit
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            mapReference?.removeOnMapClickListener(clickListener)
            lifecycleOwner.lifecycle.removeObserver(observer)
        }
    }

    AndroidView(
        modifier = modifier,
        factory = { mapView },
        update = { view ->
            view.getMapAsync { map ->
                map.setMinZoomPreference(1.0)
                map.uiSettings.isCompassEnabled = false
                val hasLocations = members.any { member -> member.latitude != null && member.longitude != null }
                val shouldAutoCenter = hasLocations && lastHadLocations.intValue == 0
                lastHadLocations.intValue = if (hasLocations) 1 else 0

                if (map.style?.uri != mapStyleUrl) {
                    map.setStyle(mapStyleUrl) {
                        renderMap(
                            context = context,
                            map = map,
                            members = members,
                            places = places,
                            selectedMemberId = selectedMemberId,
                            visualColors = visualColors,
                        )
                        applyCamera(
                            map = map,
                            members = members,
                            selectedMemberId = selectedMemberId,
                        )
                        lastAppliedRecenterToken.intValue = recenterToken
                    }
                } else {
                    renderMap(
                        context = context,
                        map = map,
                        members = members,
                        places = places,
                        selectedMemberId = selectedMemberId,
                        visualColors = visualColors,
                    )
                    if (shouldAutoCenter || recenterToken != lastAppliedRecenterToken.intValue) {
                        applyCamera(
                            map = map,
                            members = members,
                            selectedMemberId = selectedMemberId,
                        )
                        lastAppliedRecenterToken.intValue = recenterToken
                    }
                }
            }
        },
    )
}

private fun renderMap(
    context: Context,
    map: MapLibreMap,
    members: List<FamilyMemberUiModel>,
    places: List<MapPlaceUiModel>,
    selectedMemberId: String?,
    visualColors: MapVisualColors,
) {
    val style = map.style ?: return
    val markerFeatures = mutableListOf<Feature>()
    val markerClusters = MapSnapshotCalculator.groupMarkerPoints(
        points = members.mapNotNull { member ->
            val latitude = member.latitude ?: return@mapNotNull null
            val longitude = member.longitude ?: return@mapNotNull null
            MapSnapshotCalculator.MarkerPoint(
                item = member,
                latitude = latitude,
                longitude = longitude,
            )
        },
        groupingRadiusMeters = MarkerGroupingRadiusMeters,
    )

    markerClusters.forEach { cluster ->
        val clusterIsSelected = cluster.items.any { member -> member.id == selectedMemberId }
        val isSingleMember = cluster.items.size == 1
        val representative = cluster.items.firstOrNull() ?: return@forEach
        val iconKey = if (isSingleMember) {
            memberMarkerImageKey(
                initials = representative.initials,
                isSelected = clusterIsSelected,
                presenceState = representative.presenceState,
            )
        } else {
            clusterMarkerImageKey(count = cluster.items.size, isSelected = clusterIsSelected)
        }
        style.addImage(
            iconKey,
            if (isSingleMember) {
                createMemberMarkerBitmap(
                    context = context,
                    initials = representative.initials,
                    presenceState = representative.presenceState,
                    isSelected = clusterIsSelected,
                    visualColors = visualColors,
                )
            } else {
                createClusterMarkerBitmap(
                    context = context,
                    count = cluster.items.size,
                    isSelected = clusterIsSelected,
                    visualColors = visualColors,
                )
            },
        )

        val feature = Feature.fromGeometry(Point.fromLngLat(cluster.longitude, cluster.latitude)).apply {
            addStringProperty("iconKey", iconKey)
            if (isSingleMember) {
                addStringProperty("memberId", representative.id)
            } else {
                addNumberProperty("clusterCount", cluster.items.size)
            }
        }
        markerFeatures += feature
    }

    style.upsertGeoJsonSource(
        MarkerSourceId,
        FeatureCollection.fromFeatures(markerFeatures),
    )
    style.ensureSymbolLayer(
        layerId = MarkerLayerId,
        sourceId = MarkerSourceId,
        properties = markerIconProperties(get("iconKey")),
    )
    renderSavedPlaces(
        style = style,
        places = places,
        visualColors = visualColors,
    )
}

private fun renderSavedPlaces(
    style: org.maplibre.android.maps.Style,
    places: List<MapPlaceUiModel>,
    visualColors: MapVisualColors,
) {
    val features = buildList {
        places.forEach { place ->
            add(
                Feature.fromGeometry(Point.fromLngLat(place.longitude, place.latitude)).apply {
                    addStringProperty("kind", "center")
                    addStringProperty("label", place.name)
                },
            )
            add(
                Feature.fromGeometry(
                    LineString.fromLngLats(
                        buildRadiusRing(
                            latitude = place.latitude,
                            longitude = place.longitude,
                            radiusMeters = place.radiusMeters,
                        ).map { point ->
                            Point.fromLngLat(point.longitude, point.latitude)
                        },
                    ),
                ).apply {
                    addStringProperty("kind", "ring")
                },
            )
        }
    }
    style.upsertGeoJsonSource(
        SavedPlaceSourceId,
        FeatureCollection.fromFeatures(features),
    )
    style.ensureLineLayer(
        layerId = SavedPlaceRingLayerId,
        sourceId = SavedPlaceSourceId,
        color = visualColors.placeRing,
        width = 2f,
        belowLayerId = MarkerLayerId,
        filter = eq(get("kind"), "ring"),
    )
    style.ensureCircleLayer(
        layerId = SavedPlaceCenterLayerId,
        sourceId = SavedPlaceSourceId,
        color = visualColors.placeCenter,
        radius = 4.5f,
        strokeColor = visualColors.white,
        strokeWidth = 1.5f,
        belowLayerId = MarkerLayerId,
        filter = eq(get("kind"), "center"),
    )
    style.ensureSymbolLayer(
        layerId = SavedPlaceLabelLayerId,
        sourceId = SavedPlaceSourceId,
        properties = labelProperties(get("label"), 10f),
        belowLayerId = MarkerLayerId,
        filter = eq(get("kind"), "center"),
    )
}

private fun applyCamera(
    map: MapLibreMap,
    members: List<FamilyMemberUiModel>,
    selectedMemberId: String?,
) {
    val selectedMember = members.firstOrNull { member ->
        member.id == selectedMemberId && member.latitude != null && member.longitude != null
    }
    if (selectedMember != null) {
        map.animateCamera(
            CameraUpdateFactory.newCameraPosition(
                CameraPosition.Builder()
                    .target(LatLng(selectedMember.latitude!!, selectedMember.longitude!!))
                    .zoom(SelectedMemberZoom)
                    .build(),
            ),
        )
        return
    }

    val positions = members.mapNotNull { member ->
        val latitude = member.latitude ?: return@mapNotNull null
        val longitude = member.longitude ?: return@mapNotNull null
        LatLng(latitude, longitude)
    }
    when {
        positions.isEmpty() -> {
            map.cameraPosition = CameraPosition.Builder()
                .target(LatLng(20.0, 0.0))
                .zoom(1.2)
                .build()
        }

        positions.size == 1 -> {
            map.animateCamera(
                CameraUpdateFactory.newLatLngZoom(
                    positions.first(),
                    MaximumAutoZoom,
                ),
            )
        }

        else -> {
            val bounds = LatLngBounds.Builder().also { builder ->
                positions.forEach(builder::include)
            }.build()
            runCatching {
                map.getCameraForLatLngBounds(bounds, intArrayOf(128, 180, 128, 180), 0.0, 0.0)
            }.getOrNull()?.let { cameraPosition ->
                map.animateCamera(
                    CameraUpdateFactory.newCameraPosition(
                        CameraPosition.Builder(cameraPosition)
                            .zoom(MapSnapshotCalculator.clampAutoZoom(cameraPosition.zoom, MaximumAutoZoom))
                            .build(),
                    ),
                )
            }
        }
    }
}

private fun buildStatusPillLabel(
    memberCount: Int,
    staleCount: Int,
    isRefreshing: Boolean,
): String {
    return when {
        isRefreshing -> "Updating family locations"
        memberCount == 0 -> "No members visible"
        staleCount > 0 -> "$memberCount members visible · $staleCount stale"
        else -> "$memberCount members visible"
    }
}

private fun memberMarkerImageKey(
    initials: String,
    isSelected: Boolean,
    presenceState: PresenceState,
) = "member-$initials-${presenceState.name}-${if (isSelected) 1 else 0}"

private fun clusterMarkerImageKey(
    count: Int,
    isSelected: Boolean,
) = "cluster-$count-${if (isSelected) 1 else 0}"

private fun createMemberMarkerBitmap(
    context: Context,
    initials: String,
    presenceState: PresenceState,
    isSelected: Boolean,
    visualColors: MapVisualColors,
) = Bitmap.createBitmap(112, 112, Bitmap.Config.ARGB_8888).apply {
    val canvas = Canvas(this)
    val ringColor = when (presenceState) {
        PresenceState.LIVE -> visualColors.live
        PresenceState.STALE -> visualColors.stale
        PresenceState.OFFLINE -> visualColors.offline
        PresenceState.UNKNOWN -> visualColors.offline
    }
    val outerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = if (isSelected) visualColors.accent else ringColor
    }
    val innerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = visualColors.markerFill
    }
    val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = visualColors.text
        textAlign = Paint.Align.CENTER
        textSize = context.resources.displayMetrics.density * 16f
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
    }
    val centerX = width / 2f
    val centerY = height / 2f
    canvas.drawCircle(centerX, centerY, width * 0.30f, outerPaint)
    canvas.drawCircle(centerX, centerY, width * 0.25f, innerPaint)
    val baseline = centerY - (textPaint.descent() + textPaint.ascent()) / 2f
    canvas.drawText(initials, centerX, baseline, textPaint)
}

private fun createClusterMarkerBitmap(
    context: Context,
    count: Int,
    isSelected: Boolean,
    visualColors: MapVisualColors,
) = Bitmap.createBitmap(112, 112, Bitmap.Config.ARGB_8888).apply {
    val canvas = Canvas(this)
    val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = if (isSelected) visualColors.accent else visualColors.background
    }
    val outlinePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = visualColors.white
        style = Paint.Style.STROKE
        strokeWidth = context.resources.displayMetrics.density * 2.5f
    }
    val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = visualColors.text
        textAlign = Paint.Align.CENTER
        textSize = context.resources.displayMetrics.density * 16f
        typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
    }
    val centerX = width / 2f
    val centerY = height / 2f
    canvas.drawCircle(centerX, centerY, width * 0.28f, fillPaint)
    canvas.drawCircle(centerX, centerY, width * 0.28f, outlinePaint)
    val baseline = centerY - (textPaint.descent() + textPaint.ascent()) / 2f
    canvas.drawText(count.toString(), centerX, baseline, textPaint)
}

private data class MapVisualColors(
    val background: Int,
    val markerFill: Int,
    val accent: Int,
    val live: Int,
    val stale: Int,
    val offline: Int,
    val text: Int,
    val placeRing: Int,
    val placeCenter: Int,
    val white: Int,
)
