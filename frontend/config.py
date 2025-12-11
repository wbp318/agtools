"""
AgTools Frontend Configuration

Application settings, API configuration, and environment management.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json


# Application Info
APP_NAME = "AgTools Professional"
APP_VERSION = "2.3.0"
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


@dataclass
class APIConfig:
    """API connection configuration."""
    base_url: str = "http://localhost:8000"
    api_prefix: str = "/api/v1"
    timeout_seconds: float = 30.0
    retry_attempts: int = 3

    @property
    def full_url(self) -> str:
        return f"{self.base_url}{self.api_prefix}"


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

    def save(self) -> None:
        """Save settings to disk."""
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

        settings_dict = {
            "api": {
                "base_url": self.api.base_url,
                "timeout_seconds": self.api.timeout_seconds,
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
        }

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_dict, f, indent=2)

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from disk or return defaults."""
        settings = cls()

        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    data = json.load(f)

                # Apply loaded settings
                if "api" in data:
                    settings.api.base_url = data["api"].get("base_url", settings.api.base_url)
                    settings.api.timeout_seconds = data["api"].get("timeout_seconds", settings.api.timeout_seconds)

                if "ui" in data:
                    settings.ui.theme = data["ui"].get("theme", settings.ui.theme)
                    settings.ui.sidebar_width = data["ui"].get("sidebar_width", settings.ui.sidebar_width)

                if "offline" in data:
                    settings.offline.enabled = data["offline"].get("enabled", settings.offline.enabled)
                    settings.offline.cache_ttl_hours = data["offline"].get("cache_ttl_hours", settings.offline.cache_ttl_hours)

                settings.region = data.get("region", settings.region)
                settings.default_crop = data.get("default_crop", settings.default_crop)
                settings.last_sync = data.get("last_sync")

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load settings: {e}")

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
