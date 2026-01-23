"""
Application Cost Optimization Module
Optimizes fertilizer, pesticide, and fungicide application costs
Helps farmers make economical decisions on input purchases and application methods
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ApplicationType(str, Enum):
    FERTILIZER = "fertilizer"
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FUNGICIDE = "fungicide"
    SEED_TREATMENT = "seed_treatment"


class ApplicationMethod(str, Enum):
    BROADCAST = "broadcast"
    BANDED = "banded"
    FOLIAR = "foliar"
    IN_FURROW = "in_furrow"
    SIDE_DRESS = "side_dress"
    AERIAL = "aerial"
    FERTIGATION = "fertigation"


# Current average input costs (2024 prices - should be updated periodically)
FERTILIZER_PRICES = {
    "urea_46-0-0": 0.55,  # $/lb N
    "uan_28": 0.52,  # $/lb N
    "uan_32": 0.54,  # $/lb N
    "anhydrous_82": 0.48,  # $/lb N (most economical per unit)
    "map_11-52-0": 0.65,  # $/lb P2O5
    "dap_18-46-0": 0.62,  # $/lb P2O5
    "potash_0-0-60": 0.42,  # $/lb K2O
    "sulfur_ams_21-0-0-24s": 0.45,  # $/lb S
    "zinc_sulfate": 1.20,  # $/lb Zn
    "boron": 2.50,  # $/lb B
}

# Application costs by method
APPLICATION_COSTS = {
    "broadcast_dry": 5.50,  # $/acre
    "broadcast_liquid": 6.00,  # $/acre
    "banded": 7.00,  # $/acre
    "anhydrous_application": 12.00,  # $/acre
    "side_dress": 10.00,  # $/acre
    "foliar_ground": 7.50,  # $/acre
    "foliar_aerial": 9.00,  # $/acre
    "in_furrow": 3.50,  # $/acre (with planter)
    "fertigation": 2.00,  # $/acre (through irrigation)
    "variable_rate_upcharge": 2.00,  # Additional $/acre for VRT
}

# Typical crop nutrient removal (lb/bushel harvested)
NUTRIENT_REMOVAL = {
    "corn": {
        "N": 0.67,  # lb N per bushel
        "P2O5": 0.37,
        "K2O": 0.27,
        "S": 0.08
    },
    "soybean": {
        "N": 3.8,  # Fixed by nodules, but removed in grain
        "P2O5": 0.80,
        "K2O": 1.40,
        "S": 0.18
    },
    "wheat": {
        "N": 1.25,
        "P2O5": 0.50,
        "K2O": 0.30,
        "S": 0.10
    }
}


@dataclass
class FertilizerRecommendation:
    """Structured fertilizer recommendation"""
    product: str
    rate_per_acre: float
    unit: str
    nutrient_supplied: Dict[str, float]
    cost_per_acre: float
    application_method: str
    timing: str


class ApplicationCostOptimizer:
    """
    Optimizes application costs for:
    - Fertilizers (N, P, K, S, micronutrients)
    - Pesticides (herbicides, insecticides, fungicides)
    - Application method selection
    - Timing optimization
    - Product sourcing
    """

    def __init__(
        self,
        custom_fertilizer_prices: Optional[Dict[str, float]] = None,
        custom_application_costs: Optional[Dict[str, float]] = None
    ):
        self.fertilizer_prices = {**FERTILIZER_PRICES}
        self.application_costs = {**APPLICATION_COSTS}

        if custom_fertilizer_prices:
            self.fertilizer_prices.update(custom_fertilizer_prices)
        if custom_application_costs:
            self.application_costs.update(custom_application_costs)

    def optimize_fertilizer_program(
        self,
        crop: str,
        yield_goal: float,
        acres: float,
        soil_test_results: Dict[str, float],
        current_prices: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Optimize fertilizer program based on yield goal and soil tests

        Args:
            crop: 'corn', 'soybean', or 'wheat'
            yield_goal: Target yield (bu/acre)
            acres: Field size
            soil_test_results: Dict with N, P, K levels (ppm or index)
            current_prices: Optional custom pricing

        Returns:
            Optimized fertilizer recommendations with costs
        """
        if current_prices:
            self.fertilizer_prices.update(current_prices)

        crop_lower = crop.lower()
        removal = NUTRIENT_REMOVAL.get(crop_lower, NUTRIENT_REMOVAL["corn"])

        # Calculate nutrient needs based on yield goal
        n_needed = self._calculate_n_requirement(crop_lower, yield_goal, soil_test_results)
        p_needed = self._calculate_p_requirement(yield_goal, soil_test_results, removal)
        k_needed = self._calculate_k_requirement(yield_goal, soil_test_results, removal)
        s_needed = yield_goal * removal.get('S', 0.08)

        # Find most economical products for each nutrient
        n_recommendation = self._optimize_nitrogen_source(n_needed, crop_lower)
        p_recommendation = self._optimize_phosphorus_source(p_needed)
        k_recommendation = self._optimize_potassium_source(k_needed)
        s_recommendation = self._optimize_sulfur_source(s_needed)

        recommendations = []
        total_product_cost = 0
        total_application_cost = 0

        for rec in [n_recommendation, p_recommendation, k_recommendation, s_recommendation]:
            if rec and rec['rate_per_acre'] > 0:
                recommendations.append(rec)
                total_product_cost += rec['cost_per_acre'] * acres
                app_cost = self.application_costs.get(rec['application_method'], 7.00)
                total_application_cost += app_cost * acres

        # Calculate per-acre totals
        total_cost = total_product_cost + total_application_cost
        cost_per_acre = total_cost / acres if acres > 0 else 0
        cost_per_bushel = cost_per_acre / yield_goal if yield_goal > 0 else 0

        # Generate optimization suggestions
        optimizations = self._identify_fertilizer_savings(
            recommendations, crop_lower, yield_goal, soil_test_results
        )

        return {
            "crop": crop,
            "yield_goal": yield_goal,
            "acres": acres,
            "nutrient_requirements": {
                "nitrogen_lb_per_acre": round(n_needed, 1),
                "phosphorus_lb_p2o5_per_acre": round(p_needed, 1),
                "potassium_lb_k2o_per_acre": round(k_needed, 1),
                "sulfur_lb_per_acre": round(s_needed, 1)
            },
            "recommendations": recommendations,
            "cost_summary": {
                "total_product_cost": round(total_product_cost, 2),
                "total_application_cost": round(total_application_cost, 2),
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2),
                "cost_per_bushel_goal": round(cost_per_bushel, 2)
            },
            "optimization_opportunities": optimizations,
            "timing_recommendations": self._get_timing_recommendations(crop_lower)
        }

    def compare_pesticide_options(
        self,
        product_options: List[Dict[str, Any]],
        acres: float,
        application_method: str = "foliar_ground",
        include_generics: bool = True
    ) -> Dict[str, Any]:
        """
        Compare pesticide options and find most economical choice

        Args:
            product_options: List of products with name, rate, cost
            acres: Field size
            application_method: How product will be applied
            include_generics: Whether to suggest generic alternatives
        """
        app_cost = self.application_costs.get(application_method, 7.50)

        comparisons = []
        for product in product_options:
            product_cost = product.get('cost_per_acre', 0)
            total_per_acre = product_cost + app_cost
            total_cost = total_per_acre * acres

            comparisons.append({
                "product": product.get('name', 'Unknown'),
                "active_ingredient": product.get('active_ingredient', ''),
                "rate": product.get('rate', ''),
                "product_cost_per_acre": round(product_cost, 2),
                "application_cost_per_acre": round(app_cost, 2),
                "total_cost_per_acre": round(total_per_acre, 2),
                "total_cost_field": round(total_cost, 2),
                "efficacy_rating": product.get('efficacy', 8)
            })

        # Sort by total cost
        comparisons.sort(key=lambda x: x['total_cost_per_acre'])

        # Calculate savings vs most expensive
        most_expensive = max(c['total_cost_per_acre'] for c in comparisons)
        for comp in comparisons:
            comp['savings_vs_most_expensive'] = round(
                (most_expensive - comp['total_cost_per_acre']) * acres, 2
            )

        # Find best value (cost per efficacy point)
        for comp in comparisons:
            comp['cost_per_efficacy_point'] = round(
                comp['total_cost_per_acre'] / comp['efficacy_rating'], 2
            )

        best_value = min(comparisons, key=lambda x: x['cost_per_efficacy_point'])
        cheapest = comparisons[0]

        return {
            "acres": acres,
            "application_method": application_method,
            "application_cost_per_acre": app_cost,
            "comparisons": comparisons,
            "recommendations": {
                "cheapest_option": cheapest['product'],
                "cheapest_cost_per_acre": cheapest['total_cost_per_acre'],
                "best_value_option": best_value['product'],
                "best_value_cost_per_efficacy": best_value['cost_per_efficacy_point'],
                "potential_savings": round(
                    (most_expensive - cheapest['total_cost_per_acre']) * acres, 2
                )
            },
            "generic_alternatives": self._find_generic_alternatives(product_options) if include_generics else []
        }

    def calculate_spray_program_costs(
        self,
        crop: str,
        acres: float,
        spray_program: List[Dict[str, Any]],
        include_scouting: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate total costs for a complete spray program (season)

        Args:
            crop: Crop type
            acres: Field size
            spray_program: List of planned applications
            include_scouting: Include scouting costs in calculation
        """
        applications = []
        total_product_cost = 0
        total_application_cost = 0

        for spray in spray_program:
            product_cost = spray.get('product_cost_per_acre', 10)
            app_cost = self.application_costs.get(
                spray.get('method', 'foliar_ground'), 7.50
            )

            field_product_cost = product_cost * acres
            field_app_cost = app_cost * acres
            field_total = field_product_cost + field_app_cost

            applications.append({
                "timing": spray.get('timing', 'TBD'),
                "product": spray.get('product', 'TBD'),
                "target": spray.get('target', 'General'),
                "product_cost_per_acre": round(product_cost, 2),
                "application_cost_per_acre": round(app_cost, 2),
                "total_cost_per_acre": round(product_cost + app_cost, 2),
                "field_total_cost": round(field_total, 2)
            })

            total_product_cost += field_product_cost
            total_application_cost += field_app_cost

        # Scouting costs (if included)
        scouting_cost = 0
        if include_scouting:
            scouting_trips = len(spray_program) + 2  # Pre and post monitoring
            scouting_cost = scouting_trips * acres * 0.05 * 25  # $25/hr, 3 min/acre

        total_cost = total_product_cost + total_application_cost + scouting_cost

        # ROI calculation
        grain_prices = {"corn": 4.50, "soybean": 12.00, "wheat": 6.00}
        grain_price = grain_prices.get(crop.lower(), 5.00)

        # Estimate yield protection (conservative 5-15% depending on applications)
        yield_goal = 200 if crop.lower() == "corn" else 55
        yield_protection_percent = min(len(spray_program) * 3, 15)
        protected_yield = yield_goal * (yield_protection_percent / 100)
        protected_revenue = protected_yield * grain_price * acres

        return {
            "crop": crop,
            "acres": acres,
            "number_of_applications": len(spray_program),
            "applications": applications,
            "cost_summary": {
                "total_product_cost": round(total_product_cost, 2),
                "total_application_cost": round(total_application_cost, 2),
                "scouting_cost": round(scouting_cost, 2),
                "total_program_cost": round(total_cost, 2),
                "cost_per_acre": round(total_cost / acres if acres > 0 else 0, 2),
                "cost_per_bushel_protected": round(
                    total_cost / (protected_yield * acres) if protected_yield > 0 else 0, 2
                )
            },
            "roi_analysis": {
                "estimated_yield_protection_percent": yield_protection_percent,
                "estimated_protected_yield_per_acre": round(protected_yield, 1),
                "grain_price": grain_price,
                "protected_revenue": round(protected_revenue, 2),
                "net_benefit": round(protected_revenue - total_cost, 2),
                "roi_percent": round(
                    ((protected_revenue - total_cost) / total_cost) * 100 if total_cost > 0 else 0, 1
                )
            },
            "optimization_tips": self._generate_spray_program_tips(spray_program, crop)
        }

    def analyze_variable_rate_savings(
        self,
        acres: float,
        zones: List[Dict[str, Any]],
        product_type: str,
        base_rate_per_acre: float
    ) -> Dict[str, Any]:
        """
        Analyze potential savings from variable rate application

        Args:
            acres: Total field acres
            zones: List of zones with 'acres' and 'recommended_rate_percent'
            product_type: Type of input being applied
            base_rate_per_acre: Flat rate cost per acre
        """
        # Flat rate cost
        flat_rate_cost = acres * base_rate_per_acre

        # Variable rate cost
        vr_product_cost = 0
        zone_details = []

        for zone in zones:
            zone_acres = zone.get('acres', 0)
            rate_percent = zone.get('recommended_rate_percent', 100)
            zone_cost = zone_acres * base_rate_per_acre * (rate_percent / 100)
            vr_product_cost += zone_cost

            zone_details.append({
                "zone_name": zone.get('name', 'Zone'),
                "acres": zone_acres,
                "rate_percent": rate_percent,
                "cost": round(zone_cost, 2)
            })

        # Add VRT technology upcharge
        vrt_upcharge = acres * self.application_costs.get('variable_rate_upcharge', 2.00)
        vr_total_cost = vr_product_cost + vrt_upcharge

        savings = flat_rate_cost - vr_total_cost
        savings_percent = (savings / flat_rate_cost * 100) if flat_rate_cost > 0 else 0

        # Break-even analysis
        if savings > 0:
            break_even = "VRT is economical"
        elif vrt_upcharge > 0:
            # How much product savings needed to offset VRT cost
            needed_savings_percent = (vrt_upcharge / flat_rate_cost) * 100
            break_even = f"Need {needed_savings_percent:.1f}% product reduction to break even"
        else:
            break_even = "Flat rate more economical"

        return {
            "product_type": product_type,
            "total_acres": acres,
            "zone_breakdown": zone_details,
            "cost_comparison": {
                "flat_rate_cost": round(flat_rate_cost, 2),
                "vrt_product_cost": round(vr_product_cost, 2),
                "vrt_technology_upcharge": round(vrt_upcharge, 2),
                "vrt_total_cost": round(vr_total_cost, 2),
                "savings": round(savings, 2),
                "savings_percent": round(savings_percent, 1)
            },
            "analysis": {
                "break_even_status": break_even,
                "recommendation": (
                    "Variable rate application recommended" if savings > 0
                    else "Continue with flat rate application"
                ),
                "additional_benefits": [
                    "Reduced environmental impact in low-need areas",
                    "Optimized crop response in high-need areas",
                    "Better nutrient use efficiency",
                    "Documentation for sustainability programs"
                ] if savings > 0 else []
            }
        }

    def _calculate_n_requirement(
        self,
        crop: str,
        yield_goal: float,
        soil_test: Dict[str, float]
    ) -> float:
        """Calculate nitrogen requirement"""
        if crop == "corn":
            # 1.0-1.2 lb N per bushel yield goal
            base_need = yield_goal * 1.1
            # Credit for previous crop, soil organic matter
            credits = soil_test.get('n_credit', 0)
            return max(0, base_need - credits)
        elif crop == "soybean":
            # Soybeans fix most of their N
            return 0
        elif crop == "wheat":
            return yield_goal * 1.3
        return 0

    def _calculate_p_requirement(
        self,
        yield_goal: float,
        soil_test: Dict[str, float],
        removal: Dict[str, float]
    ) -> float:
        """Calculate phosphorus requirement based on soil test"""
        p_level = soil_test.get('P', 25)  # ppm

        # Build/maintain/drawdown based on soil test
        if p_level < 15:  # Low
            # Build: apply 1.5x removal + maintenance
            return yield_goal * removal['P2O5'] * 1.5 + 20
        elif p_level < 25:  # Medium
            # Maintain: apply removal rate
            return yield_goal * removal['P2O5']
        else:  # High
            # Drawdown: apply 50% of removal
            return yield_goal * removal['P2O5'] * 0.5

    def _calculate_k_requirement(
        self,
        yield_goal: float,
        soil_test: Dict[str, float],
        removal: Dict[str, float]
    ) -> float:
        """Calculate potassium requirement based on soil test"""
        k_level = soil_test.get('K', 150)  # ppm

        if k_level < 120:  # Low
            return yield_goal * removal['K2O'] * 1.5 + 30
        elif k_level < 170:  # Medium
            return yield_goal * removal['K2O']
        else:  # High
            return yield_goal * removal['K2O'] * 0.5

    def _optimize_nitrogen_source(self, n_needed: float, crop: str) -> Optional[Dict]:
        """Find most economical nitrogen source"""
        if n_needed <= 0:
            return None

        # Compare N sources
        sources = {
            "anhydrous_82": {
                "analysis": 0.82,
                "price_per_lb_n": self.fertilizer_prices.get('anhydrous_82', 0.48),
                "method": "anhydrous_application",
                "timing": "Pre-plant or side-dress"
            },
            "urea_46-0-0": {
                "analysis": 0.46,
                "price_per_lb_n": self.fertilizer_prices.get('urea_46-0-0', 0.55),
                "method": "broadcast_dry",
                "timing": "Pre-plant with incorporation or side-dress"
            },
            "uan_32": {
                "analysis": 0.32,
                "price_per_lb_n": self.fertilizer_prices.get('uan_32', 0.54),
                "method": "broadcast_liquid",
                "timing": "Pre-plant or in-season"
            }
        }

        # Find cheapest per lb N
        cheapest = min(sources.items(), key=lambda x: x[1]['price_per_lb_n'])
        source_name, source_info = cheapest

        product_rate = n_needed / source_info['analysis']  # lb product per acre
        cost_per_acre = n_needed * source_info['price_per_lb_n']

        return {
            "nutrient": "Nitrogen",
            "product": source_name,
            "rate_per_acre": round(product_rate, 1),
            "unit": "lb",
            "nutrient_supplied_lb_per_acre": round(n_needed, 1),
            "cost_per_acre": round(cost_per_acre, 2),
            "price_per_lb_nutrient": source_info['price_per_lb_n'],
            "application_method": source_info['method'],
            "timing": source_info['timing']
        }

    def _optimize_phosphorus_source(self, p_needed: float) -> Optional[Dict]:
        """Find most economical P source"""
        if p_needed <= 0:
            return None

        sources = {
            "dap_18-46-0": {
                "analysis_p": 0.46,
                "analysis_n": 0.18,
                "price_per_lb_p": self.fertilizer_prices.get('dap_18-46-0', 0.62),
                "method": "broadcast_dry"
            },
            "map_11-52-0": {
                "analysis_p": 0.52,
                "analysis_n": 0.11,
                "price_per_lb_p": self.fertilizer_prices.get('map_11-52-0', 0.65),
                "method": "broadcast_dry"
            }
        }

        cheapest = min(sources.items(), key=lambda x: x[1]['price_per_lb_p'])
        source_name, source_info = cheapest

        product_rate = p_needed / source_info['analysis_p']
        cost_per_acre = p_needed * source_info['price_per_lb_p']
        n_bonus = product_rate * source_info['analysis_n']

        return {
            "nutrient": "Phosphorus",
            "product": source_name,
            "rate_per_acre": round(product_rate, 1),
            "unit": "lb",
            "nutrient_supplied_lb_per_acre": round(p_needed, 1),
            "bonus_n_supplied": round(n_bonus, 1),
            "cost_per_acre": round(cost_per_acre, 2),
            "price_per_lb_nutrient": source_info['price_per_lb_p'],
            "application_method": source_info['method'],
            "timing": "Fall or spring pre-plant"
        }

    def _optimize_potassium_source(self, k_needed: float) -> Optional[Dict]:
        """Find most economical K source"""
        if k_needed <= 0:
            return None

        price_per_lb_k = self.fertilizer_prices.get('potash_0-0-60', 0.42)
        product_rate = k_needed / 0.60  # 60% K2O
        cost_per_acre = k_needed * price_per_lb_k

        return {
            "nutrient": "Potassium",
            "product": "potash_0-0-60",
            "rate_per_acre": round(product_rate, 1),
            "unit": "lb",
            "nutrient_supplied_lb_per_acre": round(k_needed, 1),
            "cost_per_acre": round(cost_per_acre, 2),
            "price_per_lb_nutrient": price_per_lb_k,
            "application_method": "broadcast_dry",
            "timing": "Fall or spring pre-plant"
        }

    def _optimize_sulfur_source(self, s_needed: float) -> Optional[Dict]:
        """Find most economical S source"""
        if s_needed <= 10:  # Don't recommend if need is low
            return None

        price_per_lb_s = self.fertilizer_prices.get('sulfur_ams_21-0-0-24s', 0.45)
        product_rate = s_needed / 0.24  # 24% S
        cost_per_acre = s_needed * price_per_lb_s
        n_bonus = product_rate * 0.21  # Also supplies N

        return {
            "nutrient": "Sulfur",
            "product": "ams_21-0-0-24s",
            "rate_per_acre": round(product_rate, 1),
            "unit": "lb",
            "nutrient_supplied_lb_per_acre": round(s_needed, 1),
            "bonus_n_supplied": round(n_bonus, 1),
            "cost_per_acre": round(cost_per_acre, 2),
            "price_per_lb_nutrient": price_per_lb_s,
            "application_method": "broadcast_dry",
            "timing": "Spring pre-plant or in-season"
        }

    def _identify_fertilizer_savings(
        self,
        recommendations: List[Dict],
        crop: str,
        yield_goal: float,
        soil_test: Dict[str, float]
    ) -> List[Dict]:
        """Identify opportunities to reduce fertilizer costs"""
        opportunities = []

        # Check for over-application based on soil tests
        p_level = soil_test.get('P', 25)
        k_level = soil_test.get('K', 150)

        if p_level > 40:
            opportunities.append({
                "area": "Phosphorus",
                "recommendation": "Soil P is very high. Consider skipping P application this year.",
                "potential_savings_per_acre": 15.00,
                "risk_level": "Low"
            })

        if k_level > 200:
            opportunities.append({
                "area": "Potassium",
                "recommendation": "Soil K is very high. Reduce K rate by 50% or skip.",
                "potential_savings_per_acre": 12.00,
                "risk_level": "Low"
            })

        # Application method optimization
        opportunities.append({
            "area": "Application Timing",
            "recommendation": "Combine P and K application in fall to reduce trips.",
            "potential_savings_per_acre": 5.50,
            "risk_level": "None"
        })

        # N management
        if crop == "corn":
            opportunities.append({
                "area": "Nitrogen Management",
                "recommendation": "Split N applications (30% at plant, 70% side-dress) can improve efficiency 10-15%.",
                "potential_savings_per_acre": 8.00,
                "risk_level": "Low"
            })

        # Variable rate
        opportunities.append({
            "area": "Variable Rate Technology",
            "recommendation": "VRT can reduce fertilizer use 5-15% on variable fields.",
            "potential_savings_per_acre": 10.00,
            "risk_level": "Low - requires initial mapping investment"
        })

        return opportunities

    def _get_timing_recommendations(self, crop: str) -> List[Dict]:
        """Get optimal application timing recommendations"""
        if crop == "corn":
            return [
                {"timing": "Fall", "products": "P, K", "notes": "Apply after soil temps below 50F"},
                {"timing": "Pre-plant", "products": "N (30-40%), P, K, S", "notes": "2-4 weeks before planting"},
                {"timing": "At planting", "products": "Starter (N, P)", "notes": "In-furrow or 2x2"},
                {"timing": "V6-V8", "products": "N (60-70%)", "notes": "Side-dress or Y-drop"},
                {"timing": "VT-R1", "products": "Foliar micronutrients if needed", "notes": "Based on tissue tests"}
            ]
        elif crop == "soybean":
            return [
                {"timing": "Fall", "products": "P, K", "notes": "Apply after harvest"},
                {"timing": "Pre-plant", "products": "P, K, S", "notes": "Incorporate if possible"},
                {"timing": "R1-R3", "products": "Foliar S, micronutrients", "notes": "If deficiency observed"}
            ]
        return []

    def _find_generic_alternatives(self, products: List[Dict]) -> List[Dict]:
        """Find generic alternatives to brand-name products"""
        alternatives = []
        for product in products:
            ai = product.get('active_ingredient', '').lower()

            # Common generic mappings
            if 'glyphosate' in ai:
                alternatives.append({
                    "brand_product": product.get('name'),
                    "generic_alternative": "Generic Glyphosate 4 lb/gal",
                    "estimated_savings": "30-50%"
                })
            elif 'lambda-cyhalothrin' in ai:
                alternatives.append({
                    "brand_product": product.get('name'),
                    "generic_alternative": "Generic Lambda-Cy",
                    "estimated_savings": "25-40%"
                })
            elif 'azoxystrobin' in ai:
                alternatives.append({
                    "brand_product": product.get('name'),
                    "generic_alternative": "Generic Azoxystrobin (limited availability)",
                    "estimated_savings": "20-30%"
                })

        return alternatives

    def _generate_spray_program_tips(
        self,
        spray_program: List[Dict],
        crop: str
    ) -> List[str]:
        """Generate tips to optimize spray program"""
        tips = []

        if len(spray_program) > 3:
            tips.append(
                "Consider tank-mixing compatible products to reduce application passes. "
                "Each eliminated pass saves $7-10/acre in application costs."
            )

        tips.append(
            "Scout before every application. Threshold-based spraying can eliminate "
            "1-2 applications per season, saving $15-35/acre."
        )

        tips.append(
            "Time fungicide applications to growth stage (VT-R2 for corn, R3 for soybeans) "
            "for maximum ROI. Early or late applications often have poor returns."
        )

        tips.append(
            "Compare custom application quotes. Aerial may be more economical than "
            "ground at $9-11/acre when timeliness is critical."
        )

        if crop.lower() == "corn":
            tips.append(
                "If hybrid has good disease ratings, foliar fungicide may not be economical "
                "unless disease pressure is high."
            )

        return tips


# Singleton instance
_optimizer = None

def get_application_optimizer(
    custom_fertilizer_prices: Optional[Dict] = None,
    custom_application_costs: Optional[Dict] = None
) -> ApplicationCostOptimizer:
    """Get or create optimizer instance"""
    global _optimizer
    if _optimizer is None or custom_fertilizer_prices or custom_application_costs:
        _optimizer = ApplicationCostOptimizer(
            custom_fertilizer_prices,
            custom_application_costs
        )
    return _optimizer


# Example usage
if __name__ == "__main__":
    optimizer = ApplicationCostOptimizer()

    # Example: Optimize fertilizer program for corn
    soil_test = {
        "P": 22,  # ppm
        "K": 145,  # ppm
        "pH": 6.8,
        "OM": 3.2,  # %
        "n_credit": 30  # lb/acre from previous soybean
    }

    result = optimizer.optimize_fertilizer_program(
        crop="corn",
        yield_goal=200,  # bu/acre
        acres=500,
        soil_test_results=soil_test
    )

    print("=== FERTILIZER PROGRAM OPTIMIZATION ===")
    print(f"Crop: {result['crop']}")
    print(f"Yield Goal: {result['yield_goal']} bu/acre")
    print(f"Acres: {result['acres']}")

    print("\n=== NUTRIENT REQUIREMENTS ===")
    for nutrient, amount in result['nutrient_requirements'].items():
        print(f"  {nutrient}: {amount}")

    print("\n=== PRODUCT RECOMMENDATIONS ===")
    for rec in result['recommendations']:
        print(f"\n{rec['nutrient']}:")
        print(f"  Product: {rec['product']}")
        print(f"  Rate: {rec['rate_per_acre']} {rec['unit']}/acre")
        print(f"  Cost: ${rec['cost_per_acre']}/acre")

    print("\n=== COST SUMMARY ===")
    costs = result['cost_summary']
    print(f"Total Program Cost: ${costs['total_cost']:,.2f}")
    print(f"Cost per Acre: ${costs['cost_per_acre']}")
    print(f"Cost per Bushel (at goal): ${costs['cost_per_bushel_goal']}")

    print("\n=== OPTIMIZATION OPPORTUNITIES ===")
    for opp in result['optimization_opportunities']:
        print(f"\n{opp['area']}:")
        print(f"  {opp['recommendation']}")
        print(f"  Potential Savings: ${opp['potential_savings_per_acre']}/acre")
