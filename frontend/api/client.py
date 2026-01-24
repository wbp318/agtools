"""
AgTools API Client
v6.13.4

Base HTTP client for communicating with the FastAPI backend.
Handles connection management, error handling, offline fallback,
and HTTPS/SSL configuration for production deployments.
"""

import httpx
from typing import Any, Optional, Callable
from dataclasses import dataclass
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
    from_cache: bool = False

    @classmethod
    def ok(cls, data: Any, status_code: int = 200, from_cache: bool = False) -> "APIResponse":
        return cls(success=True, data=data, status_code=status_code, from_cache=from_cache)

    @classmethod
    def error(cls, message: str, status_code: int, data: Any = None) -> "APIResponse":
        return cls(success=False, data=data, status_code=status_code, error_message=message)

    @classmethod
    def offline_error(cls, message: str = "Offline - no cached data available") -> "APIResponse":
        return cls(success=False, data=None, status_code=0, error_message=message)


class APIClient:
    """
    HTTP client for the AgTools API with offline support.

    Features:
    - Automatic retry on transient failures
    - Connection state tracking
    - Proper error handling and mapping
    - Offline fallback to local cache
    - Synchronous interface (uses httpx sync client)

    Usage:
        client = APIClient()
        if client.check_connection():
            response = client.get("/crops")
            if response.success:
                crops = response.data
        else:
            # Will automatically use cache if available
            response = client.get_with_cache("/pricing/prices", "prices", "all")
    """

    def __init__(self, settings: Optional[AppSettings] = None):
        self._settings = settings or get_settings()
        self._client: Optional[httpx.Client] = None
        self._is_connected = False
        self._last_check: Optional[datetime] = None
        self._db = None  # Lazy loaded
        self._auth_token: Optional[str] = None  # JWT access token

    def _get_db(self):
        """Lazy load the local database."""
        if self._db is None:
            from database.local_db import get_local_db
            self._db = get_local_db()
        return self._db

    @property
    def base_url(self) -> str:
        return self._settings.api.full_url

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client with proper SSL configuration."""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self._auth_token:
                headers["Authorization"] = f"Bearer {self._auth_token}"

            # Configure SSL verification
            # For localhost development, allow unverified connections
            # For production HTTPS, enforce certificate verification
            verify_ssl = self._settings.api.verify_ssl
            if not verify_ssl and not self._settings.api.is_localhost:
                # Force SSL verification for non-localhost unless explicitly disabled
                print("WARNING: SSL verification disabled for non-localhost connection")

            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self._settings.api.timeout_seconds,
                headers=headers,
                verify=verify_ssl,
                # Follow redirects (e.g., HTTP->HTTPS)
                follow_redirects=True
            )

            # Log security status on first connection
            is_valid, warning = self._settings.api.validate_security()
            if warning:
                print(warning)

        return self._client

    def set_auth_token(self, token: str) -> None:
        """Set the authentication token for API requests."""
        self._auth_token = token
        # Force client recreation to update headers
        if self._client:
            self._client.close()
            self._client = None

    def clear_auth_token(self) -> None:
        """Clear the authentication token."""
        self._auth_token = None
        if self._client:
            self._client.close()
            self._client = None

    @property
    def has_auth_token(self) -> bool:
        """Check if an auth token is set."""
        return self._auth_token is not None

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

    def post_file(
        self,
        endpoint: str,
        files: dict,
        data: Optional[dict] = None
    ) -> APIResponse:
        """
        Make a POST request with file upload.

        Args:
            endpoint: API endpoint
            files: Dict of field_name -> (filename, file_object, content_type)
            data: Optional form data fields

        Returns:
            APIResponse with the result
        """
        try:
            client = self._get_client()
            response = client.post(endpoint, files=files, data=data)
            return self._handle_response(response)
        except Exception as e:
            return self._handle_exception(e)

    # -------------------------------------------------------------------------
    # Offline-Capable Methods
    # -------------------------------------------------------------------------

    def get_with_cache(self, endpoint: str, cache_category: str, cache_key: str,
                       params: Optional[dict] = None, ttl_hours: int = 24) -> APIResponse:
        """
        Make a GET request with cache fallback.

        If online, fetches from API and caches the result.
        If offline, returns cached data if available.

        Args:
            endpoint: API endpoint
            cache_category: Category for cache storage (e.g., "prices", "pests")
            cache_key: Unique key within category
            params: Optional query parameters
            ttl_hours: Cache TTL in hours

        Returns:
            APIResponse (check from_cache attribute)
        """
        db = self._get_db()

        # Try API first if connected
        if self._is_connected or self.check_connection():
            response = self.get(endpoint, params)

            if response.success:
                # Cache the successful response
                db.cache_set(cache_category, cache_key, response.data, ttl_hours)
                return response
            elif response.status_code == 0:
                # Connection lost mid-request, try cache
                pass
            else:
                # Server returned an error, don't use cache
                return response

        # Try cache
        cached_data = db.cache_get(cache_category, cache_key)
        if cached_data is not None:
            return APIResponse.ok(cached_data, 200, from_cache=True)

        return APIResponse.offline_error()

    def post_with_cache(self, endpoint: str, data: Optional[dict],
                        cache_category: str, cache_key: str,
                        params: Optional[dict] = None, ttl_hours: int = 24) -> APIResponse:
        """
        Make a POST request with cache fallback.

        For calculation endpoints that can be cached based on input parameters.

        Args:
            endpoint: API endpoint
            data: Request body
            cache_category: Category for cache storage
            cache_key: Unique key (should be derived from input data)
            params: Optional query parameters
            ttl_hours: Cache TTL in hours

        Returns:
            APIResponse (check from_cache attribute)
        """
        db = self._get_db()

        # Try API first if connected
        if self._is_connected or self.check_connection():
            response = self.post(endpoint, data, params)

            if response.success:
                # Cache the successful response
                db.cache_set(cache_category, cache_key, response.data, ttl_hours)
                return response
            elif response.status_code == 0:
                # Connection lost, try cache
                pass
            else:
                return response

        # Try cache
        cached_data = db.cache_get(cache_category, cache_key)
        if cached_data is not None:
            return APIResponse.ok(cached_data, 200, from_cache=True)

        return APIResponse.offline_error()

    def post_with_offline_calc(self, endpoint: str, data: Optional[dict],
                               offline_calculator: Callable[[dict], Any],
                               cache_category: str = None, cache_key: str = None,
                               params: Optional[dict] = None) -> APIResponse:
        """
        Make a POST request with offline calculation fallback.

        If online, fetches from API.
        If offline, uses the provided offline calculator function.

        Args:
            endpoint: API endpoint
            data: Request body
            offline_calculator: Function that takes request data and returns result
            cache_category: Optional category for caching API response
            cache_key: Optional key for caching
            params: Optional query parameters

        Returns:
            APIResponse
        """
        db = self._get_db()

        # Try API first if connected
        if self._is_connected or self.check_connection():
            response = self.post(endpoint, data, params)

            if response.success:
                # Optionally cache
                if cache_category and cache_key:
                    db.cache_set(cache_category, cache_key, response.data, 24)
                return response
            elif response.status_code == 0:
                # Connection lost, use offline calculator
                pass
            else:
                return response

        # Use offline calculator
        try:
            result = offline_calculator(data or {})
            return APIResponse.ok(result, 200, from_cache=True)
        except Exception as e:
            return APIResponse.error(f"Offline calculation error: {str(e)}", 0)

    def queue_for_sync(self, action: str, endpoint: str, payload: dict = None) -> int:
        """
        Queue a write operation for later sync.

        Use this when offline to queue changes that will be
        synchronized when connection is restored.

        Args:
            action: HTTP method (POST, PUT, DELETE)
            endpoint: API endpoint
            payload: Request payload

        Returns:
            Queue ID
        """
        db = self._get_db()
        return db.queue_sync_action(action, endpoint, payload)


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
