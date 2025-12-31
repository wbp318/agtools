"""
GenFin Receivables Service - Customers, Invoices, Payments Received, Estimates
Complete accounts receivable management for farm operations
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid

from .genfin_core_service import genfin_core_service, TransactionStatus


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


@dataclass
class Customer:
    """Customer record"""
    customer_id: str
    company_name: str
    display_name: str
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    mobile: str = ""
    fax: str = ""
    website: str = ""

    # Billing address
    billing_address_line1: str = ""
    billing_address_line2: str = ""
    billing_city: str = ""
    billing_state: str = ""
    billing_zip: str = ""
    billing_country: str = "USA"

    # Shipping address
    shipping_address_line1: str = ""
    shipping_address_line2: str = ""
    shipping_city: str = ""
    shipping_state: str = ""
    shipping_zip: str = ""
    shipping_country: str = "USA"

    # Financial
    tax_exempt: bool = False
    tax_id: str = ""
    default_income_account_id: Optional[str] = None
    payment_terms: str = "Net 30"
    credit_limit: float = 0.0

    # Classification
    customer_type: str = ""  # Buyer, Wholesaler, Retail, Government
    notes: str = ""
    status: CustomerStatus = CustomerStatus.ACTIVE

    # Balance
    opening_balance: float = 0.0
    opening_balance_date: Optional[date] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class InvoiceLine:
    """Line item on an invoice"""
    line_id: str
    account_id: str
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float = 0.0
    tax_code: Optional[str] = None
    tax_amount: float = 0.0
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    class_id: Optional[str] = None
    location_id: Optional[str] = None
    service_date: Optional[date] = None


@dataclass
class Invoice:
    """Customer invoice"""
    invoice_id: str
    invoice_number: str
    customer_id: str
    invoice_date: date
    due_date: date
    lines: List[InvoiceLine]

    # Reference
    po_number: str = ""  # Customer's PO number
    terms: str = "Net 30"
    memo: str = ""
    message_on_invoice: str = ""
    message_on_statement: str = ""

    # Addresses
    billing_address: str = ""
    shipping_address: str = ""

    # Totals
    subtotal: float = 0.0
    discount_total: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0
    amount_paid: float = 0.0
    balance_due: float = 0.0

    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT
    ar_account_id: Optional[str] = None
    journal_entry_id: Optional[str] = None

    # Email tracking
    email_sent: bool = False
    email_sent_date: Optional[datetime] = None
    last_viewed_date: Optional[datetime] = None

    # From estimate
    estimate_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PaymentReceived:
    """Payment received from customer"""
    payment_id: str
    payment_date: date
    customer_id: str
    deposit_account_id: str
    payment_method: PaymentMethod
    reference_number: str = ""  # Check number, transaction ID
    memo: str = ""
    total_amount: float = 0.0
    applied_invoices: List[Dict] = field(default_factory=list)  # [{invoice_id, amount}]
    unapplied_amount: float = 0.0
    journal_entry_id: Optional[str] = None
    is_voided: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CustomerCredit:
    """Credit memo to customer"""
    credit_id: str
    credit_number: str
    customer_id: str
    credit_date: date
    lines: List[InvoiceLine]

    reason: str = ""
    memo: str = ""
    total: float = 0.0
    amount_applied: float = 0.0
    balance: float = 0.0

    status: str = "open"  # open, applied, refunded
    journal_entry_id: Optional[str] = None
    related_invoice_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Estimate:
    """Estimate/Quote for customer"""
    estimate_id: str
    estimate_number: str
    customer_id: str
    estimate_date: date
    expiration_date: date
    lines: List[InvoiceLine]

    # Reference
    po_number: str = ""
    terms: str = ""
    memo: str = ""
    message_to_customer: str = ""

    # Totals
    subtotal: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0

    # Status
    status: EstimateStatus = EstimateStatus.DRAFT
    accepted_date: Optional[date] = None
    converted_invoice_id: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SalesReceipt:
    """Sales receipt (payment at time of sale)"""
    receipt_id: str
    receipt_number: str
    customer_id: Optional[str]
    receipt_date: date
    lines: List[InvoiceLine]

    payment_method: PaymentMethod
    deposit_account_id: str
    reference_number: str = ""
    memo: str = ""

    subtotal: float = 0.0
    tax_total: float = 0.0
    total: float = 0.0

    journal_entry_id: Optional[str] = None
    is_voided: bool = False
    created_at: datetime = field(default_factory=datetime.now)


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
    GenFin Accounts Receivable Service

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.customers: Dict[str, Customer] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.payments: Dict[str, PaymentReceived] = {}
        self.credits: Dict[str, CustomerCredit] = {}
        self.estimates: Dict[str, Estimate] = {}
        self.sales_receipts: Dict[str, SalesReceipt] = {}

        self.next_invoice_number = 1001
        self.next_estimate_number = 1
        self.next_credit_number = 1
        self.next_receipt_number = 1

        # Default AR account
        self.default_ar_account_id = self._get_default_ar_account()

        self._initialized = True

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

        ob_date = None
        if opening_balance_date:
            ob_date = datetime.strptime(opening_balance_date, "%Y-%m-%d").date()

        customer = Customer(
            customer_id=customer_id,
            company_name=company_name,
            display_name=display_name or company_name,
            contact_name=contact_name,
            email=email,
            phone=phone,
            billing_address_line1=billing_address_line1,
            billing_city=billing_city,
            billing_state=billing_state,
            billing_zip=billing_zip,
            tax_exempt=tax_exempt,
            payment_terms=payment_terms,
            customer_type=customer_type,
            default_income_account_id=default_income_account_id,
            credit_limit=credit_limit,
            opening_balance=opening_balance,
            opening_balance_date=ob_date
        )

        self.customers[customer_id] = customer

        return {
            "success": True,
            "customer_id": customer_id,
            "customer": self._customer_to_dict(customer)
        }

    def update_customer(self, customer_id: str, **kwargs) -> Dict:
        """Update customer information"""
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        customer = self.customers[customer_id]

        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)

        customer.updated_at = datetime.now()

        return {
            "success": True,
            "customer": self._customer_to_dict(customer)
        }

    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer"""
        if customer_id not in self.customers:
            return False
        del self.customers[customer_id]
        return True

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer by ID"""
        if customer_id not in self.customers:
            return None
        return self._customer_to_dict(self.customers[customer_id])

    def list_customers(
        self,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        search: Optional[str] = None,
        with_balance_only: bool = False
    ) -> List[Dict]:
        """List customers with filtering"""
        result = []

        for customer in self.customers.values():
            if status and customer.status.value != status:
                continue
            if customer_type and customer.customer_type != customer_type:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in customer.company_name.lower() and
                    search_lower not in customer.display_name.lower() and
                    search_lower not in customer.contact_name.lower()):
                    continue

            balance = self.get_customer_balance(customer.customer_id)

            if with_balance_only and balance == 0:
                continue

            customer_dict = self._customer_to_dict(customer)
            customer_dict["balance"] = balance
            result.append(customer_dict)

        return sorted(result, key=lambda c: c["display_name"])

    def get_customer_balance(self, customer_id: str) -> float:
        """Calculate customer balance (amount owed to us)"""
        balance = 0.0

        # Add opening balance
        if customer_id in self.customers:
            balance = self.customers[customer_id].opening_balance

        # Add unpaid invoices
        for invoice in self.invoices.values():
            if invoice.customer_id == customer_id and invoice.status in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]:
                balance += invoice.balance_due

        # Subtract unapplied credits
        for credit in self.credits.values():
            if credit.customer_id == customer_id and credit.status == "open":
                balance -= credit.balance

        # Subtract unapplied payments
        for payment in self.payments.values():
            if payment.customer_id == customer_id and not payment.is_voided:
                balance -= payment.unapplied_amount

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
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        invoice_id = str(uuid.uuid4())
        invoice_number = f"INV-{self.next_invoice_number:05d}"
        self.next_invoice_number += 1

        # Parse date and calculate due date
        i_date = datetime.strptime(invoice_date, "%Y-%m-%d").date()
        days = PAYMENT_TERMS.get(terms, 30)
        d_date = i_date + timedelta(days=days)

        # Process lines
        invoice_lines = []
        subtotal = 0.0
        discount_total = 0.0
        tax_total = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
            discount = line.get("discount_amount", 0)
            tax_amount = line.get("tax_amount", 0)

            service_date = None
            if line.get("service_date"):
                service_date = datetime.strptime(line["service_date"], "%Y-%m-%d").date()

            invoice_lines.append(InvoiceLine(
                line_id=str(uuid.uuid4()),
                account_id=line["account_id"],
                description=line.get("description", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line_amount,
                tax_code=line.get("tax_code"),
                tax_amount=tax_amount,
                discount_percent=line.get("discount_percent", 0),
                discount_amount=discount,
                class_id=line.get("class_id"),
                location_id=line.get("location_id"),
                service_date=service_date
            ))

            subtotal += line_amount
            discount_total += discount
            tax_total += tax_amount

        total = subtotal - discount_total + tax_total

        # Get customer addresses
        customer = self.customers[customer_id]
        billing_addr = f"{customer.billing_address_line1}\n{customer.billing_city}, {customer.billing_state} {customer.billing_zip}"
        shipping_addr = f"{customer.shipping_address_line1}\n{customer.shipping_city}, {customer.shipping_state} {customer.shipping_zip}"

        invoice = Invoice(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            customer_id=customer_id,
            invoice_date=i_date,
            due_date=d_date,
            lines=invoice_lines,
            po_number=po_number,
            terms=terms,
            memo=memo,
            message_on_invoice=message_on_invoice,
            billing_address=billing_addr,
            shipping_address=shipping_addr,
            subtotal=round(subtotal, 2),
            discount_total=round(discount_total, 2),
            tax_total=round(tax_total, 2),
            total=round(total, 2),
            amount_paid=0.0,
            balance_due=round(total, 2),
            status=InvoiceStatus.DRAFT,
            ar_account_id=ar_account_id or self.default_ar_account_id,
            estimate_id=estimate_id
        )

        self.invoices[invoice_id] = invoice

        return {
            "success": True,
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "invoice": self._invoice_to_dict(invoice)
        }

    def send_invoice(self, invoice_id: str) -> Dict:
        """Send/post an invoice - create journal entry and change status"""
        if invoice_id not in self.invoices:
            return {"success": False, "error": "Invoice not found"}

        invoice = self.invoices[invoice_id]

        if invoice.status not in [InvoiceStatus.DRAFT]:
            return {"success": False, "error": "Invoice has already been sent"}

        # Create journal entry
        # Debit AR, Credit income accounts
        journal_lines = []

        journal_lines.append({
            "account_id": invoice.ar_account_id,
            "description": f"Invoice {invoice.invoice_number} - {self.customers[invoice.customer_id].display_name}",
            "debit": invoice.total,
            "credit": 0,
            "customer_id": invoice.customer_id
        })

        for line in invoice.lines:
            journal_lines.append({
                "account_id": line.account_id,
                "description": line.description,
                "debit": 0,
                "credit": line.amount - line.discount_amount,
                "class_id": line.class_id,
                "location_id": line.location_id,
                "customer_id": invoice.customer_id
            })

        # Tax liability if any
        if invoice.tax_total > 0:
            tax_account = genfin_core_service.get_account_by_number("2500")
            if tax_account:
                journal_lines.append({
                    "account_id": tax_account["account_id"],
                    "description": f"Sales tax - Invoice {invoice.invoice_number}",
                    "debit": 0,
                    "credit": invoice.tax_total
                })

        je_result = genfin_core_service.create_journal_entry(
            entry_date=invoice.invoice_date.isoformat(),
            lines=journal_lines,
            memo=f"Invoice {invoice.invoice_number}",
            source_type="invoice",
            source_id=invoice_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        invoice.journal_entry_id = je_result["entry_id"]
        invoice.status = InvoiceStatus.SENT
        invoice.email_sent = True
        invoice.email_sent_date = datetime.now()
        invoice.updated_at = datetime.now()

        # Check if overdue
        if invoice.due_date < date.today():
            invoice.status = InvoiceStatus.OVERDUE

        return {
            "success": True,
            "invoice": self._invoice_to_dict(invoice),
            "journal_entry_id": je_result["entry_id"]
        }

    def void_invoice(self, invoice_id: str, reason: str = "") -> Dict:
        """Void an invoice"""
        if invoice_id not in self.invoices:
            return {"success": False, "error": "Invoice not found"}

        invoice = self.invoices[invoice_id]

        if invoice.amount_paid > 0:
            return {"success": False, "error": "Cannot void invoice with payments applied"}

        # Void journal entry if exists
        if invoice.journal_entry_id:
            genfin_core_service.void_journal_entry(invoice.journal_entry_id, reason)

        invoice.status = InvoiceStatus.VOIDED
        invoice.memo = f"{invoice.memo} [VOIDED: {reason}]"
        invoice.updated_at = datetime.now()

        return {
            "success": True,
            "invoice": self._invoice_to_dict(invoice)
        }

    def get_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Get invoice by ID"""
        if invoice_id not in self.invoices:
            return None
        return self._invoice_to_dict(self.invoices[invoice_id])

    def delete_invoice(self, invoice_id: str) -> bool:
        """Delete an invoice"""
        if invoice_id not in self.invoices:
            return False
        del self.invoices[invoice_id]
        return True

    def list_invoices(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        unpaid_only: bool = False
    ) -> List[Dict]:
        """List invoices with filtering"""
        result = []

        for invoice in self.invoices.values():
            if customer_id and invoice.customer_id != customer_id:
                continue
            if status and invoice.status.value != status:
                continue
            if start_date:
                if invoice.invoice_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if invoice.invoice_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue
            if unpaid_only and invoice.status not in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]:
                continue

            result.append(self._invoice_to_dict(invoice))

        return sorted(result, key=lambda i: i["invoice_date"], reverse=True)

    # ==================== PAYMENTS RECEIVED ====================

    def receive_payment(
        self,
        customer_id: str,
        payment_date: str,
        deposit_account_id: str,
        payment_method: str,
        total_amount: float,
        invoices_to_apply: List[Dict] = None,  # [{invoice_id, amount}]
        reference_number: str = "",
        memo: str = ""
    ) -> Dict:
        """Receive payment from customer"""
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        invoices_to_apply = invoices_to_apply or []

        # Validate invoices and amounts
        total_applied = 0.0
        for inv_payment in invoices_to_apply:
            invoice_id = inv_payment["invoice_id"]
            amount = inv_payment["amount"]

            if invoice_id not in self.invoices:
                return {"success": False, "error": f"Invoice {invoice_id} not found"}

            invoice = self.invoices[invoice_id]
            if invoice.customer_id != customer_id:
                return {"success": False, "error": f"Invoice {invoice.invoice_number} does not belong to this customer"}
            if invoice.status not in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]:
                return {"success": False, "error": f"Invoice {invoice.invoice_number} is not payable"}
            if amount > invoice.balance_due:
                return {"success": False, "error": f"Payment amount exceeds balance on {invoice.invoice_number}"}

            total_applied += amount

        if total_applied > total_amount:
            return {"success": False, "error": "Total applied exceeds payment amount"}

        payment_id = str(uuid.uuid4())
        p_date = datetime.strptime(payment_date, "%Y-%m-%d").date()

        # Create journal entry
        # Debit Bank, Credit AR
        journal_lines = [
            {
                "account_id": deposit_account_id,
                "description": f"Payment from {self.customers[customer_id].display_name}",
                "debit": total_amount,
                "credit": 0,
                "customer_id": customer_id
            },
            {
                "account_id": self.default_ar_account_id,
                "description": f"Payment from {self.customers[customer_id].display_name}",
                "debit": 0,
                "credit": total_amount,
                "customer_id": customer_id
            }
        ]

        je_result = genfin_core_service.create_journal_entry(
            entry_date=payment_date,
            lines=journal_lines,
            memo=f"Payment received: {reference_number}" if reference_number else f"Payment from {self.customers[customer_id].display_name}",
            source_type="payment_received",
            source_id=payment_id,
            auto_post=True
        )

        if not je_result["success"]:
            return {"success": False, "error": f"Failed to create journal entry: {je_result.get('error')}"}

        # Apply payments to invoices
        applied_invoices = []
        for inv_payment in invoices_to_apply:
            invoice = self.invoices[inv_payment["invoice_id"]]
            amount = inv_payment["amount"]

            invoice.amount_paid += amount
            invoice.balance_due = round(invoice.total - invoice.amount_paid, 2)

            if invoice.balance_due == 0:
                invoice.status = InvoiceStatus.PAID
            else:
                invoice.status = InvoiceStatus.PARTIAL

            invoice.updated_at = datetime.now()

            applied_invoices.append({
                "invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "amount": amount,
                "balance_remaining": invoice.balance_due
            })

        unapplied = round(total_amount - total_applied, 2)

        payment = PaymentReceived(
            payment_id=payment_id,
            payment_date=p_date,
            customer_id=customer_id,
            deposit_account_id=deposit_account_id,
            payment_method=PaymentMethod(payment_method),
            reference_number=reference_number,
            memo=memo,
            total_amount=total_amount,
            applied_invoices=applied_invoices,
            unapplied_amount=unapplied,
            journal_entry_id=je_result["entry_id"]
        )

        self.payments[payment_id] = payment

        return {
            "success": True,
            "payment_id": payment_id,
            "payment": self._payment_to_dict(payment)
        }

    def apply_payment_to_invoice(self, payment_id: str, invoice_id: str, amount: float) -> Dict:
        """Apply unapplied payment to an invoice"""
        if payment_id not in self.payments:
            return {"success": False, "error": "Payment not found"}
        if invoice_id not in self.invoices:
            return {"success": False, "error": "Invoice not found"}

        payment = self.payments[payment_id]
        invoice = self.invoices[invoice_id]

        if payment.customer_id != invoice.customer_id:
            return {"success": False, "error": "Payment and invoice must be for the same customer"}
        if amount > payment.unapplied_amount:
            return {"success": False, "error": "Amount exceeds unapplied balance"}
        if amount > invoice.balance_due:
            return {"success": False, "error": "Amount exceeds invoice balance"}

        # Apply to invoice
        invoice.amount_paid += amount
        invoice.balance_due = round(invoice.total - invoice.amount_paid, 2)

        if invoice.balance_due == 0:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIAL

        # Update payment
        payment.unapplied_amount = round(payment.unapplied_amount - amount, 2)
        payment.applied_invoices.append({
            "invoice_id": invoice.invoice_id,
            "invoice_number": invoice.invoice_number,
            "amount": amount,
            "balance_remaining": invoice.balance_due
        })

        return {
            "success": True,
            "payment_unapplied": payment.unapplied_amount,
            "invoice_balance": invoice.balance_due
        }

    def void_payment(self, payment_id: str, reason: str = "") -> Dict:
        """Void a payment received"""
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

        # Reverse invoice applications
        for applied in payment.applied_invoices:
            if applied["invoice_id"] in self.invoices:
                invoice = self.invoices[applied["invoice_id"]]
                invoice.amount_paid -= applied["amount"]
                invoice.balance_due = round(invoice.total - invoice.amount_paid, 2)

                if invoice.balance_due == invoice.total:
                    invoice.status = InvoiceStatus.SENT
                    if invoice.due_date < date.today():
                        invoice.status = InvoiceStatus.OVERDUE
                else:
                    invoice.status = InvoiceStatus.PARTIAL

        payment.is_voided = True

        return {
            "success": True,
            "message": "Payment voided successfully"
        }

    def list_payments(
        self,
        customer_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_voided: bool = False
    ) -> List[Dict]:
        """List payments received"""
        result = []

        for payment in self.payments.values():
            if customer_id and payment.customer_id != customer_id:
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
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        credit_id = str(uuid.uuid4())
        credit_number = f"CRD-{self.next_credit_number:05d}"
        self.next_credit_number += 1

        c_date = datetime.strptime(credit_date, "%Y-%m-%d").date()

        # Process lines
        credit_lines = []
        total = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)

            credit_lines.append(InvoiceLine(
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

        # Create journal entry (reverse of invoice)
        # Credit AR, Debit income accounts
        journal_lines = []

        journal_lines.append({
            "account_id": self.default_ar_account_id,
            "description": f"Credit Memo {credit_number}",
            "debit": 0,
            "credit": total,
            "customer_id": customer_id
        })

        for line in credit_lines:
            journal_lines.append({
                "account_id": line.account_id,
                "description": line.description,
                "debit": line.amount,
                "credit": 0,
                "class_id": line.class_id,
                "location_id": line.location_id
            })

        je_result = genfin_core_service.create_journal_entry(
            entry_date=credit_date,
            lines=journal_lines,
            memo=f"Credit Memo {credit_number}",
            source_type="customer_credit",
            source_id=credit_id,
            auto_post=True
        )

        credit = CustomerCredit(
            credit_id=credit_id,
            credit_number=credit_number,
            customer_id=customer_id,
            credit_date=c_date,
            lines=credit_lines,
            reason=reason,
            memo=memo,
            total=round(total, 2),
            amount_applied=0.0,
            balance=round(total, 2),
            journal_entry_id=je_result.get("entry_id"),
            related_invoice_id=related_invoice_id
        )

        self.credits[credit_id] = credit

        return {
            "success": True,
            "credit_id": credit_id,
            "credit_number": credit_number,
            "credit": self._credit_to_dict(credit)
        }

    def apply_credit_to_invoice(self, credit_id: str, invoice_id: str, amount: float) -> Dict:
        """Apply customer credit to an invoice"""
        if credit_id not in self.credits:
            return {"success": False, "error": "Credit not found"}
        if invoice_id not in self.invoices:
            return {"success": False, "error": "Invoice not found"}

        credit = self.credits[credit_id]
        invoice = self.invoices[invoice_id]

        if credit.customer_id != invoice.customer_id:
            return {"success": False, "error": "Credit and invoice must be for the same customer"}
        if amount > credit.balance:
            return {"success": False, "error": "Amount exceeds credit balance"}
        if amount > invoice.balance_due:
            return {"success": False, "error": "Amount exceeds invoice balance"}

        # Apply credit
        credit.amount_applied += amount
        credit.balance = round(credit.total - credit.amount_applied, 2)
        if credit.balance == 0:
            credit.status = "applied"

        invoice.amount_paid += amount
        invoice.balance_due = round(invoice.total - invoice.amount_paid, 2)
        if invoice.balance_due == 0:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIAL

        return {
            "success": True,
            "credit_balance": credit.balance,
            "invoice_balance": invoice.balance_due
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
        if customer_id not in self.customers:
            return {"success": False, "error": "Customer not found"}

        estimate_id = str(uuid.uuid4())
        estimate_number = f"EST-{self.next_estimate_number:05d}"
        self.next_estimate_number += 1

        e_date = datetime.strptime(estimate_date, "%Y-%m-%d").date()
        exp_date = e_date + timedelta(days=expiration_days)

        # Process lines
        estimate_lines = []
        subtotal = 0.0
        tax_total = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
            tax_amount = line.get("tax_amount", 0)

            estimate_lines.append(InvoiceLine(
                line_id=str(uuid.uuid4()),
                account_id=line.get("account_id", ""),
                description=line.get("description", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line_amount,
                tax_amount=tax_amount,
                class_id=line.get("class_id"),
                location_id=line.get("location_id")
            ))

            subtotal += line_amount
            tax_total += tax_amount

        estimate = Estimate(
            estimate_id=estimate_id,
            estimate_number=estimate_number,
            customer_id=customer_id,
            estimate_date=e_date,
            expiration_date=exp_date,
            lines=estimate_lines,
            po_number=po_number,
            terms=terms or self.customers[customer_id].payment_terms,
            memo=memo,
            message_to_customer=message_to_customer,
            subtotal=round(subtotal, 2),
            tax_total=round(tax_total, 2),
            total=round(subtotal + tax_total, 2),
            status=EstimateStatus.DRAFT
        )

        self.estimates[estimate_id] = estimate

        return {
            "success": True,
            "estimate_id": estimate_id,
            "estimate_number": estimate_number,
            "estimate": self._estimate_to_dict(estimate)
        }

    def send_estimate(self, estimate_id: str) -> Dict:
        """Mark estimate as sent"""
        if estimate_id not in self.estimates:
            return {"success": False, "error": "Estimate not found"}

        estimate = self.estimates[estimate_id]
        estimate.status = EstimateStatus.SENT
        estimate.updated_at = datetime.now()

        return {
            "success": True,
            "estimate": self._estimate_to_dict(estimate)
        }

    def accept_estimate(self, estimate_id: str) -> Dict:
        """Mark estimate as accepted"""
        if estimate_id not in self.estimates:
            return {"success": False, "error": "Estimate not found"}

        estimate = self.estimates[estimate_id]
        estimate.status = EstimateStatus.ACCEPTED
        estimate.accepted_date = date.today()
        estimate.updated_at = datetime.now()

        return {
            "success": True,
            "estimate": self._estimate_to_dict(estimate)
        }

    def convert_estimate_to_invoice(self, estimate_id: str, invoice_date: str) -> Dict:
        """Convert accepted estimate to invoice"""
        if estimate_id not in self.estimates:
            return {"success": False, "error": "Estimate not found"}

        estimate = self.estimates[estimate_id]

        if estimate.status not in [EstimateStatus.ACCEPTED, EstimateStatus.SENT]:
            return {"success": False, "error": "Estimate must be sent or accepted"}

        # Create invoice lines from estimate
        invoice_lines = []
        for line in estimate.lines:
            invoice_lines.append({
                "account_id": line.account_id,
                "description": line.description,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "tax_amount": line.tax_amount,
                "class_id": line.class_id,
                "location_id": line.location_id
            })

        result = self.create_invoice(
            customer_id=estimate.customer_id,
            invoice_date=invoice_date,
            lines=invoice_lines,
            po_number=estimate.po_number,
            terms=estimate.terms,
            memo=f"From Estimate {estimate.estimate_number}",
            estimate_id=estimate_id
        )

        if result["success"]:
            estimate.status = EstimateStatus.CONVERTED
            estimate.converted_invoice_id = result["invoice_id"]
            estimate.updated_at = datetime.now()

        return result

    def list_estimates(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """List estimates"""
        result = []

        for estimate in self.estimates.values():
            if customer_id and estimate.customer_id != customer_id:
                continue
            if status and estimate.status.value != status:
                continue
            if start_date:
                if estimate.estimate_date < datetime.strptime(start_date, "%Y-%m-%d").date():
                    continue
            if end_date:
                if estimate.estimate_date > datetime.strptime(end_date, "%Y-%m-%d").date():
                    continue

            # Check for expiration
            if estimate.status == EstimateStatus.SENT and estimate.expiration_date < date.today():
                estimate.status = EstimateStatus.EXPIRED

            result.append(self._estimate_to_dict(estimate))

        return sorted(result, key=lambda e: e["estimate_date"], reverse=True)

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
        receipt_number = f"SR-{self.next_receipt_number:05d}"
        self.next_receipt_number += 1

        r_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()

        # Process lines
        receipt_lines = []
        subtotal = 0.0
        tax_total = 0.0

        for line in lines:
            line_amount = line.get("quantity", 1) * line.get("unit_price", 0)
            tax_amount = line.get("tax_amount", 0)

            receipt_lines.append(InvoiceLine(
                line_id=str(uuid.uuid4()),
                account_id=line["account_id"],
                description=line.get("description", ""),
                quantity=line.get("quantity", 1),
                unit_price=line.get("unit_price", 0),
                amount=line_amount,
                tax_amount=tax_amount,
                class_id=line.get("class_id"),
                location_id=line.get("location_id")
            ))

            subtotal += line_amount
            tax_total += tax_amount

        total = subtotal + tax_total

        # Create journal entry
        # Debit Bank, Credit Income
        journal_lines = []

        journal_lines.append({
            "account_id": deposit_account_id,
            "description": f"Sales Receipt {receipt_number}",
            "debit": total,
            "credit": 0,
            "customer_id": customer_id
        })

        for line in receipt_lines:
            journal_lines.append({
                "account_id": line.account_id,
                "description": line.description,
                "debit": 0,
                "credit": line.amount,
                "class_id": line.class_id,
                "location_id": line.location_id
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

        receipt = SalesReceipt(
            receipt_id=receipt_id,
            receipt_number=receipt_number,
            customer_id=customer_id,
            receipt_date=r_date,
            lines=receipt_lines,
            payment_method=PaymentMethod(payment_method),
            deposit_account_id=deposit_account_id,
            reference_number=reference_number,
            memo=memo,
            subtotal=round(subtotal, 2),
            tax_total=round(tax_total, 2),
            total=round(total, 2),
            journal_entry_id=je_result.get("entry_id")
        )

        self.sales_receipts[receipt_id] = receipt

        return {
            "success": True,
            "receipt_id": receipt_id,
            "receipt_number": receipt_number,
            "receipt": self._receipt_to_dict(receipt)
        }

    # ==================== REPORTS ====================

    def get_ar_aging(self, as_of_date: Optional[str] = None) -> Dict:
        """Generate accounts receivable aging report"""
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

        for invoice in self.invoices.values():
            if invoice.status not in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]:
                continue
            if invoice.invoice_date > ref_date:
                continue

            days_old = (ref_date - invoice.due_date).days
            customer_name = self.customers[invoice.customer_id].display_name if invoice.customer_id in self.customers else "Unknown"

            entry = {
                "invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "customer_id": invoice.customer_id,
                "customer_name": customer_name,
                "invoice_date": invoice.invoice_date.isoformat(),
                "due_date": invoice.due_date.isoformat(),
                "days_overdue": max(0, days_old),
                "balance": invoice.balance_due
            }

            if days_old <= 0:
                aging["current"].append(entry)
                aging["totals"]["current"] += invoice.balance_due
            elif days_old <= 30:
                aging["1_30"].append(entry)
                aging["totals"]["1_30"] += invoice.balance_due
            elif days_old <= 60:
                aging["31_60"].append(entry)
                aging["totals"]["31_60"] += invoice.balance_due
            elif days_old <= 90:
                aging["61_90"].append(entry)
                aging["totals"]["61_90"] += invoice.balance_due
            else:
                aging["over_90"].append(entry)
                aging["totals"]["over_90"] += invoice.balance_due

            aging["totals"]["total"] += invoice.balance_due

        # Round totals
        for key in aging["totals"]:
            aging["totals"][key] = round(aging["totals"][key], 2)

        return {
            "as_of_date": ref_date.isoformat(),
            "aging": aging
        }

    def get_customer_statement(self, customer_id: str, start_date: str, end_date: str) -> Dict:
        """Generate customer statement"""
        if customer_id not in self.customers:
            return {"error": "Customer not found"}

        customer = self.customers[customer_id]
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Calculate opening balance
        opening_balance = customer.opening_balance

        for invoice in self.invoices.values():
            if invoice.customer_id != customer_id:
                continue
            if invoice.status == InvoiceStatus.VOIDED:
                continue
            if invoice.invoice_date < s_date:
                opening_balance += invoice.total

        for payment in self.payments.values():
            if payment.customer_id != customer_id:
                continue
            if payment.is_voided:
                continue
            if payment.payment_date < s_date:
                opening_balance -= payment.total_amount

        # Get transactions in period
        transactions = []
        running_balance = opening_balance

        # Collect all transactions
        all_trans = []

        for invoice in self.invoices.values():
            if invoice.customer_id != customer_id:
                continue
            if invoice.status == InvoiceStatus.VOIDED:
                continue
            if s_date <= invoice.invoice_date <= e_date:
                all_trans.append({
                    "date": invoice.invoice_date,
                    "type": "Invoice",
                    "number": invoice.invoice_number,
                    "description": invoice.memo or f"Invoice {invoice.invoice_number}",
                    "amount": invoice.total,
                    "payment": 0
                })

        for payment in self.payments.values():
            if payment.customer_id != customer_id:
                continue
            if payment.is_voided:
                continue
            if s_date <= payment.payment_date <= e_date:
                all_trans.append({
                    "date": payment.payment_date,
                    "type": "Payment",
                    "number": payment.reference_number or payment.payment_id[:8],
                    "description": payment.memo or "Payment received",
                    "amount": 0,
                    "payment": payment.total_amount
                })

        # Sort by date
        all_trans.sort(key=lambda t: t["date"])

        for trans in all_trans:
            running_balance += trans["amount"] - trans["payment"]
            transactions.append({
                "date": trans["date"].isoformat(),
                "type": trans["type"],
                "number": trans["number"],
                "description": trans["description"],
                "charges": trans["amount"],
                "payments": trans["payment"],
                "balance": round(running_balance, 2)
            })

        return {
            "customer": self._customer_to_dict(customer),
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
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        invoice_total = 0.0
        invoice_count = 0
        receipt_total = 0.0
        receipt_count = 0
        payments_received = 0.0
        payment_count = 0

        by_customer = {}

        for invoice in self.invoices.values():
            if invoice.status == InvoiceStatus.VOIDED:
                continue
            if s_date <= invoice.invoice_date <= e_date:
                invoice_total += invoice.total
                invoice_count += 1

                cust_name = self.customers[invoice.customer_id].display_name if invoice.customer_id in self.customers else "Unknown"
                if cust_name not in by_customer:
                    by_customer[cust_name] = 0
                by_customer[cust_name] += invoice.total

        for receipt in self.sales_receipts.values():
            if receipt.is_voided:
                continue
            if s_date <= receipt.receipt_date <= e_date:
                receipt_total += receipt.total
                receipt_count += 1

        for payment in self.payments.values():
            if payment.is_voided:
                continue
            if s_date <= payment.payment_date <= e_date:
                payments_received += payment.total_amount
                payment_count += 1

        top_customers = sorted(
            [{"customer": k, "total": round(v, 2)} for k, v in by_customer.items()],
            key=lambda x: x["total"],
            reverse=True
        )[:10]

        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_invoiced": round(invoice_total, 2),
            "invoice_count": invoice_count,
            "total_receipts": round(receipt_total, 2),
            "receipt_count": receipt_count,
            "total_sales": round(invoice_total + receipt_total, 2),
            "payments_received": round(payments_received, 2),
            "payment_count": payment_count,
            "top_customers": top_customers
        }

    # ==================== UTILITY METHODS ====================

    def _customer_to_dict(self, customer: Customer) -> Dict:
        """Convert Customer to dictionary"""
        return {
            "customer_id": customer.customer_id,
            "company_name": customer.company_name,
            "display_name": customer.display_name,
            "contact_name": customer.contact_name,
            "email": customer.email,
            "phone": customer.phone,
            "mobile": customer.mobile,
            "website": customer.website,
            "billing_address": {
                "line1": customer.billing_address_line1,
                "line2": customer.billing_address_line2,
                "city": customer.billing_city,
                "state": customer.billing_state,
                "zip": customer.billing_zip,
                "country": customer.billing_country
            },
            "shipping_address": {
                "line1": customer.shipping_address_line1,
                "line2": customer.shipping_address_line2,
                "city": customer.shipping_city,
                "state": customer.shipping_state,
                "zip": customer.shipping_zip,
                "country": customer.shipping_country
            },
            "tax_exempt": customer.tax_exempt,
            "tax_id": customer.tax_id,
            "default_income_account_id": customer.default_income_account_id,
            "payment_terms": customer.payment_terms,
            "credit_limit": customer.credit_limit,
            "customer_type": customer.customer_type,
            "notes": customer.notes,
            "status": customer.status.value,
            "created_at": customer.created_at.isoformat(),
            "updated_at": customer.updated_at.isoformat()
        }

    def _invoice_to_dict(self, invoice: Invoice) -> Dict:
        """Convert Invoice to dictionary"""
        customer_name = self.customers[invoice.customer_id].display_name if invoice.customer_id in self.customers else "Unknown"

        return {
            "invoice_id": invoice.invoice_id,
            "invoice_number": invoice.invoice_number,
            "customer_id": invoice.customer_id,
            "customer_name": customer_name,
            "invoice_date": invoice.invoice_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "po_number": invoice.po_number,
            "terms": invoice.terms,
            "memo": invoice.memo,
            "message_on_invoice": invoice.message_on_invoice,
            "billing_address": invoice.billing_address,
            "shipping_address": invoice.shipping_address,
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
                    "discount_percent": line.discount_percent,
                    "discount_amount": line.discount_amount,
                    "class_id": line.class_id,
                    "location_id": line.location_id,
                    "service_date": line.service_date.isoformat() if line.service_date else None
                }
                for line in invoice.lines
            ],
            "subtotal": invoice.subtotal,
            "discount_total": invoice.discount_total,
            "tax_total": invoice.tax_total,
            "total": invoice.total,
            "amount_paid": invoice.amount_paid,
            "balance_due": invoice.balance_due,
            "status": invoice.status.value,
            "email_sent": invoice.email_sent,
            "email_sent_date": invoice.email_sent_date.isoformat() if invoice.email_sent_date else None,
            "estimate_id": invoice.estimate_id,
            "journal_entry_id": invoice.journal_entry_id,
            "created_at": invoice.created_at.isoformat(),
            "updated_at": invoice.updated_at.isoformat()
        }

    def _payment_to_dict(self, payment: PaymentReceived) -> Dict:
        """Convert PaymentReceived to dictionary"""
        customer_name = self.customers[payment.customer_id].display_name if payment.customer_id in self.customers else "Unknown"

        return {
            "payment_id": payment.payment_id,
            "payment_date": payment.payment_date.isoformat(),
            "customer_id": payment.customer_id,
            "customer_name": customer_name,
            "deposit_account_id": payment.deposit_account_id,
            "payment_method": payment.payment_method.value,
            "reference_number": payment.reference_number,
            "memo": payment.memo,
            "total_amount": payment.total_amount,
            "applied_invoices": payment.applied_invoices,
            "unapplied_amount": payment.unapplied_amount,
            "is_voided": payment.is_voided,
            "journal_entry_id": payment.journal_entry_id,
            "created_at": payment.created_at.isoformat()
        }

    def _credit_to_dict(self, credit: CustomerCredit) -> Dict:
        """Convert CustomerCredit to dictionary"""
        customer_name = self.customers[credit.customer_id].display_name if credit.customer_id in self.customers else "Unknown"

        return {
            "credit_id": credit.credit_id,
            "credit_number": credit.credit_number,
            "customer_id": credit.customer_id,
            "customer_name": customer_name,
            "credit_date": credit.credit_date.isoformat(),
            "reason": credit.reason,
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
            "related_invoice_id": credit.related_invoice_id,
            "journal_entry_id": credit.journal_entry_id,
            "created_at": credit.created_at.isoformat()
        }

    def _estimate_to_dict(self, estimate: Estimate) -> Dict:
        """Convert Estimate to dictionary"""
        customer_name = self.customers[estimate.customer_id].display_name if estimate.customer_id in self.customers else "Unknown"

        return {
            "estimate_id": estimate.estimate_id,
            "estimate_number": estimate.estimate_number,
            "customer_id": estimate.customer_id,
            "customer_name": customer_name,
            "estimate_date": estimate.estimate_date.isoformat(),
            "expiration_date": estimate.expiration_date.isoformat(),
            "po_number": estimate.po_number,
            "terms": estimate.terms,
            "memo": estimate.memo,
            "message_to_customer": estimate.message_to_customer,
            "lines": [
                {
                    "line_id": line.line_id,
                    "account_id": line.account_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "amount": line.amount,
                    "tax_amount": line.tax_amount
                }
                for line in estimate.lines
            ],
            "subtotal": estimate.subtotal,
            "tax_total": estimate.tax_total,
            "total": estimate.total,
            "status": estimate.status.value,
            "accepted_date": estimate.accepted_date.isoformat() if estimate.accepted_date else None,
            "converted_invoice_id": estimate.converted_invoice_id,
            "created_at": estimate.created_at.isoformat(),
            "updated_at": estimate.updated_at.isoformat()
        }

    def _receipt_to_dict(self, receipt: SalesReceipt) -> Dict:
        """Convert SalesReceipt to dictionary"""
        customer_name = None
        if receipt.customer_id and receipt.customer_id in self.customers:
            customer_name = self.customers[receipt.customer_id].display_name

        return {
            "receipt_id": receipt.receipt_id,
            "receipt_number": receipt.receipt_number,
            "customer_id": receipt.customer_id,
            "customer_name": customer_name,
            "receipt_date": receipt.receipt_date.isoformat(),
            "payment_method": receipt.payment_method.value,
            "deposit_account_id": receipt.deposit_account_id,
            "reference_number": receipt.reference_number,
            "memo": receipt.memo,
            "lines": [
                {
                    "line_id": line.line_id,
                    "account_id": line.account_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "amount": line.amount,
                    "tax_amount": line.tax_amount
                }
                for line in receipt.lines
            ],
            "subtotal": receipt.subtotal,
            "tax_total": receipt.tax_total,
            "total": receipt.total,
            "is_voided": receipt.is_voided,
            "journal_entry_id": receipt.journal_entry_id,
            "created_at": receipt.created_at.isoformat()
        }

    def get_service_summary(self) -> Dict:
        """Get GenFin Receivables service summary"""
        total_customers = len(self.customers)
        active_customers = sum(1 for c in self.customers.values() if c.status == CustomerStatus.ACTIVE)
        total_invoices = len(self.invoices)
        open_invoices = sum(1 for i in self.invoices.values() if i.status in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
        total_outstanding = sum(i.balance_due for i in self.invoices.values() if i.status in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])

        return {
            "service": "GenFin Receivables",
            "version": "1.0.0",
            "total_customers": total_customers,
            "active_customers": active_customers,
            "total_invoices": total_invoices,
            "open_invoices": open_invoices,
            "total_outstanding": round(total_outstanding, 2),
            "total_payments": len(self.payments),
            "total_credits": len(self.credits),
            "total_estimates": len(self.estimates),
            "total_sales_receipts": len(self.sales_receipts)
        }


# Singleton instance
genfin_receivables_service = GenFinReceivablesService()
