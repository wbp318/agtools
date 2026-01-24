"""
AgTools Yield Response Screen

Interactive yield response curve visualization and Economic Optimum Rate calculator.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QComboBox, QDoubleSpinBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor


# Import pyqtgraph for charting
try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS, set_widget_class
from models.yield_response import (
    Crop, Nutrient, SoilTestLevel, ResponseModel,
    YieldCurveRequest, EORRequest, EORResult,
    CompareRatesRequest, CompareRatesResponse,
)
from api.yield_response_api import get_yield_response_api


class InputPanel(QFrame):
    """Input panel for yield response parameters."""

    inputs_changed = pyqtSignal()
    calculate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header = QLabel("Input Parameters")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Form layout
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Crop selection
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Corn", Crop.CORN.value)
        self._crop_combo.addItem("Soybean", Crop.SOYBEAN.value)
        self._crop_combo.addItem("Wheat", Crop.WHEAT.value)
        self._crop_combo.currentIndexChanged.connect(self._on_input_changed)
        form.addRow("Crop:", self._crop_combo)

        # Nutrient selection
        self._nutrient_combo = QComboBox()
        self._nutrient_combo.addItem("Nitrogen (N)", Nutrient.NITROGEN.value)
        self._nutrient_combo.addItem("Phosphorus (P₂O₅)", Nutrient.PHOSPHORUS.value)
        self._nutrient_combo.addItem("Potassium (K₂O)", Nutrient.POTASSIUM.value)
        self._nutrient_combo.currentIndexChanged.connect(self._on_input_changed)
        form.addRow("Nutrient:", self._nutrient_combo)

        # Soil test level
        self._soil_combo = QComboBox()
        self._soil_combo.addItem("Very Low", SoilTestLevel.VERY_LOW.value)
        self._soil_combo.addItem("Low", SoilTestLevel.LOW.value)
        self._soil_combo.addItem("Medium", SoilTestLevel.MEDIUM.value)
        self._soil_combo.addItem("High", SoilTestLevel.HIGH.value)
        self._soil_combo.addItem("Very High", SoilTestLevel.VERY_HIGH.value)
        self._soil_combo.setCurrentIndex(2)  # Default to Medium
        self._soil_combo.currentIndexChanged.connect(self._on_input_changed)
        form.addRow("Soil Test Level:", self._soil_combo)

        # Yield potential
        self._yield_spin = QSpinBox()
        self._yield_spin.setRange(50, 350)
        self._yield_spin.setValue(200)
        self._yield_spin.setSuffix(" bu/ac")
        self._yield_spin.valueChanged.connect(self._on_input_changed)
        form.addRow("Yield Potential:", self._yield_spin)

        layout.addLayout(form)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Price inputs header
        price_header = QLabel("Price Inputs")
        price_header_font = QFont()
        price_header_font.setPointSize(12)
        price_header_font.setWeight(QFont.Weight.DemiBold)
        price_header.setFont(price_header_font)
        layout.addWidget(price_header)

        price_form = QFormLayout()
        price_form.setSpacing(12)
        price_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Nutrient cost
        self._nutrient_cost_spin = QDoubleSpinBox()
        self._nutrient_cost_spin.setRange(0.10, 3.00)
        self._nutrient_cost_spin.setValue(0.65)
        self._nutrient_cost_spin.setSingleStep(0.05)
        self._nutrient_cost_spin.setPrefix("$")
        self._nutrient_cost_spin.setSuffix("/lb")
        self._nutrient_cost_spin.setDecimals(2)
        self._nutrient_cost_spin.valueChanged.connect(self._on_input_changed)
        price_form.addRow("Nutrient Cost:", self._nutrient_cost_spin)

        # Grain price
        self._grain_price_spin = QDoubleSpinBox()
        self._grain_price_spin.setRange(2.00, 12.00)
        self._grain_price_spin.setValue(4.50)
        self._grain_price_spin.setSingleStep(0.25)
        self._grain_price_spin.setPrefix("$")
        self._grain_price_spin.setSuffix("/bu")
        self._grain_price_spin.setDecimals(2)
        self._grain_price_spin.valueChanged.connect(self._on_input_changed)
        price_form.addRow("Grain Price:", self._grain_price_spin)

        # Field acres
        self._acres_spin = QSpinBox()
        self._acres_spin.setRange(1, 10000)
        self._acres_spin.setValue(100)
        self._acres_spin.setSuffix(" acres")
        self._acres_spin.valueChanged.connect(self._on_input_changed)
        price_form.addRow("Field Size:", self._acres_spin)

        layout.addLayout(price_form)

        # Price ratio display
        self._price_ratio_label = QLabel()
        self._price_ratio_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        self._update_price_ratio()
        layout.addWidget(self._price_ratio_label)

        layout.addStretch()

        # Calculate button
        self._calc_btn = QPushButton("Calculate EOR")
        self._calc_btn.setMinimumHeight(44)
        self._calc_btn.clicked.connect(self.calculate_requested.emit)
        layout.addWidget(self._calc_btn)

        # Response model (advanced)
        model_label = QLabel("Response Model:")
        model_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        layout.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.addItem("Quadratic Plateau", ResponseModel.QUADRATIC_PLATEAU.value)
        self._model_combo.addItem("Quadratic", ResponseModel.QUADRATIC.value)
        self._model_combo.addItem("Linear Plateau", ResponseModel.LINEAR_PLATEAU.value)
        self._model_combo.addItem("Mitscherlich", ResponseModel.MITSCHERLICH.value)
        self._model_combo.addItem("Square Root", ResponseModel.SQUARE_ROOT.value)
        self._model_combo.currentIndexChanged.connect(self._on_input_changed)
        layout.addWidget(self._model_combo)

        self.setMinimumWidth(280)
        self.setMaximumWidth(350)

    def _on_input_changed(self) -> None:
        """Handle input value changes."""
        self._update_price_ratio()
        self.inputs_changed.emit()

    def _update_price_ratio(self) -> None:
        """Update the price ratio display."""
        nutrient_cost = self._nutrient_cost_spin.value()
        grain_price = self._grain_price_spin.value()
        ratio = nutrient_cost / grain_price if grain_price > 0 else 0
        self._price_ratio_label.setText(f"Price Ratio: {ratio:.3f} (N cost ÷ grain price)")

    def get_crop(self) -> str:
        return self._crop_combo.currentData()

    def get_nutrient(self) -> str:
        return self._nutrient_combo.currentData()

    def get_soil_test_level(self) -> str:
        return self._soil_combo.currentData()

    def get_yield_potential(self) -> int:
        return self._yield_spin.value()

    def get_nutrient_cost(self) -> float:
        return self._nutrient_cost_spin.value()

    def get_grain_price(self) -> float:
        return self._grain_price_spin.value()

    def get_acres(self) -> int:
        return self._acres_spin.value()

    def get_response_model(self) -> str:
        return self._model_combo.currentData()

    def get_curve_request(self) -> YieldCurveRequest:
        """Build yield curve request from current inputs."""
        return YieldCurveRequest(
            crop=self.get_crop(),
            nutrient=self.get_nutrient(),
            soil_test_level=self.get_soil_test_level(),
            yield_potential=self.get_yield_potential(),
            response_model=self.get_response_model(),
            min_rate=0,
            max_rate=300 if self.get_nutrient() == "nitrogen" else 150,
            rate_step=5,
        )

    def get_eor_request(self) -> EORRequest:
        """Build EOR request from current inputs."""
        return EORRequest(
            crop=self.get_crop(),
            nutrient=self.get_nutrient(),
            nutrient_cost_per_lb=self.get_nutrient_cost(),
            grain_price_per_bu=self.get_grain_price(),
            soil_test_level=self.get_soil_test_level(),
            yield_potential=self.get_yield_potential(),
            response_model=self.get_response_model(),
            acres=self.get_acres(),
        )


class ResultsPanel(QFrame):
    """Panel displaying EOR calculation results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Economic Optimum Rate")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Main result display
        self._eor_value = QLabel("-- lb/ac")
        eor_font = QFont()
        eor_font.setPointSize(28)
        eor_font.setWeight(QFont.Weight.Bold)
        self._eor_value.setFont(eor_font)
        self._eor_value.setStyleSheet(f"color: {COLORS['primary']};")
        self._eor_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._eor_value)

        # Results grid
        results_grid = QGridLayout()
        results_grid.setSpacing(8)

        self._result_labels = {}
        result_items = [
            ("eor_yield", "Expected Yield", "-- bu/ac"),
            ("max_yield", "Max Yield", "-- bu/ac"),
            ("yield_sacrifice", "Yield Sacrifice", "-- bu/ac"),
            ("net_return", "Net Return at EOR", "$--/ac"),
            ("savings", "Savings vs Max Rate", "$--/ac"),
            ("fert_savings", "Fertilizer Saved", "-- lb/ac"),
        ]

        for i, (key, label, default) in enumerate(result_items):
            row = i // 2
            col = (i % 2) * 2

            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
            results_grid.addWidget(label_widget, row, col)

            value_widget = QLabel(default)
            value_widget.setStyleSheet("font-weight: 600;")
            results_grid.addWidget(value_widget, row, col + 1)
            self._result_labels[key] = value_widget

        layout.addLayout(results_grid)

        # Recommendation
        self._recommendation = QLabel("")
        self._recommendation.setWordWrap(True)
        self._recommendation.setStyleSheet(f"""
            background-color: {COLORS['info_light']};
            border: 1px solid {COLORS['info']};
            border-radius: 4px;
            padding: 12px;
            color: {COLORS['text_primary']};
        """)
        self._recommendation.setVisible(False)
        layout.addWidget(self._recommendation)

        layout.addStretch()

    def update_results(self, result: EORResult) -> None:
        """Update display with EOR results."""
        self._eor_value.setText(f"{result.economic_optimum_rate:.0f} lb/ac")

        self._result_labels["eor_yield"].setText(f"{result.eor_yield:.1f} bu/ac")
        self._result_labels["max_yield"].setText(f"{result.max_yield:.1f} bu/ac")
        self._result_labels["yield_sacrifice"].setText(f"{result.yield_sacrifice:.1f} bu/ac")
        self._result_labels["net_return"].setText(f"${result.net_return_at_eor:.2f}/ac")
        self._result_labels["savings"].setText(f"${result.savings_vs_max:.2f}/ac")
        self._result_labels["fert_savings"].setText(f"{result.fertilizer_savings_lb:.0f} lb/ac")

        if result.recommendation:
            self._recommendation.setText(result.recommendation)
            self._recommendation.setVisible(True)
        else:
            self._recommendation.setVisible(False)

    def clear_results(self) -> None:
        """Clear all results."""
        self._eor_value.setText("-- lb/ac")
        for label in self._result_labels.values():
            label.setText("--")
        self._recommendation.setVisible(False)


class YieldCurveChart(QWidget):
    """Interactive yield response curve chart using pyqtgraph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._eor_line = None
        self._max_yield_line = None

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not HAS_PYQTGRAPH:
            # Fallback if pyqtgraph not installed
            error_label = QLabel("pyqtgraph not installed.\nRun: pip install pyqtgraph")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {COLORS['error']};")
            layout.addWidget(error_label)
            return

        # Configure pyqtgraph
        pg.setConfigOptions(antialias=True, background='w', foreground='k')

        # Create plot widget
        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setLabel('left', 'Yield', units='bu/ac')
        self._plot_widget.setLabel('bottom', 'Application Rate', units='lb/ac')
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.setTitle("Yield Response Curve")

        # Style the plot
        self._plot_widget.getAxis('left').setStyle(tickFont=QFont("Segoe UI", 9))
        self._plot_widget.getAxis('bottom').setStyle(tickFont=QFont("Segoe UI", 9))

        layout.addWidget(self._plot_widget)

        # Legend
        self._legend = self._plot_widget.addLegend(offset=(10, 10))

    def plot_curve(self, curve_data: list, eor: float = None, max_rate: float = None) -> None:
        """Plot yield response curve with optional EOR and max yield markers."""
        if not HAS_PYQTGRAPH:
            return

        # Clear existing plots
        self._plot_widget.clear()
        if self._legend:
            self._legend.clear()

        if not curve_data:
            return

        # Extract data
        rates = [p.rate_lb_per_acre for p in curve_data]
        yields = [p.yield_bu_per_acre for p in curve_data]

        # Plot main curve
        pen = pg.mkPen(color=COLORS['primary'], width=3)
        self._plot_widget.plot(
            rates, yields,
            pen=pen,
            name="Yield Response"
        )

        # Add EOR vertical line
        if eor is not None:
            eor_pen = pg.mkPen(color=COLORS['success'], width=2, style=Qt.PenStyle.DashLine)
            self._eor_line = pg.InfiniteLine(
                pos=eor,
                angle=90,
                pen=eor_pen,
                label=f"EOR: {eor:.0f} lb/ac",
                labelOpts={'position': 0.9, 'color': COLORS['success']}
            )
            self._plot_widget.addItem(self._eor_line)

        # Add max yield vertical line
        if max_rate is not None and max_rate != eor:
            max_pen = pg.mkPen(color=COLORS['warning'], width=2, style=Qt.PenStyle.DotLine)
            self._max_yield_line = pg.InfiniteLine(
                pos=max_rate,
                angle=90,
                pen=max_pen,
                label=f"Max: {max_rate:.0f} lb/ac",
                labelOpts={'position': 0.8, 'color': COLORS['warning']}
            )
            self._plot_widget.addItem(self._max_yield_line)

        # Set axis ranges with padding
        self._plot_widget.setXRange(min(rates), max(rates) * 1.05)
        self._plot_widget.setYRange(min(yields) * 0.95, max(yields) * 1.02)

    def clear_chart(self) -> None:
        """Clear the chart."""
        if HAS_PYQTGRAPH:
            self._plot_widget.clear()


class RateComparisonTable(QWidget):
    """Table comparing different application rates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QLabel("Rate Comparison")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Rate (lb/ac)", "Yield (bu/ac)", "Gross Revenue",
            "Fert. Cost", "Net Return", "Rank"
        ])

        # Configure table
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self._table)

    def update_comparison(self, response: CompareRatesResponse) -> None:
        """Update table with rate comparison data."""
        self._table.setRowCount(len(response.comparisons))

        for row, comp in enumerate(response.comparisons):
            # Highlight best rate
            is_best = comp.rate == response.best_rate

            items = [
                f"{comp.rate:.0f}",
                f"{comp.yield_bu:.1f}",
                f"${comp.gross_revenue:,.0f}",
                f"${comp.fertilizer_cost:,.0f}",
                f"${comp.net_return:,.0f}",
                f"#{comp.rank}",
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if is_best:
                    item.setBackground(QColor(COLORS['success_light']))
                    item.setForeground(QColor(COLORS['primary_dark']))

                self._table.setItem(row, col, item)

    def clear_table(self) -> None:
        """Clear the table."""
        self._table.setRowCount(0)


class YieldResponseScreen(QWidget):
    """
    Main yield response calculator screen.

    Features:
    - Input panel for crop, nutrient, prices
    - Interactive yield curve visualization
    - Economic Optimum Rate calculation
    - Rate comparison table
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_yield_response_api()
        self._current_curve_data = None
        self._current_eor = None
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Initialize the UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left panel - Inputs
        self._input_panel = InputPanel()
        layout.addWidget(self._input_panel)

        # Right panel - Results and Charts
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Top section - Chart and Results side by side
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Chart
        chart_frame = QFrame()
        set_widget_class(chart_frame, "card")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(8, 8, 8, 8)

        self._chart = YieldCurveChart()
        chart_layout.addWidget(self._chart)

        top_splitter.addWidget(chart_frame)

        # Results panel
        self._results_panel = ResultsPanel()
        self._results_panel.setMinimumWidth(280)
        self._results_panel.setMaximumWidth(350)
        top_splitter.addWidget(self._results_panel)

        top_splitter.setSizes([600, 300])
        right_layout.addWidget(top_splitter, 2)

        # Bottom section - Rate comparison table
        table_frame = QFrame()
        set_widget_class(table_frame, "card")
        table_layout = QVBoxLayout(table_frame)

        self._rate_table = RateComparisonTable()
        table_layout.addWidget(self._rate_table)

        right_layout.addWidget(table_frame, 1)

        layout.addWidget(right_panel, 1)

        # Loading indicator
        self._loading_label = QLabel("Calculating...")
        self._loading_label.setStyleSheet(f"""
            background-color: {COLORS['info_light']};
            border: 1px solid {COLORS['info']};
            border-radius: 4px;
            padding: 8px 16px;
            color: {COLORS['info']};
        """)
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setVisible(False)
        self._loading_label.setParent(self)

    def _setup_connections(self) -> None:
        """Setup signal connections."""
        self._input_panel.calculate_requested.connect(self._calculate)

    def _calculate(self) -> None:
        """Perform EOR calculation and update display."""
        self._loading_label.setVisible(True)
        self._loading_label.move(
            self.width() // 2 - 60,
            self.height() // 2 - 20
        )

        # Get curve data
        curve_request = self._input_panel.get_curve_request()
        success, curve_result = self._api.generate_curve(curve_request)

        if not success:
            self._show_error(f"Failed to generate curve: {curve_result}")
            self._loading_label.setVisible(False)
            return

        self._current_curve_data = curve_result

        # Get EOR
        eor_request = self._input_panel.get_eor_request()
        success, eor_result = self._api.calculate_eor(eor_request)

        if not success:
            self._show_error(f"Failed to calculate EOR: {eor_result}")
            self._loading_label.setVisible(False)
            return

        self._current_eor = eor_result

        # Update chart
        self._chart.plot_curve(
            curve_result.curve_data,
            eor=eor_result.economic_optimum_rate,
            max_rate=eor_result.max_yield_rate
        )

        # Update results
        self._results_panel.update_results(eor_result)

        # Get rate comparison (compare EOR, max, and some alternatives)
        eor_rate = eor_result.economic_optimum_rate
        max_rate = eor_result.max_yield_rate

        # Create comparison rates
        rates = sorted(set([
            max(0, eor_rate - 30),
            eor_rate,
            (eor_rate + max_rate) / 2,
            max_rate,
            min(300, max_rate + 30),
        ]))

        compare_request = CompareRatesRequest(
            crop=self._input_panel.get_crop(),
            nutrient=self._input_panel.get_nutrient(),
            rates_to_compare=rates,
            nutrient_cost_per_lb=self._input_panel.get_nutrient_cost(),
            grain_price_per_bu=self._input_panel.get_grain_price(),
            soil_test_level=self._input_panel.get_soil_test_level(),
            yield_potential=self._input_panel.get_yield_potential(),
            acres=self._input_panel.get_acres(),
        )

        success, compare_result = self._api.compare_rates(compare_request)

        if success:
            self._rate_table.update_comparison(compare_result)

        self._loading_label.setVisible(False)

    def _show_error(self, message: str) -> None:
        """Show error message."""
        QMessageBox.warning(self, "Calculation Error", message)

    def resizeEvent(self, event) -> None:
        """Handle resize to reposition loading indicator."""
        super().resizeEvent(event)
        if self._loading_label.isVisible():
            self._loading_label.move(
                self.width() // 2 - 60,
                self.height() // 2 - 20
            )
