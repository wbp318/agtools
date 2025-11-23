"""
Professional Crop Consulting System - FastAPI Backend
Main application entry point
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
    description="Professional-grade crop consulting system for corn and soybean pest/disease management",
    version="1.0.0"
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
