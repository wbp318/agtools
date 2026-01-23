"""
Enterprise Operations Service for AgTools
Version: 3.9.0

Comprehensive enterprise operations featuring:
- Labor/Crew Management (scheduling, time tracking, certifications, payroll prep)
- Land/Lease Management (lease tracking, rental agreements, landowner payments)
- Cash Flow Forecasting (12-month projections, seasonal planning)
- Multi-Entity Support (multiple farms, partnerships, LLCs)
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import statistics


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

# ----- Labor/Crew Management -----

class EmployeeStatus(Enum):
    """Employee status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SEASONAL = "seasonal"
    TERMINATED = "terminated"


class EmployeeType(Enum):
    """Employee type"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SEASONAL = "seasonal"
    CONTRACT = "contract"
    FAMILY = "family"


class PayType(Enum):
    """Pay type"""
    HOURLY = "hourly"
    SALARY = "salary"
    PIECE_RATE = "piece_rate"
    SHARE = "share"


class CertificationType(Enum):
    """Certification types"""
    PRIVATE_APPLICATOR = "private_applicator"
    COMMERCIAL_APPLICATOR = "commercial_applicator"
    CDL_A = "cdl_a"
    CDL_B = "cdl_b"
    HAZMAT = "hazmat"
    FIRST_AID = "first_aid"
    CPR = "cpr"
    FORKLIFT = "forklift"
    WPS_HANDLER = "wps_handler"
    WPS_WORKER = "wps_worker"
    GRAIN_HANDLING = "grain_handling"
    CONFINED_SPACE = "confined_space"


class TimeEntryType(Enum):
    """Time entry types"""
    REGULAR = "regular"
    OVERTIME = "overtime"
    DOUBLE_TIME = "double_time"
    PTO = "pto"
    SICK = "sick"
    HOLIDAY = "holiday"


@dataclass
class Employee:
    """Employee record"""
    id: str
    first_name: str
    last_name: str
    employee_type: EmployeeType
    status: EmployeeStatus
    pay_type: PayType
    pay_rate: float
    hire_date: date
    phone: str
    email: str
    emergency_contact: str
    emergency_phone: str
    address: str
    certifications: List[str]
    notes: str
    entity_id: str  # Which entity they work for


@dataclass
class Certification:
    """Employee certification"""
    id: str
    employee_id: str
    cert_type: CertificationType
    cert_number: str
    issue_date: date
    expiration_date: date
    issuing_authority: str
    notes: str


@dataclass
class TimeEntry:
    """Time tracking entry"""
    id: str
    employee_id: str
    work_date: date
    start_time: str
    end_time: str
    hours: float
    entry_type: TimeEntryType
    task_description: str
    field_id: Optional[str]
    equipment_id: Optional[str]
    entity_id: str
    approved: bool
    approved_by: Optional[str]


@dataclass
class ScheduleEntry:
    """Work schedule entry"""
    id: str
    employee_id: str
    scheduled_date: date
    start_time: str
    end_time: str
    task: str
    field_id: Optional[str]
    notes: str
    entity_id: str


# ----- Land/Lease Management -----

class LeaseType(Enum):
    """Lease types"""
    CASH_RENT = "cash_rent"
    CROP_SHARE = "crop_share"
    FLEX_LEASE = "flex_lease"
    CUSTOM_FARM = "custom_farm"
    OWNED = "owned"


class PaymentFrequency(Enum):
    """Payment frequency"""
    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    AT_HARVEST = "at_harvest"


class LeaseStatus(Enum):
    """Lease status"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    NEGOTIATING = "negotiating"


@dataclass
class Landowner:
    """Landowner record"""
    id: str
    name: str
    contact_name: str
    phone: str
    email: str
    address: str
    tax_id: str
    payment_method: str  # check, direct_deposit, etc
    bank_info: str  # encrypted/masked
    notes: str


@dataclass
class LandParcel:
    """Land parcel record"""
    id: str
    name: str
    legal_description: str
    county: str
    state: str
    total_acres: float
    tillable_acres: float
    fsa_farm_number: str
    fsa_tract_number: str
    soil_types: List[str]
    ownership_type: LeaseType
    landowner_id: Optional[str]
    entity_id: str
    notes: str


@dataclass
class Lease:
    """Lease agreement"""
    id: str
    parcel_id: str
    landowner_id: str
    lease_type: LeaseType
    status: LeaseStatus
    start_date: date
    end_date: date
    acres: float
    # Cash rent terms
    cash_rent_per_acre: float
    total_annual_rent: float
    payment_frequency: PaymentFrequency
    # Crop share terms
    landlord_share_pct: float
    tenant_share_pct: float
    landlord_pays: List[str]  # What expenses landlord covers
    # Flex lease terms
    base_rent: float
    bonus_structure: str
    # General
    auto_renew: bool
    notice_days: int
    special_terms: str
    document_path: str
    entity_id: str


@dataclass
class LeasePayment:
    """Lease payment record"""
    id: str
    lease_id: str
    landowner_id: str
    payment_date: date
    amount: float
    payment_type: str  # rent, bonus, reimbursement
    check_number: str
    notes: str
    entity_id: str


# ----- Cash Flow Forecasting -----

class CashFlowCategory(Enum):
    """Cash flow categories"""
    # Income
    CROP_SALES = "crop_sales"
    LIVESTOCK_SALES = "livestock_sales"
    GOVERNMENT_PAYMENTS = "government_payments"
    CROP_INSURANCE = "crop_insurance"
    CUSTOM_WORK = "custom_work"
    OTHER_INCOME = "other_income"
    # Expenses
    SEED = "seed"
    FERTILIZER = "fertilizer"
    CHEMICALS = "chemicals"
    FUEL = "fuel"
    REPAIRS = "repairs"
    LAND_RENT = "land_rent"
    LABOR = "labor"
    INSURANCE = "insurance"
    UTILITIES = "utilities"
    LOAN_PAYMENTS = "loan_payments"
    EQUIPMENT_PURCHASE = "equipment_purchase"
    TAXES = "taxes"
    LIVING_EXPENSES = "living_expenses"
    OTHER_EXPENSE = "other_expense"


class TransactionStatus(Enum):
    """Transaction status"""
    PROJECTED = "projected"
    COMMITTED = "committed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CashFlowEntry:
    """Cash flow entry"""
    id: str
    entity_id: str
    category: CashFlowCategory
    description: str
    amount: float  # Positive for income, negative for expense
    transaction_date: date
    status: TransactionStatus
    recurring: bool
    recurrence_pattern: str  # monthly, quarterly, annual
    linked_lease_id: Optional[str]
    linked_loan_id: Optional[str]
    notes: str


@dataclass
class Loan:
    """Loan record"""
    id: str
    entity_id: str
    lender: str
    loan_type: str  # operating, equipment, real_estate
    original_amount: float
    current_balance: float
    interest_rate: float
    payment_amount: float
    payment_frequency: PaymentFrequency
    next_payment_date: date
    maturity_date: date
    collateral: str
    notes: str


# ----- Multi-Entity Support -----

class EntityType(Enum):
    """Entity types"""
    SOLE_PROPRIETOR = "sole_proprietor"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    S_CORP = "s_corp"
    C_CORP = "c_corp"
    TRUST = "trust"
    FAMILY_LP = "family_lp"


@dataclass
class FarmEntity:
    """Farm entity record"""
    id: str
    name: str
    entity_type: EntityType
    tax_id: str
    state_of_formation: str
    formation_date: date
    fiscal_year_end: str  # "12/31" or "06/30" etc
    primary_contact: str
    phone: str
    email: str
    address: str
    owners: List[Dict[str, Any]]  # [{name, ownership_pct, role}]
    bank_accounts: List[str]
    is_active: bool
    notes: str


@dataclass
class EntityAllocation:
    """Allocation of resources between entities"""
    id: str
    source_entity_id: str
    target_entity_id: str
    resource_type: str  # equipment, labor, land
    resource_id: str
    allocation_pct: float
    effective_date: date
    end_date: Optional[date]
    notes: str


# =============================================================================
# DEFAULT DATA
# =============================================================================

# Louisiana average cash rents by region (2024)
CASH_RENT_AVERAGES = {
    "north_louisiana": {
        "irrigated_row_crop": 175,
        "dryland_row_crop": 125,
        "pasture": 35
    },
    "central_louisiana": {
        "irrigated_row_crop": 185,
        "dryland_row_crop": 135,
        "pasture": 40
    },
    "south_louisiana": {
        "irrigated_row_crop": 200,
        "dryland_row_crop": 150,
        "rice": 225,
        "sugarcane": 250,
        "pasture": 45
    },
    "delta_region": {
        "irrigated_row_crop": 220,
        "dryland_row_crop": 160,
        "rice": 240
    }
}

# Typical farm expense timing
EXPENSE_TIMING = {
    CashFlowCategory.SEED: [2, 3, 4],  # Feb-Apr
    CashFlowCategory.FERTILIZER: [1, 2, 3, 4, 5],  # Jan-May
    CashFlowCategory.CHEMICALS: [3, 4, 5, 6, 7],  # Mar-Jul
    CashFlowCategory.FUEL: list(range(1, 13)),  # Year-round
    CashFlowCategory.LAND_RENT: [1, 3, 11],  # Jan, Mar, Nov typical
    CashFlowCategory.LABOR: list(range(1, 13)),  # Year-round
    CashFlowCategory.CROP_INSURANCE: [3, 4],  # Mar-Apr
    CashFlowCategory.TAXES: [4, 6, 9, 12],  # Quarterly estimates
}

# Typical income timing
INCOME_TIMING = {
    CashFlowCategory.CROP_SALES: [9, 10, 11, 12, 1, 2],  # Harvest through Feb
    CashFlowCategory.GOVERNMENT_PAYMENTS: [10, 11, 12, 2],
    CashFlowCategory.CROP_INSURANCE: [11, 12, 1],  # After harvest
}

# Certification validity periods (years)
CERT_VALIDITY = {
    CertificationType.PRIVATE_APPLICATOR: 5,
    CertificationType.COMMERCIAL_APPLICATOR: 3,
    CertificationType.CDL_A: 5,
    CertificationType.CDL_B: 5,
    CertificationType.HAZMAT: 2,
    CertificationType.FIRST_AID: 2,
    CertificationType.CPR: 2,
    CertificationType.FORKLIFT: 3,
    CertificationType.WPS_HANDLER: 5,
    CertificationType.WPS_WORKER: 5,
    CertificationType.GRAIN_HANDLING: 3,
    CertificationType.CONFINED_SPACE: 1,
}


# =============================================================================
# ENTERPRISE OPERATIONS SERVICE CLASS
# =============================================================================

class EnterpriseOperationsService:
    """Enterprise operations management service"""

    def __init__(self):
        # Entities
        self.entities: Dict[str, FarmEntity] = {}
        self.allocations: Dict[str, EntityAllocation] = {}

        # Labor
        self.employees: Dict[str, Employee] = {}
        self.certifications: Dict[str, Certification] = {}
        self.time_entries: Dict[str, TimeEntry] = {}
        self.schedules: Dict[str, ScheduleEntry] = {}

        # Land
        self.landowners: Dict[str, Landowner] = {}
        self.parcels: Dict[str, LandParcel] = {}
        self.leases: Dict[str, Lease] = {}
        self.lease_payments: Dict[str, LeasePayment] = {}

        # Cash Flow
        self.cash_flow_entries: Dict[str, CashFlowEntry] = {}
        self.loans: Dict[str, Loan] = {}

        self._counters = {
            "entity": 0, "employee": 0, "cert": 0, "time": 0, "schedule": 0,
            "landowner": 0, "parcel": 0, "lease": 0, "payment": 0,
            "cashflow": 0, "loan": 0, "allocation": 0
        }

        # Create default entity
        self._create_default_entity()

    def _next_id(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix.upper()}-{self._counters[prefix]:04d}"

    def _create_default_entity(self):
        """Create a default farming entity"""
        entity = FarmEntity(
            id="ENTITY-0001",
            name="Main Farm Operation",
            entity_type=EntityType.SOLE_PROPRIETOR,
            tax_id="",
            state_of_formation="LA",
            formation_date=date(2000, 1, 1),
            fiscal_year_end="12/31",
            primary_contact="",
            phone="",
            email="",
            address="",
            owners=[],
            bank_accounts=[],
            is_active=True,
            notes="Default entity"
        )
        self.entities["ENTITY-0001"] = entity
        self._counters["entity"] = 1

    # =========================================================================
    # ENTITY MANAGEMENT
    # =========================================================================

    def create_entity(
        self,
        name: str,
        entity_type: str,
        tax_id: str = "",
        state_of_formation: str = "LA",
        fiscal_year_end: str = "12/31",
        owners: List[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new farming entity"""
        try:
            etype = EntityType(entity_type)
        except ValueError:
            return {"error": f"Invalid entity type: {entity_type}"}

        entity_id = self._next_id("entity")

        entity = FarmEntity(
            id=entity_id,
            name=name,
            entity_type=etype,
            tax_id=tax_id,
            state_of_formation=state_of_formation,
            formation_date=kwargs.get("formation_date", date.today()),
            fiscal_year_end=fiscal_year_end,
            primary_contact=kwargs.get("primary_contact", ""),
            phone=kwargs.get("phone", ""),
            email=kwargs.get("email", ""),
            address=kwargs.get("address", ""),
            owners=owners or [],
            bank_accounts=kwargs.get("bank_accounts", []),
            is_active=True,
            notes=kwargs.get("notes", "")
        )

        self.entities[entity_id] = entity

        return {
            "id": entity_id,
            "name": name,
            "entity_type": entity_type,
            "state": state_of_formation,
            "owners": owners or [],
            "message": f"Entity '{name}' created successfully"
        }

    def get_entities(self, active_only: bool = True) -> Dict[str, Any]:
        """Get all entities"""
        entities = []
        for entity in self.entities.values():
            if active_only and not entity.is_active:
                continue
            entities.append({
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type.value,
                "tax_id": entity.tax_id[-4:] + "****" if entity.tax_id else "",
                "owners": entity.owners,
                "is_active": entity.is_active
            })

        return {
            "count": len(entities),
            "entities": entities
        }

    def create_allocation(
        self,
        source_entity_id: str,
        target_entity_id: str,
        resource_type: str,
        resource_id: str,
        allocation_pct: float,
        effective_date: date
    ) -> Dict[str, Any]:
        """Create resource allocation between entities"""
        if source_entity_id not in self.entities:
            return {"error": f"Source entity {source_entity_id} not found"}
        if target_entity_id not in self.entities:
            return {"error": f"Target entity {target_entity_id} not found"}

        alloc_id = self._next_id("allocation")

        allocation = EntityAllocation(
            id=alloc_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            resource_type=resource_type,
            resource_id=resource_id,
            allocation_pct=allocation_pct,
            effective_date=effective_date,
            end_date=None,
            notes=""
        )

        self.allocations[alloc_id] = allocation

        return {
            "id": alloc_id,
            "source": self.entities[source_entity_id].name,
            "target": self.entities[target_entity_id].name,
            "resource_type": resource_type,
            "allocation_pct": allocation_pct,
            "message": f"Allocated {allocation_pct}% of {resource_type} from {self.entities[source_entity_id].name} to {self.entities[target_entity_id].name}"
        }

    # =========================================================================
    # LABOR/CREW MANAGEMENT
    # =========================================================================

    def add_employee(
        self,
        first_name: str,
        last_name: str,
        employee_type: str,
        pay_type: str,
        pay_rate: float,
        phone: str = "",
        email: str = "",
        entity_id: str = "ENTITY-0001",
        **kwargs
    ) -> Dict[str, Any]:
        """Add a new employee"""
        try:
            emp_type = EmployeeType(employee_type)
            p_type = PayType(pay_type)
        except ValueError as e:
            return {"error": str(e)}

        emp_id = self._next_id("employee")

        employee = Employee(
            id=emp_id,
            first_name=first_name,
            last_name=last_name,
            employee_type=emp_type,
            status=EmployeeStatus.ACTIVE,
            pay_type=p_type,
            pay_rate=pay_rate,
            hire_date=kwargs.get("hire_date", date.today()),
            phone=phone,
            email=email,
            emergency_contact=kwargs.get("emergency_contact", ""),
            emergency_phone=kwargs.get("emergency_phone", ""),
            address=kwargs.get("address", ""),
            certifications=[],
            notes=kwargs.get("notes", ""),
            entity_id=entity_id
        )

        self.employees[emp_id] = employee

        return {
            "id": emp_id,
            "name": f"{first_name} {last_name}",
            "type": employee_type,
            "pay": f"${pay_rate:.2f}/{pay_type}",
            "entity": self.entities.get(entity_id, {}).name if entity_id in self.entities else entity_id,
            "message": f"Employee {first_name} {last_name} added"
        }

    def add_certification(
        self,
        employee_id: str,
        cert_type: str,
        cert_number: str,
        issue_date: date,
        expiration_date: date,
        issuing_authority: str = ""
    ) -> Dict[str, Any]:
        """Add certification to employee"""
        if employee_id not in self.employees:
            return {"error": f"Employee {employee_id} not found"}

        try:
            ctype = CertificationType(cert_type)
        except ValueError:
            return {"error": f"Invalid certification type: {cert_type}"}

        cert_id = self._next_id("cert")

        cert = Certification(
            id=cert_id,
            employee_id=employee_id,
            cert_type=ctype,
            cert_number=cert_number,
            issue_date=issue_date,
            expiration_date=expiration_date,
            issuing_authority=issuing_authority,
            notes=""
        )

        self.certifications[cert_id] = cert

        emp = self.employees[employee_id]
        emp.certifications.append(cert_type)

        days_until_exp = (expiration_date - date.today()).days

        return {
            "id": cert_id,
            "employee": f"{emp.first_name} {emp.last_name}",
            "certification": cert_type,
            "expires": expiration_date.isoformat(),
            "days_until_expiration": days_until_exp,
            "status": "valid" if days_until_exp > 90 else "expiring_soon" if days_until_exp > 0 else "expired",
            "message": f"Certification added for {emp.first_name} {emp.last_name}"
        }

    def record_time(
        self,
        employee_id: str,
        work_date: date,
        hours: float,
        task_description: str,
        start_time: str = "07:00",
        end_time: str = "17:00",
        entry_type: str = "regular",
        field_id: str = None,
        equipment_id: str = None,
        entity_id: str = "ENTITY-0001"
    ) -> Dict[str, Any]:
        """Record time entry for employee"""
        if employee_id not in self.employees:
            return {"error": f"Employee {employee_id} not found"}

        try:
            etype = TimeEntryType(entry_type)
        except ValueError:
            return {"error": f"Invalid entry type: {entry_type}"}

        time_id = self._next_id("time")
        emp = self.employees[employee_id]

        # Calculate pay
        if etype == TimeEntryType.OVERTIME:
            rate_multiplier = 1.5
        elif etype == TimeEntryType.DOUBLE_TIME:
            rate_multiplier = 2.0
        else:
            rate_multiplier = 1.0

        if emp.pay_type == PayType.HOURLY:
            gross_pay = hours * emp.pay_rate * rate_multiplier
        else:
            gross_pay = 0  # Salary employees tracked differently

        entry = TimeEntry(
            id=time_id,
            employee_id=employee_id,
            work_date=work_date,
            start_time=start_time,
            end_time=end_time,
            hours=hours,
            entry_type=etype,
            task_description=task_description,
            field_id=field_id,
            equipment_id=equipment_id,
            entity_id=entity_id,
            approved=False,
            approved_by=None
        )

        self.time_entries[time_id] = entry

        return {
            "id": time_id,
            "employee": f"{emp.first_name} {emp.last_name}",
            "date": work_date.isoformat(),
            "hours": hours,
            "type": entry_type,
            "task": task_description,
            "gross_pay": round(gross_pay, 2) if emp.pay_type == PayType.HOURLY else "salary",
            "status": "pending_approval",
            "message": f"Time entry recorded: {hours} hours for {emp.first_name}"
        }

    def get_timesheet(
        self,
        employee_id: str = None,
        start_date: date = None,
        end_date: date = None,
        entity_id: str = None
    ) -> Dict[str, Any]:
        """Get timesheet summary"""
        if start_date is None:
            # Default to current week
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
        if end_date is None:
            end_date = start_date + timedelta(days=6)

        entries = []
        for entry in self.time_entries.values():
            if start_date <= entry.work_date <= end_date:
                if employee_id and entry.employee_id != employee_id:
                    continue
                if entity_id and entry.entity_id != entity_id:
                    continue

                emp = self.employees.get(entry.employee_id)
                entries.append({
                    "id": entry.id,
                    "employee": f"{emp.first_name} {emp.last_name}" if emp else entry.employee_id,
                    "date": entry.work_date.isoformat(),
                    "hours": entry.hours,
                    "type": entry.entry_type.value,
                    "task": entry.task_description,
                    "approved": entry.approved
                })

        # Summarize by employee
        by_employee = {}
        for entry in entries:
            emp_name = entry["employee"]
            if emp_name not in by_employee:
                by_employee[emp_name] = {"regular": 0, "overtime": 0, "total": 0}
            by_employee[emp_name]["total"] += entry["hours"]
            if entry["type"] == "overtime":
                by_employee[emp_name]["overtime"] += entry["hours"]
            else:
                by_employee[emp_name]["regular"] += entry["hours"]

        return {
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "entries_count": len(entries),
            "by_employee": by_employee,
            "total_hours": sum(e["hours"] for e in entries),
            "pending_approval": len([e for e in entries if not e["approved"]]),
            "entries": entries
        }

    def create_schedule(
        self,
        employee_id: str,
        scheduled_date: date,
        start_time: str,
        end_time: str,
        task: str,
        field_id: str = None,
        entity_id: str = "ENTITY-0001"
    ) -> Dict[str, Any]:
        """Create work schedule entry"""
        if employee_id not in self.employees:
            return {"error": f"Employee {employee_id} not found"}

        sched_id = self._next_id("schedule")
        emp = self.employees[employee_id]

        schedule = ScheduleEntry(
            id=sched_id,
            employee_id=employee_id,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            task=task,
            field_id=field_id,
            notes="",
            entity_id=entity_id
        )

        self.schedules[sched_id] = schedule

        return {
            "id": sched_id,
            "employee": f"{emp.first_name} {emp.last_name}",
            "date": scheduled_date.isoformat(),
            "time": f"{start_time} - {end_time}",
            "task": task,
            "message": f"Scheduled {emp.first_name} for {task} on {scheduled_date}"
        }

    def get_crew_schedule(
        self,
        start_date: date,
        end_date: date = None,
        entity_id: str = None
    ) -> Dict[str, Any]:
        """Get crew schedule for date range"""
        if end_date is None:
            end_date = start_date + timedelta(days=6)

        schedules = []
        for sched in self.schedules.values():
            if start_date <= sched.scheduled_date <= end_date:
                if entity_id and sched.entity_id != entity_id:
                    continue
                emp = self.employees.get(sched.employee_id)
                schedules.append({
                    "id": sched.id,
                    "employee": f"{emp.first_name} {emp.last_name}" if emp else sched.employee_id,
                    "date": sched.scheduled_date.isoformat(),
                    "time": f"{sched.start_time} - {sched.end_time}",
                    "task": sched.task
                })

        # Organize by date
        by_date = {}
        for sched in schedules:
            d = sched["date"]
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(sched)

        return {
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "total_scheduled": len(schedules),
            "by_date": by_date
        }

    def get_certification_alerts(self, days_ahead: int = 90) -> Dict[str, Any]:
        """Get certification expiration alerts"""
        alerts = []
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        for cert in self.certifications.values():
            if cert.expiration_date <= cutoff:
                emp = self.employees.get(cert.employee_id)
                days_until = (cert.expiration_date - today).days

                if days_until < 0:
                    urgency = "expired"
                elif days_until <= 30:
                    urgency = "critical"
                elif days_until <= 60:
                    urgency = "high"
                else:
                    urgency = "normal"

                alerts.append({
                    "employee": f"{emp.first_name} {emp.last_name}" if emp else cert.employee_id,
                    "certification": cert.cert_type.value,
                    "expires": cert.expiration_date.isoformat(),
                    "days_until": days_until,
                    "urgency": urgency
                })

        alerts.sort(key=lambda x: x["days_until"])

        return {
            "as_of": today.isoformat(),
            "alerts_count": len(alerts),
            "expired": len([a for a in alerts if a["urgency"] == "expired"]),
            "critical": len([a for a in alerts if a["urgency"] == "critical"]),
            "alerts": alerts
        }

    def generate_payroll_summary(
        self,
        pay_period_start: date,
        pay_period_end: date,
        entity_id: str = None
    ) -> Dict[str, Any]:
        """Generate payroll summary for pay period"""
        summaries = []

        for emp_id, emp in self.employees.items():
            if emp.status != EmployeeStatus.ACTIVE:
                continue
            if entity_id and emp.entity_id != entity_id:
                continue

            # Get time entries for period
            regular_hours = 0
            overtime_hours = 0
            pto_hours = 0

            for entry in self.time_entries.values():
                if entry.employee_id != emp_id:
                    continue
                if not (pay_period_start <= entry.work_date <= pay_period_end):
                    continue

                if entry.entry_type == TimeEntryType.OVERTIME:
                    overtime_hours += entry.hours
                elif entry.entry_type in [TimeEntryType.PTO, TimeEntryType.SICK]:
                    pto_hours += entry.hours
                else:
                    regular_hours += entry.hours

            # Calculate pay
            if emp.pay_type == PayType.HOURLY:
                regular_pay = regular_hours * emp.pay_rate
                overtime_pay = overtime_hours * emp.pay_rate * 1.5
                pto_pay = pto_hours * emp.pay_rate
                gross_pay = regular_pay + overtime_pay + pto_pay
            else:
                # Salary - assume bi-weekly
                gross_pay = emp.pay_rate / 26 if emp.pay_rate > 1000 else emp.pay_rate
                regular_pay = gross_pay
                overtime_pay = 0
                pto_pay = 0

            if regular_hours > 0 or emp.pay_type == PayType.SALARY:
                summaries.append({
                    "employee_id": emp_id,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "pay_type": emp.pay_type.value,
                    "regular_hours": regular_hours,
                    "overtime_hours": overtime_hours,
                    "pto_hours": pto_hours,
                    "regular_pay": round(regular_pay, 2),
                    "overtime_pay": round(overtime_pay, 2),
                    "gross_pay": round(gross_pay, 2)
                })

        total_gross = sum(s["gross_pay"] for s in summaries)

        return {
            "pay_period": f"{pay_period_start.isoformat()} to {pay_period_end.isoformat()}",
            "employees": len(summaries),
            "total_regular_hours": sum(s["regular_hours"] for s in summaries),
            "total_overtime_hours": sum(s["overtime_hours"] for s in summaries),
            "total_gross_pay": round(total_gross, 2),
            "summaries": summaries
        }

    # =========================================================================
    # LAND/LEASE MANAGEMENT
    # =========================================================================

    def add_landowner(
        self,
        name: str,
        contact_name: str = "",
        phone: str = "",
        email: str = "",
        address: str = "",
        payment_method: str = "check",
        **kwargs
    ) -> Dict[str, Any]:
        """Add a landowner"""
        owner_id = self._next_id("landowner")

        landowner = Landowner(
            id=owner_id,
            name=name,
            contact_name=contact_name or name,
            phone=phone,
            email=email,
            address=address,
            tax_id=kwargs.get("tax_id", ""),
            payment_method=payment_method,
            bank_info="",
            notes=kwargs.get("notes", "")
        )

        self.landowners[owner_id] = landowner

        return {
            "id": owner_id,
            "name": name,
            "contact": contact_name,
            "phone": phone,
            "payment_method": payment_method,
            "message": f"Landowner {name} added"
        }

    def add_land_parcel(
        self,
        name: str,
        total_acres: float,
        tillable_acres: float,
        county: str,
        ownership_type: str,
        landowner_id: str = None,
        entity_id: str = "ENTITY-0001",
        **kwargs
    ) -> Dict[str, Any]:
        """Add a land parcel"""
        try:
            own_type = LeaseType(ownership_type)
        except ValueError:
            return {"error": f"Invalid ownership type: {ownership_type}"}

        parcel_id = self._next_id("parcel")

        parcel = LandParcel(
            id=parcel_id,
            name=name,
            legal_description=kwargs.get("legal_description", ""),
            county=county,
            state=kwargs.get("state", "LA"),
            total_acres=total_acres,
            tillable_acres=tillable_acres,
            fsa_farm_number=kwargs.get("fsa_farm_number", ""),
            fsa_tract_number=kwargs.get("fsa_tract_number", ""),
            soil_types=kwargs.get("soil_types", []),
            ownership_type=own_type,
            landowner_id=landowner_id,
            entity_id=entity_id,
            notes=kwargs.get("notes", "")
        )

        self.parcels[parcel_id] = parcel

        return {
            "id": parcel_id,
            "name": name,
            "total_acres": total_acres,
            "tillable_acres": tillable_acres,
            "county": county,
            "ownership": ownership_type,
            "message": f"Parcel {name} ({tillable_acres} tillable acres) added"
        }

    def create_lease(
        self,
        parcel_id: str,
        landowner_id: str,
        lease_type: str,
        start_date: date,
        end_date: date,
        acres: float,
        cash_rent_per_acre: float = 0,
        payment_frequency: str = "annual",
        entity_id: str = "ENTITY-0001",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a lease agreement"""
        if parcel_id not in self.parcels:
            return {"error": f"Parcel {parcel_id} not found"}
        if landowner_id not in self.landowners:
            return {"error": f"Landowner {landowner_id} not found"}

        try:
            l_type = LeaseType(lease_type)
            pay_freq = PaymentFrequency(payment_frequency)
        except ValueError as e:
            return {"error": str(e)}

        lease_id = self._next_id("lease")
        total_rent = acres * cash_rent_per_acre

        lease = Lease(
            id=lease_id,
            parcel_id=parcel_id,
            landowner_id=landowner_id,
            lease_type=l_type,
            status=LeaseStatus.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            acres=acres,
            cash_rent_per_acre=cash_rent_per_acre,
            total_annual_rent=total_rent,
            payment_frequency=pay_freq,
            landlord_share_pct=kwargs.get("landlord_share_pct", 0),
            tenant_share_pct=kwargs.get("tenant_share_pct", 100),
            landlord_pays=kwargs.get("landlord_pays", []),
            base_rent=kwargs.get("base_rent", 0),
            bonus_structure=kwargs.get("bonus_structure", ""),
            auto_renew=kwargs.get("auto_renew", True),
            notice_days=kwargs.get("notice_days", 90),
            special_terms=kwargs.get("special_terms", ""),
            document_path=kwargs.get("document_path", ""),
            entity_id=entity_id
        )

        self.leases[lease_id] = lease

        parcel = self.parcels[parcel_id]
        landowner = self.landowners[landowner_id]

        return {
            "id": lease_id,
            "parcel": parcel.name,
            "landowner": landowner.name,
            "lease_type": lease_type,
            "acres": acres,
            "rent_per_acre": cash_rent_per_acre,
            "total_annual_rent": total_rent,
            "term": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "message": f"Lease created: {acres} acres from {landowner.name} at ${cash_rent_per_acre}/acre"
        }

    def record_lease_payment(
        self,
        lease_id: str,
        payment_date: date,
        amount: float,
        payment_type: str = "rent",
        check_number: str = "",
        notes: str = ""
    ) -> Dict[str, Any]:
        """Record a lease payment"""
        if lease_id not in self.leases:
            return {"error": f"Lease {lease_id} not found"}

        lease = self.leases[lease_id]
        payment_id = self._next_id("payment")

        payment = LeasePayment(
            id=payment_id,
            lease_id=lease_id,
            landowner_id=lease.landowner_id,
            payment_date=payment_date,
            amount=amount,
            payment_type=payment_type,
            check_number=check_number,
            notes=notes,
            entity_id=lease.entity_id
        )

        self.lease_payments[payment_id] = payment

        landowner = self.landowners.get(lease.landowner_id)

        return {
            "id": payment_id,
            "lease_id": lease_id,
            "landowner": landowner.name if landowner else lease.landowner_id,
            "amount": amount,
            "date": payment_date.isoformat(),
            "type": payment_type,
            "check_number": check_number,
            "message": f"Payment of ${amount:,.2f} recorded"
        }

    def get_lease_summary(self, entity_id: str = None) -> Dict[str, Any]:
        """Get summary of all leases"""
        leases = []
        total_acres = 0
        total_rent = 0
        owned_acres = 0

        for lease in self.leases.values():
            if entity_id and lease.entity_id != entity_id:
                continue
            if lease.status != LeaseStatus.ACTIVE:
                continue

            parcel = self.parcels.get(lease.parcel_id)
            landowner = self.landowners.get(lease.landowner_id)

            leases.append({
                "id": lease.id,
                "parcel": parcel.name if parcel else lease.parcel_id,
                "landowner": landowner.name if landowner else lease.landowner_id,
                "acres": lease.acres,
                "type": lease.lease_type.value,
                "rent_per_acre": lease.cash_rent_per_acre,
                "annual_rent": lease.total_annual_rent,
                "expires": lease.end_date.isoformat()
            })

            if lease.lease_type == LeaseType.OWNED:
                owned_acres += lease.acres
            else:
                total_acres += lease.acres
                total_rent += lease.total_annual_rent

        # Upcoming expirations
        today = date.today()
        expiring = [lease for lease in leases if datetime.strptime(lease["expires"], "%Y-%m-%d").date() <= today + timedelta(days=365)]

        return {
            "as_of": today.isoformat(),
            "summary": {
                "total_leased_acres": total_acres,
                "owned_acres": owned_acres,
                "total_annual_rent": round(total_rent, 2),
                "avg_rent_per_acre": round(total_rent / total_acres, 2) if total_acres > 0 else 0,
                "active_leases": len(leases)
            },
            "expiring_within_year": len(expiring),
            "leases": leases
        }

    def get_lease_payment_schedule(self, year: int = None) -> Dict[str, Any]:
        """Get payment schedule for all leases"""
        if year is None:
            year = date.today().year

        schedule = []

        for lease in self.leases.values():
            if lease.status != LeaseStatus.ACTIVE:
                continue

            landowner = self.landowners.get(lease.landowner_id)
            parcel = self.parcels.get(lease.parcel_id)

            # Determine payment dates based on frequency
            if lease.payment_frequency == PaymentFrequency.ANNUAL:
                payment_months = [lease.start_date.month]
            elif lease.payment_frequency == PaymentFrequency.SEMI_ANNUAL:
                payment_months = [lease.start_date.month, (lease.start_date.month + 6 - 1) % 12 + 1]
            elif lease.payment_frequency == PaymentFrequency.QUARTERLY:
                payment_months = [lease.start_date.month]
                for i in range(3):
                    payment_months.append((payment_months[-1] + 3 - 1) % 12 + 1)
            else:
                payment_months = list(range(1, 13))

            payment_amount = lease.total_annual_rent / len(payment_months)

            for month in payment_months:
                schedule.append({
                    "lease_id": lease.id,
                    "parcel": parcel.name if parcel else lease.parcel_id,
                    "landowner": landowner.name if landowner else lease.landowner_id,
                    "payment_date": date(year, month, 1).isoformat(),
                    "amount": round(payment_amount, 2)
                })

        schedule.sort(key=lambda x: x["payment_date"])

        # Sum by month
        by_month = {}
        for item in schedule:
            month = item["payment_date"][:7]
            if month not in by_month:
                by_month[month] = 0
            by_month[month] += item["amount"]

        return {
            "year": year,
            "total_payments": len(schedule),
            "total_amount": sum(s["amount"] for s in schedule),
            "by_month": {k: round(v, 2) for k, v in by_month.items()},
            "schedule": schedule
        }

    def get_rent_comparison(self, region: str = "delta_region") -> Dict[str, Any]:
        """Compare your rents to regional averages"""
        regional_avg = CASH_RENT_AVERAGES.get(region, CASH_RENT_AVERAGES["delta_region"])

        comparisons = []
        for lease in self.leases.values():
            if lease.status != LeaseStatus.ACTIVE:
                continue
            if lease.lease_type != LeaseType.CASH_RENT:
                continue

            parcel = self.parcels.get(lease.parcel_id)

            # Assume irrigated row crop for comparison
            regional_rate = regional_avg.get("irrigated_row_crop", 200)
            difference = lease.cash_rent_per_acre - regional_rate
            pct_diff = (difference / regional_rate * 100) if regional_rate > 0 else 0

            comparisons.append({
                "parcel": parcel.name if parcel else lease.parcel_id,
                "your_rate": lease.cash_rent_per_acre,
                "regional_avg": regional_rate,
                "difference": round(difference, 2),
                "pct_difference": round(pct_diff, 1),
                "status": "above_avg" if difference > 0 else "below_avg" if difference < 0 else "at_avg"
            })

        avg_your_rate = statistics.mean([c["your_rate"] for c in comparisons]) if comparisons else 0

        return {
            "region": region,
            "regional_averages": regional_avg,
            "your_average_rate": round(avg_your_rate, 2),
            "comparisons": comparisons
        }

    # =========================================================================
    # CASH FLOW FORECASTING
    # =========================================================================

    def add_cash_flow_entry(
        self,
        category: str,
        description: str,
        amount: float,
        transaction_date: date,
        status: str = "projected",
        recurring: bool = False,
        recurrence_pattern: str = "",
        entity_id: str = "ENTITY-0001",
        **kwargs
    ) -> Dict[str, Any]:
        """Add a cash flow entry"""
        try:
            cat = CashFlowCategory(category)
            stat = TransactionStatus(status)
        except ValueError as e:
            return {"error": str(e)}

        entry_id = self._next_id("cashflow")

        # Make amount negative for expenses
        expense_categories = [
            CashFlowCategory.SEED, CashFlowCategory.FERTILIZER, CashFlowCategory.CHEMICALS,
            CashFlowCategory.FUEL, CashFlowCategory.REPAIRS, CashFlowCategory.LAND_RENT,
            CashFlowCategory.LABOR, CashFlowCategory.INSURANCE, CashFlowCategory.UTILITIES,
            CashFlowCategory.LOAN_PAYMENTS, CashFlowCategory.EQUIPMENT_PURCHASE,
            CashFlowCategory.TAXES, CashFlowCategory.LIVING_EXPENSES, CashFlowCategory.OTHER_EXPENSE
        ]

        if cat in expense_categories and amount > 0:
            amount = -amount

        entry = CashFlowEntry(
            id=entry_id,
            entity_id=entity_id,
            category=cat,
            description=description,
            amount=amount,
            transaction_date=transaction_date,
            status=stat,
            recurring=recurring,
            recurrence_pattern=recurrence_pattern,
            linked_lease_id=kwargs.get("linked_lease_id"),
            linked_loan_id=kwargs.get("linked_loan_id"),
            notes=kwargs.get("notes", "")
        )

        self.cash_flow_entries[entry_id] = entry

        return {
            "id": entry_id,
            "category": category,
            "description": description,
            "amount": amount,
            "date": transaction_date.isoformat(),
            "type": "income" if amount > 0 else "expense",
            "status": status,
            "message": f"Cash flow entry added: {description} ${abs(amount):,.2f}"
        }

    def add_loan(
        self,
        lender: str,
        loan_type: str,
        original_amount: float,
        current_balance: float,
        interest_rate: float,
        payment_amount: float,
        payment_frequency: str,
        next_payment_date: date,
        maturity_date: date,
        entity_id: str = "ENTITY-0001",
        **kwargs
    ) -> Dict[str, Any]:
        """Add a loan record"""
        try:
            pay_freq = PaymentFrequency(payment_frequency)
        except ValueError:
            return {"error": f"Invalid payment frequency: {payment_frequency}"}

        loan_id = self._next_id("loan")

        loan = Loan(
            id=loan_id,
            entity_id=entity_id,
            lender=lender,
            loan_type=loan_type,
            original_amount=original_amount,
            current_balance=current_balance,
            interest_rate=interest_rate,
            payment_amount=payment_amount,
            payment_frequency=pay_freq,
            next_payment_date=next_payment_date,
            maturity_date=maturity_date,
            collateral=kwargs.get("collateral", ""),
            notes=kwargs.get("notes", "")
        )

        self.loans[loan_id] = loan

        return {
            "id": loan_id,
            "lender": lender,
            "type": loan_type,
            "balance": current_balance,
            "rate": f"{interest_rate}%",
            "payment": payment_amount,
            "next_payment": next_payment_date.isoformat(),
            "message": f"Loan from {lender} added: ${current_balance:,.2f} at {interest_rate}%"
        }

    def generate_cash_flow_forecast(
        self,
        months: int = 12,
        starting_balance: float = 0,
        entity_id: str = None
    ) -> Dict[str, Any]:
        """Generate 12-month cash flow forecast"""
        today = date.today()
        forecast = []

        running_balance = starting_balance

        for i in range(months):
            month_date = date(today.year + (today.month + i - 1) // 12,
                            (today.month + i - 1) % 12 + 1, 1)
            month_name = month_date.strftime("%Y-%m")

            income = 0
            expenses = 0
            items = []

            # Get entries for this month
            for entry in self.cash_flow_entries.values():
                if entity_id and entry.entity_id != entity_id:
                    continue

                entry_month = entry.transaction_date.strftime("%Y-%m")
                if entry_month == month_name:
                    items.append({
                        "category": entry.category.value,
                        "description": entry.description,
                        "amount": entry.amount
                    })
                    if entry.amount > 0:
                        income += entry.amount
                    else:
                        expenses += abs(entry.amount)

            # Add loan payments
            for loan in self.loans.values():
                if entity_id and loan.entity_id != entity_id:
                    continue

                # Check if payment falls in this month
                if loan.payment_frequency == PaymentFrequency.MONTHLY:
                    items.append({
                        "category": "loan_payments",
                        "description": f"Loan payment - {loan.lender}",
                        "amount": -loan.payment_amount
                    })
                    expenses += loan.payment_amount

            # Add lease payments
            for lease in self.leases.values():
                if entity_id and lease.entity_id != entity_id:
                    continue
                if lease.status != LeaseStatus.ACTIVE:
                    continue

                # Simplified - assume annual payment in start month
                if lease.payment_frequency == PaymentFrequency.ANNUAL:
                    if month_date.month == lease.start_date.month:
                        landowner = self.landowners.get(lease.landowner_id)
                        items.append({
                            "category": "land_rent",
                            "description": f"Land rent - {landowner.name if landowner else 'Unknown'}",
                            "amount": -lease.total_annual_rent
                        })
                        expenses += lease.total_annual_rent

            net = income - expenses
            running_balance += net

            forecast.append({
                "month": month_name,
                "income": round(income, 2),
                "expenses": round(expenses, 2),
                "net": round(net, 2),
                "ending_balance": round(running_balance, 2),
                "items_count": len(items)
            })

        # Find critical points
        min_balance = min(f["ending_balance"] for f in forecast)
        min_month = next(f["month"] for f in forecast if f["ending_balance"] == min_balance)

        return {
            "forecast_period": f"{forecast[0]['month']} to {forecast[-1]['month']}",
            "starting_balance": starting_balance,
            "summary": {
                "total_income": sum(f["income"] for f in forecast),
                "total_expenses": sum(f["expenses"] for f in forecast),
                "ending_balance": forecast[-1]["ending_balance"],
                "minimum_balance": min_balance,
                "minimum_balance_month": min_month
            },
            "cash_flow_warning": min_balance < 0,
            "monthly_forecast": forecast
        }

    def get_loan_summary(self, entity_id: str = None) -> Dict[str, Any]:
        """Get summary of all loans"""
        loans = []
        total_balance = 0
        total_annual_payments = 0

        for loan in self.loans.values():
            if entity_id and loan.entity_id != entity_id:
                continue

            # Calculate annual payments
            if loan.payment_frequency == PaymentFrequency.MONTHLY:
                annual = loan.payment_amount * 12
            elif loan.payment_frequency == PaymentFrequency.QUARTERLY:
                annual = loan.payment_amount * 4
            elif loan.payment_frequency == PaymentFrequency.SEMI_ANNUAL:
                annual = loan.payment_amount * 2
            else:
                annual = loan.payment_amount

            loans.append({
                "id": loan.id,
                "lender": loan.lender,
                "type": loan.loan_type,
                "balance": loan.current_balance,
                "rate": loan.interest_rate,
                "payment": loan.payment_amount,
                "frequency": loan.payment_frequency.value,
                "annual_payments": annual,
                "next_payment": loan.next_payment_date.isoformat(),
                "maturity": loan.maturity_date.isoformat()
            })

            total_balance += loan.current_balance
            total_annual_payments += annual

        return {
            "total_loans": len(loans),
            "total_balance": round(total_balance, 2),
            "total_annual_payments": round(total_annual_payments, 2),
            "loans": loans
        }

    def get_cash_flow_categories(self) -> Dict[str, Any]:
        """Get available cash flow categories"""
        income_cats = [
            CashFlowCategory.CROP_SALES, CashFlowCategory.LIVESTOCK_SALES,
            CashFlowCategory.GOVERNMENT_PAYMENTS, CashFlowCategory.CROP_INSURANCE,
            CashFlowCategory.CUSTOM_WORK, CashFlowCategory.OTHER_INCOME
        ]
        expense_cats = [
            CashFlowCategory.SEED, CashFlowCategory.FERTILIZER, CashFlowCategory.CHEMICALS,
            CashFlowCategory.FUEL, CashFlowCategory.REPAIRS, CashFlowCategory.LAND_RENT,
            CashFlowCategory.LABOR, CashFlowCategory.INSURANCE, CashFlowCategory.UTILITIES,
            CashFlowCategory.LOAN_PAYMENTS, CashFlowCategory.EQUIPMENT_PURCHASE,
            CashFlowCategory.TAXES, CashFlowCategory.LIVING_EXPENSES, CashFlowCategory.OTHER_EXPENSE
        ]

        return {
            "income": [{"id": c.value, "name": c.value.replace("_", " ").title()} for c in income_cats],
            "expense": [{"id": c.value, "name": c.value.replace("_", " ").title()} for c in expense_cats]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_enterprise_operations_service: Optional[EnterpriseOperationsService] = None


def get_enterprise_operations_service() -> EnterpriseOperationsService:
    """Get or create the enterprise operations service singleton"""
    global _enterprise_operations_service
    if _enterprise_operations_service is None:
        _enterprise_operations_service = EnterpriseOperationsService()
    return _enterprise_operations_service
