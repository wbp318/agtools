"""
AgTools Application

PyQt6 application setup and initialization with login flow.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import APP_NAME, APP_ORGANIZATION, get_settings
from ui.main_window import MainWindow
from ui.screens.login import LoginScreen
from api.auth_api import UserInfo, get_auth_api
from api.client import get_api_client


class AgToolsApp(QApplication):
    """
    Main application class for AgTools.

    Handles application-wide settings, login flow, and initialization.
    """

    def __init__(self, argv: list):
        super().__init__(argv)
        self._setup_application()
        self._main_window: MainWindow | None = None
        self._login_window: LoginScreen | None = None
        self._current_user: UserInfo | None = None
        self._settings = get_settings()

    def _setup_application(self) -> None:
        """Configure application-wide settings."""
        self.setApplicationName(APP_NAME)
        self.setOrganizationName(APP_ORGANIZATION)

        # Set default font
        font = QFont("Segoe UI", 11)
        self.setFont(font)

        # High DPI scaling (handled automatically in PyQt6)
        # Just ensure we're using the native style
        self.setStyle("Fusion")

    def start(self) -> int:
        """
        Start the application with login flow.

        Returns:
            Exit code from application execution
        """
        # Check for existing valid token
        saved_token = self._settings.get("auth_token", "")
        if saved_token:
            # Try to validate token
            client = get_api_client()
            client.set_auth_token(saved_token)

            auth_api = get_auth_api()
            user, error = auth_api.get_current_user()

            if user:
                # Token is valid, go straight to main app
                self._current_user = user
                self._show_main_window()
                return self.exec()

        # No valid token, show login
        self._show_login()
        return self.exec()

    def _show_login(self) -> None:
        """Show the login window."""
        self._login_window = LoginScreen()
        self._login_window.login_successful.connect(self._on_login_successful)
        self._login_window.show()

    def _on_login_successful(self, user: UserInfo) -> None:
        """Handle successful login."""
        self._current_user = user

        # Close login window
        if self._login_window:
            self._login_window.close()
            self._login_window = None

        # Show main window
        self._show_main_window()

    def _show_main_window(self) -> None:
        """Show the main application window."""
        self._main_window = MainWindow(current_user=self._current_user)
        self._main_window.show()

        # Connect to handle logout (window close)
        self._main_window.destroyed.connect(self._on_main_window_closed)

    def _on_main_window_closed(self) -> None:
        """Handle main window closed (logout or exit)."""
        # Check if we should show login again
        saved_token = self._settings.get("auth_token", "")
        if not saved_token:
            # Token was cleared (logout), show login again
            self._current_user = None
            self._show_login()

    def create_main_window(self) -> MainWindow:
        """Create and return the main window (for backwards compatibility)."""
        self._main_window = MainWindow(current_user=self._current_user)
        return self._main_window

    def get_main_window(self) -> MainWindow | None:
        """Get the main window instance."""
        return self._main_window

    def get_current_user(self) -> UserInfo | None:
        """Get the current logged in user."""
        return self._current_user


def create_application(argv: list = None) -> AgToolsApp:
    """
    Create the application instance.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Configured AgToolsApp instance
    """
    if argv is None:
        argv = sys.argv
    return AgToolsApp(argv)
