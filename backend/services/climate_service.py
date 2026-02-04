"""
Climate and Weather Data Service for AgTools

Provides comprehensive weather data integration, Growing Degree Days (GDD) tracking,
precipitation monitoring, and climate trend analysis for agricultural research.

Features:
- Real-time weather data from Open-Meteo API (free, no key required)
- Growing Degree Days (GDD) calculation and tracking
- Precipitation logging and accumulation
- Weather-based alerts and recommendations
- Historical climate data and trend analysis
- Frost/freeze risk assessment
- Heat stress monitoring
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import sqlite3
import os

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# =============================================================================
# ENUMS
# =============================================================================

class WeatherAlertType(str, Enum):
    """Types of weather alerts"""
    FROST_WARNING = "frost_warning"
    FREEZE_WARNING = "freeze_warning"
    HEAT_STRESS = "heat_stress"
    DROUGHT = "drought"
    EXCESSIVE_RAIN = "excessive_rain"
    HIGH_WIND = "high_wind"
    HAIL_RISK = "hail_risk"
    SPRAY_WINDOW = "spray_window"


class PrecipitationType(str, Enum):
    """Types of precipitation"""
    RAIN = "rain"
    SNOW = "snow"
    SLEET = "sleet"
    HAIL = "hail"
    MIXED = "mixed"


# =============================================================================
# GDD BASE TEMPERATURES (°F)
# =============================================================================

GDD_BASE_TEMPS = {
    "corn": 50,
    "soybean": 50,
    "wheat": 40,
    "cotton": 60,
    "sorghum": 50,
    "alfalfa": 41,
    "sunflower": 44,
    "canola": 41,
}

# GDD thresholds for crop stages
CORN_GDD_STAGES = {
    "emergence": 125,
    "v2": 200,
    "v4": 345,
    "v6": 475,
    "v8": 610,
    "v10": 740,
    "v12": 870,
    "vt_tassel": 1135,
    "r1_silking": 1200,
    "r2_blister": 1350,
    "r3_milk": 1500,
    "r4_dough": 1700,
    "r5_dent": 1925,
    "r6_maturity": 2450,
}

SOYBEAN_GDD_STAGES = {
    "emergence": 130,
    "v1": 215,
    "v3": 365,
    "v5": 520,
    "r1_bloom": 710,
    "r3_pod": 890,
    "r5_seed": 1100,
    "r7_maturity": 1550,
    "r8_harvest": 1800,
}


# =============================================================================
# PYDANTIC MODELS - Weather Data
# =============================================================================

class CurrentWeather(BaseModel):
    """Current weather conditions"""
    temperature_f: float
    feels_like_f: float
    humidity_percent: float
    wind_speed_mph: float
    wind_direction: str
    wind_gust_mph: Optional[float] = None
    pressure_mb: float
    cloud_cover_percent: float
    dew_point_f: float
    conditions: str
    last_updated: datetime


class DailyForecast(BaseModel):
    """Daily weather forecast"""
    date: date
    high_f: float
    low_f: float
    avg_temp_f: float
    precipitation_inches: float
    precipitation_probability: float
    humidity_percent: float
    wind_speed_mph: float
    conditions: str
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    uv_index: float
    gdd_corn: float
    gdd_soybean: float


class HourlyForecast(BaseModel):
    """Hourly weather forecast"""
    datetime: datetime
    temperature_f: float
    feels_like_f: float
    humidity_percent: float
    wind_speed_mph: float
    wind_gust_mph: Optional[float] = None
    precipitation_inches: float
    precipitation_probability: float
    conditions: str


class WeatherForecast(BaseModel):
    """Complete weather forecast"""
    location: str
    latitude: float
    longitude: float
    timezone: str
    current: CurrentWeather
    daily: List[DailyForecast]
    hourly: List[HourlyForecast]
    fetched_at: datetime


# =============================================================================
# PYDANTIC MODELS - GDD Tracking
# =============================================================================

class GDDEntry(BaseModel):
    """Single day GDD entry"""
    date: date
    high_f: float
    low_f: float
    gdd_corn: float
    gdd_soybean: float
    gdd_wheat: float
    cumulative_corn: float
    cumulative_soybean: float
    cumulative_wheat: float


class GDDSummary(BaseModel):
    """GDD summary for a field/location"""
    field_id: Optional[int] = None
    field_name: Optional[str] = None
    crop_type: str
    planting_date: date
    current_date: date
    accumulated_gdd: float
    current_stage: str
    next_stage: str
    gdd_to_next_stage: float
    days_to_next_stage_estimate: int
    percent_to_maturity: float
    projected_maturity_date: Optional[date] = None


class GDDRecordCreate(BaseModel):
    """Create a GDD record"""
    field_id: int
    record_date: date
    high_temp_f: float
    low_temp_f: float
    source: str = "manual"


class GDDRecordResponse(BaseModel):
    """Response for GDD record"""
    id: int
    field_id: int
    field_name: Optional[str] = None
    record_date: date
    high_temp_f: float
    low_temp_f: float
    gdd_corn: float
    gdd_soybean: float
    gdd_wheat: float
    source: str
    created_at: datetime


# =============================================================================
# PYDANTIC MODELS - Precipitation
# =============================================================================

class PrecipitationCreate(BaseModel):
    """Record precipitation"""
    field_id: int
    record_date: date
    amount_inches: float = Field(..., ge=0)
    precip_type: PrecipitationType = PrecipitationType.RAIN
    duration_hours: Optional[float] = Field(None, ge=0)
    intensity: Optional[str] = None
    source: str = "manual"
    notes: Optional[str] = None


class PrecipitationResponse(BaseModel):
    """Response for precipitation record"""
    id: int
    field_id: int
    field_name: Optional[str] = None
    record_date: date
    amount_inches: float
    precip_type: PrecipitationType
    duration_hours: Optional[float]
    intensity: Optional[str]
    source: str
    notes: Optional[str]
    created_at: datetime


class PrecipitationSummary(BaseModel):
    """Precipitation summary for a period"""
    field_id: Optional[int] = None
    period_start: date
    period_end: date
    total_inches: float
    rain_days: int
    avg_per_rain_day: float
    max_single_day: float
    max_date: Optional[date] = None
    by_month: Dict[str, float]


# =============================================================================
# PYDANTIC MODELS - Weather Alerts
# =============================================================================

class WeatherAlert(BaseModel):
    """Weather alert for agricultural operations"""
    alert_type: WeatherAlertType
    severity: str
    title: str
    message: str
    affected_fields: List[int]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recommendations: List[str]
    created_at: datetime


class SprayWindow(BaseModel):
    """Optimal spray window based on weather"""
    start_time: datetime
    end_time: datetime
    duration_hours: float
    quality: str
    temperature_f: float
    humidity_percent: float
    wind_speed_mph: float
    precipitation_risk: float
    notes: List[str]


# =============================================================================
# PYDANTIC MODELS - Climate Analysis
# =============================================================================

class ClimateSummary(BaseModel):
    """Climate summary for research"""
    location: str
    year: int
    avg_high_f: float
    avg_low_f: float
    record_high_f: float
    record_high_date: Optional[date] = None
    record_low_f: float
    record_low_date: Optional[date] = None
    days_above_90: int
    days_above_100: int
    days_below_32: int
    days_below_0: int
    first_frost_date: Optional[date] = None
    last_frost_date: Optional[date] = None
    frost_free_days: int
    total_precipitation_inches: float
    rain_days: int
    snow_inches: Optional[float] = None
    max_single_day_precip: float
    total_gdd_corn: float
    total_gdd_soybean: float
    growing_season_start: Optional[date] = None
    growing_season_end: Optional[date] = None


class ClimateComparison(BaseModel):
    """Compare climate between years"""
    location: str
    years: List[int]
    metrics: Dict[str, Dict[int, float]]
    trends: Dict[str, str]


# =============================================================================
# CLIMATE SERVICE CLASS
# =============================================================================

class ClimateService:
    """
    Service for weather data, GDD tracking, and climate analysis.

    Uses Open-Meteo API for weather data (free, no API key required).
    Supports research documentation with comprehensive climate metrics.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize climate tracking tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # GDD records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS climate_gdd (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                record_date DATE NOT NULL,
                high_temp_f REAL NOT NULL,
                low_temp_f REAL NOT NULL,
                gdd_corn REAL,
                gdd_soybean REAL,
                gdd_wheat REAL,
                source VARCHAR(50) DEFAULT 'manual',
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(field_id, record_date),
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Precipitation records
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS climate_precipitation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_id INTEGER NOT NULL,
                record_date DATE NOT NULL,
                amount_inches REAL NOT NULL,
                precip_type VARCHAR(20) DEFAULT 'rain',
                duration_hours REAL,
                intensity VARCHAR(20),
                source VARCHAR(50) DEFAULT 'manual',
                notes TEXT,
                created_by_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (field_id) REFERENCES fields(id)
            )
        """)

        # Weather observations cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS climate_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                observation_date DATE NOT NULL,
                high_temp_f REAL,
                low_temp_f REAL,
                avg_temp_f REAL,
                precipitation_inches REAL,
                humidity_percent REAL,
                wind_speed_mph REAL,
                conditions TEXT,
                raw_data TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(latitude, longitude, observation_date)
            )
        """)

        # Location settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS climate_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timezone VARCHAR(50),
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_climate_gdd_field_date ON climate_gdd(field_id, record_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_climate_precip_field_date ON climate_precipitation(field_id, record_date)")

        conn.commit()
        conn.close()

    # =========================================================================
    # GDD CALCULATIONS
    # =========================================================================

    def _calculate_gdd(self, high: float, low: float, base: float) -> float:
        """
        Calculate Growing Degree Days using the standard method.
        GDD = ((High + Low) / 2) - Base
        Uses 86°F ceiling for corn.
        """
        high_adj = min(high, 86)
        low_adj = max(low, base)
        avg = (high_adj + low_adj) / 2
        gdd = max(0, avg - base)
        return round(gdd, 1)

    def record_gdd(
        self,
        data: GDDRecordCreate,
        user_id: int
    ) -> Tuple[Optional[GDDRecordResponse], Optional[str]]:
        """Record daily temperature for GDD tracking"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            gdd_corn = self._calculate_gdd(data.high_temp_f, data.low_temp_f, GDD_BASE_TEMPS["corn"])
            gdd_soybean = self._calculate_gdd(data.high_temp_f, data.low_temp_f, GDD_BASE_TEMPS["soybean"])
            gdd_wheat = self._calculate_gdd(data.high_temp_f, data.low_temp_f, GDD_BASE_TEMPS["wheat"])

            cursor.execute("""
                INSERT OR REPLACE INTO climate_gdd
                (field_id, record_date, high_temp_f, low_temp_f,
                 gdd_corn, gdd_soybean, gdd_wheat, source, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.record_date.isoformat(),
                data.high_temp_f, data.low_temp_f,
                gdd_corn, gdd_soybean, gdd_wheat,
                data.source, user_id
            ))

            gdd_id = cursor.lastrowid
            conn.commit()

            result = self.get_gdd_record(gdd_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_gdd_record(self, record_id: int) -> Optional[GDDRecordResponse]:
        """Get a single GDD record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT g.*, f.name as field_name
            FROM climate_gdd g
            LEFT JOIN fields f ON g.field_id = f.id
            WHERE g.id = ?
        """, (record_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return GDDRecordResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            record_date=date.fromisoformat(row["record_date"]),
            high_temp_f=row["high_temp_f"],
            low_temp_f=row["low_temp_f"],
            gdd_corn=row["gdd_corn"],
            gdd_soybean=row["gdd_soybean"],
            gdd_wheat=row["gdd_wheat"],
            source=row["source"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def list_gdd_records(
        self,
        field_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[GDDRecordResponse]:
        """List GDD records for a field"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT g.*, f.name as field_name
            FROM climate_gdd g
            LEFT JOIN fields f ON g.field_id = f.id
            WHERE g.field_id = ?
        """
        params = [field_id]

        if start_date:
            query += " AND g.record_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND g.record_date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY g.record_date"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            GDDRecordResponse(
                id=row["id"],
                field_id=row["field_id"],
                field_name=row["field_name"] if "field_name" in row.keys() else None,
                record_date=date.fromisoformat(row["record_date"]),
                high_temp_f=row["high_temp_f"],
                low_temp_f=row["low_temp_f"],
                gdd_corn=row["gdd_corn"],
                gdd_soybean=row["gdd_soybean"],
                gdd_wheat=row["gdd_wheat"],
                source=row["source"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            )
            for row in rows
        ]

    def get_accumulated_gdd(
        self,
        field_id: int,
        crop_type: str,
        start_date: date,
        end_date: Optional[date] = None
    ) -> Tuple[float, List[GDDEntry]]:
        """Get accumulated GDD from planting date"""
        if end_date is None:
            end_date = date.today()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT record_date, high_temp_f, low_temp_f,
                   gdd_corn, gdd_soybean, gdd_wheat
            FROM climate_gdd
            WHERE field_id = ?
            AND record_date >= ?
            AND record_date <= ?
            ORDER BY record_date
        """, (field_id, start_date.isoformat(), end_date.isoformat()))

        rows = cursor.fetchall()
        conn.close()

        entries = []
        cumulative_corn = 0
        cumulative_soybean = 0
        cumulative_wheat = 0

        for row in rows:
            cumulative_corn += row["gdd_corn"] or 0
            cumulative_soybean += row["gdd_soybean"] or 0
            cumulative_wheat += row["gdd_wheat"] or 0

            entries.append(GDDEntry(
                date=date.fromisoformat(row["record_date"]),
                high_f=row["high_temp_f"],
                low_f=row["low_temp_f"],
                gdd_corn=row["gdd_corn"] or 0,
                gdd_soybean=row["gdd_soybean"] or 0,
                gdd_wheat=row["gdd_wheat"] or 0,
                cumulative_corn=cumulative_corn,
                cumulative_soybean=cumulative_soybean,
                cumulative_wheat=cumulative_wheat
            ))

        crop_gdd = {
            "corn": cumulative_corn,
            "soybean": cumulative_soybean,
            "wheat": cumulative_wheat
        }

        return crop_gdd.get(crop_type.lower(), cumulative_corn), entries

    def get_gdd_summary(
        self,
        field_id: int,
        crop_type: str,
        planting_date: date
    ) -> GDDSummary:
        """Get GDD summary with crop stage predictions"""
        accumulated, entries = self.get_accumulated_gdd(field_id, crop_type, planting_date)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM fields WHERE id = ?", (field_id,))
        row = cursor.fetchone()
        field_name = row["name"] if row else None
        conn.close()

        stages = CORN_GDD_STAGES if crop_type.lower() == "corn" else SOYBEAN_GDD_STAGES

        current_stage = "pre-emergence"
        next_stage = "emergence"
        gdd_to_next = 0

        sorted_stages = sorted(stages.items(), key=lambda x: x[1])

        for i, (stage_name, stage_gdd) in enumerate(sorted_stages):
            if accumulated >= stage_gdd:
                current_stage = stage_name
                if i + 1 < len(sorted_stages):
                    next_stage = sorted_stages[i + 1][0]
                    gdd_to_next = sorted_stages[i + 1][1] - accumulated
                else:
                    next_stage = "mature"
                    gdd_to_next = 0
            else:
                next_stage = stage_name
                gdd_to_next = stage_gdd - accumulated
                break

        avg_gdd_per_day = 15
        if entries:
            recent_entries = entries[-14:] if len(entries) >= 14 else entries
            total_gdd = sum(e.gdd_corn if crop_type.lower() == "corn" else e.gdd_soybean for e in recent_entries)
            avg_gdd_per_day = total_gdd / len(recent_entries) if recent_entries else 15

        days_to_next = int(gdd_to_next / avg_gdd_per_day) if avg_gdd_per_day > 0 else 0

        maturity_gdd = sorted_stages[-1][1]
        percent_to_maturity = min(100, (accumulated / maturity_gdd) * 100)

        gdd_remaining = maturity_gdd - accumulated
        days_to_maturity = int(gdd_remaining / avg_gdd_per_day) if avg_gdd_per_day > 0 else 0
        projected_maturity = date.today() + timedelta(days=days_to_maturity) if days_to_maturity > 0 else None

        return GDDSummary(
            field_id=field_id,
            field_name=field_name,
            crop_type=crop_type,
            planting_date=planting_date,
            current_date=date.today(),
            accumulated_gdd=accumulated,
            current_stage=current_stage.replace("_", " ").title(),
            next_stage=next_stage.replace("_", " ").title(),
            gdd_to_next_stage=max(0, gdd_to_next),
            days_to_next_stage_estimate=max(0, days_to_next),
            percent_to_maturity=round(percent_to_maturity, 1),
            projected_maturity_date=projected_maturity
        )

    # =========================================================================
    # PRECIPITATION TRACKING
    # =========================================================================

    def record_precipitation(
        self,
        data: PrecipitationCreate,
        user_id: int
    ) -> Tuple[Optional[PrecipitationResponse], Optional[str]]:
        """Record precipitation event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO climate_precipitation
                (field_id, record_date, amount_inches, precip_type,
                 duration_hours, intensity, source, notes, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.field_id, data.record_date.isoformat(),
                data.amount_inches, data.precip_type.value,
                data.duration_hours, data.intensity,
                data.source, data.notes, user_id
            ))

            precip_id = cursor.lastrowid
            conn.commit()

            result = self.get_precipitation_record(precip_id)
            conn.close()

            return result, None

        except Exception as e:
            return None, str(e)

    def get_precipitation_record(self, record_id: int) -> Optional[PrecipitationResponse]:
        """Get a single precipitation record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, f.name as field_name
            FROM climate_precipitation p
            LEFT JOIN fields f ON p.field_id = f.id
            WHERE p.id = ?
        """, (record_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return PrecipitationResponse(
            id=row["id"],
            field_id=row["field_id"],
            field_name=row["field_name"] if "field_name" in row.keys() else None,
            record_date=date.fromisoformat(row["record_date"]),
            amount_inches=row["amount_inches"],
            precip_type=PrecipitationType(row["precip_type"]),
            duration_hours=row["duration_hours"],
            intensity=row["intensity"],
            source=row["source"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        )

    def list_precipitation(
        self,
        field_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[PrecipitationResponse]:
        """List precipitation records with filters"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT p.*, f.name as field_name
            FROM climate_precipitation p
            LEFT JOIN fields f ON p.field_id = f.id
            WHERE 1=1
        """
        params = []

        if field_id:
            query += " AND p.field_id = ?"
            params.append(field_id)

        if start_date:
            query += " AND p.record_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND p.record_date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY p.record_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            PrecipitationResponse(
                id=row["id"],
                field_id=row["field_id"],
                field_name=row["field_name"] if "field_name" in row.keys() else None,
                record_date=date.fromisoformat(row["record_date"]),
                amount_inches=row["amount_inches"],
                precip_type=PrecipitationType(row["precip_type"]),
                duration_hours=row["duration_hours"],
                intensity=row["intensity"],
                source=row["source"],
                notes=row["notes"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            )
            for row in rows
        ]

    def get_precipitation_summary(
        self,
        start_date: date,
        end_date: date,
        field_id: Optional[int] = None
    ) -> PrecipitationSummary:
        """Get precipitation summary for a period"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                record_date,
                SUM(amount_inches) as daily_total
            FROM climate_precipitation
            WHERE record_date >= ? AND record_date <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if field_id:
            query += " AND field_id = ?"
            params.append(field_id)

        query += " GROUP BY record_date ORDER BY record_date"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return PrecipitationSummary(
                field_id=field_id,
                period_start=start_date,
                period_end=end_date,
                total_inches=0,
                rain_days=0,
                avg_per_rain_day=0,
                max_single_day=0,
                by_month={}
            )

        total_inches = sum(row["daily_total"] for row in rows)
        rain_days = len(rows)
        max_day = max(rows, key=lambda x: x["daily_total"])

        by_month = {}
        for row in rows:
            d = date.fromisoformat(row["record_date"])
            month_key = d.strftime("%Y-%m")
            by_month[month_key] = by_month.get(month_key, 0) + row["daily_total"]

        return PrecipitationSummary(
            field_id=field_id,
            period_start=start_date,
            period_end=end_date,
            total_inches=round(total_inches, 2),
            rain_days=rain_days,
            avg_per_rain_day=round(total_inches / rain_days, 2) if rain_days > 0 else 0,
            max_single_day=round(max_day["daily_total"], 2),
            max_date=date.fromisoformat(max_day["record_date"]),
            by_month=by_month
        )

    # =========================================================================
    # CLIMATE ANALYSIS
    # =========================================================================

    def get_climate_summary(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> ClimateSummary:
        """Get annual climate summary"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        query = """
            SELECT
                record_date,
                high_temp_f,
                low_temp_f,
                gdd_corn,
                gdd_soybean
            FROM climate_gdd
            WHERE record_date >= ? AND record_date <= ?
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if field_id:
            query += " AND field_id = ?"
            params.append(field_id)

        query += " ORDER BY record_date"

        cursor.execute(query, params)
        temp_rows = cursor.fetchall()

        precip_summary = self.get_precipitation_summary(start_date, end_date, field_id)

        conn.close()

        if not temp_rows:
            return ClimateSummary(
                location="Field" if field_id else "Farm",
                year=year,
                avg_high_f=0, avg_low_f=0,
                record_high_f=0, record_low_f=0,
                days_above_90=0, days_above_100=0,
                days_below_32=0, days_below_0=0,
                frost_free_days=0,
                total_precipitation_inches=precip_summary.total_inches,
                rain_days=precip_summary.rain_days,
                max_single_day_precip=precip_summary.max_single_day,
                total_gdd_corn=0,
                total_gdd_soybean=0
            )

        highs = [row["high_temp_f"] for row in temp_rows]
        lows = [row["low_temp_f"] for row in temp_rows]

        record_high = max(highs)
        record_low = min(lows)
        record_high_date = None
        record_low_date = None

        for row in temp_rows:
            if row["high_temp_f"] == record_high and not record_high_date:
                record_high_date = date.fromisoformat(row["record_date"])
            if row["low_temp_f"] == record_low and not record_low_date:
                record_low_date = date.fromisoformat(row["record_date"])

        days_above_90 = sum(1 for h in highs if h >= 90)
        days_above_100 = sum(1 for h in highs if h >= 100)
        days_below_32 = sum(1 for low in lows if low <= 32)
        days_below_0 = sum(1 for low in lows if low <= 0)

        first_frost = None
        last_frost = None
        for row in temp_rows:
            d = date.fromisoformat(row["record_date"])
            if row["low_temp_f"] <= 32:
                if d.month >= 7:
                    if first_frost is None:
                        first_frost = d
                else:
                    last_frost = d

        frost_free_days = 0
        if first_frost and last_frost:
            frost_free_days = (first_frost - last_frost).days

        total_gdd_corn = sum(row["gdd_corn"] or 0 for row in temp_rows)
        total_gdd_soybean = sum(row["gdd_soybean"] or 0 for row in temp_rows)

        return ClimateSummary(
            location="Field" if field_id else "Farm",
            year=year,
            avg_high_f=round(sum(highs) / len(highs), 1),
            avg_low_f=round(sum(lows) / len(lows), 1),
            record_high_f=record_high,
            record_high_date=record_high_date,
            record_low_f=record_low,
            record_low_date=record_low_date,
            days_above_90=days_above_90,
            days_above_100=days_above_100,
            days_below_32=days_below_32,
            days_below_0=days_below_0,
            first_frost_date=first_frost,
            last_frost_date=last_frost,
            frost_free_days=frost_free_days,
            total_precipitation_inches=precip_summary.total_inches,
            rain_days=precip_summary.rain_days,
            max_single_day_precip=precip_summary.max_single_day,
            total_gdd_corn=round(total_gdd_corn, 1),
            total_gdd_soybean=round(total_gdd_soybean, 1)
        )

    def compare_years(
        self,
        years: List[int],
        field_id: Optional[int] = None
    ) -> ClimateComparison:
        """Compare climate data across multiple years"""
        metrics = {
            "avg_high": {},
            "avg_low": {},
            "total_precipitation": {},
            "gdd_corn": {},
            "gdd_soybean": {},
            "days_above_90": {},
            "frost_free_days": {}
        }

        for year in years:
            summary = self.get_climate_summary(year, field_id)
            metrics["avg_high"][year] = summary.avg_high_f
            metrics["avg_low"][year] = summary.avg_low_f
            metrics["total_precipitation"][year] = summary.total_precipitation_inches
            metrics["gdd_corn"][year] = summary.total_gdd_corn
            metrics["gdd_soybean"][year] = summary.total_gdd_soybean
            metrics["days_above_90"][year] = summary.days_above_90
            metrics["frost_free_days"][year] = summary.frost_free_days

        trends = {}
        for metric, values in metrics.items():
            if len(values) >= 2:
                sorted_years = sorted(values.keys())
                first = values[sorted_years[0]]
                last = values[sorted_years[-1]]
                if first > 0:
                    change_pct = ((last - first) / first) * 100
                    if change_pct > 5:
                        trends[metric] = "increasing"
                    elif change_pct < -5:
                        trends[metric] = "decreasing"
                    else:
                        trends[metric] = "stable"
                else:
                    trends[metric] = "stable"

        return ClimateComparison(
            location="Field" if field_id else "Farm",
            years=years,
            metrics=metrics,
            trends=trends
        )

    def export_climate_data(
        self,
        year: int,
        field_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export climate data for research"""
        climate_summary = self.get_climate_summary(year, field_id)

        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        gdd_records = []
        if field_id:
            gdd_records = self.list_gdd_records(field_id, start_date, end_date)

        precip_records = self.list_precipitation(field_id, start_date, end_date)

        return {
            "metadata": {
                "export_date": datetime.now(timezone.utc).isoformat(),
                "year": year,
                "field_id": field_id,
                "software": "AgTools Climate Module",
                "version": "1.0.0"
            },
            "climate_summary": climate_summary.model_dump(),
            "gdd_records": [r.model_dump() for r in gdd_records],
            "precipitation_records": [r.model_dump() for r in precip_records]
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_climate_service(db_path: str = None) -> ClimateService:
    """Get an instance of the climate service"""
    if db_path is None:
        db_path = os.environ.get("AGTOOLS_DB_PATH", "agtools.db")
    return ClimateService(db_path)
