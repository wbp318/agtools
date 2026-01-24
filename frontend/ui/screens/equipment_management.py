"""
Equipment Management Screen

Screen for managing farm equipment fleet - tractors, combines, sprayers, etc.
AgTools v2.5.0 Phase 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QTextEdit, QDoubleSpinBox, QSpinBox, QGroupBox,
    QDateEdit
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.equipment_api import (
    get_equipment_api, EquipmentAPI, EquipmentInfo
)
from api.auth_api import UserInfo


# Status colors for visual identification
STATUS_COLORS = {
    "available": "#2e7d32",      # Green
    "in_use": "#1976d2",         # Blue
    "maintenance": "#f57c00",    # Orange
    "retired": "#757575",        # Gray
}

# Equipment type icons/colors
TYPE_COLORS = {
    "tractor": "#4caf50",
    "combine": "#ff9800",
    "sprayer": "#2196f3",
    "planter": "#9c27b0",
    "tillage": "#795548",
    "truck": "#607d8b",
    "atv": "#00bcd4",
    "grain_cart": "#ff5722",
    "other": "#9e9e9e",
}


class CreateEquipmentDialog(QDialog):
    """Dialog for creating new equipment."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Equipment")
        self.setMinimumWidth(550)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(10)

        # Name
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., Main Tractor, Sprayer #2")
        basic_layout.addRow("Equipment Name:", self._name_input)

        # Type
        self._type_combo = QComboBox()
        for value, label in EquipmentAPI.EQUIPMENT_TYPES:
            self._type_combo.addItem(label, value)
        basic_layout.addRow("Type:", self._type_combo)

        # Status
        self._status_combo = QComboBox()
        for value, label in EquipmentAPI.EQUIPMENT_STATUSES:
            self._status_combo.addItem(label, value)
        basic_layout.addRow("Status:", self._status_combo)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Details Group
        details_group = QGroupBox("Equipment Details")
        details_layout = QFormLayout()
        details_layout.setSpacing(10)

        # Make
        self._make_input = QLineEdit()
        self._make_input.setPlaceholderText("e.g., John Deere, Case IH")
        details_layout.addRow("Make:", self._make_input)

        # Model
        self._model_input = QLineEdit()
        self._model_input.setPlaceholderText("e.g., 8R 410, 9250")
        details_layout.addRow("Model:", self._model_input)

        # Year
        self._year_input = QSpinBox()
        self._year_input.setRange(1950, 2030)
        self._year_input.setValue(2020)
        details_layout.addRow("Year:", self._year_input)

        # Serial Number
        self._serial_input = QLineEdit()
        self._serial_input.setPlaceholderText("Optional")
        details_layout.addRow("Serial Number:", self._serial_input)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Usage/Cost Group
        usage_group = QGroupBox("Usage & Costs")
        usage_layout = QFormLayout()
        usage_layout.setSpacing(10)

        # Current Hours
        self._hours_input = QDoubleSpinBox()
        self._hours_input.setRange(0, 100000)
        self._hours_input.setDecimals(1)
        self._hours_input.setSuffix(" hrs")
        usage_layout.addRow("Current Hours:", self._hours_input)

        # Hourly Rate
        self._hourly_rate_input = QDoubleSpinBox()
        self._hourly_rate_input.setRange(0, 1000)
        self._hourly_rate_input.setDecimals(2)
        self._hourly_rate_input.setPrefix("$")
        self._hourly_rate_input.setSuffix("/hr")
        usage_layout.addRow("Hourly Rate:", self._hourly_rate_input)

        # Current Value
        self._value_input = QDoubleSpinBox()
        self._value_input.setRange(0, 10000000)
        self._value_input.setDecimals(0)
        self._value_input.setPrefix("$")
        self._value_input.setSingleStep(1000)
        usage_layout.addRow("Current Value:", self._value_input)

        # Location
        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("e.g., Main Shop, North Barn")
        usage_layout.addRow("Location:", self._location_input)

        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(80)
        self._notes_input.setPlaceholderText("Additional notes about this equipment...")
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Add Equipment")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """)
        create_btn.clicked.connect(self._create_equipment)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _create_equipment(self):
        """Validate and prepare equipment data."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Equipment name is required")
            return

        self.equipment_data = {
            "name": name,
            "equipment_type": self._type_combo.currentData(),
            "status": self._status_combo.currentData(),
            "make": self._make_input.text().strip() or None,
            "model": self._model_input.text().strip() or None,
            "year": self._year_input.value(),
            "serial_number": self._serial_input.text().strip() or None,
            "current_hours": self._hours_input.value(),
            "hourly_rate": self._hourly_rate_input.value() or None,
            "current_value": self._value_input.value() or None,
            "current_location": self._location_input.text().strip() or None,
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class EditEquipmentDialog(QDialog):
    """Dialog for editing existing equipment."""

    def __init__(self, equipment: EquipmentInfo, parent=None):
        super().__init__(parent)
        self.equipment = equipment
        self.setWindowTitle(f"Edit Equipment: {equipment.name}")
        self.setMinimumWidth(550)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(10)

        # Name
        self._name_input = QLineEdit(self.equipment.name)
        basic_layout.addRow("Equipment Name:", self._name_input)

        # Type
        self._type_combo = QComboBox()
        type_idx = 0
        for idx, (value, label) in enumerate(EquipmentAPI.EQUIPMENT_TYPES):
            self._type_combo.addItem(label, value)
            if value == self.equipment.equipment_type:
                type_idx = idx
        self._type_combo.setCurrentIndex(type_idx)
        basic_layout.addRow("Type:", self._type_combo)

        # Status
        self._status_combo = QComboBox()
        status_idx = 0
        for idx, (value, label) in enumerate(EquipmentAPI.EQUIPMENT_STATUSES):
            self._status_combo.addItem(label, value)
            if value == self.equipment.status:
                status_idx = idx
        self._status_combo.setCurrentIndex(status_idx)
        basic_layout.addRow("Status:", self._status_combo)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Details Group
        details_group = QGroupBox("Equipment Details")
        details_layout = QFormLayout()
        details_layout.setSpacing(10)

        # Make
        self._make_input = QLineEdit(self.equipment.make or "")
        details_layout.addRow("Make:", self._make_input)

        # Model
        self._model_input = QLineEdit(self.equipment.model or "")
        details_layout.addRow("Model:", self._model_input)

        # Year
        self._year_input = QSpinBox()
        self._year_input.setRange(1950, 2030)
        self._year_input.setValue(self.equipment.year or 2020)
        details_layout.addRow("Year:", self._year_input)

        # Serial Number
        self._serial_input = QLineEdit(self.equipment.serial_number or "")
        details_layout.addRow("Serial Number:", self._serial_input)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Usage/Cost Group
        usage_group = QGroupBox("Usage & Costs")
        usage_layout = QFormLayout()
        usage_layout.setSpacing(10)

        # Current Hours (display only)
        hours_label = QLabel(f"{self.equipment.current_hours:,.1f} hrs")
        hours_label.setStyleSheet("font-weight: bold;")
        usage_layout.addRow("Current Hours:", hours_label)

        # Hourly Rate
        self._hourly_rate_input = QDoubleSpinBox()
        self._hourly_rate_input.setRange(0, 1000)
        self._hourly_rate_input.setDecimals(2)
        self._hourly_rate_input.setPrefix("$")
        self._hourly_rate_input.setSuffix("/hr")
        self._hourly_rate_input.setValue(self.equipment.hourly_rate or 0)
        usage_layout.addRow("Hourly Rate:", self._hourly_rate_input)

        # Current Value
        self._value_input = QDoubleSpinBox()
        self._value_input.setRange(0, 10000000)
        self._value_input.setDecimals(0)
        self._value_input.setPrefix("$")
        self._value_input.setSingleStep(1000)
        self._value_input.setValue(self.equipment.current_value or 0)
        usage_layout.addRow("Current Value:", self._value_input)

        # Location
        self._location_input = QLineEdit(self.equipment.current_location or "")
        usage_layout.addRow("Location:", self._location_input)

        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(80)
        self._notes_input.setText(self.equipment.notes or "")
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """)
        save_btn.clicked.connect(self._save_equipment)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_equipment(self):
        """Validate and prepare equipment update data."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Equipment name is required")
            return

        self.equipment_data = {
            "name": name,
            "equipment_type": self._type_combo.currentData(),
            "status": self._status_combo.currentData(),
            "make": self._make_input.text().strip() or None,
            "model": self._model_input.text().strip() or None,
            "year": self._year_input.value(),
            "serial_number": self._serial_input.text().strip() or None,
            "hourly_rate": self._hourly_rate_input.value() or None,
            "current_value": self._value_input.value() or None,
            "current_location": self._location_input.text().strip() or None,
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class UpdateHoursDialog(QDialog):
    """Dialog for updating equipment hours."""

    def __init__(self, equipment: EquipmentInfo, parent=None):
        super().__init__(parent)
        self.equipment = equipment
        self.setWindowTitle(f"Update Hours: {equipment.name}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Info
        info_label = QLabel(f"<b>{self.equipment.name}</b><br>"
                           f"{self.equipment.make_model_display}")
        layout.addWidget(info_label)

        # Current hours
        current_label = QLabel(f"Current Hours: <b>{self.equipment.current_hours:,.1f}</b>")
        current_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(current_label)

        # New hours input
        form_layout = QFormLayout()
        self._hours_input = QDoubleSpinBox()
        self._hours_input.setRange(self.equipment.current_hours, 100000)
        self._hours_input.setDecimals(1)
        self._hours_input.setSuffix(" hrs")
        self._hours_input.setValue(self.equipment.current_hours)
        form_layout.addRow("New Hours:", self._hours_input)
        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        update_btn = QPushButton("Update Hours")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        update_btn.clicked.connect(self._update_hours)
        button_layout.addWidget(update_btn)

        layout.addLayout(button_layout)

    def _update_hours(self):
        """Validate and set new hours."""
        new_hours = self._hours_input.value()
        if new_hours < self.equipment.current_hours:
            QMessageBox.warning(self, "Validation Error",
                              "New hours cannot be less than current hours")
            return

        self.new_hours = new_hours
        self.accept()


class LogMaintenanceDialog(QDialog):
    """Dialog for logging maintenance."""

    def __init__(self, equipment: EquipmentInfo, parent=None):
        super().__init__(parent)
        self.equipment = equipment
        self.setWindowTitle(f"Log Maintenance: {equipment.name}")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Equipment Info
        info_label = QLabel(f"<b>{self.equipment.name}</b><br>"
                           f"{self.equipment.make_model_display} | "
                           f"Hours: {self.equipment.current_hours:,.1f}")
        layout.addWidget(info_label)

        # Maintenance Details
        details_group = QGroupBox("Maintenance Details")
        details_layout = QFormLayout()
        details_layout.setSpacing(10)

        # Type
        self._type_combo = QComboBox()
        for value, label in EquipmentAPI.MAINTENANCE_TYPES:
            self._type_combo.addItem(label, value)
        details_layout.addRow("Maintenance Type:", self._type_combo)

        # Service Date
        self._service_date = QDateEdit()
        self._service_date.setDate(QDate.currentDate())
        self._service_date.setCalendarPopup(True)
        details_layout.addRow("Service Date:", self._service_date)

        # Cost
        self._cost_input = QDoubleSpinBox()
        self._cost_input.setRange(0, 100000)
        self._cost_input.setDecimals(2)
        self._cost_input.setPrefix("$")
        details_layout.addRow("Cost:", self._cost_input)

        # Performed By
        self._performed_by_input = QLineEdit()
        self._performed_by_input.setPlaceholderText("e.g., Shop, John Deere Dealer")
        details_layout.addRow("Performed By:", self._performed_by_input)

        # Vendor
        self._vendor_input = QLineEdit()
        self._vendor_input.setPlaceholderText("e.g., Local Parts Store")
        details_layout.addRow("Vendor:", self._vendor_input)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Next Service Group
        next_group = QGroupBox("Next Service (Optional)")
        next_layout = QFormLayout()
        next_layout.setSpacing(10)

        # Next Service Date
        self._next_date = QDateEdit()
        self._next_date.setDate(QDate.currentDate().addMonths(6))
        self._next_date.setCalendarPopup(True)
        self._next_date_enabled = QComboBox()
        self._next_date_enabled.addItems(["Not Scheduled", "Schedule by Date"])
        self._next_date_enabled.currentIndexChanged.connect(
            lambda: self._next_date.setEnabled(self._next_date_enabled.currentIndex() == 1)
        )
        self._next_date.setEnabled(False)
        next_layout.addRow("Next Service:", self._next_date_enabled)
        next_layout.addRow("", self._next_date)

        # Next Service Hours
        self._next_hours = QDoubleSpinBox()
        self._next_hours.setRange(0, 100000)
        self._next_hours.setDecimals(0)
        self._next_hours.setSuffix(" hrs")
        self._next_hours.setSpecialValueText("Not set")
        next_layout.addRow("Or at Hours:", self._next_hours)

        next_group.setLayout(next_layout)
        layout.addWidget(next_group)

        # Description
        desc_group = QGroupBox("Description & Parts Used")
        desc_layout = QVBoxLayout()
        self._description_input = QTextEdit()
        self._description_input.setMaximumHeight(60)
        self._description_input.setPlaceholderText("Description of work performed...")
        desc_layout.addWidget(self._description_input)

        self._parts_input = QLineEdit()
        self._parts_input.setPlaceholderText("Parts used (e.g., Oil filter, 10W-40 oil)")
        desc_layout.addWidget(self._parts_input)
        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        log_btn = QPushButton("Log Maintenance")
        log_btn.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
        """)
        log_btn.clicked.connect(self._log_maintenance)
        button_layout.addWidget(log_btn)

        layout.addLayout(button_layout)

    def _log_maintenance(self):
        """Prepare maintenance data."""
        next_date = None
        if self._next_date_enabled.currentIndex() == 1:
            next_date = self._next_date.date().toString("yyyy-MM-dd")

        next_hours = None
        if self._next_hours.value() > 0:
            next_hours = self._next_hours.value()

        self.maintenance_data = {
            "equipment_id": self.equipment.id,
            "maintenance_type": self._type_combo.currentData(),
            "service_date": self._service_date.date().toString("yyyy-MM-dd"),
            "next_service_date": next_date,
            "next_service_hours": next_hours,
            "cost": self._cost_input.value() or None,
            "performed_by": self._performed_by_input.text().strip() or None,
            "vendor": self._vendor_input.text().strip() or None,
            "description": self._description_input.toPlainText().strip() or None,
            "parts_used": self._parts_input.text().strip() or None
        }
        self.accept()


class EquipmentManagementScreen(QWidget):
    """
    Equipment management screen for Farm Operations Manager.

    Features:
    - List equipment with filters (type, status, search)
    - Create new equipment
    - Edit existing equipment
    - Update hour meter readings
    - Log maintenance
    - View equipment summary
    - Delete equipment (manager/admin only)
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._equipment_api = get_equipment_api()
        self._equipment: list[EquipmentInfo] = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user after login."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the equipment management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Equipment Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add equipment button
        add_btn = QPushButton("+ Add Equipment")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """)
        add_btn.clicked.connect(self._show_create_dialog)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Summary cards
        summary_layout = QHBoxLayout()

        self._total_equipment_label = QLabel("0")
        self._total_equipment_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        equip_card = self._create_summary_card("Total Equipment", self._total_equipment_label)
        summary_layout.addWidget(equip_card)

        self._total_value_label = QLabel("$0")
        self._total_value_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
            }
        """)
        value_card = self._create_summary_card("Fleet Value", self._total_value_label)
        summary_layout.addWidget(value_card)

        self._total_hours_label = QLabel("0")
        self._total_hours_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #7b1fa2;
            }
        """)
        hours_card = self._create_summary_card("Total Hours", self._total_hours_label)
        summary_layout.addWidget(hours_card)

        self._in_maintenance_label = QLabel("0")
        self._in_maintenance_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #f57c00;
            }
        """)
        maint_card = self._create_summary_card("In Maintenance", self._in_maintenance_label)
        summary_layout.addWidget(maint_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Filters
        filter_layout = QHBoxLayout()

        # Type filter
        filter_layout.addWidget(QLabel("Type:"))
        self._type_filter = QComboBox()
        self._type_filter.addItem("All Types", None)
        for value, label in EquipmentAPI.EQUIPMENT_TYPES:
            self._type_filter.addItem(label, value)
        self._type_filter.currentIndexChanged.connect(self._load_equipment)
        filter_layout.addWidget(self._type_filter)

        # Status filter
        filter_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItem("All Statuses", None)
        for value, label in EquipmentAPI.EQUIPMENT_STATUSES:
            self._status_filter.addItem(label, value)
        self._status_filter.currentIndexChanged.connect(self._load_equipment)
        filter_layout.addWidget(self._status_filter)

        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search equipment...")
        self._search_input.textChanged.connect(self._load_equipment)
        filter_layout.addWidget(self._search_input)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Equipment table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "Equipment Name", "Type", "Make/Model", "Year", "Hours",
            "Status", "Value", "Location", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(8, 280)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
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
        layout.addWidget(self._table)

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
        """Load equipment and summary."""
        self._load_equipment()
        self._load_summary()

    def _load_summary(self):
        """Load summary statistics."""
        summary, error = self._equipment_api.get_summary()
        if summary:
            self._total_equipment_label.setText(str(summary.total_equipment))
            self._total_value_label.setText(f"${summary.total_value:,.0f}")
            self._total_hours_label.setText(f"{summary.total_hours:,.0f}")
            self._in_maintenance_label.setText(str(summary.in_maintenance))

    def _load_equipment(self):
        """Load equipment from API with current filters."""
        equipment_type = self._type_filter.currentData()
        status = self._status_filter.currentData()
        search = self._search_input.text().strip() or None

        equipment, error = self._equipment_api.list_equipment(
            equipment_type=equipment_type,
            status=status,
            search=search
        )

        if error:
            self._status_label.setText(f"Error loading equipment: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._equipment = equipment
        self._populate_table()
        self._status_label.setText(f"{len(equipment)} equipment found")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_table(self):
        """Populate the table with equipment data."""
        self._table.setRowCount(len(self._equipment))

        for row, equip in enumerate(self._equipment):
            # Equipment Name
            name_item = QTableWidgetItem(equip.name)
            name_item.setFont(QFont("Arial", -1, QFont.Weight.Bold))
            self._table.setItem(row, 0, name_item)

            # Type (color-coded)
            type_item = QTableWidgetItem(equip.type_display)
            type_color = TYPE_COLORS.get(equip.equipment_type, "#666")
            type_item.setForeground(QColor(type_color))
            self._table.setItem(row, 1, type_item)

            # Make/Model
            self._table.setItem(row, 2, QTableWidgetItem(equip.make_model_display))

            # Year
            year_text = str(equip.year) if equip.year else "-"
            self._table.setItem(row, 3, QTableWidgetItem(year_text))

            # Hours
            self._table.setItem(row, 4, QTableWidgetItem(equip.hours_display))

            # Status (color-coded)
            status_item = QTableWidgetItem(equip.status_display)
            status_color = STATUS_COLORS.get(equip.status, "#666")
            status_item.setForeground(QColor(status_color))
            self._table.setItem(row, 5, status_item)

            # Value
            self._table.setItem(row, 6, QTableWidgetItem(equip.value_display))

            # Location
            self._table.setItem(row, 7, QTableWidgetItem(equip.current_location or "-"))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            edit_btn.clicked.connect(lambda checked, e=equip: self._show_edit_dialog(e))
            actions_layout.addWidget(edit_btn)

            # Hours button
            hours_btn = QPushButton("Hours")
            hours_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7b1fa2;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #6a1b9a;
                }
            """)
            hours_btn.clicked.connect(lambda checked, e=equip: self._show_hours_dialog(e))
            actions_layout.addWidget(hours_btn)

            # Maintenance button
            maint_btn = QPushButton("Service")
            maint_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f57c00;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e65100;
                }
            """)
            maint_btn.clicked.connect(lambda checked, e=equip: self._show_maintenance_dialog(e))
            actions_layout.addWidget(maint_btn)

            # Delete button (manager/admin only)
            if self._current_user and self._current_user.role in ("admin", "manager"):
                delete_btn = QPushButton("Del")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d32f2f;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #b71c1c;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, e=equip: self._delete_equipment(e))
                actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 8, actions_widget)

    def _show_create_dialog(self):
        """Show create equipment dialog."""
        dialog = CreateEquipmentDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            equipment, error = self._equipment_api.create_equipment(**dialog.equipment_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to create equipment: {error}")
            else:
                QMessageBox.information(self, "Success",
                                       f"Equipment '{equipment.name}' created successfully")
                self._load_data()

    def _show_edit_dialog(self, equipment: EquipmentInfo):
        """Show edit equipment dialog."""
        dialog = EditEquipmentDialog(equipment=equipment, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated, error = self._equipment_api.update_equipment(
                equipment.id, **dialog.equipment_data
            )
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update equipment: {error}")
            else:
                QMessageBox.information(self, "Success", "Equipment updated successfully")
                self._load_data()

    def _show_hours_dialog(self, equipment: EquipmentInfo):
        """Show update hours dialog."""
        dialog = UpdateHoursDialog(equipment=equipment, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated, error = self._equipment_api.update_hours(
                equipment.id, dialog.new_hours
            )
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update hours: {error}")
            else:
                QMessageBox.information(self, "Success",
                                       f"Hours updated to {dialog.new_hours:,.1f}")
                self._load_data()

    def _show_maintenance_dialog(self, equipment: EquipmentInfo):
        """Show log maintenance dialog."""
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

    def _delete_equipment(self, equipment: EquipmentInfo):
        """Delete equipment."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to retire '{equipment.name}'?\n\n"
            f"Hours: {equipment.current_hours:,.1f}\n"
            f"Value: {equipment.value_display}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._equipment_api.delete_equipment(equipment.id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to retire equipment: {error}")
            else:
                QMessageBox.information(self, "Success", "Equipment retired successfully")
                self._load_data()

    def refresh(self):
        """Refresh the equipment list."""
        self._load_data()
