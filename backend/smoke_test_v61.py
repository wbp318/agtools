"""
GenFin v6.1 Smoke Test Suite
Tests all new Inventory, Classes/Projects, and Advanced Reports endpoints
"""
import os
import requests
import json
from datetime import datetime, date

BASE = os.environ.get('AGTOOLS_API_URL', 'http://127.0.0.1:8000/api/v1')
TEST_USER = os.environ.get('AGTOOLS_TEST_USER', 'admin')
TEST_PASS = os.environ.get('AGTOOLS_TEST_PASSWORD')  # No default - must be set

if not TEST_PASS:
    print("ERROR: Set AGTOOLS_TEST_PASSWORD environment variable")
    exit(1)

# Login
resp = requests.post(f'{BASE}/auth/login', json={'username': TEST_USER, 'password': TEST_PASS}, timeout=10)
token = resp.json()['tokens']['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

results = []
passed = 0
failed = 0

def test(name, method, endpoint, params=None, json_data=None, expect_status=None):
    global passed, failed
    try:
        url = f'{BASE}{endpoint}'
        if method == 'GET':
            r = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            r = requests.post(url, headers=headers, params=params, json=json_data)
        elif method == 'PUT':
            r = requests.put(url, headers=headers, params=params, json=json_data)
        elif method == 'DELETE':
            r = requests.delete(url, headers=headers)

        if expect_status:
            ok = r.status_code == expect_status
        else:
            ok = r.status_code in [200, 201]

        if ok:
            passed += 1
            status = 'PASS'
        else:
            failed += 1
            status = f'FAIL ({r.status_code})'
            try:
                detail = str(r.json().get('detail', ''))[:50]
                if detail:
                    status += f' - {detail}'
            except (ValueError, KeyError, TypeError) as e:
                # Response might not be JSON
                pass

        results.append(f'{status}: {method} {endpoint}')
        return r.json() if r.status_code in [200, 201] else None
    except Exception as e:
        failed += 1
        results.append(f'ERROR: {method} {endpoint} - {str(e)[:50]}')
        return None

print('='*70)
print('GENFIN v6.1 SMOKE TEST RESULTS')
print('='*70)
print(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# 1. INVENTORY & ITEMS
print('1. INVENTORY & ITEMS')
print('-'*50)

test('List Items', 'GET', '/genfin/items')

# Create service item with query params
service = test('Create Service Item', 'POST', '/genfin/items/service',
    params={'name': 'Custom Spraying', 'description': 'Per-acre application', 'sales_price': 15.50})

# Create inventory item
inventory = test('Create Inventory Item', 'POST', '/genfin/items/inventory',
    params={'name': 'Roundup PowerMax', 'description': 'Glyphosate herbicide',
            'sales_price': 45.00, 'cost': 32.00, 'reorder_point': 10})

# Create group item
group = test('Create Group Item', 'POST', '/genfin/items/group',
    params={'name': 'Spring Planting Kit', 'description': 'Complete planting package'})

# Price levels
test('Create Price Level', 'POST', '/genfin/price-levels',
    params={'name': 'Wholesale', 'adjustment_percent': -15.0, 'description': '15% off retail'})

test('Inventory Valuation Report', 'GET', '/genfin/reports/inventory-valuation')
test('Inventory Summary', 'GET', '/genfin/inventory/summary')
test('Inventory Lots', 'GET', '/genfin/inventory/lots')

for r in results[-8:]:
    print(f'  {r}')
print()

# 2. CLASSES & PROJECTS
print('2. CLASSES & PROJECTS')
print('-'*50)
results_start = len(results)

test('List Classes', 'GET', '/genfin/classes')
test('Classes Summary', 'GET', '/genfin/classes/summary')
test('Classes Hierarchy', 'GET', '/genfin/classes/hierarchy')

# Create class
new_class = test('Create Class', 'POST', '/genfin/classes',
    params={'name': 'North Farm', 'class_type': 'location', 'description': 'North 40 acres'})

# Projects
test('List Projects', 'GET', '/genfin/projects')
project = test('Create Project', 'POST', '/genfin/projects',
    params={'name': '2025 Custom Planting', 'billing_method': 'time_and_materials',
            'estimated_revenue': 45000.00, 'estimated_cost': 28000.00})

# Get project ID for billable items
project_id = project.get('id') if project else None

if project_id:
    test('Add Billable Expense', 'POST', f'/genfin/projects/{project_id}/billable-expense',
        params={'expense_date': '2025-04-15', 'description': 'Diesel for planting',
                'amount': 850.00, 'markup_percent': 15.0})

    test('Add Billable Time', 'POST', f'/genfin/projects/{project_id}/billable-time',
        params={'entry_date': '2025-04-15', 'hours': 8.0, 'hourly_rate': 45.00,
                'description': 'Planting operations'})

    test('Get Billable Expenses', 'GET', f'/genfin/projects/{project_id}/billable-expenses')
    test('Get Project Detail', 'GET', f'/genfin/projects/{project_id}')

for r in results[results_start:]:
    print(f'  {r}')
print()

# 3. ADVANCED REPORTS & DASHBOARD
print('3. ADVANCED REPORTS & DASHBOARD')
print('-'*50)
results_start = len(results)

test('Report Catalog', 'GET', '/genfin/reports/catalog')
test('Dashboard', 'GET', '/genfin/dashboard')
test('Dashboard Widgets', 'GET', '/genfin/dashboard/widgets')
test('Memorized Reports', 'GET', '/genfin/memorized-reports')
test('Advanced Reports Summary', 'GET', '/genfin/advanced-reports/summary')

# Create memorized report
test('Create Memorized Report', 'POST', '/genfin/memorized-reports',
    params={'name': 'Monthly Report', 'report_type': 'profit_loss', 'category': 'financial'})

# Reports with date params
today = date.today()
start = f'{today.year}-01-01'
end = today.isoformat()

test('Profit Loss Report', 'GET', '/genfin/reports/profit-loss',
    params={'start_date': start, 'end_date': end})

test('Balance Sheet', 'GET', '/genfin/reports/balance-sheet',
    params={'as_of_date': end})

test('Cash Flow', 'GET', '/genfin/reports/cash-flow',
    params={'start_date': start, 'end_date': end})

test('Financial Ratios', 'GET', '/genfin/reports/financial-ratios')

for r in results[results_start:]:
    print(f'  {r}')
print()

# 4. EXISTING GENFIN v6.0 SANITY CHECK
print('4. GENFIN v6.0 SANITY CHECK (Core Features)')
print('-'*50)
results_start = len(results)

test('Chart of Accounts', 'GET', '/genfin/accounts')
test('Trial Balance', 'GET', '/genfin/trial-balance')
test('Vendors', 'GET', '/genfin/vendors')
test('Customers', 'GET', '/genfin/customers')
test('Bank Accounts', 'GET', '/genfin/bank-accounts')
test('Employees', 'GET', '/genfin/employees')
test('Budgets', 'GET', '/genfin/budgets')
test('AP Aging', 'GET', '/genfin/ap-aging')
test('AR Aging', 'GET', '/genfin/ar-aging')

for r in results[results_start:]:
    print(f'  {r}')
print()

# Summary
print('='*70)
print('SUMMARY')
print('='*70)
total = passed + failed
print(f'Total Tests: {total}')
print(f'Passed: {passed} ({passed/total*100:.0f}%)')
print(f'Failed: {failed} ({failed/total*100:.0f}%)')
print()
if failed == 0:
    print('STATUS: ALL TESTS PASSED!')
elif passed/total >= 0.8:
    print('STATUS: MOSTLY PASSING - Minor issues to fix')
elif passed/total >= 0.5:
    print('STATUS: MIXED RESULTS - Several issues to address')
else:
    print('STATUS: NEEDS ATTENTION - Many endpoints need fixes')
print('='*70)

# List failed tests
if failed > 0:
    print()
    print('FAILED TESTS:')
    for r in results:
        if 'FAIL' in r or 'ERROR' in r:
            print(f'  {r}')
