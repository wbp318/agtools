"""
AgTools Sidebar Navigation

Windows 98 Retro Style with Turquoise Theme.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from ui.retro_styles import RETRO_COLORS


class NavButton(QPushButton):
    """Windows 98 style navigation button for sidebar items."""

    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        display_text = f"  {icon}  {text}" if icon else f"    {text}"
        self.setText(display_text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._nav_id = text.lower().replace(" ", "_")
        self._apply_style(False)

    @property
    def nav_id(self) -> str:
        return self._nav_id

    def _apply_style(self, active: bool) -> None:
        """Apply Windows 98 beveled button style."""
        c = RETRO_COLORS
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {c['turquoise_pale']};
                    color: #003030;
                    border: 2px solid;
                    border-top-color: #003030;
                    border-left-color: #003030;
                    border-bottom-color: {c['turquoise_light']};
                    border-right-color: {c['turquoise_light']};
                    text-align: left;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #002020;
                    border: none;
                    text-align: left;
                    padding: 8px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {c['turquoise_pale']};
                    color: #003030;
                    border-left: 3px solid #003030;
                }}
            """)

    def set_active(self, active: bool) -> None:
        """Set the active state of this nav button."""
        self.setChecked(active)
        self._apply_style(active)


class SectionHeader(QLabel):
    """Windows 98 style section header for grouping nav items."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        c = RETRO_COLORS
        font = QFont()
        font.setPointSize(8)
        font.setWeight(QFont.Weight.Bold)
        self.setFont(font)
        self.setStyleSheet(f"""
            color: #001515;
            padding: 14px 12px 4px 12px;
            background: transparent;
            letter-spacing: 1px;
        """)


class Sidebar(QFrame):
    """
    Windows 98 Retro Sidebar Navigation.

    Signals:
        navigation_clicked(str): Emitted when a nav item is clicked, with the nav_id
    """

    navigation_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nav_buttons: dict[str, NavButton] = {}
        self._current_nav: str = ""
        self._setup_ui()
        self._apply_retro_style()

    def _setup_ui(self) -> None:
        """Initialize the sidebar UI."""
        c = RETRO_COLORS
        self.setFixedWidth(220)
        self.setMinimumHeight(400)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo/Title area - Windows 98 style title bar
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {c['turquoise_dark']},
                    stop:1 {c['turquoise_medium']});
                border-bottom: 2px groove rgba(255,255,255,0.3);
            }}
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(12, 12, 12, 12)

        title_label = QLabel("AgTools")
        title_font = QFont("Segoe UI", 16)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {c['text_white']}; background: transparent;")
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Professional v6.5")
        subtitle_label.setStyleSheet(f"color: {c['turquoise_pale']}; font-size: 9pt; background: transparent;")
        title_layout.addWidget(subtitle_label)

        layout.addWidget(title_frame)

        # Scroll area for nav items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {c['turquoise_dark']};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c['turquoise_medium']};
                border-radius: 4px;
                margin: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

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

        # Equipment & Inventory Section (Phase 4)
        nav_layout.addWidget(SectionHeader("Equipment"))
        self._add_nav_item(nav_layout, "Equipment", icon="\u2692")  # Hammer/tools
        self._add_nav_item(nav_layout, "Inventory", icon="\u2630")  # Box/inventory
        self._add_nav_item(nav_layout, "Maintenance", icon="\u2694")  # Wrench

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

        # Analytics Section (Phase 5)
        nav_layout.addWidget(SectionHeader("Analytics"))
        self._add_nav_item(nav_layout, "Reports", icon="\u2637")  # Chart/analytics

        # Import Section (v2.9)
        nav_layout.addWidget(SectionHeader("Import"))
        self._add_nav_item(nav_layout, "QuickBooks", icon="\u21E9")  # Download arrow

        # Accounting Section (GenFin v6.3)
        nav_layout.addWidget(SectionHeader("Accounting"))
        self._add_nav_item(nav_layout, "GenFin", icon="\u0024")  # Dollar sign

        # Farm Operations Section (v6.4.0)
        nav_layout.addWidget(SectionHeader("Farm Ops"))
        self._add_nav_item(nav_layout, "Livestock", icon="\u2618")  # Animal-like
        self._add_nav_item(nav_layout, "Seeds", icon="\u2619")  # Seed/plant

        # Spacer
        nav_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Settings at bottom
        nav_layout.addWidget(SectionHeader(""))
        self._add_nav_item(nav_layout, "Settings", icon="\u2699")  # Gear

        scroll.setWidget(nav_widget)
        layout.addWidget(scroll, 1)

        # Version info at bottom - Windows 98 sunken panel style
        version_label = QLabel("v6.5.2")
        version_label.setStyleSheet(f"""
            color: {c['turquoise_pale']};
            background: {c['turquoise_dark']};
            padding: 6px 16px;
            font-size: 9pt;
            border-top: 1px solid rgba(0,0,0,0.3);
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

    def _apply_retro_style(self) -> None:
        """Apply Windows 98 retro turquoise theme to sidebar."""
        c = RETRO_COLORS
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {c['turquoise_dark']},
                    stop:0.5 {c['turquoise']},
                    stop:1 {c['turquoise_dark']});
                border-right: 3px solid;
                border-right-color: {c['bevel_darker']};
            }}
        """)

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
