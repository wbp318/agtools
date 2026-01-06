"""
Accounting Import API Client

Handles communication with the accounting import endpoints.
AgTools v2.9.0
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple

from .client import APIClient, get_api_client


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class QBAccountMapping:
    """QuickBooks account to category mapping."""
    id: int
    qb_account: str
    agtools_category: str
    is_default: bool
    created_at: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "QBAccountMapping":
        return cls(
            id=data.get("id", 0),
            qb_account=data.get("qb_account", ""),
            agtools_category=data.get("agtools_category", ""),
            is_default=data.get("is_default", False),
            created_at=data.get("created_at")
        )


@dataclass
class QBAccountPreview:
    """Account found in QB export with suggested mapping."""
    account: str
    count: int
    total: float
    suggested_category: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "QBAccountPreview":
        return cls(
            account=data.get("account", ""),
            count=data.get("count", 0),
            total=float(data.get("total", 0)),
            suggested_category=data.get("suggested_category")
        )


@dataclass
class QBImportPreview:
    """Preview of QuickBooks import."""
    format_detected: str
    total_rows: int
    expense_rows: int
    skipped_rows: int
    date_range: Dict[str, str]
    accounts_found: List[QBAccountPreview]
    unmapped_accounts: List[str]
    sample_transactions: List[Dict[str, Any]]
    warnings: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "QBImportPreview":
        return cls(
            format_detected=data.get("format_detected", "unknown"),
            total_rows=data.get("total_rows", 0),
            expense_rows=data.get("expense_rows", 0),
            skipped_rows=data.get("skipped_rows", 0),
            date_range=data.get("date_range", {}),
            accounts_found=[
                QBAccountPreview.from_dict(a)
                for a in data.get("accounts_found", [])
            ],
            unmapped_accounts=data.get("unmapped_accounts", []),
            sample_transactions=data.get("sample_transactions", []),
            warnings=data.get("warnings", [])
        )


@dataclass
class QBImportSummary:
    """Summary after QuickBooks import."""
    batch_id: int
    total_processed: int
    successful: int
    failed: int
    skipped_non_expense: int
    duplicates_skipped: int
    by_category: Dict[str, int]
    by_account: Dict[str, float]
    total_amount: float
    errors: List[str]

    @classmethod
    def from_dict(cls, data: dict) -> "QBImportSummary":
        return cls(
            batch_id=data.get("batch_id", 0),
            total_processed=data.get("total_processed", 0),
            successful=data.get("successful", 0),
            failed=data.get("failed", 0),
            skipped_non_expense=data.get("skipped_non_expense", 0),
            duplicates_skipped=data.get("duplicates_skipped", 0),
            by_category=data.get("by_category", {}),
            by_account=data.get("by_account", {}),
            total_amount=float(data.get("total_amount", 0)),
            errors=data.get("errors", [])
        )


@dataclass
class QBFormat:
    """Supported QuickBooks format."""
    format: str
    name: str
    description: str

    @classmethod
    def from_dict(cls, data: dict) -> "QBFormat":
        return cls(
            format=data.get("format", ""),
            name=data.get("name", ""),
            description=data.get("description", "")
        )


@dataclass
class ExpenseCategory:
    """Expense category option."""
    value: str
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> "ExpenseCategory":
        return cls(
            value=data.get("value", ""),
            name=data.get("name", "")
        )


# ============================================================================
# API CLASS
# ============================================================================

class AccountingImportAPI:
    """API client for accounting import operations."""

    def __init__(self, client: Optional[APIClient] = None):
        self.client = client or get_api_client()

    def preview_import(self, file_path: str) -> Tuple[Optional[QBImportPreview], Optional[str]]:
        """
        Preview an accounting software CSV export before importing.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (QBImportPreview or None, error message or None)
        """
        try:
            with open(file_path, 'rb') as f:
                filename = file_path.replace('\\', '/').split('/')[-1]
                files = {'file': (filename, f, 'text/csv')}
                response = self.client.post_file('/accounting-import/preview', files=files)

            if response.success and response.data:
                return QBImportPreview.from_dict(response.data), None
            return None, response.error or "Unknown error"
        except Exception as e:
            return None, str(e)

    def import_data(
        self,
        file_path: str,
        account_mappings: Dict[str, str],
        tax_year: Optional[int] = None,
        save_mappings: bool = True
    ) -> Tuple[Optional[QBImportSummary], Optional[str]]:
        """
        Import expenses from an accounting software CSV export.

        Args:
            file_path: Path to the CSV file
            account_mappings: Dict of account -> agtools_category
            tax_year: Optional tax year override
            save_mappings: Whether to save mappings for future use

        Returns:
            Tuple of (QBImportSummary or None, error message or None)
        """
        try:
            with open(file_path, 'rb') as f:
                filename = file_path.replace('\\', '/').split('/')[-1]
                files = {'file': (filename, f, 'text/csv')}
                data = {
                    'account_mappings': json.dumps(account_mappings),
                    'save_mappings': 'true' if save_mappings else 'false'
                }
                if tax_year:
                    data['tax_year'] = str(tax_year)

                response = self.client.post_file(
                    '/accounting-import/import',
                    files=files,
                    data=data
                )

            if response.success and response.data:
                return QBImportSummary.from_dict(response.data), None
            return None, response.error or "Unknown error"
        except Exception as e:
            return None, str(e)

    def get_mappings(self) -> Tuple[List[QBAccountMapping], Optional[str]]:
        """Get user's saved accounting software account mappings."""
        response = self.client.get('/accounting-import/mappings')
        if response.success and response.data:
            return [QBAccountMapping.from_dict(m) for m in response.data], None
        return [], response.error

    def save_mappings(self, mappings: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """Save accounting software account to AgTools category mappings."""
        response = self.client.post('/accounting-import/mappings', data=mappings)
        return response.success, response.error

    def delete_mapping(self, mapping_id: int) -> Tuple[bool, Optional[str]]:
        """Delete an accounting software account mapping."""
        response = self.client.delete(f'/accounting-import/mappings/{mapping_id}')
        return response.success, response.error

    def get_supported_formats(self) -> Tuple[List[QBFormat], Optional[str]]:
        """Get list of supported accounting software export formats."""
        response = self.client.get('/accounting-import/formats')
        if response.success and response.data:
            return [QBFormat.from_dict(f) for f in response.data], None
        return [], response.error

    def get_default_mappings(self) -> Tuple[Dict[str, str], Optional[str]]:
        """Get default accounting software account to category mappings."""
        response = self.client.get('/accounting-import/default-mappings')
        if response.success and response.data:
            return response.data, None
        return {}, response.error

    def get_categories(self) -> Tuple[List[ExpenseCategory], Optional[str]]:
        """Get list of available expense categories."""
        response = self.client.get('/costs/categories')
        if response.success and response.data:
            return [ExpenseCategory.from_dict(c) for c in response.data], None
        return [], response.error


# ============================================================================
# SINGLETON
# ============================================================================

_accounting_api: Optional[AccountingImportAPI] = None


def get_accounting_import_api() -> AccountingImportAPI:
    """Get or create the Accounting Import API singleton."""
    global _accounting_api
    if _accounting_api is None:
        _accounting_api = AccountingImportAPI()
    return _accounting_api
