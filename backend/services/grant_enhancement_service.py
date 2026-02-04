"""
Grant Enhancement Service for AgTools
Version: 3.6.0

This service extends grant support with:
- Economic Impact Calculator (precision ag ROI for SBIR)
- Data Quality/Completeness Tracker (grant readiness scoring)
- Partnership Opportunity Finder (research matching)
"""

from datetime import datetime, date, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import statistics


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class PrecisionAgTechnology(Enum):
    """Precision agriculture technologies"""
    GPS_GUIDANCE = "gps_guidance"
    AUTOSTEER = "autosteer"
    SECTION_CONTROL_PLANTER = "section_control_planter"
    SECTION_CONTROL_SPRAYER = "section_control_sprayer"
    VARIABLE_RATE_SEEDING = "variable_rate_seeding"
    VARIABLE_RATE_FERTILIZER = "variable_rate_fertilizer"
    VARIABLE_RATE_IRRIGATION = "variable_rate_irrigation"
    YIELD_MONITOR = "yield_monitor"
    SOIL_SAMPLING_GRID = "soil_sampling_grid"
    DRONE_IMAGERY = "drone_imagery"
    SATELLITE_IMAGERY = "satellite_imagery"
    TELEMATICS = "telematics"
    MOISTURE_SENSORS = "moisture_sensors"
    WEATHER_STATION = "weather_station"


class DataCategory(Enum):
    """Categories of farm data for completeness tracking"""
    FIELD_BOUNDARIES = "field_boundaries"
    SOIL_TESTS = "soil_tests"
    YIELD_DATA = "yield_data"
    PLANTING_RECORDS = "planting_records"
    APPLICATION_RECORDS = "application_records"
    HARVEST_RECORDS = "harvest_records"
    WEATHER_DATA = "weather_data"
    FINANCIAL_RECORDS = "financial_records"
    EQUIPMENT_RECORDS = "equipment_records"
    IMAGERY = "imagery"
    SCOUTING_RECORDS = "scouting_records"
    SUSTAINABILITY_METRICS = "sustainability_metrics"


class ResearchArea(Enum):
    """Agricultural research areas"""
    PRECISION_AG = "precision_agriculture"
    SUSTAINABILITY = "sustainability"
    SOIL_HEALTH = "soil_health"
    PEST_MANAGEMENT = "pest_management"
    VARIETY_TRIALS = "variety_trials"
    NUTRIENT_MANAGEMENT = "nutrient_management"
    WATER_MANAGEMENT = "water_management"
    COVER_CROPS = "cover_crops"
    CARBON_SEQUESTRATION = "carbon_sequestration"
    CLIMATE_ADAPTATION = "climate_adaptation"
    DIGITAL_AGRICULTURE = "digital_agriculture"
    ECONOMICS = "economics"


class PartnerType(Enum):
    """Types of research partners"""
    UNIVERSITY = "university"
    EXTENSION = "extension"
    FEDERAL_AGENCY = "federal_agency"
    NONPROFIT = "nonprofit"
    INDUSTRY = "industry"
    COOPERATIVE = "cooperative"


@dataclass
class TechnologyInvestment:
    """Record of precision ag technology investment"""
    technology: PrecisionAgTechnology
    purchase_year: int
    purchase_cost: float
    annual_subscription: float  # For services like JD Ops
    acres_covered: float
    expected_life_years: int
    notes: str = ""


@dataclass
class DataRecord:
    """Record of data availability"""
    category: DataCategory
    years_available: List[int]
    completeness_pct: float  # 0-100
    format: str  # e.g., "JD Operations Center", "CSV", "Paper"
    last_updated: date
    notes: str = ""


@dataclass
class PartnerOpportunity:
    """Research partnership opportunity"""
    partner_name: str
    partner_type: PartnerType
    research_areas: List[ResearchArea]
    contact_info: str
    website: str
    grant_programs: List[str]
    requirements: List[str]
    match_score: int  # 0-100


# =============================================================================
# PRECISION AG BENEFIT RATES
# =============================================================================

# Industry-validated savings rates for precision ag technologies
TECHNOLOGY_BENEFITS = {
    PrecisionAgTechnology.GPS_GUIDANCE: {
        "name": "GPS Guidance",
        "overlap_reduction_pct": 5.0,  # 5% overlap reduction
        "input_savings_per_acre": 3.50,
        "yield_improvement_pct": 0.5,
        "time_savings_pct": 10.0,
        "typical_cost": 3000,
        "annual_sub": 0,
        "life_years": 10,
        "description": "Basic GPS lightbar guidance for reduced overlap"
    },
    PrecisionAgTechnology.AUTOSTEER: {
        "name": "AutoSteer/AutoTrac",
        "overlap_reduction_pct": 10.0,  # 10% overlap reduction
        "input_savings_per_acre": 8.00,
        "yield_improvement_pct": 1.5,
        "time_savings_pct": 15.0,
        "typical_cost": 15000,
        "annual_sub": 1500,  # JD activation
        "life_years": 10,
        "description": "Automated steering with RTK precision"
    },
    PrecisionAgTechnology.SECTION_CONTROL_PLANTER: {
        "name": "Planter Section Control",
        "overlap_reduction_pct": 3.0,  # Seed overlap in point rows
        "input_savings_per_acre": 12.00,  # Seed is expensive
        "yield_improvement_pct": 2.0,  # Better stands
        "time_savings_pct": 5.0,
        "typical_cost": 25000,
        "annual_sub": 0,
        "life_years": 10,
        "description": "Individual row clutches for turn compensation"
    },
    PrecisionAgTechnology.SECTION_CONTROL_SPRAYER: {
        "name": "Sprayer Section Control",
        "overlap_reduction_pct": 8.0,
        "input_savings_per_acre": 6.50,
        "yield_improvement_pct": 0.5,
        "time_savings_pct": 5.0,
        "typical_cost": 12000,
        "annual_sub": 0,
        "life_years": 10,
        "description": "Boom section control for reduced chemical overlap"
    },
    PrecisionAgTechnology.VARIABLE_RATE_SEEDING: {
        "name": "Variable Rate Seeding",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 8.00,
        "yield_improvement_pct": 3.0,  # Right population for each zone
        "time_savings_pct": 0,
        "typical_cost": 8000,
        "annual_sub": 500,  # Prescription services
        "life_years": 10,
        "description": "Zone-based seeding rate optimization"
    },
    PrecisionAgTechnology.VARIABLE_RATE_FERTILIZER: {
        "name": "Variable Rate Fertilizer",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 15.00,  # Significant N savings
        "yield_improvement_pct": 2.5,
        "time_savings_pct": 0,
        "typical_cost": 10000,
        "annual_sub": 800,
        "life_years": 10,
        "description": "Zone-based nutrient application"
    },
    PrecisionAgTechnology.VARIABLE_RATE_IRRIGATION: {
        "name": "Variable Rate Irrigation",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 25.00,  # Water + pumping costs
        "yield_improvement_pct": 5.0,
        "time_savings_pct": 20.0,
        "typical_cost": 50000,
        "annual_sub": 2000,
        "life_years": 15,
        "description": "Zone-based irrigation management"
    },
    PrecisionAgTechnology.YIELD_MONITOR: {
        "name": "Yield Monitor",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 2.00,  # Enables better decisions
        "yield_improvement_pct": 1.0,
        "time_savings_pct": 0,
        "typical_cost": 8000,
        "annual_sub": 0,
        "life_years": 10,
        "description": "Harvest yield mapping for zone management"
    },
    PrecisionAgTechnology.SOIL_SAMPLING_GRID: {
        "name": "Grid Soil Sampling",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 10.00,
        "yield_improvement_pct": 2.0,
        "time_savings_pct": 0,
        "typical_cost": 0,  # Service cost
        "annual_sub": 1200,  # Per sampling cycle
        "life_years": 1,
        "description": "2.5-acre grid sampling for VRT prescriptions"
    },
    PrecisionAgTechnology.DRONE_IMAGERY: {
        "name": "Drone Imagery/Scouting",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 4.00,
        "yield_improvement_pct": 1.5,
        "time_savings_pct": 50.0,  # Scouting time
        "typical_cost": 5000,
        "annual_sub": 500,
        "life_years": 5,
        "description": "UAV-based crop monitoring and scouting"
    },
    PrecisionAgTechnology.SATELLITE_IMAGERY: {
        "name": "Satellite Imagery",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 2.00,
        "yield_improvement_pct": 0.5,
        "time_savings_pct": 30.0,
        "typical_cost": 0,
        "annual_sub": 1500,
        "life_years": 1,
        "description": "Regular satellite imagery for crop monitoring"
    },
    PrecisionAgTechnology.TELEMATICS: {
        "name": "Machine Telematics",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 1.50,
        "yield_improvement_pct": 0,
        "time_savings_pct": 10.0,
        "typical_cost": 2000,
        "annual_sub": 600,
        "life_years": 10,
        "description": "JD Connected/telematics for machine monitoring"
    },
    PrecisionAgTechnology.MOISTURE_SENSORS: {
        "name": "Soil Moisture Sensors",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 8.00,  # Water savings
        "yield_improvement_pct": 3.0,
        "time_savings_pct": 15.0,
        "typical_cost": 3000,
        "annual_sub": 400,
        "life_years": 5,
        "description": "In-field soil moisture monitoring"
    },
    PrecisionAgTechnology.WEATHER_STATION: {
        "name": "On-Farm Weather Station",
        "overlap_reduction_pct": 0,
        "input_savings_per_acre": 2.00,
        "yield_improvement_pct": 1.0,
        "time_savings_pct": 5.0,
        "typical_cost": 2500,
        "annual_sub": 300,
        "life_years": 10,
        "description": "Local weather data for spray timing and irrigation"
    },
}


# =============================================================================
# DATA QUALITY REQUIREMENTS BY GRANT TYPE
# =============================================================================

GRANT_DATA_REQUIREMENTS = {
    "USDA_SBIR": {
        "required": [
            DataCategory.YIELD_DATA,
            DataCategory.FINANCIAL_RECORDS,
            DataCategory.EQUIPMENT_RECORDS,
        ],
        "recommended": [
            DataCategory.FIELD_BOUNDARIES,
            DataCategory.APPLICATION_RECORDS,
            DataCategory.SUSTAINABILITY_METRICS,
        ],
        "nice_to_have": [
            DataCategory.IMAGERY,
            DataCategory.WEATHER_DATA,
        ],
        "min_years": 2,
        "description": "Technology commercialization - need proof of concept data"
    },
    "SARE": {
        "required": [
            DataCategory.FIELD_BOUNDARIES,
            DataCategory.SOIL_TESTS,
            DataCategory.PLANTING_RECORDS,
            DataCategory.APPLICATION_RECORDS,
        ],
        "recommended": [
            DataCategory.YIELD_DATA,
            DataCategory.SUSTAINABILITY_METRICS,
            DataCategory.SCOUTING_RECORDS,
        ],
        "nice_to_have": [
            DataCategory.WEATHER_DATA,
            DataCategory.FINANCIAL_RECORDS,
        ],
        "min_years": 1,
        "description": "Sustainable agriculture research - need baseline practice data"
    },
    "CIG": {
        "required": [
            DataCategory.FIELD_BOUNDARIES,
            DataCategory.SUSTAINABILITY_METRICS,
            DataCategory.APPLICATION_RECORDS,
            DataCategory.YIELD_DATA,
        ],
        "recommended": [
            DataCategory.SOIL_TESTS,
            DataCategory.WEATHER_DATA,
            DataCategory.FINANCIAL_RECORDS,
        ],
        "nice_to_have": [
            DataCategory.IMAGERY,
            DataCategory.SCOUTING_RECORDS,
        ],
        "min_years": 3,
        "description": "Climate-smart innovation - need carbon/sustainability baseline"
    },
    "EQIP": {
        "required": [
            DataCategory.FIELD_BOUNDARIES,
            DataCategory.SOIL_TESTS,
        ],
        "recommended": [
            DataCategory.APPLICATION_RECORDS,
            DataCategory.YIELD_DATA,
        ],
        "nice_to_have": [
            DataCategory.SUSTAINABILITY_METRICS,
            DataCategory.FINANCIAL_RECORDS,
        ],
        "min_years": 1,
        "description": "Conservation practices - need resource concern documentation"
    },
    "NSF_SBIR": {
        "required": [
            DataCategory.YIELD_DATA,
            DataCategory.EQUIPMENT_RECORDS,
            DataCategory.FINANCIAL_RECORDS,
        ],
        "recommended": [
            DataCategory.IMAGERY,
            DataCategory.WEATHER_DATA,
            DataCategory.APPLICATION_RECORDS,
        ],
        "nice_to_have": [
            DataCategory.SUSTAINABILITY_METRICS,
            DataCategory.SCOUTING_RECORDS,
        ],
        "min_years": 2,
        "description": "Technical innovation - need quantitative outcome data"
    },
}


# =============================================================================
# RESEARCH PARTNERSHIP DATABASE
# =============================================================================

RESEARCH_PARTNERS = [
    {
        "name": "LSU AgCenter",
        "type": PartnerType.UNIVERSITY,
        "location": "Baton Rouge, LA",
        "research_areas": [
            ResearchArea.VARIETY_TRIALS,
            ResearchArea.PEST_MANAGEMENT,
            ResearchArea.SOIL_HEALTH,
            ResearchArea.NUTRIENT_MANAGEMENT,
            ResearchArea.SUSTAINABILITY,
        ],
        "contact": "LSU AgCenter Research Station",
        "website": "https://www.lsuagcenter.com/topics/crops",
        "grant_programs": ["SARE", "CIG", "USDA_SBIR"],
        "requirements": ["Field trial space", "Data sharing agreement", "Multi-year commitment"],
        "notes": "Strong corn/soybean/rice programs, CIG partnership opportunity"
    },
    {
        "name": "LSU Department of Agricultural Economics",
        "type": PartnerType.UNIVERSITY,
        "location": "Baton Rouge, LA",
        "research_areas": [
            ResearchArea.ECONOMICS,
            ResearchArea.PRECISION_AG,
            ResearchArea.DIGITAL_AGRICULTURE,
        ],
        "contact": "LSU Ag Economics",
        "website": "https://www.lsu.edu/agriculture/agecon/",
        "grant_programs": ["USDA_SBIR", "NSF_SBIR", "SARE"],
        "requirements": ["Economic data sharing", "Case study participation"],
        "notes": "Good fit for precision ag ROI studies, technology adoption research"
    },
    {
        "name": "Southern University Ag Center",
        "type": PartnerType.UNIVERSITY,
        "location": "Baton Rouge, LA",
        "research_areas": [
            ResearchArea.SUSTAINABILITY,
            ResearchArea.SOIL_HEALTH,
            ResearchArea.COVER_CROPS,
        ],
        "contact": "Southern University Agricultural Research",
        "website": "https://www.suagcenter.com/",
        "grant_programs": ["SARE", "EQIP", "CIG"],
        "requirements": ["Small farm focus", "Outreach participation"],
        "notes": "1890 institution - special grant eligibility"
    },
    {
        "name": "USDA-ARS Southern Regional Research Center",
        "type": PartnerType.FEDERAL_AGENCY,
        "location": "New Orleans, LA",
        "research_areas": [
            ResearchArea.PEST_MANAGEMENT,
            ResearchArea.SUSTAINABILITY,
            ResearchArea.CLIMATE_ADAPTATION,
        ],
        "contact": "USDA-ARS SRRC",
        "website": "https://www.ars.usda.gov/southeast-area/new-orleans-la/",
        "grant_programs": ["CIG", "USDA_SBIR"],
        "requirements": ["Research collaboration", "Data sharing"],
        "notes": "Federal research partnership opportunity"
    },
    {
        "name": "Louisiana Cooperative Extension Service",
        "type": PartnerType.EXTENSION,
        "location": "Statewide, LA",
        "research_areas": [
            ResearchArea.PRECISION_AG,
            ResearchArea.PEST_MANAGEMENT,
            ResearchArea.NUTRIENT_MANAGEMENT,
            ResearchArea.VARIETY_TRIALS,
        ],
        "contact": "Parish Extension Agent",
        "website": "https://www.lsuagcenter.com/portals/our_offices/parishes",
        "grant_programs": ["SARE", "EQIP"],
        "requirements": ["Demonstration field", "Field day hosting"],
        "notes": "Great for outreach component of grants"
    },
    {
        "name": "Delta F.A.R.M.",
        "type": PartnerType.NONPROFIT,
        "location": "Delta Region",
        "research_areas": [
            ResearchArea.WATER_MANAGEMENT,
            ResearchArea.SUSTAINABILITY,
            ResearchArea.SOIL_HEALTH,
        ],
        "contact": "Delta F.A.R.M.",
        "website": "https://www.deltafarm.org/",
        "grant_programs": ["CIG", "SARE", "EQIP"],
        "requirements": ["Water conservation focus", "Best practices implementation"],
        "notes": "Delta water quality and sustainability focus"
    },
    {
        "name": "Louisiana Farm Bureau Federation",
        "type": PartnerType.COOPERATIVE,
        "location": "Statewide, LA",
        "research_areas": [
            ResearchArea.ECONOMICS,
            ResearchArea.PRECISION_AG,
        ],
        "contact": "LA Farm Bureau",
        "website": "https://www.lafarmbureau.org/",
        "grant_programs": ["USDA_SBIR"],
        "requirements": ["Membership", "Industry support letter"],
        "notes": "Good source for letters of support"
    },
    {
        "name": "The Sustainability Consortium",
        "type": PartnerType.NONPROFIT,
        "location": "National",
        "research_areas": [
            ResearchArea.SUSTAINABILITY,
            ResearchArea.CARBON_SEQUESTRATION,
            ResearchArea.DIGITAL_AGRICULTURE,
        ],
        "contact": "TSC Agriculture",
        "website": "https://www.sustainabilityconsortium.org/",
        "grant_programs": ["CIG", "NSF_SBIR"],
        "requirements": ["Sustainability data sharing", "Metric alignment"],
        "notes": "Supply chain sustainability credibility"
    },
    {
        "name": "Field to Market",
        "type": PartnerType.NONPROFIT,
        "location": "National",
        "research_areas": [
            ResearchArea.SUSTAINABILITY,
            ResearchArea.CARBON_SEQUESTRATION,
            ResearchArea.WATER_MANAGEMENT,
        ],
        "contact": "Field to Market",
        "website": "https://fieldtomarket.org/",
        "grant_programs": ["CIG", "SARE"],
        "requirements": ["Fieldprint calculator use", "Continuous improvement"],
        "notes": "Industry-recognized sustainability metrics"
    },
    {
        "name": "National Corn Growers Association",
        "type": PartnerType.COOPERATIVE,
        "location": "National",
        "research_areas": [
            ResearchArea.SUSTAINABILITY,
            ResearchArea.PRECISION_AG,
            ResearchArea.CARBON_SEQUESTRATION,
        ],
        "contact": "NCGA Sustainability",
        "website": "https://www.ncga.com/",
        "grant_programs": ["CIG", "USDA_SBIR"],
        "requirements": ["Corn grower", "Data contribution"],
        "notes": "NCGA Soil Health Partnership connection"
    },
    {
        "name": "United Soybean Board",
        "type": PartnerType.COOPERATIVE,
        "location": "National",
        "research_areas": [
            ResearchArea.SUSTAINABILITY,
            ResearchArea.PRECISION_AG,
            ResearchArea.SOIL_HEALTH,
        ],
        "contact": "USB Research",
        "website": "https://www.unitedsoybean.org/",
        "grant_programs": ["CIG", "SARE"],
        "requirements": ["Soybean grower", "Research participation"],
        "notes": "Checkoff-funded research opportunities"
    },
    {
        "name": "Mississippi State University Extension",
        "type": PartnerType.EXTENSION,
        "location": "Mississippi (Delta Region)",
        "research_areas": [
            ResearchArea.PRECISION_AG,
            ResearchArea.VARIETY_TRIALS,
            ResearchArea.WATER_MANAGEMENT,
        ],
        "contact": "MSU Extension",
        "website": "https://extension.msstate.edu/agriculture",
        "grant_programs": ["SARE", "CIG"],
        "requirements": ["Cross-state collaboration"],
        "notes": "Delta region collaboration opportunity"
    },
    {
        "name": "University of Arkansas Division of Agriculture",
        "type": PartnerType.UNIVERSITY,
        "location": "Arkansas (Delta Region)",
        "research_areas": [
            ResearchArea.PRECISION_AG,
            ResearchArea.WATER_MANAGEMENT,
            ResearchArea.SOIL_HEALTH,
            ResearchArea.VARIETY_TRIALS,
        ],
        "contact": "UA Division of Agriculture",
        "website": "https://www.uaex.uada.edu/",
        "grant_programs": ["SARE", "CIG", "USDA_SBIR"],
        "requirements": ["Regional collaboration"],
        "notes": "Strong rice and row crop programs"
    },
]


# =============================================================================
# GRANT ENHANCEMENT SERVICE CLASS
# =============================================================================

class GrantEnhancementService:
    """Service for advanced grant support features"""

    def __init__(self):
        self.investments: Dict[str, TechnologyInvestment] = {}
        self.data_records: Dict[str, DataRecord] = {}
        self.investment_counter = 0

    # -------------------------------------------------------------------------
    # ECONOMIC IMPACT CALCULATOR
    # -------------------------------------------------------------------------

    def get_technology_catalog(self) -> List[Dict[str, Any]]:
        """Get catalog of precision ag technologies with benefit rates"""
        return [
            {
                "id": tech.value,
                "name": info["name"],
                "description": info["description"],
                "benefits": {
                    "overlap_reduction_pct": info["overlap_reduction_pct"],
                    "input_savings_per_acre": info["input_savings_per_acre"],
                    "yield_improvement_pct": info["yield_improvement_pct"],
                    "time_savings_pct": info["time_savings_pct"]
                },
                "typical_costs": {
                    "purchase": info["typical_cost"],
                    "annual_subscription": info["annual_sub"],
                    "expected_life_years": info["life_years"]
                }
            }
            for tech, info in TECHNOLOGY_BENEFITS.items()
        ]

    def record_technology_investment(
        self,
        technology: str,
        purchase_year: int,
        purchase_cost: float,
        annual_subscription: float,
        acres_covered: float,
        expected_life_years: int,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Record a precision ag technology investment"""
        try:
            tech_enum = PrecisionAgTechnology(technology)
        except ValueError:
            return {"error": f"Unknown technology: {technology}"}

        self.investment_counter += 1
        inv_id = f"INV-{self.investment_counter:04d}"

        investment = TechnologyInvestment(
            technology=tech_enum,
            purchase_year=purchase_year,
            purchase_cost=purchase_cost,
            annual_subscription=annual_subscription,
            acres_covered=acres_covered,
            expected_life_years=expected_life_years,
            notes=notes
        )

        self.investments[inv_id] = investment
        info = TECHNOLOGY_BENEFITS[tech_enum]

        # Calculate annual benefit
        annual_input_savings = info["input_savings_per_acre"] * acres_covered

        # Estimate yield benefit (assume $5/bu corn value, 180 bu/ac base)
        yield_value_per_acre = 180 * 5  # $900/acre gross
        yield_benefit = (info["yield_improvement_pct"] / 100) * yield_value_per_acre * acres_covered

        annual_benefit = annual_input_savings + yield_benefit
        annual_cost = (purchase_cost / expected_life_years) + annual_subscription
        net_annual_benefit = annual_benefit - annual_cost

        return {
            "id": inv_id,
            "technology": technology,
            "technology_name": info["name"],
            "purchase_cost": purchase_cost,
            "acres_covered": acres_covered,
            "annual_benefits": {
                "input_savings": round(annual_input_savings, 2),
                "yield_improvement_value": round(yield_benefit, 2),
                "total_annual_benefit": round(annual_benefit, 2)
            },
            "annual_costs": {
                "depreciation": round(purchase_cost / expected_life_years, 2),
                "subscription": annual_subscription,
                "total_annual_cost": round(annual_cost, 2)
            },
            "net_annual_benefit": round(net_annual_benefit, 2),
            "roi_percent": round((net_annual_benefit / annual_cost) * 100, 1) if annual_cost > 0 else 0,
            "payback_years": round(purchase_cost / annual_benefit, 1) if annual_benefit > 0 else None,
            "message": f"Recorded {info['name']} investment covering {acres_covered} acres"
        }

    def calculate_single_technology_roi(
        self,
        technology: str,
        acres: float,
        purchase_cost: Optional[float] = None,
        annual_subscription: Optional[float] = None,
        years: int = 5,
        corn_price: float = 5.00,
        soybean_price: float = 12.00,
        base_corn_yield: float = 180,
        base_soybean_yield: float = 50
    ) -> Dict[str, Any]:
        """Calculate ROI for a single technology investment"""
        try:
            tech_enum = PrecisionAgTechnology(technology)
        except ValueError:
            return {"error": f"Unknown technology: {technology}"}

        info = TECHNOLOGY_BENEFITS[tech_enum]

        # Use provided costs or defaults
        cost = purchase_cost if purchase_cost is not None else info["typical_cost"]
        sub = annual_subscription if annual_subscription is not None else info["annual_sub"]
        life = info["life_years"]

        # Calculate annual benefits
        input_savings = info["input_savings_per_acre"] * acres

        # Yield improvement (average corn/soy)
        avg_yield_value = ((base_corn_yield * corn_price) + (base_soybean_yield * soybean_price)) / 2
        yield_benefit = (info["yield_improvement_pct"] / 100) * avg_yield_value * acres

        # Time savings (value at $25/hour, 0.5 hours/acre base)
        time_savings_value = (info["time_savings_pct"] / 100) * 0.5 * 25 * acres

        annual_benefit = input_savings + yield_benefit + time_savings_value
        annual_cost = (cost / life) + sub
        net_annual = annual_benefit - annual_cost

        # Multi-year projection
        yearly_projection = []
        cumulative_benefit = 0
        cumulative_cost = cost  # Initial investment

        for year in range(1, years + 1):
            cumulative_benefit += annual_benefit
            cumulative_cost += sub
            net_cumulative = cumulative_benefit - cumulative_cost

            yearly_projection.append({
                "year": year,
                "annual_benefit": round(annual_benefit, 2),
                "annual_cost": round(sub, 2),
                "cumulative_benefit": round(cumulative_benefit, 2),
                "cumulative_cost": round(cumulative_cost, 2),
                "net_position": round(net_cumulative, 2)
            })

        # Payback period
        if annual_benefit > sub:
            payback = cost / (annual_benefit - sub)
        else:
            payback = None

        return {
            "technology": technology,
            "technology_name": info["name"],
            "acres": acres,
            "initial_investment": cost,
            "annual_subscription": sub,
            "expected_life_years": life,

            "annual_benefits_breakdown": {
                "input_savings": round(input_savings, 2),
                "yield_improvement": round(yield_benefit, 2),
                "time_savings": round(time_savings_value, 2),
                "total": round(annual_benefit, 2)
            },

            "benefit_rates": {
                "input_savings_per_acre": info["input_savings_per_acre"],
                "yield_improvement_pct": info["yield_improvement_pct"],
                "overlap_reduction_pct": info["overlap_reduction_pct"],
                "time_savings_pct": info["time_savings_pct"]
            },

            "annual_net_benefit": round(net_annual, 2),
            "roi_percent": round((net_annual / annual_cost) * 100, 1) if annual_cost > 0 else 0,
            "payback_years": round(payback, 1) if payback else "N/A",

            "multi_year_projection": yearly_projection,

            "sbir_summary": f"{info['name']}: ${round(annual_benefit, 0)}/year benefit on {acres} acres, "
                          f"{round(payback, 1) if payback else 'N/A'} year payback, "
                          f"{round((net_annual / annual_cost) * 100, 0) if annual_cost > 0 else 0}% ROI"
        }

    def calculate_portfolio_roi(
        self,
        technologies: Optional[List[str]] = None,
        acres: float = 1000,
        years: int = 5
    ) -> Dict[str, Any]:
        """Calculate combined ROI for portfolio of precision ag investments"""

        if technologies is None:
            # Use recorded investments
            if not self.investments:
                return {"error": "No investments recorded. Provide technologies list or record investments first."}
            tech_list = [inv.technology.value for inv in self.investments.values()]
            acres = statistics.mean([inv.acres_covered for inv in self.investments.values()])
        else:
            tech_list = technologies

        # Calculate each technology
        tech_results = []
        total_investment = 0
        total_annual_benefit = 0
        total_annual_sub = 0

        for tech in tech_list:
            result = self.calculate_single_technology_roi(tech, acres, years=years)
            if "error" not in result:
                tech_results.append({
                    "technology": result["technology_name"],
                    "investment": result["initial_investment"],
                    "annual_benefit": result["annual_benefits_breakdown"]["total"],
                    "annual_subscription": result["annual_subscription"],
                    "roi_percent": result["roi_percent"]
                })
                total_investment += result["initial_investment"]
                total_annual_benefit += result["annual_benefits_breakdown"]["total"]
                total_annual_sub += result["annual_subscription"]

        # Portfolio metrics
        total_annual_cost = total_annual_sub + (total_investment / 10)  # Assume 10 year avg life
        net_annual = total_annual_benefit - total_annual_cost

        if total_annual_benefit > total_annual_sub:
            portfolio_payback = total_investment / (total_annual_benefit - total_annual_sub)
        else:
            portfolio_payback = None

        # Multi-year projection
        yearly = []
        cum_benefit = 0
        cum_cost = total_investment

        for year in range(1, years + 1):
            cum_benefit += total_annual_benefit
            cum_cost += total_annual_sub
            yearly.append({
                "year": year,
                "cumulative_benefit": round(cum_benefit, 2),
                "cumulative_cost": round(cum_cost, 2),
                "net_position": round(cum_benefit - cum_cost, 2)
            })

        return {
            "portfolio_summary": {
                "technologies_count": len(tech_results),
                "acres_covered": acres,
                "total_investment": round(total_investment, 2),
                "total_annual_subscriptions": round(total_annual_sub, 2),
                "total_annual_benefit": round(total_annual_benefit, 2),
                "net_annual_benefit": round(net_annual, 2),
                "portfolio_roi_percent": round((net_annual / total_annual_cost) * 100, 1) if total_annual_cost > 0 else 0,
                "portfolio_payback_years": round(portfolio_payback, 1) if portfolio_payback else "N/A"
            },
            "technologies": tech_results,
            "multi_year_projection": yearly,
            "per_acre_metrics": {
                "investment_per_acre": round(total_investment / acres, 2),
                "annual_benefit_per_acre": round(total_annual_benefit / acres, 2),
                "net_benefit_per_acre": round(net_annual / acres, 2)
            },
            "sbir_narrative": self._generate_sbir_narrative(tech_results, acres, total_investment, total_annual_benefit, portfolio_payback)
        }

    def _generate_sbir_narrative(
        self,
        technologies: List[Dict],
        acres: float,
        investment: float,
        annual_benefit: float,
        payback: Optional[float]
    ) -> str:
        """Generate narrative text for SBIR proposal"""
        tech_names = [t["technology"] for t in technologies]

        narrative = f"""Economic Impact Analysis

Our precision agriculture investment portfolio includes {len(technologies)} integrated technologies
({', '.join(tech_names)}) deployed across {acres:,.0f} acres of row crop production.

Total capital investment: ${investment:,.0f}
Annual economic benefit: ${annual_benefit:,.0f}
Payback period: {f'{payback:.1f} years' if payback else 'N/A'}
Annual benefit per acre: ${annual_benefit/acres:.2f}/acre

These benefits derive from:
- Reduced input overlap and waste through precision application
- Optimized seeding rates and nutrient placement
- Improved yield through zone-based management
- Labor efficiency gains from automation

The documented ROI demonstrates the commercial viability of precision agriculture
technology adoption by small-to-medium scale operations, validating the market
opportunity for AgTools decision support software."""

        return narrative

    def generate_economic_impact_report(
        self,
        farm_name: str,
        technologies: List[str],
        acres: float,
        years_of_data: int = 3
    ) -> Dict[str, Any]:
        """Generate comprehensive economic impact report for grant applications"""
        portfolio = self.calculate_portfolio_roi(technologies, acres, years=5)

        return {
            "report_type": "Economic Impact Analysis",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,

            "executive_summary": {
                "total_investment": portfolio["portfolio_summary"]["total_investment"],
                "annual_roi": f"{portfolio['portfolio_summary']['portfolio_roi_percent']}%",
                "payback_period": portfolio["portfolio_summary"]["portfolio_payback_years"],
                "annual_benefit": portfolio["portfolio_summary"]["total_annual_benefit"],
                "benefit_per_acre": portfolio["per_acre_metrics"]["annual_benefit_per_acre"]
            },

            "technology_stack": portfolio["technologies"],

            "financial_projections": portfolio["multi_year_projection"],

            "methodology": {
                "benefit_sources": [
                    "Input cost reduction from overlap elimination",
                    "Yield improvement from optimized placement",
                    "Labor efficiency from automation",
                    "Decision support from data integration"
                ],
                "assumptions": [
                    "Corn price: $5.00/bu, Soybean: $12.00/bu",
                    "Base yields: Corn 180 bu/ac, Soybean 50 bu/ac",
                    "Labor value: $25/hour",
                    "Analysis period: 5 years"
                ],
                "data_sources": [
                    "On-farm yield monitor data",
                    "As-applied maps from JD Operations Center",
                    "Financial records and input invoices",
                    "Industry benchmark studies (Purdue, USDA-ERS)"
                ]
            },

            "sbir_narrative": portfolio["sbir_narrative"],

            "supporting_metrics": {
                "acres_under_precision_management": acres,
                "years_of_operational_data": years_of_data,
                "data_integration_platform": "John Deere Operations Center",
                "technologies_integrated": len(technologies)
            }
        }

    # -------------------------------------------------------------------------
    # DATA QUALITY/COMPLETENESS TRACKER
    # -------------------------------------------------------------------------

    def get_data_categories(self) -> List[Dict[str, Any]]:
        """Get list of data categories for tracking"""
        return [
            {
                "id": cat.value,
                "name": cat.value.replace("_", " ").title(),
                "description": self._get_category_description(cat)
            }
            for cat in DataCategory
        ]

    def _get_category_description(self, category: DataCategory) -> str:
        """Get description for data category"""
        descriptions = {
            DataCategory.FIELD_BOUNDARIES: "GPS boundaries for all fields with acreage",
            DataCategory.SOIL_TESTS: "Grid or zone soil sampling results",
            DataCategory.YIELD_DATA: "Harvest yield monitor data by field",
            DataCategory.PLANTING_RECORDS: "Planting dates, varieties, populations, seed lots",
            DataCategory.APPLICATION_RECORDS: "Fertilizer and pesticide applications with rates",
            DataCategory.HARVEST_RECORDS: "Harvest dates, moisture, storage locations",
            DataCategory.WEATHER_DATA: "Local weather observations or station data",
            DataCategory.FINANCIAL_RECORDS: "Input costs, revenue, profit/loss by field",
            DataCategory.EQUIPMENT_RECORDS: "Machine hours, maintenance, fuel usage",
            DataCategory.IMAGERY: "Aerial/satellite imagery, drone flights, NDVI",
            DataCategory.SCOUTING_RECORDS: "Pest/disease observations, stand counts",
            DataCategory.SUSTAINABILITY_METRICS: "Carbon footprint, practice documentation",
        }
        return descriptions.get(category, "")

    def record_data_availability(
        self,
        category: str,
        years_available: List[int],
        completeness_pct: float,
        format: str,
        last_updated: date,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Record data availability for a category"""
        try:
            cat_enum = DataCategory(category)
        except ValueError:
            return {"error": f"Unknown category: {category}"}

        record = DataRecord(
            category=cat_enum,
            years_available=years_available,
            completeness_pct=min(100, max(0, completeness_pct)),
            format=format,
            last_updated=last_updated,
            notes=notes
        )

        self.data_records[category] = record

        return {
            "category": category,
            "category_name": category.replace("_", " ").title(),
            "years_available": years_available,
            "completeness_pct": completeness_pct,
            "format": format,
            "last_updated": last_updated.isoformat(),
            "message": f"Recorded {category.replace('_', ' ')} data availability"
        }

    def assess_data_completeness(
        self,
        grant_program: str = "USDA_SBIR"
    ) -> Dict[str, Any]:
        """Assess data completeness for a specific grant program"""
        if grant_program not in GRANT_DATA_REQUIREMENTS:
            return {"error": f"Unknown grant program: {grant_program}"}

        requirements = GRANT_DATA_REQUIREMENTS[grant_program]
        current_year = datetime.now(timezone.utc).year

        # Check required data
        required_status = []
        required_score = 0
        for cat in requirements["required"]:
            cat_key = cat.value
            if cat_key in self.data_records:
                record = self.data_records[cat_key]
                years_count = len([y for y in record.years_available if y >= current_year - requirements["min_years"]])
                meets_years = years_count >= requirements["min_years"]
                status = "complete" if record.completeness_pct >= 80 and meets_years else "partial"
                required_status.append({
                    "category": cat_key,
                    "name": cat_key.replace("_", " ").title(),
                    "status": status,
                    "completeness": record.completeness_pct,
                    "years": record.years_available,
                    "format": record.format
                })
                required_score += record.completeness_pct if meets_years else record.completeness_pct * 0.5
            else:
                required_status.append({
                    "category": cat_key,
                    "name": cat_key.replace("_", " ").title(),
                    "status": "missing",
                    "completeness": 0,
                    "years": [],
                    "format": None
                })

        # Check recommended data
        recommended_status = []
        recommended_score = 0
        for cat in requirements["recommended"]:
            cat_key = cat.value
            if cat_key in self.data_records:
                record = self.data_records[cat_key]
                recommended_status.append({
                    "category": cat_key,
                    "name": cat_key.replace("_", " ").title(),
                    "status": "available",
                    "completeness": record.completeness_pct
                })
                recommended_score += record.completeness_pct
            else:
                recommended_status.append({
                    "category": cat_key,
                    "name": cat_key.replace("_", " ").title(),
                    "status": "missing",
                    "completeness": 0
                })

        # Calculate scores
        max_required = len(requirements["required"]) * 100
        max_recommended = len(requirements["recommended"]) * 100

        required_pct = (required_score / max_required * 100) if max_required > 0 else 0
        recommended_pct = (recommended_score / max_recommended * 100) if max_recommended > 0 else 0

        # Overall score (weighted: required 70%, recommended 30%)
        overall_score = (required_pct * 0.7) + (recommended_pct * 0.3)

        # Letter grade
        if overall_score >= 90:
            grade = "A"
            readiness = "Excellent - Ready to apply"
        elif overall_score >= 80:
            grade = "B"
            readiness = "Good - Minor gaps to address"
        elif overall_score >= 70:
            grade = "C"
            readiness = "Fair - Some data collection needed"
        elif overall_score >= 60:
            grade = "D"
            readiness = "Needs work - Significant gaps"
        else:
            grade = "F"
            readiness = "Not ready - Major data gaps"

        # Generate action items
        action_items = []
        for item in required_status:
            if item["status"] == "missing":
                action_items.append(f"CRITICAL: Collect {item['name']} data")
            elif item["status"] == "partial":
                action_items.append(f"IMPORTANT: Complete {item['name']} data ({item['completeness']:.0f}% complete)")

        for item in recommended_status:
            if item["status"] == "missing":
                action_items.append(f"RECOMMENDED: Add {item['name']} data")

        return {
            "grant_program": grant_program,
            "program_description": requirements["description"],
            "min_years_required": requirements["min_years"],

            "required_data": {
                "items": required_status,
                "score": round(required_pct, 1),
                "complete_count": sum(1 for s in required_status if s["status"] == "complete"),
                "total_count": len(required_status)
            },

            "recommended_data": {
                "items": recommended_status,
                "score": round(recommended_pct, 1),
                "available_count": sum(1 for s in recommended_status if s["status"] == "available"),
                "total_count": len(recommended_status)
            },

            "overall_assessment": {
                "score": round(overall_score, 1),
                "grade": grade,
                "readiness": readiness
            },

            "action_items": action_items[:10],  # Top 10 priorities

            "data_collection_priority": [
                item["category"] for item in required_status if item["status"] == "missing"
            ]
        }

    def generate_data_quality_report(
        self,
        farm_name: str,
        target_grants: List[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        if target_grants is None:
            target_grants = ["USDA_SBIR", "SARE", "CIG", "EQIP"]

        assessments = []
        for grant in target_grants:
            assessment = self.assess_data_completeness(grant)
            if "error" not in assessment:
                assessments.append(assessment)

        # Summary across all grants
        if assessments:
            avg_score = statistics.mean([a["overall_assessment"]["score"] for a in assessments])
            best_fit = max(assessments, key=lambda x: x["overall_assessment"]["score"])
        else:
            avg_score = 0
            best_fit = None

        # Aggregate action items
        all_actions = []
        for a in assessments:
            all_actions.extend(a.get("action_items", []))

        # Deduplicate and prioritize
        unique_actions = list(dict.fromkeys(all_actions))

        return {
            "report_type": "Data Quality Assessment",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,

            "summary": {
                "data_categories_tracked": len(self.data_records),
                "average_readiness_score": round(avg_score, 1),
                "best_fit_program": best_fit["grant_program"] if best_fit else None,
                "best_fit_score": best_fit["overall_assessment"]["score"] if best_fit else 0
            },

            "by_grant_program": [
                {
                    "program": a["grant_program"],
                    "score": a["overall_assessment"]["score"],
                    "grade": a["overall_assessment"]["grade"],
                    "readiness": a["overall_assessment"]["readiness"]
                }
                for a in assessments
            ],

            "data_inventory": [
                {
                    "category": cat,
                    "name": cat.replace("_", " ").title(),
                    "completeness": record.completeness_pct,
                    "years": record.years_available,
                    "format": record.format,
                    "last_updated": record.last_updated.isoformat()
                }
                for cat, record in self.data_records.items()
            ],

            "priority_actions": unique_actions[:10],

            "recommendations": self._generate_data_recommendations(assessments)
        }

    def _generate_data_recommendations(self, assessments: List[Dict]) -> List[str]:
        """Generate recommendations based on assessments"""
        recommendations = []

        # Check for common gaps
        missing_categories = set()
        for a in assessments:
            for item in a["required_data"]["items"]:
                if item["status"] == "missing":
                    missing_categories.add(item["category"])

        if "yield_data" in missing_categories:
            recommendations.append("Set up yield monitor calibration and data export from JD Operations Center")
        if "soil_tests" in missing_categories:
            recommendations.append("Schedule grid soil sampling - consider 2.5-acre grids for VRT")
        if "sustainability_metrics" in missing_categories:
            recommendations.append("Use AgTools sustainability dashboard to track inputs and carbon footprint")
        if "financial_records" in missing_categories:
            recommendations.append("Export expense data from accounting system or set up AgTools expense tracking")

        if not recommendations:
            recommendations.append("Data collection is strong - focus on maintaining records and filling any partial gaps")

        return recommendations

    # -------------------------------------------------------------------------
    # PARTNERSHIP OPPORTUNITY FINDER
    # -------------------------------------------------------------------------

    def get_research_areas(self) -> List[Dict[str, str]]:
        """Get list of research areas"""
        return [
            {"id": area.value, "name": area.value.replace("_", " ").title()}
            for area in ResearchArea
        ]

    def get_partner_types(self) -> List[Dict[str, str]]:
        """Get list of partner types"""
        return [
            {"id": ptype.value, "name": ptype.value.replace("_", " ").title()}
            for ptype in PartnerType
        ]

    def find_partnership_opportunities(
        self,
        farm_capabilities: List[str],
        target_grants: List[str] = None,
        preferred_partner_types: List[str] = None,
        state: str = "LA"
    ) -> Dict[str, Any]:
        """Find matching research partnership opportunities"""

        # Convert capabilities to research areas
        capability_areas = []
        for cap in farm_capabilities:
            try:
                capability_areas.append(ResearchArea(cap))
            except ValueError:
                pass  # Skip invalid areas

        if target_grants is None:
            target_grants = ["SARE", "CIG", "USDA_SBIR"]

        matches = []
        for partner in RESEARCH_PARTNERS:
            # Calculate match score
            score = 0

            # Research area overlap (max 50 points)
            partner_areas = partner["research_areas"]
            overlap = len(set(capability_areas) & set(partner_areas))
            area_score = min(50, overlap * 15)
            score += area_score

            # Grant program alignment (max 30 points)
            grant_overlap = len(set(target_grants) & set(partner["grant_programs"]))
            grant_score = min(30, grant_overlap * 10)
            score += grant_score

            # Location bonus (max 20 points)
            if state.upper() in partner.get("location", "").upper():
                score += 20
            elif "national" in partner.get("location", "").lower():
                score += 10

            # Partner type preference
            if preferred_partner_types:
                if partner["type"].value in preferred_partner_types:
                    score += 10

            if score >= 20:  # Minimum threshold
                matches.append({
                    "partner_name": partner["name"],
                    "partner_type": partner["type"].value,
                    "location": partner["location"],
                    "match_score": min(100, score),
                    "research_areas": [a.value for a in partner["research_areas"]],
                    "matching_areas": [a.value for a in set(capability_areas) & set(partner["research_areas"])],
                    "grant_programs": partner["grant_programs"],
                    "matching_grants": list(set(target_grants) & set(partner["grant_programs"])),
                    "contact": partner["contact"],
                    "website": partner["website"],
                    "requirements": partner["requirements"],
                    "notes": partner.get("notes", "")
                })

        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return {
            "search_criteria": {
                "capabilities": farm_capabilities,
                "target_grants": target_grants,
                "preferred_partners": preferred_partner_types,
                "state": state
            },
            "matches_found": len(matches),
            "top_matches": matches[:10],
            "all_matches": matches,
            "next_steps": [
                "Review top matches and identify 2-3 potential partners",
                "Visit partner websites to understand current research priorities",
                "Reach out to contacts to discuss collaboration opportunities",
                "Prepare farm capability summary and data availability overview"
            ]
        }

    def get_partner_details(self, partner_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific partner"""
        for partner in RESEARCH_PARTNERS:
            if partner["name"].lower() == partner_name.lower():
                return {
                    "name": partner["name"],
                    "type": partner["type"].value,
                    "location": partner["location"],
                    "research_areas": [a.value for a in partner["research_areas"]],
                    "contact": partner["contact"],
                    "website": partner["website"],
                    "grant_programs": partner["grant_programs"],
                    "requirements": partner["requirements"],
                    "notes": partner.get("notes", ""),
                    "collaboration_tips": self._get_collaboration_tips(partner["type"])
                }
        return None

    def _get_collaboration_tips(self, partner_type: PartnerType) -> List[str]:
        """Get tips for collaborating with different partner types"""
        tips = {
            PartnerType.UNIVERSITY: [
                "Reach out to department heads or research station directors",
                "Offer field trial space and data sharing",
                "Be prepared for multi-year commitments",
                "Ask about graduate student involvement opportunities"
            ],
            PartnerType.EXTENSION: [
                "Contact your parish extension agent first",
                "Offer to host field days or demonstration plots",
                "Provide real-world case study data",
                "Participate in extension education events"
            ],
            PartnerType.FEDERAL_AGENCY: [
                "Identify specific research programs that align",
                "Be prepared for formal data sharing agreements",
                "Highlight unique aspects of your operation",
                "Consider CRADA (Cooperative R&D Agreement) opportunities"
            ],
            PartnerType.NONPROFIT: [
                "Align your practices with their mission",
                "Participate in industry initiatives and metrics programs",
                "Share success stories for their communications",
                "Attend their events and workshops"
            ],
            PartnerType.INDUSTRY: [
                "Look for pilot program opportunities",
                "Provide feedback on products and services",
                "Participate in beta testing programs",
                "Connect through dealer relationships"
            ],
            PartnerType.COOPERATIVE: [
                "Engage through membership channels",
                "Participate in grower committees",
                "Contribute to checkoff-funded research",
                "Provide testimonials and case studies"
            ],
        }
        return tips.get(partner_type, [])

    def generate_partnership_report(
        self,
        farm_name: str,
        farm_capabilities: List[str],
        target_grants: List[str],
        state: str = "LA"
    ) -> Dict[str, Any]:
        """Generate comprehensive partnership opportunity report"""
        opportunities = self.find_partnership_opportunities(
            farm_capabilities=farm_capabilities,
            target_grants=target_grants,
            state=state
        )

        # Categorize by partner type
        by_type = {}
        for match in opportunities["all_matches"]:
            ptype = match["partner_type"]
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append(match)

        # Categorize by grant program
        by_grant = {}
        for match in opportunities["all_matches"]:
            for grant in match["matching_grants"]:
                if grant not in by_grant:
                    by_grant[grant] = []
                by_grant[grant].append(match["partner_name"])

        return {
            "report_type": "Partnership Opportunity Analysis",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,

            "summary": {
                "total_opportunities": len(opportunities["all_matches"]),
                "top_match": opportunities["top_matches"][0]["partner_name"] if opportunities["top_matches"] else None,
                "top_match_score": opportunities["top_matches"][0]["match_score"] if opportunities["top_matches"] else 0
            },

            "capabilities_analyzed": farm_capabilities,
            "target_grants": target_grants,

            "top_opportunities": [
                {
                    "partner": m["partner_name"],
                    "type": m["partner_type"],
                    "score": m["match_score"],
                    "website": m["website"],
                    "why_good_fit": m["matching_areas"]
                }
                for m in opportunities["top_matches"][:5]
            ],

            "by_partner_type": {
                ptype: [m["partner_name"] for m in matches]
                for ptype, matches in by_type.items()
            },

            "by_grant_program": by_grant,

            "outreach_plan": {
                "immediate": [
                    f"Contact {opportunities['top_matches'][0]['partner_name']}" if opportunities["top_matches"] else "Identify potential partners",
                    "Prepare farm capability overview document",
                    "Gather 3-year data summary"
                ],
                "short_term": [
                    "Schedule introductory meetings with top 3 matches",
                    "Attend extension field days in your area",
                    "Join relevant commodity organization research committees"
                ],
                "ongoing": [
                    "Maintain relationships with research contacts",
                    "Share relevant data and observations",
                    "Participate in industry events and conferences"
                ]
            },

            "all_opportunities": opportunities["all_matches"]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_grant_enhancement_service: Optional[GrantEnhancementService] = None


def get_grant_enhancement_service() -> GrantEnhancementService:
    """Get or create the grant enhancement service singleton"""
    global _grant_enhancement_service
    if _grant_enhancement_service is None:
        _grant_enhancement_service = GrantEnhancementService()
    return _grant_enhancement_service
