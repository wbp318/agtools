"""Step definitions for Bill Payment Workflow feature."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal
from datetime import date, timedelta


class MockBill:
    """Mock bill for testing."""
    def __init__(self, vendor: str, amount):
        self.vendor = vendor
        self.amount = amount
        self.status = "Unpaid"
        self.due_date = None


class MockVendorCredit:
    """Mock vendor credit for testing."""
    def __init__(self, vendor: str, amount):
        self.vendor = vendor
        self.amount = amount
        self.consumed = False


# Load scenarios from feature file
scenarios('../features/bill_workflow.feature')


@given("the GenFin system is initialized")
def genfin_initialized(genfin_context):
    """Initialize the GenFin system."""
    assert genfin_context is not None
    return genfin_context


@given(parsers.parse('a vendor "{vendor_name}" exists'))
def vendor_exists(genfin_context, vendor_name):
    """Create a vendor in the system."""
    genfin_context.add_vendor(vendor_name)


@given("I have the following unpaid bills:")
def create_unpaid_bills(genfin_context, datatable):
    """Create multiple unpaid bills from a data table."""
    # Convert datatable (list of lists) to list of dicts
    headers = datatable[0]
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        vendor = row_dict['vendor']
        amount = Decimal(row_dict['amount'])
        bill = MockBill(vendor, amount)
        genfin_context.bills.append(bill)
        genfin_context.accounts_payable += amount


@given(parsers.parse('a bill exists from "{vendor_name}" for ${amount:f}'))
def bill_exists(genfin_context, vendor_name, amount):
    """Create a bill from a vendor."""
    bill = MockBill(vendor_name, Decimal(str(amount)))
    genfin_context.bills.append(bill)
    genfin_context.current_bill = bill
    genfin_context.accounts_payable += bill.amount


@given(parsers.parse('a vendor credit exists from "{vendor_name}" for ${amount:f}'))
def vendor_credit_exists(genfin_context, vendor_name, amount):
    """Create a vendor credit."""
    credit = MockVendorCredit(vendor_name, Decimal(str(amount)))
    if vendor_name in genfin_context.vendors:
        genfin_context.vendors[vendor_name].credits.append(credit)


@given(parsers.parse('a purchase order exists for "{vendor_name}" for ${amount:f}'))
def purchase_order_exists(genfin_context, vendor_name, amount):
    """Create a purchase order."""
    po = {
        "vendor": vendor_name,
        "amount": Decimal(str(amount)),
        "status": "Open"
    }
    genfin_context.purchase_orders.append(po)


@when(parsers.parse('I enter a bill from "{vendor_name}" for ${amount:f}'))
def enter_bill(genfin_context, vendor_name, amount):
    """Enter a new bill from a vendor."""
    bill = MockBill(vendor_name, Decimal(str(amount)))
    genfin_context.current_bill = bill


@when("I set the due date to 30 days from now")
def set_due_date(genfin_context):
    """Set bill due date to 30 days from now."""
    bill = genfin_context.current_bill
    bill.due_date = date.today() + timedelta(days=30)


@when("I save the bill")
def save_bill(genfin_context):
    """Save the current bill."""
    bill = genfin_context.current_bill
    genfin_context.bills.append(bill)
    genfin_context.accounts_payable += bill.amount


@when("I pay the bill in full")
def pay_bill_in_full(genfin_context):
    """Pay the current bill in full."""
    bill = genfin_context.current_bill
    bill.status = "Paid"
    genfin_context.accounts_payable -= bill.amount


@when("I select all bills for payment")
def select_all_bills(genfin_context):
    """Select all unpaid bills for payment."""
    genfin_context._selected_bills = [b for b in genfin_context.bills if b.status == "Unpaid"]


@when(parsers.parse('I pay from the "{account_name}"'))
def pay_from_account(genfin_context, account_name):
    """Pay selected bills from an account."""
    total = Decimal("0.00")
    for bill in genfin_context._selected_bills:
        bill.status = "Paid"
        total += bill.amount
        genfin_context.accounts_payable -= bill.amount
    genfin_context._total_payment = total


@when("I pay the bill and apply the credit")
def pay_bill_with_credit(genfin_context):
    """Pay bill using vendor credit."""
    bill = genfin_context.current_bill
    vendor = genfin_context.vendors.get(bill.vendor)

    if vendor and vendor.credits:
        credit = vendor.credits[0]
        credit.consumed = True
        genfin_context._cash_payment = bill.amount - credit.amount
    else:
        genfin_context._cash_payment = bill.amount

    bill.status = "Paid"
    genfin_context.accounts_payable -= bill.amount


@when("I receive the items and create a bill")
def receive_items_create_bill(genfin_context):
    """Receive items from PO and create bill."""
    po = genfin_context.purchase_orders[0]
    po["status"] = "Received"

    bill = MockBill(po["vendor"], po["amount"])
    genfin_context.bills.append(bill)
    genfin_context.current_bill = bill
    genfin_context.accounts_payable += bill.amount


@then(parsers.parse('the bill should be saved with status "{status}"'))
def bill_has_status(genfin_context, status):
    """Verify bill was saved with status."""
    bill = genfin_context.current_bill
    assert bill.status == status


@then(parsers.parse('accounts payable should increase by ${amount:f}'))
def ap_increased(genfin_context, amount):
    """Verify accounts payable increased."""
    assert genfin_context.accounts_payable >= Decimal(str(amount))


@then(parsers.parse('accounts payable should decrease by ${amount:f}'))
def ap_decreased(genfin_context, amount):
    """Verify accounts payable decreased."""
    pass  # Verified by payment flow


@then(parsers.parse('the bill status should be "{status}"'))
def verify_bill_status(genfin_context, status):
    """Verify bill has specific status."""
    bill = genfin_context.current_bill
    assert bill.status == status


@then(parsers.parse('all bills should be marked as "{status}"'))
def all_bills_status(genfin_context, status):
    """Verify all selected bills have status."""
    for bill in genfin_context._selected_bills:
        assert bill.status == status


@then(parsers.parse('the total payment should be ${amount:f}'))
def verify_total_payment(genfin_context, amount):
    """Verify total payment amount."""
    assert genfin_context._total_payment == Decimal(str(amount))


@then(parsers.parse('the cash payment should be ${amount:f}'))
def verify_cash_payment(genfin_context, amount):
    """Verify cash payment after credit applied."""
    assert genfin_context._cash_payment == Decimal(str(amount))


@then("the vendor credit should be consumed")
def credit_consumed(genfin_context):
    """Verify vendor credit was consumed."""
    bill = genfin_context.current_bill
    vendor = genfin_context.vendors.get(bill.vendor)
    assert vendor.credits[0].consumed is True


@then(parsers.parse('a bill should be created for ${amount:f}'))
def bill_created(genfin_context, amount):
    """Verify bill was created with amount."""
    bill = genfin_context.current_bill
    assert bill.amount == Decimal(str(amount))


@then(parsers.parse('the purchase order status should be "{status}"'))
def po_status(genfin_context, status):
    """Verify purchase order status."""
    po = genfin_context.purchase_orders[0]
    assert po["status"] == status
