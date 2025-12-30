-- Migration 007: Livestock Management
-- AgTools v6.4.0 - Farm Operations Suite
-- Supports: Cattle, Hogs, Poultry, Sheep, Goats

-- Livestock Groups (for batch tracking - poultry flocks, hog batches)
CREATE TABLE IF NOT EXISTS livestock_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    species TEXT NOT NULL CHECK (species IN ('cattle', 'hog', 'poultry', 'sheep', 'goat')),
    head_count INTEGER DEFAULT 0,
    start_date DATE,
    source TEXT,
    cost_per_head REAL DEFAULT 0,
    barn_location TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'sold', 'processed', 'dispersed')),
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Livestock Animals (individual animal tracking)
CREATE TABLE IF NOT EXISTS livestock_animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_number TEXT,
    name TEXT,
    species TEXT NOT NULL CHECK (species IN ('cattle', 'hog', 'poultry', 'sheep', 'goat')),
    breed TEXT,
    sex TEXT CHECK (sex IN ('male', 'female', 'castrated', 'unknown')),
    birth_date DATE,
    purchase_date DATE,
    purchase_price REAL DEFAULT 0,
    sire_id INTEGER REFERENCES livestock_animals(id),
    dam_id INTEGER REFERENCES livestock_animals(id),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'sold', 'deceased', 'culled', 'transferred')),
    current_weight REAL,
    current_location TEXT,
    group_id INTEGER REFERENCES livestock_groups(id),
    registration_number TEXT,
    color_markings TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Livestock Health Records
CREATE TABLE IF NOT EXISTS livestock_health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER REFERENCES livestock_animals(id),
    group_id INTEGER REFERENCES livestock_groups(id),
    record_date DATE NOT NULL,
    record_type TEXT NOT NULL CHECK (record_type IN (
        'vaccination', 'treatment', 'vet_visit', 'injury',
        'illness', 'deworming', 'hoof_trim', 'castration',
        'pregnancy_check', 'other'
    )),
    description TEXT,
    medication TEXT,
    dosage TEXT,
    dosage_unit TEXT,
    route TEXT CHECK (route IN ('oral', 'injection', 'topical', 'pour_on', 'other')),
    administered_by TEXT,
    vet_name TEXT,
    cost REAL DEFAULT 0,
    withdrawal_days INTEGER DEFAULT 0,
    withdrawal_end_date DATE,
    next_due_date DATE,
    lot_number TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Livestock Breeding Records
CREATE TABLE IF NOT EXISTS livestock_breeding_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    female_id INTEGER NOT NULL REFERENCES livestock_animals(id),
    male_id INTEGER REFERENCES livestock_animals(id),
    semen_source TEXT,
    breeding_date DATE NOT NULL,
    breeding_method TEXT CHECK (breeding_method IN ('natural', 'ai', 'embryo_transfer')),
    technician TEXT,
    expected_due_date DATE,
    actual_birth_date DATE,
    offspring_count INTEGER DEFAULT 0,
    live_births INTEGER DEFAULT 0,
    stillbirths INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'open', 'aborted', 'completed')),
    gestation_days INTEGER,
    calving_ease INTEGER CHECK (calving_ease BETWEEN 1 AND 5),
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Livestock Weights
CREATE TABLE IF NOT EXISTS livestock_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER REFERENCES livestock_animals(id),
    group_id INTEGER REFERENCES livestock_groups(id),
    weight_date DATE NOT NULL,
    weight_lbs REAL NOT NULL,
    avg_weight REAL,
    sample_size INTEGER,
    weight_type TEXT CHECK (weight_type IN ('birth', 'weaning', 'yearling', 'sale', 'routine', 'other')),
    adg REAL,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Livestock Sales
CREATE TABLE IF NOT EXISTS livestock_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER REFERENCES livestock_animals(id),
    group_id INTEGER REFERENCES livestock_groups(id),
    sale_date DATE NOT NULL,
    buyer_name TEXT,
    buyer_contact TEXT,
    head_count INTEGER DEFAULT 1,
    sale_weight REAL,
    price_per_lb REAL,
    sale_price REAL NOT NULL,
    sale_type TEXT CHECK (sale_type IN ('auction', 'private', 'contract', 'cull', 'breeding_stock')),
    market_name TEXT,
    commission REAL DEFAULT 0,
    trucking_cost REAL DEFAULT 0,
    net_proceeds REAL,
    check_number TEXT,
    payment_received INTEGER DEFAULT 0,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Livestock Feed Records (optional tracking)
CREATE TABLE IF NOT EXISTS livestock_feed_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER REFERENCES livestock_groups(id),
    animal_id INTEGER REFERENCES livestock_animals(id),
    feed_date DATE NOT NULL,
    feed_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    quantity_unit TEXT DEFAULT 'lbs',
    cost_per_unit REAL DEFAULT 0,
    total_cost REAL DEFAULT 0,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_livestock_animals_species ON livestock_animals(species);
CREATE INDEX IF NOT EXISTS idx_livestock_animals_status ON livestock_animals(status);
CREATE INDEX IF NOT EXISTS idx_livestock_animals_tag ON livestock_animals(tag_number);
CREATE INDEX IF NOT EXISTS idx_livestock_animals_group ON livestock_animals(group_id);
CREATE INDEX IF NOT EXISTS idx_livestock_animals_sire ON livestock_animals(sire_id);
CREATE INDEX IF NOT EXISTS idx_livestock_animals_dam ON livestock_animals(dam_id);

CREATE INDEX IF NOT EXISTS idx_livestock_groups_species ON livestock_groups(species);
CREATE INDEX IF NOT EXISTS idx_livestock_groups_status ON livestock_groups(status);

CREATE INDEX IF NOT EXISTS idx_livestock_health_animal ON livestock_health_records(animal_id);
CREATE INDEX IF NOT EXISTS idx_livestock_health_group ON livestock_health_records(group_id);
CREATE INDEX IF NOT EXISTS idx_livestock_health_date ON livestock_health_records(record_date);
CREATE INDEX IF NOT EXISTS idx_livestock_health_type ON livestock_health_records(record_type);
CREATE INDEX IF NOT EXISTS idx_livestock_health_next_due ON livestock_health_records(next_due_date);

CREATE INDEX IF NOT EXISTS idx_livestock_breeding_female ON livestock_breeding_records(female_id);
CREATE INDEX IF NOT EXISTS idx_livestock_breeding_male ON livestock_breeding_records(male_id);
CREATE INDEX IF NOT EXISTS idx_livestock_breeding_date ON livestock_breeding_records(breeding_date);
CREATE INDEX IF NOT EXISTS idx_livestock_breeding_due ON livestock_breeding_records(expected_due_date);
CREATE INDEX IF NOT EXISTS idx_livestock_breeding_status ON livestock_breeding_records(status);

CREATE INDEX IF NOT EXISTS idx_livestock_weights_animal ON livestock_weights(animal_id);
CREATE INDEX IF NOT EXISTS idx_livestock_weights_group ON livestock_weights(group_id);
CREATE INDEX IF NOT EXISTS idx_livestock_weights_date ON livestock_weights(weight_date);

CREATE INDEX IF NOT EXISTS idx_livestock_sales_animal ON livestock_sales(animal_id);
CREATE INDEX IF NOT EXISTS idx_livestock_sales_group ON livestock_sales(group_id);
CREATE INDEX IF NOT EXISTS idx_livestock_sales_date ON livestock_sales(sale_date);

CREATE INDEX IF NOT EXISTS idx_livestock_feed_group ON livestock_feed_records(group_id);
CREATE INDEX IF NOT EXISTS idx_livestock_feed_date ON livestock_feed_records(feed_date);

-- Triggers for updated_at
CREATE TRIGGER IF NOT EXISTS update_livestock_animals_timestamp
    AFTER UPDATE ON livestock_animals
    FOR EACH ROW
BEGIN
    UPDATE livestock_animals SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_livestock_groups_timestamp
    AFTER UPDATE ON livestock_groups
    FOR EACH ROW
BEGIN
    UPDATE livestock_groups SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_livestock_health_timestamp
    AFTER UPDATE ON livestock_health_records
    FOR EACH ROW
BEGIN
    UPDATE livestock_health_records SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_livestock_breeding_timestamp
    AFTER UPDATE ON livestock_breeding_records
    FOR EACH ROW
BEGIN
    UPDATE livestock_breeding_records SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_livestock_weights_timestamp
    AFTER UPDATE ON livestock_weights
    FOR EACH ROW
BEGIN
    UPDATE livestock_weights SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_livestock_sales_timestamp
    AFTER UPDATE ON livestock_sales
    FOR EACH ROW
BEGIN
    UPDATE livestock_sales SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_livestock_feed_timestamp
    AFTER UPDATE ON livestock_feed_records
    FOR EACH ROW
BEGIN
    UPDATE livestock_feed_records SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Update animal weight when new weight is recorded
CREATE TRIGGER IF NOT EXISTS update_animal_weight_on_insert
    AFTER INSERT ON livestock_weights
    FOR EACH ROW
    WHEN NEW.animal_id IS NOT NULL
BEGIN
    UPDATE livestock_animals
    SET current_weight = NEW.weight_lbs, updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.animal_id;
END;

-- Mark animal as sold when sale is recorded
CREATE TRIGGER IF NOT EXISTS update_animal_status_on_sale
    AFTER INSERT ON livestock_sales
    FOR EACH ROW
    WHEN NEW.animal_id IS NOT NULL
BEGIN
    UPDATE livestock_animals
    SET status = 'sold', updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.animal_id;
END;
