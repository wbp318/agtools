"""
GenFin Classes & Projects Service - QuickBooks-style Class Tracking and Job Costing
Track income/expenses by class, project, and job for detailed profitability analysis
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid


class ClassType(Enum):
    """Class types for categorization"""
    DEPARTMENT = "department"
    LOCATION = "location"
    DIVISION = "division"
    PRODUCT_LINE = "product_line"
    FARM = "farm"  # Farm-specific
    FIELD = "field"  # Farm-specific
    CROP = "crop"  # Farm-specific
    CUSTOM = "custom"


class ProjectStatus(Enum):
    """Project/Job status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class BillableStatus(Enum):
    """Billable expense status"""
    NOT_BILLED = "not_billed"
    PENDING = "pending"
    BILLED = "billed"


class ProgressBillingType(Enum):
    """Progress billing types"""
    PERCENT = "percent"
    AMOUNT = "amount"
    MILESTONES = "milestones"


@dataclass
class Class:
    """QuickBooks-style Class for categorizing transactions"""
    class_id: str
    name: str
    class_type: ClassType = ClassType.CUSTOM
    parent_class_id: Optional[str] = None  # For subclasses

    description: str = ""
    is_active: bool = True

    # Tracking
    total_income: float = 0.0
    total_expenses: float = 0.0
    transaction_count: int = 0

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Project:
    """Project/Job for job costing"""
    project_id: str
    name: str
    project_number: str = ""
    customer_id: Optional[str] = None

    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    due_date: Optional[date] = None

    # Description
    description: str = ""
    notes: str = ""

    # Status
    status: ProjectStatus = ProjectStatus.NOT_STARTED

    # Budget
    estimated_revenue: float = 0.0
    estimated_cost: float = 0.0
    estimated_hours: float = 0.0

    # Actuals
    actual_revenue: float = 0.0
    actual_cost: float = 0.0
    actual_hours: float = 0.0

    # Billing
    billing_method: str = "fixed"  # fixed, time_and_materials, percent_complete
    contract_amount: float = 0.0
    amount_billed: float = 0.0
    amount_received: float = 0.0

    # Classification
    class_id: Optional[str] = None
    project_type: str = ""

    # Parent for sub-projects
    parent_project_id: Optional[str] = None

    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BillableExpense:
    """Billable expense tied to a project"""
    expense_id: str
    project_id: str
    expense_date: date

    # Expense details
    description: str
    vendor_id: Optional[str] = None
    amount: float = 0.0
    markup_percent: float = 0.0
    billable_amount: float = 0.0

    # Categorization
    expense_account_id: Optional[str] = None
    item_id: Optional[str] = None

    # Status
    status: BillableStatus = BillableStatus.NOT_BILLED
    invoice_id: Optional[str] = None
    billed_date: Optional[date] = None

    # Source
    bill_id: Optional[str] = None
    time_entry_id: Optional[str] = None

    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BillableTime:
    """Billable time entry for a project"""
    time_entry_id: str
    project_id: str
    entry_date: date

    # Employee/Contractor
    employee_id: Optional[str] = None
    employee_name: str = ""

    # Time
    hours: float = 0.0
    hourly_rate: float = 0.0
    amount: float = 0.0

    # Billing
    is_billable: bool = True
    billable_rate: float = 0.0
    billable_amount: float = 0.0

    # Status
    status: BillableStatus = BillableStatus.NOT_BILLED
    invoice_id: Optional[str] = None
    billed_date: Optional[date] = None

    # Details
    service_item_id: Optional[str] = None
    description: str = ""
    notes: str = ""

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProjectMilestone:
    """Project milestone for progress billing"""
    milestone_id: str
    project_id: str
    name: str
    description: str = ""

    # Billing
    amount: float = 0.0
    percent_of_total: float = 0.0

    # Status
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    is_completed: bool = False
    is_billed: bool = False
    invoice_id: Optional[str] = None

    order: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProgressBilling:
    """Progress billing record"""
    billing_id: str
    project_id: str
    billing_date: date

    billing_type: ProgressBillingType
    percent_complete: float = 0.0
    amount: float = 0.0

    # For milestone billing
    milestone_ids: List[str] = field(default_factory=list)

    description: str = ""
    invoice_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TransactionClass:
    """Links transactions to classes (journal entries, bills, invoices, etc.)"""
    link_id: str
    transaction_type: str  # journal_entry, bill, invoice, expense, etc.
    transaction_id: str
    class_id: str
    amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class GenFinClassesService:
    """
    GenFin Classes & Projects Service

    QuickBooks-style class and job costing:
    - Class tracking (departments, locations, fields)
    - Project/Job management
    - Job costing with estimates vs actuals
    - Billable expenses and time
    - Progress invoicing
    - Profitability by class/project
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

        self.classes: Dict[str, Class] = {}
        self.projects: Dict[str, Project] = {}
        self.billable_expenses: Dict[str, BillableExpense] = {}
        self.billable_time: Dict[str, BillableTime] = {}
        self.milestones: Dict[str, ProjectMilestone] = {}
        self.progress_billings: Dict[str, ProgressBilling] = {}
        self.transaction_classes: Dict[str, TransactionClass] = {}

        self._initialize_farm_classes()
        self._initialized = True

    def _initialize_farm_classes(self):
        """Initialize default farm-related classes"""
        farm_classes = [
            {"name": "Corn", "type": ClassType.CROP},
            {"name": "Soybeans", "type": ClassType.CROP},
            {"name": "Wheat", "type": ClassType.CROP},
            {"name": "Equipment", "type": ClassType.DEPARTMENT},
            {"name": "Overhead", "type": ClassType.DEPARTMENT},
            {"name": "Custom Work", "type": ClassType.DEPARTMENT},
        ]

        for fc in farm_classes:
            class_id = str(uuid.uuid4())
            cls = Class(
                class_id=class_id,
                name=fc["name"],
                class_type=fc["type"]
            )
            self.classes[class_id] = cls

    # ==================== CLASS MANAGEMENT ====================

    def create_class(
        self,
        name: str,
        class_type: str = "custom",
        parent_class_id: Optional[str] = None,
        description: str = ""
    ) -> Dict:
        """Create a new class"""
        class_id = str(uuid.uuid4())

        # Validate parent if provided
        if parent_class_id and parent_class_id not in self.classes:
            return {"success": False, "error": "Parent class not found"}

        cls = Class(
            class_id=class_id,
            name=name,
            class_type=ClassType(class_type),
            parent_class_id=parent_class_id,
            description=description
        )

        self.classes[class_id] = cls

        return {
            "success": True,
            "class_id": class_id,
            "class": self._class_to_dict(cls)
        }

    def update_class(self, class_id: str, **kwargs) -> Dict:
        """Update a class"""
        if class_id not in self.classes:
            return {"success": False, "error": "Class not found"}

        cls = self.classes[class_id]

        for key, value in kwargs.items():
            if hasattr(cls, key) and value is not None:
                if key == "class_type":
                    value = ClassType(value)
                setattr(cls, key, value)

        cls.updated_at = datetime.now()

        return {
            "success": True,
            "class": self._class_to_dict(cls)
        }

    def get_class(self, class_id: str) -> Optional[Dict]:
        """Get class by ID"""
        if class_id not in self.classes:
            return None
        return self._class_to_dict(self.classes[class_id])

    def list_classes(
        self,
        class_type: Optional[str] = None,
        parent_class_id: Optional[str] = None,
        active_only: bool = True,
        include_hierarchy: bool = False
    ) -> List[Dict]:
        """List classes with filtering"""
        result = []

        for cls in self.classes.values():
            if active_only and not cls.is_active:
                continue
            if class_type and cls.class_type.value != class_type:
                continue
            if parent_class_id is not None and cls.parent_class_id != parent_class_id:
                continue

            class_dict = self._class_to_dict(cls)

            if include_hierarchy:
                # Add subclasses
                class_dict["subclasses"] = [
                    self._class_to_dict(c) for c in self.classes.values()
                    if c.parent_class_id == cls.class_id and c.is_active
                ]

            result.append(class_dict)

        return sorted(result, key=lambda c: c["name"])

    def get_class_hierarchy(self) -> List[Dict]:
        """Get classes organized as hierarchy"""
        # Get top-level classes
        top_level = [c for c in self.classes.values() if c.parent_class_id is None and c.is_active]

        def build_tree(parent_id: Optional[str]) -> List[Dict]:
            children = [c for c in self.classes.values() if c.parent_class_id == parent_id and c.is_active]
            result = []
            for child in sorted(children, key=lambda c: c.name):
                node = self._class_to_dict(child)
                node["children"] = build_tree(child.class_id)
                result.append(node)
            return result

        return build_tree(None)

    # ==================== PROJECT/JOB MANAGEMENT ====================

    def create_project(
        self,
        name: str,
        customer_id: Optional[str] = None,
        project_number: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        estimated_revenue: float = 0.0,
        estimated_cost: float = 0.0,
        billing_method: str = "fixed",
        contract_amount: float = 0.0,
        class_id: Optional[str] = None,
        description: str = ""
    ) -> Dict:
        """Create a new project/job"""
        project_id = str(uuid.uuid4())

        # Generate project number if not provided
        if not project_number:
            project_number = f"P-{len(self.projects) + 1:05d}"

        project = Project(
            project_id=project_id,
            name=name,
            project_number=project_number,
            customer_id=customer_id,
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None,
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            estimated_revenue=estimated_revenue,
            estimated_cost=estimated_cost,
            billing_method=billing_method,
            contract_amount=contract_amount,
            class_id=class_id,
            description=description
        )

        self.projects[project_id] = project

        return {
            "success": True,
            "project_id": project_id,
            "project_number": project_number,
            "project": self._project_to_dict(project)
        }

    def update_project(self, project_id: str, **kwargs) -> Dict:
        """Update a project"""
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        project = self.projects[project_id]

        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                if key == "status":
                    value = ProjectStatus(value)
                elif key in ["start_date", "end_date", "due_date"] and isinstance(value, str):
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                setattr(project, key, value)

        project.updated_at = datetime.now()

        return {
            "success": True,
            "project": self._project_to_dict(project)
        }

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        if project_id not in self.projects:
            return None

        project = self.projects[project_id]
        result = self._project_to_dict(project)

        # Add detailed financials
        result["billable_expenses"] = self.get_project_billable_expenses(project_id)
        result["billable_time"] = self.get_project_billable_time(project_id)
        result["milestones"] = [
            self._milestone_to_dict(m) for m in self.milestones.values()
            if m.project_id == project_id
        ]

        return result

    def list_projects(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        class_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict]:
        """List projects with filtering"""
        result = []

        for project in self.projects.values():
            if active_only and not project.is_active:
                continue
            if customer_id and project.customer_id != customer_id:
                continue
            if status and project.status.value != status:
                continue
            if class_id and project.class_id != class_id:
                continue

            result.append(self._project_to_dict(project))

        return sorted(result, key=lambda p: p["name"])

    def update_project_status(self, project_id: str, status: str) -> Dict:
        """Update project status"""
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        project = self.projects[project_id]
        project.status = ProjectStatus(status)

        if status == "completed" and project.end_date is None:
            project.end_date = date.today()

        project.updated_at = datetime.now()

        return {
            "success": True,
            "project": self._project_to_dict(project)
        }

    # ==================== BILLABLE EXPENSES ====================

    def add_billable_expense(
        self,
        project_id: str,
        expense_date: str,
        description: str,
        amount: float,
        vendor_id: Optional[str] = None,
        markup_percent: float = 0.0,
        expense_account_id: Optional[str] = None,
        item_id: Optional[str] = None,
        bill_id: Optional[str] = None,
        notes: str = ""
    ) -> Dict:
        """Add a billable expense to a project"""
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        expense_id = str(uuid.uuid4())
        e_date = datetime.strptime(expense_date, "%Y-%m-%d").date()

        # Calculate billable amount with markup
        markup = amount * (markup_percent / 100) if markup_percent else 0
        billable_amount = amount + markup

        expense = BillableExpense(
            expense_id=expense_id,
            project_id=project_id,
            expense_date=e_date,
            description=description,
            vendor_id=vendor_id,
            amount=amount,
            markup_percent=markup_percent,
            billable_amount=billable_amount,
            expense_account_id=expense_account_id,
            item_id=item_id,
            bill_id=bill_id,
            notes=notes
        )

        self.billable_expenses[expense_id] = expense

        # Update project actuals
        project = self.projects[project_id]
        project.actual_cost += amount
        project.updated_at = datetime.now()

        return {
            "success": True,
            "expense_id": expense_id,
            "expense": self._expense_to_dict(expense)
        }

    def get_project_billable_expenses(
        self,
        project_id: str,
        unbilled_only: bool = False
    ) -> List[Dict]:
        """Get billable expenses for a project"""
        result = []

        for expense in self.billable_expenses.values():
            if expense.project_id != project_id:
                continue
            if unbilled_only and expense.status == BillableStatus.BILLED:
                continue

            result.append(self._expense_to_dict(expense))

        return sorted(result, key=lambda e: e["expense_date"])

    def mark_expense_billed(
        self,
        expense_id: str,
        invoice_id: str
    ) -> Dict:
        """Mark an expense as billed"""
        if expense_id not in self.billable_expenses:
            return {"success": False, "error": "Expense not found"}

        expense = self.billable_expenses[expense_id]
        expense.status = BillableStatus.BILLED
        expense.invoice_id = invoice_id
        expense.billed_date = date.today()

        return {"success": True, "message": "Expense marked as billed"}

    # ==================== BILLABLE TIME ====================

    def add_billable_time(
        self,
        project_id: str,
        entry_date: str,
        hours: float,
        hourly_rate: float = 0.0,
        employee_id: Optional[str] = None,
        employee_name: str = "",
        is_billable: bool = True,
        billable_rate: Optional[float] = None,
        service_item_id: Optional[str] = None,
        description: str = "",
        notes: str = ""
    ) -> Dict:
        """Add billable time to a project"""
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        time_entry_id = str(uuid.uuid4())
        e_date = datetime.strptime(entry_date, "%Y-%m-%d").date()

        amount = hours * hourly_rate
        bill_rate = billable_rate if billable_rate is not None else hourly_rate
        billable_amount = hours * bill_rate if is_billable else 0

        time_entry = BillableTime(
            time_entry_id=time_entry_id,
            project_id=project_id,
            entry_date=e_date,
            employee_id=employee_id,
            employee_name=employee_name,
            hours=hours,
            hourly_rate=hourly_rate,
            amount=amount,
            is_billable=is_billable,
            billable_rate=bill_rate,
            billable_amount=billable_amount,
            service_item_id=service_item_id,
            description=description,
            notes=notes
        )

        self.billable_time[time_entry_id] = time_entry

        # Update project actuals
        project = self.projects[project_id]
        project.actual_cost += amount
        project.actual_hours += hours
        if is_billable:
            project.actual_revenue += billable_amount
        project.updated_at = datetime.now()

        return {
            "success": True,
            "time_entry_id": time_entry_id,
            "time_entry": self._time_entry_to_dict(time_entry)
        }

    def get_project_billable_time(
        self,
        project_id: str,
        unbilled_only: bool = False
    ) -> List[Dict]:
        """Get billable time for a project"""
        result = []

        for entry in self.billable_time.values():
            if entry.project_id != project_id:
                continue
            if unbilled_only and entry.status == BillableStatus.BILLED:
                continue

            result.append(self._time_entry_to_dict(entry))

        return sorted(result, key=lambda t: t["entry_date"])

    def mark_time_billed(
        self,
        time_entry_id: str,
        invoice_id: str
    ) -> Dict:
        """Mark time as billed"""
        if time_entry_id not in self.billable_time:
            return {"success": False, "error": "Time entry not found"}

        entry = self.billable_time[time_entry_id]
        entry.status = BillableStatus.BILLED
        entry.invoice_id = invoice_id
        entry.billed_date = date.today()

        return {"success": True, "message": "Time entry marked as billed"}

    # ==================== MILESTONES & PROGRESS BILLING ====================

    def add_milestone(
        self,
        project_id: str,
        name: str,
        amount: float = 0.0,
        percent_of_total: float = 0.0,
        due_date: Optional[str] = None,
        description: str = "",
        order: int = 0
    ) -> Dict:
        """Add a milestone to a project"""
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        milestone_id = str(uuid.uuid4())

        milestone = ProjectMilestone(
            milestone_id=milestone_id,
            project_id=project_id,
            name=name,
            description=description,
            amount=amount,
            percent_of_total=percent_of_total,
            due_date=datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None,
            order=order
        )

        self.milestones[milestone_id] = milestone

        return {
            "success": True,
            "milestone_id": milestone_id,
            "milestone": self._milestone_to_dict(milestone)
        }

    def complete_milestone(self, milestone_id: str) -> Dict:
        """Mark a milestone as completed"""
        if milestone_id not in self.milestones:
            return {"success": False, "error": "Milestone not found"}

        milestone = self.milestones[milestone_id]
        milestone.is_completed = True
        milestone.completed_date = date.today()

        return {"success": True, "message": "Milestone completed"}

    def create_progress_billing(
        self,
        project_id: str,
        billing_date: str,
        billing_type: str,
        percent_complete: float = 0.0,
        amount: float = 0.0,
        milestone_ids: List[str] = None,
        description: str = ""
    ) -> Dict:
        """Create a progress billing for a project"""
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}

        project = self.projects[project_id]
        billing_id = str(uuid.uuid4())
        b_date = datetime.strptime(billing_date, "%Y-%m-%d").date()

        # Calculate amount based on billing type
        if billing_type == "percent":
            # Bill based on percentage complete
            previous_billed_percent = (project.amount_billed / project.contract_amount * 100) if project.contract_amount > 0 else 0
            billing_percent = percent_complete - previous_billed_percent
            amount = (billing_percent / 100) * project.contract_amount

        elif billing_type == "milestones":
            # Bill for completed milestones
            amount = 0
            for mid in (milestone_ids or []):
                if mid in self.milestones:
                    ms = self.milestones[mid]
                    if not ms.is_billed:
                        amount += ms.amount
                        ms.is_billed = True

        billing = ProgressBilling(
            billing_id=billing_id,
            project_id=project_id,
            billing_date=b_date,
            billing_type=ProgressBillingType(billing_type),
            percent_complete=percent_complete,
            amount=amount,
            milestone_ids=milestone_ids or [],
            description=description
        )

        self.progress_billings[billing_id] = billing

        # Update project
        project.amount_billed += amount
        project.updated_at = datetime.now()

        return {
            "success": True,
            "billing_id": billing_id,
            "amount": round(amount, 2),
            "total_billed": round(project.amount_billed, 2),
            "remaining": round(project.contract_amount - project.amount_billed, 2)
        }

    # ==================== TRANSACTION CLASSIFICATION ====================

    def assign_class(
        self,
        transaction_type: str,
        transaction_id: str,
        class_id: str,
        amount: float = 0.0
    ) -> Dict:
        """Assign a class to a transaction"""
        if class_id not in self.classes:
            return {"success": False, "error": "Class not found"}

        link_id = str(uuid.uuid4())

        link = TransactionClass(
            link_id=link_id,
            transaction_type=transaction_type,
            transaction_id=transaction_id,
            class_id=class_id,
            amount=amount
        )

        self.transaction_classes[link_id] = link

        # Update class totals
        cls = self.classes[class_id]
        if amount > 0:
            cls.total_income += amount
        else:
            cls.total_expenses += abs(amount)
        cls.transaction_count += 1

        return {"success": True, "link_id": link_id}

    def get_class_transactions(
        self,
        class_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get transactions for a class"""
        result = []

        for link in self.transaction_classes.values():
            if link.class_id != class_id:
                continue

            result.append({
                "link_id": link.link_id,
                "transaction_type": link.transaction_type,
                "transaction_id": link.transaction_id,
                "amount": link.amount,
                "created_at": link.created_at.isoformat()
            })

        return result

    # ==================== REPORTS ====================

    def get_profitability_by_class(self, start_date: str, end_date: str) -> Dict:
        """Get profitability report by class"""
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        class_totals = {}

        for cls in self.classes.values():
            if not cls.is_active:
                continue

            class_totals[cls.class_id] = {
                "class_id": cls.class_id,
                "class_name": cls.name,
                "class_type": cls.class_type.value,
                "income": 0.0,
                "expenses": 0.0,
                "profit": 0.0,
                "margin_percent": 0.0
            }

        # Sum up transaction amounts by class
        for link in self.transaction_classes.values():
            if link.class_id not in class_totals:
                continue

            if link.amount > 0:
                class_totals[link.class_id]["income"] += link.amount
            else:
                class_totals[link.class_id]["expenses"] += abs(link.amount)

        # Calculate profit and margin
        result = []
        total_income = 0
        total_expenses = 0

        for ct in class_totals.values():
            ct["profit"] = ct["income"] - ct["expenses"]
            if ct["income"] > 0:
                ct["margin_percent"] = round((ct["profit"] / ct["income"]) * 100, 2)

            ct["income"] = round(ct["income"], 2)
            ct["expenses"] = round(ct["expenses"], 2)
            ct["profit"] = round(ct["profit"], 2)

            total_income += ct["income"]
            total_expenses += ct["expenses"]

            if ct["income"] > 0 or ct["expenses"] > 0:
                result.append(ct)

        return {
            "report": "Profitability by Class",
            "period": {"start": start_date, "end": end_date},
            "classes": sorted(result, key=lambda x: x["profit"], reverse=True),
            "totals": {
                "income": round(total_income, 2),
                "expenses": round(total_expenses, 2),
                "profit": round(total_income - total_expenses, 2)
            }
        }

    def get_project_profitability(self, project_id: str) -> Dict:
        """Get detailed profitability for a project"""
        if project_id not in self.projects:
            return {"error": "Project not found"}

        project = self.projects[project_id]

        # Get expenses by category
        expense_by_account = {}
        for exp in self.billable_expenses.values():
            if exp.project_id != project_id:
                continue
            acct = exp.expense_account_id or "Uncategorized"
            if acct not in expense_by_account:
                expense_by_account[acct] = 0
            expense_by_account[acct] += exp.amount

        # Get time by employee
        time_by_employee = {}
        for entry in self.billable_time.values():
            if entry.project_id != project_id:
                continue
            emp = entry.employee_name or "Unassigned"
            if emp not in time_by_employee:
                time_by_employee[emp] = {"hours": 0, "cost": 0, "billable": 0}
            time_by_employee[emp]["hours"] += entry.hours
            time_by_employee[emp]["cost"] += entry.amount
            time_by_employee[emp]["billable"] += entry.billable_amount

        gross_profit = project.actual_revenue - project.actual_cost
        margin = (gross_profit / project.actual_revenue * 100) if project.actual_revenue > 0 else 0

        return {
            "project_id": project_id,
            "project_name": project.name,
            "project_number": project.project_number,
            "status": project.status.value,
            "estimates": {
                "revenue": project.estimated_revenue,
                "cost": project.estimated_cost,
                "hours": project.estimated_hours,
                "profit": project.estimated_revenue - project.estimated_cost
            },
            "actuals": {
                "revenue": round(project.actual_revenue, 2),
                "cost": round(project.actual_cost, 2),
                "hours": round(project.actual_hours, 2),
                "profit": round(gross_profit, 2)
            },
            "variance": {
                "revenue": round(project.actual_revenue - project.estimated_revenue, 2),
                "cost": round(project.actual_cost - project.estimated_cost, 2),
                "hours": round(project.actual_hours - project.estimated_hours, 2)
            },
            "margin_percent": round(margin, 2),
            "billing": {
                "contract_amount": project.contract_amount,
                "amount_billed": project.amount_billed,
                "amount_received": project.amount_received,
                "unbilled": round(project.contract_amount - project.amount_billed, 2)
            },
            "expenses_by_account": expense_by_account,
            "time_by_employee": time_by_employee
        }

    def get_unbilled_summary(self) -> Dict:
        """Get summary of all unbilled time and expenses"""
        unbilled_expenses = []
        unbilled_time = []
        total_unbilled_expenses = 0
        total_unbilled_time = 0

        for exp in self.billable_expenses.values():
            if exp.status != BillableStatus.BILLED:
                unbilled_expenses.append({
                    "expense_id": exp.expense_id,
                    "project_id": exp.project_id,
                    "description": exp.description,
                    "amount": exp.amount,
                    "billable_amount": exp.billable_amount,
                    "date": exp.expense_date.isoformat()
                })
                total_unbilled_expenses += exp.billable_amount

        for entry in self.billable_time.values():
            if entry.is_billable and entry.status != BillableStatus.BILLED:
                unbilled_time.append({
                    "time_entry_id": entry.time_entry_id,
                    "project_id": entry.project_id,
                    "employee": entry.employee_name,
                    "hours": entry.hours,
                    "billable_amount": entry.billable_amount,
                    "date": entry.entry_date.isoformat()
                })
                total_unbilled_time += entry.billable_amount

        return {
            "unbilled_expenses": unbilled_expenses,
            "unbilled_time": unbilled_time,
            "total_unbilled_expenses": round(total_unbilled_expenses, 2),
            "total_unbilled_time": round(total_unbilled_time, 2),
            "total_unbilled": round(total_unbilled_expenses + total_unbilled_time, 2)
        }

    # ==================== UTILITY METHODS ====================

    def _class_to_dict(self, cls: Class) -> Dict:
        """Convert Class to dictionary"""
        return {
            "class_id": cls.class_id,
            "name": cls.name,
            "class_type": cls.class_type.value,
            "parent_class_id": cls.parent_class_id,
            "description": cls.description,
            "is_active": cls.is_active,
            "total_income": round(cls.total_income, 2),
            "total_expenses": round(cls.total_expenses, 2),
            "net": round(cls.total_income - cls.total_expenses, 2),
            "transaction_count": cls.transaction_count,
            "created_at": cls.created_at.isoformat()
        }

    def _project_to_dict(self, project: Project) -> Dict:
        """Convert Project to dictionary"""
        gross_profit = project.actual_revenue - project.actual_cost
        budget_remaining = project.estimated_cost - project.actual_cost

        return {
            "project_id": project.project_id,
            "name": project.name,
            "project_number": project.project_number,
            "customer_id": project.customer_id,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "description": project.description,
            "status": project.status.value,
            "class_id": project.class_id,
            "billing_method": project.billing_method,
            "contract_amount": project.contract_amount,
            "estimated_revenue": project.estimated_revenue,
            "estimated_cost": project.estimated_cost,
            "estimated_hours": project.estimated_hours,
            "actual_revenue": round(project.actual_revenue, 2),
            "actual_cost": round(project.actual_cost, 2),
            "actual_hours": round(project.actual_hours, 2),
            "gross_profit": round(gross_profit, 2),
            "budget_remaining": round(budget_remaining, 2),
            "percent_complete": round((project.actual_cost / project.estimated_cost * 100) if project.estimated_cost > 0 else 0, 1),
            "amount_billed": project.amount_billed,
            "amount_received": project.amount_received,
            "is_active": project.is_active,
            "created_at": project.created_at.isoformat()
        }

    def _expense_to_dict(self, expense: BillableExpense) -> Dict:
        """Convert BillableExpense to dictionary"""
        return {
            "expense_id": expense.expense_id,
            "project_id": expense.project_id,
            "expense_date": expense.expense_date.isoformat(),
            "description": expense.description,
            "vendor_id": expense.vendor_id,
            "amount": expense.amount,
            "markup_percent": expense.markup_percent,
            "billable_amount": round(expense.billable_amount, 2),
            "status": expense.status.value,
            "invoice_id": expense.invoice_id,
            "billed_date": expense.billed_date.isoformat() if expense.billed_date else None,
            "notes": expense.notes
        }

    def _time_entry_to_dict(self, entry: BillableTime) -> Dict:
        """Convert BillableTime to dictionary"""
        return {
            "time_entry_id": entry.time_entry_id,
            "project_id": entry.project_id,
            "entry_date": entry.entry_date.isoformat(),
            "employee_id": entry.employee_id,
            "employee_name": entry.employee_name,
            "hours": entry.hours,
            "hourly_rate": entry.hourly_rate,
            "amount": round(entry.amount, 2),
            "is_billable": entry.is_billable,
            "billable_rate": entry.billable_rate,
            "billable_amount": round(entry.billable_amount, 2),
            "status": entry.status.value,
            "invoice_id": entry.invoice_id,
            "description": entry.description
        }

    def _milestone_to_dict(self, milestone: ProjectMilestone) -> Dict:
        """Convert ProjectMilestone to dictionary"""
        return {
            "milestone_id": milestone.milestone_id,
            "project_id": milestone.project_id,
            "name": milestone.name,
            "description": milestone.description,
            "amount": milestone.amount,
            "percent_of_total": milestone.percent_of_total,
            "due_date": milestone.due_date.isoformat() if milestone.due_date else None,
            "completed_date": milestone.completed_date.isoformat() if milestone.completed_date else None,
            "is_completed": milestone.is_completed,
            "is_billed": milestone.is_billed,
            "order": milestone.order
        }

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        active_projects = sum(1 for p in self.projects.values() if p.is_active and p.status == ProjectStatus.IN_PROGRESS)

        return {
            "service": "GenFin Classes & Projects",
            "version": "1.0.0",
            "features": [
                "Class Tracking (Departments, Locations, Fields)",
                "Project/Job Management",
                "Job Costing",
                "Billable Expenses",
                "Billable Time Tracking",
                "Progress Invoicing",
                "Milestone Billing",
                "Profitability Reports"
            ],
            "total_classes": len(self.classes),
            "total_projects": len(self.projects),
            "active_projects": active_projects,
            "billable_expenses_count": len(self.billable_expenses),
            "billable_time_entries": len(self.billable_time)
        }


# Singleton instance
genfin_classes_service = GenFinClassesService()
