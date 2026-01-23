"""
Accounting Software Import Service for AgTools

Handles importing expense data from Accounting Software Desktop/Online exports.
Supports:
- Accounting Software Desktop CSV exports (Transaction Detail, Transaction List)
- Accounting Software Online CSV exports
- Account-to-category mapping
- Split transaction handling
- Smart transaction filtering (expenses only)

AgTools v2.9.0
"""

import csv
import io
import sqlite3
import re
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel

from services.cost_tracking_service import (
    ExpenseCategory,
    ImportStatus,
    get_cost_tracking_service
)


# ============================================================================
# ENUMS
# ============================================================================

class QBExportFormat(str, Enum):
    """Accounting Software export format types"""
    DESKTOP_TRANSACTION_DETAIL = "desktop_transaction_detail"
    DESKTOP_TRANSACTION_LIST = "desktop_transaction_list"
    DESKTOP_CHECK_DETAIL = "desktop_check_detail"
    ONLINE_EXPORT = "online_export"
    GENERIC = "generic"  # Falls back to standard CSV import


class QBTransactionType(str, Enum):
    """Accounting Software transaction types"""
    # Expense types (we want these)
    BILL = "Bill"
    BILL_PAYMENT = "Bill Payment"
    CHECK = "Check"
    CREDIT_CARD_CHARGE = "Credit Card Charge"
    CREDIT_CARD_CREDIT = "Credit Card Credit"
    EXPENSE = "Expense"
    PURCHASE_ORDER = "Purchase Order"
    VENDOR_CREDIT = "Vendor Credit"

    # Non-expense types (we skip these)
    DEPOSIT = "Deposit"
    TRANSFER = "Transfer"
    INVOICE = "Invoice"
    PAYMENT = "Payment"
    SALES_RECEIPT = "Sales Receipt"
    JOURNAL = "Journal Entry"
    ESTIMATE = "Estimate"


# Transaction types that represent expenses
EXPENSE_TRANSACTION_TYPES = {
    "bill", "check", "credit card charge", "expense",
    "credit card", "credit card credit", "vendor credit"
}

# Transaction types to skip
SKIP_TRANSACTION_TYPES = {
    "deposit", "transfer", "invoice", "payment", "sales receipt",
    "journal entry", "estimate", "sales order", "credit memo"
}


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class QBAccountMapping(BaseModel):
    """Mapping from Accounting Software account to AgTools category"""
    id: Optional[int] = None
    qb_account: str  # Accounting Software account name (e.g., "Farm Expense:Seed")
    agtools_category: ExpenseCategory
    is_default: bool = False
    created_at: Optional[datetime] = None


class QBImportPreview(BaseModel):
    """Preview of Accounting Software import"""
    format_detected: str
    total_rows: int
    expense_rows: int
    skipped_rows: int  # Non-expense transactions
    date_range: Dict[str, str]  # min_date, max_date
    accounts_found: List[Dict[str, Any]]  # account, count, suggested_category
    unmapped_accounts: List[str]
    sample_transactions: List[Dict[str, Any]]
    warnings: List[str]


class QBImportRequest(BaseModel):
    """Request to import Accounting Software data"""
    account_mappings: Dict[str, str]  # qb_account -> agtools_category
    include_transaction_types: Optional[List[str]] = None  # Filter to specific types
    tax_year: Optional[int] = None
    save_mappings: bool = True  # Save these mappings for future imports


class QBImportSummary(BaseModel):
    """Summary after QB import"""
    batch_id: int
    total_processed: int
    successful: int
    failed: int
    skipped_non_expense: int
    duplicates_skipped: int
    by_category: Dict[str, int]  # category -> count
    by_account: Dict[str, float]  # qb_account -> total_amount
    total_amount: float
    errors: List[str]


# ============================================================================
# QB ACCOUNT -> AGTOOLS CATEGORY MAPPING
# ============================================================================

# Default mappings for common Accounting Software account names
DEFAULT_QB_MAPPINGS: Dict[str, ExpenseCategory] = {
    # Seed accounts
    "seed": ExpenseCategory.SEED,
    "seed expense": ExpenseCategory.SEED,
    "farm expense:seed": ExpenseCategory.SEED,
    "crop inputs:seed": ExpenseCategory.SEED,

    # Fertilizer accounts
    "fertilizer": ExpenseCategory.FERTILIZER,
    "fert": ExpenseCategory.FERTILIZER,
    "farm expense:fertilizer": ExpenseCategory.FERTILIZER,
    "crop inputs:fertilizer": ExpenseCategory.FERTILIZER,
    "nutrients": ExpenseCategory.FERTILIZER,

    # Chemical accounts
    "chemical": ExpenseCategory.CHEMICAL,
    "chemicals": ExpenseCategory.CHEMICAL,
    "herbicide": ExpenseCategory.CHEMICAL,
    "pesticide": ExpenseCategory.CHEMICAL,
    "farm expense:chemical": ExpenseCategory.CHEMICAL,
    "crop inputs:chemical": ExpenseCategory.CHEMICAL,
    "crop protection": ExpenseCategory.CHEMICAL,

    # Fuel accounts
    "fuel": ExpenseCategory.FUEL,
    "diesel": ExpenseCategory.FUEL,
    "gasoline": ExpenseCategory.FUEL,
    "gas": ExpenseCategory.FUEL,
    "farm expense:fuel": ExpenseCategory.FUEL,
    "vehicle:fuel": ExpenseCategory.FUEL,
    "fuel and oil": ExpenseCategory.FUEL,

    # Repairs accounts
    "repairs": ExpenseCategory.REPAIRS,
    "repair": ExpenseCategory.REPAIRS,
    "maintenance": ExpenseCategory.REPAIRS,
    "equipment repair": ExpenseCategory.REPAIRS,
    "farm expense:repairs": ExpenseCategory.REPAIRS,
    "repairs and maintenance": ExpenseCategory.REPAIRS,
    "parts": ExpenseCategory.REPAIRS,

    # Labor accounts
    "labor": ExpenseCategory.LABOR,
    "wages": ExpenseCategory.LABOR,
    "payroll": ExpenseCategory.LABOR,
    "salaries": ExpenseCategory.LABOR,
    "payroll expenses": ExpenseCategory.LABOR,
    "farm labor": ExpenseCategory.LABOR,

    # Custom hire accounts
    "custom hire": ExpenseCategory.CUSTOM_HIRE,
    "custom work": ExpenseCategory.CUSTOM_HIRE,
    "custom farming": ExpenseCategory.CUSTOM_HIRE,
    "aerial application": ExpenseCategory.CUSTOM_HIRE,
    "flying": ExpenseCategory.CUSTOM_HIRE,
    "trucking": ExpenseCategory.CUSTOM_HIRE,
    "hauling": ExpenseCategory.CUSTOM_HIRE,
    "custom harvesting": ExpenseCategory.CUSTOM_HIRE,

    # Land rent accounts
    "land rent": ExpenseCategory.LAND_RENT,
    "cash rent": ExpenseCategory.LAND_RENT,
    "rent expense": ExpenseCategory.LAND_RENT,
    "farm rent": ExpenseCategory.LAND_RENT,
    "rent - farm": ExpenseCategory.LAND_RENT,
    "lease": ExpenseCategory.LAND_RENT,

    # Crop insurance accounts
    "crop insurance": ExpenseCategory.CROP_INSURANCE,
    "insurance:crop": ExpenseCategory.CROP_INSURANCE,
    "insurance - crop": ExpenseCategory.CROP_INSURANCE,
    "farm insurance": ExpenseCategory.CROP_INSURANCE,

    # Interest accounts
    "interest": ExpenseCategory.INTEREST,
    "interest expense": ExpenseCategory.INTEREST,
    "loan interest": ExpenseCategory.INTEREST,
    "operating interest": ExpenseCategory.INTEREST,
    "bank charges": ExpenseCategory.INTEREST,

    # Utilities accounts
    "utilities": ExpenseCategory.UTILITIES,
    "electric": ExpenseCategory.UTILITIES,
    "electricity": ExpenseCategory.UTILITIES,
    "power": ExpenseCategory.UTILITIES,
    "water": ExpenseCategory.UTILITIES,
    "phone": ExpenseCategory.UTILITIES,
    "telephone": ExpenseCategory.UTILITIES,
    "internet": ExpenseCategory.UTILITIES,

    # Storage accounts
    "storage": ExpenseCategory.STORAGE,
    "drying": ExpenseCategory.STORAGE,
    "grain storage": ExpenseCategory.STORAGE,
    "elevator": ExpenseCategory.STORAGE,
    "grain drying": ExpenseCategory.STORAGE,
    "bin rent": ExpenseCategory.STORAGE,
}


# ============================================================================
# ACCOUNTING IMPORT SERVICE
# ============================================================================

class AccountingImportService:
    """
    Service for importing expense data from accounting software exports.

    Handles:
    - Format detection (Desktop vs Online, different report types)
    - Account-to-category mapping with smart defaults
    - Transaction type filtering (expenses only)
    - Split transaction handling
    - Duplicate detection
    """

    def __init__(self, db_path: str = "agtools.db"):
        """Initialize accounting import service."""
        self.db_path = db_path
        self.cost_service = get_cost_tracking_service(db_path)
        self._init_mapping_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_mapping_table(self) -> None:
        """Initialize QB account mapping table."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qb_account_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                qb_account TEXT NOT NULL,
                agtools_category TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, qb_account)
            )
        """)

        conn.commit()
        conn.close()

    # ========================================================================
    # FORMAT DETECTION
    # ========================================================================

    def detect_format(self, csv_content: str) -> Tuple[QBExportFormat, List[str]]:
        """
        Detect which Accounting Software export format we're dealing with.

        Returns:
            Tuple of (format, headers)
        """
        reader = csv.reader(io.StringIO(csv_content))

        # Skip potential title rows (QB often has report title at top)
        headers = []
        for i, row in enumerate(reader):
            if i > 5:  # Give up after 5 rows
                break
            # Look for row that looks like headers (has common QB columns)
            row_lower = [c.lower().strip() for c in row]
            if any(h in row_lower for h in ["date", "type", "name", "amount", "num"]):
                headers = [c.strip() for c in row]
                break

        if not headers:
            return QBExportFormat.GENERIC, []

        headers_lower = [h.lower() for h in headers]

        # QB Desktop Transaction Detail Report
        # Usually has: Date, Type, Num, Name, Memo, Split, Amount, Balance
        if "split" in headers_lower and "balance" in headers_lower:
            return QBExportFormat.DESKTOP_TRANSACTION_DETAIL, headers

        # QB Desktop Check Detail
        # Has: Date, Num, Name, Amount with check-specific columns
        if "clr" in headers_lower or "cleared" in headers_lower:
            return QBExportFormat.DESKTOP_CHECK_DETAIL, headers

        # QB Desktop Transaction List
        # Usually has: Type, Date, Num, Name, Memo, Account, Amount
        if "account" in headers_lower and "type" in headers_lower:
            return QBExportFormat.DESKTOP_TRANSACTION_LIST, headers

        # QB Online Export
        # Often has: Date, Transaction Type, Name, Memo/Description, Amount
        if "transaction type" in headers_lower:
            return QBExportFormat.ONLINE_EXPORT, headers

        # Fall back to generic
        return QBExportFormat.GENERIC, headers

    # ========================================================================
    # PREVIEW
    # ========================================================================

    def preview_import(
        self,
        csv_content: str,
        user_id: int
    ) -> QBImportPreview:
        """
        Preview Accounting Software import and identify accounts to map.

        Args:
            csv_content: Raw CSV string
            user_id: User for saved mappings

        Returns:
            QBImportPreview with accounts and suggestions
        """
        format_type, headers = self.detect_format(csv_content)
        warnings = []

        if format_type == QBExportFormat.GENERIC:
            warnings.append("Could not detect Accounting Software format. Using generic CSV import.")
            # Fall back to standard preview
            preview = self.cost_service.preview_csv(csv_content)
            return QBImportPreview(
                format_detected=format_type.value,
                total_rows=preview.row_count,
                expense_rows=preview.row_count,
                skipped_rows=0,
                date_range={"min_date": "", "max_date": ""},
                accounts_found=[],
                unmapped_accounts=[],
                sample_transactions=preview.sample_rows[:5],
                warnings=warnings
            )

        # Parse the CSV with detected format
        column_map = self._get_column_mapping(format_type, headers)

        # Get user's saved mappings
        saved_mappings = self.get_user_mappings(user_id)

        # Parse all rows
        rows = self._parse_csv_rows(csv_content, headers, column_map)

        # Analyze
        accounts: Dict[str, Dict] = {}  # account -> {count, total, category}
        expense_count = 0
        skipped_count = 0
        dates = []
        sample_transactions = []

        for row in rows:
            trans_type = row.get("type", "").lower()

            # Skip non-expense transactions
            if self._is_skippable_transaction(trans_type):
                skipped_count += 1
                continue

            expense_count += 1

            # Track account
            account = row.get("account", row.get("split", "Unknown"))
            if account:
                if account not in accounts:
                    # Try to suggest a category
                    suggested = self._suggest_category(account, saved_mappings)
                    accounts[account] = {
                        "account": account,
                        "count": 0,
                        "total": 0.0,
                        "suggested_category": suggested.value if suggested else None
                    }
                accounts[account]["count"] += 1
                accounts[account]["total"] += row.get("amount", 0)

            # Track date range
            if row.get("date"):
                dates.append(row["date"])

            # Sample transactions
            if len(sample_transactions) < 10:
                sample_transactions.append(row)

        # Find unmapped accounts
        unmapped = [
            acc for acc, data in accounts.items()
            if data["suggested_category"] is None
        ]

        # Date range
        date_range = {
            "min_date": min(dates).isoformat() if dates else "",
            "max_date": max(dates).isoformat() if dates else ""
        }

        return QBImportPreview(
            format_detected=format_type.value,
            total_rows=len(rows),
            expense_rows=expense_count,
            skipped_rows=skipped_count,
            date_range=date_range,
            accounts_found=sorted(accounts.values(), key=lambda x: -x["total"]),
            unmapped_accounts=unmapped,
            sample_transactions=sample_transactions,
            warnings=warnings
        )

    def _get_column_mapping(
        self,
        format_type: QBExportFormat,
        headers: List[str]
    ) -> Dict[str, int]:
        """Get column index mapping for the format."""
        headers_lower = [h.lower() for h in headers]
        mapping = {}

        # Common column detection
        for i, h in enumerate(headers_lower):
            if h in ["date", "trans date", "transaction date"]:
                mapping["date"] = i
            elif h in ["type", "transaction type", "trans type"]:
                mapping["type"] = i
            elif h in ["num", "ref no", "reference", "doc num"]:
                mapping["num"] = i
            elif h in ["name", "payee", "vendor"]:
                mapping["name"] = i
            elif h in ["memo", "description", "memo/description", "desc"]:
                mapping["memo"] = i
            elif h in ["split", "category", "account"]:
                mapping["account"] = i
            elif h == "account":
                mapping["account"] = i
            elif h in ["amount", "debit", "payment"]:
                mapping["amount"] = i
            elif h == "credit":
                mapping["credit"] = i
            elif h in ["balance", "running balance"]:
                mapping["balance"] = i

        return mapping

    def _parse_csv_rows(
        self,
        csv_content: str,
        headers: List[str],
        column_map: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Parse CSV rows using column mapping."""
        reader = csv.reader(io.StringIO(csv_content))
        rows = []

        # Skip to header row
        found_headers = False
        for row in reader:
            if not found_headers:
                if row == headers:
                    found_headers = True
                continue

            if not any(row):  # Skip empty rows
                continue

            parsed = {}

            # Extract fields using mapping
            if "date" in column_map and column_map["date"] < len(row):
                parsed["date"] = self._parse_date(row[column_map["date"]])

            if "type" in column_map and column_map["type"] < len(row):
                parsed["type"] = row[column_map["type"]].strip()

            if "num" in column_map and column_map["num"] < len(row):
                parsed["num"] = row[column_map["num"]].strip()

            if "name" in column_map and column_map["name"] < len(row):
                parsed["name"] = row[column_map["name"]].strip()

            if "memo" in column_map and column_map["memo"] < len(row):
                parsed["memo"] = row[column_map["memo"]].strip()

            if "account" in column_map and column_map["account"] < len(row):
                parsed["account"] = row[column_map["account"]].strip()
                # Handle QB's parent:child account format
                parsed["account_display"] = parsed["account"].split(":")[-1] if parsed["account"] else ""

            # Amount - may be in amount, debit, or credit column
            amount = 0.0
            if "amount" in column_map and column_map["amount"] < len(row):
                amount = self._parse_amount(row[column_map["amount"]])
            elif "credit" in column_map and column_map["credit"] < len(row):
                # Credit column (negative for us - it's a refund)
                credit = self._parse_amount(row[column_map["credit"]])
                if credit:
                    amount = -credit

            parsed["amount"] = abs(amount) if amount else 0.0
            parsed["is_credit"] = amount < 0 if amount else False

            if parsed.get("date") or parsed.get("amount"):
                rows.append(parsed)

        return rows

    def _is_skippable_transaction(self, trans_type: str) -> bool:
        """Check if transaction type should be skipped."""
        trans_lower = trans_type.lower().strip()

        # Skip if it's a known non-expense type
        for skip in SKIP_TRANSACTION_TYPES:
            if skip in trans_lower:
                return True

        return False

    def _parse_date(self, value: str) -> Optional[date]:
        """Parse date from various QB formats."""
        if not value or not value.strip():
            return None

        value = value.strip()

        formats = [
            "%m/%d/%Y",
            "%m/%d/%y",
            "%Y-%m-%d",
            "%m-%d-%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        return None

    def _parse_amount(self, value: str) -> Optional[float]:
        """Parse amount from QB format."""
        if not value or not value.strip():
            return None

        # Remove currency symbols, spaces, and commas
        cleaned = re.sub(r'[$,\s]', '', value.strip())

        # Handle parentheses for negative (common in accounting)
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        try:
            return float(cleaned)
        except ValueError:
            return None

    # ========================================================================
    # ACCOUNT MAPPING
    # ========================================================================

    def _suggest_category(
        self,
        qb_account: str,
        saved_mappings: Dict[str, ExpenseCategory]
    ) -> Optional[ExpenseCategory]:
        """Suggest a category for a QB account."""
        account_lower = qb_account.lower().strip()

        # Check saved mappings first
        if account_lower in saved_mappings:
            return saved_mappings[account_lower]

        # Check default mappings
        if account_lower in DEFAULT_QB_MAPPINGS:
            return DEFAULT_QB_MAPPINGS[account_lower]

        # Try partial matches
        for default_key, category in DEFAULT_QB_MAPPINGS.items():
            # Check if default key is contained in account name
            if default_key in account_lower:
                return category
            # Check if account name is contained in default key
            if account_lower in default_key:
                return category

        # Try matching individual words
        account_words = set(account_lower.replace(":", " ").split())
        for default_key, category in DEFAULT_QB_MAPPINGS.items():
            default_words = set(default_key.replace(":", " ").split())
            if account_words & default_words:  # Any common words
                return category

        return None

    def get_user_mappings(self, user_id: int) -> Dict[str, ExpenseCategory]:
        """Get saved QB account mappings for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT qb_account, agtools_category FROM qb_account_mappings
            WHERE user_id = ?
        """, (user_id,))

        mappings = {
            row["qb_account"].lower(): ExpenseCategory(row["agtools_category"])
            for row in cursor.fetchall()
        }

        conn.close()
        return mappings

    def save_user_mappings(
        self,
        user_id: int,
        mappings: Dict[str, str]
    ) -> int:
        """
        Save QB account mappings for a user.

        Args:
            user_id: User ID
            mappings: Dict of qb_account -> agtools_category

        Returns:
            Number of mappings saved
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        saved = 0
        for qb_account, category in mappings.items():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO qb_account_mappings
                    (user_id, qb_account, agtools_category)
                    VALUES (?, ?, ?)
                """, (user_id, qb_account.lower(), category))
                saved += 1
            except sqlite3.Error:
                continue

        conn.commit()
        conn.close()
        return saved

    def get_all_user_mappings(self, user_id: int) -> List[QBAccountMapping]:
        """Get all saved QB account mappings for a user as list."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, qb_account, agtools_category, is_default, created_at
            FROM qb_account_mappings
            WHERE user_id = ?
            ORDER BY qb_account
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            QBAccountMapping(
                id=row["id"],
                qb_account=row["qb_account"],
                agtools_category=ExpenseCategory(row["agtools_category"]),
                is_default=bool(row["is_default"]),
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            )
            for row in rows
        ]

    def delete_user_mapping(self, user_id: int, mapping_id: int) -> bool:
        """Delete a QB account mapping."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM qb_account_mappings
            WHERE id = ? AND user_id = ?
        """, (mapping_id, user_id))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ========================================================================
    # IMPORT
    # ========================================================================

    def import_quickbooks(
        self,
        csv_content: str,
        user_id: int,
        account_mappings: Dict[str, str],
        source_file: str = "quickbooks_export.csv",
        tax_year: Optional[int] = None,
        save_mappings: bool = True
    ) -> QBImportSummary:
        """
        Import expenses from Accounting Software CSV export.

        Args:
            csv_content: Raw CSV string
            user_id: User performing import
            account_mappings: Dict of qb_account -> agtools_category
            source_file: Original filename
            tax_year: Tax year (derived from dates if not provided)
            save_mappings: Save mappings for future imports

        Returns:
            QBImportSummary with results
        """
        # Save mappings if requested
        if save_mappings and account_mappings:
            self.save_user_mappings(user_id, account_mappings)

        # Detect format and get column mapping
        format_type, headers = self.detect_format(csv_content)
        column_map = self._get_column_mapping(format_type, headers)

        # Parse rows
        rows = self._parse_csv_rows(csv_content, headers, column_map)

        # Create import batch
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO import_batches (source_file, source_type, user_id, status)
            VALUES (?, ?, ?, ?)
        """, (source_file, f"quickbooks_{format_type.value}", user_id, ImportStatus.PROCESSING.value))
        batch_id = cursor.lastrowid

        # Process each row
        successful = 0
        failed = 0
        skipped_non_expense = 0
        duplicates = 0
        errors = []
        by_category: Dict[str, int] = {}
        by_account: Dict[str, float] = {}
        total_amount = 0.0

        # Convert mappings to lowercase for matching
        mappings_lower = {k.lower(): v for k, v in account_mappings.items()}

        for i, row in enumerate(rows, start=1):
            try:
                trans_type = row.get("type", "").lower()

                # Skip non-expense transactions
                if self._is_skippable_transaction(trans_type):
                    skipped_non_expense += 1
                    continue

                # Skip credits/refunds (negative amounts)
                if row.get("is_credit"):
                    skipped_non_expense += 1
                    continue

                # Get amount
                amount = row.get("amount", 0)
                if not amount or amount <= 0:
                    continue

                # Get date
                expense_date = row.get("date")
                if not expense_date:
                    errors.append(f"Row {i}: Missing date")
                    failed += 1
                    continue

                # Determine category from account
                qb_account = row.get("account", "").lower()
                category_str = mappings_lower.get(qb_account)

                if not category_str:
                    # Try partial match
                    for map_key, map_val in mappings_lower.items():
                        if map_key in qb_account or qb_account in map_key:
                            category_str = map_val
                            break

                if not category_str:
                    # Fall back to auto-detection
                    category = self._suggest_category(qb_account, {})
                    if not category:
                        category = ExpenseCategory.OTHER
                else:
                    try:
                        category = ExpenseCategory(category_str)
                    except ValueError:
                        category = ExpenseCategory.OTHER

                # Build reference for duplicate checking
                reference = row.get("num", "")
                vendor = row.get("name", "")

                # Check for duplicates
                if reference:
                    cursor.execute("""
                        SELECT id FROM expenses
                        WHERE quickbooks_id = ? AND expense_date = ? AND amount = ?
                        AND is_active = 1
                    """, (reference, expense_date.isoformat(), amount))
                    if cursor.fetchone():
                        duplicates += 1
                        continue

                # Derive tax year
                year = tax_year or expense_date.year

                # Insert expense
                cursor.execute("""
                    INSERT INTO expenses (
                        category, vendor, description, amount, expense_date, tax_year,
                        source_type, source_reference, import_batch_id, quickbooks_id,
                        notes, created_by_user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    category.value,
                    vendor or None,
                    row.get("memo") or None,
                    amount,
                    expense_date.isoformat(),
                    year,
                    f"quickbooks_{format_type.value}",
                    source_file,
                    batch_id,
                    reference or None,
                    f"QB Account: {row.get('account', 'Unknown')}" if row.get('account') else None,
                    user_id
                ))

                successful += 1
                total_amount += amount

                # Track stats
                by_category[category.value] = by_category.get(category.value, 0) + 1
                orig_account = row.get("account", "Unknown")
                by_account[orig_account] = by_account.get(orig_account, 0) + amount

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
                failed += 1

        # Update batch record
        status = ImportStatus.COMPLETED.value
        error_msg = "; ".join(errors[:10]) if errors else None

        cursor.execute("""
            UPDATE import_batches
            SET total_records = ?, successful = ?, failed = ?, status = ?, error_message = ?
            WHERE id = ?
        """, (len(rows), successful, failed, status, error_msg, batch_id))

        conn.commit()
        conn.close()

        return QBImportSummary(
            batch_id=batch_id,
            total_processed=len(rows),
            successful=successful,
            failed=failed,
            skipped_non_expense=skipped_non_expense,
            duplicates_skipped=duplicates,
            by_category=by_category,
            by_account=by_account,
            total_amount=round(total_amount, 2),
            errors=errors[:20]
        )

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def get_supported_formats(self) -> List[Dict[str, str]]:
        """Get list of supported QB export formats."""
        return [
            {
                "format": QBExportFormat.DESKTOP_TRANSACTION_DETAIL.value,
                "name": "QB Desktop - Transaction Detail Report",
                "description": "Export from Reports > Transaction Detail by Account"
            },
            {
                "format": QBExportFormat.DESKTOP_TRANSACTION_LIST.value,
                "name": "QB Desktop - Transaction List",
                "description": "Export from Reports > Transaction List by Date"
            },
            {
                "format": QBExportFormat.DESKTOP_CHECK_DETAIL.value,
                "name": "QB Desktop - Check Detail",
                "description": "Export from Reports > Check Detail"
            },
            {
                "format": QBExportFormat.ONLINE_EXPORT.value,
                "name": "QB Online Export",
                "description": "Export from Accounting Software Online transactions"
            }
        ]

    def get_category_list(self) -> List[Dict[str, str]]:
        """Get list of available expense categories."""
        return [
            {"value": c.value, "label": c.value.replace("_", " ").title()}
            for c in ExpenseCategory
        ]


# ============================================================================
# SINGLETON
# ============================================================================

_qb_import_service: Optional[AccountingImportService] = None


def get_qb_import_service(db_path: str = "agtools.db") -> AccountingImportService:
    """Get or create the accounting import service singleton."""
    global _qb_import_service
    if _qb_import_service is None:
        _qb_import_service = AccountingImportService(db_path)
    return _qb_import_service
