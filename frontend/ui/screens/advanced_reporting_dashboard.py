"""
Advanced Reporting Dashboard Screen

Unified dashboard combining farm operations and financial KPIs
with drill-down capabilities.

AgTools v6.8.0
"""

from datetime import date, datetime
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QDateEdit, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer

from ..styles import COLORS
from ..widgets.kpi_card import KPICard, KPICardGrid
from ..widgets.common import LoadingOverlay, StatusMessage
from ..widgets.export_toolbar import ExportToolbar

from api.unified_dashboard_api import (
    get_unified_dashboard_api, UnifiedDashboard, KPI,
    TransactionList
)
from api.export_api import get_export_api


class SectionHeader(QFrame):
    """Section header with icon and title."""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self._setup_ui(title, icon)

    def _setup_ui(self, title: str, icon: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 18pt; color: {COLORS['primary']};")
            layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14pt;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
        """)
        layout.addWidget(title_label)
        layout.addStretch()


class AlertBanner(QFrame):
    """Alert banner showing critical/warning alerts."""

    clicked = pyqtSignal(str)  # kpi_id

    def __init__(self, alerts: List[Dict], parent=None):
        super().__init__(parent)
        self._alerts = alerts
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Determine severity
        has_critical = any(a.severity == "critical" for a in self._alerts)
        bg_color = COLORS['error_light'] if has_critical else COLORS['warning_light']
        text_color = COLORS['error'] if has_critical else COLORS['warning']

        self.setStyleSheet(f"""
            AlertBanner {{
                background-color: {bg_color};
                border: 1px solid {text_color};
                border-radius: 4px;
            }}
        """)

        # Icon
        icon = QLabel("\u26A0" if not has_critical else "\u2718")
        icon.setStyleSheet(f"font-size: 16pt; color: {text_color};")
        layout.addWidget(icon)

        # Message
        if len(self._alerts) == 1:
            msg = self._alerts[0].message
        else:
            msg = f"{len(self._alerts)} alerts require attention"

        msg_label = QLabel(msg)
        msg_label.setStyleSheet(f"color: {text_color}; font-weight: 500;")
        layout.addWidget(msg_label)

        layout.addStretch()

        # View button
        view_btn = QPushButton("View Details")
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {text_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error'] if has_critical else COLORS['warning']};
            }}
        """)
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.clicked.connect(self._show_details)
        layout.addWidget(view_btn)

    def _show_details(self):
        """Show alert details dialog."""
        if self._alerts and self._alerts[0].kpi:
            self.clicked.emit(self._alerts[0].kpi)


class FilteredTransactionsDialog(QDialog):
    """Dialog showing filtered transactions from KPI drill-down."""

    def __init__(self, title: str, transactions: TransactionList, parent=None):
        super().__init__(parent)
        self._transactions = transactions
        self.setWindowTitle(title)
        self.setMinimumSize(700, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel(f"Showing {self._transactions.count} transactions")
        header.setStyleSheet(f"font-size: 12pt; color: {COLORS['text_secondary']};")
        layout.addWidget(header)

        # Table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Date", "Vendor", "Category", "Description", "Amount"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLORS['border']};
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_variant']};
                padding: 8px;
                border: none;
                font-weight: 600;
            }}
        """)

        # Populate table
        table.setRowCount(len(self._transactions.transactions))
        for i, txn in enumerate(self._transactions.transactions):
            table.setItem(i, 0, QTableWidgetItem(txn.date))
            table.setItem(i, 1, QTableWidgetItem(txn.vendor or "-"))
            table.setItem(i, 2, QTableWidgetItem(txn.category or "-"))
            table.setItem(i, 3, QTableWidgetItem(txn.description or "-"))

            amount_item = QTableWidgetItem(txn.amount_display)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(i, 4, amount_item)

        layout.addWidget(table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)


class AdvancedReportingDashboard(QWidget):
    """
    Advanced Reporting Dashboard combining farm + financial KPIs.

    Signals:
        navigate_to(str): Request navigation to another screen/report
    """

    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_unified_dashboard_api()
        self._dashboard_data: Optional[UnifiedDashboard] = None
        self._auto_refresh_timer: Optional[QTimer] = None

        self._setup_ui()
        self._load_dashboard()

    def _setup_ui(self):
        """Initialize the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        # Title
        title = QLabel("Analytics Dashboard")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 20pt;
                font-weight: 600;
                color: {COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Date range picker
        date_frame = QFrame()
        date_layout = QHBoxLayout(date_frame)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)

        date_layout.addWidget(QLabel("From:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate(date.today().year, 1, 1))
        self._date_from.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self._date_from)

        date_layout.addWidget(QLabel("To:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.dateChanged.connect(self._on_date_changed)
        date_layout.addWidget(self._date_to)

        header_layout.addWidget(date_frame)

        # Refresh button
        refresh_btn = QPushButton("\u21BB Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
        """)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_dashboard)
        header_layout.addWidget(refresh_btn)

        # Export toolbar
        self._export_toolbar = ExportToolbar()
        self._export_toolbar.set_export_handler(self._handle_export)
        header_layout.addWidget(self._export_toolbar)

        layout.addLayout(header_layout)

        # Status message
        self._status_message = StatusMessage()
        layout.addWidget(self._status_message)

        # Alert banner placeholder
        self._alert_container = QVBoxLayout()
        layout.addLayout(self._alert_container)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(24)

        # Financial KPIs Section
        self._content_layout.addWidget(SectionHeader("Financial Performance", "\U0001F4B0"))
        self._financial_grid = KPICardGrid(columns=2)
        self._content_layout.addWidget(self._financial_grid)

        # Farm Operations KPIs Section
        self._content_layout.addWidget(SectionHeader("Farm Operations", "\U0001F33E"))
        self._farm_grid = KPICardGrid(columns=2)
        self._content_layout.addWidget(self._farm_grid)

        # Revenue Trend Section
        self._content_layout.addWidget(SectionHeader("Revenue Trend", "\U0001F4C8"))
        self._trend_chart_container = QFrame()
        self._trend_chart_container.setMinimumHeight(200)
        self._trend_chart_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        self._content_layout.addWidget(self._trend_chart_container)

        # Last updated
        self._last_updated_label = QLabel("Last updated: Never")
        self._last_updated_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        self._last_updated_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._content_layout.addWidget(self._last_updated_label)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Loading overlay
        self._loading = LoadingOverlay(self)

    def _load_dashboard(self):
        """Load dashboard data from API."""
        self._loading.show_loading("Loading dashboard...")

        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        dashboard, error = self._api.get_dashboard(date_from, date_to)

        self._loading.hide_loading()

        if error:
            self._status_message.show_error(f"Failed to load dashboard: {error}")
            return

        self._dashboard_data = dashboard
        self._update_ui()

    def _update_ui(self):
        """Update UI with dashboard data."""
        if not self._dashboard_data:
            return

        # Clear existing cards
        self._financial_grid.clear()
        self._farm_grid.clear()

        # Update alerts
        self._update_alerts()

        # Add financial KPI cards
        for kpi_id, kpi in self._dashboard_data.financial_kpis.items():
            card = self._create_kpi_card(kpi)
            self._financial_grid.add_card(card)

        # Add farm KPI cards
        for kpi_id, kpi in self._dashboard_data.farm_kpis.items():
            card = self._create_kpi_card(kpi)
            self._farm_grid.add_card(card)

        # Update last updated
        self._last_updated_label.setText(
            f"Last updated: {datetime.now().strftime('%I:%M %p')}"
        )

    def _create_kpi_card(self, kpi: KPI) -> KPICard:
        """Create a KPI card from KPI data."""
        card = KPICard(
            kpi_id=kpi.kpi_id,
            title=kpi.title,
            value=kpi.formatted_value,
            subtitle=kpi.subtitle,
            trend=kpi.trend,
            change_percent=kpi.change_percent,
            chart_type=kpi.chart_type,
            chart_data={
                "labels": kpi.chart_data.labels,
                "values": kpi.chart_data.values,
                "colors": kpi.chart_data.colors,
                "datasets": kpi.chart_data.datasets
            },
            drill_down_report=kpi.drill_down_report,
            drill_down_filters=kpi.drill_down_filters,
            detail_data=[
                {"label": d.label, "value": d.value}
                for d in kpi.detail_data
            ]
        )

        # Connect signals
        card.filter_clicked.connect(self._on_filter_clicked)
        card.report_clicked.connect(self._on_report_clicked)

        return card

    def _update_alerts(self):
        """Update the alert banner."""
        # Clear existing alerts
        while self._alert_container.count():
            item = self._alert_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self._dashboard_data and self._dashboard_data.has_alerts:
            # Filter to critical and warning only
            important_alerts = [
                a for a in self._dashboard_data.alerts
                if a.severity in ("critical", "warning")
            ]

            if important_alerts:
                banner = AlertBanner(important_alerts)
                banner.clicked.connect(self._on_alert_clicked)
                self._alert_container.addWidget(banner)

    def _on_date_changed(self):
        """Handle date range change."""
        # Debounce - wait a moment before reloading
        if hasattr(self, '_date_timer'):
            self._date_timer.stop()

        self._date_timer = QTimer()
        self._date_timer.setSingleShot(True)
        self._date_timer.timeout.connect(self._load_dashboard)
        self._date_timer.start(500)

    def _on_filter_clicked(self, kpi_id: str, filters: Dict[str, Any]):
        """Handle filter drill-down action."""
        self._loading.show_loading("Loading transactions...")

        transactions, error = self._api.get_transactions(
            kpi_type=kpi_id,
            filter_value=filters.get("filter_value"),
            date_from=filters.get("date_from"),
            date_to=filters.get("date_to")
        )

        self._loading.hide_loading()

        if error:
            self._status_message.show_error(f"Failed to load transactions: {error}")
            return

        # Show dialog with transactions
        kpi = self._dashboard_data.all_kpis.get(kpi_id)
        title = f"{kpi.title if kpi else kpi_id} - Transactions"
        dialog = FilteredTransactionsDialog(title, transactions, self)
        dialog.exec()

    def _on_report_clicked(self, report_type: str):
        """Handle report drill-down action."""
        # Map report types to navigation targets
        report_map = {
            "statement_cash_flows": "genfin_reports",
            "profit_loss": "genfin_reports",
            "ar_aging_detail": "genfin_reports",
            "ap_aging_detail": "genfin_reports",
            "cost_per_acre": "reports",
            "field_performance": "reports",
            "equipment": "equipment",
            "financial": "reports",
        }

        target = report_map.get(report_type, "reports")
        self.navigate_to.emit(target)

    def _on_alert_clicked(self, kpi_id: str):
        """Handle alert banner click."""
        # Find and highlight the relevant KPI card
        card = self._financial_grid.get_card(kpi_id) or self._farm_grid.get_card(kpi_id)
        if card:
            # Scroll to card and expand it
            card.setFocus()

    def set_current_user(self, user):
        """Set the current user (called by main window)."""
        self._load_dashboard()

    def showEvent(self, event):
        """Handle show event - refresh data."""
        super().showEvent(event)
        # Optionally refresh when shown
        # self._load_dashboard()

    def start_auto_refresh(self, interval_minutes: int = 5):
        """Start auto-refresh timer."""
        if self._auto_refresh_timer:
            self._auto_refresh_timer.stop()

        self._auto_refresh_timer = QTimer()
        self._auto_refresh_timer.timeout.connect(self._load_dashboard)
        self._auto_refresh_timer.start(interval_minutes * 60 * 1000)

    def stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self._auto_refresh_timer:
            self._auto_refresh_timer.stop()
            self._auto_refresh_timer = None

    def _handle_export(self, format_type: str):
        """
        Handle export request from toolbar.

        Args:
            format_type: Export format (csv, excel, pdf)

        Returns:
            Tuple of (content_bytes, filename, content_type)
        """
        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        api = get_export_api()
        result, error = api.export_unified_dashboard(format_type, date_from, date_to)

        if error:
            raise Exception(error)

        return result.content, result.filename, result.content_type
