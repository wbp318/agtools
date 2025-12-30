"""
Livestock Management Screen

Provides UI for managing livestock animals, groups, health records, breeding, weights, and sales.
AgTools v6.4.0 - Farm Operations Suite
"""

from datetime import date
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QDialog, QFormLayout, QGroupBox, QDateEdit,
    QDoubleSpinBox, QSpinBox, QTextEdit, QTabWidget, QMessageBox,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from api.livestock_api import (
    get_livestock_api, LivestockAPI, AnimalInfo, GroupInfo,
    HealthRecordInfo, BreedingRecordInfo, WeightRecordInfo, SaleRecordInfo,
    LivestockSummary
)
from api.auth_api import UserInfo


# ============================================================================
# DIALOGS
# ============================================================================

class AddAnimalDialog(QDialog):
    """Dialog for adding a new animal."""

    def __init__(self, groups: List[GroupInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Animal")
        self.setMinimumWidth(500)
        self._groups = groups
        self._api = get_livestock_api()
        self.animal_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Basic info group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()

        self._species_combo = QComboBox()
        for value, label in LivestockAPI.SPECIES_TYPES:
            self._species_combo.addItem(label, value)
        self._species_combo.currentIndexChanged.connect(self._on_species_changed)
        basic_layout.addRow("Species*:", self._species_combo)

        self._tag_input = QLineEdit()
        self._tag_input.setPlaceholderText("e.g., 123, A-45")
        basic_layout.addRow("Tag Number:", self._tag_input)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Optional name")
        basic_layout.addRow("Name:", self._name_input)

        self._breed_combo = QComboBox()
        self._breed_combo.setEditable(True)
        basic_layout.addRow("Breed:", self._breed_combo)

        self._sex_combo = QComboBox()
        for value, label in LivestockAPI.SEX_TYPES:
            self._sex_combo.addItem(label, value)
        basic_layout.addRow("Sex:", self._sex_combo)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Details group
        details_group = QGroupBox("Details")
        details_layout = QFormLayout()

        self._birth_date = QDateEdit()
        self._birth_date.setCalendarPopup(True)
        self._birth_date.setDate(QDate.currentDate())
        self._birth_date.setDisplayFormat("MM/dd/yyyy")
        details_layout.addRow("Birth Date:", self._birth_date)

        self._purchase_date = QDateEdit()
        self._purchase_date.setCalendarPopup(True)
        self._purchase_date.setDate(QDate.currentDate())
        self._purchase_date.setDisplayFormat("MM/dd/yyyy")
        details_layout.addRow("Purchase Date:", self._purchase_date)

        self._purchase_price = QDoubleSpinBox()
        self._purchase_price.setRange(0, 1000000)
        self._purchase_price.setPrefix("$")
        self._purchase_price.setDecimals(2)
        details_layout.addRow("Purchase Price:", self._purchase_price)

        self._weight_input = QDoubleSpinBox()
        self._weight_input.setRange(0, 10000)
        self._weight_input.setSuffix(" lbs")
        self._weight_input.setDecimals(1)
        details_layout.addRow("Current Weight:", self._weight_input)

        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("Pasture, barn, pen, etc.")
        details_layout.addRow("Location:", self._location_input)

        self._group_combo = QComboBox()
        self._group_combo.addItem("-- No Group --", None)
        for group in self._groups:
            self._group_combo.addItem(f"{group.group_name} ({group.species_display})", group.id)
        details_layout.addRow("Group:", self._group_combo)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(80)
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Add Animal")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save_animal)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        # Load breeds for initial species
        self._on_species_changed()

    def _on_species_changed(self):
        """Update breeds when species changes."""
        species = self._species_combo.currentData()
        breeds, _ = self._api.get_breeds(species)
        self._breed_combo.clear()
        self._breed_combo.addItems(breeds if breeds else ["Other"])

    def _save_animal(self):
        """Save the animal."""
        species = self._species_combo.currentData()
        if not species:
            QMessageBox.warning(self, "Validation Error", "Please select a species.")
            return

        self.animal_data = {
            "species": species,
            "tag_number": self._tag_input.text().strip() or None,
            "name": self._name_input.text().strip() or None,
            "breed": self._breed_combo.currentText() or None,
            "sex": self._sex_combo.currentData(),
            "birth_date": self._birth_date.date().toString("yyyy-MM-dd"),
            "purchase_date": self._purchase_date.date().toString("yyyy-MM-dd"),
            "purchase_price": self._purchase_price.value(),
            "current_weight": self._weight_input.value() if self._weight_input.value() > 0 else None,
            "current_location": self._location_input.text().strip() or None,
            "group_id": self._group_combo.currentData(),
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class AddGroupDialog(QDialog):
    """Dialog for adding a new livestock group."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Livestock Group")
        self.setMinimumWidth(450)
        self.group_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., Spring 2025 Calves")
        form_layout.addRow("Group Name*:", self._name_input)

        self._species_combo = QComboBox()
        for value, label in LivestockAPI.SPECIES_TYPES:
            self._species_combo.addItem(label, value)
        form_layout.addRow("Species*:", self._species_combo)

        self._head_count = QSpinBox()
        self._head_count.setRange(0, 100000)
        form_layout.addRow("Head Count:", self._head_count)

        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDate(QDate.currentDate())
        self._start_date.setDisplayFormat("MM/dd/yyyy")
        form_layout.addRow("Start Date:", self._start_date)

        self._source_input = QLineEdit()
        self._source_input.setPlaceholderText("e.g., XYZ Ranch, Local Auction")
        form_layout.addRow("Source:", self._source_input)

        self._cost_per_head = QDoubleSpinBox()
        self._cost_per_head.setRange(0, 100000)
        self._cost_per_head.setPrefix("$")
        self._cost_per_head.setDecimals(2)
        form_layout.addRow("Cost/Head:", self._cost_per_head)

        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("Barn, pasture, etc.")
        form_layout.addRow("Location:", self._location_input)

        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        form_layout.addRow("Notes:", self._notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Add Group")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save_group)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_group(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a group name.")
            return

        self.group_data = {
            "group_name": name,
            "species": self._species_combo.currentData(),
            "head_count": self._head_count.value(),
            "start_date": self._start_date.date().toString("yyyy-MM-dd"),
            "source": self._source_input.text().strip() or None,
            "cost_per_head": self._cost_per_head.value(),
            "barn_location": self._location_input.text().strip() or None,
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class HealthRecordDialog(QDialog):
    """Dialog for adding a health record."""

    def __init__(self, animals: List[AnimalInfo], groups: List[GroupInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Health Record")
        self.setMinimumWidth(500)
        self._animals = animals
        self._groups = groups
        self.record_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Target selection
        self._target_combo = QComboBox()
        self._target_combo.addItem("-- Select Animal or Group --", (None, None))
        for animal in self._animals:
            self._target_combo.addItem(f"Animal: {animal.display_name}", ("animal", animal.id))
        for group in self._groups:
            self._target_combo.addItem(f"Group: {group.group_name}", ("group", group.id))
        form_layout.addRow("Target*:", self._target_combo)

        self._record_date = QDateEdit()
        self._record_date.setCalendarPopup(True)
        self._record_date.setDate(QDate.currentDate())
        self._record_date.setDisplayFormat("MM/dd/yyyy")
        form_layout.addRow("Date*:", self._record_date)

        self._type_combo = QComboBox()
        for value, label in LivestockAPI.HEALTH_RECORD_TYPES:
            self._type_combo.addItem(label, value)
        form_layout.addRow("Type*:", self._type_combo)

        self._medication_input = QLineEdit()
        self._medication_input.setPlaceholderText("e.g., Ivermectin, Draxxin")
        form_layout.addRow("Medication:", self._medication_input)

        self._dosage_input = QLineEdit()
        self._dosage_input.setPlaceholderText("e.g., 5 ml")
        form_layout.addRow("Dosage:", self._dosage_input)

        self._route_combo = QComboBox()
        self._route_combo.addItem("-- Select --", None)
        for value, label in LivestockAPI.MEDICATION_ROUTES:
            self._route_combo.addItem(label, value)
        form_layout.addRow("Route:", self._route_combo)

        self._administered_by = QLineEdit()
        form_layout.addRow("Administered By:", self._administered_by)

        self._vet_name = QLineEdit()
        form_layout.addRow("Vet Name:", self._vet_name)

        self._cost_input = QDoubleSpinBox()
        self._cost_input.setRange(0, 100000)
        self._cost_input.setPrefix("$")
        self._cost_input.setDecimals(2)
        form_layout.addRow("Cost:", self._cost_input)

        self._withdrawal_days = QSpinBox()
        self._withdrawal_days.setRange(0, 365)
        self._withdrawal_days.setSuffix(" days")
        form_layout.addRow("Withdrawal:", self._withdrawal_days)

        self._next_due = QDateEdit()
        self._next_due.setCalendarPopup(True)
        self._next_due.setDate(QDate.currentDate().addDays(365))
        self._next_due.setDisplayFormat("MM/dd/yyyy")
        form_layout.addRow("Next Due:", self._next_due)

        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        form_layout.addRow("Notes:", self._notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Add Record")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save_record)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_record(self):
        target = self._target_combo.currentData()
        if not target or target == (None, None):
            QMessageBox.warning(self, "Validation Error", "Please select an animal or group.")
            return

        target_type, target_id = target
        self.record_data = {
            "animal_id": target_id if target_type == "animal" else None,
            "group_id": target_id if target_type == "group" else None,
            "record_date": self._record_date.date().toString("yyyy-MM-dd"),
            "record_type": self._type_combo.currentData(),
            "medication": self._medication_input.text().strip() or None,
            "dosage": self._dosage_input.text().strip() or None,
            "route": self._route_combo.currentData(),
            "administered_by": self._administered_by.text().strip() or None,
            "vet_name": self._vet_name.text().strip() or None,
            "cost": self._cost_input.value(),
            "withdrawal_days": self._withdrawal_days.value(),
            "next_due_date": self._next_due.date().toString("yyyy-MM-dd"),
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class WeightRecordDialog(QDialog):
    """Dialog for recording weight."""

    def __init__(self, animals: List[AnimalInfo], groups: List[GroupInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Weight")
        self.setMinimumWidth(400)
        self._animals = animals
        self._groups = groups
        self.record_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self._target_combo = QComboBox()
        self._target_combo.addItem("-- Select Animal or Group --", (None, None))
        for animal in self._animals:
            self._target_combo.addItem(f"Animal: {animal.display_name}", ("animal", animal.id))
        for group in self._groups:
            self._target_combo.addItem(f"Group: {group.group_name}", ("group", group.id))
        form_layout.addRow("Target*:", self._target_combo)

        self._weight_date = QDateEdit()
        self._weight_date.setCalendarPopup(True)
        self._weight_date.setDate(QDate.currentDate())
        self._weight_date.setDisplayFormat("MM/dd/yyyy")
        form_layout.addRow("Date*:", self._weight_date)

        self._weight_input = QDoubleSpinBox()
        self._weight_input.setRange(0.1, 10000)
        self._weight_input.setSuffix(" lbs")
        self._weight_input.setDecimals(1)
        form_layout.addRow("Weight*:", self._weight_input)

        self._type_combo = QComboBox()
        for value, label in LivestockAPI.WEIGHT_TYPES:
            self._type_combo.addItem(label, value)
        form_layout.addRow("Weight Type:", self._type_combo)

        self._notes_input = QLineEdit()
        form_layout.addRow("Notes:", self._notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Record Weight")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save_record)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_record(self):
        target = self._target_combo.currentData()
        if not target or target == (None, None):
            QMessageBox.warning(self, "Validation Error", "Please select an animal or group.")
            return

        if self._weight_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid weight.")
            return

        target_type, target_id = target
        self.record_data = {
            "animal_id": target_id if target_type == "animal" else None,
            "group_id": target_id if target_type == "group" else None,
            "weight_date": self._weight_date.date().toString("yyyy-MM-dd"),
            "weight_lbs": self._weight_input.value(),
            "weight_type": self._type_combo.currentData(),
            "notes": self._notes_input.text().strip() or None
        }
        self.accept()


class SaleRecordDialog(QDialog):
    """Dialog for recording a sale."""

    def __init__(self, animals: List[AnimalInfo], groups: List[GroupInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Sale")
        self.setMinimumWidth(500)
        self._animals = animals
        self._groups = groups
        self.record_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self._target_combo = QComboBox()
        self._target_combo.addItem("-- Select Animal or Group --", (None, None))
        for animal in self._animals:
            self._target_combo.addItem(f"Animal: {animal.display_name}", ("animal", animal.id))
        for group in self._groups:
            self._target_combo.addItem(f"Group: {group.group_name}", ("group", group.id))
        form_layout.addRow("Target*:", self._target_combo)

        self._sale_date = QDateEdit()
        self._sale_date.setCalendarPopup(True)
        self._sale_date.setDate(QDate.currentDate())
        self._sale_date.setDisplayFormat("MM/dd/yyyy")
        form_layout.addRow("Sale Date*:", self._sale_date)

        self._head_count = QSpinBox()
        self._head_count.setRange(1, 10000)
        self._head_count.setValue(1)
        form_layout.addRow("Head Count:", self._head_count)

        self._sale_weight = QDoubleSpinBox()
        self._sale_weight.setRange(0, 100000)
        self._sale_weight.setSuffix(" lbs")
        self._sale_weight.setDecimals(1)
        form_layout.addRow("Sale Weight:", self._sale_weight)

        self._price_per_lb = QDoubleSpinBox()
        self._price_per_lb.setRange(0, 100)
        self._price_per_lb.setPrefix("$")
        self._price_per_lb.setSuffix("/lb")
        self._price_per_lb.setDecimals(2)
        form_layout.addRow("Price/lb:", self._price_per_lb)

        self._sale_price = QDoubleSpinBox()
        self._sale_price.setRange(0, 10000000)
        self._sale_price.setPrefix("$")
        self._sale_price.setDecimals(2)
        form_layout.addRow("Sale Price*:", self._sale_price)

        self._type_combo = QComboBox()
        for value, label in LivestockAPI.SALE_TYPES:
            self._type_combo.addItem(label, value)
        form_layout.addRow("Sale Type:", self._type_combo)

        self._buyer_input = QLineEdit()
        form_layout.addRow("Buyer:", self._buyer_input)

        self._market_input = QLineEdit()
        form_layout.addRow("Market/Location:", self._market_input)

        self._commission = QDoubleSpinBox()
        self._commission.setRange(0, 100000)
        self._commission.setPrefix("$")
        self._commission.setDecimals(2)
        form_layout.addRow("Commission:", self._commission)

        self._trucking = QDoubleSpinBox()
        self._trucking.setRange(0, 10000)
        self._trucking.setPrefix("$")
        self._trucking.setDecimals(2)
        form_layout.addRow("Trucking:", self._trucking)

        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        form_layout.addRow("Notes:", self._notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Record Sale")
        save_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        save_btn.clicked.connect(self._save_record)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_record(self):
        target = self._target_combo.currentData()
        if not target or target == (None, None):
            QMessageBox.warning(self, "Validation Error", "Please select an animal or group.")
            return

        if self._sale_price.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter a sale price.")
            return

        target_type, target_id = target
        self.record_data = {
            "animal_id": target_id if target_type == "animal" else None,
            "group_id": target_id if target_type == "group" else None,
            "sale_date": self._sale_date.date().toString("yyyy-MM-dd"),
            "head_count": self._head_count.value(),
            "sale_weight": self._sale_weight.value() if self._sale_weight.value() > 0 else None,
            "price_per_lb": self._price_per_lb.value() if self._price_per_lb.value() > 0 else None,
            "sale_price": self._sale_price.value(),
            "sale_type": self._type_combo.currentData(),
            "buyer_name": self._buyer_input.text().strip() or None,
            "market_name": self._market_input.text().strip() or None,
            "commission": self._commission.value(),
            "trucking_cost": self._trucking.value(),
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


# ============================================================================
# MAIN SCREEN
# ============================================================================

class LivestockManagementScreen(QWidget):
    """Main livestock management screen."""

    # Color scheme
    SPECIES_COLORS = {
        "cattle": "#8B4513",  # Saddle brown
        "hog": "#FF69B4",     # Hot pink
        "poultry": "#FFD700", # Gold
        "sheep": "#F5F5DC",   # Beige
        "goat": "#A0522D"     # Sienna
    }

    STATUS_COLORS = {
        "active": "#4CAF50",
        "sold": "#2196F3",
        "deceased": "#9E9E9E",
        "culled": "#FF9800",
        "transferred": "#9C27B0"
    }

    def __init__(self, current_user: Optional[UserInfo] = None):
        super().__init__()
        self._current_user = current_user
        self._api = get_livestock_api()
        self._animals: List[AnimalInfo] = []
        self._groups: List[GroupInfo] = []
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
        title = QLabel("Livestock Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2e7d32;")
        layout.addWidget(title)

        # Summary cards
        self._summary_layout = QHBoxLayout()
        self._summary_layout.setSpacing(15)

        self._total_head_label = QLabel("0")
        self._summary_layout.addWidget(self._create_summary_card("Total Head", self._total_head_label))

        self._total_groups_label = QLabel("0")
        self._summary_layout.addWidget(self._create_summary_card("Groups", self._total_groups_label))

        self._health_alerts_label = QLabel("0")
        self._summary_layout.addWidget(self._create_summary_card("Health Alerts", self._health_alerts_label))

        self._due_dates_label = QLabel("0")
        self._summary_layout.addWidget(self._create_summary_card("Due Soon", self._due_dates_label))

        self._recent_sales_label = QLabel("$0")
        self._summary_layout.addWidget(self._create_summary_card("Sales (30d)", self._recent_sales_label))

        layout.addLayout(self._summary_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        # Filters
        self._species_filter = QComboBox()
        self._species_filter.addItem("All Species", None)
        for value, label in LivestockAPI.SPECIES_TYPES:
            self._species_filter.addItem(label, value)
        self._species_filter.currentIndexChanged.connect(self._load_data)
        toolbar_layout.addWidget(QLabel("Species:"))
        toolbar_layout.addWidget(self._species_filter)

        self._status_filter = QComboBox()
        self._status_filter.addItem("All Statuses", None)
        for value, label in LivestockAPI.ANIMAL_STATUSES:
            self._status_filter.addItem(label, value)
        self._status_filter.currentIndexChanged.connect(self._load_data)
        toolbar_layout.addWidget(QLabel("Status:"))
        toolbar_layout.addWidget(self._status_filter)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by tag, name, breed...")
        self._search_input.textChanged.connect(self._load_data)
        toolbar_layout.addWidget(self._search_input)

        toolbar_layout.addStretch()

        # Action buttons
        add_animal_btn = QPushButton("+ Add Animal")
        add_animal_btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 8px 16px;")
        add_animal_btn.clicked.connect(self._show_add_animal_dialog)
        toolbar_layout.addWidget(add_animal_btn)

        add_group_btn = QPushButton("+ Add Group")
        add_group_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 8px 16px;")
        add_group_btn.clicked.connect(self._show_add_group_dialog)
        toolbar_layout.addWidget(add_group_btn)

        layout.addLayout(toolbar_layout)

        # Tabs
        self._tabs = QTabWidget()

        # Animals tab
        animals_widget = QWidget()
        animals_layout = QVBoxLayout(animals_widget)
        self._animals_table = QTableWidget()
        self._animals_table.setColumnCount(9)
        self._animals_table.setHorizontalHeaderLabels([
            "Tag/Name", "Species", "Breed", "Sex", "Age", "Weight", "Status", "Location", "Actions"
        ])
        self._animals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._animals_table.setAlternatingRowColors(True)
        self._animals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        animals_layout.addWidget(self._animals_table)
        self._tabs.addTab(animals_widget, "Animals")

        # Groups tab
        groups_widget = QWidget()
        groups_layout = QVBoxLayout(groups_widget)
        self._groups_table = QTableWidget()
        self._groups_table.setColumnCount(7)
        self._groups_table.setHorizontalHeaderLabels([
            "Name", "Species", "Head Count", "Location", "Status", "Value", "Actions"
        ])
        self._groups_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._groups_table.setAlternatingRowColors(True)
        groups_layout.addWidget(self._groups_table)
        self._tabs.addTab(groups_widget, "Groups")

        # Health tab
        health_widget = QWidget()
        health_layout = QVBoxLayout(health_widget)

        health_toolbar = QHBoxLayout()
        add_health_btn = QPushButton("+ Add Health Record")
        add_health_btn.setStyleSheet("background-color: #f57c00; color: white; padding: 6px 12px;")
        add_health_btn.clicked.connect(self._show_health_dialog)
        health_toolbar.addWidget(add_health_btn)
        health_toolbar.addStretch()
        health_layout.addLayout(health_toolbar)

        self._health_table = QTableWidget()
        self._health_table.setColumnCount(7)
        self._health_table.setHorizontalHeaderLabels([
            "Date", "Target", "Type", "Medication", "Cost", "Next Due", "Notes"
        ])
        self._health_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._health_table.setAlternatingRowColors(True)
        health_layout.addWidget(self._health_table)
        self._tabs.addTab(health_widget, "Health Records")

        # Weights tab
        weights_widget = QWidget()
        weights_layout = QVBoxLayout(weights_widget)

        weights_toolbar = QHBoxLayout()
        add_weight_btn = QPushButton("+ Record Weight")
        add_weight_btn.setStyleSheet("background-color: #7b1fa2; color: white; padding: 6px 12px;")
        add_weight_btn.clicked.connect(self._show_weight_dialog)
        weights_toolbar.addWidget(add_weight_btn)
        weights_toolbar.addStretch()
        weights_layout.addLayout(weights_toolbar)

        self._weights_table = QTableWidget()
        self._weights_table.setColumnCount(6)
        self._weights_table.setHorizontalHeaderLabels([
            "Date", "Target", "Weight", "Type", "ADG", "Notes"
        ])
        self._weights_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._weights_table.setAlternatingRowColors(True)
        weights_layout.addWidget(self._weights_table)
        self._tabs.addTab(weights_widget, "Weights")

        # Sales tab
        sales_widget = QWidget()
        sales_layout = QVBoxLayout(sales_widget)

        sales_toolbar = QHBoxLayout()
        add_sale_btn = QPushButton("+ Record Sale")
        add_sale_btn.setStyleSheet("background-color: #0288d1; color: white; padding: 6px 12px;")
        add_sale_btn.clicked.connect(self._show_sale_dialog)
        sales_toolbar.addWidget(add_sale_btn)
        sales_toolbar.addStretch()
        sales_layout.addLayout(sales_toolbar)

        self._sales_table = QTableWidget()
        self._sales_table.setColumnCount(7)
        self._sales_table.setHorizontalHeaderLabels([
            "Date", "Target", "Head", "Weight", "Price", "Net", "Buyer"
        ])
        self._sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._sales_table.setAlternatingRowColors(True)
        sales_layout.addWidget(self._sales_table)
        self._tabs.addTab(sales_widget, "Sales")

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
        self._load_animals()
        self._load_groups()
        self._load_health_records()
        self._load_weight_records()
        self._load_sale_records()

    def _load_summary(self):
        """Load summary statistics."""
        summary, error = self._api.get_summary()
        if error:
            self._status_label.setText(f"Error loading summary: {error}")
            return

        if summary:
            self._total_head_label.setText(str(summary.total_head))
            self._total_groups_label.setText(str(summary.total_groups))
            self._health_alerts_label.setText(str(summary.health_alerts))
            self._due_dates_label.setText(str(summary.upcoming_due_dates))
            self._recent_sales_label.setText(f"${summary.recent_sales_30d:,.0f}")

    def _load_animals(self):
        """Load animals into the table."""
        species = self._species_filter.currentData()
        status = self._status_filter.currentData()
        search = self._search_input.text().strip() or None

        self._animals, error = self._api.list_animals(
            species=species, status=status, search=search
        )

        if error:
            self._status_label.setText(f"Error loading animals: {error}")
            return

        self._animals_table.setRowCount(len(self._animals))
        for row, animal in enumerate(self._animals):
            self._animals_table.setItem(row, 0, QTableWidgetItem(animal.display_name))
            self._animals_table.setItem(row, 1, QTableWidgetItem(animal.species_display))
            self._animals_table.setItem(row, 2, QTableWidgetItem(animal.breed or ""))
            self._animals_table.setItem(row, 3, QTableWidgetItem(animal.sex_display))
            self._animals_table.setItem(row, 4, QTableWidgetItem(animal.age_display))
            self._animals_table.setItem(row, 5, QTableWidgetItem(animal.weight_display))

            status_item = QTableWidgetItem(animal.status_display)
            color = self.STATUS_COLORS.get(animal.status, "#666")
            status_item.setForeground(QColor(color))
            self._animals_table.setItem(row, 6, status_item)

            self._animals_table.setItem(row, 7, QTableWidgetItem(animal.current_location or ""))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 2px 8px; font-size: 11px;")
            edit_btn.clicked.connect(lambda checked, a=animal: self._edit_animal(a))
            actions_layout.addWidget(edit_btn)

            if self._current_user and self._current_user.role in ("admin", "manager"):
                del_btn = QPushButton("Del")
                del_btn.setStyleSheet("background-color: #d32f2f; color: white; padding: 2px 8px; font-size: 11px;")
                del_btn.clicked.connect(lambda checked, a=animal: self._delete_animal(a))
                actions_layout.addWidget(del_btn)

            self._animals_table.setCellWidget(row, 8, actions_widget)

        self._status_label.setText(f"Loaded {len(self._animals)} animals")

    def _load_groups(self):
        """Load groups into the table."""
        species = self._species_filter.currentData()
        self._groups, error = self._api.list_groups(species=species)

        if error:
            return

        self._groups_table.setRowCount(len(self._groups))
        for row, group in enumerate(self._groups):
            self._groups_table.setItem(row, 0, QTableWidgetItem(group.group_name))
            self._groups_table.setItem(row, 1, QTableWidgetItem(group.species_display))
            self._groups_table.setItem(row, 2, QTableWidgetItem(str(group.head_count)))
            self._groups_table.setItem(row, 3, QTableWidgetItem(group.barn_location or ""))
            self._groups_table.setItem(row, 4, QTableWidgetItem(group.status_display))
            self._groups_table.setItem(row, 5, QTableWidgetItem(f"${group.total_value:,.2f}"))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 2px 8px; font-size: 11px;")
            actions_layout.addWidget(edit_btn)

            self._groups_table.setCellWidget(row, 6, actions_widget)

    def _load_health_records(self):
        """Load health records."""
        records, error = self._api.list_health_records()
        if error:
            return

        self._health_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self._health_table.setItem(row, 0, QTableWidgetItem(record.record_date))
            self._health_table.setItem(row, 1, QTableWidgetItem(record.target_display))
            self._health_table.setItem(row, 2, QTableWidgetItem(record.record_type_display))
            self._health_table.setItem(row, 3, QTableWidgetItem(record.medication or ""))
            self._health_table.setItem(row, 4, QTableWidgetItem(f"${record.cost:.2f}"))
            self._health_table.setItem(row, 5, QTableWidgetItem(record.next_due_date or ""))
            self._health_table.setItem(row, 6, QTableWidgetItem(record.notes or ""))

    def _load_weight_records(self):
        """Load weight records."""
        records, error = self._api.list_weight_records()
        if error:
            return

        self._weights_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self._weights_table.setItem(row, 0, QTableWidgetItem(record.weight_date))
            target = record.animal_tag or record.group_name or "Unknown"
            self._weights_table.setItem(row, 1, QTableWidgetItem(target))
            self._weights_table.setItem(row, 2, QTableWidgetItem(f"{record.weight_lbs:,.0f} lbs"))
            self._weights_table.setItem(row, 3, QTableWidgetItem(record.weight_type_display))
            self._weights_table.setItem(row, 4, QTableWidgetItem(record.adg_display))
            self._weights_table.setItem(row, 5, QTableWidgetItem(record.notes or ""))

    def _load_sale_records(self):
        """Load sale records."""
        records, error = self._api.list_sale_records()
        if error:
            return

        self._sales_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self._sales_table.setItem(row, 0, QTableWidgetItem(record.sale_date))
            target = record.animal_tag or record.group_name or "Unknown"
            self._sales_table.setItem(row, 1, QTableWidgetItem(target))
            self._sales_table.setItem(row, 2, QTableWidgetItem(str(record.head_count)))
            self._sales_table.setItem(row, 3, QTableWidgetItem(f"{record.sale_weight or 0:,.0f} lbs"))
            self._sales_table.setItem(row, 4, QTableWidgetItem(record.price_display))
            self._sales_table.setItem(row, 5, QTableWidgetItem(record.net_display))
            self._sales_table.setItem(row, 6, QTableWidgetItem(record.buyer_name or ""))

    def _show_add_animal_dialog(self):
        """Show dialog to add a new animal."""
        dialog = AddAnimalDialog(self._groups, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.animal_data:
            animal, error = self._api.create_animal(**dialog.animal_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to create animal: {error}")
            else:
                self._status_label.setText(f"Animal added successfully")
                self._load_data()

    def _show_add_group_dialog(self):
        """Show dialog to add a new group."""
        dialog = AddGroupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.group_data:
            group, error = self._api.create_group(**dialog.group_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to create group: {error}")
            else:
                self._status_label.setText(f"Group added successfully")
                self._load_data()

    def _show_health_dialog(self):
        """Show dialog to add a health record."""
        dialog = HealthRecordDialog(self._animals, self._groups, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.record_data:
            record, error = self._api.create_health_record(**dialog.record_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to create health record: {error}")
            else:
                self._status_label.setText(f"Health record added successfully")
                self._load_data()

    def _show_weight_dialog(self):
        """Show dialog to record weight."""
        dialog = WeightRecordDialog(self._animals, self._groups, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.record_data:
            record, error = self._api.create_weight_record(**dialog.record_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to record weight: {error}")
            else:
                self._status_label.setText(f"Weight recorded successfully")
                self._load_data()

    def _show_sale_dialog(self):
        """Show dialog to record a sale."""
        dialog = SaleRecordDialog(self._animals, self._groups, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.record_data:
            record, error = self._api.create_sale_record(**dialog.record_data)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to record sale: {error}")
            else:
                self._status_label.setText(f"Sale recorded successfully")
                self._load_data()

    def _edit_animal(self, animal: AnimalInfo):
        """Edit an animal."""
        # For now, just show info
        QMessageBox.information(self, "Edit Animal",
            f"Edit functionality for {animal.display_name}\n"
            f"Species: {animal.species_display}\n"
            f"Status: {animal.status_display}")

    def _delete_animal(self, animal: AnimalInfo):
        """Delete an animal."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {animal.display_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._api.delete_animal(animal.id)
            if error:
                QMessageBox.warning(self, "Error", f"Failed to delete: {error}")
            else:
                self._status_label.setText(f"Animal deleted")
                self._load_data()
