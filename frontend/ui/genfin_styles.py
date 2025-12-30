"""
GenFin 90s QuickBooks Style Theme

Authentic 90s QuickBooks aesthetic with teal blue color scheme.
Features beveled 3D buttons, gradient title bars, and chunky icons.
"""

# 90s QuickBooks Teal Color Palette
GENFIN_COLORS = {
    # Primary Teal Theme
    "teal_dark": "#004D4D",
    "teal": "#008080",
    "teal_light": "#20B2AA",
    "teal_bright": "#40E0D0",

    # 90s Window Colors
    "window_bg": "#C0C0C0",          # Classic Windows gray
    "window_dark": "#808080",
    "window_light": "#FFFFFF",
    "window_face": "#D4D0C8",        # Windows 98 face color

    # Button bevel colors (3D effect)
    "bevel_light": "#FFFFFF",
    "bevel_dark": "#404040",
    "bevel_shadow": "#808080",

    # Title bar gradient
    "titlebar_start": "#006666",
    "titlebar_end": "#00CCCC",
    "titlebar_text": "#FFFFFF",

    # Panel colors
    "panel_bg": "#E8E8E8",
    "panel_border": "#808080",
    "panel_header": "#004D4D",

    # Text colors
    "text_dark": "#000000",
    "text_normal": "#333333",
    "text_light": "#666666",
    "text_white": "#FFFFFF",
    "text_link": "#0066CC",

    # Status colors (90s style - more muted)
    "status_green": "#008000",
    "status_red": "#CC0000",
    "status_yellow": "#CC9900",
    "status_blue": "#000099",

    # Icon button colors
    "icon_bg": "#D4D0C8",
    "icon_hover": "#E8E8E8",
    "icon_active": "#B8B4A8",
    "icon_border": "#808080",

    # Table/list colors
    "table_header": "#006666",
    "table_row_alt": "#F0F8F8",
    "table_row": "#FFFFFF",
    "table_selected": "#008080",
    "table_border": "#808080",
}


def get_genfin_stylesheet() -> str:
    """
    Generate the complete GenFin 90s QuickBooks stylesheet.

    Returns:
        Complete QSS stylesheet string with 90s QuickBooks aesthetic
    """
    c = GENFIN_COLORS

    return f"""
    /* ========================================
       GENFIN 90s QUICKBOOKS THEME
       ======================================== */

    /* Main window background */
    QWidget[class="genfin-main"] {{
        background-color: {c["window_bg"]};
        font-family: "MS Sans Serif", "Tahoma", "Arial", sans-serif;
        font-size: 11px;
    }}

    /* ========================================
       TITLE BAR / HEADER
       ======================================== */

    QFrame[class="genfin-titlebar"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c["titlebar_start"]},
            stop:1 {c["titlebar_end"]});
        border: 2px outset {c["teal"]};
        padding: 4px 8px;
        min-height: 28px;
    }}

    QLabel[class="genfin-title"] {{
        color: {c["titlebar_text"]};
        font-family: "Arial Black", "Arial", sans-serif;
        font-size: 16px;
        font-weight: bold;
        background: transparent;
        text-shadow: 1px 1px 2px {c["teal_dark"]};
    }}

    QLabel[class="genfin-subtitle"] {{
        color: {c["teal_bright"]};
        font-size: 10px;
        background: transparent;
    }}

    /* ========================================
       3D BEVELED BUTTONS (90s Style)
       ======================================== */

    QPushButton[class="genfin-button"] {{
        background-color: {c["window_face"]};
        color: {c["text_dark"]};
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-bottom: 2px solid {c["bevel_dark"]};
        border-right: 2px solid {c["bevel_dark"]};
        padding: 4px 12px;
        min-height: 24px;
        font-family: "MS Sans Serif", "Tahoma", sans-serif;
        font-size: 11px;
        font-weight: bold;
    }}

    QPushButton[class="genfin-button"]:hover {{
        background-color: {c["icon_hover"]};
    }}

    QPushButton[class="genfin-button"]:pressed {{
        background-color: {c["icon_active"]};
        border-top: 2px solid {c["bevel_dark"]};
        border-left: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_light"]};
        padding-left: 14px;
        padding-top: 6px;
    }}

    QPushButton[class="genfin-button"]:disabled {{
        background-color: {c["window_bg"]};
        color: {c["bevel_shadow"]};
    }}

    /* Teal primary button */
    QPushButton[class="genfin-button-primary"] {{
        background-color: {c["teal"]};
        color: {c["text_white"]};
        border-top: 2px solid {c["teal_light"]};
        border-left: 2px solid {c["teal_light"]};
        border-bottom: 2px solid {c["teal_dark"]};
        border-right: 2px solid {c["teal_dark"]};
        padding: 4px 16px;
        min-height: 24px;
        font-weight: bold;
    }}

    QPushButton[class="genfin-button-primary"]:hover {{
        background-color: {c["teal_light"]};
    }}

    QPushButton[class="genfin-button-primary"]:pressed {{
        background-color: {c["teal_dark"]};
        border-top: 2px solid {c["teal_dark"]};
        border-left: 2px solid {c["teal_dark"]};
        border-bottom: 2px solid {c["teal_light"]};
        border-right: 2px solid {c["teal_light"]};
    }}

    /* ========================================
       ICON BUTTONS (QuickBooks Home Grid)
       ======================================== */

    QPushButton[class="genfin-icon-button"] {{
        background-color: {c["icon_bg"]};
        color: {c["text_dark"]};
        border: 2px outset {c["bevel_shadow"]};
        padding: 8px;
        min-width: 100px;
        min-height: 80px;
        font-family: "MS Sans Serif", "Tahoma", sans-serif;
        font-size: 10px;
        font-weight: bold;
        text-align: center;
    }}

    QPushButton[class="genfin-icon-button"]:hover {{
        background-color: {c["icon_hover"]};
        border: 2px outset {c["teal"]};
    }}

    QPushButton[class="genfin-icon-button"]:pressed {{
        background-color: {c["icon_active"]};
        border: 2px inset {c["bevel_shadow"]};
        padding-left: 10px;
        padding-top: 10px;
    }}

    /* ========================================
       PANELS & GROUPBOXES (Sunken 3D)
       ======================================== */

    QFrame[class="genfin-panel"] {{
        background-color: {c["panel_bg"]};
        border-top: 2px solid {c["bevel_dark"]};
        border-left: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_light"]};
        padding: 8px;
    }}

    QFrame[class="genfin-panel-raised"] {{
        background-color: {c["window_face"]};
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-bottom: 2px solid {c["bevel_dark"]};
        border-right: 2px solid {c["bevel_dark"]};
        padding: 8px;
    }}

    QGroupBox[class="genfin-group"] {{
        background-color: {c["panel_bg"]};
        border: 2px groove {c["bevel_shadow"]};
        border-radius: 0px;
        margin-top: 12px;
        padding: 12px;
        padding-top: 20px;
        font-weight: bold;
    }}

    QGroupBox[class="genfin-group"]::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 6px;
        background-color: {c["panel_bg"]};
        color: {c["teal_dark"]};
        font-weight: bold;
    }}

    /* ========================================
       TOOLBAR (90s Icon Bar)
       ======================================== */

    QFrame[class="genfin-toolbar"] {{
        background-color: {c["window_face"]};
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-bottom: 2px solid {c["bevel_dark"]};
        border-right: 2px solid {c["bevel_dark"]};
        padding: 4px;
        spacing: 2px;
    }}

    QPushButton[class="genfin-toolbar-button"] {{
        background-color: {c["window_face"]};
        color: {c["text_dark"]};
        border: 1px solid transparent;
        padding: 4px 8px;
        min-width: 60px;
        min-height: 32px;
        font-size: 9px;
        font-weight: bold;
    }}

    QPushButton[class="genfin-toolbar-button"]:hover {{
        border-top: 1px solid {c["bevel_light"]};
        border-left: 1px solid {c["bevel_light"]};
        border-bottom: 1px solid {c["bevel_dark"]};
        border-right: 1px solid {c["bevel_dark"]};
    }}

    QPushButton[class="genfin-toolbar-button"]:pressed {{
        border-top: 1px solid {c["bevel_dark"]};
        border-left: 1px solid {c["bevel_dark"]};
        border-bottom: 1px solid {c["bevel_light"]};
        border-right: 1px solid {c["bevel_light"]};
        background-color: {c["icon_active"]};
    }}

    /* ========================================
       INPUT FIELDS (Sunken 3D)
       ======================================== */

    QLineEdit[class="genfin-input"], QTextEdit[class="genfin-input"] {{
        background-color: {c["text_white"]};
        color: {c["text_dark"]};
        border-top: 2px solid {c["bevel_dark"]};
        border-left: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_light"]};
        padding: 4px 6px;
        font-family: "MS Sans Serif", "Tahoma", sans-serif;
        font-size: 11px;
        selection-background-color: {c["teal"]};
        selection-color: {c["text_white"]};
    }}

    QLineEdit[class="genfin-input"]:focus {{
        border-top: 2px solid {c["teal_dark"]};
        border-left: 2px solid {c["teal_dark"]};
        border-bottom: 2px solid {c["teal_light"]};
        border-right: 2px solid {c["teal_light"]};
    }}

    QLineEdit[class="genfin-input"]:disabled {{
        background-color: {c["window_bg"]};
        color: {c["bevel_shadow"]};
    }}

    /* ========================================
       COMBOBOX (90s Dropdown)
       ======================================== */

    QComboBox[class="genfin-combo"] {{
        background-color: {c["text_white"]};
        color: {c["text_dark"]};
        border-top: 2px solid {c["bevel_dark"]};
        border-left: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_light"]};
        padding: 4px 6px;
        min-height: 20px;
        font-size: 11px;
    }}

    QComboBox[class="genfin-combo"]::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid {c["bevel_shadow"]};
        background-color: {c["window_face"]};
        border-top: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_dark"]};
    }}

    QComboBox[class="genfin-combo"]::down-arrow {{
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {c["text_dark"]};
    }}

    QComboBox[class="genfin-combo"] QAbstractItemView {{
        background-color: {c["text_white"]};
        border: 1px solid {c["bevel_dark"]};
        selection-background-color: {c["teal"]};
        selection-color: {c["text_white"]};
    }}

    /* ========================================
       TABLE (90s Grid with Headers)
       ======================================== */

    QTableWidget[class="genfin-table"], QTableView[class="genfin-table"] {{
        background-color: {c["table_row"]};
        alternate-background-color: {c["table_row_alt"]};
        border: 2px inset {c["bevel_shadow"]};
        gridline-color: {c["table_border"]};
        selection-background-color: {c["table_selected"]};
        selection-color: {c["text_white"]};
        font-size: 11px;
    }}

    QHeaderView[class="genfin-header"]::section {{
        background-color: {c["table_header"]};
        color: {c["text_white"]};
        padding: 4px 8px;
        border: 1px outset {c["teal_light"]};
        font-weight: bold;
        font-size: 11px;
    }}

    QHeaderView[class="genfin-header"]::section:hover {{
        background-color: {c["teal_light"]};
    }}

    QHeaderView[class="genfin-header"]::section:pressed {{
        background-color: {c["teal_dark"]};
        border: 1px inset {c["teal_light"]};
    }}

    /* ========================================
       TAB WIDGET (90s Notebook Tabs)
       ======================================== */

    QTabWidget[class="genfin-tabs"]::pane {{
        background-color: {c["panel_bg"]};
        border: 2px groove {c["bevel_shadow"]};
        border-radius: 0px;
        margin-top: -2px;
    }}

    QTabBar[class="genfin-tabbar"]::tab {{
        background-color: {c["window_face"]};
        color: {c["text_dark"]};
        padding: 6px 16px;
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_dark"]};
        border-bottom: none;
        margin-right: 2px;
        font-weight: bold;
    }}

    QTabBar[class="genfin-tabbar"]::tab:selected {{
        background-color: {c["panel_bg"]};
        border-bottom: 2px solid {c["panel_bg"]};
        margin-bottom: -2px;
    }}

    QTabBar[class="genfin-tabbar"]::tab:!selected {{
        margin-top: 3px;
        background-color: {c["window_bg"]};
    }}

    QTabBar[class="genfin-tabbar"]::tab:hover:!selected {{
        background-color: {c["icon_hover"]};
    }}

    /* ========================================
       SCROLLBARS (90s Style)
       ======================================== */

    QScrollBar:vertical {{
        background-color: {c["window_bg"]};
        width: 16px;
        margin: 16px 0 16px 0;
        border: 1px solid {c["bevel_shadow"]};
    }}

    QScrollBar::handle:vertical {{
        background-color: {c["window_face"]};
        min-height: 20px;
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-bottom: 2px solid {c["bevel_dark"]};
        border-right: 2px solid {c["bevel_dark"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background-color: {c["window_face"]};
        height: 16px;
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-bottom: 2px solid {c["bevel_dark"]};
        border-right: 2px solid {c["bevel_dark"]};
    }}

    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background-color: {c["window_bg"]};
    }}

    QScrollBar:horizontal {{
        background-color: {c["window_bg"]};
        height: 16px;
        margin: 0 16px 0 16px;
        border: 1px solid {c["bevel_shadow"]};
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c["window_face"]};
        min-width: 20px;
        border-top: 2px solid {c["bevel_light"]};
        border-left: 2px solid {c["bevel_light"]};
        border-bottom: 2px solid {c["bevel_dark"]};
        border-right: 2px solid {c["bevel_dark"]};
    }}

    /* ========================================
       STATUS BAR (90s InfoBar)
       ======================================== */

    QFrame[class="genfin-statusbar"] {{
        background-color: {c["window_face"]};
        border-top: 2px solid {c["bevel_dark"]};
        padding: 2px 8px;
        min-height: 20px;
    }}

    QLabel[class="genfin-status-text"] {{
        color: {c["text_dark"]};
        font-size: 10px;
        background: transparent;
    }}

    QFrame[class="genfin-status-panel"] {{
        background-color: {c["panel_bg"]};
        border-top: 1px solid {c["bevel_dark"]};
        border-left: 1px solid {c["bevel_dark"]};
        border-bottom: 1px solid {c["bevel_light"]};
        border-right: 1px solid {c["bevel_light"]};
        padding: 2px 6px;
    }}

    /* ========================================
       MENU BAR (90s Style)
       ======================================== */

    QMenuBar[class="genfin-menubar"] {{
        background-color: {c["window_face"]};
        color: {c["text_dark"]};
        border-bottom: 1px solid {c["bevel_shadow"]};
        padding: 2px;
        font-size: 11px;
    }}

    QMenuBar[class="genfin-menubar"]::item {{
        padding: 4px 8px;
        background: transparent;
    }}

    QMenuBar[class="genfin-menubar"]::item:selected {{
        background-color: {c["teal"]};
        color: {c["text_white"]};
    }}

    QMenu[class="genfin-menu"] {{
        background-color: {c["window_face"]};
        border: 2px outset {c["bevel_shadow"]};
        padding: 2px;
    }}

    QMenu[class="genfin-menu"]::item {{
        padding: 4px 24px 4px 8px;
    }}

    QMenu[class="genfin-menu"]::item:selected {{
        background-color: {c["teal"]};
        color: {c["text_white"]};
    }}

    QMenu[class="genfin-menu"]::separator {{
        height: 1px;
        background-color: {c["bevel_shadow"]};
        margin: 4px 2px;
    }}

    /* ========================================
       LABELS & TEXT
       ======================================== */

    QLabel[class="genfin-header-text"] {{
        color: {c["teal_dark"]};
        font-family: "Arial", sans-serif;
        font-size: 14px;
        font-weight: bold;
        background: transparent;
    }}

    QLabel[class="genfin-section-text"] {{
        color: {c["text_dark"]};
        font-size: 11px;
        font-weight: bold;
        background: transparent;
        padding: 4px 0;
    }}

    QLabel[class="genfin-label"] {{
        color: {c["text_dark"]};
        font-size: 11px;
        background: transparent;
    }}

    QLabel[class="genfin-money-positive"] {{
        color: {c["status_green"]};
        font-family: "Courier New", monospace;
        font-size: 12px;
        font-weight: bold;
    }}

    QLabel[class="genfin-money-negative"] {{
        color: {c["status_red"]};
        font-family: "Courier New", monospace;
        font-size: 12px;
        font-weight: bold;
    }}

    /* ========================================
       NAVIGATION SIDEBAR (QuickBooks Style)
       ======================================== */

    QFrame[class="genfin-nav-sidebar"] {{
        background-color: {c["teal_dark"]};
        border-right: 2px solid {c["teal"]};
    }}

    QPushButton[class="genfin-nav-button"] {{
        background-color: transparent;
        color: {c["teal_bright"]};
        border: none;
        padding: 10px 12px;
        text-align: left;
        font-size: 11px;
        font-weight: bold;
    }}

    QPushButton[class="genfin-nav-button"]:hover {{
        background-color: {c["teal"]};
        color: {c["text_white"]};
    }}

    QPushButton[class="genfin-nav-button"][class~="active"] {{
        background-color: {c["teal"]};
        color: {c["text_white"]};
        border-left: 3px solid {c["teal_bright"]};
    }}

    QLabel[class="genfin-nav-header"] {{
        color: {c["teal_light"]};
        font-size: 9px;
        font-weight: bold;
        padding: 12px 12px 4px 12px;
        text-transform: uppercase;
        background: transparent;
    }}

    /* ========================================
       MISC WIDGETS
       ======================================== */

    QCheckBox[class="genfin-checkbox"] {{
        color: {c["text_dark"]};
        font-size: 11px;
        spacing: 6px;
    }}

    QCheckBox[class="genfin-checkbox"]::indicator {{
        width: 13px;
        height: 13px;
        border-top: 2px solid {c["bevel_dark"]};
        border-left: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_light"]};
        background-color: {c["text_white"]};
    }}

    QCheckBox[class="genfin-checkbox"]::indicator:checked {{
        background-color: {c["teal"]};
    }}

    QRadioButton[class="genfin-radio"] {{
        color: {c["text_dark"]};
        font-size: 11px;
        spacing: 6px;
    }}

    QProgressBar[class="genfin-progress"] {{
        background-color: {c["panel_bg"]};
        border-top: 2px solid {c["bevel_dark"]};
        border-left: 2px solid {c["bevel_dark"]};
        border-bottom: 2px solid {c["bevel_light"]};
        border-right: 2px solid {c["bevel_light"]};
        height: 16px;
        text-align: center;
        font-size: 10px;
    }}

    QProgressBar[class="genfin-progress"]::chunk {{
        background-color: {c["teal"]};
    }}

    /* ========================================
       DIVIDERS & SEPARATORS
       ======================================== */

    QFrame[class="genfin-divider-h"] {{
        background-color: {c["bevel_shadow"]};
        min-height: 2px;
        max-height: 2px;
    }}

    QFrame[class="genfin-divider-v"] {{
        background-color: {c["bevel_shadow"]};
        min-width: 2px;
        max-width: 2px;
    }}

    /* ========================================
       TOOLTIP (90s Style)
       ======================================== */

    QToolTip {{
        background-color: #FFFFE1;
        color: {c["text_dark"]};
        border: 1px solid {c["text_dark"]};
        padding: 4px;
        font-size: 11px;
    }}
    """


def set_genfin_class(widget, class_name: str) -> None:
    """
    Set a CSS class on a widget for GenFin styling.

    Args:
        widget: The QWidget to style
        class_name: The class name to apply
    """
    widget.setProperty("class", class_name)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
