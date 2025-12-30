"""
GenFin Core Service - Chart of Accounts, General Ledger, Journal Entries
Complete double-entry accounting system for farm financial management
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid


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
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.accounts: Dict[str, Account] = {}
        self.journal_entries: Dict[str, JournalEntry] = {}
        self.fiscal_periods: Dict[str, FiscalPeriod] = {}
        self.classes: Dict[str, ClassTracking] = {}
        self.locations: Dict[str, Location] = {}
        self.next_entry_number = 1
        self.company_name = "GenFin"
        self.fiscal_year_start_month = 1  # January

        # Initialize with farm chart of accounts
        self._initialize_chart_of_accounts()
        self._initialized = True

    def _initialize_chart_of_accounts(self):
        """Set up default farm chart of accounts"""
        for acct in FARM_CHART_OF_ACCOUNTS:
            account_id = str(uuid.uuid4())
            self.accounts[account_id] = Account(
                account_id=account_id,
                account_number=acct["number"],
                name=acct["name"],
                account_type=acct["type"],
                sub_type=acct["sub_type"],
                is_system=True
            )

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
        # Check for duplicate account number
        for acct in self.accounts.values():
            if acct.account_number == account_number:
                return {"success": False, "error": f"Account number {account_number} already exists"}

        account_id = str(uuid.uuid4())

        try:
            acct_type = AccountType(account_type)
            acct_sub_type = AccountSubType(sub_type)
        except ValueError as e:
            return {"success": False, "error": f"Invalid account type: {str(e)}"}

        ob_date = None
        if opening_balance_date:
            ob_date = datetime.strptime(opening_balance_date, "%Y-%m-%d").date()

        account = Account(
            account_id=account_id,
            account_number=account_number,
            name=name,
            account_type=acct_type,
            sub_type=acct_sub_type,
            description=description,
            parent_account_id=parent_account_id,
            tax_line=tax_line,
            opening_balance=opening_balance,
            opening_balance_date=ob_date
        )

        self.accounts[account_id] = account

        # Create opening balance journal entry if needed
        if opening_balance != 0 and ob_date:
            self._create_opening_balance_entry(account, opening_balance, ob_date)

        return {
            "success": True,
            "account_id": account_id,
            "account": self._account_to_dict(account)
        }

    def _create_opening_balance_entry(self, account: Account, balance: float, entry_date: date):
        """Create journal entry for opening balance"""
        # Find or create Opening Balance Equity account
        obe_account = None
        for acct in self.accounts.values():
            if acct.name == "Opening Balance Equity":
                obe_account = acct
                break

        if not obe_account:
            obe_id = str(uuid.uuid4())
            obe_account = Account(
                account_id=obe_id,
                account_number="3900",
                name="Opening Balance Equity",
                account_type=AccountType.EQUITY,
                sub_type=AccountSubType.OWNER_EQUITY,
                is_system=True
            )
            self.accounts[obe_id] = obe_account

        # Create journal entry
        lines = []
        if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            # Debit the account, credit OBE
            lines.append(JournalEntryLine(
                line_id=str(uuid.uuid4()),
                account_id=account.account_id,
                description=f"Opening balance - {account.name}",
                debit=abs(balance),
                credit=0
            ))
            lines.append(JournalEntryLine(
                line_id=str(uuid.uuid4()),
                account_id=obe_account.account_id,
                description=f"Opening balance - {account.name}",
                debit=0,
                credit=abs(balance)
            ))
        else:
            # Credit the account, debit OBE
            lines.append(JournalEntryLine(
                line_id=str(uuid.uuid4()),
                account_id=account.account_id,
                description=f"Opening balance - {account.name}",
                debit=0,
                credit=abs(balance)
            ))
            lines.append(JournalEntryLine(
                line_id=str(uuid.uuid4()),
                account_id=obe_account.account_id,
                description=f"Opening balance - {account.name}",
                debit=abs(balance),
                credit=0
            ))

        entry = JournalEntry(
            entry_id=str(uuid.uuid4()),
            entry_number=self.next_entry_number,
            entry_date=entry_date,
            lines=lines,
            memo=f"Opening balance for {account.name}",
            status=TransactionStatus.POSTED,
            source_type="opening_balance"
        )

        self.journal_entries[entry.entry_id] = entry
        self.next_entry_number += 1

    def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        tax_line: Optional[str] = None
    ) -> Dict:
        """Update an existing account"""
        if account_id not in self.accounts:
            return {"success": False, "error": "Account not found"}

        account = self.accounts[account_id]

        if name:
            account.name = name
        if description is not None:
            account.description = description
        if is_active is not None:
            account.is_active = is_active
        if tax_line is not None:
            account.tax_line = tax_line

        account.updated_at = datetime.now()

        return {
            "success": True,
            "account": self._account_to_dict(account)
        }

    def delete_account(self, account_id: str) -> Dict:
        """Delete an account (only if no transactions)"""
        if account_id not in self.accounts:
            return {"success": False, "error": "Account not found"}

        account = self.accounts[account_id]

        if account.is_system:
            return {"success": False, "error": "Cannot delete system account"}

        # Check for transactions
        for entry in self.journal_entries.values():
            for line in entry.lines:
                if line.account_id == account_id:
                    return {"success": False, "error": "Cannot delete account with transactions"}

        del self.accounts[account_id]
        return {"success": True, "message": "Account deleted"}

    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get a single account"""
        if account_id not in self.accounts:
            return None
        return self._account_to_dict(self.accounts[account_id])

    def get_account_by_number(self, account_number: str) -> Optional[Dict]:
        """Get account by account number"""
        for account in self.accounts.values():
            if account.account_number == account_number:
                return self._account_to_dict(account)
        return None

    def list_accounts(
        self,
        account_type: Optional[str] = None,
        active_only: bool = True,
        include_balances: bool = False
    ) -> List[Dict]:
        """List all accounts with optional filtering"""
        result = []

        for account in sorted(self.accounts.values(), key=lambda a: a.account_number):
            if active_only and not account.is_active:
                continue
            if account_type and account.account_type.value != account_type:
                continue

            acct_dict = self._account_to_dict(account)

            if include_balances:
                acct_dict["balance"] = self.get_account_balance(account.account_id)

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

        for account in sorted(self.accounts.values(), key=lambda a: a.account_number):
            if not account.is_active:
                continue

            acct_dict = self._account_to_dict(account)
            acct_dict["balance"] = self.get_account_balance(account.account_id)

            if account.account_type == AccountType.ASSET:
                coa["assets"].append(acct_dict)
            elif account.account_type == AccountType.LIABILITY:
                coa["liabilities"].append(acct_dict)
            elif account.account_type == AccountType.EQUITY:
                coa["equity"].append(acct_dict)
            elif account.account_type == AccountType.REVENUE:
                coa["revenue"].append(acct_dict)
            elif account.account_type == AccountType.EXPENSE:
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

        # Validate accounts exist
        for line in lines:
            if line["account_id"] not in self.accounts:
                return {"success": False, "error": f"Account {line['account_id']} not found"}

        entry_id = str(uuid.uuid4())
        je_lines = []

        for line in lines:
            je_lines.append(JournalEntryLine(
                line_id=str(uuid.uuid4()),
                account_id=line["account_id"],
                description=line.get("description", ""),
                debit=line.get("debit", 0),
                credit=line.get("credit", 0),
                tax_code=line.get("tax_code"),
                billable=line.get("billable", False),
                customer_id=line.get("customer_id"),
                vendor_id=line.get("vendor_id"),
                class_id=line.get("class_id"),
                location_id=line.get("location_id")
            ))

        entry = JournalEntry(
            entry_id=entry_id,
            entry_number=self.next_entry_number,
            entry_date=datetime.strptime(entry_date, "%Y-%m-%d").date(),
            lines=je_lines,
            memo=memo,
            status=TransactionStatus.POSTED if auto_post else TransactionStatus.DRAFT,
            source_type=source_type,
            source_id=source_id,
            adjusting_entry=adjusting_entry,
            posted_at=datetime.now() if auto_post else None
        )

        self.journal_entries[entry_id] = entry
        self.next_entry_number += 1

        return {
            "success": True,
            "entry_id": entry_id,
            "entry_number": entry.entry_number,
            "entry": self._entry_to_dict(entry)
        }

    def post_journal_entry(self, entry_id: str) -> Dict:
        """Post a draft journal entry"""
        if entry_id not in self.journal_entries:
            return {"success": False, "error": "Journal entry not found"}

        entry = self.journal_entries[entry_id]

        if entry.status != TransactionStatus.DRAFT:
            return {"success": False, "error": f"Entry is already {entry.status.value}"}

        entry.status = TransactionStatus.POSTED
        entry.posted_at = datetime.now()

        return {
            "success": True,
            "entry": self._entry_to_dict(entry)
        }

    def void_journal_entry(self, entry_id: str, reason: str = "") -> Dict:
        """Void a posted journal entry"""
        if entry_id not in self.journal_entries:
            return {"success": False, "error": "Journal entry not found"}

        entry = self.journal_entries[entry_id]

        if entry.status == TransactionStatus.VOIDED:
            return {"success": False, "error": "Entry is already voided"}

        if entry.status == TransactionStatus.RECONCILED:
            return {"success": False, "error": "Cannot void reconciled entry"}

        entry.status = TransactionStatus.VOIDED
        entry.memo = f"{entry.memo} [VOIDED: {reason}]"

        return {
            "success": True,
            "entry": self._entry_to_dict(entry)
        }

    def reverse_journal_entry(self, entry_id: str, reversal_date: str) -> Dict:
        """Create a reversing entry for a posted journal entry"""
        if entry_id not in self.journal_entries:
            return {"success": False, "error": "Journal entry not found"}

        original = self.journal_entries[entry_id]

        if original.status != TransactionStatus.POSTED:
            return {"success": False, "error": "Can only reverse posted entries"}

        # Create reversed lines
        reversed_lines = []
        for line in original.lines:
            reversed_lines.append({
                "account_id": line.account_id,
                "description": f"Reversal: {line.description}",
                "debit": line.credit,  # Swap debit and credit
                "credit": line.debit,
                "class_id": line.class_id,
                "location_id": line.location_id
            })

        result = self.create_journal_entry(
            entry_date=reversal_date,
            lines=reversed_lines,
            memo=f"Reversal of entry #{original.entry_number}",
            source_type="reversal",
            source_id=entry_id,
            auto_post=True
        )

        if result["success"]:
            original.reversing_entry = True
            result["original_entry_id"] = entry_id

        return result

    def get_journal_entry(self, entry_id: str) -> Optional[Dict]:
        """Get a single journal entry"""
        if entry_id not in self.journal_entries:
            return None
        return self._entry_to_dict(self.journal_entries[entry_id])

    def list_journal_entries(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        account_id: Optional[str] = None
    ) -> List[Dict]:
        """List journal entries with filtering"""
        result = []

        for entry in sorted(self.journal_entries.values(), key=lambda e: (e.entry_date, e.entry_number)):
            if start_date:
                if entry.entry_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if entry.entry_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue
            if status and entry.status.value != status:
                continue
            if source_type and entry.source_type != source_type:
                continue
            if account_id:
                if not any(line.account_id == account_id for line in entry.lines):
                    continue

            result.append(self._entry_to_dict(entry))

        return result

    # ==================== GENERAL LEDGER ====================

    def get_account_balance(
        self,
        account_id: str,
        as_of_date: Optional[str] = None
    ) -> float:
        """Calculate account balance as of a date"""
        if account_id not in self.accounts:
            return 0.0

        account = self.accounts[account_id]
        balance = account.opening_balance

        cutoff_date = None
        if as_of_date:
            cutoff_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()

        for entry in self.journal_entries.values():
            if entry.status not in [TransactionStatus.POSTED, TransactionStatus.RECONCILED]:
                continue
            if cutoff_date and entry.entry_date > cutoff_date:
                continue

            for line in entry.lines:
                if line.account_id == account_id:
                    # Assets and Expenses increase with debits
                    if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                        balance += line.debit - line.credit
                    # Liabilities, Equity, Revenue increase with credits
                    else:
                        balance += line.credit - line.debit

        return round(balance, 2)

    def get_account_ledger(
        self,
        account_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Get detailed ledger for an account"""
        if account_id not in self.accounts:
            return {"error": "Account not found"}

        account = self.accounts[account_id]

        # Calculate opening balance
        opening_balance = account.opening_balance
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            for entry in self.journal_entries.values():
                if entry.status not in [TransactionStatus.POSTED, TransactionStatus.RECONCILED]:
                    continue
                if entry.entry_date >= start:
                    continue
                for line in entry.lines:
                    if line.account_id == account_id:
                        if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                            opening_balance += line.debit - line.credit
                        else:
                            opening_balance += line.credit - line.debit

        # Get transactions
        transactions = []
        running_balance = opening_balance

        for entry in sorted(self.journal_entries.values(), key=lambda e: (e.entry_date, e.entry_number)):
            if entry.status not in [TransactionStatus.POSTED, TransactionStatus.RECONCILED]:
                continue
            if start_date:
                if entry.entry_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if entry.entry_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            for line in entry.lines:
                if line.account_id == account_id:
                    if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                        running_balance += line.debit - line.credit
                    else:
                        running_balance += line.credit - line.debit

                    transactions.append({
                        "date": entry.entry_date.isoformat(),
                        "entry_number": entry.entry_number,
                        "entry_id": entry.entry_id,
                        "description": line.description or entry.memo,
                        "debit": line.debit,
                        "credit": line.credit,
                        "balance": round(running_balance, 2),
                        "source_type": entry.source_type
                    })

        return {
            "account": self._account_to_dict(account),
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

        for account in sorted(self.accounts.values(), key=lambda a: a.account_number):
            if not account.is_active:
                continue

            balance = self.get_account_balance(account.account_id, as_of_date)

            if balance == 0:
                continue

            debit = balance if balance > 0 and account.account_type in [AccountType.ASSET, AccountType.EXPENSE] else 0
            credit = abs(balance) if balance < 0 and account.account_type in [AccountType.ASSET, AccountType.EXPENSE] else 0

            if account.account_type in [AccountType.LIABILITY, AccountType.EQUITY, AccountType.REVENUE]:
                debit = abs(balance) if balance < 0 else 0
                credit = balance if balance > 0 else 0

            # Normalize
            if account.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
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
                "account_number": account.account_number,
                "account_name": account.name,
                "account_type": account.account_type.value,
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
            period = FiscalPeriod(
                period_id=period_id,
                name=f"{year}-{month:02d}",
                start_date=date(year, month, 1),
                end_date=date(year, month, end_day),
                fiscal_year=year,
                period_number=period_num
            )

            self.fiscal_periods[period_id] = period
            periods.append({
                "period_id": period_id,
                "name": period.name,
                "start_date": period.start_date.isoformat(),
                "end_date": period.end_date.isoformat(),
                "period_number": period.period_number
            })

        return {
            "success": True,
            "fiscal_year": year,
            "periods": periods
        }

    def close_fiscal_period(self, period_id: str, closed_by: str) -> Dict:
        """Close a fiscal period"""
        if period_id not in self.fiscal_periods:
            return {"success": False, "error": "Period not found"}

        period = self.fiscal_periods[period_id]
        period.is_closed = True
        period.closed_at = datetime.now()
        period.closed_by = closed_by

        return {
            "success": True,
            "period": {
                "period_id": period.period_id,
                "name": period.name,
                "is_closed": period.is_closed,
                "closed_at": period.closed_at.isoformat()
            }
        }

    def close_fiscal_year(self, year: int, retained_earnings_account_id: str) -> Dict:
        """Close fiscal year - transfer net income to retained earnings"""
        # Calculate net income
        total_revenue = 0
        total_expenses = 0

        year_start = date(year, self.fiscal_year_start_month, 1)
        if self.fiscal_year_start_month == 1:
            year_end = date(year, 12, 31)
        else:
            year_end = date(year + 1, self.fiscal_year_start_month - 1, 28)

        for account in self.accounts.values():
            if account.account_type == AccountType.REVENUE:
                total_revenue += self.get_account_balance(account.account_id, year_end.isoformat())
            elif account.account_type == AccountType.EXPENSE:
                total_expenses += self.get_account_balance(account.account_id, year_end.isoformat())

        net_income = total_revenue - total_expenses

        # Create closing entry
        closing_lines = []

        # Close revenue accounts
        for account in self.accounts.values():
            if account.account_type == AccountType.REVENUE:
                balance = self.get_account_balance(account.account_id, year_end.isoformat())
                if balance != 0:
                    closing_lines.append({
                        "account_id": account.account_id,
                        "description": f"Close {account.name}",
                        "debit": balance if balance > 0 else 0,
                        "credit": abs(balance) if balance < 0 else 0
                    })

        # Close expense accounts
        for account in self.accounts.values():
            if account.account_type == AccountType.EXPENSE:
                balance = self.get_account_balance(account.account_id, year_end.isoformat())
                if balance != 0:
                    closing_lines.append({
                        "account_id": account.account_id,
                        "description": f"Close {account.name}",
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

        tracking = ClassTracking(
            class_id=class_id,
            name=name,
            parent_class_id=parent_class_id
        )

        self.classes[class_id] = tracking

        return {
            "success": True,
            "class_id": class_id,
            "name": name
        }

    def list_classes(self) -> List[Dict]:
        """List all classes"""
        return [
            {
                "class_id": c.class_id,
                "name": c.name,
                "parent_class_id": c.parent_class_id,
                "is_active": c.is_active
            }
            for c in self.classes.values()
        ]

    def create_location(self, name: str, address: str = "") -> Dict:
        """Create a location for tracking"""
        location_id = str(uuid.uuid4())

        location = Location(
            location_id=location_id,
            name=name,
            address=address
        )

        self.locations[location_id] = location

        return {
            "success": True,
            "location_id": location_id,
            "name": name
        }

    def list_locations(self) -> List[Dict]:
        """List all locations"""
        return [
            {
                "location_id": loc.location_id,
                "name": loc.name,
                "address": loc.address,
                "is_active": loc.is_active
            }
            for loc in self.locations.values()
        ]

    # ==================== UTILITY METHODS ====================

    def _account_to_dict(self, account: Account) -> Dict:
        """Convert Account to dictionary"""
        return {
            "account_id": account.account_id,
            "account_number": account.account_number,
            "name": account.name,
            "account_type": account.account_type.value,
            "sub_type": account.sub_type.value,
            "description": account.description,
            "parent_account_id": account.parent_account_id,
            "is_active": account.is_active,
            "is_system": account.is_system,
            "tax_line": account.tax_line,
            "opening_balance": account.opening_balance,
            "opening_balance_date": account.opening_balance_date.isoformat() if account.opening_balance_date else None,
            "currency": account.currency,
            "created_at": account.created_at.isoformat(),
            "updated_at": account.updated_at.isoformat()
        }

    def _entry_to_dict(self, entry: JournalEntry) -> Dict:
        """Convert JournalEntry to dictionary"""
        return {
            "entry_id": entry.entry_id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat(),
            "lines": [
                {
                    "line_id": line.line_id,
                    "account_id": line.account_id,
                    "account_name": self.accounts[line.account_id].name if line.account_id in self.accounts else "Unknown",
                    "account_number": self.accounts[line.account_id].account_number if line.account_id in self.accounts else "",
                    "description": line.description,
                    "debit": line.debit,
                    "credit": line.credit,
                    "tax_code": line.tax_code,
                    "billable": line.billable,
                    "customer_id": line.customer_id,
                    "vendor_id": line.vendor_id,
                    "class_id": line.class_id,
                    "location_id": line.location_id
                }
                for line in entry.lines
            ],
            "memo": entry.memo,
            "status": entry.status.value,
            "source_type": entry.source_type,
            "source_id": entry.source_id,
            "adjusting_entry": entry.adjusting_entry,
            "reversing_entry": entry.reversing_entry,
            "reversed_entry_id": entry.reversed_entry_id,
            "created_by": entry.created_by,
            "created_at": entry.created_at.isoformat(),
            "posted_at": entry.posted_at.isoformat() if entry.posted_at else None,
            "total_debits": sum(line.debit for line in entry.lines),
            "total_credits": sum(line.credit for line in entry.lines)
        }

    def get_system_summary(self) -> Dict:
        """Get GenFin system summary"""
        total_accounts = len(self.accounts)
        active_accounts = sum(1 for a in self.accounts.values() if a.is_active)
        total_entries = len(self.journal_entries)
        posted_entries = sum(1 for e in self.journal_entries.values() if e.status == TransactionStatus.POSTED)

        return {
            "system": "GenFin Core Accounting",
            "version": "1.0.0",
            "company_name": self.company_name,
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "total_journal_entries": total_entries,
            "posted_entries": posted_entries,
            "fiscal_year_start_month": self.fiscal_year_start_month,
            "next_entry_number": self.next_entry_number,
            "classes_count": len(self.classes),
            "locations_count": len(self.locations)
        }


# Singleton instance
genfin_core_service = GenFinCoreService()
