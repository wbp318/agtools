# Measurement Converter for Spray Applications

> **Feature:** Imperial to Metric conversion for agricultural spray applications
> **Target Version:** 6.14.0
> **Status:** Implementation Plan

## Overview

Build a comprehensive measurement converter for agricultural spray applications, converting imperial units to metric for South African/Brazilian operators. The feature supports:

1. **Direct input conversion** - Manual entry from consultant recommendations
2. **AgTools integration** - Automatic conversion of spray recommendations
3. **Side-by-side display** - Both imperial and metric shown together
4. **Tank mix calculator** - Field-ready calculations in metric
5. **Reference products** - Common chemicals with pre-converted rates

---

## Core Conversion Constants

```python
# Application Rates (per area)
GAL_PER_ACRE_TO_L_PER_HA = 9.354      # 1 gal/acre = 9.354 L/ha
LB_PER_ACRE_TO_KG_PER_HA = 1.121      # 1 lb/acre = 1.121 kg/ha
OZ_PER_ACRE_TO_G_PER_HA = 70.05       # 1 oz/acre = 70.05 g/ha
FL_OZ_PER_ACRE_TO_ML_PER_HA = 73.08   # 1 fl oz/acre = 73.08 mL/ha
PT_PER_ACRE_TO_L_PER_HA = 1.169       # 1 pint/acre = 1.169 L/ha
QT_PER_ACRE_TO_L_PER_HA = 2.338       # 1 quart/acre = 2.338 L/ha

# Volume
GAL_TO_L = 3.785
FL_OZ_TO_ML = 29.574
QT_TO_L = 0.946
PT_TO_L = 0.473

# Weight
LB_TO_KG = 0.4536
OZ_TO_G = 28.35

# Area
ACRE_TO_HA = 0.4047

# Speed
MPH_TO_KMH = 1.609

# Pressure
PSI_TO_BAR = 0.0689

# Temperature
def f_to_c(f): return (f - 32) * 5/9
```

---

## Files to Create

### 1. Backend Service
**File:** `backend/services/measurement_converter_service.py`

**Functions:**
- `convert_rate(value, from_unit, to_unit)` - Generic rate conversion
- `convert_spray_rate(value, unit)` - Spray rate to metric (returns both units)
- `calculate_tank_mix(tank_size_L, rate_per_ha, field_size_ha)` - Tank mix calculator
- `get_reference_products()` - Common products with pre-converted rates
- `convert_recommendation(recommendation_dict)` - Takes AgTools recommendation, adds metric

### 2. API Router
**File:** `backend/routers/converters.py`

**Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/convert/spray-rate` | POST | Convert single spray rate |
| `/api/v1/convert/tank-mix` | POST | Calculate tank mix amounts |
| `/api/v1/convert/reference-products` | GET | Get common products with rates |
| `/api/v1/convert/batch` | POST | Bulk conversions |
| `/api/v1/convert/recommendation` | POST | Convert AgTools recommendation |

### 3. Frontend Models
**File:** `frontend/models/measurement_converter.py`

```python
@dataclass
class ConversionResult:
    imperial_value: float
    imperial_unit: str
    imperial_display: str  # "32 fl oz/acre"
    metric_value: float
    metric_unit: str
    metric_display: str    # "2.34 L/ha"

@dataclass
class TankMixResult:
    tank_size_liters: float
    rate_per_ha: float
    field_size_ha: float
    product_per_tank: float
    tanks_needed: int
    coverage_per_tank_ha: float
    leftover_liters: float
```

### 4. Frontend API Client
**File:** `frontend/api/measurement_converter_api.py`

### 5. Frontend Screen
**File:** `frontend/ui/screens/measurement_converter.py`

**Three Tabs:**

| Tab | Features |
|-----|----------|
| **Quick Converter** | Unit type dropdown, value input, from/to units, dual display |
| **Tank Mix Calculator** | Tank size, rate, field size inputs; product/tank results |
| **Reference Products** | Category filter, search, sortable table with both units |

---

## Integration Points

### 1. Spray Recommender Service
**File:** `backend/services/spray_recommender.py`

Modify `_format_product_recommendation()` to include metric equivalents:
```python
# BEFORE:
"rate": "3 oz/ac"

# AFTER:
"rate": "3 oz/ac",
"rate_metric": "210 g/ha",
"rate_imperial": "3 oz/ac"
```

### 2. Spray Timing Frontend
**File:** `frontend/ui/screens/spray_timing.py`

Modify `SpraySettingsPanel` to show dual units side-by-side.

### 3. Sidebar Navigation
**File:** `frontend/ui/sidebar.py`

Add "Unit Converter" menu item under Tools section.

---

## Reference Products Data

### Herbicides
| Product | Imperial Rate | Metric Rate | Use Case |
|---------|---------------|-------------|----------|
| Glyphosate (Roundup PowerMax) | 32 fl oz/acre | 2.34 L/ha | Burndown |
| Glyphosate (Roundup PowerMax) | 22 fl oz/acre | 1.61 L/ha | Pre-plant |
| 2,4-D Amine | 1 pt/acre | 1.17 L/ha | Broadleaf weeds |
| 2,4-D Amine | 2 pt/acre | 2.34 L/ha | Tough perennials |
| Dicamba (Clarity) | 8-16 fl oz/acre | 0.58-1.17 L/ha | Broadleaf |
| Atrazine | 1-2 qt/acre | 2.34-4.68 L/ha | Pre-emerge |
| Metolachlor (Dual II Magnum) | 1-1.5 pt/acre | 1.17-1.75 L/ha | Grass control |

### Fungicides
| Product | Imperial Rate | Metric Rate | Use Case |
|---------|---------------|-------------|----------|
| Triazole (Tilt, Folicur) | 4-6 fl oz/acre | 292-439 mL/ha | Foliar disease |
| Strobilurin (Headline, Quadris) | 6-12 fl oz/acre | 439-877 mL/ha | Preventive |
| Mancozeb | 1.5-2 lb/acre | 1.68-2.24 kg/ha | Contact fungicide |

### Insecticides
| Product | Imperial Rate | Metric Rate | Use Case |
|---------|---------------|-------------|----------|
| Chlorpyrifos (Lorsban) | 1-2 pt/acre | 1.17-2.34 L/ha | Soil insects |
| Lambda-cyhalothrin (Warrior) | 2-3 fl oz/acre | 146-219 mL/ha | Foliar insects |
| Bifenthrin (Brigade) | 2-6 fl oz/acre | 146-439 mL/ha | Broad spectrum |

### Adjuvants
| Product | Imperial Rate | Metric Rate | Use Case |
|---------|---------------|-------------|----------|
| Crop oil concentrate | 1-2 pt/acre | 1.17-2.34 L/ha | Penetrant |
| Non-ionic surfactant | 0.25-0.5% v/v | 0.25-0.5% v/v | Spreader |
| Ammonium sulfate | 8.5-17 lb/100 gal | 1-2 kg/100 L | Water conditioner |

---

## Implementation Order

1. Backend service with conversion functions
2. API router with endpoints
3. Frontend models and API client
4. Frontend converter screen (standalone)
5. Add to sidebar navigation
6. Test standalone converter works
7. Integrate into spray_recommender.py responses
8. Integrate into spray_timing.py display
9. Final testing across all integration points

---

## Verification

### Backend Tests
- Unit test all conversion functions with known values
- Test tank mix calculator with edge cases
- Test API endpoints return correct formats

### Frontend Manual Testing
- Convert known values and verify accuracy
- Test tank mix calculator with real-world scenarios
- Verify reference products display correctly

### Integration Testing
- Verify spray recommendations show both units
- Verify spray timing screen shows dual units
- Test with actual AgTools recommendations
