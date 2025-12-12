-- Migration 002: Task Management System
-- Created: December 12, 2025
-- AgTools v2.5.0 Phase 2

-- ============================================================================
-- TASKS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'todo',      -- todo, in_progress, completed, cancelled
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',  -- low, medium, high, urgent

    -- Assignment (can be assigned to user, crew, or both)
    assigned_to_user_id INTEGER,
    assigned_to_crew_id INTEGER,
    created_by_user_id INTEGER NOT NULL,

    -- Dates
    due_date DATE,
    completed_at TIMESTAMP,

    -- Soft delete
    is_active BOOLEAN DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (assigned_to_user_id) REFERENCES users(id),
    FOREIGN KEY (assigned_to_crew_id) REFERENCES crews(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_user ON tasks(assigned_to_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_crew ON tasks(assigned_to_crew_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_active ON tasks(is_active);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
