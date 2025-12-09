# AgTools: Professional Crop Consulting System

---

## ⚠️ PROPRIETARY SOFTWARE - DEMONSTRATION ONLY

**This software is NOT open source and NOT free to use.**

This repository is publicly viewable for **demonstration and evaluation purposes only**. All code, algorithms, knowledge bases, and intellectual property are proprietary and confidential.

### 🚫 PROHIBITED Without Commercial License:
- ❌ Commercial use of any kind
- ❌ Running as a service (SaaS)
- ❌ Copying, modifying, or distributing the code
- ❌ Creating derivative works
- ❌ Using for consulting services

### ✅ INTERESTED IN USING THIS SYSTEM?

We offer commercial licensing options:
- **SaaS Subscriptions** - For consultants and farmers
- **White-Label Licensing** - For ag retailers and co-ops
- **API Access** - For third-party integration
- **Custom Development** - Tailored to your business

**Contact:** See [LICENSE](LICENSE) for full terms and contact information.

**Copyright © 2024 New Generation Farms. All Rights Reserved.**

---

## 🌾 Overview

**AgTools** is a professional-grade crop consulting platform designed with 30 years of field experience and modern AI technology. This system provides data-driven pest/disease identification, intelligent spray recommendations, economic threshold analysis, **input cost optimization**, and complete decision support for corn and soybean production.

**Version 2.2** adds **Yield Response & Economic Optimum Rate (EOR) Calculator** - calculate the most profitable fertilizer rates based on yield response curves and real-time prices. Stop leaving money in the field by over-applying or sacrificing yield by under-applying.

**This is not a hobby project** - it's a professional tool that provides genuine consulting value.

## ⚡ Quick Start

> **⚠️ FOR EVALUATION ONLY:** These instructions are for authorized evaluation purposes. Commercial use requires a license. See LICENSE file.

### Prerequisites

You need these installed on your computer:

- **Python 3.8+** - Download from https://www.python.org/downloads/
  - During installation, CHECK "Add Python to PATH"
- **Git** (optional) - Download from https://git-scm.com/downloads

### Installation

**Option 1: Clone with Git (Recommended)**
```bash
git clone https://github.com/wbp318/agtools.git
cd agtools
```

**Option 2: Download ZIP**
1. Go to https://github.com/wbp318/agtools
2. Click green "Code" button → "Download ZIP"
3. Extract and open the folder

### Run the System

```bash
# Install dependencies (one time)
cd backend
pip install -r requirements.txt

# Start the API server
python main.py

# Visit http://localhost:8000/docs for interactive API
```

See **[QUICKSTART.md](QUICKSTART.md)** for detailed farmer-friendly setup guide with screenshots.

## 🎯 What This System Does

### Core Capabilities

1. **Pest & Disease Identification**
   - Hybrid approach: AI image recognition + symptom-based diagnosis
   - 23 corn pests/diseases + 23 soybean pests/diseases
   - Confidence scoring and multiple match suggestions
   - Based on university extension research

2. **Intelligent Spray Recommendations**
   - Specific product recommendations with rates and timing
   - 40+ real pesticide products with label information
   - Economic analysis: cost, ROI, net benefit
   - Resistance management with MOA rotation
   - Weather-optimized application windows

3. **Economic Threshold Analysis**
   - Determines if treatment is economically justified
   - Calculates yield protection vs. control costs
   - Real-time ROI analysis
   - Grain price integration

4. **Weather Integration**
   - 5-day spray window forecast
   - Temperature, wind, rain, humidity analysis
   - Optimal application timing recommendations
   - Disease pressure modeling (GDD tracking)

5. **Professional Reporting**
   - Client-ready scouting reports
   - Economic justification for treatments
   - Resistance management documentation
   - Historical tracking

6. **Input Cost Optimization (v2.0)**
   - **Labor Cost Analysis**: Scouting routes, application labor, seasonal budgeting
   - **Fertilizer Optimization**: Soil test-based recommendations, economical nutrient sources
   - **Pesticide Cost Comparison**: Product comparison, generic alternatives, spray program ROI
   - **Irrigation Optimization**: Water need calculations, scheduling, system comparison
   - **Complete Farm Analysis**: Unified cost analysis with prioritized savings opportunities

7. **Real-Time Pricing Service (NEW in v2.1)**
   - **Custom Supplier Quotes**: Input your actual dealer prices for accurate calculations
   - **Buy Now vs Wait Analysis**: Price trend tracking with purchase timing recommendations
   - **Regional Price Adjustments**: 7 regions with automatic price multipliers
   - **Supplier Comparison**: Compare quotes across multiple suppliers
   - **Price Alerts**: Notifications for expiring quotes and above-average prices
   - **60+ Products**: Fertilizers, pesticides, seeds, fuel, and custom application rates

8. **Weather-Smart Spray Timing (v2.1)**
   - **Condition Evaluation**: Real-time spray condition scoring (wind, temp, humidity, inversions)
   - **Spray Window Finder**: Scans forecasts to find optimal application windows
   - **Cost of Waiting Calculator**: Economic analysis of "spray today vs wait"
   - **Disease Pressure Forecasting**: Predicts disease risk from weather patterns
   - **Growth Stage Timing**: Crop and stage-specific spray recommendations
   - **Drift Risk Assessment**: Inversion detection and mitigation recommendations

9. **Yield Response & Economic Optimum Rates (NEW in v2.2)**
   - **Yield Response Curves**: Generate curves showing yield vs nutrient rate for N, P, K
   - **Economic Optimum Rate (EOR)**: Calculate the most profitable rate, not just maximum yield
   - **Price Sensitivity Analysis**: See how optimal rates change with nutrient/grain prices
   - **Multi-Nutrient Optimization**: Optimize N, P, K together within a budget constraint
   - **Rate Scenario Comparison**: Compare profitability of different application rates
   - **5 Response Models**: Quadratic, quadratic-plateau, linear-plateau, Mitscherlich, square-root
   - **Soil Test Adjustments**: Rates adjusted based on soil test levels (very low to very high)

## 💰 Business Value

### What Makes This Worth Money?

- **46 Pests/Diseases** with complete management information
- **40+ Pesticide Products** with real label data (rates, PHI, REI)
- **Economic Models** showing ROI for every recommendation
- **Resistance Management** built into all recommendations
- **Professional Knowledge** equivalent to extension bulletins

### Example ROI

**Scenario:** Soybean aphid at threshold in 160-acre field

1. System identifies pest → Soybean Aphid (95% confidence)
2. Threshold check → TREAT (300/plant vs 250 threshold)
3. Recommendation → Warrior II 2.56 oz/acre
4. Economics:
   - Protected yield: 4 bu/acre × 160 acres = 640 bu
   - Revenue protected: 640 bu × $12 = $7,680
   - Total cost: $2,800
   - **Net benefit: $4,880**
   - **ROI: 174%**

Your consulting fee is fully justified!

## 🏗️ System Architecture

```
agtools/
├── database/
│   ├── schema.sql                    # PostgreSQL database schema
│   ├── seed_data.py                  # Pest & disease knowledge base
│   └── chemical_database.py          # Pesticide products & labels
│
├── backend/
│   ├── main.py                       # FastAPI application (v2.2 - 1800+ lines, 42+ endpoints)
│   ├── requirements.txt              # Python dependencies
│   └── services/
│       ├── pest_identification.py    # Symptom-based pest ID
│       ├── disease_identification.py # Disease diagnosis
│       ├── spray_recommender.py      # Spray recommendations
│       ├── threshold_calculator.py   # Economic analysis
│       ├── weather_service.py        # Weather integration
│       ├── ai_identification.py      # AI image recognition
│       ├── labor_optimizer.py        # Labor cost optimization (v2.0)
│       ├── application_cost_optimizer.py  # Fertilizer/pesticide costs (v2.0)
│       ├── irrigation_optimizer.py   # Irrigation optimization (v2.0)
│       ├── input_cost_optimizer.py   # Unified cost analysis (v2.0)
│       ├── pricing_service.py        # Real-time pricing (v2.1)
│       ├── spray_timing_optimizer.py # Weather-smart spraying (v2.1)
│       └── yield_response_optimizer.py # Economic optimum rates (NEW v2.2)
│
├── frontend/                         # PyQt6 Desktop Application
│   ├── main.py                       # Entry point
│   ├── app.py                        # QApplication setup
│   ├── config.py                     # Settings management
│   ├── requirements.txt              # PyQt6, httpx, pyqtgraph
│   ├── api/                          # API client modules
│   │   ├── client.py                 # Base HTTP client
│   │   ├── yield_response_api.py     # Yield response endpoints
│   │   ├── spray_api.py              # Spray timing endpoints
│   │   ├── pricing_api.py            # Pricing endpoints
│   │   └── cost_optimizer_api.py     # Cost optimizer endpoints
│   ├── models/                       # Data classes
│   │   ├── yield_response.py
│   │   ├── spray.py
│   │   ├── pricing.py
│   │   └── cost_optimizer.py
│   └── ui/
│       ├── styles.py                 # Professional QSS theme
│       ├── sidebar.py                # Navigation sidebar
│       ├── main_window.py            # Main window layout
│       └── screens/
│           ├── dashboard.py          # Home screen
│           ├── yield_response.py     # Yield calculator with charts
│           ├── spray_timing.py       # Weather evaluation
│           ├── cost_optimizer.py     # Tabbed cost analysis
│           └── pricing.py            # Price management & alerts
│
├── CHANGELOG.md                      # Development changelog (reference for new sessions)
├── PROFESSIONAL_SYSTEM_GUIDE.md      # Complete documentation
├── QUICKSTART.md                     # 5-minute setup guide
└── README.md                         # This file
```

## 📊 Knowledge Base

### Corn (10 Pests + 13 Diseases)
**Pests:** Corn Rootworm, European Corn Borer, Western Bean Cutworm, Fall Armyworm, Black Cutworm, Corn Leaf Aphid, Spider Mites, Japanese Beetle, Stalk Borer, Corn Earworm

**Diseases:** Gray Leaf Spot, Northern/Southern Corn Leaf Blight, Common/Southern Rust, Tar Spot, Anthracnose, Eyespot, Goss's Wilt, Stewart's Wilt, Diplodia/Gibberella/Aspergillus Ear Rots

### Soybeans (10 Pests + 13 Diseases)
**Pests:** Soybean Aphid, Spider Mites, Bean Leaf Beetle, Japanese Beetle, Grasshoppers, Stink Bugs, Dectes Stem Borer, Soybean Looper, Thistle Caterpillar, Grape Colaspis

**Diseases:** White Mold, SDS, SCN, Brown Stem Rot, Frogeye Leaf Spot, Septoria Brown Spot, Bacterial Blight, Cercospora Leaf Blight, Anthracnose, Phytophthora Root Rot, Soybean Rust, Charcoal Rot, Pod and Stem Blight

### Chemicals (40+ Products)
**Insecticides:** Pyrethroids (Brigade, Warrior II, Mustang Maxx), Diamides (Besiege, Coragen), Neonicotinoids (Actara, Assail), Organophosphates (Lorsban), Carbamates (Sevin)

**Fungicides:** Premixes (Trivapro, Delaro, Priaxor, Stratego YLD), QoIs (Quadris), Seed Treatments (ILeVO, ApronMaxx), White Mold specific (Endura, Proline)

## 🚀 API Endpoints

### Pest & Disease Management
| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/pests` | Get pest database |
| `GET /api/v1/diseases` | Get disease database |
| `GET /api/v1/products` | Get pesticide products |
| `POST /api/v1/identify/pest` | Identify pest by symptoms |
| `POST /api/v1/identify/disease` | Identify disease |
| `POST /api/v1/identify/image` | AI image identification |
| `POST /api/v1/recommend/spray` | Get spray recommendations |
| `POST /api/v1/threshold/check` | Economic threshold analysis |
| `GET /api/v1/weather/spray-window` | Spray timing forecast |

### Input Cost Optimization (v2.0)
| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/optimize/labor/scouting` | Calculate scouting labor costs |
| `POST /api/v1/optimize/labor/application` | Application labor analysis |
| `POST /api/v1/optimize/labor/seasonal-budget` | Complete seasonal labor budget |
| `POST /api/v1/optimize/fertilizer` | Optimize fertilizer program |
| `POST /api/v1/optimize/pesticides/compare` | Compare pesticide costs |
| `POST /api/v1/optimize/spray-program` | Full spray program ROI |
| `POST /api/v1/optimize/irrigation/water-need` | Current crop water need |
| `POST /api/v1/optimize/irrigation/cost` | Irrigation cost calculator |
| `POST /api/v1/optimize/irrigation/season` | Season irrigation schedule |
| `GET /api/v1/optimize/irrigation/system-comparison` | Compare irrigation systems |
| `POST /api/v1/optimize/irrigation/water-savings` | Water savings strategies |
| `POST /api/v1/optimize/complete-analysis` | **Complete farm cost analysis** |
| `POST /api/v1/optimize/quick-estimate` | Quick cost estimate |
| `POST /api/v1/optimize/budget-worksheet` | Generate budget worksheet |

### Real-Time Pricing Service (NEW in v2.1)
| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/pricing/prices` | Get all prices (filter by category) |
| `GET /api/v1/pricing/price/{product_id}` | Get specific product price |
| `POST /api/v1/pricing/set-price` | Set custom supplier quote |
| `POST /api/v1/pricing/bulk-update` | Bulk import price list |
| `POST /api/v1/pricing/buy-recommendation` | **Buy now vs wait analysis** |
| `POST /api/v1/pricing/calculate-input-costs` | Calculate costs with custom prices |
| `POST /api/v1/pricing/compare-suppliers` | Compare supplier pricing |
| `GET /api/v1/pricing/alerts` | Expiring quotes & price alerts |
| `GET /api/v1/pricing/budget-prices/{crop}` | Generate budget price list |

### Weather-Smart Spray Timing (v2.1)
| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/spray-timing/evaluate` | Evaluate current spray conditions |
| `POST /api/v1/spray-timing/find-windows` | Find optimal windows in forecast |
| `POST /api/v1/spray-timing/cost-of-waiting` | Economic analysis of waiting |
| `POST /api/v1/spray-timing/disease-pressure` | Assess disease risk from weather |
| `GET /api/v1/spray-timing/growth-stage-timing/{crop}/{stage}` | Stage-specific guidance |

### Yield Response & Economic Optimum (NEW in v2.2)
| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/yield-response/curve` | Generate yield response curve |
| `POST /api/v1/yield-response/economic-optimum` | **Calculate Economic Optimum Rate (EOR)** |
| `POST /api/v1/yield-response/compare-rates` | Compare profitability of different rates |
| `POST /api/v1/yield-response/price-sensitivity` | Analyze EOR changes with prices |
| `POST /api/v1/yield-response/multi-nutrient` | **Optimize N, P, K with budget** |
| `GET /api/v1/yield-response/crop-parameters/{crop}` | View agronomic parameters |
| `GET /api/v1/yield-response/price-ratio-guide` | Quick field reference table |

Visit http://localhost:8000/docs for interactive documentation.

## 📖 Documentation

- **CHANGELOG.md** - Development changelog (reference at start of new sessions)
- **QUICKSTART.md** - Get running in 5 minutes
- **PROFESSIONAL_SYSTEM_GUIDE.md** - Complete system documentation
- **database/seed_data.py** - View pest/disease knowledge base
- **database/chemical_database.py** - View product library

## 🛠️ Technology Stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL with PostGIS (optional - can use in-memory)
- **AI/ML:** TensorFlow, scikit-learn
- **APIs:** Weather.gov, OpenWeather (integration ready)

## 📈 Next Steps

### Immediate Use (Week 1)
1. Run the API and test endpoints
2. Use for real field scouting
3. Validate recommendations against extension resources
4. Build confidence in the system

### Production Deployment (Month 1)
1. Set up PostgreSQL database
2. Add user authentication
3. Create simple web interface
4. Deploy to cloud (AWS, Digital Ocean, etc.)

### Business Growth (Month 2-3)
1. Build mobile app or responsive web app
2. Add field mapping and GPS integration
3. Generate PDF reports for clients
4. Integrate with equipment (sprayers, monitors)

### Advanced Features (Month 4+)
1. Custom AI model training from your field photos
2. Satellite imagery integration
3. Market price feeds for dynamic economics
4. Regional disease/pest pressure mapping

## 💡 Use Cases

### For Crop Consultants
- Make faster, data-driven recommendations
- Justify recommendations with economic analysis
- Manage resistance with built-in MOA rotation
- Scale your business with technology

### For Farmers
- Get professional-grade pest/disease identification
- Know if treatment is economically justified
- Optimize spray timing with weather
- Reduce input costs while protecting yield

### For Ag Retailers
- Provide value-added consulting services
- Recommend right products at right rates
- Build customer trust with data
- Differentiate from competitors

## 🎓 Professional Knowledge Incorporated

This system includes:
- ✅ Economic threshold methodology
- ✅ Integrated Pest Management (IPM) principles
- ✅ Resistance management strategies (IRAC/FRAC codes)
- ✅ Label compliance (PHI, REI, maximum rates)
- ✅ Application timing optimization
- ✅ Tank mix compatibility
- ✅ Weather-based decision support
- ✅ Cost optimization
- ✅ Regional pest/disease variations
- ✅ Yield response economics (diminishing returns)
- ✅ Economic Optimum Rate calculations (EOR)

## 📞 Support & Development

This is a living system designed to grow:
- Add new pests/diseases as encountered
- Refine economic models with real data
- Train custom AI models on your photos
- Integrate with your specific workflow
- Build client-specific features

## 📄 License

**PROPRIETARY LICENSE** - This software is proprietary and confidential. Commercial use is strictly prohibited without a license agreement. See [LICENSE](LICENSE) file for complete terms.

**All intellectual property rights reserved by New Generation Farms.**

## 🌟 What's Different?

Unlike simple pest ID apps, this system:
1. **Makes recommendations** - not just identification
2. **Shows the economics** - proves treatment is justified
3. **Manages resistance** - protects long-term efficacy
4. **Professional-grade** - based on extension research
5. **Complete workflow** - from scouting to application

**This is a professional tool for professional consultants.**

---

Created by [@wbp318](https://github.com/wbp318)

**Start small. Think big. Build value.**
