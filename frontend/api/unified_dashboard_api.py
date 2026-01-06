"""
Unified Dashboard API Client

Handles API calls for the Advanced Reporting Dashboard.
AgTools v6.8.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES - KPI DATA
# ============================================================================

@dataclass
class KPIChartData:
    """Chart data for a KPI."""
    labels: List[str]
    values: List[float]
    colors: List[str] = field(default_factory=list)
    datasets: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "KPIChartData":
        return cls(
            labels=data.get("labels", []),
            values=data.get("values", []),
            colors=data.get("colors", []),
            datasets=data.get("datasets", [])
        )


@dataclass
class KPIDetailItem:
    """Detail item for expanded card view."""
    label: str
    value: str

    @classmethod
    def from_dict(cls, data: dict) -> "KPIDetailItem":
        return cls(
            label=data.get("label", ""),
            value=data.get("value", "")
        )


@dataclass
class KPI:
    """KPI data structure."""
    kpi_id: str
    title: str
    value: float
    formatted_value: str
    subtitle: str
    trend: str  # "up", "down", "neutral"
    change_percent: float
    chart_type: str  # "line", "bar", "pie", "donut", "stacked_bar"
    chart_data: KPIChartData
    drill_down_report: str
    drill_down_filters: Dict[str, Any]
    detail_data: List[KPIDetailItem]

    @classmethod
    def from_dict(cls, data: dict) -> "KPI":
        return cls(
            kpi_id=data.get("kpi_id", ""),
            title=data.get("title", ""),
            value=float(data.get("value", 0)),
            formatted_value=data.get("formatted_value", "$0.00"),
            subtitle=data.get("subtitle", ""),
            trend=data.get("trend", "neutral"),
            change_percent=float(data.get("change_percent", 0)),
            chart_type=data.get("chart_type", "bar"),
            chart_data=KPIChartData.from_dict(data.get("chart_data", {})),
            drill_down_report=data.get("drill_down_report", ""),
            drill_down_filters=data.get("drill_down_filters", {}),
            detail_data=[KPIDetailItem.from_dict(d) for d in data.get("detail_data", [])]
        )

    @property
    def is_positive(self) -> bool:
        """Check if the KPI trend is positive."""
        return self.trend == "up"

    @property
    def trend_icon(self) -> str:
        """Get the trend icon."""
        if self.trend == "up":
            return "\u25B2"  # Up triangle
        elif self.trend == "down":
            return "\u25BC"  # Down triangle
        return "\u25CF"  # Dot

    @property
    def trend_color(self) -> str:
        """Get the trend color."""
        if self.trend == "up":
            return "#388E3C"  # Green
        elif self.trend == "down":
            return "#D32F2F"  # Red
        return "#757575"  # Gray


# ============================================================================
# DATA CLASSES - DASHBOARD ALERT
# ============================================================================

@dataclass
class DashboardAlert:
    """Alert item for the dashboard."""
    alert_type: str
    severity: str  # "info", "warning", "critical"
    message: str
    kpi: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "DashboardAlert":
        return cls(
            alert_type=data.get("type", ""),
            severity=data.get("severity", "info"),
            message=data.get("message", ""),
            kpi=data.get("kpi")
        )

    @property
    def severity_color(self) -> str:
        """Get the severity color."""
        colors = {
            "info": "#1976D2",
            "warning": "#F57C00",
            "critical": "#D32F2F"
        }
        return colors.get(self.severity, "#757575")

    @property
    def severity_icon(self) -> str:
        """Get the severity icon."""
        icons = {
            "info": "\u2139",  # Info
            "warning": "\u26A0",  # Warning
            "critical": "\u2718"  # X
        }
        return icons.get(self.severity, "\u2022")


# ============================================================================
# DATA CLASSES - FULL DASHBOARD
# ============================================================================

@dataclass
class UnifiedDashboard:
    """Complete dashboard data."""
    snapshot_date: str
    date_range: Dict[str, str]
    crop_year: int
    financial_kpis: Dict[str, KPI]
    farm_kpis: Dict[str, KPI]
    charts: Dict[str, Any]
    alerts: List[DashboardAlert]
    last_updated: str

    @classmethod
    def from_dict(cls, data: dict) -> "UnifiedDashboard":
        # Parse financial KPIs
        financial_kpis = {}
        for key, kpi_data in data.get("financial_kpis", {}).items():
            financial_kpis[key] = KPI.from_dict(kpi_data)

        # Parse farm KPIs
        farm_kpis = {}
        for key, kpi_data in data.get("farm_kpis", {}).items():
            farm_kpis[key] = KPI.from_dict(kpi_data)

        return cls(
            snapshot_date=data.get("snapshot_date", ""),
            date_range=data.get("date_range", {}),
            crop_year=data.get("crop_year", 0),
            financial_kpis=financial_kpis,
            farm_kpis=farm_kpis,
            charts=data.get("charts", {}),
            alerts=[DashboardAlert.from_dict(a) for a in data.get("alerts", [])],
            last_updated=data.get("last_updated", "")
        )

    @property
    def all_kpis(self) -> Dict[str, KPI]:
        """Get all KPIs combined."""
        return {**self.financial_kpis, **self.farm_kpis}

    @property
    def has_alerts(self) -> bool:
        """Check if there are any alerts."""
        return len(self.alerts) > 0

    @property
    def critical_alerts(self) -> List[DashboardAlert]:
        """Get critical alerts only."""
        return [a for a in self.alerts if a.severity == "critical"]

    @property
    def warning_alerts(self) -> List[DashboardAlert]:
        """Get warning alerts only."""
        return [a for a in self.alerts if a.severity == "warning"]


# ============================================================================
# DATA CLASSES - TRANSACTIONS
# ============================================================================

@dataclass
class FilteredTransaction:
    """Transaction item from drill-down filter."""
    id: int
    date: str
    vendor: Optional[str]
    category: Optional[str]
    amount: float
    description: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "FilteredTransaction":
        return cls(
            id=data.get("id", 0),
            date=data.get("date", ""),
            vendor=data.get("vendor"),
            category=data.get("category"),
            amount=float(data.get("amount", 0)),
            description=data.get("description")
        )

    @property
    def amount_display(self) -> str:
        """Format amount for display."""
        return f"${self.amount:,.2f}"


@dataclass
class TransactionList:
    """List of filtered transactions."""
    kpi_type: str
    filter_value: Optional[str]
    count: int
    transactions: List[FilteredTransaction]

    @classmethod
    def from_dict(cls, data: dict) -> "TransactionList":
        return cls(
            kpi_type=data.get("kpi_type", ""),
            filter_value=data.get("filter_value"),
            count=data.get("count", 0),
            transactions=[FilteredTransaction.from_dict(t) for t in data.get("transactions", [])]
        )


# ============================================================================
# DATA CLASSES - KPI DETAIL
# ============================================================================

@dataclass
class KPIDetail:
    """Detailed KPI data for expanded view."""
    kpi_id: str
    title: str
    summary: Dict[str, Any]
    data: Dict[str, Any]
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "KPIDetail":
        return cls(
            kpi_id=data.get("kpi_id", ""),
            title=data.get("title", ""),
            summary=data.get("summary", {}),
            data=data,
            error=data.get("error")
        )


# ============================================================================
# UNIFIED DASHBOARD API CLIENT
# ============================================================================

class UnifiedDashboardAPI:
    """API client for the Unified Dashboard."""

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def get_dashboard(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        crop_year: Optional[int] = None
    ) -> Tuple[Optional[UnifiedDashboard], Optional[str]]:
        """
        Get the complete unified dashboard.

        Args:
            date_from: Start date (YYYY-MM-DD) or None for YTD
            date_to: End date (YYYY-MM-DD) or None for today
            crop_year: Crop year for farm data (defaults to current year)

        Returns:
            Tuple of (UnifiedDashboard, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if crop_year:
            params["crop_year"] = crop_year

        response = self._client.get("/unified-dashboard", params=params if params else None)

        if response.error:
            return None, response.error

        return UnifiedDashboard.from_dict(response.data), None

    def get_transactions(
        self,
        kpi_type: str,
        filter_value: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50
    ) -> Tuple[Optional[TransactionList], Optional[str]]:
        """
        Get filtered transactions for KPI drill-down.

        Args:
            kpi_type: KPI type (ar_aging, ap_aging, cost_per_acre, input_costs)
            filter_value: Filter value (e.g., "30_day", "fertilizer")
            date_from: Start date
            date_to: End date
            limit: Max records to return

        Returns:
            Tuple of (TransactionList, error_message or None)
        """
        params = {"kpi_type": kpi_type, "limit": limit}
        if filter_value:
            params["filter_value"] = filter_value
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._client.get("/unified-dashboard/transactions", params=params)

        if response.error:
            return None, response.error

        return TransactionList.from_dict(response.data), None

    def get_kpi_detail(self, kpi_id: str) -> Tuple[Optional[KPIDetail], Optional[str]]:
        """
        Get detailed data for KPI card expansion.

        Args:
            kpi_id: KPI identifier

        Returns:
            Tuple of (KPIDetail, error_message or None)
        """
        response = self._client.get(f"/unified-dashboard/kpi/{kpi_id}/detail")

        if response.error:
            return None, response.error

        return KPIDetail.from_dict(response.data), None

    def get_service_summary(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Get service summary/info.

        Returns:
            Tuple of (summary dict, error_message or None)
        """
        response = self._client.get("/unified-dashboard/summary")

        if response.error:
            return None, response.error

        return response.data, None


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_unified_dashboard_api: Optional[UnifiedDashboardAPI] = None


def get_unified_dashboard_api() -> UnifiedDashboardAPI:
    """Get or create the unified dashboard API singleton."""
    global _unified_dashboard_api

    if _unified_dashboard_api is None:
        _unified_dashboard_api = UnifiedDashboardAPI()

    return _unified_dashboard_api
