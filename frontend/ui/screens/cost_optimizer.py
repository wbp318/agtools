"""
AgTools Cost Optimizer Screen

Tabbed interface for comprehensive input cost optimization.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QComboBox, QDoubleSpinBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QFormLayout, QMessageBox,
    QCheckBox
)
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS, set_widget_class
from models.cost_optimizer import (
    QuickEstimateRequest, FertilizerRequest, IrrigationCostRequest,
)
from api.cost_optimizer_api import get_cost_optimizer_api


class CostSummaryCard(QFrame):
    """Card displaying a cost summary with breakdown."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        set_widget_class(self, "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(self._title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Total value
        self._total_label = QLabel("$0")
        total_font = QFont()
        total_font.setPointSize(20)
        total_font.setWeight(QFont.Weight.Bold)
        self._total_label.setFont(total_font)
        self._total_label.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(self._total_label)

        # Per acre
        self._per_acre_label = QLabel("$0/acre")
        self._per_acre_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._per_acre_label)

        # Breakdown table
        self._breakdown_layout = QVBoxLayout()
        layout.addLayout(self._breakdown_layout)

        layout.addStretch()

    def set_values(self, total: float, per_acre: float, breakdown: dict = None) -> None:
        """Update the card values."""
        self._total_label.setText(f"${total:,.0f}")
        self._per_acre_label.setText(f"${per_acre:.2f}/acre")

        # Clear old breakdown
        while self._breakdown_layout.count():
            item = self._breakdown_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new breakdown
        if breakdown:
            for key, value in breakdown.items():
                row = QHBoxLayout()
                key_label = QLabel(key.replace("_", " ").title() + ":")
                key_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
                val_label = QLabel(f"${value:,.0f}")
                val_label.setStyleSheet("font-size: 10pt;")
                row.addWidget(key_label)
                row.addStretch()
                row.addWidget(val_label)

                container = QWidget()
                container.setLayout(row)
                self._breakdown_layout.addWidget(container)


class QuickEstimateTab(QWidget):
    """Quick estimate tab using industry averages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_cost_optimizer_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left - Inputs
        input_frame = QFrame()
        set_widget_class(input_frame, "card")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(12)

        header = QLabel("Quick Cost Estimate")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        input_layout.addWidget(header)

        desc = QLabel("Get a fast estimate using industry averages.\nGreat for initial planning.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        input_layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(10)

        # Crop
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Corn", "corn")
        self._crop_combo.addItem("Soybean", "soybean")
        self._crop_combo.addItem("Wheat", "wheat")
        form.addRow("Crop:", self._crop_combo)

        # Acres
        self._acres_spin = QSpinBox()
        self._acres_spin.setRange(1, 50000)
        self._acres_spin.setValue(500)
        self._acres_spin.setSuffix(" acres")
        form.addRow("Total Acres:", self._acres_spin)

        # Yield goal
        self._yield_spin = QSpinBox()
        self._yield_spin.setRange(20, 350)
        self._yield_spin.setValue(200)
        self._yield_spin.setSuffix(" bu/ac")
        form.addRow("Yield Goal:", self._yield_spin)

        # Irrigated
        self._irrigated_check = QCheckBox("Field is irrigated")
        form.addRow("", self._irrigated_check)

        input_layout.addLayout(form)
        input_layout.addStretch()

        # Calculate button
        calc_btn = QPushButton("Calculate Estimate")
        calc_btn.setMinimumHeight(44)
        calc_btn.clicked.connect(self._calculate)
        input_layout.addWidget(calc_btn)

        input_frame.setMaximumWidth(350)
        layout.addWidget(input_frame)

        # Right - Results
        results_frame = QWidget()
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(16)

        # Summary cards row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._total_card = CostSummaryCard("Total Input Cost")
        cards_layout.addWidget(self._total_card)

        self._revenue_card = CostSummaryCard("Gross Revenue")
        cards_layout.addWidget(self._revenue_card)

        self._profit_card = CostSummaryCard("Net Return")
        cards_layout.addWidget(self._profit_card)

        results_layout.addLayout(cards_layout)

        # Cost breakdown
        breakdown_frame = QFrame()
        set_widget_class(breakdown_frame, "card")
        breakdown_layout = QVBoxLayout(breakdown_frame)

        breakdown_header = QLabel("Cost Breakdown (per acre)")
        breakdown_header_font = QFont()
        breakdown_header_font.setPointSize(12)
        breakdown_header_font.setWeight(QFont.Weight.DemiBold)
        breakdown_header.setFont(breakdown_header_font)
        breakdown_layout.addWidget(breakdown_header)

        self._breakdown_table = QTableWidget()
        self._breakdown_table.setColumnCount(3)
        self._breakdown_table.setHorizontalHeaderLabels(["Category", "Cost/Acre", "Total Cost"])
        header = self._breakdown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._breakdown_table.setAlternatingRowColors(True)
        self._breakdown_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        breakdown_layout.addWidget(self._breakdown_table)

        results_layout.addWidget(breakdown_frame)

        # Savings potential
        savings_frame = QFrame()
        set_widget_class(savings_frame, "card")
        savings_layout = QVBoxLayout(savings_frame)

        savings_header = QLabel("Optimization Potential")
        savings_header.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        savings_layout.addWidget(savings_header)

        self._savings_label = QLabel("Run estimate to see potential savings")
        self._savings_label.setWordWrap(True)
        savings_layout.addWidget(self._savings_label)

        results_layout.addWidget(savings_frame)

        layout.addWidget(results_frame, 1)

    def _calculate(self) -> None:
        """Calculate quick estimate."""
        request = QuickEstimateRequest(
            acres=self._acres_spin.value(),
            crop=self._crop_combo.currentData(),
            is_irrigated=self._irrigated_check.isChecked(),
            yield_goal=self._yield_spin.value(),
        )

        success, result = self._api.quick_estimate(request)

        if not success:
            QMessageBox.warning(self, "Error", f"Failed to calculate: {result}")
            return

        # Update cards
        self._total_card.set_values(
            result.total_cost,
            result.total_cost_per_acre,
            result.cost_breakdown
        )

        self._revenue_card.set_values(
            result.gross_revenue,
            result.gross_revenue / result.acres if result.acres > 0 else 0
        )

        profit_color = COLORS['success'] if result.net_return > 0 else COLORS['error']
        self._profit_card._total_label.setStyleSheet(f"color: {profit_color};")
        self._profit_card.set_values(
            result.net_return,
            result.return_per_acre
        )

        # Update breakdown table
        breakdown = result.cost_breakdown
        self._breakdown_table.setRowCount(len(breakdown))
        acres = result.acres

        for row, (cat, cost_per_acre) in enumerate(breakdown.items()):
            self._breakdown_table.setItem(row, 0, QTableWidgetItem(cat.replace("_", " ").title()))
            self._breakdown_table.setItem(row, 1, QTableWidgetItem(f"${cost_per_acre:.2f}"))
            self._breakdown_table.setItem(row, 2, QTableWidgetItem(f"${cost_per_acre * acres:,.0f}"))

        # Update savings
        self._savings_label.setText(
            f"Based on typical optimization opportunities:\n\n"
            f"Potential savings: ${result.potential_savings_low:,.0f} - ${result.potential_savings_high:,.0f}\n"
            f"(10-20% of total input costs)\n\n"
            f"Break-even yield: {result.break_even_yield:.1f} bu/ac"
        )
        self._savings_label.setStyleSheet(f"color: {COLORS['text_primary']};")


class FertilizerTab(QWidget):
    """Fertilizer optimization tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_cost_optimizer_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left - Inputs
        input_frame = QFrame()
        set_widget_class(input_frame, "card")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(12)

        header = QLabel("Fertilizer Optimization")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        input_layout.addWidget(header)

        desc = QLabel("Optimize fertilizer based on soil tests and yield goals.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        input_layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(10)

        # Crop
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Corn", "corn")
        self._crop_combo.addItem("Soybean", "soybean")
        self._crop_combo.addItem("Wheat", "wheat")
        form.addRow("Crop:", self._crop_combo)

        # Acres
        self._acres_spin = QSpinBox()
        self._acres_spin.setRange(1, 50000)
        self._acres_spin.setValue(160)
        self._acres_spin.setSuffix(" acres")
        form.addRow("Field Size:", self._acres_spin)

        # Yield goal
        self._yield_spin = QSpinBox()
        self._yield_spin.setRange(20, 350)
        self._yield_spin.setValue(200)
        self._yield_spin.setSuffix(" bu/ac")
        form.addRow("Yield Goal:", self._yield_spin)

        input_layout.addLayout(form)

        # Soil test section
        soil_header = QLabel("Soil Test Results")
        soil_header.setStyleSheet("font-weight: 600; margin-top: 8px;")
        input_layout.addWidget(soil_header)

        soil_form = QFormLayout()
        soil_form.setSpacing(10)

        # P
        self._p_spin = QDoubleSpinBox()
        self._p_spin.setRange(0, 100)
        self._p_spin.setValue(20)
        self._p_spin.setSuffix(" ppm")
        self._p_spin.setDecimals(1)
        soil_form.addRow("Phosphorus (P):", self._p_spin)

        # K
        self._k_spin = QDoubleSpinBox()
        self._k_spin.setRange(0, 400)
        self._k_spin.setValue(150)
        self._k_spin.setSuffix(" ppm")
        self._k_spin.setDecimals(0)
        soil_form.addRow("Potassium (K):", self._k_spin)

        # pH
        self._ph_spin = QDoubleSpinBox()
        self._ph_spin.setRange(4.0, 9.0)
        self._ph_spin.setValue(6.5)
        self._ph_spin.setDecimals(1)
        soil_form.addRow("pH:", self._ph_spin)

        # Previous crop
        self._prev_crop_combo = QComboBox()
        self._prev_crop_combo.addItem("None / Other", None)
        self._prev_crop_combo.addItem("Soybean (N credit)", "soybean")
        self._prev_crop_combo.addItem("Alfalfa (N credit)", "alfalfa")
        self._prev_crop_combo.addItem("Corn", "corn")
        soil_form.addRow("Previous Crop:", self._prev_crop_combo)

        input_layout.addLayout(soil_form)
        input_layout.addStretch()

        # Calculate button
        calc_btn = QPushButton("Optimize Fertilizer")
        calc_btn.setMinimumHeight(44)
        calc_btn.clicked.connect(self._calculate)
        input_layout.addWidget(calc_btn)

        input_frame.setMaximumWidth(350)
        layout.addWidget(input_frame)

        # Right - Results
        results_frame = QFrame()
        set_widget_class(results_frame, "card")
        results_layout = QVBoxLayout(results_frame)

        results_header = QLabel("Fertilizer Recommendations")
        results_header_font = QFont()
        results_header_font.setPointSize(14)
        results_header_font.setWeight(QFont.Weight.DemiBold)
        results_header.setFont(results_header_font)
        results_layout.addWidget(results_header)

        # Results table
        self._results_table = QTableWidget()
        self._results_table.setColumnCount(4)
        self._results_table.setHorizontalHeaderLabels([
            "Nutrient", "Rate (lb/ac)", "Product", "Cost/Acre"
        ])
        header = self._results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._results_table.setAlternatingRowColors(True)
        self._results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        results_layout.addWidget(self._results_table)

        # Totals
        totals_layout = QHBoxLayout()

        self._total_cost_label = QLabel("Total Cost: $--")
        self._total_cost_label.setStyleSheet(f"font-size: 14pt; font-weight: 600; color: {COLORS['primary']};")
        totals_layout.addWidget(self._total_cost_label)

        totals_layout.addStretch()

        self._cost_per_acre_label = QLabel("$--/acre")
        self._cost_per_acre_label.setStyleSheet(f"font-size: 12pt; color: {COLORS['text_secondary']};")
        totals_layout.addWidget(self._cost_per_acre_label)

        results_layout.addLayout(totals_layout)

        layout.addWidget(results_frame, 1)

    def _calculate(self) -> None:
        """Calculate fertilizer optimization."""
        request = FertilizerRequest(
            crop=self._crop_combo.currentData(),
            acres=self._acres_spin.value(),
            yield_goal=self._yield_spin.value(),
            soil_test_p_ppm=self._p_spin.value(),
            soil_test_k_ppm=self._k_spin.value(),
            soil_test_ph=self._ph_spin.value(),
            previous_crop=self._prev_crop_combo.currentData(),
        )

        success, result = self._api.optimize_fertilizer(request)

        if not success:
            QMessageBox.warning(self, "Error", f"Failed to optimize: {result}")
            return

        # Update table
        self._results_table.setRowCount(len(result.recommendations))
        for row, rec in enumerate(result.recommendations):
            self._results_table.setItem(row, 0, QTableWidgetItem(rec.nutrient.upper()))
            self._results_table.setItem(row, 1, QTableWidgetItem(f"{rec.recommended_rate:.0f}"))
            self._results_table.setItem(row, 2, QTableWidgetItem(rec.recommended_product))
            self._results_table.setItem(row, 3, QTableWidgetItem(f"${rec.cost_per_acre:.2f}"))

        # Update totals
        self._total_cost_label.setText(f"Total Cost: ${result.total_cost:,.0f}")
        self._cost_per_acre_label.setText(f"${result.total_cost_per_acre:.2f}/acre")


class IrrigationTab(QWidget):
    """Irrigation cost analysis tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_cost_optimizer_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left - Inputs
        input_frame = QFrame()
        set_widget_class(input_frame, "card")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(12)

        header = QLabel("Irrigation Cost Analysis")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        input_layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        # System type
        self._system_combo = QComboBox()
        self._system_combo.addItem("Center Pivot", "center_pivot")
        self._system_combo.addItem("Drip", "drip")
        self._system_combo.addItem("Sprinkler", "sprinkler")
        self._system_combo.addItem("Flood", "flood")
        self._system_combo.addItem("Furrow", "furrow")
        form.addRow("System Type:", self._system_combo)

        # Acres
        self._acres_spin = QSpinBox()
        self._acres_spin.setRange(1, 5000)
        self._acres_spin.setValue(125)
        self._acres_spin.setSuffix(" acres")
        form.addRow("Irrigated Acres:", self._acres_spin)

        # Crop
        self._crop_combo = QComboBox()
        self._crop_combo.addItem("Corn", "corn")
        self._crop_combo.addItem("Soybean", "soybean")
        self._crop_combo.addItem("Wheat", "wheat")
        form.addRow("Crop:", self._crop_combo)

        # Water applied
        self._water_spin = QDoubleSpinBox()
        self._water_spin.setRange(0, 30)
        self._water_spin.setValue(12)
        self._water_spin.setSuffix(" inches")
        self._water_spin.setDecimals(1)
        form.addRow("Water Applied:", self._water_spin)

        # Pumping depth
        self._depth_spin = QSpinBox()
        self._depth_spin.setRange(0, 1000)
        self._depth_spin.setValue(200)
        self._depth_spin.setSuffix(" ft")
        form.addRow("Pumping Depth:", self._depth_spin)

        input_layout.addLayout(form)

        # Cost inputs
        cost_header = QLabel("Cost Inputs")
        cost_header.setStyleSheet("font-weight: 600; margin-top: 8px;")
        input_layout.addWidget(cost_header)

        cost_form = QFormLayout()
        cost_form.setSpacing(10)

        self._water_cost_spin = QDoubleSpinBox()
        self._water_cost_spin.setRange(0, 50)
        self._water_cost_spin.setValue(5.00)
        self._water_cost_spin.setPrefix("$")
        self._water_cost_spin.setSuffix("/ac-in")
        self._water_cost_spin.setDecimals(2)
        cost_form.addRow("Water Cost:", self._water_cost_spin)

        self._elec_spin = QDoubleSpinBox()
        self._elec_spin.setRange(0.01, 0.50)
        self._elec_spin.setValue(0.10)
        self._elec_spin.setPrefix("$")
        self._elec_spin.setSuffix("/kWh")
        self._elec_spin.setDecimals(2)
        cost_form.addRow("Electricity:", self._elec_spin)

        input_layout.addLayout(cost_form)
        input_layout.addStretch()

        # Calculate button
        calc_btn = QPushButton("Analyze Costs")
        calc_btn.setMinimumHeight(44)
        calc_btn.clicked.connect(self._calculate)
        input_layout.addWidget(calc_btn)

        input_frame.setMaximumWidth(350)
        layout.addWidget(input_frame)

        # Right - Results
        results_frame = QWidget()
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(16)

        # Cost cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._variable_card = CostSummaryCard("Variable Costs")
        cards_layout.addWidget(self._variable_card)

        self._fixed_card = CostSummaryCard("Fixed Costs")
        cards_layout.addWidget(self._fixed_card)

        self._total_card = CostSummaryCard("Total Cost")
        cards_layout.addWidget(self._total_card)

        results_layout.addLayout(cards_layout)

        # Details
        details_frame = QFrame()
        set_widget_class(details_frame, "card")
        details_layout = QVBoxLayout(details_frame)

        details_header = QLabel("Cost Details")
        details_header_font = QFont()
        details_header_font.setPointSize(12)
        details_header_font.setWeight(QFont.Weight.DemiBold)
        details_header.setFont(details_header_font)
        details_layout.addWidget(details_header)

        self._details_grid = QGridLayout()
        self._details_grid.setSpacing(8)

        details_items = [
            ("water_cost", "Water Cost"),
            ("pumping_cost", "Pumping/Energy Cost"),
            ("maintenance_cost", "Maintenance"),
            ("efficiency", "System Efficiency"),
            ("cost_per_inch", "Cost per Acre-Inch"),
        ]

        for i, (key, label) in enumerate(details_items):
            row = i // 2
            col = (i % 2) * 2

            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self._details_grid.addWidget(label_widget, row, col)

            value_widget = QLabel("--")
            value_widget.setObjectName(key)
            value_widget.setStyleSheet("font-weight: 600;")
            self._details_grid.addWidget(value_widget, row, col + 1)

        details_layout.addLayout(self._details_grid)
        results_layout.addWidget(details_frame)

        # Savings potential
        savings_frame = QFrame()
        set_widget_class(savings_frame, "card")
        savings_layout = QVBoxLayout(savings_frame)

        savings_header = QLabel("Potential Savings")
        savings_header.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        savings_layout.addWidget(savings_header)

        self._savings_label = QLabel("Run analysis to see savings opportunities")
        self._savings_label.setWordWrap(True)
        savings_layout.addWidget(self._savings_label)

        results_layout.addWidget(savings_frame)

        layout.addWidget(results_frame, 1)

    def _calculate(self) -> None:
        """Calculate irrigation costs."""
        request = IrrigationCostRequest(
            system_type=self._system_combo.currentData(),
            acres=self._acres_spin.value(),
            crop=self._crop_combo.currentData(),
            water_applied_inches=self._water_spin.value(),
            pumping_depth_ft=self._depth_spin.value(),
            water_cost_per_acre_inch=self._water_cost_spin.value(),
            electricity_rate=self._elec_spin.value(),
        )

        success, result = self._api.analyze_irrigation_cost(request)

        if not success:
            QMessageBox.warning(self, "Error", f"Failed to analyze: {result}")
            return

        acres = self._acres_spin.value()

        # Update cards
        self._variable_card.set_values(
            result.total_variable_cost,
            result.total_variable_cost / acres if acres > 0 else 0,
            {"water": result.water_cost, "pumping": result.pumping_cost}
        )

        self._fixed_card.set_values(
            result.total_fixed_cost,
            result.total_fixed_cost / acres if acres > 0 else 0,
            {"maintenance": result.maintenance_cost}
        )

        self._total_card.set_values(
            result.total_cost,
            result.cost_per_acre
        )

        # Update details
        details = {
            "water_cost": f"${result.water_cost:,.0f}",
            "pumping_cost": f"${result.pumping_cost:,.0f}",
            "maintenance_cost": f"${result.maintenance_cost:,.0f}",
            "efficiency": f"{result.efficiency_percent:.0f}%",
            "cost_per_inch": f"${result.cost_per_acre_inch:.2f}/ac-in",
        }

        for key, value in details.items():
            label = self._details_grid.parentWidget().findChild(QLabel, key)
            if label:
                label.setText(value)

        # Update savings
        if result.potential_savings > 0:
            self._savings_label.setText(
                f"Potential savings: ${result.potential_savings:,.0f}\n\n"
                f"Consider:\n"
                f"• Soil moisture monitoring\n"
                f"• Variable rate irrigation\n"
                f"• Scheduling optimization"
            )
        else:
            self._savings_label.setText("Your irrigation is already well optimized.")


class CostOptimizerScreen(QWidget):
    """
    Main cost optimizer screen with tabbed interface.

    Tabs:
    - Quick Estimate: Fast estimates using industry averages
    - Fertilizer: Soil test-based fertilizer optimization
    - Irrigation: Irrigation cost analysis
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Tab widget
        self._tabs = QTabWidget()

        # Add tabs
        self._tabs.addTab(QuickEstimateTab(), "Quick Estimate")
        self._tabs.addTab(FertilizerTab(), "Fertilizer")
        self._tabs.addTab(IrrigationTab(), "Irrigation")

        layout.addWidget(self._tabs)
