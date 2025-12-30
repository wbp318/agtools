"""
Climate Resilience & Adaptation Service
Comprehensive climate risk assessment, adaptation planning, and resilience scoring.

Features:
- Climate risk assessment by region
- Extreme weather vulnerability scoring
- Drought resilience calculator
- Flood risk analysis
- Heat stress impact projections
- Climate adaptation strategies
- Long-term climate projections
- Resilience scorecard for grants
- Climate-smart practice tracking
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class ClimateRiskType(str, Enum):
    DROUGHT = "drought"
    FLOOD = "flood"
    HEAT_STRESS = "heat_stress"
    COLD_STRESS = "cold_stress"
    HAIL = "hail"
    TORNADO = "tornado"
    HURRICANE = "hurricane"
    WILDFIRE = "wildfire"
    FROST = "frost"
    EXCESSIVE_MOISTURE = "excessive_moisture"


class AdaptationCategory(str, Enum):
    WATER_MANAGEMENT = "water_management"
    SOIL_HEALTH = "soil_health"
    CROP_SELECTION = "crop_selection"
    INFRASTRUCTURE = "infrastructure"
    DIVERSIFICATION = "diversification"
    INSURANCE = "insurance"
    TECHNOLOGY = "technology"
    FINANCIAL = "financial"


class SoilHealthPractice(str, Enum):
    COVER_CROPS = "cover_crops"
    NO_TILL = "no_till"
    REDUCED_TILL = "reduced_till"
    CROP_ROTATION = "crop_rotation"
    ORGANIC_MATTER = "organic_matter"
    COMPOSTING = "composting"
    RESIDUE_MANAGEMENT = "residue_management"


class WaterManagementPractice(str, Enum):
    IRRIGATION_EFFICIENCY = "irrigation_efficiency"
    DRAINAGE_IMPROVEMENT = "drainage_improvement"
    WATER_HARVESTING = "water_harvesting"
    DROUGHT_TOLERANT_VARIETIES = "drought_tolerant_varieties"
    CONTROLLED_DRAINAGE = "controlled_drainage"
    SUBSURFACE_DRIP = "subsurface_drip"
    PIVOT_CONVERSION = "pivot_conversion"


# Climate risk factors by USDA region
REGIONAL_CLIMATE_RISKS = {
    "midwest": {
        "primary_risks": [ClimateRiskType.DROUGHT, ClimateRiskType.FLOOD, ClimateRiskType.HEAT_STRESS],
        "secondary_risks": [ClimateRiskType.HAIL, ClimateRiskType.TORNADO],
        "historical_frequency": {
            ClimateRiskType.DROUGHT: 0.15,  # 15% of years
            ClimateRiskType.FLOOD: 0.20,
            ClimateRiskType.HEAT_STRESS: 0.25,
            ClimateRiskType.HAIL: 0.10,
            ClimateRiskType.TORNADO: 0.05
        },
        "projected_change_2050": {
            "temperature_increase_f": 3.5,
            "precipitation_change_percent": 5,
            "extreme_heat_days_increase": 15,
            "drought_frequency_increase": 0.25
        }
    },
    "southeast": {
        "primary_risks": [ClimateRiskType.HURRICANE, ClimateRiskType.FLOOD, ClimateRiskType.HEAT_STRESS],
        "secondary_risks": [ClimateRiskType.DROUGHT, ClimateRiskType.EXCESSIVE_MOISTURE],
        "historical_frequency": {
            ClimateRiskType.HURRICANE: 0.15,
            ClimateRiskType.FLOOD: 0.25,
            ClimateRiskType.HEAT_STRESS: 0.35,
            ClimateRiskType.DROUGHT: 0.10,
            ClimateRiskType.EXCESSIVE_MOISTURE: 0.20
        },
        "projected_change_2050": {
            "temperature_increase_f": 4.0,
            "precipitation_change_percent": 10,
            "extreme_heat_days_increase": 25,
            "hurricane_intensity_increase": 0.15
        }
    },
    "great_plains": {
        "primary_risks": [ClimateRiskType.DROUGHT, ClimateRiskType.HEAT_STRESS, ClimateRiskType.HAIL],
        "secondary_risks": [ClimateRiskType.TORNADO, ClimateRiskType.WILDFIRE],
        "historical_frequency": {
            ClimateRiskType.DROUGHT: 0.25,
            ClimateRiskType.HEAT_STRESS: 0.30,
            ClimateRiskType.HAIL: 0.15,
            ClimateRiskType.TORNADO: 0.08,
            ClimateRiskType.WILDFIRE: 0.05
        },
        "projected_change_2050": {
            "temperature_increase_f": 4.5,
            "precipitation_change_percent": -10,
            "extreme_heat_days_increase": 30,
            "drought_frequency_increase": 0.40
        }
    },
    "northeast": {
        "primary_risks": [ClimateRiskType.FLOOD, ClimateRiskType.EXCESSIVE_MOISTURE, ClimateRiskType.FROST],
        "secondary_risks": [ClimateRiskType.DROUGHT, ClimateRiskType.HEAT_STRESS],
        "historical_frequency": {
            ClimateRiskType.FLOOD: 0.18,
            ClimateRiskType.EXCESSIVE_MOISTURE: 0.20,
            ClimateRiskType.FROST: 0.12,
            ClimateRiskType.DROUGHT: 0.08,
            ClimateRiskType.HEAT_STRESS: 0.15
        },
        "projected_change_2050": {
            "temperature_increase_f": 3.0,
            "precipitation_change_percent": 15,
            "extreme_heat_days_increase": 12,
            "growing_season_extension_days": 20
        }
    },
    "west": {
        "primary_risks": [ClimateRiskType.DROUGHT, ClimateRiskType.WILDFIRE, ClimateRiskType.HEAT_STRESS],
        "secondary_risks": [ClimateRiskType.FLOOD],
        "historical_frequency": {
            ClimateRiskType.DROUGHT: 0.35,
            ClimateRiskType.WILDFIRE: 0.15,
            ClimateRiskType.HEAT_STRESS: 0.30,
            ClimateRiskType.FLOOD: 0.10
        },
        "projected_change_2050": {
            "temperature_increase_f": 4.0,
            "precipitation_change_percent": -15,
            "extreme_heat_days_increase": 35,
            "water_availability_decrease": 0.25
        }
    }
}

# Adaptation strategies with effectiveness ratings
ADAPTATION_STRATEGIES = {
    "drought": {
        "high_effectiveness": [
            {
                "practice": "Drought-tolerant crop varieties",
                "risk_reduction": 0.30,
                "cost_level": "low",
                "implementation_time": "1 season"
            },
            {
                "practice": "Soil health improvement (cover crops, no-till)",
                "risk_reduction": 0.25,
                "cost_level": "medium",
                "implementation_time": "3-5 years"
            },
            {
                "practice": "Efficient irrigation systems",
                "risk_reduction": 0.35,
                "cost_level": "high",
                "implementation_time": "1-2 years"
            }
        ],
        "medium_effectiveness": [
            {
                "practice": "Crop rotation diversification",
                "risk_reduction": 0.15,
                "cost_level": "low",
                "implementation_time": "1 season"
            },
            {
                "practice": "Early planting dates",
                "risk_reduction": 0.10,
                "cost_level": "none",
                "implementation_time": "1 season"
            }
        ]
    },
    "flood": {
        "high_effectiveness": [
            {
                "practice": "Controlled drainage",
                "risk_reduction": 0.35,
                "cost_level": "high",
                "implementation_time": "1 year"
            },
            {
                "practice": "Cover crops for soil infiltration",
                "risk_reduction": 0.25,
                "cost_level": "low",
                "implementation_time": "1 season"
            },
            {
                "practice": "Waterway/buffer establishment",
                "risk_reduction": 0.20,
                "cost_level": "medium",
                "implementation_time": "2-3 years"
            }
        ],
        "medium_effectiveness": [
            {
                "practice": "No-till/reduced tillage",
                "risk_reduction": 0.15,
                "cost_level": "low",
                "implementation_time": "1 season"
            }
        ]
    },
    "heat_stress": {
        "high_effectiveness": [
            {
                "practice": "Heat-tolerant varieties",
                "risk_reduction": 0.30,
                "cost_level": "low",
                "implementation_time": "1 season"
            },
            {
                "practice": "Earlier planting to avoid heat",
                "risk_reduction": 0.20,
                "cost_level": "none",
                "implementation_time": "1 season"
            },
            {
                "practice": "Irrigation for cooling",
                "risk_reduction": 0.25,
                "cost_level": "medium",
                "implementation_time": "1 season"
            }
        ],
        "medium_effectiveness": [
            {
                "practice": "Increased plant populations",
                "risk_reduction": 0.10,
                "cost_level": "low",
                "implementation_time": "1 season"
            }
        ]
    }
}

# Climate-smart agriculture practices
CLIMATE_SMART_PRACTICES = {
    "soil_carbon": {
        "cover_crops": {
            "description": "Winter cover crops for soil protection",
            "carbon_benefit_tons_acre_year": 0.3,
            "nrcs_code": "340",
            "resilience_benefit": ["drought", "flood", "heat_stress"]
        },
        "no_till": {
            "description": "Continuous no-till management",
            "carbon_benefit_tons_acre_year": 0.5,
            "nrcs_code": "329",
            "resilience_benefit": ["drought", "flood"]
        },
        "compost_application": {
            "description": "Regular compost/manure application",
            "carbon_benefit_tons_acre_year": 0.4,
            "nrcs_code": "590",
            "resilience_benefit": ["drought"]
        }
    },
    "water_efficiency": {
        "irrigation_scheduling": {
            "description": "Soil moisture-based irrigation",
            "water_savings_percent": 25,
            "nrcs_code": "449",
            "resilience_benefit": ["drought"]
        },
        "drip_irrigation": {
            "description": "Conversion to drip/micro irrigation",
            "water_savings_percent": 40,
            "nrcs_code": "441",
            "resilience_benefit": ["drought"]
        }
    },
    "nutrient_management": {
        "precision_application": {
            "description": "Variable rate nutrient application",
            "emission_reduction_percent": 15,
            "nrcs_code": "590",
            "resilience_benefit": ["water_quality"]
        },
        "nitrification_inhibitors": {
            "description": "Use of nitrogen stabilizers",
            "emission_reduction_percent": 20,
            "nrcs_code": "590",
            "resilience_benefit": ["water_quality"]
        }
    }
}


@dataclass
class ClimateEvent:
    """Record of climate event impact"""
    event_id: str
    event_date: date
    event_type: ClimateRiskType
    severity: str  # minor, moderate, severe, catastrophic
    fields_affected: List[str]
    acres_affected: float
    crop_loss_percent: float
    estimated_financial_loss: float
    description: str
    recovery_actions: List[str] = None


@dataclass
class AdaptationPractice:
    """Record of adaptation practice implementation"""
    practice_id: str
    field_id: str
    category: AdaptationCategory
    practice_name: str
    implementation_date: date
    nrcs_practice_code: str
    cost_total: float
    cost_share_received: float
    risk_types_addressed: List[ClimateRiskType]
    notes: str = ""


@dataclass
class ResilienceAssessment:
    """Resilience assessment record"""
    assessment_id: str
    assessment_date: date
    field_id: str
    assessor: str
    drought_score: float
    flood_score: float
    heat_score: float
    overall_score: float
    recommendations: List[str]


class ClimateResilienceService:
    """
    Climate resilience planning and assessment service.
    Designed for USDA climate-smart agriculture grants, CSP, EQIP,
    and state climate adaptation programs.
    """

    def __init__(self):
        self.climate_events: List[ClimateEvent] = []
        self.adaptation_practices: List[AdaptationPractice] = []
        self.resilience_assessments: List[ResilienceAssessment] = []

    # =========================================================================
    # CLIMATE RISK ASSESSMENT
    # =========================================================================

    def assess_climate_risk(
        self,
        region: str,
        farm_acres: float,
        crop_types: List[str],
        has_irrigation: bool = False,
        soil_type: str = "loam",
        historical_events: List[Dict] = None
    ) -> Dict:
        """
        Comprehensive climate risk assessment for a farm operation.
        """

        regional_data = REGIONAL_CLIMATE_RISKS.get(region.lower(), REGIONAL_CLIMATE_RISKS["midwest"])

        # Base risk scores by type
        risk_scores = {}

        for risk_type in ClimateRiskType:
            frequency = regional_data["historical_frequency"].get(risk_type, 0)

            # Base score from regional frequency (0-100)
            base_score = frequency * 100 * 2  # Scale up

            # Adjust for farm characteristics
            adjustment = 1.0

            # Irrigation reduces drought risk
            if risk_type == ClimateRiskType.DROUGHT and has_irrigation:
                adjustment *= 0.5

            # Soil type adjustments
            if risk_type == ClimateRiskType.DROUGHT:
                if soil_type in ["sand", "sandy_loam"]:
                    adjustment *= 1.3
                elif soil_type in ["clay", "silty_clay"]:
                    adjustment *= 0.8

            if risk_type == ClimateRiskType.FLOOD:
                if soil_type in ["clay", "silty_clay"]:
                    adjustment *= 1.3
                elif soil_type in ["sand", "sandy_loam"]:
                    adjustment *= 0.7

            # Historical event adjustment
            if historical_events:
                event_count = len([e for e in historical_events
                                  if e.get("type") == risk_type.value])
                if event_count > 2:
                    adjustment *= 1.2

            risk_scores[risk_type.value] = {
                "base_score": round(base_score, 1),
                "adjusted_score": round(base_score * adjustment, 1),
                "regional_frequency": f"{frequency * 100:.0f}% of years",
                "in_primary_risks": risk_type in regional_data["primary_risks"]
            }

        # Calculate overall risk
        primary_risk_scores = [
            risk_scores[r.value]["adjusted_score"]
            for r in regional_data["primary_risks"]
        ]
        overall_risk = sum(primary_risk_scores) / len(primary_risk_scores) if primary_risk_scores else 0

        # Risk level determination
        if overall_risk >= 40:
            risk_level = "High"
            urgency = "Immediate action recommended"
        elif overall_risk >= 25:
            risk_level = "Moderate"
            urgency = "Planning recommended within 1-2 years"
        elif overall_risk >= 15:
            risk_level = "Low-Moderate"
            urgency = "Monitor and plan for long-term"
        else:
            risk_level = "Low"
            urgency = "Standard risk management sufficient"

        return {
            "region": region,
            "farm_acres": farm_acres,
            "assessment_date": datetime.now().isoformat(),
            "risk_scores": risk_scores,
            "primary_risks": [r.value for r in regional_data["primary_risks"]],
            "secondary_risks": [r.value for r in regional_data["secondary_risks"]],
            "overall_risk_score": round(overall_risk, 1),
            "risk_level": risk_level,
            "urgency": urgency,
            "climate_projections_2050": regional_data["projected_change_2050"],
            "recommended_adaptations": self._get_priority_adaptations(
                regional_data["primary_risks"]
            ),
            "grant_opportunities": self._identify_grant_opportunities(risk_level, region)
        }

    def _get_priority_adaptations(
        self,
        primary_risks: List[ClimateRiskType]
    ) -> List[Dict]:
        """Get priority adaptation strategies for primary risks"""
        adaptations = []

        for risk in primary_risks[:3]:  # Top 3 risks
            risk_strategies = ADAPTATION_STRATEGIES.get(risk.value, {})
            high_eff = risk_strategies.get("high_effectiveness", [])

            for strategy in high_eff[:2]:  # Top 2 strategies per risk
                adaptations.append({
                    "risk_addressed": risk.value,
                    "strategy": strategy["practice"],
                    "risk_reduction": f"{strategy['risk_reduction'] * 100:.0f}%",
                    "cost_level": strategy["cost_level"],
                    "implementation_time": strategy["implementation_time"]
                })

        return adaptations

    def _identify_grant_opportunities(self, risk_level: str, region: str) -> List[Dict]:
        """Identify relevant grant programs for climate adaptation"""
        grants = [
            {
                "program": "USDA EQIP - Climate Adaptation",
                "relevance": "High" if risk_level in ["High", "Moderate"] else "Medium",
                "typical_funding": "$10,000-$50,000",
                "focus": "Conservation practices for climate resilience"
            },
            {
                "program": "CSP - Conservation Stewardship Program",
                "relevance": "High",
                "typical_funding": "$2,000-$40,000/year",
                "focus": "Climate-smart agriculture practices"
            },
            {
                "program": "USDA Climate-Smart Commodities",
                "relevance": "High" if risk_level in ["High", "Moderate"] else "Medium",
                "typical_funding": "Varies by partnership",
                "focus": "Carbon sequestration and emission reduction"
            },
            {
                "program": "State Climate Resilience Grants",
                "relevance": "Medium",
                "typical_funding": "$5,000-$25,000",
                "focus": "State-specific adaptation programs"
            }
        ]

        return grants

    # =========================================================================
    # DROUGHT RESILIENCE
    # =========================================================================

    def calculate_drought_resilience(
        self,
        field_id: str,
        soil_organic_matter: float,
        soil_water_holding_capacity: str,  # low, medium, high
        has_irrigation: bool,
        irrigation_capacity_inches: float,
        cover_crop_use: bool,
        tillage_system: str,  # conventional, reduced, no-till
        drought_tolerant_varieties: bool,
        crop_insurance: bool
    ) -> Dict:
        """
        Calculate drought resilience score for a field.
        Key metric for climate adaptation grants.
        """

        score = 0
        factors = []

        # Soil organic matter (0-25 points)
        som_score = min(25, soil_organic_matter * 5)  # 5 points per % OM up to 5%
        score += som_score
        factors.append({
            "factor": "Soil Organic Matter",
            "value": f"{soil_organic_matter}%",
            "score": round(som_score, 1),
            "max_score": 25,
            "benefit": "Higher OM increases water holding capacity"
        })

        # Water holding capacity (0-15 points)
        whc_scores = {"low": 5, "medium": 10, "high": 15}
        whc_score = whc_scores.get(soil_water_holding_capacity, 10)
        score += whc_score
        factors.append({
            "factor": "Water Holding Capacity",
            "value": soil_water_holding_capacity,
            "score": whc_score,
            "max_score": 15,
            "benefit": "Higher capacity provides drought buffer"
        })

        # Irrigation (0-25 points)
        if has_irrigation:
            irr_score = min(25, irrigation_capacity_inches * 5)
            factors.append({
                "factor": "Irrigation Capacity",
                "value": f"{irrigation_capacity_inches} inches available",
                "score": round(irr_score, 1),
                "max_score": 25,
                "benefit": "Irrigation provides critical drought relief"
            })
        else:
            irr_score = 0
            factors.append({
                "factor": "Irrigation",
                "value": "None",
                "score": 0,
                "max_score": 25,
                "benefit": "No irrigation increases vulnerability"
            })
        score += irr_score

        # Cover crops (0-10 points)
        cc_score = 10 if cover_crop_use else 0
        score += cc_score
        factors.append({
            "factor": "Cover Crops",
            "value": "Yes" if cover_crop_use else "No",
            "score": cc_score,
            "max_score": 10,
            "benefit": "Improves soil water infiltration"
        })

        # Tillage system (0-10 points)
        tillage_scores = {"conventional": 2, "reduced": 6, "no-till": 10}
        till_score = tillage_scores.get(tillage_system, 2)
        score += till_score
        factors.append({
            "factor": "Tillage System",
            "value": tillage_system,
            "score": till_score,
            "max_score": 10,
            "benefit": "Reduced tillage preserves soil moisture"
        })

        # Drought tolerant varieties (0-10 points)
        var_score = 10 if drought_tolerant_varieties else 0
        score += var_score
        factors.append({
            "factor": "Drought-Tolerant Varieties",
            "value": "Yes" if drought_tolerant_varieties else "No",
            "score": var_score,
            "max_score": 10,
            "benefit": "Genetic tolerance reduces yield loss"
        })

        # Crop insurance (0-5 points)
        ins_score = 5 if crop_insurance else 0
        score += ins_score
        factors.append({
            "factor": "Crop Insurance",
            "value": "Yes" if crop_insurance else "No",
            "score": ins_score,
            "max_score": 5,
            "benefit": "Financial protection from losses"
        })

        max_score = 100

        # Determine resilience level
        if score >= 80:
            level = "Highly Resilient"
            recommendation = "Excellent drought preparedness"
        elif score >= 60:
            level = "Moderately Resilient"
            recommendation = "Good foundation, some improvements possible"
        elif score >= 40:
            level = "Somewhat Vulnerable"
            recommendation = "Consider additional drought adaptations"
        else:
            level = "Highly Vulnerable"
            recommendation = "Priority attention needed for drought risk"

        return {
            "field_id": field_id,
            "drought_resilience_score": round(score, 1),
            "max_score": max_score,
            "resilience_level": level,
            "recommendation": recommendation,
            "factors": factors,
            "improvement_opportunities": [
                f for f in factors
                if f["score"] < f["max_score"] * 0.7
            ],
            "expected_yield_protection": {
                "moderate_drought": f"{min(95, 50 + score * 0.45):.0f}% of normal yield",
                "severe_drought": f"{min(80, 30 + score * 0.50):.0f}% of normal yield"
            },
            "grant_eligibility": {
                "eqip_drought": score < 70,
                "csp_enhancement": True,
                "state_programs": score < 60
            }
        }

    # =========================================================================
    # FLOOD RESILIENCE
    # =========================================================================

    def calculate_flood_resilience(
        self,
        field_id: str,
        in_floodplain: bool,
        flood_history_events: int,  # Number of floods in past 10 years
        soil_drainage_class: str,  # well, moderate, poor
        has_tile_drainage: bool,
        has_controlled_drainage: bool,
        has_grassed_waterways: bool,
        cover_crop_use: bool,
        tillage_system: str,
        crop_insurance: bool
    ) -> Dict:
        """
        Calculate flood resilience score for a field.
        """

        score = 100  # Start at 100, subtract for risk factors

        factors = []

        # Floodplain location (major factor)
        if in_floodplain:
            score -= 30
            factors.append({
                "factor": "Floodplain Location",
                "status": "In floodplain",
                "impact": -30,
                "mitigation": "Consider flood insurance, elevation"
            })
        else:
            factors.append({
                "factor": "Floodplain Location",
                "status": "Not in floodplain",
                "impact": 0,
                "mitigation": None
            })

        # Flood history
        history_penalty = min(25, flood_history_events * 5)
        score -= history_penalty
        factors.append({
            "factor": "Flood History",
            "status": f"{flood_history_events} events in 10 years",
            "impact": -history_penalty,
            "mitigation": "Drainage improvements, waterways"
        })

        # Soil drainage
        drainage_impacts = {"well": 0, "moderate": -10, "poor": -20}
        drainage_impact = drainage_impacts.get(soil_drainage_class, -10)
        score += drainage_impact  # Adding negative number
        factors.append({
            "factor": "Soil Drainage",
            "status": soil_drainage_class,
            "impact": drainage_impact,
            "mitigation": "Tile drainage, cover crops" if drainage_impact < 0 else None
        })

        # Positive factors (add back)
        if has_tile_drainage:
            score += 15
            factors.append({
                "factor": "Tile Drainage",
                "status": "Installed",
                "impact": +15,
                "mitigation": None
            })

        if has_controlled_drainage:
            score += 10
            factors.append({
                "factor": "Controlled Drainage",
                "status": "Installed",
                "impact": +10,
                "mitigation": None
            })

        if has_grassed_waterways:
            score += 10
            factors.append({
                "factor": "Grassed Waterways",
                "status": "Present",
                "impact": +10,
                "mitigation": None
            })

        if cover_crop_use:
            score += 10
            factors.append({
                "factor": "Cover Crops",
                "status": "Used",
                "impact": +10,
                "mitigation": None
            })

        if tillage_system in ["reduced", "no-till"]:
            score += 5
            factors.append({
                "factor": "Reduced Tillage",
                "status": tillage_system,
                "impact": +5,
                "mitigation": None
            })

        # Clamp score
        score = max(0, min(100, score))

        # Determine level
        if score >= 75:
            level = "Highly Resilient"
        elif score >= 55:
            level = "Moderately Resilient"
        elif score >= 35:
            level = "Somewhat Vulnerable"
        else:
            level = "Highly Vulnerable"

        return {
            "field_id": field_id,
            "flood_resilience_score": round(score, 1),
            "resilience_level": level,
            "factors": factors,
            "recommendations": [
                f["mitigation"] for f in factors
                if f["mitigation"] is not None
            ],
            "estimated_loss_reduction": {
                "minor_flood": f"{score * 0.8:.0f}% yield protected",
                "major_flood": f"{score * 0.5:.0f}% yield protected"
            }
        }

    # =========================================================================
    # CLIMATE PROJECTIONS
    # =========================================================================

    def get_climate_projections(
        self,
        region: str,
        crop_type: str,
        projection_year: int = 2050
    ) -> Dict:
        """
        Get climate projections and impact analysis for planning.
        """

        regional_data = REGIONAL_CLIMATE_RISKS.get(region.lower(), REGIONAL_CLIMATE_RISKS["midwest"])
        projections = regional_data.get("projected_change_2050", {})

        # Crop-specific impact factors
        CROP_HEAT_SENSITIVITY = {
            "corn": {"optimal_temp": 77, "stress_temp": 95, "yield_loss_per_degree": 2.5},
            "soybean": {"optimal_temp": 77, "stress_temp": 93, "yield_loss_per_degree": 2.0},
            "wheat": {"optimal_temp": 70, "stress_temp": 85, "yield_loss_per_degree": 3.0},
            "rice": {"optimal_temp": 82, "stress_temp": 95, "yield_loss_per_degree": 1.8},
            "cotton": {"optimal_temp": 80, "stress_temp": 100, "yield_loss_per_degree": 1.5}
        }

        crop_data = CROP_HEAT_SENSITIVITY.get(crop_type.lower(),
                                               CROP_HEAT_SENSITIVITY["corn"])

        # Calculate projected impacts
        temp_increase = projections.get("temperature_increase_f", 3.5)
        extra_heat_days = projections.get("extreme_heat_days_increase", 15)

        # Yield impact estimate
        yield_impact = extra_heat_days * crop_data["yield_loss_per_degree"] / 100
        yield_impact = min(0.30, yield_impact)  # Cap at 30%

        # Growing season changes
        growing_season_change = projections.get("growing_season_extension_days",
                                                 temp_increase * 3)

        return {
            "region": region,
            "projection_year": projection_year,
            "crop_type": crop_type,
            "climate_changes": {
                "temperature_increase_f": temp_increase,
                "precipitation_change_percent": projections.get("precipitation_change_percent", 0),
                "extreme_heat_days_increase": extra_heat_days,
                "growing_season_change_days": round(growing_season_change, 0)
            },
            "crop_impacts": {
                "yield_impact_without_adaptation": f"-{yield_impact * 100:.1f}%",
                "heat_stress_increase": f"+{extra_heat_days} days above {crop_data['stress_temp']}F",
                "water_demand_change": f"+{temp_increase * 3:.0f}%"
            },
            "adaptation_potential": {
                "variety_selection": "Can offset 30-50% of heat impact",
                "irrigation_expansion": "Critical in water-limited regions",
                "planting_date_shifts": f"Earlier by {temp_increase * 3:.0f} days",
                "soil_health": "Improved water retention reduces drought stress"
            },
            "opportunities": {
                "longer_growing_season": growing_season_change > 0,
                "double_cropping_potential": growing_season_change > 14,
                "new_crop_options": temp_increase > 3
            },
            "planning_recommendations": [
                f"Select {crop_type} varieties with improved heat tolerance",
                "Invest in soil health to improve water retention",
                "Consider irrigation capacity expansion",
                "Develop flexible planting strategies",
                "Monitor emerging pest/disease pressures"
            ]
        }

    # =========================================================================
    # ADAPTATION TRACKING
    # =========================================================================

    def record_adaptation_practice(self, practice: AdaptationPractice) -> Dict:
        """Record implementation of an adaptation practice"""
        self.adaptation_practices.append(practice)

        return {
            "recorded": True,
            "practice_id": practice.practice_id,
            "practice": practice.practice_name,
            "category": practice.category.value,
            "risks_addressed": [r.value for r in practice.risk_types_addressed],
            "cost_share_received": practice.cost_share_received,
            "message": "Adaptation practice recorded"
        }

    def get_adaptation_summary(
        self,
        field_id: Optional[str] = None
    ) -> Dict:
        """Get summary of adaptation practices implemented"""

        practices = self.adaptation_practices
        if field_id:
            practices = [p for p in practices if p.field_id == field_id]

        if not practices:
            return {
                "practices_implemented": 0,
                "message": "No adaptation practices recorded"
            }

        total_cost = sum(p.cost_total for p in practices)
        total_cost_share = sum(p.cost_share_received for p in practices)

        # Group by category
        by_category = {}
        for p in practices:
            cat = p.category.value
            if cat not in by_category:
                by_category[cat] = {"count": 0, "cost": 0}
            by_category[cat]["count"] += 1
            by_category[cat]["cost"] += p.cost_total

        # Risks addressed
        risks_addressed = set()
        for p in practices:
            for r in p.risk_types_addressed:
                risks_addressed.add(r.value)

        return {
            "practices_implemented": len(practices),
            "total_investment": round(total_cost, 2),
            "cost_share_received": round(total_cost_share, 2),
            "net_farmer_cost": round(total_cost - total_cost_share, 2),
            "by_category": by_category,
            "risks_addressed": list(risks_addressed),
            "nrcs_practices": list(set(p.nrcs_practice_code for p in practices if p.nrcs_practice_code)),
            "practice_details": [
                {
                    "practice": p.practice_name,
                    "category": p.category.value,
                    "date": p.implementation_date.isoformat(),
                    "cost": p.cost_total
                }
                for p in practices
            ]
        }

    # =========================================================================
    # CLIMATE EVENT TRACKING
    # =========================================================================

    def record_climate_event(self, event: ClimateEvent) -> Dict:
        """Record a climate event and its impacts"""
        self.climate_events.append(event)

        return {
            "recorded": True,
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "severity": event.severity,
            "acres_affected": event.acres_affected,
            "estimated_loss": event.estimated_financial_loss,
            "message": "Climate event recorded"
        }

    def analyze_climate_event_history(
        self,
        start_year: int,
        end_year: int
    ) -> Dict:
        """Analyze historical climate events for risk assessment"""

        events = [
            e for e in self.climate_events
            if start_year <= e.event_date.year <= end_year
        ]

        if not events:
            return {
                "period": f"{start_year}-{end_year}",
                "events_recorded": 0,
                "message": "No climate events in this period"
            }

        # Group by type
        by_type = {}
        for e in events:
            et = e.event_type.value
            if et not in by_type:
                by_type[et] = {"count": 0, "total_loss": 0, "acres_affected": 0}
            by_type[et]["count"] += 1
            by_type[et]["total_loss"] += e.estimated_financial_loss
            by_type[et]["acres_affected"] += e.acres_affected

        # Annual frequency
        years = end_year - start_year + 1
        annual_frequency = {
            et: data["count"] / years
            for et, data in by_type.items()
        }

        # Total losses
        total_loss = sum(e.estimated_financial_loss for e in events)
        avg_annual_loss = total_loss / years

        return {
            "period": f"{start_year}-{end_year}",
            "years_analyzed": years,
            "total_events": len(events),
            "events_by_type": by_type,
            "annual_frequency": annual_frequency,
            "financial_impact": {
                "total_losses": round(total_loss, 2),
                "average_annual_loss": round(avg_annual_loss, 2),
                "largest_single_event": round(max(e.estimated_financial_loss for e in events), 2)
            },
            "risk_trends": {
                "most_frequent": max(by_type.keys(), key=lambda k: by_type[k]["count"]) if by_type else None,
                "most_costly": max(by_type.keys(), key=lambda k: by_type[k]["total_loss"]) if by_type else None
            }
        }

    # =========================================================================
    # RESILIENCE SCORECARD
    # =========================================================================

    def calculate_overall_resilience_score(
        self,
        farm_id: str,
        region: str,
        drought_data: Dict,
        flood_data: Dict,
        heat_data: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate comprehensive resilience scorecard for grant applications.
        """

        # Extract scores
        drought_score = drought_data.get("drought_resilience_score", 50)
        flood_score = flood_data.get("flood_resilience_score", 50)
        heat_score = heat_data.get("heat_resilience_score", 50) if heat_data else 50

        # Get regional risk weights
        regional_data = REGIONAL_CLIMATE_RISKS.get(region.lower(), REGIONAL_CLIMATE_RISKS["midwest"])
        primary_risks = [r.value for r in regional_data["primary_risks"]]

        # Weight scores by regional relevance
        weights = {"drought": 0.33, "flood": 0.33, "heat_stress": 0.34}

        if "drought" in primary_risks:
            weights["drought"] = 0.40
            weights["flood"] = 0.30
            weights["heat_stress"] = 0.30
        elif "flood" in primary_risks:
            weights["drought"] = 0.30
            weights["flood"] = 0.40
            weights["heat_stress"] = 0.30

        # Calculate weighted overall score
        overall_score = (
            drought_score * weights["drought"] +
            flood_score * weights["flood"] +
            heat_score * weights["heat_stress"]
        )

        # Get adaptation progress
        adaptation_summary = self.get_adaptation_summary()

        # Determine grade
        if overall_score >= 85:
            grade = "A"
            status = "Climate-Ready Leader"
        elif overall_score >= 75:
            grade = "B"
            status = "Strong Resilience"
        elif overall_score >= 65:
            grade = "C"
            status = "Moderate Resilience"
        elif overall_score >= 50:
            grade = "D"
            status = "Needs Improvement"
        else:
            grade = "F"
            status = "High Vulnerability"

        return {
            "farm_id": farm_id,
            "region": region,
            "assessment_date": datetime.now().isoformat(),
            "component_scores": {
                "drought_resilience": {
                    "score": round(drought_score, 1),
                    "weight": weights["drought"],
                    "weighted_score": round(drought_score * weights["drought"], 1)
                },
                "flood_resilience": {
                    "score": round(flood_score, 1),
                    "weight": weights["flood"],
                    "weighted_score": round(flood_score * weights["flood"], 1)
                },
                "heat_resilience": {
                    "score": round(heat_score, 1),
                    "weight": weights["heat_stress"],
                    "weighted_score": round(heat_score * weights["heat_stress"], 1)
                }
            },
            "overall_score": round(overall_score, 1),
            "grade": grade,
            "status": status,
            "adaptation_progress": {
                "practices_implemented": adaptation_summary.get("practices_implemented", 0),
                "total_investment": adaptation_summary.get("total_investment", 0),
                "risks_addressed": adaptation_summary.get("risks_addressed", [])
            },
            "certifications": {
                "climate_smart_eligible": overall_score >= 65,
                "resilience_leader": overall_score >= 85,
                "priority_for_assistance": overall_score < 50
            },
            "recommendations": self._generate_resilience_recommendations(
                drought_score, flood_score, heat_score
            ),
            "grant_documentation": {
                "overall_resilience_score": round(overall_score, 1),
                "grade": grade,
                "primary_risks": primary_risks,
                "adaptations_completed": adaptation_summary.get("practices_implemented", 0),
                "assessment_methodology": "Multi-factor weighted resilience assessment"
            }
        }

    def _generate_resilience_recommendations(
        self,
        drought_score: float,
        flood_score: float,
        heat_score: float
    ) -> List[str]:
        """Generate prioritized recommendations based on scores"""
        recommendations = []

        scores = [
            ("Drought", drought_score, "drought"),
            ("Flood", flood_score, "flood"),
            ("Heat Stress", heat_score, "heat_stress")
        ]

        # Sort by lowest score (highest priority)
        scores.sort(key=lambda x: x[1])

        for name, score, risk_type in scores:
            if score < 60:
                strategies = ADAPTATION_STRATEGIES.get(risk_type, {})
                high_eff = strategies.get("high_effectiveness", [])
                if high_eff:
                    recommendations.append(
                        f"{name} resilience needs improvement (score: {score:.0f}). "
                        f"Priority: {high_eff[0]['practice']}"
                    )

        if not recommendations:
            recommendations.append(
                "Strong resilience across all risk types. "
                "Continue monitoring and maintaining practices."
            )

        return recommendations[:3]  # Top 3

    # =========================================================================
    # GRANT REPORTING
    # =========================================================================

    def generate_climate_resilience_grant_report(
        self,
        farm_id: str,
        region: str,
        grant_program: str
    ) -> Dict:
        """
        Generate comprehensive climate resilience report for grant applications.
        """

        risk_assessment = self.assess_climate_risk(region, 0, [], False, "loam")
        adaptation_summary = self.get_adaptation_summary()
        event_history = self.analyze_climate_event_history(
            datetime.now().year - 5,
            datetime.now().year
        )

        return {
            "report_title": f"Climate Resilience Assessment Report",
            "farm_id": farm_id,
            "region": region,
            "grant_program": grant_program,
            "generated_date": datetime.now().isoformat(),
            "sections": {
                "climate_risk_assessment": {
                    "overall_risk_level": risk_assessment.get("risk_level"),
                    "primary_risks": risk_assessment.get("primary_risks", []),
                    "risk_scores": risk_assessment.get("risk_scores", {})
                },
                "historical_events": {
                    "events_recorded": event_history.get("total_events", 0),
                    "total_financial_impact": event_history.get("financial_impact", {}).get("total_losses", 0),
                    "most_frequent_risk": event_history.get("risk_trends", {}).get("most_frequent")
                },
                "adaptation_actions": {
                    "practices_implemented": adaptation_summary.get("practices_implemented", 0),
                    "total_investment": adaptation_summary.get("total_investment", 0),
                    "cost_share_received": adaptation_summary.get("cost_share_received", 0),
                    "risks_addressed": adaptation_summary.get("risks_addressed", [])
                },
                "climate_projections": {
                    "temperature_increase": f"{risk_assessment.get('climate_projections_2050', {}).get('temperature_increase_f', 0)}°F by 2050",
                    "precipitation_change": f"{risk_assessment.get('climate_projections_2050', {}).get('precipitation_change_percent', 0)}%"
                }
            },
            "grant_compliance_metrics": {
                "risk_assessment_complete": True,
                "adaptations_documented": adaptation_summary.get("practices_implemented", 0) > 0,
                "climate_projections_analyzed": True,
                "nrcs_practices": adaptation_summary.get("nrcs_practices", [])
            },
            "recommended_next_steps": risk_assessment.get("recommended_adaptations", [])
        }


# Create singleton instance
climate_resilience_service = ClimateResilienceService()
