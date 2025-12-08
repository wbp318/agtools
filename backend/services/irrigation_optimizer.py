"""
Irrigation Optimization Module
Helps farmers optimize water usage, timing, and costs for irrigated crops
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum
import math


class IrrigationType(str, Enum):
    CENTER_PIVOT = "center_pivot"
    LINEAR_MOVE = "linear_move"
    DRIP = "drip"
    FURROW = "furrow"
    FLOOD = "flood"
    SUBSURFACE_DRIP = "subsurface_drip"
    TRAVELING_GUN = "traveling_gun"


class WaterSource(str, Enum):
    GROUNDWATER_WELL = "groundwater_well"
    SURFACE_WATER = "surface_water"
    MUNICIPAL = "municipal"
    RECYCLED = "recycled"


# Crop water use coefficients (inches of water per growing degree day)
CROP_WATER_USE = {
    "corn": {
        "peak_daily_et": 0.35,  # inches per day at peak
        "seasonal_water_need": 24,  # inches total
        "critical_stages": ["VT", "R1", "R2", "R3"],  # Stages where stress is most damaging
        "kc_coefficients": {  # Crop coefficients by growth stage
            "VE": 0.30,
            "V6": 0.50,
            "V12": 0.80,
            "VT": 1.15,
            "R1": 1.20,
            "R2": 1.15,
            "R3": 1.05,
            "R4": 0.90,
            "R5": 0.70,
            "R6": 0.40
        }
    },
    "soybean": {
        "peak_daily_et": 0.30,
        "seasonal_water_need": 20,
        "critical_stages": ["R3", "R4", "R5"],
        "kc_coefficients": {
            "VC": 0.35,
            "V3": 0.50,
            "V6": 0.75,
            "R1": 1.00,
            "R2": 1.10,
            "R3": 1.15,
            "R4": 1.10,
            "R5": 0.90,
            "R6": 0.50
        }
    }
}

# Irrigation system efficiency ratings
SYSTEM_EFFICIENCY = {
    "center_pivot": {
        "application_efficiency": 0.85,  # 85% of water reaches root zone
        "distribution_uniformity": 0.90,
        "energy_use_per_acre_inch": 15.0,  # kWh per acre-inch
        "typical_flow_gpm": 800,
        "maintenance_annual_per_acre": 8.00
    },
    "linear_move": {
        "application_efficiency": 0.87,
        "distribution_uniformity": 0.92,
        "energy_use_per_acre_inch": 14.0,
        "typical_flow_gpm": 600,
        "maintenance_annual_per_acre": 10.00
    },
    "subsurface_drip": {
        "application_efficiency": 0.95,
        "distribution_uniformity": 0.95,
        "energy_use_per_acre_inch": 8.0,
        "typical_flow_gpm": 200,
        "maintenance_annual_per_acre": 25.00
    },
    "drip": {
        "application_efficiency": 0.90,
        "distribution_uniformity": 0.90,
        "energy_use_per_acre_inch": 10.0,
        "typical_flow_gpm": 150,
        "maintenance_annual_per_acre": 20.00
    },
    "furrow": {
        "application_efficiency": 0.60,
        "distribution_uniformity": 0.70,
        "energy_use_per_acre_inch": 5.0,
        "typical_flow_gpm": 1500,
        "maintenance_annual_per_acre": 3.00
    },
    "flood": {
        "application_efficiency": 0.50,
        "distribution_uniformity": 0.60,
        "energy_use_per_acre_inch": 4.0,
        "typical_flow_gpm": 2000,
        "maintenance_annual_per_acre": 2.00
    }
}

# Water costs by source
WATER_COSTS = {
    "groundwater_well": {
        "pumping_cost_per_acre_inch": 4.50,  # Energy cost to pump
        "water_right_annual_per_acre": 15.00,  # Permit/rights cost
        "well_maintenance_annual": 500.00
    },
    "surface_water": {
        "water_cost_per_acre_inch": 2.50,  # District delivery charge
        "assessment_annual_per_acre": 25.00,
        "infrastructure_fee_annual": 200.00
    },
    "municipal": {
        "water_cost_per_acre_inch": 12.00,  # Treated water is expensive
        "connection_fee_annual": 150.00
    }
}


@dataclass
class IrrigationSchedule:
    """Represents a single irrigation event"""
    date: date
    amount_inches: float
    duration_hours: float
    cost: float
    reason: str
    growth_stage: Optional[str] = None


class IrrigationOptimizer:
    """
    Optimizes irrigation decisions based on:
    - Crop water needs by growth stage
    - Soil moisture levels
    - Weather forecasts (ET and rainfall)
    - Water costs and availability
    - System efficiency
    """

    def __init__(
        self,
        custom_water_costs: Optional[Dict] = None,
        electricity_rate_per_kwh: float = 0.10
    ):
        self.water_costs = {**WATER_COSTS}
        if custom_water_costs:
            for source, costs in custom_water_costs.items():
                if source in self.water_costs:
                    self.water_costs[source].update(costs)
        self.electricity_rate = electricity_rate_per_kwh

    def calculate_crop_water_need(
        self,
        crop: str,
        growth_stage: str,
        reference_et: float,
        recent_rainfall_inches: float = 0,
        soil_moisture_percent: float = 50
    ) -> Dict[str, Any]:
        """
        Calculate current crop water need

        Args:
            crop: 'corn' or 'soybean'
            growth_stage: Current growth stage
            reference_et: Reference evapotranspiration (inches/day)
            recent_rainfall_inches: Rainfall in last 7 days
            soil_moisture_percent: Current soil moisture (0-100)

        Returns:
            Water need analysis and irrigation recommendation
        """
        crop_lower = crop.lower()
        crop_data = CROP_WATER_USE.get(crop_lower, CROP_WATER_USE['corn'])

        # Get crop coefficient for growth stage
        kc = crop_data['kc_coefficients'].get(growth_stage, 0.8)

        # Calculate crop ET
        crop_et = reference_et * kc

        # Determine if irrigation is needed
        effective_rainfall = recent_rainfall_inches * 0.75  # 75% effectiveness
        net_water_need = crop_et * 7 - effective_rainfall  # Weekly need

        # Soil moisture factor
        if soil_moisture_percent > 70:
            irrigation_urgency = "Low"
            recommended_amount = max(0, net_water_need * 0.5)
        elif soil_moisture_percent > 50:
            irrigation_urgency = "Medium"
            recommended_amount = net_water_need
        else:
            irrigation_urgency = "High"
            recommended_amount = net_water_need * 1.2

        # Critical stage check
        is_critical = growth_stage in crop_data['critical_stages']
        if is_critical and soil_moisture_percent < 60:
            irrigation_urgency = "Critical"
            recommended_amount *= 1.1

        return {
            "crop": crop,
            "growth_stage": growth_stage,
            "crop_coefficient": kc,
            "reference_et_in_per_day": reference_et,
            "crop_et_in_per_day": round(crop_et, 3),
            "weekly_crop_water_use": round(crop_et * 7, 2),
            "effective_rainfall": round(effective_rainfall, 2),
            "net_water_need_inches": round(net_water_need, 2),
            "current_soil_moisture_percent": soil_moisture_percent,
            "is_critical_stage": is_critical,
            "irrigation_urgency": irrigation_urgency,
            "recommended_irrigation_inches": round(max(0, recommended_amount), 2),
            "recommendation": self._generate_irrigation_recommendation(
                irrigation_urgency, recommended_amount, is_critical, growth_stage
            )
        }

    def calculate_irrigation_costs(
        self,
        acres: float,
        inches_to_apply: float,
        irrigation_type: str,
        water_source: str,
        pumping_depth_ft: float = 150
    ) -> Dict[str, Any]:
        """
        Calculate total cost of an irrigation event

        Args:
            acres: Field size
            inches_to_apply: Amount of water to apply
            irrigation_type: Type of irrigation system
            water_source: Source of water
            pumping_depth_ft: Depth to water (for wells)

        Returns:
            Detailed cost breakdown
        """
        system = SYSTEM_EFFICIENCY.get(irrigation_type, SYSTEM_EFFICIENCY['center_pivot'])
        water_cost_data = self.water_costs.get(water_source, WATER_COSTS['groundwater_well'])

        # Account for system efficiency - need to pump more to apply target
        gross_application = inches_to_apply / system['application_efficiency']

        # Water volume calculations
        acre_inches = gross_application * acres
        gallons = acre_inches * 27154  # gallons per acre-inch

        # Energy cost (pumping)
        if water_source == "groundwater_well":
            # Energy to lift water depends on depth
            # Formula: kWh = (GPM × Head × 0.746) / (3960 × pump_efficiency)
            pump_efficiency = 0.65
            energy_factor = pumping_depth_ft / 150  # Normalize to 150 ft standard
            kwh_per_acre_inch = system['energy_use_per_acre_inch'] * energy_factor
            energy_cost = acre_inches * kwh_per_acre_inch * self.electricity_rate
        else:
            energy_cost = acre_inches * system['energy_use_per_acre_inch'] * 0.5 * self.electricity_rate

        # Water cost
        if water_source == "groundwater_well":
            water_cost = water_cost_data['pumping_cost_per_acre_inch'] * acre_inches
        elif water_source == "surface_water":
            water_cost = water_cost_data['water_cost_per_acre_inch'] * acre_inches
        else:
            water_cost = water_cost_data.get('water_cost_per_acre_inch', 5.00) * acre_inches

        # Labor cost (system monitoring)
        labor_hours = 0.5 + (acres / 200) * 0.25  # Base + scale factor
        labor_cost = labor_hours * 20.00  # $20/hr

        # Equipment wear
        equipment_cost = acres * 0.50  # $0.50/acre per irrigation

        total_cost = energy_cost + water_cost + labor_cost + equipment_cost
        cost_per_acre = total_cost / acres if acres > 0 else 0
        cost_per_acre_inch = total_cost / acre_inches if acre_inches > 0 else 0

        return {
            "irrigation_details": {
                "target_application_inches": inches_to_apply,
                "gross_application_inches": round(gross_application, 2),
                "system_efficiency_percent": system['application_efficiency'] * 100,
                "total_acre_inches": round(acre_inches, 1),
                "total_gallons": round(gallons, 0)
            },
            "cost_breakdown": {
                "energy_cost": round(energy_cost, 2),
                "water_cost": round(water_cost, 2),
                "labor_cost": round(labor_cost, 2),
                "equipment_wear": round(equipment_cost, 2),
                "total_cost": round(total_cost, 2)
            },
            "unit_costs": {
                "cost_per_acre": round(cost_per_acre, 2),
                "cost_per_acre_inch": round(cost_per_acre_inch, 2),
                "cost_per_1000_gallons": round(total_cost / (gallons / 1000) if gallons > 0 else 0, 2)
            },
            "system_info": {
                "irrigation_type": irrigation_type,
                "water_source": water_source,
                "pumping_depth_ft": pumping_depth_ft if water_source == "groundwater_well" else "N/A"
            }
        }

    def optimize_irrigation_schedule(
        self,
        crop: str,
        acres: float,
        irrigation_type: str,
        water_source: str,
        season_start: date,
        season_end: date,
        expected_rainfall_inches: float,
        soil_water_holding_capacity: float = 2.0,
        pumping_depth_ft: float = 150
    ) -> Dict[str, Any]:
        """
        Create optimized irrigation schedule for the season

        Args:
            crop: Crop type
            acres: Field size
            irrigation_type: Irrigation system type
            water_source: Water source
            season_start: Start of irrigation season
            season_end: End of irrigation season
            expected_rainfall_inches: Expected total rainfall
            soil_water_holding_capacity: Inches of water soil can hold
            pumping_depth_ft: Well depth

        Returns:
            Optimized season schedule with costs
        """
        crop_data = CROP_WATER_USE.get(crop.lower(), CROP_WATER_USE['corn'])
        system = SYSTEM_EFFICIENCY.get(irrigation_type, SYSTEM_EFFICIENCY['center_pivot'])

        # Calculate season water need
        seasonal_et = crop_data['seasonal_water_need']
        effective_rainfall = expected_rainfall_inches * 0.70  # 70% effective
        net_irrigation_need = seasonal_et - effective_rainfall

        # Account for efficiency
        gross_irrigation_need = net_irrigation_need / system['application_efficiency']

        # Calculate number of irrigations
        # Typical application is 0.75-1.25 inches per event
        optimal_application = min(soil_water_holding_capacity * 0.5, 1.0)
        num_irrigations = math.ceil(gross_irrigation_need / optimal_application)

        # Calculate season costs
        season_days = (season_end - season_start).days

        # Water costs
        total_acre_inches = gross_irrigation_need * acres
        cost_per_event = self.calculate_irrigation_costs(
            acres, optimal_application, irrigation_type, water_source, pumping_depth_ft
        )

        total_variable_cost = cost_per_event['cost_breakdown']['total_cost'] * num_irrigations

        # Fixed annual costs
        fixed_costs = self._calculate_annual_fixed_costs(
            acres, irrigation_type, water_source
        )

        total_season_cost = total_variable_cost + fixed_costs['total_fixed_cost']
        cost_per_acre = total_season_cost / acres if acres > 0 else 0

        # Generate schedule recommendations
        schedule = self._generate_irrigation_schedule(
            crop, season_start, season_end, num_irrigations, optimal_application
        )

        # ROI analysis
        roi = self._calculate_irrigation_roi(
            crop, acres, total_season_cost, net_irrigation_need
        )

        return {
            "season_summary": {
                "crop": crop,
                "acres": acres,
                "season_length_days": season_days,
                "seasonal_crop_et_inches": seasonal_et,
                "expected_effective_rainfall_inches": round(effective_rainfall, 1),
                "net_irrigation_need_inches": round(net_irrigation_need, 1),
                "gross_irrigation_need_inches": round(gross_irrigation_need, 1),
                "number_of_irrigations": num_irrigations,
                "application_per_event_inches": round(optimal_application, 2)
            },
            "system_details": {
                "irrigation_type": irrigation_type,
                "water_source": water_source,
                "system_efficiency": f"{system['application_efficiency'] * 100}%",
                "total_water_applied_acre_inches": round(total_acre_inches, 0)
            },
            "cost_analysis": {
                "variable_costs": {
                    "cost_per_irrigation_event": round(cost_per_event['cost_breakdown']['total_cost'], 2),
                    "total_variable_cost": round(total_variable_cost, 2)
                },
                "fixed_costs": fixed_costs,
                "total_season_cost": round(total_season_cost, 2),
                "cost_per_acre": round(cost_per_acre, 2),
                "cost_per_bushel_potential": round(
                    cost_per_acre / (200 if crop.lower() == 'corn' else 55), 2
                )
            },
            "recommended_schedule": schedule,
            "roi_analysis": roi,
            "optimization_opportunities": self._identify_irrigation_savings(
                irrigation_type, water_source, gross_irrigation_need, acres
            )
        }

    def compare_irrigation_systems(
        self,
        acres: float,
        annual_water_need_inches: float,
        water_source: str,
        current_system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare different irrigation systems for cost effectiveness
        """
        comparisons = []

        for system_type, system_data in SYSTEM_EFFICIENCY.items():
            # Calculate gross water need for this system
            gross_water = annual_water_need_inches / system_data['application_efficiency']
            acre_inches = gross_water * acres

            # Energy cost
            energy_cost = acre_inches * system_data['energy_use_per_acre_inch'] * self.electricity_rate

            # Water cost (simplified)
            water_cost_data = self.water_costs.get(water_source, WATER_COSTS['groundwater_well'])
            if water_source == "groundwater_well":
                water_cost = water_cost_data['pumping_cost_per_acre_inch'] * acre_inches
            else:
                water_cost = water_cost_data.get('water_cost_per_acre_inch', 3.00) * acre_inches

            # Maintenance
            maintenance_cost = system_data['maintenance_annual_per_acre'] * acres

            # Total annual operating cost
            total_annual_cost = energy_cost + water_cost + maintenance_cost
            cost_per_acre = total_annual_cost / acres

            comparisons.append({
                "system_type": system_type,
                "efficiency_percent": system_data['application_efficiency'] * 100,
                "uniformity_percent": system_data['distribution_uniformity'] * 100,
                "gross_water_needed_inches": round(gross_water, 1),
                "annual_energy_cost": round(energy_cost, 2),
                "annual_water_cost": round(water_cost, 2),
                "annual_maintenance_cost": round(maintenance_cost, 2),
                "total_annual_operating_cost": round(total_annual_cost, 2),
                "operating_cost_per_acre": round(cost_per_acre, 2),
                "is_current_system": system_type == current_system
            })

        # Sort by operating cost
        comparisons.sort(key=lambda x: x['operating_cost_per_acre'])

        # Calculate potential savings
        if current_system and current_system in [c['system_type'] for c in comparisons]:
            current_cost = next(
                c['total_annual_operating_cost']
                for c in comparisons if c['system_type'] == current_system
            )
            for comp in comparisons:
                comp['savings_vs_current'] = round(current_cost - comp['total_annual_operating_cost'], 2)
        else:
            most_expensive = max(c['total_annual_operating_cost'] for c in comparisons)
            for comp in comparisons:
                comp['savings_vs_most_expensive'] = round(
                    most_expensive - comp['total_annual_operating_cost'], 2
                )

        return {
            "acres": acres,
            "annual_crop_water_need_inches": annual_water_need_inches,
            "water_source": water_source,
            "system_comparison": comparisons,
            "recommendations": {
                "most_economical": comparisons[0]['system_type'],
                "most_economical_cost_per_acre": comparisons[0]['operating_cost_per_acre'],
                "most_efficient": max(comparisons, key=lambda x: x['efficiency_percent'])['system_type'],
                "best_uniformity": max(comparisons, key=lambda x: x['uniformity_percent'])['system_type']
            },
            "notes": self._generate_system_comparison_notes(comparisons, acres)
        }

    def analyze_water_savings_strategies(
        self,
        current_usage_acre_inches: float,
        acres: float,
        irrigation_type: str,
        water_source: str
    ) -> Dict[str, Any]:
        """
        Analyze strategies to reduce water usage and costs
        """
        current_cost = self.calculate_irrigation_costs(
            acres,
            current_usage_acre_inches / acres,
            irrigation_type,
            water_source
        )['cost_breakdown']['total_cost']

        strategies = []

        # Strategy 1: Soil moisture monitoring
        soil_moisture_savings = current_usage_acre_inches * 0.15  # 15% typical savings
        soil_moisture_cost_saved = current_cost * 0.15
        strategies.append({
            "strategy": "Soil Moisture Monitoring",
            "description": "Install soil moisture sensors to irrigate only when needed",
            "implementation_cost": 500 + acres * 2,  # Base + per acre
            "annual_water_savings_acre_inches": round(soil_moisture_savings, 1),
            "annual_cost_savings": round(soil_moisture_cost_saved, 2),
            "payback_years": round((500 + acres * 2) / soil_moisture_cost_saved, 1) if soil_moisture_cost_saved > 0 else "N/A",
            "difficulty": "Easy"
        })

        # Strategy 2: Deficit irrigation
        deficit_savings = current_usage_acre_inches * 0.20  # 20% less water
        deficit_cost_saved = current_cost * 0.20
        yield_risk = "5-10% potential yield reduction in severe stress years"
        strategies.append({
            "strategy": "Managed Deficit Irrigation",
            "description": "Apply less water during non-critical growth stages",
            "implementation_cost": 0,
            "annual_water_savings_acre_inches": round(deficit_savings, 1),
            "annual_cost_savings": round(deficit_cost_saved, 2),
            "payback_years": "Immediate",
            "difficulty": "Medium - requires careful management",
            "risk": yield_risk
        })

        # Strategy 3: Night irrigation
        night_savings = current_cost * 0.08  # 8% from reduced evaporation
        strategies.append({
            "strategy": "Night Irrigation",
            "description": "Irrigate at night to reduce evaporation losses",
            "implementation_cost": 0,
            "annual_water_savings_acre_inches": round(current_usage_acre_inches * 0.05, 1),
            "annual_cost_savings": round(night_savings, 2),
            "payback_years": "Immediate",
            "difficulty": "Easy"
        })

        # Strategy 4: Variable Rate Irrigation (VRI)
        if acres > 50:
            vri_savings = current_usage_acre_inches * 0.12
            vri_cost_saved = current_cost * 0.12
            vri_implementation = 15000 + acres * 30
            strategies.append({
                "strategy": "Variable Rate Irrigation (VRI)",
                "description": "Apply different amounts to different zones based on soil/crop variability",
                "implementation_cost": round(vri_implementation, 2),
                "annual_water_savings_acre_inches": round(vri_savings, 1),
                "annual_cost_savings": round(vri_cost_saved, 2),
                "payback_years": round(vri_implementation / vri_cost_saved, 1) if vri_cost_saved > 0 else "N/A",
                "difficulty": "Complex - requires zone mapping"
            })

        # Strategy 5: Cover crops
        cover_crop_water_savings = current_usage_acre_inches * 0.05
        cover_crop_cost = acres * 35  # Seed + establishment
        strategies.append({
            "strategy": "Cover Crops for Soil Health",
            "description": "Improve soil water holding capacity with cover crops",
            "implementation_cost": round(cover_crop_cost, 2),
            "annual_water_savings_acre_inches": round(cover_crop_water_savings, 1),
            "annual_cost_savings": round(current_cost * 0.05, 2),
            "payback_years": "2-3 years (cumulative soil improvement)",
            "difficulty": "Medium",
            "additional_benefits": "Improved soil structure, reduced erosion, nutrient cycling"
        })

        # Calculate total potential savings
        total_water_savings = sum(s['annual_water_savings_acre_inches'] for s in strategies)
        total_cost_savings = sum(s['annual_cost_savings'] for s in strategies)

        return {
            "current_analysis": {
                "annual_water_use_acre_inches": current_usage_acre_inches,
                "acres": acres,
                "irrigation_type": irrigation_type,
                "water_source": water_source,
                "current_annual_cost": round(current_cost, 2)
            },
            "water_saving_strategies": strategies,
            "total_potential_impact": {
                "max_water_savings_acre_inches": round(total_water_savings, 1),
                "max_water_savings_percent": round(total_water_savings / current_usage_acre_inches * 100, 1),
                "max_cost_savings": round(total_cost_savings, 2),
                "max_cost_savings_percent": round(total_cost_savings / current_cost * 100 if current_cost > 0 else 0, 1)
            },
            "recommended_priority": [
                s['strategy'] for s in sorted(
                    strategies,
                    key=lambda x: (
                        x['annual_cost_savings'] / max(x['implementation_cost'], 1)
                        if isinstance(x['implementation_cost'], (int, float)) else 0
                    ),
                    reverse=True
                )[:3]
            ]
        }

    def _generate_irrigation_recommendation(
        self,
        urgency: str,
        amount: float,
        is_critical: bool,
        growth_stage: str
    ) -> str:
        """Generate human-readable irrigation recommendation"""
        if urgency == "Critical":
            return (
                f"IRRIGATE IMMEDIATELY. Crop is at critical stage ({growth_stage}) "
                f"with low soil moisture. Apply {amount:.1f} inches within 24-48 hours "
                "to prevent significant yield loss."
            )
        elif urgency == "High":
            return (
                f"Schedule irrigation soon. Apply {amount:.1f} inches within 3-5 days. "
                "Soil moisture is below optimal for current growth stage."
            )
        elif urgency == "Medium":
            return (
                f"Monitor conditions. Consider applying {amount:.1f} inches within 7 days "
                "if no significant rainfall is forecast."
            )
        else:
            return (
                "No immediate irrigation needed. Current soil moisture is adequate. "
                "Continue monitoring and check forecast for upcoming weather."
            )

    def _calculate_annual_fixed_costs(
        self,
        acres: float,
        irrigation_type: str,
        water_source: str
    ) -> Dict[str, Any]:
        """Calculate annual fixed costs for irrigation"""
        system = SYSTEM_EFFICIENCY.get(irrigation_type, SYSTEM_EFFICIENCY['center_pivot'])
        water_data = self.water_costs.get(water_source, WATER_COSTS['groundwater_well'])

        maintenance = system['maintenance_annual_per_acre'] * acres

        if water_source == "groundwater_well":
            water_rights = water_data.get('water_right_annual_per_acre', 15.00) * acres
            well_maintenance = water_data.get('well_maintenance_annual', 500.00)
            fixed_total = maintenance + water_rights + well_maintenance
        elif water_source == "surface_water":
            assessment = water_data.get('assessment_annual_per_acre', 25.00) * acres
            infrastructure = water_data.get('infrastructure_fee_annual', 200.00)
            fixed_total = maintenance + assessment + infrastructure
        else:
            connection = water_data.get('connection_fee_annual', 150.00)
            fixed_total = maintenance + connection

        return {
            "equipment_maintenance": round(maintenance, 2),
            "water_access_fees": round(fixed_total - maintenance, 2),
            "total_fixed_cost": round(fixed_total, 2),
            "fixed_cost_per_acre": round(fixed_total / acres if acres > 0 else 0, 2)
        }

    def _generate_irrigation_schedule(
        self,
        crop: str,
        season_start: date,
        season_end: date,
        num_irrigations: int,
        amount_per_irrigation: float
    ) -> List[Dict[str, Any]]:
        """Generate recommended irrigation schedule"""
        crop_data = CROP_WATER_USE.get(crop.lower(), CROP_WATER_USE['corn'])
        season_days = (season_end - season_start).days

        schedule = []
        interval = season_days // (num_irrigations + 1)

        for i in range(num_irrigations):
            irrigation_date = season_start + timedelta(days=interval * (i + 1))

            # Determine growth stage (simplified)
            days_in = interval * (i + 1)
            if days_in < 30:
                stage = "Early vegetative"
            elif days_in < 60:
                stage = "Late vegetative"
            elif days_in < 90:
                stage = "Reproductive (CRITICAL)"
            else:
                stage = "Grain fill"

            schedule.append({
                "irrigation_number": i + 1,
                "target_date": irrigation_date.isoformat(),
                "amount_inches": round(amount_per_irrigation, 2),
                "growth_stage": stage,
                "priority": "High" if "CRITICAL" in stage else "Medium",
                "notes": (
                    "Prioritize this irrigation - reproductive stage is most sensitive to water stress"
                    if "CRITICAL" in stage else
                    "Adjust timing based on rainfall and soil moisture conditions"
                )
            })

        return schedule

    def _calculate_irrigation_roi(
        self,
        crop: str,
        acres: float,
        irrigation_cost: float,
        water_applied_inches: float
    ) -> Dict[str, Any]:
        """Calculate ROI of irrigation"""
        # Yield response to irrigation (simplified)
        # Corn: ~15 bu/acre per inch of water (during deficit)
        # Soybean: ~4 bu/acre per inch of water
        if crop.lower() == "corn":
            yield_response = 15  # bu/acre-inch
            grain_price = 4.50
            dryland_yield = 120
            irrigated_yield = 200
        else:
            yield_response = 4
            grain_price = 12.00
            dryland_yield = 35
            irrigated_yield = 55

        yield_increase = irrigated_yield - dryland_yield
        revenue_increase = yield_increase * grain_price * acres
        net_benefit = revenue_increase - irrigation_cost
        roi_percent = (net_benefit / irrigation_cost * 100) if irrigation_cost > 0 else 0

        return {
            "dryland_yield_estimate": dryland_yield,
            "irrigated_yield_estimate": irrigated_yield,
            "yield_increase_per_acre": yield_increase,
            "grain_price": grain_price,
            "gross_revenue_increase": round(revenue_increase, 2),
            "irrigation_cost": round(irrigation_cost, 2),
            "net_benefit": round(net_benefit, 2),
            "roi_percent": round(roi_percent, 1),
            "break_even_yield_increase": round(irrigation_cost / (grain_price * acres), 1)
        }

    def _identify_irrigation_savings(
        self,
        irrigation_type: str,
        water_source: str,
        water_need: float,
        acres: float
    ) -> List[Dict[str, Any]]:
        """Identify opportunities to reduce irrigation costs"""
        opportunities = []

        system = SYSTEM_EFFICIENCY.get(irrigation_type, SYSTEM_EFFICIENCY['center_pivot'])

        # Efficiency upgrade opportunity
        if system['application_efficiency'] < 0.85:
            savings = water_need * (0.85 - system['application_efficiency']) * acres * 5  # $5/acre-inch
            opportunities.append({
                "opportunity": "Upgrade to higher efficiency system",
                "current_efficiency": f"{system['application_efficiency'] * 100}%",
                "target_efficiency": "85%+",
                "potential_annual_savings": round(savings, 2),
                "notes": "Consider center pivot or SDI for significant water and cost savings"
            })

        # Scheduling optimization
        opportunities.append({
            "opportunity": "Implement soil moisture-based scheduling",
            "potential_water_savings_percent": "10-20%",
            "potential_annual_savings": round(water_need * 0.15 * acres * 5, 2),
            "notes": "Soil moisture sensors prevent over-irrigation and optimize timing"
        })

        # Night irrigation
        opportunities.append({
            "opportunity": "Irrigate at night",
            "potential_water_savings_percent": "3-8%",
            "potential_annual_savings": round(water_need * 0.05 * acres * 5, 2),
            "notes": "Reduced evaporation and potentially lower energy rates"
        })

        # Maintenance
        opportunities.append({
            "opportunity": "Regular system maintenance",
            "potential_water_savings_percent": "5-10%",
            "potential_annual_savings": round(water_need * 0.07 * acres * 5, 2),
            "notes": "Check nozzles, pressure, leaks annually. Improves uniformity and efficiency"
        })

        return opportunities

    def _generate_system_comparison_notes(
        self,
        comparisons: List[Dict],
        acres: float
    ) -> List[str]:
        """Generate notes for system comparison"""
        notes = []

        # Scale considerations
        if acres < 50:
            notes.append(
                "For smaller fields, consider simpler systems like drip or traveling gun "
                "to avoid high center pivot infrastructure costs."
            )
        elif acres > 500:
            notes.append(
                "Large fields benefit most from center pivot efficiency. "
                "Consider multiple pivots for very large or irregular fields."
            )

        # Efficiency note
        notes.append(
            "Higher efficiency systems cost more to install but save water and energy "
            "long-term. Calculate payback period for your situation."
        )

        # SDI consideration
        if any(c['system_type'] == 'subsurface_drip' for c in comparisons):
            notes.append(
                "Subsurface drip has highest efficiency but also highest installation cost. "
                "Best for high-value crops or water-limited situations."
            )

        return notes


# Singleton instance
_optimizer = None

def get_irrigation_optimizer(
    custom_water_costs: Optional[Dict] = None,
    electricity_rate: float = 0.10
) -> IrrigationOptimizer:
    """Get or create optimizer instance"""
    global _optimizer
    if _optimizer is None or custom_water_costs:
        _optimizer = IrrigationOptimizer(custom_water_costs, electricity_rate)
    return _optimizer


# Example usage
if __name__ == "__main__":
    optimizer = IrrigationOptimizer()

    # Example: Calculate water need
    print("=== CROP WATER NEED ANALYSIS ===")
    water_need = optimizer.calculate_crop_water_need(
        crop="corn",
        growth_stage="VT",
        reference_et=0.28,
        recent_rainfall_inches=0.5,
        soil_moisture_percent=45
    )

    print(f"Crop: {water_need['crop']}")
    print(f"Growth Stage: {water_need['growth_stage']} (Critical: {water_need['is_critical_stage']})")
    print(f"Crop ET: {water_need['crop_et_in_per_day']} in/day")
    print(f"Weekly Water Use: {water_need['weekly_crop_water_use']} inches")
    print(f"Irrigation Urgency: {water_need['irrigation_urgency']}")
    print(f"Recommended: {water_need['recommended_irrigation_inches']} inches")
    print(f"\n{water_need['recommendation']}")

    # Example: Calculate irrigation costs
    print("\n\n=== IRRIGATION COST ANALYSIS ===")
    costs = optimizer.calculate_irrigation_costs(
        acres=130,
        inches_to_apply=1.0,
        irrigation_type="center_pivot",
        water_source="groundwater_well",
        pumping_depth_ft=180
    )

    print(f"Target Application: {costs['irrigation_details']['target_application_inches']} inches")
    print(f"Gross Application: {costs['irrigation_details']['gross_application_inches']} inches")
    print(f"System Efficiency: {costs['irrigation_details']['system_efficiency_percent']}%")
    print(f"\nCost Breakdown:")
    print(f"  Energy: ${costs['cost_breakdown']['energy_cost']}")
    print(f"  Water: ${costs['cost_breakdown']['water_cost']}")
    print(f"  Labor: ${costs['cost_breakdown']['labor_cost']}")
    print(f"  Equipment: ${costs['cost_breakdown']['equipment_wear']}")
    print(f"  TOTAL: ${costs['cost_breakdown']['total_cost']}")
    print(f"\nCost per Acre: ${costs['unit_costs']['cost_per_acre']}")

    # Example: Season optimization
    print("\n\n=== SEASON IRRIGATION OPTIMIZATION ===")
    season = optimizer.optimize_irrigation_schedule(
        crop="corn",
        acres=130,
        irrigation_type="center_pivot",
        water_source="groundwater_well",
        season_start=date(2024, 5, 15),
        season_end=date(2024, 9, 15),
        expected_rainfall_inches=12,
        pumping_depth_ft=180
    )

    print(f"Seasonal Water Need: {season['season_summary']['net_irrigation_need_inches']} inches")
    print(f"Number of Irrigations: {season['season_summary']['number_of_irrigations']}")
    print(f"Total Season Cost: ${season['cost_analysis']['total_season_cost']:,.2f}")
    print(f"Cost per Acre: ${season['cost_analysis']['cost_per_acre']}")
    print(f"\nROI: {season['roi_analysis']['roi_percent']}%")
    print(f"Net Benefit: ${season['roi_analysis']['net_benefit']:,.2f}")
