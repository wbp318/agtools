# Failed Tests Report - AgTools v6.12.0

**Generated:** 2026-01-15
**Test Run:** 613 passed, 7 failed, 14 skipped (98.9% pass rate)

---

## Executive Summary

| Category | Count | Root Cause |
|----------|-------|------------|
| Backend Infinity Error | 5 | Division by zero in sustainability calculations |
| API Response Format | 1 | Health endpoint returns dict, test expects list |
| Import Error | 1 | Missing `SoilTestLevel` class in yield service |
| **Total** | **7** | |

---

## Detailed Failure Analysis

### Failure #1: test_animal_timeline

**File:** `tests/test_livestock_sustainability.py:797`
**Test Class:** `TestLivestockManagement`

**Error:**
```python
AssertionError: assert False
  where False = isinstance({'count': 0, 'records': []}, list)
```

**What Happened:**
- Test calls `GET /api/v1/livestock/health?animal_id={id}`
- Test expects a `list` of health records
- API returns `{'count': 0, 'records': []}` (paginated dict format)

**Root Cause:**
The livestock health endpoint returns a paginated response with `count` and `records` keys, not a flat list.

**Fix (Test):**
```python
# Before (line 797):
assert isinstance(health_response.json(), list)

# After:
data = health_response.json()
records = data.get("records", data) if isinstance(data, dict) else data
assert isinstance(records, list)
```

**Priority:** Low (test fix only)
**Effort:** 5 minutes

---

### Failures #2-6: Sustainability Infinity Errors

**Files:**
- `test_sustainability_score_calculation` (line 1100)
- `test_biodiversity_index` (line 1177)
- `test_peer_benchmarking` (line 1276)
- `test_certification_compliance` (line 1302)
- `test_sustainability_export` (line 1349)

**Test Class:** `TestSustainability`

**Error:**
```python
ValueError: Out of range float values are not JSON compliant: inf
```

**What Happened:**
- Tests call sustainability endpoints (`/api/v1/sustainability/scorecard`, `/report`, `/export`)
- Backend calculates efficiency scores using division
- When there's no data, division by zero returns `float('inf')`
- JSON serializer cannot encode infinity values

**Root Cause (Backend):**
In `backend/services/sustainability_service.py`, calculations like:
```python
efficiency = total_output / total_input  # Returns inf when total_input = 0
```

**Affected Backend Code Locations:**

1. **`sustainability_service.py` - `get_sustainability_scorecard()`** (~line 450)
   ```python
   # Problem code pattern:
   carbon_efficiency = carbon_sequestered / carbon_emitted  # inf when emitted = 0
   water_efficiency = crop_yield / water_used  # inf when water_used = 0
   input_efficiency = output_value / input_cost  # inf when input_cost = 0
   ```

2. **`sustainability_service.py` - `get_sustainability_report()`** (~line 550)
   ```python
   # Same division patterns
   efficiency_ratio = output / input  # inf when input = 0
   ```

3. **`sustainability_service.py` - `export_sustainability_data()`** (~line 650)
   ```python
   # Exports raw calculated values including infinity
   ```

**Fix (Backend):**
```python
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide, returning default if denominator is zero or result is infinite."""
    if denominator == 0:
        return default
    result = numerator / denominator
    if math.isinf(result) or math.isnan(result):
        return default
    return result

# Usage:
carbon_efficiency = safe_divide(carbon_sequestered, carbon_emitted, default=0.0)
water_efficiency = safe_divide(crop_yield, water_used, default=0.0)
input_efficiency = safe_divide(output_value, input_cost, default=0.0)
```

**Alternative Fix (JSON Encoder):**
Add a custom JSON encoder that handles infinity:
```python
import json
import math

class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            if math.isinf(obj):
                return None  # or 0.0, or "Infinity"
            if math.isnan(obj):
                return None
        return super().default(obj)

# In FastAPI response:
return JSONResponse(content=data, encoder=SafeJSONEncoder)
```

**Priority:** High (backend bug)
**Effort:** 30 minutes
**Impact:** Fixes 5 tests

---

### Failure #7: test_yield_prediction_scenarios

**File:** `tests/test_ai_grants.py:358`
**Test Class:** `TestYieldPrediction`

**Error:**
```python
ImportError: cannot import name 'SoilTestLevel' from 'services.yield_response_optimizer'
```

**What Happened:**
- Test calls `POST /api/v1/yield-response/compare-rates`
- The endpoint imports `SoilTestLevel` from `yield_response_optimizer`
- This class/enum doesn't exist or was renamed/removed

**Root Cause (Backend):**
The `SoilTestLevel` class is referenced in the yield response optimizer but either:
1. Was never defined
2. Was removed/renamed
3. Is defined in a different location

**Investigation Needed:**
```bash
# Check if SoilTestLevel exists anywhere
grep -r "class SoilTestLevel" backend/
grep -r "SoilTestLevel" backend/services/yield_response_optimizer.py
```

**Potential Fix (Backend):**
If `SoilTestLevel` is an enum for soil test categories:
```python
# Add to yield_response_optimizer.py
from enum import Enum

class SoilTestLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
```

Or if it was moved, update the import:
```python
# Change from:
from services.yield_response_optimizer import SoilTestLevel

# To:
from services.soil_service import SoilTestLevel  # or wherever it is
```

**Priority:** Medium (backend import error)
**Effort:** 15 minutes
**Impact:** Fixes 1 test

---

## Summary Fix Plan

### Phase 1: Quick Test Fixes (10 minutes)

| Test | Fix | Location |
|------|-----|----------|
| `test_animal_timeline` | Handle dict response format | `test_livestock_sustainability.py:797` |

### Phase 2: Backend Fixes (45 minutes)

| Issue | Fix | Location |
|-------|-----|----------|
| Infinity values | Add `safe_divide()` helper | `sustainability_service.py` |
| SoilTestLevel import | Define missing class or fix import | `yield_response_optimizer.py` |

### Implementation Order

1. **[5 min]** Fix `test_animal_timeline` assertion
2. **[15 min]** Add `SoilTestLevel` enum to backend
3. **[30 min]** Add `safe_divide()` helper and update all division operations in sustainability service

---

## Code Patches

### Patch 1: Fix test_animal_timeline

```python
# File: tests/test_livestock_sustainability.py
# Line: 797

# Replace:
assert isinstance(health_response.json(), list)

# With:
health_data = health_response.json()
health_records = health_data.get("records", health_data) if isinstance(health_data, dict) else health_data
assert isinstance(health_records, list), f"Expected list of health records, got {type(health_records)}"
```

### Patch 2: Add safe_divide helper

```python
# File: backend/services/sustainability_service.py
# Add at top of file after imports:

import math

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, handling division by zero and infinity.

    Args:
        numerator: The dividend
        denominator: The divisor
        default: Value to return if division is invalid (default 0.0)

    Returns:
        The quotient, or default if denominator is 0 or result is inf/nan
    """
    if denominator == 0 or denominator is None:
        return default
    try:
        result = numerator / denominator
        if math.isinf(result) or math.isnan(result):
            return default
        return result
    except (TypeError, ZeroDivisionError):
        return default
```

### Patch 3: Add SoilTestLevel enum

```python
# File: backend/services/yield_response_optimizer.py
# Add after imports:

from enum import Enum

class SoilTestLevel(str, Enum):
    """Soil test result categories for nutrient recommendations."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    OPTIMUM = "optimum"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_ppm(cls, ppm: float, nutrient: str = "phosphorus") -> "SoilTestLevel":
        """Convert PPM reading to soil test level based on nutrient type."""
        # Default thresholds for phosphorus (Bray P1)
        if ppm < 8:
            return cls.VERY_LOW
        elif ppm < 15:
            return cls.LOW
        elif ppm < 25:
            return cls.MEDIUM
        elif ppm < 40:
            return cls.OPTIMUM
        elif ppm < 60:
            return cls.HIGH
        else:
            return cls.VERY_HIGH
```

---

## Verification Commands

After applying fixes, run:

```bash
# Test specific failures
pytest tests/test_livestock_sustainability.py::TestLivestockManagement::test_animal_timeline -v
pytest tests/test_livestock_sustainability.py::TestSustainability -v
pytest tests/test_ai_grants.py::TestYieldPrediction::test_yield_prediction_scenarios -v

# Run all tests
pytest tests/test_critical_paths.py tests/test_auth_security.py tests/test_climate_costs.py tests/test_livestock_sustainability.py tests/test_reporting_safety.py tests/test_ai_grants.py tests/test_inventory_equipment_seed.py tests/test_business_research.py tests/test_genfin_endpoints.py --tb=no -q
```

---

## Expected Results After Fixes

| Metric | Before | After |
|--------|--------|-------|
| Passed | 613 | 620 |
| Failed | 7 | 0 |
| Skipped | 14 | 14 |
| Pass Rate | 98.9% | 100% |

---

## Notes

- The 14 skipped tests are intentional (endpoints not implemented or optional features)
- Rate limiting warnings during tests are expected and don't cause failures
- Deprecation warnings (datetime.utcnow) are backend code style issues, not test failures
