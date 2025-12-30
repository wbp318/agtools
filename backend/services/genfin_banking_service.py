"""
GenFin Banking Service - Bank Accounts, Transactions, Reconciliation, CHECK PRINTING, ACH/Direct Deposit
Complete banking and check management for farm operations
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
import math

from .genfin_core_service import genfin_core_service


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
    STALE = "stale"  # Over 180 days


class ReconciliationStatus(Enum):
    """Reconciliation status"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISCREPANCY = "discrepancy"


class CheckFormat(Enum):
    """Check printing formats"""
    STANDARD_TOP = "standard_top"  # Check on top, stub below
    STANDARD_MIDDLE = "standard_middle"  # Stub, check, stub
    STANDARD_BOTTOM = "standard_bottom"  # Stub on top, check below
    VOUCHER_3UP = "voucher_3up"  # 3 checks per page with vouchers
    WALLET = "wallet"  # Personal wallet-size checks
    QUICKBOOKS_STANDARD = "quickbooks_standard"  # QB compatible format
    QUICKBOOKS_VOUCHER = "quickbooks_voucher"  # QB voucher checks


class ACHTransactionCode(Enum):
    """ACH/NACHA transaction codes"""
    CHECKING_CREDIT = "22"  # Deposit to checking
    CHECKING_DEBIT = "27"  # Withdrawal from checking
    SAVINGS_CREDIT = "32"  # Deposit to savings
    SAVINGS_DEBIT = "37"  # Withdrawal from savings
    CHECKING_CREDIT_PRENOTE = "23"  # Prenote for checking deposit
    CHECKING_DEBIT_PRENOTE = "28"  # Prenote for checking withdrawal


@dataclass
class BankAccount:
    """Bank account record"""
    bank_account_id: str
    account_name: str
    account_type: BankAccountType

    # Bank details
    bank_name: str
    routing_number: str
    account_number: str

    # Check printing
    check_printing_enabled: bool = True
    next_check_number: int = 1001
    check_format: CheckFormat = CheckFormat.QUICKBOOKS_VOUCHER

    # Direct deposit
    ach_enabled: bool = False
    ach_company_id: str = ""  # Your company's ACH ID
    ach_company_name: str = ""

    # Linked GL account
    gl_account_id: Optional[str] = None

    # Balance tracking
    current_balance: float = 0.0
    available_balance: float = 0.0
    last_reconciled_date: Optional[date] = None
    last_reconciled_balance: float = 0.0

    # Status
    is_active: bool = True
    is_default: bool = False

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BankTransaction:
    """Bank transaction record"""
    transaction_id: str
    bank_account_id: str
    transaction_date: date
    transaction_type: TransactionType

    amount: float
    payee: str = ""
    memo: str = ""
    reference_number: str = ""  # Check number, confirmation, etc.

    # Categorization
    category_account_id: Optional[str] = None

    # Reconciliation
    is_reconciled: bool = False
    reconciled_date: Optional[date] = None

    # Linking
    journal_entry_id: Optional[str] = None
    check_id: Optional[str] = None
    transfer_id: Optional[str] = None

    # Import tracking
    imported: bool = False
    import_id: Optional[str] = None
    fitid: Optional[str] = None  # Financial Institution Transaction ID

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Check:
    """Check record for printing and tracking"""
    check_id: str
    bank_account_id: str
    check_number: int
    check_date: date

    # Payee info
    payee_name: str
    payee_address_line1: str = ""
    payee_address_line2: str = ""
    payee_city: str = ""
    payee_state: str = ""
    payee_zip: str = ""

    # Amount
    amount: float = 0.0
    amount_in_words: str = ""

    # Details
    memo: str = ""
    voucher_description: str = ""  # Detailed description for voucher stub

    # For bill payments
    bills_paid: List[Dict] = field(default_factory=list)  # [{bill_id, bill_number, amount}]
    vendor_id: Optional[str] = None

    # Status
    status: CheckStatus = CheckStatus.PRINTED
    printed_at: Optional[datetime] = None
    cleared_date: Optional[date] = None
    voided_date: Optional[date] = None
    void_reason: str = ""

    # Signature
    signature_line_1: str = ""  # For printed signature or blank line
    signature_line_2: str = ""  # Second signature if required
    requires_two_signatures: bool = False
    two_signature_threshold: float = 10000.0

    # Linking
    journal_entry_id: Optional[str] = None
    transaction_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CheckPrintBatch:
    """Batch of checks to print"""
    batch_id: str
    bank_account_id: str
    checks: List[str]  # Check IDs
    created_at: datetime = field(default_factory=datetime.now)
    printed_at: Optional[datetime] = None
    print_status: str = "pending"  # pending, printing, completed, failed


@dataclass
class ACHBatch:
    """ACH/Direct Deposit batch"""
    batch_id: str
    bank_account_id: str
    batch_date: date
    effective_date: date

    # Batch header info
    company_name: str
    company_id: str
    batch_description: str = ""  # e.g., "PAYROLL", "VENDOR PMT"

    # Entries
    entries: List[Dict] = field(default_factory=list)
    # Each entry: {recipient_name, routing_number, account_number, account_type, amount, transaction_code, individual_id}

    # Totals
    total_debit: float = 0.0
    total_credit: float = 0.0
    entry_count: int = 0

    # Status
    status: str = "created"  # created, generated, submitted, processed
    nacha_file_content: str = ""

    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None


@dataclass
class Reconciliation:
    """Bank reconciliation session"""
    reconciliation_id: str
    bank_account_id: str
    statement_date: date
    statement_ending_balance: float

    # Period
    period_start: date
    period_end: date

    # Calculated values
    beginning_balance: float = 0.0
    cleared_deposits: float = 0.0
    cleared_payments: float = 0.0
    cleared_balance: float = 0.0

    # Outstanding items
    outstanding_deposits: List[str] = field(default_factory=list)
    outstanding_checks: List[str] = field(default_factory=list)

    # Difference
    difference: float = 0.0

    # Status
    status: ReconciliationStatus = ReconciliationStatus.IN_PROGRESS
    completed_at: Optional[datetime] = None
    completed_by: str = ""

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Transfer:
    """Bank transfer between accounts"""
    transfer_id: str
    from_account_id: str
    to_account_id: str
    transfer_date: date
    amount: float
    memo: str = ""

    from_transaction_id: Optional[str] = None
    to_transaction_id: Optional[str] = None
    journal_entry_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)


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
    GenFin Banking Service

    Complete banking functionality:
    - Bank account management
    - Transaction tracking
    - CHECK PRINTING (multiple formats, MICR support)
    - Bank reconciliation
    - Transfers between accounts
    - ACH/Direct Deposit file generation (NACHA format)
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

        self.bank_accounts: Dict[str, BankAccount] = {}
        self.transactions: Dict[str, BankTransaction] = {}
        self.checks: Dict[str, Check] = {}
        self.check_batches: Dict[str, CheckPrintBatch] = {}
        self.ach_batches: Dict[str, ACHBatch] = {}
        self.reconciliations: Dict[str, Reconciliation] = {}
        self.transfers: Dict[str, Transfer] = {}

        self._initialized = True

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

        # Set as default if first account
        is_default = len(self.bank_accounts) == 0

        account = BankAccount(
            bank_account_id=bank_account_id,
            account_name=account_name,
            account_type=BankAccountType(account_type),
            bank_name=bank_name,
            routing_number=routing_number,
            account_number=account_number,
            gl_account_id=gl_account_id,
            current_balance=starting_balance,
            available_balance=starting_balance,
            next_check_number=starting_check_number,
            check_format=CheckFormat(check_format),
            ach_enabled=ach_enabled,
            ach_company_id=ach_company_id,
            ach_company_name=ach_company_name,
            is_default=is_default
        )

        self.bank_accounts[bank_account_id] = account

        return {
            "success": True,
            "bank_account_id": bank_account_id,
            "account": self._account_to_dict(account)
        }

    def update_bank_account(self, bank_account_id: str, **kwargs) -> Dict:
        """Update bank account settings"""
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        account = self.bank_accounts[bank_account_id]

        for key, value in kwargs.items():
            if hasattr(account, key) and value is not None:
                if key == "check_format":
                    value = CheckFormat(value)
                elif key == "account_type":
                    value = BankAccountType(value)
                setattr(account, key, value)

        account.updated_at = datetime.now()

        return {
            "success": True,
            "account": self._account_to_dict(account)
        }

    def get_bank_account(self, bank_account_id: str) -> Optional[Dict]:
        """Get bank account by ID"""
        if bank_account_id not in self.bank_accounts:
            return None
        return self._account_to_dict(self.bank_accounts[bank_account_id])

    def list_bank_accounts(self, active_only: bool = True) -> List[Dict]:
        """List all bank accounts"""
        result = []
        for account in self.bank_accounts.values():
            if active_only and not account.is_active:
                continue
            result.append(self._account_to_dict(account))
        return sorted(result, key=lambda a: a["account_name"])

    def set_default_account(self, bank_account_id: str) -> Dict:
        """Set default bank account"""
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        for account in self.bank_accounts.values():
            account.is_default = (account.bank_account_id == bank_account_id)

        return {"success": True, "message": "Default account updated"}

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
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        account = self.bank_accounts[bank_account_id]

        if not account.check_printing_enabled:
            return {"success": False, "error": "Check printing not enabled for this account"}

        check_id = str(uuid.uuid4())
        c_date = datetime.strptime(check_date, "%Y-%m-%d").date()

        # Use provided check number or get next
        if check_number is None:
            check_number = account.next_check_number
            account.next_check_number += 1

        # Convert amount to words
        amount_words = number_to_words(amount)

        # Build voucher description from bills if provided
        if bills_paid and not voucher_description:
            desc_lines = []
            for bill in bills_paid:
                desc_lines.append(f"Bill #{bill.get('bill_number', 'N/A')}: ${bill.get('amount', 0):.2f}")
            voucher_description = "\n".join(desc_lines)

        check = Check(
            check_id=check_id,
            bank_account_id=bank_account_id,
            check_number=check_number,
            check_date=c_date,
            payee_name=payee_name,
            payee_address_line1=payee_address_line1,
            payee_address_line2=payee_address_line2,
            payee_city=payee_city,
            payee_state=payee_state,
            payee_zip=payee_zip,
            amount=amount,
            amount_in_words=amount_words,
            memo=memo,
            voucher_description=voucher_description,
            bills_paid=bills_paid or [],
            vendor_id=vendor_id,
            status=CheckStatus.OUTSTANDING,
            requires_two_signatures=amount >= 10000.0
        )

        self.checks[check_id] = check

        # Create bank transaction
        trans_id = str(uuid.uuid4())
        transaction = BankTransaction(
            transaction_id=trans_id,
            bank_account_id=bank_account_id,
            transaction_date=c_date,
            transaction_type=TransactionType.CHECK,
            amount=-amount,  # Negative for outgoing
            payee=payee_name,
            memo=memo,
            reference_number=str(check_number),
            check_id=check_id
        )
        self.transactions[trans_id] = transaction
        check.transaction_id = trans_id

        # Update account balance
        account.current_balance -= amount

        return {
            "success": True,
            "check_id": check_id,
            "check_number": check_number,
            "check": self._check_to_dict(check)
        }

    def get_check_print_data(self, check_id: str) -> Dict:
        """Get formatted data for printing a check"""
        if check_id not in self.checks:
            return {"error": "Check not found"}

        check = self.checks[check_id]
        account = self.bank_accounts.get(check.bank_account_id)

        if not account:
            return {"error": "Bank account not found"}

        # Format MICR line (standard format)
        # ⑆ = Transit symbol, ⑈ = On-Us symbol, ⑇ = Amount symbol
        micr_routing = f"⑆{account.routing_number}⑆"
        micr_account = f"{account.account_number}⑈"
        micr_check = f"{check.check_number:08d}"
        micr_line = f"{micr_routing} {micr_account} {micr_check}"

        # Alternate MICR using standard characters for compatibility
        micr_line_alt = f"C{account.routing_number}C {account.account_number}D {check.check_number:08d}"

        # Format payee address
        payee_address = check.payee_address_line1
        if check.payee_address_line2:
            payee_address += f"\n{check.payee_address_line2}"
        if check.payee_city or check.payee_state or check.payee_zip:
            payee_address += f"\n{check.payee_city}, {check.payee_state} {check.payee_zip}"

        # Format date
        date_formatted = check.check_date.strftime("%m/%d/%Y")
        date_long = check.check_date.strftime("%B %d, %Y")

        return {
            "check_id": check.check_id,
            "check_number": check.check_number,
            "check_number_formatted": f"{check.check_number:08d}",

            # Bank info
            "bank_name": account.bank_name,
            "routing_number": account.routing_number,
            "account_number": account.account_number,
            "account_number_masked": f"****{account.account_number[-4:]}",

            # MICR line for magnetic ink
            "micr_line": micr_line,
            "micr_line_alt": micr_line_alt,

            # Date
            "check_date": check.check_date.isoformat(),
            "date_formatted": date_formatted,
            "date_long": date_long,

            # Payee
            "payee_name": check.payee_name,
            "payee_address": payee_address,
            "payee_address_line1": check.payee_address_line1,
            "payee_address_line2": check.payee_address_line2,
            "payee_city": check.payee_city,
            "payee_state": check.payee_state,
            "payee_zip": check.payee_zip,

            # Amount
            "amount": check.amount,
            "amount_formatted": f"${check.amount:,.2f}",
            "amount_numeric": f"**{check.amount:,.2f}**",  # With security asterisks
            "amount_in_words": check.amount_in_words,
            "amount_in_words_line": f"{check.amount_in_words}{'*' * (50 - len(check.amount_in_words))}",  # Pad with asterisks

            # Memo
            "memo": check.memo,

            # Voucher stub info
            "voucher_description": check.voucher_description,
            "bills_paid": check.bills_paid,

            # Signature
            "requires_two_signatures": check.requires_two_signatures,
            "signature_line_1": check.signature_line_1,
            "signature_line_2": check.signature_line_2,

            # Print format
            "check_format": account.check_format.value,

            # Status
            "status": check.status.value,
            "printed_at": check.printed_at.isoformat() if check.printed_at else None
        }

    def get_check_print_layout(self, check_id: str, format_override: Optional[str] = None) -> Dict:
        """Get complete print layout for a check with positioning"""
        print_data = self.get_check_print_data(check_id)
        if "error" in print_data:
            return print_data

        check = self.checks[check_id]
        account = self.bank_accounts[check.bank_account_id]

        check_format = CheckFormat(format_override) if format_override else account.check_format

        # Define print positions (in inches from top-left)
        # These match standard QuickBooks check layouts

        if check_format == CheckFormat.QUICKBOOKS_VOUCHER:
            # QuickBooks Voucher Check (3.5" check with 2 voucher stubs)
            layout = {
                "page_size": {"width": 8.5, "height": 11},
                "check_area": {
                    "top": 7.0,
                    "height": 3.5
                },
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
                    "top": 0.0,
                    "height": 3.5,
                    "fields": {
                        "payee": {"x": 0.5, "y": 0.5},
                        "date": {"x": 6.0, "y": 0.5},
                        "check_number": {"x": 7.0, "y": 0.5},
                        "description": {"x": 0.5, "y": 1.0},
                        "amount": {"x": 6.5, "y": 2.5}
                    }
                },
                "voucher_2": {
                    "top": 3.5,
                    "height": 3.5,
                    "fields": {
                        "payee": {"x": 0.5, "y": 4.0},
                        "date": {"x": 6.0, "y": 4.0},
                        "check_number": {"x": 7.0, "y": 4.0},
                        "description": {"x": 0.5, "y": 4.5},
                        "amount": {"x": 6.5, "y": 6.0}
                    }
                }
            }

        elif check_format == CheckFormat.QUICKBOOKS_STANDARD:
            # QuickBooks Standard Check (check on top, one stub below)
            layout = {
                "page_size": {"width": 8.5, "height": 11},
                "check_area": {
                    "top": 0.0,
                    "height": 3.5
                },
                "fields": {
                    "date": {"x": 6.5, "y": 0.3},
                    "payee_name": {"x": 1.0, "y": 0.8},
                    "amount_numeric": {"x": 6.8, "y": 0.8},
                    "amount_words": {"x": 0.5, "y": 1.3, "width": 5.5},
                    "payee_address": {"x": 1.0, "y": 1.6},
                    "memo": {"x": 0.5, "y": 2.8},
                    "signature_line_1": {"x": 4.5, "y": 2.8},
                    "micr_line": {"x": 0.5, "y": 3.3},
                    "check_number": {"x": 7.0, "y": 0.0}
                },
                "stub_area": {
                    "top": 3.5,
                    "height": 7.5,
                    "fields": {
                        "payee": {"x": 0.5, "y": 4.0},
                        "date": {"x": 0.5, "y": 4.5},
                        "check_number": {"x": 2.5, "y": 4.5},
                        "description": {"x": 0.5, "y": 5.0},
                        "amount": {"x": 6.5, "y": 4.5}
                    }
                }
            }

        elif check_format == CheckFormat.VOUCHER_3UP:
            # 3-per-page voucher checks
            layout = {
                "page_size": {"width": 8.5, "height": 11},
                "checks_per_page": 3,
                "check_height": 3.667,
                "fields": {
                    "date": {"x": 6.5, "y_offset": 0.3},
                    "payee_name": {"x": 1.0, "y_offset": 0.7},
                    "amount_numeric": {"x": 6.8, "y_offset": 0.7},
                    "amount_words": {"x": 0.5, "y_offset": 1.1, "width": 5.5},
                    "memo": {"x": 0.5, "y_offset": 2.0},
                    "signature_line_1": {"x": 4.5, "y_offset": 2.5},
                    "micr_line": {"x": 0.5, "y_offset": 3.4},
                    "check_number": {"x": 7.0, "y_offset": 0.0}
                }
            }

        else:
            # Standard top check format
            layout = {
                "page_size": {"width": 8.5, "height": 11},
                "check_area": {
                    "top": 0.0,
                    "height": 3.5
                },
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
        if check_id not in self.checks:
            return {"success": False, "error": "Check not found"}

        check = self.checks[check_id]
        check.status = CheckStatus.PRINTED
        check.printed_at = datetime.now()

        return {
            "success": True,
            "check": self._check_to_dict(check)
        }

    def void_check(self, check_id: str, reason: str = "") -> Dict:
        """Void a check"""
        if check_id not in self.checks:
            return {"success": False, "error": "Check not found"}

        check = self.checks[check_id]

        if check.status == CheckStatus.CLEARED:
            return {"success": False, "error": "Cannot void a cleared check"}

        check.status = CheckStatus.VOIDED
        check.voided_date = date.today()
        check.void_reason = reason

        # Reverse the transaction
        if check.transaction_id and check.transaction_id in self.transactions:
            trans = self.transactions[check.transaction_id]
            account = self.bank_accounts[check.bank_account_id]
            account.current_balance -= trans.amount  # Add back (trans.amount is negative)

        return {
            "success": True,
            "check": self._check_to_dict(check)
        }

    def create_check_batch(self, bank_account_id: str, check_ids: List[str]) -> Dict:
        """Create a batch of checks for printing"""
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        # Validate all checks
        for check_id in check_ids:
            if check_id not in self.checks:
                return {"success": False, "error": f"Check {check_id} not found"}
            if self.checks[check_id].bank_account_id != bank_account_id:
                return {"success": False, "error": f"Check {check_id} is not from this bank account"}

        batch_id = str(uuid.uuid4())

        batch = CheckPrintBatch(
            batch_id=batch_id,
            bank_account_id=bank_account_id,
            checks=check_ids
        )

        self.check_batches[batch_id] = batch

        return {
            "success": True,
            "batch_id": batch_id,
            "check_count": len(check_ids)
        }

    def get_check_batch_print_data(self, batch_id: str) -> Dict:
        """Get print data for entire batch"""
        if batch_id not in self.check_batches:
            return {"error": "Batch not found"}

        batch = self.check_batches[batch_id]
        checks_data = []

        for check_id in batch.checks:
            check_data = self.get_check_print_layout(check_id)
            if "error" not in check_data:
                checks_data.append(check_data)

        return {
            "batch_id": batch_id,
            "bank_account_id": batch.bank_account_id,
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
        result = []

        for check in self.checks.values():
            if bank_account_id and check.bank_account_id != bank_account_id:
                continue
            if status and check.status.value != status:
                continue
            if vendor_id and check.vendor_id != vendor_id:
                continue
            if start_date:
                if check.check_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if check.check_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            result.append(self._check_to_dict(check))

        return sorted(result, key=lambda c: c["check_number"], reverse=True)

    def get_outstanding_checks(self, bank_account_id: str) -> Dict:
        """Get list of outstanding (uncleared) checks"""
        if bank_account_id not in self.bank_accounts:
            return {"error": "Bank account not found"}

        outstanding = []
        total = 0.0

        for check in self.checks.values():
            if check.bank_account_id != bank_account_id:
                continue
            if check.status in [CheckStatus.OUTSTANDING, CheckStatus.PRINTED]:
                outstanding.append(self._check_to_dict(check))
                total += check.amount

        # Check for stale checks (over 180 days)
        today = date.today()
        for check_dict in outstanding:
            check_date = datetime.strptime(check_dict["check_date"], "%Y-%m-%d").date()
            if (today - check_date).days > 180:
                check_dict["is_stale"] = True

        return {
            "outstanding_checks": sorted(outstanding, key=lambda c: c["check_number"]),
            "count": len(outstanding),
            "total_amount": round(total, 2)
        }

    # ==================== ACH / DIRECT DEPOSIT ====================

    def create_ach_batch(
        self,
        bank_account_id: str,
        effective_date: str,
        batch_description: str,
        entries: List[Dict]
    ) -> Dict:
        """Create an ACH/Direct Deposit batch"""
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        account = self.bank_accounts[bank_account_id]

        if not account.ach_enabled:
            return {"success": False, "error": "ACH not enabled for this account"}

        batch_id = str(uuid.uuid4())
        eff_date = datetime.strptime(effective_date, "%Y-%m-%d").date()

        # Validate and process entries
        total_credit = 0.0
        total_debit = 0.0
        processed_entries = []

        for entry in entries:
            amount = entry.get("amount", 0)
            trans_code = entry.get("transaction_code", ACHTransactionCode.CHECKING_CREDIT.value)

            processed_entries.append({
                "recipient_name": entry.get("recipient_name", "")[:22],  # NACHA limit
                "routing_number": entry.get("routing_number", ""),
                "account_number": entry.get("account_number", ""),
                "account_type": entry.get("account_type", "checking"),
                "amount": amount,
                "transaction_code": trans_code,
                "individual_id": entry.get("individual_id", "")[:15],
                "individual_name": entry.get("individual_name", entry.get("recipient_name", ""))[:22]
            })

            if trans_code in ["22", "32"]:  # Credits
                total_credit += amount
            else:
                total_debit += amount

        batch = ACHBatch(
            batch_id=batch_id,
            bank_account_id=bank_account_id,
            batch_date=date.today(),
            effective_date=eff_date,
            company_name=account.ach_company_name[:16],
            company_id=account.ach_company_id,
            batch_description=batch_description[:10],
            entries=processed_entries,
            total_credit=round(total_credit, 2),
            total_debit=round(total_debit, 2),
            entry_count=len(processed_entries)
        )

        self.ach_batches[batch_id] = batch

        return {
            "success": True,
            "batch_id": batch_id,
            "entry_count": len(processed_entries),
            "total_credit": round(total_credit, 2),
            "total_debit": round(total_debit, 2)
        }

    def generate_nacha_file(self, batch_id: str) -> Dict:
        """Generate NACHA format file for ACH batch"""
        if batch_id not in self.ach_batches:
            return {"error": "Batch not found"}

        batch = self.ach_batches[batch_id]
        account = self.bank_accounts.get(batch.bank_account_id)

        if not account:
            return {"error": "Bank account not found"}

        lines = []

        # File Header Record (1)
        file_creation_date = datetime.now().strftime("%y%m%d")
        file_creation_time = datetime.now().strftime("%H%M")

        file_header = (
            "1"                                  # Record Type Code
            "01"                                 # Priority Code
            f" {account.routing_number:>9}"     # Immediate Destination (with leading space)
            f"{account.ach_company_id:>10}"     # Immediate Origin
            f"{file_creation_date}"             # File Creation Date
            f"{file_creation_time}"             # File Creation Time
            "A"                                  # File ID Modifier
            "094"                               # Record Size
            "10"                                # Blocking Factor
            "1"                                 # Format Code
            f"{account.bank_name:<23}"          # Immediate Destination Name
            f"{account.ach_company_name:<23}"   # Immediate Origin Name
            "        "                          # Reference Code
        )
        lines.append(file_header)

        # Batch Header Record (5)
        effective_date = batch.effective_date.strftime("%y%m%d")

        batch_header = (
            "5"                                  # Record Type Code
            "200"                               # Service Class Code (mixed debits/credits)
            f"{batch.company_name:<16}"         # Company Name
            f"{' ' * 20}"                       # Company Discretionary Data
            f"{batch.company_id:<10}"           # Company Identification
            "PPD"                               # Standard Entry Class (Prearranged Payment)
            f"{batch.batch_description:<10}"    # Company Entry Description
            f"{batch.batch_date.strftime('%y%m%d')}"  # Company Descriptive Date
            f"{effective_date}"                 # Effective Entry Date
            "   "                               # Settlement Date (leave blank)
            "1"                                 # Originator Status Code
            f"{account.routing_number[:8]:<8}" # Originating DFI Identification
            f"{1:07d}"                          # Batch Number
        )
        lines.append(batch_header)

        # Entry Detail Records (6)
        entry_hash = 0
        trace_number = 1

        for entry in batch.entries:
            routing_num = entry["routing_number"]
            entry_hash += int(routing_num[:8])

            entry_detail = (
                "6"                                      # Record Type Code
                f"{entry['transaction_code']}"           # Transaction Code
                f"{routing_num[:8]}{routing_num[8] if len(routing_num) > 8 else ' '}"  # Receiving DFI + Check Digit
                f"{entry['account_number']:<17}"         # DFI Account Number
                f"{int(entry['amount'] * 100):010d}"     # Amount
                f"{entry['individual_id']:<15}"          # Individual ID
                f"{entry['individual_name']:<22}"        # Individual Name
                "  "                                     # Discretionary Data
                "0"                                      # Addenda Record Indicator
                f"{account.routing_number[:8]}{trace_number:07d}"  # Trace Number
            )
            lines.append(entry_detail)
            trace_number += 1

        # Batch Control Record (8)
        entry_hash_mod = entry_hash % 10000000000  # Last 10 digits

        batch_control = (
            "8"                                          # Record Type Code
            "200"                                       # Service Class Code
            f"{batch.entry_count:06d}"                  # Entry/Addenda Count
            f"{entry_hash_mod:010d}"                    # Entry Hash
            f"{int(batch.total_debit * 100):012d}"      # Total Debit Entry Dollar Amount
            f"{int(batch.total_credit * 100):012d}"    # Total Credit Entry Dollar Amount
            f"{batch.company_id:<10}"                   # Company Identification
            f"{' ' * 19}"                               # Message Auth Code (blank)
            f"{' ' * 6}"                                # Reserved
            f"{account.routing_number[:8]:<8}"          # Originating DFI Identification
            f"{1:07d}"                                  # Batch Number
        )
        lines.append(batch_control)

        # File Control Record (9)
        block_count = math.ceil((len(lines) + 1) / 10)

        file_control = (
            "9"                                          # Record Type Code
            f"{1:06d}"                                   # Batch Count
            f"{block_count:06d}"                        # Block Count
            f"{batch.entry_count:08d}"                  # Entry/Addenda Count
            f"{entry_hash_mod:010d}"                    # Entry Hash
            f"{int(batch.total_debit * 100):012d}"      # Total Debit Entry Dollar Amount
            f"{int(batch.total_credit * 100):012d}"    # Total Credit Entry Dollar Amount
            f"{' ' * 39}"                               # Reserved
        )
        lines.append(file_control)

        # Pad to block size (10 records per block)
        while len(lines) % 10 != 0:
            lines.append("9" * 94)

        nacha_content = "\n".join(lines)
        batch.nacha_file_content = nacha_content
        batch.status = "generated"

        return {
            "success": True,
            "batch_id": batch_id,
            "file_content": nacha_content,
            "record_count": len(lines),
            "entry_count": batch.entry_count,
            "total_credit": batch.total_credit,
            "total_debit": batch.total_debit,
            "filename": f"ACH_{batch.batch_date.strftime('%Y%m%d')}_{batch_id[:8]}.txt"
        }

    def list_ach_batches(
        self,
        bank_account_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List ACH batches"""
        result = []

        for batch in self.ach_batches.values():
            if bank_account_id and batch.bank_account_id != bank_account_id:
                continue
            if status and batch.status != status:
                continue
            if start_date:
                if batch.batch_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if batch.batch_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            result.append({
                "batch_id": batch.batch_id,
                "bank_account_id": batch.bank_account_id,
                "batch_date": batch.batch_date.isoformat(),
                "effective_date": batch.effective_date.isoformat(),
                "batch_description": batch.batch_description,
                "entry_count": batch.entry_count,
                "total_credit": batch.total_credit,
                "total_debit": batch.total_debit,
                "status": batch.status,
                "created_at": batch.created_at.isoformat()
            })

        return sorted(result, key=lambda b: b["batch_date"], reverse=True)

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
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        trans_id = str(uuid.uuid4())
        d_date = datetime.strptime(deposit_date, "%Y-%m-%d").date()

        transaction = BankTransaction(
            transaction_id=trans_id,
            bank_account_id=bank_account_id,
            transaction_date=d_date,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            memo=memo,
            reference_number=reference_number,
            category_account_id=category_account_id
        )

        self.transactions[trans_id] = transaction

        # Update balance
        account = self.bank_accounts[bank_account_id]
        account.current_balance += amount

        return {
            "success": True,
            "transaction_id": trans_id,
            "transaction": self._transaction_to_dict(transaction)
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
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        trans_id = str(uuid.uuid4())
        w_date = datetime.strptime(withdrawal_date, "%Y-%m-%d").date()

        transaction = BankTransaction(
            transaction_id=trans_id,
            bank_account_id=bank_account_id,
            transaction_date=w_date,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=-amount,
            payee=payee,
            memo=memo,
            reference_number=reference_number,
            category_account_id=category_account_id
        )

        self.transactions[trans_id] = transaction

        # Update balance
        account = self.bank_accounts[bank_account_id]
        account.current_balance -= amount

        return {
            "success": True,
            "transaction_id": trans_id,
            "transaction": self._transaction_to_dict(transaction)
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
        if from_account_id not in self.bank_accounts:
            return {"success": False, "error": "Source account not found"}
        if to_account_id not in self.bank_accounts:
            return {"success": False, "error": "Destination account not found"}

        transfer_id = str(uuid.uuid4())
        t_date = datetime.strptime(transfer_date, "%Y-%m-%d").date()

        # Create outgoing transaction
        from_trans_id = str(uuid.uuid4())
        from_trans = BankTransaction(
            transaction_id=from_trans_id,
            bank_account_id=from_account_id,
            transaction_date=t_date,
            transaction_type=TransactionType.TRANSFER,
            amount=-amount,
            memo=f"Transfer to {self.bank_accounts[to_account_id].account_name}",
            transfer_id=transfer_id
        )
        self.transactions[from_trans_id] = from_trans

        # Create incoming transaction
        to_trans_id = str(uuid.uuid4())
        to_trans = BankTransaction(
            transaction_id=to_trans_id,
            bank_account_id=to_account_id,
            transaction_date=t_date,
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            memo=f"Transfer from {self.bank_accounts[from_account_id].account_name}",
            transfer_id=transfer_id
        )
        self.transactions[to_trans_id] = to_trans

        # Update balances
        self.bank_accounts[from_account_id].current_balance -= amount
        self.bank_accounts[to_account_id].current_balance += amount

        transfer = Transfer(
            transfer_id=transfer_id,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            transfer_date=t_date,
            amount=amount,
            memo=memo,
            from_transaction_id=from_trans_id,
            to_transaction_id=to_trans_id
        )

        self.transfers[transfer_id] = transfer

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
        if bank_account_id not in self.bank_accounts:
            return {"success": False, "error": "Bank account not found"}

        account = self.bank_accounts[bank_account_id]

        recon_id = str(uuid.uuid4())
        s_date = datetime.strptime(statement_date, "%Y-%m-%d").date()

        # Determine period start
        if account.last_reconciled_date:
            period_start = account.last_reconciled_date + timedelta(days=1)
            beginning_balance = account.last_reconciled_balance
        else:
            period_start = s_date - timedelta(days=30)
            beginning_balance = 0.0

        reconciliation = Reconciliation(
            reconciliation_id=recon_id,
            bank_account_id=bank_account_id,
            statement_date=s_date,
            statement_ending_balance=statement_ending_balance,
            period_start=period_start,
            period_end=s_date,
            beginning_balance=beginning_balance
        )

        self.reconciliations[recon_id] = reconciliation

        return {
            "success": True,
            "reconciliation_id": recon_id,
            "period_start": period_start.isoformat(),
            "period_end": s_date.isoformat(),
            "beginning_balance": beginning_balance,
            "statement_ending_balance": statement_ending_balance
        }

    def mark_transaction_cleared(self, reconciliation_id: str, transaction_id: str) -> Dict:
        """Mark a transaction as cleared in reconciliation"""
        if reconciliation_id not in self.reconciliations:
            return {"success": False, "error": "Reconciliation not found"}
        if transaction_id not in self.transactions:
            return {"success": False, "error": "Transaction not found"}

        recon = self.reconciliations[reconciliation_id]
        trans = self.transactions[transaction_id]

        trans.is_reconciled = True
        trans.reconciled_date = date.today()

        # If it's a check, update check status
        if trans.check_id and trans.check_id in self.checks:
            self.checks[trans.check_id].status = CheckStatus.CLEARED
            self.checks[trans.check_id].cleared_date = date.today()

        return {"success": True, "message": "Transaction marked as cleared"}

    def complete_reconciliation(self, reconciliation_id: str, completed_by: str) -> Dict:
        """Complete bank reconciliation"""
        if reconciliation_id not in self.reconciliations:
            return {"success": False, "error": "Reconciliation not found"}

        recon = self.reconciliations[reconciliation_id]
        account = self.bank_accounts[recon.bank_account_id]

        # Calculate cleared amounts
        cleared_deposits = 0.0
        cleared_payments = 0.0
        outstanding_deposits = []
        outstanding_checks = []

        for trans in self.transactions.values():
            if trans.bank_account_id != recon.bank_account_id:
                continue
            if trans.transaction_date > recon.statement_date:
                continue

            if trans.is_reconciled:
                if trans.amount > 0:
                    cleared_deposits += trans.amount
                else:
                    cleared_payments += abs(trans.amount)
            else:
                if trans.amount > 0:
                    outstanding_deposits.append(trans.transaction_id)
                else:
                    outstanding_checks.append(trans.transaction_id)

        # Calculate difference
        cleared_balance = recon.beginning_balance + cleared_deposits - cleared_payments
        difference = recon.statement_ending_balance - cleared_balance

        recon.cleared_deposits = cleared_deposits
        recon.cleared_payments = cleared_payments
        recon.cleared_balance = cleared_balance
        recon.outstanding_deposits = outstanding_deposits
        recon.outstanding_checks = outstanding_checks
        recon.difference = round(difference, 2)

        if abs(difference) < 0.01:
            recon.status = ReconciliationStatus.COMPLETED
            account.last_reconciled_date = recon.statement_date
            account.last_reconciled_balance = recon.statement_ending_balance
        else:
            recon.status = ReconciliationStatus.DISCREPANCY

        recon.completed_at = datetime.now()
        recon.completed_by = completed_by

        return {
            "success": True,
            "status": recon.status.value,
            "cleared_deposits": cleared_deposits,
            "cleared_payments": cleared_payments,
            "cleared_balance": cleared_balance,
            "outstanding_deposits_count": len(outstanding_deposits),
            "outstanding_checks_count": len(outstanding_checks),
            "difference": recon.difference,
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
        result = []

        for trans in self.transactions.values():
            if trans.bank_account_id != bank_account_id:
                continue
            if start_date:
                if trans.transaction_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if trans.transaction_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue
            if transaction_type and trans.transaction_type.value != transaction_type:
                continue
            if unreconciled_only and trans.is_reconciled:
                continue

            result.append(self._transaction_to_dict(trans))

        return sorted(result, key=lambda t: t["transaction_date"], reverse=True)

    def get_register(self, bank_account_id: str, start_date: str, end_date: str) -> Dict:
        """Get check register / bank register for account"""
        if bank_account_id not in self.bank_accounts:
            return {"error": "Bank account not found"}

        account = self.bank_accounts[bank_account_id]
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Get opening balance
        opening_balance = 0.0
        for trans in self.transactions.values():
            if trans.bank_account_id != bank_account_id:
                continue
            if trans.transaction_date < s_date:
                opening_balance += trans.amount

        # Get transactions in period
        entries = []
        running_balance = opening_balance

        transactions = sorted(
            [t for t in self.transactions.values()
             if t.bank_account_id == bank_account_id and s_date <= t.transaction_date <= e_date],
            key=lambda t: (t.transaction_date, t.created_at)
        )

        for trans in transactions:
            running_balance += trans.amount

            entry = {
                "date": trans.transaction_date.isoformat(),
                "type": trans.transaction_type.value,
                "reference": trans.reference_number,
                "payee": trans.payee,
                "memo": trans.memo,
                "payment": abs(trans.amount) if trans.amount < 0 else 0,
                "deposit": trans.amount if trans.amount > 0 else 0,
                "balance": round(running_balance, 2),
                "reconciled": trans.is_reconciled
            }

            # Add check details if applicable
            if trans.check_id and trans.check_id in self.checks:
                check = self.checks[trans.check_id]
                entry["check_number"] = check.check_number
                entry["check_status"] = check.status.value

            entries.append(entry)

        return {
            "account_name": account.account_name,
            "bank_name": account.bank_name,
            "period_start": start_date,
            "period_end": end_date,
            "opening_balance": round(opening_balance, 2),
            "entries": entries,
            "closing_balance": round(running_balance, 2),
            "total_deposits": sum(e["deposit"] for e in entries),
            "total_payments": sum(e["payment"] for e in entries)
        }

    # ==================== UTILITY METHODS ====================

    def _account_to_dict(self, account: BankAccount) -> Dict:
        """Convert BankAccount to dictionary"""
        return {
            "bank_account_id": account.bank_account_id,
            "account_name": account.account_name,
            "account_type": account.account_type.value,
            "bank_name": account.bank_name,
            "routing_number": account.routing_number,
            "account_number_masked": f"****{account.account_number[-4:]}",
            "check_printing_enabled": account.check_printing_enabled,
            "next_check_number": account.next_check_number,
            "check_format": account.check_format.value,
            "ach_enabled": account.ach_enabled,
            "gl_account_id": account.gl_account_id,
            "current_balance": round(account.current_balance, 2),
            "available_balance": round(account.available_balance, 2),
            "last_reconciled_date": account.last_reconciled_date.isoformat() if account.last_reconciled_date else None,
            "last_reconciled_balance": account.last_reconciled_balance,
            "is_active": account.is_active,
            "is_default": account.is_default,
            "created_at": account.created_at.isoformat()
        }

    def _check_to_dict(self, check: Check) -> Dict:
        """Convert Check to dictionary"""
        return {
            "check_id": check.check_id,
            "bank_account_id": check.bank_account_id,
            "check_number": check.check_number,
            "check_date": check.check_date.isoformat(),
            "payee_name": check.payee_name,
            "payee_address": f"{check.payee_address_line1}, {check.payee_city}, {check.payee_state} {check.payee_zip}",
            "amount": check.amount,
            "amount_formatted": f"${check.amount:,.2f}",
            "amount_in_words": check.amount_in_words,
            "memo": check.memo,
            "status": check.status.value,
            "vendor_id": check.vendor_id,
            "bills_paid": check.bills_paid,
            "printed_at": check.printed_at.isoformat() if check.printed_at else None,
            "cleared_date": check.cleared_date.isoformat() if check.cleared_date else None,
            "voided_date": check.voided_date.isoformat() if check.voided_date else None,
            "void_reason": check.void_reason,
            "requires_two_signatures": check.requires_two_signatures,
            "created_at": check.created_at.isoformat()
        }

    def _transaction_to_dict(self, trans: BankTransaction) -> Dict:
        """Convert BankTransaction to dictionary"""
        return {
            "transaction_id": trans.transaction_id,
            "bank_account_id": trans.bank_account_id,
            "transaction_date": trans.transaction_date.isoformat(),
            "transaction_type": trans.transaction_type.value,
            "amount": trans.amount,
            "payee": trans.payee,
            "memo": trans.memo,
            "reference_number": trans.reference_number,
            "category_account_id": trans.category_account_id,
            "is_reconciled": trans.is_reconciled,
            "reconciled_date": trans.reconciled_date.isoformat() if trans.reconciled_date else None,
            "check_id": trans.check_id,
            "created_at": trans.created_at.isoformat()
        }

    def get_service_summary(self) -> Dict:
        """Get GenFin Banking service summary"""
        total_balance = sum(a.current_balance for a in self.bank_accounts.values() if a.is_active)
        outstanding_checks_total = sum(
            c.amount for c in self.checks.values()
            if c.status in [CheckStatus.OUTSTANDING, CheckStatus.PRINTED]
        )

        return {
            "service": "GenFin Banking",
            "version": "1.0.0",
            "features": [
                "Bank Account Management",
                "Check Printing (Multiple Formats)",
                "ACH/Direct Deposit (NACHA)",
                "Bank Reconciliation",
                "Transaction Tracking",
                "Fund Transfers"
            ],
            "total_bank_accounts": len(self.bank_accounts),
            "active_accounts": sum(1 for a in self.bank_accounts.values() if a.is_active),
            "total_balance": round(total_balance, 2),
            "total_checks": len(self.checks),
            "outstanding_checks": sum(1 for c in self.checks.values() if c.status in [CheckStatus.OUTSTANDING, CheckStatus.PRINTED]),
            "outstanding_checks_amount": round(outstanding_checks_total, 2),
            "ach_batches": len(self.ach_batches),
            "check_formats_supported": [f.value for f in CheckFormat]
        }


# Singleton instance
genfin_banking_service = GenFinBankingService()
