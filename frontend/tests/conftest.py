"""
Frontend Test Configuration

Pytest fixtures and configuration for frontend tests.
"""

import sys
import os
import pytest

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def qapp():
    """Create a single QApplication for the entire test session."""
    # Skip if PyQt6 not available
    pytest.importorskip("PyQt6")

    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test to prevent Qt object lifetime issues."""
    # Reset sync manager to prevent "wrapped C/C++ object deleted" errors
    try:
        from core.sync_manager import reset_sync_manager
        reset_sync_manager()
    except ImportError:
        pass

    yield

    # Clean up after test
    try:
        from core.sync_manager import reset_sync_manager
        reset_sync_manager()
    except ImportError:
        pass
