"""
AgTools Measurement Converter Screen

Imperial to metric conversion for agricultural spray applications.
Designed for South African and Brazilian operators.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QComboBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QFormLayout, QMessageBox, QLineEdit,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.retro_styles import RETRO_COLORS
from models.measurement_converter import (
    ApplicationRateUnit,
    ConversionResult,
    TankMixResult,
    ReferenceProduct,
    convert_locally,
)
from api.measurement_converter_api import get_measurement_converter_api


# Local color scheme using retro colors
COLORS = {
    "primary": RETRO_COLORS["turquoise_dark"],
    "primary_light": RETRO_COLORS["turquoise_light"],
    "surface": RETRO_COLORS["cream"],
    "surface_alt": RETRO_COLORS["cream_light"],
    "border": RETRO_COLORS["turquoise_medium"],
    "text": RETRO_COLORS["text_black"],
    "text_secondary": RETRO_COLORS["text_light"],
    "success": RETRO_COLORS["status_ok"],
    "warning": RETRO_COLORS["status_warning"],
    "card_bg": RETRO_COLORS["window_face"],
    "result_bg": RETRO_COLORS["cyan_light"],
}


def create_card_frame() -> QFrame:
    """Create a styled card frame."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['card_bg']};
            border: 2px solid {COLORS['border']};
            border-radius: 4px;
            padding: 12px;
        }}
    """)
    return frame


def create_result_frame() -> QFrame:
    """Create a styled result display frame."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['result_bg']};
            border: 2px solid {COLORS['primary']};
            border-radius: 6px;
            padding: 16px;
        }}
    """)
    return frame


def create_header_label(text: str) -> QLabel:
    """Create a styled header label."""
    label = QLabel(text)
    label.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 4px 0;
        }}
    """)
    return label


def create_result_label(text: str = "", large: bool = False) -> QLabel:
    """Create a styled result label."""
    label = QLabel(text)
    size = "24px" if large else "18px"
    label.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['text']};
            font-size: {size};
            font-weight: bold;
        }}
    """)
    return label


class QuickConverterTab(QWidget):
    """Tab for quick unit conversions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_measurement_converter_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = create_header_label("Quick Unit Converter")
        layout.addWidget(header)

        # Description
        desc = QLabel("Convert imperial spray application rates to metric for field operators.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Conversion input section
        input_frame = create_card_frame()
        input_layout = QFormLayout(input_frame)
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(16, 16, 16, 16)

        # Unit type selector
        self._unit_type_combo = QComboBox()
        self._unit_type_combo.addItem("Application Rate (Volume)", "rate_volume")
        self._unit_type_combo.addItem("Application Rate (Weight)", "rate_weight")
        self._unit_type_combo.addItem("Volume", "volume")
        self._unit_type_combo.addItem("Weight", "weight")
        self._unit_type_combo.addItem("Area", "area")
        self._unit_type_combo.addItem("Speed", "speed")
        self._unit_type_combo.addItem("Pressure", "pressure")
        self._unit_type_combo.addItem("Temperature", "temperature")
        self._unit_type_combo.currentIndexChanged.connect(self._on_type_changed)
        input_layout.addRow("Conversion Type:", self._unit_type_combo)

        # Value input
        self._value_spin = QDoubleSpinBox()
        self._value_spin.setRange(0.01, 99999)
        self._value_spin.setDecimals(3)
        self._value_spin.setValue(32)
        self._value_spin.valueChanged.connect(self._on_value_changed)
        input_layout.addRow("Value:", self._value_spin)

        # From unit selector
        self._from_unit_combo = QComboBox()
        self._from_unit_combo.currentIndexChanged.connect(self._on_value_changed)
        input_layout.addRow("From Unit:", self._from_unit_combo)

        layout.addWidget(input_frame)

        # Result section
        result_frame = create_result_frame()
        result_layout = QVBoxLayout(result_frame)
        result_layout.setSpacing(12)

        # Imperial display
        imperial_row = QHBoxLayout()
        imperial_row.addWidget(QLabel("Imperial:"))
        self._imperial_label = create_result_label("32 fl oz/acre")
        imperial_row.addWidget(self._imperial_label)
        imperial_row.addStretch()
        result_layout.addLayout(imperial_row)

        # Equals sign
        equals = QLabel("=")
        equals.setStyleSheet("font-size: 24px; font-weight: bold; color: #00868B;")
        equals.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.addWidget(equals)

        # Metric display (larger)
        metric_row = QHBoxLayout()
        metric_row.addWidget(QLabel("Metric:"))
        self._metric_label = create_result_label("2.34 L/ha", large=True)
        self._metric_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['primary']};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        metric_row.addWidget(self._metric_label)
        metric_row.addStretch()

        # Copy button
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedWidth(80)
        self._copy_btn.clicked.connect(self._copy_metric)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_light']};
            }}
        """)
        metric_row.addWidget(self._copy_btn)
        result_layout.addLayout(metric_row)

        layout.addWidget(result_frame)

        # Quick reference card
        ref_frame = create_card_frame()
        ref_layout = QVBoxLayout(ref_frame)

        ref_header = QLabel("Quick Reference")
        ref_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        ref_layout.addWidget(ref_header)

        ref_text = QLabel(
            "1 gal/acre = 9.35 L/ha  |  1 lb/acre = 1.12 kg/ha\n"
            "1 fl oz/acre = 73.08 mL/ha  |  1 oz/acre = 70.05 g/ha\n"
            "1 pt/acre = 1.17 L/ha  |  1 qt/acre = 2.34 L/ha\n"
            "1 acre = 0.40 ha  |  1 mph = 1.61 km/h  |  1 PSI = 0.07 bar"
        )
        ref_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: monospace;")
        ref_layout.addWidget(ref_text)

        layout.addWidget(ref_frame)
        layout.addStretch()

        # Initialize unit options
        self._on_type_changed()

    def _on_type_changed(self) -> None:
        """Update unit options when type changes."""
        unit_type = self._unit_type_combo.currentData()
        self._from_unit_combo.clear()

        if unit_type == "rate_volume":
            self._from_unit_combo.addItem("gal/acre", "gal_per_acre")
            self._from_unit_combo.addItem("fl oz/acre", "fl_oz_per_acre")
            self._from_unit_combo.addItem("pt/acre", "pt_per_acre")
            self._from_unit_combo.addItem("qt/acre", "qt_per_acre")
        elif unit_type == "rate_weight":
            self._from_unit_combo.addItem("lb/acre", "lb_per_acre")
            self._from_unit_combo.addItem("oz/acre", "oz_per_acre")
        elif unit_type == "volume":
            self._from_unit_combo.addItem("gallon", "gal")
            self._from_unit_combo.addItem("fl oz", "fl_oz")
            self._from_unit_combo.addItem("quart", "qt")
            self._from_unit_combo.addItem("pint", "pt")
        elif unit_type == "weight":
            self._from_unit_combo.addItem("pound", "lb")
            self._from_unit_combo.addItem("ounce", "oz")
        elif unit_type == "area":
            self._from_unit_combo.addItem("acre", "acre")
        elif unit_type == "speed":
            self._from_unit_combo.addItem("mph", "mph")
        elif unit_type == "pressure":
            self._from_unit_combo.addItem("PSI", "psi")
        elif unit_type == "temperature":
            self._from_unit_combo.addItem("Fahrenheit", "F")

        self._on_value_changed()

    def _on_value_changed(self) -> None:
        """Convert when value or unit changes."""
        value = self._value_spin.value()
        unit_type = self._unit_type_combo.currentData()
        from_unit = self._from_unit_combo.currentData()

        if not from_unit:
            return

        try:
            # Try local conversion first for speed
            if unit_type in ("rate_volume", "rate_weight"):
                unit_enum = ApplicationRateUnit(from_unit)
                result = convert_locally(value, unit_enum)
                self._imperial_label.setText(result.imperial_display)
                self._metric_label.setText(result.metric_display)
            else:
                # Use API for other conversions
                if unit_type == "volume":
                    success, result = self._api.convert_volume(value, from_unit)
                elif unit_type == "weight":
                    success, result = self._api.convert_weight(value, from_unit)
                elif unit_type == "area":
                    success, result = self._api.convert_area(value)
                elif unit_type == "speed":
                    success, result = self._api.convert_speed(value)
                elif unit_type == "pressure":
                    success, result = self._api.convert_pressure(value)
                elif unit_type == "temperature":
                    success, result = self._api.convert_temperature(value)
                else:
                    return

                if success and isinstance(result, ConversionResult):
                    self._imperial_label.setText(result.imperial_display)
                    self._metric_label.setText(result.metric_display)
                else:
                    # Fallback to local calc for common cases
                    self._imperial_label.setText(f"{value:g}")
                    self._metric_label.setText("--")
        except Exception:
            self._imperial_label.setText(f"{value:g}")
            self._metric_label.setText("Error")

    def _copy_metric(self) -> None:
        """Copy metric value to clipboard."""
        text = self._metric_label.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

        # Visual feedback
        self._copy_btn.setText("Copied!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._copy_btn.setText("Copy"))


class TankMixCalculatorTab(QWidget):
    """Tab for tank mix calculations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_measurement_converter_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = create_header_label("Tank Mix Calculator")
        layout.addWidget(header)

        desc = QLabel("Calculate product amounts per tank based on your sprayer and field size.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Input section
        input_frame = create_card_frame()
        input_layout = QFormLayout(input_frame)
        input_layout.setSpacing(12)
        input_layout.setContentsMargins(16, 16, 16, 16)

        # Tank size
        self._tank_size_spin = QDoubleSpinBox()
        self._tank_size_spin.setRange(50, 10000)
        self._tank_size_spin.setValue(500)
        self._tank_size_spin.setSuffix(" L")
        self._tank_size_spin.setDecimals(0)
        input_layout.addRow("Tank Size:", self._tank_size_spin)

        # Application rate
        self._app_rate_spin = QDoubleSpinBox()
        self._app_rate_spin.setRange(10, 1000)
        self._app_rate_spin.setValue(150)
        self._app_rate_spin.setSuffix(" L/ha")
        self._app_rate_spin.setDecimals(1)
        input_layout.addRow("Application Rate:", self._app_rate_spin)

        # Field size
        self._field_size_spin = QDoubleSpinBox()
        self._field_size_spin.setRange(0.1, 10000)
        self._field_size_spin.setValue(40)
        self._field_size_spin.setSuffix(" ha")
        self._field_size_spin.setDecimals(2)
        input_layout.addRow("Field Size:", self._field_size_spin)

        # Product rate (optional)
        self._product_rate_spin = QDoubleSpinBox()
        self._product_rate_spin.setRange(0, 100)
        self._product_rate_spin.setValue(2.5)
        self._product_rate_spin.setSuffix(" L/ha")
        self._product_rate_spin.setDecimals(3)
        input_layout.addRow("Product Rate:", self._product_rate_spin)

        # Calculate button
        calc_btn = QPushButton("Calculate")
        calc_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_light']};
            }}
        """)
        calc_btn.clicked.connect(self._calculate)
        input_layout.addRow("", calc_btn)

        layout.addWidget(input_frame)

        # Results section
        result_frame = create_result_frame()
        result_layout = QGridLayout(result_frame)
        result_layout.setSpacing(16)
        result_layout.setContentsMargins(16, 16, 16, 16)

        # Result labels
        self._product_per_tank_label = create_result_label("--", large=True)
        self._tanks_needed_label = create_result_label("--", large=True)
        self._coverage_per_tank_label = create_result_label("--")
        self._total_product_label = create_result_label("--")
        self._leftover_label = create_result_label("--")

        # Layout results in grid
        result_layout.addWidget(QLabel("Product per Tank:"), 0, 0)
        result_layout.addWidget(self._product_per_tank_label, 0, 1)
        result_layout.addWidget(QLabel("L"), 0, 2)

        result_layout.addWidget(QLabel("Tanks Needed:"), 1, 0)
        result_layout.addWidget(self._tanks_needed_label, 1, 1)
        result_layout.addWidget(QLabel("tanks"), 1, 2)

        result_layout.addWidget(QLabel("Coverage per Tank:"), 2, 0)
        result_layout.addWidget(self._coverage_per_tank_label, 2, 1)
        result_layout.addWidget(QLabel("ha"), 2, 2)

        result_layout.addWidget(QLabel("Total Product Needed:"), 3, 0)
        result_layout.addWidget(self._total_product_label, 3, 1)
        result_layout.addWidget(QLabel("L"), 3, 2)

        result_layout.addWidget(QLabel("Leftover (last tank):"), 4, 0)
        result_layout.addWidget(self._leftover_label, 4, 1)
        result_layout.addWidget(QLabel("L"), 4, 2)

        layout.addWidget(result_frame)
        layout.addStretch()

    def _calculate(self) -> None:
        """Calculate tank mix amounts."""
        tank_size = self._tank_size_spin.value()
        app_rate = self._app_rate_spin.value()
        field_size = self._field_size_spin.value()
        product_rate = self._product_rate_spin.value() if self._product_rate_spin.value() > 0 else None

        success, result = self._api.calculate_tank_mix(
            tank_size, app_rate, field_size, product_rate
        )

        if success and isinstance(result, TankMixResult):
            self._product_per_tank_label.setText(f"{result.product_per_tank_liters:.2f}")
            self._tanks_needed_label.setText(str(result.tanks_needed))
            self._coverage_per_tank_label.setText(f"{result.coverage_per_tank_ha:.2f}")
            self._total_product_label.setText(f"{result.total_product_needed_liters:.2f}")
            self._leftover_label.setText(f"{result.leftover_liters:.1f}")
        else:
            QMessageBox.warning(self, "Error", f"Calculation failed: {result}")


class ReferenceProductsTab(QWidget):
    """Tab showing reference products with rates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_measurement_converter_api()
        self._products: list[ReferenceProduct] = []
        self._setup_ui()
        self._load_products()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = create_header_label("Reference Products")
        layout.addWidget(header)

        desc = QLabel("Common agricultural chemicals with application rates in both imperial and metric.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Filter bar
        filter_frame = create_card_frame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(12, 8, 12, 8)

        filter_layout.addWidget(QLabel("Category:"))
        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories", None)
        self._category_combo.addItem("Herbicides", "herbicide")
        self._category_combo.addItem("Fungicides", "fungicide")
        self._category_combo.addItem("Insecticides", "insecticide")
        self._category_combo.addItem("Adjuvants", "adjuvant")
        self._category_combo.currentIndexChanged.connect(self._load_products)
        filter_layout.addWidget(self._category_combo)

        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Product name or active ingredient...")
        self._search_input.setMinimumWidth(200)
        self._search_input.textChanged.connect(self._load_products)
        filter_layout.addWidget(self._search_input)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # Products table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Product", "Active Ingredient", "Use Case", "Imperial Rate", "Metric Rate"
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                alternate-background-color: {COLORS['surface_alt']};
                gridline-color: {COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['primary']};
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }}
        """)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)

    def _load_products(self) -> None:
        """Load products from API."""
        category = self._category_combo.currentData()
        search = self._search_input.text().strip() or None

        success, result = self._api.get_reference_products(category, search)

        if success and isinstance(result, list):
            self._products = result
            self._populate_table()
        else:
            self._table.setRowCount(0)

    def _populate_table(self) -> None:
        """Populate table with products."""
        # Count total rows needed (one per rate)
        total_rows = sum(len(p.rates) for p in self._products)
        self._table.setRowCount(total_rows)

        row = 0
        for product in self._products:
            for i, rate in enumerate(product.rates):
                # Product name (only show on first row for this product)
                if i == 0:
                    name_item = QTableWidgetItem(product.name)
                    name_item.setFont(QFont("", -1, QFont.Weight.Bold))
                    self._table.setItem(row, 0, name_item)

                    ai_item = QTableWidgetItem(product.active_ingredient)
                    self._table.setItem(row, 1, ai_item)
                else:
                    self._table.setItem(row, 0, QTableWidgetItem(""))
                    self._table.setItem(row, 1, QTableWidgetItem(""))

                # Use case
                self._table.setItem(row, 2, QTableWidgetItem(rate.use_case))

                # Imperial rate
                imperial_item = QTableWidgetItem(rate.imperial)
                self._table.setItem(row, 3, imperial_item)

                # Metric rate (highlighted)
                metric_item = QTableWidgetItem(rate.metric)
                metric_item.setForeground(QColor(COLORS['primary']))
                metric_item.setFont(QFont("", -1, QFont.Weight.Bold))
                self._table.setItem(row, 4, metric_item)

                row += 1


class MeasurementConverterScreen(QWidget):
    """Main measurement converter screen with tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Screen background
        self.setStyleSheet(f"background-color: {COLORS['surface']};")

        # Title bar
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary']};
                padding: 16px;
            }}
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(20, 12, 20, 12)

        title = QLabel("Unit Converter")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title)

        subtitle = QLabel("Imperial to Metric for Field Operators")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
            }
        """)
        title_layout.addWidget(subtitle)
        title_layout.addStretch()

        layout.addWidget(title_frame)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {COLORS['surface']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['card_bg']};
                color: {COLORS['text']};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['primary_light']};
            }}
        """)

        # Add tabs
        self._tabs.addTab(QuickConverterTab(self), "Quick Converter")
        self._tabs.addTab(TankMixCalculatorTab(self), "Tank Mix Calculator")
        self._tabs.addTab(ReferenceProductsTab(self), "Reference Products")

        layout.addWidget(self._tabs)
