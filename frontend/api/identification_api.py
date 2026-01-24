"""
Pest and Disease Identification API Client

API calls for pest/disease identification and lookup.
"""

from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import APIClient, get_api_client
from models.identification import (
    PestIdentificationRequest, DiseaseIdentificationRequest,
    PestInfo, DiseaseInfo,
    PestListResponse, DiseaseListResponse,
)


class IdentificationAPI:
    """
    API client for pest and disease identification endpoints.

    All methods return (success, result_or_error) tuples.
    """

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    # =========================================================================
    # Pest Endpoints
    # =========================================================================

    def get_pests(self, crop: Optional[str] = None) -> tuple[bool, PestListResponse | str]:
        """
        Get list of pests, optionally filtered by crop.

        Args:
            crop: Optional crop filter ('corn' or 'soybean')

        Returns:
            (success, PestListResponse or error message)
        """
        params = {}
        if crop:
            params["crop"] = crop

        response = self._client.get("/pests", params=params if params else None)

        if response.success:
            return True, PestListResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get pests"

    def identify_pest(self, request: PestIdentificationRequest) -> tuple[bool, List[PestInfo] | str]:
        """
        Identify pest based on symptoms and conditions.

        Args:
            request: PestIdentificationRequest with crop, stage, symptoms

        Returns:
            (success, list of PestInfo matches or error message)
        """
        response = self._client.post("/identify/pest", request.to_dict())

        if response.success:
            if isinstance(response.data, list):
                return True, [PestInfo.from_dict(p) for p in response.data]
            else:
                return True, []
        else:
            return False, response.error_message or "Failed to identify pest"

    # =========================================================================
    # Disease Endpoints
    # =========================================================================

    def get_diseases(self, crop: Optional[str] = None) -> tuple[bool, DiseaseListResponse | str]:
        """
        Get list of diseases, optionally filtered by crop.

        Args:
            crop: Optional crop filter ('corn' or 'soybean')

        Returns:
            (success, DiseaseListResponse or error message)
        """
        params = {}
        if crop:
            params["crop"] = crop

        response = self._client.get("/diseases", params=params if params else None)

        if response.success:
            return True, DiseaseListResponse.from_dict(response.data)
        else:
            return False, response.error_message or "Failed to get diseases"

    def identify_disease(self, request: DiseaseIdentificationRequest) -> tuple[bool, List[DiseaseInfo] | str]:
        """
        Identify disease based on symptoms and conditions.

        Args:
            request: DiseaseIdentificationRequest with crop, stage, symptoms

        Returns:
            (success, list of DiseaseInfo matches or error message)
        """
        response = self._client.post("/identify/disease", request.to_dict())

        if response.success:
            if isinstance(response.data, list):
                return True, [DiseaseInfo.from_dict(d) for d in response.data]
            else:
                return True, []
        else:
            return False, response.error_message or "Failed to identify disease"


# Singleton instance
_identification_api: Optional[IdentificationAPI] = None


def get_identification_api() -> IdentificationAPI:
    """Get the singleton IdentificationAPI instance."""
    global _identification_api
    if _identification_api is None:
        _identification_api = IdentificationAPI()
    return _identification_api


def reset_identification_api() -> None:
    """Reset the singleton (for testing)."""
    global _identification_api
    _identification_api = None
