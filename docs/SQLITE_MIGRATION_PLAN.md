# GenFin SQLite Migration Plan

## Overview
Migrate all 13 GenFin in-memory services to SQLite persistence to ensure data survives restarts.

## Current State
- 13 services using `Dict[str, dataclass]` in-memory storage (51 dictionaries total)
- 1 service already migrated: `genfin_entity_service.py`
- 1 reference implementation: `genfin_1099_service.py`

## Migration Order (By Dependency)

### Phase 1: Foundation (Critical)
1. `genfin_core_service.py` - 6 tables (accounts, journal_entries, journal_entry_lines, fiscal_periods, classes, locations)
2. `genfin_reports_service.py` - 1 table (saved_reports)

### Phase 2: Business Operations
3. `genfin_receivables_service.py` - 8 tables (customers, invoices, invoice_lines, payments, payment_applications, credits, estimates, sales_receipts)
4. `genfin_payables_service.py` - 7 tables (vendors, bills, bill_lines, payments, payment_applications, credits, purchase_orders)
5. `genfin_inventory_service.py` - 8 tables (items, lots, adjustments, adjustment_lines, counts, count_items, price_levels, tax_codes)
6. `genfin_banking_service.py` - 11 tables (bank_accounts, transactions, checks, check_lines, check_batches, deposits, deposit_items, ach_batches, ach_entries, reconciliations, transfers)

### Phase 3: Supporting Services
7. `genfin_payroll_service.py` - 10 tables (employees, pay_rates, time_entries, earning_types, deduction_types, employee_deductions, pay_runs, paychecks, tax_payments, pay_schedules)
8. `genfin_fixed_assets_service.py` - 2 tables (fixed_assets, depreciation_entries)
9. `genfin_classes_service.py` - 7 tables (projects, billable_expenses, billable_time, milestones, progress_billings, transaction_classes)
10. `genfin_budget_service.py` - 4 tables (budgets, budget_lines, forecasts, scenarios)

### Phase 4: Auxiliary Services
11. `genfin_recurring_service.py` - 2 tables (recurring_templates, generated_transactions)
12. `genfin_bank_feeds_service.py` - 3 tables (import_files, imported_transactions, category_rules)
13. `genfin_advanced_reports_service.py` - 2 tables (memorized_reports, dashboard_widgets)

## Implementation Pattern

Each service migration follows this pattern:

```python
class GenFin[Service]Service:
    _instance = None

    def __new__(cls, db_path: str = "agtools.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "agtools.db"):
        if self._initialized:
            return
        self.db_path = db_path
        self._init_tables()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        # CREATE TABLE IF NOT EXISTS statements
        pass

    def _row_to_entity(self, row: sqlite3.Row) -> Dict:
        # Convert row to dictionary
        pass
```

## Key Changes Per Method Type

| Operation | In-Memory | SQLite |
|-----------|-----------|--------|
| Create | `self.entities[id] = entity` | `INSERT INTO ... VALUES (?)` |
| Read | `self.entities.get(id)` | `SELECT * FROM ... WHERE id = ?` |
| Update | `entity.field = value` | `UPDATE ... SET field = ? WHERE id = ?` |
| Delete | `del self.entities[id]` | `UPDATE ... SET is_active = 0` (soft delete) |
| List | `list(self.entities.values())` | `SELECT * FROM ... WHERE is_active = 1` |

## Critical Files

1. `backend/services/genfin_core_service.py` - Start here (foundation)
2. `backend/services/genfin_entity_service.py` - Reference implementation
3. `backend/services/base_service.py` - Utility patterns
4. `backend/database/db_utils.py` - Connection helpers

## Testing Strategy

1. Create temp database for each test
2. Verify CRUD operations
3. Test data persistence across service restart
4. Run existing workflow tests to ensure API compatibility

## Verification

After each service migration:
```bash
python -m pytest tests/test_genfin_api.py tests/test_genfin_workflow.py -v
```

## Estimated Effort

- Phase 1: 18-23 hours
- Phase 2: 48-64 hours
- Phase 3: 34-46 hours
- Phase 4: 11-16 hours
- **Total: 111-149 hours**

## Risk Mitigation

1. Keep method signatures identical for API compatibility
2. Use database transactions for multi-table operations
3. Create backups before migration
4. Test each service before moving to next
