# AgTools Development Changelog

> **Purpose:** This file tracks the latest development updates for AgTools. Reference this file at the start of new chat sessions to understand recent changes and current system capabilities.

---

## Current Version: 2.8.0 (Released - December 26, 2025)

### Latest Session: December 26, 2025

#### v2.8.0 - Profitability Analysis & Input Optimization

**Status:** ✅ RELEASED

**Goal:** Build tools to maximize profitability and identify cost-cutting opportunities without sacrificing yield. Focus on turning a profit without relying on government subsidies.

**Phase 1: Profitability Service** - ✅ COMPLETE (December 26, 2025)
- Created `backend/services/profitability_service.py` (~950 lines)
- **Break-Even Calculator:**
  - Calculate break-even yield at any price
  - Calculate break-even price at any yield
  - Margin of safety analysis (yield cushion, price cushion)
  - Risk level assessment
  - Actionable recommendations
- **Input ROI Ranker:**
  - Rank all inputs by return on investment
  - Identify lowest ROI inputs to cut first
  - Cut risk assessment (low/medium/high yield impact)
  - Net benefit analysis (savings vs yield loss)
  - "What if I cut this?" projections
- **Scenario Planner:**
  - What-if analysis for price changes
  - What-if analysis for yield changes
  - What-if analysis for cost changes
  - Combined scenario matrix
  - Best case / worst case identification
  - Price and yield sensitivity analysis
  - Risk assessment across all scenarios
- **Budget Tracker:**
  - Set budget targets by category
  - Track actual vs budgeted spending
  - Category-level alerts (on track, warning, over budget, critical)
  - Projected profit calculation
  - Break-even status tracking
  - Recommendations for staying on budget

**Crop Support Added:**
- Corn (default)
- Soybeans
- **Rice** (new for Louisiana operations)
  - Default yield: 7,500 lbs/acre (75 cwt)
  - Pricing in $/cwt
  - Higher irrigation costs ($120/acre - flood irrigation)
  - Higher chemical costs ($95/acre)
  - Aerial application costs included
- Wheat
- Cotton
- Grain Sorghum

**Phase 2: API Endpoints** - ✅ COMPLETE (December 26, 2025)
- Added 7 new endpoints under `/api/v1/profitability/`:
  - `POST /api/v1/profitability/break-even` - Calculate break-even yields and prices
  - `POST /api/v1/profitability/input-roi` - Rank inputs by ROI, identify what to cut
  - `POST /api/v1/profitability/scenarios` - Run what-if scenario analysis
  - `POST /api/v1/profitability/budget` - Track budget vs actual spending
  - `GET /api/v1/profitability/summary/{crop}` - Quick profitability summary
  - `GET /api/v1/profitability/crops` - List supported crops with parameters
  - `GET /api/v1/profitability/input-categories` - List input cost categories
- Updated API version to 2.8.0
- All endpoints require authentication

**Phase 3: Testing** - ✅ COMPLETE (December 26, 2025)
- All service methods tested and working:
  - Break-even calculator: $565/acre costs, projects $122,500 profit on 500 acres corn
  - Input ROI ranker: Identifies fuel as top cut candidate
  - Scenario planner: Best case $276,400 to worst case -$55,700
  - Rice support: $740/acre cost (includes flood irrigation)
- Risk assessment working correctly

---

## Previous Version: 2.7.0 (Released - December 23, 2025)

### Latest Session: December 23, 2025

#### v2.7.0 - Cost Per Acre Tracking Module

**Status:** ✅ RELEASED

**What's Being Built:**
Cost-per-acre tracking module that imports expense data from QuickBooks (CSV or scanned reports) and calculates cost-per-acre by field and by crop. Supports split allocations where a single expense applies to multiple fields.

**Phase 1: Database Schema** - ✅ COMPLETE (December 23, 2025)
- Created `database/migrations/006_cost_tracking.sql`
- New tables:
  - `expense_categories` - Predefined categories (seed, fertilizer, chemical, fuel, repairs, labor, custom_hire, land_rent, crop_insurance, interest, utilities, storage, other)
  - `import_batches` - Track import sessions for audit/undo
  - `column_mappings` - Save user's CSV column mappings for reuse
  - `expenses` - Master expense records with OCR support fields
  - `expense_allocations` - Link expenses to fields with split percentages
- Views for reporting:
  - `v_cost_per_acre` - Cost per acre by field, year, and category
  - `v_unallocated_expenses` - Expenses needing allocation
- Triggers for auto-updating timestamps

**Phase 2: Cost Tracking Service** - ✅ COMPLETE (December 23, 2025)
- Created `backend/services/cost_tracking_service.py` (~900 lines)
- CSV Import with flexible column mapper:
  - Auto-detect column mappings from headers
  - Parse various date and amount formats
  - Auto-detect expense categories from vendor/description text
  - Duplicate detection by reference + date + amount
  - Import batch tracking for audit/undo
- Expense CRUD operations
- Allocation management (single + split across fields)
- Cost-per-acre reporting:
  - Report by field with category breakdown
  - Category breakdown with percentages
  - Cost by crop type summary
  - Year-over-year comparison
- Saved column mappings for reuse
- Rollback import functionality

**Phase 3: OCR Import** - ✅ COMPLETE (December 23, 2025)
- Added OCR processing to cost_tracking_service.py
- Features:
  - Process scanned images (JPG, PNG) and PDFs
  - Uses pytesseract for text extraction
  - Automatic amount and date parsing from OCR text
  - Vendor name extraction from text patterns
  - Category auto-detection from extracted text
  - Confidence scoring (flags low-confidence for review)
  - Review queue for OCR expenses needing verification
  - Approve/correct OCR expenses workflow
- Dependencies: pytesseract, Pillow, pdf2image (optional for PDFs)

**Phase 4: API Endpoints** - ✅ COMPLETE (December 23, 2025)
- Added 22 new endpoints to `backend/main.py` under `/api/v1/costs/`
- Import endpoints:
  - `POST /api/v1/costs/import/csv/preview` - Preview CSV and get mapping suggestions
  - `POST /api/v1/costs/import/csv` - Import CSV with column mapping
  - `POST /api/v1/costs/import/scan` - Import via OCR (image/PDF)
  - `GET /api/v1/costs/imports` - List import batches
  - `DELETE /api/v1/costs/imports/{id}` - Rollback import
- Column mapping endpoints:
  - `GET /api/v1/costs/mappings` - List saved mappings
  - `POST /api/v1/costs/mappings` - Save mapping
  - `DELETE /api/v1/costs/mappings/{id}` - Delete mapping
- Expense CRUD:
  - `GET /api/v1/costs/expenses` - List with filters
  - `POST /api/v1/costs/expenses` - Create manual expense
  - `GET /api/v1/costs/expenses/{id}` - Get with allocations
  - `PUT /api/v1/costs/expenses/{id}` - Update
  - `DELETE /api/v1/costs/expenses/{id}` - Delete (manager+)
- OCR review:
  - `GET /api/v1/costs/review` - Get review queue
  - `POST /api/v1/costs/expenses/{id}/approve` - Approve OCR expense
- Allocation endpoints:
  - `GET /api/v1/costs/expenses/{id}/allocations` - Get allocations
  - `POST /api/v1/costs/expenses/{id}/allocations` - Set allocations
  - `POST /api/v1/costs/allocations/suggest` - Suggest by acreage
  - `GET /api/v1/costs/unallocated` - List unallocated expenses
- Report endpoints:
  - `GET /api/v1/costs/reports/per-acre` - Cost per acre report
  - `GET /api/v1/costs/reports/by-category` - Category breakdown
  - `GET /api/v1/costs/reports/by-crop` - Cost by crop type
  - `POST /api/v1/costs/reports/comparison` - Year comparison
  - `GET /api/v1/costs/categories` - List expense categories

**Phase 5: Testing** - ✅ COMPLETE (December 23, 2025)
- All imports verified
- Cost tracking service creates successfully
- CSV preview and column mapping working
- 13 expense categories available
- main.py loads with 165 total routes (24 new cost tracking routes)
- All endpoints registered correctly

**v2.7.0 Status:** ✅ COMPLETE - Ready for use

---

## Previous Version: 2.6.0 (Released - December 22, 2025)

### Session: December 22, 2025

#### v2.6.0 - Phase 6: Mobile/Crew Interface - RELEASED

**Status:** ✅ RELEASED - All smoke tests passing (66/66 - 100%)

**Smoke Test Results:** See `tests/SMOKE_TEST_RESULTS_v26.md` for full report

**Bug Fixes (December 22, 2025):**
- Fixed mobile login authentication to use `user_service.authenticate()` instead of non-existent `auth_service.authenticate_user()`
- Fixed session cookie name in test script (`agtools_session` not `session`)

**What Was Built:**
Mobile-friendly web interface for crew members using FastAPI + Jinja2 templates.

**Phase 6.1 Files Created:** ✅ COMPLETE
- `database/migrations/005_mobile_crew.sql` - time_entries & task_photos tables
- `backend/mobile/__init__.py` - Mobile module init
- `backend/mobile/auth.py` - Cookie-based session authentication
- `backend/templates/base.html` - Base Jinja2 template (mobile-first)
- `backend/templates/login.html` - Mobile login page
- `backend/static/css/mobile.css` - Mobile-first responsive CSS (~400 lines)

**Phase 6.2 Files Created:** ✅ COMPLETE (December 20, 2025)
- `backend/mobile/routes.py` - Mobile web routes (~280 lines)
  - Login GET/POST routes with session cookie management
  - Logout route with cookie clearing
  - Task list route with filtering (status, priority)
  - Task detail route with permission checking
  - Task status update POST route
- `backend/templates/tasks/list.html` - Task list template
  - Summary cards (To Do, In Progress, Completed counts)
  - Filter dropdowns for status and priority
  - Task cards with priority/status badges
  - Overdue task highlighting
  - Empty state messaging
  - Pull-to-refresh functionality
- `backend/static/js/app.js` - Core mobile JavaScript
  - Offline detection and banner
  - Form double-submit prevention
  - Touch feedback enhancements
  - Toast notification utility

**Phase 6.2 Integration:**
- Updated `backend/mobile/__init__.py` - Export router and configure_templates
- Updated `backend/main.py` - Mount static files, configure templates, include mobile router

**Phase 6.3 Files Created:** ✅ COMPLETE (December 20, 2025)
- `backend/templates/tasks/detail.html` - Task detail template
  - Back navigation link
  - Task badges (priority, status, overdue)
  - Info cards (due date, assigned to, crew, created date)
  - Full description display
  - Quick action buttons for status changes (Start, Complete, Reopen)
  - Task metadata section (created by, updated, completed dates)
  - Confirmation dialogs for status changes

**Phase 6.4 Files Created:** ✅ COMPLETE (December 20, 2025)
- `backend/services/time_entry_service.py` - Time entry service (~480 lines)
  - TimeEntryCreate/Update/Response Pydantic models
  - TimeEntryType enum (work, travel, break)
  - CRUD operations for time entries
  - Task time summaries (total hours, by type, contributors)
  - User time summaries with date ranges
  - Ownership-based edit/delete permissions
- Updated `backend/mobile/routes.py` - Added time logging routes
  - POST /m/tasks/{id}/time - Log hours worked
  - POST /m/tasks/{id}/time/{entry_id}/delete - Delete entry
- Updated `backend/templates/tasks/detail.html` - Time logging UI
  - Time log form with hours, type, notes
  - Time entries list with user, date, notes
  - Total hours badge in section header
  - Delete button for own entries
- Updated `backend/static/css/mobile.css` - Time form/entry styles

**Phase 6.5 Files Created:** ✅ COMPLETE (December 20, 2025)
- `backend/services/photo_service.py` - Photo service (~400 lines)
  - PhotoResponse Pydantic model
  - File validation (extensions, size limits)
  - UUID-based filename generation
  - GPS coordinate storage
  - CRUD operations with ownership checking
  - Automatic uploads directory creation
- Updated `backend/mobile/routes.py` - Added photo routes
  - POST /m/tasks/{id}/photo - Upload photo with GPS
  - POST /m/tasks/{id}/photo/{photo_id}/delete - Delete photo
  - GET /m/uploads/photos/{filename} - Serve photo files
- Updated `backend/templates/tasks/detail.html` - Photo UI
  - Camera/upload button with GPS capture
  - Caption input field
  - Responsive photo gallery (2-3 columns)
  - Photo delete button for owner
  - File size validation (10MB max)
- Updated `backend/static/css/mobile.css` - Photo form/gallery styles

**Phase 6.6 Files Created:** ✅ COMPLETE (December 20, 2025)
- `backend/static/manifest.json` - PWA web app manifest
  - App name, icons, theme color, display mode
  - Start URL and scope for mobile routes
- `backend/static/js/sw.js` - Service worker (~170 lines)
  - Cache-first strategy for static assets
  - Network-first with offline fallback for pages
  - Automatic cache cleanup on version update
  - Background sync ready architecture
- `backend/templates/offline.html` - Offline fallback page
  - Friendly offline message with icon
  - Retry button
  - Auto-reload when back online
  - Tips for users while offline
- Updated `backend/mobile/routes.py` - Added offline route
- Updated `backend/templates/base.html` - Service worker registration
- Created `backend/static/icons/` directory for PWA icons

**New Database Tables:**
- `time_entries` - Track hours worked on tasks
- `task_photos` - Store photo attachments with GPS

**Remaining TODO:**

| Phase | Task | Status |
|-------|------|--------|
| 6.2 | Create `backend/mobile/routes.py` with login/logout/task list routes | ✅ done |
| 6.2 | Integrate mobile routes into `backend/main.py` | ✅ done |
| 6.2 | Create `backend/templates/tasks/list.html` | ✅ done |
| 6.3 | Create `backend/templates/tasks/detail.html` | ✅ done |
| 6.3 | Add status update routes to routes.py | ✅ done |
| 6.4 | Create `backend/services/time_entry_service.py` | ✅ done |
| 6.4 | Add time logging routes and API endpoints | ✅ done |
| 6.5 | Create `backend/services/photo_service.py` | ✅ done |
| 6.5 | Create `backend/uploads/` directory for photos | ✅ done |
| 6.6 | Create `backend/static/js/sw.js` (service worker) | ✅ done |
| 6.6 | Create `backend/static/manifest.json` (PWA) | ✅ done |
| 6.6 | Create `backend/templates/offline.html` | ✅ done |

**Web Routes (planned):**
- `/m/login` - Mobile login (GET/POST)
- `/m/logout` - Clear session, redirect
- `/m/tasks` - Task list (my assigned tasks)
- `/m/tasks/{id}` - Task detail with actions
- `/m/tasks/{id}/status` - One-tap status update (POST)
- `/m/tasks/{id}/time` - Log time entry (POST)
- `/m/tasks/{id}/photo` - Upload photo (POST)

---

## Previous Version: 2.5.0 (Released - December 19, 2025)

### Session: December 19, 2025

#### Documentation Updates - v2.5.0 Complete

All documentation updated to reflect v2.5.0 Farm Operations Manager completion:

**FARM_OPS_MANAGER_PLAN.md:**
- Status updated to "✅ COMPLETE - All 5 Phases Implemented"
- Phase 5 marked complete with "What Was Built" section
- Added December 19 changelog entry

**QUICKSTART.md:**
- Added Equipment Management, Inventory Tracking, Maintenance Scheduling, Reports & Analytics sections
- Added 4 new features (#14-17) to "What This System Does" list
- Fixed JD Integration reference to v2.6 (pending account approval)

**README.md:**
- Added reporting_service.py, reports_api.py, reports_dashboard.py to architecture
- Added Reports & Analytics API endpoints section (7 endpoints)
- Updated endpoint count to 123
- Fixed JD Integration to v2.6

---

### Previous Session: December 19, 2025

#### Smoke Test Results - 100% Pass Rate

**Test Date:** December 19, 2025

| Metric | Value |
|--------|-------|
| Total Tests | 65 |
| Passed | 65 |
| Failed | 0 |
| **Pass Rate** | **100.0%** |

**Categories Tested:**
- Root, Auth, Users, Crews, Tasks: ✅ All Pass
- Fields, Operations, Pricing: ✅ All Pass
- Yield Response, Spray Timing, Cost Optimizer: ✅ All Pass
- Pest/Disease Identification: ✅ All Pass
- Equipment Management (Phase 4): ✅ 3/3 Pass
- Inventory Management (Phase 4): ✅ 3/3 Pass
- **Reports & Analytics (Phase 5): ✅ 7/7 Pass**
- API Documentation: ✅ 101 endpoints documented
- Frontend Imports: ✅ 31/31 modules import correctly

**Bugs Fixed:**
- Fixed `low_stock_count` NULL bug in dashboard summary (COALESCE wrapper)
- Updated smoke test for inventory alerts list response format

See `tests/SMOKE_TEST_RESULTS_v2.5.0_Phase5.md` for detailed results.

---

### Previous Session: December 18, 2025

#### v2.5.0 - Phase 5: Reporting & Analytics Dashboard ✅ COMPLETE

**Status:** ✅ Phase 1 (Auth) | ✅ Phase 2 (Tasks) | ✅ Phase 3 (Fields & Ops) | ✅ Phase 4 (Equipment & Inventory) | ✅ Phase 5 (Reports) COMPLETE

**What Was Built:**

1. **Reporting Service** ✅ COMPLETE
   - Backend service aggregating data from all other services
   - Operations reports with date range filtering
   - Financial reports with cost breakdown by category
   - Equipment utilization reports with maintenance summaries
   - Inventory status reports with alerts
   - Field performance reports with yield comparisons
   - CSV export for all report types

2. **Reports API Endpoints** ✅ COMPLETE
   - `GET /api/v1/reports/operations` - Operations report
   - `GET /api/v1/reports/financial` - Financial summary
   - `GET /api/v1/reports/equipment` - Equipment utilization
   - `GET /api/v1/reports/inventory` - Inventory status
   - `GET /api/v1/reports/fields` - Field performance
   - `GET /api/v1/reports/dashboard` - Combined summary
   - `POST /api/v1/reports/export/csv` - Export to CSV

3. **Reports Dashboard UI** ✅ COMPLETE
   - 4-tab interface with date range filtering
   - Tab 1: Operations Overview - summary cards, bar charts, operations table
   - Tab 2: Financial Analysis - cost/revenue cards, cost breakdown, profit by field
   - Tab 3: Equipment & Inventory - fleet stats, utilization charts, alerts tables
   - Tab 4: Field Performance - yield cards, field comparison chart, summary table
   - CSV export functionality with save dialog

**Files Created:**
- `backend/services/reporting_service.py` (~850 lines)
- `frontend/api/reports_api.py` (~450 lines)
- `frontend/ui/screens/reports_dashboard.py` (~800 lines)

**Files Modified:**
- `backend/main.py` - Added 7 reporting endpoints
- `frontend/api/__init__.py` - Added ReportsAPI exports
- `frontend/ui/screens/__init__.py` - Added ReportsDashboardScreen export
- `frontend/ui/sidebar.py` - Added Analytics section with Reports nav
- `frontend/ui/main_window.py` - Integrated ReportsDashboardScreen

**New Sidebar Navigation:**
```
Analytics Section:
└── Reports (reports & analytics dashboard)
```

---

#### v2.5.0 - Phase 4: Equipment & Inventory Tracking ✅ COMPLETE

**Status:** ✅ Phase 1 (Auth) | ✅ Phase 2 (Tasks) | ✅ Phase 3 (Fields & Ops) | ✅ Phase 4 (Equipment & Inventory) COMPLETE

**What Was Built:**

1. **Equipment Fleet Management** ✅ COMPLETE
   - Track all equipment: tractors, combines, sprayers, planters, tillage, trucks, ATVs, grain carts
   - Equipment registry with make, model, year, serial number, purchase info
   - Hour meter tracking and usage logging
   - Status tracking: available, in_use, maintenance, retired
   - Hourly operating cost tracking
   - Full CRUD UI with summary cards, filters, and table view

2. **Maintenance Scheduling** ✅ COMPLETE
   - Service history logging with maintenance type, cost, vendor, parts
   - Schedule next service by date or hours
   - Maintenance alerts for upcoming/overdue service (urgency-based cards)
   - Alerts view: overdue (red), due soon (orange), upcoming (blue)
   - History table with equipment, type, and date range filters

3. **Inventory Management** ✅ COMPLETE
   - Track all inputs: seed, fertilizer, chemicals, fuel, parts, supplies
   - Quantity and unit tracking with reorder points (low stock alerts)
   - Storage location and batch/lot numbers
   - Expiration date tracking for chemicals (expiring soon alerts)
   - Cost per unit and total value tracking
   - Quick purchase and quantity adjustment dialogs

4. **Inventory Transactions** ✅ COMPLETE
   - Purchase recording with vendor and invoice tracking
   - Usage tracking linked to field operations
   - Inventory adjustments with reason tracking
   - Transaction history per item

5. **Operations Integration** ✅ COMPLETE
   - Equipment selection when logging operations
   - Hours used tracking per operation
   - Inventory item selection for products
   - Auto-populate product name and unit from inventory

**Files Created/Modified:**

**Backend (Previous Session):**
- `database/migrations/004_equipment_inventory.sql` ✅ (5 tables + field_operations mod)
- `backend/services/equipment_service.py` (~700 lines) ✅
- `backend/services/inventory_service.py` (~650 lines) ✅
- `backend/main.py` - 24 new API endpoints ✅

**Frontend API Clients:**
- `frontend/api/equipment_api.py` (~500 lines) ✅
- `frontend/api/inventory_api.py` (~600 lines) ✅ NEW
- `frontend/api/__init__.py` - Updated exports ✅

**Frontend UI Screens:**
- `frontend/ui/screens/equipment_management.py` (~1040 lines) ✅ NEW
  - CreateEquipmentDialog, EditEquipmentDialog
  - UpdateHoursDialog, LogMaintenanceDialog
  - Equipment table with type/status filtering
  - Summary cards: total equipment, fleet value, hours, in maintenance
- `frontend/ui/screens/inventory_management.py` (~1100 lines) ✅ NEW
  - CreateItemDialog, EditItemDialog
  - QuickPurchaseDialog, AdjustQuantityDialog
  - Inventory table with category/location filtering
  - Summary cards: total items, value, low stock, expiring
- `frontend/ui/screens/maintenance_schedule.py` (~560 lines) ✅ NEW
  - MaintenanceAlertCard with urgency-based styling
  - Alerts tab with scrollable card grid
  - History tab with equipment/type filters
  - Summary cards: overdue, due soon, upcoming, total equipment

**Navigation Integration:**
- `frontend/ui/screens/__init__.py` - Added new screen exports ✅
- `frontend/ui/sidebar.py` - Added Equipment section nav ✅
- `frontend/ui/main_window.py` - Integrated new screens ✅

**Operations Log Enhancement:**
- `frontend/ui/screens/operations_log.py` - Equipment & inventory integration ✅
  - Equipment selection with hours used tracking
  - Inventory item selection for product tracking
  - Auto-populate product name/unit from inventory

**New Sidebar Navigation:**
```
Equipment Section:
├── Equipment (fleet management)
├── Inventory (inputs tracking)
└── Maintenance (schedule & alerts)
```

**API Endpoints (24 total):**
- Equipment: 8 endpoints (CRUD + hours + types + summary)
- Maintenance: 4 endpoints (CRUD + alerts + history)
- Inventory: 8 endpoints (CRUD + summary + categories + alerts)
- Transactions: 4 endpoints (record + history + purchase + adjust)

---

### Previous Session: December 17, 2025

#### v2.5.0 - Phase 4: Equipment & Inventory Backend Complete

**Status:** ✅ Phase 1 (Auth) | ✅ Phase 2 (Tasks) | ✅ Phase 3 (Fields & Ops) | 🔄 Phase 4 Backend COMPLETE

**What Was Done:**
- Database migration for equipment and inventory tables
- Backend services for equipment and inventory management
- 24 new API endpoints
- Frontend equipment API client

**Files Created:**
- `database/migrations/004_equipment_inventory.sql`
- `backend/services/equipment_service.py`
- `backend/services/inventory_service.py`
- `frontend/api/equipment_api.py`

---

### Previous Session: December 16, 2025

#### v2.5.0 - Smoke Tests & Bug Fixes

**Status:** ✅ Phase 1 (Auth) | ✅ Phase 2 (Tasks) | ✅ Phase 3 (Fields & Operations) COMPLETE

**What Was Done:**

1. **Comprehensive Smoke Tests** ✅ COMPLETE
   - Created `tests/smoke_test_v25.py` - Full API test suite
   - Created `tests/SMOKE_TEST_RESULTS_v2.5.0.md` - Detailed test report
   - **Results:** 96.6% overall pass rate (56/58 tests)
     - Backend API: 95.2% (20/21)
     - Frontend Imports: 95.5% (21/22)
     - Frontend UI Screens: 100% (15/15)

2. **Critical Bug Fix: JWT Token Validation** ✅ FIXED
   - **Issue:** Tokens generated on login were immediately rejected as "Invalid or expired token"
   - **Root Cause:** Import path mismatch caused different SECRET_KEYs
     - `main.py` used: `from services.auth_service import ...`
     - `middleware/auth_middleware.py` used: `from backend.services.auth_service import ...`
   - **Fix:** Standardized import paths in `backend/middleware/auth_middleware.py`
   - **Impact:** All authenticated endpoints now work correctly

3. **Bug Fix: F-String Syntax Errors** ✅ FIXED
   - **File:** `frontend/ui/screens/operations_log.py`
   - **Issue:** Malformed f-strings causing import failures
   - **Lines Fixed:** 729, 730, 738, 744, 745, 746

4. **Files Modified:**
   - `backend/middleware/auth_middleware.py` - Fixed import paths
   - `frontend/ui/screens/operations_log.py` - Fixed f-string syntax
   - `tests/smoke_test_v25.py` - NEW: Comprehensive test suite
   - `tests/SMOKE_TEST_RESULTS_v2.5.0.md` - NEW: Test report

5. **Known Issue (Non-blocking):**
   - GET /fields returns 500 on fresh database (migration not run)
   - **Resolution:** Run `database/migrations/003_field_operations.sql`

---

### Previous Session: December 15, 2025

#### v2.5.0 - Farm Operations Manager: Phase 3 Complete

**Status:** ✅ Phase 1 (Auth) | ✅ Phase 2 (Tasks) | ✅ Phase 3 (Fields & Operations) COMPLETE

**What Was Built:**

1. **Field Management System** ✅ COMPLETE
   - Full CRUD operations for farm fields
   - Field attributes: name, farm grouping, acreage, crop, soil type, irrigation
   - GPS coordinate support (lat/lng)
   - GeoJSON boundary support for precision agriculture
   - Operation statistics per field
   - Summary dashboard with total fields/acres by crop/farm

2. **Operations Logging System** ✅ COMPLETE
   - Log all field operations: spray, fertilizer, planting, harvest, tillage, scouting, irrigation
   - Product tracking with rates and quantities
   - Cost tracking (product cost, application cost, total)
   - Harvest-specific fields (yield, moisture)
   - Weather conditions recording (temp, wind, humidity)
   - Operation history per field
   - Summary statistics with cost breakdowns

3. **Backend Changes:**
   - **New Files:**
     - `backend/services/field_service.py` (~450 lines) - Field CRUD with enums
     - `backend/services/field_operations_service.py` (~550 lines) - Operations logging
     - `database/migrations/003_field_operations.sql` - Fields & operations tables
   - **Modified:**
     - `backend/main.py` - Added 14 new endpoints (92 total routes now)

4. **Frontend Changes:**
   - **New Files:**
     - `frontend/api/field_api.py` (~290 lines) - Field API client
     - `frontend/api/operations_api.py` (~380 lines) - Operations API client
     - `frontend/ui/screens/field_management.py` (~500 lines) - Field management screen
     - `frontend/ui/screens/operations_log.py` (~550 lines) - Operations log screen
   - **Modified:**
     - `frontend/ui/main_window.py` - Added new screens
     - `frontend/ui/sidebar.py` - Added "Operations > Fields" and "Operations > Operations" nav
     - `frontend/api/__init__.py` - New API exports

5. **New API Endpoints (14 total):**
   ```
   Field Management:
     GET    /api/v1/fields              - List fields (with filters)
     POST   /api/v1/fields              - Create field
     GET    /api/v1/fields/summary      - Field statistics
     GET    /api/v1/fields/farms        - List farm names
     GET    /api/v1/fields/{id}         - Get field details
     PUT    /api/v1/fields/{id}         - Update field
     DELETE /api/v1/fields/{id}         - Delete field (manager+)

   Operations Log:
     GET    /api/v1/operations              - List operations
     POST   /api/v1/operations              - Create operation
     GET    /api/v1/operations/summary      - Operations statistics
     GET    /api/v1/operations/{id}         - Get operation details
     PUT    /api/v1/operations/{id}         - Update operation
     DELETE /api/v1/operations/{id}         - Delete operation (manager+)
     GET    /api/v1/fields/{id}/operations  - Field operation history
   ```

6. **Database Schema:**
   - `fields` table: id, name, farm_name, acreage, current_crop, soil_type, irrigation_type, location_lat, location_lng, boundary (GeoJSON), notes
   - `field_operations` table: id, field_id, operation_type, operation_date, product_name, rate, rate_unit, quantity, quantity_unit, acres_covered, costs, yield data, weather, operator_id, task_id link

7. **UI Features:**
   - **Field Management:**
     - Summary cards (total fields, total acres, crops)
     - Filter by farm, crop, search
     - Create/Edit dialogs with dropdowns for crop/soil/irrigation
     - Color-coded crop badges
     - View history button linking to operations
     - Delete for managers/admins
   - **Operations Log:**
     - Summary cards (total operations, total cost, breakdown by type)
     - Filter by field, operation type, date range
     - Log operation dialog with dynamic fields (harvest shows yield/moisture)
     - Cost tracking fields
     - Weather condition recording
     - Color-coded operation type badges
     - View details, delete for managers

**Total New Code:** ~2,700 lines

---

### Previous Session: December 12, 2025

#### v2.5.0 - Farm Operations Manager: Phase 2 Complete

**Status:** ✅ Phase 1 (Auth) COMPLETE | ✅ Phase 2 (Tasks) COMPLETE

**What Was Built:**

1. **Task Management Core** ✅ COMPLETE
   - Full CRUD operations for tasks
   - Role-based access control (admin sees all, manager sees crew tasks, crew sees own)
   - Status workflow: todo → in_progress → completed/cancelled
   - Priority levels: low, medium, high, urgent
   - Assignment to users or crews
   - Due date tracking with overdue detection

2. **Backend Changes:**
   - **New Files:**
     - `backend/services/task_service.py` (~500 lines) - Task service with CRUD
     - `database/migrations/002_task_management.sql` - Tasks table
   - **Modified:**
     - `backend/main.py` - Added 6 task endpoints (78 total routes)

3. **Frontend Changes:**
   - **New Files:**
     - `frontend/api/task_api.py` (~270 lines) - Task API client
     - `frontend/ui/screens/task_management.py` (~520 lines) - Task screen
   - **Modified:**
     - `frontend/ui/main_window.py` - Added TaskManagementScreen
     - `frontend/ui/sidebar.py` - Added "Operations > Tasks" nav, v2.5.0
     - `frontend/api/__init__.py` - Task API exports
     - `frontend/ui/screens/__init__.py` - Screen exports

4. **New API Endpoints (6 total):**
   ```
   Task Management:
     GET    /api/v1/tasks              - List tasks (filtered by role)
     POST   /api/v1/tasks              - Create task
     GET    /api/v1/tasks/{id}         - Get task details
     PUT    /api/v1/tasks/{id}         - Update task
     DELETE /api/v1/tasks/{id}         - Delete task (manager+)
     POST   /api/v1/tasks/{id}/status  - Change task status
   ```

5. **UI Features:**
   - Task list table with color-coded status/priority badges
   - Create/Edit dialogs with user/crew assignment dropdowns
   - Date picker for due dates
   - Filter by: status, priority, "My Tasks" toggle
   - Quick status buttons (Start, Complete)
   - Overdue task highlighting (red text)
   - Delete button for managers/admins only

**Total New Code:** ~1,300 lines

---

### Previous Session: December 11, 2025 @ Evening

#### v2.5.0 - Farm Operations Manager: Phase 1 Complete

**Status:** ✅ Phase 1 (User & Auth System) COMPLETE

**What Was Built:**

1. **Multi-User Authentication System** ✅ COMPLETE
   - JWT-based authentication with 24-hour access tokens
   - Bcrypt password hashing (secure, Python 3.13 compatible)
   - Role-based access control (admin, manager, crew)
   - Session management with token storage
   - Audit logging for security events

2. **User Management** ✅ COMPLETE
   - Create, edit, deactivate users (admin only)
   - User listing with role and status filters
   - Password management (change own password)
   - Profile updates

3. **Crew/Team Management** ✅ COMPLETE
   - Create and manage crews/teams
   - Assign managers to crews
   - Add/remove crew members
   - View crew membership

4. **Backend Changes:**
   - **New Files:**
     - `backend/services/auth_service.py` (~350 lines)
     - `backend/services/user_service.py` (~1050 lines)
     - `backend/middleware/auth_middleware.py` (~170 lines)
     - `database/migrations/001_auth_system.sql`
   - **Modified:**
     - `backend/main.py` - Added 17 new endpoints
     - `backend/requirements.txt` - Added auth dependencies

5. **Frontend Changes:**
   - **New Files:**
     - `frontend/ui/screens/login.py` (~280 lines) - Login screen
     - `frontend/ui/screens/user_management.py` (~400 lines) - Admin user mgmt
     - `frontend/ui/screens/crew_management.py` (~420 lines) - Crew mgmt
     - `frontend/api/auth_api.py` (~220 lines)
     - `frontend/api/user_api.py` (~140 lines)
     - `frontend/api/crew_api.py` (~170 lines)
   - **Modified:**
     - `frontend/app.py` - Login flow integration
     - `frontend/main.py` - Uses new start() method
     - `frontend/ui/main_window.py` - User menu, logout, admin screens
     - `frontend/api/client.py` - Auth token support
     - `frontend/api/__init__.py` - New exports
     - `frontend/ui/screens/__init__.py` - New screen exports

**New API Endpoints (17 total):**
```
Authentication:
  POST /api/v1/auth/login          - Login and get tokens
  POST /api/v1/auth/logout         - Logout and invalidate session
  POST /api/v1/auth/refresh        - Refresh access token
  GET  /api/v1/auth/me             - Get current user info
  PUT  /api/v1/auth/me             - Update own profile
  POST /api/v1/auth/change-password - Change own password

User Management (admin/manager):
  GET  /api/v1/users               - List users with filters
  POST /api/v1/users               - Create user (admin)
  GET  /api/v1/users/{id}          - Get user details
  PUT  /api/v1/users/{id}          - Update user (admin)
  DELETE /api/v1/users/{id}        - Deactivate user (admin)

Crew Management:
  GET  /api/v1/crews               - List crews
  POST /api/v1/crews               - Create crew (admin)
  GET  /api/v1/crews/{id}          - Get crew details
  PUT  /api/v1/crews/{id}          - Update crew (admin)
  GET  /api/v1/crews/{id}/members  - Get crew members
  POST /api/v1/crews/{id}/members/{user_id} - Add member
  DELETE /api/v1/crews/{id}/members/{user_id} - Remove member
  GET  /api/v1/users/{id}/crews    - Get user's crews
```

**Default Admin Account:**
- Username: `admin`
- Password: `admin123`
- **IMPORTANT:** Change this password immediately after first login!

**To Test:**
```bash
# Start backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Start frontend (in another terminal)
cd frontend
python main.py
# Login with admin / admin123
```

**Next Up: Phase 2 - Task Management Core**
- Projects and task creation
- Task assignments and dependencies
- Status workflows
- Time tracking

---

### Previous Session: December 11, 2025 @ 12:30 PM CST

#### Pivoted from John Deere Integration to Farm Operations Manager

**Reason:** John Deere Developer Account requires business application/approval process

**Overview:** Import field data, yield maps, and application history from John Deere Operations Center API to eliminate manual data entry and enable precision zone-based recommendations.

**Implementation Phases:**

1. **Phase 1: JD API Client & Authentication** (4-6 hours)
   - Create `backend/services/john_deere_service.py` - OAuth 2.0 client
   - Token management with secure storage
   - Connection testing and error handling
   - Add JD tab to Settings screen for auth configuration

2. **Phase 2: Field Boundary Sync** (4-6 hours)
   - Import field boundaries (GeoJSON) from JD Ops Center
   - Auto-populate farm/field hierarchy
   - Add `jd_field_id`, `jd_org_id`, `last_jd_sync` columns to database
   - Sync status indicators in UI

3. **Phase 3: Yield/Harvest Data Import** (8-10 hours)
   - Import historical yield maps from harvest operations
   - Create `harvest_data` table with zone-level yields
   - Calibrate yield response models with actual field outcomes
   - Enable variable rate recommendations by yield zone

4. **Phase 4: Application History Tracking** (6-8 hours)
   - Import spray/fertilizer application records
   - Link to AgTools recommendations for ROI validation
   - Compliance audit trail (products, rates, dates, areas)
   - Resistance management verification

**Key JD API Endpoints:**
- `GET /organizations/{id}/fields` - Farm/field hierarchy
- `GET /fields/{id}/boundaries` - Field geometry (GeoJSON)
- `GET /fields/{id}/operations` - Applications, harvest, tillage
- Equipment APIs for machine hours and efficiency

**Database Changes Required:**
- Add to `fields` table: `jd_field_id`, `jd_org_id`, `last_jd_sync`
- New table: `harvest_data` (field_id, zone_geometry, yield, moisture, harvest_date)
- New table: `application_history` (field_id, jd_operation_id, product, rate, date, area)
- New table: `jd_auth_tokens` (user_id, access_token, refresh_token, expires_at)

**Value Delivered:**
- Eliminate manual field/boundary entry
- Real historical yield data for model calibration
- Zone-specific recommendations (vs field-average)
- Application compliance audit trail
- ROI validation (recommended vs actual outcomes)

**Prerequisites:**
- John Deere Developer Account (https://developer.deere.com)
- API credentials (client_id, client_secret)
- User connects their JD Ops Center account via OAuth

---

### Previous Session: December 11, 2025 @ 8:05 AM CST

#### Features Completed That Session

1. **PyQt6 Frontend - Phase 9: Polish & Testing** ✅ COMPLETE
   - **New Files Created:**
     - `frontend/ui/screens/settings.py` (~500 lines) - Full settings screen with tabs
     - `frontend/ui/widgets/common.py` (~400 lines) - Reusable UI components
     - `frontend/tests/test_phase9.py` (~130 lines) - Integration tests

   - **Settings Screen (`settings.py`):**
     - **General Tab:**
       - Region selection (7 agricultural regions)
       - Default crop preference
       - Theme selection (Light/Dark)
       - Sidebar width configuration
       - Offline mode settings (enable/disable, cache TTL)
       - Sync on startup option
       - Auto-fallback to offline option
     - **Connection Tab:**
       - API server URL configuration
       - Timeout settings
       - Test Connection button with live feedback
       - Connection status display with refresh
     - **Data Tab:**
       - Local cache statistics (entries, products, pests, etc.)
       - Cache management (clear expired, clear all, optimize)
       - Data export to CSV (calculation history, product prices)
       - Database file size display
     - **About Tab:**
       - Application branding and version
       - Feature list
       - Data directory paths

   - **Common Widgets (`widgets/common.py`):**
     - `LoadingOverlay` - Semi-transparent overlay with progress spinner
     - `LoadingButton` - Button with loading state management
     - `StatusMessage` - Inline success/error/warning/info messages
     - `ValidatedLineEdit` - Input field with validation feedback
     - `ValidatedSpinBox` - Spin box with warning range highlighting
     - `ConfirmDialog` - Customizable confirmation dialogs
     - `ToastNotification` - Auto-hiding toast notifications

   - **Integration Tests:**
     - Settings screen import test
     - Common widgets import test
     - All screens import verification (8 screens)
     - Offline integration test (database, calculators)
     - API client offline methods test
     - Config and settings test
     - **Results:** 6/6 tests passed

   - **Files Modified:**
     - `frontend/ui/screens/__init__.py` - Added SettingsScreen export
     - `frontend/ui/widgets/__init__.py` - Added common widget exports
     - `frontend/ui/main_window.py` - Integrated SettingsScreen
     - `frontend/config.py` - Version bump to 2.4.0

   - **To Test:**
     ```bash
     cd frontend
     python tests/test_phase9.py  # Run integration tests
     python main.py               # Launch app, click Settings in sidebar
     ```

---

2. **PyQt6 Frontend - Phase 8: Offline Mode & Local Database** ✅ COMPLETE
   - **New Files Created:**
     - `frontend/database/local_db.py` (~550 lines) - SQLite database for offline caching
     - `frontend/core/sync_manager.py` (~450 lines) - Online/offline detection and sync
     - `frontend/core/calculations/yield_response.py` (~450 lines) - Offline EOR calculator
     - `frontend/core/calculations/spray_timing.py` (~400 lines) - Offline spray evaluator

   - **SQLite Local Database (`local_db.py`):**
     - Thread-safe connection management
     - Automatic schema initialization and migrations
     - Tables: cache, products, custom_prices, pests, diseases, crop_parameters, calculation_history, sync_queue
     - Cache with TTL expiration
     - Sync queue for offline changes
     - Full CRUD operations for products, pests, diseases

   - **Sync Manager (`sync_manager.py`):**
     - Qt signals for connection state changes
     - Periodic connection monitoring (30s intervals)
     - Automatic sync when coming online
     - Push pending changes to server
     - Pull fresh data from server (prices, pests, diseases, crop parameters)
     - Conflict resolution (server wins)
     - Background sync threading

   - **Offline Yield Calculator:**
     - Full EOR (Economic Optimum Rate) calculation
     - 5 response models (quadratic plateau, quadratic, linear plateau, Mitscherlich, square root)
     - Crop parameters for corn, soybean, wheat
     - Soil test level adjustments
     - Previous crop N credits
     - Price ratio guide generation
     - Yield curve generation

   - **Offline Spray Calculator:**
     - Delta T calculation (inversion risk)
     - Multi-factor condition assessment (wind, temp, humidity, rain, Delta T)
     - Risk level determination (excellent to do-not-spray)
     - Cost of waiting economic analysis
     - Spray type-specific thresholds

   - **API Client Updates (`client.py`):**
     - Added `get_with_cache()` - GET with cache fallback
     - Added `post_with_cache()` - POST with cache fallback
     - Added `post_with_offline_calc()` - POST with offline calculator fallback
     - Added `queue_for_sync()` - Queue offline changes
     - `from_cache` attribute on APIResponse

   - **UI Updates (`main_window.py`):**
     - New `SyncStatusWidget` with sync button and pending count
     - Sync button in top bar
     - "X pending" indicator for offline changes
     - Last sync time in status bar
     - Sync progress in status bar
     - Connection state integration with SyncManager

   - **Files Modified:**
     - `frontend/database/__init__.py` - Added LocalDatabase exports
     - `frontend/core/__init__.py` - Added SyncManager exports
     - `frontend/core/calculations/__init__.py` - Added offline calculator exports

   - **Capabilities:**
     - Work completely offline with cached data
     - Queue price updates while offline
     - Calculate EOR and spray timing without server
     - Automatic sync when reconnected
     - Visual indicators for offline status

   - **To Test:**
     ```bash
     cd frontend
     python main.py
     # Disconnect from network
     # Use Yield Calculator - works with offline engine
     # Use Spray Timing - works with offline engine
     # Add custom price - queued for sync
     # Reconnect - click Sync button to sync pending changes
     ```

---

### Previous Session: December 9, 2025 @ 8:30 PM CST

#### Bug Fixes Completed This Session

1. **Fixed Critical Yield Response Optimizer Infinite Recursion Bug** ✅ CRITICAL FIX
   - **Issue:** `calculate_economic_optimum()` called `_calculate_sensitivity()` which recursively called `calculate_economic_optimum()` again, causing infinite recursion and server crashes
   - **Solution:** Added `_skip_sensitivity` parameter to prevent recursive sensitivity calculations
   - **File Modified:** `backend/services/yield_response_optimizer.py`
   - **Impact:** All yield-response API endpoints now work correctly

2. **Added Missing Yield Response Optimizer Methods** ✅ COMPLETE
   - Added `get_crop_parameters(crop)` method - returns agronomic parameters for a crop
   - Added `generate_price_ratio_guide(crop, nutrient)` method - generates EOR lookup table
   - **Endpoints now functional:**
     - `GET /api/v1/yield-response/crop-parameters/{crop}`
     - `GET /api/v1/yield-response/price-ratio-guide`

#### Smoke Tests Completed This Session ✅ ALL PASSED

1. **Backend API Tests:**
   - Root endpoint (`/`) - OK
   - Pricing API (`/api/v1/pricing/prices`) - OK (56 products)
   - Yield Response economic-optimum - OK (EOR: 170.5 lb/acre for corn N)
   - Yield Response crop-parameters - OK (corn: N, P, K, S parameters)
   - Yield Response price-ratio-guide - OK (9 price ratio scenarios)
   - Spray Timing growth-stage-timing - OK
   - Cost Optimizer quick-estimate - OK
   - Pest Identification - OK (European Corn Borer, Fall Armyworm)

2. **Frontend Tests:**
   - All UI screens import successfully
   - MainWindow creates without errors
   - All API client modules load correctly
   - All model modules load correctly
   - All screen classes instantiate properly

---

### Previous Session: December 9, 2025 @ 5:30 PM CST

#### Features Completed That Session

1. **PyQt6 Frontend - Phase 7: Pest/Disease Identification Screens** ✅ COMPLETE
   - **New Files Created:**
     - `frontend/models/identification.py` (~250 lines) - Data models for pest/disease
     - `frontend/api/identification_api.py` (~130 lines) - API client
     - `frontend/ui/screens/pest_identification.py` (~380 lines) - Pest ID screen
     - `frontend/ui/screens/disease_identification.py` (~380 lines) - Disease ID screen

   - **Pest Identification Screen:**
     - Crop and growth stage selection
     - Symptom checklist (20 pest symptoms)
     - Severity rating (1-10)
     - Location/pattern selector
     - Results display with confidence scores
     - Detailed pest cards showing:
       - Common and scientific names
       - Description and damage symptoms
       - Identification features
       - Economic thresholds (highlighted)
       - Management notes

   - **Disease Identification Screen:**
     - Crop and growth stage selection
     - Symptom checklist (20 disease symptoms)
     - Weather conditions selector
     - Severity rating and location pattern
     - Results display with confidence scores
     - Detailed disease cards showing:
       - Common and scientific names
       - Description and symptoms
       - Favorable conditions
       - Management recommendations

   - **Files Modified:**
     - `frontend/models/__init__.py` - Added identification exports
     - `frontend/api/__init__.py` - Added IdentificationAPI export
     - `frontend/ui/screens/__init__.py` - Added screen exports
     - `frontend/ui/main_window.py` - Integrated new screens

   - **To Test:**
     ```bash
     cd frontend
     python main.py
     # Click "Pests" or "Diseases" from sidebar
     # Select symptoms and click "Identify"
     ```

---

### Previous Session: December 9, 2025 @ 4:45 PM CST

#### Bug Fixes & Improvements That Session

1. **Fixed Backend Requirements** ✅
   - Updated `backend/requirements.txt` to use flexible version constraints (>=) instead of pinned versions
   - TensorFlow 2.14.0 was unavailable; now accepts TensorFlow >= 2.15.0
   - Resolved pip installation failures on fresh systems

2. **Fixed Frontend Import Issues** ✅
   - Changed relative imports (`from ..config`) to absolute imports (`from config`)
   - Fixed initialization order bug in `ui/sidebar.py` (`_nav_buttons` initialized before `_setup_ui()`)
   - Files modified:
     - `frontend/ui/main_window.py` - Absolute imports
     - `frontend/ui/__init__.py` - Absolute imports
     - `frontend/ui/sidebar.py` - Fixed init order, absolute imports
     - `frontend/ui/screens/__init__.py` - Absolute imports
     - `frontend/ui/screens/dashboard.py` - Absolute imports
     - `frontend/api/__init__.py` - Absolute imports

3. **Verified System Runs Successfully** ✅
   - Backend: `cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000`
   - Frontend: `cd frontend && python main.py`
   - All 42+ API endpoints load correctly
   - PyQt6 GUI starts without errors

---

### Previous Session: December 9, 2025 @ 9:15 AM CST

#### Features Completed That Session

1. **PyQt6 Frontend - Phase 6: Pricing Screen** ✅ COMPLETE
   - Location: `frontend/ui/screens/pricing.py`
   - **Tabbed Interface with 3 Tabs:**
     - **Price List Tab:**
       - Product table with all prices (60+ products)
       - Category filter (Fertilizer, Pesticide, Seed, Fuel, Custom Application)
       - Region selector (7 regions with price adjustments)
       - Source indicator (default vs custom/supplier)
       - "Set Price" button for each product
       - SetPriceDialog: Enter supplier quote with expiration date
     - **Buy/Wait Tab:**
       - Product selector with common products
       - Quantity and purchase deadline inputs
       - Large recommendation display (BUY NOW / WAIT / SPLIT PURCHASE)
       - Price analysis grid (current, total cost, trend, vs 90-day avg)
       - Color-coded trend indicators
       - Reasoning and suggested action display
       - Potential savings calculation
     - **Alerts Tab:**
       - Price alerts list with auto-refresh
       - Color-coded alert cards (warning, error, info)
       - Expiring quote notifications
       - Above-average price warnings
       - Supplier and expiry info display
   - **Reusable Components:**
     - SetPriceDialog: Modal for entering supplier prices
   - **Files Created/Modified:**
     - `frontend/ui/screens/pricing.py` (~550 lines) - NEW
     - `frontend/ui/screens/__init__.py` - Updated exports
     - `frontend/ui/main_window.py` - Integrated PricingScreen
   - **To Test:**
     ```bash
     cd frontend
     python main.py
     # Click "Price Manager" from dashboard or sidebar
     # Use tabs: Price List, Buy/Wait, Alerts
     ```

2. **PyQt6 Frontend - Phase 5: Cost Optimizer Screen** ✅ COMPLETE
   - Location: `frontend/ui/screens/cost_optimizer.py`
   - **New API Client & Models Created:**
     - `frontend/models/cost_optimizer.py` (~350 lines):
       - OptimizationPriority, IrrigationType enums
       - CropInfo, QuickEstimateRequest/Response
       - FarmProfileRequest, CompleteAnalysisResponse
       - FertilizerRequest/Response, IrrigationCostRequest/Response
       - LaborScoutingRequest/Response
     - `frontend/api/cost_optimizer_api.py` (~130 lines):
       - quick_estimate(), complete_analysis()
       - optimize_fertilizer(), analyze_irrigation_cost()
       - analyze_scouting_labor(), get_budget_worksheet()
   - **Tabbed Interface with 3 Tabs:**
     - **Quick Estimate Tab:**
       - Crop, acres, yield goal, irrigated inputs
       - Cost summary cards (Total Cost, Revenue, Net Return)
       - Detailed cost breakdown table by category
       - Savings potential display (10-20% range)
       - Break-even yield calculation
     - **Fertilizer Tab:**
       - Crop selection and yield goal
       - Soil test inputs (P ppm, K ppm, pH)
       - Previous crop N credit selection
       - Nutrient recommendations table (N, P2O5, K2O)
       - Product suggestions with costs
       - Total cost display
     - **Irrigation Tab:**
       - System type selector (center pivot, drip, sprinkler, flood, furrow)
       - Water applied, pumping depth inputs
       - Water cost and electricity rate inputs
       - Variable/Fixed/Total cost cards
       - Efficiency and cost per acre-inch display
       - Savings opportunities
   - **Reusable Components:**
     - CostSummaryCard: Displays total, per-acre, and breakdown
   - **Files Created/Modified:**
     - `frontend/models/cost_optimizer.py` - NEW
     - `frontend/api/cost_optimizer_api.py` - NEW
     - `frontend/ui/screens/cost_optimizer.py` (~650 lines) - NEW
     - `frontend/models/__init__.py` - Updated exports
     - `frontend/api/__init__.py` - Updated exports
     - `frontend/ui/screens/__init__.py` - Updated exports
     - `frontend/ui/main_window.py` - Integrated CostOptimizerScreen
   - **To Test:**
     ```bash
     cd frontend
     python main.py
     # Click "Cost Analysis" from dashboard or sidebar
     # Use tabs to explore Quick Estimate, Fertilizer, Irrigation
     ```

2. **PyQt6 Frontend - Phase 4: Spray Timing Screen** ✅ COMPLETE
   - Location: `frontend/ui/screens/spray_timing.py`
   - **Weather Input Panel:**
     - Temperature, wind speed, wind direction inputs
     - Humidity, rain chance, dew point, cloud cover
     - Real-time Delta T calculation with ideal range indicator (2-8°F)
   - **Spray Settings Panel:**
     - Spray type selector (herbicide, insecticide, fungicide, growth regulator, desiccant)
     - Optional product name input
     - Cost analysis inputs (acres, product cost, application cost)
     - Crop, yield goal, grain price for economic analysis
   - **Risk Level Indicator:**
     - Large visual display with color-coded risk levels
     - Score 0-100 with progress bar
     - EXCELLENT (green) → DO NOT SPRAY (red) spectrum
   - **Conditions Assessment Table:**
     - Factor-by-factor breakdown (wind, temp, humidity, etc.)
     - Status indicators (suitable, marginal, unsuitable)
     - Detailed messages for each factor
   - **Recommendations Panel:**
     - Concerns list with bullet points
     - Actionable recommendations
   - **Cost of Waiting Analysis:**
     - SPRAY NOW vs WAIT recommendation
     - Cost comparison (spray now vs wait)
     - Yield loss risk percentage
     - Action items list
   - **Files Created/Modified:**
     - `frontend/ui/screens/spray_timing.py` (~650 lines) - NEW
     - `frontend/ui/screens/__init__.py` - Updated exports
     - `frontend/ui/main_window.py` - Integrated SprayTimingScreen
   - **To Test:**
     ```bash
     cd frontend
     python main.py
     # Click "Spray Timing" from dashboard or sidebar
     # Enter weather conditions and click "Evaluate Conditions"
     ```

2. **PyQt6 Frontend - Phase 3: Yield Response Screen** ✅ COMPLETE
   - Location: `frontend/ui/screens/yield_response.py`
   - **Interactive Yield Response Calculator:**
     - Full input panel with crop, nutrient, soil test level, yield potential
     - Price inputs with nutrient cost and grain price
     - Real-time price ratio display
     - Response model selector (5 models: quadratic plateau, quadratic, linear plateau, Mitscherlich, square root)
   - **Pyqtgraph Yield Curve Visualization:**
     - Interactive yield response curve chart
     - EOR marker line (green dashed) showing economic optimum rate
     - Max yield marker line (orange dotted) for comparison
     - Auto-scaling axes with proper labels
   - **EOR Results Panel:**
     - Large EOR rate display (primary result)
     - Expected yield at EOR
     - Max yield comparison
     - Yield sacrifice calculation
     - Net return at EOR ($/acre)
     - Savings vs max rate application
     - Fertilizer savings (lb/acre)
     - Dynamic recommendation text
   - **Rate Comparison Table:**
     - Compares EOR with max rate and alternatives
     - Shows yield, gross revenue, fertilizer cost, net return
     - Highlights best rate (green background)
     - Ranked by net return
   - **API Integration:**
     - Connected to yield_response_api.py
     - Error handling with user-friendly messages
     - Loading indicator during calculations
   - **Files Created/Modified:**
     - `frontend/ui/screens/yield_response.py` (~550 lines) - NEW
     - `frontend/ui/screens/__init__.py` - Updated exports
     - `frontend/ui/main_window.py` - Integrated YieldResponseScreen
   - **To Test:**
     ```bash
     cd frontend
     python main.py
     # Click "Yield Calculator" from dashboard or sidebar
     # Adjust inputs and click "Calculate EOR"
     ```

---

### Previous Session: December 8, 2025 @ 10:53 PM CST

#### Features Completed That Session

1. **Yield Response & Economic Optimum Rate Calculator** ✅ COMPLETE
   - Location: `backend/services/yield_response_optimizer.py`
   - **New API Endpoints (7 total):**
     - `POST /api/v1/yield-response/curve` - Generate yield response curve for any nutrient
     - `POST /api/v1/yield-response/economic-optimum` - Calculate Economic Optimum Rate (EOR)
     - `POST /api/v1/yield-response/compare-rates` - Compare profitability of different rates
     - `POST /api/v1/yield-response/price-sensitivity` - Analyze EOR changes with prices
     - `POST /api/v1/yield-response/multi-nutrient` - Optimize N, P, K simultaneously
     - `GET /api/v1/yield-response/crop-parameters/{crop}` - View underlying agronomic data
     - `GET /api/v1/yield-response/price-ratio-guide` - Quick field reference lookup table
   - **Capabilities:**
     - 5 yield response models (quadratic, quadratic-plateau, linear-plateau, Mitscherlich, square-root)
     - Economic Optimum Rate calculation using calculus-based approach
     - Multi-nutrient optimization with budget constraints
     - Price sensitivity analysis for volatile markets
     - Soil test adjustments (5 levels: very low to very high)
     - Previous crop nitrogen credits
     - Crop-specific parameters for corn, soybean, wheat
     - Price ratio lookup tables for field decisions
   - **Key Economics Concept:**
     - EOR = rate where marginal cost equals marginal revenue
     - Maximizes profit, not yield (avoids over-application)
     - Accounts for diminishing returns in fertilizer response

2. **Documentation Update for v2.2** ✅ COMPLETE
   - **PROFESSIONAL_SYSTEM_GUIDE.md** - Added complete v2.2 section (~300 lines):
     - Updated "What Makes This Professional" with item 9 (yield response)
     - Updated architecture diagram with `yield_response_optimizer.py`
     - Full documentation of all 7 yield response endpoints with examples
     - Key concepts explained (EOR, price ratios, diminishing returns)
     - 5 yield response models documented
     - Soil test adjustment tables
     - Real-world examples with dollar savings calculations
     - Updated conclusion and version history table
   - **QUICKSTART.md** - Added farmer-friendly v2.2 guide (~160 lines):
     - "What's My Most Profitable N Rate?" with example output
     - "Compare Different N Rates" usage guide
     - "How Do Prices Change My Optimal Rate?" tutorial
     - "Optimize N, P, and K Together" multi-nutrient guide
     - "Quick Reference: Price Ratio Guide" field lookup
     - Updated "The Bottom Line" section (now 10 key questions)
   - **README.md** - Already complete (verified)
   - **CHANGELOG.md** - This update

3. **PyQt6 Frontend - Phase 1: Foundation** ✅ COMPLETE
   - Location: `frontend/`
   - **Architecture Designed:**
     - Professional desktop app for crop consulting
     - Responsive layout (1366x768 to 1920x1080+)
     - Offline-capable with API fallback
     - Interactive charts with pyqtgraph
   - **Files Created (Phase 1):**
     - `frontend/main.py` - Application entry point
     - `frontend/app.py` - QApplication setup
     - `frontend/config.py` - Settings management with save/load
     - `frontend/requirements.txt` - PyQt6, httpx, pyqtgraph, numpy
     - `frontend/ui/styles.py` - Professional green/brown theme (~500 lines QSS)
     - `frontend/ui/sidebar.py` - Navigation sidebar with sections
     - `frontend/ui/main_window.py` - Main window with status bar
     - `frontend/ui/screens/dashboard.py` - Dashboard with quick actions
     - Package `__init__.py` files for all directories
   - **UI Features Implemented:**
     - Sidebar navigation with grouped sections (Identify, Recommend, Optimize)
     - Professional color palette (agriculture green, earth brown)
     - Connection status indicator (Online/Offline)
     - Quick action cards on dashboard
     - Responsive layout using QSplitter
     - Placeholder screens for all 9 feature areas
   - **To Run:**
     ```bash
     cd frontend
     pip install -r requirements.txt
     python main.py
     ```
   - **Remaining Phases (planned for future sessions):**
     - ~~Phase 2: API Client & Models~~ ✅ DONE
     - ~~Phase 3: Yield Response Screen~~ ✅ DONE
     - ~~Phase 4: Spray Timing Screen~~ ✅ DONE
     - ~~Phase 5: Cost Optimizer Screen~~ ✅ DONE
     - ~~Phase 6: Pricing Screen~~ ✅ DONE
     - Phase 7: Pest/Disease ID Screens
     - Phase 8: Offline Mode & Local DB
     - Phase 9: Polish & Testing

4. **PyQt6 Frontend - Phase 2: API Client & Models** ✅ COMPLETE
   - Location: `frontend/api/` and `frontend/models/`
   - **Base HTTP Client (`api/client.py`):**
     - APIClient class with httpx for HTTP requests
     - Connection state tracking (online/offline)
     - Automatic error handling and mapping
     - Retry support and timeout configuration
     - APIResponse wrapper for consistent return types
     - Custom exceptions (ConnectionError, ValidationError, etc.)
     - Singleton pattern with get_api_client()
   - **Data Models Created:**
     - `models/yield_response.py` (~350 lines):
       - Enums: Crop, Nutrient, SoilTestLevel, ResponseModel
       - Request classes: YieldCurveRequest, EORRequest, CompareRatesRequest, etc.
       - Response classes: YieldCurveResponse, EORResult, CompareRatesResponse, etc.
       - All with to_dict() and from_dict() methods
     - `models/spray.py` (~350 lines):
       - Enums: SprayType, RiskLevel, DiseasePressure
       - WeatherCondition dataclass for weather input
       - SprayEvaluation, SprayWindow, CostOfWaitingResult
       - DiseasePressureResponse, GrowthStageTimingResponse
     - `models/pricing.py` (~400 lines):
       - Enums: ProductCategory, Region, PriceTrend, BuyRecommendation
       - ProductPrice, SetPriceRequest/Response
       - BulkUpdateRequest/Response
       - BuyRecommendationRequest/Response with PriceAnalysis
       - InputCostRequest/Response
       - PriceAlert, SupplierComparison classes
   - **API Modules Created:**
     - `api/yield_response_api.py` - All 7 yield response endpoints
     - `api/spray_api.py` - All 5 spray timing endpoints
     - `api/pricing_api.py` - All 9 pricing service endpoints
   - **Total:** ~1,400 lines of API/model code

5. **Git History Cleanup** ✅ COMPLETE
   - Removed unrelated `age-verification.js` commit from history
   - Rebased and force-pushed to clean up repository
   - No impact on app functionality

---

## Version History

### v2.1.0 - Pricing & Spray Timing (December 2025)

**Features Added:**
1. **Real-Time/Custom Pricing Integration** ✅ COMPLETE
   - Location: `backend/services/pricing_service.py`
   - **New API Endpoints (9 total):**
     - `GET /api/v1/pricing/prices` - Get all prices with optional category filter
     - `GET /api/v1/pricing/price/{product_id}` - Get specific product price
     - `POST /api/v1/pricing/set-price` - Set custom supplier quote
     - `POST /api/v1/pricing/bulk-update` - Bulk import price list
     - `POST /api/v1/pricing/buy-recommendation` - Buy now vs wait analysis
     - `POST /api/v1/pricing/calculate-input-costs` - Calculate costs with custom prices
     - `POST /api/v1/pricing/compare-suppliers` - Compare supplier pricing
     - `GET /api/v1/pricing/alerts` - Expiring quotes and price alerts
     - `GET /api/v1/pricing/budget-prices/{crop}` - Generate budget price list
   - **Capabilities:**
     - 7 regional price adjustments (Midwest, Northern Plains, Southern Plains, etc.)
     - 60+ default products with prices (fertilizers, pesticides, seeds, fuel)
     - Price history tracking with trend analysis
     - Buy/wait recommendations based on price trends
     - Supplier quote management with expiration tracking
     - Savings calculations vs. default prices

2. **Weather-Smart Spray Timing Optimizer** ✅ COMPLETE
   - Location: `backend/services/spray_timing_optimizer.py`
   - **New API Endpoints (5 total):**
     - `POST /api/v1/spray-timing/evaluate` - Evaluate current spray conditions
     - `POST /api/v1/spray-timing/find-windows` - Find optimal windows in forecast
     - `POST /api/v1/spray-timing/cost-of-waiting` - Economic analysis of waiting
     - `POST /api/v1/spray-timing/disease-pressure` - Assess disease risk from weather
     - `GET /api/v1/spray-timing/growth-stage-timing/{crop}/{growth_stage}` - Stage-specific guidance
   - **Capabilities:**
     - Evaluates 7 weather factors (wind, temp, humidity, rain, inversion, leaf wetness, dew point)
     - 5 spray types supported (herbicide, insecticide, fungicide, growth regulator, desiccant)
     - Product-specific rainfastness requirements (20+ products)
     - Disease pressure models for 6 major diseases
     - Cost-of-waiting calculator with yield loss estimates
     - Growth stage-specific timing recommendations
     - Drift risk assessment and mitigation recommendations

---

## Version History

### v2.0.0 - Input Cost Optimization Release (December 2025)

**Major Features Added:**
- Complete Labor Cost Optimizer (`backend/services/labor_optimizer.py`)
  - Scouting cost analysis with field grouping
  - Application labor optimization by equipment type
  - Seasonal labor budgeting
  - Custom vs. self-application comparison

- Application Cost Optimizer (`backend/services/application_cost_optimizer.py`)
  - Pesticide product comparison with efficacy ratings
  - Spray program cost analysis with ROI
  - Variable Rate Application (VRA) analysis
  - Generic alternative suggestions
  - Tank-mix optimization

- Fertilizer Optimization (`backend/services/application_cost_optimizer.py`)
  - Nutrient requirement calculations (N, P, K, S)
  - Economical product selection by cost per lb nutrient
  - Soil test-based recommendations
  - Split application timing optimization

- Irrigation Cost Optimizer (`backend/services/irrigation_optimizer.py`)
  - Crop water need calculations (ET-based)
  - System efficiency comparisons (7 irrigation types)
  - Water savings strategy analysis
  - Season irrigation scheduling
  - Upgrade ROI calculations

- Master Input Cost Optimizer (`backend/services/input_cost_optimizer.py`)
  - Complete farm analysis integrating all domains
  - Priority-based recommendations (cost, ROI, sustainability, risk)
  - Quick estimate tool
  - Budget worksheet generation
  - Strategy comparison

**API Endpoints Added:** 20+ endpoints under `/api/v1/optimize/`

### v1.0.0 - Professional Crop Consulting System (November 2025)

**Core Features:**
- Professional pest/disease identification (46 pests/diseases)
- Intelligent spray recommendation engine (40+ products)
- Economic threshold calculators
- Resistance management with MOA rotation
- Complete pesticide database with label information

---

## Architecture Overview

```
AgTools v2.5.0
├── backend/
│   ├── main.py                           # FastAPI app (1800+ lines, 59+ endpoints)
│   ├── services/
│   │   ├── labor_optimizer.py            # Labor cost optimization
│   │   ├── application_cost_optimizer.py # Fertilizer/pesticide costs
│   │   ├── irrigation_optimizer.py       # Water/irrigation costs
│   │   ├── input_cost_optimizer.py       # Master cost integration
│   │   ├── pricing_service.py            # v2.1 - Dynamic pricing
│   │   ├── spray_timing_optimizer.py     # v2.1 - Weather-smart spraying
│   │   ├── yield_response_optimizer.py   # v2.2 - Economic optimum rates
│   │   ├── auth_service.py               # v2.5 - JWT authentication
│   │   └── user_service.py               # v2.5 - User & crew management
│   ├── middleware/
│   │   └── auth_middleware.py            # v2.5 - Auth middleware
│   └── models/
├── frontend/                             # PyQt6 Desktop Application
│   ├── main.py                           # Entry point
│   ├── app.py                            # QApplication setup (with login flow)
│   ├── config.py                         # Settings management
│   ├── requirements.txt                  # PyQt6, httpx, pyqtgraph
│   ├── api/                              # API client modules (with offline support)
│   │   ├── client.py                     # v2.3 - Cache/offline fallback
│   │   ├── auth_api.py                   # v2.5 - Authentication API
│   │   ├── user_api.py                   # v2.5 - User management API
│   │   └── crew_api.py                   # v2.5 - Crew management API
│   ├── models/                           # Data classes
│   ├── database/                         # v2.3 - Local SQLite cache
│   │   └── local_db.py                   # SQLite database manager
│   ├── core/                             # v2.3 - Core services
│   │   ├── sync_manager.py               # Online/offline sync management
│   │   └── calculations/                 # Offline calculation engines
│   │       ├── yield_response.py         # Offline EOR calculator
│   │       └── spray_timing.py           # Offline spray evaluator
│   └── ui/
│       ├── styles.py                     # Professional QSS theme
│       ├── sidebar.py                    # Navigation sidebar
│       ├── main_window.py                # Main window (with sync UI)
│       ├── screens/
│       │   ├── dashboard.py              # Home screen
│       │   ├── yield_response.py         # Phase 3 - Interactive charts
│       │   ├── spray_timing.py           # Phase 4 - Weather evaluation
│       │   ├── cost_optimizer.py         # Phase 5 - Tabbed cost analysis
│       │   ├── pricing.py                # Phase 6 - Price management
│       │   ├── pest_identification.py    # Phase 7 - Pest ID
│       │   ├── disease_identification.py # Phase 7 - Disease ID
│       │   ├── settings.py               # Phase 9 - Settings & preferences
│       │   ├── login.py                  # v2.5 - Login screen
│       │   ├── user_management.py        # v2.5 - Admin user management
│       │   └── crew_management.py        # v2.5 - Crew/team management
│       ├── widgets/                      # Reusable components
│       │   └── common.py                 # Phase 9 - Loading, validation, toasts
│       └── tests/
│           └── test_phase9.py            # Phase 9 - Integration tests
├── database/
│   ├── schema.sql
│   ├── chemical_database.py
│   ├── seed_data.py
│   └── migrations/
│       └── 001_auth_system.sql           # v2.5 - Auth tables
└── docs/
```

---

## Key Files Quick Reference

### Backend Services
| Feature | File Path | Lines | Endpoints |
|---------|-----------|-------|-----------|
| Labor Costs | `backend/services/labor_optimizer.py` | ~400 | 3 |
| Pesticide/Fertilizer | `backend/services/application_cost_optimizer.py` | ~830 | 4 |
| Irrigation | `backend/services/irrigation_optimizer.py` | ~600 | 5 |
| Master Optimizer | `backend/services/input_cost_optimizer.py` | ~500 | 3 |
| Pricing Service | `backend/services/pricing_service.py` | ~650 | 9 |
| Spray Timing | `backend/services/spray_timing_optimizer.py` | ~750 | 5 |
| Yield Response | `backend/services/yield_response_optimizer.py` | ~850 | 7 |
| **Auth Service** | `backend/services/auth_service.py` | ~350 | 6 |
| **User Service** | `backend/services/user_service.py` | ~1050 | 11 |
| API Endpoints | `backend/main.py` | ~2000 | 59+ |

### Frontend (v2.5)
| Feature | File Path | Lines |
|---------|-----------|-------|
| **Login Screen** | `frontend/ui/screens/login.py` | ~280 |
| **User Management** | `frontend/ui/screens/user_management.py` | ~400 |
| **Crew Management** | `frontend/ui/screens/crew_management.py` | ~420 |
| **Auth API** | `frontend/api/auth_api.py` | ~220 |
| **User API** | `frontend/api/user_api.py` | ~140 |
| **Crew API** | `frontend/api/crew_api.py` | ~170 |
| Local Database | `frontend/database/local_db.py` | ~550 |
| Sync Manager | `frontend/core/sync_manager.py` | ~450 |
| Offline Yield Calc | `frontend/core/calculations/yield_response.py` | ~450 |
| Offline Spray Calc | `frontend/core/calculations/spray_timing.py` | ~400 |
| Settings Screen | `frontend/ui/screens/settings.py` | ~500 |
| Common Widgets | `frontend/ui/widgets/common.py` | ~400 |
| API Client | `frontend/api/client.py` | ~410 |
| Main Window | `frontend/ui/main_window.py` | ~490 |

### v2.5 New Endpoint Summary

**Authentication (`/api/v1/auth/`):**
- `POST /login` - Login and get tokens
- `POST /logout` - Logout and invalidate session
- `POST /refresh` - Refresh access token
- `GET /me` - Get current user info
- `PUT /me` - Update own profile
- `POST /change-password` - Change own password

**User Management (`/api/v1/users/`):**
- `GET /` - List users with filters
- `POST /` - Create user (admin only)
- `GET /{id}` - Get user details
- `PUT /{id}` - Update user (admin only)
- `DELETE /{id}` - Deactivate user (admin only)

**Crew Management (`/api/v1/crews/`):**
- `GET /` - List crews
- `POST /` - Create crew (admin only)
- `GET /{id}` - Get crew details
- `PUT /{id}` - Update crew (admin only)
- `GET /{id}/members` - Get crew members
- `POST /{id}/members/{user_id}` - Add member
- `DELETE /{id}/members/{user_id}` - Remove member
- `GET /users/{id}/crews` - Get user's crews

### v2.2 New Endpoint Summary

**Yield Response (`/api/v1/yield-response/`):**
- `POST /curve` - Generate yield response curve
- `POST /economic-optimum` - Calculate Economic Optimum Rate (EOR)
- `POST /compare-rates` - Compare profitability of different rates
- `POST /price-sensitivity` - Analyze EOR changes with price ratios
- `POST /multi-nutrient` - Optimize N, P, K together with budget constraint
- `GET /crop-parameters/{crop}` - View agronomic parameters
- `GET /price-ratio-guide` - Quick field reference table

### v2.1 Endpoint Summary

**Pricing Service (`/api/v1/pricing/`):**
- `GET /prices` - All prices by category
- `GET /price/{id}` - Single product price
- `POST /set-price` - Add supplier quote
- `POST /bulk-update` - Import price list
- `POST /buy-recommendation` - Buy now vs wait
- `POST /calculate-input-costs` - Cost calculator
- `POST /compare-suppliers` - Supplier comparison
- `GET /alerts` - Price alerts
- `GET /budget-prices/{crop}` - Budget planning

**Spray Timing (`/api/v1/spray-timing/`):**
- `POST /evaluate` - Current conditions check
- `POST /find-windows` - Find spray windows
- `POST /cost-of-waiting` - Economic analysis
- `POST /disease-pressure` - Disease risk assessment
- `GET /growth-stage-timing/{crop}/{stage}` - Stage guidance

---

## Upcoming Features (Roadmap)

- [x] **Farm Operations Manager (v2.5)** ✅ **COMPLETE**
  - [x] Phase 1: Multi-User Authentication System **DONE**
  - [x] Phase 2: Task Management Core **DONE**
  - [x] Phase 3: Field Operations & Logging **DONE**
  - [x] Phase 4: Equipment & Inventory Tracking **DONE**
  - [x] Phase 5: Reporting & Analytics Dashboard **DONE**
- [ ] **John Deere Operations Center Integration** (v2.6 - requires JD Developer Account approval)
  - [ ] JD API Client & OAuth Authentication
  - [ ] Field Boundary Sync
  - [ ] Yield/Harvest Data Import
  - [ ] Application History Tracking
- [ ] Field-level precision / zone management (enabled by JD yield zones)
- [x] ~~Input-to-yield response curves (economic optimum rates)~~ **DONE v2.2**
- [x] ~~Offline mode & local database~~ **DONE v2.3**
- [x] ~~Phase 9: Polish & Testing~~ **DONE v2.4** (PyQt6 frontend complete!)
- [ ] Custom vs. hire equipment decision engine
- [ ] Carbon credit / sustainability ROI calculator
- [ ] Mobile app / frontend web interface
- [ ] Climate FieldView integration (future)

---

## Notes for Future Sessions

When starting a new chat, reference this file to understand:
1. What features exist and where they're located
2. What's currently being developed
3. The overall architecture pattern (FastAPI + service layer + singletons)
4. API endpoint structure (`/api/v1/optimize/...`)

All cost optimizers follow the same pattern:
- Enum classes for types
- Constants dictionaries for pricing/rates
- Main optimizer class with public analysis methods
- Singleton getter function for FastAPI dependency injection
