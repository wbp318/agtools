"""
Pytest configuration and fixtures for AgTools backend tests.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_pest_request():
    """Sample pest identification request."""
    return {
        "crop": "corn",
        "growth_stage": "V6",
        "symptoms": ["leaf_holes", "frass_present"],
        "severity_rating": 5,
    }


@pytest.fixture
def sample_disease_request():
    """Sample disease identification request."""
    return {
        "crop": "corn",
        "growth_stage": "R1",
        "symptoms": ["leaf_lesions", "gray_spots"],
        "weather_conditions": "warm_wet",
    }


@pytest.fixture
def sample_spray_conditions():
    """Sample spray timing evaluation request."""
    return {
        "weather": {
            "datetime": "2025-06-15T10:00:00",
            "temp_f": 78,
            "humidity_pct": 55,
            "wind_mph": 6,
            "wind_direction": "SW",
            "precip_chance_pct": 10,
            "precip_amount_in": 0,
            "cloud_cover_pct": 30,
            "dew_point_f": 58
        },
        "spray_type": "herbicide"
    }


@pytest.fixture
def sample_quick_estimate():
    """Sample quick estimate request."""
    return {
        "acres": 160,
        "crop": "corn",
        "is_irrigated": False,
        "yield_goal": 200
    }


@pytest.fixture
def sample_eor_request():
    """Sample economic optimum rate request."""
    return {
        "crop": "corn",
        "nutrient": "nitrogen",
        "soil_test_level": "medium",
        "yield_potential": 200,
        "previous_crop": "soybean",
        "nutrient_price_per_lb": 0.65,
        "grain_price_per_bu": 4.50
    }
