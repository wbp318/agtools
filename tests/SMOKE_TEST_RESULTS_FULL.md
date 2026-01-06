# Full Smoke Test Results - AgTools v3.1

**Date:** 2026-01-05 22:32:48
**Duration:** 2.18 seconds

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 64 |
| Passed | 44 |
| Failed | 20 |
| **Pass Rate** | **68.8%** |

## Results by Category

### AI (8/9 passed)

| Test | Status | Details |
|------|--------|--------|
| AIImageService | ❌ Fail | No module named 'httpx' |
| CropHealthService singleton | ✅ Pass | - |
| CropHealthService ready | ✅ Pass | - |
| YieldPredictionService singleton | ✅ Pass | - |
| YieldPredictionService ready | ✅ Pass | - |
| ExpenseCategorizationService singleton | ✅ Pass | - |
| ExpenseCategorizationService ready | ✅ Pass | - |
| SprayAIService singleton | ✅ Pass | - |
| SprayAIService ready | ✅ Pass | - |

### Database (10/10 passed)

| Test | Status | Details |
|------|--------|--------|
| schema.sql exists | ✅ Pass | - |
| Schema readable | ✅ Pass | 10416 bytes |
| Table definition: crops | ✅ Pass | - |
| Table definition: pests | ✅ Pass | - |
| Table definition: diseases | ✅ Pass | - |
| Table definition: fields | ✅ Pass | - |
| Table definition: products | ✅ Pass | - |
| seed_data.py exists | ✅ Pass | - |
| Seed data loads | ✅ Pass | 20 pests, 27 diseases |
| chemical_database.py exists | ✅ Pass | - |

### Docker (7/7 passed)

| Test | Status | Details |
|------|--------|--------|
| Dockerfile exists | ✅ Pass | - |
| docker-compose.yml exists | ✅ Pass | - |
| .env.example exists | ✅ Pass | - |
| .dockerignore exists | ✅ Pass | - |
| Dockerfile has FROM | ✅ Pass | - |
| Dockerfile has EXPOSE | ✅ Pass | - |
| Dockerfile has CMD | ✅ Pass | - |

### Email (6/6 passed)

| Test | Status | Details |
|------|--------|--------|
| EmailNotificationService import | ✅ Pass | - |
| EmailNotificationService singleton | ✅ Pass | - |
| Notification types loaded | ✅ Pass | 10 types |
| Create notification | ✅ Pass | - |
| Notification has subject | ✅ Pass | - |
| Notification has body | ✅ Pass | - |

### Export (5/6 passed)

| Test | Status | Details |
|------|--------|--------|
| DataExportService import | ✅ Pass | - |
| DataExportService singleton | ✅ Pass | - |
| CSV export | ✅ Pass | 58 bytes |
| CSV has headers | ✅ Pass | - |
| Excel export | ❌ Fail | openpyxl not installed |
| Fields export | ✅ Pass | - |

### Main App (0/1 passed)

| Test | Status | Details |
|------|--------|--------|
| FastAPI app loads | ❌ Fail | No module named 'fastapi' |

### Mobile (3/5 passed)

| Test | Status | Details |
|------|--------|--------|
| Mobile routes module | ❌ Fail | No module named 'fastapi' |
| Mobile auth module | ❌ Fail | No module named 'fastapi' |
| Template: base.html | ✅ Pass | - |
| Template: login.html | ✅ Pass | - |
| Template: offline.html | ✅ Pass | - |

### PDF (1/2 passed)

| Test | Status | Details |
|------|--------|--------|
| PDFReportService import | ✅ Pass | - |
| PDFReportService singleton | ❌ Fail | reportlab is required for PDF generation. Install  |

### Services (4/18 passed)

| Test | Status | Details |
|------|--------|--------|
| AuthService | ❌ Fail | No module named 'jose' |
| UserService | ❌ Fail | No module named 'pydantic' |
| TaskService | ❌ Fail | No module named 'pydantic' |
| FieldService | ❌ Fail | No module named 'pydantic' |
| FieldOperationsService | ❌ Fail | No module named 'pydantic' |
| EquipmentService | ❌ Fail | No module named 'pydantic' |
| InventoryService | ❌ Fail | No module named 'pydantic' |
| ReportingService | ❌ Fail | No module named 'pydantic' |
| TimeEntryService | ❌ Fail | No module named 'pydantic' |
| PhotoService | ❌ Fail | No module named 'pydantic' |
| CostTrackingService | ❌ Fail | No module named 'pydantic' |
| AccountingImportService | ❌ Fail | No module named 'pydantic' |
| ProfitabilityService | ❌ Fail | No module named 'pydantic' |
| AIImageService | ❌ Fail | No module named 'httpx' |
| CropHealthService | ✅ Pass | - |
| YieldPredictionService | ✅ Pass | - |
| ExpenseCategorizationService | ✅ Pass | - |
| SprayAIService | ✅ Pass | - |

