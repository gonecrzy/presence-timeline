package com.gonecrzy.gpstrack.ui.map

import org.maplibre.android.maps.Style
import org.maplibre.android.style.expressions.Expression
import org.maplibre.android.style.layers.CircleLayer
import org.maplibre.android.style.layers.LineLayer
import org.maplibre.android.style.layers.PropertyFactory.circleColor
import org.maplibre.android.style.layers.PropertyFactory.circleRadius
import org.maplibre.android.style.layers.PropertyFactory.circleStrokeColor
import org.maplibre.android.style.layers.PropertyFactory.circleStrokeWidth
import org.maplibre.android.style.layers.PropertyFactory.iconAllowOverlap
import org.maplibre.android.style.layers.PropertyFactory.iconIgnorePlacement
import org.maplibre.android.style.layers.PropertyFactory.iconImage
import org.maplibre.android.style.layers.PropertyFactory.lineCap
import org.maplibre.android.style.layers.PropertyFactory.lineColor
import org.maplibre.android.style.layers.PropertyFactory.lineJoin
import org.maplibre.android.style.layers.PropertyFactory.lineWidth
import org.maplibre.android.style.layers.PropertyFactory.textAllowOverlap
import org.maplibre.android.style.layers.PropertyFactory.textColor
import org.maplibre.android.style.layers.PropertyFactory.textField
import org.maplibre.android.style.layers.PropertyFactory.textHaloColor
import org.maplibre.android.style.layers.PropertyFactory.textHaloWidth
import org.maplibre.android.style.layers.PropertyFactory.textIgnorePlacement
import org.maplibre.android.style.layers.PropertyFactory.textOffset
import org.maplibre.android.style.layers.PropertyFactory.textSize
import org.maplibre.android.style.layers.PropertyValue
import org.maplibre.android.style.layers.SymbolLayer
import org.maplibre.android.style.sources.GeoJsonSource
import org.maplibre.geojson.FeatureCollection

fun Style.upsertGeoJsonSource(
    sourceId: String,
    features: FeatureCollection,
) {
    val existing = getSourceAs<GeoJsonSource>(sourceId)
    if (existing != null) {
        existing.setGeoJson(features)
    } else {
        addSource(GeoJsonSource(sourceId, features))
    }
}

fun Style.ensureLineLayer(
    layerId: String,
    sourceId: String,
    color: Int,
    width: Float,
    belowLayerId: String? = null,
    filter: Expression? = null,
) {
    val layer = getLayerAs<LineLayer>(layerId) ?: LineLayer(layerId, sourceId).also { newLayer ->
        if (belowLayerId != null && getLayer(belowLayerId) != null) {
            addLayerBelow(newLayer, belowLayerId)
        } else {
            addLayer(newLayer)
        }
    }
    layer.setProperties(
        lineColor(color),
        lineWidth(width),
        lineCap("round"),
        lineJoin("round"),
    )
    if (filter != null) {
        layer.setFilter(filter)
    }
}

fun Style.ensureCircleLayer(
    layerId: String,
    sourceId: String,
    color: Int,
    radius: Float,
    strokeColor: Int,
    strokeWidth: Float,
    belowLayerId: String? = null,
    filter: Expression? = null,
) {
    val layer = getLayerAs<CircleLayer>(layerId) ?: CircleLayer(layerId, sourceId).also { newLayer ->
        if (belowLayerId != null && getLayer(belowLayerId) != null) {
            addLayerBelow(newLayer, belowLayerId)
        } else {
            addLayer(newLayer)
        }
    }
    layer.setProperties(
        circleColor(color),
        circleRadius(radius),
        circleStrokeColor(strokeColor),
        circleStrokeWidth(strokeWidth),
    )
    if (filter != null) {
        layer.setFilter(filter)
    }
}

fun Style.ensureSymbolLayer(
    layerId: String,
    sourceId: String,
    properties: Array<out PropertyValue<*>>,
    belowLayerId: String? = null,
    filter: Expression? = null,
) {
    val layer = getLayerAs<SymbolLayer>(layerId) ?: SymbolLayer(layerId, sourceId).also { newLayer ->
        if (belowLayerId != null && getLayer(belowLayerId) != null) {
            addLayerBelow(newLayer, belowLayerId)
        } else {
            addLayer(newLayer)
        }
    }
    layer.setProperties(*properties)
    if (filter != null) {
        layer.setFilter(filter)
    }
}

fun markerIconProperties(iconExpression: Expression): Array<PropertyValue<*>> = arrayOf(
    iconImage(iconExpression),
    iconAllowOverlap(true),
    iconIgnorePlacement(true),
)

fun labelProperties(
    textExpression: Expression,
    textSizeSp: Float,
) = arrayOf(
    textField(textExpression),
    textSize(textSizeSp),
    textColor("#FFFFFF"),
    textHaloColor("#102132"),
    textHaloWidth(1.5f),
    textOffset(arrayOf(0f, 1.4f)),
    textAllowOverlap(true),
    textIgnorePlacement(true),
)
