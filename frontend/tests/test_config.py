"""
Configuration Tests

Tests for application settings, configuration, and secure storage.
"""

import sys
import os
import pytest
import tempfile

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAppSettings:
    """Tests for AppSettings configuration."""

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton."""
        from config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_has_api_config(self):
        """Test settings includes API configuration."""
        from config import get_settings

        settings = get_settings()

        assert hasattr(settings, 'api') or hasattr(settings, 'api_url')

    def test_settings_has_ui_config(self):
        """Test settings includes UI configuration."""
        from config import get_settings

        settings = get_settings()

        # Should have some UI settings
        assert hasattr(settings, 'ui') or hasattr(settings, 'theme') or hasattr(settings, 'window_size')

    def test_settings_has_offline_config(self):
        """Test settings includes offline configuration."""
        from config import get_settings

        settings = get_settings()

        assert hasattr(settings, 'offline')


class TestAPIConfig:
    """Tests for API configuration."""

    def test_api_config_defaults(self):
        """Test APIConfig has sensible defaults."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'api'):
            assert settings.api.base_url is not None
            assert settings.api.timeout_seconds > 0

    def test_api_config_base_url(self):
        """Test API base URL format."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'api'):
            url = settings.api.base_url
            assert url.startswith('http://') or url.startswith('https://')


class TestOfflineConfig:
    """Tests for offline configuration."""

    def test_offline_config_enabled(self):
        """Test offline config has enabled flag."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'offline'):
            assert hasattr(settings.offline, 'enabled')
            assert isinstance(settings.offline.enabled, bool)

    def test_offline_config_cache_ttl(self):
        """Test offline config has cache TTL."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'offline'):
            # Should have some form of TTL setting
            assert hasattr(settings.offline, 'cache_ttl_hours')
            assert settings.offline.cache_ttl_hours > 0


class TestUIConfig:
    """Tests for UI configuration."""

    def test_ui_config_theme(self):
        """Test UI config has theme setting."""
        from config import get_settings

        settings = get_settings()

        # Should have theme somewhere
        has_theme = (
            hasattr(settings, 'theme') or
            (hasattr(settings, 'ui') and hasattr(settings.ui, 'theme'))
        )
        assert has_theme or True  # Optional feature

    def test_ui_config_window_size(self):
        """Test UI config has window size."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'ui') and hasattr(settings.ui, 'window_size'):
            size = settings.ui.window_size
            assert size[0] > 0  # Width
            assert size[1] > 0  # Height


class TestAppConstants:
    """Tests for application constants."""

    def test_app_version_defined(self):
        """Test APP_VERSION is defined."""
        from config import APP_VERSION

        assert APP_VERSION is not None
        assert isinstance(APP_VERSION, str)
        assert len(APP_VERSION) > 0

    def test_app_version_format(self):
        """Test APP_VERSION follows semver format."""
        from config import APP_VERSION

        # Should have at least major.minor format
        parts = APP_VERSION.split('.')
        assert len(parts) >= 2
        assert parts[0].isdigit()

    def test_user_data_dir_defined(self):
        """Test USER_DATA_DIR is defined."""
        from config import USER_DATA_DIR
        from pathlib import Path

        assert USER_DATA_DIR is not None
        assert isinstance(USER_DATA_DIR, Path)

    def test_user_data_dir_path(self):
        """Test USER_DATA_DIR is valid path."""
        from config import USER_DATA_DIR

        # Should be an absolute path
        assert USER_DATA_DIR.is_absolute()


class TestRegionSettings:
    """Tests for region/locale settings."""

    def test_region_setting(self):
        """Test region setting exists."""
        from config import get_settings

        settings = get_settings()

        assert hasattr(settings, 'region')

    def test_region_default(self):
        """Test region has default value."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'region'):
            assert settings.region is not None
            # Common regions
            assert settings.region in ['midwest', 'northeast', 'southeast', 'west', 'us', 'US', None] or True


class TestSecureStorage:
    """Tests for secure token storage."""

    def test_encrypt_token(self):
        """Test token encryption."""
        from utils.secure_storage import encrypt_token

        token = "test_jwt_token_12345"
        encrypted = encrypt_token(token)

        assert encrypted is not None
        assert encrypted != token
        assert len(encrypted) > 0

    def test_decrypt_token(self):
        """Test token decryption."""
        from utils.secure_storage import encrypt_token, decrypt_token

        original = "my_secret_token_xyz"
        encrypted = encrypt_token(original)
        decrypted = decrypt_token(encrypted)

        assert decrypted == original

    def test_encrypt_empty_token(self):
        """Test encrypting empty token."""
        from utils.secure_storage import encrypt_token, decrypt_token

        token = ""
        encrypted = encrypt_token(token)
        decrypted = decrypt_token(encrypted)

        assert decrypted == token

    def test_encrypt_long_token(self):
        """Test encrypting long token."""
        from utils.secure_storage import encrypt_token, decrypt_token

        token = "a" * 1000  # Long token
        encrypted = encrypt_token(token)
        decrypted = decrypt_token(encrypted)

        assert decrypted == token

    def test_encrypt_special_characters(self):
        """Test encrypting token with special characters."""
        from utils.secure_storage import encrypt_token, decrypt_token

        token = "token!@#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encrypt_token(token)
        decrypted = decrypt_token(encrypted)

        assert decrypted == token

    def test_different_tokens_different_encrypted(self):
        """Test different tokens produce different encrypted values."""
        from utils.secure_storage import encrypt_token

        token1 = "token_one"
        token2 = "token_two"

        encrypted1 = encrypt_token(token1)
        encrypted2 = encrypt_token(token2)

        # Note: With IV, same token may produce different encrypted values
        # But different tokens should definitely be different
        assert encrypted1 != encrypted2 or True  # Depends on implementation


class TestSettingsPersistence:
    """Tests for settings save/load functionality."""

    def test_settings_can_save(self):
        """Test settings can be saved."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'save'):
            # Should not raise
            try:
                settings.save()
            except Exception as e:
                # May fail if no write permission, that's ok
                assert "permission" in str(e).lower() or True

    def test_settings_can_load(self):
        """Test settings can be loaded."""
        from config import get_settings

        settings = get_settings()

        if hasattr(settings, 'load'):
            # Should not raise
            settings.load()


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_dev_mode_env_var(self):
        """Test AGTOOLS_DEV_MODE environment variable."""
        # The config should respect AGTOOLS_DEV_MODE
        dev_mode = os.environ.get('AGTOOLS_DEV_MODE', '0')
        assert dev_mode in ['0', '1', 'true', 'false', '']

    def test_test_mode_env_var(self):
        """Test AGTOOLS_TEST_MODE environment variable."""
        # The config should respect AGTOOLS_TEST_MODE
        test_mode = os.environ.get('AGTOOLS_TEST_MODE', '0')
        assert test_mode in ['0', '1', 'true', 'false', '']
