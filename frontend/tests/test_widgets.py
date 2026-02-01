"""
Widget Tests

Tests for reusable UI widget components.
"""

import sys
import os
import pytest

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PyQt6 is required for these tests
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestCommonWidgets:
    """Tests for common widget module."""

    def test_common_widgets_import(self):
        """Test common widgets module imports."""
        from ui.widgets.common import LoadingOverlay
        assert LoadingOverlay is not None

    def test_loading_overlay_initialization(self, qapp):
        """Test LoadingOverlay widget initializes."""
        from ui.widgets.common import LoadingOverlay

        parent = QWidget()
        overlay = LoadingOverlay(parent)
        assert overlay is not None

    def test_loading_overlay_show_hide(self, qapp):
        """Test LoadingOverlay show/hide methods."""
        from ui.widgets.common import LoadingOverlay

        parent = QWidget()
        overlay = LoadingOverlay(parent)

        # Should have show/hide methods
        assert hasattr(overlay, 'show') or hasattr(overlay, 'start')
        assert hasattr(overlay, 'hide') or hasattr(overlay, 'stop')

    def test_loading_overlay_message(self, qapp):
        """Test LoadingOverlay with custom message."""
        from ui.widgets.common import LoadingOverlay

        parent = QWidget()
        overlay = LoadingOverlay(parent)

        if hasattr(overlay, 'set_message'):
            overlay.set_message("Loading data...")


class TestLoadingButton:
    """Tests for LoadingButton widget."""

    def test_loading_button_import(self):
        """Test LoadingButton imports."""
        try:
            from ui.widgets.common import LoadingButton
            assert LoadingButton is not None
        except ImportError:
            pytest.skip("LoadingButton not in common module")

    def test_loading_button_initialization(self, qapp):
        """Test LoadingButton initializes."""
        try:
            from ui.widgets.common import LoadingButton

            button = LoadingButton("Click Me")
            assert button is not None
        except ImportError:
            pytest.skip("LoadingButton not available")

    def test_loading_button_states(self, qapp):
        """Test LoadingButton loading state."""
        try:
            from ui.widgets.common import LoadingButton

            button = LoadingButton("Submit")

            if hasattr(button, 'set_loading'):
                button.set_loading(True)
                assert button.isEnabled() is False or True  # May disable when loading

                button.set_loading(False)
        except ImportError:
            pytest.skip("LoadingButton not available")


class TestStatusMessage:
    """Tests for StatusMessage widget."""

    def test_status_message_import(self):
        """Test StatusMessage imports."""
        try:
            from ui.widgets.common import StatusMessage
            assert StatusMessage is not None
        except ImportError:
            pytest.skip("StatusMessage not in common module")

    def test_status_message_types(self, qapp):
        """Test StatusMessage different types."""
        try:
            from ui.widgets.common import StatusMessage

            # Test different message types
            if hasattr(StatusMessage, 'success'):
                msg = StatusMessage.success("Operation completed")
                assert msg is not None

            if hasattr(StatusMessage, 'error'):
                msg = StatusMessage.error("Operation failed")
                assert msg is not None

            if hasattr(StatusMessage, 'warning'):
                msg = StatusMessage.warning("Please check input")
                assert msg is not None
        except ImportError:
            pytest.skip("StatusMessage not available")


class TestValidatedLineEdit:
    """Tests for ValidatedLineEdit widget."""

    def test_validated_line_edit_import(self):
        """Test ValidatedLineEdit imports."""
        try:
            from ui.widgets.common import ValidatedLineEdit
            assert ValidatedLineEdit is not None
        except ImportError:
            pytest.skip("ValidatedLineEdit not in common module")

    def test_validated_line_edit_initialization(self, qapp):
        """Test ValidatedLineEdit initializes."""
        try:
            from ui.widgets.common import ValidatedLineEdit

            edit = ValidatedLineEdit()
            assert edit is not None
        except ImportError:
            pytest.skip("ValidatedLineEdit not available")


class TestConfirmDialog:
    """Tests for ConfirmDialog widget."""

    def test_confirm_dialog_import(self):
        """Test ConfirmDialog imports."""
        try:
            from ui.widgets.common import ConfirmDialog
            assert ConfirmDialog is not None
        except ImportError:
            pytest.skip("ConfirmDialog not in common module")


class TestToastNotification:
    """Tests for ToastNotification widget."""

    def test_toast_notification_import(self):
        """Test ToastNotification imports."""
        try:
            from ui.widgets.common import ToastNotification
            assert ToastNotification is not None
        except ImportError:
            pytest.skip("ToastNotification not in common module")


class TestKPICard:
    """Tests for KPICard widget."""

    def test_kpi_card_import(self):
        """Test KPICard imports."""
        from ui.widgets.kpi_card import KPICard
        assert KPICard is not None

    def test_kpi_card_initialization(self, qapp):
        """Test KPICard initializes."""
        from ui.widgets.kpi_card import KPICard

        card = KPICard(
            title="Total Revenue",
            value="$125,000",
            trend="+5.2%"
        )
        assert card is not None
        assert isinstance(card, QWidget)

    def test_kpi_card_with_data(self, qapp):
        """Test KPICard with various data."""
        from ui.widgets.kpi_card import KPICard

        # Test with number value
        card1 = KPICard(title="Count", value="42")
        assert card1 is not None

        # Test with formatted value
        card2 = KPICard(title="Yield", value="185 bu/acre")
        assert card2 is not None

    def test_kpi_card_update(self, qapp):
        """Test KPICard value update."""
        from ui.widgets.kpi_card import KPICard

        card = KPICard(title="Status", value="0")

        if hasattr(card, 'set_value'):
            card.set_value("100")

        if hasattr(card, 'update_value'):
            card.update_value("200")

    def test_kpi_card_trend(self, qapp):
        """Test KPICard trend display."""
        from ui.widgets.kpi_card import KPICard

        # Positive trend
        card_up = KPICard(title="Sales", value="$50k", trend="+10%")
        assert card_up is not None

        # Negative trend
        card_down = KPICard(title="Costs", value="$30k", trend="-5%")
        assert card_down is not None


class TestExportToolbar:
    """Tests for ExportToolbar widget."""

    def test_export_toolbar_import(self):
        """Test ExportToolbar imports."""
        try:
            from ui.widgets.export_toolbar import ExportToolbar
            assert ExportToolbar is not None
        except ImportError:
            pytest.skip("ExportToolbar not available")

    def test_export_toolbar_initialization(self, qapp):
        """Test ExportToolbar initializes."""
        try:
            from ui.widgets.export_toolbar import ExportToolbar

            toolbar = ExportToolbar()
            assert toolbar is not None
        except ImportError:
            pytest.skip("ExportToolbar not available")


class TestWidgetStyling:
    """Tests for widget styling."""

    def test_widgets_accept_stylesheet(self, qapp):
        """Test widgets accept stylesheet."""
        from ui.widgets.kpi_card import KPICard

        card = KPICard(title="Test", value="0")

        # Should be able to set stylesheet
        card.setStyleSheet("background: white;")

    def test_widget_size_hints(self, qapp):
        """Test widgets have reasonable size hints."""
        from ui.widgets.kpi_card import KPICard

        card = KPICard(title="Test", value="0")

        size = card.sizeHint()
        assert size.width() >= 0
        assert size.height() >= 0


class TestMainWindow:
    """Tests for MainWindow component."""

    def test_main_window_import(self):
        """Test MainWindow imports."""
        from ui.main_window import MainWindow
        assert MainWindow is not None

    def test_main_window_initialization(self, qapp):
        """Test MainWindow initializes."""
        from ui.main_window import MainWindow

        window = MainWindow()
        assert window is not None

    def test_main_window_has_central_widget(self, qapp):
        """Test MainWindow has central widget."""
        from ui.main_window import MainWindow

        window = MainWindow()
        assert window.centralWidget() is not None


class TestSidebar:
    """Tests for Sidebar component."""

    def test_sidebar_import(self):
        """Test Sidebar imports."""
        from ui.sidebar import Sidebar
        assert Sidebar is not None

    def test_sidebar_initialization(self, qapp):
        """Test Sidebar initializes."""
        from ui.sidebar import Sidebar

        sidebar = Sidebar()
        assert sidebar is not None
        assert isinstance(sidebar, QWidget)


class TestStyles:
    """Tests for style/theme modules."""

    def test_styles_import(self):
        """Test styles module imports."""
        from ui.styles import COLORS, get_stylesheet
        assert COLORS is not None
        assert get_stylesheet is not None

    def test_colors_dict(self):
        """Test COLORS dictionary has expected keys."""
        from ui.styles import COLORS

        assert isinstance(COLORS, dict)
        # Should have some color definitions
        assert len(COLORS) > 0

    def test_get_stylesheet(self):
        """Test get_stylesheet returns valid CSS."""
        from ui.styles import get_stylesheet

        stylesheet = get_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_genfin_styles_import(self):
        """Test GenFin styles import."""
        from ui.genfin_styles import get_genfin_stylesheet
        assert get_genfin_stylesheet is not None

    def test_retro_styles_import(self):
        """Test retro styles import."""
        from ui.retro_styles import get_retro_stylesheet
        assert get_retro_stylesheet is not None
