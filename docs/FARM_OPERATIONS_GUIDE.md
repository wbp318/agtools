# Farm Operations Suite - Complete Guide

*Version 6.4.0 | December 2025*

---

## Overview

The **Farm Operations Suite** adds comprehensive farm operations management to AgTools. This release includes two complete modules with more planned.

### Current Modules (v6.4.0)

1. **Livestock Management** - Track all livestock species with health, breeding, and sales
2. **Seed & Planting** - Seed inventory, planting records, and emergence tracking

### Coming Soon (v6.4.x)

3. **Harvest Module** - Scale tickets, moisture tracking, yield analysis
4. **Soil & Fertility** - Soil tests, lab imports, nutrient recommendations
5. **Crop Planning + FSA** - Rotations, budgets, base acres, PLC/ARC, CRP

---

## Module 1: Livestock Management

### Supported Species

| Species | Gestation Days | Common Uses |
|---------|----------------|-------------|
| Cattle | 283 | Beef, dairy, breeding |
| Hogs | 114 | Pork production |
| Poultry | N/A | Eggs, meat (flock-based) |
| Sheep | 152 | Wool, meat |
| Goats | 150 | Meat, dairy, brush clearing |

### Individual Animal Tracking

Track individual animals with:

| Field | Description |
|-------|-------------|
| Tag Number | Unique identifier (ear tag, RFID) |
| Name | Optional animal name |
| Species | Cattle, Hog, Poultry, Sheep, Goat |
| Breed | Species-specific breed list |
| Sex | Male, Female, Castrated |
| Birth Date | Date of birth |
| Purchase Date | When acquired |
| Purchase Price | Cost of animal |
| Sire/Dam | Parent tracking (lineage) |
| Status | Active, Sold, Deceased, Culled |

### Group/Batch Tracking

For poultry flocks and hog batches:

| Field | Description |
|-------|-------------|
| Group Name | Identifier (e.g., "Spring 2025 Broilers") |
| Species | Poultry, Hog |
| Head Count | Number of animals |
| Start Date | When group started |
| Source | Where acquired |
| Cost Per Head | Price per animal |
| Location | Barn/pen location |
| Status | Active, Sold, Processed |

### Health Records

Track all health events:

| Record Type | Use Case |
|-------------|----------|
| Vaccination | Routine vaccinations |
| Treatment | Illness/injury treatments |
| Vet Visit | Veterinary consultations |
| Injury | Injury documentation |
| Illness | Disease tracking |
| Deworming | Parasite control |

**Fields:**
- Record date and type
- Description of event
- Medication/product used
- Dosage and administration route
- Who administered
- Veterinarian name
- Cost
- Next due date (for scheduling)

### Breeding Records

Complete breeding management:

| Field | Description |
|-------|-------------|
| Female ID | Breeding female |
| Male ID | Breeding male (optional) |
| Breeding Date | When bred |
| Method | Natural or AI |
| Expected Due Date | Auto-calculated from gestation |
| Actual Birth Date | When birthing occurred |
| Offspring Count | Total born |
| Live Births | Surviving offspring |
| Status | Pending, Confirmed, Failed, Complete |

**Gestation Calculation:**
The system automatically calculates expected due dates based on species-specific gestation periods.

### Weight Tracking

Monitor growth performance:

| Field | Description |
|-------|-------------|
| Animal/Group ID | Which animal or group |
| Weight Date | When weighed |
| Weight (lbs) | Measured weight |
| Avg Weight | For groups only |
| Sample Size | For groups only |
| Notes | Weaning, sale, etc. |

**ADG Calculation:**
Average Daily Gain is automatically calculated between weight records:
```
ADG = (Current Weight - Previous Weight) / Days Between Weights
```

### Sale Records

Track all sales:

| Field | Description |
|-------|-------------|
| Animal/Group ID | What was sold |
| Sale Date | When sold |
| Buyer Name | Who bought |
| Head Count | Number sold |
| Sale Price | Total price |
| Sale Weight | Total weight sold |
| Price Per Lb | $/lb calculation |
| Market Name | Auction, direct, etc. |

---

## Module 2: Seed & Planting

### Supported Crops

| Crop | Common Traits |
|------|---------------|
| Corn | RR2X, VT2P, SmartStax, Trecepta |
| Soybean | RR2X, Enlist E3, XtendFlex, LLGT27 |
| Wheat | Clearfield, CoAXium |
| Cotton | Bollgard II, TwinLink Plus |
| Rice | Clearfield, Provisia |
| Sorghum | Inzen, Double Team |
| Alfalfa | Roundup Ready |
| Other | Various |

### Seed Inventory

Track all seed varieties:

| Field | Description |
|-------|-------------|
| Variety Name | Seed variety (e.g., "P1197AM") |
| Crop Type | Corn, Soybean, etc. |
| Brand | DeKalb, Pioneer, Asgrow, etc. |
| Product Code | Manufacturer's code |
| Trait Package | RR2X, VT2P, Enlist, etc. |
| Relative Maturity | 2.5, 105 days, etc. |
| Germination Rate | Tested germination % |
| Quantity Units | Bags, units, lbs, bushels |
| Quantity On Hand | Current inventory |
| Unit Cost | Price per unit |
| Lot Number | Manufacturer lot |
| Storage Location | Where stored |
| Supplier | Where purchased |

### Seed Treatments

Track treatments applied to seed:

| Treatment Type | Description |
|----------------|-------------|
| Fungicide | Disease protection |
| Insecticide | Pest protection |
| Nematicide | Nematode control |
| Inoculant | Nitrogen fixation (soybeans) |
| Biological | Beneficial organisms |
| Other | Custom treatments |

**Fields:**
- Treatment name and type
- Active ingredient
- Rate and unit
- Cost per unit
- Application date
- Applied by

### Planting Records

Document all plantings:

| Field | Description |
|-------|-------------|
| Field ID | Which field planted |
| Seed Inventory ID | Which seed used |
| Planting Date | When planted |
| Planting Rate | Seeds/acre, lbs/acre, etc. |
| Row Spacing | Inches between rows |
| Planting Depth | Inches |
| Acres Planted | Total acres |
| Population Target | Plants/acre goal |
| Equipment | Planter used |
| Soil Temperature | At planting |
| Soil Moisture | Dry, Adequate, Wet, Saturated |
| Weather Conditions | Notes |
| Seed Lot Used | Lot number planted |
| Units Used | Bags/units used |
| Cost Per Acre | Calculated cost |
| Status | Planned, In Progress, Completed, Replant Needed |

**Automatic Seed Deduction:**
When a planting record is created with units used, the system automatically deducts from seed inventory.

### Emergence Tracking

Monitor stand establishment:

| Field | Description |
|-------|-------------|
| Planting Record ID | Which planting |
| Check Date | When checked |
| Days After Planting | Auto-calculated |
| Stand Count | Plants counted |
| Count Area | Row feet, sq ft, etc. |
| Plants Per Acre | Calculated population |
| Stand Percentage | % of target achieved |
| Uniformity Score | 1-5 rating |
| Vigor Score | 1-5 rating |
| Growth Stage | VE, V1, V2, etc. |
| Issues Noted | Crusting, insects, etc. |

**Stand Percentage Calculation:**
```
Stand % = (Actual Plants/Acre / Target Population) x 100
```

---

## API Endpoints

### Livestock Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/livestock/animals` | List all animals |
| POST | `/api/v1/livestock/animals` | Add new animal |
| GET | `/api/v1/livestock/animals/{id}` | Get animal details |
| PUT | `/api/v1/livestock/animals/{id}` | Update animal |
| DELETE | `/api/v1/livestock/animals/{id}` | Delete animal |
| GET | `/api/v1/livestock/groups` | List groups/flocks |
| POST | `/api/v1/livestock/groups` | Create group |
| GET | `/api/v1/livestock/groups/{id}` | Get group details |
| PUT | `/api/v1/livestock/groups/{id}` | Update group |
| DELETE | `/api/v1/livestock/groups/{id}` | Delete group |
| GET | `/api/v1/livestock/health` | List health records |
| POST | `/api/v1/livestock/health` | Add health record |
| GET | `/api/v1/livestock/health/{id}` | Get health record |
| DELETE | `/api/v1/livestock/health/{id}` | Delete health record |
| GET | `/api/v1/livestock/breeding` | List breeding records |
| POST | `/api/v1/livestock/breeding` | Add breeding record |
| PUT | `/api/v1/livestock/breeding/{id}` | Update breeding record |
| GET | `/api/v1/livestock/weights` | List weight records |
| POST | `/api/v1/livestock/weights` | Add weight record |
| GET | `/api/v1/livestock/sales` | List sales |
| POST | `/api/v1/livestock/sales` | Record sale |
| GET | `/api/v1/livestock/summary` | Herd statistics |

### Seed & Planting

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/seeds` | List seed inventory |
| POST | `/api/v1/seeds` | Add seed variety |
| GET | `/api/v1/seeds/{id}` | Get seed details |
| PUT | `/api/v1/seeds/{id}` | Update seed |
| DELETE | `/api/v1/seeds/{id}` | Delete seed |
| GET | `/api/v1/seeds/summary` | Seed statistics |
| GET | `/api/v1/seeds/traits/{crop}` | Trait packages by crop |
| GET | `/api/v1/planting` | List planting records |
| POST | `/api/v1/planting` | Create planting record |
| GET | `/api/v1/planting/{id}` | Get planting details |
| PUT | `/api/v1/planting/{id}` | Update planting |
| GET | `/api/v1/planting/{id}/emergence` | List emergence records |
| POST | `/api/v1/planting/emergence` | Add emergence check |

---

## Desktop Application

### Navigation

Access Farm Operations modules from the sidebar:
- **Farm Ops** section
- **Livestock** - Livestock management screen
- **Seeds** - Seed & planting screen

### Livestock Screen

**Tabs:**
1. **Animals** - Individual animal management
2. **Groups** - Batch/flock tracking
3. **Health Records** - Vaccinations and treatments
4. **Weights** - Weight history
5. **Sales** - Sale records

**Summary Cards:**
- Total Head
- Total Groups
- Health Alerts (vaccinations due)
- Average Weight

**Actions:**
- Add Animal / Add Group
- View/Edit details
- Record health event
- Record weight
- Record sale

### Seed & Planting Screen

**Tabs:**
1. **Seed Inventory** - Variety management
2. **Planting Records** - Field plantings
3. **Emergence Checks** - Stand monitoring

**Summary Cards:**
- Varieties in Stock
- Total Seed Value
- Acres Planted
- Average Stand %

**Actions:**
- Add Seed Variety
- Create Planting Record
- Add Emergence Check
- Filter by crop, field, status

---

## Best Practices

### Livestock Management

**Daily:**
- Record any health treatments
- Note animal observations

**Weekly:**
- Check for upcoming vaccinations
- Review breeding due dates
- Weigh growing animals

**Monthly:**
- Review herd health trends
- Update inventory counts
- Reconcile sales records

### Seed & Planting

**Pre-Season:**
- Enter seed inventory
- Record seed treatments
- Plan field assignments

**Planting Season:**
- Create planting records daily
- Note conditions (soil temp, moisture)
- Track units used per field

**Post-Planting:**
- Check emergence at 7-10 days
- Record stand counts
- Document any replant decisions

---

## Planned Features (v6.4.x)

### Module 3: Harvest Management

- Scale ticket entry and tracking
- Moisture adjustment calculations
- Yield per field/variety analysis
- CSV import from John Deere Ops Center
- CSV import from Climate FieldView
- Delivery and settlement tracking

### Module 4: Soil & Fertility

- Soil sample entry and history
- Lab CSV imports (Ward Labs, A&L, Midwest Labs)
- Nutrient trend analysis
- Fertilizer plan creation
- Application tracking
- Cost per acre calculations

### Module 5: Crop Planning + FSA

- Multi-year crop rotation planning
- Budget creation with break-even
- Scenario modeling (what-if)
- FSA farm/tract registration
- Base acres tracking
- PLC/ARC election tracking
- CRP contract management
- Payment history tracking

---

## GenFin Integration (v6.5.0)

Farm Operations integrates seamlessly with **GenFin** - the complete farm financial management system:

| Operation | GenFin Integration |
|-----------|-------------------|
| **Livestock Sales** | Auto-create invoices and record revenue |
| **Livestock Purchases** | Auto-create bills and track expenses |
| **Seed Purchases** | Track as inventory, record vendor payments |
| **Planting Costs** | Allocate expenses to fields for cost-per-acre |

GenFin v6.5.0 provides full QuickBooks Desktop parity:
- Bank Accounts, Check Register, Reconciliation
- Customer Statements, Credit Memos
- Credit Cards, Vendor Credits
- Pay Liabilities, Payroll Center
- Fixed Assets, Recurring/Memorized Transactions
- Budgets, Entities (Classes/Locations), Settings, Help

See `docs/GENFIN.md` for complete GenFin documentation.

---

## Support

Farm Operations Suite is part of AgTools Professional.

- **API Documentation:** http://localhost:8000/docs
- **CHANGELOG.md:** Development history
- **Issues:** GitHub repository

---

*Farm Operations Suite - Professional Farm Management*

**Copyright 2025 New Generation Farms. All Rights Reserved.**
