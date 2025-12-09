"""
Cost Optimizer API Client

API calls for input cost optimization across labor, fertilizer, pesticides, and irrigation.
"""

from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APIClient, get_api_client
from models.cost_optimizer import (
    QuickEstimateRequest, QuickEstimateResponse,
    FarmProfileRequest, CompleteAnalysisResponse,
    FertilizerRequest, FertilizerResponse,
    IrrigationCostRequest, IrrigationCostResponse,
    LaborScoutingRequest, LaborScoutingResponse,
)


class CostOptimizerAPI:
    """
    API client for cost optimization endpoints.

    All methods return (success, result_or_error) tuples.
    """

    BASE_PATH = "/optimize"

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def quick_estimate(self, request: QuickEstimateRequest) -> tuple[bool, QuickEstimateResponse | str]:
        """
        Get quick cost estimate using industry averages.

        Args:
            request: QuickEstimateRequest with basic farm info

        Returns:
            (success, QuickEstimateResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/quick-estimate", request.to_dict())

        if response.success:
            return True, QuickEstimateResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get quick estimate"

    def complete_analysis(self, request: FarmProfileRequest) -> tuple[bool, CompleteAnalysisResponse | str]:
        """
        Perform complete farm cost analysis.

        Args:
            request: FarmProfileRequest with full farm profile

        Returns:
            (success, CompleteAnalysisResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/complete-analysis", request.to_dict())

        if response.success:
            return True, CompleteAnalysisResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to complete analysis"

    def optimize_fertilizer(self, request: FertilizerRequest) -> tuple[bool, FertilizerResponse | str]:
        """
        Get optimized fertilizer recommendations.

        Args:
            request: FertilizerRequest with soil test and crop info

        Returns:
            (success, FertilizerResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/fertilizer", request.to_dict())

        if response.success:
            return True, FertilizerResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to optimize fertilizer"

    def analyze_irrigation_cost(self, request: IrrigationCostRequest) -> tuple[bool, IrrigationCostResponse | str]:
        """
        Analyze irrigation costs.

        Args:
            request: IrrigationCostRequest with system and usage info

        Returns:
            (success, IrrigationCostResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/irrigation/cost", request.to_dict())

        if response.success:
            return True, IrrigationCostResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to analyze irrigation cost"

    def analyze_scouting_labor(self, request: LaborScoutingRequest) -> tuple[bool, LaborScoutingResponse | str]:
        """
        Analyze scouting labor costs.

        Args:
            request: LaborScoutingRequest with field info

        Returns:
            (success, LaborScoutingResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/labor/scouting", request.to_dict())

        if response.success:
            return True, LaborScoutingResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to analyze scouting labor"

    def get_budget_worksheet(
        self,
        acres: float,
        crop: str,
        is_irrigated: bool = False
    ) -> tuple[bool, dict | str]:
        """
        Get a printable budget worksheet.

        Args:
            acres: Total acres
            crop: Crop type
            is_irrigated: Whether irrigated

        Returns:
            (success, worksheet dict or error message)
        """
        response = self._client.post(
            f"{self.BASE_PATH}/budget-worksheet",
            {"acres": acres, "crop": crop, "is_irrigated": is_irrigated}
        )

        if response.success:
            return True, response.data
        else:
            return False, response.error_message or "Failed to get budget worksheet"


# Singleton instance
_cost_optimizer_api: Optional[CostOptimizerAPI] = None


def get_cost_optimizer_api() -> CostOptimizerAPI:
    """Get the global cost optimizer API instance."""
    global _cost_optimizer_api
    if _cost_optimizer_api is None:
        _cost_optimizer_api = CostOptimizerAPI()
    return _cost_optimizer_api
