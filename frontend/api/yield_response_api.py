"""
Yield Response API Client

API calls for yield response curves and economic optimum rate calculations.
"""

from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APIClient, APIResponse, get_api_client
from models.yield_response import (
    YieldCurveRequest, YieldCurveResponse,
    EORRequest, EORResult,
    CompareRatesRequest, CompareRatesResponse,
    PriceSensitivityRequest, PriceSensitivityResponse,
    MultiNutrientRequest, MultiNutrientResult,
    PriceRatioGuide,
)


class YieldResponseAPI:
    """
    API client for yield response endpoints.

    All methods return (success, result_or_error) tuples.
    """

    BASE_PATH = "/yield-response"

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def generate_curve(self, request: YieldCurveRequest) -> tuple[bool, YieldCurveResponse | str]:
        """
        Generate a yield response curve.

        Args:
            request: YieldCurveRequest with parameters

        Returns:
            (success, YieldCurveResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/curve", request.to_dict())

        if response.success:
            return True, YieldCurveResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to generate curve"

    def calculate_eor(self, request: EORRequest) -> tuple[bool, EORResult | str]:
        """
        Calculate Economic Optimum Rate (EOR).

        Args:
            request: EORRequest with prices and parameters

        Returns:
            (success, EORResult or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/economic-optimum", request.to_dict())

        if response.success:
            return True, EORResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to calculate EOR"

    def compare_rates(self, request: CompareRatesRequest) -> tuple[bool, CompareRatesResponse | str]:
        """
        Compare profitability of different application rates.

        Args:
            request: CompareRatesRequest with rates to compare

        Returns:
            (success, CompareRatesResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/compare-rates", request.to_dict())

        if response.success:
            return True, CompareRatesResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to compare rates"

    def price_sensitivity(self, request: PriceSensitivityRequest) -> tuple[bool, PriceSensitivityResponse | str]:
        """
        Analyze how EOR changes with different price scenarios.

        Args:
            request: PriceSensitivityRequest with price ranges

        Returns:
            (success, PriceSensitivityResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/price-sensitivity", request.to_dict())

        if response.success:
            return True, PriceSensitivityResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to analyze price sensitivity"

    def multi_nutrient(self, request: MultiNutrientRequest) -> tuple[bool, MultiNutrientResult | str]:
        """
        Optimize multiple nutrients together within a budget.

        Args:
            request: MultiNutrientRequest with soil tests and budget

        Returns:
            (success, MultiNutrientResult or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/multi-nutrient", request.to_dict())

        if response.success:
            return True, MultiNutrientResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to optimize nutrients"

    def get_crop_parameters(self, crop: str = "corn") -> tuple[bool, dict | str]:
        """
        Get yield response parameters for a crop.

        Args:
            crop: Crop type (corn, soybean, wheat)

        Returns:
            (success, parameters dict or error message)
        """
        response = self._client.get(f"{self.BASE_PATH}/crop-parameters/{crop}")

        if response.success:
            return True, response.data
        else:
            return False, response.error_message or "Failed to get crop parameters"

    def get_price_ratio_guide(self, crop: str = "corn", nutrient: str = "nitrogen") -> tuple[bool, PriceRatioGuide | str]:
        """
        Get price ratio quick reference guide.

        Args:
            crop: Crop type
            nutrient: Nutrient type

        Returns:
            (success, PriceRatioGuide or error message)
        """
        response = self._client.get(
            f"{self.BASE_PATH}/price-ratio-guide",
            params={"crop": crop, "nutrient": nutrient}
        )

        if response.success:
            return True, PriceRatioGuide.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get price ratio guide"


# Singleton instance
_yield_response_api: Optional[YieldResponseAPI] = None


def get_yield_response_api() -> YieldResponseAPI:
    """Get the global yield response API instance."""
    global _yield_response_api
    if _yield_response_api is None:
        _yield_response_api = YieldResponseAPI()
    return _yield_response_api
