"""
AgTools Windows 98 Retro Theme - Turquoise Edition

Authentic Windows 95/98 aesthetic with turquoise color scheme.
Features beveled 3D buttons, gradient title bars, and classic UI elements.
"""

# Windows 98 Turquoise Color Palette
RETRO_COLORS = {
    # Primary Turquoise Theme
    "turquoise_dark": "#00868B",      # Dark cyan/turquoise
    "turquoise": "#00CED1",           # Dark turquoise
    "turquoise_medium": "#48D1CC",    # Medium turquoise
    "turquoise_light": "#40E0D0",     # Turquoise
    "turquoise_pale": "#AFEEEE",      # Pale turquoise
    "cyan_light": "#E0FFFF",          # Light cyan

    # Retro warm tones (like old CRT monitors)
    "cream": "#F5F5DC",               # Beige/cream
    "cream_light": "#FFFEF0",         # Light cream
    "cream_dark": "#E8E4D0",          # Darker cream

    # Windows 98 System Colors
    "window_bg": "#C0C0C0",           # Classic Windows silver
    "window_face": "#D4D0C8",         # Windows 98 3D face
    "window_dark": "#808080",         # Dark gray
    "window_darker": "#404040",       # Darker gray
    "window_light": "#FFFFFF",        # White highlight
    "window_frame": "#0A0A0A",        # Near black frame

    # Button bevel colors (3D effect)
    "bevel_light": "#FFFFFF",         # Top/left highlight
    "bevel_medium": "#DFDFDF",        # Secondary highlight
    "bevel_dark": "#808080",          # Bottom/right shadow
    "bevel_darker": "#404040",        # Outer shadow

    # Title bar gradient (Windows 98 active)
    "titlebar_active_start": "#00868B",
    "titlebar_active_end": "#48D1CC",
    "titlebar_inactive_start": "#808080",
    "titlebar_inactive_end": "#C0C0C0",
    "titlebar_text": "#FFFFFF",

    # Desktop/MDI background
    "desktop_bg": "#008080",          # Classic teal desktop
    "mdi_bg": "#3A6EA5",              # MDI client area

    # Panel colors
    "panel_bg": "#D4D0C8",
    "panel_border": "#808080",
    "panel_header_bg": "#00868B",
    "panel_header_text": "#FFFFFF",

    # Text colors
    "text_black": "#000000",
    "text_dark": "#333333",
    "text_normal": "#000000",
    "text_light": "#808080",
    "text_white": "#FFFFFF",
    "text_disabled": "#808080",
    "text_link": "#0000FF",
    "text_link_visited": "#800080",

    # Selection colors
    "selection_bg": "#00868B",
    "selection_text": "#FFFFFF",
    "highlight_bg": "#000080",        # Classic Windows highlight
    "highlight_text": "#FFFFFF",

    # Status colors (Windows 98 style)
    "status_ok": "#008000",
    "status_warning": "#808000",
    "status_error": "#800000",
    "status_info": "#000080",

    # List/Table colors
    "list_bg": "#FFFFFF",
    "list_alt_bg": "#F0FFFF",         # Light cyan alternate
    "list_header_bg": "#D4D0C8",
    "list_header_text": "#000000",
    "list_selected_bg": "#00868B",
    "list_selected_text": "#FFFFFF",
    "list_border": "#808080",

    # Input field colors
    "input_bg": "#FFFFFF",
    "input_border": "#808080",
    "input_border_focus": "#00868B",
    "input_text": "#000000",

    # Scrollbar colors
    "scrollbar_bg": "#D4D0C8",
    "scrollbar_thumb": "#C0C0C0",
    "scrollbar_arrow": "#000000",

    # Menu colors
    "menu_bg": "#D4D0C8",
    "menu_border": "#808080",
    "menu_text": "#000000",
    "menu_disabled": "#808080",
    "menu_highlight_bg": "#00868B",
    "menu_highlight_text": "#FFFFFF",

    # Tooltip colors
    "tooltip_bg": "#FFFFE1",          # Classic tooltip yellow
    "tooltip_border": "#000000",
    "tooltip_text": "#000000",
}


def get_retro_stylesheet():
    """Generate the complete Windows 98 retro stylesheet."""
    c = RETRO_COLORS

    return f"""
    /* ============================================
       AgTools Windows 98 Retro Theme - Turquoise
       ============================================ */

    /* Base Application - Retro Cream Theme */
    QMainWindow, QWidget {{
        background-color: {c['cream']};
        color: {c['text_normal']};
        font-family: "Tahoma", "MS Sans Serif", sans-serif;
        font-size: 11px;
    }}

    /* ============================================
       Windows 98 3D Beveled Buttons
       ============================================ */
    QPushButton {{
        background-color: {c['window_face']};
        color: {c['text_black']};
        border: 2px solid;
        border-top-color: {c['bevel_light']};
        border-left-color: {c['bevel_light']};
        border-bottom-color: {c['bevel_dark']};
        border-right-color: {c['bevel_dark']};
        padding: 4px 16px;
        min-height: 21px;
        font-family: "Tahoma", sans-serif;
    }}

    QPushButton:hover {{
        background-color: {c['cream']};
    }}

    QPushButton:pressed {{
        background-color: {c['window_bg']};
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
    }}

    QPushButton:disabled {{
        color: {c['text_disabled']};
    }}

    /* Primary action buttons (turquoise) */
    QPushButton[class="retro-primary"] {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_light']},
            stop:1 {c['turquoise']});
        color: white;
        font-weight: bold;
        border-top-color: {c['turquoise_light']};
        border-left-color: {c['turquoise_light']};
        border-bottom-color: {c['turquoise_dark']};
        border-right-color: {c['turquoise_dark']};
    }}

    QPushButton[class="retro-primary"]:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_medium']},
            stop:1 {c['turquoise_light']});
    }}

    /* ============================================
       Windows 98 Sunken Input Fields
       ============================================ */
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: white;
        color: {c['text_black']};
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
        padding: 2px 4px;
        selection-background-color: {c['turquoise']};
        selection-color: white;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c['turquoise']};
    }}

    /* ============================================
       Windows 98 ComboBox
       ============================================ */
    QComboBox {{
        background-color: {c['window_face']};
        color: {c['text_black']};
        border: 2px solid;
        border-top-color: {c['bevel_light']};
        border-left-color: {c['bevel_light']};
        border-bottom-color: {c['bevel_dark']};
        border-right-color: {c['bevel_dark']};
        padding: 2px 4px;
        min-height: 21px;
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 18px;
        border-left: 1px solid {c['bevel_dark']};
        background-color: {c['window_face']};
    }}

    QComboBox QAbstractItemView {{
        background-color: white;
        color: {c['text_black']};
        border: 1px solid {c['bevel_dark']};
        selection-background-color: {c['turquoise']};
        selection-color: white;
    }}

    /* ============================================
       Windows 98 Group Box (etched border)
       ============================================ */
    QGroupBox {{
        background-color: {c['cream']};
        border: 2px groove {c['bevel_dark']};
        margin-top: 12px;
        padding-top: 8px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 8px;
        padding: 0 4px;
        background-color: {c['cream']};
        color: {c['text_black']};
    }}

    /* ============================================
       Windows 98 Frame Styles
       ============================================ */
    QFrame[class="retro-raised"] {{
        background-color: {c['window_face']};
        border: 2px solid;
        border-top-color: {c['bevel_light']};
        border-left-color: {c['bevel_light']};
        border-bottom-color: {c['bevel_dark']};
        border-right-color: {c['bevel_dark']};
    }}

    QFrame[class="retro-sunken"] {{
        background-color: {c['cream']};
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
    }}

    QFrame[class="retro-groove"] {{
        background-color: {c['cream']};
        border: 2px groove {c['bevel_dark']};
    }}

    QFrame[class="retro-panel"] {{
        background-color: {c['window_face']};
        border: 1px solid {c['bevel_dark']};
    }}

    /* Header panel with turquoise gradient */
    QFrame[class="retro-header"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['turquoise_dark']},
            stop:1 {c['turquoise']});
        border: none;
        padding: 4px 8px;
    }}

    /* ============================================
       Labels
       ============================================ */
    QLabel {{
        color: {c['text_normal']};
        background: transparent;
    }}

    QLabel[class="retro-header-text"] {{
        color: {c['text_white']};
        font-weight: bold;
        font-size: 14px;
    }}

    QLabel[class="retro-title"] {{
        color: {c['turquoise_dark']};
        font-weight: bold;
        font-size: 16px;
    }}

    /* ============================================
       Table/Tree Views - Clean Style
       ============================================ */
    QTableWidget, QTableView, QTreeWidget, QTreeView, QListWidget, QListView {{
        background-color: white;
        alternate-background-color: {c['cyan_light']};
        color: {c['text_normal']};
        border: 1px solid {c['turquoise']};
        border-radius: 4px;
        gridline-color: {c['turquoise_pale']};
        selection-background-color: {c['turquoise']};
        selection-color: white;
    }}

    QTableWidget::item:selected, QTableView::item:selected,
    QTreeWidget::item:selected, QTreeView::item:selected,
    QListWidget::item:selected, QListView::item:selected {{
        background-color: {c['turquoise']};
        color: white;
    }}

    QHeaderView::section {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_pale']},
            stop:1 {c['turquoise_medium']});
        color: {c['turquoise_dark']};
        padding: 6px 8px;
        border: none;
        border-right: 1px solid {c['turquoise']};
        border-bottom: 1px solid {c['turquoise']};
        font-weight: bold;
    }}

    QHeaderView::section:hover {{
        background: {c['turquoise_light']};
        color: white;
    }}

    /* ============================================
       Tabs - Clean Turquoise Style
       ============================================ */
    QTabWidget::pane {{
        background-color: {c['cyan_light']};
        border: 1px solid {c['turquoise']};
        border-radius: 4px;
        top: -1px;
    }}

    QTabBar::tab {{
        background: {c['turquoise_pale']};
        color: {c['turquoise_dark']};
        border: 1px solid {c['turquoise']};
        border-bottom: none;
        border-radius: 4px 4px 0 0;
        padding: 6px 16px;
        margin-right: 2px;
        font-weight: bold;
    }}

    QTabBar::tab:selected {{
        background: {c['cyan_light']};
        color: {c['turquoise_dark']};
        border-bottom: 1px solid {c['cyan_light']};
    }}

    QTabBar::tab:hover:!selected {{
        background: {c['turquoise_light']};
        color: white;
    }}

    /* ============================================
       Scrollbars - Clean Turquoise
       ============================================ */
    QScrollBar:vertical {{
        background-color: {c['turquoise_pale']};
        width: 12px;
        border: none;
        border-radius: 6px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c['turquoise']};
        border-radius: 5px;
        min-height: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c['turquoise_dark']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: {c['turquoise_pale']};
        height: 12px;
        border: none;
        border-radius: 6px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c['turquoise']};
        border-radius: 5px;
        min-width: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {c['turquoise_dark']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ============================================
       Menu Bar (Windows 98 style)
       ============================================ */
    QMenuBar {{
        background-color: {c['window_face']};
        color: {c['text_normal']};
        border-bottom: 1px solid {c['bevel_dark']};
        padding: 2px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 4px 8px;
    }}

    QMenuBar::item:selected {{
        background-color: {c['selection_bg']};
        color: {c['selection_text']};
    }}

    QMenu {{
        background-color: {c['menu_bg']};
        color: {c['menu_text']};
        border: 2px solid;
        border-top-color: {c['bevel_light']};
        border-left-color: {c['bevel_light']};
        border-bottom-color: {c['bevel_darker']};
        border-right-color: {c['bevel_darker']};
    }}

    QMenu::item {{
        padding: 4px 24px 4px 24px;
    }}

    QMenu::item:selected {{
        background-color: {c['menu_highlight_bg']};
        color: {c['menu_highlight_text']};
    }}

    QMenu::separator {{
        height: 2px;
        background: {c['bevel_dark']};
        margin: 4px 2px;
    }}

    /* ============================================
       Status Bar
       ============================================ */
    QStatusBar {{
        background-color: {c['window_face']};
        border-top: 2px solid;
        border-top-color: {c['bevel_dark']};
    }}

    QStatusBar::item {{
        border: none;
    }}

    QStatusBar QLabel {{
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
        padding: 2px 8px;
        margin: 2px;
    }}

    /* ============================================
       ToolBar
       ============================================ */
    QToolBar {{
        background-color: {c['window_face']};
        border: none;
        border-bottom: 2px groove {c['bevel_dark']};
        spacing: 2px;
        padding: 2px;
    }}

    QToolButton {{
        background-color: {c['window_face']};
        border: 2px solid transparent;
        padding: 4px;
    }}

    QToolButton:hover {{
        border-top-color: {c['bevel_light']};
        border-left-color: {c['bevel_light']};
        border-bottom-color: {c['bevel_darker']};
        border-right-color: {c['bevel_darker']};
    }}

    QToolButton:pressed {{
        border-top-color: {c['bevel_darker']};
        border-left-color: {c['bevel_darker']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
        background-color: {c['window_bg']};
    }}

    /* ============================================
       Progress Bar
       ============================================ */
    QProgressBar {{
        background-color: {c['window_face']};
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
        text-align: center;
    }}

    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_light']},
            stop:1 {c['turquoise_dark']});
    }}

    /* ============================================
       Checkbox and Radio (Windows 98 style)
       ============================================ */
    QCheckBox, QRadioButton {{
        color: {c['text_normal']};
        spacing: 6px;
    }}

    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        background-color: {c['input_bg']};
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c['input_bg']};
        image: none;
    }}

    QRadioButton::indicator {{
        width: 13px;
        height: 13px;
        background-color: {c['input_bg']};
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
        border-radius: 7px;
    }}

    /* ============================================
       Tooltips
       ============================================ */
    QToolTip {{
        background-color: {c['tooltip_bg']};
        color: {c['tooltip_text']};
        border: 1px solid {c['tooltip_border']};
        padding: 2px 4px;
    }}

    /* ============================================
       Splitter
       ============================================ */
    QSplitter::handle {{
        background-color: {c['window_face']};
    }}

    QSplitter::handle:horizontal {{
        width: 4px;
        border-left: 1px solid {c['bevel_light']};
        border-right: 1px solid {c['bevel_dark']};
    }}

    QSplitter::handle:vertical {{
        height: 4px;
        border-top: 1px solid {c['bevel_light']};
        border-bottom: 1px solid {c['bevel_dark']};
    }}

    /* ============================================
       Dialogs
       ============================================ */
    QDialog {{
        background-color: {c['window_face']};
    }}

    QDialogButtonBox QPushButton {{
        min-width: 75px;
    }}

    /* ============================================
       Scroll Area
       ============================================ */
    QScrollArea {{
        background-color: {c['window_face']};
        border: none;
    }}

    /* ============================================
       Date/Time Edit
       ============================================ */
    QDateEdit, QTimeEdit, QDateTimeEdit {{
        background-color: {c['input_bg']};
        color: {c['input_text']};
        border: 2px solid;
        border-top-color: {c['bevel_dark']};
        border-left-color: {c['bevel_dark']};
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
        padding: 2px;
    }}

    QCalendarWidget {{
        background-color: {c['window_face']};
    }}

    QCalendarWidget QToolButton {{
        background-color: {c['window_face']};
        color: {c['text_normal']};
    }}

    QCalendarWidget QMenu {{
        background-color: {c['menu_bg']};
    }}
    """


# Convenience function to apply retro styling to a widget
def apply_retro_style(widget):
    """Apply the Windows 98 retro stylesheet to a widget."""
    widget.setStyleSheet(get_retro_stylesheet())


# Sidebar specific styling for Windows 98 look
def get_retro_sidebar_stylesheet():
    """Get stylesheet specifically for the sidebar."""
    c = RETRO_COLORS

    return f"""
    /* Sidebar Container */
    QFrame#sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_dark']},
            stop:1 {c['turquoise']});
        border-right: 2px solid;
        border-right-color: {c['bevel_darker']};
    }}

    /* Sidebar Buttons */
    QPushButton.sidebar-btn {{
        background: transparent;
        color: {c['text_white']};
        border: none;
        text-align: left;
        padding: 8px 12px;
        font-size: 11px;
    }}

    QPushButton.sidebar-btn:hover {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_medium']},
            stop:1 {c['turquoise_light']});
        border: 2px solid;
        border-top-color: {c['bevel_light']};
        border-left-color: {c['bevel_light']};
        border-bottom-color: rgba(0,0,0,0.3);
        border-right-color: rgba(0,0,0,0.3);
    }}

    QPushButton.sidebar-btn:pressed, QPushButton.sidebar-btn[active="true"] {{
        background: {c['turquoise_dark']};
        border: 2px solid;
        border-top-color: rgba(0,0,0,0.3);
        border-left-color: rgba(0,0,0,0.3);
        border-bottom-color: {c['bevel_light']};
        border-right-color: {c['bevel_light']};
    }}

    /* Section Headers */
    QLabel.sidebar-section {{
        color: {c['cyan_light']};
        font-weight: bold;
        font-size: 9px;
        padding: 12px 12px 4px 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    /* Sidebar Title */
    QLabel.sidebar-title {{
        color: {c['text_white']};
        font-weight: bold;
        font-size: 14px;
        padding: 12px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 {c['turquoise_dark']},
            stop:0.5 {c['turquoise']},
            stop:1 {c['turquoise_dark']});
        border-bottom: 2px groove rgba(255,255,255,0.3);
    }}

    /* Scroll Area in Sidebar */
    QScrollArea {{
        background: transparent;
        border: none;
    }}

    QScrollBar:vertical {{
        background: {c['turquoise_dark']};
        width: 12px;
    }}

    QScrollBar::handle:vertical {{
        background: {c['turquoise_medium']};
        border-radius: 4px;
        margin: 2px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """
