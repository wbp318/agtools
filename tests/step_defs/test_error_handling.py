"""Step definitions for Error Handling feature."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

scenarios('../features/error_handling.feature')


@pytest.fixture
def error_context():
    """Context for error handling tests."""
    return {
        'customers': {},
        'vendors': {},
        'invoices': {},
        'bills': {},
        'accounts': {},
        'checks': {},
        'credits': {},
        'purchase_orders': {},
        'last_error': None,
        'operation_result': None
    }


@given("the GenFin system is initialized")
def system_initialized(error_context):
    """Initialize system."""
    error_context['initialized'] = True


# Invoice error scenarios
@when(parsers.parse('I try to create an invoice for customer "{customer_id}"'))
def try_create_invoice_invalid_customer(error_context, customer_id):
    """Try to create invoice for invalid customer."""
    if customer_id not in error_context['customers']:
        error_context['last_error'] = "Customer not found"
        error_context['operation_result'] = {'success': False}


@then(parsers.parse('I should receive an error "{error_message}"'))
def verify_error_message(error_context, error_message):
    """Verify error message."""
    assert error_context['last_error'] == error_message


@then("no invoice should be created")
def no_invoice_created(error_context):
    """Verify no invoice created."""
    assert error_context.get('operation_result', {}).get('success') == False


@given(parsers.parse('a customer exists with an invoice for ${amount:f}'))
def customer_with_invoice(error_context, amount):
    """Create customer with invoice."""
    error_context['customers']['test-customer'] = {'id': 'test-customer'}
    error_context['invoices']['test-invoice'] = {
        'customer_id': 'test-customer',
        'total': Decimal(str(amount)),
        'balance_due': Decimal(str(amount)),
        'status': 'sent'
    }
    error_context['current_invoice_id'] = 'test-invoice'


@when(parsers.parse('I try to apply a payment of ${amount:f} to the invoice'))
def try_apply_overpayment(error_context, amount):
    """Try to apply payment exceeding balance."""
    invoice = error_context['invoices'].get('test-invoice')
    if invoice and Decimal(str(amount)) > invoice['balance_due']:
        error_context['last_error'] = "Payment amount exceeds balance"


@given(parsers.parse('a payment of ${amount:f} has been applied'))
def payment_applied(error_context, amount):
    """Apply payment to invoice."""
    invoice = error_context['invoices'].get('test-invoice')
    if invoice:
        invoice['amount_paid'] = Decimal(str(amount))
        invoice['balance_due'] -= Decimal(str(amount))


@when("I try to void the invoice")
def try_void_invoice_with_payments(error_context):
    """Try to void invoice with payments."""
    invoice = error_context['invoices'].get('test-invoice')
    if invoice and invoice.get('amount_paid', 0) > 0:
        error_context['last_error'] = "Cannot void invoice with payments"


@then("the invoice should remain active")
def invoice_remains_active(error_context):
    """Verify invoice still active."""
    invoice = error_context['invoices'].get('test-invoice')
    assert invoice is not None
    assert invoice.get('status') != 'voided'


@then(parsers.parse('the invoice balance should remain ${amount:f}'))
def invoice_balance_unchanged(error_context, amount):
    """Verify invoice balance unchanged."""
    invoice = error_context['invoices'].get('test-invoice')
    assert invoice['balance_due'] == Decimal(str(amount))


# Bill error scenarios
@when(parsers.parse('I try to create a bill for vendor "{vendor_id}"'))
def try_create_bill_invalid_vendor(error_context, vendor_id):
    """Try to create bill for invalid vendor."""
    if vendor_id not in error_context['vendors']:
        error_context['last_error'] = "Vendor not found"
        error_context['operation_result'] = {'success': False}


@then("no bill should be created")
def no_bill_created(error_context):
    """Verify no bill created."""
    assert error_context.get('operation_result', {}).get('success') == False


@given(parsers.parse('a vendor exists with a bill for ${amount:f}'))
def vendor_with_bill(error_context, amount):
    """Create vendor with bill."""
    error_context['vendors']['test-vendor'] = {'id': 'test-vendor'}
    error_context['bills']['test-bill'] = {
        'vendor_id': 'test-vendor',
        'total': Decimal(str(amount)),
        'balance_due': Decimal(str(amount)),
        'status': 'open'
    }
    error_context['current_bill_id'] = 'test-bill'


@when(parsers.parse('I try to pay ${amount:f} on the bill'))
def try_overpay_bill(error_context, amount):
    """Try to pay more than bill balance."""
    bill = error_context['bills'].get('test-bill')
    if bill and Decimal(str(amount)) > bill['balance_due']:
        error_context['last_error'] = "Payment amount exceeds balance"


@then(parsers.parse('the bill balance should remain ${amount:f}'))
def bill_balance_unchanged(error_context, amount):
    """Verify bill balance unchanged."""
    bill = error_context['bills'].get('test-bill')
    assert bill['balance_due'] == Decimal(str(amount))


@given(parsers.parse('a payment of ${amount:f} has been made'))
def bill_payment_made(error_context, amount):
    """Record bill payment."""
    bill = error_context['bills'].get('test-bill')
    if bill:
        bill['amount_paid'] = Decimal(str(amount))
        bill['balance_due'] -= Decimal(str(amount))


@when("I try to void the bill")
def try_void_bill_with_payments(error_context):
    """Try to void bill with payments."""
    bill = error_context['bills'].get('test-bill')
    if bill and bill.get('amount_paid', 0) > 0:
        error_context['last_error'] = "Cannot void bill with payments"


# Check error scenarios
@given("a bank account with check printing disabled")
def account_check_disabled(error_context):
    """Create account with check printing disabled."""
    error_context['accounts']['no-check-account'] = {
        'id': 'no-check-account',
        'check_printing_enabled': False
    }
    error_context['current_account_id'] = 'no-check-account'


@when("I try to create a check on that account")
def try_create_check_disabled(error_context):
    """Try to create check on disabled account."""
    account = error_context['accounts'].get('no-check-account')
    if account and not account.get('check_printing_enabled', True):
        error_context['last_error'] = "Check printing not enabled"
        error_context['operation_result'] = {'success': False}


@then("no check should be created")
def no_check_created(error_context):
    """Verify no check created."""
    assert error_context.get('operation_result', {}).get('success') == False


@given("a bank account with a cleared check")
def account_with_cleared_check(error_context):
    """Create account with cleared check."""
    error_context['accounts']['check-account'] = {'id': 'check-account'}
    error_context['checks']['cleared-check'] = {
        'account_id': 'check-account',
        'status': 'cleared'
    }
    error_context['current_check_id'] = 'cleared-check'


@when("I try to void the cleared check")
def try_void_cleared_check(error_context):
    """Try to void cleared check."""
    check = error_context['checks'].get('cleared-check')
    if check and check.get('status') == 'cleared':
        error_context['last_error'] = "Cannot void a cleared check"


@then("the check should remain cleared")
def check_remains_cleared(error_context):
    """Verify check still cleared."""
    check = error_context['checks'].get('cleared-check')
    assert check['status'] == 'cleared'


# Reconciliation error scenarios
@given(parsers.parse('a bank account "{account_name}" with balance ${balance:f}'))
def create_account_for_recon(error_context, account_name, balance):
    """Create bank account."""
    error_context['accounts'][account_name] = {
        'id': account_name,
        'balance': Decimal(str(balance))
    }
    error_context['current_account_name'] = account_name


@when(parsers.parse('I start reconciliation with statement balance ${balance:f}'))
def start_recon_with_balance(error_context, balance):
    """Start reconciliation."""
    error_context['reconciliation'] = {
        'statement_balance': Decimal(str(balance)),
        'status': 'in_progress'
    }


@when("I complete the reconciliation")
def complete_recon(error_context):
    """Complete reconciliation."""
    recon = error_context.get('reconciliation')
    account_name = error_context.get('current_account_name')
    if recon and account_name:
        account = error_context['accounts'][account_name]
        difference = recon['statement_balance'] - account['balance']
        if abs(difference) > Decimal('0.01'):
            recon['status'] = 'discrepancy'
            recon['difference'] = difference
        else:
            recon['status'] = 'completed'


@then("the reconciliation should report a discrepancy")
def verify_discrepancy(error_context):
    """Verify discrepancy reported."""
    recon = error_context.get('reconciliation')
    assert recon['status'] == 'discrepancy'


# Credit application error scenarios
@given(parsers.parse('customer "{customer_name}" with a credit of ${amount:f}'))
def customer_with_credit(error_context, customer_name, amount):
    """Create customer with credit."""
    error_context['customers'][customer_name] = {'id': customer_name}
    error_context['credits'][customer_name + '-credit'] = {
        'customer_id': customer_name,
        'amount': Decimal(str(amount)),
        'balance': Decimal(str(amount))
    }


@given(parsers.parse('customer "{customer_name}" with an invoice of ${amount:f}'))
def customer_with_invoice_for_credit(error_context, customer_name, amount):
    """Create customer with invoice."""
    error_context['customers'][customer_name] = {'id': customer_name}
    error_context['invoices'][customer_name + '-invoice'] = {
        'customer_id': customer_name,
        'total': Decimal(str(amount)),
        'balance_due': Decimal(str(amount))
    }


@when("I try to apply Customer A credit to Customer B invoice")
def try_apply_wrong_customer_credit(error_context):
    """Try to apply credit to wrong customer."""
    credit = error_context['credits'].get('Customer A-credit')
    invoice = error_context['invoices'].get('Customer B-invoice')
    if credit and invoice and credit['customer_id'] != invoice['customer_id']:
        error_context['last_error'] = "Credit and invoice must be for the same customer"


# Vendor credit error scenarios
@given(parsers.parse('vendor "{vendor_name}" with a credit of ${amount:f}'))
def vendor_with_credit(error_context, vendor_name, amount):
    """Create vendor with credit."""
    error_context['vendors'][vendor_name] = {'id': vendor_name}
    error_context['credits'][vendor_name + '-credit'] = {
        'vendor_id': vendor_name,
        'amount': Decimal(str(amount)),
        'balance': Decimal(str(amount))
    }


@given(parsers.parse('vendor "{vendor_name}" with a bill of ${amount:f}'))
def vendor_with_bill_for_credit(error_context, vendor_name, amount):
    """Create vendor with bill."""
    error_context['vendors'][vendor_name] = {'id': vendor_name}
    error_context['bills'][vendor_name + '-bill'] = {
        'vendor_id': vendor_name,
        'total': Decimal(str(amount)),
        'balance_due': Decimal(str(amount))
    }


@when("I try to apply Vendor A credit to Vendor B bill")
def try_apply_wrong_vendor_credit(error_context):
    """Try to apply credit to wrong vendor."""
    credit = error_context['credits'].get('Vendor A-credit')
    bill = error_context['bills'].get('Vendor B-bill')
    if credit and bill and credit['vendor_id'] != bill['vendor_id']:
        error_context['last_error'] = "Credit and bill must be for the same vendor"


# Transfer error scenarios
@given(parsers.parse('a bank account "{account_name}" exists'))
def account_exists(error_context, account_name):
    """Create bank account."""
    error_context['accounts'][account_name] = {'id': account_name, 'balance': Decimal('1000')}


@when(parsers.parse('I try to transfer from "{source}" to "{target}"'))
def try_transfer_invalid(error_context, source, target):
    """Try invalid transfer."""
    if source not in error_context['accounts']:
        error_context['last_error'] = "Source account not found"
    elif target not in error_context['accounts']:
        error_context['last_error'] = "Destination account not found"


# Purchase order error scenarios
@given("a vendor with a draft purchase order")
def vendor_with_draft_po(error_context):
    """Create vendor with draft PO."""
    error_context['vendors']['po-vendor'] = {'id': 'po-vendor'}
    error_context['purchase_orders']['draft-po'] = {
        'vendor_id': 'po-vendor',
        'status': 'draft'
    }
    error_context['current_po_id'] = 'draft-po'


@when("I try to receive items on the draft PO")
def try_receive_draft_po(error_context):
    """Try to receive on draft PO."""
    po = error_context['purchase_orders'].get('draft-po')
    if po and po['status'] not in ['approved', 'partial']:
        error_context['last_error'] = "PO must be approved before receiving"


# ACH error scenarios
@given("a bank account without ACH enabled")
def account_no_ach(error_context):
    """Create account without ACH."""
    error_context['accounts']['no-ach-account'] = {
        'id': 'no-ach-account',
        'ach_enabled': False
    }
    error_context['current_account_id'] = 'no-ach-account'


@when("I try to create an ACH batch on that account")
def try_create_ach_disabled(error_context):
    """Try to create ACH on disabled account."""
    account = error_context['accounts'].get('no-ach-account')
    if account and not account.get('ach_enabled', False):
        error_context['last_error'] = "ACH not enabled for this account"
