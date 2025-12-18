-- Migration 004: Equipment & Inventory Tracking
-- Created: December 17, 2025
-- AgTools v2.5.0 Phase 4

-- ============================================================================
-- EQUIPMENT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,      -- tractor, combine, sprayer, planter, tillage, truck, atv, grain_cart, other

    -- Identification
    make VARCHAR(100),                        -- John Deere, Case IH, etc.
    model VARCHAR(100),
    year INTEGER,
    serial_number VARCHAR(100),

    -- Acquisition
    purchase_date DATE,
    purchase_cost DECIMAL(12, 2),
    current_value DECIMAL(12, 2),             -- For depreciation tracking

    -- Operating costs
    hourly_rate DECIMAL(8, 2),                -- $/hour operating cost

    -- Usage tracking
    current_hours DECIMAL(10, 1) DEFAULT 0,   -- Current hour meter reading

    -- Status
    status VARCHAR(20) DEFAULT 'available',   -- available, in_use, maintenance, retired
    current_location VARCHAR(100),            -- Where is it parked/stored

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
-- EQUIPMENT MAINTENANCE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS equipment_maintenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,

    -- Maintenance details
    maintenance_type VARCHAR(50) NOT NULL,    -- oil_change, filter, repairs, inspection, tires, winterization, other
    service_date DATE NOT NULL,

    -- Scheduling
    next_service_date DATE,                   -- When is next service due (by date)
    next_service_hours DECIMAL(10, 1),        -- When is next service due (by hours)

    -- Cost tracking
    cost DECIMAL(10, 2),

    -- Who performed
    performed_by VARCHAR(100),                -- Technician name or "Self"
    vendor VARCHAR(100),                      -- Dealership, shop name

    -- Details
    description TEXT,
    parts_used TEXT,                          -- JSON or comma-separated list

    -- Ownership
    created_by_user_id INTEGER NOT NULL,

    -- Soft delete
    is_active BOOLEAN DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ============================================================================
-- EQUIPMENT USAGE TABLE (Links equipment to field operations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS equipment_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    field_operation_id INTEGER,               -- Link to field operation if applicable

    -- Usage details
    usage_date DATE NOT NULL,
    hours_used DECIMAL(8, 1),                 -- Hours used this session
    starting_hours DECIMAL(10, 1),            -- Meter at start
    ending_hours DECIMAL(10, 1),              -- Meter at end

    -- Fuel tracking
    fuel_used DECIMAL(8, 2),
    fuel_unit VARCHAR(20) DEFAULT 'gallons',  -- gallons, liters

    -- Who operated
    operator_id INTEGER,

    -- Additional info
    notes TEXT,

    -- Ownership
    created_by_user_id INTEGER NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (field_operation_id) REFERENCES field_operations(id),
    FOREIGN KEY (operator_id) REFERENCES users(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ============================================================================
-- INVENTORY ITEMS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,            -- seed, fertilizer, herbicide, fungicide, insecticide, fuel, parts, supplies

    -- Product identification
    manufacturer VARCHAR(100),
    product_code VARCHAR(100),                -- EPA number, SKU, etc.
    sku VARCHAR(50),

    -- Quantity tracking
    quantity DECIMAL(12, 3) NOT NULL DEFAULT 0,
    unit VARCHAR(50) NOT NULL,                -- gallons, pounds, bags, cases, each, etc.
    min_quantity DECIMAL(12, 3),              -- Reorder point (alert when below)

    -- Storage
    storage_location VARCHAR(100),            -- "Chemical Shed", "Bin 3", etc.
    batch_number VARCHAR(100),                -- Lot number for traceability
    expiration_date DATE,                     -- Important for chemicals

    -- Cost tracking
    unit_cost DECIMAL(10, 3),                 -- Cost per unit
    total_value DECIMAL(12, 2),               -- Computed: quantity * unit_cost

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
-- INVENTORY TRANSACTIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_item_id INTEGER NOT NULL,

    -- Transaction details
    transaction_type VARCHAR(50) NOT NULL,    -- purchase, usage, adjustment, transfer, return
    quantity DECIMAL(12, 3) NOT NULL,         -- Positive for additions, negative for deductions

    -- Cost tracking
    unit_cost DECIMAL(10, 3),
    total_cost DECIMAL(12, 2),

    -- Reference (what caused this transaction)
    reference_type VARCHAR(50),               -- field_operation, manual, purchase_order, etc.
    reference_id INTEGER,                     -- ID of the referenced record

    -- Vendor info (for purchases)
    vendor VARCHAR(100),
    invoice_number VARCHAR(100),

    -- Additional info
    notes TEXT,

    -- Ownership
    created_by_user_id INTEGER NOT NULL,

    -- Timestamp (no update - transactions are immutable)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ============================================================================
-- MODIFY FIELD_OPERATIONS TABLE
-- Add equipment_id column for linking operations to equipment
-- ============================================================================

-- Add equipment_id to field_operations (SQLite requires recreating table for ALTER TABLE ADD FOREIGN KEY)
-- For simplicity, we add the column without enforcing FK at DB level (enforced in app layer)
ALTER TABLE field_operations ADD COLUMN equipment_id INTEGER;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Equipment indexes
CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_make ON equipment(make);
CREATE INDEX IF NOT EXISTS idx_equipment_created_by ON equipment(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_equipment_active ON equipment(is_active);

-- Equipment maintenance indexes
CREATE INDEX IF NOT EXISTS idx_maint_equipment ON equipment_maintenance(equipment_id);
CREATE INDEX IF NOT EXISTS idx_maint_type ON equipment_maintenance(maintenance_type);
CREATE INDEX IF NOT EXISTS idx_maint_date ON equipment_maintenance(service_date);
CREATE INDEX IF NOT EXISTS idx_maint_next_date ON equipment_maintenance(next_service_date);
CREATE INDEX IF NOT EXISTS idx_maint_active ON equipment_maintenance(is_active);

-- Equipment usage indexes
CREATE INDEX IF NOT EXISTS idx_usage_equipment ON equipment_usage(equipment_id);
CREATE INDEX IF NOT EXISTS idx_usage_operation ON equipment_usage(field_operation_id);
CREATE INDEX IF NOT EXISTS idx_usage_date ON equipment_usage(usage_date);
CREATE INDEX IF NOT EXISTS idx_usage_operator ON equipment_usage(operator_id);

-- Inventory items indexes
CREATE INDEX IF NOT EXISTS idx_inv_name ON inventory_items(name);
CREATE INDEX IF NOT EXISTS idx_inv_category ON inventory_items(category);
CREATE INDEX IF NOT EXISTS idx_inv_manufacturer ON inventory_items(manufacturer);
CREATE INDEX IF NOT EXISTS idx_inv_product_code ON inventory_items(product_code);
CREATE INDEX IF NOT EXISTS idx_inv_location ON inventory_items(storage_location);
CREATE INDEX IF NOT EXISTS idx_inv_expiration ON inventory_items(expiration_date);
CREATE INDEX IF NOT EXISTS idx_inv_created_by ON inventory_items(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_inv_active ON inventory_items(is_active);

-- Inventory transactions indexes
CREATE INDEX IF NOT EXISTS idx_trans_item ON inventory_transactions(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_trans_type ON inventory_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_trans_ref_type ON inventory_transactions(reference_type);
CREATE INDEX IF NOT EXISTS idx_trans_ref_id ON inventory_transactions(reference_id);
CREATE INDEX IF NOT EXISTS idx_trans_date ON inventory_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_trans_created_by ON inventory_transactions(created_by_user_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_inv_category_active ON inventory_items(category, is_active);
CREATE INDEX IF NOT EXISTS idx_maint_equip_date ON equipment_maintenance(equipment_id, service_date);
CREATE INDEX IF NOT EXISTS idx_usage_equip_date ON equipment_usage(equipment_id, usage_date);

-- Index on new field_operations column
CREATE INDEX IF NOT EXISTS idx_field_ops_equipment ON field_operations(equipment_id);
