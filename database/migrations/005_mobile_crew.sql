-- Migration 005: Mobile/Crew Interface
-- Time entries and task photos for crew mobile interface
-- AgTools v2.6.0 Phase 6
-- Created: December 19, 2025

-- ============================================================================
-- TIME ENTRIES TABLE
-- Tracks hours worked on tasks by crew members
-- ============================================================================

CREATE TABLE IF NOT EXISTS time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    hours DECIMAL(5, 2) NOT NULL,
    work_date DATE NOT NULL,
    start_time TIME,                    -- Optional: when they started
    end_time TIME,                      -- Optional: when they ended
    notes TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================================
-- TASK PHOTOS TABLE
-- Stores photo attachments for tasks (field conditions, issues, progress)
-- ============================================================================

CREATE TABLE IF NOT EXISTS task_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,     -- Original filename
    stored_path VARCHAR(500) NOT NULL,  -- Path in uploads directory
    file_size INTEGER,                  -- Size in bytes
    mime_type VARCHAR(100),             -- image/jpeg, image/png, etc.
    caption TEXT,                       -- Optional description

    -- GPS location if available from device
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries(task_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_user ON time_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(work_date);
CREATE INDEX IF NOT EXISTS idx_time_entries_task_user ON time_entries(task_id, user_id);

CREATE INDEX IF NOT EXISTS idx_task_photos_task ON task_photos(task_id);
CREATE INDEX IF NOT EXISTS idx_task_photos_user ON task_photos(user_id);

-- ============================================================================
-- ADD TOTAL HOURS TO TASKS TABLE (computed field cache)
-- ============================================================================

-- Note: We'll calculate total_hours dynamically from time_entries
-- This avoids sync issues and keeps the data normalized

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Uncomment to insert test data:
-- INSERT INTO time_entries (task_id, user_id, hours, work_date, notes)
-- VALUES (1, 2, 2.5, '2025-12-19', 'Sprayed north section');
