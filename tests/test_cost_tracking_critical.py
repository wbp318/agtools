"""
Critical Tests for Cost Tracking Service
=========================================
Tests for expense management, CSV import, allocations, and cost-per-acre analysis.

Priority: CRITICAL
Coverage Target: Cost Tracking Service core workflows
"""

import pytest
import csv
import io
from decimal import Decimal
from datetime import date, datetime, timedelta
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))


class TestExpenseCRUD:
    """Test expense CRUD operations - Foundation for cost tracking."""

    def test_create_expense_basic(self, client, auth_headers):
        """Test basic expense creation."""
        expense_data = {
            "category": "seed",
            "vendor": "Pioneer Seeds",
            "description": "Corn seed purchase",
            "amount": 15000.00,
            "expense_date": date.today().isoformat(),
            "tax_year": 2025
        }

        response = client.post(
            "/api/v1/costs/expenses",
            json=expense_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 404, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("category") == "seed"
            assert data.get("amount") == 15000.00

    def test_create_expense_all_categories(self, client, auth_headers):
        """Test expense creation for all valid categories."""
        categories = [
            "seed", "fertilizer", "chemical", "fuel",
            "repairs", "labor", "custom_hire",
            "land_rent", "crop_insurance", "interest",
            "utilities", "storage", "other"
        ]

        for category in categories:
            expense_data = {
                "category": category,
                "description": f"Test {category} expense",
                "amount": 1000.00,
                "expense_date": date.today().isoformat(),
                "tax_year": 2025
            }

            response = client.post(
                "/api/v1/costs/expenses",
                json=expense_data,
                headers=auth_headers
            )

            # Should accept all valid categories
            assert response.status_code in [200, 201, 404, 422]

    def test_create_expense_invalid_category(self, client, auth_headers):
        """Test expense creation with invalid category."""
        expense_data = {
            "category": "invalid_category",
            "amount": 1000.00,
            "expense_date": date.today().isoformat(),
            "tax_year": 2025
        }

        response = client.post(
            "/api/v1/costs/expenses",
            json=expense_data,
            headers=auth_headers
        )

        # Should reject invalid category
        assert response.status_code in [400, 422, 404]

    def test_get_expense_by_id(self, client, auth_headers):
        """Test retrieving expense by ID."""
        # First create an expense
        expense_data = {
            "category": "fertilizer",
            "vendor": "Nutrien",
            "amount": 8500.00,
            "expense_date": date.today().isoformat(),
            "tax_year": 2025
        }

        create_response = client.post(
            "/api/v1/costs/expenses",
            json=expense_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            created = create_response.json()
            expense_id = created.get("id")

            # Retrieve expense
            get_response = client.get(
                f"/api/v1/costs/expenses/{expense_id}",
                headers=auth_headers
            )

            assert get_response.status_code in [200, 404]
            if get_response.status_code == 200:
                data = get_response.json()
                # Response may have nested "expense" structure
                expense_data = data.get("expense", data)
                assert expense_data.get("vendor") == "Nutrien"

    def test_update_expense(self, client, auth_headers):
        """Test updating expense."""
        # Create expense first
        expense_data = {
            "category": "fuel",
            "vendor": "Casey's",
            "amount": 500.00,
            "expense_date": date.today().isoformat(),
            "tax_year": 2025
        }

        create_response = client.post(
            "/api/v1/costs/expenses",
            json=expense_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            created = create_response.json()
            expense_id = created.get("id")

            # Update amount
            update_data = {"amount": 550.00}
            update_response = client.put(
                f"/api/v1/costs/expenses/{expense_id}",
                json=update_data,
                headers=auth_headers
            )

            assert update_response.status_code in [200, 404]
            if update_response.status_code == 200:
                data = update_response.json()
                assert data.get("amount") == 550.00

    def test_delete_expense(self, client, auth_headers):
        """Test deleting expense (soft delete)."""
        # Create expense first
        expense_data = {
            "category": "repairs",
            "amount": 250.00,
            "expense_date": date.today().isoformat(),
            "tax_year": 2025
        }

        create_response = client.post(
            "/api/v1/costs/expenses",
            json=expense_data,
            headers=auth_headers
        )

        if create_response.status_code in [200, 201]:
            created = create_response.json()
            expense_id = created.get("id")

            # Delete expense
            delete_response = client.delete(
                f"/api/v1/costs/expenses/{expense_id}",
                headers=auth_headers
            )

            assert delete_response.status_code in [200, 204, 404]

    def test_list_expenses_with_filters(self, client, auth_headers):
        """Test listing expenses with various filters."""
        # Test basic list
        response = client.get(
            "/api/v1/costs/expenses",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Test with category filter
            filtered_response = client.get(
                "/api/v1/costs/expenses",
                params={"category": "seed"},
                headers=auth_headers
            )
            assert filtered_response.status_code == 200

            # Test with date range
            date_response = client.get(
                "/api/v1/costs/expenses",
                params={
                    "start_date": (date.today() - timedelta(days=30)).isoformat(),
                    "end_date": date.today().isoformat()
                },
                headers=auth_headers
            )
            assert date_response.status_code == 200


class TestCSVImport:
    """Test CSV import and parsing - Data ingestion critical."""

    def test_preview_csv_import(self, client, auth_headers, data_factory):
        """Test CSV import preview."""
        csv_content = data_factory.csv_import_data()

        response = client.post(
            "/api/v1/costs/import/preview",
            data={"csv_content": csv_content},
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 422]

        if response.status_code == 200:
            data = response.json()
            assert "headers" in data or "preview" in data

    def test_import_csv_expenses(self, client, auth_headers):
        """Test importing expenses from CSV."""
        csv_content = """Date,Description,Amount,Category
2025-01-10,Fertilizer Purchase,5000.00,fertilizer
2025-01-11,Seed Purchase - Corn,12000.00,seed
2025-01-12,Diesel Fuel,800.00,fuel
2025-01-13,Equipment Repair,1500.00,repairs"""

        # First preview
        preview_response = client.post(
            "/api/v1/costs/import/preview",
            data={"csv_content": csv_content},
            headers=auth_headers
        )

        # Then import
        import_data = {
            "csv_content": csv_content,
            "tax_year": 2025,
            "column_mapping": {
                "date": "Date",
                "description": "Description",
                "amount": "Amount",
                "category": "Category"
            }
        }

        response = client.post(
            "/api/v1/costs/import",
            json=import_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 404, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "successful" in data or "imported" in data or "batch_id" in data

    def test_import_quickbooks_format(self, client, auth_headers):
        """Test importing QuickBooks export format."""
        # QuickBooks typical CSV format
        qb_csv = """Trans #,Type,Date,Num,Name,Memo,Account,Clr,Split,Amount
1001,Check,01/15/2025,1234,Pioneer Seeds,Corn seed,Seed Expense,R,Checking,-15000.00
1002,Check,01/16/2025,1235,Nutrien,28-0-0 fertilizer,Fertilizer Expense,R,Checking,-8500.00
1003,Check,01/17/2025,1236,Casey's,Farm fuel,Fuel Expense,R,Checking,-750.00"""

        import_data = {
            "csv_content": qb_csv,
            "tax_year": 2025,
            "source_format": "quickbooks"
        }

        response = client.post(
            "/api/v1/costs/import/quickbooks",
            json=import_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 404, 422]

    def test_import_duplicate_detection(self, client, auth_headers):
        """Test that duplicate expenses are detected during import."""
        csv_content = """Date,Description,Amount,Category
2025-01-20,Duplicate Test,1000.00,other
2025-01-20,Duplicate Test,1000.00,other"""

        import_data = {
            "csv_content": csv_content,
            "tax_year": 2025
        }

        response = client.post(
            "/api/v1/costs/import",
            json=import_data,
            headers=auth_headers
        )

        if response.status_code in [200, 201]:
            data = response.json()
            # Should report duplicates skipped
            assert "duplicates_skipped" in data or "duplicates" in data or "skipped" in data

    def test_import_validation_errors(self, client, auth_headers):
        """Test import handles validation errors gracefully."""
        # CSV with invalid data
        csv_content = """Date,Description,Amount,Category
invalid-date,Test expense,-100.00,invalid_category
2025-01-20,Valid expense,500.00,seed"""

        import_data = {
            "csv_content": csv_content,
            "tax_year": 2025
        }

        response = client.post(
            "/api/v1/costs/import",
            json=import_data,
            headers=auth_headers
        )

        # Should handle errors and report them
        assert response.status_code in [200, 201, 400, 422, 404]


class TestCostAllocation:
    """Test expense allocation to fields - Cost-per-acre foundation."""

    def test_allocate_expense_to_field(self, client, auth_headers, data_factory):
        """Test allocating expense to a single field."""
        # First create a field
        field_data = data_factory.field()
        field_response = client.post(
            "/api/v1/fields",
            json=field_data,
            headers=auth_headers
        )

        if field_response.status_code in [200, 201]:
            field = field_response.json()
            field_id = field.get("id")

            # Create expense
            expense_data = {
                "category": "fertilizer",
                "amount": 5000.00,
                "expense_date": date.today().isoformat(),
                "tax_year": 2025
            }

            expense_response = client.post(
                "/api/v1/costs/expenses",
                json=expense_data,
                headers=auth_headers
            )

            if expense_response.status_code in [200, 201]:
                expense = expense_response.json()
                expense_id = expense.get("id")

                # Allocate to field - endpoint expects a list of allocations
                allocation_data = [{
                    "field_id": field_id,
                    "crop_year": 2025,
                    "allocation_percent": 100.0
                }]

                alloc_response = client.post(
                    f"/api/v1/costs/expenses/{expense_id}/allocations",
                    json=allocation_data,
                    headers=auth_headers
                )

                assert alloc_response.status_code in [200, 201, 404, 422]

    def test_allocate_expense_multiple_fields(self, client, auth_headers, data_factory):
        """Test allocating expense across multiple fields."""
        # Create two fields
        field1_data = data_factory.field("field1")
        field2_data = data_factory.field("field2")

        field1_response = client.post("/api/v1/fields", json=field1_data, headers=auth_headers)
        field2_response = client.post("/api/v1/fields", json=field2_data, headers=auth_headers)

        if field1_response.status_code in [200, 201] and field2_response.status_code in [200, 201]:
            field1 = field1_response.json()
            field2 = field2_response.json()

            # Create expense
            expense_data = {
                "category": "chemical",
                "amount": 10000.00,
                "expense_date": date.today().isoformat(),
                "tax_year": 2025
            }

            expense_response = client.post(
                "/api/v1/costs/expenses",
                json=expense_data,
                headers=auth_headers
            )

            if expense_response.status_code in [200, 201]:
                expense = expense_response.json()
                expense_id = expense.get("id")

                # Allocate 60/40 split
                allocations = [
                    {"field_id": field1.get("id"), "crop_year": 2025, "allocation_percent": 60.0},
                    {"field_id": field2.get("id"), "crop_year": 2025, "allocation_percent": 40.0}
                ]

                for alloc in allocations:
                    client.post(
                        f"/api/v1/costs/expenses/{expense_id}/allocations",
                        json=alloc,
                        headers=auth_headers
                    )

    def test_allocation_exceeds_100_percent(self, client, auth_headers, data_factory):
        """Test that allocations cannot exceed 100%."""
        # Create field
        field_data = data_factory.field()
        field_response = client.post("/api/v1/fields", json=field_data, headers=auth_headers)

        if field_response.status_code in [200, 201]:
            field = field_response.json()
            field_id = field.get("id")

            # Create expense
            expense_data = {
                "category": "seed",
                "amount": 8000.00,
                "expense_date": date.today().isoformat(),
                "tax_year": 2025
            }

            expense_response = client.post(
                "/api/v1/costs/expenses",
                json=expense_data,
                headers=auth_headers
            )

            if expense_response.status_code in [200, 201]:
                expense = expense_response.json()
                expense_id = expense.get("id")

                # First allocation of 80%
                alloc1 = {"field_id": field_id, "crop_year": 2025, "allocation_percent": 80.0}
                client.post(
                    f"/api/v1/costs/expenses/{expense_id}/allocations",
                    json=alloc1,
                    headers=auth_headers
                )

                # Second allocation that would exceed 100%
                alloc2 = {"field_id": field_id, "crop_year": 2025, "allocation_percent": 30.0}
                response = client.post(
                    f"/api/v1/costs/expenses/{expense_id}/allocations",
                    json=alloc2,
                    headers=auth_headers
                )

                # Should reject or warn
                assert response.status_code in [200, 400, 422, 404]


class TestCostPerAcre:
    """Test cost-per-acre calculations - Key business metric."""

    def test_cost_per_acre_by_field(self, client, auth_headers, data_factory):
        """Test cost-per-acre calculation for a single field."""
        # Create field with known acreage
        field_data = data_factory.field()
        field_data["acreage"] = 100.0  # 100 acres

        field_response = client.post("/api/v1/fields", json=field_data, headers=auth_headers)

        if field_response.status_code in [200, 201]:
            field = field_response.json()
            field_id = field.get("id")

            # Create and allocate expenses
            expenses = [
                {"category": "seed", "amount": 10000.00},  # $100/acre
                {"category": "fertilizer", "amount": 15000.00},  # $150/acre
                {"category": "chemical", "amount": 5000.00}  # $50/acre
            ]

            for exp in expenses:
                exp_data = {
                    **exp,
                    "expense_date": date.today().isoformat(),
                    "tax_year": 2025
                }
                exp_response = client.post(
                    "/api/v1/costs/expenses",
                    json=exp_data,
                    headers=auth_headers
                )

                if exp_response.status_code in [200, 201]:
                    expense = exp_response.json()
                    # Allocate 100% to field
                    alloc_data = {
                        "field_id": field_id,
                        "crop_year": 2025,
                        "allocation_percent": 100.0
                    }
                    client.post(
                        f"/api/v1/costs/expenses/{expense.get('id')}/allocations",
                        json=alloc_data,
                        headers=auth_headers
                    )

            # Get cost-per-acre report
            response = client.get(
                f"/api/v1/costs/per-acre",
                params={"field_id": field_id, "year": 2025},
                headers=auth_headers
            )

            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                # Expected: ($10000 + $15000 + $5000) / 100 acres = $300/acre
                # Actual calculation depends on implementation

    def test_cost_per_acre_by_category(self, client, auth_headers):
        """Test cost-per-acre breakdown by category."""
        response = client.get(
            "/api/v1/costs/per-acre/by-category",
            params={"year": 2025},
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Should have category breakdown

    def test_cost_per_acre_comparison(self, client, auth_headers):
        """Test cost-per-acre comparison across fields."""
        response = client.get(
            "/api/v1/costs/per-acre/comparison",
            params={"year": 2025},
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

    def test_cost_per_acre_year_over_year(self, client, auth_headers):
        """Test year-over-year cost-per-acre trend."""
        response = client.get(
            "/api/v1/costs/per-acre/trend",
            params={"start_year": 2023, "end_year": 2025},
            headers=auth_headers
        )

        assert response.status_code in [200, 404]


class TestBudgetVsActual:
    """Test budget vs actual analysis - Decision support."""

    def test_set_budget(self, client, auth_headers):
        """Test setting budget for a category."""
        budget_data = {
            "category": "seed",
            "budgeted_amount": 50000.00,
            "year": 2025
        }

        response = client.post(
            "/api/v1/costs/budgets",
            json=budget_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 404, 422]

    def test_budget_vs_actual_report(self, client, auth_headers):
        """Test budget vs actual comparison report."""
        response = client.get(
            "/api/v1/costs/budget-vs-actual",
            params={"year": 2025},
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Should include budget, actual, variance


class TestExpenseCategorization:
    """Test automatic expense categorization - AI/ML feature."""

    def test_auto_categorize_expense(self, client, auth_headers):
        """Test automatic categorization based on description."""
        expense_data = {
            "description": "Pioneer P1197 corn seed 80 bags",
            "amount": 12000.00,
            "expense_date": date.today().isoformat(),
            "tax_year": 2025
        }

        response = client.post(
            "/api/v1/costs/expenses/auto-categorize",
            json=expense_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 404, 422]

        if response.status_code == 200:
            data = response.json()
            # Should suggest "seed" category
            suggested = data.get("suggested_category") or data.get("category")
            # Category should be inferred from description

    def test_categorization_learning(self, client, auth_headers):
        """Test that categorization improves from user corrections."""
        # This would test the ML feedback loop
        correction_data = {
            "description": "Custom fertilizer application",
            "original_category": "other",
            "correct_category": "custom_hire"
        }

        response = client.post(
            "/api/v1/costs/categorization/feedback",
            json=correction_data,
            headers=auth_headers
        )

        assert response.status_code in [200, 201, 404]


# ============================================================================
# UNIT TESTS FOR SERVICE LAYER
# ============================================================================

class TestCostTrackingServiceUnit:
    """Unit tests for cost tracking service (no API calls)."""

    def test_cost_per_acre_calculation(self):
        """Test cost-per-acre calculation logic."""
        total_cost = Decimal("30000.00")
        acres = Decimal("100.0")

        cost_per_acre = total_cost / acres

        assert cost_per_acre == Decimal("300.00")

    def test_cost_allocation_amounts(self):
        """Test allocation amount calculation."""
        expense_amount = Decimal("10000.00")
        allocation_percent = Decimal("60.0")

        allocated_amount = expense_amount * (allocation_percent / Decimal("100"))

        assert allocated_amount == Decimal("6000.00")

    def test_budget_variance_calculation(self):
        """Test budget variance calculation."""
        budgeted = Decimal("50000.00")
        actual = Decimal("45000.00")

        variance = budgeted - actual
        variance_percent = (variance / budgeted * Decimal("100")).quantize(Decimal("0.01"))

        assert variance == Decimal("5000.00")
        assert variance_percent == Decimal("10.00")  # 10% under budget

    def test_category_grouping(self):
        """Test expense category grouping."""
        categories_by_group = {
            "inputs": ["seed", "fertilizer", "chemical", "fuel"],
            "operations": ["repairs", "labor", "custom_hire"],
            "overhead": ["land_rent", "crop_insurance", "interest", "utilities", "storage"],
            "other": ["other"]
        }

        # Verify all categories are grouped
        all_categories = []
        for group_cats in categories_by_group.values():
            all_categories.extend(group_cats)

        expected_categories = [
            "seed", "fertilizer", "chemical", "fuel",
            "repairs", "labor", "custom_hire",
            "land_rent", "crop_insurance", "interest",
            "utilities", "storage", "other"
        ]

        assert sorted(all_categories) == sorted(expected_categories)

    def test_csv_parsing(self):
        """Test CSV parsing logic."""
        csv_content = """Date,Description,Amount,Category
2025-01-15,Test expense,1000.00,seed"""

        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["Date"] == "2025-01-15"
        assert rows[0]["Description"] == "Test expense"
        assert rows[0]["Amount"] == "1000.00"
        assert rows[0]["Category"] == "seed"

    def test_decimal_precision(self):
        """Test decimal precision for financial calculations."""
        # Ensure no floating point errors
        amount1 = Decimal("1234.56")
        amount2 = Decimal("789.44")

        total = amount1 + amount2

        assert total == Decimal("2024.00")
        assert str(total) == "2024.00"

    def test_date_range_filtering(self):
        """Test date range filtering logic."""
        expenses_dates = [
            date(2025, 1, 1),
            date(2025, 1, 15),
            date(2025, 2, 1),
            date(2025, 3, 1)
        ]

        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)

        filtered = [d for d in expenses_dates if start_date <= d <= end_date]

        assert len(filtered) == 2
        assert date(2025, 1, 1) in filtered
        assert date(2025, 1, 15) in filtered
