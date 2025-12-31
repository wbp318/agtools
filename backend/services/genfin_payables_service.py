"""
GenFin Payables Service - Vendors, Bills, Payments, Purchase Orders
Complete accounts payable management for farm operations
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid

from .genfin_core_service import genfin_core_service, TransactionStatus


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


@dataclass
class Vendor:
    """Vendor/Supplier record"""
    vendor_id: str
    company_name: str
    display_name: str
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    fax: str = ""
    website: str = ""

    # Address
    billing_address_line1: str = ""
    billing_address_line2: str = ""
    billing_city: str = ""
    billing_state: str = ""
    billing_zip: str = ""
    billing_country: str = "USA"

    # Tax info
    tax_id: str = ""  # EIN or SSN
    is_1099_vendor: bool = False
    default_expense_account_id: Optional[str] = None

    # Terms
    payment_terms: str = "Net 30"
    credit_limit: float = 0.0

    # Tracking
    vendor_type: str = ""  # Supplier, Contractor, Service Provider
    notes: str = ""
    status: VendorStatus = VendorStatus.ACTIVE
    opening_balance: float = 0.0
    opening_balance_date: Optional[date] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BillLine:
    """Line item on a bill"""
    line_id: str
    account_id: str
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0
    tax_code: Optional[str] = None
    tax_amount: float = 0.0
    billable: bool = False
    customer_id: Optional[str] = None
    class_id: Optional[str] = None
    location_id: Optional[str] = None


@dataclass
class Bill:
    """Vendor bill/invoice"""
    bill_id: str
    bill_number: str
    vendor_id: str
    bill_date: date
    due_date: date
    lines: List[BillLine]

    reference_number: str = ""  # Vendor's invoice number
    terms: str = "Net 30"
    memo: str = ""

    subtotal: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0
    amount_paid: float = 0.0
    balance_due: float = 0.0

    status: BillStatus = BillStatus.DRAFT
    ap_account_id: Optional[str] = None
    journal_entry_id: Optional[str] = None

    purchase_order_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BillPayment:
    """Payment applied to bills"""
    payment_id: str
    payment_date: date
    vendor_id: str
    bank_account_id: str
    payment_method: PaymentMethod
    reference_number: str = ""  # Check number, transaction ID
    memo: str = ""
    total_amount: float = 0.0
    applied_bills: List[Dict] = field(default_factory=list)  # [{bill_id, amount}]
    journal_entry_id: Optional[str] = None
    is_voided: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class VendorCredit:
    """Credit memo from vendor"""
    credit_id: str
    credit_number: str
    vendor_id: str
    credit_date: date
    lines: List[BillLine]

    reference_number: str = ""
    memo: str = ""
    total: float = 0.0
    amount_applied: float = 0.0
    balance: float = 0.0

    status: str = "open"  # open, applied, closed
    journal_entry_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PurchaseOrderLine:
    """Line item on a purchase order"""
    line_id: str
    item_description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0
    quantity_received: float = 0.0
    account_id: Optional[str] = None
    class_id: Optional[str] = None


@dataclass
class PurchaseOrder:
    """Purchase order"""
    po_id: str
    po_number: str
    vendor_id: str
    order_date: date
    expected_date: Optional[date]
    lines: List[PurchaseOrderLine]

    ship_to_address: str = ""
    memo: str = ""
    terms: str = ""

    subtotal: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0

    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    approved_by: Optional[str] = None
    approved_date: Optional[date] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


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
    GenFin Accounts Payable Service

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.vendors: Dict[str, Vendor] = {}
        self.bills: Dict[str, Bill] = {}
        self.payments: Dict[str, BillPayment] = {}
        self.credits: Dict[str, VendorCredit] = {}
        self.purchase_orders: Dict[str, PurchaseOrder] = {}

        self.next_bill_number = 1
        self.next_po_number = 1
        self.next_credit_number = 1

        # Default AP account
        self.default_ap_account_id = self._get_default_ap_account()

        self._initialized = True

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

        ob_date = None
        if opening_balance_date:
            ob_date = datetime.strptime(opening_balance_date, "%Y-%m-%d").date()

        vendor = Vendor(
            vendor_id=vendor_id,
            company_name=company_name,
            display_name=display_name or company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            billing_address_line1=billing_address_line1,
            billing_city=billing_city,
            billing_state=billing_state,
            billing_zip=billing_zip,
            tax_id=tax_id,
            is_1099_vendor=is_1099_vendor,
            payment_terms=payment_terms,
            vendor_type=vendor_type,
            default_expense_account_id=default_expense_account_id,
            opening_balance=opening_balance,
            opening_balance_date=ob_date
        )

        self.vendors[vendor_id] = vendor

        return {
            "success": True,
            "vendor_id": vendor_id,
            "vendor": self._vendor_to_dict(vendor)
        }

    def update_vendor(self, vendor_id: str, **kwargs) -> Dict:
        """Update vendor information"""
        if vendor_id not in self.vendors:
            return {"success": False, "error": "Vendor not found"}

        vendor = self.vendors[vendor_id]

        for key, value in kwargs.items():
            if hasattr(vendor, key) and value is not None:
                setattr(vendor, key, value)

        vendor.updated_at = datetime.now()

        return {
            "success": True,
            "vendor": self._vendor_to_dict(vendor)
        }

    def delete_vendor(self, vendor_id: str) -> bool:
        """Delete a vendor"""
        if vendor_id not in self.vendors:
            return False
        del self.vendors[vendor_id]
        return True

    def get_vendor(self, vendor_id: str) -> Optional[Dict]:
        """Get vendor by ID"""
        if vendor_id not in self.vendors:
            return None
        return self._vendor_to_dict(self.vendors[vendor_id])

    def list_vendors(
        self,
        status: Optional[str] = None,
        vendor_type: Optional[str] = None,
        is_1099: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """List vendors with filtering"""
        result = []

        for vendor in self.vendors.values():
            if status and vendor.status.value != status:
                continue
            if vendor_type and vendor.vendor_type != vendor_type:
                continue
            if is_1099 is not None and vendor.is_1099_vendor != is_1099:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in vendor.company_name.lower() and
                    search_lower not in vendor.display_name.lower() and
                    search_lower not in vendor.contact_name.lower()):
                    continue

            vendor_dict = self._vendor_to_dict(vendor)
            vendor_dict["balance"] = self.get_vendor_balance(vendor.vendor_id)
            result.append(vendor_dict)

        return sorted(result, key=lambda v: v["display_name"])

    def get_vendor_balance(self, vendor_id: str) -> float:
        """Calculate vendor balance (amount owed)"""
        balance = 0.0

        # Add opening balance
        if vendor_id in self.vendors:
            balance = self.vendors[vendor_id].opening_balance

        # Add unpaid bills
        for bill in self.bills.values():
            if bill.vendor_id == vendor_id and bill.status in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE]:
                balance += bill.balance_due

        # Subtract unapplied credits
        for credit in self.credits.values():
            if credit.vendor_id == vendor_id and credit.status == "open":
                balance -= credit.balance

        return round(balance, 2)

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
        if vendor_id not in self.vendors:
            return {"success": False, "error": "Vendor not found"}

        bill_id = str(uuid.uuid4())
        bill_number = f"BILL-{self.next_bill_number:05d}"
        self.next_bill_number += 1

        # Parse date and calculate due date
        b_date = datetime.strptime(bill_date, "%Y-%m-%d").date()
        days = PAYMENT_TERMS.get(terms, 30)
        d_date = b_date + timedelta(days=days)

        # Process lines
        bill_lines = []
        subtotal = 0.0
        tax_total = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
            tax_amount = line.get("tax_amount", 0)

            bill_lines.append(BillLine(
                line_id=str(uuid.uuid4()),
                account_id=line["account_id"],
                description=line.get("description", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line_amount,
                tax_code=line.get("tax_code"),
                tax_amount=tax_amount,
                billable=line.get("billable", False),
                customer_id=line.get("customer_id"),
                class_id=line.get("class_id"),
                location_id=line.get("location_id")
            ))

            subtotal += line_amount
            tax_total += tax_amount

        total = subtotal + tax_total

        bill = Bill(
            bill_id=bill_id,
            bill_number=bill_number,
            vendor_id=vendor_id,
            bill_date=b_date,
            due_date=d_date,
            lines=bill_lines,
            reference_number=reference_number,
            terms=terms,
            memo=memo,
            subtotal=round(subtotal, 2),
            tax_total=round(tax_total, 2),
            total=round(total, 2),
            amount_paid=0.0,
            balance_due=round(total, 2),
            status=BillStatus.DRAFT,
            ap_account_id=ap_account_id or self.default_ap_account_id,
            purchase_order_id=purchase_order_id
        )

        self.bills[bill_id] = bill

        return {
            "success": True,
            "bill_id": bill_id,
            "bill_number": bill_number,
            "bill": self._bill_to_dict(bill)
        }

    def post_bill(self, bill_id: str) -> Dict:
        """Post a bill - create journal entry and change status to open"""
        if bill_id not in self.bills:
            return {"success": False, "error": "Bill not found"}

        bill = self.bills[bill_id]

        if bill.status != BillStatus.DRAFT:
            return {"success": False, "error": "Bill is not in draft status"}

        # Create journal entry
        # Credit AP, Debit expense accounts
        journal_lines = []

        for line in bill.lines:
            journal_lines.append({
                "account_id": line.account_id,
                "description": line.description,
                "debit": line.amount + line.tax_amount,
                "credit": 0,
                "class_id": line.class_id,
                "location_id": line.location_id,
                "vendor_id": bill.vendor_id
            })

        journal_lines.append({
            "account_id": bill.ap_account_id,
            "description": f"Bill {bill.bill_number} - {self.vendors[bill.vendor_id].display_name}",
            "debit": 0,
            "credit": bill.total,
            "vendor_id": bill.vendor_id
        })

        je_result = genfin_core_service.create_journal_entry(
            entry_date=bill.bill_date.isoformat(),
            lines=journal_lines,
            memo=f"Bill {bill.bill_number} - {bill.reference_number}",
            source_type="bill",
            source_id=bill_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        bill.journal_entry_id = je_result["entry_id"]
        bill.status = BillStatus.OPEN
        bill.updated_at = datetime.now()

        # Check if overdue
        if bill.due_date < date.today():
            bill.status = BillStatus.OVERDUE

        return {
            "success": True,
            "bill": self._bill_to_dict(bill),
            "journal_entry_id": je_result["entry_id"]
        }

    def void_bill(self, bill_id: str, reason: str = "") -> Dict:
        """Void a bill"""
        if bill_id not in self.bills:
            return {"success": False, "error": "Bill not found"}

        bill = self.bills[bill_id]

        if bill.amount_paid > 0:
            return {"success": False, "error": "Cannot void bill with payments applied"}

        # Void journal entry if exists
        if bill.journal_entry_id:
            genfin_core_service.void_journal_entry(bill.journal_entry_id, reason)

        bill.status = BillStatus.VOIDED
        bill.memo = f"{bill.memo} [VOIDED: {reason}]"
        bill.updated_at = datetime.now()

        return {
            "success": True,
            "bill": self._bill_to_dict(bill)
        }

    def get_bill(self, bill_id: str) -> Optional[Dict]:
        """Get bill by ID"""
        if bill_id not in self.bills:
            return None
        return self._bill_to_dict(self.bills[bill_id])

    def delete_bill(self, bill_id: str) -> bool:
        """Delete a bill"""
        if bill_id not in self.bills:
            return False
        del self.bills[bill_id]
        return True

    def list_bills(
        self,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        unpaid_only: bool = False
    ) -> List[Dict]:
        """List bills with filtering"""
        result = []

        for bill in self.bills.values():
            if vendor_id and bill.vendor_id != vendor_id:
                continue
            if status and bill.status.value != status:
                continue
            if start_date:
                if bill.bill_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if bill.bill_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue
            if unpaid_only and bill.status not in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE]:
                continue

            result.append(self._bill_to_dict(bill))

        return sorted(result, key=lambda b: b["bill_date"], reverse=True)

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
        if vendor_id not in self.vendors:
            return {"success": False, "error": "Vendor not found"}

        # Validate bills and amounts
        total_payment = 0.0
        for bill_payment in bills_to_pay:
            bill_id = bill_payment["bill_id"]
            amount = bill_payment["amount"]

            if bill_id not in self.bills:
                return {"success": False, "error": f"Bill {bill_id} not found"}

            bill = self.bills[bill_id]
            if bill.vendor_id != vendor_id:
                return {"success": False, "error": f"Bill {bill.bill_number} does not belong to this vendor"}
            if bill.status not in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE]:
                return {"success": False, "error": f"Bill {bill.bill_number} is not payable"}
            if amount > bill.balance_due:
                return {"success": False, "error": f"Payment amount exceeds balance on {bill.bill_number}"}

            total_payment += amount

        payment_id = str(uuid.uuid4())
        p_date = datetime.strptime(payment_date, "%Y-%m-%d").date()

        # Create journal entry
        # Debit AP, Credit Bank
        journal_lines = [
            {
                "account_id": self.default_ap_account_id,
                "description": f"Payment to {self.vendors[vendor_id].display_name}",
                "debit": total_payment,
                "credit": 0,
                "vendor_id": vendor_id
            },
            {
                "account_id": bank_account_id,
                "description": f"Payment to {self.vendors[vendor_id].display_name}",
                "debit": 0,
                "credit": total_payment,
                "vendor_id": vendor_id
            }
        ]

        je_result = genfin_core_service.create_journal_entry(
            entry_date=payment_date,
            lines=journal_lines,
            memo=f"Payment: {reference_number}" if reference_number else f"Payment to {self.vendors[vendor_id].display_name}",
            source_type="bill_payment",
            source_id=payment_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        # Apply payments to bills
        applied_bills = []
        for bill_payment in bills_to_pay:
            bill = self.bills[bill_payment["bill_id"]]
            amount = bill_payment["amount"]

            bill.amount_paid += amount
            bill.balance_due = round(bill.total - bill.amount_paid, 2)

            if bill.balance_due == 0:
                bill.status = BillStatus.PAID
            else:
                bill.status = BillStatus.PARTIAL

            bill.updated_at = datetime.now()

            applied_bills.append({
                "bill_id": bill.bill_id,
                "bill_number": bill.bill_number,
                "amount": amount,
                "balance_remaining": bill.balance_due
            })

        payment = BillPayment(
            payment_id=payment_id,
            payment_date=p_date,
            vendor_id=vendor_id,
            bank_account_id=bank_account_id,
            payment_method=PaymentMethod(payment_method),
            reference_number=reference_number,
            memo=memo,
            total_amount=total_payment,
            applied_bills=applied_bills,
            journal_entry_id=je_result["entry_id"]
        )

        self.payments[payment_id] = payment

        return {
            "success": True,
            "payment_id": payment_id,
            "payment": self._payment_to_dict(payment)
        }

    def void_payment(self, payment_id: str, reason: str = "") -> Dict:
        """Void a bill payment"""
        if payment_id not in self.payments:
            return {"success": False, "error": "Payment not found"}

        payment = self.payments[payment_id]

        if payment.is_voided:
            return {"success": False, "error": "Payment is already voided"}

        # Reverse journal entry
        if payment.journal_entry_id:
            genfin_core_service.reverse_journal_entry(
                payment.journal_entry_id,
                date.today().isoformat()
            )

        # Reverse bill applications
        for applied in payment.applied_bills:
            if applied["bill_id"] in self.bills:
                bill = self.bills[applied["bill_id"]]
                bill.amount_paid -= applied["amount"]
                bill.balance_due = round(bill.total - bill.amount_paid, 2)

                if bill.balance_due == bill.total:
                    bill.status = BillStatus.OPEN
                    if bill.due_date < date.today():
                        bill.status = BillStatus.OVERDUE
                else:
                    bill.status = BillStatus.PARTIAL

        payment.is_voided = True

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
        result = []

        for payment in self.payments.values():
            if vendor_id and payment.vendor_id != vendor_id:
                continue
            if not include_voided and payment.is_voided:
                continue
            if start_date:
                if payment.payment_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if payment.payment_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            result.append(self._payment_to_dict(payment))

        return sorted(result, key=lambda p: p["payment_date"], reverse=True)

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
        if vendor_id not in self.vendors:
            return {"success": False, "error": "Vendor not found"}

        credit_id = str(uuid.uuid4())
        credit_number = f"VCRD-{self.next_credit_number:05d}"
        self.next_credit_number += 1

        c_date = datetime.strptime(credit_date, "%Y-%m-%d").date()

        # Process lines
        credit_lines = []
        total = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)

            credit_lines.append(BillLine(
                line_id=str(uuid.uuid4()),
                account_id=line["account_id"],
                description=line.get("description", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line_amount,
                class_id=line.get("class_id"),
                location_id=line.get("location_id")
            ))

            total += line_amount

        # Create journal entry (reverse of bill)
        # Debit AP, Credit expense accounts
        journal_lines = []

        for line in credit_lines:
            journal_lines.append({
                "account_id": line.account_id,
                "description": line.description,
                "debit": 0,
                "credit": line.amount,
                "class_id": line.class_id,
                "location_id": line.location_id
            })

        journal_lines.append({
            "account_id": self.default_ap_account_id,
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

        credit = VendorCredit(
            credit_id=credit_id,
            credit_number=credit_number,
            vendor_id=vendor_id,
            credit_date=c_date,
            lines=credit_lines,
            reference_number=reference_number,
            memo=memo,
            total=round(total, 2),
            amount_applied=0.0,
            balance=round(total, 2),
            journal_entry_id=je_result.get("entry_id")
        )

        self.credits[credit_id] = credit

        return {
            "success": True,
            "credit_id": credit_id,
            "credit_number": credit_number,
            "credit": self._credit_to_dict(credit)
        }

    def apply_credit_to_bill(self, credit_id: str, bill_id: str, amount: float) -> Dict:
        """Apply vendor credit to a bill"""
        if credit_id not in self.credits:
            return {"success": False, "error": "Credit not found"}
        if bill_id not in self.bills:
            return {"success": False, "error": "Bill not found"}

        credit = self.credits[credit_id]
        bill = self.bills[bill_id]

        if credit.vendor_id != bill.vendor_id:
            return {"success": False, "error": "Credit and bill must be for the same vendor"}
        if amount > credit.balance:
            return {"success": False, "error": "Amount exceeds credit balance"}
        if amount > bill.balance_due:
            return {"success": False, "error": "Amount exceeds bill balance"}

        # Apply credit
        credit.amount_applied += amount
        credit.balance = round(credit.total - credit.amount_applied, 2)
        if credit.balance == 0:
            credit.status = "applied"

        bill.amount_paid += amount
        bill.balance_due = round(bill.total - bill.amount_paid, 2)
        if bill.balance_due == 0:
            bill.status = BillStatus.PAID
        else:
            bill.status = BillStatus.PARTIAL

        return {
            "success": True,
            "credit_balance": credit.balance,
            "bill_balance": bill.balance_due
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
        if vendor_id not in self.vendors:
            return {"success": False, "error": "Vendor not found"}

        po_id = str(uuid.uuid4())
        po_number = f"PO-{self.next_po_number:05d}"
        self.next_po_number += 1

        o_date = datetime.strptime(order_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(expected_date, "%Y-%m-%d").date() if expected_date else None

        # Process lines
        po_lines = []
        subtotal = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)

            po_lines.append(PurchaseOrderLine(
                line_id=str(uuid.uuid4()),
                item_description=line.get("description", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line_amount,
                account_id=line.get("account_id"),
                class_id=line.get("class_id")
            ))

            subtotal += line_amount

        po = PurchaseOrder(
            po_id=po_id,
            po_number=po_number,
            vendor_id=vendor_id,
            order_date=o_date,
            expected_date=e_date,
            lines=po_lines,
            ship_to_address=ship_to_address,
            memo=memo,
            terms=terms or self.vendors[vendor_id].payment_terms,
            subtotal=round(subtotal, 2),
            total=round(subtotal, 2),
            status=PurchaseOrderStatus.DRAFT
        )

        self.purchase_orders[po_id] = po

        return {
            "success": True,
            "po_id": po_id,
            "po_number": po_number,
            "purchase_order": self._po_to_dict(po)
        }

    def approve_purchase_order(self, po_id: str, approved_by: str) -> Dict:
        """Approve a purchase order"""
        if po_id not in self.purchase_orders:
            return {"success": False, "error": "Purchase order not found"}

        po = self.purchase_orders[po_id]

        if po.status != PurchaseOrderStatus.DRAFT and po.status != PurchaseOrderStatus.PENDING:
            return {"success": False, "error": "Cannot approve PO in current status"}

        po.status = PurchaseOrderStatus.APPROVED
        po.approved_by = approved_by
        po.approved_date = date.today()
        po.updated_at = datetime.now()

        return {
            "success": True,
            "purchase_order": self._po_to_dict(po)
        }

    def receive_purchase_order(self, po_id: str, lines_received: List[Dict]) -> Dict:
        """Record receipt of items on a purchase order"""
        if po_id not in self.purchase_orders:
            return {"success": False, "error": "Purchase order not found"}

        po = self.purchase_orders[po_id]

        if po.status not in [PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.PARTIAL]:
            return {"success": False, "error": "PO must be approved before receiving"}

        # Update quantities received
        all_received = True
        for receipt in lines_received:
            line_id = receipt["line_id"]
            qty = receipt["quantity_received"]

            for line in po.lines:
                if line.line_id == line_id:
                    line.quantity_received += qty
                    if line.quantity_received < line.quantity:
                        all_received = False
                    break

        if all_received:
            po.status = PurchaseOrderStatus.RECEIVED
        else:
            po.status = PurchaseOrderStatus.PARTIAL

        po.updated_at = datetime.now()

        return {
            "success": True,
            "status": po.status.value,
            "purchase_order": self._po_to_dict(po)
        }

    def convert_po_to_bill(self, po_id: str, bill_date: str, reference_number: str = "") -> Dict:
        """Convert a received purchase order to a bill"""
        if po_id not in self.purchase_orders:
            return {"success": False, "error": "Purchase order not found"}

        po = self.purchase_orders[po_id]

        if po.status not in [PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.PARTIAL]:
            return {"success": False, "error": "PO must be received before converting to bill"}

        # Create bill lines from PO lines
        bill_lines = []
        for line in po.lines:
            if line.quantity_received > 0:
                bill_lines.append({
                    "account_id": line.account_id or self.vendors[po.vendor_id].default_expense_account_id,
                    "description": line.item_description,
                    "quantity": line.quantity_received,
                    "unit_price": line.unit_price,
                    "class_id": line.class_id
                })

        result = self.create_bill(
            vendor_id=po.vendor_id,
            bill_date=bill_date,
            lines=bill_lines,
            reference_number=reference_number,
            terms=po.terms,
            memo=f"From PO {po.po_number}",
            purchase_order_id=po_id
        )

        if result["success"]:
            po.status = PurchaseOrderStatus.CLOSED
            po.updated_at = datetime.now()

        return result

    def list_purchase_orders(
        self,
        vendor_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List purchase orders"""
        result = []

        for po in self.purchase_orders.values():
            if vendor_id and po.vendor_id != vendor_id:
                continue
            if status and po.status.value != status:
                continue
            if start_date:
                if po.order_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if po.order_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            result.append(self._po_to_dict(po))

        return sorted(result, key=lambda p: p["order_date"], reverse=True)

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

        for bill in self.bills.values():
            if bill.status not in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE]:
                continue
            if bill.bill_date > ref_date:
                continue

            days_old = (ref_date - bill.due_date).days
            vendor_name = self.vendors[bill.vendor_id].display_name if bill.vendor_id in self.vendors else "Unknown"

            entry = {
                "bill_id": bill.bill_id,
                "bill_number": bill.bill_number,
                "vendor_id": bill.vendor_id,
                "vendor_name": vendor_name,
                "bill_date": bill.bill_date.isoformat(),
                "due_date": bill.due_date.isoformat(),
                "days_overdue": max(0, days_old),
                "balance": bill.balance_due
            }

            if days_old <= 0:
                aging["current"].append(entry)
                aging["totals"]["current"] += bill.balance_due
            elif days_old <= 30:
                aging["1_30"].append(entry)
                aging["totals"]["1_30"] += bill.balance_due
            elif days_old <= 60:
                aging["31_60"].append(entry)
                aging["totals"]["31_60"] += bill.balance_due
            elif days_old <= 90:
                aging["61_90"].append(entry)
                aging["totals"]["61_90"] += bill.balance_due
            else:
                aging["over_90"].append(entry)
                aging["totals"]["over_90"] += bill.balance_due

            aging["totals"]["total"] += bill.balance_due

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

        for vendor in self.vendors.values():
            if not vendor.is_1099_vendor:
                continue

            total_payments = 0.0

            for payment in self.payments.values():
                if payment.vendor_id != vendor.vendor_id:
                    continue
                if payment.is_voided:
                    continue
                if payment.payment_date.year != year:
                    continue

                total_payments += payment.total_amount

            if total_payments > 0:
                result.append({
                    "vendor_id": vendor.vendor_id,
                    "vendor_name": vendor.display_name,
                    "tax_id": vendor.tax_id,
                    "address": f"{vendor.billing_address_line1}, {vendor.billing_city}, {vendor.billing_state} {vendor.billing_zip}",
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

        for bill in self.bills.values():
            if bill.status not in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE]:
                continue
            if bill.due_date > end_date:
                continue

            vendor_name = self.vendors[bill.vendor_id].display_name if bill.vendor_id in self.vendors else "Unknown"

            bills_due.append({
                "bill_id": bill.bill_id,
                "bill_number": bill.bill_number,
                "vendor_name": vendor_name,
                "due_date": bill.due_date.isoformat(),
                "balance": bill.balance_due,
                "days_until_due": (bill.due_date - today).days,
                "is_overdue": bill.due_date < today
            })

            total_due += bill.balance_due

        return {
            "period_start": today.isoformat(),
            "period_end": end_date.isoformat(),
            "bills_count": len(bills_due),
            "total_due": round(total_due, 2),
            "bills": sorted(bills_due, key=lambda b: b["due_date"])
        }

    # ==================== UTILITY METHODS ====================

    def _vendor_to_dict(self, vendor: Vendor) -> Dict:
        """Convert Vendor to dictionary"""
        return {
            "vendor_id": vendor.vendor_id,
            "company_name": vendor.company_name,
            "display_name": vendor.display_name,
            "contact_name": vendor.contact_name,
            "email": vendor.email,
            "phone": vendor.phone,
            "mobile": vendor.mobile,
            "website": vendor.website,
            "billing_address": {
                "line1": vendor.billing_address_line1,
                "line2": vendor.billing_address_line2,
                "city": vendor.billing_city,
                "state": vendor.billing_state,
                "zip": vendor.billing_zip,
                "country": vendor.billing_country
            },
            "tax_id": vendor.tax_id,
            "is_1099_vendor": vendor.is_1099_vendor,
            "default_expense_account_id": vendor.default_expense_account_id,
            "payment_terms": vendor.payment_terms,
            "credit_limit": vendor.credit_limit,
            "vendor_type": vendor.vendor_type,
            "notes": vendor.notes,
            "status": vendor.status.value,
            "created_at": vendor.created_at.isoformat(),
            "updated_at": vendor.updated_at.isoformat()
        }

    def _bill_to_dict(self, bill: Bill) -> Dict:
        """Convert Bill to dictionary"""
        vendor_name = self.vendors[bill.vendor_id].display_name if bill.vendor_id in self.vendors else "Unknown"

        return {
            "bill_id": bill.bill_id,
            "bill_number": bill.bill_number,
            "vendor_id": bill.vendor_id,
            "vendor_name": vendor_name,
            "bill_date": bill.bill_date.isoformat(),
            "due_date": bill.due_date.isoformat(),
            "reference_number": bill.reference_number,
            "terms": bill.terms,
            "memo": bill.memo,
            "lines": [
                {
                    "line_id": line.line_id,
                    "account_id": line.account_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "amount": line.amount,
                    "tax_code": line.tax_code,
                    "tax_amount": line.tax_amount,
                    "class_id": line.class_id,
                    "location_id": line.location_id
                }
                for line in bill.lines
            ],
            "subtotal": bill.subtotal,
            "tax_total": bill.tax_total,
            "total": bill.total,
            "amount_paid": bill.amount_paid,
            "balance_due": bill.balance_due,
            "status": bill.status.value,
            "purchase_order_id": bill.purchase_order_id,
            "journal_entry_id": bill.journal_entry_id,
            "created_at": bill.created_at.isoformat(),
            "updated_at": bill.updated_at.isoformat()
        }

    def _payment_to_dict(self, payment: BillPayment) -> Dict:
        """Convert BillPayment to dictionary"""
        vendor_name = self.vendors[payment.vendor_id].display_name if payment.vendor_id in self.vendors else "Unknown"

        return {
            "payment_id": payment.payment_id,
            "payment_date": payment.payment_date.isoformat(),
            "vendor_id": payment.vendor_id,
            "vendor_name": vendor_name,
            "bank_account_id": payment.bank_account_id,
            "payment_method": payment.payment_method.value,
            "reference_number": payment.reference_number,
            "memo": payment.memo,
            "total_amount": payment.total_amount,
            "applied_bills": payment.applied_bills,
            "is_voided": payment.is_voided,
            "journal_entry_id": payment.journal_entry_id,
            "created_at": payment.created_at.isoformat()
        }

    def _credit_to_dict(self, credit: VendorCredit) -> Dict:
        """Convert VendorCredit to dictionary"""
        vendor_name = self.vendors[credit.vendor_id].display_name if credit.vendor_id in self.vendors else "Unknown"

        return {
            "credit_id": credit.credit_id,
            "credit_number": credit.credit_number,
            "vendor_id": credit.vendor_id,
            "vendor_name": vendor_name,
            "credit_date": credit.credit_date.isoformat(),
            "reference_number": credit.reference_number,
            "memo": credit.memo,
            "lines": [
                {
                    "line_id": line.line_id,
                    "account_id": line.account_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "amount": line.amount
                }
                for line in credit.lines
            ],
            "total": credit.total,
            "amount_applied": credit.amount_applied,
            "balance": credit.balance,
            "status": credit.status,
            "journal_entry_id": credit.journal_entry_id,
            "created_at": credit.created_at.isoformat()
        }

    def _po_to_dict(self, po: PurchaseOrder) -> Dict:
        """Convert PurchaseOrder to dictionary"""
        vendor_name = self.vendors[po.vendor_id].display_name if po.vendor_id in self.vendors else "Unknown"

        return {
            "po_id": po.po_id,
            "po_number": po.po_number,
            "vendor_id": po.vendor_id,
            "vendor_name": vendor_name,
            "order_date": po.order_date.isoformat(),
            "expected_date": po.expected_date.isoformat() if po.expected_date else None,
            "ship_to_address": po.ship_to_address,
            "memo": po.memo,
            "terms": po.terms,
            "lines": [
                {
                    "line_id": line.line_id,
                    "item_description": line.item_description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "amount": line.amount,
                    "quantity_received": line.quantity_received,
                    "account_id": line.account_id,
                    "class_id": line.class_id
                }
                for line in po.lines
            ],
            "subtotal": po.subtotal,
            "tax_total": po.tax_total,
            "total": po.total,
            "status": po.status.value,
            "approved_by": po.approved_by,
            "approved_date": po.approved_date.isoformat() if po.approved_date else None,
            "created_at": po.created_at.isoformat(),
            "updated_at": po.updated_at.isoformat()
        }

    def get_service_summary(self) -> Dict:
        """Get GenFin Payables service summary"""
        total_vendors = len(self.vendors)
        active_vendors = sum(1 for v in self.vendors.values() if v.status == VendorStatus.ACTIVE)
        total_bills = len(self.bills)
        open_bills = sum(1 for b in self.bills.values() if b.status in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE])
        total_outstanding = sum(b.balance_due for b in self.bills.values() if b.status in [BillStatus.OPEN, BillStatus.PARTIAL, BillStatus.OVERDUE])

        return {
            "service": "GenFin Payables",
            "version": "1.0.0",
            "total_vendors": total_vendors,
            "active_vendors": active_vendors,
            "total_bills": total_bills,
            "open_bills": open_bills,
            "total_outstanding": round(total_outstanding, 2),
            "total_payments": len(self.payments),
            "total_credits": len(self.credits),
            "total_purchase_orders": len(self.purchase_orders)
        }


# Singleton instance
genfin_payables_service = GenFinPayablesService()
