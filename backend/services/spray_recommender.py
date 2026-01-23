"""
Intelligent Spray Recommendation Engine
Professional-grade pesticide recommendations with resistance management and economic analysis
"""

from typing import List, Dict, Optional, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.chemical_database import (
    INSECTICIDE_PRODUCTS,
    FUNGICIDE_PRODUCTS,
    ADJUVANTS
)
from database.seed_data import CORN_PESTS, SOYBEAN_PESTS, CORN_DISEASES, SOYBEAN_DISEASES
from services.measurement_converter_service import convert_rate_string

class SprayRecommender:
    """Professional spray recommendation system"""

    def __init__(self):
        self.insecticides = INSECTICIDE_PRODUCTS
        self.fungicides = FUNGICIDE_PRODUCTS
        self.adjuvants = ADJUVANTS
        self.corn_pests = CORN_PESTS
        self.soybean_pests = SOYBEAN_PESTS
        self.corn_diseases = CORN_DISEASES
        self.soybean_diseases = SOYBEAN_DISEASES

    def generate_spray_recommendation(
        self,
        crop: str,
        growth_stage: str,
        problem_type: str,
        problem_id: int,
        severity: int,
        field_acres: float,
        previous_applications: Optional[List[str]] = None,
        weather_forecast: Optional[Dict[str, List]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive spray recommendation

        Args:
            crop: 'corn' or 'soybean'
            growth_stage: Growth stage (VE, V3, V6, VT, R1, etc.)
            problem_type: 'pest' or 'disease'
            problem_id: Index of pest/disease in database
            severity: Severity rating 1-10
            field_acres: Size of field
            previous_applications: List of recently applied products
            weather_forecast: Temperature and rain predictions
        """

        # Get problem details
        problem_info = self._get_problem_info(crop, problem_type, problem_id)

        # Determine if spray is warranted
        action = self._determine_action(severity, growth_stage, problem_info)

        if action == "scout_again":
            return {
                "recommended_action": "scout_again",
                "primary_product": None,
                "alternative_products": [],
                "reasoning": "Severity does not justify treatment at this time. Continue monitoring.",
                "scouting_interval": "3-5 days",
                "economic_analysis": {
                    "treatment_not_warranted": True
                }
            }

        # Select appropriate products
        if problem_type == "pest":
            primary_product, alternatives = self._select_insecticide(
                crop=crop,
                pest_name=problem_info["common_name"],
                growth_stage=growth_stage,
                previous_applications=previous_applications
            )
        else:  # disease
            primary_product, alternatives = self._select_fungicide(
                crop=crop,
                disease_name=problem_info["common_name"],
                growth_stage=growth_stage,
                previous_applications=previous_applications
            )

        # Determine tank mix partners
        tank_mix = self._get_tank_mix_recommendations(
            primary_product,
            crop,
            growth_stage,
            problem_type
        )

        # Adjuvant recommendations
        adjuvants = self._get_adjuvant_recommendations(primary_product)

        # Spray timing window
        timing = self._get_spray_timing(
            problem_info,
            growth_stage,
            weather_forecast
        )

        # Economic analysis
        economics = self._calculate_economics(
            primary_product,
            field_acres,
            severity,
            crop
        )

        # Resistance management notes
        resistance_notes = self._get_resistance_management_notes(
            primary_product,
            previous_applications
        )

        return {
            "recommended_action": action,
            "primary_product": primary_product,
            "alternative_products": alternatives,
            "tank_mix_partners": tank_mix,
            "adjuvant_recommendations": adjuvants,
            "spray_timing_window": timing["window"],
            "weather_requirements": timing["requirements"],
            "application_notes": timing["notes"],
            "economic_analysis": economics,
            "resistance_management_notes": resistance_notes,
            "problem_details": {
                "name": problem_info["common_name"],
                "scientific_name": problem_info.get("scientific_name", ""),
                "type": problem_type
            }
        }

    def _get_problem_info(self, crop: str, problem_type: str, problem_id: int) -> Dict:
        """Get pest or disease information"""
        if problem_type == "pest":
            if crop == "corn":
                return self.corn_pests[problem_id] if problem_id < len(self.corn_pests) else self.corn_pests[0]
            else:
                return self.soybean_pests[problem_id] if problem_id < len(self.soybean_pests) else self.soybean_pests[0]
        else:  # disease
            if crop == "corn":
                return self.corn_diseases[problem_id] if problem_id < len(self.corn_diseases) else self.corn_diseases[0]
            else:
                return self.soybean_diseases[problem_id] if problem_id < len(self.soybean_diseases) else self.soybean_diseases[0]

    def _determine_action(self, severity: int, growth_stage: str, problem_info: Dict) -> str:
        """Determine if treatment is warranted"""
        # Severity < 4 usually doesn't warrant treatment
        if severity < 4:
            return "scout_again"

        # Late season may not warrant treatment (depends on crop value remaining)
        if growth_stage in ["R6"]:
            return "scout_again"

        # Otherwise recommend spraying
        return "spray"

    def _select_insecticide(
        self,
        crop: str,
        pest_name: str,
        growth_stage: str,
        previous_applications: Optional[List[str]]
    ) -> tuple:
        """
        Select best insecticide based on pest, crop, and resistance management
        Returns (primary_product, list of alternatives)
        """
        # Filter products labeled for this crop
        suitable_products = []

        for product in self.insecticides:
            # Check if product targets this pest
            targets = product.get("targets", "")

            # Simple keyword matching (in production would use database relationships)
            pest_keywords = self._extract_pest_keywords(pest_name)

            if any(keyword.lower() in targets.lower() for keyword in pest_keywords):
                # Check PHI compatibility with growth stage
                phi_field = f"phi_days_{crop}"
                if phi_field in product and product[phi_field] is not None:
                    suitable_products.append(product)

        if not suitable_products:
            # Default recommendation
            return self._format_product_recommendation(self.insecticides[0], crop), []

        # Score products based on multiple factors
        scored_products = []
        for product in suitable_products:
            score = self._score_insecticide(
                product,
                pest_name,
                previous_applications
            )
            scored_products.append((score, product))

        # Sort by score (highest first)
        scored_products.sort(reverse=True, key=lambda x: x[0])

        # Return top choice and next 3 alternatives
        primary = self._format_product_recommendation(scored_products[0][1], crop)
        alternatives = [
            self._format_product_recommendation(p[1], crop)
            for p in scored_products[1:4]
        ]

        return primary, alternatives

    def _select_fungicide(
        self,
        crop: str,
        disease_name: str,
        growth_stage: str,
        previous_applications: Optional[List[str]]
    ) -> tuple:
        """Select best fungicide"""
        suitable_products = []

        for product in self.fungicides:
            target_field = f"targets_{crop}"
            if target_field in product and product[target_field]:
                targets = product[target_field]

                disease_keywords = self._extract_disease_keywords(disease_name)

                if any(keyword.lower() in targets.lower() for keyword in disease_keywords):
                    suitable_products.append(product)

        if not suitable_products:
            # Default
            return self._format_product_recommendation(self.fungicides[0], crop), []

        # Prefer multi-mode fungicides (premixes) for resistance management
        scored_products = []
        for product in suitable_products:
            score = self._score_fungicide(product, disease_name)
            scored_products.append((score, product))

        scored_products.sort(reverse=True, key=lambda x: x[0])

        primary = self._format_product_recommendation(scored_products[0][1], crop)
        alternatives = [
            self._format_product_recommendation(p[1], crop)
            for p in scored_products[1:4]
        ]

        return primary, alternatives

    def _score_insecticide(
        self,
        product: Dict,
        pest_name: str,
        previous_applications: Optional[List[str]]
    ) -> float:
        """Score insecticide based on efficacy and resistance management"""
        score = 5.0  # Base score

        # Prefer different MOA than recently used
        if previous_applications:
            if product.get("trade_name") not in previous_applications:
                score += 2.0

            # Check for different chemical family
            active = product.get("active_ingredient", "")
            if not any(active in app for app in previous_applications):
                score += 1.5

        # Prefer products with shorter PHI for late season
        phi_days = product.get("phi_days_corn", 30) or product.get("phi_days_soybean", 30)
        if phi_days <= 7:
            score += 1.0
        elif phi_days <= 14:
            score += 0.5

        # Prefer products with shorter REI (easier application management)
        rei = product.get("rei_hours", 24)
        if rei <= 12:
            score += 0.5

        # Specific product preferences based on pest
        if "aphid" in pest_name.lower():
            if "neonicotinoid" in product.get("active_ingredient", "").lower() or \
               "thiamethoxam" in product.get("active_ingredient", "").lower():
                score += 2.0

        if "caterpillar" in pest_name.lower() or "worm" in pest_name.lower() or \
           "borer" in pest_name.lower():
            if "diamide" in product.get("active_ingredient", "").lower() or \
               "chlorantraniliprole" in product.get("active_ingredient", "").lower():
                score += 2.0

        return score

    def _score_fungicide(self, product: Dict, disease_name: str) -> float:
        """Score fungicide"""
        score = 5.0

        # Strongly prefer premixes (multiple MOA)
        active = product.get("active_ingredient", "")
        if "+" in active:  # Indicates premix
            score += 3.0

        # Specific disease targeting
        if "tar spot" in disease_name.lower():
            if "trivapro" in product.get("trade_name", "").lower():
                score += 2.0

        if "white mold" in disease_name.lower():
            if "proline" in product.get("trade_name", "").lower() or \
               "endura" in product.get("trade_name", "").lower():
                score += 2.0

        if "rust" in disease_name.lower():
            if "triazole" in active.lower():
                score += 1.5

        return score

    def _format_product_recommendation(self, product: Dict, crop: str) -> Dict:
        """Format product information for API response"""
        rate_field = f"{crop}_rate"
        phi_field = f"phi_days_{crop}"

        rate = product.get(rate_field, product.get("corn_rate", "See label"))
        phi = product.get(phi_field, product.get("phi_days_corn", 30))

        # Estimate cost (placeholder - real system would have pricing database)
        estimated_cost = self._estimate_product_cost(product, rate)

        # Convert rate to metric (v6.14.0 - for international operators)
        rate_metric = None
        rate_imperial = rate
        if rate and rate != "See label":
            try:
                conversion = convert_rate_string(rate)
                rate_metric = conversion.metric_display
                rate_imperial = conversion.imperial_display
            except (ValueError, AttributeError):
                # If conversion fails, leave rate_metric as None
                pass

        return {
            "product_name": product.get("trade_name", ""),
            "manufacturer": product.get("manufacturer", ""),
            "active_ingredient": product.get("active_ingredient", ""),
            "formulation": product.get("formulation", ""),
            "rate": rate,
            "rate_imperial": rate_imperial,
            "rate_metric": rate_metric,
            "cost_per_acre": estimated_cost,
            "efficacy_rating": 8,  # Placeholder - real system would have efficacy data
            "application_timing": product.get("timing", "See label"),
            "restrictions": product.get("notes", ""),
            "phi_days": phi if phi is not None else 30,
            "rei_hours": product.get("rei_hours", 24),
            "resistance_management_notes": product.get("notes", "")
        }

    def _estimate_product_cost(self, product: Dict, rate: str) -> float:
        """Estimate product cost per acre (placeholder)"""
        # Real system would integrate with pricing database
        # For now, return estimated ranges
        product_type = product.get("product_type", "")

        if product_type == "insecticide":
            # Pyrethroids cheaper, diamides more expensive
            if "pyrethroid" in str(product.get("active_ingredient", "")).lower():
                return 8.50
            elif "diamide" in str(product.get("active_ingredient", "")).lower():
                return 18.00
            elif "neonicotinoid" in str(product.get("active_ingredient", "")).lower():
                return 12.00
            else:
                return 10.00
        else:  # fungicide
            # Premixes more expensive
            if "+" in product.get("active_ingredient", ""):
                return 20.00
            else:
                return 12.00

    def _get_tank_mix_recommendations(
        self,
        primary_product: Dict,
        crop: str,
        growth_stage: str,
        problem_type: str
    ) -> List[str]:
        """Recommend tank mix partners"""
        recommendations = []

        # Common tank mixes
        if problem_type == "pest":
            # Often tank mix insecticide with fungicide at VT-R2 in corn
            if crop == "corn" and growth_stage in ["VT", "R1", "R2"]:
                recommendations.append("Consider tank-mixing with fungicide for foliar disease protection at this growth stage")

        return recommendations

    def _get_adjuvant_recommendations(self, primary_product: Dict) -> List[str]:
        """Recommend adjuvants"""
        recommendations = []

        _product_type = primary_product.get("product_name", "").lower()

        # Generic recommendations
        recommendations.append("NIS (non-ionic surfactant) at 0.25% v/v for most applications")

        # Check if specific adjuvant recommended
        if "fungicide" in str(primary_product):
            recommendations.append("InterLock or similar deposition aid at 3-6 fl oz/acre to improve coverage and rainfastness")

        return recommendations

    def _get_spray_timing(
        self,
        problem_info: Dict,
        growth_stage: str,
        weather_forecast: Optional[Dict]
    ) -> Dict[str, str]:
        """Determine optimal spray timing window"""

        # Default timing
        timing = {
            "window": "Within 3-5 days",
            "requirements": "Temperature 55-85°F, wind < 10 mph, no rain for 2-4 hours",
            "notes": ""
        }

        # Adjust based on weather forecast
        if weather_forecast:
            if weather_forecast.get("rain"):
                rain_forecast = weather_forecast["rain"]
                if any(r > 0.5 for r in rain_forecast[:2]):  # Heavy rain next 2 days
                    timing["window"] = "Wait 2-3 days for better weather window"
                    timing["notes"] = "Rain forecast within 48 hours. Delay application for better efficacy."

        # Timing notes from problem info
        if "management_notes" in problem_info:
            timing["notes"] += " " + problem_info.get("management_notes", "")

        return timing

    def _calculate_economics(
        self,
        primary_product: Dict,
        field_acres: float,
        severity: int,
        crop: str
    ) -> Dict[str, float]:
        """Calculate economic analysis of treatment"""

        cost_per_acre = primary_product.get("cost_per_acre", 10.0)
        total_treatment_cost = cost_per_acre * field_acres

        # Application cost
        application_cost_per_acre = 7.50  # Custom application rate
        total_application_cost = application_cost_per_acre * field_acres

        total_cost = total_treatment_cost + total_application_cost

        # Estimated yield protection (rough estimate based on severity)
        # Higher severity = more potential yield loss prevented
        estimated_yield_protected_bushels = severity * 3  # bushels per acre

        # Grain price estimates
        grain_prices = {"corn": 4.50, "soybean": 12.00}
        grain_price = grain_prices.get(crop, 5.00)

        protected_revenue_per_acre = estimated_yield_protected_bushels * grain_price
        total_protected_revenue = protected_revenue_per_acre * field_acres

        net_benefit = total_protected_revenue - total_cost
        roi = (net_benefit / total_cost * 100) if total_cost > 0 else 0

        return {
            "product_cost_per_acre": cost_per_acre,
            "application_cost_per_acre": application_cost_per_acre,
            "total_cost_per_acre": cost_per_acre + application_cost_per_acre,
            "total_treatment_cost": total_cost,
            "estimated_yield_protected_bu_per_acre": estimated_yield_protected_bushels,
            "protected_revenue_per_acre": protected_revenue_per_acre,
            "total_protected_revenue": total_protected_revenue,
            "net_benefit": net_benefit,
            "roi_percent": roi
        }

    def _get_resistance_management_notes(
        self,
        primary_product: Dict,
        previous_applications: Optional[List[str]]
    ) -> str:
        """Generate resistance management notes"""

        notes = []

        active = primary_product.get("active_ingredient", "")

        # Check for pyrethroid
        if "pyrethroid" in active.lower() or any(p in active.lower() for p in ["bifenthrin", "lambda", "cyhalothrin"]):
            notes.append("PYRETHROID: Rotate with different MOA (diamides, neonicotinoids, organophosphates) to manage resistance.")

        # Check for QoI fungicide
        if "azoxystrobin" in active.lower() or "pyraclostrobin" in active.lower() or "strobilurin" in active.lower():
            notes.append("QoI FUNGICIDE: Always use in combination with triazole (Group 3) or SDHI (Group 7). Do not use single-mode QoI products.")

        # Previous application check
        if previous_applications:
            notes.append(f"Recommended rotation from previous applications: {', '.join(previous_applications[:2])}")

        return " ".join(notes) if notes else "Follow label instructions and rotate MOAs to delay resistance."

    def _extract_pest_keywords(self, pest_name: str) -> List[str]:
        """Extract searchable keywords from pest name"""
        # Simple keyword extraction
        keywords = []
        pest_lower = pest_name.lower()

        if "aphid" in pest_lower:
            keywords.append("aphid")
        if "rootworm" in pest_lower:
            keywords.append("rootworm")
        if "borer" in pest_lower:
            keywords.append("borer")
        if "cutworm" in pest_lower:
            keywords.append("cutworm")
        if "armyworm" in pest_lower:
            keywords.append("armyworm")
        if "beetle" in pest_lower:
            keywords.append("beetle")
        if "mite" in pest_lower:
            keywords.append("mite")
        if "stink bug" in pest_lower:
            keywords.append("stink bug")
        if "grasshopper" in pest_lower:
            keywords.append("grasshopper")

        # Add the full name
        keywords.append(pest_name)

        return keywords

    def _extract_disease_keywords(self, disease_name: str) -> List[str]:
        """Extract searchable keywords from disease name"""
        keywords = []
        disease_lower = disease_name.lower()

        if "gray leaf spot" in disease_lower:
            keywords.extend(["gray leaf spot", "GLS"])
        if "northern corn leaf blight" in disease_lower:
            keywords.extend(["northern corn leaf blight", "NCLB"])
        if "rust" in disease_lower:
            keywords.append("rust")
        if "tar spot" in disease_lower:
            keywords.append("tar spot")
        if "white mold" in disease_lower:
            keywords.extend(["white mold", "sclerotinia"])
        if "frogeye" in disease_lower:
            keywords.append("frogeye")

        keywords.append(disease_name)

        return keywords


# Singleton instance
_recommender = None

def generate_spray_recommendation(*args, **kwargs):
    """Module-level function to generate spray recommendation"""
    global _recommender
    if _recommender is None:
        _recommender = SprayRecommender()
    return _recommender.generate_spray_recommendation(*args, **kwargs)


# Example usage
if __name__ == "__main__":
    recommender = SprayRecommender()

    # Example: Soybean aphid at threshold
    result = recommender.generate_spray_recommendation(
        crop="soybean",
        growth_stage="R2",
        problem_type="pest",
        problem_id=0,  # Soybean aphid
        severity=8,
        field_acres=160,
        previous_applications=[],
        weather_forecast={
            "temperature": [75, 78, 80, 82, 79],
            "rain": [0, 0, 0.2, 0, 0]
        }
    )

    print("=== SPRAY RECOMMENDATION ===")
    print(f"Action: {result['recommended_action']}")
    print(f"\nPrimary Product: {result['primary_product']['product_name']}")
    print(f"Active Ingredient: {result['primary_product']['active_ingredient']}")
    print(f"Rate: {result['primary_product']['rate']}")
    print(f"Cost/Acre: ${result['primary_product']['cost_per_acre']:.2f}")
    print("\nEconomic Analysis:")
    print(f"  Total Cost: ${result['economic_analysis']['total_treatment_cost']:.2f}")
    print(f"  Protected Revenue: ${result['economic_analysis']['total_protected_revenue']:.2f}")
    print(f"  Net Benefit: ${result['economic_analysis']['net_benefit']:.2f}")
    print(f"  ROI: {result['economic_analysis']['roi_percent']:.1f}%")
