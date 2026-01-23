"""
GenFin Fixed Asset Manager Service with SQLite persistence
Handles fixed asset tracking, depreciation calculations, and disposal.
"""
import sqlite3
from datetime import datetime, date
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid


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
    Manages fixed assets for GenFin with SQLite persistence.

    Features:
    - Asset register with full tracking
    - Multiple depreciation methods (MACRS, Straight-Line, Section 179)
    - Automatic depreciation calculations
    - Disposal tracking with gain/loss
    - Asset reports
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
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Fixed assets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_fixed_assets (
                    asset_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT 'other',
                    purchase_date TEXT,
                    purchase_price REAL DEFAULT 0.0,
                    vendor_id TEXT,
                    po_number TEXT DEFAULT '',
                    serial_number TEXT DEFAULT '',
                    depreciation_method TEXT DEFAULT 'straight_line',
                    useful_life_years INTEGER DEFAULT 7,
                    salvage_value REAL DEFAULT 0.0,
                    in_service_date TEXT,
                    cost_basis REAL DEFAULT 0.0,
                    accumulated_depreciation REAL DEFAULT 0.0,
                    book_value REAL DEFAULT 0.0,
                    section_179_amount REAL DEFAULT 0.0,
                    bonus_depreciation_amount REAL DEFAULT 0.0,
                    disposal_date TEXT,
                    disposal_amount REAL DEFAULT 0.0,
                    disposal_method TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    assigned_to TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    asset_account_id TEXT DEFAULT '',
                    depreciation_expense_account_id TEXT DEFAULT '',
                    accumulated_depreciation_account_id TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Depreciation entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_depreciation_entries (
                    entry_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    period_date TEXT NOT NULL,
                    depreciation_amount REAL NOT NULL,
                    accumulated_total REAL NOT NULL,
                    book_value_after REAL NOT NULL,
                    method_used TEXT NOT NULL,
                    journal_entry_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES genfin_fixed_assets(asset_id)
                )
            """)

            conn.commit()

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
        service_date = in_service_date if in_service_date else purchase_date
        now = datetime.now().isoformat()

        # Calculate cost basis after Section 179 and bonus
        bonus_amount = purchase_price * (bonus_depreciation_percent / 100) if bonus_depreciation_percent else 0.0
        cost_basis = purchase_price - section_179_amount - bonus_amount
        book_value = cost_basis
        accumulated_depreciation = section_179_amount + bonus_amount

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_fixed_assets
                (asset_id, name, description, category, purchase_date, purchase_price,
                 vendor_id, serial_number, depreciation_method, useful_life_years,
                 salvage_value, in_service_date, cost_basis, accumulated_depreciation,
                 book_value, section_179_amount, bonus_depreciation_amount,
                 location, asset_account_id, depreciation_expense_account_id,
                 accumulated_depreciation_account_id, status, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1, ?, ?)
            """, (asset_id, name, description, category, purchase_date, purchase_price,
                  vendor_id, serial_number, depreciation_method, useful_life_years,
                  salvage_value, service_date, cost_basis, accumulated_depreciation,
                  book_value, section_179_amount, bonus_amount,
                  location, asset_account_id, depreciation_expense_account_id,
                  accumulated_depreciation_account_id, now, now))
            conn.commit()

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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT asset_id FROM genfin_fixed_assets WHERE asset_id = ? AND is_active = 1",
                         (asset_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Asset not found"}

            updates = []
            values = []

            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if updates:
                updates.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(asset_id)

                cursor.execute(f"""
                    UPDATE genfin_fixed_assets
                    SET {', '.join(updates)}
                    WHERE asset_id = ?
                """, values)
                conn.commit()

        return {"success": True, "asset_id": asset_id, "message": "Asset updated"}

    def get_asset(self, asset_id: str) -> Optional[Dict]:
        """Get a single asset"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_fixed_assets WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_asset_dict(row)

    def list_assets(
        self,
        category: str = None,
        status: str = None
    ) -> Dict:
        """List all assets"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_fixed_assets WHERE is_active = 1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY name"

            cursor.execute(query, params)
            assets_list = [self._row_to_asset_dict(row) for row in cursor.fetchall()]

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
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT asset_id FROM genfin_fixed_assets WHERE asset_id = ? AND is_active = 1",
                         (asset_id,))
            if not cursor.fetchone():
                return {"success": False, "error": "Asset not found"}

            # Check for depreciation entries
            cursor.execute("SELECT COUNT(*) FROM genfin_depreciation_entries WHERE asset_id = ?",
                         (asset_id,))
            if cursor.fetchone()[0] > 0:
                return {"success": False, "error": "Cannot delete asset with depreciation history. Dispose instead."}

            cursor.execute("UPDATE genfin_fixed_assets SET is_active = 0, updated_at = ? WHERE asset_id = ?",
                         (datetime.now().isoformat(), asset_id))
            conn.commit()

        return {"success": True, "message": "Asset deleted"}

    # ==================== DEPRECIATION ====================

    def calculate_annual_depreciation(self, asset_id: str, year: int) -> Dict:
        """Calculate depreciation for a specific year"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_fixed_assets WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Asset not found"}

            if row['status'] in ['disposed', 'fully_depreciated']:
                return {"success": False, "error": "Asset is disposed or fully depreciated"}

            # Handle missing in_service_date
            if not row['in_service_date']:
                return {"depreciation": 0, "year": year, "message": "Asset has no in-service date"}

            in_service_date = datetime.strptime(row['in_service_date'], "%Y-%m-%d").date()
            years_in_service = year - in_service_date.year + 1

            if years_in_service < 1:
                return {"depreciation": 0, "year": year, "message": "Asset not yet in service"}

            depreciation = 0.0
            cost_basis = row['cost_basis'] or 0.0
            salvage_value = row['salvage_value'] or 0.0
            useful_life = row['useful_life_years'] or 1
            book_value = row['book_value'] or 0.0
            depreciation_method = row['depreciation_method']

            if depreciation_method == 'straight_line':
                annual_depr = (cost_basis - salvage_value) / useful_life
                if years_in_service <= useful_life:
                    depreciation = annual_depr

            elif depreciation_method == 'section_179':
                if years_in_service == 1:
                    depreciation = cost_basis

            elif depreciation_method == 'bonus_100':
                if years_in_service == 1:
                    depreciation = cost_basis

            elif depreciation_method.startswith("macrs"):
                rates = MACRS_RATES.get(depreciation_method, [])
                if years_in_service <= len(rates):
                    rate = rates[years_in_service - 1]
                    depreciation = cost_basis * (rate / 100)

            # Don't exceed remaining book value
            depreciation = min(depreciation, book_value)

        return {
            "asset_id": asset_id,
            "year": year,
            "depreciation": round(depreciation, 2),
            "method": depreciation_method,
            "years_in_service": years_in_service
        }

    def run_depreciation(self, period_date: str, asset_id: str = None) -> Dict:
        """Run depreciation for period (usually monthly)"""
        per_date = datetime.strptime(period_date, "%Y-%m-%d").date()
        year = per_date.year
        now = datetime.now().isoformat()

        results = []
        total_depreciation = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            if asset_id:
                cursor.execute("SELECT * FROM genfin_fixed_assets WHERE asset_id = ? AND is_active = 1",
                             (asset_id,))
            else:
                cursor.execute("SELECT * FROM genfin_fixed_assets WHERE is_active = 1 AND status = 'active'")

            assets = cursor.fetchall()

            for row in assets:
                if row['status'] != 'active':
                    continue

                book_value = row['book_value'] or 0.0
                if book_value <= 0:
                    cursor.execute("UPDATE genfin_fixed_assets SET status = 'fully_depreciated', updated_at = ? WHERE asset_id = ?",
                                 (now, row['asset_id']))
                    continue

                # Calculate annual depreciation
                annual_calc = self.calculate_annual_depreciation(row['asset_id'], year)
                annual_depr = annual_calc.get("depreciation", 0)

                # Monthly portion
                monthly_depr = annual_depr / 12
                monthly_depr = min(monthly_depr, book_value)

                if monthly_depr > 0:
                    entry_id = str(uuid.uuid4())
                    accumulated_depr = row['accumulated_depreciation'] or 0.0
                    purchase_price = row['purchase_price'] or 0.0

                    new_accumulated = accumulated_depr + monthly_depr
                    new_book_value = purchase_price - new_accumulated

                    cursor.execute("""
                        INSERT INTO genfin_depreciation_entries
                        (entry_id, asset_id, period_date, depreciation_amount,
                         accumulated_total, book_value_after, method_used, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (entry_id, row['asset_id'], period_date, monthly_depr,
                          new_accumulated, new_book_value, row['depreciation_method'], now))

                    # Update asset
                    salvage_val = row['salvage_value'] or 0.0
                    new_status = 'fully_depreciated' if new_book_value <= salvage_val else 'active'

                    cursor.execute("""
                        UPDATE genfin_fixed_assets
                        SET accumulated_depreciation = ?, book_value = ?, status = ?, updated_at = ?
                        WHERE asset_id = ?
                    """, (new_accumulated, new_book_value, new_status, now, row['asset_id']))

                    results.append({
                        "asset_id": row['asset_id'],
                        "asset_name": row['name'],
                        "depreciation": round(monthly_depr, 2),
                        "new_book_value": round(new_book_value, 2)
                    })

                    total_depreciation += monthly_depr

            conn.commit()

        return {
            "success": True,
            "period_date": period_date,
            "assets_processed": len(results),
            "total_depreciation": round(total_depreciation, 2),
            "entries": results
        }

    def get_depreciation_schedule(self, asset_id: str) -> Dict:
        """Get full depreciation schedule for an asset"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_fixed_assets WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Asset not found"}

            if not row['in_service_date']:
                return {"success": False, "error": "Asset has no in-service date"}

            in_service_date = datetime.strptime(row['in_service_date'], "%Y-%m-%d").date()
            section_179 = row['section_179_amount'] or 0.0
            bonus_depr = row['bonus_depreciation_amount'] or 0.0
            purchase_price = row['purchase_price'] or 0.0
            salvage_value = row['salvage_value'] or 0.0

            schedule = []
            running_depr = section_179 + bonus_depr
            running_book = purchase_price - running_depr

            if section_179 > 0:
                schedule.append({
                    "year": in_service_date.year,
                    "period": "Section 179",
                    "depreciation": section_179,
                    "accumulated": running_depr,
                    "book_value": running_book
                })

            if bonus_depr > 0:
                schedule.append({
                    "year": in_service_date.year,
                    "period": "Bonus Depreciation",
                    "depreciation": bonus_depr,
                    "accumulated": running_depr,
                    "book_value": running_book
                })

            useful_life = row['useful_life_years'] or 1
            for year_offset in range(useful_life + 1):
                year = in_service_date.year + year_offset
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
            "asset_name": row['name'],
            "purchase_price": row['purchase_price'],
            "cost_basis": row['cost_basis'],
            "salvage_value": row['salvage_value'],
            "method": row['depreciation_method'],
            "useful_life": row['useful_life_years'],
            "schedule": schedule
        }

    def get_depreciation_history(self, asset_id: str = None) -> Dict:
        """Get actual depreciation entries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if asset_id:
                cursor.execute("""
                    SELECT de.*, fa.name as asset_name
                    FROM genfin_depreciation_entries de
                    JOIN genfin_fixed_assets fa ON de.asset_id = fa.asset_id
                    WHERE de.asset_id = ?
                    ORDER BY de.period_date DESC
                """, (asset_id,))
            else:
                cursor.execute("""
                    SELECT de.*, fa.name as asset_name
                    FROM genfin_depreciation_entries de
                    JOIN genfin_fixed_assets fa ON de.asset_id = fa.asset_id
                    ORDER BY de.period_date DESC
                """)

            entries = []
            for row in cursor.fetchall():
                entries.append({
                    "entry_id": row['entry_id'],
                    "asset_id": row['asset_id'],
                    "asset_name": row['asset_name'],
                    "period_date": row['period_date'],
                    "depreciation_amount": row['depreciation_amount'],
                    "accumulated_total": row['accumulated_total'],
                    "book_value_after": row['book_value_after'],
                    "method": row['method_used']
                })

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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_fixed_assets WHERE asset_id = ? AND is_active = 1",
                         (asset_id,))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Asset not found"}

            if row['status'] == 'disposed':
                return {"success": False, "error": "Asset already disposed"}

            book_value = row['book_value'] or 0.0
            gain_loss = disposal_amount - book_value

            cursor.execute("""
                UPDATE genfin_fixed_assets
                SET disposal_date = ?, disposal_amount = ?, disposal_method = ?,
                    status = 'disposed', updated_at = ?
                WHERE asset_id = ?
            """, (disposal_date, disposal_amount, disposal_method,
                  datetime.now().isoformat(), asset_id))
            conn.commit()

        return {
            "success": True,
            "asset_id": asset_id,
            "asset_name": row['name'],
            "disposal_date": disposal_date,
            "disposal_amount": disposal_amount,
            "book_value_at_disposal": round(book_value, 2),
            "gain_loss": round(gain_loss, 2),
            "gain_loss_type": "gain" if gain_loss > 0 else "loss" if gain_loss < 0 else "break_even"
        }

    # ==================== REPORTS ====================

    def get_asset_register_report(self, as_of_date: str = None) -> Dict:
        """Get asset register report"""
        report_date = as_of_date if as_of_date else date.today().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_fixed_assets
                WHERE is_active = 1 AND purchase_date IS NOT NULL AND purchase_date <= ?
                ORDER BY name
            """, (report_date,))

            assets_data = []
            for row in cursor.fetchall():
                assets_data.append({
                    "asset_id": row['asset_id'],
                    "name": row['name'],
                    "category": row['category'],
                    "purchase_date": row['purchase_date'],
                    "purchase_price": row['purchase_price'] or 0.0,
                    "depreciation_method": row['depreciation_method'],
                    "accumulated_depreciation": round(row['accumulated_depreciation'] or 0.0, 2),
                    "book_value": round(row['book_value'] or 0.0, 2),
                    "status": row['status']
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
            "report_date": report_date,
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

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM genfin_fixed_assets
                WHERE is_active = 1 AND in_service_date IS NOT NULL
            """)

            for row in cursor.fetchall():
                in_service_year = int(row['in_service_date'][:4]) if row['in_service_date'] else 9999
                if in_service_year > year:
                    continue

                calc = self.calculate_annual_depreciation(row['asset_id'], year)
                depr = calc.get("depreciation", 0)

                if depr > 0 or row['status'] == 'active':
                    report_data.append({
                        "asset_id": row['asset_id'],
                        "name": row['name'],
                        "category": row['category'],
                        "method": row['depreciation_method'],
                        "annual_depreciation": round(depr, 2),
                        "expense_account": row['depreciation_expense_account_id']
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

    def _row_to_asset_dict(self, row: sqlite3.Row) -> Dict:
        """Convert row to dictionary"""
        return {
            "asset_id": row['asset_id'],
            "name": row['name'],
            "description": row['description'] or "",
            "category": row['category'],
            "purchase_date": row['purchase_date'],
            "purchase_price": row['purchase_price'] or 0.0,
            "serial_number": row['serial_number'] or "",
            "depreciation_method": row['depreciation_method'],
            "useful_life_years": row['useful_life_years'] or 1,
            "salvage_value": row['salvage_value'] or 0.0,
            "in_service_date": row['in_service_date'],
            "cost_basis": row['cost_basis'] or 0.0,
            "accumulated_depreciation": round(row['accumulated_depreciation'] or 0.0, 2),
            "book_value": round(row['book_value'] or 0.0, 2),
            "section_179_amount": row['section_179_amount'] or 0.0,
            "bonus_depreciation_amount": row['bonus_depreciation_amount'] or 0.0,
            "location": row['location'] or "",
            "status": row['status'],
            "disposal_date": row['disposal_date'],
            "disposal_amount": row['disposal_amount'] or 0.0,
            "created_at": row['created_at']
        }

    def run_all_depreciation(self, year: int) -> Dict:
        """Run depreciation for all active assets for a given year"""
        results = []
        period_date = f"{year}-12-31"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT asset_id, name FROM genfin_fixed_assets WHERE is_active = 1 AND status = 'active'")

            for row in cursor.fetchall():
                result = self.run_depreciation(period_date, row['asset_id'])
                results.append({
                    "asset_id": row['asset_id'],
                    "asset_name": row['name'],
                    "depreciation": result.get("total_depreciation", 0)
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
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM genfin_fixed_assets WHERE is_active = 1 AND status = 'active'")
            active = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_fixed_assets WHERE is_active = 1 AND status = 'disposed'")
            disposed = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_fixed_assets WHERE is_active = 1 AND status = 'fully_depreciated'")
            fully_depr = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM genfin_fixed_assets WHERE is_active = 1")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(purchase_price), 0), COALESCE(SUM(book_value), 0) FROM genfin_fixed_assets WHERE is_active = 1")
            row = cursor.fetchone()
            total_cost = row[0]
            total_book = row[1]

            cursor.execute("SELECT category, COUNT(*) FROM genfin_fixed_assets WHERE is_active = 1 GROUP BY category")
            by_category = {r[0]: r[1] for r in cursor.fetchall()}

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
            "total_assets": total,
            "active_assets": active,
            "disposed_assets": disposed,
            "fully_depreciated": fully_depr,
            "total_cost": round(total_cost, 2),
            "total_book_value": round(total_book, 2),
            "by_category": by_category
        }


# Singleton instance
genfin_fixed_assets_service = GenFinFixedAssetsService()
