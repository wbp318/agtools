"""
Field Management Screen

Screen for managing farm fields - create, edit, and track field information.
AgTools v2.5.0 Phase 3
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QTextEdit, QDoubleSpinBox, QGroupBox
)
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.field_api import get_field_api, FieldAPI, FieldInfo
from api.auth_api import UserInfo


# Crop colors for visual identification
CROP_COLORS = {
    "corn": "#f9a825",       # Yellow
    "soybean": "#558b2f",    # Green
    "wheat": "#d4a574",      # Tan
    "cotton": "#f5f5f5",     # White
    "rice": "#90caf9",       # Light Blue
    "sorghum": "#c62828",    # Red-brown
    "alfalfa": "#2e7d32",    # Dark Green
    "hay": "#8bc34a",        # Light Green
    "pasture": "#66bb6a",    # Green
    "fallow": "#9e9e9e",     # Gray
    "other": "#757575",      # Gray
}


class CreateFieldDialog(QDialog):
    """Dialog for creating a new field."""

    def __init__(self, farm_names: list = None, parent=None):
        super().__init__(parent)
        self.farm_names = farm_names or []
        self.setWindowTitle("Add New Field")
        self.setMinimumWidth(500)
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
        self._name_input.setPlaceholderText("e.g., North 40, Home Quarter")
        basic_layout.addRow("Field Name:", self._name_input)

        # Farm name
        self._farm_combo = QComboBox()
        self._farm_combo.setEditable(True)
        self._farm_combo.addItem("")
        for farm in self.farm_names:
            self._farm_combo.addItem(farm)
        self._farm_combo.setPlaceholderText("e.g., Smith Farm, Home Place")
        basic_layout.addRow("Farm:", self._farm_combo)

        # Acreage
        self._acreage_input = QDoubleSpinBox()
        self._acreage_input.setRange(0.1, 100000)
        self._acreage_input.setDecimals(2)
        self._acreage_input.setSuffix(" acres")
        self._acreage_input.setValue(80)
        basic_layout.addRow("Acreage:", self._acreage_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Field Details Group
        details_group = QGroupBox("Field Details")
        details_layout = QFormLayout()
        details_layout.setSpacing(10)

        # Current crop
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Not set", None)
        for value, label in FieldAPI.CROP_TYPES:
            self._crop_combo.addItem(label, value)
        details_layout.addRow("Current Crop:", self._crop_combo)

        # Soil type
        self._soil_combo = QComboBox()
        self._soil_combo.addItem("Not set", None)
        for value, label in FieldAPI.SOIL_TYPES:
            self._soil_combo.addItem(label, value)
        details_layout.addRow("Soil Type:", self._soil_combo)

        # Irrigation
        self._irrigation_combo = QComboBox()
        for value, label in FieldAPI.IRRIGATION_TYPES:
            self._irrigation_combo.addItem(label, value)
        details_layout.addRow("Irrigation:", self._irrigation_combo)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(80)
        self._notes_input.setPlaceholderText("Additional notes about this field...")
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Add Field")
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
        create_btn.clicked.connect(self._create_field)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _create_field(self):
        """Validate and prepare field data."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Field name is required")
            return

        acreage = self._acreage_input.value()
        if acreage <= 0:
            QMessageBox.warning(self, "Validation Error", "Acreage must be greater than 0")
            return

        self.field_data = {
            "name": name,
            "farm_name": self._farm_combo.currentText().strip() or None,
            "acreage": acreage,
            "current_crop": self._crop_combo.currentData(),
            "soil_type": self._soil_combo.currentData(),
            "irrigation_type": self._irrigation_combo.currentData(),
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class EditFieldDialog(QDialog):
    """Dialog for editing an existing field."""

    def __init__(self, field: FieldInfo, farm_names: list = None, parent=None):
        super().__init__(parent)
        self.field = field
        self.farm_names = farm_names or []
        self.setWindowTitle(f"Edit Field: {field.name}")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(10)

        # Name
        self._name_input = QLineEdit(self.field.name)
        basic_layout.addRow("Field Name:", self._name_input)

        # Farm name
        self._farm_combo = QComboBox()
        self._farm_combo.setEditable(True)
        self._farm_combo.addItem("")
        for farm in self.farm_names:
            self._farm_combo.addItem(farm)
        if self.field.farm_name:
            self._farm_combo.setCurrentText(self.field.farm_name)
        basic_layout.addRow("Farm:", self._farm_combo)

        # Acreage
        self._acreage_input = QDoubleSpinBox()
        self._acreage_input.setRange(0.1, 100000)
        self._acreage_input.setDecimals(2)
        self._acreage_input.setSuffix(" acres")
        self._acreage_input.setValue(self.field.acreage)
        basic_layout.addRow("Acreage:", self._acreage_input)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Field Details Group
        details_group = QGroupBox("Field Details")
        details_layout = QFormLayout()
        details_layout.setSpacing(10)

        # Current crop
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Not set", None)
        crop_idx = 0
        for idx, (value, label) in enumerate(FieldAPI.CROP_TYPES):
            self._crop_combo.addItem(label, value)
            if value == self.field.current_crop:
                crop_idx = idx + 1
        self._crop_combo.setCurrentIndex(crop_idx)
        details_layout.addRow("Current Crop:", self._crop_combo)

        # Soil type
        self._soil_combo = QComboBox()
        self._soil_combo.addItem("Not set", None)
        soil_idx = 0
        for idx, (value, label) in enumerate(FieldAPI.SOIL_TYPES):
            self._soil_combo.addItem(label, value)
            if value == self.field.soil_type:
                soil_idx = idx + 1
        self._soil_combo.setCurrentIndex(soil_idx)
        details_layout.addRow("Soil Type:", self._soil_combo)

        # Irrigation
        self._irrigation_combo = QComboBox()
        irrig_idx = 0
        for idx, (value, label) in enumerate(FieldAPI.IRRIGATION_TYPES):
            self._irrigation_combo.addItem(label, value)
            if value == self.field.irrigation_type:
                irrig_idx = idx
        self._irrigation_combo.setCurrentIndex(irrig_idx)
        details_layout.addRow("Irrigation:", self._irrigation_combo)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout()
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(80)
        self._notes_input.setText(self.field.notes or "")
        notes_layout.addWidget(self._notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # Info section
        info_label = QLabel(f"Operations: {self.field.total_operations} | Last operation: {self.field.last_operation_date[:10] if self.field.last_operation_date else 'None'}")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)

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
        save_btn.clicked.connect(self._save_field)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_field(self):
        """Validate and prepare field update data."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Field name is required")
            return

        self.field_data = {
            "name": name,
            "farm_name": self._farm_combo.currentText().strip() or None,
            "acreage": self._acreage_input.value(),
            "current_crop": self._crop_combo.currentData(),
            "soil_type": self._soil_combo.currentData(),
            "irrigation_type": self._irrigation_combo.currentData(),
            "notes": self._notes_input.toPlainText().strip() or None
        }
        self.accept()


class FieldManagementScreen(QWidget):
    """
    Field management screen for Farm Operations Manager.

    Features:
    - List fields with filters (farm, crop, soil type)
    - Create new fields
    - Edit existing fields
    - View field statistics
    - Delete fields (manager/admin only)
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._field_api = get_field_api()
        self._fields: list[FieldInfo] = []
        self._farm_names: list[str] = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user after login."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the field management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Field Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add field button
        add_btn = QPushButton("+ Add Field")
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

        self._total_fields_label = QLabel("0")
        self._total_fields_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2e7d32;
            }
        """)
        fields_card = self._create_summary_card("Total Fields", self._total_fields_label)
        summary_layout.addWidget(fields_card)

        self._total_acres_label = QLabel("0")
        self._total_acres_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
            }
        """)
        acres_card = self._create_summary_card("Total Acres", self._total_acres_label)
        summary_layout.addWidget(acres_card)

        self._crops_label = QLabel("-")
        self._crops_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
            }
        """)
        crops_card = self._create_summary_card("Crops", self._crops_label)
        summary_layout.addWidget(crops_card)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Filters
        filter_layout = QHBoxLayout()

        # Farm filter
        filter_layout.addWidget(QLabel("Farm:"))
        self._farm_filter = QComboBox()
        self._farm_filter.addItem("All Farms")
        self._farm_filter.currentIndexChanged.connect(self._load_fields)
        filter_layout.addWidget(self._farm_filter)

        # Crop filter
        filter_layout.addWidget(QLabel("Crop:"))
        self._crop_filter = QComboBox()
        self._crop_filter.addItem("All Crops", None)
        for value, label in FieldAPI.CROP_TYPES:
            self._crop_filter.addItem(label, value)
        self._crop_filter.currentIndexChanged.connect(self._load_fields)
        filter_layout.addWidget(self._crop_filter)

        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search fields...")
        self._search_input.textChanged.connect(self._load_fields)
        filter_layout.addWidget(self._search_input)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Fields table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "Field Name", "Farm", "Acres", "Crop", "Soil", "Irrigation", "Operations", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(7, 180)
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
        """Load farm names and fields."""
        # Load farm names for filter
        farm_names, _ = self._field_api.get_farm_names()
        self._farm_names = farm_names

        # Update farm filter
        current_farm = self._farm_filter.currentText()
        self._farm_filter.clear()
        self._farm_filter.addItem("All Farms")
        for farm in farm_names:
            self._farm_filter.addItem(farm)
        if current_farm in farm_names:
            self._farm_filter.setCurrentText(current_farm)

        # Load fields and summary
        self._load_fields()
        self._load_summary()

    def _load_summary(self):
        """Load summary statistics."""
        summary, error = self._field_api.get_summary()
        if summary:
            self._total_fields_label.setText(str(summary.total_fields))
            self._total_acres_label.setText(f"{summary.total_acreage:,.1f}")

            # Show top crops
            if summary.fields_by_crop:
                crops = list(summary.fields_by_crop.keys())[:3]
                crop_text = ", ".join(c.replace("_", " ").title() for c in crops)
                self._crops_label.setText(crop_text)
            else:
                self._crops_label.setText("No crops")

    def _load_fields(self):
        """Load fields from API with current filters."""
        farm_name = None
        if self._farm_filter.currentIndex() > 0:
            farm_name = self._farm_filter.currentText()

        current_crop = self._crop_filter.currentData()
        search = self._search_input.text().strip() or None

        fields, error = self._field_api.list_fields(
            farm_name=farm_name,
            current_crop=current_crop,
            search=search
        )

        if error:
            self._status_label.setText(f"Error loading fields: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._fields = fields
        self._populate_table()
        self._status_label.setText(f"{len(fields)} fields found")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_table(self):
        """Populate the table with field data."""
        self._table.setRowCount(len(self._fields))

        for row, field in enumerate(self._fields):
            # Field Name
            name_item = QTableWidgetItem(field.name)
            name_item.setFont(QFont("Arial", -1, QFont.Weight.Bold))
            self._table.setItem(row, 0, name_item)

            # Farm
            self._table.setItem(row, 1, QTableWidgetItem(field.farm_display))

            # Acres
            self._table.setItem(row, 2, QTableWidgetItem(f"{field.acreage:,.1f}"))

            # Crop (color-coded)
            crop_item = QTableWidgetItem(field.crop_display)
            if field.current_crop:
                crop_color = CROP_COLORS.get(field.current_crop, "#666")
                crop_item.setForeground(QColor(crop_color))
            self._table.setItem(row, 3, crop_item)

            # Soil
            self._table.setItem(row, 4, QTableWidgetItem(field.soil_display))

            # Irrigation
            self._table.setItem(row, 5, QTableWidgetItem(field.irrigation_display))

            # Operations count
            ops_text = str(field.total_operations) if field.total_operations else "0"
            self._table.setItem(row, 6, QTableWidgetItem(ops_text))

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
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            edit_btn.clicked.connect(lambda checked, f=field: self._show_edit_dialog(f))
            actions_layout.addWidget(edit_btn)

            # View History button
            history_btn = QPushButton("History")
            history_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7b1fa2;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #6a1b9a;
                }
            """)
            history_btn.clicked.connect(lambda checked, f=field: self._view_history(f))
            actions_layout.addWidget(history_btn)

            # Delete button (manager/admin only)
            if self._current_user and self._current_user.role in ("admin", "manager"):
                delete_btn = QPushButton("Delete")
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
                delete_btn.clicked.connect(lambda checked, f=field: self._delete_field(f))
                actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 7, actions_widget)

    def _show_create_dialog(self):
        """Show create field dialog."""
        dialog = CreateFieldDialog(
            farm_names=self._farm_names,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            field, error = self._field_api.create_field(**dialog.field_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to create field: {error}")
            else:
                QMessageBox.information(self, "Success", f"Field '{field.name}' created successfully")
                self._load_data()

    def _show_edit_dialog(self, field: FieldInfo):
        """Show edit field dialog."""
        dialog = EditFieldDialog(
            field=field,
            farm_names=self._farm_names,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_field, error = self._field_api.update_field(field.id, **dialog.field_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update field: {error}")
            else:
                QMessageBox.information(self, "Success", "Field updated successfully")
                self._load_data()

    def _view_history(self, field: FieldInfo):
        """View operation history for a field."""
        # This will emit a signal or switch to operations screen filtered by field
        # For now, show a message with the count
        QMessageBox.information(
            self,
            f"Field History: {field.name}",
            f"This field has {field.total_operations} recorded operations.\n\n"
            f"Last operation: {field.last_operation_date[:10] if field.last_operation_date else 'None'}\n\n"
            "View the Operations Log screen for full details."
        )

    def _delete_field(self, field: FieldInfo):
        """Delete a field."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete field '{field.name}'?\n\n"
            f"This field has {field.total_operations} recorded operations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._field_api.delete_field(field.id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to delete field: {error}")
            else:
                QMessageBox.information(self, "Success", "Field deleted successfully")
                self._load_data()

    def refresh(self):
        """Refresh the field list."""
        self._load_data()
