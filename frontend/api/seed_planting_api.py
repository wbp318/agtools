"""
Seed & Planting API Client

Handles seed inventory, planting records, and emergence tracking.
AgTools v6.4.0 - Farm Operations Suite
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict

from .client import get_api_client


@dataclass
class SeedInfo:
    """Seed inventory information"""
    id: int
    variety_name: str
    crop_type: str
    brand: Optional[str]
    product_code: Optional[str]
    trait_package: Optional[str]
    relative_maturity: Optional[str]
    germination_rate: Optional[float]
    quantity_units: str
    quantity_on_hand: float
    unit_cost: float
    lot_number: Optional[str]
    storage_location: Optional[str]
    supplier: Optional[str]
    total_value: float
    treatments_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "SeedInfo":
        return cls(
            id=data.get("id", 0),
            variety_name=data.get("variety_name", ""),
            crop_type=data.get("crop_type", ""),
            brand=data.get("brand"),
            product_code=data.get("product_code"),
            trait_package=data.get("trait_package"),
            relative_maturity=data.get("relative_maturity"),
            germination_rate=data.get("germination_rate"),
            quantity_units=data.get("quantity_units", "bags"),
            quantity_on_hand=float(data.get("quantity_on_hand", 0)),
            unit_cost=float(data.get("unit_cost", 0)),
            lot_number=data.get("lot_number"),
            storage_location=data.get("storage_location"),
            supplier=data.get("supplier"),
            total_value=float(data.get("total_value", 0)),
            treatments_count=data.get("treatments_count", 0)
        )

    @property
    def crop_display(self) -> str:
        return self.crop_type.replace("_", " ").title()

    @property
    def quantity_display(self) -> str:
        return f"{self.quantity_on_hand:,.1f} {self.quantity_units}"


@dataclass
class PlantingInfo:
    """Planting record information"""
    id: int
    field_id: int
    field_name: Optional[str]
    seed_inventory_id: Optional[int]
    variety_name: Optional[str]
    crop_type: Optional[str]
    planting_date: str
    planting_rate: float
    rate_unit: str
    row_spacing: Optional[float]
    acres_planted: float
    population_target: Optional[int]
    status: str
    cost_per_acre: Optional[float]
    total_cost: float
    emergence_checks: int
    latest_stand_pct: Optional[float]

    @classmethod
    def from_dict(cls, data: dict) -> "PlantingInfo":
        return cls(
            id=data.get("id", 0),
            field_id=data.get("field_id", 0),
            field_name=data.get("field_name"),
            seed_inventory_id=data.get("seed_inventory_id"),
            variety_name=data.get("variety_name"),
            crop_type=data.get("crop_type"),
            planting_date=data.get("planting_date", ""),
            planting_rate=float(data.get("planting_rate", 0)),
            rate_unit=data.get("rate_unit", "seeds/acre"),
            row_spacing=data.get("row_spacing"),
            acres_planted=float(data.get("acres_planted", 0)),
            population_target=data.get("population_target"),
            status=data.get("status", "completed"),
            cost_per_acre=data.get("cost_per_acre"),
            total_cost=float(data.get("total_cost", 0)),
            emergence_checks=data.get("emergence_checks", 0),
            latest_stand_pct=data.get("latest_stand_pct")
        )

    @property
    def status_display(self) -> str:
        return self.status.replace("_", " ").title()

    @property
    def stand_display(self) -> str:
        if self.latest_stand_pct is None:
            return "Not checked"
        return f"{self.latest_stand_pct:.0f}%"


@dataclass
class EmergenceInfo:
    """Emergence record information"""
    id: int
    planting_record_id: int
    check_date: str
    days_after_planting: Optional[int]
    stand_count: Optional[int]
    plants_per_acre: Optional[int]
    stand_percentage: Optional[float]
    uniformity_score: Optional[int]
    vigor_score: Optional[int]
    growth_stage: Optional[str]
    issues_noted: Optional[str]
    field_name: Optional[str]
    variety_name: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "EmergenceInfo":
        return cls(
            id=data.get("id", 0),
            planting_record_id=data.get("planting_record_id", 0),
            check_date=data.get("check_date", ""),
            days_after_planting=data.get("days_after_planting"),
            stand_count=data.get("stand_count"),
            plants_per_acre=data.get("plants_per_acre"),
            stand_percentage=data.get("stand_percentage"),
            uniformity_score=data.get("uniformity_score"),
            vigor_score=data.get("vigor_score"),
            growth_stage=data.get("growth_stage"),
            issues_noted=data.get("issues_noted"),
            field_name=data.get("field_name"),
            variety_name=data.get("variety_name")
        )

    @property
    def stand_display(self) -> str:
        if self.stand_percentage is None:
            return "N/A"
        return f"{self.stand_percentage:.0f}%"


@dataclass
class SeedPlantingSummary:
    """Summary statistics"""
    total_varieties: int
    total_seed_value: float
    varieties_by_crop: Dict[str, int]
    total_acres_planted: float
    acres_by_crop: Dict[str, float]
    avg_stand_percentage: Optional[float]
    planting_records_count: int
    emergence_checks_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "SeedPlantingSummary":
        return cls(
            total_varieties=data.get("total_varieties", 0),
            total_seed_value=float(data.get("total_seed_value", 0)),
            varieties_by_crop=data.get("varieties_by_crop", {}),
            total_acres_planted=float(data.get("total_acres_planted", 0)),
            acres_by_crop=data.get("acres_by_crop", {}),
            avg_stand_percentage=data.get("avg_stand_percentage"),
            planting_records_count=data.get("planting_records_count", 0),
            emergence_checks_count=data.get("emergence_checks_count", 0)
        )


class SeedPlantingAPI:
    """API client for seed & planting operations."""

    CROP_TYPES = [
        ("corn", "Corn"), ("soybean", "Soybean"), ("wheat", "Wheat"),
        ("cotton", "Cotton"), ("rice", "Rice"), ("sorghum", "Sorghum"),
        ("alfalfa", "Alfalfa"), ("hay", "Hay"), ("oats", "Oats"),
        ("barley", "Barley"), ("sunflower", "Sunflower"), ("canola", "Canola"),
        ("other", "Other")
    ]

    QUANTITY_UNITS = [
        ("bags", "Bags"), ("units", "Units"), ("lbs", "Pounds"),
        ("bushels", "Bushels"), ("cwt", "CWT")
    ]

    RATE_UNITS = [
        ("seeds/acre", "Seeds/Acre"), ("lbs/acre", "Lbs/Acre"),
        ("bushels/acre", "Bu/Acre"), ("units/acre", "Units/Acre"),
        ("bags/acre", "Bags/Acre")
    ]

    PLANTING_STATUSES = [
        ("planned", "Planned"), ("in_progress", "In Progress"),
        ("completed", "Completed"), ("replant_needed", "Replant Needed")
    ]

    SOIL_MOISTURE = [
        ("dry", "Dry"), ("adequate", "Adequate"),
        ("wet", "Wet"), ("saturated", "Saturated")
    ]

    def __init__(self):
        self._client = get_api_client()

    def get_summary(self, year: Optional[int] = None) -> Tuple[Optional[SeedPlantingSummary], Optional[str]]:
        """Get seed & planting summary."""
        try:
            params = {"year": year} if year else {}
            response = self._client.get("/api/v1/seeds/summary", params=params)
            if response.status_code == 200:
                return SeedPlantingSummary.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    # Seed Inventory
    def list_seeds(
        self,
        crop_type: Optional[str] = None,
        brand: Optional[str] = None,
        search: Optional[str] = None,
        in_stock_only: bool = False
    ) -> Tuple[List[SeedInfo], Optional[str]]:
        """List seed inventory."""
        try:
            params = {}
            if crop_type:
                params["crop_type"] = crop_type
            if brand:
                params["brand"] = brand
            if search:
                params["search"] = search
            if in_stock_only:
                params["in_stock_only"] = "true"

            response = self._client.get("/api/v1/seeds", params=params)
            if response.status_code == 200:
                data = response.json()
                seeds = [SeedInfo.from_dict(s) for s in data.get("seeds", [])]
                return seeds, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_seed(self, **kwargs) -> Tuple[Optional[SeedInfo], Optional[str]]:
        """Create a seed inventory item."""
        try:
            response = self._client.post("/api/v1/seeds", json=kwargs)
            if response.status_code in (200, 201):
                return SeedInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    def update_seed(self, seed_id: int, **kwargs) -> Tuple[Optional[SeedInfo], Optional[str]]:
        """Update a seed inventory item."""
        try:
            response = self._client.put(f"/api/v1/seeds/{seed_id}", json=kwargs)
            if response.status_code == 200:
                return SeedInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    def delete_seed(self, seed_id: int) -> Tuple[bool, Optional[str]]:
        """Delete a seed inventory item."""
        try:
            response = self._client.delete(f"/api/v1/seeds/{seed_id}")
            return response.status_code in (200, 204), None
        except Exception as e:
            return False, str(e)

    def get_traits(self, crop_type: str) -> Tuple[List[str], Optional[str]]:
        """Get trait packages for a crop type."""
        try:
            response = self._client.get(f"/api/v1/seeds/traits/{crop_type}")
            if response.status_code == 200:
                return response.json().get("traits", []), None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    # Planting Records
    def list_plantings(
        self,
        field_id: Optional[int] = None,
        crop_type: Optional[str] = None,
        status: Optional[str] = None,
        year: Optional[int] = None
    ) -> Tuple[List[PlantingInfo], Optional[str]]:
        """List planting records."""
        try:
            params = {}
            if field_id:
                params["field_id"] = field_id
            if crop_type:
                params["crop_type"] = crop_type
            if status:
                params["status"] = status
            if year:
                params["year"] = year

            response = self._client.get("/api/v1/planting", params=params)
            if response.status_code == 200:
                data = response.json()
                plantings = [PlantingInfo.from_dict(p) for p in data.get("plantings", [])]
                return plantings, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_planting(self, **kwargs) -> Tuple[Optional[PlantingInfo], Optional[str]]:
        """Create a planting record."""
        try:
            response = self._client.post("/api/v1/planting", json=kwargs)
            if response.status_code in (200, 201):
                return PlantingInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)

    def update_planting(self, planting_id: int, **kwargs) -> Tuple[Optional[PlantingInfo], Optional[str]]:
        """Update a planting record."""
        try:
            response = self._client.put(f"/api/v1/planting/{planting_id}", json=kwargs)
            if response.status_code == 200:
                return PlantingInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code}"
        except Exception as e:
            return None, str(e)

    # Emergence Records
    def list_emergence(self, planting_record_id: int) -> Tuple[List[EmergenceInfo], Optional[str]]:
        """List emergence records for a planting."""
        try:
            response = self._client.get(f"/api/v1/planting/{planting_record_id}/emergence")
            if response.status_code == 200:
                data = response.json()
                records = [EmergenceInfo.from_dict(e) for e in data.get("records", [])]
                return records, None
            return [], f"Error: {response.status_code}"
        except Exception as e:
            return [], str(e)

    def create_emergence(self, **kwargs) -> Tuple[Optional[EmergenceInfo], Optional[str]]:
        """Create an emergence record."""
        try:
            response = self._client.post("/api/v1/planting/emergence", json=kwargs)
            if response.status_code in (200, 201):
                return EmergenceInfo.from_dict(response.json()), None
            return None, f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return None, str(e)


_seed_planting_api: Optional[SeedPlantingAPI] = None


def get_seed_planting_api() -> SeedPlantingAPI:
    global _seed_planting_api
    if _seed_planting_api is None:
        _seed_planting_api = SeedPlantingAPI()
    return _seed_planting_api
