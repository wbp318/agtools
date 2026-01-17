"""
Rate Limiter Configuration
AgTools v6.13.2 (Final)

Provides shared rate limiting configuration for all API routes.
Uses slowapi for rate limiting based on client IP address.

Rate Limit Tiers:
- STRICT (5/minute): Authentication, password operations
- MODERATE (30/minute): Write operations (POST, PUT, DELETE)
- STANDARD (60/minute): Read operations (GET single items)
- RELAXED (120/minute): List operations, health checks
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Check if running in test mode
IS_TEST_MODE = os.environ.get("AGTOOLS_TEST_MODE") == "1"

# In test mode, use a no-op key function that returns None (disables rate limiting)
def _get_key_func():
    if IS_TEST_MODE:
        return lambda request: None  # Disable rate limiting in tests
    return get_remote_address

# Shared rate limiter instance
limiter = Limiter(key_func=_get_key_func(), enabled=not IS_TEST_MODE)

# Rate limit constants for consistent application
RATE_STRICT = "5/minute"       # Auth, password changes
RATE_MODERATE = "30/minute"    # Write operations
RATE_STANDARD = "60/minute"    # Read operations
RATE_RELAXED = "120/minute"    # List operations, health checks


def configure_rate_limiter(app):
    """
    Configure rate limiter for the FastAPI application.

    Call this in main.py after creating the app:
        from middleware.rate_limiter import configure_rate_limiter
        configure_rate_limiter(app)
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Export the limiter for use in route decorators
__all__ = [
    'limiter',
    'configure_rate_limiter',
    'RATE_STRICT',
    'RATE_MODERATE',
    'RATE_STANDARD',
    'RATE_RELAXED'
]
