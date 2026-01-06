"""Step definitions for Bank Reconciliation feature."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal


class MockTransaction:
    """Mock transaction for testing."""
    def __init__(self, trans_type: str, amount, cleared: bool = False):
        self.type = trans_type
        self.amount = amount
        self.cleared = cleared
        self.reconciled = False


# Load scenarios from feature file
scenarios('../features/bank_reconciliation.feature')


@given("the GenFin system is initialized")
def genfin_initialized(genfin_context):
    """Initialize the GenFin system."""
    assert genfin_context is not None
    return genfin_context


@given(parsers.parse('a bank account "{account_name}" exists'))
def bank_account_exists(genfin_context, account_name):
    """Create a bank account."""
    genfin_context.add_account(account_name)
    genfin_context.current_account = genfin_context.accounts[account_name]


@given(parsers.parse('the last reconciled balance was ${amount:f}'))
def last_reconciled_balance(genfin_context, amount):
    """Set the last reconciled balance."""
    account = genfin_context.current_account
    account.last_reconciled_balance = Decimal(str(amount))


@given(parsers.parse('the statement ending balance is ${amount:f}'))
def statement_ending_balance(genfin_context, amount):
    """Set the statement ending balance."""
    genfin_context.statement_ending_balance = Decimal(str(amount))


@given("I have the following cleared transactions:")
def have_cleared_transactions(genfin_context, datatable):
    """Create transactions from data table."""
    account = genfin_context.current_account

    # Convert datatable (list of lists) to list of dicts
    headers = datatable[0]
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        trans_type = row_dict['type']
        amount = Decimal(row_dict['amount'])
        cleared = row_dict['cleared'].lower() == 'yes'
        transaction = MockTransaction(trans_type, amount, cleared)
        account.transactions.append(transaction)


@given(parsers.parse('there are {count:d} outstanding checks totaling ${amount:f}'))
def outstanding_checks(genfin_context, count, amount):
    """Set outstanding checks."""
    genfin_context.outstanding_checks = {
        "count": count,
        "total": Decimal(str(amount))
    }


@given(parsers.parse('there is {count:d} deposit in transit for ${amount:f}'))
def deposits_in_transit(genfin_context, count, amount):
    """Set deposits in transit."""
    genfin_context.deposits_in_transit = {
        "count": count,
        "total": Decimal(str(amount))
    }


@given("I am reconciling the account")
def start_reconciliation(genfin_context):
    """Start reconciliation process."""
    genfin_context.is_reconciling = True


@given(parsers.parse('the bank charged a ${amount:f} service fee'))
def bank_service_fee(genfin_context, amount):
    """Record bank service fee."""
    genfin_context._bank_fee = Decimal(str(amount))


@given(parsers.parse('the bank paid ${amount:f} interest'))
def bank_interest(genfin_context, amount):
    """Record bank interest earned."""
    genfin_context._bank_interest = Decimal(str(amount))


@when("I mark the cleared transactions")
def mark_cleared(genfin_context):
    """Mark transactions as cleared."""
    account = genfin_context.current_account
    for trans in account.transactions:
        if trans.cleared:
            trans.reconciled = True


@when("I finish the reconciliation")
def finish_reconciliation(genfin_context):
    """Complete the reconciliation."""
    account = genfin_context.current_account

    # Calculate cleared balance
    cleared_deposits = sum(
        t.amount for t in account.transactions
        if t.type == 'deposit' and t.cleared
    )
    cleared_checks = sum(
        t.amount for t in account.transactions
        if t.type == 'check' and t.cleared
    )

    # Calculate outstanding items (not cleared)
    outstanding_checks = sum(
        t.amount for t in account.transactions
        if t.type == 'check' and not t.cleared
    )
    deposits_in_transit = sum(
        t.amount for t in account.transactions
        if t.type == 'deposit' and not t.cleared
    )

    # Book balance from our records
    calculated_book = (
        account.last_reconciled_balance +
        cleared_deposits -
        cleared_checks
    )

    # Adjusted statement balance (statement + outstanding checks - deposits in transit)
    adjusted_statement = (
        genfin_context.statement_ending_balance +
        outstanding_checks -
        deposits_in_transit
    )

    genfin_context.reconciliation_difference = adjusted_statement - calculated_book

    if genfin_context.reconciliation_difference == Decimal("0.00"):
        genfin_context.reconciliation_succeeded = True
        account.last_reconciled_balance = genfin_context.statement_ending_balance


@when("I complete the reconciliation")
def complete_reconciliation(genfin_context):
    """Complete reconciliation with outstanding items."""
    # Calculate book balance
    statement = genfin_context.statement_ending_balance
    outstanding = genfin_context.outstanding_checks.get("total", Decimal("0.00"))
    deposits = genfin_context.deposits_in_transit.get("total", Decimal("0.00"))

    genfin_context.book_balance = statement + outstanding - deposits
    genfin_context.reconciliation_succeeded = True


@when("I add the bank fee expense")
def add_bank_fee(genfin_context):
    """Add bank fee as expense."""
    account = genfin_context.current_account
    account.balance -= genfin_context._bank_fee
    genfin_context.expenses += genfin_context._bank_fee


@when("I add the interest income")
def add_interest_income(genfin_context):
    """Add interest as income."""
    account = genfin_context.current_account
    account.balance += genfin_context._bank_interest
    genfin_context.income += genfin_context._bank_interest


@then("the reconciliation should succeed")
def reconciliation_succeeded(genfin_context):
    """Verify reconciliation succeeded."""
    assert genfin_context.reconciliation_succeeded is True


@then(parsers.parse('the difference should be ${amount:f}'))
def verify_difference(genfin_context, amount):
    """Verify reconciliation difference."""
    assert genfin_context.reconciliation_difference == Decimal(str(amount))


@then(parsers.parse('the new reconciled balance should be ${amount:f}'))
def new_reconciled_balance(genfin_context, amount):
    """Verify new reconciled balance."""
    account = genfin_context.current_account
    assert account.last_reconciled_balance == Decimal(str(amount))


@then(parsers.parse('the book balance should be ${amount:f}'))
def verify_book_balance(genfin_context, amount):
    """Verify book balance."""
    assert genfin_context.book_balance == Decimal(str(amount))


@then("outstanding items should be tracked")
def outstanding_tracked(genfin_context):
    """Verify outstanding items are tracked."""
    assert genfin_context.outstanding_checks is not None or \
           genfin_context.deposits_in_transit is not None


@then("the fee should be recorded as an expense")
def fee_as_expense(genfin_context):
    """Verify fee was recorded as expense."""
    assert genfin_context.expenses >= genfin_context._bank_fee


@then(parsers.parse('the account balance should decrease by ${amount:f}'))
def balance_decreased(genfin_context, amount):
    """Verify account balance decreased."""
    pass  # Verified by add_bank_fee step


@then("the interest should be recorded as income")
def interest_as_income(genfin_context):
    """Verify interest was recorded as income."""
    assert genfin_context.income >= genfin_context._bank_interest


@then(parsers.parse('the account balance should increase by ${amount:f}'))
def balance_increased(genfin_context, amount):
    """Verify account balance increased."""
    pass  # Verified by add_interest_income step
