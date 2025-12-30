# GenFin - Complete Farm Financial Management System

*Version 6.0.0 | December 2025*

---

## Overview

**GenFin** is a complete farm-focused financial management system built into AgTools. It replaces the need for QuickBooks and other accounting software with features specifically designed for agricultural operations.

### Why GenFin?

- **Farm-Focused** - Chart of accounts and reports designed for agriculture
- **No Licensing Fees** - Replace QuickBooks subscriptions
- **Check Printing** - Built-in MICR check printing (replaces gcformer)
- **Direct Deposit** - NACHA file generation for ACH payments
- **Integrated** - Works seamlessly with all AgTools modules
- **Grant-Ready** - Financial reports formatted for grant applications

---

## Core Modules

### 1. Chart of Accounts & General Ledger

**60+ pre-configured farm accounts** organized by type:

| Account Type | Examples |
|--------------|----------|
| Assets | Checking, Savings, Accounts Receivable, Inventory, Equipment, Land |
| Liabilities | Accounts Payable, Operating Loans, Equipment Loans, Mortgages |
| Equity | Owner's Equity, Retained Earnings, Owner Draws |
| Revenue | Grain Sales, Custom Work, Government Payments |
| COGS | Seed, Fertilizer, Chemicals, Fuel |
| Expenses | Labor, Repairs, Insurance, Utilities, Rent |

**Features:**
- Custom account creation
- Account hierarchy support
- Active/inactive status
- Running balances
- Trial balance reports

### 2. Journal Entries

Full double-entry accounting with validation:

```
Example Entry:
Date: 2025-03-15
Description: Purchased seed for spring planting

Debit:  Seed Inventory      $45,000
Credit: Accounts Payable    $45,000
```

**Features:**
- Unlimited line items per entry
- Debits must equal credits (enforced)
- Memo and reference tracking
- Posted/draft status
- Audit trail

### 3. Fiscal Period Management

- Define fiscal years (calendar or custom)
- Month/quarter periods
- Period open/closed status
- Year-end close processing
- Retained earnings calculation

---

## Accounts Payable (Vendors & Bills)

### Vendor Management

| Field | Description |
|-------|-------------|
| Company Name | Vendor business name |
| Contact | Primary contact person |
| Address | Full mailing address |
| Phone/Email | Contact information |
| Tax ID | For 1099 reporting |
| 1099 Required | Yes/No for 1099 tracking |
| Default Account | Auto-fill expense account |
| Payment Terms | Net 10, Net 30, etc. |
| Credit Limit | Maximum outstanding balance |

### Bills & Payments

- **Bill Entry**: Line items with quantities, rates, accounts
- **Due Date Tracking**: Payment terms auto-calculate due dates
- **Partial Payments**: Apply payments to multiple bills
- **Payment Methods**: Check, ACH, credit card, cash
- **Bill History**: Complete payment history per bill

### Purchase Orders

- Create POs with line items
- Track ordered vs. received quantities
- Convert PO to bill when received
- Status: Pending, Partial, Complete, Cancelled

### AP Aging Report

| Aging Bucket | Description |
|--------------|-------------|
| Current | Not yet due |
| 1-30 Days | 1-30 days past due |
| 31-60 Days | 31-60 days past due |
| 61-90 Days | 61-90 days past due |
| 90+ Days | Over 90 days past due |

### 1099 Preparation

- Track 1099-eligible vendors
- Annual payment totals by vendor
- 1099-MISC and 1099-NEC support
- Export for tax preparation

---

## Accounts Receivable (Customers & Invoices)

### Customer Management

| Field | Description |
|-------|-------------|
| Customer Name | Individual or business |
| Billing Address | Invoice address |
| Shipping Address | Delivery address |
| Contact | Primary contact |
| Phone/Email | Contact information |
| Payment Terms | Net 10, Net 30, etc. |
| Credit Limit | Maximum credit extended |
| Tax Exempt | Yes/No with certificate |
| Default Account | Auto-fill income account |

### Invoices

- Professional invoice creation
- Line items with descriptions
- Quantity and unit pricing
- Tax calculation support
- Due date and terms
- Partial payment tracking
- Status: Draft, Sent, Paid, Partial, Overdue

### Estimates & Quotes

- Create estimates for potential work
- Convert to invoice when approved
- Expiration date tracking
- Status: Pending, Accepted, Rejected, Expired

### Payment Receipts

- Record customer payments
- Apply to specific invoices
- Partial payment support
- Multiple payment methods
- Overpayment handling

### Customer Credits

- Issue credit memos
- Apply to invoices or refund
- Track unapplied credits

### AR Aging Report

Same aging buckets as AP, organized by customer.

### Customer Statements

- Generate monthly statements
- Transaction detail
- Balance forward format
- Aging summary included

---

## Banking & Check Printing

### Bank Account Management

| Account Type | Description |
|--------------|-------------|
| Checking | Operating accounts |
| Savings | Reserve accounts |
| Credit Card | Business credit cards |
| Line of Credit | Operating lines |
| Money Market | Investment accounts |

**Features:**
- Routing and account numbers
- Opening balance tracking
- Current balance calculation
- Active/inactive status

### CHECK PRINTING (Key Feature)

**Replaces gcformer** with native check printing:

#### Supported Check Formats

| Format | Description |
|--------|-------------|
| QuickBooks Standard | Standard QB check layout |
| QuickBooks Voucher | 3-up voucher format |
| Standard Top | Check at top of page |
| Standard Middle | Check in middle |
| Standard Bottom | Check at bottom |
| Wallet | Wallet-size checks |
| 3-Per-Page | Three checks per page |

#### Check Data Generated

```
Check #: 1234
Date: December 29, 2025
Pay to: ABC Farm Supply
Amount: $12,450.00
Written: Twelve Thousand Four Hundred Fifty and 00/100 DOLLARS

MICR Line: ⑆123456789⑆ ⑈1234567890⑈ 1234
```

#### Features

- **MICR Line Generation**: Proper formatting for bank processing
- **Number-to-Words**: Automatic amount conversion
- **Batch Printing**: Print multiple checks at once
- **Check Number Tracking**: Automatic sequencing
- **Void Check Support**: Track voided checks
- **Reprint Capability**: Reprint if needed
- **Address for Window Envelopes**: Proper positioning

### ACH / Direct Deposit

Generate NACHA-format files for:
- **Payroll Direct Deposits** (PPD)
- **Vendor Payments** (CCD)
- **Customer Collections** (CCD Debit)

#### NACHA File Generation

```
File Header Record
Batch Header Record (PPD - Payroll)
  Entry Detail (Employee 1 - Credit)
  Entry Detail (Employee 2 - Credit)
  Entry Detail (Employee 3 - Credit)
Batch Control Record
File Control Record
```

**Features:**
- Industry-standard format (all banks accept)
- Immediate, next-day, or two-day settlement
- Addenda records for details
- Batch totals and hash verification
- Ready for bank upload

### Bank Reconciliation

- Enter statement balance and date
- Match cleared transactions
- Identify outstanding checks/deposits
- Calculate reconciled balance
- Flag discrepancies

---

## Payroll

### Employee Management

| Field | Description |
|-------|-------------|
| Name | First and last name |
| SSN | Social Security Number (encrypted) |
| Address | Mailing address |
| Hire Date | Employment start date |
| Department | Organizational unit |
| Pay Type | Hourly, Salary, Commission |
| Pay Rate | Hourly rate or annual salary |
| Direct Deposit | Bank account info |

### Tax Withholding (W-4)

- Federal filing status (Single, Married, Head of Household)
- Allowances/dependents claimed
- Additional federal withholding
- State filing status
- State allowances
- Additional state withholding

### Time Tracking

- Time entries by employee
- Regular and overtime hours
- Pay period tracking
- Approval workflow

### Pay Run Processing

**Automatic Calculations:**

| Tax | Rate | Notes |
|-----|------|-------|
| Federal Income | Bracketed | 2024 tax tables |
| Social Security | 6.2% | Up to $168,600 wage base |
| Medicare | 1.45% | Plus 0.9% over $200k |
| State Income | Varies | State-specific rates |
| FUTA | 6.0% | With 5.4% credit = 0.6% |
| SUTA | Varies | State unemployment |

**Pay Run Output:**
- Gross pay (hours x rate or salary)
- Overtime (1.5x for hours > 40)
- All tax withholdings
- Deductions
- Net pay

### Payment Integration

- Generate paychecks (check printing)
- Generate direct deposit file (NACHA)
- Pay stub data

---

## Financial Reports

### Profit & Loss Statement

```
REVENUE
  Grain Sales                    $850,000
  Custom Work                     $45,000
  Government Payments             $35,000
  TOTAL REVENUE                  $930,000

COST OF GOODS SOLD
  Seed                           $125,000
  Fertilizer                     $180,000
  Chemicals                       $95,000
  TOTAL COGS                     $400,000

GROSS PROFIT                     $530,000

OPERATING EXPENSES
  Labor                          $120,000
  Equipment Repairs               $45,000
  Fuel                            $65,000
  Insurance                       $28,000
  TOTAL OPERATING                $258,000

NET OPERATING INCOME             $272,000

Other Income/Expense
  Interest Income                  $2,000
  Interest Expense               ($35,000)
  TOTAL OTHER                    ($33,000)

NET PROFIT                       $239,000
```

**Features:**
- Date range selection
- Prior period comparison
- Prior year comparison
- Percentage of revenue

### Balance Sheet

```
ASSETS
  Current Assets
    Checking                     $125,000
    Savings                      $250,000
    Accounts Receivable           $45,000
    Inventory                    $180,000
    TOTAL CURRENT                $600,000

  Fixed Assets
    Equipment                    $850,000
    Land                       $2,400,000
    Buildings                    $350,000
    Less: Depreciation          ($420,000)
    TOTAL FIXED                $3,180,000

TOTAL ASSETS                   $3,780,000

LIABILITIES
  Current Liabilities
    Accounts Payable              $85,000
    Operating Loan               $150,000
    TOTAL CURRENT                $235,000

  Long-Term Liabilities
    Equipment Loans              $320,000
    Mortgage                     $980,000
    TOTAL LONG-TERM            $1,300,000

TOTAL LIABILITIES              $1,535,000

EQUITY
  Owner's Equity               $1,800,000
  Retained Earnings              $445,000
TOTAL EQUITY                   $2,245,000

TOTAL LIABILITIES + EQUITY     $3,780,000
```

### Cash Flow Statement

- Operating activities (receipts, payments)
- Investing activities (equipment, land)
- Financing activities (loans, draws)
- Net change in cash
- Beginning/ending cash balance

### Financial Ratios

| Ratio | Formula | What It Means |
|-------|---------|---------------|
| Current Ratio | Current Assets / Current Liabilities | Ability to pay short-term debts |
| Quick Ratio | (Cash + AR) / Current Liabilities | Immediate liquidity |
| Debt-to-Equity | Total Debt / Equity | Leverage level |
| Gross Margin | Gross Profit / Revenue | Production efficiency |
| Net Margin | Net Income / Revenue | Overall profitability |
| ROA | Net Income / Total Assets | Asset efficiency |
| ROE | Net Income / Equity | Return to owners |

### Additional Reports

- **General Ledger**: Transaction detail by account
- **Income by Customer**: Revenue breakdown
- **Expenses by Vendor**: Spending breakdown
- **Transaction History**: Full audit trail

---

## Budgeting & Forecasting

### Budget Creation

| Budget Type | Description |
|-------------|-------------|
| Annual | Full year budget |
| Quarterly | Q1, Q2, Q3, Q4 |
| Monthly | 12 monthly budgets |

**Features:**
- Budget by account
- Notes and assumptions
- Multiple budget versions

### Budget vs. Actual

```
Account          Budget    Actual    Variance    %
Seed            $125,000  $128,500   ($3,500)   -2.8%
Fertilizer      $180,000  $172,000    $8,000     4.4%
Chemicals        $95,000   $98,200   ($3,200)   -3.4%
Labor           $120,000  $115,000    $5,000     4.2%
```

**Variance Indicators:**
- Favorable (under budget)
- Unfavorable (over budget)
- Percentage variance

### Financial Forecasting

**Forecast Methods:**

| Method | Description |
|--------|-------------|
| Trend | Based on growth rate |
| Average | Historical average |
| Seasonal | Monthly adjustment factors |

**12-Month Projections:**
- Revenue forecasts
- Expense forecasts
- Cash flow projections
- Confidence intervals

### Scenario Planning

Create what-if scenarios:

```
Scenario: "Corn Price Drop"
  Revenue Growth: -15%
  Expense Change: 0%

  Projected Impact:
    Revenue: $930,000 -> $790,500
    Net Income: $239,000 -> $99,500
```

**Features:**
- Compare scenarios side-by-side
- Adjust multiple assumptions
- Impact analysis

### Cash Flow Projections

- Project cash position forward
- Include budgeted income/expenses
- Identify potential shortfalls
- Plan for capital needs

---

## API Endpoints

### GenFin Core
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/accounts` | GET/POST | Chart of accounts |
| `/api/v1/genfin/accounts/{id}` | GET/PUT/DELETE | Account CRUD |
| `/api/v1/genfin/accounts/{id}/ledger` | GET | Account ledger |
| `/api/v1/genfin/journal-entries` | GET/POST | Journal entries |
| `/api/v1/genfin/trial-balance` | GET | Trial balance |
| `/api/v1/genfin/fiscal-periods` | GET/POST | Fiscal periods |
| `/api/v1/genfin/close-year` | POST | Year-end close |

### GenFin Payables
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/vendors` | GET/POST | Vendor management |
| `/api/v1/genfin/bills` | GET/POST | Bill management |
| `/api/v1/genfin/bill-payments` | POST | Record payments |
| `/api/v1/genfin/vendor-credits` | GET/POST | Vendor credits |
| `/api/v1/genfin/purchase-orders` | GET/POST | Purchase orders |
| `/api/v1/genfin/ap-aging` | GET | AP aging report |
| `/api/v1/genfin/1099-summary` | GET | 1099 preparation |

### GenFin Receivables
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/customers` | GET/POST | Customer management |
| `/api/v1/genfin/invoices` | GET/POST | Invoice management |
| `/api/v1/genfin/estimates` | GET/POST | Estimates/quotes |
| `/api/v1/genfin/sales-receipts` | POST | Sales receipts |
| `/api/v1/genfin/payment-receipts` | POST | Payment receipts |
| `/api/v1/genfin/customer-credits` | GET/POST | Customer credits |
| `/api/v1/genfin/ar-aging` | GET | AR aging report |
| `/api/v1/genfin/customer-statement` | GET | Customer statements |
| `/api/v1/genfin/sales-summary` | GET | Sales summary |

### GenFin Banking
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/bank-accounts` | GET/POST | Bank accounts |
| `/api/v1/genfin/bank-transactions` | GET/POST | Transactions |
| `/api/v1/genfin/print-check` | POST | **Print single check** |
| `/api/v1/genfin/print-checks-batch` | POST | **Print batch** |
| `/api/v1/genfin/ach-batch` | POST | Create ACH batch |
| `/api/v1/genfin/generate-nacha` | POST | **Generate NACHA file** |
| `/api/v1/genfin/reconciliation` | GET/POST | Bank reconciliation |

### GenFin Payroll
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/employees` | GET/POST | Employee management |
| `/api/v1/genfin/time-entries` | GET/POST | Time tracking |
| `/api/v1/genfin/pay-runs` | GET/POST | Pay runs |
| `/api/v1/genfin/calculate-payroll` | POST | Calculate payroll |

### GenFin Reports
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/reports/profit-loss` | GET | P&L statement |
| `/api/v1/genfin/reports/balance-sheet` | GET | Balance sheet |
| `/api/v1/genfin/reports/cash-flow` | GET | Cash flow statement |
| `/api/v1/genfin/reports/financial-ratios` | GET | Financial ratios |
| `/api/v1/genfin/reports/general-ledger` | GET | GL report |
| `/api/v1/genfin/reports/income-by-customer` | GET | Customer income |
| `/api/v1/genfin/reports/expenses-by-vendor` | GET | Vendor expenses |

### GenFin Budget
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/genfin/budgets` | GET/POST | Budget management |
| `/api/v1/genfin/budgets/vs-actual` | GET | Budget vs actual |
| `/api/v1/genfin/forecasts` | GET/POST | Forecasts |
| `/api/v1/genfin/forecasts/project` | POST | Generate projections |
| `/api/v1/genfin/scenarios` | GET/POST | Scenario planning |
| `/api/v1/genfin/scenarios/compare` | POST | Compare scenarios |
| `/api/v1/genfin/cash-projection` | GET | Cash projection |

---

## Getting Started

### 1. Set Up Chart of Accounts

The system comes with 60+ pre-configured farm accounts. Review and customize:

```bash
GET /api/v1/genfin/accounts
```

Add custom accounts as needed:

```json
POST /api/v1/genfin/accounts
{
  "number": "6100",
  "name": "Custom Harvesting",
  "type": "expense",
  "sub_type": "operating",
  "description": "Custom harvest services"
}
```

### 2. Add Vendors

Enter your suppliers and service providers:

```json
POST /api/v1/genfin/vendors
{
  "name": "ABC Farm Supply",
  "contact": "John Smith",
  "email": "john@abcfarm.com",
  "phone": "555-123-4567",
  "address": "123 Main St",
  "terms": "net_30",
  "is_1099": true,
  "default_account_id": "5100"
}
```

### 3. Add Customers

Enter your grain buyers and custom work customers:

```json
POST /api/v1/genfin/customers
{
  "name": "Local Grain Elevator",
  "contact": "Jane Doe",
  "email": "jane@elevator.com",
  "terms": "net_10",
  "default_account_id": "4100"
}
```

### 4. Set Up Bank Accounts

Add your operating and savings accounts:

```json
POST /api/v1/genfin/bank-accounts
{
  "name": "Farm Operating",
  "type": "checking",
  "account_number": "1234567890",
  "routing_number": "123456789",
  "opening_balance": 50000.00
}
```

### 5. Configure Check Printing

Set your starting check number and preferred format:

```json
POST /api/v1/genfin/print-check
{
  "bank_account_id": "bank_1",
  "check_number": 1001,
  "payee": "ABC Farm Supply",
  "amount": 5000.00,
  "memo": "Invoice #12345",
  "format": "quickbooks_voucher"
}
```

### 6. Add Employees (For Payroll)

```json
POST /api/v1/genfin/employees
{
  "first_name": "Bob",
  "last_name": "Johnson",
  "ssn": "123-45-6789",
  "pay_type": "hourly",
  "pay_rate": 18.00,
  "federal_filing_status": "married",
  "federal_allowances": 2,
  "direct_deposit": true,
  "bank_name": "First National",
  "routing_number": "123456789",
  "account_number": "9876543210"
}
```

---

## Integration with AgTools

GenFin integrates with other AgTools modules:

| Module | Integration |
|--------|-------------|
| Field Operations | Auto-create bills for field operations |
| Inventory | Track inventory purchases and usage |
| Equipment | Equipment purchase and depreciation |
| Grain Storage | Grain sales invoicing |
| Enterprise Ops | Payroll for employees |
| Cost Tracking | Expense categorization |

---

## Migration from QuickBooks

### Importing Historical Data

1. Export transactions from QuickBooks
2. Use existing QuickBooks Import (v2.9)
3. Map accounts to GenFin chart of accounts
4. Review and post imported transactions

### Setting Opening Balances

For each account, set the opening balance as of your migration date:

```json
POST /api/v1/genfin/journal-entries
{
  "date": "2025-01-01",
  "description": "Opening Balance",
  "lines": [
    {"account_id": "1000", "debit": 125000.00},
    {"account_id": "3000", "credit": 125000.00}
  ]
}
```

---

## Best Practices

### Daily Operations
- Enter bills when received
- Record deposits daily
- Apply payments promptly

### Weekly Tasks
- Print vendor checks
- Process payroll (if weekly)
- Review cash position

### Monthly Tasks
- Bank reconciliation
- Generate financial statements
- Review budget vs. actual
- Customer statements

### Year-End
- Review all accounts
- Run year-end close
- Generate 1099s
- Prepare for taxes

---

## Support

GenFin is part of AgTools Professional. For questions:

- Review API documentation: `http://localhost:8000/docs`
- Check the CHANGELOG.md for updates
- Contact support through LICENSE file

---

*GenFin - Farm Financial Management Built for Farmers*

**Copyright 2025 New Generation Farms. All Rights Reserved.**
