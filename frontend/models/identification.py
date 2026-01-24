"""
Pest and Disease Identification Data Models

Data classes for pest/disease identification requests and responses.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class CropType(str, Enum):
    """Supported crop types for identification."""
    CORN = "corn"
    SOYBEAN = "soybean"
    WHEAT = "wheat"


class GrowthStage(str, Enum):
    """Crop growth stages."""
    # Corn stages
    VE = "VE"
    V1 = "V1"
    V2 = "V2"
    V3 = "V3"
    V4 = "V4"
    V6 = "V6"
    VT = "VT"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"
    # Soybean stages
    VC = "VC"


class PestType(str, Enum):
    """Types of pests."""
    INSECT = "insect"
    MITE = "mite"
    NEMATODE = "nematode"
    SLUG = "slug"
    RODENT = "rodent"


class PathogenType(str, Enum):
    """Types of disease pathogens."""
    FUNGAL = "fungal"
    BACTERIAL = "bacterial"
    VIRAL = "viral"
    OOMYCETE = "oomycete"


# Common pest symptoms for symptom selection
PEST_SYMPTOMS = [
    "Leaf feeding/chewing damage",
    "Leaf holes",
    "Leaf skeletonization",
    "Leaf curling",
    "Wilting",
    "Stunted growth",
    "Root damage",
    "Stem boring",
    "Silk clipping",
    "Pod/ear damage",
    "Defoliation",
    "Honeydew/sooty mold",
    "Webbing present",
    "Visible insects",
    "Frass present",
    "Galls",
    "Tunneling in stems",
    "Discolored roots",
    "Stand loss",
    "Lodging",
]

# Common disease symptoms for symptom selection
DISEASE_SYMPTOMS = [
    "Leaf spots",
    "Leaf lesions",
    "Gray/tan lesions",
    "Brown lesions",
    "Yellow halos around lesions",
    "Leaf blight",
    "Leaf rust/pustules",
    "White/gray mold",
    "Stem rot",
    "Root rot",
    "Wilting",
    "Premature death",
    "Stunted growth",
    "Discolored vascular tissue",
    "Ear/pod rot",
    "Seed discoloration",
    "Cankers",
    "Galls",
    "Mosaic patterns",
    "Chlorosis/yellowing",
]


@dataclass
class PestInfo:
    """Information about an identified pest."""
    id: int
    common_name: str
    scientific_name: str
    description: str
    damage_symptoms: str
    identification_features: str
    confidence: Optional[float] = None
    economic_threshold: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name,
            "description": self.description,
            "damage_symptoms": self.damage_symptoms,
            "identification_features": self.identification_features,
            "confidence": self.confidence,
            "economic_threshold": self.economic_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PestInfo":
        return cls(
            id=data.get("id", 0),
            common_name=data.get("common_name", ""),
            scientific_name=data.get("scientific_name", ""),
            description=data.get("description", ""),
            damage_symptoms=data.get("damage_symptoms", ""),
            identification_features=data.get("identification_features", ""),
            confidence=data.get("confidence"),
            economic_threshold=data.get("economic_threshold"),
        )


@dataclass
class DiseaseInfo:
    """Information about an identified disease."""
    id: int
    common_name: str
    scientific_name: str
    description: str
    symptoms: str
    favorable_conditions: str
    confidence: Optional[float] = None
    management: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name,
            "description": self.description,
            "symptoms": self.symptoms,
            "favorable_conditions": self.favorable_conditions,
            "confidence": self.confidence,
            "management": self.management,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiseaseInfo":
        return cls(
            id=data.get("id", 0),
            common_name=data.get("common_name", ""),
            scientific_name=data.get("scientific_name", ""),
            description=data.get("description", ""),
            symptoms=data.get("symptoms", ""),
            favorable_conditions=data.get("favorable_conditions", ""),
            confidence=data.get("confidence"),
            management=data.get("management"),
        )


@dataclass
class PestIdentificationRequest:
    """Request for pest identification."""
    crop: CropType
    growth_stage: GrowthStage
    symptoms: List[str]
    location_description: Optional[str] = None
    severity_rating: Optional[int] = None
    field_conditions: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "crop": self.crop.value if isinstance(self.crop, CropType) else self.crop,
            "growth_stage": self.growth_stage.value if isinstance(self.growth_stage, GrowthStage) else self.growth_stage,
            "symptoms": self.symptoms,
            "location_description": self.location_description,
            "severity_rating": self.severity_rating,
            "field_conditions": self.field_conditions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PestIdentificationRequest":
        crop = data.get("crop", "corn")
        growth_stage = data.get("growth_stage", "V6")
        return cls(
            crop=CropType(crop) if isinstance(crop, str) else crop,
            growth_stage=GrowthStage(growth_stage) if isinstance(growth_stage, str) else growth_stage,
            symptoms=data.get("symptoms", []),
            location_description=data.get("location_description"),
            severity_rating=data.get("severity_rating"),
            field_conditions=data.get("field_conditions"),
        )


@dataclass
class DiseaseIdentificationRequest:
    """Request for disease identification."""
    crop: CropType
    growth_stage: GrowthStage
    symptoms: List[str]
    weather_conditions: Optional[str] = None
    location_description: Optional[str] = None
    severity_rating: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "crop": self.crop.value if isinstance(self.crop, CropType) else self.crop,
            "growth_stage": self.growth_stage.value if isinstance(self.growth_stage, GrowthStage) else self.growth_stage,
            "symptoms": self.symptoms,
            "weather_conditions": self.weather_conditions,
            "location_description": self.location_description,
            "severity_rating": self.severity_rating,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiseaseIdentificationRequest":
        crop = data.get("crop", "corn")
        growth_stage = data.get("growth_stage", "V6")
        return cls(
            crop=CropType(crop) if isinstance(crop, str) else crop,
            growth_stage=GrowthStage(growth_stage) if isinstance(growth_stage, str) else growth_stage,
            symptoms=data.get("symptoms", []),
            weather_conditions=data.get("weather_conditions"),
            location_description=data.get("location_description"),
            severity_rating=data.get("severity_rating"),
        )


@dataclass
class PestListItem:
    """Summary item for pest listing."""
    id: int
    common_name: str
    scientific_name: str
    crops_affected: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name,
            "crops_affected": self.crops_affected,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PestListItem":
        return cls(
            id=data.get("id", 0),
            common_name=data.get("common_name", ""),
            scientific_name=data.get("scientific_name", ""),
            crops_affected=data.get("crops_affected", []),
        )


@dataclass
class DiseaseListItem:
    """Summary item for disease listing."""
    id: int
    common_name: str
    scientific_name: str
    crops_affected: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name,
            "crops_affected": self.crops_affected,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiseaseListItem":
        return cls(
            id=data.get("id", 0),
            common_name=data.get("common_name", ""),
            scientific_name=data.get("scientific_name", ""),
            crops_affected=data.get("crops_affected", []),
        )


@dataclass
class PestListResponse:
    """Response containing list of pests."""
    pests: List[PestListItem] = field(default_factory=list)
    total: int = 0

    def to_dict(self) -> dict:
        return {
            "pests": [p.to_dict() for p in self.pests],
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PestListResponse":
        # Handle both list response and dict with 'pests' key
        if isinstance(data, list):
            pests = [PestListItem.from_dict(p) for p in data]
            return cls(pests=pests, total=len(pests))
        else:
            pests_data = data.get("pests", data.get("items", []))
            pests = [PestListItem.from_dict(p) for p in pests_data]
            return cls(
                pests=pests,
                total=data.get("total", len(pests)),
            )


@dataclass
class DiseaseListResponse:
    """Response containing list of diseases."""
    diseases: List[DiseaseListItem] = field(default_factory=list)
    total: int = 0

    def to_dict(self) -> dict:
        return {
            "diseases": [d.to_dict() for d in self.diseases],
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiseaseListResponse":
        # Handle both list response and dict with 'diseases' key
        if isinstance(data, list):
            diseases = [DiseaseListItem.from_dict(d) for d in data]
            return cls(diseases=diseases, total=len(diseases))
        else:
            diseases_data = data.get("diseases", data.get("items", []))
            diseases = [DiseaseListItem.from_dict(d) for d in diseases_data]
            return cls(
                diseases=diseases,
                total=data.get("total", len(diseases)),
            )
