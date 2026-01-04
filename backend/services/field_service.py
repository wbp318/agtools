"""
Field Service for Farm Operations Manager
Handles field CRUD operations and field management.

AgTools v2.5.0 Phase 3
"""

import sqlite3
from datetime import datetime
from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field

from .auth_service import get_auth_service


# ============================================================================
# ENUMS
# ============================================================================

class CropType(str, Enum):
    """Common crop types"""
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"
    COTTON = "cotton"
    RICE = "rice"
    SORGHUM = "sorghum"
    ALFALFA = "alfalfa"
    HAY = "hay"
    PASTURE = "pasture"
    FALLOW = "fallow"
    OTHER = "other"


class SoilType(str, Enum):
    """Soil types"""
    CLAY = "clay"
    CLAY_LOAM = "clay_loam"
    LOAM = "loam"
    SANDY_LOAM = "sandy_loam"
    SANDY = "sandy"
    SILT_LOAM = "silt_loam"
    SILTY_CLAY = "silty_clay"
    ORGANIC = "organic"
    OTHER = "other"


class IrrigationType(str, Enum):
    """Irrigation system types"""
    NONE = "none"
    CENTER_PIVOT = "center_pivot"
    DRIP = "drip"
    FLOOD = "flood"
    FURROW = "furrow"
    SPRINKLER = "sprinkler"
    SUBSURFACE = "subsurface"
    OTHER = "other"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class FieldCreate(BaseModel):
    """Create field request"""
    name: str = Field(..., min_length=1, max_length=100)
    farm_name: Optional[str] = Field(None, max_length=100)
    acreage: float = Field(..., gt=0)
    current_crop: Optional[CropType] = None
    soil_type: Optional[SoilType] = None
    irrigation_type: Optional[IrrigationType] = IrrigationType.NONE
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    boundary: Optional[str] = None  # GeoJSON string
    notes: Optional[str] = None


class FieldUpdate(BaseModel):
    """Update field request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    farm_name: Optional[str] = Field(None, max_length=100)
    acreage: Optional[float] = Field(None, gt=0)
    current_crop: Optional[CropType] = None
    soil_type: Optional[SoilType] = None
    irrigation_type: Optional[IrrigationType] = None
    location_lat: Optional[float] = Field(None, ge=-90, le=90)
    location_lng: Optional[float] = Field(None, ge=-180, le=180)
    boundary: Optional[str] = None
    notes: Optional[str] = None


class FieldResponse(BaseModel):
    """Field response with all data"""
    id: int
    name: str
    farm_name: Optional[str]
    acreage: float
    current_crop: Optional[str]
    soil_type: Optional[str]
    irrigation_type: Optional[str]
    location_lat: Optional[float]
    location_lng: Optional[float]
    boundary: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Computed fields
    total_operations: int = 0
    last_operation_date: Optional[datetime] = None


class FieldSummary(BaseModel):
    """Summary of all fields"""
    total_fields: int
    total_acreage: float
    fields_by_crop: dict
    fields_by_farm: dict


# ============================================================================
# FIELD SERVICE CLASS
# ============================================================================

class FieldService:
    """
    Field service handling:
    - Field CRUD operations
    - Field listing and filtering
    - Field statistics
    """

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize field service.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.auth_service = get_auth_service()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create fields table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                farm_name VARCHAR(100),
                acreage DECIMAL(10, 2) NOT NULL,
                current_crop VARCHAR(50),
                soil_type VARCHAR(50),
                irrigation_type VARCHAR(50),
                location_lat DECIMAL(10, 7),
                location_lng DECIMAL(10, 7),
                boundary TEXT,
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_name ON fields(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_farm ON fields(farm_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_crop ON fields(current_crop)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_created_by ON fields(created_by_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fields_active ON fields(is_active)")

        conn.commit()
        conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _safe_get(self, row: sqlite3.Row, key: str, default=None):
        """Safely get a value from a sqlite3.Row."""
        try:
            return row[key]
        except (KeyError, IndexError):
            return default

    def _row_to_response(self, row: sqlite3.Row, include_stats: bool = False) -> FieldResponse:
        """Convert a database row to FieldResponse."""
        response = FieldResponse(
            id=row["id"],
            name=row["name"],
            farm_name=row["farm_name"],
            acreage=float(row["acreage"]),
            current_crop=row["current_crop"],
            soil_type=row["soil_type"],
            irrigation_type=row["irrigation_type"],
            location_lat=float(row["location_lat"]) if row["location_lat"] else None,
            location_lng=float(row["location_lng"]) if row["location_lng"] else None,
            boundary=row["boundary"],
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=self._safe_get(row, "created_by_user_name"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            total_operations=self._safe_get(row, "total_operations", 0) if include_stats else 0,
            last_operation_date=self._safe_get(row, "last_operation_date") if include_stats else None
        )
        return response

    # ========================================================================
    # CRUD METHODS
    # ========================================================================

    def create_field(
        self,
        field_data: FieldCreate,
        created_by: int
    ) -> Tuple[Optional[FieldResponse], Optional[str]]:
        """
        Create a new field.

        Args:
            field_data: Field creation data
            created_by: ID of user creating this field

        Returns:
            Tuple of (FieldResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO fields (
                    name, farm_name, acreage, current_crop, soil_type,
                    irrigation_type, location_lat, location_lng, boundary,
                    notes, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                field_data.name,
                field_data.farm_name,
                field_data.acreage,
                field_data.current_crop.value if field_data.current_crop else None,
                field_data.soil_type.value if field_data.soil_type else None,
                field_data.irrigation_type.value if field_data.irrigation_type else None,
                field_data.location_lat,
                field_data.location_lng,
                field_data.boundary,
                field_data.notes,
                created_by
            ))

            field_id = cursor.lastrowid

            # Log action
            self.auth_service.db = conn
            self.auth_service.log_action(
                user_id=created_by,
                action="create_field",
                entity_type="field",
                entity_id=field_id
            )

            conn.commit()
            conn.close()

            return self.get_field_by_id(field_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def get_field_by_id(self, field_id: int, include_stats: bool = True) -> Optional[FieldResponse]:
        """Get field by ID with optional operation statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_stats:
            cursor.execute("""
                SELECT
                    f.*,
                    u.first_name || ' ' || u.last_name as created_by_user_name,
                    (SELECT COUNT(*) FROM field_operations WHERE field_id = f.id AND is_active = 1) as total_operations,
                    (SELECT MAX(operation_date) FROM field_operations WHERE field_id = f.id AND is_active = 1) as last_operation_date
                FROM fields f
                LEFT JOIN users u ON f.created_by_user_id = u.id
                WHERE f.id = ?
            """, (field_id,))
        else:
            cursor.execute("""
                SELECT
                    f.*,
                    u.first_name || ' ' || u.last_name as created_by_user_name
                FROM fields f
                LEFT JOIN users u ON f.created_by_user_id = u.id
                WHERE f.id = ?
            """, (field_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_response(row, include_stats)

    def list_fields(
        self,
        farm_name: Optional[str] = None,
        current_crop: Optional[CropType] = None,
        soil_type: Optional[SoilType] = None,
        irrigation_type: Optional[IrrigationType] = None,
        is_active: Optional[bool] = True,
        created_by_user_id: Optional[int] = None,
        include_stats: bool = True,
        search: Optional[str] = None
    ) -> List[FieldResponse]:
        """
        List fields with optional filters.

        Args:
            farm_name: Filter by farm name
            current_crop: Filter by crop type
            soil_type: Filter by soil type
            irrigation_type: Filter by irrigation type
            is_active: Filter by active status
            created_by_user_id: Filter by creator
            include_stats: Include operation statistics
            search: Search by field or farm name

        Returns:
            List of FieldResponse
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_stats:
            query = """
                SELECT
                    f.*,
                    u.first_name || ' ' || u.last_name as created_by_user_name,
                    (SELECT COUNT(*) FROM field_operations WHERE field_id = f.id AND is_active = 1) as total_operations,
                    (SELECT MAX(operation_date) FROM field_operations WHERE field_id = f.id AND is_active = 1) as last_operation_date
                FROM fields f
                LEFT JOIN users u ON f.created_by_user_id = u.id
            """
        else:
            query = """
                SELECT
                    f.*,
                    u.first_name || ' ' || u.last_name as created_by_user_name
                FROM fields f
                LEFT JOIN users u ON f.created_by_user_id = u.id
            """

        conditions = []
        params = []

        if farm_name:
            conditions.append("f.farm_name = ?")
            params.append(farm_name)

        if current_crop:
            conditions.append("f.current_crop = ?")
            params.append(current_crop.value)

        if soil_type:
            conditions.append("f.soil_type = ?")
            params.append(soil_type.value)

        if irrigation_type:
            conditions.append("f.irrigation_type = ?")
            params.append(irrigation_type.value)

        if is_active is not None:
            conditions.append("f.is_active = ?")
            params.append(1 if is_active else 0)

        if created_by_user_id:
            conditions.append("f.created_by_user_id = ?")
            params.append(created_by_user_id)

        if search:
            conditions.append("(f.name LIKE ? OR f.farm_name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY f.farm_name, f.name"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_response(row, include_stats) for row in rows]

    def update_field(
        self,
        field_id: int,
        field_data: FieldUpdate,
        updated_by: int
    ) -> Tuple[Optional[FieldResponse], Optional[str]]:
        """
        Update a field.

        Args:
            field_id: Field ID to update
            field_data: Update data
            updated_by: ID of user performing update

        Returns:
            Tuple of (FieldResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        params = []

        if field_data.name is not None:
            updates.append("name = ?")
            params.append(field_data.name)

        if field_data.farm_name is not None:
            updates.append("farm_name = ?")
            params.append(field_data.farm_name)

        if field_data.acreage is not None:
            updates.append("acreage = ?")
            params.append(field_data.acreage)

        if field_data.current_crop is not None:
            updates.append("current_crop = ?")
            params.append(field_data.current_crop.value)

        if field_data.soil_type is not None:
            updates.append("soil_type = ?")
            params.append(field_data.soil_type.value)

        if field_data.irrigation_type is not None:
            updates.append("irrigation_type = ?")
            params.append(field_data.irrigation_type.value)

        if field_data.location_lat is not None:
            updates.append("location_lat = ?")
            params.append(field_data.location_lat)

        if field_data.location_lng is not None:
            updates.append("location_lng = ?")
            params.append(field_data.location_lng)

        if field_data.boundary is not None:
            updates.append("boundary = ?")
            params.append(field_data.boundary)

        if field_data.notes is not None:
            updates.append("notes = ?")
            params.append(field_data.notes)

        if not updates:
            conn.close()
            return self.get_field_by_id(field_id), None

        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.append(field_id)

        try:
            cursor.execute(f"""
                UPDATE fields SET {', '.join(updates)} WHERE id = ?
            """, params)

            # Log action
            self.auth_service.db = conn
            self.auth_service.log_action(
                user_id=updated_by,
                action="update_field",
                entity_type="field",
                entity_id=field_id
            )

            conn.commit()
            conn.close()

            return self.get_field_by_id(field_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def delete_field(
        self,
        field_id: int,
        deleted_by: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Soft delete a field.

        Args:
            field_id: Field ID to delete
            deleted_by: ID of user performing deletion

        Returns:
            Tuple of (success, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE fields SET is_active = 0, updated_at = ? WHERE id = ?
        """, (datetime.utcnow(), field_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "Field not found"

        # Log action
        self.auth_service.db = conn
        self.auth_service.log_action(
            user_id=deleted_by,
            action="delete_field",
            entity_type="field",
            entity_id=field_id
        )

        conn.commit()
        conn.close()

        return True, None

    # ========================================================================
    # STATISTICS METHODS
    # ========================================================================

    def get_field_summary(self, is_active: bool = True) -> FieldSummary:
        """
        Get summary statistics for all fields.

        Args:
            is_active: Only include active fields

        Returns:
            FieldSummary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total fields and acreage
        cursor.execute("""
            SELECT COUNT(*) as total_fields, COALESCE(SUM(acreage), 0) as total_acreage
            FROM fields WHERE is_active = ?
        """, (1 if is_active else 0,))

        row = cursor.fetchone()
        total_fields = row["total_fields"]
        total_acreage = float(row["total_acreage"])

        # Fields by crop
        cursor.execute("""
            SELECT current_crop, COUNT(*) as count, SUM(acreage) as acreage
            FROM fields WHERE is_active = ? AND current_crop IS NOT NULL
            GROUP BY current_crop
        """, (1 if is_active else 0,))

        fields_by_crop = {}
        for row in cursor.fetchall():
            fields_by_crop[row["current_crop"]] = {
                "count": row["count"],
                "acreage": float(row["acreage"])
            }

        # Fields by farm
        cursor.execute("""
            SELECT COALESCE(farm_name, 'Unassigned') as farm, COUNT(*) as count, SUM(acreage) as acreage
            FROM fields WHERE is_active = ?
            GROUP BY farm_name
        """, (1 if is_active else 0,))

        fields_by_farm = {}
        for row in cursor.fetchall():
            fields_by_farm[row["farm"]] = {
                "count": row["count"],
                "acreage": float(row["acreage"])
            }

        conn.close()

        return FieldSummary(
            total_fields=total_fields,
            total_acreage=total_acreage,
            fields_by_crop=fields_by_crop,
            fields_by_farm=fields_by_farm
        )

    def get_farm_names(self) -> List[str]:
        """Get list of unique farm names for dropdown filtering."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT farm_name FROM fields
            WHERE farm_name IS NOT NULL AND is_active = 1
            ORDER BY farm_name
        """)

        names = [row["farm_name"] for row in cursor.fetchall()]
        conn.close()

        return names


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_field_service: Optional[FieldService] = None


def get_field_service(db_path: str = "agtools.db") -> FieldService:
    """Get or create the field service singleton."""
    global _field_service

    if _field_service is None:
        _field_service = FieldService(db_path)

    return _field_service
