"""
Optimization Router
AgTools v6.13.0

Handles:
- Input cost optimization (labor, fertilizer, pesticides, irrigation)
- Pricing service
- Spray timing optimization
- Yield response optimization
"""

from typing import List, Optional
from datetime import date
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from middleware.auth_middleware import get_current_active_user, AuthenticatedUser

router = APIRouter(prefix="/api/v1", tags=["Optimization"])


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


class IrrigationType(str, Enum):
    CENTER_PIVOT = "center_pivot"
    DRIP = "drip"
    FLOOD = "flood"
    SPRINKLER = "sprinkler"
    SUBSURFACE = "subsurface"


class WaterSource(str, Enum):
    GROUNDWATER_WELL = "groundwater_well"
    SURFACE_WATER = "surface_water"
    MUNICIPAL = "municipal"


class InputCategory(str, Enum):
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    SEED = "seed"
    FUEL = "fuel"
    CUSTOM_APPLICATION = "custom_application"


class Region(str, Enum):
    MIDWEST_CORN_BELT = "midwest_corn_belt"
    SOUTHERN_PLAINS = "southern_plains"
    NORTHERN_PLAINS = "northern_plains"
    PACIFIC_NORTHWEST = "pacific_northwest"
    SOUTHEAST = "southeast"


class OptimizationPriority(str, Enum):
    COST_REDUCTION = "cost_reduction"
    ROI_MAXIMIZATION = "roi_maximization"
    SUSTAINABILITY = "sustainability"
    RISK_REDUCTION = "risk_reduction"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class FieldItem(BaseModel):
    name: str
    acres: float


class LaborCostRequest(BaseModel):
    fields: List[FieldItem]
    scouting_frequency_days: int = 7
    season_length_days: int = 120
    custom_labor_rates: Optional[dict] = None


class ApplicationLaborRequest(BaseModel):
    acres: float
    application_type: str
    equipment_type: str
    tank_capacity_gallons: float = 500
    application_rate_gpa: float = 15
    custom_application: bool = False
    custom_rate_per_acre: Optional[float] = None


class FertilizerOptimizationRequest(BaseModel):
    crop: CropType
    yield_goal: float
    acres: float
    soil_test_p_ppm: float
    soil_test_k_ppm: float
    soil_ph: float = 6.5
    organic_matter_percent: float = 3.0
    nitrogen_credit_lb_per_acre: float = 0


class PesticideComparisonRequest(BaseModel):
    products: List[dict]
    acres: float
    application_method: str = "ground"
    include_generics: bool = True


class SprayProgramRequest(BaseModel):
    crop: CropType
    acres: float
    spray_applications: List[dict]
    include_scouting_cost: bool = True


class IrrigationWaterNeedRequest(BaseModel):
    crop: CropType
    growth_stage: GrowthStage
    reference_et_inches_per_day: float
    recent_rainfall_inches: float = 0
    soil_moisture_percent: Optional[float] = None


class IrrigationCostRequest(BaseModel):
    acres: float
    inches_to_apply: float
    irrigation_type: IrrigationType
    water_source: WaterSource
    pumping_depth_ft: float = 100


class IrrigationSeasonRequest(BaseModel):
    crop: CropType
    acres: float
    irrigation_type: IrrigationType
    water_source: WaterSource
    season_start: date
    season_end: date
    expected_rainfall_inches: float = 15
    soil_water_holding_capacity_inches: float = 2
    pumping_depth_ft: float = 100


class WaterSavingsAnalysisRequest(BaseModel):
    current_usage_acre_inches: float
    acres: float
    irrigation_type: IrrigationType
    water_source: WaterSource


class CropItem(BaseModel):
    crop: CropType
    acres: float
    yield_goal: float


class CompleteFarmAnalysisRequest(BaseModel):
    total_acres: float
    crops: List[CropItem]
    irrigation_type: Optional[IrrigationType] = None
    water_source: Optional[WaterSource] = None
    soil_test_p_ppm: Optional[float] = None
    soil_test_k_ppm: Optional[float] = None
    season_length_days: int = 120
    optimization_priority: OptimizationPriority = OptimizationPriority.COST_REDUCTION


class QuickEstimateRequest(BaseModel):
    acres: float
    crop: CropType
    is_irrigated: bool = False
    yield_goal: Optional[float] = None


class PriceSetRequest(BaseModel):
    product_id: str
    price: float
    unit: str
    notes: Optional[str] = None


# ============================================================================
# INPUT COST OPTIMIZATION ENDPOINTS
# ============================================================================

@router.post("/optimize/labor/scouting", tags=["Cost Optimization"])
async def calculate_scouting_costs(request: LaborCostRequest):
    """Calculate and optimize scouting labor costs."""
    from services.labor_optimizer import get_labor_optimizer

    optimizer = get_labor_optimizer(request.custom_labor_rates)
    fields = [{"name": f.name, "acres": f.acres} for f in request.fields]

    result = optimizer.calculate_scouting_costs(
        fields=fields,
        scouting_frequency_days=request.scouting_frequency_days,
        season_length_days=request.season_length_days
    )

    return result


@router.post("/optimize/labor/application", tags=["Cost Optimization"])
async def calculate_application_labor(request: ApplicationLaborRequest):
    """Calculate labor costs for spray/fertilizer applications."""
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


@router.post("/optimize/labor/seasonal-budget", tags=["Cost Optimization"])
async def calculate_seasonal_labor_budget(
    total_acres: float,
    crop: CropType,
    spray_applications: int = 3,
    fertilizer_applications: int = 2,
    scouting_frequency_days: int = 7,
    season_length_days: int = 120
):
    """Calculate total seasonal labor budget for all field operations."""
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


@router.post("/optimize/fertilizer", tags=["Cost Optimization"])
async def optimize_fertilizer_program(request: FertilizerOptimizationRequest):
    """Optimize fertilizer program based on yield goal and soil tests."""
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


@router.post("/optimize/pesticides/compare", tags=["Cost Optimization"])
async def compare_pesticide_options(request: PesticideComparisonRequest):
    """Compare pesticide options to find most economical choice."""
    from services.application_cost_optimizer import get_application_optimizer

    optimizer = get_application_optimizer()

    result = optimizer.compare_pesticide_options(
        product_options=request.products,
        acres=request.acres,
        application_method=request.application_method,
        include_generics=request.include_generics
    )

    return result


@router.post("/optimize/spray-program", tags=["Cost Optimization"])
async def calculate_spray_program_costs(request: SprayProgramRequest):
    """Calculate total costs for a complete spray program."""
    from services.application_cost_optimizer import get_application_optimizer

    optimizer = get_application_optimizer()

    result = optimizer.calculate_spray_program_costs(
        crop=request.crop.value,
        acres=request.acres,
        spray_program=request.spray_applications,
        include_scouting=request.include_scouting_cost
    )

    return result


@router.post("/optimize/irrigation/water-need", tags=["Irrigation"])
async def calculate_crop_water_need(request: IrrigationWaterNeedRequest):
    """Calculate current crop water need based on growth stage and conditions."""
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


@router.post("/optimize/irrigation/cost", tags=["Irrigation"])
async def calculate_irrigation_cost(request: IrrigationCostRequest):
    """Calculate total cost of an irrigation event."""
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


@router.post("/optimize/irrigation/season", tags=["Irrigation"])
async def optimize_irrigation_season(request: IrrigationSeasonRequest):
    """Create optimized irrigation schedule for the entire season."""
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


@router.get("/optimize/irrigation/system-comparison", tags=["Irrigation"])
async def compare_irrigation_systems(
    acres: float,
    annual_water_need_inches: float = 18,
    water_source: WaterSource = WaterSource.GROUNDWATER_WELL,
    current_system: Optional[str] = None
):
    """Compare different irrigation systems for cost effectiveness."""
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.compare_irrigation_systems(
        acres=acres,
        annual_water_need_inches=annual_water_need_inches,
        water_source=water_source.value,
        current_system=current_system
    )

    return result


@router.post("/optimize/irrigation/water-savings", tags=["Irrigation"])
async def analyze_water_savings(request: WaterSavingsAnalysisRequest):
    """Analyze strategies to reduce water usage and costs."""
    from services.irrigation_optimizer import get_irrigation_optimizer

    optimizer = get_irrigation_optimizer()

    result = optimizer.analyze_water_savings_strategies(
        current_usage_acre_inches=request.current_usage_acre_inches,
        acres=request.acres,
        irrigation_type=request.irrigation_type.value,
        water_source=request.water_source.value
    )

    return result


@router.post("/optimize/complete-analysis", tags=["Cost Optimization"])
async def complete_farm_cost_analysis(request: CompleteFarmAnalysisRequest):
    """Perform complete farm input cost analysis."""
    from services.input_cost_optimizer import InputCostOptimizer, FarmProfile
    from services.input_cost_optimizer import OptimizationPriority as OPEnum

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


@router.post("/optimize/quick-estimate", tags=["Cost Optimization"])
async def quick_cost_estimate(request: QuickEstimateRequest):
    """Quick cost estimate for planning purposes."""
    from services.input_cost_optimizer import InputCostOptimizer

    optimizer = InputCostOptimizer()

    result = optimizer.quick_cost_estimate(
        acres=request.acres,
        crop=request.crop.value,
        is_irrigated=request.is_irrigated,
        yield_goal=request.yield_goal
    )

    return result


@router.post("/optimize/budget-worksheet", tags=["Cost Optimization"])
async def generate_budget_worksheet(request: CompleteFarmAnalysisRequest):
    """Generate a complete budget worksheet for the farm."""
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
# PRICING SERVICE ENDPOINTS
# ============================================================================

@router.get("/pricing/prices", tags=["Pricing"])
async def get_all_prices(
    category: Optional[InputCategory] = None,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """Get all current prices (custom + defaults)."""
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


@router.get("/pricing/price/{product_id}", tags=["Pricing"])
async def get_price(
    product_id: str,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """Get price for a specific product."""
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)
    price = service.get_price(product_id)

    if not price:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    return price


@router.post("/pricing/set-price", tags=["Pricing"])
async def set_custom_price(
    request: PriceSetRequest,
    region: Region = Region.MIDWEST_CORN_BELT,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Set a custom price for a product."""
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)

    result = service.set_custom_price(
        product_id=request.product_id,
        price=request.price,
        unit=request.unit,
        notes=request.notes
    )

    return result


@router.get("/pricing/alerts", tags=["Pricing"])
async def get_price_alerts(
    region: Region = Region.MIDWEST_CORN_BELT
):
    """Get price alerts for significant price changes."""
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)
    alerts = service.get_price_alerts()

    return {"alerts": alerts}


@router.get("/pricing/budget-prices/{crop}", tags=["Pricing"])
async def get_budget_prices(
    crop: CropType,
    region: Region = Region.MIDWEST_CORN_BELT
):
    """Get all prices needed for crop budgeting."""
    from services.pricing_service import get_pricing_service

    service = get_pricing_service(region=region.value)
    prices = service.get_budget_prices(crop.value)

    return prices
