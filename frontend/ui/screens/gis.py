"""
AgTools GIS Screen

QGIS-inspired GIS interface with map canvas, layer panel, and toolbar.
Features field boundary viewing/editing, layer management, and QGIS integration.

AgTools v6.16.0
"""

import json
import logging
import subprocess
import os
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTreeWidget, QTreeWidgetItem, QSplitter, QToolBar, QToolButton,
    QMessageBox, QFileDialog, QMenu, QDialog, QFormLayout, QLineEdit,
    QComboBox, QDoubleSpinBox, QDialogButtonBox, QColorDialog, QStatusBar,
    QGroupBox, QCheckBox, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QColor, QAction, QIcon

from ui.retro_styles import RETRO_COLORS
from ui.widgets.map_canvas import create_map_canvas, HAS_WEBENGINE
from api.gis_api import get_gis_api, LayerStyle

logger = logging.getLogger(__name__)


# ============================================================================
# STYLING
# ============================================================================

COLORS = {
    "primary": RETRO_COLORS["turquoise_dark"],
    "primary_light": RETRO_COLORS["turquoise_light"],
    "surface": RETRO_COLORS["cream"],
    "card_bg": RETRO_COLORS["window_face"],
    "border": RETRO_COLORS["turquoise_medium"],
    "text": RETRO_COLORS["text_black"],
    "text_secondary": RETRO_COLORS["text_light"],
}


# ============================================================================
# LAYER PANEL
# ============================================================================

class LayerPanel(QFrame):
    """
    Layer panel for managing map layers (QGIS-style).

    Features:
    - Tree view of layers with checkboxes for visibility
    - Right-click context menu for layer operations
    - Drag to reorder layers
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._gis_api = get_gis_api()

    def _setup_ui(self) -> None:
        self.setFixedWidth(220)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border: none;
                border-radius: 4px 4px 0 0;
                padding: 8px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("Layers")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add layer button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setToolTip("Add Layer")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.2);
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.4);
            }
        """)
        add_btn.clicked.connect(self._on_add_layer)
        header_layout.addWidget(add_btn)

        layout.addWidget(header)

        # Layer tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(15)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {COLORS['surface']};
                border: none;
                border-radius: 0 0 4px 4px;
            }}
            QTreeWidget::item {{
                padding: 4px 2px;
            }}
            QTreeWidget::item:selected {{
                background: {COLORS['primary']};
                color: white;
            }}
            QTreeWidget::indicator {{
                width: 16px;
                height: 16px;
            }}
            QTreeWidget::indicator:checked {{
                background: {COLORS['primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
            }}
            QTreeWidget::indicator:unchecked {{
                background: white;
                border: 1px solid {COLORS['border']};
                border-radius: 2px;
            }}
        """)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.itemChanged.connect(self._on_item_changed)

        layout.addWidget(self._tree)

        # Add default layers
        self._add_default_layers()

    def _add_default_layers(self) -> None:
        """Add default layer items."""
        # Fields layer (always present)
        fields_item = QTreeWidgetItem(["Fields"])
        fields_item.setFlags(fields_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        fields_item.setCheckState(0, Qt.CheckState.Checked)
        fields_item.setData(0, Qt.ItemDataRole.UserRole, {"id": "fields", "type": "builtin"})
        self._tree.addTopLevelItem(fields_item)

    def add_layer(self, layer_id: str, name: str, layer_type: str = "vector", visible: bool = True) -> None:
        """Add a layer to the panel."""
        item = QTreeWidgetItem([name])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, {"id": layer_id, "type": layer_type})
        self._tree.addTopLevelItem(item)

    def remove_layer(self, layer_id: str) -> None:
        """Remove a layer from the panel."""
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("id") == layer_id:
                self._tree.takeTopLevelItem(i)
                break

    def get_visible_layers(self) -> List[str]:
        """Get list of visible layer IDs."""
        visible = []
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data:
                    visible.append(data.get("id"))
        return visible

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle layer visibility toggle."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            layer_id = data.get("id")
            visible = item.checkState(0) == Qt.CheckState.Checked
            # Emit signal to update map
            parent = self.parent()
            if parent and hasattr(parent, '_map_canvas'):
                parent._map_canvas.set_layer_visibility(layer_id, visible)

    def _show_context_menu(self, pos) -> None:
        """Show layer context menu."""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu(self)

        zoom_action = menu.addAction("Zoom to Layer")
        zoom_action.triggered.connect(lambda: self._zoom_to_layer(data.get("id")))

        if data.get("type") != "builtin":
            menu.addSeparator()
            style_action = menu.addAction("Style...")
            style_action.triggered.connect(lambda: self._edit_style(data.get("id")))

            menu.addSeparator()
            remove_action = menu.addAction("Remove Layer")
            remove_action.triggered.connect(lambda: self._remove_layer(data.get("id")))

        menu.exec(self._tree.mapToGlobal(pos))

    def _zoom_to_layer(self, layer_id: str) -> None:
        """Zoom map to layer."""
        parent = self.parent()
        if parent and hasattr(parent, '_map_canvas'):
            parent._map_canvas.zoom_to_layer(layer_id)

    def _edit_style(self, layer_id: str) -> None:
        """Open style editor for layer."""
        # TODO: Implement style dialog
        pass

    def _remove_layer(self, layer_id: str) -> None:
        """Remove a layer."""
        reply = QMessageBox.question(
            self, "Remove Layer",
            "Remove this layer from the map?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.remove_layer(layer_id)
            parent = self.parent()
            if parent and hasattr(parent, '_map_canvas'):
                parent._map_canvas.remove_layer(layer_id)

    def _on_add_layer(self) -> None:
        """Add a new layer."""
        # Show add layer dialog
        parent = self.parent()
        if parent and hasattr(parent, '_add_layer_dialog'):
            parent._add_layer_dialog()


# ============================================================================
# PROPERTIES PANEL
# ============================================================================

class PropertiesPanel(QFrame):
    """Panel showing properties of selected feature."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFixedWidth(250)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['primary_light']});
                border: none;
                border-radius: 4px 4px 0 0;
                padding: 8px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("Properties")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 12px; background: transparent;")
        header_layout.addWidget(title)

        layout.addWidget(header)

        # Content area
        self._content = QWidget()
        self._content.setStyleSheet(f"background: {COLORS['surface']};")
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(8, 8, 8, 8)

        self._props_label = QLabel("Select a feature to view properties")
        self._props_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 20px;")
        self._props_label.setWordWrap(True)
        self._props_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self._props_label)

        content_layout.addStretch()

        layout.addWidget(self._content)

    def show_properties(self, feature_id: int, properties: Dict[str, Any]) -> None:
        """Display feature properties."""
        if not properties:
            self._props_label.setText("No properties available")
            return

        html = f"<b>Feature ID:</b> {feature_id}<br><br>"
        for key, value in properties.items():
            if value is not None:
                html += f"<b>{key}:</b> {value}<br>"

        self._props_label.setText(html)
        self._props_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def clear(self) -> None:
        """Clear properties display."""
        self._props_label.setText("Select a feature to view properties")
        self._props_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


# ============================================================================
# MAIN GIS SCREEN
# ============================================================================

class GISScreen(QWidget):
    """
    Main GIS screen with QGIS-inspired layout.

    Layout:
    ┌─────────────────────────────────────────────────────────────┐
    │ Toolbar: [Pan] [Zoom] [Select] [Draw] │ [Open QGIS] [Export]│
    ├────────────┬────────────────────────────────────────────────┤
    │ Layers     │                                                │
    │ Panel      │              Map Canvas                        │
    │            │           (Leaflet WebView)                    │
    │ ☑ Fields   │                                                │
    │ ☑ Soil     │                                                │
    │ ☐ Yield    │                                                │
    ├────────────┴────────────────────────────────────────────────┤
    │ Status: Coordinates | Scale | CRS                           │
    └─────────────────────────────────────────────────────────────┘
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gis_api = get_gis_api()
        self._current_tool = "pan"
        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self._toolbar = self._create_toolbar()
        layout.addWidget(self._toolbar)

        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {COLORS['border']};
                width: 3px;
            }}
        """)

        # Layer panel (left)
        self._layer_panel = LayerPanel(self)
        splitter.addWidget(self._layer_panel)

        # Map canvas (center)
        self._map_canvas = create_map_canvas(self)
        self._map_canvas.feature_clicked.connect(self._on_feature_clicked)
        self._map_canvas.feature_drawn.connect(self._on_feature_drawn)
        self._map_canvas.map_clicked.connect(self._on_map_clicked)
        splitter.addWidget(self._map_canvas)

        # Properties panel (right) - hidden by default
        self._props_panel = PropertiesPanel(self)
        self._props_panel.hide()
        splitter.addWidget(self._props_panel)

        # Set splitter sizes
        splitter.setSizes([220, 800, 0])

        layout.addWidget(splitter, 1)

        # Status bar
        self._status_bar = self._create_status_bar()
        layout.addWidget(self._status_bar)

    def _create_toolbar(self) -> QToolBar:
        """Create the map toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {COLORS['card_bg']};
                border-bottom: 2px solid {COLORS['border']};
                padding: 4px;
                spacing: 4px;
            }}
            QToolButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QToolButton:hover {{
                background: {COLORS['primary_light']};
                color: white;
            }}
            QToolButton:checked {{
                background: {COLORS['primary']};
                color: white;
            }}
        """)

        # Navigation tools
        self._pan_btn = self._add_tool_button(toolbar, "Pan", "pan", checkable=True, checked=True)
        self._zoom_btn = self._add_tool_button(toolbar, "Zoom", "zoom", checkable=True)
        self._select_btn = self._add_tool_button(toolbar, "Select", "select", checkable=True)

        toolbar.addSeparator()

        # Drawing tools
        self._draw_btn = self._add_tool_button(toolbar, "Draw", "draw", checkable=True)
        self._edit_btn = self._add_tool_button(toolbar, "Edit", "edit", checkable=True)

        toolbar.addSeparator()

        # Measure tools
        self._measure_btn = self._add_tool_button(toolbar, "Measure", "measure", checkable=True)

        toolbar.addSeparator()

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(), spacer.sizePolicy().verticalPolicy())
        spacer.setMinimumWidth(20)
        toolbar.addWidget(spacer)

        # Import/Export
        import_btn = self._add_tool_button(toolbar, "Import", "import")
        import_btn.clicked.connect(self._on_import)

        export_btn = self._add_tool_button(toolbar, "Export", "export")
        export_btn.clicked.connect(self._on_export)

        toolbar.addSeparator()

        # QGIS integration
        qgis_btn = self._add_tool_button(toolbar, "Open in QGIS", "qgis")
        qgis_btn.clicked.connect(self._on_open_qgis)

        # Refresh
        refresh_btn = self._add_tool_button(toolbar, "Refresh", "refresh")
        refresh_btn.clicked.connect(self._load_initial_data)

        return toolbar

    def _add_tool_button(
        self,
        toolbar: QToolBar,
        text: str,
        tool_id: str,
        checkable: bool = False,
        checked: bool = False
    ) -> QToolButton:
        """Add a tool button to the toolbar."""
        btn = QToolButton()
        btn.setText(text)
        btn.setCheckable(checkable)
        btn.setChecked(checked)
        btn.setToolTip(text)
        btn.setProperty("tool_id", tool_id)

        if checkable:
            btn.clicked.connect(lambda checked, t=tool_id: self._on_tool_selected(t))

        toolbar.addWidget(btn)
        return btn

    def _on_tool_selected(self, tool_id: str) -> None:
        """Handle tool selection."""
        # Uncheck other tool buttons
        for btn in [self._pan_btn, self._zoom_btn, self._select_btn,
                    self._draw_btn, self._edit_btn, self._measure_btn]:
            if btn.property("tool_id") != tool_id:
                btn.setChecked(False)

        self._current_tool = tool_id
        self._map_canvas.set_tool(tool_id)

        # Show/hide drawing controls
        if tool_id in ["draw", "edit"]:
            self._map_canvas.enable_drawing(True)
        else:
            self._map_canvas.enable_drawing(False)

    def _create_status_bar(self) -> QFrame:
        """Create the status bar."""
        status = QFrame()
        status.setFixedHeight(28)
        status.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['card_bg']};
                border-top: 1px solid {COLORS['border']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: 10px;
                padding: 0 8px;
            }}
        """)

        layout = QHBoxLayout(status)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(20)

        # Coordinates
        self._coords_label = QLabel("Coordinates: ---, ---")
        layout.addWidget(self._coords_label)

        # Scale
        self._scale_label = QLabel("Scale: 1:---")
        layout.addWidget(self._scale_label)

        # CRS
        self._crs_label = QLabel("CRS: EPSG:4326")
        layout.addWidget(self._crs_label)

        layout.addStretch()

        # Tool indicator
        self._tool_label = QLabel("Tool: Pan")
        self._tool_label.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold;")
        layout.addWidget(self._tool_label)

        return status

    def _load_initial_data(self) -> None:
        """Load field boundaries and layers."""
        # Load field boundaries
        fc, error = self._gis_api.get_field_boundaries()

        if error:
            logger.error("Failed to load field boundaries: %s", error)
            return

        if fc and fc.features:
            # Convert to dict for map canvas
            geojson_dict = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": f.type,
                        "geometry": f.geometry,
                        "properties": f.properties,
                        "id": f.id
                    }
                    for f in fc.features
                ]
            }

            style = {
                "fill_color": "#00868B",
                "fill_opacity": 0.3,
                "stroke_color": "#004040",
                "stroke_width": 2
            }

            self._map_canvas.add_geojson_layer("fields", geojson_dict, style, "Fields")

            # Fit to bounds if we have features
            if fc.features:
                self._fit_to_features(fc.features)

        # Load custom layers
        layers, error = self._gis_api.list_layers(visible_only=False)
        if not error:
            for layer in layers:
                if layer.name != "Fields":  # Skip built-in fields layer
                    self._layer_panel.add_layer(
                        str(layer.id),
                        layer.name,
                        layer.layer_type,
                        layer.is_visible
                    )

    def _fit_to_features(self, features: list) -> None:
        """Fit map to bounds of features."""
        min_lat = min_lng = float('inf')
        max_lat = max_lng = float('-inf')

        for f in features:
            geom = f.geometry
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [0, 0])
                min_lng = min(min_lng, coords[0])
                max_lng = max(max_lng, coords[0])
                min_lat = min(min_lat, coords[1])
                max_lat = max(max_lat, coords[1])
            elif geom.get("type") == "Polygon":
                for ring in geom.get("coordinates", [[]]):
                    for coord in ring:
                        min_lng = min(min_lng, coord[0])
                        max_lng = max(max_lng, coord[0])
                        min_lat = min(min_lat, coord[1])
                        max_lat = max(max_lat, coord[1])

        if min_lat != float('inf'):
            # Add small padding
            padding = 0.01
            self._map_canvas.fit_bounds(
                min_lat - padding,
                min_lng - padding,
                max_lat + padding,
                max_lng + padding
            )

    @pyqtSlot(int, dict)
    def _on_feature_clicked(self, feature_id: int, properties: dict) -> None:
        """Handle feature click."""
        self._props_panel.show()
        self._props_panel.show_properties(feature_id, properties)

    @pyqtSlot(dict)
    def _on_feature_drawn(self, geometry: dict) -> None:
        """Handle new feature drawn."""
        # Ask user what to do with the drawn feature
        reply = QMessageBox.question(
            self, "Save Feature",
            "Save this boundary to an existing field or create a new layer?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard
        )

        if reply == QMessageBox.StandardButton.Save:
            # Show field selection dialog
            self._save_drawn_boundary(geometry)

    @pyqtSlot(float, float)
    def _on_map_clicked(self, lat: float, lng: float) -> None:
        """Handle map click."""
        self._coords_label.setText(f"Coordinates: {lat:.6f}, {lng:.6f}")

    def _save_drawn_boundary(self, geometry: dict) -> None:
        """Save a drawn boundary to a field."""
        from PyQt6.QtWidgets import QInputDialog

        # Get field ID from user
        field_id, ok = QInputDialog.getInt(
            self, "Save Boundary",
            "Enter Field ID to update boundary:",
            1, 1, 99999
        )

        if ok:
            boundary_str = json.dumps(geometry)
            success, error = self._gis_api.update_field_boundary(field_id, boundary_str)

            if success:
                QMessageBox.information(self, "Success", "Field boundary updated.")
                self._load_initial_data()  # Refresh map
            else:
                QMessageBox.warning(self, "Error", f"Failed to update boundary: {error}")

    def _on_import(self) -> None:
        """Import GIS file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import GIS File",
            "",
            "GIS Files (*.shp *.kml *.geojson *.json *.gpkg);;Shapefiles (*.shp);;KML (*.kml);;GeoJSON (*.geojson *.json);;GeoPackage (*.gpkg)"
        )

        if file_path:
            result, error = self._gis_api.import_file(file_path)

            if error:
                QMessageBox.warning(self, "Import Error", error)
                return

            if result:
                msg = f"Import complete:\n- Imported: {result.imported_count}\n- Matched: {result.matched_count}"
                if result.errors:
                    msg += f"\n- Errors: {len(result.errors)}"
                QMessageBox.information(self, "Import Result", msg)
                self._load_initial_data()  # Refresh

    def _on_export(self) -> None:
        """Export to GIS format."""
        # Show export format dialog
        format_choice, ok = QInputDialog.getItem(
            self, "Export Format",
            "Select export format:",
            ["Shapefile (.shp)", "GeoJSON (.geojson)", "KML (.kml)", "GeoPackage (.gpkg)"],
            0, False
        )

        if not ok:
            return

        # Map display name to format
        format_map = {
            "Shapefile (.shp)": "shapefile",
            "GeoJSON (.geojson)": "geojson",
            "KML (.kml)": "kml",
            "GeoPackage (.gpkg)": "geopackage"
        }
        export_format = format_map.get(format_choice, "geojson")

        result, error = self._gis_api.export_to_format(export_format)

        if error:
            QMessageBox.warning(self, "Export Error", error)
            return

        if result and result.success:
            QMessageBox.information(
                self, "Export Complete",
                f"Exported {result.feature_count} features to:\n{result.file_path}"
            )

            # Ask if user wants to open the file location
            reply = QMessageBox.question(
                self, "Open Location",
                "Open the export folder?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes and result.file_path:
                folder = os.path.dirname(result.file_path)
                if os.path.exists(folder):
                    os.startfile(folder)

    def _on_open_qgis(self) -> None:
        """Open data in QGIS."""
        # Generate QGIS project
        result, error = self._gis_api.generate_qgis_project()

        if error:
            QMessageBox.warning(self, "QGIS Error", error)
            return

        if not result or not result.success:
            QMessageBox.warning(self, "QGIS Error", result.message if result else "Failed to generate project")
            return

        # Try to find and launch QGIS
        qgis_paths = [
            r"C:\Program Files\QGIS 3.34\bin\qgis.exe",
            r"C:\Program Files\QGIS 3.28\bin\qgis.exe",
            r"C:\Program Files\QGIS\bin\qgis.exe",
            r"C:\OSGeo4W\bin\qgis.exe",
        ]

        qgis_exe = None
        for path in qgis_paths:
            if os.path.exists(path):
                qgis_exe = path
                break

        if qgis_exe and result.project_path:
            try:
                subprocess.Popen([qgis_exe, result.project_path])
                QMessageBox.information(
                    self, "QGIS",
                    f"Opening in QGIS...\n\nProject: {result.project_path}"
                )
            except Exception as e:
                QMessageBox.warning(self, "QGIS Error", f"Failed to launch QGIS: {e}")
        else:
            # QGIS not found, just show file locations
            msg = "QGIS not found. Files have been exported to:\n\n"
            if result.project_path:
                msg += f"Project: {result.project_path}\n"
            if result.geopackage_path:
                msg += f"Data: {result.geopackage_path}"
            QMessageBox.information(self, "Export Complete", msg)

    def _add_layer_dialog(self) -> None:
        """Show dialog to add a new layer."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Layer")
        dialog.setMinimumWidth(300)

        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        layout.addRow("Name:", name_edit)

        type_combo = QComboBox()
        type_combo.addItems(["Vector", "Tile"])
        layout.addRow("Type:", type_combo)

        geom_combo = QComboBox()
        geom_combo.addItems(["Polygon", "Point", "Line"])
        layout.addRow("Geometry:", geom_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = name_edit.text().strip()
            if name:
                layer_type = type_combo.currentText().lower()
                geom_type = geom_combo.currentText().lower()

                layer, error = self._gis_api.create_layer(
                    name=name,
                    layer_type=layer_type,
                    geometry_type=geom_type
                )

                if error:
                    QMessageBox.warning(self, "Error", f"Failed to create layer: {error}")
                else:
                    self._layer_panel.add_layer(str(layer.id), name, layer_type)
                    QMessageBox.information(self, "Success", f"Layer '{name}' created.")


