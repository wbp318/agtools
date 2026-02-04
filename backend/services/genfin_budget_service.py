"""
GenFin Budget Service - Budgets, Forecasting, Variance Analysis
Complete budgeting and planning for farm operations
SQLite persistence for data durability
"""

from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid
import sqlite3
import json

from .genfin_core_service import genfin_core_service
from .genfin_reports_service import genfin_reports_service


class BudgetType(Enum):
    """Budget types"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    PROJECT = "project"


class BudgetStatus(Enum):
    """Budget status"""
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ForecastMethod(Enum):
    """Forecasting methods"""
    TREND = "trend"
    AVERAGE = "average"
    SEASONAL = "seasonal"
    MANUAL = "manual"


@dataclass
class BudgetLine:
    """Budget line item"""
    line_id: str
    account_id: str
    period_amounts: Dict[str, float]  # {"2024-01": 1000, "2024-02": 1200, ...}
    notes: str = ""


@dataclass
class Budget:
    """Budget record"""
    budget_id: str
    name: str
    fiscal_year: int
    budget_type: BudgetType
    start_date: date
    end_date: date
    lines: List[BudgetLine]

    description: str = ""
    status: BudgetStatus = BudgetStatus.DRAFT
    created_by: str = ""
    approved_by: str = ""
    approved_at: Optional[datetime] = None

    # Totals
    total_revenue: float = 0.0
    total_expenses: float = 0.0
    net_budget: float = 0.0

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Forecast:
    """Forecast record"""
    forecast_id: str
    name: str
    base_budget_id: Optional[str]
    start_date: date
    end_date: date
    method: ForecastMethod

    # Forecasted values by account and period
    forecasted_values: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # {"account_id": {"2024-01": 1000, ...}}

    assumptions: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BudgetScenario:
    """Budget scenario for what-if analysis"""
    scenario_id: str
    name: str
    base_budget_id: str
    adjustments: Dict[str, float]  # {"account_id": percentage_change}
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class GenFinBudgetService:
    """
    GenFin Budget Service

    Complete budgeting functionality:
    - Annual/Quarterly/Monthly budgets
    - Budget vs Actual analysis
    - Variance reporting
    - Cash flow forecasting
    - Scenario planning
    - Rolling forecasts
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
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Drop old tables if schema changed (migration from in-memory)
            cursor.execute("DROP TABLE IF EXISTS genfin_budget_lines")
            cursor.execute("DROP TABLE IF EXISTS genfin_budgets")
            cursor.execute("DROP TABLE IF EXISTS genfin_forecasts")
            cursor.execute("DROP TABLE IF EXISTS genfin_scenarios")

            # Budgets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_budgets (
                    budget_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    budget_type TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'draft',
                    created_by TEXT DEFAULT '',
                    approved_by TEXT DEFAULT '',
                    approved_at TEXT,
                    total_revenue REAL DEFAULT 0.0,
                    total_expenses REAL DEFAULT 0.0,
                    net_budget REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Budget lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_budget_lines (
                    line_id TEXT PRIMARY KEY,
                    budget_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    period_amounts TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (budget_id) REFERENCES genfin_budgets(budget_id)
                )
            """)

            # Forecasts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_forecasts (
                    forecast_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_budget_id TEXT,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    method TEXT NOT NULL,
                    forecasted_values TEXT NOT NULL,
                    assumptions TEXT DEFAULT '',
                    created_by TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Scenarios table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_budget_id TEXT NOT NULL,
                    adjustments TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_lines_budget ON genfin_budget_lines(budget_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_fiscal_year ON genfin_budgets(fiscal_year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_status ON genfin_budgets(status)")

            conn.commit()

    def _row_to_budget(self, row: sqlite3.Row, include_lines: bool = True) -> Budget:
        """Convert database row to Budget object"""
        budget = Budget(
            budget_id=row["budget_id"],
            name=row["name"],
            fiscal_year=row["fiscal_year"],
            budget_type=BudgetType(row["budget_type"]),
            start_date=datetime.strptime(row["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(row["end_date"], "%Y-%m-%d").date(),
            lines=[],
            description=row["description"] or "",
            status=BudgetStatus(row["status"]),
            created_by=row["created_by"] or "",
            approved_by=row["approved_by"] or "",
            approved_at=datetime.fromisoformat(row["approved_at"]) if row["approved_at"] else None,
            total_revenue=row["total_revenue"] or 0.0,
            total_expenses=row["total_expenses"] or 0.0,
            net_budget=row["net_budget"] or 0.0,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

        if include_lines:
            budget.lines = self._get_budget_lines(budget.budget_id)

        return budget

    def _get_budget_lines(self, budget_id: str) -> List[BudgetLine]:
        """Get budget lines for a budget"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_budget_lines
                WHERE budget_id = ? AND is_active = 1
            """, (budget_id,))
            rows = cursor.fetchall()

            return [
                BudgetLine(
                    line_id=row["line_id"],
                    account_id=row["account_id"],
                    period_amounts=json.loads(row["period_amounts"]),
                    notes=row["notes"] or ""
                )
                for row in rows
            ]

    def _row_to_forecast(self, row: sqlite3.Row) -> Forecast:
        """Convert database row to Forecast object"""
        return Forecast(
            forecast_id=row["forecast_id"],
            name=row["name"],
            base_budget_id=row["base_budget_id"],
            start_date=datetime.strptime(row["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(row["end_date"], "%Y-%m-%d").date(),
            method=ForecastMethod(row["method"]),
            forecasted_values=json.loads(row["forecasted_values"]),
            assumptions=row["assumptions"] or "",
            created_by=row["created_by"] or "",
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def _row_to_scenario(self, row: sqlite3.Row) -> BudgetScenario:
        """Convert database row to BudgetScenario object"""
        return BudgetScenario(
            scenario_id=row["scenario_id"],
            name=row["name"],
            base_budget_id=row["base_budget_id"],
            adjustments=json.loads(row["adjustments"]),
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def _get_budget_by_id(self, budget_id: str) -> Optional[Budget]:
        """Get budget by ID from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_budgets
                WHERE budget_id = ? AND is_active = 1
            """, (budget_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_budget(row)
            return None

    def _save_budget(self, budget: Budget):
        """Save budget to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_budgets (
                    budget_id, name, fiscal_year, budget_type, start_date, end_date,
                    description, status, created_by, approved_by, approved_at,
                    total_revenue, total_expenses, net_budget, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                budget.budget_id, budget.name, budget.fiscal_year,
                budget.budget_type.value, budget.start_date.isoformat(), budget.end_date.isoformat(),
                budget.description, budget.status.value, budget.created_by, budget.approved_by,
                budget.approved_at.isoformat() if budget.approved_at else None,
                budget.total_revenue, budget.total_expenses, budget.net_budget,
                budget.created_at.isoformat(), budget.updated_at.isoformat()
            ))
            conn.commit()

    def _save_budget_line(self, budget_id: str, line: BudgetLine):
        """Save budget line to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_budget_lines (
                    line_id, budget_id, account_id, period_amounts, notes, is_active
                ) VALUES (?, ?, ?, ?, ?, 1)
            """, (
                line.line_id, budget_id, line.account_id,
                json.dumps(line.period_amounts), line.notes
            ))
            conn.commit()

    # ==================== BUDGET MANAGEMENT ====================

    def create_budget(
        self,
        name: str,
        fiscal_year: int,
        budget_type: str = "annual",
        description: str = "",
        created_by: str = "",
        copy_from_budget_id: Optional[str] = None,
        copy_from_actuals: bool = False
    ) -> Dict:
        """Create a new budget"""
        budget_id = str(uuid.uuid4())

        # Determine date range
        start_date = date(fiscal_year, 1, 1)
        end_date = date(fiscal_year, 12, 31)

        lines = []

        if copy_from_budget_id:
            source = self._get_budget_by_id(copy_from_budget_id)
            if source:
                for source_line in source.lines:
                    new_periods = {}
                    for period, amount in source_line.period_amounts.items():
                        # Adjust year in period key
                        new_period = f"{fiscal_year}-{period.split('-')[1]}"
                        new_periods[new_period] = amount

                    lines.append(BudgetLine(
                        line_id=str(uuid.uuid4()),
                        account_id=source_line.account_id,
                        period_amounts=new_periods,
                        notes=source_line.notes
                    ))

        elif copy_from_actuals:
            # Copy from prior year actuals
            prior_year = fiscal_year - 1
            _prior_start = date(prior_year, 1, 1)
            _prior_end = date(prior_year, 12, 31)

            # Get accounts from core service
            accounts = genfin_core_service.list_accounts()
            for acc_data in accounts:
                account = genfin_core_service.get_account(acc_data["account_id"])
                if not account:
                    continue
                acc_type = account.get("account_type", "")
                if acc_type not in ["revenue", "expense"]:
                    continue

                period_amounts = {}

                # Get each month's actuals
                for month in range(1, 13):
                    month_start = date(prior_year, month, 1)
                    if month == 12:
                        month_end = date(prior_year, 12, 31)
                    else:
                        month_end = date(prior_year, month + 1, 1) - timedelta(days=1)

                    actual = genfin_reports_service._get_account_balance_for_period(
                        acc_data["account_id"], month_start, month_end
                    )

                    if actual != 0:
                        period_key = f"{fiscal_year}-{month:02d}"
                        period_amounts[period_key] = actual

                if period_amounts:
                    lines.append(BudgetLine(
                        line_id=str(uuid.uuid4()),
                        account_id=acc_data["account_id"],
                        period_amounts=period_amounts
                    ))

        else:
            # Create empty budget with all revenue/expense accounts
            accounts = genfin_core_service.list_accounts()
            for acc_data in accounts:
                account = genfin_core_service.get_account(acc_data["account_id"])
                if not account:
                    continue
                acc_type = account.get("account_type", "")
                if acc_type not in ["revenue", "expense"]:
                    continue

                period_amounts = {f"{fiscal_year}-{m:02d}": 0.0 for m in range(1, 13)}

                lines.append(BudgetLine(
                    line_id=str(uuid.uuid4()),
                    account_id=acc_data["account_id"],
                    period_amounts=period_amounts
                ))

        budget = Budget(
            budget_id=budget_id,
            name=name,
            fiscal_year=fiscal_year,
            budget_type=BudgetType(budget_type),
            start_date=start_date,
            end_date=end_date,
            lines=lines,
            description=description,
            created_by=created_by
        )

        # Calculate totals
        self._calculate_budget_totals(budget)

        # Save to database
        self._save_budget(budget)
        for line in lines:
            self._save_budget_line(budget_id, line)

        return {
            "success": True,
            "budget_id": budget_id,
            "name": name,
            "line_count": len(lines)
        }

    def _calculate_budget_totals(self, budget: Budget):
        """Calculate budget totals"""
        total_revenue = 0.0
        total_expenses = 0.0

        for line in budget.lines:
            account = genfin_core_service.get_account(line.account_id)
            if not account:
                continue

            line_total = sum(line.period_amounts.values())
            acc_type = account.get("account_type", "")

            if acc_type == "revenue":
                total_revenue += line_total
            elif acc_type == "expense":
                total_expenses += line_total

        budget.total_revenue = round(total_revenue, 2)
        budget.total_expenses = round(total_expenses, 2)
        budget.net_budget = round(total_revenue - total_expenses, 2)

    def update_budget_line(
        self,
        budget_id: str,
        account_id: str,
        period_amounts: Dict[str, float],
        notes: str = ""
    ) -> Dict:
        """Update a budget line item"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return {"success": False, "error": "Budget not found"}

        if budget.status not in [BudgetStatus.DRAFT]:
            return {"success": False, "error": "Cannot modify active/closed budget"}

        # Find or create line
        line = None
        for budget_line in budget.lines:
            if budget_line.account_id == account_id:
                line = budget_line
                break

        if line:
            line.period_amounts.update(period_amounts)
            if notes:
                line.notes = notes
            self._save_budget_line(budget_id, line)
        else:
            new_line = BudgetLine(
                line_id=str(uuid.uuid4()),
                account_id=account_id,
                period_amounts=period_amounts,
                notes=notes
            )
            budget.lines.append(new_line)
            self._save_budget_line(budget_id, new_line)

        self._calculate_budget_totals(budget)
        budget.updated_at = datetime.now(timezone.utc)
        self._save_budget(budget)

        return {"success": True, "message": "Budget line updated"}

    def update_budget_line_monthly(
        self,
        budget_id: str,
        account_id: str,
        annual_amount: float,
        distribution: str = "even"
    ) -> Dict:
        """Update budget line with annual amount distributed across months"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return {"success": False, "error": "Budget not found"}

        if distribution == "even":
            monthly_amount = annual_amount / 12
            period_amounts = {
                f"{budget.fiscal_year}-{m:02d}": round(monthly_amount, 2)
                for m in range(1, 13)
            }
        elif distribution == "seasonal_crop":
            # Typical crop cycle - higher in spring/fall
            seasonal_weights = {
                1: 0.05, 2: 0.05, 3: 0.10, 4: 0.15, 5: 0.12, 6: 0.08,
                7: 0.05, 8: 0.05, 9: 0.10, 10: 0.15, 11: 0.07, 12: 0.03
            }
            period_amounts = {
                f"{budget.fiscal_year}-{m:02d}": round(annual_amount * seasonal_weights[m], 2)
                for m in range(1, 13)
            }
        elif distribution == "harvest":
            # Revenue concentrated in harvest months
            harvest_weights = {
                1: 0.02, 2: 0.02, 3: 0.02, 4: 0.02, 5: 0.02, 6: 0.05,
                7: 0.10, 8: 0.15, 9: 0.20, 10: 0.25, 11: 0.10, 12: 0.05
            }
            period_amounts = {
                f"{budget.fiscal_year}-{m:02d}": round(annual_amount * harvest_weights[m], 2)
                for m in range(1, 13)
            }
        else:
            period_amounts = {
                f"{budget.fiscal_year}-{m:02d}": round(annual_amount / 12, 2)
                for m in range(1, 13)
            }

        return self.update_budget_line(budget_id, account_id, period_amounts)

    def activate_budget(self, budget_id: str, approved_by: str) -> Dict:
        """Activate a budget"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return {"success": False, "error": "Budget not found"}

        budget.status = BudgetStatus.ACTIVE
        budget.approved_by = approved_by
        budget.approved_at = datetime.now(timezone.utc)
        budget.updated_at = datetime.now(timezone.utc)
        self._save_budget(budget)

        return {"success": True, "message": "Budget activated"}

    def close_budget(self, budget_id: str) -> Dict:
        """Close a budget"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return {"success": False, "error": "Budget not found"}

        budget.status = BudgetStatus.CLOSED
        budget.updated_at = datetime.now(timezone.utc)
        self._save_budget(budget)

        return {"success": True, "message": "Budget closed"}

    def get_budget(self, budget_id: str) -> Optional[Dict]:
        """Get budget by ID"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return None
        return self._budget_to_dict(budget)

    def list_budgets(
        self,
        fiscal_year: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """List budgets with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_budgets WHERE is_active = 1"
            params = []

            if fiscal_year:
                query += " AND fiscal_year = ?"
                params.append(fiscal_year)
            if status:
                query += " AND status = ?"
                params.append(status)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    "budget_id": row["budget_id"],
                    "name": row["name"],
                    "fiscal_year": row["fiscal_year"],
                    "budget_type": row["budget_type"],
                    "status": row["status"],
                    "total_revenue": row["total_revenue"],
                    "total_expenses": row["total_expenses"],
                    "net_budget": row["net_budget"],
                    "created_at": row["created_at"]
                })

            return sorted(result, key=lambda b: (b["fiscal_year"], b["name"]), reverse=True)

    # ==================== BUDGET VS ACTUAL ====================

    def get_budget_vs_actual(
        self,
        budget_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        summary_only: bool = False
    ) -> Dict:
        """Get budget vs actual comparison"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return {"error": "Budget not found"}

        # Determine date range
        if start_date:
            s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        else:
            s_date = budget.start_date

        if end_date:
            e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            e_date = min(budget.end_date, date.today())

        # Get periods in range
        periods = []
        current = date(s_date.year, s_date.month, 1)
        while current <= e_date:
            periods.append(f"{current.year}-{current.month:02d}")
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        # Calculate for each account
        revenue_items = []
        expense_items = []

        total_budget_revenue = 0.0
        total_actual_revenue = 0.0
        total_budget_expense = 0.0
        total_actual_expense = 0.0

        for line in budget.lines:
            account = genfin_core_service.get_account(line.account_id)
            if not account:
                continue

            # Sum budget for periods
            budget_amount = sum(
                line.period_amounts.get(p, 0) for p in periods
            )

            # Get actual from ledger
            actual_amount = genfin_reports_service._get_account_balance_for_period(
                line.account_id, s_date, e_date
            )

            variance = actual_amount - budget_amount
            variance_pct = (variance / budget_amount * 100) if budget_amount != 0 else 0

            acc_type = account.get("account_type", "")
            item = {
                "account_id": line.account_id,
                "account_number": account.get("account_number", ""),
                "account_name": account.get("name", "Unknown"),
                "budget": round(budget_amount, 2),
                "actual": round(actual_amount, 2),
                "variance": round(variance, 2),
                "variance_percent": round(variance_pct, 1),
                "favorable": (variance > 0) if acc_type == "revenue" else (variance < 0)
            }

            if acc_type == "revenue":
                revenue_items.append(item)
                total_budget_revenue += budget_amount
                total_actual_revenue += actual_amount
            else:
                expense_items.append(item)
                total_budget_expense += budget_amount
                total_actual_expense += actual_amount

        # Calculate net
        budget_net = total_budget_revenue - total_budget_expense
        actual_net = total_actual_revenue - total_actual_expense
        net_variance = actual_net - budget_net

        result = {
            "report_type": "Budget vs Actual",
            "budget_name": budget.name,
            "period_start": s_date.isoformat(),
            "period_end": e_date.isoformat(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "revenue": {
                    "budget": round(total_budget_revenue, 2),
                    "actual": round(total_actual_revenue, 2),
                    "variance": round(total_actual_revenue - total_budget_revenue, 2),
                    "variance_percent": round((total_actual_revenue - total_budget_revenue) / total_budget_revenue * 100, 1) if total_budget_revenue > 0 else 0
                },
                "expenses": {
                    "budget": round(total_budget_expense, 2),
                    "actual": round(total_actual_expense, 2),
                    "variance": round(total_actual_expense - total_budget_expense, 2),
                    "variance_percent": round((total_actual_expense - total_budget_expense) / total_budget_expense * 100, 1) if total_budget_expense > 0 else 0
                },
                "net_income": {
                    "budget": round(budget_net, 2),
                    "actual": round(actual_net, 2),
                    "variance": round(net_variance, 2),
                    "favorable": net_variance > 0
                }
            }
        }

        if not summary_only:
            result["revenue_detail"] = sorted(revenue_items, key=lambda x: x["account_number"])
            result["expense_detail"] = sorted(expense_items, key=lambda x: x["account_number"])

        return result

    def get_monthly_variance(self, budget_id: str) -> Dict:
        """Get month-by-month variance analysis"""
        budget = self._get_budget_by_id(budget_id)
        if not budget:
            return {"error": "Budget not found"}

        months = []

        for month in range(1, 13):
            month_start = date(budget.fiscal_year, month, 1)
            if month == 12:
                month_end = date(budget.fiscal_year, 12, 31)
            else:
                month_end = date(budget.fiscal_year, month + 1, 1) - timedelta(days=1)

            period_key = f"{budget.fiscal_year}-{month:02d}"

            # Only include months up to today
            if month_start > date.today():
                break

            budget_revenue = 0.0
            budget_expense = 0.0
            actual_revenue = 0.0
            actual_expense = 0.0

            for line in budget.lines:
                account = genfin_core_service.get_account(line.account_id)
                if not account:
                    continue

                budget_amount = line.period_amounts.get(period_key, 0)
                actual_amount = genfin_reports_service._get_account_balance_for_period(
                    line.account_id, month_start, month_end
                )

                acc_type = account.get("account_type", "")
                if acc_type == "revenue":
                    budget_revenue += budget_amount
                    actual_revenue += actual_amount
                else:
                    budget_expense += budget_amount
                    actual_expense += actual_amount

            months.append({
                "month": period_key,
                "month_name": month_start.strftime("%B"),
                "budget_revenue": round(budget_revenue, 2),
                "actual_revenue": round(actual_revenue, 2),
                "revenue_variance": round(actual_revenue - budget_revenue, 2),
                "budget_expense": round(budget_expense, 2),
                "actual_expense": round(actual_expense, 2),
                "expense_variance": round(actual_expense - budget_expense, 2),
                "budget_net": round(budget_revenue - budget_expense, 2),
                "actual_net": round(actual_revenue - actual_expense, 2),
                "net_variance": round((actual_revenue - actual_expense) - (budget_revenue - budget_expense), 2)
            })

        return {
            "budget_name": budget.name,
            "fiscal_year": budget.fiscal_year,
            "months": months
        }

    # ==================== FORECASTING ====================

    def create_forecast(
        self,
        name: str,
        start_date: str,
        end_date: str,
        method: str = "trend",
        base_budget_id: Optional[str] = None,
        assumptions: str = "",
        created_by: str = ""
    ) -> Dict:
        """Create a financial forecast"""
        forecast_id = str(uuid.uuid4())
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        forecasted_values = {}

        if method == "trend":
            # Use 12-month trend to project forward
            forecasted_values = self._forecast_by_trend(s_date, e_date)
        elif method == "average":
            # Use average of past 12 months
            forecasted_values = self._forecast_by_average(s_date, e_date)
        elif method == "seasonal":
            # Use same month from prior year with growth
            forecasted_values = self._forecast_by_seasonal(s_date, e_date)

        forecast = Forecast(
            forecast_id=forecast_id,
            name=name,
            base_budget_id=base_budget_id,
            start_date=s_date,
            end_date=e_date,
            method=ForecastMethod(method),
            forecasted_values=forecasted_values,
            assumptions=assumptions,
            created_by=created_by
        )

        # Save to database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_forecasts (
                    forecast_id, name, base_budget_id, start_date, end_date,
                    method, forecasted_values, assumptions, created_by, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                forecast.forecast_id, forecast.name, forecast.base_budget_id,
                forecast.start_date.isoformat(), forecast.end_date.isoformat(),
                forecast.method.value, json.dumps(forecast.forecasted_values),
                forecast.assumptions, forecast.created_by, forecast.created_at.isoformat()
            ))
            conn.commit()

        return {
            "success": True,
            "forecast_id": forecast_id,
            "name": name,
            "method": method,
            "accounts_forecasted": len(forecasted_values)
        }

    def _forecast_by_trend(self, start_date: date, end_date: date) -> Dict:
        """Forecast using linear trend"""
        forecasted = {}

        # Get historical data (past 12 months)
        hist_end = start_date - timedelta(days=1)
        hist_start = date(hist_end.year - 1, hist_end.month, 1)

        accounts = genfin_core_service.list_accounts()
        for acc_data in accounts:
            account = genfin_core_service.get_account(acc_data["account_id"])
            if not account:
                continue
            acc_type = account.get("account_type", "")
            if acc_type not in ["revenue", "expense"]:
                continue

            # Get monthly historical data
            monthly_data = []
            current = hist_start
            while current <= hist_end:
                if current.month == 12:
                    month_end = date(current.year, 12, 31)
                else:
                    month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)

                amount = genfin_reports_service._get_account_balance_for_period(
                    acc_data["account_id"], current, month_end
                )
                monthly_data.append(amount)

                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

            if not monthly_data or sum(monthly_data) == 0:
                continue

            # Simple linear trend
            n = len(monthly_data)
            avg_amount = sum(monthly_data) / n
            trend = (monthly_data[-1] - monthly_data[0]) / n if n > 1 else 0

            # Generate forecast periods
            account_forecast = {}
            current = start_date
            month_idx = 0

            while current <= end_date:
                period_key = f"{current.year}-{current.month:02d}"
                projected = avg_amount + (trend * (n + month_idx))
                account_forecast[period_key] = round(max(0, projected), 2)

                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)
                month_idx += 1

            forecasted[acc_data["account_id"]] = account_forecast

        return forecasted

    def _forecast_by_average(self, start_date: date, end_date: date) -> Dict:
        """Forecast using simple average"""
        forecasted = {}

        hist_end = start_date - timedelta(days=1)
        hist_start = date(hist_end.year - 1, hist_end.month, 1)

        accounts = genfin_core_service.list_accounts()
        for acc_data in accounts:
            account = genfin_core_service.get_account(acc_data["account_id"])
            if not account:
                continue
            acc_type = account.get("account_type", "")
            if acc_type not in ["revenue", "expense"]:
                continue

            # Get total for past year
            total = genfin_reports_service._get_account_balance_for_period(
                acc_data["account_id"], hist_start, hist_end
            )

            if total == 0:
                continue

            monthly_avg = total / 12

            # Generate forecast periods
            account_forecast = {}
            current = start_date

            while current <= end_date:
                period_key = f"{current.year}-{current.month:02d}"
                account_forecast[period_key] = round(monthly_avg, 2)

                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

            forecasted[acc_data["account_id"]] = account_forecast

        return forecasted

    def _forecast_by_seasonal(self, start_date: date, end_date: date, growth_rate: float = 0.03) -> Dict:
        """Forecast using seasonal pattern from prior year"""
        forecasted = {}

        accounts = genfin_core_service.list_accounts()
        for acc_data in accounts:
            account = genfin_core_service.get_account(acc_data["account_id"])
            if not account:
                continue
            acc_type = account.get("account_type", "")
            if acc_type not in ["revenue", "expense"]:
                continue

            account_forecast = {}
            current = start_date

            while current <= end_date:
                # Get same month from prior year
                prior_month_start = date(current.year - 1, current.month, 1)
                if current.month == 12:
                    prior_month_end = date(current.year - 1, 12, 31)
                else:
                    prior_month_end = date(current.year - 1, current.month + 1, 1) - timedelta(days=1)

                prior_amount = genfin_reports_service._get_account_balance_for_period(
                    acc_data["account_id"], prior_month_start, prior_month_end
                )

                # Apply growth rate
                projected = prior_amount * (1 + growth_rate)

                period_key = f"{current.year}-{current.month:02d}"
                account_forecast[period_key] = round(projected, 2)

                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

            if sum(account_forecast.values()) != 0:
                forecasted[acc_data["account_id"]] = account_forecast

        return forecasted

    def get_forecast(self, forecast_id: str) -> Optional[Dict]:
        """Get forecast by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_forecasts
                WHERE forecast_id = ? AND is_active = 1
            """, (forecast_id,))
            row = cursor.fetchone()
            if row:
                forecast = self._row_to_forecast(row)
                return self._forecast_to_dict(forecast)
            return None

    def get_forecast_summary(self, forecast_id: str) -> Dict:
        """Get summary of forecasted amounts"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_forecasts
                WHERE forecast_id = ? AND is_active = 1
            """, (forecast_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": "Forecast not found"}

            forecast = self._row_to_forecast(row)

        total_revenue = 0.0
        total_expense = 0.0
        monthly_totals = {}

        for account_id, periods in forecast.forecasted_values.items():
            account = genfin_core_service.get_account(account_id)
            if not account:
                continue

            acc_type = account.get("account_type", "")
            for period, amount in periods.items():
                if period not in monthly_totals:
                    monthly_totals[period] = {"revenue": 0, "expense": 0}

                if acc_type == "revenue":
                    total_revenue += amount
                    monthly_totals[period]["revenue"] += amount
                else:
                    total_expense += amount
                    monthly_totals[period]["expense"] += amount

        return {
            "forecast_name": forecast.name,
            "method": forecast.method.value,
            "period": f"{forecast.start_date.isoformat()} to {forecast.end_date.isoformat()}",
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "total_expenses": round(total_expense, 2),
                "net_income": round(total_revenue - total_expense, 2)
            },
            "monthly": [
                {
                    "period": p,
                    "revenue": round(v["revenue"], 2),
                    "expense": round(v["expense"], 2),
                    "net": round(v["revenue"] - v["expense"], 2)
                }
                for p, v in sorted(monthly_totals.items())
            ]
        }

    def list_forecasts(self) -> List[Dict]:
        """List all forecasts"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_forecasts WHERE is_active = 1
            """)
            rows = cursor.fetchall()

            return [
                {
                    "forecast_id": row["forecast_id"],
                    "name": row["name"],
                    "method": row["method"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "created_by": row["created_by"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

    # ==================== SCENARIO PLANNING ====================

    def create_scenario(
        self,
        name: str,
        base_budget_id: str,
        adjustments: Dict[str, float],
        description: str = ""
    ) -> Dict:
        """Create a budget scenario (what-if analysis)"""
        budget = self._get_budget_by_id(base_budget_id)
        if not budget:
            return {"success": False, "error": "Base budget not found"}

        scenario_id = str(uuid.uuid4())

        scenario = BudgetScenario(
            scenario_id=scenario_id,
            name=name,
            base_budget_id=base_budget_id,
            adjustments=adjustments,
            description=description
        )

        # Save to database
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_scenarios (
                    scenario_id, name, base_budget_id, adjustments,
                    description, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                scenario.scenario_id, scenario.name, scenario.base_budget_id,
                json.dumps(scenario.adjustments), scenario.description,
                scenario.created_at.isoformat()
            ))
            conn.commit()

        return {
            "success": True,
            "scenario_id": scenario_id,
            "name": name
        }

    def run_scenario(self, scenario_id: str) -> Dict:
        """Run a budget scenario and get projected results"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_scenarios
                WHERE scenario_id = ? AND is_active = 1
            """, (scenario_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": "Scenario not found"}

            scenario = self._row_to_scenario(row)

        budget = self._get_budget_by_id(scenario.base_budget_id)
        if not budget:
            return {"error": "Base budget not found"}

        # Calculate adjusted amounts
        revenue_items = []
        expense_items = []
        total_revenue = 0.0
        total_expenses = 0.0

        for line in budget.lines:
            account = genfin_core_service.get_account(line.account_id)
            if not account:
                continue

            base_amount = sum(line.period_amounts.values())
            adjustment_pct = scenario.adjustments.get(line.account_id, 0)
            adjusted_amount = base_amount * (1 + adjustment_pct / 100)

            item = {
                "account_id": line.account_id,
                "account_name": account.get("name", "Unknown"),
                "base_amount": round(base_amount, 2),
                "adjustment_percent": adjustment_pct,
                "adjusted_amount": round(adjusted_amount, 2),
                "difference": round(adjusted_amount - base_amount, 2)
            }

            acc_type = account.get("account_type", "")
            if acc_type == "revenue":
                revenue_items.append(item)
                total_revenue += adjusted_amount
            else:
                expense_items.append(item)
                total_expenses += adjusted_amount

        base_net = budget.net_budget
        scenario_net = total_revenue - total_expenses

        return {
            "scenario_name": scenario.name,
            "base_budget": budget.name,
            "description": scenario.description,
            "revenue": {
                "items": revenue_items,
                "base_total": budget.total_revenue,
                "scenario_total": round(total_revenue, 2),
                "difference": round(total_revenue - budget.total_revenue, 2)
            },
            "expenses": {
                "items": expense_items,
                "base_total": budget.total_expenses,
                "scenario_total": round(total_expenses, 2),
                "difference": round(total_expenses - budget.total_expenses, 2)
            },
            "net_income": {
                "base": round(base_net, 2),
                "scenario": round(scenario_net, 2),
                "difference": round(scenario_net - base_net, 2),
                "percent_change": round((scenario_net - base_net) / base_net * 100, 1) if base_net != 0 else 0
            }
        }

    def list_scenarios(self) -> List[Dict]:
        """List all scenarios"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_scenarios WHERE is_active = 1
            """)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                adjustments = json.loads(row["adjustments"])
                result.append({
                    "scenario_id": row["scenario_id"],
                    "name": row["name"],
                    "base_budget_id": row["base_budget_id"],
                    "description": row["description"],
                    "adjustments_count": len(adjustments),
                    "created_at": row["created_at"]
                })

            return result

    # ==================== CASH FLOW PROJECTION ====================

    def get_cash_flow_projection(
        self,
        start_date: str,
        months_ahead: int = 12,
        starting_cash: float = 0.0
    ) -> Dict:
        """Project cash flow for upcoming months"""
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        # Get starting cash from balance sheet if not provided
        if starting_cash == 0:
            accounts = genfin_core_service.list_accounts()
            for acc_data in accounts:
                account = genfin_core_service.get_account(acc_data["account_id"])
                if account and account.get("sub_type") in ["cash", "bank"]:
                    starting_cash += genfin_core_service.get_account_balance(
                        acc_data["account_id"], start_date
                    )

        projections = []
        running_cash = starting_cash

        current = date(s_date.year, s_date.month, 1)

        for i in range(months_ahead):
            # Use seasonal forecast for projections
            period_key = f"{current.year}-{current.month:02d}"

            # Get any budget data
            projected_inflows = 0.0
            projected_outflows = 0.0

            # Check active budgets
            active_budgets = self.list_budgets(fiscal_year=current.year, status="active")
            for budget_info in active_budgets:
                budget = self._get_budget_by_id(budget_info["budget_id"])
                if not budget:
                    continue

                for line in budget.lines:
                    account = genfin_core_service.get_account(line.account_id)
                    if not account:
                        continue

                    amount = line.period_amounts.get(period_key, 0)
                    acc_type = account.get("account_type", "")

                    if acc_type == "revenue":
                        projected_inflows += amount
                    elif acc_type == "expense":
                        projected_outflows += amount

            # If no budget, use trend forecast
            if projected_inflows == 0 and projected_outflows == 0:
                hist_month_start = date(current.year - 1, current.month, 1)
                if current.month == 12:
                    hist_month_end = date(current.year - 1, 12, 31)
                else:
                    hist_month_end = date(current.year - 1, current.month + 1, 1) - timedelta(days=1)

                accounts = genfin_core_service.list_accounts()
                for acc_data in accounts:
                    account = genfin_core_service.get_account(acc_data["account_id"])
                    if not account:
                        continue

                    hist_amount = genfin_reports_service._get_account_balance_for_period(
                        acc_data["account_id"], hist_month_start, hist_month_end
                    )

                    acc_type = account.get("account_type", "")
                    if acc_type == "revenue":
                        projected_inflows += hist_amount * 1.03  # 3% growth
                    elif acc_type == "expense":
                        projected_outflows += hist_amount * 1.03

            net_change = projected_inflows - projected_outflows
            ending_cash = running_cash + net_change

            projections.append({
                "period": period_key,
                "month_name": current.strftime("%B %Y"),
                "beginning_cash": round(running_cash, 2),
                "projected_inflows": round(projected_inflows, 2),
                "projected_outflows": round(projected_outflows, 2),
                "net_change": round(net_change, 2),
                "ending_cash": round(ending_cash, 2),
                "cash_warning": ending_cash < 0
            })

            running_cash = ending_cash

            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

        return {
            "report_type": "Cash Flow Projection",
            "start_date": start_date,
            "months_projected": months_ahead,
            "starting_cash": round(starting_cash, 2),
            "projections": projections,
            "lowest_cash": min(p["ending_cash"] for p in projections) if projections else 0,
            "has_cash_shortfall": any(p["cash_warning"] for p in projections)
        }

    # ==================== UTILITY METHODS ====================

    def _budget_to_dict(self, budget: Budget) -> Dict:
        """Convert Budget to dictionary"""
        lines_data = []
        for line in budget.lines:
            account = genfin_core_service.get_account(line.account_id)
            lines_data.append({
                "line_id": line.line_id,
                "account_id": line.account_id,
                "account_number": account.get("account_number", "") if account else "",
                "account_name": account.get("name", "Unknown") if account else "Unknown",
                "period_amounts": line.period_amounts,
                "total": sum(line.period_amounts.values()),
                "notes": line.notes
            })

        return {
            "budget_id": budget.budget_id,
            "name": budget.name,
            "fiscal_year": budget.fiscal_year,
            "budget_type": budget.budget_type.value,
            "start_date": budget.start_date.isoformat(),
            "end_date": budget.end_date.isoformat(),
            "description": budget.description,
            "status": budget.status.value,
            "lines": sorted(lines_data, key=lambda line: line["account_number"]),
            "total_revenue": budget.total_revenue,
            "total_expenses": budget.total_expenses,
            "net_budget": budget.net_budget,
            "created_by": budget.created_by,
            "approved_by": budget.approved_by,
            "approved_at": budget.approved_at.isoformat() if budget.approved_at else None,
            "created_at": budget.created_at.isoformat()
        }

    def _forecast_to_dict(self, forecast: Forecast) -> Dict:
        """Convert Forecast to dictionary"""
        values_with_names = {}
        for account_id, periods in forecast.forecasted_values.items():
            account = genfin_core_service.get_account(account_id)
            values_with_names[account_id] = {
                "account_name": account.get("name", "Unknown") if account else "Unknown",
                "periods": periods
            }

        return {
            "forecast_id": forecast.forecast_id,
            "name": forecast.name,
            "base_budget_id": forecast.base_budget_id,
            "start_date": forecast.start_date.isoformat(),
            "end_date": forecast.end_date.isoformat(),
            "method": forecast.method.value,
            "forecasted_values": values_with_names,
            "assumptions": forecast.assumptions,
            "created_by": forecast.created_by,
            "created_at": forecast.created_at.isoformat()
        }

    def get_service_summary(self) -> Dict:
        """Get GenFin Budget service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM genfin_budgets WHERE is_active = 1")
            total_budgets = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_budgets WHERE is_active = 1 AND status = 'active'")
            active_budgets = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_forecasts WHERE is_active = 1")
            total_forecasts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_scenarios WHERE is_active = 1")
            total_scenarios = cursor.fetchone()[0]

        return {
            "service": "GenFin Budget",
            "version": "1.0.0",
            "features": [
                "Annual/Quarterly/Monthly Budgets",
                "Budget vs Actual Analysis",
                "Variance Reporting",
                "Financial Forecasting",
                "Scenario Planning (What-If)",
                "Cash Flow Projections",
                "Seasonal Distribution"
            ],
            "total_budgets": total_budgets,
            "active_budgets": active_budgets,
            "total_forecasts": total_forecasts,
            "total_scenarios": total_scenarios
        }


# Singleton instance
genfin_budget_service = GenFinBudgetService()
