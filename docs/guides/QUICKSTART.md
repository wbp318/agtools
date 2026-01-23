# AgTools Quick Start Guide

Get up and running with AgTools in 5 minutes.

---

## What is AgTools?

AgTools is a **professional farm management platform** that helps you:

- **Identify pests & diseases** using AI image recognition or symptom checklists
- **Get spray recommendations** with economic threshold analysis and ROI calculations
- **Optimize input costs** for fertilizer, pesticides, irrigation, and labor
- **Track farm operations** including fields, equipment, inventory, and tasks
- **Manage finances** with GenFin (complete accounting, check printing, payroll)
- **Analyze data** with 50+ reports, sustainability metrics, and yield predictions
- **Export reports** to CSV, Excel, and PDF from all dashboards
- **Track crop costs** with per-acre cost analysis and ROI calculations

**Current Version:** 6.15.1 (January 2026)

---

## Prerequisites

### Required

- **Python 3.8 or higher** - Download from https://python.org/downloads/
  - During installation, **check "Add Python to PATH"**

### Optional

- **Git** - For cloning the repository (https://git-scm.com/downloads)

---

## Installation

### Step 1: Download the Code

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/wbp318/agtools.git
cd agtools
```

**Option B: Download ZIP**
1. Go to https://github.com/wbp318/agtools
2. Click green "Code" button
3. Click "Download ZIP"
4. Extract to a folder

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs FastAPI, SQLite support, authentication libraries, and other dependencies.

### Step 3: Install Frontend Dependencies (Optional)

For the desktop application:

```bash
cd ../frontend
pip install -r requirements.txt
```

---

## Running AgTools

### Start the Backend API Server

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Leave this terminal open. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Access Points

| Interface | URL | Description |
|-----------|-----|-------------|
| API Explorer | http://localhost:8000/docs | Interactive Swagger UI with all 825+ endpoints |
| Mobile Interface | http://localhost:8000/m/login | Field crew mobile web app |
| Health Check | http://localhost:8000/ | Server status |

### Start the Desktop Application (Optional)

Open a **new terminal**:

```bash
cd frontend
python main.py
```

The desktop app provides:
- Dashboard with quick actions
- Pest/Disease identification
- Spray timing optimizer
- Cost analysis tools
- Farm operations manager
- GenFin accounting system

---

## Default Login Credentials

For development and testing:
- **Username:** `admin`
- **Password:** `admin123`

**Important:** Change these credentials in production environments.

---

## Quick Feature Overview

| Module | Description |
|--------|-------------|
| **Pest/Disease ID** | AI image recognition + symptom-based diagnosis for corn and soybeans |
| **Spray Timing** | Weather-smart application windows with optimal timing recommendations |
| **Cost Optimizer** | Fertilizer, irrigation, and labor cost analysis with ROI calculations |
| **Farm Operations** | Fields, tasks, equipment, and inventory management |
| **GenFin** | Complete accounting: check printing, payroll, AP/AR, reports |
| **Seed & Planting** | Seed inventory, planting records, emergence tracking |
| **Reports** | 50+ financial and operational reports with export options |

---

## API Quick Reference

### Authentication

```bash
# Login to get a JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response includes access_token for subsequent requests
```

### Common Operations

```bash
# List all fields
curl http://localhost:8000/api/v1/fields \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create a task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Check irrigation", "priority": "high"}'

# Get financial reports
curl http://localhost:8000/api/v1/genfin/reports/profit-loss \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Offline Mode

The desktop application works offline automatically:
- Detects when the API server is unavailable
- Uses local SQLite cache for data
- Syncs changes when connection restores

---

## Environment Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGTOOLS_DEV_MODE` | `0` | Set to `1` for auto-login and relaxed auth |
| `AGTOOLS_TEST_MODE` | `0` | Set to `1` to disable rate limiting |
| `AGTOOLS_DB_PATH` | `agtools.db` | Custom database file path |

### Example: Development Mode

```bash
# Windows
set AGTOOLS_DEV_MODE=1
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Linux/Mac
AGTOOLS_DEV_MODE=1 python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

---

## Common Commands

```bash
# Start backend server
cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Start desktop frontend
cd frontend && python main.py

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Check API health
curl http://localhost:8000/
```

---

## Troubleshooting

### "Module not found" Error

```bash
cd backend
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Use a different port
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

### Database Locked

SQLite allows only one writer at a time. Close other instances or wait for operations to complete.

### Token Expired

Access tokens expire after 24 hours. Login again to get a new token.

---

## Next Steps

- **Technical Details:** See [TECHNICAL_REFERENCE.md](../TECHNICAL_REFERENCE.md) for architecture, API details, and database schema
- **GenFin Accounting:** See [GENFIN.md](GENFIN.md) for complete financial module documentation
- **API Documentation:** Visit http://localhost:8000/docs when the server is running
- **Changelog:** See [CHANGELOG.md](../../CHANGELOG.md) for version history

---

## Getting Help

- **GitHub Issues:** https://github.com/wbp318/agtools/issues
- **Interactive API Docs:** http://localhost:8000/docs (when server is running)
- **Technical Reference:** [TECHNICAL_REFERENCE.md](../TECHNICAL_REFERENCE.md)

---

*AgTools Quick Start Guide v6.15.1*
*Copyright 2024-2026 New Generation Farms. All Rights Reserved.*
