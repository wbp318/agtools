"""
GIS Layers Service for AgTools
Manages custom map layers including soil zones, yield maps, and scout points.

AgTools v6.16.0
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel, Field

from database.db_utils import get_db_connection, DEFAULT_DB_PATH
from .base_service import BaseService

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class LayerType(str, Enum):
    """Layer types"""
    VECTOR = "vector"
    RASTER = "raster"
    TILE = "tile"


class GeometryType(str, Enum):
    """Geometry types for vector layers"""
    POINT = "point"
    LINE = "line"
    POLYGON = "polygon"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LayerStyle(BaseModel):
    """Layer styling options"""
    fill_color: str = "#00868B"
    fill_opacity: float = 0.5
    stroke_color: str = "#004040"
    stroke_width: int = 2
    stroke_opacity: float = 1.0
    point_radius: int = 6
    icon: Optional[str] = None


class LayerCreate(BaseModel):
    """Create layer request"""
    name: str = Field(..., min_length=1, max_length=100)
    layer_type: LayerType = LayerType.VECTOR
    geometry_type: Optional[GeometryType] = GeometryType.POLYGON
    description: Optional[str] = None
    style: Optional[LayerStyle] = None
    source_url: Optional[str] = None
    is_visible: bool = True
    display_order: int = 0


class LayerUpdate(BaseModel):
    """Update layer request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    style: Optional[LayerStyle] = None
    source_url: Optional[str] = None
    is_visible: Optional[bool] = None
    display_order: Optional[int] = None


class LayerResponse(BaseModel):
    """Layer response"""
    id: int
    name: str
    layer_type: str
    geometry_type: Optional[str]
    description: Optional[str]
    style: Optional[Dict[str, Any]]
    source_url: Optional[str]
    is_visible: bool
    display_order: int
    feature_count: int = 0
    created_at: str
    updated_at: str

    model_config = {"extra": "allow"}


class FeatureCreate(BaseModel):
    """Create feature request"""
    geometry: Dict[str, Any] = Field(..., description="GeoJSON geometry")
    properties: Dict[str, Any] = {}


class FeatureUpdate(BaseModel):
    """Update feature request"""
    geometry: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None


class FeatureResponse(BaseModel):
    """Feature response"""
    id: int
    layer_id: int
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    created_at: str
    updated_at: str

    model_config = {"extra": "allow"}


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON Feature Collection"""
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]] = []


# ============================================================================
# GIS LAYERS SERVICE CLASS
# ============================================================================

class GISLayersService(BaseService[LayerResponse]):
    """
    GIS Layers Service for managing custom map layers.

    Features:
    - Create/store custom layers (soil zones, yield maps, scout points)
    - Layer styling (colors, symbols)
    - Raster tile references
    - Layer visibility/order management
    """

    TABLE_NAME = "gis_layers"

    def __init__(self, db_path: str = None):
        """Initialize GIS layers service."""
        self.db_path = db_path or DEFAULT_DB_PATH
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Create gis_layers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gis_layers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    layer_type VARCHAR(20) NOT NULL DEFAULT 'vector',
                    geometry_type VARCHAR(20),
                    description TEXT,
                    style_json TEXT,
                    source_url TEXT,
                    is_visible INTEGER DEFAULT 1,
                    display_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create gis_features table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gis_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    layer_id INTEGER NOT NULL,
                    geometry TEXT NOT NULL,
                    properties TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (layer_id) REFERENCES gis_layers(id) ON DELETE CASCADE
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gis_layers_name ON gis_layers(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gis_layers_type ON gis_layers(layer_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gis_layers_visible ON gis_layers(is_visible)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_gis_features_layer ON gis_features(layer_id)")

            conn.commit()

    def _row_to_response(self, row: sqlite3.Row, **kwargs) -> LayerResponse:
        """Convert a database row to LayerResponse."""
        style = None
        if row["style_json"]:
            try:
                style = json.loads(row["style_json"])
            except json.JSONDecodeError:
                pass

        return LayerResponse(
            id=row["id"],
            name=row["name"],
            layer_type=row["layer_type"],
            geometry_type=row["geometry_type"],
            description=row["description"],
            style=style,
            source_url=row["source_url"],
            is_visible=bool(row["is_visible"]),
            display_order=row["display_order"],
            feature_count=self._safe_get(row, "feature_count", 0),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    # ========================================================================
    # LAYER CRUD
    # ========================================================================

    def create_layer(
        self,
        layer_data: LayerCreate,
        user_id: int
    ) -> Tuple[Optional[LayerResponse], Optional[str]]:
        """
        Create a new layer.

        Args:
            layer_data: Layer creation data
            user_id: ID of user creating the layer

        Returns:
            Tuple of (LayerResponse, error_message)
        """
        try:
            style_json = None
            if layer_data.style:
                style_json = json.dumps(layer_data.style.model_dump())

            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO gis_layers (
                        name, layer_type, geometry_type, description,
                        style_json, source_url, is_visible, display_order
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    layer_data.name,
                    layer_data.layer_type.value,
                    layer_data.geometry_type.value if layer_data.geometry_type else None,
                    layer_data.description,
                    style_json,
                    layer_data.source_url,
                    1 if layer_data.is_visible else 0,
                    layer_data.display_order
                ))

                layer_id = cursor.lastrowid

                self.auth_service.log_action(
                    user_id=user_id,
                    action="create_gis_layer",
                    entity_type="gis_layer",
                    entity_id=layer_id,
                    conn=conn
                )

                conn.commit()

            return self.get_layer_by_id(layer_id), None

        except Exception as e:
            return None, self._sanitize_error(e, "layer creation")

    def get_layer_by_id(self, layer_id: int) -> Optional[LayerResponse]:
        """Get layer by ID with feature count."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT l.*,
                    (SELECT COUNT(*) FROM gis_features WHERE layer_id = l.id AND is_active = 1) as feature_count
                FROM gis_layers l
                WHERE l.id = ? AND l.is_active = 1
            """, (layer_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_response(row)

    def list_layers(
        self,
        layer_type: Optional[LayerType] = None,
        visible_only: bool = False
    ) -> List[LayerResponse]:
        """
        List all layers.

        Args:
            layer_type: Filter by layer type
            visible_only: Only return visible layers

        Returns:
            List of LayerResponse
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT l.*,
                    (SELECT COUNT(*) FROM gis_features WHERE layer_id = l.id AND is_active = 1) as feature_count
                FROM gis_layers l
                WHERE l.is_active = 1
            """
            params = []

            if layer_type:
                query += " AND l.layer_type = ?"
                params.append(layer_type.value)

            if visible_only:
                query += " AND l.is_visible = 1"

            query += " ORDER BY l.display_order, l.name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_response(row) for row in rows]

    def update_layer(
        self,
        layer_id: int,
        layer_data: LayerUpdate,
        user_id: int
    ) -> Tuple[Optional[LayerResponse], Optional[str]]:
        """
        Update a layer.

        Args:
            layer_id: Layer ID
            layer_data: Update data
            user_id: ID of user performing update

        Returns:
            Tuple of (LayerResponse, error_message)
        """
        updates = []
        params = []

        if layer_data.name is not None:
            updates.append("name = ?")
            params.append(layer_data.name)

        if layer_data.description is not None:
            updates.append("description = ?")
            params.append(layer_data.description)

        if layer_data.style is not None:
            updates.append("style_json = ?")
            params.append(json.dumps(layer_data.style.model_dump()))

        if layer_data.source_url is not None:
            updates.append("source_url = ?")
            params.append(layer_data.source_url)

        if layer_data.is_visible is not None:
            updates.append("is_visible = ?")
            params.append(1 if layer_data.is_visible else 0)

        if layer_data.display_order is not None:
            updates.append("display_order = ?")
            params.append(layer_data.display_order)

        if not updates:
            return self.get_layer_by_id(layer_id), None

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(layer_id)

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(f"""
                    UPDATE gis_layers SET {', '.join(updates)}
                    WHERE id = ? AND is_active = 1
                """, params)

                if cursor.rowcount == 0:
                    return None, "Layer not found"

                self.auth_service.log_action(
                    user_id=user_id,
                    action="update_gis_layer",
                    entity_type="gis_layer",
                    entity_id=layer_id,
                    conn=conn
                )

                conn.commit()

            return self.get_layer_by_id(layer_id), None

        except Exception as e:
            return None, self._sanitize_error(e, "layer update")

    def delete_layer(self, layer_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete a layer."""
        return self.soft_delete(layer_id, user_id, entity_name="Layer")

    def update_layer_visibility(
        self,
        layer_id: int,
        is_visible: bool,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Toggle layer visibility."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE gis_layers SET is_visible = ?, updated_at = ?
                    WHERE id = ? AND is_active = 1
                """, (1 if is_visible else 0, datetime.now(timezone.utc).isoformat(), layer_id))

                if cursor.rowcount == 0:
                    return False, "Layer not found"

                conn.commit()

            return True, None

        except Exception as e:
            return False, self._sanitize_error(e, "visibility update")

    def reorder_layers(
        self,
        layer_orders: List[Dict[str, int]],
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Update display order of multiple layers.

        Args:
            layer_orders: List of {"id": layer_id, "order": display_order}
            user_id: User performing reorder

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for item in layer_orders:
                    cursor.execute("""
                        UPDATE gis_layers SET display_order = ?, updated_at = ?
                        WHERE id = ? AND is_active = 1
                    """, (item["order"], datetime.now(timezone.utc).isoformat(), item["id"]))

                conn.commit()

            return True, None

        except Exception as e:
            return False, self._sanitize_error(e, "layer reorder")

    # ========================================================================
    # FEATURE CRUD
    # ========================================================================

    def create_feature(
        self,
        layer_id: int,
        feature_data: FeatureCreate,
        user_id: int
    ) -> Tuple[Optional[FeatureResponse], Optional[str]]:
        """
        Create a feature in a layer.

        Args:
            layer_id: Layer ID
            feature_data: Feature creation data
            user_id: User creating the feature

        Returns:
            Tuple of (FeatureResponse, error_message)
        """
        try:
            # Verify layer exists
            layer = self.get_layer_by_id(layer_id)
            if not layer:
                return None, "Layer not found"

            geometry_json = json.dumps(feature_data.geometry)
            properties_json = json.dumps(feature_data.properties)

            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO gis_features (layer_id, geometry, properties)
                    VALUES (?, ?, ?)
                """, (layer_id, geometry_json, properties_json))

                feature_id = cursor.lastrowid
                conn.commit()

            return self.get_feature_by_id(feature_id), None

        except Exception as e:
            return None, self._sanitize_error(e, "feature creation")

    def get_feature_by_id(self, feature_id: int) -> Optional[FeatureResponse]:
        """Get feature by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM gis_features
                WHERE id = ? AND is_active = 1
            """, (feature_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return FeatureResponse(
                id=row["id"],
                layer_id=row["layer_id"],
                geometry=json.loads(row["geometry"]),
                properties=json.loads(row["properties"]) if row["properties"] else {},
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

    def get_layer_features(
        self,
        layer_id: int,
        as_geojson: bool = True
    ) -> GeoJSONFeatureCollection:
        """
        Get all features in a layer as GeoJSON FeatureCollection.

        Args:
            layer_id: Layer ID
            as_geojson: Return as GeoJSON (always True currently)

        Returns:
            GeoJSON FeatureCollection
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM gis_features
                WHERE layer_id = ? AND is_active = 1
            """, (layer_id,))

            rows = cursor.fetchall()

        features = []
        for row in rows:
            feature = {
                "type": "Feature",
                "id": row["id"],
                "geometry": json.loads(row["geometry"]),
                "properties": json.loads(row["properties"]) if row["properties"] else {}
            }
            features.append(feature)

        return GeoJSONFeatureCollection(features=features)

    def update_feature(
        self,
        feature_id: int,
        feature_data: FeatureUpdate,
        user_id: int
    ) -> Tuple[Optional[FeatureResponse], Optional[str]]:
        """Update a feature."""
        updates = []
        params = []

        if feature_data.geometry is not None:
            updates.append("geometry = ?")
            params.append(json.dumps(feature_data.geometry))

        if feature_data.properties is not None:
            updates.append("properties = ?")
            params.append(json.dumps(feature_data.properties))

        if not updates:
            return self.get_feature_by_id(feature_id), None

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(feature_id)

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(f"""
                    UPDATE gis_features SET {', '.join(updates)}
                    WHERE id = ? AND is_active = 1
                """, params)

                if cursor.rowcount == 0:
                    return None, "Feature not found"

                conn.commit()

            return self.get_feature_by_id(feature_id), None

        except Exception as e:
            return None, self._sanitize_error(e, "feature update")

    def delete_feature(self, feature_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a feature (soft delete)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE gis_features SET is_active = 0, updated_at = ?
                    WHERE id = ? AND is_active = 1
                """, (datetime.now(timezone.utc).isoformat(), feature_id))

                if cursor.rowcount == 0:
                    return False, "Feature not found"

                conn.commit()

            return True, None

        except Exception as e:
            return False, self._sanitize_error(e, "feature deletion")

    # ========================================================================
    # BUILT-IN LAYERS
    # ========================================================================

    def get_or_create_fields_layer(self, user_id: int) -> LayerResponse:
        """Get or create the built-in Fields layer."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM gis_layers
                WHERE name = 'Fields' AND is_active = 1
            """)

            row = cursor.fetchone()
            if row:
                return self._row_to_response(row)

        # Create default Fields layer
        layer_data = LayerCreate(
            name="Fields",
            layer_type=LayerType.VECTOR,
            geometry_type=GeometryType.POLYGON,
            description="Farm field boundaries (from field management)",
            style=LayerStyle(
                fill_color="#00868B",
                fill_opacity=0.3,
                stroke_color="#004040",
                stroke_width=2
            ),
            is_visible=True,
            display_order=0
        )

        result, _ = self.create_layer(layer_data, user_id)
        return result


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_gis_layers_service: Optional[GISLayersService] = None


def get_gis_layers_service(db_path: str = None) -> GISLayersService:
    """Get or create the GIS layers service singleton."""
    global _gis_layers_service

    if _gis_layers_service is None:
        _gis_layers_service = GISLayersService(db_path)

    return _gis_layers_service
