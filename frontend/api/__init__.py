"""
AgTools API Client Package

HTTP client for communicating with the FastAPI backend.
"""

from .client import (
    APIClient,
    APIResponse,
    APIError,
    ConnectionError,
    ValidationError,
    NotFoundError,
    ServerError,
    get_api_client,
    reset_api_client,
)
from .yield_response_api import YieldResponseAPI, get_yield_response_api
from .spray_api import SprayTimingAPI, get_spray_timing_api
from .pricing_api import PricingAPI, get_pricing_api
from .cost_optimizer_api import CostOptimizerAPI, get_cost_optimizer_api

__all__ = [
    # Base client
    "APIClient",
    "APIResponse",
    "APIError",
    "ConnectionError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "get_api_client",
    "reset_api_client",
    # Yield Response
    "YieldResponseAPI",
    "get_yield_response_api",
    # Spray Timing
    "SprayTimingAPI",
    "get_spray_timing_api",
    # Pricing
    "PricingAPI",
    "get_pricing_api",
    # Cost Optimizer
    "CostOptimizerAPI",
    "get_cost_optimizer_api",
]
