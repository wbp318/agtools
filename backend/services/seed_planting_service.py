"""
Seed & Planting Service for Farm Operations Manager
Handles seed inventory, planting records, treatments, and emergence tracking.

AgTools v6.4.0 - Farm Operations Suite
"""

import sqlite3
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel, Field

from .auth_service import get_auth_service


# ============================================================================
# ENUMS
# ============================================================================

class CropType(str, Enum):
    """Crop types for seed inventory"""
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"
    COTTON = "cotton"
    RICE = "rice"
    SORGHUM = "sorghum"
    ALFALFA = "alfalfa"
    HAY = "hay"
    OATS = "oats"
    BARLEY = "barley"
    SUNFLOWER = "sunflower"
    CANOLA = "canola"
    OTHER = "other"


class QuantityUnit(str, Enum):
    """Seed quantity units"""
    BAGS = "bags"
    UNITS = "units"
    LBS = "lbs"
    BUSHELS = "bushels"
    CWT = "cwt"


class TreatmentType(str, Enum):
    """Seed treatment types"""
    FUNGICIDE = "fungicide"
    INSECTICIDE = "insecticide"
    NEMATICIDE = "nematicide"
    INOCULANT = "inoculant"
    BIOLOGICAL = "biological"
    OTHER = "other"


class RateUnit(str, Enum):
    """Planting rate units"""
    SEEDS_PER_ACRE = "seeds/acre"
    LBS_PER_ACRE = "lbs/acre"
    BUSHELS_PER_ACRE = "bushels/acre"
    UNITS_PER_ACRE = "units/acre"
    BAGS_PER_ACRE = "bags/acre"


class SoilMoisture(str, Enum):
    """Soil moisture conditions"""
    DRY = "dry"
    ADEQUATE = "adequate"
    WET = "wet"
    SATURATED = "saturated"


class PlantingStatus(str, Enum):
    """Planting record status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REPLANT_NEEDED = "replant_needed"


class CountUnit(str, Enum):
    """Stand count measurement units"""
    SQ_FT = "sq_ft"
    ROW_FEET = "row_feet"
    THOUSANDTH_ACRE = "1/1000_acre"


class ReplantReason(str, Enum):
    """Reasons for replanting"""
    POOR_STAND = "poor_stand"
    WEATHER_DAMAGE = "weather_damage"
    PEST_DAMAGE = "pest_damage"
    DISEASE = "disease"
    FLOODING = "flooding"
    DROUGHT = "drought"
    HAIL = "hail"
    FROST = "frost"
    OTHER = "other"


# ============================================================================
# PYDANTIC MODELS - SEED INVENTORY
# ============================================================================

class SeedInventoryCreate(BaseModel):
    """Create seed inventory item"""
    variety_name: str = Field(..., min_length=1, max_length=200)
    crop_type: CropType
    brand: Optional[str] = Field(None, max_length=100)
    product_code: Optional[str] = Field(None, max_length=100)
    trait_package: Optional[str] = Field(None, max_length=100)
    relative_maturity: Optional[str] = Field(None, max_length=50)
    seed_size: Optional[float] = Field(None, ge=0)
    germination_rate: Optional[float] = Field(None, ge=0, le=100)
    quantity_units: QuantityUnit = QuantityUnit.BAGS
    quantity_on_hand: float = Field(default=0, ge=0)
    unit_cost: float = Field(default=0, ge=0)
    lot_number: Optional[str] = Field(None, max_length=100)
    purchase_date: Optional[date] = None
    expiration_date: Optional[date] = None
    storage_location: Optional[str] = Field(None, max_length=200)
    supplier: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class SeedInventoryUpdate(BaseModel):
    """Update seed inventory item"""
    variety_name: Optional[str] = Field(None, min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    trait_package: Optional[str] = Field(None, max_length=100)
    germination_rate: Optional[float] = Field(None, ge=0, le=100)
    quantity_on_hand: Optional[float] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    storage_location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class SeedInventoryResponse(BaseModel):
    """Seed inventory response"""
    id: int
    variety_name: str
    crop_type: str
    brand: Optional[str]
    product_code: Optional[str]
    trait_package: Optional[str]
    relative_maturity: Optional[str]
    seed_size: Optional[float]
    germination_rate: Optional[float]
    quantity_units: str
    quantity_on_hand: float
    unit_cost: float
    lot_number: Optional[str]
    purchase_date: Optional[date]
    expiration_date: Optional[date]
    storage_location: Optional[str]
    supplier: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Computed
    total_value: float = 0
    treatments_count: int = 0


# ============================================================================
# PYDANTIC MODELS - SEED TREATMENTS
# ============================================================================

class SeedTreatmentCreate(BaseModel):
    """Create seed treatment"""
    seed_inventory_id: int
    treatment_name: str = Field(..., min_length=1, max_length=200)
    treatment_type: Optional[TreatmentType] = None
    active_ingredient: Optional[str] = Field(None, max_length=200)
    rate: Optional[str] = Field(None, max_length=100)
    rate_unit: Optional[str] = Field(None, max_length=50)
    cost_per_unit: float = Field(default=0, ge=0)
    application_date: Optional[date] = None
    applied_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class SeedTreatmentResponse(BaseModel):
    """Seed treatment response"""
    id: int
    seed_inventory_id: int
    treatment_name: str
    treatment_type: Optional[str]
    active_ingredient: Optional[str]
    rate: Optional[str]
    rate_unit: Optional[str]
    cost_per_unit: float
    application_date: Optional[date]
    applied_by: Optional[str]
    notes: Optional[str]
    created_at: datetime


# ============================================================================
# PYDANTIC MODELS - PLANTING RECORDS
# ============================================================================

class PlantingRecordCreate(BaseModel):
    """Create planting record"""
    field_id: int
    seed_inventory_id: Optional[int] = None
    planting_date: date
    planting_rate: float = Field(..., gt=0)
    rate_unit: RateUnit = RateUnit.SEEDS_PER_ACRE
    row_spacing: Optional[float] = Field(None, gt=0)
    planting_depth: Optional[float] = Field(None, gt=0)
    acres_planted: float = Field(..., gt=0)
    population_target: Optional[int] = Field(None, gt=0)
    equipment_id: Optional[int] = None
    soil_temp: Optional[float] = None
    soil_moisture: Optional[SoilMoisture] = None
    weather_conditions: Optional[str] = Field(None, max_length=200)
    wind_speed: Optional[float] = Field(None, ge=0)
    operator_id: Optional[int] = None
    seed_lot_used: Optional[str] = Field(None, max_length=100)
    units_used: Optional[float] = Field(None, ge=0)
    cost_per_acre: Optional[float] = Field(None, ge=0)
    status: PlantingStatus = PlantingStatus.COMPLETED
    notes: Optional[str] = None


class PlantingRecordUpdate(BaseModel):
    """Update planting record"""
    planting_rate: Optional[float] = Field(None, gt=0)
    acres_planted: Optional[float] = Field(None, gt=0)
    population_target: Optional[int] = Field(None, gt=0)
    status: Optional[PlantingStatus] = None
    notes: Optional[str] = None


class PlantingRecordResponse(BaseModel):
    """Planting record response"""
    id: int
    field_id: int
    field_name: Optional[str] = None
    seed_inventory_id: Optional[int]
    variety_name: Optional[str] = None
    crop_type: Optional[str] = None
    planting_date: date
    planting_rate: float
    rate_unit: str
    row_spacing: Optional[float]
    planting_depth: Optional[float]
    acres_planted: float
    population_target: Optional[int]
    equipment_id: Optional[int]
    equipment_name: Optional[str] = None
    soil_temp: Optional[float]
    soil_moisture: Optional[str]
    weather_conditions: Optional[str]
    wind_speed: Optional[float]
    operator_id: Optional[int]
    seed_lot_used: Optional[str]
    units_used: Optional[float]
    cost_per_acre: Optional[float]
    status: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Computed
    total_cost: float = 0
    emergence_checks: int = 0
    latest_stand_pct: Optional[float] = None


# ============================================================================
# PYDANTIC MODELS - EMERGENCE RECORDS
# ============================================================================

class EmergenceRecordCreate(BaseModel):
    """Create emergence record"""
    planting_record_id: int
    check_date: date
    stand_count: Optional[int] = Field(None, ge=0)
    count_area: Optional[float] = Field(None, gt=0)
    count_unit: CountUnit = CountUnit.ROW_FEET
    plants_per_acre: Optional[int] = Field(None, ge=0)
    stand_percentage: Optional[float] = Field(None, ge=0, le=100)
    uniformity_score: Optional[int] = Field(None, ge=1, le=5)
    vigor_score: Optional[int] = Field(None, ge=1, le=5)
    growth_stage: Optional[str] = Field(None, max_length=20)
    issues_noted: Optional[str] = Field(None, max_length=500)
    photo_path: Optional[str] = None
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_lng: Optional[float] = Field(None, ge=-180, le=180)
    notes: Optional[str] = None


class EmergenceRecordResponse(BaseModel):
    """Emergence record response"""
    id: int
    planting_record_id: int
    check_date: date
    days_after_planting: Optional[int]
    stand_count: Optional[int]
    count_area: Optional[float]
    count_unit: Optional[str]
    plants_per_acre: Optional[int]
    stand_percentage: Optional[float]
    uniformity_score: Optional[int]
    vigor_score: Optional[int]
    growth_stage: Optional[str]
    issues_noted: Optional[str]
    photo_path: Optional[str]
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    notes: Optional[str]
    created_at: datetime
    # Computed
    field_name: Optional[str] = None
    variety_name: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - SUMMARY
# ============================================================================

class SeedPlantingSummary(BaseModel):
    """Summary statistics"""
    total_varieties: int
    total_seed_value: float
    varieties_by_crop: Dict[str, int]
    total_acres_planted: float
    acres_by_crop: Dict[str, float]
    avg_stand_percentage: Optional[float]
    planting_records_count: int
    emergence_checks_count: int


# ============================================================================
# SERVICE CLASS
# ============================================================================

class SeedPlantingService:
    """
    Seed & Planting service handling:
    - Seed inventory management
    - Seed treatments
    - Planting records
    - Emergence tracking
    """

    # Common trait packages by crop
    TRAIT_PACKAGES = {
        "corn": [
            "VT Double PRO", "VT2P", "SmartStax", "SmartStax PRO",
            "Trecepta", "PowerCore", "Viptera", "Agrisure Viptera",
            "Agrisure Duracade", "Genuity VT Triple PRO", "Other"
        ],
        "soybean": [
            "Roundup Ready 2 Xtend", "RR2X", "XtendFlex", "Enlist E3",
            "LibertyLink GT27", "Roundup Ready 2 Yield", "Conventional", "Other"
        ],
        "cotton": [
            "Bollgard 3 XtendFlex", "TwinLink Plus", "WideStrike 3",
            "Enlist Cotton", "PhytoGen", "Other"
        ],
        "wheat": ["Conventional", "Clearfield", "CoAXium", "Other"],
        "default": ["Conventional", "Other"]
    }

    # Common seed brands
    SEED_BRANDS = [
        "Pioneer", "DeKalb", "Asgrow", "Channel", "Golden Harvest",
        "NK", "Brevant", "LG Seeds", "Dyna-Gro", "Stine", "Beck's",
        "Wyffels", "AgriGold", "Croplan", "Lewis Hybrids", "Local Seed Co", "Other"
    ]

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self.auth_service = get_auth_service()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_database(self):
        """Initialize database tables from migration."""
        migration_path = "database/migrations/008_seed_planting.sql"
        try:
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            conn = self._get_connection()
            conn.executescript(migration_sql)
            conn.commit()
            conn.close()
        except FileNotFoundError:
            pass

    # ========================================================================
    # SEED INVENTORY OPERATIONS
    # ========================================================================

    def create_seed(self, data: SeedInventoryCreate, user_id: int) -> Tuple[Optional[SeedInventoryResponse], Optional[str]]:
        """Create a seed inventory item."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO seed_inventory (
                    variety_name, crop_type, brand, product_code, trait_package,
                    relative_maturity, seed_size, germination_rate, quantity_units,
                    quantity_on_hand, unit_cost, lot_number, purchase_date,
                    expiration_date, storage_location, supplier, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.variety_name, data.crop_type.value, data.brand, data.product_code,
                data.trait_package, data.relative_maturity, data.seed_size,
                data.germination_rate, data.quantity_units.value, data.quantity_on_hand,
                data.unit_cost, data.lot_number,
                data.purchase_date.isoformat() if data.purchase_date else None,
                data.expiration_date.isoformat() if data.expiration_date else None,
                data.storage_location, data.supplier, data.notes, user_id
            ))

            seed_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_seed(seed_id)
        except Exception as e:
            return None, str(e)

    def get_seed(self, seed_id: int) -> Tuple[Optional[SeedInventoryResponse], Optional[str]]:
        """Get a seed inventory item by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT s.*,
                    (SELECT COUNT(*) FROM seed_treatments WHERE seed_inventory_id = s.id AND is_active = 1) as treatments_count
                FROM seed_inventory s
                WHERE s.id = ? AND s.is_active = 1
            """, (seed_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Seed not found"

            return self._row_to_seed_response(row), None
        except Exception as e:
            return None, str(e)

    def list_seeds(
        self,
        crop_type: Optional[CropType] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None,
        in_stock_only: bool = False
    ) -> Tuple[List[SeedInventoryResponse], Optional[str]]:
        """List seed inventory items."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT s.*,
                    (SELECT COUNT(*) FROM seed_treatments WHERE seed_inventory_id = s.id AND is_active = 1) as treatments_count
                FROM seed_inventory s
                WHERE s.is_active = 1
            """
            params = []

            if crop_type:
                query += " AND s.crop_type = ?"
                params.append(crop_type.value)

            if brand:
                query += " AND s.brand = ?"
                params.append(brand)

            if search:
                query += " AND (s.variety_name LIKE ? OR s.brand LIKE ? OR s.product_code LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            if in_stock_only:
                query += " AND s.quantity_on_hand > 0"

            query += " ORDER BY s.crop_type, s.variety_name"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            seeds = [self._row_to_seed_response(row) for row in rows]
            return seeds, None
        except Exception as e:
            return [], str(e)

    def update_seed(self, seed_id: int, data: SeedInventoryUpdate) -> Tuple[Optional[SeedInventoryResponse], Optional[str]]:
        """Update a seed inventory item."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if data.variety_name is not None:
                updates.append("variety_name = ?")
                params.append(data.variety_name)
            if data.brand is not None:
                updates.append("brand = ?")
                params.append(data.brand)
            if data.trait_package is not None:
                updates.append("trait_package = ?")
                params.append(data.trait_package)
            if data.germination_rate is not None:
                updates.append("germination_rate = ?")
                params.append(data.germination_rate)
            if data.quantity_on_hand is not None:
                updates.append("quantity_on_hand = ?")
                params.append(data.quantity_on_hand)
            if data.unit_cost is not None:
                updates.append("unit_cost = ?")
                params.append(data.unit_cost)
            if data.storage_location is not None:
                updates.append("storage_location = ?")
                params.append(data.storage_location)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)

            if not updates:
                conn.close()
                return self.get_seed(seed_id)

            params.append(seed_id)
            cursor.execute(f"""
                UPDATE seed_inventory SET {', '.join(updates)}
                WHERE id = ? AND is_active = 1
            """, params)

            conn.commit()
            conn.close()

            return self.get_seed(seed_id)
        except Exception as e:
            return None, str(e)

    def delete_seed(self, seed_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete a seed inventory item."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("UPDATE seed_inventory SET is_active = 0 WHERE id = ?", (seed_id,))
            conn.commit()
            affected = cursor.rowcount
            conn.close()

            return affected > 0, None
        except Exception as e:
            return False, str(e)

    def _row_to_seed_response(self, row: sqlite3.Row) -> SeedInventoryResponse:
        """Convert database row to SeedInventoryResponse."""
        return SeedInventoryResponse(
            id=row["id"],
            variety_name=row["variety_name"],
            crop_type=row["crop_type"],
            brand=row["brand"],
            product_code=row["product_code"],
            trait_package=row["trait_package"],
            relative_maturity=row["relative_maturity"],
            seed_size=row["seed_size"],
            germination_rate=row["germination_rate"],
            quantity_units=row["quantity_units"],
            quantity_on_hand=row["quantity_on_hand"] or 0,
            unit_cost=row["unit_cost"] or 0,
            lot_number=row["lot_number"],
            purchase_date=datetime.fromisoformat(row["purchase_date"]).date() if row["purchase_date"] else None,
            expiration_date=datetime.fromisoformat(row["expiration_date"]).date() if row["expiration_date"] else None,
            storage_location=row["storage_location"],
            supplier=row["supplier"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            total_value=(row["quantity_on_hand"] or 0) * (row["unit_cost"] or 0),
            treatments_count=row["treatments_count"] if "treatments_count" in row.keys() else 0
        )

    # ========================================================================
    # SEED TREATMENT OPERATIONS
    # ========================================================================

    def create_treatment(self, data: SeedTreatmentCreate, user_id: int) -> Tuple[Optional[SeedTreatmentResponse], Optional[str]]:
        """Create a seed treatment record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO seed_treatments (
                    seed_inventory_id, treatment_name, treatment_type, active_ingredient,
                    rate, rate_unit, cost_per_unit, application_date, applied_by,
                    notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.seed_inventory_id, data.treatment_name,
                data.treatment_type.value if data.treatment_type else None,
                data.active_ingredient, data.rate, data.rate_unit, data.cost_per_unit,
                data.application_date.isoformat() if data.application_date else None,
                data.applied_by, data.notes, user_id
            ))

            treatment_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_treatment(treatment_id)
        except Exception as e:
            return None, str(e)

    def get_treatment(self, treatment_id: int) -> Tuple[Optional[SeedTreatmentResponse], Optional[str]]:
        """Get a seed treatment by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM seed_treatments WHERE id = ? AND is_active = 1", (treatment_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Treatment not found"

            return self._row_to_treatment_response(row), None
        except Exception as e:
            return None, str(e)

    def list_treatments(self, seed_inventory_id: int) -> Tuple[List[SeedTreatmentResponse], Optional[str]]:
        """List treatments for a seed inventory item."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM seed_treatments
                WHERE seed_inventory_id = ? AND is_active = 1
                ORDER BY application_date DESC
            """, (seed_inventory_id,))

            rows = cursor.fetchall()
            conn.close()

            treatments = [self._row_to_treatment_response(row) for row in rows]
            return treatments, None
        except Exception as e:
            return [], str(e)

    def _row_to_treatment_response(self, row: sqlite3.Row) -> SeedTreatmentResponse:
        """Convert database row to SeedTreatmentResponse."""
        return SeedTreatmentResponse(
            id=row["id"],
            seed_inventory_id=row["seed_inventory_id"],
            treatment_name=row["treatment_name"],
            treatment_type=row["treatment_type"],
            active_ingredient=row["active_ingredient"],
            rate=row["rate"],
            rate_unit=row["rate_unit"],
            cost_per_unit=row["cost_per_unit"] or 0,
            application_date=datetime.fromisoformat(row["application_date"]).date() if row["application_date"] else None,
            applied_by=row["applied_by"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"])
        )

    # ========================================================================
    # PLANTING RECORD OPERATIONS
    # ========================================================================

    def create_planting(self, data: PlantingRecordCreate, user_id: int) -> Tuple[Optional[PlantingRecordResponse], Optional[str]]:
        """Create a planting record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO planting_records (
                    field_id, seed_inventory_id, planting_date, planting_rate, rate_unit,
                    row_spacing, planting_depth, acres_planted, population_target,
                    equipment_id, soil_temp, soil_moisture, weather_conditions,
                    wind_speed, operator_id, seed_lot_used, units_used, cost_per_acre,
                    status, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.seed_inventory_id, data.planting_date.isoformat(),
                data.planting_rate, data.rate_unit.value, data.row_spacing, data.planting_depth,
                data.acres_planted, data.population_target, data.equipment_id,
                data.soil_temp, data.soil_moisture.value if data.soil_moisture else None,
                data.weather_conditions, data.wind_speed, data.operator_id,
                data.seed_lot_used, data.units_used, data.cost_per_acre,
                data.status.value, data.notes, user_id
            ))

            planting_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_planting(planting_id)
        except Exception as e:
            return None, str(e)

    def get_planting(self, planting_id: int) -> Tuple[Optional[PlantingRecordResponse], Optional[str]]:
        """Get a planting record by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT p.*,
                    f.name as field_name,
                    s.variety_name, s.crop_type,
                    e.name as equipment_name,
                    (SELECT COUNT(*) FROM emergence_records WHERE planting_record_id = p.id AND is_active = 1) as emergence_checks,
                    (SELECT stand_percentage FROM emergence_records WHERE planting_record_id = p.id AND is_active = 1 ORDER BY check_date DESC LIMIT 1) as latest_stand_pct
                FROM planting_records p
                LEFT JOIN fields f ON p.field_id = f.id
                LEFT JOIN seed_inventory s ON p.seed_inventory_id = s.id
                LEFT JOIN equipment e ON p.equipment_id = e.id
                WHERE p.id = ? AND p.is_active = 1
            """, (planting_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Planting record not found"

            return self._row_to_planting_response(row), None
        except Exception as e:
            return None, str(e)

    def list_plantings(
        self,
        field_id: Optional[int] = None,
        crop_type: Optional[CropType] = None,
        status: Optional[PlantingStatus] = None,
        year: Optional[int] = None
    ) -> Tuple[List[PlantingRecordResponse], Optional[str]]:
        """List planting records."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT p.*,
                    f.name as field_name,
                    s.variety_name, s.crop_type,
                    e.name as equipment_name,
                    (SELECT COUNT(*) FROM emergence_records WHERE planting_record_id = p.id AND is_active = 1) as emergence_checks,
                    (SELECT stand_percentage FROM emergence_records WHERE planting_record_id = p.id AND is_active = 1 ORDER BY check_date DESC LIMIT 1) as latest_stand_pct
                FROM planting_records p
                LEFT JOIN fields f ON p.field_id = f.id
                LEFT JOIN seed_inventory s ON p.seed_inventory_id = s.id
                LEFT JOIN equipment e ON p.equipment_id = e.id
                WHERE p.is_active = 1
            """
            params = []

            if field_id:
                query += " AND p.field_id = ?"
                params.append(field_id)

            if crop_type:
                query += " AND s.crop_type = ?"
                params.append(crop_type.value)

            if status:
                query += " AND p.status = ?"
                params.append(status.value)

            if year:
                query += " AND strftime('%Y', p.planting_date) = ?"
                params.append(str(year))

            query += " ORDER BY p.planting_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            plantings = [self._row_to_planting_response(row) for row in rows]
            return plantings, None
        except Exception as e:
            return [], str(e)

    def update_planting(self, planting_id: int, data: PlantingRecordUpdate) -> Tuple[Optional[PlantingRecordResponse], Optional[str]]:
        """Update a planting record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if data.planting_rate is not None:
                updates.append("planting_rate = ?")
                params.append(data.planting_rate)
            if data.acres_planted is not None:
                updates.append("acres_planted = ?")
                params.append(data.acres_planted)
            if data.population_target is not None:
                updates.append("population_target = ?")
                params.append(data.population_target)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status.value)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)

            if not updates:
                conn.close()
                return self.get_planting(planting_id)

            params.append(planting_id)
            cursor.execute(f"""
                UPDATE planting_records SET {', '.join(updates)}
                WHERE id = ? AND is_active = 1
            """, params)

            conn.commit()
            conn.close()

            return self.get_planting(planting_id)
        except Exception as e:
            return None, str(e)

    def _row_to_planting_response(self, row: sqlite3.Row) -> PlantingRecordResponse:
        """Convert database row to PlantingRecordResponse."""
        cost_per_acre = row["cost_per_acre"] or 0
        acres = row["acres_planted"] or 0

        return PlantingRecordResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            seed_inventory_id=row["seed_inventory_id"],
            variety_name=row["variety_name"] if "variety_name" in row.keys() else None,
            crop_type=row["crop_type"] if "crop_type" in row.keys() else None,
            planting_date=datetime.fromisoformat(row["planting_date"]).date(),
            planting_rate=row["planting_rate"],
            rate_unit=row["rate_unit"],
            row_spacing=row["row_spacing"],
            planting_depth=row["planting_depth"],
            acres_planted=row["acres_planted"],
            population_target=row["population_target"],
            equipment_id=row["equipment_id"],
            equipment_name=row["equipment_name"] if "equipment_name" in row.keys() else None,
            soil_temp=row["soil_temp"],
            soil_moisture=row["soil_moisture"],
            weather_conditions=row["weather_conditions"],
            wind_speed=row["wind_speed"],
            operator_id=row["operator_id"],
            seed_lot_used=row["seed_lot_used"],
            units_used=row["units_used"],
            cost_per_acre=cost_per_acre,
            status=row["status"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            total_cost=cost_per_acre * acres,
            emergence_checks=row["emergence_checks"] if "emergence_checks" in row.keys() else 0,
            latest_stand_pct=row["latest_stand_pct"] if "latest_stand_pct" in row.keys() else None
        )

    # ========================================================================
    # EMERGENCE RECORD OPERATIONS
    # ========================================================================

    def create_emergence(self, data: EmergenceRecordCreate, user_id: int) -> Tuple[Optional[EmergenceRecordResponse], Optional[str]]:
        """Create an emergence record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get planting date to calculate days after planting
            cursor.execute("SELECT planting_date FROM planting_records WHERE id = ?", (data.planting_record_id,))
            planting_row = cursor.fetchone()
            if not planting_row:
                conn.close()
                return None, "Planting record not found"

            planting_date = datetime.fromisoformat(planting_row["planting_date"]).date()
            days_after = (data.check_date - planting_date).days

            cursor.execute("""
                INSERT INTO emergence_records (
                    planting_record_id, check_date, days_after_planting, stand_count,
                    count_area, count_unit, plants_per_acre, stand_percentage,
                    uniformity_score, vigor_score, growth_stage, issues_noted,
                    photo_path, gps_lat, gps_lng, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.planting_record_id, data.check_date.isoformat(), days_after,
                data.stand_count, data.count_area, data.count_unit.value,
                data.plants_per_acre, data.stand_percentage, data.uniformity_score,
                data.vigor_score, data.growth_stage, data.issues_noted, data.photo_path,
                data.gps_lat, data.gps_lng, data.notes, user_id
            ))

            emergence_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_emergence(emergence_id)
        except Exception as e:
            return None, str(e)

    def get_emergence(self, emergence_id: int) -> Tuple[Optional[EmergenceRecordResponse], Optional[str]]:
        """Get an emergence record by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT e.*, f.name as field_name, s.variety_name
                FROM emergence_records e
                JOIN planting_records p ON e.planting_record_id = p.id
                LEFT JOIN fields f ON p.field_id = f.id
                LEFT JOIN seed_inventory s ON p.seed_inventory_id = s.id
                WHERE e.id = ? AND e.is_active = 1
            """, (emergence_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Emergence record not found"

            return self._row_to_emergence_response(row), None
        except Exception as e:
            return None, str(e)

    def list_emergence(self, planting_record_id: int) -> Tuple[List[EmergenceRecordResponse], Optional[str]]:
        """List emergence records for a planting."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT e.*, f.name as field_name, s.variety_name
                FROM emergence_records e
                JOIN planting_records p ON e.planting_record_id = p.id
                LEFT JOIN fields f ON p.field_id = f.id
                LEFT JOIN seed_inventory s ON p.seed_inventory_id = s.id
                WHERE e.planting_record_id = ? AND e.is_active = 1
                ORDER BY e.check_date DESC
            """, (planting_record_id,))

            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_emergence_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def _row_to_emergence_response(self, row: sqlite3.Row) -> EmergenceRecordResponse:
        """Convert database row to EmergenceRecordResponse."""
        return EmergenceRecordResponse(
            id=row["id"],
            planting_record_id=row["planting_record_id"],
            check_date=datetime.fromisoformat(row["check_date"]).date(),
            days_after_planting=row["days_after_planting"],
            stand_count=row["stand_count"],
            count_area=row["count_area"],
            count_unit=row["count_unit"],
            plants_per_acre=row["plants_per_acre"],
            stand_percentage=row["stand_percentage"],
            uniformity_score=row["uniformity_score"],
            vigor_score=row["vigor_score"],
            growth_stage=row["growth_stage"],
            issues_noted=row["issues_noted"],
            photo_path=row["photo_path"],
            gps_lat=row["gps_lat"],
            gps_lng=row["gps_lng"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            variety_name=row["variety_name"] if "variety_name" in row.keys() else None
        )

    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================

    def get_summary(self, year: Optional[int] = None) -> Tuple[Optional[SeedPlantingSummary], Optional[str]]:
        """Get seed & planting summary statistics."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Use current year if not specified
            if not year:
                year = date.today().year

            # Total varieties
            cursor.execute("SELECT COUNT(*) as count FROM seed_inventory WHERE is_active = 1")
            total_varieties = cursor.fetchone()["count"]

            # Total seed value
            cursor.execute("""
                SELECT COALESCE(SUM(quantity_on_hand * unit_cost), 0) as value
                FROM seed_inventory WHERE is_active = 1
            """)
            total_value = cursor.fetchone()["value"]

            # Varieties by crop
            cursor.execute("""
                SELECT crop_type, COUNT(*) as count
                FROM seed_inventory WHERE is_active = 1
                GROUP BY crop_type
            """)
            varieties_by_crop = {row["crop_type"]: row["count"] for row in cursor.fetchall()}

            # Total acres planted this year
            cursor.execute("""
                SELECT COALESCE(SUM(acres_planted), 0) as acres
                FROM planting_records
                WHERE is_active = 1 AND strftime('%Y', planting_date) = ?
            """, (str(year),))
            total_acres = cursor.fetchone()["acres"]

            # Acres by crop
            cursor.execute("""
                SELECT s.crop_type, COALESCE(SUM(p.acres_planted), 0) as acres
                FROM planting_records p
                JOIN seed_inventory s ON p.seed_inventory_id = s.id
                WHERE p.is_active = 1 AND strftime('%Y', p.planting_date) = ?
                GROUP BY s.crop_type
            """, (str(year),))
            acres_by_crop = {row["crop_type"]: row["acres"] for row in cursor.fetchall()}

            # Average stand percentage
            cursor.execute("""
                SELECT AVG(e.stand_percentage) as avg_stand
                FROM emergence_records e
                JOIN planting_records p ON e.planting_record_id = p.id
                WHERE e.is_active = 1 AND e.stand_percentage IS NOT NULL
                AND strftime('%Y', p.planting_date) = ?
            """, (str(year),))
            avg_stand_row = cursor.fetchone()
            avg_stand = round(avg_stand_row["avg_stand"], 1) if avg_stand_row["avg_stand"] else None

            # Planting records count
            cursor.execute("""
                SELECT COUNT(*) as count FROM planting_records
                WHERE is_active = 1 AND strftime('%Y', planting_date) = ?
            """, (str(year),))
            plantings_count = cursor.fetchone()["count"]

            # Emergence checks count
            cursor.execute("""
                SELECT COUNT(*) as count FROM emergence_records e
                JOIN planting_records p ON e.planting_record_id = p.id
                WHERE e.is_active = 1 AND strftime('%Y', p.planting_date) = ?
            """, (str(year),))
            emergence_count = cursor.fetchone()["count"]

            conn.close()

            return SeedPlantingSummary(
                total_varieties=total_varieties,
                total_seed_value=total_value,
                varieties_by_crop=varieties_by_crop,
                total_acres_planted=total_acres,
                acres_by_crop=acres_by_crop,
                avg_stand_percentage=avg_stand,
                planting_records_count=plantings_count,
                emergence_checks_count=emergence_count
            ), None
        except Exception as e:
            return None, str(e)

    def get_traits_for_crop(self, crop_type: CropType) -> List[str]:
        """Get trait packages for a crop type."""
        return self.TRAIT_PACKAGES.get(crop_type.value, self.TRAIT_PACKAGES["default"])


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_seed_planting_service: Optional[SeedPlantingService] = None


def get_seed_planting_service(db_path: str = "agtools.db") -> SeedPlantingService:
    """Get or create singleton seed planting service instance."""
    global _seed_planting_service
    if _seed_planting_service is None:
        _seed_planting_service = SeedPlantingService(db_path)
    return _seed_planting_service
