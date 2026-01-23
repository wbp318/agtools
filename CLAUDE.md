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

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

Tests use temporary SQLite databases for isolation. Key fixtures are in `tests/conftest.py`.

## Architecture

### Backend (`backend/`)
- **main.py**: FastAPI application with 825+ REST API endpoints
- **services/**: Business logic services (~70 service modules)
  - `genfin_*.py`: GenFin accounting services (payroll, banking, receivables, payables, reports, etc.)
  - `*_service.py`: Farm operations services (field, equipment, inventory, task, etc.)
- **routers/**: API route handlers organized by domain (auth, genfin, fields, equipment, etc.)
- **middleware/**: Auth middleware, rate limiting
- **mobile/**: Mobile web interface templates

### Frontend (`frontend/`)
- **main.py**: PyQt6 application entry point
- **api/**: HTTP client modules for backend communication
- **ui/**: User interface screens and widgets
  - `main_window.py`: Main application window
  - `screens/`: Individual screen modules
- **database/**: Local SQLite cache

### Services Architecture
Services use a `ServiceRegistry` pattern for dependency injection. Each service typically:
- Inherits from `base_service.py` patterns
- Has its own SQLite table(s)
- Exposes Pydantic models for request/response

### API Endpoint Structure
- `/api/v1/auth/*` - Authentication
- `/api/v1/fields/*`, `/api/v1/tasks/*`, `/api/v1/equipment/*`, `/api/v1/inventory/*` - Farm operations
- `/api/v1/genfin/*` - GenFin accounting (accounts, vendors, customers, banking, payroll, reports)
- `/api/v1/ai/*` - AI/ML features (pest ID, yield prediction, expense categorization)
- `/api/v1/seeds/*`, `/api/v1/planting/*` - Seed and planting management
- `/api/v1/sustainability/*` - Sustainability tracking (carbon, water, practices)
- `/api/v1/grants/*` - Grant management and compliance

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

## Key Patterns

- SQLite is the default database (PostgreSQL optional)
- Services clear and reinitialize via `ServiceRegistry.clear()` in tests
- GenFin services follow a consistent CRUD pattern with SQLite persistence
- Frontend uses httpx for async API calls with secure token storage
