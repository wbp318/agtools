"""
GenFin Payroll Service - Employees, Pay Runs, Taxes, Direct Deposit, Tax Forms
Complete payroll management for farm operations
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid

from .genfin_core_service import genfin_core_service
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
    GenFin Payroll Service

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.employees: Dict[str, Employee] = {}
        self.pay_rates: Dict[str, PayRate] = {}
        self.time_entries: Dict[str, TimeEntry] = {}
        self.earning_types: Dict[str, EarningType] = {}
        self.deduction_types: Dict[str, DeductionType] = {}
        self.employee_deductions: Dict[str, EmployeeDeduction] = {}
        self.pay_runs: Dict[str, PayRun] = {}
        self.tax_payments: Dict[str, TaxPayment] = {}

        self.next_employee_number = 1001
        self.next_pay_run_number = 1

        # Initialize default earning types
        self._initialize_earning_types()
        # Initialize default deduction types
        self._initialize_deduction_types()

        self._initialized = True

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

        for code, name, taxable, is_ot, mult in defaults:
            et_id = str(uuid.uuid4())
            self.earning_types[et_id] = EarningType(
                earning_type_id=et_id,
                code=code,
                name=name,
                is_taxable=taxable,
                is_overtime=is_ot,
                multiplier=mult
            )

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

        for code, name, pretax, is_pct, amt, pct, max_amt in defaults:
            dt_id = str(uuid.uuid4())
            self.deduction_types[dt_id] = DeductionType(
                deduction_type_id=dt_id,
                code=code,
                name=name,
                is_pretax=pretax,
                is_percentage=is_pct,
                default_amount=amt,
                default_percentage=pct,
                max_annual_amount=max_amt
            )

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
        ssn: str = "",
        date_of_birth: Optional[str] = None,
        filing_status: str = "single",
        federal_allowances: int = 0,
        payment_method: str = "check",
        bank_routing_number: str = "",
        bank_account_number: str = "",
        bank_account_type: str = "checking",
        is_owner: bool = False
    ) -> Dict:
        """Create a new employee"""
        employee_id = str(uuid.uuid4())
        employee_number = f"EMP-{self.next_employee_number}"
        self.next_employee_number += 1

        h_date = datetime.strptime(hire_date, "%Y-%m-%d").date() if hire_date else date.today()
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date() if date_of_birth else None

        employee = Employee(
            employee_id=employee_id,
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
            phone=phone,
            address_line1=address_line1,
            city=city,
            state=state,
            zip_code=zip_code,
            employee_type=EmployeeType(employee_type),
            department=department,
            job_title=job_title,
            hire_date=h_date,
            pay_type=PayType(pay_type),
            pay_rate=pay_rate,
            pay_frequency=PayFrequency(pay_frequency),
            ssn=ssn,
            date_of_birth=dob,
            filing_status=FilingStatus(filing_status),
            federal_allowances=federal_allowances,
            payment_method=PaymentMethod(payment_method),
            bank_routing_number=bank_routing_number,
            bank_account_number=bank_account_number,
            bank_account_type=bank_account_type,
            is_owner=is_owner
        )

        self.employees[employee_id] = employee

        # Create initial pay rate record
        rate_id = str(uuid.uuid4())
        self.pay_rates[rate_id] = PayRate(
            rate_id=rate_id,
            employee_id=employee_id,
            effective_date=h_date,
            pay_type=employee.pay_type,
            rate=pay_rate,
            reason="Initial rate"
        )

        return {
            "success": True,
            "employee_id": employee_id,
            "employee_number": employee_number,
            "employee": self._employee_to_dict(employee)
        }

    def update_employee(self, employee_id: str, **kwargs) -> Dict:
        """Update employee information"""
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found"}

        employee = self.employees[employee_id]

        # Handle pay rate change
        if "pay_rate" in kwargs and kwargs["pay_rate"] != employee.pay_rate:
            rate_id = str(uuid.uuid4())
            self.pay_rates[rate_id] = PayRate(
                rate_id=rate_id,
                employee_id=employee_id,
                effective_date=date.today(),
                pay_type=employee.pay_type,
                rate=kwargs["pay_rate"],
                reason=kwargs.get("rate_change_reason", "Rate change")
            )

        for key, value in kwargs.items():
            if hasattr(employee, key) and value is not None:
                if key == "employee_type":
                    value = EmployeeType(value)
                elif key == "pay_type":
                    value = PayType(value)
                elif key == "pay_frequency":
                    value = PayFrequency(value)
                elif key == "filing_status":
                    value = FilingStatus(value)
                elif key == "payment_method":
                    value = PaymentMethod(value)
                elif key in ["hire_date", "termination_date", "date_of_birth"]:
                    if isinstance(value, str):
                        value = datetime.strptime(value, "%Y-%m-%d").date()
                setattr(employee, key, value)

        employee.updated_at = datetime.now()

        return {
            "success": True,
            "employee": self._employee_to_dict(employee)
        }

    def terminate_employee(self, employee_id: str, termination_date: str, reason: str = "") -> Dict:
        """Terminate an employee"""
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found"}

        employee = self.employees[employee_id]
        employee.status = EmployeeStatus.TERMINATED
        employee.termination_date = datetime.strptime(termination_date, "%Y-%m-%d").date()
        employee.notes = f"{employee.notes}\nTerminated: {reason}" if reason else employee.notes
        employee.updated_at = datetime.now()

        return {
            "success": True,
            "employee": self._employee_to_dict(employee)
        }

    def get_employee(self, employee_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        if employee_id not in self.employees:
            return None
        return self._employee_to_dict(self.employees[employee_id])

    def list_employees(
        self,
        status: Optional[str] = None,
        employee_type: Optional[str] = None,
        department: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict]:
        """List employees with filtering"""
        result = []

        for employee in self.employees.values():
            if active_only and employee.status != EmployeeStatus.ACTIVE:
                continue
            if status and employee.status.value != status:
                continue
            if employee_type and employee.employee_type.value != employee_type:
                continue
            if department and employee.department != department:
                continue

            result.append(self._employee_to_dict(employee))

        return sorted(result, key=lambda e: e["last_name"])

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
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found"}
        if deduction_type_id not in self.deduction_types:
            return {"success": False, "error": "Deduction type not found"}

        deduction_id = str(uuid.uuid4())

        s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

        deduction = EmployeeDeduction(
            deduction_id=deduction_id,
            employee_id=employee_id,
            deduction_type_id=deduction_type_id,
            amount=amount,
            percentage=percentage,
            start_date=s_date,
            end_date=e_date
        )

        self.employee_deductions[deduction_id] = deduction

        return {
            "success": True,
            "deduction_id": deduction_id
        }

    def get_employee_deductions(self, employee_id: str) -> List[Dict]:
        """Get all deductions for an employee"""
        result = []

        for ded in self.employee_deductions.values():
            if ded.employee_id != employee_id:
                continue
            if not ded.is_active:
                continue

            ded_type = self.deduction_types.get(ded.deduction_type_id)
            if not ded_type:
                continue

            result.append({
                "deduction_id": ded.deduction_id,
                "code": ded_type.code,
                "name": ded_type.name,
                "is_pretax": ded_type.is_pretax,
                "amount": ded.amount,
                "percentage": ded.percentage,
                "start_date": ded.start_date.isoformat() if ded.start_date else None,
                "end_date": ded.end_date.isoformat() if ded.end_date else None
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
        if employee_id not in self.employees:
            return {"success": False, "error": "Employee not found"}

        entry_id = str(uuid.uuid4())
        w_date = datetime.strptime(work_date, "%Y-%m-%d").date()

        entry = TimeEntry(
            entry_id=entry_id,
            employee_id=employee_id,
            work_date=w_date,
            regular_hours=regular_hours,
            overtime_hours=overtime_hours,
            double_time_hours=double_time_hours,
            sick_hours=sick_hours,
            vacation_hours=vacation_hours,
            holiday_hours=holiday_hours,
            notes=notes
        )

        self.time_entries[entry_id] = entry

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

        for entry in self.time_entries.values():
            if employee_id and entry.employee_id != employee_id:
                continue
            if start_date:
                if entry.work_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if entry.work_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            emp = self.employees.get(entry.employee_id)
            result.append({
                "entry_id": entry.entry_id,
                "employee_id": entry.employee_id,
                "employee_name": f"{emp.first_name} {emp.last_name}" if emp else "Unknown",
                "work_date": entry.work_date.isoformat(),
                "regular_hours": entry.regular_hours,
                "overtime_hours": entry.overtime_hours,
                "double_time_hours": entry.double_time_hours,
                "sick_hours": entry.sick_hours,
                "vacation_hours": entry.vacation_hours,
                "holiday_hours": entry.holiday_hours,
                "total_hours": entry.regular_hours + entry.overtime_hours + entry.double_time_hours + entry.sick_hours + entry.vacation_hours + entry.holiday_hours,
                "approved": entry.approved,
                "notes": entry.notes
            })

        return sorted(result, key=lambda e: e["work_date"], reverse=True)

    # ==================== TAX CALCULATIONS ====================

    def _calculate_federal_tax(
        self,
        annual_gross: float,
        filing_status: FilingStatus,
        allowances: int = 0
    ) -> float:
        """Calculate federal income tax withholding"""
        # Apply standard deduction
        standard_ded = STANDARD_DEDUCTION_2024.get(filing_status, 14600)
        taxable_income = max(0, annual_gross - standard_ded)

        # Get brackets for filing status
        brackets = FEDERAL_TAX_BRACKETS_2024.get(
            filing_status,
            FEDERAL_TAX_BRACKETS_2024[FilingStatus.SINGLE]
        )

        # Calculate tax
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
        # Social Security
        ss_wage_remaining = max(0, SOCIAL_SECURITY_WAGE_BASE - ytd_gross)
        ss_taxable = min(gross_pay, ss_wage_remaining)
        ss_employee = ss_taxable * SOCIAL_SECURITY_RATE
        ss_employer = ss_taxable * SOCIAL_SECURITY_RATE

        # Medicare
        medicare_employee = gross_pay * MEDICARE_RATE
        medicare_employer = gross_pay * MEDICARE_RATE

        # Additional Medicare Tax on wages over $200k
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
        # FUTA
        futa_remaining = max(0, FUTA_WAGE_BASE - ytd_gross)
        futa_taxable = min(gross_pay, futa_remaining)
        futa = futa_taxable * FUTA_RATE

        # SUTA - varies by state, using average rate
        suta_rates = {
            "default": 0.027,  # Average state rate
            "CA": 0.034,
            "TX": 0.027,
            "NY": 0.033,
            "FL": 0.027,
            "IL": 0.0325,
        }
        suta_rate = suta_rates.get(state.upper(), suta_rates["default"])
        suta_wage_base = 15000  # Varies by state

        suta_remaining = max(0, suta_wage_base - ytd_gross)
        suta_taxable = min(gross_pay, suta_remaining)
        suta = suta_taxable * suta_rate

        return round(futa, 2), round(suta, 2)

    def _get_ytd_earnings(self, employee_id: str, as_of_date: date) -> float:
        """Get year-to-date earnings for an employee"""
        year_start = date(as_of_date.year, 1, 1)
        ytd_gross = 0.0

        for pay_run in self.pay_runs.values():
            if pay_run.status not in [PayRunStatus.APPROVED, PayRunStatus.PAID]:
                continue
            if pay_run.pay_date < year_start or pay_run.pay_date >= as_of_date:
                continue

            for line in pay_run.lines:
                if line.employee_id == employee_id:
                    ytd_gross += line.gross_pay

        return ytd_gross

    # ==================== PAY RUNS ====================

    def create_pay_run(
        self,
        pay_period_start: str,
        pay_period_end: str,
        pay_date: str,
        bank_account_id: str,
        employee_ids: List[str] = None  # None = all active employees
    ) -> Dict:
        """Create a new pay run"""
        pay_run_id = str(uuid.uuid4())
        pay_run_number = self.next_pay_run_number
        self.next_pay_run_number += 1

        p_start = datetime.strptime(pay_period_start, "%Y-%m-%d").date()
        p_end = datetime.strptime(pay_period_end, "%Y-%m-%d").date()
        p_date = datetime.strptime(pay_date, "%Y-%m-%d").date()

        # Get employees
        if employee_ids is None:
            emp_list = [e for e in self.employees.values() if e.status == EmployeeStatus.ACTIVE]
        else:
            emp_list = [self.employees[eid] for eid in employee_ids if eid in self.employees]

        lines = []
        for emp in emp_list:
            # Get time entries for period
            total_regular = 0.0
            total_ot = 0.0
            total_dt = 0.0
            total_sick = 0.0
            total_vacation = 0.0
            total_holiday = 0.0

            for entry in self.time_entries.values():
                if entry.employee_id != emp.employee_id:
                    continue
                if not (p_start <= entry.work_date <= p_end):
                    continue

                total_regular += entry.regular_hours
                total_ot += entry.overtime_hours
                total_dt += entry.double_time_hours
                total_sick += entry.sick_hours
                total_vacation += entry.vacation_hours
                total_holiday += entry.holiday_hours

            # If no time entries, use default hours for salaried
            if total_regular == 0 and emp.pay_type == PayType.SALARY:
                total_regular = emp.default_hours

            line = PayRunLine(
                line_id=str(uuid.uuid4()),
                employee_id=emp.employee_id,
                regular_hours=total_regular,
                overtime_hours=total_ot,
                double_time_hours=total_dt,
                sick_hours=total_sick,
                vacation_hours=total_vacation,
                holiday_hours=total_holiday,
                payment_method=emp.payment_method
            )

            lines.append(line)

        pay_run = PayRun(
            pay_run_id=pay_run_id,
            pay_run_number=pay_run_number,
            pay_period_start=p_start,
            pay_period_end=p_end,
            pay_date=p_date,
            bank_account_id=bank_account_id,
            lines=lines
        )

        self.pay_runs[pay_run_id] = pay_run

        return {
            "success": True,
            "pay_run_id": pay_run_id,
            "pay_run_number": pay_run_number,
            "employee_count": len(lines)
        }

    def calculate_pay_run(self, pay_run_id: str) -> Dict:
        """Calculate all pay for a pay run"""
        if pay_run_id not in self.pay_runs:
            return {"success": False, "error": "Pay run not found"}

        pay_run = self.pay_runs[pay_run_id]

        if pay_run.status not in [PayRunStatus.DRAFT, PayRunStatus.CALCULATED]:
            return {"success": False, "error": "Pay run cannot be recalculated"}

        total_gross = 0.0
        total_taxes = 0.0
        total_deductions = 0.0
        total_net = 0.0
        total_employer_taxes = 0.0

        for line in pay_run.lines:
            emp = self.employees.get(line.employee_id)
            if not emp:
                continue

            # Calculate gross pay
            if emp.pay_type == PayType.HOURLY:
                hourly_rate = emp.pay_rate
                line.regular_pay = line.regular_hours * hourly_rate
                line.overtime_pay = line.overtime_hours * hourly_rate * 1.5
                line.double_time_pay = line.double_time_hours * hourly_rate * 2.0
                line.sick_pay = line.sick_hours * hourly_rate
                line.vacation_pay = line.vacation_hours * hourly_rate
                line.holiday_pay = line.holiday_hours * hourly_rate
            else:
                # Salary - convert to per-period
                periods_per_year = {
                    PayFrequency.WEEKLY: 52,
                    PayFrequency.BIWEEKLY: 26,
                    PayFrequency.SEMIMONTHLY: 24,
                    PayFrequency.MONTHLY: 12
                }
                period_pay = emp.pay_rate / periods_per_year.get(emp.pay_frequency, 26)
                line.regular_pay = period_pay

            line.gross_pay = round(
                line.regular_pay + line.overtime_pay + line.double_time_pay +
                line.sick_pay + line.vacation_pay + line.holiday_pay +
                line.bonus + line.commission + line.other_earnings, 2
            )

            # Get YTD for tax calculations
            ytd_gross = self._get_ytd_earnings(emp.employee_id, pay_run.pay_date)

            # Calculate pre-tax deductions
            pretax_deductions = 0.0
            deductions_list = []

            for ded in self.employee_deductions.values():
                if ded.employee_id != emp.employee_id or not ded.is_active:
                    continue

                ded_type = self.deduction_types.get(ded.deduction_type_id)
                if not ded_type:
                    continue

                # Check date range
                if ded.start_date and pay_run.pay_date < ded.start_date:
                    continue
                if ded.end_date and pay_run.pay_date > ded.end_date:
                    continue

                if ded.percentage > 0:
                    ded_amount = line.gross_pay * (ded.percentage / 100)
                else:
                    ded_amount = ded.amount

                if ded_type.is_pretax:
                    pretax_deductions += ded_amount

                deductions_list.append({
                    "code": ded_type.code,
                    "name": ded_type.name,
                    "amount": round(ded_amount, 2),
                    "is_pretax": ded_type.is_pretax
                })

            # Taxable gross after pre-tax deductions
            taxable_gross = line.gross_pay - pretax_deductions

            # Calculate annualized income for tax brackets
            periods_per_year = {
                PayFrequency.WEEKLY: 52,
                PayFrequency.BIWEEKLY: 26,
                PayFrequency.SEMIMONTHLY: 24,
                PayFrequency.MONTHLY: 12
            }
            periods = periods_per_year.get(emp.pay_frequency, 26)
            annual_taxable = taxable_gross * periods

            # Federal income tax
            annual_fed_tax = self._calculate_federal_tax(
                annual_taxable,
                emp.filing_status,
                emp.federal_allowances
            )
            line.federal_income_tax = round(annual_fed_tax / periods, 2)
            line.federal_income_tax += emp.federal_additional_withholding

            # State income tax (simplified - using flat rate)
            state_rates = {
                "CA": 0.093,
                "NY": 0.0685,
                "TX": 0.0,  # No state income tax
                "FL": 0.0,
                "WA": 0.0,
                "NV": 0.0,
                "default": 0.05
            }
            state_rate = state_rates.get(emp.state.upper(), state_rates["default"])
            line.state_income_tax = round(taxable_gross * state_rate, 2)
            line.state_income_tax += emp.state_additional_withholding

            # FICA
            ss_emp, med_emp, ss_er, med_er = self._calculate_fica(taxable_gross, ytd_gross)
            line.social_security_employee = ss_emp
            line.medicare_employee = med_emp
            line.social_security_employer = ss_er
            line.medicare_employer = med_er

            # FUTA / SUTA
            line.futa, line.suta = self._calculate_futa_suta(taxable_gross, ytd_gross, emp.state)

            # Total taxes
            employee_taxes = (
                line.federal_income_tax +
                line.state_income_tax +
                line.social_security_employee +
                line.medicare_employee
            )

            # Post-tax deductions
            posttax_deductions = sum(d["amount"] for d in deductions_list if not d["is_pretax"])
            line.total_deductions = round(pretax_deductions + posttax_deductions, 2)
            line.deductions = deductions_list

            # Net pay
            line.net_pay = round(line.gross_pay - employee_taxes - line.total_deductions, 2)

            # Direct deposit amount
            if emp.payment_method == PaymentMethod.DIRECT_DEPOSIT:
                line.direct_deposit_amount = line.net_pay

            # Employer taxes
            employer_taxes = (
                line.social_security_employer +
                line.medicare_employer +
                line.futa +
                line.suta
            )

            # Add to totals
            total_gross += line.gross_pay
            total_taxes += employee_taxes
            total_deductions += line.total_deductions
            total_net += line.net_pay
            total_employer_taxes += employer_taxes

        # Update pay run totals
        pay_run.total_gross = round(total_gross, 2)
        pay_run.total_taxes = round(total_taxes, 2)
        pay_run.total_deductions = round(total_deductions, 2)
        pay_run.total_net = round(total_net, 2)
        pay_run.total_employer_taxes = round(total_employer_taxes, 2)
        pay_run.status = PayRunStatus.CALCULATED
        pay_run.updated_at = datetime.now()

        return {
            "success": True,
            "pay_run": self._pay_run_to_dict(pay_run)
        }

    def approve_pay_run(self, pay_run_id: str, approved_by: str) -> Dict:
        """Approve a calculated pay run"""
        if pay_run_id not in self.pay_runs:
            return {"success": False, "error": "Pay run not found"}

        pay_run = self.pay_runs[pay_run_id]

        if pay_run.status != PayRunStatus.CALCULATED:
            return {"success": False, "error": "Pay run must be calculated before approval"}

        pay_run.status = PayRunStatus.APPROVED
        pay_run.approved_by = approved_by
        pay_run.approved_at = datetime.now()
        pay_run.updated_at = datetime.now()

        return {
            "success": True,
            "message": "Pay run approved"
        }

    def process_pay_run(self, pay_run_id: str) -> Dict:
        """Process an approved pay run - create checks and ACH"""
        if pay_run_id not in self.pay_runs:
            return {"success": False, "error": "Pay run not found"}

        pay_run = self.pay_runs[pay_run_id]

        if pay_run.status != PayRunStatus.APPROVED:
            return {"success": False, "error": "Pay run must be approved before processing"}

        checks_created = []
        ach_entries = []

        for line in pay_run.lines:
            emp = self.employees.get(line.employee_id)
            if not emp:
                continue

            if line.payment_method == PaymentMethod.CHECK:
                # Create payroll check
                check_result = genfin_banking_service.create_check(
                    bank_account_id=pay_run.bank_account_id,
                    payee_name=f"{emp.first_name} {emp.last_name}",
                    amount=line.net_pay,
                    check_date=pay_run.pay_date.isoformat(),
                    memo=f"Payroll {pay_run.pay_period_start.isoformat()} - {pay_run.pay_period_end.isoformat()}",
                    payee_address_line1=emp.address_line1,
                    payee_city=emp.city,
                    payee_state=emp.state,
                    payee_zip=emp.zip_code,
                    voucher_description=self._generate_pay_stub(line, emp)
                )

                if check_result.get("success"):
                    line.check_id = check_result["check_id"]
                    checks_created.append(check_result["check_number"])

            elif line.payment_method == PaymentMethod.DIRECT_DEPOSIT:
                # Add to ACH batch
                ach_entries.append({
                    "recipient_name": f"{emp.last_name} {emp.first_name}"[:22],
                    "routing_number": emp.bank_routing_number,
                    "account_number": emp.bank_account_number,
                    "account_type": emp.bank_account_type,
                    "amount": line.net_pay,
                    "transaction_code": ACHTransactionCode.CHECKING_CREDIT.value if emp.bank_account_type == "checking" else ACHTransactionCode.SAVINGS_CREDIT.value,
                    "individual_id": emp.employee_number,
                    "individual_name": f"{emp.last_name} {emp.first_name}"[:22]
                })

        # Create ACH batch if there are direct deposit entries
        if ach_entries:
            ach_result = genfin_banking_service.create_ach_batch(
                bank_account_id=pay_run.bank_account_id,
                effective_date=pay_run.pay_date.isoformat(),
                batch_description="PAYROLL",
                entries=ach_entries
            )

            if ach_result.get("success"):
                pay_run.ach_batch_id = ach_result["batch_id"]

        pay_run.status = PayRunStatus.PAID
        pay_run.paid_at = datetime.now()
        pay_run.updated_at = datetime.now()

        return {
            "success": True,
            "checks_created": checks_created,
            "direct_deposits": len(ach_entries),
            "ach_batch_id": pay_run.ach_batch_id
        }

    def _generate_pay_stub(self, line: PayRunLine, emp: Employee) -> str:
        """Generate pay stub text for check voucher"""
        stub = f"""Employee: {emp.first_name} {emp.last_name} ({emp.employee_number})

EARNINGS:
  Regular ({line.regular_hours} hrs): ${line.regular_pay:,.2f}"""

        if line.overtime_hours > 0:
            stub += f"\n  Overtime ({line.overtime_hours} hrs): ${line.overtime_pay:,.2f}"
        if line.sick_hours > 0:
            stub += f"\n  Sick ({line.sick_hours} hrs): ${line.sick_pay:,.2f}"
        if line.vacation_hours > 0:
            stub += f"\n  Vacation ({line.vacation_hours} hrs): ${line.vacation_pay:,.2f}"
        if line.holiday_hours > 0:
            stub += f"\n  Holiday ({line.holiday_hours} hrs): ${line.holiday_pay:,.2f}"

        stub += f"\n  GROSS PAY: ${line.gross_pay:,.2f}"

        stub += f"""

TAXES:
  Federal Income Tax: ${line.federal_income_tax:,.2f}
  State Income Tax: ${line.state_income_tax:,.2f}
  Social Security: ${line.social_security_employee:,.2f}
  Medicare: ${line.medicare_employee:,.2f}"""

        if line.deductions:
            stub += "\n\nDEDUCTIONS:"
            for ded in line.deductions:
                stub += f"\n  {ded['name']}: ${ded['amount']:,.2f}"

        stub += f"""

NET PAY: ${line.net_pay:,.2f}"""

        return stub

    def get_pay_run(self, pay_run_id: str) -> Optional[Dict]:
        """Get pay run by ID"""
        if pay_run_id not in self.pay_runs:
            return None
        return self._pay_run_to_dict(self.pay_runs[pay_run_id])

    def list_pay_runs(
        self,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List pay runs with filtering"""
        result = []

        for pay_run in self.pay_runs.values():
            if status and pay_run.status.value != status:
                continue
            if start_date:
                if pay_run.pay_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if pay_run.pay_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            result.append({
                "pay_run_id": pay_run.pay_run_id,
                "pay_run_number": pay_run.pay_run_number,
                "pay_period": f"{pay_run.pay_period_start.isoformat()} - {pay_run.pay_period_end.isoformat()}",
                "pay_date": pay_run.pay_date.isoformat(),
                "employee_count": len(pay_run.lines),
                "total_gross": pay_run.total_gross,
                "total_net": pay_run.total_net,
                "status": pay_run.status.value,
                "created_at": pay_run.created_at.isoformat()
            })

        return sorted(result, key=lambda p: p["pay_date"], reverse=True)

    # ==================== REPORTS ====================

    def get_employee_ytd(self, employee_id: str, year: int) -> Dict:
        """Get year-to-date earnings and taxes for an employee"""
        if employee_id not in self.employees:
            return {"error": "Employee not found"}

        emp = self.employees[employee_id]

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

        for pay_run in self.pay_runs.values():
            if pay_run.status not in [PayRunStatus.APPROVED, PayRunStatus.PAID]:
                continue
            if pay_run.pay_date.year != year:
                continue

            for line in pay_run.lines:
                if line.employee_id != employee_id:
                    continue

                ytd["regular_pay"] += line.regular_pay
                ytd["overtime_pay"] += line.overtime_pay
                ytd["gross_pay"] += line.gross_pay
                ytd["federal_tax"] += line.federal_income_tax
                ytd["state_tax"] += line.state_income_tax
                ytd["social_security"] += line.social_security_employee
                ytd["medicare"] += line.medicare_employee
                ytd["total_deductions"] += line.total_deductions
                ytd["net_pay"] += line.net_pay

        # Round all values
        for key in ytd:
            ytd[key] = round(ytd[key], 2)

        return {
            "employee_id": employee_id,
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "year": year,
            "ytd": ytd
        }

    def get_payroll_summary(self, start_date: str, end_date: str) -> Dict:
        """Get payroll summary for date range"""
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

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

        for pay_run in self.pay_runs.values():
            if pay_run.status not in [PayRunStatus.APPROVED, PayRunStatus.PAID]:
                continue
            if not (s_date <= pay_run.pay_date <= e_date):
                continue

            summary["pay_run_count"] += 1

            for line in pay_run.lines:
                summary["total_gross"] += line.gross_pay
                summary["total_federal_tax"] += line.federal_income_tax
                summary["total_state_tax"] += line.state_income_tax
                summary["total_social_security_employee"] += line.social_security_employee
                summary["total_medicare_employee"] += line.medicare_employee
                summary["total_social_security_employer"] += line.social_security_employer
                summary["total_medicare_employer"] += line.medicare_employer
                summary["total_futa"] += line.futa
                summary["total_suta"] += line.suta
                summary["total_deductions"] += line.total_deductions
                summary["total_net"] += line.net_pay
                summary["employee_count"].add(line.employee_id)

        summary["employee_count"] = len(summary["employee_count"])

        # Round all numeric values
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
        # Determine date range
        if period.startswith("Q"):
            quarter = int(period[1])
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

    def _employee_to_dict(self, emp: Employee) -> Dict:
        """Convert Employee to dictionary"""
        return {
            "employee_id": emp.employee_id,
            "employee_number": emp.employee_number,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "middle_name": emp.middle_name,
            "full_name": f"{emp.first_name} {emp.last_name}",
            "email": emp.email,
            "phone": emp.phone,
            "address": f"{emp.address_line1}, {emp.city}, {emp.state} {emp.zip_code}",
            "employee_type": emp.employee_type.value,
            "department": emp.department,
            "job_title": emp.job_title,
            "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
            "status": emp.status.value,
            "pay_type": emp.pay_type.value,
            "pay_rate": emp.pay_rate,
            "pay_frequency": emp.pay_frequency.value,
            "filing_status": emp.filing_status.value,
            "payment_method": emp.payment_method.value,
            "has_direct_deposit": emp.payment_method in [PaymentMethod.DIRECT_DEPOSIT, PaymentMethod.BOTH],
            "is_owner": emp.is_owner,
            "created_at": emp.created_at.isoformat(),
            "updated_at": emp.updated_at.isoformat()
        }

    def _pay_run_to_dict(self, pay_run: PayRun) -> Dict:
        """Convert PayRun to dictionary"""
        lines_data = []
        for line in pay_run.lines:
            emp = self.employees.get(line.employee_id)
            lines_data.append({
                "line_id": line.line_id,
                "employee_id": line.employee_id,
                "employee_name": f"{emp.first_name} {emp.last_name}" if emp else "Unknown",
                "regular_hours": line.regular_hours,
                "overtime_hours": line.overtime_hours,
                "gross_pay": line.gross_pay,
                "federal_tax": line.federal_income_tax,
                "state_tax": line.state_income_tax,
                "social_security": line.social_security_employee,
                "medicare": line.medicare_employee,
                "total_deductions": line.total_deductions,
                "net_pay": line.net_pay,
                "payment_method": line.payment_method.value,
                "check_id": line.check_id
            })

        return {
            "pay_run_id": pay_run.pay_run_id,
            "pay_run_number": pay_run.pay_run_number,
            "pay_period_start": pay_run.pay_period_start.isoformat(),
            "pay_period_end": pay_run.pay_period_end.isoformat(),
            "pay_date": pay_run.pay_date.isoformat(),
            "bank_account_id": pay_run.bank_account_id,
            "lines": lines_data,
            "total_gross": pay_run.total_gross,
            "total_taxes": pay_run.total_taxes,
            "total_deductions": pay_run.total_deductions,
            "total_net": pay_run.total_net,
            "total_employer_taxes": pay_run.total_employer_taxes,
            "status": pay_run.status.value,
            "approved_by": pay_run.approved_by,
            "approved_at": pay_run.approved_at.isoformat() if pay_run.approved_at else None,
            "paid_at": pay_run.paid_at.isoformat() if pay_run.paid_at else None,
            "ach_batch_id": pay_run.ach_batch_id,
            "created_at": pay_run.created_at.isoformat()
        }

    def get_service_summary(self) -> Dict:
        """Get GenFin Payroll service summary"""
        active_employees = sum(1 for e in self.employees.values() if e.status == EmployeeStatus.ACTIVE)
        total_paid_ytd = sum(
            pr.total_net for pr in self.pay_runs.values()
            if pr.status == PayRunStatus.PAID and pr.pay_date.year == date.today().year
        )

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
            "total_employees": len(self.employees),
            "active_employees": active_employees,
            "total_pay_runs": len(self.pay_runs),
            "ytd_paid": round(total_paid_ytd, 2),
            "earning_types": len(self.earning_types),
            "deduction_types": len(self.deduction_types)
        }


# Singleton instance
genfin_payroll_service = GenFinPayrollService()
