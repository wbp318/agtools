-- Migration 003: Field Management & Operations Logging
-- Created: December 15, 2025
-- AgTools v2.5.0 Phase 3

-- ============================================================================
-- FIELDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    farm_name VARCHAR(100),                   -- Optional grouping (e.g., "North Farm", "Smith Place")
    acreage DECIMAL(10, 2) NOT NULL,
    current_crop VARCHAR(50),                 -- corn, soybean, wheat, etc.
    soil_type VARCHAR(50),                    -- clay, loam, sandy, etc.
    irrigation_type VARCHAR(50),              -- none, center_pivot, drip, etc.

    -- Location (simple lat/lng center point)
    location_lat DECIMAL(10, 7),
    location_lng DECIMAL(10, 7),

    -- Boundary (GeoJSON polygon - stored as text)
    boundary TEXT,

    -- Additional info
    notes TEXT,

    -- Ownership
    created_by_user_id INTEGER NOT NULL,

    -- Soft delete
    is_active BOOLEAN DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ============================================================================
-- FIELD OPERATIONS TABLE (Activity Log)
-- ============================================================================

CREATE TABLE IF NOT EXISTS field_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_id INTEGER NOT NULL,

    -- Operation details
    operation_type VARCHAR(50) NOT NULL,      -- spray, fertilizer, planting, harvest, tillage, scouting, irrigation, other
    operation_date DATE NOT NULL,

    -- Product/Material info (optional depending on operation type)
    product_name VARCHAR(200),
    rate DECIMAL(10, 3),
    rate_unit VARCHAR(50),                    -- oz/acre, lb/acre, gal/acre, seeds/acre, etc.
    quantity DECIMAL(10, 3),
    quantity_unit VARCHAR(50),                -- gallons, pounds, tons, bushels, etc.

    -- Area covered (defaults to field acreage if not specified)
    acres_covered DECIMAL(10, 2),

    -- Cost tracking
    product_cost DECIMAL(10, 2),
    application_cost DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),

    -- Harvest-specific fields
    yield_amount DECIMAL(10, 2),
    yield_unit VARCHAR(20),                   -- bu/acre, tons/acre
    moisture_percent DECIMAL(5, 2),

    -- Weather at time of operation
    weather_temp DECIMAL(5, 1),               -- Temperature in F
    weather_wind DECIMAL(5, 1),               -- Wind speed in mph
    weather_humidity DECIMAL(5, 1),           -- Humidity %
    weather_notes TEXT,

    -- Links
    operator_id INTEGER,                      -- Who performed the operation
    task_id INTEGER,                          -- Link to task if this operation was from a task

    -- Additional notes
    notes TEXT,

    -- Ownership
    created_by_user_id INTEGER NOT NULL,

    -- Soft delete
    is_active BOOLEAN DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (field_id) REFERENCES fields(id),
    FOREIGN KEY (operator_id) REFERENCES users(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Fields indexes
CREATE INDEX IF NOT EXISTS idx_fields_name ON fields(name);
CREATE INDEX IF NOT EXISTS idx_fields_farm ON fields(farm_name);
CREATE INDEX IF NOT EXISTS idx_fields_crop ON fields(current_crop);
CREATE INDEX IF NOT EXISTS idx_fields_created_by ON fields(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_fields_active ON fields(is_active);

-- Field operations indexes
CREATE INDEX IF NOT EXISTS idx_field_ops_field_id ON field_operations(field_id);
CREATE INDEX IF NOT EXISTS idx_field_ops_type ON field_operations(operation_type);
CREATE INDEX IF NOT EXISTS idx_field_ops_date ON field_operations(operation_date);
CREATE INDEX IF NOT EXISTS idx_field_ops_operator ON field_operations(operator_id);
CREATE INDEX IF NOT EXISTS idx_field_ops_task ON field_operations(task_id);
CREATE INDEX IF NOT EXISTS idx_field_ops_created_by ON field_operations(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_field_ops_active ON field_operations(is_active);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_field_ops_field_date ON field_operations(field_id, operation_date);
CREATE INDEX IF NOT EXISTS idx_field_ops_field_type ON field_operations(field_id, operation_type);
