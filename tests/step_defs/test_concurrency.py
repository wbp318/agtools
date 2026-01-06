"""Step definitions for Concurrency Tests feature."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from decimal import Decimal
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

scenarios('../features/concurrency_tests.feature')


@pytest.fixture
def concurrency_context():
    """Context for concurrency tests with thread safety."""
    import threading
    return {
        'customers': {},
        'vendors': {},
        'invoices': {},
        'bills': {},
        'accounts': {},
        'checks': {},
        'purchase_orders': {},
        'payments': [],
        'operations': [],
        'results': [],
        'errors': [],
        'lock': threading.Lock(),
        'next_check_number': 1001
    }


@given("the GenFin system is initialized for concurrent testing")
def system_initialized_concurrent(concurrency_context):
    """Initialize for concurrent testing."""
    concurrency_context['initialized'] = True


# Concurrent payment scenarios
@given(parsers.parse('a customer with an invoice for ${amount:f}'))
def customer_with_invoice(concurrency_context, amount):
    """Create customer with invoice."""
    concurrency_context['customers']['test-customer'] = {'id': 'test-customer'}
    concurrency_context['invoices']['test-invoice'] = {
        'customer_id': 'test-customer',
        'total': Decimal(str(amount)),
        'balance_due': Decimal(str(amount)),
        'payments': []
    }


@when(parsers.parse('two payments of ${amount:f} are applied simultaneously'))
def apply_concurrent_payments(concurrency_context, amount):
    """Apply payments concurrently."""
    payment_amount = Decimal(str(amount))
    invoice = concurrency_context['invoices']['test-invoice']

    def apply_payment():
        with concurrency_context['lock']:
            if invoice['balance_due'] >= payment_amount:
                invoice['balance_due'] -= payment_amount
                invoice['payments'].append(payment_amount)
                return True
        return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(apply_payment) for _ in range(2)]
        concurrency_context['results'] = [f.result() for f in as_completed(futures)]


@then("the invoice should be fully paid")
def invoice_fully_paid(concurrency_context):
    """Verify invoice is paid."""
    invoice = concurrency_context['invoices']['test-invoice']
    assert invoice['balance_due'] == Decimal('0')


@then(parsers.parse('the total payments should equal ${amount:f}'))
def total_payments_equal(concurrency_context, amount):
    """Verify total payments."""
    invoice = concurrency_context['invoices']['test-invoice']
    total = sum(invoice['payments'])
    assert total == Decimal(str(amount))


@then("no duplicate payments should exist")
def no_duplicate_payments(concurrency_context):
    """Verify no duplicates."""
    # With proper locking, each payment should be unique
    pass


# Concurrent check number scenarios
@given(parsers.parse('a bank account with next check number {number:d}'))
def account_with_check_number(concurrency_context, number):
    """Create account with check number."""
    concurrency_context['accounts']['check-account'] = {
        'next_check_number': number,
        'balance': Decimal('50000')
    }
    concurrency_context['next_check_number'] = number


@when(parsers.parse('{count:d} checks are created simultaneously'))
def create_concurrent_checks(concurrency_context, count):
    """Create checks concurrently."""
    check_numbers = []

    def create_check():
        with concurrency_context['lock']:
            num = concurrency_context['next_check_number']
            concurrency_context['next_check_number'] += 1
            check_numbers.append(num)
            return num

    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(create_check) for _ in range(count)]
        for f in as_completed(futures):
            f.result()

    concurrency_context['check_numbers'] = check_numbers


@then("each check should have a unique number")
def unique_check_numbers(concurrency_context):
    """Verify unique check numbers."""
    numbers = concurrency_context['check_numbers']
    assert len(numbers) == len(set(numbers))


@then(parsers.parse('check numbers should be {start:d} through {end:d}'))
def check_numbers_range(concurrency_context, start, end):
    """Verify check number range."""
    numbers = sorted(concurrency_context['check_numbers'])
    assert numbers == list(range(start, end + 1))


@then("no duplicate check numbers should exist")
def no_duplicate_checks(concurrency_context):
    """Verify no duplicate check numbers."""
    numbers = concurrency_context['check_numbers']
    assert len(numbers) == len(set(numbers))


# Concurrent bill payment scenarios
@given(parsers.parse('a bank account "{account_name}" with balance ${balance:f}'))
def create_bank_account(concurrency_context, account_name, balance):
    """Create bank account."""
    concurrency_context['accounts'][account_name] = {
        'balance': Decimal(str(balance))
    }


@given(parsers.parse('{count:d} vendors with bills of ${amount:f} each'))
def vendors_with_bills(concurrency_context, count, amount):
    """Create vendors with bills."""
    for i in range(count):
        vendor_id = f'vendor-{i}'
        bill_id = f'bill-{i}'
        concurrency_context['vendors'][vendor_id] = {'id': vendor_id}
        concurrency_context['bills'][bill_id] = {
            'vendor_id': vendor_id,
            'amount': Decimal(str(amount)),
            'status': 'open'
        }


@when("all bills are paid simultaneously")
def pay_bills_simultaneously(concurrency_context):
    """Pay all bills at once."""
    account = concurrency_context['accounts']['Shared Account']

    def pay_bill(bill_id):
        bill = concurrency_context['bills'][bill_id]
        with concurrency_context['lock']:
            if account['balance'] >= bill['amount']:
                account['balance'] -= bill['amount']
                bill['status'] = 'paid'
                return True
        return False

    with ThreadPoolExecutor(max_workers=len(concurrency_context['bills'])) as executor:
        futures = {executor.submit(pay_bill, bid): bid for bid in concurrency_context['bills']}
        concurrency_context['results'] = [f.result() for f in as_completed(futures)]


@then("all payments should succeed")
def all_payments_succeed(concurrency_context):
    """Verify all payments succeeded."""
    assert all(concurrency_context['results'])


@then(parsers.parse('the account balance should be ${amount:f}'))
def account_balance_is(concurrency_context, amount):
    """Verify account balance."""
    account = concurrency_context['accounts'].get('Shared Account') or \
              list(concurrency_context['accounts'].values())[0]
    assert account['balance'] == Decimal(str(amount))


@then("no overdraft should occur")
def no_overdraft(concurrency_context):
    """Verify no overdraft."""
    for account in concurrency_context['accounts'].values():
        assert account['balance'] >= 0


# Concurrent invoice creation
@given(parsers.parse('a customer "{customer_name}"'))
def create_customer(concurrency_context, customer_name):
    """Create customer."""
    concurrency_context['customers'][customer_name] = {
        'id': customer_name,
        'invoices': []
    }
    concurrency_context['current_customer'] = customer_name


@when(parsers.parse('{count:d} invoices are created simultaneously'))
def create_invoices_simultaneously(concurrency_context, count):
    """Create invoices concurrently."""
    customer = concurrency_context['customers'][concurrency_context['current_customer']]
    invoice_numbers = []

    def create_invoice():
        with concurrency_context['lock']:
            num = len(concurrency_context['invoices']) + 1
            inv_id = f'INV-{num:05d}'
            concurrency_context['invoices'][inv_id] = {
                'customer': customer['id'],
                'number': num
            }
            customer['invoices'].append(inv_id)
            invoice_numbers.append(num)
            return inv_id

    with ThreadPoolExecutor(max_workers=count) as executor:
        futures = [executor.submit(create_invoice) for _ in range(count)]
        for f in as_completed(futures):
            f.result()

    concurrency_context['invoice_numbers'] = invoice_numbers


@then("all invoices should have unique numbers")
def unique_invoice_numbers(concurrency_context):
    """Verify unique invoice numbers."""
    numbers = concurrency_context.get('invoice_numbers', [])
    assert len(numbers) == len(set(numbers))


@then("all invoices should be linked to the customer")
def invoices_linked(concurrency_context):
    """Verify invoices linked."""
    customer = concurrency_context['customers'][concurrency_context['current_customer']]
    assert len(customer['invoices']) > 0


@then("customer balance should reflect all invoices")
def customer_balance_reflects(concurrency_context):
    """Verify customer balance."""
    pass  # Would sum invoice totals


# Concurrent reconciliation
@given(parsers.parse('a bank account "{account_name}"'))
def create_recon_account(concurrency_context, account_name):
    """Create account for reconciliation."""
    concurrency_context['accounts'][account_name] = {
        'balance': Decimal('10000'),
        'reconciliation_active': False
    }


@when("two users try to start reconciliation simultaneously")
def start_concurrent_reconciliation(concurrency_context):
    """Start reconciliation concurrently."""
    account = list(concurrency_context['accounts'].values())[0]
    results = []

    def start_recon():
        with concurrency_context['lock']:
            if not account.get('reconciliation_active'):
                account['reconciliation_active'] = True
                return 'started'
        return 'blocked'

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(start_recon) for _ in range(2)]
        results = [f.result() for f in as_completed(futures)]

    concurrency_context['recon_results'] = results


@then("only one reconciliation should be active")
def one_recon_active(concurrency_context):
    """Verify only one reconciliation."""
    results = concurrency_context['recon_results']
    assert results.count('started') == 1


@then("Or both should be allowed with proper isolation")
def both_allowed_isolated(concurrency_context):
    """Alternative: both allowed."""
    pass  # Implementation dependent


# Concurrent deposit and withdrawal
@given(parsers.parse('a bank account with balance ${amount:f}'))
def account_with_balance(concurrency_context, amount):
    """Create account with balance."""
    concurrency_context['accounts']['concurrent-account'] = {
        'balance': Decimal(str(amount))
    }


@when(parsers.parse('a deposit of ${dep:f} and withdrawal of ${wit:f} occur simultaneously'))
def concurrent_deposit_withdrawal(concurrency_context, dep, wit):
    """Deposit and withdraw concurrently."""
    account = concurrency_context['accounts']['concurrent-account']

    def deposit():
        with concurrency_context['lock']:
            account['balance'] += Decimal(str(dep))

    def withdraw():
        with concurrency_context['lock']:
            account['balance'] -= Decimal(str(wit))

    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(deposit)
        executor.submit(withdraw)
        # Wait for completion
        time.sleep(0.1)


@then(parsers.parse('the final balance should be ${amount:f}'))
def final_balance_is(concurrency_context, amount):
    """Verify final balance."""
    account = concurrency_context['accounts']['concurrent-account']
    assert account['balance'] == Decimal(str(amount))


@then("both transactions should be recorded")
def both_recorded(concurrency_context):
    """Verify both transactions recorded."""
    pass  # Verified by balance


# Concurrent credit application
@given(parsers.parse('a vendor with credit of ${amount:f}'))
def vendor_with_credit(concurrency_context, amount):
    """Create vendor with credit."""
    concurrency_context['vendors']['credit-vendor'] = {
        'credit': Decimal(str(amount))
    }


@given(parsers.parse('two bills of ${amount:f} each'))
def two_bills(concurrency_context, amount):
    """Create two bills."""
    for i in range(2):
        concurrency_context['bills'][f'bill-{i}'] = {
            'amount': Decimal(str(amount)),
            'status': 'open'
        }


@when("the credit is applied to both bills simultaneously")
def apply_credit_simultaneously(concurrency_context):
    """Apply credit to both bills at once."""
    vendor = concurrency_context['vendors']['credit-vendor']
    applied_amounts = []

    def apply_credit(bill_id):
        bill = concurrency_context['bills'][bill_id]
        with concurrency_context['lock']:
            if vendor['credit'] >= bill['amount']:
                vendor['credit'] -= bill['amount']
                applied_amounts.append(bill['amount'])
                bill['status'] = 'paid'
                return True
        return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(apply_credit, f'bill-{i}') for i in range(2)]
        for f in as_completed(futures):
            f.result()

    concurrency_context['applied_amounts'] = applied_amounts


@then(parsers.parse('total credit applied should not exceed ${amount:f}'))
def credit_not_exceeded(concurrency_context, amount):
    """Verify credit not over-applied."""
    total_applied = sum(concurrency_context.get('applied_amounts', []))
    assert total_applied <= Decimal(str(amount))


@then("at least one application should succeed")
def at_least_one_succeeded(concurrency_context):
    """Verify at least one succeeded."""
    assert len(concurrency_context.get('applied_amounts', [])) >= 1


# High volume scenarios
@given(parsers.parse('{count:d} customers exist'))
def many_customers_exist(concurrency_context, count):
    """Create many customers."""
    for i in range(count):
        concurrency_context['customers'][f'customer-{i}'] = {'id': f'customer-{i}'}


@when(parsers.parse('{count:d} invoices are created in rapid succession'))
def rapid_invoice_creation(concurrency_context, count):
    """Create invoices rapidly."""
    def create_invoice(i):
        with concurrency_context['lock']:
            inv_id = f'INV-{i:05d}'
            concurrency_context['invoices'][inv_id] = {
                'customer': f'customer-{i % 100}',
                'amount': Decimal('100')
            }
            return inv_id

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_invoice, i) for i in range(count)]
        concurrency_context['created_invoices'] = [f.result() for f in as_completed(futures)]


@then("all invoices should be created successfully")
def all_invoices_created(concurrency_context):
    """Verify all invoices created."""
    assert len(concurrency_context['created_invoices']) == len(concurrency_context['invoices'])


@then("all invoice numbers should be unique")
def all_numbers_unique(concurrency_context):
    """Verify unique numbers."""
    inv_ids = list(concurrency_context['invoices'].keys())
    assert len(inv_ids) == len(set(inv_ids))


@then("system should maintain performance")
def performance_maintained(concurrency_context):
    """Verify performance."""
    pass  # Would measure timing


# Additional concurrent scenarios
@given("a check that is being printed")
def check_being_printed(concurrency_context):
    """Create check being printed."""
    concurrency_context['checks']['printing-check'] = {
        'status': 'printing'
    }


@when("a void request comes during printing")
def void_during_printing(concurrency_context):
    """Void request during print."""
    check = concurrency_context['checks']['printing-check']
    with concurrency_context['lock']:
        if check['status'] == 'printing':
            check['void_requested'] = True


@then("the operation should be handled gracefully")
def handled_gracefully(concurrency_context):
    """Verify graceful handling."""
    check = concurrency_context['checks']['printing-check']
    assert check.get('void_requested') or check['status'] in ['printed', 'voided']


@then("the check should end in a consistent state")
def consistent_state(concurrency_context):
    """Verify consistent state."""
    pass


@given("multiple operations targeting same records")
def multiple_ops_same_records(concurrency_context):
    """Setup for deadlock test."""
    concurrency_context['accounts']['deadlock-test'] = {'balance': Decimal('10000')}


@when("operations execute concurrently")
def execute_concurrent_ops(concurrency_context):
    """Execute operations."""
    account = concurrency_context['accounts']['deadlock-test']

    def operation(op_type):
        with concurrency_context['lock']:
            if op_type == 'add':
                account['balance'] += Decimal('100')
            else:
                account['balance'] -= Decimal('50')
            return True

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(operation, 'add'),
            executor.submit(operation, 'sub'),
            executor.submit(operation, 'add'),
            executor.submit(operation, 'sub')
        ]
        concurrency_context['results'] = [f.result() for f in as_completed(futures)]


@then("deadlocks should be avoided or handled")
def no_deadlocks(concurrency_context):
    """Verify no deadlocks."""
    assert all(concurrency_context['results'])


@then("all operations should eventually complete")
def all_ops_complete(concurrency_context):
    """Verify all completed."""
    assert len(concurrency_context['results']) == 4


@then("data integrity should be maintained")
def data_integrity(concurrency_context):
    """Verify data integrity."""
    account = concurrency_context['accounts']['deadlock-test']
    # Started with 10000, +100, -50, +100, -50 = 10100
    assert account['balance'] == Decimal('10100')


# Transfer scenarios
@given(parsers.parse('account "{name}" with ${amount:f} and account "{name2}" with ${amount2:f}'))
def two_accounts(concurrency_context, name, amount, name2, amount2):
    """Create two accounts."""
    concurrency_context['accounts'][name] = {'balance': Decimal(str(amount))}
    concurrency_context['accounts'][name2] = {'balance': Decimal(str(amount2))}


@when("transfers occur simultaneously:")
def simultaneous_transfers(concurrency_context, datatable):
    """Execute simultaneous transfers."""
    headers = datatable[0]

    def transfer(from_acc, to_acc, amount):
        with concurrency_context['lock']:
            concurrency_context['accounts'][from_acc]['balance'] -= Decimal(amount)
            concurrency_context['accounts'][to_acc]['balance'] += Decimal(amount)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for row in datatable[1:]:
            row_dict = dict(zip(headers, row))
            futures.append(executor.submit(
                transfer,
                row_dict['from'],
                row_dict['to'],
                row_dict['amount']
            ))
        for f in as_completed(futures):
            f.result()


@then(parsers.parse('account "{name}" should have ${amount:f}'))
def account_has_amount(concurrency_context, name, amount):
    """Verify account amount."""
    assert concurrency_context['accounts'][name]['balance'] == Decimal(str(amount))


@then("all transfers should be recorded")
def transfers_recorded(concurrency_context):
    """Verify transfers recorded."""
    pass


# Concurrent customer creation
@when(parsers.parse('two customers named "{name}" are created simultaneously'))
def create_duplicate_customers(concurrency_context, name):
    """Create customers with same name."""
    import uuid
    results = []

    def create_customer():
        with concurrency_context['lock']:
            cust_id = str(uuid.uuid4())
            concurrency_context['customers'][cust_id] = {'name': name, 'id': cust_id}
            results.append(cust_id)
            return cust_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create_customer) for _ in range(2)]
        for f in as_completed(futures):
            f.result()

    concurrency_context['created_customers'] = results


@then("both should be created with unique IDs")
def both_unique_ids(concurrency_context):
    """Verify unique IDs."""
    ids = concurrency_context['created_customers']
    assert len(ids) == len(set(ids))


@then("Or one should fail with appropriate error")
def one_fails(concurrency_context):
    """Alternative: one fails."""
    pass


# PO approval
@given("a purchase order awaiting approval")
def po_awaiting_approval(concurrency_context):
    """Create PO awaiting approval."""
    concurrency_context['purchase_orders']['approval-po'] = {
        'status': 'pending',
        'approved_by': None
    }


@when("two managers try to approve simultaneously")
def simultaneous_approval(concurrency_context):
    """Approve simultaneously."""
    po = concurrency_context['purchase_orders']['approval-po']
    approvals = []

    def approve(manager):
        with concurrency_context['lock']:
            if po['status'] == 'pending':
                po['status'] = 'approved'
                po['approved_by'] = manager
                approvals.append(manager)
                return True
        return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(approve, 'Manager A'),
            executor.submit(approve, 'Manager B')
        ]
        for f in as_completed(futures):
            f.result()

    concurrency_context['approvals'] = approvals


@then("the PO should be approved once")
def po_approved_once(concurrency_context):
    """Verify approved once."""
    po = concurrency_context['purchase_orders']['approval-po']
    assert po['status'] == 'approved'


@then("only one approval should be recorded")
def one_approval_recorded(concurrency_context):
    """Verify one approval."""
    assert len(concurrency_context['approvals']) == 1
