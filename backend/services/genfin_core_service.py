"""
GenFin Core Service - Chart of Accounts, General Ledger, Journal Entries
Complete double-entry accounting system for farm financial management
SQLite persistent storage implementation
"""

from datetime import datetime, date, timezone
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid
import sqlite3


class AccountType(Enum):
    """Standard accounting account types"""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class AccountSubType(Enum):
    """Detailed account subtypes for categorization"""
    # Assets
    CASH = "cash"
    BANK = "bank"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"
    PREPAID_EXPENSE = "prepaid_expense"
    FIXED_ASSET = "fixed_asset"
    ACCUMULATED_DEPRECIATION = "accumulated_depreciation"
    OTHER_ASSET = "other_asset"

    # Liabilities
    ACCOUNTS_PAYABLE = "accounts_payable"
    CREDIT_CARD = "credit_card"
    SHORT_TERM_LOAN = "short_term_loan"
    LONG_TERM_LOAN = "long_term_loan"
    PAYROLL_LIABILITY = "payroll_liability"
    SALES_TAX_PAYABLE = "sales_tax_payable"
    OTHER_LIABILITY = "other_liability"

    # Equity
    OWNER_EQUITY = "owner_equity"
    RETAINED_EARNINGS = "retained_earnings"
    OWNER_DRAW = "owner_draw"
    COMMON_STOCK = "common_stock"

    # Revenue
    SALES = "sales"
    SERVICE_REVENUE = "service_revenue"
    OTHER_INCOME = "other_income"
    INTEREST_INCOME = "interest_income"

    # Expenses
    COST_OF_GOODS = "cost_of_goods"
    OPERATING_EXPENSE = "operating_expense"
    PAYROLL_EXPENSE = "payroll_expense"
    RENT_EXPENSE = "rent_expense"
    UTILITIES = "utilities"
    DEPRECIATION = "depreciation"
    INTEREST_EXPENSE = "interest_expense"
    TAX_EXPENSE = "tax_expense"
    OTHER_EXPENSE = "other_expense"


class TransactionStatus(Enum):
    """Status of journal entries"""
    DRAFT = "draft"
    POSTED = "posted"
    VOIDED = "voided"
    RECONCILED = "reconciled"


@dataclass
class Account:
    """Chart of Accounts entry"""
    account_id: str
    account_number: str
    name: str
    account_type: AccountType
    sub_type: AccountSubType
    description: str = ""
    parent_account_id: Optional[str] = None
    is_active: bool = True
    is_system: bool = False  # System accounts can't be deleted
    tax_line: Optional[str] = None  # For tax reporting
    opening_balance: float = 0.0
    opening_balance_date: Optional[date] = None
    currency: str = "USD"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class JournalEntryLine:
    """Single line in a journal entry"""
    line_id: str
    account_id: str
    description: str
    debit: float = 0.0
    credit: float = 0.0
    tax_code: Optional[str] = None
    billable: bool = False
    customer_id: Optional[str] = None
    vendor_id: Optional[str] = None
    class_id: Optional[str] = None  # For class tracking
    location_id: Optional[str] = None  # For location tracking


@dataclass
class JournalEntry:
    """Double-entry journal entry"""
    entry_id: str
    entry_number: int
    entry_date: date
    lines: List[JournalEntryLine]
    memo: str = ""
    status: TransactionStatus = TransactionStatus.DRAFT
    source_type: str = "manual"  # manual, invoice, bill, payroll, etc.
    source_id: Optional[str] = None
    adjusting_entry: bool = False
    reversing_entry: bool = False
    reversed_entry_id: Optional[str] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    posted_at: Optional[datetime] = None


@dataclass
class FiscalPeriod:
    """Fiscal period definition"""
    period_id: str
    name: str
    start_date: date
    end_date: date
    fiscal_year: int
    period_number: int
    is_closed: bool = False
    is_adjustment_period: bool = False
    closed_at: Optional[datetime] = None
    closed_by: Optional[str] = None


@dataclass
class ClassTracking:
    """Class for departmental/project tracking"""
    class_id: str
    name: str
    parent_class_id: Optional[str] = None
    is_active: bool = True


@dataclass
class Location:
    """Location for multi-location tracking"""
    location_id: str
    name: str
    address: str = ""
    is_active: bool = True


# Default Chart of Accounts for Farm Operations
FARM_CHART_OF_ACCOUNTS = [
    # Assets
    {"number": "1000", "name": "Petty Cash", "type": AccountType.ASSET, "sub_type": AccountSubType.CASH},
    {"number": "1010", "name": "Operating Checking", "type": AccountType.ASSET, "sub_type": AccountSubType.BANK},
    {"number": "1020", "name": "Savings Account", "type": AccountType.ASSET, "sub_type": AccountSubType.BANK},
    {"number": "1100", "name": "Accounts Receivable", "type": AccountType.ASSET, "sub_type": AccountSubType.ACCOUNTS_RECEIVABLE},
    {"number": "1200", "name": "Crop Inventory", "type": AccountType.ASSET, "sub_type": AccountSubType.INVENTORY},
    {"number": "1210", "name": "Livestock Inventory", "type": AccountType.ASSET, "sub_type": AccountSubType.INVENTORY},
    {"number": "1220", "name": "Feed & Supply Inventory", "type": AccountType.ASSET, "sub_type": AccountSubType.INVENTORY},
    {"number": "1300", "name": "Prepaid Insurance", "type": AccountType.ASSET, "sub_type": AccountSubType.PREPAID_EXPENSE},
    {"number": "1310", "name": "Prepaid Rent", "type": AccountType.ASSET, "sub_type": AccountSubType.PREPAID_EXPENSE},
    {"number": "1500", "name": "Land", "type": AccountType.ASSET, "sub_type": AccountSubType.FIXED_ASSET},
    {"number": "1510", "name": "Buildings & Improvements", "type": AccountType.ASSET, "sub_type": AccountSubType.FIXED_ASSET},
    {"number": "1520", "name": "Farm Equipment", "type": AccountType.ASSET, "sub_type": AccountSubType.FIXED_ASSET},
    {"number": "1530", "name": "Vehicles", "type": AccountType.ASSET, "sub_type": AccountSubType.FIXED_ASSET},
    {"number": "1540", "name": "Irrigation Systems", "type": AccountType.ASSET, "sub_type": AccountSubType.FIXED_ASSET},
    {"number": "1550", "name": "Breeding Livestock", "type": AccountType.ASSET, "sub_type": AccountSubType.FIXED_ASSET},
    {"number": "1600", "name": "Accumulated Depreciation - Buildings", "type": AccountType.ASSET, "sub_type": AccountSubType.ACCUMULATED_DEPRECIATION},
    {"number": "1610", "name": "Accumulated Depreciation - Equipment", "type": AccountType.ASSET, "sub_type": AccountSubType.ACCUMULATED_DEPRECIATION},
    {"number": "1620", "name": "Accumulated Depreciation - Vehicles", "type": AccountType.ASSET, "sub_type": AccountSubType.ACCUMULATED_DEPRECIATION},

    # Liabilities
    {"number": "2000", "name": "Accounts Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.ACCOUNTS_PAYABLE},
    {"number": "2100", "name": "Credit Card - Business", "type": AccountType.LIABILITY, "sub_type": AccountSubType.CREDIT_CARD},
    {"number": "2200", "name": "Operating Line of Credit", "type": AccountType.LIABILITY, "sub_type": AccountSubType.SHORT_TERM_LOAN},
    {"number": "2300", "name": "Current Portion - Long Term Debt", "type": AccountType.LIABILITY, "sub_type": AccountSubType.SHORT_TERM_LOAN},
    {"number": "2400", "name": "Payroll Liabilities", "type": AccountType.LIABILITY, "sub_type": AccountSubType.PAYROLL_LIABILITY},
    {"number": "2410", "name": "Federal Withholding Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.PAYROLL_LIABILITY},
    {"number": "2420", "name": "State Withholding Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.PAYROLL_LIABILITY},
    {"number": "2430", "name": "FICA Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.PAYROLL_LIABILITY},
    {"number": "2440", "name": "FUTA Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.PAYROLL_LIABILITY},
    {"number": "2450", "name": "SUTA Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.PAYROLL_LIABILITY},
    {"number": "2500", "name": "Sales Tax Payable", "type": AccountType.LIABILITY, "sub_type": AccountSubType.SALES_TAX_PAYABLE},
    {"number": "2600", "name": "Equipment Loans", "type": AccountType.LIABILITY, "sub_type": AccountSubType.LONG_TERM_LOAN},
    {"number": "2610", "name": "Real Estate Mortgage", "type": AccountType.LIABILITY, "sub_type": AccountSubType.LONG_TERM_LOAN},
    {"number": "2620", "name": "FSA Operating Loan", "type": AccountType.LIABILITY, "sub_type": AccountSubType.LONG_TERM_LOAN},

    # Equity
    {"number": "3000", "name": "Owner's Equity", "type": AccountType.EQUITY, "sub_type": AccountSubType.OWNER_EQUITY},
    {"number": "3100", "name": "Owner's Contributions", "type": AccountType.EQUITY, "sub_type": AccountSubType.OWNER_EQUITY},
    {"number": "3200", "name": "Owner's Draws", "type": AccountType.EQUITY, "sub_type": AccountSubType.OWNER_DRAW},
    {"number": "3300", "name": "Retained Earnings", "type": AccountType.EQUITY, "sub_type": AccountSubType.RETAINED_EARNINGS},

    # Revenue
    {"number": "4000", "name": "Crop Sales - Corn", "type": AccountType.REVENUE, "sub_type": AccountSubType.SALES},
    {"number": "4010", "name": "Crop Sales - Soybeans", "type": AccountType.REVENUE, "sub_type": AccountSubType.SALES},
    {"number": "4020", "name": "Crop Sales - Wheat", "type": AccountType.REVENUE, "sub_type": AccountSubType.SALES},
    {"number": "4030", "name": "Crop Sales - Other", "type": AccountType.REVENUE, "sub_type": AccountSubType.SALES},
    {"number": "4100", "name": "Livestock Sales", "type": AccountType.REVENUE, "sub_type": AccountSubType.SALES},
    {"number": "4200", "name": "Custom Work Income", "type": AccountType.REVENUE, "sub_type": AccountSubType.SERVICE_REVENUE},
    {"number": "4300", "name": "Government Payments", "type": AccountType.REVENUE, "sub_type": AccountSubType.OTHER_INCOME},
    {"number": "4310", "name": "Crop Insurance Proceeds", "type": AccountType.REVENUE, "sub_type": AccountSubType.OTHER_INCOME},
    {"number": "4320", "name": "Conservation Program Income", "type": AccountType.REVENUE, "sub_type": AccountSubType.OTHER_INCOME},
    {"number": "4400", "name": "Cash Rent Income", "type": AccountType.REVENUE, "sub_type": AccountSubType.OTHER_INCOME},
    {"number": "4500", "name": "Interest Income", "type": AccountType.REVENUE, "sub_type": AccountSubType.INTEREST_INCOME},
    {"number": "4600", "name": "Gain on Sale of Assets", "type": AccountType.REVENUE, "sub_type": AccountSubType.OTHER_INCOME},

    # Cost of Goods Sold
    {"number": "5000", "name": "Seed Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5010", "name": "Fertilizer Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5020", "name": "Chemical Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5030", "name": "Crop Insurance Premium", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5040", "name": "Drying & Storage", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5050", "name": "Hauling & Trucking", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5100", "name": "Feed Purchased", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5110", "name": "Veterinary & Medicine", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},
    {"number": "5120", "name": "Livestock Supplies", "type": AccountType.EXPENSE, "sub_type": AccountSubType.COST_OF_GOODS},

    # Operating Expenses
    {"number": "6000", "name": "Wages & Salaries", "type": AccountType.EXPENSE, "sub_type": AccountSubType.PAYROLL_EXPENSE},
    {"number": "6010", "name": "Payroll Taxes", "type": AccountType.EXPENSE, "sub_type": AccountSubType.PAYROLL_EXPENSE},
    {"number": "6020", "name": "Employee Benefits", "type": AccountType.EXPENSE, "sub_type": AccountSubType.PAYROLL_EXPENSE},
    {"number": "6030", "name": "Contract Labor", "type": AccountType.EXPENSE, "sub_type": AccountSubType.PAYROLL_EXPENSE},
    {"number": "6100", "name": "Cash Rent Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.RENT_EXPENSE},
    {"number": "6110", "name": "Equipment Rent/Lease", "type": AccountType.EXPENSE, "sub_type": AccountSubType.RENT_EXPENSE},
    {"number": "6200", "name": "Fuel & Oil", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6210", "name": "Repairs & Maintenance", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6220", "name": "Supplies", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6300", "name": "Utilities - Electric", "type": AccountType.EXPENSE, "sub_type": AccountSubType.UTILITIES},
    {"number": "6310", "name": "Utilities - Gas/Propane", "type": AccountType.EXPENSE, "sub_type": AccountSubType.UTILITIES},
    {"number": "6320", "name": "Utilities - Water", "type": AccountType.EXPENSE, "sub_type": AccountSubType.UTILITIES},
    {"number": "6330", "name": "Utilities - Phone/Internet", "type": AccountType.EXPENSE, "sub_type": AccountSubType.UTILITIES},
    {"number": "6400", "name": "Insurance - Property", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6410", "name": "Insurance - Liability", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6420", "name": "Insurance - Vehicle", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6500", "name": "Property Taxes", "type": AccountType.EXPENSE, "sub_type": AccountSubType.TAX_EXPENSE},
    {"number": "6510", "name": "License & Permits", "type": AccountType.EXPENSE, "sub_type": AccountSubType.TAX_EXPENSE},
    {"number": "6600", "name": "Professional Fees", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6610", "name": "Accounting & Legal", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6620", "name": "Consulting Fees", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OPERATING_EXPENSE},
    {"number": "6700", "name": "Depreciation Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.DEPRECIATION},
    {"number": "6800", "name": "Interest Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.INTEREST_EXPENSE},
    {"number": "6900", "name": "Miscellaneous Expense", "type": AccountType.EXPENSE, "sub_type": AccountSubType.OTHER_EXPENSE},
]


class GenFinCoreService:
    """
    GenFin Core Accounting Service

    Provides complete double-entry accounting functionality:
    - Chart of Accounts management
    - General Ledger
    - Journal Entries
    - Fiscal Period management
    - Account balances and trial balance
    - Class and Location tracking

    Uses SQLite for persistent storage.
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
        self.company_name = "GenFin"
        self.fiscal_year_start_month = 1  # January

        # Initialize database tables
        self._init_tables()

        # Initialize with farm chart of accounts if empty
        self._initialize_chart_of_accounts()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create database tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_accounts (
                    account_id TEXT PRIMARY KEY,
                    account_number TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    sub_type TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    parent_account_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_system INTEGER DEFAULT 0,
                    tax_line TEXT,
                    opening_balance REAL DEFAULT 0.0,
                    opening_balance_date TEXT,
                    currency TEXT DEFAULT 'USD',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Journal entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_journal_entries (
                    entry_id TEXT PRIMARY KEY,
                    entry_number INTEGER NOT NULL,
                    entry_date TEXT NOT NULL,
                    memo TEXT DEFAULT '',
                    status TEXT DEFAULT 'draft',
                    source_type TEXT DEFAULT 'manual',
                    source_id TEXT,
                    adjusting_entry INTEGER DEFAULT 0,
                    reversing_entry INTEGER DEFAULT 0,
                    reversed_entry_id TEXT,
                    created_by TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    posted_at TEXT
                )
            """)

            # Journal entry lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_journal_entry_lines (
                    line_id TEXT PRIMARY KEY,
                    entry_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    debit REAL DEFAULT 0.0,
                    credit REAL DEFAULT 0.0,
                    tax_code TEXT,
                    billable INTEGER DEFAULT 0,
                    customer_id TEXT,
                    vendor_id TEXT,
                    class_id TEXT,
                    location_id TEXT,
                    FOREIGN KEY (entry_id) REFERENCES genfin_journal_entries(entry_id),
                    FOREIGN KEY (account_id) REFERENCES genfin_accounts(account_id)
                )
            """)

            # Fiscal periods table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_fiscal_periods (
                    period_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    period_number INTEGER NOT NULL,
                    is_closed INTEGER DEFAULT 0,
                    is_adjustment_period INTEGER DEFAULT 0,
                    closed_at TEXT,
                    closed_by TEXT
                )
            """)

            # Classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_classes (
                    class_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_class_id TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Locations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_locations (
                    location_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Settings table (for next_entry_number, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_core_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Initialize next_entry_number if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO genfin_core_settings (key, value) VALUES ('next_entry_number', '1')
            """)

            # Create indices for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_number ON genfin_accounts(account_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_type ON genfin_accounts(account_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_date ON genfin_journal_entries(entry_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_status ON genfin_journal_entries(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entry_lines_entry ON genfin_journal_entry_lines(entry_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entry_lines_account ON genfin_journal_entry_lines(account_id)")

            conn.commit()

    def _get_next_entry_number(self) -> int:
        """Get and increment the next entry number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM genfin_core_settings WHERE key = 'next_entry_number'")
            row = cursor.fetchone()
            current = int(row['value']) if row else 1
            cursor.execute(
                "UPDATE genfin_core_settings SET value = ? WHERE key = 'next_entry_number'",
                (str(current + 1),)
            )
            conn.commit()
            return current

    def _initialize_chart_of_accounts(self):
        """Set up default farm chart of accounts if none exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM genfin_accounts")
            count = cursor.fetchone()['count']

            if count > 0:
                return  # Already initialized

            now = datetime.now(timezone.utc).isoformat()
            for acct in FARM_CHART_OF_ACCOUNTS:
                account_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_accounts
                    (account_id, account_number, name, account_type, sub_type, is_system, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """, (
                    account_id,
                    acct["number"],
                    acct["name"],
                    acct["type"].value,
                    acct["sub_type"].value,
                    now,
                    now
                ))

            conn.commit()

    # ==================== CHART OF ACCOUNTS ====================

    def create_account(
        self,
        account_number: str,
        name: str,
        account_type: str,
        sub_type: str,
        description: str = "",
        parent_account_id: Optional[str] = None,
        tax_line: Optional[str] = None,
        opening_balance: float = 0.0,
        opening_balance_date: Optional[str] = None
    ) -> Dict:
        """Create a new account in the chart of accounts"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check for duplicate account number
            cursor.execute("SELECT account_id FROM genfin_accounts WHERE account_number = ?", (account_number,))
            if cursor.fetchone():
                return {"success": False, "error": f"Account number {account_number} already exists"}

            account_id = str(uuid.uuid4())

            try:
                # Normalize to lowercase for case-insensitive matching
                acct_type = AccountType(account_type.lower())
                # Auto-determine sub_type if not provided or empty
                sub_type_normalized = sub_type.lower() if sub_type else ""
                if not sub_type_normalized:
                    # Default sub-types based on account type
                    default_sub_types = {
                        "asset": "other_asset",
                        "liability": "other_liability",
                        "equity": "owner_equity",
                        "revenue": "other_income",
                        "expense": "other_expense"
                    }
                    sub_type_normalized = default_sub_types.get(account_type.lower(), "other_expense")
                acct_sub_type = AccountSubType(sub_type_normalized)
            except ValueError as e:
                return {"success": False, "error": f"Invalid account type: {str(e)}"}

            now = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO genfin_accounts
                (account_id, account_number, name, account_type, sub_type, description,
                 parent_account_id, tax_line, opening_balance, opening_balance_date,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account_id, account_number, name, acct_type.value, acct_sub_type.value,
                description, parent_account_id, tax_line, opening_balance, opening_balance_date,
                now, now
            ))

            conn.commit()

            # Create opening balance journal entry if needed
            if opening_balance != 0 and opening_balance_date:
                self._create_opening_balance_entry_db(account_id, name, acct_type, opening_balance, opening_balance_date)

            return {
                "success": True,
                "account_id": account_id,
                "account": self.get_account(account_id)
            }

    def _create_opening_balance_entry_db(self, account_id: str, account_name: str, account_type: AccountType, balance: float, entry_date: str):
        """Create journal entry for opening balance"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Find or create Opening Balance Equity account
            cursor.execute("SELECT account_id FROM genfin_accounts WHERE name = 'Opening Balance Equity'")
            obe_row = cursor.fetchone()

            if not obe_row:
                obe_id = str(uuid.uuid4())
                now = datetime.now(timezone.utc).isoformat()
                cursor.execute("""
                    INSERT INTO genfin_accounts
                    (account_id, account_number, name, account_type, sub_type, is_system, created_at, updated_at)
                    VALUES (?, '3900', 'Opening Balance Equity', 'equity', 'owner_equity', 1, ?, ?)
                """, (obe_id, now, now))
            else:
                obe_id = obe_row['account_id']

            # Create journal entry
            entry_id = str(uuid.uuid4())
            entry_number = self._get_next_entry_number()
            now = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO genfin_journal_entries
                (entry_id, entry_number, entry_date, memo, status, source_type, created_at, posted_at)
                VALUES (?, ?, ?, ?, 'posted', 'opening_balance', ?, ?)
            """, (entry_id, entry_number, entry_date, f"Opening balance for {account_name}", now, now))

            # Create lines
            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                # Debit the account, credit OBE
                cursor.execute("""
                    INSERT INTO genfin_journal_entry_lines
                    (line_id, entry_id, account_id, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (str(uuid.uuid4()), entry_id, account_id, f"Opening balance - {account_name}", abs(balance)))
                cursor.execute("""
                    INSERT INTO genfin_journal_entry_lines
                    (line_id, entry_id, account_id, description, debit, credit)
                    VALUES (?, ?, ?, ?, 0, ?)
                """, (str(uuid.uuid4()), entry_id, obe_id, f"Opening balance - {account_name}", abs(balance)))
            else:
                # Credit the account, debit OBE
                cursor.execute("""
                    INSERT INTO genfin_journal_entry_lines
                    (line_id, entry_id, account_id, description, debit, credit)
                    VALUES (?, ?, ?, ?, 0, ?)
                """, (str(uuid.uuid4()), entry_id, account_id, f"Opening balance - {account_name}", abs(balance)))
                cursor.execute("""
                    INSERT INTO genfin_journal_entry_lines
                    (line_id, entry_id, account_id, description, debit, credit)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (str(uuid.uuid4()), entry_id, obe_id, f"Opening balance - {account_name}", abs(balance)))

            conn.commit()

    def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        tax_line: Optional[str] = None
    ) -> Dict:
        """Update an existing account"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_accounts WHERE account_id = ?", (account_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Account not found"}

            updates = []
            params = []

            if name:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            if tax_line is not None:
                updates.append("tax_line = ?")
                params.append(tax_line)

            updates.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(account_id)

            cursor.execute(f"""
                UPDATE genfin_accounts SET {', '.join(updates)} WHERE account_id = ?
            """, params)

            conn.commit()

            return {
                "success": True,
                "account": self.get_account(account_id)
            }

    def delete_account(self, account_id: str) -> Dict:
        """Delete an account (only if no transactions)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT is_system FROM genfin_accounts WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()

            if not row:
                return {"success": False, "error": "Account not found"}

            if row['is_system']:
                return {"success": False, "error": "Cannot delete system account"}

            # Check for transactions
            cursor.execute("""
                SELECT COUNT(*) as count FROM genfin_journal_entry_lines WHERE account_id = ?
            """, (account_id,))
            if cursor.fetchone()['count'] > 0:
                return {"success": False, "error": "Cannot delete account with transactions"}

            cursor.execute("DELETE FROM genfin_accounts WHERE account_id = ?", (account_id,))
            conn.commit()

            return {"success": True, "message": "Account deleted"}

    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get a single account"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_accounts WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_account_dict(row)

    def get_account_by_number(self, account_number: str) -> Optional[Dict]:
        """Get account by account number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_accounts WHERE account_number = ?", (account_number,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_account_dict(row)

    def list_accounts(
        self,
        account_type: Optional[str] = None,
        active_only: bool = True,
        include_balances: bool = False
    ) -> List[Dict]:
        """List all accounts with optional filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_accounts WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = 1"
            if account_type:
                query += " AND account_type = ?"
                params.append(account_type)

            query += " ORDER BY account_number"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                acct_dict = self._row_to_account_dict(row)
                if include_balances:
                    acct_dict["balance"] = self.get_account_balance(row['account_id'])
                result.append(acct_dict)

            return result

    def get_chart_of_accounts(self) -> Dict:
        """Get complete chart of accounts organized by type"""
        coa = {
            "assets": [],
            "liabilities": [],
            "equity": [],
            "revenue": [],
            "expenses": []
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_accounts WHERE is_active = 1 ORDER BY account_number
            """)
            rows = cursor.fetchall()

            for row in rows:
                acct_dict = self._row_to_account_dict(row)
                acct_dict["balance"] = self.get_account_balance(row['account_id'])

                if row['account_type'] == 'asset':
                    coa["assets"].append(acct_dict)
                elif row['account_type'] == 'liability':
                    coa["liabilities"].append(acct_dict)
                elif row['account_type'] == 'equity':
                    coa["equity"].append(acct_dict)
                elif row['account_type'] == 'revenue':
                    coa["revenue"].append(acct_dict)
                elif row['account_type'] == 'expense':
                    coa["expenses"].append(acct_dict)

        return coa

    # ==================== JOURNAL ENTRIES ====================

    def create_journal_entry(
        self,
        entry_date: str,
        lines: List[Dict],
        memo: str = "",
        source_type: str = "manual",
        source_id: Optional[str] = None,
        adjusting_entry: bool = False,
        auto_post: bool = False
    ) -> Dict:
        """Create a new journal entry"""
        # Validate lines
        if len(lines) < 2:
            return {"success": False, "error": "Journal entry must have at least 2 lines"}

        total_debits = sum(line.get("debit", 0) for line in lines)
        total_credits = sum(line.get("credit", 0) for line in lines)

        if abs(total_debits - total_credits) > 0.01:
            return {
                "success": False,
                "error": f"Entry does not balance. Debits: {total_debits}, Credits: {total_credits}"
            }

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Validate accounts exist
            for line in lines:
                cursor.execute("SELECT account_id FROM genfin_accounts WHERE account_id = ?", (line["account_id"],))
                if not cursor.fetchone():
                    return {"success": False, "error": f"Account {line['account_id']} not found"}

            entry_id = str(uuid.uuid4())
            entry_number = self._get_next_entry_number()
            now = datetime.now(timezone.utc).isoformat()
            status = "posted" if auto_post else "draft"
            posted_at = now if auto_post else None

            cursor.execute("""
                INSERT INTO genfin_journal_entries
                (entry_id, entry_number, entry_date, memo, status, source_type, source_id,
                 adjusting_entry, created_at, posted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, entry_number, entry_date, memo, status, source_type, source_id,
                  1 if adjusting_entry else 0, now, posted_at))

            for line in lines:
                cursor.execute("""
                    INSERT INTO genfin_journal_entry_lines
                    (line_id, entry_id, account_id, description, debit, credit, tax_code,
                     billable, customer_id, vendor_id, class_id, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    entry_id,
                    line["account_id"],
                    line.get("description", ""),
                    line.get("debit", 0),
                    line.get("credit", 0),
                    line.get("tax_code"),
                    1 if line.get("billable", False) else 0,
                    line.get("customer_id"),
                    line.get("vendor_id"),
                    line.get("class_id"),
                    line.get("location_id")
                ))

            conn.commit()

        return {
            "success": True,
            "entry_id": entry_id,
            "entry_number": entry_number,
            "entry": self.get_journal_entry(entry_id)
        }

    def post_journal_entry(self, entry_id: str) -> Dict:
        """Post a draft journal entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT status FROM genfin_journal_entries WHERE entry_id = ?", (entry_id,))
            row = cursor.fetchone()

            if not row:
                return {"success": False, "error": "Journal entry not found"}

            if row['status'] != 'draft':
                return {"success": False, "error": f"Entry is already {row['status']}"}

            cursor.execute("""
                UPDATE genfin_journal_entries
                SET status = 'posted', posted_at = ?
                WHERE entry_id = ?
            """, (datetime.now(timezone.utc).isoformat(), entry_id))

            conn.commit()

        return {
            "success": True,
            "entry": self.get_journal_entry(entry_id)
        }

    def void_journal_entry(self, entry_id: str, reason: str = "") -> Dict:
        """Void a posted journal entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT status, memo FROM genfin_journal_entries WHERE entry_id = ?", (entry_id,))
            row = cursor.fetchone()

            if not row:
                return {"success": False, "error": "Journal entry not found"}

            if row['status'] == 'voided':
                return {"success": False, "error": "Entry is already voided"}

            if row['status'] == 'reconciled':
                return {"success": False, "error": "Cannot void reconciled entry"}

            new_memo = f"{row['memo']} [VOIDED: {reason}]"
            cursor.execute("""
                UPDATE genfin_journal_entries
                SET status = 'voided', memo = ?
                WHERE entry_id = ?
            """, (new_memo, entry_id))

            conn.commit()

        return {
            "success": True,
            "entry": self.get_journal_entry(entry_id)
        }

    def reverse_journal_entry(self, entry_id: str, reversal_date: str) -> Dict:
        """Create a reversing entry for a posted journal entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_journal_entries WHERE entry_id = ?", (entry_id,))
            original = cursor.fetchone()

            if not original:
                return {"success": False, "error": "Journal entry not found"}

            if original['status'] != 'posted':
                return {"success": False, "error": "Can only reverse posted entries"}

            # Get original lines
            cursor.execute("SELECT * FROM genfin_journal_entry_lines WHERE entry_id = ?", (entry_id,))
            original_lines = cursor.fetchall()

        # Create reversed lines
        reversed_lines = []
        for line in original_lines:
            reversed_lines.append({
                "account_id": line['account_id'],
                "description": f"Reversal: {line['description']}",
                "debit": line['credit'],  # Swap debit and credit
                "credit": line['debit'],
                "class_id": line['class_id'],
                "location_id": line['location_id']
            })

        result = self.create_journal_entry(
            entry_date=reversal_date,
            lines=reversed_lines,
            memo=f"Reversal of entry #{original['entry_number']}",
            source_type="reversal",
            source_id=entry_id,
            auto_post=True
        )

        if result["success"]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE genfin_journal_entries SET reversing_entry = 1 WHERE entry_id = ?
                """, (entry_id,))
                conn.commit()
            result["original_entry_id"] = entry_id

        return result

    def get_journal_entry(self, entry_id: str) -> Optional[Dict]:
        """Get a single journal entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_journal_entries WHERE entry_id = ?", (entry_id,))
            entry_row = cursor.fetchone()

            if not entry_row:
                return None

            cursor.execute("SELECT * FROM genfin_journal_entry_lines WHERE entry_id = ?", (entry_id,))
            line_rows = cursor.fetchall()

            return self._rows_to_entry_dict(entry_row, line_rows)

    def list_journal_entries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        account_id: Optional[str] = None
    ) -> List[Dict]:
        """List journal entries with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_journal_entries WHERE 1=1"
            params = []

            if start_date:
                query += " AND entry_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND entry_date <= ?"
                params.append(end_date)
            if status:
                query += " AND status = ?"
                params.append(status)
            if source_type:
                query += " AND source_type = ?"
                params.append(source_type)

            query += " ORDER BY entry_date, entry_number"

            cursor.execute(query, params)
            entry_rows = cursor.fetchall()

            result = []
            for entry_row in entry_rows:
                cursor.execute("SELECT * FROM genfin_journal_entry_lines WHERE entry_id = ?", (entry_row['entry_id'],))
                line_rows = cursor.fetchall()

                # Filter by account_id if specified
                if account_id:
                    has_account = any(line['account_id'] == account_id for line in line_rows)
                    if not has_account:
                        continue

                result.append(self._rows_to_entry_dict(entry_row, line_rows))

            return result

    # ==================== GENERAL LEDGER ====================

    def get_account_balance(
        self,
        account_id: str,
        as_of_date: Optional[str] = None
    ) -> float:
        """Calculate account balance as of a date"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_accounts WHERE account_id = ?", (account_id,))
            account_row = cursor.fetchone()

            if not account_row:
                return 0.0

            balance = account_row['opening_balance'] or 0.0
            account_type = account_row['account_type']

            query = """
                SELECT l.debit, l.credit FROM genfin_journal_entry_lines l
                JOIN genfin_journal_entries e ON l.entry_id = e.entry_id
                WHERE l.account_id = ? AND e.status IN ('posted', 'reconciled')
            """
            params = [account_id]

            if as_of_date:
                query += " AND e.entry_date <= ?"
                params.append(as_of_date)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                # Assets and Expenses increase with debits
                if account_type in ['asset', 'expense']:
                    balance += row['debit'] - row['credit']
                # Liabilities, Equity, Revenue increase with credits
                else:
                    balance += row['credit'] - row['debit']

        return round(balance, 2)

    def get_account_ledger(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get detailed ledger for an account"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_accounts WHERE account_id = ?", (account_id,))
            account_row = cursor.fetchone()

            if not account_row:
                return {"error": "Account not found"}

            account_type = account_row['account_type']

            # Calculate opening balance
            opening_balance = account_row['opening_balance'] or 0.0
            if start_date:
                query = """
                    SELECT l.debit, l.credit FROM genfin_journal_entry_lines l
                    JOIN genfin_journal_entries e ON l.entry_id = e.entry_id
                    WHERE l.account_id = ? AND e.status IN ('posted', 'reconciled')
                    AND e.entry_date < ?
                """
                cursor.execute(query, (account_id, start_date))
                for row in cursor.fetchall():
                    if account_type in ['asset', 'expense']:
                        opening_balance += row['debit'] - row['credit']
                    else:
                        opening_balance += row['credit'] - row['debit']

            # Get transactions
            query = """
                SELECT e.entry_id, e.entry_number, e.entry_date, e.source_type, e.memo,
                       l.description, l.debit, l.credit
                FROM genfin_journal_entry_lines l
                JOIN genfin_journal_entries e ON l.entry_id = e.entry_id
                WHERE l.account_id = ? AND e.status IN ('posted', 'reconciled')
            """
            params = [account_id]

            if start_date:
                query += " AND e.entry_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND e.entry_date <= ?"
                params.append(end_date)

            query += " ORDER BY e.entry_date, e.entry_number"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            transactions = []
            running_balance = opening_balance

            for row in rows:
                if account_type in ['asset', 'expense']:
                    running_balance += row['debit'] - row['credit']
                else:
                    running_balance += row['credit'] - row['debit']

                transactions.append({
                    "date": row['entry_date'],
                    "entry_number": row['entry_number'],
                    "entry_id": row['entry_id'],
                    "description": row['description'] or row['memo'],
                    "debit": row['debit'],
                    "credit": row['credit'],
                    "balance": round(running_balance, 2),
                    "source_type": row['source_type']
                })

        return {
            "account": self._row_to_account_dict(account_row),
            "opening_balance": round(opening_balance, 2),
            "transactions": transactions,
            "ending_balance": round(running_balance, 2),
            "total_debits": sum(t["debit"] for t in transactions),
            "total_credits": sum(t["credit"] for t in transactions)
        }

    def get_trial_balance(self, as_of_date: Optional[str] = None) -> Dict:
        """Generate trial balance report"""
        accounts = []
        total_debits = 0
        total_credits = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_accounts WHERE is_active = 1 ORDER BY account_number
            """)
            rows = cursor.fetchall()

            for account_row in rows:
                balance = self.get_account_balance(account_row['account_id'], as_of_date)

                if balance == 0:
                    continue

                account_type = account_row['account_type']

                # Normalize debit/credit columns
                if account_type in ['asset', 'expense']:
                    if balance >= 0:
                        debit = balance
                        credit = 0
                    else:
                        debit = 0
                        credit = abs(balance)
                else:
                    if balance >= 0:
                        debit = 0
                        credit = balance
                    else:
                        debit = abs(balance)
                        credit = 0

                total_debits += debit
                total_credits += credit

                accounts.append({
                    "account_number": account_row['account_number'],
                    "account_name": account_row['name'],
                    "account_type": account_type,
                    "debit": round(debit, 2),
                    "credit": round(credit, 2)
                })

        return {
            "as_of_date": as_of_date or date.today().isoformat(),
            "accounts": accounts,
            "total_debits": round(total_debits, 2),
            "total_credits": round(total_credits, 2),
            "balanced": abs(total_debits - total_credits) < 0.01
        }

    # ==================== FISCAL PERIODS ====================

    def create_fiscal_year(self, year: int) -> Dict:
        """Create fiscal periods for a year"""
        periods = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for month in range(1, 13):
                period_num = ((month - self.fiscal_year_start_month) % 12) + 1

                if month == 12:
                    end_day = 31
                elif month in [4, 6, 9, 11]:
                    end_day = 30
                elif month == 2:
                    end_day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
                else:
                    end_day = 31

                period_id = str(uuid.uuid4())
                start_date = date(year, month, 1).isoformat()
                end_date_val = date(year, month, end_day).isoformat()

                cursor.execute("""
                    INSERT INTO genfin_fiscal_periods
                    (period_id, name, start_date, end_date, fiscal_year, period_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (period_id, f"{year}-{month:02d}", start_date, end_date_val, year, period_num))

                periods.append({
                    "period_id": period_id,
                    "name": f"{year}-{month:02d}",
                    "start_date": start_date,
                    "end_date": end_date_val,
                    "period_number": period_num
                })

            conn.commit()

        return {
            "success": True,
            "fiscal_year": year,
            "periods": periods
        }

    def close_fiscal_period(self, period_id: str, closed_by: str) -> Dict:
        """Close a fiscal period"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_fiscal_periods WHERE period_id = ?", (period_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Period not found"}

            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE genfin_fiscal_periods
                SET is_closed = 1, closed_at = ?, closed_by = ?
                WHERE period_id = ?
            """, (now, closed_by, period_id))

            conn.commit()

            cursor.execute("SELECT * FROM genfin_fiscal_periods WHERE period_id = ?", (period_id,))
            period = cursor.fetchone()

        return {
            "success": True,
            "period": {
                "period_id": period['period_id'],
                "name": period['name'],
                "is_closed": bool(period['is_closed']),
                "closed_at": period['closed_at']
            }
        }

    def close_fiscal_year(self, year: int, retained_earnings_account_id: str) -> Dict:
        """Close fiscal year - transfer net income to retained earnings"""
        # Calculate net income
        total_revenue = 0
        total_expenses = 0

        _year_start = date(year, self.fiscal_year_start_month, 1)
        if self.fiscal_year_start_month == 1:
            year_end = date(year, 12, 31)
        else:
            year_end = date(year + 1, self.fiscal_year_start_month - 1, 28)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT account_id, account_type FROM genfin_accounts WHERE is_active = 1")
            accounts = cursor.fetchall()

            for account in accounts:
                if account['account_type'] == 'revenue':
                    total_revenue += self.get_account_balance(account['account_id'], year_end.isoformat())
                elif account['account_type'] == 'expense':
                    total_expenses += self.get_account_balance(account['account_id'], year_end.isoformat())

        net_income = total_revenue - total_expenses

        # Create closing entry
        closing_lines = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Close revenue accounts
            cursor.execute("SELECT account_id, name FROM genfin_accounts WHERE account_type = 'revenue' AND is_active = 1")
            for account in cursor.fetchall():
                balance = self.get_account_balance(account['account_id'], year_end.isoformat())
                if balance != 0:
                    closing_lines.append({
                        "account_id": account['account_id'],
                        "description": f"Close {account['name']}",
                        "debit": balance if balance > 0 else 0,
                        "credit": abs(balance) if balance < 0 else 0
                    })

            # Close expense accounts
            cursor.execute("SELECT account_id, name FROM genfin_accounts WHERE account_type = 'expense' AND is_active = 1")
            for account in cursor.fetchall():
                balance = self.get_account_balance(account['account_id'], year_end.isoformat())
                if balance != 0:
                    closing_lines.append({
                        "account_id": account['account_id'],
                        "description": f"Close {account['name']}",
                        "debit": 0 if balance > 0 else abs(balance),
                        "credit": balance if balance > 0 else 0
                    })

        # Transfer to retained earnings
        closing_lines.append({
            "account_id": retained_earnings_account_id,
            "description": f"Net income for {year}",
            "debit": 0 if net_income > 0 else abs(net_income),
            "credit": net_income if net_income > 0 else 0
        })

        result = self.create_journal_entry(
            entry_date=year_end.isoformat(),
            lines=closing_lines,
            memo=f"Year-end closing entry for {year}",
            source_type="year_end_close",
            adjusting_entry=True,
            auto_post=True
        )

        return {
            "success": True,
            "fiscal_year": year,
            "net_income": round(net_income, 2),
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "closing_entry": result
        }

    # ==================== CLASS & LOCATION TRACKING ====================

    def create_class(self, name: str, parent_class_id: Optional[str] = None) -> Dict:
        """Create a class for tracking"""
        class_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_classes (class_id, name, parent_class_id)
                VALUES (?, ?, ?)
            """, (class_id, name, parent_class_id))
            conn.commit()

        return {
            "success": True,
            "class_id": class_id,
            "name": name
        }

    def list_classes(self) -> List[Dict]:
        """List all classes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_classes")
            rows = cursor.fetchall()

            return [
                {
                    "class_id": row['class_id'],
                    "name": row['name'],
                    "parent_class_id": row['parent_class_id'],
                    "is_active": bool(row['is_active'])
                }
                for row in rows
            ]

    def create_location(self, name: str, address: str = "") -> Dict:
        """Create a location for tracking"""
        location_id = str(uuid.uuid4())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_locations (location_id, name, address)
                VALUES (?, ?, ?)
            """, (location_id, name, address))
            conn.commit()

        return {
            "success": True,
            "location_id": location_id,
            "name": name
        }

    def list_locations(self) -> List[Dict]:
        """List all locations"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_locations")
            rows = cursor.fetchall()

            return [
                {
                    "location_id": row['location_id'],
                    "name": row['name'],
                    "address": row['address'],
                    "is_active": bool(row['is_active'])
                }
                for row in rows
            ]

    # ==================== UTILITY METHODS ====================

    def _row_to_account_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite row to account dictionary"""
        return {
            "account_id": row['account_id'],
            "account_number": row['account_number'],
            "name": row['name'],
            "account_type": row['account_type'],
            "sub_type": row['sub_type'],
            "description": row['description'] or "",
            "parent_account_id": row['parent_account_id'],
            "is_active": bool(row['is_active']),
            "is_system": bool(row['is_system']),
            "tax_line": row['tax_line'],
            "opening_balance": row['opening_balance'] or 0.0,
            "opening_balance_date": row['opening_balance_date'],
            "currency": row['currency'] or "USD",
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    def _rows_to_entry_dict(self, entry_row: sqlite3.Row, line_rows: List[sqlite3.Row]) -> Dict:
        """Convert SQLite rows to journal entry dictionary"""
        lines = []
        for line in line_rows:
            account = self.get_account(line['account_id'])
            lines.append({
                "line_id": line['line_id'],
                "account_id": line['account_id'],
                "account_name": account['name'] if account else "Unknown",
                "account_number": account['account_number'] if account else "",
                "description": line['description'] or "",
                "debit": line['debit'] or 0,
                "credit": line['credit'] or 0,
                "tax_code": line['tax_code'],
                "billable": bool(line['billable']),
                "customer_id": line['customer_id'],
                "vendor_id": line['vendor_id'],
                "class_id": line['class_id'],
                "location_id": line['location_id']
            })

        return {
            "entry_id": entry_row['entry_id'],
            "entry_number": entry_row['entry_number'],
            "entry_date": entry_row['entry_date'],
            "lines": lines,
            "memo": entry_row['memo'] or "",
            "status": entry_row['status'],
            "source_type": entry_row['source_type'],
            "source_id": entry_row['source_id'],
            "adjusting_entry": bool(entry_row['adjusting_entry']),
            "reversing_entry": bool(entry_row['reversing_entry']),
            "reversed_entry_id": entry_row['reversed_entry_id'],
            "created_by": entry_row['created_by'] or "",
            "created_at": entry_row['created_at'],
            "posted_at": entry_row['posted_at'],
            "total_debits": sum(line['debit'] or 0 for line in line_rows),
            "total_credits": sum(line['credit'] or 0 for line in line_rows)
        }

    def get_system_summary(self) -> Dict:
        """Get GenFin system summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM genfin_accounts")
            total_accounts = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_accounts WHERE is_active = 1")
            active_accounts = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_journal_entries")
            total_entries = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_journal_entries WHERE status = 'posted'")
            posted_entries = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_classes")
            classes_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_locations")
            locations_count = cursor.fetchone()['count']

            cursor.execute("SELECT value FROM genfin_core_settings WHERE key = 'next_entry_number'")
            row = cursor.fetchone()
            next_entry_number = int(row['value']) if row else 1

        return {
            "system": "GenFin Core Accounting",
            "version": "1.0.0",
            "company_name": self.company_name,
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "total_journal_entries": total_entries,
            "posted_entries": posted_entries,
            "fiscal_year_start_month": self.fiscal_year_start_month,
            "next_entry_number": next_entry_number,
            "classes_count": classes_count,
            "locations_count": locations_count
        }


# Singleton instance
genfin_core_service = GenFinCoreService()
