"""
KPI Card Widget for Advanced Reporting Dashboard

Interactive card component with:
- Value display with trend indicator
- Mini chart (PyQtGraph)
- Drill-down menu (filter, report, expand)
- Expandable detail section

AgTools v6.8.0
"""

from typing import Optional, Dict, List, Any, Callable
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMenu, QWidget, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor

from ..styles import COLORS

# Try to import PyQtGraph for charts
try:
    import pyqtgraph as pg
    import numpy as np
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


class TrendIndicator(QLabel):
    """Small trend arrow indicator."""

    def __init__(self, direction: str = "neutral", change_percent: float = 0, parent=None):
        super().__init__(parent)
        self.update_trend(direction, change_percent)

    def update_trend(self, direction: str, change_percent: float):
        """Update the trend indicator."""
        if direction == "up":
            arrow = "\u25B2"  # Up triangle
            color = COLORS["success"]
        elif direction == "down":
            arrow = "\u25BC"  # Down triangle
            color = COLORS["error"]
        else:
            arrow = "\u25CF"  # Dot
            color = COLORS["text_secondary"]

        if abs(change_percent) > 0.1:
            text = f"{arrow} {abs(change_percent):.1f}%"
        else:
            text = arrow

        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 10pt;
                font-weight: 500;
                padding: 2px 4px;
            }}
        """)


class KPICard(QFrame):
    """
    Interactive KPI card with drill-down capabilities.

    Signals:
        filter_clicked(str, dict): Emitted when filter action selected (kpi_id, filters)
        report_clicked(str): Emitted when report action selected (report_type)
        expand_toggled(bool): Emitted when card expansion state changes
        card_clicked(str): Emitted when card is clicked (kpi_id)
    """

    filter_clicked = pyqtSignal(str, dict)
    report_clicked = pyqtSignal(str)
    expand_toggled = pyqtSignal(bool)
    card_clicked = pyqtSignal(str)

    def __init__(
        self,
        kpi_id: str,
        title: str,
        value: str,
        subtitle: str = "",
        trend: str = "neutral",
        change_percent: float = 0,
        chart_type: str = None,
        chart_data: Dict[str, Any] = None,
        drill_down_report: str = None,
        drill_down_filters: Dict[str, Any] = None,
        detail_data: List[Dict[str, str]] = None,
        parent=None
    ):
        super().__init__(parent)

        self._kpi_id = kpi_id
        self._title = title
        self._value = value
        self._subtitle = subtitle
        self._trend = trend
        self._change_percent = change_percent
        self._chart_type = chart_type
        self._chart_data = chart_data or {}
        self._drill_down_report = drill_down_report
        self._drill_down_filters = drill_down_filters or {}
        self._detail_data = detail_data or []

        self._is_expanded = False
        self._chart_widget = None
        self._detail_widget = None
        self._animation = None

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """Set up the card UI."""
        self.setFixedHeight(180)
        self.setMinimumWidth(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header row: Title + Trend
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self._title_label = QLabel(self._title)
        self._title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11pt;
                font-weight: 500;
                color: {COLORS['text_secondary']};
            }}
        """)
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        self._trend_indicator = TrendIndicator(self._trend, self._change_percent)
        header_layout.addWidget(self._trend_indicator)

        layout.addLayout(header_layout)

        # Value row
        self._value_label = QLabel(self._value)
        self._value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24pt;
                font-weight: 700;
                color: {COLORS['primary_dark']};
            }}
        """)
        layout.addWidget(self._value_label)

        # Subtitle
        if self._subtitle:
            self._subtitle_label = QLabel(self._subtitle)
            self._subtitle_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 10pt;
                    color: {COLORS['text_secondary']};
                }}
            """)
            layout.addWidget(self._subtitle_label)

        # Mini chart
        if self._chart_type and HAS_PYQTGRAPH:
            self._chart_widget = self._create_mini_chart()
            if self._chart_widget:
                layout.addWidget(self._chart_widget)

        layout.addStretch()

        # Expandable detail section (hidden by default)
        self._detail_widget = self._create_detail_section()
        self._detail_widget.setMaximumHeight(0)
        self._detail_widget.setVisible(False)
        layout.addWidget(self._detail_widget)

    def _apply_style(self):
        """Apply card styling."""
        self.setStyleSheet(f"""
            KPICard {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            KPICard:hover {{
                border-color: {COLORS['primary']};
            }}
        """)

    def _create_mini_chart(self) -> Optional[QWidget]:
        """Create a mini chart based on chart type."""
        if not HAS_PYQTGRAPH or not self._chart_data:
            return None

        chart = pg.PlotWidget()
        chart.setBackground('w')
        chart.setFixedHeight(50)
        chart.getPlotItem().hideAxis('left')
        chart.getPlotItem().hideAxis('bottom')
        chart.setMouseEnabled(False, False)

        try:
            if self._chart_type == "line":
                values = self._chart_data.get("values", [])
                if values:
                    x = np.arange(len(values))
                    color = self._chart_data.get("color", COLORS["primary"])
                    pen = pg.mkPen(color=color, width=2)
                    chart.plot(x, values, pen=pen)

            elif self._chart_type == "bar":
                values = self._chart_data.get("values", [])
                colors = self._chart_data.get("colors", [COLORS["primary"]] * len(values))
                if values:
                    x = np.arange(len(values))
                    brushes = [pg.mkBrush(c) for c in colors]
                    bar = pg.BarGraphItem(x=x, height=values, width=0.6, brushes=brushes)
                    chart.addItem(bar)

            elif self._chart_type in ["stacked_bar"]:
                values = self._chart_data.get("values", [])
                colors = self._chart_data.get("colors", [COLORS["primary"]] * len(values))
                if values:
                    x = np.arange(len(values))
                    brushes = [pg.mkBrush(c) for c in colors]
                    bar = pg.BarGraphItem(x=x, height=values, width=0.6, brushes=brushes)
                    chart.addItem(bar)

            # Pie and donut charts not supported in mini view
            elif self._chart_type in ["pie", "donut"]:
                # Show a simple bar representation instead
                values = self._chart_data.get("values", [])
                colors = self._chart_data.get("colors", [COLORS["primary"]] * len(values))
                if values:
                    x = np.arange(len(values))
                    brushes = [pg.mkBrush(c) for c in colors]
                    bar = pg.BarGraphItem(x=x, height=values, width=0.6, brushes=brushes)
                    chart.addItem(bar)

            return chart

        except Exception:
            return None

    def _create_detail_section(self) -> QWidget:
        """Create the expandable detail section."""
        detail = QFrame()
        detail.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface_variant']};
                border-top: 1px solid {COLORS['border']};
                margin-top: 8px;
                padding-top: 8px;
            }}
        """)

        layout = QVBoxLayout(detail)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(4)

        # Add detail rows
        for item in self._detail_data:
            row = QHBoxLayout()
            label = QLabel(item.get("label", ""))
            label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
            value = QLabel(item.get("value", ""))
            value.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500; font-size: 10pt;")
            row.addWidget(label)
            row.addStretch()
            row.addWidget(value)
            layout.addLayout(row)

        return detail

    def mousePressEvent(self, event):
        """Handle mouse press - show drill-down menu."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_drill_down_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click - toggle expansion."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_expand()
        super().mouseDoubleClickEvent(event)

    def _show_drill_down_menu(self, pos):
        """Show the drill-down menu."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary_light']};
                color: {COLORS['text_on_primary']};
            }}
        """)

        # Filter action
        filter_action = menu.addAction("\u2637  Filter Transactions")
        filter_action.triggered.connect(
            lambda: self.filter_clicked.emit(self._kpi_id, self._drill_down_filters)
        )

        # Report action
        report_action = menu.addAction("\u2191  Open Full Report")
        report_action.triggered.connect(
            lambda: self.report_clicked.emit(self._drill_down_report or self._kpi_id)
        )

        menu.addSeparator()

        # Expand action
        expand_text = "\u25B2  Collapse Details" if self._is_expanded else "\u25BC  Expand Details"
        expand_action = menu.addAction(expand_text)
        expand_action.triggered.connect(self._toggle_expand)

        menu.exec(pos)

    def _toggle_expand(self):
        """Toggle the expanded state of the card."""
        self._is_expanded = not self._is_expanded

        if self._is_expanded:
            # Expand
            self._detail_widget.setVisible(True)
            self._detail_widget.setMaximumHeight(0)

            # Animate expansion
            self._animation = QPropertyAnimation(self._detail_widget, b"maximumHeight")
            self._animation.setDuration(200)
            self._animation.setStartValue(0)
            self._animation.setEndValue(150)
            self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animation.start()

            # Expand card height
            self.setFixedHeight(330)
        else:
            # Collapse
            self._animation = QPropertyAnimation(self._detail_widget, b"maximumHeight")
            self._animation.setDuration(200)
            self._animation.setStartValue(self._detail_widget.height())
            self._animation.setEndValue(0)
            self._animation.setEasingCurve(QEasingCurve.Type.InCubic)
            self._animation.finished.connect(lambda: self._detail_widget.setVisible(False))
            self._animation.start()

            # Collapse card height
            self.setFixedHeight(180)

        self.expand_toggled.emit(self._is_expanded)

    def update_data(
        self,
        value: str = None,
        subtitle: str = None,
        trend: str = None,
        change_percent: float = None,
        chart_data: Dict[str, Any] = None,
        detail_data: List[Dict[str, str]] = None
    ):
        """Update the card data."""
        if value is not None:
            self._value = value
            self._value_label.setText(value)

        if subtitle is not None:
            self._subtitle = subtitle
            if hasattr(self, '_subtitle_label'):
                self._subtitle_label.setText(subtitle)

        if trend is not None or change_percent is not None:
            self._trend = trend or self._trend
            self._change_percent = change_percent if change_percent is not None else self._change_percent
            self._trend_indicator.update_trend(self._trend, self._change_percent)

        if chart_data is not None:
            self._chart_data = chart_data
            # Recreate chart with new data
            if self._chart_widget:
                layout = self.layout()
                layout.removeWidget(self._chart_widget)
                self._chart_widget.deleteLater()
                self._chart_widget = self._create_mini_chart()
                if self._chart_widget:
                    layout.insertWidget(3, self._chart_widget)

        if detail_data is not None:
            self._detail_data = detail_data
            # Rebuild detail section
            layout = self.layout()
            layout.removeWidget(self._detail_widget)
            self._detail_widget.deleteLater()
            self._detail_widget = self._create_detail_section()
            self._detail_widget.setMaximumHeight(0 if not self._is_expanded else 150)
            self._detail_widget.setVisible(self._is_expanded)
            layout.addWidget(self._detail_widget)

    @property
    def kpi_id(self) -> str:
        """Get the KPI ID."""
        return self._kpi_id

    @property
    def is_expanded(self) -> bool:
        """Check if card is expanded."""
        return self._is_expanded


class KPICardGrid(QWidget):
    """
    Grid container for KPI cards with responsive layout.
    """

    def __init__(self, columns: int = 2, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._cards: List[KPICard] = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the grid layout."""
        from PyQt6.QtWidgets import QGridLayout
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(16)

    def add_card(self, card: KPICard):
        """Add a card to the grid."""
        self._cards.append(card)
        row = (len(self._cards) - 1) // self._columns
        col = (len(self._cards) - 1) % self._columns
        self._layout.addWidget(card, row, col)

    def clear(self):
        """Remove all cards."""
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def get_card(self, kpi_id: str) -> Optional[KPICard]:
        """Get a card by KPI ID."""
        for card in self._cards:
            if card.kpi_id == kpi_id:
                return card
        return None

    @property
    def cards(self) -> List[KPICard]:
        """Get all cards."""
        return self._cards.copy()
