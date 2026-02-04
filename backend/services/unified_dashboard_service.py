"""
Unified Dashboard Service for Advanced Reporting Dashboard
Aggregates farm operations and financial data into a single dashboard view.

AgTools v6.8.0
"""

from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from .reporting_service import get_reporting_service
from .genfin_advanced_reports_service import genfin_advanced_reports_service
from .cost_tracking_service import get_cost_tracking_service
from .profitability_service import get_profitability_service


class KPIType(str, Enum):
    """KPI types for drill-down"""
    # Financial
    CASH_FLOW = "cash_flow"
    PROFIT_MARGIN = "profit_margin"
    AR_AGING = "ar_aging"
    AP_AGING = "ap_aging"
    # Farm Operations
    COST_PER_ACRE = "cost_per_acre"
    YIELD_TRENDS = "yield_trends"
    EQUIPMENT_ROI = "equipment_roi"
    INPUT_COSTS = "input_costs"


class TrendDirection(str, Enum):
    """Trend direction for KPI cards"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


@dataclass
class KPIData:
    """KPI data structure"""
    kpi_id: str
    title: str
    value: float
    formatted_value: str
    subtitle: str
    trend: TrendDirection
    change_percent: float
    chart_type: str  # line, bar, pie, donut, stacked_bar
    chart_data: Dict[str, Any]
    drill_down_report: str  # Report type to open
    drill_down_filters: Dict[str, Any]  # Filters for transaction list
    detail_data: List[Dict[str, Any]]  # Data for expanded view


class UnifiedDashboardService:
    """
    Unified Dashboard Service

    Combines data from:
    - Farm Operations (reporting_service)
    - GenFin Accounting (genfin_advanced_reports_service)
    - Cost Tracking (cost_tracking_service)
    - Profitability Analysis (profitability_service)
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "agtools.db"):
        if self._initialized:
            return

        self.db_path = db_path
        self._reporting_service = None
        self._cost_service = None
        self._profitability_service = None
        self._initialized = True

    @property
    def reporting_service(self):
        if self._reporting_service is None:
            self._reporting_service = get_reporting_service(self.db_path)
        return self._reporting_service

    @property
    def cost_service(self):
        if self._cost_service is None:
            self._cost_service = get_cost_tracking_service(self.db_path)
        return self._cost_service

    @property
    def profitability_service(self):
        if self._profitability_service is None:
            self._profitability_service = get_profitability_service(self.db_path)
        return self._profitability_service

    @property
    def genfin_service(self):
        return genfin_advanced_reports_service

    # ========================================================================
    # MAIN DASHBOARD ENDPOINT
    # ========================================================================

    def get_dashboard(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        crop_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get unified dashboard combining farm + financial KPIs.

        Args:
            date_from: Start date (YYYY-MM-DD) or None for YTD
            date_to: End date (YYYY-MM-DD) or None for today
            crop_year: Crop year for farm data (defaults to current year)

        Returns:
            Complete dashboard data with KPIs, charts, and alerts
        """
        today = date.today()

        # Parse dates
        if date_to:
            end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
        else:
            end_date = today

        if date_from:
            start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        else:
            start_date = date(today.year, 1, 1)  # YTD

        if crop_year is None:
            crop_year = today.year

        # Get financial KPIs
        financial_kpis = self._get_financial_kpis(start_date, end_date)

        # Get farm operations KPIs
        farm_kpis = self._get_farm_kpis(start_date, end_date, crop_year)

        # Get revenue trend chart data
        revenue_trend = self._get_revenue_trend(start_date, end_date)

        # Get alerts
        alerts = self._get_alerts()

        return {
            "snapshot_date": today.isoformat(),
            "date_range": {
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            },
            "crop_year": crop_year,
            "financial_kpis": financial_kpis,
            "farm_kpis": farm_kpis,
            "charts": {
                "revenue_trend": revenue_trend
            },
            "alerts": alerts,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    # ========================================================================
    # FINANCIAL KPIs
    # ========================================================================

    def _get_financial_kpis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get financial KPIs from GenFin service."""

        # Get company snapshot from GenFin
        snapshot = self.genfin_service.get_company_snapshot(end_date.isoformat())

        # Cash Flow KPI
        income = snapshot.get("income_summary", {})
        expense = snapshot.get("expense_summary", {})
        cash_flow_value = income.get("ytd", 0) - expense.get("ytd", 0)
        cash_flow_trend = self._calculate_trend(
            income.get("this_month", 0) - expense.get("this_month", 0),
            income.get("last_month", 0) - expense.get("last_month", 0)
        )

        cash_flow = {
            "kpi_id": KPIType.CASH_FLOW.value,
            "title": "Cash Flow",
            "value": cash_flow_value,
            "formatted_value": self._format_currency(cash_flow_value),
            "subtitle": "Year to Date",
            "trend": cash_flow_trend["direction"],
            "change_percent": cash_flow_trend["percent"],
            "chart_type": "line",
            "chart_data": self._get_cash_flow_chart_data(start_date, end_date),
            "drill_down_report": "statement_cash_flows",
            "drill_down_filters": {"date_from": start_date.isoformat(), "date_to": end_date.isoformat()},
            "detail_data": [
                {"label": "Income YTD", "value": self._format_currency(income.get("ytd", 0))},
                {"label": "Expenses YTD", "value": self._format_currency(expense.get("ytd", 0))},
                {"label": "This Month", "value": self._format_currency(income.get("this_month", 0) - expense.get("this_month", 0))},
                {"label": "Last Month", "value": self._format_currency(income.get("last_month", 0) - expense.get("last_month", 0))},
            ]
        }

        # Profit Margin KPI
        pl_summary = snapshot.get("profit_loss_summary", {})
        net_income = pl_summary.get("net_income_ytd", 0)
        total_income = income.get("ytd", 0)
        margin_pct = (net_income / total_income * 100) if total_income > 0 else 0

        profit_margin = {
            "kpi_id": KPIType.PROFIT_MARGIN.value,
            "title": "Profit Margin",
            "value": margin_pct,
            "formatted_value": f"{margin_pct:.1f}%",
            "subtitle": f"Net: {self._format_currency(net_income)}",
            "trend": TrendDirection.UP.value if margin_pct > 0 else TrendDirection.DOWN.value,
            "change_percent": margin_pct,
            "chart_type": "donut",
            "chart_data": {
                "labels": ["Net Income", "Expenses"],
                "values": [max(net_income, 0), expense.get("ytd", 0)],
                "colors": ["#388E3C", "#D32F2F"]
            },
            "drill_down_report": "profit_loss",
            "drill_down_filters": {"date_from": start_date.isoformat(), "date_to": end_date.isoformat()},
            "detail_data": [
                {"label": "Gross Margin", "value": f"{pl_summary.get('gross_margin_percent', 0):.1f}%"},
                {"label": "Net Margin", "value": f"{pl_summary.get('net_margin_percent', 0):.1f}%"},
                {"label": "Total Revenue", "value": self._format_currency(total_income)},
                {"label": "Total Expenses", "value": self._format_currency(expense.get("ytd", 0))},
            ]
        }

        # AR Aging KPI
        ar_summary = snapshot.get("accounts_receivable", {})
        ar_total = ar_summary.get("total_outstanding", 0)
        ar_overdue = ar_summary.get("over_90_days", 0) + ar_summary.get("61_90_days", 0)

        ar_aging = {
            "kpi_id": KPIType.AR_AGING.value,
            "title": "Accounts Receivable",
            "value": ar_total,
            "formatted_value": self._format_currency(ar_total),
            "subtitle": f"{ar_summary.get('overdue_count', 0)} overdue",
            "trend": TrendDirection.DOWN.value if ar_overdue > 0 else TrendDirection.NEUTRAL.value,
            "change_percent": (ar_overdue / ar_total * 100) if ar_total > 0 else 0,
            "chart_type": "stacked_bar",
            "chart_data": {
                "labels": ["Current", "1-30", "31-60", "61-90", "90+"],
                "values": [
                    ar_summary.get("current", 0),
                    ar_summary.get("1_30_days", 0),
                    ar_summary.get("31_60_days", 0),
                    ar_summary.get("61_90_days", 0),
                    ar_summary.get("over_90_days", 0),
                ],
                "colors": ["#4CAF50", "#8BC34A", "#FFC107", "#FF9800", "#F44336"]
            },
            "drill_down_report": "ar_aging_detail",
            "drill_down_filters": {"as_of_date": end_date.isoformat()},
            "detail_data": [
                {"label": "Current", "value": self._format_currency(ar_summary.get("current", 0))},
                {"label": "1-30 Days", "value": self._format_currency(ar_summary.get("1_30_days", 0))},
                {"label": "31-60 Days", "value": self._format_currency(ar_summary.get("31_60_days", 0))},
                {"label": "61-90 Days", "value": self._format_currency(ar_summary.get("61_90_days", 0))},
                {"label": "Over 90 Days", "value": self._format_currency(ar_summary.get("over_90_days", 0))},
            ]
        }

        # AP Aging KPI
        ap_summary = snapshot.get("accounts_payable", {})
        ap_total = ap_summary.get("total_outstanding", 0)
        ap_due_soon = ap_summary.get("due_within_week", 0)

        ap_aging = {
            "kpi_id": KPIType.AP_AGING.value,
            "title": "Accounts Payable",
            "value": ap_total,
            "formatted_value": self._format_currency(ap_total),
            "subtitle": f"{ap_due_soon} due this week",
            "trend": TrendDirection.NEUTRAL.value,
            "change_percent": 0,
            "chart_type": "stacked_bar",
            "chart_data": {
                "labels": ["Current", "1-30", "31-60", "61-90", "90+"],
                "values": [
                    ap_summary.get("current", 0),
                    ap_summary.get("1_30_days", 0),
                    ap_summary.get("31_60_days", 0),
                    ap_summary.get("61_90_days", 0),
                    ap_summary.get("over_90_days", 0),
                ],
                "colors": ["#4CAF50", "#8BC34A", "#FFC107", "#FF9800", "#F44336"]
            },
            "drill_down_report": "ap_aging_detail",
            "drill_down_filters": {"as_of_date": end_date.isoformat()},
            "detail_data": [
                {"label": "Current", "value": self._format_currency(ap_summary.get("current", 0))},
                {"label": "1-30 Days", "value": self._format_currency(ap_summary.get("1_30_days", 0))},
                {"label": "31-60 Days", "value": self._format_currency(ap_summary.get("31_60_days", 0))},
                {"label": "61-90 Days", "value": self._format_currency(ap_summary.get("61_90_days", 0))},
                {"label": "Over 90 Days", "value": self._format_currency(ap_summary.get("over_90_days", 0))},
            ]
        }

        return {
            "cash_flow": cash_flow,
            "profit_margin": profit_margin,
            "ar_aging": ar_aging,
            "ap_aging": ap_aging
        }

    # ========================================================================
    # FARM OPERATIONS KPIs
    # ========================================================================

    def _get_farm_kpis(self, start_date: date, end_date: date, crop_year: int) -> Dict[str, Any]:
        """Get farm operations KPIs."""

        # Get farm reports
        try:
            _financial_report = self.reporting_service.get_financial_report(start_date, end_date)
            equipment_report = self.reporting_service.get_equipment_report(start_date, end_date)
            field_report = self.reporting_service.get_field_performance_report(start_date, end_date)
        except Exception:
            # If no data, return empty KPIs
            _financial_report = None
            equipment_report = None
            field_report = None

        # Cost Per Acre KPI
        try:
            cost_report = self.cost_service.get_cost_per_acre_report(crop_year)
            avg_cost = cost_report.average_cost_per_acre
            cost_by_field = [
                {"field": f.field_name, "cost": f.cost_per_acre}
                for f in cost_report.fields[:5]
            ]
        except Exception:
            avg_cost = 0
            cost_by_field = []

        cost_per_acre = {
            "kpi_id": KPIType.COST_PER_ACRE.value,
            "title": "Cost Per Acre",
            "value": avg_cost,
            "formatted_value": self._format_currency(avg_cost),
            "subtitle": f"{crop_year} Average",
            "trend": TrendDirection.NEUTRAL.value,
            "change_percent": 0,
            "chart_type": "bar",
            "chart_data": {
                "labels": [f["field"] for f in cost_by_field],
                "values": [f["cost"] for f in cost_by_field],
                "colors": ["#2E7D32", "#388E3C", "#43A047", "#4CAF50", "#66BB6A"]
            },
            "drill_down_report": "cost_per_acre",
            "drill_down_filters": {"crop_year": crop_year},
            "detail_data": [
                {"label": f["field"], "value": self._format_currency(f["cost"])}
                for f in cost_by_field
            ]
        }

        # Yield Trends KPI
        avg_yield = field_report.avg_yield if field_report and field_report.avg_yield else 0
        best_field = field_report.best_field if field_report else "N/A"

        # Build historical yield data (placeholder - would pull from DB)
        yield_history = self._get_yield_history(crop_year)

        yield_trends = {
            "kpi_id": KPIType.YIELD_TRENDS.value,
            "title": "Yield Trends",
            "value": avg_yield,
            "formatted_value": f"{avg_yield:.1f} bu/ac" if avg_yield else "No data",
            "subtitle": f"Best: {best_field}",
            "trend": TrendDirection.UP.value if avg_yield > 0 else TrendDirection.NEUTRAL.value,
            "change_percent": 0,
            "chart_type": "line",
            "chart_data": yield_history,
            "drill_down_report": "field_performance",
            "drill_down_filters": {"date_from": start_date.isoformat(), "date_to": end_date.isoformat()},
            "detail_data": [
                {"label": f.field_name, "value": f"{f.yield_per_acre:.1f} bu/ac" if f.yield_per_acre else "N/A"}
                for f in (field_report.fields[:5] if field_report else [])
            ]
        }

        # Equipment ROI KPI
        fleet_value = equipment_report.total_fleet_value if equipment_report else 0
        total_hours = equipment_report.total_hours if equipment_report else 0
        utilization = (total_hours / (equipment_report.total_equipment * 500) * 100) if equipment_report and equipment_report.total_equipment > 0 else 0

        equipment_by_type = equipment_report.hours_by_type if equipment_report else {}

        equipment_roi = {
            "kpi_id": KPIType.EQUIPMENT_ROI.value,
            "title": "Equipment ROI",
            "value": utilization,
            "formatted_value": f"{utilization:.1f}%",
            "subtitle": f"Fleet: {self._format_currency(fleet_value)}",
            "trend": TrendDirection.UP.value if utilization > 50 else TrendDirection.DOWN.value,
            "change_percent": utilization,
            "chart_type": "pie",
            "chart_data": {
                "labels": list(equipment_by_type.keys())[:5],
                "values": list(equipment_by_type.values())[:5],
                "colors": ["#1565C0", "#1976D2", "#1E88E5", "#2196F3", "#42A5F5"]
            },
            "drill_down_report": "equipment",
            "drill_down_filters": {"date_from": start_date.isoformat(), "date_to": end_date.isoformat()},
            "detail_data": [
                {"label": "Fleet Value", "value": self._format_currency(fleet_value)},
                {"label": "Total Hours", "value": f"{total_hours:.0f}"},
                {"label": "Utilization", "value": f"{utilization:.1f}%"},
                {"label": "In Maintenance", "value": str(equipment_report.equipment_in_maintenance if equipment_report else 0)},
            ]
        }

        # Input Costs KPI
        try:
            cost_breakdown = self.cost_service.get_category_breakdown(crop_year)
            input_totals = {cb.category: cb.total_amount for cb in cost_breakdown}
            total_inputs = sum(input_totals.values())
        except Exception:
            input_totals = {}
            total_inputs = 0

        input_costs = {
            "kpi_id": KPIType.INPUT_COSTS.value,
            "title": "Input Costs",
            "value": total_inputs,
            "formatted_value": self._format_currency(total_inputs),
            "subtitle": f"{crop_year} Total",
            "trend": TrendDirection.NEUTRAL.value,
            "change_percent": 0,
            "chart_type": "pie",
            "chart_data": {
                "labels": list(input_totals.keys())[:6],
                "values": list(input_totals.values())[:6],
                "colors": ["#2E7D32", "#F57C00", "#7B1FA2", "#C62828", "#1565C0", "#757575"]
            },
            "drill_down_report": "financial",
            "drill_down_filters": {"crop_year": crop_year},
            "detail_data": [
                {"label": cat.replace("_", " ").title(), "value": self._format_currency(amt)}
                for cat, amt in list(input_totals.items())[:6]
            ]
        }

        return {
            "cost_per_acre": cost_per_acre,
            "yield_trends": yield_trends,
            "equipment_roi": equipment_roi,
            "input_costs": input_costs
        }

    # ========================================================================
    # CHART DATA HELPERS
    # ========================================================================

    def _get_cash_flow_chart_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get cash flow trend data for line chart."""
        # Generate monthly data points
        months = []
        current = start_date.replace(day=1)

        while current <= end_date:
            months.append(current.strftime("%b"))
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Placeholder values - would pull from actual transactions
        income_data = [0] * len(months)
        expense_data = [0] * len(months)

        return {
            "labels": months,
            "datasets": [
                {"label": "Income", "data": income_data, "color": "#388E3C"},
                {"label": "Expenses", "data": expense_data, "color": "#D32F2F"}
            ]
        }

    def _get_yield_history(self, current_year: int) -> Dict[str, Any]:
        """Get historical yield data."""
        years = [str(current_year - i) for i in range(4, -1, -1)]
        # Placeholder - would pull from actual harvest data
        yields = [0] * 5

        return {
            "labels": years,
            "values": yields,
            "color": "#2E7D32"
        }

    def _get_revenue_trend(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get revenue trend for full-width chart."""
        income_trend = self.genfin_service._get_income_trend(end_date)
        return income_trend

    # ========================================================================
    # DRILL-DOWN ENDPOINTS
    # ========================================================================

    def get_filtered_transactions(
        self,
        kpi_type: str,
        filter_value: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get filtered transaction list for KPI drill-down.

        Args:
            kpi_type: KPI type (ar_aging, ap_aging, etc.)
            filter_value: Filter value (e.g., "30_day", "60_day")
            date_from: Start date
            date_to: End date
            limit: Max records to return

        Returns:
            Filtered transaction list
        """
        transactions = []

        if kpi_type == KPIType.AR_AGING.value:
            # Get open invoices filtered by aging bucket
            transactions = self._get_ar_transactions(filter_value, limit)
        elif kpi_type == KPIType.AP_AGING.value:
            # Get unpaid bills filtered by aging bucket
            transactions = self._get_ap_transactions(filter_value, limit)
        elif kpi_type == KPIType.COST_PER_ACRE.value:
            # Get expense allocations
            transactions = self._get_cost_transactions(filter_value, limit)
        elif kpi_type == KPIType.INPUT_COSTS.value:
            # Get expenses by category
            transactions = self._get_input_transactions(filter_value, date_from, date_to, limit)

        return {
            "kpi_type": kpi_type,
            "filter_value": filter_value,
            "count": len(transactions),
            "transactions": transactions
        }

    def _get_ar_transactions(self, aging_bucket: Optional[str], limit: int) -> List[Dict]:
        """Get AR transactions for drill-down."""
        # Placeholder - would query actual invoices
        return []

    def _get_ap_transactions(self, aging_bucket: Optional[str], limit: int) -> List[Dict]:
        """Get AP transactions for drill-down."""
        # Placeholder - would query actual bills
        return []

    def _get_cost_transactions(self, field_id: Optional[str], limit: int) -> List[Dict]:
        """Get cost allocation transactions."""
        # Placeholder - would query expense allocations
        return []

    def _get_input_transactions(
        self,
        category: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Get input cost transactions."""
        try:
            start = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
            end = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None

            from .cost_tracking_service import ExpenseCategory
            cat = ExpenseCategory(category) if category else None

            result = self.cost_service.list_expenses(
                user_id=1,  # Would get from auth
                category=cat,
                start_date=start,
                end_date=end,
                limit=limit
            )

            return [
                {
                    "id": e.id,
                    "date": e.expense_date.isoformat(),
                    "vendor": e.vendor,
                    "category": e.category,
                    "amount": e.amount,
                    "description": e.description
                }
                for e in result.expenses
            ]
        except Exception:
            return []

    def get_kpi_detail(self, kpi_id: str) -> Dict[str, Any]:
        """
        Get detailed data for KPI card expansion.

        Args:
            kpi_id: KPI identifier

        Returns:
            Detailed breakdown data
        """
        today = date.today()
        start_of_year = date(today.year, 1, 1)

        if kpi_id == KPIType.AR_AGING.value:
            return self._get_ar_detail()
        elif kpi_id == KPIType.AP_AGING.value:
            return self._get_ap_detail()
        elif kpi_id == KPIType.COST_PER_ACRE.value:
            return self._get_cost_per_acre_detail(today.year)
        elif kpi_id == KPIType.EQUIPMENT_ROI.value:
            return self._get_equipment_detail(start_of_year, today)
        elif kpi_id == KPIType.INPUT_COSTS.value:
            return self._get_input_costs_detail(today.year)
        else:
            return {"kpi_id": kpi_id, "detail": "No detail available"}

    def _get_ar_detail(self) -> Dict[str, Any]:
        """Get detailed AR data."""
        report = self.genfin_service.run_ar_aging(date.today().isoformat(), detail=True)
        return {
            "kpi_id": KPIType.AR_AGING.value,
            "title": "Accounts Receivable Detail",
            "totals": report.get("totals", {}),
            "customers": report.get("customers", [])[:10]
        }

    def _get_ap_detail(self) -> Dict[str, Any]:
        """Get detailed AP data."""
        report = self.genfin_service.run_ap_aging(date.today().isoformat(), detail=True)
        return {
            "kpi_id": KPIType.AP_AGING.value,
            "title": "Accounts Payable Detail",
            "totals": report.get("totals", {}),
            "vendors": report.get("vendors", [])[:10]
        }

    def _get_cost_per_acre_detail(self, crop_year: int) -> Dict[str, Any]:
        """Get detailed cost per acre data."""
        try:
            report = self.cost_service.get_cost_per_acre_report(crop_year)
            return {
                "kpi_id": KPIType.COST_PER_ACRE.value,
                "title": f"Cost Per Acre Detail - {crop_year}",
                "summary": {
                    "total_fields": report.total_fields,
                    "total_acreage": report.total_acreage,
                    "total_cost": report.total_cost,
                    "average": report.average_cost_per_acre
                },
                "by_category": report.by_category_totals,
                "fields": [
                    {
                        "field": f.field_name,
                        "acreage": f.acreage,
                        "total_cost": f.total_cost,
                        "cost_per_acre": f.cost_per_acre,
                        "crop": f.crop_type
                    }
                    for f in report.fields
                ]
            }
        except Exception:
            return {"kpi_id": KPIType.COST_PER_ACRE.value, "error": "No data available"}

    def _get_equipment_detail(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get detailed equipment data."""
        try:
            report = self.reporting_service.get_equipment_report(start_date, end_date)
            return {
                "kpi_id": KPIType.EQUIPMENT_ROI.value,
                "title": "Equipment Utilization Detail",
                "summary": {
                    "total_equipment": report.total_equipment,
                    "fleet_value": report.total_fleet_value,
                    "total_hours": report.total_hours,
                    "in_maintenance": report.equipment_in_maintenance
                },
                "hours_by_type": report.hours_by_type,
                "equipment": [
                    {
                        "name": e.name,
                        "type": e.equipment_type,
                        "hours": e.total_hours,
                        "maintenance_cost": e.maintenance_cost,
                        "operating_cost": e.operating_cost
                    }
                    for e in report.equipment_usage[:10]
                ],
                "maintenance_alerts": [
                    {
                        "equipment": a.equipment_name,
                        "type": a.maintenance_type,
                        "due_date": a.next_service_date,
                        "urgency": a.urgency
                    }
                    for a in report.maintenance_alerts[:5]
                ]
            }
        except Exception:
            return {"kpi_id": KPIType.EQUIPMENT_ROI.value, "error": "No data available"}

    def _get_input_costs_detail(self, crop_year: int) -> Dict[str, Any]:
        """Get detailed input costs data."""
        try:
            breakdown = self.cost_service.get_category_breakdown(crop_year)
            crop_costs = self.cost_service.get_cost_by_crop(crop_year)

            return {
                "kpi_id": KPIType.INPUT_COSTS.value,
                "title": f"Input Costs Detail - {crop_year}",
                "by_category": [
                    {
                        "category": b.category,
                        "group": b.category_group,
                        "amount": b.total_amount,
                        "percent": b.percent_of_total,
                        "count": b.expense_count
                    }
                    for b in breakdown
                ],
                "by_crop": [
                    {
                        "crop": c.crop_type,
                        "acres": c.total_acres,
                        "total_cost": c.total_cost,
                        "cost_per_acre": c.cost_per_acre
                    }
                    for c in crop_costs
                ]
            }
        except Exception:
            return {"kpi_id": KPIType.INPUT_COSTS.value, "error": "No data available"}

    # ========================================================================
    # ALERTS
    # ========================================================================

    def _get_alerts(self) -> List[Dict[str, Any]]:
        """Get dashboard alerts."""
        alerts = []

        # Check AR overdue
        snapshot = self.genfin_service.get_company_snapshot()
        ar = snapshot.get("accounts_receivable", {})
        if ar.get("overdue_count", 0) > 0:
            alerts.append({
                "type": "ar_overdue",
                "severity": "warning",
                "message": f"{ar.get('overdue_count')} invoices past due",
                "kpi": KPIType.AR_AGING.value
            })

        # Check inventory alerts
        inv_alerts = snapshot.get("inventory_alerts", [])
        if inv_alerts:
            alerts.append({
                "type": "low_inventory",
                "severity": "info",
                "message": f"{len(inv_alerts)} items below reorder point",
                "kpi": "inventory"
            })

        # Check equipment maintenance
        try:
            equip_report = self.reporting_service.get_equipment_report()
            overdue = [a for a in equip_report.maintenance_alerts if a.urgency == "overdue"]
            if overdue:
                alerts.append({
                    "type": "maintenance_overdue",
                    "severity": "warning",
                    "message": f"{len(overdue)} equipment items need maintenance",
                    "kpi": KPIType.EQUIPMENT_ROI.value
                })
        except Exception:
            pass

        return alerts

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _format_currency(self, value: float) -> str:
        """Format value as currency."""
        if value >= 0:
            return f"${value:,.2f}"
        else:
            return f"-${abs(value):,.2f}"

    def _calculate_trend(self, current: float, previous: float) -> Dict[str, Any]:
        """Calculate trend direction and percentage."""
        if previous == 0:
            return {"direction": TrendDirection.NEUTRAL.value, "percent": 0}

        change = ((current - previous) / abs(previous)) * 100

        if change > 5:
            direction = TrendDirection.UP.value
        elif change < -5:
            direction = TrendDirection.DOWN.value
        else:
            direction = TrendDirection.NEUTRAL.value

        return {"direction": direction, "percent": round(change, 1)}

    def get_service_summary(self) -> Dict[str, Any]:
        """Get service summary."""
        return {
            "service": "Unified Dashboard Service",
            "version": "1.0.0",
            "features": [
                "Combined Farm + Financial KPIs",
                "8 Key Performance Indicators",
                "Drill-down to transaction lists",
                "Drill-down to full reports",
                "Expandable card details",
                "Real-time alerts"
            ],
            "kpis": {
                "financial": ["Cash Flow", "Profit Margin", "AR Aging", "AP Aging"],
                "farm": ["Cost Per Acre", "Yield Trends", "Equipment ROI", "Input Costs"]
            }
        }


# Singleton instance
_unified_dashboard_service: Optional[UnifiedDashboardService] = None


def get_unified_dashboard_service(db_path: str = "agtools.db") -> UnifiedDashboardService:
    """Get or create the unified dashboard service singleton."""
    global _unified_dashboard_service
    if _unified_dashboard_service is None:
        # Note: UnifiedDashboardService uses __new__ singleton pattern
        # so we call without args and set db_path after
        _unified_dashboard_service = UnifiedDashboardService()
        if not _unified_dashboard_service._initialized:
            _unified_dashboard_service.db_path = db_path
            _unified_dashboard_service._initialized = True
    return _unified_dashboard_service
