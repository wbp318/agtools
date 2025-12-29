"""
Professional Crop Consulting System - FastAPI Backend
Main application entry point with Input Cost Optimization
Version 2.2.0 - Added Yield Response & Economic Optimum Rate Calculator
"""

import sys
import os

# Add parent directory to path so we can import from database/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from services.equipment_service import (
    get_equipment_service,
    EquipmentCreate,
    EquipmentUpdate,
    EquipmentResponse,
    EquipmentSummary,
    EquipmentType,
    EquipmentStatus,
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    MaintenanceType,
    MaintenanceAlert,
    EquipmentUsageCreate,
    EquipmentUsageResponse
)
from services.inventory_service import (
    get_inventory_service,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    InventorySummary,
    InventoryCategory,
    TransactionCreate,
    TransactionResponse,
    TransactionType,
    InventoryAlert,
    QuickPurchaseRequest,
    AdjustQuantityRequest
)
from services.reporting_service import (
    get_reporting_service,
    ReportType,
    OperationsReport,
    FinancialReport,
    EquipmentReport,
    InventoryReport,
    FieldPerformanceReport,
    DashboardSummary
)
from services.cost_tracking_service import (
    get_cost_tracking_service,
    ExpenseCategory,
    SourceType,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseListResponse,
    AllocationCreate,
    AllocationResponse,
    ExpenseWithAllocations,
    ColumnMapping,
    ImportPreview,
    ImportResult,
    ImportBatchResponse,
    SavedMappingResponse,
    OCRScanResult,
    CostPerAcreReport,
    CostPerAcreItem,
    CategoryBreakdown,
    CropCostSummary
)
from services.quickbooks_import import (
    get_qb_import_service,
    QBImportPreview,
    QBImportSummary,
    QBAccountMapping
)
from services.profitability_service import (
    get_profitability_service,
    CropType as ProfitCropType,
    InputCategory,
    BudgetStatus,
    BreakEvenRequest,
    BreakEvenResponse,
    InputROIRequest,
    InputROIResponse,
    ScenarioRequest,
    ScenarioResponse,
    BudgetTrackerRequest,
    BudgetTrackerResponse
)
from services.sustainability_service import (
    get_sustainability_service,
    InputCategory as SustainabilityInputCategory,
    CarbonSource,
    SustainabilityPractice,
    MetricPeriod,
    InputUsageCreate,
    InputUsageResponse,
    CarbonEntryCreate,
    CarbonEntryResponse,
    WaterUsageCreate,
    WaterUsageResponse,
    PracticeRecordCreate,
    PracticeRecordResponse,
    SustainabilityScorecard,
    SustainabilityReport,
    InputSummary,
    CarbonSummary,
    WaterSummary
)
from services.climate_service import (
    get_climate_service,
    GDDRecordCreate,
    GDDRecordResponse,
    GDDSummary,
    GDDEntry,
    PrecipitationCreate,
    PrecipitationResponse,
    PrecipitationSummary,
    PrecipitationType,
    ClimateSummary,
    ClimateComparison,
    GDD_BASE_TEMPS,
    CORN_GDD_STAGES,
    SOYBEAN_GDD_STAGES
)
from services.research_service import (
    get_research_service,
    TrialType,
    ExperimentalDesign,
    PlotStatus,
    MeasurementType,
    TrialCreate,
    TrialUpdate,
    TrialResponse,
    TreatmentCreate,
    TreatmentResponse,
    PlotCreate,
    PlotResponse,
    MeasurementCreate,
    MeasurementResponse,
    TrialAnalysis,
    ResearchExport
)
from services.grant_service import (
    get_grant_service,
    GrantProgram,
    NRCSCategory,
    CarbonProgram,
    NRCS_PRACTICES,
    CARBON_PROGRAMS,
    BENCHMARK_DATA
)
from services.grant_enhancement_service import (
    get_grant_enhancement_service,
    PrecisionAgTechnology,
    DataCategory,
    ResearchArea,
    PartnerType,
    TECHNOLOGY_BENEFITS,
    GRANT_DATA_REQUIREMENTS,
    RESEARCH_PARTNERS
)
from services.grant_operations_service import (
    get_grant_operations_service,
    ApplicationStatus,
    DocumentStatus,
    LicenseType,
    ComplianceCategory,
    CropType as BudgetCropType,
    OutreachType,
    GRANT_PROGRAMS,
    CROP_BUDGET_DEFAULTS,
    COMPLIANCE_REQUIREMENTS
)
from services.farm_intelligence_service import (
    get_farm_intelligence_service,
    Commodity,
    ContractStatus,
    InsuranceType,
    CoverageLevel,
    InputCategory as ProcurementInputCategory,
    CURRENT_PRICES,
    INSURANCE_RATES
)
from services.enterprise_operations_service import (
    get_enterprise_operations_service,
    EmployeeType,
    EmployeeStatus,
    PayType,
    CertificationType,
    TimeEntryType,
    LeaseType,
    LeaseStatus,
    PaymentFrequency,
    CashFlowCategory,
    TransactionStatus,
    EntityType,
    CASH_RENT_AVERAGES
)
from services.precision_intelligence_service import (
    get_precision_intelligence_service,
    PredictionModel,
    ZoneType,
    PrescriptionType,
    RecommendationType as PrecisionRecommendationType,
    ConfidenceLevel,
    CropStage
)
from services.grain_storage_service import (
    get_grain_storage_service,
    GrainType,
    BinType,
    BinStatus,
    DryerType,
    TransactionType as GrainTransactionType,
    AlertType as GrainAlertType
)
from services.farm_business_service import (
    get_farm_business_service,
    AssetType,
    DepreciationMethod,
    TaxEntity,
    TransferMethod,
    FamilyRole,
    MilestoneCategory,
    BenchmarkMetric,
    DocumentCategory,
    MACRS_RATES
)
from mobile import mobile_router, configure_templates

# Initialize FastAPI app
app = FastAPI(
    title="AgTools Professional Crop Consulting API",
    description="Professional-grade crop consulting system with comprehensive farm management: pest/disease management, input optimization, profitability analysis, sustainability metrics, grant compliance, farm intelligence, enterprise operations, precision agriculture intelligence, grain storage management, and complete farm business suite",
    version="4.2.0",
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
# MOBILE WEB INTERFACE (Server-rendered HTML)
# ============================================================================

# Get the directory containing main.py
_backend_dir = os.path.dirname(os.path.abspath(__file__))

# Mount static files (CSS, JS, icons)
app.mount("/static", StaticFiles(directory=os.path.join(_backend_dir, "static")), name="static")

# Configure Jinja2 templates for mobile routes
configure_templates(os.path.join(_backend_dir, "templates"))

# Include mobile router (routes under /m/*)
app.include_router(mobile_router)

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
# EQUIPMENT MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/equipment", response_model=List[EquipmentResponse], tags=["Equipment"])
async def list_equipment(
    equipment_type: Optional[EquipmentType] = None,
    status: Optional[EquipmentStatus] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List all equipment with optional filters.

    - **equipment_type**: Filter by type (tractor, combine, sprayer, etc.)
    - **status**: Filter by status (available, in_use, maintenance, retired)
    - **search**: Search by name, make, model, or serial number
    """
    equip_service = get_equipment_service()
    return equip_service.list_equipment(
        equipment_type=equipment_type,
        status=status,
        search=search,
        limit=limit,
        offset=offset
    )


@app.post("/api/v1/equipment", response_model=EquipmentResponse, tags=["Equipment"])
async def create_equipment(
    equip_data: EquipmentCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new equipment record."""
    equip_service = get_equipment_service()
    equipment, error = equip_service.create_equipment(equip_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return equipment


@app.get("/api/v1/equipment/summary", response_model=EquipmentSummary, tags=["Equipment"])
async def get_equipment_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary statistics for equipment fleet."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_summary()


@app.get("/api/v1/equipment/types", tags=["Equipment"])
async def get_equipment_types(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of equipment types for dropdowns."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_types()


@app.get("/api/v1/equipment/statuses", tags=["Equipment"])
async def get_equipment_statuses(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of equipment statuses for dropdowns."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_statuses()


@app.get("/api/v1/equipment/{equipment_id}", response_model=EquipmentResponse, tags=["Equipment"])
async def get_equipment(
    equipment_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get equipment by ID."""
    equip_service = get_equipment_service()
    equipment = equip_service.get_equipment_by_id(equipment_id)

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


@app.put("/api/v1/equipment/{equipment_id}", response_model=EquipmentResponse, tags=["Equipment"])
async def update_equipment(
    equipment_id: int,
    equip_data: EquipmentUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update equipment."""
    equip_service = get_equipment_service()
    equipment, error = equip_service.update_equipment(equipment_id, equip_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


@app.delete("/api/v1/equipment/{equipment_id}", tags=["Equipment"])
async def delete_equipment(
    equipment_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Retire equipment (soft delete). Manager/admin only."""
    equip_service = get_equipment_service()
    success, error = equip_service.delete_equipment(equipment_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete equipment")

    return {"message": "Equipment retired successfully"}


@app.post("/api/v1/equipment/{equipment_id}/hours", response_model=EquipmentResponse, tags=["Equipment"])
async def update_equipment_hours(
    equipment_id: int,
    new_hours: float,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update equipment hour meter reading."""
    equip_service = get_equipment_service()
    equipment, error = equip_service.update_hours(equipment_id, new_hours, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return equipment


# ============================================================================
# MAINTENANCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/maintenance", response_model=List[MaintenanceResponse], tags=["Maintenance"])
async def list_maintenance(
    equipment_id: Optional[int] = None,
    maintenance_type: Optional[MaintenanceType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List maintenance records with optional filters."""
    equip_service = get_equipment_service()
    return equip_service.list_maintenance(
        equipment_id=equipment_id,
        maintenance_type=maintenance_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )


@app.post("/api/v1/maintenance", response_model=MaintenanceResponse, tags=["Maintenance"])
async def create_maintenance(
    maint_data: MaintenanceCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Log a maintenance record."""
    equip_service = get_equipment_service()
    maintenance, error = equip_service.create_maintenance(maint_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return maintenance


@app.get("/api/v1/maintenance/alerts", response_model=List[MaintenanceAlert], tags=["Maintenance"])
async def get_maintenance_alerts(
    days_ahead: int = 30,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get upcoming maintenance alerts.

    Returns equipment that has maintenance due within the specified number of days,
    or is overdue for service.
    """
    equip_service = get_equipment_service()
    return equip_service.get_maintenance_alerts(days_ahead=days_ahead)


@app.get("/api/v1/maintenance/types", tags=["Maintenance"])
async def get_maintenance_types(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of maintenance types for dropdowns."""
    equip_service = get_equipment_service()
    return equip_service.get_maintenance_types()


@app.get("/api/v1/equipment/{equipment_id}/maintenance", response_model=List[MaintenanceResponse], tags=["Maintenance"])
async def get_equipment_maintenance_history(
    equipment_id: int,
    limit: int = 50,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get maintenance history for specific equipment."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_maintenance_history(equipment_id, limit=limit)


@app.get("/api/v1/equipment/{equipment_id}/usage", response_model=List[EquipmentUsageResponse], tags=["Equipment"])
async def get_equipment_usage_history(
    equipment_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get usage history for specific equipment."""
    equip_service = get_equipment_service()
    return equip_service.get_equipment_usage_history(
        equipment_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )


@app.post("/api/v1/equipment/usage", response_model=EquipmentUsageResponse, tags=["Equipment"])
async def log_equipment_usage(
    usage_data: EquipmentUsageCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Log equipment usage (hours, fuel, operator)."""
    equip_service = get_equipment_service()
    usage, error = equip_service.log_usage(usage_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return usage


# ============================================================================
# INVENTORY MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/inventory", response_model=List[InventoryItemResponse], tags=["Inventory"])
async def list_inventory(
    category: Optional[InventoryCategory] = None,
    search: Optional[str] = None,
    storage_location: Optional[str] = None,
    low_stock_only: bool = False,
    expiring_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List inventory items with optional filters.

    - **category**: Filter by category (seed, fertilizer, herbicide, etc.)
    - **search**: Search by name, manufacturer, or product code
    - **storage_location**: Filter by storage location
    - **low_stock_only**: Only show items below minimum quantity
    - **expiring_only**: Only show items expiring within 30 days
    """
    inv_service = get_inventory_service()
    return inv_service.list_items(
        category=category,
        search=search,
        storage_location=storage_location,
        low_stock_only=low_stock_only,
        expiring_only=expiring_only,
        limit=limit,
        offset=offset
    )


@app.post("/api/v1/inventory", response_model=InventoryItemResponse, tags=["Inventory"])
async def create_inventory_item(
    item_data: InventoryItemCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new inventory item."""
    inv_service = get_inventory_service()
    item, error = inv_service.create_item(item_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return item


@app.get("/api/v1/inventory/summary", response_model=InventorySummary, tags=["Inventory"])
async def get_inventory_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary statistics for inventory."""
    inv_service = get_inventory_service()
    return inv_service.get_inventory_summary()


@app.get("/api/v1/inventory/categories", tags=["Inventory"])
async def get_inventory_categories(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of inventory categories for dropdowns."""
    inv_service = get_inventory_service()
    return inv_service.get_categories()


@app.get("/api/v1/inventory/locations", tags=["Inventory"])
async def get_storage_locations(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of unique storage locations."""
    inv_service = get_inventory_service()
    return inv_service.get_storage_locations()


@app.get("/api/v1/inventory/alerts", response_model=List[InventoryAlert], tags=["Inventory"])
async def get_inventory_alerts(
    expiry_days: int = 30,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get inventory alerts (low stock and expiring items).

    Returns items that are below minimum quantity or expiring within the specified days.
    """
    inv_service = get_inventory_service()
    return inv_service.get_alerts(expiry_days=expiry_days)


@app.get("/api/v1/inventory/{item_id}", response_model=InventoryItemResponse, tags=["Inventory"])
async def get_inventory_item(
    item_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get inventory item by ID."""
    inv_service = get_inventory_service()
    item = inv_service.get_item_by_id(item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return item


@app.put("/api/v1/inventory/{item_id}", response_model=InventoryItemResponse, tags=["Inventory"])
async def update_inventory_item(
    item_id: int,
    item_data: InventoryItemUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update inventory item."""
    inv_service = get_inventory_service()
    item, error = inv_service.update_item(item_id, item_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    return item


@app.delete("/api/v1/inventory/{item_id}", tags=["Inventory"])
async def delete_inventory_item(
    item_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete inventory item (soft delete). Manager/admin only."""
    inv_service = get_inventory_service()
    success, error = inv_service.delete_item(item_id, user.id)

    if not success:
        raise HTTPException(status_code=400, detail=error or "Failed to delete item")

    return {"message": "Inventory item deleted successfully"}


# ============================================================================
# INVENTORY TRANSACTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/inventory/transaction", response_model=TransactionResponse, tags=["Inventory"])
async def record_inventory_transaction(
    trans_data: TransactionCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record an inventory transaction.

    Use positive quantity for additions (purchase, return, adjustment up).
    Use negative quantity for deductions (usage, waste, adjustment down).
    """
    inv_service = get_inventory_service()
    transaction, error = inv_service.record_transaction(trans_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return transaction


@app.get("/api/v1/inventory/{item_id}/transactions", response_model=List[TransactionResponse], tags=["Inventory"])
async def get_item_transactions(
    item_id: int,
    transaction_type: Optional[TransactionType] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get transaction history for an inventory item."""
    inv_service = get_inventory_service()
    return inv_service.get_item_transactions(
        item_id,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )


@app.post("/api/v1/inventory/purchase", response_model=InventoryItemResponse, tags=["Inventory"])
async def quick_purchase(
    purchase_data: QuickPurchaseRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Quick purchase entry.

    Adds quantity to inventory and records a purchase transaction.
    """
    inv_service = get_inventory_service()
    item, error = inv_service.quick_purchase(purchase_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return item


@app.post("/api/v1/inventory/adjust", response_model=InventoryItemResponse, tags=["Inventory"])
async def adjust_quantity(
    adjust_data: AdjustQuantityRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Adjust inventory quantity (for counts, corrections).

    Sets the quantity to the new value and records an adjustment transaction.
    """
    inv_service = get_inventory_service()
    item, error = inv_service.adjust_quantity(adjust_data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return item


# ============================================================================
# REPORTING ENDPOINTS (Phase 5)
# ============================================================================

@app.get("/api/v1/reports/operations", response_model=OperationsReport, tags=["Reports"])
async def get_operations_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get operations report with aggregations.

    Returns total operations, costs, breakdowns by type, and monthly trends.
    """
    report_service = get_reporting_service()
    return report_service.get_operations_report(date_from, date_to, field_id)


@app.get("/api/v1/reports/financial", response_model=FinancialReport, tags=["Reports"])
async def get_financial_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get financial analysis report.

    Returns costs, revenue, profit/loss by field, and cost breakdowns.
    """
    report_service = get_reporting_service()
    return report_service.get_financial_report(date_from, date_to)


@app.get("/api/v1/reports/equipment", response_model=EquipmentReport, tags=["Reports"])
async def get_equipment_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get equipment utilization report.

    Returns fleet stats, equipment usage, hours by type, and maintenance alerts.
    """
    report_service = get_reporting_service()
    return report_service.get_equipment_report(date_from, date_to)


@app.get("/api/v1/reports/inventory", response_model=InventoryReport, tags=["Reports"])
async def get_inventory_report(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get inventory status report.

    Returns stock levels, values by category, and low stock/expiring alerts.
    """
    report_service = get_reporting_service()
    return report_service.get_inventory_report()


@app.get("/api/v1/reports/fields", response_model=FieldPerformanceReport, tags=["Reports"])
async def get_field_performance_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get field performance report.

    Returns per-field metrics including costs, yields, and operations count.
    """
    report_service = get_reporting_service()
    return report_service.get_field_performance_report(date_from, date_to)


@app.get("/api/v1/reports/dashboard", response_model=DashboardSummary, tags=["Reports"])
async def get_dashboard_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get combined dashboard summary.

    Returns key metrics from all areas: operations, fields, equipment, inventory.
    """
    report_service = get_reporting_service()
    return report_service.get_dashboard_summary()


class CSVExportRequest(BaseModel):
    """Request for CSV export"""
    report_type: ReportType
    date_from: Optional[date] = None
    date_to: Optional[date] = None


@app.post("/api/v1/reports/export/csv", tags=["Reports"])
async def export_report_csv(
    request: CSVExportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Export report data to CSV format.

    Returns CSV content as text.
    """
    from fastapi.responses import Response

    report_service = get_reporting_service()
    csv_content = report_service.export_to_csv(
        request.report_type,
        request.date_from,
        request.date_to
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={request.report_type.value}_report.csv"
        }
    )


# ============================================================================
# COST TRACKING - Import & Expenses
# ============================================================================

@app.post("/api/v1/costs/import/csv/preview", response_model=ImportPreview, tags=["Cost Tracking"])
async def preview_csv_import(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Preview CSV file and get column mapping suggestions.

    Upload a QuickBooks CSV export to preview and get suggested column mappings.
    """
    content = await file.read()
    csv_text = content.decode('utf-8')

    cost_service = get_cost_tracking_service()
    return cost_service.preview_csv(csv_text)


@app.post("/api/v1/costs/import/csv", response_model=ImportResult, tags=["Cost Tracking"])
async def import_csv(
    file: UploadFile = File(...),
    amount_column: str = "Amount",
    date_column: str = "Date",
    vendor_column: Optional[str] = None,
    description_column: Optional[str] = None,
    category_column: Optional[str] = None,
    reference_column: Optional[str] = None,
    default_tax_year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Import expenses from CSV file.

    Provide column mapping for your QuickBooks export format.
    """
    content = await file.read()
    csv_text = content.decode('utf-8')

    mapping = ColumnMapping(
        amount=amount_column,
        date=date_column,
        vendor=vendor_column,
        description=description_column,
        category=category_column,
        reference=reference_column
    )

    cost_service = get_cost_tracking_service()
    return cost_service.import_csv(
        csv_text,
        mapping,
        user.id,
        file.filename or "upload.csv",
        default_tax_year
    )


@app.post("/api/v1/costs/import/scan", response_model=OCRScanResult, tags=["Cost Tracking"])
async def import_scan(
    file: UploadFile = File(...),
    default_tax_year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Import expenses from scanned image or PDF using OCR.

    Supported formats: JPG, PNG, PDF
    Requires pytesseract and Pillow to be installed.
    """
    content = await file.read()

    cost_service = get_cost_tracking_service()
    expenses, warnings = cost_service.process_ocr_image(
        content,
        user.id,
        file.filename or "scan.jpg",
        default_tax_year
    )

    needs_review = sum(1 for e in expenses if e.ocr_needs_review)

    return OCRScanResult(
        expenses=expenses,
        warnings=warnings,
        needs_review_count=needs_review
    )


@app.get("/api/v1/costs/imports", response_model=List[ImportBatchResponse], tags=["Cost Tracking"])
async def list_import_batches(
    limit: int = 20,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get recent import batches for audit trail."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_import_batches(user.id, limit)


@app.delete("/api/v1/costs/imports/{batch_id}", tags=["Cost Tracking"])
async def rollback_import(
    batch_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """
    Rollback an import batch (delete all imported expenses).

    Requires manager or admin role.
    """
    cost_service = get_cost_tracking_service()
    deleted, error = cost_service.rollback_import(batch_id, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {"message": f"Rolled back {deleted} expenses", "deleted_count": deleted}


# ============================================================================
# COST TRACKING - Column Mappings
# ============================================================================

@app.get("/api/v1/costs/mappings", response_model=List[SavedMappingResponse], tags=["Cost Tracking"])
async def list_column_mappings(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get saved column mappings for this user."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_user_mappings(user.id)


class SaveMappingRequest(BaseModel):
    mapping_name: str
    column_config: ColumnMapping
    source_type: Optional[str] = None
    is_default: bool = False


@app.post("/api/v1/costs/mappings", tags=["Cost Tracking"])
async def save_column_mapping(
    request: SaveMappingRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Save a column mapping for reuse."""
    cost_service = get_cost_tracking_service()
    mapping_id = cost_service.save_column_mapping(
        user.id,
        request.mapping_name,
        request.column_config,
        request.source_type,
        request.is_default
    )
    return {"id": mapping_id, "message": "Mapping saved"}


@app.delete("/api/v1/costs/mappings/{mapping_id}", tags=["Cost Tracking"])
async def delete_column_mapping(
    mapping_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Delete a saved column mapping."""
    cost_service = get_cost_tracking_service()
    deleted = cost_service.delete_column_mapping(mapping_id, user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return {"message": "Mapping deleted"}


# ============================================================================
# COST TRACKING - Expenses CRUD
# ============================================================================

@app.get("/api/v1/costs/expenses", response_model=ExpenseListResponse, tags=["Cost Tracking"])
async def list_expenses(
    tax_year: Optional[int] = None,
    category: Optional[ExpenseCategory] = None,
    vendor: Optional[str] = None,
    unallocated_only: bool = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    List expenses with filters.

    Use unallocated_only=true to see expenses needing field allocation.
    """
    cost_service = get_cost_tracking_service()
    return cost_service.list_expenses(
        user.id,
        tax_year=tax_year,
        category=category,
        vendor=vendor,
        unallocated_only=unallocated_only,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )


@app.post("/api/v1/costs/expenses", response_model=ExpenseResponse, tags=["Cost Tracking"])
async def create_expense(
    expense: ExpenseCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a manual expense entry."""
    cost_service = get_cost_tracking_service()
    result, error = cost_service.create_expense(expense, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/costs/expenses/{expense_id}", response_model=ExpenseWithAllocations, tags=["Cost Tracking"])
async def get_expense(
    expense_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get expense details with allocations."""
    cost_service = get_cost_tracking_service()
    expense = cost_service.get_expense(expense_id)

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    allocations = cost_service.get_allocations(expense_id)

    return ExpenseWithAllocations(expense=expense, allocations=allocations)


@app.put("/api/v1/costs/expenses/{expense_id}", response_model=ExpenseResponse, tags=["Cost Tracking"])
async def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update an expense."""
    cost_service = get_cost_tracking_service()
    result, error = cost_service.update_expense(expense_id, expense, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.delete("/api/v1/costs/expenses/{expense_id}", tags=["Cost Tracking"])
async def delete_expense(
    expense_id: int,
    user: AuthenticatedUser = Depends(require_manager)
):
    """Delete an expense (soft delete). Requires manager role."""
    cost_service = get_cost_tracking_service()
    deleted = cost_service.delete_expense(expense_id, user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Expense deleted"}


# ============================================================================
# COST TRACKING - OCR Review Queue
# ============================================================================

@app.get("/api/v1/costs/review", response_model=List[ExpenseResponse], tags=["Cost Tracking"])
async def get_ocr_review_queue(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get OCR expenses needing manual review."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_expenses_needing_review(user.id)


@app.post("/api/v1/costs/expenses/{expense_id}/approve", response_model=ExpenseResponse, tags=["Cost Tracking"])
async def approve_ocr_expense(
    expense_id: int,
    corrections: Optional[ExpenseUpdate] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Approve an OCR expense after review.

    Optionally provide corrections to apply before approval.
    """
    cost_service = get_cost_tracking_service()
    result, error = cost_service.approve_ocr_expense(expense_id, user.id, corrections)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


# ============================================================================
# COST TRACKING - Allocations
# ============================================================================

@app.get("/api/v1/costs/expenses/{expense_id}/allocations", response_model=List[AllocationResponse], tags=["Cost Tracking"])
async def get_expense_allocations(
    expense_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get allocations for an expense."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_allocations(expense_id)


@app.post("/api/v1/costs/expenses/{expense_id}/allocations", response_model=List[AllocationResponse], tags=["Cost Tracking"])
async def set_expense_allocations(
    expense_id: int,
    allocations: List[AllocationCreate],
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Set allocations for an expense (replaces existing).

    Total allocation_percent across all fields should not exceed 100%.
    """
    cost_service = get_cost_tracking_service()
    result, error = cost_service.set_allocations(expense_id, allocations, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


class SuggestAllocationRequest(BaseModel):
    field_ids: List[int]


@app.post("/api/v1/costs/allocations/suggest", tags=["Cost Tracking"])
async def suggest_allocation(
    request: SuggestAllocationRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Suggest allocation percentages based on field acreage.

    Useful for splitting farm-wide expenses proportionally.
    """
    cost_service = get_cost_tracking_service()
    return cost_service.suggest_allocation_by_acreage(request.field_ids)


@app.get("/api/v1/costs/unallocated", response_model=ExpenseListResponse, tags=["Cost Tracking"])
async def get_unallocated_expenses(
    tax_year: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get expenses that haven't been fully allocated to fields."""
    cost_service = get_cost_tracking_service()
    return cost_service.list_expenses(
        user.id,
        tax_year=tax_year,
        unallocated_only=True
    )


# ============================================================================
# COST TRACKING - Reports
# ============================================================================

@app.get("/api/v1/costs/reports/per-acre", response_model=CostPerAcreReport, tags=["Cost Tracking"])
async def get_cost_per_acre_report(
    crop_year: int,
    field_ids: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get cost per acre report for a crop year.

    Optionally filter by field_ids (comma-separated).
    """
    cost_service = get_cost_tracking_service()

    field_id_list = None
    if field_ids:
        field_id_list = [int(x.strip()) for x in field_ids.split(",")]

    return cost_service.get_cost_per_acre_report(crop_year, field_id_list)


@app.get("/api/v1/costs/reports/by-category", response_model=List[CategoryBreakdown], tags=["Cost Tracking"])
async def get_category_breakdown(
    crop_year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get expense breakdown by category."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_category_breakdown(crop_year, field_id)


@app.get("/api/v1/costs/reports/by-crop", response_model=List[CropCostSummary], tags=["Cost Tracking"])
async def get_cost_by_crop(
    crop_year: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get cost summary grouped by crop type."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_cost_by_crop(crop_year)


class YearComparisonRequest(BaseModel):
    years: List[int]
    field_id: Optional[int] = None


@app.post("/api/v1/costs/reports/comparison", tags=["Cost Tracking"])
async def get_year_comparison(
    request: YearComparisonRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Compare costs across multiple years."""
    cost_service = get_cost_tracking_service()
    return cost_service.get_year_comparison(request.years, request.field_id)


@app.get("/api/v1/costs/categories", tags=["Cost Tracking"])
async def list_expense_categories():
    """Get list of available expense categories."""
    return [
        {"value": cat.value, "name": cat.name.replace("_", " ").title()}
        for cat in ExpenseCategory
    ]


# ============================================================================
# QUICKBOOKS IMPORT (v2.9.0)
# ============================================================================

@app.post("/api/v1/quickbooks/preview", response_model=QBImportPreview, tags=["QuickBooks Import"])
async def preview_quickbooks_import(
    file: UploadFile,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Preview a QuickBooks CSV export before importing.

    Returns:
    - Detected export format (Desktop Transaction Detail, Online, etc.)
    - List of accounts found with suggested category mappings
    - Unmapped accounts that need manual mapping
    - Sample transactions
    - Date range and expense count
    """
    qb_service = get_qb_import_service()
    content = await file.read()
    csv_content = content.decode("utf-8-sig")  # Handle BOM from Excel/QB
    return qb_service.preview_import(csv_content, current_user.user_id)


@app.post("/api/v1/quickbooks/import", response_model=QBImportSummary, tags=["QuickBooks Import"])
async def import_quickbooks_data(
    file: UploadFile,
    account_mappings: str = Form(...),  # JSON string of account -> category mappings
    tax_year: Optional[int] = Form(None),
    save_mappings: bool = Form(True),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Import expenses from a QuickBooks CSV export.

    Requires account_mappings as a JSON string mapping QB accounts to AgTools categories.
    Example: {"Farm Expense:Seed": "seed", "Farm Expense:Fertilizer": "fertilizer"}

    Features:
    - Auto-filters to expense transactions only (skips deposits, transfers)
    - Duplicate detection by reference number + date + amount
    - Saves mappings for future imports if save_mappings=true
    """
    import json

    qb_service = get_qb_import_service()

    # Parse mappings JSON
    try:
        mappings = json.loads(account_mappings)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid account_mappings JSON")

    # Read file
    content = await file.read()
    csv_content = content.decode("utf-8-sig")

    return qb_service.import_quickbooks(
        csv_content=csv_content,
        user_id=current_user.user_id,
        account_mappings=mappings,
        source_file=file.filename or "quickbooks_export.csv",
        tax_year=tax_year,
        save_mappings=save_mappings
    )


@app.get("/api/v1/quickbooks/mappings", response_model=List[QBAccountMapping], tags=["QuickBooks Import"])
async def get_qb_account_mappings(
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get user's saved QuickBooks account mappings."""
    qb_service = get_qb_import_service()
    return qb_service.get_all_user_mappings(current_user.user_id)


@app.post("/api/v1/quickbooks/mappings", tags=["QuickBooks Import"])
async def save_qb_account_mappings(
    mappings: Dict[str, str],
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Save QuickBooks account to AgTools category mappings.

    Body should be a dict of qb_account -> agtools_category.
    Example: {"Farm Expense:Seed": "seed", "Farm Expense:Fertilizer": "fertilizer"}
    """
    qb_service = get_qb_import_service()
    saved = qb_service.save_user_mappings(current_user.user_id, mappings)
    return {"message": f"Saved {saved} mappings", "count": saved}


@app.delete("/api/v1/quickbooks/mappings/{mapping_id}", tags=["QuickBooks Import"])
async def delete_qb_account_mapping(
    mapping_id: int,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Delete a QuickBooks account mapping."""
    qb_service = get_qb_import_service()
    if qb_service.delete_user_mapping(current_user.user_id, mapping_id):
        return {"message": "Mapping deleted"}
    raise HTTPException(status_code=404, detail="Mapping not found")


@app.get("/api/v1/quickbooks/formats", tags=["QuickBooks Import"])
async def get_supported_qb_formats():
    """Get list of supported QuickBooks export formats."""
    qb_service = get_qb_import_service()
    return qb_service.get_supported_formats()


@app.get("/api/v1/quickbooks/default-mappings", tags=["QuickBooks Import"])
async def get_default_qb_mappings():
    """
    Get default QuickBooks account to category mappings.

    These are common mappings that work for many farm operations.
    Users can customize these for their specific chart of accounts.
    """
    from services.quickbooks_import import DEFAULT_QB_MAPPINGS
    return {
        account: category.value
        for account, category in DEFAULT_QB_MAPPINGS.items()
    }


# ============================================================================
# PROFITABILITY ANALYSIS
# ============================================================================

@app.post("/api/v1/profitability/break-even", response_model=BreakEvenResponse, tags=["Profitability"])
async def calculate_break_even(
    request: BreakEvenRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate break-even yields and prices.

    Answers:
    - What yield do I need at price X to break even?
    - What price do I need at yield Y to break even?
    - How much cushion do I have before losing money?
    """
    profit_service = get_profitability_service()
    return profit_service.calculate_break_even(request)


@app.post("/api/v1/profitability/input-roi", response_model=InputROIResponse, tags=["Profitability"])
async def rank_inputs_by_roi(
    request: InputROIRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Rank all inputs by return on investment.

    Identifies:
    - Which inputs give the best return per dollar spent
    - Which inputs to cut first if you need to reduce costs
    - Risk of yield loss for each potential cut
    """
    profit_service = get_profitability_service()
    return profit_service.rank_inputs_by_roi(request)


@app.post("/api/v1/profitability/scenarios", response_model=ScenarioResponse, tags=["Profitability"])
async def run_scenarios(
    request: ScenarioRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Run what-if scenario analysis.

    Models different combinations of:
    - Grain prices (what if corn drops to $4?)
    - Yields (what if we only make 150 bu?)
    - Cost changes (what if fertilizer goes up 20%?)
    """
    profit_service = get_profitability_service()
    return profit_service.run_scenarios(request)


@app.post("/api/v1/profitability/budget", response_model=BudgetTrackerResponse, tags=["Profitability"])
async def track_budget(
    request: BudgetTrackerRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Set up and track budget vs actual spending.

    Features:
    - Set budget targets by category
    - Track spending against targets
    - Get alerts for over-budget categories
    - Project end-of-season profit
    """
    profit_service = get_profitability_service()
    return profit_service.setup_budget_tracker(request)


@app.get("/api/v1/profitability/summary/{crop}", tags=["Profitability"])
async def get_profitability_summary(
    crop: ProfitCropType,
    acres: float,
    expected_yield: Optional[float] = None,
    expected_price: Optional[float] = None,
    cost_per_acre: Optional[float] = None,
    is_irrigated: bool = False,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get a quick profitability summary combining all analyses.

    One call to get:
    - Break-even analysis
    - Input ROI ranking
    - Key scenarios
    - Recommendations
    """
    profit_service = get_profitability_service()
    return profit_service.get_profitability_summary(
        crop=crop,
        acres=acres,
        expected_yield=expected_yield,
        expected_price=expected_price,
        cost_per_acre=cost_per_acre,
        is_irrigated=is_irrigated
    )


@app.get("/api/v1/profitability/crops", tags=["Profitability"])
async def list_supported_crops():
    """Get list of supported crops with their default parameters."""
    from services.profitability_service import CROP_PARAMETERS

    result = []
    for crop_type, params in CROP_PARAMETERS.items():
        result.append({
            "crop": crop_type.value,
            "default_yield": params["default_yield"],
            "yield_unit": params["yield_unit"],
            "default_price": params["default_price"],
            "price_unit": params["price_unit"],
            "typical_yield_range": params["typical_yield_range"],
            "typical_price_range": params["typical_price_range"],
            "total_variable_cost_per_acre": sum(params["variable_costs_per_acre"].values()),
            "irrigation_cost_per_acre": params.get("irrigation_cost_per_acre", 0),
        })
    return result


@app.get("/api/v1/profitability/input-categories", tags=["Profitability"])
async def list_input_categories():
    """Get list of input cost categories."""
    return [
        {"value": cat.value, "name": cat.name.replace("_", " ").title()}
        for cat in InputCategory
    ]


# ============================================================================
# AI/ML INTELLIGENCE SUITE (v3.0)
# ============================================================================

from services.ai_image_service import get_ai_image_service, AIProvider


class AIImageRequest(BaseModel):
    """Request for AI image analysis"""
    crop: str = Field(..., description="Crop type (corn, soybean, wheat, etc.)")
    growth_stage: Optional[str] = Field(None, description="Current growth stage")
    use_local_model: bool = Field(True, description="Use local model if available")
    save_for_training: bool = Field(True, description="Save image for training data")


class AIFeedbackRequest(BaseModel):
    """User feedback on AI prediction"""
    image_hash: str = Field(..., description="Hash of the analyzed image")
    is_correct: bool = Field(..., description="Whether the top prediction was correct")
    correct_label: Optional[str] = Field(None, description="The correct identification if wrong")


@app.post("/api/v1/ai/identify/image", tags=["AI Intelligence"])
async def ai_identify_image(
    image: UploadFile = File(...),
    crop: str = Form("corn"),
    growth_stage: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    AI-based pest/disease identification from uploaded image

    Uses hybrid approach:
    1. Local trained model (if available)
    2. Cloud API (Hugging Face) for analysis
    3. Maps results to our knowledge base

    Returns top 5 matches with confidence scores
    """
    ai_service = get_ai_image_service()

    # Read image bytes
    image_bytes = await image.read()

    # Analyze image
    result = await ai_service.analyze_image(
        image_bytes=image_bytes,
        crop=crop,
        growth_stage=growth_stage,
        use_local_model=True,
        save_for_training=True
    )

    return {
        "provider": result.provider.value,
        "image_hash": result.image_hash,
        "confidence": result.confidence,
        "processing_time_ms": result.processing_time_ms,
        "identifications": result.mapped_identifications,
        "raw_labels": result.raw_labels[:5],  # Top 5 raw labels
        "notes": result.notes,
        "crop": crop,
        "growth_stage": growth_stage
    }


@app.post("/api/v1/ai/feedback", tags=["AI Intelligence"])
async def submit_ai_feedback(
    request: AIFeedbackRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Submit feedback on AI prediction to improve model accuracy

    This feedback is used to:
    - Correct training data labels
    - Track model performance
    - Improve future predictions
    """
    ai_service = get_ai_image_service()

    success = ai_service.submit_feedback(
        image_hash=request.image_hash,
        is_correct=request.is_correct,
        correct_label=request.correct_label,
        user_id=current_user.user_id
    )

    if success:
        return {"status": "success", "message": "Feedback recorded. Thank you for improving our AI!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save feedback")


@app.get("/api/v1/ai/training/stats", tags=["AI Intelligence"])
async def get_ai_training_stats(
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """
    Get statistics about collected AI training data

    Returns:
    - Total images collected
    - Verified vs unverified counts
    - Breakdown by crop and type
    - Prediction accuracy from user feedback
    - Readiness for model training
    """
    ai_service = get_ai_image_service()
    return ai_service.get_training_stats()


@app.post("/api/v1/ai/training/export", tags=["AI Intelligence"])
async def export_ai_training_data(
    output_dir: str = Form("training_export"),
    crop: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(require_admin)
):
    """
    Export verified training data for model training (Admin only)

    Creates organized directory structure:
    - output_dir/label_name/image_hash.jpg
    - output_dir/manifest.json

    Returns export statistics
    """
    ai_service = get_ai_image_service()

    result = ai_service.export_training_data(
        output_dir=output_dir,
        crop=crop
    )

    return {
        "status": "success",
        "exported_to": output_dir,
        **result
    }


@app.get("/api/v1/ai/models", tags=["AI Intelligence"])
async def list_ai_models():
    """
    List available AI models and their capabilities

    Returns information about:
    - Available models (local and cloud)
    - Supported crops and classes
    - Model accuracy metrics
    """
    from services.ai_identification import get_model_info
    return get_model_info()


# ============================================================================
# CROP HEALTH SCORING (v3.0 Phase 2)
# ============================================================================

from services.crop_health_service import get_crop_health_service, ImageType, HealthStatus


@app.post("/api/v1/ai/health/analyze", tags=["Crop Health"])
async def analyze_crop_health(
    image: UploadFile = File(...),
    image_type: str = Form("rgb"),
    field_id: Optional[int] = Form(None),
    field_name: Optional[str] = Form(None),
    grid_size: int = Form(10),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Analyze drone/satellite imagery for crop health

    Processes field imagery to calculate:
    - NDVI (Normalized Difference Vegetation Index)
    - Health scores per zone
    - Problem area detection
    - Treatment recommendations

    Image types supported:
    - rgb: Standard color photos (calculates pseudo-NDVI)
    - ndvi: Pre-calculated NDVI visualization
    - multispectral: Multi-band imagery (NIR, Red, etc.)
    """
    health_service = get_crop_health_service()

    # Read image bytes
    image_bytes = await image.read()

    # Convert image type
    try:
        img_type = ImageType(image_type.lower())
    except ValueError:
        img_type = ImageType.RGB

    # Analyze image
    report = health_service.analyze_image(
        image_bytes=image_bytes,
        image_type=img_type,
        field_id=field_id,
        field_name=field_name,
        grid_size=grid_size,
        save_results=True
    )

    # Convert dataclasses to dicts for JSON response
    return {
        "field_id": report.field_id,
        "field_name": report.field_name,
        "analysis_date": report.analysis_date,
        "image_hash": report.image_hash,
        "image_type": report.image_type.value,
        "overall_ndvi": report.overall_ndvi,
        "overall_health": report.overall_health.value,
        "healthy_percentage": report.healthy_percentage,
        "stressed_percentage": report.stressed_percentage,
        "zones": [
            {
                "zone_id": z.zone_id,
                "center_x": z.center_x,
                "center_y": z.center_y,
                "ndvi_mean": z.ndvi_mean,
                "health_status": z.health_status.value,
                "issue_type": z.issue_type.value if z.issue_type else None,
                "confidence": z.confidence,
                "recommendations": z.recommendations
            }
            for z in report.zones
        ],
        "problem_areas": report.problem_areas,
        "recommendations": report.recommendations,
        "processing_time_ms": report.processing_time_ms,
        "notes": report.notes
    }


@app.get("/api/v1/ai/health/history/{field_id}", tags=["Crop Health"])
async def get_field_health_history(
    field_id: int,
    limit: int = 10,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get health assessment history for a field

    Returns list of past assessments with:
    - Analysis dates
    - NDVI scores
    - Health percentages
    - Recommendations
    """
    health_service = get_crop_health_service()
    return health_service.get_field_history(field_id, limit)


@app.get("/api/v1/ai/health/trends/{field_id}", tags=["Crop Health"])
async def get_field_health_trends(
    field_id: int,
    crop_year: Optional[int] = None,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get health trends for a field over time

    Returns:
    - Time series of NDVI values
    - Healthy/stressed percentages over time
    - Trend summary (improving/declining)
    """
    health_service = get_crop_health_service()
    return health_service.get_health_trends(field_id, crop_year)


@app.get("/api/v1/ai/health/status-levels", tags=["Crop Health"])
async def get_health_status_levels():
    """
    Get health status level definitions

    Returns NDVI thresholds for each health category
    """
    from services.crop_health_service import CropHealthService
    return {
        "levels": [
            {"status": status.value, "min_ndvi": threshold}
            for status, threshold in CropHealthService.NDVI_THRESHOLDS.items()
        ],
        "description": {
            "excellent": "NDVI > 0.7 - Crop is thriving",
            "good": "NDVI 0.5-0.7 - Crop is healthy",
            "moderate": "NDVI 0.3-0.5 - Some stress present",
            "stressed": "NDVI 0.2-0.3 - Significant stress",
            "poor": "NDVI 0.1-0.2 - Severe stress",
            "critical": "NDVI < 0.1 - Critical condition"
        }
    }


# ============================================================================
# YIELD PREDICTION (v3.0 Phase 3)
# ============================================================================

from services.yield_prediction_service import (
    get_yield_prediction_service,
    CropType as YieldCropType,
    ModelType as YieldModelType,
    TrainingData
)


class YieldPredictionRequest(BaseModel):
    """Request for yield prediction"""
    crop: str = Field(..., description="Crop type (corn, soybean, wheat, etc.)")
    field_id: Optional[int] = Field(None, description="Optional field ID")
    field_name: Optional[str] = Field(None, description="Optional field name")
    seeding_rate: Optional[float] = Field(None, description="Seeding rate")
    nitrogen_rate: float = Field(0, description="Nitrogen applied (lbs/acre)")
    phosphorus_rate: float = Field(0, description="P2O5 applied (lbs/acre)")
    potassium_rate: float = Field(0, description="K2O applied (lbs/acre)")
    soil_ph: float = Field(6.5, description="Soil pH")
    organic_matter: float = Field(3.0, description="Organic matter %")
    total_rainfall: Optional[float] = Field(None, description="Growing season rainfall (inches)")
    gdd_accumulated: Optional[float] = Field(None, description="Growing degree days")
    avg_temp: float = Field(70, description="Average temperature")
    irrigation: bool = Field(False, description="Whether field is irrigated")


class YieldHistoryRequest(BaseModel):
    """Request to add historical yield data"""
    crop: str
    crop_year: int
    actual_yield: float
    field_id: Optional[int] = None
    planting_date: Optional[str] = None
    seed_variety: Optional[str] = None
    seeding_rate: Optional[float] = None
    nitrogen_rate: float = 0
    phosphorus_rate: float = 0
    potassium_rate: float = 0
    soil_type: Optional[str] = None
    soil_ph: Optional[float] = None
    organic_matter: Optional[float] = None
    total_rainfall: Optional[float] = None
    gdd_accumulated: Optional[float] = None
    avg_temp: Optional[float] = None
    irrigation: bool = False
    previous_crop: Optional[str] = None
    tillage_type: Optional[str] = None
    moisture_at_harvest: Optional[float] = None


@app.post("/api/v1/ai/yield/predict", tags=["Yield Prediction"])
async def predict_yield(
    request: YieldPredictionRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Predict crop yield based on inputs and conditions

    Uses trained ML model if available, otherwise uses agronomic formulas.
    Returns predicted yield with confidence interval and recommendations.
    """
    yield_service = get_yield_prediction_service()

    try:
        crop = YieldCropType(request.crop.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported crop: {request.crop}")

    prediction = yield_service.predict_yield(
        crop=crop,
        field_id=request.field_id,
        field_name=request.field_name,
        seeding_rate=request.seeding_rate,
        nitrogen_rate=request.nitrogen_rate,
        phosphorus_rate=request.phosphorus_rate,
        potassium_rate=request.potassium_rate,
        soil_ph=request.soil_ph,
        organic_matter=request.organic_matter,
        total_rainfall=request.total_rainfall,
        gdd_accumulated=request.gdd_accumulated,
        avg_temp=request.avg_temp,
        irrigation=request.irrigation
    )

    return {
        "crop": prediction.crop.value,
        "field_id": prediction.field_id,
        "field_name": prediction.field_name,
        "predicted_yield": prediction.predicted_yield,
        "yield_unit": prediction.yield_unit,
        "confidence": {
            "low": prediction.confidence_low,
            "high": prediction.confidence_high,
            "level": prediction.confidence_level
        },
        "factors": prediction.factors,
        "comparison": prediction.comparison,
        "recommendations": prediction.recommendations,
        "model_info": prediction.model_info
    }


@app.post("/api/v1/ai/yield/history", tags=["Yield Prediction"])
async def add_yield_history(
    request: YieldHistoryRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add historical yield data for model training

    More historical data improves prediction accuracy.
    Need at least 10 records per crop to train a model.
    """
    yield_service = get_yield_prediction_service()

    try:
        crop = YieldCropType(request.crop.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported crop: {request.crop}")

    training_data = TrainingData(
        crop=crop,
        crop_year=request.crop_year,
        field_id=request.field_id,
        planting_date=request.planting_date,
        seed_variety=request.seed_variety,
        seeding_rate=request.seeding_rate or 0,
        nitrogen_rate=request.nitrogen_rate,
        phosphorus_rate=request.phosphorus_rate,
        potassium_rate=request.potassium_rate,
        soil_type=request.soil_type,
        soil_ph=request.soil_ph,
        organic_matter=request.organic_matter,
        total_rainfall=request.total_rainfall,
        gdd_accumulated=request.gdd_accumulated,
        avg_temp=request.avg_temp,
        irrigation=request.irrigation,
        previous_crop=request.previous_crop,
        tillage_type=request.tillage_type,
        actual_yield=request.actual_yield,
        moisture_at_harvest=request.moisture_at_harvest
    )

    record_id = yield_service.add_historical_data(training_data)

    return {
        "status": "success",
        "record_id": record_id,
        "message": "Historical yield data added successfully"
    }


@app.post("/api/v1/ai/yield/train/{crop}", tags=["Yield Prediction"])
async def train_yield_model(
    crop: str,
    model_type: str = "random_forest",
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """
    Train yield prediction model for a crop (Manager+ only)

    Requires at least 10 historical yield records for the crop.
    Model types: random_forest, gradient_boosting, linear, ridge
    """
    yield_service = get_yield_prediction_service()

    try:
        crop_type = YieldCropType(crop.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported crop: {crop}")

    try:
        model_type_enum = YieldModelType(model_type.lower())
    except ValueError:
        model_type_enum = YieldModelType.RANDOM_FOREST

    result = yield_service.train_model(crop_type, model_type_enum)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@app.get("/api/v1/ai/yield/models", tags=["Yield Prediction"])
async def get_yield_models():
    """
    Get information about available yield prediction models

    Returns trained models, their accuracy, and supported crops.
    """
    yield_service = get_yield_prediction_service()
    return yield_service.get_model_info()


@app.get("/api/v1/ai/yield/training-stats", tags=["Yield Prediction"])
async def get_yield_training_stats(
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get statistics about available training data

    Shows how many records are available per crop and whether
    there's enough data to train a model.
    """
    yield_service = get_yield_prediction_service()
    return yield_service.get_training_data_stats()


@app.get("/api/v1/ai/yield/crops", tags=["Yield Prediction"])
async def get_supported_crops():
    """
    Get list of supported crops with default parameters

    Returns typical yields, optimal inputs, and units for each crop.
    """
    from services.yield_prediction_service import CROP_DEFAULTS, CropType as YC

    return {
        "crops": [
            {
                "crop": crop.value,
                "yield_unit": params["yield_unit"],
                "typical_yield": params["typical_yield"],
                "yield_range": params["yield_range"],
                "optimal_n": params["optimal_n"],
                "optimal_p": params["optimal_p"],
                "optimal_k": params["optimal_k"],
                "optimal_seeding": params["optimal_seeding"],
                "gdd_requirement": params["gdd_requirement"]
            }
            for crop, params in CROP_DEFAULTS.items()
        ]
    }


# ============================================================================
# SMART EXPENSE CATEGORIZATION (v3.0 Phase 4)
# ============================================================================

from services.expense_categorization_service import (
    get_expense_categorization_service,
    ExpenseCategory as AIExpenseCategory
)


class CategorizationRequest(BaseModel):
    """Request to categorize an expense"""
    description: str = Field(..., description="Expense description")
    vendor: Optional[str] = Field(None, description="Vendor name")
    amount: Optional[float] = Field(None, description="Amount")


class BatchCategorizationRequest(BaseModel):
    """Request to categorize multiple expenses"""
    expenses: List[Dict[str, Any]] = Field(..., description="List of expenses")


class CategorizationCorrectionRequest(BaseModel):
    """Request to correct a categorization"""
    description: str = Field(..., description="Expense description")
    correct_category: str = Field(..., description="Correct category")
    vendor: Optional[str] = Field(None, description="Vendor name")
    amount: Optional[float] = Field(None, description="Amount")


@app.post("/api/v1/ai/categorize/expense", tags=["Expense Categorization"])
async def categorize_expense(
    request: CategorizationRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Auto-categorize an expense from its description

    Uses ML model (if trained) and keyword rules to predict category.
    Returns confidence score and alternative suggestions.
    """
    service = get_expense_categorization_service()

    result = service.categorize(
        description=request.description,
        vendor=request.vendor,
        amount=request.amount
    )

    return {
        "description": result.description,
        "predicted_category": result.predicted_category.value,
        "confidence": result.confidence,
        "alternatives": [
            {"category": cat.value, "confidence": round(conf, 3)}
            for cat, conf in result.alternative_categories
        ],
        "matching_rules": result.matching_rules,
        "vendor_recognized": result.vendor_recognized,
        "vendor_category_history": result.vendor_category_history
    }


@app.post("/api/v1/ai/categorize/batch", tags=["Expense Categorization"])
async def categorize_expenses_batch(
    request: BatchCategorizationRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Auto-categorize multiple expenses at once

    Useful for processing QuickBooks imports or bulk expense entry.
    """
    service = get_expense_categorization_service()

    results = service.categorize_batch(request.expenses)

    return {
        "count": len(results),
        "results": [
            {
                "description": r.description,
                "predicted_category": r.predicted_category.value,
                "confidence": r.confidence,
                "vendor_recognized": r.vendor_recognized
            }
            for r in results
        ]
    }


@app.post("/api/v1/ai/categorize/correct", tags=["Expense Categorization"])
async def submit_categorization_correction(
    request: CategorizationCorrectionRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Submit a correction to improve categorization accuracy

    Corrections are used to train and improve the ML model.
    Also updates vendor-to-category mappings.
    """
    service = get_expense_categorization_service()

    try:
        category = AIExpenseCategory(request.correct_category.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid category: {request.correct_category}")

    success = service.submit_correction(
        description=request.description,
        correct_category=category,
        vendor=request.vendor,
        amount=request.amount,
        user_id=current_user.user_id
    )

    if success:
        return {
            "status": "success",
            "message": "Correction saved. Thank you for improving our AI!"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save correction")


@app.post("/api/v1/ai/categorize/train", tags=["Expense Categorization"])
async def train_categorization_model(
    min_samples: int = 50,
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """
    Train expense categorization ML model (Manager+ only)

    Requires at least 50 categorized expenses to train.
    More training data = better accuracy.
    """
    service = get_expense_categorization_service()

    result = service.train_model(min_samples=min_samples)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@app.get("/api/v1/ai/categorize/stats", tags=["Expense Categorization"])
async def get_categorization_stats(
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get training statistics for expense categorization

    Shows how many samples are available, by category, and
    whether there's enough data to train a model.
    """
    service = get_expense_categorization_service()
    return service.get_training_stats()


@app.get("/api/v1/ai/categorize/categories", tags=["Expense Categorization"])
async def get_expense_categories():
    """
    Get list of available expense categories

    Returns all supported categories for farm expenses.
    """
    service = get_expense_categorization_service()
    return {"categories": service.get_categories()}


@app.post("/api/v1/ai/categorize/suggest-qb", tags=["Expense Categorization"])
async def suggest_category_for_qb_import(
    qb_account: str = Form(...),
    description: str = Form(""),
    vendor: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Suggest category for QuickBooks import

    Analyzes QB account name and description to suggest
    the best expense category for imported transactions.
    """
    service = get_expense_categorization_service()

    result = service.suggest_category_for_import(
        qb_account=qb_account,
        description=description,
        vendor=vendor
    )

    return result


# ============================================================================
# WEATHER-BASED SPRAY AI (v3.0 Phase 5)
# ============================================================================

from services.spray_ai_service import (
    get_spray_ai_service,
    SprayType as AISprayType,
    SprayOutcome,
    SprayApplication
)


class SprayPredictionRequest(BaseModel):
    """Request for spray outcome prediction"""
    spray_type: str = Field(..., description="Type: herbicide, insecticide, fungicide")
    temperature: float = Field(..., description="Temperature in Fahrenheit")
    humidity: float = Field(..., description="Relative humidity %")
    wind_speed: float = Field(..., description="Wind speed in mph")
    rain_chance: float = Field(0, description="Rain probability 0-100")
    time_of_day: str = Field("morning", description="morning, midday, evening, night")
    field_id: Optional[int] = Field(None, description="Field ID for micro-climate")


class SprayRecordRequest(BaseModel):
    """Request to add spray application record"""
    spray_type: str
    product_name: str
    application_date: str
    temperature: float
    humidity: float
    wind_speed: float
    outcome: str
    field_id: Optional[int] = None
    application_time: Optional[str] = None
    wind_direction: Optional[str] = None
    rain_last_24h: float = 0
    rain_next_24h: float = 0
    dew_point: Optional[float] = None
    cloud_cover: Optional[float] = None
    rate_per_acre: Optional[float] = None
    acres_treated: Optional[float] = None
    applicator: Optional[str] = None
    efficacy_rating: Optional[float] = None
    notes: Optional[str] = None


@app.post("/api/v1/ai/spray/predict", tags=["Spray AI"])
async def predict_spray_outcome(
    request: SprayPredictionRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    AI-enhanced spray timing prediction

    Uses ML model (if trained) or rule-based scoring to predict
    spray application success based on weather conditions.
    """
    service = get_spray_ai_service()

    try:
        spray_type = AISprayType(request.spray_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid spray type: {request.spray_type}")

    prediction = service.predict_outcome(
        spray_type=spray_type,
        temperature=request.temperature,
        humidity=request.humidity,
        wind_speed=request.wind_speed,
        rain_chance=request.rain_chance,
        time_of_day=request.time_of_day,
        field_id=request.field_id
    )

    return {
        "spray_type": prediction.spray_type.value,
        "predicted_outcome": prediction.predicted_outcome.value,
        "success_probability": prediction.success_probability,
        "confidence": prediction.confidence,
        "risk_factors": prediction.risk_factors,
        "recommendations": prediction.recommendations,
        "historical_similar": prediction.historical_similar,
        "model_used": prediction.model_used,
        "conditions": prediction.conditions
    }


@app.post("/api/v1/ai/spray/record", tags=["Spray AI"])
async def add_spray_record(
    request: SprayRecordRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add historical spray application record

    Records are used to train and improve the AI model.
    Include outcome for best results.
    """
    service = get_spray_ai_service()

    try:
        spray_type = AISprayType(request.spray_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid spray type: {request.spray_type}")

    try:
        outcome = SprayOutcome(request.outcome.lower())
    except ValueError:
        outcome = SprayOutcome.UNKNOWN

    application = SprayApplication(
        field_id=request.field_id,
        spray_type=spray_type,
        product_name=request.product_name,
        application_date=request.application_date,
        application_time=request.application_time,
        temperature=request.temperature,
        humidity=request.humidity,
        wind_speed=request.wind_speed,
        wind_direction=request.wind_direction,
        rain_last_24h=request.rain_last_24h,
        rain_next_24h=request.rain_next_24h,
        dew_point=request.dew_point,
        cloud_cover=request.cloud_cover,
        rate_per_acre=request.rate_per_acre or 0,
        acres_treated=request.acres_treated or 0,
        applicator=request.applicator,
        outcome=outcome,
        efficacy_rating=request.efficacy_rating,
        notes=request.notes
    )

    record_id = service.add_spray_record(application)

    return {
        "status": "success",
        "record_id": record_id,
        "message": "Spray record added successfully"
    }


@app.post("/api/v1/ai/spray/train/{spray_type}", tags=["Spray AI"])
async def train_spray_model(
    spray_type: str,
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """
    Train spray prediction model (Manager+ only)

    Requires at least 20 historical spray records with outcomes.
    """
    service = get_spray_ai_service()

    try:
        spray_type_enum = AISprayType(spray_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid spray type: {spray_type}")

    result = service.train_model(spray_type_enum)

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))

    return result


@app.get("/api/v1/ai/spray/history", tags=["Spray AI"])
async def get_spray_history_analysis(
    spray_type: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get analysis of historical spray outcomes

    Shows success rates, outcome distribution, and
    average conditions for each outcome type.
    """
    service = get_spray_ai_service()

    spray_type_enum = None
    if spray_type:
        try:
            spray_type_enum = AISprayType(spray_type.lower())
        except ValueError:
            pass

    return service.get_historical_analysis(spray_type_enum)


@app.post("/api/v1/ai/spray/windows", tags=["Spray AI"])
async def find_optimal_spray_windows(
    spray_type: str = Form(...),
    forecast: str = Form(...),  # JSON array of hourly forecasts
    min_success_prob: float = Form(0.7),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Find optimal spray windows in forecast

    Analyzes hourly forecast to find best application times.
    Returns top windows sorted by success probability.
    """
    service = get_spray_ai_service()

    try:
        spray_type_enum = AISprayType(spray_type.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid spray type: {spray_type}")

    try:
        forecast_data = json.loads(forecast)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid forecast JSON")

    windows = service.get_optimal_windows(
        spray_type=spray_type_enum,
        forecast=forecast_data,
        min_success_prob=min_success_prob
    )

    return {
        "spray_type": spray_type_enum.value,
        "min_success_probability": min_success_prob,
        "windows_found": len(windows),
        "optimal_windows": windows
    }


@app.get("/api/v1/ai/spray/types", tags=["Spray AI"])
async def get_spray_types():
    """Get list of supported spray types"""
    return {
        "types": [
            {"value": t.value, "name": t.name.replace("_", " ").title()}
            for t in AISprayType
        ],
        "outcomes": [
            {"value": o.value, "name": o.name.replace("_", " ").title()}
            for o in SprayOutcome
        ]
    }


# ============================================================================
# PDF REPORT GENERATION (v3.1)
# ============================================================================

try:
    from services.pdf_report_service import get_pdf_report_service, ReportConfig
    PDF_SERVICE_AVAILABLE = True
except ImportError:
    PDF_SERVICE_AVAILABLE = False


@app.post("/api/v1/reports/pdf/scouting", tags=["PDF Reports"])
async def generate_scouting_pdf(
    field_name: str = Form(...),
    crop: str = Form(...),
    growth_stage: str = Form(...),
    observations: str = Form("[]"),
    recommendations: str = Form("[]"),
    farm_name: Optional[str] = Form(None),
    prepared_by: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Generate a scouting report PDF"""
    if not PDF_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF service not available. Install reportlab.")

    service = get_pdf_report_service()
    config = ReportConfig(
        title="Field Scouting Report",
        subtitle=f"{field_name} - {crop.title()}",
        farm_name=farm_name,
        prepared_by=prepared_by or current_user.username
    )

    try:
        obs_list = json.loads(observations)
        rec_list = json.loads(recommendations)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pdf_bytes = service.generate_scouting_report(
        field_name=field_name,
        crop=crop,
        growth_stage=growth_stage,
        observations=obs_list,
        recommendations=rec_list,
        config=config
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=scouting_{field_name}_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@app.post("/api/v1/reports/pdf/spray-recommendation", tags=["PDF Reports"])
async def generate_spray_pdf(
    field_name: str = Form(...),
    crop: str = Form(...),
    target_pest: str = Form(...),
    products: str = Form(...),
    economics: str = Form(...),
    weather_window: Optional[str] = Form(None),
    farm_name: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Generate a spray recommendation PDF"""
    if not PDF_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF service not available")

    service = get_pdf_report_service()
    config = ReportConfig(
        title="Spray Recommendation",
        subtitle=f"{target_pest} - {field_name}",
        farm_name=farm_name,
        prepared_by=current_user.username
    )

    try:
        products_list = json.loads(products)
        economics_dict = json.loads(economics)
        weather_dict = json.loads(weather_window) if weather_window else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pdf_bytes = service.generate_spray_recommendation(
        field_name=field_name,
        crop=crop,
        target_pest=target_pest,
        products=products_list,
        economics=economics_dict,
        weather_window=weather_dict,
        config=config
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=spray_rec_{field_name}_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@app.post("/api/v1/reports/pdf/cost-per-acre", tags=["PDF Reports"])
async def generate_cost_pdf(
    crop_year: int = Form(...),
    fields: str = Form(...),
    summary: str = Form(...),
    farm_name: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Generate a cost per acre report PDF"""
    if not PDF_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF service not available")

    service = get_pdf_report_service()
    config = ReportConfig(
        title="Cost Per Acre Report",
        subtitle=f"Crop Year {crop_year}",
        farm_name=farm_name,
        prepared_by=current_user.username
    )

    try:
        fields_list = json.loads(fields)
        summary_dict = json.loads(summary)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pdf_bytes = service.generate_cost_per_acre_report(
        crop_year=crop_year,
        fields=fields_list,
        summary=summary_dict,
        config=config
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cost_per_acre_{crop_year}.pdf"}
    )


@app.post("/api/v1/reports/pdf/profitability", tags=["PDF Reports"])
async def generate_profitability_pdf(
    crop_year: int = Form(...),
    fields: str = Form(...),
    summary: str = Form(...),
    farm_name: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Generate a profitability analysis PDF"""
    if not PDF_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF service not available")

    service = get_pdf_report_service()
    config = ReportConfig(
        title="Profitability Analysis",
        subtitle=f"Crop Year {crop_year}",
        farm_name=farm_name,
        prepared_by=current_user.username
    )

    try:
        fields_list = json.loads(fields)
        summary_dict = json.loads(summary)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pdf_bytes = service.generate_profitability_report(
        crop_year=crop_year,
        fields=fields_list,
        summary=summary_dict,
        config=config
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=profitability_{crop_year}.pdf"}
    )


@app.post("/api/v1/reports/pdf/equipment", tags=["PDF Reports"])
async def generate_equipment_pdf(
    equipment_list: str = Form(...),
    maintenance_alerts: str = Form("[]"),
    summary: str = Form(...),
    farm_name: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Generate an equipment status report PDF"""
    if not PDF_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF service not available")

    service = get_pdf_report_service()
    config = ReportConfig(
        title="Equipment Status Report",
        farm_name=farm_name,
        prepared_by=current_user.username
    )

    try:
        equip_list = json.loads(equipment_list)
        alerts_list = json.loads(maintenance_alerts)
        summary_dict = json.loads(summary)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pdf_bytes = service.generate_equipment_status_report(
        equipment_list=equip_list,
        maintenance_alerts=alerts_list,
        summary=summary_dict,
        config=config
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=equipment_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@app.post("/api/v1/reports/pdf/inventory", tags=["PDF Reports"])
async def generate_inventory_pdf(
    inventory_items: str = Form(...),
    low_stock_alerts: str = Form("[]"),
    expiring_soon: str = Form("[]"),
    summary: str = Form(...),
    farm_name: Optional[str] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Generate an inventory status report PDF"""
    if not PDF_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF service not available")

    service = get_pdf_report_service()
    config = ReportConfig(
        title="Inventory Status Report",
        farm_name=farm_name,
        prepared_by=current_user.username
    )

    try:
        items_list = json.loads(inventory_items)
        low_list = json.loads(low_stock_alerts)
        exp_list = json.loads(expiring_soon)
        summary_dict = json.loads(summary)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pdf_bytes = service.generate_inventory_status_report(
        inventory_items=items_list,
        low_stock_alerts=low_list,
        expiring_soon=exp_list,
        summary=summary_dict,
        config=config
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=inventory_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@app.get("/api/v1/reports/pdf/types", tags=["PDF Reports"])
async def get_pdf_report_types():
    """Get list of available PDF report types"""
    return {
        "available": PDF_SERVICE_AVAILABLE,
        "types": [
            {"type": "scouting", "name": "Scouting Report"},
            {"type": "spray_recommendation", "name": "Spray Recommendation"},
            {"type": "cost_per_acre", "name": "Cost Per Acre"},
            {"type": "profitability", "name": "Profitability Analysis"},
            {"type": "equipment", "name": "Equipment Status"},
            {"type": "inventory", "name": "Inventory Status"},
        ]
    }


# ============================================================================
# EMAIL NOTIFICATIONS (v3.1)
# ============================================================================

try:
    from services.email_notification_service import (
        get_email_notification_service, NotificationType, NotificationPriority
    )
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False


@app.post("/api/v1/notifications/send", tags=["Notifications"])
async def send_notification(
    notification_type: str = Form(...),
    recipients: str = Form(...),
    data: str = Form(...),
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Send a notification email (Manager+ only)"""
    if not EMAIL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Email service not available")

    service = get_email_notification_service()

    try:
        notif_type = NotificationType(notification_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid type: {notification_type}")

    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]
    notification = service.create_notification(notif_type, recipient_list, data_dict)
    return await service.send_notification(notification)


@app.post("/api/v1/notifications/maintenance", tags=["Notifications"])
async def send_maintenance_notification(
    recipients: str = Form(...),
    equipment_name: str = Form(...),
    maintenance_type: str = Form(...),
    due_date: str = Form(...),
    current_hours: float = Form(0),
    is_overdue: bool = Form(False),
    days_overdue: int = Form(0),
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Send maintenance alert email"""
    if not EMAIL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Email service not available")

    service = get_email_notification_service()
    recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]

    return await service.send_maintenance_alert(
        recipients=recipient_list,
        equipment_name=equipment_name,
        maintenance_type=maintenance_type,
        due_date=due_date,
        current_hours=current_hours,
        is_overdue=is_overdue,
        days_overdue=days_overdue
    )


@app.post("/api/v1/notifications/low-stock", tags=["Notifications"])
async def send_low_stock_notification(
    recipients: str = Form(...),
    item_name: str = Form(...),
    category: str = Form(...),
    current_qty: float = Form(...),
    reorder_point: float = Form(...),
    unit: str = Form(""),
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Send low stock alert email"""
    if not EMAIL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Email service not available")

    service = get_email_notification_service()
    recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]

    return await service.send_low_stock_alert(
        recipients=recipient_list,
        item_name=item_name,
        category=category,
        current_qty=current_qty,
        reorder_point=reorder_point,
        unit=unit
    )


@app.post("/api/v1/notifications/spray-window", tags=["Notifications"])
async def send_spray_window_notification(
    recipients: str = Form(...),
    field_name: str = Form(...),
    target_pest: str = Form(...),
    product_name: str = Form(...),
    temperature: float = Form(...),
    wind_speed: float = Form(...),
    humidity: float = Form(...),
    rain_forecast: str = Form("None expected"),
    window_start: str = Form(...),
    window_end: str = Form(...),
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Send spray window alert email"""
    if not EMAIL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Email service not available")

    service = get_email_notification_service()
    recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]

    return await service.send_spray_window_alert(
        recipients=recipient_list,
        field_name=field_name,
        target_pest=target_pest,
        product_name=product_name,
        temperature=temperature,
        wind_speed=wind_speed,
        humidity=humidity,
        rain_forecast=rain_forecast,
        window_start=window_start,
        window_end=window_end
    )


@app.post("/api/v1/notifications/task-assigned", tags=["Notifications"])
async def send_task_notification(
    recipients: str = Form(...),
    task_title: str = Form(...),
    priority: str = Form("normal"),
    due_date: str = Form(...),
    assigned_by: str = Form(...),
    description: str = Form(""),
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Send task assigned notification"""
    if not EMAIL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Email service not available")

    service = get_email_notification_service()
    recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]

    return await service.send_task_assigned_alert(
        recipients=recipient_list,
        task_title=task_title,
        priority=priority,
        due_date=due_date,
        assigned_by=assigned_by,
        description=description
    )


@app.post("/api/v1/notifications/daily-digest", tags=["Notifications"])
async def send_daily_digest_notification(
    recipients: str = Form(...),
    tasks_due: int = Form(0),
    maintenance_alerts: int = Form(0),
    low_stock_count: int = Form(0),
    expiring_count: int = Form(0),
    details: str = Form(""),
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Send daily digest email"""
    if not EMAIL_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Email service not available")

    service = get_email_notification_service()
    recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]

    return await service.send_daily_digest(
        recipients=recipient_list,
        tasks_due=tasks_due,
        maintenance_alerts=maintenance_alerts,
        low_stock_count=low_stock_count,
        expiring_count=expiring_count,
        details=details
    )


@app.get("/api/v1/notifications/types", tags=["Notifications"])
async def get_notification_types():
    """Get list of available notification types"""
    if not EMAIL_SERVICE_AVAILABLE:
        return {"available": False, "types": []}

    service = get_email_notification_service()
    return {"available": True, "types": service.get_notification_types()}


# ============================================================================
# DATA EXPORT ENDPOINTS
# ============================================================================

# Check if export service is available
try:
    from services.data_export_service import get_data_export_service, ExportFormat
    EXPORT_SERVICE_AVAILABLE = True
except ImportError:
    EXPORT_SERVICE_AVAILABLE = False


@app.get("/api/v1/export/fields/{format}", tags=["Export"])
async def export_fields(
    format: str,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Export all fields to CSV or Excel"""
    if not EXPORT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Export service not available")

    from fastapi.responses import Response
    service = get_data_export_service()
    field_service = get_field_service()

    fields = field_service.list_fields()
    field_data = [f.dict() for f in fields]

    export_format = ExportFormat.EXCEL if format.lower() == "excel" else ExportFormat.CSV

    if export_format == ExportFormat.EXCEL:
        content = service.export_fields(field_data, export_format)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=fields.xlsx"}
        )
    else:
        content = service.export_fields(field_data, export_format)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=fields.csv"}
        )


@app.get("/api/v1/export/equipment/{format}", tags=["Export"])
async def export_equipment(
    format: str,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Export all equipment to CSV or Excel"""
    if not EXPORT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Export service not available")

    from fastapi.responses import Response
    service = get_data_export_service()
    equip_service = get_equipment_service()

    equipment = equip_service.list_equipment()
    equip_data = [e.dict() for e in equipment]

    export_format = ExportFormat.EXCEL if format.lower() == "excel" else ExportFormat.CSV

    if export_format == ExportFormat.EXCEL:
        content = service.export_equipment(equip_data, export_format)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=equipment.xlsx"}
        )
    else:
        content = service.export_equipment(equip_data, export_format)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=equipment.csv"}
        )


@app.get("/api/v1/export/inventory/{format}", tags=["Export"])
async def export_inventory(
    format: str,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Export all inventory items to CSV or Excel"""
    if not EXPORT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Export service not available")

    from fastapi.responses import Response
    service = get_data_export_service()
    inv_service = get_inventory_service()

    items = inv_service.list_items()
    item_data = [i.dict() for i in items]

    export_format = ExportFormat.EXCEL if format.lower() == "excel" else ExportFormat.CSV

    if export_format == ExportFormat.EXCEL:
        content = service.export_inventory(item_data, export_format)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=inventory.xlsx"}
        )
    else:
        content = service.export_inventory(item_data, export_format)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory.csv"}
        )


@app.get("/api/v1/export/tasks/{format}", tags=["Export"])
async def export_tasks(
    format: str,
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Export all tasks to CSV or Excel"""
    if not EXPORT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Export service not available")

    from fastapi.responses import Response
    service = get_data_export_service()
    task_service = get_task_service()

    tasks = task_service.list_tasks()
    task_data = [t.dict() for t in tasks]

    export_format = ExportFormat.EXCEL if format.lower() == "excel" else ExportFormat.CSV

    if export_format == ExportFormat.EXCEL:
        content = service.export_tasks(task_data, export_format)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=tasks.xlsx"}
        )
    else:
        content = service.export_tasks(task_data, export_format)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tasks.csv"}
        )


@app.post("/api/v1/export/custom/{format}", tags=["Export"])
async def export_custom_data(
    format: str,
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    sheet_name: str = "Data",
    current_user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Export custom data to CSV or Excel"""
    if not EXPORT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Export service not available")

    from fastapi.responses import Response
    from services.data_export_service import ExportConfig
    service = get_data_export_service()

    config = ExportConfig(sheet_name=sheet_name)
    export_format = ExportFormat.EXCEL if format.lower() == "excel" else ExportFormat.CSV

    if export_format == ExportFormat.EXCEL:
        content = service.export_to_excel(data, columns, config)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={sheet_name.lower().replace(' ', '_')}.xlsx"}
        )
    else:
        content = service.export_to_csv(data, columns, config)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={sheet_name.lower().replace(' ', '_')}.csv"}
        )


@app.get("/api/v1/export/full-report/{format}", tags=["Export"])
async def export_full_farm_report(
    format: str,
    current_user: AuthenticatedUser = Depends(require_manager)
):
    """Export full farm report with all data (Excel only, multiple sheets)"""
    if not EXPORT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Export service not available")

    if format.lower() != "excel":
        raise HTTPException(status_code=400, detail="Full report only available in Excel format")

    from fastapi.responses import Response
    service = get_data_export_service()

    # Gather all data
    field_service = get_field_service()
    equip_service = get_equipment_service()
    inv_service = get_inventory_service()
    task_service = get_task_service()

    sheets = {
        "Fields": [f.dict() for f in field_service.list_fields()],
        "Equipment": [e.dict() for e in equip_service.list_equipment()],
        "Inventory": [i.dict() for i in inv_service.list_items()],
        "Tasks": [t.dict() for t in task_service.list_tasks()],
    }

    content = service.export_multi_sheet(sheets)

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=farm_report.xlsx"}
    )


@app.get("/api/v1/export/status", tags=["Export"])
async def get_export_status():
    """Check export service availability"""
    return {
        "available": EXPORT_SERVICE_AVAILABLE,
        "formats": ["csv", "excel"] if EXPORT_SERVICE_AVAILABLE else [],
        "endpoints": [
            "/api/v1/export/fields/{format}",
            "/api/v1/export/equipment/{format}",
            "/api/v1/export/inventory/{format}",
            "/api/v1/export/tasks/{format}",
            "/api/v1/export/custom/{format}",
            "/api/v1/export/full-report/excel"
        ] if EXPORT_SERVICE_AVAILABLE else []
    }


# ============================================================================
# SUSTAINABILITY METRICS
# ============================================================================

@app.post("/api/v1/sustainability/inputs", response_model=InputUsageResponse, tags=["Sustainability"])
async def record_input_usage(
    data: InputUsageCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record agricultural input usage for sustainability tracking.

    Tracks pesticides, fertilizers, fuel, water, and other inputs.
    Automatically calculates carbon footprint based on EPA emission factors.
    """
    service = get_sustainability_service()
    result, error = service.record_input_usage(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/sustainability/inputs", response_model=List[InputUsageResponse], tags=["Sustainability"])
async def list_input_usage(
    field_id: Optional[int] = None,
    category: Optional[SustainabilityInputCategory] = None,
    year: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List input usage records with optional filters"""
    service = get_sustainability_service()
    return service.list_input_usage(
        field_id=field_id,
        category=category,
        start_date=start_date,
        end_date=end_date,
        year=year
    )


@app.get("/api/v1/sustainability/inputs/summary", response_model=List[InputSummary], tags=["Sustainability"])
async def get_input_summary(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summarized input usage by category for a year"""
    service = get_sustainability_service()
    return service.get_input_summary(year, field_id)


@app.post("/api/v1/sustainability/carbon", response_model=CarbonEntryResponse, tags=["Sustainability"])
async def record_carbon_entry(
    data: CarbonEntryCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a carbon emission or sequestration event.

    Use positive values for emissions, negative for sequestration.
    Carbon from inputs is automatically calculated when recording input usage.
    """
    service = get_sustainability_service()
    result, error = service.record_carbon_entry(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/sustainability/carbon/summary", response_model=CarbonSummary, tags=["Sustainability"])
async def get_carbon_summary(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get carbon footprint summary for a year.

    Includes total emissions, sequestration, net carbon, and breakdown by source.
    Supports climate-smart agriculture documentation.
    """
    service = get_sustainability_service()
    return service.get_carbon_summary(year, field_id)


@app.post("/api/v1/sustainability/water", response_model=WaterUsageResponse, tags=["Sustainability"])
async def record_water_usage(
    data: WaterUsageCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record water usage for irrigation tracking"""
    service = get_sustainability_service()
    result, error = service.record_water_usage(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/sustainability/water/summary", response_model=WaterSummary, tags=["Sustainability"])
async def get_water_summary(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get water usage summary with efficiency metrics"""
    service = get_sustainability_service()
    return service.get_water_summary(year, field_id)


@app.post("/api/v1/sustainability/practices", response_model=PracticeRecordResponse, tags=["Sustainability"])
async def record_sustainability_practice(
    data: PracticeRecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record adoption of a sustainability practice.

    Supported practices include: cover crops, no-till, reduced tillage,
    crop rotation, IPM, precision application, variable rate technology,
    buffer strips, pollinator habitat, and more.

    Carbon benefits are automatically calculated based on USDA/NRCS estimates.
    """
    service = get_sustainability_service()
    result, error = service.record_practice(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/sustainability/practices", response_model=List[PracticeRecordResponse], tags=["Sustainability"])
async def list_sustainability_practices(
    year: Optional[int] = None,
    field_id: Optional[int] = None,
    practice: Optional[SustainabilityPractice] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List sustainability practices with optional filters"""
    service = get_sustainability_service()
    return service.list_practices(year=year, field_id=field_id, practice=practice)


@app.get("/api/v1/sustainability/practices/types", tags=["Sustainability"])
async def list_practice_types():
    """Get list of all available sustainability practice types"""
    return {
        "practices": [
            {"value": p.value, "label": p.value.replace("_", " ").title()}
            for p in SustainabilityPractice
        ]
    }


@app.get("/api/v1/sustainability/scorecard", response_model=SustainabilityScorecard, tags=["Sustainability"])
async def get_sustainability_scorecard(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate a comprehensive sustainability scorecard.

    Scores are calculated based on:
    - Carbon footprint (30% weight)
    - Input efficiency (25% weight)
    - Water efficiency (15% weight)
    - Practice adoption (20% weight)
    - Biodiversity support (10% weight)

    Includes year-over-year comparison and improvement recommendations.
    """
    service = get_sustainability_service()
    return service.generate_scorecard(year, field_id)


@app.get("/api/v1/sustainability/scores/history", tags=["Sustainability"])
async def get_sustainability_history(
    field_id: Optional[int] = None,
    years: int = 5,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get historical sustainability scores for trend analysis"""
    service = get_sustainability_service()
    return service.get_historical_scores(field_id, years)


@app.get("/api/v1/sustainability/report", response_model=SustainabilityReport, tags=["Sustainability"])
async def generate_sustainability_report(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate a comprehensive sustainability report.

    Includes:
    - Full sustainability scorecard with grades
    - Carbon footprint analysis
    - Input usage summary
    - Water efficiency metrics
    - Practice adoption documentation
    - Historical trends
    - Research metrics (total managed acres, carbon sequestered, etc.)
    - Improvement recommendations
    """
    service = get_sustainability_service()
    return service.generate_grant_report(year, field_id)


@app.get("/api/v1/sustainability/export", tags=["Sustainability"])
async def export_sustainability_data(
    year: int,
    field_id: Optional[int] = None,
    format: str = "json",
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Export sustainability data in research-ready format.

    Designed for academic research and documentation.
    Includes metadata, summary statistics, and detailed records.
    """
    service = get_sustainability_service()
    return service.export_research_data(year, field_id, format)


@app.get("/api/v1/sustainability/carbon-factors", tags=["Sustainability"])
async def get_carbon_emission_factors():
    """
    Get the carbon emission factors used for calculations.

    Sources: EPA, IPCC, USDA
    """
    from services.sustainability_service import CARBON_FACTORS
    return {
        "factors": CARBON_FACTORS,
        "sources": [
            "EPA Emission Factors for Greenhouse Gas Inventories",
            "IPCC Guidelines for National Greenhouse Gas Inventories",
            "USDA NRCS Conservation Practice Standards"
        ],
        "units": {
            "fuel": "kg CO2e per gallon",
            "fertilizer": "kg CO2e per lb of nutrient",
            "pesticide": "kg CO2e per lb active ingredient",
            "sequestration": "kg CO2e per acre per year (negative = capture)"
        }
    }


@app.get("/api/v1/sustainability/input-categories", tags=["Sustainability"])
async def list_input_categories():
    """Get list of all input categories for sustainability tracking"""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in SustainabilityInputCategory
        ]
    }


@app.get("/api/v1/sustainability/carbon-sources", tags=["Sustainability"])
async def list_carbon_sources():
    """Get list of all carbon emission/sequestration sources"""
    return {
        "sources": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in CarbonSource
        ]
    }


# ============================================================================
# CLIMATE & WEATHER DATA
# ============================================================================

@app.post("/api/v1/climate/gdd", response_model=GDDRecordResponse, tags=["Climate"])
async def record_gdd(
    data: GDDRecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record daily high/low temperatures for GDD tracking.

    Growing Degree Days (GDD) are automatically calculated for:
    - Corn (base 50°F)
    - Soybean (base 50°F)
    - Wheat (base 40°F)
    """
    service = get_climate_service()
    result, error = service.record_gdd(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/climate/gdd", response_model=List[GDDRecordResponse], tags=["Climate"])
async def list_gdd_records(
    field_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List GDD records for a field"""
    service = get_climate_service()
    return service.list_gdd_records(field_id, start_date, end_date)


@app.get("/api/v1/climate/gdd/accumulated", tags=["Climate"])
async def get_accumulated_gdd(
    field_id: int,
    crop_type: str,
    planting_date: date,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get accumulated GDD from planting date.

    Returns total GDD and daily entries with cumulative totals.
    """
    service = get_climate_service()
    accumulated, entries = service.get_accumulated_gdd(field_id, crop_type, planting_date, end_date)
    return {
        "field_id": field_id,
        "crop_type": crop_type,
        "planting_date": planting_date.isoformat(),
        "end_date": (end_date or date.today()).isoformat(),
        "accumulated_gdd": accumulated,
        "daily_entries": [e.model_dump() for e in entries]
    }


@app.get("/api/v1/climate/gdd/summary", response_model=GDDSummary, tags=["Climate"])
async def get_gdd_summary(
    field_id: int,
    crop_type: str,
    planting_date: date,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get GDD summary with crop stage predictions.

    Includes current stage, next stage, days to maturity,
    and projected maturity date based on recent GDD accumulation.
    """
    service = get_climate_service()
    return service.get_gdd_summary(field_id, crop_type, planting_date)


@app.get("/api/v1/climate/gdd/stages", tags=["Climate"])
async def get_crop_gdd_stages(crop_type: str = "corn"):
    """Get GDD stages for a crop type"""
    stages = CORN_GDD_STAGES if crop_type.lower() == "corn" else SOYBEAN_GDD_STAGES
    return {
        "crop_type": crop_type,
        "base_temp_f": GDD_BASE_TEMPS.get(crop_type.lower(), 50),
        "stages": [
            {"stage": k.replace("_", " ").title(), "gdd_required": v}
            for k, v in sorted(stages.items(), key=lambda x: x[1])
        ]
    }


@app.get("/api/v1/climate/gdd/base-temps", tags=["Climate"])
async def get_gdd_base_temps():
    """Get base temperatures for all supported crops"""
    return {
        "crops": [
            {"crop": k, "base_temp_f": v}
            for k, v in GDD_BASE_TEMPS.items()
        ]
    }


@app.post("/api/v1/climate/precipitation", response_model=PrecipitationResponse, tags=["Climate"])
async def record_precipitation(
    data: PrecipitationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record a precipitation event"""
    service = get_climate_service()
    result, error = service.record_precipitation(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/climate/precipitation", response_model=List[PrecipitationResponse], tags=["Climate"])
async def list_precipitation(
    field_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List precipitation records with optional filters"""
    service = get_climate_service()
    return service.list_precipitation(field_id, start_date, end_date)


@app.get("/api/v1/climate/precipitation/summary", response_model=PrecipitationSummary, tags=["Climate"])
async def get_precipitation_summary(
    start_date: date,
    end_date: date,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get precipitation summary for a period.

    Includes total rainfall, rain days, averages, and monthly breakdown.
    """
    service = get_climate_service()
    return service.get_precipitation_summary(start_date, end_date, field_id)


@app.get("/api/v1/climate/precipitation/types", tags=["Climate"])
async def list_precipitation_types():
    """Get list of precipitation types"""
    return {
        "types": [
            {"value": t.value, "label": t.value.title()}
            for t in PrecipitationType
        ]
    }


@app.get("/api/v1/climate/summary", response_model=ClimateSummary, tags=["Climate"])
async def get_climate_summary(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get annual climate summary.

    Comprehensive climate metrics including:
    - Temperature statistics (highs, lows, extremes)
    - Heat and cold stress days
    - Frost dates and frost-free season
    - Precipitation totals
    - GDD accumulation
    """
    service = get_climate_service()
    return service.get_climate_summary(year, field_id)


@app.get("/api/v1/climate/compare", response_model=ClimateComparison, tags=["Climate"])
async def compare_climate_years(
    years: str,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Compare climate data across multiple years.

    Pass years as comma-separated values (e.g., "2022,2023,2024").
    Returns metrics comparison and trends.
    """
    year_list = [int(y.strip()) for y in years.split(",")]
    service = get_climate_service()
    return service.compare_years(year_list, field_id)


@app.get("/api/v1/climate/export", tags=["Climate"])
async def export_climate_data(
    year: int,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Export climate data for research documentation.

    Includes climate summary, GDD records, and precipitation records.
    """
    service = get_climate_service()
    return service.export_climate_data(year, field_id)


# ============================================================================
# FIELD TRIAL & RESEARCH TOOLS
# ============================================================================

@app.post("/api/v1/research/trials", response_model=TrialResponse, tags=["Research"])
async def create_trial(
    data: TrialCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a new field trial.

    Supports multiple experimental designs:
    - Completely Randomized Design (CRD)
    - Randomized Complete Block Design (RCBD)
    - Split-plot and Strip-plot designs
    - Simple paired comparisons
    """
    service = get_research_service()
    result, error = service.create_trial(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/research/trials", response_model=List[TrialResponse], tags=["Research"])
async def list_trials(
    year: Optional[int] = None,
    trial_type: Optional[TrialType] = None,
    field_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List field trials with optional filters"""
    service = get_research_service()
    return service.list_trials(year, trial_type, field_id)


@app.get("/api/v1/research/trials/{trial_id}", response_model=TrialResponse, tags=["Research"])
async def get_trial(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get a specific trial by ID"""
    service = get_research_service()
    result = service.get_trial(trial_id)

    if not result:
        raise HTTPException(status_code=404, detail="Trial not found")

    return result


@app.put("/api/v1/research/trials/{trial_id}", response_model=TrialResponse, tags=["Research"])
async def update_trial(
    trial_id: int,
    data: TrialUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update a trial"""
    service = get_research_service()
    result, error = service.update_trial(trial_id, data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.post("/api/v1/research/trials/{trial_id}/treatments", response_model=TreatmentResponse, tags=["Research"])
async def add_treatment(
    trial_id: int,
    data: TreatmentCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Add a treatment to a trial"""
    if data.trial_id != trial_id:
        data.trial_id = trial_id

    service = get_research_service()
    result, error = service.add_treatment(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/research/trials/{trial_id}/treatments", response_model=List[TreatmentResponse], tags=["Research"])
async def list_treatments(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List treatments for a trial"""
    service = get_research_service()
    return service.list_treatments(trial_id)


@app.post("/api/v1/research/trials/{trial_id}/plots", response_model=PlotResponse, tags=["Research"])
async def add_plot(
    trial_id: int,
    data: PlotCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Add a plot to a trial"""
    if data.trial_id != trial_id:
        data.trial_id = trial_id

    service = get_research_service()
    result, error = service.add_plot(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/research/trials/{trial_id}/plots", response_model=List[PlotResponse], tags=["Research"])
async def list_plots(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List plots for a trial"""
    service = get_research_service()
    return service.list_plots(trial_id)


@app.post("/api/v1/research/trials/{trial_id}/generate-plots", tags=["Research"])
async def generate_plots(
    trial_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Auto-generate plots based on treatments and replications.

    Creates all plots for the trial based on the number of treatments
    and replications defined in the trial.
    """
    service = get_research_service()
    count, error = service.generate_plots(trial_id, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {"message": f"Generated {count} plots", "plots_created": count}


@app.post("/api/v1/research/measurements", response_model=MeasurementResponse, tags=["Research"])
async def record_measurement(
    data: MeasurementCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a measurement for a plot.

    Supports standard measurement types (yield, plant population, etc.)
    as well as custom measurements.
    """
    service = get_research_service()
    result, error = service.record_measurement(data, user.id)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return result


@app.get("/api/v1/research/trials/{trial_id}/measurements", response_model=List[MeasurementResponse], tags=["Research"])
async def list_measurements(
    trial_id: int,
    measurement_type: Optional[MeasurementType] = None,
    plot_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List measurements for a trial"""
    service = get_research_service()
    return service.list_measurements(trial_id, measurement_type, plot_id)


@app.get("/api/v1/research/trials/{trial_id}/analyze", response_model=TrialAnalysis, tags=["Research"])
async def analyze_trial(
    trial_id: int,
    measurement_type: MeasurementType,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Perform statistical analysis on trial data.

    Calculates treatment means, performs t-tests for pairwise comparisons,
    and provides LSD values for significance testing.
    """
    service = get_research_service()
    result = service.analyze_trial(trial_id, measurement_type)

    if not result:
        raise HTTPException(status_code=404, detail="No data available for analysis")

    return result


@app.get("/api/v1/research/trials/{trial_id}/export", tags=["Research"])
async def export_trial_data(
    trial_id: int,
    include_analysis: bool = True,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Export complete trial data for research documentation.

    Includes trial details, treatments, plots, measurements,
    and optional statistical analysis.
    """
    service = get_research_service()
    result = service.export_trial_data(trial_id, include_analysis)

    if not result:
        raise HTTPException(status_code=404, detail="Trial not found")

    return result.model_dump()


@app.get("/api/v1/research/trial-types", tags=["Research"])
async def list_trial_types():
    """Get list of available trial types"""
    return {
        "types": [
            {"value": t.value, "label": t.value.replace("_", " ").title()}
            for t in TrialType
        ]
    }


@app.get("/api/v1/research/experimental-designs", tags=["Research"])
async def list_experimental_designs():
    """Get list of available experimental designs"""
    return {
        "designs": [
            {"value": d.value, "label": d.value.replace("_", " ").title()}
            for d in ExperimentalDesign
        ]
    }


@app.get("/api/v1/research/measurement-types", tags=["Research"])
async def list_measurement_types():
    """Get list of available measurement types"""
    return {
        "types": [
            {"value": m.value, "label": m.value.replace("_", " ").title()}
            for m in MeasurementType
        ]
    }


# ============================================================================
# GRANT SUPPORT & COMPLIANCE ROUTES (v3.5.0)
# ============================================================================

# Pydantic models for Grant API
class PracticeImplementationCreate(BaseModel):
    practice_code: str = Field(..., description="NRCS practice code (e.g., '340' for Cover Crop)")
    field_id: str
    field_name: str
    acres: float
    start_date: date
    notes: str = ""
    gps_coordinates: Optional[Dict[str, float]] = None


class PracticeDocumentCreate(BaseModel):
    document_type: str = Field(..., description="Type of document (e.g., 'Seed receipts', 'Photos')")
    document_path: str
    document_date: date


class PracticeVerificationCreate(BaseModel):
    verifier: str
    verification_date: date
    passed: bool
    notes: str = ""


class CarbonCalculationRequest(BaseModel):
    practice_code: str
    acres: float
    years: int = 5


class BenchmarkComparisonRequest(BaseModel):
    metric: str
    farm_value: float
    county: str = "Louisiana"


class BenchmarkReportRequest(BaseModel):
    farm_metrics: Dict[str, float]
    farm_name: str = "Farm"


class SAREReportRequest(BaseModel):
    farm_name: str
    project_title: str
    project_description: str
    practices_implemented: List[str]
    metrics: Dict[str, Any] = {}


class SBIRMetricsRequest(BaseModel):
    product_name: str = "AgTools"
    version: str = "3.5.0"
    features: Optional[List[str]] = None


class CIGReportRequest(BaseModel):
    farm_name: str
    project_title: str
    reporting_period: Dict[str, str]
    climate_smart_practices: List[str]


class EQIPApplicationRequest(BaseModel):
    farm_name: str
    farm_acres: float
    priority_resource_concerns: List[str]
    planned_practices: List[str]


class GrantReadinessRequest(BaseModel):
    farm_name: str
    farm_acres: float
    years_in_operation: int
    current_practices: List[str]
    farm_metrics: Dict[str, float]
    target_grants: Optional[List[str]] = None


# ----- NRCS Practice Endpoints -----

@app.get("/api/v1/grants/nrcs-practices", tags=["Grant Support"])
async def get_all_nrcs_practices(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get all available NRCS conservation practices.

    Returns complete list of 15 tracked practices with codes, payment rates,
    carbon benefits, and environmental scores.
    """
    service = get_grant_service()
    return service.get_all_nrcs_practices()


@app.get("/api/v1/grants/nrcs-practices/{code}", tags=["Grant Support"])
async def get_nrcs_practice(
    code: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get details for a specific NRCS practice by code"""
    service = get_grant_service()
    result = service.get_practice_by_code(code)
    if not result:
        raise HTTPException(status_code=404, detail=f"Practice code {code} not found")
    return result


@app.get("/api/v1/grants/nrcs-practices/program/{program}", tags=["Grant Support"])
async def get_practices_by_program(
    program: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get NRCS practices eligible for a specific program.

    Programs: EQIP, CSP, CRP, CIG
    """
    service = get_grant_service()
    return service.get_practices_by_program(program)


@app.post("/api/v1/grants/practices/implement", tags=["Grant Support"])
async def record_practice_implementation(
    data: PracticeImplementationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record implementation of an NRCS conservation practice.

    Creates a trackable record with estimated payments and carbon benefits.
    """
    service = get_grant_service()
    return service.record_practice_implementation(
        practice_code=data.practice_code,
        field_id=data.field_id,
        field_name=data.field_name,
        acres=data.acres,
        start_date=data.start_date,
        notes=data.notes,
        gps_coordinates=data.gps_coordinates
    )


@app.post("/api/v1/grants/practices/{implementation_id}/document", tags=["Grant Support"])
async def add_practice_documentation(
    implementation_id: str,
    data: PracticeDocumentCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add documentation to a practice implementation.

    Tracks required documents for grant compliance verification.
    """
    service = get_grant_service()
    result = service.add_practice_documentation(
        implementation_id=implementation_id,
        document_type=data.document_type,
        document_path=data.document_path,
        document_date=data.document_date
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/v1/grants/practices/{implementation_id}/verify", tags=["Grant Support"])
async def verify_practice(
    implementation_id: str,
    data: PracticeVerificationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record verification of a practice implementation.

    Marks practice as verified for payment eligibility.
    """
    service = get_grant_service()
    result = service.verify_practice(
        implementation_id=implementation_id,
        verifier=data.verifier,
        verification_date=data.verification_date,
        passed=data.passed,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/grants/practices/summary", tags=["Grant Support"])
async def get_practice_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get summary of all implemented conservation practices.

    Includes totals by practice, status, payments, and carbon benefits.
    """
    service = get_grant_service()
    return service.get_practice_summary()


# ----- Carbon Credit Endpoints -----

@app.get("/api/v1/grants/carbon-programs", tags=["Grant Support"])
async def get_carbon_programs(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get all available carbon credit programs.

    Returns 8 programs with price ranges, requirements, and eligible practices:
    Nori, Indigo Ag, Bayer Carbon, Cargill RegenConnect, Corteva, Nutrien, Gradable, Truterra
    """
    service = get_grant_service()
    return service.get_carbon_programs()


@app.post("/api/v1/grants/carbon-credits/calculate", tags=["Grant Support"])
async def calculate_carbon_credits(
    data: CarbonCalculationRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate potential carbon credit revenue for a practice.

    Shows eligible programs with price ranges and total revenue potential.
    """
    service = get_grant_service()
    result = service.calculate_carbon_credits(
        practice_code=data.practice_code,
        acres=data.acres,
        years=data.years
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/grants/carbon-credits/portfolio", tags=["Grant Support"])
async def get_carbon_portfolio(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate total carbon credit potential for all implemented practices.

    Aggregates all practices to show total CO2e sequestration and revenue potential.
    """
    service = get_grant_service()
    return service.calculate_farm_carbon_portfolio()


# ----- Benchmark Endpoints -----

@app.get("/api/v1/grants/benchmarks", tags=["Grant Support"])
async def get_available_benchmarks(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get list of available benchmark metrics.

    Includes yield, efficiency, sustainability, and economic benchmarks
    with Louisiana, Delta region, and national averages.
    """
    service = get_grant_service()
    return service.get_available_benchmarks()


@app.post("/api/v1/grants/benchmarks/compare", tags=["Grant Support"])
async def compare_to_benchmarks(
    data: BenchmarkComparisonRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Compare farm metric to regional and national benchmarks.

    Returns percentile ranking and interpretation.
    """
    service = get_grant_service()
    result = service.compare_to_benchmarks(
        metric=data.metric,
        farm_value=data.farm_value,
        county=data.county
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/grants/benchmarks/report", tags=["Grant Support"])
async def generate_benchmark_report(
    data: BenchmarkReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate comprehensive benchmark comparison report.

    Shows strengths, opportunities, and overall percentile across all metrics.
    """
    service = get_grant_service()
    return service.generate_benchmark_report(
        farm_metrics=data.farm_metrics,
        farm_name=data.farm_name
    )


# ----- Grant Reporting Endpoints -----

@app.post("/api/v1/grants/reports/sare", tags=["Grant Support"])
async def generate_sare_report(
    data: SAREReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate report formatted for SARE grant application.

    Includes sustainable practices, environmental impact, and outreach plan sections.
    """
    service = get_grant_service()
    return service.generate_sare_report(
        farm_name=data.farm_name,
        project_title=data.project_title,
        project_description=data.project_description,
        practices_implemented=data.practices_implemented,
        metrics=data.metrics
    )


@app.post("/api/v1/grants/reports/sbir-metrics", tags=["Grant Support"])
async def generate_sbir_metrics(
    data: SBIRMetricsRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate metrics section for SBIR/STTR applications.

    Includes innovation metrics, commercialization potential, and societal benefits.
    """
    service = get_grant_service()
    return service.generate_sbir_metrics(
        product_name=data.product_name,
        version=data.version,
        features=data.features
    )


@app.post("/api/v1/grants/reports/cig", tags=["Grant Support"])
async def generate_cig_report(
    data: CIGReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate compliance report for Conservation Innovation Grant.

    Includes climate-smart agriculture practices and GHG reduction metrics.
    """
    service = get_grant_service()
    return service.generate_cig_compliance_report(
        farm_name=data.farm_name,
        project_title=data.project_title,
        reporting_period=data.reporting_period,
        climate_smart_practices=data.climate_smart_practices
    )


@app.post("/api/v1/grants/reports/eqip", tags=["Grant Support"])
async def generate_eqip_application(
    data: EQIPApplicationRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate data package for EQIP application.

    Includes practice analysis, payment estimates, and environmental benefit scores.
    """
    service = get_grant_service()
    return service.generate_eqip_application_data(
        farm_name=data.farm_name,
        farm_acres=data.farm_acres,
        priority_resource_concerns=data.priority_resource_concerns,
        planned_practices=data.planned_practices
    )


# ----- Grant Readiness Assessment -----

@app.post("/api/v1/grants/readiness", tags=["Grant Support"])
async def assess_grant_readiness(
    data: GrantReadinessRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Comprehensive assessment of readiness for various grant programs.

    Analyzes readiness for USDA SBIR, SARE, CIG, and EQIP programs.
    Returns scores, requirements met/missing, and priority actions.
    """
    service = get_grant_service()
    return service.assess_grant_readiness(
        farm_name=data.farm_name,
        farm_acres=data.farm_acres,
        years_in_operation=data.years_in_operation,
        current_practices=data.current_practices,
        farm_metrics=data.farm_metrics,
        target_grants=data.target_grants
    )


@app.get("/api/v1/grants/programs", tags=["Grant Support"])
async def list_grant_programs():
    """Get list of supported grant programs"""
    return {
        "programs": [
            {
                "id": "usda_sbir",
                "name": "USDA SBIR/STTR",
                "funding_range": "$125,000 - $650,000",
                "description": "Technology commercialization funding"
            },
            {
                "id": "sare_producer",
                "name": "SARE Producer Grant",
                "funding_range": "$10,000 - $30,000",
                "description": "Farmer-led sustainable agriculture research"
            },
            {
                "id": "cig",
                "name": "Conservation Innovation Grant",
                "funding_range": "Varies",
                "description": "Climate-smart agriculture innovation"
            },
            {
                "id": "eqip",
                "name": "EQIP",
                "funding_range": "Up to $450,000",
                "description": "Environmental quality incentives for conservation"
            },
            {
                "id": "csp",
                "name": "CSP",
                "funding_range": "Annual payments",
                "description": "Conservation stewardship payments"
            },
            {
                "id": "la_on_farm",
                "name": "Louisiana On Farm Grant",
                "funding_range": "Up to $50,000",
                "description": "Louisiana on-farm research funding"
            }
        ]
    }


@app.get("/api/v1/grants/resource-concerns", tags=["Grant Support"])
async def list_resource_concerns():
    """Get list of NRCS resource concerns for EQIP applications"""
    return {
        "resource_concerns": [
            {"id": "soil_erosion", "name": "Soil Erosion", "practices": ["340", "329", "330", "412"]},
            {"id": "water_quality", "name": "Water Quality", "practices": ["590", "393", "391", "412"]},
            {"id": "soil_health", "name": "Soil Health", "practices": ["340", "329", "328", "484"]},
            {"id": "wildlife_habitat", "name": "Wildlife Habitat", "practices": ["420", "393", "391"]},
            {"id": "air_quality", "name": "Air Quality", "practices": ["329", "345", "340"]}
        ]
    }


# ============================================================================
# GRANT ENHANCEMENT ROUTES (v3.6.0)
# ============================================================================

# Pydantic models for Grant Enhancement API
class TechnologyInvestmentCreate(BaseModel):
    technology: str = Field(..., description="Technology ID (e.g., 'autosteer', 'section_control_planter')")
    purchase_year: int
    purchase_cost: float
    annual_subscription: float = 0
    acres_covered: float
    expected_life_years: int = 10
    notes: str = ""


class TechnologyROIRequest(BaseModel):
    technology: str
    acres: float
    purchase_cost: Optional[float] = None
    annual_subscription: Optional[float] = None
    years: int = 5
    corn_price: float = 5.00
    soybean_price: float = 12.00
    base_corn_yield: float = 180
    base_soybean_yield: float = 50


class PortfolioROIRequest(BaseModel):
    technologies: List[str]
    acres: float
    years: int = 5


class EconomicImpactReportRequest(BaseModel):
    farm_name: str
    technologies: List[str]
    acres: float
    years_of_data: int = 3


class DataAvailabilityCreate(BaseModel):
    category: str = Field(..., description="Data category (e.g., 'yield_data', 'soil_tests')")
    years_available: List[int]
    completeness_pct: float = Field(..., ge=0, le=100)
    format: str = Field(..., description="Data format (e.g., 'JD Operations Center', 'CSV')")
    last_updated: date
    notes: str = ""


class DataQualityReportRequest(BaseModel):
    farm_name: str
    target_grants: Optional[List[str]] = None


class PartnershipSearchRequest(BaseModel):
    farm_capabilities: List[str] = Field(..., description="Research areas (e.g., 'precision_agriculture', 'sustainability')")
    target_grants: Optional[List[str]] = None
    preferred_partner_types: Optional[List[str]] = None
    state: str = "LA"


class PartnershipReportRequest(BaseModel):
    farm_name: str
    farm_capabilities: List[str]
    target_grants: List[str]
    state: str = "LA"


# ----- Economic Impact Calculator Endpoints -----

@app.get("/api/v1/grants/technologies", tags=["Grant Enhancement"])
async def get_technology_catalog(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get catalog of precision ag technologies with benefit rates.

    Returns 14 technologies with input savings, yield improvement,
    time savings, and typical costs.
    """
    service = get_grant_enhancement_service()
    return service.get_technology_catalog()


@app.post("/api/v1/grants/technologies/invest", tags=["Grant Enhancement"])
async def record_technology_investment(
    data: TechnologyInvestmentCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a precision ag technology investment.

    Calculates annual benefits, costs, ROI, and payback period.
    """
    service = get_grant_enhancement_service()
    result = service.record_technology_investment(
        technology=data.technology,
        purchase_year=data.purchase_year,
        purchase_cost=data.purchase_cost,
        annual_subscription=data.annual_subscription,
        acres_covered=data.acres_covered,
        expected_life_years=data.expected_life_years,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/grants/technologies/roi", tags=["Grant Enhancement"])
async def calculate_technology_roi(
    data: TechnologyROIRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate ROI for a single technology investment.

    Returns detailed breakdown of benefits, multi-year projection,
    and SBIR-ready summary.
    """
    service = get_grant_enhancement_service()
    result = service.calculate_single_technology_roi(
        technology=data.technology,
        acres=data.acres,
        purchase_cost=data.purchase_cost,
        annual_subscription=data.annual_subscription,
        years=data.years,
        corn_price=data.corn_price,
        soybean_price=data.soybean_price,
        base_corn_yield=data.base_corn_yield,
        base_soybean_yield=data.base_soybean_yield
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/grants/technologies/portfolio-roi", tags=["Grant Enhancement"])
async def calculate_portfolio_roi(
    data: PortfolioROIRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate combined ROI for portfolio of precision ag investments.

    Aggregates benefits across technologies and generates SBIR narrative.
    """
    service = get_grant_enhancement_service()
    result = service.calculate_portfolio_roi(
        technologies=data.technologies,
        acres=data.acres,
        years=data.years
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/grants/economic-impact-report", tags=["Grant Enhancement"])
async def generate_economic_impact_report(
    data: EconomicImpactReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate comprehensive economic impact report for grant applications.

    Includes executive summary, technology stack analysis, financial projections,
    methodology documentation, and SBIR-ready narrative.
    """
    service = get_grant_enhancement_service()
    return service.generate_economic_impact_report(
        farm_name=data.farm_name,
        technologies=data.technologies,
        acres=data.acres,
        years_of_data=data.years_of_data
    )


# ----- Data Quality/Completeness Tracker Endpoints -----

@app.get("/api/v1/grants/data-categories", tags=["Grant Enhancement"])
async def get_data_categories(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get list of data categories for completeness tracking.

    Returns 12 categories: field boundaries, soil tests, yield data,
    planting/application/harvest records, weather, financial, equipment,
    imagery, scouting, sustainability metrics.
    """
    service = get_grant_enhancement_service()
    return service.get_data_categories()


@app.post("/api/v1/grants/data-availability", tags=["Grant Enhancement"])
async def record_data_availability(
    data: DataAvailabilityCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record data availability for a category.

    Tracks years available, completeness percentage, format, and last update.
    """
    service = get_grant_enhancement_service()
    result = service.record_data_availability(
        category=data.category,
        years_available=data.years_available,
        completeness_pct=data.completeness_pct,
        format=data.format,
        last_updated=data.last_updated,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/grants/data-completeness/{grant_program}", tags=["Grant Enhancement"])
async def assess_data_completeness(
    grant_program: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Assess data completeness for a specific grant program.

    Returns required/recommended data status, overall score, grade,
    and prioritized action items.

    Programs: USDA_SBIR, SARE, CIG, EQIP, NSF_SBIR
    """
    service = get_grant_enhancement_service()
    result = service.assess_data_completeness(grant_program)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/grants/data-quality-report", tags=["Grant Enhancement"])
async def generate_data_quality_report(
    data: DataQualityReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate comprehensive data quality report.

    Assesses readiness across multiple grant programs with
    data inventory, priority actions, and recommendations.
    """
    service = get_grant_enhancement_service()
    return service.generate_data_quality_report(
        farm_name=data.farm_name,
        target_grants=data.target_grants
    )


# ----- Partnership Opportunity Finder Endpoints -----

@app.get("/api/v1/grants/research-areas", tags=["Grant Enhancement"])
async def get_research_areas(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get list of research areas for partnership matching.

    Returns 12 areas: precision ag, sustainability, soil health,
    pest management, variety trials, nutrient/water management,
    cover crops, carbon sequestration, climate adaptation,
    digital agriculture, economics.
    """
    service = get_grant_enhancement_service()
    return service.get_research_areas()


@app.get("/api/v1/grants/partner-types", tags=["Grant Enhancement"])
async def get_partner_types(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get list of research partner types"""
    service = get_grant_enhancement_service()
    return service.get_partner_types()


@app.post("/api/v1/grants/find-partners", tags=["Grant Enhancement"])
async def find_partnership_opportunities(
    data: PartnershipSearchRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Find matching research partnership opportunities.

    Searches 13 partners (universities, extension, federal agencies,
    nonprofits, industry, cooperatives) and scores matches based on
    research area overlap, grant alignment, and location.
    """
    service = get_grant_enhancement_service()
    return service.find_partnership_opportunities(
        farm_capabilities=data.farm_capabilities,
        target_grants=data.target_grants,
        preferred_partner_types=data.preferred_partner_types,
        state=data.state
    )


@app.get("/api/v1/grants/partners/{partner_name}", tags=["Grant Enhancement"])
async def get_partner_details(
    partner_name: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get detailed information about a specific research partner"""
    service = get_grant_enhancement_service()
    result = service.get_partner_details(partner_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Partner '{partner_name}' not found")
    return result


@app.post("/api/v1/grants/partnership-report", tags=["Grant Enhancement"])
async def generate_partnership_report(
    data: PartnershipReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate comprehensive partnership opportunity report.

    Includes top opportunities, categorization by partner type and grant program,
    outreach plan with immediate/short-term/ongoing actions.
    """
    service = get_grant_enhancement_service()
    return service.generate_partnership_report(
        farm_name=data.farm_name,
        farm_capabilities=data.farm_capabilities,
        target_grants=data.target_grants,
        state=data.state
    )


@app.get("/api/v1/grants/partners", tags=["Grant Enhancement"])
async def list_all_partners():
    """Get list of all research partners in the database"""
    return {
        "partners": [
            {
                "name": p["name"],
                "type": p["type"].value,
                "location": p["location"],
                "research_areas": [a.value for a in p["research_areas"]],
                "grant_programs": p["grant_programs"],
                "website": p["website"]
            }
            for p in RESEARCH_PARTNERS
        ],
        "total": len(RESEARCH_PARTNERS)
    }


# ============================================================================
# GRANT OPERATIONS ROUTES (v3.7.0)
# ============================================================================

# Pydantic models for Grant Operations API
class GrantApplicationCreate(BaseModel):
    program: str = Field(..., description="Grant program ID (e.g., 'USDA_SBIR', 'SARE_PRODUCER')")
    project_title: str
    project_description: str
    funding_amount: float
    deadline: date
    notes: str = ""


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., description="New status (identified, preparing, submitted, under_review, awarded, not_funded, withdrawn)")
    notes: str = ""


class DocumentStatusUpdate(BaseModel):
    document_name: str
    status: str = Field(..., description="Document status (not_started, in_progress, complete, submitted)")


class LicenseCreate(BaseModel):
    license_type: str = Field(..., description="Type (private_applicator, commercial_applicator, etc.)")
    license_number: str
    holder_name: str
    issue_date: date
    expiration_date: date
    issuing_authority: str
    categories: List[str] = []
    ceu_required: int = 0
    ceu_earned: int = 0


class CEURecordCreate(BaseModel):
    ceu_amount: float
    course_name: str
    completion_date: date


class RUPApplicationCreate(BaseModel):
    application_date: date
    product_name: str
    epa_reg_number: str
    active_ingredient: str
    field_name: str
    acres_treated: float
    rate_per_acre: float
    rate_unit: str
    target_pest: str
    applicator_name: str
    applicator_license: str
    wind_speed_mph: float = 0
    temperature_f: float = 0
    humidity_pct: float = 0
    rei_hours: int = 0
    phi_days: int = 0
    notes: str = ""


class WPSActivityCreate(BaseModel):
    record_type: str = Field(..., description="Type (training, notification, decontamination, etc.)")
    activity_date: date
    description: str
    participants: List[str]
    trainer: str = None
    documentation_path: str = None
    next_due: date = None


class EnterpriseBudgetCreate(BaseModel):
    crop: str = Field(..., description="Crop type (corn, soybeans, rice, cotton, wheat, grain_sorghum)")
    year: int
    acres: float
    expected_yield: float = None
    expected_price: float = None
    # Optional cost overrides
    seed: float = None
    fertilizer: float = None
    chemicals: float = None
    land_rent: float = None


class ScenarioAnalysisRequest(BaseModel):
    budget_id: str
    yield_scenarios: List[float] = None
    price_scenarios: List[float] = None


class OutreachActivityCreate(BaseModel):
    activity_type: str = Field(..., description="Type (field_day, presentation, workshop, webinar, etc.)")
    title: str
    activity_date: date
    description: str
    audience: str
    attendance: int
    location: str
    partners: List[str] = []
    topics: List[str] = []
    materials_path: str = None
    follow_up_contacts: int = 0
    notes: str = ""


class PublicationCreate(BaseModel):
    pub_type: str = Field(..., description="Type (journal, extension, trade, blog)")
    title: str
    authors: List[str]
    publication_venue: str
    pub_date: date
    doi_or_url: str = None
    abstract: str = ""
    keywords: List[str] = []
    grant_acknowledgment: str = None


class OutreachReportRequest(BaseModel):
    grant_program: str
    project_title: str
    start_date: date
    end_date: date


# ----- Grant Application Manager Endpoints -----

@app.get("/api/v1/grants/applications/programs", tags=["Grant Operations"])
async def get_grant_programs_list(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get list of grant programs with details.

    Returns 6 programs: USDA SBIR, SARE Producer, CIG, EQIP, LA On Farm, NSF SBIR
    with funding ranges, deadlines, and required documents.
    """
    service = get_grant_operations_service()
    return service.get_grant_programs()


@app.post("/api/v1/grants/applications", tags=["Grant Operations"])
async def create_grant_application(
    data: GrantApplicationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a new grant application.

    Initializes tracking for all required documents with deadline monitoring.
    """
    service = get_grant_operations_service()
    result = service.create_application(
        program=data.program,
        project_title=data.project_title,
        project_description=data.project_description,
        funding_amount=data.funding_amount,
        deadline=data.deadline,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/v1/grants/applications/{application_id}/status", tags=["Grant Operations"])
async def update_application_status(
    application_id: str,
    data: ApplicationStatusUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update the status of a grant application"""
    service = get_grant_operations_service()
    result = service.update_application_status(application_id, data.status, data.notes)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.put("/api/v1/grants/applications/{application_id}/documents", tags=["Grant Operations"])
async def update_document_status(
    application_id: str,
    data: DocumentStatusUpdate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update status of a required document"""
    service = get_grant_operations_service()
    result = service.update_document_status(application_id, data.document_name, data.status)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/grants/applications/{application_id}", tags=["Grant Operations"])
async def get_application_summary(
    application_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get detailed summary of a grant application"""
    service = get_grant_operations_service()
    result = service.get_application_summary(application_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/grants/applications/deadlines/upcoming", tags=["Grant Operations"])
async def get_upcoming_deadlines(
    days_ahead: int = 90,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get applications with upcoming deadlines"""
    service = get_grant_operations_service()
    return service.get_upcoming_deadlines(days_ahead)


@app.get("/api/v1/grants/applications/dashboard", tags=["Grant Operations"])
async def get_applications_dashboard(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get dashboard summary of all grant applications.

    Shows counts by status, total funding requested/awarded, and critical deadlines.
    """
    service = get_grant_operations_service()
    return service.get_application_dashboard()


# ----- Regulatory Compliance Endpoints -----

@app.get("/api/v1/compliance/requirements", tags=["Grant Operations"])
async def get_compliance_requirements(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get list of regulatory compliance requirements.

    Includes pesticide applicator, WPS training, RUP records, and storage requirements.
    """
    service = get_grant_operations_service()
    return service.get_compliance_requirements()


@app.post("/api/v1/compliance/licenses", tags=["Grant Operations"])
async def add_license(
    data: LicenseCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a license or certification record.

    Tracks expiration dates, CEU requirements, and renewal status.
    """
    service = get_grant_operations_service()
    result = service.add_license(
        license_type=data.license_type,
        license_number=data.license_number,
        holder_name=data.holder_name,
        issue_date=data.issue_date,
        expiration_date=data.expiration_date,
        issuing_authority=data.issuing_authority,
        categories=data.categories,
        ceu_required=data.ceu_required,
        ceu_earned=data.ceu_earned
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/compliance/licenses/{license_id}/ceu", tags=["Grant Operations"])
async def record_ceu(
    license_id: str,
    data: CEURecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record CEU credits earned for a license"""
    service = get_grant_operations_service()
    result = service.record_ceu(license_id, data.ceu_amount, data.course_name, data.completion_date)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/compliance/rup", tags=["Grant Operations"])
async def record_rup_application(
    data: RUPApplicationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a Restricted Use Pesticide application.

    Captures all required information for EPA/state compliance records.
    """
    service = get_grant_operations_service()
    return service.record_rup_application(
        application_date=data.application_date,
        product_name=data.product_name,
        epa_reg_number=data.epa_reg_number,
        active_ingredient=data.active_ingredient,
        field_name=data.field_name,
        acres_treated=data.acres_treated,
        rate_per_acre=data.rate_per_acre,
        rate_unit=data.rate_unit,
        target_pest=data.target_pest,
        applicator_name=data.applicator_name,
        applicator_license=data.applicator_license,
        wind_speed_mph=data.wind_speed_mph,
        temperature_f=data.temperature_f,
        humidity_pct=data.humidity_pct,
        rei_hours=data.rei_hours,
        phi_days=data.phi_days,
        notes=data.notes
    )


@app.post("/api/v1/compliance/wps", tags=["Grant Operations"])
async def record_wps_activity(
    data: WPSActivityCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a Worker Protection Standard compliance activity.

    Tracks training, notifications, and other WPS requirements.
    """
    service = get_grant_operations_service()
    return service.record_wps_activity(
        record_type=data.record_type,
        activity_date=data.activity_date,
        description=data.description,
        participants=data.participants,
        trainer=data.trainer,
        documentation_path=data.documentation_path,
        next_due=data.next_due
    )


@app.get("/api/v1/compliance/dashboard", tags=["Grant Operations"])
async def get_compliance_dashboard(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get compliance status dashboard.

    Shows license status, upcoming expirations, WPS due dates, and RUP record counts.
    """
    service = get_grant_operations_service()
    return service.get_compliance_dashboard()


# ----- Enterprise Budget Endpoints -----

@app.get("/api/v1/budgets/defaults/{crop}", tags=["Grant Operations"])
async def get_budget_defaults(
    crop: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get default budget values for a crop.

    Returns Louisiana typical costs for corn, soybeans, rice, cotton, wheat, grain sorghum.
    """
    service = get_grant_operations_service()
    result = service.get_crop_budget_defaults(crop)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/budgets", tags=["Grant Operations"])
async def create_enterprise_budget(
    data: EnterpriseBudgetCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create an enterprise budget for a crop.

    Calculates revenues, costs, net returns, and break-even points.
    """
    service = get_grant_operations_service()
    cost_overrides = {}
    if data.seed is not None:
        cost_overrides["seed"] = data.seed
    if data.fertilizer is not None:
        cost_overrides["fertilizer"] = data.fertilizer
    if data.chemicals is not None:
        cost_overrides["chemicals"] = data.chemicals
    if data.land_rent is not None:
        cost_overrides["land_rent"] = data.land_rent

    result = service.create_enterprise_budget(
        crop=data.crop,
        year=data.year,
        acres=data.acres,
        expected_yield=data.expected_yield,
        expected_price=data.expected_price,
        **cost_overrides
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/budgets/scenarios", tags=["Grant Operations"])
async def run_scenario_analysis(
    data: ScenarioAnalysisRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Run what-if scenario analysis on a budget.

    Tests combinations of yield and price scenarios to identify risk/opportunity.
    """
    service = get_grant_operations_service()
    result = service.run_scenario_analysis(
        budget_id=data.budget_id,
        yield_scenarios=data.yield_scenarios,
        price_scenarios=data.price_scenarios
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/budgets/summary", tags=["Grant Operations"])
async def get_farm_budget_summary(
    year: int = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary of all enterprise budgets for a year"""
    service = get_grant_operations_service()
    return service.get_farm_budget_summary(year)


# ----- Outreach & Impact Endpoints -----

@app.post("/api/v1/outreach/activities", tags=["Grant Operations"])
async def record_outreach_activity(
    data: OutreachActivityCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record an outreach activity.

    Tracks field days, presentations, workshops, webinars, and other events.
    """
    service = get_grant_operations_service()
    result = service.record_outreach_activity(
        activity_type=data.activity_type,
        title=data.title,
        activity_date=data.activity_date,
        description=data.description,
        audience=data.audience,
        attendance=data.attendance,
        location=data.location,
        partners=data.partners,
        topics=data.topics,
        materials_path=data.materials_path,
        follow_up_contacts=data.follow_up_contacts,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/outreach/publications", tags=["Grant Operations"])
async def record_publication(
    data: PublicationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record a publication (journal, extension, trade, blog)"""
    service = get_grant_operations_service()
    return service.record_publication(
        pub_type=data.pub_type,
        title=data.title,
        authors=data.authors,
        publication_venue=data.publication_venue,
        pub_date=data.pub_date,
        doi_or_url=data.doi_or_url,
        abstract=data.abstract,
        keywords=data.keywords,
        grant_acknowledgment=data.grant_acknowledgment
    )


@app.get("/api/v1/outreach/summary", tags=["Grant Operations"])
async def get_outreach_summary(
    start_date: date = None,
    end_date: date = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get summary of outreach activities for a period"""
    service = get_grant_operations_service()
    return service.get_outreach_summary(start_date, end_date)


@app.post("/api/v1/outreach/report", tags=["Grant Operations"])
async def generate_outreach_report(
    data: OutreachReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate outreach report for grant reporting.

    Creates formatted report with activities, publications, reach metrics, and narrative.
    """
    service = get_grant_operations_service()
    return service.generate_outreach_report(
        grant_program=data.grant_program,
        project_title=data.project_title,
        reporting_period=(data.start_date, data.end_date)
    )


@app.get("/api/v1/outreach/activity-types", tags=["Grant Operations"])
async def get_outreach_activity_types():
    """Get list of outreach activity types"""
    return {
        "types": [
            {"id": t.value, "name": t.value.replace("_", " ").title()}
            for t in OutreachType
        ]
    }


@app.get("/api/v1/budgets/crops", tags=["Grant Operations"])
async def get_budget_crop_types():
    """Get list of supported crops for budgeting"""
    return {
        "crops": [
            {"id": c.value, "name": c.value.replace("_", " ").title()}
            for c in BudgetCropType
        ]
    }


# ============================================================================
# v3.8.0 - ELITE FARM INTELLIGENCE SUITE
# ============================================================================

# ----- Pydantic Models for Market Intelligence -----

class ForwardContractCreate(BaseModel):
    """Create a forward contract"""
    commodity: str = Field(..., description="Commodity type (corn, soybeans, wheat, etc.)")
    bushels: float = Field(..., gt=0, description="Number of bushels")
    contract_price: float = Field(..., gt=0, description="Contract price per bushel")
    delivery_start: date = Field(..., description="Delivery period start date")
    delivery_end: date = Field(..., description="Delivery period end date")
    buyer: str = Field(..., description="Buyer name")
    contract_number: str = Field(..., description="Contract number")
    notes: str = Field("", description="Optional notes")


class MarketingPlanRequest(BaseModel):
    """Calculate marketing plan"""
    commodity: str = Field(..., description="Commodity type")
    expected_production: float = Field(..., gt=0, description="Expected production in bushels")
    target_avg_price: float = Field(..., gt=0, description="Target average price")


# ----- Pydantic Models for Crop Insurance -----

class InsuranceOptionsRequest(BaseModel):
    """Request insurance options comparison"""
    crop: str = Field(..., description="Crop type")
    acres: float = Field(..., gt=0, description="Number of acres")
    aph_yield: float = Field(..., gt=0, description="Actual Production History yield")
    projected_price: float = Field(..., gt=0, description="Projected price")


class InsurancePolicyCreate(BaseModel):
    """Create insurance policy record"""
    crop: str = Field(..., description="Crop type")
    crop_year: int = Field(..., description="Crop year")
    insurance_type: str = Field("revenue_protection", description="Insurance type")
    coverage_level: int = Field(75, ge=50, le=85, description="Coverage level percentage")
    acres: float = Field(..., gt=0, description="Number of acres")
    aph_yield: float = Field(..., gt=0, description="APH yield")
    projected_price: float = Field(..., gt=0, description="Projected price")


class LossRecordCreate(BaseModel):
    """Record a crop loss"""
    policy_id: str = Field(..., description="Policy ID")
    field_name: str = Field(..., description="Field name")
    acres_affected: float = Field(..., gt=0, description="Acres affected")
    cause_of_loss: str = Field(..., description="Cause of loss")
    date_of_loss: date = Field(..., description="Date loss occurred")
    estimated_loss_pct: float = Field(..., ge=0, le=100, description="Estimated loss percentage")
    documentation: List[str] = Field(default=[], description="Documentation files")


class IndemnityScenarioRequest(BaseModel):
    """Calculate indemnity scenarios"""
    policy_id: str = Field(..., description="Policy ID")
    yield_scenarios: List[float] = Field(..., description="List of yield scenarios to calculate")
    harvest_price: Optional[float] = Field(None, description="Optional harvest price override")


# ----- Pydantic Models for Soil Health -----

class SoilTestCreate(BaseModel):
    """Record soil test results"""
    field_id: str = Field(..., description="Field ID")
    field_name: str = Field(..., description="Field name")
    sample_date: date = Field(..., description="Sample date")
    lab_name: str = Field(..., description="Lab name")
    ph: float = Field(..., ge=0, le=14, description="pH level")
    organic_matter_pct: float = Field(..., ge=0, le=100, description="Organic matter percentage")
    phosphorus_ppm: float = Field(..., ge=0, description="Phosphorus (ppm)")
    potassium_ppm: float = Field(..., ge=0, description="Potassium (ppm)")
    nitrogen_ppm: float = Field(0, ge=0, description="Nitrogen (ppm)")
    calcium_ppm: float = Field(0, ge=0, description="Calcium (ppm)")
    magnesium_ppm: float = Field(0, ge=0, description="Magnesium (ppm)")
    sulfur_ppm: float = Field(0, ge=0, description="Sulfur (ppm)")
    zinc_ppm: float = Field(0, ge=0, description="Zinc (ppm)")
    cec: float = Field(0, ge=0, description="Cation Exchange Capacity")
    sample_depth: str = Field("0-6 inches", description="Sample depth")


# ----- Pydantic Models for Lender/Investor Reporting -----

class LenderReportRequest(BaseModel):
    """Generate lender report"""
    farm_name: str = Field(..., description="Farm name")
    operator_name: str = Field(..., description="Operator name")
    total_acres: float = Field(..., gt=0, description="Total acres")
    crops: Dict[str, float] = Field(..., description="Crops and acres {crop: acres}")
    year: Optional[int] = Field(None, description="Optional crop year")


class InvestorSummaryRequest(BaseModel):
    """Generate investor summary"""
    farm_name: str = Field(..., description="Farm name")
    investment_amount: float = Field(..., gt=0, description="Investment amount requested")
    term_years: int = Field(..., gt=0, description="Investment term in years")


# ----- Pydantic Models for Harvest Analytics -----

class HarvestRecordCreate(BaseModel):
    """Record harvest data"""
    field_id: str = Field(..., description="Field ID")
    field_name: str = Field(..., description="Field name")
    crop: str = Field(..., description="Crop type")
    crop_year: int = Field(..., description="Crop year")
    harvest_date: date = Field(..., description="Harvest date")
    acres_harvested: float = Field(..., gt=0, description="Acres harvested")
    total_yield: float = Field(..., gt=0, description="Total yield (bushels/lbs)")
    moisture_pct: float = Field(..., ge=0, le=100, description="Moisture percentage")
    test_weight: float = Field(0, ge=0, description="Test weight")
    quality_notes: str = Field("", description="Quality notes")
    storage_location: str = Field("", description="Storage location")


# ----- Pydantic Models for Input Procurement -----

class SupplierCreate(BaseModel):
    """Add a supplier"""
    name: str = Field(..., description="Supplier name")
    categories: List[str] = Field(..., description="Categories (seed, fertilizer, chemical, etc.)")
    contact_name: str = Field(..., description="Contact name")
    phone: str = Field(..., description="Phone number")
    email: str = Field(..., description="Email address")
    address: str = Field("", description="Address")
    payment_terms: str = Field("", description="Payment terms")
    notes: str = Field("", description="Notes")


class PriceQuoteCreate(BaseModel):
    """Add a price quote"""
    supplier_id: str = Field(..., description="Supplier ID")
    product_name: str = Field(..., description="Product name")
    category: str = Field(..., description="Category")
    unit_price: float = Field(..., gt=0, description="Unit price")
    unit: str = Field(..., description="Unit (ton, gallon, bag, etc.)")
    min_quantity: float = Field(0, ge=0, description="Minimum quantity")
    valid_until: date = Field(..., description="Quote valid until date")
    notes: str = Field("", description="Notes")


class PurchaseOrderCreate(BaseModel):
    """Create purchase order"""
    supplier_id: str = Field(..., description="Supplier ID")
    items: List[Dict[str, Any]] = Field(..., description="Items [{product, quantity, unit_price, unit}]")
    expected_delivery: date = Field(..., description="Expected delivery date")
    notes: str = Field("", description="Notes")


# ============================================================================
# MARKET INTELLIGENCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/market/prices", tags=["Market Intelligence"])
async def get_market_prices(
    commodity: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get current commodity prices.

    Returns cash prices, futures prices, and basis for commodities.
    Optionally filter by specific commodity.
    """
    service = get_farm_intelligence_service()
    return service.get_current_prices(commodity)


@app.get("/api/v1/market/basis/{commodity}", tags=["Market Intelligence"])
async def get_basis_analysis(
    commodity: str,
    location: str = "Local",
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Analyze current vs historical basis for a commodity.

    Compares current basis to historical averages and provides recommendations.
    """
    service = get_farm_intelligence_service()
    result = service.get_basis_analysis(commodity, location)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/market/contracts", tags=["Market Intelligence"])
async def create_forward_contract(
    data: ForwardContractCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a forward contract record.

    Records forward grain sales with pricing and delivery terms.
    """
    service = get_farm_intelligence_service()
    result = service.create_forward_contract(
        commodity=data.commodity,
        bushels=data.bushels,
        contract_price=data.contract_price,
        delivery_start=data.delivery_start,
        delivery_end=data.delivery_end,
        buyer=data.buyer,
        contract_number=data.contract_number,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/market/summary", tags=["Market Intelligence"])
async def get_marketing_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get marketing position summary.

    Shows all open contracts by commodity with total bushels and average prices.
    """
    service = get_farm_intelligence_service()
    return service.get_marketing_summary()


@app.post("/api/v1/market/plan", tags=["Market Intelligence"])
async def calculate_marketing_plan(
    data: MarketingPlanRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate marketing plan to achieve target price.

    Analyzes current position and recommends contracting strategy.
    """
    service = get_farm_intelligence_service()
    result = service.calculate_marketing_plan(
        commodity=data.commodity,
        expected_production=data.expected_production,
        target_avg_price=data.target_avg_price
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/market/commodities", tags=["Market Intelligence"])
async def get_available_commodities():
    """Get list of supported commodities"""
    return {
        "commodities": [
            {"id": c.value, "name": c.value.title()}
            for c in Commodity
        ]
    }


# ============================================================================
# CROP INSURANCE ENDPOINTS
# ============================================================================

@app.post("/api/v1/insurance/options", tags=["Crop Insurance"])
async def compare_insurance_options(
    data: InsuranceOptionsRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Compare crop insurance coverage options.

    Shows premiums, guarantees, and best value recommendations for all coverage levels.
    """
    service = get_farm_intelligence_service()
    result = service.get_insurance_options(
        crop=data.crop,
        acres=data.acres,
        aph_yield=data.aph_yield,
        projected_price=data.projected_price
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/insurance/policies", tags=["Crop Insurance"])
async def create_insurance_policy(
    data: InsurancePolicyCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create an insurance policy record.

    Records policy details including coverage level, premiums, and guarantees.
    """
    service = get_farm_intelligence_service()
    result = service.create_insurance_policy(
        crop=data.crop,
        crop_year=data.crop_year,
        insurance_type=data.insurance_type,
        coverage_level=data.coverage_level,
        acres=data.acres,
        aph_yield=data.aph_yield,
        projected_price=data.projected_price
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/insurance/losses", tags=["Crop Insurance"])
async def record_crop_loss(
    data: LossRecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a crop loss for insurance claim.

    Documents loss with cause, date, and estimated damage for claim filing.
    """
    service = get_farm_intelligence_service()
    result = service.record_loss(
        policy_id=data.policy_id,
        field_name=data.field_name,
        acres_affected=data.acres_affected,
        cause_of_loss=data.cause_of_loss,
        date_of_loss=data.date_of_loss,
        estimated_loss_pct=data.estimated_loss_pct,
        documentation=data.documentation
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/insurance/indemnity-scenarios", tags=["Crop Insurance"])
async def calculate_indemnity_scenarios(
    data: IndemnityScenarioRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate potential indemnity payments for different yield scenarios.

    Projects insurance payments based on various actual yield outcomes.
    """
    service = get_farm_intelligence_service()
    result = service.calculate_indemnity_scenarios(
        policy_id=data.policy_id,
        yield_scenarios=data.yield_scenarios,
        harvest_price=data.harvest_price
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/insurance/types", tags=["Crop Insurance"])
async def get_insurance_types():
    """Get list of supported insurance types"""
    return {
        "types": [
            {"id": t.value, "name": t.name, "description": t.value.replace("_", " ").title()}
            for t in InsuranceType
        ]
    }


@app.get("/api/v1/insurance/coverage-levels", tags=["Crop Insurance"])
async def get_coverage_levels():
    """Get available coverage levels"""
    return {
        "levels": [
            {"id": level.value, "label": f"{level.value}%"}
            for level in CoverageLevel
        ]
    }


# ============================================================================
# SOIL HEALTH ENDPOINTS
# ============================================================================

@app.post("/api/v1/soil/tests", tags=["Soil Health"])
async def record_soil_test(
    data: SoilTestCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record soil test results.

    Stores comprehensive soil test data with interpretations and recommendations.
    """
    service = get_farm_intelligence_service()
    return service.record_soil_test(
        field_id=data.field_id,
        field_name=data.field_name,
        sample_date=data.sample_date,
        lab_name=data.lab_name,
        ph=data.ph,
        organic_matter_pct=data.organic_matter_pct,
        phosphorus_ppm=data.phosphorus_ppm,
        potassium_ppm=data.potassium_ppm,
        nitrogen_ppm=data.nitrogen_ppm,
        calcium_ppm=data.calcium_ppm,
        magnesium_ppm=data.magnesium_ppm,
        sulfur_ppm=data.sulfur_ppm,
        zinc_ppm=data.zinc_ppm,
        cec=data.cec,
        sample_depth=data.sample_depth
    )


@app.get("/api/v1/soil/trend/{field_id}", tags=["Soil Health"])
async def get_soil_health_trend(
    field_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get soil health trends over time for a field.

    Shows multi-year trends in pH, organic matter, nutrients with health score.
    """
    service = get_farm_intelligence_service()
    result = service.get_soil_health_trend(field_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# LENDER/INVESTOR REPORTING ENDPOINTS
# ============================================================================

@app.post("/api/v1/reports/lender", tags=["Lender Reporting"])
async def generate_lender_report(
    data: LenderReportRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate professional report for agricultural lenders.

    Creates comprehensive loan package with projections and risk management summary.
    """
    service = get_farm_intelligence_service()
    return service.generate_lender_report(
        farm_name=data.farm_name,
        operator_name=data.operator_name,
        total_acres=data.total_acres,
        crops=data.crops,
        year=data.year
    )


@app.post("/api/v1/reports/investor", tags=["Lender Reporting"])
async def generate_investor_summary(
    data: InvestorSummaryRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate investment summary for potential farm investors.

    Creates professional investment overview with metrics and strengths.
    """
    service = get_farm_intelligence_service()
    return service.generate_investor_summary(
        farm_name=data.farm_name,
        investment_amount=data.investment_amount,
        term_years=data.term_years
    )


# ============================================================================
# HARVEST ANALYTICS ENDPOINTS
# ============================================================================

@app.post("/api/v1/harvest/records", tags=["Harvest Analytics"])
async def record_harvest(
    data: HarvestRecordCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record harvest data for a field.

    Stores yield data with moisture, quality, and benchmark comparisons.
    """
    service = get_farm_intelligence_service()
    result = service.record_harvest(
        field_id=data.field_id,
        field_name=data.field_name,
        crop=data.crop,
        crop_year=data.crop_year,
        harvest_date=data.harvest_date,
        acres_harvested=data.acres_harvested,
        total_yield=data.total_yield,
        moisture_pct=data.moisture_pct,
        test_weight=data.test_weight,
        quality_notes=data.quality_notes,
        storage_location=data.storage_location
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/harvest/analytics", tags=["Harvest Analytics"])
async def get_harvest_analytics(
    crop_year: int = None,
    crop: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get harvest analytics summary.

    Shows yields by crop, field rankings, and summary statistics.
    """
    service = get_farm_intelligence_service()
    return service.get_harvest_analytics(crop_year, crop)


@app.get("/api/v1/harvest/trend/{field_id}/{crop}", tags=["Harvest Analytics"])
async def get_yield_trend(
    field_id: str,
    crop: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get multi-year yield trend for a field and crop.

    Shows yield history with statistics and trend analysis.
    """
    service = get_farm_intelligence_service()
    result = service.get_yield_trend(field_id, crop)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# INPUT PROCUREMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/procurement/suppliers", tags=["Input Procurement"])
async def add_supplier(
    data: SupplierCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a supplier to the database.

    Records supplier contact info and categories for quote tracking.
    """
    service = get_farm_intelligence_service()
    return service.add_supplier(
        name=data.name,
        categories=data.categories,
        contact_name=data.contact_name,
        phone=data.phone,
        email=data.email,
        address=data.address,
        payment_terms=data.payment_terms,
        notes=data.notes
    )


@app.post("/api/v1/procurement/quotes", tags=["Input Procurement"])
async def add_price_quote(
    data: PriceQuoteCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a price quote from a supplier.

    Records product pricing for comparison across suppliers.
    """
    service = get_farm_intelligence_service()
    result = service.add_price_quote(
        supplier_id=data.supplier_id,
        product_name=data.product_name,
        category=data.category,
        unit_price=data.unit_price,
        unit=data.unit,
        min_quantity=data.min_quantity,
        valid_until=data.valid_until,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/procurement/compare", tags=["Input Procurement"])
async def compare_quotes(
    product_name: str = None,
    category: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Compare quotes across suppliers.

    Finds best prices and potential savings by product.
    """
    service = get_farm_intelligence_service()
    return service.compare_quotes(product_name, category)


@app.post("/api/v1/procurement/orders", tags=["Input Procurement"])
async def create_purchase_order(
    data: PurchaseOrderCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a purchase order.

    Records order details for tracking deliveries and costs.
    """
    service = get_farm_intelligence_service()
    result = service.create_purchase_order(
        supplier_id=data.supplier_id,
        items=data.items,
        expected_delivery=data.expected_delivery,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/procurement/summary", tags=["Input Procurement"])
async def get_procurement_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get procurement summary and recommendations.

    Shows supplier count, active quotes, open orders, and action items.
    """
    service = get_farm_intelligence_service()
    return service.get_procurement_summary()


@app.get("/api/v1/procurement/categories", tags=["Input Procurement"])
async def get_procurement_categories():
    """Get list of input categories"""
    return {
        "categories": [
            {"id": c.value, "name": c.value.replace("_", " ").title()}
            for c in ProcurementInputCategory
        ]
    }


# ============================================================================
# v3.9.0 - ENTERPRISE OPERATIONS SUITE
# ============================================================================

# ----- Pydantic Models for Entity Management -----

class EntityCreate(BaseModel):
    """Create a farming entity"""
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type (sole_proprietor, partnership, llc, etc.)")
    tax_id: str = Field("", description="Tax ID (EIN or SSN)")
    state_of_formation: str = Field("LA", description="State of formation")
    fiscal_year_end: str = Field("12/31", description="Fiscal year end date")
    owners: List[Dict[str, Any]] = Field(default=[], description="Owners [{name, ownership_pct, role}]")
    primary_contact: str = Field("", description="Primary contact name")
    phone: str = Field("", description="Phone number")
    email: str = Field("", description="Email address")


class EntityAllocationCreate(BaseModel):
    """Create resource allocation between entities"""
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    resource_type: str = Field(..., description="Resource type (equipment, labor, land)")
    resource_id: str = Field(..., description="Resource ID")
    allocation_pct: float = Field(..., ge=0, le=100, description="Allocation percentage")
    effective_date: date = Field(..., description="Effective date")


# ----- Pydantic Models for Labor Management -----

class EmployeeCreate(BaseModel):
    """Add an employee"""
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    employee_type: str = Field(..., description="Type (full_time, part_time, seasonal, contract, family)")
    pay_type: str = Field(..., description="Pay type (hourly, salary, piece_rate, share)")
    pay_rate: float = Field(..., gt=0, description="Pay rate")
    phone: str = Field("", description="Phone number")
    email: str = Field("", description="Email address")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")
    hire_date: Optional[date] = Field(None, description="Hire date")
    emergency_contact: str = Field("", description="Emergency contact name")
    emergency_phone: str = Field("", description="Emergency contact phone")


class CertificationCreate(BaseModel):
    """Add employee certification"""
    employee_id: str = Field(..., description="Employee ID")
    cert_type: str = Field(..., description="Certification type")
    cert_number: str = Field(..., description="Certificate number")
    issue_date: date = Field(..., description="Issue date")
    expiration_date: date = Field(..., description="Expiration date")
    issuing_authority: str = Field("", description="Issuing authority")


class TimeEntryCreate(BaseModel):
    """Record time entry"""
    employee_id: str = Field(..., description="Employee ID")
    work_date: date = Field(..., description="Work date")
    hours: float = Field(..., gt=0, description="Hours worked")
    task_description: str = Field(..., description="Task description")
    start_time: str = Field("07:00", description="Start time (HH:MM)")
    end_time: str = Field("17:00", description="End time (HH:MM)")
    entry_type: str = Field("regular", description="Entry type (regular, overtime, pto, etc.)")
    field_id: Optional[str] = Field(None, description="Associated field ID")
    equipment_id: Optional[str] = Field(None, description="Associated equipment ID")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")


class ScheduleCreate(BaseModel):
    """Create schedule entry"""
    employee_id: str = Field(..., description="Employee ID")
    scheduled_date: date = Field(..., description="Scheduled date")
    start_time: str = Field(..., description="Start time (HH:MM)")
    end_time: str = Field(..., description="End time (HH:MM)")
    task: str = Field(..., description="Task description")
    field_id: Optional[str] = Field(None, description="Associated field ID")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")


# ----- Pydantic Models for Land/Lease Management -----

class LandownerCreate(BaseModel):
    """Add a landowner"""
    name: str = Field(..., description="Landowner name")
    contact_name: str = Field("", description="Contact name")
    phone: str = Field("", description="Phone number")
    email: str = Field("", description="Email address")
    address: str = Field("", description="Address")
    payment_method: str = Field("check", description="Payment method")
    tax_id: str = Field("", description="Tax ID for 1099")


class LandParcelCreate(BaseModel):
    """Add a land parcel"""
    name: str = Field(..., description="Parcel name")
    total_acres: float = Field(..., gt=0, description="Total acres")
    tillable_acres: float = Field(..., gt=0, description="Tillable acres")
    county: str = Field(..., description="County")
    ownership_type: str = Field(..., description="Ownership type (cash_rent, crop_share, owned, etc.)")
    landowner_id: Optional[str] = Field(None, description="Landowner ID if rented")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")
    state: str = Field("LA", description="State")
    fsa_farm_number: str = Field("", description="FSA farm number")
    fsa_tract_number: str = Field("", description="FSA tract number")


class LeaseCreate(BaseModel):
    """Create a lease"""
    parcel_id: str = Field(..., description="Parcel ID")
    landowner_id: str = Field(..., description="Landowner ID")
    lease_type: str = Field(..., description="Lease type (cash_rent, crop_share, flex_lease)")
    start_date: date = Field(..., description="Lease start date")
    end_date: date = Field(..., description="Lease end date")
    acres: float = Field(..., gt=0, description="Leased acres")
    cash_rent_per_acre: float = Field(0, ge=0, description="Cash rent per acre")
    payment_frequency: str = Field("annual", description="Payment frequency")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")
    landlord_share_pct: float = Field(0, ge=0, le=100, description="Landlord share % (for crop share)")
    auto_renew: bool = Field(True, description="Auto renew lease")
    notice_days: int = Field(90, description="Notice days required")


class LeasePaymentCreate(BaseModel):
    """Record lease payment"""
    lease_id: str = Field(..., description="Lease ID")
    payment_date: date = Field(..., description="Payment date")
    amount: float = Field(..., gt=0, description="Payment amount")
    payment_type: str = Field("rent", description="Payment type")
    check_number: str = Field("", description="Check number")
    notes: str = Field("", description="Notes")


# ----- Pydantic Models for Cash Flow -----

class CashFlowEntryCreate(BaseModel):
    """Add cash flow entry"""
    category: str = Field(..., description="Category (crop_sales, seed, fertilizer, etc.)")
    description: str = Field(..., description="Description")
    amount: float = Field(..., description="Amount (positive for income)")
    transaction_date: date = Field(..., description="Transaction date")
    status: str = Field("projected", description="Status (projected, committed, completed)")
    recurring: bool = Field(False, description="Is recurring")
    recurrence_pattern: str = Field("", description="Recurrence pattern (monthly, quarterly, annual)")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")


class LoanCreate(BaseModel):
    """Add a loan"""
    lender: str = Field(..., description="Lender name")
    loan_type: str = Field(..., description="Loan type (operating, equipment, real_estate)")
    original_amount: float = Field(..., gt=0, description="Original loan amount")
    current_balance: float = Field(..., gt=0, description="Current balance")
    interest_rate: float = Field(..., ge=0, description="Interest rate (%)")
    payment_amount: float = Field(..., gt=0, description="Payment amount")
    payment_frequency: str = Field(..., description="Payment frequency")
    next_payment_date: date = Field(..., description="Next payment date")
    maturity_date: date = Field(..., description="Maturity date")
    entity_id: str = Field("ENTITY-0001", description="Entity ID")
    collateral: str = Field("", description="Collateral description")


class CashFlowForecastRequest(BaseModel):
    """Request cash flow forecast"""
    months: int = Field(12, ge=1, le=24, description="Months to forecast")
    starting_balance: float = Field(0, description="Starting cash balance")
    entity_id: Optional[str] = Field(None, description="Entity ID filter")


# ============================================================================
# ENTITY MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/entities", tags=["Entity Management"])
async def create_entity(
    data: EntityCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a new farming entity.

    Supports sole proprietor, partnership, LLC, S-Corp, C-Corp, trust, and family LP.
    """
    service = get_enterprise_operations_service()
    result = service.create_entity(
        name=data.name,
        entity_type=data.entity_type,
        tax_id=data.tax_id,
        state_of_formation=data.state_of_formation,
        fiscal_year_end=data.fiscal_year_end,
        owners=data.owners,
        primary_contact=data.primary_contact,
        phone=data.phone,
        email=data.email
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/entities", tags=["Entity Management"])
async def get_entities(
    active_only: bool = True,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all farming entities"""
    service = get_enterprise_operations_service()
    return service.get_entities(active_only)


@app.post("/api/v1/entities/allocations", tags=["Entity Management"])
async def create_entity_allocation(
    data: EntityAllocationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create resource allocation between entities.

    Allocates equipment, labor, or land between farming entities.
    """
    service = get_enterprise_operations_service()
    result = service.create_allocation(
        source_entity_id=data.source_entity_id,
        target_entity_id=data.target_entity_id,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        allocation_pct=data.allocation_pct,
        effective_date=data.effective_date
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/entities/types", tags=["Entity Management"])
async def get_entity_types():
    """Get available entity types"""
    return {
        "types": [
            {"id": t.value, "name": t.value.replace("_", " ").title()}
            for t in EntityType
        ]
    }


# ============================================================================
# LABOR MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/labor/employees", tags=["Labor Management"])
async def add_employee(
    data: EmployeeCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a new employee.

    Supports full-time, part-time, seasonal, contract, and family workers.
    """
    service = get_enterprise_operations_service()
    result = service.add_employee(
        first_name=data.first_name,
        last_name=data.last_name,
        employee_type=data.employee_type,
        pay_type=data.pay_type,
        pay_rate=data.pay_rate,
        phone=data.phone,
        email=data.email,
        entity_id=data.entity_id,
        hire_date=data.hire_date,
        emergency_contact=data.emergency_contact,
        emergency_phone=data.emergency_phone
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/labor/certifications", tags=["Labor Management"])
async def add_employee_certification(
    data: CertificationCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add certification to employee.

    Tracks applicator licenses, CDLs, safety certifications, and more.
    """
    service = get_enterprise_operations_service()
    result = service.add_certification(
        employee_id=data.employee_id,
        cert_type=data.cert_type,
        cert_number=data.cert_number,
        issue_date=data.issue_date,
        expiration_date=data.expiration_date,
        issuing_authority=data.issuing_authority
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/labor/time", tags=["Labor Management"])
async def record_time_entry(
    data: TimeEntryCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record time entry for employee.

    Tracks regular hours, overtime, PTO, sick time, and holiday pay.
    """
    service = get_enterprise_operations_service()
    result = service.record_time(
        employee_id=data.employee_id,
        work_date=data.work_date,
        hours=data.hours,
        task_description=data.task_description,
        start_time=data.start_time,
        end_time=data.end_time,
        entry_type=data.entry_type,
        field_id=data.field_id,
        equipment_id=data.equipment_id,
        entity_id=data.entity_id
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/labor/timesheet", tags=["Labor Management"])
async def get_timesheet(
    employee_id: str = None,
    start_date: date = None,
    end_date: date = None,
    entity_id: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get timesheet summary.

    Shows hours worked by employee with approval status.
    """
    service = get_enterprise_operations_service()
    return service.get_timesheet(employee_id, start_date, end_date, entity_id)


@app.post("/api/v1/labor/schedule", tags=["Labor Management"])
async def create_schedule_entry(
    data: ScheduleCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create work schedule entry.

    Schedules employees for specific tasks and dates.
    """
    service = get_enterprise_operations_service()
    result = service.create_schedule(
        employee_id=data.employee_id,
        scheduled_date=data.scheduled_date,
        start_time=data.start_time,
        end_time=data.end_time,
        task=data.task,
        field_id=data.field_id,
        entity_id=data.entity_id
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/labor/schedule", tags=["Labor Management"])
async def get_crew_schedule(
    start_date: date,
    end_date: date = None,
    entity_id: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get crew schedule for date range"""
    service = get_enterprise_operations_service()
    return service.get_crew_schedule(start_date, end_date, entity_id)


@app.get("/api/v1/labor/certification-alerts", tags=["Labor Management"])
async def get_certification_alerts(
    days_ahead: int = 90,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get certification expiration alerts.

    Shows upcoming and expired certifications requiring attention.
    """
    service = get_enterprise_operations_service()
    return service.get_certification_alerts(days_ahead)


@app.get("/api/v1/labor/payroll-summary", tags=["Labor Management"])
async def generate_payroll_summary(
    pay_period_start: date,
    pay_period_end: date,
    entity_id: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate payroll summary for pay period.

    Calculates hours, overtime, and gross pay for all employees.
    """
    service = get_enterprise_operations_service()
    return service.generate_payroll_summary(pay_period_start, pay_period_end, entity_id)


@app.get("/api/v1/labor/employee-types", tags=["Labor Management"])
async def get_employee_types():
    """Get available employee types"""
    return {
        "types": [{"id": t.value, "name": t.value.replace("_", " ").title()} for t in EmployeeType]
    }


@app.get("/api/v1/labor/pay-types", tags=["Labor Management"])
async def get_pay_types():
    """Get available pay types"""
    return {
        "types": [{"id": t.value, "name": t.value.replace("_", " ").title()} for t in PayType]
    }


@app.get("/api/v1/labor/certification-types", tags=["Labor Management"])
async def get_certification_types():
    """Get available certification types"""
    return {
        "types": [{"id": t.value, "name": t.value.replace("_", " ").title()} for t in CertificationType]
    }


# ============================================================================
# LAND/LEASE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/land/landowners", tags=["Land Management"])
async def add_landowner(
    data: LandownerCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a landowner.

    Records landowner contact info and payment preferences.
    """
    service = get_enterprise_operations_service()
    return service.add_landowner(
        name=data.name,
        contact_name=data.contact_name,
        phone=data.phone,
        email=data.email,
        address=data.address,
        payment_method=data.payment_method,
        tax_id=data.tax_id
    )


@app.post("/api/v1/land/parcels", tags=["Land Management"])
async def add_land_parcel(
    data: LandParcelCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a land parcel.

    Records parcel details including FSA numbers and tillable acres.
    """
    service = get_enterprise_operations_service()
    result = service.add_land_parcel(
        name=data.name,
        total_acres=data.total_acres,
        tillable_acres=data.tillable_acres,
        county=data.county,
        ownership_type=data.ownership_type,
        landowner_id=data.landowner_id,
        entity_id=data.entity_id,
        state=data.state,
        fsa_farm_number=data.fsa_farm_number,
        fsa_tract_number=data.fsa_tract_number
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/land/leases", tags=["Land Management"])
async def create_lease(
    data: LeaseCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a lease agreement.

    Supports cash rent, crop share, and flex lease arrangements.
    """
    service = get_enterprise_operations_service()
    result = service.create_lease(
        parcel_id=data.parcel_id,
        landowner_id=data.landowner_id,
        lease_type=data.lease_type,
        start_date=data.start_date,
        end_date=data.end_date,
        acres=data.acres,
        cash_rent_per_acre=data.cash_rent_per_acre,
        payment_frequency=data.payment_frequency,
        entity_id=data.entity_id,
        landlord_share_pct=data.landlord_share_pct,
        auto_renew=data.auto_renew,
        notice_days=data.notice_days
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/land/lease-payments", tags=["Land Management"])
async def record_lease_payment(
    data: LeasePaymentCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record a lease payment.

    Tracks rent payments, bonuses, and reimbursements to landowners.
    """
    service = get_enterprise_operations_service()
    result = service.record_lease_payment(
        lease_id=data.lease_id,
        payment_date=data.payment_date,
        amount=data.amount,
        payment_type=data.payment_type,
        check_number=data.check_number,
        notes=data.notes
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/v1/land/lease-summary", tags=["Land Management"])
async def get_lease_summary(
    entity_id: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get summary of all leases.

    Shows total acres, rent costs, and upcoming expirations.
    """
    service = get_enterprise_operations_service()
    return service.get_lease_summary(entity_id)


@app.get("/api/v1/land/payment-schedule", tags=["Land Management"])
async def get_lease_payment_schedule(
    year: int = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get payment schedule for all leases.

    Projects payments by month for budgeting.
    """
    service = get_enterprise_operations_service()
    return service.get_lease_payment_schedule(year)


@app.get("/api/v1/land/rent-comparison", tags=["Land Management"])
async def get_rent_comparison(
    region: str = "delta_region",
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Compare your rents to regional averages.

    Shows how your lease rates compare to area benchmarks.
    """
    service = get_enterprise_operations_service()
    return service.get_rent_comparison(region)


@app.get("/api/v1/land/lease-types", tags=["Land Management"])
async def get_lease_types():
    """Get available lease types"""
    return {
        "types": [{"id": t.value, "name": t.value.replace("_", " ").title()} for t in LeaseType]
    }


@app.get("/api/v1/land/regions", tags=["Land Management"])
async def get_rent_regions():
    """Get available regions for rent comparison"""
    return {
        "regions": [
            {"id": r, "averages": CASH_RENT_AVERAGES[r]}
            for r in CASH_RENT_AVERAGES.keys()
        ]
    }


# ============================================================================
# CASH FLOW MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/cashflow/entries", tags=["Cash Flow"])
async def add_cash_flow_entry(
    data: CashFlowEntryCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a cash flow entry.

    Records projected or actual income and expenses.
    """
    service = get_enterprise_operations_service()
    result = service.add_cash_flow_entry(
        category=data.category,
        description=data.description,
        amount=data.amount,
        transaction_date=data.transaction_date,
        status=data.status,
        recurring=data.recurring,
        recurrence_pattern=data.recurrence_pattern,
        entity_id=data.entity_id
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/cashflow/loans", tags=["Cash Flow"])
async def add_loan(
    data: LoanCreate,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a loan record.

    Tracks operating, equipment, and real estate loans.
    """
    service = get_enterprise_operations_service()
    result = service.add_loan(
        lender=data.lender,
        loan_type=data.loan_type,
        original_amount=data.original_amount,
        current_balance=data.current_balance,
        interest_rate=data.interest_rate,
        payment_amount=data.payment_amount,
        payment_frequency=data.payment_frequency,
        next_payment_date=data.next_payment_date,
        maturity_date=data.maturity_date,
        entity_id=data.entity_id,
        collateral=data.collateral
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/v1/cashflow/forecast", tags=["Cash Flow"])
async def generate_cash_flow_forecast(
    data: CashFlowForecastRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate cash flow forecast.

    Projects income, expenses, and balances for up to 24 months.
    """
    service = get_enterprise_operations_service()
    return service.generate_cash_flow_forecast(
        months=data.months,
        starting_balance=data.starting_balance,
        entity_id=data.entity_id
    )


@app.get("/api/v1/cashflow/loan-summary", tags=["Cash Flow"])
async def get_loan_summary(
    entity_id: str = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get summary of all loans.

    Shows total debt, annual payments, and maturity dates.
    """
    service = get_enterprise_operations_service()
    return service.get_loan_summary(entity_id)


@app.get("/api/v1/cashflow/categories", tags=["Cash Flow"])
async def get_cash_flow_categories():
    """Get available cash flow categories"""
    service = get_enterprise_operations_service()
    return service.get_cash_flow_categories()


# ============================================================================
# v4.0.0 - PRECISION INTELLIGENCE SUITE
# ============================================================================

# ----- Pydantic Models for Precision Intelligence -----

class YieldPredictionRequest(BaseModel):
    field_id: str
    field_name: str
    crop: str
    crop_year: int
    acres: float
    historical_yields: Optional[List[float]] = None
    soil_type: Optional[str] = "default"
    current_conditions: Optional[Dict[str, Any]] = None


class ZoneCreateRequest(BaseModel):
    field_id: str
    zone_name: str
    zone_type: str
    acres: float
    avg_yield: float
    yield_potential: float
    soil_properties: Optional[Dict[str, float]] = None


class SeedingPrescriptionRequest(BaseModel):
    field_id: str
    crop: str
    crop_year: int
    seed_cost_per_unit: float
    units_per_bag: int = 80000


class NitrogenPrescriptionRequest(BaseModel):
    field_id: str
    crop: str
    crop_year: int
    target_yield: float
    nitrogen_cost_per_unit: float
    units_per_ton: float = 2000
    soil_credits: float = 0


class PlantingRecommendationRequest(BaseModel):
    field_id: str
    field_name: str
    crop: str
    forecast_temps: List[float]
    soil_temp: float
    forecast_precip: List[float]


class SprayRecommendationPrecisionRequest(BaseModel):
    field_id: str
    field_name: str
    crop: str
    growth_stage: str
    pest_pressure: int = Field(..., ge=1, le=10)
    forecast_temps: List[float]
    forecast_wind: List[float]
    forecast_precip: List[float]


class HarvestRecommendationRequest(BaseModel):
    field_id: str
    field_name: str
    crop: str
    current_moisture: float
    forecast_temps: List[float]
    forecast_precip: List[float]


# ----- Yield Prediction Endpoints -----

@app.post("/api/v1/precision/yield/predict", tags=["Precision Intelligence"])
async def predict_yield(
    data: YieldPredictionRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Predict yield using ML-based models.

    Uses historical data, weather patterns, and soil conditions.
    """
    service = get_precision_intelligence_service()
    return service.predict_yield(
        field_id=data.field_id,
        field_name=data.field_name,
        crop=data.crop,
        crop_year=data.crop_year,
        acres=data.acres,
        historical_yields=data.historical_yields,
        soil_type=data.soil_type,
        current_conditions=data.current_conditions
    )


@app.get("/api/v1/precision/yield/history/{field_id}", tags=["Precision Intelligence"])
async def get_yield_prediction_history(
    field_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get yield prediction history for a field"""
    service = get_precision_intelligence_service()
    return service.get_prediction_history(field_id)


# ----- Management Zone Endpoints -----

@app.post("/api/v1/precision/zones", tags=["Precision Intelligence"])
async def create_management_zone(
    data: ZoneCreateRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a management zone within a field.

    Zones enable variable rate applications.
    """
    service = get_precision_intelligence_service()
    return service.create_zone(
        field_id=data.field_id,
        zone_name=data.zone_name,
        zone_type=data.zone_type,
        acres=data.acres,
        avg_yield=data.avg_yield,
        yield_potential=data.yield_potential,
        soil_properties=data.soil_properties
    )


@app.get("/api/v1/precision/zones/{field_id}", tags=["Precision Intelligence"])
async def get_field_zones(
    field_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all management zones for a field"""
    service = get_precision_intelligence_service()
    return service.get_field_zones(field_id)


@app.get("/api/v1/precision/zones/types", tags=["Precision Intelligence"])
async def get_zone_types():
    """Get available management zone types"""
    return {
        "zone_types": [z.value for z in ZoneType],
        "descriptions": {
            "high_productivity": "Areas consistently exceeding yield potential",
            "medium_productivity": "Areas meeting average yield expectations",
            "low_productivity": "Areas consistently underperforming",
            "variable": "Areas with inconsistent performance",
            "problem_area": "Areas requiring investigation/remediation"
        }
    }


# ----- Prescription Generator Endpoints -----

@app.post("/api/v1/precision/prescriptions/seeding", tags=["Precision Intelligence"])
async def generate_seeding_prescription(
    data: SeedingPrescriptionRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate variable rate seeding prescription.

    Adjusts seeding rates based on zone productivity.
    """
    service = get_precision_intelligence_service()
    return service.generate_seeding_prescription(
        field_id=data.field_id,
        crop=data.crop,
        crop_year=data.crop_year,
        seed_cost_per_unit=data.seed_cost_per_unit,
        units_per_bag=data.units_per_bag
    )


@app.post("/api/v1/precision/prescriptions/nitrogen", tags=["Precision Intelligence"])
async def generate_nitrogen_prescription(
    data: NitrogenPrescriptionRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Generate variable rate nitrogen prescription.

    Optimizes nitrogen based on yield potential and soil credits.
    """
    service = get_precision_intelligence_service()
    return service.generate_nitrogen_prescription(
        field_id=data.field_id,
        crop=data.crop,
        crop_year=data.crop_year,
        target_yield=data.target_yield,
        nitrogen_cost_per_unit=data.nitrogen_cost_per_unit,
        units_per_ton=data.units_per_ton,
        soil_credits=data.soil_credits
    )


@app.get("/api/v1/precision/prescriptions/{field_id}", tags=["Precision Intelligence"])
async def get_field_prescriptions(
    field_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all prescriptions for a field"""
    service = get_precision_intelligence_service()
    return service.get_field_prescriptions(field_id)


@app.get("/api/v1/precision/prescriptions/types", tags=["Precision Intelligence"])
async def get_prescription_types():
    """Get available prescription types"""
    return {
        "prescription_types": [p.value for p in PrescriptionType]
    }


# ----- Decision Support Endpoints -----

@app.post("/api/v1/precision/decisions/planting", tags=["Precision Intelligence"])
async def get_planting_recommendation(
    data: PlantingRecommendationRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get AI-powered planting timing recommendation.

    Analyzes soil temp, weather forecast, and conditions.
    """
    service = get_precision_intelligence_service()
    return service.get_planting_recommendation(
        field_id=data.field_id,
        field_name=data.field_name,
        crop=data.crop,
        forecast_temps=data.forecast_temps,
        soil_temp=data.soil_temp,
        forecast_precip=data.forecast_precip
    )


@app.post("/api/v1/precision/decisions/spray", tags=["Precision Intelligence"])
async def get_spray_recommendation(
    data: SprayRecommendationPrecisionRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get AI-powered spray timing recommendation.

    Optimizes application timing for efficacy and safety.
    """
    service = get_precision_intelligence_service()
    return service.get_spray_recommendation(
        field_id=data.field_id,
        field_name=data.field_name,
        crop=data.crop,
        growth_stage=data.growth_stage,
        pest_pressure=data.pest_pressure,
        forecast_temps=data.forecast_temps,
        forecast_wind=data.forecast_wind,
        forecast_precip=data.forecast_precip
    )


@app.post("/api/v1/precision/decisions/harvest", tags=["Precision Intelligence"])
async def get_harvest_recommendation(
    data: HarvestRecommendationRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Get AI-powered harvest timing recommendation.

    Balances moisture, weather, and drying costs.
    """
    service = get_precision_intelligence_service()
    return service.get_harvest_recommendation(
        field_id=data.field_id,
        field_name=data.field_name,
        crop=data.crop,
        current_moisture=data.current_moisture,
        forecast_temps=data.forecast_temps,
        forecast_precip=data.forecast_precip
    )


@app.get("/api/v1/precision/models", tags=["Precision Intelligence"])
async def get_prediction_models():
    """Get available prediction models"""
    return {
        "models": [m.value for m in PredictionModel],
        "descriptions": {
            "historical_average": "Simple average of past yields",
            "trend_analysis": "Linear trend projection",
            "weather_adjusted": "Trend with weather adjustments",
            "machine_learning": "Advanced ML prediction (future)"
        }
    }


# ============================================================================
# v4.1.0 - GRAIN & STORAGE SUITE
# ============================================================================

# ----- Pydantic Models for Grain Storage -----

class BinCreateRequest(BaseModel):
    name: str
    bin_type: str
    capacity_bushels: float
    diameter_feet: float
    height_feet: float
    has_aeration: bool = True
    has_dryer: bool = False
    dryer_type: Optional[str] = None
    dryer_capacity_bph: float = 0
    location: str = ""
    notes: str = ""


class BinLoadRequest(BaseModel):
    bin_id: str
    grain_type: str
    bushels: float
    moisture_pct: float
    test_weight: float
    source_field: str
    temperature: float = 70


class BinUnloadRequest(BaseModel):
    bin_id: str
    bushels: float
    destination: str
    price_per_bushel: Optional[float] = None
    ticket_number: str = ""


class DryingCostRequest(BaseModel):
    bushels: float
    initial_moisture: float
    target_moisture: float
    dryer_type: str
    fuel_cost_per_gallon: float
    electricity_cost_per_kwh: float = 0.12


class BasisAlertRequest(BaseModel):
    grain_type: str
    target_basis: float
    bushels: float
    delivery_location: str
    delivery_month: str
    alert_type: str = "basis_target_hit"
    notes: str = ""


# ----- Bin Management Endpoints -----

@app.post("/api/v1/grain/bins", tags=["Grain Storage"])
async def add_storage_bin(
    data: BinCreateRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a grain storage bin.

    Tracks capacity, equipment, and conditions.
    """
    service = get_grain_storage_service()
    return service.add_bin(
        name=data.name,
        bin_type=data.bin_type,
        capacity_bushels=data.capacity_bushels,
        diameter_feet=data.diameter_feet,
        height_feet=data.height_feet,
        has_aeration=data.has_aeration,
        has_dryer=data.has_dryer,
        dryer_type=data.dryer_type,
        dryer_capacity_bph=data.dryer_capacity_bph,
        location=data.location,
        notes=data.notes
    )


@app.post("/api/v1/grain/bins/load", tags=["Grain Storage"])
async def load_grain_into_bin(
    data: BinLoadRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Load grain into a bin.

    Records harvest, calculates weighted averages.
    """
    service = get_grain_storage_service()
    return service.load_bin(
        bin_id=data.bin_id,
        grain_type=data.grain_type,
        bushels=data.bushels,
        moisture_pct=data.moisture_pct,
        test_weight=data.test_weight,
        source_field=data.source_field,
        temperature=data.temperature
    )


@app.post("/api/v1/grain/bins/unload", tags=["Grain Storage"])
async def unload_grain_from_bin(
    data: BinUnloadRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Unload grain from a bin.

    Records sale or transfer with pricing.
    """
    service = get_grain_storage_service()
    return service.unload_bin(
        bin_id=data.bin_id,
        bushels=data.bushels,
        destination=data.destination,
        price_per_bushel=data.price_per_bushel,
        ticket_number=data.ticket_number
    )


@app.get("/api/v1/grain/bins", tags=["Grain Storage"])
async def get_all_bin_status(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get status of all storage bins"""
    service = get_grain_storage_service()
    return service.get_bin_status()


@app.get("/api/v1/grain/bins/{bin_id}", tags=["Grain Storage"])
async def get_bin_status(
    bin_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get status of a specific bin"""
    service = get_grain_storage_service()
    result = service.get_bin_status(bin_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/grain/bins/types", tags=["Grain Storage"])
async def get_bin_types():
    """Get available bin types"""
    return {
        "bin_types": [b.value for b in BinType],
        "dryer_types": [d.value for d in DryerType]
    }


@app.get("/api/v1/grain/inventory/summary", tags=["Grain Storage"])
async def get_inventory_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get total grain inventory summary"""
    service = get_grain_storage_service()
    return service.get_inventory_summary()


# ----- Drying Cost Calculator Endpoints -----

@app.post("/api/v1/grain/drying/calculate", tags=["Grain Storage"])
async def calculate_drying_cost(
    data: DryingCostRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Calculate grain drying costs.

    Includes fuel, shrink, and time estimates.
    """
    service = get_grain_storage_service()
    return service.calculate_drying_cost(
        bushels=data.bushels,
        initial_moisture=data.initial_moisture,
        target_moisture=data.target_moisture,
        dryer_type=data.dryer_type,
        fuel_cost_per_gallon=data.fuel_cost_per_gallon,
        electricity_cost_per_kwh=data.electricity_cost_per_kwh
    )


@app.get("/api/v1/grain/drying/rates", tags=["Grain Storage"])
async def get_drying_rates():
    """Get standard drying rates and shrink factors"""
    return {
        "shrink_factor_per_point": 1.4,
        "fuel_consumption": {
            "continuous_flow": "0.02-0.03 gal/bu/point",
            "batch": "0.025-0.035 gal/bu/point",
            "in_bin": "0.01-0.015 gal/bu/point"
        },
        "target_moisture": {
            "corn": {"storage": 14.0, "sale": 15.0},
            "soybeans": {"storage": 13.0, "sale": 13.0},
            "wheat": {"storage": 13.0, "sale": 13.5}
        }
    }


# ----- Grain Accounting Endpoints -----

@app.get("/api/v1/grain/transactions", tags=["Grain Storage"])
async def get_grain_transactions(
    grain_type: str = None,
    start_date: date = None,
    end_date: date = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get grain transactions with optional filters"""
    service = get_grain_storage_service()
    return service.get_transactions(grain_type, start_date, end_date)


@app.get("/api/v1/grain/accounting/summary", tags=["Grain Storage"])
async def get_grain_accounting_summary(
    crop_year: int = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get grain accounting summary for crop year"""
    service = get_grain_storage_service()
    return service.get_accounting_summary(crop_year)


@app.get("/api/v1/grain/types", tags=["Grain Storage"])
async def get_grain_types():
    """Get supported grain types"""
    return {
        "grain_types": [g.value for g in GrainType],
        "test_weights": {
            "corn": 56,
            "soybeans": 60,
            "wheat": 60,
            "rice": 45,
            "sorghum": 56,
            "oats": 32
        }
    }


# ----- Basis Alert Endpoints -----

@app.post("/api/v1/grain/alerts", tags=["Grain Storage"])
async def create_basis_alert(
    data: BasisAlertRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create a basis price alert.

    Get notified when target basis/price is hit.
    """
    service = get_grain_storage_service()
    return service.create_basis_alert(
        grain_type=data.grain_type,
        target_basis=data.target_basis,
        bushels=data.bushels,
        delivery_location=data.delivery_location,
        delivery_month=data.delivery_month,
        alert_type=data.alert_type,
        notes=data.notes
    )


@app.get("/api/v1/grain/alerts", tags=["Grain Storage"])
async def get_basis_alerts(
    active_only: bool = True,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all basis alerts"""
    service = get_grain_storage_service()
    return service.get_alerts(active_only)


@app.post("/api/v1/grain/alerts/check", tags=["Grain Storage"])
async def check_basis_alerts(
    current_prices: Dict[str, float],
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Check alerts against current prices.

    Returns triggered alerts.
    """
    service = get_grain_storage_service()
    return service.check_alerts(current_prices)


@app.delete("/api/v1/grain/alerts/{alert_id}", tags=["Grain Storage"])
async def delete_basis_alert(
    alert_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Delete a basis alert"""
    service = get_grain_storage_service()
    result = service.delete_alert(alert_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============================================================================
# v4.2.0 - COMPLETE FARM BUSINESS SUITE
# ============================================================================

# ----- Pydantic Models for Farm Business -----

class DepreciableAssetRequest(BaseModel):
    name: str
    asset_type: str
    purchase_date: date
    purchase_price: float
    salvage_value: float = 0
    useful_life_years: Optional[int] = None
    depreciation_method: str = "macrs_gds"
    section_179_amount: float = 0
    bonus_depreciation_pct: float = 0
    notes: str = ""


class TaxProjectionRequest(BaseModel):
    tax_year: int
    entity_type: str = "schedule_f"
    gross_income: float
    total_expenses: float


class FamilyMemberRequest(BaseModel):
    name: str
    role: str
    birth_date: Optional[date] = None
    ownership_pct: float = 0
    involvement_level: str = ""
    skills: Optional[List[str]] = None
    notes: str = ""


class AssetTransferRequest(BaseModel):
    asset_name: str
    asset_value: float
    transfer_method: str
    from_member_id: str
    to_member_id: str
    target_date: date
    notes: str = ""


class SuccessionMilestoneRequest(BaseModel):
    title: str
    category: str
    description: str
    target_date: date
    assigned_to: Optional[str] = None


class BenchmarkDataRequest(BaseModel):
    field_id: str
    crop: str
    crop_year: int
    metrics: Dict[str, float]


class DocumentUploadRequest(BaseModel):
    name: str
    category: str
    file_path: str
    file_type: str
    document_date: date
    year: int
    tags: Optional[List[str]] = None
    description: str = ""
    expiration_date: Optional[date] = None
    related_entity: str = ""


# ----- Tax Planning Endpoints -----

@app.post("/api/v1/business/tax/assets", tags=["Farm Business"])
async def add_depreciable_asset(
    data: DepreciableAssetRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a depreciable asset.

    Calculates MACRS, Section 179, and bonus depreciation.
    """
    service = get_farm_business_service()
    return service.add_depreciable_asset(
        name=data.name,
        asset_type=data.asset_type,
        purchase_date=data.purchase_date,
        purchase_price=data.purchase_price,
        salvage_value=data.salvage_value,
        useful_life_years=data.useful_life_years,
        depreciation_method=data.depreciation_method,
        section_179_amount=data.section_179_amount,
        bonus_depreciation_pct=data.bonus_depreciation_pct,
        notes=data.notes
    )


@app.get("/api/v1/business/tax/assets", tags=["Farm Business"])
async def get_all_assets(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all depreciable assets"""
    service = get_farm_business_service()
    return service.get_all_assets()


@app.get("/api/v1/business/tax/assets/{asset_id}/schedule", tags=["Farm Business"])
async def get_depreciation_schedule(
    asset_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get full depreciation schedule for an asset"""
    service = get_farm_business_service()
    result = service.get_depreciation_schedule(asset_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/business/tax/depreciation/{year}", tags=["Farm Business"])
async def get_annual_depreciation(
    year: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get total depreciation expense for a tax year"""
    service = get_farm_business_service()
    return service.get_annual_depreciation(year)


@app.post("/api/v1/business/tax/section179/optimize", tags=["Farm Business"])
async def optimize_section_179(
    net_income: float,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Optimize Section 179 deductions.

    Maximizes deductions within income limits.
    """
    service = get_farm_business_service()
    return service.calculate_section_179_optimization(net_income)


@app.post("/api/v1/business/tax/projection", tags=["Farm Business"])
async def project_tax_liability(
    data: TaxProjectionRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Project tax liability.

    Estimates income tax and self-employment tax.
    """
    service = get_farm_business_service()
    return service.project_tax_liability(
        tax_year=data.tax_year,
        entity_type=data.entity_type,
        gross_income=data.gross_income,
        total_expenses=data.total_expenses
    )


@app.get("/api/v1/business/tax/types", tags=["Farm Business"])
async def get_tax_types():
    """Get available asset types and depreciation methods"""
    return {
        "asset_types": [a.value for a in AssetType],
        "depreciation_methods": [d.value for d in DepreciationMethod],
        "entity_types": [e.value for e in TaxEntity],
        "macrs_rates": MACRS_RATES
    }


# ----- Succession Planning Endpoints -----

@app.post("/api/v1/business/succession/family", tags=["Farm Business"])
async def add_family_member(
    data: FamilyMemberRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a family member to succession plan.

    Tracks ownership, involvement, and skills.
    """
    service = get_farm_business_service()
    return service.add_family_member(
        name=data.name,
        role=data.role,
        birth_date=data.birth_date,
        ownership_pct=data.ownership_pct,
        involvement_level=data.involvement_level,
        skills=data.skills,
        notes=data.notes
    )


@app.get("/api/v1/business/succession/family", tags=["Farm Business"])
async def get_family_members(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all family members in succession plan"""
    service = get_farm_business_service()
    return service.get_family_members()


@app.post("/api/v1/business/succession/transfers", tags=["Farm Business"])
async def create_asset_transfer_plan(
    data: AssetTransferRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Create an asset transfer plan.

    Plans transfers via sale, gift, trust, etc.
    """
    service = get_farm_business_service()
    return service.create_asset_transfer_plan(
        asset_name=data.asset_name,
        asset_value=data.asset_value,
        transfer_method=data.transfer_method,
        from_member_id=data.from_member_id,
        to_member_id=data.to_member_id,
        target_date=data.target_date,
        notes=data.notes
    )


@app.get("/api/v1/business/succession/transfers", tags=["Farm Business"])
async def get_transfer_plans(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all asset transfer plans"""
    service = get_farm_business_service()
    return service.get_transfer_plans()


@app.post("/api/v1/business/succession/milestones", tags=["Farm Business"])
async def add_succession_milestone(
    data: SuccessionMilestoneRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a succession planning milestone.

    Track progress on transition goals.
    """
    service = get_farm_business_service()
    return service.add_milestone(
        title=data.title,
        category=data.category,
        description=data.description,
        target_date=data.target_date,
        assigned_to=data.assigned_to
    )


@app.get("/api/v1/business/succession/milestones", tags=["Farm Business"])
async def get_succession_milestones(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get all succession milestones"""
    service = get_farm_business_service()
    return service.get_milestones()


@app.put("/api/v1/business/succession/milestones/{milestone_id}/complete", tags=["Farm Business"])
async def complete_milestone(
    milestone_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Mark a succession milestone as complete"""
    service = get_farm_business_service()
    result = service.complete_milestone(milestone_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/business/succession/summary", tags=["Farm Business"])
async def get_succession_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get succession planning summary"""
    service = get_farm_business_service()
    return service.get_succession_summary()


@app.get("/api/v1/business/succession/roles", tags=["Farm Business"])
async def get_family_roles():
    """Get available family roles"""
    return {
        "roles": [r.value for r in FamilyRole],
        "transfer_methods": [t.value for t in TransferMethod],
        "milestone_categories": [m.value for m in MilestoneCategory]
    }


# ----- Benchmarking Dashboard Endpoints -----

@app.post("/api/v1/business/benchmarks", tags=["Farm Business"])
async def record_benchmark_data(
    data: BenchmarkDataRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Record benchmark data for a field/year.

    Track yields, costs, revenues for comparison.
    """
    service = get_farm_business_service()
    return service.record_benchmark_data(
        field_id=data.field_id,
        crop=data.crop,
        crop_year=data.crop_year,
        metrics=data.metrics
    )


@app.get("/api/v1/business/benchmarks/{field_id}", tags=["Farm Business"])
async def get_field_benchmarks(
    field_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get benchmark data for a field"""
    service = get_farm_business_service()
    return service.get_field_benchmarks(field_id)


@app.get("/api/v1/business/benchmarks/compare/{field_id}/{crop_year}", tags=["Farm Business"])
async def compare_to_regional(
    field_id: str,
    crop_year: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Compare field performance to regional benchmarks"""
    service = get_farm_business_service()
    return service.compare_to_regional(field_id, crop_year)


@app.get("/api/v1/business/benchmarks/yoy/{field_id}", tags=["Farm Business"])
async def get_year_over_year(
    field_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get year-over-year comparison for a field"""
    service = get_farm_business_service()
    return service.get_yoy_comparison(field_id)


@app.get("/api/v1/business/benchmarks/metrics", tags=["Farm Business"])
async def get_benchmark_metrics():
    """Get available benchmark metrics"""
    return {
        "metrics": [m.value for m in BenchmarkMetric]
    }


# ----- Document Vault Endpoints -----

@app.post("/api/v1/business/documents", tags=["Farm Business"])
async def add_document(
    data: DocumentUploadRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """
    Add a document to the vault.

    Organize farm documents with tags and expiration tracking.
    """
    service = get_farm_business_service()
    return service.add_document(
        name=data.name,
        category=data.category,
        file_path=data.file_path,
        file_type=data.file_type,
        document_date=data.document_date,
        year=data.year,
        tags=data.tags,
        description=data.description,
        expiration_date=data.expiration_date,
        related_entity=data.related_entity
    )


@app.get("/api/v1/business/documents", tags=["Farm Business"])
async def get_all_documents(
    category: str = None,
    year: int = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get documents with optional filters"""
    service = get_farm_business_service()
    return service.get_documents(category, year)


@app.get("/api/v1/business/documents/search", tags=["Farm Business"])
async def search_documents(
    query: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Search documents by name, tags, or description"""
    service = get_farm_business_service()
    return service.search_documents(query)


@app.get("/api/v1/business/documents/expiring", tags=["Farm Business"])
async def get_expiring_documents(
    days: int = 30,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get documents expiring within specified days"""
    service = get_farm_business_service()
    return service.get_expiring_documents(days)


@app.delete("/api/v1/business/documents/{document_id}", tags=["Farm Business"])
async def delete_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Delete a document from the vault"""
    service = get_farm_business_service()
    result = service.delete_document(document_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/api/v1/business/documents/categories", tags=["Farm Business"])
async def get_document_categories():
    """Get available document categories"""
    return {
        "categories": [c.value for c in DocumentCategory]
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
