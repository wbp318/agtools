"""
GenFin Classes & Projects Service with SQLite persistence
Track income/expenses by class, project, and job for detailed profitability analysis
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Optional
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
    parent_class_id: Optional[str] = None

    description: str = ""
    is_active: bool = True

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

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    due_date: Optional[date] = None

    description: str = ""
    notes: str = ""

    status: ProjectStatus = ProjectStatus.NOT_STARTED

    estimated_revenue: float = 0.0
    estimated_cost: float = 0.0
    estimated_hours: float = 0.0

    actual_revenue: float = 0.0
    actual_cost: float = 0.0
    actual_hours: float = 0.0

    billing_method: str = "fixed"
    contract_amount: float = 0.0
    amount_billed: float = 0.0
    amount_received: float = 0.0

    class_id: Optional[str] = None
    project_type: str = ""

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

    description: str
    vendor_id: Optional[str] = None
    amount: float = 0.0
    markup_percent: float = 0.0
    billable_amount: float = 0.0

    expense_account_id: Optional[str] = None
    item_id: Optional[str] = None

    status: BillableStatus = BillableStatus.NOT_BILLED
    invoice_id: Optional[str] = None
    billed_date: Optional[date] = None

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

    employee_id: Optional[str] = None
    employee_name: str = ""

    hours: float = 0.0
    hourly_rate: float = 0.0
    amount: float = 0.0

    is_billable: bool = True
    billable_rate: float = 0.0
    billable_amount: float = 0.0

    status: BillableStatus = BillableStatus.NOT_BILLED
    invoice_id: Optional[str] = None
    billed_date: Optional[date] = None

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

    amount: float = 0.0
    percent_of_total: float = 0.0

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

    milestone_ids: List[str] = field(default_factory=list)

    description: str = ""
    invoice_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TransactionClass:
    """Links transactions to classes"""
    link_id: str
    transaction_type: str
    transaction_id: str
    class_id: str
    amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class GenFinClassesService:
    """
    GenFin Classes & Projects Service with SQLite persistence

    QuickBooks-style class and job costing:
    - Class tracking (departments, locations, fields)
    - Project/Job management
    - Job costing with estimates vs actuals
    - Billable expenses and time
    - Progress invoicing
    - Profitability by class/project
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
        self._initialize_farm_classes()
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

            # Drop old tables if schema changed (migration)
            cursor.execute("DROP TABLE IF EXISTS genfin_classes")
            cursor.execute("DROP TABLE IF EXISTS genfin_projects")
            cursor.execute("DROP TABLE IF EXISTS genfin_billable_expenses")
            cursor.execute("DROP TABLE IF EXISTS genfin_billable_time")
            cursor.execute("DROP TABLE IF EXISTS genfin_milestones")
            cursor.execute("DROP TABLE IF EXISTS genfin_progress_billings")
            cursor.execute("DROP TABLE IF EXISTS genfin_transaction_classes")

            # Classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_classes (
                    class_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    class_type TEXT DEFAULT 'custom',
                    parent_class_id TEXT,
                    description TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    total_income REAL DEFAULT 0.0,
                    total_expenses REAL DEFAULT 0.0,
                    transaction_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    project_number TEXT DEFAULT '',
                    customer_id TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    due_date TEXT,
                    description TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    status TEXT DEFAULT 'not_started',
                    estimated_revenue REAL DEFAULT 0.0,
                    estimated_cost REAL DEFAULT 0.0,
                    estimated_hours REAL DEFAULT 0.0,
                    actual_revenue REAL DEFAULT 0.0,
                    actual_cost REAL DEFAULT 0.0,
                    actual_hours REAL DEFAULT 0.0,
                    billing_method TEXT DEFAULT 'fixed',
                    contract_amount REAL DEFAULT 0.0,
                    amount_billed REAL DEFAULT 0.0,
                    amount_received REAL DEFAULT 0.0,
                    class_id TEXT,
                    project_type TEXT DEFAULT '',
                    parent_project_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Billable expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_billable_expenses (
                    expense_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    expense_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    vendor_id TEXT,
                    amount REAL DEFAULT 0.0,
                    markup_percent REAL DEFAULT 0.0,
                    billable_amount REAL DEFAULT 0.0,
                    expense_account_id TEXT,
                    item_id TEXT,
                    status TEXT DEFAULT 'not_billed',
                    invoice_id TEXT,
                    billed_date TEXT,
                    bill_id TEXT,
                    time_entry_id TEXT,
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES genfin_projects(project_id)
                )
            """)

            # Billable time table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_billable_time (
                    time_entry_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    employee_id TEXT,
                    employee_name TEXT DEFAULT '',
                    hours REAL DEFAULT 0.0,
                    hourly_rate REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    is_billable INTEGER DEFAULT 1,
                    billable_rate REAL DEFAULT 0.0,
                    billable_amount REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'not_billed',
                    invoice_id TEXT,
                    billed_date TEXT,
                    service_item_id TEXT,
                    description TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES genfin_projects(project_id)
                )
            """)

            # Milestones table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_milestones (
                    milestone_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    amount REAL DEFAULT 0.0,
                    percent_of_total REAL DEFAULT 0.0,
                    due_date TEXT,
                    completed_date TEXT,
                    is_completed INTEGER DEFAULT 0,
                    is_billed INTEGER DEFAULT 0,
                    invoice_id TEXT,
                    sort_order INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES genfin_projects(project_id)
                )
            """)

            # Progress billings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_progress_billings (
                    billing_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    billing_date TEXT NOT NULL,
                    billing_type TEXT NOT NULL,
                    percent_complete REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    milestone_ids_json TEXT DEFAULT '[]',
                    description TEXT DEFAULT '',
                    invoice_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES genfin_projects(project_id)
                )
            """)

            # Transaction classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_transaction_classes (
                    link_id TEXT PRIMARY KEY,
                    transaction_type TEXT NOT NULL,
                    transaction_id TEXT NOT NULL,
                    class_id TEXT NOT NULL,
                    amount REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (class_id) REFERENCES genfin_classes(class_id)
                )
            """)

            conn.commit()

    def _initialize_farm_classes(self):
        """Initialize default farm-related classes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM genfin_classes")
            if cursor.fetchone()[0] > 0:
                return

            now = datetime.now().isoformat()
            farm_classes = [
                {"name": "Corn", "type": "crop"},
                {"name": "Soybeans", "type": "crop"},
                {"name": "Wheat", "type": "crop"},
                {"name": "Equipment", "type": "department"},
                {"name": "Overhead", "type": "department"},
                {"name": "Custom Work", "type": "department"},
            ]

            for fc in farm_classes:
                class_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_classes
                    (class_id, name, class_type, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, ?)
                """, (class_id, fc["name"], fc["type"], now, now))

            conn.commit()

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
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if parent_class_id:
                cursor.execute("SELECT class_id FROM genfin_classes WHERE class_id = ? AND is_active = 1",
                             (parent_class_id,))
                if not cursor.fetchone():
                    return {"success": False, "error": "Parent class not found"}

            cursor.execute("""
                INSERT INTO genfin_classes
                (class_id, name, class_type, parent_class_id, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (class_id, name, class_type, parent_class_id, description, now, now))
            conn.commit()

        return {
            "success": True,
            "class_id": class_id,
            "class": self.get_class(class_id)
        }

    def update_class(self, class_id: str, **kwargs) -> Dict:
        """Update a class"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT class_id FROM genfin_classes WHERE class_id = ? AND is_active = 1",
                         (class_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Class not found"}

            updates = []
            values = []

            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if updates:
                updates.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(class_id)

                cursor.execute(f"""
                    UPDATE genfin_classes
                    SET {', '.join(updates)}
                    WHERE class_id = ?
                """, values)
                conn.commit()

        return {
            "success": True,
            "class": self.get_class(class_id)
        }

    def get_class(self, class_id: str) -> Optional[Dict]:
        """Get class by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_classes WHERE class_id = ?", (class_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_class_dict(row)

    def list_classes(
        self,
        class_type: Optional[str] = None,
        parent_class_id: Optional[str] = None,
        active_only: bool = True,
        include_hierarchy: bool = False
    ) -> List[Dict]:
        """List classes with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_classes WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = 1"

            if class_type:
                query += " AND class_type = ?"
                params.append(class_type)

            if parent_class_id is not None:
                if parent_class_id == "":
                    query += " AND parent_class_id IS NULL"
                else:
                    query += " AND parent_class_id = ?"
                    params.append(parent_class_id)

            query += " ORDER BY name"

            cursor.execute(query, params)
            result = []

            for row in cursor.fetchall():
                class_dict = self._row_to_class_dict(row)

                if include_hierarchy:
                    cursor.execute("""
                        SELECT * FROM genfin_classes
                        WHERE parent_class_id = ? AND is_active = 1
                        ORDER BY name
                    """, (row['class_id'],))
                    class_dict["subclasses"] = [
                        self._row_to_class_dict(sub) for sub in cursor.fetchall()
                    ]

                result.append(class_dict)

        return result

    def get_class_hierarchy(self) -> List[Dict]:
        """Get classes organized as hierarchy"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            def build_tree(parent_id: Optional[str]) -> List[Dict]:
                if parent_id:
                    cursor.execute("""
                        SELECT * FROM genfin_classes
                        WHERE parent_class_id = ? AND is_active = 1
                        ORDER BY name
                    """, (parent_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM genfin_classes
                        WHERE parent_class_id IS NULL AND is_active = 1
                        ORDER BY name
                    """)

                result = []
                for row in cursor.fetchall():
                    node = self._row_to_class_dict(row)
                    node["children"] = build_tree(row['class_id'])
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
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Generate project number if not provided
            if not project_number:
                cursor.execute("SELECT COUNT(*) FROM genfin_projects")
                count = cursor.fetchone()[0]
                project_number = f"P-{count + 1:05d}"

            cursor.execute("""
                INSERT INTO genfin_projects
                (project_id, name, project_number, customer_id, start_date, end_date,
                 description, estimated_revenue, estimated_cost, billing_method,
                 contract_amount, class_id, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (project_id, name, project_number, customer_id, start_date, end_date,
                  description, estimated_revenue, estimated_cost, billing_method,
                  contract_amount, class_id, now, now))
            conn.commit()

        return {
            "success": True,
            "project_id": project_id,
            "project_number": project_number,
            "project": self.get_project(project_id)
        }

    def update_project(self, project_id: str, **kwargs) -> Dict:
        """Update a project"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id FROM genfin_projects WHERE project_id = ? AND is_active = 1",
                         (project_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Project not found"}

            updates = []
            values = []

            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if updates:
                updates.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(project_id)

                cursor.execute(f"""
                    UPDATE genfin_projects
                    SET {', '.join(updates)}
                    WHERE project_id = ?
                """, values)
                conn.commit()

        return {
            "success": True,
            "project": self.get_project(project_id)
        }

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None

            result = self._row_to_project_dict(row)

            # Add detailed financials
            result["billable_expenses"] = self.get_project_billable_expenses(project_id)
            result["billable_time"] = self.get_project_billable_time(project_id)

            cursor.execute("SELECT * FROM genfin_milestones WHERE project_id = ? ORDER BY sort_order",
                         (project_id,))
            result["milestones"] = [self._row_to_milestone_dict(m) for m in cursor.fetchall()]

        return result

    def list_projects(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        class_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict]:
        """List projects with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_projects WHERE 1=1"
            params = []

            if active_only:
                query += " AND is_active = 1"

            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            if class_id:
                query += " AND class_id = ?"
                params.append(class_id)

            query += " ORDER BY name"

            cursor.execute(query, params)
            return [self._row_to_project_dict(row) for row in cursor.fetchall()]

    def update_project_status(self, project_id: str, status: str) -> Dict:
        """Update project status"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_projects WHERE project_id = ? AND is_active = 1",
                         (project_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Project not found"}

            end_date = row['end_date']
            if status == "completed" and not end_date:
                end_date = date.today().isoformat()

            cursor.execute("""
                UPDATE genfin_projects
                SET status = ?, end_date = ?, updated_at = ?
                WHERE project_id = ?
            """, (status, end_date, datetime.now().isoformat(), project_id))
            conn.commit()

        return {
            "success": True,
            "project": self.get_project(project_id)
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id FROM genfin_projects WHERE project_id = ? AND is_active = 1",
                         (project_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Project not found"}

            expense_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            markup = amount * (markup_percent / 100) if markup_percent else 0
            billable_amount = amount + markup

            cursor.execute("""
                INSERT INTO genfin_billable_expenses
                (expense_id, project_id, expense_date, description, vendor_id, amount,
                 markup_percent, billable_amount, expense_account_id, item_id,
                 status, bill_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_billed', ?, ?, ?)
            """, (expense_id, project_id, expense_date, description, vendor_id, amount,
                  markup_percent, billable_amount, expense_account_id, item_id,
                  bill_id, notes, now))

            # Update project actuals
            cursor.execute("""
                UPDATE genfin_projects
                SET actual_cost = actual_cost + ?, updated_at = ?
                WHERE project_id = ?
            """, (amount, now, project_id))

            conn.commit()

        return {
            "success": True,
            "expense_id": expense_id,
            "expense": self._get_expense(expense_id)
        }

    def _get_expense(self, expense_id: str) -> Optional[Dict]:
        """Get single expense"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_billable_expenses WHERE expense_id = ?",
                         (expense_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_expense_dict(row)

    def get_project_billable_expenses(
        self,
        project_id: str,
        unbilled_only: bool = False
    ) -> List[Dict]:
        """Get billable expenses for a project"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_billable_expenses WHERE project_id = ?"
            params = [project_id]

            if unbilled_only:
                query += " AND status != 'billed'"

            query += " ORDER BY expense_date"

            cursor.execute(query, params)
            return [self._row_to_expense_dict(row) for row in cursor.fetchall()]

    def mark_expense_billed(self, expense_id: str, invoice_id: str) -> Dict:
        """Mark an expense as billed"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT expense_id FROM genfin_billable_expenses WHERE expense_id = ?",
                         (expense_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Expense not found"}

            cursor.execute("""
                UPDATE genfin_billable_expenses
                SET status = 'billed', invoice_id = ?, billed_date = ?
                WHERE expense_id = ?
            """, (invoice_id, date.today().isoformat(), expense_id))
            conn.commit()

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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id FROM genfin_projects WHERE project_id = ? AND is_active = 1",
                         (project_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Project not found"}

            time_entry_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            amount = hours * hourly_rate
            bill_rate = billable_rate if billable_rate is not None else hourly_rate
            billable_amount = hours * bill_rate if is_billable else 0

            cursor.execute("""
                INSERT INTO genfin_billable_time
                (time_entry_id, project_id, entry_date, employee_id, employee_name,
                 hours, hourly_rate, amount, is_billable, billable_rate, billable_amount,
                 status, service_item_id, description, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_billed', ?, ?, ?, ?)
            """, (time_entry_id, project_id, entry_date, employee_id, employee_name,
                  hours, hourly_rate, amount, 1 if is_billable else 0, bill_rate,
                  billable_amount, service_item_id, description, notes, now))

            # Update project actuals
            revenue_add = billable_amount if is_billable else 0
            cursor.execute("""
                UPDATE genfin_projects
                SET actual_cost = actual_cost + ?, actual_hours = actual_hours + ?,
                    actual_revenue = actual_revenue + ?, updated_at = ?
                WHERE project_id = ?
            """, (amount, hours, revenue_add, now, project_id))

            conn.commit()

        return {
            "success": True,
            "time_entry_id": time_entry_id,
            "time_entry": self._get_time_entry(time_entry_id)
        }

    def _get_time_entry(self, time_entry_id: str) -> Optional[Dict]:
        """Get single time entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_billable_time WHERE time_entry_id = ?",
                         (time_entry_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_time_entry_dict(row)

    def get_project_billable_time(
        self,
        project_id: str,
        unbilled_only: bool = False
    ) -> List[Dict]:
        """Get billable time for a project"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_billable_time WHERE project_id = ?"
            params = [project_id]

            if unbilled_only:
                query += " AND status != 'billed'"

            query += " ORDER BY entry_date"

            cursor.execute(query, params)
            return [self._row_to_time_entry_dict(row) for row in cursor.fetchall()]

    def mark_time_billed(self, time_entry_id: str, invoice_id: str) -> Dict:
        """Mark time as billed"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT time_entry_id FROM genfin_billable_time WHERE time_entry_id = ?",
                         (time_entry_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Time entry not found"}

            cursor.execute("""
                UPDATE genfin_billable_time
                SET status = 'billed', invoice_id = ?, billed_date = ?
                WHERE time_entry_id = ?
            """, (invoice_id, date.today().isoformat(), time_entry_id))
            conn.commit()

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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id FROM genfin_projects WHERE project_id = ? AND is_active = 1",
                         (project_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Project not found"}

            milestone_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO genfin_milestones
                (milestone_id, project_id, name, description, amount, percent_of_total,
                 due_date, is_completed, is_billed, sort_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
            """, (milestone_id, project_id, name, description, amount, percent_of_total,
                  due_date, order, now))
            conn.commit()

        return {
            "success": True,
            "milestone_id": milestone_id,
            "milestone": self._get_milestone(milestone_id)
        }

    def _get_milestone(self, milestone_id: str) -> Optional[Dict]:
        """Get single milestone"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_milestones WHERE milestone_id = ?",
                         (milestone_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_milestone_dict(row)

    def complete_milestone(self, milestone_id: str) -> Dict:
        """Mark a milestone as completed"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT milestone_id FROM genfin_milestones WHERE milestone_id = ?",
                         (milestone_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Milestone not found"}

            cursor.execute("""
                UPDATE genfin_milestones
                SET is_completed = 1, completed_date = ?
                WHERE milestone_id = ?
            """, (date.today().isoformat(), milestone_id))
            conn.commit()

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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_projects WHERE project_id = ? AND is_active = 1",
                         (project_id,))
            project_row = cursor.fetchone()
            if not project_row:
                return {"success": False, "error": "Project not found"}

            billing_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            contract_amount = project_row['contract_amount'] or 0.0
            amount_billed = project_row['amount_billed'] or 0.0

            # Calculate amount based on billing type
            if billing_type == "percent":
                previous_billed_percent = (amount_billed / contract_amount * 100) if contract_amount > 0 else 0
                billing_percent = percent_complete - previous_billed_percent
                amount = (billing_percent / 100) * contract_amount

            elif billing_type == "milestones":
                amount = 0
                for mid in (milestone_ids or []):
                    cursor.execute("SELECT amount, is_billed FROM genfin_milestones WHERE milestone_id = ?",
                                 (mid,))
                    ms_row = cursor.fetchone()
                    if ms_row and not ms_row['is_billed']:
                        amount += ms_row['amount']
                        cursor.execute("UPDATE genfin_milestones SET is_billed = 1 WHERE milestone_id = ?",
                                     (mid,))

            cursor.execute("""
                INSERT INTO genfin_progress_billings
                (billing_id, project_id, billing_date, billing_type, percent_complete,
                 amount, milestone_ids_json, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (billing_id, project_id, billing_date, billing_type, percent_complete,
                  amount, json.dumps(milestone_ids or []), description, now))

            # Update project
            new_amount_billed = amount_billed + amount
            cursor.execute("""
                UPDATE genfin_projects
                SET amount_billed = ?, updated_at = ?
                WHERE project_id = ?
            """, (new_amount_billed, now, project_id))

            conn.commit()

        return {
            "success": True,
            "billing_id": billing_id,
            "amount": round(amount, 2),
            "total_billed": round(new_amount_billed, 2),
            "remaining": round(contract_amount - new_amount_billed, 2)
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT class_id FROM genfin_classes WHERE class_id = ? AND is_active = 1",
                         (class_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Class not found"}

            link_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO genfin_transaction_classes
                (link_id, transaction_type, transaction_id, class_id, amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (link_id, transaction_type, transaction_id, class_id, amount, now))

            # Update class totals
            if amount > 0:
                cursor.execute("""
                    UPDATE genfin_classes
                    SET total_income = total_income + ?, transaction_count = transaction_count + 1
                    WHERE class_id = ?
                """, (amount, class_id))
            else:
                cursor.execute("""
                    UPDATE genfin_classes
                    SET total_expenses = total_expenses + ?, transaction_count = transaction_count + 1
                    WHERE class_id = ?
                """, (abs(amount), class_id))

            conn.commit()

        return {"success": True, "link_id": link_id}

    def get_class_transactions(
        self,
        class_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """Get transactions for a class"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_transaction_classes
                WHERE class_id = ?
                ORDER BY created_at DESC
            """, (class_id,))

            result = []
            for row in cursor.fetchall():
                result.append({
                    "link_id": row['link_id'],
                    "transaction_type": row['transaction_type'],
                    "transaction_id": row['transaction_id'],
                    "amount": row['amount'],
                    "created_at": row['created_at']
                })

        return result

    # ==================== REPORTS ====================

    def get_profitability_by_class(self, start_date: str, end_date: str) -> Dict:
        """Get profitability report by class"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_classes WHERE is_active = 1")

            class_totals = {}
            for row in cursor.fetchall():
                class_totals[row['class_id']] = {
                    "class_id": row['class_id'],
                    "class_name": row['name'],
                    "class_type": row['class_type'],
                    "income": row['total_income'] or 0.0,
                    "expenses": row['total_expenses'] or 0.0,
                    "profit": 0.0,
                    "margin_percent": 0.0
                }

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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_projects WHERE project_id = ?", (project_id,))
            project_row = cursor.fetchone()
            if not project_row:
                return {"error": "Project not found"}

            # Get expenses by category
            cursor.execute("""
                SELECT expense_account_id, SUM(amount) as total
                FROM genfin_billable_expenses
                WHERE project_id = ?
                GROUP BY expense_account_id
            """, (project_id,))
            expense_by_account = {(r['expense_account_id'] or "Uncategorized"): r['total']
                                for r in cursor.fetchall()}

            # Get time by employee
            cursor.execute("""
                SELECT employee_name, SUM(hours) as hours, SUM(amount) as cost, SUM(billable_amount) as billable
                FROM genfin_billable_time
                WHERE project_id = ?
                GROUP BY employee_name
            """, (project_id,))
            time_by_employee = {r['employee_name'] or "Unassigned": {
                "hours": r['hours'], "cost": r['cost'], "billable": r['billable']
            } for r in cursor.fetchall()}

            actual_revenue = project_row['actual_revenue'] or 0.0
            actual_cost = project_row['actual_cost'] or 0.0
            gross_profit = actual_revenue - actual_cost
            margin = (gross_profit / actual_revenue * 100) if actual_revenue > 0 else 0

        return {
            "project_id": project_id,
            "project_name": project_row['name'],
            "project_number": project_row['project_number'],
            "status": project_row['status'],
            "estimates": {
                "revenue": project_row['estimated_revenue'],
                "cost": project_row['estimated_cost'],
                "hours": project_row['estimated_hours'],
                "profit": (project_row['estimated_revenue'] or 0) - (project_row['estimated_cost'] or 0)
            },
            "actuals": {
                "revenue": round(actual_revenue, 2),
                "cost": round(actual_cost, 2),
                "hours": round(project_row['actual_hours'] or 0, 2),
                "profit": round(gross_profit, 2)
            },
            "variance": {
                "revenue": round(actual_revenue - (project_row['estimated_revenue'] or 0), 2),
                "cost": round(actual_cost - (project_row['estimated_cost'] or 0), 2),
                "hours": round((project_row['actual_hours'] or 0) - (project_row['estimated_hours'] or 0), 2)
            },
            "margin_percent": round(margin, 2),
            "billing": {
                "contract_amount": project_row['contract_amount'],
                "amount_billed": project_row['amount_billed'],
                "amount_received": project_row['amount_received'],
                "unbilled": round((project_row['contract_amount'] or 0) - (project_row['amount_billed'] or 0), 2)
            },
            "expenses_by_account": expense_by_account,
            "time_by_employee": time_by_employee
        }

    def get_unbilled_summary(self) -> Dict:
        """Get summary of all unbilled time and expenses"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM genfin_billable_expenses WHERE status != 'billed'
            """)
            unbilled_expenses = []
            total_unbilled_expenses = 0
            for row in cursor.fetchall():
                unbilled_expenses.append({
                    "expense_id": row['expense_id'],
                    "project_id": row['project_id'],
                    "description": row['description'],
                    "amount": row['amount'],
                    "billable_amount": row['billable_amount'],
                    "date": row['expense_date']
                })
                total_unbilled_expenses += row['billable_amount']

            cursor.execute("""
                SELECT * FROM genfin_billable_time WHERE is_billable = 1 AND status != 'billed'
            """)
            unbilled_time = []
            total_unbilled_time = 0
            for row in cursor.fetchall():
                unbilled_time.append({
                    "time_entry_id": row['time_entry_id'],
                    "project_id": row['project_id'],
                    "employee": row['employee_name'],
                    "hours": row['hours'],
                    "billable_amount": row['billable_amount'],
                    "date": row['entry_date']
                })
                total_unbilled_time += row['billable_amount']

        return {
            "unbilled_expenses": unbilled_expenses,
            "unbilled_time": unbilled_time,
            "total_unbilled_expenses": round(total_unbilled_expenses, 2),
            "total_unbilled_time": round(total_unbilled_time, 2),
            "total_unbilled": round(total_unbilled_expenses + total_unbilled_time, 2)
        }

    # ==================== UTILITY METHODS ====================

    def _row_to_class_dict(self, row: sqlite3.Row) -> Dict:
        """Convert class row to dictionary"""
        income = row['total_income'] or 0.0
        expenses = row['total_expenses'] or 0.0
        return {
            "class_id": row['class_id'],
            "name": row['name'],
            "class_type": row['class_type'],
            "parent_class_id": row['parent_class_id'],
            "description": row['description'] or "",
            "is_active": bool(row['is_active']),
            "total_income": round(income, 2),
            "total_expenses": round(expenses, 2),
            "net": round(income - expenses, 2),
            "transaction_count": row['transaction_count'] or 0,
            "created_at": row['created_at']
        }

    def _row_to_project_dict(self, row: sqlite3.Row) -> Dict:
        """Convert project row to dictionary"""
        actual_revenue = row['actual_revenue'] or 0.0
        actual_cost = row['actual_cost'] or 0.0
        estimated_cost = row['estimated_cost'] or 0.0
        gross_profit = actual_revenue - actual_cost
        budget_remaining = estimated_cost - actual_cost

        return {
            "project_id": row['project_id'],
            "name": row['name'],
            "project_number": row['project_number'],
            "customer_id": row['customer_id'],
            "start_date": row['start_date'],
            "end_date": row['end_date'],
            "due_date": row['due_date'],
            "description": row['description'] or "",
            "status": row['status'],
            "class_id": row['class_id'],
            "billing_method": row['billing_method'],
            "contract_amount": row['contract_amount'] or 0.0,
            "estimated_revenue": row['estimated_revenue'] or 0.0,
            "estimated_cost": estimated_cost,
            "estimated_hours": row['estimated_hours'] or 0.0,
            "actual_revenue": round(actual_revenue, 2),
            "actual_cost": round(actual_cost, 2),
            "actual_hours": round(row['actual_hours'] or 0, 2),
            "gross_profit": round(gross_profit, 2),
            "budget_remaining": round(budget_remaining, 2),
            "percent_complete": round((actual_cost / estimated_cost * 100) if estimated_cost > 0 else 0, 1),
            "amount_billed": row['amount_billed'] or 0.0,
            "amount_received": row['amount_received'] or 0.0,
            "is_active": bool(row['is_active']),
            "created_at": row['created_at']
        }

    def _row_to_expense_dict(self, row: sqlite3.Row) -> Dict:
        """Convert expense row to dictionary"""
        return {
            "expense_id": row['expense_id'],
            "project_id": row['project_id'],
            "expense_date": row['expense_date'],
            "description": row['description'],
            "vendor_id": row['vendor_id'],
            "amount": row['amount'],
            "markup_percent": row['markup_percent'],
            "billable_amount": round(row['billable_amount'], 2),
            "status": row['status'],
            "invoice_id": row['invoice_id'],
            "billed_date": row['billed_date'],
            "notes": row['notes'] or ""
        }

    def _row_to_time_entry_dict(self, row: sqlite3.Row) -> Dict:
        """Convert time entry row to dictionary"""
        return {
            "time_entry_id": row['time_entry_id'],
            "project_id": row['project_id'],
            "entry_date": row['entry_date'],
            "employee_id": row['employee_id'],
            "employee_name": row['employee_name'] or "",
            "hours": row['hours'],
            "hourly_rate": row['hourly_rate'],
            "amount": round(row['amount'], 2),
            "is_billable": bool(row['is_billable']),
            "billable_rate": row['billable_rate'],
            "billable_amount": round(row['billable_amount'], 2),
            "status": row['status'],
            "invoice_id": row['invoice_id'],
            "description": row['description'] or ""
        }

    def _row_to_milestone_dict(self, row: sqlite3.Row) -> Dict:
        """Convert milestone row to dictionary"""
        return {
            "milestone_id": row['milestone_id'],
            "project_id": row['project_id'],
            "name": row['name'],
            "description": row['description'] or "",
            "amount": row['amount'],
            "percent_of_total": row['percent_of_total'],
            "due_date": row['due_date'],
            "completed_date": row['completed_date'],
            "is_completed": bool(row['is_completed']),
            "is_billed": bool(row['is_billed']),
            "order": row['sort_order']
        }

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM genfin_classes WHERE is_active = 1")
            total_classes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_projects WHERE is_active = 1")
            total_projects = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_projects WHERE is_active = 1 AND status = 'in_progress'")
            active_projects = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_billable_expenses")
            expenses_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_billable_time")
            time_count = cursor.fetchone()[0]

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
            "total_classes": total_classes,
            "total_projects": total_projects,
            "active_projects": active_projects,
            "billable_expenses_count": expenses_count,
            "billable_time_entries": time_count
        }


# Singleton instance
genfin_classes_service = GenFinClassesService()
