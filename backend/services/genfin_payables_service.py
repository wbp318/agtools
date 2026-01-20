"""
GenFin Payables Service - Vendors, Bills, Payments, Purchase Orders
Complete accounts payable management for farm operations
SQLite-backed persistence
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from enum import Enum
import uuid
import sqlite3
import json

from .genfin_core_service import genfin_core_service


class VendorStatus(Enum):
    """Vendor status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class BillStatus(Enum):
    """Bill/Invoice status"""
    DRAFT = "draft"
    OPEN = "open"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    VOIDED = "voided"


class PaymentMethod(Enum):
    """Payment methods"""
    CHECK = "check"
    ACH = "ach"
    WIRE = "wire"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    OTHER = "other"


class PurchaseOrderStatus(Enum):
    """Purchase order status"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    RECEIVED = "received"
    PARTIAL = "partial"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Payment terms definitions
PAYMENT_TERMS = {
    "Due on Receipt": 0,
    "Net 10": 10,
    "Net 15": 15,
    "Net 30": 30,
    "Net 45": 45,
    "Net 60": 60,
    "Net 90": 90,
    "2/10 Net 30": 30,  # 2% discount if paid in 10 days
}


class GenFinPayablesService:
    """
    GenFin Accounts Payable Service - SQLite backed

    Complete AP functionality:
    - Vendor management
    - Bills/Invoices entry
    - Bill payments
    - Vendor credits
    - Purchase orders
    - Aging reports
    - 1099 tracking
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
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Vendors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_vendors (
                    vendor_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    contact_name TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    mobile TEXT DEFAULT '',
                    fax TEXT DEFAULT '',
                    website TEXT DEFAULT '',
                    billing_address_line1 TEXT DEFAULT '',
                    billing_address_line2 TEXT DEFAULT '',
                    billing_city TEXT DEFAULT '',
                    billing_state TEXT DEFAULT '',
                    billing_zip TEXT DEFAULT '',
                    billing_country TEXT DEFAULT 'USA',
                    tax_id TEXT DEFAULT '',
                    is_1099_vendor INTEGER DEFAULT 0,
                    default_expense_account_id TEXT,
                    payment_terms TEXT DEFAULT 'Net 30',
                    credit_limit REAL DEFAULT 0.0,
                    vendor_type TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    opening_balance REAL DEFAULT 0.0,
                    opening_balance_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Bills table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_bills (
                    bill_id TEXT PRIMARY KEY,
                    bill_number TEXT NOT NULL,
                    vendor_id TEXT NOT NULL,
                    bill_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    reference_number TEXT DEFAULT '',
                    terms TEXT DEFAULT 'Net 30',
                    memo TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    tax_total REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    amount_paid REAL DEFAULT 0.0,
                    balance_due REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'draft',
                    ap_account_id TEXT,
                    journal_entry_id TEXT,
                    purchase_order_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Bill lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_bill_lines (
                    line_id TEXT PRIMARY KEY,
                    bill_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    tax_code TEXT,
                    tax_amount REAL DEFAULT 0.0,
                    billable INTEGER DEFAULT 0,
                    customer_id TEXT,
                    class_id TEXT,
                    location_id TEXT,
                    FOREIGN KEY (bill_id) REFERENCES genfin_bills (bill_id)
                )
            """)

            # Bill payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_bill_payments (
                    payment_id TEXT PRIMARY KEY,
                    payment_date TEXT NOT NULL,
                    vendor_id TEXT NOT NULL,
                    bank_account_id TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    reference_number TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    total_amount REAL DEFAULT 0.0,
                    applied_bills TEXT DEFAULT '[]',
                    journal_entry_id TEXT,
                    is_voided INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Vendor credits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_vendor_credits (
                    credit_id TEXT PRIMARY KEY,
                    credit_number TEXT NOT NULL,
                    vendor_id TEXT NOT NULL,
                    credit_date TEXT NOT NULL,
                    reference_number TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    total REAL DEFAULT 0.0,
                    amount_applied REAL DEFAULT 0.0,
                    balance REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'open',
                    journal_entry_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Vendor credit lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_vendor_credit_lines (
                    line_id TEXT PRIMARY KEY,
                    credit_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    tax_code TEXT,
                    tax_amount REAL DEFAULT 0.0,
                    class_id TEXT,
                    location_id TEXT,
                    FOREIGN KEY (credit_id) REFERENCES genfin_vendor_credits (credit_id)
                )
            """)

            # Purchase orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_purchase_orders (
                    po_id TEXT PRIMARY KEY,
                    po_number TEXT NOT NULL,
                    vendor_id TEXT NOT NULL,
                    order_date TEXT NOT NULL,
                    expected_date TEXT,
                    ship_to_address TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    terms TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    tax_total REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'draft',
                    approved_by TEXT,
                    approved_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)

            # Purchase order lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_purchase_order_lines (
                    line_id TEXT PRIMARY KEY,
                    po_id TEXT NOT NULL,
                    item_description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    quantity_received REAL DEFAULT 0.0,
                    account_id TEXT,
                    class_id TEXT,
                    FOREIGN KEY (po_id) REFERENCES genfin_purchase_orders (po_id)
                )
            """)

            # Settings table for sequence numbers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_payables_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Initialize sequence numbers if not exist
            cursor.execute("INSERT OR IGNORE INTO genfin_payables_settings (key, value) VALUES ('next_bill_number', '1')")
            cursor.execute("INSERT OR IGNORE INTO genfin_payables_settings (key, value) VALUES ('next_po_number', '1')")
            cursor.execute("INSERT OR IGNORE INTO genfin_payables_settings (key, value) VALUES ('next_credit_number', '1')")

            conn.commit()

    def _get_next_number(self, key: str) -> int:
        """Get and increment sequence number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM genfin_payables_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            current = int(row['value']) if row else 1
            cursor.execute("UPDATE genfin_payables_settings SET value = ? WHERE key = ?", (str(current + 1), key))
            conn.commit()
            return current

    def _get_default_ap_account(self) -> Optional[str]:
        """Get the default Accounts Payable account"""
        account = genfin_core_service.get_account_by_number("2000")
        return account["account_id"] if account else None

    # ==================== VENDOR MANAGEMENT ====================

    def create_vendor(
        self,
        company_name: str,
        display_name: Optional[str] = None,
        contact_name: str = "",
        email: str = "",
        phone: str = "",
        billing_address_line1: str = "",
        billing_city: str = "",
        billing_state: str = "",
        billing_zip: str = "",
        tax_id: str = "",
        is_1099_vendor: bool = False,
        payment_terms: str = "Net 30",
        vendor_type: str = "",
        default_expense_account_id: Optional[str] = None,
        opening_balance: float = 0.0,
        opening_balance_date: Optional[str] = None
    ) -> Dict:
        """Create a new vendor"""
        vendor_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_vendors (
                    vendor_id, company_name, display_name, contact_name, email, phone,
                    billing_address_line1, billing_city, billing_state, billing_zip,
                    tax_id, is_1099_vendor, payment_terms, vendor_type,
                    default_expense_account_id, opening_balance, opening_balance_date,
                    status, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vendor_id, company_name, display_name or company_name, contact_name,
                email, phone, billing_address_line1, billing_city, billing_state,
                billing_zip, tax_id, 1 if is_1099_vendor else 0, payment_terms,
                vendor_type, default_expense_account_id, opening_balance,
                opening_balance_date, 'active', now, now, 1
            ))
            conn.commit()

        vendor = self.get_vendor(vendor_id)
        return {
            "success": True,
            "vendor_id": vendor_id,
            "vendor": vendor
        }

    def update_vendor(self, vendor_id: str, **kwargs) -> Dict:
        """Update vendor information"""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {"success": False, "error": "Vendor not found"}

        # Build update statement dynamically
        updates = []
        values = []

        field_mapping = {
            'company_name': 'company_name',
            'display_name': 'display_name',
            'contact_name': 'contact_name',
            'email': 'email',
            'phone': 'phone',
            'mobile': 'mobile',
            'fax': 'fax',
            'website': 'website',
            'billing_address_line1': 'billing_address_line1',
            'billing_address_line2': 'billing_address_line2',
            'billing_city': 'billing_city',
            'billing_state': 'billing_state',
            'billing_zip': 'billing_zip',
            'billing_country': 'billing_country',
            'tax_id': 'tax_id',
            'is_1099_vendor': 'is_1099_vendor',
            'default_expense_account_id': 'default_expense_account_id',
            'payment_terms': 'payment_terms',
            'credit_limit': 'credit_limit',
            'vendor_type': 'vendor_type',
            'notes': 'notes',
            'status': 'status',
        }

        for key, value in kwargs.items():
            if key in field_mapping and value is not None:
                if key == 'is_1099_vendor':
                    value = 1 if value else 0
                elif key == 'status' and hasattr(value, 'value'):
                    value = value.value
                updates.append(f"{field_mapping[key]} = ?")
                values.append(value)

        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(vendor_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE genfin_vendors SET {', '.join(updates)} WHERE vendor_id = ?",
                    values
                )
                conn.commit()

        return {
            "success": True,
            "vendor": self.get_vendor(vendor_id)
        }

    def delete_vendor(self, vendor_id: str) -> bool:
        """Delete a vendor (soft delete)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE genfin_vendors SET is_active = 0, updated_at = ? WHERE vendor_id = ?",
                (datetime.now().isoformat(), vendor_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_vendor(self, vendor_id: str) -> Optional[Dict]:
        """Get vendor by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_vendors WHERE vendor_id = ? AND is_active = 1",
                (vendor_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_vendor(row)
        return None

    def list_vendors(
        self,
        status: Optional[str] = None,
        vendor_type: Optional[str] = None,
        is_1099: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """List vendors with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_vendors WHERE is_active = 1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)
            if vendor_type:
                query += " AND vendor_type = ?"
                params.append(vendor_type)
            if is_1099 is not None:
                query += " AND is_1099_vendor = ?"
                params.append(1 if is_1099 else 0)
            if search:
                query += " AND (company_name LIKE ? OR display_name LIKE ? OR contact_name LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])

            query += " ORDER BY display_name"

            cursor.execute(query, params)
            result = []
            for row in cursor.fetchall():
                vendor_dict = self._row_to_vendor(row)
                vendor_dict["balance"] = self.get_vendor_balance(vendor_dict["vendor_id"])
                result.append(vendor_dict)

            return result

    def get_vendor_balance(self, vendor_id: str) -> float:
        """Calculate vendor balance (amount owed)"""
        balance = 0.0

        # Get opening balance
        vendor = self.get_vendor(vendor_id)
        if vendor:
            balance = vendor.get("opening_balance", 0.0) or 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Add unpaid bills
            cursor.execute("""
                SELECT COALESCE(SUM(balance_due), 0) as total
                FROM genfin_bills
                WHERE vendor_id = ? AND is_active = 1 AND status IN ('open', 'partial', 'overdue')
            """, (vendor_id,))
            row = cursor.fetchone()
            balance += row['total'] if row else 0.0

            # Subtract unapplied credits
            cursor.execute("""
                SELECT COALESCE(SUM(balance), 0) as total
                FROM genfin_vendor_credits
                WHERE vendor_id = ? AND is_active = 1 AND status = 'open'
            """, (vendor_id,))
            row = cursor.fetchone()
            balance -= row['total'] if row else 0.0

        return round(balance, 2)

    def _row_to_vendor(self, row: sqlite3.Row) -> Dict:
        """Convert vendor row to dictionary"""
        return {
            "vendor_id": row['vendor_id'],
            "company_name": row['company_name'],
            "display_name": row['display_name'],
            "contact_name": row['contact_name'] or '',
            "email": row['email'] or '',
            "phone": row['phone'] or '',
            "mobile": row['mobile'] or '',
            "website": row['website'] or '',
            "billing_address": {
                "line1": row['billing_address_line1'] or '',
                "line2": row['billing_address_line2'] or '',
                "city": row['billing_city'] or '',
                "state": row['billing_state'] or '',
                "zip": row['billing_zip'] or '',
                "country": row['billing_country'] or 'USA'
            },
            "tax_id": row['tax_id'] or '',
            "is_1099_vendor": bool(row['is_1099_vendor']),
            "default_expense_account_id": row['default_expense_account_id'],
            "payment_terms": row['payment_terms'] or 'Net 30',
            "credit_limit": row['credit_limit'] or 0.0,
            "vendor_type": row['vendor_type'] or '',
            "notes": row['notes'] or '',
            "status": row['status'],
            "opening_balance": row['opening_balance'] or 0.0,
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    # ==================== BILLS ====================

    def create_bill(
        self,
        vendor_id: str,
        bill_date: str,
        lines: List[Dict],
        reference_number: str = "",
        terms: str = "Net 30",
        memo: str = "",
        ap_account_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None
    ) -> Dict:
        """Create a new bill"""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {"success": False, "error": "Vendor not found"}

        bill_id = str(uuid.uuid4())
        bill_number = f"BILL-{self._get_next_number('next_bill_number'):05d}"

        # Parse date and calculate due date
        b_date = datetime.strptime(bill_date, "%Y-%m-%d").date()
        days = PAYMENT_TERMS.get(terms, 30)
        d_date = b_date + timedelta(days=days)

        now = datetime.now().isoformat()

        # Calculate totals
        subtotal = 0.0
        tax_total = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert bill
            cursor.execute("""
                INSERT INTO genfin_bills (
                    bill_id, bill_number, vendor_id, bill_date, due_date,
                    reference_number, terms, memo, subtotal, tax_total, total,
                    amount_paid, balance_due, status, ap_account_id, purchase_order_id,
                    created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bill_id, bill_number, vendor_id, b_date.isoformat(), d_date.isoformat(),
                reference_number, terms, memo, 0.0, 0.0, 0.0, 0.0, 0.0, 'draft',
                ap_account_id or self._get_default_ap_account(), purchase_order_id,
                now, now, 1
            ))

            # Insert lines
            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
                tax_amount = line.get("tax_amount", 0)

                cursor.execute("""
                    INSERT INTO genfin_bill_lines (
                        line_id, bill_id, account_id, description, quantity,
                        unit_price, amount, tax_code, tax_amount, billable,
                        customer_id, class_id, location_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), bill_id, line["account_id"],
                    line.get("description", ""), line.get("quantity", 1),
                    line.get("unit_price", 0), line_amount,
                    line.get("tax_code"), tax_amount,
                    1 if line.get("billable", False) else 0,
                    line.get("customer_id"), line.get("class_id"), line.get("location_id")
                ))

                subtotal += line_amount
                tax_total += tax_amount

            total = subtotal + tax_total

            # Update bill totals
            cursor.execute("""
                UPDATE genfin_bills SET subtotal = ?, tax_total = ?, total = ?, balance_due = ?
                WHERE bill_id = ?
            """, (round(subtotal, 2), round(tax_total, 2), round(total, 2), round(total, 2), bill_id))

            conn.commit()

        bill = self.get_bill(bill_id)
        return {
            "success": True,
            "bill_id": bill_id,
            "bill_number": bill_number,
            "bill": bill
        }

    def post_bill(self, bill_id: str) -> Dict:
        """Post a bill - create journal entry and change status to open"""
        bill = self.get_bill(bill_id)
        if not bill:
            return {"success": False, "error": "Bill not found"}

        if bill["status"] != "draft":
            return {"success": False, "error": "Bill is not in draft status"}

        vendor = self.get_vendor(bill["vendor_id"])

        # Create journal entry
        journal_lines = []

        for line in bill["lines"]:
            journal_lines.append({
                "account_id": line["account_id"],
                "description": line["description"],
                "debit": line["amount"] + line["tax_amount"],
                "credit": 0,
                "class_id": line.get("class_id"),
                "location_id": line.get("location_id"),
                "vendor_id": bill["vendor_id"]
            })

        journal_lines.append({
            "account_id": bill["ap_account_id"] or self._get_default_ap_account(),
            "description": f"Bill {bill['bill_number']} - {vendor['display_name']}",
            "debit": 0,
            "credit": bill["total"],
            "vendor_id": bill["vendor_id"]
        })

        je_result = genfin_core_service.create_journal_entry(
            entry_date=bill["bill_date"],
            lines=journal_lines,
            memo=f"Bill {bill['bill_number']} - {bill['reference_number']}",
            source_type="bill",
            source_id=bill_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        # Update bill status
        new_status = 'open'
        if datetime.strptime(bill["due_date"], "%Y-%m-%d").date() < date.today():
            new_status = 'overdue'

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_bills SET status = ?, journal_entry_id = ?, updated_at = ?
                WHERE bill_id = ?
            """, (new_status, je_result["entry_id"], datetime.now().isoformat(), bill_id))
            conn.commit()

        return {
            "success": True,
            "bill": self.get_bill(bill_id),
            "journal_entry_id": je_result["entry_id"]
        }

    def void_bill(self, bill_id: str, reason: str = "") -> Dict:
        """Void a bill"""
        bill = self.get_bill(bill_id)
        if not bill:
            return {"success": False, "error": "Bill not found"}

        if bill["amount_paid"] > 0:
            return {"success": False, "error": "Cannot void bill with payments applied"}

        # Void journal entry if exists
        if bill.get("journal_entry_id"):
            genfin_core_service.void_journal_entry(bill["journal_entry_id"], reason)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            new_memo = f"{bill['memo']} [VOIDED: {reason}]"
            cursor.execute("""
                UPDATE genfin_bills SET status = ?, memo = ?, updated_at = ?
                WHERE bill_id = ?
            """, ('voided', new_memo, datetime.now().isoformat(), bill_id))
            conn.commit()

        return {
            "success": True,
            "bill": self.get_bill(bill_id)
        }

    def get_bill(self, bill_id: str) -> Optional[Dict]:
        """Get bill by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bills WHERE bill_id = ? AND is_active = 1",
                (bill_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_bill(row, cursor)
        return None

    def delete_bill(self, bill_id: str) -> bool:
        """Delete a bill (soft delete)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE genfin_bills SET is_active = 0, updated_at = ? WHERE bill_id = ?",
                (datetime.now().isoformat(), bill_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_bills(
        self,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        unpaid_only: bool = False
    ) -> List[Dict]:
        """List bills with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_bills WHERE is_active = 1"
            params = []

            if vendor_id:
                query += " AND vendor_id = ?"
                params.append(vendor_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if start_date:
                query += " AND bill_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND bill_date <= ?"
                params.append(end_date)
            if unpaid_only:
                query += " AND status IN ('open', 'partial', 'overdue')"

            query += " ORDER BY bill_date DESC"

            cursor.execute(query, params)
            return [self._row_to_bill(row, cursor) for row in cursor.fetchall()]

    def _row_to_bill(self, row: sqlite3.Row, cursor: sqlite3.Cursor) -> Dict:
        """Convert bill row to dictionary"""
        vendor = self.get_vendor(row['vendor_id'])
        vendor_name = vendor['display_name'] if vendor else 'Unknown'

        # Get bill lines
        cursor.execute(
            "SELECT * FROM genfin_bill_lines WHERE bill_id = ?",
            (row['bill_id'],)
        )
        lines = [
            {
                "line_id": line['line_id'],
                "account_id": line['account_id'],
                "description": line['description'] or '',
                "quantity": line['quantity'],
                "unit_price": line['unit_price'],
                "amount": line['amount'],
                "tax_code": line['tax_code'],
                "tax_amount": line['tax_amount'],
                "class_id": line['class_id'],
                "location_id": line['location_id']
            }
            for line in cursor.fetchall()
        ]

        return {
            "bill_id": row['bill_id'],
            "bill_number": row['bill_number'],
            "vendor_id": row['vendor_id'],
            "vendor_name": vendor_name,
            "bill_date": row['bill_date'],
            "due_date": row['due_date'],
            "reference_number": row['reference_number'] or '',
            "terms": row['terms'] or 'Net 30',
            "memo": row['memo'] or '',
            "lines": lines,
            "subtotal": row['subtotal'],
            "tax_total": row['tax_total'],
            "total": row['total'],
            "amount_paid": row['amount_paid'],
            "balance_due": row['balance_due'],
            "status": row['status'],
            "ap_account_id": row['ap_account_id'],
            "purchase_order_id": row['purchase_order_id'],
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    # ==================== BILL PAYMENTS ====================

    def create_bill_payment(
        self,
        vendor_id: str,
        payment_date: str,
        bank_account_id: str,
        payment_method: str,
        bills_to_pay: List[Dict],  # [{bill_id, amount}]
        reference_number: str = "",
        memo: str = ""
    ) -> Dict:
        """Create a payment for one or more bills"""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {"success": False, "error": "Vendor not found"}

        # Validate bills and amounts
        total_payment = 0.0
        for bill_payment in bills_to_pay:
            bill_id = bill_payment["bill_id"]
            amount = bill_payment["amount"]

            bill = self.get_bill(bill_id)
            if not bill:
                return {"success": False, "error": f"Bill {bill_id} not found"}
            if bill["vendor_id"] != vendor_id:
                return {"success": False, "error": f"Bill {bill['bill_number']} does not belong to this vendor"}
            if bill["status"] not in ['open', 'partial', 'overdue']:
                return {"success": False, "error": f"Bill {bill['bill_number']} is not payable"}
            if amount > bill["balance_due"]:
                return {"success": False, "error": f"Payment amount exceeds balance on {bill['bill_number']}"}

            total_payment += amount

        payment_id = str(uuid.uuid4())
        p_date = datetime.strptime(payment_date, "%Y-%m-%d").date()

        # Create journal entry
        journal_lines = [
            {
                "account_id": self._get_default_ap_account(),
                "description": f"Payment to {vendor['display_name']}",
                "debit": total_payment,
                "credit": 0,
                "vendor_id": vendor_id
            },
            {
                "account_id": bank_account_id,
                "description": f"Payment to {vendor['display_name']}",
                "debit": 0,
                "credit": total_payment,
                "vendor_id": vendor_id
            }
        ]

        je_result = genfin_core_service.create_journal_entry(
            entry_date=payment_date,
            lines=journal_lines,
            memo=f"Payment: {reference_number}" if reference_number else f"Payment to {vendor['display_name']}",
            source_type="bill_payment",
            source_id=payment_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        # Apply payments to bills
        applied_bills = []
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for bill_payment in bills_to_pay:
                bill = self.get_bill(bill_payment["bill_id"])
                amount = bill_payment["amount"]

                new_amount_paid = bill["amount_paid"] + amount
                new_balance = round(bill["total"] - new_amount_paid, 2)

                if new_balance == 0:
                    new_status = 'paid'
                else:
                    new_status = 'partial'

                cursor.execute("""
                    UPDATE genfin_bills
                    SET amount_paid = ?, balance_due = ?, status = ?, updated_at = ?
                    WHERE bill_id = ?
                """, (new_amount_paid, new_balance, new_status, datetime.now().isoformat(), bill["bill_id"]))

                applied_bills.append({
                    "bill_id": bill["bill_id"],
                    "bill_number": bill["bill_number"],
                    "amount": amount,
                    "balance_remaining": new_balance
                })

            # Insert payment record
            cursor.execute("""
                INSERT INTO genfin_bill_payments (
                    payment_id, payment_date, vendor_id, bank_account_id, payment_method,
                    reference_number, memo, total_amount, applied_bills, journal_entry_id,
                    is_voided, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment_id, p_date.isoformat(), vendor_id, bank_account_id, payment_method,
                reference_number, memo, total_payment, json.dumps(applied_bills),
                je_result["entry_id"], 0, datetime.now().isoformat(), 1
            ))

            conn.commit()

        return {
            "success": True,
            "payment_id": payment_id,
            "payment": self._get_payment(payment_id)
        }

    def void_payment(self, payment_id: str, reason: str = "") -> Dict:
        """Void a bill payment"""
        payment = self._get_payment(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}

        if payment["is_voided"]:
            return {"success": False, "error": "Payment is already voided"}

        # Reverse journal entry
        if payment.get("journal_entry_id"):
            genfin_core_service.reverse_journal_entry(
                payment["journal_entry_id"],
                date.today().isoformat()
            )

        # Reverse bill applications
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for applied in payment["applied_bills"]:
                bill = self.get_bill(applied["bill_id"])
                if bill:
                    new_amount_paid = bill["amount_paid"] - applied["amount"]
                    new_balance = round(bill["total"] - new_amount_paid, 2)

                    if new_balance == bill["total"]:
                        new_status = 'open'
                        if datetime.strptime(bill["due_date"], "%Y-%m-%d").date() < date.today():
                            new_status = 'overdue'
                    else:
                        new_status = 'partial'

                    cursor.execute("""
                        UPDATE genfin_bills
                        SET amount_paid = ?, balance_due = ?, status = ?, updated_at = ?
                        WHERE bill_id = ?
                    """, (new_amount_paid, new_balance, new_status, datetime.now().isoformat(), bill["bill_id"]))

            # Mark payment as voided
            cursor.execute(
                "UPDATE genfin_bill_payments SET is_voided = 1 WHERE payment_id = ?",
                (payment_id,)
            )

            conn.commit()

        return {
            "success": True,
            "message": "Payment voided successfully"
        }

    def list_payments(
        self,
        vendor_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_voided: bool = False
    ) -> List[Dict]:
        """List payments with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_bill_payments WHERE is_active = 1"
            params = []

            if vendor_id:
                query += " AND vendor_id = ?"
                params.append(vendor_id)
            if not include_voided:
                query += " AND is_voided = 0"
            if start_date:
                query += " AND payment_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND payment_date <= ?"
                params.append(end_date)

            query += " ORDER BY payment_date DESC"

            cursor.execute(query, params)
            return [self._row_to_payment(row) for row in cursor.fetchall()]

    def _get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_bill_payments WHERE payment_id = ? AND is_active = 1",
                (payment_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_payment(row)
        return None

    def _row_to_payment(self, row: sqlite3.Row) -> Dict:
        """Convert payment row to dictionary"""
        vendor = self.get_vendor(row['vendor_id'])
        vendor_name = vendor['display_name'] if vendor else 'Unknown'

        return {
            "payment_id": row['payment_id'],
            "payment_date": row['payment_date'],
            "vendor_id": row['vendor_id'],
            "vendor_name": vendor_name,
            "bank_account_id": row['bank_account_id'],
            "payment_method": row['payment_method'],
            "reference_number": row['reference_number'] or '',
            "memo": row['memo'] or '',
            "total_amount": row['total_amount'],
            "applied_bills": json.loads(row['applied_bills']) if row['applied_bills'] else [],
            "is_voided": bool(row['is_voided']),
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at']
        }

    # ==================== VENDOR CREDITS ====================

    def create_vendor_credit(
        self,
        vendor_id: str,
        credit_date: str,
        lines: List[Dict],
        reference_number: str = "",
        memo: str = ""
    ) -> Dict:
        """Create a vendor credit memo"""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {"success": False, "error": "Vendor not found"}

        credit_id = str(uuid.uuid4())
        credit_number = f"VCRD-{self._get_next_number('next_credit_number'):05d}"

        c_date = datetime.strptime(credit_date, "%Y-%m-%d").date()
        now = datetime.now().isoformat()

        # Calculate total
        total = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert credit
            cursor.execute("""
                INSERT INTO genfin_vendor_credits (
                    credit_id, credit_number, vendor_id, credit_date,
                    reference_number, memo, total, amount_applied, balance,
                    status, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                credit_id, credit_number, vendor_id, c_date.isoformat(),
                reference_number, memo, 0.0, 0.0, 0.0, 'open', now, 1
            ))

            # Insert lines
            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)

                cursor.execute("""
                    INSERT INTO genfin_vendor_credit_lines (
                        line_id, credit_id, account_id, description, quantity,
                        unit_price, amount, class_id, location_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), credit_id, line["account_id"],
                    line.get("description", ""), line.get("quantity", 1),
                    line.get("unit_price", 0), line_amount,
                    line.get("class_id"), line.get("location_id")
                ))

                total += line_amount

            # Update credit totals
            cursor.execute("""
                UPDATE genfin_vendor_credits SET total = ?, balance = ?
                WHERE credit_id = ?
            """, (round(total, 2), round(total, 2), credit_id))

            conn.commit()

        # Create journal entry (reverse of bill)
        journal_lines = []
        credit = self._get_credit(credit_id)

        for line in credit["lines"]:
            journal_lines.append({
                "account_id": line["account_id"],
                "description": line["description"],
                "debit": 0,
                "credit": line["amount"],
                "class_id": line.get("class_id"),
                "location_id": line.get("location_id")
            })

        journal_lines.append({
            "account_id": self._get_default_ap_account(),
            "description": f"Vendor Credit {credit_number}",
            "debit": total,
            "credit": 0,
            "vendor_id": vendor_id
        })

        je_result = genfin_core_service.create_journal_entry(
            entry_date=credit_date,
            lines=journal_lines,
            memo=f"Vendor Credit {credit_number}",
            source_type="vendor_credit",
            source_id=credit_id,
            auto_post=True
        )

        # Update journal entry ID
        if je_result.get("entry_id"):
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE genfin_vendor_credits SET journal_entry_id = ? WHERE credit_id = ?",
                    (je_result["entry_id"], credit_id)
                )
                conn.commit()

        return {
            "success": True,
            "credit_id": credit_id,
            "credit_number": credit_number,
            "credit": self._get_credit(credit_id)
        }

    def apply_credit_to_bill(self, credit_id: str, bill_id: str, amount: float) -> Dict:
        """Apply vendor credit to a bill"""
        credit = self._get_credit(credit_id)
        if not credit:
            return {"success": False, "error": "Credit not found"}

        bill = self.get_bill(bill_id)
        if not bill:
            return {"success": False, "error": "Bill not found"}

        if credit["vendor_id"] != bill["vendor_id"]:
            return {"success": False, "error": "Credit and bill must be for the same vendor"}
        if amount > credit["balance"]:
            return {"success": False, "error": "Amount exceeds credit balance"}
        if amount > bill["balance_due"]:
            return {"success": False, "error": "Amount exceeds bill balance"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update credit
            new_credit_applied = credit["amount_applied"] + amount
            new_credit_balance = round(credit["total"] - new_credit_applied, 2)
            new_credit_status = 'applied' if new_credit_balance == 0 else 'open'

            cursor.execute("""
                UPDATE genfin_vendor_credits SET amount_applied = ?, balance = ?, status = ?
                WHERE credit_id = ?
            """, (new_credit_applied, new_credit_balance, new_credit_status, credit_id))

            # Update bill
            new_bill_paid = bill["amount_paid"] + amount
            new_bill_balance = round(bill["total"] - new_bill_paid, 2)
            new_bill_status = 'paid' if new_bill_balance == 0 else 'partial'

            cursor.execute("""
                UPDATE genfin_bills SET amount_paid = ?, balance_due = ?, status = ?, updated_at = ?
                WHERE bill_id = ?
            """, (new_bill_paid, new_bill_balance, new_bill_status, datetime.now().isoformat(), bill_id))

            conn.commit()

        return {
            "success": True,
            "credit_balance": new_credit_balance,
            "bill_balance": new_bill_balance
        }

    def _get_credit(self, credit_id: str) -> Optional[Dict]:
        """Get credit by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_vendor_credits WHERE credit_id = ? AND is_active = 1",
                (credit_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_credit(row, cursor)
        return None

    def _row_to_credit(self, row: sqlite3.Row, cursor: sqlite3.Cursor) -> Dict:
        """Convert credit row to dictionary"""
        vendor = self.get_vendor(row['vendor_id'])
        vendor_name = vendor['display_name'] if vendor else 'Unknown'

        # Get credit lines
        cursor.execute(
            "SELECT * FROM genfin_vendor_credit_lines WHERE credit_id = ?",
            (row['credit_id'],)
        )
        lines = [
            {
                "line_id": line['line_id'],
                "account_id": line['account_id'],
                "description": line['description'] or '',
                "quantity": line['quantity'],
                "unit_price": line['unit_price'],
                "amount": line['amount']
            }
            for line in cursor.fetchall()
        ]

        return {
            "credit_id": row['credit_id'],
            "credit_number": row['credit_number'],
            "vendor_id": row['vendor_id'],
            "vendor_name": vendor_name,
            "credit_date": row['credit_date'],
            "reference_number": row['reference_number'] or '',
            "memo": row['memo'] or '',
            "lines": lines,
            "total": row['total'],
            "amount_applied": row['amount_applied'],
            "balance": row['balance'],
            "status": row['status'],
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at']
        }

    # ==================== PURCHASE ORDERS ====================

    def create_purchase_order(
        self,
        vendor_id: str,
        order_date: str,
        lines: List[Dict],
        expected_date: Optional[str] = None,
        ship_to_address: str = "",
        memo: str = "",
        terms: str = ""
    ) -> Dict:
        """Create a purchase order"""
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {"success": False, "error": "Vendor not found"}

        po_id = str(uuid.uuid4())
        po_number = f"PO-{self._get_next_number('next_po_number'):05d}"

        o_date = datetime.strptime(order_date, "%Y-%m-%d").date()
        now = datetime.now().isoformat()

        subtotal = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert PO
            cursor.execute("""
                INSERT INTO genfin_purchase_orders (
                    po_id, po_number, vendor_id, order_date, expected_date,
                    ship_to_address, memo, terms, subtotal, tax_total, total,
                    status, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                po_id, po_number, vendor_id, o_date.isoformat(), expected_date,
                ship_to_address, memo, terms or vendor['payment_terms'],
                0.0, 0.0, 0.0, 'draft', now, now, 1
            ))

            # Insert lines
            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)

                cursor.execute("""
                    INSERT INTO genfin_purchase_order_lines (
                        line_id, po_id, item_description, quantity, unit_price,
                        amount, quantity_received, account_id, class_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), po_id, line.get("description", ""),
                    line.get("quantity", 1), line.get("unit_price", 0),
                    line_amount, 0.0, line.get("account_id"), line.get("class_id")
                ))

                subtotal += line_amount

            # Update PO totals
            cursor.execute("""
                UPDATE genfin_purchase_orders SET subtotal = ?, total = ?
                WHERE po_id = ?
            """, (round(subtotal, 2), round(subtotal, 2), po_id))

            conn.commit()

        return {
            "success": True,
            "po_id": po_id,
            "po_number": po_number,
            "purchase_order": self._get_po(po_id)
        }

    def approve_purchase_order(self, po_id: str, approved_by: str) -> Dict:
        """Approve a purchase order"""
        po = self._get_po(po_id)
        if not po:
            return {"success": False, "error": "Purchase order not found"}

        if po["status"] not in ['draft', 'pending']:
            return {"success": False, "error": "Cannot approve PO in current status"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_purchase_orders
                SET status = ?, approved_by = ?, approved_date = ?, updated_at = ?
                WHERE po_id = ?
            """, ('approved', approved_by, date.today().isoformat(), datetime.now().isoformat(), po_id))
            conn.commit()

        return {
            "success": True,
            "purchase_order": self._get_po(po_id)
        }

    def receive_purchase_order(self, po_id: str, lines_received: List[Dict]) -> Dict:
        """Record receipt of items on a purchase order"""
        po = self._get_po(po_id)
        if not po:
            return {"success": False, "error": "Purchase order not found"}

        if po["status"] not in ['approved', 'partial']:
            return {"success": False, "error": "PO must be approved before receiving"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            all_received = True
            for receipt in lines_received:
                line_id = receipt["line_id"]
                qty = receipt["quantity_received"]

                # Get current quantity received
                cursor.execute(
                    "SELECT quantity, quantity_received FROM genfin_purchase_order_lines WHERE line_id = ?",
                    (line_id,)
                )
                row = cursor.fetchone()
                if row:
                    new_qty_received = row['quantity_received'] + qty
                    cursor.execute(
                        "UPDATE genfin_purchase_order_lines SET quantity_received = ? WHERE line_id = ?",
                        (new_qty_received, line_id)
                    )
                    if new_qty_received < row['quantity']:
                        all_received = False

            # Update PO status
            new_status = 'received' if all_received else 'partial'
            cursor.execute("""
                UPDATE genfin_purchase_orders SET status = ?, updated_at = ?
                WHERE po_id = ?
            """, (new_status, datetime.now().isoformat(), po_id))

            conn.commit()

        return {
            "success": True,
            "status": new_status,
            "purchase_order": self._get_po(po_id)
        }

    def convert_po_to_bill(self, po_id: str, bill_date: str, reference_number: str = "") -> Dict:
        """Convert a received purchase order to a bill"""
        po = self._get_po(po_id)
        if not po:
            return {"success": False, "error": "Purchase order not found"}

        if po["status"] not in ['received', 'partial']:
            return {"success": False, "error": "PO must be received before converting to bill"}

        vendor = self.get_vendor(po["vendor_id"])

        # Create bill lines from PO lines
        bill_lines = []
        for line in po["lines"]:
            if line["quantity_received"] > 0:
                bill_lines.append({
                    "account_id": line.get("account_id") or vendor.get("default_expense_account_id"),
                    "description": line["item_description"],
                    "quantity": line["quantity_received"],
                    "unit_price": line["unit_price"],
                    "class_id": line.get("class_id")
                })

        result = self.create_bill(
            vendor_id=po["vendor_id"],
            bill_date=bill_date,
            lines=bill_lines,
            reference_number=reference_number,
            terms=po["terms"],
            memo=f"From PO {po['po_number']}",
            purchase_order_id=po_id
        )

        if result["success"]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE genfin_purchase_orders SET status = ?, updated_at = ?
                    WHERE po_id = ?
                """, ('closed', datetime.now().isoformat(), po_id))
                conn.commit()

        return result

    def list_purchase_orders(
        self,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List purchase orders"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_purchase_orders WHERE is_active = 1"
            params = []

            if vendor_id:
                query += " AND vendor_id = ?"
                params.append(vendor_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if start_date:
                query += " AND order_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND order_date <= ?"
                params.append(end_date)

            query += " ORDER BY order_date DESC"

            cursor.execute(query, params)
            return [self._row_to_po(row, cursor) for row in cursor.fetchall()]

    def _get_po(self, po_id: str) -> Optional[Dict]:
        """Get purchase order by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM genfin_purchase_orders WHERE po_id = ? AND is_active = 1",
                (po_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_po(row, cursor)
        return None

    def _row_to_po(self, row: sqlite3.Row, cursor: sqlite3.Cursor) -> Dict:
        """Convert PO row to dictionary"""
        vendor = self.get_vendor(row['vendor_id'])
        vendor_name = vendor['display_name'] if vendor else 'Unknown'

        # Get PO lines
        cursor.execute(
            "SELECT * FROM genfin_purchase_order_lines WHERE po_id = ?",
            (row['po_id'],)
        )
        lines = [
            {
                "line_id": line['line_id'],
                "item_description": line['item_description'] or '',
                "quantity": line['quantity'],
                "unit_price": line['unit_price'],
                "amount": line['amount'],
                "quantity_received": line['quantity_received'],
                "account_id": line['account_id'],
                "class_id": line['class_id']
            }
            for line in cursor.fetchall()
        ]

        return {
            "po_id": row['po_id'],
            "po_number": row['po_number'],
            "vendor_id": row['vendor_id'],
            "vendor_name": vendor_name,
            "order_date": row['order_date'],
            "expected_date": row['expected_date'],
            "ship_to_address": row['ship_to_address'] or '',
            "memo": row['memo'] or '',
            "terms": row['terms'] or '',
            "lines": lines,
            "subtotal": row['subtotal'],
            "tax_total": row['tax_total'],
            "total": row['total'],
            "status": row['status'],
            "approved_by": row['approved_by'],
            "approved_date": row['approved_date'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    # ==================== REPORTS ====================

    def get_ap_aging(self, as_of_date: Optional[str] = None) -> Dict:
        """Generate accounts payable aging report"""
        ref_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()

        aging = {
            "current": [],
            "1_30": [],
            "31_60": [],
            "61_90": [],
            "over_90": [],
            "totals": {
                "current": 0,
                "1_30": 0,
                "31_60": 0,
                "61_90": 0,
                "over_90": 0,
                "total": 0
            }
        }

        bills = self.list_bills(unpaid_only=True)

        for bill in bills:
            bill_date = datetime.strptime(bill["bill_date"], "%Y-%m-%d").date()
            if bill_date > ref_date:
                continue

            due_date = datetime.strptime(bill["due_date"], "%Y-%m-%d").date()
            days_old = (ref_date - due_date).days

            vendor = self.get_vendor(bill["vendor_id"])
            vendor_name = vendor['display_name'] if vendor else 'Unknown'

            entry = {
                "bill_id": bill["bill_id"],
                "bill_number": bill["bill_number"],
                "vendor_id": bill["vendor_id"],
                "vendor_name": vendor_name,
                "bill_date": bill["bill_date"],
                "due_date": bill["due_date"],
                "days_overdue": max(0, days_old),
                "balance": bill["balance_due"]
            }

            if days_old <= 0:
                aging["current"].append(entry)
                aging["totals"]["current"] += bill["balance_due"]
            elif days_old <= 30:
                aging["1_30"].append(entry)
                aging["totals"]["1_30"] += bill["balance_due"]
            elif days_old <= 60:
                aging["31_60"].append(entry)
                aging["totals"]["31_60"] += bill["balance_due"]
            elif days_old <= 90:
                aging["61_90"].append(entry)
                aging["totals"]["61_90"] += bill["balance_due"]
            else:
                aging["over_90"].append(entry)
                aging["totals"]["over_90"] += bill["balance_due"]

            aging["totals"]["total"] += bill["balance_due"]

        # Round totals
        for key in aging["totals"]:
            aging["totals"][key] = round(aging["totals"][key], 2)

        return {
            "as_of_date": ref_date.isoformat(),
            "aging": aging
        }

    def get_vendor_1099_summary(self, year: int) -> List[Dict]:
        """Get 1099 summary for vendors"""
        result = []

        vendors = self.list_vendors(is_1099=True)

        for vendor in vendors:
            total_payments = 0.0

            payments = self.list_payments(vendor_id=vendor["vendor_id"])
            for payment in payments:
                if payment["is_voided"]:
                    continue
                payment_date = datetime.strptime(payment["payment_date"], "%Y-%m-%d").date()
                if payment_date.year != year:
                    continue
                total_payments += payment["total_amount"]

            if total_payments > 0:
                result.append({
                    "vendor_id": vendor["vendor_id"],
                    "vendor_name": vendor["display_name"],
                    "tax_id": vendor["tax_id"],
                    "address": f"{vendor['billing_address']['line1']}, {vendor['billing_address']['city']}, {vendor['billing_address']['state']} {vendor['billing_address']['zip']}",
                    "total_payments": round(total_payments, 2),
                    "requires_1099": total_payments >= 600  # IRS threshold
                })

        return sorted(result, key=lambda v: v["total_payments"], reverse=True)

    def get_bills_due_summary(self, days_ahead: int = 30) -> Dict:
        """Get summary of bills due in upcoming period"""
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        bills_due = []
        total_due = 0.0

        bills = self.list_bills(unpaid_only=True)

        for bill in bills:
            due_date = datetime.strptime(bill["due_date"], "%Y-%m-%d").date()
            if due_date > end_date:
                continue

            vendor = self.get_vendor(bill["vendor_id"])
            vendor_name = vendor['display_name'] if vendor else 'Unknown'

            bills_due.append({
                "bill_id": bill["bill_id"],
                "bill_number": bill["bill_number"],
                "vendor_name": vendor_name,
                "due_date": bill["due_date"],
                "balance": bill["balance_due"],
                "days_until_due": (due_date - today).days,
                "is_overdue": due_date < today
            })

            total_due += bill["balance_due"]

        return {
            "period_start": today.isoformat(),
            "period_end": end_date.isoformat(),
            "bills_count": len(bills_due),
            "total_due": round(total_due, 2),
            "bills": sorted(bills_due, key=lambda b: b["due_date"])
        }

    # ==================== SERVICE SUMMARY ====================

    def get_service_summary(self) -> Dict:
        """Get GenFin Payables service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM genfin_vendors WHERE is_active = 1")
            total_vendors = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_vendors WHERE is_active = 1 AND status = 'active'")
            active_vendors = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_bills WHERE is_active = 1")
            total_bills = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_bills WHERE is_active = 1 AND status IN ('open', 'partial', 'overdue')")
            open_bills = cursor.fetchone()['count']

            cursor.execute("SELECT COALESCE(SUM(balance_due), 0) as total FROM genfin_bills WHERE is_active = 1 AND status IN ('open', 'partial', 'overdue')")
            total_outstanding = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_bill_payments WHERE is_active = 1")
            total_payments = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_vendor_credits WHERE is_active = 1")
            total_credits = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM genfin_purchase_orders WHERE is_active = 1")
            total_pos = cursor.fetchone()['count']

        return {
            "service": "GenFin Payables",
            "version": "2.0.0",
            "storage": "SQLite",
            "total_vendors": total_vendors,
            "active_vendors": active_vendors,
            "total_bills": total_bills,
            "open_bills": open_bills,
            "total_outstanding": round(total_outstanding, 2),
            "total_payments": total_payments,
            "total_credits": total_credits,
            "total_purchase_orders": total_pos
        }


# Singleton instance
genfin_payables_service = GenFinPayablesService()
