"""
AgTools Main Window

Primary application window with sidebar navigation and content area.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QFrame, QStatusBar,
    QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ..config import APP_NAME, APP_VERSION, get_settings
from .styles import COLORS, get_stylesheet
from .sidebar import Sidebar
from .screens.dashboard import DashboardScreen


class StatusIndicator(QFrame):
    """Status indicator showing connection state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # Status dot
        self._dot = QLabel("\u25CF")  # Filled circle
        self._dot.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 10pt;")
        layout.addWidget(self._dot)

        # Status text
        self._text = QLabel("Checking...")
        self._text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        layout.addWidget(self._text)

    def set_online(self) -> None:
        """Set status to online."""
        self._dot.setStyleSheet(f"color: {COLORS['online']}; font-size: 10pt;")
        self._text.setText("Online")
        self._text.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 10pt;")

    def set_offline(self) -> None:
        """Set status to offline."""
        self._dot.setStyleSheet(f"color: {COLORS['offline']}; font-size: 10pt;")
        self._text.setText("Offline")
        self._text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")

    def set_error(self, message: str = "Error") -> None:
        """Set status to error."""
        self._dot.setStyleSheet(f"color: {COLORS['error_status']}; font-size: 10pt;")
        self._text.setText(message)
        self._text.setStyleSheet(f"color: {COLORS['error']}; font-size: 10pt;")


class PlaceholderScreen(QWidget):
    """Placeholder screen for features not yet implemented."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("\u2699")  # Gear icon
        icon.setStyleSheet(f"font-size: 48pt; color: {COLORS['text_disabled']};")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        coming_soon = QLabel("Coming Soon")
        coming_soon.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14pt;")
        coming_soon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(coming_soon)


class MainWindow(QMainWindow):
    """
    Main application window.

    Contains sidebar navigation and stacked content area.
    """

    def __init__(self):
        super().__init__()
        self._settings = get_settings()
        self._is_online = False
        self._screens: dict[str, QWidget] = {}

        self._setup_window()
        self._setup_ui()
        self._setup_connections()

        # Check API connection on startup
        QTimer.singleShot(500, self._check_connection)

    def _setup_window(self) -> None:
        """Configure window properties."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(
            self._settings.ui.min_width,
            self._settings.ui.min_height
        )
        self.resize(
            self._settings.ui.default_width,
            self._settings.ui.default_height
        )

        # Apply stylesheet
        self.setStyleSheet(get_stylesheet(self._settings.ui.theme))

    def _setup_ui(self) -> None:
        """Initialize the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main horizontal layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # Content area with splitter for responsiveness
        content_frame = QFrame()
        content_frame.setStyleSheet(f"background-color: {COLORS['background']};")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar with status
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            background-color: {COLORS['surface']};
            border-bottom: 1px solid {COLORS['border']};
        """)
        top_bar.setFixedHeight(48)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        # Page title (dynamic)
        self._page_title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Weight.DemiBold)
        self._page_title.setFont(title_font)
        top_layout.addWidget(self._page_title)

        top_layout.addStretch()

        # Status indicator
        self._status_indicator = StatusIndicator()
        top_layout.addWidget(self._status_indicator)

        content_layout.addWidget(top_bar)

        # Stacked widget for screens
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        content_layout.addWidget(self._stack)

        main_layout.addWidget(content_frame, 1)

        # Add screens
        self._add_screens()

        # Status bar
        self._setup_status_bar()

        # Set initial screen
        self._sidebar.set_active_nav("dashboard")

    def _add_screens(self) -> None:
        """Add all screens to the stack."""
        # Dashboard
        dashboard = DashboardScreen()
        dashboard.navigate_to.connect(self._navigate_to)
        self._add_screen("dashboard", dashboard)

        # Placeholder screens for other features
        placeholders = [
            ("pests", "Pest Identification"),
            ("diseases", "Disease Identification"),
            ("spray", "Spray Recommendations"),
            ("timing", "Spray Timing"),
            ("costs", "Cost Optimizer"),
            ("pricing", "Price Manager"),
            ("yield", "Yield Response Calculator"),
            ("settings", "Settings"),
        ]

        for nav_id, title in placeholders:
            screen = PlaceholderScreen(title)
            self._add_screen(nav_id, screen)

    def _add_screen(self, nav_id: str, screen: QWidget) -> None:
        """Add a screen to the stack."""
        self._screens[nav_id] = screen
        self._stack.addWidget(screen)

    def _setup_status_bar(self) -> None:
        """Setup the status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        # Ready message
        status_bar.showMessage("Ready")

        # Version info on right
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        status_bar.addPermanentWidget(version_label)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        self._sidebar.navigation_clicked.connect(self._navigate_to)

    def _navigate_to(self, nav_id: str) -> None:
        """Navigate to a screen by ID."""
        if nav_id in self._screens:
            self._stack.setCurrentWidget(self._screens[nav_id])
            self._sidebar.set_active_nav(nav_id)

            # Update page title
            titles = {
                "dashboard": "Dashboard",
                "pests": "Pest Identification",
                "diseases": "Disease Identification",
                "spray": "Spray Recommendations",
                "timing": "Spray Timing",
                "costs": "Cost Optimizer",
                "pricing": "Price Manager",
                "yield": "Yield Response Calculator",
                "settings": "Settings",
            }
            self._page_title.setText(titles.get(nav_id, nav_id.title()))

    def _check_connection(self) -> None:
        """Check API connection status."""
        # For now, just simulate - actual API check will be added later
        import httpx

        try:
            settings = get_settings()
            response = httpx.get(
                f"{settings.api.base_url}/",
                timeout=5.0
            )
            if response.status_code == 200:
                self._set_online(True)
            else:
                self._set_online(False)
        except Exception:
            self._set_online(False)

    def _set_online(self, online: bool) -> None:
        """Update online/offline status."""
        self._is_online = online

        if online:
            self._status_indicator.set_online()
            self.statusBar().showMessage("Connected to API")
        else:
            self._status_indicator.set_offline()
            self.statusBar().showMessage("Offline mode - using cached data")

        # Update dashboard
        if "dashboard" in self._screens:
            dashboard = self._screens["dashboard"]
            if hasattr(dashboard, "set_connection_status"):
                dashboard.set_connection_status(online)

    def is_online(self) -> bool:
        """Check if currently online."""
        return self._is_online
