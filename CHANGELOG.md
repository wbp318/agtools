# AgTools Development Changelog

> **Current Version:** 6.5.1 | **Last Updated:** December 30, 2025

For detailed historical changes, see `docs/CHANGELOG_ARCHIVE.md`.

---

## v6.5.1 (December 30, 2025)

### Company Switcher & Write Checks Improvements

**New Features:**
- **Company/Entity Switcher** on GenFin home screen
  - Teal gradient bar with company dropdown
  - Seamlessly switch between multiple companies
  - "+ New Company" button with full entity creation dialog
  - Welcome message updates to reflect current company
- **Write Checks Dialog Overhaul**
  - Bank accounts load from Chart of Accounts API
  - Expense accounts use editable combos with auto-complete
  - Dynamic add/remove expense rows
  - Running total that auto-updates check amount
  - Delete button per expense line

---

## v6.5.0 (December 30, 2025)

### GenFin 100% Complete - Full QuickBooks Desktop Parity

**Major Milestone:** Zero placeholder screens remaining. Every GenFin feature is fully functional.

**New Screens (17 total):**

| Module | Screens Added |
|--------|---------------|
| Banking | Bank Accounts, Check Register, Transfers, Reconcile, Bank Feeds |
| Customer | Statements (email/print), Credit Memos |
| Vendor | Credit Cards, Vendor Credits |
| Payroll | Pay Liabilities (E-Pay), Employees tab in Payroll Center |
| Lists | Fixed Assets (depreciation), Recurring Transactions, Memorized Transactions |
| Other | Budgets, Entities (Classes/Locations/Names/Terms), Settings, Help Center |

**Stats:** `genfin.py` now ~8,500 lines | 35+ screen/dialog classes

---

## v6.4.0 (December 29, 2025)

### Farm Operations Suite - Modules 1 & 2

**Module 1: Livestock Management**
- Track cattle, hogs, poultry, sheep, goats
- Health records, breeding, weights, sales
- 20 new API endpoints

**Module 2: Seed & Planting**
- Seed inventory with trait packages
- Planting records, emergence tracking
- 15 new API endpoints

---

## v6.3.x (December 29, 2025)

### GenFin Advanced Features

- **v6.3.1** - 90s QuickBooks UI (teal theme, beveled 3D buttons)
- **v6.3.0** - Payroll (tax calculations), Multi-Entity, Budgets, 1099 Tracking

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 6.5.1 | Dec 30, 2025 | Company switcher, Write Checks improvements |
| 6.5.0 | Dec 30, 2025 | GenFin 100% complete (17 new screens) |
| 6.4.0 | Dec 29, 2025 | Farm Operations (Livestock, Seed & Planting) |
| 6.3.1 | Dec 29, 2025 | 90s QuickBooks teal UI theme |
| 6.3.0 | Dec 29, 2025 | Payroll, Multi-Entity, Budgets, 1099 |
| 6.2.0 | Dec 29, 2025 | Recurring transactions, Bank feeds, Fixed assets |
| 6.1.0 | Dec 29, 2025 | GenFin core (accounts, invoices, bills, reports) |
| 5.0.0 | Dec 29, 2025 | Professional crop consulting system |
| 4.3.0 | Dec 29, 2025 | Pest/disease identification AI |
| 3.x | Dec 27-28, 2025 | Equipment, inventory, task management |
| 2.x | Dec 19-26, 2025 | Field management, crew management |

---

## Roadmap

### v7.0.0 - Windows 95/98 Retro Theme (Planned)
- Excel 97 green theme for main AgTools screens
- Keep GenFin's teal QuickBooks theme
- Beveled 3D buttons, classic scrollbars, MS Sans Serif fonts

### v6.4.x - Farm Operations Continued
- Module 3: Harvest Management (scale tickets, yield analysis)
- Module 4: Soil & Fertility (soil tests, nutrient recommendations)
- Module 5: Crop Planning + FSA (rotations, PLC/ARC, CRP)

---

## Key Files Reference

| Component | File | Lines |
|-----------|------|-------|
| GenFin Accounting | `frontend/ui/screens/genfin.py` | ~8,500 |
| GenFin Styles | `frontend/ui/genfin_styles.py` | ~300 |
| Payroll Service | `backend/services/genfin_payroll_service.py` | ~2,000 |
| Livestock | `backend/services/livestock_service.py` | ~1,100 |
| Seed & Planting | `backend/services/seed_planting_service.py` | ~750 |
| Main API | `backend/main.py` | ~2,500 |
| Desktop Launcher | `start_agtools.pyw` | ~130 |

---

*For complete historical details, see `docs/CHANGELOG_ARCHIVE.md`*
