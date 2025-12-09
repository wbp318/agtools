"""
AgTools Application

PyQt6 application setup and initialization.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import APP_NAME, APP_ORGANIZATION, get_settings
from ui.main_window import MainWindow


class AgToolsApp(QApplication):
    """
    Main application class for AgTools.

    Handles application-wide settings and initialization.
    """

    def __init__(self, argv: list):
        super().__init__(argv)
        self._setup_application()
        self._main_window: MainWindow | None = None

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

    def create_main_window(self) -> MainWindow:
        """Create and return the main window."""
        self._main_window = MainWindow()
        return self._main_window

    def get_main_window(self) -> MainWindow | None:
        """Get the main window instance."""
        return self._main_window


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
