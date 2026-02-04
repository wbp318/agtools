"""
GenFin Receivables Service - Customers, Invoices, Payments Received, Estimates
Complete accounts receivable management for farm operations
SQLite persistent storage implementation
"""

from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional
from enum import Enum
import uuid
import sqlite3
import json

from .genfin_core_service import genfin_core_service


class CustomerStatus(Enum):
    """Customer status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class InvoiceStatus(Enum):
    """Invoice status"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    VOIDED = "voided"


class EstimateStatus(Enum):
    """Estimate/Quote status"""
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONVERTED = "converted"
    EXPIRED = "expired"


class PaymentMethod(Enum):
    """Payment methods received"""
    CHECK = "check"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    ACH = "ach"
    WIRE = "wire"
    OTHER = "other"


# Payment terms definitions
PAYMENT_TERMS = {
    "Due on Receipt": 0,
    "Net 10": 10,
    "Net 15": 15,
    "Net 30": 30,
    "Net 45": 45,
    "Net 60": 60,
    "Net 90": 90,
    "2/10 Net 30": 30,
}


class GenFinReceivablesService:
    """
    GenFin Accounts Receivable Service - SQLite persistent storage

    Complete AR functionality:
    - Customer management
    - Invoice creation and sending
    - Payment receipt
    - Customer credits/refunds
    - Estimates/Quotes
    - Sales receipts
    - Aging reports
    - Statement generation
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

        # Default AR account
        self.default_ar_account_id = self._get_default_ar_account()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Create database tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_customers (
                    customer_id TEXT PRIMARY KEY,
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
                    shipping_address_line1 TEXT DEFAULT '',
                    shipping_address_line2 TEXT DEFAULT '',
                    shipping_city TEXT DEFAULT '',
                    shipping_state TEXT DEFAULT '',
                    shipping_zip TEXT DEFAULT '',
                    shipping_country TEXT DEFAULT 'USA',
                    tax_exempt INTEGER DEFAULT 0,
                    tax_id TEXT DEFAULT '',
                    default_income_account_id TEXT,
                    payment_terms TEXT DEFAULT 'Net 30',
                    credit_limit REAL DEFAULT 0.0,
                    customer_type TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    opening_balance REAL DEFAULT 0.0,
                    opening_balance_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Invoices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_invoices (
                    invoice_id TEXT PRIMARY KEY,
                    invoice_number TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    invoice_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    po_number TEXT DEFAULT '',
                    terms TEXT DEFAULT 'Net 30',
                    memo TEXT DEFAULT '',
                    message_on_invoice TEXT DEFAULT '',
                    message_on_statement TEXT DEFAULT '',
                    billing_address TEXT DEFAULT '',
                    shipping_address TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    discount_total REAL DEFAULT 0.0,
                    tax_total REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    amount_paid REAL DEFAULT 0.0,
                    balance_due REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'draft',
                    ar_account_id TEXT,
                    journal_entry_id TEXT,
                    email_sent INTEGER DEFAULT 0,
                    email_sent_date TEXT,
                    last_viewed_date TEXT,
                    estimate_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Invoice lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_invoice_lines (
                    line_id TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    tax_code TEXT,
                    tax_amount REAL DEFAULT 0.0,
                    discount_percent REAL DEFAULT 0.0,
                    discount_amount REAL DEFAULT 0.0,
                    class_id TEXT,
                    location_id TEXT,
                    service_date TEXT,
                    FOREIGN KEY (invoice_id) REFERENCES genfin_invoices(invoice_id)
                )
            """)

            # Payments received table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_payments_received (
                    payment_id TEXT PRIMARY KEY,
                    payment_date TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    deposit_account_id TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    reference_number TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    total_amount REAL DEFAULT 0.0,
                    applied_invoices TEXT DEFAULT '[]',
                    unapplied_amount REAL DEFAULT 0.0,
                    journal_entry_id TEXT,
                    is_voided INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Customer credits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_customer_credits (
                    credit_id TEXT PRIMARY KEY,
                    credit_number TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    credit_date TEXT NOT NULL,
                    reason TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    total REAL DEFAULT 0.0,
                    amount_applied REAL DEFAULT 0.0,
                    balance REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'open',
                    journal_entry_id TEXT,
                    related_invoice_id TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Credit lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_credit_lines (
                    line_id TEXT PRIMARY KEY,
                    credit_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    class_id TEXT,
                    location_id TEXT,
                    FOREIGN KEY (credit_id) REFERENCES genfin_customer_credits(credit_id)
                )
            """)

            # Estimates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_estimates (
                    estimate_id TEXT PRIMARY KEY,
                    estimate_number TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    estimate_date TEXT NOT NULL,
                    expiration_date TEXT NOT NULL,
                    po_number TEXT DEFAULT '',
                    terms TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    message_to_customer TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    tax_total REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'draft',
                    accepted_date TEXT,
                    converted_invoice_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Estimate lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_estimate_lines (
                    line_id TEXT PRIMARY KEY,
                    estimate_id TEXT NOT NULL,
                    account_id TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    class_id TEXT,
                    location_id TEXT,
                    FOREIGN KEY (estimate_id) REFERENCES genfin_estimates(estimate_id)
                )
            """)

            # Sales receipts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_sales_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    receipt_number TEXT NOT NULL,
                    customer_id TEXT,
                    receipt_date TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    deposit_account_id TEXT NOT NULL,
                    reference_number TEXT DEFAULT '',
                    memo TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    tax_total REAL DEFAULT 0.0,
                    total REAL DEFAULT 0.0,
                    journal_entry_id TEXT,
                    is_voided INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # Sales receipt lines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_sales_receipt_lines (
                    line_id TEXT PRIMARY KEY,
                    receipt_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    quantity REAL DEFAULT 1.0,
                    unit_price REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    class_id TEXT,
                    location_id TEXT,
                    FOREIGN KEY (receipt_id) REFERENCES genfin_sales_receipts(receipt_id)
                )
            """)

            # Settings table for sequences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS genfin_receivables_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Initialize sequence values
            cursor.execute("INSERT OR IGNORE INTO genfin_receivables_settings (key, value) VALUES ('next_invoice_number', '1001')")
            cursor.execute("INSERT OR IGNORE INTO genfin_receivables_settings (key, value) VALUES ('next_estimate_number', '1')")
            cursor.execute("INSERT OR IGNORE INTO genfin_receivables_settings (key, value) VALUES ('next_credit_number', '1')")
            cursor.execute("INSERT OR IGNORE INTO genfin_receivables_settings (key, value) VALUES ('next_receipt_number', '1')")

            # Create indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer ON genfin_invoices(customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON genfin_invoices(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_customer ON genfin_payments_received(customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_status ON genfin_customers(status)")

            conn.commit()

    def _get_next_number(self, key: str) -> int:
        """Get and increment a sequence number"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM genfin_receivables_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            current = int(row['value']) if row else 1
            cursor.execute("UPDATE genfin_receivables_settings SET value = ? WHERE key = ?", (str(current + 1), key))
            conn.commit()
            return current

    def _get_default_ar_account(self) -> Optional[str]:
        """Get the default Accounts Receivable account"""
        account = genfin_core_service.get_account_by_number("1100")
        return account["account_id"] if account else None

    # ==================== CUSTOMER MANAGEMENT ====================

    def create_customer(
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
        tax_exempt: bool = False,
        payment_terms: str = "Net 30",
        customer_type: str = "",
        default_income_account_id: Optional[str] = None,
        credit_limit: float = 0.0,
        opening_balance: float = 0.0,
        opening_balance_date: Optional[str] = None
    ) -> Dict:
        """Create a new customer"""
        customer_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO genfin_customers
                (customer_id, company_name, display_name, contact_name, email, phone,
                 billing_address_line1, billing_city, billing_state, billing_zip,
                 tax_exempt, payment_terms, customer_type, default_income_account_id,
                 credit_limit, opening_balance, opening_balance_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id, company_name, display_name or company_name, contact_name, email, phone,
                billing_address_line1, billing_city, billing_state, billing_zip,
                1 if tax_exempt else 0, payment_terms, customer_type, default_income_account_id,
                credit_limit, opening_balance, opening_balance_date, now, now
            ))
            conn.commit()

        return {
            "success": True,
            "customer_id": customer_id,
            "customer": self.get_customer(customer_id)
        }

    def update_customer(self, customer_id: str, **kwargs) -> Dict:
        """Update customer information"""
        customer = self.get_customer(customer_id)
        if not customer:
            return {"success": False, "error": "Customer not found"}

        updates = []
        params = []
        for key, value in kwargs.items():
            if value is not None:
                if key == 'tax_exempt':
                    value = 1 if value else 0
                updates.append(f"{key} = ?")
                params.append(value)

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())
            params.append(customer_id)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE genfin_customers SET {', '.join(updates)} WHERE customer_id = ?", params)
                conn.commit()

        return {"success": True, "customer": self.get_customer(customer_id)}

    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM genfin_customers WHERE customer_id = ?", (customer_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_customers WHERE customer_id = ?", (customer_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_customer_dict(row)

    def list_customers(
        self,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        search: Optional[str] = None,
        with_balance_only: bool = False
    ) -> List[Dict]:
        """List customers with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_customers WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)
            if customer_type:
                query += " AND customer_type = ?"
                params.append(customer_type)
            if search:
                query += " AND (company_name LIKE ? OR display_name LIKE ? OR contact_name LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])

            query += " ORDER BY display_name"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                customer_dict = self._row_to_customer_dict(row)
                balance = self.get_customer_balance(row['customer_id'])
                if with_balance_only and balance == 0:
                    continue
                customer_dict["balance"] = balance
                result.append(customer_dict)

            return result

    def get_customer_balance(self, customer_id: str) -> float:
        """Calculate customer balance (amount owed to us)"""
        balance = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Opening balance
            cursor.execute("SELECT opening_balance FROM genfin_customers WHERE customer_id = ?", (customer_id,))
            row = cursor.fetchone()
            if row:
                balance = row['opening_balance'] or 0.0

            # Unpaid invoices
            cursor.execute("""
                SELECT SUM(balance_due) as total FROM genfin_invoices
                WHERE customer_id = ? AND status IN ('sent', 'viewed', 'partial', 'overdue')
            """, (customer_id,))
            row = cursor.fetchone()
            if row and row['total']:
                balance += row['total']

            # Unapplied credits
            cursor.execute("""
                SELECT SUM(balance) as total FROM genfin_customer_credits
                WHERE customer_id = ? AND status = 'open'
            """, (customer_id,))
            row = cursor.fetchone()
            if row and row['total']:
                balance -= row['total']

            # Unapplied payments
            cursor.execute("""
                SELECT SUM(unapplied_amount) as total FROM genfin_payments_received
                WHERE customer_id = ? AND is_voided = 0
            """, (customer_id,))
            row = cursor.fetchone()
            if row and row['total']:
                balance -= row['total']

        return round(balance, 2)

    # ==================== INVOICES ====================

    def create_invoice(
        self,
        customer_id: str,
        invoice_date: str,
        lines: List[Dict],
        po_number: str = "",
        terms: str = "Net 30",
        memo: str = "",
        message_on_invoice: str = "",
        ar_account_id: Optional[str] = None,
        estimate_id: Optional[str] = None
    ) -> Dict:
        """Create a new invoice"""
        if not self.get_customer(customer_id):
            return {"success": False, "error": "Customer not found"}

        invoice_id = str(uuid.uuid4())
        invoice_number = f"INV-{self._get_next_number('next_invoice_number'):05d}"

        i_date = datetime.strptime(invoice_date, "%Y-%m-%d").date()
        days = PAYMENT_TERMS.get(terms, 30)
        d_date = i_date + timedelta(days=days)

        subtotal = 0.0
        discount_total = 0.0
        tax_total = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get customer for addresses
            cursor.execute("SELECT * FROM genfin_customers WHERE customer_id = ?", (customer_id,))
            customer = cursor.fetchone()
            billing_addr = f"{customer['billing_address_line1']}\n{customer['billing_city']}, {customer['billing_state']} {customer['billing_zip']}"
            shipping_addr = f"{customer['shipping_address_line1']}\n{customer['shipping_city']}, {customer['shipping_state']} {customer['shipping_zip']}"

            # Process lines
            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
                discount = line.get("discount_amount", 0)
                tax_amount = line.get("tax_amount", 0)

                line_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO genfin_invoice_lines
                    (line_id, invoice_id, account_id, description, quantity, unit_price, amount,
                     tax_code, tax_amount, discount_percent, discount_amount, class_id, location_id, service_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    line_id, invoice_id, line["account_id"], line.get("description", ""),
                    line.get("quantity", 1), line.get("unit_price", 0), line_amount,
                    line.get("tax_code"), tax_amount, line.get("discount_percent", 0), discount,
                    line.get("class_id"), line.get("location_id"), line.get("service_date")
                ))

                subtotal += line_amount
                discount_total += discount
                tax_total += tax_amount

            total = subtotal - discount_total + tax_total
            now = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO genfin_invoices
                (invoice_id, invoice_number, customer_id, invoice_date, due_date,
                 po_number, terms, memo, message_on_invoice, billing_address, shipping_address,
                 subtotal, discount_total, tax_total, total, amount_paid, balance_due,
                 status, ar_account_id, estimate_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'draft', ?, ?, ?, ?)
            """, (
                invoice_id, invoice_number, customer_id, invoice_date, d_date.isoformat(),
                po_number, terms, memo, message_on_invoice, billing_addr, shipping_addr,
                round(subtotal, 2), round(discount_total, 2), round(tax_total, 2),
                round(total, 2), round(total, 2),
                ar_account_id or self.default_ar_account_id, estimate_id, now, now
            ))

            conn.commit()

        return {
            "success": True,
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "invoice": self.get_invoice(invoice_id)
        }

    def send_invoice(self, invoice_id: str) -> Dict:
        """Send/post an invoice - create journal entry and change status"""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return {"success": False, "error": "Invoice not found"}

        if invoice["status"] != "draft":
            return {"success": False, "error": "Invoice has already been sent"}

        customer = self.get_customer(invoice["customer_id"])

        # Create journal entry
        journal_lines = [{
            "account_id": invoice["ar_account_id"],
            "description": f"Invoice {invoice['invoice_number']} - {customer['display_name']}",
            "debit": invoice["total"],
            "credit": 0,
            "customer_id": invoice["customer_id"]
        }]

        for line in invoice["lines"]:
            journal_lines.append({
                "account_id": line["account_id"],
                "description": line["description"],
                "debit": 0,
                "credit": line["amount"] - line["discount_amount"],
                "class_id": line["class_id"],
                "location_id": line["location_id"],
                "customer_id": invoice["customer_id"]
            })

        if invoice["tax_total"] > 0:
            tax_account = genfin_core_service.get_account_by_number("2500")
            if tax_account:
                journal_lines.append({
                    "account_id": tax_account["account_id"],
                    "description": f"Sales tax - Invoice {invoice['invoice_number']}",
                    "debit": 0,
                    "credit": invoice["tax_total"]
                })

        je_result = genfin_core_service.create_journal_entry(
            entry_date=invoice["invoice_date"],
            lines=journal_lines,
            memo=f"Invoice {invoice['invoice_number']}",
            source_type="invoice",
            source_id=invoice_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        now = datetime.now(timezone.utc).isoformat()
        status = "overdue" if datetime.strptime(invoice["due_date"], "%Y-%m-%d").date() < date.today() else "sent"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_invoices
                SET status = ?, journal_entry_id = ?, email_sent = 1, email_sent_date = ?, updated_at = ?
                WHERE invoice_id = ?
            """, (status, je_result["entry_id"], now, now, invoice_id))
            conn.commit()

        return {
            "success": True,
            "invoice": self.get_invoice(invoice_id),
            "journal_entry_id": je_result["entry_id"]
        }

    def void_invoice(self, invoice_id: str, reason: str = "") -> Dict:
        """Void an invoice"""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return {"success": False, "error": "Invoice not found"}

        if invoice["amount_paid"] > 0:
            return {"success": False, "error": "Cannot void invoice with payments applied"}

        if invoice["journal_entry_id"]:
            genfin_core_service.void_journal_entry(invoice["journal_entry_id"], reason)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_invoices SET status = 'voided', memo = ?, updated_at = ? WHERE invoice_id = ?
            """, (f"{invoice['memo']} [VOIDED: {reason}]", datetime.now(timezone.utc).isoformat(), invoice_id))
            conn.commit()

        return {"success": True, "invoice": self.get_invoice(invoice_id)}

    def get_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Get invoice by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_invoices WHERE invoice_id = ?", (invoice_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute("SELECT * FROM genfin_invoice_lines WHERE invoice_id = ?", (invoice_id,))
            lines = cursor.fetchall()

            return self._row_to_invoice_dict(row, lines)

    def delete_invoice(self, invoice_id: str) -> bool:
        """Delete an invoice"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM genfin_invoice_lines WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM genfin_invoices WHERE invoice_id = ?", (invoice_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_invoices(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        unpaid_only: bool = False
    ) -> List[Dict]:
        """List invoices with filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_invoices WHERE 1=1"
            params = []

            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if start_date:
                query += " AND invoice_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND invoice_date <= ?"
                params.append(end_date)
            if unpaid_only:
                query += " AND status IN ('sent', 'viewed', 'partial', 'overdue')"

            query += " ORDER BY invoice_date DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                cursor.execute("SELECT * FROM genfin_invoice_lines WHERE invoice_id = ?", (row['invoice_id'],))
                lines = cursor.fetchall()
                result.append(self._row_to_invoice_dict(row, lines))

            return result

    # ==================== PAYMENTS RECEIVED ====================

    def receive_payment(
        self,
        customer_id: str,
        payment_date: str,
        deposit_account_id: str,
        payment_method: str,
        total_amount: float,
        invoices_to_apply: List[Dict] = None,
        reference_number: str = "",
        memo: str = ""
    ) -> Dict:
        """Receive payment from customer"""
        if not self.get_customer(customer_id):
            return {"success": False, "error": "Customer not found"}

        invoices_to_apply = invoices_to_apply or []
        total_applied = 0.0

        # Validate invoices
        for inv_payment in invoices_to_apply:
            invoice = self.get_invoice(inv_payment["invoice_id"])
            if not invoice:
                return {"success": False, "error": f"Invoice {inv_payment['invoice_id']} not found"}
            if invoice["customer_id"] != customer_id:
                return {"success": False, "error": f"Invoice {invoice['invoice_number']} does not belong to this customer"}
            if invoice["status"] not in ["sent", "viewed", "partial", "overdue"]:
                return {"success": False, "error": f"Invoice {invoice['invoice_number']} is not payable"}
            if inv_payment["amount"] > invoice["balance_due"]:
                return {"success": False, "error": f"Payment amount exceeds balance on {invoice['invoice_number']}"}
            total_applied += inv_payment["amount"]

        if total_applied > total_amount:
            return {"success": False, "error": "Total applied exceeds payment amount"}

        payment_id = str(uuid.uuid4())
        customer = self.get_customer(customer_id)

        # Create journal entry
        journal_lines = [
            {
                "account_id": deposit_account_id,
                "description": f"Payment from {customer['display_name']}",
                "debit": total_amount,
                "credit": 0,
                "customer_id": customer_id
            },
            {
                "account_id": self.default_ar_account_id,
                "description": f"Payment from {customer['display_name']}",
                "debit": 0,
                "credit": total_amount,
                "customer_id": customer_id
            }
        ]

        je_result = genfin_core_service.create_journal_entry(
            entry_date=payment_date,
            lines=journal_lines,
            memo=f"Payment received: {reference_number}" if reference_number else f"Payment from {customer['display_name']}",
            source_type="payment_received",
            source_id=payment_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        # Apply payments and update invoices
        applied_invoices = []
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for inv_payment in invoices_to_apply:
                invoice = self.get_invoice(inv_payment["invoice_id"])
                amount = inv_payment["amount"]

                new_amount_paid = invoice["amount_paid"] + amount
                new_balance = round(invoice["total"] - new_amount_paid, 2)
                new_status = "paid" if new_balance == 0 else "partial"

                cursor.execute("""
                    UPDATE genfin_invoices
                    SET amount_paid = ?, balance_due = ?, status = ?, updated_at = ?
                    WHERE invoice_id = ?
                """, (new_amount_paid, new_balance, new_status, datetime.now(timezone.utc).isoformat(), inv_payment["invoice_id"]))

                applied_invoices.append({
                    "invoice_id": invoice["invoice_id"],
                    "invoice_number": invoice["invoice_number"],
                    "amount": amount,
                    "balance_remaining": new_balance
                })

            unapplied = round(total_amount - total_applied, 2)

            cursor.execute("""
                INSERT INTO genfin_payments_received
                (payment_id, payment_date, customer_id, deposit_account_id, payment_method,
                 reference_number, memo, total_amount, applied_invoices, unapplied_amount,
                 journal_entry_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payment_id, payment_date, customer_id, deposit_account_id, payment_method,
                reference_number, memo, total_amount, json.dumps(applied_invoices), unapplied,
                je_result["entry_id"], datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        return {
            "success": True,
            "payment_id": payment_id,
            "payment": self._get_payment(payment_id)
        }

    def _get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_payments_received WHERE payment_id = ?", (payment_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_payment_dict(row)

    def apply_payment_to_invoice(self, payment_id: str, invoice_id: str, amount: float) -> Dict:
        """Apply unapplied payment to an invoice"""
        payment = self._get_payment(payment_id)
        invoice = self.get_invoice(invoice_id)

        if not payment:
            return {"success": False, "error": "Payment not found"}
        if not invoice:
            return {"success": False, "error": "Invoice not found"}
        if payment["customer_id"] != invoice["customer_id"]:
            return {"success": False, "error": "Payment and invoice must be for the same customer"}
        if amount > payment["unapplied_amount"]:
            return {"success": False, "error": "Amount exceeds unapplied balance"}
        if amount > invoice["balance_due"]:
            return {"success": False, "error": "Amount exceeds invoice balance"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update invoice
            new_amount_paid = invoice["amount_paid"] + amount
            new_balance = round(invoice["total"] - new_amount_paid, 2)
            new_status = "paid" if new_balance == 0 else "partial"

            cursor.execute("""
                UPDATE genfin_invoices SET amount_paid = ?, balance_due = ?, status = ?, updated_at = ?
                WHERE invoice_id = ?
            """, (new_amount_paid, new_balance, new_status, datetime.now(timezone.utc).isoformat(), invoice_id))

            # Update payment
            applied_invoices = payment["applied_invoices"]
            applied_invoices.append({
                "invoice_id": invoice_id,
                "invoice_number": invoice["invoice_number"],
                "amount": amount,
                "balance_remaining": new_balance
            })
            new_unapplied = round(payment["unapplied_amount"] - amount, 2)

            cursor.execute("""
                UPDATE genfin_payments_received SET applied_invoices = ?, unapplied_amount = ?
                WHERE payment_id = ?
            """, (json.dumps(applied_invoices), new_unapplied, payment_id))

            conn.commit()

        return {
            "success": True,
            "payment_unapplied": new_unapplied,
            "invoice_balance": new_balance
        }

    def void_payment(self, payment_id: str, reason: str = "") -> Dict:
        """Void a payment received"""
        payment = self._get_payment(payment_id)
        if not payment:
            return {"success": False, "error": "Payment not found"}

        if payment["is_voided"]:
            return {"success": False, "error": "Payment is already voided"}

        if payment["journal_entry_id"]:
            genfin_core_service.reverse_journal_entry(payment["journal_entry_id"], date.today().isoformat())

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Reverse invoice applications
            for applied in payment["applied_invoices"]:
                invoice = self.get_invoice(applied["invoice_id"])
                if invoice:
                    new_amount_paid = invoice["amount_paid"] - applied["amount"]
                    new_balance = round(invoice["total"] - new_amount_paid, 2)
                    new_status = "sent" if new_balance == invoice["total"] else "partial"
                    if new_status == "sent" and datetime.strptime(invoice["due_date"], "%Y-%m-%d").date() < date.today():
                        new_status = "overdue"

                    cursor.execute("""
                        UPDATE genfin_invoices SET amount_paid = ?, balance_due = ?, status = ?
                        WHERE invoice_id = ?
                    """, (new_amount_paid, new_balance, new_status, applied["invoice_id"]))

            cursor.execute("UPDATE genfin_payments_received SET is_voided = 1 WHERE payment_id = ?", (payment_id,))
            conn.commit()

        return {"success": True, "message": "Payment voided successfully"}

    def list_payments(
        self,
        customer_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_voided: bool = False
    ) -> List[Dict]:
        """List payments received"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_payments_received WHERE 1=1"
            params = []

            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
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
            rows = cursor.fetchall()

            return [self._row_to_payment_dict(row) for row in rows]

    # ==================== CUSTOMER CREDITS ====================

    def create_customer_credit(
        self,
        customer_id: str,
        credit_date: str,
        lines: List[Dict],
        reason: str = "",
        memo: str = "",
        related_invoice_id: Optional[str] = None
    ) -> Dict:
        """Create a credit memo for customer"""
        if not self.get_customer(customer_id):
            return {"success": False, "error": "Customer not found"}

        credit_id = str(uuid.uuid4())
        credit_number = f"CRD-{self._get_next_number('next_credit_number'):05d}"
        total = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Process lines
            credit_lines = []
            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
                line_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO genfin_credit_lines
                    (line_id, credit_id, account_id, description, quantity, unit_price, amount, class_id, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    line_id, credit_id, line["account_id"], line.get("description", ""),
                    line.get("quantity", 1), line.get("unit_price", 0), line_amount,
                    line.get("class_id"), line.get("location_id")
                ))

                credit_lines.append({
                    "account_id": line["account_id"],
                    "description": line.get("description", ""),
                    "amount": line_amount,
                    "class_id": line.get("class_id"),
                    "location_id": line.get("location_id")
                })
                total += line_amount

            # Create journal entry
            journal_lines = [{
                "account_id": self.default_ar_account_id,
                "description": f"Credit Memo {credit_number}",
                "debit": 0,
                "credit": total,
                "customer_id": customer_id
            }]
            for cl in credit_lines:
                journal_lines.append({
                    "account_id": cl["account_id"],
                    "description": cl["description"],
                    "debit": cl["amount"],
                    "credit": 0,
                    "class_id": cl["class_id"],
                    "location_id": cl["location_id"]
                })

            je_result = genfin_core_service.create_journal_entry(
                entry_date=credit_date,
                lines=journal_lines,
                memo=f"Credit Memo {credit_number}",
                source_type="customer_credit",
                source_id=credit_id,
                auto_post=True
            )

            cursor.execute("""
                INSERT INTO genfin_customer_credits
                (credit_id, credit_number, customer_id, credit_date, reason, memo, total,
                 amount_applied, balance, journal_entry_id, related_invoice_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """, (
                credit_id, credit_number, customer_id, credit_date, reason, memo,
                round(total, 2), round(total, 2), je_result.get("entry_id"),
                related_invoice_id, datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        return {
            "success": True,
            "credit_id": credit_id,
            "credit_number": credit_number,
            "credit": self._get_credit(credit_id)
        }

    def _get_credit(self, credit_id: str) -> Optional[Dict]:
        """Get credit by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_customer_credits WHERE credit_id = ?", (credit_id,))
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT * FROM genfin_credit_lines WHERE credit_id = ?", (credit_id,))
            lines = cursor.fetchall()
            return self._row_to_credit_dict(row, lines)

    def apply_credit_to_invoice(self, credit_id: str, invoice_id: str, amount: float) -> Dict:
        """Apply customer credit to an invoice"""
        credit = self._get_credit(credit_id)
        invoice = self.get_invoice(invoice_id)

        if not credit:
            return {"success": False, "error": "Credit not found"}
        if not invoice:
            return {"success": False, "error": "Invoice not found"}
        if credit["customer_id"] != invoice["customer_id"]:
            return {"success": False, "error": "Credit and invoice must be for the same customer"}
        if amount > credit["balance"]:
            return {"success": False, "error": "Amount exceeds credit balance"}
        if amount > invoice["balance_due"]:
            return {"success": False, "error": "Amount exceeds invoice balance"}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update credit
            new_credit_applied = credit["amount_applied"] + amount
            new_credit_balance = round(credit["total"] - new_credit_applied, 2)
            new_credit_status = "applied" if new_credit_balance == 0 else "open"

            cursor.execute("""
                UPDATE genfin_customer_credits SET amount_applied = ?, balance = ?, status = ?
                WHERE credit_id = ?
            """, (new_credit_applied, new_credit_balance, new_credit_status, credit_id))

            # Update invoice
            new_invoice_paid = invoice["amount_paid"] + amount
            new_invoice_balance = round(invoice["total"] - new_invoice_paid, 2)
            new_invoice_status = "paid" if new_invoice_balance == 0 else "partial"

            cursor.execute("""
                UPDATE genfin_invoices SET amount_paid = ?, balance_due = ?, status = ?
                WHERE invoice_id = ?
            """, (new_invoice_paid, new_invoice_balance, new_invoice_status, invoice_id))

            conn.commit()

        return {
            "success": True,
            "credit_balance": new_credit_balance,
            "invoice_balance": new_invoice_balance
        }

    # ==================== ESTIMATES ====================

    def create_estimate(
        self,
        customer_id: str,
        estimate_date: str,
        lines: List[Dict],
        expiration_days: int = 30,
        po_number: str = "",
        terms: str = "",
        memo: str = "",
        message_to_customer: str = ""
    ) -> Dict:
        """Create an estimate/quote"""
        customer = self.get_customer(customer_id)
        if not customer:
            return {"success": False, "error": "Customer not found"}

        estimate_id = str(uuid.uuid4())
        estimate_number = f"EST-{self._get_next_number('next_estimate_number'):05d}"

        e_date = datetime.strptime(estimate_date, "%Y-%m-%d").date()
        exp_date = e_date + timedelta(days=expiration_days)

        subtotal = 0.0
        tax_total = 0.0
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
                tax_amount = line.get("tax_amount", 0)
                line_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO genfin_estimate_lines
                    (line_id, estimate_id, account_id, description, quantity, unit_price, amount, tax_amount, class_id, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    line_id, estimate_id, line.get("account_id", ""), line.get("description", ""),
                    line.get("quantity", 1), line.get("unit_price", 0), line_amount, tax_amount,
                    line.get("class_id"), line.get("location_id")
                ))

                subtotal += line_amount
                tax_total += tax_amount

            cursor.execute("""
                INSERT INTO genfin_estimates
                (estimate_id, estimate_number, customer_id, estimate_date, expiration_date,
                 po_number, terms, memo, message_to_customer, subtotal, tax_total, total,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
            """, (
                estimate_id, estimate_number, customer_id, estimate_date, exp_date.isoformat(),
                po_number, terms or customer['payment_terms'], memo, message_to_customer,
                round(subtotal, 2), round(tax_total, 2), round(subtotal + tax_total, 2), now, now
            ))
            conn.commit()

        return {
            "success": True,
            "estimate_id": estimate_id,
            "estimate_number": estimate_number,
            "estimate": self._get_estimate(estimate_id)
        }

    def _get_estimate(self, estimate_id: str) -> Optional[Dict]:
        """Get estimate by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_estimates WHERE estimate_id = ?", (estimate_id,))
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT * FROM genfin_estimate_lines WHERE estimate_id = ?", (estimate_id,))
            lines = cursor.fetchall()
            return self._row_to_estimate_dict(row, lines)

    def send_estimate(self, estimate_id: str) -> Dict:
        """Mark estimate as sent"""
        estimate = self._get_estimate(estimate_id)
        if not estimate:
            return {"success": False, "error": "Estimate not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_estimates SET status = 'sent', updated_at = ? WHERE estimate_id = ?
            """, (datetime.now(timezone.utc).isoformat(), estimate_id))
            conn.commit()

        return {"success": True, "estimate": self._get_estimate(estimate_id)}

    def accept_estimate(self, estimate_id: str) -> Dict:
        """Mark estimate as accepted"""
        estimate = self._get_estimate(estimate_id)
        if not estimate:
            return {"success": False, "error": "Estimate not found"}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE genfin_estimates SET status = 'accepted', accepted_date = ?, updated_at = ?
                WHERE estimate_id = ?
            """, (date.today().isoformat(), datetime.now(timezone.utc).isoformat(), estimate_id))
            conn.commit()

        return {"success": True, "estimate": self._get_estimate(estimate_id)}

    def convert_estimate_to_invoice(self, estimate_id: str, invoice_date: str) -> Dict:
        """Convert accepted estimate to invoice"""
        estimate = self._get_estimate(estimate_id)
        if not estimate:
            return {"success": False, "error": "Estimate not found"}

        if estimate["status"] not in ["accepted", "sent"]:
            return {"success": False, "error": "Estimate must be sent or accepted"}

        invoice_lines = []
        for line in estimate["lines"]:
            invoice_lines.append({
                "account_id": line["account_id"],
                "description": line["description"],
                "quantity": line["quantity"],
                "unit_price": line["unit_price"],
                "tax_amount": line["tax_amount"],
                "class_id": line["class_id"],
                "location_id": line["location_id"]
            })

        result = self.create_invoice(
            customer_id=estimate["customer_id"],
            invoice_date=invoice_date,
            lines=invoice_lines,
            po_number=estimate["po_number"],
            terms=estimate["terms"],
            memo=f"From Estimate {estimate['estimate_number']}",
            estimate_id=estimate_id
        )

        if result["success"]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE genfin_estimates SET status = 'converted', converted_invoice_id = ?, updated_at = ?
                    WHERE estimate_id = ?
                """, (result["invoice_id"], datetime.now(timezone.utc).isoformat(), estimate_id))
                conn.commit()

        return result

    def list_estimates(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List estimates"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM genfin_estimates WHERE 1=1"
            params = []

            if customer_id:
                query += " AND customer_id = ?"
                params.append(customer_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if start_date:
                query += " AND estimate_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND estimate_date <= ?"
                params.append(end_date)

            query += " ORDER BY estimate_date DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            result = []
            for row in rows:
                # Check for expiration
                if row['status'] == 'sent' and datetime.strptime(row['expiration_date'], "%Y-%m-%d").date() < date.today():
                    cursor.execute("UPDATE genfin_estimates SET status = 'expired' WHERE estimate_id = ?", (row['estimate_id'],))
                    conn.commit()

                cursor.execute("SELECT * FROM genfin_estimate_lines WHERE estimate_id = ?", (row['estimate_id'],))
                lines = cursor.fetchall()
                result.append(self._row_to_estimate_dict(row, lines))

            return result

    # ==================== SALES RECEIPTS ====================

    def create_sales_receipt(
        self,
        receipt_date: str,
        lines: List[Dict],
        payment_method: str,
        deposit_account_id: str,
        customer_id: Optional[str] = None,
        reference_number: str = "",
        memo: str = ""
    ) -> Dict:
        """Create a sales receipt (payment at time of sale)"""
        receipt_id = str(uuid.uuid4())
        receipt_number = f"SR-{self._get_next_number('next_receipt_number'):05d}"

        subtotal = 0.0
        tax_total = 0.0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            receipt_lines = []
            for line in lines:
                line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
                tax_amount = line.get("tax_amount", 0)
                line_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO genfin_sales_receipt_lines
                    (line_id, receipt_id, account_id, description, quantity, unit_price, amount, tax_amount, class_id, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    line_id, receipt_id, line["account_id"], line.get("description", ""),
                    line.get("quantity", 1), line.get("unit_price", 0), line_amount, tax_amount,
                    line.get("class_id"), line.get("location_id")
                ))

                receipt_lines.append({
                    "account_id": line["account_id"],
                    "description": line.get("description", ""),
                    "amount": line_amount,
                    "class_id": line.get("class_id"),
                    "location_id": line.get("location_id")
                })
                subtotal += line_amount
                tax_total += tax_amount

            total = subtotal + tax_total

            # Create journal entry
            journal_lines = [{
                "account_id": deposit_account_id,
                "description": f"Sales Receipt {receipt_number}",
                "debit": total,
                "credit": 0,
                "customer_id": customer_id
            }]

            for rl in receipt_lines:
                journal_lines.append({
                    "account_id": rl["account_id"],
                    "description": rl["description"],
                    "debit": 0,
                    "credit": rl["amount"],
                    "class_id": rl["class_id"],
                    "location_id": rl["location_id"]
                })

            if tax_total > 0:
                tax_account = genfin_core_service.get_account_by_number("2500")
                if tax_account:
                    journal_lines.append({
                        "account_id": tax_account["account_id"],
                        "description": f"Sales tax - {receipt_number}",
                        "debit": 0,
                        "credit": tax_total
                    })

            je_result = genfin_core_service.create_journal_entry(
                entry_date=receipt_date,
                lines=journal_lines,
                memo=f"Sales Receipt {receipt_number}",
                source_type="sales_receipt",
                source_id=receipt_id,
                auto_post=True
            )

            cursor.execute("""
                INSERT INTO genfin_sales_receipts
                (receipt_id, receipt_number, customer_id, receipt_date, payment_method, deposit_account_id,
                 reference_number, memo, subtotal, tax_total, total, journal_entry_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                receipt_id, receipt_number, customer_id, receipt_date, payment_method, deposit_account_id,
                reference_number, memo, round(subtotal, 2), round(tax_total, 2), round(total, 2),
                je_result.get("entry_id"), datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()

        return {
            "success": True,
            "receipt_id": receipt_id,
            "receipt_number": receipt_number,
            "receipt": self._get_receipt(receipt_id)
        }

    def _get_receipt(self, receipt_id: str) -> Optional[Dict]:
        """Get sales receipt by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM genfin_sales_receipts WHERE receipt_id = ?", (receipt_id,))
            row = cursor.fetchone()
            if not row:
                return None
            cursor.execute("SELECT * FROM genfin_sales_receipt_lines WHERE receipt_id = ?", (receipt_id,))
            lines = cursor.fetchall()
            return self._row_to_receipt_dict(row, lines)

    # ==================== REPORTS ====================

    def get_ar_aging(self, as_of_date: Optional[str] = None) -> Dict:
        """Generate accounts receivable aging report"""
        ref_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()

        aging = {
            "current": [], "1_30": [], "31_60": [], "61_90": [], "over_90": [],
            "totals": {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0, "total": 0}
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT i.*, c.display_name as customer_name
                FROM genfin_invoices i
                LEFT JOIN genfin_customers c ON i.customer_id = c.customer_id
                WHERE i.status IN ('sent', 'viewed', 'partial', 'overdue')
                AND i.invoice_date <= ?
            """, (ref_date.isoformat(),))
            rows = cursor.fetchall()

            for row in rows:
                days_old = (ref_date - datetime.strptime(row['due_date'], "%Y-%m-%d").date()).days
                entry = {
                    "invoice_id": row['invoice_id'],
                    "invoice_number": row['invoice_number'],
                    "customer_id": row['customer_id'],
                    "customer_name": row['customer_name'] or "Unknown",
                    "invoice_date": row['invoice_date'],
                    "due_date": row['due_date'],
                    "days_overdue": max(0, days_old),
                    "balance": row['balance_due']
                }

                if days_old <= 0:
                    aging["current"].append(entry)
                    aging["totals"]["current"] += row['balance_due']
                elif days_old <= 30:
                    aging["1_30"].append(entry)
                    aging["totals"]["1_30"] += row['balance_due']
                elif days_old <= 60:
                    aging["31_60"].append(entry)
                    aging["totals"]["31_60"] += row['balance_due']
                elif days_old <= 90:
                    aging["61_90"].append(entry)
                    aging["totals"]["61_90"] += row['balance_due']
                else:
                    aging["over_90"].append(entry)
                    aging["totals"]["over_90"] += row['balance_due']

                aging["totals"]["total"] += row['balance_due']

        for key in aging["totals"]:
            aging["totals"][key] = round(aging["totals"][key], 2)

        return {"as_of_date": ref_date.isoformat(), "aging": aging}

    def get_customer_statement(self, customer_id: str, start_date: str, end_date: str) -> Dict:
        """Generate customer statement"""
        customer = self.get_customer(customer_id)
        if not customer:
            return {"error": "Customer not found"}

        _s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        _e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        opening_balance = customer.get("opening_balance", 0) or 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Invoices before period
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) as total FROM genfin_invoices
                WHERE customer_id = ? AND status != 'voided' AND invoice_date < ?
            """, (customer_id, start_date))
            opening_balance += cursor.fetchone()['total']

            # Payments before period
            cursor.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as total FROM genfin_payments_received
                WHERE customer_id = ? AND is_voided = 0 AND payment_date < ?
            """, (customer_id, start_date))
            opening_balance -= cursor.fetchone()['total']

            # Collect transactions
            all_trans = []

            cursor.execute("""
                SELECT * FROM genfin_invoices WHERE customer_id = ? AND status != 'voided'
                AND invoice_date >= ? AND invoice_date <= ?
            """, (customer_id, start_date, end_date))
            for row in cursor.fetchall():
                all_trans.append({
                    "date": row['invoice_date'],
                    "type": "Invoice",
                    "number": row['invoice_number'],
                    "description": row['memo'] or f"Invoice {row['invoice_number']}",
                    "amount": row['total'],
                    "payment": 0
                })

            cursor.execute("""
                SELECT * FROM genfin_payments_received WHERE customer_id = ? AND is_voided = 0
                AND payment_date >= ? AND payment_date <= ?
            """, (customer_id, start_date, end_date))
            for row in cursor.fetchall():
                all_trans.append({
                    "date": row['payment_date'],
                    "type": "Payment",
                    "number": row['reference_number'] or row['payment_id'][:8],
                    "description": row['memo'] or "Payment received",
                    "amount": 0,
                    "payment": row['total_amount']
                })

        all_trans.sort(key=lambda t: t["date"])

        transactions = []
        running_balance = opening_balance
        for trans in all_trans:
            running_balance += trans["amount"] - trans["payment"]
            transactions.append({
                "date": trans["date"],
                "type": trans["type"],
                "number": trans["number"],
                "description": trans["description"],
                "charges": trans["amount"],
                "payments": trans["payment"],
                "balance": round(running_balance, 2)
            })

        return {
            "customer": customer,
            "statement_date": date.today().isoformat(),
            "period_start": start_date,
            "period_end": end_date,
            "opening_balance": round(opening_balance, 2),
            "transactions": transactions,
            "ending_balance": round(running_balance, 2),
            "total_charges": sum(t["charges"] for t in transactions),
            "total_payments": sum(t["payments"] for t in transactions)
        }

    def get_sales_summary(self, start_date: str, end_date: str) -> Dict:
        """Get sales summary for period"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total), 0) as total
                FROM genfin_invoices WHERE status != 'voided'
                AND invoice_date >= ? AND invoice_date <= ?
            """, (start_date, end_date))
            inv_row = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total), 0) as total
                FROM genfin_sales_receipts WHERE is_voided = 0
                AND receipt_date >= ? AND receipt_date <= ?
            """, (start_date, end_date))
            rec_row = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM genfin_payments_received WHERE is_voided = 0
                AND payment_date >= ? AND payment_date <= ?
            """, (start_date, end_date))
            pay_row = cursor.fetchone()

            # Top customers
            cursor.execute("""
                SELECT c.display_name, SUM(i.total) as total
                FROM genfin_invoices i
                JOIN genfin_customers c ON i.customer_id = c.customer_id
                WHERE i.status != 'voided' AND i.invoice_date >= ? AND i.invoice_date <= ?
                GROUP BY i.customer_id ORDER BY total DESC LIMIT 10
            """, (start_date, end_date))
            top_customers = [{"customer": row['display_name'], "total": round(row['total'], 2)} for row in cursor.fetchall()]

        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_invoiced": round(inv_row['total'], 2),
            "invoice_count": inv_row['count'],
            "total_receipts": round(rec_row['total'], 2),
            "receipt_count": rec_row['count'],
            "total_sales": round(inv_row['total'] + rec_row['total'], 2),
            "payments_received": round(pay_row['total'], 2),
            "payment_count": pay_row['count'],
            "top_customers": top_customers
        }

    # ==================== UTILITY METHODS ====================

    def _row_to_customer_dict(self, row: sqlite3.Row) -> Dict:
        return {
            "customer_id": row['customer_id'],
            "company_name": row['company_name'],
            "display_name": row['display_name'],
            "contact_name": row['contact_name'] or "",
            "email": row['email'] or "",
            "phone": row['phone'] or "",
            "mobile": row['mobile'] or "",
            "website": row['website'] or "",
            "billing_address": {
                "line1": row['billing_address_line1'] or "",
                "line2": row['billing_address_line2'] or "",
                "city": row['billing_city'] or "",
                "state": row['billing_state'] or "",
                "zip": row['billing_zip'] or "",
                "country": row['billing_country'] or "USA"
            },
            "shipping_address": {
                "line1": row['shipping_address_line1'] or "",
                "line2": row['shipping_address_line2'] or "",
                "city": row['shipping_city'] or "",
                "state": row['shipping_state'] or "",
                "zip": row['shipping_zip'] or "",
                "country": row['shipping_country'] or "USA"
            },
            "tax_exempt": bool(row['tax_exempt']),
            "tax_id": row['tax_id'] or "",
            "default_income_account_id": row['default_income_account_id'],
            "payment_terms": row['payment_terms'] or "Net 30",
            "credit_limit": row['credit_limit'] or 0.0,
            "customer_type": row['customer_type'] or "",
            "notes": row['notes'] or "",
            "status": row['status'] or "active",
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    def _row_to_invoice_dict(self, row: sqlite3.Row, lines: List[sqlite3.Row]) -> Dict:
        customer = self.get_customer(row['customer_id'])
        return {
            "invoice_id": row['invoice_id'],
            "invoice_number": row['invoice_number'],
            "customer_id": row['customer_id'],
            "customer_name": customer['display_name'] if customer else "Unknown",
            "invoice_date": row['invoice_date'],
            "due_date": row['due_date'],
            "po_number": row['po_number'] or "",
            "terms": row['terms'] or "Net 30",
            "memo": row['memo'] or "",
            "message_on_invoice": row['message_on_invoice'] or "",
            "billing_address": row['billing_address'] or "",
            "shipping_address": row['shipping_address'] or "",
            "lines": [{
                "line_id": line['line_id'],
                "account_id": line['account_id'],
                "description": line['description'] or "",
                "quantity": line['quantity'] or 1,
                "unit_price": line['unit_price'] or 0,
                "amount": line['amount'] or 0,
                "tax_code": line['tax_code'],
                "tax_amount": line['tax_amount'] or 0,
                "discount_percent": line['discount_percent'] or 0,
                "discount_amount": line['discount_amount'] or 0,
                "class_id": line['class_id'],
                "location_id": line['location_id'],
                "service_date": line['service_date']
            } for line in lines],
            "subtotal": row['subtotal'] or 0,
            "discount_total": row['discount_total'] or 0,
            "tax_total": row['tax_total'] or 0,
            "total": row['total'] or 0,
            "amount_paid": row['amount_paid'] or 0,
            "balance_due": row['balance_due'] or 0,
            "status": row['status'] or "draft",
            "ar_account_id": row['ar_account_id'],
            "email_sent": bool(row['email_sent']),
            "email_sent_date": row['email_sent_date'],
            "estimate_id": row['estimate_id'],
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    def _row_to_payment_dict(self, row: sqlite3.Row) -> Dict:
        customer = self.get_customer(row['customer_id'])
        return {
            "payment_id": row['payment_id'],
            "payment_date": row['payment_date'],
            "customer_id": row['customer_id'],
            "customer_name": customer['display_name'] if customer else "Unknown",
            "deposit_account_id": row['deposit_account_id'],
            "payment_method": row['payment_method'],
            "reference_number": row['reference_number'] or "",
            "memo": row['memo'] or "",
            "total_amount": row['total_amount'] or 0,
            "applied_invoices": json.loads(row['applied_invoices']) if row['applied_invoices'] else [],
            "unapplied_amount": row['unapplied_amount'] or 0,
            "is_voided": bool(row['is_voided']),
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at']
        }

    def _row_to_credit_dict(self, row: sqlite3.Row, lines: List[sqlite3.Row]) -> Dict:
        customer = self.get_customer(row['customer_id'])
        return {
            "credit_id": row['credit_id'],
            "credit_number": row['credit_number'],
            "customer_id": row['customer_id'],
            "customer_name": customer['display_name'] if customer else "Unknown",
            "credit_date": row['credit_date'],
            "reason": row['reason'] or "",
            "memo": row['memo'] or "",
            "lines": [{
                "line_id": line['line_id'],
                "account_id": line['account_id'],
                "description": line['description'] or "",
                "quantity": line['quantity'] or 1,
                "unit_price": line['unit_price'] or 0,
                "amount": line['amount'] or 0
            } for line in lines],
            "total": row['total'] or 0,
            "amount_applied": row['amount_applied'] or 0,
            "balance": row['balance'] or 0,
            "status": row['status'] or "open",
            "related_invoice_id": row['related_invoice_id'],
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at']
        }

    def _row_to_estimate_dict(self, row: sqlite3.Row, lines: List[sqlite3.Row]) -> Dict:
        customer = self.get_customer(row['customer_id'])
        return {
            "estimate_id": row['estimate_id'],
            "estimate_number": row['estimate_number'],
            "customer_id": row['customer_id'],
            "customer_name": customer['display_name'] if customer else "Unknown",
            "estimate_date": row['estimate_date'],
            "expiration_date": row['expiration_date'],
            "po_number": row['po_number'] or "",
            "terms": row['terms'] or "",
            "memo": row['memo'] or "",
            "message_to_customer": row['message_to_customer'] or "",
            "lines": [{
                "line_id": line['line_id'],
                "account_id": line['account_id'] or "",
                "description": line['description'] or "",
                "quantity": line['quantity'] or 1,
                "unit_price": line['unit_price'] or 0,
                "amount": line['amount'] or 0,
                "tax_amount": line['tax_amount'] or 0
            } for line in lines],
            "subtotal": row['subtotal'] or 0,
            "tax_total": row['tax_total'] or 0,
            "total": row['total'] or 0,
            "status": row['status'] or "draft",
            "accepted_date": row['accepted_date'],
            "converted_invoice_id": row['converted_invoice_id'],
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }

    def _row_to_receipt_dict(self, row: sqlite3.Row, lines: List[sqlite3.Row]) -> Dict:
        customer_name = None
        if row['customer_id']:
            customer = self.get_customer(row['customer_id'])
            customer_name = customer['display_name'] if customer else None

        return {
            "receipt_id": row['receipt_id'],
            "receipt_number": row['receipt_number'],
            "customer_id": row['customer_id'],
            "customer_name": customer_name,
            "receipt_date": row['receipt_date'],
            "payment_method": row['payment_method'],
            "deposit_account_id": row['deposit_account_id'],
            "reference_number": row['reference_number'] or "",
            "memo": row['memo'] or "",
            "lines": [{
                "line_id": line['line_id'],
                "account_id": line['account_id'],
                "description": line['description'] or "",
                "quantity": line['quantity'] or 1,
                "unit_price": line['unit_price'] or 0,
                "amount": line['amount'] or 0,
                "tax_amount": line['tax_amount'] or 0
            } for line in lines],
            "subtotal": row['subtotal'] or 0,
            "tax_total": row['tax_total'] or 0,
            "total": row['total'] or 0,
            "is_voided": bool(row['is_voided']),
            "journal_entry_id": row['journal_entry_id'],
            "created_at": row['created_at']
        }

    def get_service_summary(self) -> Dict:
        """Get GenFin Receivables service summary"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM genfin_customers")
            total_customers = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_customers WHERE status = 'active'")
            active_customers = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_invoices")
            total_invoices = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_invoices WHERE status IN ('sent', 'viewed', 'partial', 'overdue')")
            open_invoices = cursor.fetchone()['total']

            cursor.execute("SELECT COALESCE(SUM(balance_due), 0) as total FROM genfin_invoices WHERE status IN ('sent', 'viewed', 'partial', 'overdue')")
            total_outstanding = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_payments_received")
            total_payments = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_customer_credits")
            total_credits = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_estimates")
            total_estimates = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as total FROM genfin_sales_receipts")
            total_receipts = cursor.fetchone()['total']

        return {
            "service": "GenFin Receivables",
            "version": "1.0.0",
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_invoices": total_invoices,
            "open_invoices": open_invoices,
            "total_outstanding": round(total_outstanding, 2),
            "total_payments": total_payments,
            "total_credits": total_credits,
            "total_estimates": total_estimates,
            "total_sales_receipts": total_receipts
        }


# Singleton instance
genfin_receivables_service = GenFinReceivablesService()
