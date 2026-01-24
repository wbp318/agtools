"""
AgTools Pest Identification Screen

Symptom-based pest identification with confidence scoring and management info.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QScrollArea,
    QComboBox, QSpinBox,
    QGroupBox, QFormLayout, QMessageBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS, set_widget_class
from models.identification import (
    PEST_SYMPTOMS,
    PestIdentificationRequest, PestInfo,
)
from api.identification_api import get_identification_api


class SymptomSelector(QGroupBox):
    """Widget for selecting pest symptoms from a checklist."""

    symptoms_changed = pyqtSignal()

    def __init__(self, title: str = "Observed Symptoms", parent=None):
        super().__init__(title, parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setSpacing(8)

        # Default symptoms - will be updated based on crop
        self._symptoms = PEST_SYMPTOMS

    def set_symptoms(self, symptoms: list[str]) -> None:
        """Update the available symptoms."""
        # Clear existing
        for cb in self._checkboxes.values():
            cb.deleteLater()
        self._checkboxes.clear()

        # Add new checkboxes
        layout = self.layout()
        # Clear layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        row, col = 0, 0
        max_cols = 3
        for symptom in symptoms:
            cb = QCheckBox(symptom.replace("_", " ").title())
            cb.stateChanged.connect(lambda: self.symptoms_changed.emit())
            self._checkboxes[symptom] = cb
            layout.addWidget(cb, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def get_selected_symptoms(self) -> list[str]:
        """Get list of selected symptom IDs."""
        return [key for key, cb in self._checkboxes.items() if cb.isChecked()]

    def clear_selection(self) -> None:
        """Uncheck all symptoms."""
        for cb in self._checkboxes.values():
            cb.setChecked(False)


class PestResultCard(QFrame):
    """Card displaying a single pest identification result."""

    def __init__(self, pest: PestInfo, parent=None):
        super().__init__(parent)
        self._pest = pest
        self._setup_ui()
        set_widget_class(self, "card")

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header with name and confidence
        header = QHBoxLayout()

        name_label = QLabel(self._pest.common_name)
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setWeight(QFont.Weight.Bold)
        name_label.setFont(name_font)
        header.addWidget(name_label)

        header.addStretch()

        # Confidence badge
        confidence_pct = int(self._pest.confidence * 100) if self._pest.confidence else 0
        confidence_label = QLabel(f"{confidence_pct}% Match")
        if confidence_pct >= 70:
            confidence_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        elif confidence_pct >= 50:
            confidence_label.setStyleSheet(f"color: {COLORS['warning']}; font-weight: bold;")
        else:
            confidence_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: bold;")
        header.addWidget(confidence_label)

        layout.addLayout(header)

        # Scientific name
        sci_name = QLabel(f"<i>{self._pest.scientific_name}</i>")
        sci_name.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(sci_name)

        # Description
        desc_label = QLabel(self._pest.description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Sections in grid
        sections = QGridLayout()
        sections.setSpacing(16)

        # Damage Symptoms
        damage_group = self._create_section("Damage Symptoms", self._pest.damage_symptoms)
        sections.addWidget(damage_group, 0, 0)

        # Identification Features
        id_group = self._create_section("Identification Features", self._pest.identification_features)
        sections.addWidget(id_group, 0, 1)

        layout.addLayout(sections)

        # Economic Threshold
        if self._pest.economic_threshold:
            threshold_frame = QFrame()
            threshold_frame.setStyleSheet(f"""
                background-color: {COLORS['warning']}20;
                border-radius: 4px;
                padding: 8px;
            """)
            threshold_layout = QVBoxLayout(threshold_frame)
            threshold_layout.setContentsMargins(8, 8, 8, 8)

            threshold_title = QLabel("Economic Threshold")
            threshold_title.setStyleSheet(f"font-weight: bold; color: {COLORS['warning']};")
            threshold_layout.addWidget(threshold_title)

            threshold_text = QLabel(self._pest.economic_threshold)
            threshold_text.setWordWrap(True)
            threshold_layout.addWidget(threshold_text)

            layout.addWidget(threshold_frame)

        # Management Notes
        if self._pest.management_notes:
            mgmt_frame = QFrame()
            mgmt_frame.setStyleSheet(f"""
                background-color: {COLORS['success']}20;
                border-radius: 4px;
                padding: 8px;
            """)
            mgmt_layout = QVBoxLayout(mgmt_frame)
            mgmt_layout.setContentsMargins(8, 8, 8, 8)

            mgmt_title = QLabel("Management Notes")
            mgmt_title.setStyleSheet(f"font-weight: bold; color: {COLORS['success']};")
            mgmt_layout.addWidget(mgmt_title)

            mgmt_text = QLabel(self._pest.management_notes)
            mgmt_text.setWordWrap(True)
            mgmt_layout.addWidget(mgmt_text)

            layout.addWidget(mgmt_frame)

    def _create_section(self, title: str, content: str) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        label = QLabel(content)
        label.setWordWrap(True)
        layout.addWidget(label)
        return group


class PestIdentificationScreen(QWidget):
    """
    Pest Identification screen with symptom-based identification.

    Features:
    - Crop and growth stage selection
    - Symptom checklist
    - Severity rating
    - Location description
    - Identification results with confidence scores
    - Management information
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_identification_api()
        self._results: list[PestInfo] = []
        self._setup_ui()
        self._update_symptoms()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left panel - Input form
        left_panel = QFrame()
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)

        # Title
        title = QLabel("Pest Identification")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        left_layout.addWidget(title)

        subtitle = QLabel("Identify pests based on observed symptoms")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        left_layout.addWidget(subtitle)

        # Crop and Growth Stage
        crop_group = QGroupBox("Field Information")
        crop_layout = QFormLayout(crop_group)

        self._crop_combo = QComboBox()
        self._crop_combo.addItems(["Corn", "Soybean"])
        self._crop_combo.currentTextChanged.connect(self._update_symptoms)
        crop_layout.addRow("Crop:", self._crop_combo)

        self._stage_combo = QComboBox()
        self._stage_combo.addItems([
            "VE", "V1", "V2", "V3", "V4", "V6", "VT",
            "R1", "R2", "R3", "R4", "R5", "R6"
        ])
        self._stage_combo.setCurrentText("V6")
        crop_layout.addRow("Growth Stage:", self._stage_combo)

        left_layout.addWidget(crop_group)

        # Symptom selector
        self._symptom_selector = SymptomSelector("Observed Symptoms")
        left_layout.addWidget(self._symptom_selector)

        # Additional info
        info_group = QGroupBox("Additional Information")
        info_layout = QFormLayout(info_group)

        self._severity_spin = QSpinBox()
        self._severity_spin.setRange(1, 10)
        self._severity_spin.setValue(5)
        self._severity_spin.setToolTip("1 = Minor, 10 = Severe")
        info_layout.addRow("Severity (1-10):", self._severity_spin)

        self._location_combo = QComboBox()
        self._location_combo.addItems([
            "Field Interior",
            "Field Edge",
            "Low Spots",
            "High Ground",
            "Near Waterway",
            "Random/Scattered"
        ])
        info_layout.addRow("Location:", self._location_combo)

        left_layout.addWidget(info_group)

        # Identify button
        self._identify_btn = QPushButton("Identify Pest")
        self._identify_btn.setMinimumHeight(44)
        self._identify_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                font-weight: bold;
                font-size: 14pt;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        self._identify_btn.clicked.connect(self._identify)
        left_layout.addWidget(self._identify_btn)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_form)
        left_layout.addWidget(clear_btn)

        left_layout.addStretch()

        layout.addWidget(left_panel)

        # Right panel - Results
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)

        results_title = QLabel("Identification Results")
        results_title_font = QFont()
        results_title_font.setPointSize(16)
        results_title_font.setWeight(QFont.Weight.DemiBold)
        results_title.setFont(results_title_font)
        right_layout.addWidget(results_title)

        # Results scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._results_widget = QWidget()
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setSpacing(16)
        self._results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Placeholder
        self._placeholder = QLabel("Select symptoms and click 'Identify Pest' to see results")
        self._placeholder.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 14pt;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._results_layout.addWidget(self._placeholder)

        scroll.setWidget(self._results_widget)
        right_layout.addWidget(scroll)

        layout.addWidget(right_panel, 1)

    def _update_symptoms(self) -> None:
        """Update symptom list based on selected crop."""
        self._crop_combo.currentText().lower()
        symptoms = PEST_SYMPTOMS
        self._symptom_selector.set_symptoms(symptoms)

    def _identify(self) -> None:
        """Run pest identification."""
        symptoms = self._symptom_selector.get_selected_symptoms()

        if not symptoms:
            QMessageBox.warning(
                self,
                "No Symptoms Selected",
                "Please select at least one symptom to identify."
            )
            return

        # Build request
        request = PestIdentificationRequest(
            crop=self._crop_combo.currentText().lower(),
            growth_stage=self._stage_combo.currentText(),
            symptoms=symptoms,
            severity_rating=self._severity_spin.value(),
            location_description=self._location_combo.currentText(),
        )

        # Call API
        self._identify_btn.setEnabled(False)
        self._identify_btn.setText("Identifying...")

        try:
            success, result = self._api.identify_pest(request)

            if success:
                self._results = result
                self._display_results()
            else:
                QMessageBox.warning(self, "Identification Failed", str(result))
        finally:
            self._identify_btn.setEnabled(True)
            self._identify_btn.setText("Identify Pest")

    def _display_results(self) -> None:
        """Display identification results."""
        # Clear existing results
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._results:
            no_results = QLabel("No matching pests found. Try selecting different symptoms.")
            no_results.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14pt;")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._results_layout.addWidget(no_results)
            return

        # Add result cards
        for pest in self._results:
            card = PestResultCard(pest)
            self._results_layout.addWidget(card)

        self._results_layout.addStretch()

    def _clear_form(self) -> None:
        """Clear the form and results."""
        self._symptom_selector.clear_selection()
        self._severity_spin.setValue(5)
        self._location_combo.setCurrentIndex(0)
        self._results = []

        # Clear results
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._results_layout.addWidget(self._placeholder)
