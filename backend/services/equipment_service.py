"""
Equipment Service for Farm Operations Manager
Handles equipment fleet management, maintenance scheduling, and usage tracking.

AgTools v2.5.0 Phase 4
"""

import sqlite3
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field

from .auth_service import get_auth_service


# ============================================================================
# ENUMS
# ============================================================================

class EquipmentType(str, Enum):
    """Types of farm equipment"""
    TRACTOR = "tractor"
    COMBINE = "combine"
    SPRAYER = "sprayer"
    PLANTER = "planter"
    TILLAGE = "tillage"
    TRUCK = "truck"
    ATV = "atv"
    GRAIN_CART = "grain_cart"
    WAGON = "wagon"
    MOWER = "mower"
    BALER = "baler"
    LOADER = "loader"
    DRILL = "drill"
    APPLICATOR = "applicator"
    OTHER = "other"


class EquipmentStatus(str, Enum):
    """Equipment availability status"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class MaintenanceType(str, Enum):
    """Types of maintenance activities"""
    OIL_CHANGE = "oil_change"
    FILTER = "filter"
    REPAIRS = "repairs"
    INSPECTION = "inspection"
    TIRES = "tires"
    BRAKES = "brakes"
    HYDRAULICS = "hydraulics"
    ELECTRICAL = "electrical"
    WINTERIZATION = "winterization"
    CALIBRATION = "calibration"
    GREASING = "greasing"
    OTHER = "other"


# ============================================================================
# PYDANTIC MODELS - EQUIPMENT
# ============================================================================

class EquipmentCreate(BaseModel):
    """Create equipment request"""
    name: str = Field(..., min_length=1, max_length=100)
    equipment_type: EquipmentType

    # Identification
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    serial_number: Optional[str] = Field(None, max_length=100)

    # Acquisition
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)

    # Operating costs
    hourly_rate: Optional[float] = Field(None, ge=0)

    # Usage
    current_hours: Optional[float] = Field(0, ge=0)

    # Status
    status: Optional[EquipmentStatus] = EquipmentStatus.AVAILABLE
    current_location: Optional[str] = Field(None, max_length=100)

    # Notes
    notes: Optional[str] = None


class EquipmentUpdate(BaseModel):
    """Update equipment request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    equipment_type: Optional[EquipmentType] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    serial_number: Optional[str] = Field(None, max_length=100)
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    hourly_rate: Optional[float] = Field(None, ge=0)
    current_hours: Optional[float] = Field(None, ge=0)
    status: Optional[EquipmentStatus] = None
    current_location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class EquipmentResponse(BaseModel):
    """Equipment response with all data"""
    id: int
    name: str
    equipment_type: EquipmentType
    make: Optional[str]
    model: Optional[str]
    year: Optional[int]
    serial_number: Optional[str]
    purchase_date: Optional[date]
    purchase_cost: Optional[float]
    current_value: Optional[float]
    hourly_rate: Optional[float]
    current_hours: float
    status: EquipmentStatus
    current_location: Optional[str]
    notes: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# PYDANTIC MODELS - MAINTENANCE
# ============================================================================

class MaintenanceCreate(BaseModel):
    """Create maintenance record request"""
    equipment_id: int
    maintenance_type: MaintenanceType
    service_date: date

    # Scheduling
    next_service_date: Optional[date] = None
    next_service_hours: Optional[float] = Field(None, ge=0)

    # Cost
    cost: Optional[float] = Field(None, ge=0)

    # Who performed
    performed_by: Optional[str] = Field(None, max_length=100)
    vendor: Optional[str] = Field(None, max_length=100)

    # Details
    description: Optional[str] = None
    parts_used: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    """Update maintenance record request"""
    maintenance_type: Optional[MaintenanceType] = None
    service_date: Optional[date] = None
    next_service_date: Optional[date] = None
    next_service_hours: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    performed_by: Optional[str] = Field(None, max_length=100)
    vendor: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parts_used: Optional[str] = None


class MaintenanceResponse(BaseModel):
    """Maintenance record response"""
    id: int
    equipment_id: int
    equipment_name: Optional[str] = None
    maintenance_type: MaintenanceType
    service_date: date
    next_service_date: Optional[date]
    next_service_hours: Optional[float]
    cost: Optional[float]
    performed_by: Optional[str]
    vendor: Optional[str]
    description: Optional[str]
    parts_used: Optional[str]
    created_by_user_id: int
    created_by_user_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# PYDANTIC MODELS - USAGE
# ============================================================================

class EquipmentUsageCreate(BaseModel):
    """Create equipment usage record"""
    equipment_id: int
    field_operation_id: Optional[int] = None
    usage_date: date
    hours_used: Optional[float] = Field(None, ge=0)
    starting_hours: Optional[float] = Field(None, ge=0)
    ending_hours: Optional[float] = Field(None, ge=0)
    fuel_used: Optional[float] = Field(None, ge=0)
    fuel_unit: Optional[str] = Field("gallons", max_length=20)
    operator_id: Optional[int] = None
    notes: Optional[str] = None


class EquipmentUsageResponse(BaseModel):
    """Equipment usage record response"""
    id: int
    equipment_id: int
    equipment_name: Optional[str] = None
    field_operation_id: Optional[int]
    usage_date: date
    hours_used: Optional[float]
    starting_hours: Optional[float]
    ending_hours: Optional[float]
    fuel_used: Optional[float]
    fuel_unit: Optional[str]
    operator_id: Optional[int]
    operator_name: Optional[str] = None
    notes: Optional[str]
    created_by_user_id: int
    created_at: datetime


# ============================================================================
# PYDANTIC MODELS - SUMMARY & ALERTS
# ============================================================================

class EquipmentSummary(BaseModel):
    """Summary of equipment fleet"""
    total_equipment: int
    equipment_by_type: dict
    equipment_by_status: dict
    total_value: float
    total_hours: float
    in_maintenance: int


class MaintenanceAlert(BaseModel):
    """Upcoming maintenance alert"""
    equipment_id: int
    equipment_name: str
    equipment_type: EquipmentType
    maintenance_type: MaintenanceType
    last_service_date: Optional[date]
    next_service_date: Optional[date]
    next_service_hours: Optional[float]
    current_hours: float
    hours_until_service: Optional[float]
    days_until_service: Optional[int]
    urgency: str  # overdue, due_soon, upcoming


# ============================================================================
# EQUIPMENT SERVICE CLASS
# ============================================================================

class EquipmentService:
    """
    Equipment service handling:
    - Equipment CRUD
    - Maintenance records
    - Usage tracking
    - Alerts and summaries
    """

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize equipment service.

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

        # Create equipment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                equipment_type VARCHAR(50) NOT NULL,
                make VARCHAR(100),
                model VARCHAR(100),
                year INTEGER,
                serial_number VARCHAR(100),
                purchase_date DATE,
                purchase_cost DECIMAL(12, 2),
                current_value DECIMAL(12, 2),
                hourly_rate DECIMAL(8, 2),
                current_hours DECIMAL(10, 1) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'available',
                current_location VARCHAR(100),
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create equipment_maintenance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment_maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                maintenance_type VARCHAR(50) NOT NULL,
                service_date DATE NOT NULL,
                next_service_date DATE,
                next_service_hours DECIMAL(10, 1),
                cost DECIMAL(10, 2),
                performed_by VARCHAR(100),
                vendor VARCHAR(100),
                description TEXT,
                parts_used TEXT,
                created_by_user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create equipment_usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipment_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER NOT NULL,
                field_operation_id INTEGER,
                usage_date DATE NOT NULL,
                hours_used DECIMAL(8, 1),
                starting_hours DECIMAL(10, 1),
                ending_hours DECIMAL(10, 1),
                fuel_used DECIMAL(8, 2),
                fuel_unit VARCHAR(20) DEFAULT 'gallons',
                operator_id INTEGER,
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (equipment_id) REFERENCES equipment(id),
                FOREIGN KEY (field_operation_id) REFERENCES field_operations(id),
                FOREIGN KEY (operator_id) REFERENCES users(id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_equipment_active ON equipment(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maint_equipment ON equipment_maintenance(equipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maint_type ON equipment_maintenance(maintenance_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_maint_date ON equipment_maintenance(service_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_equipment ON equipment_usage(equipment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_date ON equipment_usage(usage_date)")

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

    def _row_to_equipment_response(self, row: sqlite3.Row) -> EquipmentResponse:
        """Convert a database row to EquipmentResponse."""
        return EquipmentResponse(
            id=row["id"],
            name=row["name"],
            equipment_type=EquipmentType(row["equipment_type"]),
            make=row["make"],
            model=row["model"],
            year=row["year"],
            serial_number=row["serial_number"],
            purchase_date=row["purchase_date"],
            purchase_cost=float(row["purchase_cost"]) if row["purchase_cost"] else None,
            current_value=float(row["current_value"]) if row["current_value"] else None,
            hourly_rate=float(row["hourly_rate"]) if row["hourly_rate"] else None,
            current_hours=float(row["current_hours"]) if row["current_hours"] else 0,
            status=EquipmentStatus(row["status"]),
            current_location=row["current_location"],
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=self._safe_get(row, "created_by_user_name"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _row_to_maintenance_response(self, row: sqlite3.Row) -> MaintenanceResponse:
        """Convert a database row to MaintenanceResponse."""
        return MaintenanceResponse(
            id=row["id"],
            equipment_id=row["equipment_id"],
            equipment_name=self._safe_get(row, "equipment_name"),
            maintenance_type=MaintenanceType(row["maintenance_type"]),
            service_date=row["service_date"],
            next_service_date=row["next_service_date"],
            next_service_hours=float(row["next_service_hours"]) if row["next_service_hours"] else None,
            cost=float(row["cost"]) if row["cost"] else None,
            performed_by=row["performed_by"],
            vendor=row["vendor"],
            description=row["description"],
            parts_used=row["parts_used"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=self._safe_get(row, "created_by_user_name"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def _row_to_usage_response(self, row: sqlite3.Row) -> EquipmentUsageResponse:
        """Convert a database row to EquipmentUsageResponse."""
        return EquipmentUsageResponse(
            id=row["id"],
            equipment_id=row["equipment_id"],
            equipment_name=self._safe_get(row, "equipment_name"),
            field_operation_id=row["field_operation_id"],
            usage_date=row["usage_date"],
            hours_used=float(row["hours_used"]) if row["hours_used"] else None,
            starting_hours=float(row["starting_hours"]) if row["starting_hours"] else None,
            ending_hours=float(row["ending_hours"]) if row["ending_hours"] else None,
            fuel_used=float(row["fuel_used"]) if row["fuel_used"] else None,
            fuel_unit=row["fuel_unit"],
            operator_id=row["operator_id"],
            operator_name=self._safe_get(row, "operator_name"),
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_at=row["created_at"]
        )

    # ========================================================================
    # EQUIPMENT CRUD
    # ========================================================================

    def create_equipment(
        self,
        equip_data: EquipmentCreate,
        created_by: int
    ) -> Tuple[Optional[EquipmentResponse], Optional[str]]:
        """Create a new equipment record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO equipment (
                    name, equipment_type, make, model, year, serial_number,
                    purchase_date, purchase_cost, current_value, hourly_rate,
                    current_hours, status, current_location, notes, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                equip_data.name,
                equip_data.equipment_type.value,
                equip_data.make,
                equip_data.model,
                equip_data.year,
                equip_data.serial_number,
                equip_data.purchase_date.isoformat() if equip_data.purchase_date else None,
                equip_data.purchase_cost,
                equip_data.current_value,
                equip_data.hourly_rate,
                equip_data.current_hours or 0,
                equip_data.status.value if equip_data.status else EquipmentStatus.AVAILABLE.value,
                equip_data.current_location,
                equip_data.notes,
                created_by
            ))

            equip_id = cursor.lastrowid
            conn.commit()

            # Log action
            self.auth_service.log_action(
                created_by,
                "create_equipment",
                f"Created equipment: {equip_data.name}"
            )

            return self.get_equipment_by_id(equip_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def get_equipment_by_id(self, equip_id: int) -> Optional[EquipmentResponse]:
        """Get equipment by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.*,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM equipment e
            LEFT JOIN users u ON e.created_by_user_id = u.id
            WHERE e.id = ? AND e.is_active = 1
        """, (equip_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_equipment_response(row)
        return None

    def list_equipment(
        self,
        equipment_type: Optional[EquipmentType] = None,
        status: Optional[EquipmentStatus] = None,
        search: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[EquipmentResponse]:
        """List equipment with optional filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                e.*,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM equipment e
            LEFT JOIN users u ON e.created_by_user_id = u.id
        """

        conditions = []
        params = []

        conditions.append("e.is_active = ?")
        params.append(1 if is_active else 0)

        if equipment_type:
            conditions.append("e.equipment_type = ?")
            params.append(equipment_type.value)

        if status:
            conditions.append("e.status = ?")
            params.append(status.value)

        if search:
            conditions.append("(e.name LIKE ? OR e.make LIKE ? OR e.model LIKE ? OR e.serial_number LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY e.name LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_equipment_response(row) for row in rows]

    def update_equipment(
        self,
        equip_id: int,
        equip_data: EquipmentUpdate,
        updated_by: int
    ) -> Tuple[Optional[EquipmentResponse], Optional[str]]:
        """Update equipment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update
        updates = []
        params = []

        if equip_data.name is not None:
            updates.append("name = ?")
            params.append(equip_data.name)
        if equip_data.equipment_type is not None:
            updates.append("equipment_type = ?")
            params.append(equip_data.equipment_type.value)
        if equip_data.make is not None:
            updates.append("make = ?")
            params.append(equip_data.make)
        if equip_data.model is not None:
            updates.append("model = ?")
            params.append(equip_data.model)
        if equip_data.year is not None:
            updates.append("year = ?")
            params.append(equip_data.year)
        if equip_data.serial_number is not None:
            updates.append("serial_number = ?")
            params.append(equip_data.serial_number)
        if equip_data.purchase_date is not None:
            updates.append("purchase_date = ?")
            params.append(equip_data.purchase_date.isoformat())
        if equip_data.purchase_cost is not None:
            updates.append("purchase_cost = ?")
            params.append(equip_data.purchase_cost)
        if equip_data.current_value is not None:
            updates.append("current_value = ?")
            params.append(equip_data.current_value)
        if equip_data.hourly_rate is not None:
            updates.append("hourly_rate = ?")
            params.append(equip_data.hourly_rate)
        if equip_data.current_hours is not None:
            updates.append("current_hours = ?")
            params.append(equip_data.current_hours)
        if equip_data.status is not None:
            updates.append("status = ?")
            params.append(equip_data.status.value)
        if equip_data.current_location is not None:
            updates.append("current_location = ?")
            params.append(equip_data.current_location)
        if equip_data.notes is not None:
            updates.append("notes = ?")
            params.append(equip_data.notes)

        if not updates:
            return self.get_equipment_by_id(equip_id), None

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(equip_id)

        try:
            cursor.execute(
                f"UPDATE equipment SET {', '.join(updates)} WHERE id = ? AND is_active = 1",
                params
            )

            if cursor.rowcount == 0:
                conn.close()
                return None, "Equipment not found"

            conn.commit()

            self.auth_service.log_action(
                updated_by,
                "update_equipment",
                f"Updated equipment ID: {equip_id}"
            )

            return self.get_equipment_by_id(equip_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def delete_equipment(
        self,
        equip_id: int,
        deleted_by: int
    ) -> Tuple[bool, Optional[str]]:
        """Soft delete equipment (set status to retired)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE equipment
                SET is_active = 0, status = ?, updated_at = ?
                WHERE id = ? AND is_active = 1
            """, (EquipmentStatus.RETIRED.value, datetime.utcnow().isoformat(), equip_id))

            if cursor.rowcount == 0:
                conn.close()
                return False, "Equipment not found"

            conn.commit()

            self.auth_service.log_action(
                deleted_by,
                "delete_equipment",
                f"Retired equipment ID: {equip_id}"
            )

            return True, None

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def update_hours(
        self,
        equip_id: int,
        new_hours: float,
        updated_by: int
    ) -> Tuple[Optional[EquipmentResponse], Optional[str]]:
        """Update equipment hour meter."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE equipment
                SET current_hours = ?, updated_at = ?
                WHERE id = ? AND is_active = 1
            """, (new_hours, datetime.utcnow().isoformat(), equip_id))

            if cursor.rowcount == 0:
                conn.close()
                return None, "Equipment not found"

            conn.commit()

            self.auth_service.log_action(
                updated_by,
                "update_equipment_hours",
                f"Updated hours for equipment ID: {equip_id} to {new_hours}"
            )

            return self.get_equipment_by_id(equip_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    # ========================================================================
    # MAINTENANCE CRUD
    # ========================================================================

    def create_maintenance(
        self,
        maint_data: MaintenanceCreate,
        created_by: int
    ) -> Tuple[Optional[MaintenanceResponse], Optional[str]]:
        """Create a maintenance record."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify equipment exists
        cursor.execute("SELECT id FROM equipment WHERE id = ? AND is_active = 1", (maint_data.equipment_id,))
        if not cursor.fetchone():
            conn.close()
            return None, "Equipment not found"

        try:
            cursor.execute("""
                INSERT INTO equipment_maintenance (
                    equipment_id, maintenance_type, service_date,
                    next_service_date, next_service_hours,
                    cost, performed_by, vendor, description, parts_used,
                    created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                maint_data.equipment_id,
                maint_data.maintenance_type.value,
                maint_data.service_date.isoformat(),
                maint_data.next_service_date.isoformat() if maint_data.next_service_date else None,
                maint_data.next_service_hours,
                maint_data.cost,
                maint_data.performed_by,
                maint_data.vendor,
                maint_data.description,
                maint_data.parts_used,
                created_by
            ))

            maint_id = cursor.lastrowid
            conn.commit()

            self.auth_service.log_action(
                created_by,
                "create_maintenance",
                f"Logged maintenance for equipment ID: {maint_data.equipment_id}"
            )

            return self.get_maintenance_by_id(maint_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def get_maintenance_by_id(self, maint_id: int) -> Optional[MaintenanceResponse]:
        """Get maintenance record by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                m.*,
                e.name as equipment_name,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM equipment_maintenance m
            LEFT JOIN equipment e ON m.equipment_id = e.id
            LEFT JOIN users u ON m.created_by_user_id = u.id
            WHERE m.id = ? AND m.is_active = 1
        """, (maint_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_maintenance_response(row)
        return None

    def list_maintenance(
        self,
        equipment_id: Optional[int] = None,
        maintenance_type: Optional[MaintenanceType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[MaintenanceResponse]:
        """List maintenance records with filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                m.*,
                e.name as equipment_name,
                u.first_name || ' ' || u.last_name as created_by_user_name
            FROM equipment_maintenance m
            LEFT JOIN equipment e ON m.equipment_id = e.id
            LEFT JOIN users u ON m.created_by_user_id = u.id
        """

        conditions = []
        params = []

        conditions.append("m.is_active = ?")
        params.append(1 if is_active else 0)

        if equipment_id:
            conditions.append("m.equipment_id = ?")
            params.append(equipment_id)

        if maintenance_type:
            conditions.append("m.maintenance_type = ?")
            params.append(maintenance_type.value)

        if date_from:
            conditions.append("m.service_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("m.service_date <= ?")
            params.append(date_to.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY m.service_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_maintenance_response(row) for row in rows]

    def get_equipment_maintenance_history(
        self,
        equipment_id: int,
        limit: int = 50
    ) -> List[MaintenanceResponse]:
        """Get maintenance history for specific equipment."""
        return self.list_maintenance(equipment_id=equipment_id, limit=limit)

    # ========================================================================
    # USAGE TRACKING
    # ========================================================================

    def log_usage(
        self,
        usage_data: EquipmentUsageCreate,
        created_by: int
    ) -> Tuple[Optional[EquipmentUsageResponse], Optional[str]]:
        """Log equipment usage."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify equipment exists
        cursor.execute("SELECT id, current_hours FROM equipment WHERE id = ? AND is_active = 1",
                       (usage_data.equipment_id,))
        equipment = cursor.fetchone()
        if not equipment:
            conn.close()
            return None, "Equipment not found"

        # Calculate hours_used if not provided but starting/ending hours are
        hours_used = usage_data.hours_used
        if hours_used is None and usage_data.starting_hours and usage_data.ending_hours:
            hours_used = usage_data.ending_hours - usage_data.starting_hours

        try:
            cursor.execute("""
                INSERT INTO equipment_usage (
                    equipment_id, field_operation_id, usage_date,
                    hours_used, starting_hours, ending_hours,
                    fuel_used, fuel_unit, operator_id, notes,
                    created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage_data.equipment_id,
                usage_data.field_operation_id,
                usage_data.usage_date.isoformat(),
                hours_used,
                usage_data.starting_hours,
                usage_data.ending_hours,
                usage_data.fuel_used,
                usage_data.fuel_unit,
                usage_data.operator_id,
                usage_data.notes,
                created_by
            ))

            usage_id = cursor.lastrowid

            # Update equipment's current hours if ending_hours provided
            if usage_data.ending_hours and usage_data.ending_hours > (equipment["current_hours"] or 0):
                cursor.execute("""
                    UPDATE equipment SET current_hours = ?, updated_at = ?
                    WHERE id = ?
                """, (usage_data.ending_hours, datetime.utcnow().isoformat(), usage_data.equipment_id))

            conn.commit()

            return self.get_usage_by_id(usage_id), None

        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    def get_usage_by_id(self, usage_id: int) -> Optional[EquipmentUsageResponse]:
        """Get usage record by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                eu.*,
                e.name as equipment_name,
                u.first_name || ' ' || u.last_name as operator_name
            FROM equipment_usage eu
            LEFT JOIN equipment e ON eu.equipment_id = e.id
            LEFT JOIN users u ON eu.operator_id = u.id
            WHERE eu.id = ?
        """, (usage_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_usage_response(row)
        return None

    def get_equipment_usage_history(
        self,
        equipment_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[EquipmentUsageResponse]:
        """Get usage history for specific equipment."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                eu.*,
                e.name as equipment_name,
                u.first_name || ' ' || u.last_name as operator_name
            FROM equipment_usage eu
            LEFT JOIN equipment e ON eu.equipment_id = e.id
            LEFT JOIN users u ON eu.operator_id = u.id
            WHERE eu.equipment_id = ?
        """

        params = [equipment_id]

        if date_from:
            query += " AND eu.usage_date >= ?"
            params.append(date_from.isoformat())

        if date_to:
            query += " AND eu.usage_date <= ?"
            params.append(date_to.isoformat())

        query += " ORDER BY eu.usage_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_usage_response(row) for row in rows]

    # ========================================================================
    # SUMMARY AND ALERTS
    # ========================================================================

    def get_equipment_summary(self, is_active: bool = True) -> EquipmentSummary:
        """Get summary of equipment fleet."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get counts by type
        cursor.execute("""
            SELECT equipment_type, COUNT(*) as count
            FROM equipment WHERE is_active = ?
            GROUP BY equipment_type
        """, (1 if is_active else 0,))
        by_type = {row["equipment_type"]: row["count"] for row in cursor.fetchall()}

        # Get counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM equipment WHERE is_active = ?
            GROUP BY status
        """, (1 if is_active else 0,))
        by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Get totals
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(current_value), 0) as total_value,
                COALESCE(SUM(current_hours), 0) as total_hours
            FROM equipment WHERE is_active = ?
        """, (1 if is_active else 0,))
        totals = cursor.fetchone()

        conn.close()

        return EquipmentSummary(
            total_equipment=totals["total"],
            equipment_by_type=by_type,
            equipment_by_status=by_status,
            total_value=float(totals["total_value"]),
            total_hours=float(totals["total_hours"]),
            in_maintenance=by_status.get("maintenance", 0)
        )

    def get_maintenance_alerts(self, days_ahead: int = 30) -> List[MaintenanceAlert]:
        """Get upcoming maintenance alerts."""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()

        # Get last maintenance for each equipment type combo and check against next service
        cursor.execute("""
            SELECT
                e.id as equipment_id,
                e.name as equipment_name,
                e.equipment_type,
                e.current_hours,
                m.maintenance_type,
                m.service_date as last_service_date,
                m.next_service_date,
                m.next_service_hours
            FROM equipment e
            LEFT JOIN (
                SELECT equipment_id, maintenance_type, service_date, next_service_date, next_service_hours,
                       ROW_NUMBER() OVER (PARTITION BY equipment_id, maintenance_type ORDER BY service_date DESC) as rn
                FROM equipment_maintenance
                WHERE is_active = 1
            ) m ON e.id = m.equipment_id AND m.rn = 1
            WHERE e.is_active = 1
            AND (m.next_service_date IS NOT NULL OR m.next_service_hours IS NOT NULL)
        """)

        alerts = []
        for row in cursor.fetchall():
            next_date = row["next_service_date"]
            next_hours = row["next_service_hours"]
            current_hours = float(row["current_hours"]) if row["current_hours"] else 0

            days_until = None
            hours_until = None
            urgency = "upcoming"

            if next_date:
                next_date_parsed = date.fromisoformat(next_date) if isinstance(next_date, str) else next_date
                days_until = (next_date_parsed - today).days
                if days_until < 0:
                    urgency = "overdue"
                elif days_until <= 7:
                    urgency = "due_soon"

            if next_hours:
                hours_until = float(next_hours) - current_hours
                if hours_until <= 0:
                    urgency = "overdue"
                elif hours_until <= 50:
                    urgency = "due_soon"

            # Only include if within the alert window or overdue
            if days_until is not None and days_until <= days_ahead:
                alerts.append(MaintenanceAlert(
                    equipment_id=row["equipment_id"],
                    equipment_name=row["equipment_name"],
                    equipment_type=EquipmentType(row["equipment_type"]),
                    maintenance_type=MaintenanceType(row["maintenance_type"]),
                    last_service_date=row["last_service_date"],
                    next_service_date=next_date,
                    next_service_hours=next_hours,
                    current_hours=current_hours,
                    hours_until_service=hours_until,
                    days_until_service=days_until,
                    urgency=urgency
                ))
            elif hours_until is not None and (hours_until <= 100 or urgency == "overdue"):
                alerts.append(MaintenanceAlert(
                    equipment_id=row["equipment_id"],
                    equipment_name=row["equipment_name"],
                    equipment_type=EquipmentType(row["equipment_type"]),
                    maintenance_type=MaintenanceType(row["maintenance_type"]),
                    last_service_date=row["last_service_date"],
                    next_service_date=next_date,
                    next_service_hours=next_hours,
                    current_hours=current_hours,
                    hours_until_service=hours_until,
                    days_until_service=days_until,
                    urgency=urgency
                ))

        conn.close()

        # Sort by urgency (overdue first, then due_soon, then upcoming)
        urgency_order = {"overdue": 0, "due_soon": 1, "upcoming": 2}
        alerts.sort(key=lambda a: (urgency_order.get(a.urgency, 3), a.days_until_service or 999))

        return alerts

    def get_equipment_types(self) -> List[dict]:
        """Get list of equipment types for dropdowns."""
        return [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in EquipmentType
        ]

    def get_equipment_statuses(self) -> List[dict]:
        """Get list of equipment statuses for dropdowns."""
        return [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in EquipmentStatus
        ]

    def get_maintenance_types(self) -> List[dict]:
        """Get list of maintenance types for dropdowns."""
        return [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in MaintenanceType
        ]


# ============================================================================
# SINGLETON
# ============================================================================

_equipment_service: Optional[EquipmentService] = None


def get_equipment_service(db_path: str = "agtools.db") -> EquipmentService:
    """Get or create the equipment service singleton."""
    global _equipment_service

    if _equipment_service is None:
        _equipment_service = EquipmentService(db_path)

    return _equipment_service
