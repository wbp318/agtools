"""
GenFin Banking Service - Bank Accounts, Transactions, Reconciliation, CHECK PRINTING, ACH/Direct Deposit
Complete banking and check management for farm operations
SQLite-backed persistence
"""

from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional
from enum import Enum
import uuid
import sqlite3
import json
import math



class BankAccountType(Enum):
    """Bank account types"""
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money_market"
    LINE_OF_CREDIT = "line_of_credit"
    CREDIT_CARD = "credit_card"


class TransactionType(Enum):
    """Bank transaction types"""
    DEPOSIT = "deposit"
    CHECK = "check"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    ACH_CREDIT = "ach_credit"
    ACH_DEBIT = "ach_debit"
    WIRE_IN = "wire_in"
    WIRE_OUT = "wire_out"
    FEE = "fee"
    INTEREST = "interest"
    ADJUSTMENT = "adjustment"


class CheckStatus(Enum):
    """Check status"""
    PRINTED = "printed"
    CLEARED = "cleared"
    VOIDED = "voided"
    OUTSTANDING = "outstanding"
    STALE = "stale"


class ReconciliationStatus(Enum):
    """Reconciliation status"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISCREPANCY = "discrepancy"


class CheckFormat(Enum):
    """Check printing formats"""
    STANDARD_TOP = "standard_top"
    STANDARD_MIDDLE = "standard_middle"
    STANDARD_BOTTOM = "standard_bottom"
    VOUCHER_3UP = "voucher_3up"
    WALLET = "wallet"
    PROFESSIONAL_STANDARD = "professional_standard"
    PROFESSIONAL_VOUCHER = "professional_voucher"
    QUICKBOOKS_STANDARD = "quickbooks_standard"
    QUICKBOOKS_VOUCHER = "quickbooks_voucher"


class ACHTransactionCode(Enum):
    """ACH/NACHA transaction codes"""
    CHECKING_CREDIT = "22"
    CHECKING_DEBIT = "27"
    SAVINGS_CREDIT = "32"
    SAVINGS_DEBIT = "37"


# Number to words conversion for check amounts
ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
        'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
        'Seventeen', 'Eighteen', 'Nineteen']
TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
THOUSANDS = ['', 'Thousand', 'Million', 'Billion']


def number_to_words(amount: float) -> str:
    """Convert dollar amount to words for check printing"""
    if amount == 0:
        return "Zero and 00/100"

    dollars = int(amount)
    cents = int(round((amount - dollars) * 100))

    def convert_chunk(n: int) -> str:
        if n == 0:
            return ''
        elif n < 20:
            return ONES[n]
        elif n < 100:
            return TENS[n // 10] + ('' if n % 10 == 0 else '-' + ONES[n % 10])
        else:
            return ONES[n // 100] + ' Hundred' + ('' if n % 100 == 0 else ' ' + convert_chunk(n % 100))

    if dollars == 0:
        words = "Zero"
    else:
        words = ''
        chunk_count = 0
        while dollars > 0:
            chunk = dollars % 1000
            if chunk > 0:
                chunk_words = convert_chunk(chunk)
                if THOUSANDS[chunk_count]:
                    chunk_words += ' ' + THOUSANDS[chunk_count]
                words = chunk_words + (' ' + words if words else '')
            dollars //= 1000
            chunk_count += 1
        words = words.strip()

    return f"{words} and {cents:02d}/100"


class GenFinBankingService:
    """
    GenFin Banking Service - SQLite backed

    Complete banking functionality:
    - Bank account management
    - Transaction tracking
    - CHECK PRINTING (multiple formats, MICR support)
    - Bank reconciliation
    - Transfers between accounts
    - ACH/Direct Deposit file generation (NACHA format)
    """

    _instance = None

    def __new__(cls, db_path: str = "agtools.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "agtools.db"):
        if self._initialized:
            return
        self.db_path = db_path
        self._init_tables()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Bank accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_bank_accounts (
                    bank_account_id TEXT PRIMARY KEY,
                    account_name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    routing_number TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    check_printing_enabled INTEGER DEFAULT 1,
                    next_check_number INTEGER DEFAULT 1001,
                    check_format TEXT DEFAULT 'professional_voucher',
                    ach_enabled INTEGER DEFAULT 0,
                    ach_company_id TEXT DEFAULT '',
                    ach_company_name TEXT DEFAULT '',
                    gl_account_id TEXT,
                    current_balance REAL DEFAULT 0.0,
                    available_balance REAL DEFAULT 0.0,
                    last_reconciled_date TEXT,
                    last_reconciled_balance REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Bank transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_bank_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    bank_account_id TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payee TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    reference_number TEXT DEFAULT '',
                    category_account_id TEXT,
                    is_reconciled INTEGER DEFAULT 0,
                    reconciled_date TEXT,
                    journal_entry_id TEXT,
                    check_id TEXT,
                    transfer_id TEXT,
                    imported INTEGER DEFAULT 0,
                    import_id TEXT,
                    fitid TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (bank_account_id) REFERENCES genfin_bank_accounts (bank_account_id)
                )
            """)

            # Checks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_checks (
                    check_id TEXT PRIMARY KEY,
                    bank_account_id TEXT NOT NULL,
                    check_number INTEGER NOT NULL,
                    check_date TEXT NOT NULL,
                    payee_name TEXT NOT NULL,
                    payee_address_line1 TEXT DEFAULT '',
                    payee_address_line2 TEXT DEFAULT '',
                    payee_city TEXT DEFAULT '',
                    payee_state TEXT DEFAULT '',
                    payee_zip TEXT DEFAULT '',
                    amount REAL NOT NULL,
                    amount_in_words TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    voucher_description TEXT DEFAULT '',
                    bills_paid TEXT DEFAULT '[]',
                    vendor_id TEXT,
                    status TEXT DEFAULT 'outstanding',
                    printed_at TEXT,
                    cleared_date TEXT,
                    voided_date TEXT,
                    void_reason TEXT DEFAULT '',
                    signature_line_1 TEXT DEFAULT '',
                    signature_line_2 TEXT DEFAULT '',
                    requires_two_signatures INTEGER DEFAULT 0,
                    two_signature_threshold REAL DEFAULT 10000.0,
                    journal_entry_id TEXT,
                    transaction_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (bank_account_id) REFERENCES genfin_bank_accounts (bank_account_id)
                )
            """)

            # Check batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_check_batches (
                    batch_id TEXT PRIMARY KEY,
                    bank_account_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    printed_at TEXT,
                    print_status TEXT DEFAULT 'pending',
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (bank_account_id) REFERENCES genfin_bank_accounts (bank_account_id)
                )
            """)

            # Check batch items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_check_batch_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    check_id TEXT NOT NULL,
                    FOREIGN KEY (batch_id) REFERENCES genfin_check_batches (batch_id)
                )
            """)

            # Deposits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_deposits (
                    deposit_id TEXT PRIMARY KEY,
                    bank_account_id TEXT NOT NULL,
                    deposit_date TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    memo TEXT DEFAULT '',
                    journal_entry_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (bank_account_id) REFERENCES genfin_bank_accounts (bank_account_id)
                )
            """)

            # Deposit lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_deposit_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deposit_id TEXT NOT NULL,
                    account_id TEXT,
                    amount REAL DEFAULT 0.0,
                    description TEXT DEFAULT '',
                    FOREIGN KEY (deposit_id) REFERENCES genfin_deposits (deposit_id)
                )
            """)

            # ACH batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_ach_batches (
                    batch_id TEXT PRIMARY KEY,
                    bank_account_id TEXT NOT NULL,
                    batch_date TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    company_name TEXT DEFAULT '',
                    company_id TEXT DEFAULT '',
                    batch_description TEXT DEFAULT '',
                    total_debit REAL DEFAULT 0.0,
                    total_credit REAL DEFAULT 0.0,
                    entry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'created',
                    nacha_file_content TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    submitted_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (bank_account_id) REFERENCES genfin_bank_accounts (bank_account_id)
                )
            """)

            # ACH entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_ach_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    recipient_name TEXT NOT NULL,
                    routing_number TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    account_type TEXT DEFAULT 'checking',
                    amount REAL NOT NULL,
                    transaction_code TEXT NOT NULL,
                    individual_id TEXT DEFAULT '',
                    individual_name TEXT DEFAULT '',
                    FOREIGN KEY (batch_id) REFERENCES genfin_ach_batches (batch_id)
                )
            """)

            # Reconciliations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_reconciliations (
                    reconciliation_id TEXT PRIMARY KEY,
                    bank_account_id TEXT NOT NULL,
                    statement_date TEXT NOT NULL,
                    statement_ending_balance REAL NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    beginning_balance REAL DEFAULT 0.0,
                    cleared_deposits REAL DEFAULT 0.0,
                    cleared_payments REAL DEFAULT 0.0,
                    cleared_balance REAL DEFAULT 0.0,
                    outstanding_deposits TEXT DEFAULT '[]',
                    outstanding_checks TEXT DEFAULT '[]',
                    difference REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'in_progress',
                    completed_at TEXT,
                    completed_by TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (bank_account_id) REFERENCES genfin_bank_accounts (bank_account_id)
                )
            """)

            # Transfers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_transfers (
                    transfer_id TEXT PRIMARY KEY,
                    from_account_id TEXT NOT NULL,
                    to_account_id TEXT NOT NULL,
                    transfer_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    memo TEXT DEFAULT '',
                    from_transaction_id TEXT,
                    to_transaction_id TEXT,
                    journal_entry_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            conn.commit()

    # ==================== BANK ACCOUNTS ====================

    def create_bank_account(
        self,
        account_name: str,
        account_type: str,
        bank_name: str,
        routing_number: str,
        account_number: str,
        gl_account_id: Optional[str] = None,
        starting_balance: float = 0.0,
        starting_check_number: int = 1001,
        check_format: str = "quickbooks_voucher",
        ach_enabled: bool = False,
        ach_company_id: str = "",
        ach_company_name: str = ""
    ) -> Dict:
        """Create a new bank account"""
        bank_account_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if first account
            cursor.execute("SELECT COUNT(*) as count FROM genfin_bank_accounts WHERE is_active = 1")
            is_default = cursor.fetchone()['count'] == 0

            cursor.execute("""
                INSERT INTO genfin_bank_accounts (
                    bank_account_id, account_name, account_type, bank_name,
                    routing_number, account_number, gl_account_id, current_balance,
                    available_balance, next_check_number, check_format,
                    ach_enabled, ach_company_id, ach_company_name, is_default,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bank_account_id, account_name, account_type, bank_name,
                routing_number, account_number, gl_account_id, starting_balance,
                starting_balance, starting_check_number, check_format,
                1 if ach_enabled else 0, ach_company_id, ach_company_name,
                1 if is_default else 0, 1, now, now
            ))
            conn.commit()

        return {
            "success": True,
            "bank_account_id": bank_account_id,
            "account": self.get_bank_account(bank_account_id)
        }

    def update_bank_account(self, bank_account_id: str, **kwargs) -> Dict:
        """Update bank account settings"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        updates = []
        values = []

        field_mapping = {
            'account_name': 'account_name', 'account_type': 'account_type',
            'bank_name': 'bank_name', 'routing_number': 'routing_number',
            'account_number': 'account_number', 'gl_account_id': 'gl_account_id',
            'check_printing_enabled': 'check_printing_enabled',
            'next_check_number': 'next_check_number', 'check_format': 'check_format',
            'ach_enabled': 'ach_enabled', 'ach_company_id': 'ach_company_id',
            'ach_company_name': 'ach_company_name', 'is_active': 'is_active'
        }

        for key, value in kwargs.items():
            if key in field_mapping and value is not None:
                if key in ['check_printing_enabled', 'ach_enabled', 'is_active']:
                    value = 1 if value else 0
                updates.append(f"{field_mapping[key]} = ?")
                values.append(value)

        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())
            values.append(bank_account_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE genfin_bank_accounts SET {', '.join(updates)} WHERE bank_account_id = ?",
                    values
                )
                conn.commit()

        return {
            "success": True,
            "account": self.get_bank_account(bank_account_id)
        }

    def get_bank_account(self, bank_account_id: str) -> Optional[Dict]:
        """Get bank account by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bank_accounts WHERE bank_account_id = ? AND is_active = 1",
                (bank_account_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_account(row)
        return None

    def list_bank_accounts(self, active_only: bool = True) -> List[Dict]:
        """List all bank accounts"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_bank_accounts"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY account_name"

            cursor.execute(query)
            return [self._row_to_account(row) for row in cursor.fetchall()]

    def set_default_account(self, bank_account_id: str) -> Dict:
        """Set default bank account"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE genfin_bank_accounts SET is_default = 0")
            cursor.execute(
                "UPDATE genfin_bank_accounts SET is_default = 1 WHERE bank_account_id = ?",
                (bank_account_id,)
            )
            conn.commit()

        return {"success": True, "message": "Default account updated"}

    def _row_to_account(self, row: sqlite3.Row) -> Dict:
        """Convert account row to dictionary"""
        return {
            "bank_account_id": row['bank_account_id'],
            "account_name": row['account_name'],
            "account_type": row['account_type'],
            "bank_name": row['bank_name'],
            "routing_number": row['routing_number'],
            "account_number_masked": f"****{row['account_number'][-4:]}",
            "check_printing_enabled": bool(row['check_printing_enabled']),
            "next_check_number": row['next_check_number'],
            "check_format": row['check_format'],
            "ach_enabled": bool(row['ach_enabled']),
            "gl_account_id": row['gl_account_id'],
            "current_balance": round(row['current_balance'], 2),
            "available_balance": round(row['available_balance'], 2),
            "last_reconciled_date": row['last_reconciled_date'],
            "last_reconciled_balance": row['last_reconciled_balance'],
            "is_active": bool(row['is_active']),
            "is_default": bool(row['is_default']),
            "created_at": row['created_at']
        }

    # ==================== CHECK PRINTING ====================

    def create_check(
        self,
        bank_account_id: str,
        payee_name: str,
        amount: float,
        check_date: str,
        memo: str = "",
        payee_address_line1: str = "",
        payee_address_line2: str = "",
        payee_city: str = "",
        payee_state: str = "",
        payee_zip: str = "",
        vendor_id: Optional[str] = None,
        bills_paid: List[Dict] = None,
        voucher_description: str = "",
        check_number: Optional[int] = None
    ) -> Dict:
        """Create a check for printing"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bank_accounts WHERE bank_account_id = ? AND is_active = 1",
                (bank_account_id,)
            )
            account_row = cursor.fetchone()
            if not account_row:
                return {"success": False, "error": "Bank account not found"}

            if not account_row['check_printing_enabled']:
                return {"success": False, "error": "Check printing not enabled for this account"}

            check_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            # Use provided check number or get next
            if check_number is None:
                check_number = account_row['next_check_number']
                cursor.execute(
                    "UPDATE genfin_bank_accounts SET next_check_number = ? WHERE bank_account_id = ?",
                    (check_number + 1, bank_account_id)
                )

            # Convert amount to words
            amount_words = number_to_words(amount)

            # Build voucher description from bills if provided
            if bills_paid and not voucher_description:
                desc_lines = []
                for bill in bills_paid:
                    desc_lines.append(f"Bill #{bill.get('bill_number', 'N/A')}: ${bill.get('amount', 0):.2f}")
                voucher_description = "\n".join(desc_lines)

            # Insert check
            cursor.execute("""
                INSERT INTO genfin_checks (
                    check_id, bank_account_id, check_number, check_date, payee_name,
                    payee_address_line1, payee_address_line2, payee_city, payee_state,
                    payee_zip, amount, amount_in_words, memo, voucher_description,
                    bills_paid, vendor_id, status, requires_two_signatures, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                check_id, bank_account_id, check_number, check_date, payee_name,
                payee_address_line1, payee_address_line2, payee_city, payee_state,
                payee_zip, amount, amount_words, memo, voucher_description,
                json.dumps(bills_paid or []), vendor_id, 'outstanding',
                1 if amount >= 10000.0 else 0, now, 1
            ))

            # Create bank transaction
            trans_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO genfin_bank_transactions (
                    transaction_id, bank_account_id, transaction_date, transaction_type,
                    amount, payee, memo, reference_number, check_id, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trans_id, bank_account_id, check_date, 'check',
                -amount, payee_name, memo, str(check_number), check_id, now, 1
            ))

            # Update check with transaction ID
            cursor.execute(
                "UPDATE genfin_checks SET transaction_id = ? WHERE check_id = ?",
                (trans_id, check_id)
            )

            # Update account balance
            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance - ? WHERE bank_account_id = ?",
                (amount, bank_account_id)
            )

            conn.commit()

        check = self._get_check(check_id)
        return {
            "success": True,
            "check_id": check_id,
            "check_number": check_number,
            "check": check
        }

    def get_check_print_data(self, check_id: str) -> Dict:
        """Get formatted data for printing a check"""
        check = self._get_check(check_id)
        if not check:
            return {"error": "Check not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bank_accounts WHERE bank_account_id = ?",
                (check['bank_account_id'],)
            )
            account = cursor.fetchone()

        if not account:
            return {"error": "Bank account not found"}

        # Format MICR line
        micr_routing = f"⑆{account['routing_number']}⑆"
        micr_account = f"{account['account_number']}⑈"
        micr_check = f"{check['check_number']:08d}"
        micr_line = f"{micr_routing} {micr_account} {micr_check}"
        micr_line_alt = f"C{account['routing_number']}C {account['account_number']}D {check['check_number']:08d}"

        # Format payee address
        payee_address = check['payee_address_line1']
        if check.get('payee_address_line2'):
            payee_address += f"\n{check['payee_address_line2']}"
        if check.get('payee_city') or check.get('payee_state') or check.get('payee_zip'):
            payee_address += f"\n{check['payee_city']}, {check['payee_state']} {check['payee_zip']}"

        # Format date
        check_date = datetime.strptime(check['check_date'], "%Y-%m-%d").date()
        date_formatted = check_date.strftime("%m/%d/%Y")
        date_long = check_date.strftime("%B %d, %Y")

        return {
            "check_id": check['check_id'],
            "check_number": check['check_number'],
            "check_number_formatted": f"{check['check_number']:08d}",
            "bank_name": account['bank_name'],
            "routing_number": account['routing_number'],
            "account_number": account['account_number'],
            "account_number_masked": f"****{account['account_number'][-4:]}",
            "micr_line": micr_line,
            "micr_line_alt": micr_line_alt,
            "check_date": check['check_date'],
            "date_formatted": date_formatted,
            "date_long": date_long,
            "payee_name": check['payee_name'],
            "payee_address": payee_address,
            "payee_address_line1": check['payee_address_line1'],
            "payee_address_line2": check.get('payee_address_line2', ''),
            "payee_city": check.get('payee_city', ''),
            "payee_state": check.get('payee_state', ''),
            "payee_zip": check.get('payee_zip', ''),
            "amount": check['amount'],
            "amount_formatted": f"${check['amount']:,.2f}",
            "amount_numeric": f"**{check['amount']:,.2f}**",
            "amount_in_words": check['amount_in_words'],
            "amount_in_words_line": f"{check['amount_in_words']}{'*' * (50 - len(check['amount_in_words']))}",
            "memo": check['memo'],
            "voucher_description": check.get('voucher_description', ''),
            "bills_paid": check.get('bills_paid', []),
            "requires_two_signatures": check['requires_two_signatures'],
            "signature_line_1": check.get('signature_line_1', ''),
            "signature_line_2": check.get('signature_line_2', ''),
            "check_format": account['check_format'],
            "status": check['status'],
            "printed_at": check.get('printed_at')
        }

    def get_check_print_layout(self, check_id: str, format_override: Optional[str] = None) -> Dict:
        """Get complete print layout for a check with positioning"""
        print_data = self.get_check_print_data(check_id)
        if "error" in print_data:
            return print_data

        check_format = CheckFormat(format_override) if format_override else CheckFormat(print_data['check_format'])

        # Define print positions (in inches from top-left)
        if check_format == CheckFormat.QUICKBOOKS_VOUCHER:
            layout = {
                "page_size": {"width": 8.5, "height": 11},
                "check_area": {"top": 7.0, "height": 3.5},
                "fields": {
                    "date": {"x": 6.5, "y": 7.3},
                    "payee_name": {"x": 1.0, "y": 7.8},
                    "amount_numeric": {"x": 6.8, "y": 7.8},
                    "amount_words": {"x": 0.5, "y": 8.3, "width": 5.5},
                    "payee_address": {"x": 1.0, "y": 8.6},
                    "memo": {"x": 0.5, "y": 9.8},
                    "signature_line_1": {"x": 4.5, "y": 9.8},
                    "signature_line_2": {"x": 4.5, "y": 10.2},
                    "micr_line": {"x": 0.5, "y": 10.3},
                    "check_number": {"x": 7.0, "y": 7.0}
                },
                "voucher_1": {
                    "top": 0.0, "height": 3.5,
                    "fields": {"payee": {"x": 0.5, "y": 0.5}, "date": {"x": 6.0, "y": 0.5},
                              "check_number": {"x": 7.0, "y": 0.5}, "description": {"x": 0.5, "y": 1.0},
                              "amount": {"x": 6.5, "y": 2.5}}
                },
                "voucher_2": {
                    "top": 3.5, "height": 3.5,
                    "fields": {"payee": {"x": 0.5, "y": 4.0}, "date": {"x": 6.0, "y": 4.0},
                              "check_number": {"x": 7.0, "y": 4.0}, "description": {"x": 0.5, "y": 4.5},
                              "amount": {"x": 6.5, "y": 6.0}}
                }
            }
        else:
            layout = {
                "page_size": {"width": 8.5, "height": 11},
                "check_area": {"top": 0.0, "height": 3.5},
                "fields": {
                    "date": {"x": 6.5, "y": 0.5},
                    "payee_name": {"x": 1.0, "y": 1.0},
                    "amount_numeric": {"x": 6.8, "y": 1.0},
                    "amount_words": {"x": 0.5, "y": 1.5, "width": 5.5},
                    "payee_address": {"x": 1.0, "y": 2.0},
                    "memo": {"x": 0.5, "y": 2.8},
                    "signature_line_1": {"x": 4.5, "y": 3.0},
                    "micr_line": {"x": 0.5, "y": 3.3},
                    "check_number": {"x": 7.0, "y": 0.2}
                }
            }

        return {
            "print_data": print_data,
            "layout": layout,
            "format": check_format.value
        }

    def mark_check_printed(self, check_id: str) -> Dict:
        """Mark a check as printed"""
        check = self._get_check(check_id)
        if not check:
            return {"success": False, "error": "Check not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_checks SET status = ?, printed_at = ?
                WHERE check_id = ?
            """, ('printed', datetime.now(timezone.utc).isoformat(), check_id))
            conn.commit()

        return {
            "success": True,
            "check": self._get_check(check_id)
        }

    def void_check(self, check_id: str, reason: str = "") -> Dict:
        """Void a check"""
        check = self._get_check(check_id)
        if not check:
            return {"success": False, "error": "Check not found"}

        if check['status'] == 'cleared':
            return {"success": False, "error": "Cannot void a cleared check"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update check status
            cursor.execute("""
                UPDATE genfin_checks SET status = ?, voided_date = ?, void_reason = ?
                WHERE check_id = ?
            """, ('voided', date.today().isoformat(), reason, check_id))

            # Reverse the balance change
            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance + ? WHERE bank_account_id = ?",
                (check['amount'], check['bank_account_id'])
            )

            conn.commit()

        return {
            "success": True,
            "check": self._get_check(check_id)
        }

    def create_check_batch(self, bank_account_id: str, check_ids: List[str]) -> Dict:
        """Create a batch of checks for printing"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        # Validate all checks
        for check_id in check_ids:
            check = self._get_check(check_id)
            if not check:
                return {"success": False, "error": f"Check {check_id} not found"}
            if check['bank_account_id'] != bank_account_id:
                return {"success": False, "error": f"Check {check_id} is not from this bank account"}

        batch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_check_batches (batch_id, bank_account_id, created_at, print_status, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (batch_id, bank_account_id, now, 'pending', 1))

            for check_id in check_ids:
                cursor.execute("""
                    INSERT INTO genfin_check_batch_items (batch_id, check_id) VALUES (?, ?)
                """, (batch_id, check_id))

            conn.commit()

        return {
            "success": True,
            "batch_id": batch_id,
            "check_count": len(check_ids)
        }

    def get_check_batch_print_data(self, batch_id: str) -> Dict:
        """Get print data for entire batch"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_check_batches WHERE batch_id = ? AND is_active = 1",
                (batch_id,)
            )
            batch = cursor.fetchone()
            if not batch:
                return {"error": "Batch not found"}

            cursor.execute(
                "SELECT check_id FROM genfin_check_batch_items WHERE batch_id = ?",
                (batch_id,)
            )
            check_ids = [row['check_id'] for row in cursor.fetchall()]

        checks_data = []
        for check_id in check_ids:
            check_data = self.get_check_print_layout(check_id)
            if "error" not in check_data:
                checks_data.append(check_data)

        return {
            "batch_id": batch_id,
            "bank_account_id": batch['bank_account_id'],
            "checks": checks_data,
            "total_checks": len(checks_data),
            "total_amount": sum(c["print_data"]["amount"] for c in checks_data)
        }

    def list_checks(
        self,
        bank_account_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        vendor_id: Optional[str] = None
    ) -> List[Dict]:
        """List checks with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_checks WHERE is_active = 1"
            params = []

            if bank_account_id:
                query += " AND bank_account_id = ?"
                params.append(bank_account_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if vendor_id:
                query += " AND vendor_id = ?"
                params.append(vendor_id)
            if start_date:
                query += " AND check_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND check_date <= ?"
                params.append(end_date)

            query += " ORDER BY check_number DESC"

            cursor.execute(query, params)
            return [self._row_to_check(row) for row in cursor.fetchall()]

    def get_outstanding_checks(self, bank_account_id: str) -> Dict:
        """Get list of outstanding (uncleared) checks"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"error": "Bank account not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_checks
                WHERE bank_account_id = ? AND is_active = 1
                AND status IN ('outstanding', 'printed')
                ORDER BY check_number
            """, (bank_account_id,))

            outstanding = []
            total = 0.0
            today = date.today()

            for row in cursor.fetchall():
                check_dict = self._row_to_check(row)
                check_date = datetime.strptime(row['check_date'], "%Y-%m-%d").date()
                if (today - check_date).days > 180:
                    check_dict["is_stale"] = True
                outstanding.append(check_dict)
                total += row['amount']

        return {
            "outstanding_checks": outstanding,
            "count": len(outstanding),
            "total_amount": round(total, 2)
        }

    def _get_check(self, check_id: str) -> Optional[Dict]:
        """Get check by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_checks WHERE check_id = ? AND is_active = 1",
                (check_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_check(row)
        return None

    def _row_to_check(self, row: sqlite3.Row) -> Dict:
        """Convert check row to dictionary"""
        return {
            "check_id": row['check_id'],
            "bank_account_id": row['bank_account_id'],
            "check_number": row['check_number'],
            "check_date": row['check_date'],
            "payee_name": row['payee_name'],
            "payee_address_line1": row['payee_address_line1'] or '',
            "payee_address_line2": row['payee_address_line2'] or '',
            "payee_city": row['payee_city'] or '',
            "payee_state": row['payee_state'] or '',
            "payee_zip": row['payee_zip'] or '',
            "payee_address": f"{row['payee_address_line1'] or ''}, {row['payee_city'] or ''}, {row['payee_state'] or ''} {row['payee_zip'] or ''}",
            "amount": row['amount'],
            "amount_formatted": f"${row['amount']:,.2f}",
            "amount_in_words": row['amount_in_words'],
            "memo": row['memo'] or '',
            "voucher_description": row['voucher_description'] or '',
            "status": row['status'],
            "vendor_id": row['vendor_id'],
            "bills_paid": json.loads(row['bills_paid']) if row['bills_paid'] else [],
            "printed_at": row['printed_at'],
            "cleared_date": row['cleared_date'],
            "voided_date": row['voided_date'],
            "void_reason": row['void_reason'] or '',
            "requires_two_signatures": bool(row['requires_two_signatures']),
            "signature_line_1": row['signature_line_1'] or '',
            "signature_line_2": row['signature_line_2'] or '',
            "created_at": row['created_at']
        }

    # ==================== DEPOSITS ====================

    def create_deposit(
        self,
        bank_account_id: str,
        deposit_date: str,
        lines: List[Dict],
        memo: str = ""
    ) -> Dict:
        """Create a bank deposit"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        deposit_id = str(uuid.uuid4())
        total_amount = sum(line.get("amount", 0) for line in lines)
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO genfin_deposits (
                    deposit_id, bank_account_id, deposit_date, amount, memo, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (deposit_id, bank_account_id, deposit_date, total_amount, memo, now, 1))

            for line in lines:
                cursor.execute("""
                    INSERT INTO genfin_deposit_lines (deposit_id, account_id, amount, description)
                    VALUES (?, ?, ?, ?)
                """, (deposit_id, line.get('account_id'), line.get('amount', 0), line.get('description', '')))

            # Update bank account balance
            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance + ? WHERE bank_account_id = ?",
                (total_amount, bank_account_id)
            )

            conn.commit()

        return {
            "success": True,
            "deposit_id": deposit_id,
            "deposit": self.get_deposit(deposit_id)
        }

    def get_deposit(self, deposit_id: str) -> Optional[Dict]:
        """Get deposit by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_deposits WHERE deposit_id = ? AND is_active = 1",
                (deposit_id,)
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "SELECT * FROM genfin_deposit_lines WHERE deposit_id = ?",
                    (deposit_id,)
                )
                lines = [
                    {"account_id": row_line['account_id'], "amount": row_line['amount'], "description": row_line['description'] or ''}
                    for row_line in cursor.fetchall()
                ]
                return {
                    "deposit_id": row['deposit_id'],
                    "bank_account_id": row['bank_account_id'],
                    "deposit_date": row['deposit_date'],
                    "amount": row['amount'],
                    "memo": row['memo'] or '',
                    "lines": lines,
                    "journal_entry_id": row['journal_entry_id'],
                    "created_at": row['created_at']
                }
        return None

    def delete_deposit(self, deposit_id: str) -> bool:
        """Delete a deposit"""
        deposit = self.get_deposit(deposit_id)
        if not deposit:
            return False

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE genfin_deposits SET is_active = 0 WHERE deposit_id = ?",
                (deposit_id,)
            )
            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance - ? WHERE bank_account_id = ?",
                (deposit['amount'], deposit['bank_account_id'])
            )
            conn.commit()
        return True

    def list_deposits(
        self,
        bank_account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List deposits with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_deposits WHERE is_active = 1"
            params = []

            if bank_account_id:
                query += " AND bank_account_id = ?"
                params.append(bank_account_id)
            if start_date:
                query += " AND deposit_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND deposit_date <= ?"
                params.append(end_date)

            query += " ORDER BY deposit_date DESC"

            cursor.execute(query, params)
            result = []
            for row in cursor.fetchall():
                result.append({
                    "deposit_id": row['deposit_id'],
                    "bank_account_id": row['bank_account_id'],
                    "deposit_date": row['deposit_date'],
                    "amount": row['amount'],
                    "memo": row['memo'] or '',
                    "created_at": row['created_at']
                })
            return result

    def get_undeposited_funds(self) -> List[Dict]:
        """Get payments in undeposited funds account."""
        from datetime import date, timedelta
        today = date.today()

        # Sample demo data for undeposited funds
        demo_payments = [
            {
                "id": "udf-001",
                "date": (today - timedelta(days=2)).isoformat(),
                "type": "Payment",
                "customer": "Greenfield Farms",
                "amount": 1250.00,
                "method": "Check",
                "reference": "1042"
            },
            {
                "id": "udf-002",
                "date": (today - timedelta(days=1)).isoformat(),
                "type": "Payment",
                "customer": "Harvest Valley Co-op",
                "amount": 3500.00,
                "method": "Check",
                "reference": "8876"
            },
            {
                "id": "udf-003",
                "date": today.isoformat(),
                "type": "Payment",
                "customer": "AgriTech Solutions",
                "amount": 875.50,
                "method": "Credit Card",
                "reference": "CC-4521"
            }
        ]
        return demo_payments

    # ==================== ACH / DIRECT DEPOSIT ====================

    def create_ach_batch(
        self,
        bank_account_id: str,
        effective_date: str,
        batch_description: str,
        entries: List[Dict]
    ) -> Dict:
        """Create an ACH/Direct Deposit batch"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bank_accounts WHERE bank_account_id = ? AND is_active = 1",
                (bank_account_id,)
            )
            account = cursor.fetchone()

            if not account:
                return {"success": False, "error": "Bank account not found"}
            if not account['ach_enabled']:
                return {"success": False, "error": "ACH not enabled for this account"}

            batch_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            total_credit = 0.0
            total_debit = 0.0

            for entry in entries:
                amount = entry.get("amount", 0)
                trans_code = entry.get("transaction_code", "22")
                if trans_code in ["22", "32"]:
                    total_credit += amount
                else:
                    total_debit += amount

            cursor.execute("""
                INSERT INTO genfin_ach_batches (
                    batch_id, bank_account_id, batch_date, effective_date, company_name,
                    company_id, batch_description, total_debit, total_credit,
                    entry_count, status, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_id, bank_account_id, date.today().isoformat(), effective_date,
                account['ach_company_name'][:16] if account['ach_company_name'] else '',
                account['ach_company_id'], batch_description[:10],
                round(total_debit, 2), round(total_credit, 2),
                len(entries), 'created', now, 1
            ))

            for entry in entries:
                cursor.execute("""
                    INSERT INTO genfin_ach_entries (
                        batch_id, recipient_name, routing_number, account_number,
                        account_type, amount, transaction_code, individual_id, individual_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    entry.get("recipient_name", "")[:22],
                    entry.get("routing_number", ""),
                    entry.get("account_number", ""),
                    entry.get("account_type", "checking"),
                    entry.get("amount", 0),
                    entry.get("transaction_code", "22"),
                    entry.get("individual_id", "")[:15],
                    entry.get("individual_name", entry.get("recipient_name", ""))[:22]
                ))

            conn.commit()

        return {
            "success": True,
            "batch_id": batch_id,
            "entry_count": len(entries),
            "total_credit": round(total_credit, 2),
            "total_debit": round(total_debit, 2)
        }

    def generate_nacha_file(self, batch_id: str) -> Dict:
        """Generate NACHA format file for ACH batch"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM genfin_ach_batches WHERE batch_id = ? AND is_active = 1",
                (batch_id,)
            )
            batch = cursor.fetchone()
            if not batch:
                return {"error": "Batch not found"}

            cursor.execute(
                "SELECT * FROM genfin_bank_accounts WHERE bank_account_id = ?",
                (batch['bank_account_id'],)
            )
            account = cursor.fetchone()
            if not account:
                return {"error": "Bank account not found"}

            cursor.execute(
                "SELECT * FROM genfin_ach_entries WHERE batch_id = ?",
                (batch_id,)
            )
            entries = cursor.fetchall()

            lines = []

            # File Header Record (1)
            file_creation_date = datetime.now(timezone.utc).strftime("%y%m%d")
            file_creation_time = datetime.now(timezone.utc).strftime("%H%M")

            file_header = (
                "1"
                "01"
                f" {account['routing_number']:>9}"
                f"{account['ach_company_id']:>10}"
                f"{file_creation_date}"
                f"{file_creation_time}"
                "A"
                "094"
                "10"
                "1"
                f"{account['bank_name']:<23}"
                f"{account['ach_company_name']:<23}"
                "        "
            )
            lines.append(file_header)

            # Batch Header Record (5)
            effective_date = datetime.strptime(batch['effective_date'], "%Y-%m-%d").strftime("%y%m%d")
            batch_date = datetime.strptime(batch['batch_date'], "%Y-%m-%d").strftime("%y%m%d")

            batch_header = (
                "5"
                "200"
                f"{batch['company_name']:<16}"
                f"{' ' * 20}"
                f"{batch['company_id']:<10}"
                "PPD"
                f"{batch['batch_description']:<10}"
                f"{batch_date}"
                f"{effective_date}"
                "   "
                "1"
                f"{account['routing_number'][:8]:<8}"
                f"{1:07d}"
            )
            lines.append(batch_header)

            # Entry Detail Records (6)
            entry_hash = 0
            trace_number = 1

            for entry in entries:
                routing_num = entry['routing_number']
                entry_hash += int(routing_num[:8])

                entry_detail = (
                    "6"
                    f"{entry['transaction_code']}"
                    f"{routing_num[:8]}{routing_num[8] if len(routing_num) > 8 else ' '}"
                    f"{entry['account_number']:<17}"
                    f"{int(entry['amount'] * 100):010d}"
                    f"{entry['individual_id']:<15}"
                    f"{entry['individual_name']:<22}"
                    "  "
                    "0"
                    f"{account['routing_number'][:8]}{trace_number:07d}"
                )
                lines.append(entry_detail)
                trace_number += 1

            # Batch Control Record (8)
            entry_hash_mod = entry_hash % 10000000000

            batch_control = (
                "8"
                "200"
                f"{batch['entry_count']:06d}"
                f"{entry_hash_mod:010d}"
                f"{int(batch['total_debit'] * 100):012d}"
                f"{int(batch['total_credit'] * 100):012d}"
                f"{batch['company_id']:<10}"
                f"{' ' * 19}"
                f"{' ' * 6}"
                f"{account['routing_number'][:8]:<8}"
                f"{1:07d}"
            )
            lines.append(batch_control)

            # File Control Record (9)
            block_count = math.ceil((len(lines) + 1) / 10)

            file_control = (
                "9"
                f"{1:06d}"
                f"{block_count:06d}"
                f"{batch['entry_count']:08d}"
                f"{entry_hash_mod:010d}"
                f"{int(batch['total_debit'] * 100):012d}"
                f"{int(batch['total_credit'] * 100):012d}"
                f"{' ' * 39}"
            )
            lines.append(file_control)

            # Pad to block size
            while len(lines) % 10 != 0:
                lines.append("9" * 94)

            nacha_content = "\n".join(lines)

            # Update batch
            cursor.execute("""
                UPDATE genfin_ach_batches SET nacha_file_content = ?, status = ?
                WHERE batch_id = ?
            """, (nacha_content, 'generated', batch_id))
            conn.commit()

        return {
            "success": True,
            "batch_id": batch_id,
            "file_content": nacha_content,
            "record_count": len(lines),
            "entry_count": batch['entry_count'],
            "total_credit": batch['total_credit'],
            "total_debit": batch['total_debit'],
            "filename": f"ACH_{batch['batch_date'].replace('-', '')}_{batch_id[:8]}.txt"
        }

    def list_ach_batches(
        self,
        bank_account_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List ACH batches"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_ach_batches WHERE is_active = 1"
            params = []

            if bank_account_id:
                query += " AND bank_account_id = ?"
                params.append(bank_account_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if start_date:
                query += " AND batch_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND batch_date <= ?"
                params.append(end_date)

            query += " ORDER BY batch_date DESC"

            cursor.execute(query, params)
            return [
                {
                    "batch_id": row['batch_id'],
                    "bank_account_id": row['bank_account_id'],
                    "batch_date": row['batch_date'],
                    "effective_date": row['effective_date'],
                    "batch_description": row['batch_description'],
                    "entry_count": row['entry_count'],
                    "total_credit": row['total_credit'],
                    "total_debit": row['total_debit'],
                    "status": row['status'],
                    "created_at": row['created_at']
                }
                for row in cursor.fetchall()
            ]

    # ==================== TRANSACTIONS & RECONCILIATION ====================

    def record_deposit(
        self,
        bank_account_id: str,
        deposit_date: str,
        amount: float,
        memo: str = "",
        reference_number: str = "",
        category_account_id: Optional[str] = None
    ) -> Dict:
        """Record a deposit"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        trans_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_bank_transactions (
                    transaction_id, bank_account_id, transaction_date, transaction_type,
                    amount, memo, reference_number, category_account_id, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trans_id, bank_account_id, deposit_date, 'deposit',
                amount, memo, reference_number, category_account_id, now, 1
            ))

            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance + ? WHERE bank_account_id = ?",
                (amount, bank_account_id)
            )
            conn.commit()

        return {
            "success": True,
            "transaction_id": trans_id,
            "transaction": self._get_transaction(trans_id)
        }

    def record_withdrawal(
        self,
        bank_account_id: str,
        withdrawal_date: str,
        amount: float,
        payee: str = "",
        memo: str = "",
        reference_number: str = "",
        category_account_id: Optional[str] = None
    ) -> Dict:
        """Record a withdrawal"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        trans_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_bank_transactions (
                    transaction_id, bank_account_id, transaction_date, transaction_type,
                    amount, payee, memo, reference_number, category_account_id, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trans_id, bank_account_id, withdrawal_date, 'withdrawal',
                -amount, payee, memo, reference_number, category_account_id, now, 1
            ))

            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance - ? WHERE bank_account_id = ?",
                (amount, bank_account_id)
            )
            conn.commit()

        return {
            "success": True,
            "transaction_id": trans_id,
            "transaction": self._get_transaction(trans_id)
        }

    def create_transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        transfer_date: str,
        amount: float,
        memo: str = ""
    ) -> Dict:
        """Transfer between bank accounts"""
        from_account = self.get_bank_account(from_account_id)
        to_account = self.get_bank_account(to_account_id)

        if not from_account:
            return {"success": False, "error": "Source account not found"}
        if not to_account:
            return {"success": False, "error": "Destination account not found"}

        transfer_id = str(uuid.uuid4())
        from_trans_id = str(uuid.uuid4())
        to_trans_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create outgoing transaction
            cursor.execute("""
                INSERT INTO genfin_bank_transactions (
                    transaction_id, bank_account_id, transaction_date, transaction_type,
                    amount, memo, transfer_id, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                from_trans_id, from_account_id, transfer_date, 'transfer',
                -amount, f"Transfer to {to_account['account_name']}", transfer_id, now, 1
            ))

            # Create incoming transaction
            cursor.execute("""
                INSERT INTO genfin_bank_transactions (
                    transaction_id, bank_account_id, transaction_date, transaction_type,
                    amount, memo, transfer_id, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                to_trans_id, to_account_id, transfer_date, 'transfer',
                amount, f"Transfer from {from_account['account_name']}", transfer_id, now, 1
            ))

            # Update balances
            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance - ? WHERE bank_account_id = ?",
                (amount, from_account_id)
            )
            cursor.execute(
                "UPDATE genfin_bank_accounts SET current_balance = current_balance + ? WHERE bank_account_id = ?",
                (amount, to_account_id)
            )

            # Create transfer record
            cursor.execute("""
                INSERT INTO genfin_transfers (
                    transfer_id, from_account_id, to_account_id, transfer_date, amount,
                    memo, from_transaction_id, to_transaction_id, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transfer_id, from_account_id, to_account_id, transfer_date, amount,
                memo, from_trans_id, to_trans_id, now, 1
            ))

            conn.commit()

        return {
            "success": True,
            "transfer_id": transfer_id,
            "from_transaction_id": from_trans_id,
            "to_transaction_id": to_trans_id
        }

    def start_reconciliation(
        self,
        bank_account_id: str,
        statement_date: str,
        statement_ending_balance: float
    ) -> Dict:
        """Start bank reconciliation"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"success": False, "error": "Bank account not found"}

        recon_id = str(uuid.uuid4())
        s_date = datetime.strptime(statement_date, "%Y-%m-%d").date()
        now = datetime.now(timezone.utc).isoformat()

        # Determine period start
        if account['last_reconciled_date']:
            period_start = datetime.strptime(account['last_reconciled_date'], "%Y-%m-%d").date() + timedelta(days=1)
            beginning_balance = account['last_reconciled_balance']
        else:
            period_start = s_date - timedelta(days=30)
            beginning_balance = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_reconciliations (
                    reconciliation_id, bank_account_id, statement_date, statement_ending_balance,
                    period_start, period_end, beginning_balance, status, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recon_id, bank_account_id, statement_date, statement_ending_balance,
                period_start.isoformat(), statement_date, beginning_balance, 'in_progress', now, 1
            ))
            conn.commit()

        return {
            "success": True,
            "reconciliation_id": recon_id,
            "period_start": period_start.isoformat(),
            "period_end": statement_date,
            "beginning_balance": beginning_balance,
            "statement_ending_balance": statement_ending_balance
        }

    def mark_transaction_cleared(self, reconciliation_id: str, transaction_id: str) -> Dict:
        """Mark a transaction as cleared in reconciliation"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM genfin_reconciliations WHERE reconciliation_id = ? AND is_active = 1",
                (reconciliation_id,)
            )
            if not cursor.fetchone():
                return {"success": False, "error": "Reconciliation not found"}

            cursor.execute(
                "SELECT * FROM genfin_bank_transactions WHERE transaction_id = ? AND is_active = 1",
                (transaction_id,)
            )
            trans = cursor.fetchone()
            if not trans:
                return {"success": False, "error": "Transaction not found"}

            cursor.execute("""
                UPDATE genfin_bank_transactions
                SET is_reconciled = 1, reconciled_date = ?
                WHERE transaction_id = ?
            """, (date.today().isoformat(), transaction_id))

            # If it's a check, update check status
            if trans['check_id']:
                cursor.execute("""
                    UPDATE genfin_checks SET status = ?, cleared_date = ?
                    WHERE check_id = ?
                """, ('cleared', date.today().isoformat(), trans['check_id']))

            conn.commit()

        return {"success": True, "message": "Transaction marked as cleared"}

    def complete_reconciliation(self, reconciliation_id: str, completed_by: str) -> Dict:
        """Complete bank reconciliation"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM genfin_reconciliations WHERE reconciliation_id = ? AND is_active = 1",
                (reconciliation_id,)
            )
            recon = cursor.fetchone()
            if not recon:
                return {"success": False, "error": "Reconciliation not found"}

            # Calculate cleared amounts
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN amount > 0 AND is_reconciled = 1 THEN amount ELSE 0 END), 0) as cleared_deposits,
                    COALESCE(SUM(CASE WHEN amount < 0 AND is_reconciled = 1 THEN ABS(amount) ELSE 0 END), 0) as cleared_payments
                FROM genfin_bank_transactions
                WHERE bank_account_id = ? AND is_active = 1
                AND transaction_date <= ?
            """, (recon['bank_account_id'], recon['statement_date']))

            totals = cursor.fetchone()
            cleared_deposits = totals['cleared_deposits']
            cleared_payments = totals['cleared_payments']

            # Get outstanding items
            cursor.execute("""
                SELECT transaction_id, amount FROM genfin_bank_transactions
                WHERE bank_account_id = ? AND is_active = 1 AND is_reconciled = 0
                AND transaction_date <= ?
            """, (recon['bank_account_id'], recon['statement_date']))

            outstanding_deposits = []
            outstanding_checks = []
            for row in cursor.fetchall():
                if row['amount'] > 0:
                    outstanding_deposits.append(row['transaction_id'])
                else:
                    outstanding_checks.append(row['transaction_id'])

            # Calculate difference
            cleared_balance = recon['beginning_balance'] + cleared_deposits - cleared_payments
            difference = round(recon['statement_ending_balance'] - cleared_balance, 2)

            status = 'completed' if abs(difference) < 0.01 else 'discrepancy'

            # Update reconciliation
            cursor.execute("""
                UPDATE genfin_reconciliations SET
                    cleared_deposits = ?, cleared_payments = ?, cleared_balance = ?,
                    outstanding_deposits = ?, outstanding_checks = ?, difference = ?,
                    status = ?, completed_at = ?, completed_by = ?
                WHERE reconciliation_id = ?
            """, (
                cleared_deposits, cleared_payments, cleared_balance,
                json.dumps(outstanding_deposits), json.dumps(outstanding_checks),
                difference, status, datetime.now(timezone.utc).isoformat(), completed_by, reconciliation_id
            ))

            # Update bank account if balanced
            if abs(difference) < 0.01:
                cursor.execute("""
                    UPDATE genfin_bank_accounts
                    SET last_reconciled_date = ?, last_reconciled_balance = ?
                    WHERE bank_account_id = ?
                """, (recon['statement_date'], recon['statement_ending_balance'], recon['bank_account_id']))

            conn.commit()

        return {
            "success": True,
            "status": status,
            "cleared_deposits": cleared_deposits,
            "cleared_payments": cleared_payments,
            "cleared_balance": cleared_balance,
            "outstanding_deposits_count": len(outstanding_deposits),
            "outstanding_checks_count": len(outstanding_checks),
            "difference": difference,
            "is_balanced": abs(difference) < 0.01
        }

    def list_transactions(
        self,
        bank_account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None,
        unreconciled_only: bool = False
    ) -> List[Dict]:
        """List bank transactions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_bank_transactions WHERE bank_account_id = ? AND is_active = 1"
            params = [bank_account_id]

            if start_date:
                query += " AND transaction_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND transaction_date <= ?"
                params.append(end_date)
            if transaction_type:
                query += " AND transaction_type = ?"
                params.append(transaction_type)
            if unreconciled_only:
                query += " AND is_reconciled = 0"

            query += " ORDER BY transaction_date DESC"

            cursor.execute(query, params)
            return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def get_register(self, bank_account_id: str, start_date: str, end_date: str) -> Dict:
        """Get check register / bank register for account"""
        account = self.get_bank_account(bank_account_id)
        if not account:
            return {"error": "Bank account not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get opening balance
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM genfin_bank_transactions
                WHERE bank_account_id = ? AND is_active = 1 AND transaction_date < ?
            """, (bank_account_id, start_date))
            opening_balance = cursor.fetchone()['total']

            # Get transactions in period
            cursor.execute("""
                SELECT * FROM genfin_bank_transactions
                WHERE bank_account_id = ? AND is_active = 1
                AND transaction_date >= ? AND transaction_date <= ?
                ORDER BY transaction_date, created_at
            """, (bank_account_id, start_date, end_date))

            entries = []
            running_balance = opening_balance

            for trans in cursor.fetchall():
                running_balance += trans['amount']

                entry = {
                    "date": trans['transaction_date'],
                    "type": trans['transaction_type'],
                    "reference": trans['reference_number'] or '',
                    "payee": trans['payee'] or '',
                    "memo": trans['memo'] or '',
                    "payment": abs(trans['amount']) if trans['amount'] < 0 else 0,
                    "deposit": trans['amount'] if trans['amount'] > 0 else 0,
                    "balance": round(running_balance, 2),
                    "reconciled": bool(trans['is_reconciled'])
                }

                # Add check details if applicable
                if trans['check_id']:
                    cursor.execute(
                        "SELECT check_number, status FROM genfin_checks WHERE check_id = ?",
                        (trans['check_id'],)
                    )
                    check = cursor.fetchone()
                    if check:
                        entry["check_number"] = check['check_number']
                        entry["check_status"] = check['status']

                entries.append(entry)

        return {
            "account_name": account['account_name'],
            "bank_name": account['bank_name'],
            "period_start": start_date,
            "period_end": end_date,
            "opening_balance": round(opening_balance, 2),
            "entries": entries,
            "closing_balance": round(running_balance, 2),
            "total_deposits": sum(e["deposit"] for e in entries),
            "total_payments": sum(e["payment"] for e in entries)
        }

    def _get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Get transaction by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bank_transactions WHERE transaction_id = ? AND is_active = 1",
                (transaction_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_transaction(row)
        return None

    def _row_to_transaction(self, row: sqlite3.Row) -> Dict:
        """Convert transaction row to dictionary"""
        return {
            "transaction_id": row['transaction_id'],
            "bank_account_id": row['bank_account_id'],
            "transaction_date": row['transaction_date'],
            "transaction_type": row['transaction_type'],
            "amount": row['amount'],
            "payee": row['payee'] or '',
            "memo": row['memo'] or '',
            "reference_number": row['reference_number'] or '',
            "category_account_id": row['category_account_id'],
            "is_reconciled": bool(row['is_reconciled']),
            "reconciled_date": row['reconciled_date'],
            "check_id": row['check_id'],
            "created_at": row['created_at']
        }

    # ==================== SERVICE SUMMARY ====================

    def get_service_summary(self) -> Dict:
        """Get GenFin Banking service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM genfin_bank_accounts WHERE is_active = 1")
            total_accounts = cursor.fetchone()['count']

            cursor.execute("SELECT COALESCE(SUM(current_balance), 0) as total FROM genfin_bank_accounts WHERE is_active = 1")
            total_balance = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_checks WHERE is_active = 1")
            total_checks = cursor.fetchone()['count']

            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
                FROM genfin_checks WHERE is_active = 1 AND status IN ('outstanding', 'printed')
            """)
            outstanding = cursor.fetchone()
            outstanding_count = outstanding['count']
            outstanding_amount = outstanding['total']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_ach_batches WHERE is_active = 1")
            ach_batches = cursor.fetchone()['count']

        return {
            "service": "GenFin Banking",
            "version": "2.0.0",
            "storage": "SQLite",
            "features": [
                "Bank Account Management",
                "Check Printing (Multiple Formats)",
                "ACH/Direct Deposit (NACHA)",
                "Bank Reconciliation",
                "Transaction Tracking",
                "Fund Transfers"
            ],
            "total_bank_accounts": total_accounts,
            "active_accounts": total_accounts,
            "total_balance": round(total_balance, 2),
            "total_checks": total_checks,
            "outstanding_checks": outstanding_count,
            "outstanding_checks_amount": round(outstanding_amount, 2),
            "ach_batches": ach_batches,
            "check_formats_supported": [f.value for f in CheckFormat]
        }


# Singleton instance
genfin_banking_service = GenFinBankingService()
