# Farm Operations Manager - Development Plan

> **Version:** 2.5.0
> **Status:** 🔄 IN PROGRESS - Phase 1
> **Started:** December 11, 2025
> **Last Updated:** December 11, 2025

---

## Overview

A comprehensive farm operations management system combining irrigation scheduling optimization with multi-user task/project management, fully integrated with AgTools' existing crop consulting features.

### Business Value
- **Labor optimization** - Track and optimize crew hours across multiple projects
- **Irrigation efficiency** - ET-based scheduling, weather-aware, cost tracking
- **Energy cost preparation** - Baseline tracking before regional rate increases (Meta data center impact)
- **Integrated workflows** - Pest/disease IDs auto-generate spray tasks
- **Multi-user support** - Crew members view assignments, managers track progress

---

## Phase Summary

| Phase | Description | Status | Est. Effort |
|-------|-------------|--------|-------------|
| Phase 1 | User & Auth System | 🔄 IN PROGRESS | 6-8 hours |
| Phase 2 | Task Management Core | ⏳ Pending | 8-10 hours |
| Phase 3 | Field & Equipment Resources | ⏳ Pending | 6-8 hours |
| Phase 4 | Irrigation Scheduler | ⏳ Pending | 8-10 hours |
| Phase 5 | AgTools Integration | ⏳ Pending | 4-6 hours |
| Phase 6 | Mobile/Crew Interface | ⏳ Pending | 6-8 hours |

---

## Phase 1: User & Auth System

**Goal:** Establish multi-user authentication with role-based access control.

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL DEFAULT 'crew',  -- admin, manager, crew
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Sessions table (for token management)
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Crews/Teams table (optional grouping)
CREATE TABLE crews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- Crew membership
CREATE TABLE crew_members (
    crew_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (crew_id, user_id),
    FOREIGN KEY (crew_id) REFERENCES crews(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Roles & Permissions

| Permission | Admin | Manager | Crew |
|------------|-------|---------|------|
| View own tasks | ✅ | ✅ | ✅ |
| Update task status | ✅ | ✅ | ✅ |
| Create tasks | ✅ | ✅ | ❌ |
| Assign tasks to others | ✅ | ✅ | ❌ |
| View all crew tasks | ✅ | ✅ | ❌ |
| Manage projects | ✅ | ✅ | ❌ |
| Manage users | ✅ | ❌ | ❌ |
| Manage crews | ✅ | ❌ | ❌ |
| System settings | ✅ | ❌ | ❌ |
| View reports | ✅ | ✅ | ❌ |

### API Endpoints

```
POST   /api/v1/auth/register        - Register new user (admin only)
POST   /api/v1/auth/login           - Login, returns JWT token
POST   /api/v1/auth/logout          - Invalidate session
POST   /api/v1/auth/refresh         - Refresh JWT token
GET    /api/v1/auth/me              - Get current user info
PUT    /api/v1/auth/me              - Update own profile
POST   /api/v1/auth/change-password - Change own password

GET    /api/v1/users                - List all users (admin/manager)
GET    /api/v1/users/{id}           - Get user details
PUT    /api/v1/users/{id}           - Update user (admin)
DELETE /api/v1/users/{id}           - Deactivate user (admin)

GET    /api/v1/crews                - List crews
POST   /api/v1/crews                - Create crew (admin)
PUT    /api/v1/crews/{id}           - Update crew
POST   /api/v1/crews/{id}/members   - Add member to crew
DELETE /api/v1/crews/{id}/members/{user_id} - Remove member
```

### Backend Implementation

**New Files:**
- `backend/services/auth_service.py` - Authentication logic, JWT handling
- `backend/services/user_service.py` - User CRUD operations
- `backend/middleware/auth_middleware.py` - JWT validation middleware
- `backend/models/user.py` - Pydantic models for users

**Dependencies to Add:**
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data parsing

### Frontend Implementation

**New Screens:**
- `frontend/ui/screens/login.py` - Login screen
- `frontend/ui/screens/user_management.py` - Admin user management
- `frontend/ui/screens/crew_management.py` - Crew/team management

**Modified Files:**
- `frontend/config.py` - Store auth token
- `frontend/api/client.py` - Add auth headers to requests
- `frontend/ui/main_window.py` - Add login flow, user menu

### Security Considerations
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with 24-hour expiration
- Refresh tokens with 7-day expiration
- Rate limiting on login attempts
- Session invalidation on password change

### Deliverables Checklist
- [ ] Database schema migration
- [ ] Auth service with JWT
- [ ] User service with CRUD
- [ ] Auth middleware
- [ ] API endpoints (auth, users, crews)
- [ ] Login screen (frontend)
- [ ] User management screen
- [ ] Crew management screen
- [ ] Auth integration in API client
- [ ] Protected route handling

---

## Phase 2: Task Management Core

**Goal:** Create the core task and project management system.

### Database Schema (Preview)

```sql
-- Projects (grouping of related tasks)
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, archived
    start_date DATE,
    target_end_date DATE,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Tasks
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    task_type VARCHAR(50),  -- scouting, spraying, irrigation, planting, harvest, equipment, general
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, cancelled
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    assigned_to INTEGER,
    field_id INTEGER,  -- optional link to field
    equipment_id INTEGER,  -- optional equipment needed
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Task dependencies
CREATE TABLE task_dependencies (
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    PRIMARY KEY (task_id, depends_on_task_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Task comments/notes
CREATE TABLE task_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Time entries (labor tracking)
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    hours DECIMAL(5,2) NOT NULL,
    work_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Features (Preview)
- Project creation and management
- Task CRUD with assignments
- Task dependencies (Gantt-style)
- Status workflow (pending → in_progress → completed)
- Time tracking per task
- Comments/notes on tasks
- Due date tracking and overdue alerts
- Priority levels
- Filtering and search

---

## Phase 3: Field & Equipment Resources

**Goal:** Link tasks to physical resources (fields, equipment) for scheduling.

### Features (Preview)
- Field registry with boundaries
- Equipment inventory
- Equipment availability calendar
- Resource conflict detection
- Maintenance scheduling for equipment

---

## Phase 4: Irrigation Scheduler

**Goal:** Optimize irrigation scheduling for water and energy efficiency.

### Features (Preview)
- ET-based water demand calculation per field
- Weather forecast integration (skip before rain)
- Pump runtime scheduling
- Energy usage tracking (kWh per field)
- Cost tracking and reporting
- Historical comparison
- Auto-generate irrigation tasks

### Energy Tracking (Entergy Louisiana context)
- Track kWh usage per irrigation run
- Monthly/seasonal cost reports
- Baseline establishment for future rate comparisons
- Efficiency metrics (kWh per acre-inch)

---

## Phase 5: AgTools Integration

**Goal:** Connect existing AgTools features to task generation.

### Integration Points
- **Pest ID** → Generate "Scout for [pest]" or "Spray for [pest]" task
- **Disease ID** → Generate treatment task with product recommendations
- **Spray Timing** → Schedule spray task for optimal weather window
- **Scouting** → Regular scouting tasks auto-generated
- **Cost Optimizer** → Link task costs to budget tracking

---

## Phase 6: Mobile/Crew Interface

**Goal:** Simple, mobile-friendly interface for field crews.

### Features (Preview)
- Responsive web view (works on phones)
- Simple task list view
- One-tap status updates
- Time logging
- Photo attachment for tasks
- Offline capability with sync

---

## Technical Notes

### Stack
- **Backend:** FastAPI (existing) + SQLite/PostgreSQL
- **Auth:** JWT tokens with python-jose
- **Frontend:** PyQt6 (desktop) + potential web interface
- **Mobile:** Responsive web initially, native app later if needed

### Migration Path
- SQLite for development/single-user
- PostgreSQL for production/multi-user SaaS

---

## Changelog

### December 11, 2025
- Initial plan created
- Phase 1 detailed design complete
- Phases 2-6 outlined

