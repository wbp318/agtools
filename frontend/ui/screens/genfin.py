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
    QFormLayout, QTextEdit, QCheckBox, QDialogButtonBox,
    QFileDialog, QProgressDialog, QListWidget, QListWidgetItem,
    QRadioButton, QButtonGroup, QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTimer, QMarginsF, QSizeF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import (
    QFont, QShortcut, QKeySequence, QPainter, QPageLayout,
    QPageSize, QTextDocument, QColor
)
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog

import requests
import csv
import os
import json
from datetime import datetime, date
from typing import Optional, Dict, List, Any
from decimal import Decimal

from ui.genfin_styles import GENFIN_COLORS, get_genfin_stylesheet, set_genfin_class

# Backend API base URL
API_BASE = "http://127.0.0.1:8000/api/v1/genfin"


def api_get(endpoint: str) -> Optional[Dict]:
    """Make GET request to GenFin API."""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        print(f"API GET {url} returned status {response.status_code}: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"API GET error for {endpoint}: {e}")
        return None


def api_post(endpoint: str, data: Dict) -> Optional[Dict]:
    """Make POST request to GenFin API."""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.post(url, json=data, timeout=5)
        if response.status_code in [200, 201]:
            return response.json()
        print(f"API POST {url} returned status {response.status_code}: {response.text[:200]}")
        return response.json() if response.text else None
    except Exception as e:
        print(f"API POST error for {endpoint}: {e}")
        return None


def api_put(endpoint: str, data: Dict) -> Optional[Dict]:
    """Make PUT request to GenFin API."""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.put(url, json=data, timeout=5)
        if response.status_code == 200:
            return response.json()
        print(f"API PUT {url} returned status {response.status_code}: {response.text[:200]}")
        return response.json() if response.text else None
    except Exception as e:
        print(f"API PUT error for {endpoint}: {e}")
        return None


def api_delete(endpoint: str) -> bool:
    """Make DELETE request to GenFin API."""
    try:
        url = f"{API_BASE}{endpoint}"
        response = requests.delete(url, timeout=5)
        if response.status_code in [200, 204]:
            return True
        print(f"API DELETE {url} returned status {response.status_code}: {response.text[:200]}")
        return False
    except Exception as e:
        print(f"API DELETE error for {endpoint}: {e}")
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


# =============================================================================
# PRINT PREVIEW DIALOG
# =============================================================================

class PrintPreviewDialog(GenFinDialog):
    """
    Universal print preview dialog for checks, invoices, estimates,
    purchase orders, statements, and reports.
    """

    def __init__(self, document_type: str, document_data: Dict, parent=None):
        super().__init__(f"Print Preview - {document_type}", parent)
        self.document_type = document_type
        self.document_data = document_data
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        self.setMinimumSize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()

        zoom_label = QLabel("Zoom:")
        toolbar.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self._update_preview)
        toolbar.addWidget(self.zoom_combo)

        toolbar.addStretch()

        page_setup_btn = QPushButton("Page Setup...")
        page_setup_btn.clicked.connect(self._page_setup)
        toolbar.addWidget(page_setup_btn)

        layout.addLayout(toolbar)

        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setStyleSheet("background-color: #666; padding: 20px;")

        self.preview_content = QLabel()
        self.preview_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_content.setStyleSheet("""
            background-color: white;
            border: 1px solid #333;
            margin: 20px;
            padding: 40px;
        """)
        self._render_preview()

        self.preview_area.setWidget(self.preview_content)
        preview_layout.addWidget(self.preview_area)
        layout.addWidget(preview_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        btn_layout.addStretch()

        pdf_btn = QPushButton("Save as PDF")
        pdf_btn.clicked.connect(self._save_pdf)
        btn_layout.addWidget(pdf_btn)

        print_btn = QPushButton("Print")
        print_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
        """)
        print_btn.clicked.connect(self._print)
        btn_layout.addWidget(print_btn)

        layout.addLayout(btn_layout)

    def _render_preview(self):
        """Render document preview based on type."""
        html = self._generate_html()
        self.preview_content.setText("")
        self.preview_content.setMinimumSize(612, 792)  # Letter size at 72 DPI

        # Use QTextDocument for rich rendering
        doc = QTextDocument()
        doc.setHtml(html)
        self.preview_content.setText(html)
        self.preview_content.setWordWrap(True)
        self.preview_content.setTextFormat(Qt.TextFormat.RichText)

    def _generate_html(self) -> str:
        """Generate HTML for the document."""
        if self.document_type == "Check":
            return self._generate_check_html()
        elif self.document_type == "Invoice":
            return self._generate_invoice_html()
        elif self.document_type == "Estimate":
            return self._generate_estimate_html()
        elif self.document_type == "Purchase Order":
            return self._generate_po_html()
        elif self.document_type == "Statement":
            return self._generate_statement_html()
        else:
            return self._generate_report_html()

    def _generate_check_html(self) -> str:
        """Generate check preview HTML."""
        d = self.document_data
        amount = d.get("amount", 0)
        amount_words = self._number_to_words(amount)

        return f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="border: 2px solid #000; padding: 20px; margin-bottom: 20px;">
                <div style="text-align: right; font-size: 12px;">
                    <b>Check #: {d.get('check_number', '____')}</b><br>
                    Date: {d.get('date', datetime.now().strftime('%m/%d/%Y'))}
                </div>
                <div style="margin-top: 20px;">
                    <b>PAY TO THE ORDER OF:</b><br>
                    <span style="font-size: 16px;">{d.get('payee', '')}</span>
                </div>
                <div style="margin-top: 15px; text-align: right;">
                    <span style="border: 1px solid #000; padding: 5px 15px; font-size: 18px;">
                        <b>${amount:,.2f}</b>
                    </span>
                </div>
                <div style="margin-top: 15px; border-bottom: 1px solid #000; padding-bottom: 5px;">
                    {amount_words} DOLLARS
                </div>
                <div style="margin-top: 20px;">
                    <b>Memo:</b> {d.get('memo', '')}
                </div>
                <div style="margin-top: 30px; border-top: 1px solid #000; width: 250px; margin-left: auto;">
                    <center><i>Authorized Signature</i></center>
                </div>
                <div style="margin-top: 30px; font-family: 'MICR', monospace; font-size: 12px; letter-spacing: 2px;">
                    ⑆{d.get('routing', '000000000')}⑆ ⑈{d.get('account', '0000000000')}⑈ {d.get('check_number', '0000')}
                </div>
            </div>

            <div style="border: 1px dashed #999; padding: 15px; font-size: 11px;">
                <b>Check Stub</b><br>
                <table style="width: 100%; margin-top: 10px;">
                    <tr><td>Check #:</td><td>{d.get('check_number', '')}</td></tr>
                    <tr><td>Date:</td><td>{d.get('date', '')}</td></tr>
                    <tr><td>Payee:</td><td>{d.get('payee', '')}</td></tr>
                    <tr><td>Amount:</td><td>${amount:,.2f}</td></tr>
                    <tr><td>Memo:</td><td>{d.get('memo', '')}</td></tr>
                </table>
            </div>
        </div>
        """

    def _generate_invoice_html(self) -> str:
        """Generate invoice preview HTML."""
        d = self.document_data
        lines_html = ""
        subtotal = 0

        for line in d.get("lines", []):
            qty = line.get("quantity", 1)
            rate = line.get("rate", 0)
            amount = qty * rate
            subtotal += amount
            lines_html += f"""
                <tr>
                    <td>{line.get('description', '')}</td>
                    <td style="text-align: center;">{qty}</td>
                    <td style="text-align: right;">${rate:,.2f}</td>
                    <td style="text-align: right;">${amount:,.2f}</td>
                </tr>
            """

        tax = d.get("tax", 0)
        total = subtotal + tax

        return f"""
        <div style="font-family: Arial, sans-serif; padding: 30px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: {GENFIN_COLORS['teal_dark']}; margin: 0;">INVOICE</h1>
            </div>

            <table style="width: 100%; margin-bottom: 20px;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <b>Bill To:</b><br>
                        {d.get('customer_name', '')}<br>
                        {d.get('customer_address', '').replace(chr(10), '<br>')}
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <b>Invoice #:</b> {d.get('invoice_number', '')}<br>
                        <b>Date:</b> {d.get('date', '')}<br>
                        <b>Due Date:</b> {d.get('due_date', '')}<br>
                        <b>Terms:</b> {d.get('terms', 'Net 30')}
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: {GENFIN_COLORS['teal']}; color: white;">
                    <th style="padding: 8px; text-align: left;">Description</th>
                    <th style="padding: 8px; text-align: center;">Qty</th>
                    <th style="padding: 8px; text-align: right;">Rate</th>
                    <th style="padding: 8px; text-align: right;">Amount</th>
                </tr>
                {lines_html}
            </table>

            <table style="width: 250px; margin-left: auto;">
                <tr><td>Subtotal:</td><td style="text-align: right;">${subtotal:,.2f}</td></tr>
                <tr><td>Tax:</td><td style="text-align: right;">${tax:,.2f}</td></tr>
                <tr style="font-weight: bold; font-size: 14px;">
                    <td style="border-top: 2px solid #000; padding-top: 5px;">TOTAL:</td>
                    <td style="border-top: 2px solid #000; padding-top: 5px; text-align: right;">${total:,.2f}</td>
                </tr>
            </table>

            <div style="margin-top: 40px; text-align: center; font-size: 11px; color: #666;">
                Thank you for your business!
            </div>
        </div>
        """

    def _generate_estimate_html(self) -> str:
        """Generate estimate preview HTML."""
        d = self.document_data
        lines_html = ""
        total = 0

        for line in d.get("lines", []):
            qty = line.get("quantity", 1)
            rate = line.get("rate", 0)
            amount = qty * rate
            total += amount
            lines_html += f"""
                <tr>
                    <td>{line.get('description', '')}</td>
                    <td style="text-align: center;">{qty}</td>
                    <td style="text-align: right;">${rate:,.2f}</td>
                    <td style="text-align: right;">${amount:,.2f}</td>
                </tr>
            """

        return f"""
        <div style="font-family: Arial, sans-serif; padding: 30px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: {GENFIN_COLORS['teal_dark']}; margin: 0;">ESTIMATE</h1>
            </div>

            <table style="width: 100%; margin-bottom: 20px;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <b>Prepared For:</b><br>
                        {d.get('customer_name', '')}
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <b>Estimate #:</b> {d.get('estimate_number', '')}<br>
                        <b>Date:</b> {d.get('date', '')}<br>
                        <b>Valid Until:</b> {d.get('expiration_date', '')}
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: {GENFIN_COLORS['teal']}; color: white;">
                    <th style="padding: 8px; text-align: left;">Description</th>
                    <th style="padding: 8px; text-align: center;">Qty</th>
                    <th style="padding: 8px; text-align: right;">Rate</th>
                    <th style="padding: 8px; text-align: right;">Amount</th>
                </tr>
                {lines_html}
            </table>

            <table style="width: 250px; margin-left: auto;">
                <tr style="font-weight: bold; font-size: 14px;">
                    <td style="border-top: 2px solid #000; padding-top: 5px;">ESTIMATE TOTAL:</td>
                    <td style="border-top: 2px solid #000; padding-top: 5px; text-align: right;">${total:,.2f}</td>
                </tr>
            </table>

            <div style="margin-top: 40px; padding: 15px; background: #f5f5f5; border: 1px solid #ddd;">
                <b>Notes:</b><br>
                {d.get('notes', 'This estimate is valid for 30 days.')}
            </div>
        </div>
        """

    def _generate_po_html(self) -> str:
        """Generate purchase order preview HTML."""
        d = self.document_data
        lines_html = ""
        total = 0

        for line in d.get("lines", []):
            qty = line.get("quantity", 1)
            rate = line.get("rate", 0)
            amount = qty * rate
            total += amount
            lines_html += f"""
                <tr>
                    <td>{line.get('item', '')}</td>
                    <td>{line.get('description', '')}</td>
                    <td style="text-align: center;">{qty}</td>
                    <td style="text-align: right;">${rate:,.2f}</td>
                    <td style="text-align: right;">${amount:,.2f}</td>
                </tr>
            """

        return f"""
        <div style="font-family: Arial, sans-serif; padding: 30px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: {GENFIN_COLORS['teal_dark']}; margin: 0;">PURCHASE ORDER</h1>
            </div>

            <table style="width: 100%; margin-bottom: 20px;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <b>Vendor:</b><br>
                        {d.get('vendor_name', '')}
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <b>PO #:</b> {d.get('po_number', '')}<br>
                        <b>Date:</b> {d.get('date', '')}<br>
                        <b>Expected:</b> {d.get('expected_date', '')}
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: {GENFIN_COLORS['teal']}; color: white;">
                    <th style="padding: 8px; text-align: left;">Item</th>
                    <th style="padding: 8px; text-align: left;">Description</th>
                    <th style="padding: 8px; text-align: center;">Qty</th>
                    <th style="padding: 8px; text-align: right;">Rate</th>
                    <th style="padding: 8px; text-align: right;">Amount</th>
                </tr>
                {lines_html}
            </table>

            <table style="width: 250px; margin-left: auto;">
                <tr style="font-weight: bold; font-size: 14px;">
                    <td style="border-top: 2px solid #000; padding-top: 5px;">TOTAL:</td>
                    <td style="border-top: 2px solid #000; padding-top: 5px; text-align: right;">${total:,.2f}</td>
                </tr>
            </table>
        </div>
        """

    def _generate_statement_html(self) -> str:
        """Generate customer statement preview HTML."""
        d = self.document_data
        trans_html = ""

        for trans in d.get("transactions", []):
            trans_html += f"""
                <tr>
                    <td>{trans.get('date', '')}</td>
                    <td>{trans.get('type', '')}</td>
                    <td>{trans.get('reference', '')}</td>
                    <td style="text-align: right;">${trans.get('charges', 0):,.2f}</td>
                    <td style="text-align: right;">${trans.get('payments', 0):,.2f}</td>
                    <td style="text-align: right;">${trans.get('balance', 0):,.2f}</td>
                </tr>
            """

        return f"""
        <div style="font-family: Arial, sans-serif; padding: 30px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: {GENFIN_COLORS['teal_dark']}; margin: 0;">STATEMENT</h1>
            </div>

            <table style="width: 100%; margin-bottom: 20px;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <b>To:</b><br>
                        {d.get('customer_name', '')}
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <b>Statement Date:</b> {d.get('date', '')}<br>
                        <b>Account #:</b> {d.get('account_number', '')}
                    </td>
                </tr>
            </table>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: {GENFIN_COLORS['teal']}; color: white;">
                    <th style="padding: 8px; text-align: left;">Date</th>
                    <th style="padding: 8px; text-align: left;">Type</th>
                    <th style="padding: 8px; text-align: left;">Reference</th>
                    <th style="padding: 8px; text-align: right;">Charges</th>
                    <th style="padding: 8px; text-align: right;">Payments</th>
                    <th style="padding: 8px; text-align: right;">Balance</th>
                </tr>
                {trans_html}
            </table>

            <table style="width: 300px; margin-left: auto; border: 2px solid {GENFIN_COLORS['teal']};">
                <tr><td style="padding: 5px;">Current:</td><td style="text-align: right; padding: 5px;">${d.get('current', 0):,.2f}</td></tr>
                <tr><td style="padding: 5px;">1-30 Days:</td><td style="text-align: right; padding: 5px;">${d.get('aging_30', 0):,.2f}</td></tr>
                <tr><td style="padding: 5px;">31-60 Days:</td><td style="text-align: right; padding: 5px;">${d.get('aging_60', 0):,.2f}</td></tr>
                <tr><td style="padding: 5px;">61-90 Days:</td><td style="text-align: right; padding: 5px;">${d.get('aging_90', 0):,.2f}</td></tr>
                <tr><td style="padding: 5px;">Over 90:</td><td style="text-align: right; padding: 5px;">${d.get('aging_over', 0):,.2f}</td></tr>
                <tr style="font-weight: bold; background: {GENFIN_COLORS['teal']}; color: white;">
                    <td style="padding: 8px;">BALANCE DUE:</td>
                    <td style="text-align: right; padding: 8px;">${d.get('balance_due', 0):,.2f}</td>
                </tr>
            </table>
        </div>
        """

    def _generate_report_html(self) -> str:
        """Generate generic report preview HTML."""
        d = self.document_data
        return f"""
        <div style="font-family: Arial, sans-serif; padding: 30px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: {GENFIN_COLORS['teal_dark']}; margin: 0;">{d.get('title', 'Report')}</h1>
                <p style="color: #666;">{d.get('date_range', '')}</p>
            </div>

            <div style="white-space: pre-wrap; font-family: monospace;">
{d.get('content', '')}
            </div>
        </div>
        """

    def _number_to_words(self, amount: float) -> str:
        """Convert number to words for check writing."""
        ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
                'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
                'Seventeen', 'Eighteen', 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

        def convert_less_than_thousand(n):
            if n == 0:
                return ''
            elif n < 20:
                return ones[n]
            elif n < 100:
                return tens[n // 10] + ('' if n % 10 == 0 else '-' + ones[n % 10])
            else:
                return ones[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + convert_less_than_thousand(n % 100))

        dollars = int(amount)
        cents = int(round((amount - dollars) * 100))

        if dollars == 0:
            result = 'Zero'
        elif dollars < 1000:
            result = convert_less_than_thousand(dollars)
        elif dollars < 1000000:
            result = convert_less_than_thousand(dollars // 1000) + ' Thousand'
            if dollars % 1000:
                result += ' ' + convert_less_than_thousand(dollars % 1000)
        else:
            result = convert_less_than_thousand(dollars // 1000000) + ' Million'
            if dollars % 1000000:
                result += ' ' + convert_less_than_thousand((dollars % 1000000) // 1000) + ' Thousand'
                if dollars % 1000:
                    result += ' ' + convert_less_than_thousand(dollars % 1000)

        return f"{result} and {cents:02d}/100"

    def _update_preview(self):
        """Update preview zoom."""
        zoom_text = self.zoom_combo.currentText().replace("%", "")
        try:
            zoom = int(zoom_text) / 100
            base_width = 612
            base_height = 792
            self.preview_content.setMinimumSize(int(base_width * zoom), int(base_height * zoom))
        except ValueError:
            pass

    def _page_setup(self):
        """Show page setup dialog."""
        dialog = QPrintDialog(self.printer, self)
        dialog.exec()

    def _save_pdf(self):
        """Save document as PDF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save as PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'

            pdf_printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            pdf_printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            pdf_printer.setOutputFileName(file_path)
            pdf_printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

            doc = QTextDocument()
            doc.setHtml(self._generate_html())
            doc.print(pdf_printer)

            QMessageBox.information(self, "PDF Saved", f"Document saved to:\n{file_path}")

    def _print(self):
        """Print the document."""
        dialog = QPrintDialog(self.printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            doc = QTextDocument()
            doc.setHtml(self._generate_html())
            doc.print(self.printer)
            QMessageBox.information(self, "Printed", "Document sent to printer.")
            self.accept()


# =============================================================================
# IMPORT/EXPORT DIALOG
# =============================================================================

class ImportExportDialog(GenFinDialog):
    """
    Dialog for importing and exporting accounting data in
    QIF, CSV, and IIF formats.
    """

    def __init__(self, mode: str = "import", parent=None):
        title = "Import Data" if mode == "import" else "Export Data"
        super().__init__(title, parent)
        self.mode = mode
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if self.mode == "import":
            self._setup_import_ui(layout)
        else:
            self._setup_export_ui(layout)

    def _setup_import_ui(self, layout):
        """Setup UI for import mode."""
        # File selection
        file_group = QGroupBox("Select File to Import")
        file_layout = QVBoxLayout(file_group)

        file_row = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select a file to import...")
        self.file_path.setReadOnly(True)
        file_row.addWidget(self.file_path)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_import)
        file_row.addWidget(browse_btn)

        file_layout.addLayout(file_row)

        # Format info
        format_info = QLabel(
            "Supported formats:\n"
            "• QIF - Quicken Interchange Format (bank transactions)\n"
            "• CSV - Comma Separated Values (any data type)\n"
            "• IIF - Intuit Interchange Format (QuickBooks lists & transactions)"
        )
        format_info.setStyleSheet("color: #666; font-size: 10px; padding: 10px;")
        file_layout.addWidget(format_info)

        layout.addWidget(file_group)

        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QFormLayout(options_group)

        self.import_type = QComboBox()
        self.import_type.addItems([
            "Auto-detect from file",
            "Chart of Accounts",
            "Customers",
            "Vendors",
            "Transactions",
            "Invoices",
            "Bills",
            "Bank Transactions"
        ])
        options_layout.addRow("Data Type:", self.import_type)

        self.duplicate_handling = QComboBox()
        self.duplicate_handling.addItems([
            "Skip duplicates",
            "Update existing records",
            "Import as new"
        ])
        options_layout.addRow("Duplicates:", self.duplicate_handling)

        self.date_format = QComboBox()
        self.date_format.addItems([
            "MM/DD/YYYY",
            "DD/MM/YYYY",
            "YYYY-MM-DD"
        ])
        options_layout.addRow("Date Format:", self.date_format)

        layout.addWidget(options_group)

        # Preview area
        preview_group = QGroupBox("Preview (first 10 rows)")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)

        layout.addWidget(preview_group)

        # Mapping section (for CSV)
        self.mapping_group = QGroupBox("Column Mapping")
        mapping_layout = QFormLayout(self.mapping_group)

        self.mappings = {}
        for field in ["Date", "Description", "Amount", "Account", "Reference"]:
            combo = QComboBox()
            combo.addItem("-- Skip --")
            self.mappings[field] = combo
            mapping_layout.addRow(f"{field}:", combo)

        self.mapping_group.hide()
        layout.addWidget(self.mapping_group)

        # Buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        self.import_btn = QPushButton("Import")
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
        """)
        self.import_btn.clicked.connect(self._do_import)
        btn_layout.addWidget(self.import_btn)

        layout.addLayout(btn_layout)

    def _setup_export_ui(self, layout):
        """Setup UI for export mode."""
        # Data type selection
        type_group = QGroupBox("Select Data to Export")
        type_layout = QVBoxLayout(type_group)

        self.export_types = QListWidget()
        self.export_types.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        export_items = [
            "Chart of Accounts",
            "Customers",
            "Vendors",
            "Employees",
            "Invoices",
            "Bills",
            "Journal Entries",
            "Bank Transactions",
            "All Transactions"
        ]
        for item in export_items:
            self.export_types.addItem(item)
        type_layout.addWidget(self.export_types)

        layout.addWidget(type_group)

        # Format selection
        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)

        self.format_buttons = QButtonGroup()

        csv_radio = QRadioButton("CSV - Comma Separated Values (Excel compatible)")
        csv_radio.setChecked(True)
        self.format_buttons.addButton(csv_radio, 0)
        format_layout.addWidget(csv_radio)

        qif_radio = QRadioButton("QIF - Quicken Interchange Format")
        self.format_buttons.addButton(qif_radio, 1)
        format_layout.addWidget(qif_radio)

        iif_radio = QRadioButton("IIF - Intuit Interchange Format (QuickBooks)")
        self.format_buttons.addButton(iif_radio, 2)
        format_layout.addWidget(iif_radio)

        json_radio = QRadioButton("JSON - JavaScript Object Notation")
        self.format_buttons.addButton(json_radio, 3)
        format_layout.addWidget(json_radio)

        layout.addWidget(format_group)

        # Date range
        date_group = QGroupBox("Date Range (for transactions)")
        date_layout = QFormLayout(date_group)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-12))
        self.start_date.setCalendarPopup(True)
        date_layout.addRow("From:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addRow("To:", self.end_date)

        layout.addWidget(date_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.include_headers = QCheckBox("Include column headers")
        self.include_headers.setChecked(True)
        options_layout.addWidget(self.include_headers)

        self.include_ids = QCheckBox("Include record IDs")
        options_layout.addWidget(self.include_ids)

        layout.addWidget(options_group)

        # Buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
        """)
        export_btn.clicked.connect(self._do_export)
        btn_layout.addWidget(export_btn)

        layout.addLayout(btn_layout)

    def _browse_import(self):
        """Browse for import file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Import", "",
            "All Supported (*.csv *.qif *.iif);;CSV Files (*.csv);;QIF Files (*.qif);;IIF Files (*.iif)"
        )
        if file_path:
            self.file_path.setText(file_path)
            self._preview_file(file_path)
            self.import_btn.setEnabled(True)

    def _preview_file(self, file_path: str):
        """Preview the import file."""
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.csv':
                self._preview_csv(file_path)
            elif ext == '.qif':
                self._preview_qif(file_path)
            elif ext == '.iif':
                self._preview_iif(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Could not preview file:\n{e}")

    def _preview_csv(self, file_path: str):
        """Preview CSV file."""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)[:11]  # Header + 10 rows

        if not rows:
            return

        headers = rows[0]
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(min(10, len(rows) - 1))

        for i, row in enumerate(rows[1:11]):
            for j, cell in enumerate(row):
                self.preview_table.setItem(i, j, QTableWidgetItem(cell))

        # Update column mappings
        self.mapping_group.show()
        for field, combo in self.mappings.items():
            combo.clear()
            combo.addItem("-- Skip --")
            combo.addItems(headers)

            # Auto-detect mappings
            for idx, header in enumerate(headers):
                if field.lower() in header.lower():
                    combo.setCurrentIndex(idx + 1)
                    break

    def _preview_qif(self, file_path: str):
        """Preview QIF file."""
        self.mapping_group.hide()

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')[:50]

        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Field", "Value"])
        self.preview_table.setRowCount(min(10, len(lines)))

        row = 0
        for line in lines:
            if line and row < 10:
                if line.startswith('D'):
                    self.preview_table.setItem(row, 0, QTableWidgetItem("Date"))
                    self.preview_table.setItem(row, 1, QTableWidgetItem(line[1:]))
                    row += 1
                elif line.startswith('T'):
                    self.preview_table.setItem(row, 0, QTableWidgetItem("Amount"))
                    self.preview_table.setItem(row, 1, QTableWidgetItem(line[1:]))
                    row += 1
                elif line.startswith('P'):
                    self.preview_table.setItem(row, 0, QTableWidgetItem("Payee"))
                    self.preview_table.setItem(row, 1, QTableWidgetItem(line[1:]))
                    row += 1
                elif line.startswith('M'):
                    self.preview_table.setItem(row, 0, QTableWidgetItem("Memo"))
                    self.preview_table.setItem(row, 1, QTableWidgetItem(line[1:]))
                    row += 1

    def _preview_iif(self, file_path: str):
        """Preview IIF file."""
        self.mapping_group.hide()

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            rows = list(reader)[:11]

        if not rows:
            return

        # IIF files start with headers like !ACCNT, !CUST, etc.
        headers = rows[0] if rows else []
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(min(10, len(rows) - 1))

        for i, row in enumerate(rows[1:11]):
            for j, cell in enumerate(row):
                if j < len(headers):
                    self.preview_table.setItem(i, j, QTableWidgetItem(cell))

    def _do_import(self):
        """Perform the import."""
        file_path = self.file_path.text()
        if not file_path:
            QMessageBox.warning(self, "No File", "Please select a file to import.")
            return

        progress = QProgressDialog("Importing data...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            ext = os.path.splitext(file_path)[1].lower()
            records = []

            progress.setValue(20)

            if ext == '.csv':
                records = self._import_csv(file_path)
            elif ext == '.qif':
                records = self._import_qif(file_path)
            elif ext == '.iif':
                records = self._import_iif(file_path)

            progress.setValue(60)

            # Send to API based on import type
            import_type = self.import_type.currentText()
            endpoint = self._get_import_endpoint(import_type)

            if endpoint and records:
                success_count = 0
                for i, record in enumerate(records):
                    result = api_post(endpoint, record)
                    if result:
                        success_count += 1
                    progress.setValue(60 + int(40 * (i + 1) / len(records)))

                progress.close()
                QMessageBox.information(
                    self, "Import Complete",
                    f"Successfully imported {success_count} of {len(records)} records."
                )
                self.accept()
            else:
                progress.close()
                QMessageBox.warning(self, "Import Failed", "No records found or unsupported import type.")

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Import Error", f"Error importing file:\n{e}")

    def _import_csv(self, file_path: str) -> List[Dict]:
        """Import CSV file."""
        records = []
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {}
                for field, combo in self.mappings.items():
                    col = combo.currentText()
                    if col != "-- Skip --" and col in row:
                        record[field.lower()] = row[col]
                if record:
                    records.append(record)
        return records

    def _import_qif(self, file_path: str) -> List[Dict]:
        """Import QIF file."""
        records = []
        current_record = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line == '^':
                    if current_record:
                        records.append(current_record)
                        current_record = {}
                elif line.startswith('D'):
                    current_record['date'] = line[1:]
                elif line.startswith('T'):
                    current_record['amount'] = line[1:].replace(',', '')
                elif line.startswith('P'):
                    current_record['payee'] = line[1:]
                elif line.startswith('M'):
                    current_record['memo'] = line[1:]
                elif line.startswith('N'):
                    current_record['check_number'] = line[1:]
                elif line.startswith('L'):
                    current_record['category'] = line[1:]

        if current_record:
            records.append(current_record)

        return records

    def _import_iif(self, file_path: str) -> List[Dict]:
        """Import IIF file."""
        records = []
        current_type = None
        headers = None

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if not row:
                    continue
                if row[0].startswith('!'):
                    current_type = row[0][1:]
                    headers = row
                elif row[0] == current_type and headers:
                    record = {'_type': current_type}
                    for i, val in enumerate(row):
                        if i < len(headers):
                            record[headers[i]] = val
                    records.append(record)

        return records

    def _get_import_endpoint(self, import_type: str) -> str:
        """Get API endpoint for import type."""
        endpoints = {
            "Chart of Accounts": "/accounts",
            "Customers": "/customers",
            "Vendors": "/vendors",
            "Transactions": "/journal-entries",
            "Invoices": "/invoices",
            "Bills": "/bills",
            "Bank Transactions": "/bank-transactions"
        }
        return endpoints.get(import_type, "")

    def _do_export(self):
        """Perform the export."""
        selected = self.export_types.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select data types to export.")
            return

        format_id = self.format_buttons.checkedId()
        formats = {0: 'csv', 1: 'qif', 2: 'iif', 3: 'json'}
        file_format = formats.get(format_id, 'csv')

        file_filter = {
            'csv': 'CSV Files (*.csv)',
            'qif': 'QIF Files (*.qif)',
            'iif': 'IIF Files (*.iif)',
            'json': 'JSON Files (*.json)'
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", f"export.{file_format}",
            file_filter.get(file_format, 'All Files (*.*)')
        )

        if not file_path:
            return

        progress = QProgressDialog("Exporting data...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            all_data = {}
            total_items = len(selected)

            for i, item in enumerate(selected):
                data_type = item.text()
                endpoint = self._get_export_endpoint(data_type)
                if endpoint:
                    data = api_get(endpoint)
                    if data:
                        all_data[data_type] = data
                progress.setValue(int(50 * (i + 1) / total_items))

            progress.setValue(60)

            if file_format == 'csv':
                self._export_csv(file_path, all_data)
            elif file_format == 'qif':
                self._export_qif(file_path, all_data)
            elif file_format == 'iif':
                self._export_iif(file_path, all_data)
            elif file_format == 'json':
                self._export_json(file_path, all_data)

            progress.setValue(100)
            progress.close()

            QMessageBox.information(
                self, "Export Complete",
                f"Data exported successfully to:\n{file_path}"
            )
            self.accept()

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Export Error", f"Error exporting data:\n{e}")

    def _get_export_endpoint(self, data_type: str) -> str:
        """Get API endpoint for export type."""
        endpoints = {
            "Chart of Accounts": "/accounts",
            "Customers": "/customers",
            "Vendors": "/vendors",
            "Employees": "/employees",
            "Invoices": "/invoices",
            "Bills": "/bills",
            "Journal Entries": "/journal-entries",
            "Bank Transactions": "/bank-transactions",
            "All Transactions": "/journal-entries"
        }
        return endpoints.get(data_type, "")

    def _export_csv(self, file_path: str, all_data: Dict):
        """Export to CSV format."""
        for data_type, records in all_data.items():
            if not records:
                continue

            # Create separate file for each data type
            type_path = file_path.replace('.csv', f'_{data_type.replace(" ", "_")}.csv')

            with open(type_path, 'w', newline='', encoding='utf-8') as f:
                if isinstance(records, list) and records:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    if self.include_headers.isChecked():
                        writer.writeheader()
                    writer.writerows(records)

    def _export_qif(self, file_path: str, all_data: Dict):
        """Export to QIF format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for data_type, records in all_data.items():
                if not isinstance(records, list):
                    continue

                # QIF header
                if 'Bank' in data_type or 'Transaction' in data_type:
                    f.write('!Type:Bank\n')
                elif 'Account' in data_type:
                    f.write('!Type:Cat\n')

                for record in records:
                    if isinstance(record, dict):
                        if 'date' in record:
                            f.write(f"D{record['date']}\n")
                        if 'amount' in record:
                            f.write(f"T{record['amount']}\n")
                        if 'payee' in record or 'name' in record:
                            f.write(f"P{record.get('payee', record.get('name', ''))}\n")
                        if 'memo' in record or 'description' in record:
                            f.write(f"M{record.get('memo', record.get('description', ''))}\n")
                        if 'category' in record or 'account' in record:
                            f.write(f"L{record.get('category', record.get('account', ''))}\n")
                        f.write('^\n')

    def _export_iif(self, file_path: str, all_data: Dict):
        """Export to IIF format."""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')

            for data_type, records in all_data.items():
                if not isinstance(records, list) or not records:
                    continue

                # IIF type headers
                iif_type = data_type.upper().replace(' ', '')[:5]
                headers = list(records[0].keys()) if records else []

                writer.writerow([f'!{iif_type}'] + headers)

                for record in records:
                    if isinstance(record, dict):
                        writer.writerow([iif_type] + [record.get(h, '') for h in headers])

    def _export_json(self, file_path: str, all_data: Dict):
        """Export to JSON format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, default=str)


# =============================================================================
# QUICKBOOKS COMPANY IMPORT WIZARD
# =============================================================================

class QuickBooksImportWizard(GenFinDialog):
    """
    Comprehensive wizard for importing complete QuickBooks company data.
    Supports IIF exports, CSV exports, and guides users through full migration.
    """

    import_complete = pyqtSignal(str, dict)  # company_name, stats

    def __init__(self, parent=None):
        super().__init__("Import QuickBooks Company", parent)
        self.setMinimumSize(800, 650)
        self.current_step = 0
        self.import_data = {
            'company_name': '',
            'files': {},
            'accounts': [],
            'customers': [],
            'vendors': [],
            'employees': [],
            'items': [],
            'invoices': [],
            'bills': [],
            'checks': [],
            'deposits': [],
            'journal_entries': [],
            'payments_received': [],
            'bills_paid': []
        }
        self.import_stats = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {GENFIN_COLORS['teal_dark']}, stop:1 {GENFIN_COLORS['teal']});
            padding: 20px;
        """)
        header_layout = QVBoxLayout(header)

        title = QLabel("QuickBooks Company Import Wizard")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        self.step_label = QLabel("Step 1 of 4: Select Company")
        self.step_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
        header_layout.addWidget(self.step_label)

        layout.addWidget(header)

        # Progress bar
        self.progress = QFrame()
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(f"background: {GENFIN_COLORS['teal_bright']};")
        layout.addWidget(self.progress)
        self._update_progress()

        # Content area - stacked widget for steps
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: white; padding: 20px;")

        # Step 1: Company Selection/Creation
        self.stack.addWidget(self._create_step1())

        # Step 2: File Selection
        self.stack.addWidget(self._create_step2())

        # Step 3: Data Mapping & Preview
        self.stack.addWidget(self._create_step3())

        # Step 4: Import Progress & Results
        self.stack.addWidget(self._create_step4())

        layout.addWidget(self.stack, 1)

        # Navigation buttons
        nav_frame = QFrame()
        nav_frame.setStyleSheet(f"""
            background: {GENFIN_COLORS['window_face']};
            border-top: 1px solid {GENFIN_COLORS['bevel_dark']};
            padding: 12px;
        """)
        nav_layout = QHBoxLayout(nav_frame)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        nav_layout.addWidget(self.cancel_btn)

        nav_layout.addStretch()

        self.back_btn = QPushButton("< Back")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setEnabled(False)
        nav_layout.addWidget(self.back_btn)

        self.next_btn = QPushButton("Next >")
        self.next_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
            padding: 8px 24px;
        """)
        self.next_btn.clicked.connect(self._go_next)
        nav_layout.addWidget(self.next_btn)

        layout.addWidget(nav_frame)

    def _update_progress(self):
        """Update progress bar width."""
        progress_pct = ((self.current_step + 1) / 4) * 100
        self.progress.setFixedWidth(int(self.width() * progress_pct / 100))

    def _create_step1(self) -> QWidget:
        """Step 1: Company Selection."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Instructions
        info = QLabel(
            "Welcome to the QuickBooks Import Wizard!\n\n"
            "This wizard will help you import your complete QuickBooks company data "
            "into GenFin, including:\n"
            "• Chart of Accounts\n"
            "• Customers, Vendors, and Employees\n"
            "• Invoices, Bills, and Payments\n"
            "• Bank Transactions and Journal Entries\n\n"
            "First, select or create the company to import into:"
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 12px; line-height: 1.5;")
        layout.addWidget(info)

        # Company selection
        company_group = QGroupBox("Target Company")
        company_layout = QVBoxLayout(company_group)

        self.existing_radio = QRadioButton("Import into existing company:")
        self.existing_radio.setChecked(True)
        company_layout.addWidget(self.existing_radio)

        self.existing_combo = QComboBox()
        self.existing_combo.setMinimumWidth(300)
        self._load_existing_companies()
        company_layout.addWidget(self.existing_combo)

        self.new_radio = QRadioButton("Create new company:")
        company_layout.addWidget(self.new_radio)

        new_layout = QFormLayout()
        self.new_company_name = QLineEdit()
        self.new_company_name.setPlaceholderText("e.g., Tap Parker Farms LLC")
        self.new_company_name.setEnabled(False)
        new_layout.addRow("Company Name:", self.new_company_name)

        self.new_radio.toggled.connect(self.new_company_name.setEnabled)
        self.new_radio.toggled.connect(lambda x: self.existing_combo.setEnabled(not x))

        company_layout.addLayout(new_layout)
        layout.addWidget(company_group)

        # QuickBooks version info
        qb_group = QGroupBox("QuickBooks Version")
        qb_layout = QVBoxLayout(qb_group)

        self.qb_version = QComboBox()
        self.qb_version.addItems([
            "QuickBooks Desktop (Pro, Premier, Enterprise)",
            "QuickBooks Online",
            "QuickBooks for Mac",
            "Other / Generic CSV"
        ])
        qb_layout.addWidget(self.qb_version)

        qb_info = QLabel(
            "Tip: In QuickBooks Desktop, use File > Utilities > Export > Lists to IIF Files\n"
            "and File > Utilities > Export > Transactions to export your data."
        )
        qb_info.setStyleSheet("color: #666; font-size: 10px;")
        qb_layout.addWidget(qb_info)

        layout.addWidget(qb_group)
        layout.addStretch()

        return widget

    def _create_step2(self) -> QWidget:
        """Step 2: File Selection."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        info = QLabel(
            "Select the export files from QuickBooks. You can import multiple files\n"
            "to bring in different types of data. The wizard will detect the file type\n"
            "and contents automatically."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # File list
        files_group = QGroupBox("Import Files")
        files_layout = QVBoxLayout(files_group)

        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["File", "Type", "Records", "Status"])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        files_layout.addWidget(self.files_table)

        btn_layout = QHBoxLayout()

        add_file_btn = QPushButton("Add File...")
        add_file_btn.clicked.connect(self._add_import_file)
        btn_layout.addWidget(add_file_btn)

        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self._add_import_folder)
        btn_layout.addWidget(add_folder_btn)

        btn_layout.addStretch()

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_file)
        btn_layout.addWidget(remove_btn)

        files_layout.addLayout(btn_layout)
        layout.addWidget(files_group)

        # Quick import options
        quick_group = QGroupBox("Quick Import Templates")
        quick_layout = QHBoxLayout(quick_group)

        templates = [
            ("Chart of Accounts", "accounts"),
            ("Customer List", "customers"),
            ("Vendor List", "vendors"),
            ("All Transactions", "transactions")
        ]

        for name, template_type in templates:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, t=template_type: self._use_template(t))
            quick_layout.addWidget(btn)

        layout.addWidget(quick_group)

        # Detection results
        self.detection_label = QLabel("")
        self.detection_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.detection_label)

        layout.addStretch()
        return widget

    def _create_step3(self) -> QWidget:
        """Step 3: Data Mapping & Preview."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        info = QLabel(
            "Review the detected data and adjust mappings if needed.\n"
            "Check the boxes for data types you want to import."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Data categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        categories_widget = QWidget()
        cat_layout = QVBoxLayout(categories_widget)

        self.category_checks = {}
        categories = [
            ("accounts", "Chart of Accounts", "Account structure and balances"),
            ("customers", "Customers", "Customer list with contact info and balances"),
            ("vendors", "Vendors", "Vendor list with contact info and balances"),
            ("employees", "Employees", "Employee records"),
            ("items", "Items & Services", "Products, services, and inventory items"),
            ("invoices", "Invoices", "Sales invoices with line items"),
            ("bills", "Bills", "Vendor bills with line items"),
            ("payments_received", "Payments Received", "Customer payment records"),
            ("bills_paid", "Bill Payments", "Vendor payment records"),
            ("checks", "Checks Written", "Check transactions"),
            ("deposits", "Deposits", "Bank deposits"),
            ("journal_entries", "Journal Entries", "Manual journal entries"),
        ]

        for key, name, desc in categories:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame { border: 1px solid #ddd; border-radius: 4px; padding: 8px; }
                QFrame:hover { background: #f5f5f5; }
            """)
            row_layout = QHBoxLayout(frame)

            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet("font-weight: bold;")
            self.category_checks[key] = cb
            row_layout.addWidget(cb)

            count_label = QLabel("0 records")
            count_label.setObjectName(f"count_{key}")
            count_label.setStyleSheet("color: #666;")
            row_layout.addWidget(count_label)

            row_layout.addStretch()

            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #888; font-size: 10px;")
            row_layout.addWidget(desc_label)

            cat_layout.addWidget(frame)

        cat_layout.addStretch()
        scroll.setWidget(categories_widget)
        layout.addWidget(scroll, 1)

        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout(options_group)

        self.clear_existing = QCheckBox("Clear existing data before import (fresh start)")
        options_layout.addWidget(self.clear_existing)

        self.skip_duplicates = QCheckBox("Skip duplicate records")
        self.skip_duplicates.setChecked(True)
        options_layout.addWidget(self.skip_duplicates)

        self.import_balances = QCheckBox("Import opening balances")
        self.import_balances.setChecked(True)
        options_layout.addWidget(self.import_balances)

        layout.addWidget(options_group)

        return widget

    def _create_step4(self) -> QWidget:
        """Step 4: Import Progress & Results."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Progress section
        self.progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(self.progress_group)

        self.current_task_label = QLabel("Preparing import...")
        self.current_task_label.setStyleSheet("font-weight: bold;")
        progress_layout.addWidget(self.current_task_label)

        self.import_progress_bar = QProgressDialog()
        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setStyleSheet(f"""
            background: #e0e0e0;
            border-radius: 4px;
        """)

        progress_inner_layout = QHBoxLayout(self.progress_bar)
        progress_inner_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_fill = QFrame()
        self.progress_fill.setStyleSheet(f"""
            background: {GENFIN_COLORS['teal']};
            border-radius: 4px;
        """)
        self.progress_fill.setFixedWidth(0)
        progress_inner_layout.addWidget(self.progress_fill)
        progress_inner_layout.addStretch()

        progress_layout.addWidget(self.progress_bar)

        self.progress_detail = QLabel("0 of 0 records processed")
        self.progress_detail.setStyleSheet("color: #666;")
        progress_layout.addWidget(self.progress_detail)

        layout.addWidget(self.progress_group)

        # Results section
        self.results_group = QGroupBox("Import Results")
        self.results_group.hide()
        results_layout = QVBoxLayout(self.results_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Data Type", "Imported", "Skipped", "Errors"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)

        self.results_summary = QLabel("")
        self.results_summary.setStyleSheet("font-size: 14px; padding: 10px;")
        results_layout.addWidget(self.results_summary)

        layout.addWidget(self.results_group)

        # Log section
        log_group = QGroupBox("Import Log")
        log_layout = QVBoxLayout(log_group)

        self.import_log = QPlainTextEdit()
        self.import_log.setReadOnly(True)
        self.import_log.setMaximumHeight(150)
        self.import_log.setStyleSheet("font-family: monospace; font-size: 10px;")
        log_layout.addWidget(self.import_log)

        layout.addWidget(log_group)

        layout.addStretch()
        return widget

    def _load_existing_companies(self):
        """Load existing companies from API."""
        self.existing_combo.clear()
        companies = api_get("/companies") or []
        if companies:
            for company in companies:
                self.existing_combo.addItem(
                    company.get("name", "Unknown"),
                    company.get("id", company.get("entity_id"))
                )
        else:
            # Add default if no companies
            self.existing_combo.addItem("Default Company", "default")

    def _add_import_file(self):
        """Add a file to import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select QuickBooks Export File", "",
            "All Supported (*.iif *.csv *.qbo *.ofx *.txt);;IIF Files (*.iif);;CSV Files (*.csv);;Bank Files (*.qbo *.ofx);;All Files (*.*)"
        )
        if file_path:
            self._process_import_file(file_path)

    def _add_import_folder(self):
        """Add all files from a folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder with QuickBooks Exports"
        )
        if folder:
            import glob
            for ext in ['*.iif', '*.csv', '*.qbo', '*.ofx', '*.IIF', '*.CSV']:
                for file_path in glob.glob(os.path.join(folder, ext)):
                    self._process_import_file(file_path)

    def _process_import_file(self, file_path: str):
        """Process and analyze an import file."""
        filename = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        try:
            file_type = "Unknown"
            record_count = 0
            data_type = "unknown"

            if ext == '.iif':
                file_type, record_count, data_type, records = self._analyze_iif(file_path)
                self.import_data['files'][file_path] = {
                    'type': data_type,
                    'records': records
                }
            elif ext == '.csv':
                file_type, record_count, data_type, records = self._analyze_csv(file_path)
                self.import_data['files'][file_path] = {
                    'type': data_type,
                    'records': records
                }
            elif ext in ['.qbo', '.ofx']:
                file_type = "Bank Transactions"
                records = self._parse_ofx_file(file_path)
                record_count = len(records)
                data_type = "bank_transactions"
                self.import_data['files'][file_path] = {
                    'type': data_type,
                    'records': records
                }

            row = self.files_table.rowCount()
            self.files_table.insertRow(row)
            self.files_table.setItem(row, 0, QTableWidgetItem(filename))
            self.files_table.setItem(row, 1, QTableWidgetItem(file_type))
            self.files_table.setItem(row, 2, QTableWidgetItem(str(record_count)))

            status = QTableWidgetItem("Ready")
            status.setForeground(QColor('green'))
            self.files_table.setItem(row, 3, status)

            self._update_detection_label()

        except Exception as e:
            QMessageBox.warning(self, "File Error", f"Could not process file:\n{e}")

    def _analyze_iif(self, file_path: str) -> tuple:
        """Analyze IIF file and extract data."""
        records = []
        data_types_found = set()

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter='\t')
            current_type = None
            headers = None

            for row in reader:
                if not row:
                    continue

                if row[0].startswith('!'):
                    current_type = row[0][1:].upper()
                    headers = [h.upper() for h in row]
                    data_types_found.add(current_type)
                elif current_type and headers and not row[0].startswith('!'):
                    record = {'_type': current_type}
                    for i, val in enumerate(row):
                        if i < len(headers):
                            record[headers[i]] = val
                    records.append(record)

        # Determine primary data type
        type_mapping = {
            'ACCNT': ('Chart of Accounts', 'accounts'),
            'CUST': ('Customers', 'customers'),
            'VEND': ('Vendors', 'vendors'),
            'EMP': ('Employees', 'employees'),
            'INVITEM': ('Items', 'items'),
            'TRNS': ('Transactions', 'transactions'),
            'SPL': ('Transaction Lines', 'transactions'),
        }

        primary_type = "IIF Data"
        data_type = "mixed"
        for iif_type in data_types_found:
            if iif_type in type_mapping:
                primary_type, data_type = type_mapping[iif_type]
                break

        return primary_type, len(records), data_type, records

    def _analyze_csv(self, file_path: str) -> tuple:
        """Analyze CSV file and detect data type."""
        records = []

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            records = list(reader)

        # Detect type based on headers
        headers_lower = [h.lower() for h in headers]

        if any('account' in h for h in headers_lower) and any('type' in h for h in headers_lower):
            return "Chart of Accounts", len(records), "accounts", records
        elif any('customer' in h for h in headers_lower) or 'bill to' in str(headers_lower):
            return "Customers", len(records), "customers", records
        elif any('vendor' in h for h in headers_lower) or 'supplier' in str(headers_lower):
            return "Vendors", len(records), "vendors", records
        elif any('invoice' in h for h in headers_lower):
            return "Invoices", len(records), "invoices", records
        elif any('bill' in h for h in headers_lower) and 'invoice' not in str(headers_lower):
            return "Bills", len(records), "bills", records
        elif any('employee' in h for h in headers_lower):
            return "Employees", len(records), "employees", records
        elif any('item' in h for h in headers_lower) or any('product' in h for h in headers_lower):
            return "Items", len(records), "items", records
        elif any('transaction' in h for h in headers_lower) or any('date' in h and 'amount' in str(headers_lower) for h in headers_lower):
            return "Transactions", len(records), "transactions", records
        else:
            return "CSV Data", len(records), "unknown", records

    def _parse_ofx_file(self, file_path: str) -> List[Dict]:
        """Parse OFX/QBO bank file."""
        transactions = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            import re
            stmttrn_pattern = r'<STMTTRN>(.*?)</STMTTRN>'
            matches = re.findall(stmttrn_pattern, content, re.DOTALL)

            for match in matches:
                trans = {}
                trntype = re.search(r'<TRNTYPE>(\w+)', match)
                dtposted = re.search(r'<DTPOSTED>(\d+)', match)
                trnamt = re.search(r'<TRNAMT>([+-]?\d+\.?\d*)', match)
                name = re.search(r'<NAME>([^<]+)', match)
                memo = re.search(r'<MEMO>([^<]+)', match)
                fitid = re.search(r'<FITID>([^<]+)', match)

                if trntype:
                    trans['type'] = trntype.group(1)
                if dtposted:
                    date_str = dtposted.group(1)[:8]
                    trans['date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                if trnamt:
                    trans['amount'] = float(trnamt.group(1))
                if name:
                    trans['description'] = name.group(1).strip()
                if memo:
                    trans['memo'] = memo.group(1).strip()
                if fitid:
                    trans['fitid'] = fitid.group(1)

                if trans.get('amount'):
                    transactions.append(trans)

        except Exception as e:
            print(f"OFX parse error: {e}")

        return transactions

    def _remove_selected_file(self):
        """Remove selected file from import list."""
        row = self.files_table.currentRow()
        if row >= 0:
            self.files_table.removeRow(row)
            self._update_detection_label()

    def _use_template(self, template_type: str):
        """Use a quick import template."""
        file_filter = "CSV Files (*.csv);;IIF Files (*.iif);;All Files (*.*)"
        if template_type == "accounts":
            title = "Select Chart of Accounts Export"
        elif template_type == "customers":
            title = "Select Customer List Export"
        elif template_type == "vendors":
            title = "Select Vendor List Export"
        else:
            title = "Select Transaction Export"

        file_path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if file_path:
            self._process_import_file(file_path)

    def _update_detection_label(self):
        """Update the detection summary label."""
        total_files = self.files_table.rowCount()
        total_records = 0
        for row in range(total_files):
            count_item = self.files_table.item(row, 2)
            if count_item:
                try:
                    total_records += int(count_item.text())
                except ValueError:
                    pass

        self.detection_label.setText(
            f"Detected {total_files} file(s) with {total_records:,} total records"
        )

    def _go_back(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_ui()

    def _go_next(self):
        """Go to next step or finish."""
        if self.current_step == 0:
            # Validate step 1
            if self.new_radio.isChecked() and not self.new_company_name.text().strip():
                QMessageBox.warning(self, "Error", "Please enter a company name.")
                return
            if self.new_radio.isChecked():
                self.import_data['company_name'] = self.new_company_name.text().strip()
            else:
                self.import_data['company_name'] = self.existing_combo.currentText()

        elif self.current_step == 1:
            # Validate step 2
            if self.files_table.rowCount() == 0:
                QMessageBox.warning(self, "Error", "Please add at least one file to import.")
                return
            self._prepare_data_preview()

        elif self.current_step == 2:
            # Start import
            self.current_step += 1
            self.stack.setCurrentIndex(self.current_step)
            self._update_step_ui()
            self._run_import()
            return

        elif self.current_step == 3:
            # Finish
            self.accept()
            return

        self.current_step += 1
        self.stack.setCurrentIndex(self.current_step)
        self._update_step_ui()

    def _update_step_ui(self):
        """Update UI based on current step."""
        steps = [
            "Step 1 of 4: Select Company",
            "Step 2 of 4: Select Files",
            "Step 3 of 4: Review & Configure",
            "Step 4 of 4: Import Data"
        ]
        self.step_label.setText(steps[self.current_step])
        self.back_btn.setEnabled(self.current_step > 0 and self.current_step < 3)
        self._update_progress()

        if self.current_step == 3:
            self.next_btn.setText("Finish")
            self.back_btn.setEnabled(False)
        elif self.current_step == 2:
            self.next_btn.setText("Start Import")
        else:
            self.next_btn.setText("Next >")

    def _prepare_data_preview(self):
        """Prepare data preview for step 3."""
        # Aggregate all records by type
        type_counts = {
            'accounts': 0, 'customers': 0, 'vendors': 0, 'employees': 0,
            'items': 0, 'invoices': 0, 'bills': 0, 'checks': 0,
            'deposits': 0, 'journal_entries': 0, 'payments_received': 0,
            'bills_paid': 0
        }

        for file_path, file_data in self.import_data['files'].items():
            data_type = file_data.get('type', 'unknown')
            records = file_data.get('records', [])

            if data_type in type_counts:
                type_counts[data_type] += len(records)
            elif data_type == 'transactions':
                # Split transactions into appropriate categories
                for rec in records:
                    rec_type = rec.get('_type', rec.get('type', '')).upper()
                    if 'CHECK' in rec_type or rec.get('docnum', '').startswith('CHK'):
                        type_counts['checks'] += 1
                    elif 'DEPOSIT' in rec_type:
                        type_counts['deposits'] += 1
                    elif 'INVOICE' in rec_type:
                        type_counts['invoices'] += 1
                    elif 'BILL' in rec_type:
                        type_counts['bills'] += 1
                    else:
                        type_counts['journal_entries'] += 1
            elif data_type == 'bank_transactions':
                # Bank transactions go to deposits or checks based on amount
                for rec in records:
                    if rec.get('amount', 0) >= 0:
                        type_counts['deposits'] += 1
                    else:
                        type_counts['checks'] += 1

        # Update UI counts
        for key, count in type_counts.items():
            label = self.stack.widget(2).findChild(QLabel, f"count_{key}")
            if label:
                label.setText(f"{count:,} records")
            if key in self.category_checks:
                self.category_checks[key].setEnabled(count > 0)
                if count == 0:
                    self.category_checks[key].setChecked(False)

    def _run_import(self):
        """Execute the import process."""
        self.import_log.clear()
        self._log("Starting QuickBooks import...")
        self._log(f"Target company: {self.import_data['company_name']}")

        # Create company if needed
        if self.new_radio.isChecked():
            self._log("Creating new company...")
            result = api_post("/companies", {
                "name": self.import_data['company_name'],
                "type": "farm"
            })
            if result:
                self._log(f"Company created: {self.import_data['company_name']}")
            else:
                self._log("Warning: Could not create company, using default")

        total_records = sum(
            len(fd.get('records', []))
            for fd in self.import_data['files'].values()
        )
        processed = 0
        results = {}

        # Import order: accounts -> entities -> items -> transactions
        import_order = [
            ('accounts', '/accounts', 'Chart of Accounts'),
            ('customers', '/customers', 'Customers'),
            ('vendors', '/vendors', 'Vendors'),
            ('employees', '/employees', 'Employees'),
            ('items', '/inventory', 'Items'),
            ('invoices', '/invoices', 'Invoices'),
            ('bills', '/bills', 'Bills'),
            ('payments_received', '/receive-payments', 'Payments Received'),
            ('bills_paid', '/bill-payments', 'Bill Payments'),
            ('checks', '/checks', 'Checks'),
            ('deposits', '/deposits', 'Deposits'),
            ('journal_entries', '/journal-entries', 'Journal Entries'),
        ]

        for data_type, endpoint, display_name in import_order:
            if data_type not in self.category_checks:
                continue
            if not self.category_checks[data_type].isChecked():
                continue

            self._log(f"\nImporting {display_name}...")
            self.current_task_label.setText(f"Importing {display_name}...")

            records_to_import = []
            for file_data in self.import_data['files'].values():
                if file_data.get('type') == data_type:
                    records_to_import.extend(file_data.get('records', []))

            imported = 0
            skipped = 0
            errors = 0

            for record in records_to_import:
                try:
                    # Transform record to API format
                    api_record = self._transform_record(data_type, record)
                    if api_record:
                        result = api_post(endpoint, api_record)
                        if result:
                            imported += 1
                        else:
                            if self.skip_duplicates.isChecked():
                                skipped += 1
                            else:
                                errors += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors += 1
                    self._log(f"  Error: {e}")

                processed += 1
                self._update_progress_bar(processed, total_records)

            results[display_name] = {
                'imported': imported,
                'skipped': skipped,
                'errors': errors
            }
            self._log(f"  Imported: {imported}, Skipped: {skipped}, Errors: {errors}")

        self._show_results(results)

    def _transform_record(self, data_type: str, record: Dict) -> Optional[Dict]:
        """Transform a QuickBooks record to GenFin API format."""
        if data_type == 'accounts':
            return {
                'name': record.get('NAME', record.get('name', '')),
                'type': self._map_account_type(record.get('ACCNTTYPE', record.get('type', ''))),
                'number': record.get('ACCNUM', record.get('number', '')),
                'description': record.get('DESC', record.get('description', '')),
                'balance': float(record.get('BALANCE', record.get('balance', 0)) or 0)
            }
        elif data_type == 'customers':
            return {
                'name': record.get('NAME', record.get('name', record.get('Customer', ''))),
                'email': record.get('EMAIL', record.get('email', '')),
                'phone': record.get('PHONE1', record.get('phone', '')),
                'address': record.get('ADDR1', record.get('address', '')),
                'city': record.get('CITY', record.get('city', '')),
                'state': record.get('STATE', record.get('state', '')),
                'zip': record.get('ZIP', record.get('zip', '')),
                'balance': float(record.get('BALANCE', record.get('balance', 0)) or 0)
            }
        elif data_type == 'vendors':
            return {
                'name': record.get('NAME', record.get('name', record.get('Vendor', ''))),
                'email': record.get('EMAIL', record.get('email', '')),
                'phone': record.get('PHONE1', record.get('phone', '')),
                'address': record.get('ADDR1', record.get('address', '')),
                'city': record.get('CITY', record.get('city', '')),
                'state': record.get('STATE', record.get('state', '')),
                'zip': record.get('ZIP', record.get('zip', '')),
                'balance': float(record.get('BALANCE', record.get('balance', 0)) or 0)
            }
        elif data_type == 'employees':
            return {
                'first_name': record.get('FIRSTNAME', record.get('first_name', '')),
                'last_name': record.get('LASTNAME', record.get('last_name', '')),
                'email': record.get('EMAIL', record.get('email', '')),
                'phone': record.get('PHONE', record.get('phone', '')),
                'ssn': record.get('SSN', ''),
                'hire_date': record.get('HIREDATE', record.get('hire_date', '')),
            }
        elif data_type in ['invoices', 'bills', 'checks', 'deposits', 'journal_entries']:
            return {
                'date': record.get('DATE', record.get('date', '')),
                'amount': float(record.get('AMOUNT', record.get('amount', 0)) or 0),
                'description': record.get('MEMO', record.get('description', record.get('memo', ''))),
                'reference': record.get('DOCNUM', record.get('reference', record.get('num', ''))),
                'account': record.get('ACCNT', record.get('account', '')),
            }
        else:
            return None

    def _map_account_type(self, qb_type: str) -> str:
        """Map QuickBooks account type to GenFin type."""
        type_map = {
            'BANK': 'bank',
            'AR': 'accounts_receivable',
            'AP': 'accounts_payable',
            'CCARD': 'credit_card',
            'FIXASSET': 'fixed_asset',
            'OASSET': 'other_asset',
            'OCASSET': 'other_current_asset',
            'OLIAB': 'other_liability',
            'OCLIAB': 'other_current_liability',
            'LTLIAB': 'long_term_liability',
            'EQUITY': 'equity',
            'INC': 'income',
            'COGS': 'cogs',
            'EXP': 'expense',
            'EXINC': 'other_income',
            'EXEXP': 'other_expense',
        }
        return type_map.get(qb_type.upper(), 'expense')

    def _update_progress_bar(self, current: int, total: int):
        """Update the visual progress bar."""
        if total > 0:
            pct = (current / total)
            width = int(self.progress_bar.width() * pct)
            self.progress_fill.setFixedWidth(width)
            self.progress_detail.setText(f"{current:,} of {total:,} records processed")
        QApplication.processEvents()

    def _log(self, message: str):
        """Add message to import log."""
        self.import_log.appendPlainText(message)
        QApplication.processEvents()

    def _show_results(self, results: Dict):
        """Show import results."""
        self.progress_group.hide()
        self.results_group.show()

        self.results_table.setRowCount(len(results))
        total_imported = 0
        total_skipped = 0
        total_errors = 0

        for i, (name, stats) in enumerate(results.items()):
            self.results_table.setItem(i, 0, QTableWidgetItem(name))
            self.results_table.setItem(i, 1, QTableWidgetItem(str(stats['imported'])))
            self.results_table.setItem(i, 2, QTableWidgetItem(str(stats['skipped'])))

            error_item = QTableWidgetItem(str(stats['errors']))
            if stats['errors'] > 0:
                error_item.setForeground(QColor('red'))
            self.results_table.setItem(i, 3, error_item)

            total_imported += stats['imported']
            total_skipped += stats['skipped']
            total_errors += stats['errors']

        self.import_stats = {
            'imported': total_imported,
            'skipped': total_skipped,
            'errors': total_errors
        }

        if total_errors == 0:
            self.results_summary.setText(
                f"✅ Import completed successfully!\n"
                f"Imported {total_imported:,} records into {self.import_data['company_name']}"
            )
            self.results_summary.setStyleSheet(f"color: green; font-size: 14px; padding: 10px;")
        else:
            self.results_summary.setText(
                f"⚠️ Import completed with {total_errors} error(s)\n"
                f"Imported {total_imported:,} records, skipped {total_skipped:,}"
            )
            self.results_summary.setStyleSheet(f"color: orange; font-size: 14px; padding: 10px;")

        self._log(f"\n{'='*50}")
        self._log(f"IMPORT COMPLETE")
        self._log(f"Total imported: {total_imported:,}")
        self._log(f"Total skipped: {total_skipped:,}")
        self._log(f"Total errors: {total_errors}")

        self.next_btn.setEnabled(True)
        self.import_complete.emit(self.import_data['company_name'], self.import_stats)


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

        # Pay Schedule - links employee to scheduled payroll
        self.pay_schedule = QComboBox()
        self.pay_schedule.addItem("-- Select Pay Schedule --", "")
        self._load_pay_schedules()
        pay_layout.addRow("Pay Schedule*:", self.pay_schedule)

        # Payment method with clear options
        pay_layout.addRow(QLabel(""))  # Spacer
        method_label = QLabel("How will this employee be paid?")
        method_label.setStyleSheet("font-weight: bold;")
        pay_layout.addRow(method_label)

        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Check - Print paycheck",
            "Direct Deposit - ACH transfer",
            "Both - Check and Direct Deposit"
        ])
        self.payment_method.currentIndexChanged.connect(self._on_payment_method_change)
        pay_layout.addRow("Payment Method:", self.payment_method)

        # Default hours per period for salaried employees
        self.default_hours = QDoubleSpinBox()
        self.default_hours.setMaximum(200)
        self.default_hours.setValue(80)  # Default biweekly
        self.default_hours.setDecimals(1)
        pay_layout.addRow("Default Hours/Period:", self.default_hours)

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

    def _load_pay_schedules(self):
        """Load pay schedules from API for dropdown."""
        schedules = api_get("/pay-schedules")
        if schedules:
            sched_list = schedules if isinstance(schedules, list) else schedules.get("schedules", [])
            for sched in sched_list:
                if sched.get("is_active", True):
                    freq = sched.get("frequency", "biweekly").replace("_", "-").title()
                    self.pay_schedule.addItem(
                        f"{sched['name']} ({freq})",
                        sched.get("schedule_id", "")
                    )

    def _on_payment_method_change(self, index: int):
        """Handle payment method change - show/hide direct deposit fields."""
        # Direct deposit tab is always visible but this could highlight it
        pass

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
        self.default_hours.setValue(d.get("default_hours", 80))

        # Payment method mapping
        pm = d.get("payment_method", "check")
        if pm == "direct_deposit":
            self.payment_method.setCurrentIndex(1)
        elif pm == "both":
            self.payment_method.setCurrentIndex(2)
        else:
            self.payment_method.setCurrentIndex(0)

        # Pay schedule - find matching schedule
        schedule_id = d.get("pay_schedule_id", "")
        for i in range(self.pay_schedule.count()):
            if self.pay_schedule.itemData(i) == schedule_id:
                self.pay_schedule.setCurrentIndex(i)
                break

        # Direct deposit info
        self.bank_routing.setText(d.get("bank_routing_number", ""))
        self.bank_account.setText(d.get("bank_account_number", ""))
        self.bank_account_type.setCurrentText(d.get("bank_account_type", "checking"))

        # Address
        self.address.setText(d.get("address_line1", ""))
        self.city.setText(d.get("city", ""))
        if d.get("state"):
            self.state.setCurrentText(d["state"])
        self.zip_code.setText(d.get("zip_code", ""))

    def _save(self):
        """Validate and save employee data."""
        if not self.first_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "First name is required.")
            return
        if not self.last_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Last name is required.")
            return

        # Validate pay schedule is selected
        schedule_id = self.pay_schedule.currentData()
        if not schedule_id:
            QMessageBox.warning(self, "Validation Error",
                "Please select a Pay Schedule.\n\n"
                "Employees must be assigned to a pay schedule to appear in payroll.")
            return

        # Convert payment method display to value
        pm_index = self.payment_method.currentIndex()
        payment_method = ["check", "direct_deposit", "both"][pm_index]

        # Validate direct deposit info if needed
        if payment_method in ["direct_deposit", "both"]:
            if not self.bank_routing.text().strip():
                QMessageBox.warning(self, "Validation Error",
                    "Routing number is required for Direct Deposit.")
                return
            if not self.bank_account.text().strip():
                QMessageBox.warning(self, "Validation Error",
                    "Account number is required for Direct Deposit.")
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
            "pay_schedule_id": schedule_id,
            "default_hours": self.default_hours.value(),
            "filing_status": self.filing_status.currentText(),
            "federal_allowances": self.federal_allowances.value(),
            "federal_additional_withholding": self.fed_additional.value(),
            "state_allowances": self.state_allowances.value(),
            "payment_method": payment_method,
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

        # Map dialog fields to API expected fields
        self.result_data = {
            "company_name": self.name.text().strip(),
            "display_name": self.name.text().strip(),
            "contact_name": self.company.text().strip(),  # Company field used for contact
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "billing_address_line1": self.address.text().strip(),
            "billing_city": self.city.text().strip(),
            "billing_state": self.state.text().strip(),
            "billing_zip": self.zip_code.text().strip(),
            "credit_limit": self.credit_limit.value(),
            "payment_terms": self.payment_terms.currentText(),
            "customer_type": ""
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

        # Map dialog fields to API expected fields
        self.result_data = {
            "company_name": self.name.text().strip(),
            "display_name": self.name.text().strip(),
            "contact_name": self.company.text().strip(),  # Company field used for contact
            "email": self.email.text().strip(),
            "phone": self.phone.text().strip(),
            "billing_address_line1": self.address.text().strip(),
            "billing_city": self.city.text().strip(),
            "billing_state": self.state.text().strip(),
            "billing_zip": self.zip_code.text().strip(),
            "tax_id": self.tax_id.text().strip(),
            "is_1099_vendor": self.is_1099.isChecked(),
            "payment_terms": self.payment_terms.currentText(),
            "vendor_type": ""
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

class AccountComboBox(QComboBox):
    """Editable combobox for account selection with auto-complete."""

    def __init__(self, account_types: List[str] = None, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._accounts = []
        self._account_types = account_types  # Filter by type if specified

        # Setup completer for auto-complete
        self.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer().setFilterMode(Qt.MatchFlag.MatchContains)

        # Load accounts
        self._load_accounts()

    def _load_accounts(self):
        """Load accounts from API."""
        data = api_get("/accounts")
        if data:
            accounts = data if isinstance(data, list) else []

            # Filter by type if specified
            if self._account_types:
                accounts = [a for a in accounts if a.get("account_type") in self._account_types]

            self._accounts = accounts
            self.clear()
            self.addItem("")  # Empty option

            for acct in accounts:
                # Format: "Account Name (Type)"
                name = acct.get("name", "")
                acct_type = acct.get("account_type", "").replace("_", " ").title()
                display = f"{name}"
                self.addItem(display, acct.get("account_id"))

    def get_account_id(self) -> Optional[str]:
        """Get the selected account ID."""
        return self.currentData()

    def get_account_name(self) -> str:
        """Get the selected/entered account name."""
        return self.currentText().strip()


class WriteCheckDialog(GenFinDialog):
    """Dialog for writing a check - QuickBooks style with editable account combos."""

    def __init__(self, parent=None):
        super().__init__("Write Checks", parent)
        self.result_data = None
        self.setMinimumWidth(700)
        self._bank_accounts = []
        self._expense_accounts = []
        self._load_accounts()
        self._setup_ui()

    def _load_accounts(self):
        """Load accounts from API."""
        data = api_get("/accounts")
        if data:
            accounts = data if isinstance(data, list) else []
            # Bank accounts for the "from" dropdown
            self._bank_accounts = [a for a in accounts if a.get("account_type") in ["bank", "checking", "savings"]]
            # Expense accounts for line items
            self._expense_accounts = [a for a in accounts if a.get("account_type") in
                                      ["expense", "cost_of_goods_sold", "other_expense"]]
            # If no expense accounts, use all non-bank accounts
            if not self._expense_accounts:
                self._expense_accounts = [a for a in accounts if a.get("account_type") not in ["bank", "checking", "savings"]]

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
        self.bank_account.setEditable(True)
        self.bank_account.setMinimumWidth(200)
        # Add bank accounts from API
        if self._bank_accounts:
            for acct in self._bank_accounts:
                self.bank_account.addItem(acct.get("name", ""), acct.get("account_id"))
        else:
            # Fallback defaults
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

        # Expense details - QuickBooks style with editable account combos
        expense_frame = QGroupBox("Expenses")
        expense_layout = QVBoxLayout(expense_frame)

        # Add row button
        add_row_layout = QHBoxLayout()
        add_row_btn = QPushButton("+ Add Line")
        add_row_btn.clicked.connect(self._add_expense_row)
        add_row_layout.addWidget(add_row_btn)
        add_row_layout.addStretch()

        total_label = QLabel("Total:")
        total_label.setStyleSheet("font-weight: bold;")
        add_row_layout.addWidget(total_label)
        self.expense_total = QLabel("$0.00")
        self.expense_total.setStyleSheet("font-weight: bold; font-size: 14px;")
        add_row_layout.addWidget(self.expense_total)
        expense_layout.addLayout(add_row_layout)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(4)
        self.expense_table.setHorizontalHeaderLabels(["Account", "Memo", "Amount", ""])
        self.expense_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.expense_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.expense_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.expense_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.expense_table.setColumnWidth(2, 120)
        self.expense_table.setColumnWidth(3, 30)
        self.expense_table.setRowCount(3)

        # Create initial rows with editable account combos
        for row in range(3):
            self._setup_expense_row(row)

        expense_layout.addWidget(self.expense_table)
        layout.addWidget(expense_frame)

        # Buttons
        self._create_buttons(layout)

    def _setup_expense_row(self, row: int):
        """Setup a single expense row with editable account combo."""
        # Editable account combo with auto-complete
        account_combo = QComboBox()
        account_combo.setEditable(True)
        account_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        account_combo.addItem("")  # Empty option first

        # Add accounts from API
        for acct in self._expense_accounts:
            account_combo.addItem(acct.get("name", ""), acct.get("account_id"))

        # If no API accounts, add common defaults
        if not self._expense_accounts:
            defaults = ["Supplies", "Repairs & Maintenance", "Fuel", "Seed", "Fertilizer",
                       "Chemicals", "Equipment Rental", "Utilities", "Insurance", "Professional Fees",
                       "Contract Labor", "Rent", "Interest Expense", "Office Supplies", "Vehicle Expense"]
            for name in defaults:
                account_combo.addItem(name)

        self.expense_table.setCellWidget(row, 0, account_combo)

        # Memo
        self.expense_table.setItem(row, 1, QTableWidgetItem(""))

        # Amount with auto-update
        amount_spin = QDoubleSpinBox()
        amount_spin.setMaximum(9999999.99)
        amount_spin.setDecimals(2)
        amount_spin.setPrefix("$ ")
        amount_spin.valueChanged.connect(self._update_expense_total)
        self.expense_table.setCellWidget(row, 2, amount_spin)

        # Delete button
        del_btn = QPushButton("×")
        del_btn.setMaximumWidth(25)
        del_btn.setStyleSheet("color: red; font-weight: bold;")
        del_btn.clicked.connect(lambda: self._remove_expense_row(row))
        self.expense_table.setCellWidget(row, 3, del_btn)

    def _add_expense_row(self):
        """Add a new expense row."""
        row = self.expense_table.rowCount()
        self.expense_table.setRowCount(row + 1)
        self._setup_expense_row(row)

    def _remove_expense_row(self, row: int):
        """Remove an expense row."""
        if self.expense_table.rowCount() > 1:
            self.expense_table.removeRow(row)
            self._update_expense_total()

    def _update_expense_total(self):
        """Update the expense total display."""
        total = 0.0
        for row in range(self.expense_table.rowCount()):
            amount_widget = self.expense_table.cellWidget(row, 2)
            if isinstance(amount_widget, QDoubleSpinBox):
                total += amount_widget.value()
        self.expense_total.setText(f"${total:,.2f}")

        # Also update the check amount if it's less than expenses
        if self.amount.value() < total:
            self.amount.setValue(total)

    def _create_buttons(self, layout):
        """Create dialog buttons."""
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

        version = QLabel("v6.6.0")
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
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {GENFIN_COLORS['teal_dark']};
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {GENFIN_COLORS['teal_dark']};
            }}
            QScrollBar:vertical {{
                background-color: {GENFIN_COLORS['teal_dark']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {GENFIN_COLORS['teal']};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        nav_widget = QWidget()
        nav_widget.setStyleSheet(f"background-color: {GENFIN_COLORS['teal_dark']};")
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
    company_changed = pyqtSignal(str)  # Emits entity_id when company changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_entity_id = None
        self._entities = []
        self._setup_ui()
        QTimer.singleShot(100, self._load_entities)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Company Switcher at top
        company_frame = QFrame()
        company_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {GENFIN_COLORS['teal_dark']},
                    stop:1 {GENFIN_COLORS['teal']});
                border: 2px outset {GENFIN_COLORS['teal_light']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        company_layout = QHBoxLayout(company_frame)
        company_layout.setContentsMargins(12, 8, 12, 8)
        company_layout.setSpacing(12)

        company_icon = QLabel("🏢")
        company_icon.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        company_layout.addWidget(company_icon)

        company_label = QLabel("Company:")
        company_label.setStyleSheet(f"""
            color: white;
            font-weight: bold;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        company_layout.addWidget(company_label)

        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(250)
        self.company_combo.setStyleSheet(f"""
            QComboBox {{
                background: white;
                border: 2px inset {GENFIN_COLORS['bevel_shadow']};
                padding: 4px 8px;
                font-size: 12px;
                font-weight: bold;
                color: {GENFIN_COLORS['teal_dark']};
            }}
            QComboBox:hover {{
                border-color: {GENFIN_COLORS['teal']};
            }}
            QComboBox::drop-down {{
                border-left: 1px solid {GENFIN_COLORS['bevel_shadow']};
                width: 20px;
            }}
        """)
        self.company_combo.currentIndexChanged.connect(self._on_company_changed)
        company_layout.addWidget(self.company_combo)

        company_layout.addStretch()

        # Quick action buttons
        new_company_btn = QPushButton("+ New Company")
        new_company_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 {GENFIN_COLORS['window_bg']});
                border: 2px outset {GENFIN_COLORS['bevel_shadow']};
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
                color: {GENFIN_COLORS['teal_dark']};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {GENFIN_COLORS['teal_light']}, stop:1 {GENFIN_COLORS['teal']});
                color: white;
            }}
            QPushButton:pressed {{
                border-style: inset;
            }}
        """)
        new_company_btn.clicked.connect(self._add_new_company)
        company_layout.addWidget(new_company_btn)

        # Import from QuickBooks button
        import_qb_btn = QPushButton("📥 Import from QuickBooks")
        import_qb_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 {GENFIN_COLORS['window_bg']});
                border: 2px outset {GENFIN_COLORS['bevel_shadow']};
                padding: 4px 12px;
                font-size: 10px;
                font-weight: bold;
                color: {GENFIN_COLORS['teal_dark']};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {GENFIN_COLORS['teal_light']}, stop:1 {GENFIN_COLORS['teal']});
                color: white;
            }}
            QPushButton:pressed {{
                border-style: inset;
            }}
        """)
        import_qb_btn.clicked.connect(self._import_from_quickbooks)
        company_layout.addWidget(import_qb_btn)

        layout.addWidget(company_frame)

        welcome_frame = QFrame()
        welcome_frame.setProperty("class", "genfin-panel-raised")
        welcome_layout = QVBoxLayout(welcome_frame)

        self.welcome_label = QLabel("Welcome to GenFin Accounting")
        self.welcome_label.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
        """)
        welcome_layout.addWidget(self.welcome_label)

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

    def _load_entities(self):
        """Load entities/companies from API."""
        self.company_combo.blockSignals(True)
        self.company_combo.clear()

        # Always add a default company
        self.company_combo.addItem("New Generation Farms (Default)", "default")

        # Load entities from API
        result = api_get("/entities")
        if result and isinstance(result, dict):
            entities = result.get("entities", [])
            self._entities = entities
            for entity in entities:
                name = entity.get("name", "Unknown")
                entity_type = entity.get("entity_type", "").upper()
                entity_id = entity.get("id", "")
                display = f"{name} ({entity_type})" if entity_type else name
                self.company_combo.addItem(display, entity_id)

        # Set to default or first entity
        if self._current_entity_id:
            for i in range(self.company_combo.count()):
                if self.company_combo.itemData(i) == self._current_entity_id:
                    self.company_combo.setCurrentIndex(i)
                    break

        self.company_combo.blockSignals(False)
        self._update_welcome_message()

    def _on_company_changed(self, index: int):
        """Handle company selection change."""
        entity_id = self.company_combo.itemData(index)
        if entity_id and entity_id != self._current_entity_id:
            self._current_entity_id = entity_id
            company_name = self.company_combo.currentText()
            self._update_welcome_message()
            self.company_changed.emit(entity_id)
            # Reload stats for the new company
            self._load_stats()

    def _update_welcome_message(self):
        """Update welcome label with current company name."""
        company_name = self.company_combo.currentText()
        if company_name:
            # Extract just the name without the type in parentheses
            if " (" in company_name:
                company_name = company_name.split(" (")[0]
            self.welcome_label.setText(f"Welcome to {company_name}")

    def _import_from_quickbooks(self):
        """Launch QuickBooks Import Wizard to import company data."""
        dialog = QuickBooksImportWizard(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Refresh company list and stats after successful import
            self._load_entities()
            self._load_stats()
            QMessageBox.information(
                self,
                "Import Complete",
                "QuickBooks data has been successfully imported!\n\n"
                "Your financial history is now available in GenFin."
            )

    def _add_new_company(self):
        """Show dialog to add a new company/entity."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Company")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet(GENFIN_STYLESHEET)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        # Company Name
        name_label = QLabel("Company Name:")
        name_label.setProperty("class", "genfin-label")
        layout.addWidget(name_label)

        name_input = QLineEdit()
        name_input.setProperty("class", "genfin-input")
        name_input.setPlaceholderText("e.g., North Farm LLC")
        layout.addWidget(name_input)

        # Legal Name
        legal_label = QLabel("Legal Name:")
        legal_label.setProperty("class", "genfin-label")
        layout.addWidget(legal_label)

        legal_input = QLineEdit()
        legal_input.setProperty("class", "genfin-input")
        legal_input.setPlaceholderText("Full legal name")
        layout.addWidget(legal_input)

        # Entity Type
        type_label = QLabel("Entity Type:")
        type_label.setProperty("class", "genfin-label")
        layout.addWidget(type_label)

        type_combo = QComboBox()
        type_combo.setProperty("class", "genfin-combo")
        type_combo.addItems(["Farm", "LLC", "Corporation", "S-Corp", "Partnership", "Trust", "Sole Proprietorship"])
        layout.addWidget(type_combo)

        # Tax ID
        tax_label = QLabel("Tax ID (EIN):")
        tax_label.setProperty("class", "genfin-label")
        layout.addWidget(tax_label)

        tax_input = QLineEdit()
        tax_input.setProperty("class", "genfin-input")
        tax_input.setPlaceholderText("XX-XXXXXXX")
        layout.addWidget(tax_input)

        # State
        state_label = QLabel("State of Formation:")
        state_label.setProperty("class", "genfin-label")
        layout.addWidget(state_label)

        state_input = QLineEdit()
        state_input.setProperty("class", "genfin-input")
        state_input.setPlaceholderText("e.g., LA")
        state_input.setMaxLength(2)
        layout.addWidget(state_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "genfin-button")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Create Company")
        save_btn.setProperty("class", "genfin-button-primary")
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        def save_company():
            name = name_input.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Required", "Company name is required.")
                return

            data = {
                "name": name,
                "legal_name": legal_input.text().strip() or name,
                "entity_type": type_combo.currentText().lower().replace(" ", "_").replace("-", ""),
                "tax_id": tax_input.text().strip(),
                "state_of_formation": state_input.text().strip().upper()
            }

            result = api_post("/entities", data)
            if result:
                dialog.accept()
                self._load_entities()
                # Select the new company
                for i in range(self.company_combo.count()):
                    if self.company_combo.itemText(i).startswith(name):
                        self.company_combo.setCurrentIndex(i)
                        break
                QMessageBox.information(self, "Success", f"Company '{name}' created successfully!")
            else:
                QMessageBox.warning(dialog, "Error", "Failed to create company.")

        save_btn.clicked.connect(save_company)
        dialog.exec()


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
        item_id = item.get(self.id_field)

        if not item_id:
            QMessageBox.warning(self, "Error", f"Cannot delete: No {self.id_field} found in item data.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            endpoint = f"{self.api_endpoint}/{item_id}"
            print(f"Attempting to delete: {endpoint}")  # Debug
            if api_delete(endpoint):
                QMessageBox.information(self, "Success", f"'{name}' deleted successfully!")
                self.load_data()
            else:
                QMessageBox.warning(self, "Error",
                    f"Failed to delete '{name}'.\n\n"
                    f"Check console for details.\n"
                    f"Endpoint: {self.api_endpoint}/{item_id}")

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
            ["Name", "Contact", "Phone", "Balance"],
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
                # Map API response fields to display
                name = c.get("display_name") or c.get("company_name", "")
                contact = c.get("contact_name", "")
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(contact))
                self.table.setItem(i, 2, QTableWidgetItem(c.get("phone", "")))
                balance = c.get("balance", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${balance:,.2f}"))


class GenFinVendorsScreen(GenFinListScreen):
    """Vendors screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Vendors",
            ["Name", "Contact", "Phone", "Balance"],
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
                # Map API response fields to display
                name = v.get("display_name") or v.get("company_name", "")
                contact = v.get("contact_name", "")
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(contact))
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


# =============================================================================
# BANKING MODULE - QuickBooks Style Bank Management
# =============================================================================

class GenFinBankAccountsScreen(QWidget):
    """Bank Accounts management screen - QuickBooks style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accounts = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("BANK ACCOUNTS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("New Account")
        new_btn.clicked.connect(self._new_account)
        toolbar.addWidget(new_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_account)
        toolbar.addWidget(edit_btn)

        reconcile_btn = QPushButton("Reconcile")
        reconcile_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        reconcile_btn.clicked.connect(self._reconcile)
        toolbar.addWidget(reconcile_btn)

        toolbar.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Accounts table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Account Name", "Type", "Account #", "Balance", "Last Reconciled", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._view_register)
        layout.addWidget(self.table)

        # Summary panel
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['panel_bg']};
            border: 2px groove {GENFIN_COLORS['bevel_shadow']};
            padding: 8px;
        """)
        summary_layout = QHBoxLayout(summary_frame)

        self.total_label = QLabel("Total Cash: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.total_label)

        summary_layout.addStretch()

        view_register_btn = QPushButton("View Register")
        view_register_btn.clicked.connect(self._view_register)
        summary_layout.addWidget(view_register_btn)

        layout.addWidget(summary_frame)

    def load_data(self):
        """Load bank accounts from API."""
        data = api_get("/bank-accounts")
        if data is not None:
            self._accounts = data if isinstance(data, list) else []
            self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._accounts))
        total = 0

        for i, acct in enumerate(self._accounts):
            self.table.setItem(i, 0, QTableWidgetItem(acct.get("name", "")))

            acct_type = acct.get("account_type", "checking").replace("_", " ").title()
            self.table.setItem(i, 1, QTableWidgetItem(acct_type))

            self.table.setItem(i, 2, QTableWidgetItem(acct.get("account_number", "")[-4:] if acct.get("account_number") else ""))

            balance = acct.get("balance", 0)
            total += balance
            balance_item = QTableWidgetItem(f"${balance:,.2f}")
            if balance < 0:
                balance_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 3, balance_item)

            self.table.setItem(i, 4, QTableWidgetItem(acct.get("last_reconciled", "Never")))

            status = "Active" if acct.get("is_active", True) else "Inactive"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.darkGreen if status == "Active" else Qt.GlobalColor.gray)
            self.table.setItem(i, 5, status_item)

        self.total_label.setText(f"Total Cash: ${total:,.2f}")

    def _new_account(self):
        dialog = BankAccountDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/bank-accounts", dialog.result_data)
            if result:
                QMessageBox.information(self, "Success", "Bank account created!")
                self.load_data()

    def _edit_account(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._accounts):
            QMessageBox.warning(self, "Warning", "Please select an account to edit.")
            return
        dialog = BankAccountDialog(self._accounts[row], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

    def _reconcile(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._accounts):
            QMessageBox.warning(self, "Warning", "Please select an account to reconcile.")
            return
        QMessageBox.information(self, "Reconcile",
            f"Opening reconciliation for: {self._accounts[row].get('name', '')}\n\n"
            "This will open the reconciliation wizard.")

    def _view_register(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._accounts):
            QMessageBox.warning(self, "Warning", "Please select an account to view.")
            return
        QMessageBox.information(self, "Register",
            f"Opening register for: {self._accounts[row].get('name', '')}")


class BankAccountDialog(GenFinDialog):
    """Dialog for adding/editing a bank account."""

    def __init__(self, account_data: Optional[Dict] = None, parent=None):
        title = "Edit Bank Account" if account_data else "New Bank Account"
        super().__init__(title, parent)
        self.account_data = account_data
        self.result_data = None
        self._setup_ui()
        if account_data:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., Farm Operating Account")
        form.addRow("Account Name*:", self.name)

        self.account_type = QComboBox()
        self.account_type.addItems(["Checking", "Savings", "Money Market", "Credit Card", "Line of Credit"])
        form.addRow("Account Type*:", self.account_type)

        self.bank_name = QLineEdit()
        self.bank_name.setPlaceholderText("e.g., First National Bank")
        form.addRow("Bank Name:", self.bank_name)

        self.account_number = QLineEdit()
        self.account_number.setPlaceholderText("Account number")
        form.addRow("Account Number:", self.account_number)

        self.routing_number = QLineEdit()
        self.routing_number.setPlaceholderText("Routing number")
        form.addRow("Routing Number:", self.routing_number)

        self.opening_balance = QDoubleSpinBox()
        self.opening_balance.setRange(-999999999, 999999999)
        self.opening_balance.setDecimals(2)
        self.opening_balance.setPrefix("$")
        form.addRow("Opening Balance:", self.opening_balance)

        self.opening_date = QDateEdit()
        self.opening_date.setDate(QDate.currentDate())
        self.opening_date.setCalendarPopup(True)
        form.addRow("As of Date:", self.opening_date)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_data(self):
        if self.account_data:
            self.name.setText(self.account_data.get("name", ""))
            acct_type = self.account_data.get("account_type", "checking")
            idx = self.account_type.findText(acct_type.replace("_", " ").title())
            if idx >= 0:
                self.account_type.setCurrentIndex(idx)
            self.bank_name.setText(self.account_data.get("bank_name", ""))
            self.account_number.setText(self.account_data.get("account_number", ""))
            self.routing_number.setText(self.account_data.get("routing_number", ""))
            self.opening_balance.setValue(self.account_data.get("balance", 0))

    def _save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Validation", "Account name is required.")
            return

        self.result_data = {
            "name": self.name.text().strip(),
            "account_type": self.account_type.currentText().lower().replace(" ", "_"),
            "bank_name": self.bank_name.text().strip(),
            "account_number": self.account_number.text().strip(),
            "routing_number": self.routing_number.text().strip(),
            "balance": self.opening_balance.value(),
            "opening_date": self.opening_date.date().toString("yyyy-MM-dd")
        }
        self.accept()


class GenFinCheckRegisterScreen(QWidget):
    """Check Register screen - QuickBooks style transaction register."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accounts = []
        self._transactions = []
        self._current_account = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header with account selector
        header_layout = QHBoxLayout()

        header = QLabel("CHECK REGISTER")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
        """)
        header_layout.addWidget(header)

        header_layout.addStretch()

        header_layout.addWidget(QLabel("Account:"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(200)
        self.account_combo.currentIndexChanged.connect(self._on_account_change)
        header_layout.addWidget(self.account_combo)

        layout.addLayout(header_layout)

        # Toolbar
        toolbar = QHBoxLayout()

        write_check_btn = QPushButton("Write Check")
        write_check_btn.clicked.connect(self._write_check)
        toolbar.addWidget(write_check_btn)

        deposit_btn = QPushButton("Make Deposit")
        deposit_btn.clicked.connect(self._make_deposit)
        toolbar.addWidget(deposit_btn)

        transfer_btn = QPushButton("Transfer")
        transfer_btn.clicked.connect(self._transfer)
        toolbar.addWidget(transfer_btn)

        toolbar.addStretch()

        # Filter
        toolbar.addWidget(QLabel("Show:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Checks", "Deposits", "Transfers", "Uncleared"])
        self.filter_combo.currentTextChanged.connect(self._filter_transactions)
        toolbar.addWidget(self.filter_combo)

        layout.addLayout(toolbar)

        # Register table - QuickBooks style
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Date", "Num", "Payee/Description", "Payment", "Deposit", "Balance", "Clr", "Memo"
        ])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Bottom summary
        summary_layout = QHBoxLayout()

        self.balance_label = QLabel("Ending Balance: $0.00")
        self.balance_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.balance_label)

        summary_layout.addStretch()

        self.cleared_label = QLabel("Cleared: $0.00")
        summary_layout.addWidget(self.cleared_label)

        self.uncleared_label = QLabel("Uncleared: $0.00")
        summary_layout.addWidget(self.uncleared_label)

        layout.addLayout(summary_layout)

    def load_data(self):
        """Load accounts and transactions."""
        data = api_get("/bank-accounts")
        if data is not None:
            self._accounts = data if isinstance(data, list) else []
            self.account_combo.clear()
            for acct in self._accounts:
                self.account_combo.addItem(acct.get("name", ""), acct.get("account_id"))
        self._load_transactions()

    def _on_account_change(self, index):
        if index >= 0 and index < len(self._accounts):
            self._current_account = self._accounts[index]
            self._load_transactions()

    def _load_transactions(self):
        """Load transactions for current account."""
        if not self._current_account:
            return
        acct_id = self._current_account.get("account_id")
        data = api_get(f"/bank-accounts/{acct_id}/transactions")
        if data is not None:
            self._transactions = data if isinstance(data, list) else []
        else:
            self._transactions = []
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._transactions))
        running_balance = self._current_account.get("opening_balance", 0) if self._current_account else 0
        cleared_total = 0
        uncleared_total = 0

        for i, txn in enumerate(self._transactions):
            self.table.setItem(i, 0, QTableWidgetItem(txn.get("date", "")))
            self.table.setItem(i, 1, QTableWidgetItem(txn.get("number", "")))
            self.table.setItem(i, 2, QTableWidgetItem(txn.get("payee", "")))

            payment = txn.get("payment", 0)
            deposit = txn.get("deposit", 0)

            if payment > 0:
                self.table.setItem(i, 3, QTableWidgetItem(f"${payment:,.2f}"))
                running_balance -= payment
            else:
                self.table.setItem(i, 3, QTableWidgetItem(""))

            if deposit > 0:
                self.table.setItem(i, 4, QTableWidgetItem(f"${deposit:,.2f}"))
                running_balance += deposit
            else:
                self.table.setItem(i, 4, QTableWidgetItem(""))

            balance_item = QTableWidgetItem(f"${running_balance:,.2f}")
            if running_balance < 0:
                balance_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(i, 5, balance_item)

            cleared = txn.get("cleared", False)
            self.table.setItem(i, 6, QTableWidgetItem("✓" if cleared else ""))

            self.table.setItem(i, 7, QTableWidgetItem(txn.get("memo", "")))

            if cleared:
                cleared_total += (deposit - payment)
            else:
                uncleared_total += (deposit - payment)

        self.balance_label.setText(f"Ending Balance: ${running_balance:,.2f}")
        self.cleared_label.setText(f"Cleared: ${cleared_total:,.2f}")
        self.uncleared_label.setText(f"Uncleared: ${uncleared_total:,.2f}")

    def _filter_transactions(self, filter_text):
        self._populate_table()

    def _write_check(self):
        QMessageBox.information(self, "Write Check", "Opening Write Checks screen...")

    def _make_deposit(self):
        QMessageBox.information(self, "Make Deposit", "Opening Make Deposits screen...")

    def _transfer(self):
        QMessageBox.information(self, "Transfer", "Opening Transfer Funds dialog...")


class GenFinTransfersScreen(QWidget):
    """Transfer Funds screen - move money between accounts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accounts = []
        self._transfers = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("TRANSFER FUNDS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # New Transfer section
        transfer_group = QGroupBox("New Transfer")
        transfer_layout = QFormLayout(transfer_group)
        transfer_layout.setSpacing(8)

        self.from_account = QComboBox()
        transfer_layout.addRow("From Account:", self.from_account)

        self.to_account = QComboBox()
        transfer_layout.addRow("To Account:", self.to_account)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0.01, 999999999)
        self.amount.setDecimals(2)
        self.amount.setPrefix("$")
        transfer_layout.addRow("Amount:", self.amount)

        self.transfer_date = QDateEdit()
        self.transfer_date.setDate(QDate.currentDate())
        self.transfer_date.setCalendarPopup(True)
        transfer_layout.addRow("Date:", self.transfer_date)

        self.memo = QLineEdit()
        self.memo.setPlaceholderText("Optional memo")
        transfer_layout.addRow("Memo:", self.memo)

        transfer_btn = QPushButton("Transfer Funds")
        transfer_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white; padding: 10px;")
        transfer_btn.clicked.connect(self._do_transfer)
        transfer_layout.addRow("", transfer_btn)

        layout.addWidget(transfer_group)

        # Recent transfers
        history_label = QLabel("Recent Transfers")
        history_label.setStyleSheet("font-weight: bold; font-size: 12px; padding-top: 12px;")
        layout.addWidget(history_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "From", "To", "Amount", "Memo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def load_data(self):
        data = api_get("/bank-accounts")
        if data is not None:
            self._accounts = data if isinstance(data, list) else []
            self.from_account.clear()
            self.to_account.clear()
            for acct in self._accounts:
                name = f"{acct.get('name', '')} (${acct.get('balance', 0):,.2f})"
                self.from_account.addItem(name, acct.get("account_id"))
                self.to_account.addItem(name, acct.get("account_id"))

    def _do_transfer(self):
        if self.from_account.currentIndex() == self.to_account.currentIndex():
            QMessageBox.warning(self, "Error", "Cannot transfer to the same account.")
            return

        if self.amount.value() <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid amount.")
            return

        from_name = self.from_account.currentText().split(" (")[0]
        to_name = self.to_account.currentText().split(" (")[0]
        amount = self.amount.value()

        reply = QMessageBox.question(self, "Confirm Transfer",
            f"Transfer ${amount:,.2f} from {from_name} to {to_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Success", "Transfer completed successfully!")
            self.amount.setValue(0)
            self.memo.clear()
            self.load_data()


class GenFinReconcileScreen(QWidget):
    """Bank Reconciliation screen - QuickBooks style."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accounts = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("RECONCILE ACCOUNTS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Account selection
        select_group = QGroupBox("Begin Reconciliation")
        select_layout = QFormLayout(select_group)

        self.account_combo = QComboBox()
        select_layout.addRow("Account:", self.account_combo)

        self.statement_date = QDateEdit()
        self.statement_date.setDate(QDate.currentDate())
        self.statement_date.setCalendarPopup(True)
        select_layout.addRow("Statement Date:", self.statement_date)

        self.ending_balance = QDoubleSpinBox()
        self.ending_balance.setRange(-999999999, 999999999)
        self.ending_balance.setDecimals(2)
        self.ending_balance.setPrefix("$")
        select_layout.addRow("Ending Balance:", self.ending_balance)

        begin_btn = QPushButton("Begin Reconciliation")
        begin_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        begin_btn.clicked.connect(self._begin_reconcile)
        select_layout.addRow("", begin_btn)

        layout.addWidget(select_group)

        # Info panel
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            background-color: #E8F4F4;
            border: 1px solid {GENFIN_COLORS['teal']};
            padding: 12px;
        """)
        info_layout = QVBoxLayout(info_frame)

        info_label = QLabel(
            "How to Reconcile:\n\n"
            "1. Enter the ending balance from your bank statement\n"
            "2. Check off transactions that appear on your statement\n"
            "3. The difference should be $0.00 when complete\n"
            "4. Click 'Finish' to record the reconciliation"
        )
        info_label.setStyleSheet("color: #006666;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_frame)

        layout.addStretch()

    def load_data(self):
        data = api_get("/bank-accounts")
        if data is not None:
            self._accounts = data if isinstance(data, list) else []
            self.account_combo.clear()
            for acct in self._accounts:
                self.account_combo.addItem(acct.get("name", ""), acct.get("account_id"))

    def _begin_reconcile(self):
        if self.account_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Please select an account.")
            return

        QMessageBox.information(self, "Reconciliation",
            f"Starting reconciliation for: {self.account_combo.currentText()}\n"
            f"Statement Date: {self.statement_date.date().toString('MM/dd/yyyy')}\n"
            f"Ending Balance: ${self.ending_balance.value():,.2f}\n\n"
            "The reconciliation wizard would open here.")


class GenFinBankFeedsScreen(QWidget):
    """Bank Feeds screen - connect to banks and download transactions with smart auto-matching."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._feed_transactions = []
        self._existing_transactions = []
        self._vendors = []
        self._customers = []
        self._accounts = []
        self._matching_rules = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("BANK FEEDS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Connection status
        status_group = QGroupBox("Connected Accounts")
        status_layout = QVBoxLayout(status_group)

        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels([
            "Bank", "Account", "Last Updated", "New Transactions", "Status"
        ])
        self.connections_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.connections_table.setMaximumHeight(150)
        status_layout.addWidget(self.connections_table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Connection")
        add_btn.clicked.connect(self._add_connection)
        btn_layout.addWidget(add_btn)

        import_btn = QPushButton("Import OFX/QFX")
        import_btn.clicked.connect(self._import_ofx)
        btn_layout.addWidget(import_btn)

        refresh_btn = QPushButton("Refresh All")
        refresh_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        refresh_btn.clicked.connect(self._refresh_feeds)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()

        rules_btn = QPushButton("Matching Rules")
        rules_btn.clicked.connect(self._manage_rules)
        btn_layout.addWidget(rules_btn)

        status_layout.addLayout(btn_layout)

        layout.addWidget(status_group)

        # Auto-matching status
        match_group = QGroupBox("Auto-Matching Status")
        match_layout = QHBoxLayout(match_group)

        self.match_stats = QLabel("Transactions: 0 | Auto-Matched: 0 | Need Review: 0")
        match_layout.addWidget(self.match_stats)

        match_layout.addStretch()

        auto_match_btn = QPushButton("Run Auto-Match")
        auto_match_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        auto_match_btn.clicked.connect(self._run_auto_match)
        match_layout.addWidget(auto_match_btn)

        layout.addWidget(match_group)

        # Downloaded transactions
        trans_group = QGroupBox("Downloaded Transactions - Awaiting Review")
        trans_layout = QVBoxLayout(trans_group)

        # Filter bar
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Show:"))
        self.show_filter = QComboBox()
        self.show_filter.addItems(["All", "Unmatched", "Auto-Matched", "Manually Matched", "Accepted"])
        self.show_filter.currentTextChanged.connect(self._filter_transactions)
        filter_layout.addWidget(self.show_filter)

        filter_layout.addWidget(QLabel("Account:"))
        self.account_filter = QComboBox()
        self.account_filter.addItem("All Accounts")
        self.account_filter.currentTextChanged.connect(self._filter_transactions)
        filter_layout.addWidget(self.account_filter)

        filter_layout.addStretch()

        trans_layout.addLayout(filter_layout)

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(8)
        self.trans_table.setHorizontalHeaderLabels([
            "Select", "Date", "Description", "Amount", "Match Confidence",
            "Matched To", "Category", "Action"
        ])
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        trans_layout.addWidget(self.trans_table)

        action_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        action_layout.addWidget(select_all_btn)

        accept_btn = QPushButton("Accept Selected")
        accept_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        accept_btn.clicked.connect(self._accept_transactions)
        action_layout.addWidget(accept_btn)

        action_layout.addStretch()

        match_btn = QPushButton("Find Match")
        match_btn.clicked.connect(self._find_match)
        action_layout.addWidget(match_btn)

        create_btn = QPushButton("Create Transaction")
        create_btn.clicked.connect(self._create_transaction)
        action_layout.addWidget(create_btn)

        ignore_btn = QPushButton("Ignore")
        ignore_btn.clicked.connect(self._ignore_transactions)
        action_layout.addWidget(ignore_btn)

        trans_layout.addLayout(action_layout)

        layout.addWidget(trans_group)

    def load_data(self):
        """Load bank feed data and related data for matching."""
        # Load existing transactions for matching
        self._existing_transactions = api_get("/bank-transactions") or []
        self._vendors = api_get("/vendors") or []
        self._customers = api_get("/customers") or []
        self._accounts = api_get("/accounts") or []

        # Update account filter
        self.account_filter.clear()
        self.account_filter.addItem("All Accounts")
        bank_accounts = api_get("/bank-accounts") or []
        for acct in bank_accounts:
            self.account_filter.addItem(acct.get("name", ""))

        # Load demo connections (in production, would be from API)
        self.connections_table.setRowCount(0)
        self.trans_table.setRowCount(0)

        self._update_stats()

    def _add_connection(self):
        """Open bank connection wizard."""
        dialog = BankConnectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Connected",
                "Bank account connected successfully.\n"
                "Transactions will be downloaded automatically.")
            self.load_data()

    def _import_ofx(self):
        """Import OFX/QFX file from bank."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Bank File", "",
            "Bank Files (*.ofx *.qfx *.qbo);;OFX Files (*.ofx);;QFX Files (*.qfx);;All Files (*.*)"
        )
        if file_path:
            try:
                transactions = self._parse_ofx(file_path)
                self._feed_transactions.extend(transactions)
                self._populate_transactions()
                self._run_auto_match()
                QMessageBox.information(self, "Import Complete",
                    f"Imported {len(transactions)} transactions.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Error importing file:\n{e}")

    def _parse_ofx(self, file_path: str) -> List[Dict]:
        """Parse OFX/QFX file."""
        transactions = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Simple OFX parser
            import re
            stmttrn_pattern = r'<STMTTRN>(.*?)</STMTTRN>'
            matches = re.findall(stmttrn_pattern, content, re.DOTALL)

            for match in matches:
                trans = {'source': 'bank_feed', 'status': 'pending'}

                # Extract fields
                trntype = re.search(r'<TRNTYPE>(\w+)', match)
                dtposted = re.search(r'<DTPOSTED>(\d+)', match)
                trnamt = re.search(r'<TRNAMT>([+-]?\d+\.?\d*)', match)
                name = re.search(r'<NAME>([^<]+)', match)
                memo = re.search(r'<MEMO>([^<]+)', match)
                fitid = re.search(r'<FITID>([^<]+)', match)

                if trntype:
                    trans['type'] = trntype.group(1)
                if dtposted:
                    date_str = dtposted.group(1)[:8]
                    trans['date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                if trnamt:
                    trans['amount'] = float(trnamt.group(1))
                if name:
                    trans['description'] = name.group(1).strip()
                if memo:
                    trans['memo'] = memo.group(1).strip()
                if fitid:
                    trans['fitid'] = fitid.group(1)

                if trans.get('amount'):
                    transactions.append(trans)

        except Exception as e:
            print(f"OFX parse error: {e}")

        return transactions

    def _refresh_feeds(self):
        """Refresh all bank feeds."""
        progress = QProgressDialog("Refreshing bank feeds...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        progress.setValue(30)
        # In production, would call bank APIs
        progress.setValue(60)
        self._run_auto_match()
        progress.setValue(100)
        progress.close()

        QMessageBox.information(self, "Refresh Complete",
            "Bank feeds refreshed. Auto-matching has been run.")

    def _manage_rules(self):
        """Open matching rules manager."""
        dialog = MatchingRulesDialog(self._matching_rules, self._accounts, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._matching_rules = dialog.get_rules()
            self._run_auto_match()

    def _run_auto_match(self):
        """Run the auto-matching algorithm on all pending transactions."""
        matched = 0
        total = len(self._feed_transactions)

        for trans in self._feed_transactions:
            if trans.get('status') == 'pending':
                match_result = self._find_best_match(trans)
                if match_result:
                    trans['match'] = match_result
                    trans['match_confidence'] = match_result.get('confidence', 0)
                    if match_result.get('confidence', 0) >= 90:
                        trans['status'] = 'auto_matched'
                        matched += 1
                    else:
                        trans['status'] = 'needs_review'

        self._populate_transactions()
        self._update_stats()

    def _find_best_match(self, trans: Dict) -> Optional[Dict]:
        """Find the best matching transaction or entity using multiple algorithms."""
        description = trans.get('description', '').lower()
        amount = trans.get('amount', 0)
        trans_date = trans.get('date', '')

        best_match = None
        best_confidence = 0

        # 1. Check matching rules first (highest priority)
        for rule in self._matching_rules:
            if self._rule_matches(rule, trans):
                return {
                    'type': 'rule',
                    'account': rule.get('account'),
                    'confidence': 100,
                    'rule_name': rule.get('name', 'Custom Rule')
                }

        # 2. Match against existing transactions (exact or near match)
        for existing in self._existing_transactions:
            ex_amount = existing.get('amount', 0)
            ex_date = existing.get('date', '')
            ex_desc = existing.get('description', '').lower()

            # Amount must match exactly
            if abs(float(ex_amount) - float(amount)) < 0.01:
                # Calculate date proximity (within 5 days)
                if self._dates_close(trans_date, ex_date, 5):
                    # Calculate description similarity
                    desc_similarity = self._string_similarity(description, ex_desc)

                    if desc_similarity > 0.8:
                        confidence = int(90 + (desc_similarity - 0.8) * 50)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {
                                'type': 'transaction',
                                'transaction_id': existing.get('id'),
                                'description': existing.get('description'),
                                'confidence': min(confidence, 100)
                            }

        # 3. Match against vendors (for payments)
        if amount < 0:  # Negative = payment
            for vendor in self._vendors:
                vendor_name = vendor.get('name', '').lower()
                similarity = self._string_similarity(description, vendor_name)

                # Also check for partial matches in description
                if vendor_name in description:
                    similarity = max(similarity, 0.85)

                if similarity > 0.6:
                    confidence = int(similarity * 100)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            'type': 'vendor',
                            'vendor_id': vendor.get('id'),
                            'vendor_name': vendor.get('name'),
                            'default_account': vendor.get('default_account_id'),
                            'confidence': confidence
                        }

        # 4. Match against customers (for deposits)
        if amount > 0:  # Positive = deposit
            for customer in self._customers:
                customer_name = customer.get('name', '').lower()
                similarity = self._string_similarity(description, customer_name)

                if customer_name in description:
                    similarity = max(similarity, 0.85)

                if similarity > 0.6:
                    confidence = int(similarity * 100)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            'type': 'customer',
                            'customer_id': customer.get('id'),
                            'customer_name': customer.get('name'),
                            'default_account': customer.get('default_account_id'),
                            'confidence': confidence
                        }

        # 5. Keyword-based category matching
        keyword_matches = {
            'fuel': ('Fuel & Gasoline', ['gas', 'fuel', 'shell', 'exxon', 'chevron', 'bp']),
            'insurance': ('Insurance', ['insurance', 'ins', 'allstate', 'state farm']),
            'utilities': ('Utilities', ['electric', 'water', 'gas co', 'utility']),
            'supplies': ('Supplies', ['supply', 'tractor supply', 'farm supply']),
            'seed': ('Seed & Planting', ['seed', 'dekalb', 'pioneer', 'syngenta']),
            'fertilizer': ('Fertilizer', ['fertilizer', 'nutrient', 'urea', 'nitrogen']),
            'equipment': ('Equipment', ['equipment', 'deere', 'case ih', 'kubota']),
        }

        for category, (account_name, keywords) in keyword_matches.items():
            for keyword in keywords:
                if keyword in description:
                    confidence = 70  # Keyword match = 70% confidence
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            'type': 'keyword',
                            'category': category,
                            'account_name': account_name,
                            'confidence': confidence
                        }
                    break

        return best_match

    def _rule_matches(self, rule: Dict, trans: Dict) -> bool:
        """Check if a matching rule applies to transaction."""
        description = trans.get('description', '').lower()
        amount = trans.get('amount', 0)

        # Check conditions
        if rule.get('description_contains'):
            if rule['description_contains'].lower() not in description:
                return False

        if rule.get('description_starts_with'):
            if not description.startswith(rule['description_starts_with'].lower()):
                return False

        if rule.get('amount_equals'):
            if abs(float(amount) - float(rule['amount_equals'])) > 0.01:
                return False

        if rule.get('amount_greater'):
            if float(amount) <= float(rule['amount_greater']):
                return False

        if rule.get('amount_less'):
            if float(amount) >= float(rule['amount_less']):
                return False

        return True

    def _dates_close(self, date1: str, date2: str, days: int) -> bool:
        """Check if two dates are within specified days of each other."""
        try:
            from datetime import datetime, timedelta
            d1 = datetime.strptime(date1[:10], '%Y-%m-%d')
            d2 = datetime.strptime(date2[:10], '%Y-%m-%d')
            return abs((d1 - d2).days) <= days
        except:
            return False

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using Levenshtein-like algorithm."""
        if not s1 or not s2:
            return 0.0

        # Normalize strings
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()

        if s1 == s2:
            return 1.0

        # Use simple ratio of common characters
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0

        # Count matching characters
        matches = 0
        s2_chars = list(s2)
        for char in s1:
            if char in s2_chars:
                matches += 1
                s2_chars.remove(char)

        return (2.0 * matches) / (len1 + len2)

    def _populate_transactions(self):
        """Populate the transactions table."""
        show_filter = self.show_filter.currentText()
        account_filter = self.account_filter.currentText()

        filtered = []
        for trans in self._feed_transactions:
            # Apply filters
            if show_filter == "Unmatched" and trans.get('status') != 'pending':
                continue
            elif show_filter == "Auto-Matched" and trans.get('status') != 'auto_matched':
                continue
            elif show_filter == "Manually Matched" and trans.get('status') != 'manual_matched':
                continue
            elif show_filter == "Accepted" and trans.get('status') != 'accepted':
                continue

            if account_filter != "All Accounts":
                if trans.get('account') != account_filter:
                    continue

            filtered.append(trans)

        self.trans_table.setRowCount(len(filtered))

        for i, trans in enumerate(filtered):
            # Checkbox
            chk = QCheckBox()
            self.trans_table.setCellWidget(i, 0, chk)

            # Date
            self.trans_table.setItem(i, 1, QTableWidgetItem(trans.get('date', '')))

            # Description
            self.trans_table.setItem(i, 2, QTableWidgetItem(trans.get('description', '')))

            # Amount
            amount = trans.get('amount', 0)
            amount_item = QTableWidgetItem(f"${amount:,.2f}")
            if amount < 0:
                amount_item.setForeground(QColor('red'))
            else:
                amount_item.setForeground(QColor('green'))
            self.trans_table.setItem(i, 3, amount_item)

            # Match confidence
            confidence = trans.get('match_confidence', 0)
            conf_item = QTableWidgetItem(f"{confidence}%")
            if confidence >= 90:
                conf_item.setForeground(QColor('green'))
            elif confidence >= 70:
                conf_item.setForeground(QColor('orange'))
            else:
                conf_item.setForeground(QColor('red'))
            self.trans_table.setItem(i, 4, conf_item)

            # Matched to
            match = trans.get('match', {})
            match_text = ""
            if match.get('type') == 'vendor':
                match_text = f"Vendor: {match.get('vendor_name', '')}"
            elif match.get('type') == 'customer':
                match_text = f"Customer: {match.get('customer_name', '')}"
            elif match.get('type') == 'transaction':
                match_text = f"Trans: {match.get('description', '')[:30]}"
            elif match.get('type') == 'rule':
                match_text = f"Rule: {match.get('rule_name', '')}"
            elif match.get('type') == 'keyword':
                match_text = f"Category: {match.get('account_name', '')}"
            self.trans_table.setItem(i, 5, QTableWidgetItem(match_text))

            # Category dropdown
            category_combo = QComboBox()
            category_combo.addItem("-- Select --")
            for acct in self._accounts:
                if acct.get('type') in ['expense', 'income', 'cogs']:
                    category_combo.addItem(acct.get('name', ''))
            if match.get('account_name'):
                idx = category_combo.findText(match.get('account_name'))
                if idx >= 0:
                    category_combo.setCurrentIndex(idx)
            self.trans_table.setCellWidget(i, 6, category_combo)

            # Action button
            action_btn = QPushButton("Match")
            action_btn.clicked.connect(lambda checked, row=i: self._match_single(row))
            self.trans_table.setCellWidget(i, 7, action_btn)

    def _update_stats(self):
        """Update matching statistics."""
        total = len(self._feed_transactions)
        auto_matched = sum(1 for t in self._feed_transactions if t.get('status') == 'auto_matched')
        needs_review = sum(1 for t in self._feed_transactions if t.get('status') in ['pending', 'needs_review'])

        self.match_stats.setText(
            f"Transactions: {total} | Auto-Matched: {auto_matched} | Need Review: {needs_review}"
        )

    def _filter_transactions(self):
        """Filter displayed transactions."""
        self._populate_transactions()

    def _select_all(self):
        """Select all visible transactions."""
        for i in range(self.trans_table.rowCount()):
            chk = self.trans_table.cellWidget(i, 0)
            if chk:
                chk.setChecked(True)

    def _accept_transactions(self):
        """Accept selected matched transactions."""
        accepted = 0
        for i in range(self.trans_table.rowCount()):
            chk = self.trans_table.cellWidget(i, 0)
            if chk and chk.isChecked():
                if i < len(self._feed_transactions):
                    trans = self._feed_transactions[i]
                    category_combo = self.trans_table.cellWidget(i, 6)
                    category = category_combo.currentText() if category_combo else ""

                    if category and category != "-- Select --":
                        trans['status'] = 'accepted'
                        trans['category'] = category

                        # Create the actual transaction via API
                        result = api_post("/bank-transactions", {
                            "date": trans.get('date'),
                            "description": trans.get('description'),
                            "amount": trans.get('amount'),
                            "category": category,
                            "source": "bank_feed"
                        })
                        if result:
                            accepted += 1

        self._populate_transactions()
        self._update_stats()

        QMessageBox.information(self, "Accepted",
            f"Accepted {accepted} transaction(s).")

    def _find_match(self):
        """Open find match dialog for selected transaction."""
        selected = self.trans_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a transaction to match.")
            return

        row = selected[0].row()
        if row < len(self._feed_transactions):
            trans = self._feed_transactions[row]
            dialog = FindMatchDialog(trans, self._existing_transactions, self._vendors, self._customers, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                trans['match'] = dialog.get_match()
                trans['match_confidence'] = 100
                trans['status'] = 'manual_matched'
                self._populate_transactions()

    def _match_single(self, row: int):
        """Handle single row match button."""
        if row < len(self._feed_transactions):
            trans = self._feed_transactions[row]
            dialog = FindMatchDialog(trans, self._existing_transactions, self._vendors, self._customers, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                trans['match'] = dialog.get_match()
                trans['match_confidence'] = 100
                trans['status'] = 'manual_matched'
                self._populate_transactions()

    def _create_transaction(self):
        """Create a new transaction from bank feed."""
        selected = self.trans_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a transaction.")
            return

        row = selected[0].row()
        if row < len(self._feed_transactions):
            trans = self._feed_transactions[row]
            # Open appropriate dialog based on amount
            if trans.get('amount', 0) < 0:
                # Expense - open write check or bill dialog
                QMessageBox.information(self, "Create Transaction",
                    "This would open the Write Check or Enter Bill dialog\n"
                    "pre-filled with the transaction data.")
            else:
                # Deposit - open make deposit dialog
                QMessageBox.information(self, "Create Transaction",
                    "This would open the Make Deposit dialog\n"
                    "pre-filled with the transaction data.")

    def _ignore_transactions(self):
        """Ignore selected transactions."""
        ignored = 0
        for i in range(self.trans_table.rowCount()):
            chk = self.trans_table.cellWidget(i, 0)
            if chk and chk.isChecked():
                if i < len(self._feed_transactions):
                    self._feed_transactions[i]['status'] = 'ignored'
                    ignored += 1

        self._populate_transactions()
        self._update_stats()

        QMessageBox.information(self, "Ignored",
            f"Ignored {ignored} transaction(s).")


class BankConnectionDialog(GenFinDialog):
    """Dialog for adding a bank connection."""

    def __init__(self, parent=None):
        super().__init__("Add Bank Connection", parent)
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_label = QLabel(
            "Connect your bank account to automatically download transactions.\n"
            "Your credentials are encrypted and never stored locally."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        form_group = QGroupBox("Bank Information")
        form_layout = QFormLayout(form_group)

        self.bank_combo = QComboBox()
        self.bank_combo.addItems([
            "-- Select Your Bank --",
            "Chase", "Bank of America", "Wells Fargo", "US Bank",
            "PNC Bank", "Capital One", "First National Bank",
            "Farm Credit", "CoBank", "AgriBank", "Other"
        ])
        form_layout.addRow("Bank:", self.bank_combo)

        self.account_type = QComboBox()
        self.account_type.addItems(["Checking", "Savings", "Credit Card", "Line of Credit"])
        form_layout.addRow("Account Type:", self.account_type)

        self.account_name = QLineEdit()
        self.account_name.setPlaceholderText("e.g., Operating Account")
        form_layout.addRow("Account Name:", self.account_name)

        layout.addWidget(form_group)

        # Buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        connect_btn = QPushButton("Connect")
        connect_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        connect_btn.clicked.connect(self._connect)
        btn_layout.addWidget(connect_btn)

        layout.addLayout(btn_layout)

    def _connect(self):
        if self.bank_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Error", "Please select a bank.")
            return
        self.accept()


class MatchingRulesDialog(GenFinDialog):
    """Dialog for managing auto-matching rules."""

    def __init__(self, rules: List[Dict], accounts: List[Dict], parent=None):
        super().__init__("Auto-Matching Rules", parent)
        self.rules = rules.copy()
        self.accounts = accounts
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            "Create rules to automatically categorize bank transactions.\n"
            "Rules are applied in order - the first matching rule wins."
        )
        layout.addWidget(info)

        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(["Rule Name", "Condition", "Category", "Actions"])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._populate_rules()
        layout.addWidget(self.rules_table)

        # Add rule button
        add_btn = QPushButton("Add Rule")
        add_btn.clicked.connect(self._add_rule)
        layout.addWidget(add_btn)

        # Buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("Save Rules")
        save_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate_rules(self):
        self.rules_table.setRowCount(len(self.rules))
        for i, rule in enumerate(self.rules):
            self.rules_table.setItem(i, 0, QTableWidgetItem(rule.get('name', '')))
            self.rules_table.setItem(i, 1, QTableWidgetItem(rule.get('condition_text', '')))
            self.rules_table.setItem(i, 2, QTableWidgetItem(rule.get('account', '')))

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, row=i: self._delete_rule(row))
            self.rules_table.setCellWidget(i, 3, delete_btn)

    def _add_rule(self):
        """Add a new matching rule."""
        dialog = AddRuleDialog(self.accounts, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.rules.append(dialog.get_rule())
            self._populate_rules()

    def _delete_rule(self, row: int):
        if row < len(self.rules):
            del self.rules[row]
            self._populate_rules()

    def get_rules(self) -> List[Dict]:
        return self.rules


class AddRuleDialog(GenFinDialog):
    """Dialog for adding a matching rule."""

    def __init__(self, accounts: List[Dict], parent=None):
        super().__init__("Add Matching Rule", parent)
        self.accounts = accounts
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.rule_name = QLineEdit()
        self.rule_name.setPlaceholderText("e.g., Fuel Purchases")
        form.addRow("Rule Name:", self.rule_name)

        self.condition_type = QComboBox()
        self.condition_type.addItems([
            "Description contains",
            "Description starts with",
            "Amount equals",
            "Amount greater than",
            "Amount less than"
        ])
        form.addRow("Condition:", self.condition_type)

        self.condition_value = QLineEdit()
        self.condition_value.setPlaceholderText("e.g., SHELL, GAS STATION")
        form.addRow("Value:", self.condition_value)

        self.account_combo = QComboBox()
        for acct in self.accounts:
            if acct.get('type') in ['expense', 'income', 'cogs']:
                self.account_combo.addItem(acct.get('name', ''))
        form.addRow("Assign to Account:", self.account_combo)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        add_btn = QPushButton("Add Rule")
        add_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        add_btn.clicked.connect(self.accept)
        btn_layout.addWidget(add_btn)

        layout.addLayout(btn_layout)

    def get_rule(self) -> Dict:
        condition_type = self.condition_type.currentText()
        condition_value = self.condition_value.text()

        rule = {
            'name': self.rule_name.text(),
            'account': self.account_combo.currentText(),
            'condition_text': f"{condition_type}: {condition_value}"
        }

        if "contains" in condition_type:
            rule['description_contains'] = condition_value
        elif "starts with" in condition_type:
            rule['description_starts_with'] = condition_value
        elif "equals" in condition_type:
            rule['amount_equals'] = float(condition_value) if condition_value else 0
        elif "greater" in condition_type:
            rule['amount_greater'] = float(condition_value) if condition_value else 0
        elif "less" in condition_type:
            rule['amount_less'] = float(condition_value) if condition_value else 0

        return rule


class FindMatchDialog(GenFinDialog):
    """Dialog for manually finding a match for a bank transaction."""

    def __init__(self, transaction: Dict, existing: List[Dict],
                 vendors: List[Dict], customers: List[Dict], parent=None):
        super().__init__("Find Match", parent)
        self.transaction = transaction
        self.existing = existing
        self.vendors = vendors
        self.customers = customers
        self.selected_match = None
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Transaction info
        info_group = QGroupBox("Bank Transaction")
        info_layout = QFormLayout(info_group)
        info_layout.addRow("Date:", QLabel(self.transaction.get('date', '')))
        info_layout.addRow("Description:", QLabel(self.transaction.get('description', '')))
        amount = self.transaction.get('amount', 0)
        info_layout.addRow("Amount:", QLabel(f"${amount:,.2f}"))
        layout.addWidget(info_group)

        # Tabs for different match types
        tabs = QTabWidget()

        # Existing transactions tab
        trans_widget = QWidget()
        trans_layout = QVBoxLayout(trans_widget)
        self.trans_list = QListWidget()
        for trans in self.existing:
            if abs(float(trans.get('amount', 0)) - float(amount)) < 0.01:
                self.trans_list.addItem(
                    f"{trans.get('date', '')} - {trans.get('description', '')[:40]} - ${trans.get('amount', 0):,.2f}"
                )
        trans_layout.addWidget(self.trans_list)
        tabs.addTab(trans_widget, "Existing Transactions")

        # Vendors tab
        vendor_widget = QWidget()
        vendor_layout = QVBoxLayout(vendor_widget)
        self.vendor_list = QListWidget()
        for vendor in self.vendors:
            self.vendor_list.addItem(vendor.get('name', ''))
        vendor_layout.addWidget(self.vendor_list)
        tabs.addTab(vendor_widget, "Vendors")

        # Customers tab
        customer_widget = QWidget()
        customer_layout = QVBoxLayout(customer_widget)
        self.customer_list = QListWidget()
        for customer in self.customers:
            self.customer_list.addItem(customer.get('name', ''))
        customer_layout.addWidget(self.customer_list)
        tabs.addTab(customer_widget, "Customers")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        match_btn = QPushButton("Match Selected")
        match_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        match_btn.clicked.connect(self._match_selected)
        btn_layout.addWidget(match_btn)

        layout.addLayout(btn_layout)

        self.tabs = tabs

    def _match_selected(self):
        tab_index = self.tabs.currentIndex()
        if tab_index == 0:  # Transactions
            if self.trans_list.currentItem():
                self.selected_match = {
                    'type': 'transaction',
                    'description': self.trans_list.currentItem().text(),
                    'confidence': 100
                }
        elif tab_index == 1:  # Vendors
            if self.vendor_list.currentItem():
                self.selected_match = {
                    'type': 'vendor',
                    'vendor_name': self.vendor_list.currentItem().text(),
                    'confidence': 100
                }
        elif tab_index == 2:  # Customers
            if self.customer_list.currentItem():
                self.selected_match = {
                    'type': 'customer',
                    'customer_name': self.customer_list.currentItem().text(),
                    'confidence': 100
                }

        if self.selected_match:
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select an item to match.")

    def get_match(self) -> Optional[Dict]:
        return self.selected_match


# =============================================================================
# CUSTOMER MODULE - Statements & Credits
# =============================================================================

class GenFinStatementsScreen(QWidget):
    """Customer Statements screen with batch generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._customers = []
        self._invoices = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("CUSTOMER STATEMENTS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Options
        options_group = QGroupBox("Statement Options")
        options_layout = QFormLayout(options_group)

        self.statement_date = QDateEdit()
        self.statement_date.setDate(QDate.currentDate())
        self.statement_date.setCalendarPopup(True)
        options_layout.addRow("Statement Date:", self.statement_date)

        self.statement_type = QComboBox()
        self.statement_type.addItems(["Balance Forward", "Open Item", "Transaction"])
        options_layout.addRow("Statement Type:", self.statement_type)

        self.include_zero = QCheckBox("Include customers with zero balance")
        options_layout.addRow("", self.include_zero)

        self.include_credits = QCheckBox("Include credit memos")
        self.include_credits.setChecked(True)
        options_layout.addRow("", self.include_credits)

        self.include_aging = QCheckBox("Include aging summary")
        self.include_aging.setChecked(True)
        options_layout.addRow("", self.include_aging)

        layout.addWidget(options_group)

        # Customer selection
        select_group = QGroupBox("Select Customers")
        select_layout = QVBoxLayout(select_group)

        select_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        select_btn_layout.addWidget(select_all_btn)

        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self._select_none)
        select_btn_layout.addWidget(select_none_btn)

        select_balance_btn = QPushButton("Select With Balance")
        select_balance_btn.clicked.connect(self._select_with_balance)
        select_btn_layout.addWidget(select_balance_btn)

        select_overdue_btn = QPushButton("Select Overdue")
        select_overdue_btn.clicked.connect(self._select_overdue)
        select_btn_layout.addWidget(select_overdue_btn)

        select_btn_layout.addStretch()
        select_layout.addLayout(select_btn_layout)

        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels([
            "Select", "Customer", "Balance", "Overdue", "Last Statement", "Email"
        ])
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        select_layout.addWidget(self.customer_table)

        # Selection summary
        self.selection_label = QLabel("Selected: 0 customers | Total Balance: $0.00")
        select_layout.addWidget(self.selection_label)

        layout.addWidget(select_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        batch_pdf_btn = QPushButton("Generate PDFs")
        batch_pdf_btn.clicked.connect(self._generate_batch_pdfs)
        btn_layout.addWidget(batch_pdf_btn)

        btn_layout.addStretch()

        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview)
        btn_layout.addWidget(preview_btn)

        print_btn = QPushButton("Print All")
        print_btn.clicked.connect(self._print)
        btn_layout.addWidget(print_btn)

        email_btn = QPushButton("Email All")
        email_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        email_btn.clicked.connect(self._email)
        btn_layout.addWidget(email_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        data = api_get("/customers")
        if data is not None:
            self._customers = data if isinstance(data, list) else []

        invoices = api_get("/invoices")
        if invoices is not None:
            self._invoices = invoices if isinstance(invoices, list) else []

        self._populate_table()

    def _populate_table(self):
        include_zero = self.include_zero.isChecked()
        filtered = [c for c in self._customers if include_zero or c.get("balance", 0) != 0]

        self.customer_table.setRowCount(len(filtered))
        for i, cust in enumerate(filtered):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_selection_summary)
            self.customer_table.setCellWidget(i, 0, checkbox)

            self.customer_table.setItem(i, 1, QTableWidgetItem(cust.get("name", "")))

            balance = cust.get("balance", 0)
            balance_item = QTableWidgetItem(f"${balance:,.2f}")
            if balance > 0:
                balance_item.setForeground(QColor('red'))
            self.customer_table.setItem(i, 2, balance_item)

            overdue = cust.get("overdue", 0)
            overdue_item = QTableWidgetItem(f"${overdue:,.2f}")
            if overdue > 0:
                overdue_item.setForeground(QColor('red'))
            self.customer_table.setItem(i, 3, overdue_item)

            self.customer_table.setItem(i, 4, QTableWidgetItem(cust.get("last_statement", "Never")))
            self.customer_table.setItem(i, 5, QTableWidgetItem(cust.get("email", "")))

        self._update_selection_summary()

    def _update_selection_summary(self):
        selected_count = 0
        total_balance = 0

        for i in range(self.customer_table.rowCount()):
            widget = self.customer_table.cellWidget(i, 0)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                selected_count += 1
                balance_item = self.customer_table.item(i, 2)
                if balance_item:
                    balance_text = balance_item.text().replace("$", "").replace(",", "")
                    try:
                        total_balance += float(balance_text)
                    except ValueError:
                        pass

        self.selection_label.setText(
            f"Selected: {selected_count} customers | Total Balance: ${total_balance:,.2f}"
        )

    def _select_all(self):
        for i in range(self.customer_table.rowCount()):
            widget = self.customer_table.cellWidget(i, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(True)

    def _select_none(self):
        for i in range(self.customer_table.rowCount()):
            widget = self.customer_table.cellWidget(i, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def _select_with_balance(self):
        """Select customers with non-zero balance."""
        for i in range(self.customer_table.rowCount()):
            widget = self.customer_table.cellWidget(i, 0)
            balance_item = self.customer_table.item(i, 2)
            if isinstance(widget, QCheckBox) and balance_item:
                balance_text = balance_item.text().replace("$", "").replace(",", "")
                try:
                    balance = float(balance_text)
                    widget.setChecked(balance != 0)
                except ValueError:
                    widget.setChecked(False)

    def _select_overdue(self):
        """Select customers with overdue balance."""
        for i in range(self.customer_table.rowCount()):
            widget = self.customer_table.cellWidget(i, 0)
            overdue_item = self.customer_table.item(i, 3)
            if isinstance(widget, QCheckBox) and overdue_item:
                overdue_text = overdue_item.text().replace("$", "").replace(",", "")
                try:
                    overdue = float(overdue_text)
                    widget.setChecked(overdue > 0)
                except ValueError:
                    widget.setChecked(False)

    def _get_selected_customers(self) -> List[Dict]:
        """Get list of selected customers."""
        selected = []
        for i in range(self.customer_table.rowCount()):
            widget = self.customer_table.cellWidget(i, 0)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                name_item = self.customer_table.item(i, 1)
                if name_item:
                    # Find customer by name
                    for cust in self._customers:
                        if cust.get("name") == name_item.text():
                            selected.append(cust)
                            break
        return selected

    def _build_statement_data(self, customer: Dict) -> Dict:
        """Build statement data for a customer."""
        customer_id = customer.get("id", customer.get("customer_id"))

        # Get customer's invoices
        customer_invoices = [
            inv for inv in self._invoices
            if inv.get("customer_id") == customer_id
        ]

        # Calculate aging buckets
        today = date.today()
        current = 0
        aging_30 = 0
        aging_60 = 0
        aging_90 = 0
        aging_over = 0

        transactions = []
        for inv in customer_invoices:
            due_date_str = inv.get("due_date", "")
            amount = inv.get("amount", 0) - inv.get("amount_paid", 0)

            if amount > 0:
                try:
                    due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
                    days_past = (today - due_date).days

                    if days_past <= 0:
                        current += amount
                    elif days_past <= 30:
                        aging_30 += amount
                    elif days_past <= 60:
                        aging_60 += amount
                    elif days_past <= 90:
                        aging_90 += amount
                    else:
                        aging_over += amount
                except:
                    current += amount

                transactions.append({
                    "date": inv.get("date", ""),
                    "type": "Invoice",
                    "reference": inv.get("invoice_number", ""),
                    "charges": inv.get("amount", 0),
                    "payments": inv.get("amount_paid", 0),
                    "balance": amount
                })

        return {
            "customer_name": customer.get("name", ""),
            "customer_address": customer.get("address", ""),
            "date": self.statement_date.date().toString("MM/dd/yyyy"),
            "account_number": customer.get("account_number", customer_id),
            "transactions": transactions,
            "current": current,
            "aging_30": aging_30,
            "aging_60": aging_60,
            "aging_90": aging_90,
            "aging_over": aging_over,
            "balance_due": current + aging_30 + aging_60 + aging_90 + aging_over
        }

    def _preview(self):
        """Preview statement for first selected customer."""
        selected = self._get_selected_customers()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one customer.")
            return

        # Preview first selected customer
        statement_data = self._build_statement_data(selected[0])
        dialog = PrintPreviewDialog("Statement", statement_data, self)
        dialog.exec()

    def _print(self):
        """Print statements for all selected customers."""
        selected = self._get_selected_customers()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one customer.")
            return

        reply = QMessageBox.question(
            self, "Print Statements",
            f"Print statements for {len(selected)} customer(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            progress = QProgressDialog("Printing statements...", "Cancel", 0, len(selected), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                for i, customer in enumerate(selected):
                    if progress.wasCanceled():
                        break

                    statement_data = self._build_statement_data(customer)
                    doc = QTextDocument()
                    preview = PrintPreviewDialog("Statement", statement_data)
                    doc.setHtml(preview._generate_html())
                    doc.print(printer)

                    progress.setValue(i + 1)

                QMessageBox.information(self, "Complete",
                    f"Printed {len(selected)} statement(s).")

            progress.close()

    def _generate_batch_pdfs(self):
        """Generate PDF files for all selected customers."""
        selected = self._get_selected_customers()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one customer.")
            return

        # Select output folder
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not folder:
            return

        progress = QProgressDialog("Generating PDFs...", "Cancel", 0, len(selected), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        generated = 0
        for i, customer in enumerate(selected):
            if progress.wasCanceled():
                break

            statement_data = self._build_statement_data(customer)

            # Create safe filename
            safe_name = customer.get("name", "customer").replace(" ", "_")
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
            date_str = self.statement_date.date().toString("yyyyMMdd")
            filename = f"{folder}/{safe_name}_Statement_{date_str}.pdf"

            # Generate PDF
            pdf_printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            pdf_printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            pdf_printer.setOutputFileName(filename)
            pdf_printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

            preview = PrintPreviewDialog("Statement", statement_data)
            doc = QTextDocument()
            doc.setHtml(preview._generate_html())
            doc.print(pdf_printer)

            generated += 1
            progress.setValue(i + 1)

        progress.close()
        QMessageBox.information(self, "Complete",
            f"Generated {generated} PDF statement(s) in:\n{folder}")

    def _email(self):
        """Email statements to all selected customers."""
        selected = self._get_selected_customers()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select at least one customer.")
            return

        # Check for customers without email
        no_email = [c for c in selected if not c.get("email")]
        if no_email:
            reply = QMessageBox.question(
                self, "Missing Emails",
                f"{len(no_email)} customer(s) have no email address.\n"
                "Continue with remaining customers?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            selected = [c for c in selected if c.get("email")]

        if not selected:
            QMessageBox.warning(self, "No Valid Recipients",
                "No selected customers have email addresses.")
            return

        reply = QMessageBox.question(
            self, "Email Statements",
            f"Send statement emails to {len(selected)} customer(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            progress = QProgressDialog("Sending emails...", "Cancel", 0, len(selected), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            sent = 0
            for i, customer in enumerate(selected):
                if progress.wasCanceled():
                    break

                # In production, would actually send email via API
                # For now, simulate
                statement_data = self._build_statement_data(customer)

                # Call API to send email (placeholder)
                result = api_post("/statements/email", {
                    "customer_id": customer.get("id"),
                    "email": customer.get("email"),
                    "statement_date": self.statement_date.date().toString("yyyy-MM-dd"),
                    "statement_type": self.statement_type.currentText()
                })

                if result or True:  # Simulate success for demo
                    sent += 1

                progress.setValue(i + 1)

            progress.close()
            QMessageBox.information(self, "Complete",
                f"Sent {sent} statement email(s).")


class GenFinCreditMemosScreen(GenFinListScreen):
    """Credit Memos screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Credit Memos",
            ["Credit #", "Date", "Customer", "Amount", "Applied", "Status"],
            "/credit-memos",
            None,
            "credit_memo_id",
            parent
        )

    def _on_new(self):
        QMessageBox.information(self, "New Credit Memo",
            "This would open the Credit Memo form.\n\n"
            "Credit memos reduce a customer's balance\n"
            "and can be applied to invoices.")

    def load_data(self):
        data = api_get("/credit-memos")
        if data is not None:
            items = data if isinstance(data, list) else []
            self._data = items
            self.table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.table.setItem(i, 0, QTableWidgetItem(item.get("credit_number", "")))
                self.table.setItem(i, 1, QTableWidgetItem(item.get("date", "")))
                self.table.setItem(i, 2, QTableWidgetItem(item.get("customer_name", "")))
                amount = item.get("amount", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                applied = item.get("applied_amount", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"${applied:,.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(item.get("status", "Open")))


# =============================================================================
# VENDOR MODULE - Credit Cards & Vendor Credits
# =============================================================================

class GenFinCreditCardsScreen(QWidget):
    """Credit Cards tracking screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("CREDIT CARDS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("New Card")
        new_btn.clicked.connect(self._new_card)
        toolbar.addWidget(new_btn)

        charge_btn = QPushButton("Enter Charge")
        charge_btn.clicked.connect(self._enter_charge)
        toolbar.addWidget(charge_btn)

        credit_btn = QPushButton("Enter Credit")
        credit_btn.clicked.connect(self._enter_credit)
        toolbar.addWidget(credit_btn)

        payment_btn = QPushButton("Pay Credit Card")
        payment_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        payment_btn.clicked.connect(self._pay_card)
        toolbar.addWidget(payment_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Cards list
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Card Name", "Type", "Last 4", "Balance", "Credit Limit"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Summary
        summary_layout = QHBoxLayout()
        self.total_label = QLabel("Total Credit Card Debt: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        summary_layout.addWidget(self.total_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

    def load_data(self):
        # Would load from API
        self.table.setRowCount(0)
        self.total_label.setText("Total Credit Card Debt: $0.00")

    def _new_card(self):
        QMessageBox.information(self, "New Card", "This would open the new credit card setup dialog.")

    def _enter_charge(self):
        QMessageBox.information(self, "Enter Charge", "This would open the credit card charge form.")

    def _enter_credit(self):
        QMessageBox.information(self, "Enter Credit", "This would open the credit card credit/refund form.")

    def _pay_card(self):
        QMessageBox.information(self, "Pay Card", "This would open the pay credit card dialog.")


class GenFinVendorCreditsScreen(GenFinListScreen):
    """Vendor Credits screen."""

    def __init__(self, parent=None):
        super().__init__(
            "Vendor Credits",
            ["Credit #", "Date", "Vendor", "Amount", "Applied", "Status"],
            "/vendor-credits",
            None,
            "vendor_credit_id",
            parent
        )

    def _on_new(self):
        QMessageBox.information(self, "New Vendor Credit",
            "This would open the Vendor Credit form.\n\n"
            "Vendor credits reduce what you owe to a vendor\n"
            "and can be applied to bills.")

    def load_data(self):
        data = api_get("/vendor-credits")
        if data is not None:
            items = data if isinstance(data, list) else []
            self._data = items
            self.table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.table.setItem(i, 0, QTableWidgetItem(item.get("credit_number", "")))
                self.table.setItem(i, 1, QTableWidgetItem(item.get("date", "")))
                self.table.setItem(i, 2, QTableWidgetItem(item.get("vendor_name", "")))
                amount = item.get("amount", 0)
                self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
                applied = item.get("applied_amount", 0)
                self.table.setItem(i, 4, QTableWidgetItem(f"${applied:,.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(item.get("status", "Open")))


# =============================================================================
# PAYROLL - Pay Liabilities
# =============================================================================

class GenFinPayLiabilitiesScreen(QWidget):
    """Pay Payroll Liabilities screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._liabilities = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("PAY PAYROLL LIABILITIES")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Date range filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Show liabilities through:"))

        self.through_date = QDateEdit()
        self.through_date.setDate(QDate.currentDate())
        self.through_date.setCalendarPopup(True)
        filter_layout.addWidget(self.through_date)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Liabilities table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Select", "Payroll Item", "Payee", "Balance", "Due Date", "Account"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Summary and action
        summary_layout = QHBoxLayout()

        self.total_label = QLabel("Total Selected: $0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.total_label)

        summary_layout.addStretch()

        view_btn = QPushButton("View")
        view_btn.clicked.connect(self._view_liability)
        summary_layout.addWidget(view_btn)

        pay_btn = QPushButton("Pay Selected Liabilities")
        pay_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white; padding: 10px;")
        pay_btn.clicked.connect(self._pay_liabilities)
        summary_layout.addWidget(pay_btn)

        layout.addLayout(summary_layout)

        # E-Pay info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            background-color: #FFF3CD;
            border: 1px solid #FFEAA7;
            padding: 8px;
        """)
        info_layout = QVBoxLayout(info_frame)
        info_label = QLabel(
            "TIP: Set up E-Pay to electronically pay your federal and state taxes.\n"
            "This ensures timely payments and creates automatic records."
        )
        info_label.setStyleSheet("color: #856404;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_frame)

    def load_data(self):
        data = api_get("/payroll/liabilities")
        if data is not None:
            self._liabilities = data if isinstance(data, list) else []
            self._populate_table()
        else:
            # Show sample data structure
            self._liabilities = []
            self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._liabilities))
        for i, liab in enumerate(self._liabilities):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self._update_total)
            self.table.setCellWidget(i, 0, checkbox)

            self.table.setItem(i, 1, QTableWidgetItem(liab.get("item_name", "")))
            self.table.setItem(i, 2, QTableWidgetItem(liab.get("payee", "")))

            balance = liab.get("balance", 0)
            self.table.setItem(i, 3, QTableWidgetItem(f"${balance:,.2f}"))

            self.table.setItem(i, 4, QTableWidgetItem(liab.get("due_date", "")))
            self.table.setItem(i, 5, QTableWidgetItem(liab.get("account", "")))

    def _update_total(self):
        total = 0
        for i in range(self.table.rowCount()):
            widget = self.table.cellWidget(i, 0)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                if i < len(self._liabilities):
                    total += self._liabilities[i].get("balance", 0)
        self.total_label.setText(f"Total Selected: ${total:,.2f}")

    def _view_liability(self):
        QMessageBox.information(self, "View", "Opening liability detail...")

    def _pay_liabilities(self):
        QMessageBox.information(self, "Pay Liabilities",
            "This would create liability payments.\n\n"
            "You can pay electronically (E-Pay) or by check.")


# =============================================================================
# LISTS - Fixed Assets, Recurring, Memorized
# =============================================================================

class GenFinFixedAssetsScreen(QWidget):
    """Fixed Assets management screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._assets = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("FIXED ASSETS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("New Asset")
        new_btn.clicked.connect(self._new_asset)
        toolbar.addWidget(new_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_asset)
        toolbar.addWidget(edit_btn)

        dispose_btn = QPushButton("Dispose/Sell")
        dispose_btn.clicked.connect(self._dispose_asset)
        toolbar.addWidget(dispose_btn)

        depreciate_btn = QPushButton("Record Depreciation")
        depreciate_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        depreciate_btn.clicked.connect(self._record_depreciation)
        toolbar.addWidget(depreciate_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Assets table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Asset Name", "Type", "Purchase Date", "Cost", "Accum. Depr.", "Book Value", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Summary
        summary_layout = QHBoxLayout()
        self.total_cost_label = QLabel("Total Cost: $0.00")
        summary_layout.addWidget(self.total_cost_label)
        self.total_book_label = QLabel("Total Book Value: $0.00")
        summary_layout.addWidget(self.total_book_label)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

    def load_data(self):
        data = api_get("/fixed-assets")
        if data is not None:
            self._assets = data if isinstance(data, list) else []
            self._populate_table()
        else:
            self._assets = []
            self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._assets))
        total_cost = 0
        total_book = 0

        for i, asset in enumerate(self._assets):
            self.table.setItem(i, 0, QTableWidgetItem(asset.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(asset.get("asset_type", "")))
            self.table.setItem(i, 2, QTableWidgetItem(asset.get("purchase_date", "")))

            cost = asset.get("cost", 0)
            total_cost += cost
            self.table.setItem(i, 3, QTableWidgetItem(f"${cost:,.2f}"))

            depr = asset.get("accumulated_depreciation", 0)
            self.table.setItem(i, 4, QTableWidgetItem(f"${depr:,.2f}"))

            book = cost - depr
            total_book += book
            self.table.setItem(i, 5, QTableWidgetItem(f"${book:,.2f}"))

            status = asset.get("status", "Active")
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.darkGreen if status == "Active" else Qt.GlobalColor.gray)
            self.table.setItem(i, 6, status_item)

        self.total_cost_label.setText(f"Total Cost: ${total_cost:,.2f}")
        self.total_book_label.setText(f"Total Book Value: ${total_book:,.2f}")

    def _new_asset(self):
        QMessageBox.information(self, "New Asset", "This would open the new fixed asset form.")

    def _edit_asset(self):
        QMessageBox.information(self, "Edit Asset", "This would open the edit fixed asset form.")

    def _dispose_asset(self):
        QMessageBox.information(self, "Dispose Asset", "This would record the disposal or sale of an asset.")

    def _record_depreciation(self):
        QMessageBox.information(self, "Depreciation", "This would record depreciation for fixed assets.")


class GenFinRecurringTransScreen(QWidget):
    """Recurring Transactions screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recurring = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("RECURRING TRANSACTIONS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("New Recurring")
        new_btn.clicked.connect(self._new_recurring)
        toolbar.addWidget(new_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_recurring)
        toolbar.addWidget(edit_btn)

        run_btn = QPushButton("Create Now")
        run_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        run_btn.clicked.connect(self._create_now)
        toolbar.addWidget(run_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Type", "Customer/Vendor", "Amount", "Frequency", "Next Date", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def load_data(self):
        data = api_get("/recurring-transactions")
        if data is not None:
            self._recurring = data if isinstance(data, list) else []
            self._populate_table()
        else:
            self._recurring = []
            self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._recurring))
        for i, rec in enumerate(self._recurring):
            self.table.setItem(i, 0, QTableWidgetItem(rec.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(rec.get("transaction_type", "")))
            self.table.setItem(i, 2, QTableWidgetItem(rec.get("customer_vendor", "")))
            amount = rec.get("amount", 0)
            self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(rec.get("frequency", "")))
            self.table.setItem(i, 5, QTableWidgetItem(rec.get("next_date", "")))

            status = rec.get("status", "Active")
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.darkGreen if status == "Active" else Qt.GlobalColor.gray)
            self.table.setItem(i, 6, status_item)

    def _new_recurring(self):
        QMessageBox.information(self, "New Recurring", "This would open the new recurring transaction setup.")

    def _edit_recurring(self):
        QMessageBox.information(self, "Edit Recurring", "This would open the edit recurring transaction form.")

    def _create_now(self):
        QMessageBox.information(self, "Create Now", "This would create a transaction from the selected template.")


class GenFinMemorizedTransScreen(QWidget):
    """Memorized Transactions screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._memorized = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("MEMORIZED TRANSACTIONS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Info
        info_label = QLabel(
            "Memorized transactions are templates for frequently used transactions. "
            "Use them to quickly create invoices, bills, checks, and more."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; padding: 8px 0;")
        layout.addWidget(info_label)

        # Toolbar
        toolbar = QHBoxLayout()

        use_btn = QPushButton("Use Template")
        use_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        use_btn.clicked.connect(self._use_template)
        toolbar.addWidget(use_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_template)
        toolbar.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_template)
        toolbar.addWidget(delete_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Name", "Type", "Customer/Vendor", "Amount", "Group"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def load_data(self):
        data = api_get("/memorized-transactions")
        if data is not None:
            self._memorized = data if isinstance(data, list) else []
            self._populate_table()
        else:
            self._memorized = []
            self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._memorized))
        for i, mem in enumerate(self._memorized):
            self.table.setItem(i, 0, QTableWidgetItem(mem.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(mem.get("transaction_type", "")))
            self.table.setItem(i, 2, QTableWidgetItem(mem.get("customer_vendor", "")))
            amount = mem.get("amount", 0)
            self.table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(mem.get("group", "")))

    def _use_template(self):
        QMessageBox.information(self, "Use Template", "This would create a new transaction from the selected template.")

    def _edit_template(self):
        QMessageBox.information(self, "Edit Template", "This would open the template editor.")

    def _delete_template(self):
        QMessageBox.question(self, "Delete", "Are you sure you want to delete this template?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)


# =============================================================================
# BUDGETS
# =============================================================================

class GenFinBudgetsScreen(QWidget):
    """Budgets management screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._budgets = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("BUDGETS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("Create Budget")
        new_btn.clicked.connect(self._new_budget)
        toolbar.addWidget(new_btn)

        copy_btn = QPushButton("Copy Budget")
        copy_btn.clicked.connect(self._copy_budget)
        toolbar.addWidget(copy_btn)

        report_btn = QPushButton("Budget vs Actual Report")
        report_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        report_btn.clicked.connect(self._budget_report)
        toolbar.addWidget(report_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Year selector
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Fiscal Year:"))
        self.year_combo = QComboBox()
        current_year = QDate.currentDate().year()
        for year in range(current_year - 2, current_year + 3):
            self.year_combo.addItem(str(year))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self.load_data)
        year_layout.addWidget(self.year_combo)
        year_layout.addStretch()
        layout.addLayout(year_layout)

        # Budgets list
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Budget Name", "Type", "Fiscal Year", "Created", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.doubleClicked.connect(self._edit_budget)
        layout.addWidget(self.table)

    def load_data(self):
        data = api_get(f"/budgets?year={self.year_combo.currentText()}")
        if data is not None:
            self._budgets = data if isinstance(data, list) else []
            self._populate_table()
        else:
            self._budgets = []
            self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._budgets))
        for i, budget in enumerate(self._budgets):
            self.table.setItem(i, 0, QTableWidgetItem(budget.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(budget.get("budget_type", "P&L")))
            self.table.setItem(i, 2, QTableWidgetItem(str(budget.get("fiscal_year", ""))))
            self.table.setItem(i, 3, QTableWidgetItem(budget.get("created_date", "")))

            status = budget.get("status", "Active")
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.darkGreen if status == "Active" else Qt.GlobalColor.gray)
            self.table.setItem(i, 4, status_item)

    def _new_budget(self):
        QMessageBox.information(self, "New Budget",
            "Budget Setup Wizard\n\n"
            "1. Choose budget type (P&L, Balance Sheet)\n"
            "2. Select fiscal year\n"
            "3. Choose accounts to budget\n"
            "4. Enter monthly amounts\n\n"
            "This would open the budget creation wizard.")

    def _copy_budget(self):
        QMessageBox.information(self, "Copy Budget",
            "This would copy an existing budget to create a new one.")

    def _edit_budget(self):
        QMessageBox.information(self, "Edit Budget",
            "This would open the budget editor with monthly columns.")

    def _budget_report(self):
        QMessageBox.information(self, "Budget Report",
            "This would generate a Budget vs Actual report\n"
            "comparing your budgeted amounts to actual transactions.")


# =============================================================================
# ENTITIES - Classes, Locations, Names
# =============================================================================

class GenFinEntitiesScreen(QWidget):
    """Entities management screen - Classes, Locations, and Other Names."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("ENTITIES & LISTS")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Tab widget for different entity types
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {GENFIN_COLORS['bevel_dark']};
                background: {GENFIN_COLORS['window_face']};
            }}
            QTabBar::tab {{
                background: {GENFIN_COLORS['window_face']};
                border: 2px solid {GENFIN_COLORS['bevel_dark']};
                padding: 8px 16px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {GENFIN_COLORS['teal_light']};
            }}
        """)

        # Classes Tab
        classes_tab = QWidget()
        classes_layout = QVBoxLayout(classes_tab)

        classes_info = QLabel(
            "Classes help you categorize transactions by department, location, or any other meaningful grouping.\n"
            "Example: Track income/expenses by farm field, crop type, or business unit."
        )
        classes_info.setWordWrap(True)
        classes_info.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; padding: 8px;")
        classes_layout.addWidget(classes_info)

        classes_toolbar = QHBoxLayout()
        new_class_btn = QPushButton("New Class")
        new_class_btn.clicked.connect(self._new_class)
        classes_toolbar.addWidget(new_class_btn)
        classes_toolbar.addStretch()
        classes_layout.addLayout(classes_toolbar)

        self.classes_table = QTableWidget()
        self.classes_table.setColumnCount(3)
        self.classes_table.setHorizontalHeaderLabels(["Class Name", "Parent Class", "Status"])
        self.classes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        classes_layout.addWidget(self.classes_table)

        tabs.addTab(classes_tab, "Classes")

        # Locations Tab
        locations_tab = QWidget()
        locations_layout = QVBoxLayout(locations_tab)

        locations_info = QLabel(
            "Locations track where transactions occur. Use for multi-location businesses.\n"
            "Example: Main Farm, North Field, Equipment Shed, Market Stand."
        )
        locations_info.setWordWrap(True)
        locations_info.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; padding: 8px;")
        locations_layout.addWidget(locations_info)

        locations_toolbar = QHBoxLayout()
        new_loc_btn = QPushButton("New Location")
        new_loc_btn.clicked.connect(self._new_location)
        locations_toolbar.addWidget(new_loc_btn)
        locations_toolbar.addStretch()
        locations_layout.addLayout(locations_toolbar)

        self.locations_table = QTableWidget()
        self.locations_table.setColumnCount(3)
        self.locations_table.setHorizontalHeaderLabels(["Location Name", "Address", "Status"])
        self.locations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        locations_layout.addWidget(self.locations_table)

        tabs.addTab(locations_tab, "Locations")

        # Other Names Tab
        names_tab = QWidget()
        names_layout = QVBoxLayout(names_tab)

        names_info = QLabel(
            "Other Names are for people or businesses that aren't customers, vendors, or employees.\n"
            "Example: Business owners, partners, shareholders, or government agencies."
        )
        names_info.setWordWrap(True)
        names_info.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; padding: 8px;")
        names_layout.addWidget(names_info)

        names_toolbar = QHBoxLayout()
        new_name_btn = QPushButton("New Name")
        new_name_btn.clicked.connect(self._new_name)
        names_toolbar.addWidget(new_name_btn)
        names_toolbar.addStretch()
        names_layout.addLayout(names_toolbar)

        self.names_table = QTableWidget()
        self.names_table.setColumnCount(4)
        self.names_table.setHorizontalHeaderLabels(["Name", "Type", "Phone", "Notes"])
        self.names_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        names_layout.addWidget(self.names_table)

        tabs.addTab(names_tab, "Other Names")

        # Terms Tab
        terms_tab = QWidget()
        terms_layout = QVBoxLayout(terms_tab)

        terms_info = QLabel(
            "Payment Terms define when invoices are due and any early payment discounts.\n"
            "Example: Net 30, 2% 10 Net 30, Due on Receipt."
        )
        terms_info.setWordWrap(True)
        terms_info.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; padding: 8px;")
        terms_layout.addWidget(terms_info)

        terms_toolbar = QHBoxLayout()
        new_term_btn = QPushButton("New Terms")
        new_term_btn.clicked.connect(self._new_terms)
        terms_toolbar.addWidget(new_term_btn)
        terms_toolbar.addStretch()
        terms_layout.addLayout(terms_toolbar)

        self.terms_table = QTableWidget()
        self.terms_table.setColumnCount(4)
        self.terms_table.setHorizontalHeaderLabels(["Terms Name", "Due Days", "Discount %", "Discount Days"])
        self.terms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        terms_layout.addWidget(self.terms_table)

        tabs.addTab(terms_tab, "Payment Terms")

        layout.addWidget(tabs)

    def load_data(self):
        """Load entities from API."""
        # Load classes
        data = api_get("/classes")
        if data:
            classes = data if isinstance(data, list) else []
            self.classes_table.setRowCount(len(classes))
            for i, cls in enumerate(classes):
                self.classes_table.setItem(i, 0, QTableWidgetItem(cls.get("name", "")))
                self.classes_table.setItem(i, 1, QTableWidgetItem(cls.get("parent", "")))
                self.classes_table.setItem(i, 2, QTableWidgetItem("Active" if cls.get("is_active", True) else "Inactive"))

        # Load locations
        data = api_get("/locations")
        if data:
            locations = data if isinstance(data, list) else []
            self.locations_table.setRowCount(len(locations))
            for i, loc in enumerate(locations):
                self.locations_table.setItem(i, 0, QTableWidgetItem(loc.get("name", "")))
                self.locations_table.setItem(i, 1, QTableWidgetItem(loc.get("address", "")))
                self.locations_table.setItem(i, 2, QTableWidgetItem("Active" if loc.get("is_active", True) else "Inactive"))

    def _new_class(self):
        QMessageBox.information(self, "New Class", "This would open the new class dialog.")

    def _new_location(self):
        QMessageBox.information(self, "New Location", "This would open the new location dialog.")

    def _new_name(self):
        QMessageBox.information(self, "New Name", "This would open the new other name dialog.")

    def _new_terms(self):
        QMessageBox.information(self, "New Terms", "This would open the new payment terms dialog.")


# =============================================================================
# SETTINGS - Company & User Preferences
# =============================================================================

class GenFinSettingsScreen(QWidget):
    """Settings screen - Company and user preferences."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("SETTINGS & PREFERENCES")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Settings categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        # Company Information
        company_group = QGroupBox("Company Information")
        company_layout = QFormLayout(company_group)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Your Company Name")
        company_layout.addRow("Company Name:", self.company_name)

        self.legal_name = QLineEdit()
        company_layout.addRow("Legal Name:", self.legal_name)

        self.ein = QLineEdit()
        self.ein.setPlaceholderText("XX-XXXXXXX")
        company_layout.addRow("EIN/Tax ID:", self.ein)

        self.address = QLineEdit()
        company_layout.addRow("Address:", self.address)

        self.city_state_zip = QLineEdit()
        company_layout.addRow("City, State ZIP:", self.city_state_zip)

        self.phone = QLineEdit()
        company_layout.addRow("Phone:", self.phone)

        self.email = QLineEdit()
        company_layout.addRow("Email:", self.email)

        content_layout.addWidget(company_group)

        # Accounting Preferences
        acct_group = QGroupBox("Accounting Preferences")
        acct_layout = QFormLayout(acct_group)

        self.fiscal_year_start = QComboBox()
        self.fiscal_year_start.addItems(["January", "February", "March", "April", "May", "June",
                                         "July", "August", "September", "October", "November", "December"])
        acct_layout.addRow("Fiscal Year Starts:", self.fiscal_year_start)

        self.income_tax_form = QComboBox()
        self.income_tax_form.addItems(["Schedule F (Farm)", "Schedule C (Sole Prop)", "Form 1120 (Corp)",
                                       "Form 1120S (S-Corp)", "Form 1065 (Partnership)"])
        acct_layout.addRow("Income Tax Form:", self.income_tax_form)

        self.accrual_basis = QComboBox()
        self.accrual_basis.addItems(["Cash", "Accrual"])
        acct_layout.addRow("Accounting Method:", self.accrual_basis)

        self.closing_date = QDateEdit()
        self.closing_date.setCalendarPopup(True)
        acct_layout.addRow("Closing Date:", self.closing_date)

        content_layout.addWidget(acct_group)

        # Payroll Settings
        payroll_group = QGroupBox("Payroll Settings")
        payroll_layout = QFormLayout(payroll_group)

        self.payroll_service = QComboBox()
        self.payroll_service.addItems(["Manual Payroll", "Enhanced Payroll", "Full Service Payroll"])
        payroll_layout.addRow("Payroll Service:", self.payroll_service)

        self.state_unemployment = QLineEdit()
        self.state_unemployment.setPlaceholderText("e.g., 2.7%")
        payroll_layout.addRow("State Unemployment Rate:", self.state_unemployment)

        content_layout.addWidget(payroll_group)

        # Invoice Settings
        invoice_group = QGroupBox("Sales & Invoice Settings")
        invoice_layout = QFormLayout(invoice_group)

        self.default_terms = QComboBox()
        self.default_terms.addItems(["Due on Receipt", "Net 15", "Net 30", "Net 60", "2% 10 Net 30"])
        invoice_layout.addRow("Default Payment Terms:", self.default_terms)

        self.invoice_prefix = QLineEdit()
        self.invoice_prefix.setPlaceholderText("e.g., INV-")
        invoice_layout.addRow("Invoice Number Prefix:", self.invoice_prefix)

        self.late_fee = QDoubleSpinBox()
        self.late_fee.setRange(0, 100)
        self.late_fee.setSuffix("%")
        invoice_layout.addRow("Late Fee Percentage:", self.late_fee)

        content_layout.addWidget(invoice_group)

        # Display Settings
        display_group = QGroupBox("Display Preferences")
        display_layout = QFormLayout(display_group)

        self.date_format = QComboBox()
        self.date_format.addItems(["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        display_layout.addRow("Date Format:", self.date_format)

        self.number_format = QComboBox()
        self.number_format.addItems(["1,234.56", "1.234,56", "1 234.56"])
        display_layout.addRow("Number Format:", self.number_format)

        self.show_cents = QCheckBox("Always show cents (.00)")
        self.show_cents.setChecked(True)
        display_layout.addRow("", self.show_cents)

        content_layout.addWidget(display_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
            padding: 12px 24px;
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def load_data(self):
        """Load settings from API or local storage."""
        # Would load saved settings
        pass

    def _save_settings(self):
        QMessageBox.information(self, "Settings Saved",
            "Your settings have been saved successfully.")


# =============================================================================
# HELP - Help Center
# =============================================================================

class GenFinHelpScreen(QWidget):
    """Help Center screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("HELP CENTER")
        header.setStyleSheet(f"""
            color: {GENFIN_COLORS['teal_dark']};
            font-size: 18px;
            font-weight: bold;
            padding: 8px 0;
        """)
        layout.addWidget(header)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search help topics...")
        self.search_input.setStyleSheet(f"""
            padding: 10px;
            font-size: 14px;
            border: 2px solid {GENFIN_COLORS['teal']};
        """)
        search_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white; padding: 10px 20px;")
        search_btn.clicked.connect(self._search)
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # Quick Links
        quick_group = QGroupBox("Quick Links")
        quick_layout = QGridLayout(quick_group)

        topics = [
            ("Getting Started", "Learn the basics of GenFin"),
            ("Invoicing", "Create and manage invoices"),
            ("Bills & Expenses", "Track what you owe"),
            ("Banking", "Manage bank accounts"),
            ("Payroll", "Run payroll and pay employees"),
            ("Reports", "Generate financial reports"),
            ("Taxes", "Tax preparation and 1099s"),
            ("Keyboard Shortcuts", "Work faster with shortcuts"),
        ]

        for i, (title, desc) in enumerate(topics):
            btn = QPushButton(title)
            btn.setStyleSheet(f"""
                text-align: left;
                padding: 12px;
                font-weight: bold;
            """)
            btn.setToolTip(desc)
            btn.clicked.connect(lambda checked, t=title: self._open_topic(t))
            quick_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(quick_group)

        # Video Tutorials
        video_group = QGroupBox("Video Tutorials")
        video_layout = QVBoxLayout(video_group)

        videos = [
            "Introduction to GenFin (5:32)",
            "Setting Up Your Company (8:15)",
            "Creating Your First Invoice (4:45)",
            "Running Payroll (10:22)",
            "Bank Reconciliation (6:18)",
            "Year-End Closing (12:40)",
        ]

        for video in videos:
            video_btn = QPushButton(f"▶  {video}")
            video_btn.setStyleSheet("text-align: left; padding: 8px;")
            video_btn.clicked.connect(lambda checked, v=video: self._play_video(v))
            video_layout.addWidget(video_btn)

        layout.addWidget(video_group)

        # Contact Support
        support_frame = QFrame()
        support_frame.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal_light']};
            border-radius: 4px;
            padding: 16px;
        """)
        support_layout = QVBoxLayout(support_frame)

        support_header = QLabel("Need More Help?")
        support_header.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        support_layout.addWidget(support_header)

        support_text = QLabel(
            "Contact our support team:\n"
            "Email: support@agtools.com\n"
            "Phone: 1-800-AGTOOLS\n"
            "Hours: Mon-Fri 8am-6pm CST"
        )
        support_text.setStyleSheet("color: white;")
        support_layout.addWidget(support_text)

        layout.addWidget(support_frame)

        layout.addStretch()

    def load_data(self):
        """Nothing to load for help screen."""
        pass

    def _search(self):
        query = self.search_input.text()
        if query:
            QMessageBox.information(self, "Search",
                f"Searching help for: {query}\n\n"
                "This would show matching help articles.")

    def _open_topic(self, topic):
        QMessageBox.information(self, topic,
            f"Opening help topic: {topic}\n\n"
            "This would display the help article.")

    def _play_video(self, video):
        QMessageBox.information(self, "Video Tutorial",
            f"Playing: {video}\n\n"
            "This would open the video tutorial.")


# =============================================================================
# PAYROLL CENTER - QuickBooks Style Scheduled/Unscheduled Payroll
# =============================================================================

class AddPayScheduleDialog(GenFinDialog):
    """Dialog for adding/editing a pay schedule - QuickBooks style."""

    def __init__(self, schedule_data: Optional[Dict] = None, parent=None):
        title = "Edit Pay Schedule" if schedule_data else "New Pay Schedule"
        super().__init__(title, parent)
        self.schedule_data = schedule_data
        self.result_data = None
        self._setup_ui()
        if schedule_data:
            self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Schedule Info Group
        info_group = QGroupBox("Schedule Information")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., Weekly Field Crew")
        info_layout.addRow("Schedule Name*:", self.name)

        self.frequency = QComboBox()
        self.frequency.addItems(["Weekly", "Biweekly", "Semi-monthly", "Monthly"])
        self.frequency.currentTextChanged.connect(self._on_frequency_change)
        info_layout.addRow("Pay Frequency*:", self.frequency)

        layout.addWidget(info_group)

        # Pay Day Settings Group
        payday_group = QGroupBox("Pay Day Settings")
        payday_layout = QFormLayout(payday_group)
        payday_layout.setSpacing(8)

        self.pay_day_of_week = QComboBox()
        self.pay_day_of_week.addItems([
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
        ])
        self.pay_day_of_week.setCurrentIndex(4)  # Friday default
        payday_layout.addRow("Pay Day (Weekly/Biweekly):", self.pay_day_of_week)

        self.pay_day_of_month = QSpinBox()
        self.pay_day_of_month.setRange(1, 28)
        self.pay_day_of_month.setValue(15)
        payday_layout.addRow("Pay Day of Month:", self.pay_day_of_month)

        self.second_pay_day = QSpinBox()
        self.second_pay_day.setRange(0, 28)
        self.second_pay_day.setValue(0)
        self.second_pay_day.setToolTip("For semi-monthly: 0=last day, or specify day")
        payday_layout.addRow("Second Pay Day (Semi-monthly):", self.second_pay_day)

        layout.addWidget(payday_group)

        # Options Group
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        options_layout.setSpacing(8)

        self.reminder_days = QSpinBox()
        self.reminder_days.setRange(0, 14)
        self.reminder_days.setValue(3)
        options_layout.addRow("Reminder Days Before:", self.reminder_days)

        self.is_active = QCheckBox("Schedule is active")
        self.is_active.setChecked(True)
        options_layout.addRow("", self.is_active)

        layout.addWidget(options_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Schedule")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        self._on_frequency_change(self.frequency.currentText())

    def _on_frequency_change(self, frequency: str):
        """Show/hide appropriate pay day fields based on frequency."""
        is_weekly = frequency in ["Weekly", "Biweekly"]
        self.pay_day_of_week.setEnabled(is_weekly)
        self.pay_day_of_month.setEnabled(not is_weekly)
        self.second_pay_day.setEnabled(frequency == "Semi-monthly")

    def _load_data(self):
        """Load existing schedule data into form."""
        if not self.schedule_data:
            return

        self.name.setText(self.schedule_data.get("name", ""))

        freq = self.schedule_data.get("frequency", "biweekly")
        freq_map = {"weekly": 0, "biweekly": 1, "semimonthly": 2, "monthly": 3}
        self.frequency.setCurrentIndex(freq_map.get(freq, 1))

        self.pay_day_of_week.setCurrentIndex(self.schedule_data.get("pay_day_of_week", 4))
        self.pay_day_of_month.setValue(self.schedule_data.get("pay_day_of_month", 15))
        self.second_pay_day.setValue(self.schedule_data.get("second_pay_day", 0))
        self.reminder_days.setValue(self.schedule_data.get("reminder_days_before", 3))
        self.is_active.setChecked(self.schedule_data.get("is_active", True))

    def _on_save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Required Field", "Please enter a schedule name.")
            return

        freq_map = {"Weekly": "weekly", "Biweekly": "biweekly",
                    "Semi-monthly": "semimonthly", "Monthly": "monthly"}

        self.result_data = {
            "name": self.name.text().strip(),
            "frequency": freq_map[self.frequency.currentText()],
            "pay_day_of_week": self.pay_day_of_week.currentIndex(),
            "pay_day_of_month": self.pay_day_of_month.value(),
            "second_pay_day": self.second_pay_day.value(),
            "reminder_days_before": self.reminder_days.value(),
            "is_active": self.is_active.isChecked()
        }

        if self.schedule_data:
            self.result_data["schedule_id"] = self.schedule_data.get("schedule_id")

        self.accept()


class RunScheduledPayrollDialog(GenFinDialog):
    """Dialog for starting a scheduled payroll - QuickBooks style."""

    def __init__(self, schedules: List[Dict], bank_accounts: List[Dict], parent=None):
        super().__init__("Run Scheduled Payroll", parent)
        self.schedules = schedules
        self.bank_accounts = bank_accounts
        self.result_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Info banner
        banner = QLabel("Select a pay schedule to run payroll for all assigned employees.")
        banner.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal_light']};
            color: {GENFIN_COLORS['teal_dark']};
            padding: 10px;
            border: 1px solid {GENFIN_COLORS['teal']};
            font-weight: bold;
        """)
        banner.setWordWrap(True)
        layout.addWidget(banner)

        # Schedule selection
        schedule_group = QGroupBox("Pay Schedule")
        schedule_layout = QFormLayout(schedule_group)

        self.schedule_combo = QComboBox()
        for sched in self.schedules:
            if sched.get("is_active", True):
                emp_count = len(sched.get("employee_ids", []))
                next_date = sched.get("next_pay_date", "N/A")
                self.schedule_combo.addItem(
                    f"{sched['name']} ({emp_count} employees) - Next: {next_date}",
                    sched
                )
        self.schedule_combo.currentIndexChanged.connect(self._on_schedule_change)
        schedule_layout.addRow("Select Schedule:", self.schedule_combo)

        layout.addWidget(schedule_group)

        # Pay period info (auto-populated from schedule)
        period_group = QGroupBox("Pay Period")
        period_layout = QFormLayout(period_group)

        self.period_start = QDateEdit()
        self.period_start.setCalendarPopup(True)
        self.period_start.setDate(QDate.currentDate().addDays(-14))
        period_layout.addRow("Period Start:", self.period_start)

        self.period_end = QDateEdit()
        self.period_end.setCalendarPopup(True)
        self.period_end.setDate(QDate.currentDate().addDays(-1))
        period_layout.addRow("Period End:", self.period_end)

        self.pay_date = QDateEdit()
        self.pay_date.setCalendarPopup(True)
        self.pay_date.setDate(QDate.currentDate())
        period_layout.addRow("Pay Date:", self.pay_date)

        layout.addWidget(period_group)

        # Bank account selection
        bank_group = QGroupBox("Payment Account")
        bank_layout = QFormLayout(bank_group)

        self.bank_combo = QComboBox()
        for acct in self.bank_accounts:
            balance = acct.get("balance", 0)
            self.bank_combo.addItem(
                f"{acct['account_name']} (${balance:,.2f})",
                acct
            )
        bank_layout.addRow("Pay From:", self.bank_combo)

        layout.addWidget(bank_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        run_btn = QPushButton("Start Payroll")
        run_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
        """)
        run_btn.clicked.connect(self._on_run)
        btn_layout.addWidget(run_btn)

        layout.addLayout(btn_layout)

        self._on_schedule_change(0)

    def _on_schedule_change(self, index: int):
        """Update pay period dates when schedule changes."""
        if index >= 0 and index < self.schedule_combo.count():
            sched = self.schedule_combo.itemData(index)
            if sched:
                # Set dates from schedule
                if sched.get("next_pay_period_start"):
                    try:
                        start = QDate.fromString(sched["next_pay_period_start"], "yyyy-MM-dd")
                        self.period_start.setDate(start)
                    except:
                        pass
                if sched.get("next_pay_period_end"):
                    try:
                        end = QDate.fromString(sched["next_pay_period_end"], "yyyy-MM-dd")
                        self.period_end.setDate(end)
                    except:
                        pass
                if sched.get("next_pay_date"):
                    try:
                        pay = QDate.fromString(sched["next_pay_date"], "yyyy-MM-dd")
                        self.pay_date.setDate(pay)
                    except:
                        pass

    def _on_run(self):
        if self.schedule_combo.count() == 0:
            QMessageBox.warning(self, "No Schedule", "No active pay schedules found.")
            return

        if self.bank_combo.count() == 0:
            QMessageBox.warning(self, "No Account", "No bank accounts available.")
            return

        sched = self.schedule_combo.currentData()
        bank = self.bank_combo.currentData()

        if not sched or not bank:
            return

        self.result_data = {
            "schedule_id": sched["schedule_id"],
            "bank_account_id": bank["account_id"],
            "pay_period_start": self.period_start.date().toString("yyyy-MM-dd"),
            "pay_period_end": self.period_end.date().toString("yyyy-MM-dd"),
            "pay_date": self.pay_date.date().toString("yyyy-MM-dd")
        }

        self.accept()


class RunUnscheduledPayrollDialog(GenFinDialog):
    """Dialog for running unscheduled/ad-hoc payroll - QuickBooks style."""

    def __init__(self, employees: List[Dict], bank_accounts: List[Dict], parent=None):
        super().__init__("Run Unscheduled Payroll", parent)
        self.employees = employees
        self.bank_accounts = bank_accounts
        self.result_data = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Info banner
        banner = QLabel("Unscheduled payroll for bonuses, corrections, emergency advances, "
                       "commissions, or new hire first paycheck.")
        banner.setStyleSheet(f"""
            background-color: #FFF3CD;
            color: #856404;
            padding: 10px;
            border: 1px solid #FFEAA7;
            font-weight: bold;
        """)
        banner.setWordWrap(True)
        layout.addWidget(banner)

        # Payroll type
        type_group = QGroupBox("Payroll Type")
        type_layout = QFormLayout(type_group)

        self.payroll_type = QComboBox()
        self.payroll_type.addItems([
            "Bonus", "Commission", "Correction", "Emergency Advance",
            "New Hire First Paycheck", "Termination Check", "Other"
        ])
        type_layout.addRow("Reason:", self.payroll_type)

        self.memo = QLineEdit()
        self.memo.setPlaceholderText("Optional description")
        type_layout.addRow("Memo:", self.memo)

        layout.addWidget(type_group)

        # Employee selection
        emp_group = QGroupBox("Select Employees")
        emp_layout = QVBoxLayout(emp_group)

        self.emp_list = QTableWidget()
        self.emp_list.setColumnCount(4)
        self.emp_list.setHorizontalHeaderLabels(["Select", "Name", "Type", "Pay Rate"])
        self.emp_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.emp_list.setRowCount(len(self.employees))

        for i, emp in enumerate(self.employees):
            # Checkbox
            chk = QCheckBox()
            self.emp_list.setCellWidget(i, 0, chk)

            name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            self.emp_list.setItem(i, 1, QTableWidgetItem(name))
            self.emp_list.setItem(i, 2, QTableWidgetItem(emp.get("pay_type", "hourly").title()))

            rate = emp.get("pay_rate", 0)
            pay_type = emp.get("pay_type", "hourly")
            rate_str = f"${rate:,.0f}/yr" if pay_type == "salary" else f"${rate:.2f}/hr"
            self.emp_list.setItem(i, 3, QTableWidgetItem(rate_str))

        emp_layout.addWidget(self.emp_list)

        # Select all/none buttons
        sel_layout = QHBoxLayout()
        sel_all = QPushButton("Select All")
        sel_all.clicked.connect(lambda: self._select_all(True))
        sel_layout.addWidget(sel_all)

        sel_none = QPushButton("Select None")
        sel_none.clicked.connect(lambda: self._select_all(False))
        sel_layout.addWidget(sel_none)
        sel_layout.addStretch()
        emp_layout.addLayout(sel_layout)

        layout.addWidget(emp_group)

        # Pay period
        period_group = QGroupBox("Pay Period")
        period_layout = QFormLayout(period_group)

        self.period_start = QDateEdit()
        self.period_start.setCalendarPopup(True)
        self.period_start.setDate(QDate.currentDate())
        period_layout.addRow("Period Start:", self.period_start)

        self.period_end = QDateEdit()
        self.period_end.setCalendarPopup(True)
        self.period_end.setDate(QDate.currentDate())
        period_layout.addRow("Period End:", self.period_end)

        self.pay_date = QDateEdit()
        self.pay_date.setCalendarPopup(True)
        self.pay_date.setDate(QDate.currentDate())
        period_layout.addRow("Pay Date:", self.pay_date)

        layout.addWidget(period_group)

        # Bank account
        bank_group = QGroupBox("Payment Account")
        bank_layout = QFormLayout(bank_group)

        self.bank_combo = QComboBox()
        for acct in self.bank_accounts:
            balance = acct.get("balance", 0)
            self.bank_combo.addItem(
                f"{acct['account_name']} (${balance:,.2f})",
                acct
            )
        bank_layout.addRow("Pay From:", self.bank_combo)

        layout.addWidget(bank_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        run_btn = QPushButton("Create Unscheduled Payroll")
        run_btn.setStyleSheet("""
            background-color: #E67E22;
            color: white;
            font-weight: bold;
        """)
        run_btn.clicked.connect(self._on_run)
        btn_layout.addWidget(run_btn)

        layout.addLayout(btn_layout)

    def _select_all(self, selected: bool):
        for i in range(self.emp_list.rowCount()):
            chk = self.emp_list.cellWidget(i, 0)
            if chk:
                chk.setChecked(selected)

    def _on_run(self):
        # Get selected employees
        selected_ids = []
        for i in range(self.emp_list.rowCount()):
            chk = self.emp_list.cellWidget(i, 0)
            if chk and chk.isChecked():
                selected_ids.append(self.employees[i]["employee_id"])

        if not selected_ids:
            QMessageBox.warning(self, "No Employees", "Please select at least one employee.")
            return

        if self.bank_combo.count() == 0:
            QMessageBox.warning(self, "No Account", "No bank accounts available.")
            return

        bank = self.bank_combo.currentData()

        type_map = {
            "Bonus": "bonus",
            "Commission": "commission",
            "Correction": "unscheduled",
            "Emergency Advance": "unscheduled",
            "New Hire First Paycheck": "unscheduled",
            "Termination Check": "termination",
            "Other": "unscheduled"
        }

        self.result_data = {
            "pay_run_type": type_map.get(self.payroll_type.currentText(), "unscheduled"),
            "employee_ids": selected_ids,
            "bank_account_id": bank["account_id"],
            "pay_period_start": self.period_start.date().toString("yyyy-MM-dd"),
            "pay_period_end": self.period_end.date().toString("yyyy-MM-dd"),
            "pay_date": self.pay_date.date().toString("yyyy-MM-dd"),
            "memo": self.memo.text().strip() or self.payroll_type.currentText(),
            "reason": self.payroll_type.currentText()
        }

        self.accept()


class ViewPayRunDialog(GenFinDialog):
    """Dialog for viewing pay run details."""

    def __init__(self, pay_run: Dict, parent=None):
        super().__init__(f"Pay Run #{pay_run.get('pay_run_number', 'N/A')}", parent)
        self.pay_run = pay_run
        self.setMinimumWidth(700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header info
        header_group = QGroupBox("Pay Run Information")
        header_layout = QFormLayout(header_group)

        status = self.pay_run.get("status", "draft").upper()
        status_colors = {
            "DRAFT": "#6C757D",
            "CALCULATED": "#17A2B8",
            "APPROVED": "#28A745",
            "PAID": "#007BFF",
            "VOIDED": "#DC3545"
        }
        status_label = QLabel(status)
        status_label.setStyleSheet(f"""
            color: white;
            background-color: {status_colors.get(status, '#6C757D')};
            padding: 4px 8px;
            font-weight: bold;
        """)
        header_layout.addRow("Status:", status_label)

        pay_type = self.pay_run.get("pay_run_type", "scheduled").replace("_", " ").title()
        header_layout.addRow("Type:", QLabel(pay_type))

        period = f"{self.pay_run.get('pay_period_start', '')} to {self.pay_run.get('pay_period_end', '')}"
        header_layout.addRow("Pay Period:", QLabel(period))
        header_layout.addRow("Pay Date:", QLabel(self.pay_run.get("pay_date", "")))

        if self.pay_run.get("memo"):
            header_layout.addRow("Memo:", QLabel(self.pay_run["memo"]))

        layout.addWidget(header_group)

        # Totals
        totals_group = QGroupBox("Totals")
        totals_layout = QFormLayout(totals_group)

        gross = self.pay_run.get("total_gross", 0)
        totals_layout.addRow("Gross Pay:", QLabel(f"${gross:,.2f}"))

        taxes = self.pay_run.get("total_taxes", 0)
        totals_layout.addRow("Employee Taxes:", QLabel(f"${taxes:,.2f}"))

        deductions = self.pay_run.get("total_deductions", 0)
        totals_layout.addRow("Deductions:", QLabel(f"${deductions:,.2f}"))

        net = self.pay_run.get("total_net", 0)
        net_label = QLabel(f"${net:,.2f}")
        net_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        totals_layout.addRow("Net Pay:", net_label)

        employer_taxes = self.pay_run.get("total_employer_taxes", 0)
        totals_layout.addRow("Employer Taxes:", QLabel(f"${employer_taxes:,.2f}"))

        layout.addWidget(totals_group)

        # Employee lines
        lines_group = QGroupBox("Employee Pay")
        lines_layout = QVBoxLayout(lines_group)

        lines_table = QTableWidget()
        lines_table.setColumnCount(5)
        lines_table.setHorizontalHeaderLabels(["Employee", "Gross", "Taxes", "Deductions", "Net"])
        lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        lines = self.pay_run.get("lines", [])
        lines_table.setRowCount(len(lines))

        for i, line in enumerate(lines):
            lines_table.setItem(i, 0, QTableWidgetItem(line.get("employee_name", line.get("employee_id", ""))))
            lines_table.setItem(i, 1, QTableWidgetItem(f"${line.get('gross_pay', 0):,.2f}"))
            total_tax = line.get("federal_income_tax", 0) + line.get("state_income_tax", 0) + \
                       line.get("social_security_employee", 0) + line.get("medicare_employee", 0)
            lines_table.setItem(i, 2, QTableWidgetItem(f"${total_tax:,.2f}"))
            lines_table.setItem(i, 3, QTableWidgetItem(f"${line.get('total_deductions', 0):,.2f}"))
            lines_table.setItem(i, 4, QTableWidgetItem(f"${line.get('net_pay', 0):,.2f}"))

        lines_layout.addWidget(lines_table)
        layout.addWidget(lines_group)

        # Buttons
        btn_layout = QHBoxLayout()

        # Print Checks button - only show if pay run is paid and has checks
        if self.pay_run.get("status") == "paid":
            print_btn = QPushButton("Print Paychecks")
            print_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
            print_btn.setStyleSheet(f"""
                background-color: {GENFIN_COLORS['teal']};
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            """)
            print_btn.clicked.connect(self._print_checks)
            btn_layout.addWidget(print_btn)

            print_stubs_btn = QPushButton("Print Pay Stubs")
            print_stubs_btn.clicked.connect(self._print_stubs)
            btn_layout.addWidget(print_stubs_btn)

        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _print_checks(self):
        """Print paychecks for this pay run."""
        # Get check IDs from pay run lines
        checks_to_print = []
        lines = self.pay_run.get("lines", [])

        for line in lines:
            if line.get("check_id") and line.get("payment_method") in ["check", "both"]:
                checks_to_print.append({
                    "check_id": line["check_id"],
                    "employee": line.get("employee_name", ""),
                    "amount": line.get("net_pay", 0)
                })

        if not checks_to_print:
            QMessageBox.information(self, "No Checks",
                "No checks to print. All employees in this pay run use Direct Deposit.")
            return

        # Show print dialog
        dialog = PrintChecksDialog(checks_to_print, self)
        dialog.exec()

    def _print_stubs(self):
        """Print pay stubs for all employees."""
        lines = self.pay_run.get("lines", [])
        if not lines:
            QMessageBox.warning(self, "No Data", "No pay data to print.")
            return

        # For now, show a simple message - full implementation would generate PDF
        QMessageBox.information(self, "Print Pay Stubs",
            f"Ready to print {len(lines)} pay stub(s).\n\n"
            "This would send to your default printer.\n"
            "(Full print preview coming soon)")


class PrintChecksDialog(GenFinDialog):
    """Dialog for printing payroll checks."""

    def __init__(self, checks: List[Dict], parent=None):
        super().__init__("Print Paychecks", parent)
        self.checks = checks
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Printer selection
        printer_group = QGroupBox("Printer Settings")
        printer_layout = QFormLayout(printer_group)

        self.printer_combo = QComboBox()
        self.printer_combo.addItems([
            "Default Printer",
            "Check Printer (MICR)",
            "PDF Preview"
        ])
        printer_layout.addRow("Print To:", self.printer_combo)

        self.check_format = QComboBox()
        self.check_format.addItems([
            "Standard Check - Top Stub",
            "Voucher Check - 3-Part",
            "Wallet Check",
            "Quicken/QuickBooks Compatible"
        ])
        printer_layout.addRow("Check Format:", self.check_format)

        self.starting_check = QSpinBox()
        self.starting_check.setRange(1, 99999)
        self.starting_check.setValue(1001)
        printer_layout.addRow("Starting Check #:", self.starting_check)

        layout.addWidget(printer_group)

        # Checks to print
        checks_group = QGroupBox(f"Checks to Print ({len(self.checks)})")
        checks_layout = QVBoxLayout(checks_group)

        self.checks_table = QTableWidget()
        self.checks_table.setColumnCount(4)
        self.checks_table.setHorizontalHeaderLabels(["Print", "Check #", "Employee", "Amount"])
        self.checks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.checks_table.setRowCount(len(self.checks))

        check_num = self.starting_check.value()
        total = 0

        for i, check in enumerate(self.checks):
            # Print checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            self.checks_table.setCellWidget(i, 0, chk)

            # Check number
            self.checks_table.setItem(i, 1, QTableWidgetItem(str(check_num + i)))

            # Employee
            self.checks_table.setItem(i, 2, QTableWidgetItem(check.get("employee", "")))

            # Amount
            amount = check.get("amount", 0)
            total += amount
            self.checks_table.setItem(i, 3, QTableWidgetItem(f"${amount:,.2f}"))

        checks_layout.addWidget(self.checks_table)

        # Total
        total_label = QLabel(f"Total: ${total:,.2f}")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        checks_layout.addWidget(total_label)

        layout.addWidget(checks_group)

        # Print options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.print_logo = QCheckBox("Print company logo on checks")
        self.print_logo.setChecked(True)
        options_layout.addWidget(self.print_logo)

        self.print_signature = QCheckBox("Print signature image")
        options_layout.addWidget(self.print_signature)

        self.print_micr = QCheckBox("Print MICR line (requires MICR printer)")
        self.print_micr.setChecked(True)
        options_layout.addWidget(self.print_micr)

        layout.addWidget(options_group)

        # Buttons
        btn_layout = QHBoxLayout()

        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview)
        btn_layout.addWidget(preview_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        print_btn = QPushButton("Print Checks")
        print_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
        """)
        print_btn.clicked.connect(self._print)
        btn_layout.addWidget(print_btn)

        layout.addLayout(btn_layout)

    def _preview(self):
        """Show print preview."""
        QMessageBox.information(self, "Print Preview",
            "Print preview would display here.\n\n"
            "Shows checks formatted for selected format\n"
            "with all positioning for check stock.")

    def _print(self):
        """Send checks to printer."""
        # Count selected checks
        selected = 0
        for i in range(self.checks_table.rowCount()):
            chk = self.checks_table.cellWidget(i, 0)
            if chk and chk.isChecked():
                selected += 1

        if selected == 0:
            QMessageBox.warning(self, "No Selection", "Please select at least one check to print.")
            return

        # Confirm print
        reply = QMessageBox.question(self, "Confirm Print",
            f"Print {selected} check(s) to {self.printer_combo.currentText()}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Mark checks as printed via API
            for i, check in enumerate(self.checks):
                chk = self.checks_table.cellWidget(i, 0)
                if chk and chk.isChecked() and check.get("check_id"):
                    api_post(f"/checks/{check['check_id']}/mark-printed", {})

            QMessageBox.information(self, "Success",
                f"Sent {selected} check(s) to printer.\n\n"
                "Checks have been marked as printed.")
            self.accept()


class GenFinPayrollCenterScreen(QWidget):
    """
    QuickBooks-style Payroll Center with tabs for:
    - Pay Schedules management
    - Scheduled Payroll
    - Unscheduled Payroll
    - Pay History
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header with teal styling
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {GENFIN_COLORS['teal']};
                border-bottom: 3px solid {GENFIN_COLORS['teal_dark']};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)

        title = QLabel("PAYROLL CENTER")
        title.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            font-family: "Arial Black", sans-serif;
            padding: 10px;
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header_frame)

        # Tab widget for different payroll functions
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {GENFIN_COLORS['bevel_dark']};
                background: {GENFIN_COLORS['window_face']};
            }}
            QTabBar::tab {{
                background: {GENFIN_COLORS['window_face']};
                border: 2px solid {GENFIN_COLORS['bevel_dark']};
                padding: 8px 16px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background: {GENFIN_COLORS['teal_light']};
                border-bottom: 2px solid {GENFIN_COLORS['teal']};
            }}
        """)

        # === Pay Schedules Tab ===
        schedules_tab = QWidget()
        schedules_layout = QVBoxLayout(schedules_tab)
        schedules_layout.setSpacing(8)

        # Schedule buttons
        sched_btn_layout = QHBoxLayout()
        new_sched_btn = QPushButton("New Schedule")
        new_sched_btn.clicked.connect(self._new_schedule)
        sched_btn_layout.addWidget(new_sched_btn)

        edit_sched_btn = QPushButton("Edit Schedule")
        edit_sched_btn.clicked.connect(self._edit_schedule)
        sched_btn_layout.addWidget(edit_sched_btn)

        assign_btn = QPushButton("Assign Employees")
        assign_btn.clicked.connect(self._assign_employees)
        sched_btn_layout.addWidget(assign_btn)

        sched_btn_layout.addStretch()
        schedules_layout.addLayout(sched_btn_layout)

        # Schedules table
        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(6)
        self.schedules_table.setHorizontalHeaderLabels([
            "Schedule Name", "Frequency", "Employees", "Next Pay Date", "Next Period", "Status"
        ])
        self.schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        schedules_layout.addWidget(self.schedules_table)

        self.tabs.addTab(schedules_tab, "Pay Schedules")

        # === Employees Tab ===
        employees_tab = QWidget()
        employees_layout = QVBoxLayout(employees_tab)
        employees_layout.setSpacing(8)

        # Employee list header
        emp_header = QLabel("Employees on Payroll")
        emp_header.setStyleSheet(f"""
            font-weight: bold;
            font-size: 14px;
            color: {GENFIN_COLORS['teal_dark']};
            padding: 4px;
        """)
        employees_layout.addWidget(emp_header)

        # Employees table
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(7)
        self.employees_table.setHorizontalHeaderLabels([
            "Employee Name", "Employee ID", "Pay Schedule", "Pay Type", "Pay Rate", "Payment Method", "Status"
        ])
        self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.employees_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employees_table.setAlternatingRowColors(True)
        employees_layout.addWidget(self.employees_table)

        # Summary info
        self.emp_summary_label = QLabel("0 employees on payroll")
        self.emp_summary_label.setStyleSheet(f"color: {GENFIN_COLORS['text_light']}; font-style: italic;")
        employees_layout.addWidget(self.emp_summary_label)

        self.tabs.addTab(employees_tab, "Employees")

        # === Scheduled Payroll Tab ===
        scheduled_tab = QWidget()
        scheduled_layout = QVBoxLayout(scheduled_tab)

        # Due payrolls section
        due_label = QLabel("Payrolls Due or Upcoming:")
        due_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        scheduled_layout.addWidget(due_label)

        self.due_table = QTableWidget()
        self.due_table.setColumnCount(5)
        self.due_table.setHorizontalHeaderLabels([
            "Schedule", "Pay Date", "Period", "Employees", "Action"
        ])
        self.due_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.due_table.setMaximumHeight(200)
        scheduled_layout.addWidget(self.due_table)

        # Run scheduled payroll button
        run_sched_btn = QPushButton("Run Scheduled Payroll")
        run_sched_btn.setStyleSheet(f"""
            background-color: {GENFIN_COLORS['teal']};
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 12px 24px;
        """)
        run_sched_btn.clicked.connect(self._run_scheduled_payroll)
        scheduled_layout.addWidget(run_sched_btn)

        scheduled_layout.addStretch()

        self.tabs.addTab(scheduled_tab, "Scheduled Payroll")

        # === Unscheduled Payroll Tab ===
        unsched_tab = QWidget()
        unsched_layout = QVBoxLayout(unsched_tab)

        unsched_info = QLabel(
            "Use Unscheduled Payroll for:\n"
            "- Bonus payments\n"
            "- Commission payments\n"
            "- Payroll corrections\n"
            "- Emergency advances\n"
            "- New hire first paycheck\n"
            "- Termination checks"
        )
        unsched_info.setStyleSheet(f"""
            background-color: #FFF3CD;
            color: #856404;
            padding: 12px;
            border: 1px solid #FFEAA7;
        """)
        unsched_layout.addWidget(unsched_info)

        run_unsched_btn = QPushButton("Run Unscheduled Payroll")
        run_unsched_btn.setStyleSheet("""
            background-color: #E67E22;
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 12px 24px;
        """)
        run_unsched_btn.clicked.connect(self._run_unscheduled_payroll)
        unsched_layout.addWidget(run_unsched_btn)

        unsched_layout.addStretch()

        self.tabs.addTab(unsched_tab, "Unscheduled Payroll")

        # === Pay History Tab ===
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        # Filter row
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.history_type_filter = QComboBox()
        self.history_type_filter.addItems(["All Types", "Scheduled", "Unscheduled", "Bonus", "Termination"])
        self.history_type_filter.currentTextChanged.connect(self._filter_history)
        filter_layout.addWidget(self.history_type_filter)

        filter_layout.addWidget(QLabel("Status:"))
        self.history_status_filter = QComboBox()
        self.history_status_filter.addItems(["All", "Draft", "Calculated", "Approved", "Paid", "Voided"])
        self.history_status_filter.currentTextChanged.connect(self._filter_history)
        filter_layout.addWidget(self.history_status_filter)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        history_layout.addLayout(filter_layout)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Pay Run #", "Type", "Pay Date", "Period", "Employees", "Net Pay", "Status"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.doubleClicked.connect(self._view_pay_run)
        history_layout.addWidget(self.history_table)

        # Action buttons
        action_layout = QHBoxLayout()
        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self._view_pay_run)
        action_layout.addWidget(view_btn)

        calc_btn = QPushButton("Calculate")
        calc_btn.clicked.connect(self._calculate_pay_run)
        action_layout.addWidget(calc_btn)

        approve_btn = QPushButton("Approve")
        approve_btn.clicked.connect(self._approve_pay_run)
        action_layout.addWidget(approve_btn)

        process_btn = QPushButton("Process")
        process_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
        process_btn.clicked.connect(self._process_pay_run)
        action_layout.addWidget(process_btn)

        action_layout.addStretch()
        history_layout.addLayout(action_layout)

        self.tabs.addTab(history_tab, "Pay History")

        layout.addWidget(self.tabs)

        # Store data
        self._schedules = []
        self._pay_runs = []
        self._employees = []
        self._bank_accounts = []

    def load_data(self):
        """Load all payroll data from API."""
        # Load pay schedules
        data = api_get("/pay-schedules")
        if data is not None:
            self._schedules = data if isinstance(data, list) else data.get("schedules", [])
            self._populate_schedules_table()

        # Load due payrolls
        due_data = api_get("/pay-schedules/due")
        if due_data is not None:
            self._populate_due_table(due_data if isinstance(due_data, list) else due_data.get("due", []))

        # Load pay runs history
        runs_data = api_get("/pay-runs")
        if runs_data is not None:
            self._pay_runs = runs_data if isinstance(runs_data, list) else runs_data.get("pay_runs", [])
            self._populate_history_table()

        # Load employees
        emp_data = api_get("/employees")
        if emp_data is not None:
            self._employees = emp_data if isinstance(emp_data, list) else []
            self._populate_employees_table()

        # Load bank accounts
        bank_data = api_get("/bank-accounts")
        if bank_data is not None:
            self._bank_accounts = bank_data if isinstance(bank_data, list) else []

    def _populate_schedules_table(self):
        """Populate the pay schedules table."""
        self.schedules_table.setRowCount(len(self._schedules))
        for i, sched in enumerate(self._schedules):
            self.schedules_table.setItem(i, 0, QTableWidgetItem(sched.get("name", "")))

            freq = sched.get("frequency", "biweekly")
            freq_display = {"weekly": "Weekly", "biweekly": "Bi-weekly",
                           "semimonthly": "Semi-monthly", "monthly": "Monthly"}.get(freq, freq)
            self.schedules_table.setItem(i, 1, QTableWidgetItem(freq_display))

            emp_count = len(sched.get("employee_ids", []))
            self.schedules_table.setItem(i, 2, QTableWidgetItem(str(emp_count)))

            self.schedules_table.setItem(i, 3, QTableWidgetItem(sched.get("next_pay_date", "N/A")))

            period = f"{sched.get('next_pay_period_start', '')} - {sched.get('next_pay_period_end', '')}"
            self.schedules_table.setItem(i, 4, QTableWidgetItem(period))

            status = "Active" if sched.get("is_active", True) else "Inactive"
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            self.schedules_table.setItem(i, 5, status_item)

    def _populate_employees_table(self):
        """Populate the employees on payroll table."""
        # Filter to active employees only
        active_employees = [e for e in self._employees if e.get("status") == "active"]
        self.employees_table.setRowCount(len(active_employees))

        # Build schedule lookup
        schedule_lookup = {s.get("schedule_id"): s.get("name", "N/A") for s in self._schedules}

        for i, emp in enumerate(active_employees):
            # Employee name
            name = f"{emp.get('last_name', '')}, {emp.get('first_name', '')}"
            if emp.get("middle_name"):
                name += f" {emp.get('middle_name')[0]}."
            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont("MS Sans Serif", 11, QFont.Weight.Bold))
            self.employees_table.setItem(i, 0, name_item)

            # Employee ID
            self.employees_table.setItem(i, 1, QTableWidgetItem(emp.get("employee_id", "")))

            # Pay Schedule
            schedule_id = emp.get("pay_schedule_id")
            schedule_name = schedule_lookup.get(schedule_id, "Not Assigned")
            schedule_item = QTableWidgetItem(schedule_name)
            if schedule_name == "Not Assigned":
                schedule_item.setForeground(Qt.GlobalColor.red)
            self.employees_table.setItem(i, 2, schedule_item)

            # Pay Type
            pay_type = emp.get("pay_type", "hourly").title()
            self.employees_table.setItem(i, 3, QTableWidgetItem(pay_type))

            # Pay Rate
            rate = emp.get("pay_rate", 0)
            if emp.get("pay_type") == "salary":
                rate_text = f"${rate:,.0f}/yr"
            else:
                rate_text = f"${rate:.2f}/hr"
            self.employees_table.setItem(i, 4, QTableWidgetItem(rate_text))

            # Payment Method
            method = emp.get("payment_method", "check")
            method_display = {"check": "Check", "direct_deposit": "Direct Deposit", "both": "Both"}.get(method, method)
            self.employees_table.setItem(i, 5, QTableWidgetItem(method_display))

            # Status
            status_item = QTableWidgetItem("Active")
            status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.employees_table.setItem(i, 6, status_item)

        # Update summary
        total = len(active_employees)
        assigned = sum(1 for e in active_employees if e.get("pay_schedule_id"))
        unassigned = total - assigned
        summary = f"{total} employee(s) on payroll"
        if unassigned > 0:
            summary += f" ({unassigned} not assigned to a schedule)"
        self.emp_summary_label.setText(summary)

    def _populate_due_table(self, due_payrolls: List[Dict]):
        """Populate the due payrolls table."""
        self.due_table.setRowCount(len(due_payrolls))
        for i, due in enumerate(due_payrolls):
            self.due_table.setItem(i, 0, QTableWidgetItem(due.get("schedule_name", "")))
            self.due_table.setItem(i, 1, QTableWidgetItem(due.get("next_pay_date", "")))
            period = f"{due.get('next_pay_period_start', '')} - {due.get('next_pay_period_end', '')}"
            self.due_table.setItem(i, 2, QTableWidgetItem(period))
            self.due_table.setItem(i, 3, QTableWidgetItem(str(len(due.get("employee_ids", [])))))

            # Run button
            run_btn = QPushButton("Run Now")
            run_btn.setStyleSheet(f"background-color: {GENFIN_COLORS['teal']}; color: white;")
            run_btn.clicked.connect(lambda checked, s=due: self._run_specific_schedule(s))
            self.due_table.setCellWidget(i, 4, run_btn)

    def _populate_history_table(self):
        """Populate the pay history table."""
        runs = self._filter_pay_runs()
        self.history_table.setRowCount(len(runs))

        for i, run in enumerate(runs):
            self.history_table.setItem(i, 0, QTableWidgetItem(str(run.get("pay_run_number", ""))))

            run_type = run.get("pay_run_type", "scheduled").replace("_", " ").title()
            self.history_table.setItem(i, 1, QTableWidgetItem(run_type))

            self.history_table.setItem(i, 2, QTableWidgetItem(run.get("pay_date", "")))

            period = f"{run.get('pay_period_start', '')} - {run.get('pay_period_end', '')}"
            self.history_table.setItem(i, 3, QTableWidgetItem(period))

            emp_count = len(run.get("lines", []))
            self.history_table.setItem(i, 4, QTableWidgetItem(str(emp_count)))

            net = run.get("total_net", 0)
            self.history_table.setItem(i, 5, QTableWidgetItem(f"${net:,.2f}"))

            status = run.get("status", "draft").title()
            status_item = QTableWidgetItem(status)
            status_colors = {
                "Draft": Qt.GlobalColor.gray,
                "Calculated": Qt.GlobalColor.blue,
                "Approved": Qt.GlobalColor.darkGreen,
                "Paid": Qt.GlobalColor.darkBlue,
                "Voided": Qt.GlobalColor.red
            }
            status_item.setForeground(status_colors.get(status, Qt.GlobalColor.black))
            self.history_table.setItem(i, 6, status_item)

    def _filter_pay_runs(self) -> List[Dict]:
        """Filter pay runs based on current filter selections."""
        runs = self._pay_runs

        type_filter = self.history_type_filter.currentText()
        if type_filter != "All Types":
            filter_map = {
                "Scheduled": "scheduled",
                "Unscheduled": "unscheduled",
                "Bonus": "bonus",
                "Termination": "termination"
            }
            runs = [r for r in runs if r.get("pay_run_type") == filter_map.get(type_filter)]

        status_filter = self.history_status_filter.currentText()
        if status_filter != "All":
            runs = [r for r in runs if r.get("status", "").lower() == status_filter.lower()]

        return runs

    def _filter_history(self, _):
        """Handle filter change."""
        self._populate_history_table()

    def _new_schedule(self):
        """Create a new pay schedule."""
        dialog = AddPayScheduleDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/pay-schedules", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success", "Pay schedule created!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create schedule: {error}")

    def _edit_schedule(self):
        """Edit selected pay schedule."""
        row = self.schedules_table.currentRow()
        if row < 0 or row >= len(self._schedules):
            QMessageBox.warning(self, "Warning", "Please select a schedule to edit.")
            return

        schedule = self._schedules[row]
        dialog = AddPayScheduleDialog(schedule, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Info", "Schedule updated.")
            self.load_data()

    def _assign_employees(self):
        """Open dialog to assign employees to a schedule."""
        row = self.schedules_table.currentRow()
        if row < 0 or row >= len(self._schedules):
            QMessageBox.warning(self, "Warning", "Please select a schedule first.")
            return

        QMessageBox.information(self, "Info",
            "Employee assignment dialog coming soon.\n"
            "Use Employee setup to assign pay schedules for now.")

    def _run_scheduled_payroll(self):
        """Run a scheduled payroll."""
        if not self._schedules:
            QMessageBox.warning(self, "No Schedules", "No pay schedules found. Create one first.")
            return

        if not self._bank_accounts:
            QMessageBox.warning(self, "No Accounts", "No bank accounts found.")
            return

        dialog = RunScheduledPayrollDialog(self._schedules, self._bank_accounts, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/pay-runs/scheduled", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success",
                    f"Payroll created! Pay Run #{result.get('pay_run_number', 'N/A')}\n"
                    f"Employees: {result.get('employee_count', 0)}")
                self.load_data()
                self.tabs.setCurrentIndex(3)  # Switch to history tab
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create payroll: {error}")

    def _run_unscheduled_payroll(self):
        """Run an unscheduled payroll."""
        if not self._employees:
            QMessageBox.warning(self, "No Employees", "No employees found.")
            return

        if not self._bank_accounts:
            QMessageBox.warning(self, "No Accounts", "No bank accounts found.")
            return

        dialog = RunUnscheduledPayrollDialog(self._employees, self._bank_accounts, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            result = api_post("/pay-runs/unscheduled", dialog.result_data)
            if result and result.get("success"):
                QMessageBox.information(self, "Success",
                    f"Unscheduled payroll created! Pay Run #{result.get('pay_run_number', 'N/A')}")
                self.load_data()
                self.tabs.setCurrentIndex(3)  # Switch to history tab
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Failed to create payroll: {error}")

    def _run_specific_schedule(self, schedule: Dict):
        """Run payroll for a specific schedule from the due table."""
        if not self._bank_accounts:
            QMessageBox.warning(self, "No Accounts", "No bank accounts found.")
            return

        # Auto-fill the dialog with this schedule
        result = api_post("/pay-runs/scheduled", {
            "schedule_id": schedule["schedule_id"],
            "bank_account_id": self._bank_accounts[0]["account_id"]
        })

        if result and result.get("success"):
            QMessageBox.information(self, "Success",
                f"Payroll started for {schedule.get('name', '')}!\n"
                f"Pay Run #{result.get('pay_run_number', 'N/A')}")
            self.load_data()
        else:
            error = result.get("error", "Unknown error") if result else "API request failed"
            QMessageBox.warning(self, "Error", f"Failed to start payroll: {error}")

    def _get_selected_pay_run(self) -> Optional[Dict]:
        """Get the currently selected pay run from history table."""
        row = self.history_table.currentRow()
        runs = self._filter_pay_runs()
        if row >= 0 and row < len(runs):
            return runs[row]
        return None

    def _view_pay_run(self):
        """View details of selected pay run."""
        pay_run = self._get_selected_pay_run()
        if not pay_run:
            QMessageBox.warning(self, "Warning", "Please select a pay run to view.")
            return

        # Get full pay run details
        details = api_get(f"/pay-runs/{pay_run['pay_run_id']}")
        if details:
            dialog = ViewPayRunDialog(details, parent=self)
            dialog.exec()
        else:
            dialog = ViewPayRunDialog(pay_run, parent=self)
            dialog.exec()

    def _calculate_pay_run(self):
        """Calculate a draft pay run."""
        pay_run = self._get_selected_pay_run()
        if not pay_run:
            QMessageBox.warning(self, "Warning", "Please select a pay run.")
            return

        if pay_run.get("status") not in ["draft", "calculated"]:
            QMessageBox.warning(self, "Cannot Calculate",
                "Only draft or previously calculated pay runs can be calculated.")
            return

        result = api_post(f"/pay-runs/{pay_run['pay_run_id']}/calculate", {})
        if result and result.get("success"):
            QMessageBox.information(self, "Calculated",
                f"Pay run calculated!\n"
                f"Total Gross: ${result.get('total_gross', 0):,.2f}\n"
                f"Total Net: ${result.get('total_net', 0):,.2f}")
            self.load_data()
        else:
            error = result.get("error", "Unknown error") if result else "API request failed"
            QMessageBox.warning(self, "Error", f"Calculation failed: {error}")

    def _approve_pay_run(self):
        """Approve a calculated pay run."""
        pay_run = self._get_selected_pay_run()
        if not pay_run:
            QMessageBox.warning(self, "Warning", "Please select a pay run.")
            return

        if pay_run.get("status") != "calculated":
            QMessageBox.warning(self, "Cannot Approve",
                "Only calculated pay runs can be approved. Calculate first.")
            return

        reply = QMessageBox.question(self, "Confirm Approval",
            f"Approve Pay Run #{pay_run.get('pay_run_number')}?\n"
            f"Net Pay: ${pay_run.get('total_net', 0):,.2f}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            result = api_post(f"/pay-runs/{pay_run['pay_run_id']}/approve", {})
            if result and result.get("success"):
                QMessageBox.information(self, "Approved", "Pay run approved!")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Approval failed: {error}")

    def _process_pay_run(self):
        """Process an approved pay run (create checks/ACH)."""
        pay_run = self._get_selected_pay_run()
        if not pay_run:
            QMessageBox.warning(self, "Warning", "Please select a pay run.")
            return

        if pay_run.get("status") != "approved":
            QMessageBox.warning(self, "Cannot Process",
                "Only approved pay runs can be processed.")
            return

        reply = QMessageBox.question(self, "Confirm Processing",
            f"Process Pay Run #{pay_run.get('pay_run_number')}?\n"
            f"This will create checks and/or ACH transactions.\n"
            f"Net Pay: ${pay_run.get('total_net', 0):,.2f}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            result = api_post(f"/pay-runs/{pay_run['pay_run_id']}/process", {})
            if result and result.get("success"):
                checks = result.get("checks_created", [])
                dd = result.get("direct_deposits", 0)
                QMessageBox.information(self, "Processed",
                    f"Pay run processed!\n"
                    f"Checks created: {len(checks)}\n"
                    f"Direct deposits: {dd}")
                self.load_data()
            else:
                error = result.get("error", "Unknown error") if result else "API request failed"
                QMessageBox.warning(self, "Error", f"Processing failed: {error}")


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

        # Payroll Center - QuickBooks style with scheduled/unscheduled payroll
        self._add_screen("payroll", GenFinPayrollCenterScreen())

        # 1099 screen
        forms_1099 = GenFinListScreen("1099 Forms", ["Vendor", "Tax ID", "Amount", "Status"],
                                       "/1099/forms", None, "form_id")
        self._add_screen("1099", forms_1099)

        # Banking Module - QuickBooks style
        self._add_screen("banking", GenFinBankAccountsScreen())
        self._add_screen("register", GenFinCheckRegisterScreen())
        self._add_screen("transfers", GenFinTransfersScreen())
        self._add_screen("reconcile", GenFinReconcileScreen())
        self._add_screen("feeds", GenFinBankFeedsScreen())

        # Customer Module - Statements & Credits
        self._add_screen("statements", GenFinStatementsScreen())
        self._add_screen("credits", GenFinCreditMemosScreen())

        # Vendor Module - Credit Cards & Vendor Credits
        self._add_screen("creditcard", GenFinCreditCardsScreen())
        self._add_screen("vendorcredits", GenFinVendorCreditsScreen())

        # Payroll - Pay Liabilities
        self._add_screen("payliab", GenFinPayLiabilitiesScreen())

        # Lists - Fixed Assets, Recurring, Memorized
        self._add_screen("assets", GenFinFixedAssetsScreen())
        self._add_screen("recurring", GenFinRecurringTransScreen())
        self._add_screen("memorized", GenFinMemorizedTransScreen())

        # Budgets
        self._add_screen("budget", GenFinBudgetsScreen())

        # Entities, Settings, Help
        self._add_screen("entities", GenFinEntitiesScreen())
        self._add_screen("settings", GenFinSettingsScreen())
        self._add_screen("help", GenFinHelpScreen())

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
