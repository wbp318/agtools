"""
Test QuickBooks Import Service

Tests the QB import functionality with sample data.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.quickbooks_import import (
    get_qb_import_service,
    QBExportFormat,
    DEFAULT_QB_MAPPINGS,
    ExpenseCategory
)


# Sample QuickBooks Desktop Transaction Detail export
SAMPLE_QB_DESKTOP_CSV = """Transaction Detail Report
Tap Parker Farms
All Transactions
Date,Type,Num,Name,Memo,Split,Amount,Balance
01/15/2025,Bill,1001,AgriSupply Co,Corn seed for north fields,Farm Expense:Seed,12500.00,12500.00
01/15/2025,Bill,1002,AgriSupply Co,Soybean seed - variety XJ45,Farm Expense:Seed,8750.00,21250.00
02/01/2025,Bill,1003,FarmChem Inc,Spring herbicide - Roundup,Farm Expense:Chemical,4200.00,25450.00
02/15/2025,Check,2001,Delta Petroleum,Diesel fuel - February,Farm Expense:Fuel,3150.00,28600.00
03/01/2025,Bill,1004,Nutrien Ag,28-0-0 UAN Solution,Farm Expense:Fertilizer,18500.00,47100.00
03/01/2025,Bill,1005,Nutrien Ag,DAP 18-46-0,Farm Expense:Fertilizer,9200.00,56300.00
03/15/2025,Credit Card Charge,CC001,Flying S Aviation,Aerial application - herbicide,Farm Expense:Custom Hire,1800.00,58100.00
04/01/2025,Deposit,,Grain Sales,,Income:Grain Sales,-25000.00,33100.00
04/15/2025,Bill,1006,John Deere,Planter repairs - chains and bearings,Farm Expense:Repairs,875.00,33975.00
05/01/2025,Transfer,,Bank Transfer,,Checking,-5000.00,28975.00
"""

# Sample QuickBooks Online export format
SAMPLE_QB_ONLINE_CSV = """Date,Transaction Type,Name,Memo/Description,Amount
01/20/2025,Expense,Local Co-op,Seed treatment,450.00
02/10/2025,Expense,Delta Fuel,Diesel fuel,2800.00
02/25/2025,Expense,Helena Chemical,Fungicide - Headline,3200.00
03/05/2025,Bill,ABC Fertilizer,Potash 0-0-60,5500.00
03/20/2025,Check,Custom Harvesters LLC,Custom combining deposit,4000.00
04/01/2025,Invoice,Grain Elevator,,-15000.00
"""


def test_format_detection():
    """Test that QB format detection works."""
    print("\n=== Testing Format Detection ===")
    qb_service = get_qb_import_service()

    # Test Desktop format
    format_type, headers = qb_service.detect_format(SAMPLE_QB_DESKTOP_CSV)
    print(f"Desktop CSV detected as: {format_type.value}")
    print(f"Headers found: {headers}")
    assert format_type == QBExportFormat.DESKTOP_TRANSACTION_DETAIL, f"Expected desktop_transaction_detail, got {format_type}"
    print("  PASSED")

    # Test Online format
    format_type, headers = qb_service.detect_format(SAMPLE_QB_ONLINE_CSV)
    print(f"Online CSV detected as: {format_type.value}")
    assert format_type == QBExportFormat.ONLINE_EXPORT or format_type == QBExportFormat.GENERIC
    print("  PASSED")


def test_preview_import():
    """Test preview functionality."""
    print("\n=== Testing Import Preview ===")
    qb_service = get_qb_import_service()

    preview = qb_service.preview_import(SAMPLE_QB_DESKTOP_CSV, user_id=1)

    print(f"Format detected: {preview.format_detected}")
    print(f"Total rows: {preview.total_rows}")
    print(f"Expense rows: {preview.expense_rows}")
    print(f"Skipped (non-expense): {preview.skipped_rows}")
    print(f"Date range: {preview.date_range['min_date']} to {preview.date_range['max_date']}")

    print("\nAccounts found:")
    for acc in preview.accounts_found:
        suggested = acc.get('suggested_category', 'NONE')
        print(f"  {acc['account']}: ${acc['total']:.2f} ({acc['count']} transactions) -> {suggested}")

    print(f"\nUnmapped accounts: {preview.unmapped_accounts}")
    print(f"Warnings: {preview.warnings}")

    # Verify counts
    assert preview.expense_rows > 0, "Should find expense rows"
    assert preview.skipped_rows > 0, "Should skip deposit/transfer rows"
    print("\n  PASSED")


def test_category_suggestions():
    """Test that default mappings work."""
    print("\n=== Testing Category Suggestions ===")
    qb_service = get_qb_import_service()

    # Test various account names
    test_accounts = [
        ("Farm Expense:Seed", ExpenseCategory.SEED),
        ("Farm Expense:Fertilizer", ExpenseCategory.FERTILIZER),
        ("Farm Expense:Chemical", ExpenseCategory.CHEMICAL),
        ("Farm Expense:Fuel", ExpenseCategory.FUEL),
        ("Farm Expense:Custom Hire", ExpenseCategory.CUSTOM_HIRE),
        ("Farm Expense:Repairs", ExpenseCategory.REPAIRS),
        ("crop inputs:seed", ExpenseCategory.SEED),
        ("Herbicide Expense", ExpenseCategory.CHEMICAL),
    ]

    saved_mappings = {}  # Empty - rely on defaults
    passed = 0
    for account, expected in test_accounts:
        result = qb_service._suggest_category(account, saved_mappings)
        status = "OK" if result == expected else f"FAIL (got {result})"
        print(f"  {account} -> {result} [{status}]")
        if result == expected:
            passed += 1

    print(f"\n  {passed}/{len(test_accounts)} suggestions correct")
    assert passed >= len(test_accounts) * 0.7, "At least 70% of suggestions should match"
    print("  PASSED")


def test_import_with_mappings():
    """Test full import with account mappings."""
    print("\n=== Testing Full Import ===")
    qb_service = get_qb_import_service()

    # Define mappings for the sample data
    mappings = {
        "farm expense:seed": "seed",
        "farm expense:chemical": "chemical",
        "farm expense:fuel": "fuel",
        "farm expense:fertilizer": "fertilizer",
        "farm expense:custom hire": "custom_hire",
        "farm expense:repairs": "repairs",
    }

    result = qb_service.import_quickbooks(
        csv_content=SAMPLE_QB_DESKTOP_CSV,
        user_id=1,
        account_mappings=mappings,
        source_file="test_qb_export.csv",
        tax_year=2025,
        save_mappings=False  # Don't save for test
    )

    print(f"Batch ID: {result.batch_id}")
    print(f"Total processed: {result.total_processed}")
    print(f"Successful: {result.successful}")
    print(f"Failed: {result.failed}")
    print(f"Skipped non-expense: {result.skipped_non_expense}")
    print(f"Duplicates: {result.duplicates_skipped}")
    print(f"Total amount: ${result.total_amount:,.2f}")

    print("\nBy category:")
    for cat, count in result.by_category.items():
        print(f"  {cat}: {count}")

    print("\nBy account:")
    for acc, total in result.by_account.items():
        print(f"  {acc}: ${total:,.2f}")

    if result.errors:
        print(f"\nErrors: {result.errors[:5]}")

    # Verify results
    assert result.successful > 0, "Should have successful imports"
    assert result.skipped_non_expense >= 2, "Should skip deposit and transfer"
    assert "seed" in result.by_category, "Should have seed expenses"
    print("\n  PASSED")


def test_default_mappings():
    """Test that default mappings cover common accounts."""
    print("\n=== Testing Default Mappings ===")

    print(f"Total default mappings: {len(DEFAULT_QB_MAPPINGS)}")

    # Check each category has at least one mapping
    categories_covered = set(DEFAULT_QB_MAPPINGS.values())
    print(f"Categories covered: {len(categories_covered)}")

    for cat in ExpenseCategory:
        if cat in categories_covered:
            print(f"  {cat.value}: covered")
        else:
            print(f"  {cat.value}: NOT covered")

    # At least 10 categories should have defaults
    assert len(categories_covered) >= 10, "Should cover at least 10 categories"
    print("\n  PASSED")


def run_all_tests():
    """Run all QuickBooks import tests."""
    print("=" * 60)
    print("QuickBooks Import Service Tests")
    print("=" * 60)

    try:
        test_format_detection()
        test_default_mappings()
        test_category_suggestions()
        test_preview_import()
        test_import_with_mappings()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
