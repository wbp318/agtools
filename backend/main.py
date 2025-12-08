"""
Professional Crop Consulting System - FastAPI Backend
Main application entry point with Input Cost Optimization
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="AgTools Professional Crop Consulting API",
    description="Professional-grade crop consulting system with pest/disease management and input cost optimization",
    version="2.0.0",
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
