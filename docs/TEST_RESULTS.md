# AgTools Test Results

> **Last Run:** January 3, 2026 | **Version:** 6.7.8

## Summary

| Test Suite | Tests | Passed | Failed | Pass Rate |
|------------|-------|--------|--------|-----------|
| GenFin Workflow | 121 | 118 | 3* | 97.5% |
| Farm Operations | 97 | 97 | 0 | 100% |
| **Total** | **218** | **215** | **3** | **98.6%** |

*3 failures are known internal server errors in payroll service (pay schedule creation, due schedules, tax liability)

---

## GenFin Workflow (121 tests)

### Customer/Vendor/Employee Management (10 tests)
- Create/List/Get/Update customer
- Create/List/Update vendor
- Create/List employees

### Chart of Accounts (3 tests)
- Create account
- List accounts
- Verify multiple account types

### Invoices & Bills (4 tests)
- Create/List invoices
- Create/List bills

### Inventory Management (17 tests)
- Create/List/Get/Update inventory items
- Inventory summary
- Inventory lots
- Create service item
- Create stock item
- List items
- Get item by ID
- Inventory valuation
- Inventory reorder report
- Inventory stock status
- Receive inventory
- Adjust inventory

### Purchase Orders (2 tests)
- Create purchase order
- List purchase orders

### Journal Entries (2 tests)
- Create journal entry
- List journal entries

### Checks (2 tests)
- Create check
- List checks

### Time Entries (2 tests)
- Create time entry
- List time entries

### Fixed Assets (3 tests)
- Create fixed asset
- List fixed assets
- Fixed assets summary

### Bank Accounts (2 tests)
- List bank accounts
- Verify endpoint validity

### Entities (2 tests)
- List entities
- Entities summary

### Deposits (2 tests)
- Create deposit
- List deposits

### Financial Reports (16 tests)
- Trial Balance
- Balance Sheet
- Profit & Loss
- Income Statement
- AR Aging
- AP Aging
- Cash Flow
- General Ledger
- Customer balance
- Vendor balance
- Inventory valuation report
- Inventory stock status report
- Payroll summary report
- Payroll detail report
- Sales by customer
- Expenses by vendor

### Payroll (15 tests)
- List/Create pay schedules
- Get pay schedule by ID
- Due pay schedules
- Assign employee to schedule
- List/Create pay runs
- Get pay run by ID
- List time entries
- Employee YTD
- Employee deductions
- Payroll summary
- Tax liability

### Recurring Transactions (1 test)
- List recurring templates

### 1099 Tracking (2 tests)
- 1099 summary
- 1099 year data

### Bank Feeds (3 tests)
- Bank feeds summary
- Bank feed transactions
- Bank feed rules

### Classes/Departments (8 tests)
- Create/List/Get/Update class
- Classes summary
- Classes hierarchy
- Class transactions
- Profitability by class report

### Projects (14 tests)
- Create/List/Get/Update project
- Update project status
- Add/Get billable expense
- Add/Get billable time
- Add milestone
- Complete milestone
- Progress billing
- Project profitability
- Unbilled summary

### Budgets & Forecasting (14 tests)
- Create/List/Get budget
- Update budget line
- Activate budget
- Budget vs actual
- Budget monthly variance
- Create/List forecasts
- Forecast summary
- Create/List scenarios
- Run scenario
- Cash flow projection

---

## Farm Operations Workflow (97 tests)

### Field Management (6 tests)
- Create field
- List fields
- Get field by ID
- Update field
- Field summary
- List farms

### Equipment Management (8 tests)
- Create equipment
- List equipment
- Get equipment by ID
- Update equipment
- Equipment summary
- Equipment types
- Equipment statuses
- Update equipment hours

### Maintenance Management (5 tests)
- Create maintenance record
- List maintenance
- Maintenance alerts
- Maintenance types
- Equipment maintenance history

### Farm Inventory (10 tests)
- Create inventory item
- List inventory
- Get inventory item by ID
- Update inventory item
- Inventory summary
- Inventory categories
- Inventory locations
- Inventory alerts
- Create inventory transaction
- Get transaction history

### Task Management (5 tests)
- Create task
- List tasks
- Get task by ID
- Update task
- Change task status

### Crew Management (5 tests)
- Create crew
- List crews
- Get crew by ID
- Update crew
- List crew members

### Field Operations (5 tests)
- Create operation
- List operations
- Get operation by ID
- Operations summary
- Field operation history

### Climate/GDD Tracking (11 tests)
- Create GDD record
- List GDD records
- GDD accumulated
- GDD summary
- GDD growth stages
- GDD base temperatures
- Create precipitation record
- List precipitation
- Precipitation summary
- Precipitation types
- Climate summary

### Sustainability Metrics (16 tests)
- Create input usage
- List input usage
- Input usage summary
- Create carbon entry
- Carbon summary
- Create water usage
- Water summary
- Create sustainability practice
- List practices
- Practice types
- Sustainability scorecard
- Scores history
- Sustainability report
- Carbon factors
- Input categories
- Carbon sources

### Profitability Analysis (7 tests)
- Break-even analysis
- Input ROI analysis
- Scenario analysis
- Budget tracker
- Profitability summary
- Profitability crops list
- Profitability input categories

### Cost Tracking (11 tests)
- Create expense
- List expenses
- Get expense by ID
- Review pending expenses
- Unallocated expenses
- Cost per acre report
- Cost by category report
- Cost by crop report
- Cost categories
- Saved cost mappings
- Import batches

### Farm Reports (6 tests)
- Operations report
- Financial report
- Equipment report
- Inventory report
- Field performance report
- Dashboard summary

---

## Running Tests

```bash
# Run all tests
python tests/test_genfin_workflow.py && python tests/test_farm_workflow.py

# Or with pytest
python -m pytest tests/ -v
```

## Known Issues

3 payroll-related tests fail with Internal Server Error:
- Create pay schedule
- Due pay schedules
- Tax liability Q1

These are backend service bugs that need investigation.
