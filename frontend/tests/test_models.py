"""
Data Model Tests

Tests for frontend data models - enums, dataclasses, serialization.
"""

import sys
import os

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestYieldResponseModels:
    """Tests for yield response data models."""

    def test_crop_enum(self):
        """Test Crop enum values."""
        from models.yield_response import Crop

        assert Crop.CORN.value == "corn"
        assert Crop.SOYBEAN.value == "soybean"
        assert Crop.WHEAT.value == "wheat"

    def test_nutrient_enum(self):
        """Test Nutrient enum values."""
        from models.yield_response import Nutrient

        assert Nutrient.NITROGEN.value == "nitrogen"
        assert Nutrient.PHOSPHORUS.value == "phosphorus"
        assert Nutrient.POTASSIUM.value == "potassium"

    def test_soil_test_level_enum(self):
        """Test SoilTestLevel enum values."""
        from models.yield_response import SoilTestLevel

        assert SoilTestLevel.VERY_LOW is not None
        assert SoilTestLevel.LOW is not None
        assert SoilTestLevel.MEDIUM is not None
        assert SoilTestLevel.HIGH is not None

    def test_response_model_enum(self):
        """Test ResponseModel enum values."""
        from models.yield_response import ResponseModel

        # Check that model types exist
        assert hasattr(ResponseModel, 'QUADRATIC_PLATEAU') or hasattr(ResponseModel, 'QUADRATIC')

    def test_yield_curve_request_creation(self):
        """Test YieldCurveRequest dataclass."""
        from models.yield_response import YieldCurveRequest

        request = YieldCurveRequest(
            crop="corn",
            nutrient="nitrogen",
            yield_potential=200
        )
        assert request.crop == "corn"
        assert request.nutrient == "nitrogen"
        assert request.yield_potential == 200

    def test_yield_curve_point_creation(self):
        """Test YieldCurvePoint dataclass."""
        from models.yield_response import YieldCurvePoint

        point = YieldCurvePoint(
            rate_lb_per_acre=150,
            yield_bu_per_acre=180.5
        )
        assert point.rate_lb_per_acre == 150
        assert point.yield_bu_per_acre == 180.5


class TestIdentificationModels:
    """Tests for pest/disease identification models."""

    def test_crop_type_enum(self):
        """Test CropType enum values."""
        from models.identification import CropType

        assert CropType.CORN.value == "corn"
        assert CropType.SOYBEAN.value == "soybean"
        assert CropType.WHEAT.value == "wheat"

    def test_growth_stage_enum(self):
        """Test GrowthStage enum values."""
        from models.identification import GrowthStage

        # Corn stages
        assert GrowthStage.VE.value == "VE"
        assert GrowthStage.V6.value == "V6"
        assert GrowthStage.VT.value == "VT"
        assert GrowthStage.R1.value == "R1"

    def test_pest_type_enum(self):
        """Test PestType enum values."""
        from models.identification import PestType

        assert PestType.INSECT.value == "insect"
        assert PestType.MITE.value == "mite"
        assert PestType.NEMATODE.value == "nematode"

    def test_pathogen_type_enum(self):
        """Test PathogenType enum values."""
        from models.identification import PathogenType

        assert PathogenType.FUNGAL.value == "fungal"
        assert PathogenType.BACTERIAL.value == "bacterial"
        assert PathogenType.VIRAL.value == "viral"

    def test_pest_symptoms_list(self):
        """Test PEST_SYMPTOMS constant."""
        from models.identification import PEST_SYMPTOMS

        assert isinstance(PEST_SYMPTOMS, list)
        assert len(PEST_SYMPTOMS) > 0
        assert "Leaf feeding/chewing damage" in PEST_SYMPTOMS

    def test_disease_symptoms_list(self):
        """Test DISEASE_SYMPTOMS constant."""
        from models.identification import DISEASE_SYMPTOMS

        assert isinstance(DISEASE_SYMPTOMS, list)
        assert len(DISEASE_SYMPTOMS) > 0
        assert "Leaf spots" in DISEASE_SYMPTOMS

    def test_pest_info_from_dict(self):
        """Test PestInfo deserialization."""
        from models.identification import PestInfo

        data = {
            "id": 1,
            "common_name": "Corn Rootworm",
            "scientific_name": "Diabrotica virgifera",
            "description": "Major corn pest",
            "damage_symptoms": "Root pruning",
            "identification_features": "Yellow beetle"
        }
        pest = PestInfo.from_dict(data)

        assert pest.id == 1
        assert pest.common_name == "Corn Rootworm"
        assert pest.scientific_name == "Diabrotica virgifera"

    def test_pest_info_to_dict(self):
        """Test PestInfo serialization."""
        from models.identification import PestInfo

        pest = PestInfo(
            id=1,
            common_name="Aphid",
            scientific_name="Aphis gossypii",
            description="Sap-sucking insect",
            damage_symptoms="Honeydew, stunting",
            identification_features="Small, soft-bodied"
        )
        data = pest.to_dict()

        assert data["id"] == 1
        assert data["common_name"] == "Aphid"

    def test_disease_info_from_dict(self):
        """Test DiseaseInfo deserialization."""
        from models.identification import DiseaseInfo

        data = {
            "id": 1,
            "common_name": "Gray Leaf Spot",
            "scientific_name": "Cercospora zeae-maydis",
            "description": "Foliar disease of corn",
            "symptoms": "Rectangular gray lesions",
            "favorable_conditions": "Warm, humid"
        }
        disease = DiseaseInfo.from_dict(data)

        assert disease.id == 1
        assert disease.common_name == "Gray Leaf Spot"

    def test_disease_info_to_dict(self):
        """Test DiseaseInfo serialization."""
        from models.identification import DiseaseInfo

        disease = DiseaseInfo(
            id=1,
            common_name="Northern Corn Leaf Blight",
            scientific_name="Exserohilum turcicum",
            description="Foliar disease",
            symptoms="Cigar-shaped lesions",
            favorable_conditions="Cool, wet"
        )
        data = disease.to_dict()

        assert data["id"] == 1
        assert data["common_name"] == "Northern Corn Leaf Blight"

    def test_pest_identification_request(self):
        """Test PestIdentificationRequest dataclass."""
        from models.identification import (
            PestIdentificationRequest, CropType, GrowthStage
        )

        request = PestIdentificationRequest(
            crop=CropType.CORN,
            growth_stage=GrowthStage.V6,
            symptoms=["Leaf feeding/chewing damage", "Visible insects"]
        )
        assert request.crop == CropType.CORN
        assert len(request.symptoms) == 2

    def test_pest_identification_request_to_dict(self):
        """Test PestIdentificationRequest serialization."""
        from models.identification import (
            PestIdentificationRequest, CropType, GrowthStage
        )

        request = PestIdentificationRequest(
            crop=CropType.SOYBEAN,
            growth_stage=GrowthStage.R1,
            symptoms=["Defoliation"]
        )
        data = request.to_dict()

        assert data["crop"] == "soybean"
        assert data["growth_stage"] == "R1"

    def test_disease_identification_request(self):
        """Test DiseaseIdentificationRequest dataclass."""
        from models.identification import (
            DiseaseIdentificationRequest, CropType, GrowthStage
        )

        request = DiseaseIdentificationRequest(
            crop=CropType.WHEAT,
            growth_stage=GrowthStage.R2,
            symptoms=["Leaf rust/pustules"]
        )
        assert request.crop == CropType.WHEAT

    def test_pest_list_response_from_list(self):
        """Test PestListResponse from list input."""
        from models.identification import PestListResponse

        data = [
            {"id": 1, "common_name": "Pest1", "scientific_name": "Sci1"},
            {"id": 2, "common_name": "Pest2", "scientific_name": "Sci2"}
        ]
        response = PestListResponse.from_dict(data)

        assert response.total == 2
        assert len(response.pests) == 2

    def test_disease_list_response_from_dict(self):
        """Test DiseaseListResponse from dict input."""
        from models.identification import DiseaseListResponse

        data = {
            "diseases": [
                {"id": 1, "common_name": "Disease1", "scientific_name": "Sci1"}
            ],
            "total": 1
        }
        response = DiseaseListResponse.from_dict(data)

        assert response.total == 1
        assert len(response.diseases) == 1


class TestSprayModels:
    """Tests for spray data models."""

    def test_spray_model_imports(self):
        """Test spray models import correctly."""
        from models.spray import WeatherCondition, RiskLevel, SprayType
        assert WeatherCondition is not None
        assert RiskLevel is not None
        assert SprayType is not None

    def test_weather_condition_creation(self):
        """Test WeatherCondition dataclass."""
        from models.spray import WeatherCondition

        weather = WeatherCondition(
            temp_f=75.0,
            humidity_pct=60.0,
            wind_mph=8.0
        )
        assert weather.temp_f == 75.0
        assert weather.humidity_pct == 60.0

    def test_risk_level_enum(self):
        """Test RiskLevel enum values."""
        from models.spray import RiskLevel

        assert RiskLevel.EXCELLENT is not None
        assert RiskLevel.GOOD is not None
        assert RiskLevel.MARGINAL is not None
        assert RiskLevel.POOR is not None


class TestPricingModels:
    """Tests for pricing data models."""

    def test_pricing_model_imports(self):
        """Test pricing models import correctly."""
        from models.pricing import ProductPrice, GetPricesResponse
        assert ProductPrice is not None
        assert GetPricesResponse is not None

    def test_product_price_from_dict(self):
        """Test ProductPrice deserialization."""
        from models.pricing import ProductPrice

        data = {
            "price": 0.65,
            "unit": "lb",
            "description": "Nitrogen fertilizer",
            "category": "fertilizer"
        }
        price = ProductPrice.from_dict("nitrogen_28", data)
        assert price.product_id == "nitrogen_28"
        assert price.price == 0.65

    def test_product_category_enum(self):
        """Test ProductCategory enum values."""
        from models.pricing import ProductCategory

        assert ProductCategory.FERTILIZER.value == "fertilizer"
        assert ProductCategory.SEED.value == "seed"


class TestCostOptimizerModels:
    """Tests for cost optimizer data models."""

    def test_cost_optimizer_model_imports(self):
        """Test cost optimizer models import correctly."""
        from models.cost_optimizer import QuickEstimateRequest, QuickEstimateResponse
        assert QuickEstimateRequest is not None
        assert QuickEstimateResponse is not None

    def test_quick_estimate_request(self):
        """Test QuickEstimateRequest dataclass."""
        from models.cost_optimizer import QuickEstimateRequest

        request = QuickEstimateRequest(
            acres=500,
            crop="corn",
            is_irrigated=True
        )
        assert request.acres == 500
        assert request.crop == "corn"

    def test_optimization_priority_enum(self):
        """Test OptimizationPriority enum values."""
        from models.cost_optimizer import OptimizationPriority

        assert OptimizationPriority.COST_REDUCTION is not None
        assert OptimizationPriority.ROI_MAXIMIZATION is not None


class TestMeasurementConverterModels:
    """Tests for measurement converter data models."""

    def test_measurement_converter_imports(self):
        """Test measurement converter models import correctly."""
        from models.measurement_converter import ConversionResult, UnitType
        assert ConversionResult is not None
        assert UnitType is not None

    def test_conversion_result_creation(self):
        """Test ConversionResult dataclass."""
        from models.measurement_converter import ConversionResult

        result = ConversionResult(
            imperial_value=1.5,
            imperial_unit="gal/acre",
            imperial_display="1.5 gal/acre",
            metric_value=14.03,
            metric_unit="L/ha",
            metric_display="14.03 L/ha"
        )
        assert result.imperial_value == 1.5
        assert result.metric_value == 14.03

    def test_unit_type_enum(self):
        """Test UnitType enum values."""
        from models.measurement_converter import UnitType

        assert UnitType.APPLICATION_RATE_VOLUME is not None
        assert UnitType.WEIGHT is not None
        assert UnitType.AREA is not None
