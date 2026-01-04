"""
GenFin Fixed Asset Manager Service
Handles fixed asset tracking, depreciation calculations, and disposal.
"""
from datetime import datetime, date
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid
from dateutil.relativedelta import relativedelta


class DepreciationMethod(Enum):
    """Depreciation calculation methods"""
    STRAIGHT_LINE = "straight_line"
    MACRS_3 = "macrs_3"      # 3-year MACRS
    MACRS_5 = "macrs_5"      # 5-year MACRS
    MACRS_7 = "macrs_7"      # 7-year MACRS (farm machinery)
    MACRS_10 = "macrs_10"    # 10-year MACRS
    MACRS_15 = "macrs_15"    # 15-year MACRS
    MACRS_20 = "macrs_20"    # 20-year MACRS
    MACRS_27_5 = "macrs_27_5"  # 27.5-year (residential rental)
    MACRS_39 = "macrs_39"    # 39-year (commercial property)
    SECTION_179 = "section_179"  # Full expensing
    BONUS_100 = "bonus_100"  # 100% bonus depreciation
    NO_DEPRECIATION = "none"


class AssetStatus(Enum):
    """Asset status"""
    ACTIVE = "active"
    DISPOSED = "disposed"
    FULLY_DEPRECIATED = "fully_depreciated"
    INACTIVE = "inactive"


class AssetCategory(Enum):
    """Asset categories for farms"""
    FARM_MACHINERY = "farm_machinery"      # Tractors, combines, planters
    FARM_EQUIPMENT = "farm_equipment"      # Same as farm_machinery - alias
    EQUIPMENT = "equipment"                 # General equipment
    VEHICLES = "vehicles"                   # Trucks, cars, ATVs
    BUILDINGS = "buildings"                 # Barns, shops, bins
    LAND_IMPROVEMENTS = "land_improvements" # Fencing, drainage, irrigation
    OFFICE_EQUIPMENT = "office_equipment"   # Computers, furniture
    LIVESTOCK = "livestock"                 # Breeding stock
    OTHER = "other"


@dataclass
class FixedAsset:
    """A fixed asset"""
    asset_id: str
    name: str
    description: str = ""
    category: AssetCategory = AssetCategory.OTHER

    # Purchase info
    purchase_date: date = None
    purchase_price: float = 0.0
    vendor_id: Optional[str] = None
    po_number: str = ""
    serial_number: str = ""

    # Depreciation setup
    depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    useful_life_years: int = 7
    salvage_value: float = 0.0
    in_service_date: date = None

    # Current values
    cost_basis: float = 0.0  # May differ from purchase price (adjustments)
    accumulated_depreciation: float = 0.0
    book_value: float = 0.0

    # Section 179 / Bonus
    section_179_amount: float = 0.0
    bonus_depreciation_amount: float = 0.0

    # Disposal
    disposal_date: Optional[date] = None
    disposal_amount: float = 0.0
    disposal_method: str = ""  # sold, scrapped, traded, donated

    # Tracking
    location: str = ""
    assigned_to: str = ""
    notes: str = ""

    # GL accounts
    asset_account_id: str = ""
    depreciation_expense_account_id: str = ""
    accumulated_depreciation_account_id: str = ""

    # Status
    status: AssetStatus = AssetStatus.ACTIVE

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DepreciationEntry:
    """A depreciation entry for an asset"""
    entry_id: str
    asset_id: str
    period_date: date  # Usually month-end
    depreciation_amount: float
    accumulated_total: float
    book_value_after: float
    method_used: DepreciationMethod
    journal_entry_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


# MACRS depreciation tables (half-year convention)
MACRS_RATES = {
    "macrs_3": [33.33, 44.45, 14.81, 7.41],
    "macrs_5": [20.00, 32.00, 19.20, 11.52, 11.52, 5.76],
    "macrs_7": [14.29, 24.49, 17.49, 12.49, 8.93, 8.92, 8.93, 4.46],
    "macrs_10": [10.00, 18.00, 14.40, 11.52, 9.22, 7.37, 6.55, 6.55, 6.56, 6.55, 3.28],
    "macrs_15": [5.00, 9.50, 8.55, 7.70, 6.93, 6.23, 5.90, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 2.95],
    "macrs_20": [3.750, 7.219, 6.677, 6.177, 5.713, 5.285, 4.888, 4.522, 4.462, 4.461, 4.462, 4.461, 4.462, 4.461, 4.462, 4.461, 4.462, 4.461, 4.462, 4.461, 2.231]
}


class GenFinFixedAssetsService:
    """
    Manages fixed assets for GenFin.

    Features:
    - Asset register with full tracking
    - Multiple depreciation methods (MACRS, Straight-Line, Section 179)
    - Automatic depreciation calculations
    - Disposal tracking with gain/loss
    - Asset reports
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

        self.assets: Dict[str, FixedAsset] = {}
        self.depreciation_entries: Dict[str, DepreciationEntry] = {}

        self._initialized = True

    # ==================== ASSET MANAGEMENT ====================

    def create_asset(
        self,
        name: str,
        purchase_date: str,
        purchase_price: float,
        category: str = "other",
        depreciation_method: str = "macrs_7",
        useful_life_years: int = 7,
        salvage_value: float = 0.0,
        in_service_date: str = None,
        description: str = "",
        serial_number: str = "",
        location: str = "",
        vendor_id: str = None,
        section_179_amount: float = 0.0,
        bonus_depreciation_percent: float = 0.0,
        asset_account_id: str = "1500",
        depreciation_expense_account_id: str = "6100",
        accumulated_depreciation_account_id: str = "1550"
    ) -> Dict:
        """Create a new fixed asset"""
        asset_id = str(uuid.uuid4())

        purch_date = datetime.strptime(purchase_date, "%Y-%m-%d").date()
        service_date = datetime.strptime(in_service_date, "%Y-%m-%d").date() if in_service_date else purch_date

        # Calculate cost basis after Section 179 and bonus
        bonus_amount = purchase_price * (bonus_depreciation_percent / 100) if bonus_depreciation_percent else 0.0
        cost_basis = purchase_price - section_179_amount - bonus_amount

        asset = FixedAsset(
            asset_id=asset_id,
            name=name,
            description=description,
            category=AssetCategory(category),
            purchase_date=purch_date,
            purchase_price=purchase_price,
            vendor_id=vendor_id,
            serial_number=serial_number,
            depreciation_method=DepreciationMethod(depreciation_method),
            useful_life_years=useful_life_years,
            salvage_value=salvage_value,
            in_service_date=service_date,
            cost_basis=cost_basis,
            accumulated_depreciation=section_179_amount + bonus_amount,
            book_value=cost_basis,
            section_179_amount=section_179_amount,
            bonus_depreciation_amount=bonus_amount,
            location=location,
            asset_account_id=asset_account_id,
            depreciation_expense_account_id=depreciation_expense_account_id,
            accumulated_depreciation_account_id=accumulated_depreciation_account_id
        )

        self.assets[asset_id] = asset

        return {
            "success": True,
            "asset_id": asset_id,
            "name": name,
            "purchase_price": purchase_price,
            "cost_basis": cost_basis,
            "section_179": section_179_amount,
            "bonus_depreciation": bonus_amount,
            "depreciation_method": depreciation_method
        }

    def update_asset(self, asset_id: str, **kwargs) -> Dict:
        """Update an asset"""
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found"}

        asset = self.assets[asset_id]

        for key, value in kwargs.items():
            if hasattr(asset, key):
                if key in ["purchase_date", "in_service_date", "disposal_date"] and isinstance(value, str):
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                elif key == "category":
                    value = AssetCategory(value)
                elif key == "depreciation_method":
                    value = DepreciationMethod(value)
                elif key == "status":
                    value = AssetStatus(value)
                setattr(asset, key, value)

        asset.updated_at = datetime.now()

        return {"success": True, "asset_id": asset_id, "message": "Asset updated"}

    def get_asset(self, asset_id: str) -> Optional[Dict]:
        """Get a single asset"""
        if asset_id not in self.assets:
            return None
        return self._asset_to_dict(self.assets[asset_id])

    def list_assets(
        self,
        category: str = None,
        status: str = None
    ) -> Dict:
        """List all assets"""
        assets_list = []

        for asset in self.assets.values():
            if category and asset.category.value != category:
                continue
            if status and asset.status.value != status:
                continue
            assets_list.append(self._asset_to_dict(asset))

        # Sort by name
        assets_list.sort(key=lambda x: x["name"])

        total_cost = sum(a["purchase_price"] for a in assets_list)
        total_book_value = sum(a["book_value"] for a in assets_list)
        total_depreciation = sum(a["accumulated_depreciation"] for a in assets_list)

        return {
            "assets": assets_list,
            "total": len(assets_list),
            "total_cost": round(total_cost, 2),
            "total_book_value": round(total_book_value, 2),
            "total_accumulated_depreciation": round(total_depreciation, 2)
        }

    def delete_asset(self, asset_id: str) -> Dict:
        """Delete an asset (only if no depreciation taken)"""
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found"}

        # Check for depreciation entries
        has_entries = any(e.asset_id == asset_id for e in self.depreciation_entries.values())
        if has_entries:
            return {"success": False, "error": "Cannot delete asset with depreciation history. Dispose instead."}

        del self.assets[asset_id]
        return {"success": True, "message": "Asset deleted"}

    # ==================== DEPRECIATION ====================

    def calculate_annual_depreciation(self, asset_id: str, year: int) -> Dict:
        """Calculate depreciation for a specific year"""
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found"}

        asset = self.assets[asset_id]

        if asset.status in [AssetStatus.DISPOSED, AssetStatus.FULLY_DEPRECIATED]:
            return {"success": False, "error": "Asset is disposed or fully depreciated"}

        # Handle missing in_service_date
        if not asset.in_service_date:
            return {"depreciation": 0, "year": year, "message": "Asset has no in-service date"}

        # Get asset year (years since in-service)
        years_in_service = year - asset.in_service_date.year + 1

        if years_in_service < 1:
            return {"depreciation": 0, "year": year, "message": "Asset not yet in service"}

        depreciation = 0.0

        # Ensure we have valid values for calculation (default to 0 if None)
        cost_basis = asset.cost_basis or 0.0
        salvage_value = asset.salvage_value or 0.0
        useful_life = asset.useful_life_years or 1  # Prevent division by zero

        if asset.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
            # Straight-line: (Cost - Salvage) / Life
            annual_depr = (cost_basis - salvage_value) / useful_life
            if years_in_service <= asset.useful_life_years:
                depreciation = annual_depr

        elif asset.depreciation_method == DepreciationMethod.SECTION_179:
            # Section 179: All in first year
            if years_in_service == 1:
                depreciation = cost_basis

        elif asset.depreciation_method == DepreciationMethod.BONUS_100:
            # 100% bonus: All in first year
            if years_in_service == 1:
                depreciation = cost_basis

        elif asset.depreciation_method.value.startswith("macrs"):
            # MACRS depreciation
            rates = MACRS_RATES.get(asset.depreciation_method.value, [])
            if years_in_service <= len(rates):
                rate = rates[years_in_service - 1]
                depreciation = cost_basis * (rate / 100)

        # Don't exceed remaining book value
        remaining = asset.book_value or 0.0
        depreciation = min(depreciation, remaining)

        return {
            "asset_id": asset_id,
            "year": year,
            "depreciation": round(depreciation, 2),
            "method": asset.depreciation_method.value,
            "years_in_service": years_in_service
        }

    def run_depreciation(self, period_date: str, asset_id: str = None) -> Dict:
        """Run depreciation for period (usually monthly)"""
        per_date = datetime.strptime(period_date, "%Y-%m-%d").date()
        year = per_date.year

        results = []
        total_depreciation = 0.0

        # Handle specific asset or all assets
        if asset_id:
            if asset_id not in self.assets:
                return {"success": False, "error": f"Asset {asset_id} not found"}
            assets_to_process = [self.assets[asset_id]]
        else:
            assets_to_process = list(self.assets.values())

        for asset in assets_to_process:
            if asset.status != AssetStatus.ACTIVE:
                continue

            # Ensure we have valid values (default to 0 if None)
            book_value = asset.book_value or 0.0
            accumulated_depr = asset.accumulated_depreciation or 0.0
            purchase_price = asset.purchase_price or 0.0

            if book_value <= 0:
                asset.status = AssetStatus.FULLY_DEPRECIATED
                continue

            # Calculate annual depreciation
            annual_calc = self.calculate_annual_depreciation(asset.asset_id, year)
            annual_depr = annual_calc.get("depreciation", 0)

            # Monthly portion (for monthly runs)
            monthly_depr = annual_depr / 12

            # Don't exceed book value
            monthly_depr = min(monthly_depr, book_value)

            if monthly_depr > 0:
                # Create entry
                entry_id = str(uuid.uuid4())

                new_accumulated = accumulated_depr + monthly_depr
                new_book_value = purchase_price - new_accumulated

                entry = DepreciationEntry(
                    entry_id=entry_id,
                    asset_id=asset.asset_id,
                    period_date=per_date,
                    depreciation_amount=monthly_depr,
                    accumulated_total=new_accumulated,
                    book_value_after=new_book_value,
                    method_used=asset.depreciation_method
                )

                self.depreciation_entries[entry_id] = entry

                # Update asset
                asset.accumulated_depreciation = new_accumulated
                asset.book_value = new_book_value
                asset.updated_at = datetime.now()

                salvage_val = asset.salvage_value or 0.0
                if asset.book_value <= salvage_val:
                    asset.status = AssetStatus.FULLY_DEPRECIATED

                results.append({
                    "asset_id": asset.asset_id,
                    "asset_name": asset.name,
                    "depreciation": round(monthly_depr, 2),
                    "new_book_value": round(new_book_value, 2)
                })

                total_depreciation += monthly_depr

        return {
            "success": True,
            "period_date": period_date,
            "assets_processed": len(results),
            "total_depreciation": round(total_depreciation, 2),
            "entries": results
        }

    def get_depreciation_schedule(self, asset_id: str) -> Dict:
        """Get full depreciation schedule for an asset"""
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found"}

        asset = self.assets[asset_id]

        # Handle missing in_service_date
        if not asset.in_service_date:
            return {"success": False, "error": "Asset has no in-service date"}

        # Ensure valid values (default to 0 if None)
        section_179 = asset.section_179_amount or 0.0
        bonus_depr = asset.bonus_depreciation_amount or 0.0
        purchase_price = asset.purchase_price or 0.0
        salvage_value = asset.salvage_value or 0.0

        schedule = []
        running_depr = section_179 + bonus_depr
        running_book = purchase_price - running_depr

        # Add Section 179/Bonus if applicable
        if section_179 > 0:
            schedule.append({
                "year": asset.in_service_date.year,
                "period": "Section 179",
                "depreciation": section_179,
                "accumulated": running_depr,
                "book_value": running_book
            })

        if bonus_depr > 0:
            schedule.append({
                "year": asset.in_service_date.year,
                "period": "Bonus Depreciation",
                "depreciation": bonus_depr,
                "accumulated": running_depr,
                "book_value": running_book
            })

        # Project future depreciation
        useful_life = asset.useful_life_years or 1
        for year_offset in range(useful_life + 1):
            year = asset.in_service_date.year + year_offset
            calc = self.calculate_annual_depreciation(asset_id, year)
            depr = calc.get("depreciation", 0)

            if depr > 0:
                running_depr += depr
                running_book -= depr

                schedule.append({
                    "year": year,
                    "period": f"Year {year_offset + 1}",
                    "depreciation": round(depr, 2),
                    "accumulated": round(running_depr, 2),
                    "book_value": round(max(running_book, salvage_value), 2)
                })

        return {
            "asset_id": asset_id,
            "asset_name": asset.name,
            "purchase_price": asset.purchase_price,
            "cost_basis": asset.cost_basis,
            "salvage_value": asset.salvage_value,
            "method": asset.depreciation_method.value,
            "useful_life": asset.useful_life_years,
            "schedule": schedule
        }

    def get_depreciation_history(self, asset_id: str = None) -> Dict:
        """Get actual depreciation entries"""
        entries = []

        for entry in self.depreciation_entries.values():
            if asset_id and entry.asset_id != asset_id:
                continue

            asset = self.assets.get(entry.asset_id)

            entries.append({
                "entry_id": entry.entry_id,
                "asset_id": entry.asset_id,
                "asset_name": asset.name if asset else "Unknown",
                "period_date": entry.period_date.isoformat(),
                "depreciation_amount": entry.depreciation_amount,
                "accumulated_total": entry.accumulated_total,
                "book_value_after": entry.book_value_after,
                "method": entry.method_used.value
            })

        entries.sort(key=lambda x: x["period_date"], reverse=True)

        return {"entries": entries, "total": len(entries)}

    # ==================== DISPOSAL ====================

    def dispose_asset(
        self,
        asset_id: str,
        disposal_date: str,
        disposal_amount: float,
        disposal_method: str = "sold"
    ) -> Dict:
        """Dispose of an asset (sell, scrap, trade, donate)"""
        if asset_id not in self.assets:
            return {"success": False, "error": "Asset not found"}

        asset = self.assets[asset_id]

        if asset.status == AssetStatus.DISPOSED:
            return {"success": False, "error": "Asset already disposed"}

        disp_date = datetime.strptime(disposal_date, "%Y-%m-%d").date()

        # Calculate gain/loss
        gain_loss = disposal_amount - asset.book_value

        asset.disposal_date = disp_date
        asset.disposal_amount = disposal_amount
        asset.disposal_method = disposal_method
        asset.status = AssetStatus.DISPOSED
        asset.updated_at = datetime.now()

        return {
            "success": True,
            "asset_id": asset_id,
            "asset_name": asset.name,
            "disposal_date": disposal_date,
            "disposal_amount": disposal_amount,
            "book_value_at_disposal": round(asset.book_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_type": "gain" if gain_loss > 0 else "loss" if gain_loss < 0 else "break_even"
        }

    # ==================== REPORTS ====================

    def get_asset_register_report(self, as_of_date: str = None) -> Dict:
        """Get asset register report"""
        report_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()

        assets_data = []

        for asset in self.assets.values():
            # Skip assets without purchase date or purchased after report date
            if not asset.purchase_date or asset.purchase_date > report_date:
                continue

            assets_data.append({
                "asset_id": asset.asset_id,
                "name": asset.name,
                "category": asset.category.value,
                "purchase_date": asset.purchase_date.isoformat(),
                "purchase_price": asset.purchase_price or 0.0,
                "depreciation_method": asset.depreciation_method.value,
                "accumulated_depreciation": round(asset.accumulated_depreciation or 0.0, 2),
                "book_value": round(asset.book_value or 0.0, 2),
                "status": asset.status.value
            })

        # Summary by category
        by_category = {}
        for a in assets_data:
            cat = a["category"]
            if cat not in by_category:
                by_category[cat] = {"count": 0, "cost": 0, "book_value": 0}
            by_category[cat]["count"] += 1
            by_category[cat]["cost"] += a["purchase_price"]
            by_category[cat]["book_value"] += a["book_value"]

        return {
            "report_date": report_date.isoformat(),
            "assets": assets_data,
            "summary": {
                "total_assets": len(assets_data),
                "total_cost": sum(a["purchase_price"] for a in assets_data),
                "total_depreciation": sum(a["accumulated_depreciation"] for a in assets_data),
                "total_book_value": sum(a["book_value"] for a in assets_data)
            },
            "by_category": by_category
        }

    def get_depreciation_expense_report(self, year: int) -> Dict:
        """Get depreciation expense report for a year"""
        report_data = []

        for asset in self.assets.values():
            # Skip assets without in-service date or not yet in service
            if not asset.in_service_date or asset.in_service_date.year > year:
                continue

            calc = self.calculate_annual_depreciation(asset.asset_id, year)
            depr = calc.get("depreciation", 0)

            if depr > 0 or asset.status == AssetStatus.ACTIVE:
                report_data.append({
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "category": asset.category.value,
                    "method": asset.depreciation_method.value,
                    "annual_depreciation": round(depr, 2),
                    "expense_account": asset.depreciation_expense_account_id
                })

        # Group by account
        by_account = {}
        for item in report_data:
            acct = item["expense_account"]
            if acct not in by_account:
                by_account[acct] = 0
            by_account[acct] += item["annual_depreciation"]

        return {
            "year": year,
            "assets": report_data,
            "total_depreciation": sum(a["annual_depreciation"] for a in report_data),
            "by_expense_account": by_account
        }

    # ==================== UTILITIES ====================

    def _asset_to_dict(self, asset: FixedAsset) -> Dict:
        """Convert asset to dictionary"""
        return {
            "asset_id": asset.asset_id,
            "name": asset.name,
            "description": asset.description,
            "category": asset.category.value,
            "purchase_date": asset.purchase_date.isoformat() if asset.purchase_date else None,
            "purchase_price": asset.purchase_price or 0.0,
            "serial_number": asset.serial_number,
            "depreciation_method": asset.depreciation_method.value,
            "useful_life_years": asset.useful_life_years or 1,
            "salvage_value": asset.salvage_value or 0.0,
            "in_service_date": asset.in_service_date.isoformat() if asset.in_service_date else None,
            "cost_basis": asset.cost_basis or 0.0,
            "accumulated_depreciation": round(asset.accumulated_depreciation or 0.0, 2),
            "book_value": round(asset.book_value or 0.0, 2),
            "section_179_amount": asset.section_179_amount or 0.0,
            "bonus_depreciation_amount": asset.bonus_depreciation_amount or 0.0,
            "location": asset.location,
            "status": asset.status.value,
            "disposal_date": asset.disposal_date.isoformat() if asset.disposal_date else None,
            "disposal_amount": asset.disposal_amount or 0.0,
            "created_at": asset.created_at.isoformat()
        }

    def run_all_depreciation(self, year: int) -> Dict:
        """Run depreciation for all active assets for a given year"""
        results = []
        period_date = f"{year}-12-31"

        for asset in self.assets.values():
            if asset.status == AssetStatus.ACTIVE:
                result = self.run_depreciation(period_date, asset.asset_id)
                results.append({
                    "asset_id": asset.asset_id,
                    "asset_name": asset.name,
                    "depreciation": result.get("depreciation_amount", 0)
                })

        total_depreciation = sum(r["depreciation"] for r in results)

        return {
            "success": True,
            "year": year,
            "assets_processed": len(results),
            "total_depreciation": round(total_depreciation, 2),
            "results": results
        }

    def get_depreciation_report(self, year: int) -> Dict:
        """Get depreciation summary report for a tax year"""
        return self.get_depreciation_expense_report(year)

    def get_asset_register(self, as_of_date: str = None) -> Dict:
        """Get fixed asset register as of date"""
        return self.get_asset_register_report(as_of_date)

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        active = sum(1 for a in self.assets.values() if a.status == AssetStatus.ACTIVE)
        disposed = sum(1 for a in self.assets.values() if a.status == AssetStatus.DISPOSED)
        fully_depr = sum(1 for a in self.assets.values() if a.status == AssetStatus.FULLY_DEPRECIATED)

        total_cost = sum((a.purchase_price or 0.0) for a in self.assets.values())
        total_book = sum((a.book_value or 0.0) for a in self.assets.values() if a.status == AssetStatus.ACTIVE)

        by_category = {}
        for a in self.assets.values():
            cat = a.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "service": "GenFin Fixed Asset Manager",
            "version": "1.0.0",
            "features": [
                "Asset Register",
                "MACRS Depreciation (3, 5, 7, 10, 15, 20 year)",
                "Straight-Line Depreciation",
                "Section 179 Expensing",
                "Bonus Depreciation",
                "Depreciation Schedules",
                "Asset Disposal with Gain/Loss",
                "Asset Register Reports",
                "Depreciation Expense Reports"
            ],
            "depreciation_methods": [
                "straight_line", "macrs_3", "macrs_5", "macrs_7",
                "macrs_10", "macrs_15", "macrs_20", "section_179", "bonus_100"
            ],
            "total_assets": len(self.assets),
            "active_assets": active,
            "disposed_assets": disposed,
            "fully_depreciated": fully_depr,
            "total_cost": round(total_cost, 2),
            "total_book_value": round(total_book, 2),
            "by_category": by_category
        }


# Singleton instance
genfin_fixed_assets_service = GenFinFixedAssetsService()
