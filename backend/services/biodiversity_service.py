"""
Biodiversity & Pollinator Impact Service
Comprehensive tracking of wildlife habitat, pollinator health, and ecosystem services.

Features:
- Pollinator habitat assessment and scoring
- Beneficial insect population tracking
- Wildlife habitat evaluation (WHIP/CRP scoring)
- Integrated Pest Management (IPM) scoring
- Pesticide risk assessment for pollinators
- Native species planting recommendations
- Habitat connectivity analysis
- Ecosystem services valuation
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class HabitatType(str, Enum):
    POLLINATOR_STRIP = "pollinator_strip"
    NATIVE_PRAIRIE = "native_prairie"
    WETLAND = "wetland"
    RIPARIAN = "riparian"
    WINDBREAK = "windbreak"
    FIELD_BORDER = "field_border"
    COVER_CROP = "cover_crop"
    HEDGEROW = "hedgerow"
    WOODLAND = "woodland"
    GRASSLAND = "grassland"
    WILDFLOWER_MEADOW = "wildflower_meadow"
    INSECTARY_STRIP = "insectary_strip"


class PollinatorGroup(str, Enum):
    HONEY_BEES = "honey_bees"
    NATIVE_BEES = "native_bees"
    BUMBLEBEES = "bumblebees"
    BUTTERFLIES = "butterflies"
    MOTHS = "moths"
    HOVERFLIES = "hoverflies"
    BEETLES = "beetles"
    WASPS = "wasps"


class BeneficialInsectType(str, Enum):
    LADY_BEETLES = "lady_beetles"
    LACEWINGS = "lacewings"
    GROUND_BEETLES = "ground_beetles"
    PARASITIC_WASPS = "parasitic_wasps"
    PREDATORY_MITES = "predatory_mites"
    SPIDERS = "spiders"
    SYRPHID_FLIES = "syrphid_flies"
    MINUTE_PIRATE_BUGS = "minute_pirate_bugs"
    DAMSEL_BUGS = "damsel_bugs"
    ASSASSIN_BUGS = "assassin_bugs"


class WildlifeGroup(str, Enum):
    SONGBIRDS = "songbirds"
    WATERFOWL = "waterfowl"
    RAPTORS = "raptors"
    GAMEBIRDS = "gamebirds"
    DEER = "deer"
    SMALL_MAMMALS = "small_mammals"
    AMPHIBIANS = "amphibians"
    REPTILES = "reptiles"


class PesticideRiskCategory(str, Enum):
    HIGHLY_TOXIC = "highly_toxic"
    MODERATELY_TOXIC = "moderately_toxic"
    SLIGHTLY_TOXIC = "slightly_toxic"
    PRACTICALLY_NON_TOXIC = "practically_non_toxic"


# Pollinator toxicity data for common pesticides (EPA acute toxicity ratings)
# LD50 values in μg/bee - lower = more toxic
PESTICIDE_POLLINATOR_TOXICITY = {
    # Highly toxic (LD50 < 2 μg/bee)
    "chlorpyrifos": {"ld50": 0.059, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 7},
    "cyfluthrin": {"ld50": 0.002, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 3},
    "lambda_cyhalothrin": {"ld50": 0.038, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 3},
    "bifenthrin": {"ld50": 0.015, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 7},
    "permethrin": {"ld50": 0.024, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 3},
    "carbaryl": {"ld50": 1.0, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 3},
    "imidacloprid": {"ld50": 0.004, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 14},
    "clothianidin": {"ld50": 0.003, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 14},
    "thiamethoxam": {"ld50": 0.005, "category": PesticideRiskCategory.HIGHLY_TOXIC, "residual_days": 14},

    # Moderately toxic (LD50 2-11 μg/bee)
    "dimethoate": {"ld50": 2.0, "category": PesticideRiskCategory.MODERATELY_TOXIC, "residual_days": 5},
    "malathion": {"ld50": 2.5, "category": PesticideRiskCategory.MODERATELY_TOXIC, "residual_days": 3},
    "acephate": {"ld50": 4.0, "category": PesticideRiskCategory.MODERATELY_TOXIC, "residual_days": 3},

    # Slightly toxic (LD50 11-100 μg/bee)
    "spinosad": {"ld50": 15.0, "category": PesticideRiskCategory.SLIGHTLY_TOXIC, "residual_days": 1},
    "indoxacarb": {"ld50": 52.0, "category": PesticideRiskCategory.SLIGHTLY_TOXIC, "residual_days": 2},

    # Practically non-toxic (LD50 > 100 μg/bee)
    "bt_kurstaki": {"ld50": 1000.0, "category": PesticideRiskCategory.PRACTICALLY_NON_TOXIC, "residual_days": 0},
    "neem": {"ld50": 500.0, "category": PesticideRiskCategory.PRACTICALLY_NON_TOXIC, "residual_days": 0},
    "kaolin_clay": {"ld50": 10000.0, "category": PesticideRiskCategory.PRACTICALLY_NON_TOXIC, "residual_days": 0},
    "copper": {"ld50": 200.0, "category": PesticideRiskCategory.PRACTICALLY_NON_TOXIC, "residual_days": 0},
    "sulfur": {"ld50": 500.0, "category": PesticideRiskCategory.PRACTICALLY_NON_TOXIC, "residual_days": 0}
}

# Habitat value scores (0-100) for different wildlife groups
HABITAT_VALUES = {
    HabitatType.POLLINATOR_STRIP: {
        "pollinators": 95,
        "beneficial_insects": 85,
        "songbirds": 60,
        "small_mammals": 40
    },
    HabitatType.NATIVE_PRAIRIE: {
        "pollinators": 90,
        "beneficial_insects": 90,
        "songbirds": 85,
        "gamebirds": 75,
        "small_mammals": 70,
        "deer": 50
    },
    HabitatType.WETLAND: {
        "pollinators": 40,
        "waterfowl": 95,
        "amphibians": 95,
        "beneficial_insects": 60,
        "songbirds": 70
    },
    HabitatType.RIPARIAN: {
        "pollinators": 70,
        "songbirds": 85,
        "amphibians": 80,
        "beneficial_insects": 75,
        "small_mammals": 65
    },
    HabitatType.WINDBREAK: {
        "pollinators": 50,
        "songbirds": 90,
        "raptors": 70,
        "small_mammals": 75,
        "deer": 60
    },
    HabitatType.FIELD_BORDER: {
        "pollinators": 65,
        "beneficial_insects": 80,
        "songbirds": 55,
        "gamebirds": 60
    },
    HabitatType.COVER_CROP: {
        "pollinators": 50,
        "beneficial_insects": 70,
        "songbirds": 40,
        "small_mammals": 30
    },
    HabitatType.HEDGEROW: {
        "pollinators": 75,
        "songbirds": 85,
        "beneficial_insects": 80,
        "small_mammals": 70
    },
    HabitatType.WOODLAND: {
        "pollinators": 45,
        "songbirds": 90,
        "raptors": 85,
        "deer": 80,
        "small_mammals": 85
    },
    HabitatType.WILDFLOWER_MEADOW: {
        "pollinators": 100,
        "beneficial_insects": 85,
        "butterflies": 95,
        "songbirds": 70
    },
    HabitatType.INSECTARY_STRIP: {
        "pollinators": 85,
        "beneficial_insects": 95,
        "songbirds": 45
    }
}

# Native plant recommendations by region and habitat type
NATIVE_PLANT_RECOMMENDATIONS = {
    "midwest": {
        "pollinator_early_season": [
            {"name": "Wild Plum (Prunus americana)", "bloom": "April", "pollinators": ["native_bees", "butterflies"]},
            {"name": "Golden Alexander (Zizia aurea)", "bloom": "April-June", "pollinators": ["native_bees", "butterflies"]},
            {"name": "Wild Hyacinth (Camassia scilloides)", "bloom": "April-May", "pollinators": ["native_bees"]}
        ],
        "pollinator_mid_season": [
            {"name": "Purple Coneflower (Echinacea purpurea)", "bloom": "June-Aug", "pollinators": ["bumblebees", "butterflies"]},
            {"name": "Wild Bergamot (Monarda fistulosa)", "bloom": "July-Sept", "pollinators": ["native_bees", "butterflies", "hummingbirds"]},
            {"name": "Black-eyed Susan (Rudbeckia hirta)", "bloom": "June-Oct", "pollinators": ["native_bees", "butterflies"]},
            {"name": "Prairie Blazing Star (Liatris pycnostachya)", "bloom": "July-Aug", "pollinators": ["butterflies", "bumblebees"]},
            {"name": "Milkweed (Asclepias spp.)", "bloom": "June-Aug", "pollinators": ["monarch butterflies", "native_bees"]}
        ],
        "pollinator_late_season": [
            {"name": "New England Aster (Symphyotrichum novae-angliae)", "bloom": "Aug-Oct", "pollinators": ["native_bees", "butterflies"]},
            {"name": "Goldenrod (Solidago spp.)", "bloom": "Aug-Oct", "pollinators": ["native_bees", "butterflies"]},
            {"name": "Stiff Goldenrod (Solidago rigida)", "bloom": "Aug-Oct", "pollinators": ["native_bees"]}
        ],
        "beneficial_insect_plants": [
            {"name": "Yarrow (Achillea millefolium)", "benefit": "Attracts parasitic wasps, lady beetles"},
            {"name": "Sweet Fennel (Foeniculum vulgare)", "benefit": "Attracts lacewings, parasitic wasps"},
            {"name": "Buckwheat (Fagopyrum esculentum)", "benefit": "Attracts minute pirate bugs, parasitic wasps"},
            {"name": "Crimson Clover (Trifolium incarnatum)", "benefit": "Attracts ground beetles, lady beetles"}
        ]
    },
    "southeast": {
        "pollinator_early_season": [
            {"name": "Redbud (Cercis canadensis)", "bloom": "March-April", "pollinators": ["native_bees"]},
            {"name": "Wild Blue Phlox (Phlox divaricata)", "bloom": "April-May", "pollinators": ["butterflies"]}
        ],
        "pollinator_mid_season": [
            {"name": "Butterfly Weed (Asclepias tuberosa)", "bloom": "June-Aug", "pollinators": ["butterflies", "native_bees"]},
            {"name": "Coreopsis (Coreopsis spp.)", "bloom": "May-Sept", "pollinators": ["native_bees", "butterflies"]}
        ]
    }
}

# IPM scoring criteria
IPM_SCORING_CRITERIA = {
    "scouting": {
        "max_points": 20,
        "criteria": {
            "regular_scouting": 10,  # Weekly or biweekly field scouting
            "documented_records": 5,  # Written scouting reports
            "threshold_based_decisions": 5  # Treatment decisions based on thresholds
        }
    },
    "cultural_practices": {
        "max_points": 20,
        "criteria": {
            "crop_rotation": 5,
            "cover_crops": 5,
            "resistant_varieties": 5,
            "sanitation": 5
        }
    },
    "biological_control": {
        "max_points": 20,
        "criteria": {
            "habitat_for_beneficials": 10,
            "conservation_biological_control": 5,
            "augmentative_releases": 5
        }
    },
    "chemical_management": {
        "max_points": 20,
        "criteria": {
            "reduced_risk_products": 5,
            "spot_treatments": 5,
            "proper_timing": 5,
            "resistance_management": 5
        }
    },
    "pollinator_protection": {
        "max_points": 20,
        "criteria": {
            "avoid_bloom_applications": 8,
            "use_bee_safe_products": 5,
            "time_of_day_applications": 4,
            "notify_beekeepers": 3
        }
    }
}


@dataclass
class HabitatArea:
    """Record of habitat area on farm"""
    habitat_id: str
    field_id: str
    habitat_type: HabitatType
    area_acres: float
    date_established: date
    plant_species: List[str]
    nrcs_practice_code: str  # e.g., "CP42" for pollinator habitat
    management_notes: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class PollinatorObservation:
    """Record of pollinator observation"""
    observation_id: str
    location_id: str
    observation_date: datetime
    pollinator_group: PollinatorGroup
    estimated_count: int
    plant_species_visited: str
    weather_conditions: str
    observer: str
    notes: str = ""


@dataclass
class BeneficialInsectSurvey:
    """Record of beneficial insect survey"""
    survey_id: str
    field_id: str
    survey_date: datetime
    survey_method: str  # sticky trap, sweep net, visual, pitfall trap
    insect_type: BeneficialInsectType
    count: int
    crop_stage: str
    notes: str = ""


@dataclass
class PesticideApplication:
    """Record of pesticide application for pollinator risk assessment"""
    application_id: str
    field_id: str
    application_date: datetime
    product_name: str
    active_ingredient: str
    rate_oz_acre: float
    application_method: str  # foliar, soil, seed treatment
    time_of_day: str  # early morning, midday, evening, night
    blooming_crops_nearby: bool
    pollinator_precautions: List[str]
    weather_conditions: str


@dataclass
class WildlifeObservation:
    """Record of wildlife observation"""
    observation_id: str
    location_id: str
    observation_date: datetime
    wildlife_group: WildlifeGroup
    species: str
    count: int
    behavior: str  # feeding, nesting, roosting, traveling
    habitat_type: HabitatType
    notes: str = ""


class BiodiversityService:
    """
    Comprehensive biodiversity and pollinator impact tracking service.
    Supports NRCS conservation programs, pollinator protection certifications,
    and grant compliance for wildlife/habitat programs.
    """

    def __init__(self):
        self.habitat_areas: List[HabitatArea] = []
        self.pollinator_observations: List[PollinatorObservation] = []
        self.beneficial_surveys: List[BeneficialInsectSurvey] = []
        self.pesticide_applications: List[PesticideApplication] = []
        self.wildlife_observations: List[WildlifeObservation] = []

    # =========================================================================
    # HABITAT MANAGEMENT
    # =========================================================================

    def add_habitat_area(self, habitat: HabitatArea) -> Dict:
        """Add a habitat area to the farm"""
        self.habitat_areas.append(habitat)

        # Calculate habitat value
        habitat_value = HABITAT_VALUES.get(habitat.habitat_type, {})

        return {
            "success": True,
            "habitat_id": habitat.habitat_id,
            "type": habitat.habitat_type.value,
            "area_acres": habitat.area_acres,
            "nrcs_practice": habitat.nrcs_practice_code,
            "habitat_values": habitat_value,
            "plant_species_count": len(habitat.plant_species),
            "message": f"Habitat area '{habitat.habitat_type.value}' added successfully"
        }

    def calculate_farm_habitat_score(self, total_farm_acres: float) -> Dict:
        """
        Calculate comprehensive habitat score for the farm.
        Used for conservation program eligibility and grant applications.
        """

        if not self.habitat_areas:
            return {
                "total_farm_acres": total_farm_acres,
                "habitat_acres": 0,
                "habitat_percent": 0,
                "overall_score": 0,
                "grade": "F",
                "message": "No habitat areas recorded"
            }

        total_habitat_acres = sum(h.area_acres for h in self.habitat_areas)
        habitat_percent = (total_habitat_acres / total_farm_acres * 100
                         if total_farm_acres > 0 else 0)

        # Calculate scores by wildlife group
        group_scores = {}
        for group in ["pollinators", "beneficial_insects", "songbirds",
                     "gamebirds", "waterfowl", "small_mammals", "deer"]:
            weighted_score = 0
            total_weight = 0
            for habitat in self.habitat_areas:
                values = HABITAT_VALUES.get(habitat.habitat_type, {})
                if group in values:
                    weighted_score += values[group] * habitat.area_acres
                    total_weight += habitat.area_acres
            if total_weight > 0:
                group_scores[group] = round(weighted_score / total_weight, 1)

        # Calculate overall score
        # Components: habitat percentage (30%), diversity (30%), pollinator value (40%)
        habitat_pct_score = min(100, habitat_percent * 5)  # 20% habitat = 100 score

        habitat_diversity = len(set(h.habitat_type for h in self.habitat_areas))
        diversity_score = min(100, habitat_diversity * 20)  # 5 types = 100

        pollinator_score = group_scores.get("pollinators", 0)

        overall_score = (habitat_pct_score * 0.30 +
                        diversity_score * 0.30 +
                        pollinator_score * 0.40)

        # Assign grade
        if overall_score >= 90: grade = "A"
        elif overall_score >= 80: grade = "B"
        elif overall_score >= 70: grade = "C"
        elif overall_score >= 60: grade = "D"
        else: grade = "F"

        return {
            "total_farm_acres": total_farm_acres,
            "habitat_summary": {
                "total_habitat_acres": round(total_habitat_acres, 2),
                "habitat_percent": round(habitat_percent, 2),
                "habitat_types": len(set(h.habitat_type for h in self.habitat_areas)),
                "total_habitat_areas": len(self.habitat_areas)
            },
            "habitat_breakdown": [
                {
                    "type": h.habitat_type.value,
                    "acres": h.area_acres,
                    "nrcs_practice": h.nrcs_practice_code
                }
                for h in self.habitat_areas
            ],
            "wildlife_group_scores": group_scores,
            "score_components": {
                "habitat_percentage_score": round(habitat_pct_score, 1),
                "diversity_score": round(diversity_score, 1),
                "pollinator_score": round(pollinator_score, 1)
            },
            "overall_score": round(overall_score, 1),
            "grade": grade,
            "certification_eligible": {
                "bee_friendly_farming": overall_score >= 70 and pollinator_score >= 70,
                "wildlife_habitat": habitat_percent >= 10,
                "conservation_stewardship": overall_score >= 80
            },
            "recommendations": self._generate_habitat_recommendations(
                habitat_percent, habitat_diversity, pollinator_score
            )
        }

    def _generate_habitat_recommendations(
        self,
        habitat_percent: float,
        diversity: int,
        pollinator_score: float
    ) -> List[str]:
        """Generate habitat improvement recommendations"""
        recommendations = []

        if habitat_percent < 5:
            recommendations.append(
                "Consider establishing pollinator strips or field borders to reach "
                "5% habitat target for basic conservation program eligibility."
            )
        elif habitat_percent < 10:
            recommendations.append(
                "Increase habitat to 10% of farm area for Wildlife Habitat "
                "Incentive Program (WHIP) eligibility."
            )

        if diversity < 3:
            recommendations.append(
                "Add diverse habitat types (wetlands, prairie, riparian) "
                "to support a wider range of wildlife species."
            )

        if pollinator_score < 70:
            recommendations.append(
                "Establish dedicated pollinator habitat with diverse native "
                "flowering plants that bloom spring through fall."
            )

        if not recommendations:
            recommendations.append(
                "Excellent habitat management! Consider applying for "
                "Bee Friendly Farming or Wildlife Habitat certification."
            )

        return recommendations

    def get_native_plant_recommendations(
        self,
        region: str = "midwest",
        habitat_type: str = "pollinator"
    ) -> Dict:
        """Get native plant recommendations for habitat establishment"""

        regional_plants = NATIVE_PLANT_RECOMMENDATIONS.get(region, {})

        if not regional_plants:
            return {
                "region": region,
                "message": "Region not found. Using Midwest defaults.",
                "plants": NATIVE_PLANT_RECOMMENDATIONS.get("midwest", {})
            }

        return {
            "region": region,
            "habitat_type": habitat_type,
            "early_season_plants": regional_plants.get("pollinator_early_season", []),
            "mid_season_plants": regional_plants.get("pollinator_mid_season", []),
            "late_season_plants": regional_plants.get("pollinator_late_season", []),
            "beneficial_insect_plants": regional_plants.get("beneficial_insect_plants", []),
            "planting_tips": [
                "Plant diverse species for continuous bloom from April-October",
                "Include at least 3 species per bloom period",
                "Plant in masses for better pollinator attraction",
                "Avoid cultivars with double flowers (less nectar/pollen)",
                "Include host plants for butterflies (milkweed for monarchs)"
            ],
            "establishment_timeline": {
                "year_1": "Site prep, seeding, weed control",
                "year_2": "Establishment mowing, spot weed control",
                "year_3+": "Mature habitat, minimal management"
            }
        }

    # =========================================================================
    # POLLINATOR TRACKING
    # =========================================================================

    def record_pollinator_observation(self, observation: PollinatorObservation) -> Dict:
        """Record a pollinator observation"""
        self.pollinator_observations.append(observation)

        return {
            "recorded": True,
            "observation_id": observation.observation_id,
            "date": observation.observation_date.isoformat(),
            "group": observation.pollinator_group.value,
            "count": observation.estimated_count,
            "message": "Pollinator observation recorded"
        }

    def get_pollinator_summary(
        self,
        location_id: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict:
        """Get summary of pollinator observations"""

        observations = self.pollinator_observations

        if location_id:
            observations = [o for o in observations if o.location_id == location_id]

        if year:
            observations = [o for o in observations if o.observation_date.year == year]

        if not observations:
            return {
                "total_observations": 0,
                "message": "No pollinator observations found"
            }

        # Group by pollinator type
        by_group = {}
        for obs in observations:
            group = obs.pollinator_group.value
            if group not in by_group:
                by_group[group] = {"observations": 0, "total_count": 0}
            by_group[group]["observations"] += 1
            by_group[group]["total_count"] += obs.estimated_count

        # Seasonal distribution
        by_month = {}
        for obs in observations:
            month = obs.observation_date.strftime("%B")
            by_month[month] = by_month.get(month, 0) + obs.estimated_count

        return {
            "total_observations": len(observations),
            "total_pollinators_counted": sum(o.estimated_count for o in observations),
            "by_pollinator_group": by_group,
            "seasonal_distribution": by_month,
            "observation_period": {
                "first": min(o.observation_date for o in observations).isoformat(),
                "last": max(o.observation_date for o in observations).isoformat()
            },
            "diversity_index": len(by_group),
            "most_common_group": max(by_group.keys(),
                                    key=lambda k: by_group[k]["total_count"]) if by_group else None
        }

    # =========================================================================
    # BENEFICIAL INSECT TRACKING
    # =========================================================================

    def record_beneficial_survey(self, survey: BeneficialInsectSurvey) -> Dict:
        """Record a beneficial insect survey"""
        self.beneficial_surveys.append(survey)

        return {
            "recorded": True,
            "survey_id": survey.survey_id,
            "field": survey.field_id,
            "insect_type": survey.insect_type.value,
            "count": survey.count,
            "method": survey.survey_method,
            "message": "Beneficial insect survey recorded"
        }

    def calculate_biological_control_potential(self, field_id: str) -> Dict:
        """
        Calculate biological control potential based on beneficial insect surveys.
        Useful for IPM scoring and reduced pesticide use justification.
        """

        field_surveys = [s for s in self.beneficial_surveys if s.field_id == field_id]

        if not field_surveys:
            return {
                "field_id": field_id,
                "potential_score": 0,
                "message": "No beneficial insect surveys recorded"
            }

        # Beneficial insect pest control capacity
        CONTROL_CAPACITY = {
            BeneficialInsectType.LADY_BEETLES: {"aphids": 90, "scale": 60, "mites": 40},
            BeneficialInsectType.LACEWINGS: {"aphids": 85, "mites": 70, "thrips": 60},
            BeneficialInsectType.GROUND_BEETLES: {"slugs": 70, "cutworms": 60, "weed_seeds": 80},
            BeneficialInsectType.PARASITIC_WASPS: {"caterpillars": 85, "aphids": 70, "beetles": 50},
            BeneficialInsectType.PREDATORY_MITES: {"mites": 95, "thrips": 50},
            BeneficialInsectType.SPIDERS: {"general": 60},
            BeneficialInsectType.SYRPHID_FLIES: {"aphids": 80},
            BeneficialInsectType.MINUTE_PIRATE_BUGS: {"thrips": 85, "aphids": 60, "mites": 70},
            BeneficialInsectType.DAMSEL_BUGS: {"aphids": 70, "caterpillars": 60},
            BeneficialInsectType.ASSASSIN_BUGS: {"general": 65}
        }

        # Calculate control potential by pest type
        pest_control = {}
        total_beneficials = 0

        for survey in field_surveys:
            capacity = CONTROL_CAPACITY.get(survey.insect_type, {})
            for pest, effectiveness in capacity.items():
                if pest not in pest_control:
                    pest_control[pest] = 0
                # Score based on count and effectiveness
                pest_control[pest] += (survey.count * effectiveness / 100)
            total_beneficials += survey.count

        # Calculate overall biological control score
        if total_beneficials == 0:
            bc_score = 0
        elif total_beneficials < 10:
            bc_score = 30
        elif total_beneficials < 50:
            bc_score = 60
        else:
            bc_score = 85

        # Diversity bonus
        diversity = len(set(s.insect_type for s in field_surveys))
        diversity_bonus = min(15, diversity * 3)
        bc_score = min(100, bc_score + diversity_bonus)

        return {
            "field_id": field_id,
            "surveys_recorded": len(field_surveys),
            "total_beneficials_counted": total_beneficials,
            "beneficial_diversity": diversity,
            "pest_control_capacity": {
                pest: round(score, 1)
                for pest, score in sorted(pest_control.items(),
                                         key=lambda x: x[1], reverse=True)
            },
            "biological_control_score": round(bc_score, 0),
            "assessment": (
                "Strong" if bc_score >= 70 else
                "Moderate" if bc_score >= 50 else
                "Weak" if bc_score >= 30 else "Very Low"
            ),
            "pesticide_reduction_potential": (
                "30-50% reduction possible" if bc_score >= 70 else
                "15-30% reduction possible" if bc_score >= 50 else
                "Some reduction possible" if bc_score >= 30 else
                "Build beneficial populations"
            ),
            "recommendations": [
                "Continue monitoring beneficial populations",
                "Establish insectary strips for natural enemy habitat",
                "Avoid broad-spectrum insecticides during key periods",
                "Use economic thresholds before treating"
            ] if bc_score >= 50 else [
                "Establish beneficial insect habitat",
                "Reduce broad-spectrum insecticide use",
                "Plant insectary strips with flowering plants",
                "Monitor weekly for beneficial population trends"
            ]
        }

    # =========================================================================
    # PESTICIDE RISK ASSESSMENT
    # =========================================================================

    def record_pesticide_application(self, application: PesticideApplication) -> Dict:
        """Record a pesticide application with pollinator risk assessment"""
        self.pesticide_applications.append(application)

        # Assess pollinator risk
        risk_assessment = self.assess_pollinator_risk(application)

        return {
            "recorded": True,
            "application_id": application.application_id,
            "risk_assessment": risk_assessment,
            "message": "Pesticide application recorded with risk assessment"
        }

    def assess_pollinator_risk(self, application: PesticideApplication) -> Dict:
        """Assess pollinator risk from a pesticide application"""

        # Get toxicity data
        ai_lower = application.active_ingredient.lower().replace("-", "_").replace(" ", "_")
        toxicity = PESTICIDE_POLLINATOR_TOXICITY.get(ai_lower, None)

        if not toxicity:
            return {
                "risk_level": "Unknown",
                "message": f"No toxicity data available for {application.active_ingredient}",
                "recommendation": "Consult EPA Bee Precautionary Statement on label"
            }

        base_risk_score = 0
        risk_factors = []

        # Toxicity category score
        if toxicity["category"] == PesticideRiskCategory.HIGHLY_TOXIC:
            base_risk_score = 80
            risk_factors.append("Active ingredient highly toxic to bees")
        elif toxicity["category"] == PesticideRiskCategory.MODERATELY_TOXIC:
            base_risk_score = 50
            risk_factors.append("Active ingredient moderately toxic to bees")
        elif toxicity["category"] == PesticideRiskCategory.SLIGHTLY_TOXIC:
            base_risk_score = 25
            risk_factors.append("Active ingredient slightly toxic to bees")
        else:
            base_risk_score = 5
            risk_factors.append("Active ingredient practically non-toxic to bees")

        # Application timing factor
        if application.time_of_day in ["midday", "early morning"]:
            base_risk_score += 15
            risk_factors.append("Applied during active bee foraging hours")
        elif application.time_of_day == "evening":
            base_risk_score -= 10
            risk_factors.append("Evening application reduces exposure")
        elif application.time_of_day == "night":
            base_risk_score -= 20
            risk_factors.append("Night application minimizes bee exposure")

        # Blooming crops nearby
        if application.blooming_crops_nearby:
            base_risk_score += 20
            risk_factors.append("Blooming crops/flowers present nearby")

        # Application method
        if application.application_method == "foliar":
            base_risk_score += 10
            risk_factors.append("Foliar application has higher exposure risk")
        elif application.application_method == "soil":
            base_risk_score -= 5
            risk_factors.append("Soil application reduces direct exposure")

        # Precautions taken
        for precaution in application.pollinator_precautions:
            if precaution == "notified_beekeepers":
                base_risk_score -= 5
            elif precaution == "avoided_bloom":
                base_risk_score -= 15
            elif precaution == "used_buffer":
                base_risk_score -= 10

        # Clamp score
        risk_score = max(0, min(100, base_risk_score))

        # Determine risk level
        if risk_score >= 70:
            risk_level = "High"
            action = "Avoid application or implement strict pollinator protection measures"
        elif risk_score >= 40:
            risk_level = "Moderate"
            action = "Implement pollinator protection measures before application"
        elif risk_score >= 20:
            risk_level = "Low"
            action = "Standard precautions recommended"
        else:
            risk_level = "Minimal"
            action = "Low risk to pollinators with standard practices"

        return {
            "active_ingredient": application.active_ingredient,
            "toxicity_category": toxicity["category"].value,
            "ld50_ug_bee": toxicity["ld50"],
            "residual_toxicity_days": toxicity["residual_days"],
            "risk_score": round(risk_score, 0),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommended_action": action,
            "protective_measures": [
                "Apply during evening or night hours when bees are not foraging",
                "Notify beekeepers within 2 miles at least 48 hours before application",
                "Do not apply to blooming crops or when weeds are in bloom",
                "Use drift reduction nozzles and avoid windy conditions",
                f"Wait {toxicity['residual_days']} days before allowing bee activity"
            ] if risk_score >= 40 else [
                "Follow label directions for pollinator protection",
                "Standard application practices are acceptable"
            ]
        }

    def calculate_pollinator_risk_score(
        self,
        field_id: str,
        crop_year: int
    ) -> Dict:
        """Calculate cumulative pollinator risk score for a field/year"""

        field_apps = [
            a for a in self.pesticide_applications
            if a.field_id == field_id and a.application_date.year == crop_year
        ]

        if not field_apps:
            return {
                "field_id": field_id,
                "crop_year": crop_year,
                "applications": 0,
                "cumulative_risk": 0,
                "pollinator_friendly_score": 100,
                "message": "No pesticide applications recorded"
            }

        total_risk = 0
        high_risk_apps = 0
        application_details = []

        for app in field_apps:
            risk = self.assess_pollinator_risk(app)
            total_risk += risk.get("risk_score", 0)
            if risk.get("risk_level") == "High":
                high_risk_apps += 1

            application_details.append({
                "date": app.application_date.isoformat(),
                "product": app.product_name,
                "risk_level": risk.get("risk_level"),
                "risk_score": risk.get("risk_score")
            })

        avg_risk = total_risk / len(field_apps) if field_apps else 0
        pollinator_friendly_score = max(0, 100 - avg_risk)

        return {
            "field_id": field_id,
            "crop_year": crop_year,
            "total_applications": len(field_apps),
            "high_risk_applications": high_risk_apps,
            "average_risk_score": round(avg_risk, 1),
            "cumulative_risk_score": round(total_risk, 0),
            "pollinator_friendly_score": round(pollinator_friendly_score, 0),
            "application_details": application_details,
            "certification_status": {
                "bee_friendly_eligible": pollinator_friendly_score >= 70 and high_risk_apps == 0,
                "needs_improvement": high_risk_apps > 0
            },
            "recommendations": (
                ["Current practices support pollinator health",
                 "Consider applying for Bee Friendly Farming certification"]
                if pollinator_friendly_score >= 70 and high_risk_apps == 0
                else ["Reduce use of highly toxic products",
                      "Shift applications to evening/night hours",
                      "Avoid applications during bloom periods",
                      "Establish pollinator refuges away from treated areas"]
            )
        }

    # =========================================================================
    # IPM SCORING
    # =========================================================================

    def calculate_ipm_score(
        self,
        field_id: str,
        crop_year: int,
        practices: Dict[str, bool]
    ) -> Dict:
        """
        Calculate Integrated Pest Management (IPM) score.
        Required for many conservation grants and sustainability certifications.

        practices dict should include:
        - regular_scouting, documented_records, threshold_based_decisions
        - crop_rotation, cover_crops, resistant_varieties, sanitation
        - habitat_for_beneficials, conservation_biological_control, augmentative_releases
        - reduced_risk_products, spot_treatments, proper_timing, resistance_management
        - avoid_bloom_applications, use_bee_safe_products, time_of_day_applications, notify_beekeepers
        """

        scores = {}
        total_score = 0

        for category, criteria in IPM_SCORING_CRITERIA.items():
            category_score = 0
            category_details = []

            for practice, points in criteria["criteria"].items():
                achieved = practices.get(practice, False)
                if achieved:
                    category_score += points
                    category_details.append({
                        "practice": practice.replace("_", " ").title(),
                        "points": points,
                        "achieved": True
                    })
                else:
                    category_details.append({
                        "practice": practice.replace("_", " ").title(),
                        "points": points,
                        "achieved": False
                    })

            scores[category] = {
                "score": category_score,
                "max_score": criteria["max_points"],
                "percent": round(category_score / criteria["max_points"] * 100, 0),
                "details": category_details
            }
            total_score += category_score

        max_total = sum(c["max_points"] for c in IPM_SCORING_CRITERIA.values())
        overall_percent = total_score / max_total * 100

        # Determine level
        if overall_percent >= 90:
            level = "Gold"
            status = "Exemplary IPM program"
        elif overall_percent >= 75:
            level = "Silver"
            status = "Strong IPM program"
        elif overall_percent >= 60:
            level = "Bronze"
            status = "Good IPM foundation"
        else:
            level = "Basic"
            status = "IPM program needs strengthening"

        return {
            "field_id": field_id,
            "crop_year": crop_year,
            "category_scores": scores,
            "total_score": total_score,
            "max_score": max_total,
            "overall_percent": round(overall_percent, 0),
            "ipm_level": level,
            "status": status,
            "certification_eligible": {
                "basic_ipm": overall_percent >= 50,
                "advanced_ipm": overall_percent >= 75,
                "exemplary_ipm": overall_percent >= 90
            },
            "improvement_opportunities": [
                detail["practice"]
                for cat in scores.values()
                for detail in cat["details"]
                if not detail["achieved"]
            ][:5]  # Top 5 improvements
        }

    # =========================================================================
    # WILDLIFE TRACKING
    # =========================================================================

    def record_wildlife_observation(self, observation: WildlifeObservation) -> Dict:
        """Record a wildlife observation"""
        self.wildlife_observations.append(observation)

        return {
            "recorded": True,
            "observation_id": observation.observation_id,
            "species": observation.species,
            "group": observation.wildlife_group.value,
            "count": observation.count,
            "message": "Wildlife observation recorded"
        }

    def get_wildlife_summary(
        self,
        year: Optional[int] = None
    ) -> Dict:
        """Get summary of wildlife observations"""

        observations = self.wildlife_observations
        if year:
            observations = [o for o in observations if o.observation_date.year == year]

        if not observations:
            return {"total_observations": 0, "message": "No wildlife observations found"}

        # Group by wildlife type
        by_group = {}
        by_species = {}
        by_habitat = {}

        for obs in observations:
            # By group
            group = obs.wildlife_group.value
            if group not in by_group:
                by_group[group] = {"observations": 0, "individuals": 0}
            by_group[group]["observations"] += 1
            by_group[group]["individuals"] += obs.count

            # By species
            if obs.species not in by_species:
                by_species[obs.species] = 0
            by_species[obs.species] += obs.count

            # By habitat
            habitat = obs.habitat_type.value
            if habitat not in by_habitat:
                by_habitat[habitat] = 0
            by_habitat[habitat] += obs.count

        # Calculate diversity index (simple richness)
        species_richness = len(by_species)

        return {
            "total_observations": len(observations),
            "total_individuals": sum(o.count for o in observations),
            "by_wildlife_group": by_group,
            "species_list": list(by_species.keys()),
            "species_richness": species_richness,
            "top_species": dict(sorted(by_species.items(),
                                       key=lambda x: x[1], reverse=True)[:10]),
            "observations_by_habitat": by_habitat,
            "diversity_assessment": (
                "High" if species_richness >= 20 else
                "Moderate" if species_richness >= 10 else
                "Low" if species_richness >= 5 else "Very Low"
            ),
            "grant_metrics": {
                "species_documented": species_richness,
                "wildlife_groups_present": len(by_group),
                "habitats_utilized": len(by_habitat)
            }
        }

    # =========================================================================
    # ECOSYSTEM SERVICES VALUATION
    # =========================================================================

    def calculate_ecosystem_services_value(
        self,
        total_farm_acres: float
    ) -> Dict:
        """
        Calculate economic value of ecosystem services provided by farm habitats.
        Based on published economic valuations for grant applications.
        """

        # Published ecosystem service values ($/acre/year)
        # Based on Costanza et al., USDA, and state-specific studies
        SERVICE_VALUES = {
            "pollination": {
                "description": "Crop pollination services",
                "value_per_acre": 150,  # Value to adjacent crops
                "habitat_multiplier": {
                    HabitatType.POLLINATOR_STRIP: 2.0,
                    HabitatType.WILDFLOWER_MEADOW: 2.0,
                    HabitatType.NATIVE_PRAIRIE: 1.5,
                    HabitatType.HEDGEROW: 1.2,
                    HabitatType.FIELD_BORDER: 1.0
                }
            },
            "pest_control": {
                "description": "Biological pest control",
                "value_per_acre": 75,
                "habitat_multiplier": {
                    HabitatType.INSECTARY_STRIP: 2.0,
                    HabitatType.NATIVE_PRAIRIE: 1.5,
                    HabitatType.HEDGEROW: 1.5,
                    HabitatType.FIELD_BORDER: 1.2
                }
            },
            "water_quality": {
                "description": "Water filtration and quality",
                "value_per_acre": 100,
                "habitat_multiplier": {
                    HabitatType.WETLAND: 3.0,
                    HabitatType.RIPARIAN: 2.5,
                    HabitatType.NATIVE_PRAIRIE: 1.2
                }
            },
            "carbon_sequestration": {
                "description": "Carbon storage",
                "value_per_acre": 50,  # At $20/ton CO2e
                "habitat_multiplier": {
                    HabitatType.WOODLAND: 3.0,
                    HabitatType.WETLAND: 2.5,
                    HabitatType.NATIVE_PRAIRIE: 1.5,
                    HabitatType.GRASSLAND: 1.2
                }
            },
            "wildlife_habitat": {
                "description": "Habitat for wildlife",
                "value_per_acre": 40,
                "habitat_multiplier": {
                    HabitatType.WETLAND: 2.5,
                    HabitatType.WOODLAND: 2.0,
                    HabitatType.NATIVE_PRAIRIE: 1.8,
                    HabitatType.RIPARIAN: 1.8,
                    HabitatType.WINDBREAK: 1.3
                }
            },
            "soil_health": {
                "description": "Soil conservation and health",
                "value_per_acre": 60,
                "habitat_multiplier": {
                    HabitatType.COVER_CROP: 1.5,
                    HabitatType.NATIVE_PRAIRIE: 1.5,
                    HabitatType.GRASSLAND: 1.3
                }
            },
            "recreation_aesthetic": {
                "description": "Recreation and aesthetic value",
                "value_per_acre": 30,
                "habitat_multiplier": {
                    HabitatType.WETLAND: 2.0,
                    HabitatType.WOODLAND: 2.0,
                    HabitatType.WILDFLOWER_MEADOW: 1.8,
                    HabitatType.NATIVE_PRAIRIE: 1.5
                }
            }
        }

        service_totals = {}
        total_value = 0

        for service_name, service_data in SERVICE_VALUES.items():
            service_value = 0

            for habitat in self.habitat_areas:
                multiplier = service_data["habitat_multiplier"].get(habitat.habitat_type, 0)
                habitat_value = service_data["value_per_acre"] * habitat.area_acres * multiplier
                service_value += habitat_value

            service_totals[service_name] = {
                "description": service_data["description"],
                "annual_value": round(service_value, 2)
            }
            total_value += service_value

        # Per-acre value
        total_habitat_acres = sum(h.area_acres for h in self.habitat_areas)
        value_per_habitat_acre = (total_value / total_habitat_acres
                                  if total_habitat_acres > 0 else 0)
        value_per_farm_acre = total_value / total_farm_acres if total_farm_acres > 0 else 0

        return {
            "total_farm_acres": total_farm_acres,
            "habitat_acres": round(total_habitat_acres, 2),
            "ecosystem_services": service_totals,
            "total_annual_value": round(total_value, 2),
            "value_per_habitat_acre": round(value_per_habitat_acre, 2),
            "value_per_farm_acre": round(value_per_farm_acre, 2),
            "roi_comparison": {
                "ecosystem_services_value": round(total_value, 2),
                "typical_nrcs_cost_share": round(total_habitat_acres * 300, 2),
                "payback_years": round(total_habitat_acres * 300 / total_value, 1)
                    if total_value > 0 else "N/A"
            },
            "grant_documentation": {
                "methodology": "Based on published ecosystem service valuations",
                "sources": [
                    "Costanza et al. (1997, 2014) - Ecosystem services valuation",
                    "USDA Natural Resources Conservation Service",
                    "Pollinator Partnership economic studies"
                ],
                "conservative_estimate": True
            }
        }

    # =========================================================================
    # GRANT REPORTING
    # =========================================================================

    def generate_biodiversity_grant_report(
        self,
        total_farm_acres: float,
        crop_year: int,
        grant_program: str
    ) -> Dict:
        """
        Generate comprehensive biodiversity report for grant applications.
        """

        habitat_score = self.calculate_farm_habitat_score(total_farm_acres)
        pollinator_summary = self.get_pollinator_summary(year=crop_year)
        wildlife_summary = self.get_wildlife_summary(year=crop_year)
        ecosystem_value = self.calculate_ecosystem_services_value(total_farm_acres)

        return {
            "report_title": f"Biodiversity & Ecosystem Services Report - {crop_year}",
            "grant_program": grant_program,
            "generated_date": datetime.now().isoformat(),
            "farm_summary": {
                "total_acres": total_farm_acres,
                "habitat_acres": habitat_score.get("habitat_summary", {}).get("total_habitat_acres", 0),
                "habitat_percent": habitat_score.get("habitat_summary", {}).get("habitat_percent", 0),
                "habitat_types": habitat_score.get("habitat_summary", {}).get("habitat_types", 0)
            },
            "sections": {
                "habitat_assessment": {
                    "score": habitat_score.get("overall_score", 0),
                    "grade": habitat_score.get("grade", "N/A"),
                    "wildlife_group_scores": habitat_score.get("wildlife_group_scores", {}),
                    "certifications_eligible": habitat_score.get("certification_eligible", {})
                },
                "pollinator_monitoring": {
                    "observations": pollinator_summary.get("total_observations", 0),
                    "total_counted": pollinator_summary.get("total_pollinators_counted", 0),
                    "diversity": pollinator_summary.get("diversity_index", 0),
                    "groups_observed": list(pollinator_summary.get("by_pollinator_group", {}).keys())
                },
                "wildlife_observations": {
                    "total_observations": wildlife_summary.get("total_observations", 0),
                    "species_documented": wildlife_summary.get("species_richness", 0),
                    "diversity_assessment": wildlife_summary.get("diversity_assessment", "N/A")
                },
                "ecosystem_services": {
                    "total_annual_value": ecosystem_value.get("total_annual_value", 0),
                    "services_provided": list(ecosystem_value.get("ecosystem_services", {}).keys()),
                    "value_per_acre": ecosystem_value.get("value_per_farm_acre", 0)
                }
            },
            "grant_compliance_metrics": {
                "habitat_established": habitat_score.get("habitat_summary", {}).get("total_habitat_acres", 0) > 0,
                "pollinator_monitoring_active": pollinator_summary.get("total_observations", 0) > 0,
                "wildlife_documented": wildlife_summary.get("total_observations", 0) > 0,
                "ecosystem_value_calculated": ecosystem_value.get("total_annual_value", 0) > 0,
                "conservation_practices_implemented": len(self.habitat_areas) > 0
            },
            "nrcs_practice_summary": [
                {
                    "practice_code": h.nrcs_practice_code,
                    "habitat_type": h.habitat_type.value,
                    "acres": h.area_acres
                }
                for h in self.habitat_areas
            ],
            "recommendations": habitat_score.get("recommendations", [])
        }


# Create singleton instance
biodiversity_service = BiodiversityService()
