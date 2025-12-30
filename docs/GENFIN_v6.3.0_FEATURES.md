# GenFin v6.3.0 - Payroll, Multi-Entity, Budgets & 1099 Tracking

**Release Date:** December 29, 2025
**Version:** 6.3.0

---

## New Features Overview

| Feature | Description |
|---------|-------------|
| **Payroll** | Complete payroll processing with tax calculations |
| **Multi-Entity** | Manage multiple farms/businesses in one system |
| **Budgeting** | Budget creation and variance analysis |
| **1099 Tracking** | Vendor 1099 payment tracking and form generation |

---

## 1. Payroll Service

Complete payroll management for farm employees.

### Features
- Employee management (hourly/salary, W-4 info)
- Federal tax withholding calculations (2024 brackets)
- State income tax calculations
- FICA (Social Security & Medicare)
- FUTA/SUTA employer taxes
- Pre-tax and post-tax deductions (401k, insurance, etc.)
- Pay runs with approval workflow
- Direct deposit via ACH
- Pay stubs with YTD tracking
- Tax liability reports

### Key Endpoints
```
GET  /api/v1/genfin/payroll/summary
GET  /api/v1/genfin/payroll/employees
POST /api/v1/genfin/payroll/employees
POST /api/v1/genfin/payroll/pay-runs
POST /api/v1/genfin/payroll/pay-runs/{id}/calculate
POST /api/v1/genfin/payroll/pay-runs/{id}/approve
POST /api/v1/genfin/payroll/pay-runs/{id}/process
GET  /api/v1/genfin/payroll/tax-liability
```

### Tax Calculations
- 2024 Federal tax brackets
- Social Security: 6.2% (up to $168,600)
- Medicare: 1.45% (+ 0.9% over $200k)
- FUTA: 0.6% (first $7,000)

---

## 2. Multi-Entity Service

Manage multiple farms, LLCs, or businesses under one system.

### Features
- Create and manage multiple entities
- Entity types: Farm, LLC, Corporation, S-Corp, Partnership, Trust
- Inter-entity transfers with tracking
- User access control per entity
- Entity switching
- Consolidated reporting across entities

### Key Endpoints
```
GET  /api/v1/genfin/entities/summary
GET  /api/v1/genfin/entities
POST /api/v1/genfin/entities
GET  /api/v1/genfin/entities/{id}
PUT  /api/v1/genfin/entities/{id}
POST /api/v1/genfin/entities/{id}/set-default
POST /api/v1/genfin/entities/transfer
GET  /api/v1/genfin/entities/transfers
GET  /api/v1/genfin/entities/consolidated
```

### Example: Create Entity
```python
POST /api/v1/genfin/entities
{
    "name": "North Farm",
    "entity_type": "llc",
    "legal_name": "North Farm Holdings LLC",
    "tax_id": "12-3456789",
    "state_of_formation": "IA"
}
```

---

## 3. Budgeting Service

Create budgets and track actual vs. budget performance.

### Features
- Annual, quarterly, monthly budgets
- Budget by account
- Variance analysis ($ and %)
- Rolling forecasts
- Budget vs. actual reports
- What-if scenario planning

### Key Endpoints
```
GET  /api/v1/genfin/budget/summary
GET  /api/v1/genfin/budget/list
POST /api/v1/genfin/budget/create
GET  /api/v1/genfin/budget/{id}
PUT  /api/v1/genfin/budget/{id}
GET  /api/v1/genfin/budget/{id}/variance
GET  /api/v1/genfin/budget/actual-vs-budget
```

---

## 4. 1099 Tracking Service

Complete 1099 management for vendor payments.

### Features
- Track 1099-eligible vendors
- Payment tracking by box type (NEC Box 1, MISC Box 1, etc.)
- Automatic threshold monitoring ($600 IRS threshold)
- 1099-NEC and 1099-MISC form generation
- Missing information detection
- Filing status tracking
- Form preparation for e-filing

### Key Endpoints
```
GET  /api/v1/genfin/1099/summary
GET  /api/v1/genfin/1099/year/{tax_year}
POST /api/v1/genfin/1099/payments
GET  /api/v1/genfin/1099/payments/{vendor_id}/{tax_year}
POST /api/v1/genfin/1099/generate
GET  /api/v1/genfin/1099/forms
GET  /api/v1/genfin/1099/forms/{form_id}
PUT  /api/v1/genfin/1099/forms/{form_id}
POST /api/v1/genfin/1099/forms/{form_id}/ready
POST /api/v1/genfin/1099/file
GET  /api/v1/genfin/1099/vendors-needing-forms/{tax_year}
GET  /api/v1/genfin/1099/missing-info/{tax_year}
```

### 1099 Workflow
1. Record payments to 1099-eligible vendors throughout year
2. At year-end, call `/generate` to create 1099 forms
3. Review forms at `/forms` and fill in missing info
4. Mark forms ready with `/ready`
5. After e-filing, record confirmation with `/file`

### Example: Record 1099 Payment
```python
POST /api/v1/genfin/1099/payments
{
    "vendor_id": "contractor_001",
    "amount": 2500.00,
    "payment_date": "2025-06-15",
    "form_type": "1099-NEC",
    "box_number": 1,
    "description": "Consulting services"
}
```

---

## API Documentation

All new endpoints are available in Swagger UI at:
```
http://localhost:8000/docs
```

Tags:
- `GenFin Entities` - Multi-entity management
- `GenFin 1099` - 1099 tracking and forms
- `GenFin Payroll` - Employee payroll
- `GenFin Budget` - Budgeting

---

## Database Tables

### Multi-Entity
- `genfin_entities` - Business entities
- `genfin_interentity_transactions` - Transfers between entities
- `genfin_entity_users` - User access control

### 1099 Tracking
- `genfin_1099_forms` - Generated 1099 forms
- `genfin_1099_payments` - Payment records for 1099
- `genfin_1099_batches` - Filing batches

### Payroll (in-memory for now)
- Employee records
- Pay runs
- Time entries
- Deductions

---

## Testing

Run the v6.3.0 smoke test:
```bash
cd backend
python smoke_test_v63.py
```

---

## Complete GenFin Feature List (v6.3.0)

| Version | Features |
|---------|----------|
| v6.1.0 | Chart of Accounts, Customers, Vendors, Invoices, Bills, Payments, Journal Entries, Reports |
| v6.2.0 | Recurring Transactions, Bank Feeds Import, Fixed Assets |
| v6.3.0 | Payroll, Multi-Entity, Budgets, 1099 Tracking |

GenFin is now a complete accounting system suitable for farm operations.

---

*GenFin v6.3.0 - AgTools Professional Accounting*
