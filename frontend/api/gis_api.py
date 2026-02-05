"""
GIS API Client for AgTools Frontend

Handles GIS operations: field boundaries, layers, import/export, and QGIS integration.
AgTools v6.16.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class GeoJSONFeature:
    """GeoJSON Feature"""
    type: str
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "GeoJSONFeature":
        return cls(
            type=data.get("type", "Feature"),
            geometry=data.get("geometry", {}),
            properties=data.get("properties", {}),
            id=data.get("id")
        )


@dataclass
class GeoJSONFeatureCollection:
    """GeoJSON Feature Collection"""
    type: str
    features: List[GeoJSONFeature]

    @classmethod
    def from_dict(cls, data: dict) -> "GeoJSONFeatureCollection":
        features = [GeoJSONFeature.from_dict(f) for f in data.get("features", [])]
        return cls(
            type=data.get("type", "FeatureCollection"),
            features=features
        )


@dataclass
class LayerStyle:
    """Layer styling options"""
    fill_color: str = "#00868B"
    fill_opacity: float = 0.5
    stroke_color: str = "#004040"
    stroke_width: int = 2
    stroke_opacity: float = 1.0
    point_radius: int = 6
    icon: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "LayerStyle":
        if not data:
            return cls()
        return cls(
            fill_color=data.get("fill_color", "#00868B"),
            fill_opacity=data.get("fill_opacity", 0.5),
            stroke_color=data.get("stroke_color", "#004040"),
            stroke_width=data.get("stroke_width", 2),
            stroke_opacity=data.get("stroke_opacity", 1.0),
            point_radius=data.get("point_radius", 6),
            icon=data.get("icon")
        )

    def to_dict(self) -> dict:
        return {
            "fill_color": self.fill_color,
            "fill_opacity": self.fill_opacity,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "stroke_opacity": self.stroke_opacity,
            "point_radius": self.point_radius,
            "icon": self.icon
        }


@dataclass
class LayerInfo:
    """GIS Layer information"""
    id: int
    name: str
    layer_type: str
    geometry_type: Optional[str]
    description: Optional[str]
    style: Optional[LayerStyle]
    source_url: Optional[str]
    is_visible: bool
    display_order: int
    feature_count: int
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "LayerInfo":
        style = None
        if data.get("style"):
            style = LayerStyle.from_dict(data["style"])
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            layer_type=data.get("layer_type", "vector"),
            geometry_type=data.get("geometry_type"),
            description=data.get("description"),
            style=style,
            source_url=data.get("source_url"),
            is_visible=data.get("is_visible", True),
            display_order=data.get("display_order", 0),
            feature_count=data.get("feature_count", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )


@dataclass
class FeatureInfo:
    """GIS Feature information"""
    id: int
    layer_id: int
    geometry: Dict[str, Any]
    properties: Dict[str, Any]
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureInfo":
        return cls(
            id=data.get("id", 0),
            layer_id=data.get("layer_id", 0),
            geometry=data.get("geometry", {}),
            properties=data.get("properties", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )


@dataclass
class ImportResult:
    """Import operation result"""
    success: bool
    message: str
    imported_count: int = 0
    matched_count: int = 0
    errors: List[str] = field(default_factory=list)
    features: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ImportResult":
        return cls(
            success=data.get("success", False),
            message=data.get("message", ""),
            imported_count=data.get("imported_count", 0),
            matched_count=data.get("matched_count", 0),
            errors=data.get("errors", []),
            features=data.get("features", [])
        )


@dataclass
class ExportResult:
    """Export operation result"""
    success: bool
    message: str
    file_path: Optional[str] = None
    feature_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "ExportResult":
        return cls(
            success=data.get("success", False),
            message=data.get("message", ""),
            file_path=data.get("file_path"),
            feature_count=data.get("feature_count", 0)
        )


@dataclass
class AreaResult:
    """Area calculation result"""
    area_sq_meters: float
    area_acres: float
    area_hectares: float
    perimeter_meters: float

    @classmethod
    def from_dict(cls, data: dict) -> "AreaResult":
        return cls(
            area_sq_meters=data.get("area_sq_meters", 0),
            area_acres=data.get("area_acres", 0),
            area_hectares=data.get("area_hectares", 0),
            perimeter_meters=data.get("perimeter_meters", 0)
        )


@dataclass
class QGISProjectResult:
    """QGIS project generation result"""
    success: bool
    project_path: Optional[str]
    geopackage_path: Optional[str]
    message: str

    @classmethod
    def from_dict(cls, data: dict) -> "QGISProjectResult":
        return cls(
            success=data.get("success", False),
            project_path=data.get("project_path"),
            geopackage_path=data.get("geopackage_path"),
            message=data.get("message", "")
        )


# ============================================================================
# GIS API CLIENT
# ============================================================================

class GISAPI:
    """GIS API client for field boundaries, layers, and QGIS integration."""

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    # ========================================================================
    # FIELD BOUNDARIES
    # ========================================================================

    def get_field_boundaries(
        self,
        field_ids: Optional[List[int]] = None,
        farm_name: Optional[str] = None
    ) -> Tuple[Optional[GeoJSONFeatureCollection], Optional[str]]:
        """
        Get field boundaries as GeoJSON FeatureCollection.

        Args:
            field_ids: Optional list of field IDs to include
            farm_name: Optional farm name filter

        Returns:
            Tuple of (GeoJSONFeatureCollection, error_message)
        """
        params = {}
        if field_ids:
            params["field_ids"] = ",".join(str(i) for i in field_ids)
        if farm_name:
            params["farm_name"] = farm_name

        response = self._client.get("/gis/fields/boundaries", params=params if params else None)

        if not response.success:
            return None, response.error_message

        return GeoJSONFeatureCollection.from_dict(response.data), None

    def update_field_boundary(
        self,
        field_id: int,
        boundary: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Update a field's boundary.

        Args:
            field_id: Field ID
            boundary: GeoJSON geometry string

        Returns:
            Tuple of (success, error_message)
        """
        response = self._client.put(
            f"/gis/fields/{field_id}/boundary",
            data={"boundary": boundary}
        )

        if not response.success:
            return False, response.error_message

        return True, None

    # ========================================================================
    # IMPORT/EXPORT
    # ========================================================================

    def import_file(
        self,
        file_path: str,
        file_type: str = "auto",
        match_by: str = "name"
    ) -> Tuple[Optional[ImportResult], Optional[str]]:
        """
        Import a GIS file (shapefile, KML, GeoJSON).

        Args:
            file_path: Path to file to import
            file_type: File type (auto, shapefile, kml, geojson)
            match_by: How to match to existing fields (name, location, none)

        Returns:
            Tuple of (ImportResult, error_message)
        """
        import os

        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"

        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            data = {"file_type": file_type, "match_by": match_by}

            response = self._client.post_multipart(
                "/gis/import",
                files=files,
                data=data
            )

        if not response.success:
            return None, response.error_message

        return ImportResult.from_dict(response.data), None

    def export_to_format(
        self,
        format: str,
        field_ids: Optional[List[int]] = None,
        include_layers: bool = False
    ) -> Tuple[Optional[ExportResult], Optional[str]]:
        """
        Export field boundaries to GIS format.

        Args:
            format: Output format (shapefile, geojson, kml, geopackage)
            field_ids: Optional list of field IDs
            include_layers: Include custom layers

        Returns:
            Tuple of (ExportResult, error_message)
        """
        data = {
            "format": format,
            "include_layers": include_layers
        }
        if field_ids:
            data["field_ids"] = field_ids

        response = self._client.post("/gis/export", data=data)

        if not response.success:
            return None, response.error_message

        return ExportResult.from_dict(response.data), None

    # ========================================================================
    # CALCULATIONS
    # ========================================================================

    def calculate_area(
        self,
        geometry: Dict[str, Any]
    ) -> Tuple[Optional[AreaResult], Optional[str]]:
        """
        Calculate area of a geometry.

        Args:
            geometry: GeoJSON geometry dict

        Returns:
            Tuple of (AreaResult, error_message)
        """
        response = self._client.post("/gis/calculate/area", data=geometry)

        if not response.success:
            return None, response.error_message

        return AreaResult.from_dict(response.data), None

    def validate_boundary(
        self,
        boundary: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a GeoJSON boundary.

        Args:
            boundary: GeoJSON geometry string

        Returns:
            Tuple of (is_valid, error_message)
        """
        response = self._client.post(
            "/gis/validate/boundary",
            params={"boundary": boundary}
        )

        if not response.success:
            return False, response.error_message

        return response.data.get("valid", False), response.data.get("error")

    # ========================================================================
    # QGIS INTEGRATION
    # ========================================================================

    def generate_qgis_project(
        self,
        field_ids: Optional[List[int]] = None
    ) -> Tuple[Optional[QGISProjectResult], Optional[str]]:
        """
        Generate a QGIS project file with field data.

        Args:
            field_ids: Optional list of field IDs

        Returns:
            Tuple of (QGISProjectResult, error_message)
        """
        params = {}
        if field_ids:
            params["field_ids"] = ",".join(str(i) for i in field_ids)

        response = self._client.get("/gis/qgis/project", params=params if params else None)

        if not response.success:
            return None, response.error_message

        return QGISProjectResult.from_dict(response.data), None

    # ========================================================================
    # LAYERS
    # ========================================================================

    def list_layers(
        self,
        layer_type: Optional[str] = None,
        visible_only: bool = False
    ) -> Tuple[List[LayerInfo], Optional[str]]:
        """
        List all GIS layers.

        Args:
            layer_type: Filter by layer type (vector, raster, tile)
            visible_only: Only return visible layers

        Returns:
            Tuple of (list of LayerInfo, error_message)
        """
        params = {}
        if layer_type:
            params["layer_type"] = layer_type
        if visible_only:
            params["visible_only"] = "true"

        response = self._client.get("/gis/layers", params=params if params else None)

        if not response.success:
            return [], response.error_message

        layers = [LayerInfo.from_dict(d) for d in response.data]
        return layers, None

    def create_layer(
        self,
        name: str,
        layer_type: str = "vector",
        geometry_type: Optional[str] = "polygon",
        description: Optional[str] = None,
        style: Optional[LayerStyle] = None,
        is_visible: bool = True,
        display_order: int = 0
    ) -> Tuple[Optional[LayerInfo], Optional[str]]:
        """
        Create a new GIS layer.

        Returns:
            Tuple of (LayerInfo, error_message)
        """
        data = {
            "name": name,
            "layer_type": layer_type,
            "geometry_type": geometry_type,
            "is_visible": is_visible,
            "display_order": display_order
        }
        if description:
            data["description"] = description
        if style:
            data["style"] = style.to_dict()

        response = self._client.post("/gis/layers", data=data)

        if not response.success:
            return None, response.error_message

        return LayerInfo.from_dict(response.data), None

    def get_layer(self, layer_id: int) -> Tuple[Optional[LayerInfo], Optional[str]]:
        """Get a layer by ID."""
        response = self._client.get(f"/gis/layers/{layer_id}")

        if not response.success:
            return None, response.error_message

        return LayerInfo.from_dict(response.data), None

    def update_layer(
        self,
        layer_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        style: Optional[LayerStyle] = None,
        is_visible: Optional[bool] = None,
        display_order: Optional[int] = None
    ) -> Tuple[Optional[LayerInfo], Optional[str]]:
        """Update a layer."""
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if style is not None:
            data["style"] = style.to_dict()
        if is_visible is not None:
            data["is_visible"] = is_visible
        if display_order is not None:
            data["display_order"] = display_order

        response = self._client.put(f"/gis/layers/{layer_id}", data=data)

        if not response.success:
            return None, response.error_message

        return LayerInfo.from_dict(response.data), None

    def delete_layer(self, layer_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a layer."""
        response = self._client.delete(f"/gis/layers/{layer_id}")

        if not response.success:
            return False, response.error_message

        return True, None

    def toggle_layer_visibility(
        self,
        layer_id: int,
        is_visible: bool
    ) -> Tuple[bool, Optional[str]]:
        """Toggle layer visibility."""
        response = self._client.put(
            f"/gis/layers/{layer_id}/visibility",
            params={"is_visible": str(is_visible).lower()}
        )

        if not response.success:
            return False, response.error_message

        return True, None

    # ========================================================================
    # FEATURES
    # ========================================================================

    def get_layer_features(
        self,
        layer_id: int
    ) -> Tuple[Optional[GeoJSONFeatureCollection], Optional[str]]:
        """Get all features in a layer as GeoJSON."""
        response = self._client.get(f"/gis/layers/{layer_id}/features")

        if not response.success:
            return None, response.error_message

        return GeoJSONFeatureCollection.from_dict(response.data), None

    def create_feature(
        self,
        layer_id: int,
        geometry: Dict[str, Any],
        properties: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[FeatureInfo], Optional[str]]:
        """Create a feature in a layer."""
        data = {
            "geometry": geometry,
            "properties": properties or {}
        }

        response = self._client.post(f"/gis/layers/{layer_id}/features", data=data)

        if not response.success:
            return None, response.error_message

        return FeatureInfo.from_dict(response.data), None

    def update_feature(
        self,
        feature_id: int,
        geometry: Optional[Dict[str, Any]] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Tuple[Optional[FeatureInfo], Optional[str]]:
        """Update a feature."""
        data = {}
        if geometry is not None:
            data["geometry"] = geometry
        if properties is not None:
            data["properties"] = properties

        response = self._client.put(f"/gis/features/{feature_id}", data=data)

        if not response.success:
            return None, response.error_message

        return FeatureInfo.from_dict(response.data), None

    def delete_feature(self, feature_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a feature."""
        response = self._client.delete(f"/gis/features/{feature_id}")

        if not response.success:
            return False, response.error_message

        return True, None


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_gis_api: Optional[GISAPI] = None


def get_gis_api() -> GISAPI:
    """Get or create the GIS API singleton."""
    global _gis_api
    if _gis_api is None:
        _gis_api = GISAPI()
    return _gis_api
