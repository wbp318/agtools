"""
AgTools Spray Timing Screen

Weather-smart spray timing evaluation and window finder.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QScrollArea,
    QSizePolicy, QComboBox, QDoubleSpinBox, QSpinBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QTabWidget, QFormLayout, QMessageBox,
    QProgressBar, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS, set_widget_class
from models.spray import (
    SprayType, RiskLevel, DiseasePressure,
    WeatherCondition, EvaluateConditionsRequest, SprayEvaluation,
    CostOfWaitingRequest, CostOfWaitingResult,
)
from api.spray_api import get_spray_timing_api


class WeatherInputPanel(QFrame):
    """Panel for entering current weather conditions."""

    weather_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Current Weather Conditions")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Form layout
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Temperature
        self._temp_spin = QDoubleSpinBox()
        self._temp_spin.setRange(20, 110)
        self._temp_spin.setValue(75)
        self._temp_spin.setSuffix(" °F")
        self._temp_spin.setDecimals(0)
        self._temp_spin.valueChanged.connect(self.weather_changed.emit)
        form.addRow("Temperature:", self._temp_spin)

        # Wind speed
        self._wind_spin = QDoubleSpinBox()
        self._wind_spin.setRange(0, 50)
        self._wind_spin.setValue(5)
        self._wind_spin.setSuffix(" mph")
        self._wind_spin.setDecimals(1)
        self._wind_spin.valueChanged.connect(self.weather_changed.emit)
        form.addRow("Wind Speed:", self._wind_spin)

        # Wind direction
        self._wind_dir_combo = QComboBox()
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        self._wind_dir_combo.addItems(directions)
        self._wind_dir_combo.currentIndexChanged.connect(self.weather_changed.emit)
        form.addRow("Wind Direction:", self._wind_dir_combo)

        # Humidity
        self._humidity_spin = QSpinBox()
        self._humidity_spin.setRange(10, 100)
        self._humidity_spin.setValue(50)
        self._humidity_spin.setSuffix(" %")
        self._humidity_spin.valueChanged.connect(self.weather_changed.emit)
        form.addRow("Humidity:", self._humidity_spin)

        # Rain chance
        self._rain_spin = QSpinBox()
        self._rain_spin.setRange(0, 100)
        self._rain_spin.setValue(10)
        self._rain_spin.setSuffix(" %")
        self._rain_spin.valueChanged.connect(self.weather_changed.emit)
        form.addRow("Rain Chance:", self._rain_spin)

        # Dew point
        self._dewpoint_spin = QDoubleSpinBox()
        self._dewpoint_spin.setRange(20, 80)
        self._dewpoint_spin.setValue(55)
        self._dewpoint_spin.setSuffix(" °F")
        self._dewpoint_spin.setDecimals(0)
        self._dewpoint_spin.valueChanged.connect(self.weather_changed.emit)
        form.addRow("Dew Point:", self._dewpoint_spin)

        # Cloud cover
        self._cloud_spin = QSpinBox()
        self._cloud_spin.setRange(0, 100)
        self._cloud_spin.setValue(30)
        self._cloud_spin.setSuffix(" %")
        self._cloud_spin.valueChanged.connect(self.weather_changed.emit)
        form.addRow("Cloud Cover:", self._cloud_spin)

        layout.addLayout(form)

        # Delta T indicator
        self._delta_t_label = QLabel()
        self._delta_t_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        self._update_delta_t()
        layout.addWidget(self._delta_t_label)

        # Connect for delta T updates
        self._temp_spin.valueChanged.connect(self._update_delta_t)
        self._dewpoint_spin.valueChanged.connect(self._update_delta_t)

    def _update_delta_t(self) -> None:
        """Update Delta T display (temp - dewpoint, ideal is 2-8°F)."""
        delta_t = self._temp_spin.value() - self._dewpoint_spin.value()
        status = "Ideal" if 2 <= delta_t <= 8 else ("Too low - inversion risk" if delta_t < 2 else "High evaporation")
        color = COLORS['success'] if 2 <= delta_t <= 8 else COLORS['warning']
        self._delta_t_label.setText(f"Delta T: {delta_t:.0f}°F ({status})")
        self._delta_t_label.setStyleSheet(f"color: {color}; font-size: 10pt; font-weight: 600;")

    def get_weather(self) -> WeatherCondition:
        """Get current weather values as WeatherCondition."""
        return WeatherCondition(
            temp_f=self._temp_spin.value(),
            wind_mph=self._wind_spin.value(),
            wind_direction=self._wind_dir_combo.currentText(),
            humidity_pct=self._humidity_spin.value(),
            precip_chance_pct=self._rain_spin.value(),
            dew_point_f=self._dewpoint_spin.value(),
            cloud_cover_pct=self._cloud_spin.value(),
        )


class SpraySettingsPanel(QFrame):
    """Panel for spray type and product settings."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Spray Settings")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Spray type
        self._spray_type_combo = QComboBox()
        self._spray_type_combo.addItem("Herbicide", SprayType.HERBICIDE.value)
        self._spray_type_combo.addItem("Insecticide", SprayType.INSECTICIDE.value)
        self._spray_type_combo.addItem("Fungicide", SprayType.FUNGICIDE.value)
        self._spray_type_combo.addItem("Growth Regulator", SprayType.GROWTH_REGULATOR.value)
        self._spray_type_combo.addItem("Desiccant", SprayType.DESICCANT.value)
        self._spray_type_combo.currentIndexChanged.connect(self.settings_changed.emit)
        form.addRow("Spray Type:", self._spray_type_combo)

        # Product name (optional)
        self._product_input = QLineEdit()
        self._product_input.setPlaceholderText("e.g., Roundup PowerMax")
        self._product_input.textChanged.connect(self.settings_changed.emit)
        form.addRow("Product:", self._product_input)

        layout.addLayout(form)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Cost inputs header
        cost_header = QLabel("Cost Analysis Inputs")
        cost_header_font = QFont()
        cost_header_font.setPointSize(11)
        cost_header_font.setWeight(QFont.Weight.DemiBold)
        cost_header.setFont(cost_header_font)
        layout.addWidget(cost_header)

        cost_form = QFormLayout()
        cost_form.setSpacing(10)
        cost_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Acres
        self._acres_spin = QSpinBox()
        self._acres_spin.setRange(1, 10000)
        self._acres_spin.setValue(160)
        self._acres_spin.setSuffix(" ac")
        cost_form.addRow("Field Size:", self._acres_spin)

        # Product cost
        self._product_cost_spin = QDoubleSpinBox()
        self._product_cost_spin.setRange(0, 100)
        self._product_cost_spin.setValue(15.00)
        self._product_cost_spin.setPrefix("$")
        self._product_cost_spin.setSuffix("/ac")
        self._product_cost_spin.setDecimals(2)
        cost_form.addRow("Product Cost:", self._product_cost_spin)

        # Application cost
        self._app_cost_spin = QDoubleSpinBox()
        self._app_cost_spin.setRange(0, 50)
        self._app_cost_spin.setValue(8.50)
        self._app_cost_spin.setPrefix("$")
        self._app_cost_spin.setSuffix("/ac")
        self._app_cost_spin.setDecimals(2)
        cost_form.addRow("Application Cost:", self._app_cost_spin)

        # Crop
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Corn", "corn")
        self._crop_combo.addItem("Soybean", "soybean")
        self._crop_combo.addItem("Wheat", "wheat")
        cost_form.addRow("Crop:", self._crop_combo)

        # Yield goal
        self._yield_spin = QSpinBox()
        self._yield_spin.setRange(20, 350)
        self._yield_spin.setValue(200)
        self._yield_spin.setSuffix(" bu/ac")
        cost_form.addRow("Yield Goal:", self._yield_spin)

        # Grain price
        self._grain_price_spin = QDoubleSpinBox()
        self._grain_price_spin.setRange(2, 20)
        self._grain_price_spin.setValue(4.50)
        self._grain_price_spin.setPrefix("$")
        self._grain_price_spin.setSuffix("/bu")
        self._grain_price_spin.setDecimals(2)
        cost_form.addRow("Grain Price:", self._grain_price_spin)

        layout.addLayout(cost_form)
        layout.addStretch()

    def get_spray_type(self) -> str:
        return self._spray_type_combo.currentData()

    def get_product_name(self) -> str:
        return self._product_input.text() or None

    def get_acres(self) -> int:
        return self._acres_spin.value()

    def get_product_cost(self) -> float:
        return self._product_cost_spin.value()

    def get_app_cost(self) -> float:
        return self._app_cost_spin.value()

    def get_crop(self) -> str:
        return self._crop_combo.currentData()

    def get_yield_goal(self) -> int:
        return self._yield_spin.value()

    def get_grain_price(self) -> float:
        return self._grain_price_spin.value()


class RiskIndicator(QFrame):
    """Visual risk level indicator with color coding."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Risk level text
        self._risk_label = QLabel("--")
        risk_font = QFont()
        risk_font.setPointSize(20)
        risk_font.setWeight(QFont.Weight.Bold)
        self._risk_label.setFont(risk_font)
        self._risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._risk_label)

        # Score
        self._score_label = QLabel("Score: --")
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._score_label)

        # Progress bar as visual indicator
        self._score_bar = QProgressBar()
        self._score_bar.setRange(0, 100)
        self._score_bar.setValue(0)
        self._score_bar.setTextVisible(False)
        self._score_bar.setFixedHeight(8)
        layout.addWidget(self._score_bar)

        self._set_style("unknown")

    def _set_style(self, risk_level: str) -> None:
        """Apply styling based on risk level."""
        colors = {
            "excellent": (COLORS['success'], COLORS['success_light']),
            "good": ("#66BB6A", "#C8E6C9"),
            "marginal": (COLORS['warning'], COLORS['warning_light']),
            "poor": ("#EF5350", COLORS['error_light']),
            "do_not_spray": (COLORS['error'], COLORS['error_light']),
            "unknown": (COLORS['text_disabled'], COLORS['surface_variant']),
        }

        primary, bg = colors.get(risk_level.lower(), colors["unknown"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {primary};
                border-radius: 8px;
            }}
        """)
        self._risk_label.setStyleSheet(f"color: {primary}; background: transparent;")
        self._score_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['surface']};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {primary};
                border-radius: 4px;
            }}
        """)

    def set_evaluation(self, evaluation: SprayEvaluation) -> None:
        """Update display with evaluation results."""
        risk_display = {
            "excellent": "EXCELLENT",
            "good": "GOOD",
            "marginal": "MARGINAL",
            "poor": "POOR",
            "do_not_spray": "DO NOT SPRAY",
        }

        self._risk_label.setText(risk_display.get(evaluation.risk_level.lower(), evaluation.risk_level.upper()))
        self._score_label.setText(f"Score: {evaluation.overall_score:.0f}/100")
        self._score_bar.setValue(int(evaluation.overall_score))
        self._set_style(evaluation.risk_level)

    def clear(self) -> None:
        """Reset to default state."""
        self._risk_label.setText("--")
        self._score_label.setText("Score: --")
        self._score_bar.setValue(0)
        self._set_style("unknown")


class ConditionsTable(QWidget):
    """Table showing individual weather factor assessments."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Condition Assessment")
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Factor", "Status", "Details"])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)

    def update_conditions(self, conditions: list) -> None:
        """Update table with condition assessments."""
        self._table.setRowCount(len(conditions))

        status_colors = {
            "suitable": COLORS['success'],
            "marginal": COLORS['warning'],
            "unsuitable": COLORS['error'],
        }

        for row, cond in enumerate(conditions):
            # Factor name
            factor_item = QTableWidgetItem(cond.factor.replace("_", " ").title())
            self._table.setItem(row, 0, factor_item)

            # Status with color
            status_item = QTableWidgetItem(cond.status.upper())
            status_item.setForeground(QColor(status_colors.get(cond.status.lower(), COLORS['text_primary'])))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 1, status_item)

            # Message
            msg = cond.message or f"Value: {cond.value}"
            msg_item = QTableWidgetItem(msg)
            self._table.setItem(row, 2, msg_item)

    def clear(self) -> None:
        """Clear the table."""
        self._table.setRowCount(0)


class RecommendationsPanel(QFrame):
    """Panel showing concerns and recommendations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Concerns section
        concerns_header = QLabel("Concerns")
        concerns_header.setStyleSheet(f"color: {COLORS['warning']}; font-weight: 600;")
        layout.addWidget(concerns_header)

        self._concerns_label = QLabel("No concerns identified")
        self._concerns_label.setWordWrap(True)
        self._concerns_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._concerns_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Recommendations section
        rec_header = QLabel("Recommendations")
        rec_header.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        layout.addWidget(rec_header)

        self._recommendations_label = QLabel("Enter weather conditions and evaluate")
        self._recommendations_label.setWordWrap(True)
        self._recommendations_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._recommendations_label)

        layout.addStretch()

    def update_content(self, concerns: list, recommendations: list) -> None:
        """Update concerns and recommendations."""
        if concerns:
            self._concerns_label.setText("\n".join(f"• {c}" for c in concerns))
            self._concerns_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        else:
            self._concerns_label.setText("No concerns identified")
            self._concerns_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        if recommendations:
            self._recommendations_label.setText("\n".join(f"• {r}" for r in recommendations))
            self._recommendations_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        else:
            self._recommendations_label.setText("Conditions look good for spraying")
            self._recommendations_label.setStyleSheet(f"color: {COLORS['success']};")

    def clear(self) -> None:
        """Reset to default state."""
        self._concerns_label.setText("No concerns identified")
        self._concerns_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self._recommendations_label.setText("Enter weather conditions and evaluate")
        self._recommendations_label.setStyleSheet(f"color: {COLORS['text_secondary']};")


class CostOfWaitingPanel(QFrame):
    """Panel showing cost of waiting analysis."""

    def __init__(self, parent=None):
        super().__init__(parent)
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Spray Now vs. Wait Analysis")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Recommendation display
        self._rec_label = QLabel("--")
        rec_font = QFont()
        rec_font.setPointSize(16)
        rec_font.setWeight(QFont.Weight.Bold)
        self._rec_label.setFont(rec_font)
        self._rec_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rec_label.setStyleSheet(f"color: {COLORS['text_disabled']};")
        layout.addWidget(self._rec_label)

        # Reasoning
        self._reasoning_label = QLabel("")
        self._reasoning_label.setWordWrap(True)
        self._reasoning_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._reasoning_label)

        # Cost comparison grid
        cost_grid = QGridLayout()
        cost_grid.setSpacing(8)

        cost_grid.addWidget(QLabel("Cost to spray now:"), 0, 0)
        self._cost_now_label = QLabel("$--")
        self._cost_now_label.setStyleSheet("font-weight: 600;")
        cost_grid.addWidget(self._cost_now_label, 0, 1)

        cost_grid.addWidget(QLabel("Cost to wait:"), 1, 0)
        self._cost_wait_label = QLabel("$--")
        self._cost_wait_label.setStyleSheet("font-weight: 600;")
        cost_grid.addWidget(self._cost_wait_label, 1, 1)

        cost_grid.addWidget(QLabel("Yield loss risk:"), 2, 0)
        self._yield_risk_label = QLabel("--%")
        self._yield_risk_label.setStyleSheet("font-weight: 600;")
        cost_grid.addWidget(self._yield_risk_label, 2, 1)

        layout.addLayout(cost_grid)

        # Action items
        self._actions_label = QLabel("")
        self._actions_label.setWordWrap(True)
        self._actions_label.setStyleSheet(f"""
            background-color: {COLORS['info_light']};
            border: 1px solid {COLORS['info']};
            border-radius: 4px;
            padding: 8px;
        """)
        self._actions_label.setVisible(False)
        layout.addWidget(self._actions_label)

        layout.addStretch()

    def update_result(self, result: CostOfWaitingResult) -> None:
        """Update display with cost of waiting results."""
        # Color code recommendation
        rec_colors = {
            "SPRAY NOW": COLORS['success'],
            "WAIT": COLORS['warning'],
            "SPRAY NOW (WITH CAUTION)": COLORS['warning'],
        }

        self._rec_label.setText(result.recommendation)
        color = rec_colors.get(result.recommendation.upper(), COLORS['text_primary'])
        self._rec_label.setStyleSheet(f"color: {color};")

        self._reasoning_label.setText(result.reasoning)

        self._cost_now_label.setText(f"${result.cost_to_spray_now:,.0f}")
        self._cost_wait_label.setText(f"${result.cost_to_wait:,.0f}")
        self._yield_risk_label.setText(f"{result.yield_loss_risk * 100:.0f}%")

        if result.action_items:
            self._actions_label.setText("Action Items:\n" + "\n".join(f"• {a}" for a in result.action_items))
            self._actions_label.setVisible(True)
        else:
            self._actions_label.setVisible(False)

    def clear(self) -> None:
        """Reset to default state."""
        self._rec_label.setText("--")
        self._rec_label.setStyleSheet(f"color: {COLORS['text_disabled']};")
        self._reasoning_label.setText("")
        self._cost_now_label.setText("$--")
        self._cost_wait_label.setText("$--")
        self._yield_risk_label.setText("--%")
        self._actions_label.setVisible(False)


class SprayTimingScreen(QWidget):
    """
    Main spray timing screen.

    Features:
    - Weather condition inputs
    - Spray type and product selection
    - Risk level evaluation with visual indicator
    - Condition-by-condition assessment table
    - Concerns and recommendations
    - Cost of waiting analysis
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_spray_timing_api()
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Initialize the UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left panel - Inputs
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Weather inputs
        self._weather_panel = WeatherInputPanel()
        left_layout.addWidget(self._weather_panel)

        # Spray settings
        self._settings_panel = SpraySettingsPanel()
        left_layout.addWidget(self._settings_panel)

        # Evaluate button
        self._evaluate_btn = QPushButton("Evaluate Conditions")
        self._evaluate_btn.setMinimumHeight(44)
        self._evaluate_btn.clicked.connect(self._evaluate)
        left_layout.addWidget(self._evaluate_btn)

        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(380)
        layout.addWidget(left_panel)

        # Right panel - Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Top row - Risk indicator and conditions table
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Risk indicator
        self._risk_indicator = RiskIndicator()
        self._risk_indicator.setMinimumSize(200, 120)
        self._risk_indicator.setMaximumSize(250, 140)
        top_row.addWidget(self._risk_indicator)

        # Conditions table
        conditions_frame = QFrame()
        set_widget_class(conditions_frame, "card")
        conditions_layout = QVBoxLayout(conditions_frame)
        self._conditions_table = ConditionsTable()
        conditions_layout.addWidget(self._conditions_table)
        top_row.addWidget(conditions_frame, 1)

        right_layout.addLayout(top_row)

        # Middle row - Recommendations and Cost of Waiting
        middle_splitter = QSplitter(Qt.Orientation.Horizontal)

        self._recommendations_panel = RecommendationsPanel()
        middle_splitter.addWidget(self._recommendations_panel)

        self._cost_panel = CostOfWaitingPanel()
        middle_splitter.addWidget(self._cost_panel)

        middle_splitter.setSizes([400, 400])
        right_layout.addWidget(middle_splitter, 1)

        layout.addWidget(right_panel, 1)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        pass  # Evaluate on button click only

    def _evaluate(self) -> None:
        """Evaluate current spray conditions."""
        weather = self._weather_panel.get_weather()

        # Build request
        request = EvaluateConditionsRequest(
            weather=weather,
            spray_type=self._settings_panel.get_spray_type(),
            product_name=self._settings_panel.get_product_name(),
        )

        # Call API
        success, result = self._api.evaluate_conditions(request)

        if not success:
            QMessageBox.warning(self, "Evaluation Error", f"Failed to evaluate conditions: {result}")
            return

        # Update UI
        self._risk_indicator.set_evaluation(result)
        self._conditions_table.update_conditions(result.conditions)
        self._recommendations_panel.update_content(result.concerns, result.recommendations)

        # Also do cost of waiting analysis
        self._analyze_cost_of_waiting(weather)

    def _analyze_cost_of_waiting(self, current_weather: WeatherCondition) -> None:
        """Perform cost of waiting analysis."""
        request = CostOfWaitingRequest(
            current_conditions=current_weather,
            forecast=[],  # Would need actual forecast data
            spray_type=self._settings_panel.get_spray_type(),
            acres=self._settings_panel.get_acres(),
            product_cost_per_acre=self._settings_panel.get_product_cost(),
            application_cost_per_acre=self._settings_panel.get_app_cost(),
            crop=self._settings_panel.get_crop(),
            yield_goal=self._settings_panel.get_yield_goal(),
            grain_price=self._settings_panel.get_grain_price(),
        )

        success, result = self._api.cost_of_waiting(request)

        if success:
            self._cost_panel.update_result(result)
        else:
            self._cost_panel.clear()
