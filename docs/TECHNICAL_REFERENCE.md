# AgTools Technical Reference

Comprehensive technical documentation for developers and system administrators.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Services Architecture](#services-architecture)
7. [Database Schema](#database-schema)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## System Overview

AgTools is a farm management platform consisting of:

- **Backend**: FastAPI server with 825+ REST API endpoints
- **Frontend**: PyQt6 desktop application
- **Mobile**: Progressive Web App for field crews
- **Database**: SQLite (default) or PostgreSQL

### Core Features

| Module | Description |
|--------|-------------|
| **Pest/Disease ID** | AI image recognition and symptom-based diagnosis for corn and soybeans |
| **Spray Recommendations** | Weather-smart application timing with ROI calculations |
| **Farm Operations** | Fields, tasks, equipment, and inventory management |
| **GenFin** | Complete accounting system with check printing and payroll |
| **AI/ML** | Yield prediction, expense categorization, crop health analysis |
| **Sustainability** | Carbon tracking, water usage, practice monitoring |

---

## Architecture

### Directory Structure

```
agtools/
├── backend/                 # FastAPI server (Python 3.8+)
│   ├── main.py             # Application entry point (825+ endpoints)
│   ├── services/           # Business logic (~70 service modules)
│   │   ├── genfin_*.py     # GenFin accounting (13 service files)
│   │   └── *_service.py    # Farm operations services
│   ├── routers/            # API route handlers
│   │   ├── auth.py         # Authentication routes
│   │   ├── genfin.py       # GenFin accounting routes
│   │   └── *.py            # Domain-specific routes
│   ├── middleware/         # Auth middleware, rate limiting
│   ├── mobile/             # Mobile web interface templates
│   └── templates/          # HTML templates
│
├── frontend/               # Desktop application (PyQt6)
│   ├── main.py            # Application entry point
│   ├── api/               # HTTP client modules
│   ├── ui/                # User interface screens
│   │   ├── main_window.py # Main application window
│   │   └── screens/       # Individual screen modules
│   └── database/          # Local SQLite cache
│
├── database/              # Database schemas and seed data
│   ├── schema.sql         # PostgreSQL schema
│   ├── seed_data.py       # Pest/disease knowledge base
│   └── chemical_database.py # Pesticide product data
│
├── tests/                 # Test suite (600+ tests)
│   ├── conftest.py        # pytest fixtures and DataFactory
│   ├── test_critical_paths.py
│   ├── test_auth_security.py
│   ├── test_genfin_endpoints.py
│   └── test_*.py          # Feature-specific tests
│
└── docs/                  # Documentation
    ├── TECHNICAL_REFERENCE.md
    └── guides/
        ├── QUICKSTART.md
        └── GENFIN.md
```

### Service Registry Pattern

Services use a `ServiceRegistry` pattern for dependency injection:

```python
from backend.services.base_service import ServiceRegistry

# Get a service instance
field_service = ServiceRegistry.get("field_service")

# Services are singletons per request context
# Clear for testing:
ServiceRegistry.clear()
```

Each service typically:
- Manages its own SQLite table(s)
- Exposes Pydantic models for request/response validation
- Follows consistent CRUD patterns

### GenFin Service Architecture

The GenFin accounting system consists of 13 specialized service files:

| Service File | Responsibility |
|-------------|----------------|
| `genfin_core_service.py` | Chart of accounts, journal entries, fiscal periods |
| `genfin_payables_service.py` | Vendors, bills, purchase orders, vendor credits |
| `genfin_receivables_service.py` | Customers, invoices, estimates, payments, credits |
| `genfin_banking_service.py` | Bank accounts, check printing, reconciliation |
| `genfin_payroll_service.py` | Employees, pay runs, tax calculations, NACHA files |
| `genfin_reports_service.py` | P&L, balance sheet, cash flow, financial ratios |
| `genfin_budget_service.py` | Budgets, forecasts, scenarios, cash projections |
| `genfin_inventory_service.py` | Items, FIFO/LIFO/average costing, assemblies |
| `genfin_class_service.py` | Classes, projects, billable time/expenses |
| `genfin_entity_service.py` | Multi-entity management |
| `genfin_fixed_assets_service.py` | Depreciation, asset tracking |
| `genfin_bank_feeds_service.py` | OFX import, auto-matching, feed management |
| `genfin_ocr_service.py` | Receipt/invoice scanning, data extraction |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### Backend Setup

```bash
# Clone or download the repository
git clone https://github.com/wbp318/agtools.git
cd agtools

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The server runs at `http://127.0.0.1:8000`. Access the interactive API docs at `/docs`.

### Frontend Setup (Optional)

```bash
cd frontend
pip install -r requirements.txt
python main.py
```

### Mobile Interface

Access the mobile crew interface at `http://localhost:8000/m/login` (requires backend running).

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGTOOLS_DEV_MODE` | `0` | Enable dev mode (auto-login, relaxed auth) |
| `AGTOOLS_TEST_MODE` | `0` | Enable test mode (no rate limiting) |
| `AGTOOLS_DB_PATH` | `agtools.db` | Custom database path |
| `AGTOOLS_SECRET_KEY` | (generated) | JWT signing key |

### Desktop App Settings

Settings stored in `frontend/agtools_settings.json`:

```json
{
  "api_url": "http://localhost:8000",
  "theme": "light",
  "auto_sync": true
}
```

---

## API Reference

### Endpoint Categories

AgTools provides 825+ REST API endpoints organized by domain:

#### Authentication (`/api/v1/auth/*`)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User login, returns JWT tokens |
| `/api/v1/auth/logout` | POST | Invalidate session |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Current user info |
| `/api/v1/auth/users` | GET/POST | User management (admin) |

#### Farm Operations
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Fields | `/api/v1/fields/*` | Field CRUD, boundaries, statistics |
| Tasks | `/api/v1/tasks/*` | Task management, assignments, status |
| Equipment | `/api/v1/equipment/*` | Fleet tracking, maintenance logs |
| Inventory | `/api/v1/inventory/*` | Stock levels, transactions |
| Operations | `/api/v1/operations/*` | Field activity logging |

#### GenFin Accounting (`/api/v1/genfin/*`)
| Category | Key Endpoints | Description |
|----------|---------------|-------------|
| Accounts | `/accounts`, `/journal-entries`, `/trial-balance` | Chart of accounts, GL |
| Vendors | `/vendors`, `/bills`, `/bill-payments`, `/ap-aging` | Accounts payable |
| Customers | `/customers`, `/invoices`, `/ar-aging`, `/statements` | Accounts receivable |
| Banking | `/bank-accounts`, `/checks`, `/reconciliation` | Banking operations |
| Payroll | `/employees`, `/pay-runs`, `/payroll/calculate` | Payroll processing |
| Reports | `/reports/profit-loss`, `/reports/balance-sheet`, `/reports/cash-flow` | Financial reports |

#### AI/ML Features (`/api/v1/ai/*`)
| Endpoint | Description |
|----------|-------------|
| `/api/v1/ai/identify/*` | AI pest/disease image identification |
| `/api/v1/ai/yield/*` | ML yield forecasting |
| `/api/v1/ai/health/*` | NDVI crop health analysis |
| `/api/v1/ai/expense/*` | Automatic expense categorization |

#### Specialized Modules
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Seeds/Planting | `/api/v1/seeds/*`, `/api/v1/planting/*` | Seed inventory, planting records |
| Climate | `/api/v1/climate/*` | GDD, precipitation, frost tracking |
| Sustainability | `/api/v1/sustainability/*` | Carbon footprint, practices |
| Research | `/api/v1/research/*` | Field trials, statistical analysis |
| Grants | `/api/v1/grants/*` | Grant management, compliance |

### Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI with all endpoints, request/response schemas, and try-it-out functionality.

---

## Database Schema

### Core Tables

```sql
-- Users and authentication
users (id, username, email, password_hash, role, is_active, created_at, last_login)
sessions (id, user_id, token_hash, expires_at, is_valid)
audit_log (id, user_id, action, entity_type, entity_id, details, ip_address, created_at)

-- Farm operations
fields (id, name, acres, location, crop_type, soil_type, is_active)
tasks (id, title, description, field_id, assigned_to, status, due_date, priority)
equipment (id, name, type, make, model, year, hours, status)
inventory (id, name, category, quantity, unit, cost_per_unit, reorder_point)

-- GenFin accounting
genfin_accounts (id, number, name, type, sub_type, balance, is_active)
genfin_vendors (id, name, contact, email, terms, is_1099, balance)
genfin_customers (id, name, contact, email, terms, credit_limit, balance)
genfin_bills (id, vendor_id, bill_number, date, due_date, amount, status)
genfin_invoices (id, customer_id, invoice_number, date, due_date, amount, status)
genfin_journal_entries (id, date, description, is_posted)
genfin_journal_lines (id, entry_id, account_id, debit, credit, memo)
```

### Data Isolation

- Each test uses a temporary SQLite database (`:memory:` or temp file)
- Services clear via `ServiceRegistry.clear()` between tests
- Production uses persistent SQLite or PostgreSQL

---

## Testing

### Running Tests

```bash
# Run all tests
cd agtools
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_critical_paths.py -v

# Run with coverage report
python -m pytest tests/ --cov=backend --cov-report=html

# Run only GenFin tests
python -m pytest tests/test_genfin_endpoints.py -v
```

### Test Organization

| File | Tests | Focus |
|------|-------|-------|
| `test_critical_paths.py` | 20 | Core auth, CRUD, import/export |
| `test_auth_security.py` | 35 | JWT tokens, roles, error handling |
| `test_genfin_endpoints.py` | 227 | GenFin accounting (comprehensive) |
| Additional files | 300+ | Various features |

### Test Fixtures

Key fixtures in `tests/conftest.py`:

```python
# Fresh test client per test
@pytest.fixture
def client():
    """TestClient with isolated database"""

# Authentication helpers
@pytest.fixture
def auth_token(client):
    """Get JWT token for test admin user"""

@pytest.fixture
def auth_headers(auth_token):
    """Authorization headers for authenticated requests"""

# Data generation
class DataFactory:
    """Generate test data for various entity types"""

    @staticmethod
    def field() -> dict:
        """Generate random field data"""

    @staticmethod
    def task() -> dict:
        """Generate random task data"""
```

### Test Environment

Tests automatically set:
- `AGTOOLS_DEV_MODE=1` - Enables auto-login
- `AGTOOLS_TEST_MODE=1` - Disables rate limiting

Default test credentials: `admin` / `admin123`

---

## Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure you're in the correct directory
cd backend
pip install -r requirements.txt
```

#### Port already in use
```bash
# Use a different port
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

#### Database locked (SQLite)
- Only one process can write at a time
- Check for other running instances
- For concurrent access, use PostgreSQL

#### JWT token expired
- Tokens expire after 24 hours
- Use the refresh token endpoint or re-login

### Pydantic V2 Patterns

The codebase uses Pydantic V2. Key patterns:

```python
# Model configuration
class MyModel(BaseModel):
    model_config = {"extra": "allow"}  # Not class Config

# Serialization
data = model.model_dump()  # Not .dict()
json_data = model.model_dump_json()  # Not .json()
```

### Datetime Handling

Use timezone-aware datetimes:

```python
from datetime import datetime, timezone

# Correct
now = datetime.now(timezone.utc)

# For SQLite storage
cursor.execute("INSERT INTO table (created_at) VALUES (?)",
               (now.isoformat(),))
```

---

## Knowledge Base

### Corn Pests & Diseases (23 total)

**Pests**: Corn Rootworm, European Corn Borer, Western Bean Cutworm, Fall Armyworm, Black Cutworm, Corn Leaf Aphid, Spider Mites, Japanese Beetle, Stalk Borer, Corn Earworm

**Diseases**: Gray Leaf Spot, Northern/Southern Corn Leaf Blight, Common/Southern Rust, Tar Spot, Anthracnose, Eyespot, Goss's Wilt, Stewart's Wilt, Diplodia/Gibberella/Aspergillus Ear Rots

### Soybean Pests & Diseases (23 total)

**Pests**: Soybean Aphid, Spider Mites, Bean Leaf Beetle, Japanese Beetle, Grasshoppers, Stink Bugs, Dectes Stem Borer, Soybean Looper, Thistle Caterpillar, Grape Colaspis

**Diseases**: White Mold, SDS, SCN, Brown Stem Rot, Frogeye Leaf Spot, Septoria Brown Spot, Bacterial Blight, Cercospora Leaf Blight, Anthracnose, Phytophthora Root Rot, Soybean Rust, Charcoal Rot, Pod and Stem Blight

### Chemical Products (40+)

**Insecticides**: Pyrethroids (Brigade, Warrior II, Mustang Maxx), Diamides (Besiege, Coragen), Neonicotinoids (Actara, Assail)

**Fungicides**: Premixes (Trivapro, Delaro, Priaxor, Stratego YLD), QoIs (Quadris), Seed Treatments (ILeVO, ApronMaxx)

---

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for complete version history.

| Version | Release | Highlights |
|---------|---------|------------|
| 6.15.1 | Jan 2026 | GenFin API consolidation, deprecation fixes |
| 6.14.0 | Jan 2026 | Measurement converter, test improvements |
| 6.12.0 | Jan 2026 | 620+ tests, 98.9% pass rate |
| 6.10.0 | Jan 2026 | Export suite (CSV, Excel, PDF) |
| 6.7.16 | Jan 2026 | Receipt/Invoice OCR |
| 6.6.0 | Dec 2025 | Print preview, import/export, bank feeds |
| 6.5.0 | Dec 2025 | 100% GenFin parity achieved |
| 6.4.0 | Dec 2025 | Seed & planting management |
| 6.0.0 | Dec 2025 | GenFin accounting suite |

---

*AgTools Technical Reference v6.15.1*
*Copyright 2024-2026 New Generation Farms. All Rights Reserved.*
