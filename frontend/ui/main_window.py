"""
AgTools Main Window

Primary application window with sidebar navigation and content area.
Includes offline mode support with sync manager integration.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QFrame, QStatusBar,
    QSplitter, QSizePolicy, QPushButton, QProgressBar,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from config import APP_NAME, APP_VERSION, get_settings
from ui.styles import COLORS, get_stylesheet
from ui.retro_styles import RETRO_COLORS, get_retro_stylesheet
from ui.sidebar import Sidebar
from ui.screens.dashboard import DashboardScreen
from ui.screens.yield_response import YieldResponseScreen
from ui.screens.spray_timing import SprayTimingScreen
from ui.screens.cost_optimizer import CostOptimizerScreen
from ui.screens.pricing import PricingScreen
from ui.screens.pest_identification import PestIdentificationScreen
from ui.screens.disease_identification import DiseaseIdentificationScreen
from ui.screens.settings import SettingsScreen
from ui.screens.user_management import UserManagementScreen
from ui.screens.crew_management import CrewManagementScreen
from ui.screens.task_management import TaskManagementScreen
from ui.screens.field_management import FieldManagementScreen
from ui.screens.operations_log import OperationsLogScreen
from ui.screens.equipment_management import EquipmentManagementScreen
from ui.screens.inventory_management import InventoryManagementScreen
from ui.screens.maintenance_schedule import MaintenanceScheduleScreen
from ui.screens.reports_dashboard import ReportsDashboardScreen
from ui.screens.accounting_import import AccountingImportScreen
from ui.screens.genfin import GenFinScreen
from ui.screens.livestock_management import LivestockManagementScreen
from ui.screens.seed_planting import SeedPlantingScreen
from core.sync_manager import get_sync_manager, ConnectionState, SyncStatus
from api.auth_api import UserInfo


class SyncStatusWidget(QFrame):
    """Widget showing sync status with sync button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending_count = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Pending sync indicator
        self._pending_label = QLabel("")
        self._pending_label.setStyleSheet(f"""
            color: {COLORS['warning']};
            font-size: 9pt;
            padding: 2px 6px;
            background-color: {COLORS['warning']}20;
            border-radius: 3px;
        """)
        self._pending_label.hide()
        layout.addWidget(self._pending_label)

        # Sync button
        self._sync_btn = QPushButton("\u21BB Sync")  # Refresh symbol
        self._sync_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['text_disabled']};
            }}
        """)
        self._sync_btn.setFixedWidth(70)
        layout.addWidget(self._sync_btn)

    def set_pending_count(self, count: int) -> None:
        """Update the pending sync count display."""
        self._pending_count = count
        if count > 0:
            self._pending_label.setText(f"{count} pending")
            self._pending_label.show()
        else:
            self._pending_label.hide()

    def set_syncing(self, syncing: bool) -> None:
        """Set the syncing state."""
        if syncing:
            self._sync_btn.setText("\u21BB...")
            self._sync_btn.setEnabled(False)
        else:
            self._sync_btn.setText("\u21BB Sync")
            self._sync_btn.setEnabled(True)

    @property
    def sync_button(self) -> QPushButton:
        return self._sync_btn


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

    def set_syncing(self) -> None:
        """Set status to syncing."""
        self._dot.setStyleSheet(f"color: {COLORS['warning']}; font-size: 10pt;")
        self._text.setText("Syncing...")
        self._text.setStyleSheet(f"color: {COLORS['warning']}; font-size: 10pt;")

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


class UserMenuWidget(QFrame):
    """Widget showing current user and logout button."""

    logout_clicked = None  # Will be set externally

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user: UserInfo = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # User icon
        self._user_icon = QLabel("\u263A")  # Smiley face
        self._user_icon.setStyleSheet(f"font-size: 14pt; color: {COLORS['primary']};")
        layout.addWidget(self._user_icon)

        # Username
        self._username_label = QLabel("")
        self._username_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 10pt;")
        layout.addWidget(self._username_label)

        # Role badge
        self._role_label = QLabel("")
        self._role_label.setStyleSheet(f"""
            color: white;
            font-size: 8pt;
            padding: 2px 6px;
            border-radius: 3px;
            background-color: {COLORS['primary']};
        """)
        layout.addWidget(self._role_label)

        # Logout button
        self._logout_btn = QPushButton("Logout")
        self._logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']}20;
                color: {COLORS['error']};
                border-color: {COLORS['error']};
            }}
        """)
        layout.addWidget(self._logout_btn)

    def set_user(self, user: UserInfo) -> None:
        """Set the current user."""
        self._user = user
        if user:
            self._username_label.setText(user.full_name)
            self._role_label.setText(user.role.upper())

            # Color code by role
            role_colors = {
                "admin": COLORS['error'],
                "manager": "#1976d2",
                "crew": COLORS['primary']
            }
            color = role_colors.get(user.role, COLORS['primary'])
            self._role_label.setStyleSheet(f"""
                color: white;
                font-size: 8pt;
                padding: 2px 6px;
                border-radius: 3px;
                background-color: {color};
            """)

    @property
    def logout_button(self) -> QPushButton:
        return self._logout_btn


class MainWindow(QMainWindow):
    """
    Main application window.

    Contains sidebar navigation, stacked content area, and sync management.
    Integrates with SyncManager for offline mode support.
    """

    def __init__(self, current_user: UserInfo = None):
        super().__init__()
        self._settings = get_settings()
        self._is_online = False
        self._screens: dict[str, QWidget] = {}
        self._sync_manager = get_sync_manager()
        self._current_user = current_user

        self._setup_window()
        self._setup_ui()
        self._setup_connections()
        self._setup_sync_manager()

        # Start connection monitoring
        QTimer.singleShot(500, self._start_monitoring)

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

        # Apply Windows 98 retro stylesheet
        self.setStyleSheet(get_retro_stylesheet())

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

        # Content area - warm cream background like old monitors
        content_frame = QFrame()
        content_frame.setStyleSheet(f"background-color: {RETRO_COLORS['cream']};")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top bar - Windows 98 style with 3D bevel
        top_bar = QFrame()
        top_bar.setStyleSheet(f"""
            background-color: {RETRO_COLORS['window_face']};
            border-bottom: 2px solid;
            border-bottom-color: {RETRO_COLORS['bevel_dark']};
        """)
        top_bar.setFixedHeight(36)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        # Page title (dynamic) - Windows 98 style
        self._page_title = QLabel("Dashboard")
        title_font = QFont("Tahoma", 11)
        title_font.setWeight(QFont.Weight.Bold)
        self._page_title.setFont(title_font)
        self._page_title.setStyleSheet(f"color: {RETRO_COLORS['text_black']}; background: transparent;")
        top_layout.addWidget(self._page_title)

        top_layout.addStretch()

        # Sync status widget
        self._sync_status = SyncStatusWidget()
        self._sync_status.sync_button.clicked.connect(self._on_sync_clicked)
        top_layout.addWidget(self._sync_status)

        # Status indicator
        self._status_indicator = StatusIndicator()
        top_layout.addWidget(self._status_indicator)

        # User menu
        self._user_menu = UserMenuWidget()
        if self._current_user:
            self._user_menu.set_user(self._current_user)
        self._user_menu.logout_button.clicked.connect(self._on_logout_clicked)
        top_layout.addWidget(self._user_menu)

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

        # Yield Response Calculator (Phase 3)
        yield_screen = YieldResponseScreen()
        self._add_screen("yield", yield_screen)

        # Spray Timing Screen (Phase 4)
        spray_timing_screen = SprayTimingScreen()
        self._add_screen("timing", spray_timing_screen)

        # Cost Optimizer Screen (Phase 5)
        cost_optimizer_screen = CostOptimizerScreen()
        self._add_screen("costs", cost_optimizer_screen)

        # Pricing Screen (Phase 6)
        pricing_screen = PricingScreen()
        self._add_screen("pricing", pricing_screen)

        # Pest Identification Screen (Phase 7)
        pest_screen = PestIdentificationScreen()
        self._add_screen("pests", pest_screen)

        # Disease Identification Screen (Phase 7)
        disease_screen = DiseaseIdentificationScreen()
        self._add_screen("diseases", disease_screen)

        # Settings Screen (Phase 9)
        settings_screen = SettingsScreen()
        self._add_screen("settings", settings_screen)

        # Task Management Screen (Phase 2.5) - All users
        task_mgmt_screen = TaskManagementScreen(current_user=self._current_user)
        self._add_screen("tasks", task_mgmt_screen)

        # Field Management Screen (Phase 3) - All users
        field_mgmt_screen = FieldManagementScreen(current_user=self._current_user)
        self._add_screen("fields", field_mgmt_screen)

        # Operations Log Screen (Phase 3) - All users
        ops_log_screen = OperationsLogScreen(current_user=self._current_user)
        self._add_screen("operations", ops_log_screen)

        # Equipment Management Screen (Phase 4) - All users
        equipment_screen = EquipmentManagementScreen(current_user=self._current_user)
        self._add_screen("equipment", equipment_screen)

        # Inventory Management Screen (Phase 4) - All users
        inventory_screen = InventoryManagementScreen(current_user=self._current_user)
        self._add_screen("inventory", inventory_screen)

        # Maintenance Schedule Screen (Phase 4) - All users
        maintenance_screen = MaintenanceScheduleScreen(current_user=self._current_user)
        self._add_screen("maintenance", maintenance_screen)

        # Reports Dashboard Screen (Phase 5) - All users
        reports_screen = ReportsDashboardScreen(current_user=self._current_user)
        self._add_screen("reports", reports_screen)

        # Accounting Import Screen (v2.9) - All users
        accounting_import_screen = AccountingImportScreen(current_user=self._current_user)
        self._add_screen("accounting_import", accounting_import_screen)

        # GenFin Accounting Screen (v6.3) - All users
        genfin_screen = GenFinScreen()
        self._add_screen("genfin", genfin_screen)

        # Livestock Management Screen (v6.4.0) - All users
        livestock_screen = LivestockManagementScreen(current_user=self._current_user)
        self._add_screen("livestock", livestock_screen)

        # Seed & Planting Screen (v6.4.0) - All users
        seed_planting_screen = SeedPlantingScreen(current_user=self._current_user)
        self._add_screen("seeds", seed_planting_screen)

        # Admin Screens (only show for admin/manager)
        if self._current_user and self._current_user.role in ["admin", "manager"]:
            # User Management (admin only)
            if self._current_user.role == "admin":
                user_mgmt_screen = UserManagementScreen()
                self._add_screen("users", user_mgmt_screen)

            # Crew Management
            crew_mgmt_screen = CrewManagementScreen()
            self._add_screen("crews", crew_mgmt_screen)

        # Placeholder screens for other features
        placeholders = [
            ("spray", "Spray Recommendations"),
        ]

        for nav_id, title in placeholders:
            screen = PlaceholderScreen(title)
            self._add_screen(nav_id, screen)

    def _add_screen(self, nav_id: str, screen: QWidget) -> None:
        """Add a screen to the stack."""
        self._screens[nav_id] = screen
        self._stack.addWidget(screen)

    def _setup_status_bar(self) -> None:
        """Setup the status bar - Windows 98 style."""
        status_bar = QStatusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {RETRO_COLORS['window_face']};
                border-top: 1px solid {RETRO_COLORS['bevel_light']};
            }}
            QStatusBar::item {{
                border: none;
            }}
        """)
        self.setStatusBar(status_bar)

        # Ready message
        status_bar.showMessage("Ready")

        # Last sync time - sunken panel look
        self._last_sync_label = QLabel("Last sync: Never")
        self._last_sync_label.setStyleSheet(f"""
            color: {RETRO_COLORS['text_black']};
            background: {RETRO_COLORS['cream']};
            border: 1px solid {RETRO_COLORS['bevel_dark']};
            padding: 2px 8px;
            font-size: 10px;
        """)
        status_bar.addPermanentWidget(self._last_sync_label)

        # Version info - sunken panel
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet(f"""
            color: {RETRO_COLORS['text_black']};
            background: {RETRO_COLORS['cream']};
            border: 1px solid {RETRO_COLORS['bevel_dark']};
            padding: 2px 8px;
            font-weight: bold;
        """)
        status_bar.addPermanentWidget(version_label)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        self._sidebar.navigation_clicked.connect(self._navigate_to)

    def _setup_sync_manager(self) -> None:
        """Setup sync manager signal connections."""
        self._sync_manager.connection_changed.connect(self._on_connection_changed)
        self._sync_manager.sync_started.connect(self._on_sync_started)
        self._sync_manager.sync_completed.connect(self._on_sync_completed)
        self._sync_manager.sync_progress.connect(self._on_sync_progress)

    def _start_monitoring(self) -> None:
        """Start the sync manager's connection monitoring."""
        self._sync_manager.start_monitoring()
        self._update_pending_count()

        # Setup periodic pending count update
        self._pending_timer = QTimer()
        self._pending_timer.timeout.connect(self._update_pending_count)
        self._pending_timer.start(10000)  # Every 10 seconds

    def _navigate_to(self, nav_id: str) -> None:
        """Navigate to a screen by ID."""
        if nav_id in self._screens:
            self._stack.setCurrentWidget(self._screens[nav_id])
            self._sidebar.set_active_nav(nav_id)

            # Update page title
            titles = {
                "dashboard": "Dashboard",
                "fields": "Field Management",
                "operations": "Operations Log",
                "tasks": "Task Management",
                "equipment": "Equipment Management",
                "inventory": "Inventory Management",
                "maintenance": "Maintenance Schedule",
                "reports": "Reports & Analytics",
                "quickbooks": "QuickBooks Import",
                "genfin": "GenFin Accounting",
                "livestock": "Livestock Management",
                "seeds": "Seed & Planting",
                "pests": "Pest Identification",
                "diseases": "Disease Identification",
                "spray": "Spray Recommendations",
                "timing": "Spray Timing",
                "costs": "Cost Optimizer",
                "pricing": "Price Manager",
                "yield": "Yield Response Calculator",
                "settings": "Settings",
                "users": "User Management",
                "crews": "Crew Management",
            }
            self._page_title.setText(titles.get(nav_id, nav_id.title()))

    @pyqtSlot(ConnectionState)
    def _on_connection_changed(self, state: ConnectionState) -> None:
        """Handle connection state changes from sync manager."""
        self._is_online = state == ConnectionState.ONLINE

        if state == ConnectionState.ONLINE:
            self._status_indicator.set_online()
            self.statusBar().showMessage("Connected to API")
        elif state == ConnectionState.OFFLINE:
            self._status_indicator.set_offline()
            self.statusBar().showMessage("Offline mode - using cached data")
        elif state == ConnectionState.SYNCING:
            self._status_indicator.set_syncing()
            self.statusBar().showMessage("Syncing data...")
        else:
            self._status_indicator.set_error()
            self.statusBar().showMessage("Connection error")

        # Update dashboard
        if "dashboard" in self._screens:
            dashboard = self._screens["dashboard"]
            if hasattr(dashboard, "set_connection_status"):
                dashboard.set_connection_status(self._is_online)

    @pyqtSlot()
    def _on_sync_started(self) -> None:
        """Handle sync started event."""
        self._sync_status.set_syncing(True)
        self._status_indicator.set_syncing()
        self.statusBar().showMessage("Syncing data with server...")

    @pyqtSlot(object)
    def _on_sync_completed(self, result) -> None:
        """Handle sync completed event."""
        self._sync_status.set_syncing(False)
        self._update_pending_count()

        # Update last sync time
        if result.status in [SyncStatus.SUCCESS, SyncStatus.PARTIAL]:
            from datetime import datetime
            self._last_sync_label.setText(f"Last sync: {datetime.now().strftime('%H:%M')}")

            if result.status == SyncStatus.SUCCESS:
                self.statusBar().showMessage(f"Sync complete: {result.synced_items} items synced")
            else:
                self.statusBar().showMessage(
                    f"Sync partial: {result.synced_items} synced, {result.failed_items} failed"
                )
        else:
            self.statusBar().showMessage("Sync failed - will retry later")

        # Restore connection indicator
        if self._sync_manager.is_online:
            self._status_indicator.set_online()
        else:
            self._status_indicator.set_offline()

    @pyqtSlot(int, int)
    def _on_sync_progress(self, current: int, total: int) -> None:
        """Handle sync progress updates."""
        self.statusBar().showMessage(f"Syncing... ({current}/{total})")

    def _on_sync_clicked(self) -> None:
        """Handle sync button click."""
        if not self._sync_manager.is_online:
            QMessageBox.warning(
                self,
                "Offline",
                "Cannot sync while offline. Data will be synced when connection is restored."
            )
            return

        # Start sync in background
        import threading
        threading.Thread(target=self._sync_manager.sync_all, daemon=True).start()

    def _update_pending_count(self) -> None:
        """Update the pending sync count display."""
        count = self._sync_manager.pending_sync_count
        self._sync_status.set_pending_count(count)

    def is_online(self) -> bool:
        """Check if currently online."""
        return self._is_online

    def _on_logout_clicked(self) -> None:
        """Handle logout button click."""
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Clear auth token
            from api.auth_api import get_auth_api
            from api.client import get_api_client

            auth_api = get_auth_api()
            auth_api.logout()

            # Clear settings
            self._settings.set("auth_token", "")
            self._settings.set("refresh_token", "")
            self._settings.save()

            # Close this window - app.py will show login again
            self.close()

    def set_current_user(self, user: UserInfo) -> None:
        """Set the current logged in user."""
        self._current_user = user
        if hasattr(self, '_user_menu'):
            self._user_menu.set_user(user)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Stop sync manager monitoring
        self._sync_manager.stop_monitoring()

        # Stop pending timer
        if hasattr(self, '_pending_timer'):
            self._pending_timer.stop()

        super().closeEvent(event)
