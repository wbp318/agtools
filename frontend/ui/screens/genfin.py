"""
GenFin Accounting - 90s QuickBooks Style Interface

A nostalgic 90s QuickBooks-inspired accounting interface with
teal blue theme, beveled 3D buttons, and chunky icon grid.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QGroupBox, QTabWidget,
    QSizePolicy, QMessageBox, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont

from ui.genfin_styles import GENFIN_COLORS, get_genfin_stylesheet, set_genfin_class


class GenFinIconButton(QPushButton):
    """90s QuickBooks-style icon button for the home grid."""

    def __init__(self, title: str, icon: str, description: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_text = icon
        self.description = description
        self._setup_ui()

    def _setup_ui(self):
        # Use multiline text with icon on top
        display_text = f"{self.icon_text}\n{self.title}"
        if self.description:
            display_text += f"\n{self.description}"
        self.setText(display_text)
        self.setProperty("class", "genfin-icon-button")
        self.setFixedSize(120, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class GenFinToolbarButton(QPushButton):
    """90s QuickBooks-style toolbar button."""

    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        display = f"{icon}\n{text}" if icon else text
        self.setText(display)
        self.setProperty("class", "genfin-toolbar-button")


class GenFinTitleBar(QFrame):
    """90s gradient title bar with window controls feel."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-titlebar")
        self._setup_ui(title, subtitle)

    def _setup_ui(self, title: str, subtitle: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Logo icon (stylized)
        logo = QLabel("$")
        logo.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_bright']};
            font-size: 24px;
            font-weight: bold;
            font-family: "Arial Black", sans-serif;
            padding: 0 8px;
        """)
        layout.addWidget(logo)

        # Title and subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setProperty("class", "genfin-title")
        title_layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setProperty("class", "genfin-subtitle")
            title_layout.addWidget(subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        # Version badge
        version = QLabel("v6.3.0")
        version.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_bright']};
            font-size: 10px;
            padding: 2px 8px;
            background: {GENFIN_COLORS['teal_dark']};
            border: 1px solid {GENFIN_COLORS['teal_light']};
        """)
        layout.addWidget(version)


class GenFinToolbar(QFrame):
    """90s QuickBooks-style toolbar with icon buttons."""

    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    print_clicked = pyqtSignal()
    help_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-toolbar")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        buttons = [
            ("New", "+", self.new_clicked),
            ("Edit", "E", self.edit_clicked),
            ("Delete", "X", self.delete_clicked),
            (None, None, None),  # Separator
            ("Print", "P", self.print_clicked),
            ("Help", "?", self.help_clicked),
        ]

        for item in buttons:
            if item[0] is None:
                # Separator
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color: {GENFIN_COLORS['bevel_shadow']};")
                layout.addWidget(sep)
            else:
                btn = GenFinToolbarButton(item[0], item[1])
                btn.clicked.connect(item[2].emit)
                layout.addWidget(btn)

        layout.addStretch()


class GenFinNavSidebar(QFrame):
    """90s QuickBooks-style navigation sidebar."""

    navigation_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-nav-sidebar")
        self.setFixedWidth(140)
        self._buttons = {}
        self._current = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setStyleSheet(f"background: {GENFIN_COLORS['teal_dark']}; padding: 8px;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(8, 12, 8, 12)

        logo = QLabel("GenFin")
        logo.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_bright']};
            font-size: 18px;
            font-weight: bold;
            font-family: "Arial Black", sans-serif;
        """)
        logo_layout.addWidget(logo)

        tagline = QLabel("Accounting")
        tagline.setStyleSheet(f"color: {GENFIN_COLORS['teal_light']}; font-size: 9px;")
        logo_layout.addWidget(tagline)

        layout.addWidget(logo_frame)

        # Navigation sections
        nav_items = [
            ("HOME", [
                ("home", "Home"),
            ]),
            ("MONEY IN", [
                ("customers", "Customers"),
                ("invoices", "Invoices"),
                ("receive", "Receive $"),
            ]),
            ("MONEY OUT", [
                ("vendors", "Vendors"),
                ("bills", "Bills"),
                ("pay", "Pay Bills"),
            ]),
            ("BANKING", [
                ("accounts", "Chart of Acct"),
                ("banking", "Banking"),
                ("journal", "Journal"),
            ]),
            ("PAYROLL", [
                ("payroll", "Payroll"),
                ("employees", "Employees"),
            ]),
            ("REPORTS", [
                ("reports", "Reports"),
                ("1099", "1099 Forms"),
            ]),
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        for section_name, items in nav_items:
            # Section header
            header = QLabel(section_name)
            header.setProperty("class", "genfin-nav-header")
            nav_layout.addWidget(header)

            for nav_id, text in items:
                btn = QPushButton(f"  {text}")
                btn.setProperty("class", "genfin-nav-button")
                btn.clicked.connect(lambda checked, nid=nav_id: self._on_nav_click(nid))
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                nav_layout.addWidget(btn)
                self._buttons[nav_id] = btn

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        layout.addWidget(scroll, 1)

    def _on_nav_click(self, nav_id: str):
        if self._current and self._current in self._buttons:
            self._buttons[self._current].setStyleSheet("")
        self._current = nav_id
        if nav_id in self._buttons:
            self._buttons[nav_id].setStyleSheet(f"""
                background-color: {GENFIN_COLORS['teal']};
                color: {GENFIN_COLORS['text_white']};
                border-left: 3px solid {GENFIN_COLORS['teal_bright']};
            """)
        self.navigation_clicked.emit(nav_id)

    def set_active(self, nav_id: str):
        self._on_nav_click(nav_id)


class GenFinHomeScreen(QWidget):
    """90s QuickBooks-style home screen with icon grid."""

    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Welcome section
        welcome_frame = QFrame()
        welcome_frame.setProperty("class", "genfin-panel-raised")
        welcome_layout = QVBoxLayout(welcome_frame)

        welcome = QLabel("Welcome to GenFin Accounting")
        welcome.setProperty("class", "genfin-header-text")
        welcome.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
        """)
        welcome_layout.addWidget(welcome)

        subtitle = QLabel("Your Complete Farm & Business Accounting Solution")
        subtitle.setProperty("class", "genfin-label")
        welcome_layout.addWidget(subtitle)

        layout.addWidget(welcome_frame)

        # Icon grid (QuickBooks style)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(12)
        grid_layout.setContentsMargins(8, 8, 8, 8)

        # Icon buttons organized by category
        icons = [
            # Row 1 - Customers
            ("Customers", "$", "customers"),
            ("Invoices", "#", "invoices"),
            ("Receive $", "+", "receive"),
            ("Estimates", "E", "estimates"),

            # Row 2 - Vendors
            ("Vendors", "V", "vendors"),
            ("Bills", "B", "bills"),
            ("Pay Bills", "-", "pay"),
            ("Purchase", "P", "purchase"),

            # Row 3 - Banking
            ("Chart Acct", "C", "accounts"),
            ("Banking", "K", "banking"),
            ("Journal", "J", "journal"),
            ("Reconcile", "R", "reconcile"),

            # Row 4 - Payroll & Reporting
            ("Payroll", "Y", "payroll"),
            ("Employees", "M", "employees"),
            ("Reports", "T", "reports"),
            ("1099 Forms", "9", "1099"),

            # Row 5 - Multi-Entity & Budget
            ("Entities", "N", "entities"),
            ("Budget", "G", "budget"),
            ("Fixed Assets", "A", "assets"),
            ("Settings", "*", "settings"),
        ]

        for i, (title, icon, nav_id) in enumerate(icons):
            btn = GenFinIconButton(title, icon)
            btn.clicked.connect(lambda checked, nid=nav_id: self.navigate_to.emit(nid))
            grid_layout.addWidget(btn, i // 4, i % 4)

        # Center the grid
        grid_layout.setColumnStretch(4, 1)

        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, 1)

        # Quick stats bar at bottom
        stats_frame = QFrame()
        stats_frame.setProperty("class", "genfin-panel")
        stats_layout = QHBoxLayout(stats_frame)

        stats = [
            ("Cash Balance", "$142,385.00", "positive"),
            ("A/R Outstanding", "$28,500.00", "neutral"),
            ("A/P Outstanding", "$15,750.00", "neutral"),
            ("YTD Net Income", "$87,623.00", "positive"),
        ]

        for label, value, status in stats:
            stat_frame = QFrame()
            stat_layout = QVBoxLayout(stat_frame)
            stat_layout.setSpacing(2)

            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"font-size: 9px; color: {GENFIN_COLORS['text_light']};")
            stat_layout.addWidget(label_widget)

            value_widget = QLabel(value)
            color = GENFIN_COLORS['status_green'] if status == "positive" else GENFIN_COLORS['text_dark']
            value_widget.setStyleSheet(f"""
                font-family: "Courier New", monospace;
                font-size: 12px;
                font-weight: bold;
                color: {color};
            """)
            stat_layout.addWidget(value_widget)

            stats_layout.addWidget(stat_frame)

        layout.addWidget(stats_frame)


class GenFinListScreen(QWidget):
    """Generic list screen for customers, vendors, accounts, etc."""

    def __init__(self, title: str, columns: list, parent=None):
        super().__init__(parent)
        self.title = title
        self.columns = columns
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = GenFinToolbar()
        layout.addWidget(self.toolbar)

        # Content area with search
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # Search bar
        search_frame = QFrame()
        search_frame.setProperty("class", "genfin-panel-raised")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 4, 8, 4)

        search_label = QLabel("Search:")
        search_label.setProperty("class", "genfin-label")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setProperty("class", "genfin-input")
        self.search_input.setMaximumWidth(300)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Find")
        search_btn.setProperty("class", "genfin-button")
        search_layout.addWidget(search_btn)

        search_layout.addStretch()

        content_layout.addWidget(search_frame)

        # Table
        self.table = QTableWidget()
        self.table.setProperty("class", "genfin-table")
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setProperty("class", "genfin-header")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        content_layout.addWidget(self.table, 1)

        layout.addWidget(content)

    def set_data(self, rows: list):
        """Set table data from list of row tuples."""
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table.setItem(i, j, item)


class GenFinStatusBar(QFrame):
    """90s QuickBooks-style status bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-statusbar")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Main status text
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "genfin-status-text")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Date panel
        date_panel = QFrame()
        date_panel.setProperty("class", "genfin-status-panel")
        date_layout = QHBoxLayout(date_panel)
        date_layout.setContentsMargins(4, 2, 4, 2)
        self.date_label = QLabel(QDate.currentDate().toString("MMM dd, yyyy"))
        self.date_label.setProperty("class", "genfin-status-text")
        date_layout.addWidget(self.date_label)
        layout.addWidget(date_panel)

        # Company panel
        company_panel = QFrame()
        company_panel.setProperty("class", "genfin-status-panel")
        company_layout = QHBoxLayout(company_panel)
        company_layout.setContentsMargins(4, 2, 4, 2)
        self.company_label = QLabel("Tap Parker Farms")
        self.company_label.setProperty("class", "genfin-status-text")
        company_layout.addWidget(self.company_label)
        layout.addWidget(company_panel)

    def set_status(self, text: str):
        self.status_label.setText(text)


class GenFinScreen(QWidget):
    """
    Main GenFin Accounting screen with 90s QuickBooks UI.

    Features:
    - Teal blue color scheme
    - Beveled 3D buttons
    - Icon grid home screen
    - Classic toolbar
    - Navigation sidebar
    """

    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-main")
        self._screens = {}
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        self.title_bar = GenFinTitleBar("GenFin", "Professional Farm Accounting")
        layout.addWidget(self.title_bar)

        # Main content area
        main_content = QHBoxLayout()
        main_content.setContentsMargins(0, 0, 0, 0)
        main_content.setSpacing(0)

        # Navigation sidebar
        self.nav_sidebar = GenFinNavSidebar()
        self.nav_sidebar.navigation_clicked.connect(self._on_nav_click)
        main_content.addWidget(self.nav_sidebar)

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background-color: {GENFIN_COLORS['window_bg']};")

        # Add screens
        self._add_screens()

        main_content.addWidget(self.content_stack, 1)

        layout.addLayout(main_content, 1)

        # Status bar
        self.status_bar = GenFinStatusBar()
        layout.addWidget(self.status_bar)

        # Start at home
        self.nav_sidebar.set_active("home")

    def _add_screens(self):
        """Add all content screens to the stack."""
        # Home screen
        home = GenFinHomeScreen()
        home.navigate_to.connect(self._on_nav_click)
        self._add_screen("home", home)

        # List screens with sample data
        customers = GenFinListScreen("Customers", ["Name", "Company", "Phone", "Balance"])
        customers.set_data([
            ("John Smith", "Smith Farms", "(555) 123-4567", "$5,250.00"),
            ("Jane Doe", "Doe Agriculture", "(555) 234-5678", "$3,100.00"),
            ("Bob Wilson", "Wilson Grains", "(555) 345-6789", "$8,750.00"),
        ])
        self._add_screen("customers", customers)

        vendors = GenFinListScreen("Vendors", ["Name", "Company", "Phone", "Balance"])
        vendors.set_data([
            ("Ag Supply Co", "Ag Supply Inc", "(555) 111-2222", "$2,500.00"),
            ("Farm Equipment", "FE Holdings", "(555) 333-4444", "$12,000.00"),
            ("Seed & Feed", "S&F Corp", "(555) 555-6666", "$1,250.00"),
        ])
        self._add_screen("vendors", vendors)

        accounts = GenFinListScreen("Chart of Accounts", ["Number", "Name", "Type", "Balance"])
        accounts.set_data([
            ("1000", "Cash - Checking", "Bank", "$142,385.00"),
            ("1100", "Accounts Receivable", "A/R", "$28,500.00"),
            ("2000", "Accounts Payable", "A/P", "$15,750.00"),
            ("3000", "Owner's Equity", "Equity", "$250,000.00"),
            ("4000", "Crop Sales", "Income", "$425,000.00"),
            ("5000", "Seed Expense", "Expense", "$45,000.00"),
        ])
        self._add_screen("accounts", accounts)

        invoices = GenFinListScreen("Invoices", ["Number", "Customer", "Date", "Amount", "Status"])
        invoices.set_data([
            ("INV-001", "Smith Farms", "12/15/2025", "$5,250.00", "Open"),
            ("INV-002", "Doe Agriculture", "12/18/2025", "$3,100.00", "Open"),
            ("INV-003", "Wilson Grains", "12/20/2025", "$8,750.00", "Paid"),
        ])
        self._add_screen("invoices", invoices)

        bills = GenFinListScreen("Bills", ["Number", "Vendor", "Date", "Amount", "Status"])
        bills.set_data([
            ("BILL-001", "Ag Supply Co", "12/10/2025", "$2,500.00", "Open"),
            ("BILL-002", "Farm Equipment", "12/12/2025", "$12,000.00", "Open"),
            ("BILL-003", "Seed & Feed", "12/14/2025", "$1,250.00", "Paid"),
        ])
        self._add_screen("bills", bills)

        payroll = GenFinListScreen("Payroll", ["Employee", "Pay Type", "Rate", "YTD Gross"])
        payroll.set_data([
            ("Mike Johnson", "Hourly", "$22.00/hr", "$45,760.00"),
            ("Sarah Williams", "Salary", "$52,000/yr", "$50,000.00"),
            ("Tom Brown", "Hourly", "$18.00/hr", "$37,440.00"),
        ])
        self._add_screen("payroll", payroll)

        employees = GenFinListScreen("Employees", ["Name", "Position", "Hire Date", "Status"])
        employees.set_data([
            ("Mike Johnson", "Equipment Operator", "03/15/2020", "Active"),
            ("Sarah Williams", "Office Manager", "01/10/2019", "Active"),
            ("Tom Brown", "Farm Hand", "06/01/2021", "Active"),
        ])
        self._add_screen("employees", employees)

        reports = GenFinListScreen("Reports", ["Report Name", "Category", "Last Run"])
        reports.set_data([
            ("Profit & Loss", "Financial", "12/28/2025"),
            ("Balance Sheet", "Financial", "12/28/2025"),
            ("Cash Flow", "Financial", "12/25/2025"),
            ("A/R Aging", "Receivables", "12/27/2025"),
            ("A/P Aging", "Payables", "12/27/2025"),
            ("Payroll Summary", "Payroll", "12/20/2025"),
        ])
        self._add_screen("reports", reports)

        forms_1099 = GenFinListScreen("1099 Forms", ["Vendor", "Tax ID", "Amount", "Status"])
        forms_1099.set_data([
            ("Consultant LLC", "12-3456789", "$4,500.00", "Ready"),
            ("Repair Services", "98-7654321", "$2,800.00", "Missing TIN"),
            ("Land Rent Co", "55-1234567", "$12,000.00", "Ready"),
        ])
        self._add_screen("1099", forms_1099)

        # Placeholder for other screens
        for nav_id in ["receive", "pay", "banking", "journal", "estimates",
                       "purchase", "reconcile", "entities", "budget", "assets", "settings"]:
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon = QLabel("$")
            icon.setStyleSheet(f"""
                font-size: 48px;
                color: {GENFIN_COLORS['teal']};
                font-weight: bold;
            """)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(icon)

            title = QLabel(nav_id.replace("_", " ").title())
            title.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {GENFIN_COLORS['teal_dark']};
            """)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(title)

            coming = QLabel("Coming Soon")
            coming.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; font-size: 12px;")
            coming.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(coming)

            self._add_screen(nav_id, placeholder)

    def _add_screen(self, nav_id: str, widget: QWidget):
        """Add a screen to the content stack."""
        self._screens[nav_id] = widget
        self.content_stack.addWidget(widget)

    def _on_nav_click(self, nav_id: str):
        """Handle navigation click."""
        if nav_id in self._screens:
            self.content_stack.setCurrentWidget(self._screens[nav_id])
            self.status_bar.set_status(f"{nav_id.replace('_', ' ').title()} - Ready")

    def _apply_styles(self):
        """Apply the 90s QuickBooks stylesheet."""
        self.setStyleSheet(get_genfin_stylesheet())
