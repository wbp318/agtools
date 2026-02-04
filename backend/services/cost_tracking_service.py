"""
Cost Tracking Service for Cost-Per-Acre Analysis
Handles expense imports from QuickBooks (CSV/OCR), allocations, and reporting.

AgTools v2.7.0
"""

import csv
import io
import json
import re
import sqlite3
from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class ExpenseCategory(str, Enum):
    """Farm expense categories"""
    # Inputs
    SEED = "seed"
    FERTILIZER = "fertilizer"
    CHEMICAL = "chemical"
    FUEL = "fuel"
    # Operations
    REPAIRS = "repairs"
    LABOR = "labor"
    CUSTOM_HIRE = "custom_hire"
    # Overhead
    LAND_RENT = "land_rent"
    CROP_INSURANCE = "crop_insurance"
    INTEREST = "interest"
    UTILITIES = "utilities"
    STORAGE = "storage"
    # Other
    OTHER = "other"


class SourceType(str, Enum):
    """Expense source types"""
    CSV = "csv"
    OCR_SCAN = "ocr_scan"
    MANUAL = "manual"


class ImportStatus(str, Enum):
    """Import batch status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class CategoryGroup(str, Enum):
    """Expense category groups"""
    INPUTS = "inputs"
    OPERATIONS = "operations"
    OVERHEAD = "overhead"
    OTHER = "other"


# ============================================================================
# PYDANTIC MODELS - EXPENSES
# ============================================================================

class ExpenseCreate(BaseModel):
    """Create expense request"""
    category: ExpenseCategory
    vendor: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    amount: float = Field(..., gt=0)
    expense_date: date
    tax_year: int = Field(..., ge=2000, le=2100)
    quickbooks_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    """Update expense request"""
    category: Optional[ExpenseCategory] = None
    vendor: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    expense_date: Optional[date] = None
    tax_year: Optional[int] = Field(None, ge=2000, le=2100)
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    """Expense response"""
    id: int
    category: str
    vendor: Optional[str]
    description: Optional[str]
    amount: float
    expense_date: date
    tax_year: int
    source_type: str
    source_reference: Optional[str]
    import_batch_id: Optional[int]
    quickbooks_id: Optional[str]
    ocr_confidence: Optional[float]
    ocr_needs_review: bool
    notes: Optional[str]
    created_by_user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Computed
    allocated_percent: float = 0.0
    unallocated_percent: float = 100.0


class ExpenseListResponse(BaseModel):
    """Response for expense list endpoint"""
    count: int
    expenses: List[ExpenseResponse]


# ============================================================================
# PYDANTIC MODELS - ALLOCATIONS
# ============================================================================

class AllocationCreate(BaseModel):
    """Create allocation request"""
    field_id: int
    crop_year: int = Field(..., ge=2000, le=2100)
    allocation_percent: float = Field(..., ge=0, le=100)
    notes: Optional[str] = None


class AllocationResponse(BaseModel):
    """Allocation response"""
    id: int
    expense_id: int
    field_id: int
    field_name: str
    crop_year: int
    allocation_percent: float
    allocated_amount: float
    notes: Optional[str]
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime


class ExpenseWithAllocations(BaseModel):
    """Expense with its allocations"""
    expense: ExpenseResponse
    allocations: List[AllocationResponse]


# ============================================================================
# PYDANTIC MODELS - IMPORTS
# ============================================================================

class ColumnMapping(BaseModel):
    """Column mapping configuration"""
    amount: str  # Required
    date: str  # Required
    vendor: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    reference: Optional[str] = None  # For QuickBooks Num field


class ImportPreview(BaseModel):
    """Preview of CSV import"""
    headers: List[str]
    sample_rows: List[Dict[str, str]]
    suggested_mapping: Optional[ColumnMapping] = None
    row_count: int


class ImportResult(BaseModel):
    """Result of import operation"""
    batch_id: int
    total_records: int
    successful: int
    failed: int
    errors: List[str]
    duplicates_skipped: int


class ImportBatchResponse(BaseModel):
    """Import batch response"""
    id: int
    import_date: datetime
    source_file: Optional[str]
    source_type: str
    total_records: int
    successful: int
    failed: int
    status: str
    error_message: Optional[str]
    user_id: int


class SavedMappingResponse(BaseModel):
    """Saved column mapping"""
    id: int
    mapping_name: str
    source_type: Optional[str]
    column_config: Dict[str, str]
    is_default: bool
    created_at: datetime


class OCRScanResult(BaseModel):
    """Result of OCR scan processing"""
    expenses: List[ExpenseResponse]
    warnings: List[str]
    batch_id: Optional[int] = None
    needs_review_count: int = 0


# ============================================================================
# PYDANTIC MODELS - REPORTS
# ============================================================================

class CostPerAcreItem(BaseModel):
    """Cost per acre for a single field"""
    field_id: int
    field_name: str
    farm_name: Optional[str]
    crop_year: int
    crop_type: Optional[str]
    acreage: float
    total_cost: float
    cost_per_acre: float
    by_category: Dict[str, float]


class CostPerAcreReport(BaseModel):
    """Cost per acre report"""
    crop_year: int
    total_fields: int
    total_acreage: float
    total_cost: float
    average_cost_per_acre: float
    fields: List[CostPerAcreItem]
    by_category_totals: Dict[str, float]


class CategoryBreakdown(BaseModel):
    """Category breakdown"""
    category: str
    category_group: str
    total_amount: float
    percent_of_total: float
    expense_count: int


class CropCostSummary(BaseModel):
    """Cost summary by crop"""
    crop_type: str
    total_acres: float
    total_cost: float
    cost_per_acre: float
    field_count: int


# ============================================================================
# COST TRACKING SERVICE
# ============================================================================

class CostTrackingService:
    """
    Cost tracking service handling:
    - CSV import with column mapping
    - Expense CRUD operations
    - Allocation management
    - Cost-per-acre reporting
    """

    # Category auto-detection keywords
    CATEGORY_KEYWORDS = {
        ExpenseCategory.SEED: ["seed", "pioneer", "dekalb", "asgrow", "channel", "beck's"],
        ExpenseCategory.FERTILIZER: ["fertilizer", "fert", "urea", "uan", "dap", "map", "potash", "anhydrous", "nitrogen", "phosphate"],
        ExpenseCategory.CHEMICAL: ["chemical", "herbicide", "insecticide", "fungicide", "roundup", "liberty", "dicamba", "atrazine", "adjuvant"],
        ExpenseCategory.FUEL: ["fuel", "diesel", "gasoline", "gas", "propane", "petro"],
        ExpenseCategory.REPAIRS: ["repair", "parts", "maintenance", "fix", "service"],
        ExpenseCategory.LABOR: ["labor", "payroll", "wages", "salary", "employee"],
        ExpenseCategory.CUSTOM_HIRE: ["custom", "hire", "aerial", "flying", "trucking", "hauling", "combining"],
        ExpenseCategory.LAND_RENT: ["rent", "lease", "cash rent", "land"],
        ExpenseCategory.CROP_INSURANCE: ["insurance", "crop ins", "premium"],
        ExpenseCategory.INTEREST: ["interest", "loan", "operating"],
        ExpenseCategory.UTILITIES: ["electric", "utility", "power", "water"],
        ExpenseCategory.STORAGE: ["storage", "drying", "elevator", "grain bin"],
    }

    def __init__(self, db_path: str = "agtools.db"):
        """Initialize cost tracking service."""
        self.db_path = db_path
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        # Read and execute migration file
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "database", "migrations", "006_cost_tracking.sql"
        )
        if os.path.exists(migration_path):
            with open(migration_path, "r") as f:
                migration_sql = f.read()
            conn = self._get_connection()
            try:
                conn.executescript(migration_sql)
                conn.commit()
            except sqlite3.Error:
                # Tables may already exist
                pass
            finally:
                conn.close()

    # ========================================================================
    # CSV IMPORT FUNCTIONS
    # ========================================================================

    def preview_csv(self, csv_content: str) -> ImportPreview:
        """
        Preview CSV content and suggest column mappings.

        Args:
            csv_content: Raw CSV string

        Returns:
            ImportPreview with headers, sample rows, and suggested mapping
        """
        reader = csv.DictReader(io.StringIO(csv_content))
        headers = reader.fieldnames or []

        sample_rows = []
        row_count = 0
        for i, row in enumerate(reader):
            row_count += 1
            if i < 10:  # First 10 rows for preview
                sample_rows.append(dict(row))

        # Try to auto-detect column mapping
        suggested = self._suggest_column_mapping(headers)

        return ImportPreview(
            headers=headers,
            sample_rows=sample_rows,
            suggested_mapping=suggested,
            row_count=row_count
        )

    def _suggest_column_mapping(self, headers: List[str]) -> Optional[ColumnMapping]:
        """Auto-detect column mapping from headers."""
        lower_headers = {h.lower(): h for h in headers}

        mapping = {}

        # Amount column patterns
        amount_patterns = ["amount", "debit", "total", "cost", "price", "sum"]
        for pattern in amount_patterns:
            for lh, h in lower_headers.items():
                if pattern in lh:
                    mapping["amount"] = h
                    break
            if "amount" in mapping:
                break

        # Date column patterns
        date_patterns = ["date", "trans date", "transaction date", "posted"]
        for pattern in date_patterns:
            for lh, h in lower_headers.items():
                if pattern in lh:
                    mapping["date"] = h
                    break
            if "date" in mapping:
                break

        # Vendor/Name column
        vendor_patterns = ["vendor", "name", "payee", "supplier", "company"]
        for pattern in vendor_patterns:
            for lh, h in lower_headers.items():
                if pattern in lh:
                    mapping["vendor"] = h
                    break
            if "vendor" in mapping:
                break

        # Description/Memo column
        desc_patterns = ["memo", "description", "desc", "note", "detail"]
        for pattern in desc_patterns:
            for lh, h in lower_headers.items():
                if pattern in lh:
                    mapping["description"] = h
                    break
            if "description" in mapping:
                break

        # Category/Account column
        cat_patterns = ["account", "category", "class", "type"]
        for pattern in cat_patterns:
            for lh, h in lower_headers.items():
                if pattern in lh:
                    mapping["category"] = h
                    break
            if "category" in mapping:
                break

        # Reference/Num column (for deduplication)
        ref_patterns = ["num", "ref", "reference", "check", "invoice"]
        for pattern in ref_patterns:
            for lh, h in lower_headers.items():
                if pattern in lh:
                    mapping["reference"] = h
                    break
            if "reference" in mapping:
                break

        # Must have at least amount and date
        if "amount" in mapping and "date" in mapping:
            return ColumnMapping(**mapping)
        return None

    def import_csv(
        self,
        csv_content: str,
        mapping: ColumnMapping,
        user_id: int,
        source_file: str = "upload.csv",
        default_tax_year: Optional[int] = None
    ) -> ImportResult:
        """
        Import expenses from CSV using provided column mapping.

        Args:
            csv_content: Raw CSV string
            mapping: Column mapping configuration
            user_id: User performing import
            source_file: Original filename
            default_tax_year: Tax year if not derivable from date

        Returns:
            ImportResult with counts and errors
        """
        if default_tax_year is None:
            default_tax_year = datetime.now(timezone.utc).year

        conn = self._get_connection()
        cursor = conn.cursor()

        # Create import batch
        cursor.execute("""
            INSERT INTO import_batches (source_file, source_type, user_id, status)
            VALUES (?, ?, ?, ?)
        """, (source_file, SourceType.CSV.value, user_id, ImportStatus.PROCESSING.value))
        batch_id = cursor.lastrowid

        reader = csv.DictReader(io.StringIO(csv_content))

        total = 0
        successful = 0
        failed = 0
        duplicates = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            total += 1
            try:
                # Extract and validate amount
                amount_str = row.get(mapping.amount, "").strip()
                amount = self._parse_amount(amount_str)
                if amount is None or amount <= 0:
                    errors.append(f"Row {row_num}: Invalid amount '{amount_str}'")
                    failed += 1
                    continue

                # Extract and validate date
                date_str = row.get(mapping.date, "").strip()
                expense_date = self._parse_date(date_str)
                if expense_date is None:
                    errors.append(f"Row {row_num}: Invalid date '{date_str}'")
                    failed += 1
                    continue

                # Optional fields
                vendor = row.get(mapping.vendor, "").strip() if mapping.vendor else None
                description = row.get(mapping.description, "").strip() if mapping.description else None
                category_hint = row.get(mapping.category, "").strip() if mapping.category else None
                reference = row.get(mapping.reference, "").strip() if mapping.reference else None

                # Auto-detect category
                category = self._detect_category(vendor, description, category_hint)

                # Derive tax year from date
                tax_year = expense_date.year if expense_date else default_tax_year

                # Check for duplicates by reference + date + amount
                if reference:
                    cursor.execute("""
                        SELECT id FROM expenses
                        WHERE quickbooks_id = ? AND expense_date = ? AND amount = ?
                        AND is_active = 1
                    """, (reference, expense_date.isoformat(), amount))
                    if cursor.fetchone():
                        duplicates += 1
                        continue

                # Insert expense
                cursor.execute("""
                    INSERT INTO expenses (
                        category, vendor, description, amount, expense_date, tax_year,
                        source_type, source_reference, import_batch_id, quickbooks_id,
                        created_by_user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    category.value,
                    vendor or None,
                    description or None,
                    amount,
                    expense_date.isoformat(),
                    tax_year,
                    SourceType.CSV.value,
                    source_file,
                    batch_id,
                    reference or None,
                    user_id
                ))
                successful += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                failed += 1

        # Update batch record
        status = ImportStatus.COMPLETED.value if failed == 0 else ImportStatus.COMPLETED.value
        error_msg = "; ".join(errors[:10]) if errors else None  # First 10 errors

        cursor.execute("""
            UPDATE import_batches
            SET total_records = ?, successful = ?, failed = ?, status = ?, error_message = ?
            WHERE id = ?
        """, (total, successful, failed, status, error_msg, batch_id))

        conn.commit()
        conn.close()

        return ImportResult(
            batch_id=batch_id,
            total_records=total,
            successful=successful,
            failed=failed,
            errors=errors[:20],  # Return first 20 errors
            duplicates_skipped=duplicates
        )

    def _parse_amount(self, value: str) -> Optional[float]:
        """Parse amount from various formats."""
        if not value:
            return None
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,\s]', '', value)
        # Handle parentheses for negative (common in accounting)
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        try:
            amount = float(cleaned)
            return abs(amount)  # Expenses are positive
        except ValueError:
            return None

    def _parse_date(self, value: str) -> Optional[date]:
        """Parse date from various formats."""
        if not value:
            return None

        # Common date formats
        formats = [
            "%m/%d/%Y",  # 12/31/2024
            "%Y-%m-%d",  # 2024-12-31
            "%m-%d-%Y",  # 12-31-2024
            "%d/%m/%Y",  # 31/12/2024 (European)
            "%m/%d/%y",  # 12/31/24
            "%Y/%m/%d",  # 2024/12/31
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _detect_category(
        self,
        vendor: Optional[str],
        description: Optional[str],
        category_hint: Optional[str]
    ) -> ExpenseCategory:
        """Auto-detect expense category from text."""
        text = " ".join(filter(None, [vendor, description, category_hint])).lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return category

        return ExpenseCategory.OTHER

    # ========================================================================
    # COLUMN MAPPING MANAGEMENT
    # ========================================================================

    def save_column_mapping(
        self,
        user_id: int,
        mapping_name: str,
        column_config: ColumnMapping,
        source_type: Optional[str] = None,
        is_default: bool = False
    ) -> int:
        """Save a column mapping for reuse."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # If setting as default, unset other defaults for this user
        if is_default:
            cursor.execute("""
                UPDATE column_mappings SET is_default = 0 WHERE user_id = ?
            """, (user_id,))

        cursor.execute("""
            INSERT INTO column_mappings (user_id, mapping_name, source_type, column_config, is_default)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, mapping_name, source_type, column_config.model_dump_json(), is_default))

        mapping_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return mapping_id

    def get_user_mappings(self, user_id: int) -> List[SavedMappingResponse]:
        """Get all saved column mappings for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, mapping_name, source_type, column_config, is_default, created_at
            FROM column_mappings
            WHERE user_id = ?
            ORDER BY is_default DESC, created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            SavedMappingResponse(
                id=row["id"],
                mapping_name=row["mapping_name"],
                source_type=row["source_type"],
                column_config=json.loads(row["column_config"]),
                is_default=bool(row["is_default"]),
                created_at=datetime.fromisoformat(row["created_at"])
            )
            for row in rows
        ]

    def delete_column_mapping(self, mapping_id: int, user_id: int) -> bool:
        """Delete a saved column mapping."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM column_mappings WHERE id = ? AND user_id = ?
        """, (mapping_id, user_id))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    # ========================================================================
    # EXPENSE CRUD
    # ========================================================================

    def create_expense(
        self,
        expense_data: ExpenseCreate,
        user_id: int
    ) -> Tuple[Optional[ExpenseResponse], Optional[str]]:
        """Create a manual expense entry."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO expenses (
                    category, vendor, description, amount, expense_date, tax_year,
                    source_type, quickbooks_id, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                expense_data.category.value,
                expense_data.vendor,
                expense_data.description,
                expense_data.amount,
                expense_data.expense_date.isoformat(),
                expense_data.tax_year,
                SourceType.MANUAL.value,
                expense_data.quickbooks_id,
                expense_data.notes,
                user_id
            ))

            expense_id = cursor.lastrowid
            conn.commit()

            # Fetch and return the created expense
            expense = self.get_expense(expense_id)
            conn.close()
            return expense, None

        except sqlite3.Error as e:
            conn.close()
            return None, str(e)

    def get_expense(self, expense_id: int) -> Optional[ExpenseResponse]:
        """Get a single expense by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.*,
                   COALESCE(SUM(ea.allocation_percent), 0) as allocated_percent
            FROM expenses e
            LEFT JOIN expense_allocations ea ON e.id = ea.expense_id
            WHERE e.id = ? AND e.is_active = 1
            GROUP BY e.id
        """, (expense_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_expense_response(row)

    def get_expense_with_allocations(self, expense_id: int) -> Optional[ExpenseWithAllocations]:
        """Get expense with its allocations."""
        expense = self.get_expense(expense_id)
        if not expense:
            return None

        allocations = self.get_allocations(expense_id)

        return ExpenseWithAllocations(
            expense=expense,
            allocations=allocations
        )

    def list_expenses(
        self,
        user_id: int,
        tax_year: Optional[int] = None,
        category: Optional[ExpenseCategory] = None,
        vendor: Optional[str] = None,
        unallocated_only: bool = False,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> ExpenseListResponse:
        """List expenses with filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT e.*,
                   COALESCE(SUM(ea.allocation_percent), 0) as allocated_percent
            FROM expenses e
            LEFT JOIN expense_allocations ea ON e.id = ea.expense_id
            WHERE e.is_active = 1
        """
        params = []

        if tax_year:
            query += " AND e.tax_year = ?"
            params.append(tax_year)

        if category:
            query += " AND e.category = ?"
            params.append(category.value)

        if vendor:
            query += " AND e.vendor LIKE ?"
            params.append(f"%{vendor}%")

        if start_date:
            query += " AND e.expense_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND e.expense_date <= ?"
            params.append(end_date.isoformat())

        query += " GROUP BY e.id"

        if unallocated_only:
            query += " HAVING allocated_percent < 100"

        query += " ORDER BY e.expense_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Get total count
        count_query = """
            SELECT COUNT(DISTINCT e.id)
            FROM expenses e
            LEFT JOIN expense_allocations ea ON e.id = ea.expense_id
            WHERE e.is_active = 1
        """
        count_params = []

        if tax_year:
            count_query += " AND e.tax_year = ?"
            count_params.append(tax_year)
        if category:
            count_query += " AND e.category = ?"
            count_params.append(category.value)
        if vendor:
            count_query += " AND e.vendor LIKE ?"
            count_params.append(f"%{vendor}%")
        if start_date:
            count_query += " AND e.expense_date >= ?"
            count_params.append(start_date.isoformat())
        if end_date:
            count_query += " AND e.expense_date <= ?"
            count_params.append(end_date.isoformat())

        if unallocated_only:
            # Need subquery for unallocated count
            count_query = f"""
                SELECT COUNT(*) FROM (
                    SELECT e.id, COALESCE(SUM(ea.allocation_percent), 0) as alloc
                    FROM expenses e
                    LEFT JOIN expense_allocations ea ON e.id = ea.expense_id
                    WHERE e.is_active = 1
                    {"AND e.tax_year = ?" if tax_year else ""}
                    {"AND e.category = ?" if category else ""}
                    GROUP BY e.id
                    HAVING alloc < 100
                )
            """

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]

        conn.close()

        expenses = [self._row_to_expense_response(row) for row in rows]
        return ExpenseListResponse(count=total_count, expenses=expenses)

    def update_expense(
        self,
        expense_id: int,
        expense_data: ExpenseUpdate,
        user_id: int
    ) -> Tuple[Optional[ExpenseResponse], Optional[str]]:
        """Update an expense."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        params = []

        if expense_data.category is not None:
            updates.append("category = ?")
            params.append(expense_data.category.value)
        if expense_data.vendor is not None:
            updates.append("vendor = ?")
            params.append(expense_data.vendor)
        if expense_data.description is not None:
            updates.append("description = ?")
            params.append(expense_data.description)
        if expense_data.amount is not None:
            updates.append("amount = ?")
            params.append(expense_data.amount)
        if expense_data.expense_date is not None:
            updates.append("expense_date = ?")
            params.append(expense_data.expense_date.isoformat())
        if expense_data.tax_year is not None:
            updates.append("tax_year = ?")
            params.append(expense_data.tax_year)
        if expense_data.notes is not None:
            updates.append("notes = ?")
            params.append(expense_data.notes)

        if not updates:
            conn.close()
            return None, "No fields to update"

        params.append(expense_id)

        cursor.execute(f"""
            UPDATE expenses SET {", ".join(updates)}
            WHERE id = ? AND is_active = 1
        """, params)

        if cursor.rowcount == 0:
            conn.close()
            return None, "Expense not found"

        conn.commit()
        expense = self.get_expense(expense_id)
        conn.close()
        return expense, None

    def delete_expense(self, expense_id: int, user_id: int) -> bool:
        """Soft delete an expense."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE expenses SET is_active = 0 WHERE id = ?
        """, (expense_id,))

        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def _row_to_expense_response(self, row: sqlite3.Row) -> ExpenseResponse:
        """Convert database row to ExpenseResponse."""
        allocated = row["allocated_percent"] if "allocated_percent" in row.keys() else 0
        return ExpenseResponse(
            id=row["id"],
            category=row["category"],
            vendor=row["vendor"],
            description=row["description"],
            amount=float(row["amount"]),
            expense_date=date.fromisoformat(row["expense_date"]),
            tax_year=row["tax_year"],
            source_type=row["source_type"],
            source_reference=row["source_reference"],
            import_batch_id=row["import_batch_id"],
            quickbooks_id=row["quickbooks_id"],
            ocr_confidence=float(row["ocr_confidence"]) if row["ocr_confidence"] else None,
            ocr_needs_review=bool(row["ocr_needs_review"]),
            notes=row["notes"],
            created_by_user_id=row["created_by_user_id"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            allocated_percent=float(allocated),
            unallocated_percent=100.0 - float(allocated)
        )

    # ========================================================================
    # ALLOCATIONS
    # ========================================================================

    def set_allocations(
        self,
        expense_id: int,
        allocations: List[AllocationCreate],
        user_id: int
    ) -> Tuple[Optional[List[AllocationResponse]], Optional[str]]:
        """
        Set allocations for an expense (replaces existing).

        Args:
            expense_id: Expense to allocate
            allocations: List of field allocations
            user_id: User performing allocation

        Returns:
            Tuple of (allocations, error)
        """
        # Validate total percent
        total_percent = sum(a.allocation_percent for a in allocations)
        if total_percent > 100.01:  # Allow small floating point variance
            return None, f"Total allocation ({total_percent:.1f}%) exceeds 100%"

        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify expense exists
        cursor.execute("SELECT amount FROM expenses WHERE id = ? AND is_active = 1", (expense_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None, "Expense not found"

        expense_amount = float(row["amount"])

        # Delete existing allocations
        cursor.execute("DELETE FROM expense_allocations WHERE expense_id = ?", (expense_id,))

        # Insert new allocations
        for alloc in allocations:
            allocated_amount = expense_amount * (alloc.allocation_percent / 100)
            cursor.execute("""
                INSERT INTO expense_allocations (
                    expense_id, field_id, crop_year, allocation_percent,
                    allocated_amount, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                expense_id,
                alloc.field_id,
                alloc.crop_year,
                alloc.allocation_percent,
                allocated_amount,
                alloc.notes,
                user_id
            ))

        conn.commit()

        # Fetch and return allocations
        result = self.get_allocations(expense_id)
        conn.close()
        return result, None

    def get_allocations(self, expense_id: int) -> List[AllocationResponse]:
        """Get all allocations for an expense."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ea.*, f.name as field_name
            FROM expense_allocations ea
            JOIN fields f ON ea.field_id = f.id
            WHERE ea.expense_id = ?
            ORDER BY ea.allocation_percent DESC
        """, (expense_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            AllocationResponse(
                id=row["id"],
                expense_id=row["expense_id"],
                field_id=row["field_id"],
                field_name=row["field_name"],
                crop_year=row["crop_year"],
                allocation_percent=float(row["allocation_percent"]),
                allocated_amount=float(row["allocated_amount"]),
                notes=row["notes"],
                created_by_user_id=row["created_by_user_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
            for row in rows
        ]

    def suggest_allocation_by_acreage(
        self,
        field_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Suggest allocation percentages based on field acreage.

        Args:
            field_ids: Fields to include in allocation

        Returns:
            List of {field_id, field_name, acreage, suggested_percent}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        placeholders = ",".join("?" * len(field_ids))
        cursor.execute(f"""
            SELECT id, name, acreage FROM fields
            WHERE id IN ({placeholders}) AND is_active = 1
        """, field_ids)

        rows = cursor.fetchall()
        conn.close()

        total_acreage = sum(row["acreage"] for row in rows)
        if total_acreage == 0:
            return []

        return [
            {
                "field_id": row["id"],
                "field_name": row["name"],
                "acreage": float(row["acreage"]),
                "suggested_percent": round((row["acreage"] / total_acreage) * 100, 2)
            }
            for row in rows
        ]

    # ========================================================================
    # COST-PER-ACRE REPORTS
    # ========================================================================

    def get_cost_per_acre_report(
        self,
        crop_year: int,
        field_ids: Optional[List[int]] = None
    ) -> CostPerAcreReport:
        """
        Generate cost-per-acre report for a crop year.

        Args:
            crop_year: Year to report on
            field_ids: Optional filter to specific fields

        Returns:
            CostPerAcreReport
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT
                ea.field_id,
                f.name as field_name,
                f.farm_name,
                f.acreage,
                f.current_crop,
                e.category,
                SUM(ea.allocated_amount) as category_cost
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            JOIN fields f ON ea.field_id = f.id
            WHERE ea.crop_year = ? AND e.is_active = 1 AND f.is_active = 1
        """
        params = [crop_year]

        if field_ids:
            placeholders = ",".join("?" * len(field_ids))
            query += f" AND ea.field_id IN ({placeholders})"
            params.extend(field_ids)

        query += " GROUP BY ea.field_id, e.category ORDER BY f.name, e.category"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Aggregate by field
        fields_data: Dict[int, Dict] = {}
        by_category_totals: Dict[str, float] = {}

        for row in rows:
            field_id = row["field_id"]
            category = row["category"]
            cost = float(row["category_cost"])

            if field_id not in fields_data:
                fields_data[field_id] = {
                    "field_id": field_id,
                    "field_name": row["field_name"],
                    "farm_name": row["farm_name"],
                    "acreage": float(row["acreage"]),
                    "crop_type": row["current_crop"],
                    "total_cost": 0,
                    "by_category": {}
                }

            fields_data[field_id]["total_cost"] += cost
            fields_data[field_id]["by_category"][category] = cost

            by_category_totals[category] = by_category_totals.get(category, 0) + cost

        # Build field items
        fields = []
        total_acreage = 0
        total_cost = 0

        for fd in fields_data.values():
            cost_per_acre = fd["total_cost"] / fd["acreage"] if fd["acreage"] > 0 else 0
            fields.append(CostPerAcreItem(
                field_id=fd["field_id"],
                field_name=fd["field_name"],
                farm_name=fd["farm_name"],
                crop_year=crop_year,
                crop_type=fd["crop_type"],
                acreage=fd["acreage"],
                total_cost=fd["total_cost"],
                cost_per_acre=round(cost_per_acre, 2),
                by_category=fd["by_category"]
            ))
            total_acreage += fd["acreage"]
            total_cost += fd["total_cost"]

        avg_cost_per_acre = total_cost / total_acreage if total_acreage > 0 else 0

        return CostPerAcreReport(
            crop_year=crop_year,
            total_fields=len(fields),
            total_acreage=round(total_acreage, 2),
            total_cost=round(total_cost, 2),
            average_cost_per_acre=round(avg_cost_per_acre, 2),
            fields=sorted(fields, key=lambda f: f.cost_per_acre, reverse=True),
            by_category_totals=by_category_totals
        )

    def get_category_breakdown(
        self,
        crop_year: int,
        field_id: Optional[int] = None
    ) -> List[CategoryBreakdown]:
        """Get expense breakdown by category."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                e.category,
                ec.category_group,
                SUM(ea.allocated_amount) as total_amount,
                COUNT(DISTINCT e.id) as expense_count
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            LEFT JOIN expense_categories ec ON e.category = ec.name
            WHERE ea.crop_year = ? AND e.is_active = 1
        """
        params = [crop_year]

        if field_id:
            query += " AND ea.field_id = ?"
            params.append(field_id)

        query += " GROUP BY e.category ORDER BY total_amount DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        total = sum(float(row["total_amount"]) for row in rows)

        return [
            CategoryBreakdown(
                category=row["category"],
                category_group=row["category_group"] or "other",
                total_amount=float(row["total_amount"]),
                percent_of_total=round((float(row["total_amount"]) / total * 100) if total > 0 else 0, 1),
                expense_count=row["expense_count"]
            )
            for row in rows
        ]

    def get_cost_by_crop(self, crop_year: int) -> List[CropCostSummary]:
        """Get cost summary grouped by crop type."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                f.current_crop,
                SUM(f.acreage) as total_acres,
                SUM(ea.allocated_amount) as total_cost,
                COUNT(DISTINCT f.id) as field_count
            FROM expense_allocations ea
            JOIN expenses e ON ea.expense_id = e.id
            JOIN fields f ON ea.field_id = f.id
            WHERE ea.crop_year = ? AND e.is_active = 1 AND f.is_active = 1
            GROUP BY f.current_crop
            ORDER BY total_cost DESC
        """, (crop_year,))

        rows = cursor.fetchall()
        conn.close()

        return [
            CropCostSummary(
                crop_type=row["current_crop"] or "Unknown",
                total_acres=float(row["total_acres"]),
                total_cost=float(row["total_cost"]),
                cost_per_acre=round(float(row["total_cost"]) / float(row["total_acres"]), 2) if row["total_acres"] > 0 else 0,
                field_count=row["field_count"]
            )
            for row in rows
        ]

    def get_year_comparison(
        self,
        years: List[int],
        field_id: Optional[int] = None
    ) -> Dict[int, Dict[str, float]]:
        """Compare costs across multiple years."""
        conn = self._get_connection()
        cursor = conn.cursor()

        results = {}
        for year in years:
            query = """
                SELECT
                    SUM(ea.allocated_amount) as total_cost,
                    SUM(f.acreage) as total_acres
                FROM expense_allocations ea
                JOIN expenses e ON ea.expense_id = e.id
                JOIN fields f ON ea.field_id = f.id
                WHERE ea.crop_year = ? AND e.is_active = 1
            """
            params = [year]

            if field_id:
                query += " AND ea.field_id = ?"
                params.append(field_id)

            cursor.execute(query, params)
            row = cursor.fetchone()

            total_cost = float(row["total_cost"]) if row["total_cost"] else 0
            total_acres = float(row["total_acres"]) if row["total_acres"] else 0
            cost_per_acre = total_cost / total_acres if total_acres > 0 else 0

            results[year] = {
                "total_cost": round(total_cost, 2),
                "total_acres": round(total_acres, 2),
                "cost_per_acre": round(cost_per_acre, 2)
            }

        conn.close()
        return results

    # ========================================================================
    # IMPORT BATCH MANAGEMENT
    # ========================================================================

    def get_import_batches(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[ImportBatchResponse]:
        """Get recent import batches for a user."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM import_batches
            WHERE user_id = ?
            ORDER BY import_date DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [
            ImportBatchResponse(
                id=row["id"],
                import_date=datetime.fromisoformat(row["import_date"]),
                source_file=row["source_file"],
                source_type=row["source_type"],
                total_records=row["total_records"],
                successful=row["successful"],
                failed=row["failed"],
                status=row["status"],
                error_message=row["error_message"],
                user_id=row["user_id"]
            )
            for row in rows
        ]

    def rollback_import(self, batch_id: int, user_id: int) -> Tuple[int, Optional[str]]:
        """
        Rollback (delete) all expenses from an import batch.

        Args:
            batch_id: Import batch to rollback
            user_id: User performing rollback

        Returns:
            Tuple of (deleted_count, error)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify batch belongs to user
        cursor.execute("""
            SELECT id FROM import_batches WHERE id = ? AND user_id = ?
        """, (batch_id, user_id))

        if not cursor.fetchone():
            conn.close()
            return 0, "Import batch not found or not authorized"

        # Delete allocations for expenses in this batch
        cursor.execute("""
            DELETE FROM expense_allocations
            WHERE expense_id IN (SELECT id FROM expenses WHERE import_batch_id = ?)
        """, (batch_id,))

        # Delete expenses
        cursor.execute("""
            DELETE FROM expenses WHERE import_batch_id = ?
        """, (batch_id,))
        deleted = cursor.rowcount

        # Update batch status
        cursor.execute("""
            UPDATE import_batches SET status = ? WHERE id = ?
        """, (ImportStatus.ROLLED_BACK.value, batch_id))

        conn.commit()
        conn.close()

        return deleted, None


    # ========================================================================
    # OCR IMPORT
    # ========================================================================

    def process_ocr_image(
        self,
        image_data: bytes,
        user_id: int,
        source_file: str = "scan.jpg",
        default_tax_year: Optional[int] = None
    ) -> Tuple[List[ExpenseResponse], List[str]]:
        """
        Process a scanned image/PDF and extract expenses using OCR.

        Args:
            image_data: Raw image bytes (JPG, PNG) or PDF
            user_id: User performing import
            source_file: Original filename
            default_tax_year: Tax year if not derivable

        Returns:
            Tuple of (extracted_expenses, warnings)
        """
        if default_tax_year is None:
            default_tax_year = datetime.now(timezone.utc).year

        warnings = []

        # Try to import OCR libraries
        try:
            from PIL import Image
            import pytesseract
        except ImportError as e:
            warnings.append(f"OCR libraries not installed: {e}. Install with: pip install pytesseract Pillow")
            return [], warnings

        # Check if it's a PDF
        is_pdf = source_file.lower().endswith('.pdf') or image_data[:4] == b'%PDF'

        try:
            if is_pdf:
                # Try to convert PDF to images
                try:
                    from pdf2image import convert_from_bytes
                    images = convert_from_bytes(image_data)
                    text_parts = []
                    for img in images:
                        text_parts.append(pytesseract.image_to_string(img))
                    raw_text = "\n".join(text_parts)
                except ImportError:
                    warnings.append("PDF support requires pdf2image. Install with: pip install pdf2image")
                    return [], warnings
            else:
                # Process image directly
                image = Image.open(io.BytesIO(image_data))
                raw_text = pytesseract.image_to_string(image)

        except Exception as e:
            warnings.append(f"OCR processing failed: {str(e)}")
            return [], warnings

        # Parse extracted text
        extracted = self._parse_ocr_text(raw_text, default_tax_year)

        if not extracted:
            warnings.append("No expense data could be extracted from the image")
            return [], warnings

        # Create import batch
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO import_batches (source_file, source_type, user_id, status)
            VALUES (?, ?, ?, ?)
        """, (source_file, SourceType.OCR_SCAN.value, user_id, ImportStatus.PROCESSING.value))
        batch_id = cursor.lastrowid

        # Insert extracted expenses
        created_expenses = []
        for item in extracted:
            needs_review = item.get("confidence", 100) < 80

            cursor.execute("""
                INSERT INTO expenses (
                    category, vendor, description, amount, expense_date, tax_year,
                    source_type, source_reference, import_batch_id,
                    ocr_confidence, ocr_needs_review, ocr_raw_text,
                    created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["category"].value,
                item.get("vendor"),
                item.get("description"),
                item["amount"],
                item["date"].isoformat(),
                item["date"].year,
                SourceType.OCR_SCAN.value,
                source_file,
                batch_id,
                item.get("confidence", 50),
                needs_review,
                raw_text[:2000],  # Store first 2000 chars of raw text
                user_id
            ))

            expense_id = cursor.lastrowid
            expense = self.get_expense(expense_id)
            if expense:
                created_expenses.append(expense)

            if needs_review:
                warnings.append(f"Expense #{expense_id} has low confidence ({item.get('confidence', 50):.0f}%) - please verify")

        # Update batch
        cursor.execute("""
            UPDATE import_batches
            SET total_records = ?, successful = ?, status = ?
            WHERE id = ?
        """, (len(extracted), len(created_expenses), ImportStatus.COMPLETED.value, batch_id))

        conn.commit()
        conn.close()

        return created_expenses, warnings

    def _parse_ocr_text(
        self,
        text: str,
        default_year: int
    ) -> List[Dict[str, Any]]:
        """
        Parse OCR text to extract expense data.

        Returns list of dicts with: amount, date, vendor, description, category, confidence
        """
        expenses = []

        # Currency patterns
        amount_pattern = r'\$?\s*([\d,]+\.?\d{0,2})'

        # Date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})',
        ]

        # Split into lines
        lines = text.split('\n')

        # Look for expense-like patterns
        current_vendor = None
        current_date = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to find a date in this line
            _found_date = None
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    parsed = self._parse_date(match.group(1))
                    if parsed:
                        _found_date = parsed
                        current_date = parsed
                        break

            # Try to find amounts
            amounts = re.findall(amount_pattern, line)
            for amount_str in amounts:
                amount = self._parse_amount(amount_str)
                if amount and amount > 1.0:  # Filter out tiny amounts
                    # Determine confidence based on what we found
                    confidence = 50
                    if current_date:
                        confidence += 20
                    if current_vendor:
                        confidence += 15

                    # Try to extract vendor from line
                    vendor = self._extract_vendor_from_line(line)
                    if vendor:
                        current_vendor = vendor
                        confidence += 15

                    # Detect category
                    category = self._detect_category(current_vendor, line, None)

                    expenses.append({
                        "amount": amount,
                        "date": current_date or date(default_year, 1, 1),
                        "vendor": current_vendor,
                        "description": line[:200] if len(line) > 10 else None,
                        "category": category,
                        "confidence": min(confidence, 100)
                    })

        # Deduplicate by amount + date
        seen = set()
        unique = []
        for exp in expenses:
            key = (exp["amount"], exp["date"])
            if key not in seen:
                seen.add(key)
                unique.append(exp)

        return unique

    def _extract_vendor_from_line(self, line: str) -> Optional[str]:
        """Try to extract vendor name from a line."""
        # Common vendor indicators
        vendor_indicators = ["from:", "payee:", "to:", "paid to:", "vendor:"]

        lower_line = line.lower()
        for indicator in vendor_indicators:
            if indicator in lower_line:
                idx = lower_line.index(indicator) + len(indicator)
                remaining = line[idx:].strip()
                # Take first few words
                words = remaining.split()[:4]
                if words:
                    return " ".join(words)

        # Look for capitalized words at start of line (company names)
        words = line.split()
        if words and words[0][0].isupper() and len(words[0]) > 2:
            # Take capitalized words
            vendor_words = []
            for word in words[:3]:
                if word[0].isupper() or word.upper() == word:
                    vendor_words.append(word)
                else:
                    break
            if vendor_words:
                return " ".join(vendor_words)

        return None

    def get_expenses_needing_review(self, user_id: int) -> List[ExpenseResponse]:
        """Get OCR expenses that need manual review."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.*,
                   COALESCE(SUM(ea.allocation_percent), 0) as allocated_percent
            FROM expenses e
            LEFT JOIN expense_allocations ea ON e.id = ea.expense_id
            WHERE e.ocr_needs_review = 1 AND e.is_active = 1
            GROUP BY e.id
            ORDER BY e.created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_expense_response(row) for row in rows]

    def approve_ocr_expense(
        self,
        expense_id: int,
        user_id: int,
        updates: Optional[ExpenseUpdate] = None
    ) -> Tuple[Optional[ExpenseResponse], Optional[str]]:
        """
        Approve an OCR expense after review, optionally with corrections.

        Args:
            expense_id: Expense to approve
            user_id: User approving
            updates: Optional corrections to apply

        Returns:
            Tuple of (expense, error)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Apply any updates first
        if updates:
            result, error = self.update_expense(expense_id, updates, user_id)
            if error:
                conn.close()
                return None, error

        # Mark as reviewed
        cursor.execute("""
            UPDATE expenses SET ocr_needs_review = 0 WHERE id = ?
        """, (expense_id,))

        conn.commit()
        expense = self.get_expense(expense_id)
        conn.close()

        return expense, None


# ============================================================================
# SINGLETON
# ============================================================================

_cost_tracking_service: Optional[CostTrackingService] = None


def get_cost_tracking_service(db_path: str = "agtools.db") -> CostTrackingService:
    """Get or create the cost tracking service singleton."""
    global _cost_tracking_service
    if _cost_tracking_service is None:
        _cost_tracking_service = CostTrackingService(db_path)
    return _cost_tracking_service
