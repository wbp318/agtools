# Farm Operations Manager - Development Plan

> **Version:** 2.5.0
> **Status:** 🔄 IN PROGRESS - Phases 1-4 Complete, Ready for Phase 5
> **Started:** December 11, 2025
> **Last Updated:** December 18, 2025

---

## Overview

A comprehensive farm operations management system combining irrigation scheduling optimization with multi-user task/project management, fully integrated with AgTools' existing crop consulting features.

### Business Value
- **Labor optimization** - Track and optimize crew hours across multiple projects
- **Irrigation efficiency** - ET-based scheduling, weather-aware, cost tracking
- **Energy cost preparation** - Baseline tracking before regional rate increases (Meta data center impact)
- **Integrated workflows** - Pest/disease IDs auto-generate spray tasks
- **Multi-user support** - Crew members view assignments, managers track progress

---

## Phase Summary

| Phase | Description | Status | Est. Effort |
|-------|-------------|--------|-------------|
| Phase 1 | User & Auth System | ✅ COMPLETE | 6-8 hours |
| Phase 2 | Task Management Core | ✅ COMPLETE | 8-10 hours |
| Phase 3 | Field Operations & Logging | ✅ COMPLETE | 6-8 hours |
| Phase 4 | Equipment & Inventory Tracking | ✅ COMPLETE | 6-8 hours |
| Phase 5 | Reporting & Analytics Dashboard | ⏳ Pending | 8-10 hours |
| Phase 6 | Mobile/Crew Interface | ⏳ Pending | 6-8 hours |

---

## Phase 1: User & Auth System

**Goal:** Establish multi-user authentication with role-based access control.

**Status:** ✅ COMPLETE (December 11, 2025)

### What Was Built

**Backend:**
- `backend/services/auth_service.py` (~350 lines) - JWT token handling, bcrypt password hashing
- `backend/services/user_service.py` (~1050 lines) - User & crew CRUD, authentication
- `backend/middleware/auth_middleware.py` (~170 lines) - Protected route decorators
- 17 new API endpoints for auth, users, and crews

**Frontend:**
- `frontend/ui/screens/login.py` (~280 lines) - Login screen with remember me
- `frontend/ui/screens/user_management.py` (~400 lines) - Admin user management
- `frontend/ui/screens/crew_management.py` (~420 lines) - Crew/team management
- `frontend/api/auth_api.py` (~220 lines) - Auth API client
- `frontend/api/user_api.py` (~140 lines) - User API client
- `frontend/api/crew_api.py` (~170 lines) - Crew API client
- Updated `app.py` with login flow
- Updated `main_window.py` with user menu and logout

**Database:**
- `database/migrations/001_auth_system.sql` - Schema for users, sessions, crews

**Default Admin:**
- Username: `admin`
- Password: `admin123` (change immediately!)

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'crew',  -- admin, manager, crew
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table (for token management)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Crews/Teams table (optional grouping)
CREATE TABLE crews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- Crew membership
CREATE TABLE crew_members (
    crew_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (crew_id, user_id),
    FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Roles & Permissions

| Permission | Admin | Manager | Crew |
|------------|-------|---------|------|
| View own tasks | ✅ | ✅ | ✅ |
| Update task status | ✅ | ✅ | ✅ |
| Create tasks | ✅ | ✅ | ❌ |
| Assign tasks to others | ✅ | ✅ | ❌ |
| View all crew tasks | ✅ | ✅ | ❌ |
| Manage projects | ✅ | ✅ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| Manage crews | ✅ | ❌ | ❌ |
| System settings | ✅ | ❌ | ❌ |
| View reports | ✅ | ✅ | ❌ |

### API Endpoints

```
POST   /api/v1/auth/register        - Register new user (admin only)
POST   /api/v1/auth/login           - Login, returns JWT token
POST   /api/v1/auth/logout          - Invalidate session
POST   /api/v1/auth/refresh         - Refresh JWT token
GET    /api/v1/auth/me              - Get current user info
PUT    /api/v1/auth/me              - Update own profile
POST   /api/v1/auth/change-password - Change own password

GET    /api/v1/users                - List all users (admin/manager)
GET    /api/v1/users/{id}           - Get user details
PUT    /api/v1/users/{id}           - Update user (admin)
DELETE /api/v1/users/{id}           - Deactivate user (admin)

GET    /api/v1/crews                - List crews
POST   /api/v1/crews                - Create crew (admin)
PUT    /api/v1/crews/{id}           - Update crew
POST   /api/v1/crews/{id}/members   - Add member to crew
DELETE /api/v1/crews/{id}/members/{user_id} - Remove member
```

### Backend Implementation

**New Files:**
- `backend/services/auth_service.py` - Authentication logic, JWT handling
- `backend/services/user_service.py` - User CRUD operations
- `backend/middleware/auth_middleware.py` - JWT validation middleware
- `backend/models/user.py` - Pydantic models for users

**Dependencies to Add:**
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data parsing

### Frontend Implementation

**New Screens:**
- `frontend/ui/screens/login.py` - Login screen
- `frontend/ui/screens/user_management.py` - Admin user management
- `frontend/ui/screens/crew_management.py` - Crew/team management

**Modified Files:**
- `frontend/config.py` - Store auth token
- `frontend/api/client.py` - Add auth headers to requests
- `frontend/ui/main_window.py` - Add login flow, user menu

### Security Considerations
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with 24-hour expiration
- Refresh tokens with 7-day expiration
- Rate limiting on login attempts
- Session invalidation on password change

### Deliverables Checklist
- [ ] Database schema migration
- [ ] Auth service with JWT
- [ ] User service with CRUD
- [ ] Auth middleware
- [ ] API endpoints (auth, users, crews)
- [ ] Login screen (frontend)
- [ ] User management screen
- [ ] Crew management screen
- [ ] Auth integration in API client
- [ ] Protected route handling

---

## Phase 2: Task Management Core

**Goal:** Create the core task and project management system.

**Status:** ✅ COMPLETE (December 12, 2025)

### What Was Built

**Backend:**
- `backend/services/task_service.py` (~500 lines) - Task CRUD, status workflow, role-based access
- `database/migrations/002_task_management.sql` - Tasks table schema
- 6 new API endpoints for task management

**Frontend:**
- `frontend/api/task_api.py` (~270 lines) - Task API client
- `frontend/ui/screens/task_management.py` (~520 lines) - Task management screen

**Features:**
- Task CRUD operations (create, read, update, delete)
- Status workflow: todo → in_progress → completed/cancelled
- Priority levels: low, medium, high, urgent
- Assignment to users or crews
- Due date tracking with overdue detection
- Role-based access (admin sees all, manager sees crew, crew sees own)
- Filter by status, priority, "My Tasks"
- Quick status change buttons

### Database Schema

```sql
-- Projects (grouping of related tasks)
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, archived
    start_date DATE,
    target_end_date DATE,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tasks
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(50),  -- scouting, spraying, irrigation, planting, harvest, equipment, general
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    assigned_to INTEGER,
    field_id INTEGER,  -- optional link to field
    equipment_id INTEGER,  -- optional equipment needed
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Task dependencies
CREATE TABLE task_dependencies (
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, depends_on_task_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Task comments/notes
CREATE TABLE task_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Time entries (labor tracking)
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    hours DECIMAL(5,2) NOT NULL,
    work_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Features (Preview)
- Project creation and management
- Task CRUD with assignments
- Task dependencies (Gantt-style)
- Status workflow (pending → in_progress → completed)
- Time tracking per task
- Comments/notes on tasks
- Due date tracking and overdue alerts
- Priority levels
- Filtering and search

---

## Phase 3: Field Operations & Logging

**Goal:** Enable tracking of farm fields and all field operations.

**Status:** ✅ COMPLETE (December 15, 2025)

### What Was Built

**Backend:**
- `backend/services/field_service.py` (~450 lines) - Field CRUD with enums
- `backend/services/field_operations_service.py` (~550 lines) - Operations logging
- `database/migrations/003_field_operations.sql` - Fields & operations tables
- 14 new API endpoints (92 total now)

**Frontend:**
- `frontend/api/field_api.py` (~290 lines) - Field API client
- `frontend/api/operations_api.py` (~380 lines) - Operations API client
- `frontend/ui/screens/field_management.py` (~500 lines) - Field management screen
- `frontend/ui/screens/operations_log.py` (~550 lines) - Operations log screen

**Features:**
- **Field Management:**
  - CRUD for farm fields
  - Attributes: name, farm, acreage, crop, soil, irrigation
  - GPS coordinates and GeoJSON boundary support
  - Summary statistics by crop and farm
  - Search and filtering

- **Operations Logging:**
  - Log all operation types: spray, fertilizer, planting, harvest, tillage, scouting, irrigation
  - Product/material tracking with rates and quantities
  - Cost tracking (product + application costs)
  - Harvest data (yield, moisture)
  - Weather conditions recording
  - Operation history per field
  - Summary statistics with cost breakdown

### Database Schema

```sql
-- Fields table
CREATE TABLE fields (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    farm_name VARCHAR(100),
    acreage DECIMAL(10, 2) NOT NULL,
    current_crop VARCHAR(50),
    soil_type VARCHAR(50),
    irrigation_type VARCHAR(50),
    location_lat DECIMAL(10, 7),
    location_lng DECIMAL(10, 7),
    boundary TEXT,  -- GeoJSON
    notes TEXT,
    created_by_user_id INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Field operations table
CREATE TABLE field_operations (
    id INTEGER PRIMARY KEY,
    field_id INTEGER NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    operation_date DATE NOT NULL,
    product_name VARCHAR(200),
    rate DECIMAL(10, 3),
    rate_unit VARCHAR(50),
    quantity DECIMAL(10, 3),
    quantity_unit VARCHAR(50),
    acres_covered DECIMAL(10, 2),
    product_cost DECIMAL(10, 2),
    application_cost DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    yield_amount DECIMAL(10, 2),
    yield_unit VARCHAR(20),
    moisture_percent DECIMAL(5, 2),
    weather_temp DECIMAL(5, 1),
    weather_wind DECIMAL(5, 1),
    weather_humidity DECIMAL(5, 1),
    weather_notes TEXT,
    operator_id INTEGER,
    task_id INTEGER,  -- Link to task if from task
    notes TEXT,
    created_by_user_id INTEGER,
    is_active BOOLEAN DEFAULT 1
);
```

---

## Phase 4: Equipment & Inventory Tracking

**Goal:** Track equipment and inventory for farm operations.

**Status:** ✅ COMPLETE (December 18, 2025)

### What Was Built

**Backend:**
- `backend/services/equipment_service.py` (~700 lines) - Equipment CRUD, maintenance, hours tracking
- `backend/services/inventory_service.py` (~650 lines) - Inventory CRUD, transactions, alerts
- `database/migrations/004_equipment_inventory.sql` - 5 tables + field_operations mod
- 24 new API endpoints (Equipment: 8, Maintenance: 4, Inventory: 8, Transactions: 4)

**Frontend API Clients:**
- `frontend/api/equipment_api.py` (~500 lines) - Equipment API client
- `frontend/api/inventory_api.py` (~600 lines) - Inventory API client

**Frontend UI Screens:**
- `frontend/ui/screens/equipment_management.py` (~1040 lines)
  - CreateEquipmentDialog, EditEquipmentDialog
  - UpdateHoursDialog, LogMaintenanceDialog
  - Equipment table with type/status filtering
  - Summary cards: total equipment, fleet value, hours, in maintenance
- `frontend/ui/screens/inventory_management.py` (~1100 lines)
  - CreateItemDialog, EditItemDialog
  - QuickPurchaseDialog, AdjustQuantityDialog
  - Inventory table with category/location filtering
  - Summary cards: total items, value, low stock, expiring
- `frontend/ui/screens/maintenance_schedule.py` (~560 lines)
  - MaintenanceAlertCard with urgency-based styling
  - Alerts tab with scrollable card grid
  - History tab with equipment/type filters
  - Summary cards: overdue, due soon, upcoming, total equipment

**Navigation Integration:**
- `frontend/ui/screens/__init__.py` - Added new screen exports
- `frontend/ui/sidebar.py` - Added Equipment section nav
- `frontend/ui/main_window.py` - Integrated new screens

**Operations Log Enhancement:**
- `frontend/ui/screens/operations_log.py` - Equipment & inventory integration
  - Equipment selection with hours used tracking
  - Inventory item selection for product tracking
  - Auto-populate product name/unit from inventory

### Features Delivered

1. **Equipment Fleet Management**
   - Track all equipment: tractors, combines, sprayers, planters, tillage, trucks, ATVs, grain carts
   - Equipment registry with make, model, year, serial number, purchase info
   - Hour meter tracking and usage logging
   - Status tracking: available, in_use, maintenance, retired
   - Hourly operating cost tracking

2. **Maintenance Scheduling**
   - Service history logging with maintenance type, cost, vendor, parts
   - Schedule next service by date or hours
   - Maintenance alerts for upcoming/overdue service (urgency-based cards)
   - Alerts view: overdue (red), due soon (orange), upcoming (blue)

3. **Inventory Management**
   - Track all inputs: seed, fertilizer, chemicals, fuel, parts, supplies
   - Quantity and unit tracking with reorder points (low stock alerts)
   - Storage location and batch/lot numbers
   - Expiration date tracking for chemicals (expiring soon alerts)
   - Cost per unit and total value tracking

4. **Inventory Transactions**
   - Purchase recording with vendor and invoice tracking
   - Usage tracking linked to field operations
   - Inventory adjustments with reason tracking
   - Transaction history per item

5. **Operations Integration**
   - Equipment selection when logging operations
   - Hours used tracking per operation
   - Inventory item selection for products
   - Auto-populate product name and unit from inventory

### New Sidebar Navigation

```
Equipment Section:
├── Equipment (fleet management)
├── Inventory (inputs tracking)
└── Maintenance (schedule & alerts)
```

### Database Schema

```sql
-- Equipment table
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    serial_number VARCHAR(100),
    purchase_date DATE,
    purchase_price DECIMAL(12, 2),
    current_hours DECIMAL(10, 1),
    hourly_cost DECIMAL(8, 2),
    status VARCHAR(20) DEFAULT 'available',
    notes TEXT,
    is_active BOOLEAN DEFAULT 1
);

-- Maintenance records
CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY,
    equipment_id INTEGER NOT NULL,
    maintenance_type VARCHAR(50),
    maintenance_date DATE NOT NULL,
    hours_at_service DECIMAL(10, 1),
    cost DECIMAL(10, 2),
    vendor VARCHAR(100),
    parts_used TEXT,
    notes TEXT,
    next_service_date DATE,
    next_service_hours DECIMAL(10, 1),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- Inventory items
CREATE TABLE inventory_items (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity DECIMAL(12, 3) DEFAULT 0,
    unit VARCHAR(50),
    reorder_point DECIMAL(12, 3),
    storage_location VARCHAR(100),
    batch_lot_number VARCHAR(100),
    expiration_date DATE,
    cost_per_unit DECIMAL(10, 4),
    notes TEXT,
    is_active BOOLEAN DEFAULT 1
);

-- Inventory transactions
CREATE TABLE inventory_transactions (
    id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(12, 3) NOT NULL,
    unit_cost DECIMAL(10, 4),
    total_cost DECIMAL(12, 2),
    vendor VARCHAR(100),
    invoice_number VARCHAR(100),
    field_operation_id INTEGER,
    notes TEXT,
    transaction_date TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(id)
);

-- Equipment usage per operation (added to field_operations)
ALTER TABLE field_operations ADD COLUMN equipment_id INTEGER;
ALTER TABLE field_operations ADD COLUMN equipment_hours_used DECIMAL(6, 1);
ALTER TABLE field_operations ADD COLUMN inventory_item_id INTEGER;
```

### API Endpoints (24 total)

**Equipment Management:**
- `GET /api/v1/equipment` - List equipment with filters
- `POST /api/v1/equipment` - Create equipment
- `GET /api/v1/equipment/summary` - Fleet summary stats
- `GET /api/v1/equipment/types` - List equipment types
- `GET /api/v1/equipment/{id}` - Get equipment details
- `PUT /api/v1/equipment/{id}` - Update equipment
- `DELETE /api/v1/equipment/{id}` - Deactivate equipment
- `POST /api/v1/equipment/{id}/hours` - Update hour meter

**Maintenance:**
- `POST /api/v1/equipment/{id}/maintenance` - Log maintenance
- `GET /api/v1/maintenance/alerts` - Get maintenance alerts
- `GET /api/v1/maintenance/history` - Get maintenance history

**Inventory:**
- `GET /api/v1/inventory` - List inventory items
- `POST /api/v1/inventory` - Create item
- `GET /api/v1/inventory/summary` - Inventory summary stats
- `GET /api/v1/inventory/categories` - List categories
- `GET /api/v1/inventory/alerts` - Low stock & expiration alerts
- `GET /api/v1/inventory/{id}` - Get item details
- `PUT /api/v1/inventory/{id}` - Update item
- `DELETE /api/v1/inventory/{id}` - Deactivate item

**Transactions:**
- `POST /api/v1/inventory/{id}/purchase` - Record purchase
- `POST /api/v1/inventory/{id}/adjust` - Adjust quantity
- `POST /api/v1/inventory/{id}/use` - Record usage
- `GET /api/v1/inventory/{id}/transactions` - Transaction history

**Total New Code:** ~4,600 lines

---

## Phase 5: Reporting & Analytics Dashboard

**Goal:** Provide insights and reports across all farm operations.

**Status:** 🔄 IN PROGRESS (December 18, 2025)

### Architecture

**Approach:** New ReportingService that aggregates from existing services:
- Leverages existing summary methods (get_operations_summary, get_equipment_summary, etc.)
- Adds date-range filtering and cross-functional aggregations
- Uses pyqtgraph for charts (already available)
- CSV export capability

### Report Tabs

**Tab 1: Operations Overview**
- Summary Cards: Total operations, Total cost, Avg cost/acre, Top operation type
- Bar chart: Operations by type
- Line chart: Costs over time (monthly)
- Table: Recent operations with filters

**Tab 2: Financial Analysis**
- Summary Cards: Total input costs, Equipment costs, Revenue (harvest), Net profit
- Pie chart: Cost breakdown by category
- Bar chart: Profit/loss by field
- Table: Cost details by field

**Tab 3: Equipment & Inventory**
- Summary Cards: Fleet value, Total hours, Items in stock, Low stock count
- Bar chart: Equipment utilization (hours)
- Bar chart: Inventory value by category
- Tables: Maintenance alerts, Low stock items

**Tab 4: Field Performance**
- Summary Cards: Total fields, Total acres, Avg yield, Best field
- Bar chart: Yield by field
- Table: Field summary with operations, costs, yields

### Implementation Checklist

**Backend:**
- [ ] Create `backend/services/reporting_service.py` (~600 lines)
  - [ ] get_operations_report(date_from, date_to, field_id)
  - [ ] get_financial_report(date_from, date_to)
  - [ ] get_equipment_report(date_from, date_to)
  - [ ] get_inventory_report()
  - [ ] get_field_performance_report(date_from, date_to)
  - [ ] export_report_csv(report_type, date_from, date_to)

- [ ] Add reporting endpoints to `backend/main.py` (7 endpoints)
  - [ ] GET /api/v1/reports/operations
  - [ ] GET /api/v1/reports/financial
  - [ ] GET /api/v1/reports/equipment
  - [ ] GET /api/v1/reports/inventory
  - [ ] GET /api/v1/reports/fields
  - [ ] GET /api/v1/reports/dashboard
  - [ ] POST /api/v1/reports/export/csv

**Frontend:**
- [ ] Create `frontend/api/reports_api.py` (~300 lines)
  - [ ] ReportsAPI class with methods for each endpoint
  - [ ] Dataclasses: OperationsReport, FinancialReport, etc.

- [ ] Create `frontend/ui/screens/reports_dashboard.py` (~1200 lines)
  - [ ] Date range selector (From/To)
  - [ ] Export CSV button
  - [ ] Tab 1: Operations Overview (cards + charts + table)
  - [ ] Tab 2: Financial Analysis (cards + charts + table)
  - [ ] Tab 3: Equipment & Inventory (cards + charts + tables)
  - [ ] Tab 4: Field Performance (cards + chart + table)

**Integration:**
- [ ] Update `frontend/ui/screens/__init__.py`
- [ ] Update `frontend/ui/sidebar.py` - Add Reports nav
- [ ] Update `frontend/ui/main_window.py` - Integrate screen
- [ ] Update `frontend/api/__init__.py`

### Files to Create/Modify

**New Files (3):**
1. `backend/services/reporting_service.py` (~600 lines)
2. `frontend/api/reports_api.py` (~300 lines)
3. `frontend/ui/screens/reports_dashboard.py` (~1200 lines)

**Modified Files (4):**
1. `backend/main.py` - Add 7 endpoints
2. `frontend/ui/screens/__init__.py` - Export screen
3. `frontend/ui/sidebar.py` - Add nav item
4. `frontend/ui/main_window.py` - Integrate screen

### Estimated Scope
- Backend: ~600 lines
- Frontend API: ~300 lines
- Frontend UI: ~1200 lines
- Integration: ~50 lines
- **Total: ~2,150 lines**

---

## Phase 6: Mobile/Crew Interface

**Goal:** Simple, mobile-friendly interface for field crews.

### Features (Preview)
- Responsive web view (works on phones)
- Simple task list view
- One-tap status updates
- Time logging
- Photo attachment for tasks
- Offline capability with sync

---

## Technical Notes

### Stack
- **Backend:** FastAPI (existing) + SQLite/PostgreSQL
- **Auth:** JWT tokens with python-jose
- **Frontend:** PyQt6 (desktop) + potential web interface
- **Mobile:** Responsive web initially, native app later if needed

### Migration Path
- SQLite for development/single-user
- PostgreSQL for production/multi-user SaaS

---

## Changelog

### December 18, 2025
- **Phase 4 COMPLETE**: Equipment & Inventory Tracking
- Added equipment fleet management (tractors, sprayers, planters, combines, etc.)
- Added maintenance scheduling with alerts (overdue, due soon, upcoming)
- Added inventory tracking for all farm inputs (seed, fertilizer, chemicals, fuel, parts)
- Added inventory transactions (purchases, usage, adjustments)
- Integrated equipment and inventory into operations log
- 24 new API endpoints
- ~4,600 new lines of code

### December 15, 2025
- **Phase 3 COMPLETE**: Field Operations & Logging
- Added field management (CRUD, attributes, stats)
- Added operations logging (10 operation types, costs, yields, weather)
- 14 new API endpoints (92 total)
- ~2,700 new lines of code

### December 12, 2025
- **Phase 2 COMPLETE**: Task Management Core
- Added task CRUD with status workflow
- Role-based access control for tasks
- 6 new API endpoints
- ~1,300 new lines of code

### December 11, 2025
- **Phase 1 COMPLETE**: User & Auth System
- Initial plan created
- Phase 1 detailed design and implementation
- JWT authentication, user/crew management
- 17 new API endpoints

