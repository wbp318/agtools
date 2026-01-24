"""
Reports Dashboard Screen

Provides comprehensive reports and analytics across all farm operations.
AgTools v2.5.0 Phase 5
"""

import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QTabWidget, QFrame
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QColor

from api.auth_api import UserInfo
from api.reports_api import (
    get_reports_api, OperationsReport, FinancialReport, EquipmentReport,
    InventoryReport, FieldPerformanceReport
)
from api.export_api import get_export_api

from ui.widgets.export_toolbar import ExportToolbar

# Try to import pyqtgraph for charts
try:
    import pyqtgraph as pg
    import numpy as np
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

# Color constants
COLORS = {
    "primary": "#2e7d32",
    "primary_dark": "#1b5e20",
    "secondary": "#1976d2",
    "warning": "#f57c00",
    "error": "#d32f2f",
    "success": "#388e3c",
    "text": "#212121",
    "text_secondary": "#757575",
    "background": "#f5f5f5",
    "white": "#ffffff"
}

OPERATION_COLORS = {
    "spray": "#4caf50",
    "fertilizer": "#ff9800",
    "planting": "#2196f3",
    "harvest": "#9c27b0",
    "tillage": "#795548",
    "scouting": "#00bcd4",
    "irrigation": "#3f51b5",
    "other": "#757575"
}


class ReportsDashboardScreen(QWidget):
    """
    Reports and Analytics Dashboard Screen.

    Provides 4 tabs:
    - Operations Overview
    - Financial Analysis
    - Equipment & Inventory
    - Field Performance
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._reports_api = get_reports_api()

        # Report data
        self._ops_report = None
        self._financial_report = None
        self._equipment_report = None
        self._inventory_report = None
        self._field_report = None

        self._setup_ui()
        self._load_reports()

    def set_current_user(self, user: UserInfo):
        """Update the current user."""
        self._current_user = user
        self._load_reports()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Reports & Analytics")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {COLORS["primary"]};
            }}
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Date range filters
        header_layout.addWidget(QLabel("From:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-3))
        self._date_from.setMaximumWidth(130)
        self._date_from.dateChanged.connect(self._load_reports)
        header_layout.addWidget(self._date_from)

        header_layout.addWidget(QLabel("To:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setMaximumWidth(130)
        self._date_to.dateChanged.connect(self._load_reports)
        header_layout.addWidget(self._date_to)

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
        refresh_btn.clicked.connect(self._load_reports)
        header_layout.addWidget(refresh_btn)

        # Export toolbar (CSV, Excel, PDF)
        self._export_toolbar = ExportToolbar()
        self._export_toolbar.set_export_handler(self._handle_export)
        header_layout.addWidget(self._export_toolbar)

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
        self._create_operations_tab()
        self._create_financial_tab()
        self._create_equipment_tab()
        self._create_fields_tab()

        layout.addWidget(self._tabs)

    # ========================================================================
    # TAB 1: OPERATIONS OVERVIEW
    # ========================================================================

    def _create_operations_tab(self):
        """Create the Operations Overview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Summary cards
        cards_layout = QHBoxLayout()

        self._ops_total_label = QLabel("0")
        cards_layout.addWidget(self._create_summary_card("Total Operations", self._ops_total_label, COLORS["primary"]))

        self._ops_cost_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Total Cost", self._ops_cost_label, COLORS["secondary"]))

        self._ops_avg_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Avg Cost/Acre", self._ops_avg_label, COLORS["warning"]))

        self._ops_top_label = QLabel("-")
        cards_layout.addWidget(self._create_summary_card("Top Operation", self._ops_top_label, "#7b1fa2"))

        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # Operations by type chart
        type_frame = QFrame()
        type_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        type_layout = QVBoxLayout(type_frame)
        type_layout.addWidget(QLabel("Operations by Type"))

        if HAS_PYQTGRAPH:
            self._ops_type_chart = pg.PlotWidget()
            self._ops_type_chart.setBackground('w')
            self._ops_type_chart.setMinimumHeight(200)
            type_layout.addWidget(self._ops_type_chart)
        else:
            self._ops_type_chart = QLabel("Charts require pyqtgraph")
            type_layout.addWidget(self._ops_type_chart)

        charts_layout.addWidget(type_frame)

        # Monthly costs chart
        monthly_frame = QFrame()
        monthly_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        monthly_layout = QVBoxLayout(monthly_frame)
        monthly_layout.addWidget(QLabel("Monthly Costs"))

        if HAS_PYQTGRAPH:
            self._ops_monthly_chart = pg.PlotWidget()
            self._ops_monthly_chart.setBackground('w')
            self._ops_monthly_chart.setMinimumHeight(200)
            monthly_layout.addWidget(self._ops_monthly_chart)
        else:
            self._ops_monthly_chart = QLabel("Charts require pyqtgraph")
            monthly_layout.addWidget(self._ops_monthly_chart)

        charts_layout.addWidget(monthly_frame)
        layout.addLayout(charts_layout)

        # Operations table
        self._ops_table = QTableWidget()
        self._ops_table.setColumnCount(4)
        self._ops_table.setHorizontalHeaderLabels(["Operation Type", "Count", "Total Cost", "Avg Cost"])
        self._ops_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._ops_table.setAlternatingRowColors(True)
        self._ops_table.setMinimumHeight(150)
        layout.addWidget(self._ops_table)

        self._tabs.addTab(tab, "Operations")

    # ========================================================================
    # TAB 2: FINANCIAL ANALYSIS
    # ========================================================================

    def _create_financial_tab(self):
        """Create the Financial Analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Summary cards
        cards_layout = QHBoxLayout()

        self._fin_input_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Input Costs", self._fin_input_label, COLORS["error"]))

        self._fin_equip_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Equipment Costs", self._fin_equip_label, COLORS["warning"]))

        self._fin_revenue_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Revenue", self._fin_revenue_label, COLORS["secondary"]))

        self._fin_profit_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Net Profit", self._fin_profit_label, COLORS["success"]))

        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # Cost breakdown chart
        cost_frame = QFrame()
        cost_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.addWidget(QLabel("Cost by Category"))

        if HAS_PYQTGRAPH:
            self._fin_cost_chart = pg.PlotWidget()
            self._fin_cost_chart.setBackground('w')
            self._fin_cost_chart.setMinimumHeight(200)
            cost_layout.addWidget(self._fin_cost_chart)
        else:
            self._fin_cost_chart = QLabel("Charts require pyqtgraph")
            cost_layout.addWidget(self._fin_cost_chart)

        charts_layout.addWidget(cost_frame)

        # Profit by field chart
        profit_frame = QFrame()
        profit_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        profit_layout = QVBoxLayout(profit_frame)
        profit_layout.addWidget(QLabel("Profit by Field"))

        if HAS_PYQTGRAPH:
            self._fin_profit_chart = pg.PlotWidget()
            self._fin_profit_chart.setBackground('w')
            self._fin_profit_chart.setMinimumHeight(200)
            profit_layout.addWidget(self._fin_profit_chart)
        else:
            self._fin_profit_chart = QLabel("Charts require pyqtgraph")
            profit_layout.addWidget(self._fin_profit_chart)

        charts_layout.addWidget(profit_frame)
        layout.addLayout(charts_layout)

        # Fields table
        self._fin_table = QTableWidget()
        self._fin_table.setColumnCount(7)
        self._fin_table.setHorizontalHeaderLabels(["Field", "Farm", "Acres", "Cost", "Cost/Acre", "Revenue", "Profit"])
        self._fin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._fin_table.setAlternatingRowColors(True)
        self._fin_table.setMinimumHeight(150)
        layout.addWidget(self._fin_table)

        self._tabs.addTab(tab, "Financial")

    # ========================================================================
    # TAB 3: EQUIPMENT & INVENTORY
    # ========================================================================

    def _create_equipment_tab(self):
        """Create the Equipment & Inventory tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Summary cards
        cards_layout = QHBoxLayout()

        self._equip_value_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Fleet Value", self._equip_value_label, COLORS["primary"]))

        self._equip_hours_label = QLabel("0")
        cards_layout.addWidget(self._create_summary_card("Total Hours", self._equip_hours_label, COLORS["secondary"]))

        self._inv_value_label = QLabel("$0")
        cards_layout.addWidget(self._create_summary_card("Inventory Value", self._inv_value_label, COLORS["warning"]))

        self._inv_low_label = QLabel("0")
        cards_layout.addWidget(self._create_summary_card("Low Stock", self._inv_low_label, COLORS["error"]))

        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # Equipment hours chart
        hours_frame = QFrame()
        hours_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        hours_layout = QVBoxLayout(hours_frame)
        hours_layout.addWidget(QLabel("Equipment Hours"))

        if HAS_PYQTGRAPH:
            self._equip_hours_chart = pg.PlotWidget()
            self._equip_hours_chart.setBackground('w')
            self._equip_hours_chart.setMinimumHeight(200)
            hours_layout.addWidget(self._equip_hours_chart)
        else:
            self._equip_hours_chart = QLabel("Charts require pyqtgraph")
            hours_layout.addWidget(self._equip_hours_chart)

        charts_layout.addWidget(hours_frame)

        # Inventory value chart
        inv_frame = QFrame()
        inv_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        inv_layout = QVBoxLayout(inv_frame)
        inv_layout.addWidget(QLabel("Inventory by Category"))

        if HAS_PYQTGRAPH:
            self._inv_value_chart = pg.PlotWidget()
            self._inv_value_chart.setBackground('w')
            self._inv_value_chart.setMinimumHeight(200)
            inv_layout.addWidget(self._inv_value_chart)
        else:
            self._inv_value_chart = QLabel("Charts require pyqtgraph")
            inv_layout.addWidget(self._inv_value_chart)

        charts_layout.addWidget(inv_frame)
        layout.addLayout(charts_layout)

        # Tables row
        tables_layout = QHBoxLayout()

        # Maintenance alerts table
        maint_frame = QFrame()
        maint_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; }")
        maint_layout = QVBoxLayout(maint_frame)
        maint_layout.addWidget(QLabel("Maintenance Alerts"))

        self._maint_table = QTableWidget()
        self._maint_table.setColumnCount(4)
        self._maint_table.setHorizontalHeaderLabels(["Equipment", "Type", "Due Date", "Status"])
        self._maint_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._maint_table.setAlternatingRowColors(True)
        self._maint_table.setMaximumHeight(150)
        maint_layout.addWidget(self._maint_table)

        tables_layout.addWidget(maint_frame)

        # Low stock table
        low_frame = QFrame()
        low_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; }")
        low_layout = QVBoxLayout(low_frame)
        low_layout.addWidget(QLabel("Low Stock Items"))

        self._low_stock_table = QTableWidget()
        self._low_stock_table.setColumnCount(4)
        self._low_stock_table.setHorizontalHeaderLabels(["Item", "Category", "Quantity", "Unit"])
        self._low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._low_stock_table.setAlternatingRowColors(True)
        self._low_stock_table.setMaximumHeight(150)
        low_layout.addWidget(self._low_stock_table)

        tables_layout.addWidget(low_frame)
        layout.addLayout(tables_layout)

        self._tabs.addTab(tab, "Equipment & Inventory")

    # ========================================================================
    # TAB 4: FIELD PERFORMANCE
    # ========================================================================

    def _create_fields_tab(self):
        """Create the Field Performance tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Summary cards
        cards_layout = QHBoxLayout()

        self._field_count_label = QLabel("0")
        cards_layout.addWidget(self._create_summary_card("Total Fields", self._field_count_label, COLORS["primary"]))

        self._field_acres_label = QLabel("0")
        cards_layout.addWidget(self._create_summary_card("Total Acres", self._field_acres_label, COLORS["secondary"]))

        self._field_yield_label = QLabel("-")
        cards_layout.addWidget(self._create_summary_card("Avg Yield", self._field_yield_label, COLORS["warning"]))

        self._field_best_label = QLabel("-")
        cards_layout.addWidget(self._create_summary_card("Best Field", self._field_best_label, COLORS["success"]))

        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # Yield by field chart
        yield_frame = QFrame()
        yield_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        yield_layout = QVBoxLayout(yield_frame)
        yield_layout.addWidget(QLabel("Yield by Field"))

        if HAS_PYQTGRAPH:
            self._field_yield_chart = pg.PlotWidget()
            self._field_yield_chart.setBackground('w')
            self._field_yield_chart.setMinimumHeight(200)
            yield_layout.addWidget(self._field_yield_chart)
        else:
            self._field_yield_chart = QLabel("Charts require pyqtgraph")
            yield_layout.addWidget(self._field_yield_chart)

        charts_layout.addWidget(yield_frame)

        # Acreage by crop chart
        crop_frame = QFrame()
        crop_frame.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 4px; }")
        crop_layout = QVBoxLayout(crop_frame)
        crop_layout.addWidget(QLabel("Acreage by Crop"))

        if HAS_PYQTGRAPH:
            self._field_crop_chart = pg.PlotWidget()
            self._field_crop_chart.setBackground('w')
            self._field_crop_chart.setMinimumHeight(200)
            crop_layout.addWidget(self._field_crop_chart)
        else:
            self._field_crop_chart = QLabel("Charts require pyqtgraph")
            crop_layout.addWidget(self._field_crop_chart)

        charts_layout.addWidget(crop_frame)
        layout.addLayout(charts_layout)

        # Fields table
        self._fields_table = QTableWidget()
        self._fields_table.setColumnCount(8)
        self._fields_table.setHorizontalHeaderLabels(["Field", "Farm", "Acres", "Crop", "Operations", "Cost", "Cost/Acre", "Yield/Acre"])
        self._fields_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._fields_table.setAlternatingRowColors(True)
        self._fields_table.setMinimumHeight(150)
        layout.addWidget(self._fields_table)

        self._tabs.addTab(tab, "Field Performance")

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _create_summary_card(self, title: str, value_label: QLabel, color: str) -> QWidget:
        """Create a summary card widget."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["white"]};
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        card.setMinimumWidth(150)
        card.setMaximumWidth(200)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        layout.addWidget(title_lbl)

        value_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(value_label)

        return card

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def _load_reports(self):
        """Load all reports."""
        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        self._status_label.setText("Loading reports...")

        # Load all reports
        self._load_operations_report(date_from, date_to)
        self._load_financial_report(date_from, date_to)
        self._load_equipment_report(date_from, date_to)
        self._load_inventory_report()
        self._load_field_report(date_from, date_to)

        self._status_label.setText(f"Reports loaded. Date range: {date_from} to {date_to}")

    def _load_operations_report(self, date_from: str, date_to: str):
        """Load operations report."""
        report, error = self._reports_api.get_operations_report(date_from, date_to)

        if error:
            self._status_label.setText(f"Error loading operations: {error}")
            return

        self._ops_report = report

        # Update summary cards
        self._ops_total_label.setText(str(report.total_operations))
        self._ops_cost_label.setText(f"${report.total_cost:,.2f}")
        self._ops_avg_label.setText(f"${report.avg_cost_per_acre:,.2f}")
        self._ops_top_label.setText(report.top_operation_type.replace("_", " ").title() if report.top_operation_type else "-")

        # Update table
        self._ops_table.setRowCount(len(report.operations_by_type))
        for row, (op_type, count) in enumerate(report.operations_by_type.items()):
            cost = report.cost_by_type.get(op_type, 0)
            avg = cost / count if count > 0 else 0

            self._ops_table.setItem(row, 0, QTableWidgetItem(op_type.replace("_", " ").title()))
            self._ops_table.setItem(row, 1, QTableWidgetItem(str(count)))
            self._ops_table.setItem(row, 2, QTableWidgetItem(f"${cost:,.2f}"))
            self._ops_table.setItem(row, 3, QTableWidgetItem(f"${avg:,.2f}"))

        # Update charts
        if HAS_PYQTGRAPH and report.operations_by_type:
            self._update_ops_type_chart(report)
            self._update_ops_monthly_chart(report)

    def _load_financial_report(self, date_from: str, date_to: str):
        """Load financial report."""
        report, error = self._reports_api.get_financial_report(date_from, date_to)

        if error:
            return

        self._financial_report = report

        # Update summary cards
        self._fin_input_label.setText(f"${report.total_input_costs:,.2f}")
        self._fin_equip_label.setText(f"${report.total_equipment_costs:,.2f}")
        self._fin_revenue_label.setText(f"${report.total_revenue:,.2f}")
        self._fin_profit_label.setText(f"${report.net_profit:,.2f}")

        # Color profit label
        profit_color = COLORS["success"] if report.net_profit >= 0 else COLORS["error"]
        self._fin_profit_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {profit_color};")

        # Update table
        self._fin_table.setRowCount(len(report.fields))
        for row, field in enumerate(report.fields):
            self._fin_table.setItem(row, 0, QTableWidgetItem(field.field_name))
            self._fin_table.setItem(row, 1, QTableWidgetItem(field.farm_name or "-"))
            self._fin_table.setItem(row, 2, QTableWidgetItem(f"{field.acreage:.1f}"))
            self._fin_table.setItem(row, 3, QTableWidgetItem(f"${field.total_cost:,.2f}"))
            self._fin_table.setItem(row, 4, QTableWidgetItem(f"${field.cost_per_acre:,.2f}"))
            self._fin_table.setItem(row, 5, QTableWidgetItem(f"${field.revenue:,.2f}"))

            profit_item = QTableWidgetItem(f"${field.profit:,.2f}")
            profit_item.setForeground(QColor(COLORS["success"] if field.profit >= 0 else COLORS["error"]))
            self._fin_table.setItem(row, 6, profit_item)

        # Update charts
        if HAS_PYQTGRAPH:
            self._update_fin_cost_chart(report)
            self._update_fin_profit_chart(report)

    def _load_equipment_report(self, date_from: str, date_to: str):
        """Load equipment report."""
        report, error = self._reports_api.get_equipment_report(date_from, date_to)

        if error:
            return

        self._equipment_report = report

        # Update summary cards
        self._equip_value_label.setText(f"${report.total_fleet_value:,.2f}")
        self._equip_hours_label.setText(f"{report.total_hours:,.1f}")

        # Update maintenance table
        alerts = report.maintenance_alerts[:10]  # Show top 10
        self._maint_table.setRowCount(len(alerts))
        for row, alert in enumerate(alerts):
            self._maint_table.setItem(row, 0, QTableWidgetItem(alert.equipment_name))
            self._maint_table.setItem(row, 1, QTableWidgetItem((alert.maintenance_type or "").replace("_", " ").title()))
            self._maint_table.setItem(row, 2, QTableWidgetItem(alert.next_service_date or "-"))

            status_item = QTableWidgetItem(alert.urgency.replace("_", " ").title())
            status_item.setForeground(QColor(alert.urgency_color))
            self._maint_table.setItem(row, 3, status_item)

        # Update chart
        if HAS_PYQTGRAPH and report.hours_by_type:
            self._update_equip_hours_chart(report)

    def _load_inventory_report(self):
        """Load inventory report."""
        report, error = self._reports_api.get_inventory_report()

        if error:
            return

        self._inventory_report = report

        # Update summary cards
        self._inv_value_label.setText(f"${report.total_value:,.2f}")
        self._inv_low_label.setText(str(report.low_stock_count))

        # Update low stock table
        items = report.low_stock_items[:10]  # Show top 10
        self._low_stock_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._low_stock_table.setItem(row, 0, QTableWidgetItem(item.name))
            self._low_stock_table.setItem(row, 1, QTableWidgetItem(item.category_display))
            self._low_stock_table.setItem(row, 2, QTableWidgetItem(f"{item.quantity:.1f}"))
            self._low_stock_table.setItem(row, 3, QTableWidgetItem(item.unit))

        # Update chart
        if HAS_PYQTGRAPH and report.value_by_category:
            self._update_inv_value_chart(report)

    def _load_field_report(self, date_from: str, date_to: str):
        """Load field performance report."""
        report, error = self._reports_api.get_field_performance_report(date_from, date_to)

        if error:
            return

        self._field_report = report

        # Update summary cards
        self._field_count_label.setText(str(report.total_fields))
        self._field_acres_label.setText(f"{report.total_acreage:,.1f}")
        self._field_yield_label.setText(f"{report.avg_yield:.1f} bu/acre" if report.avg_yield else "-")
        self._field_best_label.setText(report.best_field or "-")

        # Update table
        self._fields_table.setRowCount(len(report.fields))
        for row, field in enumerate(report.fields):
            self._fields_table.setItem(row, 0, QTableWidgetItem(field.field_name))
            self._fields_table.setItem(row, 1, QTableWidgetItem(field.farm_name or "-"))
            self._fields_table.setItem(row, 2, QTableWidgetItem(f"{field.acreage:.1f}"))
            self._fields_table.setItem(row, 3, QTableWidgetItem(field.crop_display))
            self._fields_table.setItem(row, 4, QTableWidgetItem(str(field.operation_count)))
            self._fields_table.setItem(row, 5, QTableWidgetItem(f"${field.total_cost:,.2f}"))
            self._fields_table.setItem(row, 6, QTableWidgetItem(f"${field.cost_per_acre:,.2f}"))
            self._fields_table.setItem(row, 7, QTableWidgetItem(field.yield_display))

        # Update charts
        if HAS_PYQTGRAPH:
            self._update_field_yield_chart(report)
            self._update_field_crop_chart(report)

    # ========================================================================
    # CHART UPDATES
    # ========================================================================

    def _update_ops_type_chart(self, report: OperationsReport):
        """Update operations by type bar chart."""
        self._ops_type_chart.clear()

        types = list(report.operations_by_type.keys())
        counts = list(report.operations_by_type.values())

        if not types:
            return

        x = np.arange(len(types))
        colors = [OPERATION_COLORS.get(t, "#757575") for t in types]

        bar = pg.BarGraphItem(x=x, height=counts, width=0.6, brushes=colors)
        self._ops_type_chart.addItem(bar)

        # Set axis labels
        ax = self._ops_type_chart.getAxis('bottom')
        ax.setTicks([[(i, t.replace("_", " ").title()[:8]) for i, t in enumerate(types)]])

    def _update_ops_monthly_chart(self, report: OperationsReport):
        """Update monthly costs line chart."""
        self._ops_monthly_chart.clear()

        if not report.monthly_costs:
            return

        months = [m.month for m in report.monthly_costs]
        costs = [m.cost for m in report.monthly_costs]

        x = np.arange(len(months))

        pen = pg.mkPen(color=COLORS["primary"], width=2)
        self._ops_monthly_chart.plot(x, costs, pen=pen, symbol='o', symbolBrush=COLORS["primary"])

        ax = self._ops_monthly_chart.getAxis('bottom')
        ax.setTicks([[(i, m[-5:]) for i, m in enumerate(months)]])  # Show MM only

    def _update_fin_cost_chart(self, report: FinancialReport):
        """Update cost by category bar chart."""
        self._fin_cost_chart.clear()

        if not report.cost_by_category:
            return

        categories = list(report.cost_by_category.keys())
        values = list(report.cost_by_category.values())

        x = np.arange(len(categories))
        colors = [OPERATION_COLORS.get(c, "#757575") for c in categories]

        bar = pg.BarGraphItem(x=x, height=values, width=0.6, brushes=colors)
        self._fin_cost_chart.addItem(bar)

        ax = self._fin_cost_chart.getAxis('bottom')
        ax.setTicks([[(i, c.replace("_", " ").title()[:8]) for i, c in enumerate(categories)]])

    def _update_fin_profit_chart(self, report: FinancialReport):
        """Update profit by field bar chart."""
        self._fin_profit_chart.clear()

        if not report.fields:
            return

        fields = [f.field_name[:10] for f in report.fields[:10]]  # Top 10
        profits = [f.profit for f in report.fields[:10]]

        x = np.arange(len(fields))
        colors = [COLORS["success"] if p >= 0 else COLORS["error"] for p in profits]

        bar = pg.BarGraphItem(x=x, height=profits, width=0.6, brushes=colors)
        self._fin_profit_chart.addItem(bar)

        ax = self._fin_profit_chart.getAxis('bottom')
        ax.setTicks([[(i, f) for i, f in enumerate(fields)]])

    def _update_equip_hours_chart(self, report: EquipmentReport):
        """Update equipment hours by type chart."""
        self._equip_hours_chart.clear()

        if not report.hours_by_type:
            return

        types = list(report.hours_by_type.keys())
        hours = list(report.hours_by_type.values())

        x = np.arange(len(types))

        bar = pg.BarGraphItem(x=x, height=hours, width=0.6, brush=COLORS["secondary"])
        self._equip_hours_chart.addItem(bar)

        ax = self._equip_hours_chart.getAxis('bottom')
        ax.setTicks([[(i, t.replace("_", " ").title()[:8]) for i, t in enumerate(types)]])

    def _update_inv_value_chart(self, report: InventoryReport):
        """Update inventory value by category chart."""
        self._inv_value_chart.clear()

        if not report.value_by_category:
            return

        categories = list(report.value_by_category.keys())
        values = list(report.value_by_category.values())

        x = np.arange(len(categories))

        bar = pg.BarGraphItem(x=x, height=values, width=0.6, brush=COLORS["warning"])
        self._inv_value_chart.addItem(bar)

        ax = self._inv_value_chart.getAxis('bottom')
        ax.setTicks([[(i, c.replace("_", " ").title()[:8]) for i, c in enumerate(categories)]])

    def _update_field_yield_chart(self, report: FieldPerformanceReport):
        """Update yield by field chart."""
        self._field_yield_chart.clear()

        fields_with_yield = [f for f in report.fields if f.yield_per_acre]
        if not fields_with_yield:
            return

        fields = [f.field_name[:10] for f in fields_with_yield[:10]]
        yields = [f.yield_per_acre for f in fields_with_yield[:10]]

        x = np.arange(len(fields))

        bar = pg.BarGraphItem(x=x, height=yields, width=0.6, brush=COLORS["success"])
        self._field_yield_chart.addItem(bar)

        ax = self._field_yield_chart.getAxis('bottom')
        ax.setTicks([[(i, f) for i, f in enumerate(fields)]])

    def _update_field_crop_chart(self, report: FieldPerformanceReport):
        """Update acreage by crop chart."""
        self._field_crop_chart.clear()

        if not report.acreage_by_crop:
            return

        crops = list(report.acreage_by_crop.keys())
        acreage = list(report.acreage_by_crop.values())

        x = np.arange(len(crops))

        bar = pg.BarGraphItem(x=x, height=acreage, width=0.6, brush=COLORS["primary"])
        self._field_crop_chart.addItem(bar)

        ax = self._field_crop_chart.getAxis('bottom')
        ax.setTicks([[(i, c.replace("_", " ").title()[:8]) for i, c in enumerate(crops)]])

    # ========================================================================
    # EXPORT
    # ========================================================================

    def _handle_export(self, format_type: str):
        """
        Handle export request from toolbar.

        Args:
            format_type: Export format (csv, excel, pdf)

        Returns:
            Tuple of (content_bytes, filename, content_type)
        """
        current_tab = self._tabs.currentIndex()
        report_types = ["operations", "financial", "equipment", "fields"]
        report_type = report_types[current_tab] if current_tab < len(report_types) else "operations"

        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        api = get_export_api()
        result, error = api.export_reports(report_type, format_type, date_from, date_to)

        if error:
            raise Exception(error)

        return result.content, result.filename, result.content_type
