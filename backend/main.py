"""
Professional Crop Consulting System - FastAPI Backend
Main application entry point with Input Cost Optimization
Version 2.2.0 - Added Yield Response & Economic Optimum Rate Calculator
"""

import sys
import os

# Add parent directory to path so we can import from database/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum
import uvicorn

# Auth imports
from middleware.auth_middleware import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_manager,
    AuthenticatedUser,
    get_client_ip,
    get_user_agent
)
from services.auth_service import (
    UserRole,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    LoginRequest,
    PasswordChange
)
from services.user_service import (
    get_user_service,
    CrewCreate,
    CrewUpdate,
    CrewResponse,
    CrewMemberResponse
)
from services.task_service import (
    get_task_service,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    StatusChangeRequest
)
from services.field_service import (
    get_field_service,
    FieldCreate,
    FieldUpdate,
    FieldResponse,
    FieldSummary,
    CropType as FieldCropType,
    SoilType,
    IrrigationType as FieldIrrigationType
)
from services.field_operations_service import (
    get_field_operations_service,
    OperationCreate,
    OperationUpdate,
    OperationResponse,
    OperationsSummary,
    FieldOperationHistory,
    OperationType
)

# Initialize FastAPI app
app = FastAPI(
    title="AgTools Professional Crop Consulting API",
    description="Professional-grade crop consulting system with pest/disease management, input cost optimization, dynamic pricing, weather-smart spray timing, and yield response economics",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS (Data Validation)
# ============================================================================

class CropType(str, Enum):
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"

class ProblemType(str, Enum):
    PEST = "pest"
    DISEASE = "disease"
    NUTRIENT = "nutrient_deficiency"
    WEED = "weed"

class GrowthStage(str, Enum):
    # Corn
    VE = "VE"
    V1 = "V1"
    V3 = "V3"
    V6 = "V6"
    VT = "VT"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"
    # Soybeans use same R stages, different V stages
    VC = "VC"
    V2 = "V2"
    V4 = "V4"

class IdentificationMethod(str, Enum):
    AI_IMAGE = "ai_image"
    GUIDED = "guided"
    MANUAL = "manual"

class RecommendedAction(str, Enum):
    SPRAY = "spray"
    SCOUT_AGAIN = "scout_again"
    NO_ACTION = "no_action"
    CONSULT_SPECIALIST = "consult_specialist"

# Request Models
class FieldInfo(BaseModel):
    field_name: str
    farm_name: Optional[str] = None
    acres: Optional[float] = None
    crop: CropType
    growth_stage: GrowthStage
    planting_date: Optional[date] = None
    previous_crop: Optional[str] = None

class PestIdentificationRequest(BaseModel):
    crop: CropType
    growth_stage: GrowthStage
    symptoms: List[str]
    location_description: Optional[str] = None
    severity_rating: Optional[int] = Field(None, ge=1, le=10)
    field_conditions: Optional[Dict[str, Any]] = None

class DiseaseIdentificationRequest(BaseModel):
    crop: CropType
    growth_stage: GrowthStage
    symptoms: List[str]
    weather_conditions: Optional[str] = None
    location_description: Optional[str] = None
    severity_rating: Optional[int] = Field(None, ge=1, le=10)

class SprayRecommendationRequest(BaseModel):
    crop: CropType
    growth_stage: GrowthStage
    problem_type: ProblemType
    problem_id: int  # pest_id or disease_id
    severity: int = Field(..., ge=1, le=10)
    field_acres: float
    previous_applications: Optional[List[str]] = None
    temperature_forecast: Optional[List[float]] = None
    rain_forecast_inches: Optional[List[float]] = None

class EconomicThresholdRequest(BaseModel):
    crop: CropType
    pest_name: str
    population_count: float
    growth_stage: GrowthStage
    control_cost_per_acre: float
    expected_yield: float
    grain_price: float

# Response Models
class PestInfo(BaseModel):
    id: int
    common_name: str
    scientific_name: str
    confidence: Optional[float] = None
    description: str
    damage_symptoms: str
    identification_features: str
    economic_threshold: Optional[str] = None

class DiseaseInfo(BaseModel):
    id: int
    common_name: str
    scientific_name: str
    confidence: Optional[float] = None
    description: str
    symptoms: str
    favorable_conditions: str
    management: Optional[str] = None

class ProductRecommendation(BaseModel):
    product_name: str
    active_ingredient: str
    rate: str
    cost_per_acre: float
    efficacy_rating: int = Field(..., ge=1, le=10)
    application_timing: str
    restrictions: Optional[str] = None
    phi_days: int
    rei_hours: int
    resistance_management_notes: Optional[str] = None

class SprayRecommendation(BaseModel):
    recommended_action: RecommendedAction
    primary_product: Optional[ProductRecommendation] = None
    alternative_products: List[ProductRecommendation] = []
    tank_mix_partners: List[str] = []
    adjuvant_recommendations: List[str] = []
    spray_timing_window: str
    weather_requirements: str
    application_notes: str
    economic_analysis: Dict[str, float]

class EconomicThresholdResult(BaseModel):
    threshold_exceeded: bool
    current_population: float
    threshold_value: float
    threshold_unit: str
    estimated_yield_loss_bushels: float
    estimated_revenue_loss: float
    estimated_control_cost: float
    net_benefit_of_treatment: float
    recommendation: str


# ============================================================================
# INPUT COST OPTIMIZATION MODELS
# ============================================================================

class IrrigationType(str, Enum):
    CENTER_PIVOT = "center_pivot"
    LINEAR_MOVE = "linear_move"
    DRIP = "drip"
    SUBSURFACE_DRIP = "subsurface_drip"
    FURROW = "furrow"

class WaterSource(str, Enum):
    GROUNDWATER_WELL = "groundwater_well"
    SURFACE_WATER = "surface_water"
    MUNICIPAL = "municipal"

class OptimizationPriority(str, Enum):
    COST_REDUCTION = "cost_reduction"
    ROI_MAXIMIZATION = "roi_maximization"
    SUSTAINABILITY = "sustainability"
    RISK_REDUCTION = "risk_reduction"

# Request Models for Cost Optimization
class FieldDefinition(BaseModel):
    name: str
    acres: float
    crop: Optional[CropType] = None

class LaborCostRequest(BaseModel):
    fields: List[FieldDefinition]
    scouting_frequency_days: int = Field(default=7, ge=3, le=21)
    season_length_days: int = Field(default=120, ge=60, le=180)
    custom_labor_rates: Optional[Dict[str, float]] = None

class ApplicationLaborRequest(BaseModel):
    acres: float
    application_type: str = "spray"
    equipment_type: str = "self_propelled_120ft"
    tank_capacity_gallons: float = 1200
    application_rate_gpa: float = 15
    custom_application: bool = False
    custom_rate_per_acre: float = 7.50

class FertilizerOptimizationRequest(BaseModel):
    crop: CropType
    yield_goal: float
    acres: float
    soil_test_p_ppm: float = Field(..., description="Soil test phosphorus in ppm")
    soil_test_k_ppm: float = Field(..., description="Soil test potassium in ppm")
    soil_ph: Optional[float] = Field(default=6.5, ge=4.5, le=8.5)
    organic_matter_percent: Optional[float] = Field(default=3.0, ge=0.5, le=10.0)
    nitrogen_credit_lb_per_acre: float = Field(default=0, ge=0, le=200)

class PesticideComparisonRequest(BaseModel):
    acres: float
    products: List[Dict[str, Any]]
    application_method: str = "foliar_ground"
    include_generics: bool = True

class SprayProgramRequest(BaseModel):
    crop: CropType
    acres: float
    spray_applications: List[Dict[str, Any]]
    include_scouting_cost: bool = True

class IrrigationWaterNeedRequest(BaseModel):
    crop: CropType
    growth_stage: GrowthStage
    reference_et_inches_per_day: float = Field(..., ge=0.05, le=0.50)
    recent_rainfall_inches: float = Field(default=0, ge=0)
    soil_moisture_percent: float = Field(default=50, ge=0, le=100)

class IrrigationCostRequest(BaseModel):
    acres: float
    inches_to_apply: float
    irrigation_type: IrrigationType
    water_source: WaterSource
    pumping_depth_ft: float = Field(default=150, ge=20, le=500)

class IrrigationSeasonRequest(BaseModel):
    crop: CropType
    acres: float
    irrigation_type: IrrigationType
    water_source: WaterSource
    season_start: date
    season_end: date
    expected_rainfall_inches: float = Field(default=15, ge=0)
    soil_water_holding_capacity_inches: float = Field(default=2.0, ge=0.5, le=4.0)
    pumping_depth_ft: float = Field(default=150, ge=20, le=500)

class WaterSavingsAnalysisRequest(BaseModel):
    current_usage_acre_inches: float
    acres: float
    irrigation_type: IrrigationType
    water_source: WaterSource

class CropDefinition(BaseModel):
    crop: CropType
    acres: float
    yield_goal: Optional[float] = None

class CompleteFarmAnalysisRequest(BaseModel):
    total_acres: float
    crops: List[CropDefinition]
    irrigation_type: Optional[IrrigationType] = None
    water_source: Optional[WaterSource] = None
    soil_test_p_ppm: Optional[float] = None
    soil_test_k_ppm: Optional[float] = None
    season_length_days: int = Field(default=120, ge=60, le=180)
    optimization_priority: OptimizationPriority = OptimizationPriority.COST_REDUCTION

class QuickEstimateRequest(BaseModel):
    acres: float
    crop: CropType
    is_irrigated: bool = False
    yield_goal: Optional[float] = None


# ============================================================================
# PRICING SERVICE MODELS (v2.1)
# ============================================================================

class InputCategory(str, Enum):
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    SEED = "seed"
    FUEL = "fuel"
    CUSTOM_APPLICATION = "custom_application"


class Region(str, Enum):
    MIDWEST_CORN_BELT = "midwest_corn_belt"
    NORTHERN_PLAINS = "northern_plains"
    SOUTHERN_PLAINS = "southern_plains"
    DELTA = "delta"
    SOUTHEAST = "southeast"
    PACIFIC_NORTHWEST = "pacific_northwest"
    MOUNTAIN = "mountain"


class SetPriceRequest(BaseModel):
    product_id: str = Field(..., description="Product identifier (e.g., 'urea_46', 'glyphosate_generic')")
    price: float = Field(..., ge=0, description="Quoted price")
    supplier: Optional[str] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class BulkPriceUpdateRequest(BaseModel):
    price_updates: List[Dict[str, Any]]
    supplier: Optional[str] = None


class InputCostCalculationRequest(BaseModel):
    crop: CropType
    acres: float
    yield_goal: float
    inputs: List[Dict[str, Any]] = Field(..., description="List of {product_id, rate_per_acre} or {product_id, total_quantity}")


class BuyRecommendationRequest(BaseModel):
    product_id: str
    quantity_needed: float
    purchase_deadline: Optional[datetime] = None


class SupplierComparisonRequest(BaseModel):
    product_ids: List[str]
    acres: float = 1.0


# ============================================================================
# SPRAY TIMING OPTIMIZER MODELS (v2.1)
# ============================================================================

class SprayTypeEnum(str, Enum):
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FUNGICIDE = "fungicide"
    GROWTH_REGULATOR = "growth_regulator"
    DESICCANT = "desiccant"


class PressureLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class WeatherConditionInput(BaseModel):
    datetime: datetime
    temp_f: float = Field(..., ge=-40, le=130)
    humidity_pct: float = Field(..., ge=0, le=100)
    wind_mph: float = Field(..., ge=0, le=100)
    wind_direction: str = "N"
    precip_chance_pct: float = Field(default=0, ge=0, le=100)
    precip_amount_in: float = Field(default=0, ge=0)
    cloud_cover_pct: float = Field(default=50, ge=0, le=100)
    dew_point_f: float = Field(default=55, ge=-40, le=100)


class EvaluateConditionsRequest(BaseModel):
    weather: WeatherConditionInput
    spray_type: SprayTypeEnum
    product_name: Optional[str] = None


class FindSprayWindowsRequest(BaseModel):
    forecast: List[WeatherConditionInput]
    spray_type: SprayTypeEnum
    min_window_hours: float = Field(default=3.0, ge=1.0, le=12.0)
    product_name: Optional[str] = None


class CostOfWaitingRequest(BaseModel):
    current_conditions: WeatherConditionInput
    forecast: List[WeatherConditionInput]
    spray_type: SprayTypeEnum
    acres: float
    product_cost_per_acre: float
    application_cost_per_acre: float = 8.50
    target_pest_or_disease: Optional[str] = None
    current_pressure: PressureLevel = PressureLevel.MODERATE
    crop: CropType = CropType.CORN
    yield_goal: float = 200
    grain_price: float = 4.50


class DiseasePressureRequest(BaseModel):
    weather_history: List[WeatherConditionInput]
    crop: CropType
    growth_stage: GrowthStage


# ============================================================================
# YIELD RESPONSE OPTIMIZER MODELS (v2.2)
# ============================================================================

class NutrientType(str, Enum):
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"
    POTASSIUM = "potassium"
    SULFUR = "sulfur"


class ResponseModelType(str, Enum):
    QUADRATIC = "quadratic"
    QUADRATIC_PLATEAU = "quadratic_plateau"
    LINEAR_PLATEAU = "linear_plateau"
    MITSCHERLICH = "mitscherlich"
    SQUARE_ROOT = "square_root"


class SoilTestLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class YieldResponseCurveRequest(BaseModel):
    crop: CropType
    nutrient: NutrientType
    min_rate: float = Field(default=0, ge=0, description="Minimum rate lb/acre")
    max_rate: float = Field(default=250, ge=0, description="Maximum rate lb/acre")
    rate_step: float = Field(default=10, ge=1, description="Rate increment")
    soil_test_level: SoilTestLevel = SoilTestLevel.MEDIUM
    previous_crop: Optional[str] = None
    response_model: ResponseModelType = ResponseModelType.QUADRATIC_PLATEAU


class EconomicOptimumRequest(BaseModel):
    crop: CropType
    nutrient: NutrientType
    nutrient_price_per_lb: float = Field(..., ge=0, description="Price per lb of nutrient")
    grain_price_per_bu: float = Field(..., ge=0, description="Grain price $/bu")
    soil_test_level: SoilTestLevel = SoilTestLevel.MEDIUM
    previous_crop: Optional[str] = None
    response_model: ResponseModelType = ResponseModelType.QUADRATIC_PLATEAU
    acres: float = Field(default=1.0, ge=0, description="Field acres for total calculations")


class RateScenarioRequest(BaseModel):
    crop: CropType
    nutrient: NutrientType
    rates: List[float] = Field(..., description="List of rates to compare (lb/acre)")
    nutrient_price_per_lb: float = Field(..., ge=0)
    grain_price_per_bu: float = Field(..., ge=0)
    acres: float = Field(default=1.0, ge=0)
    soil_test_level: SoilTestLevel = SoilTestLevel.MEDIUM


class PriceSensitivityRequest(BaseModel):
    crop: CropType
    nutrient: NutrientType
    base_nutrient_price: float = Field(..., ge=0)
    base_grain_price: float = Field(..., ge=0)
    nutrient_price_range_pct: float = Field(default=30, ge=0, le=100)
    grain_price_range_pct: float = Field(default=30, ge=0, le=100)
    soil_test_level: SoilTestLevel = SoilTestLevel.MEDIUM


class MultiNutrientOptimizationRequest(BaseModel):
    crop: CropType
    acres: float = Field(..., ge=0)
    budget: Optional[float] = Field(default=None, description="Optional budget constraint ($)")
    nutrient_prices: Dict[str, float] = Field(
        default={"nitrogen": 0.55, "phosphorus": 0.65, "potassium": 0.45},
        description="Prices per lb nutrient"
    )
    grain_price: float = Field(..., ge=0)
    soil_test_p_ppm: float = Field(default=25, ge=0)
    soil_test_k_ppm: float = Field(default=150, ge=0)
    previous_crop: Optional[str] = None
    yield_goal: Optional[float] = None


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/")
async def root():
    """API health check and information"""
    return {
        "name": "AgTools Professional Crop Consulting API",
        "version": "1.0.0",
        "status": "operational",
        "description": "Professional-grade pest/disease identification and spray recommendation system"
    }

@app.get("/api/v1/crops")
async def get_crops():
    """Get list of supported crops"""
    return {
        "crops": [
            {"id": 1, "name": "Corn", "scientific_name": "Zea mays"},
            {"id": 2, "name": "Soybean", "scientific_name": "Glycine max"}
        ]
    }

@app.get("/api/v1/pests")
async def get_pests(crop: Optional[CropType] = None):
    """Get list of pests, optionally filtered by crop"""
    # This will query the database - for now returning sample data
    from database.seed_data import CORN_PESTS, SOYBEAN_PESTS

    if crop == CropType.CORN:
        pests = CORN_PESTS
    elif crop == CropType.SOYBEAN:
        pests = SOYBEAN_PESTS
    else:
        pests = CORN_PESTS + SOYBEAN_PESTS

    return {
        "count": len(pests),
        "pests": [
            {
                "id": idx + 1,
                "common_name": p["common_name"],
                "scientific_name": p["scientific_name"],
                "pest_type": p["pest_type"]
            }
            for idx, p in enumerate(pests)
        ]
    }

@app.get("/api/v1/diseases")
async def get_diseases(crop: Optional[CropType] = None):
    """Get list of diseases, optionally filtered by crop"""
    from database.seed_data import CORN_DISEASES, SOYBEAN_DISEASES

    if crop == CropType.CORN:
        diseases = CORN_DISEASES
    elif crop == CropType.SOYBEAN:
        diseases = SOYBEAN_DISEASES
    else:
        diseases = CORN_DISEASES + SOYBEAN_DISEASES

    return {
        "count": len(diseases),
        "diseases": [
            {
                "id": idx + 1,
                "common_name": d["common_name"],
                "scientific_name": d["scientific_name"],
                "pathogen_type": d["pathogen_type"]
            }
            for idx, d in enumerate(diseases)
        ]
    }

@app.post("/api/v1/identify/pest", response_model=List[PestInfo])
async def identify_pest(request: PestIdentificationRequest):
    """
    Identify pest based on symptoms and field conditions
    Uses hybrid approach: symptom matching + AI when image provided
    """
    from services.pest_identification import identify_pest_by_symptoms

    results = identify_pest_by_symptoms(
        crop=request.crop,
        symptoms=request.symptoms,
        growth_stage=request.growth_stage,
        field_conditions=request.field_conditions
    )

    return results

@app.post("/api/v1/identify/disease", response_model=List[DiseaseInfo])
async def identify_disease(request: DiseaseIdentificationRequest):
    """
    Identify disease based on symptoms and conditions
    """
    from services.disease_identification import identify_disease_by_symptoms

    results = identify_disease_by_symptoms(
        crop=request.crop,
        symptoms=request.symptoms,
        growth_stage=request.growth_stage,
        weather_conditions=request.weather_conditions
    )

    return results

@app.post("/api/v1/identify/image")
async def identify_from_image(
    image: UploadFile = File(...),
    crop: CropType = CropType.CORN,
    growth_stage: GrowthStage = GrowthStage.V6
):
    """
    AI-based identification from uploaded image
    Returns top 3 matches with confidence scores
    """
    from services.ai_identification import identify_from_image as ai_identify

    # Save uploaded image
    image_bytes = await image.read()

    results = ai_identify(
        image_bytes=image_bytes,
        crop=crop,
        growth_stage=growth_stage
    )

    return results

@app.post("/api/v1/recommend/spray", response_model=SprayRecommendation)
async def get_spray_recommendation(request: SprayRecommendationRequest):
    """
    Get intelligent spray recommendations based on problem identified
    Includes product selection, timing, resistance management, and economics
    """
    from services.spray_recommender import generate_spray_recommendation

    recommendation = generate_spray_recommendation(
        crop=request.crop,
        growth_stage=request.growth_stage,
        problem_type=request.problem_type,
        problem_id=request.problem_id,
        severity=request.severity,
        field_acres=request.field_acres,
        previous_applications=request.previous_applications,
        weather_forecast={
            "temperature": request.temperature_forecast,
            "rain": request.rain_forecast_inches
        }
    )

    return recommendation

@app.post("/api/v1/threshold/check", response_model=EconomicThresholdResult)
async def check_economic_threshold(request: EconomicThresholdRequest):
    """
    Check if pest population exceeds economic threshold
    Provides detailed economic analysis
    """
    from services.threshold_calculator import calculate_economic_threshold

    result = calculate_economic_threshold(
        crop=request.crop,
        pest_name=request.pest_name,
        population_count=request.population_count,
        growth_stage=request.growth_stage,
        control_cost_per_acre=request.control_cost_per_acre,
        expected_yield=request.expected_yield,
        grain_price=request.grain_price
    )

    return result

@app.get("/api/v1/products")
async def get_products(product_type: Optional[str] = None):
    """Get list of pesticide products"""
    from database.chemical_database import INSECTICIDE_PRODUCTS, FUNGICIDE_PRODUCTS

    if product_type == "insecticide":
        products = INSECTICIDE_PRODUCTS
    elif product_type == "fungicide":
        products = FUNGICIDE_PRODUCTS
    else:
        products = INSECTICIDE_PRODUCTS + FUNGICIDE_PRODUCTS

    return {
        "count": len(products),
        "products": [
            {
                "trade_name": p["trade_name"],
                "manufacturer": p["manufacturer"],
                "type": p["product_type"],
                "active_ingredient": p["active_ingredient"]
            }
            for p in products
        ]
    }

@app.get("/api/v1/weather/spray-window")
async def get_spray_window(
    latitude: float,
    longitude: float,
    days_ahead: int = 5
):
    """
    Get optimal spray windows based on weather forecast
    Considers temperature, wind, rain, and humidity
    """
    from services.weather_service import get_spray_windows

    windows = get_spray_windows(
        latitude=latitude,
        longitude=longitude,
        days_ahead=days_ahead
    )

    return windows

@app.get("/api/v1/growth-stage/estimate")
async def estimate_growth_stage(
    crop: CropType,
    planting_date: date,
    location_lat: float,
    location_lon: float
):
    """
    Estimate current growth stage based on planting date and GDD
    """
    from services.growth_stage_calculator import estimate_growth_stage as calc_stage

    stage = calc_stage(
        crop=crop,
        planting_date=planting_date,
        latitude=location_lat,
        longitude=location_lon
    )

    return stage

# ============================================================================
# SCOUTING AND FIELD MANAGEMENT ENDPOINTS
# ============================================================================

class ScoutingReport(BaseModel):
    field_id: int
    scout_date: date
    crop: CropType
    growth_stage: GrowthStage
    observations: str
    problems_found: List[Dict[str, Any]] = []
    images: List[str] = []
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    weather_at_time: Optional[Dict[str, Any]] = None

@app.post("/api/v1/scouting/report")
async def create_scouting_report(report: ScoutingReport):
    """Create a new field scouting report"""
    # This would save to database
    return {
        "success": True,
        "report_id": 12345,
        "message": "Scouting report created successfully"
    }

@app.get("/api/v1/scouting/reports/{field_id}")
async def get_scouting_reports(field_id: int, limit: int = 10):
    """Get scouting reports for a field"""
    # This would query database
    return {
        "field_id": field_id,
        "reports": []
    }

# ============================================================================
# INPUT COST OPTIMIZATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/optimize/labor/scouting")
async def calculate_scouting_costs(request: LaborCostRequest):
    """
    Calculate and optimize scouting labor costs
    Returns cost breakdown and optimization recommendations
    """
    from services.labor_optimizer import get_labor_optimizer

    optimizer = get_labor_optimizer(request.custom_labor_rates)

    fields = [{"name": f.name, "acres": f.acres} for f in request.fields]

    result = optimizer.calculate_scouting_costs(
        fields=fields,
        scouting_frequency_days=request.scouting_frequency_days,
        season_length_days=request.season_length_days
    )

    return result


@app.post("/api/v1/optimize/labor/application")
async def calculate_application_labor(request: ApplicationLaborRequest):
    """
    Calculate labor costs for spray/fertilizer applications
    Compare self-application vs custom application
    """
    from services.labor_optimizer import get_labor_optimizer

    optimizer = get_labor_optimizer()

    result = optimizer.calculate_application_labor(
        acres=request.acres,
        application_type=request.application_type,
        equipment_type=request.equipment_type,
        tank_capacity_gallons=request.tank_capacity_gallons,
        application_rate_gpa=request.application_rate_gpa,
        custom_application=request.custom_application,
        custom_rate_per_acre=request.custom_rate_per_acre
    )

    return result


@app.post("/api/v1/optimize/labor/seasonal-budget")
async def calculate_seasonal_labor_budget(
    total_acres: float,
    crop: CropType,
    spray_applications: int = 3,
    fertilizer_applications: int = 2,
    scouting_frequency_days: int = 7,
    season_length_days: int = 120
):
    """
    Calculate total seasonal labor budget for all field operations
    """
    from services.labor_optimizer import get_labor_optimizer

    optimizer = get_labor_optimizer()

    result = optimizer.calculate_seasonal_labor_budget(
        total_acres=total_acres,
        crop=crop.value,
        expected_spray_applications=spray_applications,
        expected_fertilizer_applications=fertilizer_applications,
        scouting_frequency_days=scouting_frequency_days,
        season_length_days=season_length_days
    )

    return result


@app.post("/api/v1/optimize/fertilizer")
async def optimize_fertilizer_program(request: FertilizerOptimizationRequest):
    """
    Optimize fertilizer program based on yield goal and soil tests
    Returns most economical nutrient sources and rates
    """
    from services.application_cost_optimizer import get_application_optimizer

    optimizer = get_application_optimizer()

    soil_test = {
        "P": request.soil_test_p_ppm,
        "K": request.soil_test_k_ppm,
        "pH": request.soil_ph,
        "OM": request.organic_matter_percent,
        "n_credit": request.nitrogen_credit_lb_per_acre
    }

    result = optimizer.optimize_fertilizer_program(
        crop=request.crop.value,
        yield_goal=request.yield_goal,
        acres=request.acres,
        soil_test_results=soil_test
    )

    return result


@app.post("/api/v1/optimize/pesticides/compare")
async def compare_pesticide_options(request: PesticideComparisonRequest):
    """
    Compare pesticide options to find most economical choice
    """
    from services.application_cost_optimizer import get_application_optimizer

    optimizer = get_application_optimizer()

    result = optimizer.compare_pesticide_options(
        product_options=request.products,
        acres=request.acres,
        application_method=request.application_method,
        include_generics=request.include_generics
    )

    return result


@app.post("/api/v1/optimize/spray-program")
async def calculate_spray_program_costs(request: SprayProgramRequest):
    """
    Calculate total costs for a complete spray program (season)
    Includes ROI analysis
    """
    from services.application_cost_optimizer import get_application_optimizer

    optimizer = get_application_optimizer()

    result = optimizer.calculate_spray_program_costs(
        crop=request.crop.value,
        acres=request.acres,
        spray_program=request.spray_applications,
        include_scouting=request.include_scouting_cost
    )

    return result


@app.post("/api/v1/optimize/irrigation/water-need")
async def calculate_crop_water_need(request: IrrigationWaterNeedRequest):
    """
    Calculate current crop water need based on growth stage and conditions
    Returns irrigation urgency and recommendations
    """
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.calculate_crop_water_need(
        crop=request.crop.value,
        growth_stage=request.growth_stage.value,
        reference_et=request.reference_et_inches_per_day,
        recent_rainfall_inches=request.recent_rainfall_inches,
        soil_moisture_percent=request.soil_moisture_percent
    )

    return result


@app.post("/api/v1/optimize/irrigation/cost")
async def calculate_irrigation_cost(request: IrrigationCostRequest):
    """
    Calculate total cost of an irrigation event
    Returns detailed cost breakdown
    """
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.calculate_irrigation_costs(
        acres=request.acres,
        inches_to_apply=request.inches_to_apply,
        irrigation_type=request.irrigation_type.value,
        water_source=request.water_source.value,
        pumping_depth_ft=request.pumping_depth_ft
    )

    return result


@app.post("/api/v1/optimize/irrigation/season")
async def optimize_irrigation_season(request: IrrigationSeasonRequest):
    """
    Create optimized irrigation schedule for the entire season
    Returns schedule, costs, and ROI analysis
    """
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.optimize_irrigation_schedule(
        crop=request.crop.value,
        acres=request.acres,
        irrigation_type=request.irrigation_type.value,
        water_source=request.water_source.value,
        season_start=request.season_start,
        season_end=request.season_end,
        expected_rainfall_inches=request.expected_rainfall_inches,
        soil_water_holding_capacity=request.soil_water_holding_capacity_inches,
        pumping_depth_ft=request.pumping_depth_ft
    )

    return result


@app.get("/api/v1/optimize/irrigation/system-comparison")
async def compare_irrigation_systems(
    acres: float,
    annual_water_need_inches: float = 18,
    water_source: WaterSource = WaterSource.GROUNDWATER_WELL,
    current_system: Optional[str] = None
):
    """
    Compare different irrigation systems for cost effectiveness
    """
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.compare_irrigation_systems(
        acres=acres,
        annual_water_need_inches=annual_water_need_inches,
        water_source=water_source.value,
        current_system=current_system
    )

    return result


@app.post("/api/v1/optimize/irrigation/water-savings")
async def analyze_water_savings(request: WaterSavingsAnalysisRequest):
    """
    Analyze strategies to reduce water usage and costs
    Returns prioritized recommendations with savings estimates
    """
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.analyze_water_savings_strategies(
        current_usage_acre_inches=request.current_usage_acre_inches,
        acres=request.acres,
        irrigation_type=request.irrigation_type.value,
        water_source=request.water_source.value
    )

    return result


@app.post("/api/v1/optimize/complete-analysis")
async def complete_farm_cost_analysis(request: CompleteFarmAnalysisRequest):
    """
    Perform complete farm input cost analysis
    Combines labor, application, and irrigation optimization
    Returns comprehensive cost breakdown and prioritized recommendations
    """
    from services.input_cost_optimizer import InputCostOptimizer, FarmProfile

    optimizer = InputCostOptimizer()

    # Build soil test results if provided
    soil_test = None
    if request.soil_test_p_ppm is not None and request.soil_test_k_ppm is not None:
        soil_test = {
            "P": request.soil_test_p_ppm,
            "K": request.soil_test_k_ppm
        }

    farm_profile = FarmProfile(
        total_acres=request.total_acres,
        crops=[
            {
                "crop": c.crop.value,
                "acres": c.acres,
                "yield_goal": c.yield_goal
            }
            for c in request.crops
        ],
        irrigation_system=request.irrigation_type.value if request.irrigation_type else None,
        water_source=request.water_source.value if request.water_source else None,
        soil_test_results=soil_test
    )

    # Map priority enum
    from services.input_cost_optimizer import OptimizationPriority as OPEnum
    priority_map = {
        OptimizationPriority.COST_REDUCTION: OPEnum.COST_REDUCTION,
        OptimizationPriority.ROI_MAXIMIZATION: OPEnum.ROI_MAXIMIZATION,
        OptimizationPriority.SUSTAINABILITY: OPEnum.SUSTAINABILITY,
        OptimizationPriority.RISK_REDUCTION: OPEnum.RISK_REDUCTION
    }

    result = optimizer.analyze_complete_farm_costs(
        farm_profile=farm_profile,
        season_length_days=request.season_length_days,
        optimization_priority=priority_map[request.optimization_priority]
    )

    return result


@app.post("/api/v1/optimize/quick-estimate")
async def quick_cost_estimate(request: QuickEstimateRequest):
    """
    Quick cost estimate for planning purposes
    Uses industry averages for fast estimation
    """
    from services.input_cost_optimizer import InputCostOptimizer

    optimizer = InputCostOptimizer()

    result = optimizer.quick_cost_estimate(
        acres=request.acres,
        crop=request.crop.value,
        is_irrigated=request.is_irrigated,
        yield_goal=request.yield_goal
    )

    return result


@app.post("/api/v1/optimize/budget-worksheet")
async def generate_budget_worksheet(request: CompleteFarmAnalysisRequest):
    """
    Generate a complete budget worksheet for the farm
    Includes line items, totals, and scenario analysis
    """
    from services.input_cost_optimizer import InputCostOptimizer, FarmProfile

    optimizer = InputCostOptimizer()

    soil_test = None
    if request.soil_test_p_ppm is not None and request.soil_test_k_ppm is not None:
        soil_test = {
            "P": request.soil_test_p_ppm,
            "K": request.soil_test_k_ppm
        }

    farm_profile = FarmProfile(
        total_acres=request.total_acres,
        crops=[
            {
                "crop": c.crop.value,
                "acres": c.acres,
                "yield_goal": c.yield_goal
            }
            for c in request.crops
        ],
        irrigation_system=request.irrigation_type.value if request.irrigation_type else None,
        water_source=request.water_source.value if request.water_source else None,
        soil_test_results=soil_test
    )

    result = optimizer.generate_budget_worksheet(
        farm_profile=farm_profile,
        include_scenarios=True
    )

    return result


# ============================================================================
# PRICING SERVICE ENDPOINTS (v2.1)
# ============================================================================

@app.get("/api/v1/pricing/prices")
async def get_all_prices(
    category: Optional[InputCategory] = None,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Get all current prices (custom + defaults)
    Filter by category: fertilizer, pesticide, seed, fuel, custom_application
    """
    from services.pricing_service import get_pricing_service, InputCategory as IC

    service = get_pricing_service(region=region.value)

    category_map = {
        InputCategory.FERTILIZER: IC.FERTILIZER,
        InputCategory.PESTICIDE: IC.PESTICIDE,
        InputCategory.SEED: IC.SEED,
        InputCategory.FUEL: IC.FUEL,
        InputCategory.CUSTOM_APPLICATION: IC.CUSTOM_APPLICATION,
    }

    cat = category_map.get(category) if category else None
    prices = service.get_all_prices(category=cat)

    return {
        "region": region.value,
        "category": category.value if category else "all",
        "count": len(prices),
        "prices": prices
    }


@app.get("/api/v1/pricing/price/{product_id}")
async def get_price(
    product_id: str,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """Get current price for a specific product"""
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)
    price = service.get_price(product_id)

    if not price:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found")

    return {
        "product_id": product_id,
        "region": region.value,
        **price
    }


@app.post("/api/v1/pricing/set-price")
async def set_custom_price(
    request: SetPriceRequest,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Set a custom price from a supplier quote
    Updates the price used in all cost calculations
    Returns comparison to default/average price
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)

    result = service.set_custom_price(
        product_id=request.product_id,
        price=request.price,
        supplier=request.supplier,
        valid_until=request.valid_until,
        notes=request.notes
    )

    return result


@app.post("/api/v1/pricing/bulk-update")
async def bulk_update_prices(
    request: BulkPriceUpdateRequest,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Bulk update prices from a supplier quote sheet
    Useful for importing an entire price list at once
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)

    result = service.bulk_update_prices(
        price_updates=request.price_updates,
        supplier=request.supplier
    )

    return result


@app.post("/api/v1/pricing/buy-recommendation")
async def get_buy_recommendation(
    request: BuyRecommendationRequest,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Get recommendation on whether to buy now or wait
    Based on price trends and historical data
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)

    result = service.get_buy_recommendation(
        product_id=request.product_id,
        quantity_needed=request.quantity_needed,
        purchase_deadline=request.purchase_deadline
    )

    return result


@app.post("/api/v1/pricing/calculate-input-costs")
async def calculate_input_costs(
    request: InputCostCalculationRequest,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Calculate total input costs using current (custom or default) prices
    Returns line-item breakdown and summary
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)

    result = service.calculate_input_costs(
        crop=request.crop.value,
        acres=request.acres,
        yield_goal=request.yield_goal,
        inputs=request.inputs
    )

    return result


@app.post("/api/v1/pricing/compare-suppliers")
async def compare_suppliers(
    request: SupplierComparisonRequest,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Compare prices across suppliers for given products
    Identifies cheapest supplier overall
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)

    result = service.compare_suppliers(
        product_ids=request.product_ids,
        acres=request.acres
    )

    return result


@app.get("/api/v1/pricing/alerts")
async def get_price_alerts(region: Region = Region.MIDWEST_CORN_BELT):
    """
    Get alerts for expiring quotes and prices above average
    Use for proactive price management
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)
    alerts = service.get_price_alerts()

    return {
        "region": region.value,
        "alert_count": len(alerts),
        "alerts": alerts
    }


@app.get("/api/v1/pricing/budget-prices/{crop}")
async def generate_budget_prices(
    crop: CropType,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """
    Generate complete price list for budget planning
    Uses custom prices where available, defaults otherwise
    """
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)
    result = service.generate_budget_prices(crop=crop.value)

    return result


# ============================================================================
# SPRAY TIMING OPTIMIZER ENDPOINTS (v2.1)
# ============================================================================

@app.post("/api/v1/spray-timing/evaluate")
async def evaluate_spray_conditions(request: EvaluateConditionsRequest):
    """
    Evaluate if current weather conditions are suitable for spraying
    Returns risk level, score, and actionable recommendations
    """
    from services.spray_timing_optimizer import (
        get_spray_timing_optimizer,
        WeatherCondition,
        SprayType
    )

    optimizer = get_spray_timing_optimizer()

    # Convert request to WeatherCondition
    weather = WeatherCondition(
        datetime=request.weather.datetime,
        temp_f=request.weather.temp_f,
        humidity_pct=request.weather.humidity_pct,
        wind_mph=request.weather.wind_mph,
        wind_direction=request.weather.wind_direction,
        precip_chance_pct=request.weather.precip_chance_pct,
        precip_amount_in=request.weather.precip_amount_in,
        cloud_cover_pct=request.weather.cloud_cover_pct,
        dew_point_f=request.weather.dew_point_f
    )

    spray_type = SprayType(request.spray_type.value)

    result = optimizer.evaluate_current_conditions(
        weather=weather,
        spray_type=spray_type,
        product_name=request.product_name
    )

    return result


@app.post("/api/v1/spray-timing/find-windows")
async def find_spray_windows(request: FindSprayWindowsRequest):
    """
    Find optimal spray windows in a weather forecast
    Returns list of windows with quality ratings
    """
    from services.spray_timing_optimizer import (
        get_spray_timing_optimizer,
        WeatherCondition,
        SprayType
    )

    optimizer = get_spray_timing_optimizer()

    # Convert forecast to WeatherCondition objects
    forecast = [
        WeatherCondition(
            datetime=w.datetime,
            temp_f=w.temp_f,
            humidity_pct=w.humidity_pct,
            wind_mph=w.wind_mph,
            wind_direction=w.wind_direction,
            precip_chance_pct=w.precip_chance_pct,
            precip_amount_in=w.precip_amount_in,
            cloud_cover_pct=w.cloud_cover_pct,
            dew_point_f=w.dew_point_f
        )
        for w in request.forecast
    ]

    spray_type = SprayType(request.spray_type.value)

    result = optimizer.find_spray_windows(
        forecast=forecast,
        spray_type=spray_type,
        min_window_hours=request.min_window_hours,
        product_name=request.product_name
    )

    return result


@app.post("/api/v1/spray-timing/cost-of-waiting")
async def calculate_cost_of_waiting(request: CostOfWaitingRequest):
    """
    Calculate the economic cost of waiting to spray vs. spraying now
    Helps answer: 'Should I spray today in marginal conditions or wait?'
    """
    from services.spray_timing_optimizer import (
        get_spray_timing_optimizer,
        WeatherCondition,
        SprayType
    )

    optimizer = get_spray_timing_optimizer()

    # Convert current conditions
    current = WeatherCondition(
        datetime=request.current_conditions.datetime,
        temp_f=request.current_conditions.temp_f,
        humidity_pct=request.current_conditions.humidity_pct,
        wind_mph=request.current_conditions.wind_mph,
        wind_direction=request.current_conditions.wind_direction,
        precip_chance_pct=request.current_conditions.precip_chance_pct,
        precip_amount_in=request.current_conditions.precip_amount_in,
        cloud_cover_pct=request.current_conditions.cloud_cover_pct,
        dew_point_f=request.current_conditions.dew_point_f
    )

    # Convert forecast
    forecast = [
        WeatherCondition(
            datetime=w.datetime,
            temp_f=w.temp_f,
            humidity_pct=w.humidity_pct,
            wind_mph=w.wind_mph,
            wind_direction=w.wind_direction,
            precip_chance_pct=w.precip_chance_pct,
            precip_amount_in=w.precip_amount_in,
            cloud_cover_pct=w.cloud_cover_pct,
            dew_point_f=w.dew_point_f
        )
        for w in request.forecast
    ]

    spray_type = SprayType(request.spray_type.value)

    result = optimizer.calculate_cost_of_waiting(
        current_conditions=current,
        forecast=forecast,
        spray_type=spray_type,
        acres=request.acres,
        product_cost_per_acre=request.product_cost_per_acre,
        application_cost_per_acre=request.application_cost_per_acre,
        target_pest_or_disease=request.target_pest_or_disease,
        current_pressure=request.current_pressure.value,
        crop=request.crop.value,
        yield_goal=request.yield_goal,
        grain_price=request.grain_price
    )

    return result


@app.post("/api/v1/spray-timing/disease-pressure")
async def assess_disease_pressure(request: DiseasePressureRequest):
    """
    Assess disease pressure based on recent weather conditions
    Returns risk levels for relevant diseases and recommendations
    """
    from services.spray_timing_optimizer import (
        get_spray_timing_optimizer,
        WeatherCondition
    )

    optimizer = get_spray_timing_optimizer()

    # Convert weather history
    weather_history = [
        WeatherCondition(
            datetime=w.datetime,
            temp_f=w.temp_f,
            humidity_pct=w.humidity_pct,
            wind_mph=w.wind_mph,
            wind_direction=w.wind_direction,
            precip_chance_pct=w.precip_chance_pct,
            precip_amount_in=w.precip_amount_in,
            cloud_cover_pct=w.cloud_cover_pct,
            dew_point_f=w.dew_point_f
        )
        for w in request.weather_history
    ]

    result = optimizer.assess_disease_pressure(
        weather_history=weather_history,
        crop=request.crop.value,
        growth_stage=request.growth_stage.value
    )

    return result


@app.get("/api/v1/spray-timing/growth-stage-timing/{crop}/{growth_stage}")
async def get_growth_stage_timing(
    crop: CropType,
    growth_stage: GrowthStage,
    spray_type: SprayTypeEnum = SprayTypeEnum.FUNGICIDE
):
    """
    Get optimal spray timing guidance by crop and growth stage
    Returns timing recommendations and suggested products
    """
    from services.spray_timing_optimizer import (
        get_spray_timing_optimizer,
        SprayType
    )

    optimizer = get_spray_timing_optimizer()

    result = optimizer.get_spray_timing_by_growth_stage(
        crop=crop.value,
        growth_stage=growth_stage.value,
        spray_type=SprayType(spray_type.value)
    )

    return result


# ============================================================================
# YIELD RESPONSE OPTIMIZER ENDPOINTS (v2.2)
# ============================================================================

@app.post("/api/v1/yield-response/curve")
async def generate_yield_response_curve(request: YieldResponseCurveRequest):
    """
    Generate a yield response curve for a nutrient
    Shows how yield changes with increasing nutrient rates
    Essential for understanding diminishing returns
    """
    from services.yield_response_optimizer import get_yield_response_optimizer

    optimizer = get_yield_response_optimizer()

    # Convert soil test level enum to approximate ppm value
    soil_ppm_map = {
        SoilTestLevel.VERY_LOW: 5,
        SoilTestLevel.LOW: 10,
        SoilTestLevel.MEDIUM: 20,
        SoilTestLevel.HIGH: 40,
        SoilTestLevel.VERY_HIGH: 80,
    }

    result = optimizer.generate_response_curve(
        crop=request.crop.value,
        nutrient=request.nutrient.value,
        rate_range=(request.min_rate, request.max_rate),
        rate_step=request.rate_step,
        soil_test_level=soil_ppm_map.get(request.soil_test_level),
        previous_crop=request.previous_crop
    )

    return result


@app.post("/api/v1/yield-response/economic-optimum")
async def calculate_economic_optimum_rate(request: EconomicOptimumRequest):
    """
    Calculate the Economic Optimum Rate (EOR) for a nutrient
    The rate where marginal cost equals marginal revenue
    Returns the rate that maximizes profit, not yield
    """
    from services.yield_response_optimizer import get_yield_response_optimizer

    optimizer = get_yield_response_optimizer()

    # Convert soil test level enum to approximate ppm value
    soil_ppm_map = {
        SoilTestLevel.VERY_LOW: 5,
        SoilTestLevel.LOW: 10,
        SoilTestLevel.MEDIUM: 20,
        SoilTestLevel.HIGH: 40,
        SoilTestLevel.VERY_HIGH: 80,
    }

    result = optimizer.calculate_economic_optimum(
        crop=request.crop.value,
        nutrient=request.nutrient.value,
        nutrient_cost=request.nutrient_price_per_lb,
        commodity_price=request.grain_price_per_bu,
        soil_test_level=soil_ppm_map.get(request.soil_test_level),
        previous_crop=request.previous_crop
    )

    # Convert dataclass to dict for JSON response
    return {
        "optimum_rate": result.optimum_rate,
        "optimum_yield": result.optimum_yield,
        "agronomic_max_rate": result.agronomic_max_rate,
        "agronomic_max_yield": result.agronomic_max_yield,
        "yield_at_optimum_vs_max": result.yield_at_optimum_vs_max,
        "total_input_cost": result.total_input_cost,
        "gross_revenue": result.gross_revenue,
        "net_return": result.net_return,
        "return_per_dollar": result.return_per_dollar,
        "breakeven_rate": result.breakeven_rate,
        "price_ratio": result.price_ratio,
        "sensitivity": result.sensitivity,
        "acres": request.acres
    }


@app.post("/api/v1/yield-response/compare-rates")
async def compare_rate_scenarios(request: RateScenarioRequest):
    """
    Compare profitability of different application rates
    Useful for 'what-if' analysis and rate decisions
    """
    from services.yield_response_optimizer import (
        get_yield_response_optimizer,
        SoilTestLevel as STL
    )

    optimizer = get_yield_response_optimizer()

    soil_map = {
        SoilTestLevel.VERY_LOW: STL.VERY_LOW,
        SoilTestLevel.LOW: STL.LOW,
        SoilTestLevel.MEDIUM: STL.MEDIUM,
        SoilTestLevel.HIGH: STL.HIGH,
        SoilTestLevel.VERY_HIGH: STL.VERY_HIGH,
    }

    result = optimizer.compare_rate_scenarios(
        crop=request.crop.value,
        nutrient=request.nutrient.value,
        rates=request.rates,
        nutrient_price_per_lb=request.nutrient_price_per_lb,
        grain_price_per_bu=request.grain_price_per_bu,
        acres=request.acres,
        soil_test_level=soil_map[request.soil_test_level]
    )

    return result


@app.post("/api/v1/yield-response/price-sensitivity")
async def analyze_price_sensitivity(request: PriceSensitivityRequest):
    """
    Analyze how economic optimum rate changes with prices
    Shows rate recommendations at different nutrient:grain price ratios
    Critical for forward planning with volatile markets
    """
    from services.yield_response_optimizer import (
        get_yield_response_optimizer,
        SoilTestLevel as STL
    )

    optimizer = get_yield_response_optimizer()

    soil_map = {
        SoilTestLevel.VERY_LOW: STL.VERY_LOW,
        SoilTestLevel.LOW: STL.LOW,
        SoilTestLevel.MEDIUM: STL.MEDIUM,
        SoilTestLevel.HIGH: STL.HIGH,
        SoilTestLevel.VERY_HIGH: STL.VERY_HIGH,
    }

    result = optimizer.analyze_price_sensitivity(
        crop=request.crop.value,
        nutrient=request.nutrient.value,
        base_nutrient_price=request.base_nutrient_price,
        base_grain_price=request.base_grain_price,
        nutrient_price_range_pct=request.nutrient_price_range_pct,
        grain_price_range_pct=request.grain_price_range_pct,
        soil_test_level=soil_map[request.soil_test_level]
    )

    return result


@app.post("/api/v1/yield-response/multi-nutrient")
async def optimize_multi_nutrient(request: MultiNutrientOptimizationRequest):
    """
    Optimize rates across multiple nutrients simultaneously
    Accounts for nutrient interactions and budget constraints
    Returns complete fertilizer recommendation with economics
    """
    from services.yield_response_optimizer import get_yield_response_optimizer

    optimizer = get_yield_response_optimizer()

    result = optimizer.multi_nutrient_optimization(
        crop=request.crop.value,
        acres=request.acres,
        budget=request.budget,
        nutrient_prices=request.nutrient_prices,
        grain_price=request.grain_price,
        soil_test_p_ppm=request.soil_test_p_ppm,
        soil_test_k_ppm=request.soil_test_k_ppm,
        previous_crop=request.previous_crop,
        yield_goal=request.yield_goal
    )

    return result


@app.get("/api/v1/yield-response/crop-parameters/{crop}")
async def get_crop_response_parameters(crop: CropType):
    """
    Get the yield response parameters for a crop
    Shows the underlying agronomic data driving calculations
    """
    from services.yield_response_optimizer import get_yield_response_optimizer

    optimizer = get_yield_response_optimizer()
    result = optimizer.get_crop_parameters(crop=crop.value)

    return result


@app.get("/api/v1/yield-response/price-ratio-guide")
async def get_price_ratio_guide(
    crop: CropType = CropType.CORN,
    nutrient: NutrientType = NutrientType.NITROGEN
):
    """
    Get a quick reference guide for EOR based on price ratios
    Lookup table for field decisions without detailed calculations
    """
    from services.yield_response_optimizer import get_yield_response_optimizer

    optimizer = get_yield_response_optimizer()

    result = optimizer.generate_price_ratio_guide(
        crop=crop.value,
        nutrient=nutrient.value
    )

    return result


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

class LoginResponse(BaseModel):
    """Login response with tokens and user info"""
    tokens: Token
    user: UserResponse


@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    Returns access_token (24h) and refresh_token (7d).
    """
    user_service = get_user_service()

    tokens, user, error = user_service.authenticate(
        username=login_data.username,
        password=login_data.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )

    if error:
        raise HTTPException(
            status_code=401,
            detail=error
        )

    return LoginResponse(tokens=tokens, user=user)


@app.post("/api/v1/auth/logout", tags=["Authentication"])
async def logout(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Logout current user and invalidate session."""
    from fastapi.security import HTTPBearer

    # Get token from header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    user_service = get_user_service()
    user_service.logout(token, user.id, get_client_ip(request))

    return {"message": "Logged out successfully"}


@app.post("/api/v1/auth/refresh", response_model=Token, tags=["Authentication"])
async def refresh_tokens(refresh_token: str):
    """Get new access token using refresh token."""
    user_service = get_user_service()

    tokens, error = user_service.refresh_tokens(refresh_token)

    if error:
        raise HTTPException(status_code=401, detail=error)

    return tokens


@app.get("/api/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(user: AuthenticatedUser = Depends(get_current_active_user)):
    """Get current authenticated user's info."""
    user_service = get_user_service()
    return user_service.get_user_by_id(user.id)


@app.put("/api/v1/auth/me", response_model=UserResponse, tags=["Authentication"])
async def update_current_user(
    user_data: UserUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update current user's profile (non-admin fields only)."""
    # Users can only update certain fields on themselves
    safe_update = UserUpdate(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone
        # Note: role and is_active cannot be self-updated
    )

    user_service = get_user_service()
    updated_user, error = user_service.update_user(user.id, safe_update, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return updated_user


@app.post("/api/v1/auth/change-password", tags=["Authentication"])
async def change_password(
    password_data: PasswordChange,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Change current user's password."""
    user_service = get_user_service()

    success, error = user_service.change_password(
        user_id=user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Password changed successfully. Please login again."}


# ============================================================================
# USER MANAGEMENT ENDPOINTS (Admin/Manager)
# ============================================================================

@app.get("/api/v1/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    crew_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(require_manager)
):
    """List all users (manager/admin only)."""
    user_service = get_user_service()
    return user_service.list_users(role=role, is_active=is_active, crew_id=crew_id)


@app.post("/api/v1/users", response_model=UserResponse, tags=["Users"])
async def create_user(
    user_data: UserCreate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Create a new user (admin only)."""
    user_service = get_user_service()

    new_user, error = user_service.create_user(user_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return new_user


@app.get("/api/v1/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(
    user_id: int,
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Get user by ID (manager/admin only)."""
    user_service = get_user_service()
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.put("/api/v1/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Update a user (admin only)."""
    user_service = get_user_service()

    updated_user, error = user_service.update_user(user_id, user_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@app.delete("/api/v1/users/{user_id}", tags=["Users"])
async def deactivate_user(
    user_id: int,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Deactivate a user (admin only). Soft delete - can be reactivated."""
    user_service = get_user_service()

    success, error = user_service.delete_user(user_id, admin.id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "User deactivated successfully"}


# ============================================================================
# CREW MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/crews", response_model=List[CrewResponse], tags=["Crews"])
async def list_crews(
    is_active: Optional[bool] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List all crews."""
    user_service = get_user_service()
    return user_service.list_crews(is_active=is_active)


@app.post("/api/v1/crews", response_model=CrewResponse, tags=["Crews"])
async def create_crew(
    crew_data: CrewCreate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Create a new crew (admin only)."""
    user_service = get_user_service()

    crew, error = user_service.create_crew(crew_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return crew


@app.get("/api/v1/crews/{crew_id}", response_model=CrewResponse, tags=["Crews"])
async def get_crew(
    crew_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crew by ID."""
    user_service = get_user_service()
    crew = user_service.get_crew_by_id(crew_id)

    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")

    return crew


@app.put("/api/v1/crews/{crew_id}", response_model=CrewResponse, tags=["Crews"])
async def update_crew(
    crew_id: int,
    crew_data: CrewUpdate,
    admin: AuthenticatedUser = Depends(require_admin)
):
    """Update a crew (admin only)."""
    user_service = get_user_service()

    crew, error = user_service.update_crew(crew_id, crew_data, admin.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")

    return crew


@app.get("/api/v1/crews/{crew_id}/members", response_model=List[CrewMemberResponse], tags=["Crews"])
async def get_crew_members(
    crew_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all members of a crew."""
    user_service = get_user_service()
    return user_service.get_crew_members(crew_id)


@app.post("/api/v1/crews/{crew_id}/members/{user_id}", tags=["Crews"])
async def add_crew_member(
    crew_id: int,
    user_id: int,
    manager: AuthenticatedUser = Depends(require_manager)
):
    """Add a user to a crew (manager/admin only)."""
    user_service = get_user_service()

    success, error = user_service.add_crew_member(crew_id, user_id, manager.id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Member added successfully"}


@app.delete("/api/v1/crews/{crew_id}/members/{user_id}", tags=["Crews"])
async def remove_crew_member(
    crew_id: int,
    user_id: int,
    manager: AuthenticatedUser = Depends(require_manager)
):
    """Remove a user from a crew (manager/admin only)."""
    user_service = get_user_service()

    success, error = user_service.remove_crew_member(crew_id, user_id, manager.id)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return {"message": "Member removed successfully"}


@app.get("/api/v1/users/{user_id}/crews", response_model=List[CrewResponse], tags=["Crews"])
async def get_user_crews(
    user_id: int,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all crews a user belongs to."""
    # Users can see their own crews, managers can see anyone's
    if user_id != current_user.id and not current_user.is_manager:
        raise HTTPException(status_code=403, detail="Access denied")

    user_service = get_user_service()
    return user_service.get_user_crews(user_id)


# ============================================================================
# TASK MANAGEMENT ENDPOINTS (v2.5 Phase 2)
# ============================================================================

class TaskListResponse(BaseModel):
    """Response for task list endpoint"""
    count: int
    tasks: List[TaskResponse]


@app.get("/api/v1/tasks", response_model=TaskListResponse, tags=["Tasks"])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_user_id: Optional[int] = None,
    assigned_to_crew_id: Optional[int] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    my_tasks: bool = False,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List tasks with role-based filtering.

    - Admin: sees all tasks
    - Manager: sees own tasks, created tasks, and crew-assigned tasks
    - Crew: sees only own assigned tasks or tasks assigned to their crews

    Filters:
    - status: todo, in_progress, completed, cancelled
    - priority: low, medium, high, urgent
    - my_tasks: true to show only tasks assigned to current user
    """
    task_service = get_task_service()

    # Convert status/priority strings to enums if provided
    status_enum = TaskStatus(status) if status else None
    priority_enum = TaskPriority(priority) if priority else None

    tasks = task_service.list_tasks(
        status=status_enum,
        priority=priority_enum,
        assigned_to_user_id=assigned_to_user_id,
        assigned_to_crew_id=assigned_to_crew_id,
        due_before=due_before,
        due_after=due_after,
        user_id=user.id,
        user_role=user.role.value,
        my_tasks_only=my_tasks
    )

    return TaskListResponse(count=len(tasks), tasks=tasks)


@app.post("/api/v1/tasks", response_model=TaskResponse, tags=["Tasks"])
async def create_task(
    task_data: TaskCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a new task.

    - All users can create tasks
    - Crew members can only assign tasks to themselves
    - Managers/admins can assign to anyone
    """
    task_service = get_task_service()

    # Crew members can only self-assign
    if user.role == UserRole.CREW:
        if task_data.assigned_to_user_id and task_data.assigned_to_user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Crew members can only assign tasks to themselves"
            )
        # Auto-assign to self if no assignment specified
        if not task_data.assigned_to_user_id and not task_data.assigned_to_crew_id:
            task_data.assigned_to_user_id = user.id

    task, error = task_service.create_task(task_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return task


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get task by ID."""
    task_service = get_task_service()

    # Check permission
    if not task_service.can_view_task(task_id, user.id, user.role.value):
        raise HTTPException(status_code=403, detail="Access denied")

    task = task_service.get_task_by_id(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Update a task.

    - Admin: can update any task
    - Manager: can update own tasks, created tasks, or crew-assigned tasks
    - Crew: can only update tasks assigned to them
    """
    task_service = get_task_service()

    # Check permission
    if not task_service.can_edit_task(task_id, user.id, user.role.value):
        raise HTTPException(status_code=403, detail="Access denied")

    # Crew members cannot reassign tasks to others
    if user.role == UserRole.CREW:
        if task_data.assigned_to_user_id and task_data.assigned_to_user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Crew members cannot reassign tasks to others"
            )

    task, error = task_service.update_task(task_id, task_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.delete("/api/v1/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """
    Delete a task (soft delete).

    Manager/admin only.
    """
    task_service = get_task_service()

    # Managers can only delete tasks they have access to
    if user.role == UserRole.MANAGER:
        if not task_service.can_edit_task(task_id, user.id, user.role.value):
            raise HTTPException(status_code=403, detail="Access denied")

    success, error = task_service.delete_task(task_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete task")

    return {"message": "Task deleted successfully"}


@app.post("/api/v1/tasks/{task_id}/status", response_model=TaskResponse, tags=["Tasks"])
async def change_task_status(
    task_id: int,
    status_data: StatusChangeRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Change task status.

    Valid transitions:
    - todo -> in_progress, cancelled
    - in_progress -> todo, completed, cancelled
    - completed -> in_progress (reopen)
    - cancelled -> todo (restore)
    """
    task_service = get_task_service()

    # Check permission
    if not task_service.can_edit_task(task_id, user.id, user.role.value):
        raise HTTPException(status_code=403, detail="Access denied")

    task, error = task_service.change_status(task_id, status_data.status, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# ============================================================================
# FIELD MANAGEMENT ENDPOINTS (v2.5 Phase 3)
# ============================================================================

class FieldListResponse(BaseModel):
    """Response for field list endpoint"""
    count: int
    fields: List[FieldResponse]


@app.get("/api/v1/fields", response_model=FieldListResponse, tags=["Fields"])
async def list_fields(
    farm_name: Optional[str] = None,
    current_crop: Optional[str] = None,
    soil_type: Optional[str] = None,
    irrigation_type: Optional[str] = None,
    search: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List all fields with optional filters.

    Filters:
    - farm_name: Filter by farm grouping
    - current_crop: Filter by crop type (corn, soybean, wheat, etc.)
    - soil_type: Filter by soil type (clay, loam, sandy, etc.)
    - irrigation_type: Filter by irrigation (none, center_pivot, drip, etc.)
    - search: Search by field or farm name
    """
    field_service = get_field_service()

    # Convert string filters to enums if provided
    crop_enum = FieldCropType(current_crop) if current_crop else None
    soil_enum = SoilType(soil_type) if soil_type else None
    irrig_enum = FieldIrrigationType(irrigation_type) if irrigation_type else None

    fields = field_service.list_fields(
        farm_name=farm_name,
        current_crop=crop_enum,
        soil_type=soil_enum,
        irrigation_type=irrig_enum,
        search=search
    )

    return FieldListResponse(count=len(fields), fields=fields)


@app.post("/api/v1/fields", response_model=FieldResponse, tags=["Fields"])
async def create_field(
    field_data: FieldCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new field."""
    field_service = get_field_service()

    field, error = field_service.create_field(field_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return field


@app.get("/api/v1/fields/summary", response_model=FieldSummary, tags=["Fields"])
async def get_field_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary statistics for all fields."""
    field_service = get_field_service()
    return field_service.get_field_summary()


@app.get("/api/v1/fields/farms", tags=["Fields"])
async def get_farm_names(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of unique farm names for filtering."""
    field_service = get_field_service()
    return {"farms": field_service.get_farm_names()}


@app.get("/api/v1/fields/{field_id}", response_model=FieldResponse, tags=["Fields"])
async def get_field(
    field_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get field by ID."""
    field_service = get_field_service()
    field = field_service.get_field_by_id(field_id)

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return field


@app.put("/api/v1/fields/{field_id}", response_model=FieldResponse, tags=["Fields"])
async def update_field(
    field_id: int,
    field_data: FieldUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update a field."""
    field_service = get_field_service()

    field, error = field_service.update_field(field_id, field_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return field


@app.delete("/api/v1/fields/{field_id}", tags=["Fields"])
async def delete_field(
    field_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete a field (soft delete). Manager/admin only."""
    field_service = get_field_service()

    success, error = field_service.delete_field(field_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete field")

    return {"message": "Field deleted successfully"}


# ============================================================================
# FIELD OPERATIONS ENDPOINTS (v2.5 Phase 3)
# ============================================================================

class OperationListResponse(BaseModel):
    """Response for operation list endpoint"""
    count: int
    operations: List[OperationResponse]


@app.get("/api/v1/operations", response_model=OperationListResponse, tags=["Operations"])
async def list_operations(
    field_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    operator_id: Optional[int] = None,
    farm_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List field operations with optional filters.

    Filters:
    - field_id: Filter by specific field
    - operation_type: spray, fertilizer, planting, harvest, tillage, scouting, irrigation, other
    - date_from/date_to: Date range filter
    - operator_id: Filter by who performed the operation
    - farm_name: Filter by farm
    - limit/offset: Pagination
    """
    ops_service = get_field_operations_service()

    # Convert operation_type string to enum if provided
    op_type_enum = OperationType(operation_type) if operation_type else None

    operations = ops_service.list_operations(
        field_id=field_id,
        operation_type=op_type_enum,
        date_from=date_from,
        date_to=date_to,
        operator_id=operator_id,
        farm_name=farm_name,
        limit=limit,
        offset=offset
    )

    return OperationListResponse(count=len(operations), operations=operations)


@app.post("/api/v1/operations", response_model=OperationResponse, tags=["Operations"])
async def create_operation(
    op_data: OperationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Log a new field operation.

    Operation types: spray, fertilizer, planting, harvest, tillage, scouting, irrigation, seed_treatment, cover_crop, other
    """
    ops_service = get_field_operations_service()

    operation, error = ops_service.create_operation(op_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return operation


@app.get("/api/v1/operations/summary", response_model=OperationsSummary, tags=["Operations"])
async def get_operations_summary(
    field_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get summary statistics for operations.

    Returns total operations, operations by type, and cost summaries.
    """
    ops_service = get_field_operations_service()

    return ops_service.get_operations_summary(
        field_id=field_id,
        date_from=date_from,
        date_to=date_to
    )


@app.get("/api/v1/operations/{operation_id}", response_model=OperationResponse, tags=["Operations"])
async def get_operation(
    operation_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get operation by ID."""
    ops_service = get_field_operations_service()
    operation = ops_service.get_operation_by_id(operation_id)

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    return operation


@app.put("/api/v1/operations/{operation_id}", response_model=OperationResponse, tags=["Operations"])
async def update_operation(
    operation_id: int,
    op_data: OperationUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update an operation."""
    ops_service = get_field_operations_service()

    operation, error = ops_service.update_operation(operation_id, op_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    return operation


@app.delete("/api/v1/operations/{operation_id}", tags=["Operations"])
async def delete_operation(
    operation_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete an operation (soft delete). Manager/admin only."""
    ops_service = get_field_operations_service()

    success, error = ops_service.delete_operation(operation_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete operation")

    return {"message": "Operation deleted successfully"}


@app.get("/api/v1/fields/{field_id}/operations", response_model=FieldOperationHistory, tags=["Operations"])
async def get_field_operation_history(
    field_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get complete operation history for a specific field.

    Returns field info, all operations, and summary statistics.
    """
    ops_service = get_field_operations_service()

    history = ops_service.get_field_operation_history(field_id)

    if not history:
        raise HTTPException(status_code=404, detail="Field not found")

    return history


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload during development
        log_level="info"
    )
