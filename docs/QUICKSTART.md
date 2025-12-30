# Quick Start Guide - AgTools Professional Crop Consulting System

## For Farmers: Plain English Guide

This guide explains how to use AgTools to **lower your input costs** and **make better decisions** about fertilizer, pesticides, irrigation, and labor. No computer science degree needed - just follow along.

---

## What This System Does (In Plain English)

Think of AgTools as your **digital agronomist** that:

1. **Identifies Bugs & Diseases** - Tell it what you see, it tells you what it is
   - **Desktop App** (v2.2.1): Professional screens with symptom checklists and confidence scoring
2. **Recommends Treatments** - Tells you WHAT to spray, HOW MUCH, and WHETHER it's worth the money
3. **Optimizes Your Costs** - Helps you figure out where you're spending too much on:
   - Labor (scouting, spraying, etc.)
   - Fertilizer (are you putting on too much?)
   - Pesticides (is there a cheaper product that works just as well?)
   - Irrigation (are you pumping more water than you need?)
4. **Uses YOUR Prices** (v2.1) - Input your actual supplier quotes for accurate calculations
5. **Tells You When to Spray** (v2.1) - Weather-smart timing to avoid wasted applications
6. **Calculates Economic Optimum Rates** (v2.2) - Find the most PROFITABLE fertilizer rate, not just max yield
7. **Professional Desktop Interface** (v2.2.1) - Full PyQt6 app with all features integrated
8. **Works Offline** (v2.3.0) - Automatic fallback to local database when API unavailable
9. **Configurable Settings** (v2.4.0) - Full settings screen with preferences, API config, and data management
10. **Multi-User Farm Operations** (v2.5.0) - Login system with roles (admin, manager, crew), user management, and team/crew organization
11. **Field Management** (v2.5.0) - Track all your farm fields with acreage, crop type, soil, and irrigation
12. **Operations Logging** (v2.5.0) - Record sprays, fertilizer, planting, harvest with costs and yields
13. **Task Management** (v2.5.0) - Create, assign, and track tasks with due dates and priorities
14. **Equipment Management** (v2.5.0) - Track tractors, combines, sprayers with hours and maintenance schedules
15. **Inventory Tracking** (v2.5.0) - Manage seeds, fertilizers, chemicals, fuel with low stock and expiration alerts
16. **Maintenance Scheduling** (v2.5.0) - Service reminders with overdue, due soon, and upcoming alerts
17. **Reports & Analytics** (v2.5.0) - 4-tab dashboard with charts and CSV export for operations, financials, equipment, and field performance
18. **Mobile Crew Interface** (v2.6.0) - PWA mobile web app for field crews with task list, time logging, photo uploads, and offline support
19. **Cost Per Acre Tracking** (v2.7.0) - Import expenses from QuickBooks CSV or scanned receipts, allocate to fields, get cost-per-acre reports
20. **QuickBooks Import** (v2.9.0) - Direct QuickBooks export import with auto-format detection, account-to-category mapping, and smart filtering
21. **AI Image Identification** (v3.0.0) - Upload field photos for instant AI pest/disease identification with confidence scoring
22. **Crop Health Scoring** (v3.0.0) - NDVI analysis from drone/satellite imagery with zone-based health maps
23. **Yield Prediction** (v3.0.0) - ML-based yield predictions using your field inputs and historical data
24. **Smart Expense Categorization** (v3.0.0) - Auto-categorize expenses with 95%+ accuracy, learns from your corrections
25. **Spray AI** (v3.0.0) - ML-enhanced spray timing that learns from your outcomes and improves over time
26. **Sustainability Dashboard** (v3.2.0) - Track carbon footprint, input usage, and conservation practices with EPA/IPCC-compliant calculations
27. **Climate Integration** (v3.3.0) - GDD tracking for 8 crops, crop stage prediction, precipitation logging, and heat stress monitoring
28. **Field Trial Tools** (v3.4.0) - Research-grade trial management with statistical analysis (t-tests, LSD) for variety and treatment trials
29. **Enterprise Operations** (v3.9.0) - Labor management, land/lease tracking, cash flow forecasting, and multi-entity support
30. **Precision Intelligence** (v4.0.0) - AI-powered yield prediction, variable rate prescriptions, management zones, and decision support
31. **Grain & Storage Management** (v4.1.0) - Bin management, drying cost calculator, grain accounting, and basis price alerts
32. **Complete Farm Business Suite** (v4.2.0) - Tax planning with MACRS depreciation, succession planning, benchmarking dashboard, and document vault
33. **GenFin Financial Management** (v6.0.0-6.3.x) - Complete farm accounting system:
    - **Chart of Accounts**: 60+ farm-specific accounts with double-entry accounting
    - **Accounts Payable**: Vendors, bills, payments, purchase orders, 1099 tracking
    - **Accounts Receivable**: Customers, invoices, estimates, payments, statements
    - **CHECK PRINTING**: Multiple formats with MICR support - print checks directly!
    - **ACH/Direct Deposit**: Generate NACHA files for payroll and vendor payments
    - **Payroll**: Employee management with automatic tax calculations
    - **Financial Reports**: Profit & Loss, Balance Sheet, Cash Flow, Ratios
    - **Budgeting**: Budget vs. actual, forecasting, scenario planning
    - **90s QuickBooks UI** (v6.3.1): Nostalgic teal blue theme with beveled 3D buttons
    - **Multi-Entity Support** (v6.3.0): Manage multiple business entities (Farm, LLC, Corp)
    - **1099 Tracking** (v6.3.0): 1099-NEC and 1099-MISC preparation with threshold monitoring
34. **Farm Operations Suite** (v6.4.0) - Comprehensive farm operations management:
    - **Livestock Management**: Track cattle, hogs, poultry, sheep, goats with health records
    - **Group/Batch Tracking**: Manage poultry flocks and hog groups
    - **Health Records**: Vaccinations, treatments, vet visits with due date alerts
    - **Breeding Records**: Gestation tracking, expected birth dates, offspring counts
    - **Weight Tracking**: Weight history with ADG (average daily gain) calculations
    - **Sale Records**: Buyer tracking, price/lb, profit calculation
    - **Seed Inventory**: Variety tracking, traits, lot numbers, storage locations
    - **Planting Records**: Field planting with rates, populations, costs
    - **Emergence Monitoring**: Stand counts, uniformity scores, growth stages
35. **GenFin 100% Complete** (v6.5.0) - Full QuickBooks Desktop parity:
    - **Banking Module**: Bank Accounts, Check Register, Transfers, Reconciliation, Bank Feeds
    - **Customer Module**: Statements generator, Credit Memos
    - **Vendor Module**: Credit Cards tracking, Vendor Credits
    - **Payroll Module**: Pay Liabilities with E-Pay, Employees visible in Payroll Center
    - **Lists Module**: Fixed Assets with depreciation, Recurring/Memorized Transactions
    - **Planning**: Budgets with Budget vs Actual reports, Entities (Classes/Locations/Names/Terms)
    - **Settings & Help**: Complete company settings, Help Center with search and tutorials
    - **Zero Placeholders**: Every GenFin navigation item leads to a fully functional screen

---

## What You Need Before Starting

Before you can use AgTools, you need a few things on your computer:

1. **Python** (version 3.8 or newer) - This is the programming language the system runs on
   - Download from: https://www.python.org/downloads/
   - During installation, **CHECK THE BOX** that says "Add Python to PATH"

2. **Git** (optional but recommended) - This helps you download the code
   - Download from: https://git-scm.com/downloads
   - Just click "Next" through the installer

**Not sure if you have these?** Open a command prompt and type:
```bash
python --version
git --version
```
If you see version numbers, you're good. If you see an error, you need to install them.

---

## Getting Started (One-Time Setup)

### Step 1: Download the AgTools Code

You have two options:

**Option A: Using Git (Recommended)**

Open a command prompt (search for "cmd" in Windows) and type:

```bash
git clone https://github.com/wbp318/agtools.git
```

This downloads all the code to a folder called "agtools" on your computer.

**Option B: Download as ZIP (If you don't have Git)**

1. Go to: https://github.com/wbp318/agtools
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to a folder you can find (like your Documents folder)

### Step 2: Open the AgTools Folder

In your command prompt, navigate to where you downloaded the code:

```bash
cd agtools
```

**If you downloaded the ZIP**, you might need to type the full path, like:
```bash
cd C:\Users\YourName\Documents\agtools-master
```

**Tip:** You can also type `cd ` (with a space) and then drag the folder into the command prompt window - it will fill in the path for you!

### Step 3: Install the Required Pieces

Now go into the backend folder and install what the system needs:

```bash
cd backend
pip install -r requirements.txt
```

This downloads all the pieces the system needs. **Only do this once** - unless you see errors later, then try running it again.

### Step 4: Start the Backend API

Every time you want to use AgTools, navigate to the backend folder and type:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

You'll see a message that says "Uvicorn running". Leave this window open.

### Step 5: Choose Your Interface

You have TWO options for using AgTools:

#### Option A: Web API (Browser-based)

Open your web browser (Chrome, Edge, Firefox) and go to:

**http://localhost:8000/docs**

This opens the interactive API where you can click buttons and fill in forms.

#### Option B: Desktop Application (NEW - Recommended)

Open a NEW command prompt (keep the API server running) and type:

```bash
cd frontend
pip install -r requirements.txt  # One-time setup
python main.py
```

This opens the **professional desktop application** with:
- **Dashboard** - Quick access to all features
- **Yield Calculator** - Interactive charts showing yield response curves
- **Spray Timing** - Weather evaluation with spray/wait recommendations
- **Cost Optimizer** - Tabbed interface for fertilizer, irrigation, labor analysis
- **Price Manager** - Your supplier quotes, buy/wait analysis, alerts
- **Pest Identification** - Symptom checklist with 20 pest symptoms, severity ratings, confidence scoring
- **Disease Identification** - Weather conditions input, management recommendations, detailed disease cards
- **Settings** (NEW v2.4.0) - 4-tab configuration: General preferences, API connection, data management, about

**Offline Mode (NEW v2.3.0):** The desktop app now works offline! If the API isn't running, the app automatically switches to offline mode using local SQLite cache. You'll see "Offline" status in the toolbar, and features like yield calculations and spray timing still work. Data syncs automatically when connection is restored.

---

## Running Tests (NEW v2.4.0)

Before using the system in production, you can run the integration tests to verify everything is working:

```bash
cd frontend
python tests/test_phase9.py
```

**What the tests verify:**
- Settings screen imports correctly
- Common widgets (loading overlays, validation) work
- All 8 screens import and initialize
- Offline mode components (database, calculators) function
- API client offline methods are available
- Configuration saves and loads properly

**Expected output:**
```
Running Phase 9 Integration Tests
==================================
[PASS] Settings screen import
[PASS] Common widgets import
[PASS] All screens import (8 screens)
[PASS] Offline integration
[PASS] API client offline methods
[PASS] Config and settings

==================================
Results: 6/6 tests passed
All Phase 9 tests passed!
```

---

## How to Use Each Feature

### 🐛 Identifying a Pest (Desktop App - NEW v2.2.1)

**When to use:** You found bugs in your field and want to know what they are using the desktop app.

1. Start the backend API and desktop app (see setup above)
2. Click **"Pests"** from the sidebar navigation
3. Fill in the identification form:
   - **Crop**: Select corn or soybean
   - **Growth Stage**: Select the current stage (V6, VT, R3, etc.)
   - **Symptoms**: Check all symptoms you observe from the 20-symptom checklist
   - **Severity**: Rate the infestation severity (1-10)
   - **Location/Pattern**: Select where damage is occurring
4. Click **"Identify"**

**What you get:**
- Confidence-ranked list of possible pests
- Detailed pest cards showing:
  - Common and scientific names
  - Description and damage symptoms
  - Identification features
  - **Economic thresholds** (highlighted in green)
  - Management notes

**Example symptoms to look for:**
- Curled leaves, yellowing, sticky residue → Aphids
- Holes in leaves, frass (insect droppings) → Caterpillars
- Stippling, bronzing, webbing → Spider mites
- Root damage, lodging → Rootworms

---

### 🦠 Identifying a Disease (Desktop App - NEW v2.2.1)

**When to use:** You see disease symptoms and want identification with management options.

1. Click **"Diseases"** from the sidebar navigation
2. Fill in the identification form:
   - **Crop**: Select corn or soybean
   - **Growth Stage**: Current stage
   - **Symptoms**: Check symptoms from the 20-disease symptom checklist
   - **Weather Conditions**: Select recent weather (warm/humid, cool/wet, etc.)
   - **Severity**: Rate the infection severity (1-10)
   - **Location Pattern**: Where symptoms appear (lower canopy, scattered, etc.)
3. Click **"Identify"**

**What you get:**
- Confidence-ranked list of possible diseases
- Detailed disease cards showing:
  - Common and scientific names
  - Description and symptoms
  - **Favorable conditions** for disease development
  - Management recommendations

**Example symptoms to look for:**
- Gray rectangular lesions → Gray Leaf Spot
- Tan cigar-shaped lesions → Northern Corn Leaf Blight
- White cottony mold at nodes → White Mold (soybeans)
- Sudden wilting, interveinal chlorosis → SDS (soybeans)

---

### ⚙️ Configuring Settings (Desktop App - NEW v2.4.0)

**When to use:** Customize the app behavior, configure API connection, or manage your local data.

1. Click **"Settings"** from the sidebar navigation (bottom section)
2. Navigate between the **4 tabs**:

**General Tab - Your Preferences:**
- **Region**: Select your agricultural region (affects default prices)
  - Midwest Corn Belt, Northern Plains, Southern Plains, Delta, Southeast, Pacific Northwest, Mountain
- **Default Crop**: Set your primary crop (corn or soybean)
- **Theme**: Choose Light or Dark mode
- **Sidebar Width**: Adjust navigation panel size
- **Offline Mode Settings**:
  - Enable/disable offline fallback
  - Set cache TTL (time-to-live) in hours
  - Enable sync on startup
  - Enable auto-fallback when API unavailable

**Connection Tab - API Configuration:**
- **API Server URL**: Default is `http://127.0.0.1:8000`
- **Timeout**: How long to wait for API responses (default 30 seconds)
- **Test Connection**: Click to verify the backend is reachable
- **Connection Status**: Shows current online/offline state with refresh button

**Data Tab - Cache Management:**
- **Cache Statistics**: View entries, products, pests, diseases, calculations stored locally
- **Cache Management**:
  - **Clear Expired**: Remove only stale cache entries
  - **Clear All**: Delete entire local cache
  - **Optimize**: Compact the SQLite database
- **Data Export**:
  - Export calculation history to CSV
  - Export product prices to CSV
- **Database Size**: Shows current SQLite file size

**About Tab - Application Info:**
- AgTools version and branding
- Complete feature list
- Data directory paths (where settings and cache are stored)

---

### 🔄 Using Offline Mode (NEW v2.3.0)

**When to use:** When you're in the field without internet, or the backend API is unavailable.

**How it works:**
1. The app automatically detects when the API is unreachable
2. Status bar shows "Offline" indicator
3. Core features continue working with local calculations:
   - Yield Response Calculator (full EOR calculations)
   - Spray Timing Evaluator (weather condition assessment)
   - Previously cached pest/disease data
   - Previously cached product prices
4. Changes you make (like custom prices) are queued for sync
5. When connection restores, click **"Sync"** button to push pending changes

**Sync Status Indicators:**
- **Green dot**: Online and synced
- **Yellow dot**: Online with pending changes
- **Red dot**: Offline mode active
- **"X pending"**: Shows number of queued changes

**To manually sync:**
1. Ensure the backend API is running
2. Click the **Sync** button in the top toolbar
3. Watch the status bar for sync progress
4. Pending count resets to 0 when complete

**Offline Mode Tips:**
- The first time you run online, let data cache before going offline
- Yield calculations and spray timing work fully offline
- Pest/disease identification requires cached data or API connection
- Custom prices are queued and sync when back online

---

### 🔧 Troubleshooting Offline Mode

**Problem: "Offline" shows even when backend is running**
1. Check the API URL in Settings → Connection tab
2. Ensure it matches where the backend is running (default: `http://127.0.0.1:8000`)
3. Click "Test Connection" to diagnose
4. Make sure the backend terminal shows "Uvicorn running"

**Problem: Data not syncing when back online**
1. Check the pending count in the toolbar
2. Click the Sync button manually
3. If sync fails, check Settings → Connection for errors
4. Verify backend is running and accessible

**Problem: Old data showing in offline mode**
1. Go to Settings → Data tab
2. Click "Clear Expired" to remove stale cache
3. Reconnect to API to refresh data
4. Or "Clear All" to start fresh (will need to recache)

**Problem: Database getting too large**
1. Go to Settings → Data tab
2. View current database size
3. Click "Optimize" to compact the database
4. Consider "Clear Expired" to remove old entries

---

### 🐛 Identifying a Pest (API Method)

**When to use:** You found bugs in your field and want to know what they are.

1. Find **"POST /api/v1/identify/pest"** in the list
2. Click on it, then click **"Try it out"**
3. Fill in the form:
   - **crop**: Type `corn` or `soybean`
   - **growth_stage**: Type the stage like `V6`, `VT`, `R3`, etc.
   - **symptoms**: Describe what you see in quotes, like `["curled leaves", "sticky residue", "yellowing"]`
4. Click **"Execute"**
5. The system tells you what pest it likely is and how confident it is

**Example:**
```json
{
  "crop": "soybean",
  "growth_stage": "R3",
  "symptoms": ["curled_leaves", "yellowing", "sticky_residue"]
}
```

Result: "Soybean Aphid - 92% confidence"

---

### 💉 Getting a Spray Recommendation

**When to use:** You've identified a pest or disease and want to know what to spray.

1. Find **"POST /api/v1/recommend/spray"**
2. Click **"Try it out"**
3. Fill in:
   - **crop**: `corn` or `soybean`
   - **growth_stage**: Current stage
   - **problem_type**: `pest` or `disease`
   - **problem_id**: The number of the pest (0 = first one in the list)
   - **severity**: How bad is it? (1-10, where 10 is the worst)
   - **field_acres**: How many acres?
4. Click **"Execute"**

**What you get back:**
- Product name and how much to use
- Cost per acre
- Total cost for your field
- ROI (return on investment) - is it worth spraying?
- When to spray based on weather

---

### 💰 Figuring Out If Treatment is Worth It

**When to use:** Before you spend money on spray, you want to know if it'll pay off.

1. Find **"POST /api/v1/threshold/check"**
2. Fill in:
   - **crop**: `corn` or `soybean`
   - **pest_name**: What you found (like `soybean aphid`)
   - **population_count**: How many per plant? (count 10 plants, average them)
   - **control_cost_per_acre**: What will treatment cost? (around $15-20 typical)
   - **expected_yield**: What yield are you expecting? (bushels/acre)
   - **grain_price**: Current price (corn ~$4.50, beans ~$12.00)
3. Click **"Execute"**

**What you get:**
- Whether the population is above threshold
- How much yield you'll lose if you don't treat
- How much money that costs you
- Net benefit: Money saved minus spray cost
- Clear YES or NO recommendation

---

## 🆕 INPUT COST OPTIMIZATION (The Money-Saving Features)

These new features help you figure out where you can cut costs without hurting yields.

### 💵 Quick Cost Estimate

**When to use:** You want a fast estimate of what it costs to grow a crop.

1. Find **"POST /api/v1/optimize/quick-estimate"**
2. Fill in:
   - **acres**: Your field size
   - **crop**: `corn` or `soybean`
   - **is_irrigated**: `true` or `false`
   - **yield_goal**: What you're aiming for
3. Click **"Execute"**

**What you get:**
- Cost breakdown: seed, fertilizer, pesticides, labor, irrigation
- Total cost per acre
- Break-even yield (the yield you need just to cover costs)
- Potential savings range (10-20% typical)

**Example:** 160 acres of irrigated corn, 200 bu/acre goal
- Total cost: ~$75,000
- Cost per acre: ~$470
- Break-even: 105 bu/acre
- Potential savings: $7,500 - $15,000

---

### 🌿 Optimizing Your Fertilizer Program

**When to use:** Before you buy fertilizer, figure out exactly what you need.

1. Find **"POST /api/v1/optimize/fertilizer"**
2. Fill in your soil test results:
   - **soil_test_p_ppm**: Your phosphorus level
   - **soil_test_k_ppm**: Your potassium level
   - **yield_goal**: Target yield
   - **acres**: Field size
   - **nitrogen_credit_lb_per_acre**: Credit from last year (beans give ~40 lb credit)
3. Click **"Execute"**

**What you get:**
- Exactly how many pounds of N, P, K you need
- Most economical products to buy
- Application timing recommendations
- Ways to save more money

**Real Example:**
Your soil test shows P at 22 ppm, K at 145 ppm. You want 200 bu corn on 500 acres.
- System recommends: 190 lb N, 74 lb P2O5, 54 lb K2O per acre
- Best products: Anhydrous ammonia ($0.48/lb N), DAP, Potash
- Total fertilizer cost: ~$87,500
- Savings opportunities: Split N application saves $4,000

---

### 🚿 Irrigation Planning

**When to use:** You want to know when and how much to water.

#### Check Current Water Need

1. Find **"POST /api/v1/optimize/irrigation/water-need"**
2. Fill in:
   - **crop**: `corn` or `soybean`
   - **growth_stage**: Current stage (VT and R1 are critical for corn!)
   - **reference_et_inches_per_day**: Get from local weather (usually 0.20-0.35)
   - **recent_rainfall_inches**: Rain in last week
   - **soil_moisture_percent**: Your estimate (probe or feel)
3. Click **"Execute"**

**What you get:**
- How much water your crop is using per day
- Whether you need to irrigate NOW, SOON, or WAIT
- How many inches to apply
- Plain English recommendation

**Example output:**
"IRRIGATE SOON. Crop is at critical stage (VT) with soil moisture at 45%. Apply 1.2 inches within 3-5 days to prevent yield loss."

#### Calculate Irrigation Costs

1. Find **"POST /api/v1/optimize/irrigation/cost"**
2. Fill in your system info:
   - **acres**: Field size
   - **inches_to_apply**: How much water
   - **irrigation_type**: `center_pivot`, `drip`, `furrow`, etc.
   - **water_source**: `groundwater_well` or `surface_water`
   - **pumping_depth_ft**: How deep is your well?
3. Click **"Execute"**

**What you get:**
- Energy cost (electricity to pump)
- Water cost
- Labor cost
- Total cost per irrigation
- Cost per acre-inch

**Example:** 130 acres, 1 inch, center pivot, 180 ft well
- Energy: $48
- Total per irrigation: $156
- Cost per acre: $1.20

---

### 👷 Labor Cost Analysis

**When to use:** You want to know if you're spending too much on scouting and spraying.

#### Calculate Scouting Costs

1. Find **"POST /api/v1/optimize/labor/scouting"**
2. List your fields:
```json
{
  "fields": [
    {"name": "North 80", "acres": 80},
    {"name": "South 160", "acres": 160},
    {"name": "Home Farm", "acres": 200}
  ],
  "scouting_frequency_days": 7
}
```
3. Click **"Execute"**

**What you get:**
- Total hours you spend scouting per season
- Total cost (at $25/hour for a scout)
- Cost per acre
- Ways to reduce costs (group fields, use drones, etc.)

---

### 📊 Complete Farm Analysis (The Big Picture)

**When to use:** You want to see ALL your costs and find the biggest savings opportunities.

1. Find **"POST /api/v1/optimize/complete-analysis"**
2. Fill in your whole farm:
```json
{
  "total_acres": 800,
  "crops": [
    {"crop": "corn", "acres": 500, "yield_goal": 200},
    {"crop": "soybean", "acres": 300, "yield_goal": 55}
  ],
  "irrigation_type": "center_pivot",
  "water_source": "groundwater_well",
  "soil_test_p_ppm": 22,
  "soil_test_k_ppm": 155
}
```
3. Click **"Execute"**

**What you get:**
- Complete cost breakdown by category
- Total input costs for the whole farm
- Top 10 ways to save money, in order of priority
- ROI analysis showing current vs. optimized profit
- Action plan: what to do first, second, third

**Example Output:**
```
FARM SUMMARY: 800 acres (500 corn, 300 beans)

TOTAL INPUT COSTS: $298,450
  - Labor: $18,200
  - Fertilizer: $87,500
  - Pesticides: $32,750
  - Irrigation: $72,000
  - Other: $88,000

POTENTIAL SAVINGS: $42,800 (14%)

TOP RECOMMENDATIONS:
1. Switch to night irrigation - Save $5,800/year
2. Reduce scouting frequency in clean fields - Save $3,200/year
3. Use soil moisture sensors - Save $10,800/year
4. Combine P/K application in fall - Save $2,750/year
5. Compare generic pesticide options - Save $4,600/year

CURRENT NET RETURN: $156,000
OPTIMIZED NET RETURN: $198,800
IMPROVEMENT: $42,800 more profit
```

---

## Common Questions

### "I found bugs but I'm not sure what they are"
Use the pest identification tool. Describe what you see - leaf damage, color, size of bugs. The system will give you its best guess with a confidence percentage.

### "The system says to spray, but is it really worth it?"
Always check the economic threshold tool. It calculates whether the money you'll spend on spray will actually be less than the yield you'd lose. If the "net benefit" is negative, don't spray.

### "My fertilizer bill is too high"
Use the fertilizer optimization tool with your actual soil test results. Many farmers over-apply P and K because their soils are already high. The system shows you exactly what you need - no more, no less.

### "I think I'm over-irrigating"
Use the irrigation water-need calculator before every watering. It uses actual crop water use science to tell you exactly how much your crop needs based on growth stage and weather.

### "How do I know if my costs are reasonable?"
Use the quick estimate to see industry averages, then use the complete farm analysis to see how your actual costs compare. Anything more than 10% above average deserves a closer look.

---

## 🆕 FARM OPERATIONS MANAGER (NEW in v2.5)

These features help you manage your farm fields, track operations, and coordinate tasks across your team.

### 🌾 Managing Your Fields

**When to use:** Set up your farm fields to track what's planted where and log all operations.

1. Click **"Fields"** from the sidebar navigation
2. Click **"+ Add Field"** to create a new field
3. Fill in the field details:
   - **Field Name**: e.g., "North 40", "Home Quarter"
   - **Farm**: Group fields by farm name (optional)
   - **Acreage**: Field size in acres
   - **Current Crop**: Select corn, soybean, wheat, etc.
   - **Soil Type**: Clay, loam, sandy, etc.
   - **Irrigation**: None, center pivot, drip, etc.
4. Click **"Add Field"**

**What you get:**
- Summary cards showing total fields and acres
- Breakdown by crop type and farm
- Filter by farm, crop, or search by name
- Quick access to field operation history

---

### 📋 Logging Field Operations

**When to use:** Record spray applications, fertilizer, planting, harvest, tillage, and other field activities.

1. Click **"Operations"** from the sidebar navigation
2. Click **"+ Log Operation"**
3. Fill in the operation details:
   - **Field**: Select which field this operation is for
   - **Operation Type**: Spray, fertilizer, planting, harvest, tillage, scouting, etc.
   - **Date**: When the operation occurred
   - **Product Info**: Product name, rate, quantity (for sprays/fertilizer)
   - **Cost Info**: Product cost, application cost (optional)
   - **Weather**: Temperature, wind, humidity at time of application (optional)
   - **Harvest Data**: Yield and moisture (for harvest operations)
4. Click **"Log Operation"**

**What you get:**
- Complete operation history for compliance/audit trails
- Cost tracking with summary statistics
- Filter by field, operation type, date range
- Summary cards showing total operations and costs

**Operation types:**
- **Spray**: Herbicide, insecticide, fungicide applications
- **Fertilizer**: Nitrogen, P&K, micronutrients
- **Planting**: Seed and seeding rate
- **Harvest**: Yield and moisture data
- **Tillage**: Field prep, disking, plowing
- **Scouting**: Field checks and observations
- **Irrigation**: Water applications

---

### ✅ Managing Tasks (v2.5)

**When to use:** Assign work to crew members, track progress, and manage priorities.

1. Click **"Tasks"** from the sidebar navigation
2. Click **"+ New Task"** to create a task
3. Fill in:
   - **Title**: Brief description of the work
   - **Description**: Detailed instructions (optional)
   - **Priority**: Low, medium, high, urgent
   - **Assign To**: User or crew
   - **Due Date**: When it needs to be done
4. Click **"Create Task"**

**Task workflow:**
- **To Do** → **Start** → **In Progress** → **Complete**
- Quick status buttons let crew update with one click
- Overdue tasks highlighted in red
- Filter by status, priority, or "My Tasks"

---

### 🚜 Managing Equipment (v2.5)

**When to use:** Track your tractors, combines, sprayers, and other equipment with hours and maintenance schedules.

1. Click **"Equipment"** from the sidebar navigation (Equipment section)
2. Click **"+ Add Equipment"** to add a machine
3. Fill in:
   - **Name**: e.g., "John Deere 8370R", "Case 7150 Combine"
   - **Type**: Tractor, combine, sprayer, planter, tillage, truck, ATV, grain cart
   - **Make/Model/Year**: Equipment details
   - **Serial Number**: For records
   - **Purchase Date & Price**: For depreciation tracking
   - **Current Hours**: Hour meter reading
   - **Hourly Cost**: Operating cost per hour
4. Click **"Add Equipment"**

**What you get:**
- Fleet summary cards (total equipment, fleet value, total hours)
- Equipment table with status filtering (available, in use, maintenance, retired)
- Update hours button to track usage
- Log maintenance button for service records

---

### 📦 Managing Inventory (v2.5)

**When to use:** Track seeds, fertilizers, chemicals, fuel, parts, and other inputs with quantities and alerts.

1. Click **"Inventory"** from the sidebar navigation
2. Click **"+ Add Item"** to add an inventory item
3. Fill in:
   - **Name**: e.g., "Pioneer P1197", "Roundup PowerMax", "Diesel Fuel"
   - **Category**: Seed, fertilizer, chemical, fuel, parts, supplies
   - **Quantity & Unit**: Current stock (e.g., 50 bags, 200 gallons)
   - **Reorder Point**: Get alerts when stock drops below this level
   - **Storage Location**: Where it's stored
   - **Batch/Lot Number**: For chemicals and seed
   - **Expiration Date**: For chemicals (get expiring soon alerts)
   - **Cost Per Unit**: For value tracking
4. Click **"Add Item"**

**Quick Actions:**
- **Quick Purchase**: Record a purchase with vendor and invoice info
- **Adjust Quantity**: Correct inventory counts with reason tracking
- **View Transactions**: See purchase and usage history

**Alerts:**
- **Low Stock**: Items below reorder point (yellow warning)
- **Expiring Soon**: Chemicals expiring within 30 days (red warning)

---

### 🔧 Maintenance Scheduling (v2.5)

**When to use:** Track equipment service schedules and get alerts for overdue or upcoming maintenance.

1. Click **"Maintenance"** from the sidebar navigation
2. View the **Alerts Tab** to see:
   - **Overdue** (red): Maintenance past due date or hours
   - **Due Soon** (orange): Coming up within 7 days or 50 hours
   - **Upcoming** (blue): Scheduled in the next 30 days
3. View the **History Tab** to see past maintenance records
4. Filter by equipment or maintenance type

**Logging Maintenance:**
1. Go to Equipment screen
2. Click **"Log Maintenance"** on any equipment
3. Fill in:
   - **Maintenance Type**: Oil change, filter, tires, repairs, inspection, etc.
   - **Date**: When service was performed
   - **Hours at Service**: Current hour meter
   - **Cost**: Total service cost
   - **Vendor**: Who did the work
   - **Parts Used**: List of parts
   - **Next Service**: Date or hours for next service
4. Click **"Log Maintenance"**

---

### 📊 Reports & Analytics Dashboard (v2.5)

**When to use:** Get insights across all your farm operations with charts and exportable reports.

1. Click **"Reports"** from the sidebar navigation (Analytics section)
2. Set the **Date Range** using From/To date pickers
3. Navigate between the **4 tabs**:

**Tab 1: Operations Overview**
- Summary cards: Total operations, total cost, average cost/acre
- Bar chart: Operations by type (spray, fertilizer, planting, etc.)
- Operations table with details

**Tab 2: Financial Analysis**
- Summary cards: Total input costs, equipment costs, revenue, net profit
- Cost breakdown chart by category
- Profit/loss by field

**Tab 3: Equipment & Inventory**
- Fleet statistics: Value, hours logged, items in stock
- Equipment utilization chart
- Maintenance alerts and low stock items tables

**Tab 4: Field Performance**
- Summary cards: Total fields, acres, average yield
- Field comparison chart
- Field summary table with yields and costs

**Export to CSV:**
- Click **"Export CSV"** button
- Select report type (operations, financial, equipment, inventory, fields)
- Save file for spreadsheet analysis

---

## 🆕 MOBILE CREW INTERFACE (NEW in v2.6)

A mobile-friendly web interface for field crews to view tasks, log time, and upload photos from the field.

### 📱 Accessing the Mobile Interface

With the backend running, open a mobile browser:

**http://localhost:8000/m/login**

### What Crews Can Do

1. **View Task List** - See assigned tasks with status and priority badges
2. **One-Tap Status Updates** - Start, complete, or reopen tasks instantly
3. **Log Time** - Track hours worked (work, travel, break types)
4. **Upload Photos** - Capture field photos with GPS coordinates
5. **Work Offline** - PWA caches pages for offline access
6. **Install as App** - Add to home screen for app-like experience

### Mobile Routes

| Route | Purpose |
|-------|---------|
| `/m/login` | Mobile login page |
| `/m/tasks` | Task list with filters |
| `/m/tasks/{id}` | Task detail with actions |

### PWA Features

- **Offline Support** - Service worker caches static assets and pages
- **Installable** - Add to home screen on iOS/Android
- **Auto-Sync** - Pages reload when back online

---

## 🆕 COST PER ACRE TRACKING (NEW in v2.7)

Track all your farm expenses from QuickBooks and calculate true cost-per-acre by field and by crop.

### 💰 What This Feature Does

1. **Import from QuickBooks** - Upload CSV exports or scan receipts
2. **Auto-Categorize** - Automatically detects seed, fertilizer, chemical, fuel, etc.
3. **Split Allocations** - Allocate one expense across multiple fields by percentage
4. **Cost Reports** - See cost-per-acre by field, by crop, by category
5. **Year Comparison** - Compare costs across years

### 📊 Expense Categories

The system tracks 13 expense categories:

**Inputs:**
- Seed, Fertilizer, Chemical (herbicides/insecticides/fungicides), Fuel

**Operations:**
- Repairs, Labor, Custom Hire

**Overhead:**
- Land Rent, Crop Insurance, Interest, Utilities, Storage

**Other:**
- Miscellaneous expenses

---

### 📥 Importing Expenses from CSV

**When to use:** You exported a report from QuickBooks and want to import the expenses.

#### Step 1: Preview Your CSV

1. Find **"POST /api/v1/costs/import/csv/preview"**
2. Upload your QuickBooks CSV file
3. The system shows:
   - Column headers from your file
   - Sample rows
   - Suggested column mappings

#### Step 2: Import with Column Mapping

1. Find **"POST /api/v1/costs/import/csv"**
2. Upload your CSV file
3. Set the column mappings:
   - **amount_column**: Which column has the dollar amount (e.g., "Amount", "Debit")
   - **date_column**: Which column has the date (e.g., "Date", "Trans Date")
   - **vendor_column**: Which column has the vendor name (optional)
   - **description_column**: Which column has the memo/description (optional)
   - **reference_column**: Which column has the check/invoice number (for duplicate detection)
4. Click **"Execute"**

**What you get:**
- Count of imported expenses
- Count of duplicates skipped
- Any errors encountered
- Batch ID for tracking/rollback

**Example QuickBooks columns:**
```
Date, Type, Num, Name, Memo, Account, Debit, Credit
```
Map: amount_column="Debit", date_column="Date", vendor_column="Name", description_column="Memo", reference_column="Num"

---

### 📸 Importing from Scanned Receipts (OCR)

**When to use:** You have scanned invoices or receipts and want to extract the expenses.

**Prerequisites:** Install OCR libraries:
```bash
pip install pytesseract Pillow pdf2image
```
Also install Tesseract OCR on your system.

1. Find **"POST /api/v1/costs/import/scan"**
2. Upload your image (JPG, PNG) or PDF
3. Click **"Execute"**

**What you get:**
- Extracted expenses with amounts, dates, vendors
- Confidence scores (low-confidence items flagged for review)
- Warnings about any extraction issues

**Note:** OCR works best with:
- Clear, high-resolution scans
- Standard invoice formats
- Machine-printed text (not handwritten)

---

### 🔍 Reviewing OCR Extractions

**When to use:** After OCR import, review and correct any low-confidence extractions.

1. Find **"GET /api/v1/costs/review"** - See all expenses needing review
2. For each expense, verify the amount, date, vendor, and category
3. Find **"POST /api/v1/costs/expenses/{expense_id}/approve"**
4. Optionally provide corrections in the request body
5. Click **"Execute"** to approve

---

### ✏️ Manual Expense Entry

**When to use:** Add an expense manually (not from import).

1. Find **"POST /api/v1/costs/expenses"**
2. Fill in:
```json
{
  "category": "fertilizer",
  "vendor": "Local Co-op",
  "description": "Spring nitrogen application",
  "amount": 8500.00,
  "expense_date": "2024-04-15",
  "tax_year": 2024
}
```
3. Click **"Execute"**

**Category options:** seed, fertilizer, chemical, fuel, repairs, labor, custom_hire, land_rent, crop_insurance, interest, utilities, storage, other

---

### 📋 Viewing and Filtering Expenses

**When to use:** See all your expenses with filters.

1. Find **"GET /api/v1/costs/expenses"**
2. Optional filters:
   - **tax_year**: Filter by year (e.g., 2024)
   - **category**: Filter by category (e.g., "fertilizer")
   - **vendor**: Search by vendor name
   - **unallocated_only**: Set to `true` to see expenses not yet assigned to fields
   - **start_date** / **end_date**: Date range filter
3. Click **"Execute"**

**What you get:**
- List of expenses with all details
- Allocation percentage (how much has been assigned to fields)

---

### 🏗️ Allocating Expenses to Fields

This is the key step - assigning each expense to one or more fields so you can calculate cost-per-acre.

#### Single Field Allocation (100%)

**When to use:** An expense applies to just one field.

1. Find **"POST /api/v1/costs/expenses/{expense_id}/allocations"**
2. Fill in:
```json
[
  {
    "field_id": 1,
    "crop_year": 2024,
    "allocation_percent": 100
  }
]
```
3. Click **"Execute"**

#### Split Allocation (Multiple Fields)

**When to use:** An expense applies to multiple fields (e.g., bulk fertilizer purchase).

1. Find **"POST /api/v1/costs/expenses/{expense_id}/allocations"**
2. Fill in with percentages that total 100% or less:
```json
[
  {
    "field_id": 1,
    "crop_year": 2024,
    "allocation_percent": 40,
    "notes": "North 80 - 40 acres"
  },
  {
    "field_id": 2,
    "crop_year": 2024,
    "allocation_percent": 35,
    "notes": "South 160 - 35 acres"
  },
  {
    "field_id": 3,
    "crop_year": 2024,
    "allocation_percent": 25,
    "notes": "Home Farm - 25 acres"
  }
]
```
3. Click **"Execute"**

#### Get Allocation Suggestions

**When to use:** You want to split an expense proportionally by field acreage.

1. Find **"POST /api/v1/costs/allocations/suggest"**
2. Provide the field IDs:
```json
{
  "field_ids": [1, 2, 3]
}
```
3. Click **"Execute"**

**What you get:**
- Each field with suggested percentage based on acreage
- Example: 80 acres + 160 acres + 200 acres = 18.2%, 36.4%, 45.4%

---

### 📊 Cost Per Acre Reports

The payoff - see your actual cost per acre by field!

#### Cost Per Acre by Field

1. Find **"GET /api/v1/costs/reports/per-acre"**
2. Set **crop_year** (e.g., 2024)
3. Optionally filter by **field_ids** (comma-separated)
4. Click **"Execute"**

**What you get:**
```json
{
  "crop_year": 2024,
  "total_fields": 5,
  "total_acreage": 800.0,
  "total_cost": 376000.0,
  "average_cost_per_acre": 470.0,
  "fields": [
    {
      "field_name": "North 80",
      "acreage": 80.0,
      "total_cost": 42000.0,
      "cost_per_acre": 525.0,
      "by_category": {
        "seed": 8000.0,
        "fertilizer": 15000.0,
        "chemical": 6400.0,
        "fuel": 3200.0,
        "land_rent": 9400.0
      }
    }
  ]
}
```

#### Category Breakdown

1. Find **"GET /api/v1/costs/reports/by-category"**
2. Set **crop_year**
3. Optionally filter by **field_id**
4. Click **"Execute"**

**What you get:**
- Each category with total amount and percentage of total
- Example: Fertilizer = $87,500 (23.3%), Land Rent = $96,000 (25.5%)

#### Cost by Crop Type

1. Find **"GET /api/v1/costs/reports/by-crop"**
2. Set **crop_year**
3. Click **"Execute"**

**What you get:**
- Cost per acre by crop (corn, soybeans, etc.)
- Great for comparing profitability across crops

#### Year-Over-Year Comparison

1. Find **"POST /api/v1/costs/reports/comparison"**
2. Provide years to compare:
```json
{
  "years": [2022, 2023, 2024],
  "field_id": null
}
```
3. Click **"Execute"**

**What you get:**
- Total cost, total acres, and cost per acre for each year
- See how your costs have changed

---

### 🔄 Managing Import Batches

#### View Import History

1. Find **"GET /api/v1/costs/imports"**
2. Click **"Execute"**
3. See all your import batches with success/fail counts

#### Rollback an Import

**When to use:** You imported the wrong file or need to redo an import.

1. Find **"DELETE /api/v1/costs/imports/{batch_id}"**
2. Enter the batch ID
3. Click **"Execute"**
4. All expenses from that import are deleted

---

### 💾 Saving Column Mappings

**When to use:** Save your QuickBooks column mapping for reuse.

1. Find **"POST /api/v1/costs/mappings"**
2. Fill in:
```json
{
  "mapping_name": "QuickBooks Transaction Detail",
  "column_config": {
    "amount": "Debit",
    "date": "Date",
    "vendor": "Name",
    "description": "Memo",
    "reference": "Num"
  },
  "source_type": "QuickBooks",
  "is_default": true
}
```
3. Click **"Execute"**

Next time you import, you can use **"GET /api/v1/costs/mappings"** to retrieve your saved mappings.

---

## 🆕 QUICKBOOKS IMPORT (NEW in v2.9)

Direct import from QuickBooks exports with automatic format detection, smart account mapping, and expense filtering.

### 📥 Why Use QuickBooks Import?

The v2.7 cost tracking requires manual column mapping for each CSV. The v2.9 QuickBooks Import:
- **Auto-detects** your QuickBooks export format (Desktop or Online)
- **Auto-maps** your QB accounts to AgTools expense categories
- **Auto-filters** to expenses only (skips deposits, transfers, invoices)
- **Saves your mappings** for one-click future imports

### 📋 Supported QuickBooks Formats

| Format | How to Export |
|--------|---------------|
| QB Desktop - Transaction Detail | Reports → Transaction Detail by Account → Export CSV |
| QB Desktop - Transaction List | Reports → Transaction List by Date → Export CSV |
| QB Desktop - Check Detail | Reports → Check Detail → Export CSV |
| QB Online | Transactions → Export → CSV |

### 📥 Step 1: Preview Your QuickBooks Export

1. Find **"POST /api/v1/quickbooks/preview"**
2. Upload your QuickBooks CSV file
3. Click **"Execute"**

**What you get:**
- **Format detected**: Which QB export type was recognized
- **Expense rows**: How many expense transactions found
- **Skipped rows**: How many non-expense transactions (deposits, transfers) will be skipped
- **Accounts found**: List of your QB accounts with suggested category mappings
- **Unmapped accounts**: Accounts that need manual mapping

**Example preview:**
```
Format: desktop_transaction_detail
Total rows: 250
Expense rows: 180
Skipped: 70 (deposits, transfers)

Accounts found:
  Farm Expense:Seed       → seed (suggested)
  Farm Expense:Fertilizer → fertilizer (suggested)
  Farm Expense:Chemical   → chemical (suggested)
  Equipment Repair        → repairs (suggested)
  Custom Work             → NOT MAPPED (needs assignment)
```

### 📥 Step 2: Import with Account Mappings

1. Find **"POST /api/v1/quickbooks/import"**
2. Upload your CSV file
3. Provide account mappings as JSON:
```json
{
  "Farm Expense:Seed": "seed",
  "Farm Expense:Fertilizer": "fertilizer",
  "Farm Expense:Chemical": "chemical",
  "Equipment Repair": "repairs",
  "Custom Work": "custom_hire"
}
```
4. Click **"Execute"**

**What you get:**
- **Successful imports**: Number of expenses created
- **Skipped**: Non-expense transactions and duplicates
- **By category**: Breakdown of imports by category
- **Total amount**: Sum of all imported expenses

### 📋 Default Account Mappings

The system includes 73 default mappings for common farm accounts:

| QB Account Pattern | AgTools Category |
|-------------------|------------------|
| seed, pioneer, dekalb, asgrow | seed |
| fertilizer, fert, urea, dap, potash | fertilizer |
| chemical, herbicide, insecticide, fungicide | chemical |
| fuel, diesel, gasoline | fuel |
| repair, maintenance, parts | repairs |
| labor, payroll, wages | labor |
| custom hire, aerial, trucking | custom_hire |
| land rent, cash rent, lease | land_rent |
| crop insurance | crop_insurance |
| interest, loan | interest |
| utilities, electric, water | utilities |
| storage, drying, elevator | storage |

### 💾 Saving Your Mappings

Your account mappings are automatically saved after each import. For future imports:

1. Find **"GET /api/v1/quickbooks/mappings"** - View your saved mappings
2. Next import will auto-suggest using your saved mappings
3. Update mappings: **"POST /api/v1/quickbooks/mappings"**
4. Delete a mapping: **"DELETE /api/v1/quickbooks/mappings/{id}"**

### 📋 QuickBooks Import Workflow

1. **Export from QuickBooks** - Transaction Detail by Account works best
2. **Preview** - Upload to `/api/v1/quickbooks/preview`
3. **Review mappings** - Check suggested categories, map any unmapped accounts
4. **Import** - Upload to `/api/v1/quickbooks/import` with your mappings
5. **Allocate to fields** - Use cost tracking endpoints to assign expenses to fields
6. **View reports** - See cost-per-acre by field, crop, and category

**Best Practice:** Run QuickBooks exports quarterly and import to stay current on your costs.

---

## 🆕 AI/ML INTELLIGENCE SUITE (NEW in v3.0)

Five AI-powered features that learn from your data and improve over time.

### 📸 AI Image Identification

**When to use:** You're in the field with your phone and want to identify a pest or disease from a photo.

1. Find **"POST /api/v1/ai/identify/image"**
2. Upload your field photo (JPG, PNG)
3. Click **"Execute"**

**What you get:**
- Top 5 possible identifications with confidence scores
- Links to pest/disease details from the knowledge base
- Management recommendations

**How it improves:**
- Submit feedback when predictions are wrong
- The system collects training data for custom model development
- Over time, accuracy increases for your specific region and conditions

---

### 🌿 Crop Health Scoring from Imagery

**When to use:** You have drone or satellite imagery of a field and want to assess health.

1. Find **"POST /api/v1/ai/health/analyze"**
2. Upload your field image
3. Optionally specify number of zones for grid analysis
4. Click **"Execute"**

**What you get:**
- Overall field health score (Excellent to Critical)
- NDVI or pseudo-NDVI calculation
- Zone-by-zone health breakdown
- Problem detection (water stress, nutrient deficiency, pest damage)
- Specific recommendations for problem areas

**Health Levels:**
| Status | NDVI Range | What it means |
|--------|------------|---------------|
| Excellent | > 0.7 | Healthy, vigorous crop |
| Good | 0.5 - 0.7 | Normal growth |
| Moderate | 0.3 - 0.5 | Minor stress, monitor |
| Stressed | 0.2 - 0.3 | Intervention needed |
| Poor | 0.1 - 0.2 | Significant problems |
| Critical | < 0.1 | Severe damage |

---

### 📊 Yield Prediction Model

**When to use:** You want to estimate expected yield based on your field inputs.

1. Find **"POST /api/v1/ai/yield/predict"**
2. Fill in your field data:
```json
{
  "crop": "corn",
  "field_id": 1,
  "planted_acres": 160,
  "plant_population": 34000,
  "nitrogen_applied": 180,
  "phosphorus_applied": 60,
  "potassium_applied": 40,
  "previous_crop": "soybean",
  "planting_date": "2025-04-25",
  "irrigation_type": "center_pivot"
}
```
3. Click **"Execute"**

**What you get:**
- Predicted yield (e.g., 195 bu/acre)
- Confidence interval (e.g., 185-205 bu/acre)
- Factors affecting the prediction
- Comparison to crop defaults

**Training your model:**
1. After harvest, record actual yields: **"POST /api/v1/ai/yield/record"**
2. Train model from your data: **"POST /api/v1/ai/yield/train"**
3. Check model status: **"GET /api/v1/ai/yield/model-status"**

The more years of data you provide, the more accurate predictions become for your specific fields.

---

### 💰 Smart Expense Categorization

**When to use:** You have expense descriptions and want them auto-categorized.

1. Find **"POST /api/v1/ai/expense/categorize"**
2. Fill in:
```json
{
  "description": "Pioneer P1197 seed corn 80 bags",
  "vendor": "Local Co-op",
  "amount": 18500.00
}
```
3. Click **"Execute"**

**What you get:**
- Predicted category (e.g., "seed")
- Confidence score (e.g., 0.95)
- Alternative suggestions if confidence is low

**19 Categories:**
seed, fertilizer, chemical, fuel, repairs, labor, custom_hire, land_rent, crop_insurance, interest, utilities, storage, equipment, marketing, trucking, supplies, professional_services, taxes, other

**Batch categorization:**
- Use **"POST /api/v1/ai/expense/categorize-batch"** to categorize multiple expenses at once

**Training from corrections:**
1. When the system is wrong, submit feedback: **"POST /api/v1/ai/expense/feedback"**
2. Periodically train: **"POST /api/v1/ai/expense/train"**
3. Accuracy improves with your corrections

---

### 🌤️ Weather-Based Spray AI

**When to use:** You want ML-enhanced spray timing predictions that improve with your outcomes.

1. Find **"POST /api/v1/ai/spray/predict"**
2. Fill in current conditions:
```json
{
  "field_id": 1,
  "spray_type": "fungicide",
  "target_pest": "gray_leaf_spot",
  "temperature_f": 78,
  "humidity_pct": 55,
  "wind_mph": 6,
  "hours_until_rain": 48,
  "pest_pressure": "moderate"
}
```
3. Click **"Execute"**

**What you get:**
- Spray timing recommendation (Spray Now, Wait, Caution)
- Confidence score
- Optimal window timing
- Risk factors

**Recording outcomes for learning:**
1. Record application: **"POST /api/v1/ai/spray/record"**
2. After 2-4 weeks, record outcome: **"POST /api/v1/ai/spray/outcome"**
```json
{
  "application_id": 123,
  "efficacy_score": 85,
  "notes": "Good control, some escapes in low areas"
}
```
3. Train model: **"POST /api/v1/ai/spray/train"**

**How it learns:**
- Tracks which conditions led to good vs. poor efficacy
- Learns your micro-climate patterns
- Adjusts recommendations based on your specific fields
- Improves with each recorded outcome

---

### 📋 Quick Reference: AI/ML Workflow

1. **Start using AI features** - They work immediately with default models
2. **Submit feedback when wrong** - Helps improve accuracy
3. **Record actual outcomes** - Yields, spray efficacy, expense corrections
4. **Train periodically** - Use the /train endpoints after collecting data
5. **Check model status** - See accuracy metrics and training data counts

**The more data you provide, the smarter the system becomes for YOUR farm.**

---

### 📋 Quick Reference: Cost Tracking Workflow

1. **Export from QuickBooks** - Get your expenses as CSV
2. **Preview CSV** - Check column detection
3. **Import CSV** - Map columns and import
4. **Review** - Check any OCR or low-confidence items
5. **Allocate** - Assign each expense to fields
6. **Report** - View cost per acre by field

**Best Practice:** Do this quarterly or monthly to stay on top of your costs.

---

## 🆕 REAL-TIME PRICING (NEW in v2.1)

These features let you use YOUR actual prices instead of averages, so your cost calculations are accurate.

### 💲 Adding Your Supplier Quotes

**When to use:** You got a quote from your co-op or dealer and want to use those real prices.

1. Find **"POST /api/v1/pricing/set-price"**
2. Fill in:
```json
{
  "product_id": "urea_46",
  "price": 0.48,
  "supplier": "Local Co-op",
  "notes": "Early booking discount"
}
```
3. Click **"Execute"**

**What you get:**
- Confirmation your price was saved
- Comparison to default price - are you getting a good deal?
- Savings percentage

**Common product IDs:**
- Fertilizers: `urea_46`, `anhydrous_ammonia_82`, `dap_18_46`, `potash_60`, `uan_32`
- Herbicides: `glyphosate_generic`, `dicamba_xtendimax`, `liberty_280`
- Insecticides: `bifenthrin_generic`, `warrior_ii`, `prevathon`
- Fungicides: `headline_amp`, `trivapro`, `delaro_325`

---

### 🛒 Should I Buy Now or Wait?

**When to use:** Prices are high and you're wondering if they'll come down.

1. Find **"POST /api/v1/pricing/buy-recommendation"**
2. Fill in:
```json
{
  "product_id": "urea_46",
  "quantity_needed": 50000,
  "purchase_deadline": "2025-03-01T00:00:00"
}
```
3. Click **"Execute"**

**What you get:**
- Current price vs. 90-day average
- Price trend (rising, falling, stable)
- Clear recommendation: BUY NOW, WAIT, or SPLIT PURCHASE
- Reasoning: "Prices trending down, currently 8% above average"

---

### 📋 Loading All Your Prices at Once

**When to use:** Your dealer gave you a complete price list and you want to load it all.

1. Find **"POST /api/v1/pricing/bulk-update"**
2. Fill in:
```json
{
  "price_updates": [
    {"product_id": "urea_46", "price": 0.48},
    {"product_id": "dap_18_46", "price": 0.58},
    {"product_id": "potash_60", "price": 0.38},
    {"product_id": "glyphosate_generic", "price": 3.80}
  ],
  "supplier": "County Co-op"
}
```
3. Click **"Execute"**

**What you get:**
- All prices updated at once
- Total potential savings across all products

---

## 🆕 WEATHER-SMART SPRAY TIMING (NEW in v2.1)

These features help you spray at the right time and avoid wasted applications.

### 🌤️ Can I Spray Right Now?

**When to use:** You're ready to spray but want to check if conditions are good.

1. Find **"POST /api/v1/spray-timing/evaluate"**
2. Fill in current weather:
```json
{
  "weather": {
    "datetime": "2025-06-15T10:00:00",
    "temp_f": 78,
    "humidity_pct": 55,
    "wind_mph": 6,
    "wind_direction": "SW",
    "precip_chance_pct": 10,
    "precip_amount_in": 0,
    "cloud_cover_pct": 30,
    "dew_point_f": 58
  },
  "spray_type": "herbicide",
  "product_name": "glyphosate"
}
```
3. Click **"Execute"**

**What you get:**
- Risk level: EXCELLENT, GOOD, MARGINAL, POOR, or DO NOT SPRAY
- Score out of 100
- Specific issues: "Wind approaching limit (8 mph)"
- Clear recommendation: "Good conditions - proceed with application"

---

### ⏰ Should I Spray Today or Wait?

**When to use:** Conditions aren't perfect but you're worried about yield loss from waiting.

1. Find **"POST /api/v1/spray-timing/cost-of-waiting"**
2. Fill in your situation:
```json
{
  "current_conditions": {
    "datetime": "2025-06-15T10:00:00",
    "temp_f": 88,
    "humidity_pct": 40,
    "wind_mph": 12,
    "wind_direction": "S",
    "precip_chance_pct": 5,
    "precip_amount_in": 0,
    "cloud_cover_pct": 20,
    "dew_point_f": 55
  },
  "forecast": [],
  "spray_type": "fungicide",
  "acres": 160,
  "product_cost_per_acre": 22.00,
  "application_cost_per_acre": 8.50,
  "target_pest_or_disease": "gray_leaf_spot",
  "current_pressure": "moderate",
  "crop": "corn",
  "yield_goal": 200,
  "grain_price": 4.50
}
```
3. Click **"Execute"**

**What you get:**
- Cost to spray now (including wasted product risk)
- Cost to wait (yield loss estimate)
- Clear recommendation: SPRAY NOW, WAIT, or SPRAY NOW WITH CAUTION
- Reasoning: "Yield loss risk ($2,340) outweighs efficacy risk. Use drift reduction."
- Action items: specific steps to take

**Example output:**
```
RECOMMENDATION: SPRAY NOW (with caution)

REASONING: Yield loss from waiting ($2,340) exceeds efficacy
risk from current conditions. Use drift reduction measures.

COST TO SPRAY NOW: $5,180 (including 15% efficacy risk)
COST TO WAIT: $2,340 (yield loss over 48 hours)

ACTION ITEMS:
- Use drift reduction nozzles (AI, TTI)
- Reduce spray pressure to 30-40 PSI
- Increase carrier volume to 15+ GPA
- Monitor radar closely
```

---

### 🦠 Is Disease Pressure Building?

**When to use:** You want to know if recent weather has created disease risk.

1. Find **"POST /api/v1/spray-timing/disease-pressure"**
2. Fill in recent weather (past 7-14 days):
```json
{
  "weather_history": [
    {"datetime": "2025-06-08T12:00:00", "temp_f": 78, "humidity_pct": 85, "wind_mph": 5, "precip_amount_in": 0.2, "dew_point_f": 68},
    {"datetime": "2025-06-09T12:00:00", "temp_f": 80, "humidity_pct": 90, "wind_mph": 3, "precip_amount_in": 0.5, "dew_point_f": 72},
    {"datetime": "2025-06-10T12:00:00", "temp_f": 82, "humidity_pct": 88, "wind_mph": 4, "precip_amount_in": 0, "dew_point_f": 70}
  ],
  "crop": "corn",
  "growth_stage": "VT"
}
```
3. Click **"Execute"**

**What you get:**
- Risk level for each disease: HIGH, MODERATE, LOW, MINIMAL
- Which weather factors triggered the risk
- Clear recommendation: "High disease pressure for Gray Leaf Spot. Consider preventive fungicide."

---

### 🌱 When Should I Spray for This Growth Stage?

**When to use:** You want to know the optimal timing for a spray at your crop's current stage.

1. Find **"GET /api/v1/spray-timing/growth-stage-timing/{crop}/{growth_stage}"**
2. Fill in:
   - **crop**: `corn` or `soybean`
   - **growth_stage**: Current stage like `VT`, `R3`, etc.
   - **spray_type**: `fungicide`, `insecticide`, or `herbicide`
3. Click **"Execute"**

**What you get:**
- Timing recommendation for this stage
- Key considerations
- Suggested products

**Example for corn at VT with fungicide:**
```
TIMING: OPTIMAL timing for fungicide ROI
CONSIDERATIONS:
- Apply at VT to R2
- Protect ear leaf
SUGGESTED PRODUCTS:
- Headline AMP
- Trivapro
- Miravis Neo
```

---

## 🆕 YIELD RESPONSE & ECONOMIC OPTIMUM RATES (NEW in v2.2)

These features help you find the **most profitable fertilizer rate** - not just the rate for maximum yield. This is important because the last 20-30 lb of nitrogen often costs more than it returns.

### 📊 What's My Most Profitable N Rate?

**When to use:** Before you apply fertilizer, find out the rate that maximizes profit.

1. Find **"POST /api/v1/yield-response/economic-optimum"**
2. Fill in:
```json
{
  "crop": "corn",
  "nutrient": "nitrogen",
  "soil_test_level": "medium",
  "yield_potential": 200,
  "previous_crop": "soybean",
  "nutrient_cost_per_lb": 0.65,
  "grain_price_per_bu": 4.50
}
```
3. Click **"Execute"**

**What you get:**
- Economic optimum rate (EOR) - the most profitable rate
- Maximum yield rate - what you'd need for absolute max yield
- How much yield you sacrifice (usually only 1-3 bu)
- How much money you SAVE by not over-applying
- Net return per acre at each rate

**Example output:**
```
ECONOMIC OPTIMUM RATE: 168 lb N/acre

vs. Maximum Yield Rate: 195 lb N/acre

What this means:
- At 168 lb N: Yield = 197.2 bu, Net return = $778/acre
- At 195 lb N: Yield = 198.5 bu, Net return = $764/acre

YOU SAVE: $14.15/acre by applying 27 lb LESS nitrogen
YIELD SACRIFICE: Only 1.3 bu/acre

RECOMMENDATION: Apply 168 lb N/acre. The last 27 lb of N
costs $17.55 but only returns $5.85 in grain. Not worth it.
```

---

### 💵 Compare Different N Rates

**When to use:** You're debating between different rates (like 150 vs 180 vs 200).

1. Find **"POST /api/v1/yield-response/compare-rates"**
2. Fill in:
```json
{
  "crop": "corn",
  "nutrient": "nitrogen",
  "soil_test_level": "medium",
  "yield_potential": 200,
  "rates_to_compare": [120, 150, 180, 210],
  "nutrient_cost_per_lb": 0.65,
  "grain_price_per_bu": 4.50
}
```
3. Click **"Execute"**

**What you get:**
- Yield at each rate
- Fertilizer cost at each rate
- Net return at each rate
- Ranking from most to least profitable

**Example:** You'll see that 180 lb might give $774/acre net return while 210 lb only gives $761/acre - more fertilizer, LESS profit!

---

### 📈 How Do Prices Change My Optimal Rate?

**When to use:** Fertilizer prices are different than last year and you want to know how to adjust.

1. Find **"POST /api/v1/yield-response/price-sensitivity"**
2. Fill in different price scenarios:
```json
{
  "crop": "corn",
  "nutrient": "nitrogen",
  "soil_test_level": "medium",
  "yield_potential": 200,
  "nutrient_cost_range": [0.45, 0.55, 0.65, 0.75, 0.85],
  "grain_price_range": [4.00, 4.50, 5.00, 5.50]
}
```
3. Click **"Execute"**

**What you get:**
A table showing optimal rate at every price combination:
- Cheap N + high corn = apply more (190+ lb)
- Expensive N + cheap corn = back off (150-160 lb)

---

### 🌽 Optimize N, P, and K Together

**When to use:** You have a budget and want to allocate it optimally across all nutrients.

1. Find **"POST /api/v1/yield-response/multi-nutrient"**
2. Fill in:
```json
{
  "crop": "corn",
  "yield_potential": 200,
  "soil_test_p_ppm": 18,
  "soil_test_k_ppm": 145,
  "previous_crop": "soybean",
  "budget_per_acre": 150,
  "nutrient_prices": {
    "nitrogen": 0.65,
    "phosphorus": 0.75,
    "potassium": 0.45
  },
  "grain_price": 4.50
}
```
3. Click **"Execute"**

**What you get:**
- Optimal lb/acre of N, P2O5, and K2O
- Whether you're under/over budget
- Expected yield and net return
- Whether budget is limiting your yield

---

### 📋 Quick Reference: Price Ratio Guide

**When to use:** You want a simple rule of thumb for adjusting rates.

1. Find **"GET /api/v1/yield-response/price-ratio-guide"**
2. Click **"Execute"**

**What you get:**
A printable table you can take to the field:

| Price Ratio* | What to do |
|--------------|-----------|
| Under 0.10 | Apply max rate |
| 0.10 - 0.15 | Reduce 5-15% |
| 0.15 - 0.20 | Reduce 15-20% |
| Over 0.20 | Reduce 25%+ |

*Price Ratio = N cost per lb ÷ corn price per bu

**Example:** N at $0.65/lb, corn at $4.50/bu = 0.144 ratio → reduce about 10% from max.

---

## The Bottom Line

**This system helps you answer the questions that cost you money:**

1. What is this pest/disease?
2. Should I spray or wait?
3. What product should I use?
4. Am I spending too much on fertilizer?
5. Am I over-irrigating?
6. Where are my biggest opportunities to save money?
7. **Am I getting good prices from my supplier?** (v2.1)
8. **Is now a good time to spray?** (v2.1)
9. **What's my most profitable fertilizer rate?** (v2.2)
10. **How should I adjust rates when prices change?** (v2.2)
11. **What's my actual cost per acre by field?** (v2.7)
12. **Where are my biggest expense categories?** (v2.7)
13. **How do my costs compare year-over-year?** (v2.7)
14. **How do I get my QuickBooks data into AgTools?** (v2.9)
15. **What accounts do I map to what categories?** (v2.9)
16. **What pest or disease is in this photo?** (v3.0 - AI Image ID)
17. **How healthy is my field from this drone image?** (v3.0 - Crop Health)
18. **What yield should I expect this year?** (v3.0 - Yield Prediction)
19. **What category is this expense?** (v3.0 - Smart Categorization)
20. **When is the best time to spray based on my past results?** (v3.0 - Spray AI)
21. **How do I manage employees and payroll?** (v3.9.0 - Enterprise Operations)
22. **What are my land lease payments?** (v3.9.0 - Land & Lease Management)
23. **What's my cash flow look like for the next year?** (v3.9.0 - Cash Flow Forecasting)
24. **What yield should I expect based on my history and weather?** (v4.0.0 - Yield Prediction Engine)
25. **What seeding rate should I use in each zone?** (v4.0.0 - Variable Rate Prescriptions)
26. **When should I plant, spray, or harvest?** (v4.0.0 - Decision Support AI)
27. **How much grain is in each bin and what's the moisture?** (v4.1.0 - Grain Storage)
28. **How much will it cost to dry this grain?** (v4.1.0 - Drying Calculator)
29. **Alert me when basis hits my target** (v4.1.0 - Basis Alerts)
30. **What's my depreciation schedule for tax planning?** (v4.2.0 - Tax Tools)
31. **How do I plan my farm succession?** (v4.2.0 - Succession Planning)
32. **How do I compare to regional benchmarks?** (v4.2.0 - Benchmarking)

**Every dollar saved on inputs goes straight to your bottom line.**

---

## 🆕 ENTERPRISE OPERATIONS SUITE (NEW in v3.9)

These features help you manage the business side of your farm operation.

### 👷 Labor & Crew Management

**When to use:** Track employees, certifications, time entries, and payroll calculations.

#### Adding Employees

1. Find **"POST /api/v1/labor/employees"**
2. Fill in employee details:
```json
{
  "name": "John Smith",
  "email": "john@farm.com",
  "phone": "555-123-4567",
  "employee_type": "full_time",
  "pay_type": "hourly",
  "pay_rate": 18.50,
  "hire_date": "2024-01-15",
  "job_title": "Equipment Operator",
  "department": "Field Operations"
}
```
3. Click **"Execute"**

**Employee Types:** full_time, part_time, seasonal, contractor
**Pay Types:** hourly, salary, piece_rate

#### Tracking Certifications

1. Find **"POST /api/v1/labor/employees/{id}/certifications"**
2. Add certifications like CDL, pesticide applicator license, etc.
3. System alerts you when certifications are expiring

**Certification Types:** cdl_class_a, cdl_class_b, pesticide_applicator, commercial_applicator, first_aid, hazmat, forklift, grain_handling

#### Time Tracking

1. Find **"POST /api/v1/labor/time-entries"**
2. Record hours worked:
```json
{
  "employee_id": "EMP-0001",
  "entry_type": "regular",
  "date": "2025-03-15",
  "hours": 10.5,
  "break_hours": 0.5,
  "field_id": "FIELD-001",
  "task_description": "Planting corn",
  "equipment_used": "JD 8R 340"
}
```

**Entry Types:** regular, overtime, travel, training, maintenance

#### Payroll Calculations

1. Find **"GET /api/v1/labor/payroll-summary"**
2. Set date range and get:
   - Regular hours and pay by employee
   - Overtime hours and pay
   - Total labor costs by department
   - Cost per acre breakdown

---

### 🏠 Land & Lease Management

**When to use:** Track landowners, parcels, leases, and rental payments.

#### Adding Landowners

1. Find **"POST /api/v1/land/landowners"**
2. Store contact info:
```json
{
  "name": "Robert Johnson Estate",
  "contact_person": "Mary Johnson",
  "phone": "555-987-6543",
  "email": "mary@email.com",
  "address": "123 Main St, Ruston, LA",
  "notes": "Prefer communication via email"
}
```

#### Recording Land Parcels

1. Find **"POST /api/v1/land/parcels"**
2. Record FSA info, legal description, and acres:
```json
{
  "landowner_id": "LO-0001",
  "parcel_name": "Johnson North 80",
  "fsa_farm_number": "1234",
  "fsa_tract_number": "5678",
  "legal_description": "NW 1/4 Sec 12 T18N R3W",
  "total_acres": 80.5,
  "tillable_acres": 75.2,
  "county": "Lincoln",
  "state": "LA"
}
```

#### Managing Leases

1. Find **"POST /api/v1/land/leases"**
2. Create cash rent or crop share leases:
```json
{
  "parcel_id": "PARCEL-0001",
  "lease_type": "cash_rent",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "annual_rent": 15000.00,
  "payment_frequency": "semi_annual",
  "first_payment_date": "2025-03-01",
  "auto_renew": true,
  "notes": "3% increase annually"
}
```

**Lease Types:** cash_rent, crop_share, flexible_cash, custom

#### Tracking Payments

1. Find **"POST /api/v1/land/lease-payments"**
2. Record each payment
3. View payment history and upcoming due dates
4. Get alerts for leases expiring within 90 days

---

### 💵 Cash Flow Forecasting

**When to use:** Project income and expenses for up to 24 months.

#### Recording Cash Flow Entries

1. Find **"POST /api/v1/cashflow/entries"**
2. Record income or expenses:
```json
{
  "category": "crop_sales",
  "description": "Corn sale - 5000 bu @ $4.50",
  "amount": 22500.00,
  "transaction_date": "2025-09-15",
  "status": "projected",
  "recurring": false
}
```

**Income Categories:** crop_sales, government_payments, custom_work, other_income
**Expense Categories:** seed, fertilizer, chemical, fuel, repairs, labor, land_rent, crop_insurance, interest, utilities, custom_hire, miscellaneous

#### Adding Loans

1. Find **"POST /api/v1/cashflow/loans"**
2. Track operating and equipment loans:
```json
{
  "lender": "Farm Credit",
  "loan_type": "operating",
  "original_amount": 200000.00,
  "current_balance": 175000.00,
  "interest_rate": 7.5,
  "payment_amount": 12500.00,
  "payment_frequency": "monthly",
  "next_payment_date": "2025-04-01",
  "maturity_date": "2025-12-31"
}
```

#### Generating Forecasts

1. Find **"POST /api/v1/cashflow/forecast"**
2. Set parameters:
```json
{
  "months": 12,
  "starting_balance": 50000.00
}
```
3. Get month-by-month projections showing:
   - Expected income
   - Expected expenses
   - Loan payments
   - Ending balance
   - Warning flags for negative balances

---

### 🏢 Multi-Entity Support

**When to use:** Manage multiple farming entities (LLCs, partnerships, etc.)

1. Find **"POST /api/v1/entities"**
2. Create entities:
```json
{
  "name": "Smith Family Farms LLC",
  "entity_type": "llc",
  "tax_id": "12-3456789",
  "state_of_formation": "LA",
  "formation_date": "2020-01-15"
}
```

3. Allocate expenses and income across entities
4. Generate entity-specific reports

---

## 🆕 PRECISION INTELLIGENCE SUITE (NEW in v4.0)

AI-powered precision agriculture tools for data-driven decisions.

### 📊 Yield Prediction Engine

**When to use:** Predict yields before harvest using historical data and weather.

1. Find **"POST /api/v1/precision/yield/predict"**
2. Fill in field data:
```json
{
  "field_id": "FIELD-001",
  "field_name": "North 80",
  "crop": "corn",
  "crop_year": 2025,
  "acres": 80,
  "historical_yields": [185, 192, 178, 195, 188],
  "soil_type": "silt_loam",
  "current_conditions": {
    "gdd_accumulated": 2400,
    "rainfall_inches": 18.5,
    "stress_events": 2
  }
}
```

**What you get:**
- Predicted yield (e.g., 192 bu/acre)
- Confidence interval (185-199 bu/acre)
- Confidence level (high/medium/low)
- Factors affecting prediction
- Recommendations to improve yield

**Prediction Models:**
- `historical_average`: Simple average of past yields
- `trend_analysis`: Linear trend projection
- `weather_adjusted`: Trend with weather adjustments

---

### 🗺️ Management Zone Analytics

**When to use:** Create zones within fields for variable rate applications.

#### Creating Zones

1. Find **"POST /api/v1/precision/zones"**
2. Define each zone:
```json
{
  "field_id": "FIELD-001",
  "zone_name": "High Yield Zone A",
  "zone_type": "high_productivity",
  "acres": 25.5,
  "avg_yield": 210,
  "yield_potential": 220,
  "soil_properties": {
    "om_pct": 3.2,
    "ph": 6.5,
    "cec": 18
  }
}
```

**Zone Types:**
- `high_productivity`: Consistently exceeds yield potential
- `medium_productivity`: Meets average yield expectations
- `low_productivity`: Consistently underperforms
- `variable`: Inconsistent performance
- `problem_area`: Requires investigation

---

### 🌱 Variable Rate Prescriptions

**When to use:** Generate zone-based seeding and fertilizer prescriptions.

#### Seeding Prescription

1. Find **"POST /api/v1/precision/prescriptions/seeding"**
2. Generate prescription:
```json
{
  "field_id": "FIELD-001",
  "crop": "corn",
  "crop_year": 2025,
  "seed_cost_per_unit": 280.00,
  "units_per_bag": 80000
}
```

**What you get:**
- Zone-by-zone seeding rates
- High zones: 34,000+ seeds/acre
- Medium zones: 32,000 seeds/acre
- Low zones: 30,000 seeds/acre
- Total bags needed
- Cost comparison vs. flat rate
- Savings from variable rate

#### Nitrogen Prescription

1. Find **"POST /api/v1/precision/prescriptions/nitrogen"**
2. Generate prescription:
```json
{
  "field_id": "FIELD-001",
  "crop": "corn",
  "crop_year": 2025,
  "target_yield": 200,
  "nitrogen_cost_per_unit": 0.65,
  "units_per_ton": 2000,
  "soil_credits": 40
}
```

**What you get:**
- Zone-by-zone N rates based on yield potential
- Total N needed
- Estimated cost
- Comparison to flat rate application

---

### 🤖 Decision Support AI

**When to use:** Get AI-powered recommendations for planting, spraying, and harvest timing.

#### Planting Recommendations

1. Find **"POST /api/v1/precision/decisions/planting"**
2. Provide conditions:
```json
{
  "field_id": "FIELD-001",
  "field_name": "North 80",
  "crop": "corn",
  "forecast_temps": [58, 62, 65, 68, 70, 72, 74],
  "soil_temp": 52,
  "forecast_precip": [0, 0.2, 0, 0, 0.5, 0, 0]
}
```

**What you get:**
- Recommendation: PLANT NOW / WAIT / CAUTION
- Confidence score
- Risk factors (soil temp, rain forecast)
- Optimal planting window
- Action items

#### Spray Timing Recommendations

1. Find **"POST /api/v1/precision/decisions/spray"**
2. Provide conditions including wind, temps, and pest pressure
3. Get optimal spray windows with risk scores

#### Harvest Recommendations

1. Find **"POST /api/v1/precision/decisions/harvest"**
2. Provide moisture levels and weather forecast
3. Get harvest timing advice balancing moisture, weather, and drying costs

---

## 🆕 GRAIN & STORAGE SUITE (NEW in v4.1)

Complete grain management from harvest to sale.

### 🏗️ Bin Management

**When to use:** Track grain storage bins, capacity, and inventory.

#### Adding a Storage Bin

1. Find **"POST /api/v1/grain/bins"**
2. Configure your bin:
```json
{
  "name": "Bin 1 - Main Yard",
  "bin_type": "round_steel",
  "capacity_bushels": 50000,
  "diameter_feet": 36,
  "height_feet": 32,
  "has_aeration": true,
  "has_dryer": true,
  "dryer_type": "continuous_flow",
  "dryer_capacity_bph": 1500,
  "location": "Main storage yard"
}
```

**Bin Types:** round_steel, flat_storage, concrete, temporary, hopper_bottom
**Dryer Types:** in_bin, continuous_flow, batch, natural_air

#### Loading Grain

1. Find **"POST /api/v1/grain/bins/load"**
2. Record harvest:
```json
{
  "bin_id": "BIN-0001",
  "grain_type": "corn",
  "bushels": 8500,
  "moisture_pct": 18.5,
  "test_weight": 54.2,
  "source_field": "North 80",
  "temperature": 75
}
```

**What you get:**
- Updated inventory with weighted average moisture
- Percent full calculation
- Transaction ID for tracking

#### Unloading/Selling Grain

1. Find **"POST /api/v1/grain/bins/unload"**
2. Record sale:
```json
{
  "bin_id": "BIN-0001",
  "bushels": 5000,
  "destination": "ADM Elevator - Monroe",
  "price_per_bushel": 4.85,
  "ticket_number": "T-12345"
}
```

**What you get:**
- Transaction recorded with total value
- Updated inventory
- Remaining bushels

---

### 💨 Drying Cost Calculator

**When to use:** Calculate costs before deciding to dry or sell wet.

1. Find **"POST /api/v1/grain/drying/calculate"**
2. Input parameters:
```json
{
  "bushels": 10000,
  "initial_moisture": 22.0,
  "target_moisture": 15.0,
  "dryer_type": "continuous_flow",
  "fuel_cost_per_gallon": 3.50,
  "electricity_cost_per_kwh": 0.12
}
```

**What you get:**
- Points to remove (7 points in this example)
- Shrink loss: 1.4% per point = 9.8% = 980 bushels
- Fuel cost estimate
- Electricity cost
- Total drying cost
- Cost per bushel
- **Recommendation:** Dry vs. sell wet comparison

**Shrink Factor:** Industry standard 1.4% shrink per point of moisture removed

---

### 📊 Grain Accounting

**When to use:** Track grain from field to sale with bushel-level accounting.

#### View Transactions

1. Find **"GET /api/v1/grain/transactions"**
2. Filter by grain type, date range
3. See complete history:
   - Harvest In
   - Sales Out
   - Transfers
   - Shrink adjustments
   - Feed use

#### Accounting Summary

1. Find **"GET /api/v1/grain/accounting/summary"**
2. Set crop year
3. Get totals:
   - Bushels harvested
   - Bushels sold
   - Bushels remaining
   - Average sale price
   - Total revenue

---

### 🔔 Basis Price Alerts

**When to use:** Get notified when basis hits your target.

#### Creating an Alert

1. Find **"POST /api/v1/grain/alerts"**
2. Set your target:
```json
{
  "grain_type": "corn",
  "target_basis": -0.25,
  "bushels": 10000,
  "delivery_location": "ADM Monroe",
  "delivery_month": "December 2025",
  "alert_type": "basis_target_hit",
  "notes": "Sell when basis narrows to -25"
}
```

#### Checking Alerts

1. Find **"POST /api/v1/grain/alerts/check"**
2. Input current prices:
```json
{
  "corn": -0.22,
  "soybeans": -0.35
}
```
3. Get list of triggered alerts
4. Take action on favorable basis

---

## 🆕 COMPLETE FARM BUSINESS SUITE (NEW in v4.2)

Comprehensive business management tools.

### 📋 Tax Planning Tools

**When to use:** Track depreciation, plan Section 179, and project tax liability.

#### Adding Depreciable Assets

1. Find **"POST /api/v1/business/tax/assets"**
2. Record equipment purchase:
```json
{
  "name": "John Deere 8R 340 Tractor",
  "asset_type": "machinery",
  "purchase_date": "2025-03-15",
  "purchase_price": 425000.00,
  "salvage_value": 85000.00,
  "depreciation_method": "macrs_gds",
  "section_179_amount": 200000.00,
  "bonus_depreciation_pct": 60,
  "notes": "Trade-in value $85,000"
}
```

**Asset Types:** machinery, equipment, vehicle, building, land_improvement, livestock_breeding, computer, office_equipment

**Depreciation Methods:**
- `straight_line`: Equal annual depreciation
- `macrs_gds`: Modified Accelerated Cost Recovery System (most common)
- `macrs_ads`: Alternative Depreciation System
- `section_179`: Immediate expensing up to $1.16M limit
- `bonus_depreciation`: Additional first-year depreciation

#### Viewing Depreciation Schedules

1. Find **"GET /api/v1/business/tax/assets/{asset_id}/schedule"**
2. Get year-by-year depreciation:
   - Year 1: Section 179 + Bonus + MACRS = $285,000
   - Year 2: MACRS = $28,571
   - Years 3-7: Declining balance
   - Book value each year

#### Section 179 Optimization

1. Find **"POST /api/v1/business/tax/section179/optimize"**
2. Enter net income
3. Get recommendation on optimal Section 179 election
4. Shows tax savings at different election amounts

#### Tax Liability Projection

1. Find **"POST /api/v1/business/tax/projection"**
2. Enter income and expenses:
```json
{
  "tax_year": 2025,
  "entity_type": "schedule_f",
  "gross_income": 850000.00,
  "total_expenses": 680000.00
}
```

**What you get:**
- Net farm income
- Self-employment tax estimate
- Estimated income tax
- Total tax liability
- Effective tax rate

---

### 👨‍👩‍👧‍👦 Succession Planning

**When to use:** Plan your farm's transition to the next generation.

#### Adding Family Members

1. Find **"POST /api/v1/business/succession/family"**
2. Record family involvement:
```json
{
  "name": "Michael Smith",
  "role": "child",
  "birth_date": "1995-06-15",
  "ownership_pct": 15.0,
  "involvement_level": "Full-time operator",
  "skills": ["equipment operation", "crop planning", "marketing"],
  "notes": "Taking over field operations 2026"
}
```

**Family Roles:** owner, operator, spouse, child, grandchild, sibling, in_law, employee, advisor

#### Creating Asset Transfer Plans

1. Find **"POST /api/v1/business/succession/transfers"**
2. Plan the transfer:
```json
{
  "asset_name": "North 160 acres",
  "asset_value": 1200000.00,
  "transfer_method": "installment_sale",
  "from_member_id": "FAM-0001",
  "to_member_id": "FAM-0002",
  "target_date": "2027-01-01",
  "notes": "15-year installment at AFR rate"
}
```

**Transfer Methods:** sale, gift, inheritance, installment_sale, lease_purchase, trust, llc_transfer

#### Succession Milestones

1. Find **"POST /api/v1/business/succession/milestones"**
2. Create milestones:
```json
{
  "title": "Update estate plan with attorney",
  "category": "legal",
  "description": "Review wills, trusts, and POAs",
  "target_date": "2025-06-01",
  "assigned_to": "FAM-0001"
}
```

**Milestone Categories:** legal, financial, operational, training, communication, documentation, tax_planning, insurance

---

### 📈 Benchmarking Dashboard

**When to use:** Compare your performance to regional averages and track year-over-year.

#### Recording Benchmark Data

1. Find **"POST /api/v1/business/benchmarks"**
2. Enter field performance:
```json
{
  "field_id": "FIELD-001",
  "crop": "corn",
  "crop_year": 2024,
  "metrics": {
    "yield_per_acre": 198,
    "cost_per_acre": 485,
    "revenue_per_acre": 891,
    "cost_per_bushel": 2.45
  }
}
```

**Benchmark Metrics:** yield_per_acre, cost_per_acre, revenue_per_acre, net_income_per_acre, cost_per_bushel, return_on_assets, debt_to_asset, working_capital, input_cost_ratio

#### Compare to Regional Benchmarks

1. Find **"GET /api/v1/business/benchmarks/compare/{field_id}/{crop_year}"**
2. Get comparison:
   - Your yield vs. regional average
   - Your costs vs. regional average
   - Performance grade (Above/Below average)
   - Specific areas for improvement

#### Year-Over-Year Comparison

1. Find **"GET /api/v1/business/benchmarks/yoy/{field_id}"**
2. See multi-year trends:
   - Yield trend
   - Cost trend
   - Profitability trend
   - Best/worst years

---

### 📁 Document Vault

**When to use:** Centralize all farm documents with organization and expiration tracking.

#### Adding Documents

1. Find **"POST /api/v1/business/documents"**
2. Upload document info:
```json
{
  "name": "2024 Farm Operating Loan",
  "category": "financial",
  "file_path": "/documents/loans/2024_operating.pdf",
  "file_type": "pdf",
  "document_date": "2024-01-15",
  "year": 2024,
  "tags": ["loan", "farm credit", "operating"],
  "description": "Annual operating loan agreement",
  "expiration_date": "2024-12-31",
  "related_entity": "Smith Family Farms LLC"
}
```

**Document Categories:** tax, legal, insurance, financial, lease, certification, compliance, equipment, contracts, personnel, other

#### Searching Documents

1. Find **"GET /api/v1/business/documents/search"**
2. Search by query (searches name, tags, description)
3. Get matching documents

#### Expiration Alerts

1. Find **"GET /api/v1/business/documents/expiring"**
2. Set days parameter (default 30)
3. Get list of documents expiring soon:
   - Insurance policies
   - Certifications
   - Leases
   - Contracts

---

## 🚜 John Deere Operations Center Integration (Planned for v2.8)

**Note:** This feature is planned for v2.8 as John Deere Developer Account requires a business application/approval process.

If you use John Deere Operations Center, v2.8 will let you:

- **Import your fields automatically** - No more manual boundary entry
- **See actual yield maps** - Historical yield data by zone
- **Track what was applied** - Compare recommendations to actual applications
- **Get zone-specific recommendations** - Variable rate suggestions based on yield history
- **Validate ROI** - See if recommendations actually improved outcomes

**Prerequisites for v2.8:**
1. John Deere Developer Account - https://developer.deere.com (requires business application)
2. API credentials (client_id, client_secret)
3. Your JD Ops Center account with field data

This feature is planned for future development once JD Developer Account approval is obtained.

---

## Getting Help

If something doesn't work:

1. Make sure the system is running (you see the "Uvicorn running" message)
2. Refresh the browser page
3. Check that you filled in all required fields
4. Try the example inputs shown above first

The system has built-in documentation - click on any endpoint to see exactly what it needs.

---

**Start with the Quick Estimate to see where you stand, then dig into the specific areas where you can save the most money.**

