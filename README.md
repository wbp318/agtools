# AgTools - Farm Management Made Simple

**A complete farm management system for crop consulting, pest identification, spray recommendations, financial tracking, and more.**

---

## What is AgTools?

AgTools helps farmers and consultants:
- **Identify pests and diseases** using symptoms or photos
- **Get spray recommendations** with costs and timing
- **Track expenses** and see cost-per-acre
- **Manage fields, equipment, and inventory**
- **Handle farm accounting** (invoices, bills, payroll, checks)
- **Track livestock** and planting records

---

## Getting Started (5 minutes)

### Step 1: Install Python

1. Go to https://python.org/downloads
2. Download Python (click the big yellow button)
3. Run the installer
4. **Important:** Check the box that says "Add Python to PATH"
5. Click Install

### Step 2: Download AgTools

**Option A - If you have Git:**
```
git clone https://github.com/wbp318/agtools.git
```

**Option B - Download ZIP:**
1. Go to https://github.com/wbp318/agtools
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file

### Step 3: Start the Server

Open a command prompt (Windows) or terminal (Mac), then:

```
cd agtools/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

You should see: `Uvicorn running on http://127.0.0.1:8000`

### Step 4: Open AgTools

Open your web browser and go to:
- **API Explorer:** http://localhost:8000/docs
- **Mobile Interface:** http://localhost:8000/m/login

That's it! AgTools is running.

---

## Using the Desktop App (Optional)

For a full desktop experience:

```
cd agtools/frontend
pip install -r requirements.txt
python main.py
```

---

## Features

### Pest & Disease Identification
Upload a photo or describe symptoms to identify problems in your corn or soybean fields. Get treatment recommendations with costs.

### Spray Recommendations
Get product recommendations with:
- Application rates
- Best timing based on weather
- Cost per acre
- Return on investment

### Farm Operations
- **Fields:** Track all your farm fields
- **Tasks:** Assign work to crew members
- **Equipment:** Log hours and maintenance
- **Inventory:** Track chemicals, seed, fuel, parts

### Financial Management (GenFin)
- **Accounts Payable:** Track bills, vendors, payments
- **Accounts Receivable:** Invoices, customers, statements
- **Check Printing:** Print checks directly
- **Payroll:** Employee management and pay runs
- **Reports:** Profit & Loss, Balance Sheet, Cash Flow

### Livestock & Planting
- Track animals (cattle, hogs, poultry, sheep, goats)
- Health records, breeding, weight tracking
- Seed inventory and planting records

---

## Need Help?

- **Quick Setup Guide:** See [QUICKSTART.md](QUICKSTART.md)
- **Technical Details:** See [docs/TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)
- **What's New:** See [CHANGELOG.md](CHANGELOG.md)

---

## License

**This software is proprietary.** It is shared publicly for demonstration and evaluation only.

Commercial use requires a license. Contact information is in the [LICENSE](LICENSE) file.

Copyright 2025 New Generation Farms and William Brooks Parker. All Rights Reserved.
