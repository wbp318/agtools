"""
Measurement Converter Data Models

Data models for imperial to metric conversion of agricultural measurements.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any


class UnitType(str, Enum):
    """Categories of unit conversions."""
    APPLICATION_RATE_VOLUME = "application_rate_volume"
    APPLICATION_RATE_WEIGHT = "application_rate_weight"
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

    @property
    def display_name(self) -> str:
        """Human-readable unit name."""
        names = {
            self.GAL_PER_ACRE: "gal/acre",
            self.FL_OZ_PER_ACRE: "fl oz/acre",
            self.PT_PER_ACRE: "pt/acre",
            self.QT_PER_ACRE: "qt/acre",
            self.LB_PER_ACRE: "lb/acre",
            self.OZ_PER_ACRE: "oz/acre",
        }
        return names.get(self, self.value)


class ProductCategory(str, Enum):
    """Chemical product categories."""
    HERBICIDE = "herbicide"
    FUNGICIDE = "fungicide"
    INSECTICIDE = "insecticide"
    ADJUVANT = "adjuvant"

    @property
    def display_name(self) -> str:
        """Human-readable category name."""
        return self.value.capitalize()


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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversionResult":
        return cls(
            imperial_value=data.get("imperial_value", 0),
            imperial_unit=data.get("imperial_unit", ""),
            imperial_display=data.get("imperial_display", ""),
            metric_value=data.get("metric_value", 0),
            metric_unit=data.get("metric_unit", ""),
            metric_display=data.get("metric_display", ""),
        )


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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TankMixResult":
        return cls(
            tank_size_liters=data.get("tank_size_liters", 0),
            application_rate_l_per_ha=data.get("application_rate_l_per_ha", 0),
            field_size_ha=data.get("field_size_ha", 0),
            product_per_tank_liters=data.get("product_per_tank_liters", 0),
            tanks_needed=data.get("tanks_needed", 0),
            coverage_per_tank_ha=data.get("coverage_per_tank_ha", 0),
            total_product_needed_liters=data.get("total_product_needed_liters", 0),
            leftover_liters=data.get("leftover_liters", 0),
        )


@dataclass
class TankMixImperialResult:
    """Tank mix calculation with both unit systems."""
    metric: TankMixResult
    imperial: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric.to_dict(),
            "imperial": self.imperial
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TankMixImperialResult":
        return cls(
            metric=TankMixResult.from_dict(data.get("metric", {})),
            imperial=data.get("imperial", {})
        )


@dataclass
class ProductRate:
    """A single rate for a reference product."""
    imperial: str
    metric: str
    use_case: str
    imperial_value: float = 0.0
    metric_value: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductRate":
        return cls(
            imperial=data.get("imperial", ""),
            metric=data.get("metric", ""),
            use_case=data.get("use_case", ""),
            imperial_value=data.get("imperial_value", 0.0),
            metric_value=data.get("metric_value", 0.0),
        )


@dataclass
class ReferenceProduct:
    """A reference product with typical application rates."""
    name: str
    category: str
    active_ingredient: str
    rates: List[ProductRate] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "active_ingredient": self.active_ingredient,
            "rates": [
                {
                    "imperial": r.imperial,
                    "metric": r.metric,
                    "use_case": r.use_case,
                    "imperial_value": r.imperial_value,
                    "metric_value": r.metric_value,
                }
                for r in self.rates
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReferenceProduct":
        rates = [ProductRate.from_dict(r) for r in data.get("rates", [])]
        return cls(
            name=data.get("name", ""),
            category=data.get("category", ""),
            active_ingredient=data.get("active_ingredient", ""),
            rates=rates,
        )


@dataclass
class SprayRateConversionRequest:
    """Request to convert a spray application rate."""
    value: float
    unit: str

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "unit": self.unit}


@dataclass
class RateStringConversionRequest:
    """Request to convert a rate string."""
    rate_string: str

    def to_dict(self) -> Dict[str, Any]:
        return {"rate_string": self.rate_string}


@dataclass
class TankMixRequest:
    """Request to calculate tank mix amounts."""
    tank_size_liters: float
    application_rate_l_per_ha: float
    field_size_ha: float
    product_rate_l_per_ha: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "tank_size_liters": self.tank_size_liters,
            "application_rate_l_per_ha": self.application_rate_l_per_ha,
            "field_size_ha": self.field_size_ha,
        }
        if self.product_rate_l_per_ha is not None:
            d["product_rate_l_per_ha"] = self.product_rate_l_per_ha
        return d


@dataclass
class TankMixImperialRequest:
    """Request to calculate tank mix from imperial inputs."""
    tank_size_gallons: float
    application_rate_gpa: float
    field_size_acres: float
    product_rate_per_acre: Optional[float] = None
    product_unit: str = "fl_oz"

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "tank_size_gallons": self.tank_size_gallons,
            "application_rate_gpa": self.application_rate_gpa,
            "field_size_acres": self.field_size_acres,
            "product_unit": self.product_unit,
        }
        if self.product_rate_per_acre is not None:
            d["product_rate_per_acre"] = self.product_rate_per_acre
        return d


@dataclass
class ServiceSummary:
    """Summary of converter service capabilities."""
    supported_rate_units: List[str]
    supported_volume_units: List[str]
    supported_weight_units: List[str]
    product_categories: List[str]
    total_reference_products: int
    conversion_constants: Dict[str, float]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceSummary":
        return cls(
            supported_rate_units=data.get("supported_rate_units", []),
            supported_volume_units=data.get("supported_volume_units", []),
            supported_weight_units=data.get("supported_weight_units", []),
            product_categories=data.get("product_categories", []),
            total_reference_products=data.get("total_reference_products", 0),
            conversion_constants=data.get("conversion_constants", {}),
        )


# Conversion constants for local calculations (matching backend)
CONVERSION_CONSTANTS = {
    # Application Rates
    "GAL_PER_ACRE_TO_L_PER_HA": 9.354,
    "LB_PER_ACRE_TO_KG_PER_HA": 1.121,
    "OZ_PER_ACRE_TO_G_PER_HA": 70.05,
    "FL_OZ_PER_ACRE_TO_ML_PER_HA": 73.08,
    "PT_PER_ACRE_TO_L_PER_HA": 1.169,
    "QT_PER_ACRE_TO_L_PER_HA": 2.338,
    # Volume
    "GAL_TO_L": 3.785,
    "FL_OZ_TO_ML": 29.574,
    "QT_TO_L": 0.946,
    "PT_TO_L": 0.473,
    # Weight
    "LB_TO_KG": 0.4536,
    "OZ_TO_G": 28.35,
    # Area
    "ACRE_TO_HA": 0.4047,
    # Speed
    "MPH_TO_KMH": 1.609,
    # Pressure
    "PSI_TO_BAR": 0.0689,
}


def convert_locally(value: float, unit: ApplicationRateUnit) -> ConversionResult:
    """
    Perform conversion locally without API call.

    For quick offline conversions in the UI.
    """
    conversions = {
        ApplicationRateUnit.GAL_PER_ACRE: (9.354, "L/ha", "gal/acre"),
        ApplicationRateUnit.FL_OZ_PER_ACRE: (0.07308, "L/ha", "fl oz/acre"),
        ApplicationRateUnit.PT_PER_ACRE: (1.169, "L/ha", "pt/acre"),
        ApplicationRateUnit.QT_PER_ACRE: (2.338, "L/ha", "qt/acre"),
        ApplicationRateUnit.LB_PER_ACRE: (1.121, "kg/ha", "lb/acre"),
        ApplicationRateUnit.OZ_PER_ACRE: (0.07005, "kg/ha", "oz/acre"),
    }

    factor, metric_unit, imperial_unit = conversions[unit]
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
