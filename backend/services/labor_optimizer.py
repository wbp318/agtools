"""
Labor Cost Optimization Module
Helps farmers reduce labor costs through efficient scheduling and resource allocation
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class LaborType(str, Enum):
    SCOUTING = "scouting"
    SPRAYING = "spraying"
    FERTILIZING = "fertilizing"
    IRRIGATION_MGMT = "irrigation_management"
    EQUIPMENT_MAINTENANCE = "equipment_maintenance"
    GENERAL_FIELD_WORK = "general_field_work"


# Regional labor rates ($/hour) - configurable per operation
DEFAULT_LABOR_RATES = {
    "farm_hand": 15.00,
    "equipment_operator": 20.00,
    "certified_scout": 25.00,
    "agronomist": 75.00,
    "spray_technician": 22.00,
    "irrigation_tech": 20.00,
    "manager": 35.00
}

# Time estimates for common tasks (hours per acre or per task)
TASK_TIME_ESTIMATES = {
    "scouting": {
        "per_acre": 0.05,  # 3 minutes per acre average
        "min_per_field": 0.5,  # Minimum 30 min per field
        "travel_base": 0.25  # 15 min base travel time
    },
    "spray_application": {
        "small_sprayer_60ft": 0.025,  # 1.5 min per acre (40 ac/hr)
        "large_sprayer_90ft": 0.017,  # 1 min per acre (60 ac/hr)
        "self_propelled_120ft": 0.012,  # 45 sec per acre (80 ac/hr)
        "aerial": 0.005,  # 18 sec per acre (200 ac/hr)
        "setup_time": 0.5,  # 30 min setup per spray session
        "fill_time_per_tank": 0.25  # 15 min per tank fill
    },
    "fertilizer_application": {
        "spreader_per_acre": 0.02,  # 1.2 min per acre
        "side_dress_per_acre": 0.033,  # 2 min per acre
        "setup_time": 0.5
    },
    "irrigation": {
        "pivot_check_per_system": 0.5,  # 30 min per pivot
        "drip_maintenance_per_acre": 0.1,
        "pump_check": 0.25
    }
}


@dataclass
class LaborTask:
    """Represents a single labor task"""
    task_type: LaborType
    field_name: str
    acres: float
    worker_type: str
    estimated_hours: float
    hourly_rate: float
    total_cost: float
    priority: int  # 1=urgent, 2=soon, 3=routine
    optimal_timing: Optional[str] = None


class LaborOptimizer:
    """
    Optimizes farm labor costs through:
    - Efficient route planning
    - Task batching
    - Optimal scheduling
    - Worker utilization tracking
    """

    def __init__(self, custom_labor_rates: Optional[Dict[str, float]] = None):
        self.labor_rates = {**DEFAULT_LABOR_RATES}
        if custom_labor_rates:
            self.labor_rates.update(custom_labor_rates)

    def calculate_scouting_costs(
        self,
        fields: List[Dict[str, Any]],
        scouting_frequency_days: int = 7,
        season_length_days: int = 120
    ) -> Dict[str, Any]:
        """
        Calculate scouting labor costs for the season

        Args:
            fields: List of field dicts with 'name', 'acres', 'location' keys
            scouting_frequency_days: How often to scout each field
            season_length_days: Growing season length

        Returns:
            Cost breakdown and optimization recommendations
        """
        total_acres = sum(f.get('acres', 0) for f in fields)
        total_fields = len(fields)
        scouting_trips = season_length_days // scouting_frequency_days

        # Calculate time per scouting session
        time_estimates = TASK_TIME_ESTIMATES["scouting"]

        field_details = []
        total_scouting_hours = 0

        for field in fields:
            acres = field.get('acres', 80)
            field_time = max(
                acres * time_estimates['per_acre'],
                time_estimates['min_per_field']
            )
            # Add travel time (could be optimized with route planning)
            field_time += time_estimates['travel_base']

            field_details.append({
                "field_name": field.get('name', 'Unknown'),
                "acres": acres,
                "time_per_visit_hours": round(field_time, 2),
                "season_visits": scouting_trips,
                "total_season_hours": round(field_time * scouting_trips, 2)
            })
            total_scouting_hours += field_time * scouting_trips

        # Cost calculation
        scout_rate = self.labor_rates.get('certified_scout', 25.00)
        total_scouting_cost = total_scouting_hours * scout_rate
        cost_per_acre = total_scouting_cost / total_acres if total_acres > 0 else 0

        # Optimization recommendations
        recommendations = self._generate_scouting_recommendations(
            fields, total_acres, scouting_frequency_days, cost_per_acre
        )

        return {
            "summary": {
                "total_fields": total_fields,
                "total_acres": total_acres,
                "scouting_frequency_days": scouting_frequency_days,
                "total_scouting_trips": scouting_trips,
                "total_hours_per_season": round(total_scouting_hours, 1),
                "hourly_rate": scout_rate,
                "total_cost": round(total_scouting_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2)
            },
            "field_breakdown": field_details,
            "optimization_recommendations": recommendations,
            "potential_savings": self._calculate_scouting_savings(
                fields, total_scouting_cost, scouting_frequency_days
            )
        }

    def calculate_application_labor(
        self,
        acres: float,
        application_type: str,
        equipment_type: str = "self_propelled_120ft",
        tank_capacity_gallons: float = 1200,
        application_rate_gpa: float = 15,
        custom_application: bool = False,
        custom_rate_per_acre: float = 7.50
    ) -> Dict[str, Any]:
        """
        Calculate labor costs for spray/fertilizer applications

        Args:
            acres: Total acres to cover
            application_type: 'spray' or 'fertilizer'
            equipment_type: Type of equipment (affects speed)
            tank_capacity_gallons: Sprayer tank capacity
            application_rate_gpa: Gallons per acre
            custom_application: Whether using custom applicator
            custom_rate_per_acre: Custom applicator rate

        Returns:
            Labor cost breakdown
        """
        if custom_application:
            return {
                "summary": {
                    "acres": acres,
                    "method": "custom_application",
                    "cost_per_acre": custom_rate_per_acre,
                    "total_cost": round(acres * custom_rate_per_acre, 2),
                    "labor_hours": 0,
                    "your_time_investment": "Minimal - ordering and field access coordination"
                },
                "comparison": self._compare_custom_vs_self(
                    acres, custom_rate_per_acre, equipment_type
                )
            }

        # Self-application calculations
        time_estimates = TASK_TIME_ESTIMATES["spray_application"]
        time_per_acre = time_estimates.get(equipment_type, 0.017)

        # Calculate number of tank fills needed
        acres_per_tank = tank_capacity_gallons / application_rate_gpa
        tank_fills = (acres / acres_per_tank) if acres_per_tank > 0 else 1

        # Total time calculation
        field_time = acres * time_per_acre
        setup_time = time_estimates['setup_time']
        fill_time = tank_fills * time_estimates['fill_time_per_tank']
        total_hours = field_time + setup_time + fill_time

        # Labor cost
        operator_rate = self.labor_rates.get('equipment_operator', 20.00)
        labor_cost = total_hours * operator_rate

        # Equipment operating costs (fuel, wear)
        fuel_cost_per_hour = 25.00  # Diesel consumption estimate
        equipment_cost = total_hours * fuel_cost_per_hour

        total_cost = labor_cost + equipment_cost
        cost_per_acre = total_cost / acres if acres > 0 else 0

        return {
            "summary": {
                "acres": acres,
                "equipment": equipment_type,
                "method": "self_application",
                "field_time_hours": round(field_time, 2),
                "setup_time_hours": round(setup_time, 2),
                "fill_time_hours": round(fill_time, 2),
                "total_hours": round(total_hours, 2),
                "tank_fills_required": round(tank_fills, 1),
                "labor_cost": round(labor_cost, 2),
                "fuel_equipment_cost": round(equipment_cost, 2),
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2)
            },
            "efficiency_metrics": {
                "acres_per_hour": round(1 / time_per_acre, 1),
                "cost_efficiency": "High" if cost_per_acre < 6 else "Medium" if cost_per_acre < 10 else "Review needed"
            },
            "comparison": self._compare_custom_vs_self(
                acres, custom_rate_per_acre, equipment_type
            )
        }

    def optimize_field_route(
        self,
        fields: List[Dict[str, Any]],
        start_location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Optimize travel route between fields to minimize labor time

        Simple nearest-neighbor algorithm (can be upgraded to more sophisticated)
        """
        if not fields:
            return {"error": "No fields provided"}

        # Simple distance-based optimization
        # In production, would use actual GPS coordinates and road distances
        remaining = fields.copy()
        route = []
        current_location = start_location or {"lat": 0, "lon": 0}
        total_travel_time = 0

        while remaining:
            # Find nearest field (simplified - using index as proxy for distance)
            nearest_idx = 0
            route.append(remaining.pop(nearest_idx))

        # Calculate potential savings
        unoptimized_time = len(fields) * 0.5  # 30 min between each field
        optimized_time = len(fields) * 0.33  # Optimized: 20 min average
        time_saved = unoptimized_time - optimized_time

        travel_rate = self.labor_rates.get('equipment_operator', 20.00)

        return {
            "optimized_route": [f.get('name', f'Field {i}') for i, f in enumerate(route)],
            "estimated_travel_hours": round(optimized_time, 2),
            "travel_cost": round(optimized_time * travel_rate, 2),
            "time_saved_hours": round(time_saved, 2),
            "cost_saved": round(time_saved * travel_rate, 2),
            "recommendation": "Group nearby fields together for same-day operations"
        }

    def calculate_seasonal_labor_budget(
        self,
        total_acres: float,
        crop: str,
        expected_spray_applications: int = 3,
        expected_fertilizer_applications: int = 2,
        scouting_frequency_days: int = 7,
        season_length_days: int = 120
    ) -> Dict[str, Any]:
        """
        Calculate total seasonal labor budget for field operations
        """
        # Scouting costs
        scouting_trips = season_length_days // scouting_frequency_days
        scouting_hours = total_acres * 0.05 * scouting_trips
        scouting_cost = scouting_hours * self.labor_rates.get('certified_scout', 25.00)

        # Application costs (assuming self-application)
        spray_hours = total_acres * 0.017 * expected_spray_applications
        spray_labor = spray_hours * self.labor_rates.get('equipment_operator', 20.00)

        fertilizer_hours = total_acres * 0.025 * expected_fertilizer_applications
        fertilizer_labor = fertilizer_hours * self.labor_rates.get('equipment_operator', 20.00)

        # Equipment maintenance (10% of operating hours)
        total_equipment_hours = spray_hours + fertilizer_hours
        maintenance_hours = total_equipment_hours * 0.10
        maintenance_cost = maintenance_hours * self.labor_rates.get('equipment_operator', 20.00)

        # Management/planning time
        management_hours = total_acres * 0.005 * season_length_days / 30  # per month
        management_cost = management_hours * self.labor_rates.get('manager', 35.00)

        total_hours = scouting_hours + spray_hours + fertilizer_hours + maintenance_hours + management_hours
        total_cost = scouting_cost + spray_labor + fertilizer_labor + maintenance_cost + management_cost

        return {
            "crop": crop,
            "total_acres": total_acres,
            "season_length_days": season_length_days,
            "labor_breakdown": {
                "scouting": {
                    "hours": round(scouting_hours, 1),
                    "cost": round(scouting_cost, 2)
                },
                "spray_applications": {
                    "applications": expected_spray_applications,
                    "hours": round(spray_hours, 1),
                    "cost": round(spray_labor, 2)
                },
                "fertilizer_applications": {
                    "applications": expected_fertilizer_applications,
                    "hours": round(fertilizer_hours, 1),
                    "cost": round(fertilizer_labor, 2)
                },
                "equipment_maintenance": {
                    "hours": round(maintenance_hours, 1),
                    "cost": round(maintenance_cost, 2)
                },
                "management_planning": {
                    "hours": round(management_hours, 1),
                    "cost": round(management_cost, 2)
                }
            },
            "totals": {
                "total_hours": round(total_hours, 1),
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(total_cost / total_acres if total_acres > 0 else 0, 2)
            },
            "optimization_opportunities": self._identify_labor_optimizations(
                total_acres, scouting_cost, spray_labor, fertilizer_labor
            )
        }

    def _generate_scouting_recommendations(
        self,
        fields: List[Dict],
        total_acres: float,
        frequency: int,
        cost_per_acre: float
    ) -> List[str]:
        """Generate scouting optimization recommendations"""
        recommendations = []

        if frequency < 7:
            recommendations.append(
                f"Consider reducing scouting frequency from every {frequency} days to "
                "7-10 days during low-pressure periods to reduce costs by 20-30%"
            )

        if len(fields) > 5:
            recommendations.append(
                "With multiple fields, group nearby fields into scouting routes "
                "to reduce travel time by up to 25%"
            )

        if cost_per_acre > 3.00:
            recommendations.append(
                "Scouting costs above $3/acre - consider zone-based scouting "
                "focusing on historically problematic areas"
            )

        if total_acres > 500:
            recommendations.append(
                "For large operations, consider drone scouting for initial "
                "surveillance with targeted ground-truthing to reduce labor 40-50%"
            )

        recommendations.append(
            "Use threshold-based scouting: increase frequency when pest "
            "pressure is detected, reduce during clean periods"
        )

        return recommendations

    def _calculate_scouting_savings(
        self,
        fields: List[Dict],
        current_cost: float,
        current_frequency: int
    ) -> Dict[str, Any]:
        """Calculate potential savings from scouting optimizations"""
        # Scenario 1: Reduce frequency
        reduced_freq_cost = current_cost * (current_frequency / 10)
        freq_savings = current_cost - reduced_freq_cost

        # Scenario 2: Zone-based scouting (30% reduction)
        zone_cost = current_cost * 0.70
        zone_savings = current_cost - zone_cost

        # Scenario 3: Drone-assisted (50% reduction for large operations)
        total_acres = sum(f.get('acres', 0) for f in fields)
        if total_acres > 500:
            drone_cost = current_cost * 0.50
            drone_savings = current_cost - drone_cost
        else:
            drone_savings = 0

        return {
            "current_annual_cost": round(current_cost, 2),
            "scenario_reduced_frequency": {
                "new_cost": round(reduced_freq_cost, 2),
                "savings": round(freq_savings, 2),
                "description": "Scout every 10 days instead of current frequency"
            },
            "scenario_zone_based": {
                "new_cost": round(zone_cost, 2),
                "savings": round(zone_savings, 2),
                "description": "Focus on high-risk zones, reduce whole-field walks"
            },
            "scenario_drone_assisted": {
                "new_cost": round(current_cost - drone_savings, 2),
                "savings": round(drone_savings, 2),
                "description": "Use drone imagery for initial surveillance (500+ acres)"
            }
        }

    def _compare_custom_vs_self(
        self,
        acres: float,
        custom_rate: float,
        equipment_type: str
    ) -> Dict[str, Any]:
        """Compare custom application vs self-application costs"""
        custom_cost = acres * custom_rate

        # Self-application estimate
        time_per_acre = TASK_TIME_ESTIMATES["spray_application"].get(equipment_type, 0.017)
        hours = acres * time_per_acre + 0.5  # Plus setup
        self_labor = hours * self.labor_rates.get('equipment_operator', 20.00)
        self_fuel = hours * 25.00
        self_cost = self_labor + self_fuel

        difference = custom_cost - self_cost

        return {
            "custom_application_cost": round(custom_cost, 2),
            "self_application_cost": round(self_cost, 2),
            "difference": round(difference, 2),
            "recommendation": (
                "Self-application saves money" if difference > 0
                else "Custom application more economical (consider equipment/time value)"
            ),
            "break_even_acres": round(
                (0.5 * 45) / (custom_rate - (time_per_acre * 45)), 1  # Where setup time becomes worth it
            ) if custom_rate > (time_per_acre * 45) else "N/A"
        }

    def _identify_labor_optimizations(
        self,
        acres: float,
        scouting_cost: float,
        spray_cost: float,
        fertilizer_cost: float
    ) -> List[Dict[str, Any]]:
        """Identify specific labor optimization opportunities"""
        optimizations = []

        # Check scouting efficiency
        scouting_per_acre = scouting_cost / acres if acres > 0 else 0
        if scouting_per_acre > 2.50:
            optimizations.append({
                "area": "Scouting",
                "current_cost_per_acre": round(scouting_per_acre, 2),
                "potential_savings_percent": 25,
                "action": "Implement zone-based or drone-assisted scouting"
            })

        # Check application efficiency
        spray_per_acre = spray_cost / acres if acres > 0 else 0
        if spray_per_acre > 5.00:
            optimizations.append({
                "area": "Spray Applications",
                "current_cost_per_acre": round(spray_per_acre, 2),
                "potential_savings_percent": 20,
                "action": "Upgrade to larger boom width or consider custom application"
            })

        # Check fertilizer efficiency
        fert_per_acre = fertilizer_cost / acres if acres > 0 else 0
        if fert_per_acre > 4.00:
            optimizations.append({
                "area": "Fertilizer Applications",
                "current_cost_per_acre": round(fert_per_acre, 2),
                "potential_savings_percent": 15,
                "action": "Combine applications or use variable rate to reduce passes"
            })

        # General recommendations based on scale
        if acres > 1000:
            optimizations.append({
                "area": "Scale Efficiency",
                "recommendation": "Large operation - ensure equipment capacity matches scale",
                "action": "Review custom vs owned equipment economics"
            })
        elif acres < 200:
            optimizations.append({
                "area": "Scale Efficiency",
                "recommendation": "Smaller operation - custom services may be more economical",
                "action": "Compare custom application quotes to ownership costs"
            })

        return optimizations


# Singleton instance
_optimizer = None

def get_labor_optimizer(custom_rates: Optional[Dict[str, float]] = None) -> LaborOptimizer:
    """Get or create labor optimizer instance"""
    global _optimizer
    if _optimizer is None or custom_rates:
        _optimizer = LaborOptimizer(custom_rates)
    return _optimizer


# Example usage
if __name__ == "__main__":
    optimizer = LaborOptimizer()

    # Example: Calculate scouting costs
    fields = [
        {"name": "North 80", "acres": 80},
        {"name": "South 160", "acres": 160},
        {"name": "River Bottom", "acres": 120},
        {"name": "Home Farm", "acres": 200}
    ]

    scouting = optimizer.calculate_scouting_costs(fields, scouting_frequency_days=7)

    print("=== SCOUTING LABOR ANALYSIS ===")
    print(f"Total Acres: {scouting['summary']['total_acres']}")
    print(f"Total Season Hours: {scouting['summary']['total_hours_per_season']}")
    print(f"Total Cost: ${scouting['summary']['total_cost']}")
    print(f"Cost per Acre: ${scouting['summary']['cost_per_acre']}")

    print("\n=== OPTIMIZATION RECOMMENDATIONS ===")
    for rec in scouting['optimization_recommendations']:
        print(f"• {rec}")

    print("\n=== POTENTIAL SAVINGS ===")
    savings = scouting['potential_savings']
    print(f"Zone-based scouting could save: ${savings['scenario_zone_based']['savings']}")

    # Example: Calculate application labor
    print("\n\n=== SPRAY APPLICATION LABOR ===")
    spray = optimizer.calculate_application_labor(
        acres=500,
        application_type="spray",
        equipment_type="self_propelled_120ft"
    )
    print(f"Total Hours: {spray['summary']['total_hours']}")
    print(f"Total Cost: ${spray['summary']['total_cost']}")
    print(f"Acres per Hour: {spray['efficiency_metrics']['acres_per_hour']}")
