"""
AI/ML Intelligence Router
AgTools v6.13.2

Handles:
- Crop health scoring
- Yield prediction
- Smart expense categorization
- Weather-based spray AI
- Pest/disease identification
"""

from typing import List, Optional, Dict, Any
from datetime import date
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from pydantic import BaseModel, Field

from middleware.auth_middleware import get_current_active_user, AuthenticatedUser
from middleware.rate_limiter import limiter, RATE_STRICT, RATE_MODERATE

router = APIRouter(prefix="/api/v1", tags=["AI/ML"])


# ============================================================================
# ENUMS
# ============================================================================

class CropType(str, Enum):
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"


class GrowthStage(str, Enum):
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
    VC = "VC"
    V2 = "V2"
    V4 = "V4"


class ProblemType(str, Enum):
    PEST = "pest"
    DISEASE = "disease"
    NUTRIENT = "nutrient_deficiency"
    WEED = "weed"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

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


class YieldPredictionRequest(BaseModel):
    field_id: int
    crop: CropType
    growth_stage: GrowthStage
    plant_population: Optional[float] = None
    soil_moisture: Optional[float] = None
    rainfall_to_date: Optional[float] = None
    gdd_accumulated: Optional[float] = None


# ============================================================================
# PEST/DISEASE IDENTIFICATION ENDPOINTS
# ============================================================================

@router.post("/identify/pest", response_model=List[PestInfo], tags=["Identification"])
@limiter.limit(RATE_MODERATE)
async def identify_pest(request: Request, pest_request: PestIdentificationRequest):
    """Identify pest based on symptoms and conditions. Rate limited: 30/minute."""
    from services.pest_disease_service import get_pest_disease_service

    service = get_pest_disease_service()
    results = service.identify_pest(
        crop=pest_request.crop.value,
        growth_stage=pest_request.growth_stage.value,
        symptoms=pest_request.symptoms,
        field_conditions=pest_request.field_conditions
    )

    return results


@router.post("/identify/disease", response_model=List[DiseaseInfo], tags=["Identification"])
@limiter.limit(RATE_MODERATE)
async def identify_disease(request: Request, disease_request: DiseaseIdentificationRequest):
    """Identify disease based on symptoms and conditions. Rate limited: 30/minute."""
    from services.pest_disease_service import get_pest_disease_service

    service = get_pest_disease_service()
    results = service.identify_disease(
        crop=disease_request.crop.value,
        growth_stage=disease_request.growth_stage.value,
        symptoms=disease_request.symptoms,
        weather_conditions=disease_request.weather_conditions
    )

    return results


@router.post("/identify/image", tags=["Identification"])
@limiter.limit(RATE_STRICT)
async def identify_from_image(
    request: Request,
    file: UploadFile = File(...),
    crop: Optional[CropType] = None,
    growth_stage: Optional[GrowthStage] = None
):
    """Identify pest or disease from uploaded image. Rate limited: 5/minute (compute-intensive)."""
    from services.ai_image_service import get_ai_image_service

    service = get_ai_image_service()

    content = await file.read()
    # analyze_image is an async method, must await it
    result = await service.analyze_image(
        image_bytes=content,
        crop=crop.value if crop else "corn",
        growth_stage=growth_stage.value if growth_stage else None
    )

    # Convert ImageAnalysisResult to dict for JSON response
    return {
        "provider": result.provider.value,
        "identifications": result.mapped_identifications,
        "confidence": result.confidence,
        "processing_time_ms": result.processing_time_ms,
        "notes": result.notes
    }


# ============================================================================
# CROP HEALTH SCORING
# ============================================================================

@router.get("/health/field/{field_id}", tags=["Crop Health"])
async def get_field_health_score(
    field_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get health score for a specific field."""
    from services.crop_health_service import get_crop_health_service

    service = get_crop_health_service()
    result = service.get_field_health_score(field_id)

    if not result:
        raise HTTPException(status_code=404, detail="Field not found")

    return result


@router.get("/health/summary", tags=["Crop Health"])
async def get_health_summary(
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get health summary across all fields."""
    from services.crop_health_service import get_crop_health_service

    service = get_crop_health_service()
    return service.get_health_summary()


@router.post("/health/calculate", tags=["Crop Health"])
async def calculate_health_score(
    field_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Recalculate health score for a field."""
    from services.crop_health_service import get_crop_health_service

    service = get_crop_health_service()
    result = service.calculate_health_score(field_id)

    return result


# ============================================================================
# YIELD PREDICTION
# ============================================================================

@router.post("/yield/predict", tags=["Yield Prediction"])
@limiter.limit(RATE_MODERATE)
async def predict_yield(
    request: Request,
    yield_request: YieldPredictionRequest,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Predict yield for a field based on current conditions. Rate limited: 30/minute."""
    from services.yield_prediction_service import get_yield_prediction_service

    service = get_yield_prediction_service()
    result = service.predict_yield(
        field_id=yield_request.field_id,
        crop=yield_request.crop.value,
        growth_stage=yield_request.growth_stage.value,
        plant_population=yield_request.plant_population,
        soil_moisture=yield_request.soil_moisture,
        rainfall_to_date=yield_request.rainfall_to_date,
        gdd_accumulated=yield_request.gdd_accumulated
    )

    return result


@router.get("/yield/field/{field_id}/history", tags=["Yield Prediction"])
async def get_yield_history(
    field_id: int,
    years: int = 5,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get yield prediction history for a field."""
    from services.yield_prediction_service import get_yield_prediction_service

    service = get_yield_prediction_service()
    return service.get_yield_history(field_id, years)


# ============================================================================
# SMART EXPENSE CATEGORIZATION
# ============================================================================

@router.post("/expenses/categorize", tags=["Smart Categorization"])
async def categorize_expense(
    description: str,
    amount: Optional[float] = None,
    vendor: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Automatically categorize an expense."""
    from services.expense_categorization_service import get_expense_categorization_service

    service = get_expense_categorization_service()
    result = service.categorize_expense(
        description=description,
        amount=amount,
        vendor=vendor
    )

    return result


@router.post("/expenses/categorize/batch", tags=["Smart Categorization"])
@limiter.limit(RATE_MODERATE)
async def categorize_expenses_batch(
    request: Request,
    expenses: List[dict],
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Categorize multiple expenses at once. Rate limited: 30/minute."""
    from services.expense_categorization_service import get_expense_categorization_service

    service = get_expense_categorization_service()
    results = service.categorize_batch(expenses)

    return {"categorized": results}


# ============================================================================
# WEATHER-BASED SPRAY AI
# ============================================================================

@router.get("/spray/recommendation", tags=["Spray AI"])
async def get_spray_recommendation(
    field_id: int,
    product_type: str,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get AI recommendation for spray timing."""
    from services.spray_ai_service import get_spray_ai_service

    service = get_spray_ai_service()
    result = service.get_spray_recommendation(
        field_id=field_id,
        product_type=product_type
    )

    return result


@router.get("/spray/windows", tags=["Spray AI"])
async def get_spray_windows(
    days_ahead: int = 7,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get optimal spray windows for the next N days."""
    from services.spray_ai_service import get_spray_ai_service

    service = get_spray_ai_service()
    return service.get_spray_windows(days_ahead)


@router.get("/weather/spray-window", tags=["Weather"])
async def get_weather_spray_window(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    days_ahead: int = 5
):
    """Get spray window recommendations based on weather forecast."""
    from services.weather_service import get_weather_service

    service = get_weather_service()
    result = service.get_spray_windows(
        latitude=latitude,
        longitude=longitude,
        days_ahead=days_ahead
    )

    return result
