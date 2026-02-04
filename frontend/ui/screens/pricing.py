"""
AgTools Pricing Screen

Price management, supplier quotes, and buy/wait recommendations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QComboBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QFormLayout, QMessageBox,
    QLineEdit, QDateEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS, set_widget_class
from models.pricing import (
    SetPriceRequest, BuyRecommendationRequest, PriceAlert,
)
from api.pricing_api import get_pricing_api
from database.local_db import get_local_db


class SetPriceDialog(QDialog):
    """Dialog for setting a custom supplier price."""

    def __init__(self, product_id: str, current_price: float, parent=None):
        super().__init__(parent)
        self._product_id = product_id
        self._current_price = current_price
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Set Supplier Price")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Product info
        info_label = QLabel(f"Product: {self._product_id}")
        info_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(info_label)

        current_label = QLabel(f"Current Price: ${self._current_price:.2f}")
        current_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(current_label)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        # New price
        self._price_spin = QDoubleSpinBox()
        self._price_spin.setRange(0.01, 10000)
        self._price_spin.setValue(self._current_price)
        self._price_spin.setPrefix("$")
        self._price_spin.setDecimals(2)
        form.addRow("New Price:", self._price_spin)

        # Supplier
        self._supplier_input = QLineEdit()
        self._supplier_input.setPlaceholderText("e.g., CHS, Nutrien, Local Co-op")
        form.addRow("Supplier:", self._supplier_input)

        # Valid until
        self._valid_date = QDateEdit()
        self._valid_date.setCalendarPopup(True)
        self._valid_date.setDate(QDate.currentDate().addDays(30))
        form.addRow("Valid Until:", self._valid_date)

        # Notes
        self._notes_input = QLineEdit()
        self._notes_input.setPlaceholderText("Optional notes")
        form.addRow("Notes:", self._notes_input)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_request(self) -> SetPriceRequest:
        """Get the SetPriceRequest from dialog inputs."""
        return SetPriceRequest(
            product_id=self._product_id,
            price=self._price_spin.value(),
            supplier=self._supplier_input.text() or None,
            valid_until=self._valid_date.date().toString("yyyy-MM-dd"),
            notes=self._notes_input.text() or None,
        )


class PriceListTab(QWidget):
    """Tab showing all product prices with filtering."""

    price_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_pricing_api()
        self._prices = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Filter bar
        filter_frame = QFrame()
        set_widget_class(filter_frame, "card")
        filter_layout = QHBoxLayout(filter_frame)

        filter_layout.addWidget(QLabel("Category:"))
        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories", None)
        self._category_combo.addItem("Fertilizer", "fertilizer")
        self._category_combo.addItem("Pesticide", "pesticide")
        self._category_combo.addItem("Seed", "seed")
        self._category_combo.addItem("Fuel", "fuel")
        self._category_combo.addItem("Custom Application", "custom_application")
        self._category_combo.currentIndexChanged.connect(self._load_prices)
        filter_layout.addWidget(self._category_combo)

        filter_layout.addWidget(QLabel("Region:"))
        self._region_combo = QComboBox()
        self._region_combo.addItem("Midwest Corn Belt", "midwest_corn_belt")
        self._region_combo.addItem("Northern Plains", "northern_plains")
        self._region_combo.addItem("Southern Plains", "southern_plains")
        self._region_combo.addItem("Delta", "delta")
        self._region_combo.addItem("Southeast", "southeast")
        self._region_combo.currentIndexChanged.connect(self._load_prices)
        filter_layout.addWidget(self._region_combo)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_prices)
        filter_layout.addWidget(refresh_btn)

        layout.addWidget(filter_frame)

        # Price table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Product", "Category", "Price", "Unit", "Source", "Actions"
        ])

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self._table)

        # Summary
        summary_layout = QHBoxLayout()
        self._count_label = QLabel("0 products")
        self._count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        summary_layout.addWidget(self._count_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Initial load
        self._load_prices()

    def _load_prices(self) -> None:
        """Load prices from API with offline fallback."""
        category = self._category_combo.currentData()
        region = self._region_combo.currentData()
        cache_key = f"prices_{category or 'all'}_{region}"

        success, result = self._api.get_prices(category=category, region=region)

        if success:
            self._prices = result.prices
            # Cache for offline use
            try:
                db = get_local_db()
                db.cache_set("pricing", cache_key, {
                    "prices": {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in self._prices.items()}
                }, ttl_hours=24)
            except Exception:
                pass  # Cache failure is not critical
            self._update_table()
        else:
            # Try to load from cache
            try:
                db = get_local_db()
                cached = db.cache_get("pricing", cache_key)
                if cached and "prices" in cached:
                    from models.pricing import ProductPrice
                    self._prices = {k: ProductPrice.from_dict(v) if isinstance(v, dict) else v
                                   for k, v in cached["prices"].items()}
                    self._update_table()
                    QMessageBox.information(self, "Offline Mode",
                        "Using cached prices. Connect to server for latest data.")
                    return
            except Exception:
                pass

            # No cache available
            error_msg = "Unable to connect to server" if "connect" in str(result).lower() else str(result)
            QMessageBox.warning(self, "Error", f"Failed to load prices: {error_msg}\n\nMake sure the backend server is running.")

    def _update_table(self) -> None:
        """Update the price table."""
        self._table.setRowCount(len(self._prices))

        for row, (product_id, price) in enumerate(self._prices.items()):
            # Product
            self._table.setItem(row, 0, QTableWidgetItem(price.description or product_id))

            # Category
            self._table.setItem(row, 1, QTableWidgetItem(price.category.title()))

            # Price
            price_item = QTableWidgetItem(f"${price.price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, price_item)

            # Unit
            self._table.setItem(row, 3, QTableWidgetItem(price.unit))

            # Source with color
            source_item = QTableWidgetItem(price.source.title())
            if price.source == "custom" or price.source == "supplier":
                source_item.setForeground(QColor(COLORS['success']))
            self._table.setItem(row, 4, source_item)

            # Actions button
            edit_btn = QPushButton("Set Price")
            edit_btn.setProperty("product_id", product_id)
            edit_btn.setProperty("current_price", price.price)
            edit_btn.clicked.connect(self._on_set_price)
            self._table.setCellWidget(row, 5, edit_btn)

        self._count_label.setText(f"{len(self._prices)} products")

    def _on_set_price(self) -> None:
        """Handle set price button click."""
        btn = self.sender()
        product_id = btn.property("product_id")
        current_price = btn.property("current_price")

        dialog = SetPriceDialog(product_id, current_price, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            request = dialog.get_request()
            success, result = self._api.set_price(request)

            if success:
                QMessageBox.information(
                    self, "Price Updated",
                    f"Price updated to ${result.new_price:.2f}\n"
                    f"Savings vs default: ${result.savings_vs_default:.2f} ({result.savings_percent:.1f}%)"
                )
                self._load_prices()
                self.price_updated.emit()
            else:
                QMessageBox.warning(self, "Error", f"Failed to update price: {result}")


class BuyRecommendationTab(QWidget):
    """Tab for buy now vs wait recommendations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_pricing_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left - Input
        input_frame = QFrame()
        set_widget_class(input_frame, "card")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(12)

        header = QLabel("Buy or Wait Analysis")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        input_layout.addWidget(header)

        desc = QLabel("Get recommendations on whether to buy now or wait based on price trends.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setWordWrap(True)
        input_layout.addWidget(desc)

        form = QFormLayout()
        form.setSpacing(10)

        # Product selection
        self._product_combo = QComboBox()
        self._product_combo.setEditable(True)
        self._product_combo.setPlaceholderText("Select or type product ID")
        # Add common products
        common_products = [
            "urea_46", "uan_28", "dap_18_46", "map_11_52", "potash_60",
            "roundup_powermax", "warrant", "bicep_ii_magnum",
            "corn_seed", "soybean_seed",
        ]
        self._product_combo.addItems(common_products)
        form.addRow("Product:", self._product_combo)

        # Quantity
        self._quantity_spin = QDoubleSpinBox()
        self._quantity_spin.setRange(1, 100000)
        self._quantity_spin.setValue(100)
        self._quantity_spin.setDecimals(0)
        form.addRow("Quantity Needed:", self._quantity_spin)

        # Deadline
        self._deadline_date = QDateEdit()
        self._deadline_date.setCalendarPopup(True)
        self._deadline_date.setDate(QDate.currentDate().addMonths(2))
        form.addRow("Purchase By:", self._deadline_date)

        input_layout.addLayout(form)
        input_layout.addStretch()

        # Analyze button
        analyze_btn = QPushButton("Get Recommendation")
        analyze_btn.setMinimumHeight(44)
        analyze_btn.clicked.connect(self._analyze)
        input_layout.addWidget(analyze_btn)

        input_frame.setMaximumWidth(350)
        layout.addWidget(input_frame)

        # Right - Results
        results_frame = QFrame()
        set_widget_class(results_frame, "card")
        results_layout = QVBoxLayout(results_frame)
        results_layout.setSpacing(16)

        # Recommendation header
        self._rec_label = QLabel("--")
        rec_font = QFont()
        rec_font.setPointSize(24)
        rec_font.setWeight(QFont.Weight.Bold)
        self._rec_label.setFont(rec_font)
        self._rec_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._rec_label.setStyleSheet(f"color: {COLORS['text_disabled']};")
        results_layout.addWidget(self._rec_label)

        # Product info
        self._product_info = QLabel("")
        self._product_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._product_info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        results_layout.addWidget(self._product_info)

        # Price analysis grid
        analysis_frame = QFrame()
        analysis_frame.setStyleSheet(f"background-color: {COLORS['surface_variant']}; border-radius: 8px; padding: 12px;")
        analysis_layout = QGridLayout(analysis_frame)
        analysis_layout.setSpacing(8)

        analysis_labels = [
            ("current_price", "Current Price"),
            ("total_cost", "Total Cost"),
            ("trend", "Price Trend"),
            ("vs_avg", "vs 90-Day Avg"),
        ]

        for i, (key, label) in enumerate(analysis_labels):
            row = i // 2
            col = (i % 2) * 2

            label_widget = QLabel(label + ":")
            label_widget.setStyleSheet(f"color: {COLORS['text_secondary']};")
            analysis_layout.addWidget(label_widget, row, col)

            value_widget = QLabel("--")
            value_widget.setObjectName(key)
            value_widget.setStyleSheet("font-weight: 600;")
            analysis_layout.addWidget(value_widget, row, col + 1)

        results_layout.addWidget(analysis_frame)

        # Reasoning
        self._reasoning_label = QLabel("")
        self._reasoning_label.setWordWrap(True)
        self._reasoning_label.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 8px;")
        results_layout.addWidget(self._reasoning_label)

        # Action
        self._action_label = QLabel("")
        self._action_label.setWordWrap(True)
        self._action_label.setStyleSheet(f"""
            background-color: {COLORS['info_light']};
            border: 1px solid {COLORS['info']};
            border-radius: 4px;
            padding: 12px;
        """)
        self._action_label.setVisible(False)
        results_layout.addWidget(self._action_label)

        # Potential savings
        self._savings_label = QLabel("")
        self._savings_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
        self._savings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_layout.addWidget(self._savings_label)

        results_layout.addStretch()
        layout.addWidget(results_frame, 1)

    def _analyze(self) -> None:
        """Get buy recommendation."""
        product_id = self._product_combo.currentText()
        if not product_id:
            QMessageBox.warning(self, "Error", "Please select a product")
            return

        request = BuyRecommendationRequest(
            product_id=product_id,
            quantity_needed=self._quantity_spin.value(),
            purchase_deadline=self._deadline_date.date().toString("yyyy-MM-dd"),
        )

        success, result = self._api.get_buy_recommendation(request)

        if not success:
            QMessageBox.warning(self, "Error", f"Failed to get recommendation: {result}")
            return

        # Update recommendation
        rec_colors = {
            "buy_now": COLORS['success'],
            "wait": COLORS['warning'],
            "split_purchase": COLORS['info'],
            "forward_contract": COLORS['primary'],
        }
        rec_display = {
            "buy_now": "BUY NOW",
            "wait": "WAIT",
            "split_purchase": "SPLIT PURCHASE",
            "forward_contract": "FORWARD CONTRACT",
        }

        rec = result.recommendation.lower()
        self._rec_label.setText(rec_display.get(rec, result.recommendation.upper()))
        self._rec_label.setStyleSheet(f"color: {rec_colors.get(rec, COLORS['text_primary'])};")

        # Product info
        self._product_info.setText(f"{result.product_description} - {result.quantity_needed:.0f} {result.unit}")

        # Analysis values
        analysis_frame = self.findChild(QFrame)
        if analysis_frame:
            current_price = analysis_frame.findChild(QLabel, "current_price")
            if current_price:
                current_price.setText(f"${result.current_price:.2f}/{result.unit}")

            total_cost = analysis_frame.findChild(QLabel, "total_cost")
            if total_cost:
                total_cost.setText(f"${result.current_total_cost:,.0f}")

            trend = analysis_frame.findChild(QLabel, "trend")
            if trend:
                trend_colors = {"rising": COLORS['error'], "falling": COLORS['success'], "stable": COLORS['text_primary']}
                trend.setText(result.price_analysis.trend.upper())
                trend.setStyleSheet(f"font-weight: 600; color: {trend_colors.get(result.price_analysis.trend, COLORS['text_primary'])};")

            vs_avg = analysis_frame.findChild(QLabel, "vs_avg")
            if vs_avg:
                pct = result.price_analysis.current_vs_90_day_avg_percent
                sign = "+" if pct > 0 else ""
                color = COLORS['error'] if pct > 0 else COLORS['success']
                vs_avg.setText(f"{sign}{pct:.1f}%")
                vs_avg.setStyleSheet(f"font-weight: 600; color: {color};")

        # Reasoning
        self._reasoning_label.setText(result.reasoning)

        # Action
        if result.suggested_action:
            self._action_label.setText(f"Suggested Action: {result.suggested_action}")
            self._action_label.setVisible(True)
        else:
            self._action_label.setVisible(False)

        # Savings
        if result.potential_savings_if_wait > 0:
            self._savings_label.setText(f"Potential savings if you wait: ${result.potential_savings_if_wait:,.0f}")
        else:
            self._savings_label.setText("")


class AlertsTab(QWidget):
    """Tab showing price alerts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._api = get_pricing_api()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Price Alerts")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        header_layout.addWidget(header)

        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_alerts)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Alerts list
        self._alerts_frame = QFrame()
        set_widget_class(self._alerts_frame, "card")
        self._alerts_layout = QVBoxLayout(self._alerts_frame)
        self._alerts_layout.setSpacing(8)

        layout.addWidget(self._alerts_frame)
        layout.addStretch()

        # Initial load
        self._load_alerts()

    def _load_alerts(self) -> None:
        """Load alerts from API."""
        success, result = self._api.get_alerts()

        if not success:
            self._show_message(f"Failed to load alerts: {result}", is_error=True)
            return

        # Clear existing
        while self._alerts_layout.count():
            item = self._alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not result.alerts:
            no_alerts = QLabel("No alerts at this time")
            no_alerts.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 20px;")
            no_alerts.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._alerts_layout.addWidget(no_alerts)
            return

        # Add alert cards
        for alert in result.alerts:
            card = self._create_alert_card(alert)
            self._alerts_layout.addWidget(card)

    def _create_alert_card(self, alert: PriceAlert) -> QFrame:
        """Create a card for an alert."""
        card = QFrame()

        # Color based on alert type
        if "expir" in alert.alert_type.lower():
            bg = COLORS['warning_light']
            border = COLORS['warning']
            icon = "⚠"
        elif "above" in alert.alert_type.lower():
            bg = COLORS['error_light']
            border = COLORS['error']
            icon = "📈"
        else:
            bg = COLORS['info_light']
            border = COLORS['info']
            icon = "ℹ"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 12px;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setSpacing(12)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20pt; background: transparent;")
        layout.addWidget(icon_label)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Title
        title = QLabel(alert.description or alert.product_id)
        title.setStyleSheet("font-weight: 600; background: transparent;")
        content_layout.addWidget(title)

        # Message
        msg = QLabel(alert.message)
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        content_layout.addWidget(msg)

        # Supplier/expiry info
        if alert.supplier or alert.days_until_expiry is not None:
            info_parts = []
            if alert.supplier:
                info_parts.append(f"Supplier: {alert.supplier}")
            if alert.days_until_expiry is not None:
                info_parts.append(f"Expires in {alert.days_until_expiry} days")
            info = QLabel(" | ".join(info_parts))
            info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt; background: transparent;")
            content_layout.addWidget(info)

        layout.addLayout(content_layout, 1)

        return card

    def _show_message(self, message: str, is_error: bool = False) -> None:
        """Show a message in the alerts area."""
        while self._alerts_layout.count():
            item = self._alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        label = QLabel(message)
        color = COLORS['error'] if is_error else COLORS['text_secondary']
        label.setStyleSheet(f"color: {color}; padding: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._alerts_layout.addWidget(label)


class PricingScreen(QWidget):
    """
    Main pricing screen with tabbed interface.

    Tabs:
    - Price List: View and manage all product prices
    - Buy/Wait: Get buy or wait recommendations
    - Alerts: View price alerts and expiring quotes
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
        price_list_tab = PriceListTab()
        self._tabs.addTab(price_list_tab, "Price List")
        self._tabs.addTab(BuyRecommendationTab(), "Buy/Wait")
        self._tabs.addTab(AlertsTab(), "Alerts")

        layout.addWidget(self._tabs)
