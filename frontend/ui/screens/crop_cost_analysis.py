"""
Crop Cost Analysis Dashboard Screen

Comprehensive crop cost analysis with KPIs, comparisons, and trends.
5 Tabs: Overview, Field Comparison, Crop Comparison, Year over Year, ROI Analysis
AgTools v6.9.0
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QTabWidget, QScrollArea, QFrame, QSpinBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

from api.auth_api import UserInfo
from api.crop_cost_analysis_api import (
    get_crop_cost_analysis_api,
    CropAnalysisSummary,
    FieldCostDetail,
    FieldComparisonMatrix,
    CropComparisonItem,
    YearOverYearData,
    ROIAnalysisItem,
    TrendDataPoint
)

# Try to import pyqtgraph for charts
try:
    import pyqtgraph as pg
    import numpy as np
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# Color constants (matching retro theme)
COLORS = {
    "primary": "#00868B",  # Dark turquoise
    "primary_light": "#00CED1",
    "secondary": "#1976d2",
    "warning": "#f57c00",
    "error": "#d32f2f",
    "success": "#388e3c",
    "text": "#212121",
    "text_secondary": "#757575",
    "background": "#F5F5DC",  # Cream
    "white": "#ffffff",
    "purple": "#7b1fa2"
}

CROP_COLORS = {
    "corn": "#f9a825",
    "soybean": "#558b2f",
    "soybeans": "#558b2f",
    "wheat": "#d4a574",
    "rice": "#8d6e63",
    "cotton": "#e0e0e0",
    "sorghum": "#ff7043"
}


class CropCostAnalysisScreen(QWidget):
    """
    Crop Cost Analysis Dashboard Screen.

    5 Tabs:
    - Tab 1: Overview (KPI cards with summary metrics)
    - Tab 2: Field Comparison (table + bar chart)
    - Tab 3: Crop Comparison (compare crops across fields)
    - Tab 4: Year over Year (line charts, multi-year tables)
    - Tab 5: ROI Analysis (profitability ranking, break-even)
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._api = get_crop_cost_analysis_api()

        # Data storage
        self._summary_data = None
        self._field_comparison_data = None
        self._crop_comparison_data = None
        self._year_data = None
        self._roi_data = None

        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Update the current user."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Crop Cost Analysis")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {COLORS["primary"]};
            }}
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Year selector
        header_layout.addWidget(QLabel("Crop Year:"))
        self._year_spin = QSpinBox()
        self._year_spin.setRange(2000, 2100)
        self._year_spin.setValue(QDate.currentDate().year())
        self._year_spin.setMaximumWidth(100)
        self._year_spin.valueChanged.connect(self._on_year_changed)
        header_layout.addWidget(self._year_spin)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["secondary"]};
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1565c0;
            }}
        """)
        refresh_btn.clicked.connect(self._load_data)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self._status_label)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 2px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
        """)

        # Create tabs
        self._create_overview_tab()
        self._create_field_comparison_tab()
        self._create_crop_comparison_tab()
        self._create_yoy_tab()
        self._create_roi_tab()

        layout.addWidget(self._tabs)

    def _on_year_changed(self):
        """Handle year change."""
        self._load_data()

    # ========================================================================
    # TAB 1: OVERVIEW
    # ========================================================================

    def _create_overview_tab(self):
        """Create the Overview tab with KPI cards."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Summary cards row 1
        cards_layout1 = QHBoxLayout()

        self._total_cost_label = QLabel("$0")
        cards_layout1.addWidget(self._create_summary_card("Total Cost", self._total_cost_label, COLORS["error"]))

        self._cost_per_acre_label = QLabel("$0")
        cards_layout1.addWidget(self._create_summary_card("Avg Cost/Acre", self._cost_per_acre_label, COLORS["warning"]))

        self._cost_per_bu_label = QLabel("$0")
        cards_layout1.addWidget(self._create_summary_card("Avg Cost/Bu", self._cost_per_bu_label, COLORS["secondary"]))

        self._top_roi_label = QLabel("-")
        cards_layout1.addWidget(self._create_summary_card("Top ROI Crop", self._top_roi_label, COLORS["purple"]))

        cards_layout1.addStretch()
        layout.addLayout(cards_layout1)

        # Summary cards row 2
        cards_layout2 = QHBoxLayout()

        self._total_yield_label = QLabel("0")
        cards_layout2.addWidget(self._create_summary_card("Total Yield", self._total_yield_label, COLORS["primary"]))

        self._revenue_label = QLabel("$0")
        cards_layout2.addWidget(self._create_summary_card("Gross Revenue", self._revenue_label, COLORS["secondary"]))

        self._profit_label = QLabel("$0")
        cards_layout2.addWidget(self._create_summary_card("Net Profit", self._profit_label, COLORS["success"]))

        self._field_count_label = QLabel("0")
        cards_layout2.addWidget(self._create_summary_card("Fields", self._field_count_label, COLORS["primary"]))

        cards_layout2.addStretch()
        layout.addLayout(cards_layout2)

        # Charts row
        charts_layout = QHBoxLayout()

        # Cost breakdown chart
        cost_frame = QFrame()
        cost_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.addWidget(QLabel("Cost by Category"))

        if HAS_PYQTGRAPH:
            self._overview_cost_chart = pg.PlotWidget()
            self._overview_cost_chart.setBackground('w')
            self._overview_cost_chart.setMinimumHeight(200)
            cost_layout.addWidget(self._overview_cost_chart)
        else:
            self._overview_cost_chart = QLabel("Charts require pyqtgraph")
            cost_layout.addWidget(self._overview_cost_chart)

        charts_layout.addWidget(cost_frame)

        # Profit by field chart
        profit_frame = QFrame()
        profit_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        profit_layout = QVBoxLayout(profit_frame)
        profit_layout.addWidget(QLabel("Profit by Field"))

        if HAS_PYQTGRAPH:
            self._overview_profit_chart = pg.PlotWidget()
            self._overview_profit_chart.setBackground('w')
            self._overview_profit_chart.setMinimumHeight(200)
            profit_layout.addWidget(self._overview_profit_chart)
        else:
            self._overview_profit_chart = QLabel("Charts require pyqtgraph")
            profit_layout.addWidget(self._overview_profit_chart)

        charts_layout.addWidget(profit_frame)
        layout.addLayout(charts_layout)

        # Category breakdown table
        self._category_table = QTableWidget()
        self._category_table.setColumnCount(2)
        self._category_table.setHorizontalHeaderLabels(["Category", "Total Cost"])
        self._category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._category_table.setAlternatingRowColors(True)
        self._category_table.setMaximumHeight(200)
        layout.addWidget(self._category_table)

        self._tabs.addTab(tab, "Overview")

    # ========================================================================
    # TAB 2: FIELD COMPARISON
    # ========================================================================

    def _create_field_comparison_tab(self):
        """Create the Field Comparison tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Filters row
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Sort By:"))
        self._field_sort_combo = QComboBox()
        self._field_sort_combo.addItems([
            "Cost/Acre", "Cost/Bushel", "Yield/Acre",
            "ROI %", "Total Cost", "Profit"
        ])
        self._field_sort_combo.currentIndexChanged.connect(self._on_field_sort_changed)
        filter_layout.addWidget(self._field_sort_combo)

        self._field_order_combo = QComboBox()
        self._field_order_combo.addItems(["Descending", "Ascending"])
        self._field_order_combo.currentIndexChanged.connect(self._on_field_sort_changed)
        filter_layout.addWidget(self._field_order_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # Cost per acre chart
        cost_frame = QFrame()
        cost_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.addWidget(QLabel("Cost per Acre by Field"))

        if HAS_PYQTGRAPH:
            self._field_cost_chart = pg.PlotWidget()
            self._field_cost_chart.setBackground('w')
            self._field_cost_chart.setMinimumHeight(200)
            cost_layout.addWidget(self._field_cost_chart)
        else:
            self._field_cost_chart = QLabel("Charts require pyqtgraph")
            cost_layout.addWidget(self._field_cost_chart)

        charts_layout.addWidget(cost_frame)

        # Yield per acre chart
        yield_frame = QFrame()
        yield_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        yield_layout = QVBoxLayout(yield_frame)
        yield_layout.addWidget(QLabel("Yield per Acre by Field"))

        if HAS_PYQTGRAPH:
            self._field_yield_chart = pg.PlotWidget()
            self._field_yield_chart.setBackground('w')
            self._field_yield_chart.setMinimumHeight(200)
            yield_layout.addWidget(self._field_yield_chart)
        else:
            self._field_yield_chart = QLabel("Charts require pyqtgraph")
            yield_layout.addWidget(self._field_yield_chart)

        charts_layout.addWidget(yield_frame)
        layout.addLayout(charts_layout)

        # Field comparison table
        self._field_table = QTableWidget()
        self._field_table.setColumnCount(10)
        self._field_table.setHorizontalHeaderLabels([
            "Field", "Farm", "Crop", "Acres", "Total Cost",
            "Cost/Acre", "Yield", "Yield/Acre", "ROI %", "Profit"
        ])
        self._field_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._field_table.setAlternatingRowColors(True)
        layout.addWidget(self._field_table)

        self._tabs.addTab(tab, "Field Comparison")

    # ========================================================================
    # TAB 3: CROP COMPARISON
    # ========================================================================

    def _create_crop_comparison_tab(self):
        """Create the Crop Comparison tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Crop summary cards (scrollable)
        self._crop_cards_scroll = QScrollArea()
        self._crop_cards_scroll.setWidgetResizable(True)
        self._crop_cards_scroll.setMaximumHeight(120)
        self._crop_cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._crop_cards_widget = QWidget()
        self._crop_cards_layout = QHBoxLayout(self._crop_cards_widget)
        self._crop_cards_layout.setContentsMargins(0, 0, 0, 0)

        self._crop_cards_scroll.setWidget(self._crop_cards_widget)
        layout.addWidget(self._crop_cards_scroll)

        # Charts row
        charts_layout = QHBoxLayout()

        # Cost comparison chart
        cost_frame = QFrame()
        cost_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.addWidget(QLabel("Cost per Acre by Crop"))

        if HAS_PYQTGRAPH:
            self._crop_cost_chart = pg.PlotWidget()
            self._crop_cost_chart.setBackground('w')
            self._crop_cost_chart.setMinimumHeight(200)
            cost_layout.addWidget(self._crop_cost_chart)
        else:
            self._crop_cost_chart = QLabel("Charts require pyqtgraph")
            cost_layout.addWidget(self._crop_cost_chart)

        charts_layout.addWidget(cost_frame)

        # ROI comparison chart
        roi_frame = QFrame()
        roi_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        roi_layout = QVBoxLayout(roi_frame)
        roi_layout.addWidget(QLabel("ROI % by Crop"))

        if HAS_PYQTGRAPH:
            self._crop_roi_chart = pg.PlotWidget()
            self._crop_roi_chart.setBackground('w')
            self._crop_roi_chart.setMinimumHeight(200)
            roi_layout.addWidget(self._crop_roi_chart)
        else:
            self._crop_roi_chart = QLabel("Charts require pyqtgraph")
            roi_layout.addWidget(self._crop_roi_chart)

        charts_layout.addWidget(roi_frame)
        layout.addLayout(charts_layout)

        # Crop comparison table
        self._crop_table = QTableWidget()
        self._crop_table.setColumnCount(9)
        self._crop_table.setHorizontalHeaderLabels([
            "Crop", "Fields", "Acres", "Total Cost",
            "Avg Cost/Acre", "Avg Cost/Bu", "Avg Yield/Acre", "ROI %", "Profit"
        ])
        self._crop_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._crop_table.setAlternatingRowColors(True)
        layout.addWidget(self._crop_table)

        self._tabs.addTab(tab, "Crop Comparison")

    # ========================================================================
    # TAB 4: YEAR OVER YEAR
    # ========================================================================

    def _create_yoy_tab(self):
        """Create the Year over Year tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Year range selector
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Years:"))
        self._start_year_spin = QSpinBox()
        self._start_year_spin.setRange(2000, 2100)
        self._start_year_spin.setValue(QDate.currentDate().year() - 4)
        self._start_year_spin.valueChanged.connect(self._load_yoy_data)
        filter_layout.addWidget(self._start_year_spin)

        filter_layout.addWidget(QLabel("to"))
        self._end_year_spin = QSpinBox()
        self._end_year_spin.setRange(2000, 2100)
        self._end_year_spin.setValue(QDate.currentDate().year())
        self._end_year_spin.valueChanged.connect(self._load_yoy_data)
        filter_layout.addWidget(self._end_year_spin)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Trend charts row
        charts_layout = QHBoxLayout()

        # Cost trend chart
        cost_frame = QFrame()
        cost_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.addWidget(QLabel("Cost per Acre Trend"))

        if HAS_PYQTGRAPH:
            self._yoy_cost_chart = pg.PlotWidget()
            self._yoy_cost_chart.setBackground('w')
            self._yoy_cost_chart.setMinimumHeight(180)
            cost_layout.addWidget(self._yoy_cost_chart)
        else:
            self._yoy_cost_chart = QLabel("Charts require pyqtgraph")
            cost_layout.addWidget(self._yoy_cost_chart)

        charts_layout.addWidget(cost_frame)

        # Yield trend chart
        yield_frame = QFrame()
        yield_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        yield_layout = QVBoxLayout(yield_frame)
        yield_layout.addWidget(QLabel("Yield per Acre Trend"))

        if HAS_PYQTGRAPH:
            self._yoy_yield_chart = pg.PlotWidget()
            self._yoy_yield_chart.setBackground('w')
            self._yoy_yield_chart.setMinimumHeight(180)
            yield_layout.addWidget(self._yoy_yield_chart)
        else:
            self._yoy_yield_chart = QLabel("Charts require pyqtgraph")
            yield_layout.addWidget(self._yoy_yield_chart)

        charts_layout.addWidget(yield_frame)
        layout.addLayout(charts_layout)

        # ROI trend chart
        roi_frame = QFrame()
        roi_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        roi_layout = QVBoxLayout(roi_frame)
        roi_layout.addWidget(QLabel("ROI % Trend"))

        if HAS_PYQTGRAPH:
            self._yoy_roi_chart = pg.PlotWidget()
            self._yoy_roi_chart.setBackground('w')
            self._yoy_roi_chart.setMinimumHeight(150)
            roi_layout.addWidget(self._yoy_roi_chart)
        else:
            self._yoy_roi_chart = QLabel("Charts require pyqtgraph")
            roi_layout.addWidget(self._yoy_roi_chart)

        layout.addWidget(roi_frame)

        # YoY table
        self._yoy_table = QTableWidget()
        self._yoy_table.setColumnCount(9)
        self._yoy_table.setHorizontalHeaderLabels([
            "Year", "Acres", "Total Cost", "Cost/Acre",
            "Yield", "Yield/Acre", "Revenue", "Profit", "ROI %"
        ])
        self._yoy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._yoy_table.setAlternatingRowColors(True)
        layout.addWidget(self._yoy_table)

        self._tabs.addTab(tab, "Year over Year")

    # ========================================================================
    # TAB 5: ROI ANALYSIS
    # ========================================================================

    def _create_roi_tab(self):
        """Create the ROI Analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Group by selector
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Group By:"))
        self._roi_group_combo = QComboBox()
        self._roi_group_combo.addItems(["Field", "Crop"])
        self._roi_group_combo.currentIndexChanged.connect(self._on_roi_group_changed)
        filter_layout.addWidget(self._roi_group_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # ROI ranking chart
        ranking_frame = QFrame()
        ranking_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        ranking_layout = QVBoxLayout(ranking_frame)
        ranking_layout.addWidget(QLabel("Profitability Ranking"))

        if HAS_PYQTGRAPH:
            self._roi_ranking_chart = pg.PlotWidget()
            self._roi_ranking_chart.setBackground('w')
            self._roi_ranking_chart.setMinimumHeight(200)
            ranking_layout.addWidget(self._roi_ranking_chart)
        else:
            self._roi_ranking_chart = QLabel("Charts require pyqtgraph")
            ranking_layout.addWidget(self._roi_ranking_chart)

        charts_layout.addWidget(ranking_frame)

        # Break-even chart
        be_frame = QFrame()
        be_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        be_layout = QVBoxLayout(be_frame)
        be_layout.addWidget(QLabel("Margin of Safety"))

        if HAS_PYQTGRAPH:
            self._roi_margin_chart = pg.PlotWidget()
            self._roi_margin_chart.setBackground('w')
            self._roi_margin_chart.setMinimumHeight(200)
            be_layout.addWidget(self._roi_margin_chart)
        else:
            self._roi_margin_chart = QLabel("Charts require pyqtgraph")
            be_layout.addWidget(self._roi_margin_chart)

        charts_layout.addWidget(be_frame)
        layout.addLayout(charts_layout)

        # ROI detail table
        self._roi_table = QTableWidget()
        self._roi_table.setColumnCount(8)
        self._roi_table.setHorizontalHeaderLabels([
            "Name", "Investment", "Return", "Profit",
            "ROI %", "Break-Even Yield", "Break-Even Price", "Safety Margin"
        ])
        self._roi_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._roi_table.setAlternatingRowColors(True)
        layout.addWidget(self._roi_table)

        self._tabs.addTab(tab, "ROI Analysis")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_summary_card(self, title: str, value_label: QLabel, color: str) -> QFrame:
        """Create a summary card widget."""
        card = QFrame()
        card.setMinimumWidth(150)
        card.setMaximumWidth(200)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(title_label)

        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

    def _create_crop_card(self, crop: CropComparisonItem) -> QFrame:
        """Create a crop summary card."""
        card = QFrame()
        card.setMinimumWidth(180)
        card.setMaximumWidth(220)
        crop_color = CROP_COLORS.get(crop.crop_type.lower(), COLORS["primary"])
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {crop_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        title_label = QLabel(crop.crop_type)
        title_label.setStyleSheet(f"color: {crop_color}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        cost_label = QLabel(f"${crop.avg_cost_per_acre:,.0f}/acre")
        cost_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")
        layout.addWidget(cost_label)

        roi_color = COLORS["success"] if crop.roi_percent >= 0 else COLORS["error"]
        roi_label = QLabel(f"ROI: {crop.roi_percent:.1f}%")
        roi_label.setStyleSheet(f"color: {roi_color}; font-size: 12px; font-weight: bold;")
        layout.addWidget(roi_label)

        return card

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def _load_data(self):
        """Load all data for all tabs."""
        crop_year = self._year_spin.value()
        self._status_label.setText("Loading...")

        # Load summary
        summary, error = self._api.get_summary(crop_year)
        if error:
            self._status_label.setText(f"Error: {error}")
        else:
            self._summary_data = summary
            self._update_overview_tab()

        # Load field comparison
        self._load_field_comparison()

        # Load crop comparison
        crops, error = self._api.get_crop_comparison(crop_year)
        if not error:
            self._crop_comparison_data = crops
            self._update_crop_comparison_tab()

        # Load YoY data
        self._load_yoy_data()

        # Load ROI data
        self._load_roi_data()

        self._status_label.setText(f"Last updated: {QDate.currentDate().toString()}")

    def _load_field_comparison(self):
        """Load field comparison data."""
        crop_year = self._year_spin.value()
        sort_map = {
            0: "cost_per_acre",
            1: "cost_per_bushel",
            2: "yield_per_acre",
            3: "roi_percent",
            4: "total_cost",
            5: "profit"
        }
        sort_by = sort_map.get(self._field_sort_combo.currentIndex(), "cost_per_acre")
        sort_order = "desc" if self._field_order_combo.currentIndex() == 0 else "asc"

        comparison, error = self._api.get_field_comparison(crop_year, sort_by=sort_by, sort_order=sort_order)
        if not error:
            self._field_comparison_data = comparison
            self._update_field_comparison_tab()

    def _load_yoy_data(self):
        """Load year-over-year data."""
        start = self._start_year_spin.value()
        end = self._end_year_spin.value()
        years = list(range(start, end + 1))

        yoy_data, error = self._api.get_year_comparison(years)
        if not error:
            self._year_data = yoy_data
            self._update_yoy_tab()

    def _load_roi_data(self):
        """Load ROI analysis data."""
        crop_year = self._year_spin.value()
        group_by = "field" if self._roi_group_combo.currentIndex() == 0 else "crop"

        roi_data, error = self._api.get_roi_analysis(crop_year, group_by)
        if not error:
            self._roi_data = roi_data
            self._update_roi_tab()

    def _on_field_sort_changed(self):
        """Handle field sort change."""
        self._load_field_comparison()

    def _on_roi_group_changed(self):
        """Handle ROI group change."""
        self._load_roi_data()

    # ========================================================================
    # TAB UPDATES
    # ========================================================================

    def _update_overview_tab(self):
        """Update the Overview tab with loaded data."""
        if not self._summary_data:
            return

        s = self._summary_data
        self._total_cost_label.setText(s.total_cost_display)
        self._cost_per_acre_label.setText(s.cost_per_acre_display)
        self._cost_per_bu_label.setText(s.cost_per_bushel_display)
        self._top_roi_label.setText(f"{s.top_roi_crop or '-'} ({s.roi_display})")
        self._total_yield_label.setText(f"{s.total_yield:,.0f} bu")
        self._revenue_label.setText(s.revenue_display)
        self._profit_label.setText(s.profit_display)
        self._profit_label.setStyleSheet(f"color: {s.profit_color}; font-size: 20px; font-weight: bold;")
        self._field_count_label.setText(str(s.field_count))

        # Update category table
        categories = s.cost_by_category
        self._category_table.setRowCount(len(categories))
        for i, (cat, cost) in enumerate(sorted(categories.items(), key=lambda x: -x[1])):
            self._category_table.setItem(i, 0, QTableWidgetItem(cat.title()))
            cost_item = QTableWidgetItem(f"${cost:,.2f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._category_table.setItem(i, 1, cost_item)

        # Update charts
        if HAS_PYQTGRAPH and categories:
            self._draw_category_chart(categories)

    def _update_field_comparison_tab(self):
        """Update the Field Comparison tab."""
        if not self._field_comparison_data:
            return

        fields = self._field_comparison_data.fields

        # Update table
        self._field_table.setRowCount(len(fields))
        for i, f in enumerate(fields):
            self._field_table.setItem(i, 0, QTableWidgetItem(f.field_name))
            self._field_table.setItem(i, 1, QTableWidgetItem(f.farm_name or "-"))
            self._field_table.setItem(i, 2, QTableWidgetItem(f.crop_type or "-"))
            self._field_table.setItem(i, 3, QTableWidgetItem(f"{f.acreage:,.1f}"))

            cost_item = QTableWidgetItem(f"${f.total_cost:,.0f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._field_table.setItem(i, 4, cost_item)

            cpa_item = QTableWidgetItem(f"${f.cost_per_acre:,.2f}")
            cpa_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._field_table.setItem(i, 5, cpa_item)

            self._field_table.setItem(i, 6, QTableWidgetItem(f"{f.total_yield:,.0f}"))

            ypa_item = QTableWidgetItem(f"{f.yield_per_acre:,.1f}")
            ypa_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._field_table.setItem(i, 7, ypa_item)

            roi_item = QTableWidgetItem(f"{f.roi_percent:.1f}%")
            roi_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._field_table.setItem(i, 8, roi_item)

            profit_item = QTableWidgetItem(f"${f.profit:,.0f}")
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            profit_item.setForeground(QColor(f.profit_color))
            self._field_table.setItem(i, 9, profit_item)

        # Update charts
        if HAS_PYQTGRAPH and fields:
            self._draw_field_charts(fields)

    def _update_crop_comparison_tab(self):
        """Update the Crop Comparison tab."""
        if not self._crop_comparison_data:
            return

        crops = self._crop_comparison_data

        # Clear and rebuild crop cards
        while self._crop_cards_layout.count():
            item = self._crop_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for crop in crops:
            card = self._create_crop_card(crop)
            self._crop_cards_layout.addWidget(card)
        self._crop_cards_layout.addStretch()

        # Update table
        self._crop_table.setRowCount(len(crops))
        for i, c in enumerate(crops):
            self._crop_table.setItem(i, 0, QTableWidgetItem(c.crop_type))
            self._crop_table.setItem(i, 1, QTableWidgetItem(str(c.field_count)))
            self._crop_table.setItem(i, 2, QTableWidgetItem(f"{c.total_acres:,.1f}"))

            cost_item = QTableWidgetItem(f"${c.total_cost:,.0f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._crop_table.setItem(i, 3, cost_item)

            cpa_item = QTableWidgetItem(f"${c.avg_cost_per_acre:,.2f}")
            cpa_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._crop_table.setItem(i, 4, cpa_item)

            cpb = f"${c.avg_cost_per_bushel:,.2f}" if c.avg_cost_per_bushel else "N/A"
            self._crop_table.setItem(i, 5, QTableWidgetItem(cpb))

            self._crop_table.setItem(i, 6, QTableWidgetItem(f"{c.avg_yield_per_acre:,.1f}"))

            roi_item = QTableWidgetItem(f"{c.roi_percent:.1f}%")
            roi_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._crop_table.setItem(i, 7, roi_item)

            profit_item = QTableWidgetItem(c.profit_display)
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            profit_item.setForeground(QColor(c.profit_color))
            self._crop_table.setItem(i, 8, profit_item)

        # Update charts
        if HAS_PYQTGRAPH and crops:
            self._draw_crop_charts(crops)

    def _update_yoy_tab(self):
        """Update the Year over Year tab."""
        if not self._year_data:
            return

        data = self._year_data

        # Update table
        self._yoy_table.setRowCount(len(data))
        for i, d in enumerate(data):
            self._yoy_table.setItem(i, 0, QTableWidgetItem(str(d.year)))
            self._yoy_table.setItem(i, 1, QTableWidgetItem(f"{d.total_acres:,.1f}"))

            cost_item = QTableWidgetItem(f"${d.total_cost:,.0f}")
            cost_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._yoy_table.setItem(i, 2, cost_item)

            cpa_item = QTableWidgetItem(f"${d.avg_cost_per_acre:,.2f}")
            cpa_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._yoy_table.setItem(i, 3, cpa_item)

            self._yoy_table.setItem(i, 4, QTableWidgetItem(f"{d.total_yield:,.0f}"))
            self._yoy_table.setItem(i, 5, QTableWidgetItem(f"{d.avg_yield_per_acre:,.1f}"))

            rev_item = QTableWidgetItem(f"${d.revenue:,.0f}")
            rev_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._yoy_table.setItem(i, 6, rev_item)

            profit_item = QTableWidgetItem(f"${d.profit:,.0f}")
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            profit_color = COLORS["success"] if d.profit >= 0 else COLORS["error"]
            profit_item.setForeground(QColor(profit_color))
            self._yoy_table.setItem(i, 7, profit_item)

            roi_item = QTableWidgetItem(f"{d.roi_percent:.1f}%")
            roi_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._yoy_table.setItem(i, 8, roi_item)

        # Update charts
        if HAS_PYQTGRAPH and data:
            self._draw_yoy_charts(data)

    def _update_roi_tab(self):
        """Update the ROI Analysis tab."""
        if not self._roi_data:
            return

        data = self._roi_data

        # Update table
        self._roi_table.setRowCount(len(data))
        for i, r in enumerate(data):
            self._roi_table.setItem(i, 0, QTableWidgetItem(r.entity_name))

            inv_item = QTableWidgetItem(f"${r.total_investment:,.0f}")
            inv_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._roi_table.setItem(i, 1, inv_item)

            ret_item = QTableWidgetItem(f"${r.total_return:,.0f}")
            ret_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._roi_table.setItem(i, 2, ret_item)

            profit_item = QTableWidgetItem(f"${r.net_profit:,.0f}")
            profit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            profit_color = COLORS["success"] if r.net_profit >= 0 else COLORS["error"]
            profit_item.setForeground(QColor(profit_color))
            self._roi_table.setItem(i, 3, profit_item)

            roi_item = QTableWidgetItem(r.roi_display)
            roi_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            roi_item.setForeground(QColor(r.roi_color))
            self._roi_table.setItem(i, 4, roi_item)

            be_yield_item = QTableWidgetItem(f"{r.break_even_yield:,.1f} bu")
            be_yield_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._roi_table.setItem(i, 5, be_yield_item)

            be_price_item = QTableWidgetItem(f"${r.break_even_price:,.2f}")
            be_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._roi_table.setItem(i, 6, be_price_item)

            margin_item = QTableWidgetItem(r.margin_display)
            margin_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            margin_item.setForeground(QColor(r.margin_color))
            self._roi_table.setItem(i, 7, margin_item)

        # Update charts
        if HAS_PYQTGRAPH and data:
            self._draw_roi_charts(data)

    # ========================================================================
    # CHART DRAWING
    # ========================================================================

    def _draw_category_chart(self, categories: dict):
        """Draw cost by category bar chart."""
        if not HAS_PYQTGRAPH:
            return

        self._overview_cost_chart.clear()

        sorted_cats = sorted(categories.items(), key=lambda x: -x[1])[:10]
        x = list(range(len(sorted_cats)))
        heights = [c[1] for c in sorted_cats]
        labels = [c[0].title()[:8] for c in sorted_cats]

        bg = pg.BarGraphItem(x=x, height=heights, width=0.6, brush=COLORS["primary"])
        self._overview_cost_chart.addItem(bg)

        ax = self._overview_cost_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])

    def _draw_field_charts(self, fields: list):
        """Draw field comparison charts."""
        if not HAS_PYQTGRAPH:
            return

        # Limit to top 10 fields
        display_fields = fields[:10]

        # Cost per acre chart
        self._field_cost_chart.clear()
        x = list(range(len(display_fields)))
        heights = [f.cost_per_acre for f in display_fields]
        labels = [f.field_name[:10] for f in display_fields]

        bg = pg.BarGraphItem(x=x, height=heights, width=0.6, brush=COLORS["warning"])
        self._field_cost_chart.addItem(bg)

        ax = self._field_cost_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])

        # Yield per acre chart
        self._field_yield_chart.clear()
        heights = [f.yield_per_acre for f in display_fields]

        bg = pg.BarGraphItem(x=x, height=heights, width=0.6, brush=COLORS["success"])
        self._field_yield_chart.addItem(bg)

        ax = self._field_yield_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])

    def _draw_crop_charts(self, crops: list):
        """Draw crop comparison charts."""
        if not HAS_PYQTGRAPH:
            return

        # Cost per acre chart
        self._crop_cost_chart.clear()
        x = list(range(len(crops)))
        heights = [c.avg_cost_per_acre for c in crops]
        labels = [c.crop_type[:8] for c in crops]
        colors = [CROP_COLORS.get(c.crop_type.lower(), COLORS["primary"]) for c in crops]

        for i, (xi, h, col) in enumerate(zip(x, heights, colors)):
            bg = pg.BarGraphItem(x=[xi], height=[h], width=0.6, brush=col)
            self._crop_cost_chart.addItem(bg)

        ax = self._crop_cost_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])

        # ROI chart
        self._crop_roi_chart.clear()
        heights = [c.roi_percent for c in crops]

        for i, (xi, h, col) in enumerate(zip(x, heights, colors)):
            bar_color = COLORS["success"] if h >= 0 else COLORS["error"]
            bg = pg.BarGraphItem(x=[xi], height=[h], width=0.6, brush=bar_color)
            self._crop_roi_chart.addItem(bg)

        ax = self._crop_roi_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])

    def _draw_yoy_charts(self, data: list):
        """Draw year-over-year trend charts."""
        if not HAS_PYQTGRAPH:
            return

        years = [d.year for d in data]

        # Cost trend
        self._yoy_cost_chart.clear()
        costs = [d.avg_cost_per_acre for d in data]
        self._yoy_cost_chart.plot(years, costs, pen=pg.mkPen(COLORS["warning"], width=2), symbol='o')

        # Yield trend
        self._yoy_yield_chart.clear()
        yields = [d.avg_yield_per_acre for d in data]
        self._yoy_yield_chart.plot(years, yields, pen=pg.mkPen(COLORS["success"], width=2), symbol='o')

        # ROI trend
        self._yoy_roi_chart.clear()
        rois = [d.roi_percent for d in data]
        self._yoy_roi_chart.plot(years, rois, pen=pg.mkPen(COLORS["primary"], width=2), symbol='o')
        # Add zero line
        self._yoy_roi_chart.addLine(y=0, pen=pg.mkPen('#ccc', style=Qt.PenStyle.DashLine))

    def _draw_roi_charts(self, data: list):
        """Draw ROI analysis charts."""
        if not HAS_PYQTGRAPH:
            return

        display_data = data[:10]

        # ROI ranking chart
        self._roi_ranking_chart.clear()
        x = list(range(len(display_data)))
        heights = [r.roi_percent for r in display_data]
        labels = [r.entity_name[:10] for r in display_data]

        for i, (xi, h) in enumerate(zip(x, heights)):
            bar_color = COLORS["success"] if h >= 0 else COLORS["error"]
            bg = pg.BarGraphItem(x=[xi], height=[h], width=0.6, brush=bar_color)
            self._roi_ranking_chart.addItem(bg)

        ax = self._roi_ranking_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])

        # Margin chart
        self._roi_margin_chart.clear()
        margins = [r.margin_of_safety_percent for r in display_data]

        for i, (xi, h) in enumerate(zip(x, margins)):
            bar_color = COLORS["success"] if h >= 20 else (COLORS["warning"] if h >= 0 else COLORS["error"])
            bg = pg.BarGraphItem(x=[xi], height=[h], width=0.6, brush=bar_color)
            self._roi_margin_chart.addItem(bg)

        ax = self._roi_margin_chart.getAxis('bottom')
        ax.setTicks([[(i, labels[i]) for i in x]])
        self._roi_margin_chart.addLine(y=0, pen=pg.mkPen('#ccc', style=Qt.PenStyle.DashLine))
