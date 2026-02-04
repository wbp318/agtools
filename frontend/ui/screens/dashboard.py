"""
AgTools Dashboard Screen

Home screen with quick actions, system status, and recent activity.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.styles import COLORS, set_widget_class


class QuickActionCard(QFrame):
    """Card component for quick action buttons."""

    clicked = pyqtSignal(str)

    def __init__(self, title: str, description: str, icon: str, action_id: str, parent=None):
        super().__init__(parent)
        self._action_id = action_id
        self._setup_ui(title, description, icon)
        set_widget_class(self, "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_ui(self, title: str, description: str, icon: str) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 32pt; color: {COLORS['primary']};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self.setMinimumSize(180, 150)
        self.setMaximumSize(220, 180)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._action_id)
        super().mousePressEvent(event)


class StatusCard(QFrame):
    """Card showing system status information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        set_widget_class(self, "card")

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("System Status")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setWeight(QFont.Weight.DemiBold)
        header.setFont(header_font)
        layout.addWidget(header)

        # Status items
        self._api_status = self._create_status_row("API Connection", "Checking...", "info")
        self._data_status = self._create_status_row("Data Cache", "Not loaded", "info")
        self._sync_status = self._create_status_row("Last Sync", "Never", "info")

        layout.addWidget(self._api_status)
        layout.addWidget(self._data_status)
        layout.addWidget(self._sync_status)

        layout.addStretch()

    def _create_status_row(self, label: str, value: str, status: str) -> QFrame:
        """Create a status row with label and value."""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 4, 0, 4)

        label_widget = QLabel(label + ":")
        label_widget.setStyleSheet(f"color: {COLORS['text_secondary']};")

        value_widget = QLabel(value)
        value_widget.setObjectName("value")

        # Color based on status
        color = COLORS.get(status, COLORS['text_primary'])
        if status == "online":
            color = COLORS['success']
        elif status == "offline":
            color = COLORS['warning']
        elif status == "error":
            color = COLORS['error']

        value_widget.setStyleSheet(f"color: {color}; font-weight: 600;")

        layout.addWidget(label_widget)
        layout.addStretch()
        layout.addWidget(value_widget)

        return frame

    def set_api_status(self, connected: bool) -> None:
        """Update API connection status."""
        value_label = self._api_status.findChild(QLabel, "value")
        if value_label:
            if connected:
                value_label.setText("Connected")
                value_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: 600;")
            else:
                value_label.setText("Offline Mode")
                value_label.setStyleSheet(f"color: {COLORS['warning']}; font-weight: 600;")

    def set_sync_time(self, time_str: str) -> None:
        """Update last sync time."""
        value_label = self._sync_status.findChild(QLabel, "value")
        if value_label:
            value_label.setText(time_str)


class DashboardScreen(QWidget):
    """
    Main dashboard screen with quick actions and status.

    Signals:
        navigate_to(str): Request navigation to another screen
    """

    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # Header
        header_layout = QVBoxLayout()

        welcome_label = QLabel("Welcome to AgTools")
        set_widget_class(welcome_label, "title")
        header_layout.addWidget(welcome_label)

        subtitle = QLabel("Professional Crop Consulting System")
        set_widget_class(subtitle, "subtitle")
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)

        # Main content in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)

        # Quick Actions Section
        actions_header = QLabel("Quick Actions")
        set_widget_class(actions_header, "header")
        content_layout.addWidget(actions_header)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(16)

        # Quick action cards
        quick_actions = [
            ("Yield Calculator", "Calculate economic\noptimum rates", "\u2191", "yield"),
            ("Spray Timing", "Check current\nspray conditions", "\u23F1", "timing"),
            ("Cost Analysis", "Optimize your\ninput costs", "\u0024", "costs"),
            ("Identify Pest", "AI-powered pest\nidentification", "\u2618", "pests"),
            ("Disease Check", "Identify crop\ndiseases", "\u2695", "diseases"),
            ("Price Manager", "Manage supplier\nquotes", "\u2696", "pricing"),
        ]

        for i, (title, desc, icon, action_id) in enumerate(quick_actions):
            card = QuickActionCard(title, desc, icon, action_id)
            card.clicked.connect(self._on_quick_action)
            actions_grid.addWidget(card, i // 3, i % 3)

        content_layout.addLayout(actions_grid)

        # Status Section
        status_layout = QHBoxLayout()
        status_layout.setSpacing(16)

        # Status card
        self._status_card = StatusCard()
        self._status_card.setMinimumWidth(300)
        self._status_card.setMaximumWidth(400)
        status_layout.addWidget(self._status_card)

        # Info card
        info_card = QFrame()
        set_widget_class(info_card, "card")
        info_layout = QVBoxLayout(info_card)

        info_header = QLabel("Getting Started")
        info_header_font = QFont()
        info_header_font.setPointSize(14)
        info_header_font.setWeight(QFont.Weight.DemiBold)
        info_header.setFont(info_header_font)
        info_layout.addWidget(info_header)

        tips = [
            "Use Yield Calculator to find your most profitable fertilizer rates",
            "Check Spray Timing before any application",
            "Add your supplier prices for accurate cost calculations",
            "Cost Analysis shows your biggest savings opportunities",
        ]

        for tip in tips:
            tip_label = QLabel(f"\u2022 {tip}")
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 4px 0;")
            info_layout.addWidget(tip_label)

        info_layout.addStretch()
        status_layout.addWidget(info_card, 1)

        content_layout.addLayout(status_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

    def _on_quick_action(self, action_id: str) -> None:
        """Handle quick action card click."""
        self.navigate_to.emit(action_id)

    def set_connection_status(self, connected: bool) -> None:
        """Update the connection status display."""
        self._status_card.set_api_status(connected)

    def set_sync_time(self, time_str: str) -> None:
        """Update the last sync time display."""
        self._status_card.set_sync_time(time_str)

    def refresh(self) -> None:
        """Refresh the dashboard data."""
        # Dashboard is mostly static, but this method satisfies the interface
        pass
