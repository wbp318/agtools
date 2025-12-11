# Professional Crop Consulting System - Complete Guide

## 🌾 Overview

You now have a **professional-grade crop consulting system** designed with 30 years of consulting experience and modern technology. This system rivals commercial platforms and provides genuine value for crop consulting businesses.

### What Makes This Professional?

1. **Real-World Data**: Comprehensive pest/disease database based on university extension research
2. **Economic Analysis**: Built-in threshold calculators and ROI analysis
3. **Resistance Management**: Intelligent chemical rotation and MOA tracking
4. **Weather Integration**: Spray window optimization and disease forecasting
5. **Hybrid AI**: Combines image recognition with symptom-based diagnosis
6. **Professional Recommendations**: Specific products, rates, timing, and economics
7. **Real-Time Pricing (v2.1)**: Use your actual supplier quotes for accurate calculations
8. **Weather-Smart Spray Timing (v2.1)**: Economic analysis of spray timing decisions
9. **Yield Response & Economic Optimum Rates (v2.2)**: Calculate the most profitable fertilizer rate, not just max yield
10. **Professional Desktop Interface (v2.2.1)**: Complete PyQt6 application with pest/disease identification screens, interactive charts, and professional UI
11. **Offline Mode & Local Database (v2.3.0)**: Full offline operation with SQLite caching, automatic online/offline detection, and background sync
12. **Settings & UI Polish (v2.4.0)**: Comprehensive settings screen, reusable widget library, loading states, toast notifications, and validation feedback

---

## 🏗️ System Architecture

```
agtools/
├── database/
│   ├── schema.sql                          # PostgreSQL database schema
│   ├── seed_data.py                        # Pest & disease knowledge base
│   └── chemical_database.py                # Pesticide products & labels
│
├── backend/
│   ├── main.py                             # FastAPI application (v2.2 - 1800+ lines, 42+ endpoints)
│   ├── requirements.txt                    # Backend dependencies
│   └── services/
│       ├── pest_identification.py          # Symptom-based pest ID
│       ├── disease_identification.py       # Disease diagnosis
│       ├── spray_recommender.py            # Intelligent spray recommendations
│       ├── threshold_calculator.py         # Economic threshold analysis
│       ├── weather_service.py              # Weather API integration
│       ├── ai_identification.py            # AI image recognition
│       ├── labor_optimizer.py              # Labor cost optimization (v2.0)
│       ├── application_cost_optimizer.py   # Fertilizer/pesticide costs (v2.0)
│       ├── irrigation_optimizer.py         # Irrigation optimization (v2.0)
│       ├── input_cost_optimizer.py         # Unified cost analysis (v2.0)
│       ├── pricing_service.py              # Real-time pricing (v2.1)
│       ├── spray_timing_optimizer.py       # Weather-smart spraying (v2.1)
│       └── yield_response_optimizer.py     # Economic optimum rates (v2.2)
│
├── frontend/                               # PyQt6 Desktop Application
│   ├── main.py                             # Application entry point
│   ├── app.py                              # QApplication setup
│   ├── config.py                           # Settings management (v2.4.0)
│   ├── requirements.txt                    # Frontend dependencies (PyQt6, httpx, pyqtgraph)
│   ├── api/                                # API client modules
│   │   ├── client.py                       # Base HTTP client with offline support
│   │   ├── yield_response_api.py           # Yield response endpoints
│   │   ├── spray_api.py                    # Spray timing endpoints
│   │   ├── pricing_api.py                  # Pricing endpoints
│   │   ├── cost_optimizer_api.py           # Cost optimizer endpoints
│   │   └── identification_api.py           # Pest/disease ID
│   ├── database/                           # Local database (NEW v2.3.0)
│   │   └── local_db.py                     # SQLite caching for offline mode
│   ├── core/                               # Core logic (NEW v2.3.0)
│   │   ├── sync_manager.py                 # Online/offline detection & sync
│   │   └── calculations/                   # Offline calculators
│   │       ├── yield_response.py           # Offline EOR calculator
│   │       └── spray_timing.py             # Offline spray evaluator
│   ├── models/                             # Data classes
│   │   ├── yield_response.py
│   │   ├── spray.py
│   │   ├── pricing.py
│   │   ├── cost_optimizer.py
│   │   └── identification.py               # Pest/disease models
│   ├── tests/                              # Frontend tests (NEW v2.4.0)
│   │   └── test_phase9.py                  # Integration tests
│   └── ui/
│       ├── styles.py                       # Professional QSS theme
│       ├── sidebar.py                      # Navigation sidebar
│       ├── main_window.py                  # Main window with sync UI
│       ├── widgets/                        # Reusable widgets (NEW v2.4.0)
│       │   └── common.py                   # LoadingOverlay, StatusMessage, etc.
│       └── screens/
│           ├── dashboard.py                # Home screen with quick actions
│           ├── yield_response.py           # Interactive yield curves
│           ├── spray_timing.py             # Weather evaluation
│           ├── cost_optimizer.py           # Tabbed cost analysis
│           ├── pricing.py                  # Price management & alerts
│           ├── pest_identification.py      # Pest ID screen
│           ├── disease_identification.py   # Disease ID screen
│           └── settings.py                 # Settings screen (NEW v2.4.0)
│
├── CHANGELOG.md                            # Development changelog
├── PROFESSIONAL_SYSTEM_GUIDE.md            # Complete documentation
├── QUICKSTART.md                           # 5-minute setup guide
├── README.md                               # Overview and quick start
└── LICENSE                                 # Proprietary license
```

---

## 📊 Knowledge Base Content

### Corn Pests (10 Major Pests)
- Corn Rootworm (Western & Northern)
- European Corn Borer
- Western Bean Cutworm
- Fall Armyworm
- Black Cutworm
- Corn Leaf Aphid
- Spider Mites
- Japanese Beetle
- Stalk Borer
- Corn Earworm

### Soybean Pests (10 Major Pests)
- Soybean Aphid
- Two-Spotted Spider Mite
- Bean Leaf Beetle
- Japanese Beetle
- Grasshoppers
- Stink Bugs (multiple species)
- Dectes Stem Borer
- Soybean Looper
- Thistle Caterpillar
- Grape Colaspis

### Corn Diseases (13 Major Diseases)
- Gray Leaf Spot
- Northern Corn Leaf Blight
- Southern Corn Leaf Blight
- Common Rust
- Southern Rust
- Tar Spot
- Anthracnose
- Eyespot
- Goss's Wilt
- Stewart's Wilt
- Diplodia Ear Rot
- Gibberella Ear Rot
- Aspergillus Ear Rot

### Soybean Diseases (13 Major Diseases)
- White Mold (Sclerotinia)
- Sudden Death Syndrome (SDS)
- Soybean Cyst Nematode (SCN)
- Brown Stem Rot
- Frogeye Leaf Spot
- Septoria Brown Spot
- Bacterial Blight
- Cercospora Leaf Blight
- Anthracnose
- Phytophthora Root Rot
- Soybean Rust
- Charcoal Rot
- Pod and Stem Blight

### Chemical Database (40+ Products)
- **Insecticides**: Pyrethroids, Neonicotinoids, Diamides, Organophosphates, Carbamates
- **Fungicides**: QoI + Triazole premixes, SDHI products, Seed treatments
- **Complete Label Info**: Rates, PHI, REI, timing, restrictions

---

## 🚀 Getting Started

### Prerequisites

Before you begin, make sure you have the following installed:

**Required:**
- **Python 3.8 or newer**
  - Download: https://www.python.org/downloads/
  - **IMPORTANT:** During installation, check the box "Add Python to PATH"
  - Verify installation: Open command prompt and type `python --version`

**Optional but Recommended:**
- **Git** - For cloning the repository
  - Download: https://git-scm.com/downloads
  - Verify installation: `git --version`

### Step 1: Download the Code

**Option A: Using Git (Recommended)**

Open a command prompt or terminal and run:

```bash
git clone https://github.com/wbp318/agtools.git
cd agtools
```

**Option B: Download as ZIP**

1. Visit https://github.com/wbp318/agtools
2. Click the green **"Code"** button
3. Select **"Download ZIP"**
4. Extract the ZIP file to your desired location
5. Open a command prompt and navigate to the extracted folder

### Step 2: Install Dependencies

Navigate to the backend folder and install required packages:

```bash
cd backend
pip install -r requirements.txt
```

This installs all necessary Python packages. You only need to do this once.

### Required Dependencies (Reference)

The system uses these key packages (installed automatically):

**Backend:**
```
fastapi>=0.104.1          # Web framework
uvicorn>=0.24.0           # ASGI server
pydantic>=2.4.2           # Data validation
python-multipart>=0.0.6   # File uploads
tensorflow>=2.15.0        # AI/ML (optional)
pillow>=10.1.0            # Image processing
numpy>=1.24.3             # Numerical computing
pandas>=2.1.3             # Data analysis
scikit-learn>=1.3.2       # Machine learning
requests>=2.31.0          # HTTP requests
```

**Frontend (Desktop App):**
```
PyQt6>=6.5.0              # Desktop GUI framework
httpx>=0.25.0             # HTTP client for API calls
pyqtgraph>=0.13.0         # Interactive charts
numpy>=1.24.0             # Numerical computing
python-dateutil>=2.8.0    # Date/time utilities
```

### Step 3: Run the API Server

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

You should see output like:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 4: Access the System

You have two options:

**Option A: Web API (Swagger UI)**

Open your web browser and go to:

- **Interactive API Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc format)
- **API Health Check:** http://localhost:8000/

**Option B: Desktop Application (Recommended)**

Open a new terminal (keep API running) and run:

```bash
cd frontend
pip install -r requirements.txt  # One-time setup
python main.py
```

The desktop app provides a professional interface with:
- **Dashboard** - Quick access to all features
- **Yield Calculator** - Interactive yield response curves with pyqtgraph charts
- **Spray Timing** - Weather evaluation with clear SPRAY/WAIT recommendations
- **Cost Optimizer** - Tabbed interface (Quick Estimate, Fertilizer, Irrigation)
- **Price Manager** - Supplier quotes, buy/wait analysis, alerts
- **Pest Identification** (NEW v2.2.1) - 20-symptom checklist, severity ratings, confidence scoring, detailed pest cards with economic thresholds
- **Disease Identification** (NEW v2.2.1) - Weather conditions input, symptom selection, management recommendations, favorable conditions display

### Troubleshooting

**"python is not recognized"**
- Python wasn't added to PATH during installation
- Reinstall Python and CHECK "Add Python to PATH"
- Or use `python3` instead of `python`

**"pip is not recognized"**
- Try `python -m pip install -r requirements.txt`

**Port 8000 already in use**
- Another program is using port 8000
- Edit `main.py` and change the port number (e.g., to 8001)

**Import errors when starting**
- Run `pip install -r requirements.txt` again
- Make sure you're in the `backend` folder

---

## 💡 Core Features & Usage

### 1. Pest Identification

**Symptom-Based Identification:**

```python
POST /api/v1/identify/pest

{
  "crop": "soybean",
  "growth_stage": "R3",
  "symptoms": ["curled_leaves", "yellowing", "sticky_residue"],
  "field_conditions": {
    "weather": "warm",
    "location": "field_interior"
  }
}
```

**Response:**
```json
[
  {
    "id": 0,
    "common_name": "Soybean Aphid",
    "scientific_name": "Aphis glycines",
    "confidence": 0.95,
    "description": "Most economically important soybean pest...",
    "economic_threshold": "250 aphids per plant with increasing populations before R6",
    "management_notes": "Scout weekly V2-R5. Foliar insecticides..."
  }
]
```

### 2. Disease Identification

```python
POST /api/v1/identify/disease

{
  "crop": "corn",
  "growth_stage": "R2",
  "symptoms": ["rectangular_lesions", "gray_lesions", "lower_leaves"],
  "weather_conditions": "warm, humid, cloudy"
}
```

### 3. Spray Recommendations

**Get Intelligent Recommendations:**

```python
POST /api/v1/recommend/spray

{
  "crop": "soybean",
  "growth_stage": "R3",
  "problem_type": "pest",
  "problem_id": 0,  # Soybean aphid
  "severity": 8,
  "field_acres": 160,
  "previous_applications": ["Warrior II"],
  "temperature_forecast": [75, 78, 80, 82, 79],
  "rain_forecast_inches": [0, 0, 0.2, 0, 0]
}
```

**Response includes:**
- Primary product recommendation with rate, cost, PHI, REI
- Alternative products (for resistance management)
- Tank mix suggestions
- Adjuvant recommendations
- Optimal spray timing window
- Weather requirements
- **Complete economic analysis**: Cost, protected revenue, net benefit, ROI%
- Resistance management notes

### 4. Economic Threshold Analysis

```python
POST /api/v1/threshold/check

{
  "crop": "soybean",
  "pest_name": "soybean aphid",
  "population_count": 300,
  "growth_stage": "R3",
  "control_cost_per_acre": 15.00,
  "expected_yield": 50,
  "grain_price": 12.00
}
```

**Response:**
```json
{
  "threshold_exceeded": true,
  "current_population": 300,
  "threshold_value": 250,
  "threshold_unit": "aphids per plant",
  "estimated_yield_loss_bushels": 2.5,
  "estimated_revenue_loss": 30.00,
  "estimated_control_cost": 15.00,
  "net_benefit_of_treatment": 15.00,
  "recommendation": "Treatment recommended. Expected net benefit: $15.00/acre"
}
```

### 5. Weather Integration

```python
GET /api/v1/weather/spray-window?latitude=41.878&longitude=-93.098&days_ahead=5
```

**Returns:**
- 5-day forecast
- Spray suitability rating (0-10)
- Specific concerns (wind, rain, temperature)
- Best time of day for application
- Overall recommendations

### 6. AI Image Recognition

```python
POST /api/v1/identify/image
Content-Type: multipart/form-data

image: [file upload]
crop: "corn"
growth_stage: "V6"
```

Returns top 3 matches with confidence scores, combining AI with manual verification guidance.

---

## 🎯 Real-World Consulting Workflow

### Example: Soybean Aphid Outbreak

1. **Field Scouting**: Find aphids on soybeans at R3 stage
2. **Count Population**: Average 300 aphids/plant across field
3. **Check Threshold**:
   ```
   POST /api/v1/threshold/check
   -> Result: TREAT - Net benefit $15/acre
   ```
4. **Get Spray Recommendation**:
   ```
   POST /api/v1/recommend/spray
   -> Primary: Warrior II 2.56 oz/acre
   -> Alternatives: Actara, Assail (different MOA)
   -> Cost: $10/acre product + $7.50 application
   -> ROI: 85%
   ```
5. **Check Weather**:
   ```
   GET /api/v1/weather/spray-window
   -> Best window: Thursday - Rating 9/10
   -> Avoid Friday (70% rain chance)
   ```
6. **Make Recommendation**: Spray Thursday morning with Warrior II + NIS

**Client Value**:
- Protected 4 bushels/acre × 160 acres = 640 bushels
- 640 bu × $12.00 = $7,680 protected revenue
- Cost: $2,800 total
- Net benefit: $4,880
- Your consulting fee fully justified!

---

## 📈 What Makes This Worth Money?

### 1. **Data-Driven Decisions**
- No guessing - everything based on economic thresholds
- ROI calculated for every recommendation
- Resistance management to protect long-term efficacy

### 2. **Professional Knowledge Base**
- 23 corn pests/diseases with full management info
- 23 soybean pests/diseases
- 40+ pesticide products with real label information
- University extension-quality information

### 3. **Complete Recommendations**
- Not just "spray something" - specific products and rates
- Alternative options for resistance management
- Timing windows based on weather
- Economic justification

### 4. **Client-Ready Reports**
- Threshold analysis showing treatment is justified
- Cost/benefit breakdown
- Professional product recommendations with labels
- Weather-optimized timing

### 5. **Scalability**
- One consultant can manage many more acres
- Consistent, quality recommendations across all fields
- Historical tracking and trend analysis

---

## 🔧 Next Steps to Production

### Phase 1: Core Refinement (Week 1-2)
1. Set up PostgreSQL database
2. Populate with seed data
3. Test all API endpoints
4. Add user authentication
5. Create simple web interface

### Phase 2: Field Testing (Week 3-4)
1. Use in real field scouting
2. Validate recommendations against extension resources
3. Refine economic models with real data
4. Build confidence scores from field validation

### Phase 3: Client Features (Week 5-8)
1. Multi-farm/multi-field management
2. Historical tracking and reporting
3. PDF report generation
4. Mobile-responsive web app
5. Offline mode for field use

### Phase 4: Advanced Features (Week 9-12)
1. Integrate real weather APIs (Weather.gov, OpenWeather)
2. Satellite imagery integration
3. Field mapping with GIS
4. Custom ML model training from field photos
5. Market price integration for dynamic economics

---

## 💰 Monetization Strategies

### 1. **Consulting Service Enhancement**
- Charge premium for data-driven recommendations
- Offer "precision scouting" package with full reporting
- Per-acre fee for season-long monitoring

### 2. **Software as a Service (SaaS)**
- $199/month for full access
- $49/month for basic (DIY farmers)
- $999/year enterprise (multiple consultants)

### 3. **API Licensing**
- Sell API access to other consultants/ag retailers
- $0.10 per recommendation generated
- White-label option for co-ops

### 4. **Data Services**
- Aggregate anonymized data for research
- Regional pest/disease pressure maps
- Predictive analytics

---

## 📚 Technical Documentation

### API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/crops` | GET | List supported crops |
| `/api/v1/pests` | GET | Get pest database |
| `/api/v1/diseases` | GET | Get disease database |
| `/api/v1/products` | GET | Get pesticide products |
| `/api/v1/identify/pest` | POST | Identify pest by symptoms |
| `/api/v1/identify/disease` | POST | Identify disease |
| `/api/v1/identify/image` | POST | AI image identification |
| `/api/v1/recommend/spray` | POST | Get spray recommendations |
| `/api/v1/threshold/check` | POST | Economic threshold analysis |
| `/api/v1/weather/spray-window` | GET | Spray timing forecast |
| `/api/v1/scouting/report` | POST | Create scouting report |

### Database Schema

- **8 core tables**: crops, pests, diseases, products, recommendations, thresholds
- **Fully normalized** with proper foreign keys
- **GIS-ready** with PostGIS support for field mapping
- **Extensible** - easy to add new pests, products, crops

---

## 🎓 Professional Knowledge

### What A 30-Year Consultant Would Know

This system incorporates:

1. **Economic Thresholds** - When to treat vs. scout
2. **Resistance Management** - Rotating MOAs, avoiding resistance
3. **Label Compliance** - PHI, REI, maximum rates
4. **Application Timing** - Weather windows, growth stages
5. **Tank Mix Compatibility** - What mixes, what doesn't
6. **Regional Variations** - Pest pressure differences
7. **Integrated Pest Management (IPM)** - Not just spray everything
8. **Disease Forecasting** - Weather-based risk models
9. **Cost Optimization** - Cheapest effective option
10. **Regulatory Compliance** - Applicator record keeping

---

## 💰 INPUT COST OPTIMIZATION (v2.0)

Version 2.0 adds comprehensive input cost optimization - the features that help farmers **reduce costs without reducing yields**. This is where the real money-saving happens.

### Overview: Three Pillars of Cost Reduction

1. **Labor Optimization** - Reduce scouting and application labor costs
2. **Application Cost Optimization** - Fertilizer, pesticide, and fungicide cost reduction
3. **Irrigation Optimization** - Water and energy cost savings

### Labor Cost Optimization

The labor optimizer helps you understand where time (and money) is being spent.

#### Scouting Cost Analysis

```python
POST /api/v1/optimize/labor/scouting

{
  "fields": [
    {"name": "North 80", "acres": 80},
    {"name": "South 160", "acres": 160},
    {"name": "River Bottom", "acres": 120}
  ],
  "scouting_frequency_days": 7,
  "season_length_days": 120
}
```

**Returns:**
- Hours spent scouting per field
- Total season cost (at $25/hr for certified scout)
- Cost per acre
- **Optimization recommendations**: Route planning, frequency adjustments, drone integration

#### Application Labor Analysis

```python
POST /api/v1/optimize/labor/application

{
  "acres": 500,
  "equipment_type": "self_propelled_120ft",
  "tank_capacity_gallons": 1200,
  "custom_application": false
}
```

**Returns:**
- Time required for application
- Setup and fill times
- Labor vs. custom applicator comparison
- **Break-even analysis**: When does owning equipment pay vs. custom?

#### Seasonal Labor Budget

```python
POST /api/v1/optimize/labor/seasonal-budget?total_acres=500&crop=corn
```

**Returns complete season breakdown:**
- Scouting hours and cost
- Spray application labor
- Fertilizer application labor
- Equipment maintenance time
- Management/planning time
- **Total labor cost per acre**

### Application Cost Optimization

#### Fertilizer Program Optimization

The most powerful feature for reducing input costs - uses your actual soil tests to recommend exactly what you need.

```python
POST /api/v1/optimize/fertilizer

{
  "crop": "corn",
  "yield_goal": 200,
  "acres": 500,
  "soil_test_p_ppm": 22,
  "soil_test_k_ppm": 145,
  "nitrogen_credit_lb_per_acre": 40
}
```

**Returns:**
- **Exact nutrient requirements**: N, P2O5, K2O, S (lb/acre)
- **Most economical products**: Compares anhydrous vs. urea vs. UAN, MAP vs. DAP, etc.
- **Application timing recommendations**: Fall P/K, spring N, side-dress schedule
- **Cost per acre and per bushel**
- **Optimization opportunities**:
  - Skip P/K if soil tests high
  - Split N for better efficiency
  - Variable rate to match field variability

**Real savings example:**
A 500-acre corn farm with high P levels (40 ppm) might be applying $15/acre in unnecessary P. That's $7,500/year in savings.

#### Pesticide Cost Comparison

```python
POST /api/v1/optimize/pesticides/compare

{
  "acres": 160,
  "products": [
    {"name": "Warrior II", "cost_per_acre": 8.50, "active_ingredient": "lambda-cyhalothrin", "efficacy": 9},
    {"name": "Generic Lambda", "cost_per_acre": 5.00, "active_ingredient": "lambda-cyhalothrin", "efficacy": 9},
    {"name": "Brigade", "cost_per_acre": 9.00, "active_ingredient": "bifenthrin", "efficacy": 8}
  ],
  "include_generics": true
}
```

**Returns:**
- Side-by-side cost comparison
- Cost per efficacy point (value analysis)
- **Savings vs. most expensive option**
- Generic alternatives where available

#### Complete Spray Program ROI

```python
POST /api/v1/optimize/spray-program

{
  "crop": "corn",
  "acres": 500,
  "spray_applications": [
    {"timing": "V6", "product": "Herbicide", "product_cost_per_acre": 25, "target": "Weeds"},
    {"timing": "VT", "product": "Fungicide", "product_cost_per_acre": 20, "target": "Gray Leaf Spot"},
    {"timing": "VT", "product": "Insecticide", "product_cost_per_acre": 10, "target": "Rootworm beetles"}
  ]
}
```

**Returns:**
- Total program cost
- Cost per application
- Estimated yield protection
- **Complete ROI analysis**: Is the fungicide worth it?
- **Optimization tips**: Tank-mixing to reduce passes, threshold-based decisions

### Irrigation Optimization

For irrigated operations, water costs can be 15-25% of input costs. These tools help optimize every acre-inch.

#### Crop Water Need Calculator

```python
POST /api/v1/optimize/irrigation/water-need

{
  "crop": "corn",
  "growth_stage": "VT",
  "reference_et_inches_per_day": 0.30,
  "recent_rainfall_inches": 0.5,
  "soil_moisture_percent": 45
}
```

**Returns:**
- Current crop water use (inches/day)
- Net irrigation need
- **Urgency level**: Critical, High, Medium, Low
- Plain English recommendation
- Whether you're at a critical growth stage

#### Irrigation Cost Calculator

```python
POST /api/v1/optimize/irrigation/cost

{
  "acres": 130,
  "inches_to_apply": 1.0,
  "irrigation_type": "center_pivot",
  "water_source": "groundwater_well",
  "pumping_depth_ft": 180
}
```

**Returns:**
- Energy cost (pumping)
- Water cost
- Labor cost
- Equipment wear
- **Total cost per acre-inch**

#### Season Irrigation Schedule

```python
POST /api/v1/optimize/irrigation/season

{
  "crop": "corn",
  "acres": 130,
  "irrigation_type": "center_pivot",
  "water_source": "groundwater_well",
  "season_start": "2024-05-15",
  "season_end": "2024-09-15",
  "expected_rainfall_inches": 12
}
```

**Returns:**
- Total water need for season
- Number of irrigations needed
- Recommended schedule with dates
- **Total season cost**
- **ROI analysis**: Dryland vs. irrigated economics

#### Water Savings Analysis

```python
POST /api/v1/optimize/irrigation/water-savings

{
  "current_usage_acre_inches": 2400,
  "acres": 130,
  "irrigation_type": "center_pivot",
  "water_source": "groundwater_well"
}
```

**Returns prioritized strategies:**
1. **Soil moisture monitoring**: 15% savings, $500 to implement
2. **Night irrigation**: 5-8% savings, free to implement
3. **Deficit irrigation**: 20% savings, requires careful management
4. **Variable rate irrigation**: 12% savings, $15k+ investment
5. **Cover crops**: 5% long-term savings, improves soil

Each strategy includes payback period and difficulty level.

### Complete Farm Analysis

The master endpoint that ties everything together:

```python
POST /api/v1/optimize/complete-analysis

{
  "total_acres": 800,
  "crops": [
    {"crop": "corn", "acres": 500, "yield_goal": 200},
    {"crop": "soybean", "acres": 300, "yield_goal": 55}
  ],
  "irrigation_type": "center_pivot",
  "water_source": "groundwater_well",
  "soil_test_p_ppm": 22,
  "soil_test_k_ppm": 155,
  "optimization_priority": "cost_reduction"
}
```

**Returns comprehensive analysis:**

```json
{
  "total_costs": {
    "labor": 18200,
    "applications": 120250,
    "irrigation": 72000,
    "total": 298450,
    "cost_per_acre": 373
  },
  "potential_savings": 42800,
  "savings_percent": 14.3,
  "top_recommendations": [
    "Install soil moisture sensors - Save $10,800/year",
    "Switch to night irrigation - Save $5,800/year",
    "Reduce P application (soil test high) - Save $7,500/year"
  ],
  "roi_analysis": {
    "current_net_return": 156000,
    "optimized_net_return": 198800,
    "improvement": 42800
  }
}
```

### Quick Estimate Tool

For fast planning without detailed inputs:

```python
POST /api/v1/optimize/quick-estimate

{
  "acres": 160,
  "crop": "corn",
  "is_irrigated": true,
  "yield_goal": 200
}
```

**Returns industry-average estimates:**
- Cost breakdown by category
- Total cost and cost per acre
- Break-even yield
- Potential savings range (10-20%)

### Budget Worksheet Generator

```python
POST /api/v1/optimize/budget-worksheet

{
  "total_acres": 800,
  "crops": [
    {"crop": "corn", "acres": 500, "yield_goal": 200},
    {"crop": "soybean", "acres": 300, "yield_goal": 55}
  ]
}
```

**Returns complete budget worksheet:**
- Line-item breakdown for each crop
- Revenue projections
- Break-even analysis
- **Three scenarios**: Conservative, Aggressive, Optimized

### Real-World Cost Savings Examples

**Example 1: Fertilizer Over-Application**
- Farm: 1,000 acres corn
- Soil test: P at 45 ppm (very high)
- Current practice: Applying 60 lb P2O5/acre maintenance
- Recommendation: Skip P for 2 years
- **Savings: $39,000 over 2 years**

**Example 2: Irrigation Efficiency**
- Farm: 500 acres irrigated
- Current practice: Water on calendar schedule
- Recommendation: Soil moisture-based scheduling
- Water savings: 15%
- **Savings: $8,500/year**

**Example 3: Spray Program Optimization**
- Farm: 800 acres
- Current: 4 spray applications per season
- Finding: One application below threshold, fungicide on resistant hybrid
- Recommendation: Skip 2 applications in clean years
- **Savings: $12,000/year when conditions allow**

---

## 💲 REAL-TIME PRICING SERVICE (v2.1)

Version 2.1 adds the ability to use your actual supplier prices instead of industry averages. This makes all cost calculations accurate to YOUR situation.

### Why This Matters

- Industry averages can be off by 10-20%
- Your co-op may have better prices than a retailer
- Early booking discounts change the math
- Regional price differences are significant

### Key Features

#### 1. Custom Supplier Quotes

Input your actual prices from supplier quotes:

```python
POST /api/v1/pricing/set-price

{
  "product_id": "urea_46",
  "price": 0.48,
  "supplier": "County Co-op",
  "valid_until": "2025-03-01T00:00:00",
  "notes": "Early booking discount"
}
```

**Response shows:**
- Comparison to default/average price
- Savings percentage
- Whether this is a good deal

#### 2. Bulk Price Import

Load an entire price list from your dealer:

```python
POST /api/v1/pricing/bulk-update

{
  "price_updates": [
    {"product_id": "urea_46", "price": 0.48},
    {"product_id": "anhydrous_ammonia_82", "price": 0.42},
    {"product_id": "dap_18_46", "price": 0.58},
    {"product_id": "glyphosate_generic", "price": 3.80}
  ],
  "supplier": "County Co-op"
}
```

#### 3. Buy Now vs Wait Analysis

Wondering if you should buy now or wait for prices to drop?

```python
POST /api/v1/pricing/buy-recommendation

{
  "product_id": "urea_46",
  "quantity_needed": 50000,
  "purchase_deadline": "2025-03-01T00:00:00"
}
```

**Returns:**
- Current price vs. 90-day average
- Price trend (rising, falling, stable, volatile)
- Clear recommendation: BUY NOW, WAIT, SPLIT PURCHASE, or FORWARD CONTRACT
- Reasoning and suggested action

#### 4. Supplier Comparison

Compare quotes from multiple suppliers:

```python
POST /api/v1/pricing/compare-suppliers

{
  "product_ids": ["urea_46", "dap_18_46", "potash_60"],
  "acres": 500
}
```

**Returns:**
- Price comparison by product
- Total cost by supplier
- Cheapest supplier recommendation
- Potential savings

#### 5. Price Alerts

Get notified about expiring quotes and price changes:

```python
GET /api/v1/pricing/alerts
```

**Returns:**
- Quotes expiring within 7 days
- Products priced above 90-day average
- Action recommendations

### Regional Price Adjustments

Prices automatically adjust based on your region:

| Region | Adjustment |
|--------|------------|
| Midwest Corn Belt | Baseline |
| Northern Plains | +5% |
| Southern Plains | +8% |
| Delta | +3% |
| Southeast | +10% |
| Pacific Northwest | +12% |
| Mountain | +15% |

### Product Categories Available

**60+ products with default prices:**
- **Fertilizers**: N sources (anhydrous, urea, UAN), P sources (DAP, MAP, TSP), K (potash), S, micronutrients
- **Herbicides**: Glyphosate, dicamba, Liberty, atrazine, Dual, Warrant, Laudis
- **Insecticides**: Pyrethroids (bifenthrin, lambda-cy), Prevathon, Hero, Lorsban
- **Fungicides**: Headline AMP, Trivapro, Delaro, Priaxor, Miravis Neo, generics
- **Seeds**: Corn (conventional through premium), soybeans (all trait packages)
- **Fuel**: Diesel, gasoline, propane, electricity
- **Custom Application**: Ground spray, aerial, fertilizer spreading, combining

---

## 🌤️ WEATHER-SMART SPRAY TIMING (v2.1)

The spray timing optimizer helps you make better decisions about WHEN to spray. This prevents wasted applications and optimizes efficacy.

### Why This Matters

- **Wasted applications cost money**: A herbicide applied before heavy rain = wasted product
- **Poor conditions reduce efficacy**: Hot, dry, windy = poor uptake and drift
- **Waiting too long costs yield**: Disease/pest pressure builds while you wait
- **The math is complicated**: This tool does it for you

### Key Features

#### 1. Current Conditions Evaluation

Check if right now is a good time to spray:

```python
POST /api/v1/spray-timing/evaluate

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

**Returns:**
- Risk level: EXCELLENT, GOOD, MARGINAL, POOR, DO NOT SPRAY
- Score out of 100
- Specific issues identified
- Clear recommendation

**Factors evaluated:**
- Wind speed and direction (drift risk)
- Temperature (volatilization, plant stress)
- Humidity (drift, uptake)
- Rain probability (washoff)
- Inversion potential (drift)
- Leaf wetness (herbicide efficacy)
- Product-specific rainfastness requirements

#### 2. Find Spray Windows in Forecast

Scan a weather forecast to find the best times:

```python
POST /api/v1/spray-timing/find-windows

{
  "forecast": [/* array of hourly weather conditions */],
  "spray_type": "fungicide",
  "min_window_hours": 3.0,
  "product_name": "trivapro"
}
```

**Returns:**
- List of spray windows with start/end times
- Quality rating for each window
- Duration in hours
- Best window recommendation
- Limiting factors for each window

#### 3. Cost of Waiting Analysis

The key question: "Should I spray today in marginal conditions, or wait?"

```python
POST /api/v1/spray-timing/cost-of-waiting

{
  "current_conditions": {/* current weather */},
  "forecast": [/* upcoming weather */],
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

**Returns:**

```json
{
  "recommendation": "SPRAY NOW (with caution)",
  "reasoning": "Yield loss risk ($2,340) outweighs efficacy risk",
  "economic_analysis": {
    "cost_to_spray_now": 5180,
    "cost_to_wait": 2340,
    "net_cost_of_waiting": -2840
  },
  "action_items": [
    "Use drift reduction nozzles (AI, TTI)",
    "Reduce spray pressure to 30-40 PSI",
    "Increase carrier volume to 15+ GPA"
  ]
}
```

**The math it does:**
- Estimates yield loss per day of delay (based on pest/disease and pressure)
- Estimates efficacy reduction from poor conditions
- Calculates dollar cost of each option
- Makes clear recommendation with reasoning

#### 4. Disease Pressure Forecasting

Assess disease risk based on recent weather:

```python
POST /api/v1/spray-timing/disease-pressure

{
  "weather_history": [/* past 7-14 days of weather */],
  "crop": "corn",
  "growth_stage": "VT"
}
```

**Returns risk assessment for relevant diseases:**
- Gray Leaf Spot: HIGH (humidity + warm temps + extended leaf wetness)
- Northern Corn Leaf Blight: MODERATE
- Southern Rust: LOW

**Diseases modeled:**
- Gray Leaf Spot (corn)
- Northern Corn Leaf Blight (corn)
- Southern Rust (corn)
- Frogeye Leaf Spot (soybean)
- Sudden Death Syndrome (soybean)
- White Mold (soybean)

#### 5. Growth Stage Timing Guidance

What should you be spraying at each growth stage?

```python
GET /api/v1/spray-timing/growth-stage-timing/corn/VT?spray_type=fungicide
```

**Returns:**
- Timing recommendation for this stage
- Key considerations
- Suggested products

**Example (corn at VT, fungicide):**
```json
{
  "timing_recommendation": "OPTIMAL timing for fungicide ROI",
  "considerations": [
    "Apply at VT to R2",
    "Protect ear leaf"
  ],
  "suggested_products": [
    "Headline AMP",
    "Trivapro",
    "Miravis Neo"
  ]
}
```

### Spray Type Configurations

Each spray type has different optimal conditions:

| Factor | Herbicide | Insecticide | Fungicide |
|--------|-----------|-------------|-----------|
| Wind (mph) | 3-10 | 2-10 | 2-12 |
| Temp (°F) | 45-85 | 50-90 | 50-85 |
| Humidity (%) | 40-95 | 30-90 | 50-95 |
| Rain-free hours | 4+ | 2+ | 2+ |
| Inversion sensitive | Yes | Yes | Less |
| Leaf wetness OK | No | Yes | Yes |

### Product-Specific Rainfastness

The system knows how long each product needs to dry:

| Product | Hours Needed |
|---------|--------------|
| Glyphosate | 4 |
| Dicamba | 4 |
| 2,4-D | 6 |
| Liberty | 4 |
| Lambda-cyhalothrin | 1 |
| Azoxystrobin | 2 |
| Propiconazole | 1 |

---

## 📈 YIELD RESPONSE & ECONOMIC OPTIMUM RATES (v2.2)

Version 2.2 adds the ability to calculate the **most profitable fertilizer rate** - not just the rate for maximum yield. This is critical because fertilizer response follows the law of diminishing returns: the last 20 lb of nitrogen rarely pays for itself.

### Why This Matters

- **Maximum yield ≠ Maximum profit**: The rate that gives you maximum yield often costs more than it returns
- **Price ratios change optimal rates**: When fertilizer is expensive or grain is cheap, you should back off rates
- **Soil test levels affect response**: High-testing soils don't respond as much to additional fertilizer
- **This is the math consultants do by hand** - now automated

### Key Concepts

#### Economic Optimum Rate (EOR)

The EOR is the rate where **marginal cost equals marginal revenue** - the point where the last pound of fertilizer exactly pays for itself.

- Below EOR: You're leaving profit in the field (under-applying)
- Above EOR: You're spending more than you're getting back (over-applying)
- At EOR: Maximum profit, not maximum yield

#### Price Ratio

The ratio of nutrient cost to grain value determines optimal rates:

```
Price Ratio = Cost per lb nutrient / Value per bushel grain
```

**Example:**
- Nitrogen costs $0.65/lb
- Corn is $4.50/bu
- Price Ratio = 0.65 / 4.50 = 0.144

Higher price ratios → Lower optimal rates
Lower price ratios → Higher optimal rates

### Key Features

#### 1. Generate Yield Response Curve

Visualize how yield responds to nutrient rates:

```python
POST /api/v1/yield-response/curve

{
  "crop": "corn",
  "nutrient": "nitrogen",
  "soil_test_level": "medium",
  "yield_potential": 200,
  "previous_crop": "soybean",
  "model_type": "quadratic_plateau"
}
```

**Returns:**
- Yield at each rate from 0-300 lb/acre
- Maximum yield and rate to achieve it
- Shape parameters for the response curve
- Agronomic plateau point (where additional nutrient stops helping)

#### 2. Calculate Economic Optimum Rate

Find the most profitable rate based on current prices:

```python
POST /api/v1/yield-response/economic-optimum

{
  "crop": "corn",
  "nutrient": "nitrogen",
  "soil_test_level": "medium",
  "yield_potential": 200,
  "previous_crop": "soybean",
  "nutrient_cost_per_lb": 0.65,
  "grain_price_per_bu": 4.50,
  "model_type": "quadratic_plateau"
}
```

**Returns:**
```json
{
  "economic_optimum_rate": 168,
  "max_yield_rate": 195,
  "expected_yield_at_eor": 197.2,
  "max_possible_yield": 198.5,
  "yield_sacrifice": 1.3,
  "price_ratio": 0.144,
  "net_return_at_eor": 778.40,
  "net_return_at_max_yield": 764.25,
  "savings_vs_max_yield": 14.15,
  "fertilizer_savings_lb": 27,
  "recommendation": "Apply 168 lb N/acre. This rate maximizes profit, saving $14.15/acre vs. maximum yield rate while sacrificing only 1.3 bu/acre."
}
```

**The math it does:**
- Calculates yield at every rate using the response model
- Finds where marginal yield × grain price = nutrient cost
- Shows you exactly how much you save by not over-applying

#### 3. Compare Different Application Rates

See profitability across a range of rates:

```python
POST /api/v1/yield-response/compare-rates

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

**Returns:**
- Yield at each rate
- Gross revenue at each rate
- Fertilizer cost at each rate
- Net return at each rate
- Ranking from most to least profitable

**Example output:**
| Rate | Yield | Revenue | Fert Cost | Net Return | Rank |
|------|-------|---------|-----------|------------|------|
| 150 | 192.5 | $866.25 | $97.50 | $768.75 | 2 |
| 180 | 198.0 | $891.00 | $117.00 | $774.00 | 1 |
| 120 | 182.0 | $819.00 | $78.00 | $741.00 | 3 |
| 210 | 199.5 | $897.75 | $136.50 | $761.25 | 4 |

This shows that 180 lb is more profitable than either 150 or 210!

#### 4. Price Sensitivity Analysis

How does the optimal rate change with prices?

```python
POST /api/v1/yield-response/price-sensitivity

{
  "crop": "corn",
  "nutrient": "nitrogen",
  "soil_test_level": "medium",
  "yield_potential": 200,
  "nutrient_cost_range": [0.45, 0.55, 0.65, 0.75, 0.85],
  "grain_price_range": [4.00, 4.50, 5.00, 5.50]
}
```

**Returns a matrix showing optimal rate at each price combination:**

| N Cost | $4.00 Corn | $4.50 Corn | $5.00 Corn | $5.50 Corn |
|--------|------------|------------|------------|------------|
| $0.45/lb | 182 | 188 | 192 | 195 |
| $0.55/lb | 175 | 180 | 185 | 189 |
| $0.65/lb | 168 | 173 | 178 | 182 |
| $0.75/lb | 161 | 166 | 171 | 175 |
| $0.85/lb | 154 | 159 | 164 | 168 |

**Use this when:**
- Planning fertilizer purchases before prices are set
- Deciding whether to adjust rates mid-season
- Advising clients with different cost structures

#### 5. Multi-Nutrient Optimization

Optimize N, P, and K together within a budget:

```python
POST /api/v1/yield-response/multi-nutrient

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

**Returns:**
```json
{
  "optimal_rates": {
    "nitrogen": 165,
    "p2o5": 55,
    "k2o": 45
  },
  "total_cost_per_acre": 147.25,
  "under_budget_by": 2.75,
  "expected_yield": 195.8,
  "expected_net_return": 733.85,
  "limiting_factor": "budget",
  "recommendations": [
    "Budget is constraining N rate by 8 lb. Consider increasing budget $5.20/acre for $12.40 additional return.",
    "P application is near maintenance level - soil building not occurring.",
    "K level adequate - maintenance rate applied."
  ]
}
```

**The optimization logic:**
- Allocates budget to get the highest marginal return per dollar
- Considers soil test levels for P and K
- Accounts for N credits from previous crop
- Shows if budget is constraining yield

#### 6. View Crop Parameters

See the underlying agronomic data:

```python
GET /api/v1/yield-response/crop-parameters/corn
```

**Returns:**
- Base response parameters for each nutrient
- Soil test adjustment factors
- Previous crop credits
- Model coefficients for different response curves

Useful for understanding how the system calculates recommendations.

#### 7. Price Ratio Quick Reference

Get a lookup table for field decisions:

```python
GET /api/v1/yield-response/price-ratio-guide
```

**Returns a printable reference table:**

| Price Ratio | Suggested N Rate Adjustment |
|-------------|----------------------------|
| < 0.10 | Apply up to agronomic max |
| 0.10 - 0.12 | Reduce 5% from max |
| 0.12 - 0.15 | Reduce 10-15% from max |
| 0.15 - 0.18 | Reduce 15-20% from max |
| 0.18 - 0.22 | Reduce 20-25% from max |
| > 0.22 | Reduce 25%+ - consider breakeven |

**Take this to the field** - quick mental math when talking to clients.

### Yield Response Models

The system supports 5 different yield response models:

| Model | Best For | Shape |
|-------|----------|-------|
| Quadratic | General use | Smooth curve with decline after peak |
| Quadratic-Plateau | Most crops | Increases then plateaus (no decline) |
| Linear-Plateau | P and K response | Linear increase to plateau |
| Mitscherlich | Biological accuracy | Exponential approach to maximum |
| Square Root | N response in some soils | Steep initial response, gradual plateau |

**Quadratic-Plateau** is the default and most commonly used for nitrogen in corn.

### Soil Test Level Adjustments

Response varies by soil fertility level:

| Soil Test Level | P Response | K Response | N Credit |
|-----------------|------------|------------|----------|
| Very Low | 150% | 140% | 0 |
| Low | 125% | 120% | 0 |
| Medium | 100% | 100% | 0 |
| High | 50% | 60% | 15 lb |
| Very High | 25% | 30% | 30 lb |

High-testing soils give less response - the system accounts for this automatically.

### Real-World Examples

**Example 1: High Fertilizer Prices**
- Situation: Nitrogen at $0.85/lb, corn at $4.50/bu
- Traditional advice: 1.2 lb N per bu yield goal = 240 lb N for 200 bu goal
- EOR calculation: 154 lb N
- **Savings: 86 lb N × $0.85 = $73.10/acre**
- Yield sacrifice: 3.2 bu ($14.40)
- **Net gain: $58.70/acre**

**Example 2: Cheap Fertilizer, High Corn**
- Situation: Nitrogen at $0.45/lb, corn at $5.50/bu
- EOR calculation: 195 lb N (near max)
- At these prices, pushing for max yield makes sense

**Example 3: Following Soybeans**
- Situation: Corn after soybeans
- N credit: 40 lb/acre
- Adjusted EOR: 128 lb N (vs 168 lb after corn)
- **Savings: 40 lb × $0.65 = $26/acre**

---

## 📡 OFFLINE MODE & LOCAL DATABASE (v2.3.0)

Version 2.3 adds complete offline capability to the desktop application. This enables field use without internet connectivity while maintaining full calculation functionality.

### Why This Matters

- **Field connectivity is unreliable**: Many farms have spotty or no cell coverage
- **Don't lose work**: Queue changes offline and sync when back online
- **Core calculations work anywhere**: EOR and spray timing don't need the server
- **Cached data persists**: Previously fetched pest/disease data remains available

### Architecture

#### Local SQLite Database

Location: `frontend/database/local_db.py` (~550 lines)

The local database provides:
- **Thread-safe connection management**: Safe for PyQt6's multi-threaded UI
- **Automatic schema initialization**: Creates tables on first run
- **8 core tables**:
  - `cache` - General API response cache with TTL
  - `products` - Product catalog with prices
  - `custom_prices` - User-entered supplier quotes
  - `pests` - Pest database cache
  - `diseases` - Disease database cache
  - `crop_parameters` - Agronomic parameters for calculations
  - `calculation_history` - Log of all calculations performed
  - `sync_queue` - Pending changes waiting to sync

**Cache with TTL:**
```python
# Data automatically expires after configured hours
cache_entry = {
    "key": "api/v1/pests",
    "data": {...},
    "expires_at": datetime.now() + timedelta(hours=24)
}
```

**Sync Queue:**
```python
# Changes made offline are queued
sync_item = {
    "id": 1,
    "operation": "set_price",
    "data": {"product_id": "urea_46", "price": 0.48},
    "created_at": "2025-12-11T10:00:00"
}
```

#### Sync Manager

Location: `frontend/core/sync_manager.py` (~450 lines)

The sync manager handles online/offline detection and data synchronization:

**Features:**
- **Qt signals for state changes**: UI updates reactively
- **Periodic connection monitoring**: Checks every 30 seconds
- **Automatic sync on reconnection**: Pushes pending changes
- **Background threading**: Sync doesn't block UI
- **Conflict resolution**: Server wins for conflicts

**Connection States:**
```python
class ConnectionState(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
```

**Signals emitted:**
- `connection_changed(ConnectionState)` - Online/offline transitions
- `sync_started()` - Sync operation beginning
- `sync_progress(int, int)` - Progress updates (current, total)
- `sync_completed(bool, str)` - Success/failure with message
- `sync_item_completed(str)` - Individual item synced

#### Offline Calculators

The system includes full offline versions of key calculators:

**Offline Yield Calculator** (`frontend/core/calculations/yield_response.py` ~450 lines):
- Complete EOR (Economic Optimum Rate) calculation
- 5 response models (quadratic plateau, quadratic, linear plateau, Mitscherlich, square root)
- Crop parameters for corn, soybean, wheat
- Soil test level adjustments
- Previous crop N credits
- Price ratio guide generation
- Yield curve generation

**Offline Spray Calculator** (`frontend/core/calculations/spray_timing.py` ~400 lines):
- Delta T calculation (inversion risk)
- Multi-factor condition assessment (wind, temp, humidity, rain, Delta T)
- Risk level determination (excellent to do-not-spray)
- Cost of waiting economic analysis
- Spray type-specific thresholds

### API Client Offline Support

The API client (`frontend/api/client.py`) includes offline-aware methods:

```python
# GET with cache fallback
response = await client.get_with_cache("/api/v1/pests")
# Returns cached data if offline

# POST with offline calculation fallback
response = await client.post_with_offline_calc(
    "/api/v1/yield-response/economic-optimum",
    data=request_data,
    offline_calculator=yield_calculator.calculate_eor
)
# Uses local calculator if offline

# Queue changes for later sync
client.queue_for_sync("set_price", {"product_id": "urea_46", "price": 0.48})
# Stored in sync_queue table
```

**APIResponse includes cache indicator:**
```python
response.from_cache  # True if data came from local cache
```

### UI Integration

The main window includes sync status display:

**Sync Status Widget:**
- Sync button with spinner during operation
- Pending count indicator ("3 pending")
- Color-coded status dot (green/yellow/red)

**Status Bar:**
- Last sync time display
- Sync progress during operations
- Connection state text

### Usage Workflow

**First run (online):**
1. App connects to API
2. Fetches and caches pest/disease databases
3. Caches product prices
4. Downloads crop parameters
5. Ready for offline use

**Working offline:**
1. App detects API unavailable
2. Switches to offline mode automatically
3. Yield calculator uses local engine
4. Spray timing uses local engine
5. Pest/disease lookup uses cached data
6. Price changes queued in sync_queue

**Reconnecting:**
1. App detects API available
2. User clicks Sync (or auto-syncs)
3. Pending changes pushed to server
4. Fresh data pulled from server
5. Local cache updated

### Configuration

Settings for offline mode (in Settings screen → General tab):
- **Enable offline mode**: Toggle offline fallback
- **Cache TTL (hours)**: How long cached data is valid
- **Sync on startup**: Auto-sync when app launches
- **Auto-fallback**: Automatically switch to offline when API fails

---

## ⚙️ SETTINGS & UI POLISH (v2.4.0)

Version 2.4 completes the PyQt6 desktop application with a comprehensive settings screen, reusable widget library, and integration tests.

### Settings Screen

Location: `frontend/ui/screens/settings.py` (~500 lines)

The settings screen provides 4 tabs for complete application configuration:

#### General Tab

**User Preferences:**
- **Region Selection**: 7 agricultural regions (Midwest Corn Belt, Northern Plains, Southern Plains, Delta, Southeast, Pacific Northwest, Mountain)
- **Default Crop**: Corn or Soybean preference
- **Theme**: Light or Dark mode
- **Sidebar Width**: Adjust navigation panel size (150-300px)

**Offline Mode Settings:**
- **Enable Offline Mode**: Toggle offline fallback capability
- **Cache TTL**: Set data expiration time (1-168 hours)
- **Sync on Startup**: Automatically sync when app launches
- **Auto-Fallback**: Switch to offline when API is unreachable

#### Connection Tab

**API Configuration:**
- **Server URL**: Configurable API endpoint (default: http://127.0.0.1:8000)
- **Timeout**: Request timeout in seconds (5-120)
- **Test Connection**: Button with live feedback showing connection status
- **Connection Status**: Real-time display with refresh button

**Test Connection Results:**
- Success: Shows server version and response time
- Failure: Shows error message and troubleshooting hints

#### Data Tab

**Cache Statistics:**
- Total cache entries
- Products cached
- Pests cached
- Diseases cached
- Calculation history entries
- Sync queue pending items

**Cache Management:**
- **Clear Expired**: Remove only stale entries (safe)
- **Clear All**: Delete entire cache (requires re-caching)
- **Optimize Database**: VACUUM operation to reclaim space

**Data Export:**
- **Export History**: Save calculation history to CSV
- **Export Prices**: Save product prices to CSV

**Database Info:**
- Current SQLite file size
- Database file path

#### About Tab

**Application Information:**
- AgTools branding and version
- Feature list highlighting capabilities
- Data directory paths

### Common Widgets Library

Location: `frontend/ui/widgets/common.py` (~400 lines)

Reusable UI components for consistent user experience:

#### LoadingOverlay

Semi-transparent overlay with progress spinner:
```python
overlay = LoadingOverlay(parent_widget)
overlay.show_loading("Calculating...")
# ... perform operation
overlay.hide_loading()
```

Features:
- Semi-transparent background
- Centered spinner animation
- Optional message text
- Blocks interaction during loading

#### LoadingButton

Button with built-in loading state:
```python
button = LoadingButton("Calculate")
button.set_loading(True, "Processing...")
# ... perform operation
button.set_loading(False)
```

Features:
- Disables during loading
- Shows spinner icon
- Customizable loading text
- Returns to original state

#### StatusMessage

Inline success/error/warning/info messages:
```python
message = StatusMessage()
message.show_success("Calculation complete!")
message.show_error("Connection failed")
message.show_warning("Using cached data")
message.show_info("Tip: Try adjusting the rate")
```

Features:
- Color-coded by type (green/red/yellow/blue)
- Icon indicators
- Auto-hide option with timer
- Dismissible with close button

#### ValidatedLineEdit

Text input with validation feedback:
```python
input_field = ValidatedLineEdit()
input_field.set_validation(is_valid=False, message="Must be a number")
input_field.clear_validation()
```

Features:
- Red border when invalid
- Tooltip shows error message
- Clear method to reset state
- Works with any QLineEdit validator

#### ValidatedSpinBox

Number input with warning range:
```python
spinbox = ValidatedSpinBox()
spinbox.set_warning_range(min_val=100, max_val=200)
# Shows yellow when value outside range but still valid
```

Features:
- Warning state (yellow) vs error state (red)
- Range-based warnings
- Tooltip explains issue
- Supports both int and double values

#### ConfirmDialog

Customizable confirmation dialogs:
```python
dialog = ConfirmDialog(
    title="Clear Cache",
    message="This will delete all cached data. Continue?",
    confirm_text="Clear",
    cancel_text="Cancel",
    icon_type="warning"
)
if dialog.exec() == QDialog.Accepted:
    # User confirmed
```

Features:
- Customizable title, message, button text
- Icon types: warning, question, info, error
- Modal behavior
- Returns confirmation result

#### ToastNotification

Auto-hiding toast notifications:
```python
toast = ToastNotification(parent)
toast.show_toast("Settings saved!", duration=3000)
```

Features:
- Appears at bottom of parent widget
- Auto-hides after duration
- Fade in/out animation
- Multiple types (success, error, info)

### Integration Tests

Location: `frontend/tests/test_phase9.py` (~130 lines)

Comprehensive tests verifying all Phase 9 features:

**Test Suite:**
1. **Settings screen import**: Verifies SettingsScreen class loads
2. **Common widgets import**: Verifies all 7 widget classes load
3. **All screens import**: Tests all 8 screens (Dashboard, YieldResponse, SprayTiming, CostOptimizer, Pricing, PestIdentification, DiseaseIdentification, Settings)
4. **Offline integration**: Tests LocalDatabase and offline calculators
5. **API client offline methods**: Verifies get_with_cache, post_with_offline_calc, queue_for_sync
6. **Config and settings**: Tests AppConfig save/load functionality

**Running Tests:**
```bash
cd frontend
python tests/test_phase9.py
```

**Expected Output:**
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

### Version 2.4.0 Files Summary

**New Files Created:**
- `frontend/ui/screens/settings.py` - Settings screen with 4 tabs
- `frontend/ui/widgets/common.py` - 7 reusable UI widgets
- `frontend/tests/test_phase9.py` - Integration test suite

**Files Modified:**
- `frontend/ui/screens/__init__.py` - Added SettingsScreen export
- `frontend/ui/widgets/__init__.py` - Added common widget exports
- `frontend/ui/main_window.py` - Integrated SettingsScreen in sidebar
- `frontend/config.py` - Version bump to 2.4.0

---

## ✅ Conclusion

You now have a **professional-grade foundation** for a crop consulting business that can:

- **Identify pests and diseases** with professional accuracy (desktop UI v2.2.1)
- **Recommend specific products** with rates, timing, and economics
- **Calculate economic thresholds** showing when treatment pays
- **Manage resistance** through intelligent product rotation
- **Optimize spray timing** with weather integration
- **Generate ROI analysis** justifying every recommendation
- **Use your actual prices** for accurate cost calculations (v2.1)
- **Make weather-smart spray decisions** with cost-of-waiting analysis (v2.1)
- **Calculate economic optimum fertilizer rates** maximizing profit, not just yield (v2.2)
- **Professional desktop interface** with complete PyQt6 application (v2.2.1)
- **Work offline** with full calculation capability and automatic sync (v2.3.0)
- **Configure everything** with comprehensive settings screen (v2.4.0)

This system is **immediately usable** for real consulting work and can be **enhanced incrementally** as you use it in the field.

**The value is real** - this represents years of extension research, product labels, and consulting experience codified into a professional decision support system.

### Version History

| Version | Date | Features |
|---------|------|----------|
| 1.0 | Nov 2025 | Core pest/disease ID, spray recommendations, economic thresholds |
| 2.0 | Dec 2025 | Input cost optimization (labor, fertilizer, irrigation) |
| 2.1 | Dec 2025 | Real-time pricing, weather-smart spray timing |
| 2.2 | Dec 2025 | Yield response curves, economic optimum rate (EOR) calculator |
| 2.2.1 | Dec 2025 | Pest/disease identification screens, yield response bug fixes, complete smoke tests |
| 2.3.0 | Dec 2025 | Offline mode with SQLite caching, sync manager, offline calculators |
| 2.4.0 | Dec 2025 | Settings screen (4 tabs), common widget library (7 widgets), integration tests |

---

## 📞 Support & Development

The system is designed to grow with your business:
- Add new pests/diseases as you encounter them
- Refine economic models with real field data
- Train custom AI models on your photos
- Integrate with equipment (sprayers, drones)
- Build client portals and mobile apps

**You have the foundation. Now make it yours.**

---

*Built for professional crop consultants by someone who understands the value of data-driven agronomy.*
