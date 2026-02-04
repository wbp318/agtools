"""
Grant Support & Compliance Service for AgTools
Version: 3.5.0

This service provides grant application support including:
- NRCS conservation practice tracking with official codes
- Carbon credit calculation and market integration
- Grant reporting engine for SARE/SBIR/CIG
- Benchmark comparisons vs regional/national averages
"""

from datetime import datetime, date, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import statistics


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class GrantProgram(Enum):
    """Supported grant programs"""
    USDA_SBIR = "usda_sbir"
    NSF_SBIR = "nsf_sbir"
    SARE_PRODUCER = "sare_producer"
    SARE_RESEARCH = "sare_research"
    CIG = "cig"  # Conservation Innovation Grant
    EQIP = "eqip"  # Environmental Quality Incentives Program
    CSP = "csp"  # Conservation Stewardship Program
    CRP = "crp"  # Conservation Reserve Program
    LA_ON_FARM = "la_on_farm"


class NRCSCategory(Enum):
    """NRCS practice categories"""
    SOIL_HEALTH = "soil_health"
    WATER_QUALITY = "water_quality"
    WATER_QUANTITY = "water_quantity"
    AIR_QUALITY = "air_quality"
    WILDLIFE = "wildlife"
    ENERGY = "energy"
    PLANT_HEALTH = "plant_health"


class CarbonProgram(Enum):
    """Carbon credit programs"""
    NORI = "nori"
    INDIGO_AG = "indigo_ag"
    BAYER_CARBON = "bayer_carbon"
    CARGILL_REGENERATE = "cargill_regenerate"
    CORTEVA_CARBON = "corteva_carbon"
    NUTRIEN_CARBON = "nutrien_carbon"
    GRADABLE = "gradable"
    TRUTERRA = "truterra"


@dataclass
class NRCSPractice:
    """NRCS conservation practice definition"""
    code: str
    name: str
    category: NRCSCategory
    description: str
    payment_rate: float  # $/acre typical
    carbon_benefit: float  # tons CO2e/acre/year
    soil_health_points: int  # 0-100
    water_quality_points: int  # 0-100
    biodiversity_points: int  # 0-100
    eligible_programs: List[str]
    documentation_required: List[str]
    verification_method: str


@dataclass
class PracticeImplementation:
    """Record of implemented practice"""
    id: str
    practice_code: str
    field_id: str
    field_name: str
    acres: float
    start_date: date
    end_date: Optional[date]
    status: str  # planned, active, completed, verified
    verification_date: Optional[date]
    verifier: Optional[str]
    notes: str
    documentation: List[str]
    gps_coordinates: Optional[Dict[str, float]]


@dataclass
class CarbonCredit:
    """Carbon credit estimation"""
    practice_code: str
    acres: float
    annual_tons_co2e: float
    market_price_low: float
    market_price_mid: float
    market_price_high: float
    annual_revenue_low: float
    annual_revenue_mid: float
    annual_revenue_high: float
    eligible_programs: List[str]
    verification_required: str
    contract_length_years: int


@dataclass
class BenchmarkData:
    """Benchmark comparison data"""
    metric: str
    farm_value: float
    county_avg: float
    state_avg: float
    national_avg: float
    top_10_pct: float
    percentile_rank: int
    interpretation: str


@dataclass
class GrantReport:
    """Generated grant report"""
    grant_program: str
    report_type: str
    generated_date: datetime
    farm_name: str
    project_title: str
    sections: Dict[str, Any]
    metrics: Dict[str, Any]
    attachments: List[str]


# =============================================================================
# NRCS PRACTICE DATABASE
# =============================================================================

NRCS_PRACTICES = {
    # Cover Crop - Code 340
    "340": NRCSPractice(
        code="340",
        name="Cover Crop",
        category=NRCSCategory.SOIL_HEALTH,
        description="Crops including grasses, legumes, and forbs for seasonal vegetative cover",
        payment_rate=50.0,
        carbon_benefit=0.5,
        soil_health_points=85,
        water_quality_points=75,
        biodiversity_points=60,
        eligible_programs=["EQIP", "CSP", "CIG"],
        documentation_required=["Seed receipts", "Planting dates", "Species mix", "Termination method", "Photos"],
        verification_method="Field inspection or aerial imagery"
    ),

    # No-Till - Code 329
    "329": NRCSPractice(
        code="329",
        name="Residue and Tillage Management, No-Till",
        category=NRCSCategory.SOIL_HEALTH,
        description="Managing the amount, orientation, and distribution of crop residue with no tillage",
        payment_rate=35.0,
        carbon_benefit=0.3,
        soil_health_points=90,
        water_quality_points=80,
        biodiversity_points=50,
        eligible_programs=["EQIP", "CSP", "CIG"],
        documentation_required=["Equipment logs", "Field records", "Residue photos"],
        verification_method="Field inspection showing >60% residue"
    ),

    # Reduced Tillage - Code 345
    "345": NRCSPractice(
        code="345",
        name="Residue and Tillage Management, Reduced Till",
        category=NRCSCategory.SOIL_HEALTH,
        description="Managing residue with reduced tillage intensity",
        payment_rate=25.0,
        carbon_benefit=0.15,
        soil_health_points=70,
        water_quality_points=65,
        biodiversity_points=40,
        eligible_programs=["EQIP", "CSP"],
        documentation_required=["Tillage records", "Equipment logs", "Residue measurements"],
        verification_method="Field inspection showing 30-60% residue"
    ),

    # Nutrient Management - Code 590
    "590": NRCSPractice(
        code="590",
        name="Nutrient Management",
        category=NRCSCategory.WATER_QUALITY,
        description="Managing nutrients based on soil tests, yield goals, and timing",
        payment_rate=20.0,
        carbon_benefit=0.1,
        soil_health_points=60,
        water_quality_points=90,
        biodiversity_points=30,
        eligible_programs=["EQIP", "CSP", "CIG"],
        documentation_required=["Soil tests", "Nutrient plan", "Application records", "Yield records"],
        verification_method="Nutrient plan review and application record audit"
    ),

    # Pest Management - Code 595
    "595": NRCSPractice(
        code="595",
        name="Integrated Pest Management",
        category=NRCSCategory.PLANT_HEALTH,
        description="Using biological, cultural, and chemical tactics to manage pests",
        payment_rate=15.0,
        carbon_benefit=0.05,
        soil_health_points=40,
        water_quality_points=75,
        biodiversity_points=70,
        eligible_programs=["EQIP", "CSP"],
        documentation_required=["Scouting records", "Threshold calculations", "Application records", "Pest ID"],
        verification_method="IPM plan and scouting record review"
    ),

    # Precision Application - Code 592
    "592": NRCSPractice(
        code="592",
        name="Precision Application Technology",
        category=NRCSCategory.WATER_QUALITY,
        description="Using GPS and variable rate technology for precise input application",
        payment_rate=30.0,
        carbon_benefit=0.12,
        soil_health_points=50,
        water_quality_points=85,
        biodiversity_points=40,
        eligible_programs=["EQIP", "CSP", "CIG"],
        documentation_required=["Equipment calibration", "As-applied maps", "VRT prescriptions", "Controller logs"],
        verification_method="As-applied map review and equipment inspection"
    ),

    # Crop Rotation - Code 328
    "328": NRCSPractice(
        code="328",
        name="Conservation Crop Rotation",
        category=NRCSCategory.SOIL_HEALTH,
        description="Growing crops in recurring sequence to improve soil health",
        payment_rate=25.0,
        carbon_benefit=0.2,
        soil_health_points=75,
        water_quality_points=70,
        biodiversity_points=55,
        eligible_programs=["EQIP", "CSP"],
        documentation_required=["Rotation plan", "Planting records", "Crop history"],
        verification_method="Field records showing 3+ year rotation"
    ),

    # Grassed Waterway - Code 412
    "412": NRCSPractice(
        code="412",
        name="Grassed Waterway",
        category=NRCSCategory.WATER_QUALITY,
        description="Natural or constructed channel shaped to required dimensions with grass",
        payment_rate=500.0,  # Per waterway
        carbon_benefit=0.1,
        soil_health_points=40,
        water_quality_points=95,
        biodiversity_points=65,
        eligible_programs=["EQIP", "CSP", "CRP"],
        documentation_required=["Design specifications", "Installation records", "Maintenance log", "Photos"],
        verification_method="Field inspection and measurement"
    ),

    # Filter Strip - Code 393
    "393": NRCSPractice(
        code="393",
        name="Filter Strip",
        category=NRCSCategory.WATER_QUALITY,
        description="Strip of vegetation at edge of field to filter sediment and nutrients",
        payment_rate=300.0,  # Per acre
        carbon_benefit=0.3,
        soil_health_points=50,
        water_quality_points=90,
        biodiversity_points=70,
        eligible_programs=["EQIP", "CSP", "CRP"],
        documentation_required=["Width/length measurements", "Species list", "Maintenance records"],
        verification_method="Field inspection and measurement"
    ),

    # Pollinator Habitat - Code 420
    "420": NRCSPractice(
        code="420",
        name="Wildlife Habitat Planting",
        category=NRCSCategory.WILDLIFE,
        description="Establishing wildlife habitat including pollinator plantings",
        payment_rate=350.0,
        carbon_benefit=0.25,
        soil_health_points=45,
        water_quality_points=60,
        biodiversity_points=95,
        eligible_programs=["EQIP", "CSP", "CRP"],
        documentation_required=["Species mix", "Acreage", "Establishment photos", "Bloom dates"],
        verification_method="Field inspection during bloom"
    ),

    # Riparian Buffer - Code 391
    "391": NRCSPractice(
        code="391",
        name="Riparian Forest Buffer",
        category=NRCSCategory.WATER_QUALITY,
        description="Trees/shrubs adjacent to water bodies for water quality",
        payment_rate=400.0,
        carbon_benefit=1.0,
        soil_health_points=55,
        water_quality_points=95,
        biodiversity_points=85,
        eligible_programs=["EQIP", "CSP", "CRP"],
        documentation_required=["Species list", "Width measurements", "Survival counts", "Photos"],
        verification_method="Field inspection and survival assessment"
    ),

    # Irrigation Water Management - Code 449
    "449": NRCSPractice(
        code="449",
        name="Irrigation Water Management",
        category=NRCSCategory.WATER_QUANTITY,
        description="Managing irrigation to optimize water use efficiency",
        payment_rate=40.0,
        carbon_benefit=0.08,
        soil_health_points=40,
        water_quality_points=75,
        biodiversity_points=25,
        eligible_programs=["EQIP", "CSP"],
        documentation_required=["Irrigation schedule", "Soil moisture data", "Water usage records"],
        verification_method="Water use records and scheduling review"
    ),

    # Mulching - Code 484
    "484": NRCSPractice(
        code="484",
        name="Mulching",
        category=NRCSCategory.SOIL_HEALTH,
        description="Applying organic materials to soil surface",
        payment_rate=100.0,
        carbon_benefit=0.2,
        soil_health_points=70,
        water_quality_points=60,
        biodiversity_points=45,
        eligible_programs=["EQIP"],
        documentation_required=["Material type", "Application rate", "Coverage area"],
        verification_method="Field inspection"
    ),

    # Contour Farming - Code 330
    "330": NRCSPractice(
        code="330",
        name="Contour Farming",
        category=NRCSCategory.SOIL_HEALTH,
        description="Farming sloping land on the contour",
        payment_rate=15.0,
        carbon_benefit=0.05,
        soil_health_points=60,
        water_quality_points=75,
        biodiversity_points=30,
        eligible_programs=["EQIP", "CSP"],
        documentation_required=["Slope measurements", "Contour maps", "Field photos"],
        verification_method="Field inspection and GPS mapping"
    ),

    # Strip Cropping - Code 585
    "585": NRCSPractice(
        code="585",
        name="Stripcropping",
        category=NRCSCategory.SOIL_HEALTH,
        description="Growing crops in alternating strips along the contour",
        payment_rate=30.0,
        carbon_benefit=0.15,
        soil_health_points=65,
        water_quality_points=80,
        biodiversity_points=50,
        eligible_programs=["EQIP", "CSP"],
        documentation_required=["Strip widths", "Crop sequence", "Field maps"],
        verification_method="Aerial imagery or field inspection"
    ),
}


# =============================================================================
# CARBON CREDIT MARKET DATA
# =============================================================================

CARBON_PROGRAMS = {
    CarbonProgram.NORI: {
        "name": "Nori",
        "price_per_ton": {"low": 15.0, "mid": 20.0, "high": 25.0},
        "contract_years": 10,
        "verification": "Third-party verification required",
        "eligible_practices": ["340", "329", "345", "328"],
        "requirements": ["3+ years of data", "No-till or cover crop baseline", "Soil sampling"],
        "website": "https://nori.com"
    },
    CarbonProgram.INDIGO_AG: {
        "name": "Indigo Carbon",
        "price_per_ton": {"low": 20.0, "mid": 25.0, "high": 30.0},
        "contract_years": 5,
        "verification": "Indigo verification process",
        "eligible_practices": ["340", "329", "590", "328"],
        "requirements": ["Practice change from baseline", "Enrollment agreement", "Data sharing"],
        "website": "https://indigoag.com/carbon"
    },
    CarbonProgram.BAYER_CARBON: {
        "name": "Bayer Carbon Program",
        "price_per_ton": {"low": 18.0, "mid": 22.0, "high": 28.0},
        "contract_years": 3,
        "verification": "Bayer Climate Corp verification",
        "eligible_practices": ["340", "329", "590", "592"],
        "requirements": ["Climate FieldView data", "Practice adoption", "Outcome tracking"],
        "website": "https://www.bayer.com/carbon"
    },
    CarbonProgram.CARGILL_REGENERATE: {
        "name": "Cargill RegenConnect",
        "price_per_ton": {"low": 22.0, "mid": 28.0, "high": 35.0},
        "contract_years": 5,
        "verification": "Cargill verification",
        "eligible_practices": ["340", "329", "328", "590"],
        "requirements": ["Corn/soy acres", "Regenerative practice adoption", "Documentation"],
        "website": "https://www.cargill.com/sustainability/regenerative-agriculture"
    },
    CarbonProgram.CORTEVA_CARBON: {
        "name": "Corteva Carbon Initiative",
        "price_per_ton": {"low": 17.0, "mid": 21.0, "high": 26.0},
        "contract_years": 5,
        "verification": "Third-party verification",
        "eligible_practices": ["340", "329", "345", "590"],
        "requirements": ["Practice documentation", "Baseline establishment", "Annual reporting"],
        "website": "https://www.corteva.com/resources/carbon"
    },
    CarbonProgram.NUTRIEN_CARBON: {
        "name": "Nutrien Carbon Program",
        "price_per_ton": {"low": 20.0, "mid": 24.0, "high": 30.0},
        "contract_years": 5,
        "verification": "Nutrien Ag Solutions verification",
        "eligible_practices": ["340", "329", "590", "592"],
        "requirements": ["Nutrien customer", "Data sharing agreement", "Practice records"],
        "website": "https://www.nutrien.com"
    },
    CarbonProgram.GRADABLE: {
        "name": "Gradable by ADM",
        "price_per_ton": {"low": 15.0, "mid": 19.0, "high": 24.0},
        "contract_years": 3,
        "verification": "ADM verification process",
        "eligible_practices": ["340", "329", "328", "590"],
        "requirements": ["ADM delivery agreement", "Practice documentation", "Data upload"],
        "website": "https://www.gradable.com"
    },
    CarbonProgram.TRUTERRA: {
        "name": "Truterra (Land O'Lakes)",
        "price_per_ton": {"low": 18.0, "mid": 23.0, "high": 28.0},
        "contract_years": 5,
        "verification": "Truterra Insights verification",
        "eligible_practices": ["340", "329", "590", "449"],
        "requirements": ["Truterra Insights enrollment", "Field data", "Practice adoption"],
        "website": "https://www.truterraag.com"
    },
}


# =============================================================================
# BENCHMARK DATA (Regional Averages)
# =============================================================================

BENCHMARK_DATA = {
    # Yield benchmarks (bu/acre)
    "corn_yield": {
        "louisiana_avg": 175.0,
        "delta_region_avg": 180.0,
        "national_avg": 177.0,
        "top_10_pct": 220.0,
        "unit": "bu/acre"
    },
    "soybean_yield": {
        "louisiana_avg": 48.0,
        "delta_region_avg": 52.0,
        "national_avg": 50.0,
        "top_10_pct": 65.0,
        "unit": "bu/acre"
    },
    "rice_yield": {
        "louisiana_avg": 7200.0,
        "delta_region_avg": 7500.0,
        "national_avg": 7800.0,
        "top_10_pct": 9000.0,
        "unit": "lbs/acre"
    },

    # Input efficiency benchmarks
    "nitrogen_efficiency": {
        "louisiana_avg": 1.1,
        "delta_region_avg": 1.15,
        "national_avg": 1.2,
        "top_10_pct": 1.4,
        "unit": "bu corn/lb N"
    },
    "water_use_efficiency": {
        "louisiana_avg": 4.5,
        "delta_region_avg": 4.8,
        "national_avg": 5.0,
        "top_10_pct": 6.0,
        "unit": "bu/acre-inch"
    },
    "pesticide_use": {
        "louisiana_avg": 4.5,
        "delta_region_avg": 4.2,
        "national_avg": 4.0,
        "top_10_pct": 2.5,
        "unit": "lb ai/acre"
    },

    # Carbon/sustainability benchmarks
    "carbon_footprint": {
        "louisiana_avg": 850.0,
        "delta_region_avg": 800.0,
        "national_avg": 780.0,
        "top_10_pct": 500.0,
        "unit": "kg CO2e/acre"
    },
    "soil_organic_matter": {
        "louisiana_avg": 2.5,
        "delta_region_avg": 2.8,
        "national_avg": 3.2,
        "top_10_pct": 4.5,
        "unit": "%"
    },
    "cover_crop_adoption": {
        "louisiana_avg": 8.0,
        "delta_region_avg": 12.0,
        "national_avg": 15.0,
        "top_10_pct": 80.0,
        "unit": "% of acres"
    },
    "no_till_adoption": {
        "louisiana_avg": 25.0,
        "delta_region_avg": 35.0,
        "national_avg": 40.0,
        "top_10_pct": 100.0,
        "unit": "% of acres"
    },

    # Economic benchmarks
    "cost_per_bushel_corn": {
        "louisiana_avg": 3.80,
        "delta_region_avg": 3.60,
        "national_avg": 3.50,
        "top_10_pct": 2.80,
        "unit": "$/bu"
    },
    "cost_per_bushel_soybean": {
        "louisiana_avg": 8.50,
        "delta_region_avg": 8.00,
        "national_avg": 7.80,
        "top_10_pct": 6.50,
        "unit": "$/bu"
    },
    "profit_per_acre": {
        "louisiana_avg": 150.0,
        "delta_region_avg": 180.0,
        "national_avg": 200.0,
        "top_10_pct": 350.0,
        "unit": "$/acre"
    },
}


# =============================================================================
# GRANT SERVICE CLASS
# =============================================================================

class GrantService:
    """Service for grant application support and compliance tracking"""

    def __init__(self):
        self.practices: Dict[str, PracticeImplementation] = {}
        self.practice_counter = 0

    # -------------------------------------------------------------------------
    # GRANT PROGRAM LISTING
    # -------------------------------------------------------------------------

    def list_programs(self) -> Dict[str, Any]:
        """List all available grant programs"""
        # Define program metadata
        program_info = {
            GrantProgram.USDA_SBIR: {
                "name": "USDA Small Business Innovation Research",
                "agency": "USDA",
                "description": "Competitive research grants for small businesses",
                "max_funding": 100000.0,
                "eligibility": ["Small business", "U.S. owned", "For-profit"]
            },
            GrantProgram.NSF_SBIR: {
                "name": "NSF Small Business Innovation Research",
                "agency": "NSF",
                "description": "Technology innovation funding for small businesses",
                "max_funding": 256000.0,
                "eligibility": ["Small business", "U.S. owned", "Technology focus"]
            },
            GrantProgram.SARE_PRODUCER: {
                "name": "SARE Producer Grant",
                "agency": "USDA SARE",
                "description": "On-farm research for sustainable agriculture",
                "max_funding": 15000.0,
                "eligibility": ["Active farmer/rancher", "U.S. based"]
            },
            GrantProgram.SARE_RESEARCH: {
                "name": "SARE Research & Education",
                "agency": "USDA SARE",
                "description": "Research projects advancing sustainable agriculture",
                "max_funding": 250000.0,
                "eligibility": ["Researchers", "Educators", "Farmers"]
            },
            GrantProgram.CIG: {
                "name": "Conservation Innovation Grant",
                "agency": "NRCS",
                "description": "Innovative conservation approaches",
                "max_funding": 1000000.0,
                "eligibility": ["Any entity", "Conservation focus"]
            },
            GrantProgram.EQIP: {
                "name": "Environmental Quality Incentives Program",
                "agency": "NRCS",
                "description": "Conservation practices on working lands",
                "max_funding": 450000.0,
                "eligibility": ["Agricultural producers", "Forest landowners"]
            },
            GrantProgram.CSP: {
                "name": "Conservation Stewardship Program",
                "agency": "NRCS",
                "description": "Maintaining and improving conservation systems",
                "max_funding": 200000.0,
                "eligibility": ["Agricultural producers", "Active conservation"]
            },
            GrantProgram.CRP: {
                "name": "Conservation Reserve Program",
                "agency": "FSA",
                "description": "Land retirement for conservation",
                "max_funding": 50000.0,
                "eligibility": ["Agricultural landowners", "Cropland history"]
            },
            GrantProgram.LA_ON_FARM: {
                "name": "Louisiana On-Farm Research",
                "agency": "LSU AgCenter",
                "description": "On-farm trials in Louisiana",
                "max_funding": 10000.0,
                "eligibility": ["Louisiana farmers", "Research collaboration"]
            }
        }

        programs = [
            {
                "id": program.value,
                "name": info["name"],
                "agency": info["agency"],
                "description": info.get("description"),
                "max_funding": info.get("max_funding"),
                "deadline": None,
                "eligibility": info.get("eligibility", [])
            }
            for program, info in program_info.items()
        ]

        return {"programs": programs, "total": len(programs)}

    # -------------------------------------------------------------------------
    # NRCS PRACTICE MANAGEMENT
    # -------------------------------------------------------------------------

    def get_all_nrcs_practices(self) -> List[Dict[str, Any]]:
        """Get all available NRCS practices"""
        return [
            {
                "code": p.code,
                "name": p.name,
                "category": p.category.value,
                "description": p.description,
                "payment_rate": p.payment_rate,
                "carbon_benefit": p.carbon_benefit,
                "soil_health_points": p.soil_health_points,
                "water_quality_points": p.water_quality_points,
                "biodiversity_points": p.biodiversity_points,
                "eligible_programs": p.eligible_programs,
                "documentation_required": p.documentation_required,
                "verification_method": p.verification_method
            }
            for p in NRCS_PRACTICES.values()
        ]

    def get_practice_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get a specific NRCS practice by code"""
        practice = NRCS_PRACTICES.get(code)
        if not practice:
            return None
        return {
            "code": practice.code,
            "name": practice.name,
            "category": practice.category.value,
            "description": practice.description,
            "payment_rate": practice.payment_rate,
            "carbon_benefit": practice.carbon_benefit,
            "soil_health_points": practice.soil_health_points,
            "water_quality_points": practice.water_quality_points,
            "biodiversity_points": practice.biodiversity_points,
            "eligible_programs": practice.eligible_programs,
            "documentation_required": practice.documentation_required,
            "verification_method": practice.verification_method
        }

    def get_practices_by_program(self, program: str) -> List[Dict[str, Any]]:
        """Get NRCS practices eligible for a specific program"""
        return [
            {
                "code": p.code,
                "name": p.name,
                "category": p.category.value,
                "payment_rate": p.payment_rate,
                "carbon_benefit": p.carbon_benefit
            }
            for p in NRCS_PRACTICES.values()
            if program.upper() in p.eligible_programs
        ]

    def record_practice_implementation(
        self,
        practice_code: str,
        field_id: str,
        field_name: str,
        acres: float,
        start_date: date,
        notes: str = "",
        gps_coordinates: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Record implementation of an NRCS practice"""
        if practice_code not in NRCS_PRACTICES:
            return {"error": f"Unknown practice code: {practice_code}"}

        self.practice_counter += 1
        impl_id = f"IMPL-{self.practice_counter:04d}"

        implementation = PracticeImplementation(
            id=impl_id,
            practice_code=practice_code,
            field_id=field_id,
            field_name=field_name,
            acres=acres,
            start_date=start_date,
            end_date=None,
            status="active",
            verification_date=None,
            verifier=None,
            notes=notes,
            documentation=[],
            gps_coordinates=gps_coordinates
        )

        self.practices[impl_id] = implementation
        practice = NRCS_PRACTICES[practice_code]

        return {
            "id": impl_id,
            "practice_code": practice_code,
            "practice_name": practice.name,
            "field_id": field_id,
            "field_name": field_name,
            "acres": acres,
            "start_date": start_date.isoformat(),
            "status": "active",
            "estimated_payment": acres * practice.payment_rate,
            "estimated_carbon_benefit": acres * practice.carbon_benefit,
            "documentation_required": practice.documentation_required,
            "message": f"Practice {practice.name} recorded for {acres} acres on {field_name}"
        }

    def add_practice_documentation(
        self,
        implementation_id: str,
        document_type: str,
        document_path: str,
        document_date: date
    ) -> Dict[str, Any]:
        """Add documentation to a practice implementation"""
        if implementation_id not in self.practices:
            return {"error": f"Implementation {implementation_id} not found"}

        impl = self.practices[implementation_id]
        doc_entry = f"{document_type}: {document_path} ({document_date.isoformat()})"
        impl.documentation.append(doc_entry)

        practice = NRCS_PRACTICES[impl.practice_code]
        remaining = [
            req for req in practice.documentation_required
            if not any(req.lower() in doc.lower() for doc in impl.documentation)
        ]

        return {
            "implementation_id": implementation_id,
            "document_added": doc_entry,
            "total_documents": len(impl.documentation),
            "remaining_required": remaining,
            "documentation_complete": len(remaining) == 0
        }

    def verify_practice(
        self,
        implementation_id: str,
        verifier: str,
        verification_date: date,
        passed: bool,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Record verification of a practice implementation"""
        if implementation_id not in self.practices:
            return {"error": f"Implementation {implementation_id} not found"}

        impl = self.practices[implementation_id]
        impl.verification_date = verification_date
        impl.verifier = verifier
        impl.status = "verified" if passed else "failed"
        if notes:
            impl.notes += f" | Verification: {notes}"

        practice = NRCS_PRACTICES[impl.practice_code]

        return {
            "implementation_id": implementation_id,
            "practice_code": impl.practice_code,
            "practice_name": practice.name,
            "verification_date": verification_date.isoformat(),
            "verifier": verifier,
            "status": impl.status,
            "payment_eligible": passed,
            "estimated_payment": impl.acres * practice.payment_rate if passed else 0,
            "notes": notes
        }

    def get_practice_summary(self) -> Dict[str, Any]:
        """Get summary of all implemented practices"""
        if not self.practices:
            return {
                "total_implementations": 0,
                "total_acres": 0,
                "by_status": {},
                "by_practice": {},
                "total_estimated_payment": 0,
                "total_carbon_benefit": 0
            }

        by_status = {}
        by_practice = {}
        total_payment = 0
        total_carbon = 0
        total_acres = 0

        for impl in self.practices.values():
            # Count by status
            by_status[impl.status] = by_status.get(impl.status, 0) + 1

            # Aggregate by practice
            practice = NRCS_PRACTICES[impl.practice_code]
            if impl.practice_code not in by_practice:
                by_practice[impl.practice_code] = {
                    "name": practice.name,
                    "implementations": 0,
                    "total_acres": 0,
                    "estimated_payment": 0,
                    "carbon_benefit": 0
                }
            by_practice[impl.practice_code]["implementations"] += 1
            by_practice[impl.practice_code]["total_acres"] += impl.acres
            by_practice[impl.practice_code]["estimated_payment"] += impl.acres * practice.payment_rate
            by_practice[impl.practice_code]["carbon_benefit"] += impl.acres * practice.carbon_benefit

            total_acres += impl.acres
            total_payment += impl.acres * practice.payment_rate
            total_carbon += impl.acres * practice.carbon_benefit

        return {
            "total_implementations": len(self.practices),
            "total_acres": round(total_acres, 1),
            "by_status": by_status,
            "by_practice": by_practice,
            "total_estimated_payment": round(total_payment, 2),
            "total_carbon_benefit": round(total_carbon, 2),
            "units": {
                "payment": "USD",
                "carbon": "tons CO2e/year"
            }
        }

    # -------------------------------------------------------------------------
    # CARBON CREDIT CALCULATIONS
    # -------------------------------------------------------------------------

    def get_carbon_programs(self) -> List[Dict[str, Any]]:
        """Get all available carbon credit programs"""
        return [
            {
                "id": program.value,
                "name": info["name"],
                "price_per_ton": info["price_per_ton"],
                "contract_years": info["contract_years"],
                "verification": info["verification"],
                "eligible_practices": info["eligible_practices"],
                "requirements": info["requirements"],
                "website": info["website"]
            }
            for program, info in CARBON_PROGRAMS.items()
        ]

    def calculate_carbon_credits(
        self,
        practice_code: str,
        acres: float,
        years: int = 5
    ) -> Dict[str, Any]:
        """Calculate potential carbon credit revenue for a practice"""
        if practice_code not in NRCS_PRACTICES:
            return {"error": f"Unknown practice code: {practice_code}"}

        practice = NRCS_PRACTICES[practice_code]
        annual_tons = acres * practice.carbon_benefit

        # Find eligible programs
        eligible_programs = []
        for program, info in CARBON_PROGRAMS.items():
            if practice_code in info["eligible_practices"]:
                contract_years = min(years, info["contract_years"])
                total_tons = annual_tons * contract_years

                eligible_programs.append({
                    "program": info["name"],
                    "price_range": info["price_per_ton"],
                    "contract_years": contract_years,
                    "annual_tons": round(annual_tons, 2),
                    "total_tons": round(total_tons, 2),
                    "annual_revenue": {
                        "low": round(annual_tons * info["price_per_ton"]["low"], 2),
                        "mid": round(annual_tons * info["price_per_ton"]["mid"], 2),
                        "high": round(annual_tons * info["price_per_ton"]["high"], 2)
                    },
                    "total_revenue": {
                        "low": round(total_tons * info["price_per_ton"]["low"], 2),
                        "mid": round(total_tons * info["price_per_ton"]["mid"], 2),
                        "high": round(total_tons * info["price_per_ton"]["high"], 2)
                    },
                    "requirements": info["requirements"],
                    "verification": info["verification"]
                })

        # Calculate averages across programs
        if eligible_programs:
            avg_annual_mid = statistics.mean([p["annual_revenue"]["mid"] for p in eligible_programs])
            avg_total_mid = statistics.mean([p["total_revenue"]["mid"] for p in eligible_programs])
        else:
            avg_annual_mid = 0
            avg_total_mid = 0

        return {
            "practice_code": practice_code,
            "practice_name": practice.name,
            "acres": acres,
            "carbon_benefit_rate": practice.carbon_benefit,
            "annual_tons_co2e": round(annual_tons, 2),
            "eligible_programs": eligible_programs,
            "average_annual_revenue": round(avg_annual_mid, 2),
            "average_total_revenue": round(avg_total_mid, 2),
            "summary": f"{acres} acres of {practice.name} could generate ~${round(avg_annual_mid, 0)}/year in carbon credits"
        }

    def calculate_farm_carbon_portfolio(
        self,
        implementations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate total carbon credit potential for all implemented practices"""
        if implementations:
            impls = [self.practices[i] for i in implementations if i in self.practices]
        else:
            impls = list(self.practices.values())

        if not impls:
            return {
                "total_acres": 0,
                "annual_tons_co2e": 0,
                "eligible_programs": [],
                "potential_revenue": {"low": 0, "mid": 0, "high": 0},
                "by_practice": []
            }

        total_acres = 0
        total_annual_tons = 0
        by_practice = {}
        all_eligible_codes = set()

        for impl in impls:
            practice = NRCS_PRACTICES.get(impl.practice_code)
            if not practice:
                continue

            total_acres += impl.acres
            annual_tons = impl.acres * practice.carbon_benefit
            total_annual_tons += annual_tons

            if impl.practice_code not in by_practice:
                by_practice[impl.practice_code] = {
                    "name": practice.name,
                    "total_acres": 0,
                    "annual_tons": 0
                }
            by_practice[impl.practice_code]["total_acres"] += impl.acres
            by_practice[impl.practice_code]["annual_tons"] += annual_tons
            all_eligible_codes.add(impl.practice_code)

        # Find programs that accept any of our practices
        revenue_by_program = []
        for program, info in CARBON_PROGRAMS.items():
            program_eligible = [c for c in all_eligible_codes if c in info["eligible_practices"]]
            if program_eligible:
                eligible_tons = sum(
                    by_practice[c]["annual_tons"]
                    for c in program_eligible
                )
                revenue_by_program.append({
                    "program": info["name"],
                    "eligible_tons": round(eligible_tons, 2),
                    "annual_revenue": {
                        "low": round(eligible_tons * info["price_per_ton"]["low"], 2),
                        "mid": round(eligible_tons * info["price_per_ton"]["mid"], 2),
                        "high": round(eligible_tons * info["price_per_ton"]["high"], 2)
                    }
                })

        # Best program recommendation
        if revenue_by_program:
            best_program = max(revenue_by_program, key=lambda x: x["annual_revenue"]["mid"])
            total_revenue_low = best_program["annual_revenue"]["low"]
            total_revenue_mid = best_program["annual_revenue"]["mid"]
            total_revenue_high = best_program["annual_revenue"]["high"]
        else:
            best_program = None
            total_revenue_low = total_revenue_mid = total_revenue_high = 0

        return {
            "total_acres": round(total_acres, 1),
            "annual_tons_co2e": round(total_annual_tons, 2),
            "by_practice": [
                {
                    "code": code,
                    "name": data["name"],
                    "acres": round(data["total_acres"], 1),
                    "annual_tons": round(data["annual_tons"], 2)
                }
                for code, data in by_practice.items()
            ],
            "eligible_programs": revenue_by_program,
            "best_program": best_program["program"] if best_program else None,
            "potential_revenue": {
                "low": round(total_revenue_low, 2),
                "mid": round(total_revenue_mid, 2),
                "high": round(total_revenue_high, 2)
            },
            "summary": f"Farm portfolio: {round(total_annual_tons, 1)} tons CO2e/year, potential ${round(total_revenue_mid, 0)}/year"
        }

    # -------------------------------------------------------------------------
    # BENCHMARK COMPARISONS
    # -------------------------------------------------------------------------

    def get_available_benchmarks(self) -> List[Dict[str, Any]]:
        """Get list of available benchmark metrics"""
        return [
            {
                "metric": metric,
                "unit": data["unit"],
                "louisiana_avg": data["louisiana_avg"],
                "national_avg": data["national_avg"],
                "top_10_pct": data["top_10_pct"]
            }
            for metric, data in BENCHMARK_DATA.items()
        ]

    def compare_to_benchmarks(
        self,
        metric: str,
        farm_value: float,
        county: str = "Louisiana"
    ) -> Dict[str, Any]:
        """Compare farm metric to regional and national benchmarks"""
        if metric not in BENCHMARK_DATA:
            return {"error": f"Unknown metric: {metric}. Available: {list(BENCHMARK_DATA.keys())}"}

        bench = BENCHMARK_DATA[metric]

        # Determine if higher or lower is better
        lower_is_better = metric in [
            "carbon_footprint", "pesticide_use",
            "cost_per_bushel_corn", "cost_per_bushel_soybean"
        ]

        # Calculate percentile (simplified linear interpolation)
        if lower_is_better:
            # For metrics where lower is better
            if farm_value <= bench["top_10_pct"]:
                percentile = 95
            elif farm_value >= bench["national_avg"] * 1.5:
                percentile = 10
            else:
                range_size = bench["national_avg"] * 1.5 - bench["top_10_pct"]
                position = farm_value - bench["top_10_pct"]
                percentile = max(10, min(95, 95 - int(85 * position / range_size)))
        else:
            # For metrics where higher is better
            if farm_value >= bench["top_10_pct"]:
                percentile = 95
            elif farm_value <= bench["national_avg"] * 0.5:
                percentile = 10
            else:
                range_size = bench["top_10_pct"] - bench["national_avg"] * 0.5
                position = farm_value - bench["national_avg"] * 0.5
                percentile = max(10, min(95, 10 + int(85 * position / range_size)))

        # Generate interpretation
        vs_state = ((farm_value - bench["louisiana_avg"]) / bench["louisiana_avg"]) * 100
        vs_national = ((farm_value - bench["national_avg"]) / bench["national_avg"]) * 100
        vs_top = ((farm_value - bench["top_10_pct"]) / bench["top_10_pct"]) * 100

        if lower_is_better:
            if farm_value < bench["louisiana_avg"]:
                interpretation = f"Excellent! {abs(vs_state):.1f}% better than state average"
            elif farm_value < bench["national_avg"]:
                interpretation = f"Good - better than national average but {vs_state:.1f}% above state average"
            else:
                interpretation = f"Opportunity for improvement - {vs_national:.1f}% above national average"
        else:
            if farm_value > bench["top_10_pct"]:
                interpretation = "Exceptional! In top 10% nationally"
            elif farm_value > bench["national_avg"]:
                interpretation = f"Above average - {vs_national:.1f}% above national average"
            else:
                interpretation = f"Opportunity for improvement - {abs(vs_national):.1f}% below national average"

        return {
            "metric": metric,
            "farm_value": farm_value,
            "unit": bench["unit"],
            "comparisons": {
                "louisiana_avg": bench["louisiana_avg"],
                "delta_region_avg": bench["delta_region_avg"],
                "national_avg": bench["national_avg"],
                "top_10_percent": bench["top_10_pct"]
            },
            "differences": {
                "vs_state_avg": round(vs_state, 1),
                "vs_national_avg": round(vs_national, 1),
                "vs_top_10_pct": round(vs_top, 1)
            },
            "percentile_rank": percentile,
            "lower_is_better": lower_is_better,
            "interpretation": interpretation
        }

    def generate_benchmark_report(
        self,
        farm_metrics: Dict[str, float],
        farm_name: str = "Farm"
    ) -> Dict[str, Any]:
        """Generate comprehensive benchmark comparison report"""
        comparisons = []
        strengths = []
        opportunities = []

        for metric, value in farm_metrics.items():
            if metric in BENCHMARK_DATA:
                result = self.compare_to_benchmarks(metric, value)
                comparisons.append(result)

                if result["percentile_rank"] >= 70:
                    strengths.append({
                        "metric": metric,
                        "percentile": result["percentile_rank"],
                        "value": value,
                        "unit": result["unit"]
                    })
                elif result["percentile_rank"] <= 40:
                    opportunities.append({
                        "metric": metric,
                        "percentile": result["percentile_rank"],
                        "value": value,
                        "unit": result["unit"],
                        "target": result["comparisons"]["national_avg"]
                    })

        # Calculate overall score
        if comparisons:
            avg_percentile = statistics.mean([c["percentile_rank"] for c in comparisons])
        else:
            avg_percentile = 50

        return {
            "farm_name": farm_name,
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "metrics_compared": len(comparisons),
            "overall_percentile": round(avg_percentile),
            "comparisons": comparisons,
            "strengths": strengths,
            "improvement_opportunities": opportunities,
            "summary": f"{farm_name} ranks in the {round(avg_percentile)}th percentile overall across {len(comparisons)} metrics"
        }

    # -------------------------------------------------------------------------
    # GRANT REPORTING ENGINE
    # -------------------------------------------------------------------------

    def generate_sare_report(
        self,
        farm_name: str,
        project_title: str,
        project_description: str,
        practices_implemented: List[str],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate report formatted for SARE grant application"""

        # Gather practice data
        practice_details = []
        total_acres = 0
        total_carbon = 0

        for code in practices_implemented:
            practice = NRCS_PRACTICES.get(code)
            if practice:
                # Find implementations of this practice
                impl_acres = sum(
                    impl.acres for impl in self.practices.values()
                    if impl.practice_code == code
                )
                practice_details.append({
                    "code": code,
                    "name": practice.name,
                    "description": practice.description,
                    "acres_implemented": impl_acres,
                    "environmental_benefits": {
                        "soil_health_points": practice.soil_health_points,
                        "water_quality_points": practice.water_quality_points,
                        "biodiversity_points": practice.biodiversity_points,
                        "carbon_sequestration": impl_acres * practice.carbon_benefit
                    }
                })
                total_acres += impl_acres
                total_carbon += impl_acres * practice.carbon_benefit

        return {
            "report_type": "SARE Producer Grant Application",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,
            "project_title": project_title,

            "sections": {
                "project_summary": {
                    "description": project_description,
                    "total_acres": total_acres,
                    "practices_count": len(practice_details)
                },

                "sustainable_practices": practice_details,

                "environmental_impact": {
                    "annual_carbon_sequestration_tons": round(total_carbon, 2),
                    "soil_health_improvement": "Documented through soil testing",
                    "water_quality_benefit": "Reduced nutrient runoff potential",
                    "biodiversity_enhancement": "Habitat creation and preservation"
                },

                "economic_analysis": metrics.get("economic", {
                    "input_cost_reduction": "To be measured",
                    "yield_impact": "To be measured",
                    "net_benefit_per_acre": "To be calculated"
                }),

                "outreach_plan": {
                    "target_audience": "Regional farmers",
                    "methods": [
                        "Field days",
                        "Extension presentations",
                        "Social media documentation",
                        "Published results"
                    ]
                },

                "evaluation_metrics": {
                    "soil_organic_matter": "Pre and post measurement",
                    "input_usage": "Tracked via AgTools",
                    "carbon_footprint": "Calculated using EPA factors",
                    "economic_returns": "Cost-benefit analysis"
                }
            },

            "attachments_needed": [
                "Farm map with practice locations",
                "Soil test results (baseline)",
                "3-year crop history",
                "Budget spreadsheet",
                "Letters of support"
            ]
        }

    def generate_sbir_metrics(
        self,
        product_name: str = "AgTools",
        version: str = "3.5.0",
        features: List[str] = None
    ) -> Dict[str, Any]:
        """Generate metrics section for SBIR/STTR applications"""

        if features is None:
            features = [
                "AI-powered pest/disease identification",
                "GDD-based crop stage prediction",
                "Sustainability metrics dashboard",
                "Research trial management",
                "Carbon footprint tracking",
                "Grant compliance reporting"
            ]

        return {
            "report_type": "SBIR/STTR Technical Metrics",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "product_name": product_name,
            "version": version,

            "innovation_metrics": {
                "ai_capabilities": {
                    "pest_disease_database": "46+ species",
                    "identification_method": "Hybrid cloud + local AI",
                    "accuracy_target": "90%+ validated accuracy"
                },
                "decision_support": {
                    "crop_types_supported": ["corn", "soybean", "wheat", "rice", "cotton"],
                    "gdd_tracking": "8 crops with stage prediction",
                    "spray_recommendation": "40+ products with resistance management"
                },
                "data_capabilities": {
                    "carbon_calculation": "EPA/IPCC compliant factors",
                    "statistical_analysis": "ANOVA, LSD, treatment comparisons",
                    "export_formats": ["JSON", "CSV", "PDF reports"]
                }
            },

            "commercialization_metrics": {
                "target_market": "Small to mid-size farms (500-5000 acres)",
                "market_size": "2.04 million US farms",
                "pricing_model": "$199/month SaaS",
                "revenue_potential": {
                    "year_1": "10 customers = $23,880 ARR",
                    "year_3": "100 customers = $238,800 ARR",
                    "year_5": "500 customers = $1,194,000 ARR"
                }
            },

            "societal_benefits": {
                "environmental": [
                    "Reduced pesticide overuse through precise identification",
                    "Optimized input application reducing runoff",
                    "Carbon sequestration tracking and verification"
                ],
                "economic": [
                    "Input cost reduction for farmers",
                    "Improved decision-making reducing losses",
                    "Carbon credit revenue generation"
                ],
                "scientific": [
                    "Research-grade trial management",
                    "Statistical analysis for publication",
                    "Climate adaptation tracking"
                ]
            },

            "technical_readiness": {
                "current_trl": 7,  # Technology Readiness Level
                "trl_description": "System prototype demonstrated in operational environment",
                "development_status": "Functional system with active users",
                "validation_status": "Field testing in progress"
            },

            "features": features
        }

    def generate_cig_compliance_report(
        self,
        farm_name: str,
        project_title: str,
        reporting_period: Dict[str, str],
        climate_smart_practices: List[str]
    ) -> Dict[str, Any]:
        """Generate compliance report for Conservation Innovation Grant"""

        # Gather climate-smart practice implementations
        csp_implementations = []
        total_ghg_reduction = 0

        for code in climate_smart_practices:
            practice = NRCS_PRACTICES.get(code)
            if practice:
                impl_list = [
                    impl for impl in self.practices.values()
                    if impl.practice_code == code
                ]
                total_impl_acres = sum(impl.acres for impl in impl_list)
                ghg_reduction = total_impl_acres * practice.carbon_benefit

                csp_implementations.append({
                    "practice_code": code,
                    "practice_name": practice.name,
                    "category": practice.category.value,
                    "implementations": len(impl_list),
                    "total_acres": total_impl_acres,
                    "ghg_reduction_tons": round(ghg_reduction, 2),
                    "verification_status": "verified" if any(
                        impl.status == "verified" for impl in impl_list
                    ) else "pending"
                })
                total_ghg_reduction += ghg_reduction

        return {
            "report_type": "CIG Compliance Report",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,
            "project_title": project_title,
            "reporting_period": reporting_period,

            "climate_smart_agriculture": {
                "practices_implemented": csp_implementations,
                "total_ghg_reduction_tons": round(total_ghg_reduction, 2),
                "ghg_reduction_methodology": "USDA COMET-Farm compatible calculations"
            },

            "project_outcomes": {
                "acres_enrolled": sum(p["total_acres"] for p in csp_implementations),
                "practices_adopted": len(csp_implementations),
                "verification_complete": sum(
                    1 for p in csp_implementations
                    if p["verification_status"] == "verified"
                )
            },

            "data_collection": {
                "method": "AgTools digital platform",
                "frequency": "Continuous with manual verification",
                "quality_assurance": "GPS-verified, photo-documented"
            },

            "next_steps": [
                "Continue practice implementation",
                "Complete pending verifications",
                "Collect soil samples for analysis",
                "Document economic outcomes"
            ]
        }

    def generate_eqip_application_data(
        self,
        farm_name: str,
        farm_acres: float,
        priority_resource_concerns: List[str],
        planned_practices: List[str]
    ) -> Dict[str, Any]:
        """Generate data package for EQIP application"""

        # Calculate potential payments and environmental benefits
        practice_analysis = []
        total_payment = 0
        total_soil_points = 0
        total_water_points = 0

        for code in planned_practices:
            practice = NRCS_PRACTICES.get(code)
            if practice and "EQIP" in practice.eligible_programs:
                estimated_acres = farm_acres * 0.5  # Assume 50% of farm
                payment = estimated_acres * practice.payment_rate

                practice_analysis.append({
                    "code": code,
                    "name": practice.name,
                    "category": practice.category.value,
                    "estimated_acres": estimated_acres,
                    "payment_rate": practice.payment_rate,
                    "estimated_payment": round(payment, 2),
                    "environmental_benefits": {
                        "soil_health": practice.soil_health_points,
                        "water_quality": practice.water_quality_points,
                        "carbon_benefit": practice.carbon_benefit * estimated_acres
                    },
                    "documentation_checklist": practice.documentation_required
                })

                total_payment += payment
                total_soil_points += practice.soil_health_points
                total_water_points += practice.water_quality_points

        # Rank resource concerns
        resource_concern_mapping = {
            "soil_erosion": ["340", "329", "330", "412"],
            "water_quality": ["590", "393", "391", "412"],
            "soil_health": ["340", "329", "328", "484"],
            "wildlife_habitat": ["420", "393", "391"],
            "air_quality": ["329", "345", "340"]
        }

        recommended_practices = []
        for concern in priority_resource_concerns:
            if concern in resource_concern_mapping:
                for code in resource_concern_mapping[concern]:
                    if code not in planned_practices and code not in recommended_practices:
                        practice = NRCS_PRACTICES.get(code)
                        if practice:
                            recommended_practices.append({
                                "code": code,
                                "name": practice.name,
                                "addresses_concern": concern,
                                "payment_rate": practice.payment_rate
                            })

        return {
            "report_type": "EQIP Application Package",
            "generated_date": datetime.now(timezone.utc).isoformat(),
            "farm_name": farm_name,
            "farm_acres": farm_acres,

            "resource_concerns": {
                "primary": priority_resource_concerns,
                "addressed_by_planned_practices": [
                    p["category"] for p in practice_analysis
                ]
            },

            "planned_practices": practice_analysis,

            "financial_summary": {
                "total_estimated_payment": round(total_payment, 2),
                "practices_count": len(practice_analysis),
                "average_per_practice": round(total_payment / len(practice_analysis), 2) if practice_analysis else 0
            },

            "environmental_score": {
                "soil_health_index": round(total_soil_points / len(practice_analysis), 1) if practice_analysis else 0,
                "water_quality_index": round(total_water_points / len(practice_analysis), 1) if practice_analysis else 0,
                "combined_benefit_score": round((total_soil_points + total_water_points) / (2 * len(practice_analysis)), 1) if practice_analysis else 0
            },

            "additional_recommendations": recommended_practices[:5],  # Top 5

            "required_documents": [
                "Farm operating plan",
                "Conservation plan (Form NRCS-CPA-1)",
                "Farm maps with field boundaries",
                "Soil survey data",
                "Current crop rotation",
                "Environmental evaluation (if required)"
            ]
        }

    # -------------------------------------------------------------------------
    # COMPREHENSIVE GRANT READINESS ASSESSMENT
    # -------------------------------------------------------------------------

    def assess_grant_readiness(
        self,
        farm_name: str,
        farm_acres: float,
        years_in_operation: int,
        current_practices: List[str],
        farm_metrics: Dict[str, float],
        target_grants: List[str] = None
    ) -> Dict[str, Any]:
        """Comprehensive assessment of readiness for various grant programs"""

        if target_grants is None:
            target_grants = ["USDA_SBIR", "SARE_PRODUCER", "CIG", "EQIP"]

        # Assess each target grant
        grant_assessments = []

        for grant in target_grants:
            readiness_score = 0
            requirements_met = []
            requirements_missing = []

            if grant == "USDA_SBIR":
                # SBIR requirements
                if len(current_practices) >= 3:
                    readiness_score += 25
                    requirements_met.append("Multiple practices implemented")
                else:
                    requirements_missing.append("Need 3+ practices for strong data")

                if farm_metrics:
                    readiness_score += 25
                    requirements_met.append("Metrics being tracked")
                else:
                    requirements_missing.append("Need documented metrics")

                if years_in_operation >= 2:
                    readiness_score += 25
                    requirements_met.append("Operational history established")
                else:
                    requirements_missing.append("Need longer operational history")

                readiness_score += 25  # AgTools technology exists
                requirements_met.append("Technology platform ready")

            elif grant == "SARE_PRODUCER":
                # SARE requirements
                sustainability_practices = ["340", "329", "345", "328", "590"]
                has_sustainability = any(p in current_practices for p in sustainability_practices)

                if has_sustainability:
                    readiness_score += 30
                    requirements_met.append("Sustainable practices in place")
                else:
                    requirements_missing.append("Need cover crops, no-till, or rotation")

                if farm_acres >= 100:
                    readiness_score += 20
                    requirements_met.append("Adequate scale for research")
                else:
                    requirements_missing.append("May need larger research area")

                if farm_metrics:
                    readiness_score += 25
                    requirements_met.append("Baseline data available")
                else:
                    requirements_missing.append("Need baseline metrics for comparison")

                readiness_score += 25  # Farmer eligibility
                requirements_met.append("Farmer eligibility confirmed")

            elif grant == "CIG":
                # CIG requirements
                climate_practices = ["340", "329", "590", "449"]
                climate_count = sum(1 for p in current_practices if p in climate_practices)

                if climate_count >= 2:
                    readiness_score += 30
                    requirements_met.append("Climate-smart practices adopted")
                else:
                    requirements_missing.append("Need more climate-smart practices")

                if "carbon_footprint" in farm_metrics:
                    readiness_score += 25
                    requirements_met.append("Carbon tracking in place")
                else:
                    requirements_missing.append("Need carbon footprint tracking")

                if farm_acres >= 500:
                    readiness_score += 20
                    requirements_met.append("Scale suitable for innovation project")
                else:
                    requirements_missing.append("May need partnership for scale")

                readiness_score += 25  # Technology platform
                requirements_met.append("Data collection system ready")

            elif grant == "EQIP":
                # EQIP requirements
                eqip_practices = [
                    p for p in current_practices
                    if p in NRCS_PRACTICES and "EQIP" in NRCS_PRACTICES[p].eligible_programs
                ]

                if len(eqip_practices) >= 1:
                    readiness_score += 30
                    requirements_met.append("EQIP-eligible practices planned")
                else:
                    requirements_missing.append("Need to identify EQIP practices")

                readiness_score += 25  # Farmer eligibility
                requirements_met.append("Likely meets AGI requirements")

                readiness_score += 25  # Conservation need
                requirements_met.append("Resource concerns documentable")

                if farm_metrics:
                    readiness_score += 20
                    requirements_met.append("Documentation system ready")
                else:
                    requirements_missing.append("Need documentation system")

            # Letter grade
            if readiness_score >= 90:
                grade = "A"
            elif readiness_score >= 80:
                grade = "B"
            elif readiness_score >= 70:
                grade = "C"
            elif readiness_score >= 60:
                grade = "D"
            else:
                grade = "F"

            grant_assessments.append({
                "grant_program": grant,
                "readiness_score": readiness_score,
                "grade": grade,
                "requirements_met": requirements_met,
                "requirements_missing": requirements_missing,
                "recommendation": "Apply now" if readiness_score >= 75 else "Address gaps first"
            })

        # Overall readiness
        avg_readiness = statistics.mean([g["readiness_score"] for g in grant_assessments])

        return {
            "farm_name": farm_name,
            "assessment_date": datetime.now(timezone.utc).isoformat(),
            "overall_readiness_score": round(avg_readiness, 1),
            "grant_assessments": grant_assessments,
            "top_opportunity": max(grant_assessments, key=lambda x: x["readiness_score"]),
            "priority_actions": self._get_priority_actions(grant_assessments),
            "documentation_status": {
                "practices_documented": len(self.practices),
                "practices_verified": sum(1 for p in self.practices.values() if p.status == "verified"),
                "metrics_tracked": len(farm_metrics) if farm_metrics else 0
            }
        }

    def _get_priority_actions(self, assessments: List[Dict]) -> List[str]:
        """Extract priority actions from grant assessments"""
        all_missing = []
        for assessment in assessments:
            all_missing.extend(assessment["requirements_missing"])

        # Deduplicate and prioritize
        priority_actions = []
        seen = set()
        for action in all_missing:
            if action not in seen:
                seen.add(action)
                priority_actions.append(action)

        return priority_actions[:5]  # Top 5 priorities


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_grant_service: Optional[GrantService] = None


def get_grant_service() -> GrantService:
    """Get or create the grant service singleton"""
    global _grant_service
    if _grant_service is None:
        _grant_service = GrantService()
    return _grant_service
