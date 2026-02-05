"""
GIS Service for AgTools
Core Geographic Information System operations including import/export,
coordinate transformations, and boundary management.

AgTools v6.16.0
"""

import json
import logging
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel, Field

from database.db_utils import get_db_connection, DEFAULT_DB_PATH
from .base_service import BaseService

logger = logging.getLogger(__name__)

# Try to import GIS libraries
try:
    import geopandas as gpd
    from shapely.geometry import shape, mapping, Polygon, MultiPolygon, Point
    from shapely.ops import transform
    import pyproj
    from fiona.crs import from_epsg
    HAS_GIS_LIBS = True
except ImportError:
    HAS_GIS_LIBS = False
    logger.warning("GIS libraries not installed. Install with: pip install geopandas shapely fiona pyproj")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class GeoJSONFeature(BaseModel):
    """GeoJSON Feature"""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = {}
    id: Optional[int] = None


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON Feature Collection"""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature] = []


class BoundaryUpdate(BaseModel):
    """Update field boundary request"""
    boundary: str = Field(..., description="GeoJSON geometry string")


class ImportRequest(BaseModel):
    """Import shapefile/KML request"""
    file_path: str
    file_type: str = Field(default="auto", description="auto, shapefile, kml, geojson")
    match_by: str = Field(default="name", description="name, location, none")


class ImportResult(BaseModel):
    """Import operation result"""
    success: bool
    message: str
    imported_count: int = 0
    matched_count: int = 0
    errors: List[str] = []
    features: List[Dict[str, Any]] = []


class ExportRequest(BaseModel):
    """Export request"""
    format: str = Field(..., description="shapefile, geojson, kml, geopackage")
    field_ids: Optional[List[int]] = None
    include_layers: bool = False


class ExportResult(BaseModel):
    """Export operation result"""
    success: bool
    message: str
    file_path: Optional[str] = None
    feature_count: int = 0


class AreaResult(BaseModel):
    """Area calculation result"""
    area_sq_meters: float
    area_acres: float
    area_hectares: float
    perimeter_meters: float


class QGISProjectResult(BaseModel):
    """QGIS project generation result"""
    success: bool
    project_path: Optional[str] = None
    geopackage_path: Optional[str] = None
    message: str


# ============================================================================
# GIS SERVICE CLASS
# ============================================================================

class GISService(BaseService):
    """
    GIS Service for geographic operations.

    Features:
    - Import shapefiles, KML, GeoJSON
    - Export to various GIS formats
    - Coordinate system transformations
    - Area and distance calculations
    - Boundary validation
    - QGIS project generation
    """

    TABLE_NAME = "fields"  # Uses existing fields table

    def __init__(self, db_path: str = None):
        """Initialize GIS service."""
        self.db_path = db_path or DEFAULT_DB_PATH
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database - uses existing fields table."""
        pass  # Fields table already exists

    def _row_to_response(self, row: sqlite3.Row, **kwargs) -> Dict[str, Any]:
        """Convert row to dict."""
        return dict(row)

    # ========================================================================
    # FIELD BOUNDARIES
    # ========================================================================

    def get_field_boundaries(
        self,
        field_ids: Optional[List[int]] = None,
        farm_name: Optional[str] = None
    ) -> GeoJSONFeatureCollection:
        """
        Get field boundaries as GeoJSON FeatureCollection.

        Args:
            field_ids: Optional list of field IDs to include
            farm_name: Optional farm name filter

        Returns:
            GeoJSON FeatureCollection
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, name, farm_name, acreage, current_crop, soil_type,
                       location_lat, location_lng, boundary
                FROM fields
                WHERE is_active = 1
            """
            params = []

            if field_ids:
                placeholders = ",".join("?" * len(field_ids))
                query += f" AND id IN ({placeholders})"
                params.extend(field_ids)

            if farm_name:
                query += " AND farm_name = ?"
                params.append(farm_name)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        features = []
        for row in rows:
            # Parse boundary GeoJSON or create point from coordinates
            geometry = None
            if row["boundary"]:
                try:
                    geometry = json.loads(row["boundary"])
                except json.JSONDecodeError:
                    pass

            if geometry is None and row["location_lat"] and row["location_lng"]:
                # Create point geometry from coordinates
                geometry = {
                    "type": "Point",
                    "coordinates": [row["location_lng"], row["location_lat"]]
                }

            if geometry:
                feature = GeoJSONFeature(
                    id=row["id"],
                    geometry=geometry,
                    properties={
                        "id": row["id"],
                        "name": row["name"],
                        "farm_name": row["farm_name"],
                        "acreage": row["acreage"],
                        "current_crop": row["current_crop"],
                        "soil_type": row["soil_type"]
                    }
                )
                features.append(feature)

        return GeoJSONFeatureCollection(features=features)

    def update_field_boundary(
        self,
        field_id: int,
        boundary: str,
        user_id: int,
        recalculate_acreage: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Update a field's boundary.

        Args:
            field_id: Field ID
            boundary: GeoJSON geometry string
            user_id: User making the update
            recalculate_acreage: Whether to recalculate acreage from geometry

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate GeoJSON
            geom_data = json.loads(boundary)
            if "type" not in geom_data:
                return False, "Invalid GeoJSON: missing type"

            acreage = None
            if recalculate_acreage and HAS_GIS_LIBS:
                try:
                    geom = shape(geom_data)
                    area_result = self.calculate_area(geom)
                    acreage = area_result.area_acres
                except Exception as e:
                    logger.warning("Could not calculate area: %s", e)

            # Also extract centroid for location_lat/lng
            center_lat = None
            center_lng = None
            if HAS_GIS_LIBS:
                try:
                    geom = shape(geom_data)
                    centroid = geom.centroid
                    center_lng = centroid.x
                    center_lat = centroid.y
                except Exception as e:
                    logger.warning("Could not calculate centroid: %s", e)

            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Build update query
                updates = ["boundary = ?", "updated_at = ?"]
                params = [boundary, datetime.now(timezone.utc).isoformat()]

                if acreage is not None:
                    updates.append("acreage = ?")
                    params.append(acreage)

                if center_lat is not None:
                    updates.append("location_lat = ?")
                    params.append(center_lat)

                if center_lng is not None:
                    updates.append("location_lng = ?")
                    params.append(center_lng)

                params.append(field_id)

                cursor.execute(f"""
                    UPDATE fields
                    SET {', '.join(updates)}
                    WHERE id = ? AND is_active = 1
                """, params)

                if cursor.rowcount == 0:
                    return False, "Field not found"

                # Log action
                self.auth_service.log_action(
                    user_id=user_id,
                    action="update_field_boundary",
                    entity_type="field",
                    entity_id=field_id,
                    conn=conn
                )

                conn.commit()

            return True, None

        except json.JSONDecodeError:
            return False, "Invalid JSON in boundary"
        except Exception as e:
            return False, self._sanitize_error(e, "boundary update")

    # ========================================================================
    # IMPORT OPERATIONS
    # ========================================================================

    def import_file(
        self,
        file_path: str,
        file_type: str = "auto",
        match_by: str = "name",
        user_id: Optional[int] = None
    ) -> ImportResult:
        """
        Import geographic data from file.

        Args:
            file_path: Path to file
            file_type: File type (auto, shapefile, kml, geojson)
            match_by: How to match imported features to existing fields
            user_id: User performing import

        Returns:
            ImportResult
        """
        if not HAS_GIS_LIBS:
            return ImportResult(
                success=False,
                message="GIS libraries not installed. Run: pip install geopandas shapely fiona pyproj"
            )

        if not os.path.exists(file_path):
            return ImportResult(success=False, message=f"File not found: {file_path}")

        try:
            # Detect file type
            if file_type == "auto":
                ext = os.path.splitext(file_path)[1].lower()
                if ext in [".shp", ".dbf", ".shx"]:
                    file_type = "shapefile"
                elif ext == ".kml":
                    file_type = "kml"
                elif ext in [".geojson", ".json"]:
                    file_type = "geojson"
                elif ext in [".gpkg"]:
                    file_type = "geopackage"
                else:
                    return ImportResult(success=False, message=f"Unknown file type: {ext}")

            # Read file with geopandas
            if file_type == "kml":
                gdf = gpd.read_file(file_path, driver="KML")
            else:
                gdf = gpd.read_file(file_path)

            # Transform to WGS84 if needed
            if gdf.crs and gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")

            imported_count = 0
            matched_count = 0
            errors = []
            features = []

            for idx, row in gdf.iterrows():
                try:
                    geom = row.geometry
                    if geom is None:
                        continue

                    # Extract properties
                    props = {}
                    for col in gdf.columns:
                        if col != "geometry":
                            val = row[col]
                            if val is not None and str(val) != "nan":
                                props[col] = str(val)

                    # Get name from common field names
                    name = None
                    for name_field in ["name", "Name", "NAME", "field_name", "FIELD_NAME", "label"]:
                        if name_field in props:
                            name = props[name_field]
                            break

                    # Convert geometry to GeoJSON string
                    geom_json = json.dumps(mapping(geom))

                    # Calculate area
                    area_acres = None
                    try:
                        area_result = self.calculate_area(geom)
                        area_acres = area_result.area_acres
                    except Exception:
                        pass

                    feature_data = {
                        "name": name or f"Imported Field {idx + 1}",
                        "geometry": mapping(geom),
                        "properties": props,
                        "area_acres": area_acres
                    }
                    features.append(feature_data)

                    # Match to existing field if requested
                    if match_by == "name" and name:
                        match_result = self._match_and_update_field(
                            name=name,
                            boundary=geom_json,
                            user_id=user_id
                        )
                        if match_result:
                            matched_count += 1
                        else:
                            imported_count += 1
                    else:
                        imported_count += 1

                except Exception as e:
                    errors.append(f"Error processing feature {idx}: {str(e)}")

            return ImportResult(
                success=True,
                message=f"Imported {imported_count} features, matched {matched_count} existing fields",
                imported_count=imported_count,
                matched_count=matched_count,
                errors=errors,
                features=features
            )

        except Exception as e:
            logger.error("Import error: %s", e)
            return ImportResult(success=False, message=f"Import failed: {str(e)}")

    def _match_and_update_field(
        self,
        name: str,
        boundary: str,
        user_id: Optional[int]
    ) -> bool:
        """Match imported feature to existing field by name."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM fields
                WHERE LOWER(name) = LOWER(?) AND is_active = 1
            """, (name,))

            row = cursor.fetchone()
            if row:
                success, _ = self.update_field_boundary(
                    row["id"], boundary, user_id or 1
                )
                return success

        return False

    # ========================================================================
    # EXPORT OPERATIONS
    # ========================================================================

    def export_to_format(
        self,
        format: str,
        field_ids: Optional[List[int]] = None,
        include_layers: bool = False,
        output_dir: Optional[str] = None
    ) -> ExportResult:
        """
        Export field boundaries to GIS format.

        Args:
            format: Output format (shapefile, geojson, kml, geopackage)
            field_ids: Optional list of field IDs (all if None)
            include_layers: Include custom layers
            output_dir: Output directory (temp if None)

        Returns:
            ExportResult
        """
        if not HAS_GIS_LIBS:
            return ExportResult(
                success=False,
                message="GIS libraries not installed"
            )

        try:
            # Get field boundaries
            fc = self.get_field_boundaries(field_ids=field_ids)

            if not fc.features:
                return ExportResult(
                    success=False,
                    message="No fields with boundaries found"
                )

            # Create GeoDataFrame
            features_for_gdf = []
            for f in fc.features:
                geom = shape(f.geometry)
                props = f.properties.copy()
                props["id"] = f.id
                features_for_gdf.append({"geometry": geom, **props})

            gdf = gpd.GeoDataFrame(features_for_gdf, crs="EPSG:4326")

            # Determine output path
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix="agtools_gis_")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if format == "shapefile":
                output_path = os.path.join(output_dir, f"fields_{timestamp}.shp")
                gdf.to_file(output_path, driver="ESRI Shapefile")
            elif format == "geojson":
                output_path = os.path.join(output_dir, f"fields_{timestamp}.geojson")
                gdf.to_file(output_path, driver="GeoJSON")
            elif format == "kml":
                output_path = os.path.join(output_dir, f"fields_{timestamp}.kml")
                gdf.to_file(output_path, driver="KML")
            elif format == "geopackage":
                output_path = os.path.join(output_dir, f"fields_{timestamp}.gpkg")
                gdf.to_file(output_path, driver="GPKG", layer="fields")
            else:
                return ExportResult(
                    success=False,
                    message=f"Unknown format: {format}"
                )

            return ExportResult(
                success=True,
                message=f"Exported {len(fc.features)} features",
                file_path=output_path,
                feature_count=len(fc.features)
            )

        except Exception as e:
            logger.error("Export error: %s", e)
            return ExportResult(success=False, message=f"Export failed: {str(e)}")

    # ========================================================================
    # COORDINATE TRANSFORMATIONS
    # ========================================================================

    def transform_coordinates(
        self,
        geometry: Dict[str, Any],
        from_crs: str = "EPSG:4326",
        to_crs: str = "EPSG:32614"  # UTM Zone 14N (central US)
    ) -> Dict[str, Any]:
        """
        Transform geometry coordinates between coordinate systems.

        Args:
            geometry: GeoJSON geometry
            from_crs: Source CRS (default WGS84)
            to_crs: Target CRS (default UTM Zone 14N)

        Returns:
            Transformed GeoJSON geometry
        """
        if not HAS_GIS_LIBS:
            raise RuntimeError("GIS libraries not installed")

        geom = shape(geometry)
        transformer = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True)
        transformed = transform(transformer.transform, geom)

        return mapping(transformed)

    def get_utm_zone(self, longitude: float) -> str:
        """
        Get UTM zone for a given longitude.

        Args:
            longitude: Longitude in degrees

        Returns:
            EPSG code for UTM zone
        """
        zone = int((longitude + 180) / 6) + 1
        # Assuming northern hemisphere for US farms
        return f"EPSG:326{zone:02d}"

    # ========================================================================
    # CALCULATIONS
    # ========================================================================

    def calculate_area(self, geometry) -> AreaResult:
        """
        Calculate area of a geometry.

        Args:
            geometry: Shapely geometry or GeoJSON dict

        Returns:
            AreaResult with area in various units
        """
        if not HAS_GIS_LIBS:
            raise RuntimeError("GIS libraries not installed")

        if isinstance(geometry, dict):
            geometry = shape(geometry)

        # Get centroid longitude to determine UTM zone
        centroid = geometry.centroid
        utm_crs = self.get_utm_zone(centroid.x)

        # Transform to UTM for accurate area calculation
        transformer = pyproj.Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)
        utm_geom = transform(transformer.transform, geometry)

        area_sq_meters = utm_geom.area
        perimeter_meters = utm_geom.length

        # Convert to other units
        area_acres = area_sq_meters / 4046.8564224  # sq meters to acres
        area_hectares = area_sq_meters / 10000  # sq meters to hectares

        return AreaResult(
            area_sq_meters=round(area_sq_meters, 2),
            area_acres=round(area_acres, 2),
            area_hectares=round(area_hectares, 4),
            perimeter_meters=round(perimeter_meters, 2)
        )

    def calculate_distance(
        self,
        point1: Tuple[float, float],
        point2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two points in meters.

        Args:
            point1: (longitude, latitude)
            point2: (longitude, latitude)

        Returns:
            Distance in meters
        """
        if not HAS_GIS_LIBS:
            raise RuntimeError("GIS libraries not installed")

        # Use geodesic calculation
        geod = pyproj.Geod(ellps="WGS84")
        _, _, distance = geod.inv(point1[0], point1[1], point2[0], point2[1])

        return abs(distance)

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def validate_boundary(self, boundary: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a GeoJSON boundary.

        Args:
            boundary: GeoJSON geometry string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            geom_data = json.loads(boundary)

            if "type" not in geom_data:
                return False, "Missing 'type' field"

            valid_types = ["Point", "LineString", "Polygon", "MultiPoint",
                          "MultiLineString", "MultiPolygon", "GeometryCollection"]
            if geom_data["type"] not in valid_types:
                return False, f"Invalid geometry type: {geom_data['type']}"

            if geom_data["type"] != "GeometryCollection" and "coordinates" not in geom_data:
                return False, "Missing 'coordinates' field"

            if HAS_GIS_LIBS:
                geom = shape(geom_data)
                if not geom.is_valid:
                    return False, f"Invalid geometry: {geom.is_valid}"

            return True, None

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    # ========================================================================
    # QGIS BRIDGE
    # ========================================================================

    def generate_qgis_project(
        self,
        field_ids: Optional[List[int]] = None,
        output_dir: Optional[str] = None
    ) -> QGISProjectResult:
        """
        Generate a QGIS project file with field data.

        Args:
            field_ids: Optional list of field IDs
            output_dir: Output directory

        Returns:
            QGISProjectResult
        """
        if not HAS_GIS_LIBS:
            return QGISProjectResult(
                success=False,
                message="GIS libraries not installed"
            )

        try:
            # Export to GeoPackage first
            export_result = self.export_to_format(
                format="geopackage",
                field_ids=field_ids,
                output_dir=output_dir
            )

            if not export_result.success:
                return QGISProjectResult(
                    success=False,
                    message=export_result.message
                )

            gpkg_path = export_result.file_path
            qgs_path = gpkg_path.replace(".gpkg", ".qgs")

            # Generate minimal QGIS project XML
            qgs_content = self._generate_qgis_xml(gpkg_path)

            with open(qgs_path, "w", encoding="utf-8") as f:
                f.write(qgs_content)

            return QGISProjectResult(
                success=True,
                project_path=qgs_path,
                geopackage_path=gpkg_path,
                message=f"Generated QGIS project with {export_result.feature_count} features"
            )

        except Exception as e:
            logger.error("QGIS project generation error: %s", e)
            return QGISProjectResult(
                success=False,
                message=f"Failed to generate QGIS project: {str(e)}"
            )

    def _generate_qgis_xml(self, gpkg_path: str) -> str:
        """Generate minimal QGIS project XML."""
        gpkg_name = os.path.basename(gpkg_path)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<qgis version="3.28" projectname="AgTools Fields">
  <title>AgTools Field Boundaries</title>
  <projectlayers>
    <maplayer geometry="Polygon" name="fields" type="vector">
      <datasource>./{gpkg_name}|layername=fields</datasource>
      <provider>ogr</provider>
    </maplayer>
  </projectlayers>
  <mapcanvas>
    <destinationsrs>
      <spatialrefsys>
        <authid>EPSG:4326</authid>
      </spatialrefsys>
    </destinationsrs>
  </mapcanvas>
</qgis>'''


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_gis_service: Optional[GISService] = None


def get_gis_service(db_path: str = None) -> GISService:
    """Get or create the GIS service singleton."""
    global _gis_service

    if _gis_service is None:
        _gis_service = GISService(db_path)

    return _gis_service
