"""
Measurement Converter API Client

API client for imperial to metric conversion endpoints.
"""

from typing import Any, Dict, List, Optional, Tuple

from api.client import get_api_client, APIClient
from models.measurement_converter import (
    ConversionResult,
    TankMixResult,
    TankMixImperialResult,
    ReferenceProduct,
    ServiceSummary,
    SprayRateConversionRequest,
    RateStringConversionRequest,
    TankMixRequest,
    TankMixImperialRequest,
)


class MeasurementConverterAPI:
    """API client for measurement conversion endpoints."""

    BASE_PATH = "/api/v1/convert"

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def get_summary(self) -> Tuple[bool, ServiceSummary | str]:
        """Get a summary of the converter service capabilities."""
        response = self._client.get(f"{self.BASE_PATH}/summary")

        if response.success:
            return True, ServiceSummary.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get service summary"

    def convert_spray_rate(
        self,
        value: float,
        unit: str
    ) -> Tuple[bool, ConversionResult | str]:
        """
        Convert a spray application rate from imperial to metric.

        Args:
            value: The numeric value to convert
            unit: The unit (gal_per_acre, fl_oz_per_acre, pt_per_acre, qt_per_acre, lb_per_acre, oz_per_acre)
        """
        request = SprayRateConversionRequest(value=value, unit=unit)
        response = self._client.post(f"{self.BASE_PATH}/spray-rate", request.to_dict())

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert spray rate"

    def convert_rate_string(self, rate_string: str) -> Tuple[bool, ConversionResult | str]:
        """
        Parse and convert a rate string like '32 fl oz/acre' to metric.

        Args:
            rate_string: Rate string to parse (e.g., "32 fl oz/acre", "2 pt/acre")
        """
        request = RateStringConversionRequest(rate_string=rate_string)
        response = self._client.post(f"{self.BASE_PATH}/rate-string", request.to_dict())

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert rate string"

    def convert_volume(self, value: float, unit: str) -> Tuple[bool, ConversionResult | str]:
        """Convert a volume from imperial to metric."""
        response = self._client.post(f"{self.BASE_PATH}/volume", {"value": value, "unit": unit})

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert volume"

    def convert_weight(self, value: float, unit: str) -> Tuple[bool, ConversionResult | str]:
        """Convert a weight from imperial to metric."""
        response = self._client.post(f"{self.BASE_PATH}/weight", {"value": value, "unit": unit})

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert weight"

    def convert_area(self, value: float) -> Tuple[bool, ConversionResult | str]:
        """Convert acres to hectares."""
        response = self._client.post(f"{self.BASE_PATH}/area", {"value": value})

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert area"

    def convert_speed(self, value: float) -> Tuple[bool, ConversionResult | str]:
        """Convert mph to km/h."""
        response = self._client.post(f"{self.BASE_PATH}/speed", {"value": value})

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert speed"

    def convert_pressure(self, value: float) -> Tuple[bool, ConversionResult | str]:
        """Convert PSI to bar."""
        response = self._client.post(f"{self.BASE_PATH}/pressure", {"value": value})

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert pressure"

    def convert_temperature(self, value: float) -> Tuple[bool, ConversionResult | str]:
        """Convert Fahrenheit to Celsius."""
        response = self._client.post(f"{self.BASE_PATH}/temperature", {"value": value})

        if response.success:
            return True, ConversionResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to convert temperature"

    def calculate_tank_mix(
        self,
        tank_size_liters: float,
        application_rate_l_per_ha: float,
        field_size_ha: float,
        product_rate_l_per_ha: Optional[float] = None
    ) -> Tuple[bool, TankMixResult | str]:
        """
        Calculate tank mix amounts (metric inputs).

        Args:
            tank_size_liters: Tank size in liters
            application_rate_l_per_ha: Carrier application rate in L/ha
            field_size_ha: Field size in hectares
            product_rate_l_per_ha: Product rate in L/ha (optional)
        """
        request = TankMixRequest(
            tank_size_liters=tank_size_liters,
            application_rate_l_per_ha=application_rate_l_per_ha,
            field_size_ha=field_size_ha,
            product_rate_l_per_ha=product_rate_l_per_ha
        )
        response = self._client.post(f"{self.BASE_PATH}/tank-mix", request.to_dict())

        if response.success:
            return True, TankMixResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to calculate tank mix"

    def calculate_tank_mix_imperial(
        self,
        tank_size_gallons: float,
        application_rate_gpa: float,
        field_size_acres: float,
        product_rate_per_acre: Optional[float] = None,
        product_unit: str = "fl_oz"
    ) -> Tuple[bool, TankMixImperialResult | str]:
        """
        Calculate tank mix from imperial inputs, returning both unit systems.

        Args:
            tank_size_gallons: Tank size in gallons
            application_rate_gpa: Gallons per acre
            field_size_acres: Field size in acres
            product_rate_per_acre: Product rate per acre (optional)
            product_unit: Unit of product rate (fl_oz, pt, qt, gal)
        """
        request = TankMixImperialRequest(
            tank_size_gallons=tank_size_gallons,
            application_rate_gpa=application_rate_gpa,
            field_size_acres=field_size_acres,
            product_rate_per_acre=product_rate_per_acre,
            product_unit=product_unit
        )
        response = self._client.post(f"{self.BASE_PATH}/tank-mix-imperial", request.to_dict())

        if response.success:
            return True, TankMixImperialResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to calculate tank mix"

    def get_reference_products(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[bool, List[ReferenceProduct] | str]:
        """
        Get reference products with application rates in both units.

        Args:
            category: Filter by category (herbicide, fungicide, insecticide, adjuvant)
            search: Search by product name or active ingredient
        """
        params = {}
        if category:
            params["category"] = category
        if search:
            params["search"] = search

        # Build query string
        query = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"{self.BASE_PATH}/reference-products"
        if query:
            path = f"{path}?{query}"

        response = self._client.get(path)

        if response.success:
            products = [ReferenceProduct.from_dict(p) for p in response.data]
            return True, products
        else:
            return False, response.error_message or "Failed to get reference products"

    def batch_convert(
        self,
        conversions: List[Dict[str, Any]]
    ) -> Tuple[bool, List[Dict[str, Any]] | str]:
        """
        Convert multiple values in a single request.

        Args:
            conversions: List of dicts with 'value' and 'unit' keys
        """
        response = self._client.post(f"{self.BASE_PATH}/batch", {"conversions": conversions})

        if response.success:
            return True, response.data.get("results", [])
        else:
            return False, response.error_message or "Failed to batch convert"

    def convert_recommendation(
        self,
        recommendation: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any] | str]:
        """
        Convert an AgTools spray recommendation, adding metric equivalents.

        Args:
            recommendation: AgTools recommendation object
        """
        response = self._client.post(f"{self.BASE_PATH}/recommendation", {"recommendation": recommendation})

        if response.success:
            return True, response.data
        else:
            return False, response.error_message or "Failed to convert recommendation"


# Singleton instance
_api_instance: Optional[MeasurementConverterAPI] = None


def get_measurement_converter_api() -> MeasurementConverterAPI:
    """Get the singleton measurement converter API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = MeasurementConverterAPI()
    return _api_instance
