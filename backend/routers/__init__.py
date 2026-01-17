"""
FastAPI Routers Module
AgTools v6.13.0

Organized API endpoints as FastAPI routers for better maintainability.
"""

from .auth import router as auth_router
from .fields import router as fields_router
from .equipment import router as equipment_router
from .inventory import router as inventory_router
from .tasks import router as tasks_router
from .optimization import router as optimization_router
from .reports import router as reports_router
from .ai_ml import router as ai_ml_router
from .grants import router as grants_router
from .sustainability import router as sustainability_router
from .farm_business import router as farm_business_router
from .genfin import router as genfin_router
from .livestock import router as livestock_router
from .crops import router as crops_router
from .converters import router as converters_router

__all__ = [
    'auth_router',
    'fields_router',
    'equipment_router',
    'inventory_router',
    'tasks_router',
    'optimization_router',
    'reports_router',
    'ai_ml_router',
    'grants_router',
    'sustainability_router',
    'farm_business_router',
    'genfin_router',
    'livestock_router',
    'crops_router',
    'converters_router',
]
