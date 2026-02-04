"""
Sustainability Metrics Service for AgTools

Tracks environmental impact and sustainability metrics for agricultural operations.
Supports climate-smart agriculture initiatives and research documentation.

Features:
- Carbon footprint tracking (per field, per operation, per acre)
- Input reduction monitoring (pesticides, fertilizers, fuel)
- Water usage tracking and efficiency metrics
- Sustainability scorecards with year-over-year comparisons
- Research-ready data export
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import sqlite3
import os
import math


def _safe_float(value: float, default: float = 0.0) -> float:
    """Convert infinity/nan to a safe default value for JSON serialization"""
    if math.isinf(value) or math.isnan(value):
        return default
    return value


# =============================================================================
# ENUMS
# =============================================================================

class InputCategory(str, Enum):
    """Categories of agricultural inputs tracked for sustainability"""
    PESTICIDE = "pesticide"
    HERBICIDE = "herbicide"
    FUNGICIDE = "fungicide"
    INSECTICIDE = "insecticide"
    FERTILIZER_N = "fertilizer_nitrogen"
    FERTILIZER_P = "fertilizer_phosphorus"
    FERTILIZER_K = "fertilizer_potassium"
    FUEL_DIESEL = "fuel_diesel"
    FUEL_GAS = "fuel_gasoline"
    FUEL_PROPANE = "fuel_propane"
    WATER_IRRIGATION = "water_irrigation"
    SEED = "seed"
    LIME = "lime"
    OTHER = "other"


class CarbonSource(str, Enum):
    """Sources of carbon emissions/sequestration"""
    FUEL_COMBUSTION = "fuel_combustion"
    FERTILIZER_PRODUCTION = "fertilizer_production"
    FERTILIZER_APPLICATION = "fertilizer_application"  # N2O emissions
    PESTICIDE_PRODUCTION = "pesticide_production"
    MACHINERY_MANUFACTURING = "machinery_manufacturing"
    SOIL_SEQUESTRATION = "soil_sequestration"  # Negative = carbon capture
    COVER_CROP = "cover_crop"  # Negative = carbon capture
    TILLAGE = "tillage"  # Releases soil carbon
    NO_TILL = "no_till"  # Preserves soil carbon


class SustainabilityPractice(str, Enum):
    """Sustainable agriculture practices that can be tracked"""
    COVER_CROPS = "cover_crops"
    NO_TILL = "no_till"
    REDUCED_TILL = "reduced_till"
    CROP_ROTATION = "crop_rotation"
    INTEGRATED_PEST_MANAGEMENT = "ipm"
    PRECISION_APPLICATION = "precision_application"
    VARIABLE_RATE = "variable_rate"
    BUFFER_STRIPS = "buffer_strips"
    WATERWAY_PROTECTION = "waterway_protection"
    POLLINATOR_HABITAT = "pollinator_habitat"
    ORGANIC_PRACTICES = "organic_practices"
    SOIL_TESTING = "soil_testing"
    NUTRIENT_MANAGEMENT_PLAN = "nutrient_management_plan"
    IRRIGATION_EFFICIENCY = "irrigation_efficiency"


class MetricPeriod(str, Enum):
    """Time periods for aggregating metrics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"
    ANNUAL = "annual"


# =============================================================================
# CARBON EMISSION FACTORS (kg CO2e per unit)
# Sources: EPA, IPCC, USDA
# =============================================================================

CARBON_FACTORS = {
    # Fuel emissions (kg CO2e per gallon)
    "fuel_diesel": 10.21,
    "fuel_gasoline": 8.89,
    "fuel_propane": 5.79,

    # Fertilizer production emissions (kg CO2e per lb of nutrient)
    "fertilizer_nitrogen": 2.63,  # Includes N2O from application
    "fertilizer_phosphorus": 0.45,
    "fertilizer_potassium": 0.32,

    # Pesticide production (kg CO2e per lb active ingredient)
    "pesticide": 4.5,
    "herbicide": 6.3,
    "fungicide": 3.8,
    "insecticide": 5.1,

    # Carbon sequestration (negative = capture, kg CO2e per acre per year)
    "cover_crop": -0.5 * 1000,  # 0.5 metric tons per acre
    "no_till": -0.3 * 1000,  # 0.3 metric tons per acre
    "reduced_till": -0.15 * 1000,

    # Tillage releases (kg CO2e per acre per pass)
    "conventional_till": 50,
    "chisel_plow": 30,
    "disk": 20,
}


# =============================================================================
# PYDANTIC MODELS - Input Usage
# =============================================================================

class InputUsageCreate(BaseModel):
    """Record input usage for sustainability tracking"""
    field_id: int
    category: InputCategory
    product_name: Optional[str] = None
    quantity: float = Field(..., ge=0, description="Amount used")
    unit: str = Field(..., description="Unit of measurement (gal, lb, oz, etc.)")
    application_date: date
    acres_applied: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

    # Optional detailed tracking
    active_ingredient_lbs: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)


class InputUsageResponse(BaseModel):
    """Response model for input usage records"""
    id: int
    field_id: int
    field_name: Optional[str] = None
    category: InputCategory
    product_name: Optional[str]
    quantity: float
    unit: str
    application_date: date
    acres_applied: Optional[float]
    rate_per_acre: Optional[float]
    notes: Optional[str]
    active_ingredient_lbs: Optional[float]
    cost: Optional[float]
    cost_per_acre: Optional[float]
    carbon_footprint_kg: Optional[float]
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# PYDANTIC MODELS - Carbon Tracking
# =============================================================================

class CarbonEntryCreate(BaseModel):
    """Record a carbon emission or sequestration event"""
    field_id: Optional[int] = None
    source: CarbonSource
    carbon_kg: float = Field(..., description="kg CO2e (negative for sequestration)")
    activity_date: date
    description: Optional[str] = None
    calculation_method: Optional[str] = Field(None, description="How value was calculated")
    data_source: Optional[str] = Field(None, description="Source of emission factor")


class CarbonEntryResponse(BaseModel):
    """Response model for carbon entries"""
    id: int
    field_id: Optional[int]
    field_name: Optional[str]
    source: CarbonSource
    carbon_kg: float
    carbon_per_acre: Optional[float]
    activity_date: date
    description: Optional[str]
    calculation_method: Optional[str]
    data_source: Optional[str]
    created_by_user_id: int
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Water Tracking
# =============================================================================

class WaterUsageCreate(BaseModel):
    """Record water usage for irrigation tracking"""
    field_id: int
    usage_date: date
    gallons: float = Field(..., ge=0)
    irrigation_method: Optional[str] = Field(None, description="pivot, drip, flood, etc.")
    source: Optional[str] = Field(None, description="well, river, municipal, etc.")
    acres_irrigated: Optional[float] = Field(None, ge=0)
    hours_run: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class WaterUsageResponse(BaseModel):
    """Response model for water usage records"""
    id: int
    field_id: int
    field_name: Optional[str]
    usage_date: date
    gallons: float
    gallons_per_acre: Optional[float]
    irrigation_method: Optional[str]
    source: Optional[str]
    acres_irrigated: Optional[float]
    hours_run: Optional[float]
    notes: Optional[str]
    created_by_user_id: int
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Sustainability Practices
# =============================================================================

class PracticeRecordCreate(BaseModel):
    """Record adoption of a sustainability practice"""
    field_id: int
    practice: SustainabilityPractice
    year: int
    acres_implemented: float = Field(..., ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    details: Optional[str] = None
    verified: bool = False
    verification_source: Optional[str] = None


class PracticeRecordResponse(BaseModel):
    """Response model for practice records"""
    id: int
    field_id: int
    field_name: Optional[str]
    practice: SustainabilityPractice
    practice_display: str
    year: int
    acres_implemented: float
    start_date: Optional[date]
    end_date: Optional[date]
    details: Optional[str]
    verified: bool
    verification_source: Optional[str]
    carbon_benefit_kg: Optional[float]
    created_by_user_id: int
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Sustainability Scorecard
# =============================================================================

class SustainabilityScore(BaseModel):
    """Individual metric score"""
    metric: str
    score: float = Field(..., ge=0, le=100)
    weight: float = Field(..., ge=0, le=1)
    weighted_score: float
    trend: str = Field(..., description="improving, stable, declining")
    details: Optional[str] = None


class SustainabilityScorecard(BaseModel):
    """Complete sustainability scorecard for a farm or field"""
    entity_type: str  # "farm" or "field"
    entity_id: Optional[int]
    entity_name: str
    year: int
    overall_score: float = Field(..., ge=0, le=100)
    grade: str  # A, B, C, D, F

    # Individual scores
    carbon_score: SustainabilityScore
    input_efficiency_score: SustainabilityScore
    water_efficiency_score: SustainabilityScore
    practice_adoption_score: SustainabilityScore
    biodiversity_score: SustainabilityScore

    # Summary metrics
    total_carbon_footprint_kg: float
    carbon_per_acre: float
    carbon_sequestered_kg: float
    net_carbon_kg: float

    total_acres: float
    practices_adopted: List[str]
    improvement_opportunities: List[str]

    # Year-over-year comparison
    previous_year_score: Optional[float]
    score_change: Optional[float]
    score_change_percent: Optional[float]

    generated_at: datetime


# =============================================================================
# PYDANTIC MODELS - Reports and Analytics
# =============================================================================

class InputSummary(BaseModel):
    """Summary of input usage for a period"""
    category: InputCategory
    total_quantity: float
    unit: str
    total_cost: Optional[float]
    total_acres: float
    rate_per_acre: float
    carbon_footprint_kg: float
    year_over_year_change: Optional[float]


class CarbonSummary(BaseModel):
    """Carbon footprint summary"""
    period: str
    total_emissions_kg: float
    total_sequestration_kg: float
    net_carbon_kg: float
    emissions_per_acre: float
    sequestration_per_acre: float
    net_per_acre: float
    by_source: Dict[str, float]
    trend: str


class WaterSummary(BaseModel):
    """Water usage summary"""
    period: str
    total_gallons: float
    total_acres: float
    gallons_per_acre: float
    by_method: Dict[str, float]
    by_source: Dict[str, float]
    efficiency_score: float
    trend: str


class SustainabilityReport(BaseModel):
    """Comprehensive sustainability report for research and documentation"""
    report_title: str
    generated_at: datetime
    period_start: date
    period_end: date

    # Farm overview
    farm_name: str
    total_acres: float
    total_fields: int
    crops_grown: List[str]

    # Sustainability scorecard
    scorecard: SustainabilityScorecard

    # Detailed metrics
    input_summary: List[InputSummary]
    carbon_summary: CarbonSummary
    water_summary: Optional[WaterSummary]

    # Practice adoption
    practices_summary: Dict[str, Any]

    # Trends (multi-year if available)
    historical_scores: List[Dict[str, Any]]

    # Recommendations
    improvement_recommendations: List[str]

    # Grant-ready metrics
    grant_metrics: Dict[str, Any]


# =============================================================================
# SUSTAINABILITY SERVICE CLASS
# =============================================================================

class SustainabilityService:
    """
    Service for tracking and analyzing agricultural sustainability metrics.

    Provides comprehensive environmental impact documentation:
    - Comprehensive input tracking (chemicals, fertilizers, fuel)
    - Carbon footprint calculation and tracking
    - Water usage monitoring
    - Sustainability practice documentation
    - Research-ready data export
    - Year-over-year trend analysis
    """

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize sustainability tracking tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Input usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sustainability_inputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                category VARCHAR(50) NOT NULL,
                product_name VARCHAR(200),
                quantity REAL NOT NULL,
                unit VARCHAR(50) NOT NULL,
                application_date DATE NOT NULL,
                acres_applied REAL,
                active_ingredient_lbs REAL,
                cost REAL,
                notes TEXT,
                carbon_footprint_kg REAL,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Carbon tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sustainability_carbon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER,
                source VARCHAR(50) NOT NULL,
                carbon_kg REAL NOT NULL,
                activity_date DATE NOT NULL,
                description TEXT,
                calculation_method TEXT,
                data_source TEXT,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Water usage tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sustainability_water (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                usage_date DATE NOT NULL,
                gallons REAL NOT NULL,
                irrigation_method VARCHAR(100),
                source VARCHAR(100),
                acres_irrigated REAL,
                hours_run REAL,
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Sustainability practices adopted
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sustainability_practices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                practice VARCHAR(50) NOT NULL,
                year INTEGER NOT NULL,
                acres_implemented REAL NOT NULL,
                start_date DATE,
                end_date DATE,
                details TEXT,
                verified BOOLEAN DEFAULT 0,
                verification_source TEXT,
                carbon_benefit_kg REAL,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Annual sustainability scores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sustainability_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(20) NOT NULL,
                entity_id INTEGER,
                year INTEGER NOT NULL,
                overall_score REAL NOT NULL,
                carbon_score REAL,
                input_score REAL,
                water_score REAL,
                practice_score REAL,
                biodiversity_score REAL,
                scorecard_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, entity_id, year)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inputs_field ON sustainability_inputs(field_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inputs_date ON sustainability_inputs(application_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inputs_category ON sustainability_inputs(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_carbon_field ON sustainability_carbon(field_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_carbon_date ON sustainability_carbon(activity_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_field ON sustainability_water(field_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_date ON sustainability_water(usage_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_practices_field ON sustainability_practices(field_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_practices_year ON sustainability_practices(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_year ON sustainability_scores(year)")

        conn.commit()
        conn.close()

    # =========================================================================
    # INPUT USAGE TRACKING
    # =========================================================================

    def record_input_usage(self, data: InputUsageCreate, user_id: int) -> Tuple[Optional[InputUsageResponse], Optional[str]]:
        """Record an input usage event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Calculate carbon footprint based on category
            carbon_kg = self._calculate_input_carbon(data)

            cursor.execute("""
                INSERT INTO sustainability_inputs
                (field_id, category, product_name, quantity, unit, application_date,
                 acres_applied, active_ingredient_lbs, cost, notes, carbon_footprint_kg,
                 created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.category.value, data.product_name,
                data.quantity, data.unit, data.application_date.isoformat(),
                data.acres_applied, data.active_ingredient_lbs, data.cost,
                data.notes, carbon_kg, user_id
            ))

            input_id = cursor.lastrowid

            # Auto-create carbon entry for significant inputs
            if carbon_kg and carbon_kg > 0:
                source = self._map_input_to_carbon_source(data.category)
                cursor.execute("""
                    INSERT INTO sustainability_carbon
                    (field_id, source, carbon_kg, activity_date, description,
                     calculation_method, data_source, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.field_id, source.value, carbon_kg,
                    data.application_date.isoformat(),
                    f"{data.category.value}: {data.quantity} {data.unit} of {data.product_name or 'product'}",
                    "EPA emission factors",
                    "AgTools automatic calculation",
                    user_id
                ))

            conn.commit()

            # Fetch the created record
            result = self.get_input_usage(input_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def _calculate_input_carbon(self, data: InputUsageCreate) -> float:
        """Calculate carbon footprint for an input usage"""
        category = data.category.value

        # Use active ingredient if available, otherwise estimate
        if data.active_ingredient_lbs:
            quantity_lbs = data.active_ingredient_lbs
        else:
            # Convert common units to lbs for estimation
            quantity_lbs = self._convert_to_lbs(data.quantity, data.unit, category)

        # Get emission factor
        factor = CARBON_FACTORS.get(category, 0)

        # For fuel, use gallons directly
        if category.startswith("fuel_"):
            return data.quantity * factor

        return quantity_lbs * factor

    def _convert_to_lbs(self, quantity: float, unit: str, category: str) -> float:
        """Convert quantity to pounds for carbon calculation"""
        unit_lower = unit.lower()

        conversions = {
            "lb": 1.0, "lbs": 1.0, "pound": 1.0, "pounds": 1.0,
            "oz": 0.0625, "ounce": 0.0625, "ounces": 0.0625,
            "kg": 2.205, "kilogram": 2.205,
            "g": 0.0022, "gram": 0.0022, "grams": 0.0022,
            "ton": 2000, "tons": 2000,
            "gal": 8.34, "gallon": 8.34, "gallons": 8.34,  # Water weight
            "qt": 2.085, "quart": 2.085,
            "pt": 1.04, "pint": 1.04,
        }

        return quantity * conversions.get(unit_lower, 1.0)

    def _map_input_to_carbon_source(self, category: InputCategory) -> CarbonSource:
        """Map input category to carbon source"""
        mapping = {
            InputCategory.PESTICIDE: CarbonSource.PESTICIDE_PRODUCTION,
            InputCategory.HERBICIDE: CarbonSource.PESTICIDE_PRODUCTION,
            InputCategory.FUNGICIDE: CarbonSource.PESTICIDE_PRODUCTION,
            InputCategory.INSECTICIDE: CarbonSource.PESTICIDE_PRODUCTION,
            InputCategory.FERTILIZER_N: CarbonSource.FERTILIZER_APPLICATION,
            InputCategory.FERTILIZER_P: CarbonSource.FERTILIZER_PRODUCTION,
            InputCategory.FERTILIZER_K: CarbonSource.FERTILIZER_PRODUCTION,
            InputCategory.FUEL_DIESEL: CarbonSource.FUEL_COMBUSTION,
            InputCategory.FUEL_GAS: CarbonSource.FUEL_COMBUSTION,
            InputCategory.FUEL_PROPANE: CarbonSource.FUEL_COMBUSTION,
        }
        return mapping.get(category, CarbonSource.FUEL_COMBUSTION)

    def get_input_usage(self, input_id: int) -> Optional[InputUsageResponse]:
        """Get a single input usage record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT i.*, f.name as field_name
            FROM sustainability_inputs i
            LEFT JOIN fields f ON i.field_id = f.id
            WHERE i.id = ?
        """, (input_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_input_response(row)

    def _row_to_input_response(self, row: sqlite3.Row) -> InputUsageResponse:
        """Convert database row to InputUsageResponse"""
        acres = row["acres_applied"]
        quantity = row["quantity"]
        cost = row["cost"]

        rate_per_acre = quantity / acres if acres and acres > 0 else None
        cost_per_acre = cost / acres if cost and acres and acres > 0 else None

        return InputUsageResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            category=InputCategory(row["category"]),
            product_name=row["product_name"],
            quantity=row["quantity"],
            unit=row["unit"],
            application_date=date.fromisoformat(row["application_date"]),
            acres_applied=row["acres_applied"],
            rate_per_acre=rate_per_acre,
            notes=row["notes"],
            active_ingredient_lbs=row["active_ingredient_lbs"],
            cost=row["cost"],
            cost_per_acre=cost_per_acre,
            carbon_footprint_kg=row["carbon_footprint_kg"],
            created_by_user_id=row["created_by_user_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(timezone.utc)
        )

    def list_input_usage(
        self,
        field_id: Optional[int] = None,
        category: Optional[InputCategory] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        year: Optional[int] = None
    ) -> List[InputUsageResponse]:
        """List input usage records with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT i.*, f.name as field_name
            FROM sustainability_inputs i
            LEFT JOIN fields f ON i.field_id = f.id
            WHERE 1=1
        """
        params = []

        if field_id:
            query += " AND i.field_id = ?"
            params.append(field_id)

        if category:
            query += " AND i.category = ?"
            params.append(category.value)

        if start_date:
            query += " AND i.application_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND i.application_date <= ?"
            params.append(end_date.isoformat())

        if year:
            query += " AND strftime('%Y', i.application_date) = ?"
            params.append(str(year))

        query += " ORDER BY i.application_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_input_response(row) for row in rows]

    def get_input_summary(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> List[InputSummary]:
        """Get summarized input usage by category for a year"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                category,
                unit,
                SUM(quantity) as total_quantity,
                SUM(cost) as total_cost,
                SUM(acres_applied) as total_acres,
                SUM(carbon_footprint_kg) as total_carbon
            FROM sustainability_inputs
            WHERE strftime('%Y', application_date) = ?
        """
        params = [str(year)]

        if field_id:
            query += " AND field_id = ?"
            params.append(field_id)

        query += " GROUP BY category, unit"

        cursor.execute(query, params)
        current_rows = cursor.fetchall()

        # Get previous year for comparison
        cursor.execute(query.replace("= ?", "= ?", 1), [str(year - 1)] + params[1:])
        prev_rows = cursor.fetchall()

        conn.close()

        # Build lookup for previous year
        prev_lookup = {row["category"]: row["total_quantity"] for row in prev_rows}

        summaries = []
        for row in current_rows:
            total_acres = row["total_acres"] or 1
            prev_qty = prev_lookup.get(row["category"])
            yoy_change = None
            if prev_qty and prev_qty > 0:
                yoy_change = ((row["total_quantity"] - prev_qty) / prev_qty) * 100

            summaries.append(InputSummary(
                category=InputCategory(row["category"]),
                total_quantity=row["total_quantity"],
                unit=row["unit"],
                total_cost=row["total_cost"],
                total_acres=total_acres,
                rate_per_acre=row["total_quantity"] / total_acres,
                carbon_footprint_kg=row["total_carbon"] or 0,
                year_over_year_change=yoy_change
            ))

        return summaries

    # =========================================================================
    # CARBON TRACKING
    # =========================================================================

    def record_carbon_entry(self, data: CarbonEntryCreate, user_id: int) -> Tuple[Optional[CarbonEntryResponse], Optional[str]]:
        """Record a carbon emission or sequestration event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sustainability_carbon
                (field_id, source, carbon_kg, activity_date, description,
                 calculation_method, data_source, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.source.value, data.carbon_kg,
                data.activity_date.isoformat(), data.description,
                data.calculation_method, data.data_source, user_id
            ))

            entry_id = cursor.lastrowid
            conn.commit()

            result = self.get_carbon_entry(entry_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_carbon_entry(self, entry_id: int) -> Optional[CarbonEntryResponse]:
        """Get a single carbon entry"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.*, f.name as field_name, f.acreage as field_acres
            FROM sustainability_carbon c
            LEFT JOIN fields f ON c.field_id = f.id
            WHERE c.id = ?
        """, (entry_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_carbon_response(row)

    def _row_to_carbon_response(self, row: sqlite3.Row) -> CarbonEntryResponse:
        """Convert database row to CarbonEntryResponse"""
        field_acres = row["field_acres"] if "field_acres" in row.keys() else None
        carbon_per_acre = row["carbon_kg"] / field_acres if field_acres and field_acres > 0 else None

        return CarbonEntryResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            source=CarbonSource(row["source"]),
            carbon_kg=row["carbon_kg"],
            carbon_per_acre=carbon_per_acre,
            activity_date=date.fromisoformat(row["activity_date"]),
            description=row["description"],
            calculation_method=row["calculation_method"],
            data_source=row["data_source"],
            created_by_user_id=row["created_by_user_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def get_carbon_summary(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> CarbonSummary:
        """Get carbon footprint summary for a year"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                source,
                SUM(CASE WHEN carbon_kg > 0 THEN carbon_kg ELSE 0 END) as emissions,
                SUM(CASE WHEN carbon_kg < 0 THEN carbon_kg ELSE 0 END) as sequestration
            FROM sustainability_carbon
            WHERE strftime('%Y', activity_date) = ?
        """
        params = [str(year)]

        if field_id:
            query += " AND field_id = ?"
            params.append(field_id)

        query += " GROUP BY source"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Get total acres
        if field_id:
            cursor.execute("SELECT acreage as total FROM fields WHERE id = ?", (field_id,))
        else:
            cursor.execute("SELECT SUM(acreage) as total FROM fields WHERE is_active = 1")
        acres_row = cursor.fetchone()
        total_acres = acres_row["total"] or 1

        conn.close()

        # Calculate totals
        total_emissions = 0
        total_sequestration = 0
        by_source = {}

        for row in rows:
            emissions = row["emissions"] or 0
            sequestration = row["sequestration"] or 0
            total_emissions += emissions
            total_sequestration += sequestration
            by_source[row["source"]] = emissions + sequestration

        net_carbon = total_emissions + total_sequestration  # sequestration is negative

        return CarbonSummary(
            period=str(year),
            total_emissions_kg=_safe_float(total_emissions),
            total_sequestration_kg=_safe_float(abs(total_sequestration)),
            net_carbon_kg=_safe_float(net_carbon),
            emissions_per_acre=_safe_float(total_emissions / total_acres),
            sequestration_per_acre=_safe_float(abs(total_sequestration) / total_acres),
            net_per_acre=_safe_float(net_carbon / total_acres),
            by_source={k: _safe_float(v) for k, v in by_source.items()},
            trend="improving" if net_carbon < 0 else "needs_improvement"
        )

    # =========================================================================
    # WATER TRACKING
    # =========================================================================

    def record_water_usage(self, data: WaterUsageCreate, user_id: int) -> Tuple[Optional[WaterUsageResponse], Optional[str]]:
        """Record water usage"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sustainability_water
                (field_id, usage_date, gallons, irrigation_method, source,
                 acres_irrigated, hours_run, notes, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.usage_date.isoformat(), data.gallons,
                data.irrigation_method, data.source, data.acres_irrigated,
                data.hours_run, data.notes, user_id
            ))

            water_id = cursor.lastrowid
            conn.commit()

            result = self.get_water_usage(water_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_water_usage(self, water_id: int) -> Optional[WaterUsageResponse]:
        """Get a single water usage record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT w.*, f.name as field_name
            FROM sustainability_water w
            LEFT JOIN fields f ON w.field_id = f.id
            WHERE w.id = ?
        """, (water_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_water_response(row)

    def _row_to_water_response(self, row: sqlite3.Row) -> WaterUsageResponse:
        """Convert database row to WaterUsageResponse"""
        acres = row["acres_irrigated"]
        gallons_per_acre = row["gallons"] / acres if acres and acres > 0 else None

        return WaterUsageResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            usage_date=date.fromisoformat(row["usage_date"]),
            gallons=row["gallons"],
            gallons_per_acre=gallons_per_acre,
            irrigation_method=row["irrigation_method"],
            source=row["source"],
            acres_irrigated=row["acres_irrigated"],
            hours_run=row["hours_run"],
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def get_water_summary(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> WaterSummary:
        """Get water usage summary for a year"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                SUM(gallons) as total_gallons,
                SUM(acres_irrigated) as total_acres,
                irrigation_method,
                source
            FROM sustainability_water
            WHERE strftime('%Y', usage_date) = ?
        """
        params = [str(year)]

        if field_id:
            query += " AND field_id = ?"
            params.append(field_id)

        # Get totals
        cursor.execute(query.replace("irrigation_method,", "").replace("source", "1"), params)
        totals = cursor.fetchone()

        # Get by method
        cursor.execute(query + " GROUP BY irrigation_method", params)
        method_rows = cursor.fetchall()

        # Get by source
        cursor.execute(query.replace("irrigation_method,", "") + " GROUP BY source", params)
        source_rows = cursor.fetchall()

        conn.close()

        total_gallons = totals["total_gallons"] or 0
        total_acres = totals["total_acres"] or 1

        by_method = {row["irrigation_method"] or "unknown": _safe_float(row["total_gallons"] or 0) for row in method_rows}
        by_source = {row["source"] or "unknown": _safe_float(row["total_gallons"] or 0) for row in source_rows}

        # Calculate efficiency score (lower gallons per acre = higher score)
        gpa = total_gallons / total_acres if total_acres > 0 else 0
        # Benchmark: drip ~2000 gal/acre, flood ~5000 gal/acre
        efficiency_score = max(0, min(100, 100 - (gpa / 50)))  # Simplified scoring

        return WaterSummary(
            period=str(year),
            total_gallons=_safe_float(total_gallons),
            total_acres=_safe_float(total_acres),
            gallons_per_acre=_safe_float(gpa),
            by_method=by_method,
            by_source=by_source,
            efficiency_score=_safe_float(efficiency_score),
            trend="stable"
        )

    # =========================================================================
    # SUSTAINABILITY PRACTICES
    # =========================================================================

    def record_practice(self, data: PracticeRecordCreate, user_id: int) -> Tuple[Optional[PracticeRecordResponse], Optional[str]]:
        """Record adoption of a sustainability practice"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Calculate carbon benefit
            carbon_benefit = self._calculate_practice_carbon_benefit(data)

            cursor.execute("""
                INSERT INTO sustainability_practices
                (field_id, practice, year, acres_implemented, start_date, end_date,
                 details, verified, verification_source, carbon_benefit_kg, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.practice.value, data.year, data.acres_implemented,
                data.start_date.isoformat() if data.start_date else None,
                data.end_date.isoformat() if data.end_date else None,
                data.details, data.verified, data.verification_source,
                carbon_benefit, user_id
            ))

            practice_id = cursor.lastrowid

            # Record carbon sequestration entry
            if carbon_benefit and carbon_benefit < 0:  # Negative = sequestration
                source = CarbonSource.COVER_CROP if data.practice == SustainabilityPractice.COVER_CROPS else CarbonSource.NO_TILL
                cursor.execute("""
                    INSERT INTO sustainability_carbon
                    (field_id, source, carbon_kg, activity_date, description,
                     calculation_method, data_source, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.field_id, source.value, carbon_benefit,
                    date(data.year, 12, 31).isoformat(),
                    f"{data.practice.value} on {data.acres_implemented} acres",
                    "USDA/NRCS estimates",
                    "AgTools automatic calculation",
                    user_id
                ))

            conn.commit()

            result = self.get_practice(practice_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def _calculate_practice_carbon_benefit(self, data: PracticeRecordCreate) -> float:
        """Calculate carbon benefit of a sustainability practice"""
        practice_benefits = {
            SustainabilityPractice.COVER_CROPS: -500,  # kg CO2e per acre sequestered
            SustainabilityPractice.NO_TILL: -300,
            SustainabilityPractice.REDUCED_TILL: -150,
            SustainabilityPractice.CROP_ROTATION: -100,
            SustainabilityPractice.PRECISION_APPLICATION: -50,  # Reduced input = less emissions
            SustainabilityPractice.VARIABLE_RATE: -75,
            SustainabilityPractice.BUFFER_STRIPS: -200,
            SustainabilityPractice.POLLINATOR_HABITAT: -100,
        }

        benefit_per_acre = practice_benefits.get(data.practice, 0)
        return benefit_per_acre * data.acres_implemented

    def get_practice(self, practice_id: int) -> Optional[PracticeRecordResponse]:
        """Get a single practice record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, f.name as field_name
            FROM sustainability_practices p
            LEFT JOIN fields f ON p.field_id = f.id
            WHERE p.id = ?
        """, (practice_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_practice_response(row)

    def _row_to_practice_response(self, row: sqlite3.Row) -> PracticeRecordResponse:
        """Convert database row to PracticeRecordResponse"""
        practice = SustainabilityPractice(row["practice"])

        # Human-readable practice names
        practice_display = {
            SustainabilityPractice.COVER_CROPS: "Cover Crops",
            SustainabilityPractice.NO_TILL: "No-Till",
            SustainabilityPractice.REDUCED_TILL: "Reduced Tillage",
            SustainabilityPractice.CROP_ROTATION: "Crop Rotation",
            SustainabilityPractice.INTEGRATED_PEST_MANAGEMENT: "Integrated Pest Management (IPM)",
            SustainabilityPractice.PRECISION_APPLICATION: "Precision Application",
            SustainabilityPractice.VARIABLE_RATE: "Variable Rate Technology",
            SustainabilityPractice.BUFFER_STRIPS: "Buffer Strips",
            SustainabilityPractice.WATERWAY_PROTECTION: "Waterway Protection",
            SustainabilityPractice.POLLINATOR_HABITAT: "Pollinator Habitat",
            SustainabilityPractice.ORGANIC_PRACTICES: "Organic Practices",
            SustainabilityPractice.SOIL_TESTING: "Soil Testing",
            SustainabilityPractice.NUTRIENT_MANAGEMENT_PLAN: "Nutrient Management Plan",
            SustainabilityPractice.IRRIGATION_EFFICIENCY: "Irrigation Efficiency",
        }

        return PracticeRecordResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            practice=practice,
            practice_display=practice_display.get(practice, practice.value),
            year=row["year"],
            acres_implemented=row["acres_implemented"],
            start_date=date.fromisoformat(row["start_date"]) if row["start_date"] else None,
            end_date=date.fromisoformat(row["end_date"]) if row["end_date"] else None,
            details=row["details"],
            verified=bool(row["verified"]),
            verification_source=row["verification_source"],
            carbon_benefit_kg=row["carbon_benefit_kg"],
            created_by_user_id=row["created_by_user_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def list_practices(
        self,
        year: Optional[int] = None,
        field_id: Optional[int] = None,
        practice: Optional[SustainabilityPractice] = None
    ) -> List[PracticeRecordResponse]:
        """List sustainability practices with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT p.*, f.name as field_name
            FROM sustainability_practices p
            LEFT JOIN fields f ON p.field_id = f.id
            WHERE 1=1
        """
        params = []

        if year:
            query += " AND p.year = ?"
            params.append(year)

        if field_id:
            query += " AND p.field_id = ?"
            params.append(field_id)

        if practice:
            query += " AND p.practice = ?"
            params.append(practice.value)

        query += " ORDER BY p.year DESC, p.created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_practice_response(row) for row in rows]

    # =========================================================================
    # SUSTAINABILITY SCORECARD
    # =========================================================================

    def get_scorecard(
        self,
        field_id: Optional[int] = None,
        year: Optional[int] = None
    ) -> SustainabilityScorecard:
        """Get sustainability scorecard (wrapper for generate_scorecard)"""
        if year is None:
            year = datetime.now(timezone.utc).year
        return self.generate_scorecard(year=year, field_id=field_id)

    def generate_scorecard(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> SustainabilityScorecard:
        """Generate a comprehensive sustainability scorecard"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Determine entity
        if field_id:
            cursor.execute("SELECT name, acreage FROM fields WHERE id = ?", (field_id,))
            row = cursor.fetchone()
            entity_name = row["name"] if row else "Unknown Field"
            total_acres = row["acreage"] if row else 0
            entity_type = "field"
        else:
            entity_name = "Farm Total"
            cursor.execute("SELECT SUM(acreage) as total FROM fields WHERE is_active = 1")
            row = cursor.fetchone()
            total_acres = row["total"] or 0
            entity_type = "farm"

        # Get summaries
        carbon_summary = self.get_carbon_summary(year, field_id)
        input_summaries = self.get_input_summary(year, field_id)

        # Calculate carbon score (0-100, lower emissions = higher score)
        # Target: Net zero or negative
        net_per_acre = _safe_float(carbon_summary.net_per_acre)
        if net_per_acre <= 0:
            carbon_score_value = 100  # Carbon negative = perfect
        elif net_per_acre < 500:
            carbon_score_value = 80 + (20 * (500 - net_per_acre) / 500)
        elif net_per_acre < 1000:
            carbon_score_value = 60 + (20 * (1000 - net_per_acre) / 500)
        elif net_per_acre < 2000:
            carbon_score_value = 40 + (20 * (2000 - net_per_acre) / 1000)
        else:
            carbon_score_value = max(0, 40 - (net_per_acre - 2000) / 100)
        carbon_score_value = _safe_float(carbon_score_value, 50.0)

        carbon_score = SustainabilityScore(
            metric="Carbon Footprint",
            score=carbon_score_value,
            weight=0.30,
            weighted_score=_safe_float(carbon_score_value * 0.30),
            trend="improving" if net_per_acre < 0 else "needs_improvement",
            details=f"Net {net_per_acre:.0f} kg CO2e/acre"
        )

        # Calculate input efficiency score
        total_input_carbon = _safe_float(sum(s.carbon_footprint_kg for s in input_summaries))
        input_per_acre = _safe_float(total_input_carbon / total_acres if total_acres > 0 else 0)

        if input_per_acre < 100:
            input_score_value = 100
        elif input_per_acre < 300:
            input_score_value = 70 + (30 * (300 - input_per_acre) / 200)
        elif input_per_acre < 500:
            input_score_value = 50 + (20 * (500 - input_per_acre) / 200)
        else:
            input_score_value = max(0, 50 - (input_per_acre - 500) / 20)
        input_score_value = _safe_float(input_score_value, 50.0)

        input_efficiency_score = SustainabilityScore(
            metric="Input Efficiency",
            score=input_score_value,
            weight=0.25,
            weighted_score=_safe_float(input_score_value * 0.25),
            trend="stable",
            details=f"{input_per_acre:.0f} kg CO2e/acre from inputs"
        )

        # Water efficiency score
        try:
            water_summary = self.get_water_summary(year, field_id)
            water_score_value = _safe_float(water_summary.efficiency_score, 70.0)
        except (ValueError, AttributeError, TypeError):
            water_score_value = 70.0  # Default if no water data

        water_efficiency_score = SustainabilityScore(
            metric="Water Efficiency",
            score=water_score_value,
            weight=0.15,
            weighted_score=_safe_float(water_score_value * 0.15),
            trend="stable",
            details="Based on irrigation efficiency"
        )

        # Practice adoption score
        practices = self.list_practices(year=year, field_id=field_id)
        unique_practices = set(p.practice for p in practices)
        practice_count = len(unique_practices)

        # Score based on number of practices (max 14 possible)
        practice_score_value = _safe_float(min(100, (practice_count / 7) * 100), 50.0)

        practice_adoption_score = SustainabilityScore(
            metric="Practice Adoption",
            score=practice_score_value,
            weight=0.20,
            weighted_score=_safe_float(practice_score_value * 0.20),
            trend="improving" if practice_count > 0 else "needs_improvement",
            details=f"{practice_count} sustainable practices adopted"
        )

        # Biodiversity score (based on specific practices)
        biodiversity_practices = {
            SustainabilityPractice.COVER_CROPS,
            SustainabilityPractice.BUFFER_STRIPS,
            SustainabilityPractice.POLLINATOR_HABITAT,
            SustainabilityPractice.CROP_ROTATION,
        }
        bio_count = len(unique_practices & biodiversity_practices)
        biodiversity_score_value = _safe_float(min(100, (bio_count / 4) * 100), 50.0)

        biodiversity_score = SustainabilityScore(
            metric="Biodiversity",
            score=biodiversity_score_value,
            weight=0.10,
            weighted_score=_safe_float(biodiversity_score_value * 0.10),
            trend="improving" if bio_count > 0 else "stable",
            details=f"{bio_count} biodiversity-supporting practices"
        )

        # Calculate overall score
        overall_score = _safe_float(
            carbon_score.weighted_score +
            input_efficiency_score.weighted_score +
            water_efficiency_score.weighted_score +
            practice_adoption_score.weighted_score +
            biodiversity_score.weighted_score,
            50.0
        )

        # Assign grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        # Get previous year score
        cursor.execute("""
            SELECT overall_score FROM sustainability_scores
            WHERE entity_type = ? AND year = ?
            AND (entity_id = ? OR (entity_id IS NULL AND ? IS NULL))
        """, (entity_type, year - 1, field_id, field_id))
        prev_row = cursor.fetchone()
        previous_year_score = prev_row["overall_score"] if prev_row else None

        score_change = _safe_float(overall_score - previous_year_score) if previous_year_score else None
        score_change_percent = _safe_float(score_change / previous_year_score * 100) if previous_year_score and score_change else None

        # Improvement opportunities
        improvements = []
        if carbon_score.score < 70:
            improvements.append("Increase cover crop usage to improve carbon sequestration")
        if input_efficiency_score.score < 70:
            improvements.append("Consider precision application to reduce input usage")
        if practice_score_value < 50:
            improvements.append("Adopt additional sustainable practices (no-till, IPM, buffer strips)")
        if biodiversity_score_value < 50:
            improvements.append("Add pollinator habitat or buffer strips for biodiversity")

        conn.close()

        scorecard = SustainabilityScorecard(
            entity_type=entity_type,
            entity_id=field_id,
            entity_name=entity_name,
            year=year,
            overall_score=overall_score,
            grade=grade,
            carbon_score=carbon_score,
            input_efficiency_score=input_efficiency_score,
            water_efficiency_score=water_efficiency_score,
            practice_adoption_score=practice_adoption_score,
            biodiversity_score=biodiversity_score,
            total_carbon_footprint_kg=_safe_float(carbon_summary.total_emissions_kg),
            carbon_per_acre=_safe_float(carbon_summary.emissions_per_acre),
            carbon_sequestered_kg=_safe_float(carbon_summary.total_sequestration_kg),
            net_carbon_kg=_safe_float(carbon_summary.net_carbon_kg),
            total_acres=_safe_float(total_acres),
            practices_adopted=[p.value for p in unique_practices],
            improvement_opportunities=improvements,
            previous_year_score=previous_year_score,
            score_change=score_change,
            score_change_percent=score_change_percent,
            generated_at=datetime.now(timezone.utc)
        )

        # Save scorecard to database
        self._save_scorecard(scorecard)

        return scorecard

    def _save_scorecard(self, scorecard: SustainabilityScorecard):
        """Save scorecard to database for historical tracking"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO sustainability_scores
            (entity_type, entity_id, year, overall_score, carbon_score,
             input_score, water_score, practice_score, biodiversity_score, scorecard_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scorecard.entity_type,
            scorecard.entity_id,
            scorecard.year,
            scorecard.overall_score,
            scorecard.carbon_score.score,
            scorecard.input_efficiency_score.score,
            scorecard.water_efficiency_score.score,
            scorecard.practice_adoption_score.score,
            scorecard.biodiversity_score.score,
            scorecard.model_dump_json()
        ))

        conn.commit()
        conn.close()

    def get_historical_scores(
        self,
        field_id: Optional[int] = None,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """Get historical sustainability scores"""
        conn = self._get_connection()
        cursor = conn.cursor()

        entity_type = "field" if field_id else "farm"

        cursor.execute("""
            SELECT year, overall_score, carbon_score, input_score,
                   water_score, practice_score, biodiversity_score
            FROM sustainability_scores
            WHERE entity_type = ?
            AND (entity_id = ? OR (entity_id IS NULL AND ? IS NULL))
            ORDER BY year DESC
            LIMIT ?
        """, (entity_type, field_id, field_id, years))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # =========================================================================
    # RESEARCH DATA EXPORT
    # =========================================================================

    def _sanitize_floats(self, obj: Any) -> Any:
        """Recursively sanitize float values to be JSON-serializable (replace inf/nan with None)"""
        if isinstance(obj, dict):
            return {k: self._sanitize_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_floats(v) for v in obj]
        elif isinstance(obj, float):
            if math.isinf(obj) or math.isnan(obj):
                return None
            return obj
        return obj

    def export_research_data(
        self,
        year: int,
        field_id: Optional[int] = None,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """Export sustainability data in research-ready format"""
        inputs = self.list_input_usage(field_id=field_id, year=year)
        practices = self.list_practices(year=year, field_id=field_id)
        carbon = self.get_carbon_summary(year, field_id)
        scorecard = self.generate_scorecard(year, field_id)

        export_data = {
            "metadata": {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "year": year,
                "field_id": field_id,
                "format": format,
                "software": "AgTools Sustainability Module",
                "version": "1.0.0"
            },
            "summary": {
                "total_acres": scorecard.total_acres,
                "overall_sustainability_score": scorecard.overall_score,
                "grade": scorecard.grade,
                "net_carbon_kg_per_acre": carbon.net_per_acre,
                "practices_count": len(scorecard.practices_adopted)
            },
            "carbon_metrics": {
                "total_emissions_kg": carbon.total_emissions_kg,
                "total_sequestration_kg": carbon.total_sequestration_kg,
                "net_carbon_kg": carbon.net_carbon_kg,
                "emissions_per_acre": carbon.emissions_per_acre,
                "by_source": carbon.by_source
            },
            "input_records": [i.model_dump() for i in inputs],
            "practice_records": [p.model_dump() for p in practices],
            "scores": {
                "carbon": scorecard.carbon_score.model_dump(),
                "input_efficiency": scorecard.input_efficiency_score.model_dump(),
                "water_efficiency": scorecard.water_efficiency_score.model_dump(),
                "practice_adoption": scorecard.practice_adoption_score.model_dump(),
                "biodiversity": scorecard.biodiversity_score.model_dump()
            }
        }

        # Sanitize any infinity/nan values for JSON serialization
        return self._sanitize_floats(export_data)

    def get_report(
        self,
        year: Optional[int] = None,
        field_id: Optional[int] = None
    ) -> SustainabilityReport:
        """Get comprehensive sustainability report (wrapper for generate_grant_report)"""
        if year is None:
            year = datetime.now(timezone.utc).year
        return self.generate_grant_report(year=year, field_id=field_id)

    def generate_grant_report(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> SustainabilityReport:
        """Generate a comprehensive sustainability report for research documentation"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get farm info
        cursor.execute("SELECT COUNT(*) as count, SUM(acreage) as acres FROM fields WHERE is_active = 1")
        farm_row = cursor.fetchone()

        # Get crops grown
        cursor.execute("SELECT DISTINCT current_crop FROM fields WHERE is_active = 1 AND current_crop IS NOT NULL")
        crops = [row["current_crop"] for row in cursor.fetchall()]

        conn.close()

        scorecard = self.generate_scorecard(year, field_id)
        input_summary = self.get_input_summary(year, field_id)
        carbon_summary = self.get_carbon_summary(year, field_id)

        try:
            water_summary = self.get_water_summary(year, field_id)
        except (ValueError, AttributeError, TypeError):
            water_summary = None

        practices = self.list_practices(year=year, field_id=field_id)
        historical = self.get_historical_scores(field_id, years=5)

        # Practice summary
        practice_summary = {}
        for p in practices:
            if p.practice.value not in practice_summary:
                practice_summary[p.practice.value] = {
                    "display_name": p.practice_display,
                    "total_acres": 0,
                    "fields_count": 0,
                    "verified_acres": 0
                }
            practice_summary[p.practice.value]["total_acres"] += p.acres_implemented
            practice_summary[p.practice.value]["fields_count"] += 1
            if p.verified:
                practice_summary[p.practice.value]["verified_acres"] += p.acres_implemented

        # Grant-ready metrics
        grant_metrics = {
            "total_managed_acres": scorecard.total_acres,
            "sustainable_practice_acres": sum(p.acres_implemented for p in practices),
            "carbon_sequestered_metric_tons": scorecard.carbon_sequestered_kg / 1000,
            "net_carbon_metric_tons": scorecard.net_carbon_kg / 1000,
            "practices_implemented": len(set(p.practice for p in practices)),
            "sustainability_score": scorecard.overall_score,
            "year_over_year_improvement": scorecard.score_change_percent,
            "climate_smart_practices": [
                p.practice_display for p in practices
                if p.practice in {
                    SustainabilityPractice.COVER_CROPS,
                    SustainabilityPractice.NO_TILL,
                    SustainabilityPractice.REDUCED_TILL,
                    SustainabilityPractice.PRECISION_APPLICATION,
                    SustainabilityPractice.VARIABLE_RATE
                }
            ]
        }

        # Recommendations
        recommendations = scorecard.improvement_opportunities.copy()
        if not any(p.practice == SustainabilityPractice.NUTRIENT_MANAGEMENT_PLAN for p in practices):
            recommendations.append("Develop a formal Nutrient Management Plan for documentation")
        if not any(p.practice == SustainabilityPractice.SOIL_TESTING for p in practices):
            recommendations.append("Implement regular soil testing program")

        return SustainabilityReport(
            report_title=f"Sustainability Report - {year}",
            generated_at=datetime.now(timezone.utc),
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            farm_name="Farm Operations",
            total_acres=scorecard.total_acres,
            total_fields=farm_row["count"] or 0,
            crops_grown=crops,
            scorecard=scorecard,
            input_summary=input_summary,
            carbon_summary=carbon_summary,
            water_summary=water_summary,
            practices_summary=practice_summary,
            historical_scores=historical,
            improvement_recommendations=recommendations,
            grant_metrics=grant_metrics
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_sustainability_service(db_path: str = None) -> SustainabilityService:
    """Get an instance of the sustainability service"""
    if db_path is None:
        db_path = os.environ.get("AGTOOLS_DB_PATH", "agtools.db")
    return SustainabilityService(db_path)
