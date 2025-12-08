# Quick Start Guide - AgTools Professional Crop Consulting System

## For Farmers: Plain English Guide

This guide explains how to use AgTools to **lower your input costs** and **make better decisions** about fertilizer, pesticides, irrigation, and labor. No computer science degree needed - just follow along.

---

## What This System Does (In Plain English)

Think of AgTools as your **digital agronomist** that:

1. **Identifies Bugs & Diseases** - Tell it what you see, it tells you what it is
2. **Recommends Treatments** - Tells you WHAT to spray, HOW MUCH, and WHETHER it's worth the money
3. **Optimizes Your Costs** - Helps you figure out where you're spending too much on:
   - Labor (scouting, spraying, etc.)
   - Fertilizer (are you putting on too much?)
   - Pesticides (is there a cheaper product that works just as well?)
   - Irrigation (are you pumping more water than you need?)

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

### Step 4: Start the System

Every time you want to use AgTools, navigate to the backend folder and type:

```bash
python main.py
```

You'll see a message that says the system is running. Leave this window open.

### Step 5: Open the Tool in Your Browser

Open your web browser (Chrome, Edge, Firefox) and go to:

**http://localhost:8000/docs**

This opens the interactive tool where you can click buttons and fill in forms.

---

## How to Use Each Feature

### 🐛 Identifying a Pest

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

## The Bottom Line

**This system helps you answer the questions that cost you money:**

1. What is this pest/disease?
2. Should I spray or wait?
3. What product should I use?
4. Am I spending too much on fertilizer?
5. Am I over-irrigating?
6. Where are my biggest opportunities to save money?

**Every dollar saved on inputs goes straight to your bottom line.**

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

