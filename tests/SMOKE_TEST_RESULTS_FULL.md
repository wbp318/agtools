# Full Smoke Test Results - AgTools v3.1

**Date:** 2025-12-27 12:35:27
**Duration:** 3.98 seconds

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | 90 |
| Passed | 90 |
| Failed | 0 |
| **Pass Rate** | **100.0%** |

## Results by Category

### AI (10/10 passed)

| Test | Status | Details |
|------|--------|--------|
| AIImageService singleton | ✅ Pass | - |
| Knowledge base loaded | ✅ Pass | 2 crops |
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

### Export (7/7 passed)

| Test | Status | Details |
|------|--------|--------|
| DataExportService import | ✅ Pass | - |
| DataExportService singleton | ✅ Pass | - |
| CSV export | ✅ Pass | 58 bytes |
| CSV has headers | ✅ Pass | - |
| Excel export | ✅ Pass | 5129 bytes |
| Excel file valid | ✅ Pass | - |
| Fields export | ✅ Pass | - |

### Main App (1/1 passed)

| Test | Status | Details |
|------|--------|--------|
| FastAPI app loads | ✅ Pass | 228 routes |

### Mobile (5/5 passed)

| Test | Status | Details |
|------|--------|--------|
| Mobile routes module | ✅ Pass | - |
| Mobile auth module | ✅ Pass | - |
| Template: base.html | ✅ Pass | - |
| Template: login.html | ✅ Pass | - |
| Template: offline.html | ✅ Pass | - |

### PDF (5/5 passed)

| Test | Status | Details |
|------|--------|--------|
| PDFReportService import | ✅ Pass | - |
| PDFReportService singleton | ✅ Pass | - |
| Generate scouting report | ✅ Pass | 2498 bytes |
| Generate spray report | ✅ Pass | 2861 bytes |
| Generate cost report | ✅ Pass | 2420 bytes |

### Routes (21/21 passed)

| Test | Status | Details |
|------|--------|--------|
| auth endpoints | ✅ Pass | 6 routes |
| users endpoints | ✅ Pass | 6 routes |
| crews endpoints | ✅ Pass | 7 routes |
| tasks endpoints | ✅ Pass | 6 routes |
| fields endpoints | ✅ Pass | 8 routes |
| operations endpoints | ✅ Pass | 6 routes |
| equipment endpoints | ✅ Pass | 12 routes |
| maintenance endpoints | ✅ Pass | 4 routes |
| inventory endpoints | ✅ Pass | 13 routes |
| reports endpoints | ✅ Pass | 14 routes |
| costs endpoints | ✅ Pass | 24 routes |
| quickbooks endpoints | ✅ Pass | 7 routes |
| profitability endpoints | ✅ Pass | 7 routes |
| ai endpoints | ✅ Pass | 28 routes |
| optimize endpoints | ✅ Pass | 14 routes |
| pricing endpoints | ✅ Pass | 9 routes |
| spray-timing endpoints | ✅ Pass | 5 routes |
| yield-response endpoints | ✅ Pass | 7 routes |
| identify endpoints | ✅ Pass | 3 routes |
| recommend endpoints | ✅ Pass | 1 routes |
| mobile endpoints | ✅ Pass | 12 routes |

### Services (18/18 passed)

| Test | Status | Details |
|------|--------|--------|
| AuthService | ✅ Pass | - |
| UserService | ✅ Pass | - |
| TaskService | ✅ Pass | - |
| FieldService | ✅ Pass | - |
| FieldOperationsService | ✅ Pass | - |
| EquipmentService | ✅ Pass | - |
| InventoryService | ✅ Pass | - |
| ReportingService | ✅ Pass | - |
| TimeEntryService | ✅ Pass | - |
| PhotoService | ✅ Pass | - |
| CostTrackingService | ✅ Pass | - |
| QuickBooksImportService | ✅ Pass | - |
| ProfitabilityService | ✅ Pass | - |
| AIImageService | ✅ Pass | - |
| CropHealthService | ✅ Pass | - |
| YieldPredictionService | ✅ Pass | - |
| ExpenseCategorizationService | ✅ Pass | - |
| SprayAIService | ✅ Pass | - |

