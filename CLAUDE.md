# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgTools is a farm management system for crop consulting, pest identification, spray recommendations, financial tracking (GenFin), and farm operations. It consists of a FastAPI backend and a PyQt6 desktop frontend.

## Build & Run Commands

### Backend (FastAPI Server)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend (PyQt6 Desktop App)
```bash
cd frontend
pip install -r requirements.txt
python main.py
```

### Running Tests
```bash
# Run all tests from project root
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_critical_paths.py -v

# Run a specific test class
python -m pytest tests/test_genfin_endpoints.py::TestAccounts -v

# Run a single test
python -m pytest tests/test_genfin_endpoints.py::TestAccounts::test_create_account -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

Tests use temporary SQLite databases for isolation. Key fixtures are in `tests/conftest.py`.

## Architecture

### Backend (`backend/`)
- **main.py**: FastAPI application with 825+ REST API endpoints. Most GenFin endpoints are defined here with Pydantic request models.
- **routers/**: Supplementary route handlers organized by domain. Note: `genfin.py` router has rate-limited endpoints and some duplicates with main.py - main.py takes priority for Pydantic model endpoints.
- **services/**: Business logic services (~70 service modules)
  - `genfin_*.py`: GenFin accounting services (payroll, banking, receivables, payables, reports, etc.)
  - `*_service.py`: Farm operations services (field, equipment, inventory, task, etc.)
  - `base_service.py`: Base class with common CRUD patterns and `ServiceRegistry` for dependency injection
- **middleware/**: Auth middleware, rate limiting
- **mobile/**: Mobile web interface templates (Jinja2)

### Frontend (`frontend/`)
- **main.py**: PyQt6 application entry point
- **api/**: HTTP client modules for backend communication
- **ui/**: User interface screens and widgets
- **database/**: Local SQLite cache

### Services Architecture
Services use a `ServiceRegistry` pattern for dependency injection. Each service typically:
- Inherits from `base_service.py` patterns
- Has its own SQLite table(s) initialized in `_init_tables()`
- Exposes Pydantic models for request/response
- Returns dictionaries from methods (not Pydantic models directly)

### API Endpoint Structure
- `/api/v1/auth/*` - Authentication
- `/api/v1/fields/*`, `/api/v1/tasks/*`, `/api/v1/equipment/*`, `/api/v1/inventory/*` - Farm operations
- `/api/v1/genfin/*` - GenFin accounting (accounts, vendors, customers, banking, payroll, reports)
- `/api/v1/ai/*` - AI/ML features (pest ID, yield prediction, expense categorization)
- `/api/v1/seeds/*`, `/api/v1/planting/*` - Seed and planting management
- `/api/v1/sustainability/*` - Sustainability tracking (carbon, water, practices)
- `/api/v1/grants/*` - Grant management and compliance

### GenFin Module Structure
GenFin is a full accounting system with these service files:
- `genfin_core_service.py` - Chart of accounts, journal entries
- `genfin_receivables_service.py` - Customers, invoices, AR aging
- `genfin_payables_service.py` - Vendors, bills, AP aging
- `genfin_banking_service.py` - Bank accounts, checks, deposits, ACH
- `genfin_payroll_service.py` - Employees, pay schedules, pay runs
- `genfin_reports_service.py` - P&L, balance sheet, cash flow
- `genfin_budget_service.py` - Budgets, forecasts, scenarios

## Environment Variables

- `AGTOOLS_DEV_MODE=1` - Enable dev mode (auto-login, relaxed auth)
- `AGTOOLS_TEST_MODE=1` - Enable test mode (no rate limiting)
- `AGTOOLS_DB_PATH=path.db` - Custom database path

## Testing Notes

- Tests set `AGTOOLS_DEV_MODE=1` and `AGTOOLS_TEST_MODE=1` automatically
- Default test admin credentials: username `admin`, password `admin123`
- Use `DataFactory` class from `conftest.py` to generate test data
- The `client` fixture provides a fresh TestClient per test function
- The `auth_token` and `auth_headers` fixtures handle authentication
- `test_ids` fixture (module-scoped) stores created entity IDs across tests within a file
- Services clear and reinitialize via `ServiceRegistry.clear()` in tests

## Key Patterns

- SQLite is the default database (PostgreSQL optional)
- GenFin services follow a consistent CRUD pattern with SQLite persistence
- Frontend uses httpx for async API calls with secure token storage
- Pydantic V2 is used - use `model_dump()` not `.dict()`, use `model_config = {"extra": "allow"}` not `class Config`
- Use `datetime.now(timezone.utc)` not `datetime.utcnow()` (deprecated in Python 3.12+)

## Common Issues

### Duplicate Endpoints
Some endpoints exist in both `main.py` and `routers/genfin.py`. FastAPI routes to whichever is registered first. The `main.py` versions use Pydantic models; `genfin.py` versions may use Query params. Tests expect Pydantic model patterns.

### Response Format Mismatches
Services return dictionaries with various field names. Response models in routers should use `model_config = {"extra": "allow"}` and optional fields to handle variations.

### Test Data Dependencies
Test classes share `test_ids` fixture. Tests may fail when run in full suite but pass individually due to test ordering and data dependencies.
