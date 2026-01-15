# Quick Start Guide - AgTools v6.10.0

Get up and running with AgTools in 5 minutes.

---

## What AgTools Does

AgTools is a **professional farm management platform** that helps you:

- **Identify pests & diseases** using AI image recognition or symptom checklists
- **Get spray recommendations** with economic threshold analysis and ROI calculations
- **Optimize input costs** for fertilizer, pesticides, irrigation, and labor
- **Track farm operations** including fields, equipment, inventory, and tasks
- **Manage finances** with GenFin (complete accounting, check printing, payroll)
- **Analyze data** with 50+ reports, sustainability metrics, and yield predictions
- **Export reports** to CSV, Excel, and PDF from all dashboards
- **Track crop costs** with per-acre cost analysis and ROI calculations

**Current Version:** 6.10.0 (January 2026) - Export Suite with CSV/Excel/PDF support

---

## Prerequisites

1. **Python 3.8+** - Download from https://python.org/downloads/
   - During installation, CHECK "Add Python to PATH"

2. **Git** (optional) - Download from https://git-scm.com/downloads

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
2. Click green "Code" button → "Download ZIP"
3. Extract to a folder

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies

```bash
cd ../frontend
pip install -r requirements.txt
```

---

## Running AgTools

### Start the Backend API

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Leave this terminal open. You'll see "Uvicorn running on http://127.0.0.1:8000"

### Start the Desktop Application

Open a **new terminal**:

```bash
cd frontend
python main.py
```

The desktop app opens with:
- Dashboard with quick actions
- Pest/Disease identification
- Spray timing optimizer
- Cost analysis tools
- Farm operations manager
- GenFin accounting system
- And much more...

### Access the Web API (Alternative)

Open your browser to: **http://localhost:8000/docs**

This shows the interactive API documentation with all 500+ endpoints.

### Mobile Crew Interface

For field crews on mobile devices: **http://localhost:8000/m/login**

---

## Quick Feature Overview

| Module | What It Does |
|--------|--------------|
| **Pest/Disease ID** | AI image recognition + symptom-based diagnosis |
| **Spray Timing** | Weather-smart application windows |
| **Cost Optimizer** | Fertilizer, irrigation, labor analysis |
| **Farm Operations** | Fields, tasks, equipment, inventory |
| **GenFin** | Full accounting, check printing, payroll |
| **Livestock** | Animals, health records, breeding, sales |
| **Seed & Planting** | Seed inventory, planting records, emergence |
| **Reports** | 50+ financial and operational reports |

---

## Default Login Credentials

For development/testing:
- **Username:** admin
- **Password:** admin123

*Note: Change these in production!*

---

## Offline Mode

The desktop app works offline automatically:
- Detects when API is unavailable
- Uses local SQLite cache
- Syncs when connection restores

---

## Next Steps

- **Detailed Documentation:** See [PROFESSIONAL_SYSTEM_GUIDE.md](PROFESSIONAL_SYSTEM_GUIDE.md)
- **GenFin Accounting:** See [GENFIN.md](GENFIN.md)
- **Farm Operations:** See [FARM_OPERATIONS_GUIDE.md](FARM_OPERATIONS_GUIDE.md)
- **API Reference:** http://localhost:8000/docs

---

## Getting Help

- **GitHub Issues:** https://github.com/wbp318/agtools/issues
- **API Docs:** http://localhost:8000/docs (when backend is running)

---

## Common Commands

```bash
# Start backend
cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Start frontend
cd frontend && python main.py

# Run tests
cd backend && python -m pytest tests/ -v

# Check API health
curl http://localhost:8000/
```

---

*AgTools v6.7.16 - Professional Farm Management Platform*
*Copyright © 2025-2026 New Generation Farms. All Rights Reserved.*
