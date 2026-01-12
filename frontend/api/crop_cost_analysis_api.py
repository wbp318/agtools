"""
Crop Cost Analysis API Client

Handles crop cost analysis endpoints for the Farm Operations Manager.
AgTools v6.9.0
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES - SUMMARY
# ============================================================================

@dataclass
class CropAnalysisSummary:
    """High-level KPIs for crop cost analysis dashboard"""
    crop_year: int
    total_cost: float
    total_acres: float
    avg_cost_per_acre: float
    avg_cost_per_bushel: Optional[float]
    total_yield: float
    avg_yield_per_acre: float
    gross_revenue: float
    net_profit: float
    profit_margin_percent: float
    top_roi_crop: Optional[str]
    top_roi_value: float
    field_count: int
    cost_by_category: Dict[str, float]

    @classmethod
    def from_dict(cls, data: dict) -> "CropAnalysisSummary":
        return cls(
            crop_year=data.get("crop_year", 0),
            total_cost=float(data.get("total_cost", 0)),
            total_acres=float(data.get("total_acres", 0)),
            avg_cost_per_acre=float(data.get("avg_cost_per_acre", 0)),
            avg_cost_per_bushel=float(data["avg_cost_per_bushel"]) if data.get("avg_cost_per_bushel") else None,
            total_yield=float(data.get("total_yield", 0)),
            avg_yield_per_acre=float(data.get("avg_yield_per_acre", 0)),
            gross_revenue=float(data.get("gross_revenue", 0)),
            net_profit=float(data.get("net_profit", 0)),
            profit_margin_percent=float(data.get("profit_margin_percent", 0)),
            top_roi_crop=data.get("top_roi_crop"),
            top_roi_value=float(data.get("top_roi_value", 0)),
            field_count=data.get("field_count", 0),
            cost_by_category=data.get("cost_by_category", {})
        )

    @property
    def total_cost_display(self) -> str:
        return f"${self.total_cost:,.2f}"

    @property
    def cost_per_acre_display(self) -> str:
        return f"${self.avg_cost_per_acre:,.2f}"

    @property
    def cost_per_bushel_display(self) -> str:
        if self.avg_cost_per_bushel:
            return f"${self.avg_cost_per_bushel:,.2f}"
        return "N/A"

    @property
    def revenue_display(self) -> str:
        return f"${self.gross_revenue:,.2f}"

    @property
    def profit_display(self) -> str:
        return f"${self.net_profit:,.2f}"

    @property
    def profit_color(self) -> str:
        return "#2e7d32" if self.net_profit >= 0 else "#d32f2f"

    @property
    def roi_display(self) -> str:
        return f"{self.top_roi_value:.1f}%"


# ============================================================================
# DATA CLASSES - FIELD COMPARISON
# ============================================================================

@dataclass
class FieldCostDetail:
    """Cost breakdown for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    crop_type: Optional[str]
    acreage: float
    crop_year: int
    total_cost: float
    cost_per_acre: float
    cost_per_bushel: Optional[float]
    total_yield: float
    yield_per_acre: float
    revenue: float
    profit: float
    roi_percent: float
    cost_by_category: Dict[str, float]

    @classmethod
    def from_dict(cls, data: dict) -> "FieldCostDetail":
        return cls(
            field_id=data.get("field_id", 0),
            field_name=data.get("field_name", ""),
            farm_name=data.get("farm_name"),
            crop_type=data.get("crop_type"),
            acreage=float(data.get("acreage", 0)),
            crop_year=data.get("crop_year", 0),
            total_cost=float(data.get("total_cost", 0)),
            cost_per_acre=float(data.get("cost_per_acre", 0)),
            cost_per_bushel=float(data["cost_per_bushel"]) if data.get("cost_per_bushel") else None,
            total_yield=float(data.get("total_yield", 0)),
            yield_per_acre=float(data.get("yield_per_acre", 0)),
            revenue=float(data.get("revenue", 0)),
            profit=float(data.get("profit", 0)),
            roi_percent=float(data.get("roi_percent", 0)),
            cost_by_category=data.get("cost_by_category", {})
        )

    @property
    def profit_display(self) -> str:
        return f"${self.profit:,.2f}"

    @property
    def profit_color(self) -> str:
        return "#2e7d32" if self.profit >= 0 else "#d32f2f"

    @property
    def roi_display(self) -> str:
        return f"{self.roi_percent:.1f}%"

    @property
    def roi_color(self) -> str:
        if self.roi_percent >= 20:
            return "#2e7d32"
        elif self.roi_percent >= 0:
            return "#f57c00"
        return "#d32f2f"


@dataclass
class FieldComparisonMatrix:
    """Field vs field comparison matrix"""
    crop_year: int
    fields: List[FieldCostDetail]
    summary: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> "FieldComparisonMatrix":
        return cls(
            crop_year=data.get("crop_year", 0),
            fields=[FieldCostDetail.from_dict(f) for f in data.get("fields", [])],
            summary=data.get("summary", {})
        )


# ============================================================================
# DATA CLASSES - CROP COMPARISON
# ============================================================================

@dataclass
class CropComparisonItem:
    """Comparison data for a single crop type"""
    crop_type: str
    total_acres: float
    field_count: int
    total_cost: float
    avg_cost_per_acre: float
    avg_cost_per_bushel: Optional[float]
    total_yield: float
    avg_yield_per_acre: float
    total_revenue: float
    profit: float
    roi_percent: float

    @classmethod
    def from_dict(cls, data: dict) -> "CropComparisonItem":
        return cls(
            crop_type=data.get("crop_type", ""),
            total_acres=float(data.get("total_acres", 0)),
            field_count=data.get("field_count", 0),
            total_cost=float(data.get("total_cost", 0)),
            avg_cost_per_acre=float(data.get("avg_cost_per_acre", 0)),
            avg_cost_per_bushel=float(data["avg_cost_per_bushel"]) if data.get("avg_cost_per_bushel") else None,
            total_yield=float(data.get("total_yield", 0)),
            avg_yield_per_acre=float(data.get("avg_yield_per_acre", 0)),
            total_revenue=float(data.get("total_revenue", 0)),
            profit=float(data.get("profit", 0)),
            roi_percent=float(data.get("roi_percent", 0))
        )

    @property
    def profit_display(self) -> str:
        return f"${self.profit:,.2f}"

    @property
    def profit_color(self) -> str:
        return "#2e7d32" if self.profit >= 0 else "#d32f2f"

    @property
    def roi_display(self) -> str:
        return f"{self.roi_percent:.1f}%"


# ============================================================================
# DATA CLASSES - YEAR OVER YEAR
# ============================================================================

@dataclass
class YearOverYearData:
    """Year-over-year comparison data"""
    year: int
    total_acres: float
    total_cost: float
    avg_cost_per_acre: float
    avg_cost_per_bushel: Optional[float]
    total_yield: float
    avg_yield_per_acre: float
    revenue: float
    profit: float
    roi_percent: float

    @classmethod
    def from_dict(cls, data: dict) -> "YearOverYearData":
        return cls(
            year=data.get("year", 0),
            total_acres=float(data.get("total_acres", 0)),
            total_cost=float(data.get("total_cost", 0)),
            avg_cost_per_acre=float(data.get("avg_cost_per_acre", 0)),
            avg_cost_per_bushel=float(data["avg_cost_per_bushel"]) if data.get("avg_cost_per_bushel") else None,
            total_yield=float(data.get("total_yield", 0)),
            avg_yield_per_acre=float(data.get("avg_yield_per_acre", 0)),
            revenue=float(data.get("revenue", 0)),
            profit=float(data.get("profit", 0)),
            roi_percent=float(data.get("roi_percent", 0))
        )


# ============================================================================
# DATA CLASSES - ROI ANALYSIS
# ============================================================================

@dataclass
class ROIAnalysisItem:
    """ROI analysis for a field or crop"""
    entity_id: int
    entity_name: str
    entity_type: str
    crop_type: Optional[str]
    acreage: float
    total_investment: float
    total_return: float
    net_profit: float
    roi_percent: float
    break_even_yield: float
    break_even_price: float
    margin_of_safety_percent: float
    actual_yield: float
    market_price: float

    @classmethod
    def from_dict(cls, data: dict) -> "ROIAnalysisItem":
        return cls(
            entity_id=data.get("entity_id", 0),
            entity_name=data.get("entity_name", ""),
            entity_type=data.get("entity_type", "field"),
            crop_type=data.get("crop_type"),
            acreage=float(data.get("acreage", 0)),
            total_investment=float(data.get("total_investment", 0)),
            total_return=float(data.get("total_return", 0)),
            net_profit=float(data.get("net_profit", 0)),
            roi_percent=float(data.get("roi_percent", 0)),
            break_even_yield=float(data.get("break_even_yield", 0)),
            break_even_price=float(data.get("break_even_price", 0)),
            margin_of_safety_percent=float(data.get("margin_of_safety_percent", 0)),
            actual_yield=float(data.get("actual_yield", 0)),
            market_price=float(data.get("market_price", 0))
        )

    @property
    def roi_display(self) -> str:
        return f"{self.roi_percent:.1f}%"

    @property
    def roi_color(self) -> str:
        if self.roi_percent >= 20:
            return "#2e7d32"
        elif self.roi_percent >= 0:
            return "#f57c00"
        return "#d32f2f"

    @property
    def margin_display(self) -> str:
        return f"{self.margin_of_safety_percent:.1f}%"

    @property
    def margin_color(self) -> str:
        if self.margin_of_safety_percent >= 20:
            return "#2e7d32"
        elif self.margin_of_safety_percent >= 0:
            return "#f57c00"
        return "#d32f2f"


# ============================================================================
# DATA CLASSES - TRENDS
# ============================================================================

@dataclass
class TrendDataPoint:
    """Single data point for trend charts"""
    year: int
    value: float
    label: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TrendDataPoint":
        return cls(
            year=data.get("year", 0),
            value=float(data.get("value", 0)),
            label=data.get("label")
        )


# ============================================================================
# API CLIENT CLASS
# ============================================================================

class CropCostAnalysisAPI:
    """API client for crop cost analysis endpoints."""

    def __init__(self, client: APIClient):
        self._client = client

    def get_summary(
        self,
        crop_year: int,
        field_ids: Optional[List[int]] = None,
        crop_types: Optional[List[str]] = None
    ) -> Tuple[Optional[CropAnalysisSummary], Optional[str]]:
        """Get summary KPIs for crop cost analysis."""
        params = {"crop_year": crop_year}
        if field_ids:
            params["field_ids"] = ",".join(map(str, field_ids))
        if crop_types:
            params["crop_types"] = ",".join(crop_types)

        data, error = self._client.get("/api/v1/crop-analysis/summary", params=params)
        if error:
            return None, error
        return CropAnalysisSummary.from_dict(data), None

    def get_field_comparison(
        self,
        crop_year: int,
        field_ids: Optional[List[int]] = None,
        sort_by: str = "cost_per_acre",
        sort_order: str = "desc"
    ) -> Tuple[Optional[FieldComparisonMatrix], Optional[str]]:
        """Get field-by-field comparison data."""
        params = {
            "crop_year": crop_year,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        if field_ids:
            params["field_ids"] = ",".join(map(str, field_ids))

        data, error = self._client.get("/api/v1/crop-analysis/comparison", params=params)
        if error:
            return None, error
        return FieldComparisonMatrix.from_dict(data), None

    def get_crop_comparison(
        self,
        crop_year: int,
        crop_types: Optional[List[str]] = None
    ) -> Tuple[Optional[List[CropComparisonItem]], Optional[str]]:
        """Get crop comparison data."""
        params = {"crop_year": crop_year}
        if crop_types:
            params["crop_types"] = ",".join(crop_types)

        data, error = self._client.get("/api/v1/crop-analysis/crops", params=params)
        if error:
            return None, error
        return [CropComparisonItem.from_dict(item) for item in data], None

    def get_crop_detail(
        self,
        crop_type: str,
        crop_year: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Get detailed analysis for a specific crop type."""
        params = {"crop_year": crop_year}
        data, error = self._client.get(f"/api/v1/crop-analysis/crops/{crop_type}", params=params)
        if error:
            return None, error
        return data, None

    def get_field_history(
        self,
        field_id: int,
        years: Optional[List[int]] = None
    ) -> Tuple[Optional[List[YearOverYearData]], Optional[str]]:
        """Get multi-year history for a specific field."""
        params = {}
        if years:
            params["years"] = ",".join(map(str, years))

        data, error = self._client.get(f"/api/v1/crop-analysis/field/{field_id}/history", params=params)
        if error:
            return None, error
        return [YearOverYearData.from_dict(item) for item in data], None

    def get_year_comparison(
        self,
        years: List[int],
        field_id: Optional[int] = None,
        crop_type: Optional[str] = None
    ) -> Tuple[Optional[List[YearOverYearData]], Optional[str]]:
        """Compare costs and yields across multiple years."""
        params = {"years": ",".join(map(str, years))}
        if field_id:
            params["field_id"] = field_id
        if crop_type:
            params["crop_type"] = crop_type

        data, error = self._client.get("/api/v1/crop-analysis/years", params=params)
        if error:
            return None, error
        return [YearOverYearData.from_dict(item) for item in data], None

    def get_roi_analysis(
        self,
        crop_year: int,
        group_by: str = "field"
    ) -> Tuple[Optional[List[ROIAnalysisItem]], Optional[str]]:
        """Get ROI breakdown and profitability ranking."""
        params = {
            "crop_year": crop_year,
            "group_by": group_by
        }
        data, error = self._client.get("/api/v1/crop-analysis/roi", params=params)
        if error:
            return None, error
        return [ROIAnalysisItem.from_dict(item) for item in data], None

    def get_trends(
        self,
        start_year: int,
        end_year: int,
        metric: str = "cost_per_acre",
        field_id: Optional[int] = None,
        crop_type: Optional[str] = None
    ) -> Tuple[Optional[List[TrendDataPoint]], Optional[str]]:
        """Get trend data for charts."""
        params = {
            "start_year": start_year,
            "end_year": end_year,
            "metric": metric
        }
        if field_id:
            params["field_id"] = field_id
        if crop_type:
            params["crop_type"] = crop_type

        data, error = self._client.get("/api/v1/crop-analysis/trends", params=params)
        if error:
            return None, error
        return [TrendDataPoint.from_dict(item) for item in data], None


# ============================================================================
# SINGLETON
# ============================================================================

_crop_cost_analysis_api: Optional[CropCostAnalysisAPI] = None


def get_crop_cost_analysis_api() -> CropCostAnalysisAPI:
    """Get or create the crop cost analysis API singleton."""
    global _crop_cost_analysis_api
    if _crop_cost_analysis_api is None:
        _crop_cost_analysis_api = CropCostAnalysisAPI(get_api_client())
    return _crop_cost_analysis_api
