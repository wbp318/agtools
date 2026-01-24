"""
Export Toolbar Widget

Reusable export button with dropdown menu for CSV, Excel, and PDF exports.
Follows existing AgTools widget patterns.

AgTools v6.10.0
"""

from typing import Optional, Callable, Tuple
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QMenu,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction

from ..retro_styles import RETRO_COLORS


class ExportToolbar(QWidget):
    """
    Reusable export toolbar with dropdown menu.

    Provides CSV, Excel, and PDF export options with consistent styling
    across all dashboard screens.

    Signals:
        export_started(str): Emitted when export begins (format type)
        export_completed(str, str): Emitted on success (format, file_path)
        export_failed(str, str): Emitted on error (format, error_message)

    Usage:
        toolbar = ExportToolbar()
        toolbar.set_export_handler(self._handle_export)
        header_layout.addWidget(toolbar)

    Handler signature:
        def _handle_export(format_type: str) -> Tuple[bytes, str, str]:
            # Returns: (content_bytes, suggested_filename, content_type)
    """

    export_started = pyqtSignal(str)
    export_completed = pyqtSignal(str, str)
    export_failed = pyqtSignal(str, str)

    def __init__(
        self,
        parent=None,
        show_csv: bool = True,
        show_excel: bool = True,
        show_pdf: bool = True,
        button_text: str = "Export"
    ):
        super().__init__(parent)
        self._export_handler: Optional[Callable] = None
        self._show_csv = show_csv
        self._show_excel = show_excel
        self._show_pdf = show_pdf
        self._button_text = button_text
        self._setup_ui()

    def _setup_ui(self):
        """Setup the export button with dropdown menu."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Export button with dropdown arrow
        self._export_btn = QPushButton(f"\u2913 {self._button_text}")
        self._export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {RETRO_COLORS['turquoise_dark']};
                color: {RETRO_COLORS['text_white']};
                padding: 8px 16px;
                border: 2px outset {RETRO_COLORS['bevel_light']};
                border-radius: 0px;
                font-weight: bold;
                font-family: "MS Sans Serif", "Segoe UI", sans-serif;
            }}
            QPushButton:hover {{
                background-color: {RETRO_COLORS['turquoise']};
            }}
            QPushButton:pressed {{
                background-color: {RETRO_COLORS['turquoise_dark']};
                border: 2px inset {RETRO_COLORS['bevel_dark']};
            }}
            QPushButton::menu-indicator {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                padding-right: 8px;
            }}
        """)

        # Dropdown menu
        self._menu = QMenu(self)
        self._menu.setStyleSheet(f"""
            QMenu {{
                background-color: {RETRO_COLORS['menu_bg']};
                border: 2px outset {RETRO_COLORS['bevel_light']};
                padding: 2px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                color: {RETRO_COLORS['text_black']};
            }}
            QMenu::item:selected {{
                background-color: {RETRO_COLORS['selection_bg']};
                color: {RETRO_COLORS['selection_text']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {RETRO_COLORS['panel_border']};
                margin: 4px 8px;
            }}
        """)

        if self._show_csv:
            csv_action = QAction("\U0001F4C4 Export to CSV", self)
            csv_action.setStatusTip("Export data to comma-separated values file")
            csv_action.triggered.connect(lambda: self._do_export("csv"))
            self._menu.addAction(csv_action)

        if self._show_excel:
            excel_action = QAction("\U0001F4CA Export to Excel", self)
            excel_action.setStatusTip("Export data to Excel spreadsheet")
            excel_action.triggered.connect(lambda: self._do_export("excel"))
            self._menu.addAction(excel_action)

        if self._show_pdf:
            if self._show_csv or self._show_excel:
                self._menu.addSeparator()
            pdf_action = QAction("\U0001F4D1 Export to PDF", self)
            pdf_action.setStatusTip("Export report as PDF document")
            pdf_action.triggered.connect(lambda: self._do_export("pdf"))
            self._menu.addAction(pdf_action)

        self._export_btn.setMenu(self._menu)
        layout.addWidget(self._export_btn)

    def set_export_handler(self, handler: Callable[[str], Tuple[bytes, str, str]]):
        """
        Set the export handler callback.

        Handler signature: (format: str) -> Tuple[bytes, str, str]
        Returns: (content_bytes, suggested_filename, content_type)

        Args:
            handler: Callable that performs the export and returns file content
        """
        self._export_handler = handler

    def _do_export(self, format_type: str):
        """Execute export operation."""
        if not self._export_handler:
            QMessageBox.warning(
                self, "Export Error",
                "Export handler not configured."
            )
            return

        self.export_started.emit(format_type)

        try:
            # Call the handler to get export data
            result = self._export_handler(format_type)

            if result is None:
                self.export_failed.emit(format_type, "Export returned no data")
                return

            content, filename, content_type = result

            # Get save path from user
            file_filter = self._get_file_filter(format_type)
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                f"Export {format_type.upper()}",
                filename,
                file_filter
            )

            if not save_path:
                # User cancelled
                self.export_failed.emit(format_type, "Export cancelled")
                return

            # Ensure correct extension
            save_path = self._ensure_extension(save_path, format_type)

            # Write file
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(save_path, mode) as f:
                f.write(content)

            self.export_completed.emit(format_type, save_path)
            QMessageBox.information(
                self,
                "Export Complete",
                f"Report exported successfully to:\n{save_path}"
            )

        except Exception as e:
            error_msg = str(e)
            self.export_failed.emit(format_type, error_msg)
            QMessageBox.warning(
                self,
                "Export Error",
                f"Failed to export {format_type.upper()}:\n{error_msg}"
            )

    def _get_file_filter(self, format_type: str) -> str:
        """Get file dialog filter for format."""
        filters = {
            "csv": "CSV Files (*.csv);;All Files (*)",
            "excel": "Excel Files (*.xlsx);;All Files (*)",
            "pdf": "PDF Files (*.pdf);;All Files (*)"
        }
        return filters.get(format_type, "All Files (*)")

    def _ensure_extension(self, path: str, format_type: str) -> str:
        """Ensure file has correct extension."""
        extensions = {
            "csv": ".csv",
            "excel": ".xlsx",
            "pdf": ".pdf"
        }
        ext = extensions.get(format_type, "")
        if ext and not path.lower().endswith(ext):
            path += ext
        return path

    def setEnabled(self, enabled: bool):
        """Enable/disable the export button."""
        self._export_btn.setEnabled(enabled)
        super().setEnabled(enabled)

    def set_button_text(self, text: str):
        """Update the button text."""
        self._button_text = text
        self._export_btn.setText(f"\u2913 {text}")
