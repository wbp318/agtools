"""
Pest & Disease Service
======================
Unified service wrapper for pest and disease identification.
Provides the API interface expected by the routers.

AgTools v6.14.0
"""

from typing import List, Dict, Optional, Any
from .pest_identification import PestIdentifier
from .disease_identification import DiseaseIdentifier


class PestDiseaseService:
    """Unified service for pest and disease identification."""

    _instance = None

    def __new__(cls):
        """Singleton pattern for service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.pest_identifier = PestIdentifier()
        self.disease_identifier = DiseaseIdentifier()
        self._initialized = True

    def identify_pest(
        self,
        crop: str,
        growth_stage: str,
        symptoms: List[str],
        field_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Identify pest based on symptoms and conditions.

        Args:
            crop: Crop type ('corn', 'soybean')
            growth_stage: Growth stage (e.g., 'V6', 'R1')
            symptoms: List of observed symptoms
            field_conditions: Optional field context

        Returns:
            List of pest identification results with confidence scores
        """
        results = self.pest_identifier.identify_by_symptoms(
            crop=crop,
            symptoms=symptoms,
            growth_stage=growth_stage,
            field_conditions=field_conditions
        )

        # Transform to match API response model
        transformed = []
        for idx, result in enumerate(results):
            transformed.append({
                "id": result.get("id", idx + 1),
                "common_name": result.get("common_name", result.get("name", "Unknown")),
                "scientific_name": result.get("scientific_name", ""),
                "confidence": result.get("confidence", 0.0),
                "description": result.get("description", ""),
                "damage_symptoms": result.get("damage_symptoms", result.get("symptoms", "")),
                "identification_features": result.get("identification_features", ""),
                "economic_threshold": result.get("economic_threshold", None)
            })

        return transformed

    def identify_disease(
        self,
        crop: str,
        growth_stage: str,
        symptoms: List[str],
        weather_conditions: Optional[str] = None
    ) -> List[Dict]:
        """
        Identify disease based on symptoms and conditions.

        Args:
            crop: Crop type ('corn', 'soybean')
            growth_stage: Growth stage (e.g., 'V6', 'R1')
            symptoms: List of observed symptoms
            weather_conditions: Weather description

        Returns:
            List of disease identification results with confidence scores
        """
        results = self.disease_identifier.identify_by_symptoms(
            crop=crop,
            symptoms=symptoms,
            growth_stage=growth_stage,
            weather_conditions=weather_conditions
        )

        # Transform to match API response model
        transformed = []
        for idx, result in enumerate(results):
            transformed.append({
                "id": result.get("id", idx + 1),
                "common_name": result.get("common_name", result.get("name", "Unknown")),
                "scientific_name": result.get("scientific_name", ""),
                "confidence": result.get("confidence", 0.0),
                "description": result.get("description", ""),
                "symptoms": result.get("symptoms", ""),
                "favorable_conditions": result.get("favorable_conditions", ""),
                "management": result.get("management", result.get("treatment", None))
            })

        return transformed


# Singleton accessor
_service_instance = None


def get_pest_disease_service() -> PestDiseaseService:
    """Get the singleton PestDiseaseService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = PestDiseaseService()
    return _service_instance
