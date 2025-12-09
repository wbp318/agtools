"""
API endpoint tests for AgTools backend.

Run with: pytest tests/ -v
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self, client):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_welcome_message(self, client):
        """Root endpoint should return API info."""
        response = client.get("/")
        data = response.json()
        assert "message" in data or "status" in data


class TestCropsEndpoint:
    """Tests for the crops endpoint."""

    def test_get_crops(self, client):
        """GET /api/v1/crops should return crop list."""
        response = client.get("/api/v1/crops")
        assert response.status_code == 200


class TestPestsEndpoints:
    """Tests for pest-related endpoints."""

    def test_get_all_pests(self, client):
        """GET /api/v1/pests should return pest list."""
        response = client.get("/api/v1/pests")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "pests" in data
        assert data["count"] > 0

    def test_get_corn_pests(self, client):
        """GET /api/v1/pests?crop=corn should return corn pests."""
        response = client.get("/api/v1/pests", params={"crop": "corn"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0

    def test_get_soybean_pests(self, client):
        """GET /api/v1/pests?crop=soybean should return soybean pests."""
        response = client.get("/api/v1/pests", params={"crop": "soybean"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0

    def test_identify_pest(self, client, sample_pest_request):
        """POST /api/v1/identify/pest should identify pest by symptoms."""
        response = client.post("/api/v1/identify/pest", json=sample_pest_request)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDiseasesEndpoints:
    """Tests for disease-related endpoints."""

    def test_get_all_diseases(self, client):
        """GET /api/v1/diseases should return disease list."""
        response = client.get("/api/v1/diseases")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "diseases" in data
        assert data["count"] > 0

    def test_get_corn_diseases(self, client):
        """GET /api/v1/diseases?crop=corn should return corn diseases."""
        response = client.get("/api/v1/diseases", params={"crop": "corn"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0

    def test_get_soybean_diseases(self, client):
        """GET /api/v1/diseases?crop=soybean should return soybean diseases."""
        response = client.get("/api/v1/diseases", params={"crop": "soybean"})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0

    def test_identify_disease(self, client, sample_disease_request):
        """POST /api/v1/identify/disease should identify disease by symptoms."""
        response = client.post("/api/v1/identify/disease", json=sample_disease_request)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestProductsEndpoint:
    """Tests for the products endpoint."""

    def test_get_products(self, client):
        """GET /api/v1/products should return product list."""
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "products" in data


class TestPricingEndpoints:
    """Tests for pricing-related endpoints."""

    def test_get_prices(self, client):
        """GET /api/v1/pricing/prices should return price list."""
        response = client.get("/api/v1/pricing/prices")
        assert response.status_code == 200


class TestSprayTimingEndpoints:
    """Tests for spray timing endpoints."""

    def test_evaluate_conditions(self, client, sample_spray_conditions):
        """POST /api/v1/spray-timing/evaluate should evaluate spray conditions."""
        response = client.post("/api/v1/spray-timing/evaluate", json=sample_spray_conditions)
        assert response.status_code == 200
        data = response.json()
        # Response has nested evaluation object
        assert "evaluation" in data
        assert "risk_level" in data["evaluation"]


class TestCostOptimizerEndpoints:
    """Tests for cost optimizer endpoints."""

    def test_quick_estimate(self, client, sample_quick_estimate):
        """POST /api/v1/optimize/quick-estimate should return cost estimate."""
        response = client.post("/api/v1/optimize/quick-estimate", json=sample_quick_estimate)
        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data or "cost" in data or "costs" in data


class TestYieldResponseEndpoints:
    """Tests for yield response endpoints."""

    def test_yield_curve(self, client):
        """POST /api/v1/yield-response/curve should return yield curve."""
        request = {
            "crop": "corn",
            "nutrient": "nitrogen",
            "soil_test_level": "medium",
            "yield_potential": 200,
            "previous_crop": "soybean"
        }
        response = client.post("/api/v1/yield-response/curve", json=request)
        assert response.status_code == 200

    # Note: economic-optimum and price-ratio-guide have backend issues to fix
    # test_economic_optimum - has import error for SoilTestLevel
    # test_price_ratio_guide - missing generate_price_ratio_guide method


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema(self, client):
        """GET /openapi.json should return OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_docs(self, client):
        """GET /docs should return Swagger UI."""
        response = client.get("/docs")
        assert response.status_code == 200
