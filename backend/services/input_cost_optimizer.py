"""
Unified Input Cost Optimization Module
Combines labor, application, and irrigation optimization for comprehensive farm cost analysis
This is the main entry point for farmers to understand and reduce their input costs
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import date
from enum import Enum

from services.labor_optimizer import LaborOptimizer, get_labor_optimizer
from services.application_cost_optimizer import ApplicationCostOptimizer, get_application_optimizer
from services.irrigation_optimizer import IrrigationOptimizer, get_irrigation_optimizer


class OptimizationPriority(str, Enum):
    COST_REDUCTION = "cost_reduction"  # Minimize total costs
    ROI_MAXIMIZATION = "roi_maximization"  # Maximize return on investment
    SUSTAINABILITY = "sustainability"  # Balance cost with environmental impact
    RISK_REDUCTION = "risk_reduction"  # Minimize yield risk


@dataclass
class FarmProfile:
    """Complete farm profile for optimization"""
    total_acres: float
    crops: List[Dict[str, Any]]  # [{"crop": "corn", "acres": 500, "yield_goal": 200}]
    irrigation_system: Optional[str] = None
    water_source: Optional[str] = None
    soil_test_results: Optional[Dict[str, float]] = None
    previous_year_costs: Optional[Dict[str, float]] = None


class InputCostOptimizer:
    """
    Master optimizer that coordinates all cost optimization modules to provide:
    - Complete farm input cost analysis
    - Prioritized savings recommendations
    - ROI-based decision support
    - Season-long budget planning
    """

    def __init__(
        self,
        custom_labor_rates: Optional[Dict[str, float]] = None,
        custom_fertilizer_prices: Optional[Dict[str, float]] = None,
        custom_water_costs: Optional[Dict[str, float]] = None,
        electricity_rate_per_kwh: float = 0.10
    ):
        self.labor_optimizer = get_labor_optimizer(custom_labor_rates)
        self.application_optimizer = get_application_optimizer(custom_fertilizer_prices)
        self.irrigation_optimizer = get_irrigation_optimizer(custom_water_costs, electricity_rate_per_kwh)

    def analyze_complete_farm_costs(
        self,
        farm_profile: FarmProfile,
        season_length_days: int = 120,
        optimization_priority: OptimizationPriority = OptimizationPriority.COST_REDUCTION
    ) -> Dict[str, Any]:
        """
        Perform complete farm input cost analysis

        Args:
            farm_profile: Complete farm information
            season_length_days: Length of growing season
            optimization_priority: What to optimize for

        Returns:
            Comprehensive cost analysis with recommendations
        """
        results = {
            "farm_summary": {
                "total_acres": farm_profile.total_acres,
                "crops": [c['crop'] for c in farm_profile.crops],
                "has_irrigation": farm_profile.irrigation_system is not None,
                "optimization_priority": optimization_priority.value
            },
            "cost_categories": {},
            "total_costs": {},
            "optimization_opportunities": [],
            "action_plan": []
        }

        total_variable_cost = 0
        total_fixed_cost = 0
        total_potential_savings = 0

        # 1. Analyze labor costs
        labor_analysis = self._analyze_labor_costs(farm_profile, season_length_days)
        results["cost_categories"]["labor"] = labor_analysis
        total_variable_cost += labor_analysis["summary"]["total_cost"]
        total_potential_savings += labor_analysis["potential_savings"]

        # 2. Analyze application costs (fertilizer, pesticides)
        application_analysis = self._analyze_application_costs(farm_profile)
        results["cost_categories"]["applications"] = application_analysis
        total_variable_cost += application_analysis["summary"]["total_cost"]
        total_potential_savings += application_analysis["potential_savings"]

        # 3. Analyze irrigation costs (if applicable)
        if farm_profile.irrigation_system:
            irrigation_analysis = self._analyze_irrigation_costs(farm_profile, season_length_days)
            results["cost_categories"]["irrigation"] = irrigation_analysis
            total_variable_cost += irrigation_analysis["summary"]["variable_cost"]
            total_fixed_cost += irrigation_analysis["summary"]["fixed_cost"]
            total_potential_savings += irrigation_analysis["potential_savings"]

        # Calculate totals
        total_cost = total_variable_cost + total_fixed_cost
        cost_per_acre = total_cost / farm_profile.total_acres if farm_profile.total_acres > 0 else 0

        results["total_costs"] = {
            "total_variable_cost": round(total_variable_cost, 2),
            "total_fixed_cost": round(total_fixed_cost, 2),
            "total_input_cost": round(total_cost, 2),
            "cost_per_acre": round(cost_per_acre, 2),
            "total_potential_savings": round(total_potential_savings, 2),
            "potential_savings_percent": round(
                total_potential_savings / total_cost * 100 if total_cost > 0 else 0, 1
            )
        }

        # Generate prioritized recommendations
        results["optimization_opportunities"] = self._prioritize_recommendations(
            results["cost_categories"],
            optimization_priority
        )

        # Create action plan
        results["action_plan"] = self._create_action_plan(
            results["optimization_opportunities"],
            farm_profile
        )

        # Calculate ROI summary
        results["roi_summary"] = self._calculate_roi_summary(
            farm_profile, total_cost, total_potential_savings
        )

        return results

    def quick_cost_estimate(
        self,
        acres: float,
        crop: str,
        is_irrigated: bool = False,
        yield_goal: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Quick cost estimate for planning purposes
        Uses industry averages for fast estimation
        """
        crop_lower = crop.lower()

        # Default yield goals
        default_yields = {"corn": 180, "soybean": 50, "wheat": 60}
        yield_goal = yield_goal or default_yields.get(crop_lower, 150)

        # Industry average costs per acre (2024 estimates)
        average_costs = {
            "corn": {
                "seed": 120,
                "fertilizer": 175,
                "pesticides": 45,
                "labor": 25,
                "irrigation": 85 if is_irrigated else 0,
                "other": 30
            },
            "soybean": {
                "seed": 70,
                "fertilizer": 45,
                "pesticides": 35,
                "labor": 20,
                "irrigation": 65 if is_irrigated else 0,
                "other": 25
            },
            "wheat": {
                "seed": 40,
                "fertilizer": 95,
                "pesticides": 30,
                "labor": 20,
                "irrigation": 70 if is_irrigated else 0,
                "other": 20
            }
        }

        costs = average_costs.get(crop_lower, average_costs["corn"])

        total_per_acre = sum(costs.values())
        total_cost = total_per_acre * acres

        # Grain prices for ROI
        grain_prices = {"corn": 4.50, "soybean": 12.00, "wheat": 6.00}
        grain_price = grain_prices.get(crop_lower, 5.00)

        gross_revenue = yield_goal * grain_price * acres
        net_return = gross_revenue - total_cost
        break_even_yield = total_per_acre / grain_price

        return {
            "quick_estimate": True,
            "crop": crop,
            "acres": acres,
            "yield_goal": yield_goal,
            "is_irrigated": is_irrigated,
            "cost_breakdown_per_acre": costs,
            "total_cost_per_acre": round(total_per_acre, 2),
            "total_cost": round(total_cost, 2),
            "economics": {
                "grain_price": grain_price,
                "gross_revenue": round(gross_revenue, 2),
                "net_return": round(net_return, 2),
                "return_per_acre": round(net_return / acres if acres > 0 else 0, 2),
                "break_even_yield": round(break_even_yield, 1)
            },
            "optimization_potential": {
                "typical_savings_range_percent": "10-20%",
                "potential_savings_low": round(total_cost * 0.10, 2),
                "potential_savings_high": round(total_cost * 0.20, 2)
            },
            "note": "This is a quick estimate using industry averages. Use detailed analysis for accurate planning."
        }

    def compare_input_strategies(
        self,
        acres: float,
        crop: str,
        strategies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare different input strategies side-by-side

        Args:
            acres: Field size
            crop: Crop type
            strategies: List of strategy dicts with different input levels

        Returns:
            Side-by-side comparison with recommendations
        """
        comparisons = []

        for strategy in strategies:
            name = strategy.get("name", "Strategy")

            # Calculate costs for each component
            fertilizer_cost = strategy.get("fertilizer_cost_per_acre", 150) * acres
            pesticide_cost = strategy.get("pesticide_cost_per_acre", 40) * acres
            labor_cost = strategy.get("labor_cost_per_acre", 25) * acres
            irrigation_cost = strategy.get("irrigation_cost_per_acre", 0) * acres

            total_cost = fertilizer_cost + pesticide_cost + labor_cost + irrigation_cost

            # Estimate yield impact
            yield_estimate = strategy.get("expected_yield", 180)
            grain_price = 4.50 if crop.lower() == "corn" else 12.00
            gross_revenue = yield_estimate * grain_price * acres
            net_return = gross_revenue - total_cost

            comparisons.append({
                "strategy_name": name,
                "costs": {
                    "fertilizer": round(fertilizer_cost, 2),
                    "pesticides": round(pesticide_cost, 2),
                    "labor": round(labor_cost, 2),
                    "irrigation": round(irrigation_cost, 2),
                    "total": round(total_cost, 2),
                    "per_acre": round(total_cost / acres if acres > 0 else 0, 2)
                },
                "expected_yield": yield_estimate,
                "gross_revenue": round(gross_revenue, 2),
                "net_return": round(net_return, 2),
                "return_per_acre": round(net_return / acres if acres > 0 else 0, 2),
                "cost_per_bushel": round(total_cost / (yield_estimate * acres) if yield_estimate > 0 else 0, 2)
            })

        # Sort by net return
        comparisons.sort(key=lambda x: x["net_return"], reverse=True)

        best_return = comparisons[0]
        lowest_cost = min(comparisons, key=lambda x: x["costs"]["total"])

        return {
            "acres": acres,
            "crop": crop,
            "strategies_compared": len(strategies),
            "comparisons": comparisons,
            "recommendations": {
                "best_return_strategy": best_return["strategy_name"],
                "best_return_amount": best_return["net_return"],
                "lowest_cost_strategy": lowest_cost["strategy_name"],
                "lowest_cost_amount": lowest_cost["costs"]["total"],
                "return_difference": round(
                    best_return["net_return"] - comparisons[-1]["net_return"], 2
                )
            }
        }

    def generate_budget_worksheet(
        self,
        farm_profile: FarmProfile,
        include_scenarios: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a complete budget worksheet for the farm
        """
        worksheets = []

        for crop_info in farm_profile.crops:
            crop = crop_info["crop"]
            acres = crop_info.get("acres", 100)
            yield_goal = crop_info.get("yield_goal", 180 if crop == "corn" else 50)

            # Get detailed cost estimates
            worksheet = {
                "crop": crop,
                "acres": acres,
                "yield_goal": yield_goal,
                "line_items": []
            }

            # Seed costs
            seed_cost = 120 if crop == "corn" else 70
            worksheet["line_items"].append({
                "category": "Seed",
                "description": f"{crop.title()} seed",
                "cost_per_acre": seed_cost,
                "total_cost": round(seed_cost * acres, 2),
                "notes": "Based on average 2024 prices"
            })

            # Fertilizer
            if farm_profile.soil_test_results:
                fert_analysis = self.application_optimizer.optimize_fertilizer_program(
                    crop=crop,
                    yield_goal=yield_goal,
                    acres=acres,
                    soil_test_results=farm_profile.soil_test_results
                )
                fert_cost = fert_analysis["cost_summary"]["cost_per_acre"]
            else:
                fert_cost = 175 if crop == "corn" else 45

            worksheet["line_items"].append({
                "category": "Fertilizer",
                "description": "N-P-K and micronutrients",
                "cost_per_acre": round(fert_cost, 2),
                "total_cost": round(fert_cost * acres, 2),
                "notes": "Adjusted for soil test levels" if farm_profile.soil_test_results else "Industry average"
            })

            # Pesticides
            pest_cost = 45 if crop == "corn" else 35
            worksheet["line_items"].append({
                "category": "Pesticides",
                "description": "Herbicides, insecticides, fungicides",
                "cost_per_acre": pest_cost,
                "total_cost": round(pest_cost * acres, 2),
                "notes": "Estimate - varies by pressure"
            })

            # Labor
            labor_analysis = self.labor_optimizer.calculate_seasonal_labor_budget(
                total_acres=acres,
                crop=crop,
                expected_spray_applications=3,
                expected_fertilizer_applications=2
            )
            labor_cost = labor_analysis["totals"]["cost_per_acre"]

            worksheet["line_items"].append({
                "category": "Labor",
                "description": "Scouting, applications, management",
                "cost_per_acre": round(labor_cost, 2),
                "total_cost": round(labor_cost * acres, 2),
                "notes": "Includes scouting, spray, fertilizer application"
            })

            # Irrigation (if applicable)
            if farm_profile.irrigation_system:
                irr_cost = 85 if crop == "corn" else 65
                worksheet["line_items"].append({
                    "category": "Irrigation",
                    "description": f"{farm_profile.irrigation_system} system operation",
                    "cost_per_acre": irr_cost,
                    "total_cost": round(irr_cost * acres, 2),
                    "notes": "Variable and fixed costs"
                })

            # Calculate totals
            total_per_acre = sum(item["cost_per_acre"] for item in worksheet["line_items"])
            total_cost = sum(item["total_cost"] for item in worksheet["line_items"])

            worksheet["totals"] = {
                "total_cost_per_acre": round(total_per_acre, 2),
                "total_cost": round(total_cost, 2)
            }

            # Add revenue projection
            grain_price = 4.50 if crop == "corn" else 12.00
            gross_revenue = yield_goal * grain_price * acres
            worksheet["revenue_projection"] = {
                "yield_goal": yield_goal,
                "grain_price": grain_price,
                "gross_revenue": round(gross_revenue, 2),
                "net_return": round(gross_revenue - total_cost, 2),
                "return_per_acre": round((gross_revenue - total_cost) / acres if acres > 0 else 0, 2),
                "break_even_yield": round(total_per_acre / grain_price, 1)
            }

            worksheets.append(worksheet)

        # Farm total summary
        farm_total_cost = sum(w["totals"]["total_cost"] for w in worksheets)
        farm_total_revenue = sum(w["revenue_projection"]["gross_revenue"] for w in worksheets)
        farm_net_return = sum(w["revenue_projection"]["net_return"] for w in worksheets)

        result = {
            "farm_profile": {
                "total_acres": farm_profile.total_acres,
                "crops": [c["crop"] for c in farm_profile.crops],
                "irrigated": farm_profile.irrigation_system is not None
            },
            "crop_worksheets": worksheets,
            "farm_totals": {
                "total_input_cost": round(farm_total_cost, 2),
                "total_gross_revenue": round(farm_total_revenue, 2),
                "total_net_return": round(farm_net_return, 2),
                "average_cost_per_acre": round(
                    farm_total_cost / farm_profile.total_acres if farm_profile.total_acres > 0 else 0, 2
                ),
                "average_return_per_acre": round(
                    farm_net_return / farm_profile.total_acres if farm_profile.total_acres > 0 else 0, 2
                )
            }
        }

        # Add scenarios if requested
        if include_scenarios:
            result["scenarios"] = self._generate_budget_scenarios(worksheets, farm_profile)

        return result

    def _analyze_labor_costs(
        self,
        farm_profile: FarmProfile,
        season_length_days: int
    ) -> Dict[str, Any]:
        """Analyze labor costs for the farm"""
        # Create field list from crops
        fields = [
            {"name": f"{c['crop']} field", "acres": c.get("acres", 100)}
            for c in farm_profile.crops
        ]

        # Get scouting costs
        scouting = self.labor_optimizer.calculate_scouting_costs(
            fields=fields,
            scouting_frequency_days=7,
            season_length_days=season_length_days
        )

        # Get seasonal labor budget
        seasonal = self.labor_optimizer.calculate_seasonal_labor_budget(
            total_acres=farm_profile.total_acres,
            crop=farm_profile.crops[0]["crop"] if farm_profile.crops else "corn",
            season_length_days=season_length_days
        )

        total_cost = seasonal["totals"]["total_cost"]

        # Calculate potential savings
        potential_savings = 0
        for opp in seasonal.get("optimization_opportunities", []):
            if "potential_savings_percent" in opp:
                # Estimate portion of total
                potential_savings += total_cost * (opp["potential_savings_percent"] / 100) * 0.3

        return {
            "summary": {
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(seasonal["totals"]["cost_per_acre"], 2)
            },
            "breakdown": seasonal["labor_breakdown"],
            "potential_savings": round(potential_savings, 2),
            "recommendations": scouting.get("optimization_recommendations", [])[:3]
        }

    def _analyze_application_costs(self, farm_profile: FarmProfile) -> Dict[str, Any]:
        """Analyze fertilizer and pesticide application costs"""
        total_cost = 0
        potential_savings = 0
        recommendations = []

        for crop_info in farm_profile.crops:
            crop = crop_info["crop"]
            acres = crop_info.get("acres", 100)
            yield_goal = crop_info.get("yield_goal", 180 if crop == "corn" else 50)

            # Fertilizer costs
            if farm_profile.soil_test_results:
                fert_result = self.application_optimizer.optimize_fertilizer_program(
                    crop=crop,
                    yield_goal=yield_goal,
                    acres=acres,
                    soil_test_results=farm_profile.soil_test_results
                )
                fert_cost = fert_result["cost_summary"]["total_cost"]

                for opp in fert_result.get("optimization_opportunities", []):
                    potential_savings += opp.get("potential_savings_per_acre", 0) * acres
                    recommendations.append(opp["recommendation"])
            else:
                # Use defaults
                fert_cost = (175 if crop == "corn" else 45) * acres

            # Pesticide costs (estimated)
            pest_cost = (45 if crop == "corn" else 35) * acres

            total_cost += fert_cost + pest_cost

        # Add general savings estimate for pesticides
        potential_savings += total_cost * 0.10  # 10% from threshold-based decisions

        return {
            "summary": {
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(
                    total_cost / farm_profile.total_acres if farm_profile.total_acres > 0 else 0, 2
                )
            },
            "potential_savings": round(potential_savings, 2),
            "recommendations": recommendations[:5]
        }

    def _analyze_irrigation_costs(
        self,
        farm_profile: FarmProfile,
        season_length_days: int
    ) -> Dict[str, Any]:
        """Analyze irrigation costs"""
        # Use the primary crop for analysis
        crop = farm_profile.crops[0]["crop"] if farm_profile.crops else "corn"

        season_analysis = self.irrigation_optimizer.optimize_irrigation_schedule(
            crop=crop,
            acres=farm_profile.total_acres,
            irrigation_type=farm_profile.irrigation_system or "center_pivot",
            water_source=farm_profile.water_source or "groundwater_well",
            season_start=date.today(),
            season_end=date.today().replace(month=date.today().month + 4),
            expected_rainfall_inches=15
        )

        variable_cost = season_analysis["cost_analysis"]["variable_costs"]["total_variable_cost"]
        fixed_cost = season_analysis["cost_analysis"]["fixed_costs"]["total_fixed_cost"]

        # Calculate potential savings from strategies
        water_analysis = self.irrigation_optimizer.analyze_water_savings_strategies(
            current_usage_acre_inches=season_analysis["season_summary"]["gross_irrigation_need_inches"] * farm_profile.total_acres,
            acres=farm_profile.total_acres,
            irrigation_type=farm_profile.irrigation_system or "center_pivot",
            water_source=farm_profile.water_source or "groundwater_well"
        )

        potential_savings = sum(
            s.get("annual_cost_savings", 0)
            for s in water_analysis.get("water_saving_strategies", [])[:3]
        )

        return {
            "summary": {
                "variable_cost": round(variable_cost, 2),
                "fixed_cost": round(fixed_cost, 2),
                "total_cost": round(variable_cost + fixed_cost, 2),
                "cost_per_acre": round(
                    (variable_cost + fixed_cost) / farm_profile.total_acres
                    if farm_profile.total_acres > 0 else 0, 2
                )
            },
            "potential_savings": round(potential_savings, 2),
            "roi": season_analysis.get("roi_analysis", {}),
            "recommendations": [
                s["strategy"] for s in water_analysis.get("water_saving_strategies", [])[:3]
            ]
        }

    def _prioritize_recommendations(
        self,
        cost_categories: Dict[str, Any],
        priority: OptimizationPriority
    ) -> List[Dict[str, Any]]:
        """Prioritize all recommendations based on optimization priority"""
        all_recommendations = []

        # Collect all recommendations with their savings potential
        for category, data in cost_categories.items():
            for rec in data.get("recommendations", []):
                savings = data.get("potential_savings", 0) / max(len(data.get("recommendations", [])), 1)
                all_recommendations.append({
                    "category": category,
                    "recommendation": rec if isinstance(rec, str) else rec.get("recommendation", str(rec)),
                    "estimated_savings": round(savings, 2),
                    "difficulty": "Medium",  # Default
                    "priority_score": self._calculate_priority_score(
                        savings, category, priority
                    )
                })

        # Sort by priority score
        all_recommendations.sort(key=lambda x: x["priority_score"], reverse=True)

        return all_recommendations[:10]  # Top 10 recommendations

    def _calculate_priority_score(
        self,
        savings: float,
        category: str,
        priority: OptimizationPriority
    ) -> float:
        """Calculate priority score for a recommendation"""
        base_score = savings / 100  # Normalize to reasonable range

        # Adjust based on priority
        if priority == OptimizationPriority.COST_REDUCTION:
            return base_score * 1.0
        elif priority == OptimizationPriority.ROI_MAXIMIZATION:
            # Favor irrigation and application (direct yield impact)
            if category in ["irrigation", "applications"]:
                return base_score * 1.3
            return base_score * 0.8
        elif priority == OptimizationPriority.SUSTAINABILITY:
            # Favor irrigation efficiency
            if category == "irrigation":
                return base_score * 1.5
            return base_score * 1.0
        elif priority == OptimizationPriority.RISK_REDUCTION:
            # Favor consistent monitoring
            if category == "labor":
                return base_score * 1.2
            return base_score * 1.0

        return base_score

    def _create_action_plan(
        self,
        recommendations: List[Dict],
        farm_profile: FarmProfile
    ) -> List[Dict[str, Any]]:
        """Create prioritized action plan"""
        actions = []

        for i, rec in enumerate(recommendations[:5], 1):
            actions.append({
                "priority": i,
                "category": rec["category"],
                "action": rec["recommendation"],
                "estimated_savings": rec["estimated_savings"],
                "implementation": self._get_implementation_steps(rec["category"]),
                "timeline": "Within 30 days" if i <= 2 else "Within 90 days"
            })

        return actions

    def _get_implementation_steps(self, category: str) -> List[str]:
        """Get implementation steps for a category"""
        steps = {
            "labor": [
                "Review current scouting routes and frequency",
                "Identify fields that can be grouped together",
                "Consider technology (drones, sensors) for large operations"
            ],
            "applications": [
                "Get current soil tests if not recent",
                "Compare product prices from multiple suppliers",
                "Review threshold-based decision making"
            ],
            "irrigation": [
                "Install soil moisture monitoring",
                "Schedule night irrigations where possible",
                "Check system for leaks and efficiency"
            ]
        }
        return steps.get(category, ["Review current practices", "Identify inefficiencies", "Implement changes"])

    def _calculate_roi_summary(
        self,
        farm_profile: FarmProfile,
        total_cost: float,
        potential_savings: float
    ) -> Dict[str, Any]:
        """Calculate overall ROI summary"""
        # Estimate gross revenue
        total_revenue = 0
        for crop_info in farm_profile.crops:
            crop = crop_info["crop"]
            acres = crop_info.get("acres", 100)
            yield_goal = crop_info.get("yield_goal", 180 if crop == "corn" else 50)
            grain_price = 4.50 if crop == "corn" else 12.00
            total_revenue += yield_goal * grain_price * acres

        current_net = total_revenue - total_cost
        optimized_net = total_revenue - (total_cost - potential_savings)

        return {
            "current_scenario": {
                "total_input_cost": round(total_cost, 2),
                "gross_revenue": round(total_revenue, 2),
                "net_return": round(current_net, 2),
                "return_on_inputs": round(current_net / total_cost * 100 if total_cost > 0 else 0, 1)
            },
            "optimized_scenario": {
                "total_input_cost": round(total_cost - potential_savings, 2),
                "gross_revenue": round(total_revenue, 2),
                "net_return": round(optimized_net, 2),
                "return_on_inputs": round(
                    optimized_net / (total_cost - potential_savings) * 100
                    if (total_cost - potential_savings) > 0 else 0, 1
                )
            },
            "improvement": {
                "cost_reduction": round(potential_savings, 2),
                "net_return_increase": round(optimized_net - current_net, 2),
                "roi_improvement_percent": round(
                    ((optimized_net - current_net) / max(current_net, 1)) * 100, 1
                )
            }
        }

    def _generate_budget_scenarios(
        self,
        worksheets: List[Dict],
        farm_profile: FarmProfile
    ) -> Dict[str, Any]:
        """Generate alternative budget scenarios"""
        base_cost = sum(w["totals"]["total_cost"] for w in worksheets)
        base_revenue = sum(w["revenue_projection"]["gross_revenue"] for w in worksheets)

        scenarios = {
            "conservative": {
                "description": "Reduced inputs, lower yield expectation",
                "cost_adjustment": 0.85,  # 15% less inputs
                "yield_adjustment": 0.90,  # 10% lower yield
            },
            "aggressive": {
                "description": "Maximum inputs for maximum yield",
                "cost_adjustment": 1.20,  # 20% more inputs
                "yield_adjustment": 1.10,  # 10% higher yield potential
            },
            "optimized": {
                "description": "Targeted inputs based on analysis",
                "cost_adjustment": 0.90,  # 10% less through optimization
                "yield_adjustment": 1.00,  # Maintain yield
            }
        }

        results = {}
        for name, scenario in scenarios.items():
            adjusted_cost = base_cost * scenario["cost_adjustment"]
            adjusted_revenue = base_revenue * scenario["yield_adjustment"]
            net_return = adjusted_revenue - adjusted_cost

            results[name] = {
                "description": scenario["description"],
                "total_cost": round(adjusted_cost, 2),
                "gross_revenue": round(adjusted_revenue, 2),
                "net_return": round(net_return, 2),
                "return_per_acre": round(
                    net_return / farm_profile.total_acres if farm_profile.total_acres > 0 else 0, 2
                )
            }

        return results


# Singleton instance
_master_optimizer = None

def get_input_cost_optimizer(**kwargs) -> InputCostOptimizer:
    """Get or create master optimizer instance"""
    global _master_optimizer
    if _master_optimizer is None:
        _master_optimizer = InputCostOptimizer(**kwargs)
    return _master_optimizer


# Example usage
if __name__ == "__main__":
    optimizer = InputCostOptimizer()

    # Create a farm profile
    farm = FarmProfile(
        total_acres=800,
        crops=[
            {"crop": "corn", "acres": 500, "yield_goal": 200},
            {"crop": "soybean", "acres": 300, "yield_goal": 55}
        ],
        irrigation_system="center_pivot",
        water_source="groundwater_well",
        soil_test_results={
            "P": 22,
            "K": 155,
            "pH": 6.5,
            "OM": 3.0
        }
    )

    # Run complete analysis
    print("=== COMPLETE FARM INPUT COST ANALYSIS ===")
    analysis = optimizer.analyze_complete_farm_costs(farm)

    print(f"\nFarm Summary:")
    print(f"  Total Acres: {analysis['farm_summary']['total_acres']}")
    print(f"  Crops: {', '.join(analysis['farm_summary']['crops'])}")
    print(f"  Irrigated: {analysis['farm_summary']['has_irrigation']}")

    print(f"\n=== COST SUMMARY ===")
    costs = analysis['total_costs']
    print(f"Total Input Cost: ${costs['total_input_cost']:,.2f}")
    print(f"Cost per Acre: ${costs['cost_per_acre']}")
    print(f"Potential Savings: ${costs['total_potential_savings']:,.2f} ({costs['potential_savings_percent']}%)")

    print(f"\n=== TOP RECOMMENDATIONS ===")
    for i, rec in enumerate(analysis['optimization_opportunities'][:5], 1):
        print(f"{i}. [{rec['category'].upper()}] {rec['recommendation']}")
        print(f"   Estimated Savings: ${rec['estimated_savings']}")

    print(f"\n=== ROI ANALYSIS ===")
    roi = analysis['roi_summary']
    print(f"Current Net Return: ${roi['current_scenario']['net_return']:,.2f}")
    print(f"Optimized Net Return: ${roi['optimized_scenario']['net_return']:,.2f}")
    print(f"Potential Improvement: ${roi['improvement']['net_return_increase']:,.2f}")

    # Quick estimate example
    print("\n\n=== QUICK COST ESTIMATE ===")
    quick = optimizer.quick_cost_estimate(
        acres=160,
        crop="corn",
        is_irrigated=True,
        yield_goal=200
    )
    print(f"Crop: {quick['crop']}")
    print(f"Total Cost: ${quick['total_cost']:,.2f}")
    print(f"Cost per Acre: ${quick['total_cost_per_acre']}")
    print(f"Break-even Yield: {quick['economics']['break_even_yield']} bu/acre")
