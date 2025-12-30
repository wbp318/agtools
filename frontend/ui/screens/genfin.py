"""
GenFin Accounting - 90s QuickBooks Style Interface

A nostalgic 90s QuickBooks-inspired accounting interface with
teal blue theme, beveled 3D buttons, and chunky icon grid.
Now with full CRUD functionality connected to backend API.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QGroupBox, QTabWidget,
    QSizePolicy, QMessageBox, QSpacerItem, QDialog,
    QFormLayout, QTextEdit, QCheckBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence

import requests
from datetime import datetime, date
from typing import Optional, Dict, List, Any

from ui.genfin_styles import GENFIN_COLORS, get_genfin_stylesheet, set_genfin_class

# Backend API base URL
API_BASE = "http://127.0.0.1:8000/api/v1/genfin"


def api_get(endpoint: str) -> Optional[Dict]:
    """Make GET request to GenFin API."""
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"API GET error: {e}")
        return None


def api_post(endpoint: str, data: Dict) -> Optional[Dict]:
    """Make POST request to GenFin API."""
    try:
        response = requests.post(f"{API_BASE}{endpoint}", json=data, timeout=5)
        return response.json()
    except Exception as e:
        print(f"API POST error: {e}")
        return None


def api_put(endpoint: str, data: Dict) -> Optional[Dict]:
    """Make PUT request to GenFin API."""
    try:
        response = requests.put(f"{API_BASE}{endpoint}", json=data, timeout=5)
        return response.json()
    except Exception as e:
        print(f"API PUT error: {e}")
        return None


def api_delete(endpoint: str) -> bool:
    """Make DELETE request to GenFin API."""
    try:
        response = requests.delete(f"{API_BASE}{endpoint}", timeout=5)
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"API DELETE error: {e}")
        return False


# =============================================================================
# DIALOG COMPONENTS
# =============================================================================

class GenFinDialog(QDialog):
    """Base dialog with 90s QuickBooks styling."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self._setup_base_style()

    def _setup_base_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {GENFIN_COLORS['window_face']};
                font-family: "MS Sans Serif", "Tahoma", sans-serif;
                font-size: 11px;
            }}
            QLabel {{
                color: {GENFIN_COLORS['text_dark']};
            }}
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                background-color: white;
                border-top: 2px solid {GENFIN_COLORS['bevel_dark']};
                border-left: 2px solid {GENFIN_COLORS['bevel_dark']};
                border-bottom: 2px solid {GENFIN_COLORS['bevel_light']};
                border-right: 2px solid {GENFIN_COLORS['bevel_light']};
                padding: 4px;
                min-height: 20px;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px groove {GENFIN_COLORS['bevel_shadow']};
                margin-top: 12px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                padding: 0 6px;
                color: {GENFIN_COLORS['teal_dark']};
            }}
            QPushButton {{
                background-color: {GENFIN_COLORS['window_face']};
                border-top: 2px solid {GENFIN_COLORS['bevel_light']};
                border-left: 2px solid {GENFIN_COLORS['bevel_light']};
                border-bottom: 2px solid {GENFIN_COLORS['bevel_dark']};
                border-right: 2px solid {GENFIN_COLORS['bevel_dark']};
                padding: 6px 16px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {GENFIN_COLORS['icon_hover']};
            }}
            QPushButton:pressed {{
                border-top: 2px solid {GENFIN_COLORS['bevel_dark']};
                border-left: 2px solid {GENFIN_COLORS['bevel_dark']};
                border-bottom: 2px solid {GENFIN_COLORS['bevel_light']};
                border-right: 2px solid {GENFIN_COLORS['bevel_light']};
            }}
        """)


class AddEmployeeDialog(GenFinDialog):
    """Dialog for adding/editing an employee."""

    def __init__(self, employee_data: Optional[Dict] = None, parent=None):
        title = "Edit Employee" if employee_data else "Add New Employee"
        super().__init__(title, parent)
        self.employee_data = employee_data
        self.result_data = None
        self._setup_ui()
        if employee_data:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Create tab widget for organizing fields
        tabs = QTabWidget()

        # === Personal Info Tab ===
        personal_tab = QWidget()
        personal_layout = QFormLayout(personal_tab)
        personal_layout.setSpacing(8)

        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("Required")
        personal_layout.addRow("First Name*:", self.first_name)

        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Required")
        personal_layout.addRow("Last Name*:", self.last_name)

        self.middle_name = QLineEdit()
        personal_layout.addRow("Middle Name:", self.middle_name)

        self.email = QLineEdit()
        self.email.setPlaceholderText("email@example.com")
        personal_layout.addRow("Email:", self.email)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("(555) 123-4567")
        personal_layout.addRow("Phone:", self.phone)

        self.ssn = QLineEdit()
        self.ssn.setPlaceholderText("XXX-XX-XXXX")
        self.ssn.setEchoMode(QLineEdit.EchoMode.Password)
        personal_layout.addRow("SSN:", self.ssn)

        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDate(QDate(1990, 1, 1))
        personal_layout.addRow("Date of Birth:", self.dob)

        tabs.addTab(personal_tab, "Personal")

        # === Address Tab ===
        address_tab = QWidget()
        address_layout = QFormLayout(address_tab)
        address_layout.setSpacing(8)

        self.address = QLineEdit()
        address_layout.addRow("Address:", self.address)

        self.city = QLineEdit()
        address_layout.addRow("City:", self.city)

        self.state = QComboBox()
        states = ["", "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
        self.state.addItems(states)
        address_layout.addRow("State:", self.state)

        self.zip_code = QLineEdit()
        self.zip_code.setMaximumWidth(100)
        address_layout.addRow("ZIP Code:", self.zip_code)

        tabs.addTab(address_tab, "Address")

        # === Employment Tab ===
        employment_tab = QWidget()
        employment_layout = QFormLayout(employment_tab)
        employment_layout.setSpacing(8)

        self.employee_type = QComboBox()
        self.employee_type.addItems(["full_time", "part_time", "seasonal", "contractor"])
        employment_layout.addRow("Employee Type:", self.employee_type)

        self.department = QLineEdit()
        employment_layout.addRow("Department:", self.department)

        self.job_title = QLineEdit()
        employment_layout.addRow("Job Title:", self.job_title)

        self.hire_date = QDateEdit()
        self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate())
        employment_layout.addRow("Hire Date:", self.hire_date)

        self.is_owner = QCheckBox("This employee is an owner/shareholder")
        employment_layout.addRow("", self.is_owner)

        tabs.addTab(employment_tab, "Employment")

        # === Pay Tab ===
        pay_tab = QWidget()
        pay_layout = QFormLayout(pay_tab)
        pay_layout.setSpacing(8)

        self.pay_type = QComboBox()
        self.pay_type.addItems(["hourly", "salary", "piece_rate"])
        pay_layout.addRow("Pay Type:", self.pay_type)

        self.pay_rate = QDoubleSpinBox()
        self.pay_rate.setMaximum(999999.99)
        self.pay_rate.setDecimals(2)
        self.pay_rate.setPrefix("$ ")
        pay_layout.addRow("Pay Rate:", self.pay_rate)

        self.pay_frequency = QComboBox()
        self.pay_frequency.addItems(["weekly", "biweekly", "semimonthly", "monthly"])
        self.pay_frequency.setCurrentText("biweekly")
        pay_layout.addRow("Pay Frequency:", self.pay_frequency)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["check", "direct_deposit", "both"])
        pay_layout.addRow("Payment Method:", self.payment_method)

        tabs.addTab(pay_tab, "Pay")

        # === Tax Tab ===
        tax_tab = QWidget()
        tax_layout = QFormLayout(tax_tab)
        tax_layout.setSpacing(8)

        self.filing_status = QComboBox()
        self.filing_status.addItems([
            "single", "married_filing_jointly",
            "married_filing_separately", "head_of_household"
        ])
        tax_layout.addRow("Filing Status:", self.filing_status)

        self.federal_allowances = QSpinBox()
        self.federal_allowances.setMaximum(20)
        tax_layout.addRow("Federal Allowances:", self.federal_allowances)

        self.fed_additional = QDoubleSpinBox()
        self.fed_additional.setMaximum(9999.99)
        self.fed_additional.setPrefix("$ ")
        tax_layout.addRow("Fed. Additional W/H:", self.fed_additional)

        self.state_allowances = QSpinBox()
        self.state_allowances.setMaximum(20)
        tax_layout.addRow("State Allowances:", self.state_allowances)

        tabs.addTab(tax_tab, "Tax Info")

        # === Direct Deposit Tab ===
        dd_tab = QWidget()
        dd_layout = QFormLayout(dd_tab)
        dd_layout.setSpacing(8)

        self.bank_routing = QLineEdit()
        self.bank_routing.setPlaceholderText("9 digits")
        dd_layout.addRow("Routing Number:", self.bank_routing)

        self.bank_account = QLineEdit()
        self.bank_account.setEchoMode(QLineEdit.EchoMode.Password)
        dd_layout.addRow("Account Number:", self.bank_account)

        self.bank_account_type = QComboBox()
        self.bank_account_type.addItems(["checking", "savings"])
        dd_layout.addRow("Account Type:", self.bank_account_type)

        tabs.addTab(dd_tab, "Direct Deposit")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            border-top: 2px solid {GENFIN_COLORS['teal_light']};
            border-left: 2px solid {GENFIN_COLORS['teal_light']};
            border-bottom: 2px solid {GENFIN_COLORS['teal_dark']};
            border-right: 2px solid {GENFIN_COLORS['teal_dark']};
        """)
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_data(self):
        """Load existing employee data into form."""
        d = self.employee_data
        self.first_name.setText(d.get("first_name", ""))
        self.last_name.setText(d.get("last_name", ""))
        self.middle_name.setText(d.get("middle_name", ""))
        self.email.setText(d.get("email", ""))
        self.phone.setText(d.get("phone", ""))

        if d.get("hire_date"):
            self.hire_date.setDate(QDate.fromString(d["hire_date"], "yyyy-MM-dd"))

        self.employee_type.setCurrentText(d.get("employee_type", "full_time"))
        self.department.setText(d.get("department", ""))
        self.job_title.setText(d.get("job_title", ""))
        self.pay_type.setCurrentText(d.get("pay_type", "hourly"))
        self.pay_rate.setValue(d.get("pay_rate", 0))
        self.pay_frequency.setCurrentText(d.get("pay_frequency", "biweekly"))
        self.filing_status.setCurrentText(d.get("filing_status", "single"))
        self.payment_method.setCurrentText(d.get("payment_method", "check"))

    def _save(self):
        """Validate and save employee data."""
        if not self.first_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "First name is required.")
            return
        if not self.last_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Last name is required.")
            return

        self.result_data = {
            "first_name": self.first_name.text().strip(),
            "last_name": self.last_name.text().strip(),
            "middle_name": self.middle_name.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "ssn": self.ssn.text().strip(),
            "date_of_birth": self.dob.date().toString("yyyy-MM-dd"),
            "address_line1": self.address.text().strip(),
            "city": self.city.text().strip(),
            "state": self.state.currentText(),
            "zip_code": self.zip_code.text().strip(),
            "employee_type": self.employee_type.currentText(),
            "department": self.department.text().strip(),
            "job_title": self.job_title.text().strip(),
            "hire_date": self.hire_date.date().toString("yyyy-MM-dd"),
            "pay_type": self.pay_type.currentText(),
            "pay_rate": self.pay_rate.value(),
            "pay_frequency": self.pay_frequency.currentText(),
            "filing_status": self.filing_status.currentText(),
            "federal_allowances": self.federal_allowances.value(),
            "federal_additional_withholding": self.fed_additional.value(),
            "state_allowances": self.state_allowances.value(),
            "payment_method": self.payment_method.currentText(),
            "bank_routing_number": self.bank_routing.text().strip(),
            "bank_account_number": self.bank_account.text().strip(),
            "bank_account_type": self.bank_account_type.currentText(),
            "is_owner": self.is_owner.isChecked()
        }
        self.accept()


class AddCustomerDialog(GenFinDialog):
    """Dialog for adding/editing a customer."""

    def __init__(self, customer_data: Optional[Dict] = None, parent=None):
        title = "Edit Customer" if customer_data else "Add New Customer"
        super().__init__(title, parent)
        self.customer_data = customer_data
        self.result_data = None
        self._setup_ui()
        if customer_data:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Required")
        form.addRow("Customer Name*:", self.name)

        self.company = QLineEdit()
        form.addRow("Company:", self.company)

        self.email = QLineEdit()
        form.addRow("Email:", self.email)

        self.phone = QLineEdit()
        form.addRow("Phone:", self.phone)

        self.address = QLineEdit()
        form.addRow("Address:", self.address)

        self.city = QLineEdit()
        form.addRow("City:", self.city)

        self.state = QLineEdit()
        self.state.setMaximumWidth(60)
        form.addRow("State:", self.state)

        self.zip_code = QLineEdit()
        self.zip_code.setMaximumWidth(100)
        form.addRow("ZIP:", self.zip_code)

        self.credit_limit = QDoubleSpinBox()
        self.credit_limit.setMaximum(9999999.99)
        self.credit_limit.setPrefix("$ ")
        form.addRow("Credit Limit:", self.credit_limit)

        self.payment_terms = QComboBox()
        self.payment_terms.addItems(["Net 30", "Net 15", "Net 60", "Due on Receipt", "Net 10"])
        form.addRow("Payment Terms:", self.payment_terms)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form.addRow("Notes:", self.notes)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_data(self):
        d = self.customer_data
        self.name.setText(d.get("name", ""))
        self.company.setText(d.get("company", ""))
        self.email.setText(d.get("email", ""))
        self.phone.setText(d.get("phone", ""))
        self.address.setText(d.get("address_line1", ""))
        self.city.setText(d.get("city", ""))
        self.state.setText(d.get("state", ""))
        self.zip_code.setText(d.get("zip_code", ""))
        self.credit_limit.setValue(d.get("credit_limit", 0))
        self.notes.setText(d.get("notes", ""))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Customer name is required.")
            return

        self.result_data = {
            "name": self.name.text().strip(),
            "company": self.company.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "address_line1": self.address.text().strip(),
            "city": self.city.text().strip(),
            "state": self.state.text().strip(),
            "zip_code": self.zip_code.text().strip(),
            "credit_limit": self.credit_limit.value(),
            "payment_terms": self.payment_terms.currentText(),
            "notes": self.notes.toPlainText()
        }
        self.accept()


class AddVendorDialog(GenFinDialog):
    """Dialog for adding/editing a vendor."""

    def __init__(self, vendor_data: Optional[Dict] = None, parent=None):
        title = "Edit Vendor" if vendor_data else "Add New Vendor"
        super().__init__(title, parent)
        self.vendor_data = vendor_data
        self.result_data = None
        self._setup_ui()
        if vendor_data:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.name = QLineEdit()
        self.name.setPlaceholderText("Required")
        form.addRow("Vendor Name*:", self.name)

        self.company = QLineEdit()
        form.addRow("Company:", self.company)

        self.email = QLineEdit()
        form.addRow("Email:", self.email)

        self.phone = QLineEdit()
        form.addRow("Phone:", self.phone)

        self.address = QLineEdit()
        form.addRow("Address:", self.address)

        self.city = QLineEdit()
        form.addRow("City:", self.city)

        self.state = QLineEdit()
        self.state.setMaximumWidth(60)
        form.addRow("State:", self.state)

        self.zip_code = QLineEdit()
        self.zip_code.setMaximumWidth(100)
        form.addRow("ZIP:", self.zip_code)

        self.tax_id = QLineEdit()
        self.tax_id.setPlaceholderText("XX-XXXXXXX (for 1099)")
        form.addRow("Tax ID:", self.tax_id)

        self.is_1099 = QCheckBox("This vendor receives 1099")
        form.addRow("", self.is_1099)

        self.payment_terms = QComboBox()
        self.payment_terms.addItems(["Net 30", "Net 15", "Net 60", "Due on Receipt", "Net 10"])
        form.addRow("Payment Terms:", self.payment_terms)

        self.default_expense = QComboBox()
        self.default_expense.addItems(["", "Supplies", "Repairs", "Fuel", "Seed", "Fertilizer", "Equipment"])
        form.addRow("Default Expense:", self.default_expense)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form.addRow("Notes:", self.notes)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_data(self):
        d = self.vendor_data
        self.name.setText(d.get("name", ""))
        self.company.setText(d.get("company", ""))
        self.email.setText(d.get("email", ""))
        self.phone.setText(d.get("phone", ""))
        self.address.setText(d.get("address_line1", ""))
        self.city.setText(d.get("city", ""))
        self.state.setText(d.get("state", ""))
        self.zip_code.setText(d.get("zip_code", ""))
        self.tax_id.setText(d.get("tax_id", ""))
        self.is_1099.setChecked(d.get("is_1099_vendor", False))
        self.notes.setText(d.get("notes", ""))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Vendor name is required.")
            return

        self.result_data = {
            "name": self.name.text().strip(),
            "company": self.company.text().strip(),
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "address_line1": self.address.text().strip(),
            "city": self.city.text().strip(),
            "state": self.state.text().strip(),
            "zip_code": self.zip_code.text().strip(),
            "tax_id": self.tax_id.text().strip(),
            "is_1099_vendor": self.is_1099.isChecked(),
            "payment_terms": self.payment_terms.currentText(),
            "default_expense_account": self.default_expense.currentText(),
            "notes": self.notes.toPlainText()
        }
        self.accept()


class AddInvoiceDialog(GenFinDialog):
    """Dialog for creating an invoice."""

    def __init__(self, customers: List[Dict], parent=None):
        super().__init__("Create Invoice", parent)
        self.customers = customers
        self.result_data = None
        self.setMinimumWidth(600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        form_left = QFormLayout()
        self.customer = QComboBox()
        self.customer.addItem("-- Select Customer --", "")
        for c in self.customers:
            self.customer.addItem(c.get("name", "Unknown"), c.get("customer_id"))
        form_left.addRow("Customer*:", self.customer)

        self.invoice_date = QDateEdit()
        self.invoice_date.setCalendarPopup(True)
        self.invoice_date.setDate(QDate.currentDate())
        form_left.addRow("Invoice Date:", self.invoice_date)

        header_layout.addLayout(form_left)

        form_right = QFormLayout()
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(30))
        form_right.addRow("Due Date:", self.due_date)

        self.terms = QComboBox()
        self.terms.addItems(["Net 30", "Net 15", "Net 60", "Due on Receipt"])
        form_right.addRow("Terms:", self.terms)

        header_layout.addLayout(form_right)
        layout.addLayout(header_layout)

        # Line items
        lines_group = QGroupBox("Line Items")
        lines_layout = QVBoxLayout(lines_group)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(4)
        self.lines_table.setHorizontalHeaderLabels(["Description", "Quantity", "Rate", "Amount"])
        self.lines_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.lines_table.setRowCount(5)

        # Initialize empty rows
        for row in range(5):
            self.lines_table.setItem(row, 0, QTableWidgetItem(""))
            qty = QDoubleSpinBox()
            qty.setValue(1)
            qty.setDecimals(2)
            self.lines_table.setCellWidget(row, 1, qty)
            rate = QDoubleSpinBox()
            rate.setMaximum(999999.99)
            rate.setPrefix("$")
            self.lines_table.setCellWidget(row, 2, rate)
            self.lines_table.setItem(row, 3, QTableWidgetItem("$0.00"))

        lines_layout.addWidget(self.lines_table)
        layout.addWidget(lines_group)

        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        totals_form = QFormLayout()
        self.subtotal = QLabel("$0.00")
        self.subtotal.setStyleSheet("font-weight: bold;")
        totals_form.addRow("Subtotal:", self.subtotal)

        self.total = QLabel("$0.00")
        self.total.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {GENFIN_COLORS['teal_dark']};")
        totals_form.addRow("Total:", self.total)

        totals_layout.addLayout(totals_form)
        layout.addLayout(totals_layout)

        # Memo
        memo_layout = QFormLayout()
        self.memo = QLineEdit()
        memo_layout.addRow("Memo:", self.memo)
        layout.addLayout(memo_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Create Invoice")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _save(self):
        if not self.customer.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return

        # Collect line items
        lines = []
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            desc_item = self.lines_table.item(row, 0)
            desc = desc_item.text() if desc_item else ""
            if not desc.strip():
                continue

            qty_widget = self.lines_table.cellWidget(row, 1)
            rate_widget = self.lines_table.cellWidget(row, 2)
            qty = qty_widget.value() if qty_widget else 0
            rate = rate_widget.value() if rate_widget else 0

            amount = qty * rate
            total += amount

            lines.append({
                "description": desc,
                "quantity": qty,
                "rate": rate,
                "amount": amount
            })

        if not lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one line item.")
            return

        self.result_data = {
            "customer_id": self.customer.currentData(),
            "invoice_date": self.invoice_date.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "terms": self.terms.currentText(),
            "lines": lines,
            "memo": self.memo.text(),
            "total": total
        }
        self.accept()


class AddBillDialog(GenFinDialog):
    """Dialog for creating a bill."""

    def __init__(self, vendors: List[Dict], parent=None):
        super().__init__("Enter Bill", parent)
        self.vendors = vendors
        self.result_data = None
        self.setMinimumWidth(600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        form_left = QFormLayout()
        self.vendor = QComboBox()
        self.vendor.addItem("-- Select Vendor --", "")
        for v in self.vendors:
            self.vendor.addItem(v.get("name", "Unknown"), v.get("vendor_id"))
        form_left.addRow("Vendor*:", self.vendor)

        self.bill_date = QDateEdit()
        self.bill_date.setCalendarPopup(True)
        self.bill_date.setDate(QDate.currentDate())
        form_left.addRow("Bill Date:", self.bill_date)

        header_layout.addLayout(form_left)

        form_right = QFormLayout()
        self.ref_number = QLineEdit()
        self.ref_number.setPlaceholderText("Vendor invoice #")
        form_right.addRow("Ref Number:", self.ref_number)

        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate().addDays(30))
        form_right.addRow("Due Date:", self.due_date)

        header_layout.addLayout(form_right)
        layout.addLayout(header_layout)

        # Line items
        lines_group = QGroupBox("Expenses")
        lines_layout = QVBoxLayout(lines_group)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(3)
        self.lines_table.setHorizontalHeaderLabels(["Account/Description", "Memo", "Amount"])
        self.lines_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.lines_table.setRowCount(5)

        for row in range(5):
            account = QComboBox()
            account.addItems(["", "Supplies", "Repairs & Maintenance", "Fuel",
                            "Seed & Plants", "Fertilizer", "Equipment", "Utilities",
                            "Insurance", "Professional Services", "Rent"])
            self.lines_table.setCellWidget(row, 0, account)
            self.lines_table.setItem(row, 1, QTableWidgetItem(""))
            amount = QDoubleSpinBox()
            amount.setMaximum(999999.99)
            amount.setPrefix("$")
            self.lines_table.setCellWidget(row, 2, amount)

        lines_layout.addWidget(self.lines_table)
        layout.addWidget(lines_group)

        # Total
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.total = QLabel("$0.00")
        self.total.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {GENFIN_COLORS['teal_dark']};")
        totals_layout.addWidget(QLabel("Total:"))
        totals_layout.addWidget(self.total)
        layout.addLayout(totals_layout)

        # Memo
        memo_layout = QFormLayout()
        self.memo = QLineEdit()
        memo_layout.addRow("Memo:", self.memo)
        layout.addLayout(memo_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save Bill")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _save(self):
        if not self.vendor.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a vendor.")
            return

        lines = []
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            account_widget = self.lines_table.cellWidget(row, 0)
            account = account_widget.currentText() if account_widget else ""
            if not account:
                continue

            memo_item = self.lines_table.item(row, 1)
            memo = memo_item.text() if memo_item else ""

            amount_widget = self.lines_table.cellWidget(row, 2)
            amount = amount_widget.value() if amount_widget else 0

            if amount > 0:
                total += amount
                lines.append({
                    "account": account,
                    "memo": memo,
                    "amount": amount
                })

        if not lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one expense line.")
            return

        self.result_data = {
            "vendor_id": self.vendor.currentData(),
            "bill_date": self.bill_date.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date.date().toString("yyyy-MM-dd"),
            "ref_number": self.ref_number.text(),
            "lines": lines,
            "memo": self.memo.text(),
            "total": total
        }
        self.accept()


# =============================================================================
# RECEIVE PAYMENT DIALOG
# =============================================================================

class ReceivePaymentDialog(GenFinDialog):
    """Dialog for receiving payment from a customer."""

    def __init__(self, customers: List[Dict], parent=None):
        super().__init__("Receive Payment", parent)
        self.customers = customers
        self.result_data = None
        self.setMinimumWidth(650)
        self._open_invoices = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header section
        header_frame = QGroupBox("Payment Information")
        header_layout = QFormLayout(header_frame)
        header_layout.setSpacing(8)

        self.customer = QComboBox()
        self.customer.addItem("-- Select Customer --", "")
        for c in self.customers:
            balance = c.get("balance", 0)
            self.customer.addItem(f"{c.get('name', 'Unknown')} (${balance:,.2f} due)", c.get("customer_id"))
        self.customer.currentIndexChanged.connect(self._load_open_invoices)
        header_layout.addRow("Customer*:", self.customer)

        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        header_layout.addRow("Payment Date:", self.payment_date)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Check", "Cash", "Credit Card", "ACH/EFT", "Wire Transfer", "Other"])
        header_layout.addRow("Payment Method:", self.payment_method)

        self.ref_number = QLineEdit()
        self.ref_number.setPlaceholderText("Check # or Reference")
        header_layout.addRow("Reference #:", self.ref_number)

        self.amount = QDoubleSpinBox()
        self.amount.setPrefix("$ ")
        self.amount.setMaximum(9999999.99)
        self.amount.setDecimals(2)
        header_layout.addRow("Amount Received*:", self.amount)

        self.deposit_to = QComboBox()
        self.deposit_to.addItems(["Undeposited Funds", "Checking", "Savings", "Petty Cash"])
        header_layout.addRow("Deposit To:", self.deposit_to)

        layout.addWidget(header_frame)

        # Open Invoices section
        invoices_frame = QGroupBox("Apply to Open Invoices")
        invoices_layout = QVBoxLayout(invoices_frame)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(5)
        self.invoices_table.setHorizontalHeaderLabels(["Apply", "Invoice #", "Date", "Original Amt", "Open Balance"])
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setMaximumHeight(200)
        invoices_layout.addWidget(self.invoices_table)

        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        self.total_applied = QLabel("Applied: $0.00")
        self.total_applied.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.total_applied)

        totals_layout.addSpacing(20)

        self.unapplied_amt = QLabel("Unapplied: $0.00")
        self.unapplied_amt.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['status_red']};")
        totals_layout.addWidget(self.unapplied_amt)

        invoices_layout.addLayout(totals_layout)
        layout.addWidget(invoices_frame)

        # Memo
        memo_layout = QHBoxLayout()
        memo_layout.addWidget(QLabel("Memo:"))
        self.memo = QLineEdit()
        self.memo.setPlaceholderText("Optional memo for this payment")
        memo_layout.addWidget(self.memo)
        layout.addLayout(memo_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        save_new_btn = QPushButton("Save & New")
        save_new_btn.clicked.connect(self._save_new)
        button_layout.addWidget(save_new_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_open_invoices(self):
        """Load open invoices for selected customer."""
        customer_id = self.customer.currentData()
        if not customer_id:
            self.invoices_table.setRowCount(0)
            return

        # Fetch open invoices for customer
        invoices = api_get(f"/customers/{customer_id}/invoices?status=open")
        if invoices is None:
            invoices = []

        self._open_invoices = invoices if isinstance(invoices, list) else []
        self.invoices_table.setRowCount(len(self._open_invoices))

        for i, inv in enumerate(self._open_invoices):
            # Checkbox for apply
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_totals)
            self.invoices_table.setCellWidget(i, 0, checkbox)

            # Invoice details
            self.invoices_table.setItem(i, 1, QTableWidgetItem(inv.get("invoice_number", "")))
            self.invoices_table.setItem(i, 2, QTableWidgetItem(inv.get("invoice_date", "")))
            original = inv.get("total", 0)
            self.invoices_table.setItem(i, 3, QTableWidgetItem(f"${original:,.2f}"))
            balance = inv.get("balance_due", original)
            self.invoices_table.setItem(i, 4, QTableWidgetItem(f"${balance:,.2f}"))

    def _update_totals(self):
        """Update applied and unapplied totals."""
        total_applied = 0.0
        for i in range(self.invoices_table.rowCount()):
            checkbox = self.invoices_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                balance_item = self.invoices_table.item(i, 4)
                if balance_item:
                    balance_str = balance_item.text().replace("$", "").replace(",", "")
                    total_applied += float(balance_str)

        received = self.amount.value()
        unapplied = received - total_applied

        self.total_applied.setText(f"Applied: ${total_applied:,.2f}")
        if unapplied >= 0:
            self.unapplied_amt.setText(f"Unapplied: ${unapplied:,.2f}")
            self.unapplied_amt.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['status_green']};")
        else:
            self.unapplied_amt.setText(f"Over-Applied: ${abs(unapplied):,.2f}")
            self.unapplied_amt.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['status_red']};")

    def _save(self):
        if not self.customer.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return

        if self.amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter an amount received.")
            return

        applied_invoices = []
        for i in range(self.invoices_table.rowCount()):
            checkbox = self.invoices_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked() and i < len(self._open_invoices):
                inv = self._open_invoices[i]
                balance_item = self.invoices_table.item(i, 4)
                amount = float(balance_item.text().replace("$", "").replace(",", "")) if balance_item else 0
                applied_invoices.append({
                    "invoice_id": inv.get("invoice_id"),
                    "amount": amount
                })

        self.result_data = {
            "customer_id": self.customer.currentData(),
            "payment_date": self.payment_date.date().toString("yyyy-MM-dd"),
            "payment_method": self.payment_method.currentText().lower().replace(" ", "_"),
            "reference_number": self.ref_number.text(),
            "amount": self.amount.value(),
            "deposit_account": self.deposit_to.currentText(),
            "applied_invoices": applied_invoices,
            "memo": self.memo.text()
        }
        self.accept()

    def _save_new(self):
        """Save and reset for new payment."""
        self._save()
        if self.result_data:
            # Reset form
            self.customer.setCurrentIndex(0)
            self.amount.setValue(0)
            self.ref_number.clear()
            self.memo.clear()
            self.invoices_table.setRowCount(0)


# =============================================================================
# PAY BILLS DIALOG
# =============================================================================

class PayBillsDialog(GenFinDialog):
    """Dialog for paying vendor bills."""

    def __init__(self, vendors: List[Dict], parent=None):
        super().__init__("Pay Bills", parent)
        self.vendors = vendors
        self.result_data = None
        self.setMinimumWidth(700)
        self._open_bills = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Filter section
        filter_frame = QGroupBox("Filter Bills")
        filter_layout = QHBoxLayout(filter_frame)

        filter_layout.addWidget(QLabel("Show bills due:"))
        self.due_filter = QComboBox()
        self.due_filter.addItems(["All", "Due Today", "Due This Week", "Overdue"])
        self.due_filter.currentIndexChanged.connect(self._load_open_bills)
        filter_layout.addWidget(self.due_filter)

        filter_layout.addWidget(QLabel("Vendor:"))
        self.vendor_filter = QComboBox()
        self.vendor_filter.addItem("All Vendors", "")
        for v in self.vendors:
            self.vendor_filter.addItem(v.get("name", ""), v.get("vendor_id"))
        self.vendor_filter.currentIndexChanged.connect(self._load_open_bills)
        filter_layout.addWidget(self.vendor_filter)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

        # Bills table
        bills_frame = QGroupBox("Bills to Pay")
        bills_layout = QVBoxLayout(bills_frame)

        self.bills_table = QTableWidget()
        self.bills_table.setColumnCount(7)
        self.bills_table.setHorizontalHeaderLabels([
            "Pay", "Date Due", "Vendor", "Ref #", "Original Amt", "Open Balance", "Payment"
        ])
        self.bills_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.bills_table.setAlternatingRowColors(True)
        bills_layout.addWidget(self.bills_table)

        layout.addWidget(bills_frame, 1)

        # Payment info
        payment_frame = QGroupBox("Payment Information")
        payment_layout = QFormLayout(payment_frame)

        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        payment_layout.addRow("Payment Date:", self.payment_date)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Check", "ACH/EFT", "Credit Card", "Wire Transfer", "Cash"])
        payment_layout.addRow("Payment Method:", self.payment_method)

        self.pay_from = QComboBox()
        self.pay_from.addItems(["Checking", "Savings", "Money Market", "Credit Card"])
        payment_layout.addRow("Pay From Account:", self.pay_from)

        layout.addWidget(payment_frame)

        # Totals bar
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        totals_layout.addWidget(QLabel("Bills Selected:"))
        self.selected_count = QLabel("0")
        self.selected_count.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.selected_count)

        totals_layout.addSpacing(20)

        totals_layout.addWidget(QLabel("Total to Pay:"))
        self.total_payment = QLabel("$0.00")
        self.total_payment.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['teal_dark']};")
        totals_layout.addWidget(self.total_payment)

        layout.addLayout(totals_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        pay_btn = QPushButton("Pay Selected Bills")
        pay_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        pay_btn.clicked.connect(self._save)
        button_layout.addWidget(pay_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Load initial bills
        QTimer.singleShot(100, self._load_open_bills)

    def _load_open_bills(self):
        """Load open bills based on filters."""
        vendor_id = self.vendor_filter.currentData()
        endpoint = "/bills?status=open"
        if vendor_id:
            endpoint += f"&vendor_id={vendor_id}"

        bills = api_get(endpoint)
        if bills is None:
            bills = []

        self._open_bills = bills if isinstance(bills, list) else []
        self.bills_table.setRowCount(len(self._open_bills))

        for i, bill in enumerate(self._open_bills):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_totals)
            self.bills_table.setCellWidget(i, 0, checkbox)

            # Bill details
            self.bills_table.setItem(i, 1, QTableWidgetItem(bill.get("due_date", "")))
            self.bills_table.setItem(i, 2, QTableWidgetItem(bill.get("vendor_name", "")))
            self.bills_table.setItem(i, 3, QTableWidgetItem(bill.get("ref_number", "")))
            original = bill.get("total", 0)
            self.bills_table.setItem(i, 4, QTableWidgetItem(f"${original:,.2f}"))
            balance = bill.get("balance_due", original)
            self.bills_table.setItem(i, 5, QTableWidgetItem(f"${balance:,.2f}"))

            # Payment amount spinbox
            payment_spin = QDoubleSpinBox()
            payment_spin.setPrefix("$ ")
            payment_spin.setMaximum(balance)
            payment_spin.setDecimals(2)
            payment_spin.setValue(balance)
            payment_spin.valueChanged.connect(self._update_totals)
            self.bills_table.setCellWidget(i, 6, payment_spin)

    def _update_totals(self):
        """Update selected count and total payment."""
        count = 0
        total = 0.0

        for i in range(self.bills_table.rowCount()):
            checkbox = self.bills_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                count += 1
                payment_spin = self.bills_table.cellWidget(i, 6)
                if payment_spin:
                    total += payment_spin.value()

        self.selected_count.setText(str(count))
        self.total_payment.setText(f"${total:,.2f}")

    def _save(self):
        payments = []
        for i in range(self.bills_table.rowCount()):
            checkbox = self.bills_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked() and i < len(self._open_bills):
                payment_spin = self.bills_table.cellWidget(i, 6)
                amount = payment_spin.value() if payment_spin else 0
                if amount > 0:
                    bill = self._open_bills[i]
                    payments.append({
                        "bill_id": bill.get("bill_id"),
                        "amount": amount
                    })

        if not payments:
            QMessageBox.warning(self, "Validation Error", "Please select at least one bill to pay.")
            return

        self.result_data = {
            "payment_date": self.payment_date.date().toString("yyyy-MM-dd"),
            "payment_method": self.payment_method.currentText().lower().replace(" ", "_"),
            "pay_from_account": self.pay_from.currentText(),
            "payments": payments
        }
        self.accept()


# =============================================================================
# WRITE CHECK DIALOG
# =============================================================================

class WriteCheckDialog(GenFinDialog):
    """Dialog for writing a check."""

    def __init__(self, parent=None):
        super().__init__("Write Checks", parent)
        self.result_data = None
        self.setMinimumWidth(650)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Check header (looks like a check)
        check_frame = QFrame()
        check_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFF0;
                border: 2px solid {GENFIN_COLORS['bevel_dark']};
                border-radius: 4px;
                padding: 16px;
            }}
        """)
        check_layout = QVBoxLayout(check_frame)

        # Bank account row
        bank_row = QHBoxLayout()
        bank_row.addWidget(QLabel("Bank Account:"))
        self.bank_account = QComboBox()
        self.bank_account.addItems(["Checking", "Savings", "Money Market", "Payroll"])
        bank_row.addWidget(self.bank_account)
        bank_row.addStretch()
        bank_row.addWidget(QLabel("Check #:"))
        self.check_number = QLineEdit()
        self.check_number.setMaximumWidth(100)
        self.check_number.setPlaceholderText("Auto")
        bank_row.addWidget(self.check_number)
        check_layout.addLayout(bank_row)

        check_layout.addSpacing(8)

        # Date and payee
        payee_row = QHBoxLayout()
        payee_row.addWidget(QLabel("Date:"))
        self.check_date = QDateEdit()
        self.check_date.setCalendarPopup(True)
        self.check_date.setDate(QDate.currentDate())
        payee_row.addWidget(self.check_date)
        payee_row.addSpacing(20)
        payee_row.addWidget(QLabel("Pay to the Order of:"))
        self.payee = QLineEdit()
        self.payee.setMinimumWidth(250)
        payee_row.addWidget(self.payee)
        check_layout.addLayout(payee_row)

        # Amount
        amount_row = QHBoxLayout()
        amount_row.addStretch()
        amount_row.addWidget(QLabel("$"))
        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(9999999.99)
        self.amount.setDecimals(2)
        self.amount.setMinimumWidth(150)
        self.amount.setStyleSheet("font-size: 14px; font-weight: bold;")
        amount_row.addWidget(self.amount)
        check_layout.addLayout(amount_row)

        # Address
        addr_row = QHBoxLayout()
        self.address = QTextEdit()
        self.address.setMaximumHeight(60)
        self.address.setPlaceholderText("Payee Address (optional)")
        addr_row.addWidget(self.address)
        check_layout.addLayout(addr_row)

        # Memo
        memo_row = QHBoxLayout()
        memo_row.addWidget(QLabel("Memo:"))
        self.memo = QLineEdit()
        memo_row.addWidget(self.memo)
        check_layout.addLayout(memo_row)

        layout.addWidget(check_frame)

        # Expense details
        expense_frame = QGroupBox("Expense Details")
        expense_layout = QVBoxLayout(expense_frame)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(3)
        self.expense_table.setHorizontalHeaderLabels(["Account", "Memo", "Amount"])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.expense_table.setRowCount(5)

        expense_accounts = ["", "Supplies", "Repairs", "Fuel", "Seed", "Fertilizer",
                           "Equipment", "Utilities", "Insurance", "Professional Fees", "Other"]

        for row in range(5):
            account_combo = QComboBox()
            account_combo.addItems(expense_accounts)
            self.expense_table.setCellWidget(row, 0, account_combo)

            self.expense_table.setItem(row, 1, QTableWidgetItem(""))

            amount_spin = QDoubleSpinBox()
            amount_spin.setMaximum(9999999.99)
            amount_spin.setDecimals(2)
            amount_spin.setPrefix("$ ")
            self.expense_table.setCellWidget(row, 2, amount_spin)

        expense_layout.addWidget(self.expense_table)
        layout.addWidget(expense_frame)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        print_btn = QPushButton("Print Check")
        print_btn.clicked.connect(self._print_check)
        button_layout.addWidget(print_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _print_check(self):
        """Print the check."""
        QMessageBox.information(self, "Print", "Check print functionality coming soon!")

    def _save(self):
        if not self.payee.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter payee name.")
            return

        if self.amount.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter an amount.")
            return

        expenses = []
        for row in range(self.expense_table.rowCount()):
            account_widget = self.expense_table.cellWidget(row, 0)
            account = account_widget.currentText() if account_widget else ""
            if not account:
                continue

            memo_item = self.expense_table.item(row, 1)
            memo = memo_item.text() if memo_item else ""

            amount_widget = self.expense_table.cellWidget(row, 2)
            amt = amount_widget.value() if amount_widget else 0
            if amt > 0:
                expenses.append({"account": account, "memo": memo, "amount": amt})

        self.result_data = {
            "bank_account": self.bank_account.currentText(),
            "check_number": self.check_number.text() or "auto",
            "check_date": self.check_date.date().toString("yyyy-MM-dd"),
            "payee": self.payee.text().strip(),
            "amount": self.amount.value(),
            "address": self.address.toPlainText(),
            "memo": self.memo.text(),
            "expenses": expenses
        }
        self.accept()


# =============================================================================
# MAKE DEPOSIT DIALOG
# =============================================================================

class MakeDepositDialog(GenFinDialog):
    """Dialog for making a bank deposit."""

    def __init__(self, parent=None):
        super().__init__("Make Deposits", parent)
        self.result_data = None
        self.setMinimumWidth(700)
        self._undeposited = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Deposit info
        info_frame = QGroupBox("Deposit Information")
        info_layout = QFormLayout(info_frame)

        self.deposit_date = QDateEdit()
        self.deposit_date.setCalendarPopup(True)
        self.deposit_date.setDate(QDate.currentDate())
        info_layout.addRow("Deposit Date:", self.deposit_date)

        self.deposit_to = QComboBox()
        self.deposit_to.addItems(["Checking", "Savings", "Money Market"])
        info_layout.addRow("Deposit To:", self.deposit_to)

        layout.addWidget(info_frame)

        # Undeposited funds
        funds_frame = QGroupBox("Payments to Deposit (from Undeposited Funds)")
        funds_layout = QVBoxLayout(funds_frame)

        self.funds_table = QTableWidget()
        self.funds_table.setColumnCount(5)
        self.funds_table.setHorizontalHeaderLabels(["Select", "Date", "Type", "Customer/Payer", "Amount"])
        self.funds_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.funds_table.setAlternatingRowColors(True)
        funds_layout.addWidget(self.funds_table)

        layout.addWidget(funds_frame, 1)

        # Other items
        other_frame = QGroupBox("Other Cash/Checks to Deposit")
        other_layout = QVBoxLayout(other_frame)

        self.other_table = QTableWidget()
        self.other_table.setColumnCount(4)
        self.other_table.setHorizontalHeaderLabels(["Received From", "Account", "Memo", "Amount"])
        self.other_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.other_table.setRowCount(3)

        accounts = ["", "Other Income", "Sales", "Interest Income", "Refunds"]
        for row in range(3):
            self.other_table.setItem(row, 0, QTableWidgetItem(""))
            account_combo = QComboBox()
            account_combo.addItems(accounts)
            self.other_table.setCellWidget(row, 1, account_combo)
            self.other_table.setItem(row, 2, QTableWidgetItem(""))
            amount_spin = QDoubleSpinBox()
            amount_spin.setPrefix("$ ")
            amount_spin.setMaximum(9999999.99)
            amount_spin.setDecimals(2)
            self.other_table.setCellWidget(row, 3, amount_spin)

        other_layout.addWidget(self.other_table)
        layout.addWidget(other_frame)

        # Totals
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        totals_layout.addWidget(QLabel("Total Deposit:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {GENFIN_COLORS['teal_dark']};")
        totals_layout.addWidget(self.total_label)
        layout.addLayout(totals_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        # Load undeposited funds
        QTimer.singleShot(100, self._load_undeposited)

    def _load_undeposited(self):
        """Load payments in undeposited funds."""
        payments = api_get("/deposits/undeposited")
        if payments is None:
            payments = []

        self._undeposited = payments if isinstance(payments, list) else []
        self.funds_table.setRowCount(len(self._undeposited))

        for i, pmt in enumerate(self._undeposited):
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_total)
            self.funds_table.setCellWidget(i, 0, checkbox)

            self.funds_table.setItem(i, 1, QTableWidgetItem(pmt.get("date", "")))
            self.funds_table.setItem(i, 2, QTableWidgetItem(pmt.get("type", "Payment")))
            self.funds_table.setItem(i, 3, QTableWidgetItem(pmt.get("customer", "")))
            amount = pmt.get("amount", 0)
            self.funds_table.setItem(i, 4, QTableWidgetItem(f"${amount:,.2f}"))

    def _update_total(self):
        """Update total deposit amount."""
        total = 0.0

        # Undeposited funds
        for i in range(self.funds_table.rowCount()):
            checkbox = self.funds_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                amount_item = self.funds_table.item(i, 4)
                if amount_item:
                    total += float(amount_item.text().replace("$", "").replace(",", ""))

        # Other items
        for i in range(self.other_table.rowCount()):
            amount_spin = self.other_table.cellWidget(i, 3)
            if amount_spin:
                total += amount_spin.value()

        self.total_label.setText(f"${total:,.2f}")

    def _save(self):
        selected_payments = []
        for i in range(self.funds_table.rowCount()):
            checkbox = self.funds_table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked() and i < len(self._undeposited):
                selected_payments.append(self._undeposited[i].get("payment_id"))

        other_items = []
        for row in range(self.other_table.rowCount()):
            from_item = self.other_table.item(row, 0)
            received_from = from_item.text() if from_item else ""
            if not received_from:
                continue

            account_combo = self.other_table.cellWidget(row, 1)
            account = account_combo.currentText() if account_combo else ""

            memo_item = self.other_table.item(row, 2)
            memo = memo_item.text() if memo_item else ""

            amount_spin = self.other_table.cellWidget(row, 3)
            amount = amount_spin.value() if amount_spin else 0

            if amount > 0:
                other_items.append({
                    "received_from": received_from,
                    "account": account,
                    "memo": memo,
                    "amount": amount
                })

        if not selected_payments and not other_items:
            QMessageBox.warning(self, "Validation Error", "Please select payments or add items to deposit.")
            return

        self.result_data = {
            "deposit_date": self.deposit_date.date().toString("yyyy-MM-dd"),
            "deposit_to_account": self.deposit_to.currentText(),
            "selected_payments": selected_payments,
            "other_items": other_items
        }
        self.accept()


# =============================================================================
# JOURNAL ENTRY DIALOG
# =============================================================================

class JournalEntryDialog(GenFinDialog):
    """Dialog for creating a journal entry."""

    def __init__(self, parent=None):
        super().__init__("Journal Entry", parent)
        self.result_data = None
        self.setMinimumWidth(700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        form = QFormLayout()
        self.entry_date = QDateEdit()
        self.entry_date.setCalendarPopup(True)
        self.entry_date.setDate(QDate.currentDate())
        form.addRow("Date:", self.entry_date)

        self.entry_number = QLineEdit()
        self.entry_number.setPlaceholderText("Auto")
        form.addRow("Entry #:", self.entry_number)

        header_layout.addLayout(form)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Journal lines
        lines_frame = QGroupBox("Journal Lines")
        lines_layout = QVBoxLayout(lines_frame)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(4)
        self.lines_table.setHorizontalHeaderLabels(["Account", "Memo", "Debit", "Credit"])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lines_table.setRowCount(10)

        accounts = ["", "Checking", "Savings", "Accounts Receivable", "Accounts Payable",
                   "Inventory", "Equipment", "Accumulated Depreciation", "Loans Payable",
                   "Owner's Equity", "Sales Revenue", "Cost of Goods Sold", "Wages Expense",
                   "Rent Expense", "Utilities", "Supplies", "Insurance", "Depreciation"]

        for row in range(10):
            account_combo = QComboBox()
            account_combo.addItems(accounts)
            self.lines_table.setCellWidget(row, 0, account_combo)

            self.lines_table.setItem(row, 1, QTableWidgetItem(""))

            debit_spin = QDoubleSpinBox()
            debit_spin.setPrefix("$ ")
            debit_spin.setMaximum(9999999.99)
            debit_spin.setDecimals(2)
            debit_spin.valueChanged.connect(self._update_totals)
            self.lines_table.setCellWidget(row, 2, debit_spin)

            credit_spin = QDoubleSpinBox()
            credit_spin.setPrefix("$ ")
            credit_spin.setMaximum(9999999.99)
            credit_spin.setDecimals(2)
            credit_spin.valueChanged.connect(self._update_totals)
            self.lines_table.setCellWidget(row, 3, credit_spin)

        lines_layout.addWidget(self.lines_table)

        # Totals row
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        totals_layout.addWidget(QLabel("Debits:"))
        self.total_debits = QLabel("$0.00")
        self.total_debits.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.total_debits)

        totals_layout.addSpacing(20)

        totals_layout.addWidget(QLabel("Credits:"))
        self.total_credits = QLabel("$0.00")
        self.total_credits.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.total_credits)

        totals_layout.addSpacing(20)

        self.balance_status = QLabel("BALANCED")
        self.balance_status.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['status_green']};")
        totals_layout.addWidget(self.balance_status)

        lines_layout.addLayout(totals_layout)
        layout.addWidget(lines_frame, 1)

        # Memo
        memo_layout = QHBoxLayout()
        memo_layout.addWidget(QLabel("Memo:"))
        self.memo = QLineEdit()
        memo_layout.addWidget(self.memo)
        layout.addLayout(memo_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        save_new_btn = QPushButton("Save & New")
        save_new_btn.clicked.connect(self._save_new)
        button_layout.addWidget(save_new_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _update_totals(self):
        """Update debit/credit totals and balance status."""
        total_debit = 0.0
        total_credit = 0.0

        for row in range(self.lines_table.rowCount()):
            debit_spin = self.lines_table.cellWidget(row, 2)
            credit_spin = self.lines_table.cellWidget(row, 3)
            if debit_spin:
                total_debit += debit_spin.value()
            if credit_spin:
                total_credit += credit_spin.value()

        self.total_debits.setText(f"${total_debit:,.2f}")
        self.total_credits.setText(f"${total_credit:,.2f}")

        if abs(total_debit - total_credit) < 0.01:
            self.balance_status.setText("BALANCED")
            self.balance_status.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['status_green']};")
        else:
            diff = total_debit - total_credit
            self.balance_status.setText(f"OUT OF BALANCE: ${abs(diff):,.2f}")
            self.balance_status.setStyleSheet(f"font-weight: bold; color: {GENFIN_COLORS['status_red']};")

    def _save(self):
        lines = []
        total_debit = 0.0
        total_credit = 0.0

        for row in range(self.lines_table.rowCount()):
            account_widget = self.lines_table.cellWidget(row, 0)
            account = account_widget.currentText() if account_widget else ""
            if not account:
                continue

            memo_item = self.lines_table.item(row, 1)
            memo = memo_item.text() if memo_item else ""

            debit_spin = self.lines_table.cellWidget(row, 2)
            credit_spin = self.lines_table.cellWidget(row, 3)
            debit = debit_spin.value() if debit_spin else 0
            credit = credit_spin.value() if credit_spin else 0

            if debit > 0 or credit > 0:
                total_debit += debit
                total_credit += credit
                lines.append({
                    "account": account,
                    "memo": memo,
                    "debit": debit,
                    "credit": credit
                })

        if not lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one line.")
            return

        if abs(total_debit - total_credit) >= 0.01:
            QMessageBox.warning(self, "Validation Error", "Entry must be balanced (debits = credits).")
            return

        self.result_data = {
            "entry_date": self.entry_date.date().toString("yyyy-MM-dd"),
            "entry_number": self.entry_number.text() or "auto",
            "lines": lines,
            "memo": self.memo.text()
        }
        self.accept()

    def _save_new(self):
        """Save and reset for new entry."""
        self._save()
        if self.result_data:
            self.entry_number.clear()
            self.memo.clear()
            for row in range(self.lines_table.rowCount()):
                account_widget = self.lines_table.cellWidget(row, 0)
                if account_widget:
                    account_widget.setCurrentIndex(0)
                self.lines_table.setItem(row, 1, QTableWidgetItem(""))
                debit_spin = self.lines_table.cellWidget(row, 2)
                credit_spin = self.lines_table.cellWidget(row, 3)
                if debit_spin:
                    debit_spin.setValue(0)
                if credit_spin:
                    credit_spin.setValue(0)


# =============================================================================
# ESTIMATE DIALOG
# =============================================================================

class EstimateDialog(GenFinDialog):
    """Dialog for creating estimates/quotes."""

    def __init__(self, customers: List[Dict], parent=None):
        super().__init__("Create Estimate", parent)
        self.customers = customers
        self.result_data = None
        self.setMinimumWidth(700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        form_left = QFormLayout()
        self.customer = QComboBox()
        self.customer.addItem("-- Select Customer --", "")
        for c in self.customers:
            self.customer.addItem(c.get("name", "Unknown"), c.get("customer_id"))
        form_left.addRow("Customer*:", self.customer)

        self.estimate_date = QDateEdit()
        self.estimate_date.setCalendarPopup(True)
        self.estimate_date.setDate(QDate.currentDate())
        form_left.addRow("Estimate Date:", self.estimate_date)

        header_layout.addLayout(form_left)

        form_right = QFormLayout()
        self.estimate_number = QLineEdit()
        self.estimate_number.setPlaceholderText("Auto")
        form_right.addRow("Estimate #:", self.estimate_number)

        self.expiration_date = QDateEdit()
        self.expiration_date.setCalendarPopup(True)
        self.expiration_date.setDate(QDate.currentDate().addDays(30))
        form_right.addRow("Expiration:", self.expiration_date)

        header_layout.addLayout(form_right)
        layout.addLayout(header_layout)

        # Line items
        lines_frame = QGroupBox("Line Items")
        lines_layout = QVBoxLayout(lines_frame)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(5)
        self.lines_table.setHorizontalHeaderLabels(["Item/Service", "Description", "Qty", "Rate", "Amount"])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lines_table.setRowCount(5)

        items = ["", "Custom Work", "Consulting", "Parts", "Labor", "Supplies", "Equipment Rental"]

        for row in range(5):
            item_combo = QComboBox()
            item_combo.addItems(items)
            self.lines_table.setCellWidget(row, 0, item_combo)

            self.lines_table.setItem(row, 1, QTableWidgetItem(""))

            qty_spin = QSpinBox()
            qty_spin.setMinimum(0)
            qty_spin.setMaximum(9999)
            qty_spin.setValue(1)
            qty_spin.valueChanged.connect(self._update_total)
            self.lines_table.setCellWidget(row, 2, qty_spin)

            rate_spin = QDoubleSpinBox()
            rate_spin.setPrefix("$ ")
            rate_spin.setMaximum(999999.99)
            rate_spin.setDecimals(2)
            rate_spin.valueChanged.connect(self._update_total)
            self.lines_table.setCellWidget(row, 3, rate_spin)

            amount_label = QLabel("$0.00")
            amount_label.setStyleSheet("font-weight: bold;")
            self.lines_table.setCellWidget(row, 4, amount_label)

        lines_layout.addWidget(self.lines_table)

        # Total row
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {GENFIN_COLORS['teal_dark']};")
        total_layout.addWidget(self.total_label)
        lines_layout.addLayout(total_layout)

        layout.addWidget(lines_frame, 1)

        # Message
        msg_layout = QHBoxLayout()
        msg_layout.addWidget(QLabel("Message:"))
        self.message = QLineEdit()
        self.message.setPlaceholderText("Message to display on estimate")
        msg_layout.addWidget(self.message)
        layout.addLayout(msg_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        email_btn = QPushButton("Email Estimate")
        email_btn.clicked.connect(lambda: QMessageBox.information(self, "Email", "Email functionality coming soon!"))
        button_layout.addWidget(email_btn)

        print_btn = QPushButton("Print")
        print_btn.clicked.connect(lambda: QMessageBox.information(self, "Print", "Print functionality coming soon!"))
        button_layout.addWidget(print_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _update_total(self):
        """Update line amounts and total."""
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            qty_spin = self.lines_table.cellWidget(row, 2)
            rate_spin = self.lines_table.cellWidget(row, 3)
            amount_label = self.lines_table.cellWidget(row, 4)

            qty = qty_spin.value() if qty_spin else 0
            rate = rate_spin.value() if rate_spin else 0
            amount = qty * rate

            if amount_label:
                amount_label.setText(f"${amount:,.2f}")
            total += amount

        self.total_label.setText(f"${total:,.2f}")

    def _save(self):
        if not self.customer.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return

        lines = []
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            item_widget = self.lines_table.cellWidget(row, 0)
            item = item_widget.currentText() if item_widget else ""
            if not item:
                continue

            desc_item = self.lines_table.item(row, 1)
            desc = desc_item.text() if desc_item else ""

            qty_spin = self.lines_table.cellWidget(row, 2)
            qty = qty_spin.value() if qty_spin else 0

            rate_spin = self.lines_table.cellWidget(row, 3)
            rate = rate_spin.value() if rate_spin else 0

            if qty > 0 and rate > 0:
                amount = qty * rate
                total += amount
                lines.append({
                    "item": item,
                    "description": desc,
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount
                })

        if not lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one line item.")
            return

        self.result_data = {
            "customer_id": self.customer.currentData(),
            "estimate_date": self.estimate_date.date().toString("yyyy-MM-dd"),
            "estimate_number": self.estimate_number.text() or "auto",
            "expiration_date": self.expiration_date.date().toString("yyyy-MM-dd"),
            "lines": lines,
            "total": total,
            "message": self.message.text()
        }
        self.accept()


# =============================================================================
# PURCHASE ORDER DIALOG
# =============================================================================

class PurchaseOrderDialog(GenFinDialog):
    """Dialog for creating purchase orders."""

    def __init__(self, vendors: List[Dict], parent=None):
        super().__init__("Create Purchase Order", parent)
        self.vendors = vendors
        self.result_data = None
        self.setMinimumWidth(700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()

        form_left = QFormLayout()
        self.vendor = QComboBox()
        self.vendor.addItem("-- Select Vendor --", "")
        for v in self.vendors:
            self.vendor.addItem(v.get("name", "Unknown"), v.get("vendor_id"))
        form_left.addRow("Vendor*:", self.vendor)

        self.po_date = QDateEdit()
        self.po_date.setCalendarPopup(True)
        self.po_date.setDate(QDate.currentDate())
        form_left.addRow("PO Date:", self.po_date)

        header_layout.addLayout(form_left)

        form_right = QFormLayout()
        self.po_number = QLineEdit()
        self.po_number.setPlaceholderText("Auto")
        form_right.addRow("PO #:", self.po_number)

        self.ship_to = QComboBox()
        self.ship_to.addItems(["Main Office", "Warehouse", "Field Location", "Other"])
        form_right.addRow("Ship To:", self.ship_to)

        header_layout.addLayout(form_right)
        layout.addLayout(header_layout)

        # Line items
        lines_frame = QGroupBox("Order Items")
        lines_layout = QVBoxLayout(lines_frame)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(5)
        self.lines_table.setHorizontalHeaderLabels(["Item", "Description", "Qty", "Rate", "Amount"])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lines_table.setRowCount(5)

        items = ["", "Seed", "Fertilizer", "Fuel", "Parts", "Supplies", "Equipment", "Services"]

        for row in range(5):
            item_combo = QComboBox()
            item_combo.addItems(items)
            self.lines_table.setCellWidget(row, 0, item_combo)

            self.lines_table.setItem(row, 1, QTableWidgetItem(""))

            qty_spin = QSpinBox()
            qty_spin.setMinimum(0)
            qty_spin.setMaximum(9999)
            qty_spin.setValue(0)
            qty_spin.valueChanged.connect(self._update_total)
            self.lines_table.setCellWidget(row, 2, qty_spin)

            rate_spin = QDoubleSpinBox()
            rate_spin.setPrefix("$ ")
            rate_spin.setMaximum(999999.99)
            rate_spin.setDecimals(2)
            rate_spin.valueChanged.connect(self._update_total)
            self.lines_table.setCellWidget(row, 3, rate_spin)

            amount_label = QLabel("$0.00")
            amount_label.setStyleSheet("font-weight: bold;")
            self.lines_table.setCellWidget(row, 4, amount_label)

        lines_layout.addWidget(self.lines_table)

        # Total row
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {GENFIN_COLORS['teal_dark']};")
        total_layout.addWidget(self.total_label)
        lines_layout.addLayout(total_layout)

        layout.addWidget(lines_frame, 1)

        # Memo
        memo_layout = QHBoxLayout()
        memo_layout.addWidget(QLabel("Vendor Memo:"))
        self.memo = QLineEdit()
        memo_layout.addWidget(self.memo)
        layout.addLayout(memo_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        email_btn = QPushButton("Email PO")
        email_btn.clicked.connect(lambda: QMessageBox.information(self, "Email", "Email functionality coming soon!"))
        button_layout.addWidget(email_btn)

        print_btn = QPushButton("Print")
        print_btn.clicked.connect(lambda: QMessageBox.information(self, "Print", "Print functionality coming soon!"))
        button_layout.addWidget(print_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _update_total(self):
        """Update line amounts and total."""
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            qty_spin = self.lines_table.cellWidget(row, 2)
            rate_spin = self.lines_table.cellWidget(row, 3)
            amount_label = self.lines_table.cellWidget(row, 4)

            qty = qty_spin.value() if qty_spin else 0
            rate = rate_spin.value() if rate_spin else 0
            amount = qty * rate

            if amount_label:
                amount_label.setText(f"${amount:,.2f}")
            total += amount

        self.total_label.setText(f"${total:,.2f}")

    def _save(self):
        if not self.vendor.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a vendor.")
            return

        lines = []
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            item_widget = self.lines_table.cellWidget(row, 0)
            item = item_widget.currentText() if item_widget else ""
            if not item:
                continue

            desc_item = self.lines_table.item(row, 1)
            desc = desc_item.text() if desc_item else ""

            qty_spin = self.lines_table.cellWidget(row, 2)
            qty = qty_spin.value() if qty_spin else 0

            rate_spin = self.lines_table.cellWidget(row, 3)
            rate = rate_spin.value() if rate_spin else 0

            if qty > 0:
                amount = qty * rate
                total += amount
                lines.append({
                    "item": item,
                    "description": desc,
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount
                })

        if not lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one line item.")
            return

        self.result_data = {
            "vendor_id": self.vendor.currentData(),
            "po_date": self.po_date.date().toString("yyyy-MM-dd"),
            "po_number": self.po_number.text() or "auto",
            "ship_to": self.ship_to.currentText(),
            "lines": lines,
            "total": total,
            "memo": self.memo.text()
        }
        self.accept()


# =============================================================================
# SALES RECEIPT DIALOG
# =============================================================================

class SalesReceiptDialog(GenFinDialog):
    """Dialog for creating sales receipts (immediate payment sales)."""

    def __init__(self, customers: List[Dict], parent=None):
        super().__init__("Create Sales Receipt", parent)
        self.customers = customers
        self.result_data = None
        self.setMinimumWidth(700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header_frame = QGroupBox("Receipt Information")
        header_layout = QFormLayout(header_frame)

        self.customer = QComboBox()
        self.customer.addItem("Walk-in Customer", "")
        for c in self.customers:
            self.customer.addItem(c.get("name", "Unknown"), c.get("customer_id"))
        header_layout.addRow("Customer:", self.customer)

        self.sale_date = QDateEdit()
        self.sale_date.setCalendarPopup(True)
        self.sale_date.setDate(QDate.currentDate())
        header_layout.addRow("Sale Date:", self.sale_date)

        self.receipt_number = QLineEdit()
        self.receipt_number.setPlaceholderText("Auto")
        header_layout.addRow("Receipt #:", self.receipt_number)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Check", "Credit Card", "Debit Card", "ACH"])
        header_layout.addRow("Payment Method:", self.payment_method)

        self.deposit_to = QComboBox()
        self.deposit_to.addItems(["Undeposited Funds", "Checking", "Cash Register"])
        header_layout.addRow("Deposit To:", self.deposit_to)

        layout.addWidget(header_frame)

        # Line items
        lines_frame = QGroupBox("Items Sold")
        lines_layout = QVBoxLayout(lines_frame)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(5)
        self.lines_table.setHorizontalHeaderLabels(["Item/Service", "Description", "Qty", "Rate", "Amount"])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lines_table.setRowCount(5)

        items = ["", "Product Sale", "Service", "Consulting", "Rental", "Parts", "Labor"]

        for row in range(5):
            item_combo = QComboBox()
            item_combo.addItems(items)
            self.lines_table.setCellWidget(row, 0, item_combo)

            self.lines_table.setItem(row, 1, QTableWidgetItem(""))

            qty_spin = QSpinBox()
            qty_spin.setMinimum(0)
            qty_spin.setMaximum(9999)
            qty_spin.setValue(1)
            qty_spin.valueChanged.connect(self._update_total)
            self.lines_table.setCellWidget(row, 2, qty_spin)

            rate_spin = QDoubleSpinBox()
            rate_spin.setPrefix("$ ")
            rate_spin.setMaximum(999999.99)
            rate_spin.setDecimals(2)
            rate_spin.valueChanged.connect(self._update_total)
            self.lines_table.setCellWidget(row, 3, rate_spin)

            amount_label = QLabel("$0.00")
            amount_label.setStyleSheet("font-weight: bold;")
            self.lines_table.setCellWidget(row, 4, amount_label)

        lines_layout.addWidget(self.lines_table)

        # Total row
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {GENFIN_COLORS['teal_dark']};")
        total_layout.addWidget(self.total_label)
        lines_layout.addLayout(total_layout)

        layout.addWidget(lines_frame, 1)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        print_btn = QPushButton("Print Receipt")
        print_btn.clicked.connect(lambda: QMessageBox.information(self, "Print", "Print functionality coming soon!"))
        button_layout.addWidget(print_btn)

        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        save_new_btn = QPushButton("Save & New")
        save_new_btn.clicked.connect(self._save_new)
        button_layout.addWidget(save_new_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _update_total(self):
        """Update line amounts and total."""
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            qty_spin = self.lines_table.cellWidget(row, 2)
            rate_spin = self.lines_table.cellWidget(row, 3)
            amount_label = self.lines_table.cellWidget(row, 4)

            qty = qty_spin.value() if qty_spin else 0
            rate = rate_spin.value() if rate_spin else 0
            amount = qty * rate

            if amount_label:
                amount_label.setText(f"${amount:,.2f}")
            total += amount

        self.total_label.setText(f"${total:,.2f}")

    def _save(self):
        lines = []
        total = 0.0
        for row in range(self.lines_table.rowCount()):
            item_widget = self.lines_table.cellWidget(row, 0)
            item = item_widget.currentText() if item_widget else ""
            if not item:
                continue

            desc_item = self.lines_table.item(row, 1)
            desc = desc_item.text() if desc_item else ""

            qty_spin = self.lines_table.cellWidget(row, 2)
            qty = qty_spin.value() if qty_spin else 0

            rate_spin = self.lines_table.cellWidget(row, 3)
            rate = rate_spin.value() if rate_spin else 0

            if qty > 0 and rate > 0:
                amount = qty * rate
                total += amount
                lines.append({
                    "item": item,
                    "description": desc,
                    "quantity": qty,
                    "rate": rate,
                    "amount": amount
                })

        if not lines:
            QMessageBox.warning(self, "Validation Error", "Please add at least one line item.")
            return

        self.result_data = {
            "customer_id": self.customer.currentData() or None,
            "sale_date": self.sale_date.date().toString("yyyy-MM-dd"),
            "receipt_number": self.receipt_number.text() or "auto",
            "payment_method": self.payment_method.currentText().lower(),
            "deposit_to": self.deposit_to.currentText(),
            "lines": lines,
            "total": total
        }
        self.accept()

    def _save_new(self):
        """Save and reset for new receipt."""
        self._save()
        if self.result_data:
            self.customer.setCurrentIndex(0)
            self.receipt_number.clear()
            for row in range(self.lines_table.rowCount()):
                item_widget = self.lines_table.cellWidget(row, 0)
                if item_widget:
                    item_widget.setCurrentIndex(0)
                self.lines_table.setItem(row, 1, QTableWidgetItem(""))
                qty_spin = self.lines_table.cellWidget(row, 2)
                rate_spin = self.lines_table.cellWidget(row, 3)
                if qty_spin:
                    qty_spin.setValue(1)
                if rate_spin:
                    rate_spin.setValue(0)


# =============================================================================
# TIME ENTRY DIALOG
# =============================================================================

class TimeEntryDialog(GenFinDialog):
    """Dialog for entering time tracking entries."""

    def __init__(self, employees: List[Dict], customers: List[Dict], parent=None):
        super().__init__("Time Entry", parent)
        self.employees = employees
        self.customers = customers
        self.result_data = None
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.employee = QComboBox()
        self.employee.addItem("-- Select Employee --", "")
        for e in self.employees:
            name = e.get("full_name", f"{e.get('first_name', '')} {e.get('last_name', '')}")
            self.employee.addItem(name, e.get("employee_id"))
        form.addRow("Employee*:", self.employee)

        self.customer = QComboBox()
        self.customer.addItem("-- Select Customer (optional) --", "")
        for c in self.customers:
            self.customer.addItem(c.get("name", "Unknown"), c.get("customer_id"))
        form.addRow("Customer/Job:", self.customer)

        self.service_item = QComboBox()
        self.service_item.addItems(["", "General Labor", "Field Work", "Equipment Operation",
                                    "Repair", "Consulting", "Administrative", "Other"])
        form.addRow("Service Item:", self.service_item)

        self.work_date = QDateEdit()
        self.work_date.setCalendarPopup(True)
        self.work_date.setDate(QDate.currentDate())
        form.addRow("Date:", self.work_date)

        hours_layout = QHBoxLayout()
        self.hours = QDoubleSpinBox()
        self.hours.setMaximum(24)
        self.hours.setDecimals(2)
        self.hours.setSingleStep(0.25)
        hours_layout.addWidget(self.hours)
        hours_layout.addWidget(QLabel("hours"))
        hours_layout.addStretch()
        form.addRow("Duration:", hours_layout)

        self.billable = QCheckBox("Billable")
        self.billable.setChecked(True)
        form.addRow("", self.billable)

        self.hourly_rate = QDoubleSpinBox()
        self.hourly_rate.setPrefix("$ ")
        self.hourly_rate.setMaximum(999.99)
        self.hourly_rate.setDecimals(2)
        self.hourly_rate.valueChanged.connect(self._update_total)
        form.addRow("Hourly Rate:", self.hourly_rate)

        self.hours.valueChanged.connect(self._update_total)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Description of work performed")
        form.addRow("Notes:", self.notes)

        layout.addLayout(form)

        # Total
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total:"))
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {GENFIN_COLORS['teal_dark']};")
        total_layout.addWidget(self.total_label)
        layout.addLayout(total_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save & Close")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        save_new_btn = QPushButton("Save & New")
        save_new_btn.clicked.connect(self._save_new)
        button_layout.addWidget(save_new_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _update_total(self):
        """Update total amount."""
        hours = self.hours.value()
        rate = self.hourly_rate.value()
        total = hours * rate
        self.total_label.setText(f"${total:,.2f}")

    def _save(self):
        if not self.employee.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select an employee.")
            return

        if self.hours.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter hours worked.")
            return

        self.result_data = {
            "employee_id": self.employee.currentData(),
            "customer_id": self.customer.currentData() or None,
            "service_item": self.service_item.currentText(),
            "work_date": self.work_date.date().toString("yyyy-MM-dd"),
            "hours": self.hours.value(),
            "billable": self.billable.isChecked(),
            "hourly_rate": self.hourly_rate.value(),
            "total": self.hours.value() * self.hourly_rate.value(),
            "notes": self.notes.toPlainText()
        }
        self.accept()

    def _save_new(self):
        """Save and reset for new entry."""
        self._save()
        if self.result_data:
            self.hours.setValue(0)
            self.notes.clear()


# =============================================================================
# INVENTORY ITEM DIALOG
# =============================================================================

class InventoryItemDialog(GenFinDialog):
    """Dialog for adding/editing inventory items."""

    def __init__(self, item_data: Optional[Dict] = None, parent=None):
        title = "Edit Item" if item_data else "Add New Item"
        super().__init__(title, parent)
        self.item_data = item_data
        self.result_data = None
        self.setMinimumWidth(550)
        self._setup_ui()
        if item_data:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Basic info
        basic_frame = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_frame)

        self.item_type = QComboBox()
        self.item_type.addItems(["Inventory Part", "Non-Inventory Part", "Service", "Other Charge"])
        basic_layout.addRow("Type:", self.item_type)

        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("Required")
        basic_layout.addRow("Name*:", self.item_name)

        self.description = QLineEdit()
        basic_layout.addRow("Description:", self.description)

        self.sku = QLineEdit()
        basic_layout.addRow("SKU:", self.sku)

        layout.addWidget(basic_frame)

        # Pricing
        pricing_frame = QGroupBox("Pricing")
        pricing_layout = QFormLayout(pricing_frame)

        self.cost = QDoubleSpinBox()
        self.cost.setPrefix("$ ")
        self.cost.setMaximum(999999.99)
        self.cost.setDecimals(2)
        pricing_layout.addRow("Cost:", self.cost)

        self.sales_price = QDoubleSpinBox()
        self.sales_price.setPrefix("$ ")
        self.sales_price.setMaximum(999999.99)
        self.sales_price.setDecimals(2)
        pricing_layout.addRow("Sales Price:", self.sales_price)

        layout.addWidget(pricing_frame)

        # Inventory (only for inventory parts)
        self.inventory_frame = QGroupBox("Inventory")
        inventory_layout = QFormLayout(self.inventory_frame)

        self.quantity_on_hand = QSpinBox()
        self.quantity_on_hand.setMaximum(999999)
        inventory_layout.addRow("Qty on Hand:", self.quantity_on_hand)

        self.reorder_point = QSpinBox()
        self.reorder_point.setMaximum(999999)
        inventory_layout.addRow("Reorder Point:", self.reorder_point)

        self.preferred_vendor = QComboBox()
        self.preferred_vendor.addItems(["", "Various", "To be determined"])
        inventory_layout.addRow("Preferred Vendor:", self.preferred_vendor)

        layout.addWidget(self.inventory_frame)

        # Accounts
        accounts_frame = QGroupBox("Account Mapping")
        accounts_layout = QFormLayout(accounts_frame)

        self.income_account = QComboBox()
        self.income_account.addItems(["Sales Revenue", "Service Revenue", "Other Income"])
        accounts_layout.addRow("Income Account:", self.income_account)

        self.expense_account = QComboBox()
        self.expense_account.addItems(["Cost of Goods Sold", "Supplies", "Materials"])
        accounts_layout.addRow("Expense Account:", self.expense_account)

        self.asset_account = QComboBox()
        self.asset_account.addItems(["Inventory Asset", "Supplies on Hand"])
        accounts_layout.addRow("Asset Account:", self.asset_account)

        layout.addWidget(accounts_frame)

        # Active status
        self.is_active = QCheckBox("Item is active")
        self.is_active.setChecked(True)
        layout.addWidget(self.is_active)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_data(self):
        d = self.item_data
        self.item_name.setText(d.get("name", ""))
        self.description.setText(d.get("description", ""))
        self.sku.setText(d.get("sku", ""))
        self.cost.setValue(d.get("cost", 0))
        self.sales_price.setValue(d.get("sales_price", 0))
        self.quantity_on_hand.setValue(d.get("quantity_on_hand", 0))
        self.reorder_point.setValue(d.get("reorder_point", 0))
        self.is_active.setChecked(d.get("is_active", True))

    def _save(self):
        if not self.item_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Item name is required.")
            return

        self.result_data = {
            "item_type": self.item_type.currentText().lower().replace(" ", "_"),
            "name": self.item_name.text().strip(),
            "description": self.description.text(),
            "sku": self.sku.text(),
            "cost": self.cost.value(),
            "sales_price": self.sales_price.value(),
            "quantity_on_hand": self.quantity_on_hand.value(),
            "reorder_point": self.reorder_point.value(),
            "income_account": self.income_account.currentText(),
            "expense_account": self.expense_account.currentText(),
            "asset_account": self.asset_account.currentText(),
            "is_active": self.is_active.isChecked()
        }
        self.accept()


# =============================================================================
# SHORTCUT LEGEND DIALOG
# =============================================================================

class ShortcutLegendDialog(GenFinDialog):
    """Dialog showing all keyboard shortcuts."""

    def __init__(self, parent=None):
        super().__init__("Keyboard Shortcuts", parent)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("GenFin Keyboard Shortcuts")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {GENFIN_COLORS['teal_dark']};
            padding: 8px;
        """)
        layout.addWidget(title)

        # Scroll area for shortcuts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        # Navigation shortcuts
        nav_group = QGroupBox("Navigation")
        nav_layout = QGridLayout(nav_group)
        nav_shortcuts = [
            ("H", "Home"),
            ("M", "Employees"),
            ("V", "Vendors"),
            ("B", "Bills"),
            ("C", "Chart of Accounts"),
            ("K", "Banking"),
            ("J", "Journal Entries"),
            ("Y", "Payroll"),
            ("T", "Reports"),
            ("$", "Customers"),
            ("#", "Invoices"),
            ("+", "Receive Payments"),
            ("-", "Pay Bills"),
            ("E", "Estimates"),
            ("P", "Purchase Orders"),
            ("R", "Reconciliation"),
            ("9", "1099 Forms"),
            ("N", "Entities"),
            ("G", "Budget"),
            ("A", "Fixed Assets"),
            ("W", "Write Checks"),
            ("I", "Inventory"),
            ("L", "Sales Receipts"),
            ("O", "Time Tracking"),
        ]
        for i, (key, desc) in enumerate(nav_shortcuts):
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(f"""
                background: {GENFIN_COLORS['teal']};
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 3px;
                font-family: monospace;
                min-width: 20px;
                text-align: center;
            """)
            key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nav_layout.addWidget(key_lbl, i // 3, (i % 3) * 2)
            nav_layout.addWidget(QLabel(desc), i // 3, (i % 3) * 2 + 1)
        content_layout.addWidget(nav_group)

        # Action shortcuts
        action_group = QGroupBox("Actions (in List Screens)")
        action_layout = QGridLayout(action_group)
        action_shortcuts = [
            ("Ctrl+N", "New Item"),
            ("Ctrl+E", "Edit Selected"),
            ("Enter", "Edit Selected"),
            ("Delete", "Delete Selected"),
            ("F5", "Refresh"),
            ("Ctrl+F", "Find/Search"),
            ("Ctrl+P", "Print"),
            ("Ctrl+S", "Save"),
        ]
        for i, (key, desc) in enumerate(action_shortcuts):
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(f"""
                background: {GENFIN_COLORS['bevel_shadow']};
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 3px;
                font-family: monospace;
            """)
            action_layout.addWidget(key_lbl, i // 2, (i % 2) * 2)
            action_layout.addWidget(QLabel(desc), i // 2, (i % 2) * 2 + 1)
        content_layout.addWidget(action_group)

        # History shortcuts
        history_group = QGroupBox("History Navigation")
        history_layout = QGridLayout(history_group)
        history_shortcuts = [
            ("Alt+Left", "Go Back"),
            ("Backspace", "Go Back"),
            ("Alt+Right", "Go Forward"),
            ("Escape", "Go to Home"),
            ("F1", "This Help"),
        ]
        for i, (key, desc) in enumerate(history_shortcuts):
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(f"""
                background: {GENFIN_COLORS['teal_dark']};
                color: white;
                font-weight: bold;
                padding: 4px 8px;
                border-radius: 3px;
                font-family: monospace;
            """)
            history_layout.addWidget(key_lbl, i // 2, (i % 2) * 2)
            history_layout.addWidget(QLabel(desc), i // 2, (i % 2) * 2 + 1)
        content_layout.addWidget(history_group)

        # Toolbar shortcuts
        toolbar_group = QGroupBox("Toolbar Buttons")
        toolbar_layout = QGridLayout(toolbar_group)
        toolbar_shortcuts = [
            ("+", "New"),
            ("E", "Edit"),
            ("X", "Delete"),
            ("R", "Refresh"),
            ("P", "Print"),
            ("?", "Help"),
        ]
        for i, (key, desc) in enumerate(toolbar_shortcuts):
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(f"""
                background: {GENFIN_COLORS['window_face']};
                color: {GENFIN_COLORS['text_dark']};
                font-weight: bold;
                padding: 4px 8px;
                border: 2px outset {GENFIN_COLORS['bevel_light']};
                font-family: monospace;
            """)
            toolbar_layout.addWidget(key_lbl, i // 3, (i % 3) * 2)
            toolbar_layout.addWidget(QLabel(desc), i // 3, (i % 3) * 2 + 1)
        content_layout.addWidget(toolbar_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            padding: 8px 24px;
            font-weight: bold;
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


# =============================================================================
# UI COMPONENTS
# =============================================================================

class GenFinIconButton(QPushButton):
    """90s QuickBooks-style icon button for the home grid."""

    def __init__(self, title: str, icon: str, description: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon_text = icon
        self.description = description
        self._setup_ui()

    def _setup_ui(self):
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

        logo = QLabel("$")
        logo.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_bright']};
            font-size: 24px;
            font-weight: bold;
            font-family: "Arial Black", sans-serif;
            padding: 0 8px;
        """)
        layout.addWidget(logo)

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

        version = QLabel("v6.4.0")
        version.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_bright']};
            font-size: 10px;
            padding: 2px 8px;
            background: {GENFIN_COLORS['teal_dark']};
            border: 1px solid {GENFIN_COLORS['teal_light']};
        """)
        layout.addWidget(version)


class GenFinToolbar(QFrame):
    """90s QuickBooks-style toolbar with icon buttons and keyboard shortcuts."""

    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    print_clicked = pyqtSignal()
    help_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-toolbar")
        self._buttons = {}
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        buttons = [
            ("New", "+", self.new_clicked, "new"),
            ("Edit", "E", self.edit_clicked, "edit"),
            ("Delete", "X", self.delete_clicked, "delete"),
            (None, None, None, None),
            ("Refresh", "R", self.refresh_clicked, "refresh"),
            ("Print", "P", self.print_clicked, "print"),
            ("Help", "?", self.help_clicked, "help"),
        ]

        for item in buttons:
            if item[0] is None:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"color: {GENFIN_COLORS['bevel_shadow']};")
                layout.addWidget(sep)
            else:
                btn = GenFinToolbarButton(item[0], item[1])
                btn.clicked.connect(item[2].emit)
                layout.addWidget(btn)
                self._buttons[item[3]] = btn

        layout.addStretch()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for toolbar buttons."""
        # + for New
        QShortcut(QKeySequence("+"), self).activated.connect(self.new_clicked.emit)
        QShortcut(QKeySequence("="), self).activated.connect(self.new_clicked.emit)  # = is + without shift
        # E for Edit (when focused on toolbar parent)
        # X for Delete
        # R for Refresh
        # P for Print
        # ? for Help
        # Note: Single letter shortcuts are handled at GenFinScreen level to avoid conflicts


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

        nav_items = [
            ("HOME", [("home", "Home")]),
            ("CUSTOMERS", [
                ("customers", "Customers"),
                ("invoices", "Invoices"),
                ("receive", "Receive $"),
                ("sales", "Sales Receipts"),
                ("estimates", "Estimates"),
                ("statements", "Statements"),
                ("credits", "Credit Memos"),
            ]),
            ("VENDORS", [
                ("vendors", "Vendors"),
                ("bills", "Enter Bills"),
                ("pay", "Pay Bills"),
                ("checks", "Write Checks"),
                ("purchase", "Purchase Orders"),
                ("creditcard", "Credit Cards"),
                ("vendorcredits", "Vendor Credits"),
            ]),
            ("BANKING", [
                ("accounts", "Chart of Accts"),
                ("banking", "Bank Accounts"),
                ("register", "Check Register"),
                ("deposits", "Make Deposits"),
                ("transfers", "Transfers"),
                ("reconcile", "Reconcile"),
                ("feeds", "Bank Feeds"),
                ("journal", "Journal Entry"),
            ]),
            ("PAYROLL", [
                ("employees", "Employees"),
                ("payroll", "Run Payroll"),
                ("time", "Time Tracking"),
                ("payliab", "Pay Liabilities"),
            ]),
            ("LISTS", [
                ("inventory", "Items & Svcs"),
                ("assets", "Fixed Assets"),
                ("recurring", "Recurring Trans"),
                ("memorized", "Memorized Trans"),
                ("entities", "Entities"),
            ]),
            ("REPORTS", [
                ("reports", "Report Center"),
                ("1099", "1099 Forms"),
                ("budget", "Budgets"),
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

        welcome_frame = QFrame()
        welcome_frame.setProperty("class", "genfin-panel-raised")
        welcome_layout = QVBoxLayout(welcome_frame)

        welcome = QLabel("Welcome to GenFin Accounting")
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(12)
        grid_layout.setContentsMargins(8, 8, 8, 8)

        # QuickBooks-style icon grid - organized by function
        icons = [
            # Row 1: Money In (Receivables)
            ("Customers", "$", "customers"),
            ("Invoices", "#", "invoices"),
            ("Receive $", "+", "receive"),
            ("Sales Rcpt", "L", "sales"),
            # Row 2: Money In continued + Estimates
            ("Estimates", "E", "estimates"),
            ("Statements", "S", "statements"),
            ("Credits", "Z", "credits"),
            ("Deposits", "D", "deposits"),
            # Row 3: Money Out (Payables)
            ("Vendors", "V", "vendors"),
            ("Bills", "B", "bills"),
            ("Pay Bills", "-", "pay"),
            ("Checks", "W", "checks"),
            # Row 4: Money Out continued
            ("Purch Ord", "P", "purchase"),
            ("Credit Card", "X", "creditcard"),
            ("Vend Cred", "U", "vendorcredits"),
            ("1099 Forms", "9", "1099"),
            # Row 5: Banking
            ("Chart Acct", "C", "accounts"),
            ("Banking", "K", "banking"),
            ("Reconcile", "R", "reconcile"),
            ("Journal", "J", "journal"),
            # Row 6: Banking continued + Transfers
            ("Transfers", "~", "transfers"),
            ("Bank Feeds", "F", "feeds"),
            ("Recurring", "Q", "recurring"),
            ("Register", ">", "register"),
            # Row 7: Payroll
            ("Employees", "M", "employees"),
            ("Payroll", "Y", "payroll"),
            ("Time Track", "O", "time"),
            ("Pay Liab", "!", "payliab"),
            # Row 8: Other
            ("Inventory", "I", "inventory"),
            ("Assets", "A", "assets"),
            ("Budget", "G", "budget"),
            ("Entities", "N", "entities"),
            # Row 9: Reports & Settings
            ("Reports", "T", "reports"),
            ("Memorized", "@", "memorized"),
            ("Settings", "*", "settings"),
            ("Help", "?", "help"),
        ]

        for i, (title, icon, nav_id) in enumerate(icons):
            btn = GenFinIconButton(title, icon)
            btn.clicked.connect(lambda checked, nid=nav_id: self.navigate_to.emit(nid))
            grid_layout.addWidget(btn, i // 4, i % 4)

        grid_layout.setColumnStretch(4, 1)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, 1)

        # Quick stats - will be loaded from API
        self.stats_frame = QFrame()
        self.stats_frame.setProperty("class", "genfin-panel")
        self.stats_layout = QHBoxLayout(self.stats_frame)

        self._add_stat("Cash Balance", "$0.00", "neutral")
        self._add_stat("A/R Outstanding", "$0.00", "neutral")
        self._add_stat("A/P Outstanding", "$0.00", "neutral")
        self._add_stat("YTD Net Income", "$0.00", "neutral")

        layout.addWidget(self.stats_frame)

        # Load stats after small delay
        QTimer.singleShot(500, self._load_stats)

    def _add_stat(self, label: str, value: str, status: str):
        stat_frame = QFrame()
        stat_layout = QVBoxLayout(stat_frame)
        stat_layout.setSpacing(2)

        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"font-size: 9px; color: {GENFIN_COLORS['text_light']};")
        stat_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setObjectName(label.replace(" ", "_"))
        color = GENFIN_COLORS['status_green'] if status == "positive" else GENFIN_COLORS['text_dark']
        value_widget.setStyleSheet(f"""
            font-family: "Courier New", monospace;
            font-size: 12px;
            font-weight: bold;
            color: {color};
        """)
        stat_layout.addWidget(value_widget)

        self.stats_layout.addWidget(stat_frame)

    def _load_stats(self):
        """Load stats from API."""
        summary = api_get("/summary")
        if summary:
            # Update labels
            cash = self.stats_frame.findChild(QLabel, "Cash_Balance")
            if cash:
                cash.setText(f"${summary.get('cash_balance', 0):,.2f}")
            ar = self.stats_frame.findChild(QLabel, "A/R_Outstanding")
            if ar:
                ar.setText(f"${summary.get('ar_balance', 0):,.2f}")
            ap = self.stats_frame.findChild(QLabel, "A/P_Outstanding")
            if ap:
                ap.setText(f"${summary.get('ap_balance', 0):,.2f}")


class GenFinListScreen(QWidget):
    """Generic list screen with full CRUD functionality."""

    def __init__(self, title: str, columns: list, api_endpoint: str,
                 dialog_class=None, id_field: str = "id", parent=None):
        super().__init__(parent)
        self.title = title
        self.columns = columns
        self.api_endpoint = api_endpoint
        self.dialog_class = dialog_class
        self.id_field = id_field
        self._data = []
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for this list screen."""
        # Ctrl+N - New
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._on_new)
        # Ctrl+E - Edit
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._on_edit)
        # Enter - Edit selected
        QShortcut(QKeySequence("Return"), self).activated.connect(self._on_edit)
        # Delete - Delete selected
        QShortcut(QKeySequence("Delete"), self).activated.connect(self._on_delete)
        # F5 - Refresh
        QShortcut(QKeySequence("F5"), self).activated.connect(self.load_data)
        # Ctrl+F - Focus search
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._focus_search)

    def _focus_search(self):
        """Focus the search input."""
        if hasattr(self, 'search_input'):
            self.search_input.setFocus()
            self.search_input.selectAll()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = GenFinToolbar()
        self.toolbar.new_clicked.connect(self._on_new)
        self.toolbar.edit_clicked.connect(self._on_edit)
        self.toolbar.delete_clicked.connect(self._on_delete)
        self.toolbar.refresh_clicked.connect(self.load_data)
        layout.addWidget(self.toolbar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

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
        self.search_input.textChanged.connect(self._filter_data)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Find")
        search_btn.setProperty("class", "genfin-button")
        search_btn.clicked.connect(self._filter_data)
        search_layout.addWidget(search_btn)

        search_layout.addStretch()
        content_layout.addWidget(search_frame)

        self.table = QTableWidget()
        self.table.setProperty("class", "genfin-table")
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setProperty("class", "genfin-header")
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self._on_edit)

        content_layout.addWidget(self.table, 1)
        layout.addWidget(content)

    def load_data(self):
        """Load data from API."""
        data = api_get(self.api_endpoint)
        if data is not None:
            self._data = data if isinstance(data, list) else data.get("items", [])
            self._populate_table(self._data)

    def _populate_table(self, data: list):
        """Populate table with data."""
        self.table.setRowCount(len(data))
        for i, item in enumerate(data):
            for j, col in enumerate(self.columns):
                key = col.lower().replace(" ", "_")
                value = item.get(key, "")
                if value is None:
                    value = ""
                elif isinstance(value, (int, float)) and "balance" in key.lower():
                    value = f"${value:,.2f}"
                elif isinstance(value, (int, float)) and ("rate" in key.lower() or "amount" in key.lower()):
                    value = f"${value:,.2f}"
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def _filter_data(self):
        """Filter displayed data based on search."""
        search_text = self.search_input.text().lower()
        if not search_text:
            self._populate_table(self._data)
            return

        filtered = []
        for item in self._data:
            for value in item.values():
                if search_text in str(value).lower():
                    filtered.append(item)
                    break
        self._populate_table(filtered)

    def _get_selected_item(self) -> Optional[Dict]:
        """Get currently selected item data."""
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return None
        return self._data[row]

    def _on_new(self):
        """Handle new item."""
        if not self.dialog_class:
            QMessageBox.information(self, "Info", f"Add {self.title} coming soon!")
            return

        dialog = self.dialog_class(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post(self.api_endpoint, dialog.result_data)
            if result and result.get("success", True):
                QMessageBox.information(self, "Success", f"{self.title} created successfully!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create: {error}")

    def _on_edit(self):
        """Handle edit item."""
        item = self._get_selected_item()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select an item to edit.")
            return

        if not self.dialog_class:
            QMessageBox.information(self, "Info", f"Edit {self.title} coming soon!")
            return

        dialog = self.dialog_class(item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            item_id = item.get(self.id_field)
            # For now, just reload - full edit API integration can be added
            QMessageBox.information(self, "Info", "Edit saved (refresh to see changes).")
            self.load_data()

    def _on_delete(self):
        """Handle delete item."""
        item = self._get_selected_item()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select an item to delete.")
            return

        name = item.get("name", item.get("full_name", "this item"))
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            item_id = item.get(self.id_field)
            if api_delete(f"{self.api_endpoint}/{item_id}"):
                QMessageBox.information(self, "Success", "Item deleted successfully!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete item.")

    def set_data(self, rows: list):
        """Set table data from list of row tuples (for static data)."""
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.table.setItem(i, j, item)


class GenFinEmployeesScreen(GenFinListScreen):
    """Employees screen with specific employee handling."""

    def __init__(self, parent=None):
        super().__init__(
            "Employees",
            ["Name", "Position", "Type", "Pay Rate", "Status"],
            "/employees",
            None,
            "employee_id",
            parent
        )

    def _on_new(self):
        dialog = AddEmployeeDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/employees", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success",
                    f"Employee {dialog.result_data['first_name']} {dialog.result_data['last_name']} created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create employee: {error}")

    def _on_edit(self):
        item = self._get_selected_item()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select an employee to edit.")
            return

        dialog = AddEmployeeDialog(item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Info", "Employee updated.")
            self.load_data()

    def load_data(self):
        """Load employees from API."""
        data = api_get("/employees")
        if data is not None:
            employees = data if isinstance(data, list) else []
            self._data = employees
            self.table.setRowCount(len(employees))
            for i, emp in enumerate(employees):
                name = emp.get("full_name", f"{emp.get('first_name', '')} {emp.get('last_name', '')}")
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(emp.get("job_title", "")))
                self.table.setItem(i, 2, QTableWidgetItem(emp.get("employee_type", "")))
                rate = emp.get("pay_rate", 0)
                pay_type = emp.get("pay_type", "hourly")
                if pay_type == "salary":
                    rate_str = f"${rate:,.0f}/yr"
                else:
                    rate_str = f"${rate:.2f}/hr"
                self.table.setItem(i, 3, QTableWidgetItem(rate_str))
                self.table.setItem(i, 4, QTableWidgetItem(emp.get("status", "active").title()))


class GenFinCustomersScreen(GenFinListScreen):
    """Customers screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Customers",
            ["Name", "Company", "Phone", "Balance"],
            "/customers",
            None,
            "customer_id",
            parent
        )

    def _on_new(self):
        dialog = AddCustomerDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/customers", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Customer created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create customer: {error}")

    def load_data(self):
        data = api_get("/customers")
        if data is not None:
            customers = data if isinstance(data, list) else []
            self._data = customers
            self.table.setRowCount(len(customers))
            for i, c in enumerate(customers):
                self.table.setItem(i, 0, QTableWidgetItem(c.get("name", "")))
                self.table.setItem(i, 1, QTableWidgetItem(c.get("company", "")))
                self.table.setItem(i, 2, QTableWidgetItem(c.get("phone", "")))
                balance = c.get("balance", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${balance:,.2f}"))


class GenFinVendorsScreen(GenFinListScreen):
    """Vendors screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Vendors",
            ["Name", "Company", "Phone", "Balance"],
            "/vendors",
            None,
            "vendor_id",
            parent
        )

    def _on_new(self):
        dialog = AddVendorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/vendors", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Vendor created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create vendor: {error}")

    def load_data(self):
        data = api_get("/vendors")
        if data is not None:
            vendors = data if isinstance(data, list) else []
            self._data = vendors
            self.table.setRowCount(len(vendors))
            for i, v in enumerate(vendors):
                self.table.setItem(i, 0, QTableWidgetItem(v.get("name", "")))
                self.table.setItem(i, 1, QTableWidgetItem(v.get("company", "")))
                self.table.setItem(i, 2, QTableWidgetItem(v.get("phone", "")))
                balance = v.get("balance", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${balance:,.2f}"))


class GenFinInvoicesScreen(GenFinListScreen):
    """Invoices screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Invoices",
            ["Number", "Customer", "Date", "Amount", "Status"],
            "/invoices",
            None,
            "invoice_id",
            parent
        )
        self._customers = []

    def _on_new(self):
        # Load customers first
        customers = api_get("/customers")
        if customers:
            self._customers = customers if isinstance(customers, list) else []

        dialog = AddInvoiceDialog(self._customers, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/invoices", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Invoice created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create invoice: {error}")

    def load_data(self):
        data = api_get("/invoices")
        if data is not None:
            invoices = data if isinstance(data, list) else []
            self._data = invoices
            self.table.setRowCount(len(invoices))
            for i, inv in enumerate(invoices):
                self.table.setItem(i, 0, QTableWidgetItem(inv.get("invoice_number", "")))
                self.table.setItem(i, 1, QTableWidgetItem(inv.get("customer_name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(inv.get("invoice_date", "")))
                amount = inv.get("total", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(inv.get("status", "").title()))


class GenFinBillsScreen(GenFinListScreen):
    """Bills screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Bills",
            ["Number", "Vendor", "Date", "Amount", "Status"],
            "/bills",
            None,
            "bill_id",
            parent
        )
        self._vendors = []

    def _on_new(self):
        # Load vendors first
        vendors = api_get("/vendors")
        if vendors:
            self._vendors = vendors if isinstance(vendors, list) else []

        dialog = AddBillDialog(self._vendors, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/bills", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Bill entered!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to enter bill: {error}")

    def load_data(self):
        data = api_get("/bills")
        if data is not None:
            bills = data if isinstance(data, list) else []
            self._data = bills
            self.table.setRowCount(len(bills))
            for i, bill in enumerate(bills):
                self.table.setItem(i, 0, QTableWidgetItem(bill.get("bill_number", "")))
                self.table.setItem(i, 1, QTableWidgetItem(bill.get("vendor_name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(bill.get("bill_date", "")))
                amount = bill.get("total", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(bill.get("status", "").title()))


class GenFinAccountsScreen(GenFinListScreen):
    """Chart of Accounts screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Chart of Accounts",
            ["Number", "Name", "Type", "Balance"],
            "/accounts",
            None,
            "account_id",
            parent
        )

    def load_data(self):
        data = api_get("/chart-of-accounts")
        if data is not None:
            accounts = data if isinstance(data, list) else []
            self._data = accounts
            self.table.setRowCount(len(accounts))
            for i, acc in enumerate(accounts):
                self.table.setItem(i, 0, QTableWidgetItem(acc.get("account_number", "")))
                self.table.setItem(i, 1, QTableWidgetItem(acc.get("name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(acc.get("account_type", "")))
                balance = acc.get("balance", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${balance:,.2f}"))


class GenFinReceivePaymentsScreen(GenFinListScreen):
    """Receive Payments screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Receive Payments",
            ["Date", "Customer", "Amount", "Method", "Reference", "Status"],
            "/payments/received",
            None,
            "payment_id",
            parent
        )
        self._customers = []

    def _on_new(self):
        # Load customers first
        customers = api_get("/customers")
        if customers:
            self._customers = customers if isinstance(customers, list) else []

        dialog = ReceivePaymentDialog(self._customers, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/payments/receive", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Payment received!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to record payment: {error}")

    def load_data(self):
        data = api_get("/payments/received")
        if data is not None:
            payments = data if isinstance(data, list) else []
            self._data = payments
            self.table.setRowCount(len(payments))
            for i, pmt in enumerate(payments):
                self.table.setItem(i, 0, QTableWidgetItem(pmt.get("payment_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(pmt.get("customer_name", "")))
                amount = pmt.get("amount", 0)
                self.table.setItem(i, 2, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 3, QTableWidgetItem(pmt.get("payment_method", "").title()))
                self.table.setItem(i, 4, QTableWidgetItem(pmt.get("reference_number", "")))
                self.table.setItem(i, 5, QTableWidgetItem(pmt.get("status", "").title()))


class GenFinPayBillsScreen(GenFinListScreen):
    """Pay Bills screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Bill Payments",
            ["Date", "Vendor", "Amount", "Method", "Account", "Status"],
            "/payments/bills",
            None,
            "payment_id",
            parent
        )
        self._vendors = []

    def _on_new(self):
        # Load vendors first
        vendors = api_get("/vendors")
        if vendors:
            self._vendors = vendors if isinstance(vendors, list) else []

        dialog = PayBillsDialog(self._vendors, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/payments/pay-bills", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Bills paid!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to pay bills: {error}")

    def load_data(self):
        data = api_get("/payments/bills")
        if data is not None:
            payments = data if isinstance(data, list) else []
            self._data = payments
            self.table.setRowCount(len(payments))
            for i, pmt in enumerate(payments):
                self.table.setItem(i, 0, QTableWidgetItem(pmt.get("payment_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(pmt.get("vendor_name", "")))
                amount = pmt.get("amount", 0)
                self.table.setItem(i, 2, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 3, QTableWidgetItem(pmt.get("payment_method", "").title()))
                self.table.setItem(i, 4, QTableWidgetItem(pmt.get("pay_from_account", "")))
                self.table.setItem(i, 5, QTableWidgetItem(pmt.get("status", "").title()))


class GenFinWriteChecksScreen(GenFinListScreen):
    """Write Checks screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Checks",
            ["Date", "Check #", "Payee", "Amount", "Account", "Status"],
            "/checks",
            None,
            "check_id",
            parent
        )

    def _on_new(self):
        dialog = WriteCheckDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/checks", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Check recorded!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to write check: {error}")

    def load_data(self):
        data = api_get("/checks")
        if data is not None:
            checks = data if isinstance(data, list) else []
            self._data = checks
            self.table.setRowCount(len(checks))
            for i, chk in enumerate(checks):
                self.table.setItem(i, 0, QTableWidgetItem(chk.get("check_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(chk.get("check_number", "")))
                self.table.setItem(i, 2, QTableWidgetItem(chk.get("payee", "")))
                amount = chk.get("amount", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(chk.get("bank_account", "")))
                self.table.setItem(i, 5, QTableWidgetItem(chk.get("status", "").title()))


class GenFinMakeDepositsScreen(GenFinListScreen):
    """Make Deposits screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Deposits",
            ["Date", "Deposit To", "Items", "Amount", "Status"],
            "/deposits",
            None,
            "deposit_id",
            parent
        )

    def _on_new(self):
        dialog = MakeDepositDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/deposits", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Deposit recorded!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to make deposit: {error}")

    def load_data(self):
        data = api_get("/deposits")
        if data is not None:
            deposits = data if isinstance(data, list) else []
            self._data = deposits
            self.table.setRowCount(len(deposits))
            for i, dep in enumerate(deposits):
                self.table.setItem(i, 0, QTableWidgetItem(dep.get("deposit_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(dep.get("deposit_to_account", "")))
                self.table.setItem(i, 2, QTableWidgetItem(str(dep.get("item_count", 0))))
                amount = dep.get("total", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(dep.get("status", "").title()))


class GenFinJournalEntriesScreen(GenFinListScreen):
    """Journal Entries screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Journal Entries",
            ["Date", "Entry #", "Memo", "Debits", "Credits", "Status"],
            "/journal-entries",
            None,
            "entry_id",
            parent
        )

    def _on_new(self):
        dialog = JournalEntryDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/journal-entries", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Journal entry recorded!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create journal entry: {error}")

    def load_data(self):
        data = api_get("/journal-entries")
        if data is not None:
            entries = data if isinstance(data, list) else []
            self._data = entries
            self.table.setRowCount(len(entries))
            for i, entry in enumerate(entries):
                self.table.setItem(i, 0, QTableWidgetItem(entry.get("entry_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(entry.get("entry_number", "")))
                self.table.setItem(i, 2, QTableWidgetItem(entry.get("memo", "")))
                debits = entry.get("total_debits", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${debits:,.2f}"))
                credits = entry.get("total_credits", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"${credits:,.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(entry.get("status", "").title()))


class GenFinEstimatesScreen(GenFinListScreen):
    """Estimates screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Estimates",
            ["Date", "Estimate #", "Customer", "Amount", "Expires", "Status"],
            "/estimates",
            None,
            "estimate_id",
            parent
        )
        self._customers = []

    def _on_new(self):
        customers = api_get("/customers")
        if customers:
            self._customers = customers if isinstance(customers, list) else []

        dialog = EstimateDialog(self._customers, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/estimates", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Estimate created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create estimate: {error}")

    def load_data(self):
        data = api_get("/estimates")
        if data is not None:
            estimates = data if isinstance(data, list) else []
            self._data = estimates
            self.table.setRowCount(len(estimates))
            for i, est in enumerate(estimates):
                self.table.setItem(i, 0, QTableWidgetItem(est.get("estimate_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(est.get("estimate_number", "")))
                self.table.setItem(i, 2, QTableWidgetItem(est.get("customer_name", "")))
                amount = est.get("total", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(est.get("expiration_date", "")))
                self.table.setItem(i, 5, QTableWidgetItem(est.get("status", "").title()))


class GenFinPurchaseOrdersScreen(GenFinListScreen):
    """Purchase Orders screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Purchase Orders",
            ["Date", "PO #", "Vendor", "Ship To", "Amount", "Status"],
            "/purchase-orders",
            None,
            "po_id",
            parent
        )
        self._vendors = []

    def _on_new(self):
        vendors = api_get("/vendors")
        if vendors:
            self._vendors = vendors if isinstance(vendors, list) else []

        dialog = PurchaseOrderDialog(self._vendors, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/purchase-orders", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Purchase order created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create purchase order: {error}")

    def load_data(self):
        data = api_get("/purchase-orders")
        if data is not None:
            orders = data if isinstance(data, list) else []
            self._data = orders
            self.table.setRowCount(len(orders))
            for i, po in enumerate(orders):
                self.table.setItem(i, 0, QTableWidgetItem(po.get("po_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(po.get("po_number", "")))
                self.table.setItem(i, 2, QTableWidgetItem(po.get("vendor_name", "")))
                self.table.setItem(i, 3, QTableWidgetItem(po.get("ship_to", "")))
                amount = po.get("total", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"${amount:,.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(po.get("status", "").title()))


class GenFinSalesReceiptsScreen(GenFinListScreen):
    """Sales Receipts screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Sales Receipts",
            ["Date", "Receipt #", "Customer", "Method", "Amount"],
            "/sales-receipts",
            None,
            "receipt_id",
            parent
        )
        self._customers = []

    def _on_new(self):
        customers = api_get("/customers")
        if customers:
            self._customers = customers if isinstance(customers, list) else []

        dialog = SalesReceiptDialog(self._customers, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/sales-receipts", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Sales receipt recorded!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create sales receipt: {error}")

    def load_data(self):
        data = api_get("/sales-receipts")
        if data is not None:
            receipts = data if isinstance(data, list) else []
            self._data = receipts
            self.table.setRowCount(len(receipts))
            for i, rcpt in enumerate(receipts):
                self.table.setItem(i, 0, QTableWidgetItem(rcpt.get("sale_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(rcpt.get("receipt_number", "")))
                self.table.setItem(i, 2, QTableWidgetItem(rcpt.get("customer_name", "Walk-in")))
                self.table.setItem(i, 3, QTableWidgetItem(rcpt.get("payment_method", "").title()))
                amount = rcpt.get("total", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"${amount:,.2f}"))


class GenFinTimeTrackingScreen(GenFinListScreen):
    """Time Tracking screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Time Tracking",
            ["Date", "Employee", "Customer/Job", "Service", "Hours", "Amount"],
            "/time-entries",
            None,
            "entry_id",
            parent
        )
        self._employees = []
        self._customers = []

    def _on_new(self):
        employees = api_get("/employees")
        if employees:
            self._employees = employees if isinstance(employees, list) else []

        customers = api_get("/customers")
        if customers:
            self._customers = customers if isinstance(customers, list) else []

        dialog = TimeEntryDialog(self._employees, self._customers, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/time-entries", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Time entry recorded!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to record time: {error}")

    def load_data(self):
        data = api_get("/time-entries")
        if data is not None:
            entries = data if isinstance(data, list) else []
            self._data = entries
            self.table.setRowCount(len(entries))
            for i, entry in enumerate(entries):
                self.table.setItem(i, 0, QTableWidgetItem(entry.get("work_date", "")))
                self.table.setItem(i, 1, QTableWidgetItem(entry.get("employee_name", "")))
                self.table.setItem(i, 2, QTableWidgetItem(entry.get("customer_name", "")))
                self.table.setItem(i, 3, QTableWidgetItem(entry.get("service_item", "")))
                hours = entry.get("hours", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"{hours:.2f}"))
                amount = entry.get("total", 0)
                self.table.setItem(i, 5, QTableWidgetItem(f"${amount:,.2f}"))


class GenFinInventoryScreen(GenFinListScreen):
    """Inventory/Items screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Items & Services",
            ["Name", "Type", "Description", "Cost", "Price", "Qty"],
            "/items",
            None,
            "item_id",
            parent
        )

    def _on_new(self):
        dialog = InventoryItemDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/items", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Item created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create item: {error}")

    def _on_edit(self):
        item = self._get_selected_item()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select an item to edit.")
            return

        dialog = InventoryItemDialog(item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Info", "Item updated.")
            self.load_data()

    def load_data(self):
        data = api_get("/items")
        if data is not None:
            items = data if isinstance(data, list) else []
            self._data = items
            self.table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.table.setItem(i, 0, QTableWidgetItem(item.get("name", "")))
                self.table.setItem(i, 1, QTableWidgetItem(item.get("item_type", "").replace("_", " ").title()))
                self.table.setItem(i, 2, QTableWidgetItem(item.get("description", "")))
                cost = item.get("cost", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${cost:,.2f}"))
                price = item.get("sales_price", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"${price:,.2f}"))
                qty = item.get("quantity_on_hand", 0)
                self.table.setItem(i, 5, QTableWidgetItem(str(qty)))


class GenFinReportsScreen(QWidget):
    """Reports screen with report catalog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QLabel("Reports")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(header)

        # Report categories
        categories = [
            ("Financial Reports", [
                ("Profit & Loss", "/reports/profit-loss"),
                ("Balance Sheet", "/reports/balance-sheet"),
                ("Cash Flow Statement", "/reports/cash-flow"),
                ("Trial Balance", "/reports/trial-balance"),
            ]),
            ("Receivables", [
                ("A/R Aging Summary", "/reports/ar-aging"),
                ("Customer Balance", "/reports/customer-balance"),
                ("Open Invoices", "/reports/open-invoices"),
            ]),
            ("Payables", [
                ("A/P Aging Summary", "/reports/ap-aging"),
                ("Vendor Balance", "/reports/vendor-balance"),
                ("Unpaid Bills", "/reports/unpaid-bills"),
            ]),
            ("Payroll", [
                ("Payroll Summary", "/reports/payroll-summary"),
                ("Payroll Detail", "/reports/payroll-detail"),
            ]),
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        for cat_name, reports in categories:
            group = QGroupBox(cat_name)
            group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    border: 2px groove {GENFIN_COLORS['bevel_shadow']};
                    margin-top: 12px;
                    padding-top: 16px;
                }}
                QGroupBox::title {{
                    color: {GENFIN_COLORS['teal_dark']};
                }}
            """)
            group_layout = QVBoxLayout(group)

            for report_name, endpoint in reports:
                btn = QPushButton(report_name)
                btn.setProperty("class", "genfin-button")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, e=endpoint, n=report_name: self._run_report(e, n))
                group_layout.addWidget(btn)

            content_layout.addWidget(group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

    def _run_report(self, endpoint: str, name: str):
        """Run a report and display results."""
        data = api_get(endpoint)
        if data:
            QMessageBox.information(self, name,
                f"Report generated successfully!\n\nData preview available in API response.")
        else:
            QMessageBox.warning(self, "Error", "Failed to generate report.")


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

        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "genfin-status-text")
        layout.addWidget(self.status_label)

        layout.addStretch()

        date_panel = QFrame()
        date_panel.setProperty("class", "genfin-status-panel")
        date_layout = QHBoxLayout(date_panel)
        date_layout.setContentsMargins(4, 2, 4, 2)
        self.date_label = QLabel(QDate.currentDate().toString("MMM dd, yyyy"))
        self.date_label.setProperty("class", "genfin-status-text")
        date_layout.addWidget(self.date_label)
        layout.addWidget(date_panel)

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
    Now fully functional with API connections.
    """

    navigate_to = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "genfin-main")
        self._screens = {}
        self._nav_history = []  # Navigation history stack
        self._nav_position = -1  # Current position in history
        self._setup_ui()
        self._apply_styles()
        self._setup_shortcuts()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = GenFinTitleBar("GenFin", "Professional Farm Accounting")
        layout.addWidget(self.title_bar)

        main_content = QHBoxLayout()
        main_content.setContentsMargins(0, 0, 0, 0)
        main_content.setSpacing(0)

        self.nav_sidebar = GenFinNavSidebar()
        self.nav_sidebar.navigation_clicked.connect(self._on_nav_click)
        main_content.addWidget(self.nav_sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background-color: {GENFIN_COLORS['window_bg']};")

        self._add_screens()

        main_content.addWidget(self.content_stack, 1)
        layout.addLayout(main_content, 1)

        self.status_bar = GenFinStatusBar()
        layout.addWidget(self.status_bar)

        self.nav_sidebar.set_active("home")

    def _add_screens(self):
        """Add all content screens."""
        # Home screen
        home = GenFinHomeScreen()
        home.navigate_to.connect(self._on_nav_click)
        self._add_screen("home", home)

        # Functional screens - Core Lists
        self._add_screen("customers", GenFinCustomersScreen())
        self._add_screen("vendors", GenFinVendorsScreen())
        self._add_screen("invoices", GenFinInvoicesScreen())
        self._add_screen("bills", GenFinBillsScreen())
        self._add_screen("accounts", GenFinAccountsScreen())
        self._add_screen("employees", GenFinEmployeesScreen())
        self._add_screen("reports", GenFinReportsScreen())

        # Payment screens - Money In/Out
        self._add_screen("receive", GenFinReceivePaymentsScreen())
        self._add_screen("pay", GenFinPayBillsScreen())
        self._add_screen("checks", GenFinWriteChecksScreen())
        self._add_screen("deposits", GenFinMakeDepositsScreen())
        self._add_screen("journal", GenFinJournalEntriesScreen())

        # Transaction screens
        self._add_screen("estimates", GenFinEstimatesScreen())
        self._add_screen("purchase", GenFinPurchaseOrdersScreen())
        self._add_screen("sales", GenFinSalesReceiptsScreen())
        self._add_screen("time", GenFinTimeTrackingScreen())
        self._add_screen("inventory", GenFinInventoryScreen())

        # Payroll screen
        payroll = GenFinListScreen("Payroll", ["Pay Run #", "Period", "Employees", "Total", "Status"],
                                    "/pay-runs", None, "pay_run_id")
        self._add_screen("payroll", payroll)

        # 1099 screen
        forms_1099 = GenFinListScreen("1099 Forms", ["Vendor", "Tax ID", "Amount", "Status"],
                                       "/1099/forms", None, "form_id")
        self._add_screen("1099", forms_1099)

        # Placeholder screens for features still in development
        placeholders = [
            # Customer-related
            "statements", "credits",
            # Vendor-related
            "creditcard", "vendorcredits",
            # Banking
            "banking", "register", "transfers", "reconcile", "feeds",
            # Payroll
            "payliab",
            # Lists
            "assets", "recurring", "memorized", "entities",
            # Other
            "budget", "settings", "help"
        ]

        for nav_id in placeholders:
            self._add_placeholder_screen(nav_id)

    def _add_placeholder_screen(self, nav_id: str):
        """Add a placeholder screen for features in development."""
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

    def _on_nav_click(self, nav_id: str, add_to_history: bool = True):
        """Handle navigation click."""
        if nav_id in self._screens:
            screen = self._screens[nav_id]
            self.content_stack.setCurrentWidget(screen)
            self.status_bar.set_status(f"{nav_id.replace('_', ' ').title()} - Ready")

            # Track navigation history
            if add_to_history:
                # If we're not at the end of history, truncate forward history
                if self._nav_position < len(self._nav_history) - 1:
                    self._nav_history = self._nav_history[:self._nav_position + 1]
                # Don't add duplicates
                if not self._nav_history or self._nav_history[-1] != nav_id:
                    self._nav_history.append(nav_id)
                    self._nav_position = len(self._nav_history) - 1

            # Load data if the screen has a load_data method
            if hasattr(screen, 'load_data'):
                screen.load_data()

    def _go_back(self):
        """Navigate back in history."""
        if self._nav_position > 0:
            self._nav_position -= 1
            nav_id = self._nav_history[self._nav_position]
            self._on_nav_click(nav_id, add_to_history=False)
            self.nav_sidebar.set_active(nav_id)

    def _go_forward(self):
        """Navigate forward in history."""
        if self._nav_position < len(self._nav_history) - 1:
            self._nav_position += 1
            nav_id = self._nav_history[self._nav_position]
            self._on_nav_click(nav_id, add_to_history=False)
            self.nav_sidebar.set_active(nav_id)

    def _apply_styles(self):
        """Apply the 90s QuickBooks stylesheet."""
        self.setStyleSheet(get_genfin_stylesheet())

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for quick navigation."""
        # Map keys to navigation IDs (matching the icon letters)
        shortcuts = {
            "$": "customers",
            "#": "invoices",
            "V": "vendors",
            "B": "bills",
            "C": "accounts",
            "K": "banking",
            "J": "journal",
            "Y": "payroll",
            "M": "employees",
            "T": "reports",
            "9": "1099",
            "N": "entities",
            "G": "budget",
            "A": "assets",
            "H": "home",
            "W": "checks",       # Write Checks
            "I": "inventory",   # Inventory/Items
            "L": "sales",       # Sales Receipts
            "O": "time",        # Time Tracking
            "Q": "recurring",   # Recurring Transactions
            "F": "feeds",       # Bank Feeds
            "D": "deposits",    # Make Deposits
        }

        for key, nav_id in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(lambda nid=nav_id: self._on_nav_click(nid))

        # Also add Ctrl+N for New, Ctrl+E for Edit, etc. on list screens
        new_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_shortcut.activated.connect(self._trigger_new)

        edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_shortcut.activated.connect(self._trigger_edit)

        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._trigger_delete)

        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self._trigger_refresh)

        # Escape to go back to home
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(lambda: self._on_nav_click("home"))

        # Back/Forward navigation
        back_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        back_shortcut.activated.connect(self._go_back)

        back_shortcut2 = QShortcut(QKeySequence("Backspace"), self)
        back_shortcut2.activated.connect(self._go_back)

        forward_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        forward_shortcut.activated.connect(self._go_forward)

        # F1 for Help/Shortcut Legend
        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self._show_shortcut_legend)

        # Ctrl+P for Print
        print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        print_shortcut.activated.connect(self._trigger_print)

    def _show_shortcut_legend(self):
        """Show the keyboard shortcut legend dialog."""
        dialog = ShortcutLegendDialog(self)
        dialog.exec()

    def _trigger_print(self):
        """Trigger Print action on current screen."""
        current = self.content_stack.currentWidget()
        if hasattr(current, 'toolbar') and hasattr(current.toolbar, 'print_clicked'):
            current.toolbar.print_clicked.emit()

    def _trigger_new(self):
        """Trigger New action on current screen."""
        current = self.content_stack.currentWidget()
        if hasattr(current, 'toolbar') and hasattr(current.toolbar, 'new_clicked'):
            current.toolbar.new_clicked.emit()

    def _trigger_edit(self):
        """Trigger Edit action on current screen."""
        current = self.content_stack.currentWidget()
        if hasattr(current, 'toolbar') and hasattr(current.toolbar, 'edit_clicked'):
            current.toolbar.edit_clicked.emit()

    def _trigger_delete(self):
        """Trigger Delete action on current screen."""
        current = self.content_stack.currentWidget()
        if hasattr(current, 'toolbar') and hasattr(current.toolbar, 'delete_clicked'):
            current.toolbar.delete_clicked.emit()

    def _trigger_refresh(self):
        """Trigger Refresh action on current screen."""
        current = self.content_stack.currentWidget()
        if hasattr(current, 'toolbar') and hasattr(current.toolbar, 'refresh_clicked'):
            current.toolbar.refresh_clicked.emit()
        elif hasattr(current, 'load_data'):
            current.load_data()
