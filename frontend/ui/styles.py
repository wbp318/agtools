"""
AgTools Professional Theme

Clean, professional styling for the crop consulting application.
Uses Qt Style Sheets (QSS) for consistent appearance.
"""

# Color Palette - Professional Agriculture Theme
COLORS = {
    # Primary colors
    "primary": "#2E7D32",           # Agriculture green
    "primary_dark": "#1B5E20",
    "primary_light": "#4CAF50",

    # Secondary colors
    "secondary": "#5D4037",         # Earth brown
    "secondary_dark": "#3E2723",
    "secondary_light": "#8D6E63",

    # Background & Surface
    "background": "#FAFAFA",
    "surface": "#FFFFFF",
    "surface_variant": "#F5F5F5",

    # Text
    "text_primary": "#212121",
    "text_secondary": "#757575",
    "text_disabled": "#BDBDBD",
    "text_on_primary": "#FFFFFF",

    # Status colors
    "error": "#D32F2F",
    "error_light": "#FFCDD2",
    "warning": "#F57C00",
    "warning_light": "#FFE0B2",
    "success": "#388E3C",
    "success_light": "#C8E6C9",
    "info": "#1976D2",
    "info_light": "#BBDEFB",

    # Borders & Dividers
    "border": "#E0E0E0",
    "divider": "#EEEEEE",

    # Sidebar specific
    "sidebar_bg": "#263238",
    "sidebar_text": "#ECEFF1",
    "sidebar_hover": "#37474F",
    "sidebar_active": "#2E7D32",

    # Status indicators
    "online": "#4CAF50",
    "offline": "#FF9800",
    "error_status": "#F44336",
}


def get_stylesheet(theme: str = "light") -> str:
    """
    Generate the complete application stylesheet.

    Args:
        theme: "light" or "dark" (dark not yet implemented)

    Returns:
        Complete QSS stylesheet string
    """
    c = COLORS

    return f"""
    /* ========================================
       GLOBAL STYLES
       ======================================== */

    QMainWindow {{
        background-color: {c["background"]};
    }}

    QWidget {{
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 11pt;
        color: {c["text_primary"]};
    }}

    /* ========================================
       LABELS & TEXT
       ======================================== */

    QLabel {{
        color: {c["text_primary"]};
        background: transparent;
    }}

    QLabel[class="header"] {{
        font-size: 16pt;
        font-weight: 600;
        color: {c["text_primary"]};
        padding: 8px 0;
    }}

    QLabel[class="title"] {{
        font-size: 24pt;
        font-weight: 600;
        color: {c["primary_dark"]};
        padding: 16px 0;
    }}

    QLabel[class="subtitle"] {{
        font-size: 13pt;
        color: {c["text_secondary"]};
        padding: 4px 0;
    }}

    QLabel[class="caption"] {{
        font-size: 10pt;
        color: {c["text_secondary"]};
    }}

    /* ========================================
       BUTTONS
       ======================================== */

    QPushButton {{
        background-color: {c["primary"]};
        color: {c["text_on_primary"]};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        min-height: 36px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {c["primary_dark"]};
    }}

    QPushButton:pressed {{
        background-color: {c["primary_dark"]};
    }}

    QPushButton:disabled {{
        background-color: {c["text_disabled"]};
        color: {c["surface"]};
    }}

    QPushButton[class="secondary"] {{
        background-color: {c["surface"]};
        color: {c["primary"]};
        border: 2px solid {c["primary"]};
    }}

    QPushButton[class="secondary"]:hover {{
        background-color: {c["primary"]};
        color: {c["text_on_primary"]};
    }}

    QPushButton[class="flat"] {{
        background-color: transparent;
        color: {c["primary"]};
        border: none;
    }}

    QPushButton[class="flat"]:hover {{
        background-color: {c["surface_variant"]};
    }}

    QPushButton[class="danger"] {{
        background-color: {c["error"]};
    }}

    QPushButton[class="danger"]:hover {{
        background-color: #B71C1C;
    }}

    /* ========================================
       INPUT FIELDS
       ======================================== */

    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
        selection-background-color: {c["primary_light"]};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {c["primary"]};
        padding: 7px 11px;
    }}

    QLineEdit:disabled {{
        background-color: {c["surface_variant"]};
        color: {c["text_disabled"]};
    }}

    /* ========================================
       COMBO BOXES / DROPDOWNS
       ======================================== */

    QComboBox {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
        min-width: 120px;
    }}

    QComboBox:hover {{
        border-color: {c["primary"]};
    }}

    QComboBox:focus {{
        border: 2px solid {c["primary"]};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {c["text_secondary"]};
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["primary_light"]};
        selection-color: {c["text_on_primary"]};
        padding: 4px;
    }}

    /* ========================================
       SPIN BOXES
       ======================================== */

    QSpinBox, QDoubleSpinBox {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        padding: 8px 12px;
        min-height: 32px;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c["primary"]};
    }}

    /* ========================================
       SCROLL AREAS
       ======================================== */

    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QScrollBar:vertical {{
        background-color: {c["surface_variant"]};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c["text_disabled"]};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c["text_secondary"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background-color: {c["surface_variant"]};
        height: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c["text_disabled"]};
        border-radius: 5px;
        min-width: 30px;
    }}

    /* ========================================
       TABLES
       ======================================== */

    QTableWidget, QTableView {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 4px;
        gridline-color: {c["divider"]};
        selection-background-color: {c["primary_light"]};
    }}

    QHeaderView::section {{
        background-color: {c["surface_variant"]};
        color: {c["text_primary"]};
        padding: 8px 12px;
        border: none;
        border-bottom: 2px solid {c["border"]};
        font-weight: 600;
    }}

    QTableWidget::item, QTableView::item {{
        padding: 8px 12px;
    }}

    QTableWidget::item:selected {{
        background-color: {c["primary_light"]};
        color: {c["text_on_primary"]};
    }}

    /* ========================================
       TAB WIDGET
       ======================================== */

    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        border-radius: 4px;
        background-color: {c["surface"]};
        margin-top: -1px;
    }}

    QTabBar::tab {{
        background-color: {c["surface_variant"]};
        color: {c["text_secondary"]};
        padding: 10px 20px;
        border: 1px solid {c["border"]};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {c["surface"]};
        color: {c["primary"]};
        font-weight: 600;
        border-bottom: 2px solid {c["primary"]};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {c["surface"]};
        color: {c["text_primary"]};
    }}

    /* ========================================
       GROUP BOX / CARDS
       ======================================== */

    QGroupBox {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        margin-top: 16px;
        padding: 16px;
        padding-top: 24px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {c["text_primary"]};
        font-weight: 600;
        font-size: 12pt;
    }}

    /* ========================================
       FRAME / CARD COMPONENT
       ======================================== */

    QFrame[class="card"] {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 16px;
    }}

    QFrame[class="card-elevated"] {{
        background-color: {c["surface"]};
        border: none;
        border-radius: 8px;
        padding: 16px;
    }}

    /* ========================================
       SIDEBAR STYLES
       ======================================== */

    QFrame[class="sidebar"] {{
        background-color: {c["sidebar_bg"]};
        border: none;
    }}

    QFrame[class="sidebar"] QLabel {{
        color: {c["sidebar_text"]};
    }}

    QFrame[class="sidebar"] QPushButton {{
        background-color: transparent;
        color: {c["sidebar_text"]};
        text-align: left;
        padding: 12px 16px;
        border-radius: 0;
        border: none;
        font-weight: normal;
    }}

    QFrame[class="sidebar"] QPushButton:hover {{
        background-color: {c["sidebar_hover"]};
    }}

    QFrame[class="sidebar"] QPushButton[class="active"] {{
        background-color: {c["sidebar_active"]};
        border-left: 3px solid {c["primary_light"]};
    }}

    QFrame[class="sidebar"] QPushButton[class="section-header"] {{
        color: {c["text_disabled"]};
        font-size: 9pt;
        font-weight: 600;
        text-transform: uppercase;
        padding: 16px 16px 8px 16px;
    }}

    QFrame[class="sidebar"] QPushButton[class="section-header"]:hover {{
        background-color: transparent;
    }}

    /* ========================================
       STATUS BAR
       ======================================== */

    QStatusBar {{
        background-color: {c["surface_variant"]};
        border-top: 1px solid {c["border"]};
        padding: 4px 8px;
    }}

    QStatusBar QLabel {{
        padding: 0 8px;
    }}

    /* ========================================
       STATUS INDICATORS
       ======================================== */

    QLabel[class="status-online"] {{
        color: {c["online"]};
        font-weight: 600;
    }}

    QLabel[class="status-offline"] {{
        color: {c["offline"]};
        font-weight: 600;
    }}

    QLabel[class="status-error"] {{
        color: {c["error_status"]};
        font-weight: 600;
    }}

    /* ========================================
       ALERT / MESSAGE BOXES
       ======================================== */

    QFrame[class="alert-success"] {{
        background-color: {c["success_light"]};
        border: 1px solid {c["success"]};
        border-radius: 4px;
        padding: 12px;
    }}

    QFrame[class="alert-warning"] {{
        background-color: {c["warning_light"]};
        border: 1px solid {c["warning"]};
        border-radius: 4px;
        padding: 12px;
    }}

    QFrame[class="alert-error"] {{
        background-color: {c["error_light"]};
        border: 1px solid {c["error"]};
        border-radius: 4px;
        padding: 12px;
    }}

    QFrame[class="alert-info"] {{
        background-color: {c["info_light"]};
        border: 1px solid {c["info"]};
        border-radius: 4px;
        padding: 12px;
    }}

    /* ========================================
       PROGRESS BAR
       ======================================== */

    QProgressBar {{
        background-color: {c["surface_variant"]};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {c["primary"]};
        border-radius: 4px;
    }}

    /* ========================================
       TOOLTIPS
       ======================================== */

    QToolTip {{
        background-color: {c["sidebar_bg"]};
        color: {c["sidebar_text"]};
        border: none;
        padding: 8px 12px;
        border-radius: 4px;
    }}

    /* ========================================
       SPLITTER
       ======================================== */

    QSplitter::handle {{
        background-color: {c["border"]};
    }}

    QSplitter::handle:horizontal {{
        width: 2px;
    }}

    QSplitter::handle:vertical {{
        height: 2px;
    }}

    QSplitter::handle:hover {{
        background-color: {c["primary"]};
    }}
    """


# Convenience function for setting class properties
def set_widget_class(widget, class_name: str) -> None:
    """
    Set a CSS class on a widget for styling.

    Args:
        widget: The QWidget to style
        class_name: The class name to apply
    """
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
