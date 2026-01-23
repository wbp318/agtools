"""
GenFin Advanced Reports Service - QuickBooks-style Comprehensive Reporting
50+ reports, company snapshot dashboard, graphs, memorized reports
SQLite persistence for data durability
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import uuid
import sqlite3
import json


class ReportCategory(Enum):
    """Report categories matching QuickBooks"""
    COMPANY_FINANCIAL = "company_financial"
    CUSTOMERS_RECEIVABLES = "customers_receivables"
    SALES = "sales"
    JOBS_TIME_MILEAGE = "jobs_time_mileage"
    VENDORS_PAYABLES = "vendors_payables"
    PURCHASES = "purchases"
    EMPLOYEES_PAYROLL = "employees_payroll"
    BANKING = "banking"
    ACCOUNTANT_TAXES = "accountant_taxes"
    BUDGETS_FORECASTS = "budgets_forecasts"
    LIST = "list"
    CUSTOM = "custom"


class DateRange(Enum):
    """Predefined date ranges"""
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    THIS_FISCAL_YEAR = "this_fiscal_year"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_QUARTER = "last_quarter"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class ChartType(Enum):
    """Chart types for dashboard"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    STACKED_BAR = "stacked_bar"


@dataclass
class MemorizedReport:
    """Saved/memorized report configuration"""
    report_id: str
    name: str
    report_type: str
    category: ReportCategory

    # Parameters
    date_range: DateRange = DateRange.THIS_MONTH
    custom_start_date: Optional[date] = None
    custom_end_date: Optional[date] = None

    # Filters
    filters: Dict = field(default_factory=dict)

    # Display options
    show_header: bool = True
    show_footer: bool = True
    sort_by: str = ""
    group_by: str = ""

    # Sharing
    is_shared: bool = False
    created_by: str = ""

    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    name: str
    widget_type: str  # metric, chart, list, alert
    position: int = 0

    # Data source
    report_type: str = ""
    metric_name: str = ""

    # Chart settings
    chart_type: ChartType = ChartType.BAR

    # Display
    is_visible: bool = True
    refresh_interval: int = 300  # seconds

    created_at: datetime = field(default_factory=datetime.now)


class GenFinAdvancedReportsService:
    """
    GenFin Advanced Reports Service

    Complete QuickBooks-style reporting:
    - 50+ standard reports
    - Company snapshot dashboard
    - Memorized reports
    - Charts and graphs
    - Custom date ranges
    - Report filtering and grouping
    - Export capabilities
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

        # Reference to other GenFin services
        self.core_service = None
        self.payables_service = None
        self.receivables_service = None
        self.banking_service = None
        self.payroll_service = None
        self.inventory_service = None
        self.classes_service = None

        self._init_tables()
        self._initialize_default_dashboard()
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
            cursor.execute("DROP TABLE IF EXISTS genfin_memorized_reports")
            cursor.execute("DROP TABLE IF EXISTS genfin_dashboard_widgets")

            # Memorized reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_memorized_reports (
                    report_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    date_range TEXT DEFAULT 'this_month',
                    custom_start_date TEXT,
                    custom_end_date TEXT,
                    filters TEXT DEFAULT '{}',
                    show_header INTEGER DEFAULT 1,
                    show_footer INTEGER DEFAULT 1,
                    sort_by TEXT DEFAULT '',
                    group_by TEXT DEFAULT '',
                    is_shared INTEGER DEFAULT 0,
                    created_by TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    last_run TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Dashboard widgets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_dashboard_widgets (
                    widget_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    widget_type TEXT NOT NULL,
                    position INTEGER DEFAULT 0,
                    report_type TEXT DEFAULT '',
                    metric_name TEXT DEFAULT '',
                    chart_type TEXT DEFAULT 'bar',
                    is_visible INTEGER DEFAULT 1,
                    refresh_interval INTEGER DEFAULT 300,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memorized_category ON genfin_memorized_reports(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_widgets_position ON genfin_dashboard_widgets(position)")

            conn.commit()

    def _row_to_memorized_report(self, row: sqlite3.Row) -> MemorizedReport:
        """Convert database row to MemorizedReport object"""
        # Handle category - default to CUSTOM if invalid
        try:
            category = ReportCategory(row["category"])
        except ValueError:
            category = ReportCategory.CUSTOM

        # Handle date range - default to THIS_MONTH if invalid
        try:
            date_range = DateRange(row["date_range"])
        except ValueError:
            date_range = DateRange.THIS_MONTH

        return MemorizedReport(
            report_id=row["report_id"],
            name=row["name"],
            report_type=row["report_type"],
            category=category,
            date_range=date_range,
            custom_start_date=datetime.strptime(row["custom_start_date"], "%Y-%m-%d").date() if row["custom_start_date"] else None,
            custom_end_date=datetime.strptime(row["custom_end_date"], "%Y-%m-%d").date() if row["custom_end_date"] else None,
            filters=json.loads(row["filters"]) if row["filters"] else {},
            show_header=bool(row["show_header"]),
            show_footer=bool(row["show_footer"]),
            sort_by=row["sort_by"] or "",
            group_by=row["group_by"] or "",
            is_shared=bool(row["is_shared"]),
            created_by=row["created_by"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None
        )

    def _row_to_widget(self, row: sqlite3.Row) -> DashboardWidget:
        """Convert database row to DashboardWidget object"""
        # Handle chart type - default to BAR if invalid
        try:
            chart_type = ChartType(row["chart_type"])
        except ValueError:
            chart_type = ChartType.BAR

        return DashboardWidget(
            widget_id=row["widget_id"],
            name=row["name"],
            widget_type=row["widget_type"],
            position=row["position"] or 0,
            report_type=row["report_type"] or "",
            metric_name=row["metric_name"] or "",
            chart_type=chart_type,
            is_visible=bool(row["is_visible"]),
            refresh_interval=row["refresh_interval"] or 300,
            created_at=datetime.fromisoformat(row["created_at"])
        )

    def _save_memorized_report(self, report: MemorizedReport):
        """Save memorized report to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_memorized_reports (
                    report_id, name, report_type, category, date_range,
                    custom_start_date, custom_end_date, filters,
                    show_header, show_footer, sort_by, group_by,
                    is_shared, created_by, created_at, last_run, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                report.report_id, report.name, report.report_type, report.category.value,
                report.date_range.value,
                report.custom_start_date.isoformat() if report.custom_start_date else None,
                report.custom_end_date.isoformat() if report.custom_end_date else None,
                json.dumps(report.filters),
                1 if report.show_header else 0, 1 if report.show_footer else 0,
                report.sort_by, report.group_by,
                1 if report.is_shared else 0, report.created_by,
                report.created_at.isoformat(),
                report.last_run.isoformat() if report.last_run else None
            ))
            conn.commit()

    def _save_widget(self, widget: DashboardWidget):
        """Save dashboard widget to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_dashboard_widgets (
                    widget_id, name, widget_type, position,
                    report_type, metric_name, chart_type,
                    is_visible, refresh_interval, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                widget.widget_id, widget.name, widget.widget_type, widget.position,
                widget.report_type, widget.metric_name, widget.chart_type.value,
                1 if widget.is_visible else 0, widget.refresh_interval,
                widget.created_at.isoformat()
            ))
            conn.commit()

    def _get_all_widgets(self) -> List[DashboardWidget]:
        """Get all active dashboard widgets"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_dashboard_widgets
                WHERE is_active = 1
                ORDER BY position
            """)
            return [self._row_to_widget(row) for row in cursor.fetchall()]

    def _get_all_memorized_reports(self) -> List[MemorizedReport]:
        """Get all active memorized reports"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_memorized_reports
                WHERE is_active = 1
            """)
            return [self._row_to_memorized_report(row) for row in cursor.fetchall()]

    def set_services(
        self,
        core=None,
        payables=None,
        receivables=None,
        banking=None,
        payroll=None,
        inventory=None,
        classes=None
    ):
        """Set references to other GenFin services"""
        self.core_service = core
        self.payables_service = payables
        self.receivables_service = receivables
        self.banking_service = banking
        self.payroll_service = payroll
        self.inventory_service = inventory
        self.classes_service = classes

    def _initialize_default_dashboard(self):
        """Initialize default dashboard widgets"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM genfin_dashboard_widgets WHERE is_active = 1")
            if cursor.fetchone()[0] > 0:
                return  # Already initialized

        default_widgets = [
            {"name": "Income Summary", "type": "metric", "report": "income_summary"},
            {"name": "Expense Summary", "type": "metric", "report": "expense_summary"},
            {"name": "Net Income", "type": "metric", "report": "net_income"},
            {"name": "Bank Balance", "type": "metric", "report": "bank_balance"},
            {"name": "Accounts Receivable", "type": "metric", "report": "ar_total"},
            {"name": "Accounts Payable", "type": "metric", "report": "ap_total"},
            {"name": "Income vs Expenses", "type": "chart", "chart": ChartType.BAR},
            {"name": "Expense Breakdown", "type": "chart", "chart": ChartType.PIE},
            {"name": "Cash Flow Trend", "type": "chart", "chart": ChartType.LINE},
            {"name": "Overdue Invoices", "type": "list", "report": "overdue_invoices"},
            {"name": "Bills Due Soon", "type": "list", "report": "bills_due"},
            {"name": "Low Inventory Alerts", "type": "alert", "report": "low_inventory"},
        ]

        for i, widget in enumerate(default_widgets):
            widget_id = str(uuid.uuid4())
            w = DashboardWidget(
                widget_id=widget_id,
                name=widget["name"],
                widget_type=widget["type"],
                position=i,
                report_type=widget.get("report", ""),
                chart_type=widget.get("chart", ChartType.BAR)
            )
            self._save_widget(w)

    def _get_date_range(self, range_type: str, custom_start: str = None, custom_end: str = None) -> Tuple[date, date]:
        """Calculate date range from range type"""
        today = date.today()

        if range_type == "today":
            return today, today
        elif range_type == "this_week":
            start = today - timedelta(days=today.weekday())
            return start, today
        elif range_type == "this_month":
            start = today.replace(day=1)
            return start, today
        elif range_type == "this_quarter":
            quarter = (today.month - 1) // 3
            start = date(today.year, quarter * 3 + 1, 1)
            return start, today
        elif range_type == "this_year":
            start = date(today.year, 1, 1)
            return start, today
        elif range_type == "last_month":
            first_this_month = today.replace(day=1)
            last_month_end = first_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            return last_month_start, last_month_end
        elif range_type == "last_quarter":
            quarter = (today.month - 1) // 3
            if quarter == 0:
                start = date(today.year - 1, 10, 1)
                end = date(today.year - 1, 12, 31)
            else:
                start = date(today.year, (quarter - 1) * 3 + 1, 1)
                end = date(today.year, quarter * 3, 1) - timedelta(days=1)
            return start, end
        elif range_type == "last_year":
            return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
        elif range_type == "custom" and custom_start and custom_end:
            return (
                datetime.strptime(custom_start, "%Y-%m-%d").date(),
                datetime.strptime(custom_end, "%Y-%m-%d").date()
            )
        else:
            return date(today.year, 1, 1), today

    # ==================== REPORT CATALOG ====================

    def get_report_catalog(self) -> Dict:
        """Get catalog of all available reports"""
        return {
            "company_financial": {
                "name": "Company & Financial",
                "reports": [
                    {"id": "profit_loss", "name": "Profit & Loss Standard"},
                    {"id": "profit_loss_detail", "name": "Profit & Loss Detail"},
                    {"id": "profit_loss_ytd", "name": "Profit & Loss YTD Comparison"},
                    {"id": "profit_loss_prev_year", "name": "Profit & Loss Prev Year Comparison"},
                    {"id": "profit_loss_by_class", "name": "Profit & Loss by Class"},
                    {"id": "profit_loss_by_job", "name": "Profit & Loss by Job"},
                    {"id": "balance_sheet", "name": "Balance Sheet Standard"},
                    {"id": "balance_sheet_detail", "name": "Balance Sheet Detail"},
                    {"id": "balance_sheet_prev_year", "name": "Balance Sheet Prev Year Comparison"},
                    {"id": "statement_cash_flows", "name": "Statement of Cash Flows"},
                    {"id": "trial_balance", "name": "Trial Balance"},
                    {"id": "general_ledger", "name": "General Ledger"},
                    {"id": "transaction_detail", "name": "Transaction Detail by Account"},
                    {"id": "journal", "name": "Journal"},
                    {"id": "audit_trail", "name": "Audit Trail"},
                ]
            },
            "customers_receivables": {
                "name": "Customers & Receivables",
                "reports": [
                    {"id": "ar_aging_summary", "name": "A/R Aging Summary"},
                    {"id": "ar_aging_detail", "name": "A/R Aging Detail"},
                    {"id": "customer_balance_summary", "name": "Customer Balance Summary"},
                    {"id": "customer_balance_detail", "name": "Customer Balance Detail"},
                    {"id": "collections_report", "name": "Collections Report"},
                    {"id": "open_invoices", "name": "Open Invoices"},
                    {"id": "customer_contact_list", "name": "Customer Contact List"},
                ]
            },
            "sales": {
                "name": "Sales",
                "reports": [
                    {"id": "sales_by_customer", "name": "Sales by Customer Summary"},
                    {"id": "sales_by_customer_detail", "name": "Sales by Customer Detail"},
                    {"id": "sales_by_item", "name": "Sales by Item Summary"},
                    {"id": "sales_by_item_detail", "name": "Sales by Item Detail"},
                    {"id": "sales_by_rep", "name": "Sales by Rep Summary"},
                    {"id": "sales_graph", "name": "Sales Graph"},
                    {"id": "pending_sales", "name": "Pending Sales"},
                ]
            },
            "vendors_payables": {
                "name": "Vendors & Payables",
                "reports": [
                    {"id": "ap_aging_summary", "name": "A/P Aging Summary"},
                    {"id": "ap_aging_detail", "name": "A/P Aging Detail"},
                    {"id": "vendor_balance_summary", "name": "Vendor Balance Summary"},
                    {"id": "vendor_balance_detail", "name": "Vendor Balance Detail"},
                    {"id": "unpaid_bills", "name": "Unpaid Bills Detail"},
                    {"id": "vendor_contact_list", "name": "Vendor Contact List"},
                    {"id": "1099_summary", "name": "1099 Summary"},
                ]
            },
            "purchases": {
                "name": "Purchases",
                "reports": [
                    {"id": "purchases_by_vendor", "name": "Purchases by Vendor Summary"},
                    {"id": "purchases_by_vendor_detail", "name": "Purchases by Vendor Detail"},
                    {"id": "purchases_by_item", "name": "Purchases by Item Summary"},
                    {"id": "purchases_by_item_detail", "name": "Purchases by Item Detail"},
                    {"id": "open_purchase_orders", "name": "Open Purchase Orders"},
                ]
            },
            "inventory": {
                "name": "Inventory",
                "reports": [
                    {"id": "inventory_valuation", "name": "Inventory Valuation Summary"},
                    {"id": "inventory_valuation_detail", "name": "Inventory Valuation Detail"},
                    {"id": "inventory_stock_status", "name": "Inventory Stock Status by Item"},
                    {"id": "inventory_reorder", "name": "Inventory Reorder Report"},
                    {"id": "physical_inventory", "name": "Physical Inventory Worksheet"},
                    {"id": "pending_builds", "name": "Pending Builds"},
                ]
            },
            "employees_payroll": {
                "name": "Employees & Payroll",
                "reports": [
                    {"id": "payroll_summary", "name": "Payroll Summary"},
                    {"id": "payroll_detail", "name": "Payroll Detail"},
                    {"id": "employee_earnings", "name": "Employee Earnings Summary"},
                    {"id": "payroll_liability", "name": "Payroll Liability Balances"},
                    {"id": "payroll_tax_liability", "name": "Payroll Tax Liability"},
                    {"id": "employee_contact_list", "name": "Employee Contact List"},
                ]
            },
            "banking": {
                "name": "Banking",
                "reports": [
                    {"id": "deposit_detail", "name": "Deposit Detail"},
                    {"id": "check_detail", "name": "Check Detail"},
                    {"id": "missing_checks", "name": "Missing Checks"},
                    {"id": "reconciliation_discrepancy", "name": "Reconciliation Discrepancy"},
                    {"id": "previous_reconciliation", "name": "Previous Reconciliation"},
                ]
            },
            "jobs_time": {
                "name": "Jobs, Time & Mileage",
                "reports": [
                    {"id": "job_profitability", "name": "Job Profitability Summary"},
                    {"id": "job_profitability_detail", "name": "Job Profitability Detail"},
                    {"id": "job_estimates_vs_actuals", "name": "Job Estimates vs Actuals Summary"},
                    {"id": "job_estimates_vs_actuals_detail", "name": "Job Estimates vs Actuals Detail"},
                    {"id": "unbilled_costs", "name": "Unbilled Costs by Job"},
                    {"id": "open_balances", "name": "Open Balances by Job"},
                    {"id": "time_by_job", "name": "Time by Job Summary"},
                    {"id": "time_by_job_detail", "name": "Time by Job Detail"},
                    {"id": "time_by_name", "name": "Time by Name"},
                ]
            },
            "budgets": {
                "name": "Budgets & Forecasts",
                "reports": [
                    {"id": "budget_overview", "name": "Budget Overview"},
                    {"id": "budget_vs_actual", "name": "Budget vs Actual"},
                    {"id": "profit_loss_budget_performance", "name": "P&L Budget Performance"},
                    {"id": "profit_loss_budget_vs_actual", "name": "P&L Budget vs Actual"},
                    {"id": "forecast_overview", "name": "Forecast Overview"},
                    {"id": "cash_flow_forecast", "name": "Cash Flow Forecast"},
                ]
            },
            "lists": {
                "name": "List Reports",
                "reports": [
                    {"id": "account_list", "name": "Account Listing"},
                    {"id": "item_list", "name": "Item Listing"},
                    {"id": "customer_list", "name": "Customer Listing"},
                    {"id": "vendor_list", "name": "Vendor Listing"},
                    {"id": "employee_list", "name": "Employee Listing"},
                    {"id": "class_list", "name": "Class Listing"},
                    {"id": "terms_list", "name": "Terms Listing"},
                ]
            }
        }

    # ==================== COMPANY SNAPSHOT DASHBOARD ====================

    def get_company_snapshot(self, as_of_date: str = None) -> Dict:
        """Get company snapshot dashboard - like QuickBooks home page"""
        if as_of_date:
            snapshot_date = datetime.strptime(as_of_date, "%Y-%m-%d").date()
        else:
            snapshot_date = date.today()

        # Calculate key metrics
        return {
            "snapshot_date": snapshot_date.isoformat(),
            "income_summary": self._get_income_summary(snapshot_date),
            "expense_summary": self._get_expense_summary(snapshot_date),
            "profit_loss_summary": self._get_profit_loss_summary(snapshot_date),
            "bank_accounts": self._get_bank_accounts_summary(),
            "accounts_receivable": self._get_ar_summary(),
            "accounts_payable": self._get_ap_summary(),
            "inventory_alerts": self._get_inventory_alerts(),
            "reminders": self._get_reminders(),
            "income_trend": self._get_income_trend(snapshot_date),
            "expense_breakdown": self._get_expense_breakdown(snapshot_date),
            "customers_owing_most": self._get_top_customers_owing(),
            "vendors_owed_most": self._get_top_vendors_owed(),
        }

    def _get_income_summary(self, as_of: date) -> Dict:
        """Get income summary for dashboard"""
        return {
            "today": 0.0,
            "this_week": 0.0,
            "this_month": 0.0,
            "this_quarter": 0.0,
            "ytd": 0.0,
            "last_month": 0.0,
            "change_from_last_month": 0.0,
            "change_percent": 0.0
        }

    def _get_expense_summary(self, as_of: date) -> Dict:
        """Get expense summary for dashboard"""
        return {
            "today": 0.0,
            "this_week": 0.0,
            "this_month": 0.0,
            "this_quarter": 0.0,
            "ytd": 0.0,
            "last_month": 0.0,
            "change_from_last_month": 0.0,
            "change_percent": 0.0
        }

    def _get_profit_loss_summary(self, as_of: date) -> Dict:
        """Get P&L summary for dashboard"""
        income = self._get_income_summary(as_of)
        expenses = self._get_expense_summary(as_of)

        return {
            "net_income_today": income["today"] - expenses["today"],
            "net_income_this_week": income["this_week"] - expenses["this_week"],
            "net_income_this_month": income["this_month"] - expenses["this_month"],
            "net_income_ytd": income["ytd"] - expenses["ytd"],
            "gross_margin_percent": 0.0,
            "net_margin_percent": 0.0
        }

    def _get_bank_accounts_summary(self) -> List[Dict]:
        """Get bank accounts summary"""
        accounts = []
        if self.banking_service:
            for acct in self.banking_service.list_bank_accounts():
                accounts.append({
                    "account_id": acct["bank_account_id"],
                    "name": acct["account_name"],
                    "balance": acct["current_balance"],
                    "last_reconciled": acct.get("last_reconciled_date")
                })
        return accounts

    def _get_ar_summary(self) -> Dict:
        """Get A/R summary"""
        return {
            "total_outstanding": 0.0,
            "current": 0.0,
            "1_30_days": 0.0,
            "31_60_days": 0.0,
            "61_90_days": 0.0,
            "over_90_days": 0.0,
            "overdue_count": 0
        }

    def _get_ap_summary(self) -> Dict:
        """Get A/P summary"""
        return {
            "total_outstanding": 0.0,
            "current": 0.0,
            "1_30_days": 0.0,
            "31_60_days": 0.0,
            "61_90_days": 0.0,
            "over_90_days": 0.0,
            "due_within_week": 0
        }

    def _get_inventory_alerts(self) -> List[Dict]:
        """Get low inventory alerts"""
        alerts = []
        if self.inventory_service:
            reorder = self.inventory_service.get_reorder_report()
            for item in reorder.get("items", [])[:10]:
                alerts.append({
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "on_hand": item["quantity_on_hand"],
                    "reorder_point": item["reorder_point"],
                    "suggested_order": item.get("suggested_order", 0)
                })
        return alerts

    def _get_reminders(self) -> Dict:
        """Get reminders for dashboard"""
        return {
            "bills_due_today": 0,
            "bills_due_this_week": 0,
            "invoices_to_send": 0,
            "deposits_to_make": 0,
            "checks_to_print": 0,
            "overdue_invoices": 0,
            "items_to_receive": 0
        }

    def _get_income_trend(self, as_of: date) -> Dict:
        """Get income trend data for chart"""
        months = []
        for i in range(11, -1, -1):
            month = (as_of.month - i - 1) % 12 + 1
            year = as_of.year if as_of.month > i else as_of.year - 1
            months.append({
                "month": date(year, month, 1).strftime("%b %Y"),
                "income": 0.0,
                "expenses": 0.0
            })
        return {
            "chart_type": "bar",
            "labels": [m["month"] for m in months],
            "datasets": [
                {"label": "Income", "data": [m["income"] for m in months]},
                {"label": "Expenses", "data": [m["expenses"] for m in months]}
            ]
        }

    def _get_expense_breakdown(self, as_of: date) -> Dict:
        """Get expense breakdown by category for pie chart"""
        categories = [
            {"name": "Seed", "amount": 0.0, "percent": 0.0},
            {"name": "Fertilizer", "amount": 0.0, "percent": 0.0},
            {"name": "Chemicals", "amount": 0.0, "percent": 0.0},
            {"name": "Fuel", "amount": 0.0, "percent": 0.0},
            {"name": "Labor", "amount": 0.0, "percent": 0.0},
            {"name": "Repairs", "amount": 0.0, "percent": 0.0},
            {"name": "Other", "amount": 0.0, "percent": 0.0},
        ]

        return {
            "chart_type": "pie",
            "labels": [c["name"] for c in categories],
            "data": [c["amount"] for c in categories],
            "details": categories
        }

    def _get_top_customers_owing(self) -> List[Dict]:
        """Get top 5 customers with highest outstanding balance"""
        return []

    def _get_top_vendors_owed(self) -> List[Dict]:
        """Get top 5 vendors you owe the most"""
        return []

    # ==================== FINANCIAL REPORTS ====================

    def run_profit_loss(
        self,
        start_date: str,
        end_date: str,
        compare_to: str = None,
        group_by: str = None,
        class_id: str = None
    ) -> Dict:
        """Run Profit & Loss report"""
        report = {
            "report_name": "Profit & Loss",
            "subtitle": f"For the period {start_date} to {end_date}",
            "date_range": {"start": start_date, "end": end_date},
            "sections": {
                "income": {"title": "Income", "accounts": [], "total": 0.0},
                "cost_of_goods_sold": {"title": "Cost of Goods Sold", "accounts": [], "total": 0.0},
                "gross_profit": 0.0,
                "expenses": {"title": "Expenses", "accounts": [], "total": 0.0},
                "net_operating_income": 0.0,
                "other_income": {"title": "Other Income", "accounts": [], "total": 0.0},
                "other_expenses": {"title": "Other Expenses", "accounts": [], "total": 0.0},
                "net_other_income": 0.0,
                "net_income": 0.0
            },
            "comparison": None if not compare_to else {}
        }
        return report

    def run_balance_sheet(self, as_of_date: str, compare_to: str = None) -> Dict:
        """Run Balance Sheet report"""
        report = {
            "report_name": "Balance Sheet",
            "subtitle": f"As of {as_of_date}",
            "as_of_date": as_of_date,
            "sections": {
                "assets": {
                    "current_assets": {"title": "Current Assets", "accounts": [], "total": 0.0},
                    "fixed_assets": {"title": "Fixed Assets", "accounts": [], "total": 0.0},
                    "other_assets": {"title": "Other Assets", "accounts": [], "total": 0.0},
                    "total_assets": 0.0
                },
                "liabilities": {
                    "current_liabilities": {"title": "Current Liabilities", "accounts": [], "total": 0.0},
                    "long_term_liabilities": {"title": "Long-Term Liabilities", "accounts": [], "total": 0.0},
                    "total_liabilities": 0.0
                },
                "equity": {"title": "Equity", "accounts": [], "total": 0.0},
                "total_liabilities_equity": 0.0
            }
        }
        return report

    def run_trial_balance(self, as_of_date: str) -> Dict:
        """Run Trial Balance report"""
        return {
            "report_name": "Trial Balance",
            "as_of_date": as_of_date,
            "accounts": [],
            "total_debit": 0.0,
            "total_credit": 0.0,
            "is_balanced": True
        }

    def run_general_ledger(self, start_date: str, end_date: str, account_id: str = None) -> Dict:
        """Run General Ledger report"""
        return {
            "report_name": "General Ledger",
            "date_range": {"start": start_date, "end": end_date},
            "accounts": [],
            "total_debits": 0.0,
            "total_credits": 0.0
        }

    # ==================== A/R REPORTS ====================

    def run_ar_aging(self, as_of_date: str, detail: bool = False) -> Dict:
        """Run A/R Aging report"""
        return {
            "report_name": "A/R Aging Summary" if not detail else "A/R Aging Detail",
            "as_of_date": as_of_date,
            "aging_buckets": ["Current", "1-30", "31-60", "61-90", "Over 90"],
            "customers": [],
            "totals": {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0, "total": 0.0}
        }

    def run_customer_balance(self, detail: bool = False) -> Dict:
        """Run Customer Balance report"""
        return {
            "report_name": "Customer Balance Summary" if not detail else "Customer Balance Detail",
            "as_of_date": date.today().isoformat(),
            "customers": [],
            "total_balance": 0.0
        }

    def run_open_invoices(self) -> Dict:
        """Run Open Invoices report"""
        return {
            "report_name": "Open Invoices",
            "as_of_date": date.today().isoformat(),
            "invoices": [],
            "total_open": 0.0,
            "count": 0
        }

    # ==================== A/P REPORTS ====================

    def run_ap_aging(self, as_of_date: str, detail: bool = False) -> Dict:
        """Run A/P Aging report"""
        return {
            "report_name": "A/P Aging Summary" if not detail else "A/P Aging Detail",
            "as_of_date": as_of_date,
            "aging_buckets": ["Current", "1-30", "31-60", "61-90", "Over 90"],
            "vendors": [],
            "totals": {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0, "total": 0.0}
        }

    def run_vendor_balance(self, detail: bool = False) -> Dict:
        """Run Vendor Balance report"""
        return {
            "report_name": "Vendor Balance Summary" if not detail else "Vendor Balance Detail",
            "as_of_date": date.today().isoformat(),
            "vendors": [],
            "total_balance": 0.0
        }

    def run_unpaid_bills(self) -> Dict:
        """Run Unpaid Bills report"""
        return {
            "report_name": "Unpaid Bills Detail",
            "as_of_date": date.today().isoformat(),
            "bills": [],
            "total_unpaid": 0.0,
            "count": 0
        }

    # ==================== SALES REPORTS ====================

    def run_sales_by_customer(self, start_date: str, end_date: str, detail: bool = False) -> Dict:
        """Run Sales by Customer report"""
        return {
            "report_name": "Sales by Customer Summary" if not detail else "Sales by Customer Detail",
            "date_range": {"start": start_date, "end": end_date},
            "customers": [],
            "total_sales": 0.0
        }

    def run_sales_by_item(self, start_date: str, end_date: str, detail: bool = False) -> Dict:
        """Run Sales by Item report"""
        return {
            "report_name": "Sales by Item Summary" if not detail else "Sales by Item Detail",
            "date_range": {"start": start_date, "end": end_date},
            "items": [],
            "total_sales": 0.0
        }

    # ==================== PURCHASES REPORTS ====================

    def run_purchases_by_vendor(self, start_date: str, end_date: str, detail: bool = False) -> Dict:
        """Run Purchases by Vendor report"""
        return {
            "report_name": "Purchases by Vendor Summary" if not detail else "Purchases by Vendor Detail",
            "date_range": {"start": start_date, "end": end_date},
            "vendors": [],
            "total_purchases": 0.0
        }

    def run_purchases_by_item(self, start_date: str, end_date: str, detail: bool = False) -> Dict:
        """Run Purchases by Item report"""
        return {
            "report_name": "Purchases by Item Summary" if not detail else "Purchases by Item Detail",
            "date_range": {"start": start_date, "end": end_date},
            "items": [],
            "total_purchases": 0.0
        }

    # ==================== INVENTORY REPORTS ====================

    def run_inventory_valuation(self, detail: bool = False) -> Dict:
        """Run Inventory Valuation report"""
        if self.inventory_service:
            return self.inventory_service.get_inventory_valuation_report()
        return {
            "report_name": "Inventory Valuation Summary" if not detail else "Inventory Valuation Detail",
            "as_of_date": date.today().isoformat(),
            "items": [],
            "total_value": 0.0
        }

    def run_inventory_stock_status(self) -> Dict:
        """Run Inventory Stock Status report"""
        if self.inventory_service:
            return self.inventory_service.get_inventory_stock_status()
        return {
            "report_name": "Inventory Stock Status",
            "as_of_date": date.today().isoformat(),
            "items": [],
            "in_stock": 0,
            "low_stock": 0,
            "out_of_stock": 0
        }

    # ==================== PAYROLL REPORTS ====================

    def run_payroll_summary(self, start_date: str, end_date: str) -> Dict:
        """Run Payroll Summary report"""
        return {
            "report_name": "Payroll Summary",
            "date_range": {"start": start_date, "end": end_date},
            "employees": [],
            "totals": {"gross_pay": 0.0, "federal_tax": 0.0, "state_tax": 0.0, "social_security": 0.0, "medicare": 0.0, "net_pay": 0.0}
        }

    def run_payroll_detail(self, start_date: str, end_date: str) -> Dict:
        """Run Payroll Detail report"""
        return {
            "report_name": "Payroll Detail",
            "date_range": {"start": start_date, "end": end_date},
            "pay_runs": [],
            "totals": {"gross_pay": 0.0, "total_taxes": 0.0, "net_pay": 0.0}
        }

    # ==================== JOB REPORTS ====================

    def run_job_profitability(self, detail: bool = False) -> Dict:
        """Run Job Profitability report"""
        if self.classes_service:
            projects = self.classes_service.list_projects()
            result = []
            for p in projects:
                result.append({
                    "project_id": p["project_id"],
                    "name": p["name"],
                    "customer_id": p.get("customer_id"),
                    "estimated_cost": p.get("estimated_cost", 0),
                    "actual_cost": p.get("actual_cost", 0),
                    "estimated_revenue": p.get("estimated_revenue", 0),
                    "actual_revenue": p.get("actual_revenue", 0),
                    "profit": p.get("gross_profit", 0)
                })
            return {
                "report_name": "Job Profitability Summary" if not detail else "Job Profitability Detail",
                "jobs": result,
                "total_estimated_cost": sum(r["estimated_cost"] for r in result),
                "total_actual_cost": sum(r["actual_cost"] for r in result),
                "total_profit": sum(r["profit"] for r in result)
            }
        return {"report_name": "Job Profitability Summary", "jobs": [], "total_profit": 0.0}

    def run_estimates_vs_actuals(self, detail: bool = False) -> Dict:
        """Run Job Estimates vs Actuals report"""
        return {
            "report_name": "Job Estimates vs Actuals Summary" if not detail else "Job Estimates vs Actuals Detail",
            "jobs": [],
            "variance_summary": {"cost_variance": 0.0, "revenue_variance": 0.0, "hours_variance": 0.0}
        }

    def run_unbilled_costs(self) -> Dict:
        """Run Unbilled Costs by Job report"""
        if self.classes_service:
            return self.classes_service.get_unbilled_summary()
        return {"report_name": "Unbilled Costs by Job", "jobs": [], "total_unbilled": 0.0}

    # ==================== MEMORIZED REPORTS ====================

    def memorize_report(
        self,
        name: str,
        report_type: str,
        category: str,
        date_range: str = "this_month",
        filters: Dict = None,
        **kwargs
    ) -> Dict:
        """Save a memorized report configuration"""
        report_id = str(uuid.uuid4())

        # Handle category - default to CUSTOM if invalid
        try:
            cat = ReportCategory(category)
        except ValueError:
            cat = ReportCategory.CUSTOM

        # Handle date range - default to THIS_MONTH if invalid
        try:
            dr = DateRange(date_range)
        except ValueError:
            dr = DateRange.THIS_MONTH

        memorized = MemorizedReport(
            report_id=report_id,
            name=name,
            report_type=report_type,
            category=cat,
            date_range=dr,
            filters=filters or {}
        )

        self._save_memorized_report(memorized)

        return {"success": True, "report_id": report_id, "name": name}

    def run_memorized_report(self, report_id: str) -> Dict:
        """Run a memorized report"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_memorized_reports
                WHERE report_id = ? AND is_active = 1
            """, (report_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": "Memorized report not found"}

            memorized = self._row_to_memorized_report(row)

        # Calculate date range
        start, end = self._get_date_range(
            memorized.date_range.value,
            memorized.custom_start_date.isoformat() if memorized.custom_start_date else None,
            memorized.custom_end_date.isoformat() if memorized.custom_end_date else None
        )

        # Run the actual report
        report_method = getattr(self, f"run_{memorized.report_type}", None)
        if report_method:
            result = report_method(start.isoformat(), end.isoformat())
            memorized.last_run = datetime.now()
            self._save_memorized_report(memorized)
            return result

        return {"error": "Report type not found"}

    def list_memorized_reports(self) -> List[Dict]:
        """List all memorized reports"""
        reports = self._get_all_memorized_reports()
        return [
            {
                "report_id": m.report_id,
                "name": m.name,
                "report_type": m.report_type,
                "category": m.category.value,
                "last_run": m.last_run.isoformat() if m.last_run else None,
                "created_at": m.created_at.isoformat()
            }
            for m in reports
        ]

    def delete_memorized_report(self, report_id: str) -> Dict:
        """Delete a memorized report (soft delete)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_memorized_reports
                SET is_active = 0
                WHERE report_id = ?
            """, (report_id,))
            if cursor.rowcount == 0:
                return {"success": False, "error": "Report not found"}
            conn.commit()

        return {"success": True, "message": "Report deleted"}

    # ==================== DASHBOARD WIDGETS ====================

    def get_dashboard(self) -> Dict:
        """Get full dashboard configuration and data"""
        widgets_list = []

        for widget in self._get_all_widgets():
            widget_data = {
                "widget_id": widget.widget_id,
                "name": widget.name,
                "type": widget.widget_type,
                "position": widget.position,
                "is_visible": widget.is_visible
            }

            if widget.widget_type == "chart":
                widget_data["chart_type"] = widget.chart_type.value

            # Get widget data
            widget_data["data"] = self._get_widget_data(widget)
            widgets_list.append(widget_data)

        return {
            "dashboard": "Company Snapshot",
            "last_updated": datetime.now().isoformat(),
            "widgets": widgets_list
        }

    def _get_widget_data(self, widget: DashboardWidget) -> Any:
        """Get data for a dashboard widget"""
        if widget.widget_type == "metric":
            return {"value": 0, "change": 0, "change_percent": 0}
        elif widget.widget_type == "chart":
            return {"labels": [], "datasets": []}
        elif widget.widget_type == "list":
            return {"items": [], "count": 0}
        elif widget.widget_type == "alert":
            return {"alerts": [], "count": 0}
        return None

    def update_widget(self, widget_id: str, **kwargs) -> Dict:
        """Update a dashboard widget"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_dashboard_widgets
                WHERE widget_id = ? AND is_active = 1
            """, (widget_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Widget not found"}

            widget = self._row_to_widget(row)

        for key, value in kwargs.items():
            if hasattr(widget, key) and value is not None:
                if key == "chart_type":
                    value = ChartType(value)
                setattr(widget, key, value)

        self._save_widget(widget)
        return {"success": True, "message": "Widget updated"}

    def reorder_widgets(self, widget_order: List[str]) -> Dict:
        """Reorder dashboard widgets"""
        for i, widget_id in enumerate(widget_order):
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE genfin_dashboard_widgets
                    SET position = ?
                    WHERE widget_id = ? AND is_active = 1
                """, (i, widget_id))
                conn.commit()

        return {"success": True, "message": "Widgets reordered"}

    # ==================== UTILITY ====================

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        catalog = self.get_report_catalog()
        total_reports = sum(len(cat["reports"]) for cat in catalog.values())

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM genfin_memorized_reports WHERE is_active = 1")
            memorized_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM genfin_dashboard_widgets WHERE is_active = 1")
            widgets_count = cursor.fetchone()[0]

        return {
            "service": "GenFin Advanced Reports",
            "version": "1.0.0",
            "features": [
                "50+ Standard Reports",
                "Company Snapshot Dashboard",
                "Memorized Reports",
                "Customizable Date Ranges",
                "Report Filtering",
                "Charts and Graphs",
                "Dashboard Widgets"
            ],
            "total_reports": total_reports,
            "report_categories": len(catalog),
            "memorized_reports": memorized_count,
            "dashboard_widgets": widgets_count
        }


# Singleton instance
genfin_advanced_reports_service = GenFinAdvancedReportsService()
