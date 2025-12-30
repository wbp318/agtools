"""
Livestock Management API Client

Handles livestock CRUD operations for the Farm Operations Manager.
AgTools v6.4.0 - Farm Operations Suite
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES - GROUPS
# ============================================================================

@dataclass
class GroupInfo:
    """Livestock group information dataclass"""
    id: int
    group_name: str
    species: str
    head_count: int
    start_date: Optional[str]
    source: Optional[str]
    cost_per_head: float
    barn_location: Optional[str]
    status: str
    notes: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    created_by_user_id: int
    total_value: float
    avg_weight: Optional[float]

    @classmethod
    def from_dict(cls, data: dict) -> "GroupInfo":
        """Create GroupInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            group_name=data.get("group_name", ""),
            species=data.get("species", ""),
            head_count=data.get("head_count", 0),
            start_date=data.get("start_date"),
            source=data.get("source"),
            cost_per_head=float(data.get("cost_per_head", 0)),
            barn_location=data.get("barn_location"),
            status=data.get("status", "active"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by_user_id=data.get("created_by_user_id", 0),
            total_value=float(data.get("total_value", 0)),
            avg_weight=data.get("avg_weight")
        )

    @property
    def species_display(self) -> str:
        """Get display-friendly species text."""
        return self.species.title()

    @property
    def status_display(self) -> str:
        """Get display-friendly status text."""
        return self.status.replace("_", " ").title()


# ============================================================================
# DATA CLASSES - ANIMALS
# ============================================================================

@dataclass
class AnimalInfo:
    """Animal information dataclass"""
    id: int
    tag_number: Optional[str]
    name: Optional[str]
    species: str
    breed: Optional[str]
    sex: Optional[str]
    birth_date: Optional[str]
    purchase_date: Optional[str]
    purchase_price: float
    sire_id: Optional[int]
    dam_id: Optional[int]
    status: str
    current_weight: Optional[float]
    current_location: Optional[str]
    group_id: Optional[int]
    group_name: Optional[str]
    registration_number: Optional[str]
    color_markings: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    created_by_user_id: int
    age_days: Optional[int]
    sire_tag: Optional[str]
    dam_tag: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "AnimalInfo":
        """Create AnimalInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            tag_number=data.get("tag_number"),
            name=data.get("name"),
            species=data.get("species", ""),
            breed=data.get("breed"),
            sex=data.get("sex"),
            birth_date=data.get("birth_date"),
            purchase_date=data.get("purchase_date"),
            purchase_price=float(data.get("purchase_price", 0)),
            sire_id=data.get("sire_id"),
            dam_id=data.get("dam_id"),
            status=data.get("status", "active"),
            current_weight=data.get("current_weight"),
            current_location=data.get("current_location"),
            group_id=data.get("group_id"),
            group_name=data.get("group_name"),
            registration_number=data.get("registration_number"),
            color_markings=data.get("color_markings"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by_user_id=data.get("created_by_user_id", 0),
            age_days=data.get("age_days"),
            sire_tag=data.get("sire_tag"),
            dam_tag=data.get("dam_tag")
        )

    @property
    def display_name(self) -> str:
        """Get display name (tag or name)."""
        if self.tag_number and self.name:
            return f"{self.tag_number} - {self.name}"
        return self.tag_number or self.name or f"Animal #{self.id}"

    @property
    def species_display(self) -> str:
        """Get display-friendly species text."""
        return self.species.title()

    @property
    def sex_display(self) -> str:
        """Get display-friendly sex text."""
        if not self.sex:
            return "Unknown"
        return self.sex.title()

    @property
    def status_display(self) -> str:
        """Get display-friendly status text."""
        return self.status.replace("_", " ").title()

    @property
    def age_display(self) -> str:
        """Get human-readable age."""
        if self.age_days is None:
            return "Unknown"
        if self.age_days < 30:
            return f"{self.age_days} days"
        months = self.age_days // 30
        if months < 24:
            return f"{months} months"
        years = self.age_days // 365
        return f"{years} years"

    @property
    def weight_display(self) -> str:
        """Get formatted weight."""
        if self.current_weight is None:
            return "N/A"
        return f"{self.current_weight:,.0f} lbs"


# ============================================================================
# DATA CLASSES - HEALTH RECORDS
# ============================================================================

@dataclass
class HealthRecordInfo:
    """Health record information dataclass"""
    id: int
    animal_id: Optional[int]
    group_id: Optional[int]
    record_date: str
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
    withdrawal_end_date: Optional[str]
    next_due_date: Optional[str]
    lot_number: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: str
    animal_tag: Optional[str]
    group_name: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "HealthRecordInfo":
        """Create HealthRecordInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            animal_id=data.get("animal_id"),
            group_id=data.get("group_id"),
            record_date=data.get("record_date", ""),
            record_type=data.get("record_type", ""),
            description=data.get("description"),
            medication=data.get("medication"),
            dosage=data.get("dosage"),
            dosage_unit=data.get("dosage_unit"),
            route=data.get("route"),
            administered_by=data.get("administered_by"),
            vet_name=data.get("vet_name"),
            cost=float(data.get("cost", 0)),
            withdrawal_days=data.get("withdrawal_days", 0),
            withdrawal_end_date=data.get("withdrawal_end_date"),
            next_due_date=data.get("next_due_date"),
            lot_number=data.get("lot_number"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            animal_tag=data.get("animal_tag"),
            group_name=data.get("group_name")
        )

    @property
    def record_type_display(self) -> str:
        """Get display-friendly record type."""
        return self.record_type.replace("_", " ").title()

    @property
    def target_display(self) -> str:
        """Get the animal/group this record applies to."""
        if self.animal_tag:
            return f"Animal: {self.animal_tag}"
        if self.group_name:
            return f"Group: {self.group_name}"
        return "Unknown"


# ============================================================================
# DATA CLASSES - BREEDING RECORDS
# ============================================================================

@dataclass
class BreedingRecordInfo:
    """Breeding record information dataclass"""
    id: int
    female_id: int
    male_id: Optional[int]
    semen_source: Optional[str]
    breeding_date: str
    breeding_method: Optional[str]
    technician: Optional[str]
    expected_due_date: Optional[str]
    actual_birth_date: Optional[str]
    offspring_count: int
    live_births: int
    stillbirths: int
    status: str
    gestation_days: Optional[int]
    calving_ease: Optional[int]
    notes: Optional[str]
    is_active: bool
    created_at: str
    female_tag: Optional[str]
    male_tag: Optional[str]
    days_until_due: Optional[int]

    @classmethod
    def from_dict(cls, data: dict) -> "BreedingRecordInfo":
        """Create BreedingRecordInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            female_id=data.get("female_id", 0),
            male_id=data.get("male_id"),
            semen_source=data.get("semen_source"),
            breeding_date=data.get("breeding_date", ""),
            breeding_method=data.get("breeding_method"),
            technician=data.get("technician"),
            expected_due_date=data.get("expected_due_date"),
            actual_birth_date=data.get("actual_birth_date"),
            offspring_count=data.get("offspring_count", 0),
            live_births=data.get("live_births", 0),
            stillbirths=data.get("stillbirths", 0),
            status=data.get("status", "pending"),
            gestation_days=data.get("gestation_days"),
            calving_ease=data.get("calving_ease"),
            notes=data.get("notes"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", ""),
            female_tag=data.get("female_tag"),
            male_tag=data.get("male_tag"),
            days_until_due=data.get("days_until_due")
        )

    @property
    def status_display(self) -> str:
        """Get display-friendly status."""
        return self.status.replace("_", " ").title()

    @property
    def method_display(self) -> str:
        """Get display-friendly breeding method."""
        if not self.breeding_method:
            return "Unknown"
        methods = {"natural": "Natural", "ai": "AI", "embryo_transfer": "Embryo Transfer"}
        return methods.get(self.breeding_method, self.breeding_method.title())

    @property
    def sire_display(self) -> str:
        """Get sire display text."""
        if self.male_tag:
            return self.male_tag
        if self.semen_source:
            return f"AI: {self.semen_source}"
        return "Unknown"


# ============================================================================
# DATA CLASSES - WEIGHT RECORDS
# ============================================================================

@dataclass
class WeightRecordInfo:
    """Weight record information dataclass"""
    id: int
    animal_id: Optional[int]
    group_id: Optional[int]
    weight_date: str
    weight_lbs: float
    avg_weight: Optional[float]
    sample_size: Optional[int]
    weight_type: Optional[str]
    adg: Optional[float]
    notes: Optional[str]
    created_at: str
    animal_tag: Optional[str]
    group_name: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "WeightRecordInfo":
        """Create WeightRecordInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            animal_id=data.get("animal_id"),
            group_id=data.get("group_id"),
            weight_date=data.get("weight_date", ""),
            weight_lbs=float(data.get("weight_lbs", 0)),
            avg_weight=data.get("avg_weight"),
            sample_size=data.get("sample_size"),
            weight_type=data.get("weight_type"),
            adg=data.get("adg"),
            notes=data.get("notes"),
            created_at=data.get("created_at", ""),
            animal_tag=data.get("animal_tag"),
            group_name=data.get("group_name")
        )

    @property
    def weight_type_display(self) -> str:
        """Get display-friendly weight type."""
        if not self.weight_type:
            return "Routine"
        return self.weight_type.replace("_", " ").title()

    @property
    def adg_display(self) -> str:
        """Get formatted ADG."""
        if self.adg is None:
            return "N/A"
        return f"{self.adg:.2f} lbs/day"


# ============================================================================
# DATA CLASSES - SALE RECORDS
# ============================================================================

@dataclass
class SaleRecordInfo:
    """Sale record information dataclass"""
    id: int
    animal_id: Optional[int]
    group_id: Optional[int]
    sale_date: str
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
    created_at: str
    animal_tag: Optional[str]
    group_name: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "SaleRecordInfo":
        """Create SaleRecordInfo from API response dict."""
        return cls(
            id=data.get("id", 0),
            animal_id=data.get("animal_id"),
            group_id=data.get("group_id"),
            sale_date=data.get("sale_date", ""),
            buyer_name=data.get("buyer_name"),
            buyer_contact=data.get("buyer_contact"),
            head_count=data.get("head_count", 1),
            sale_weight=data.get("sale_weight"),
            price_per_lb=data.get("price_per_lb"),
            sale_price=float(data.get("sale_price", 0)),
            sale_type=data.get("sale_type"),
            market_name=data.get("market_name"),
            commission=float(data.get("commission", 0)),
            trucking_cost=float(data.get("trucking_cost", 0)),
            net_proceeds=data.get("net_proceeds"),
            check_number=data.get("check_number"),
            payment_received=data.get("payment_received", False),
            notes=data.get("notes"),
            created_at=data.get("created_at", ""),
            animal_tag=data.get("animal_tag"),
            group_name=data.get("group_name")
        )

    @property
    def sale_type_display(self) -> str:
        """Get display-friendly sale type."""
        if not self.sale_type:
            return "Private"
        return self.sale_type.replace("_", " ").title()

    @property
    def price_display(self) -> str:
        """Get formatted sale price."""
        return f"${self.sale_price:,.2f}"

    @property
    def net_display(self) -> str:
        """Get formatted net proceeds."""
        if self.net_proceeds is None:
            return "N/A"
        return f"${self.net_proceeds:,.2f}"


# ============================================================================
# DATA CLASSES - SUMMARY
# ============================================================================

@dataclass
class LivestockSummary:
    """Summary statistics for livestock"""
    total_head: int
    total_groups: int
    by_species: Dict[str, int]
    by_status: Dict[str, int]
    avg_weight_by_species: Dict[str, float]
    total_value: float
    health_alerts: int
    upcoming_due_dates: int
    recent_sales_30d: float

    @classmethod
    def from_dict(cls, data: dict) -> "LivestockSummary":
        """Create LivestockSummary from API response dict."""
        return cls(
            total_head=data.get("total_head", 0),
            total_groups=data.get("total_groups", 0),
            by_species=data.get("by_species", {}),
            by_status=data.get("by_status", {}),
            avg_weight_by_species=data.get("avg_weight_by_species", {}),
            total_value=float(data.get("total_value", 0)),
            health_alerts=data.get("health_alerts", 0),
            upcoming_due_dates=data.get("upcoming_due_dates", 0),
            recent_sales_30d=float(data.get("recent_sales_30d", 0))
        )


# ============================================================================
# LIVESTOCK API CLASS
# ============================================================================

class LivestockAPI:
    """API client for livestock management operations."""

    # Species options
    SPECIES_TYPES = [
        ("cattle", "Cattle"),
        ("hog", "Hogs"),
        ("poultry", "Poultry"),
        ("sheep", "Sheep"),
        ("goat", "Goats")
    ]

    # Sex options
    SEX_TYPES = [
        ("male", "Male"),
        ("female", "Female"),
        ("castrated", "Castrated"),
        ("unknown", "Unknown")
    ]

    # Animal status options
    ANIMAL_STATUSES = [
        ("active", "Active"),
        ("sold", "Sold"),
        ("deceased", "Deceased"),
        ("culled", "Culled"),
        ("transferred", "Transferred")
    ]

    # Group status options
    GROUP_STATUSES = [
        ("active", "Active"),
        ("sold", "Sold"),
        ("processed", "Processed"),
        ("dispersed", "Dispersed")
    ]

    # Health record types
    HEALTH_RECORD_TYPES = [
        ("vaccination", "Vaccination"),
        ("treatment", "Treatment"),
        ("vet_visit", "Vet Visit"),
        ("injury", "Injury"),
        ("illness", "Illness"),
        ("deworming", "Deworming"),
        ("hoof_trim", "Hoof Trim"),
        ("castration", "Castration"),
        ("pregnancy_check", "Pregnancy Check"),
        ("other", "Other")
    ]

    # Medication routes
    MEDICATION_ROUTES = [
        ("oral", "Oral"),
        ("injection", "Injection"),
        ("topical", "Topical"),
        ("pour_on", "Pour-On"),
        ("other", "Other")
    ]

    # Breeding methods
    BREEDING_METHODS = [
        ("natural", "Natural"),
        ("ai", "Artificial Insemination"),
        ("embryo_transfer", "Embryo Transfer")
    ]

    # Breeding statuses
    BREEDING_STATUSES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("open", "Open"),
        ("aborted", "Aborted"),
        ("completed", "Completed")
    ]

    # Weight types
    WEIGHT_TYPES = [
        ("birth", "Birth"),
        ("weaning", "Weaning"),
        ("yearling", "Yearling"),
        ("sale", "Sale"),
        ("routine", "Routine"),
        ("other", "Other")
    ]

    # Sale types
    SALE_TYPES = [
        ("auction", "Auction"),
        ("private", "Private Sale"),
        ("contract", "Contract"),
        ("cull", "Cull"),
        ("breeding_stock", "Breeding Stock")
    ]

    def __init__(self):
        self._client = get_api_client()

    # ========================================================================
    # GROUP OPERATIONS
    # ========================================================================

    def get_summary(self) -> Tuple[Optional[LivestockSummary], Optional[str]]:
        """Get livestock summary statistics."""
        try:
            response = self._client.get("/api/v1/livestock/summary")
            if response.status_code == 200:
                return LivestockSummary.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def list_groups(
        self,
        species: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[GroupInfo], Optional[str]]:
        """List livestock groups with optional filters."""
        try:
            params = {}
            if species:
                params["species"] = species
            if status:
                params["status"] = status
            if search:
                params["search"] = search

            response = self._client.get("/api/v1/livestock/groups", params=params)
            if response.status_code == 200:
                data = response.json()
                groups = [GroupInfo.from_dict(g) for g in data.get("groups", [])]
                return groups, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def get_group(self, group_id: int) -> Tuple[Optional[GroupInfo], Optional[str]]:
        """Get a specific livestock group."""
        try:
            response = self._client.get(f"/api/v1/livestock/groups/{group_id}")
            if response.status_code == 200:
                return GroupInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def create_group(self, **kwargs) -> Tuple[Optional[GroupInfo], Optional[str]]:
        """Create a new livestock group."""
        try:
            response = self._client.post("/api/v1/livestock/groups", json=kwargs)
            if response.status_code in (200, 201):
                return GroupInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    def update_group(self, group_id: int, **kwargs) -> Tuple[Optional[GroupInfo], Optional[str]]:
        """Update an existing livestock group."""
        try:
            response = self._client.put(f"/api/v1/livestock/groups/{group_id}", json=kwargs)
            if response.status_code == 200:
                return GroupInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def delete_group(self, group_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a livestock group."""
        try:
            response = self._client.delete(f"/api/v1/livestock/groups/{group_id}")
            if response.status_code in (200, 204):
                return True, None
            return False, f"Error: {response.status_code}"
        except Exception as e:
            return False, str(e)

    # ========================================================================
    # ANIMAL OPERATIONS
    # ========================================================================

    def list_animals(
        self,
        species: Optional[str] = None,
        status: Optional[str] = None,
        group_id: Optional[int] = None,
        sex: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[AnimalInfo], Optional[str]]:
        """List animals with optional filters."""
        try:
            params = {"limit": limit, "offset": offset}
            if species:
                params["species"] = species
            if status:
                params["status"] = status
            if group_id:
                params["group_id"] = group_id
            if sex:
                params["sex"] = sex
            if search:
                params["search"] = search

            response = self._client.get("/api/v1/livestock", params=params)
            if response.status_code == 200:
                data = response.json()
                animals = [AnimalInfo.from_dict(a) for a in data.get("animals", [])]
                return animals, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def get_animal(self, animal_id: int) -> Tuple[Optional[AnimalInfo], Optional[str]]:
        """Get a specific animal."""
        try:
            response = self._client.get(f"/api/v1/livestock/{animal_id}")
            if response.status_code == 200:
                return AnimalInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def create_animal(self, **kwargs) -> Tuple[Optional[AnimalInfo], Optional[str]]:
        """Create a new animal."""
        try:
            response = self._client.post("/api/v1/livestock", json=kwargs)
            if response.status_code in (200, 201):
                return AnimalInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    def update_animal(self, animal_id: int, **kwargs) -> Tuple[Optional[AnimalInfo], Optional[str]]:
        """Update an existing animal."""
        try:
            response = self._client.put(f"/api/v1/livestock/{animal_id}", json=kwargs)
            if response.status_code == 200:
                return AnimalInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def delete_animal(self, animal_id: int) -> Tuple[bool, Optional[str]]:
        """Delete an animal."""
        try:
            response = self._client.delete(f"/api/v1/livestock/{animal_id}")
            if response.status_code in (200, 204):
                return True, None
            return False, f"Error: {response.status_code}"
        except Exception as e:
            return False, str(e)

    def get_breeds(self, species: str) -> Tuple[List[str], Optional[str]]:
        """Get common breeds for a species."""
        try:
            response = self._client.get(f"/api/v1/livestock/breeds/{species}")
            if response.status_code == 200:
                return response.json().get("breeds", []), None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    # ========================================================================
    # HEALTH RECORD OPERATIONS
    # ========================================================================

    def list_health_records(
        self,
        animal_id: Optional[int] = None,
        group_id: Optional[int] = None,
        record_type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Tuple[List[HealthRecordInfo], Optional[str]]:
        """List health records with optional filters."""
        try:
            params = {}
            if animal_id:
                params["animal_id"] = animal_id
            if group_id:
                params["group_id"] = group_id
            if record_type:
                params["record_type"] = record_type
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date

            response = self._client.get("/api/v1/livestock/health", params=params)
            if response.status_code == 200:
                data = response.json()
                records = [HealthRecordInfo.from_dict(r) for r in data.get("records", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def get_health_alerts(self) -> Tuple[List[HealthRecordInfo], Optional[str]]:
        """Get upcoming health alerts."""
        try:
            response = self._client.get("/api/v1/livestock/health/alerts")
            if response.status_code == 200:
                data = response.json()
                records = [HealthRecordInfo.from_dict(r) for r in data.get("alerts", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_health_record(self, **kwargs) -> Tuple[Optional[HealthRecordInfo], Optional[str]]:
        """Create a new health record."""
        try:
            response = self._client.post("/api/v1/livestock/health", json=kwargs)
            if response.status_code in (200, 201):
                return HealthRecordInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    # ========================================================================
    # BREEDING RECORD OPERATIONS
    # ========================================================================

    def list_breeding_records(
        self,
        female_id: Optional[int] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Tuple[List[BreedingRecordInfo], Optional[str]]:
        """List breeding records with optional filters."""
        try:
            params = {}
            if female_id:
                params["female_id"] = female_id
            if status:
                params["status"] = status
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date

            response = self._client.get("/api/v1/livestock/breeding", params=params)
            if response.status_code == 200:
                data = response.json()
                records = [BreedingRecordInfo.from_dict(r) for r in data.get("records", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def get_upcoming_due_dates(self, days: int = 60) -> Tuple[List[BreedingRecordInfo], Optional[str]]:
        """Get breeding records with upcoming due dates."""
        try:
            response = self._client.get("/api/v1/livestock/breeding/due", params={"days": days})
            if response.status_code == 200:
                data = response.json()
                records = [BreedingRecordInfo.from_dict(r) for r in data.get("records", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_breeding_record(self, **kwargs) -> Tuple[Optional[BreedingRecordInfo], Optional[str]]:
        """Create a new breeding record."""
        try:
            response = self._client.post("/api/v1/livestock/breeding", json=kwargs)
            if response.status_code in (200, 201):
                return BreedingRecordInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    def update_breeding_record(self, record_id: int, **kwargs) -> Tuple[Optional[BreedingRecordInfo], Optional[str]]:
        """Update an existing breeding record."""
        try:
            response = self._client.put(f"/api/v1/livestock/breeding/{record_id}", json=kwargs)
            if response.status_code == 200:
                return BreedingRecordInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    # ========================================================================
    # WEIGHT RECORD OPERATIONS
    # ========================================================================

    def list_weight_records(
        self,
        animal_id: Optional[int] = None,
        group_id: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Tuple[List[WeightRecordInfo], Optional[str]]:
        """List weight records with optional filters."""
        try:
            params = {}
            if animal_id:
                params["animal_id"] = animal_id
            if group_id:
                params["group_id"] = group_id
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date

            response = self._client.get("/api/v1/livestock/weights", params=params)
            if response.status_code == 200:
                data = response.json()
                records = [WeightRecordInfo.from_dict(r) for r in data.get("records", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_weight_record(self, **kwargs) -> Tuple[Optional[WeightRecordInfo], Optional[str]]:
        """Create a new weight record."""
        try:
            response = self._client.post("/api/v1/livestock/weights", json=kwargs)
            if response.status_code in (200, 201):
                return WeightRecordInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    # ========================================================================
    # SALE RECORD OPERATIONS
    # ========================================================================

    def list_sale_records(
        self,
        animal_id: Optional[int] = None,
        group_id: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        sale_type: Optional[str] = None
    ) -> Tuple[List[SaleRecordInfo], Optional[str]]:
        """List sale records with optional filters."""
        try:
            params = {}
            if animal_id:
                params["animal_id"] = animal_id
            if group_id:
                params["group_id"] = group_id
            if from_date:
                params["from_date"] = from_date
            if to_date:
                params["to_date"] = to_date
            if sale_type:
                params["sale_type"] = sale_type

            response = self._client.get("/api/v1/livestock/sales", params=params)
            if response.status_code == 200:
                data = response.json()
                records = [SaleRecordInfo.from_dict(r) for r in data.get("records", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_sale_record(self, **kwargs) -> Tuple[Optional[SaleRecordInfo], Optional[str]]:
        """Create a new sale record."""
        try:
            response = self._client.post("/api/v1/livestock/sales", json=kwargs)
            if response.status_code in (200, 201):
                return SaleRecordInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_livestock_api: Optional[LivestockAPI] = None


def get_livestock_api() -> LivestockAPI:
    """Get or create singleton livestock API instance."""
    global _livestock_api
    if _livestock_api is None:
        _livestock_api = LivestockAPI()
    return _livestock_api
