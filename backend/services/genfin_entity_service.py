"""
GenFin Multi-Entity Service
Manage multiple businesses/farms in one system

Features:
- Create and manage multiple entities (farms, LLCs, etc.)
- Separate chart of accounts per entity
- Entity switching
- Consolidated reporting across entities
- Inter-entity transactions

GenFin v6.3.0
"""

import sqlite3
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Tuple
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class EntityType(str, Enum):
    FARM = "farm"
    LLC = "llc"
    CORPORATION = "corporation"
    SOLE_PROPRIETOR = "sole_proprietor"
    PARTNERSHIP = "partnership"
    S_CORP = "s_corp"
    TRUST = "trust"
    OTHER = "other"


class EntityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EntityCreate(BaseModel):
    """Create a new entity"""
    name: str
    legal_name: Optional[str] = None
    entity_type: EntityType = EntityType.FARM
    tax_id: Optional[str] = None  # EIN or SSN
    state_of_formation: Optional[str] = None
    fiscal_year_end: int = 12  # Month (1-12)

    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Contact
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class EntityResponse(BaseModel):
    """Entity response"""
    id: int
    code: str
    name: str
    legal_name: Optional[str]
    entity_type: str
    tax_id: Optional[str]
    state_of_formation: Optional[str]
    fiscal_year_end: int
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    status: str
    is_default: bool
    created_at: datetime


class InterEntityTransfer(BaseModel):
    """Transfer between entities"""
    from_entity_id: int
    to_entity_id: int
    amount: float
    description: str
    transfer_date: date = Field(default_factory=date.today)
    from_account_id: Optional[str] = None  # Will use inter-entity account if not specified
    to_account_id: Optional[str] = None


# ============================================================================
# MULTI-ENTITY SERVICE
# ============================================================================

class GenFinEntityService:
    """Service for managing multiple business entities"""

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self._init_tables()
        self._ensure_default_entity()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize entity tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genfin_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                legal_name VARCHAR(200),
                entity_type VARCHAR(50) DEFAULT 'farm',
                tax_id VARCHAR(20),
                state_of_formation VARCHAR(2),
                fiscal_year_end INTEGER DEFAULT 12,
                address_line1 VARCHAR(200),
                address_line2 VARCHAR(200),
                city VARCHAR(100),
                state VARCHAR(2),
                zip_code VARCHAR(20),
                phone VARCHAR(20),
                email VARCHAR(200),
                website VARCHAR(200),
                status VARCHAR(20) DEFAULT 'active',
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Inter-entity transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genfin_interentity_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_entity_id INTEGER NOT NULL,
                to_entity_id INTEGER NOT NULL,
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                transfer_date DATE NOT NULL,
                from_journal_entry_id INTEGER,
                to_journal_entry_id INTEGER,
                status VARCHAR(20) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_entity_id) REFERENCES genfin_entities(id),
                FOREIGN KEY (to_entity_id) REFERENCES genfin_entities(id)
            )
        """)

        # Entity user access (who can access which entities)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genfin_entity_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                can_view BOOLEAN DEFAULT 1,
                can_edit BOOLEAN DEFAULT 0,
                can_admin BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES genfin_entities(id),
                UNIQUE(entity_id, user_id)
            )
        """)

        conn.commit()
        conn.close()

    def _ensure_default_entity(self):
        """Ensure at least one default entity exists"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM genfin_entities")
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("""
                INSERT INTO genfin_entities (code, name, legal_name, entity_type, is_default)
                VALUES ('MAIN', 'Main Farm', 'Main Farm Operations', 'farm', 1)
            """)
            conn.commit()

        conn.close()

    # ========================================================================
    # ENTITY MANAGEMENT
    # ========================================================================

    def create_entity(self, data: EntityCreate) -> Tuple[Optional[EntityResponse], Optional[str]]:
        """Create a new entity"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Generate code from name
        code = ''.join(c for c in data.name.upper() if c.isalnum())[:10]

        # Ensure unique code
        cursor.execute("SELECT COUNT(*) FROM genfin_entities WHERE code = ?", (code,))
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT MAX(id) FROM genfin_entities")
            max_id = cursor.fetchone()[0] or 0
            code = f"{code[:7]}{max_id + 1:03d}"

        try:
            cursor.execute("""
                INSERT INTO genfin_entities (
                    code, name, legal_name, entity_type, tax_id, state_of_formation,
                    fiscal_year_end, address_line1, address_line2, city, state,
                    zip_code, phone, email, website
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, data.name, data.legal_name or data.name, data.entity_type.value,
                data.tax_id, data.state_of_formation, data.fiscal_year_end,
                data.address_line1, data.address_line2, data.city, data.state,
                data.zip_code, data.phone, data.email, data.website
            ))

            entity_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_entity(entity_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def get_entity(self, entity_id: int) -> Optional[EntityResponse]:
        """Get entity by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM genfin_entities WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_entity(row)

    def get_default_entity(self) -> Optional[EntityResponse]:
        """Get the default entity"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM genfin_entities WHERE is_default = 1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_entity(row)

    def list_entities(self, active_only: bool = True) -> List[EntityResponse]:
        """List all entities"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM genfin_entities"
        if active_only:
            query += " WHERE status = 'active'"
        query += " ORDER BY is_default DESC, name"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_entity(row) for row in rows]

    def update_entity(self, entity_id: int, **kwargs) -> Tuple[Optional[EntityResponse], Optional[str]]:
        """Update an entity"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build update statement
        updates = []
        params = []

        allowed_fields = [
            'name', 'legal_name', 'entity_type', 'tax_id', 'state_of_formation',
            'fiscal_year_end', 'address_line1', 'address_line2', 'city', 'state',
            'zip_code', 'phone', 'email', 'website', 'status'
        ]

        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = ?")
                value = kwargs[field]
                if hasattr(value, 'value'):  # Enum
                    value = value.value
                params.append(value)

        if not updates:
            conn.close()
            return None, "No fields to update"

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(entity_id)

        try:
            cursor.execute(f"""
                UPDATE genfin_entities SET {", ".join(updates)} WHERE id = ?
            """, params)

            conn.commit()
            conn.close()

            return self.get_entity(entity_id), None

        except Exception as e:
            conn.close()
            return None, str(e)

    def set_default_entity(self, entity_id: int) -> Tuple[bool, Optional[str]]:
        """Set an entity as the default"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Clear existing default
            cursor.execute("UPDATE genfin_entities SET is_default = 0")

            # Set new default
            cursor.execute("UPDATE genfin_entities SET is_default = 1 WHERE id = ?", (entity_id,))

            if cursor.rowcount == 0:
                conn.close()
                return False, "Entity not found"

            conn.commit()
            conn.close()
            return True, None

        except Exception as e:
            conn.close()
            return False, str(e)

    def _row_to_entity(self, row: sqlite3.Row) -> EntityResponse:
        """Convert row to EntityResponse"""
        return EntityResponse(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            legal_name=row["legal_name"],
            entity_type=row["entity_type"],
            tax_id=row["tax_id"],
            state_of_formation=row["state_of_formation"],
            fiscal_year_end=row["fiscal_year_end"],
            address_line1=row["address_line1"],
            address_line2=row["address_line2"],
            city=row["city"],
            state=row["state"],
            zip_code=row["zip_code"],
            phone=row["phone"],
            email=row["email"],
            website=row["website"],
            status=row["status"],
            is_default=bool(row["is_default"]),
            created_at=row["created_at"]
        )

    # ========================================================================
    # INTER-ENTITY TRANSACTIONS
    # ========================================================================

    def create_inter_entity_transfer(self, data: InterEntityTransfer) -> Tuple[Optional[Dict], Optional[str]]:
        """Create a transfer between entities"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verify both entities exist
        cursor.execute("SELECT id FROM genfin_entities WHERE id IN (?, ?)",
                      (data.from_entity_id, data.to_entity_id))
        if len(cursor.fetchall()) != 2:
            conn.close()
            return None, "One or both entities not found"

        try:
            cursor.execute("""
                INSERT INTO genfin_interentity_transactions (
                    from_entity_id, to_entity_id, amount, description, transfer_date
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                data.from_entity_id, data.to_entity_id, data.amount,
                data.description, data.transfer_date.isoformat()
            ))

            transfer_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return {
                "transfer_id": transfer_id,
                "from_entity_id": data.from_entity_id,
                "to_entity_id": data.to_entity_id,
                "amount": data.amount,
                "description": data.description,
                "transfer_date": data.transfer_date.isoformat(),
                "status": "completed"
            }, None

        except Exception as e:
            conn.close()
            return None, str(e)

    def get_inter_entity_transfers(
        self,
        entity_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """Get inter-entity transfers"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT t.*,
                   fe.name as from_entity_name,
                   te.name as to_entity_name
            FROM genfin_interentity_transactions t
            JOIN genfin_entities fe ON t.from_entity_id = fe.id
            JOIN genfin_entities te ON t.to_entity_id = te.id
            WHERE 1=1
        """
        params = []

        if entity_id:
            query += " AND (t.from_entity_id = ? OR t.to_entity_id = ?)"
            params.extend([entity_id, entity_id])

        if start_date:
            query += " AND t.transfer_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND t.transfer_date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY t.transfer_date DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            "transfer_id": row["id"],
            "from_entity_id": row["from_entity_id"],
            "from_entity_name": row["from_entity_name"],
            "to_entity_id": row["to_entity_id"],
            "to_entity_name": row["to_entity_name"],
            "amount": float(row["amount"]),
            "description": row["description"],
            "transfer_date": row["transfer_date"],
            "status": row["status"]
        } for row in rows]

    # ========================================================================
    # USER ACCESS
    # ========================================================================

    def grant_user_access(
        self,
        entity_id: int,
        user_id: int,
        role: str = "user",
        can_view: bool = True,
        can_edit: bool = False,
        can_admin: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Grant a user access to an entity"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO genfin_entity_users (
                    entity_id, user_id, role, can_view, can_edit, can_admin
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (entity_id, user_id, role, can_view, can_edit, can_admin))

            conn.commit()
            conn.close()
            return True, None

        except Exception as e:
            conn.close()
            return False, str(e)

    def get_user_entities(self, user_id: int) -> List[EntityResponse]:
        """Get all entities a user has access to"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.* FROM genfin_entities e
            JOIN genfin_entity_users eu ON e.id = eu.entity_id
            WHERE eu.user_id = ? AND eu.can_view = 1 AND e.status = 'active'
            ORDER BY e.is_default DESC, e.name
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_entity(row) for row in rows]

    def check_user_access(self, entity_id: int, user_id: int, permission: str = "view") -> bool:
        """Check if user has specific permission on entity"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT can_view, can_edit, can_admin FROM genfin_entity_users
            WHERE entity_id = ? AND user_id = ?
        """, (entity_id, user_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        if permission == "view":
            return bool(row["can_view"])
        elif permission == "edit":
            return bool(row["can_edit"])
        elif permission == "admin":
            return bool(row["can_admin"])

        return False

    # ========================================================================
    # CONSOLIDATED REPORTING
    # ========================================================================

    def get_consolidated_summary(self, entity_ids: Optional[List[int]] = None) -> Dict:
        """Get consolidated financial summary across entities"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if entity_ids:
            placeholders = ",".join("?" * len(entity_ids))
            cursor.execute(f"""
                SELECT * FROM genfin_entities WHERE id IN ({placeholders}) AND status = 'active'
            """, entity_ids)
        else:
            cursor.execute("SELECT * FROM genfin_entities WHERE status = 'active'")

        entities = cursor.fetchall()
        conn.close()

        # This would integrate with genfin_reports_service for actual financials
        # For now, return summary structure
        return {
            "entity_count": len(entities),
            "entities": [{
                "id": e["id"],
                "name": e["name"],
                "entity_type": e["entity_type"]
            } for e in entities],
            "consolidated_assets": 0,  # Would calculate from chart of accounts
            "consolidated_liabilities": 0,
            "consolidated_equity": 0,
            "consolidated_revenue": 0,
            "consolidated_expenses": 0,
            "eliminations": 0,  # Inter-entity transaction eliminations
            "report_date": date.today().isoformat()
        }

    # ========================================================================
    # SERVICE SUMMARY
    # ========================================================================

    def get_service_summary(self) -> Dict:
        """Get service summary"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM genfin_entities WHERE status = 'active'")
        entity_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM genfin_interentity_transactions")
        transfer_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM genfin_entity_users")
        user_count = cursor.fetchone()[0]

        # Get count by entity type for by_type dict
        cursor.execute("SELECT entity_type, COUNT(*) FROM genfin_entities WHERE status = 'active' GROUP BY entity_type")
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "service": "GenFin Multi-Entity",
            "version": "6.3.0",
            "total_entities": entity_count,
            "active_entities": entity_count,
            "by_type": by_type,
            "inter_entity_transfers": transfer_count,
            "users_with_access": user_count,
            "features": [
                "Multiple business entities",
                "Entity switching",
                "Inter-entity transfers",
                "User access control per entity",
                "Consolidated reporting",
                "Separate chart of accounts per entity"
            ]
        }


# ============================================================================
# SINGLETON
# ============================================================================

_entity_service: Optional[GenFinEntityService] = None


def get_entity_service(db_path: str = "agtools.db") -> GenFinEntityService:
    """Get or create entity service singleton"""
    global _entity_service
    if _entity_service is None:
        _entity_service = GenFinEntityService(db_path)
    return _entity_service
