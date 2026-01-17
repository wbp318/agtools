# AgTools Technical Reference

> For the simple getting started guide, see the main [README.md](../README.md)

This document contains detailed technical documentation for developers and advanced users.

---

## System Architecture

```
agtools/
├── backend/           # FastAPI server (Python)
│   ├── main.py        # API application (825+ endpoints)
│   ├── services/      # Business logic services
│   ├── routers/       # API route handlers
│   ├── middleware/    # Auth, rate limiting
│   ├── mobile/        # Mobile web interface
│   └── templates/     # HTML templates
│
├── frontend/          # Desktop application (PyQt6)
│   ├── main.py        # Entry point
│   ├── api/           # API client modules
│   ├── ui/            # User interface screens
│   └── database/      # Local SQLite cache
│
├── database/          # Database schemas and seed data
│   ├── schema.sql     # PostgreSQL schema
│   ├── seed_data.py   # Pest/disease knowledge base
│   └── chemical_database.py  # Pesticide products
│
├── tests/             # Test suite (600+ tests)
│   ├── conftest.py    # pytest fixtures
│   └── test_*.py      # Test modules
│
└── docs/              # Documentation
```

---

## API Endpoints Overview

AgTools provides 825+ REST API endpoints organized into these categories:

### Core Features
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Authentication | `/api/v1/auth/*` | Login, logout, tokens, user info |
| Pest/Disease ID | `/api/v1/identify/*` | Symptom-based and AI image identification |
| Spray Recommendations | `/api/v1/recommend/*` | Product recommendations with economics |
| Weather | `/api/v1/weather/*` | Spray windows, conditions |

### Farm Operations
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Fields | `/api/v1/fields/*` | Field CRUD, boundaries, stats |
| Tasks | `/api/v1/tasks/*` | Task management, assignments |
| Equipment | `/api/v1/equipment/*` | Fleet tracking, maintenance |
| Inventory | `/api/v1/inventory/*` | Stock levels, transactions |
| Operations | `/api/v1/operations/*` | Field activity logging |

### Financial (GenFin)
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Accounts | `/api/v1/genfin/accounts` | Chart of accounts |
| Vendors | `/api/v1/genfin/vendors/*` | AP management |
| Customers | `/api/v1/genfin/customers/*` | AR management |
| Banking | `/api/v1/genfin/bank-accounts/*` | Bank accounts, checks |
| Payroll | `/api/v1/genfin/employees/*` | Employees, pay runs |
| Reports | `/api/v1/genfin/reports/*` | P&L, Balance Sheet, Cash Flow |

### AI/ML Features
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Image ID | `/api/v1/ai/identify/*` | AI pest/disease identification |
| Yield Prediction | `/api/v1/ai/yield/*` | ML yield forecasting |
| Crop Health | `/api/v1/ai/health/*` | NDVI analysis |
| Expense AI | `/api/v1/ai/expense/*` | Auto-categorization |

### Specialized Modules
| Category | Endpoints | Description |
|----------|-----------|-------------|
| Livestock | `/api/v1/livestock/*` | Animals, health, breeding |
| Seed/Planting | `/api/v1/seeds/*`, `/api/v1/planting/*` | Seed inventory, planting records |
| Climate | `/api/v1/climate/*` | GDD, precipitation, frost |
| Sustainability | `/api/v1/sustainability/*` | Carbon, practices |
| Research | `/api/v1/research/*` | Field trials, statistics |

Visit `http://localhost:8000/docs` for interactive API documentation.

---

## Knowledge Base

### Corn (23 Pests/Diseases)
**Pests:** Corn Rootworm, European Corn Borer, Western Bean Cutworm, Fall Armyworm, Black Cutworm, Corn Leaf Aphid, Spider Mites, Japanese Beetle, Stalk Borer, Corn Earworm

**Diseases:** Gray Leaf Spot, Northern/Southern Corn Leaf Blight, Common/Southern Rust, Tar Spot, Anthracnose, Eyespot, Goss's Wilt, Stewart's Wilt, Diplodia/Gibberella/Aspergillus Ear Rots

### Soybeans (23 Pests/Diseases)
**Pests:** Soybean Aphid, Spider Mites, Bean Leaf Beetle, Japanese Beetle, Grasshoppers, Stink Bugs, Dectes Stem Borer, Soybean Looper, Thistle Caterpillar, Grape Colaspis

**Diseases:** White Mold, SDS, SCN, Brown Stem Rot, Frogeye Leaf Spot, Septoria Brown Spot, Bacterial Blight, Cercospora Leaf Blight, Anthracnose, Phytophthora Root Rot, Soybean Rust, Charcoal Rot, Pod and Stem Blight

### Chemical Products (40+)
**Insecticides:** Pyrethroids (Brigade, Warrior II, Mustang Maxx), Diamides (Besiege, Coragen), Neonicotinoids (Actara, Assail)

**Fungicides:** Premixes (Trivapro, Delaro, Priaxor, Stratego YLD), QoIs (Quadris), Seed Treatments (ILeVO, ApronMaxx)

---

## Running Tests

```bash
# Run all tests
cd agtools
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_critical_paths.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html
```

**Test Files:**
| File | Tests | Focus |
|------|-------|-------|
| `test_critical_paths.py` | 20 | Core auth, CRUD, import/export |
| `test_auth_security.py` | 35 | JWT, roles, error handling |
| `test_genfin_endpoints.py` | 226 | GenFin accounting |
| Additional files | 300+ | Various features |

---

## Configuration

### Environment Variables
```
AGTOOLS_DEV_MODE=1        # Enable dev mode (auto-login)
AGTOOLS_TEST_MODE=1       # Enable test mode (no rate limiting)
AGTOOLS_DB_PATH=path.db   # Custom database path
```

### Settings File
The desktop app stores settings in `frontend/agtools_settings.json`:
```json
{
  "api_url": "http://localhost:8000",
  "theme": "light",
  "auto_sync": true
}
```

---

## Technology Stack

- **Backend:** FastAPI (Python 3.8+)
- **Frontend:** PyQt6 desktop application
- **Mobile:** Progressive Web App (PWA)
- **Database:** SQLite (default) or PostgreSQL
- **AI/ML:** scikit-learn, TensorFlow

---

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for detailed version history.

| Version | Highlights |
|---------|------------|
| 6.14.0 | Measurement converter, test fixes |
| 6.12.0 | 620+ tests, 98.9% pass rate |
| 6.10.0 | Export suite (CSV, Excel, PDF) |
| 6.4.0 | Livestock, seed & planting |
| 6.0.0 | GenFin accounting suite |
| 4.0.0 | Precision agriculture AI |
| 3.0.0 | AI/ML intelligence suite |
| 2.5.0 | Farm operations manager |
| 1.0.0 | Core pest/disease ID |

---

For more documentation:
- [CHANGELOG.md](../CHANGELOG.md) - Development history
- [QUICKSTART.md](../QUICKSTART.md) - Quick setup guide
- [docs/GENFIN.md](GENFIN.md) - Financial module guide
