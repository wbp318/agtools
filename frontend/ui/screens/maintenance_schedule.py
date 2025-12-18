"""
Maintenance Schedule Screen

Screen for viewing equipment maintenance schedule, alerts, and history.
AgTools v2.5.0 Phase 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QGroupBox, QTabWidget, QScrollArea,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.equipment_api import (
    get_equipment_api, EquipmentAPI, EquipmentInfo,
    MaintenanceInfo, MaintenanceAlert
)
from api.auth_api import UserInfo


# Urgency colors
URGENCY_COLORS = {
    "overdue": "#d32f2f",      # Red
    "due_soon": "#ff9800",     # Orange
    "upcoming": "#2196f3",     # Blue
}

# Maintenance type colors
MAINTENANCE_COLORS = {
    "oil_change": "#ff9800",
    "filter": "#4caf50",
    "repairs": "#f44336",
    "inspection": "#2196f3",
    "tires": "#795548",
    "brakes": "#e91e63",
    "hydraulics": "#9c27b0",
    "electrical": "#00bcd4",
    "winterization": "#607d8b",
    "calibration": "#009688",
    "greasing": "#8bc34a",
    "other": "#757575",
}


class MaintenanceAlertCard(QFrame):
    """Widget displaying a maintenance alert card."""

    def __init__(self, alert: MaintenanceAlert, on_log_service=None, parent=None):
        super().__init__(parent)
        self.alert = alert
        self._on_log_service = on_log_service
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Set border color based on urgency
        color = URGENCY_COLORS.get(self.alert.urgency, "#2196f3")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header row
        header_layout = QHBoxLayout()

        # Urgency badge
        urgency_label = QLabel(self.alert.urgency_display)
        urgency_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        header_layout.addWidget(urgency_label)

        # Maintenance type
        type_label = QLabel(self.alert.maintenance_type.replace("_", " ").title())
        maint_color = MAINTENANCE_COLORS.get(self.alert.maintenance_type, "#666")
        type_label.setStyleSheet(f"color: {maint_color}; font-weight: bold;")
        header_layout.addWidget(type_label)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Equipment name
        name_label = QLabel(self.alert.equipment_name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(name_label)

        # Equipment type
        type_info = QLabel(self.alert.equipment_type.replace("_", " ").title())
        type_info.setStyleSheet("color: #666;")
        layout.addWidget(type_info)

        # Due info
        due_label = QLabel(self.alert.due_display)
        due_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        layout.addWidget(due_label)

        # Hours info
        if self.alert.current_hours:
            hours_text = f"Current Hours: {self.alert.current_hours:,.1f}"
            if self.alert.next_service_hours:
                hours_text += f" / Service at: {self.alert.next_service_hours:,.0f}"
            hours_label = QLabel(hours_text)
            hours_label.setStyleSheet("color: #666; font-size: 11px;")
            layout.addWidget(hours_label)

        # Log service button
        if self._on_log_service:
            log_btn = QPushButton("Log Service")
            log_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1b5e20;
                }
            """)
            log_btn.clicked.connect(lambda: self._on_log_service(self.alert.equipment_id))
            layout.addWidget(log_btn)


class MaintenanceScheduleScreen(QWidget):
    """
    Maintenance schedule screen for Farm Operations Manager.

    Features:
    - View maintenance alerts (overdue, due soon, upcoming)
    - View maintenance history
    - Filter by equipment type and maintenance type
    - Log new maintenance from alerts
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._equipment_api = get_equipment_api()
        self._alerts: list[MaintenanceAlert] = []
        self._maintenance_history: list[MaintenanceInfo] = []
        self._equipment_list: list[EquipmentInfo] = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user after login."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the maintenance schedule UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Maintenance Schedule")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Summary cards
        summary_layout = QHBoxLayout()

        self._overdue_label = QLabel("0")
        self._overdue_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #d32f2f;
            }
        """)
        overdue_card = self._create_summary_card("Overdue", self._overdue_label)
        summary_layout.addWidget(overdue_card)

        self._due_soon_label = QLabel("0")
        self._due_soon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ff9800;
            }
        """)
        due_soon_card = self._create_summary_card("Due Soon", self._due_soon_label)
        summary_layout.addWidget(due_soon_card)

        self._upcoming_label = QLabel("0")
        self._upcoming_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2196f3;
            }
        """)
        upcoming_card = self._create_summary_card("Upcoming", self._upcoming_label)
        summary_layout.addWidget(upcoming_card)

        self._total_equipment_label = QLabel("0")
        self._total_equipment_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        total_card = self._create_summary_card("Total Equipment", self._total_equipment_label)
        summary_layout.addWidget(total_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Tabs for Alerts and History
        self._tabs = QTabWidget()

        # Alerts Tab
        alerts_widget = QWidget()
        alerts_layout = QVBoxLayout(alerts_widget)

        # Alerts filter
        alerts_filter_layout = QHBoxLayout()

        alerts_filter_layout.addWidget(QLabel("Days Ahead:"))
        self._days_ahead_combo = QComboBox()
        self._days_ahead_combo.addItems(["7 days", "14 days", "30 days", "60 days", "90 days"])
        self._days_ahead_combo.setCurrentIndex(2)  # 30 days default
        self._days_ahead_combo.currentIndexChanged.connect(self._load_alerts)
        alerts_filter_layout.addWidget(self._days_ahead_combo)

        alerts_filter_layout.addStretch()
        alerts_layout.addLayout(alerts_filter_layout)

        # Alerts scroll area
        self._alerts_scroll = QScrollArea()
        self._alerts_scroll.setWidgetResizable(True)
        self._alerts_scroll.setStyleSheet("QScrollArea { border: none; }")

        self._alerts_container = QWidget()
        self._alerts_layout = QVBoxLayout(self._alerts_container)
        self._alerts_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._alerts_scroll.setWidget(self._alerts_container)

        alerts_layout.addWidget(self._alerts_scroll)

        self._tabs.addTab(alerts_widget, "Maintenance Alerts")

        # History Tab
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)

        # History filters
        history_filter_layout = QHBoxLayout()

        history_filter_layout.addWidget(QLabel("Equipment:"))
        self._equipment_filter = QComboBox()
        self._equipment_filter.addItem("All Equipment", None)
        self._equipment_filter.currentIndexChanged.connect(self._load_history)
        history_filter_layout.addWidget(self._equipment_filter)

        history_filter_layout.addWidget(QLabel("Type:"))
        self._maint_type_filter = QComboBox()
        self._maint_type_filter.addItem("All Types", None)
        for value, label in EquipmentAPI.MAINTENANCE_TYPES:
            self._maint_type_filter.addItem(label, value)
        self._maint_type_filter.currentIndexChanged.connect(self._load_history)
        history_filter_layout.addWidget(self._maint_type_filter)

        history_filter_layout.addStretch()
        history_layout.addLayout(history_filter_layout)

        # History table
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(8)
        self._history_table.setHorizontalHeaderLabels([
            "Date", "Equipment", "Type", "Description",
            "Cost", "Performed By", "Vendor", "Next Service"
        ])
        self._history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._history_table.setAlternatingRowColors(True)
        self._history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        history_layout.addWidget(self._history_table)

        self._tabs.addTab(history_widget, "Maintenance History")

        layout.addWidget(self._tabs)

        # Status bar
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #666;")
        layout.addWidget(self._status_label)

    def _create_summary_card(self, title: str, value_label: QLabel) -> QWidget:
        """Create a summary card widget."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; color: #666;")
        card_layout.addWidget(title_lbl)

        card_layout.addWidget(value_label)

        return card

    def _load_data(self):
        """Load all data."""
        self._load_equipment_list()
        self._load_alerts()
        self._load_history()

    def _load_equipment_list(self):
        """Load equipment list for filters."""
        equipment, _ = self._equipment_api.list_equipment()
        self._equipment_list = equipment

        # Update equipment filter
        current_idx = self._equipment_filter.currentIndex()
        self._equipment_filter.clear()
        self._equipment_filter.addItem("All Equipment", None)
        for equip in equipment:
            self._equipment_filter.addItem(equip.name, equip.id)
        if current_idx < self._equipment_filter.count():
            self._equipment_filter.setCurrentIndex(current_idx)

        # Update total equipment count
        self._total_equipment_label.setText(str(len(equipment)))

    def _load_alerts(self):
        """Load maintenance alerts."""
        # Parse days ahead
        days_text = self._days_ahead_combo.currentText()
        days_ahead = int(days_text.split()[0])

        alerts, error = self._equipment_api.get_maintenance_alerts(days_ahead=days_ahead)

        if error:
            self._status_label.setText(f"Error loading alerts: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._alerts = alerts
        self._populate_alerts()

        # Update summary counts
        overdue = sum(1 for a in alerts if a.urgency == "overdue")
        due_soon = sum(1 for a in alerts if a.urgency == "due_soon")
        upcoming = sum(1 for a in alerts if a.urgency == "upcoming")

        self._overdue_label.setText(str(overdue))
        self._due_soon_label.setText(str(due_soon))
        self._upcoming_label.setText(str(upcoming))

        self._status_label.setText(f"{len(alerts)} maintenance alerts")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_alerts(self):
        """Populate the alerts container with alert cards."""
        # Clear existing alerts
        while self._alerts_layout.count():
            item = self._alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._alerts:
            no_alerts = QLabel("No maintenance alerts scheduled")
            no_alerts.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            no_alerts.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._alerts_layout.addWidget(no_alerts)
            return

        # Group by urgency
        urgency_order = ["overdue", "due_soon", "upcoming"]
        alerts_by_urgency = {}

        for alert in self._alerts:
            if alert.urgency not in alerts_by_urgency:
                alerts_by_urgency[alert.urgency] = []
            alerts_by_urgency[alert.urgency].append(alert)

        for urgency in urgency_order:
            if urgency in alerts_by_urgency:
                # Section header
                header = QLabel(urgency.replace("_", " ").title())
                header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                color = URGENCY_COLORS.get(urgency, "#666")
                header.setStyleSheet(f"color: {color}; padding: 10px 0;")
                self._alerts_layout.addWidget(header)

                # Alert cards in a grid-like layout
                cards_layout = QHBoxLayout()
                cards_layout.setSpacing(10)

                for i, alert in enumerate(alerts_by_urgency[urgency]):
                    card = MaintenanceAlertCard(
                        alert,
                        on_log_service=self._log_service_for_equipment
                    )
                    card.setMaximumWidth(350)
                    card.setMinimumWidth(280)
                    cards_layout.addWidget(card)

                    # Start new row every 3 cards
                    if (i + 1) % 3 == 0:
                        cards_layout.addStretch()
                        self._alerts_layout.addLayout(cards_layout)
                        cards_layout = QHBoxLayout()
                        cards_layout.setSpacing(10)

                cards_layout.addStretch()
                self._alerts_layout.addLayout(cards_layout)

        self._alerts_layout.addStretch()

    def _load_history(self):
        """Load maintenance history."""
        equipment_id = self._equipment_filter.currentData()
        maintenance_type = self._maint_type_filter.currentData()

        maintenance, error = self._equipment_api.list_maintenance(
            equipment_id=equipment_id,
            maintenance_type=maintenance_type,
            limit=100
        )

        if error:
            self._status_label.setText(f"Error loading history: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._maintenance_history = maintenance
        self._populate_history()

    def _populate_history(self):
        """Populate the history table."""
        self._history_table.setRowCount(len(self._maintenance_history))

        for row, maint in enumerate(self._maintenance_history):
            # Date
            date_text = maint.service_date[:10] if maint.service_date else "-"
            self._history_table.setItem(row, 0, QTableWidgetItem(date_text))

            # Equipment
            self._history_table.setItem(row, 1, QTableWidgetItem(maint.equipment_name or "-"))

            # Type (color-coded)
            type_item = QTableWidgetItem(maint.type_display)
            type_color = MAINTENANCE_COLORS.get(maint.maintenance_type, "#666")
            type_item.setForeground(QColor(type_color))
            self._history_table.setItem(row, 2, type_item)

            # Description
            self._history_table.setItem(row, 3, QTableWidgetItem(maint.description or "-"))

            # Cost
            self._history_table.setItem(row, 4, QTableWidgetItem(maint.cost_display))

            # Performed By
            self._history_table.setItem(row, 5, QTableWidgetItem(maint.performed_by or "-"))

            # Vendor
            self._history_table.setItem(row, 6, QTableWidgetItem(maint.vendor or "-"))

            # Next Service
            next_text = "-"
            if maint.next_service_date:
                next_text = maint.next_service_date[:10]
            elif maint.next_service_hours:
                next_text = f"At {maint.next_service_hours:,.0f} hrs"
            self._history_table.setItem(row, 7, QTableWidgetItem(next_text))

    def _log_service_for_equipment(self, equipment_id: int):
        """Open the equipment management screen to log service."""
        # Find the equipment
        equipment = None
        for equip in self._equipment_list:
            if equip.id == equipment_id:
                equipment = equip
                break

        if not equipment:
            QMessageBox.warning(self, "Error", "Equipment not found")
            return

        # Import and show dialog directly here
        from ui.screens.equipment_management import LogMaintenanceDialog

        dialog = LogMaintenanceDialog(equipment=equipment, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            maintenance, error = self._equipment_api.create_maintenance(
                **dialog.maintenance_data
            )
            if error:
                QMessageBox.critical(self, "Error", f"Failed to log maintenance: {error}")
            else:
                QMessageBox.information(self, "Success", "Maintenance logged successfully")
                self._load_data()

    def refresh(self):
        """Refresh the maintenance schedule."""
        self._load_data()
