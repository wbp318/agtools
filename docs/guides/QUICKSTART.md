# AgTools Quick Start Guide

Complete guide to installing, configuring, and using every feature in AgTools.

**Version:** 6.15.3 | **Updated:** February 2026

---

## Table of Contents

1. [Installation](#installation)
2. [First Launch](#first-launch)
3. [Pest & Disease Identification](#pest--disease-identification)
4. [Spray Recommendations](#spray-recommendations)
5. [Field Management](#field-management)
6. [Task Management](#task-management)
7. [Equipment Tracking](#equipment-tracking)
8. [Inventory Management](#inventory-management)
9. [GenFin Accounting](#genfin-accounting)
10. [Seed & Planting](#seed--planting)
11. [Weather & Climate](#weather--climate)
12. [AI & Machine Learning](#ai--machine-learning)
13. [Sustainability Tracking](#sustainability-tracking)
14. [Reports & Export](#reports--export)
15. [Mobile Interface](#mobile-interface)
16. [Configuration](#configuration)
17. [Troubleshooting](#troubleshooting)

---

## Installation

### System Requirements

- **Operating System:** Windows 10+, macOS 10.14+, or Linux
- **Python:** Version 3.12 or higher
- **RAM:** 4 GB minimum, 8 GB recommended
- **Storage:** 500 MB for application, plus space for your data
- **Internet:** Required only for weather features and updates

### Step 1: Install Python

1. Go to https://python.org/downloads
2. Download Python 3.12 or higher
3. Run the installer
4. **IMPORTANT:** Check the box that says **"Add Python to PATH"**
5. Click "Install Now"

Verify installation:
```bash
python --version
# Should show: Python 3.12.x or higher
```

### Step 2: Download AgTools

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/wbp318/agtools.git
cd agtools
```

**Option B: Download ZIP**
1. Go to https://github.com/wbp318/agtools
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract to a folder (e.g., `C:\agtools` or `~/agtools`)

### Step 3: Install Dependencies

**Backend (Required):**
```bash
cd backend
pip install -r requirements.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (server)
- SQLite support
- Authentication libraries
- Data validation (Pydantic)
- And other dependencies

**Frontend Desktop App (Optional):**
```bash
cd ../frontend
pip install -r requirements.txt
```

This installs:
- PyQt6 (desktop interface)
- httpx (API client)
- Local database support

---

## First Launch

### Starting the Server

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Leave this terminal open** - the server must be running for AgTools to work.

### Accessing AgTools

| Interface | URL | Best For |
|-----------|-----|----------|
| **API Explorer** | http://localhost:8000/docs | Testing endpoints, developers |
| **Mobile Interface** | http://localhost:8000/m/login | Field crews, phones/tablets |
| **Desktop App** | Run `python main.py` in frontend/ | Full-featured daily use |

### Setting Up Admin Credentials

Admin credentials must be configured before first login. Choose one method:

**Method 1: Environment Variables (Recommended)**
```bash
# Windows
set AGTOOLS_ADMIN_USER=your_username
set AGTOOLS_ADMIN_PASS=your_secure_password

# Linux/Mac
export AGTOOLS_ADMIN_USER=your_username
export AGTOOLS_ADMIN_PASS=your_secure_password
```

**Method 2: Credentials File**
Create `backend/.credentials` with:
```
ADMIN_USER=your_username
ADMIN_PASS=your_secure_password
```

See `backend/.credentials.example` for a template. The `.credentials` file is gitignored for security.

### Starting the Desktop App

Open a **new terminal** (keep the server running):
```bash
cd frontend
python main.py
```

The desktop application provides the full AgTools experience with:
- Dashboard overview
- All management screens
- Offline capability
- Print support

---

## Pest & Disease Identification

AgTools can identify 46 pests and diseases affecting corn and soybeans.

### How to Identify a Problem

**Method 1: Symptom Checklist**
1. Go to Pest/Disease ID screen
2. Select your crop (Corn or Soybeans)
3. Check the symptoms you're seeing:
   - Leaf discoloration
   - Holes or feeding damage
   - Wilting
   - Lesions or spots
   - Root damage
   - etc.
4. Click "Identify"
5. View ranked results with confidence scores

**Method 2: Photo Upload (AI)**
1. Go to AI Identification
2. Upload a photo of the affected plant
3. AI analyzes the image
4. Get identification with treatment recommendations

### Supported Pests & Diseases

**Corn (23 problems):**

| Type | Name | Key Symptoms |
|------|------|--------------|
| Pest | Corn Rootworm | Root damage, lodging, "goose-necking" |
| Pest | European Corn Borer | Broken tassels, stalk tunneling |
| Pest | Western Bean Cutworm | Ear feeding, silk clipping |
| Pest | Fall Armyworm | Ragged leaf feeding, frass |
| Pest | Black Cutworm | Cut plants at soil line |
| Pest | Corn Leaf Aphid | Honeydew, sooty mold, stunting |
| Pest | Spider Mites | Stippling, webbing, bronzing |
| Pest | Japanese Beetle | Skeletonized leaves |
| Disease | Gray Leaf Spot | Rectangular gray-brown lesions |
| Disease | Northern Corn Leaf Blight | Cigar-shaped lesions |
| Disease | Southern Corn Leaf Blight | Smaller tan lesions |
| Disease | Common Rust | Cinnamon-brown pustules |
| Disease | Southern Rust | Orange pustules, mostly on upper leaves |
| Disease | Tar Spot | Black raised stromata |
| Disease | Anthracnose | Top dieback, stalk rot |
| Disease | Goss's Wilt | "Freckles" in lesions, bacterial exudate |
| Disease | Stewart's Wilt | Yellow streaks, flea beetle spread |
| Disease | Ear Rots | White, pink, or green mold on ears |

**Soybeans (23 problems):**

| Type | Name | Key Symptoms |
|------|------|--------------|
| Pest | Soybean Aphid | Honeydew, stunting, leaf curl |
| Pest | Spider Mites | Stippling, bronzing, webbing |
| Pest | Bean Leaf Beetle | Round holes in leaves |
| Pest | Japanese Beetle | Skeletonized leaves |
| Pest | Stink Bugs | Flat, shriveled seeds |
| Pest | Grasshoppers | Ragged leaf margins |
| Pest | Soybean Looper | Defoliation, windowpane feeding |
| Disease | White Mold | White fluffy growth, sclerotia |
| Disease | Sudden Death Syndrome | Interveinal chlorosis, root rot |
| Disease | Soybean Cyst Nematode | Stunting, yellowing in patches |
| Disease | Brown Stem Rot | Brown pith, leaf scorch |
| Disease | Frogeye Leaf Spot | Circular lesions with purple borders |
| Disease | Phytophthora Root Rot | Wilting, chocolate-brown roots |
| Disease | Charcoal Rot | Gray stem, microsclerotia |
| Disease | Soybean Rust | Tan to reddish-brown pustules |

### Treatment Recommendations

Each identification includes:
- **Product recommendations** with rates
- **Application timing** guidance
- **Economic threshold** analysis
- **Cost per acre** estimates
- **Expected efficacy** percentages

---

## Spray Recommendations

Get data-driven recommendations for pest and disease control.

### Getting a Recommendation

1. Select the problem you're treating
2. Enter field size (acres)
3. Specify application method (ground/aerial)
4. View recommendations ranked by:
   - **Efficacy** - How well it works
   - **Cost** - Price per acre
   - **ROI** - Return on investment

### Product Database

AgTools includes 40+ products:

**Insecticides:**
| Product | Active Ingredient | Target Pests |
|---------|------------------|--------------|
| Warrior II | Lambda-cyhalothrin | Broad-spectrum |
| Brigade | Bifenthrin | Aphids, rootworms |
| Mustang Maxx | Zeta-cypermethrin | Armyworms, beetles |
| Besiege | Chlorantraniliprole + Lambda | Borers, worms |
| Coragen | Chlorantraniliprole | Lepidoptera |
| Actara | Thiamethoxam | Aphids, beetles |
| Assail | Acetamiprid | Aphids |

**Fungicides:**
| Product | Active Ingredients | Target Diseases |
|---------|-------------------|-----------------|
| Trivapro | Azoxystrobin + Propiconazole + Benzovindiflupyr | Broad-spectrum |
| Delaro | Prothioconazole + Trifloxystrobin | Leaf diseases |
| Priaxor | Fluxapyroxad + Pyraclostrobin | Rust, leaf spot |
| Stratego YLD | Prothioconazole + Trifloxystrobin | Multiple |
| Quadris | Azoxystrobin | QoI fungicide |

### Spray Timing

Recommendations consider:
- **Weather windows** - Wind speed, temperature, humidity
- **Growth stage** - Best timing for maximum effect
- **Re-entry intervals** - Worker safety
- **Pre-harvest intervals** - Food safety
- **Tank mix compatibility** - What can be combined

### Cost Analysis

For each recommendation:
```
Product: Trivapro
Rate: 13.7 oz/acre
Product Cost: $22.50/acre
Application Cost: $8.00/acre
Total Cost: $30.50/acre
Expected Yield Protection: 8 bu/acre
At $4.50/bu = $36.00/acre benefit
ROI: 118%
```

---

## Field Management

Track all your farm fields with detailed information.

### Creating a Field

1. Go to Field Management
2. Click "Add Field"
3. Enter field details:

| Field | Description | Example |
|-------|-------------|---------|
| Name | Field identifier | "North 40" |
| Acres | Field size | 40.5 |
| Legal Description | Section-Township-Range | "NE 1/4 Sec 12 T2N R3W" |
| GPS Coordinates | Center point | 41.1234, -89.5678 |
| Soil Type | Primary soil | "Drummer silty clay loam" |
| Drainage | Tile/surface/none | "Pattern tiled 30'" |
| Owner | Landowner name | "Smith Family Trust" |
| Rent Type | Cash/share/owned | "Cash rent" |
| Rent Amount | Annual payment | $250/acre |

### Field Operations Tracking

Log all activities on each field:
- **Tillage** - Date, type, depth
- **Planting** - Date, variety, population, depth
- **Fertilizer** - Product, rate, method
- **Spraying** - Product, rate, target
- **Harvest** - Date, yield, moisture, test weight

### Field Statistics

View per-field analytics:
- Historical yields by year
- Input costs per acre
- Net profit/loss
- Cost of production trends
- Yield response to inputs

---

## Task Management

Organize work and manage your crew efficiently.

### Creating Tasks

1. Go to Task Management
2. Click "New Task"
3. Fill in details:

| Field | Description |
|-------|-------------|
| Title | Brief description |
| Description | Full details |
| Priority | Low / Medium / High / Critical |
| Due Date | When it needs to be done |
| Assigned To | Crew member(s) |
| Field | Related field (optional) |
| Equipment | Required equipment (optional) |
| Estimated Hours | Time estimate |

### Task Statuses

- **Pending** - Not started
- **In Progress** - Currently being worked on
- **Completed** - Finished
- **Cancelled** - No longer needed

### Crew Assignment

Assign tasks to specific workers:
- View worker availability
- Track time spent
- Monitor completion rates
- Generate productivity reports

### Task Categories

Organize tasks by type:
- Field work
- Equipment maintenance
- Office/admin
- Meetings
- Training
- Emergency

---

## Equipment Tracking

Manage your entire fleet of machinery.

### Adding Equipment

| Field | Description | Example |
|-------|-------------|---------|
| Name | Equipment identifier | "JD 8370R #1" |
| Type | Equipment category | "Tractor" |
| Make | Manufacturer | "John Deere" |
| Model | Model number | "8370R" |
| Year | Model year | 2020 |
| Serial Number | VIN/Serial | "1RW8370RXLD012345" |
| Purchase Date | When acquired | "2020-03-15" |
| Purchase Price | Cost | $350,000 |
| Current Hours | Hour meter reading | 2,450 |

### Equipment Types

- Tractors
- Combines
- Planters
- Sprayers
- Tillage equipment
- Grain carts
- Trucks
- Trailers
- Other implements

### Hour Logging

Track usage for each piece of equipment:
- Date and hours worked
- Operator
- Field/location
- Task performed

### Maintenance Tracking

Schedule and record maintenance:
- **Service intervals** - Oil changes, filters
- **Upcoming service** - Based on hours
- **Maintenance history** - All past work
- **Parts used** - Links to inventory
- **Costs** - Labor and parts

### Equipment Costs

Calculate true cost of ownership:
- Depreciation
- Fuel consumption
- Repair costs
- Cost per hour
- Cost per acre

---

## Inventory Management

Track all your supplies and inputs.

### Inventory Categories

| Category | Examples |
|----------|----------|
| **Chemicals** | Herbicides, insecticides, fungicides |
| **Seed** | Corn, soybean, wheat varieties |
| **Fertilizer** | Nitrogen, phosphorus, potassium, micronutrients |
| **Fuel** | Diesel, gasoline, DEF |
| **Parts** | Filters, belts, bearings, hardware |
| **Supplies** | Oil, grease, shop supplies |

### Inventory Fields

| Field | Description |
|-------|-------------|
| Item Name | Product name |
| SKU/Part Number | Identifier |
| Category | Type of item |
| Quantity On Hand | Current stock |
| Unit | gal, lb, bag, each |
| Cost Per Unit | Purchase price |
| Reorder Point | When to reorder |
| Location | Storage location |
| Supplier | Vendor name |

### Inventory Transactions

- **Receive** - Add new stock
- **Use** - Deduct for field operations
- **Adjust** - Correct counts
- **Transfer** - Move between locations

### Low Stock Alerts

Get notified when items fall below reorder points:
- Dashboard widget shows low items
- Generate reorder reports
- Track historical usage for planning

---

## GenFin Accounting

Complete farm financial management system.

### Chart of Accounts

60+ pre-configured farm accounts:

**Assets:**
- Checking accounts
- Savings accounts
- Accounts receivable
- Inventory
- Equipment
- Land

**Liabilities:**
- Accounts payable
- Operating loans
- Equipment loans
- Real estate mortgages

**Revenue:**
- Grain sales
- Custom work income
- Government payments
- Other farm income

**Expenses:**
- Seed, fertilizer, chemicals
- Labor and benefits
- Equipment repairs
- Fuel and utilities
- Insurance, rent, taxes

### Vendors & Bills

Manage all your suppliers:

1. **Add Vendors** with contact info, payment terms
2. **Enter Bills** when invoices arrive
3. **Track Due Dates** to avoid late fees
4. **Pay Bills** with checks or ACH
5. **View AP Aging** report

### Customers & Invoices

Track money owed to you:

1. **Add Customers** (grain elevators, custom work clients)
2. **Create Invoices** for work performed
3. **Send Statements** monthly
4. **Record Payments** when received
5. **View AR Aging** report

### Check Printing

Print checks directly from AgTools:

- **MICR encoding** for bank processing
- **Multiple formats** (voucher, wallet, 3-per-page)
- **Batch printing** for multiple checks
- **Check register** tracking
- **Void check** management

### Payroll

Full payroll processing:

1. **Add Employees** with W-4 information
2. **Enter Time** worked
3. **Calculate Pay** with tax withholding:
   - Federal income tax
   - Social Security (6.2%)
   - Medicare (1.45%)
   - State income tax
4. **Generate Paychecks** or direct deposit (NACHA files)
5. **Track Liabilities** for tax payments

### Financial Reports

50+ reports available:

| Report | Description |
|--------|-------------|
| **Profit & Loss** | Income minus expenses |
| **Balance Sheet** | Assets, liabilities, equity |
| **Cash Flow** | Money in and out |
| **Trial Balance** | All account balances |
| **General Ledger** | Transaction details |
| **AP Aging** | Bills by age |
| **AR Aging** | Invoices by age |
| **Budget vs Actual** | Compare to plan |

### Detailed GenFin Guide

See [GENFIN.md](GENFIN.md) for complete accounting documentation.

---

## Seed & Planting

Track seed inventory and planting records.

### Seed Inventory

| Field | Description |
|-------|-------------|
| Variety | Seed product name |
| Brand | Manufacturer |
| Crop | Corn, soybean, wheat |
| Trait Package | GT, LL, RR2, etc. |
| Maturity | Relative maturity |
| Units On Hand | Bags/units |
| Cost Per Unit | Purchase price |
| Lot Number | Tracking |
| Germination % | Test results |
| Treatment | Seed treatment applied |

### Planting Records

For each field planting:

| Field | Description |
|-------|-------------|
| Field | Which field |
| Date Planted | Planting date |
| Variety | Seed used |
| Population | Seeds/acre |
| Row Spacing | Inches |
| Planting Depth | Inches |
| Soil Temp | At planting |
| Soil Moisture | Conditions |
| Acres Planted | Amount |

### Emergence Tracking

Monitor stand establishment:
- Days to emergence
- Stand count (plants/acre)
- Emergence uniformity
- Replant decisions

---

## Weather & Climate

Weather-smart farming decisions.

### Weather Integration

Current and forecast data:
- Temperature
- Humidity
- Wind speed and direction
- Precipitation
- UV index

### Spray Windows

Identify optimal application times:
- **Wind:** 3-10 mph ideal
- **Temperature:** 40-85°F
- **Humidity:** >40% preferred
- **Rain-free period:** Per product label

### Growing Degree Days (GDD)

Track crop development:
- Accumulated GDD by date
- Corn staging predictions
- Insect emergence models
- Disease risk periods

### Climate Records

Historical data for planning:
- Average temperatures by month
- Precipitation totals
- First/last frost dates
- Growing season length

---

## AI & Machine Learning

Advanced analytics and automation.

### AI Pest Identification

Upload photos for automatic identification:
- Analyzes plant images
- Identifies likely problems
- Provides confidence scores
- Suggests treatments

### Yield Prediction

ML models estimate yields based on:
- Weather data
- Soil conditions
- Input applications
- Historical yields
- Satellite imagery

### Expense Categorization

Automatic transaction categorization:
- Learns from your patterns
- Suggests categories for new expenses
- Improves over time
- Reduces data entry

### Crop Health Analysis

NDVI and satellite data analysis:
- Identify stress areas
- Track crop vigor
- Compare fields
- Spot problems early

---

## Sustainability Tracking

Monitor and improve environmental practices.

### Carbon Footprint

Track carbon metrics:
- Fuel consumption
- Fertilizer usage
- Tillage practices
- Cover crop benefits
- Carbon credits potential

### Water Usage

Monitor irrigation and water:
- Irrigation records
- Water efficiency
- Rainfall tracking
- Conservation practices

### Sustainable Practices

Document and score practices:
- Cover crops
- Reduced tillage
- Precision application
- Integrated pest management
- Nutrient management planning

### Compliance Reporting

Generate reports for:
- Conservation programs
- Sustainability certifications
- Grant applications
- Buyer requirements

---

## Reports & Export

Get your data out in any format.

### Report Types

**Operational Reports:**
- Field activity history
- Equipment usage
- Task completion
- Inventory status
- Labor hours

**Financial Reports:**
- Profit & Loss
- Balance Sheet
- Cash Flow
- Budget variance
- Cost per acre

**Analytical Reports:**
- Yield analysis
- Input ROI
- Equipment costs
- Enterprise analysis

### Export Formats

| Format | Best For |
|--------|----------|
| **PDF** | Printing, sharing |
| **Excel** | Analysis, manipulation |
| **CSV** | Database import |
| **JSON** | API integration |

### Scheduled Reports

Set up automatic report generation:
- Daily, weekly, monthly
- Email delivery
- Custom date ranges

---

## Mobile Interface

Field access from any device.

### Accessing Mobile Interface

Open on your phone or tablet:
```
http://[your-server-ip]:8000/m/login
```

### Mobile Features

Optimized for field use:
- **Time entry** - Log hours worked
- **Task updates** - Mark tasks complete
- **Quick notes** - Voice-to-text notes
- **Photo capture** - Document conditions
- **GPS location** - Automatic field detection
- **Offline mode** - Works without signal

### Progressive Web App (PWA)

Install on your device:
1. Open the mobile URL in Chrome/Safari
2. Tap "Add to Home Screen"
3. App icon appears like native app
4. Works offline

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGTOOLS_DEV_MODE` | `0` | `1` enables auto-login |
| `AGTOOLS_TEST_MODE` | `0` | `1` disables rate limiting |
| `AGTOOLS_DB_PATH` | `agtools.db` | Database file location |
| `AGTOOLS_SECRET_KEY` | (generated) | JWT signing key |

### Setting Environment Variables

**Windows (Command Prompt):**
```cmd
set AGTOOLS_DEV_MODE=1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Windows (PowerShell):**
```powershell
$env:AGTOOLS_DEV_MODE=1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Linux/Mac:**
```bash
AGTOOLS_DEV_MODE=1 python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Desktop App Settings

Edit `frontend/agtools_settings.json`:
```json
{
  "api_url": "http://localhost:8000",
  "theme": "light",
  "auto_sync": true,
  "offline_mode": false
}
```

### Database Location

Default: `backend/agtools.db`

To use a different location:
```bash
AGTOOLS_DB_PATH=/path/to/your/database.db python -m uvicorn main:app
```

---

## Troubleshooting

### Server Won't Start

**"Port already in use"**
```bash
# Use a different port
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

**"Module not found"**
```bash
cd backend
pip install -r requirements.txt
```

### Can't Log In

**Check credentials:**
- Default: `admin` / `admin123`
- Passwords are case-sensitive

**Check server is running:**
- Look for "Uvicorn running on http://127.0.0.1:8000"
- Try http://localhost:8000/ in browser

### Database Errors

**"Database is locked"**
- SQLite allows one writer at a time
- Close other applications accessing the database
- For multi-user, consider PostgreSQL

**"Table not found"**
- Database may need initialization
- Delete `agtools.db` and restart (loses data)

### Token Expired

- Access tokens expire after 24 hours
- Simply log in again
- Or use the refresh token endpoint

### Desktop App Won't Connect

- Verify server is running
- Check `api_url` in settings
- Try opening http://localhost:8000/docs in browser

### Common Commands

```bash
# Start backend server
cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Start desktop app
cd frontend && python main.py

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Check API health
curl http://localhost:8000/

# View API docs
# Open: http://localhost:8000/docs
```

---

## Next Steps

1. **Set up your farm** - Add fields, equipment, and inventory
2. **Configure GenFin** - Set up chart of accounts and vendors
3. **Explore the API** - Visit http://localhost:8000/docs
4. **Read the full docs:**
   - [Technical Reference](../TECHNICAL_REFERENCE.md) - Architecture and API details
   - [GenFin Guide](GENFIN.md) - Complete accounting documentation

---

## Getting Help

- **API Documentation:** http://localhost:8000/docs
- **GitHub Issues:** https://github.com/wbp318/agtools/issues
- **Technical Reference:** [TECHNICAL_REFERENCE.md](../TECHNICAL_REFERENCE.md)

---

*AgTools Quick Start Guide v6.15.2*
*Copyright 2024-2026 New Generation Farms and William Brooks Parker. All Rights Reserved.*
