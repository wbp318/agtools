"""
Export API Client

Handles export operations for reports across all dashboards.
Supports CSV, Excel, and PDF export formats.

AgTools v6.10.0
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime
import httpx

from .client import APIClient, get_api_client


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    content: bytes
    filename: str
    content_type: str
    error: Optional[str] = None

    @classmethod
    def from_response(
        cls,
        content: bytes,
        filename: str,
        content_type: str
    ) -> "ExportResult":
        return cls(
            success=True,
            content=content,
            filename=filename,
            content_type=content_type
        )

    @classmethod
    def error_result(cls, error: str) -> "ExportResult":
        return cls(
            success=False,
            content=b"",
            filename="",
            content_type="",
            error=error
        )


class ExportAPI:
    """
    API client for export operations.

    Handles CSV, Excel, and PDF exports for:
    - Unified Dashboard (Advanced Reporting)
    - Reports Dashboard (Operations, Financial, Equipment, Fields)
    - Crop Cost Analysis Dashboard
    """

    # Content type mappings
    CONTENT_TYPES = {
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf"
    }

    # File extension mappings
    EXTENSIONS = {
        "csv": ".csv",
        "excel": ".xlsx",
        "pdf": ".pdf"
    }

    def __init__(self, client: Optional[APIClient] = None):
        self._client = client or get_api_client()

    def _get_raw_client(self) -> httpx.Client:
        """Get the underlying httpx client for binary downloads."""
        return self._client._get_client()

    def _generate_filename(self, base_name: str, format_type: str) -> str:
        """Generate a filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self.EXTENSIONS.get(format_type, "")
        return f"{base_name}_{timestamp}{ext}"

    def export_unified_dashboard(
        self,
        format_type: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[ExportResult], Optional[str]]:
        """
        Export unified dashboard data.

        Args:
            format_type: Export format (csv, excel, pdf)
            date_from: Optional start date (YYYY-MM-DD)
            date_to: Optional end date (YYYY-MM-DD)

        Returns:
            Tuple of (ExportResult, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        return self._do_export(
            f"/export/unified-dashboard/{format_type}",
            params,
            "unified_dashboard_report",
            format_type
        )

    def export_reports(
        self,
        report_type: str,
        format_type: str,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Tuple[Optional[ExportResult], Optional[str]]:
        """
        Export reports dashboard data.

        Args:
            report_type: Report type (operations, financial, equipment, fields)
            format_type: Export format (csv, excel, pdf)
            date_from: Optional start date (YYYY-MM-DD)
            date_to: Optional end date (YYYY-MM-DD)

        Returns:
            Tuple of (ExportResult, error_message or None)
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        return self._do_export(
            f"/export/reports/{report_type}/{format_type}",
            params,
            f"{report_type}_report",
            format_type
        )

    def export_crop_cost_analysis(
        self,
        format_type: str,
        crop_year: int,
        tab: str = "overview"
    ) -> Tuple[Optional[ExportResult], Optional[str]]:
        """
        Export crop cost analysis data.

        Args:
            format_type: Export format (csv, excel, pdf)
            crop_year: Year of crop analysis
            tab: Dashboard tab (overview, field_comparison, crop_comparison, yoy, roi)

        Returns:
            Tuple of (ExportResult, error_message or None)
        """
        params = {
            "crop_year": crop_year,
            "tab": tab
        }

        return self._do_export(
            f"/export/crop-cost-analysis/{format_type}",
            params,
            f"crop_cost_analysis_{crop_year}",
            format_type
        )

    def _do_export(
        self,
        endpoint: str,
        params: dict,
        base_filename: str,
        format_type: str
    ) -> Tuple[Optional[ExportResult], Optional[str]]:
        """
        Perform the export operation.

        Args:
            endpoint: API endpoint
            params: Query parameters
            base_filename: Base name for the generated file
            format_type: Export format type

        Returns:
            Tuple of (ExportResult, error_message or None)
        """
        try:
            client = self._get_raw_client()
            response = client.get(endpoint, params=params if params else None)

            if response.status_code == 200:
                filename = self._generate_filename(base_filename, format_type)
                content_type = self.CONTENT_TYPES.get(
                    format_type,
                    "application/octet-stream"
                )

                return ExportResult.from_response(
                    content=response.content,
                    filename=filename,
                    content_type=content_type
                ), None

            # Handle error response
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", str(error_data))
            except Exception:
                error_msg = response.text or f"HTTP {response.status_code}"

            return None, error_msg

        except httpx.ConnectError:
            return None, "Unable to connect to API server"
        except httpx.TimeoutException:
            return None, "Request timed out"
        except Exception as e:
            return None, f"Export failed: {str(e)}"


# Singleton instance
_export_api: Optional[ExportAPI] = None


def get_export_api() -> ExportAPI:
    """Get or create the export API singleton."""
    global _export_api
    if _export_api is None:
        _export_api = ExportAPI()
    return _export_api
