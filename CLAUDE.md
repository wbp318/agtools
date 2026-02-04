# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgTools (v6.15.3) is a farm management system for crop consulting, pest identification, spray recommendations, financial tracking (GenFin), and farm operations. It consists of a FastAPI backend, PyQt6 desktop frontend, and mobile PWA interface.

**Requirements:** Python 3.12+

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

### Mobile Interface
Access at `http://localhost:8000/m/login` when backend is running.

### Building Standalone Executable
```bash
cd frontend
pip install -r requirements.txt
python build.py
```

This creates `dist/AgTools.exe` - a standalone Windows executable that users can download and run without Python installed. The backend server must still be running for full functionality.

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

Tests use temporary SQLite databases for isolation. Key fixtures are in `tests/conftest.py`. Use `test_db_path_module` for module-scoped database sharing when tests need shared state.

```bash
# Run frontend tests (requires PyQt6)
python -m pytest frontend/tests/ -v
```

### Linting
```bash
# Check backend
ruff check backend/

# Check frontend
ruff check frontend/

# Auto-fix issues
ruff check backend/ --fix
ruff check frontend/ --fix
```

Configuration is in `ruff.toml`. The linter catches undefined names, unused imports, and style issues.

## Architecture

### Backend (`backend/`)
- **main.py**: FastAPI application with 825+ REST API endpoints. Most GenFin endpoints are defined here with Pydantic request models.
- **routers/**: Supplementary route handlers organized by domain. Note: `genfin.py` router has rate-limited endpoints and some duplicates with main.py - main.py takes priority for Pydantic model endpoints.
- **services/**: Business logic services (~70 service modules)
  - `genfin_*.py`: GenFin accounting services (13 files)
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
- Has its own SQLite table(s) initialized in `_init_database()`
- Exposes Pydantic models for request/response
- Returns dictionaries from methods (not Pydantic models directly)
- Has a `MAX_LIMIT = 10000` cap on list queries to prevent memory exhaustion

Get services via factory functions (e.g., `get_field_service()`) which use `ServiceRegistry.get_service()` internally.

### API Endpoint Structure
- `/api/v1/auth/*` - Authentication
- `/api/v1/fields/*`, `/api/v1/tasks/*`, `/api/v1/equipment/*`, `/api/v1/inventory/*` - Farm operations
- `/api/v1/genfin/*` - GenFin accounting (accounts, vendors, customers, banking, payroll, reports)
- `/api/v1/ai/*` - AI/ML features (pest ID, yield prediction, expense categorization)
- `/api/v1/seeds/*`, `/api/v1/planting/*` - Seed and planting management
- `/api/v1/sustainability/*` - Sustainability tracking (carbon, water, practices)
- `/api/v1/grants/*` - Grant management and compliance

### GenFin Module Structure
GenFin is a full accounting system with 13 service files:
- `genfin_core_service.py` - Chart of accounts, journal entries, fiscal periods
- `genfin_receivables_service.py` - Customers, invoices, AR aging, payments
- `genfin_payables_service.py` - Vendors, bills, AP aging, bill payments
- `genfin_banking_service.py` - Bank accounts, checks, deposits, reconciliation
- `genfin_payroll_service.py` - Employees, pay schedules, pay runs, NACHA
- `genfin_reports_service.py` - P&L, balance sheet, cash flow, financial ratios
- `genfin_budget_service.py` - Budgets, forecasts, scenarios
- `genfin_inventory_service.py` - Items, FIFO/LIFO costing, assemblies
- `genfin_class_service.py` - Classes, projects, billable time
- `genfin_entity_service.py` - Multi-entity management
- `genfin_fixed_assets_service.py` - Depreciation, asset tracking
- `genfin_bank_feeds_service.py` - OFX import, transaction matching
- `genfin_advanced_reports_service.py` - Additional report types

## Environment Variables

- `AGTOOLS_DEV_MODE=1` - Enable dev mode (auto-login, relaxed auth)
- `AGTOOLS_TEST_MODE=1` - Enable test mode (no rate limiting)
- `AGTOOLS_DB_PATH=path.db` - Custom database path

## Testing Notes

- 1,042 tests total (810 backend + 232 frontend), 227 GenFin tests in `test_genfin_endpoints.py`
- Tests set `AGTOOLS_DEV_MODE=1` and `AGTOOLS_TEST_MODE=1` automatically
- Default test admin credentials: username `admin`, password `admin123`
- Use `DataFactory` class from `conftest.py` to generate test data
- The `client` fixture provides a fresh TestClient per test function
- The `auth_token` and `auth_headers` fixtures handle authentication
- `test_ids` fixture (function-scoped) provides a fresh dict per test; use class-level attributes if you need shared state across a test class
- Services clear and reinitialize via `ServiceRegistry.clear()` in tests

## Key Patterns

- SQLite is the default database (PostgreSQL optional)
- GenFin services follow a consistent CRUD pattern with SQLite persistence
- Frontend uses httpx for async API calls with secure token storage
- Pydantic V2 is used:
  - Use `model_dump()` not `.dict()`
  - Use `model_config = {"extra": "allow"}` not `class Config`
- Python 3.12+ datetime:
  - Use `datetime.now(timezone.utc)` not `datetime.utcnow()`
  - When passing datetime to SQLite queries, use `.isoformat()`
- Logging pattern for services:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.warning("Message: %s", variable)  # Use %s formatting, not f-strings
  ```

## Common Issues

### Duplicate Endpoints
Some endpoints exist in both `main.py` and `routers/genfin.py`. FastAPI routes to whichever is registered first. The `main.py` versions use Pydantic models; `genfin.py` versions may use Query params. Tests expect Pydantic model patterns.

### Response Format Mismatches
Services return dictionaries with various field names. Response models in routers should use `model_config = {"extra": "allow"}` and optional fields to handle variations.

### Test Data Dependencies
Test classes share `test_ids` fixture. Tests may fail when run in full suite but pass individually due to test ordering and data dependencies.

### SQLite Datetime
Always use `.isoformat()` when passing datetime objects to SQLite:
```python
cursor.execute("INSERT INTO table (created_at) VALUES (?)",
               (datetime.now(timezone.utc).isoformat(),))
```
