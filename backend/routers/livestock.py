"""
Livestock Management Router
AgTools v6.13.0

Handles:
- Animal management
- Health records
- Breeding records
- Weight tracking
- Sales management
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from middleware.auth_middleware import get_current_active_user, require_manager, AuthenticatedUser

router = APIRouter(prefix="/api/v1/livestock", tags=["Livestock"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class AnimalResponse(BaseModel):
    id: int
    tag_number: str
    species: str
    breed: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = "active"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class AnimalListResponse(BaseModel):
    animals: List[AnimalResponse]
    total: int

class HealthRecordResponse(BaseModel):
    id: int
    animal_id: int
    record_type: str
    record_date: date
    description: str
    treatment: Optional[str] = None
    vet_name: Optional[str] = None
    cost: Optional[float] = None
    created_at: Optional[datetime] = None

class HealthRecordListResponse(BaseModel):
    records: List[HealthRecordResponse]
    total: int

class BreedingRecordResponse(BaseModel):
    id: int
    female_id: int
    male_id: Optional[int] = None
    breeding_date: date
    method: str
    expected_due: Optional[date] = None
    actual_birth_date: Optional[date] = None
    offspring_count: Optional[int] = None
    status: Optional[str] = "pending"
    created_at: Optional[datetime] = None

class BreedingRecordListResponse(BaseModel):
    records: List[BreedingRecordResponse]
    total: int

class WeightRecordResponse(BaseModel):
    id: int
    animal_id: int
    weight: float
    weight_date: date
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class WeightRecordListResponse(BaseModel):
    records: List[WeightRecordResponse]
    total: int

class SaleRecordResponse(BaseModel):
    id: int
    animal_id: int
    sale_date: date
    sale_price: float
    buyer: Optional[str] = None
    weight_at_sale: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class SaleRecordListResponse(BaseModel):
    sales: List[SaleRecordResponse]
    total: int

class TimelineEventResponse(BaseModel):
    event_type: str
    event_date: date
    description: str
    details: Optional[Dict[str, Any]] = None

class AnimalTimelineResponse(BaseModel):
    animal_id: int
    events: List[TimelineEventResponse]


# ============================================================================
# ANIMAL MANAGEMENT
# ============================================================================

@router.get("", response_model=AnimalListResponse, tags=["Livestock"])
async def list_animals(
    species: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List all animals."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    return service.list_animals(
        species=species,
        status=status,
        location=location
    )


@router.post("", response_model=AnimalResponse, tags=["Livestock"])
async def create_animal(
    tag_number: str,
    species: str,
    breed: Optional[str] = None,
    birth_date: Optional[date] = None,
    sex: Optional[str] = None,
    location: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a new animal record."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    result = service.create_animal(
        tag_number=tag_number,
        species=species,
        breed=breed,
        birth_date=birth_date,
        sex=sex,
        location=location,
        created_by=user.id
    )

    return result


# IMPORTANT: Static routes must come BEFORE /{animal_id} to avoid route conflicts

@router.get("/health", response_model=HealthRecordListResponse, tags=["Livestock Health"])
async def list_health_records(
    animal_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List health records."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    return service.list_health_records(
        animal_id=animal_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/health", response_model=HealthRecordResponse, tags=["Livestock Health"])
async def create_health_record(
    animal_id: int,
    record_type: str,
    record_date: date,
    description: str,
    treatment: Optional[str] = None,
    vet_name: Optional[str] = None,
    cost: Optional[float] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a health record."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    result = service.create_health_record(
        animal_id=animal_id,
        record_type=record_type,
        record_date=record_date,
        description=description,
        treatment=treatment,
        vet_name=vet_name,
        cost=cost,
        created_by=user.id
    )

    return result


@router.get("/breeding", response_model=BreedingRecordListResponse, tags=["Livestock Breeding"])
async def list_breeding_records(
    animal_id: Optional[int] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List breeding records."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    return service.list_breeding_records(animal_id=animal_id)


@router.post("/breeding", response_model=BreedingRecordResponse, tags=["Livestock Breeding"])
async def create_breeding_record(
    female_id: int,
    male_id: Optional[int] = None,
    breeding_date: date = None,
    method: str = "natural",
    expected_due: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Create a breeding record."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    result = service.create_breeding_record(
        female_id=female_id,
        male_id=male_id,
        breeding_date=breeding_date,
        method=method,
        expected_due=expected_due,
        created_by=user.id
    )

    return result


@router.get("/weights", response_model=WeightRecordListResponse, tags=["Livestock Weights"])
async def list_weight_records(
    animal_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List weight records."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    return service.list_weight_records(
        animal_id=animal_id,
        date_from=date_from,
        date_to=date_to
    )


@router.post("/weights", response_model=WeightRecordResponse, tags=["Livestock Weights"])
async def record_weight(
    animal_id: int,
    weight: float,
    weight_date: date,
    notes: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record an animal weight."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    result = service.record_weight(
        animal_id=animal_id,
        weight=weight,
        weight_date=weight_date,
        notes=notes,
        created_by=user.id
    )

    return result


@router.get("/sales", response_model=SaleRecordListResponse, tags=["Livestock Sales"])
async def list_sales(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """List livestock sales."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    return service.list_sales(
        date_from=date_from,
        date_to=date_to
    )


@router.post("/sales", response_model=SaleRecordResponse, tags=["Livestock Sales"])
async def record_sale(
    animal_id: int,
    sale_date: date,
    sale_price: float,
    buyer: Optional[str] = None,
    weight_at_sale: Optional[float] = None,
    notes: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Record a livestock sale."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    result = service.record_sale(
        animal_id=animal_id,
        sale_date=sale_date,
        sale_price=sale_price,
        buyer=buyer,
        weight_at_sale=weight_at_sale,
        notes=notes,
        created_by=user.id
    )

    return result


# Dynamic route must come AFTER static routes

@router.get("/{animal_id}", response_model=AnimalResponse, tags=["Livestock"])
async def get_animal(
    animal_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get animal details."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    animal = service.get_animal(animal_id)

    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    return animal


@router.put("/{animal_id}", response_model=AnimalResponse, tags=["Livestock"])
async def update_animal(
    animal_id: int,
    tag_number: Optional[str] = None,
    breed: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Update animal record."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    result = service.update_animal(
        animal_id=animal_id,
        tag_number=tag_number,
        breed=breed,
        status=status,
        location=location,
        notes=notes,
        updated_by=user.id
    )

    if not result:
        raise HTTPException(status_code=404, detail="Animal not found")

    return result


@router.get("/{animal_id}/timeline", response_model=AnimalTimelineResponse, tags=["Livestock"])
async def get_animal_timeline(
    animal_id: int,
    user: AuthenticatedUser = Depends(get_current_active_user)
):
    """Get complete timeline for an animal."""
    from services.livestock_service import get_livestock_service

    service = get_livestock_service()
    return service.get_animal_timeline(animal_id)
