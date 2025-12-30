"""
Livestock Service for Farm Operations Manager
Handles livestock CRUD operations, health records, breeding, weights, and sales.

AgTools v6.4.0 - Farm Operations Suite
"""

import sqlite3
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel, Field

from .auth_service import get_auth_service


# ============================================================================
# ENUMS
# ============================================================================

class Species(str, Enum):
    """Livestock species"""
    CATTLE = "cattle"
    HOG = "hog"
    POULTRY = "poultry"
    SHEEP = "sheep"
    GOAT = "goat"


class Sex(str, Enum):
    """Animal sex"""
    MALE = "male"
    FEMALE = "female"
    CASTRATED = "castrated"
    UNKNOWN = "unknown"


class AnimalStatus(str, Enum):
    """Animal status"""
    ACTIVE = "active"
    SOLD = "sold"
    DECEASED = "deceased"
    CULLED = "culled"
    TRANSFERRED = "transferred"


class GroupStatus(str, Enum):
    """Group status"""
    ACTIVE = "active"
    SOLD = "sold"
    PROCESSED = "processed"
    DISPERSED = "dispersed"


class HealthRecordType(str, Enum):
    """Health record types"""
    VACCINATION = "vaccination"
    TREATMENT = "treatment"
    VET_VISIT = "vet_visit"
    INJURY = "injury"
    ILLNESS = "illness"
    DEWORMING = "deworming"
    HOOF_TRIM = "hoof_trim"
    CASTRATION = "castration"
    PREGNANCY_CHECK = "pregnancy_check"
    OTHER = "other"


class MedicationRoute(str, Enum):
    """Medication administration routes"""
    ORAL = "oral"
    INJECTION = "injection"
    TOPICAL = "topical"
    POUR_ON = "pour_on"
    OTHER = "other"


class BreedingMethod(str, Enum):
    """Breeding methods"""
    NATURAL = "natural"
    AI = "ai"
    EMBRYO_TRANSFER = "embryo_transfer"


class BreedingStatus(str, Enum):
    """Breeding record status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    OPEN = "open"
    ABORTED = "aborted"
    COMPLETED = "completed"


class WeightType(str, Enum):
    """Weight record types"""
    BIRTH = "birth"
    WEANING = "weaning"
    YEARLING = "yearling"
    SALE = "sale"
    ROUTINE = "routine"
    OTHER = "other"


class SaleType(str, Enum):
    """Sale types"""
    AUCTION = "auction"
    PRIVATE = "private"
    CONTRACT = "contract"
    CULL = "cull"
    BREEDING_STOCK = "breeding_stock"


# ============================================================================
# PYDANTIC MODELS - GROUPS
# ============================================================================

class GroupCreate(BaseModel):
    """Create livestock group"""
    group_name: str = Field(..., min_length=1, max_length=100)
    species: Species
    head_count: int = Field(default=0, ge=0)
    start_date: Optional[date] = None
    source: Optional[str] = Field(None, max_length=200)
    cost_per_head: float = Field(default=0, ge=0)
    barn_location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class GroupUpdate(BaseModel):
    """Update livestock group"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=100)
    head_count: Optional[int] = Field(None, ge=0)
    source: Optional[str] = Field(None, max_length=200)
    cost_per_head: Optional[float] = Field(None, ge=0)
    barn_location: Optional[str] = Field(None, max_length=100)
    status: Optional[GroupStatus] = None
    notes: Optional[str] = None


class GroupResponse(BaseModel):
    """Livestock group response"""
    id: int
    group_name: str
    species: str
    head_count: int
    start_date: Optional[date]
    source: Optional[str]
    cost_per_head: float
    barn_location: Optional[str]
    status: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    # Computed
    total_value: float = 0
    avg_weight: Optional[float] = None


# ============================================================================
# PYDANTIC MODELS - ANIMALS
# ============================================================================

class AnimalCreate(BaseModel):
    """Create animal"""
    tag_number: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    species: Species
    breed: Optional[str] = Field(None, max_length=100)
    sex: Optional[Sex] = Sex.UNKNOWN
    birth_date: Optional[date] = None
    purchase_date: Optional[date] = None
    purchase_price: float = Field(default=0, ge=0)
    sire_id: Optional[int] = None
    dam_id: Optional[int] = None
    current_weight: Optional[float] = Field(None, ge=0)
    current_location: Optional[str] = Field(None, max_length=100)
    group_id: Optional[int] = None
    registration_number: Optional[str] = Field(None, max_length=100)
    color_markings: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class AnimalUpdate(BaseModel):
    """Update animal"""
    tag_number: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    breed: Optional[str] = Field(None, max_length=100)
    sex: Optional[Sex] = None
    birth_date: Optional[date] = None
    current_weight: Optional[float] = Field(None, ge=0)
    current_location: Optional[str] = Field(None, max_length=100)
    group_id: Optional[int] = None
    status: Optional[AnimalStatus] = None
    registration_number: Optional[str] = Field(None, max_length=100)
    color_markings: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class AnimalResponse(BaseModel):
    """Animal response"""
    id: int
    tag_number: Optional[str]
    name: Optional[str]
    species: str
    breed: Optional[str]
    sex: Optional[str]
    birth_date: Optional[date]
    purchase_date: Optional[date]
    purchase_price: float
    sire_id: Optional[int]
    dam_id: Optional[int]
    status: str
    current_weight: Optional[float]
    current_location: Optional[str]
    group_id: Optional[int]
    group_name: Optional[str] = None
    registration_number: Optional[str]
    color_markings: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    # Computed
    age_days: Optional[int] = None
    sire_tag: Optional[str] = None
    dam_tag: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - HEALTH RECORDS
# ============================================================================

class HealthRecordCreate(BaseModel):
    """Create health record"""
    animal_id: Optional[int] = None
    group_id: Optional[int] = None
    record_date: date
    record_type: HealthRecordType
    description: Optional[str] = None
    medication: Optional[str] = Field(None, max_length=200)
    dosage: Optional[str] = Field(None, max_length=100)
    dosage_unit: Optional[str] = Field(None, max_length=50)
    route: Optional[MedicationRoute] = None
    administered_by: Optional[str] = Field(None, max_length=100)
    vet_name: Optional[str] = Field(None, max_length=100)
    cost: float = Field(default=0, ge=0)
    withdrawal_days: int = Field(default=0, ge=0)
    next_due_date: Optional[date] = None
    lot_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class HealthRecordResponse(BaseModel):
    """Health record response"""
    id: int
    animal_id: Optional[int]
    group_id: Optional[int]
    record_date: date
    record_type: str
    description: Optional[str]
    medication: Optional[str]
    dosage: Optional[str]
    dosage_unit: Optional[str]
    route: Optional[str]
    administered_by: Optional[str]
    vet_name: Optional[str]
    cost: float
    withdrawal_days: int
    withdrawal_end_date: Optional[date]
    next_due_date: Optional[date]
    lot_number: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    # Computed
    animal_tag: Optional[str] = None
    group_name: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - BREEDING
# ============================================================================

class BreedingRecordCreate(BaseModel):
    """Create breeding record"""
    female_id: int
    male_id: Optional[int] = None
    semen_source: Optional[str] = Field(None, max_length=200)
    breeding_date: date
    breeding_method: Optional[BreedingMethod] = BreedingMethod.NATURAL
    technician: Optional[str] = Field(None, max_length=100)
    expected_due_date: Optional[date] = None
    notes: Optional[str] = None


class BreedingRecordUpdate(BaseModel):
    """Update breeding record"""
    status: Optional[BreedingStatus] = None
    actual_birth_date: Optional[date] = None
    offspring_count: Optional[int] = Field(None, ge=0)
    live_births: Optional[int] = Field(None, ge=0)
    stillbirths: Optional[int] = Field(None, ge=0)
    calving_ease: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class BreedingRecordResponse(BaseModel):
    """Breeding record response"""
    id: int
    female_id: int
    male_id: Optional[int]
    semen_source: Optional[str]
    breeding_date: date
    breeding_method: Optional[str]
    technician: Optional[str]
    expected_due_date: Optional[date]
    actual_birth_date: Optional[date]
    offspring_count: int
    live_births: int
    stillbirths: int
    status: str
    gestation_days: Optional[int]
    calving_ease: Optional[int]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    # Computed
    female_tag: Optional[str] = None
    male_tag: Optional[str] = None
    days_until_due: Optional[int] = None


# ============================================================================
# PYDANTIC MODELS - WEIGHTS
# ============================================================================

class WeightRecordCreate(BaseModel):
    """Create weight record"""
    animal_id: Optional[int] = None
    group_id: Optional[int] = None
    weight_date: date
    weight_lbs: float = Field(..., gt=0)
    avg_weight: Optional[float] = Field(None, gt=0)
    sample_size: Optional[int] = Field(None, ge=1)
    weight_type: Optional[WeightType] = WeightType.ROUTINE
    notes: Optional[str] = None


class WeightRecordResponse(BaseModel):
    """Weight record response"""
    id: int
    animal_id: Optional[int]
    group_id: Optional[int]
    weight_date: date
    weight_lbs: float
    avg_weight: Optional[float]
    sample_size: Optional[int]
    weight_type: Optional[str]
    adg: Optional[float]
    notes: Optional[str]
    created_at: datetime
    # Computed
    animal_tag: Optional[str] = None
    group_name: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - SALES
# ============================================================================

class SaleRecordCreate(BaseModel):
    """Create sale record"""
    animal_id: Optional[int] = None
    group_id: Optional[int] = None
    sale_date: date
    buyer_name: Optional[str] = Field(None, max_length=200)
    buyer_contact: Optional[str] = Field(None, max_length=200)
    head_count: int = Field(default=1, ge=1)
    sale_weight: Optional[float] = Field(None, ge=0)
    price_per_lb: Optional[float] = Field(None, ge=0)
    sale_price: float = Field(..., ge=0)
    sale_type: Optional[SaleType] = SaleType.PRIVATE
    market_name: Optional[str] = Field(None, max_length=200)
    commission: float = Field(default=0, ge=0)
    trucking_cost: float = Field(default=0, ge=0)
    notes: Optional[str] = None


class SaleRecordResponse(BaseModel):
    """Sale record response"""
    id: int
    animal_id: Optional[int]
    group_id: Optional[int]
    sale_date: date
    buyer_name: Optional[str]
    buyer_contact: Optional[str]
    head_count: int
    sale_weight: Optional[float]
    price_per_lb: Optional[float]
    sale_price: float
    sale_type: Optional[str]
    market_name: Optional[str]
    commission: float
    trucking_cost: float
    net_proceeds: Optional[float]
    check_number: Optional[str]
    payment_received: bool
    notes: Optional[str]
    created_at: datetime
    # Computed
    animal_tag: Optional[str] = None
    group_name: Optional[str] = None


# ============================================================================
# PYDANTIC MODELS - SUMMARY
# ============================================================================

class LivestockSummary(BaseModel):
    """Summary statistics"""
    total_head: int
    total_groups: int
    by_species: Dict[str, int]
    by_status: Dict[str, int]
    avg_weight_by_species: Dict[str, float]
    total_value: float
    health_alerts: int
    upcoming_due_dates: int
    recent_sales_30d: float


# ============================================================================
# LIVESTOCK SERVICE CLASS
# ============================================================================

class LivestockService:
    """
    Livestock service handling:
    - Animal and group CRUD
    - Health records
    - Breeding records
    - Weight tracking
    - Sales tracking
    - Summary statistics
    """

    # Common cattle breeds
    CATTLE_BREEDS = [
        "Angus", "Black Angus", "Red Angus", "Hereford", "Charolais",
        "Simmental", "Limousin", "Brahman", "Brangus", "Beefmaster",
        "Shorthorn", "Gelbvieh", "Maine-Anjou", "Wagyu", "Holstein",
        "Jersey", "Guernsey", "Brown Swiss", "Crossbred", "Other"
    ]

    # Common hog breeds
    HOG_BREEDS = [
        "Yorkshire", "Duroc", "Hampshire", "Berkshire", "Landrace",
        "Chester White", "Poland China", "Spotted", "Pietrain",
        "Large Black", "Tamworth", "Crossbred", "Other"
    ]

    # Common poultry breeds
    POULTRY_BREEDS = [
        "Cornish Cross", "Rhode Island Red", "Leghorn", "Plymouth Rock",
        "Orpington", "Wyandotte", "Australorp", "Sussex", "Brahma",
        "Turkey Broad Breasted White", "Turkey Bronze", "Other"
    ]

    # Common sheep breeds
    SHEEP_BREEDS = [
        "Suffolk", "Hampshire", "Dorset", "Merino", "Rambouillet",
        "Columbia", "Targhee", "Polypay", "Katahdin", "Dorper",
        "Texel", "Southdown", "Crossbred", "Other"
    ]

    # Common goat breeds
    GOAT_BREEDS = [
        "Boer", "Kiko", "Spanish", "Savanna", "Nubian", "Alpine",
        "Saanen", "LaMancha", "Toggenburg", "Oberhasli", "Nigerian Dwarf",
        "Pygmy", "Angora", "Crossbred", "Other"
    ]

    # Gestation periods (days)
    GESTATION_DAYS = {
        "cattle": 283,
        "hog": 114,
        "sheep": 147,
        "goat": 150,
        "poultry": 21  # Incubation for chickens
    }

    def __init__(self, db_path: str = "agtools.db"):
        self.db_path = db_path
        self.auth_service = get_auth_service()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_database(self):
        """Initialize database tables from migration."""
        migration_path = "database/migrations/007_livestock.sql"
        try:
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            conn = self._get_connection()
            conn.executescript(migration_sql)
            conn.commit()
            conn.close()
        except FileNotFoundError:
            pass  # Migration will be run separately

    # ========================================================================
    # GROUP OPERATIONS
    # ========================================================================

    def create_group(self, data: GroupCreate, user_id: int) -> Tuple[Optional[GroupResponse], Optional[str]]:
        """Create a livestock group."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO livestock_groups (
                    group_name, species, head_count, start_date, source,
                    cost_per_head, barn_location, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.group_name, data.species.value, data.head_count,
                data.start_date.isoformat() if data.start_date else None,
                data.source, data.cost_per_head, data.barn_location,
                data.notes, user_id
            ))

            group_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_group(group_id)
        except Exception as e:
            return None, str(e)

    def get_group(self, group_id: int) -> Tuple[Optional[GroupResponse], Optional[str]]:
        """Get a livestock group by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM livestock_groups WHERE id = ? AND is_active = 1
            """, (group_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Group not found"

            return self._row_to_group_response(row), None
        except Exception as e:
            return None, str(e)

    def list_groups(
        self,
        species: Optional[Species] = None,
        status: Optional[GroupStatus] = None,
        search: Optional[str] = None
    ) -> Tuple[List[GroupResponse], Optional[str]]:
        """List livestock groups with filters."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM livestock_groups WHERE is_active = 1"
            params = []

            if species:
                query += " AND species = ?"
                params.append(species.value)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            if search:
                query += " AND (group_name LIKE ? OR barn_location LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            groups = [self._row_to_group_response(row) for row in rows]
            return groups, None
        except Exception as e:
            return [], str(e)

    def update_group(self, group_id: int, data: GroupUpdate) -> Tuple[Optional[GroupResponse], Optional[str]]:
        """Update a livestock group."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if data.group_name is not None:
                updates.append("group_name = ?")
                params.append(data.group_name)
            if data.head_count is not None:
                updates.append("head_count = ?")
                params.append(data.head_count)
            if data.source is not None:
                updates.append("source = ?")
                params.append(data.source)
            if data.cost_per_head is not None:
                updates.append("cost_per_head = ?")
                params.append(data.cost_per_head)
            if data.barn_location is not None:
                updates.append("barn_location = ?")
                params.append(data.barn_location)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status.value)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)

            if not updates:
                conn.close()
                return self.get_group(group_id)

            params.append(group_id)
            cursor.execute(f"""
                UPDATE livestock_groups SET {', '.join(updates)}
                WHERE id = ? AND is_active = 1
            """, params)

            conn.commit()
            conn.close()

            return self.get_group(group_id)
        except Exception as e:
            return None, str(e)

    def delete_group(self, group_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete a livestock group."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE livestock_groups SET is_active = 0 WHERE id = ?
            """, (group_id,))

            conn.commit()
            affected = cursor.rowcount
            conn.close()

            return affected > 0, None
        except Exception as e:
            return False, str(e)

    def _row_to_group_response(self, row: sqlite3.Row) -> GroupResponse:
        """Convert database row to GroupResponse."""
        return GroupResponse(
            id=row["id"],
            group_name=row["group_name"],
            species=row["species"],
            head_count=row["head_count"],
            start_date=datetime.fromisoformat(row["start_date"]).date() if row["start_date"] else None,
            source=row["source"],
            cost_per_head=row["cost_per_head"] or 0,
            barn_location=row["barn_location"],
            status=row["status"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            created_by_user_id=row["created_by_user_id"],
            total_value=row["head_count"] * (row["cost_per_head"] or 0)
        )

    # ========================================================================
    # ANIMAL OPERATIONS
    # ========================================================================

    def create_animal(self, data: AnimalCreate, user_id: int) -> Tuple[Optional[AnimalResponse], Optional[str]]:
        """Create an animal."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO livestock_animals (
                    tag_number, name, species, breed, sex, birth_date,
                    purchase_date, purchase_price, sire_id, dam_id,
                    current_weight, current_location, group_id,
                    registration_number, color_markings, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.tag_number, data.name, data.species.value, data.breed,
                data.sex.value if data.sex else None,
                data.birth_date.isoformat() if data.birth_date else None,
                data.purchase_date.isoformat() if data.purchase_date else None,
                data.purchase_price, data.sire_id, data.dam_id,
                data.current_weight, data.current_location, data.group_id,
                data.registration_number, data.color_markings, data.notes, user_id
            ))

            animal_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_animal(animal_id)
        except Exception as e:
            return None, str(e)

    def get_animal(self, animal_id: int) -> Tuple[Optional[AnimalResponse], Optional[str]]:
        """Get an animal by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT a.*,
                    g.group_name,
                    s.tag_number as sire_tag,
                    d.tag_number as dam_tag
                FROM livestock_animals a
                LEFT JOIN livestock_groups g ON a.group_id = g.id
                LEFT JOIN livestock_animals s ON a.sire_id = s.id
                LEFT JOIN livestock_animals d ON a.dam_id = d.id
                WHERE a.id = ? AND a.is_active = 1
            """, (animal_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Animal not found"

            return self._row_to_animal_response(row), None
        except Exception as e:
            return None, str(e)

    def list_animals(
        self,
        species: Optional[Species] = None,
        status: Optional[AnimalStatus] = None,
        group_id: Optional[int] = None,
        sex: Optional[Sex] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AnimalResponse], Optional[str]]:
        """List animals with filters."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT a.*,
                    g.group_name,
                    s.tag_number as sire_tag,
                    d.tag_number as dam_tag
                FROM livestock_animals a
                LEFT JOIN livestock_groups g ON a.group_id = g.id
                LEFT JOIN livestock_animals s ON a.sire_id = s.id
                LEFT JOIN livestock_animals d ON a.dam_id = d.id
                WHERE a.is_active = 1
            """
            params = []

            if species:
                query += " AND a.species = ?"
                params.append(species.value)

            if status:
                query += " AND a.status = ?"
                params.append(status.value)

            if group_id:
                query += " AND a.group_id = ?"
                params.append(group_id)

            if sex:
                query += " AND a.sex = ?"
                params.append(sex.value)

            if search:
                query += " AND (a.tag_number LIKE ? OR a.name LIKE ? OR a.breed LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            animals = [self._row_to_animal_response(row) for row in rows]
            return animals, None
        except Exception as e:
            return [], str(e)

    def update_animal(self, animal_id: int, data: AnimalUpdate) -> Tuple[Optional[AnimalResponse], Optional[str]]:
        """Update an animal."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if data.tag_number is not None:
                updates.append("tag_number = ?")
                params.append(data.tag_number)
            if data.name is not None:
                updates.append("name = ?")
                params.append(data.name)
            if data.breed is not None:
                updates.append("breed = ?")
                params.append(data.breed)
            if data.sex is not None:
                updates.append("sex = ?")
                params.append(data.sex.value)
            if data.birth_date is not None:
                updates.append("birth_date = ?")
                params.append(data.birth_date.isoformat())
            if data.current_weight is not None:
                updates.append("current_weight = ?")
                params.append(data.current_weight)
            if data.current_location is not None:
                updates.append("current_location = ?")
                params.append(data.current_location)
            if data.group_id is not None:
                updates.append("group_id = ?")
                params.append(data.group_id)
            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status.value)
            if data.registration_number is not None:
                updates.append("registration_number = ?")
                params.append(data.registration_number)
            if data.color_markings is not None:
                updates.append("color_markings = ?")
                params.append(data.color_markings)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)

            if not updates:
                conn.close()
                return self.get_animal(animal_id)

            params.append(animal_id)
            cursor.execute(f"""
                UPDATE livestock_animals SET {', '.join(updates)}
                WHERE id = ? AND is_active = 1
            """, params)

            conn.commit()
            conn.close()

            return self.get_animal(animal_id)
        except Exception as e:
            return None, str(e)

    def delete_animal(self, animal_id: int) -> Tuple[bool, Optional[str]]:
        """Soft delete an animal."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE livestock_animals SET is_active = 0 WHERE id = ?
            """, (animal_id,))

            conn.commit()
            affected = cursor.rowcount
            conn.close()

            return affected > 0, None
        except Exception as e:
            return False, str(e)

    def _row_to_animal_response(self, row: sqlite3.Row) -> AnimalResponse:
        """Convert database row to AnimalResponse."""
        birth_date = None
        age_days = None
        if row["birth_date"]:
            birth_date = datetime.fromisoformat(row["birth_date"]).date()
            age_days = (date.today() - birth_date).days

        return AnimalResponse(
            id=row["id"],
            tag_number=row["tag_number"],
            name=row["name"],
            species=row["species"],
            breed=row["breed"],
            sex=row["sex"],
            birth_date=birth_date,
            purchase_date=datetime.fromisoformat(row["purchase_date"]).date() if row["purchase_date"] else None,
            purchase_price=row["purchase_price"] or 0,
            sire_id=row["sire_id"],
            dam_id=row["dam_id"],
            status=row["status"],
            current_weight=row["current_weight"],
            current_location=row["current_location"],
            group_id=row["group_id"],
            group_name=row["group_name"] if "group_name" in row.keys() else None,
            registration_number=row["registration_number"],
            color_markings=row["color_markings"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            created_by_user_id=row["created_by_user_id"],
            age_days=age_days,
            sire_tag=row["sire_tag"] if "sire_tag" in row.keys() else None,
            dam_tag=row["dam_tag"] if "dam_tag" in row.keys() else None
        )

    # ========================================================================
    # HEALTH RECORD OPERATIONS
    # ========================================================================

    def create_health_record(self, data: HealthRecordCreate, user_id: int) -> Tuple[Optional[HealthRecordResponse], Optional[str]]:
        """Create a health record."""
        try:
            if not data.animal_id and not data.group_id:
                return None, "Must specify animal_id or group_id"

            # Calculate withdrawal end date
            withdrawal_end = None
            if data.withdrawal_days > 0:
                withdrawal_end = data.record_date + timedelta(days=data.withdrawal_days)

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO livestock_health_records (
                    animal_id, group_id, record_date, record_type, description,
                    medication, dosage, dosage_unit, route, administered_by,
                    vet_name, cost, withdrawal_days, withdrawal_end_date,
                    next_due_date, lot_number, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.animal_id, data.group_id, data.record_date.isoformat(),
                data.record_type.value, data.description, data.medication,
                data.dosage, data.dosage_unit,
                data.route.value if data.route else None,
                data.administered_by, data.vet_name, data.cost,
                data.withdrawal_days,
                withdrawal_end.isoformat() if withdrawal_end else None,
                data.next_due_date.isoformat() if data.next_due_date else None,
                data.lot_number, data.notes, user_id
            ))

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_health_record(record_id)
        except Exception as e:
            return None, str(e)

    def get_health_record(self, record_id: int) -> Tuple[Optional[HealthRecordResponse], Optional[str]]:
        """Get a health record by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT h.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_health_records h
                LEFT JOIN livestock_animals a ON h.animal_id = a.id
                LEFT JOIN livestock_groups g ON h.group_id = g.id
                WHERE h.id = ? AND h.is_active = 1
            """, (record_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Health record not found"

            return self._row_to_health_response(row), None
        except Exception as e:
            return None, str(e)

    def list_health_records(
        self,
        animal_id: Optional[int] = None,
        group_id: Optional[int] = None,
        record_type: Optional[HealthRecordType] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Tuple[List[HealthRecordResponse], Optional[str]]:
        """List health records with filters."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT h.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_health_records h
                LEFT JOIN livestock_animals a ON h.animal_id = a.id
                LEFT JOIN livestock_groups g ON h.group_id = g.id
                WHERE h.is_active = 1
            """
            params = []

            if animal_id:
                query += " AND h.animal_id = ?"
                params.append(animal_id)

            if group_id:
                query += " AND h.group_id = ?"
                params.append(group_id)

            if record_type:
                query += " AND h.record_type = ?"
                params.append(record_type.value)

            if from_date:
                query += " AND h.record_date >= ?"
                params.append(from_date.isoformat())

            if to_date:
                query += " AND h.record_date <= ?"
                params.append(to_date.isoformat())

            query += " ORDER BY h.record_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_health_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def get_health_alerts(self) -> Tuple[List[HealthRecordResponse], Optional[str]]:
        """Get upcoming health alerts (treatments due within 30 days)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            today = date.today()
            future = today + timedelta(days=30)

            cursor.execute("""
                SELECT h.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_health_records h
                LEFT JOIN livestock_animals a ON h.animal_id = a.id
                LEFT JOIN livestock_groups g ON h.group_id = g.id
                WHERE h.is_active = 1
                AND h.next_due_date IS NOT NULL
                AND h.next_due_date BETWEEN ? AND ?
                ORDER BY h.next_due_date ASC
            """, (today.isoformat(), future.isoformat()))

            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_health_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def _row_to_health_response(self, row: sqlite3.Row) -> HealthRecordResponse:
        """Convert database row to HealthRecordResponse."""
        return HealthRecordResponse(
            id=row["id"],
            animal_id=row["animal_id"],
            group_id=row["group_id"],
            record_date=datetime.fromisoformat(row["record_date"]).date(),
            record_type=row["record_type"],
            description=row["description"],
            medication=row["medication"],
            dosage=row["dosage"],
            dosage_unit=row["dosage_unit"],
            route=row["route"],
            administered_by=row["administered_by"],
            vet_name=row["vet_name"],
            cost=row["cost"] or 0,
            withdrawal_days=row["withdrawal_days"] or 0,
            withdrawal_end_date=datetime.fromisoformat(row["withdrawal_end_date"]).date() if row["withdrawal_end_date"] else None,
            next_due_date=datetime.fromisoformat(row["next_due_date"]).date() if row["next_due_date"] else None,
            lot_number=row["lot_number"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            animal_tag=row["animal_tag"] if "animal_tag" in row.keys() else None,
            group_name=row["group_name"] if "group_name" in row.keys() else None
        )

    # ========================================================================
    # BREEDING RECORD OPERATIONS
    # ========================================================================

    def create_breeding_record(self, data: BreedingRecordCreate, user_id: int) -> Tuple[Optional[BreedingRecordResponse], Optional[str]]:
        """Create a breeding record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get female's species for gestation calculation
            cursor.execute("SELECT species FROM livestock_animals WHERE id = ?", (data.female_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None, "Female animal not found"

            species = row["species"]
            gestation = self.GESTATION_DAYS.get(species, 280)

            # Calculate expected due date if not provided
            expected_due = data.expected_due_date
            if not expected_due:
                expected_due = data.breeding_date + timedelta(days=gestation)

            cursor.execute("""
                INSERT INTO livestock_breeding_records (
                    female_id, male_id, semen_source, breeding_date,
                    breeding_method, technician, expected_due_date,
                    gestation_days, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.female_id, data.male_id, data.semen_source,
                data.breeding_date.isoformat(),
                data.breeding_method.value if data.breeding_method else None,
                data.technician, expected_due.isoformat(),
                gestation, data.notes, user_id
            ))

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_breeding_record(record_id)
        except Exception as e:
            return None, str(e)

    def get_breeding_record(self, record_id: int) -> Tuple[Optional[BreedingRecordResponse], Optional[str]]:
        """Get a breeding record by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT b.*,
                    f.tag_number as female_tag,
                    m.tag_number as male_tag
                FROM livestock_breeding_records b
                LEFT JOIN livestock_animals f ON b.female_id = f.id
                LEFT JOIN livestock_animals m ON b.male_id = m.id
                WHERE b.id = ? AND b.is_active = 1
            """, (record_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Breeding record not found"

            return self._row_to_breeding_response(row), None
        except Exception as e:
            return None, str(e)

    def list_breeding_records(
        self,
        female_id: Optional[int] = None,
        status: Optional[BreedingStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Tuple[List[BreedingRecordResponse], Optional[str]]:
        """List breeding records with filters."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT b.*,
                    f.tag_number as female_tag,
                    m.tag_number as male_tag
                FROM livestock_breeding_records b
                LEFT JOIN livestock_animals f ON b.female_id = f.id
                LEFT JOIN livestock_animals m ON b.male_id = m.id
                WHERE b.is_active = 1
            """
            params = []

            if female_id:
                query += " AND b.female_id = ?"
                params.append(female_id)

            if status:
                query += " AND b.status = ?"
                params.append(status.value)

            if from_date:
                query += " AND b.breeding_date >= ?"
                params.append(from_date.isoformat())

            if to_date:
                query += " AND b.breeding_date <= ?"
                params.append(to_date.isoformat())

            query += " ORDER BY b.breeding_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_breeding_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def get_upcoming_due_dates(self, days: int = 60) -> Tuple[List[BreedingRecordResponse], Optional[str]]:
        """Get breeding records with due dates in the next N days."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            today = date.today()
            future = today + timedelta(days=days)

            cursor.execute("""
                SELECT b.*,
                    f.tag_number as female_tag,
                    m.tag_number as male_tag
                FROM livestock_breeding_records b
                LEFT JOIN livestock_animals f ON b.female_id = f.id
                LEFT JOIN livestock_animals m ON b.male_id = m.id
                WHERE b.is_active = 1
                AND b.status IN ('pending', 'confirmed')
                AND b.expected_due_date BETWEEN ? AND ?
                ORDER BY b.expected_due_date ASC
            """, (today.isoformat(), future.isoformat()))

            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_breeding_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def update_breeding_record(self, record_id: int, data: BreedingRecordUpdate) -> Tuple[Optional[BreedingRecordResponse], Optional[str]]:
        """Update a breeding record."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if data.status is not None:
                updates.append("status = ?")
                params.append(data.status.value)
            if data.actual_birth_date is not None:
                updates.append("actual_birth_date = ?")
                params.append(data.actual_birth_date.isoformat())
            if data.offspring_count is not None:
                updates.append("offspring_count = ?")
                params.append(data.offspring_count)
            if data.live_births is not None:
                updates.append("live_births = ?")
                params.append(data.live_births)
            if data.stillbirths is not None:
                updates.append("stillbirths = ?")
                params.append(data.stillbirths)
            if data.calving_ease is not None:
                updates.append("calving_ease = ?")
                params.append(data.calving_ease)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)

            if not updates:
                conn.close()
                return self.get_breeding_record(record_id)

            params.append(record_id)
            cursor.execute(f"""
                UPDATE livestock_breeding_records SET {', '.join(updates)}
                WHERE id = ? AND is_active = 1
            """, params)

            conn.commit()
            conn.close()

            return self.get_breeding_record(record_id)
        except Exception as e:
            return None, str(e)

    def _row_to_breeding_response(self, row: sqlite3.Row) -> BreedingRecordResponse:
        """Convert database row to BreedingRecordResponse."""
        expected_due = datetime.fromisoformat(row["expected_due_date"]).date() if row["expected_due_date"] else None
        days_until_due = None
        if expected_due and row["status"] in ("pending", "confirmed"):
            days_until_due = (expected_due - date.today()).days

        return BreedingRecordResponse(
            id=row["id"],
            female_id=row["female_id"],
            male_id=row["male_id"],
            semen_source=row["semen_source"],
            breeding_date=datetime.fromisoformat(row["breeding_date"]).date(),
            breeding_method=row["breeding_method"],
            technician=row["technician"],
            expected_due_date=expected_due,
            actual_birth_date=datetime.fromisoformat(row["actual_birth_date"]).date() if row["actual_birth_date"] else None,
            offspring_count=row["offspring_count"] or 0,
            live_births=row["live_births"] or 0,
            stillbirths=row["stillbirths"] or 0,
            status=row["status"],
            gestation_days=row["gestation_days"],
            calving_ease=row["calving_ease"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            female_tag=row["female_tag"] if "female_tag" in row.keys() else None,
            male_tag=row["male_tag"] if "male_tag" in row.keys() else None,
            days_until_due=days_until_due
        )

    # ========================================================================
    # WEIGHT RECORD OPERATIONS
    # ========================================================================

    def create_weight_record(self, data: WeightRecordCreate, user_id: int) -> Tuple[Optional[WeightRecordResponse], Optional[str]]:
        """Create a weight record."""
        try:
            if not data.animal_id and not data.group_id:
                return None, "Must specify animal_id or group_id"

            conn = self._get_connection()
            cursor = conn.cursor()

            # Calculate ADG if we have previous weight for this animal
            adg = None
            if data.animal_id:
                cursor.execute("""
                    SELECT weight_lbs, weight_date FROM livestock_weights
                    WHERE animal_id = ? AND is_active = 1
                    ORDER BY weight_date DESC LIMIT 1
                """, (data.animal_id,))
                prev = cursor.fetchone()
                if prev:
                    prev_date = datetime.fromisoformat(prev["weight_date"]).date()
                    days = (data.weight_date - prev_date).days
                    if days > 0:
                        adg = (data.weight_lbs - prev["weight_lbs"]) / days

            cursor.execute("""
                INSERT INTO livestock_weights (
                    animal_id, group_id, weight_date, weight_lbs,
                    avg_weight, sample_size, weight_type, adg, notes,
                    created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.animal_id, data.group_id, data.weight_date.isoformat(),
                data.weight_lbs, data.avg_weight, data.sample_size,
                data.weight_type.value if data.weight_type else None,
                adg, data.notes, user_id
            ))

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_weight_record(record_id)
        except Exception as e:
            return None, str(e)

    def get_weight_record(self, record_id: int) -> Tuple[Optional[WeightRecordResponse], Optional[str]]:
        """Get a weight record by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT w.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_weights w
                LEFT JOIN livestock_animals a ON w.animal_id = a.id
                LEFT JOIN livestock_groups g ON w.group_id = g.id
                WHERE w.id = ? AND w.is_active = 1
            """, (record_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Weight record not found"

            return self._row_to_weight_response(row), None
        except Exception as e:
            return None, str(e)

    def list_weight_records(
        self,
        animal_id: Optional[int] = None,
        group_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Tuple[List[WeightRecordResponse], Optional[str]]:
        """List weight records with filters."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT w.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_weights w
                LEFT JOIN livestock_animals a ON w.animal_id = a.id
                LEFT JOIN livestock_groups g ON w.group_id = g.id
                WHERE w.is_active = 1
            """
            params = []

            if animal_id:
                query += " AND w.animal_id = ?"
                params.append(animal_id)

            if group_id:
                query += " AND w.group_id = ?"
                params.append(group_id)

            if from_date:
                query += " AND w.weight_date >= ?"
                params.append(from_date.isoformat())

            if to_date:
                query += " AND w.weight_date <= ?"
                params.append(to_date.isoformat())

            query += " ORDER BY w.weight_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_weight_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def _row_to_weight_response(self, row: sqlite3.Row) -> WeightRecordResponse:
        """Convert database row to WeightRecordResponse."""
        return WeightRecordResponse(
            id=row["id"],
            animal_id=row["animal_id"],
            group_id=row["group_id"],
            weight_date=datetime.fromisoformat(row["weight_date"]).date(),
            weight_lbs=row["weight_lbs"],
            avg_weight=row["avg_weight"],
            sample_size=row["sample_size"],
            weight_type=row["weight_type"],
            adg=row["adg"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            animal_tag=row["animal_tag"] if "animal_tag" in row.keys() else None,
            group_name=row["group_name"] if "group_name" in row.keys() else None
        )

    # ========================================================================
    # SALE RECORD OPERATIONS
    # ========================================================================

    def create_sale_record(self, data: SaleRecordCreate, user_id: int) -> Tuple[Optional[SaleRecordResponse], Optional[str]]:
        """Create a sale record."""
        try:
            if not data.animal_id and not data.group_id:
                return None, "Must specify animal_id or group_id"

            # Calculate net proceeds
            net_proceeds = data.sale_price - data.commission - data.trucking_cost

            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO livestock_sales (
                    animal_id, group_id, sale_date, buyer_name, buyer_contact,
                    head_count, sale_weight, price_per_lb, sale_price,
                    sale_type, market_name, commission, trucking_cost,
                    net_proceeds, notes, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.animal_id, data.group_id, data.sale_date.isoformat(),
                data.buyer_name, data.buyer_contact, data.head_count,
                data.sale_weight, data.price_per_lb, data.sale_price,
                data.sale_type.value if data.sale_type else None,
                data.market_name, data.commission, data.trucking_cost,
                net_proceeds, data.notes, user_id
            ))

            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return self.get_sale_record(record_id)
        except Exception as e:
            return None, str(e)

    def get_sale_record(self, record_id: int) -> Tuple[Optional[SaleRecordResponse], Optional[str]]:
        """Get a sale record by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT s.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_sales s
                LEFT JOIN livestock_animals a ON s.animal_id = a.id
                LEFT JOIN livestock_groups g ON s.group_id = g.id
                WHERE s.id = ? AND s.is_active = 1
            """, (record_id,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None, "Sale record not found"

            return self._row_to_sale_response(row), None
        except Exception as e:
            return None, str(e)

    def list_sale_records(
        self,
        animal_id: Optional[int] = None,
        group_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        sale_type: Optional[SaleType] = None
    ) -> Tuple[List[SaleRecordResponse], Optional[str]]:
        """List sale records with filters."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT s.*,
                    a.tag_number as animal_tag,
                    g.group_name
                FROM livestock_sales s
                LEFT JOIN livestock_animals a ON s.animal_id = a.id
                LEFT JOIN livestock_groups g ON s.group_id = g.id
                WHERE s.is_active = 1
            """
            params = []

            if animal_id:
                query += " AND s.animal_id = ?"
                params.append(animal_id)

            if group_id:
                query += " AND s.group_id = ?"
                params.append(group_id)

            if from_date:
                query += " AND s.sale_date >= ?"
                params.append(from_date.isoformat())

            if to_date:
                query += " AND s.sale_date <= ?"
                params.append(to_date.isoformat())

            if sale_type:
                query += " AND s.sale_type = ?"
                params.append(sale_type.value)

            query += " ORDER BY s.sale_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            records = [self._row_to_sale_response(row) for row in rows]
            return records, None
        except Exception as e:
            return [], str(e)

    def _row_to_sale_response(self, row: sqlite3.Row) -> SaleRecordResponse:
        """Convert database row to SaleRecordResponse."""
        return SaleRecordResponse(
            id=row["id"],
            animal_id=row["animal_id"],
            group_id=row["group_id"],
            sale_date=datetime.fromisoformat(row["sale_date"]).date(),
            buyer_name=row["buyer_name"],
            buyer_contact=row["buyer_contact"],
            head_count=row["head_count"] or 1,
            sale_weight=row["sale_weight"],
            price_per_lb=row["price_per_lb"],
            sale_price=row["sale_price"],
            sale_type=row["sale_type"],
            market_name=row["market_name"],
            commission=row["commission"] or 0,
            trucking_cost=row["trucking_cost"] or 0,
            net_proceeds=row["net_proceeds"],
            check_number=row["check_number"],
            payment_received=bool(row["payment_received"]),
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            animal_tag=row["animal_tag"] if "animal_tag" in row.keys() else None,
            group_name=row["group_name"] if "group_name" in row.keys() else None
        )

    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================

    def get_summary(self) -> Tuple[Optional[LivestockSummary], Optional[str]]:
        """Get livestock summary statistics."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Total head count
            cursor.execute("""
                SELECT COUNT(*) as total FROM livestock_animals
                WHERE is_active = 1 AND status = 'active'
            """)
            total_head = cursor.fetchone()["total"]

            # Total groups
            cursor.execute("""
                SELECT COUNT(*) as total FROM livestock_groups
                WHERE is_active = 1 AND status = 'active'
            """)
            total_groups = cursor.fetchone()["total"]

            # By species
            cursor.execute("""
                SELECT species, COUNT(*) as count FROM livestock_animals
                WHERE is_active = 1 AND status = 'active'
                GROUP BY species
            """)
            by_species = {row["species"]: row["count"] for row in cursor.fetchall()}

            # By status
            cursor.execute("""
                SELECT status, COUNT(*) as count FROM livestock_animals
                WHERE is_active = 1
                GROUP BY status
            """)
            by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Average weight by species
            cursor.execute("""
                SELECT species, AVG(current_weight) as avg_wt FROM livestock_animals
                WHERE is_active = 1 AND status = 'active' AND current_weight IS NOT NULL
                GROUP BY species
            """)
            avg_weight_by_species = {
                row["species"]: round(row["avg_wt"], 1) if row["avg_wt"] else 0
                for row in cursor.fetchall()
            }

            # Total purchase value
            cursor.execute("""
                SELECT COALESCE(SUM(purchase_price), 0) as total FROM livestock_animals
                WHERE is_active = 1 AND status = 'active'
            """)
            total_value = cursor.fetchone()["total"]

            # Health alerts (treatments due in next 30 days)
            today = date.today()
            future = today + timedelta(days=30)
            cursor.execute("""
                SELECT COUNT(*) as count FROM livestock_health_records
                WHERE is_active = 1 AND next_due_date BETWEEN ? AND ?
            """, (today.isoformat(), future.isoformat()))
            health_alerts = cursor.fetchone()["count"]

            # Upcoming due dates (next 60 days)
            future60 = today + timedelta(days=60)
            cursor.execute("""
                SELECT COUNT(*) as count FROM livestock_breeding_records
                WHERE is_active = 1 AND status IN ('pending', 'confirmed')
                AND expected_due_date BETWEEN ? AND ?
            """, (today.isoformat(), future60.isoformat()))
            upcoming_due = cursor.fetchone()["count"]

            # Recent sales (last 30 days)
            past30 = today - timedelta(days=30)
            cursor.execute("""
                SELECT COALESCE(SUM(net_proceeds), 0) as total FROM livestock_sales
                WHERE is_active = 1 AND sale_date >= ?
            """, (past30.isoformat(),))
            recent_sales = cursor.fetchone()["total"]

            conn.close()

            return LivestockSummary(
                total_head=total_head,
                total_groups=total_groups,
                by_species=by_species,
                by_status=by_status,
                avg_weight_by_species=avg_weight_by_species,
                total_value=total_value,
                health_alerts=health_alerts,
                upcoming_due_dates=upcoming_due,
                recent_sales_30d=recent_sales
            ), None
        except Exception as e:
            return None, str(e)

    def get_breeds_for_species(self, species: Species) -> List[str]:
        """Get common breeds for a species."""
        breeds_map = {
            Species.CATTLE: self.CATTLE_BREEDS,
            Species.HOG: self.HOG_BREEDS,
            Species.POULTRY: self.POULTRY_BREEDS,
            Species.SHEEP: self.SHEEP_BREEDS,
            Species.GOAT: self.GOAT_BREEDS
        }
        return breeds_map.get(species, ["Other"])


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_livestock_service: Optional[LivestockService] = None


def get_livestock_service(db_path: str = "agtools.db") -> LivestockService:
    """Get or create singleton livestock service instance."""
    global _livestock_service
    if _livestock_service is None:
        _livestock_service = LivestockService(db_path)
    return _livestock_service
