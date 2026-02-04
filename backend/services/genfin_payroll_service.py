"""
GenFin Payroll Service - Employees, Pay Runs, Taxes, Direct Deposit, Tax Forms
Complete payroll management for farm operations with SQLite persistence
"""

import sqlite3
import json
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid

from .genfin_banking_service import genfin_banking_service, ACHTransactionCode


class EmployeeStatus(Enum):
    """Employee status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


class EmployeeType(Enum):
    """Employee type"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SEASONAL = "seasonal"
    CONTRACTOR = "contractor"  # 1099


class PayFrequency(Enum):
    """Pay frequency"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"


class PayType(Enum):
    """Pay type"""
    HOURLY = "hourly"
    SALARY = "salary"
    PIECE_RATE = "piece_rate"


class PayRunStatus(Enum):
    """Pay run status"""
    DRAFT = "draft"
    CALCULATED = "calculated"
    APPROVED = "approved"
    PAID = "paid"
    VOIDED = "voided"


class PayRunType(Enum):
    """Pay run type - QuickBooks-style scheduled vs unscheduled"""
    SCHEDULED = "scheduled"  # Regular scheduled payroll
    UNSCHEDULED = "unscheduled"  # Ad-hoc (bonus, correction, emergency)
    TERMINATION = "termination"  # Final paycheck for terminated employee
    BONUS = "bonus"  # Bonus-only run
    COMMISSION = "commission"  # Commission-only run


class PaymentMethod(Enum):
    """Payment method for employee"""
    CHECK = "check"
    DIRECT_DEPOSIT = "direct_deposit"
    BOTH = "both"  # Split between check and DD


class FilingStatus(Enum):
    """Federal tax filing status"""
    SINGLE = "single"
    MARRIED_FILING_JOINTLY = "married_filing_jointly"
    MARRIED_FILING_SEPARATELY = "married_filing_separately"
    HEAD_OF_HOUSEHOLD = "head_of_household"


@dataclass
class Employee:
    """Employee record"""
    employee_id: str
    employee_number: str
    first_name: str
    last_name: str
    middle_name: str = ""

    # Contact
    email: str = ""
    phone: str = ""
    mobile: str = ""

    # Address
    address_line1: str = ""
    address_line2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""

    # Employment
    employee_type: EmployeeType = EmployeeType.FULL_TIME
    department: str = ""
    job_title: str = ""
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    status: EmployeeStatus = EmployeeStatus.ACTIVE

    # Pay
    pay_type: PayType = PayType.HOURLY
    pay_rate: float = 0.0  # Hourly rate or annual salary
    pay_frequency: PayFrequency = PayFrequency.BIWEEKLY
    default_hours: float = 80.0  # Default hours per pay period

    # Tax info
    ssn: str = ""  # Encrypted in production
    date_of_birth: Optional[date] = None
    filing_status: FilingStatus = FilingStatus.SINGLE
    federal_allowances: int = 0  # W-4 allowances (old system)
    federal_additional_withholding: float = 0.0
    state_allowances: int = 0
    state_additional_withholding: float = 0.0
    is_exempt: bool = False

    # Payment
    payment_method: PaymentMethod = PaymentMethod.CHECK
    bank_routing_number: str = ""
    bank_account_number: str = ""
    bank_account_type: str = "checking"  # checking or savings

    # Workers comp
    workers_comp_code: str = ""

    # Tracking
    notes: str = ""
    is_owner: bool = False  # For S-Corp shareholders, etc.

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PayRate:
    """Pay rate record for tracking rate changes"""
    rate_id: str
    employee_id: str
    effective_date: date
    pay_type: PayType
    rate: float
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TimeEntry:
    """Time entry for employee"""
    entry_id: str
    employee_id: str
    work_date: date
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    double_time_hours: float = 0.0
    sick_hours: float = 0.0
    vacation_hours: float = 0.0
    holiday_hours: float = 0.0
    other_hours: float = 0.0
    other_hours_type: str = ""
    piece_count: float = 0.0  # For piece rate pay
    notes: str = ""
    approved: bool = False
    approved_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EarningType:
    """Earning type configuration"""
    earning_type_id: str
    code: str
    name: str
    is_taxable: bool = True
    is_overtime: bool = False
    multiplier: float = 1.0  # 1.5 for overtime, 2.0 for double time
    expense_account_id: Optional[str] = None
    is_active: bool = True


@dataclass
class DeductionType:
    """Deduction type configuration"""
    deduction_type_id: str
    code: str
    name: str
    is_pretax: bool = False  # Pre-tax reduces taxable income
    is_percentage: bool = False
    default_amount: float = 0.0
    default_percentage: float = 0.0
    max_annual_amount: Optional[float] = None
    liability_account_id: Optional[str] = None
    is_active: bool = True


@dataclass
class EmployeeDeduction:
    """Employee-specific deduction"""
    deduction_id: str
    employee_id: str
    deduction_type_id: str
    amount: float = 0.0
    percentage: float = 0.0
    is_active: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@dataclass
class PayRunLine:
    """Single employee's pay in a pay run"""
    line_id: str
    employee_id: str

    # Hours
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    double_time_hours: float = 0.0
    sick_hours: float = 0.0
    vacation_hours: float = 0.0
    holiday_hours: float = 0.0

    # Earnings
    regular_pay: float = 0.0
    overtime_pay: float = 0.0
    double_time_pay: float = 0.0
    sick_pay: float = 0.0
    vacation_pay: float = 0.0
    holiday_pay: float = 0.0
    bonus: float = 0.0
    commission: float = 0.0
    other_earnings: float = 0.0
    gross_pay: float = 0.0

    # Taxes
    federal_income_tax: float = 0.0
    state_income_tax: float = 0.0
    local_income_tax: float = 0.0
    social_security_employee: float = 0.0
    medicare_employee: float = 0.0
    additional_medicare: float = 0.0

    # Employer taxes
    social_security_employer: float = 0.0
    medicare_employer: float = 0.0
    futa: float = 0.0
    suta: float = 0.0

    # Deductions
    deductions: List[Dict] = field(default_factory=list)
    total_deductions: float = 0.0

    # Net
    net_pay: float = 0.0

    # Payment
    payment_method: PaymentMethod = PaymentMethod.CHECK
    check_id: Optional[str] = None
    direct_deposit_amount: float = 0.0


@dataclass
class PayRun:
    """Payroll run"""
    pay_run_id: str
    pay_run_number: int
    pay_period_start: date
    pay_period_end: date
    pay_date: date
    bank_account_id: str

    # QuickBooks-style payroll type
    pay_run_type: PayRunType = PayRunType.SCHEDULED
    pay_schedule_id: Optional[str] = None  # Link to schedule for scheduled runs

    lines: List[PayRunLine] = field(default_factory=list)

    # Totals
    total_gross: float = 0.0
    total_taxes: float = 0.0
    total_deductions: float = 0.0
    total_net: float = 0.0
    total_employer_taxes: float = 0.0

    status: PayRunStatus = PayRunStatus.DRAFT
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    memo: str = ""
    journal_entry_id: Optional[str] = None
    ach_batch_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaxPayment:
    """Tax payment record"""
    payment_id: str
    tax_type: str  # federal, state, futa, suta, etc.
    period_start: date
    period_end: date
    payment_date: date
    amount: float
    confirmation_number: str = ""
    memo: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PaySchedule:
    """
    Pay Schedule - QuickBooks-style payroll scheduling

    Defines when employees get paid:
    - Frequency (weekly, biweekly, semi-monthly, monthly)
    - Pay day (day of week for weekly/biweekly, day of month for monthly)
    - Which employees are on this schedule
    - Next scheduled run date
    """
    schedule_id: str
    name: str  # e.g., "Weekly Field Crew", "Monthly Salaried"
    frequency: PayFrequency

    # For weekly/biweekly - day of week (0=Monday, 6=Sunday)
    pay_day_of_week: int = 4  # Friday

    # For monthly/semi-monthly - day(s) of month
    pay_day_of_month: int = 15  # 15th
    second_pay_day: int = 0  # For semi-monthly (e.g., 15th and last day)

    # Scheduling
    next_pay_period_start: Optional[date] = None
    next_pay_period_end: Optional[date] = None
    next_pay_date: Optional[date] = None

    # Track employees on this schedule
    employee_ids: List[str] = field(default_factory=list)

    # Settings
    is_active: bool = True
    auto_calculate: bool = False  # Auto-calculate when run starts
    reminder_days_before: int = 3  # Days before pay date to send reminder

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# 2024 Federal Tax Brackets
FEDERAL_TAX_BRACKETS_2024 = {
    FilingStatus.SINGLE: [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37)
    ],
    FilingStatus.MARRIED_FILING_JOINTLY: [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float('inf'), 0.37)
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (16550, 0.10),
        (63100, 0.12),
        (100500, 0.22),
        (191950, 0.24),
        (243700, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37)
    ]
}

# Social Security / Medicare rates
SOCIAL_SECURITY_RATE = 0.062  # 6.2%
SOCIAL_SECURITY_WAGE_BASE = 168600  # 2024 wage base
MEDICARE_RATE = 0.0145  # 1.45%
ADDITIONAL_MEDICARE_RATE = 0.009  # 0.9% on wages over $200k
ADDITIONAL_MEDICARE_THRESHOLD = 200000

# FUTA / SUTA
FUTA_RATE = 0.006  # 0.6% after credit
FUTA_WAGE_BASE = 7000

# Standard deduction for tax calculation
STANDARD_DEDUCTION_2024 = {
    FilingStatus.SINGLE: 14600,
    FilingStatus.MARRIED_FILING_JOINTLY: 29200,
    FilingStatus.HEAD_OF_HOUSEHOLD: 21900
}


class GenFinPayrollService:
    """
    GenFin Payroll Service with SQLite persistence

    Complete payroll functionality:
    - Employee management
    - Time tracking
    - Pay runs with tax calculations
    - Direct deposit via ACH
    - Check printing
    - Tax payments
    - Year-end forms (W-2, 1099)
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
        self._initialize_defaults()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Employees table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_employees (
                    employee_id TEXT PRIMARY KEY,
                    employee_number TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    middle_name TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    mobile TEXT DEFAULT '',
                    address_line1 TEXT DEFAULT '',
                    address_line2 TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    state TEXT DEFAULT '',
                    zip_code TEXT DEFAULT '',
                    employee_type TEXT DEFAULT 'full_time',
                    department TEXT DEFAULT '',
                    job_title TEXT DEFAULT '',
                    hire_date TEXT,
                    termination_date TEXT,
                    status TEXT DEFAULT 'active',
                    pay_type TEXT DEFAULT 'hourly',
                    pay_rate REAL DEFAULT 0.0,
                    pay_frequency TEXT DEFAULT 'biweekly',
                    default_hours REAL DEFAULT 80.0,
                    ssn TEXT DEFAULT '',
                    date_of_birth TEXT,
                    filing_status TEXT DEFAULT 'single',
                    federal_allowances INTEGER DEFAULT 0,
                    federal_additional_withholding REAL DEFAULT 0.0,
                    state_allowances INTEGER DEFAULT 0,
                    state_additional_withholding REAL DEFAULT 0.0,
                    is_exempt INTEGER DEFAULT 0,
                    payment_method TEXT DEFAULT 'check',
                    bank_routing_number TEXT DEFAULT '',
                    bank_account_number TEXT DEFAULT '',
                    bank_account_type TEXT DEFAULT 'checking',
                    workers_comp_code TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    is_owner INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Pay rates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_pay_rates (
                    rate_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    pay_type TEXT NOT NULL,
                    rate REAL NOT NULL,
                    reason TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES genfin_employees(employee_id)
                )
            """)

            # Time entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_time_entries (
                    entry_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    work_date TEXT NOT NULL,
                    regular_hours REAL DEFAULT 0.0,
                    overtime_hours REAL DEFAULT 0.0,
                    double_time_hours REAL DEFAULT 0.0,
                    sick_hours REAL DEFAULT 0.0,
                    vacation_hours REAL DEFAULT 0.0,
                    holiday_hours REAL DEFAULT 0.0,
                    other_hours REAL DEFAULT 0.0,
                    other_hours_type TEXT DEFAULT '',
                    piece_count REAL DEFAULT 0.0,
                    notes TEXT DEFAULT '',
                    approved INTEGER DEFAULT 0,
                    approved_by TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES genfin_employees(employee_id)
                )
            """)

            # Earning types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_earning_types (
                    earning_type_id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    is_taxable INTEGER DEFAULT 1,
                    is_overtime INTEGER DEFAULT 0,
                    multiplier REAL DEFAULT 1.0,
                    expense_account_id TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Deduction types table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_deduction_types (
                    deduction_type_id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    is_pretax INTEGER DEFAULT 0,
                    is_percentage INTEGER DEFAULT 0,
                    default_amount REAL DEFAULT 0.0,
                    default_percentage REAL DEFAULT 0.0,
                    max_annual_amount REAL,
                    liability_account_id TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Employee deductions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_employee_deductions (
                    deduction_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    deduction_type_id TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    percentage REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    start_date TEXT,
                    end_date TEXT,
                    FOREIGN KEY (employee_id) REFERENCES genfin_employees(employee_id),
                    FOREIGN KEY (deduction_type_id) REFERENCES genfin_deduction_types(deduction_type_id)
                )
            """)

            # Pay runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_pay_runs (
                    pay_run_id TEXT PRIMARY KEY,
                    pay_run_number INTEGER NOT NULL,
                    pay_period_start TEXT NOT NULL,
                    pay_period_end TEXT NOT NULL,
                    pay_date TEXT NOT NULL,
                    bank_account_id TEXT NOT NULL,
                    pay_run_type TEXT DEFAULT 'scheduled',
                    pay_schedule_id TEXT,
                    total_gross REAL DEFAULT 0.0,
                    total_taxes REAL DEFAULT 0.0,
                    total_deductions REAL DEFAULT 0.0,
                    total_net REAL DEFAULT 0.0,
                    total_employer_taxes REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'draft',
                    approved_by TEXT DEFAULT '',
                    approved_at TEXT,
                    paid_at TEXT,
                    memo TEXT DEFAULT '',
                    journal_entry_id TEXT,
                    ach_batch_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Pay run lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_pay_run_lines (
                    line_id TEXT PRIMARY KEY,
                    pay_run_id TEXT NOT NULL,
                    employee_id TEXT NOT NULL,
                    regular_hours REAL DEFAULT 0.0,
                    overtime_hours REAL DEFAULT 0.0,
                    double_time_hours REAL DEFAULT 0.0,
                    sick_hours REAL DEFAULT 0.0,
                    vacation_hours REAL DEFAULT 0.0,
                    holiday_hours REAL DEFAULT 0.0,
                    regular_pay REAL DEFAULT 0.0,
                    overtime_pay REAL DEFAULT 0.0,
                    double_time_pay REAL DEFAULT 0.0,
                    sick_pay REAL DEFAULT 0.0,
                    vacation_pay REAL DEFAULT 0.0,
                    holiday_pay REAL DEFAULT 0.0,
                    bonus REAL DEFAULT 0.0,
                    commission REAL DEFAULT 0.0,
                    other_earnings REAL DEFAULT 0.0,
                    gross_pay REAL DEFAULT 0.0,
                    federal_income_tax REAL DEFAULT 0.0,
                    state_income_tax REAL DEFAULT 0.0,
                    local_income_tax REAL DEFAULT 0.0,
                    social_security_employee REAL DEFAULT 0.0,
                    medicare_employee REAL DEFAULT 0.0,
                    additional_medicare REAL DEFAULT 0.0,
                    social_security_employer REAL DEFAULT 0.0,
                    medicare_employer REAL DEFAULT 0.0,
                    futa REAL DEFAULT 0.0,
                    suta REAL DEFAULT 0.0,
                    deductions_json TEXT DEFAULT '[]',
                    total_deductions REAL DEFAULT 0.0,
                    net_pay REAL DEFAULT 0.0,
                    payment_method TEXT DEFAULT 'check',
                    check_id TEXT,
                    direct_deposit_amount REAL DEFAULT 0.0,
                    FOREIGN KEY (pay_run_id) REFERENCES genfin_pay_runs(pay_run_id),
                    FOREIGN KEY (employee_id) REFERENCES genfin_employees(employee_id)
                )
            """)

            # Tax payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_tax_payments (
                    payment_id TEXT PRIMARY KEY,
                    tax_type TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    payment_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    confirmation_number TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # Pay schedules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_pay_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    pay_day_of_week INTEGER DEFAULT 4,
                    pay_day_of_month INTEGER DEFAULT 15,
                    second_pay_day INTEGER DEFAULT 0,
                    next_pay_period_start TEXT,
                    next_pay_period_end TEXT,
                    next_pay_date TEXT,
                    employee_ids_json TEXT DEFAULT '[]',
                    is_active INTEGER DEFAULT 1,
                    auto_calculate INTEGER DEFAULT 0,
                    reminder_days_before INTEGER DEFAULT 3,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Payroll settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_payroll_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            conn.commit()

    def _initialize_defaults(self):
        """Initialize default earning types, deduction types, and pay schedules"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if defaults already exist
            cursor.execute("SELECT COUNT(*) FROM genfin_earning_types")
            if cursor.fetchone()[0] == 0:
                self._initialize_earning_types()

            cursor.execute("SELECT COUNT(*) FROM genfin_deduction_types")
            if cursor.fetchone()[0] == 0:
                self._initialize_deduction_types()

            cursor.execute("SELECT COUNT(*) FROM genfin_pay_schedules")
            if cursor.fetchone()[0] == 0:
                self._initialize_pay_schedules()

            # Initialize settings if not exists
            cursor.execute("SELECT COUNT(*) FROM genfin_payroll_settings WHERE key = 'next_employee_number'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO genfin_payroll_settings (key, value) VALUES (?, ?)",
                             ("next_employee_number", "1001"))
                cursor.execute("INSERT INTO genfin_payroll_settings (key, value) VALUES (?, ?)",
                             ("next_pay_run_number", "1"))
                conn.commit()

    def _get_next_number(self, key: str) -> int:
        """Get and increment a sequence number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM genfin_payroll_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            current = int(row['value']) if row else 1
            cursor.execute("UPDATE genfin_payroll_settings SET value = ? WHERE key = ?",
                         (str(current + 1), key))
            conn.commit()
            return current

    def _initialize_earning_types(self):
        """Set up default earning types"""
        defaults = [
            ("REG", "Regular Pay", True, False, 1.0),
            ("OT", "Overtime Pay", True, True, 1.5),
            ("DT", "Double Time Pay", True, True, 2.0),
            ("HOL", "Holiday Pay", True, False, 1.0),
            ("VAC", "Vacation Pay", True, False, 1.0),
            ("SICK", "Sick Pay", True, False, 1.0),
            ("BONUS", "Bonus", True, False, 1.0),
            ("COMM", "Commission", True, False, 1.0),
            ("TIP", "Tips", True, False, 1.0),
            ("REIMB", "Reimbursement", False, False, 1.0),
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for code, name, taxable, is_ot, mult in defaults:
                et_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_earning_types
                    (earning_type_id, code, name, is_taxable, is_overtime, multiplier, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (et_id, code, name, 1 if taxable else 0, 1 if is_ot else 0, mult))
            conn.commit()

    def _initialize_deduction_types(self):
        """Set up default deduction types"""
        defaults = [
            ("401K", "401(k) Contribution", True, True, 0, 6.0, 23000),
            ("HSA", "HSA Contribution", True, False, 0, 0, 4150),
            ("HEALTH", "Health Insurance", True, False, 0, 0, None),
            ("DENTAL", "Dental Insurance", True, False, 0, 0, None),
            ("VISION", "Vision Insurance", True, False, 0, 0, None),
            ("LIFE", "Life Insurance", False, False, 0, 0, None),
            ("GARN", "Garnishment", False, False, 0, 0, None),
            ("CHSUP", "Child Support", False, False, 0, 0, None),
            ("LOAN", "Employee Loan Repayment", False, False, 0, 0, None),
            ("UNION", "Union Dues", False, False, 0, 0, None),
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for code, name, pretax, is_pct, amt, pct, max_amt in defaults:
                dt_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_deduction_types
                    (deduction_type_id, code, name, is_pretax, is_percentage,
                     default_amount, default_percentage, max_annual_amount, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (dt_id, code, name, 1 if pretax else 0, 1 if is_pct else 0,
                      amt, pct, max_amt))
            conn.commit()

    def _initialize_pay_schedules(self):
        """Set up default pay schedules - QuickBooks style"""
        now = datetime.now(timezone.utc).isoformat()

        schedules = [
            ("Weekly", PayFrequency.WEEKLY, 4, 15, 0),
            ("Every Other Week", PayFrequency.BIWEEKLY, 4, 15, 0),
            ("Twice a Month", PayFrequency.SEMIMONTHLY, 4, 15, 0),
            ("Monthly", PayFrequency.MONTHLY, 4, 1, 0),
        ]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for name, freq, dow, dom, second in schedules:
                schedule_id = str(uuid.uuid4())
                next_start = self._calculate_next_period_start(freq)
                next_end = self._calculate_next_period_end(freq)
                next_pay = self._calculate_next_pay_date(freq, dow, dom)

                cursor.execute("""
                    INSERT INTO genfin_pay_schedules
                    (schedule_id, name, frequency, pay_day_of_week, pay_day_of_month,
                     second_pay_day, next_pay_period_start, next_pay_period_end,
                     next_pay_date, employee_ids_json, is_active, auto_calculate,
                     reminder_days_before, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', 1, 0, 3, ?, ?)
                """, (schedule_id, name, freq.value, dow, dom, second,
                      next_start.isoformat() if next_start else None,
                      next_end.isoformat() if next_end else None,
                      next_pay.isoformat() if next_pay else None,
                      now, now))
            conn.commit()

    def _calculate_next_period_start(self, frequency: PayFrequency) -> date:
        """Calculate the next pay period start date"""
        today = date.today()

        if frequency == PayFrequency.WEEKLY:
            days_since_monday = today.weekday()
            return today - timedelta(days=days_since_monday)

        elif frequency == PayFrequency.BIWEEKLY:
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            week_num = week_start.isocalendar()[1]
            if week_num % 2 == 1:
                week_start -= timedelta(days=7)
            return week_start

        elif frequency == PayFrequency.SEMIMONTHLY:
            if today.day <= 15:
                return date(today.year, today.month, 1)
            else:
                return date(today.year, today.month, 16)

        elif frequency == PayFrequency.MONTHLY:
            return date(today.year, today.month, 1)

        return today

    def _calculate_next_period_end(self, frequency: PayFrequency) -> date:
        """Calculate the next pay period end date"""
        start = self._calculate_next_period_start(frequency)

        if frequency == PayFrequency.WEEKLY:
            return start + timedelta(days=6)

        elif frequency == PayFrequency.BIWEEKLY:
            return start + timedelta(days=13)

        elif frequency == PayFrequency.SEMIMONTHLY:
            if start.day == 1:
                return date(start.year, start.month, 15)
            else:
                if start.month == 12:
                    return date(start.year + 1, 1, 1) - timedelta(days=1)
                else:
                    return date(start.year, start.month + 1, 1) - timedelta(days=1)

        elif frequency == PayFrequency.MONTHLY:
            if start.month == 12:
                return date(start.year + 1, 1, 1) - timedelta(days=1)
            else:
                return date(start.year, start.month + 1, 1) - timedelta(days=1)

        return start

    def _calculate_next_pay_date(self, frequency: PayFrequency, pay_day_of_week: int = 4, pay_day_of_month: int = 15) -> date:
        """Calculate the next pay date"""
        today = date.today()

        if frequency in [PayFrequency.WEEKLY, PayFrequency.BIWEEKLY]:
            days_ahead = pay_day_of_week - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            if frequency == PayFrequency.BIWEEKLY:
                week_num = today.isocalendar()[1]
                if week_num % 2 == 1:
                    days_ahead += 7
            return today + timedelta(days=days_ahead)

        elif frequency == PayFrequency.SEMIMONTHLY:
            if today.day <= 15:
                return date(today.year, today.month, 15)
            else:
                if today.month == 12:
                    return date(today.year, 12, 31)
                else:
                    return date(today.year, today.month + 1, 1) - timedelta(days=1)

        elif frequency == PayFrequency.MONTHLY:
            if today.day <= pay_day_of_month:
                return date(today.year, today.month, pay_day_of_month)
            else:
                if today.month == 12:
                    return date(today.year + 1, 1, pay_day_of_month)
                else:
                    return date(today.year, today.month + 1, pay_day_of_month)

        return today

    # ==================== PAY SCHEDULE MANAGEMENT ====================

    def create_pay_schedule(
        self,
        name: str,
        frequency: str,
        pay_day_of_week: int = 4,
        pay_day_of_month: int = 15,
        second_pay_day: int = 0
    ) -> Dict:
        """Create a new pay schedule"""
        schedule_id = str(uuid.uuid4())
        freq = PayFrequency(frequency)
        now = datetime.now(timezone.utc).isoformat()

        next_start = self._calculate_next_period_start(freq)
        next_end = self._calculate_next_period_end(freq)
        next_pay = self._calculate_next_pay_date(freq, pay_day_of_week, pay_day_of_month)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_pay_schedules
                (schedule_id, name, frequency, pay_day_of_week, pay_day_of_month,
                 second_pay_day, next_pay_period_start, next_pay_period_end,
                 next_pay_date, employee_ids_json, is_active, auto_calculate,
                 reminder_days_before, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', 1, 0, 3, ?, ?)
            """, (schedule_id, name, frequency, pay_day_of_week, pay_day_of_month,
                  second_pay_day,
                  next_start.isoformat() if next_start else None,
                  next_end.isoformat() if next_end else None,
                  next_pay.isoformat() if next_pay else None,
                  now, now))
            conn.commit()

        return {
            "id": schedule_id,
            "schedule_id": schedule_id,
            "name": name,
            "frequency": frequency,
            "next_pay_date": next_pay
        }

    def assign_employee_to_schedule(self, employee_id: str, schedule_id: str) -> Dict:
        """Assign an employee to a pay schedule"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check employee exists
            cursor.execute("SELECT employee_id FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                         (employee_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Employee not found"}

            # Check schedule exists
            cursor.execute("SELECT schedule_id, employee_ids_json, frequency FROM genfin_pay_schedules WHERE schedule_id = ? AND is_active = 1",
                         (schedule_id,))
            schedule_row = cursor.fetchone()
            if not schedule_row:
                return {"success": False, "error": "Pay schedule not found"}

            # Remove from all other schedules
            cursor.execute("SELECT schedule_id, employee_ids_json FROM genfin_pay_schedules WHERE is_active = 1")
            for row in cursor.fetchall():
                emp_ids = json.loads(row['employee_ids_json'] or '[]')
                if employee_id in emp_ids:
                    emp_ids.remove(employee_id)
                    cursor.execute("UPDATE genfin_pay_schedules SET employee_ids_json = ?, updated_at = ? WHERE schedule_id = ?",
                                 (json.dumps(emp_ids), datetime.now(timezone.utc).isoformat(), row['schedule_id']))

            # Add to new schedule
            emp_ids = json.loads(schedule_row['employee_ids_json'] or '[]')
            if employee_id not in emp_ids:
                emp_ids.append(employee_id)
            cursor.execute("UPDATE genfin_pay_schedules SET employee_ids_json = ?, updated_at = ? WHERE schedule_id = ?",
                         (json.dumps(emp_ids), datetime.now(timezone.utc).isoformat(), schedule_id))

            # Update employee's pay frequency
            cursor.execute("UPDATE genfin_employees SET pay_frequency = ?, updated_at = ? WHERE employee_id = ?",
                         (schedule_row['frequency'], datetime.now(timezone.utc).isoformat(), employee_id))

            conn.commit()

        return {
            "success": True,
            "message": "Employee assigned to schedule"
        }

    def get_pay_schedule(self, schedule_id: str) -> Optional[Dict]:
        """Get a pay schedule by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_pay_schedules WHERE schedule_id = ? AND is_active = 1",
                         (schedule_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_schedule(row)

    def list_pay_schedules(self, active_only: bool = True) -> Dict:
        """List all pay schedules"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM genfin_pay_schedules WHERE is_active = 1")
            else:
                cursor.execute("SELECT * FROM genfin_pay_schedules")

            result = []
            for row in cursor.fetchall():
                sched_dict = self._row_to_schedule(row)
                sched_dict["id"] = row['schedule_id']
                sched_dict["frequency"] = row['frequency']
                sched_dict["next_pay_date"] = datetime.strptime(row['next_pay_date'], "%Y-%m-%d").date() if row['next_pay_date'] else None
                result.append(sched_dict)

        return {"schedules": result, "total": len(result)}

    def get_scheduled_payrolls_due(self, days_ahead: int = 7) -> List[Dict]:
        """Get list of scheduled payrolls that are due or upcoming within specified days"""
        today = date.today()
        due_payrolls = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_pay_schedules WHERE is_active = 1")

            for row in cursor.fetchall():
                emp_ids = json.loads(row['employee_ids_json'] or '[]')
                if not emp_ids:
                    continue

                next_pay = datetime.strptime(row['next_pay_date'], "%Y-%m-%d").date() if row['next_pay_date'] else None
                if not next_pay:
                    continue

                days_until = (next_pay - today).days

                if days_until <= days_ahead:
                    due_payrolls.append({
                        "schedule_id": row['schedule_id'],
                        "schedule_name": row['name'],
                        "frequency": row['frequency'],
                        "pay_period_start": row['next_pay_period_start'],
                        "pay_period_end": row['next_pay_period_end'],
                        "pay_date": row['next_pay_date'],
                        "days_until_pay_date": days_until,
                        "employee_count": len(emp_ids),
                        "status": "overdue" if days_until < 0 else "due" if days_until == 0 else "upcoming"
                    })

        return sorted(due_payrolls, key=lambda p: p["days_until_pay_date"])

    def _row_to_schedule(self, row: sqlite3.Row) -> Dict:
        """Convert schedule row to dictionary"""
        emp_ids = json.loads(row['employee_ids_json'] or '[]')
        return {
            "schedule_id": row['schedule_id'],
            "name": row['name'],
            "frequency": row['frequency'],
            "pay_day_of_week": row['pay_day_of_week'],
            "pay_day_of_month": row['pay_day_of_month'],
            "second_pay_day": row['second_pay_day'],
            "next_pay_period_start": row['next_pay_period_start'],
            "next_pay_period_end": row['next_pay_period_end'],
            "next_pay_date": row['next_pay_date'],
            "employee_count": len(emp_ids),
            "employee_ids": emp_ids,
            "is_active": bool(row['is_active']),
            "auto_calculate": bool(row['auto_calculate']),
            "reminder_days_before": row['reminder_days_before']
        }

    def _advance_schedule(self, schedule_id: str):
        """Advance a pay schedule to the next period after payroll is run"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_pay_schedules WHERE schedule_id = ?", (schedule_id,))
            row = cursor.fetchone()
            if not row:
                return

            frequency = PayFrequency(row['frequency'])
            next_start = datetime.strptime(row['next_pay_period_start'], "%Y-%m-%d").date() if row['next_pay_period_start'] else None
            next_end = datetime.strptime(row['next_pay_period_end'], "%Y-%m-%d").date() if row['next_pay_period_end'] else None
            next_pay = datetime.strptime(row['next_pay_date'], "%Y-%m-%d").date() if row['next_pay_date'] else None

            if not next_start or not next_end or not next_pay:
                return

            # Calculate next period based on frequency
            if frequency == PayFrequency.WEEKLY:
                next_start += timedelta(days=7)
                next_end += timedelta(days=7)
                next_pay += timedelta(days=7)

            elif frequency == PayFrequency.BIWEEKLY:
                next_start += timedelta(days=14)
                next_end += timedelta(days=14)
                next_pay += timedelta(days=14)

            elif frequency == PayFrequency.SEMIMONTHLY:
                if next_end.day <= 15:
                    next_start = date(next_end.year, next_end.month, 16)
                    if next_end.month == 12:
                        next_month = date(next_end.year + 1, 1, 1)
                    else:
                        next_month = date(next_end.year, next_end.month + 1, 1)
                    next_end = next_month - timedelta(days=1)
                    next_pay = next_end
                else:
                    if next_end.month == 12:
                        next_month = 1
                        next_year = next_end.year + 1
                    else:
                        next_month = next_end.month + 1
                        next_year = next_end.year
                    next_start = date(next_year, next_month, 1)
                    next_end = date(next_year, next_month, 15)
                    next_pay = next_end

            elif frequency == PayFrequency.MONTHLY:
                if next_start.month == 12:
                    next_start = date(next_start.year + 1, 1, 1)
                    next_end = date(next_start.year + 1, 1, 31)
                    next_pay = date(next_start.year + 1, 1, row['pay_day_of_month'])
                else:
                    next_start = date(next_start.year, next_start.month + 1, 1)
                    if next_start.month + 1 == 12:
                        next_end = date(next_start.year, 12, 31)
                    else:
                        next_end = date(next_start.year, next_start.month + 2, 1) - timedelta(days=1)
                    next_pay = date(next_start.year, next_start.month + 1, min(row['pay_day_of_month'], 28))

            cursor.execute("""
                UPDATE genfin_pay_schedules
                SET next_pay_period_start = ?, next_pay_period_end = ?, next_pay_date = ?, updated_at = ?
                WHERE schedule_id = ?
            """, (next_start.isoformat(), next_end.isoformat(), next_pay.isoformat(),
                  datetime.now(timezone.utc).isoformat(), schedule_id))
            conn.commit()

    # ==================== EMPLOYEE MANAGEMENT ====================

    def create_employee(
        self,
        first_name: str,
        last_name: str,
        middle_name: str = "",
        email: str = "",
        phone: str = "",
        address_line1: str = "",
        city: str = "",
        state: str = "",
        zip_code: str = "",
        employee_type: str = "full_time",
        department: str = "",
        job_title: str = "",
        hire_date: Optional[str] = None,
        pay_type: str = "hourly",
        pay_rate: float = 0.0,
        pay_frequency: str = "biweekly",
        pay_schedule_id: Optional[str] = None,
        default_hours: float = 80.0,
        ssn: str = "",
        date_of_birth: Optional[str] = None,
        filing_status: str = "single",
        federal_allowances: int = 0,
        federal_additional_withholding: float = 0.0,
        state_allowances: int = 0,
        payment_method: str = "check",
        bank_routing_number: str = "",
        bank_account_number: str = "",
        bank_account_type: str = "checking",
        is_owner: bool = False
    ) -> Dict:
        """Create a new employee"""
        employee_id = str(uuid.uuid4())
        emp_number = self._get_next_number("next_employee_number")
        employee_number = f"EMP-{emp_number}"

        h_date = hire_date if hire_date else date.today().isoformat()
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_employees
                (employee_id, employee_number, first_name, last_name, middle_name,
                 email, phone, address_line1, city, state, zip_code,
                 employee_type, department, job_title, hire_date,
                 status, pay_type, pay_rate, pay_frequency, default_hours,
                 ssn, date_of_birth, filing_status, federal_allowances,
                 federal_additional_withholding, state_allowances,
                 payment_method, bank_routing_number, bank_account_number,
                 bank_account_type, is_owner, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active',
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (employee_id, employee_number, first_name, last_name, middle_name,
                  email, phone, address_line1, city, state, zip_code,
                  employee_type, department, job_title, h_date,
                  pay_type, pay_rate, pay_frequency, default_hours,
                  ssn, date_of_birth, filing_status, federal_allowances,
                  federal_additional_withholding, state_allowances,
                  payment_method, bank_routing_number, bank_account_number,
                  bank_account_type, 1 if is_owner else 0, now, now))

            # Create initial pay rate record
            rate_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO genfin_pay_rates
                (rate_id, employee_id, effective_date, pay_type, rate, reason, created_at)
                VALUES (?, ?, ?, ?, ?, 'Initial rate', ?)
            """, (rate_id, employee_id, h_date, pay_type, pay_rate, now))

            conn.commit()

        # Assign to pay schedule if provided
        if pay_schedule_id:
            self.assign_employee_to_schedule(employee_id, pay_schedule_id)

        # Get employee for return
        emp = self.get_employee(employee_id)
        if emp:
            # Get count for numeric ID
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM genfin_employees WHERE is_active = 1")
                emp["id"] = cursor.fetchone()[0]
        return emp

    def update_employee(self, employee_id: str, **kwargs) -> Dict:
        """Update employee information"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                         (employee_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Employee not found"}

            # Handle pay rate change
            if "pay_rate" in kwargs and kwargs["pay_rate"] != row['pay_rate']:
                rate_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_pay_rates
                    (rate_id, employee_id, effective_date, pay_type, rate, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (rate_id, employee_id, date.today().isoformat(),
                      kwargs.get("pay_type", row['pay_type']),
                      kwargs["pay_rate"],
                      kwargs.get("rate_change_reason", "Rate change"),
                      datetime.now(timezone.utc).isoformat()))

            # Handle pay schedule change
            if "pay_schedule_id" in kwargs:
                new_schedule_id = kwargs.pop("pay_schedule_id")
                if new_schedule_id:
                    self.assign_employee_to_schedule(employee_id, new_schedule_id)

            # Build update query
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None and key not in ['rate_change_reason']:
                    if key in ['hire_date', 'termination_date', 'date_of_birth']:
                        if isinstance(value, str):
                            updates.append(f"{key} = ?")
                            values.append(value)
                    elif key == 'is_owner':
                        updates.append(f"{key} = ?")
                        values.append(1 if value else 0)
                    else:
                        updates.append(f"{key} = ?")
                        values.append(value)

            if updates:
                updates.append("updated_at = ?")
                values.append(datetime.now(timezone.utc).isoformat())
                values.append(employee_id)

                cursor.execute(f"""
                    UPDATE genfin_employees
                    SET {', '.join(updates)}
                    WHERE employee_id = ?
                """, values)
                conn.commit()

        return {
            "success": True,
            "employee": self.get_employee(employee_id)
        }

    def terminate_employee(self, employee_id: str, termination_date: str, reason: str = "") -> Dict:
        """Terminate an employee"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                         (employee_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Employee not found"}

            notes = row['notes'] or ""
            if reason:
                notes = f"{notes}\nTerminated: {reason}"

            cursor.execute("""
                UPDATE genfin_employees
                SET status = 'terminated', termination_date = ?, notes = ?, updated_at = ?
                WHERE employee_id = ?
            """, (termination_date, notes, datetime.now(timezone.utc).isoformat(), employee_id))
            conn.commit()

        return {
            "success": True,
            "employee": self.get_employee(employee_id)
        }

    def get_employee(self, employee_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ?", (employee_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_employee(row)

    def list_employees(
        self,
        status: Optional[str] = None,
        employee_type: Optional[str] = None,
        department: Optional[str] = None,
        active_only: bool = True
    ) -> Dict:
        """List employees with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_employees WHERE is_active = 1"
            params = []

            if active_only:
                query += " AND status = 'active'"
            elif status:
                query += " AND status = ?"
                params.append(status)

            if employee_type:
                query += " AND employee_type = ?"
                params.append(employee_type)

            if department:
                query += " AND department = ?"
                params.append(department)

            query += " ORDER BY last_name, first_name"

            cursor.execute(query, params)
            result = [self._row_to_employee(row) for row in cursor.fetchall()]

        return {"employees": result, "total": len(result)}

    def _row_to_employee(self, row: sqlite3.Row) -> Dict:
        """Convert employee row to dictionary"""
        # Find which pay schedule this employee is assigned to
        pay_schedule_id = None
        pay_schedule_name = None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT schedule_id, name, employee_ids_json FROM genfin_pay_schedules WHERE is_active = 1")
            for sched_row in cursor.fetchall():
                emp_ids = json.loads(sched_row['employee_ids_json'] or '[]')
                if row['employee_id'] in emp_ids:
                    pay_schedule_id = sched_row['schedule_id']
                    pay_schedule_name = sched_row['name']
                    break

        return {
            "employee_id": row['employee_id'],
            "employee_number": row['employee_number'],
            "first_name": row['first_name'],
            "last_name": row['last_name'],
            "middle_name": row['middle_name'] or "",
            "full_name": f"{row['first_name']} {row['last_name']}",
            "email": row['email'] or "",
            "phone": row['phone'] or "",
            "address_line1": row['address_line1'] or "",
            "city": row['city'] or "",
            "state": row['state'] or "",
            "zip_code": row['zip_code'] or "",
            "address": f"{row['address_line1'] or ''}, {row['city'] or ''}, {row['state'] or ''} {row['zip_code'] or ''}",
            "employee_type": row['employee_type'],
            "department": row['department'] or "",
            "job_title": row['job_title'] or "",
            "hire_date": row['hire_date'],
            "status": row['status'],
            "pay_type": row['pay_type'],
            "pay_rate": row['pay_rate'],
            "pay_frequency": row['pay_frequency'],
            "pay_schedule_id": pay_schedule_id,
            "pay_schedule_name": pay_schedule_name,
            "default_hours": row['default_hours'],
            "filing_status": row['filing_status'],
            "federal_allowances": row['federal_allowances'],
            "federal_additional_withholding": row['federal_additional_withholding'],
            "state_allowances": row['state_allowances'],
            "payment_method": row['payment_method'],
            "bank_routing_number": row['bank_routing_number'] or "",
            "bank_account_number": row['bank_account_number'][-4:] if row['bank_account_number'] else "",
            "bank_account_type": row['bank_account_type'] or "checking",
            "has_direct_deposit": row['payment_method'] in ['direct_deposit', 'both'],
            "is_owner": bool(row['is_owner']),
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    # ==================== DEDUCTIONS ====================

    def add_employee_deduction(
        self,
        employee_id: str,
        deduction_type_id: str,
        amount: float = 0.0,
        percentage: float = 0.0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Add a deduction to an employee"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT employee_id FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                         (employee_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Employee not found"}

            cursor.execute("SELECT deduction_type_id FROM genfin_deduction_types WHERE deduction_type_id = ? AND is_active = 1",
                         (deduction_type_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Deduction type not found"}

            deduction_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO genfin_employee_deductions
                (deduction_id, employee_id, deduction_type_id, amount, percentage,
                 is_active, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (deduction_id, employee_id, deduction_type_id, amount, percentage,
                  start_date, end_date))
            conn.commit()

        return {
            "success": True,
            "deduction_id": deduction_id
        }

    def get_employee_deductions(self, employee_id: str) -> List[Dict]:
        """Get all deductions for an employee"""
        result = []

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ed.*, dt.code, dt.name, dt.is_pretax
                FROM genfin_employee_deductions ed
                JOIN genfin_deduction_types dt ON ed.deduction_type_id = dt.deduction_type_id
                WHERE ed.employee_id = ? AND ed.is_active = 1
            """, (employee_id,))

            for row in cursor.fetchall():
                result.append({
                    "deduction_id": row['deduction_id'],
                    "code": row['code'],
                    "name": row['name'],
                    "is_pretax": bool(row['is_pretax']),
                    "amount": row['amount'],
                    "percentage": row['percentage'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date']
                })

        return result

    # ==================== TIME ENTRY ====================

    def record_time(
        self,
        employee_id: str,
        work_date: str,
        regular_hours: float = 0.0,
        overtime_hours: float = 0.0,
        double_time_hours: float = 0.0,
        sick_hours: float = 0.0,
        vacation_hours: float = 0.0,
        holiday_hours: float = 0.0,
        notes: str = ""
    ) -> Dict:
        """Record time for an employee"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT employee_id FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                         (employee_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Employee not found"}

            entry_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO genfin_time_entries
                (entry_id, employee_id, work_date, regular_hours, overtime_hours,
                 double_time_hours, sick_hours, vacation_hours, holiday_hours,
                 notes, approved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (entry_id, employee_id, work_date, regular_hours, overtime_hours,
                  double_time_hours, sick_hours, vacation_hours, holiday_hours,
                  notes, datetime.now(timezone.utc).isoformat()))
            conn.commit()

        return {
            "success": True,
            "entry_id": entry_id
        }

    def get_time_entries(
        self,
        employee_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get time entries with filtering"""
        result = []

        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT te.*, e.first_name, e.last_name
                FROM genfin_time_entries te
                JOIN genfin_employees e ON te.employee_id = e.employee_id
                WHERE 1=1
            """
            params = []

            if employee_id:
                query += " AND te.employee_id = ?"
                params.append(employee_id)

            if start_date:
                query += " AND te.work_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND te.work_date <= ?"
                params.append(end_date)

            query += " ORDER BY te.work_date DESC"

            cursor.execute(query, params)

            for row in cursor.fetchall():
                total_hours = (row['regular_hours'] + row['overtime_hours'] +
                              row['double_time_hours'] + row['sick_hours'] +
                              row['vacation_hours'] + row['holiday_hours'])
                result.append({
                    "entry_id": row['entry_id'],
                    "employee_id": row['employee_id'],
                    "employee_name": f"{row['first_name']} {row['last_name']}",
                    "work_date": row['work_date'],
                    "regular_hours": row['regular_hours'],
                    "overtime_hours": row['overtime_hours'],
                    "double_time_hours": row['double_time_hours'],
                    "sick_hours": row['sick_hours'],
                    "vacation_hours": row['vacation_hours'],
                    "holiday_hours": row['holiday_hours'],
                    "total_hours": total_hours,
                    "approved": bool(row['approved']),
                    "notes": row['notes'] or ""
                })

        return result

    # ==================== TAX CALCULATIONS ====================

    def _calculate_federal_tax(
        self,
        annual_gross: float,
        filing_status: FilingStatus,
        allowances: int = 0
    ) -> float:
        """Calculate federal income tax withholding"""
        standard_ded = STANDARD_DEDUCTION_2024.get(filing_status, 14600)
        taxable_income = max(0, annual_gross - standard_ded)

        brackets = FEDERAL_TAX_BRACKETS_2024.get(
            filing_status,
            FEDERAL_TAX_BRACKETS_2024[FilingStatus.SINGLE]
        )

        tax = 0.0
        prev_bracket = 0

        for bracket_limit, rate in brackets:
            if taxable_income <= bracket_limit:
                tax += (taxable_income - prev_bracket) * rate
                break
            else:
                tax += (bracket_limit - prev_bracket) * rate
                prev_bracket = bracket_limit

        return max(0, tax)

    def _calculate_fica(self, gross_pay: float, ytd_gross: float) -> Tuple[float, float, float, float]:
        """Calculate FICA taxes (SS and Medicare)"""
        ss_wage_remaining = max(0, SOCIAL_SECURITY_WAGE_BASE - ytd_gross)
        ss_taxable = min(gross_pay, ss_wage_remaining)
        ss_employee = ss_taxable * SOCIAL_SECURITY_RATE
        ss_employer = ss_taxable * SOCIAL_SECURITY_RATE

        medicare_employee = gross_pay * MEDICARE_RATE
        medicare_employer = gross_pay * MEDICARE_RATE

        additional_medicare = 0.0
        if ytd_gross + gross_pay > ADDITIONAL_MEDICARE_THRESHOLD:
            excess = max(0, ytd_gross + gross_pay - ADDITIONAL_MEDICARE_THRESHOLD)
            additional_medicare = min(gross_pay, excess) * ADDITIONAL_MEDICARE_RATE

        return (
            round(ss_employee, 2),
            round(medicare_employee + additional_medicare, 2),
            round(ss_employer, 2),
            round(medicare_employer, 2)
        )

    def _calculate_futa_suta(self, gross_pay: float, ytd_gross: float, state: str) -> Tuple[float, float]:
        """Calculate FUTA and SUTA (employer taxes)"""
        futa_remaining = max(0, FUTA_WAGE_BASE - ytd_gross)
        futa_taxable = min(gross_pay, futa_remaining)
        futa = futa_taxable * FUTA_RATE

        suta_rates = {
            "default": 0.027,
            "CA": 0.034,
            "TX": 0.027,
            "NY": 0.033,
            "FL": 0.027,
            "IL": 0.0325,
        }
        suta_rate = suta_rates.get(state.upper(), suta_rates["default"])
        suta_wage_base = 15000

        suta_remaining = max(0, suta_wage_base - ytd_gross)
        suta_taxable = min(gross_pay, suta_remaining)
        suta = suta_taxable * suta_rate

        return round(futa, 2), round(suta, 2)

    def _get_ytd_earnings(self, employee_id: str, as_of_date: date) -> float:
        """Get year-to-date earnings for an employee"""
        year_start = date(as_of_date.year, 1, 1)
        ytd_gross = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prl.gross_pay
                FROM genfin_pay_run_lines prl
                JOIN genfin_pay_runs pr ON prl.pay_run_id = pr.pay_run_id
                WHERE prl.employee_id = ?
                  AND pr.status IN ('approved', 'paid')
                  AND pr.pay_date >= ?
                  AND pr.pay_date < ?
            """, (employee_id, year_start.isoformat(), as_of_date.isoformat()))

            for row in cursor.fetchall():
                ytd_gross += row['gross_pay']

        return ytd_gross

    # ==================== PAY RUNS ====================

    def start_scheduled_payroll(self, schedule_id: str, bank_account_id: str) -> Dict:
        """Start a scheduled payroll run - QuickBooks style"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_pay_schedules WHERE schedule_id = ? AND is_active = 1",
                         (schedule_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Pay schedule not found"}

            emp_ids = json.loads(row['employee_ids_json'] or '[]')
            if not emp_ids:
                return {"success": False, "error": "No employees assigned to this schedule"}

            result = self.create_pay_run(
                pay_period_start=row['next_pay_period_start'],
                pay_period_end=row['next_pay_period_end'],
                pay_date=row['next_pay_date'],
                bank_account_id=bank_account_id,
                employee_ids=emp_ids,
                pay_run_type="scheduled",
                pay_schedule_id=schedule_id
            )

            if result.get("success") and row['auto_calculate']:
                self.calculate_pay_run(result["pay_run_id"])

        return result

    def create_unscheduled_payroll(
        self,
        pay_period_start: str,
        pay_period_end: str,
        pay_date: str,
        bank_account_id: str,
        employee_ids: List[str],
        reason: str = ""
    ) -> Dict:
        """Create an unscheduled payroll run - QuickBooks style"""
        if not employee_ids:
            return {"success": False, "error": "Must specify at least one employee"}

        return self.create_pay_run(
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            pay_date=pay_date,
            bank_account_id=bank_account_id,
            employee_ids=employee_ids,
            pay_run_type="unscheduled",
            memo=f"Unscheduled payroll: {reason}" if reason else "Unscheduled payroll"
        )

    def create_termination_check(
        self,
        employee_id: str,
        termination_date: str,
        pay_date: str,
        bank_account_id: str,
        include_pto_payout: bool = True,
        pto_hours_to_pay: float = 0.0,
        final_bonus: float = 0.0,
        reason: str = ""
    ) -> Dict:
        """Create a termination/final paycheck - QuickBooks style"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                         (employee_id,))
            emp_row = cursor.fetchone()
            if not emp_row:
                return {"success": False, "error": "Employee not found"}

            term_date = datetime.strptime(termination_date, "%Y-%m-%d").date()

            # Find the last pay period end for this employee
            cursor.execute("""
                SELECT pr.pay_period_end
                FROM genfin_pay_runs pr
                JOIN genfin_pay_run_lines prl ON pr.pay_run_id = prl.pay_run_id
                WHERE prl.employee_id = ? AND pr.status IN ('approved', 'paid')
                ORDER BY pr.pay_date DESC LIMIT 1
            """, (employee_id,))
            last_row = cursor.fetchone()

            if last_row:
                last_end = datetime.strptime(last_row['pay_period_end'], "%Y-%m-%d").date()
                period_start = last_end + timedelta(days=1)
            else:
                period_start = datetime.strptime(emp_row['hire_date'], "%Y-%m-%d").date() if emp_row['hire_date'] else term_date

            result = self.create_pay_run(
                pay_period_start=period_start.isoformat(),
                pay_period_end=termination_date,
                pay_date=pay_date,
                bank_account_id=bank_account_id,
                employee_ids=[employee_id],
                pay_run_type="termination",
                memo=f"Final paycheck - Termination: {reason}" if reason else "Final paycheck"
            )

            if result.get("success"):
                # Add PTO payout and bonus
                if include_pto_payout and pto_hours_to_pay > 0:
                    pay_type = emp_row['pay_type']
                    pay_rate = emp_row['pay_rate']
                    if pay_type == 'hourly':
                        vacation_pay = pto_hours_to_pay * pay_rate
                    else:
                        hourly_rate = pay_rate / 2080
                        vacation_pay = pto_hours_to_pay * hourly_rate

                    cursor.execute("""
                        UPDATE genfin_pay_run_lines
                        SET vacation_pay = ?, vacation_hours = ?
                        WHERE pay_run_id = ? AND employee_id = ?
                    """, (vacation_pay, pto_hours_to_pay, result["pay_run_id"], employee_id))

                if final_bonus > 0:
                    cursor.execute("""
                        UPDATE genfin_pay_run_lines
                        SET bonus = ?
                        WHERE pay_run_id = ? AND employee_id = ?
                    """, (final_bonus, result["pay_run_id"], employee_id))

                conn.commit()

                # Terminate the employee
                self.terminate_employee(employee_id, termination_date, reason)

        return result

    def create_bonus_payroll(
        self,
        bank_account_id: str,
        pay_date: str,
        bonus_list: List[Dict],
        memo: str = "Bonus payment"
    ) -> Dict:
        """Create a bonus-only payroll run - QuickBooks style"""
        if not bonus_list:
            return {"success": False, "error": "No bonus amounts specified"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Validate employees
            for bonus_item in bonus_list:
                emp_id = bonus_item.get("employee_id")
                if emp_id:
                    cursor.execute("SELECT employee_id FROM genfin_employees WHERE employee_id = ? AND is_active = 1",
                                 (emp_id,))
                    if not cursor.fetchone():
                        return {"success": False, "error": f"Employee {emp_id} not found"}

            _p_date = datetime.strptime(pay_date, "%Y-%m-%d").date()
            pay_run_id = str(uuid.uuid4())
            pay_run_number = self._get_next_number("next_pay_run_number")
            now = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO genfin_pay_runs
                (pay_run_id, pay_run_number, pay_period_start, pay_period_end,
                 pay_date, bank_account_id, pay_run_type, status, memo,
                 is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'bonus', 'draft', ?, 1, ?, ?)
            """, (pay_run_id, pay_run_number, pay_date, pay_date, pay_date,
                  bank_account_id, memo, now, now))

            line_count = 0
            total_bonus = 0.0
            for bonus_item in bonus_list:
                emp_id = bonus_item.get("employee_id")
                amount = bonus_item.get("amount", 0.0)

                if not emp_id or amount <= 0:
                    continue

                cursor.execute("SELECT payment_method FROM genfin_employees WHERE employee_id = ?",
                             (emp_id,))
                emp_row = cursor.fetchone()
                if not emp_row:
                    continue

                line_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_pay_run_lines
                    (line_id, pay_run_id, employee_id, bonus, payment_method)
                    VALUES (?, ?, ?, ?, ?)
                """, (line_id, pay_run_id, emp_id, amount, emp_row['payment_method']))

                line_count += 1
                total_bonus += amount

            conn.commit()

        return {
            "success": True,
            "pay_run_id": pay_run_id,
            "pay_run_number": pay_run_number,
            "pay_run_type": "bonus",
            "employee_count": line_count,
            "total_bonus": total_bonus
        }

    def create_pay_run(
        self,
        pay_period_start: str,
        pay_period_end: str,
        pay_date: str,
        bank_account_id: str,
        employee_ids: List[str] = None,
        pay_run_type: str = "scheduled",
        pay_schedule_id: Optional[str] = None,
        memo: str = ""
    ) -> Dict:
        """Create a new pay run"""
        pay_run_id = str(uuid.uuid4())
        pay_run_number = self._get_next_number("next_pay_run_number")
        now = datetime.now(timezone.utc).isoformat()

        _p_start = datetime.strptime(pay_period_start, "%Y-%m-%d").date()
        _p_end = datetime.strptime(pay_period_end, "%Y-%m-%d").date()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get employees
            if employee_ids is None:
                cursor.execute("SELECT * FROM genfin_employees WHERE is_active = 1 AND status = 'active'")
                emp_rows = cursor.fetchall()
            else:
                placeholders = ','.join(['?' for _ in employee_ids])
                cursor.execute(f"SELECT * FROM genfin_employees WHERE employee_id IN ({placeholders}) AND is_active = 1",
                             employee_ids)
                emp_rows = cursor.fetchall()

            # Create pay run
            cursor.execute("""
                INSERT INTO genfin_pay_runs
                (pay_run_id, pay_run_number, pay_period_start, pay_period_end,
                 pay_date, bank_account_id, pay_run_type, pay_schedule_id,
                 status, memo, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, 1, ?, ?)
            """, (pay_run_id, pay_run_number, pay_period_start, pay_period_end,
                  pay_date, bank_account_id, pay_run_type, pay_schedule_id,
                  memo, now, now))

            # Create lines for each employee
            for emp_row in emp_rows:
                # Get time entries for period
                cursor.execute("""
                    SELECT SUM(regular_hours) as reg, SUM(overtime_hours) as ot,
                           SUM(double_time_hours) as dt, SUM(sick_hours) as sick,
                           SUM(vacation_hours) as vac, SUM(holiday_hours) as hol
                    FROM genfin_time_entries
                    WHERE employee_id = ? AND work_date >= ? AND work_date <= ?
                """, (emp_row['employee_id'], pay_period_start, pay_period_end))

                time_row = cursor.fetchone()

                total_regular = time_row['reg'] or 0.0
                total_ot = time_row['ot'] or 0.0
                total_dt = time_row['dt'] or 0.0
                total_sick = time_row['sick'] or 0.0
                total_vacation = time_row['vac'] or 0.0
                total_holiday = time_row['hol'] or 0.0

                # If no time entries, use default hours for salaried
                if total_regular == 0 and emp_row['pay_type'] == 'salary':
                    total_regular = emp_row['default_hours']

                line_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_pay_run_lines
                    (line_id, pay_run_id, employee_id, regular_hours, overtime_hours,
                     double_time_hours, sick_hours, vacation_hours, holiday_hours,
                     payment_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (line_id, pay_run_id, emp_row['employee_id'], total_regular,
                      total_ot, total_dt, total_sick, total_vacation, total_holiday,
                      emp_row['payment_method']))

            conn.commit()

        return {
            "success": True,
            "pay_run_id": pay_run_id,
            "pay_run_number": pay_run_number,
            "employee_count": len(emp_rows)
        }

    def calculate_pay_run(self, pay_run_id: str) -> Dict:
        """Calculate all pay for a pay run"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM genfin_pay_runs WHERE pay_run_id = ? AND is_active = 1",
                         (pay_run_id,))
            pay_run_row = cursor.fetchone()
            if not pay_run_row:
                return {"success": False, "error": "Pay run not found"}

            if pay_run_row['status'] not in ['draft', 'calculated']:
                return {"success": False, "error": "Pay run cannot be recalculated"}

            pay_date = datetime.strptime(pay_run_row['pay_date'], "%Y-%m-%d").date()

            total_gross = 0.0
            total_taxes = 0.0
            total_deductions = 0.0
            total_net = 0.0
            total_employer_taxes = 0.0

            cursor.execute("SELECT * FROM genfin_pay_run_lines WHERE pay_run_id = ?", (pay_run_id,))
            lines = cursor.fetchall()

            for line in lines:
                cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ?",
                             (line['employee_id'],))
                emp_row = cursor.fetchone()
                if not emp_row:
                    continue

                # Calculate gross pay
                pay_type = emp_row['pay_type']
                pay_rate = emp_row['pay_rate']
                pay_frequency = PayFrequency(emp_row['pay_frequency'])

                if pay_type == 'hourly':
                    regular_pay = line['regular_hours'] * pay_rate
                    overtime_pay = line['overtime_hours'] * pay_rate * 1.5
                    double_time_pay = line['double_time_hours'] * pay_rate * 2.0
                    sick_pay = line['sick_hours'] * pay_rate
                    vacation_pay = line['vacation_hours'] * pay_rate
                    holiday_pay = line['holiday_hours'] * pay_rate
                else:
                    periods_per_year = {
                        PayFrequency.WEEKLY: 52,
                        PayFrequency.BIWEEKLY: 26,
                        PayFrequency.SEMIMONTHLY: 24,
                        PayFrequency.MONTHLY: 12
                    }
                    period_pay = pay_rate / periods_per_year.get(pay_frequency, 26)
                    regular_pay = period_pay
                    overtime_pay = 0.0
                    double_time_pay = 0.0
                    sick_pay = 0.0
                    vacation_pay = 0.0
                    holiday_pay = 0.0

                # Add existing bonus/vacation from line
                bonus = line['bonus'] or 0.0
                vacation_pay = max(vacation_pay, line['vacation_pay'] or 0.0)

                gross_pay = round(
                    regular_pay + overtime_pay + double_time_pay +
                    sick_pay + vacation_pay + holiday_pay +
                    bonus + (line['commission'] or 0.0) + (line['other_earnings'] or 0.0), 2
                )

                # Get YTD for tax calculations
                ytd_gross = self._get_ytd_earnings(emp_row['employee_id'], pay_date)

                # Calculate pre-tax deductions
                pretax_deductions = 0.0
                deductions_list = []

                cursor.execute("""
                    SELECT ed.*, dt.code, dt.name, dt.is_pretax
                    FROM genfin_employee_deductions ed
                    JOIN genfin_deduction_types dt ON ed.deduction_type_id = dt.deduction_type_id
                    WHERE ed.employee_id = ? AND ed.is_active = 1
                """, (emp_row['employee_id'],))

                for ded_row in cursor.fetchall():
                    # Check date range
                    if ded_row['start_date'] and pay_date < datetime.strptime(ded_row['start_date'], "%Y-%m-%d").date():
                        continue
                    if ded_row['end_date'] and pay_date > datetime.strptime(ded_row['end_date'], "%Y-%m-%d").date():
                        continue

                    if ded_row['percentage'] > 0:
                        ded_amount = gross_pay * (ded_row['percentage'] / 100)
                    else:
                        ded_amount = ded_row['amount']

                    if ded_row['is_pretax']:
                        pretax_deductions += ded_amount

                    deductions_list.append({
                        "code": ded_row['code'],
                        "name": ded_row['name'],
                        "amount": round(ded_amount, 2),
                        "is_pretax": bool(ded_row['is_pretax'])
                    })

                # Taxable gross after pre-tax deductions
                taxable_gross = gross_pay - pretax_deductions

                # Calculate annualized income for tax brackets
                periods_per_year = {
                    PayFrequency.WEEKLY: 52,
                    PayFrequency.BIWEEKLY: 26,
                    PayFrequency.SEMIMONTHLY: 24,
                    PayFrequency.MONTHLY: 12
                }
                periods = periods_per_year.get(pay_frequency, 26)
                annual_taxable = taxable_gross * periods

                # Federal income tax
                filing_status = FilingStatus(emp_row['filing_status'])
                annual_fed_tax = self._calculate_federal_tax(
                    annual_taxable,
                    filing_status,
                    emp_row['federal_allowances']
                )
                federal_income_tax = round(annual_fed_tax / periods, 2)
                federal_income_tax += emp_row['federal_additional_withholding']

                # State income tax
                state_rates = {
                    "CA": 0.093, "NY": 0.0685, "TX": 0.0, "FL": 0.0,
                    "WA": 0.0, "NV": 0.0, "default": 0.05
                }
                state = emp_row['state'] or ""
                state_rate = state_rates.get(state.upper(), state_rates["default"])
                state_income_tax = round(taxable_gross * state_rate, 2)
                state_income_tax += emp_row['state_additional_withholding']

                # FICA
                ss_emp, med_emp, ss_er, med_er = self._calculate_fica(taxable_gross, ytd_gross)

                # FUTA / SUTA
                futa, suta = self._calculate_futa_suta(taxable_gross, ytd_gross, state)

                # Total taxes
                employee_taxes = (
                    federal_income_tax + state_income_tax + ss_emp + med_emp
                )

                # Post-tax deductions
                posttax_deductions = sum(d["amount"] for d in deductions_list if not d["is_pretax"])
                total_line_deductions = round(pretax_deductions + posttax_deductions, 2)

                # Net pay
                net_pay = round(gross_pay - employee_taxes - total_line_deductions, 2)

                # Direct deposit amount
                dd_amount = net_pay if emp_row['payment_method'] == 'direct_deposit' else 0.0

                # Employer taxes
                employer_taxes = ss_er + med_er + futa + suta

                # Update line
                cursor.execute("""
                    UPDATE genfin_pay_run_lines
                    SET regular_pay = ?, overtime_pay = ?, double_time_pay = ?,
                        sick_pay = ?, vacation_pay = ?, holiday_pay = ?,
                        gross_pay = ?, federal_income_tax = ?, state_income_tax = ?,
                        social_security_employee = ?, medicare_employee = ?,
                        social_security_employer = ?, medicare_employer = ?,
                        futa = ?, suta = ?, deductions_json = ?,
                        total_deductions = ?, net_pay = ?, direct_deposit_amount = ?
                    WHERE line_id = ?
                """, (regular_pay, overtime_pay, double_time_pay,
                      sick_pay, vacation_pay, holiday_pay,
                      gross_pay, federal_income_tax, state_income_tax,
                      ss_emp, med_emp, ss_er, med_er, futa, suta,
                      json.dumps(deductions_list), total_line_deductions,
                      net_pay, dd_amount, line['line_id']))

                # Add to totals
                total_gross += gross_pay
                total_taxes += employee_taxes
                total_deductions += total_line_deductions
                total_net += net_pay
                total_employer_taxes += employer_taxes

            # Update pay run totals
            cursor.execute("""
                UPDATE genfin_pay_runs
                SET total_gross = ?, total_taxes = ?, total_deductions = ?,
                    total_net = ?, total_employer_taxes = ?, status = 'calculated',
                    updated_at = ?
                WHERE pay_run_id = ?
            """, (round(total_gross, 2), round(total_taxes, 2),
                  round(total_deductions, 2), round(total_net, 2),
                  round(total_employer_taxes, 2), datetime.now(timezone.utc).isoformat(),
                  pay_run_id))

            conn.commit()

        return {
            "success": True,
            "pay_run": self.get_pay_run(pay_run_id)
        }

    def approve_pay_run(self, pay_run_id: str, approved_by: str) -> Dict:
        """Approve a calculated pay run"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM genfin_pay_runs WHERE pay_run_id = ? AND is_active = 1",
                         (pay_run_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Pay run not found"}

            if row['status'] != 'calculated':
                return {"success": False, "error": "Pay run must be calculated before approval"}

            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE genfin_pay_runs
                SET status = 'approved', approved_by = ?, approved_at = ?, updated_at = ?
                WHERE pay_run_id = ?
            """, (approved_by, now, now, pay_run_id))
            conn.commit()

        return {
            "success": True,
            "message": "Pay run approved"
        }

    def process_pay_run(self, pay_run_id: str) -> Dict:
        """Process an approved pay run - create checks and ACH"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_pay_runs WHERE pay_run_id = ? AND is_active = 1",
                         (pay_run_id,))
            pay_run_row = cursor.fetchone()
            if not pay_run_row:
                return {"success": False, "error": "Pay run not found"}

            if pay_run_row['status'] != 'approved':
                return {"success": False, "error": "Pay run must be approved before processing"}

            checks_created = []
            ach_entries = []

            cursor.execute("SELECT * FROM genfin_pay_run_lines WHERE pay_run_id = ?", (pay_run_id,))
            lines = cursor.fetchall()

            for line in lines:
                cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ?",
                             (line['employee_id'],))
                emp_row = cursor.fetchone()
                if not emp_row:
                    continue

                if line['payment_method'] == 'check':
                    # Create payroll check
                    check_result = genfin_banking_service.create_check(
                        bank_account_id=pay_run_row['bank_account_id'],
                        payee_name=f"{emp_row['first_name']} {emp_row['last_name']}",
                        amount=line['net_pay'],
                        check_date=pay_run_row['pay_date'],
                        memo=f"Payroll {pay_run_row['pay_period_start']} - {pay_run_row['pay_period_end']}",
                        payee_address_line1=emp_row['address_line1'] or "",
                        payee_city=emp_row['city'] or "",
                        payee_state=emp_row['state'] or "",
                        payee_zip=emp_row['zip_code'] or "",
                        voucher_description=self._generate_pay_stub(line, emp_row)
                    )

                    if check_result.get("success"):
                        cursor.execute("UPDATE genfin_pay_run_lines SET check_id = ? WHERE line_id = ?",
                                     (check_result["check_id"], line['line_id']))
                        checks_created.append(check_result["check_number"])

                elif line['payment_method'] == 'direct_deposit':
                    ach_entries.append({
                        "recipient_name": f"{emp_row['last_name']} {emp_row['first_name']}"[:22],
                        "routing_number": emp_row['bank_routing_number'],
                        "account_number": emp_row['bank_account_number'],
                        "account_type": emp_row['bank_account_type'],
                        "amount": line['net_pay'],
                        "transaction_code": ACHTransactionCode.CHECKING_CREDIT.value if emp_row['bank_account_type'] == "checking" else ACHTransactionCode.SAVINGS_CREDIT.value,
                        "individual_id": emp_row['employee_number'],
                        "individual_name": f"{emp_row['last_name']} {emp_row['first_name']}"[:22]
                    })

            # Create ACH batch if there are direct deposit entries
            ach_batch_id = None
            if ach_entries:
                ach_result = genfin_banking_service.create_ach_batch(
                    bank_account_id=pay_run_row['bank_account_id'],
                    effective_date=pay_run_row['pay_date'],
                    batch_description="PAYROLL",
                    entries=ach_entries
                )
                if ach_result.get("success"):
                    ach_batch_id = ach_result["batch_id"]

            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE genfin_pay_runs
                SET status = 'paid', paid_at = ?, ach_batch_id = ?, updated_at = ?
                WHERE pay_run_id = ?
            """, (now, ach_batch_id, now, pay_run_id))

            conn.commit()

            # Advance the pay schedule if this was a scheduled payroll
            if pay_run_row['pay_schedule_id'] and pay_run_row['pay_run_type'] == 'scheduled':
                self._advance_schedule(pay_run_row['pay_schedule_id'])

        return {
            "success": True,
            "checks_created": checks_created,
            "direct_deposits": len(ach_entries),
            "ach_batch_id": ach_batch_id,
            "pay_run_type": pay_run_row['pay_run_type']
        }

    def _generate_pay_stub(self, line: sqlite3.Row, emp_row: sqlite3.Row) -> str:
        """Generate pay stub text for check voucher"""
        stub = f"""Employee: {emp_row['first_name']} {emp_row['last_name']} ({emp_row['employee_number']})

EARNINGS:
  Regular ({line['regular_hours']} hrs): ${line['regular_pay']:,.2f}"""

        if line['overtime_hours'] > 0:
            stub += f"\n  Overtime ({line['overtime_hours']} hrs): ${line['overtime_pay']:,.2f}"
        if line['sick_hours'] > 0:
            stub += f"\n  Sick ({line['sick_hours']} hrs): ${line['sick_pay']:,.2f}"
        if line['vacation_hours'] > 0:
            stub += f"\n  Vacation ({line['vacation_hours']} hrs): ${line['vacation_pay']:,.2f}"
        if line['holiday_hours'] > 0:
            stub += f"\n  Holiday ({line['holiday_hours']} hrs): ${line['holiday_pay']:,.2f}"

        stub += f"\n  GROSS PAY: ${line['gross_pay']:,.2f}"

        stub += f"""

TAXES:
  Federal Income Tax: ${line['federal_income_tax']:,.2f}
  State Income Tax: ${line['state_income_tax']:,.2f}
  Social Security: ${line['social_security_employee']:,.2f}
  Medicare: ${line['medicare_employee']:,.2f}"""

        deductions = json.loads(line['deductions_json'] or '[]')
        if deductions:
            stub += "\n\nDEDUCTIONS:"
            for ded in deductions:
                stub += f"\n  {ded['name']}: ${ded['amount']:,.2f}"

        stub += f"""

NET PAY: ${line['net_pay']:,.2f}"""

        return stub

    def get_pay_run(self, pay_run_id: str) -> Optional[Dict]:
        """Get pay run by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_pay_runs WHERE pay_run_id = ?", (pay_run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_pay_run(row)

    def list_pay_runs(
        self,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """List pay runs with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_pay_runs WHERE is_active = 1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if start_date:
                query += " AND pay_date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND pay_date <= ?"
                params.append(end_date)

            query += " ORDER BY pay_date DESC"

            cursor.execute(query, params)

            result = []
            for row in cursor.fetchall():
                cursor.execute("SELECT COUNT(*) FROM genfin_pay_run_lines WHERE pay_run_id = ?",
                             (row['pay_run_id'],))
                emp_count = cursor.fetchone()[0]

                result.append({
                    "id": row['pay_run_id'],
                    "schedule_id": row['pay_schedule_id'] or "",
                    "pay_date": datetime.strptime(row['pay_date'], "%Y-%m-%d").date(),
                    "status": row['status'],
                    "total_gross": row['total_gross'],
                    "total_net": row['total_net'],
                    "pay_run_id": row['pay_run_id'],
                    "pay_run_number": row['pay_run_number'],
                    "pay_period": f"{row['pay_period_start']} - {row['pay_period_end']}",
                    "employee_count": emp_count,
                    "created_at": row['created_at']
                })

        return {"pay_runs": result, "total": len(result)}

    def _row_to_pay_run(self, row: sqlite3.Row) -> Dict:
        """Convert pay run row to dictionary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prl.*, e.first_name, e.last_name
                FROM genfin_pay_run_lines prl
                JOIN genfin_employees e ON prl.employee_id = e.employee_id
                WHERE prl.pay_run_id = ?
            """, (row['pay_run_id'],))

            lines_data = []
            for line_row in cursor.fetchall():
                lines_data.append({
                    "line_id": line_row['line_id'],
                    "employee_id": line_row['employee_id'],
                    "employee_name": f"{line_row['first_name']} {line_row['last_name']}",
                    "regular_hours": line_row['regular_hours'],
                    "overtime_hours": line_row['overtime_hours'],
                    "gross_pay": line_row['gross_pay'],
                    "federal_tax": line_row['federal_income_tax'],
                    "state_tax": line_row['state_income_tax'],
                    "social_security": line_row['social_security_employee'],
                    "medicare": line_row['medicare_employee'],
                    "total_deductions": line_row['total_deductions'],
                    "net_pay": line_row['net_pay'],
                    "payment_method": line_row['payment_method'],
                    "check_id": line_row['check_id']
                })

        return {
            "pay_run_id": row['pay_run_id'],
            "pay_run_number": row['pay_run_number'],
            "pay_period_start": row['pay_period_start'],
            "pay_period_end": row['pay_period_end'],
            "pay_date": row['pay_date'],
            "bank_account_id": row['bank_account_id'],
            "lines": lines_data,
            "total_gross": row['total_gross'],
            "total_taxes": row['total_taxes'],
            "total_deductions": row['total_deductions'],
            "total_net": row['total_net'],
            "total_employer_taxes": row['total_employer_taxes'],
            "status": row['status'],
            "approved_by": row['approved_by'] or "",
            "approved_at": row['approved_at'],
            "paid_at": row['paid_at'],
            "ach_batch_id": row['ach_batch_id'],
            "created_at": row['created_at']
        }

    # ==================== REPORTS ====================

    def get_employee_ytd(self, employee_id: str, year: int) -> Dict:
        """Get year-to-date earnings and taxes for an employee"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_employees WHERE employee_id = ?", (employee_id,))
            emp_row = cursor.fetchone()
            if not emp_row:
                return {"error": "Employee not found"}

            ytd = {
                "regular_pay": 0.0,
                "overtime_pay": 0.0,
                "gross_pay": 0.0,
                "federal_tax": 0.0,
                "state_tax": 0.0,
                "social_security": 0.0,
                "medicare": 0.0,
                "total_deductions": 0.0,
                "net_pay": 0.0
            }

            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"

            cursor.execute("""
                SELECT prl.*
                FROM genfin_pay_run_lines prl
                JOIN genfin_pay_runs pr ON prl.pay_run_id = pr.pay_run_id
                WHERE prl.employee_id = ?
                  AND pr.status IN ('approved', 'paid')
                  AND pr.pay_date >= ? AND pr.pay_date <= ?
            """, (employee_id, year_start, year_end))

            for line_row in cursor.fetchall():
                ytd["regular_pay"] += line_row['regular_pay']
                ytd["overtime_pay"] += line_row['overtime_pay']
                ytd["gross_pay"] += line_row['gross_pay']
                ytd["federal_tax"] += line_row['federal_income_tax']
                ytd["state_tax"] += line_row['state_income_tax']
                ytd["social_security"] += line_row['social_security_employee']
                ytd["medicare"] += line_row['medicare_employee']
                ytd["total_deductions"] += line_row['total_deductions']
                ytd["net_pay"] += line_row['net_pay']

            for key in ytd:
                ytd[key] = round(ytd[key], 2)

        return {
            "employee_id": employee_id,
            "employee_name": f"{emp_row['first_name']} {emp_row['last_name']}",
            "year": year,
            "ytd": ytd
        }

    def get_payroll_summary(self, start_date: str, end_date: str) -> Dict:
        """Get payroll summary for date range"""
        summary = {
            "total_gross": 0.0,
            "total_federal_tax": 0.0,
            "total_state_tax": 0.0,
            "total_social_security_employee": 0.0,
            "total_medicare_employee": 0.0,
            "total_social_security_employer": 0.0,
            "total_medicare_employer": 0.0,
            "total_futa": 0.0,
            "total_suta": 0.0,
            "total_deductions": 0.0,
            "total_net": 0.0,
            "pay_run_count": 0,
            "employee_count": set()
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pr.pay_run_id, prl.*
                FROM genfin_pay_runs pr
                JOIN genfin_pay_run_lines prl ON pr.pay_run_id = prl.pay_run_id
                WHERE pr.status IN ('approved', 'paid')
                  AND pr.pay_date >= ? AND pr.pay_date <= ?
            """, (start_date, end_date))

            pay_run_ids = set()
            for row in cursor.fetchall():
                pay_run_ids.add(row['pay_run_id'])
                summary["total_gross"] += row['gross_pay']
                summary["total_federal_tax"] += row['federal_income_tax']
                summary["total_state_tax"] += row['state_income_tax']
                summary["total_social_security_employee"] += row['social_security_employee']
                summary["total_medicare_employee"] += row['medicare_employee']
                summary["total_social_security_employer"] += row['social_security_employer']
                summary["total_medicare_employer"] += row['medicare_employer']
                summary["total_futa"] += row['futa']
                summary["total_suta"] += row['suta']
                summary["total_deductions"] += row['total_deductions']
                summary["total_net"] += row['net_pay']
                summary["employee_count"].add(row['employee_id'])

            summary["pay_run_count"] = len(pay_run_ids)
            summary["employee_count"] = len(summary["employee_count"])

        for key in summary:
            if isinstance(summary[key], float):
                summary[key] = round(summary[key], 2)

        summary["total_employer_taxes"] = round(
            summary["total_social_security_employer"] +
            summary["total_medicare_employer"] +
            summary["total_futa"] +
            summary["total_suta"], 2
        )

        summary["total_tax_liability"] = round(
            summary["total_federal_tax"] +
            summary["total_state_tax"] +
            summary["total_social_security_employee"] +
            summary["total_medicare_employee"] +
            summary["total_employer_taxes"], 2
        )

        return {
            "period_start": start_date,
            "period_end": end_date,
            "summary": summary
        }

    def get_tax_liability(self, period: str, year: int) -> Dict:
        """Get tax liability for a period (monthly, quarterly)"""
        period_upper = period.upper()
        if period_upper.startswith("Q"):
            quarter = int(period_upper[1])
            month_start = (quarter - 1) * 3 + 1
            month_end = quarter * 3
            start_date = date(year, month_start, 1)
            if month_end == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = date(year, month_end + 1, 1) - timedelta(days=1)
        else:
            month = int(period)
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

        summary = self.get_payroll_summary(start_date.isoformat(), end_date.isoformat())

        return {
            "period": period,
            "year": year,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "federal_income_tax": summary["summary"]["total_federal_tax"],
            "social_security_total": round(
                summary["summary"]["total_social_security_employee"] +
                summary["summary"]["total_social_security_employer"], 2
            ),
            "medicare_total": round(
                summary["summary"]["total_medicare_employee"] +
                summary["summary"]["total_medicare_employer"], 2
            ),
            "total_federal_deposit": round(
                summary["summary"]["total_federal_tax"] +
                summary["summary"]["total_social_security_employee"] +
                summary["summary"]["total_social_security_employer"] +
                summary["summary"]["total_medicare_employee"] +
                summary["summary"]["total_medicare_employer"], 2
            ),
            "state_income_tax": summary["summary"]["total_state_tax"],
            "futa": summary["summary"]["total_futa"],
            "suta": summary["summary"]["total_suta"]
        }

    # ==================== UTILITY METHODS ====================

    def get_service_summary(self) -> Dict:
        """Get GenFin Payroll service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM genfin_employees WHERE is_active = 1 AND status = 'active'")
            active_employees = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_employees WHERE is_active = 1")
            total_employees = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_pay_runs WHERE is_active = 1")
            total_pay_runs = cursor.fetchone()[0]

            year_start = f"{date.today().year}-01-01"
            cursor.execute("""
                SELECT COALESCE(SUM(total_net), 0)
                FROM genfin_pay_runs
                WHERE status = 'paid' AND pay_date >= ?
            """, (year_start,))
            total_paid_ytd = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_earning_types WHERE is_active = 1")
            earning_types = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_deduction_types WHERE is_active = 1")
            deduction_types = cursor.fetchone()[0]

        return {
            "service": "GenFin Payroll",
            "version": "1.0.0",
            "features": [
                "Employee Management",
                "Time Tracking",
                "Tax Calculations (Federal, State, FICA)",
                "Direct Deposit (ACH)",
                "Payroll Check Printing",
                "Tax Liability Reports",
                "YTD Reporting"
            ],
            "total_employees": total_employees,
            "active_employees": active_employees,
            "total_pay_runs": total_pay_runs,
            "ytd_paid": round(total_paid_ytd, 2),
            "earning_types": earning_types,
            "deduction_types": deduction_types
        }


# Singleton instance
genfin_payroll_service = GenFinPayrollService()
