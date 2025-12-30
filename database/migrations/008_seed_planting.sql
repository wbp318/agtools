-- Migration 008: Seed & Planting Management
-- AgTools v6.4.0 - Farm Operations Suite
-- Tracks seed inventory, planting records, seed treatments, and emergence

-- Seed Inventory
CREATE TABLE IF NOT EXISTS seed_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variety_name TEXT NOT NULL,
    crop_type TEXT NOT NULL CHECK (crop_type IN (
        'corn', 'soybean', 'wheat', 'cotton', 'rice', 'sorghum',
        'alfalfa', 'hay', 'oats', 'barley', 'sunflower', 'canola', 'other'
    )),
    brand TEXT,
    product_code TEXT,
    trait_package TEXT,  -- RR2X, VT2P, Enlist, XtendFlex, etc.
    relative_maturity TEXT,  -- 2.5, 105 days, etc.
    seed_size REAL,  -- seeds per pound or per unit
    germination_rate REAL CHECK (germination_rate IS NULL OR (germination_rate >= 0 AND germination_rate <= 100)),
    quantity_units TEXT DEFAULT 'bags' CHECK (quantity_units IN ('bags', 'units', 'lbs', 'bushels', 'cwt')),
    quantity_on_hand REAL DEFAULT 0,
    unit_cost REAL DEFAULT 0,
    lot_number TEXT,
    purchase_date DATE,
    expiration_date DATE,
    storage_location TEXT,
    supplier TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Seed Treatments (applied to seed inventory)
CREATE TABLE IF NOT EXISTS seed_treatments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seed_inventory_id INTEGER NOT NULL REFERENCES seed_inventory(id) ON DELETE CASCADE,
    treatment_name TEXT NOT NULL,
    treatment_type TEXT CHECK (treatment_type IN (
        'fungicide', 'insecticide', 'nematicide', 'inoculant', 'biological', 'other'
    )),
    active_ingredient TEXT,
    rate TEXT,
    rate_unit TEXT,
    cost_per_unit REAL DEFAULT 0,
    application_date DATE,
    applied_by TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Planting Records
CREATE TABLE IF NOT EXISTS planting_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER REFERENCES fields(id),
    seed_inventory_id INTEGER REFERENCES seed_inventory(id),
    planting_date DATE NOT NULL,
    planting_rate REAL NOT NULL,
    rate_unit TEXT DEFAULT 'seeds/acre' CHECK (rate_unit IN (
        'seeds/acre', 'lbs/acre', 'bushels/acre', 'units/acre', 'bags/acre'
    )),
    row_spacing REAL,  -- inches
    row_spacing_unit TEXT DEFAULT 'inches',
    planting_depth REAL,  -- inches
    acres_planted REAL NOT NULL,
    population_target INTEGER,  -- plants/acre target
    equipment_id INTEGER REFERENCES equipment(id),
    soil_temp REAL,
    soil_moisture TEXT CHECK (soil_moisture IN ('dry', 'adequate', 'wet', 'saturated')),
    weather_conditions TEXT,
    wind_speed REAL,
    operator_id INTEGER REFERENCES users(id),
    seed_lot_used TEXT,
    units_used REAL,
    cost_per_acre REAL,
    status TEXT DEFAULT 'completed' CHECK (status IN ('planned', 'in_progress', 'completed', 'replant_needed')),
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Emergence Records
CREATE TABLE IF NOT EXISTS emergence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planting_record_id INTEGER NOT NULL REFERENCES planting_records(id) ON DELETE CASCADE,
    check_date DATE NOT NULL,
    days_after_planting INTEGER,
    stand_count INTEGER,  -- plants counted
    count_area REAL,  -- area counted (sq ft or row feet)
    count_unit TEXT DEFAULT 'row_feet' CHECK (count_unit IN ('sq_ft', 'row_feet', '1/1000_acre')),
    plants_per_acre INTEGER,  -- calculated
    stand_percentage REAL CHECK (stand_percentage IS NULL OR (stand_percentage >= 0 AND stand_percentage <= 100)),
    uniformity_score INTEGER CHECK (uniformity_score IS NULL OR (uniformity_score >= 1 AND uniformity_score <= 5)),
    vigor_score INTEGER CHECK (vigor_score IS NULL OR (vigor_score >= 1 AND vigor_score <= 5)),
    growth_stage TEXT,  -- V1, V2, VE, etc.
    issues_noted TEXT,  -- crusting, insects, disease, etc.
    photo_path TEXT,
    gps_lat REAL,
    gps_lng REAL,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Replant Records (links to original planting)
CREATE TABLE IF NOT EXISTS replant_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_planting_id INTEGER NOT NULL REFERENCES planting_records(id),
    replant_planting_id INTEGER REFERENCES planting_records(id),
    replant_reason TEXT CHECK (replant_reason IN (
        'poor_stand', 'weather_damage', 'pest_damage', 'disease', 'flooding',
        'drought', 'hail', 'frost', 'other'
    )),
    acres_replanted REAL,
    decision_date DATE,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_seed_inventory_crop ON seed_inventory(crop_type);
CREATE INDEX IF NOT EXISTS idx_seed_inventory_brand ON seed_inventory(brand);
CREATE INDEX IF NOT EXISTS idx_seed_inventory_variety ON seed_inventory(variety_name);
CREATE INDEX IF NOT EXISTS idx_seed_inventory_active ON seed_inventory(is_active);

CREATE INDEX IF NOT EXISTS idx_seed_treatments_seed ON seed_treatments(seed_inventory_id);
CREATE INDEX IF NOT EXISTS idx_seed_treatments_type ON seed_treatments(treatment_type);

CREATE INDEX IF NOT EXISTS idx_planting_records_field ON planting_records(field_id);
CREATE INDEX IF NOT EXISTS idx_planting_records_seed ON planting_records(seed_inventory_id);
CREATE INDEX IF NOT EXISTS idx_planting_records_date ON planting_records(planting_date);
CREATE INDEX IF NOT EXISTS idx_planting_records_status ON planting_records(status);

CREATE INDEX IF NOT EXISTS idx_emergence_planting ON emergence_records(planting_record_id);
CREATE INDEX IF NOT EXISTS idx_emergence_date ON emergence_records(check_date);

CREATE INDEX IF NOT EXISTS idx_replant_original ON replant_records(original_planting_id);

-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_seed_inventory_timestamp
    AFTER UPDATE ON seed_inventory
    FOR EACH ROW
BEGIN
    UPDATE seed_inventory SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_seed_treatments_timestamp
    AFTER UPDATE ON seed_treatments
    FOR EACH ROW
BEGIN
    UPDATE seed_treatments SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_planting_records_timestamp
    AFTER UPDATE ON planting_records
    FOR EACH ROW
BEGIN
    UPDATE planting_records SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_emergence_records_timestamp
    AFTER UPDATE ON emergence_records
    FOR EACH ROW
BEGIN
    UPDATE emergence_records SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Trigger to calculate days after planting
CREATE TRIGGER IF NOT EXISTS calc_days_after_planting
    BEFORE INSERT ON emergence_records
    FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NEW.days_after_planting IS NULL THEN
            julianday(NEW.check_date) - julianday(
                (SELECT planting_date FROM planting_records WHERE id = NEW.planting_record_id)
            )
        ELSE NEW.days_after_planting
    END;
END;

-- Trigger to update seed inventory when planting record is created
CREATE TRIGGER IF NOT EXISTS deduct_seed_on_planting
    AFTER INSERT ON planting_records
    FOR EACH ROW
    WHEN NEW.seed_inventory_id IS NOT NULL AND NEW.units_used IS NOT NULL
BEGIN
    UPDATE seed_inventory
    SET quantity_on_hand = quantity_on_hand - NEW.units_used,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.seed_inventory_id;
END;
