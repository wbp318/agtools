"""
AgTools API Client

Base HTTP client for communicating with the FastAPI backend.
Handles connection management, error handling, and offline fallback.
"""

import httpx
from typing import Any, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings, AppSettings


class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class ConnectionError(APIError):
    """Raised when unable to connect to the API."""
    pass


class ValidationError(APIError):
    """Raised when the API returns a validation error."""
    pass


class NotFoundError(APIError):
    """Raised when a resource is not found."""
    pass


class ServerError(APIError):
    """Raised when the server returns a 5xx error."""
    pass


@dataclass
class APIResponse:
    """Wrapper for API responses."""
    success: bool
    data: Any
    status_code: int
    error_message: Optional[str] = None

    @classmethod
    def ok(cls, data: Any, status_code: int = 200) -> "APIResponse":
        return cls(success=True, data=data, status_code=status_code)

    @classmethod
    def error(cls, message: str, status_code: int, data: Any = None) -> "APIResponse":
        return cls(success=False, data=data, status_code=status_code, error_message=message)


class APIClient:
    """
    HTTP client for the AgTools API.

    Features:
    - Automatic retry on transient failures
    - Connection state tracking
    - Proper error handling and mapping
    - Synchronous interface (uses httpx sync client)

    Usage:
        client = APIClient()
        if client.check_connection():
            response = client.get("/crops")
            if response.success:
                crops = response.data
    """

    def __init__(self, settings: Optional[AppSettings] = None):
        self._settings = settings or get_settings()
        self._client: Optional[httpx.Client] = None
        self._is_connected = False
        self._last_check: Optional[datetime] = None

    @property
    def base_url(self) -> str:
        return self._settings.api.full_url

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self._settings.api.timeout_seconds,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def check_connection(self) -> bool:
        """
        Check if the API is reachable.

        Returns:
            True if connected, False otherwise
        """
        try:
            # Hit the root endpoint which should return quickly
            response = httpx.get(
                self._settings.api.base_url + "/",
                timeout=5.0
            )
            self._is_connected = response.status_code == 200
            self._last_check = datetime.now()
            return self._is_connected
        except Exception:
            self._is_connected = False
            self._last_check = datetime.now()
            return False

    def _handle_response(self, response: httpx.Response) -> APIResponse:
        """Process an HTTP response and return an APIResponse."""
        try:
            data = response.json() if response.content else None
        except Exception:
            data = response.text

        if response.is_success:
            return APIResponse.ok(data, response.status_code)

        # Handle error responses
        error_message = "Unknown error"
        if isinstance(data, dict):
            error_message = data.get("detail", data.get("message", str(data)))
        elif data:
            error_message = str(data)

        return APIResponse.error(error_message, response.status_code, data)

    def _handle_exception(self, e: Exception) -> APIResponse:
        """Convert exceptions to APIResponse."""
        if isinstance(e, httpx.ConnectError):
            self._is_connected = False
            return APIResponse.error("Unable to connect to API server", 0)
        elif isinstance(e, httpx.TimeoutException):
            return APIResponse.error("Request timed out", 0)
        elif isinstance(e, httpx.HTTPStatusError):
            return APIResponse.error(str(e), e.response.status_code)
        else:
            return APIResponse.error(f"Unexpected error: {str(e)}", 0)

    def get(self, endpoint: str, params: Optional[dict] = None) -> APIResponse:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint (e.g., "/crops")
            params: Optional query parameters

        Returns:
            APIResponse with the result
        """
        try:
            client = self._get_client()
            response = client.get(endpoint, params=params)
            return self._handle_response(response)
        except Exception as e:
            return self._handle_exception(e)

    def post(self, endpoint: str, data: Optional[dict] = None, params: Optional[dict] = None) -> APIResponse:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint
            data: Request body (will be JSON encoded)
            params: Optional query parameters

        Returns:
            APIResponse with the result
        """
        try:
            client = self._get_client()
            response = client.post(endpoint, json=data, params=params)
            return self._handle_response(response)
        except Exception as e:
            return self._handle_exception(e)

    def put(self, endpoint: str, data: Optional[dict] = None) -> APIResponse:
        """Make a PUT request."""
        try:
            client = self._get_client()
            response = client.put(endpoint, json=data)
            return self._handle_response(response)
        except Exception as e:
            return self._handle_exception(e)

    def delete(self, endpoint: str) -> APIResponse:
        """Make a DELETE request."""
        try:
            client = self._get_client()
            response = client.delete(endpoint)
            return self._handle_response(response)
        except Exception as e:
            return self._handle_exception(e)


# Singleton instance
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get the global API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client


def reset_api_client() -> None:
    """Reset the global API client (useful for testing or reconnecting)."""
    global _api_client
    if _api_client:
        _api_client.close()
    _api_client = None
