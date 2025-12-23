-- Migration 006: Cost Per Acre Tracking Module
-- Supports QuickBooks CSV/OCR imports, split allocations, and cost-per-acre reports
-- Created: December 23, 2025

-- ============================================================================
-- EXPENSE CATEGORIES (reference table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    category_group VARCHAR(50) NOT NULL,  -- inputs, operations, overhead, other
    description TEXT,
    display_order INTEGER DEFAULT 0
);

-- Seed expense categories
INSERT OR IGNORE INTO expense_categories (name, category_group, description, display_order) VALUES
-- Inputs
('seed', 'inputs', 'Seed purchases including treatment costs', 1),
('fertilizer', 'inputs', 'All fertilizer products (dry, liquid, anhydrous)', 2),
('chemical', 'inputs', 'Herbicides, insecticides, fungicides, adjuvants', 3),
('fuel', 'inputs', 'Diesel, gasoline, propane for farm operations', 4),
-- Operations
('repairs', 'operations', 'Equipment repairs and maintenance parts', 5),
('labor', 'operations', 'Hired labor, payroll, and related costs', 6),
('custom_hire', 'operations', 'Custom application, combining, trucking, etc.', 7),
-- Overhead
('land_rent', 'overhead', 'Cash rent and crop share equivalents', 8),
('crop_insurance', 'overhead', 'Crop insurance premiums', 9),
('interest', 'overhead', 'Operating loan interest', 10),
('utilities', 'overhead', 'Electricity, natural gas, water for farm use', 11),
('storage', 'overhead', 'Grain storage, drying, and handling', 12),
-- Other
('other', 'other', 'Miscellaneous farm expenses', 99);

-- ============================================================================
-- IMPORT BATCHES (track import sessions for audit/undo)
-- ============================================================================
CREATE TABLE IF NOT EXISTS import_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255),            -- Original filename
    source_type VARCHAR(20) NOT NULL,    -- csv, ocr_scan, manual
    total_records INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed, rolled_back
    error_message TEXT,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================================
-- COLUMN MAPPINGS (save user's CSV column mappings for reuse)
-- ============================================================================
CREATE TABLE IF NOT EXISTS column_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mapping_name VARCHAR(100) NOT NULL,   -- User-friendly name for this mapping
    source_type VARCHAR(50),              -- e.g., "QuickBooks Transaction Detail"
    column_config TEXT NOT NULL,          -- JSON: {"amount": "Debit", "date": "Date", ...}
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================================
-- EXPENSES (master expense records from QuickBooks)
-- ============================================================================
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core expense data
    category VARCHAR(50) NOT NULL,        -- References expense_categories.name
    vendor VARCHAR(200),
    description TEXT,
    amount DECIMAL(12, 2) NOT NULL,       -- Total expense amount
    expense_date DATE NOT NULL,
    tax_year INTEGER NOT NULL,

    -- Import source tracking
    source_type VARCHAR(20) NOT NULL,     -- csv, ocr_scan, manual
    source_reference VARCHAR(255),        -- Filename, invoice #, etc.
    import_batch_id INTEGER,              -- Links to import_batches
    quickbooks_id VARCHAR(100),           -- For deduplication (Num/Ref field)

    -- OCR-specific fields
    ocr_confidence DECIMAL(5, 2),         -- 0-100 confidence score
    ocr_needs_review BOOLEAN DEFAULT 0,   -- Flag for manual verification
    ocr_raw_text TEXT,                    -- Original extracted text

    -- Metadata
    notes TEXT,
    created_by_user_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (import_batch_id) REFERENCES import_batches(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_tax_year ON expenses(tax_year);
CREATE INDEX IF NOT EXISTS idx_expenses_vendor ON expenses(vendor);
CREATE INDEX IF NOT EXISTS idx_expenses_quickbooks_id ON expenses(quickbooks_id);
CREATE INDEX IF NOT EXISTS idx_expenses_batch ON expenses(import_batch_id);

-- ============================================================================
-- EXPENSE ALLOCATIONS (link expenses to fields with split percentages)
-- ============================================================================
CREATE TABLE IF NOT EXISTS expense_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    crop_year INTEGER NOT NULL,           -- Growing season year

    -- Allocation details
    allocation_percent DECIMAL(5, 2) NOT NULL,  -- 0.00 to 100.00
    allocated_amount DECIMAL(12, 2) NOT NULL,   -- Calculated: expense.amount * percent/100

    -- Optional details
    notes TEXT,

    -- Metadata
    created_by_user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES fields(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),

    -- Ensure unique allocation per expense-field-year combination
    UNIQUE(expense_id, field_id, crop_year)
);

-- Index for cost-per-acre queries
CREATE INDEX IF NOT EXISTS idx_allocations_field ON expense_allocations(field_id);
CREATE INDEX IF NOT EXISTS idx_allocations_crop_year ON expense_allocations(crop_year);
CREATE INDEX IF NOT EXISTS idx_allocations_expense ON expense_allocations(expense_id);

-- ============================================================================
-- VIEWS FOR REPORTING
-- ============================================================================

-- Cost per acre by field and year
CREATE VIEW IF NOT EXISTS v_cost_per_acre AS
SELECT
    ea.field_id,
    f.name AS field_name,
    f.farm_name,
    f.acreage,
    f.current_crop,
    ea.crop_year,
    e.category,
    ec.category_group,
    SUM(ea.allocated_amount) AS total_cost,
    ROUND(SUM(ea.allocated_amount) / f.acreage, 2) AS cost_per_acre
FROM expense_allocations ea
JOIN expenses e ON ea.expense_id = e.id
JOIN fields f ON ea.field_id = f.id
LEFT JOIN expense_categories ec ON e.category = ec.name
WHERE e.is_active = 1
GROUP BY ea.field_id, ea.crop_year, e.category;

-- Unallocated expenses
CREATE VIEW IF NOT EXISTS v_unallocated_expenses AS
SELECT
    e.*,
    COALESCE(SUM(ea.allocation_percent), 0) AS allocated_percent,
    100 - COALESCE(SUM(ea.allocation_percent), 0) AS unallocated_percent
FROM expenses e
LEFT JOIN expense_allocations ea ON e.id = ea.expense_id
WHERE e.is_active = 1
GROUP BY e.id
HAVING unallocated_percent > 0;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp on expense update
CREATE TRIGGER IF NOT EXISTS trg_expenses_updated
AFTER UPDATE ON expenses
BEGIN
    UPDATE expenses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamp on allocation update
CREATE TRIGGER IF NOT EXISTS trg_allocations_updated
AFTER UPDATE ON expense_allocations
BEGIN
    UPDATE expense_allocations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update timestamp on column_mappings update
CREATE TRIGGER IF NOT EXISTS trg_column_mappings_updated
AFTER UPDATE ON column_mappings
BEGIN
    UPDATE column_mappings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
