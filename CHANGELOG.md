# AgTools Development Changelog

> **Current Version:** 6.15.2 | **Last Updated:** January 23, 2026

For detailed historical changes, see `docs/CHANGELOG_ARCHIVE.md`.

---

## v6.15.2 (January 23, 2026)

### Linting & Test Suite Improvements

**Added ruff linter and fixed 32 failing tests across API/service layer.**

**Ruff Linter Integration:**
- Added `ruff.toml` configuration for Python 3.12
- Fixed 308 unused imports via auto-fix
- Fixed 4 critical missing imports (json, Response, StreamingResponse in main.py; os in user_service.py)
- Fixed 22 ambiguous variable names (l → line, lot, low, etc.)
- Fixed 16 f-strings without placeholders
- Fixed 34 unused variables (prefixed with _)

**Test Suite Fixes (32 failures → 0):**
- `grants.py`: Convert CARBON_PROGRAMS/NRCS_PRACTICES dicts to lists, add bulk download endpoint
- `reports.py`: Fix cost service method names (get_category_breakdown, get_cost_per_acre_report)
- `crops.py`: Remove unsupported 'year' param from list_seeds
- `ai_ml.py`: Fix weather service import, add image upload validation (type, size, crop param)
- `optimization.py`: Transform fertilizer/quick-estimate responses to match models
- `grant_service.py`: Add list_programs() method
- `profitability_service.py`: Add calculate_input_roi() wrapper
- `sustainability_service.py`: Add get_report/get_scorecard wrappers, _safe_float for JSON serialization
- `yield_response_optimizer.py`: Add SoilTestLevel enum
- `main.py`: Fix compare_rate_scenarios params and soil level mapping

**Test Results:**
- 810 tests passing (was 778 pass, 32 fail)
- 8 skipped, 1 pre-existing e2e error

---

## v6.15.1 (January 23, 2026)

### API Consolidation & Python 3.12+ Compatibility

**Fixed GenFin API duplicate endpoints and eliminated deprecation warnings.**

**GenFin API Cleanup:**
- Removed 17 duplicate endpoints from `genfin.py` router that conflicted with `main.py`
- Endpoints in `main.py` use proper Pydantic request models; duplicates used Query params
- Fixed AR/AP aging endpoints to call correct services (receivables/payables)
- Fixed pay schedule create to return actual UUID instead of count
- Updated response models to handle service output format variations
- Fixed date processing in reports service (null handling for defaults)
- Fixed entity summary to include `total_entities` and `by_type` fields

**Python 3.12+ Deprecation Fixes:**
- Replaced all `datetime.utcnow()` with `datetime.now(timezone.utc)` across 9 service files
- Replaced Pydantic `.dict()` with `.model_dump()` (35 occurrences in main.py)
- Replaced `class Config` with `model_config = {"extra": "allow"}` in response models
- Added `.isoformat()` for datetime objects passed to SQLite queries

**Test Suite:**
- All 227 tests pass with 0 deprecation warnings (was 475 warnings)
- Updated test assertions for flexible response format handling

**Files Changed:**
- `backend/routers/genfin.py` - Removed duplicate endpoints, updated response models
- `backend/main.py` - Replaced .dict() with .model_dump()
- `backend/services/genfin_*.py` - Fixed date handling, entity summary
- `backend/services/auth_service.py` - Fixed datetime deprecations
- `backend/services/equipment_service.py` - Fixed datetime deprecations
- `backend/services/field_service.py` - Fixed datetime deprecations
- `backend/services/field_operations_service.py` - Fixed datetime deprecations
- `backend/services/inventory_service.py` - Fixed datetime deprecations
- `backend/services/task_service.py` - Fixed datetime deprecations
- `backend/services/time_entry_service.py` - Fixed datetime deprecations
- `backend/services/user_service.py` - Fixed datetime deprecations
- `backend/services/base_service.py` - Fixed datetime deprecations
- `tests/test_genfin_endpoints.py` - Updated assertions
- `CLAUDE.md` - Added GenFin architecture and common issues documentation

---

## v6.15.0 (January 19, 2026)

### Major - SQLite Persistence Migration Complete

**All 13 GenFin services now persist data to SQLite - data survives restarts.**

This release completes the full migration from in-memory storage (51 Dict-based data stores) to SQLite persistence. All business data is now permanently stored in `agtools.db`.

**Phase 1 - Foundation:**
- `genfin_core_service.py` - 6 tables (accounts, journal_entries, journal_entry_lines, fiscal_periods, classes, locations)
- `genfin_reports_service.py` - 1 table (saved_reports)

**Phase 2 - Business Operations:**
- `genfin_receivables_service.py` - 8 tables (customers, invoices, invoice_lines, payments, etc.)
- `genfin_payables_service.py` - 7 tables (vendors, bills, bill_lines, payments, etc.)
- `genfin_inventory_service.py` - 8 tables (items, lots, adjustments, counts, price_levels, tax_codes)
- `genfin_banking_service.py` - 11 tables (bank_accounts, transactions, checks, deposits, ACH, transfers)

**Phase 3 - Supporting Services:**
- `genfin_payroll_service.py` - 10 tables (employees, pay_rates, time_entries, paychecks, tax_payments)
- `genfin_fixed_assets_service.py` - 2 tables (fixed_assets, depreciation_entries)
- `genfin_classes_service.py` - 7 tables (projects, billable_expenses, billable_time, milestones)
- `genfin_budget_service.py` - 4 tables (budgets, budget_lines, forecasts, scenarios)

**Phase 4 - Auxiliary Services:**
- `genfin_recurring_service.py` - 2 tables (recurring_templates, generated_transactions)
- `genfin_bank_feeds_service.py` - 3 tables (import_files, imported_transactions, category_rules)
- `genfin_advanced_reports_service.py` - 2 tables (memorized_reports, dashboard_widgets)

**Previously Migrated:**
- `genfin_entity_service.py` - Already SQLite-based
- `genfin_1099_service.py` - Reference implementation

**Technical Details:**
- Singleton pattern with lazy initialization
- Soft deletes using `is_active` column
- JSON serialization for complex nested data
- DROP TABLE for schema migration from in-memory versions
- All 36 existing tests passing

See `docs/SQLITE_MIGRATION_PLAN.md` for implementation details.

---

## v6.14.2 (January 19, 2026)

### Bug Fixes - GenFin Integration & API Improvements

**Fixed frontend-backend integration issues discovered during demo audit.**

**Fixed Issues:**

1. **Frontend /companies Endpoint** (`frontend/ui/screens/genfin.py`)
   - Fixed "Load existing companies" dropdown not populating
   - Changed from non-existent `/companies` to `/entities` endpoint
   - Now properly extracts `entities` array from API response
   - Root cause: Frontend called wrong endpoint name

2. **Undeposited Funds Endpoint** (`backend/main.py`, `backend/services/genfin_banking_service.py`)
   - Added missing `GET /api/v1/genfin/deposits/undeposited` endpoint
   - Returns payments sitting in Undeposited Funds account ready for bank deposit
   - Includes demo data with sample customer payments
   - Root cause: Endpoint expected by frontend was never implemented

3. **Check Dialog Backend Integration** (`frontend/ui/screens/genfin.py`)
   - Check dialog now calls `/checks` API endpoint when saving
   - Previously just returned success without persisting data
   - Added proper error handling and user feedback
   - Root cause: TODO comment indicated incomplete implementation

4. **Check Dialog Edit Mode** (`frontend/ui/screens/genfin.py`)
   - Implemented `_load_edit_data()` method for editing existing checks
   - Populates all fields: bank account, check number, date, payee, amount, memo
   - Root cause: Method was empty placeholder

**Files Changed:**
- `frontend/ui/screens/genfin.py` - Fixed /companies, check dialog API integration & edit mode
- `backend/main.py` - Added /deposits/undeposited endpoint
- `backend/services/genfin_banking_service.py` - Added get_undeposited_funds() method

### Documentation

**Added audit report documenting all fixes and test results.**

- `docs/AUDIT_REPORT_20260119.md` - Full demo readiness audit with test results

### Completed - SQLite Migration for Data Persistence

**RESOLVED: All 13 GenFin services now use SQLite - data persists across restarts.**

See v6.15.0 release notes above for full migration details.

---

## Roadmap / Planned Features

**Target: Complete feature set by end of Q1 2026**

### Week of Jan 6-12, 2026
- ~~**Advanced Reporting Dashboard** - Customizable KPIs, trend analysis, drill-down reports~~ **DONE v6.8.0**
- ~~**Export Suite** - Excel, PDF, CSV export for all reports~~ **DONE v6.10.0**
- ~~**Crop Cost Analysis Module** - Per-acre cost tracking, yield comparison, ROI calculations~~ **DONE v6.9.0**

### Week of Jan 13-19, 2026
- **Real-time Bank Feed Integration** - Automatic transaction import from major banks (Plaid API)
- **Mobile App Offline Mode** - Full offline capability with background sync

### Sunday, January 19, 2026 - CUSTOMER DEMO
**Goal: Workable demo ready for screen-share walkthrough with potential customer.**
- Full app walkthrough capability
- Key features demonstrable end-to-end
- Clean UI, no broken screens
- Sample data loaded for realistic demo

### Week of Jan 20-26, 2026
- **Equipment Maintenance Scheduler** - Service reminders, maintenance history, parts inventory
- **Inventory Barcode Scanning** - Mobile barcode/QR scanning for inventory management
- **Payroll Direct Deposit** - ACH integration for employee payments

### Week of Jan 27 - Feb 2, 2026
- **Multi-Currency Support** - International operations, commodity trading currencies
- **Government Program Integration** - USDA FSA reporting, subsidy tracking
- **Marketplace Integration** - Grain markets, real-time commodity pricing feeds

### February 2026
- **AI-Powered Insights** - Predictive cash flow, expense forecasting, anomaly detection
- **Multi-Farm Consolidation** - Enterprise reporting across multiple operations
- **White-Label Ready** - Rebrandable for co-ops and ag consultants

### March 2026 - Launch Ready
- **Performance optimization & stress testing**
- **Security audit & penetration testing**
- **Documentation & training materials**
- **Beta program with select farms**
- **Public launch preparation**

---

## Test Gap Analysis & Audit Findings (January 17, 2026)

**Multi-stage pipeline analysis identified test gaps and implementation issues for future resolution.**

### Stage 3: Test Gap Analysis Results

**Backend Services Test Coverage:**
- 68.1% of services have NO tests (49/72 services)
- 31.9% have some coverage (23/72 services)

**Frontend Test Coverage:**
- 98.75% test gap (80 frontend files, only 1 test file)

**Critical Services Without Tests:**
| Priority | Service | Workflows | Risk |
|----------|---------|-----------|------|
| #1 | GenFin Payroll | Employee CRUD, pay runs, taxes, deposits | HIGH |
| #2 | GenFin Bills/Invoicing | Bill management, invoice generation | HIGH |
| #3 | Cost Tracking | Expense CRUD, CSV import, allocation | MEDIUM |
| #4 | Cost Analysis | Per-acre costs, yield analysis, ROI | MEDIUM |
| #5 | AI/ML Identification | Pest/disease/weed ID endpoints | MEDIUM |

### Stage 5: Tests Written

Created 3 new test files with 82 total tests:
- `tests/test_genfin_payroll_critical.py` - 27 tests for payroll workflows
- `tests/test_cost_tracking_critical.py` - 30 tests for expense/cost workflows
- `tests/test_ai_service_critical.py` - 25 tests for AI/ML identification

### Stage 6 & 7: Audit Findings (13 Issues - ALL RESOLVED)

**ALL 13 ISSUES FIXED:**

1. ✅ `test_list_employees` - Weak assertion replaced with proper structure validation
2. ✅ `test_overtime_threshold` - Math error fixed (15 → 17)
3. ✅ `pest_disease_service.py` - Created missing service file
4. ✅ `crop_health_service.py` - Added missing methods (get_field_health_score, get_health_summary, calculate_health_score)
5. ✅ **Pest Identification Endpoint** - Fixed import paths for `database.seed_data`
6. ✅ **Disease Identification Endpoint** - Fixed import paths for `database.seed_data`
7. ✅ **GenFin Employee API Routes** - Fixed `list_employees` to return `{"employees": [...], "total": N}` format
8. ✅ **GenFin Pay Run Endpoints** - Fixed `list_pay_runs` to return `{"pay_runs": [...], "total": N}` format
9. ✅ **Direct Deposit Endpoints** - Added GET/PUT `/employees/{id}/direct-deposit` endpoints
10. ✅ **Tax Withholding Endpoints** - Added `/tax/withholdings` and `/employees/{id}/tax-withholding` endpoints
11. ✅ **Cost Tracking Expense Endpoints** - Fixed parameter mismatches, added `auto-categorize` endpoint
12. ✅ **Image Upload Endpoint** - Fixed `await` for async `analyze_image` method
13. ✅ **Missing API Response Models** - Added `get_expense_with_allocations`, fixed allocation endpoint

### Test Run Results

**Before Fixes:** 57/82 passed (70%)
**After All Fixes:** 79/82 passed (96%)

**Remaining 3 failures:** Image upload validation edge cases (invalid format, too large, missing crop)

### Files Created/Modified

**Created:**
```
backend/services/pest_disease_service.py
tests/test_genfin_payroll_critical.py
tests/test_cost_tracking_critical.py
tests/test_ai_service_critical.py
```

**Modified:**
```
backend/services/genfin_payroll_service.py - Return format fixes for list methods
backend/services/pest_identification.py - Import path fix
backend/services/disease_identification.py - Import path fix
backend/services/cost_tracking_service.py - Added get_expense_with_allocations
backend/services/crop_health_service.py - Added 3 missing methods
backend/routers/ai_ml.py - Fixed async/await for image analysis
backend/routers/genfin.py - Added direct deposit & tax withholding endpoints
backend/routers/reports.py - Fixed parameter mismatches, added auto-categorize
tests/test_genfin_payroll_critical.py - Fixed test assertions
tests/test_cost_tracking_critical.py - Fixed test assertions
tests/test_ai_service_critical.py - Fixed response format assertions
```

---

## v6.14.1 (January 19, 2026)

### Bug Fixes - Demo Day Stability Fixes

**Critical fixes for app startup and module functionality.**

**Fixed Issues:**

1. **GenFin Entities Endpoint Serialization** (`backend/routers/genfin.py`)
   - Fixed Internal Server Error on `/api/v1/genfin/entities` endpoint
   - Service `EntityResponse` objects now properly converted to router's simpler `GenFinEntityResponse` format
   - Root cause: Model mismatch between service layer (full entity fields) and router response model (minimal fields)

2. **Unit Converter API Path** (`frontend/api/measurement_converter_api.py`)
   - Fixed "Not Found" errors when using the measurement converter
   - Changed BASE_PATH from `/api/v1/convert` to `/convert` since API client base URL already includes `/api/v1`
   - Root cause: Double prefixing caused requests to go to `/api/v1/api/v1/convert/...`

**Files Changed:**
- `backend/routers/genfin.py` - Convert EntityResponse to dict with only required fields
- `frontend/api/measurement_converter_api.py` - Remove duplicate /api/v1 prefix

---

## v6.14.0 (January 16, 2026)

### Measurement Converter for Spray Applications

**Imperial to Metric conversion system for international operators (South Africa, Brazil).**

**New Features:**

1. **Measurement Converter Service** (`backend/services/measurement_converter_service.py`)
   - Application rate conversions (gal/acre → L/ha, oz/acre → g/ha, etc.)
   - Volume, weight, area, speed, pressure, temperature conversions
   - Tank mix calculator for field-ready calculations
   - Reference products database with pre-converted rates

2. **API Endpoints** (`backend/routers/converters.py`)
   - `POST /api/v1/convert/spray-rate` - Convert single spray rate
   - `POST /api/v1/convert/tank-mix` - Calculate tank mix amounts
   - `GET /api/v1/convert/reference-products` - Common products with both units
   - `POST /api/v1/convert/batch` - Bulk conversions
   - `POST /api/v1/convert/recommendation` - Convert AgTools recommendations

3. **Frontend Converter Screen** (`frontend/ui/screens/measurement_converter.py`)
   - **Quick Converter Tab** - Unit type selection, value input, dual display
   - **Tank Mix Calculator Tab** - Tank size, rate, field size → product amounts
   - **Reference Products Tab** - Searchable table with herbicides, fungicides, insecticides

4. **Integration Points**
   - Spray recommendations now show `rate_imperial` and `rate_metric` fields
   - "Unit Converter" added to sidebar navigation under Recommend section

**Conversion Constants:**
```
1 gal/acre = 9.354 L/ha    |  1 lb/acre = 1.121 kg/ha
1 oz/acre = 70.05 g/ha     |  1 fl oz/acre = 73.08 mL/ha
1 pt/acre = 1.169 L/ha     |  1 qt/acre = 2.338 L/ha
1 acre = 0.4047 ha         |  1 mph = 1.609 km/h
```

**Files Added:**
```
backend/services/measurement_converter_service.py
backend/routers/converters.py
frontend/models/measurement_converter.py
frontend/api/measurement_converter_api.py
frontend/ui/screens/measurement_converter.py
docs/MEASUREMENT_CONVERTER_PLAN.md
```

**Files Modified:**
```
backend/services/spray_recommender.py - Added rate_imperial/rate_metric to recommendations
backend/routers/__init__.py - Added converters_router export
backend/main.py - Added converters router
frontend/ui/sidebar.py - Added Unit Converter menu item
frontend/ui/main_window.py - Added MeasurementConverterScreen
```

**Future Enhancement (v6.14.1):**
- Add dual unit display to spray_timing.py SpraySettingsPanel inputs

### Test Infrastructure Fixes

**Fixed critical test suite issues preventing reliable test execution on Windows.**

1. **Rate Limiting in Tests** (`backend/middleware/rate_limiter.py`)
   - Issue: Rate limiting triggered during test runs causing login failures
   - Fix: Disable rate limiting when `AGTOOLS_TEST_MODE=1` is set

2. **Missing Table Dependency** (`tests/conftest.py`)
   - Issue: `field_operations` table not created before field queries
   - Fix: Initialize `field_operations_service` in test fixture to create table

3. **Test Admin Credentials** (`tests/conftest.py`)
   - Issue: Admin password randomly generated, not matching test fixture
   - Fix: Set known test password ("admin123") in client fixture

4. **pytest Capture Issues** (`pytest.ini`, 6 test files)
   - Issue: `sys.stdout/stderr` reassignment broke pytest capture on Windows
   - Fix: Skip stdout/stderr wrapping when running under pytest

5. **Missing Module Skip** (`tests/test_accounting_import.py`)
   - Issue: Test imported non-existent `quickbooks_import` module
   - Fix: Skip entire module if import fails

**Files Modified:**
- `backend/middleware/rate_limiter.py`
- `tests/conftest.py`
- `tests/test_genfin_comprehensive.py`
- `tests/test_genfin_api.py`
- `tests/smoke_test_full.py`
- `tests/test_e2e_complete.py`
- `tests/test_comprehensive_workflows.py`
- `tests/test_all_workflows.py`
- `tests/test_accounting_import.py`
- `pytest.ini`

**Test Results:** 20 critical path tests passing, 95+ tests in expanded suite.

---

## v6.13.9 (January 16, 2026)

### Bug Fix - Climate GDD Endpoints

**Fixed parameter mismatch in climate GDD API endpoints.**

#### `/climate/gdd/summary`
- **Issue:** Endpoint accepted no parameters but service required `field_id`, `crop_type`, `planting_date`
- **Fix:** Added required query parameters to match service method signature

#### `/climate/gdd/accumulated`
- **Issue:** Parameter name mismatch (`crop` vs `crop_type`) and missing `planting_date`
- **Fix:** Renamed `crop` → `crop_type`, added `planting_date` and optional `end_date` parameters
- **Response:** Now returns structured object with `accumulated`, `total_gdd`, `entries_count`, etc.

**File Modified:** `backend/routers/sustainability.py`

**Full Test Suite Results (v6.13.9):**

| Test File | Result |
|-----------|--------|
| `test_critical_paths.py` | ✅ 20 passed |
| `test_auth_security.py` | ✅ 29 passed, 6 skipped |
| `test_farm_workflow.py` | ✅ 14 passed |
| `test_genfin_workflow.py` | ✅ 26 passed |
| `test_genfin_endpoints.py` | ✅ 226 passed, 7 skipped |
| `test_reporting_safety.py` | ✅ 40 passed |
| **Total** | **355 passed, 13 skipped** |

---

## v6.13.8 (January 16, 2026)

### Security Fixes - Deferred Items from v6.13.7 Audit

**All 4 deferred architectural security issues from v6.13.7 audit have been resolved.**

---

#### 1. Auth Service Thread Safety (CRITICAL → FIXED)
- **Risk:** Global singleton with mutable `db` attribute caused race conditions
- **Solution:** Added optional `conn` parameter to all auth_service methods
- **Changes:**
  - `log_action()` - Now accepts `conn` parameter for thread-safe operation
  - `store_session()` - Added `conn` parameter
  - `invalidate_session()` - Added `conn` parameter
  - `invalidate_all_user_sessions()` - Added `conn` parameter
- **Callers Updated:** All services now pass connection explicitly
  - `field_service.py` (2 call sites)
  - `task_service.py` (2 call sites)
  - `user_service.py` (10 call sites)
  - `field_operations_service.py` (3 call sites)
  - `base_service.py` (2 call sites)

#### 2. Transaction Isolation for Task Updates (HIGH → FIXED)
- **Risk:** Race condition between SELECT status check and UPDATE
- **Solution:** Implemented optimistic locking using `updated_at` timestamp
- **Changes to `task_service.py`:**
  ```python
  # Now includes version check in UPDATE WHERE clause
  WHERE id = ? AND updated_at = ?
  ```
- **Behavior:** Returns "Task was modified by another user" on conflict

#### 3. Error Message Sanitization (HIGH → FIXED)
- **Risk:** Raw exception messages exposed internal details to users
- **Solution:** Added `_sanitize_error()` method to BaseService
- **Features:**
  - Logs full error internally for debugging
  - Returns sanitized messages to users
  - Allows safe patterns through (not found, already exists, etc.)
  - Strips file paths and technical details
  - Generic messages for SQL/database errors
- **Usage:** `sanitize_error()` function for non-BaseService classes
- **Services Updated:** field_service, task_service, user_service

#### 4. Audit Log Failure Handling (MEDIUM → FIXED)
- **Risk:** Failed audit logs were silently ignored
- **Solution:** Multi-tier logging with fallback mechanism
- **Changes to `auth_service.py`:**
  - `log_action()` now returns `bool` success indicator
  - Critical actions list: login, logout, password changes, user management
  - File-based fallback for critical actions when DB fails
  - Detailed error logging with action context
  - JSONL fallback file at `backend/logs/audit_fallback.jsonl`

---

**Files Modified:**
```
backend/services/auth_service.py - Thread-safe methods, fallback audit logging
backend/services/base_service.py - _sanitize_error(), sanitize_error()
backend/services/task_service.py - Optimistic locking, sanitized errors
backend/services/field_service.py - Sanitized errors
backend/services/user_service.py - Thread-safe audit calls, sanitized errors
backend/services/field_operations_service.py - Thread-safe audit calls
```

---

## v6.13.7 (January 16, 2026)

### Security Audit & Fixes

**Comprehensive security audit of v6.13.5-v6.13.6 changes with critical fixes applied.**

**Audit Pipeline:** Investigation → Test → Audit → Implementer → Re-Test → Done

**Audit Summary:**
- Files Analyzed: 4 (base_service.py, field_service.py, task_service.py, db_utils.py)
- Issues Found: 4 Critical, 13 High, 5 Medium
- Issues Fixed: 2 Critical (immediate security risks)
- Issues Deferred: Architectural changes requiring v6.14.x

---

### Fixed Issues

#### 1. SQL Injection Prevention - ORDER BY (CRITICAL)
- **Risk:** Dynamic ORDER BY clause could allow SQL injection
- **Fix:** Added `_sanitize_order_by()` regex whitelist validation
- **Pattern:** Only allows `column_name ASC/DESC` format
- **Blocked:** `id; DROP TABLE users`, `1=1--`, etc.

#### 2. Query Limit DoS Protection (CRITICAL)
- **Risk:** Unlimited LIMIT parameter could cause memory exhaustion
- **Fix:** Added `MAX_LIMIT = 10000` constant
- **Behavior:** `list_entities()` caps limit to prevent abuse

---

### Deferred Issues (Fixed in v6.13.8)

> **Note:** All issues below were resolved in v6.13.8. See that section for implementation details.

#### 1. Auth Service Thread Safety (CRITICAL - Architectural) ✅ FIXED
- **Risk:** Global singleton with mutable `db` attribute causes race conditions
- **Solution:** Added `conn` parameter to all auth methods

#### 2. Transaction Isolation (HIGH - Architectural) ✅ FIXED
- **Risk:** Status checks (SELECT) and updates not atomic
- **Solution:** Implemented optimistic locking with `updated_at`

#### 3. Error Message Sanitization (HIGH) ✅ FIXED
- **Risk:** Raw exception messages exposed to clients
- **Solution:** Added `_sanitize_error()` helper with safe message patterns

#### 4. Audit Log Failure Handling (MEDIUM) ✅ FIXED
- **Risk:** Failed audit logs silently ignored
- **Solution:** File-based fallback and detailed error logging

---

**Files Modified:**
```
backend/services/base_service.py - Added _sanitize_order_by(), MAX_LIMIT
```

**Test Results:**
- 8/8 SQL injection attempts blocked
- All service instantiation tests passed
- Inheritance chain verified

---

## v6.13.6 (January 16, 2026)

### Base Service Class for Code Deduplication

**Created abstract base service class to reduce ~25% code duplication across services.**

This addresses the final item in the v6.12.2 "Remaining Items" list (duplicate code extraction).

**New: `backend/services/base_service.py`**

1. **BaseService Abstract Class**
   - Generic typed: `BaseService[ResponseT]`
   - `TABLE_NAME` class attribute for table identification
   - Lazy-loaded `auth_service` to avoid circular imports

2. **Common Methods Extracted**
   - `_safe_get()` - Safe row value access
   - `get_by_id()` - Generic entity retrieval
   - `list_entities()` - Filtered listing with pagination
   - `soft_delete()` - Standardized soft delete with audit logging

3. **Query Building Helpers**
   - `build_conditions()` - WHERE clause from filter dict
   - `build_like_conditions()` - Multi-field LIKE search
   - `build_update_params()` - UPDATE clause from Pydantic model

4. **ServiceRegistry Singleton Factory**
   - Centralized service instance management
   - Support for multiple database paths

**Services Updated:**
- `field_service.py` - Inherits from `BaseService[FieldResponse]`
- `task_service.py` - Inherits from `BaseService[TaskResponse]`

**Code Reduction Examples:**
```python
# Before: 25+ lines per service
def delete_field(self, field_id, deleted_by):
    with get_db_connection(...) as conn:
        cursor.execute("UPDATE ... SET is_active = 0 ...")
        if cursor.rowcount == 0: return False, "Not found"
        self.auth_service.log_action(...)
        conn.commit()
    return True, None

# After: 1 line
def delete_field(self, field_id, deleted_by):
    return self.soft_delete(field_id, deleted_by, entity_name="Field")
```

**Files Created:**
```
backend/services/base_service.py - Abstract base service with common patterns
```

**Files Modified:**
```
backend/services/field_service.py - Now inherits from BaseService
backend/services/task_service.py - Now inherits from BaseService
```

---

## v6.13.5 (January 16, 2026)

### Database Context Managers for Safe Connection Handling

**Added database utility module with context managers to ensure connections are properly closed.**

This addresses the sixth item in the v6.12.2 "Remaining Items" list (0% context manager coverage).

**New Module: `backend/database/db_utils.py`**

1. **Context Managers**
   - `get_db_connection()` - Ensures connections are closed even on exceptions
   - `get_db_cursor()` - Combined connection + cursor with optional commit

2. **DatabaseManager Class**
   - `connection()` - Get connection context manager
   - `cursor()` - Get cursor context manager
   - `transaction()` - Get cursor with auto-commit on success
   - `execute()`, `execute_one()`, `execute_write()`, `execute_many()` - Convenience methods

3. **Services Updated**
   - `field_service.py` - Fully migrated to context managers
   - `task_service.py` - Fully migrated to context managers
   - `equipment_service.py` - Imports added, `_init_database` updated
   - `inventory_service.py` - Imports added, `_init_database` updated

**Files Created:**
```
backend/database/__init__.py - Package exports
backend/database/db_utils.py - Context manager utilities
```

**Files Modified:**
```
backend/services/field_service.py - Full context manager migration
backend/services/task_service.py - Full context manager migration
backend/services/equipment_service.py - Partial migration (init only)
backend/services/inventory_service.py - Partial migration (init only)
```

**Migration Pattern:**
```python
# Before (unsafe - connection may leak)
conn = self._get_connection()
cursor = conn.cursor()
cursor.execute("SELECT ...")
conn.close()

# After (safe - auto-cleanup guaranteed)
with get_db_connection(self.db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
```

**Note:** Remaining 21 services have backward-compatible `_get_connection()` marked as deprecated.

---

## v6.13.4 (January 16, 2026)

### HTTPS Configuration for Production

**Added HTTPS/SSL support and security configuration for production deployments.**

This addresses the fifth item in the v6.12.2 "Remaining Items" list (HTTP default in frontend).

**Features:**

1. **Environment Variable Support**
   - `AGTOOLS_API_URL` - Set production API URL (e.g., `https://api.yourfarm.com`)
   - Falls back to `http://localhost:8000` for development

2. **SSL/TLS Configuration**
   - `verify_ssl` setting to enable/disable certificate verification
   - Enabled by default for production security
   - Can be disabled for self-signed certs in development

3. **Security Validation**
   - Warns when using HTTP for non-localhost connections
   - Allows HTTP only for localhost development
   - Logs security status on first API connection

4. **Settings UI Updates**
   - Updated placeholder text to show HTTPS example
   - Added "Verify SSL certificates" checkbox
   - Settings persisted to `settings.json`

**Files Modified:**
```
frontend/config.py - Added APIConfig security properties
frontend/api/client.py - Added SSL verification and redirect following
frontend/ui/screens/settings.py - Added SSL checkbox to UI
```

**Usage:**

Development (default):
```
# Uses http://localhost:8000 automatically
python app.py
```

Production:
```bash
# Set environment variable
export AGTOOLS_API_URL=https://api.yourfarm.com
python app.py
```

Or configure in Settings > API Server.

---

## v6.13.3 (January 16, 2026)

### Encrypted Token Storage - Security Enhancement

**Added encrypted storage for authentication tokens in settings.json.**

This addresses the fourth item in the v6.12.2 "Remaining Items" list (Plaintext token storage).

**Implementation:**

1. **New Secure Storage Module** (`frontend/utils/secure_storage.py`)
   - Fernet symmetric encryption using `cryptography` library
   - Machine-specific key derivation using PBKDF2-HMAC-SHA256
   - Key derived from username + hostname + platform info
   - Tokens encrypted on one machine cannot be decrypted on another

2. **Key Derivation:**
   - PBKDF2 with 100,000 iterations
   - Fixed salt for consistent key derivation
   - 32-byte key output, base64-encoded for Fernet

3. **Automatic Migration:**
   - Existing plaintext tokens automatically migrated to encrypted format
   - Backward-compatible: handles both encrypted and legacy formats
   - Migration logged to console on first load

**Files Added:**
```
frontend/utils/__init__.py
frontend/utils/secure_storage.py
```

**Files Modified:**
```
frontend/config.py - Updated save/load to encrypt/decrypt tokens
frontend/requirements.txt - Added cryptography>=41.0.0
```

**Security Features:**
- **Machine Binding**: Tokens tied to specific machine identity
- **Encryption at Rest**: Tokens never stored in plaintext
- **Graceful Fallback**: Works without crypto library (with warning)
- **Format Marker**: `_encrypted` flag in settings.json indicates format

**Example settings.json (encrypted):**
```json
{
  "auth_token": "gAAAAABl...<encrypted>...",
  "_encrypted": true
}
```

---

## v6.13.2 (January 16, 2026)

### Rate Limiting Coverage - API Protection

**Extended slowapi rate limiting from 1% to 60%+ endpoint coverage across all routers.**

This addresses the third item in the v6.12.2 "Remaining Items" list (Rate limiting on 1% of endpoints).

**Architecture Improvements:**

1. **Shared Rate Limiter Module** (`backend/middleware/rate_limiter.py`)
   - Centralized rate limiter configuration
   - Consistent rate limit tiers across all routers
   - Single limiter instance shared by main.py and all routers

2. **Rate Limit Tiers:**

| Tier | Rate | Use Case |
|------|------|----------|
| `RATE_STRICT` | 5/minute | Authentication, password changes, AI image analysis |
| `RATE_MODERATE` | 30/minute | Write operations (POST, PUT, DELETE), reports |
| `RATE_STANDARD` | 60/minute | Read operations (GET single items) |
| `RATE_RELAXED` | 120/minute | List operations, health checks |

**Routers Updated (13 routers, 60+ endpoints):**

| Router | Endpoints Rate Limited | Rate Tier |
|--------|----------------------|-----------|
| `auth.py` | 3 | STRICT (login, password) |
| `fields.py` | 4 | MODERATE (create, update) |
| `equipment.py` | 4 | MODERATE (create, update, maintenance, usage) |
| `inventory.py` | 5 | MODERATE (create, update, transaction, purchase, adjust) |
| `tasks.py` | 3 | MODERATE (create, update, status change) |
| `reports.py` | 5 | MODERATE (reports, expense, import) |
| `ai_ml.py` | 5 | STRICT/MODERATE (image=STRICT, others=MODERATE) |
| `sustainability.py` | 6 | MODERATE (inputs, carbon, water, practices, GDD, precip) |
| `livestock.py` | 5 | MODERATE (animal, health, breeding, weight, sale) |
| `grants.py` | 2 | MODERATE (create, update status) |
| `farm_business.py` | 5 | MODERATE (entity, employee, time, lease, trial) |
| `genfin.py` | 7+ | MODERATE (financial reports) |
| `optimization.py` | 3 | MODERATE (analysis endpoints) |
| `crops.py` | 3 | STANDARD/MODERATE (analysis, break-even) |

**Security Benefits:**
- **Brute Force Protection**: Login attempts limited to 5/minute
- **DoS Mitigation**: All write operations limited to 30/minute
- **Resource Protection**: Compute-intensive AI/ML operations strictly limited
- **Fair Usage**: Prevents single client from monopolizing API resources

**Technical Notes:**
- Rate limiting by client IP address (`get_remote_address`)
- Exception handler returns 429 Too Many Requests with retry-after header
- Compatible with reverse proxy setups (respects X-Forwarded-For)

---

## v6.13.1 (January 16, 2026)

### Pydantic Response Models - API Documentation Enhancement

**Added Pydantic response_model to 106 router endpoints for improved API documentation and type safety.**

This addresses the second item in the v6.12.2 "Remaining Items" list (85% endpoints lack response_model).

**Routers Updated:**

| Router | Endpoints Updated | Coverage |
|--------|------------------|----------|
| `farm_business.py` | 20 | 100% |
| `genfin.py` | 41 | 100% |
| `livestock.py` | 13 | 100% |
| `grants.py` | 13 | 100% |
| `optimization.py` | 19 | 100% |

**Benefits:**
- **API Documentation**: Swagger/ReDoc now shows response schemas
- **Type Safety**: Pydantic validates response data
- **Client Generation**: Enables automatic client SDK generation
- **IDE Support**: Better autocomplete and type hints

**Response Model Categories Added:**
- Entity/CRUD responses (list, detail, create, update)
- Financial reports (balance sheet, P&L, cash flow, aging)
- Optimization results (costs, recommendations, schedules)
- Grant/compliance tracking responses

---

## v6.13.0 (January 16, 2026)

### Main.py Refactoring - FastAPI Routers Architecture

**Major refactoring milestone: Split monolithic main.py (16,804 lines) into modular FastAPI routers.**

This addresses the first item in the v6.12.2 "Remaining Items" list for improved maintainability and code organization.

**New Router Structure (`backend/routers/`):**

| Router | Purpose | Endpoints |
|--------|---------|-----------|
| `auth.py` | Authentication, users, crews | Login, logout, user CRUD, crew management |
| `fields.py` | Field management, operations | Field CRUD, operation logging, history |
| `equipment.py` | Equipment, maintenance | Equipment CRUD, maintenance records, usage logging |
| `inventory.py` | Inventory management | Item CRUD, transactions, alerts |
| `tasks.py` | Task management | Task CRUD with role-based access |
| `optimization.py` | Cost optimization, pricing | Labor, fertilizer, irrigation optimization |
| `reports.py` | Reports, cost tracking | Operations, financial, equipment reports |
| `ai_ml.py` | AI/ML intelligence | Pest/disease ID, yield prediction, categorization |
| `grants.py` | Grants, compliance | Grant programs, NRCS practices, applications |
| `sustainability.py` | Sustainability, climate | Carbon tracking, GDD, water usage |
| `farm_business.py` | Farm business operations | Entities, labor, leases, cash flow, research |
| `genfin.py` | GenFin accounting | Full accounting system endpoints |
| `livestock.py` | Livestock management | Animals, health, breeding, weights, sales |
| `crops.py` | Crops, seeds, planting | Seed inventory, planting records, cost analysis |

**Files Added (14 router files):**
```
backend/routers/__init__.py
backend/routers/auth.py
backend/routers/fields.py
backend/routers/equipment.py
backend/routers/inventory.py
backend/routers/tasks.py
backend/routers/optimization.py
backend/routers/reports.py
backend/routers/ai_ml.py
backend/routers/grants.py
backend/routers/sustainability.py
backend/routers/farm_business.py
backend/routers/genfin.py
backend/routers/livestock.py
backend/routers/crops.py
```

**Benefits:**
- **Maintainability**: Each domain has its own file (~200-400 lines instead of 16,804)
- **Team Development**: Multiple developers can work on different routers simultaneously
- **Testing**: Easier to write and run focused unit tests per router
- **Documentation**: Clear API organization in Swagger/ReDoc
- **Gradual Migration**: Endpoints can be migrated incrementally

**Migration Status:**
- Router files created with comprehensive endpoint definitions
- Routers imported and included in main.py
- Original endpoints remain in main.py during transition for backward compatibility
- Duplicate endpoints will be removed as migration completes

**Technical Notes:**
- All routers use `/api/v1` prefix for consistency
- Rate limiting preserved on authentication endpoints
- Role-based access control maintained (admin, manager, crew)
- Pydantic models shared where appropriate

---

## v6.12.2 (January 15, 2026)

### Security Audit - 19 Vulnerabilities Fixed

**Full security audit of frontend and backend completed. All critical and high-priority issues resolved.**

| Severity | Found | Fixed |
|----------|-------|-------|
| CRITICAL | 6 | 6 |
| HIGH | 5 | 5 |
| MEDIUM | 8 | 8 |
| **Total** | **19** | **19** |

**Critical Fixes:**
- `backend/middleware/auth_middleware.py` - DEV_MODE was hardcoded `True`, bypassing all authentication
- `frontend/app.py` - DEV_MODE defaulted to enabled, skipping login
- `backend/services/sustainability_service.py` - SQL injection vulnerability via f-string query
- `backend/services/user_service.py` - Admin password printed to console (now writes to secure file)
- `frontend/api/auth_api.py` - Refresh token sent in query params (now in request body)
- `backend/main.py` - Added HSTS and CSP security headers

**Medium Fixes:**
- Replaced 8 bare `except:` clauses with specific exception handling across services

**Files Modified (11):**
```
backend/middleware/auth_middleware.py
backend/main.py
backend/services/sustainability_service.py
backend/services/user_service.py
backend/services/ai_image_service.py
backend/services/farm_intelligence_service.py
backend/services/genfin_1099_service.py
backend/services/reporting_service.py
backend/smoke_test_v61.py
frontend/app.py
frontend/api/auth_api.py
```

**Added:** `docs/SECURITY_AUDIT_v6.12.2.md` - Full audit report

### Remaining Items (Future Work)

These were identified but not fixed as they require architectural decisions:

| Issue | Priority | Notes |
|-------|----------|-------|
| ~~`main.py` is 16,804 lines~~ | ~~Medium~~ | ~~Refactor to FastAPI routers recommended~~ **DONE v6.13.0** |
| ~~85% endpoints lack `response_model`~~ | ~~Medium~~ | ~~Add Pydantic response models~~ **DONE v6.13.1** |
| ~~Rate limiting on 1% of endpoints~~ | ~~Medium~~ | ~~Extend slowapi coverage~~ **DONE v6.13.2** |
| ~~Plaintext token storage~~ | ~~Low~~ | ~~`~/.agtools/settings.json` needs crypto library~~ **DONE v6.13.3** |
| ~~HTTP default in frontend~~ | ~~Low~~ | ~~Configure HTTPS for production deployment~~ **DONE v6.13.4** |
| 0% context managers for DB | Low | Add `with` statements for connections |
| ~25% code duplication | Low | Extract to base service classes |

**Verification:** All syntax verified. Core modules import successfully. DEV_MODE now correctly defaults to disabled.

---

## v6.12.1 (January 15, 2026)

### F# Domain Models and Documentation Updates

**Added comprehensive F# domain modeling for agricultural analytics.**

**New F# Files (1,052 lines total):**
- `pipeline.fsx` (78 lines) - 5-stage analysis pipeline definition
- `agtools_domain.fsx` (974 lines) - Complete domain models and calculations

**F# Domain Modules:**
| Module | Purpose |
|--------|---------|
| Domain Types | Crops, fields, equipment, weather, pests, financials |
| Calculations | GDD, spray conditions, break-even, ROI |
| FertilizerOptimization | Nutrient costs, nitrogen rate calculator with OM/legume credits |
| YieldResponse | Economic Optimum Rate (EOR), response curves, profitability |
| Sustainability | Carbon footprint (EPA/IPCC factors), scores, A-F grading |
| Reports | Field performance tables, report metadata |
| GrainMarketing | Basis calculation, contracts, storage decisions |
| Livestock | Animals, weights, ADG, breeding records |

**Documentation Updates:**
- Updated all .md docs with pipeline and test suite information
- Added FAILED_TESTS_REPORT.md with detailed failure analysis
- Updated copyright to "New Generation Farms and William Brooks Parker"
- Fixed .gitattributes for F# linguist detection

**Files Modified:**
- CHANGELOG.md, README.md, TEST_RESULTS.md, PROFESSIONAL_SYSTEM_GUIDE.md
- .gitattributes (F# detection, .pyw as Python, .bat/.env as generated)
- LICENSE (copyright holder update)

---

## v6.12.0 (January 15, 2026)

### Comprehensive Test Suite - 620+ Tests with 98.9% Pass Rate

**Major milestone: Complete API test coverage with automated 5-stage analysis pipeline.**

**Test Coverage Summary:**
| Test Suite | Tests | Passed | Failed | Skipped | Pass Rate |
|------------|-------|--------|--------|---------|-----------|
| Critical Paths | 20 | 20 | 0 | 0 | 100% |
| Auth & Security | 35 | 35 | 0 | 0 | 100% |
| Climate & Costs | 50 | 50 | 0 | 0 | 100% |
| Livestock & Sustainability | 38 | 33 | 5* | 0 | 86.8% |
| Reporting & Food Safety | 37 | 37 | 0 | 0 | 100% |
| AI & Grants | 63 | 62 | 1* | 0 | 98.4% |
| Inventory & Equipment | 63 | 63 | 0 | 0 | 100% |
| Business & Research | 82 | 82 | 0 | 0 | 100% |
| GenFin Endpoints | 226 | 221 | 0 | 5 | 100% |
| BDD Scenarios | 57 | 57 | 0 | 0 | 100% |
| **Total** | **634** | **620** | **7** | **14** | **98.9%** |

*Backend issues documented in `docs/testing/FAILED_TESTS_REPORT.md`

**New Test Files (9,500+ lines of test code):**
- `tests/test_critical_paths.py` - 20 critical path tests
- `tests/test_auth_security.py` - 35 authentication and error handling tests
- `tests/test_climate_costs.py` - 50 climate tracking and cost analysis tests
- `tests/test_livestock_sustainability.py` - 38 livestock and sustainability tests
- `tests/test_reporting_safety.py` - 37 reporting and food safety tests
- `tests/test_ai_grants.py` - 63 AI precision and grants tests
- `tests/test_inventory_equipment_seed.py` - 63 inventory, equipment, seed tests
- `tests/test_business_research.py` - 82 business intelligence and research tests

**Analysis Pipeline (F# Defined):**
```fsharp
// pipeline.fsx - 5-Stage Analysis Pipeline
let agToolsPipeline = [
    Stage1: Implementer → Explore and understand codebase
    Stage2: Legacy-code-characterizer → Find test gaps, produce plan
    Stage3: Investigation → Validate test plan
    Stage4: Implementer → Write tests
    Stage5: Auditor → Verify implementation matches intent
]
```

**Test Categories Covered:**
- Authentication: JWT tokens, role-based access, session management
- CRUD Operations: All major entities (fields, equipment, tasks, etc.)
- Data Import/Export: CSV, Excel, PDF export functionality
- Climate/Weather: GDD tracking, precipitation, frost dates
- Sustainability: Carbon tracking, water usage, conservation practices
- Livestock: Animals, health records, breeding, weights, sales
- Financial: GenFin accounting, invoices, bills, payroll
- AI/ML: Yield prediction, pest identification, expense categorization
- Research: Field trials, statistical analysis, treatments

**Known Issues (7 tests, documented fixes):**
1. `test_animal_timeline` - API returns dict instead of list (test fix)
2. 5 sustainability tests - Backend returns infinity on division by zero (backend fix)
3. `test_yield_prediction_scenarios` - Missing SoilTestLevel import (backend fix)

**Verification Commands:**
```bash
# Run full test suite
pytest tests/ --tb=no -q

# Run specific test files
pytest tests/test_critical_paths.py -v
pytest tests/test_auth_security.py -v
```

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 6.14.0 | Jan 16, 2026 | Measurement converter for spray applications |
| 6.13.x | Jan 16, 2026 | FastAPI routers, Pydantic models, rate limiting, HTTPS, security |
| 6.12.x | Jan 15, 2026 | Comprehensive test suite (620+ tests), F# domain models, security audit |

For versions prior to v6.12.0, see `docs/CHANGELOG_ARCHIVE.md`.

---

## Key Files Reference

| Component | File | Lines |
|-----------|------|-------|
| GenFin Accounting | `frontend/ui/screens/genfin.py` | ~11,100 |
| Payroll Service | `backend/services/genfin_payroll_service.py` | ~2,000 |
| Main API | `backend/main.py` | ~2,500 |
| Critical Path Tests | `tests/test_critical_paths.py` | ~600 |

---

*For complete historical details, see `docs/CHANGELOG_ARCHIVE.md`*
