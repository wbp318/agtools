"""
AgTools Frontend Configuration
v6.13.3

Application settings, API configuration, and environment management.
Includes secure encrypted storage for authentication tokens.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json

# Secure token storage
from utils.secure_storage import (
    encrypt_token,
    decrypt_token,
    migrate_plaintext_token,
    is_encryption_available
)


# Application Info
APP_NAME = "AgTools Professional"
APP_VERSION = "2.4.0"
APP_ORGANIZATION = "New Generation Farms"


# Paths
BASE_DIR = Path(__file__).parent
RESOURCES_DIR = BASE_DIR / "resources"
DATA_DIR = RESOURCES_DIR / "data"
ICONS_DIR = RESOURCES_DIR / "icons"
IMAGES_DIR = RESOURCES_DIR / "images"

# User data location (for settings, cache, etc.)
USER_DATA_DIR = Path.home() / ".agtools"
CACHE_DIR = USER_DATA_DIR / "cache"
SETTINGS_FILE = USER_DATA_DIR / "settings.json"


def _get_default_base_url() -> str:
    """
    Get the default API base URL.

    Priority:
    1. AGTOOLS_API_URL environment variable
    2. Default to localhost for development

    For production, set AGTOOLS_API_URL=https://api.yourfarm.com
    """
    env_url = os.getenv("AGTOOLS_API_URL")
    if env_url:
        return env_url.rstrip("/")
    return "http://localhost:8000"


@dataclass
class APIConfig:
    """API connection configuration."""
    base_url: str = None  # Set in __post_init__
    api_prefix: str = "/api/v1"
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    verify_ssl: bool = True  # SSL certificate verification
    allow_insecure_localhost: bool = True  # Allow HTTP for localhost only

    def __post_init__(self):
        if self.base_url is None:
            self.base_url = _get_default_base_url()

    @property
    def full_url(self) -> str:
        return f"{self.base_url}{self.api_prefix}"

    @property
    def is_https(self) -> bool:
        """Check if using HTTPS."""
        return self.base_url.startswith("https://")

    @property
    def is_localhost(self) -> bool:
        """Check if connecting to localhost."""
        return "localhost" in self.base_url or "127.0.0.1" in self.base_url

    def validate_security(self) -> tuple[bool, str]:
        """
        Validate security configuration.

        Returns:
            (is_valid, warning_message)
        """
        if not self.is_https:
            if self.is_localhost and self.allow_insecure_localhost:
                return True, ""
            return False, "WARNING: Using HTTP for non-localhost. Set AGTOOLS_API_URL to an HTTPS URL for production."
        return True, ""


@dataclass
class UIConfig:
    """User interface configuration."""
    # Window settings
    min_width: int = 1024
    min_height: int = 600
    default_width: int = 1400
    default_height: int = 900

    # Sidebar
    sidebar_width: int = 200
    sidebar_collapsed_width: int = 60

    # Theme
    theme: str = "light"  # "light" or "dark"

    # Font sizes
    font_size_body: int = 11
    font_size_header: int = 16
    font_size_title: int = 24


@dataclass
class OfflineConfig:
    """Offline mode configuration."""
    enabled: bool = True
    cache_ttl_hours: int = 24
    sync_on_startup: bool = True
    auto_fallback: bool = True  # Auto switch to offline if API unavailable


@dataclass
class AppSettings:
    """Complete application settings."""
    api: APIConfig = field(default_factory=APIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    offline: OfflineConfig = field(default_factory=OfflineConfig)

    # User preferences
    region: str = "midwest_corn_belt"
    default_crop: str = "corn"

    # State
    is_offline: bool = False
    last_sync: Optional[str] = None

    # Authentication
    auth_token: str = ""

    # App info
    app_version: str = APP_VERSION
    app_name: str = APP_NAME

    # Extra settings storage
    _extra: dict = field(default_factory=dict)

    def get(self, key: str, default=None):
        """Get a setting value by key."""
        if hasattr(self, key):
            return getattr(self, key)
        return self._extra.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a setting value by key."""
        if hasattr(self, key) and key != '_extra':
            setattr(self, key, value)
        else:
            self._extra[key] = value

    def save(self) -> None:
        """Save settings to disk with encrypted token storage."""
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Encrypt the auth token before saving
        encrypted_token = encrypt_token(self.auth_token) if self.auth_token else ""

        settings_dict = {
            "api": {
                "base_url": self.api.base_url,
                "timeout_seconds": self.api.timeout_seconds,
                "verify_ssl": self.api.verify_ssl,
            },
            "ui": {
                "theme": self.ui.theme,
                "sidebar_width": self.ui.sidebar_width,
            },
            "offline": {
                "enabled": self.offline.enabled,
                "cache_ttl_hours": self.offline.cache_ttl_hours,
            },
            "region": self.region,
            "default_crop": self.default_crop,
            "last_sync": self.last_sync,
            "auth_token": encrypted_token,  # Stored encrypted
            "_encrypted": True,  # Marker for encrypted storage format
        }

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_dict, f, indent=2)

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from disk or return defaults.

        Handles decryption of stored tokens and migration from plaintext.
        """
        settings = cls()
        needs_resave = False

        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)

                # Apply loaded settings
                if "api" in data:
                    settings.api.base_url = data["api"].get("base_url", settings.api.base_url)
                    settings.api.timeout_seconds = data["api"].get("timeout_seconds", settings.api.timeout_seconds)
                    settings.api.verify_ssl = data["api"].get("verify_ssl", settings.api.verify_ssl)

                if "ui" in data:
                    settings.ui.theme = data["ui"].get("theme", settings.ui.theme)
                    settings.ui.sidebar_width = data["ui"].get("sidebar_width", settings.ui.sidebar_width)

                if "offline" in data:
                    settings.offline.enabled = data["offline"].get("enabled", settings.offline.enabled)
                    settings.offline.cache_ttl_hours = data["offline"].get("cache_ttl_hours", settings.offline.cache_ttl_hours)

                settings.region = data.get("region", settings.region)
                settings.default_crop = data.get("default_crop", settings.default_crop)
                settings.last_sync = data.get("last_sync")

                # Handle token - decrypt if encrypted, migrate if plaintext
                stored_token = data.get("auth_token", "")
                is_encrypted_format = data.get("_encrypted", False)

                if stored_token:
                    if is_encrypted_format:
                        # Token is encrypted, decrypt it
                        settings.auth_token = decrypt_token(stored_token)
                    else:
                        # Legacy plaintext token - migrate to encrypted
                        settings.auth_token = stored_token
                        needs_resave = True  # Re-save with encryption
                else:
                    settings.auth_token = ""

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load settings: {e}")

        # Re-save if we migrated a plaintext token
        if needs_resave and settings.auth_token:
            try:
                settings.save()
                print("Settings migrated to encrypted token storage.")
            except Exception as e:
                print(f"Warning: Could not migrate settings: {e}")

        return settings


# Global settings instance (lazy loaded)
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings.load()
    return _settings


def reset_settings() -> AppSettings:
    """Reset settings to defaults."""
    global _settings
    _settings = AppSettings()
    _settings.save()
    return _settings
