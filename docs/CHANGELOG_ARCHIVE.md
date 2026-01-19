# AgTools Changelog Archive

> Archived changelog entries for versions prior to v6.12.0 (before January 15, 2026).
> For current changelog, see `/CHANGELOG.md`.

---

## v6.11.0 (January 15, 2026)

### Critical Path Testing - 20 Core Tests (100% Pass Rate)

**Initial test infrastructure with critical path coverage.**

**New Test File:**
- `tests/test_critical_paths.py` - 20 essential tests

**Critical Tests:**
1. API health check
2. User registration
3. User login (JWT)
4. Token refresh
5. Create field
6. Get field details
7. Update field
8. Create equipment
9. Create task
10. Delete field (soft-delete)
11. Create operation
12. Update task
13. Get weather data
14. CSV data import
15. Generate report
16. Export to Excel
17. Concurrent request handling
18. Rate limiting behavior
19. Large dataset pagination
20. Data integrity validation

**Test Fixtures:**
- Enhanced `conftest.py` with shared fixtures
- `DataFactory` for generating test data
- Automatic cleanup of test entities

---

## v6.10.0 (January 15, 2026)

### Export Suite - Complete Report Export System

**Unified export functionality (CSV, Excel, PDF) for all report dashboards.**

**New Reusable Widget:**
- `frontend/ui/widgets/export_toolbar.py` - Dropdown button with CSV/Excel/PDF options
- Turquoise retro theme styling
- Signal-based architecture for export events
- File save dialog with format-specific filters

**New API Client:**
- `frontend/api/export_api.py` - Export API client
- Methods for all three dashboards
- Binary file download handling

**New Backend Endpoints:**
```
GET /api/v1/export/unified-dashboard/{format}
GET /api/v1/export/reports/{report_type}/{format}
GET /api/v1/export/crop-cost-analysis/{format}
```

**Dashboard Integrations:**

| Dashboard | Previous | Now |
|-----------|----------|-----|
| Advanced Reporting Dashboard | No export | CSV, Excel, PDF |
| Reports Dashboard | CSV only | CSV, Excel, PDF |
| Crop Cost Analysis | No export | CSV, Excel, PDF |

---

## v6.9.0 (January 12, 2026)

### Crop Cost Analysis Module

**Comprehensive crop cost analysis dashboard with per-acre tracking, yield comparisons, and ROI calculations across all fields and crops.**

**New Backend Service:**
- `backend/services/crop_cost_analysis_service.py` - Aggregation service for cost analysis

**New API Endpoints:**
- `GET /api/v1/crop-analysis/summary` - High-level KPIs
- `GET /api/v1/crop-analysis/comparison` - Field-by-field comparison matrix
- `GET /api/v1/crop-analysis/crops` - Crop type comparison
- `GET /api/v1/crop-analysis/crops/{crop_type}` - Detailed analysis for specific crop
- `GET /api/v1/crop-analysis/field/{field_id}/history` - Multi-year field history
- `GET /api/v1/crop-analysis/years` - Year-over-year comparison
- `GET /api/v1/crop-analysis/roi` - ROI breakdown
- `GET /api/v1/crop-analysis/trends` - Trend data for charting

**Dashboard Features (5 Tabs):**
- Overview, Field Comparison, Crop Comparison, Year over Year, ROI Analysis

---

## v6.8.1 (January 7, 2026)

### Bug Fixes & Comprehensive Testing

**Major endpoint fixes, route ordering corrections, and comprehensive workflow test suite achieving 95.2% pass rate.**

**Critical Bug Fixes:**
- Checkbox Visual Feedback
- Fertilizer Optimizer Field Mismatch
- Fertilizer Response Parsing
- Accounting Import Type Error

**Route Ordering Fixes (backend/main.py):**
- Fixed livestock route ordering conflicts

**Testing Infrastructure:**
- Improved pass rate from 53.4% to 87.8% (65/74 tests)
- 9 complete end-to-end workflows (95.2% pass rate)

---

## v6.8.0 (January 6, 2026)

### Advanced Reporting Dashboard

**New unified analytics dashboard combining farm operations and financial KPIs with full drill-down capabilities.**

**New Features:**
- 8 Key Performance Indicators
- Three Drill-Down Behaviors
- Interactive KPI Cards with mini charts
- Alert Banner, Date Range Picker, Auto-Refresh

**New Files:**
- `backend/services/unified_dashboard_service.py`
- `frontend/ui/screens/advanced_reporting_dashboard.py`
- `frontend/ui/widgets/kpi_card.py`
- `frontend/api/unified_dashboard_api.py`

---

## v6.7.17 (January 5, 2026)

### Documentation & CI Fixes

- Updated all documentation to v6.7.16
- Fixed CI/CD pipeline failures

---

## v6.7.16 (January 5, 2026)

### Receipt/Invoice OCR Feature

**Multi-provider OCR service with intelligent data extraction.**

**OCR Capabilities:**
- Tesseract (local), Google Vision API, AWS Textract
- Vendor detection, date parsing, amount extraction
- Line item extraction, image preprocessing

---

## v6.7.15 (January 5, 2026)

### pytest-bdd Workflow Testing Framework

**57 BDD scenarios passing with Gherkin syntax.**

**Documentation Reorganization:**
- `docs/grants/`, `docs/guides/`, `docs/development/`, `docs/testing/`

**Trademark Compliance Updates:**
- Renamed quickbooks_import.py to accounting_import.py
- Updated API endpoints and class names

---

## v6.7.14 (January 4, 2026)

### Test Suite Fixes - 100% Pass Rate Achieved

**Test Results: 226 passed, 7 skipped**

---

## v6.7.13 (January 4, 2026)

### API Route Ordering Fix

**217 passing (93% pass rate), 9 failing**

---

## v6.7.12 (January 4, 2026)

### Fixed Asset Depreciation Service Bug Fixes

**216 passing (93% pass rate)**

---

## v6.7.11 (January 4, 2026)

### Major GenFin Test Suite Improvements

**Test Results Improved: 57 failures to 14 failures (75% reduction)**

---

## v6.7.10 (January 3, 2026)

### Comprehensive GenFin Endpoint Test Suite

**234 individual test functions covering all 257 GenFin API endpoints**

---

## v6.7.9 (January 3, 2026)

### GenFin Payroll Bug Fixes

- Fixed 3 Internal Server Errors in Payroll Endpoints

---

## v6.7.8 (January 3, 2026)

### GenFin Comprehensive Test Suite Expansion

**Expanded test coverage from 54 to 121 tests**

---

## v6.7.7 (January 3, 2026)

### Farm Operations Workflow Test Suite

**97 comprehensive tests with 100% pass rate**

---

## v6.7.6 (December 31, 2025)

### Workflow Test Suite Expansion

**54 tests with 100% pass rate**

---

## v6.7.5 (December 31, 2025)

### Security Vulnerability Fixes

- DEV_MODE auth bypass fixed
- Hardcoded passwords removed
- CORS restrictive default

---

## v6.7.4 (December 31, 2025)

### Bill Edit Functionality

---

## v6.7.3 (December 30, 2025)

### Purchase Orders API & Comprehensive Testing

---

## v6.7.2 (December 30, 2025)

### Bug Fixes & API Compatibility

---

## v6.7.1 (December 30, 2025)

### Full QuickBooks Desktop Parity - Complete Transaction Workflow

- Pay Bills, Vendor Credits, Receive Payments
- Bank Reconciliation, Memorized Transactions
- Sales Orders with Deposits, Purchase Orders

---

## v6.7.0 (December 30, 2025)

### QuickBooks Desktop Parity - Write Checks

---

## v6.6.2 (December 30, 2025)

### GenFin API Robustness & CRUD Completeness

---

## v6.6.1 (December 30, 2025)

### GenFin Bug Fixes & Automated Testing

---

## v6.6.0 (December 30, 2025)

### Full QuickBooks Parity - Final Features

- Print Preview System
- Import/Export System
- Bank Feed Auto-Matching
- Batch Statement Generation

---

## v6.5.2 (December 30, 2025)

### Windows 98 Retro Theme - Turquoise Edition

---

## v6.5.1 (December 30, 2025)

### Company Switcher & Write Checks Improvements

---

## v6.5.0 (December 30, 2025)

### GenFin 100% Complete - Full QuickBooks Desktop Parity

**Major Milestone:** Zero placeholder screens remaining.

---

## v6.4.0 (December 29, 2025)

### Farm Operations Suite - Modules 1 & 2

- Module 1: Livestock Management
- Module 2: Seed & Planting

---

## v6.3.x (December 29, 2025)

### GenFin Advanced Features

- v6.3.1 - 90s QuickBooks UI
- v6.3.0 - Payroll, Multi-Entity, Budgets, 1099 Tracking

---

## Earlier Versions

For versions prior to v6.3.0, see git history.
