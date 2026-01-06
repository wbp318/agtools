"""Pytest configuration and shared fixtures for GenFin BDD tests."""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import MagicMock


class MockAccount:
    """Mock bank account for testing."""
    def __init__(self, name: str, balance: Decimal = Decimal("0.00")):
        self.name = name
        self.balance = balance
        self.last_reconciled_balance = Decimal("0.00")
        self.transactions = []


class MockVendor:
    """Mock vendor for testing."""
    def __init__(self, name: str):
        self.name = name
        self.credits = []


class MockCustomer:
    """Mock customer for testing."""
    def __init__(self, name: str):
        self.name = name


class MockTransaction:
    """Mock transaction for testing."""
    def __init__(self, trans_type: str, amount: Decimal, cleared: bool = False):
        self.type = trans_type
        self.amount = amount
        self.cleared = cleared


class MockBill:
    """Mock bill for testing."""
    def __init__(self, vendor: str, amount: Decimal):
        self.vendor = vendor
        self.amount = amount
        self.status = "Unpaid"
        self.due_date = None


class MockInvoice:
    """Mock invoice for testing."""
    def __init__(self, customer: str, amount: Decimal = Decimal("0.00")):
        self.customer = customer
        self.amount = amount
        self.balance_due = amount
        self.status = "Open"
        self.line_items = []


class MockCheck:
    """Mock check for testing."""
    def __init__(self, check_number: int, amount: Decimal):
        self.check_number = check_number
        self.amount = amount
        self.status = "Pending"
        self.printed = False
        self.print_date = None
        self.expense_lines = []


class MockVendorCredit:
    """Mock vendor credit for testing."""
    def __init__(self, vendor: str, amount: Decimal):
        self.vendor = vendor
        self.amount = amount
        self.consumed = False


class GenFinTestContext:
    """Shared test context for GenFin BDD tests."""

    def __init__(self):
        self.accounts = {}
        self.vendors = {}
        self.customers = {}
        self.bills = []
        self.invoices = []
        self.checks = []
        self.purchase_orders = []
        self.next_check_number = 1001
        self.accounts_receivable = Decimal("0.00")
        self.accounts_payable = Decimal("0.00")
        self.expenses = Decimal("0.00")
        self.income = Decimal("0.00")

        # Reconciliation state
        self.statement_ending_balance = Decimal("0.00")
        self.outstanding_checks = []
        self.deposits_in_transit = []
        self.book_balance = Decimal("0.00")
        self.reconciliation_difference = Decimal("0.00")
        self.reconciliation_succeeded = False
        self.is_reconciling = False

        # Current working objects
        self.current_invoice = None
        self.current_bill = None
        self.current_check = None
        self.current_account = None

    def add_account(self, name: str, balance: Decimal = Decimal("0.00")) -> MockAccount:
        account = MockAccount(name, balance)
        self.accounts[name] = account
        return account

    def add_vendor(self, name: str) -> MockVendor:
        vendor = MockVendor(name)
        self.vendors[name] = vendor
        return vendor

    def add_customer(self, name: str) -> MockCustomer:
        customer = MockCustomer(name)
        self.customers[name] = customer
        return customer

    def get_next_check_number(self) -> int:
        num = self.next_check_number
        self.next_check_number += 1
        return num


@pytest.fixture
def genfin_context():
    """Provide a fresh GenFin test context for each scenario."""
    return GenFinTestContext()


@pytest.fixture
def initialized_system(genfin_context):
    """Provide an initialized GenFin system context."""
    # System is considered initialized when context exists
    return genfin_context
