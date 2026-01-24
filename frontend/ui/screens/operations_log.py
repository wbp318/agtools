"""
Operations Log Screen

Screen for logging and tracking field operations - sprays, fertilizer, planting, harvest, etc.
AgTools v2.5.0 Phase 3
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QTextEdit, QDoubleSpinBox, QGroupBox,
    QDateEdit, QSpinBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.operations_api import get_operations_api, OperationsAPI, OperationInfo
from api.field_api import get_field_api, FieldInfo
from api.equipment_api import get_equipment_api, EquipmentInfo
from api.inventory_api import get_inventory_api, InventoryItem
from api.auth_api import UserInfo


# Operation type colors
OPERATION_COLORS = {
    "spray": "#1976d2",       # Blue
    "fertilizer": "#2e7d32",  # Green
    "planting": "#7b1fa2",    # Purple
    "harvest": "#f9a825",     # Yellow/Gold
    "tillage": "#795548",     # Brown
    "scouting": "#00796b",    # Teal
    "irrigation": "#0288d1",  # Light Blue
    "seed_treatment": "#c2185b", # Pink
    "cover_crop": "#558b2f",  # Dark Green
    "other": "#757575",       # Gray
}


class LogOperationDialog(QDialog):
    """Dialog for logging a new field operation."""

    def __init__(self, fields: list = None, users: list = None,
                 equipment: list = None, inventory: list = None, parent=None):
        super().__init__(parent)
        self.fields = fields or []
        self.users = users or []
        self.equipment = equipment or []
        self.inventory = inventory or []
        self.setWindowTitle("Log Field Operation")
        self.setMinimumWidth(550)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Basic Info Group
        basic_group = QGroupBox("Operation Details")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(10)

        # Field selection
        self._field_combo = QComboBox()
        self._field_combo.addItem("Select Field...", None)
        for field in self.fields:
            display = f"{field.name} ({field.acreage:.1f} ac)"
            if field.farm_name:
                display = f"{field.farm_name} - {display}"
            self._field_combo.addItem(display, field.id)
        basic_layout.addRow("Field:", self._field_combo)

        # Operation type
        self._type_combo = QComboBox()
        for value, label in OperationsAPI.OPERATION_TYPES:
            self._type_combo.addItem(label, value)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        basic_layout.addRow("Operation Type:", self._type_combo)

        # Date
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        basic_layout.addRow("Date:", self._date_edit)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Equipment Selection Group (Phase 4)
        equipment_group = QGroupBox("Equipment Used (Optional)")
        equipment_layout = QFormLayout()
        equipment_layout.setSpacing(10)

        # Equipment selection
        self._equipment_combo = QComboBox()
        self._equipment_combo.addItem("No equipment selected", None)
        for equip in self.equipment:
            if equip.status == "available" or equip.status == "in_use":
                display = f"{equip.name} ({equip.type_display})"
                if equip.make and equip.model:
                    display += f" - {equip.make} {equip.model}"
                self._equipment_combo.addItem(display, equip.id)
        equipment_layout.addRow("Equipment:", self._equipment_combo)

        # Hours used
        self._hours_used_input = QDoubleSpinBox()
        self._hours_used_input.setRange(0, 100)
        self._hours_used_input.setDecimals(1)
        self._hours_used_input.setSuffix(" hrs")
        self._hours_used_input.setSpecialValueText("N/A")
        equipment_layout.addRow("Hours Used:", self._hours_used_input)

        equipment_group.setLayout(equipment_layout)
        layout.addWidget(equipment_group)

        # Product Info Group
        self._product_group = QGroupBox("Product Information")
        product_layout = QFormLayout()
        product_layout.setSpacing(10)

        # Inventory item selection (Phase 4)
        self._inventory_combo = QComboBox()
        self._inventory_combo.addItem("Enter manually / Not in inventory", None)
        for item in self.inventory:
            if item.quantity > 0:
                display = f"{item.name} ({item.quantity:.2f} {item.unit} available)"
                self._inventory_combo.addItem(display, item.id)
        self._inventory_combo.currentIndexChanged.connect(self._on_inventory_selected)
        product_layout.addRow("From Inventory:", self._inventory_combo)

        # Product name
        self._product_input = QLineEdit()
        self._product_input.setPlaceholderText("e.g., Roundup PowerMax, 28% UAN")
        product_layout.addRow("Product:", self._product_input)

        # Rate
        rate_layout = QHBoxLayout()
        self._rate_input = QDoubleSpinBox()
        self._rate_input.setRange(0, 100000)
        self._rate_input.setDecimals(3)
        rate_layout.addWidget(self._rate_input)

        self._rate_unit_combo = QComboBox()
        self._rate_unit_combo.setEditable(True)
        for unit in OperationsAPI.RATE_UNITS:
            self._rate_unit_combo.addItem(unit)
        rate_layout.addWidget(self._rate_unit_combo)
        product_layout.addRow("Rate:", rate_layout)

        # Quantity
        qty_layout = QHBoxLayout()
        self._qty_input = QDoubleSpinBox()
        self._qty_input.setRange(0, 1000000)
        self._qty_input.setDecimals(2)
        qty_layout.addWidget(self._qty_input)

        self._qty_unit_combo = QComboBox()
        self._qty_unit_combo.setEditable(True)
        for unit in OperationsAPI.QUANTITY_UNITS:
            self._qty_unit_combo.addItem(unit)
        qty_layout.addWidget(self._qty_unit_combo)
        product_layout.addRow("Total Quantity:", qty_layout)

        self._product_group.setLayout(product_layout)
        layout.addWidget(self._product_group)

        # Harvest Info Group (hidden by default)
        self._harvest_group = QGroupBox("Harvest Information")
        harvest_layout = QFormLayout()
        harvest_layout.setSpacing(10)

        # Yield
        yield_layout = QHBoxLayout()
        self._yield_input = QDoubleSpinBox()
        self._yield_input.setRange(0, 1000)
        self._yield_input.setDecimals(1)
        yield_layout.addWidget(self._yield_input)

        self._yield_unit_combo = QComboBox()
        for unit in OperationsAPI.YIELD_UNITS:
            self._yield_unit_combo.addItem(unit)
        yield_layout.addWidget(self._yield_unit_combo)
        harvest_layout.addRow("Yield:", yield_layout)

        # Moisture
        self._moisture_input = QDoubleSpinBox()
        self._moisture_input.setRange(0, 100)
        self._moisture_input.setDecimals(1)
        self._moisture_input.setSuffix("%")
        harvest_layout.addRow("Moisture:", self._moisture_input)

        self._harvest_group.setLayout(harvest_layout)
        self._harvest_group.hide()
        layout.addWidget(self._harvest_group)

        # Cost Group
        cost_group = QGroupBox("Cost Tracking (Optional)")
        cost_layout = QFormLayout()
        cost_layout.setSpacing(10)

        # Acres covered
        self._acres_input = QDoubleSpinBox()
        self._acres_input.setRange(0, 100000)
        self._acres_input.setDecimals(2)
        self._acres_input.setSuffix(" acres")
        self._acres_input.setSpecialValueText("Use field acreage")
        cost_layout.addRow("Acres Covered:", self._acres_input)

        # Product cost
        self._product_cost_input = QDoubleSpinBox()
        self._product_cost_input.setRange(0, 1000000)
        self._product_cost_input.setDecimals(2)
        self._product_cost_input.setPrefix("$")
        cost_layout.addRow("Product Cost:", self._product_cost_input)

        # Application cost
        self._app_cost_input = QDoubleSpinBox()
        self._app_cost_input.setRange(0, 100000)
        self._app_cost_input.setDecimals(2)
        self._app_cost_input.setPrefix("$")
        cost_layout.addRow("Application Cost:", self._app_cost_input)

        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        # Weather Group (collapsed by default)
        weather_group = QGroupBox("Weather Conditions (Optional)")
        weather_layout = QFormLayout()
        weather_layout.setSpacing(10)

        weather_row = QHBoxLayout()

        self._temp_input = QSpinBox()
        self._temp_input.setRange(-40, 130)
        self._temp_input.setSuffix(" F")
        self._temp_input.setSpecialValueText("N/A")
        self._temp_input.setValue(-40)
        weather_row.addWidget(QLabel("Temp:"))
        weather_row.addWidget(self._temp_input)

        self._wind_input = QSpinBox()
        self._wind_input.setRange(0, 100)
        self._wind_input.setSuffix(" mph")
        weather_row.addWidget(QLabel("Wind:"))
        weather_row.addWidget(self._wind_input)

        self._humidity_input = QSpinBox()
        self._humidity_input.setRange(0, 100)
        self._humidity_input.setSuffix("%")
        weather_row.addWidget(QLabel("Humidity:"))
        weather_row.addWidget(self._humidity_input)

        weather_layout.addRow(weather_row)

        weather_group.setLayout(weather_layout)
        layout.addWidget(weather_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setPlaceholderText("Additional notes about this operation...")
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Log Operation")
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
        create_btn.clicked.connect(self._create_operation)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _on_type_changed(self, index):
        """Handle operation type change."""
        op_type = self._type_combo.currentData()

        # Show/hide harvest group
        if op_type == "harvest":
            self._harvest_group.show()
            self._product_group.hide()
        else:
            self._harvest_group.hide()
            self._product_group.show()

    def _on_inventory_selected(self, index):
        """Handle inventory item selection."""
        inventory_id = self._inventory_combo.currentData()
        if inventory_id:
            # Find the selected inventory item and populate product field
            for item in self.inventory:
                if item.id == inventory_id:
                    self._product_input.setText(item.name)
                    # Set unit in the quantity unit combo
                    unit_idx = self._qty_unit_combo.findText(item.unit)
                    if unit_idx >= 0:
                        self._qty_unit_combo.setCurrentIndex(unit_idx)
                    else:
                        self._qty_unit_combo.setCurrentText(item.unit)
                    break

    def _create_operation(self):
        """Validate and prepare operation data."""
        field_id = self._field_combo.currentData()

        if not field_id:
            QMessageBox.warning(self, "Validation Error", "Please select a field")
            return

        op_type = self._type_combo.currentData()

        self.operation_data = {
            "field_id": field_id,
            "operation_type": op_type,
            "operation_date": self._date_edit.date().toString("yyyy-MM-dd"),
        }

        # Add equipment info (Phase 4)
        equipment_id = self._equipment_combo.currentData()
        if equipment_id:
            self.operation_data["equipment_id"] = equipment_id
            if self._hours_used_input.value() > 0:
                self.operation_data["hours_used"] = self._hours_used_input.value()

        # Add product info
        if self._product_input.text().strip():
            self.operation_data["product_name"] = self._product_input.text().strip()
        if self._rate_input.value() > 0:
            self.operation_data["rate"] = self._rate_input.value()
            self.operation_data["rate_unit"] = self._rate_unit_combo.currentText()
        if self._qty_input.value() > 0:
            self.operation_data["quantity"] = self._qty_input.value()
            self.operation_data["quantity_unit"] = self._qty_unit_combo.currentText()

        # Add inventory item reference (Phase 4)
        inventory_item_id = self._inventory_combo.currentData()
        if inventory_item_id:
            self.operation_data["inventory_item_id"] = inventory_item_id

        # Add harvest info
        if op_type == "harvest":
            if self._yield_input.value() > 0:
                self.operation_data["yield_amount"] = self._yield_input.value()
                self.operation_data["yield_unit"] = self._yield_unit_combo.currentText()
            if self._moisture_input.value() > 0:
                self.operation_data["moisture_percent"] = self._moisture_input.value()

        # Add cost info
        if self._acres_input.value() > 0:
            self.operation_data["acres_covered"] = self._acres_input.value()
        if self._product_cost_input.value() > 0:
            self.operation_data["product_cost"] = self._product_cost_input.value()
        if self._app_cost_input.value() > 0:
            self.operation_data["application_cost"] = self._app_cost_input.value()

        # Add weather info
        if self._temp_input.value() > -40:
            self.operation_data["weather_temp"] = self._temp_input.value()
        if self._wind_input.value() > 0:
            self.operation_data["weather_wind"] = self._wind_input.value()
        if self._humidity_input.value() > 0:
            self.operation_data["weather_humidity"] = self._humidity_input.value()

        # Add notes
        if self._notes_input.toPlainText().strip():
            self.operation_data["notes"] = self._notes_input.toPlainText().strip()

        self.accept()


class OperationsLogScreen(QWidget):
    """
    Operations log screen for Farm Operations Manager.

    Features:
    - List operations with filters (field, type, date range)
    - Log new operations
    - View operation details
    - Summary statistics
    - Delete operations (manager/admin only)
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._ops_api = get_operations_api()
        self._field_api = get_field_api()
        self._equipment_api = get_equipment_api()
        self._inventory_api = get_inventory_api()
        self._operations: list[OperationInfo] = []
        self._fields: list[FieldInfo] = []
        self._equipment: list[EquipmentInfo] = []
        self._inventory: list[InventoryItem] = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user after login."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the operations log UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Operations Log")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add operation button
        add_btn = QPushButton("+ Log Operation")
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
        add_btn.clicked.connect(self._show_log_dialog)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Summary cards
        summary_layout = QHBoxLayout()

        self._total_ops_label = QLabel("0")
        self._total_ops_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        ops_card = self._create_summary_card("Total Operations", self._total_ops_label)
        summary_layout.addWidget(ops_card)

        self._total_cost_label = QLabel("$0")
        self._total_cost_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
            }
        """)
        cost_card = self._create_summary_card("Total Cost", self._total_cost_label)
        summary_layout.addWidget(cost_card)

        self._breakdown_label = QLabel("-")
        self._breakdown_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
            }
        """)
        breakdown_card = self._create_summary_card("By Type", self._breakdown_label)
        summary_layout.addWidget(breakdown_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Filters
        filter_layout = QHBoxLayout()

        # Field filter
        filter_layout.addWidget(QLabel("Field:"))
        self._field_filter = QComboBox()
        self._field_filter.addItem("All Fields", None)
        self._field_filter.currentIndexChanged.connect(self._load_operations)
        filter_layout.addWidget(self._field_filter)

        # Type filter
        filter_layout.addWidget(QLabel("Type:"))
        self._type_filter = QComboBox()
        self._type_filter.addItem("All Types", None)
        for value, label in OperationsAPI.OPERATION_TYPES:
            self._type_filter.addItem(label, value)
        self._type_filter.currentIndexChanged.connect(self._load_operations)
        filter_layout.addWidget(self._type_filter)

        # Date range
        filter_layout.addWidget(QLabel("From:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-6))
        self._date_from.dateChanged.connect(self._load_operations)
        filter_layout.addWidget(self._date_from)

        filter_layout.addWidget(QLabel("To:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.dateChanged.connect(self._load_operations)
        filter_layout.addWidget(self._date_to)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Operations table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Date", "Field", "Type", "Product", "Rate", "Cost", "Notes", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(7, 120)
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
        """Load fields, equipment, inventory and operations."""
        # Load fields for filter and dialog
        fields, _ = self._field_api.list_fields()
        self._fields = fields

        # Load equipment for dialog (Phase 4)
        equipment, _ = self._equipment_api.list_equipment(status="available")
        equipment_in_use, _ = self._equipment_api.list_equipment(status="in_use")
        self._equipment = equipment + equipment_in_use

        # Load inventory for dialog (Phase 4)
        inventory, _ = self._inventory_api.list_items()
        self._inventory = [item for item in inventory if item.quantity > 0]

        # Update field filter
        current_field = self._field_filter.currentData()
        self._field_filter.clear()
        self._field_filter.addItem("All Fields", None)
        for field in fields:
            display = f"{field.name} ({field.acreage:.1f} ac)"
            if field.farm_name:
                display = f"{field.farm_name} - {display}"
            self._field_filter.addItem(display, field.id)

        # Restore selection
        if current_field:
            for i in range(self._field_filter.count()):
                if self._field_filter.itemData(i) == current_field:
                    self._field_filter.setCurrentIndex(i)
                    break

        # Load operations and summary
        self._load_operations()
        self._load_summary()

    def _load_summary(self):
        """Load summary statistics."""
        field_id = self._field_filter.currentData()
        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        summary, error = self._ops_api.get_summary(
            field_id=field_id,
            date_from=date_from,
            date_to=date_to
        )

        if summary:
            self._total_ops_label.setText(str(summary.total_operations))
            self._total_cost_label.setText(f"${summary.total_cost:,.2f}")

            # Show top operation types
            if summary.operations_by_type:
                sorted_types = sorted(
                    summary.operations_by_type.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                type_text = ", ".join(
                    f"{t.replace('_', ' ').title()}: {c}"
                    for t, c in sorted_types
                )
                self._breakdown_label.setText(type_text)
            else:
                self._breakdown_label.setText("No operations")

    def _load_operations(self):
        """Load operations from API with current filters."""
        field_id = self._field_filter.currentData()
        operation_type = self._type_filter.currentData()
        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        operations, error = self._ops_api.list_operations(
            field_id=field_id,
            operation_type=operation_type,
            date_from=date_from,
            date_to=date_to
        )

        if error:
            self._status_label.setText(f"Error loading operations: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._operations = operations
        self._populate_table()
        self._status_label.setText(f"{len(operations)} operations found")
        self._status_label.setStyleSheet("color: #666;")

        # Also update summary
        self._load_summary()

    def _populate_table(self):
        """Populate the table with operation data."""
        self._table.setRowCount(len(self._operations))

        for row, op in enumerate(self._operations):
            # Date
            date_text = op.operation_date[:10] if op.operation_date else "-"
            self._table.setItem(row, 0, QTableWidgetItem(date_text))

            # Field
            field_text = op.field_name
            if op.farm_name:
                field_text = f"{op.farm_name} - {field_text}"
            self._table.setItem(row, 1, QTableWidgetItem(field_text))

            # Type (color-coded)
            type_item = QTableWidgetItem(op.operation_type_display)
            type_color = OPERATION_COLORS.get(op.operation_type, "#666")
            type_item.setForeground(QColor(type_color))
            self._table.setItem(row, 2, type_item)

            # Product
            self._table.setItem(row, 3, QTableWidgetItem(op.product_name or "-"))

            # Rate
            self._table.setItem(row, 4, QTableWidgetItem(op.rate_display))

            # Cost
            self._table.setItem(row, 5, QTableWidgetItem(op.cost_display))

            # Notes (truncated)
            notes_text = (op.notes[:30] + "...") if op.notes and len(op.notes) > 30 else (op.notes or "-")
            self._table.setItem(row, 6, QTableWidgetItem(notes_text))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            # View/Edit button
            view_btn = QPushButton("View")
            view_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            view_btn.clicked.connect(lambda checked, o=op: self._view_operation(o))
            actions_layout.addWidget(view_btn)

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
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #b71c1c;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, o=op: self._delete_operation(o))
                actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 7, actions_widget)

    def _show_log_dialog(self):
        """Show log operation dialog."""
        if not self._fields:
            QMessageBox.warning(
                self,
                "No Fields",
                "Please add fields before logging operations.\n\n"
                "Go to Field Management to add fields."
            )
            return

        dialog = LogOperationDialog(
            fields=self._fields,
            equipment=self._equipment,
            inventory=self._inventory,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            operation, error = self._ops_api.create_operation(**dialog.operation_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to log operation: {error}")
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    f"{operation.operation_type_display} logged successfully for {operation.field_name}"
                )
                self._load_data()

    def _view_operation(self, op: OperationInfo):
        """View operation details."""
        details = f"""
Operation Details
==================

Date: {op.operation_date}
Field: {op.field_name} ({op.farm_name or 'No farm'})
Type: {op.operation_type_display}

Product: {op.product_name or 'N/A'}
Rate: {op.rate_display}
Acres: {op.acres_covered or 'Field default'}

Costs:
  Product: {f'${op.product_cost:,.2f}' if op.product_cost else 'N/A'}
  Application: {f'${op.application_cost:,.2f}' if op.application_cost else 'N/A'}
  Total: {op.cost_display}
"""

        if op.operation_type == "harvest":
            details += f"""
Harvest Results:
  Yield: {op.yield_display}
  Moisture: {f'{op.moisture_percent}%' if op.moisture_percent else 'N/A'}
"""

        if op.weather_temp or op.weather_wind or op.weather_humidity:
            details += f"""
Weather:
  Temperature: {f'{op.weather_temp}F' if op.weather_temp else 'N/A'}
  Wind: {f'{op.weather_wind} mph' if op.weather_wind else 'N/A'}
  Humidity: {f'{op.weather_humidity}%' if op.weather_humidity else 'N/A'}
"""

        if op.notes:
            details += f"""
Notes: {op.notes}
"""

        details += f"""
Logged by: {op.created_by_user_name or 'Unknown'}
Logged on: {op.created_at[:10] if op.created_at else 'Unknown'}
"""

        QMessageBox.information(self, f"Operation #{op.id}", details)

    def _delete_operation(self, op: OperationInfo):
        """Delete an operation."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this {op.operation_type_display} "
            f"for {op.field_name} on {op.operation_date}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._ops_api.delete_operation(op.id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to delete operation: {error}")
            else:
                QMessageBox.information(self, "Success", "Operation deleted successfully")
                self._load_data()

    def refresh(self):
        """Refresh the operations list."""
        self._load_data()
