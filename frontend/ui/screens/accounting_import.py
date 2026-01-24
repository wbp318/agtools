"""
Accounting Import Screen

Screen for importing expenses from accounting software CSV exports.
AgTools v2.9.0
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QFrame,
    QSpinBox, QCheckBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.accounting_import_api import (
    get_accounting_import_api, AccountingImportAPI, QBImportPreview,
    QBImportSummary, ExpenseCategory
)


# Category colors for visual identification
CATEGORY_COLORS = {
    "seed": "#4caf50",           # Green
    "fertilizer": "#ff9800",     # Orange
    "chemical": "#f44336",       # Red
    "fuel": "#795548",           # Brown
    "repairs": "#607d8b",        # Gray-blue
    "labor": "#2196f3",          # Blue
    "custom_hire": "#9c27b0",    # Purple
    "land_rent": "#009688",      # Teal
    "crop_insurance": "#00bcd4", # Cyan
    "interest": "#ffc107",       # Amber
    "utilities": "#e91e63",      # Pink
    "storage": "#8bc34a",        # Light green
    "other": "#757575",          # Gray
}


class PreviewWorker(QThread):
    """Background worker for previewing QB import."""
    finished = pyqtSignal(object, str)  # (preview, error)

    def __init__(self, api: AccountingImportAPI, file_path: str):
        super().__init__()
        self.api = api
        self.file_path = file_path

    def run(self):
        preview, error = self.api.preview_import(self.file_path)
        self.finished.emit(preview, error or "")


class ImportWorker(QThread):
    """Background worker for importing QB data."""
    finished = pyqtSignal(object, str)  # (summary, error)

    def __init__(self, api: AccountingImportAPI, file_path: str, mappings: dict,
                 tax_year: int = None, save_mappings: bool = True):
        super().__init__()
        self.api = api
        self.file_path = file_path
        self.mappings = mappings
        self.tax_year = tax_year
        self.save_mappings = save_mappings

    def run(self):
        summary, error = self.api.import_data(
            self.file_path, self.mappings, self.tax_year, self.save_mappings
        )
        self.finished.emit(summary, error or "")


class AccountingImportScreen(QWidget):
    """
    Screen for importing expenses from accounting software exports.

    Features:
    - File selection with drag-and-drop
    - Auto-preview showing detected format and accounts
    - Mapping editor for assigning categories
    - Import with progress feedback
    - Results summary
    """

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.api = get_accounting_import_api()
        self.preview_data: QBImportPreview = None
        self.selected_file: str = None
        self.categories: list = []
        self.worker = None
        self._setup_ui()
        self._load_categories()

    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("QuickBooks Import")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(header)

        subtitle = QLabel("Import expenses from QuickBooks Desktop or Online exports")
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(subtitle)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - File selection and preview
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # File selection group
        file_group = QGroupBox("1. Select QuickBooks Export File")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(10)

        # File path row
        file_row = QHBoxLayout()
        self._file_path_input = QLineEdit()
        self._file_path_input.setPlaceholderText("Select a QuickBooks CSV export file...")
        self._file_path_input.setReadOnly(True)
        file_row.addWidget(self._file_path_input, 1)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.setFixedWidth(100)
        self._browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(self._browse_btn)

        file_layout.addLayout(file_row)

        # Supported formats info
        formats_label = QLabel(
            "<b>Supported formats:</b> QB Desktop Transaction Detail, "
            "Transaction List, Check Detail, QB Online Export"
        )
        formats_label.setWordWrap(True)
        formats_label.setStyleSheet("color: #666; font-size: 11px;")
        file_layout.addWidget(formats_label)

        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # Preview group
        preview_group = QGroupBox("2. Preview")
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(10)

        # Status frame
        self._status_frame = QFrame()
        self._status_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        status_layout = QFormLayout(self._status_frame)
        status_layout.setSpacing(5)

        self._format_label = QLabel("-")
        status_layout.addRow("Format Detected:", self._format_label)

        self._rows_label = QLabel("-")
        status_layout.addRow("Total Rows:", self._rows_label)

        self._expenses_label = QLabel("-")
        status_layout.addRow("Expense Transactions:", self._expenses_label)

        self._skipped_label = QLabel("-")
        status_layout.addRow("Skipped (non-expense):", self._skipped_label)

        self._date_range_label = QLabel("-")
        status_layout.addRow("Date Range:", self._date_range_label)

        preview_layout.addWidget(self._status_frame)

        # Warnings
        self._warnings_label = QLabel("")
        self._warnings_label.setStyleSheet("color: #ff9800; font-weight: bold;")
        self._warnings_label.setWordWrap(True)
        self._warnings_label.hide()
        preview_layout.addWidget(self._warnings_label)

        preview_group.setLayout(preview_layout)
        left_layout.addWidget(preview_group)

        # Options group
        options_group = QGroupBox("3. Import Options")
        options_layout = QFormLayout()
        options_layout.setSpacing(10)

        self._tax_year_spin = QSpinBox()
        self._tax_year_spin.setRange(2020, 2030)
        self._tax_year_spin.setValue(2025)
        self._tax_year_spin.setToolTip("Override tax year (leave as-is to use dates from file)")
        options_layout.addRow("Tax Year:", self._tax_year_spin)

        self._save_mappings_check = QCheckBox("Save mappings for future imports")
        self._save_mappings_check.setChecked(True)
        options_layout.addRow("", self._save_mappings_check)

        options_group.setLayout(options_layout)
        left_layout.addWidget(options_group)

        left_layout.addStretch()
        splitter.addWidget(left_panel)

        # Right panel - Account mappings
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        mapping_group = QGroupBox("4. Account Mappings")
        mapping_layout = QVBoxLayout()
        mapping_layout.setSpacing(10)

        mapping_info = QLabel(
            "Assign each QuickBooks account to an expense category. "
            "Suggested mappings are auto-filled based on account names."
        )
        mapping_info.setWordWrap(True)
        mapping_info.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        mapping_layout.addWidget(mapping_info)

        # Mappings table
        self._mappings_table = QTableWidget()
        self._mappings_table.setColumnCount(4)
        self._mappings_table.setHorizontalHeaderLabels([
            "QB Account", "Transactions", "Total $", "AgTools Category"
        ])
        self._mappings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._mappings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._mappings_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._mappings_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._mappings_table.setColumnWidth(3, 150)
        self._mappings_table.setAlternatingRowColors(True)
        self._mappings_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #eee;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        mapping_layout.addWidget(self._mappings_table)

        # Unmapped warning
        self._unmapped_label = QLabel("")
        self._unmapped_label.setStyleSheet("color: #f44336; font-weight: bold;")
        self._unmapped_label.hide()
        mapping_layout.addWidget(self._unmapped_label)

        mapping_group.setLayout(mapping_layout)
        right_layout.addWidget(mapping_group)

        splitter.addWidget(right_panel)
        splitter.setSizes([400, 500])

        layout.addWidget(splitter, 1)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.hide()
        layout.addWidget(self._progress_bar)

        # Bottom buttons
        button_row = QHBoxLayout()
        button_row.addStretch()

        self._import_btn = QPushButton("Import Expenses")
        self._import_btn.setFixedWidth(150)
        self._import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._do_import)
        button_row.addWidget(self._import_btn)

        layout.addLayout(button_row)

    def _load_categories(self):
        """Load expense categories from API."""
        categories, error = self.api.get_categories()
        if categories:
            self.categories = categories
        else:
            # Fallback categories
            self.categories = [
                ExpenseCategory("seed", "Seed"),
                ExpenseCategory("fertilizer", "Fertilizer"),
                ExpenseCategory("chemical", "Chemical"),
                ExpenseCategory("fuel", "Fuel"),
                ExpenseCategory("repairs", "Repairs"),
                ExpenseCategory("labor", "Labor"),
                ExpenseCategory("custom_hire", "Custom Hire"),
                ExpenseCategory("land_rent", "Land Rent"),
                ExpenseCategory("crop_insurance", "Crop Insurance"),
                ExpenseCategory("interest", "Interest"),
                ExpenseCategory("utilities", "Utilities"),
                ExpenseCategory("storage", "Storage"),
                ExpenseCategory("other", "Other"),
            ]

    def _browse_file(self):
        """Open file browser to select QB export."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select QuickBooks Export",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.selected_file = file_path
            self._file_path_input.setText(file_path)
            self._preview_file()

    def _preview_file(self):
        """Preview the selected file."""
        if not self.selected_file:
            return

        # Show loading state
        self._format_label.setText("Loading...")
        self._browse_btn.setEnabled(False)
        self._import_btn.setEnabled(False)
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.show()

        # Start preview worker
        self.worker = PreviewWorker(self.api, self.selected_file)
        self.worker.finished.connect(self._on_preview_complete)
        self.worker.start()

    def _on_preview_complete(self, preview: QBImportPreview, error: str):
        """Handle preview completion."""
        self._progress_bar.hide()
        self._browse_btn.setEnabled(True)

        if error:
            self._format_label.setText("Error")
            QMessageBox.warning(self, "Preview Error", f"Could not preview file:\n{error}")
            return

        self.preview_data = preview

        # Update status labels
        format_name = preview.format_detected.replace("_", " ").title()
        self._format_label.setText(format_name)
        self._rows_label.setText(str(preview.total_rows))
        self._expenses_label.setText(f"{preview.expense_rows} ({preview.expense_rows * 100 // max(preview.total_rows, 1)}%)")
        self._skipped_label.setText(str(preview.skipped_rows))

        if preview.date_range.get("min_date") and preview.date_range.get("max_date"):
            self._date_range_label.setText(
                f"{preview.date_range['min_date']} to {preview.date_range['max_date']}"
            )
        else:
            self._date_range_label.setText("-")

        # Show warnings
        if preview.warnings:
            self._warnings_label.setText("\n".join(preview.warnings))
            self._warnings_label.show()
        else:
            self._warnings_label.hide()

        # Populate mappings table
        self._populate_mappings_table(preview.accounts_found)

        # Show unmapped warning
        if preview.unmapped_accounts:
            self._unmapped_label.setText(
                f"Warning: {len(preview.unmapped_accounts)} accounts need manual mapping"
            )
            self._unmapped_label.show()
        else:
            self._unmapped_label.hide()

        # Enable import if we have expense rows
        self._import_btn.setEnabled(preview.expense_rows > 0)

    def _populate_mappings_table(self, accounts: list):
        """Populate the account mappings table."""
        self._mappings_table.setRowCount(len(accounts))

        for row, account in enumerate(accounts):
            # QB Account name
            name_item = QTableWidgetItem(account.account)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._mappings_table.setItem(row, 0, name_item)

            # Transaction count
            count_item = QTableWidgetItem(str(account.count))
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._mappings_table.setItem(row, 1, count_item)

            # Total amount
            total_item = QTableWidgetItem(f"${account.total:,.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._mappings_table.setItem(row, 2, total_item)

            # Category dropdown
            combo = QComboBox()
            for cat in self.categories:
                combo.addItem(cat.name, cat.value)

            # Set suggested category
            if account.suggested_category:
                index = combo.findData(account.suggested_category)
                if index >= 0:
                    combo.setCurrentIndex(index)
                    # Color the row to show it's auto-mapped
                    color = CATEGORY_COLORS.get(account.suggested_category, "#f5f5f5")
                    name_item.setBackground(QColor(color + "20"))
            else:
                # Highlight unmapped
                name_item.setBackground(QColor("#ffebee"))

            self._mappings_table.setCellWidget(row, 3, combo)

    def _get_mappings(self) -> dict:
        """Get current account mappings from the table."""
        mappings = {}
        for row in range(self._mappings_table.rowCount()):
            account = self._mappings_table.item(row, 0).text()
            combo = self._mappings_table.cellWidget(row, 3)
            if combo:
                category = combo.currentData()
                mappings[account] = category
        return mappings

    def _do_import(self):
        """Execute the import."""
        if not self.selected_file or not self.preview_data:
            return

        mappings = self._get_mappings()

        # Check for unmapped accounts
        unmapped = [
            acc for acc in self.preview_data.accounts_found
            if not mappings.get(acc.account)
        ]
        if unmapped:
            result = QMessageBox.question(
                self,
                "Unmapped Accounts",
                f"{len(unmapped)} accounts are not mapped. They will use 'Other' category.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result != QMessageBox.StandardButton.Yes:
                return

        # Disable UI during import
        self._browse_btn.setEnabled(False)
        self._import_btn.setEnabled(False)
        self._progress_bar.setRange(0, 0)
        self._progress_bar.show()

        # Start import worker
        tax_year = self._tax_year_spin.value()
        save_mappings = self._save_mappings_check.isChecked()

        self.worker = ImportWorker(
            self.api, self.selected_file, mappings, tax_year, save_mappings
        )
        self.worker.finished.connect(self._on_import_complete)
        self.worker.start()

    def _on_import_complete(self, summary: QBImportSummary, error: str):
        """Handle import completion."""
        self._progress_bar.hide()
        self._browse_btn.setEnabled(True)
        self._import_btn.setEnabled(True)

        if error:
            QMessageBox.critical(self, "Import Error", f"Import failed:\n{error}")
            return

        # Build summary message
        msg = f"""Import Complete!

Batch ID: {summary.batch_id}
Total Processed: {summary.total_processed}
Successfully Imported: {summary.successful}
Failed: {summary.failed}
Skipped (non-expense): {summary.skipped_non_expense}
Duplicates Skipped: {summary.duplicates_skipped}

Total Amount: ${summary.total_amount:,.2f}

By Category:"""

        for cat, count in sorted(summary.by_category.items()):
            msg += f"\n  {cat}: {count}"

        if summary.errors:
            msg += f"\n\nErrors ({len(summary.errors)}):"
            for err in summary.errors[:5]:
                msg += f"\n  - {err}"
            if len(summary.errors) > 5:
                msg += f"\n  ... and {len(summary.errors) - 5} more"

        QMessageBox.information(self, "Import Complete", msg)

        # Reset UI for another import
        self._clear_preview()

    def _clear_preview(self):
        """Clear the preview and reset UI."""
        self.preview_data = None
        self.selected_file = None
        self._file_path_input.clear()
        self._format_label.setText("-")
        self._rows_label.setText("-")
        self._expenses_label.setText("-")
        self._skipped_label.setText("-")
        self._date_range_label.setText("-")
        self._warnings_label.hide()
        self._unmapped_label.hide()
        self._mappings_table.setRowCount(0)
        self._import_btn.setEnabled(False)

    def set_current_user(self, user):
        """Set the current user."""
        self.current_user = user
