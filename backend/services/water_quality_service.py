"""
Water Quality & Nutrient Management Service
Grant-focused module for tracking water quality, nutrient runoff, and watershed impact.

Features:
- Nutrient runoff modeling (N, P, K loss estimates)
- Water quality monitoring integration
- Watershed impact analysis
- Buffer strip effectiveness calculator
- Tile drainage management
- Nutrient use efficiency (NUE) tracking
- 4R Nutrient Stewardship compliance
- Edge-of-field monitoring support
"""

from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class WaterBodyType(str, Enum):
    STREAM = "stream"
    RIVER = "river"
    LAKE = "lake"
    POND = "pond"
    WETLAND = "wetland"
    DRAINAGE_DITCH = "drainage_ditch"
    GROUNDWATER = "groundwater"


class NutrientSource(str, Enum):
    COMMERCIAL_FERTILIZER = "commercial_fertilizer"
    MANURE = "manure"
    BIOSOLIDS = "biosolids"
    LEGUME_CREDIT = "legume_credit"
    IRRIGATION_WATER = "irrigation_water"
    ATMOSPHERIC_DEPOSITION = "atmospheric_deposition"


class SoilDrainageClass(str, Enum):
    VERY_POORLY_DRAINED = "very_poorly_drained"
    POORLY_DRAINED = "poorly_drained"
    SOMEWHAT_POORLY_DRAINED = "somewhat_poorly_drained"
    MODERATELY_WELL_DRAINED = "moderately_well_drained"
    WELL_DRAINED = "well_drained"
    SOMEWHAT_EXCESSIVELY_DRAINED = "somewhat_excessively_drained"
    EXCESSIVELY_DRAINED = "excessively_drained"


class BufferType(str, Enum):
    GRASS_WATERWAY = "grass_waterway"
    RIPARIAN_BUFFER = "riparian_buffer"
    FILTER_STRIP = "filter_strip"
    WETLAND_BUFFER = "wetland_buffer"
    CONTOUR_BUFFER = "contour_buffer"
    FIELD_BORDER = "field_border"


# Nutrient loss coefficients by soil type and drainage (lbs/acre/year base rates)
NUTRIENT_LOSS_COEFFICIENTS = {
    "nitrogen": {
        "base_leaching_rate": 0.25,  # 25% of applied N can leach
        "base_runoff_rate": 0.05,    # 5% in surface runoff
        "volatilization_rate": 0.10, # 10% volatilization (urea)
        "denitrification_rate": 0.08 # 8% denitrification
    },
    "phosphorus": {
        "base_runoff_rate": 0.03,    # 3% in surface runoff
        "sediment_bound_rate": 0.02, # 2% with sediment
        "dissolved_rate": 0.01       # 1% dissolved
    },
    "potassium": {
        "base_leaching_rate": 0.05,  # 5% leaching
        "base_runoff_rate": 0.02     # 2% runoff
    }
}

# Soil drainage impact multipliers
DRAINAGE_MULTIPLIERS = {
    SoilDrainageClass.VERY_POORLY_DRAINED: {"runoff": 1.8, "leaching": 0.5},
    SoilDrainageClass.POORLY_DRAINED: {"runoff": 1.5, "leaching": 0.7},
    SoilDrainageClass.SOMEWHAT_POORLY_DRAINED: {"runoff": 1.3, "leaching": 0.9},
    SoilDrainageClass.MODERATELY_WELL_DRAINED: {"runoff": 1.0, "leaching": 1.0},
    SoilDrainageClass.WELL_DRAINED: {"runoff": 0.8, "leaching": 1.2},
    SoilDrainageClass.SOMEWHAT_EXCESSIVELY_DRAINED: {"runoff": 0.6, "leaching": 1.5},
    SoilDrainageClass.EXCESSIVELY_DRAINED: {"runoff": 0.4, "leaching": 1.8}
}

# Buffer strip effectiveness (% reduction)
BUFFER_EFFECTIVENESS = {
    BufferType.GRASS_WATERWAY: {
        "sediment": 0.85,
        "nitrogen": 0.50,
        "phosphorus": 0.65,
        "pesticides": 0.60
    },
    BufferType.RIPARIAN_BUFFER: {
        "sediment": 0.90,
        "nitrogen": 0.70,
        "phosphorus": 0.75,
        "pesticides": 0.70
    },
    BufferType.FILTER_STRIP: {
        "sediment": 0.80,
        "nitrogen": 0.45,
        "phosphorus": 0.60,
        "pesticides": 0.55
    },
    BufferType.WETLAND_BUFFER: {
        "sediment": 0.95,
        "nitrogen": 0.80,
        "phosphorus": 0.70,
        "pesticides": 0.75
    },
    BufferType.CONTOUR_BUFFER: {
        "sediment": 0.70,
        "nitrogen": 0.35,
        "phosphorus": 0.50,
        "pesticides": 0.45
    },
    BufferType.FIELD_BORDER: {
        "sediment": 0.60,
        "nitrogen": 0.30,
        "phosphorus": 0.45,
        "pesticides": 0.40
    }
}

# 4R Nutrient Stewardship criteria
FOUR_R_CRITERIA = {
    "right_source": {
        "description": "Match fertilizer type to crop needs",
        "best_practices": [
            "Use enhanced efficiency fertilizers",
            "Consider slow-release formulations",
            "Match nutrient ratios to soil tests",
            "Use stabilizers/inhibitors when appropriate"
        ]
    },
    "right_rate": {
        "description": "Match amount to crop needs based on soil tests",
        "best_practices": [
            "Base rates on recent soil tests",
            "Account for all nutrient credits",
            "Use realistic yield goals",
            "Consider field variability"
        ]
    },
    "right_time": {
        "description": "Make nutrients available when crops need them",
        "best_practices": [
            "Split nitrogen applications",
            "Avoid fall application in vulnerable areas",
            "Time with crop uptake patterns",
            "Consider weather forecasts"
        ]
    },
    "right_place": {
        "description": "Keep nutrients where crops can use them",
        "best_practices": [
            "Incorporate fertilizer when possible",
            "Use precision placement",
            "Band apply when appropriate",
            "Avoid sensitive areas"
        ]
    }
}


@dataclass
class NutrientApplication:
    """Record of nutrient application"""
    field_id: str
    date: date
    source: NutrientSource
    product_name: str
    nitrogen_lbs_acre: float
    phosphorus_lbs_acre: float  # P2O5
    potassium_lbs_acre: float   # K2O
    application_method: str     # broadcast, banded, injected, etc.
    incorporated: bool
    inhibitor_used: bool        # Nitrification/urease inhibitor
    notes: str = ""


@dataclass
class WaterSample:
    """Water quality sample record"""
    sample_id: str
    location_id: str
    location_name: str
    water_body_type: WaterBodyType
    sample_date: datetime
    sample_depth_inches: float

    # Nutrient concentrations (mg/L)
    nitrate_n: Optional[float] = None
    ammonium_n: Optional[float] = None
    total_nitrogen: Optional[float] = None
    orthophosphate: Optional[float] = None
    total_phosphorus: Optional[float] = None
    potassium: Optional[float] = None

    # Other parameters
    ph: Optional[float] = None
    dissolved_oxygen: Optional[float] = None
    turbidity_ntu: Optional[float] = None
    conductivity_us_cm: Optional[float] = None
    temperature_f: Optional[float] = None

    # Sediment
    total_suspended_solids: Optional[float] = None

    # Pesticides detected
    pesticides_detected: List[Dict] = None

    lab_name: str = ""
    notes: str = ""


@dataclass
class BufferStrip:
    """Conservation buffer information"""
    buffer_id: str
    field_id: str
    buffer_type: BufferType
    length_feet: float
    average_width_feet: float
    vegetation_type: str
    date_established: date
    nrcs_practice_code: str  # e.g., "393" for filter strip
    cost_share_program: str = ""
    maintenance_schedule: str = ""


@dataclass
class TileDrainageSystem:
    """Tile drainage system information"""
    system_id: str
    field_id: str
    total_acres_drained: float
    tile_spacing_feet: float
    tile_depth_inches: float
    outlet_type: str  # direct, controlled, saturated buffer, bioreactor
    has_controlled_drainage: bool
    has_saturated_buffer: bool
    has_bioreactor: bool
    installation_year: int
    notes: str = ""


class WaterQualityService:
    """
    Comprehensive water quality and nutrient management service.
    Designed for grant compliance, environmental reporting, and conservation planning.
    """

    def __init__(self):
        self.nutrient_applications: List[NutrientApplication] = []
        self.water_samples: List[WaterSample] = []
        self.buffer_strips: List[BufferStrip] = []
        self.tile_systems: List[TileDrainageSystem] = []
        self.monitoring_locations: Dict[str, Dict] = {}

    # =========================================================================
    # NUTRIENT APPLICATION TRACKING
    # =========================================================================

    def record_nutrient_application(self, application: NutrientApplication) -> Dict:
        """Record a nutrient application event"""
        self.nutrient_applications.append(application)

        # Calculate potential losses
        loss_estimate = self.estimate_nutrient_loss(
            application.nitrogen_lbs_acre,
            application.phosphorus_lbs_acre,
            application.potassium_lbs_acre,
            SoilDrainageClass.MODERATELY_WELL_DRAINED,  # Default
            application.incorporated,
            application.inhibitor_used
        )

        return {
            "recorded": True,
            "application_id": f"NA-{len(self.nutrient_applications)}",
            "field_id": application.field_id,
            "date": application.date.isoformat(),
            "nutrients_applied": {
                "nitrogen_lbs_acre": application.nitrogen_lbs_acre,
                "phosphorus_lbs_acre": application.phosphorus_lbs_acre,
                "potassium_lbs_acre": application.potassium_lbs_acre
            },
            "estimated_losses": loss_estimate,
            "message": "Nutrient application recorded successfully"
        }

    def estimate_nutrient_loss(
        self,
        nitrogen_applied: float,
        phosphorus_applied: float,
        potassium_applied: float,
        drainage_class: SoilDrainageClass,
        incorporated: bool = False,
        inhibitor_used: bool = False,
        annual_precip_inches: float = 50.0,
        slope_percent: float = 2.0
    ) -> Dict:
        """
        Estimate potential nutrient losses from applied fertilizer.
        Based on research from Midwest universities and USDA-ARS.
        """

        drainage_mult = DRAINAGE_MULTIPLIERS.get(
            drainage_class,
            {"runoff": 1.0, "leaching": 1.0}
        )

        # Precipitation factor (higher precip = more loss)
        precip_factor = annual_precip_inches / 40.0  # Normalized to 40"

        # Slope factor for runoff
        slope_factor = 1.0 + (slope_percent / 10.0)

        # Incorporation reduces surface losses by 50-80%
        incorporation_factor = 0.3 if incorporated else 1.0

        # Inhibitors reduce N losses by 10-30%
        inhibitor_factor = 0.75 if inhibitor_used else 1.0

        # Calculate nitrogen losses
        n_coef = NUTRIENT_LOSS_COEFFICIENTS["nitrogen"]
        n_leaching = (nitrogen_applied * n_coef["base_leaching_rate"] *
                     drainage_mult["leaching"] * precip_factor * inhibitor_factor)
        n_runoff = (nitrogen_applied * n_coef["base_runoff_rate"] *
                   drainage_mult["runoff"] * slope_factor * incorporation_factor)
        n_volatilization = (nitrogen_applied * n_coef["volatilization_rate"] *
                           incorporation_factor * inhibitor_factor)
        n_denitrification = (nitrogen_applied * n_coef["denitrification_rate"] *
                            drainage_mult["runoff"])  # More in wet soils

        total_n_loss = n_leaching + n_runoff + n_volatilization + n_denitrification
        n_efficiency = ((nitrogen_applied - total_n_loss) / nitrogen_applied * 100
                       if nitrogen_applied > 0 else 100)

        # Calculate phosphorus losses
        p_coef = NUTRIENT_LOSS_COEFFICIENTS["phosphorus"]
        p_runoff = (phosphorus_applied * p_coef["base_runoff_rate"] *
                   drainage_mult["runoff"] * slope_factor * incorporation_factor)
        p_sediment = (phosphorus_applied * p_coef["sediment_bound_rate"] *
                     slope_factor)
        p_dissolved = phosphorus_applied * p_coef["dissolved_rate"] * precip_factor

        total_p_loss = p_runoff + p_sediment + p_dissolved

        # Calculate potassium losses
        k_coef = NUTRIENT_LOSS_COEFFICIENTS["potassium"]
        k_leaching = (potassium_applied * k_coef["base_leaching_rate"] *
                     drainage_mult["leaching"] * precip_factor)
        k_runoff = (potassium_applied * k_coef["base_runoff_rate"] *
                   drainage_mult["runoff"] * slope_factor)

        total_k_loss = k_leaching + k_runoff

        return {
            "nitrogen": {
                "applied_lbs_acre": nitrogen_applied,
                "leaching_loss": round(n_leaching, 2),
                "runoff_loss": round(n_runoff, 2),
                "volatilization_loss": round(n_volatilization, 2),
                "denitrification_loss": round(n_denitrification, 2),
                "total_loss_lbs_acre": round(total_n_loss, 2),
                "use_efficiency_percent": round(n_efficiency, 1),
                "loss_pathway_primary": "leaching" if n_leaching > n_runoff else "runoff"
            },
            "phosphorus": {
                "applied_lbs_acre": phosphorus_applied,
                "runoff_loss": round(p_runoff, 2),
                "sediment_bound_loss": round(p_sediment, 2),
                "dissolved_loss": round(p_dissolved, 2),
                "total_loss_lbs_acre": round(total_p_loss, 2),
                "loss_pathway_primary": "sediment" if p_sediment > p_runoff else "runoff"
            },
            "potassium": {
                "applied_lbs_acre": potassium_applied,
                "leaching_loss": round(k_leaching, 2),
                "runoff_loss": round(k_runoff, 2),
                "total_loss_lbs_acre": round(total_k_loss, 2)
            },
            "factors_applied": {
                "drainage_class": drainage_class.value,
                "incorporated": incorporated,
                "inhibitor_used": inhibitor_used,
                "annual_precipitation_in": annual_precip_inches,
                "slope_percent": slope_percent
            },
            "recommendations": self._generate_loss_reduction_recommendations(
                n_efficiency, total_p_loss, incorporated, inhibitor_used
            )
        }

    def _generate_loss_reduction_recommendations(
        self,
        n_efficiency: float,
        p_loss: float,
        incorporated: bool,
        inhibitor_used: bool
    ) -> List[str]:
        """Generate recommendations to reduce nutrient losses"""
        recommendations = []

        if n_efficiency < 70:
            recommendations.append(
                "Nitrogen use efficiency is below optimal (<70%). "
                "Consider split applications to better match crop uptake."
            )

        if not incorporated:
            recommendations.append(
                "Incorporate fertilizer within 24 hours to reduce "
                "volatilization and runoff losses by 50-80%."
            )

        if not inhibitor_used:
            recommendations.append(
                "Consider nitrification inhibitors (e.g., N-Serve, Instinct) "
                "to reduce nitrogen leaching by 10-30%."
            )

        if p_loss > 0.5:
            recommendations.append(
                "Phosphorus loss risk is elevated. Consider buffer strips, "
                "reduced tillage, or cover crops to reduce sediment transport."
            )

        if not recommendations:
            recommendations.append(
                "Current practices show good nutrient management. "
                "Continue monitoring and documenting for grant reporting."
            )

        return recommendations

    def calculate_nutrient_use_efficiency(
        self,
        field_id: str,
        crop_year: int,
        yield_achieved: float,
        crop_type: str
    ) -> Dict:
        """
        Calculate Nutrient Use Efficiency (NUE) metrics.
        Key metric for grant applications and sustainability reporting.
        """

        # Crop nutrient uptake (lbs per bushel harvested)
        CROP_NUTRIENT_UPTAKE = {
            "corn": {"N": 0.90, "P2O5": 0.38, "K2O": 0.27},  # Per bushel grain
            "soybean": {"N": 3.40, "P2O5": 0.80, "K2O": 1.40},
            "wheat": {"N": 1.25, "P2O5": 0.50, "K2O": 0.30},
            "rice": {"N": 0.90, "P2O5": 0.45, "K2O": 0.25}
        }

        # Get applications for this field and year
        field_apps = [a for a in self.nutrient_applications
                     if a.field_id == field_id and a.date.year == crop_year]

        total_n_applied = sum(a.nitrogen_lbs_acre for a in field_apps)
        total_p_applied = sum(a.phosphorus_lbs_acre for a in field_apps)
        total_k_applied = sum(a.potassium_lbs_acre for a in field_apps)

        # Get crop uptake coefficients
        uptake = CROP_NUTRIENT_UPTAKE.get(crop_type.lower(),
                                          CROP_NUTRIENT_UPTAKE["corn"])

        # Calculate nutrient removed in grain
        n_removed = yield_achieved * uptake["N"]
        p_removed = yield_achieved * uptake["P2O5"]
        k_removed = yield_achieved * uptake["K2O"]

        # Calculate efficiencies
        n_use_efficiency = (n_removed / total_n_applied * 100
                          if total_n_applied > 0 else 0)
        p_use_efficiency = (p_removed / total_p_applied * 100
                          if total_p_applied > 0 else 0)
        k_use_efficiency = (k_removed / total_k_applied * 100
                          if total_k_applied > 0 else 0)

        # Partial Factor Productivity (yield per unit nutrient)
        pfp_n = yield_achieved / total_n_applied if total_n_applied > 0 else 0
        pfp_p = yield_achieved / total_p_applied if total_p_applied > 0 else 0

        # Rate assessment
        def assess_nue(efficiency, nutrient):
            if nutrient == "N":
                if efficiency >= 80: return "Excellent"
                elif efficiency >= 60: return "Good"
                elif efficiency >= 40: return "Fair"
                else: return "Poor - review N management"
            else:  # P and K
                if efficiency >= 100: return "Mining soil reserves"
                elif efficiency >= 70: return "Sustainable"
                elif efficiency >= 40: return "Building soil reserves"
                else: return "Excessive application"

        return {
            "field_id": field_id,
            "crop_year": crop_year,
            "crop_type": crop_type,
            "yield_bu_acre": yield_achieved,
            "nutrients_applied": {
                "nitrogen_lbs_acre": total_n_applied,
                "phosphorus_lbs_acre": total_p_applied,
                "potassium_lbs_acre": total_k_applied
            },
            "nutrients_removed": {
                "nitrogen_lbs_acre": round(n_removed, 1),
                "phosphorus_lbs_acre": round(p_removed, 1),
                "potassium_lbs_acre": round(k_removed, 1)
            },
            "nutrient_balance": {
                "nitrogen_lbs_acre": round(total_n_applied - n_removed, 1),
                "phosphorus_lbs_acre": round(total_p_applied - p_removed, 1),
                "potassium_lbs_acre": round(total_k_applied - k_removed, 1)
            },
            "use_efficiency_percent": {
                "nitrogen": round(n_use_efficiency, 1),
                "phosphorus": round(p_use_efficiency, 1),
                "potassium": round(k_use_efficiency, 1)
            },
            "partial_factor_productivity": {
                "nitrogen_bu_per_lb": round(pfp_n, 2),
                "phosphorus_bu_per_lb": round(pfp_p, 2)
            },
            "assessment": {
                "nitrogen": assess_nue(n_use_efficiency, "N"),
                "phosphorus": assess_nue(p_use_efficiency, "P"),
                "potassium": assess_nue(k_use_efficiency, "K")
            },
            "grant_metrics": {
                "meets_4r_criteria": n_use_efficiency >= 50 and p_use_efficiency <= 120,
                "sustainability_score": min(100, (n_use_efficiency + p_use_efficiency) / 2),
                "improvement_potential": max(0, 80 - n_use_efficiency)
            }
        }

    # =========================================================================
    # WATER QUALITY MONITORING
    # =========================================================================

    def add_monitoring_location(
        self,
        location_id: str,
        name: str,
        water_body_type: WaterBodyType,
        latitude: float,
        longitude: float,
        upstream_field_ids: List[str],
        description: str = ""
    ) -> Dict:
        """Add a water quality monitoring location"""
        self.monitoring_locations[location_id] = {
            "location_id": location_id,
            "name": name,
            "water_body_type": water_body_type.value,
            "latitude": latitude,
            "longitude": longitude,
            "upstream_field_ids": upstream_field_ids,
            "description": description,
            "date_established": datetime.now().isoformat()
        }

        return {
            "success": True,
            "location_id": location_id,
            "message": f"Monitoring location '{name}' added successfully"
        }

    def record_water_sample(self, sample: WaterSample) -> Dict:
        """Record a water quality sample"""
        self.water_samples.append(sample)

        # Evaluate against water quality standards
        assessment = self.assess_water_quality(sample)

        return {
            "recorded": True,
            "sample_id": sample.sample_id,
            "location": sample.location_name,
            "date": sample.sample_date.isoformat(),
            "quality_assessment": assessment,
            "message": "Water sample recorded successfully"
        }

    def assess_water_quality(self, sample: WaterSample) -> Dict:
        """
        Assess water quality against EPA and state standards.
        Standards based on EPA criteria for aquatic life and drinking water.
        """

        # EPA water quality criteria (mg/L)
        WATER_QUALITY_STANDARDS = {
            "nitrate_n": {
                "drinking_water": 10.0,  # EPA MCL
                "aquatic_life": 2.0,     # General guidance
                "excellent": 1.0
            },
            "total_phosphorus": {
                "streams": 0.1,          # EPA recommendation
                "lakes": 0.025,          # Eutrophication threshold
                "excellent": 0.01
            },
            "dissolved_oxygen": {
                "minimum": 5.0,          # Aquatic life
                "good": 7.0,
                "excellent": 9.0
            },
            "ph": {
                "minimum": 6.5,
                "maximum": 9.0,
                "optimal_min": 6.8,
                "optimal_max": 8.5
            },
            "turbidity": {
                "drinking_water": 4.0,   # NTU
                "aquatic_life": 25.0,
                "excellent": 5.0
            }
        }

        issues = []
        status = "Good"

        # Check nitrate
        if sample.nitrate_n is not None:
            if sample.nitrate_n > WATER_QUALITY_STANDARDS["nitrate_n"]["drinking_water"]:
                issues.append(f"Nitrate ({sample.nitrate_n} mg/L) exceeds drinking water standard (10 mg/L)")
                status = "Poor"
            elif sample.nitrate_n > WATER_QUALITY_STANDARDS["nitrate_n"]["aquatic_life"]:
                issues.append(f"Nitrate ({sample.nitrate_n} mg/L) elevated for aquatic life")
                if status != "Poor": status = "Fair"

        # Check phosphorus
        if sample.total_phosphorus is not None:
            threshold = (WATER_QUALITY_STANDARDS["total_phosphorus"]["lakes"]
                        if sample.water_body_type in [WaterBodyType.LAKE, WaterBodyType.POND]
                        else WATER_QUALITY_STANDARDS["total_phosphorus"]["streams"])
            if sample.total_phosphorus > threshold:
                issues.append(f"Phosphorus ({sample.total_phosphorus} mg/L) exceeds threshold ({threshold} mg/L)")
                if status != "Poor": status = "Fair"

        # Check dissolved oxygen
        if sample.dissolved_oxygen is not None:
            if sample.dissolved_oxygen < WATER_QUALITY_STANDARDS["dissolved_oxygen"]["minimum"]:
                issues.append(f"Dissolved oxygen ({sample.dissolved_oxygen} mg/L) below minimum for aquatic life")
                status = "Poor"
            elif sample.dissolved_oxygen < WATER_QUALITY_STANDARDS["dissolved_oxygen"]["good"]:
                if status not in ["Poor", "Fair"]: status = "Fair"

        # Check pH
        if sample.ph is not None:
            if sample.ph < WATER_QUALITY_STANDARDS["ph"]["minimum"] or sample.ph > WATER_QUALITY_STANDARDS["ph"]["maximum"]:
                issues.append(f"pH ({sample.ph}) outside acceptable range (6.5-9.0)")
                status = "Poor"

        # Check turbidity
        if sample.turbidity_ntu is not None:
            if sample.turbidity_ntu > WATER_QUALITY_STANDARDS["turbidity"]["aquatic_life"]:
                issues.append(f"Turbidity ({sample.turbidity_ntu} NTU) elevated")
                if status not in ["Poor"]: status = "Fair"

        # Check for excellent status
        if not issues:
            if (sample.nitrate_n is not None and
                sample.nitrate_n <= WATER_QUALITY_STANDARDS["nitrate_n"]["excellent"] and
                sample.dissolved_oxygen is not None and
                sample.dissolved_oxygen >= WATER_QUALITY_STANDARDS["dissolved_oxygen"]["excellent"]):
                status = "Excellent"

        return {
            "overall_status": status,
            "issues_found": issues,
            "meets_drinking_water_standards": (
                sample.nitrate_n is None or
                sample.nitrate_n <= WATER_QUALITY_STANDARDS["nitrate_n"]["drinking_water"]
            ),
            "supports_aquatic_life": status in ["Good", "Excellent"],
            "recommendations": self._generate_water_quality_recommendations(issues, sample)
        }

    def _generate_water_quality_recommendations(
        self,
        issues: List[str],
        sample: WaterSample
    ) -> List[str]:
        """Generate recommendations based on water quality issues"""
        recommendations = []

        if any("Nitrate" in issue for issue in issues):
            recommendations.append(
                "Implement nitrogen best management practices: split applications, "
                "cover crops, buffer strips, and controlled drainage."
            )

        if any("Phosphorus" in issue for issue in issues):
            recommendations.append(
                "Address phosphorus loading through: soil testing before application, "
                "reduced tillage, buffer strips, and avoiding application near waterways."
            )

        if any("oxygen" in issue.lower() for issue in issues):
            recommendations.append(
                "Low dissolved oxygen may indicate nutrient enrichment (eutrophication). "
                "Consider watershed-level nutrient reduction strategies."
            )

        if any("Turbidity" in issue for issue in issues):
            recommendations.append(
                "High turbidity indicates sediment loading. Implement erosion control: "
                "cover crops, residue management, grass waterways, and terraces."
            )

        if not recommendations:
            recommendations.append(
                "Water quality is acceptable. Continue monitoring and documenting "
                "for grant compliance and trend analysis."
            )

        return recommendations

    def get_water_quality_trends(
        self,
        location_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Analyze water quality trends over time for a location"""

        location_samples = [
            s for s in self.water_samples
            if s.location_id == location_id
            and start_date <= s.sample_date.date() <= end_date
        ]

        if not location_samples:
            return {
                "location_id": location_id,
                "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
                "sample_count": 0,
                "message": "No samples found for this period"
            }

        # Sort by date
        location_samples.sort(key=lambda s: s.sample_date)

        # Calculate statistics
        def calc_stats(values):
            if not values:
                return None
            clean_values = [v for v in values if v is not None]
            if not clean_values:
                return None
            return {
                "min": round(min(clean_values), 3),
                "max": round(max(clean_values), 3),
                "mean": round(sum(clean_values) / len(clean_values), 3),
                "count": len(clean_values),
                "trend": "improving" if clean_values[-1] < clean_values[0] else
                        "declining" if clean_values[-1] > clean_values[0] else "stable"
            }

        return {
            "location_id": location_id,
            "location_name": location_samples[0].location_name,
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "sample_count": len(location_samples),
            "parameters": {
                "nitrate_n": calc_stats([s.nitrate_n for s in location_samples]),
                "total_phosphorus": calc_stats([s.total_phosphorus for s in location_samples]),
                "dissolved_oxygen": calc_stats([s.dissolved_oxygen for s in location_samples]),
                "turbidity": calc_stats([s.turbidity_ntu for s in location_samples]),
                "ph": calc_stats([s.ph for s in location_samples])
            },
            "first_sample_date": location_samples[0].sample_date.isoformat(),
            "last_sample_date": location_samples[-1].sample_date.isoformat()
        }

    # =========================================================================
    # BUFFER STRIP MANAGEMENT
    # =========================================================================

    def add_buffer_strip(self, buffer: BufferStrip) -> Dict:
        """Add a conservation buffer strip"""
        self.buffer_strips.append(buffer)

        # Calculate area and effectiveness
        area_acres = (buffer.length_feet * buffer.average_width_feet) / 43560
        effectiveness = BUFFER_EFFECTIVENESS.get(buffer.buffer_type, {})

        return {
            "success": True,
            "buffer_id": buffer.buffer_id,
            "area_acres": round(area_acres, 2),
            "effectiveness": {
                "sediment_reduction": f"{effectiveness.get('sediment', 0) * 100:.0f}%",
                "nitrogen_reduction": f"{effectiveness.get('nitrogen', 0) * 100:.0f}%",
                "phosphorus_reduction": f"{effectiveness.get('phosphorus', 0) * 100:.0f}%"
            },
            "nrcs_practice": buffer.nrcs_practice_code,
            "message": f"Buffer strip added: {buffer.buffer_type.value}"
        }

    def calculate_buffer_impact(self, field_id: str) -> Dict:
        """Calculate total conservation impact of buffers for a field"""

        field_buffers = [b for b in self.buffer_strips if b.field_id == field_id]

        if not field_buffers:
            return {
                "field_id": field_id,
                "buffer_count": 0,
                "message": "No buffer strips recorded for this field"
            }

        total_area = 0
        total_sediment_reduction = 0
        total_n_reduction = 0
        total_p_reduction = 0

        buffer_details = []

        for buffer in field_buffers:
            area = (buffer.length_feet * buffer.average_width_feet) / 43560
            effectiveness = BUFFER_EFFECTIVENESS.get(buffer.buffer_type, {})

            # Assume 10 tons/acre base erosion, 50 lbs N and 10 lbs P potential loss
            sediment_prevented = area * 10 * effectiveness.get('sediment', 0)
            n_prevented = area * 50 * effectiveness.get('nitrogen', 0)
            p_prevented = area * 10 * effectiveness.get('phosphorus', 0)

            total_area += area
            total_sediment_reduction += sediment_prevented
            total_n_reduction += n_prevented
            total_p_reduction += p_prevented

            buffer_details.append({
                "buffer_id": buffer.buffer_id,
                "type": buffer.buffer_type.value,
                "area_acres": round(area, 2),
                "sediment_tons_prevented": round(sediment_prevented, 1),
                "nitrogen_lbs_prevented": round(n_prevented, 1),
                "phosphorus_lbs_prevented": round(p_prevented, 1)
            })

        return {
            "field_id": field_id,
            "buffer_count": len(field_buffers),
            "total_buffer_area_acres": round(total_area, 2),
            "annual_impact_estimates": {
                "sediment_prevented_tons": round(total_sediment_reduction, 1),
                "nitrogen_prevented_lbs": round(total_n_reduction, 1),
                "phosphorus_prevented_lbs": round(total_p_reduction, 1)
            },
            "buffer_details": buffer_details,
            "grant_value": {
                "sediment_at_50_per_ton": round(total_sediment_reduction * 50, 2),
                "nitrogen_at_5_per_lb": round(total_n_reduction * 5, 2),
                "phosphorus_at_10_per_lb": round(total_p_reduction * 10, 2),
                "total_environmental_value": round(
                    total_sediment_reduction * 50 +
                    total_n_reduction * 5 +
                    total_p_reduction * 10, 2
                )
            }
        }

    # =========================================================================
    # TILE DRAINAGE MANAGEMENT
    # =========================================================================

    def add_tile_system(self, system: TileDrainageSystem) -> Dict:
        """Add tile drainage system information"""
        self.tile_systems.append(system)

        # Calculate environmental impact factors
        base_n_loss = system.total_acres_drained * 25  # Base 25 lbs/acre N loss through tiles

        reduction = 0
        practices = []

        if system.has_controlled_drainage:
            reduction += 0.30  # 30% N reduction
            practices.append("Controlled drainage (-30% N)")

        if system.has_saturated_buffer:
            reduction += 0.40  # 40% N reduction
            practices.append("Saturated buffer (-40% N)")

        if system.has_bioreactor:
            reduction += 0.45  # 45% N reduction
            practices.append("Bioreactor (-45% N)")

        n_loss_with_practices = base_n_loss * (1 - min(reduction, 0.80))

        return {
            "success": True,
            "system_id": system.system_id,
            "acres_drained": system.total_acres_drained,
            "conservation_practices": practices,
            "estimated_n_loss": {
                "without_practices_lbs": round(base_n_loss, 0),
                "with_practices_lbs": round(n_loss_with_practices, 0),
                "reduction_lbs": round(base_n_loss - n_loss_with_practices, 0),
                "reduction_percent": round(reduction * 100, 0)
            },
            "message": "Tile drainage system recorded"
        }

    # =========================================================================
    # 4R NUTRIENT STEWARDSHIP
    # =========================================================================

    def assess_4r_compliance(self, field_id: str, crop_year: int) -> Dict:
        """
        Assess compliance with 4R Nutrient Stewardship principles.
        Essential for many conservation and sustainability grants.
        """

        field_apps = [a for a in self.nutrient_applications
                     if a.field_id == field_id and a.date.year == crop_year]

        if not field_apps:
            return {
                "field_id": field_id,
                "crop_year": crop_year,
                "message": "No nutrient applications recorded for assessment"
            }

        scores = {
            "right_source": 0,
            "right_rate": 0,
            "right_time": 0,
            "right_place": 0
        }

        max_score = len(field_apps) * 25  # 25 points per application per R

        for app in field_apps:
            # Right Source scoring
            if app.inhibitor_used:
                scores["right_source"] += 25
            elif app.source in [NutrientSource.COMMERCIAL_FERTILIZER, NutrientSource.MANURE]:
                scores["right_source"] += 20
            else:
                scores["right_source"] += 15

            # Right Rate scoring (assume soil test based if recorded)
            if app.nitrogen_lbs_acre <= 200:  # Reasonable rate
                scores["right_rate"] += 25
            elif app.nitrogen_lbs_acre <= 250:
                scores["right_rate"] += 20
            else:
                scores["right_rate"] += 10

            # Right Time scoring
            month = app.date.month
            if month in [4, 5, 6]:  # Spring/early summer
                scores["right_time"] += 25
            elif month in [3, 7]:  # Early spring/mid-summer
                scores["right_time"] += 20
            else:  # Fall application
                scores["right_time"] += 10

            # Right Place scoring
            if app.incorporated or app.application_method in ["injected", "banded"]:
                scores["right_place"] += 25
            elif app.application_method == "broadcast":
                scores["right_place"] += 15
            else:
                scores["right_place"] += 20

        # Calculate percentages
        def calc_percent(score):
            return round(score / max_score * 100, 0) if max_score > 0 else 0

        overall_score = sum(scores.values()) / (max_score * 4) * 100 if max_score > 0 else 0

        # Determine grade
        if overall_score >= 90:
            grade = "A"
            status = "Excellent - Fully compliant with 4R principles"
        elif overall_score >= 80:
            grade = "B"
            status = "Good - Meets most 4R criteria"
        elif overall_score >= 70:
            grade = "C"
            status = "Fair - Room for improvement"
        elif overall_score >= 60:
            grade = "D"
            status = "Needs Improvement"
        else:
            grade = "F"
            status = "Poor - Significant improvements needed"

        return {
            "field_id": field_id,
            "crop_year": crop_year,
            "application_count": len(field_apps),
            "scores": {
                "right_source": {
                    "score_percent": calc_percent(scores["right_source"]),
                    "description": FOUR_R_CRITERIA["right_source"]["description"],
                    "best_practices": FOUR_R_CRITERIA["right_source"]["best_practices"]
                },
                "right_rate": {
                    "score_percent": calc_percent(scores["right_rate"]),
                    "description": FOUR_R_CRITERIA["right_rate"]["description"],
                    "best_practices": FOUR_R_CRITERIA["right_rate"]["best_practices"]
                },
                "right_time": {
                    "score_percent": calc_percent(scores["right_time"]),
                    "description": FOUR_R_CRITERIA["right_time"]["description"],
                    "best_practices": FOUR_R_CRITERIA["right_time"]["best_practices"]
                },
                "right_place": {
                    "score_percent": calc_percent(scores["right_place"]),
                    "description": FOUR_R_CRITERIA["right_place"]["description"],
                    "best_practices": FOUR_R_CRITERIA["right_place"]["best_practices"]
                }
            },
            "overall_score": round(overall_score, 0),
            "grade": grade,
            "status": status,
            "certification_eligible": overall_score >= 80,
            "grant_documentation": {
                "4r_certified": overall_score >= 80,
                "score_breakdown": {
                    "right_source": calc_percent(scores["right_source"]),
                    "right_rate": calc_percent(scores["right_rate"]),
                    "right_time": calc_percent(scores["right_time"]),
                    "right_place": calc_percent(scores["right_place"])
                }
            }
        }

    # =========================================================================
    # WATERSHED ANALYSIS
    # =========================================================================

    def analyze_watershed_impact(
        self,
        field_ids: List[str],
        crop_year: int,
        watershed_name: str,
        total_watershed_acres: float
    ) -> Dict:
        """
        Analyze cumulative watershed impact from multiple fields.
        Critical for conservation district and watershed grant applications.
        """

        total_n_applied = 0
        total_p_applied = 0
        total_field_acres = 0
        field_details = []

        for field_id in field_ids:
            field_apps = [a for a in self.nutrient_applications
                        if a.field_id == field_id and a.date.year == crop_year]

            n_applied = sum(a.nitrogen_lbs_acre for a in field_apps)
            p_applied = sum(a.phosphorus_lbs_acre for a in field_apps)

            # Get buffer impact for field
            buffer_impact = self.calculate_buffer_impact(field_id)

            field_acres = 100  # Placeholder - would come from field database
            total_field_acres += field_acres
            total_n_applied += n_applied * field_acres
            total_p_applied += p_applied * field_acres

            field_details.append({
                "field_id": field_id,
                "n_applied_lbs_acre": n_applied,
                "p_applied_lbs_acre": p_applied,
                "buffer_count": buffer_impact.get("buffer_count", 0)
            })

        # Estimate watershed loading (simplified model)
        # Assume 15% of applied N and 5% of applied P reaches watershed
        estimated_n_loading = total_n_applied * 0.15
        estimated_p_loading = total_p_applied * 0.05

        # Per-acre contribution
        n_per_acre = estimated_n_loading / total_watershed_acres if total_watershed_acres > 0 else 0
        p_per_acre = estimated_p_loading / total_watershed_acres if total_watershed_acres > 0 else 0

        return {
            "watershed_name": watershed_name,
            "crop_year": crop_year,
            "watershed_total_acres": total_watershed_acres,
            "fields_analyzed": len(field_ids),
            "field_acres_in_watershed": total_field_acres,
            "percent_of_watershed": round(total_field_acres / total_watershed_acres * 100, 1),
            "total_nutrients_applied": {
                "nitrogen_lbs": round(total_n_applied, 0),
                "phosphorus_lbs": round(total_p_applied, 0)
            },
            "estimated_watershed_loading": {
                "nitrogen_lbs": round(estimated_n_loading, 0),
                "phosphorus_lbs": round(estimated_p_loading, 0),
                "nitrogen_lbs_per_watershed_acre": round(n_per_acre, 2),
                "phosphorus_lbs_per_watershed_acre": round(p_per_acre, 3)
            },
            "loading_assessment": {
                "nitrogen": "High" if n_per_acre > 10 else "Moderate" if n_per_acre > 5 else "Low",
                "phosphorus": "High" if p_per_acre > 0.5 else "Moderate" if p_per_acre > 0.2 else "Low"
            },
            "field_details": field_details,
            "reduction_targets": {
                "nitrogen_20_percent_reduction": round(estimated_n_loading * 0.20, 0),
                "phosphorus_20_percent_reduction": round(estimated_p_loading * 0.20, 0)
            },
            "grant_metrics": {
                "baseline_n_loading": round(estimated_n_loading, 0),
                "baseline_p_loading": round(estimated_p_loading, 0),
                "target_n_reduction": "20% minimum recommended",
                "target_p_reduction": "20% minimum recommended",
                "monitoring_recommended": True
            }
        }

    # =========================================================================
    # GRANT REPORTING
    # =========================================================================

    def generate_water_quality_grant_report(
        self,
        field_ids: List[str],
        crop_year: int,
        grant_program: str
    ) -> Dict:
        """
        Generate comprehensive water quality report for grant applications.
        Includes all metrics commonly required by NRCS, EPA, and conservation grants.
        """

        report_data = {
            "report_title": f"Water Quality & Nutrient Management Report - {crop_year}",
            "grant_program": grant_program,
            "generated_date": datetime.now().isoformat(),
            "fields_included": field_ids,
            "sections": {}
        }

        # Section 1: Nutrient Management Summary
        total_apps = []
        for field_id in field_ids:
            apps = [a for a in self.nutrient_applications
                   if a.field_id == field_id and a.date.year == crop_year]
            total_apps.extend(apps)

        report_data["sections"]["nutrient_management"] = {
            "total_applications": len(total_apps),
            "total_nitrogen_lbs": round(sum(a.nitrogen_lbs_acre for a in total_apps), 0),
            "total_phosphorus_lbs": round(sum(a.phosphorus_lbs_acre for a in total_apps), 0),
            "applications_with_inhibitors": len([a for a in total_apps if a.inhibitor_used]),
            "applications_incorporated": len([a for a in total_apps if a.incorporated])
        }

        # Section 2: Conservation Practices
        all_buffers = []
        for field_id in field_ids:
            buffers = [b for b in self.buffer_strips if b.field_id == field_id]
            all_buffers.extend(buffers)

        buffer_area = sum(
            (b.length_feet * b.average_width_feet) / 43560
            for b in all_buffers
        )

        report_data["sections"]["conservation_practices"] = {
            "buffer_strips_count": len(all_buffers),
            "buffer_area_acres": round(buffer_area, 2),
            "buffer_types": list(set(b.buffer_type.value for b in all_buffers)),
            "nrcs_practice_codes": list(set(b.nrcs_practice_code for b in all_buffers))
        }

        # Section 3: Water Quality Monitoring
        all_samples = []
        for loc_id in self.monitoring_locations:
            loc_samples = [s for s in self.water_samples
                         if s.location_id == loc_id and s.sample_date.year == crop_year]
            all_samples.extend(loc_samples)

        report_data["sections"]["water_quality_monitoring"] = {
            "monitoring_locations": len(self.monitoring_locations),
            "samples_collected": len(all_samples),
            "parameters_monitored": [
                "Nitrate-N", "Total Phosphorus", "Dissolved Oxygen",
                "pH", "Turbidity", "Conductivity"
            ]
        }

        # Section 4: 4R Compliance Summary
        compliance_scores = []
        for field_id in field_ids:
            assessment = self.assess_4r_compliance(field_id, crop_year)
            if "overall_score" in assessment:
                compliance_scores.append(assessment["overall_score"])

        avg_4r_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0

        report_data["sections"]["4r_compliance"] = {
            "fields_assessed": len(compliance_scores),
            "average_score": round(avg_4r_score, 0),
            "fields_certified": len([s for s in compliance_scores if s >= 80]),
            "overall_status": "Compliant" if avg_4r_score >= 80 else "Needs Improvement"
        }

        # Section 5: Environmental Impact Summary
        report_data["sections"]["environmental_impact"] = {
            "estimated_n_reduction_from_practices": "Calculate based on buffer effectiveness",
            "estimated_p_reduction_from_practices": "Calculate based on buffer effectiveness",
            "sediment_reduction_tons": "Calculate based on conservation practices",
            "water_quality_improvement": "Document trend data"
        }

        # Grant-specific metrics
        report_data["grant_compliance_metrics"] = {
            "nutrient_management_plan": len(total_apps) > 0,
            "water_quality_monitoring": len(all_samples) > 0,
            "conservation_buffers": len(all_buffers) > 0,
            "4r_stewardship": avg_4r_score >= 80,
            "documentation_complete": True
        }

        return report_data


# Create singleton instance
water_quality_service = WaterQualityService()
