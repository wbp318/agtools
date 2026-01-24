"""
Spray Timing API Client

API calls for spray timing evaluation and recommendations.
"""

from typing import Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APIClient, get_api_client
from models.spray import (
    EvaluateConditionsRequest, SprayEvaluation,
    FindWindowsRequest, FindWindowsResponse,
    CostOfWaitingRequest, CostOfWaitingResult,
    DiseasePressureRequest, DiseasePressureResponse,
    GrowthStageTimingResponse,
)


class SprayTimingAPI:
    """
    API client for spray timing endpoints.

    All methods return (success, result_or_error) tuples.
    """

    BASE_PATH = "/spray-timing"

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def evaluate_conditions(self, request: EvaluateConditionsRequest) -> tuple[bool, SprayEvaluation | str]:
        """
        Evaluate current spray conditions.

        Args:
            request: EvaluateConditionsRequest with weather and spray type

        Returns:
            (success, SprayEvaluation or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/evaluate", request.to_dict())

        if response.success:
            return True, SprayEvaluation.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to evaluate conditions"

    def find_windows(self, request: FindWindowsRequest) -> tuple[bool, FindWindowsResponse | str]:
        """
        Find optimal spray windows in a forecast.

        Args:
            request: FindWindowsRequest with forecast data

        Returns:
            (success, FindWindowsResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/find-windows", request.to_dict())

        if response.success:
            return True, FindWindowsResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to find spray windows"

    def cost_of_waiting(self, request: CostOfWaitingRequest) -> tuple[bool, CostOfWaitingResult | str]:
        """
        Analyze economic cost of waiting to spray.

        Args:
            request: CostOfWaitingRequest with conditions and economics

        Returns:
            (success, CostOfWaitingResult or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/cost-of-waiting", request.to_dict())

        if response.success:
            return True, CostOfWaitingResult.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to analyze cost of waiting"

    def assess_disease_pressure(self, request: DiseasePressureRequest) -> tuple[bool, DiseasePressureResponse | str]:
        """
        Assess disease pressure based on weather history.

        Args:
            request: DiseasePressureRequest with weather history

        Returns:
            (success, DiseasePressureResponse or error message)
        """
        response = self._client.post(f"{self.BASE_PATH}/disease-pressure", request.to_dict())

        if response.success:
            return True, DiseasePressureResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to assess disease pressure"

    def get_growth_stage_timing(
        self,
        crop: str,
        growth_stage: str,
        spray_type: str = "fungicide"
    ) -> tuple[bool, GrowthStageTimingResponse | str]:
        """
        Get spray timing guidance for a specific growth stage.

        Args:
            crop: Crop type (corn, soybean)
            growth_stage: Current growth stage (V6, VT, R1, etc.)
            spray_type: Type of spray application

        Returns:
            (success, GrowthStageTimingResponse or error message)
        """
        response = self._client.get(
            f"{self.BASE_PATH}/growth-stage-timing/{crop}/{growth_stage}",
            params={"spray_type": spray_type}
        )

        if response.success:
            return True, GrowthStageTimingResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get growth stage timing"


# Singleton instance
_spray_timing_api: Optional[SprayTimingAPI] = None


def get_spray_timing_api() -> SprayTimingAPI:
    """Get the global spray timing API instance."""
    global _spray_timing_api
    if _spray_timing_api is None:
        _spray_timing_api = SprayTimingAPI()
    return _spray_timing_api
