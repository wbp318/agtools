"""
Inventory Management Screen

Screen for managing farm inventory - seeds, fertilizers, chemicals, parts, etc.
AgTools v2.5.0 Phase 4
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QTextEdit, QDoubleSpinBox, QGroupBox,
    QDateEdit, QCheckBox
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.inventory_api import (
    get_inventory_api, InventoryAPI, InventoryItem
)
from api.auth_api import UserInfo


# Category colors for visual identification
CATEGORY_COLORS = {
    "seed": "#4caf50",           # Green
    "fertilizer": "#ff9800",     # Orange
    "herbicide": "#f44336",      # Red
    "fungicide": "#9c27b0",      # Purple
    "insecticide": "#e91e63",    # Pink
    "adjuvant": "#00bcd4",       # Cyan
    "fuel": "#795548",           # Brown
    "parts": "#607d8b",          # Gray-blue
    "supplies": "#9e9e9e",       # Gray
    "other": "#757575",          # Dark gray
}

# Alert type colors
ALERT_COLORS = {
    "expired": "#d32f2f",
    "low_stock": "#ff9800",
    "expiring": "#ffc107",
}


class CreateItemDialog(QDialog):
    """Dialog for creating new inventory item."""

    def __init__(self, storage_locations: list = None, parent=None):
        super().__init__(parent)
        self.storage_locations = storage_locations or []
        self.setWindowTitle("Add Inventory Item")
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
        self._name_input.setPlaceholderText("e.g., Roundup PowerMax, NK Seed Corn")
        basic_layout.addRow("Item Name:", self._name_input)

        # Category
        self._category_combo = QComboBox()
        for value, label in InventoryAPI.CATEGORIES:
            self._category_combo.addItem(label, value)
        basic_layout.addRow("Category:", self._category_combo)

        # Manufacturer
        self._manufacturer_input = QLineEdit()
        self._manufacturer_input.setPlaceholderText("e.g., Bayer, Syngenta")
        basic_layout.addRow("Manufacturer:", self._manufacturer_input)

        # Product Code
        self._product_code_input = QLineEdit()
        self._product_code_input.setPlaceholderText("Optional")
        basic_layout.addRow("Product Code:", self._product_code_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Quantity Group
        qty_group = QGroupBox("Quantity & Units")
        qty_layout = QFormLayout()
        qty_layout.setSpacing(10)

        # Quantity
        self._quantity_input = QDoubleSpinBox()
        self._quantity_input.setRange(0, 1000000)
        self._quantity_input.setDecimals(2)
        qty_layout.addRow("Quantity:", self._quantity_input)

        # Unit
        self._unit_combo = QComboBox()
        self._unit_combo.setEditable(True)
        for unit in InventoryAPI.UNITS:
            self._unit_combo.addItem(unit)
        qty_layout.addRow("Unit:", self._unit_combo)

        # Min Quantity (reorder point)
        self._min_qty_input = QDoubleSpinBox()
        self._min_qty_input.setRange(0, 100000)
        self._min_qty_input.setDecimals(2)
        self._min_qty_input.setSpecialValueText("Not set")
        qty_layout.addRow("Reorder Point:", self._min_qty_input)

        qty_group.setLayout(qty_layout)
        layout.addWidget(qty_group)

        # Storage & Tracking Group
        storage_group = QGroupBox("Storage & Tracking")
        storage_layout = QFormLayout()
        storage_layout.setSpacing(10)

        # Storage Location
        self._location_combo = QComboBox()
        self._location_combo.setEditable(True)
        self._location_combo.addItem("")
        for loc in self.storage_locations:
            self._location_combo.addItem(loc)
        self._location_combo.setPlaceholderText("e.g., Chemical Shed, Main Barn")
        storage_layout.addRow("Storage Location:", self._location_combo)

        # Batch Number
        self._batch_input = QLineEdit()
        self._batch_input.setPlaceholderText("Optional lot/batch number")
        storage_layout.addRow("Batch/Lot Number:", self._batch_input)

        # Expiration Date
        self._expiration_check = QCheckBox("Has expiration date")
        self._expiration_date = QDateEdit()
        self._expiration_date.setDate(QDate.currentDate().addYears(1))
        self._expiration_date.setCalendarPopup(True)
        self._expiration_date.setEnabled(False)
        self._expiration_check.toggled.connect(self._expiration_date.setEnabled)
        storage_layout.addRow("", self._expiration_check)
        storage_layout.addRow("Expiration Date:", self._expiration_date)

        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)

        # Cost Group
        cost_group = QGroupBox("Cost")
        cost_layout = QFormLayout()
        cost_layout.setSpacing(10)

        self._unit_cost_input = QDoubleSpinBox()
        self._unit_cost_input.setRange(0, 100000)
        self._unit_cost_input.setDecimals(2)
        self._unit_cost_input.setPrefix("$")
        self._unit_cost_input.setSuffix(" per unit")
        cost_layout.addRow("Unit Cost:", self._unit_cost_input)

        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setPlaceholderText("Additional notes...")
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Add Item")
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
        create_btn.clicked.connect(self._create_item)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _create_item(self):
        """Validate and prepare item data."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Item name is required")
            return

        unit = self._unit_combo.currentText().strip()
        if not unit:
            QMessageBox.warning(self, "Validation Error", "Unit is required")
            return

        expiration = None
        if self._expiration_check.isChecked():
            expiration = self._expiration_date.date().toString("yyyy-MM-dd")

        self.item_data = {
            "name": name,
            "category": self._category_combo.currentData(),
            "unit": unit,
            "quantity": self._quantity_input.value(),
            "manufacturer": self._manufacturer_input.text().strip() or None,
            "product_code": self._product_code_input.text().strip() or None,
            "min_quantity": self._min_qty_input.value() or None,
            "storage_location": self._location_combo.currentText().strip() or None,
            "batch_number": self._batch_input.text().strip() or None,
            "expiration_date": expiration,
            "unit_cost": self._unit_cost_input.value() or None,
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class EditItemDialog(QDialog):
    """Dialog for editing inventory item."""

    def __init__(self, item: InventoryItem, storage_locations: list = None, parent=None):
        super().__init__(parent)
        self.item = item
        self.storage_locations = storage_locations or []
        self.setWindowTitle(f"Edit Item: {item.name}")
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
        self._name_input = QLineEdit(self.item.name)
        basic_layout.addRow("Item Name:", self._name_input)

        # Category
        self._category_combo = QComboBox()
        cat_idx = 0
        for idx, (value, label) in enumerate(InventoryAPI.CATEGORIES):
            self._category_combo.addItem(label, value)
            if value == self.item.category:
                cat_idx = idx
        self._category_combo.setCurrentIndex(cat_idx)
        basic_layout.addRow("Category:", self._category_combo)

        # Manufacturer
        self._manufacturer_input = QLineEdit(self.item.manufacturer or "")
        basic_layout.addRow("Manufacturer:", self._manufacturer_input)

        # Product Code
        self._product_code_input = QLineEdit(self.item.product_code or "")
        basic_layout.addRow("Product Code:", self._product_code_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Quantity Group
        qty_group = QGroupBox("Quantity & Units")
        qty_layout = QFormLayout()
        qty_layout.setSpacing(10)

        # Current Quantity (display only)
        qty_label = QLabel(self.item.quantity_display)
        qty_label.setStyleSheet("font-weight: bold;")
        qty_layout.addRow("Current Quantity:", qty_label)

        # Unit
        self._unit_combo = QComboBox()
        self._unit_combo.setEditable(True)
        for unit in InventoryAPI.UNITS:
            self._unit_combo.addItem(unit)
        self._unit_combo.setCurrentText(self.item.unit)
        qty_layout.addRow("Unit:", self._unit_combo)

        # Min Quantity
        self._min_qty_input = QDoubleSpinBox()
        self._min_qty_input.setRange(0, 100000)
        self._min_qty_input.setDecimals(2)
        self._min_qty_input.setSpecialValueText("Not set")
        self._min_qty_input.setValue(self.item.min_quantity or 0)
        qty_layout.addRow("Reorder Point:", self._min_qty_input)

        qty_group.setLayout(qty_layout)
        layout.addWidget(qty_group)

        # Storage Group
        storage_group = QGroupBox("Storage & Tracking")
        storage_layout = QFormLayout()
        storage_layout.setSpacing(10)

        # Storage Location
        self._location_combo = QComboBox()
        self._location_combo.setEditable(True)
        self._location_combo.addItem("")
        for loc in self.storage_locations:
            self._location_combo.addItem(loc)
        if self.item.storage_location:
            self._location_combo.setCurrentText(self.item.storage_location)
        storage_layout.addRow("Storage Location:", self._location_combo)

        # Batch Number
        self._batch_input = QLineEdit(self.item.batch_number or "")
        storage_layout.addRow("Batch/Lot Number:", self._batch_input)

        # Expiration Date
        self._expiration_check = QCheckBox("Has expiration date")
        self._expiration_date = QDateEdit()
        self._expiration_date.setCalendarPopup(True)
        if self.item.expiration_date:
            self._expiration_check.setChecked(True)
            self._expiration_date.setDate(QDate.fromString(self.item.expiration_date[:10], "yyyy-MM-dd"))
            self._expiration_date.setEnabled(True)
        else:
            self._expiration_date.setDate(QDate.currentDate().addYears(1))
            self._expiration_date.setEnabled(False)
        self._expiration_check.toggled.connect(self._expiration_date.setEnabled)
        storage_layout.addRow("", self._expiration_check)
        storage_layout.addRow("Expiration Date:", self._expiration_date)

        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)

        # Cost Group
        cost_group = QGroupBox("Cost")
        cost_layout = QFormLayout()
        cost_layout.setSpacing(10)

        self._unit_cost_input = QDoubleSpinBox()
        self._unit_cost_input.setRange(0, 100000)
        self._unit_cost_input.setDecimals(2)
        self._unit_cost_input.setPrefix("$")
        self._unit_cost_input.setSuffix(" per unit")
        self._unit_cost_input.setValue(self.item.unit_cost or 0)
        cost_layout.addRow("Unit Cost:", self._unit_cost_input)

        # Total value display
        value_label = QLabel(self.item.value_display)
        value_label.setStyleSheet("font-weight: bold; color: #1976d2;")
        cost_layout.addRow("Total Value:", value_label)

        cost_group.setLayout(cost_layout)
        layout.addWidget(cost_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setText(self.item.notes or "")
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
        save_btn.clicked.connect(self._save_item)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_item(self):
        """Validate and prepare item data."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Item name is required")
            return

        expiration = None
        if self._expiration_check.isChecked():
            expiration = self._expiration_date.date().toString("yyyy-MM-dd")

        self.item_data = {
            "name": name,
            "category": self._category_combo.currentData(),
            "unit": self._unit_combo.currentText().strip(),
            "manufacturer": self._manufacturer_input.text().strip() or None,
            "product_code": self._product_code_input.text().strip() or None,
            "min_quantity": self._min_qty_input.value() or None,
            "storage_location": self._location_combo.currentText().strip() or None,
            "batch_number": self._batch_input.text().strip() or None,
            "expiration_date": expiration,
            "unit_cost": self._unit_cost_input.value() or None,
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class QuickPurchaseDialog(QDialog):
    """Dialog for quick purchase/add quantity."""

    def __init__(self, item: InventoryItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"Add Purchase: {item.name}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Item Info
        info_label = QLabel(f"<b>{self.item.name}</b><br>"
                           f"Current: {self.item.quantity_display}")
        layout.addWidget(info_label)

        # Purchase Details
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Quantity
        self._quantity_input = QDoubleSpinBox()
        self._quantity_input.setRange(0.01, 100000)
        self._quantity_input.setDecimals(2)
        self._quantity_input.setSuffix(f" {self.item.unit}")
        self._quantity_input.setValue(1)
        form_layout.addRow("Quantity Purchased:", self._quantity_input)

        # Unit Cost
        self._unit_cost_input = QDoubleSpinBox()
        self._unit_cost_input.setRange(0, 100000)
        self._unit_cost_input.setDecimals(2)
        self._unit_cost_input.setPrefix("$")
        self._unit_cost_input.setValue(self.item.unit_cost or 0)
        form_layout.addRow("Unit Cost:", self._unit_cost_input)

        # Vendor
        self._vendor_input = QLineEdit()
        self._vendor_input.setPlaceholderText("e.g., Local Co-op, Helena")
        form_layout.addRow("Vendor:", self._vendor_input)

        # Invoice
        self._invoice_input = QLineEdit()
        self._invoice_input.setPlaceholderText("Optional invoice number")
        form_layout.addRow("Invoice #:", self._invoice_input)

        layout.addLayout(form_layout)

        # Notes
        self._notes_input = QLineEdit()
        self._notes_input.setPlaceholderText("Optional notes")
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self._notes_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        add_btn = QPushButton("Add Purchase")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self._add_purchase)
        button_layout.addWidget(add_btn)

        layout.addLayout(button_layout)

    def _add_purchase(self):
        """Prepare purchase data."""
        quantity = self._quantity_input.value()
        if quantity <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than 0")
            return

        self.purchase_data = {
            "inventory_item_id": self.item.id,
            "quantity": quantity,
            "unit_cost": self._unit_cost_input.value() or None,
            "vendor": self._vendor_input.text().strip() or None,
            "invoice_number": self._invoice_input.text().strip() or None,
            "notes": self._notes_input.text().strip() or None
        }
        self.accept()


class AdjustQuantityDialog(QDialog):
    """Dialog for adjusting inventory quantity."""

    def __init__(self, item: InventoryItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"Adjust Quantity: {item.name}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Item Info
        info_label = QLabel(f"<b>{self.item.name}</b><br>"
                           f"Category: {self.item.category_display}")
        layout.addWidget(info_label)

        # Current quantity
        current_label = QLabel(f"Current Quantity: <b>{self.item.quantity_display}</b>")
        current_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(current_label)

        # New quantity
        form_layout = QFormLayout()

        self._new_qty_input = QDoubleSpinBox()
        self._new_qty_input.setRange(0, 1000000)
        self._new_qty_input.setDecimals(2)
        self._new_qty_input.setSuffix(f" {self.item.unit}")
        self._new_qty_input.setValue(self.item.quantity)
        form_layout.addRow("New Quantity:", self._new_qty_input)

        self._reason_input = QLineEdit()
        self._reason_input.setPlaceholderText("e.g., Physical count, spillage, theft")
        form_layout.addRow("Reason:", self._reason_input)

        layout.addLayout(form_layout)

        # Difference preview
        self._diff_label = QLabel("")
        self._diff_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._diff_label)
        self._new_qty_input.valueChanged.connect(self._update_diff)
        self._update_diff()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        adjust_btn = QPushButton("Adjust Quantity")
        adjust_btn.setStyleSheet("""
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
        adjust_btn.clicked.connect(self._adjust)
        button_layout.addWidget(adjust_btn)

        layout.addLayout(button_layout)

    def _update_diff(self):
        """Update difference preview."""
        new_qty = self._new_qty_input.value()
        diff = new_qty - self.item.quantity
        if diff > 0:
            self._diff_label.setText(f"Change: +{diff:,.2f} {self.item.unit}")
            self._diff_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        elif diff < 0:
            self._diff_label.setText(f"Change: {diff:,.2f} {self.item.unit}")
            self._diff_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        else:
            self._diff_label.setText("No change")
            self._diff_label.setStyleSheet("font-weight: bold; color: #666;")

    def _adjust(self):
        """Prepare adjustment data."""
        self.adjust_data = {
            "inventory_item_id": self.item.id,
            "new_quantity": self._new_qty_input.value(),
            "reason": self._reason_input.text().strip() or None
        }
        self.accept()


class InventoryManagementScreen(QWidget):
    """
    Inventory management screen for Farm Operations Manager.

    Features:
    - List inventory items with filters (category, location, search)
    - Create new items
    - Edit existing items
    - Quick purchase (add quantity)
    - Adjust quantity (counts/corrections)
    - View alerts (low stock, expiring)
    - Delete items (manager/admin only)
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._inventory_api = get_inventory_api()
        self._items: list[InventoryItem] = []
        self._storage_locations: list[str] = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user after login."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the inventory management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Inventory Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add item button
        add_btn = QPushButton("+ Add Item")
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

        self._total_items_label = QLabel("0")
        self._total_items_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        items_card = self._create_summary_card("Total Items", self._total_items_label)
        summary_layout.addWidget(items_card)

        self._total_value_label = QLabel("$0")
        self._total_value_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
            }
        """)
        value_card = self._create_summary_card("Inventory Value", self._total_value_label)
        summary_layout.addWidget(value_card)

        self._low_stock_label = QLabel("0")
        self._low_stock_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ff9800;
            }
        """)
        low_card = self._create_summary_card("Low Stock", self._low_stock_label)
        summary_layout.addWidget(low_card)

        self._expiring_label = QLabel("0")
        self._expiring_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #d32f2f;
            }
        """)
        exp_card = self._create_summary_card("Expiring Soon", self._expiring_label)
        summary_layout.addWidget(exp_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Filters
        filter_layout = QHBoxLayout()

        # Category filter
        filter_layout.addWidget(QLabel("Category:"))
        self._category_filter = QComboBox()
        self._category_filter.addItem("All Categories", None)
        for value, label in InventoryAPI.CATEGORIES:
            self._category_filter.addItem(label, value)
        self._category_filter.currentIndexChanged.connect(self._load_items)
        filter_layout.addWidget(self._category_filter)

        # Location filter
        filter_layout.addWidget(QLabel("Location:"))
        self._location_filter = QComboBox()
        self._location_filter.addItem("All Locations")
        self._location_filter.currentIndexChanged.connect(self._load_items)
        filter_layout.addWidget(self._location_filter)

        # Low stock filter
        self._low_stock_check = QCheckBox("Low Stock Only")
        self._low_stock_check.toggled.connect(self._load_items)
        filter_layout.addWidget(self._low_stock_check)

        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search items...")
        self._search_input.textChanged.connect(self._load_items)
        filter_layout.addWidget(self._search_input)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Inventory table
        self._table = QTableWidget()
        self._table.setColumnCount(9)
        self._table.setHorizontalHeaderLabels([
            "Item Name", "Category", "Quantity", "Unit Cost",
            "Total Value", "Location", "Expiration", "Status", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(8, 260)
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
        """Load inventory data and update UI."""
        # Load storage locations for filters and dialogs
        locations, _ = self._inventory_api.get_storage_locations()
        self._storage_locations = locations

        # Update location filter
        current_loc = self._location_filter.currentText()
        self._location_filter.clear()
        self._location_filter.addItem("All Locations")
        for loc in locations:
            self._location_filter.addItem(loc)
        if current_loc in locations:
            self._location_filter.setCurrentText(current_loc)

        # Load items and summary
        self._load_items()
        self._load_summary()

    def _load_summary(self):
        """Load summary statistics."""
        summary, error = self._inventory_api.get_summary()
        if summary:
            self._total_items_label.setText(str(summary.total_items))
            self._total_value_label.setText(f"${summary.total_value:,.0f}")
            self._low_stock_label.setText(str(summary.low_stock_count))
            self._expiring_label.setText(str(summary.expiring_soon_count))

    def _load_items(self):
        """Load inventory items from API with current filters."""
        category = self._category_filter.currentData()

        storage_location = None
        if self._location_filter.currentIndex() > 0:
            storage_location = self._location_filter.currentText()

        search = self._search_input.text().strip() or None
        low_stock_only = self._low_stock_check.isChecked()

        items, error = self._inventory_api.list_items(
            category=category,
            storage_location=storage_location,
            search=search,
            low_stock_only=low_stock_only
        )

        if error:
            self._status_label.setText(f"Error loading inventory: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._items = items
        self._populate_table()
        self._status_label.setText(f"{len(items)} items found")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_table(self):
        """Populate the table with inventory data."""
        self._table.setRowCount(len(self._items))

        for row, item in enumerate(self._items):
            # Item Name
            name_item = QTableWidgetItem(item.name)
            name_item.setFont(QFont("Arial", -1, QFont.Weight.Bold))
            self._table.setItem(row, 0, name_item)

            # Category (color-coded)
            cat_item = QTableWidgetItem(item.category_display)
            cat_color = CATEGORY_COLORS.get(item.category, "#666")
            cat_item.setForeground(QColor(cat_color))
            self._table.setItem(row, 1, cat_item)

            # Quantity
            qty_item = QTableWidgetItem(item.quantity_display)
            if item.is_low_stock:
                qty_item.setForeground(QColor("#ff9800"))
            self._table.setItem(row, 2, qty_item)

            # Unit Cost
            self._table.setItem(row, 3, QTableWidgetItem(item.unit_cost_display))

            # Total Value
            self._table.setItem(row, 4, QTableWidgetItem(item.value_display))

            # Location
            self._table.setItem(row, 5, QTableWidgetItem(item.storage_location or "-"))

            # Expiration
            exp_item = QTableWidgetItem(item.expiry_status)
            if item.is_expiring_soon:
                exp_item.setForeground(QColor("#d32f2f"))
            self._table.setItem(row, 6, exp_item)

            # Status
            status_item = QTableWidgetItem(item.stock_status)
            if item.is_low_stock:
                status_item.setForeground(QColor("#ff9800"))
            else:
                status_item.setForeground(QColor("#2e7d32"))
            self._table.setItem(row, 7, status_item)

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
            edit_btn.clicked.connect(lambda checked, i=item: self._show_edit_dialog(i))
            actions_layout.addWidget(edit_btn)

            # Purchase button
            buy_btn = QPushButton("Buy")
            buy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #1b5e20;
                }
            """)
            buy_btn.clicked.connect(lambda checked, i=item: self._show_purchase_dialog(i))
            actions_layout.addWidget(buy_btn)

            # Adjust button
            adjust_btn = QPushButton("Adjust")
            adjust_btn.setStyleSheet("""
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
            adjust_btn.clicked.connect(lambda checked, i=item: self._show_adjust_dialog(i))
            actions_layout.addWidget(adjust_btn)

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
                delete_btn.clicked.connect(lambda checked, i=item: self._delete_item(i))
                actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 8, actions_widget)

    def _show_create_dialog(self):
        """Show create item dialog."""
        dialog = CreateItemDialog(
            storage_locations=self._storage_locations,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item, error = self._inventory_api.create_item(**dialog.item_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to create item: {error}")
            else:
                QMessageBox.information(self, "Success",
                                       f"Item '{item.name}' added successfully")
                self._load_data()

    def _show_edit_dialog(self, item: InventoryItem):
        """Show edit item dialog."""
        dialog = EditItemDialog(
            item=item,
            storage_locations=self._storage_locations,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated, error = self._inventory_api.update_item(
                item.id, **dialog.item_data
            )
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update item: {error}")
            else:
                QMessageBox.information(self, "Success", "Item updated successfully")
                self._load_data()

    def _show_purchase_dialog(self, item: InventoryItem):
        """Show quick purchase dialog."""
        dialog = QuickPurchaseDialog(item=item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated, error = self._inventory_api.quick_purchase(**dialog.purchase_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to record purchase: {error}")
            else:
                QMessageBox.information(self, "Success",
                                       f"Added {dialog.purchase_data['quantity']:.2f} {item.unit}")
                self._load_data()

    def _show_adjust_dialog(self, item: InventoryItem):
        """Show adjust quantity dialog."""
        dialog = AdjustQuantityDialog(item=item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated, error = self._inventory_api.adjust_quantity(**dialog.adjust_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to adjust quantity: {error}")
            else:
                QMessageBox.information(self, "Success", "Quantity adjusted successfully")
                self._load_data()

    def _delete_item(self, item: InventoryItem):
        """Delete inventory item."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{item.name}'?\n\n"
            f"Quantity: {item.quantity_display}\n"
            f"Value: {item.value_display}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._inventory_api.delete_item(item.id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to delete item: {error}")
            else:
                QMessageBox.information(self, "Success", "Item deleted successfully")
                self._load_data()

    def refresh(self):
        """Refresh the inventory list."""
        self._load_data()
