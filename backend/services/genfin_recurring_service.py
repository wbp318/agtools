"""
GenFin Recurring Transactions Service
Handles scheduled automatic generation of bills, invoices, journal entries, and other transactions.
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import uuid
from dateutil.relativedelta import relativedelta


class RecurrenceFrequency(Enum):
    """How often the transaction repeats"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    SEMI_MONTHLY = "semi_monthly"  # 1st and 15th
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"


class RecurrenceType(Enum):
    """Type of recurring transaction"""
    INVOICE = "invoice"
    BILL = "bill"
    JOURNAL_ENTRY = "journal_entry"
    CHECK = "check"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    SALES_RECEIPT = "sales_receipt"
    CREDIT_MEMO = "credit_memo"
    VENDOR_CREDIT = "vendor_credit"
    PAYCHECK = "paycheck"


class RecurrenceStatus(Enum):
    """Status of the recurring template"""
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"
    COMPLETED = "completed"


@dataclass
class RecurringTemplate:
    """Template for recurring transactions"""
    template_id: str
    name: str
    recurrence_type: RecurrenceType
    frequency: RecurrenceFrequency

    # Schedule
    start_date: date
    end_date: Optional[date] = None  # None = no end
    next_date: Optional[date] = None
    last_generated: Optional[date] = None

    # Limits
    max_occurrences: Optional[int] = None  # None = unlimited
    occurrences_generated: int = 0

    # Transaction details
    amount: float = 0.0
    memo: str = ""

    # Entity references
    customer_id: Optional[str] = None
    vendor_id: Optional[str] = None
    account_id: Optional[str] = None
    bank_account_id: Optional[str] = None

    # Line items for invoices/bills
    line_items: List[Dict] = field(default_factory=list)

    # For journal entries
    journal_lines: List[Dict] = field(default_factory=list)

    # Options
    auto_generate: bool = True  # False = needs approval
    days_in_advance: int = 0  # Generate X days before due
    notify_on_generate: bool = True

    # Status
    status: RecurrenceStatus = RecurrenceStatus.ACTIVE

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None


@dataclass
class GeneratedTransaction:
    """Record of a generated transaction"""
    generation_id: str
    template_id: str
    transaction_type: RecurrenceType
    transaction_id: str  # ID of the created transaction
    generated_date: date
    due_date: date
    amount: float
    status: str  # "generated", "posted", "voided"
    created_at: datetime = field(default_factory=datetime.now)


class GenFinRecurringService:
    """
    Manages recurring transactions for GenFin.

    Features:
    - Create recurring templates for any transaction type
    - Multiple frequency options (daily to annually)
    - Auto-generate or require approval
    - Track generation history
    - Handle end dates and occurrence limits
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

        self.templates: Dict[str, RecurringTemplate] = {}
        self.generated_transactions: Dict[str, GeneratedTransaction] = {}

        self._initialized = True

    # ==================== TEMPLATE MANAGEMENT ====================

    def create_recurring_invoice(
        self,
        name: str,
        customer_id: str,
        frequency: str,
        base_amount: float,
        start_date: str,
        end_date: str = None,
        memo: str = "",
        line_items: List[Dict] = None,
        max_occurrences: int = None,
        auto_generate: bool = True,
        days_in_advance: int = 0
    ) -> Dict:
        """Create a recurring invoice template"""
        template_id = str(uuid.uuid4())

        if line_items is None:
            line_items = []

        total_amount = base_amount if base_amount > 0 else sum(item.get("quantity", 1) * item.get("rate", 0) for item in line_items)

        template = RecurringTemplate(
            template_id=template_id,
            name=name,
            recurrence_type=RecurrenceType.INVOICE,
            frequency=RecurrenceFrequency(frequency),
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            next_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            max_occurrences=max_occurrences,
            amount=total_amount,
            memo=memo,
            customer_id=customer_id,
            line_items=line_items,
            auto_generate=auto_generate,
            days_in_advance=days_in_advance
        )

        self.templates[template_id] = template

        return {
            "success": True,
            "template_id": template_id,
            "name": name,
            "frequency": frequency,
            "next_date": template.next_date.isoformat(),
            "amount": total_amount
        }

    def create_recurring_bill(
        self,
        name: str,
        vendor_id: str,
        frequency: str,
        base_amount: float,
        start_date: str,
        end_date: str = None,
        memo: str = "",
        expense_account: str = "6000",
        line_items: List[Dict] = None,
        max_occurrences: int = None,
        auto_generate: bool = True,
        days_in_advance: int = 0
    ) -> Dict:
        """Create a recurring bill template"""
        template_id = str(uuid.uuid4())

        if line_items is None:
            line_items = []

        total_amount = base_amount if base_amount > 0 else sum(item.get("quantity", 1) * item.get("rate", 0) for item in line_items)

        template = RecurringTemplate(
            template_id=template_id,
            name=name,
            recurrence_type=RecurrenceType.BILL,
            frequency=RecurrenceFrequency(frequency),
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            next_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            max_occurrences=max_occurrences,
            amount=total_amount,
            memo=memo,
            vendor_id=vendor_id,
            line_items=line_items,
            auto_generate=auto_generate,
            days_in_advance=days_in_advance
        )

        self.templates[template_id] = template

        return {
            "success": True,
            "template_id": template_id,
            "name": name,
            "frequency": frequency,
            "next_date": template.next_date.isoformat(),
            "amount": total_amount
        }

    def create_recurring_journal_entry(
        self,
        name: str,
        frequency: str,
        debit_account: str,
        credit_account: str,
        amount: float,
        start_date: str,
        end_date: str = None,
        memo: str = "",
        journal_lines: List[Dict] = None,
        max_occurrences: int = None,
        auto_generate: bool = True
    ) -> Dict:
        """Create a recurring journal entry template"""
        template_id = str(uuid.uuid4())

        # If journal_lines not provided, create from debit/credit accounts
        if journal_lines is None:
            journal_lines = [
                {"account": debit_account, "debit": amount, "credit": 0},
                {"account": credit_account, "debit": 0, "credit": amount}
            ]

        # Validate debits = credits
        total_debits = sum(line.get("debit", 0) for line in journal_lines)
        total_credits = sum(line.get("credit", 0) for line in journal_lines)

        if abs(total_debits - total_credits) > 0.01:
            return {"success": False, "error": "Debits must equal credits"}

        template = RecurringTemplate(
            template_id=template_id,
            name=name,
            recurrence_type=RecurrenceType.JOURNAL_ENTRY,
            frequency=RecurrenceFrequency(frequency),
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            next_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            max_occurrences=max_occurrences,
            amount=total_debits,
            memo=memo,
            journal_lines=journal_lines,
            auto_generate=auto_generate
        )

        self.templates[template_id] = template

        return {
            "success": True,
            "template_id": template_id,
            "name": name,
            "frequency": frequency,
            "next_date": template.next_date.isoformat(),
            "amount": total_debits
        }

    def create_recurring_transfer(
        self,
        name: str,
        from_account_id: str,
        to_account_id: str,
        amount: float,
        frequency: str,
        start_date: str,
        end_date: str = None,
        max_occurrences: int = None,
        memo: str = "",
        auto_generate: bool = True
    ) -> Dict:
        """Create a recurring transfer between accounts"""
        template_id = str(uuid.uuid4())

        template = RecurringTemplate(
            template_id=template_id,
            name=name,
            recurrence_type=RecurrenceType.TRANSFER,
            frequency=RecurrenceFrequency(frequency),
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            next_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            max_occurrences=max_occurrences,
            amount=amount,
            memo=memo,
            bank_account_id=from_account_id,
            account_id=to_account_id,  # Using account_id for destination
            auto_generate=auto_generate
        )

        self.templates[template_id] = template

        return {
            "success": True,
            "template_id": template_id,
            "name": name,
            "frequency": frequency,
            "next_date": template.next_date.isoformat(),
            "amount": amount
        }

    def create_recurring_check(
        self,
        name: str,
        vendor_id: str,
        bank_account_id: str,
        amount: float,
        frequency: str,
        start_date: str,
        end_date: str = None,
        max_occurrences: int = None,
        memo: str = "",
        auto_generate: bool = False  # Checks usually need approval
    ) -> Dict:
        """Create a recurring check template"""
        template_id = str(uuid.uuid4())

        template = RecurringTemplate(
            template_id=template_id,
            name=name,
            recurrence_type=RecurrenceType.CHECK,
            frequency=RecurrenceFrequency(frequency),
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None,
            next_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            max_occurrences=max_occurrences,
            amount=amount,
            memo=memo,
            vendor_id=vendor_id,
            bank_account_id=bank_account_id,
            auto_generate=auto_generate
        )

        self.templates[template_id] = template

        return {
            "success": True,
            "template_id": template_id,
            "name": name,
            "frequency": frequency,
            "next_date": template.next_date.isoformat(),
            "amount": amount
        }

    def update_template(self, template_id: str, **kwargs) -> Dict:
        """Update a recurring template"""
        if template_id not in self.templates:
            return {"success": False, "error": "Template not found"}

        template = self.templates[template_id]

        for key, value in kwargs.items():
            if hasattr(template, key):
                if key in ["start_date", "end_date", "next_date"] and isinstance(value, str):
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                elif key == "frequency":
                    value = RecurrenceFrequency(value)
                elif key == "status":
                    value = RecurrenceStatus(value)
                setattr(template, key, value)

        template.updated_at = datetime.now()

        return {
            "success": True,
            "template_id": template_id,
            "message": "Template updated"
        }

    def pause_template(self, template_id: str) -> Dict:
        """Pause a recurring template"""
        if template_id not in self.templates:
            return {"success": False, "error": "Template not found"}

        self.templates[template_id].status = RecurrenceStatus.PAUSED
        self.templates[template_id].updated_at = datetime.now()

        return {"success": True, "message": "Template paused"}

    def resume_template(self, template_id: str) -> Dict:
        """Resume a paused template"""
        if template_id not in self.templates:
            return {"success": False, "error": "Template not found"}

        template = self.templates[template_id]
        template.status = RecurrenceStatus.ACTIVE

        # Recalculate next date if it's in the past
        today = date.today()
        if template.next_date and template.next_date < today:
            template.next_date = self._calculate_next_date(template.next_date, template.frequency, today)

        template.updated_at = datetime.now()

        return {"success": True, "message": "Template resumed", "next_date": template.next_date.isoformat()}

    def delete_template(self, template_id: str) -> Dict:
        """Delete a recurring template"""
        if template_id not in self.templates:
            return {"success": False, "error": "Template not found"}

        del self.templates[template_id]
        return {"success": True, "message": "Template deleted"}

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a single template"""
        if template_id not in self.templates:
            return None
        return self._template_to_dict(self.templates[template_id])

    def list_templates(
        self,
        recurrence_type: str = None,
        status: str = None
    ) -> Dict:
        """List all recurring templates"""
        templates_list = []

        for template in self.templates.values():
            if recurrence_type and template.recurrence_type.value != recurrence_type:
                continue
            if status and template.status.value != status:
                continue
            templates_list.append(self._template_to_dict(template))

        # Sort by next date
        templates_list.sort(key=lambda x: x.get("next_date") or "9999-12-31")

        return {
            "templates": templates_list,
            "total": len(templates_list),
            "active": sum(1 for t in templates_list if t["status"] == "active")
        }

    # ==================== GENERATION ====================

    def _calculate_next_date(
        self,
        current_date: date,
        frequency: RecurrenceFrequency,
        min_date: date = None
    ) -> date:
        """Calculate the next occurrence date"""
        next_date = current_date

        while min_date and next_date <= min_date:
            if frequency == RecurrenceFrequency.DAILY:
                next_date += timedelta(days=1)
            elif frequency == RecurrenceFrequency.WEEKLY:
                next_date += timedelta(weeks=1)
            elif frequency == RecurrenceFrequency.BI_WEEKLY:
                next_date += timedelta(weeks=2)
            elif frequency == RecurrenceFrequency.SEMI_MONTHLY:
                if next_date.day < 15:
                    next_date = next_date.replace(day=15)
                else:
                    next_date = (next_date.replace(day=1) + relativedelta(months=1))
            elif frequency == RecurrenceFrequency.MONTHLY:
                next_date += relativedelta(months=1)
            elif frequency == RecurrenceFrequency.QUARTERLY:
                next_date += relativedelta(months=3)
            elif frequency == RecurrenceFrequency.SEMI_ANNUALLY:
                next_date += relativedelta(months=6)
            elif frequency == RecurrenceFrequency.ANNUALLY:
                next_date += relativedelta(years=1)

        if not min_date:
            # Just calculate next occurrence
            if frequency == RecurrenceFrequency.DAILY:
                next_date += timedelta(days=1)
            elif frequency == RecurrenceFrequency.WEEKLY:
                next_date += timedelta(weeks=1)
            elif frequency == RecurrenceFrequency.BI_WEEKLY:
                next_date += timedelta(weeks=2)
            elif frequency == RecurrenceFrequency.SEMI_MONTHLY:
                if next_date.day < 15:
                    next_date = next_date.replace(day=15)
                else:
                    next_date = (next_date.replace(day=1) + relativedelta(months=1))
            elif frequency == RecurrenceFrequency.MONTHLY:
                next_date += relativedelta(months=1)
            elif frequency == RecurrenceFrequency.QUARTERLY:
                next_date += relativedelta(months=3)
            elif frequency == RecurrenceFrequency.SEMI_ANNUALLY:
                next_date += relativedelta(months=6)
            elif frequency == RecurrenceFrequency.ANNUALLY:
                next_date += relativedelta(years=1)

        return next_date

    def get_due_transactions(self, as_of_date: str = None) -> Dict:
        """Get all transactions due for generation"""
        check_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()

        due_transactions = []

        for template in self.templates.values():
            if template.status != RecurrenceStatus.ACTIVE:
                continue

            if not template.next_date:
                continue

            # Check if due (including days_in_advance)
            due_date = template.next_date - timedelta(days=template.days_in_advance)

            if due_date <= check_date:
                # Check end date
                if template.end_date and template.next_date > template.end_date:
                    continue

                # Check max occurrences
                if template.max_occurrences and template.occurrences_generated >= template.max_occurrences:
                    continue

                due_transactions.append({
                    "template_id": template.template_id,
                    "name": template.name,
                    "type": template.recurrence_type.value,
                    "due_date": template.next_date.isoformat(),
                    "amount": template.amount,
                    "auto_generate": template.auto_generate,
                    "customer_id": template.customer_id,
                    "vendor_id": template.vendor_id
                })

        return {
            "due_transactions": due_transactions,
            "count": len(due_transactions),
            "as_of_date": check_date.isoformat()
        }

    def generate_transaction(self, template_id: str, transaction_date: str = None) -> Dict:
        """Generate a transaction from a template"""
        if template_id not in self.templates:
            return {"success": False, "error": "Template not found"}

        template = self.templates[template_id]

        if template.status != RecurrenceStatus.ACTIVE:
            return {"success": False, "error": "Template is not active"}

        gen_date = datetime.strptime(transaction_date, "%Y-%m-%d").date() if transaction_date else template.next_date

        # Create the generation record
        generation_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())  # In real impl, this would be the actual transaction ID

        generated = GeneratedTransaction(
            generation_id=generation_id,
            template_id=template_id,
            transaction_type=template.recurrence_type,
            transaction_id=transaction_id,
            generated_date=date.today(),
            due_date=gen_date,
            amount=template.amount,
            status="generated"
        )

        self.generated_transactions[generation_id] = generated

        # Update template
        template.occurrences_generated += 1
        template.last_generated = date.today()
        template.next_date = self._calculate_next_date(gen_date, template.frequency)
        template.updated_at = datetime.now()

        # Check if completed
        if template.max_occurrences and template.occurrences_generated >= template.max_occurrences:
            template.status = RecurrenceStatus.COMPLETED
        if template.end_date and template.next_date > template.end_date:
            template.status = RecurrenceStatus.EXPIRED

        return {
            "success": True,
            "generation_id": generation_id,
            "transaction_id": transaction_id,
            "type": template.recurrence_type.value,
            "amount": template.amount,
            "due_date": gen_date.isoformat(),
            "next_date": template.next_date.isoformat() if template.status == RecurrenceStatus.ACTIVE else None,
            "occurrences_generated": template.occurrences_generated
        }

    def generate_all_due(self, as_of_date: str = None) -> Dict:
        """Generate all due auto-generate transactions"""
        due = self.get_due_transactions(as_of_date)

        generated = []
        skipped = []

        for trans in due["due_transactions"]:
            if trans["auto_generate"]:
                result = self.generate_transaction(trans["template_id"], trans["due_date"])
                if result.get("success"):
                    generated.append(result)
                else:
                    skipped.append({"template_id": trans["template_id"], "error": result.get("error")})
            else:
                skipped.append({"template_id": trans["template_id"], "reason": "Requires manual approval"})

        return {
            "generated": generated,
            "generated_count": len(generated),
            "skipped": skipped,
            "skipped_count": len(skipped)
        }

    def get_generation_history(self, template_id: str = None, limit: int = 50) -> Dict:
        """Get history of generated transactions"""
        history = []

        for gen in self.generated_transactions.values():
            if template_id and gen.template_id != template_id:
                continue

            template = self.templates.get(gen.template_id)

            history.append({
                "generation_id": gen.generation_id,
                "template_id": gen.template_id,
                "template_name": template.name if template else "Unknown",
                "type": gen.transaction_type.value,
                "transaction_id": gen.transaction_id,
                "generated_date": gen.generated_date.isoformat(),
                "due_date": gen.due_date.isoformat(),
                "amount": gen.amount,
                "status": gen.status
            })

        # Sort by generated date descending
        history.sort(key=lambda x: x["generated_date"], reverse=True)

        return {
            "history": history[:limit],
            "total": len(history)
        }

    # ==================== UTILITIES ====================

    def _template_to_dict(self, template: RecurringTemplate) -> Dict:
        """Convert template to dictionary"""
        return {
            "template_id": template.template_id,
            "name": template.name,
            "type": template.recurrence_type.value,
            "frequency": template.frequency.value,
            "start_date": template.start_date.isoformat(),
            "end_date": template.end_date.isoformat() if template.end_date else None,
            "next_date": template.next_date.isoformat() if template.next_date else None,
            "last_generated": template.last_generated.isoformat() if template.last_generated else None,
            "max_occurrences": template.max_occurrences,
            "occurrences_generated": template.occurrences_generated,
            "amount": template.amount,
            "memo": template.memo,
            "customer_id": template.customer_id,
            "vendor_id": template.vendor_id,
            "auto_generate": template.auto_generate,
            "days_in_advance": template.days_in_advance,
            "status": template.status.value,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        active = sum(1 for t in self.templates.values() if t.status == RecurrenceStatus.ACTIVE)
        paused = sum(1 for t in self.templates.values() if t.status == RecurrenceStatus.PAUSED)

        by_type = {}
        for t in self.templates.values():
            type_name = t.recurrence_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            "service": "GenFin Recurring Transactions",
            "version": "1.0.0",
            "features": [
                "Recurring Invoices",
                "Recurring Bills",
                "Recurring Journal Entries",
                "Recurring Transfers",
                "Recurring Checks",
                "Multiple Frequencies (Daily to Annually)",
                "Auto-Generate or Manual Approval",
                "End Dates and Occurrence Limits"
            ],
            "total_templates": len(self.templates),
            "active_templates": active,
            "paused_templates": paused,
            "templates_by_type": by_type,
            "total_generated": len(self.generated_transactions)
        }


# Singleton instance
genfin_recurring_service = GenFinRecurringService()
