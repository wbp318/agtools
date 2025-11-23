-- Professional Crop Consulting System Database Schema
-- Designed for corn and soybean pest/disease management and spray recommendations

-- ============================================================================
-- PEST AND DISEASE MANAGEMENT
-- ============================================================================

CREATE TABLE crops (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(200),
    category VARCHAR(50), -- 'row_crop', 'specialty', 'small_grain'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE growth_stages (
    id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(id),
    stage_code VARCHAR(10), -- 'VE', 'V3', 'V6', 'VT', 'R1', 'R3', etc.
    stage_name VARCHAR(100),
    description TEXT,
    typical_days_from_planting INTEGER,
    key_management_activities TEXT
);

CREATE TABLE pests (
    id SERIAL PRIMARY KEY,
    common_name VARCHAR(200) NOT NULL,
    scientific_name VARCHAR(200),
    pest_type VARCHAR(50), -- 'insect', 'mite', 'nematode', 'vertebrate'
    description TEXT,
    lifecycle TEXT,
    identification_features TEXT,
    damage_symptoms TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE diseases (
    id SERIAL PRIMARY KEY,
    common_name VARCHAR(200) NOT NULL,
    scientific_name VARCHAR(200),
    pathogen_type VARCHAR(50), -- 'fungal', 'bacterial', 'viral', 'nematode'
    description TEXT,
    symptoms TEXT,
    favorable_conditions TEXT,
    lifecycle TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pest_crop_association (
    id SERIAL PRIMARY KEY,
    pest_id INTEGER REFERENCES pests(id),
    crop_id INTEGER REFERENCES crops(id),
    severity_rating INTEGER, -- 1-10 scale
    common_in_region VARCHAR(100),
    typical_timing VARCHAR(100), -- 'early season', 'mid season', 'late season'
    vulnerable_growth_stages TEXT -- comma-separated stage codes
);

CREATE TABLE disease_crop_association (
    id SERIAL PRIMARY KEY,
    disease_id INTEGER REFERENCES diseases(id),
    crop_id INTEGER REFERENCES crops(id),
    severity_rating INTEGER,
    common_in_region VARCHAR(100),
    typical_timing VARCHAR(100),
    vulnerable_growth_stages TEXT
);

CREATE TABLE pest_images (
    id SERIAL PRIMARY KEY,
    pest_id INTEGER REFERENCES pests(id),
    image_url VARCHAR(500),
    image_type VARCHAR(50), -- 'adult', 'larva', 'egg', 'damage', 'field_sign'
    description TEXT,
    source VARCHAR(200),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE disease_images (
    id SERIAL PRIMARY KEY,
    disease_id INTEGER REFERENCES diseases(id),
    image_url VARCHAR(500),
    image_type VARCHAR(50), -- 'leaf_symptom', 'stalk', 'root', 'ear', 'field_overview'
    description TEXT,
    growth_stage VARCHAR(20),
    source VARCHAR(200),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ECONOMIC THRESHOLDS AND SCOUTING
-- ============================================================================

CREATE TABLE economic_thresholds (
    id SERIAL PRIMARY KEY,
    pest_id INTEGER REFERENCES pests(id),
    crop_id INTEGER REFERENCES crops(id),
    growth_stage VARCHAR(20),
    threshold_value DECIMAL(10, 2),
    threshold_unit VARCHAR(50), -- 'per plant', 'per square foot', '% defoliation', etc.
    threshold_description TEXT,
    cost_of_control DECIMAL(10, 2),
    yield_loss_per_unit DECIMAL(10, 2), -- bushels lost per threshold unit
    source VARCHAR(200), -- extension publication reference
    region VARCHAR(100)
);

-- ============================================================================
-- CHEMICAL DATABASE
-- ============================================================================

CREATE TABLE active_ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    chemical_family VARCHAR(100), -- 'pyrethroid', 'neonicotinoid', 'organophosphate', etc.
    mode_of_action VARCHAR(100), -- IRAC or FRAC code
    resistance_group VARCHAR(20), -- For resistance management
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    trade_name VARCHAR(200) NOT NULL,
    manufacturer VARCHAR(200),
    product_type VARCHAR(50), -- 'insecticide', 'fungicide', 'herbicide', 'adjuvant'
    formulation VARCHAR(100), -- 'EC', 'WDG', 'SC', etc.
    epa_reg_number VARCHAR(50),
    active_ingredient_id INTEGER REFERENCES active_ingredients(id),
    concentration VARCHAR(50), -- '2.5 lb ai/gal', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_labels (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    crop_id INTEGER REFERENCES crops(id),
    target_pest_id INTEGER REFERENCES pests(id) NULL,
    target_disease_id INTEGER REFERENCES diseases(id) NULL,
    min_rate DECIMAL(10, 4),
    max_rate DECIMAL(10, 4),
    rate_unit VARCHAR(50), -- 'oz/acre', 'fl oz/acre', 'lb/acre'
    application_timing TEXT,
    phi_days INTEGER, -- Pre-harvest interval
    rei_hours INTEGER, -- Re-entry interval
    max_applications_per_season INTEGER,
    max_rate_per_season DECIMAL(10, 4),
    special_restrictions TEXT,
    adjuvant_recommendations TEXT
);

CREATE TABLE tank_mix_compatibility (
    id SERIAL PRIMARY KEY,
    product_a_id INTEGER REFERENCES products(id),
    product_b_id INTEGER REFERENCES products(id),
    compatibility VARCHAR(20), -- 'compatible', 'incompatible', 'caution', 'unknown'
    notes TEXT,
    tested_date DATE,
    source VARCHAR(200)
);

-- ============================================================================
-- SPRAY RECOMMENDATIONS AND DECISIONS
-- ============================================================================

CREATE TABLE spray_recommendations (
    id SERIAL PRIMARY KEY,
    recommendation_date DATE NOT NULL,
    field_id INTEGER, -- Will reference fields table when we add field management
    crop_id INTEGER REFERENCES crops(id),
    growth_stage VARCHAR(20),
    problem_type VARCHAR(20), -- 'pest', 'disease', 'weed'
    problem_id INTEGER, -- pest_id or disease_id
    severity_level INTEGER, -- 1-10
    threshold_exceeded BOOLEAN,
    recommended_action VARCHAR(50), -- 'spray', 'scout_again', 'no_action'
    recommended_product_id INTEGER REFERENCES products(id),
    application_rate DECIMAL(10, 4),
    rate_unit VARCHAR(50),
    application_volume VARCHAR(50), -- gallons per acre
    adjuvants TEXT,
    timing_notes TEXT,
    cost_per_acre DECIMAL(10, 2),
    expected_efficacy INTEGER, -- percentage
    resistance_management_notes TEXT,
    weather_considerations TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- IDENTIFICATION SYSTEM (AI + Guided)
-- ============================================================================

CREATE TABLE identification_sessions (
    id SERIAL PRIMARY KEY,
    session_uuid VARCHAR(100) UNIQUE NOT NULL,
    crop_id INTEGER REFERENCES crops(id),
    growth_stage VARCHAR(20),
    identification_type VARCHAR(20), -- 'pest', 'disease', 'nutrient_deficiency'
    method VARCHAR(20), -- 'image_ai', 'guided', 'manual'
    image_path VARCHAR(500),
    field_location_lat DECIMAL(10, 8),
    field_location_lon DECIMAL(11, 8),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE identification_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES identification_sessions(id),
    pest_id INTEGER REFERENCES pests(id) NULL,
    disease_id INTEGER REFERENCES diseases(id) NULL,
    confidence_score DECIMAL(5, 4), -- 0.0 to 1.0
    identification_method VARCHAR(50), -- 'ai_model', 'guided_questions', 'user_selected'
    notes TEXT,
    verified_by_expert BOOLEAN DEFAULT FALSE
);

CREATE TABLE guided_questions (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    question_category VARCHAR(50), -- 'location', 'timing', 'symptoms', 'environment'
    applicable_to VARCHAR(20), -- 'pest', 'disease', 'both'
    order_sequence INTEGER
);

CREATE TABLE guided_answers (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES guided_questions(id),
    answer_text TEXT NOT NULL,
    narrows_to_pest_ids TEXT, -- comma-separated pest IDs
    narrows_to_disease_ids TEXT -- comma-separated disease IDs
);

-- ============================================================================
-- USER AND FIELD MANAGEMENT (Basic structure for future expansion)
-- ============================================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200),
    role VARCHAR(50), -- 'grower', 'consultant', 'advisor', 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fields (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    field_name VARCHAR(200) NOT NULL,
    farm_name VARCHAR(200),
    acres DECIMAL(10, 2),
    soil_type VARCHAR(100),
    geojson_boundary TEXT, -- GeoJSON polygon for field boundary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scouting_reports (
    id SERIAL PRIMARY KEY,
    field_id INTEGER REFERENCES fields(id),
    scout_date DATE NOT NULL,
    crop_id INTEGER REFERENCES crops(id),
    growth_stage VARCHAR(20),
    weather_conditions TEXT,
    observations TEXT,
    images TEXT, -- JSON array of image paths
    location_lat DECIMAL(10, 8),
    location_lon DECIMAL(11, 8),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_pests_common_name ON pests(common_name);
CREATE INDEX idx_diseases_common_name ON diseases(common_name);
CREATE INDEX idx_products_trade_name ON products(trade_name);
CREATE INDEX idx_identification_sessions_uuid ON identification_sessions(session_uuid);
CREATE INDEX idx_spray_recommendations_date ON spray_recommendations(recommendation_date);
CREATE INDEX idx_scouting_reports_date ON scouting_reports(scout_date);
CREATE INDEX idx_scouting_reports_field ON scouting_reports(field_id);
