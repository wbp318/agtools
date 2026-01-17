"""
Measurement Converter Service for Agricultural Spray Applications

Provides imperial to metric conversions for international operators.
Includes tank mix calculator and reference product database.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import re
import math


# =============================================================================
# CONVERSION CONSTANTS
# =============================================================================

# Application Rates (per area)
GAL_PER_ACRE_TO_L_PER_HA = 9.354       # 1 gal/acre = 9.354 L/ha
LB_PER_ACRE_TO_KG_PER_HA = 1.121       # 1 lb/acre = 1.121 kg/ha
OZ_PER_ACRE_TO_G_PER_HA = 70.05        # 1 oz/acre = 70.05 g/ha
FL_OZ_PER_ACRE_TO_ML_PER_HA = 73.08    # 1 fl oz/acre = 73.08 mL/ha
PT_PER_ACRE_TO_L_PER_HA = 1.169        # 1 pint/acre = 1.169 L/ha
QT_PER_ACRE_TO_L_PER_HA = 2.338        # 1 quart/acre = 2.338 L/ha

# Volume
GAL_TO_L = 3.785
FL_OZ_TO_ML = 29.574
QT_TO_L = 0.946
PT_TO_L = 0.473

# Weight
LB_TO_KG = 0.4536
OZ_TO_G = 28.35

# Area
ACRE_TO_HA = 0.4047

# Speed
MPH_TO_KMH = 1.609

# Pressure
PSI_TO_BAR = 0.0689


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class UnitType(str, Enum):
    """Categories of unit conversions."""
    APPLICATION_RATE_VOLUME = "application_rate_volume"  # gal/acre, fl oz/acre, etc.
    APPLICATION_RATE_WEIGHT = "application_rate_weight"  # lb/acre, oz/acre
    VOLUME = "volume"
    WEIGHT = "weight"
    AREA = "area"
    SPEED = "speed"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"


class ApplicationRateUnit(str, Enum):
    """Imperial application rate units."""
    GAL_PER_ACRE = "gal_per_acre"
    FL_OZ_PER_ACRE = "fl_oz_per_acre"
    PT_PER_ACRE = "pt_per_acre"
    QT_PER_ACRE = "qt_per_acre"
    LB_PER_ACRE = "lb_per_acre"
    OZ_PER_ACRE = "oz_per_acre"


class ProductCategory(str, Enum):
    """Chemical product categories."""
    HERBICIDE = "herbicide"
    FUNGICIDE = "fungicide"
    INSECTICIDE = "insecticide"
    ADJUVANT = "adjuvant"


@dataclass
class ConversionResult:
    """Result of a unit conversion with both imperial and metric values."""
    imperial_value: float
    imperial_unit: str
    imperial_display: str
    metric_value: float
    metric_unit: str
    metric_display: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TankMixResult:
    """Result of a tank mix calculation."""
    tank_size_liters: float
    application_rate_l_per_ha: float
    field_size_ha: float
    product_per_tank_liters: float
    tanks_needed: int
    coverage_per_tank_ha: float
    total_product_needed_liters: float
    leftover_liters: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductRate:
    """A single rate for a product."""
    imperial: str
    metric: str
    use_case: str
    imperial_value: float = 0.0
    metric_value: float = 0.0


@dataclass
class ReferenceProduct:
    """A reference product with typical rates."""
    name: str
    category: ProductCategory
    active_ingredient: str
    rates: List[ProductRate]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "active_ingredient": self.active_ingredient,
            "rates": [
                {
                    "imperial": r.imperial,
                    "metric": r.metric,
                    "use_case": r.use_case,
                    "imperial_value": r.imperial_value,
                    "metric_value": r.metric_value
                }
                for r in self.rates
            ]
        }


# =============================================================================
# REFERENCE PRODUCTS DATABASE
# =============================================================================

REFERENCE_PRODUCTS: List[ReferenceProduct] = [
    # HERBICIDES
    ReferenceProduct(
        name="Glyphosate (Roundup PowerMax)",
        category=ProductCategory.HERBICIDE,
        active_ingredient="Glyphosate 48.7%",
        rates=[
            ProductRate("32 fl oz/acre", "2.34 L/ha", "Burndown", 32, 2.34),
            ProductRate("22 fl oz/acre", "1.61 L/ha", "Pre-plant", 22, 1.61),
            ProductRate("44 fl oz/acre", "3.22 L/ha", "Perennial weeds", 44, 3.22),
        ]
    ),
    ReferenceProduct(
        name="2,4-D Amine",
        category=ProductCategory.HERBICIDE,
        active_ingredient="2,4-D dimethylamine salt",
        rates=[
            ProductRate("1 pt/acre", "1.17 L/ha", "Broadleaf weeds", 1, 1.17),
            ProductRate("2 pt/acre", "2.34 L/ha", "Tough perennials", 2, 2.34),
            ProductRate("1.5 pt/acre", "1.75 L/ha", "General use", 1.5, 1.75),
        ]
    ),
    ReferenceProduct(
        name="Dicamba (Clarity/Banvel)",
        category=ProductCategory.HERBICIDE,
        active_ingredient="Dicamba 56.8%",
        rates=[
            ProductRate("8 fl oz/acre", "0.58 L/ha", "Post-emerge corn", 8, 0.58),
            ProductRate("16 fl oz/acre", "1.17 L/ha", "Burndown", 16, 1.17),
            ProductRate("4 fl oz/acre", "0.29 L/ha", "Light rate", 4, 0.29),
        ]
    ),
    ReferenceProduct(
        name="Atrazine 4L",
        category=ProductCategory.HERBICIDE,
        active_ingredient="Atrazine 42.6%",
        rates=[
            ProductRate("1 qt/acre", "2.34 L/ha", "Pre-emerge", 1, 2.34),
            ProductRate("2 qt/acre", "4.68 L/ha", "Burndown", 2, 4.68),
            ProductRate("1.5 qt/acre", "3.51 L/ha", "Post-emerge", 1.5, 3.51),
        ]
    ),
    ReferenceProduct(
        name="Metolachlor (Dual II Magnum)",
        category=ProductCategory.HERBICIDE,
        active_ingredient="S-metolachlor 83.7%",
        rates=[
            ProductRate("1 pt/acre", "1.17 L/ha", "Light soils", 1, 1.17),
            ProductRate("1.33 pt/acre", "1.56 L/ha", "Medium soils", 1.33, 1.56),
            ProductRate("1.67 pt/acre", "1.95 L/ha", "Heavy soils", 1.67, 1.95),
        ]
    ),
    ReferenceProduct(
        name="Clethodim (Select Max)",
        category=ProductCategory.HERBICIDE,
        active_ingredient="Clethodim 12.6%",
        rates=[
            ProductRate("9 fl oz/acre", "0.66 L/ha", "Annual grasses", 9, 0.66),
            ProductRate("16 fl oz/acre", "1.17 L/ha", "Volunteer corn", 16, 1.17),
        ]
    ),
    ReferenceProduct(
        name="Paraquat (Gramoxone)",
        category=ProductCategory.HERBICIDE,
        active_ingredient="Paraquat 30.1%",
        rates=[
            ProductRate("2 pt/acre", "2.34 L/ha", "Burndown", 2, 2.34),
            ProductRate("3 pt/acre", "3.51 L/ha", "Heavy weed pressure", 3, 3.51),
        ]
    ),

    # FUNGICIDES
    ReferenceProduct(
        name="Propiconazole (Tilt)",
        category=ProductCategory.FUNGICIDE,
        active_ingredient="Propiconazole 41.8%",
        rates=[
            ProductRate("4 fl oz/acre", "292 mL/ha", "Preventive", 4, 0.292),
            ProductRate("6 fl oz/acre", "439 mL/ha", "Curative", 6, 0.439),
        ]
    ),
    ReferenceProduct(
        name="Tebuconazole (Folicur)",
        category=ProductCategory.FUNGICIDE,
        active_ingredient="Tebuconazole 38.7%",
        rates=[
            ProductRate("4 fl oz/acre", "292 mL/ha", "Wheat diseases", 4, 0.292),
            ProductRate("6 fl oz/acre", "439 mL/ha", "High pressure", 6, 0.439),
        ]
    ),
    ReferenceProduct(
        name="Azoxystrobin (Quadris)",
        category=ProductCategory.FUNGICIDE,
        active_ingredient="Azoxystrobin 22.9%",
        rates=[
            ProductRate("6 fl oz/acre", "439 mL/ha", "Preventive", 6, 0.439),
            ProductRate("9 fl oz/acre", "658 mL/ha", "Curative", 9, 0.658),
            ProductRate("12 fl oz/acre", "877 mL/ha", "Max rate", 12, 0.877),
        ]
    ),
    ReferenceProduct(
        name="Pyraclostrobin (Headline)",
        category=ProductCategory.FUNGICIDE,
        active_ingredient="Pyraclostrobin 23.6%",
        rates=[
            ProductRate("6 fl oz/acre", "439 mL/ha", "Corn/soybeans", 6, 0.439),
            ProductRate("9 fl oz/acre", "658 mL/ha", "High pressure", 9, 0.658),
        ]
    ),
    ReferenceProduct(
        name="Mancozeb (Dithane)",
        category=ProductCategory.FUNGICIDE,
        active_ingredient="Mancozeb 75%",
        rates=[
            ProductRate("1.5 lb/acre", "1.68 kg/ha", "Low pressure", 1.5, 1.68),
            ProductRate("2 lb/acre", "2.24 kg/ha", "High pressure", 2, 2.24),
        ]
    ),
    ReferenceProduct(
        name="Chlorothalonil (Bravo)",
        category=ProductCategory.FUNGICIDE,
        active_ingredient="Chlorothalonil 54%",
        rates=[
            ProductRate("1.5 pt/acre", "1.75 L/ha", "Preventive", 1.5, 1.75),
            ProductRate("2 pt/acre", "2.34 L/ha", "High pressure", 2, 2.34),
        ]
    ),

    # INSECTICIDES
    ReferenceProduct(
        name="Chlorpyrifos (Lorsban)",
        category=ProductCategory.INSECTICIDE,
        active_ingredient="Chlorpyrifos 44.9%",
        rates=[
            ProductRate("1 pt/acre", "1.17 L/ha", "Light infestation", 1, 1.17),
            ProductRate("2 pt/acre", "2.34 L/ha", "Heavy infestation", 2, 2.34),
        ]
    ),
    ReferenceProduct(
        name="Lambda-cyhalothrin (Warrior)",
        category=ProductCategory.INSECTICIDE,
        active_ingredient="Lambda-cyhalothrin 11.4%",
        rates=[
            ProductRate("1.92 fl oz/acre", "140 mL/ha", "Low pressure", 1.92, 0.140),
            ProductRate("3.2 fl oz/acre", "234 mL/ha", "High pressure", 3.2, 0.234),
        ]
    ),
    ReferenceProduct(
        name="Bifenthrin (Brigade)",
        category=ProductCategory.INSECTICIDE,
        active_ingredient="Bifenthrin 25.1%",
        rates=[
            ProductRate("2.1 fl oz/acre", "154 mL/ha", "Aphids", 2.1, 0.154),
            ProductRate("6.4 fl oz/acre", "468 mL/ha", "Armyworm", 6.4, 0.468),
        ]
    ),
    ReferenceProduct(
        name="Imidacloprid (Admire Pro)",
        category=ProductCategory.INSECTICIDE,
        active_ingredient="Imidacloprid 42.8%",
        rates=[
            ProductRate("1.3 fl oz/acre", "95 mL/ha", "Foliar", 1.3, 0.095),
            ProductRate("7 fl oz/acre", "512 mL/ha", "Soil drench", 7, 0.512),
        ]
    ),
    ReferenceProduct(
        name="Spinosad (Entrust)",
        category=ProductCategory.INSECTICIDE,
        active_ingredient="Spinosad 80%",
        rates=[
            ProductRate("1.25 oz/acre", "88 g/ha", "Caterpillars", 1.25, 0.088),
            ProductRate("2 oz/acre", "140 g/ha", "Heavy pressure", 2, 0.140),
        ]
    ),

    # ADJUVANTS
    ReferenceProduct(
        name="Crop Oil Concentrate (COC)",
        category=ProductCategory.ADJUVANT,
        active_ingredient="Petroleum oil 83%",
        rates=[
            ProductRate("1 pt/acre", "1.17 L/ha", "Standard", 1, 1.17),
            ProductRate("2 pt/acre", "2.34 L/ha", "Difficult weeds", 2, 2.34),
            ProductRate("1% v/v", "1% v/v", "By volume", 0, 0),
        ]
    ),
    ReferenceProduct(
        name="Non-Ionic Surfactant (NIS)",
        category=ProductCategory.ADJUVANT,
        active_ingredient="Alkylphenol ethoxylate",
        rates=[
            ProductRate("0.25% v/v", "0.25% v/v", "Standard", 0, 0),
            ProductRate("0.5% v/v", "0.5% v/v", "Heavy wax", 0, 0),
        ]
    ),
    ReferenceProduct(
        name="Ammonium Sulfate (AMS)",
        category=ProductCategory.ADJUVANT,
        active_ingredient="Ammonium sulfate 100%",
        rates=[
            ProductRate("8.5 lb/100 gal", "1 kg/100 L", "Hard water", 8.5, 1.0),
            ProductRate("17 lb/100 gal", "2 kg/100 L", "Very hard water", 17, 2.0),
        ]
    ),
    ReferenceProduct(
        name="Drift Retardant",
        category=ProductCategory.ADJUVANT,
        active_ingredient="Polyacrylamide polymer",
        rates=[
            ProductRate("4 fl oz/100 gal", "31 mL/100 L", "Light wind", 4, 0.031),
            ProductRate("8 fl oz/100 gal", "62 mL/100 L", "Moderate wind", 8, 0.062),
        ]
    ),
]


# =============================================================================
# CONVERSION FUNCTIONS
# =============================================================================

def fahrenheit_to_celsius(f: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (f - 32) * 5 / 9


def celsius_to_fahrenheit(c: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (c * 9 / 5) + 32


def convert_application_rate(
    value: float,
    from_unit: ApplicationRateUnit
) -> ConversionResult:
    """
    Convert an application rate from imperial to metric.

    Args:
        value: The numeric value to convert
        from_unit: The imperial unit of the input

    Returns:
        ConversionResult with both imperial and metric values
    """
    conversions = {
        ApplicationRateUnit.GAL_PER_ACRE: (GAL_PER_ACRE_TO_L_PER_HA, "L/ha", "gal/acre"),
        ApplicationRateUnit.FL_OZ_PER_ACRE: (FL_OZ_PER_ACRE_TO_ML_PER_HA / 1000, "L/ha", "fl oz/acre"),
        ApplicationRateUnit.PT_PER_ACRE: (PT_PER_ACRE_TO_L_PER_HA, "L/ha", "pt/acre"),
        ApplicationRateUnit.QT_PER_ACRE: (QT_PER_ACRE_TO_L_PER_HA, "L/ha", "qt/acre"),
        ApplicationRateUnit.LB_PER_ACRE: (LB_PER_ACRE_TO_KG_PER_HA, "kg/ha", "lb/acre"),
        ApplicationRateUnit.OZ_PER_ACRE: (OZ_PER_ACRE_TO_G_PER_HA / 1000, "kg/ha", "oz/acre"),
    }

    factor, metric_unit, imperial_unit = conversions[from_unit]
    metric_value = value * factor

    # For small volumes, use mL instead of L
    if metric_unit == "L/ha" and metric_value < 1:
        metric_value = metric_value * 1000
        metric_unit = "mL/ha"

    # For small weights, use g instead of kg
    if metric_unit == "kg/ha" and metric_value < 1:
        metric_value = metric_value * 1000
        metric_unit = "g/ha"

    return ConversionResult(
        imperial_value=value,
        imperial_unit=imperial_unit,
        imperial_display=f"{value:g} {imperial_unit}",
        metric_value=round(metric_value, 2),
        metric_unit=metric_unit,
        metric_display=f"{round(metric_value, 2):g} {metric_unit}"
    )


def convert_volume(value: float, from_unit: str) -> ConversionResult:
    """Convert volume from imperial to metric."""
    conversions = {
        "gal": (GAL_TO_L, "L", "gal"),
        "gallon": (GAL_TO_L, "L", "gal"),
        "gallons": (GAL_TO_L, "L", "gal"),
        "fl_oz": (FL_OZ_TO_ML, "mL", "fl oz"),
        "floz": (FL_OZ_TO_ML, "mL", "fl oz"),
        "fl oz": (FL_OZ_TO_ML, "mL", "fl oz"),
        "qt": (QT_TO_L, "L", "qt"),
        "quart": (QT_TO_L, "L", "qt"),
        "quarts": (QT_TO_L, "L", "qt"),
        "pt": (PT_TO_L, "L", "pt"),
        "pint": (PT_TO_L, "L", "pt"),
        "pints": (PT_TO_L, "L", "pt"),
    }

    from_unit_lower = from_unit.lower().strip()
    if from_unit_lower not in conversions:
        raise ValueError(f"Unknown volume unit: {from_unit}")

    factor, metric_unit, imperial_unit = conversions[from_unit_lower]
    metric_value = value * factor

    return ConversionResult(
        imperial_value=value,
        imperial_unit=imperial_unit,
        imperial_display=f"{value:g} {imperial_unit}",
        metric_value=round(metric_value, 3),
        metric_unit=metric_unit,
        metric_display=f"{round(metric_value, 3):g} {metric_unit}"
    )


def convert_weight(value: float, from_unit: str) -> ConversionResult:
    """Convert weight from imperial to metric."""
    conversions = {
        "lb": (LB_TO_KG, "kg", "lb"),
        "lbs": (LB_TO_KG, "kg", "lb"),
        "pound": (LB_TO_KG, "kg", "lb"),
        "pounds": (LB_TO_KG, "kg", "lb"),
        "oz": (OZ_TO_G, "g", "oz"),
        "ounce": (OZ_TO_G, "g", "oz"),
        "ounces": (OZ_TO_G, "g", "oz"),
    }

    from_unit_lower = from_unit.lower().strip()
    if from_unit_lower not in conversions:
        raise ValueError(f"Unknown weight unit: {from_unit}")

    factor, metric_unit, imperial_unit = conversions[from_unit_lower]
    metric_value = value * factor

    return ConversionResult(
        imperial_value=value,
        imperial_unit=imperial_unit,
        imperial_display=f"{value:g} {imperial_unit}",
        metric_value=round(metric_value, 3),
        metric_unit=metric_unit,
        metric_display=f"{round(metric_value, 3):g} {metric_unit}"
    )


def convert_area(value: float, from_unit: str = "acre") -> ConversionResult:
    """Convert area from acres to hectares."""
    metric_value = value * ACRE_TO_HA

    return ConversionResult(
        imperial_value=value,
        imperial_unit="acre" if value == 1 else "acres",
        imperial_display=f"{value:g} {'acre' if value == 1 else 'acres'}",
        metric_value=round(metric_value, 2),
        metric_unit="ha",
        metric_display=f"{round(metric_value, 2):g} ha"
    )


def convert_speed(value: float, from_unit: str = "mph") -> ConversionResult:
    """Convert speed from mph to km/h."""
    metric_value = value * MPH_TO_KMH

    return ConversionResult(
        imperial_value=value,
        imperial_unit="mph",
        imperial_display=f"{value:g} mph",
        metric_value=round(metric_value, 1),
        metric_unit="km/h",
        metric_display=f"{round(metric_value, 1):g} km/h"
    )


def convert_pressure(value: float, from_unit: str = "psi") -> ConversionResult:
    """Convert pressure from PSI to bar."""
    metric_value = value * PSI_TO_BAR

    return ConversionResult(
        imperial_value=value,
        imperial_unit="PSI",
        imperial_display=f"{value:g} PSI",
        metric_value=round(metric_value, 2),
        metric_unit="bar",
        metric_display=f"{round(metric_value, 2):g} bar"
    )


def convert_temperature(value: float, from_unit: str = "F") -> ConversionResult:
    """Convert temperature from Fahrenheit to Celsius."""
    metric_value = fahrenheit_to_celsius(value)

    return ConversionResult(
        imperial_value=value,
        imperial_unit="F",
        imperial_display=f"{value:g}°F",
        metric_value=round(metric_value, 1),
        metric_unit="C",
        metric_display=f"{round(metric_value, 1):g}°C"
    )


def parse_rate_string(rate_str: str) -> Tuple[float, str]:
    """
    Parse a rate string like "32 fl oz/acre" into value and unit.

    Returns:
        Tuple of (value, unit_string)
    """
    # Pattern to match number (with optional decimal) followed by unit
    pattern = r'^([\d.]+)\s*(.+)$'
    match = re.match(pattern, rate_str.strip())

    if not match:
        raise ValueError(f"Cannot parse rate string: {rate_str}")

    value = float(match.group(1))
    unit = match.group(2).strip()

    return value, unit


def convert_rate_string(rate_str: str) -> ConversionResult:
    """
    Convert a rate string like "32 fl oz/acre" to metric.

    Handles common formats:
    - "32 fl oz/acre" -> "2.34 L/ha"
    - "2 pt/acre" -> "2.34 L/ha"
    - "1.5 lb/acre" -> "1.68 kg/ha"
    """
    value, unit = parse_rate_string(rate_str)

    # Normalize unit string
    unit_lower = unit.lower().replace(" ", "").replace("-", "")

    # Map to ApplicationRateUnit
    unit_mapping = {
        "gal/acre": ApplicationRateUnit.GAL_PER_ACRE,
        "gal/ac": ApplicationRateUnit.GAL_PER_ACRE,
        "gallon/acre": ApplicationRateUnit.GAL_PER_ACRE,
        "gallons/acre": ApplicationRateUnit.GAL_PER_ACRE,
        "floz/acre": ApplicationRateUnit.FL_OZ_PER_ACRE,
        "floz/ac": ApplicationRateUnit.FL_OZ_PER_ACRE,
        "fl.oz/acre": ApplicationRateUnit.FL_OZ_PER_ACRE,
        "oz/acre": ApplicationRateUnit.OZ_PER_ACRE,  # Weight oz
        "oz/ac": ApplicationRateUnit.OZ_PER_ACRE,
        "pt/acre": ApplicationRateUnit.PT_PER_ACRE,
        "pt/ac": ApplicationRateUnit.PT_PER_ACRE,
        "pint/acre": ApplicationRateUnit.PT_PER_ACRE,
        "pints/acre": ApplicationRateUnit.PT_PER_ACRE,
        "qt/acre": ApplicationRateUnit.QT_PER_ACRE,
        "qt/ac": ApplicationRateUnit.QT_PER_ACRE,
        "quart/acre": ApplicationRateUnit.QT_PER_ACRE,
        "quarts/acre": ApplicationRateUnit.QT_PER_ACRE,
        "lb/acre": ApplicationRateUnit.LB_PER_ACRE,
        "lb/ac": ApplicationRateUnit.LB_PER_ACRE,
        "lbs/acre": ApplicationRateUnit.LB_PER_ACRE,
        "pound/acre": ApplicationRateUnit.LB_PER_ACRE,
        "pounds/acre": ApplicationRateUnit.LB_PER_ACRE,
    }

    if unit_lower not in unit_mapping:
        raise ValueError(f"Unknown application rate unit: {unit}")

    return convert_application_rate(value, unit_mapping[unit_lower])


# =============================================================================
# TANK MIX CALCULATOR
# =============================================================================

def calculate_tank_mix(
    tank_size_liters: float,
    application_rate_l_per_ha: float,
    field_size_ha: float,
    product_rate_l_per_ha: Optional[float] = None
) -> TankMixResult:
    """
    Calculate tank mix amounts for a spray application.

    Args:
        tank_size_liters: Size of the spray tank in liters
        application_rate_l_per_ha: Carrier (water) application rate in L/ha
        field_size_ha: Total field size in hectares
        product_rate_l_per_ha: Product application rate in L/ha (optional)

    Returns:
        TankMixResult with calculated values
    """
    if tank_size_liters <= 0:
        raise ValueError("Tank size must be positive")
    if application_rate_l_per_ha <= 0:
        raise ValueError("Application rate must be positive")
    if field_size_ha <= 0:
        raise ValueError("Field size must be positive")

    # Calculate coverage per tank
    coverage_per_tank_ha = tank_size_liters / application_rate_l_per_ha

    # Calculate tanks needed
    tanks_needed_exact = field_size_ha / coverage_per_tank_ha
    tanks_needed = math.ceil(tanks_needed_exact)

    # Calculate leftover
    total_volume_needed = field_size_ha * application_rate_l_per_ha
    total_volume_with_full_tanks = tanks_needed * tank_size_liters
    leftover_liters = total_volume_with_full_tanks - total_volume_needed

    # Calculate product amount per tank if rate provided
    if product_rate_l_per_ha:
        product_per_tank = coverage_per_tank_ha * product_rate_l_per_ha
        total_product_needed = field_size_ha * product_rate_l_per_ha
    else:
        product_per_tank = 0.0
        total_product_needed = 0.0

    return TankMixResult(
        tank_size_liters=tank_size_liters,
        application_rate_l_per_ha=application_rate_l_per_ha,
        field_size_ha=field_size_ha,
        product_per_tank_liters=round(product_per_tank, 2),
        tanks_needed=tanks_needed,
        coverage_per_tank_ha=round(coverage_per_tank_ha, 2),
        total_product_needed_liters=round(total_product_needed, 2),
        leftover_liters=round(leftover_liters, 2)
    )


def calculate_tank_mix_imperial(
    tank_size_gallons: float,
    application_rate_gpa: float,
    field_size_acres: float,
    product_rate_per_acre: Optional[float] = None,
    product_unit: str = "fl_oz"
) -> Dict[str, Any]:
    """
    Calculate tank mix starting from imperial units, returning both systems.

    Args:
        tank_size_gallons: Tank size in gallons
        application_rate_gpa: Gallons per acre
        field_size_acres: Field size in acres
        product_rate_per_acre: Product rate per acre
        product_unit: Unit of product rate (fl_oz, pt, qt, lb, oz)
    """
    # Convert to metric
    tank_size_l = tank_size_gallons * GAL_TO_L
    app_rate_l_ha = application_rate_gpa * GAL_PER_ACRE_TO_L_PER_HA
    field_size_ha = field_size_acres * ACRE_TO_HA

    # Convert product rate to L/ha if provided
    product_rate_l_ha = None
    if product_rate_per_acre:
        unit_factors = {
            "fl_oz": FL_OZ_PER_ACRE_TO_ML_PER_HA / 1000,
            "pt": PT_PER_ACRE_TO_L_PER_HA,
            "qt": QT_PER_ACRE_TO_L_PER_HA,
            "gal": GAL_PER_ACRE_TO_L_PER_HA,
        }
        factor = unit_factors.get(product_unit, FL_OZ_PER_ACRE_TO_ML_PER_HA / 1000)
        product_rate_l_ha = product_rate_per_acre * factor

    # Calculate in metric
    result = calculate_tank_mix(tank_size_l, app_rate_l_ha, field_size_ha, product_rate_l_ha)

    # Add imperial equivalents
    return {
        "metric": result.to_dict(),
        "imperial": {
            "tank_size_gallons": tank_size_gallons,
            "application_rate_gpa": application_rate_gpa,
            "field_size_acres": field_size_acres,
            "product_per_tank_imperial": round(result.product_per_tank_liters / GAL_TO_L, 2) if product_rate_per_acre else 0,
            "tanks_needed": result.tanks_needed,
            "coverage_per_tank_acres": round(result.coverage_per_tank_ha / ACRE_TO_HA, 2),
            "leftover_gallons": round(result.leftover_liters / GAL_TO_L, 2)
        }
    }


# =============================================================================
# RECOMMENDATION CONVERSION
# =============================================================================

def convert_recommendation(recommendation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take an AgTools spray recommendation and add metric equivalents.

    Looks for rate fields and adds _metric versions alongside.
    """
    result = recommendation.copy()

    # Fields that might contain rates
    rate_fields = ["rate", "application_rate", "product_rate", "adjuvant_rate"]

    for field in rate_fields:
        if field in result and isinstance(result[field], str):
            try:
                conversion = convert_rate_string(result[field])
                result[f"{field}_imperial"] = conversion.imperial_display
                result[f"{field}_metric"] = conversion.metric_display
            except ValueError:
                # If we can't parse it, leave it as-is
                pass

    # Handle nested products
    if "products" in result and isinstance(result["products"], list):
        for product in result["products"]:
            if isinstance(product, dict) and "rate" in product:
                try:
                    conversion = convert_rate_string(product["rate"])
                    product["rate_imperial"] = conversion.imperial_display
                    product["rate_metric"] = conversion.metric_display
                except ValueError:
                    pass

    # Handle recommendations list
    if "recommendations" in result and isinstance(result["recommendations"], list):
        for rec in result["recommendations"]:
            if isinstance(rec, dict) and "rate" in rec:
                try:
                    conversion = convert_rate_string(rec["rate"])
                    rec["rate_imperial"] = conversion.imperial_display
                    rec["rate_metric"] = conversion.metric_display
                except ValueError:
                    pass

    return result


# =============================================================================
# SERVICE CLASS
# =============================================================================

class MeasurementConverterService:
    """Service for agricultural measurement conversions."""

    def convert_spray_rate(
        self,
        value: float,
        unit: str
    ) -> Dict[str, Any]:
        """Convert a spray application rate to metric."""
        # Map string unit to enum
        unit_mapping = {
            "gal_per_acre": ApplicationRateUnit.GAL_PER_ACRE,
            "fl_oz_per_acre": ApplicationRateUnit.FL_OZ_PER_ACRE,
            "pt_per_acre": ApplicationRateUnit.PT_PER_ACRE,
            "qt_per_acre": ApplicationRateUnit.QT_PER_ACRE,
            "lb_per_acre": ApplicationRateUnit.LB_PER_ACRE,
            "oz_per_acre": ApplicationRateUnit.OZ_PER_ACRE,
        }

        if unit not in unit_mapping:
            raise ValueError(f"Unknown unit: {unit}. Valid units: {list(unit_mapping.keys())}")

        result = convert_application_rate(value, unit_mapping[unit])
        return result.to_dict()

    def convert_rate_string(self, rate_str: str) -> Dict[str, Any]:
        """Convert a rate string like '32 fl oz/acre' to metric."""
        result = convert_rate_string(rate_str)
        return result.to_dict()

    def convert_volume(self, value: float, unit: str) -> Dict[str, Any]:
        """Convert volume from imperial to metric."""
        result = convert_volume(value, unit)
        return result.to_dict()

    def convert_weight(self, value: float, unit: str) -> Dict[str, Any]:
        """Convert weight from imperial to metric."""
        result = convert_weight(value, unit)
        return result.to_dict()

    def convert_area(self, value: float) -> Dict[str, Any]:
        """Convert acres to hectares."""
        result = convert_area(value)
        return result.to_dict()

    def convert_speed(self, value: float) -> Dict[str, Any]:
        """Convert mph to km/h."""
        result = convert_speed(value)
        return result.to_dict()

    def convert_pressure(self, value: float) -> Dict[str, Any]:
        """Convert PSI to bar."""
        result = convert_pressure(value)
        return result.to_dict()

    def convert_temperature(self, value: float) -> Dict[str, Any]:
        """Convert Fahrenheit to Celsius."""
        result = convert_temperature(value)
        return result.to_dict()

    def calculate_tank_mix(
        self,
        tank_size_liters: float,
        application_rate_l_per_ha: float,
        field_size_ha: float,
        product_rate_l_per_ha: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate tank mix amounts."""
        result = calculate_tank_mix(
            tank_size_liters,
            application_rate_l_per_ha,
            field_size_ha,
            product_rate_l_per_ha
        )
        return result.to_dict()

    def calculate_tank_mix_imperial(
        self,
        tank_size_gallons: float,
        application_rate_gpa: float,
        field_size_acres: float,
        product_rate_per_acre: Optional[float] = None,
        product_unit: str = "fl_oz"
    ) -> Dict[str, Any]:
        """Calculate tank mix from imperial inputs, returning both systems."""
        return calculate_tank_mix_imperial(
            tank_size_gallons,
            application_rate_gpa,
            field_size_acres,
            product_rate_per_acre,
            product_unit
        )

    def get_reference_products(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get reference products with rates in both units."""
        products = REFERENCE_PRODUCTS

        # Filter by category
        if category:
            try:
                cat_enum = ProductCategory(category.lower())
                products = [p for p in products if p.category == cat_enum]
            except ValueError:
                pass  # Invalid category, return all

        # Filter by search term
        if search:
            search_lower = search.lower()
            products = [
                p for p in products
                if search_lower in p.name.lower()
                or search_lower in p.active_ingredient.lower()
            ]

        return [p.to_dict() for p in products]

    def convert_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Convert an AgTools recommendation, adding metric equivalents."""
        return convert_recommendation(recommendation)

    def batch_convert(self, conversions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert multiple values in a single call."""
        results = []

        for item in conversions:
            try:
                value = item.get("value")
                unit = item.get("unit")

                if value is None or unit is None:
                    results.append({"error": "Missing value or unit"})
                    continue

                result = self.convert_spray_rate(float(value), unit)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        return results

    def get_service_summary(self) -> Dict[str, Any]:
        """Get a summary of the converter service capabilities."""
        return {
            "supported_rate_units": [u.value for u in ApplicationRateUnit],
            "supported_volume_units": ["gal", "fl_oz", "qt", "pt"],
            "supported_weight_units": ["lb", "oz"],
            "product_categories": [c.value for c in ProductCategory],
            "total_reference_products": len(REFERENCE_PRODUCTS),
            "conversion_constants": {
                "gal_per_acre_to_l_per_ha": GAL_PER_ACRE_TO_L_PER_HA,
                "lb_per_acre_to_kg_per_ha": LB_PER_ACRE_TO_KG_PER_HA,
                "acre_to_ha": ACRE_TO_HA,
                "mph_to_kmh": MPH_TO_KMH,
                "psi_to_bar": PSI_TO_BAR,
            }
        }


# Singleton instance
_service_instance: Optional[MeasurementConverterService] = None


def get_measurement_converter_service() -> MeasurementConverterService:
    """Get the singleton measurement converter service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MeasurementConverterService()
    return _service_instance
