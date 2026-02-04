# AgTools

A complete farm management system that helps farmers and crop consultants run their operations more efficiently.

---

## What Does AgTools Do?

AgTools is like having a digital assistant for your farm. It helps you:

- **Identify crop problems** - Take a photo of a sick plant or describe the symptoms, and AgTools tells you what's wrong and how to fix it
- **Plan spray applications** - Get recommendations on what products to use, when to spray, and how much it will cost
- **Track your fields** - Keep records of all your fields, what's planted, and what work has been done
- **Manage equipment** - Log hours, schedule maintenance, and track your fleet
- **Handle accounting** - Full bookkeeping with check printing, payroll, invoices, and financial reports
- **Organize your crew** - Assign tasks to workers and track their time

---

## How It Works (The Simple Version)

AgTools has three main parts that work together:

```
┌─────────────────────────────────────────────────────────────────┐
│                         YOUR DEVICES                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Desktop Computer          Phone/Tablet          Web Browser   │
│   ┌─────────────┐          ┌──────────┐          ┌──────────┐  │
│   │  Desktop    │          │  Mobile  │          │   API    │  │
│   │    App      │          │   App    │          │  Docs    │  │
│   │  (PyQt6)    │          │  (PWA)   │          │ (Swagger)│  │
│   └──────┬──────┘          └────┬─────┘          └────┬─────┘  │
│          │                      │                      │        │
│          └──────────────────────┼──────────────────────┘        │
│                                 │                                │
│                                 ▼                                │
│                    ┌────────────────────────┐                   │
│                    │      Backend Server     │                   │
│                    │       (FastAPI)         │                   │
│                    │                         │                   │
│                    │  • 825+ API endpoints   │                   │
│                    │  • Business logic       │                   │
│                    │  • Security & auth      │                   │
│                    └───────────┬─────────────┘                   │
│                                │                                 │
│                                ▼                                 │
│                    ┌────────────────────────┐                   │
│                    │       Database          │                   │
│                    │       (SQLite)          │                   │
│                    │                         │                   │
│                    │  • All your farm data   │                   │
│                    │  • Financial records    │                   │
│                    │  • User accounts        │                   │
│                    └────────────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**In Plain English:**

1. **You interact** through a desktop app, phone browser, or web interface
2. **The server** (backend) processes all your requests and handles the logic
3. **The database** stores everything safely on your computer

Everything runs locally on your machine - your data never leaves your computer unless you choose to share it.

---

## Quick Start

### Option A: Download Standalone Executable (Easiest)

1. Download `AgTools.exe` from [Releases](https://github.com/wbp318/agtools/releases)
2. Start the backend server (see Option B, Steps 1-3)
3. Run `AgTools.exe`

### Option B: Run from Source

#### Step 1: Install Python

Download Python 3.12+ from https://python.org/downloads and install it. **Check "Add Python to PATH"** during installation.

### Step 2: Download AgTools

```bash
git clone https://github.com/wbp318/agtools.git
cd agtools
```

Or download the ZIP from GitHub and extract it.

### Step 3: Start the Server

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Step 4: Open AgTools

- **API Explorer:** http://localhost:8000/docs
- **Mobile Interface:** http://localhost:8000/m/login

**First-time Setup:** Configure admin credentials via environment variables:
```bash
set AGTOOLS_ADMIN_USER=your_username
set AGTOOLS_ADMIN_PASS=your_password
```
Or create `backend/.credentials` file (see `backend/.credentials.example`).

---

## Features at a Glance

| Feature | What It Does |
|---------|--------------|
| **Pest & Disease ID** | Identify problems in corn and soybeans using photos or symptoms |
| **Spray Recommendations** | Get product suggestions with timing and cost analysis |
| **Field Management** | Track fields, crops, soil types, and boundaries |
| **Task Management** | Create and assign work orders to crew members |
| **Equipment Tracking** | Log hours, maintenance, and equipment status |
| **Inventory Control** | Track chemicals, seed, fuel, and parts |
| **GenFin Accounting** | Full double-entry bookkeeping with 50+ reports |
| **Check Printing** | Print checks directly with MICR encoding |
| **Payroll** | Calculate wages, taxes, and generate direct deposits |
| **Seed & Planting** | Track seed inventory and planting records |
| **Weather Integration** | Spray timing based on weather conditions |
| **AI Features** | Yield prediction, expense categorization, crop health |

---

## Project Structure

```
agtools/
├── backend/           ← The "brain" - handles all the logic
│   ├── main.py        ← Main application (825+ features)
│   ├── services/      ← Business logic (70+ modules)
│   └── routers/       ← API endpoints organized by feature
│
├── frontend/          ← Desktop application
│   ├── main.py        ← App launcher
│   └── ui/            ← User interface screens
│
├── database/          ← Data storage setup
│   ├── schema.sql     ← Database structure
│   └── seed_data.py   ← Pest/disease knowledge base
│
├── tests/             ← Quality assurance (1,042 tests)
│
└── docs/              ← Documentation
    ├── TECHNICAL_REFERENCE.md  ← Developer details
    └── guides/
        ├── QUICKSTART.md       ← Getting started
        └── GENFIN.md           ← Accounting guide
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Quick Start Guide](docs/guides/QUICKSTART.md) | Step-by-step setup instructions with all features explained |
| [Technical Reference](docs/TECHNICAL_REFERENCE.md) | Detailed architecture, API docs, and developer guide |
| [GenFin Accounting](docs/guides/GENFIN.md) | Complete guide to the financial management system |
| [Changelog](CHANGELOG.md) | Version history and updates |

---

## Technology

AgTools is built with modern, reliable technology:

- **Python** - The programming language (easy to read and maintain)
- **FastAPI** - Web framework (fast and well-documented)
- **SQLite** - Database (simple, no setup required)
- **PyQt6** - Desktop interface (native look and feel)
- **Pydantic** - Data validation (catches errors early)

---

## License

**Proprietary Software** - This code is shared publicly for demonstration purposes only.

Commercial use requires a license. See [LICENSE](LICENSE) for full terms.

Copyright 2024-2026 New Generation Farms and William Brooks Parker. All Rights Reserved.
