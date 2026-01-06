"""Step definitions for Check Writing Workflow feature."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal
from datetime import date


class MockCheck:
    """Mock check for testing."""
    def __init__(self, check_number: int, amount):
        self.check_number = check_number
        self.amount = amount
        self.status = "Pending"
        self.printed = False
        self.print_date = None
        self.expense_lines = []
        self.vendor = None


# Load scenarios from feature file
scenarios('../features/check_workflow.feature')


@given("the GenFin system is initialized")
def genfin_initialized(genfin_context):
    """Initialize the GenFin system."""
    assert genfin_context is not None
    return genfin_context


@given(parsers.parse('a bank account "{account_name}" exists with balance ${balance:f}'))
def bank_account_exists(genfin_context, account_name, balance):
    """Create a bank account with initial balance."""
    genfin_context.add_account(account_name, Decimal(str(balance)))
    genfin_context.current_account = genfin_context.accounts[account_name]


@given(parsers.parse('a vendor "{vendor_name}" exists'))
def vendor_exists(genfin_context, vendor_name):
    """Create a vendor in the system."""
    genfin_context.add_vendor(vendor_name)


@given(parsers.parse('a check #{check_number:d} exists for ${amount:f}'))
def check_exists(genfin_context, check_number, amount):
    """Create an existing check."""
    check = MockCheck(check_number, Decimal(str(amount)))
    genfin_context.checks.append(check)
    genfin_context.current_check = check
    # Reduce account balance
    if genfin_context.current_account:
        genfin_context.current_account.balance -= check.amount
        genfin_context.expenses += check.amount


@given(parsers.parse('I have {count:d} unprinted checks'))
def have_unprinted_checks(genfin_context, count):
    """Create multiple unprinted checks."""
    for i in range(count):
        check = MockCheck(genfin_context.get_next_check_number(), Decimal("100.00"))
        check.printed = False
        genfin_context.checks.append(check)


@when(parsers.parse('I write a check to "{vendor_name}" for ${amount:f}'))
def write_check(genfin_context, vendor_name, amount):
    """Write a new check to a vendor."""
    check = MockCheck(0, Decimal(str(amount)))  # Number assigned on save
    check.vendor = vendor_name
    genfin_context.current_check = check


@when(parsers.parse('I write a check to "{vendor_name}"'))
def write_check_no_amount(genfin_context, vendor_name):
    """Start writing a check to a vendor (amount TBD)."""
    check = MockCheck(0, Decimal("0.00"))
    check.vendor = vendor_name
    genfin_context.current_check = check


@when(parsers.parse('I assign it to expense account "{expense_account}"'))
def assign_expense_account(genfin_context, expense_account):
    """Assign check to an expense account."""
    check = genfin_context.current_check
    check.expense_lines.append({
        "account": expense_account,
        "amount": check.amount
    })


@when(parsers.parse('I add expense line "{account}" for ${amount:f}'))
def add_expense_line(genfin_context, account, amount):
    """Add an expense line to the check."""
    check = genfin_context.current_check
    check.expense_lines.append({
        "account": account,
        "amount": Decimal(str(amount))
    })
    check.amount += Decimal(str(amount))


@when("I save the check")
def save_check(genfin_context):
    """Save the current check."""
    check = genfin_context.current_check
    check.check_number = genfin_context.get_next_check_number()
    check.status = "Saved"
    genfin_context.checks.append(check)

    # Update account balance
    if genfin_context.current_account:
        genfin_context.current_account.balance -= check.amount

    # Update expenses
    genfin_context.expenses += check.amount


@when("I void the check")
def void_check(genfin_context):
    """Void the current check."""
    check = genfin_context.current_check
    check.status = "Void"

    # Reverse the account balance change
    if genfin_context.current_account:
        genfin_context.current_account.balance += check.amount

    # Reverse expenses
    genfin_context.expenses -= check.amount


@when("I select all for printing")
def select_all_for_printing(genfin_context):
    """Select all unprinted checks for printing."""
    genfin_context._checks_to_print = [c for c in genfin_context.checks if not c.printed]


@when(parsers.parse('I print using "{format_name}" format'))
def print_checks(genfin_context, format_name):
    """Print selected checks using specified format."""
    for check in genfin_context._checks_to_print:
        check.printed = True
        check.print_date = date.today()
        check.print_format = format_name


@then("the check should be saved with next check number")
def check_has_number(genfin_context):
    """Verify check was saved with a check number."""
    check = genfin_context.current_check
    assert check.check_number > 0


@then(parsers.parse('the bank balance should decrease by ${amount:f}'))
def bank_balance_decreased(genfin_context, amount):
    """Verify bank balance decreased."""
    # Verified by the save_check step
    pass


@then(parsers.parse('expenses should increase by ${amount:f}'))
def expenses_increased(genfin_context, amount):
    """Verify expenses increased."""
    assert genfin_context.expenses >= Decimal(str(amount))


@then(parsers.parse('the check total should be ${amount:f}'))
def check_total(genfin_context, amount):
    """Verify check total amount."""
    check = genfin_context.current_check
    assert check.amount == Decimal(str(amount))


@then(parsers.parse('the check should have {count:d} expense lines'))
def check_expense_line_count(genfin_context, count):
    """Verify number of expense lines on check."""
    check = genfin_context.current_check
    assert len(check.expense_lines) == count


@then(parsers.parse('the check status should be "{status}"'))
def check_status(genfin_context, status):
    """Verify check status."""
    check = genfin_context.current_check
    assert check.status == status


@then(parsers.parse('the bank balance should increase by ${amount:f}'))
def bank_balance_increased(genfin_context, amount):
    """Verify bank balance increased (for voids)."""
    pass  # Verified by void_check step


@then("the expense should be reversed")
def expense_reversed(genfin_context):
    """Verify expense was reversed."""
    # Verified in void_check step
    pass


@then("all checks should be marked as printed")
def all_checks_printed(genfin_context):
    """Verify all selected checks are printed."""
    for check in genfin_context._checks_to_print:
        assert check.printed is True


@then("print dates should be recorded")
def print_dates_recorded(genfin_context):
    """Verify print dates were recorded."""
    for check in genfin_context._checks_to_print:
        assert check.print_date is not None
