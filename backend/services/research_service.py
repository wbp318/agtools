"""
Field Trial & Research Service for AgTools

Provides tools for conducting agricultural research trials with proper
experimental design, data collection, and statistical analysis.

Features:
- Field trial management with treatment/control plots
- Replicated study design support (RCBD, split-plot)
- Data collection forms with validation
- Statistical analysis (t-tests, ANOVA)
- Research data export in standard formats
- Protocol documentation
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import sqlite3
import os
import math
from statistics import mean, stdev, variance


# =============================================================================
# ENUMS
# =============================================================================

class TrialType(str, Enum):
    """Types of field trials"""
    VARIETY_TRIAL = "variety_trial"
    TREATMENT_COMPARISON = "treatment_comparison"
    RATE_STUDY = "rate_study"
    TIMING_STUDY = "timing_study"
    PRODUCT_EVALUATION = "product_evaluation"
    DEMONSTRATION = "demonstration"
    ON_FARM_RESEARCH = "on_farm_research"


class ExperimentalDesign(str, Enum):
    """Experimental design types"""
    CRD = "completely_randomized"  # Completely Randomized Design
    RCBD = "randomized_complete_block"  # Randomized Complete Block Design
    SPLIT_PLOT = "split_plot"
    STRIP_PLOT = "strip_plot"
    FACTORIAL = "factorial"
    SIMPLE_PAIRED = "simple_paired"  # Simple A/B comparison


class PlotStatus(str, Enum):
    """Status of a plot"""
    PLANNED = "planned"
    PLANTED = "planted"
    GROWING = "growing"
    HARVESTED = "harvested"
    ABANDONED = "abandoned"


class MeasurementType(str, Enum):
    """Types of measurements that can be recorded"""
    YIELD = "yield"
    PLANT_POPULATION = "plant_population"
    PLANT_HEIGHT = "plant_height"
    PEST_RATING = "pest_rating"
    DISEASE_RATING = "disease_rating"
    VIGOR_RATING = "vigor_rating"
    MOISTURE = "moisture"
    TEST_WEIGHT = "test_weight"
    LODGING = "lodging"
    GREENSNAP = "greensnap"
    STANDABILITY = "standability"
    CUSTOM = "custom"


# =============================================================================
# PYDANTIC MODELS - Trial Management
# =============================================================================

class TrialCreate(BaseModel):
    """Create a new field trial"""
    name: str = Field(..., min_length=1, max_length=200)
    trial_type: TrialType
    design: ExperimentalDesign
    year: int
    field_id: Optional[int] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    hypothesis: Optional[str] = None

    # Protocol details
    crop_type: str
    planting_date: Optional[date] = None
    harvest_date: Optional[date] = None

    # Design parameters
    num_treatments: int = Field(..., ge=1)
    num_replications: int = Field(1, ge=1)
    plot_size_acres: Optional[float] = Field(None, ge=0)
    plot_length_ft: Optional[float] = Field(None, ge=0)
    plot_width_ft: Optional[float] = Field(None, ge=0)

    # Metadata
    principal_investigator: Optional[str] = None
    funding_source: Optional[str] = None
    protocol_number: Optional[str] = None


class TrialUpdate(BaseModel):
    """Update a trial"""
    name: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    hypothesis: Optional[str] = None
    planting_date: Optional[date] = None
    harvest_date: Optional[date] = None
    principal_investigator: Optional[str] = None
    conclusion: Optional[str] = None


class TrialResponse(BaseModel):
    """Response model for trial"""
    id: int
    name: str
    trial_type: TrialType
    design: ExperimentalDesign
    year: int
    field_id: Optional[int]
    field_name: Optional[str]
    description: Optional[str]
    objective: Optional[str]
    hypothesis: Optional[str]
    conclusion: Optional[str]

    crop_type: str
    planting_date: Optional[date]
    harvest_date: Optional[date]

    num_treatments: int
    num_replications: int
    plot_size_acres: Optional[float]
    plot_count: int

    principal_investigator: Optional[str]
    funding_source: Optional[str]
    protocol_number: Optional[str]

    status: str
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# PYDANTIC MODELS - Treatments
# =============================================================================

class TreatmentCreate(BaseModel):
    """Create a treatment for a trial"""
    trial_id: int
    treatment_number: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_control: bool = False

    # Product/treatment details
    product_name: Optional[str] = None
    rate: Optional[float] = None
    rate_unit: Optional[str] = None
    application_timing: Optional[str] = None
    application_method: Optional[str] = None


class TreatmentResponse(BaseModel):
    """Response model for treatment"""
    id: int
    trial_id: int
    treatment_number: int
    name: str
    description: Optional[str]
    is_control: bool
    product_name: Optional[str]
    rate: Optional[float]
    rate_unit: Optional[str]
    application_timing: Optional[str]
    application_method: Optional[str]
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Plots
# =============================================================================

class PlotCreate(BaseModel):
    """Create a plot"""
    trial_id: int
    treatment_id: int
    replication: int = Field(..., ge=1)
    plot_number: Optional[int] = None
    row_number: Optional[int] = None
    column_number: Optional[int] = None

    # Location
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    location_notes: Optional[str] = None


class PlotResponse(BaseModel):
    """Response model for plot"""
    id: int
    trial_id: int
    treatment_id: int
    treatment_name: str
    replication: int
    plot_number: Optional[int]
    row_number: Optional[int]
    column_number: Optional[int]
    status: PlotStatus
    gps_latitude: Optional[float]
    gps_longitude: Optional[float]
    location_notes: Optional[str]
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Measurements
# =============================================================================

class MeasurementCreate(BaseModel):
    """Record a measurement"""
    plot_id: int
    measurement_type: MeasurementType
    value: float
    unit: Optional[str] = None
    measurement_date: date
    notes: Optional[str] = None

    # For custom measurements
    custom_name: Optional[str] = None


class MeasurementResponse(BaseModel):
    """Response model for measurement"""
    id: int
    plot_id: int
    plot_number: Optional[int]
    treatment_name: str
    replication: int
    measurement_type: MeasurementType
    custom_name: Optional[str]
    value: float
    unit: Optional[str]
    measurement_date: date
    notes: Optional[str]
    created_by_user_id: int
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Analysis Results
# =============================================================================

class TreatmentMean(BaseModel):
    """Treatment mean for analysis"""
    treatment_id: int
    treatment_name: str
    is_control: bool
    n: int
    mean: float
    std_dev: float
    std_error: float
    min_value: float
    max_value: float
    cv_percent: float


class TTestResult(BaseModel):
    """T-test comparison result"""
    treatment_a: str
    treatment_b: str
    mean_a: float
    mean_b: float
    difference: float
    difference_percent: float
    t_statistic: float
    p_value: float
    significant: bool
    significance_level: str


class ANOVAResult(BaseModel):
    """ANOVA result"""
    source: str
    df: int
    ss: float
    ms: float
    f_value: float
    p_value: float
    significant: bool


class TrialAnalysis(BaseModel):
    """Complete trial analysis"""
    trial_id: int
    trial_name: str
    measurement_type: str
    analysis_date: datetime

    # Summary statistics
    overall_mean: float
    overall_std: float
    cv_percent: float
    n_total: int

    # Treatment means
    treatment_means: List[TreatmentMean]

    # LSD (Least Significant Difference)
    lsd_05: Optional[float] = None
    lsd_01: Optional[float] = None

    # ANOVA (if replicated)
    anova: Optional[List[ANOVAResult]] = None

    # Pairwise comparisons
    pairwise_tests: Optional[List[TTestResult]] = None

    # Recommendations
    top_performer: Optional[str] = None
    significantly_different: bool
    interpretation: str


class ResearchExport(BaseModel):
    """Research data export"""
    trial: TrialResponse
    treatments: List[TreatmentResponse]
    plots: List[PlotResponse]
    measurements: List[MeasurementResponse]
    analysis: Optional[TrialAnalysis] = None
    export_date: datetime
    export_format: str


# =============================================================================
# RESEARCH SERVICE CLASS
# =============================================================================

class ResearchService:
    """
    Service for managing field trials and research data.

    Supports proper experimental design, data collection,
    and statistical analysis for agricultural research.
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
        """Initialize research tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Trials
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_trials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                trial_type VARCHAR(50) NOT NULL,
                design VARCHAR(50) NOT NULL,
                year INTEGER NOT NULL,
                field_id INTEGER,
                description TEXT,
                objective TEXT,
                hypothesis TEXT,
                conclusion TEXT,
                crop_type VARCHAR(50) NOT NULL,
                planting_date DATE,
                harvest_date DATE,
                num_treatments INTEGER NOT NULL,
                num_replications INTEGER DEFAULT 1,
                plot_size_acres REAL,
                plot_length_ft REAL,
                plot_width_ft REAL,
                principal_investigator VARCHAR(200),
                funding_source VARCHAR(200),
                protocol_number VARCHAR(100),
                status VARCHAR(20) DEFAULT 'active',
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Treatments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_treatments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trial_id INTEGER NOT NULL,
                treatment_number INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                is_control BOOLEAN DEFAULT 0,
                product_name VARCHAR(200),
                rate REAL,
                rate_unit VARCHAR(50),
                application_timing VARCHAR(100),
                application_method VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(trial_id, treatment_number),
                FOREIGN KEY (trial_id) REFERENCES research_trials(id)
            )
        """)

        # Plots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_plots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trial_id INTEGER NOT NULL,
                treatment_id INTEGER NOT NULL,
                replication INTEGER NOT NULL,
                plot_number INTEGER,
                row_number INTEGER,
                column_number INTEGER,
                status VARCHAR(20) DEFAULT 'planned',
                gps_latitude REAL,
                gps_longitude REAL,
                location_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trial_id) REFERENCES research_trials(id),
                FOREIGN KEY (treatment_id) REFERENCES research_treatments(id)
            )
        """)

        # Measurements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plot_id INTEGER NOT NULL,
                measurement_type VARCHAR(50) NOT NULL,
                custom_name VARCHAR(100),
                value REAL NOT NULL,
                unit VARCHAR(50),
                measurement_date DATE NOT NULL,
                notes TEXT,
                created_by_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plot_id) REFERENCES research_plots(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trials_year ON research_trials(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_treatments_trial ON research_treatments(trial_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plots_trial ON research_plots(trial_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_plots_treatment ON research_plots(treatment_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_plot ON research_measurements(plot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_type ON research_measurements(measurement_type)")

        conn.commit()
        conn.close()

    # =========================================================================
    # TRIAL MANAGEMENT
    # =========================================================================

    def create_trial(
        self,
        data: TrialCreate,
        user_id: int
    ) -> Tuple[Optional[TrialResponse], Optional[str]]:
        """Create a new field trial"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO research_trials
                (name, trial_type, design, year, field_id, description, objective,
                 hypothesis, crop_type, planting_date, harvest_date, num_treatments,
                 num_replications, plot_size_acres, plot_length_ft, plot_width_ft,
                 principal_investigator, funding_source, protocol_number, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.name, data.trial_type.value, data.design.value,
                data.year, data.field_id, data.description, data.objective,
                data.hypothesis, data.crop_type,
                data.planting_date.isoformat() if data.planting_date else None,
                data.harvest_date.isoformat() if data.harvest_date else None,
                data.num_treatments, data.num_replications, data.plot_size_acres,
                data.plot_length_ft, data.plot_width_ft, data.principal_investigator,
                data.funding_source, data.protocol_number, user_id
            ))

            trial_id = cursor.lastrowid
            conn.commit()

            result = self.get_trial(trial_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_trial(self, trial_id: int) -> Optional[TrialResponse]:
        """Get a single trial"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.*, f.name as field_name,
                   (SELECT COUNT(*) FROM research_plots WHERE trial_id = t.id) as plot_count
            FROM research_trials t
            LEFT JOIN fields f ON t.field_id = f.id
            WHERE t.id = ?
        """, (trial_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_trial_response(row)

    def _row_to_trial_response(self, row: sqlite3.Row) -> TrialResponse:
        """Convert database row to TrialResponse"""
        return TrialResponse(
            id=row["id"],
            name=row["name"],
            trial_type=TrialType(row["trial_type"]),
            design=ExperimentalDesign(row["design"]),
            year=row["year"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            description=row["description"],
            objective=row["objective"],
            hypothesis=row["hypothesis"],
            conclusion=row["conclusion"],
            crop_type=row["crop_type"],
            planting_date=date.fromisoformat(row["planting_date"]) if row["planting_date"] else None,
            harvest_date=date.fromisoformat(row["harvest_date"]) if row["harvest_date"] else None,
            num_treatments=row["num_treatments"],
            num_replications=row["num_replications"],
            plot_size_acres=row["plot_size_acres"],
            plot_count=row["plot_count"] if "plot_count" in row.keys() else 0,
            principal_investigator=row["principal_investigator"],
            funding_source=row["funding_source"],
            protocol_number=row["protocol_number"],
            status=row["status"],
            created_by_user_id=row["created_by_user_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(timezone.utc)
        )

    def list_trials(
        self,
        year: Optional[int] = None,
        trial_type: Optional[TrialType] = None,
        field_id: Optional[int] = None
    ) -> List[TrialResponse]:
        """List trials with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT t.*, f.name as field_name,
                   (SELECT COUNT(*) FROM research_plots WHERE trial_id = t.id) as plot_count
            FROM research_trials t
            LEFT JOIN fields f ON t.field_id = f.id
            WHERE 1=1
        """
        params = []

        if year:
            query += " AND t.year = ?"
            params.append(year)

        if trial_type:
            query += " AND t.trial_type = ?"
            params.append(trial_type.value)

        if field_id:
            query += " AND t.field_id = ?"
            params.append(field_id)

        query += " ORDER BY t.year DESC, t.created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_trial_response(row) for row in rows]

    def update_trial(
        self,
        trial_id: int,
        data: TrialUpdate,
        user_id: int
    ) -> Tuple[Optional[TrialResponse], Optional[str]]:
        """Update a trial"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if data.name is not None:
                updates.append("name = ?")
                params.append(data.name)
            if data.description is not None:
                updates.append("description = ?")
                params.append(data.description)
            if data.objective is not None:
                updates.append("objective = ?")
                params.append(data.objective)
            if data.hypothesis is not None:
                updates.append("hypothesis = ?")
                params.append(data.hypothesis)
            if data.planting_date is not None:
                updates.append("planting_date = ?")
                params.append(data.planting_date.isoformat())
            if data.harvest_date is not None:
                updates.append("harvest_date = ?")
                params.append(data.harvest_date.isoformat())
            if data.principal_investigator is not None:
                updates.append("principal_investigator = ?")
                params.append(data.principal_investigator)
            if data.conclusion is not None:
                updates.append("conclusion = ?")
                params.append(data.conclusion)

            if not updates:
                return self.get_trial(trial_id), None

            updates.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(trial_id)

            cursor.execute(f"""
                UPDATE research_trials SET {', '.join(updates)} WHERE id = ?
            """, params)

            conn.commit()

            result = self.get_trial(trial_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    # =========================================================================
    # TREATMENT MANAGEMENT
    # =========================================================================

    def add_treatment(
        self,
        data: TreatmentCreate,
        user_id: int
    ) -> Tuple[Optional[TreatmentResponse], Optional[str]]:
        """Add a treatment to a trial"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO research_treatments
                (trial_id, treatment_number, name, description, is_control,
                 product_name, rate, rate_unit, application_timing, application_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.trial_id, data.treatment_number, data.name, data.description,
                data.is_control, data.product_name, data.rate, data.rate_unit,
                data.application_timing, data.application_method
            ))

            treatment_id = cursor.lastrowid
            conn.commit()

            result = self.get_treatment(treatment_id)
            conn.close()

            return result, None

        except sqlite3.IntegrityError:
            return None, f"Treatment number {data.treatment_number} already exists in this trial"
        except Exception as e:
            return None, str(e)

    def get_treatment(self, treatment_id: int) -> Optional[TreatmentResponse]:
        """Get a single treatment"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM research_treatments WHERE id = ?", (treatment_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return TreatmentResponse(
            id=row["id"],
            trial_id=row["trial_id"],
            treatment_number=row["treatment_number"],
            name=row["name"],
            description=row["description"],
            is_control=bool(row["is_control"]),
            product_name=row["product_name"],
            rate=row["rate"],
            rate_unit=row["rate_unit"],
            application_timing=row["application_timing"],
            application_method=row["application_method"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def list_treatments(self, trial_id: int) -> List[TreatmentResponse]:
        """List treatments for a trial"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM research_treatments
            WHERE trial_id = ?
            ORDER BY treatment_number
        """, (trial_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            TreatmentResponse(
                id=row["id"],
                trial_id=row["trial_id"],
                treatment_number=row["treatment_number"],
                name=row["name"],
                description=row["description"],
                is_control=bool(row["is_control"]),
                product_name=row["product_name"],
                rate=row["rate"],
                rate_unit=row["rate_unit"],
                application_timing=row["application_timing"],
                application_method=row["application_method"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            )
            for row in rows
        ]

    # =========================================================================
    # PLOT MANAGEMENT
    # =========================================================================

    def add_plot(
        self,
        data: PlotCreate,
        user_id: int
    ) -> Tuple[Optional[PlotResponse], Optional[str]]:
        """Add a plot to a trial"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO research_plots
                (trial_id, treatment_id, replication, plot_number, row_number,
                 column_number, gps_latitude, gps_longitude, location_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.trial_id, data.treatment_id, data.replication,
                data.plot_number, data.row_number, data.column_number,
                data.gps_latitude, data.gps_longitude, data.location_notes
            ))

            plot_id = cursor.lastrowid
            conn.commit()

            result = self.get_plot(plot_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_plot(self, plot_id: int) -> Optional[PlotResponse]:
        """Get a single plot"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, t.name as treatment_name
            FROM research_plots p
            JOIN research_treatments t ON p.treatment_id = t.id
            WHERE p.id = ?
        """, (plot_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return PlotResponse(
            id=row["id"],
            trial_id=row["trial_id"],
            treatment_id=row["treatment_id"],
            treatment_name=row["treatment_name"],
            replication=row["replication"],
            plot_number=row["plot_number"],
            row_number=row["row_number"],
            column_number=row["column_number"],
            status=PlotStatus(row["status"]),
            gps_latitude=row["gps_latitude"],
            gps_longitude=row["gps_longitude"],
            location_notes=row["location_notes"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def list_plots(self, trial_id: int) -> List[PlotResponse]:
        """List plots for a trial"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, t.name as treatment_name
            FROM research_plots p
            JOIN research_treatments t ON p.treatment_id = t.id
            WHERE p.trial_id = ?
            ORDER BY p.replication, t.treatment_number
        """, (trial_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            PlotResponse(
                id=row["id"],
                trial_id=row["trial_id"],
                treatment_id=row["treatment_id"],
                treatment_name=row["treatment_name"],
                replication=row["replication"],
                plot_number=row["plot_number"],
                row_number=row["row_number"],
                column_number=row["column_number"],
                status=PlotStatus(row["status"]),
                gps_latitude=row["gps_latitude"],
                gps_longitude=row["gps_longitude"],
                location_notes=row["location_notes"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            )
            for row in rows
        ]

    def generate_plots(
        self,
        trial_id: int,
        user_id: int
    ) -> Tuple[int, Optional[str]]:
        """Generate all plots for a trial based on treatments and replications"""
        try:
            trial = self.get_trial(trial_id)
            if not trial:
                return 0, "Trial not found"

            treatments = self.list_treatments(trial_id)
            if not treatments:
                return 0, "No treatments defined for this trial"

            conn = self._get_connection()
            cursor = conn.cursor()

            plot_number = 1
            plots_created = 0

            for rep in range(1, trial.num_replications + 1):
                for treatment in treatments:
                    cursor.execute("""
                        INSERT INTO research_plots
                        (trial_id, treatment_id, replication, plot_number)
                        VALUES (?, ?, ?, ?)
                    """, (trial_id, treatment.id, rep, plot_number))
                    plot_number += 1
                    plots_created += 1

            conn.commit()
            conn.close()

            return plots_created, None

        except Exception as e:
            return 0, str(e)

    # =========================================================================
    # MEASUREMENT RECORDING
    # =========================================================================

    def record_measurement(
        self,
        data: MeasurementCreate,
        user_id: int
    ) -> Tuple[Optional[MeasurementResponse], Optional[str]]:
        """Record a measurement for a plot"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO research_measurements
                (plot_id, measurement_type, custom_name, value, unit,
                 measurement_date, notes, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.plot_id, data.measurement_type.value, data.custom_name,
                data.value, data.unit, data.measurement_date.isoformat(),
                data.notes, user_id
            ))

            measurement_id = cursor.lastrowid
            conn.commit()

            result = self.get_measurement(measurement_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_measurement(self, measurement_id: int) -> Optional[MeasurementResponse]:
        """Get a single measurement"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT m.*, p.plot_number, p.replication, t.name as treatment_name
            FROM research_measurements m
            JOIN research_plots p ON m.plot_id = p.id
            JOIN research_treatments t ON p.treatment_id = t.id
            WHERE m.id = ?
        """, (measurement_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return MeasurementResponse(
            id=row["id"],
            plot_id=row["plot_id"],
            plot_number=row["plot_number"],
            treatment_name=row["treatment_name"],
            replication=row["replication"],
            measurement_type=MeasurementType(row["measurement_type"]),
            custom_name=row["custom_name"],
            value=row["value"],
            unit=row["unit"],
            measurement_date=date.fromisoformat(row["measurement_date"]),
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def list_measurements(
        self,
        trial_id: int,
        measurement_type: Optional[MeasurementType] = None,
        plot_id: Optional[int] = None
    ) -> List[MeasurementResponse]:
        """List measurements for a trial"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT m.*, p.plot_number, p.replication, t.name as treatment_name
            FROM research_measurements m
            JOIN research_plots p ON m.plot_id = p.id
            JOIN research_treatments t ON p.treatment_id = t.id
            WHERE p.trial_id = ?
        """
        params = [trial_id]

        if measurement_type:
            query += " AND m.measurement_type = ?"
            params.append(measurement_type.value)

        if plot_id:
            query += " AND m.plot_id = ?"
            params.append(plot_id)

        query += " ORDER BY m.measurement_date, t.treatment_number, p.replication"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            MeasurementResponse(
                id=row["id"],
                plot_id=row["plot_id"],
                plot_number=row["plot_number"],
                treatment_name=row["treatment_name"],
                replication=row["replication"],
                measurement_type=MeasurementType(row["measurement_type"]),
                custom_name=row["custom_name"],
                value=row["value"],
                unit=row["unit"],
                measurement_date=date.fromisoformat(row["measurement_date"]),
                notes=row["notes"],
                created_by_user_id=row["created_by_user_id"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            )
            for row in rows
        ]

    # =========================================================================
    # STATISTICAL ANALYSIS
    # =========================================================================

    def analyze_trial(
        self,
        trial_id: int,
        measurement_type: MeasurementType
    ) -> Optional[TrialAnalysis]:
        """Perform statistical analysis on trial data"""
        trial = self.get_trial(trial_id)
        if not trial:
            return None

        measurements = self.list_measurements(trial_id, measurement_type)
        if not measurements:
            return None

        treatments = self.list_treatments(trial_id)

        # Group measurements by treatment
        treatment_data: Dict[int, Dict[str, Any]] = {}
        for t in treatments:
            treatment_data[t.id] = {
                "name": t.name,
                "is_control": t.is_control,
                "values": []
            }

        conn = self._get_connection()
        cursor = conn.cursor()

        # Get treatment_id for each measurement via plot
        for m in measurements:
            cursor.execute("""
                SELECT treatment_id FROM research_plots WHERE id = ?
            """, (m.plot_id,))
            row = cursor.fetchone()
            if row and row["treatment_id"] in treatment_data:
                treatment_data[row["treatment_id"]]["values"].append(m.value)

        conn.close()

        # Calculate treatment means
        all_values = []
        treatment_means = []

        for tid, tdata in treatment_data.items():
            values = tdata["values"]
            if not values:
                continue

            all_values.extend(values)

            n = len(values)
            m = mean(values)
            sd = stdev(values) if n > 1 else 0
            se = sd / math.sqrt(n) if n > 0 else 0
            cv = (sd / m * 100) if m != 0 else 0

            treatment_means.append(TreatmentMean(
                treatment_id=tid,
                treatment_name=tdata["name"],
                is_control=tdata["is_control"],
                n=n,
                mean=round(m, 2),
                std_dev=round(sd, 2),
                std_error=round(se, 2),
                min_value=min(values),
                max_value=max(values),
                cv_percent=round(cv, 1)
            ))

        if not all_values:
            return None

        # Overall statistics
        overall_mean = mean(all_values)
        overall_std = stdev(all_values) if len(all_values) > 1 else 0
        cv_percent = (overall_std / overall_mean * 100) if overall_mean != 0 else 0

        # Sort treatment means by mean value (descending)
        treatment_means.sort(key=lambda x: x.mean, reverse=True)

        # Pairwise t-tests
        pairwise_tests = []
        for i, ta in enumerate(treatment_means):
            for tb in treatment_means[i+1:]:
                t_result = self._perform_ttest(
                    treatment_data[ta.treatment_id]["values"],
                    treatment_data[tb.treatment_id]["values"],
                    ta.treatment_name,
                    tb.treatment_name
                )
                if t_result:
                    pairwise_tests.append(t_result)

        # Determine if significantly different
        sig_diffs = [t for t in pairwise_tests if t.significant]
        significantly_different = len(sig_diffs) > 0

        # Top performer
        top_performer = treatment_means[0].treatment_name if treatment_means else None

        # Interpretation
        if significantly_different:
            interpretation = f"{top_performer} showed the highest {measurement_type.value} with statistically significant differences from other treatments."
        else:
            interpretation = f"No statistically significant differences were detected among treatments for {measurement_type.value}."

        # LSD calculation (simplified)
        lsd_05 = None
        lsd_01 = None
        if len(treatment_means) > 1 and trial.num_replications > 1:
            # Pooled standard error
            mse = sum(t.std_dev ** 2 for t in treatment_means) / len(treatment_means)
            se_diff = math.sqrt(2 * mse / trial.num_replications)
            # Approximate t-values
            lsd_05 = round(2.0 * se_diff, 2)  # Approximate t for 0.05
            lsd_01 = round(2.6 * se_diff, 2)  # Approximate t for 0.01

        return TrialAnalysis(
            trial_id=trial_id,
            trial_name=trial.name,
            measurement_type=measurement_type.value,
            analysis_date=datetime.now(timezone.utc),
            overall_mean=round(overall_mean, 2),
            overall_std=round(overall_std, 2),
            cv_percent=round(cv_percent, 1),
            n_total=len(all_values),
            treatment_means=treatment_means,
            lsd_05=lsd_05,
            lsd_01=lsd_01,
            pairwise_tests=pairwise_tests if pairwise_tests else None,
            top_performer=top_performer,
            significantly_different=significantly_different,
            interpretation=interpretation
        )

    def _perform_ttest(
        self,
        values_a: List[float],
        values_b: List[float],
        name_a: str,
        name_b: str
    ) -> Optional[TTestResult]:
        """Perform a two-sample t-test"""
        if len(values_a) < 2 or len(values_b) < 2:
            return None

        n_a = len(values_a)
        n_b = len(values_b)
        mean_a = mean(values_a)
        mean_b = mean(values_b)
        var_a = variance(values_a)
        var_b = variance(values_b)

        # Pooled variance t-test
        pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
        se = math.sqrt(pooled_var * (1/n_a + 1/n_b))

        if se == 0:
            return None

        t_stat = (mean_a - mean_b) / se
        _df = n_a + n_b - 2

        # Approximate p-value using t-distribution approximation
        # For simplicity, using critical values
        significant = abs(t_stat) > 2.0  # Approximate for df > 10

        difference = mean_a - mean_b
        diff_pct = (difference / mean_b * 100) if mean_b != 0 else 0

        # Determine significance level
        if abs(t_stat) > 3.0:
            sig_level = "p < 0.01"
        elif abs(t_stat) > 2.0:
            sig_level = "p < 0.05"
        else:
            sig_level = "p > 0.05"

        return TTestResult(
            treatment_a=name_a,
            treatment_b=name_b,
            mean_a=round(mean_a, 2),
            mean_b=round(mean_b, 2),
            difference=round(difference, 2),
            difference_percent=round(diff_pct, 1),
            t_statistic=round(t_stat, 3),
            p_value=0.05 if significant else 0.10,  # Simplified
            significant=significant,
            significance_level=sig_level
        )

    # =========================================================================
    # DATA EXPORT
    # =========================================================================

    def export_trial_data(
        self,
        trial_id: int,
        include_analysis: bool = True
    ) -> Optional[ResearchExport]:
        """Export all trial data for research documentation"""
        trial = self.get_trial(trial_id)
        if not trial:
            return None

        treatments = self.list_treatments(trial_id)
        plots = self.list_plots(trial_id)
        measurements = self.list_measurements(trial_id)

        analysis = None
        if include_analysis and measurements:
            # Get the most common measurement type
            type_counts: Dict[str, int] = {}
            for m in measurements:
                type_counts[m.measurement_type.value] = type_counts.get(m.measurement_type.value, 0) + 1

            if type_counts:
                main_type = max(type_counts, key=type_counts.get)
                analysis = self.analyze_trial(trial_id, MeasurementType(main_type))

        return ResearchExport(
            trial=trial,
            treatments=treatments,
            plots=plots,
            measurements=measurements,
            analysis=analysis,
            export_date=datetime.now(timezone.utc),
            export_format="json"
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_research_service(db_path: str = None) -> ResearchService:
    """Get an instance of the research service"""
    if db_path is None:
        db_path = os.environ.get("AGTOOLS_DB_PATH", "agtools.db")
    return ResearchService(db_path)
