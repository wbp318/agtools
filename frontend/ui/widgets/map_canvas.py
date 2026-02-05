"""
Map Canvas Widget for AgTools GIS

Leaflet-based map widget using PyQt6 WebEngineView with Python-JavaScript bridge.
Supports viewing/editing GeoJSON layers, drawing tools, and measurement.

AgTools v6.16.0
"""

import json
import logging
from typing import Optional, List, Dict, Any, Callable

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QUrl
from PyQt6.QtWebChannel import QWebChannel

logger = logging.getLogger(__name__)

# Try to import WebEngine (optional dependency)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
    logger.warning("PyQt6-WebEngine not installed. Map canvas will be disabled.")


# ============================================================================
# JAVASCRIPT BRIDGE
# ============================================================================

class MapBridge(QObject):
    """
    Bridge between Python and JavaScript for map interactions.

    Signals are emitted when the user interacts with the map in JavaScript.
    Slots can be called from JavaScript to pass data back to Python.
    """

    # Signals emitted from JavaScript actions
    feature_clicked = pyqtSignal(int, dict)  # feature_id, properties
    feature_drawn = pyqtSignal(dict)  # GeoJSON geometry
    feature_edited = pyqtSignal(int, dict)  # feature_id, new geometry
    map_clicked = pyqtSignal(float, float)  # lat, lng
    bounds_changed = pyqtSignal(dict)  # bounds dict
    measurement_complete = pyqtSignal(float, str)  # value, unit

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(int, str)
    def onFeatureClicked(self, feature_id: int, properties_json: str):
        """Called from JavaScript when a feature is clicked."""
        try:
            properties = json.loads(properties_json) if properties_json else {}
            self.feature_clicked.emit(feature_id, properties)
        except json.JSONDecodeError:
            self.feature_clicked.emit(feature_id, {})

    @pyqtSlot(str)
    def onFeatureDrawn(self, geometry_json: str):
        """Called from JavaScript when a new feature is drawn."""
        try:
            geometry = json.loads(geometry_json)
            self.feature_drawn.emit(geometry)
        except json.JSONDecodeError:
            logger.error("Invalid GeoJSON from draw operation")

    @pyqtSlot(int, str)
    def onFeatureEdited(self, feature_id: int, geometry_json: str):
        """Called from JavaScript when a feature is edited."""
        try:
            geometry = json.loads(geometry_json)
            self.feature_edited.emit(feature_id, geometry)
        except json.JSONDecodeError:
            logger.error("Invalid GeoJSON from edit operation")

    @pyqtSlot(float, float)
    def onMapClicked(self, lat: float, lng: float):
        """Called from JavaScript when the map is clicked."""
        self.map_clicked.emit(lat, lng)

    @pyqtSlot(str)
    def onBoundsChanged(self, bounds_json: str):
        """Called from JavaScript when map bounds change."""
        try:
            bounds = json.loads(bounds_json)
            self.bounds_changed.emit(bounds)
        except json.JSONDecodeError:
            pass

    @pyqtSlot(float, str)
    def onMeasurementComplete(self, value: float, unit: str):
        """Called from JavaScript when a measurement is complete."""
        self.measurement_complete.emit(value, unit)


# ============================================================================
# MAP CANVAS WIDGET
# ============================================================================

class MapCanvas(QFrame):
    """
    Leaflet-based map canvas widget.

    Features:
    - Display OpenStreetMap and satellite imagery base maps
    - Load and display GeoJSON layers
    - Drawing tools (polygon, point, line)
    - Editing existing features
    - Measurement tools (area, distance)
    - Coordinate display
    """

    # Signals
    feature_clicked = pyqtSignal(int, dict)
    feature_drawn = pyqtSignal(dict)
    feature_edited = pyqtSignal(int, dict)
    map_clicked = pyqtSignal(float, float)
    coordinates_changed = pyqtSignal(float, float)  # Cursor position

    # Default map center (central US)
    DEFAULT_CENTER = (39.8283, -98.5795)
    DEFAULT_ZOOM = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layers: Dict[str, Dict[str, Any]] = {}
        self._current_tool = "pan"
        self._is_ready = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the map UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not HAS_WEBENGINE:
            # Show placeholder if WebEngine is not available
            from PyQt6.QtWidgets import QLabel
            from PyQt6.QtCore import Qt
            placeholder = QLabel("Map view requires PyQt6-WebEngine.\nInstall with: pip install PyQt6-WebEngine")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    background: #f0f0f0;
                    color: #666;
                    font-size: 14px;
                    border: 2px dashed #ccc;
                    padding: 40px;
                }
            """)
            layout.addWidget(placeholder)
            return

        # Create web view
        self._web_view = QWebEngineView()
        self._web_view.setMinimumSize(400, 300)

        # Setup web channel for Python-JavaScript communication
        self._bridge = MapBridge(self)
        self._channel = QWebChannel()
        self._channel.registerObject("bridge", self._bridge)
        self._web_view.page().setWebChannel(self._channel)

        # Connect bridge signals
        self._bridge.feature_clicked.connect(self.feature_clicked.emit)
        self._bridge.feature_drawn.connect(self.feature_drawn.emit)
        self._bridge.feature_edited.connect(self.feature_edited.emit)
        self._bridge.map_clicked.connect(self.map_clicked.emit)

        # Load map HTML
        html_content = self._generate_map_html()
        self._web_view.setHtml(html_content)

        layout.addWidget(self._web_view)

    def _generate_map_html(self) -> str:
        """Generate the HTML/JavaScript for the Leaflet map."""
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgTools Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        * {{ margin: 0; padding: 0; }}
        html, body {{ height: 100%; width: 100%; }}
        #map {{ height: 100%; width: 100%; }}
        .leaflet-control-layers {{ max-height: 300px; overflow-y: auto; }}
        .info-popup {{ font-family: Tahoma, sans-serif; font-size: 12px; }}
        .info-popup h4 {{ margin: 0 0 5px 0; color: #00868B; }}
        .info-popup table {{ border-collapse: collapse; }}
        .info-popup td {{ padding: 2px 8px 2px 0; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Initialize bridge
        var bridge = null;
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            bridge = channel.objects.bridge;
            mapReady();
        }});

        // Initialize map
        var map = L.map('map', {{
            center: [{self.DEFAULT_CENTER[0]}, {self.DEFAULT_CENTER[1]}],
            zoom: {self.DEFAULT_ZOOM},
            zoomControl: true
        }});

        // Base layers
        var osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);

        var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri',
            maxZoom: 19
        }});

        var topoLayer = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenTopoMap',
            maxZoom: 17
        }});

        // Layer control
        var baseMaps = {{
            "OpenStreetMap": osmLayer,
            "Satellite": satelliteLayer,
            "Topographic": topoLayer
        }};
        var overlays = {{}};
        var layerControl = L.control.layers(baseMaps, overlays).addTo(map);

        // Drawing tools
        var drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

        var drawControl = new L.Control.Draw({{
            draw: {{
                polygon: {{
                    shapeOptions: {{
                        color: '#00868B',
                        fillColor: '#00868B',
                        fillOpacity: 0.3
                    }}
                }},
                polyline: false,
                rectangle: false,
                circle: false,
                circlemarker: false,
                marker: {{
                    icon: L.icon({{
                        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41]
                    }})
                }}
            }},
            edit: {{
                featureGroup: drawnItems
            }}
        }});

        var drawControlEnabled = false;

        // Store GeoJSON layers
        var geoJsonLayers = {{}};
        var currentTool = 'pan';

        // Map events
        map.on('click', function(e) {{
            if (bridge && currentTool === 'pan') {{
                bridge.onMapClicked(e.latlng.lat, e.latlng.lng);
            }}
        }});

        map.on('moveend', function() {{
            if (bridge) {{
                var bounds = map.getBounds();
                bridge.onBoundsChanged(JSON.stringify({{
                    north: bounds.getNorth(),
                    south: bounds.getSouth(),
                    east: bounds.getEast(),
                    west: bounds.getWest()
                }}));
            }}
        }});

        map.on('mousemove', function(e) {{
            // Update coordinate display (handled in Python)
        }});

        // Draw events
        map.on(L.Draw.Event.CREATED, function(e) {{
            var layer = e.layer;
            drawnItems.addLayer(layer);
            if (bridge) {{
                var geojson = layer.toGeoJSON();
                bridge.onFeatureDrawn(JSON.stringify(geojson.geometry));
            }}
        }});

        map.on(L.Draw.Event.EDITED, function(e) {{
            e.layers.eachLayer(function(layer) {{
                if (bridge && layer.feature && layer.feature.id) {{
                    var geojson = layer.toGeoJSON();
                    bridge.onFeatureEdited(layer.feature.id, JSON.stringify(geojson.geometry));
                }}
            }});
        }});

        // Functions called from Python
        function mapReady() {{
            console.log('Map ready');
        }}

        function setView(lat, lng, zoom) {{
            map.setView([lat, lng], zoom);
        }}

        function fitBounds(south, west, north, east) {{
            map.fitBounds([[south, west], [north, east]]);
        }}

        function addGeoJsonLayer(layerId, geojsonStr, styleStr, layerName) {{
            var geojson = JSON.parse(geojsonStr);
            var style = JSON.parse(styleStr);

            // Remove existing layer with same ID
            if (geoJsonLayers[layerId]) {{
                map.removeLayer(geoJsonLayers[layerId]);
                layerControl.removeLayer(geoJsonLayers[layerId]);
            }}

            var layer = L.geoJSON(geojson, {{
                style: function(feature) {{
                    return {{
                        color: style.stroke_color || '#004040',
                        weight: style.stroke_width || 2,
                        opacity: style.stroke_opacity || 1,
                        fillColor: style.fill_color || '#00868B',
                        fillOpacity: style.fill_opacity || 0.3
                    }};
                }},
                pointToLayer: function(feature, latlng) {{
                    return L.circleMarker(latlng, {{
                        radius: style.point_radius || 6,
                        fillColor: style.fill_color || '#00868B',
                        color: style.stroke_color || '#004040',
                        weight: style.stroke_width || 2,
                        opacity: style.stroke_opacity || 1,
                        fillOpacity: style.fill_opacity || 0.5
                    }});
                }},
                onEachFeature: function(feature, layer) {{
                    // Click handler
                    layer.on('click', function(e) {{
                        if (bridge && feature.id) {{
                            bridge.onFeatureClicked(
                                feature.id,
                                JSON.stringify(feature.properties || {{}})
                            );
                        }}
                        L.DomEvent.stopPropagation(e);
                    }});

                    // Popup with properties
                    if (feature.properties) {{
                        var content = '<div class="info-popup">';
                        if (feature.properties.name) {{
                            content += '<h4>' + feature.properties.name + '</h4>';
                        }}
                        content += '<table>';
                        for (var key in feature.properties) {{
                            if (key !== 'name' && feature.properties[key]) {{
                                content += '<tr><td><b>' + key + ':</b></td><td>' + feature.properties[key] + '</td></tr>';
                            }}
                        }}
                        content += '</table></div>';
                        layer.bindPopup(content);
                    }}
                }}
            }}).addTo(map);

            geoJsonLayers[layerId] = layer;
            layerControl.addOverlay(layer, layerName || layerId);
        }}

        function removeLayer(layerId) {{
            if (geoJsonLayers[layerId]) {{
                map.removeLayer(geoJsonLayers[layerId]);
                layerControl.removeLayer(geoJsonLayers[layerId]);
                delete geoJsonLayers[layerId];
            }}
        }}

        function setLayerVisibility(layerId, visible) {{
            if (geoJsonLayers[layerId]) {{
                if (visible) {{
                    map.addLayer(geoJsonLayers[layerId]);
                }} else {{
                    map.removeLayer(geoJsonLayers[layerId]);
                }}
            }}
        }}

        function clearAllLayers() {{
            for (var id in geoJsonLayers) {{
                map.removeLayer(geoJsonLayers[id]);
                layerControl.removeLayer(geoJsonLayers[id]);
            }}
            geoJsonLayers = {{}};
            drawnItems.clearLayers();
        }}

        function enableDrawing(enabled) {{
            if (enabled && !drawControlEnabled) {{
                map.addControl(drawControl);
                drawControlEnabled = true;
            }} else if (!enabled && drawControlEnabled) {{
                map.removeControl(drawControl);
                drawControlEnabled = false;
            }}
        }}

        function setTool(tool) {{
            currentTool = tool;
            enableDrawing(tool === 'draw' || tool === 'edit');
        }}

        function zoomToLayer(layerId) {{
            if (geoJsonLayers[layerId]) {{
                map.fitBounds(geoJsonLayers[layerId].getBounds());
            }}
        }}

        function highlightFeature(layerId, featureId) {{
            // Highlight a specific feature
            if (geoJsonLayers[layerId]) {{
                geoJsonLayers[layerId].eachLayer(function(layer) {{
                    if (layer.feature && layer.feature.id === featureId) {{
                        layer.setStyle({{
                            color: '#FF6600',
                            weight: 4
                        }});
                        layer.openPopup();
                    }}
                }});
            }}
        }}
    </script>
</body>
</html>
'''

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_view(self, lat: float, lng: float, zoom: int = 14) -> None:
        """Set the map center and zoom level."""
        if HAS_WEBENGINE:
            self._run_js(f"setView({lat}, {lng}, {zoom})")

    def fit_bounds(self, south: float, west: float, north: float, east: float) -> None:
        """Fit the map to the given bounds."""
        if HAS_WEBENGINE:
            self._run_js(f"fitBounds({south}, {west}, {north}, {east})")

    def add_geojson_layer(
        self,
        layer_id: str,
        geojson: Dict[str, Any],
        style: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> None:
        """
        Add a GeoJSON layer to the map.

        Args:
            layer_id: Unique identifier for the layer
            geojson: GeoJSON data (dict)
            style: Optional style dict with fill_color, stroke_color, etc.
            name: Display name for layer control
        """
        if not HAS_WEBENGINE:
            return

        self._layers[layer_id] = {
            "geojson": geojson,
            "style": style or {},
            "name": name or layer_id
        }

        geojson_str = json.dumps(geojson).replace("'", "\\'")
        style_str = json.dumps(style or {}).replace("'", "\\'")
        name_escaped = (name or layer_id).replace("'", "\\'")

        self._run_js(f"addGeoJsonLayer('{layer_id}', '{geojson_str}', '{style_str}', '{name_escaped}')")

    def remove_layer(self, layer_id: str) -> None:
        """Remove a layer from the map."""
        if HAS_WEBENGINE:
            self._layers.pop(layer_id, None)
            self._run_js(f"removeLayer('{layer_id}')")

    def set_layer_visibility(self, layer_id: str, visible: bool) -> None:
        """Set visibility of a layer."""
        if HAS_WEBENGINE:
            self._run_js(f"setLayerVisibility('{layer_id}', {'true' if visible else 'false'})")

    def clear_all_layers(self) -> None:
        """Remove all layers from the map."""
        if HAS_WEBENGINE:
            self._layers.clear()
            self._run_js("clearAllLayers()")

    def enable_drawing(self, enabled: bool = True) -> None:
        """Enable or disable drawing tools."""
        if HAS_WEBENGINE:
            self._run_js(f"enableDrawing({'true' if enabled else 'false'})")

    def set_tool(self, tool: str) -> None:
        """
        Set the current map tool.

        Args:
            tool: One of 'pan', 'draw', 'edit', 'measure'
        """
        self._current_tool = tool
        if HAS_WEBENGINE:
            self._run_js(f"setTool('{tool}')")

    def zoom_to_layer(self, layer_id: str) -> None:
        """Zoom the map to fit a layer's bounds."""
        if HAS_WEBENGINE:
            self._run_js(f"zoomToLayer('{layer_id}')")

    def highlight_feature(self, layer_id: str, feature_id: int) -> None:
        """Highlight a specific feature."""
        if HAS_WEBENGINE:
            self._run_js(f"highlightFeature('{layer_id}', {feature_id})")

    def get_current_tool(self) -> str:
        """Get the current tool name."""
        return self._current_tool

    def _run_js(self, script: str) -> None:
        """Execute JavaScript in the web view."""
        if HAS_WEBENGINE and hasattr(self, '_web_view'):
            self._web_view.page().runJavaScript(script)


# ============================================================================
# SIMPLE FALLBACK MAP (No WebEngine)
# ============================================================================

class SimpleMapCanvas(QFrame):
    """
    Simple fallback map canvas when WebEngine is not available.
    Displays a static placeholder with field list.
    """

    feature_clicked = pyqtSignal(int, dict)
    feature_drawn = pyqtSignal(dict)
    feature_edited = pyqtSignal(int, dict)
    map_clicked = pyqtSignal(float, float)
    coordinates_changed = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        from PyQt6.QtWidgets import QLabel, QListWidget
        from PyQt6.QtCore import Qt

        layout = QVBoxLayout(self)

        header = QLabel("Map View (Simplified)")
        header.setStyleSheet("font-weight: bold; font-size: 14px; color: #00868B;")
        layout.addWidget(header)

        info = QLabel("Install PyQt6-WebEngine for interactive maps:\npip install PyQt6-WebEngine")
        info.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info)

        self._field_list = QListWidget()
        self._field_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #00868B;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background: #00868B;
                color: white;
            }
        """)
        layout.addWidget(self._field_list)

    def set_view(self, lat: float, lng: float, zoom: int = 14) -> None:
        pass

    def fit_bounds(self, south: float, west: float, north: float, east: float) -> None:
        pass

    def add_geojson_layer(self, layer_id: str, geojson: Dict, style: Dict = None, name: str = None) -> None:
        # Add features to list
        if "features" in geojson:
            for feature in geojson["features"]:
                props = feature.get("properties", {})
                name = props.get("name", f"Feature {feature.get('id', '?')}")
                self._field_list.addItem(name)

    def remove_layer(self, layer_id: str) -> None:
        pass

    def set_layer_visibility(self, layer_id: str, visible: bool) -> None:
        pass

    def clear_all_layers(self) -> None:
        self._field_list.clear()

    def enable_drawing(self, enabled: bool = True) -> None:
        pass

    def set_tool(self, tool: str) -> None:
        pass

    def zoom_to_layer(self, layer_id: str) -> None:
        pass

    def highlight_feature(self, layer_id: str, feature_id: int) -> None:
        pass

    def get_current_tool(self) -> str:
        return "pan"


def create_map_canvas(parent=None) -> QFrame:
    """Factory function to create the appropriate map canvas."""
    if HAS_WEBENGINE:
        return MapCanvas(parent)
    else:
        return SimpleMapCanvas(parent)
