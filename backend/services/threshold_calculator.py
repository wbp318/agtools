"""
Economic Threshold Calculator
Determines if pest populations justify treatment based on economics
"""

from typing import Dict


def calculate_economic_threshold(
    crop: str,
    pest_name: str,
    population_count: float,
    growth_stage: str,
    control_cost_per_acre: float,
    expected_yield: float,
    grain_price: float
) -> Dict:
    """
    Calculate if treatment is economically justified

    Args:
        crop: 'corn' or 'soybean'
        pest_name: Name of pest
        population_count: Current population (units vary by pest)
        growth_stage: Current growth stage
        control_cost_per_acre: Cost of treatment per acre
        expected_yield: Expected yield (bu/acre)
        grain_price: Current grain price ($/bu)

    Returns:
        Economic analysis with recommendation
    """

    # Threshold database (simplified - real system would query database)
    thresholds = {
        "corn": {
            "corn rootworm adult": {
                "threshold": 1.0,
                "unit": "beetles per plant",
                "yield_loss_per_unit": 2.0  # bushels per acre
            },
            "european corn borer": {
                "threshold": 1.0,
                "unit": "larvae per plant",
                "yield_loss_per_unit": 5.0
            },
            "western bean cutworm": {
                "threshold": 0.08,  # 8% of plants
                "unit": "proportion infested",
                "yield_loss_per_unit": 3.0
            }
        },
        "soybean": {
            "soybean aphid": {
                "threshold": 250,
                "unit": "aphids per plant",
                "yield_loss_per_unit": 0.05  # bushels per aphid above threshold
            },
            "bean leaf beetle": {
                "threshold": 0.20,  # 20% defoliation
                "unit": "proportion defoliation",
                "yield_loss_per_unit": 0.5
            },
            "spider mite": {
                "threshold": 0.20,
                "unit": "proportion of plants with mites",
                "yield_loss_per_unit": 2.0
            },
            "stink bug": {
                "threshold": 5.0,
                "unit": "bugs per 25 sweeps",
                "yield_loss_per_unit": 1.0
            }
        }
    }

    # Get threshold for this pest/crop
    pest_lower = pest_name.lower()
    crop_lower = crop.lower()

    threshold_info = None
    for pest_key in thresholds.get(crop_lower, {}):
        if pest_key in pest_lower:
            threshold_info = thresholds[crop_lower][pest_key]
            break

    if not threshold_info:
        # Default threshold if not in database
        threshold_info = {
            "threshold": population_count * 0.8,  # Set threshold just below current
            "unit": "units",
            "yield_loss_per_unit": 2.0
        }

    threshold_value = threshold_info["threshold"]
    threshold_unit = threshold_info["unit"]
    yield_loss_per_unit = threshold_info["yield_loss_per_unit"]

    # Calculate if threshold exceeded
    threshold_exceeded = population_count > threshold_value

    # Calculate potential yield loss
    if threshold_exceeded:
        units_above_threshold = population_count - threshold_value
        estimated_yield_loss = units_above_threshold * yield_loss_per_unit
    else:
        estimated_yield_loss = 0

    # Economic calculations
    estimated_revenue_loss = estimated_yield_loss * grain_price
    net_benefit_of_treatment = estimated_revenue_loss - control_cost_per_acre

    # Recommendation
    if threshold_exceeded and net_benefit_of_treatment > 0:
        recommendation = f"Treatment recommended. Expected net benefit: ${net_benefit_of_treatment:.2f}/acre"
    elif threshold_exceeded and net_benefit_of_treatment <= 0:
        recommendation = "Threshold exceeded but treatment not economical at current grain prices"
    else:
        recommendation = "Threshold not exceeded. Continue monitoring."

    return {
        "threshold_exceeded": threshold_exceeded,
        "current_population": population_count,
        "threshold_value": threshold_value,
        "threshold_unit": threshold_unit,
        "estimated_yield_loss_bushels": round(estimated_yield_loss, 2),
        "estimated_revenue_loss": round(estimated_revenue_loss, 2),
        "estimated_control_cost": control_cost_per_acre,
        "net_benefit_of_treatment": round(net_benefit_of_treatment, 2),
        "recommendation": recommendation
    }


# Example usage
if __name__ == "__main__":
    # Example: Soybean aphid at 300/plant
    result = calculate_economic_threshold(
        crop="soybean",
        pest_name="soybean aphid",
        population_count=300,
        growth_stage="R3",
        control_cost_per_acre=15.00,
        expected_yield=50,
        grain_price=12.00
    )

    print("=== ECONOMIC THRESHOLD ANALYSIS ===")
    print(f"Current Population: {result['current_population']} {result['threshold_unit']}")
    print(f"Economic Threshold: {result['threshold_value']} {result['threshold_unit']}")
    print(f"Threshold Exceeded: {result['threshold_exceeded']}")
    print(f"\nEstimated Yield Loss: {result['estimated_yield_loss_bushels']} bu/acre")
    print(f"Revenue Loss: ${result['estimated_revenue_loss']:.2f}/acre")
    print(f"Control Cost: ${result['estimated_control_cost']:.2f}/acre")
    print(f"Net Benefit: ${result['net_benefit_of_treatment']:.2f}/acre")
    print(f"\n{result['recommendation']}")
