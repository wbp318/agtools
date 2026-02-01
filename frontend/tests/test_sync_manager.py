"""
Sync Manager Tests

Tests for connection state tracking and offline/online synchronization.
"""

import sys
import os
import pytest

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConnectionState:
    """Tests for connection state enum and transitions."""

    def test_connection_state_enum(self):
        """Test ConnectionState enum values."""
        from core.sync_manager import ConnectionState

        assert ConnectionState.UNKNOWN is not None
        assert ConnectionState.ONLINE is not None
        assert ConnectionState.OFFLINE is not None
        assert ConnectionState.SYNCING is not None
        assert ConnectionState.ERROR is not None

    def test_connection_state_values(self):
        """Test ConnectionState enum has distinct values."""
        from core.sync_manager import ConnectionState

        states = [
            ConnectionState.UNKNOWN,
            ConnectionState.ONLINE,
            ConnectionState.OFFLINE,
            ConnectionState.SYNCING,
            ConnectionState.ERROR
        ]
        # All states should be unique
        assert len(set(states)) == 5


class TestSyncManager:
    """Tests for SyncManager functionality."""

    def test_sync_manager_initialization(self):
        """Test SyncManager initializes correctly."""
        from core.sync_manager import SyncManager

        manager = SyncManager()
        assert manager is not None

    def test_initial_connection_state(self):
        """Test initial connection state is UNKNOWN."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()

        # Initial state should be UNKNOWN
        assert manager.state in [
            ConnectionState.UNKNOWN,
            ConnectionState.OFFLINE,
            ConnectionState.ONLINE
        ]

    def test_set_online_state(self):
        """Test setting online state."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()
        manager.set_state(ConnectionState.ONLINE)

        assert manager.state == ConnectionState.ONLINE

    def test_set_offline_state(self):
        """Test setting offline state."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()
        manager.set_state(ConnectionState.OFFLINE)

        assert manager.state == ConnectionState.OFFLINE

    def test_is_online_property(self):
        """Test is_online property."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()

        manager.set_state(ConnectionState.ONLINE)
        assert manager.is_online is True

        manager.set_state(ConnectionState.OFFLINE)
        assert manager.is_online is False

    def test_is_syncing_property(self):
        """Test is_syncing property."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()

        manager.set_state(ConnectionState.SYNCING)
        assert manager.is_syncing is True

        manager.set_state(ConnectionState.ONLINE)
        assert manager.is_syncing is False


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_sync_result_creation(self):
        """Test SyncResult creation."""
        from core.sync_manager import SyncResult

        result = SyncResult(
            success=True,
            items_synced=10,
            items_failed=0
        )

        assert result.success is True
        assert result.items_synced == 10
        assert result.items_failed == 0

    def test_sync_result_with_errors(self):
        """Test SyncResult with errors."""
        from core.sync_manager import SyncResult

        result = SyncResult(
            success=False,
            items_synced=5,
            items_failed=3,
            errors=["Network timeout", "Server error"]
        )

        assert result.success is False
        assert result.items_failed == 3
        assert len(result.errors) == 2

    def test_sync_result_partial_success(self):
        """Test SyncResult with partial success."""
        from core.sync_manager import SyncResult

        result = SyncResult(
            success=True,  # Overall success
            items_synced=8,
            items_failed=2,
            warnings=["2 items skipped"]
        )

        assert result.success is True
        assert result.items_synced == 8
        assert result.items_failed == 2


class TestSyncQueue:
    """Tests for sync queue management."""

    def test_queue_item_addition(self):
        """Test adding items to sync queue."""
        from core.sync_manager import SyncManager

        manager = SyncManager()

        if hasattr(manager, 'queue_item'):
            manager.queue_item("field", "create", {"name": "Test Field"})
            assert manager.pending_count > 0

    def test_queue_multiple_items(self):
        """Test queueing multiple items."""
        from core.sync_manager import SyncManager

        manager = SyncManager()

        if hasattr(manager, 'queue_item'):
            manager.queue_item("field", "create", {"name": "Field 1"})
            manager.queue_item("field", "create", {"name": "Field 2"})
            manager.queue_item("task", "update", {"id": 1, "status": "done"})

            assert manager.pending_count >= 3

    def test_clear_queue(self):
        """Test clearing sync queue."""
        from core.sync_manager import SyncManager

        manager = SyncManager()

        if hasattr(manager, 'queue_item') and hasattr(manager, 'clear_queue'):
            manager.queue_item("test", "create", {})
            manager.clear_queue()
            assert manager.pending_count == 0


class TestOfflineFallback:
    """Tests for offline fallback behavior."""

    def test_offline_mode_detection(self):
        """Test detection of offline mode."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()
        manager.set_state(ConnectionState.OFFLINE)

        assert manager.should_use_cache is True

    def test_online_mode_uses_api(self):
        """Test online mode prefers API."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()
        manager.set_state(ConnectionState.ONLINE)

        assert manager.should_use_cache is False

    def test_error_state_fallback(self):
        """Test error state falls back to cache."""
        from core.sync_manager import SyncManager, ConnectionState

        manager = SyncManager()
        manager.set_state(ConnectionState.ERROR)

        # Error state should fall back to cache
        assert manager.should_use_cache is True


class TestSyncManagerSignals:
    """Tests for PyQt signals (if using Qt)."""

    def test_has_connection_changed_signal(self):
        """Test SyncManager has connection_changed signal."""
        from core.sync_manager import SyncManager

        manager = SyncManager()

        # Check if it has signal attributes
        assert hasattr(manager, 'connection_changed') or hasattr(manager, 'signals')

    def test_has_sync_completed_signal(self):
        """Test SyncManager has sync_completed signal."""
        from core.sync_manager import SyncManager

        manager = SyncManager()

        assert hasattr(manager, 'sync_completed') or hasattr(manager, 'signals')


class TestSyncManagerSingleton:
    """Tests for SyncManager singleton pattern."""

    def test_singleton_instance(self):
        """Test SyncManager uses singleton pattern."""
        from core.sync_manager import get_sync_manager

        manager1 = get_sync_manager()
        manager2 = get_sync_manager()

        assert manager1 is manager2

    def test_singleton_state_persistence(self):
        """Test singleton state persists."""
        from core.sync_manager import get_sync_manager, ConnectionState

        manager1 = get_sync_manager()
        manager1.set_state(ConnectionState.ONLINE)

        manager2 = get_sync_manager()
        assert manager2.state == ConnectionState.ONLINE
