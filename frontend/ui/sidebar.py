"""
AgTools Sidebar Navigation

Professional sidebar with grouped navigation items.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from ui.styles import set_widget_class, COLORS


class NavButton(QPushButton):
    """Navigation button for sidebar items."""

    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        display_text = f"  {icon}  {text}" if icon else f"    {text}"
        self.setText(display_text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._nav_id = text.lower().replace(" ", "_")

    @property
    def nav_id(self) -> str:
        return self._nav_id

    def set_active(self, active: bool) -> None:
        """Set the active state of this nav button."""
        self.setChecked(active)
        if active:
            set_widget_class(self, "active")
        else:
            self.setProperty("class", "")
            self.style().unpolish(self)
            self.style().polish(self)


class SectionHeader(QLabel):
    """Section header label for grouping nav items."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        font = QFont()
        font.setPointSize(9)
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
        self.setStyleSheet(f"""
            color: {COLORS['text_disabled']};
            padding: 16px 16px 8px 16px;
            background: transparent;
        """)


class Sidebar(QFrame):
    """
    Main sidebar navigation component.

    Signals:
        navigation_clicked(str): Emitted when a nav item is clicked, with the nav_id
    """

    navigation_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nav_buttons: dict[str, NavButton] = {}
        self._current_nav: str = ""
        self._setup_ui()

        set_widget_class(self, "sidebar")

    def _setup_ui(self) -> None:
        """Initialize the sidebar UI."""
        self.setFixedWidth(200)
        self.setMinimumHeight(400)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo/Title area
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(16, 16, 16, 16)

        title_label = QLabel("AgTools")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['primary_light']};")
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Professional")
        subtitle_label.setStyleSheet(f"color: {COLORS['sidebar_text']}; font-size: 10pt;")
        title_layout.addWidget(subtitle_label)

        layout.addWidget(title_frame)

        # Scroll area for nav items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        # Dashboard
        self._add_nav_item(nav_layout, "Dashboard", icon="\u2302")  # House icon

        # Operations Section (Phase 2.5 & 3)
        nav_layout.addWidget(SectionHeader("Operations"))
        self._add_nav_item(nav_layout, "Fields", icon="\u25A3")  # Field/square
        self._add_nav_item(nav_layout, "Operations", icon="\u2699")  # Gear/log
        self._add_nav_item(nav_layout, "Tasks", icon="\u2611")  # Checkbox

        # Identify Section
        nav_layout.addWidget(SectionHeader("Identify"))
        self._add_nav_item(nav_layout, "Pests", icon="\u2618")  # Bug-like
        self._add_nav_item(nav_layout, "Diseases", icon="\u2695")  # Medical

        # Recommend Section
        nav_layout.addWidget(SectionHeader("Recommend"))
        self._add_nav_item(nav_layout, "Spray", icon="\u2744")  # Spray-like
        self._add_nav_item(nav_layout, "Timing", icon="\u23F1")  # Clock

        # Optimize Section
        nav_layout.addWidget(SectionHeader("Optimize"))
        self._add_nav_item(nav_layout, "Costs", icon="\u0024")  # Dollar
        self._add_nav_item(nav_layout, "Pricing", icon="\u2696")  # Scale
        self._add_nav_item(nav_layout, "Yield", icon="\u2191")  # Up arrow

        # Spacer
        nav_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Settings at bottom
        nav_layout.addWidget(SectionHeader(""))
        self._add_nav_item(nav_layout, "Settings", icon="\u2699")  # Gear

        scroll.setWidget(nav_widget)
        layout.addWidget(scroll, 1)

        # Version info at bottom
        version_label = QLabel("v2.5.0")
        version_label.setStyleSheet(f"""
            color: {COLORS['text_disabled']};
            padding: 8px 16px;
            font-size: 9pt;
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

    def _add_nav_item(self, layout: QVBoxLayout, text: str, icon: str = "") -> None:
        """Add a navigation item to the sidebar."""
        btn = NavButton(text, icon)
        btn.clicked.connect(lambda checked, t=text: self._on_nav_clicked(t))
        layout.addWidget(btn)
        self._nav_buttons[text.lower().replace(" ", "_")] = btn

    def _on_nav_clicked(self, text: str) -> None:
        """Handle navigation item click."""
        nav_id = text.lower().replace(" ", "_")
        self.set_active_nav(nav_id)
        self.navigation_clicked.emit(nav_id)

    def set_active_nav(self, nav_id: str) -> None:
        """
        Set the active navigation item.

        Args:
            nav_id: The navigation ID to activate
        """
        # Deactivate previous
        if self._current_nav and self._current_nav in self._nav_buttons:
            self._nav_buttons[self._current_nav].set_active(False)

        # Activate new
        if nav_id in self._nav_buttons:
            self._nav_buttons[nav_id].set_active(True)
            self._current_nav = nav_id

    def get_nav_ids(self) -> list[str]:
        """Get list of all navigation IDs."""
        return list(self._nav_buttons.keys())
