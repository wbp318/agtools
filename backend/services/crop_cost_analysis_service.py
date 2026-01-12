"""
Crop Cost Analysis Service
Comprehensive crop cost analysis with per-acre tracking, yield comparisons, and ROI calculations.

Provides:
- Summary KPIs (total cost, cost/acre, cost/bushel, ROI)
- Field vs field comparison
- Crop vs crop comparison
- Year over year trends
- ROI analysis and break-even calculations

AgTools v6.9.0
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import sqlite3

from pydantic import BaseModel, Field


# ============================================================================
# MARKET PRICES (same pattern as other services)
# ============================================================================

MARKET_PRICES = {
    "corn": 4.50,
    "soybean": 12.00,
    "soybeans": 12.00,
    "wheat": 6.00,
    "rice": 15.00,  # per cwt
    "cotton": 0.80,  # per lb
    "grain_sorghum": 4.25,
    "sorghum": 4.25,
    "alfalfa": 200.00,  # per ton
    "hay": 150.00,  # per ton
}

# Default yields by crop (bu/acre or appropriate unit)
DEFAULT_YIELDS = {
    "corn": 180,
    "soybean": 50,
    "soybeans": 50,
    "wheat": 55,
    "rice": 75,  # cwt
    "cotton": 1000,  # lbs
    "grain_sorghum": 100,
    "sorghum": 100,
}


# ============================================================================
# PYDANTIC MODELS - RESPONSES
# ============================================================================

class CropAnalysisSummary(BaseModel):
    """High-level KPIs for dashboard overview"""
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


class FieldCostDetail(BaseModel):
    """Cost breakdown for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    crop_type: Optional[str]
    acreage: float
    crop_year: int
    # Cost metrics
    total_cost: float
    cost_per_acre: float
    cost_per_bushel: Optional[float]
    # Yield metrics
    total_yield: float
    yield_per_acre: float
    # Revenue & ROI
    revenue: float
    profit: float
    roi_percent: float
    # Category breakdown
    cost_by_category: Dict[str, float]


class FieldComparisonMatrix(BaseModel):
    """Field vs field comparison matrix"""
    crop_year: int
    fields: List[FieldCostDetail]
    summary: Dict[str, Any]


class CropComparisonItem(BaseModel):
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


class YearOverYearData(BaseModel):
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


class ROIAnalysisItem(BaseModel):
    """ROI analysis for a field or crop"""
    entity_id: int
    entity_name: str
    entity_type: str  # 'field' or 'crop'
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


class TrendDataPoint(BaseModel):
    """Single data point for trend charts"""
    year: int
    value: float
    label: Optional[str] = None


# ============================================================================
# CROP COST ANALYSIS SERVICE
# ============================================================================

class CropCostAnalysisService:
    """
    Aggregation service for crop cost analysis.

    Combines data from:
    - expense_allocations (costs by field)
    - field_operations (yield data from harvest)
    - fields (acreage, crop type)
    """

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _safe_get(self, row: sqlite3.Row, key: str, default=None):
        """Safely get value from sqlite3.Row."""
        try:
            val = row[key]
            return val if val is not None else default
        except (KeyError, IndexError):
            return default

    def _get_market_price(self, crop_type: Optional[str]) -> float:
        """Get market price for a crop type."""
        if not crop_type:
            return 5.0
        return MARKET_PRICES.get(crop_type.lower(), 5.0)

    # ========================================================================
    # SUMMARY KPIs
    # ========================================================================

    def get_summary(
        self,
        crop_year: int,
        field_ids: Optional[List[int]] = None,
        crop_types: Optional[List[str]] = None
    ) -> CropAnalysisSummary:
        """
        Get high-level KPIs for the overview dashboard.

        Returns aggregate metrics across all fields or filtered subset.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build field filter
        field_filter = ""
        params: List[Any] = [crop_year]

        if field_ids:
            placeholders = ",".join("?" * len(field_ids))
            field_filter += f" AND f.id IN ({placeholders})"
            params.extend(field_ids)

        if crop_types:
            placeholders = ",".join("?" * len(crop_types))
            field_filter += f" AND LOWER(f.current_crop) IN ({placeholders})"
            params.extend([c.lower() for c in crop_types])

        # Get cost data by field and category
        cursor.execute(f"""
            SELECT
                f.id AS field_id,
                f.name AS field_name,
                f.acreage,
                f.current_crop,
                e.category,
                SUM(ea.allocated_amount) AS category_cost
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            JOIN fields f ON ea.field_id = f.id
            WHERE ea.crop_year = ?
              AND e.is_active = 1
              AND f.is_active = 1
              {field_filter}
            GROUP BY f.id, e.category
        """, params)

        cost_rows = cursor.fetchall()

        # Aggregate by field
        field_costs: Dict[int, Dict[str, Any]] = {}
        cost_by_category: Dict[str, float] = {}

        for row in cost_rows:
            fid = row["field_id"]
            if fid not in field_costs:
                field_costs[fid] = {
                    "name": row["field_name"],
                    "acreage": float(row["acreage"] or 0),
                    "crop": row["current_crop"],
                    "total_cost": 0.0
                }

            cat_cost = float(row["category_cost"] or 0)
            field_costs[fid]["total_cost"] += cat_cost

            category = row["category"]
            if category:
                cost_by_category[category] = cost_by_category.get(category, 0) + cat_cost

        # Get yield data
        yield_params = [crop_year]
        yield_filter = ""
        if field_ids:
            placeholders = ",".join("?" * len(field_ids))
            yield_filter += f" AND fo.field_id IN ({placeholders})"
            yield_params.extend(field_ids)

        cursor.execute(f"""
            SELECT
                fo.field_id,
                f.current_crop,
                SUM(COALESCE(fo.yield_amount, 0) * COALESCE(fo.acres_covered, f.acreage)) AS total_yield
            FROM field_operations fo
            JOIN fields f ON fo.field_id = f.id
            WHERE fo.operation_type = 'harvest'
              AND CAST(strftime('%Y', fo.operation_date) AS INTEGER) = ?
              AND fo.is_active = 1
              {yield_filter}
            GROUP BY fo.field_id
        """, yield_params)

        yield_rows = cursor.fetchall()
        field_yields: Dict[int, float] = {}
        for row in yield_rows:
            field_yields[row["field_id"]] = float(row["total_yield"] or 0)

        conn.close()

        # Calculate aggregates
        total_cost = sum(fc["total_cost"] for fc in field_costs.values())
        total_acres = sum(fc["acreage"] for fc in field_costs.values())
        total_yield = sum(field_yields.values())

        avg_cost_per_acre = total_cost / total_acres if total_acres > 0 else 0
        avg_cost_per_bushel = total_cost / total_yield if total_yield > 0 else None
        avg_yield_per_acre = total_yield / total_acres if total_acres > 0 else 0

        # Calculate revenue using weighted average price
        gross_revenue = 0.0
        for fid, fc in field_costs.items():
            crop = fc.get("crop")
            price = self._get_market_price(crop)
            field_yield = field_yields.get(fid, 0)
            gross_revenue += field_yield * price

        net_profit = gross_revenue - total_cost
        profit_margin = (net_profit / gross_revenue * 100) if gross_revenue > 0 else 0

        # Find top ROI crop
        crop_roi: Dict[str, Dict[str, float]] = {}
        for fid, fc in field_costs.items():
            crop = fc.get("crop") or "unknown"
            if crop not in crop_roi:
                crop_roi[crop] = {"cost": 0, "revenue": 0}
            crop_roi[crop]["cost"] += fc["total_cost"]
            price = self._get_market_price(crop)
            crop_roi[crop]["revenue"] += field_yields.get(fid, 0) * price

        top_roi_crop = None
        top_roi_value = 0.0
        for crop, data in crop_roi.items():
            if data["cost"] > 0:
                roi = (data["revenue"] - data["cost"]) / data["cost"] * 100
                if roi > top_roi_value or top_roi_crop is None:
                    top_roi_crop = crop
                    top_roi_value = roi

        return CropAnalysisSummary(
            crop_year=crop_year,
            total_cost=round(total_cost, 2),
            total_acres=round(total_acres, 2),
            avg_cost_per_acre=round(avg_cost_per_acre, 2),
            avg_cost_per_bushel=round(avg_cost_per_bushel, 2) if avg_cost_per_bushel else None,
            total_yield=round(total_yield, 2),
            avg_yield_per_acre=round(avg_yield_per_acre, 2),
            gross_revenue=round(gross_revenue, 2),
            net_profit=round(net_profit, 2),
            profit_margin_percent=round(profit_margin, 1),
            top_roi_crop=top_roi_crop,
            top_roi_value=round(top_roi_value, 1),
            field_count=len(field_costs),
            cost_by_category=cost_by_category
        )

    # ========================================================================
    # FIELD COMPARISON
    # ========================================================================

    def get_field_comparison(
        self,
        crop_year: int,
        field_ids: Optional[List[int]] = None,
        sort_by: str = "cost_per_acre",
        sort_order: str = "desc"
    ) -> FieldComparisonMatrix:
        """
        Get field-by-field comparison matrix.

        Joins expenses, yields, and calculates ROI for each field.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build filter
        field_filter = ""
        params: List[Any] = [crop_year]

        if field_ids:
            placeholders = ",".join("?" * len(field_ids))
            field_filter = f" AND f.id IN ({placeholders})"
            params.extend(field_ids)

        # Get all fields with costs
        cursor.execute(f"""
            SELECT
                f.id AS field_id,
                f.name AS field_name,
                f.farm_name,
                f.acreage,
                f.current_crop,
                e.category,
                SUM(ea.allocated_amount) AS category_cost
            FROM fields f
            LEFT JOIN expense_allocations ea ON ea.field_id = f.id AND ea.crop_year = ?
            LEFT JOIN expenses e ON ea.expense_id = e.id AND e.is_active = 1
            WHERE f.is_active = 1 {field_filter}
            GROUP BY f.id, e.category
        """, params)

        cost_rows = cursor.fetchall()

        # Get yield data
        cursor.execute(f"""
            SELECT
                fo.field_id,
                SUM(COALESCE(fo.yield_amount, 0) * COALESCE(fo.acres_covered, f.acreage)) AS total_yield
            FROM field_operations fo
            JOIN fields f ON fo.field_id = f.id
            WHERE fo.operation_type = 'harvest'
              AND CAST(strftime('%Y', fo.operation_date) AS INTEGER) = ?
              AND fo.is_active = 1
              {field_filter.replace('f.id', 'fo.field_id') if field_filter else ''}
            GROUP BY fo.field_id
        """, params)

        yield_rows = cursor.fetchall()
        field_yields: Dict[int, float] = {row["field_id"]: float(row["total_yield"] or 0) for row in yield_rows}

        conn.close()

        # Build field details
        field_data: Dict[int, Dict[str, Any]] = {}

        for row in cost_rows:
            fid = row["field_id"]
            if fid not in field_data:
                field_data[fid] = {
                    "field_id": fid,
                    "field_name": row["field_name"],
                    "farm_name": row["farm_name"],
                    "crop_type": row["current_crop"],
                    "acreage": float(row["acreage"] or 0),
                    "total_cost": 0.0,
                    "cost_by_category": {}
                }

            category = row["category"]
            cat_cost = float(row["category_cost"] or 0)

            if category:
                field_data[fid]["total_cost"] += cat_cost
                field_data[fid]["cost_by_category"][category] = cat_cost

        # Build field details list
        fields: List[FieldCostDetail] = []

        for fid, fd in field_data.items():
            acreage = fd["acreage"]
            total_cost = fd["total_cost"]
            total_yield = field_yields.get(fid, 0)
            crop = fd["crop_type"]
            price = self._get_market_price(crop)

            cost_per_acre = total_cost / acreage if acreage > 0 else 0
            cost_per_bushel = total_cost / total_yield if total_yield > 0 else None
            yield_per_acre = total_yield / acreage if acreage > 0 else 0
            revenue = total_yield * price
            profit = revenue - total_cost
            roi = (profit / total_cost * 100) if total_cost > 0 else 0

            fields.append(FieldCostDetail(
                field_id=fid,
                field_name=fd["field_name"],
                farm_name=fd["farm_name"],
                crop_type=crop,
                acreage=round(acreage, 2),
                crop_year=crop_year,
                total_cost=round(total_cost, 2),
                cost_per_acre=round(cost_per_acre, 2),
                cost_per_bushel=round(cost_per_bushel, 2) if cost_per_bushel else None,
                total_yield=round(total_yield, 2),
                yield_per_acre=round(yield_per_acre, 2),
                revenue=round(revenue, 2),
                profit=round(profit, 2),
                roi_percent=round(roi, 1),
                cost_by_category=fd["cost_by_category"]
            ))

        # Sort
        sort_key_map = {
            "cost_per_acre": lambda f: f.cost_per_acre,
            "cost_per_bushel": lambda f: f.cost_per_bushel or 0,
            "yield_per_acre": lambda f: f.yield_per_acre,
            "roi_percent": lambda f: f.roi_percent,
            "total_cost": lambda f: f.total_cost,
            "profit": lambda f: f.profit,
            "acreage": lambda f: f.acreage,
        }

        sort_func = sort_key_map.get(sort_by, lambda f: f.cost_per_acre)
        fields.sort(key=sort_func, reverse=(sort_order == "desc"))

        # Summary stats
        total_cost = sum(f.total_cost for f in fields)
        total_acres = sum(f.acreage for f in fields)
        total_yield = sum(f.total_yield for f in fields)
        total_revenue = sum(f.revenue for f in fields)

        summary = {
            "total_fields": len(fields),
            "total_cost": round(total_cost, 2),
            "total_acres": round(total_acres, 2),
            "avg_cost_per_acre": round(total_cost / total_acres, 2) if total_acres > 0 else 0,
            "total_yield": round(total_yield, 2),
            "total_revenue": round(total_revenue, 2),
            "net_profit": round(total_revenue - total_cost, 2)
        }

        return FieldComparisonMatrix(
            crop_year=crop_year,
            fields=fields,
            summary=summary
        )

    def get_field_history(
        self,
        field_id: int,
        years: Optional[List[int]] = None
    ) -> List[YearOverYearData]:
        """
        Get multi-year history for a specific field.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get field info
        cursor.execute("""
            SELECT id, name, acreage, current_crop
            FROM fields WHERE id = ? AND is_active = 1
        """, (field_id,))

        field_row = cursor.fetchone()
        if not field_row:
            conn.close()
            return []

        acreage = float(field_row["acreage"] or 0)
        crop = field_row["current_crop"]
        price = self._get_market_price(crop)

        # Get costs by year
        year_filter = ""
        params: List[Any] = [field_id]

        if years:
            placeholders = ",".join("?" * len(years))
            year_filter = f" AND ea.crop_year IN ({placeholders})"
            params.extend(years)

        cursor.execute(f"""
            SELECT
                ea.crop_year,
                SUM(ea.allocated_amount) AS total_cost
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            WHERE ea.field_id = ? AND e.is_active = 1 {year_filter}
            GROUP BY ea.crop_year
            ORDER BY ea.crop_year
        """, params)

        cost_by_year: Dict[int, float] = {}
        for row in cursor.fetchall():
            cost_by_year[row["crop_year"]] = float(row["total_cost"] or 0)

        # Get yields by year
        cursor.execute(f"""
            SELECT
                CAST(strftime('%Y', fo.operation_date) AS INTEGER) AS year,
                SUM(COALESCE(fo.yield_amount, 0) * COALESCE(fo.acres_covered, ?)) AS total_yield
            FROM field_operations fo
            WHERE fo.field_id = ?
              AND fo.operation_type = 'harvest'
              AND fo.is_active = 1
              {year_filter.replace('ea.crop_year', "CAST(strftime('%Y', fo.operation_date) AS INTEGER)") if year_filter else ''}
            GROUP BY year
            ORDER BY year
        """, [acreage, field_id] + (years if years else []))

        yield_by_year: Dict[int, float] = {}
        for row in cursor.fetchall():
            yield_by_year[row["year"]] = float(row["total_yield"] or 0)

        conn.close()

        # Build year data
        all_years = sorted(set(list(cost_by_year.keys()) + list(yield_by_year.keys())))

        results: List[YearOverYearData] = []
        for year in all_years:
            total_cost = cost_by_year.get(year, 0)
            total_yield = yield_by_year.get(year, 0)

            cost_per_acre = total_cost / acreage if acreage > 0 else 0
            cost_per_bushel = total_cost / total_yield if total_yield > 0 else None
            yield_per_acre = total_yield / acreage if acreage > 0 else 0
            revenue = total_yield * price
            profit = revenue - total_cost
            roi = (profit / total_cost * 100) if total_cost > 0 else 0

            results.append(YearOverYearData(
                year=year,
                total_acres=round(acreage, 2),
                total_cost=round(total_cost, 2),
                avg_cost_per_acre=round(cost_per_acre, 2),
                avg_cost_per_bushel=round(cost_per_bushel, 2) if cost_per_bushel else None,
                total_yield=round(total_yield, 2),
                avg_yield_per_acre=round(yield_per_acre, 2),
                revenue=round(revenue, 2),
                profit=round(profit, 2),
                roi_percent=round(roi, 1)
            ))

        return results

    # ========================================================================
    # CROP COMPARISON
    # ========================================================================

    def get_crop_comparison(
        self,
        crop_year: int,
        crop_types: Optional[List[str]] = None
    ) -> List[CropComparisonItem]:
        """
        Compare crops across all fields.

        Aggregates by crop type.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build filter
        crop_filter = ""
        params: List[Any] = [crop_year]

        if crop_types:
            placeholders = ",".join("?" * len(crop_types))
            crop_filter = f" AND LOWER(f.current_crop) IN ({placeholders})"
            params.extend([c.lower() for c in crop_types])

        # Get costs by crop
        cursor.execute(f"""
            SELECT
                LOWER(f.current_crop) AS crop_type,
                COUNT(DISTINCT f.id) AS field_count,
                SUM(DISTINCT f.acreage) AS total_acres,
                SUM(ea.allocated_amount) AS total_cost
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            JOIN fields f ON ea.field_id = f.id
            WHERE ea.crop_year = ?
              AND e.is_active = 1
              AND f.is_active = 1
              AND f.current_crop IS NOT NULL
              {crop_filter}
            GROUP BY LOWER(f.current_crop)
        """, params)

        crop_costs: Dict[str, Dict[str, float]] = {}
        for row in cursor.fetchall():
            crop = row["crop_type"]
            if crop:
                crop_costs[crop] = {
                    "field_count": row["field_count"],
                    "total_acres": float(row["total_acres"] or 0),
                    "total_cost": float(row["total_cost"] or 0)
                }

        # Get yields by crop
        cursor.execute(f"""
            SELECT
                LOWER(f.current_crop) AS crop_type,
                SUM(COALESCE(fo.yield_amount, 0) * COALESCE(fo.acres_covered, f.acreage)) AS total_yield
            FROM field_operations fo
            JOIN fields f ON fo.field_id = f.id
            WHERE fo.operation_type = 'harvest'
              AND CAST(strftime('%Y', fo.operation_date) AS INTEGER) = ?
              AND fo.is_active = 1
              AND f.current_crop IS NOT NULL
              {crop_filter.replace('ea.crop_year = ?', "CAST(strftime('%Y', fo.operation_date) AS INTEGER) = ?") if crop_filter else ''}
            GROUP BY LOWER(f.current_crop)
        """, params)

        crop_yields: Dict[str, float] = {}
        for row in cursor.fetchall():
            crop = row["crop_type"]
            if crop:
                crop_yields[crop] = float(row["total_yield"] or 0)

        conn.close()

        # Build comparison items
        results: List[CropComparisonItem] = []

        for crop, data in crop_costs.items():
            total_acres = data["total_acres"]
            total_cost = data["total_cost"]
            total_yield = crop_yields.get(crop, 0)
            price = self._get_market_price(crop)

            avg_cost_per_acre = total_cost / total_acres if total_acres > 0 else 0
            avg_cost_per_bushel = total_cost / total_yield if total_yield > 0 else None
            avg_yield_per_acre = total_yield / total_acres if total_acres > 0 else 0
            revenue = total_yield * price
            profit = revenue - total_cost
            roi = (profit / total_cost * 100) if total_cost > 0 else 0

            results.append(CropComparisonItem(
                crop_type=crop.title(),
                total_acres=round(total_acres, 2),
                field_count=data["field_count"],
                total_cost=round(total_cost, 2),
                avg_cost_per_acre=round(avg_cost_per_acre, 2),
                avg_cost_per_bushel=round(avg_cost_per_bushel, 2) if avg_cost_per_bushel else None,
                total_yield=round(total_yield, 2),
                avg_yield_per_acre=round(avg_yield_per_acre, 2),
                total_revenue=round(revenue, 2),
                profit=round(profit, 2),
                roi_percent=round(roi, 1)
            ))

        # Sort by ROI descending
        results.sort(key=lambda x: x.roi_percent, reverse=True)

        return results

    def get_crop_detail(
        self,
        crop_type: str,
        crop_year: int
    ) -> Dict[str, Any]:
        """
        Get detailed breakdown for a specific crop type.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        crop_lower = crop_type.lower()

        # Get fields with this crop
        cursor.execute("""
            SELECT
                f.id AS field_id,
                f.name AS field_name,
                f.farm_name,
                f.acreage
            FROM fields f
            WHERE LOWER(f.current_crop) = ? AND f.is_active = 1
        """, (crop_lower,))

        fields = []
        field_ids = []
        for row in cursor.fetchall():
            fields.append({
                "field_id": row["field_id"],
                "field_name": row["field_name"],
                "farm_name": row["farm_name"],
                "acreage": float(row["acreage"] or 0)
            })
            field_ids.append(row["field_id"])

        if not field_ids:
            conn.close()
            return {
                "crop_type": crop_type,
                "crop_year": crop_year,
                "fields": [],
                "cost_by_category": {},
                "summary": {}
            }

        placeholders = ",".join("?" * len(field_ids))

        # Get costs by category
        cursor.execute(f"""
            SELECT
                e.category,
                SUM(ea.allocated_amount) AS total_cost
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            WHERE ea.field_id IN ({placeholders})
              AND ea.crop_year = ?
              AND e.is_active = 1
            GROUP BY e.category
        """, field_ids + [crop_year])

        cost_by_category: Dict[str, float] = {}
        total_cost = 0.0
        for row in cursor.fetchall():
            cat = row["category"]
            cost = float(row["total_cost"] or 0)
            if cat:
                cost_by_category[cat] = cost
                total_cost += cost

        # Get total yield
        cursor.execute(f"""
            SELECT
                SUM(COALESCE(fo.yield_amount, 0) * COALESCE(fo.acres_covered, f.acreage)) AS total_yield
            FROM field_operations fo
            JOIN fields f ON fo.field_id = f.id
            WHERE fo.field_id IN ({placeholders})
              AND fo.operation_type = 'harvest'
              AND CAST(strftime('%Y', fo.operation_date) AS INTEGER) = ?
              AND fo.is_active = 1
        """, field_ids + [crop_year])

        yield_row = cursor.fetchone()
        total_yield = float(yield_row["total_yield"] or 0) if yield_row else 0

        conn.close()

        # Calculate summary
        total_acres = sum(f["acreage"] for f in fields)
        price = self._get_market_price(crop_type)
        revenue = total_yield * price
        profit = revenue - total_cost
        roi = (profit / total_cost * 100) if total_cost > 0 else 0

        return {
            "crop_type": crop_type.title(),
            "crop_year": crop_year,
            "fields": fields,
            "cost_by_category": cost_by_category,
            "summary": {
                "total_acres": round(total_acres, 2),
                "total_cost": round(total_cost, 2),
                "cost_per_acre": round(total_cost / total_acres, 2) if total_acres > 0 else 0,
                "total_yield": round(total_yield, 2),
                "yield_per_acre": round(total_yield / total_acres, 2) if total_acres > 0 else 0,
                "revenue": round(revenue, 2),
                "profit": round(profit, 2),
                "roi_percent": round(roi, 1),
                "market_price": price
            }
        }

    # ========================================================================
    # YEAR OVER YEAR
    # ========================================================================

    def get_year_comparison(
        self,
        years: List[int],
        field_id: Optional[int] = None,
        crop_type: Optional[str] = None
    ) -> List[YearOverYearData]:
        """
        Compare costs and yields across multiple years.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build filters
        filters = []
        params: List[Any] = []

        if field_id:
            filters.append("ea.field_id = ?")
            params.append(field_id)

        if crop_type:
            filters.append("LOWER(f.current_crop) = ?")
            params.append(crop_type.lower())

        filter_sql = " AND " + " AND ".join(filters) if filters else ""

        results: List[YearOverYearData] = []

        for year in sorted(years):
            # Get costs for this year
            cursor.execute(f"""
                SELECT
                    SUM(ea.allocated_amount) AS total_cost,
                    SUM(DISTINCT f.acreage) AS total_acres
                FROM expense_allocations ea
                JOIN expenses e ON ea.expense_id = e.id
                JOIN fields f ON ea.field_id = f.id
                WHERE ea.crop_year = ?
                  AND e.is_active = 1
                  AND f.is_active = 1
                  {filter_sql}
            """, [year] + params)

            cost_row = cursor.fetchone()
            total_cost = float(cost_row["total_cost"] or 0) if cost_row else 0
            total_acres = float(cost_row["total_acres"] or 0) if cost_row else 0

            # Get yields for this year
            yield_filter = filter_sql.replace("ea.field_id", "fo.field_id").replace("ea.crop_year", "1=1")
            cursor.execute(f"""
                SELECT
                    SUM(COALESCE(fo.yield_amount, 0) * COALESCE(fo.acres_covered, f.acreage)) AS total_yield
                FROM field_operations fo
                JOIN fields f ON fo.field_id = f.id
                WHERE fo.operation_type = 'harvest'
                  AND CAST(strftime('%Y', fo.operation_date) AS INTEGER) = ?
                  AND fo.is_active = 1
                  {yield_filter}
            """, [year] + params)

            yield_row = cursor.fetchone()
            total_yield = float(yield_row["total_yield"] or 0) if yield_row else 0

            # Calculate metrics
            avg_price = 5.0  # Default
            if crop_type:
                avg_price = self._get_market_price(crop_type)

            cost_per_acre = total_cost / total_acres if total_acres > 0 else 0
            cost_per_bushel = total_cost / total_yield if total_yield > 0 else None
            yield_per_acre = total_yield / total_acres if total_acres > 0 else 0
            revenue = total_yield * avg_price
            profit = revenue - total_cost
            roi = (profit / total_cost * 100) if total_cost > 0 else 0

            results.append(YearOverYearData(
                year=year,
                total_acres=round(total_acres, 2),
                total_cost=round(total_cost, 2),
                avg_cost_per_acre=round(cost_per_acre, 2),
                avg_cost_per_bushel=round(cost_per_bushel, 2) if cost_per_bushel else None,
                total_yield=round(total_yield, 2),
                avg_yield_per_acre=round(yield_per_acre, 2),
                revenue=round(revenue, 2),
                profit=round(profit, 2),
                roi_percent=round(roi, 1)
            ))

        conn.close()
        return results

    def get_trend_data(
        self,
        start_year: int,
        end_year: int,
        metric: str = "cost_per_acre",
        field_id: Optional[int] = None,
        crop_type: Optional[str] = None
    ) -> List[TrendDataPoint]:
        """
        Get trend data for charting.
        """
        years = list(range(start_year, end_year + 1))
        year_data = self.get_year_comparison(years, field_id, crop_type)

        metric_map = {
            "cost_per_acre": lambda d: d.avg_cost_per_acre,
            "cost_per_bushel": lambda d: d.avg_cost_per_bushel or 0,
            "yield_per_acre": lambda d: d.avg_yield_per_acre,
            "roi_percent": lambda d: d.roi_percent,
            "total_cost": lambda d: d.total_cost,
            "profit": lambda d: d.profit,
        }

        value_func = metric_map.get(metric, lambda d: d.avg_cost_per_acre)

        return [
            TrendDataPoint(
                year=d.year,
                value=value_func(d),
                label=f"{d.year}"
            )
            for d in year_data
        ]

    # ========================================================================
    # ROI ANALYSIS
    # ========================================================================

    def get_roi_breakdown(
        self,
        crop_year: int,
        group_by: str = "field"  # 'field' or 'crop'
    ) -> List[ROIAnalysisItem]:
        """
        Get ROI analysis by field or crop.
        """
        if group_by == "crop":
            return self._get_roi_by_crop(crop_year)
        else:
            return self._get_roi_by_field(crop_year)

    def _get_roi_by_field(self, crop_year: int) -> List[ROIAnalysisItem]:
        """Get ROI breakdown by field."""
        comparison = self.get_field_comparison(crop_year)

        results: List[ROIAnalysisItem] = []

        for field in comparison.fields:
            if field.total_cost == 0:
                continue

            price = self._get_market_price(field.crop_type)
            be_yield = field.total_cost / price if price > 0 else 0
            be_price = field.total_cost / field.total_yield if field.total_yield > 0 else 0

            margin_of_safety = 0.0
            if field.total_yield > 0 and be_yield > 0:
                margin_of_safety = (field.total_yield - be_yield) / field.total_yield * 100

            results.append(ROIAnalysisItem(
                entity_id=field.field_id,
                entity_name=field.field_name,
                entity_type="field",
                crop_type=field.crop_type,
                acreage=field.acreage,
                total_investment=field.total_cost,
                total_return=field.revenue,
                net_profit=field.profit,
                roi_percent=field.roi_percent,
                break_even_yield=round(be_yield, 2),
                break_even_price=round(be_price, 2),
                margin_of_safety_percent=round(margin_of_safety, 1),
                actual_yield=field.total_yield,
                market_price=price
            ))

        # Sort by ROI descending
        results.sort(key=lambda x: x.roi_percent, reverse=True)
        return results

    def _get_roi_by_crop(self, crop_year: int) -> List[ROIAnalysisItem]:
        """Get ROI breakdown by crop type."""
        crop_comparison = self.get_crop_comparison(crop_year)

        results: List[ROIAnalysisItem] = []

        for idx, crop in enumerate(crop_comparison):
            if crop.total_cost == 0:
                continue

            price = self._get_market_price(crop.crop_type)
            be_yield = crop.total_cost / price if price > 0 else 0
            be_price = crop.total_cost / crop.total_yield if crop.total_yield > 0 else 0

            margin_of_safety = 0.0
            if crop.total_yield > 0 and be_yield > 0:
                margin_of_safety = (crop.total_yield - be_yield) / crop.total_yield * 100

            results.append(ROIAnalysisItem(
                entity_id=idx + 1,
                entity_name=crop.crop_type,
                entity_type="crop",
                crop_type=crop.crop_type,
                acreage=crop.total_acres,
                total_investment=crop.total_cost,
                total_return=crop.total_revenue,
                net_profit=crop.profit,
                roi_percent=crop.roi_percent,
                break_even_yield=round(be_yield, 2),
                break_even_price=round(be_price, 2),
                margin_of_safety_percent=round(margin_of_safety, 1),
                actual_yield=crop.total_yield,
                market_price=price
            ))

        # Sort by ROI descending
        results.sort(key=lambda x: x.roi_percent, reverse=True)
        return results

    def get_service_summary(self) -> Dict[str, Any]:
        """Get service status summary."""
        return {
            "service": "CropCostAnalysisService",
            "version": "6.9.0",
            "description": "Crop cost analysis with per-acre tracking and ROI calculations",
            "endpoints": [
                "GET /api/v1/crop-analysis/summary",
                "GET /api/v1/crop-analysis/comparison",
                "GET /api/v1/crop-analysis/field/{field_id}/history",
                "GET /api/v1/crop-analysis/crops/{crop_type}",
                "GET /api/v1/crop-analysis/roi",
                "GET /api/v1/crop-analysis/trends"
            ]
        }


# ============================================================================
# MODULE-LEVEL SINGLETON GETTER
# ============================================================================

_crop_cost_analysis_service: Optional[CropCostAnalysisService] = None


def get_crop_cost_analysis_service(db_path: str = "agtools.db") -> CropCostAnalysisService:
    """Get or create the crop cost analysis service singleton."""
    global _crop_cost_analysis_service
    if _crop_cost_analysis_service is None:
        _crop_cost_analysis_service = CropCostAnalysisService(db_path)
    return _crop_cost_analysis_service
