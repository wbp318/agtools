"""
Seed & Planting Management Screen

Provides UI for managing seed inventory, planting records, and emergence tracking.
AgTools v6.4.0 - Farm Operations Suite
"""

from datetime import date
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QDialog, QFormLayout, QGroupBox, QDateEdit,
    QDoubleSpinBox, QSpinBox, QTextEdit, QTabWidget, QMessageBox,
    QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from api.seed_planting_api import (
    get_seed_planting_api, SeedPlantingAPI, SeedInfo, PlantingInfo,
    EmergenceInfo, SeedPlantingSummary
)
from api.field_api import get_field_api, FieldAPI
from api.auth_api import UserInfo


# ============================================================================
# DIALOGS
# ============================================================================

class AddSeedDialog(QDialog):
    """Dialog for adding seed inventory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Seed Inventory")
        self.setMinimumWidth(500)
        self._api = get_seed_planting_api()
        self.seed_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Basic info
        basic_group = QGroupBox("Seed Information")
        basic_layout = QFormLayout()

        self._variety_input = QLineEdit()
        self._variety_input.setPlaceholderText("e.g., P1366AM, AG46X0")
        basic_layout.addRow("Variety Name*:", self._variety_input)

        self._crop_combo = QComboBox()
        for value, label in SeedPlantingAPI.CROP_TYPES:
            self._crop_combo.addItem(label, value)
        self._crop_combo.currentIndexChanged.connect(self._on_crop_changed)
        basic_layout.addRow("Crop Type*:", self._crop_combo)

        self._brand_combo = QComboBox()
        self._brand_combo.setEditable(True)
        self._brand_combo.addItems([
            "Pioneer", "DeKalb", "Asgrow", "Channel", "Golden Harvest",
            "NK", "Brevant", "LG Seeds", "Dyna-Gro", "Stine", "Beck's",
            "Wyffels", "AgriGold", "Croplan", "Other"
        ])
        basic_layout.addRow("Brand:", self._brand_combo)

        self._product_code = QLineEdit()
        self._product_code.setPlaceholderText("Product/SKU code")
        basic_layout.addRow("Product Code:", self._product_code)

        self._trait_combo = QComboBox()
        self._trait_combo.setEditable(True)
        basic_layout.addRow("Trait Package:", self._trait_combo)

        self._maturity_input = QLineEdit()
        self._maturity_input.setPlaceholderText("e.g., 2.5, 105 days")
        basic_layout.addRow("Relative Maturity:", self._maturity_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Inventory
        inv_group = QGroupBox("Inventory")
        inv_layout = QFormLayout()

        self._quantity = QDoubleSpinBox()
        self._quantity.setRange(0, 100000)
        self._quantity.setDecimals(1)
        inv_layout.addRow("Quantity On Hand:", self._quantity)

        self._unit_combo = QComboBox()
        for value, label in SeedPlantingAPI.QUANTITY_UNITS:
            self._unit_combo.addItem(label, value)
        inv_layout.addRow("Unit:", self._unit_combo)

        self._unit_cost = QDoubleSpinBox()
        self._unit_cost.setRange(0, 10000)
        self._unit_cost.setPrefix("$")
        self._unit_cost.setDecimals(2)
        inv_layout.addRow("Cost per Unit:", self._unit_cost)

        self._lot_number = QLineEdit()
        basic_layout.addRow("Lot Number:", self._lot_number)

        self._storage = QLineEdit()
        self._storage.setPlaceholderText("Bin, building, etc.")
        inv_layout.addRow("Storage Location:", self._storage)

        self._supplier = QLineEdit()
        inv_layout.addRow("Supplier:", self._supplier)

        self._germ_rate = QDoubleSpinBox()
        self._germ_rate.setRange(0, 100)
        self._germ_rate.setSuffix("%")
        self._germ_rate.setValue(95)
        inv_layout.addRow("Germination Rate:", self._germ_rate)

        inv_group.setLayout(inv_layout)
        layout.addWidget(inv_group)

        # Notes
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(60)
        self._notes.setPlaceholderText("Additional notes...")
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self._notes)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Add Seed")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Initialize traits
        self._on_crop_changed()

    def _on_crop_changed(self):
        """Update traits when crop changes."""
        crop = self._crop_combo.currentData()
        traits, _ = self._api.get_traits(crop)
        self._trait_combo.clear()
        self._trait_combo.addItems(traits if traits else ["Conventional", "Other"])

    def _save(self):
        variety = self._variety_input.text().strip()
        if not variety:
            QMessageBox.warning(self, "Validation Error", "Please enter a variety name.")
            return

        self.seed_data = {
            "variety_name": variety,
            "crop_type": self._crop_combo.currentData(),
            "brand": self._brand_combo.currentText() or None,
            "product_code": self._product_code.text().strip() or None,
            "trait_package": self._trait_combo.currentText() or None,
            "relative_maturity": self._maturity_input.text().strip() or None,
            "quantity_on_hand": self._quantity.value(),
            "quantity_units": self._unit_combo.currentData(),
            "unit_cost": self._unit_cost.value(),
            "lot_number": self._lot_number.text().strip() or None,
            "storage_location": self._storage.text().strip() or None,
            "supplier": self._supplier.text().strip() or None,
            "germination_rate": self._germ_rate.value() if self._germ_rate.value() > 0 else None,
            "notes": self._notes.toPlainText().strip() or None
        }
        self.accept()


class PlantingRecordDialog(QDialog):
    """Dialog for creating a planting record."""

    def __init__(self, seeds: List[SeedInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Planting Record")
        self.setMinimumWidth(550)
        self._seeds = seeds
        self._field_api = get_field_api()
        self.planting_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Field & Seed
        basic_group = QGroupBox("Field & Seed")
        basic_layout = QFormLayout()

        self._field_combo = QComboBox()
        fields, _ = self._field_api.list_fields()
        self._field_combo.addItem("-- Select Field --", None)
        for field in fields:
            self._field_combo.addItem(f"{field.name} ({field.acreage:.1f} ac)", field.id)
        basic_layout.addRow("Field*:", self._field_combo)

        self._seed_combo = QComboBox()
        self._seed_combo.addItem("-- Select Seed --", None)
        for seed in self._seeds:
            self._seed_combo.addItem(
                f"{seed.variety_name} ({seed.crop_display}) - {seed.quantity_display}",
                seed.id
            )
        basic_layout.addRow("Seed*:", self._seed_combo)

        self._planting_date = QDateEdit()
        self._planting_date.setCalendarPopup(True)
        self._planting_date.setDate(QDate.currentDate())
        self._planting_date.setDisplayFormat("MM/dd/yyyy")
        basic_layout.addRow("Planting Date*:", self._planting_date)

        self._acres = QDoubleSpinBox()
        self._acres.setRange(0.1, 100000)
        self._acres.setSuffix(" acres")
        self._acres.setDecimals(1)
        basic_layout.addRow("Acres Planted*:", self._acres)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Planting Details
        details_group = QGroupBox("Planting Details")
        details_layout = QFormLayout()

        self._rate = QDoubleSpinBox()
        self._rate.setRange(0, 500000)
        self._rate.setDecimals(0)
        self._rate.setValue(32000)
        details_layout.addRow("Planting Rate*:", self._rate)

        self._rate_unit = QComboBox()
        for value, label in SeedPlantingAPI.RATE_UNITS:
            self._rate_unit.addItem(label, value)
        details_layout.addRow("Rate Unit:", self._rate_unit)

        self._row_spacing = QDoubleSpinBox()
        self._row_spacing.setRange(0, 100)
        self._row_spacing.setSuffix(" inches")
        self._row_spacing.setValue(30)
        details_layout.addRow("Row Spacing:", self._row_spacing)

        self._depth = QDoubleSpinBox()
        self._depth.setRange(0, 10)
        self._depth.setSuffix(" inches")
        self._depth.setDecimals(2)
        self._depth.setValue(2.0)
        details_layout.addRow("Planting Depth:", self._depth)

        self._population = QSpinBox()
        self._population.setRange(0, 500000)
        self._population.setSuffix(" plants/ac")
        self._population.setValue(32000)
        details_layout.addRow("Population Target:", self._population)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Conditions
        cond_group = QGroupBox("Conditions")
        cond_layout = QFormLayout()

        self._soil_temp = QDoubleSpinBox()
        self._soil_temp.setRange(0, 120)
        self._soil_temp.setSuffix(" °F")
        cond_layout.addRow("Soil Temp:", self._soil_temp)

        self._moisture = QComboBox()
        self._moisture.addItem("-- Select --", None)
        for value, label in SeedPlantingAPI.SOIL_MOISTURE:
            self._moisture.addItem(label, value)
        cond_layout.addRow("Soil Moisture:", self._moisture)

        self._weather = QLineEdit()
        self._weather.setPlaceholderText("Sunny, cloudy, etc.")
        cond_layout.addRow("Weather:", self._weather)

        cond_group.setLayout(cond_layout)
        layout.addWidget(cond_group)

        # Notes
        self._notes = QTextEdit()
        self._notes.setMaximumHeight(50)
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self._notes)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Add Planting Record")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        field_id = self._field_combo.currentData()
        if not field_id:
            QMessageBox.warning(self, "Validation Error", "Please select a field.")
            return

        self.planting_data = {
            "field_id": field_id,
            "seed_inventory_id": self._seed_combo.currentData(),
            "planting_date": self._planting_date.date().toString("yyyy-MM-dd"),
            "acres_planted": self._acres.value(),
            "planting_rate": self._rate.value(),
            "rate_unit": self._rate_unit.currentData(),
            "row_spacing": self._row_spacing.value() if self._row_spacing.value() > 0 else None,
            "planting_depth": self._depth.value() if self._depth.value() > 0 else None,
            "population_target": self._population.value() if self._population.value() > 0 else None,
            "soil_temp": self._soil_temp.value() if self._soil_temp.value() > 0 else None,
            "soil_moisture": self._moisture.currentData(),
            "weather_conditions": self._weather.text().strip() or None,
            "notes": self._notes.toPlainText().strip() or None
        }
        self.accept()


class EmergenceCheckDialog(QDialog):
    """Dialog for recording emergence check."""

    def __init__(self, plantings: List[PlantingInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Emergence Check")
        self.setMinimumWidth(450)
        self._plantings = plantings
        self.emergence_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._planting_combo = QComboBox()
        self._planting_combo.addItem("-- Select Planting --", None)
        for p in self._plantings:
            self._planting_combo.addItem(
                f"{p.field_name or 'Field'} - {p.variety_name or 'Unknown'} ({p.planting_date})",
                p.id
            )
        form.addRow("Planting*:", self._planting_combo)

        self._check_date = QDateEdit()
        self._check_date.setCalendarPopup(True)
        self._check_date.setDate(QDate.currentDate())
        self._check_date.setDisplayFormat("MM/dd/yyyy")
        form.addRow("Check Date*:", self._check_date)

        self._stand_count = QSpinBox()
        self._stand_count.setRange(0, 10000)
        self._stand_count.setSuffix(" plants")
        form.addRow("Stand Count:", self._stand_count)

        self._count_area = QDoubleSpinBox()
        self._count_area.setRange(0, 1000)
        self._count_area.setValue(17.5)
        form.addRow("Count Area:", self._count_area)

        self._stand_pct = QDoubleSpinBox()
        self._stand_pct.setRange(0, 100)
        self._stand_pct.setSuffix("%")
        form.addRow("Stand Percentage:", self._stand_pct)

        self._uniformity = QSpinBox()
        self._uniformity.setRange(1, 5)
        self._uniformity.setValue(3)
        form.addRow("Uniformity (1-5):", self._uniformity)

        self._vigor = QSpinBox()
        self._vigor.setRange(1, 5)
        self._vigor.setValue(3)
        form.addRow("Vigor (1-5):", self._vigor)

        self._growth_stage = QLineEdit()
        self._growth_stage.setPlaceholderText("VE, V1, V2, etc.")
        form.addRow("Growth Stage:", self._growth_stage)

        self._issues = QLineEdit()
        self._issues.setPlaceholderText("Crusting, insects, etc.")
        form.addRow("Issues Noted:", self._issues)

        self._notes = QTextEdit()
        self._notes.setMaximumHeight(50)
        form.addRow("Notes:", self._notes)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Record Check")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        planting_id = self._planting_combo.currentData()
        if not planting_id:
            QMessageBox.warning(self, "Validation Error", "Please select a planting record.")
            return

        self.emergence_data = {
            "planting_record_id": planting_id,
            "check_date": self._check_date.date().toString("yyyy-MM-dd"),
            "stand_count": self._stand_count.value() if self._stand_count.value() > 0 else None,
            "count_area": self._count_area.value() if self._count_area.value() > 0 else None,
            "stand_percentage": self._stand_pct.value() if self._stand_pct.value() > 0 else None,
            "uniformity_score": self._uniformity.value(),
            "vigor_score": self._vigor.value(),
            "growth_stage": self._growth_stage.text().strip() or None,
            "issues_noted": self._issues.text().strip() or None,
            "notes": self._notes.toPlainText().strip() or None
        }
        self.accept()


# ============================================================================
# MAIN SCREEN
# ============================================================================

class SeedPlantingScreen(QWidget):
    """Main seed & planting management screen."""

    CROP_COLORS = {
        "corn": "#FFD700",
        "soybean": "#228B22",
        "wheat": "#DEB887",
        "cotton": "#F5F5F5",
        "rice": "#87CEEB",
        "sorghum": "#CD853F",
        "alfalfa": "#90EE90",
        "hay": "#F4A460"
    }

    def __init__(self, current_user: Optional[UserInfo] = None):
        super().__init__()
        self._current_user = current_user
        self._api = get_seed_planting_api()
        self._seeds: List[SeedInfo] = []
        self._plantings: List[PlantingInfo] = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Seed & Planting Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2e7d32;")
        layout.addWidget(title)

        # Summary cards
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(15)

        self._varieties_label = QLabel("0")
        summary_layout.addWidget(self._create_summary_card("Varieties", self._varieties_label))

        self._seed_value_label = QLabel("$0")
        summary_layout.addWidget(self._create_summary_card("Seed Value", self._seed_value_label))

        self._acres_label = QLabel("0")
        summary_layout.addWidget(self._create_summary_card("Acres Planted", self._acres_label))

        self._stand_label = QLabel("N/A")
        summary_layout.addWidget(self._create_summary_card("Avg Stand %", self._stand_label))

        layout.addLayout(summary_layout)

        # Toolbar
        toolbar = QHBoxLayout()

        self._crop_filter = QComboBox()
        self._crop_filter.addItem("All Crops", None)
        for value, label in SeedPlantingAPI.CROP_TYPES:
            self._crop_filter.addItem(label, value)
        self._crop_filter.currentIndexChanged.connect(self._load_data)
        toolbar.addWidget(QLabel("Crop:"))
        toolbar.addWidget(self._crop_filter)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search varieties...")
        self._search.textChanged.connect(self._load_data)
        toolbar.addWidget(self._search)

        self._in_stock = QCheckBox("In Stock Only")
        self._in_stock.stateChanged.connect(self._load_data)
        toolbar.addWidget(self._in_stock)

        toolbar.addStretch()

        add_seed_btn = QPushButton("+ Add Seed")
        add_seed_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        add_seed_btn.clicked.connect(self._show_add_seed_dialog)
        toolbar.addWidget(add_seed_btn)

        add_planting_btn = QPushButton("+ Add Planting")
        add_planting_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 8px 16px;")
        add_planting_btn.clicked.connect(self._show_add_planting_dialog)
        toolbar.addWidget(add_planting_btn)

        layout.addLayout(toolbar)

        # Tabs
        self._tabs = QTabWidget()

        # Seed Inventory Tab
        seed_widget = QWidget()
        seed_layout = QVBoxLayout(seed_widget)
        self._seed_table = QTableWidget()
        self._seed_table.setColumnCount(8)
        self._seed_table.setHorizontalHeaderLabels([
            "Variety", "Crop", "Brand", "Traits", "Qty", "Cost", "Value", "Actions"
        ])
        self._seed_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._seed_table.setAlternatingRowColors(True)
        seed_layout.addWidget(self._seed_table)
        self._tabs.addTab(seed_widget, "Seed Inventory")

        # Planting Records Tab
        planting_widget = QWidget()
        planting_layout = QVBoxLayout(planting_widget)
        self._planting_table = QTableWidget()
        self._planting_table.setColumnCount(8)
        self._planting_table.setHorizontalHeaderLabels([
            "Date", "Field", "Variety", "Acres", "Rate", "Status", "Stand %", "Actions"
        ])
        self._planting_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._planting_table.setAlternatingRowColors(True)
        planting_layout.addWidget(self._planting_table)
        self._tabs.addTab(planting_widget, "Planting Records")

        # Emergence Tab
        emergence_widget = QWidget()
        emergence_layout = QVBoxLayout(emergence_widget)

        emergence_toolbar = QHBoxLayout()
        add_emergence_btn = QPushButton("+ Record Emergence Check")
        add_emergence_btn.setStyleSheet("background-color: #7b1fa2; color: white; padding: 6px 12px;")
        add_emergence_btn.clicked.connect(self._show_emergence_dialog)
        emergence_toolbar.addWidget(add_emergence_btn)
        emergence_toolbar.addStretch()
        emergence_layout.addLayout(emergence_toolbar)

        self._emergence_table = QTableWidget()
        self._emergence_table.setColumnCount(8)
        self._emergence_table.setHorizontalHeaderLabels([
            "Date", "Field", "Variety", "DAP", "Stand %", "Uniformity", "Vigor", "Issues"
        ])
        self._emergence_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._emergence_table.setAlternatingRowColors(True)
        emergence_layout.addWidget(self._emergence_table)
        self._tabs.addTab(emergence_widget, "Emergence Checks")

        layout.addWidget(self._tabs)

        # Status bar
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self._status_label)

    def _create_summary_card(self, title: str, value_label: QLabel) -> QWidget:
        """Create a summary card widget."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        card_layout.addWidget(title_label)

        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2e7d32;")
        card_layout.addWidget(value_label)

        return card

    def _load_data(self):
        """Load all data."""
        self._load_summary()
        self._load_seeds()
        self._load_plantings()
        self._load_emergence()

    def _load_summary(self):
        """Load summary statistics."""
        summary, error = self._api.get_summary()
        if error:
            self._status_label.setText(f"Error: {error}")
            return

        if summary:
            self._varieties_label.setText(str(summary.total_varieties))
            self._seed_value_label.setText(f"${summary.total_seed_value:,.0f}")
            self._acres_label.setText(f"{summary.total_acres_planted:,.0f}")
            if summary.avg_stand_percentage:
                self._stand_label.setText(f"{summary.avg_stand_percentage:.0f}%")
            else:
                self._stand_label.setText("N/A")

    def _load_seeds(self):
        """Load seed inventory."""
        crop_type = self._crop_filter.currentData()
        search = self._search.text().strip() or None
        in_stock = self._in_stock.isChecked()

        self._seeds, error = self._api.list_seeds(
            crop_type=crop_type, search=search, in_stock_only=in_stock
        )

        if error:
            self._status_label.setText(f"Error: {error}")
            return

        self._seed_table.setRowCount(len(self._seeds))
        for row, seed in enumerate(self._seeds):
            self._seed_table.setItem(row, 0, QTableWidgetItem(seed.variety_name))

            crop_item = QTableWidgetItem(seed.crop_display)
            color = self.CROP_COLORS.get(seed.crop_type, "#666")
            crop_item.setBackground(QColor(color))
            self._seed_table.setItem(row, 1, crop_item)

            self._seed_table.setItem(row, 2, QTableWidgetItem(seed.brand or ""))
            self._seed_table.setItem(row, 3, QTableWidgetItem(seed.trait_package or ""))
            self._seed_table.setItem(row, 4, QTableWidgetItem(seed.quantity_display))
            self._seed_table.setItem(row, 5, QTableWidgetItem(f"${seed.unit_cost:,.2f}"))
            self._seed_table.setItem(row, 6, QTableWidgetItem(f"${seed.total_value:,.2f}"))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 2px 8px; font-size: 11px;")
            actions_layout.addWidget(edit_btn)

            if self._current_user and self._current_user.role in ("admin", "manager"):
                del_btn = QPushButton("Del")
                del_btn.setStyleSheet("background-color: #d32f2f; color: white; padding: 2px 8px; font-size: 11px;")
                del_btn.clicked.connect(lambda checked, s=seed: self._delete_seed(s))
                actions_layout.addWidget(del_btn)

            self._seed_table.setCellWidget(row, 7, actions_widget)

        self._status_label.setText(f"Loaded {len(self._seeds)} seed varieties")

    def _load_plantings(self):
        """Load planting records."""
        crop_type = self._crop_filter.currentData()
        self._plantings, error = self._api.list_plantings(crop_type=crop_type)

        if error:
            return

        self._planting_table.setRowCount(len(self._plantings))
        for row, p in enumerate(self._plantings):
            self._planting_table.setItem(row, 0, QTableWidgetItem(p.planting_date))
            self._planting_table.setItem(row, 1, QTableWidgetItem(p.field_name or ""))
            self._planting_table.setItem(row, 2, QTableWidgetItem(p.variety_name or ""))
            self._planting_table.setItem(row, 3, QTableWidgetItem(f"{p.acres_planted:,.1f}"))
            self._planting_table.setItem(row, 4, QTableWidgetItem(f"{p.planting_rate:,.0f}"))
            self._planting_table.setItem(row, 5, QTableWidgetItem(p.status_display))
            self._planting_table.setItem(row, 6, QTableWidgetItem(p.stand_display))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            view_btn = QPushButton("View")
            view_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 2px 8px; font-size: 11px;")
            actions_layout.addWidget(view_btn)

            self._planting_table.setCellWidget(row, 7, actions_widget)

    def _load_emergence(self):
        """Load all emergence checks (aggregate from all plantings)."""
        # For simplicity, show recent emergence for current plantings
        self._emergence_table.setRowCount(0)
        all_records = []

        for p in self._plantings[:20]:  # Limit to recent plantings
            records, _ = self._api.list_emergence(p.id)
            for r in records:
                r.field_name = p.field_name
                r.variety_name = p.variety_name
                all_records.append(r)

        # Sort by date descending
        all_records.sort(key=lambda x: x.check_date, reverse=True)

        self._emergence_table.setRowCount(len(all_records[:50]))  # Limit display
        for row, e in enumerate(all_records[:50]):
            self._emergence_table.setItem(row, 0, QTableWidgetItem(e.check_date))
            self._emergence_table.setItem(row, 1, QTableWidgetItem(e.field_name or ""))
            self._emergence_table.setItem(row, 2, QTableWidgetItem(e.variety_name or ""))
            self._emergence_table.setItem(row, 3, QTableWidgetItem(str(e.days_after_planting or "")))
            self._emergence_table.setItem(row, 4, QTableWidgetItem(e.stand_display))
            self._emergence_table.setItem(row, 5, QTableWidgetItem(str(e.uniformity_score or "")))
            self._emergence_table.setItem(row, 6, QTableWidgetItem(str(e.vigor_score or "")))
            self._emergence_table.setItem(row, 7, QTableWidgetItem(e.issues_noted or ""))

    def _show_add_seed_dialog(self):
        """Show dialog to add seed."""
        dialog = AddSeedDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.seed_data:
            seed, error = self._api.create_seed(**dialog.seed_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to add seed: {error}")
            else:
                self._status_label.setText("Seed added successfully")
                self._load_data()

    def _show_add_planting_dialog(self):
        """Show dialog to add planting record."""
        dialog = PlantingRecordDialog(self._seeds, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.planting_data:
            planting, error = self._api.create_planting(**dialog.planting_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to add planting: {error}")
            else:
                self._status_label.setText("Planting record added successfully")
                self._load_data()

    def _show_emergence_dialog(self):
        """Show dialog to record emergence check."""
        dialog = EmergenceCheckDialog(self._plantings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.emergence_data:
            record, error = self._api.create_emergence(**dialog.emergence_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to record emergence: {error}")
            else:
                self._status_label.setText("Emergence check recorded")
                self._load_data()

    def _delete_seed(self, seed: SeedInfo):
        """Delete a seed inventory item."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {seed.variety_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._api.delete_seed(seed.id)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to delete: {error}")
            else:
                self._status_label.setText("Seed deleted")
                self._load_data()
