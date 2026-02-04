"""
AgTools Settings Screen

User preferences, application configuration, and data management.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QComboBox, QSpinBox, QLineEdit,
    QGroupBox, QFormLayout, QMessageBox, QCheckBox,
    QTabWidget, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS
from config import get_settings, reset_settings, APP_VERSION, USER_DATA_DIR
from database.local_db import get_local_db, DB_PATH


class SettingsGroup(QGroupBox):
    """Styled group box for settings sections."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: 600;
                font-size: 12pt;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {COLORS['primary']};
            }}
        """)


class GeneralSettingsTab(QWidget):
    """General application settings."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Region Settings
        region_group = SettingsGroup("Region & Defaults")
        region_layout = QFormLayout(region_group)
        region_layout.setSpacing(12)

        self._region_combo = QComboBox()
        self._region_combo.addItems([
            "Midwest Corn Belt",
            "Northern Plains",
            "Southern Plains",
            "Delta",
            "Southeast",
            "Pacific Northwest",
            "California"
        ])
        self._region_combo.currentIndexChanged.connect(self._on_change)
        region_layout.addRow("Region:", self._region_combo)

        self._default_crop_combo = QComboBox()
        self._default_crop_combo.addItems(["Corn", "Soybean", "Wheat"])
        self._default_crop_combo.currentIndexChanged.connect(self._on_change)
        region_layout.addRow("Default Crop:", self._default_crop_combo)

        layout.addWidget(region_group)

        # UI Settings
        ui_group = SettingsGroup("User Interface")
        ui_layout = QFormLayout(ui_group)
        ui_layout.setSpacing(12)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Light", "Dark (Coming Soon)"])
        self._theme_combo.currentIndexChanged.connect(self._on_change)
        ui_layout.addRow("Theme:", self._theme_combo)

        self._sidebar_width_spin = QSpinBox()
        self._sidebar_width_spin.setRange(150, 300)
        self._sidebar_width_spin.setSuffix(" px")
        self._sidebar_width_spin.valueChanged.connect(self._on_change)
        ui_layout.addRow("Sidebar Width:", self._sidebar_width_spin)

        layout.addWidget(ui_group)

        # Offline Settings
        offline_group = SettingsGroup("Offline Mode")
        offline_layout = QFormLayout(offline_group)
        offline_layout.setSpacing(12)

        self._offline_enabled = QCheckBox("Enable offline mode")
        self._offline_enabled.stateChanged.connect(self._on_change)
        offline_layout.addRow(self._offline_enabled)

        self._cache_ttl_spin = QSpinBox()
        self._cache_ttl_spin.setRange(1, 168)  # 1 hour to 1 week
        self._cache_ttl_spin.setSuffix(" hours")
        self._cache_ttl_spin.valueChanged.connect(self._on_change)
        offline_layout.addRow("Cache TTL:", self._cache_ttl_spin)

        self._sync_on_startup = QCheckBox("Sync data on startup")
        self._sync_on_startup.stateChanged.connect(self._on_change)
        offline_layout.addRow(self._sync_on_startup)

        self._auto_fallback = QCheckBox("Auto-switch to offline if server unavailable")
        self._auto_fallback.stateChanged.connect(self._on_change)
        offline_layout.addRow(self._auto_fallback)

        layout.addWidget(offline_group)

        layout.addStretch()

    def _load_settings(self) -> None:
        """Load current settings into UI."""
        # Region
        region_map = {
            "midwest_corn_belt": 0, "northern_plains": 1, "southern_plains": 2,
            "delta": 3, "southeast": 4, "pacific_northwest": 5, "california": 6
        }
        self._region_combo.setCurrentIndex(region_map.get(self._settings.region, 0))

        # Default crop
        crop_map = {"corn": 0, "soybean": 1, "wheat": 2}
        self._default_crop_combo.setCurrentIndex(crop_map.get(self._settings.default_crop, 0))

        # UI
        self._theme_combo.setCurrentIndex(0 if self._settings.ui.theme == "light" else 1)
        self._sidebar_width_spin.setValue(self._settings.ui.sidebar_width)

        # Offline
        self._offline_enabled.setChecked(self._settings.offline.enabled)
        self._cache_ttl_spin.setValue(self._settings.offline.cache_ttl_hours)
        self._sync_on_startup.setChecked(self._settings.offline.sync_on_startup)
        self._auto_fallback.setChecked(self._settings.offline.auto_fallback)

    def _on_change(self) -> None:
        self.settings_changed.emit()

    def save_settings(self) -> None:
        """Save settings from UI to config."""
        region_values = [
            "midwest_corn_belt", "northern_plains", "southern_plains",
            "delta", "southeast", "pacific_northwest", "california"
        ]
        self._settings.region = region_values[self._region_combo.currentIndex()]

        crop_values = ["corn", "soybean", "wheat"]
        self._settings.default_crop = crop_values[self._default_crop_combo.currentIndex()]

        self._settings.ui.theme = "light" if self._theme_combo.currentIndex() == 0 else "dark"
        self._settings.ui.sidebar_width = self._sidebar_width_spin.value()

        self._settings.offline.enabled = self._offline_enabled.isChecked()
        self._settings.offline.cache_ttl_hours = self._cache_ttl_spin.value()
        self._settings.offline.sync_on_startup = self._sync_on_startup.isChecked()
        self._settings.offline.auto_fallback = self._auto_fallback.isChecked()

        self._settings.save()


class ConnectionSettingsTab(QWidget):
    """API connection settings."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # API Settings
        api_group = SettingsGroup("API Server")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(12)

        self._base_url_edit = QLineEdit()
        self._base_url_edit.setPlaceholderText("https://api.yourfarm.com or http://localhost:8000")
        self._base_url_edit.textChanged.connect(self._on_change)
        api_layout.addRow("Server URL:", self._base_url_edit)

        # SSL verification checkbox
        self._verify_ssl_check = QCheckBox("Verify SSL certificates (recommended for production)")
        self._verify_ssl_check.setChecked(True)
        self._verify_ssl_check.stateChanged.connect(self._on_change)
        api_layout.addRow("Security:", self._verify_ssl_check)

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(5, 120)
        self._timeout_spin.setSuffix(" seconds")
        self._timeout_spin.valueChanged.connect(self._on_change)
        api_layout.addRow("Timeout:", self._timeout_spin)

        # Test connection button
        test_layout = QHBoxLayout()
        self._test_btn = QPushButton("Test Connection")
        self._test_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self._test_btn)

        self._test_result = QLabel("")
        test_layout.addWidget(self._test_result)
        test_layout.addStretch()

        api_layout.addRow(test_layout)

        layout.addWidget(api_group)

        # Connection Status
        status_group = SettingsGroup("Connection Status")
        status_layout = QVBoxLayout(status_group)

        self._status_text = QTextEdit()
        self._status_text.setReadOnly(True)
        self._status_text.setMaximumHeight(150)
        self._status_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['surface_variant']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
            }}
        """)
        status_layout.addWidget(self._status_text)

        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self._refresh_status)
        status_layout.addWidget(refresh_btn)

        layout.addWidget(status_group)

        layout.addStretch()

    def _load_settings(self) -> None:
        self._base_url_edit.setText(self._settings.api.base_url)
        self._verify_ssl_check.setChecked(self._settings.api.verify_ssl)
        self._timeout_spin.setValue(int(self._settings.api.timeout_seconds))
        self._refresh_status()

    def _on_change(self) -> None:
        self.settings_changed.emit()

    def _test_connection(self) -> None:
        """Test API connection."""
        import httpx

        url = self._base_url_edit.text()
        self._test_result.setText("Testing...")
        self._test_result.setStyleSheet(f"color: {COLORS['text_secondary']};")

        try:
            response = httpx.get(f"{url}/", timeout=5.0)
            if response.status_code == 200:
                self._test_result.setText("Connected!")
                self._test_result.setStyleSheet(f"color: {COLORS['success']};")
            else:
                self._test_result.setText(f"Error: {response.status_code}")
                self._test_result.setStyleSheet(f"color: {COLORS['error']};")
        except Exception:
            self._test_result.setText("Failed")
            self._test_result.setStyleSheet(f"color: {COLORS['error']};")

    def _refresh_status(self) -> None:
        """Refresh connection status display."""
        import httpx
        from datetime import datetime, timezone

        lines = [f"Status check at {datetime.now(timezone.utc).strftime('%H:%M:%S')}"]
        lines.append("-" * 40)

        url = self._settings.api.base_url
        try:
            response = httpx.get(f"{url}/", timeout=5.0)
            lines.append(f"Server: {url}")
            lines.append(f"Status: Connected (HTTP {response.status_code})")

            # Try to get version info
            data = response.json()
            if isinstance(data, dict):
                lines.append(f"API Version: {data.get('version', 'Unknown')}")

        except httpx.ConnectError:
            lines.append(f"Server: {url}")
            lines.append("Status: OFFLINE - Cannot connect")
        except Exception as e:
            lines.append(f"Status: Error - {str(e)[:50]}")

        self._status_text.setText("\n".join(lines))

    def save_settings(self) -> None:
        """Save settings from UI to config."""
        self._settings.api.base_url = self._base_url_edit.text()
        self._settings.api.verify_ssl = self._verify_ssl_check.isChecked()
        self._settings.api.timeout_seconds = float(self._timeout_spin.value())
        self._settings.save()


class DataManagementTab(QWidget):
    """Data cache and export management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = get_local_db()
        self._setup_ui()
        self._refresh_stats()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Cache Statistics
        cache_group = SettingsGroup("Local Cache Statistics")
        cache_layout = QVBoxLayout(cache_group)

        self._stats_grid = QGridLayout()
        self._stats_grid.setSpacing(8)

        self._stat_labels = {}
        stats = [
            ("cache", "Cache Entries"),
            ("products", "Products"),
            ("pests", "Pests"),
            ("diseases", "Diseases"),
            ("calculation_history", "Calculations"),
            ("sync_queue", "Pending Sync"),
            ("file_size_mb", "Database Size"),
        ]

        for i, (key, label) in enumerate(stats):
            row = i // 2
            col = (i % 2) * 2

            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self._stats_grid.addWidget(label_widget, row, col)

            value_widget = QLabel("--")
            value_widget.setStyleSheet("font-weight: 600;")
            self._stats_grid.addWidget(value_widget, row, col + 1)
            self._stat_labels[key] = value_widget

        cache_layout.addLayout(self._stats_grid)

        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self._refresh_stats)
        cache_layout.addWidget(refresh_btn)

        layout.addWidget(cache_group)

        # Cache Management
        manage_group = SettingsGroup("Cache Management")
        manage_layout = QVBoxLayout(manage_group)

        btn_layout = QHBoxLayout()

        clear_expired_btn = QPushButton("Clear Expired Cache")
        clear_expired_btn.clicked.connect(self._clear_expired)
        btn_layout.addWidget(clear_expired_btn)

        clear_all_btn = QPushButton("Clear All Cache")
        clear_all_btn.setStyleSheet(f"background-color: {COLORS['warning']};")
        clear_all_btn.clicked.connect(self._clear_all_cache)
        btn_layout.addWidget(clear_all_btn)

        optimize_btn = QPushButton("Optimize Database")
        optimize_btn.clicked.connect(self._optimize_db)
        btn_layout.addWidget(optimize_btn)

        manage_layout.addLayout(btn_layout)

        layout.addWidget(manage_group)

        # Data Export
        export_group = SettingsGroup("Data Export")
        export_layout = QVBoxLayout(export_group)

        export_info = QLabel("Export your calculation history and cached data for backup or analysis.")
        export_info.setWordWrap(True)
        export_info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        export_layout.addWidget(export_info)

        export_btn_layout = QHBoxLayout()

        export_history_btn = QPushButton("Export Calculation History (CSV)")
        export_history_btn.clicked.connect(self._export_history)
        export_btn_layout.addWidget(export_history_btn)

        export_prices_btn = QPushButton("Export Prices (CSV)")
        export_prices_btn.clicked.connect(self._export_prices)
        export_btn_layout.addWidget(export_prices_btn)

        export_layout.addLayout(export_btn_layout)

        layout.addWidget(export_group)

        layout.addStretch()

    def _refresh_stats(self) -> None:
        """Refresh cache statistics."""
        stats = self._db.get_stats()

        for key, label in self._stat_labels.items():
            value = stats.get(key, 0)
            if key == "file_size_mb":
                label.setText(f"{value} MB")
            else:
                label.setText(str(value))

    def _clear_expired(self) -> None:
        """Clear expired cache entries."""
        count = self._db.cache_clear_expired()
        QMessageBox.information(
            self, "Cache Cleared",
            f"Removed {count} expired cache entries."
        )
        self._refresh_stats()

    def _clear_all_cache(self) -> None:
        """Clear all cached data."""
        reply = QMessageBox.question(
            self, "Clear All Cache",
            "Are you sure you want to clear all cached data?\n\n"
            "This will not affect your pending sync items.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._db.cache_delete("prices")
            self._db.cache_delete("pests")
            self._db.cache_delete("diseases")
            self._db.cache_delete("yield_response")
            self._db.cache_delete("spray_timing")
            QMessageBox.information(self, "Done", "Cache cleared successfully.")
            self._refresh_stats()

    def _optimize_db(self) -> None:
        """Optimize database file."""
        self._db.vacuum()
        QMessageBox.information(self, "Done", "Database optimized.")
        self._refresh_stats()

    def _export_history(self) -> None:
        """Export calculation history to CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Calculation History",
            "calculation_history.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            calculations = self._db.get_calculations(limit=1000)

            if not calculations:
                QMessageBox.information(self, "No Data", "No calculation history to export.")
                return

            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Type', 'Date', 'Inputs', 'Results'])

                for calc in calculations:
                    writer.writerow([
                        calc['id'],
                        calc['calculation_type'],
                        calc['created_at'],
                        str(calc['inputs']),
                        str(calc['results'])
                    ])

            QMessageBox.information(self, "Exported", f"Exported {len(calculations)} calculations to:\n{file_path}")

    def _export_prices(self) -> None:
        """Export product prices to CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Prices",
            "product_prices.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            products = self._db.get_products()

            if not products:
                QMessageBox.information(self, "No Data", "No product data to export.")
                return

            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Category', 'Unit', 'Base Price', 'Current Price', 'Source'])

                for product in products:
                    writer.writerow([
                        product.get('id'),
                        product.get('name'),
                        product.get('category'),
                        product.get('unit'),
                        product.get('base_price'),
                        product.get('current_price'),
                        product.get('price_source')
                    ])

            QMessageBox.information(self, "Exported", f"Exported {len(products)} products to:\n{file_path}")


class AboutTab(QWidget):
    """About and version information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(24)

        # Logo/Title area
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary']};
                border-radius: 8px;
                padding: 24px;
            }}
        """)
        title_layout = QVBoxLayout(title_frame)

        app_name = QLabel("AgTools Professional")
        app_name.setStyleSheet("color: white; font-size: 24pt; font-weight: bold;")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(app_name)

        version = QLabel(f"Version {APP_VERSION}")
        version.setStyleSheet("color: white; font-size: 14pt;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(version)

        tagline = QLabel("Professional Crop Consulting System")
        tagline.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11pt;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(tagline)

        layout.addWidget(title_frame)

        # Info
        info_group = SettingsGroup("Application Information")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        info_layout.addRow("Organization:", QLabel("New Generation Farms"))
        info_layout.addRow("Data Directory:", QLabel(str(USER_DATA_DIR)))
        info_layout.addRow("Database:", QLabel(str(DB_PATH)))

        layout.addWidget(info_group)

        # Features
        features_group = SettingsGroup("Features")
        features_layout = QVBoxLayout(features_group)

        features = [
            "Yield Response & Economic Optimum Rate Calculator",
            "Weather-Smart Spray Timing Optimizer",
            "Input Cost Optimization Suite",
            "Real-Time Price Management",
            "AI-Powered Pest & Disease Identification",
            "Offline Mode with Local Database",
            "Background Data Synchronization",
        ]

        for feature in features:
            feat_label = QLabel(f"  {feature}")
            feat_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            features_layout.addWidget(feat_label)

        layout.addWidget(features_group)

        layout.addStretch()


class SettingsScreen(QWidget):
    """
    Settings screen with tabbed interface for all configuration options.

    Tabs:
    - General: Region, defaults, UI preferences
    - Connection: API server settings
    - Data: Cache management and export
    - About: Version and app info
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Settings")
        header_font = QFont()
        header_font.setPointSize(20)
        header_font.setWeight(QFont.Weight.Bold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                background-color: {COLORS['surface']};
            }}
            QTabBar::tab {{
                padding: 8px 16px;
                margin-right: 4px;
                background-color: {COLORS['surface_variant']};
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['surface']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['primary_light']};
                color: white;
            }}
        """)

        # Create tabs
        self._general_tab = GeneralSettingsTab()
        self._connection_tab = ConnectionSettingsTab()
        self._data_tab = DataManagementTab()
        self._about_tab = AboutTab()

        self._tabs.addTab(self._general_tab, "General")
        self._tabs.addTab(self._connection_tab, "Connection")
        self._tabs.addTab(self._data_tab, "Data")
        self._tabs.addTab(self._about_tab, "About")

        layout.addWidget(self._tabs, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_settings)
        btn_layout.addWidget(reset_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                padding: 8px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        pass

    def _save_settings(self) -> None:
        """Save all settings."""
        self._general_tab.save_settings()
        self._connection_tab.save_settings()

        QMessageBox.information(
            self, "Settings Saved",
            "Your settings have been saved.\n\n"
            "Some changes may require restarting the application."
        )

    def _reset_settings(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            reset_settings()
            self._general_tab._load_settings()
            self._connection_tab._load_settings()
            QMessageBox.information(self, "Reset", "Settings have been reset to defaults.")
