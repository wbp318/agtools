"""
Pricing Service API Client

API calls for pricing, supplier quotes, and cost calculations.
"""

from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APIClient, APIResponse, get_api_client
from models.pricing import (
    ProductPrice, GetPricesResponse,
    SetPriceRequest, SetPriceResponse,
    BulkUpdateRequest, BulkUpdateResponse,
    BuyRecommendationRequest, BuyRecommendationResponse,
    InputCostRequest, InputCostResponse,
    PriceAlertsResponse,
    SupplierComparisonRequest, SupplierComparisonResponse,
)


class PricingAPI:
    """
    API client for pricing service endpoints.

    All methods return (success, result_or_error) tuples.
    """

    BASE_PATH = "/pricing"

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def get_prices(
        self,
        category: Optional[str] = None,
        region: str = "midwest_corn_belt"
    ) -> tuple[bool, GetPricesResponse | str]:
        """
        Get all product prices.

        Args:
            category: Optional filter (fertilizer, pesticide, seed, fuel, custom_application)
            region: Geographic region for price adjustments

        Returns:
            (success, GetPricesResponse or error message)
        """
        params = {"region": region}
        if category:
            params["category"] = category

        response = self._client.get(f"{self.BASE_PATH}/prices", params=params)

        if response.success:
            return True, GetPricesResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get prices"

    def get_price(
        self,
        product_id: str,
        region: str = "midwest_corn_belt"
    ) -> tuple[bool, ProductPrice | str]:
        """
        Get price for a specific product.

        Args:
            product_id: Product identifier
            region: Geographic region

        Returns:
            (success, ProductPrice or error message)
        """
        response = self._client.get(
            f"{self.BASE_PATH}/price/{product_id}",
            params={"region": region}
        )

        if response.success:
            return True, ProductPrice.from_dict(product_id, response.data)
        else:
            return False, response.error_message or "Failed to get price"

    def set_price(
        self,
        request: SetPriceRequest,
        region: str = "midwest_corn_belt"
    ) -> tuple[bool, SetPriceResponse | str]:
        """
        Set a custom supplier price.

        Args:
            request: SetPriceRequest with price details
            region: Geographic region

        Returns:
            (success, SetPriceResponse or error message)
        """
        response = self._client.post(
            f"{self.BASE_PATH}/set-price",
            data=request.to_dict(),
            params={"region": region}
        )

        if response.success:
            return True, SetPriceResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to set price"

    def bulk_update(self, request: BulkUpdateRequest) -> tuple[bool, BulkUpdateResponse | str]:
        """
        Bulk update multiple prices at once.

        Args:
            request: BulkUpdateRequest with list of price updates

        Returns:
            (success, BulkUpdateResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/bulk-update", request.to_dict())

        if response.success:
            return True, BulkUpdateResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to bulk update prices"

    def get_buy_recommendation(
        self,
        request: BuyRecommendationRequest
    ) -> tuple[bool, BuyRecommendationResponse | str]:
        """
        Get buy now vs wait recommendation.

        Args:
            request: BuyRecommendationRequest with product and quantity

        Returns:
            (success, BuyRecommendationResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/buy-recommendation", request.to_dict())

        if response.success:
            return True, BuyRecommendationResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get buy recommendation"

    def calculate_input_costs(self, request: InputCostRequest) -> tuple[bool, InputCostResponse | str]:
        """
        Calculate total input costs using current prices.

        Args:
            request: InputCostRequest with inputs and rates

        Returns:
            (success, InputCostResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/calculate-input-costs", request.to_dict())

        if response.success:
            return True, InputCostResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to calculate input costs"

    def compare_suppliers(self, request: SupplierComparisonRequest) -> tuple[bool, SupplierComparisonResponse | str]:
        """
        Compare prices across suppliers.

        Args:
            request: SupplierComparisonRequest with product list

        Returns:
            (success, SupplierComparisonResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/compare-suppliers", request.to_dict())

        if response.success:
            return True, SupplierComparisonResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to compare suppliers"

    def get_alerts(self, region: str = "midwest_corn_belt") -> tuple[bool, PriceAlertsResponse | str]:
        """
        Get price alerts (expiring quotes, above-average prices).

        Args:
            region: Geographic region

        Returns:
            (success, PriceAlertsResponse or error message)
        """
        response = self._client.get(f"{self.BASE_PATH}/alerts", params={"region": region})

        if response.success:
            return True, PriceAlertsResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get alerts"

    def get_budget_prices(
        self,
        crop: str,
        region: str = "midwest_corn_belt"
    ) -> tuple[bool, dict | str]:
        """
        Get budget prices for a crop.

        Args:
            crop: Crop type
            region: Geographic region

        Returns:
            (success, budget prices dict or error message)
        """
        response = self._client.get(
            f"{self.BASE_PATH}/budget-prices/{crop}",
            params={"region": region}
        )

        if response.success:
            return True, response.data
        else:
            return False, response.error_message or "Failed to get budget prices"


# Singleton instance
_pricing_api: Optional[PricingAPI] = None


def get_pricing_api() -> PricingAPI:
    """Get the global pricing API instance."""
    global _pricing_api
    if _pricing_api is None:
        _pricing_api = PricingAPI()
    return _pricing_api
