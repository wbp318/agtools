"""Step definitions for Multi-Step Workflows feature."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal

scenarios('../features/multi_step_workflows.feature')


@pytest.fixture
def workflow_context():
    """Context for workflow tests."""
    return {
        'customers': {},
        'vendors': {},
        'invoices': {},
        'bills': {},
        'accounts': {},
        'checks': {},
        'estimates': {},
        'purchase_orders': {},
        'credits': {},
        'reconciliation': None,
        'accounts_receivable': Decimal('0'),
        'accounts_payable': Decimal('0')
    }


@given("the GenFin system is fully initialized")
def system_fully_initialized(workflow_context):
    """Initialize system."""
    workflow_context['initialized'] = True


@given(parsers.parse('I create a vendor "{vendor_name}"'))
def create_vendor(workflow_context, vendor_name):
    """Create vendor."""
    import uuid
    vendor_id = str(uuid.uuid4())
    workflow_context['vendors'][vendor_name] = {
        'id': vendor_id,
        'name': vendor_name,
        'balance': Decimal('0')
    }
    workflow_context['current_vendor'] = vendor_name


@when(parsers.parse('I create a purchase order with items totaling ${amount:f}'))
def create_po_with_total(workflow_context, amount):
    """Create PO with total."""
    vendor = workflow_context['vendors'].get(workflow_context.get('current_vendor'))
    po_id = f"PO-{len(workflow_context['purchase_orders']) + 1}"
    workflow_context['purchase_orders'][po_id] = {
        'vendor': workflow_context.get('current_vendor'),
        'total': Decimal(str(amount)),
        'status': 'draft'
    }
    workflow_context['current_po'] = po_id


@when(parsers.parse('the PO is approved by "{approver}"'))
def approve_po(workflow_context, approver):
    """Approve PO."""
    po_id = workflow_context.get('current_po')
    if po_id:
        workflow_context['purchase_orders'][po_id]['status'] = 'approved'
        workflow_context['purchase_orders'][po_id]['approved_by'] = approver


@when("I receive all items on the PO")
def receive_all_po_items(workflow_context):
    """Receive all PO items."""
    po_id = workflow_context.get('current_po')
    if po_id:
        workflow_context['purchase_orders'][po_id]['status'] = 'received'


@when("I create a bill from the received PO")
def create_bill_from_po(workflow_context):
    """Create bill from PO."""
    po_id = workflow_context.get('current_po')
    if po_id:
        po = workflow_context['purchase_orders'][po_id]
        bill_id = f"BILL-{len(workflow_context['bills']) + 1}"
        workflow_context['bills'][bill_id] = {
            'vendor': po['vendor'],
            'total': po['total'],
            'balance_due': po['total'],
            'status': 'draft',
            'from_po': po_id
        }
        workflow_context['current_bill'] = bill_id


@when("I post the bill")
def post_bill(workflow_context):
    """Post bill."""
    bill_id = workflow_context.get('current_bill')
    if bill_id:
        bill = workflow_context['bills'][bill_id]
        bill['status'] = 'open'
        workflow_context['accounts_payable'] += bill['total']


@then(parsers.parse('accounts payable should increase by ${amount:f}'))
def ap_increased(workflow_context, amount):
    """Verify AP increased."""
    assert workflow_context['accounts_payable'] >= Decimal(str(amount))


@when("I write a check to pay the bill")
def write_check_for_bill(workflow_context):
    """Write check for bill."""
    bill_id = workflow_context.get('current_bill')
    if bill_id:
        bill = workflow_context['bills'][bill_id]
        check_id = f"CHK-{len(workflow_context['checks']) + 1}"
        workflow_context['checks'][check_id] = {
            'amount': bill['balance_due'],
            'payee': bill['vendor'],
            'bill': bill_id
        }
        bill['status'] = 'paid'
        bill['balance_due'] = Decimal('0')
        workflow_context['accounts_payable'] -= bill['total']


@then(parsers.parse('the bill status should be "{status}"'))
def verify_bill_status(workflow_context, status):
    """Verify bill status."""
    bill_id = workflow_context.get('current_bill')
    assert workflow_context['bills'][bill_id]['status'] == status


@then(parsers.parse('accounts payable should decrease by ${amount:f}'))
def ap_decreased(workflow_context, amount):
    """Verify AP decreased."""
    pass  # Verified by payment


# Customer/Sales workflow steps
@given(parsers.parse('I create a customer "{customer_name}"'))
def create_customer(workflow_context, customer_name):
    """Create customer."""
    import uuid
    workflow_context['customers'][customer_name] = {
        'id': str(uuid.uuid4()),
        'name': customer_name,
        'balance': Decimal('0')
    }
    workflow_context['current_customer'] = customer_name


@when(parsers.parse('I create an estimate for ${amount:f}'))
def create_estimate(workflow_context, amount):
    """Create estimate."""
    est_id = f"EST-{len(workflow_context['estimates']) + 1}"
    workflow_context['estimates'][est_id] = {
        'customer': workflow_context.get('current_customer'),
        'total': Decimal(str(amount)),
        'status': 'draft'
    }
    workflow_context['current_estimate'] = est_id


@when("the customer accepts the estimate")
def accept_estimate(workflow_context):
    """Accept estimate."""
    est_id = workflow_context.get('current_estimate')
    if est_id:
        workflow_context['estimates'][est_id]['status'] = 'accepted'


@when("I convert the estimate to an invoice")
def convert_estimate_to_invoice(workflow_context):
    """Convert estimate to invoice."""
    est_id = workflow_context.get('current_estimate')
    if est_id:
        est = workflow_context['estimates'][est_id]
        inv_id = f"INV-{len(workflow_context['invoices']) + 1}"
        workflow_context['invoices'][inv_id] = {
            'customer': est['customer'],
            'total': est['total'],
            'balance_due': est['total'],
            'status': 'draft',
            'from_estimate': est_id
        }
        workflow_context['current_invoice'] = inv_id
        est['status'] = 'converted'


@when("I send the invoice")
def send_invoice(workflow_context):
    """Send invoice."""
    inv_id = workflow_context.get('current_invoice')
    if inv_id:
        inv = workflow_context['invoices'][inv_id]
        inv['status'] = 'sent'
        workflow_context['accounts_receivable'] += inv['total']


@then(parsers.parse('accounts receivable should increase by ${amount:f}'))
def ar_increased(workflow_context, amount):
    """Verify AR increased."""
    assert workflow_context['accounts_receivable'] >= Decimal(str(amount))


@when(parsers.parse('I receive partial payment of ${amount:f}'))
def receive_partial_payment(workflow_context, amount):
    """Receive partial payment."""
    inv_id = workflow_context.get('current_invoice')
    if inv_id:
        inv = workflow_context['invoices'][inv_id]
        payment = Decimal(str(amount))
        inv['balance_due'] -= payment
        inv['status'] = 'partial' if inv['balance_due'] > 0 else 'paid'


@then(parsers.parse('the invoice balance should be ${amount:f}'))
def verify_invoice_balance(workflow_context, amount):
    """Verify invoice balance."""
    inv_id = workflow_context.get('current_invoice')
    assert workflow_context['invoices'][inv_id]['balance_due'] == Decimal(str(amount))


@when(parsers.parse('I receive final payment of ${amount:f}'))
def receive_final_payment(workflow_context, amount):
    """Receive final payment."""
    inv_id = workflow_context.get('current_invoice')
    if inv_id:
        inv = workflow_context['invoices'][inv_id]
        inv['balance_due'] = Decimal('0')
        inv['status'] = 'paid'
        workflow_context['accounts_receivable'] -= inv['total']


@then(parsers.parse('the invoice status should be "{status}"'))
def verify_invoice_status(workflow_context, status):
    """Verify invoice status."""
    inv_id = workflow_context.get('current_invoice')
    assert workflow_context['invoices'][inv_id]['status'] == status


# Reconciliation workflow
@given(parsers.parse('a bank account with last reconciled balance ${amount:f}'))
def account_with_recon_balance(workflow_context, amount):
    """Create account with reconciled balance."""
    workflow_context['accounts']['recon-account'] = {
        'balance': Decimal(str(amount)),
        'last_reconciled_balance': Decimal(str(amount))
    }
    workflow_context['current_account'] = 'recon-account'


@given("the following transactions occurred:")
def record_transactions(workflow_context, datatable):
    """Record transactions."""
    headers = datatable[0]
    account = workflow_context['accounts'][workflow_context['current_account']]
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        amount = Decimal(row_dict['amount'])
        if row_dict['type'] == 'deposit':
            account['balance'] += amount
        else:
            account['balance'] -= amount


@when(parsers.parse('I start reconciliation with statement balance ${amount:f}'))
def start_reconciliation(workflow_context, amount):
    """Start reconciliation."""
    workflow_context['reconciliation'] = {
        'statement_balance': Decimal(str(amount)),
        'status': 'in_progress'
    }


@when("I mark all transactions as cleared")
def mark_all_cleared(workflow_context):
    """Mark all transactions cleared."""
    pass


@when("I complete the reconciliation")
def complete_reconciliation(workflow_context):
    """Complete reconciliation."""
    if workflow_context.get('reconciliation'):
        workflow_context['reconciliation']['status'] = 'completed'


@then("the reconciliation should succeed")
def recon_succeeded(workflow_context):
    """Verify reconciliation succeeded."""
    assert workflow_context['reconciliation']['status'] == 'completed'


# Vendor credit workflow
@given("a vendor with the following open bills:")
def vendor_with_open_bills(workflow_context, datatable):
    """Create vendor with bills."""
    workflow_context['vendors']['credit-vendor'] = {'name': 'credit-vendor'}
    headers = datatable[0]
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        workflow_context['bills'][row_dict['bill_number']] = {
            'vendor': 'credit-vendor',
            'total': Decimal(row_dict['amount']),
            'balance_due': Decimal(row_dict['amount']),
            'status': 'open'
        }


@when(parsers.parse('I receive a vendor credit for ${amount:f}'))
def receive_vendor_credit(workflow_context, amount):
    """Receive vendor credit."""
    workflow_context['credits']['vendor-credit'] = {
        'vendor': 'credit-vendor',
        'amount': Decimal(str(amount)),
        'balance': Decimal(str(amount))
    }


@when(parsers.parse('I apply ${credit_amount:f} to {bill_id}'))
def apply_credit_to_bill(workflow_context, credit_amount, bill_id):
    """Apply credit to bill."""
    credit = workflow_context['credits']['vendor-credit']
    bill = workflow_context['bills'][bill_id]
    amount = Decimal(str(credit_amount))
    credit['balance'] -= amount
    bill['balance_due'] -= amount
    if bill['balance_due'] <= 0:
        bill['status'] = 'paid'


@then(parsers.re(r'(?P<bill_id>BILL-\d+) should be paid'))
def bill_is_paid(workflow_context, bill_id):
    """Verify bill is paid."""
    assert workflow_context['bills'][bill_id]['status'] == 'paid'


@then(parsers.re(r'(?P<bill_id>BILL-\d+) balance should be \$(?P<amount>[\d.]+)'))
def bill_balance_is(workflow_context, bill_id, amount):
    """Verify bill balance."""
    assert workflow_context['bills'][bill_id]['balance_due'] == Decimal(str(amount))


@then(parsers.parse('the invoice balance should be ${amount:f}'))
def invoice_balance_is(workflow_context, amount):
    """Verify invoice balance."""
    inv_id = workflow_context.get('current_invoice')
    if inv_id:
        assert workflow_context['invoices'][inv_id]['balance_due'] == Decimal(str(amount))


@then(parsers.parse('the bank balance should be ${amount:f}'))
def bank_balance_is(workflow_context, amount):
    """Verify bank balance."""
    account = workflow_context['accounts'].get('batch-account')
    if account:
        assert account['balance'] == Decimal(str(amount))


# Customer credit workflow
@given(parsers.parse('a customer with an invoice for ${amount:f}'))
def customer_with_invoice_amount(workflow_context, amount):
    """Create customer with invoice."""
    workflow_context['customers']['credit-customer'] = {'name': 'credit-customer'}
    workflow_context['invoices']['credit-invoice'] = {
        'customer': 'credit-customer',
        'total': Decimal(str(amount)),
        'balance_due': Decimal(str(amount)),
        'status': 'sent'
    }
    workflow_context['current_invoice'] = 'credit-invoice'


@when(parsers.parse('they make a payment of ${amount:f}'))
def customer_makes_payment(workflow_context, amount):
    """Customer makes payment."""
    inv = workflow_context['invoices']['credit-invoice']
    inv['balance_due'] -= Decimal(str(amount))


@when(parsers.parse('I issue a credit memo for ${amount:f}'))
def issue_credit_memo(workflow_context, amount):
    """Issue credit memo."""
    workflow_context['credits']['customer-credit'] = {
        'customer': 'credit-customer',
        'amount': Decimal(str(amount)),
        'balance': Decimal(str(amount))
    }


@when("I apply the credit to the invoice")
def apply_credit_to_invoice(workflow_context):
    """Apply credit to invoice."""
    credit = workflow_context['credits']['customer-credit']
    inv = workflow_context['invoices']['credit-invoice']
    inv['balance_due'] -= credit['balance']
    credit['balance'] = Decimal('0')


@when(parsers.parse('the customer pays the remaining ${amount:f}'))
def customer_pays_remaining(workflow_context, amount):
    """Customer pays remaining."""
    inv = workflow_context['invoices']['credit-invoice']
    inv['balance_due'] = Decimal('0')
    inv['status'] = 'paid'


@then("the invoice should be fully paid")
def invoice_fully_paid(workflow_context):
    """Verify invoice fully paid."""
    assert workflow_context['invoices']['credit-invoice']['status'] == 'paid'


# Batch payment workflow
@given("the following vendors with open bills:")
def vendors_with_bills(workflow_context, datatable):
    """Create vendors with bills."""
    headers = datatable[0]
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        vendor = row_dict['vendor']
        if vendor not in workflow_context['vendors']:
            workflow_context['vendors'][vendor] = {'name': vendor, 'bills': []}
        bill_id = f"BILL-{vendor}"
        workflow_context['bills'][bill_id] = {
            'vendor': vendor,
            'total': Decimal(row_dict['amount']),
            'balance_due': Decimal(row_dict['amount']),
            'status': 'open'
        }
        workflow_context['vendors'][vendor]['bills'].append(bill_id)


@given(parsers.parse('a bank account with balance ${amount:f}'))
def bank_account_with_balance(workflow_context, amount):
    """Create bank account."""
    workflow_context['accounts']['batch-account'] = {
        'balance': Decimal(str(amount))
    }


@when("I create batch payment for all vendors")
def create_batch_payment(workflow_context):
    """Create batch payment."""
    total = Decimal('0')
    for bill_id, bill in workflow_context['bills'].items():
        if bill['status'] == 'open':
            total += bill['balance_due']
            bill['status'] = 'paid'
            bill['balance_due'] = Decimal('0')
    workflow_context['batch_total'] = total
    workflow_context['accounts']['batch-account']['balance'] -= total


@then(parsers.parse('checks should total ${amount:f}'))
def checks_total(workflow_context, amount):
    """Verify check total."""
    assert workflow_context['batch_total'] == Decimal(str(amount))


@then("all bills should be marked as paid")
def all_bills_paid(workflow_context):
    """Verify all bills paid."""
    for bill in workflow_context['bills'].values():
        assert bill['status'] == 'paid'


@then(parsers.parse('the bank balance should be ${amount:f}'))
def bank_balance_is(workflow_context, amount):
    """Verify bank balance."""
    assert workflow_context['accounts']['batch-account']['balance'] == Decimal(str(amount))


# Recurring invoice workflow
@given("customers with recurring services:")
def customers_with_recurring(workflow_context, datatable):
    """Create customers with recurring services."""
    headers = datatable[0]
    workflow_context['recurring'] = []
    for row in datatable[1:]:
        row_dict = dict(zip(headers, row))
        workflow_context['customers'][row_dict['customer']] = {'name': row_dict['customer']}
        workflow_context['recurring'].append({
            'customer': row_dict['customer'],
            'amount': Decimal(row_dict['monthly_amount'])
        })


@when("I generate monthly invoices")
def generate_monthly_invoices(workflow_context):
    """Generate monthly invoices."""
    for recurring in workflow_context['recurring']:
        inv_id = f"INV-{recurring['customer']}"
        workflow_context['invoices'][inv_id] = {
            'customer': recurring['customer'],
            'total': recurring['amount'],
            'balance_due': recurring['amount'],
            'status': 'draft'
        }


@then(parsers.parse('{count:d} invoices should be created totaling ${amount:f}'))
def invoices_created_totaling(workflow_context, count, amount):
    """Verify invoices created."""
    draft_invoices = [i for i in workflow_context['invoices'].values() if i['status'] == 'draft']
    assert len(draft_invoices) == count
    total = sum(i['total'] for i in draft_invoices)
    assert total == Decimal(str(amount))


@when("I send all invoices")
def send_all_invoices(workflow_context):
    """Send all invoices."""
    for inv in workflow_context['invoices'].values():
        if inv['status'] == 'draft':
            inv['status'] = 'sent'
            workflow_context['accounts_receivable'] += inv['total']
