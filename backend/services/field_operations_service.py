"""
Field Operations Service for Farm Operations Manager
Handles operation/activity logging for fields.

AgTools v2.5.0 Phase 3
"""

import sqlite3
from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional, List, Tuple

from pydantic import BaseModel, Field

from .auth_service import get_auth_service


# ============================================================================
# ENUMS
# ============================================================================

class OperationType(str, Enum):
    """Types of field operations"""
    SPRAY = "spray"
    FERTILIZER = "fertilizer"
    PLANTING = "planting"
    HARVEST = "harvest"
    TILLAGE = "tillage"
    SCOUTING = "scouting"
    IRRIGATION = "irrigation"
    SEED_TREATMENT = "seed_treatment"
    COVER_CROP = "cover_crop"
    OTHER = "other"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class OperationCreate(BaseModel):
    """Create operation request"""
    field_id: int
    operation_type: OperationType
    operation_date: date

    # Product info (optional)
    product_name: Optional[str] = Field(None, max_length=200)
    rate: Optional[float] = Field(None, ge=0)
    rate_unit: Optional[str] = Field(None, max_length=50)
    quantity: Optional[float] = Field(None, ge=0)
    quantity_unit: Optional[str] = Field(None, max_length=50)

    # Area
    acres_covered: Optional[float] = Field(None, gt=0)

    # Cost
    product_cost: Optional[float] = Field(None, ge=0)
    application_cost: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)

    # Harvest specific
    yield_amount: Optional[float] = Field(None, ge=0)
    yield_unit: Optional[str] = Field(None, max_length=20)
    moisture_percent: Optional[float] = Field(None, ge=0, le=100)

    # Weather
    weather_temp: Optional[float] = None
    weather_wind: Optional[float] = Field(None, ge=0)
    weather_humidity: Optional[float] = Field(None, ge=0, le=100)
    weather_notes: Optional[str] = None

    # Links
    operator_id: Optional[int] = None
    task_id: Optional[int] = None

    # Notes
    notes: Optional[str] = None


class OperationUpdate(BaseModel):
    """Update operation request"""
    operation_type: Optional[OperationType] = None
    operation_date: Optional[date] = None

    product_name: Optional[str] = Field(None, max_length=200)
    rate: Optional[float] = Field(None, ge=0)
    rate_unit: Optional[str] = Field(None, max_length=50)
    quantity: Optional[float] = Field(None, ge=0)
    quantity_unit: Optional[str] = Field(None, max_length=50)

    acres_covered: Optional[float] = Field(None, gt=0)

    product_cost: Optional[float] = Field(None, ge=0)
    application_cost: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)

    yield_amount: Optional[float] = Field(None, ge=0)
    yield_unit: Optional[str] = Field(None, max_length=20)
    moisture_percent: Optional[float] = Field(None, ge=0, le=100)

    weather_temp: Optional[float] = None
    weather_wind: Optional[float] = Field(None, ge=0)
    weather_humidity: Optional[float] = Field(None, ge=0, le=100)
    weather_notes: Optional[str] = None

    operator_id: Optional[int] = None
    task_id: Optional[int] = None
    notes: Optional[str] = None


class OperationResponse(BaseModel):
    """Operation response with joined data"""
    id: int
    field_id: int
    field_name: str
    farm_name: Optional[str] = None
    operation_type: OperationType
    operation_date: date

    product_name: Optional[str]
    rate: Optional[float]
    rate_unit: Optional[str]
    quantity: Optional[float]
    quantity_unit: Optional[str]

    acres_covered: Optional[float]

    product_cost: Optional[float]
    application_cost: Optional[float]
    total_cost: Optional[float]

    yield_amount: Optional[float]
    yield_unit: Optional[str]
    moisture_percent: Optional[float]

    weather_temp: Optional[float]
    weather_wind: Optional[float]
    weather_humidity: Optional[float]
    weather_notes: Optional[str]

    operator_id: Optional[int]
    operator_name: Optional[str] = None
    task_id: Optional[int]
    notes: Optional[str]

    created_by_user_id: int
    created_by_user_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OperationsSummary(BaseModel):
    """Summary of operations for a field or all fields"""
    total_operations: int
    operations_by_type: dict
    total_cost: float
    cost_by_type: dict
    date_range: dict  # earliest and latest operation dates


class FieldOperationHistory(BaseModel):
    """Complete operation history for a field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    acreage: float
    operations: List[OperationResponse]
    summary: OperationsSummary


# ============================================================================
# FIELD OPERATIONS SERVICE CLASS
# ============================================================================

class FieldOperationsService:
    """
    Field operations service handling:
    - Operation CRUD
    - Operation history and filtering
    - Summary statistics
    """

    def __init__(self, db_path: str = "agtools.db"):
        """
        Initialize field operations service.

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

        # Create field_operations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                operation_type VARCHAR(50) NOT NULL,
                operation_date DATE NOT NULL,
                product_name VARCHAR(200),
                rate DECIMAL(10, 3),
                rate_unit VARCHAR(50),
                quantity DECIMAL(10, 3),
                quantity_unit VARCHAR(50),
                acres_covered DECIMAL(10, 2),
                product_cost DECIMAL(10, 2),
                application_cost DECIMAL(10, 2),
                total_cost DECIMAL(10, 2),
                yield_amount DECIMAL(10, 2),
                yield_unit VARCHAR(20),
                moisture_percent DECIMAL(5, 2),
                weather_temp DECIMAL(5, 1),
                weather_wind DECIMAL(5, 1),
                weather_humidity DECIMAL(5, 1),
                weather_notes TEXT,
                operator_id INTEGER,
                task_id INTEGER,
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id),
                FOREIGN KEY (operator_id) REFERENCES users(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (created_by_user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_ops_field_id ON field_operations(field_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_ops_type ON field_operations(operation_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_ops_date ON field_operations(operation_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_ops_operator ON field_operations(operator_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_ops_task ON field_operations(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_field_ops_active ON field_operations(is_active)")

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

    def _row_to_response(self, row: sqlite3.Row) -> OperationResponse:
        """Convert a database row to OperationResponse."""
        return OperationResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"],
            farm_name=self._safe_get(row, "farm_name"),
            operation_type=OperationType(row["operation_type"]),
            operation_date=row["operation_date"],
            product_name=row["product_name"],
            rate=float(row["rate"]) if row["rate"] else None,
            rate_unit=row["rate_unit"],
            quantity=float(row["quantity"]) if row["quantity"] else None,
            quantity_unit=row["quantity_unit"],
            acres_covered=float(row["acres_covered"]) if row["acres_covered"] else None,
            product_cost=float(row["product_cost"]) if row["product_cost"] else None,
            application_cost=float(row["application_cost"]) if row["application_cost"] else None,
            total_cost=float(row["total_cost"]) if row["total_cost"] else None,
            yield_amount=float(row["yield_amount"]) if row["yield_amount"] else None,
            yield_unit=row["yield_unit"],
            moisture_percent=float(row["moisture_percent"]) if row["moisture_percent"] else None,
            weather_temp=float(row["weather_temp"]) if row["weather_temp"] else None,
            weather_wind=float(row["weather_wind"]) if row["weather_wind"] else None,
            weather_humidity=float(row["weather_humidity"]) if row["weather_humidity"] else None,
            weather_notes=row["weather_notes"],
            operator_id=row["operator_id"],
            operator_name=self._safe_get(row, "operator_name"),
            task_id=row["task_id"],
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_by_user_name=self._safe_get(row, "created_by_user_name"),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    # ========================================================================
    # CRUD METHODS
    # ========================================================================

    def create_operation(
        self,
        op_data: OperationCreate,
        created_by: int
    ) -> Tuple[Optional[OperationResponse], Optional[str]]:
        """
        Create a new field operation.

        Args:
            op_data: Operation creation data
            created_by: ID of user creating this operation

        Returns:
            Tuple of (OperationResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify field exists
        cursor.execute("SELECT id, acreage FROM fields WHERE id = ? AND is_active = 1", (op_data.field_id,))
        field = cursor.fetchone()
        if not field:
            conn.close()
            return None, "Field not found"

        # Default acres_covered to field acreage if not specified
        acres_covered = op_data.acres_covered or field["acreage"]

        # Calculate total_cost if not provided
        total_cost = op_data.total_cost
        if total_cost is None and (op_data.product_cost or op_data.application_cost):
            total_cost = (op_data.product_cost or 0) + (op_data.application_cost or 0)

        try:
            cursor.execute("""
                INSERT INTO field_operations (
                    field_id, operation_type, operation_date,
                    product_name, rate, rate_unit, quantity, quantity_unit,
                    acres_covered, product_cost, application_cost, total_cost,
                    yield_amount, yield_unit, moisture_percent,
                    weather_temp, weather_wind, weather_humidity, weather_notes,
                    operator_id, task_id, notes, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                op_data.field_id,
                op_data.operation_type.value,
                op_data.operation_date.isoformat(),
                op_data.product_name,
                op_data.rate,
                op_data.rate_unit,
                op_data.quantity,
                op_data.quantity_unit,
                acres_covered,
                op_data.product_cost,
                op_data.application_cost,
                total_cost,
                op_data.yield_amount,
                op_data.yield_unit,
                op_data.moisture_percent,
                op_data.weather_temp,
                op_data.weather_wind,
                op_data.weather_humidity,
                op_data.weather_notes,
                op_data.operator_id,
                op_data.task_id,
                op_data.notes,
                created_by
            ))

            op_id = cursor.lastrowid

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=created_by,
                action="create_operation",
                entity_type="field_operation",
                entity_id=op_id,
                conn=conn
            )

            conn.commit()
            conn.close()

            return self.get_operation_by_id(op_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def get_operation_by_id(self, op_id: int) -> Optional[OperationResponse]:
        """Get operation by ID with joined field/user data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.*,
                f.name as field_name,
                f.farm_name,
                u1.first_name || ' ' || u1.last_name as operator_name,
                u2.first_name || ' ' || u2.last_name as created_by_user_name
            FROM field_operations o
            LEFT JOIN fields f ON o.field_id = f.id
            LEFT JOIN users u1 ON o.operator_id = u1.id
            LEFT JOIN users u2 ON o.created_by_user_id = u2.id
            WHERE o.id = ?
        """, (op_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_response(row)

    def list_operations(
        self,
        field_id: Optional[int] = None,
        operation_type: Optional[OperationType] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        operator_id: Optional[int] = None,
        task_id: Optional[int] = None,
        farm_name: Optional[str] = None,
        is_active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[OperationResponse]:
        """
        List operations with optional filters.

        Args:
            field_id: Filter by field
            operation_type: Filter by operation type
            date_from: Filter operations on or after this date
            date_to: Filter operations on or before this date
            operator_id: Filter by operator
            task_id: Filter by linked task
            farm_name: Filter by farm name
            is_active: Filter by active status
            limit: Max results to return
            offset: Results offset for pagination

        Returns:
            List of OperationResponse
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                o.*,
                f.name as field_name,
                f.farm_name,
                u1.first_name || ' ' || u1.last_name as operator_name,
                u2.first_name || ' ' || u2.last_name as created_by_user_name
            FROM field_operations o
            LEFT JOIN fields f ON o.field_id = f.id
            LEFT JOIN users u1 ON o.operator_id = u1.id
            LEFT JOIN users u2 ON o.created_by_user_id = u2.id
        """

        conditions = []
        params = []

        if field_id:
            conditions.append("o.field_id = ?")
            params.append(field_id)

        if operation_type:
            conditions.append("o.operation_type = ?")
            params.append(operation_type.value)

        if date_from:
            conditions.append("o.operation_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("o.operation_date <= ?")
            params.append(date_to.isoformat())

        if operator_id:
            conditions.append("o.operator_id = ?")
            params.append(operator_id)

        if task_id:
            conditions.append("o.task_id = ?")
            params.append(task_id)

        if farm_name:
            conditions.append("f.farm_name = ?")
            params.append(farm_name)

        if is_active is not None:
            conditions.append("o.is_active = ?")
            params.append(1 if is_active else 0)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY o.operation_date DESC, o.created_at DESC"
        query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_response(row) for row in rows]

    def update_operation(
        self,
        op_id: int,
        op_data: OperationUpdate,
        updated_by: int
    ) -> Tuple[Optional[OperationResponse], Optional[str]]:
        """
        Update an operation.

        Args:
            op_id: Operation ID to update
            op_data: Update data
            updated_by: ID of user performing update

        Returns:
            Tuple of (OperationResponse, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        params = []

        if op_data.operation_type is not None:
            updates.append("operation_type = ?")
            params.append(op_data.operation_type.value)

        if op_data.operation_date is not None:
            updates.append("operation_date = ?")
            params.append(op_data.operation_date.isoformat())

        if op_data.product_name is not None:
            updates.append("product_name = ?")
            params.append(op_data.product_name)

        if op_data.rate is not None:
            updates.append("rate = ?")
            params.append(op_data.rate)

        if op_data.rate_unit is not None:
            updates.append("rate_unit = ?")
            params.append(op_data.rate_unit)

        if op_data.quantity is not None:
            updates.append("quantity = ?")
            params.append(op_data.quantity)

        if op_data.quantity_unit is not None:
            updates.append("quantity_unit = ?")
            params.append(op_data.quantity_unit)

        if op_data.acres_covered is not None:
            updates.append("acres_covered = ?")
            params.append(op_data.acres_covered)

        if op_data.product_cost is not None:
            updates.append("product_cost = ?")
            params.append(op_data.product_cost)

        if op_data.application_cost is not None:
            updates.append("application_cost = ?")
            params.append(op_data.application_cost)

        if op_data.total_cost is not None:
            updates.append("total_cost = ?")
            params.append(op_data.total_cost)

        if op_data.yield_amount is not None:
            updates.append("yield_amount = ?")
            params.append(op_data.yield_amount)

        if op_data.yield_unit is not None:
            updates.append("yield_unit = ?")
            params.append(op_data.yield_unit)

        if op_data.moisture_percent is not None:
            updates.append("moisture_percent = ?")
            params.append(op_data.moisture_percent)

        if op_data.weather_temp is not None:
            updates.append("weather_temp = ?")
            params.append(op_data.weather_temp)

        if op_data.weather_wind is not None:
            updates.append("weather_wind = ?")
            params.append(op_data.weather_wind)

        if op_data.weather_humidity is not None:
            updates.append("weather_humidity = ?")
            params.append(op_data.weather_humidity)

        if op_data.weather_notes is not None:
            updates.append("weather_notes = ?")
            params.append(op_data.weather_notes)

        if op_data.operator_id is not None:
            updates.append("operator_id = ?")
            params.append(op_data.operator_id if op_data.operator_id > 0 else None)

        if op_data.task_id is not None:
            updates.append("task_id = ?")
            params.append(op_data.task_id if op_data.task_id > 0 else None)

        if op_data.notes is not None:
            updates.append("notes = ?")
            params.append(op_data.notes)

        if not updates:
            conn.close()
            return self.get_operation_by_id(op_id), None

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(op_id)

        try:
            cursor.execute(f"""
                UPDATE field_operations SET {', '.join(updates)} WHERE id = ?
            """, params)

            # Log action (thread-safe - pass connection explicitly)
            self.auth_service.log_action(
                user_id=updated_by,
                action="update_operation",
                entity_type="field_operation",
                entity_id=op_id,
                conn=conn
            )

            conn.commit()
            conn.close()

            return self.get_operation_by_id(op_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def delete_operation(
        self,
        op_id: int,
        deleted_by: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Soft delete an operation.

        Args:
            op_id: Operation ID to delete
            deleted_by: ID of user performing deletion

        Returns:
            Tuple of (success, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE field_operations SET is_active = 0, updated_at = ? WHERE id = ?
        """, (datetime.now(timezone.utc).isoformat(), op_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, "Operation not found"

        # Log action (thread-safe - pass connection explicitly)
        self.auth_service.log_action(
            user_id=deleted_by,
            action="delete_operation",
            entity_type="field_operation",
            entity_id=op_id,
            conn=conn
        )

        conn.commit()
        conn.close()

        return True, None

    # ========================================================================
    # STATISTICS METHODS
    # ========================================================================

    def get_operations_summary(
        self,
        field_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        is_active: bool = True
    ) -> OperationsSummary:
        """
        Get summary statistics for operations.

        Args:
            field_id: Filter by field (optional)
            date_from: Start date filter
            date_to: End date filter
            is_active: Only include active operations

        Returns:
            OperationsSummary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause
        conditions = ["is_active = ?"]
        params = [1 if is_active else 0]

        if field_id:
            conditions.append("field_id = ?")
            params.append(field_id)

        if date_from:
            conditions.append("operation_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("operation_date <= ?")
            params.append(date_to.isoformat())

        where_clause = " AND ".join(conditions)

        # Total operations and cost
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_operations,
                COALESCE(SUM(total_cost), 0) as total_cost,
                MIN(operation_date) as earliest_date,
                MAX(operation_date) as latest_date
            FROM field_operations
            WHERE {where_clause}
        """, params)

        row = cursor.fetchone()
        total_operations = row["total_operations"]
        total_cost = float(row["total_cost"])
        earliest_date = row["earliest_date"]
        latest_date = row["latest_date"]

        # Operations by type
        cursor.execute(f"""
            SELECT operation_type, COUNT(*) as count
            FROM field_operations
            WHERE {where_clause}
            GROUP BY operation_type
        """, params)

        operations_by_type = {}
        for row in cursor.fetchall():
            operations_by_type[row["operation_type"]] = row["count"]

        # Cost by type
        cursor.execute(f"""
            SELECT operation_type, COALESCE(SUM(total_cost), 0) as cost
            FROM field_operations
            WHERE {where_clause}
            GROUP BY operation_type
        """, params)

        cost_by_type = {}
        for row in cursor.fetchall():
            cost_by_type[row["operation_type"]] = float(row["cost"])

        conn.close()

        return OperationsSummary(
            total_operations=total_operations,
            operations_by_type=operations_by_type,
            total_cost=total_cost,
            cost_by_type=cost_by_type,
            date_range={
                "earliest": earliest_date,
                "latest": latest_date
            }
        )

    def get_field_operation_history(self, field_id: int) -> Optional[FieldOperationHistory]:
        """
        Get complete operation history for a field.

        Args:
            field_id: Field ID

        Returns:
            FieldOperationHistory or None if field not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get field info
        cursor.execute("""
            SELECT id, name, farm_name, acreage FROM fields WHERE id = ? AND is_active = 1
        """, (field_id,))

        field = cursor.fetchone()
        if not field:
            conn.close()
            return None

        conn.close()

        # Get operations
        operations = self.list_operations(field_id=field_id, limit=1000)

        # Get summary
        summary = self.get_operations_summary(field_id=field_id)

        return FieldOperationHistory(
            field_id=field["id"],
            field_name=field["name"],
            farm_name=field["farm_name"],
            acreage=float(field["acreage"]),
            operations=operations,
            summary=summary
        )


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_field_operations_service: Optional[FieldOperationsService] = None


def get_field_operations_service(db_path: str = "agtools.db") -> FieldOperationsService:
    """Get or create the field operations service singleton."""
    global _field_operations_service

    if _field_operations_service is None:
        _field_operations_service = FieldOperationsService(db_path)

    return _field_operations_service
