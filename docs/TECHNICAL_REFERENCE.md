# AgTools Technical Reference

Complete technical documentation for developers, system administrators, and integrators.

**Version:** 6.15.1 | **Updated:** January 2026

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Backend Structure](#backend-structure)
3. [API Reference](#api-reference)
4. [Authentication & Security](#authentication--security)
5. [Database Schema](#database-schema)
6. [GenFin Services](#genfin-services)
7. [Farm Operations Services](#farm-operations-services)
8. [AI/ML Services](#aiml-services)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## System Architecture

### Overview

AgTools follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│   │   Desktop    │    │   Mobile     │    │   Swagger    │              │
│   │   (PyQt6)    │    │   (PWA)      │    │   (OpenAPI)  │              │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘              │
│          │                   │                   │                       │
│          └───────────────────┼───────────────────┘                       │
│                              │                                           │
│                         HTTP/REST                                        │
│                              │                                           │
├──────────────────────────────┼──────────────────────────────────────────┤
│                         API LAYER                                        │
├──────────────────────────────┼──────────────────────────────────────────┤
│                              │                                           │
│   ┌──────────────────────────┴───────────────────────────────┐          │
│   │                    FastAPI Application                    │          │
│   │                                                           │          │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │          │
│   │  │   Routers   │  │ Middleware  │  │  Validation │       │          │
│   │  │  (825+ EP)  │  │ (Auth,Rate) │  │  (Pydantic) │       │          │
│   │  └─────────────┘  └─────────────┘  └─────────────┘       │          │
│   │                                                           │          │
│   └──────────────────────────┬───────────────────────────────┘          │
│                              │                                           │
├──────────────────────────────┼──────────────────────────────────────────┤
│                      BUSINESS LOGIC LAYER                                │
├──────────────────────────────┼──────────────────────────────────────────┤
│                              │                                           │
│   ┌──────────────────────────┴───────────────────────────────┐          │
│   │                    Service Registry                       │          │
│   │                                                           │          │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │          │
│   │  │  GenFin     │  │    Farm     │  │    AI/ML    │       │          │
│   │  │ (13 files)  │  │ Operations  │  │  Services   │       │          │
│   │  └─────────────┘  └─────────────┘  └─────────────┘       │          │
│   │                                                           │          │
│   └──────────────────────────┬───────────────────────────────┘          │
│                              │                                           │
├──────────────────────────────┼──────────────────────────────────────────┤
│                         DATA LAYER                                       │
├──────────────────────────────┼──────────────────────────────────────────┤
│                              │                                           │
│   ┌──────────────────────────┴───────────────────────────────┐          │
│   │                    SQLite / PostgreSQL                    │          │
│   │                                                           │          │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │          │
│   │  │   Users &   │  │    Farm     │  │   GenFin    │       │          │
│   │  │    Auth     │  │    Data     │  │  Accounting │       │          │
│   │  └─────────────┘  └─────────────┘  └─────────────┘       │          │
│   │                                                           │          │
│   └──────────────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | PyQt6 | Desktop application |
| **Mobile** | HTML/CSS/JS | Progressive Web App |
| **API** | FastAPI | REST API framework |
| **Validation** | Pydantic | Request/response validation |
| **Auth** | python-jose | JWT token handling |
| **Password** | bcrypt | Password hashing |
| **Database** | SQLite | Default data storage |
| **Database** | PostgreSQL | Optional production database |
| **Testing** | pytest | Test framework |

---

## Backend Structure

### Directory Layout

```
backend/
├── main.py                     # FastAPI application entry point
│                               # - 825+ API endpoints
│                               # - Application startup/shutdown
│                               # - Middleware configuration
│
├── routers/                    # API route handlers
│   ├── auth.py                 # Authentication endpoints
│   ├── genfin.py               # GenFin accounting routes
│   ├── fields.py               # Field management
│   ├── tasks.py                # Task management
│   ├── equipment.py            # Equipment tracking
│   ├── inventory.py            # Inventory management
│   └── ...                     # Additional routers
│
├── services/                   # Business logic (70+ modules)
│   │
│   │  # GenFin Accounting Services (13 files)
│   ├── genfin_core_service.py          # Accounts, journal entries, periods
│   ├── genfin_payables_service.py      # Vendors, bills, AP
│   ├── genfin_receivables_service.py   # Customers, invoices, AR
│   ├── genfin_banking_service.py       # Bank accounts, checks
│   ├── genfin_payroll_service.py       # Employees, pay runs
│   ├── genfin_reports_service.py       # Financial reports
│   ├── genfin_budget_service.py        # Budgets, forecasts
│   ├── genfin_inventory_service.py     # Items, costing
│   ├── genfin_class_service.py         # Classes, projects
│   ├── genfin_entity_service.py        # Multi-entity
│   ├── genfin_fixed_assets_service.py  # Depreciation
│   ├── genfin_bank_feeds_service.py    # Bank feed import
│   ├── genfin_ocr_service.py           # Receipt scanning
│   │
│   │  # Farm Operations Services
│   ├── field_service.py                # Field management
│   ├── field_operations_service.py     # Field activity logging
│   ├── task_service.py                 # Task management
│   ├── equipment_service.py            # Equipment tracking
│   ├── inventory_service.py            # Inventory management
│   ├── time_entry_service.py           # Time tracking
│   │
│   │  # Core Services
│   ├── auth_service.py                 # Authentication
│   ├── user_service.py                 # User management
│   ├── base_service.py                 # Service registry
│   │
│   │  # AI/ML Services
│   ├── pest_identification_service.py  # Pest/disease ID
│   ├── yield_prediction_service.py     # Yield ML models
│   ├── expense_categorization_service.py # Expense AI
│   └── ...
│
├── middleware/                 # Request middleware
│   ├── auth_middleware.py      # JWT validation
│   └── rate_limit.py           # Rate limiting
│
├── mobile/                     # Mobile web interface
│   └── templates/              # Jinja2 templates
│
└── templates/                  # HTML templates
```

### Service Registry Pattern

Services are managed through a central registry:

```python
# backend/services/base_service.py

class ServiceRegistry:
    """Singleton registry for service instances."""

    _services: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        """Register a service instance."""
        cls._services[name] = service

    @classmethod
    def get(cls, name: str) -> Any:
        """Get a registered service."""
        return cls._services.get(name)

    @classmethod
    def clear(cls) -> None:
        """Clear all services (for testing)."""
        cls._services.clear()
```

Usage:
```python
# Register a service
ServiceRegistry.register("field_service", FieldService(db_path))

# Get a service
field_service = ServiceRegistry.get("field_service")

# In tests, clear between tests
ServiceRegistry.clear()
```

---

## API Reference

### Endpoint Summary

| Category | Count | Base Path |
|----------|-------|-----------|
| Authentication | 15 | `/api/v1/auth` |
| Fields | 25 | `/api/v1/fields` |
| Tasks | 20 | `/api/v1/tasks` |
| Equipment | 30 | `/api/v1/equipment` |
| Inventory | 25 | `/api/v1/inventory` |
| GenFin Core | 50 | `/api/v1/genfin` |
| GenFin Banking | 40 | `/api/v1/genfin/bank-*` |
| GenFin Payroll | 35 | `/api/v1/genfin/employees`, `/payroll` |
| GenFin Reports | 60 | `/api/v1/genfin/reports` |
| AI/ML | 30 | `/api/v1/ai` |
| Seeds/Planting | 25 | `/api/v1/seeds`, `/planting` |
| Weather/Climate | 20 | `/api/v1/weather`, `/climate` |
| Sustainability | 25 | `/api/v1/sustainability` |
| Grants | 20 | `/api/v1/grants` |
| **Total** | **825+** | |

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login, returns JWT |
| POST | `/api/v1/auth/logout` | Invalidate session |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user info |
| PUT | `/api/v1/auth/me` | Update current user |
| POST | `/api/v1/auth/change-password` | Change password |
| GET | `/api/v1/auth/users` | List users (admin) |
| POST | `/api/v1/auth/users` | Create user (admin) |
| GET | `/api/v1/auth/users/{id}` | Get user (admin) |
| PUT | `/api/v1/auth/users/{id}` | Update user (admin) |
| DELETE | `/api/v1/auth/users/{id}` | Delete user (admin) |

### Field Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/fields` | List all fields |
| POST | `/api/v1/fields` | Create field |
| GET | `/api/v1/fields/{id}` | Get field details |
| PUT | `/api/v1/fields/{id}` | Update field |
| DELETE | `/api/v1/fields/{id}` | Delete field |
| GET | `/api/v1/fields/{id}/operations` | List field operations |
| POST | `/api/v1/fields/{id}/operations` | Log field operation |
| GET | `/api/v1/fields/{id}/statistics` | Get field statistics |
| GET | `/api/v1/fields/{id}/history` | Get field history |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks` | List tasks |
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks/{id}` | Get task |
| PUT | `/api/v1/tasks/{id}` | Update task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |
| POST | `/api/v1/tasks/{id}/assign` | Assign task |
| POST | `/api/v1/tasks/{id}/complete` | Mark complete |
| GET | `/api/v1/tasks/user/{user_id}` | Tasks by user |
| GET | `/api/v1/tasks/field/{field_id}` | Tasks by field |

### Equipment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/equipment` | List equipment |
| POST | `/api/v1/equipment` | Add equipment |
| GET | `/api/v1/equipment/{id}` | Get equipment |
| PUT | `/api/v1/equipment/{id}` | Update equipment |
| DELETE | `/api/v1/equipment/{id}` | Delete equipment |
| POST | `/api/v1/equipment/{id}/hours` | Log hours |
| GET | `/api/v1/equipment/{id}/hours` | Get hour history |
| POST | `/api/v1/equipment/{id}/maintenance` | Log maintenance |
| GET | `/api/v1/equipment/{id}/maintenance` | Get maintenance history |
| GET | `/api/v1/equipment/{id}/costs` | Get cost analysis |

### GenFin Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/genfin/accounts` | List accounts |
| POST | `/api/v1/genfin/accounts` | Create account |
| GET | `/api/v1/genfin/accounts/{id}` | Get account |
| PUT | `/api/v1/genfin/accounts/{id}` | Update account |
| DELETE | `/api/v1/genfin/accounts/{id}` | Delete account |
| GET | `/api/v1/genfin/accounts/{id}/ledger` | Account ledger |
| GET | `/api/v1/genfin/trial-balance` | Trial balance |
| GET | `/api/v1/genfin/journal-entries` | List entries |
| POST | `/api/v1/genfin/journal-entries` | Create entry |
| GET | `/api/v1/genfin/journal-entries/{id}` | Get entry |
| POST | `/api/v1/genfin/journal-entries/{id}/post` | Post entry |
| DELETE | `/api/v1/genfin/journal-entries/{id}` | Void entry |

### GenFin Vendor/Bill Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/genfin/vendors` | List vendors |
| POST | `/api/v1/genfin/vendors` | Create vendor |
| GET | `/api/v1/genfin/vendors/{id}` | Get vendor |
| PUT | `/api/v1/genfin/vendors/{id}` | Update vendor |
| DELETE | `/api/v1/genfin/vendors/{id}` | Delete vendor |
| GET | `/api/v1/genfin/bills` | List bills |
| POST | `/api/v1/genfin/bills` | Create bill |
| GET | `/api/v1/genfin/bills/{id}` | Get bill |
| PUT | `/api/v1/genfin/bills/{id}` | Update bill |
| POST | `/api/v1/genfin/bill-payments` | Pay bill |
| GET | `/api/v1/genfin/ap-aging` | AP aging report |

### GenFin Customer/Invoice Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/genfin/customers` | List customers |
| POST | `/api/v1/genfin/customers` | Create customer |
| GET | `/api/v1/genfin/customers/{id}` | Get customer |
| PUT | `/api/v1/genfin/customers/{id}` | Update customer |
| DELETE | `/api/v1/genfin/customers/{id}` | Delete customer |
| GET | `/api/v1/genfin/invoices` | List invoices |
| POST | `/api/v1/genfin/invoices` | Create invoice |
| GET | `/api/v1/genfin/invoices/{id}` | Get invoice |
| POST | `/api/v1/genfin/payment-receipts` | Record payment |
| GET | `/api/v1/genfin/ar-aging` | AR aging report |
| GET | `/api/v1/genfin/customer-statements/{id}` | Statement |

### GenFin Banking Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/genfin/bank-accounts` | List bank accounts |
| POST | `/api/v1/genfin/bank-accounts` | Create bank account |
| GET | `/api/v1/genfin/bank-accounts/{id}` | Get bank account |
| GET | `/api/v1/genfin/checks` | List checks |
| POST | `/api/v1/genfin/checks` | Create check |
| POST | `/api/v1/genfin/print-check` | Print single check |
| POST | `/api/v1/genfin/print-checks-batch` | Print batch |
| POST | `/api/v1/genfin/checks/{id}/void` | Void check |
| GET | `/api/v1/genfin/reconciliation/{id}` | Get reconciliation |
| POST | `/api/v1/genfin/reconciliation/{id}` | Save reconciliation |

### GenFin Payroll Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/genfin/employees` | List employees |
| POST | `/api/v1/genfin/employees` | Create employee |
| GET | `/api/v1/genfin/employees/{id}` | Get employee |
| PUT | `/api/v1/genfin/employees/{id}` | Update employee |
| GET | `/api/v1/genfin/payroll/schedules` | Pay schedules |
| POST | `/api/v1/genfin/payroll/schedules` | Create schedule |
| GET | `/api/v1/genfin/payroll/runs` | List pay runs |
| POST | `/api/v1/genfin/payroll/runs` | Create pay run |
| POST | `/api/v1/genfin/payroll/calculate` | Calculate payroll |
| POST | `/api/v1/genfin/payroll/generate-nacha` | Generate NACHA |

### GenFin Report Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/genfin/reports/profit-loss` | P&L statement |
| GET | `/api/v1/genfin/reports/balance-sheet` | Balance sheet |
| GET | `/api/v1/genfin/reports/cash-flow` | Cash flow |
| GET | `/api/v1/genfin/reports/financial-ratios` | Financial ratios |
| GET | `/api/v1/genfin/reports/general-ledger` | General ledger |
| GET | `/api/v1/genfin/reports/income-by-customer` | Revenue by customer |
| GET | `/api/v1/genfin/reports/expenses-by-vendor` | Spending by vendor |
| GET | `/api/v1/genfin/reports/budget-vs-actual` | Budget comparison |
| GET | `/api/v1/genfin/reports/catalog` | All available reports |
| POST | `/api/v1/genfin/reports/generate/{report_id}` | Run any report |

### AI/ML Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/identify/image` | AI pest ID from image |
| POST | `/api/v1/ai/identify/symptoms` | Symptom-based ID |
| GET | `/api/v1/ai/yield/predict` | Yield prediction |
| POST | `/api/v1/ai/expense/categorize` | Categorize expense |
| GET | `/api/v1/ai/health/ndvi/{field_id}` | NDVI analysis |

---

## Authentication & Security

### JWT Token Flow

```
1. Client sends credentials to /auth/login
   └── POST { username, password }

2. Server validates credentials
   └── Checks password hash against stored hash

3. Server generates tokens
   ├── Access Token (24 hour expiry)
   └── Refresh Token (7 day expiry)

4. Client stores tokens
   └── Secure storage (keychain, encrypted)

5. Client sends access token with requests
   └── Authorization: Bearer <token>

6. When access token expires
   └── POST /auth/refresh with refresh token
```

### Token Structure

```python
# Access Token Payload
{
    "sub": "user_id",
    "username": "admin",
    "role": "admin",
    "exp": 1704067200,
    "type": "access"
}

# Refresh Token Payload
{
    "sub": "user_id",
    "exp": 1704672000,
    "type": "refresh",
    "jti": "unique_token_id"
}
```

### User Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all features |
| `manager` | Manage operations, view reports |
| `crew` | Log time, update tasks |

### Password Requirements

- Minimum 8 characters
- Hashed with bcrypt (12 rounds)
- Truncated to 72 bytes (bcrypt limit)

### Security Best Practices

1. **Never share tokens** - Keep JWT tokens secure
2. **Use HTTPS** in production - Encrypt all traffic
3. **Change default password** - `admin123` is not secure
4. **Set SECRET_KEY** - Use environment variable
5. **Monitor audit log** - Track security events

---

## Database Schema

### Core Tables

```sql
-- Users and Authentication
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'crew',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL,
    refresh_token_hash VARCHAR(64),
    expires_at TIMESTAMP NOT NULL,
    refresh_expires_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Farm Operations Tables

```sql
CREATE TABLE fields (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    acres REAL,
    legal_description TEXT,
    latitude REAL,
    longitude REAL,
    soil_type VARCHAR(100),
    drainage_type VARCHAR(50),
    owner_name VARCHAR(100),
    rent_type VARCHAR(20),
    rent_amount REAL,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    field_id INTEGER REFERENCES fields(id),
    assigned_to INTEGER REFERENCES users(id),
    equipment_id INTEGER REFERENCES equipment(id),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    due_date DATE,
    estimated_hours REAL,
    actual_hours REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE equipment (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    serial_number VARCHAR(50),
    purchase_date DATE,
    purchase_price REAL,
    current_hours REAL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sku VARCHAR(50),
    category VARCHAR(50),
    quantity REAL DEFAULT 0,
    unit VARCHAR(20),
    cost_per_unit REAL,
    reorder_point REAL,
    location VARCHAR(100),
    supplier VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### GenFin Accounting Tables

```sql
CREATE TABLE genfin_accounts (
    id INTEGER PRIMARY KEY,
    number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,  -- asset, liability, equity, revenue, expense
    sub_type VARCHAR(50),
    description TEXT,
    balance REAL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    parent_id INTEGER REFERENCES genfin_accounts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE genfin_vendors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    terms VARCHAR(20) DEFAULT 'net_30',
    tax_id VARCHAR(20),
    is_1099 BOOLEAN DEFAULT FALSE,
    default_account_id INTEGER REFERENCES genfin_accounts(id),
    balance REAL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE genfin_customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    billing_address TEXT,
    shipping_address TEXT,
    terms VARCHAR(20) DEFAULT 'net_30',
    credit_limit REAL,
    tax_exempt BOOLEAN DEFAULT FALSE,
    default_account_id INTEGER REFERENCES genfin_accounts(id),
    balance REAL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE genfin_journal_entries (
    id INTEGER PRIMARY KEY,
    entry_date DATE NOT NULL,
    description TEXT,
    reference VARCHAR(50),
    is_posted BOOLEAN DEFAULT FALSE,
    is_adjusting BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP
);

CREATE TABLE genfin_journal_lines (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER REFERENCES genfin_journal_entries(id),
    account_id INTEGER REFERENCES genfin_accounts(id),
    debit REAL DEFAULT 0,
    credit REAL DEFAULT 0,
    memo TEXT
);
```

---

## GenFin Services

### Service File Reference

| Service | File | Lines | Description |
|---------|------|-------|-------------|
| Core | `genfin_core_service.py` | ~800 | Accounts, journal entries, fiscal periods |
| Payables | `genfin_payables_service.py` | ~900 | Vendors, bills, payments, AP |
| Receivables | `genfin_receivables_service.py` | ~850 | Customers, invoices, payments, AR |
| Banking | `genfin_banking_service.py` | ~700 | Bank accounts, checks, NACHA |
| Payroll | `genfin_payroll_service.py` | ~1000 | Employees, tax calculations, pay runs |
| Reports | `genfin_reports_service.py` | ~1200 | P&L, balance sheet, cash flow, ratios |
| Budget | `genfin_budget_service.py` | ~600 | Budgets, forecasts, scenarios |
| Inventory | `genfin_inventory_service.py` | ~750 | Items, FIFO/LIFO, assemblies |
| Class | `genfin_class_service.py` | ~500 | Classes, projects, billable items |
| Entity | `genfin_entity_service.py` | ~400 | Multi-entity management |
| Fixed Assets | `genfin_fixed_assets_service.py` | ~450 | Depreciation, asset tracking |
| Bank Feeds | `genfin_bank_feeds_service.py` | ~550 | OFX import, auto-matching |
| OCR | `genfin_ocr_service.py` | ~400 | Receipt scanning |

### Key Methods by Service

**genfin_core_service.py:**
- `create_account()` - Create chart of accounts entry
- `create_journal_entry()` - Create journal entry with lines
- `post_journal_entry()` - Post entry to GL
- `get_trial_balance()` - Generate trial balance
- `close_fiscal_period()` - Period close

**genfin_reports_service.py:**
- `get_profit_loss()` - Generate P&L statement
- `get_balance_sheet()` - Generate balance sheet
- `get_cash_flow()` - Generate cash flow statement
- `get_financial_ratios()` - Calculate key ratios

**genfin_payroll_service.py:**
- `create_employee()` - Add employee with W-4 info
- `calculate_payroll()` - Calculate wages and taxes
- `create_pay_run()` - Process pay run
- `generate_nacha_file()` - Create ACH file

---

## Farm Operations Services

### Field Service

```python
class FieldService:
    def create_field(self, field_data: FieldCreate) -> Field
    def get_field(self, field_id: int) -> Optional[Field]
    def list_fields(self, active_only: bool = True) -> List[Field]
    def update_field(self, field_id: int, data: FieldUpdate) -> Field
    def delete_field(self, field_id: int) -> bool
    def get_field_statistics(self, field_id: int) -> FieldStats
```

### Task Service

```python
class TaskService:
    def create_task(self, task_data: TaskCreate) -> Task
    def get_task(self, task_id: int) -> Optional[Task]
    def list_tasks(self, filters: TaskFilters) -> List[Task]
    def assign_task(self, task_id: int, user_id: int) -> Task
    def complete_task(self, task_id: int, actual_hours: float) -> Task
    def get_tasks_by_user(self, user_id: int) -> List[Task]
```

### Equipment Service

```python
class EquipmentService:
    def add_equipment(self, data: EquipmentCreate) -> Equipment
    def log_hours(self, equipment_id: int, hours: float, date: date) -> HourLog
    def log_maintenance(self, equipment_id: int, data: MaintenanceLog) -> Maintenance
    def get_cost_analysis(self, equipment_id: int) -> CostAnalysis
    def get_upcoming_maintenance(self) -> List[MaintenanceReminder]
```

---

## AI/ML Services

### Pest Identification

```python
class PestIdentificationService:
    def identify_from_symptoms(
        self,
        crop: str,
        symptoms: List[str]
    ) -> List[IdentificationResult]

    def identify_from_image(
        self,
        image_data: bytes
    ) -> List[IdentificationResult]

    def get_treatment_recommendations(
        self,
        pest_id: str
    ) -> List[TreatmentRecommendation]
```

### Yield Prediction

```python
class YieldPredictionService:
    def predict_yield(
        self,
        field_id: int,
        crop: str,
        planting_date: date,
        weather_data: WeatherData
    ) -> YieldPrediction
```

---

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific file
python -m pytest tests/test_genfin_endpoints.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Run single test
python -m pytest tests/test_auth.py::test_login -v
```

### Test Organization

| File | Tests | Focus |
|------|-------|-------|
| `conftest.py` | - | Fixtures and helpers |
| `test_critical_paths.py` | 20 | Core functionality |
| `test_auth_security.py` | 35 | Authentication |
| `test_genfin_endpoints.py` | 227 | GenFin accounting |
| `test_field_operations.py` | 40 | Farm operations |
| `test_equipment.py` | 30 | Equipment tracking |
| `test_inventory.py` | 25 | Inventory management |

### Key Fixtures

```python
@pytest.fixture
def client():
    """Fresh TestClient with isolated database."""
    # Sets up temporary database
    # Clears service registry
    # Returns FastAPI TestClient

@pytest.fixture
def auth_headers(client):
    """Get authenticated headers."""
    # Logs in as admin
    # Returns {"Authorization": "Bearer <token>"}

@pytest.fixture
def test_ids():
    """Module-scoped dict for sharing IDs between tests."""
    return {}

class DataFactory:
    """Generate test data."""

    @staticmethod
    def field() -> dict:
        return {
            "name": f"Field {uuid4().hex[:8]}",
            "acres": random.uniform(10, 500),
            ...
        }
```

### Test Environment

Tests automatically configure:
- `AGTOOLS_DEV_MODE=1` - Auto-login enabled
- `AGTOOLS_TEST_MODE=1` - Rate limiting disabled
- Temporary SQLite database

---

## Deployment

### Development

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### Production

```bash
# With gunicorn (Linux)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With uvicorn (any platform)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

```bash
# Required for production
export AGTOOLS_SECRET_KEY="your-secure-random-key"
export AGTOOLS_DB_PATH="/var/lib/agtools/production.db"

# Optional
export AGTOOLS_DEV_MODE=0
export AGTOOLS_TEST_MODE=0
```

### Database Options

**SQLite (default):**
- Single file, no setup
- Good for single-user
- Limited concurrent writes

**PostgreSQL (production):**
- Better concurrent access
- Full ACID compliance
- Set `DATABASE_URL` environment variable

---

## Troubleshooting

### Common Errors

**"Module not found"**
```bash
pip install -r requirements.txt
```

**"Address already in use"**
```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# Use different port
uvicorn main:app --port 8001
```

**"Database is locked"**
- SQLite allows one writer
- Close other connections
- Use PostgreSQL for multi-user

**"Token expired"**
- Access tokens expire in 24 hours
- Call `/auth/refresh` with refresh token
- Or login again

### Pydantic V2 Migration

The codebase uses Pydantic V2:

```python
# Model config (not class Config)
class MyModel(BaseModel):
    model_config = {"extra": "allow"}

# Serialization (not .dict())
data = model.model_dump()

# JSON (not .json())
json_str = model.model_dump_json()
```

### Datetime Handling

Use timezone-aware datetimes:

```python
from datetime import datetime, timezone

# Correct
now = datetime.now(timezone.utc)

# For SQLite
cursor.execute("INSERT ... VALUES (?)", (now.isoformat(),))
```

### Logging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

*AgTools Technical Reference v6.15.1*
*Copyright 2024-2026 New Generation Farms and William Brooks Parker. All Rights Reserved.*
