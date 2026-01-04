# AgTools Test Results

> **Last Run:** January 3, 2026 | **Version:** 6.7.7

## Summary

| Test Suite | Tests | Passed | Failed | Pass Rate |
|------------|-------|--------|--------|-----------|
| GenFin Workflow | 54 | 54 | 0 | 100% |
| Farm Operations | 97 | 97 | 0 | 100% |
| **Total** | **151** | **151** | **0** | **100%** |

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

## GenFin Workflow (54 tests)

### Financial Management
- Customer Management (CRUD)
- Vendor Management (CRUD)
- Employee Management
- Chart of Accounts
- Invoice Workflow
- Bill Workflow
- Inventory Management
- Purchase Orders
- Journal Entries
- Checks
- Time Entries
- Fixed Assets
- Bank Accounts
- Entities (Multi-Company)
- Deposits
- Financial Reports (8 reports)
- Payroll
- Recurring Transactions
- 1099 Tracking
- Bank Feeds

---

## Running Tests

```bash
# Run all tests
python tests/test_genfin_workflow.py && python tests/test_farm_workflow.py

# Or with pytest
python -m pytest tests/ -v
```
