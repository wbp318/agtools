"""
AgTools Core Package

Core functionality including:
- Sync manager for online/offline operation
- Offline calculation engines
"""

from core.sync_manager import (
    SyncManager,
    get_sync_manager,
    reset_sync_manager,
    ConnectionState,
    SyncStatus,
    SyncResult
)

__all__ = [
    "SyncManager",
    "get_sync_manager",
    "reset_sync_manager",
    "ConnectionState",
    "SyncStatus",
    "SyncResult",
]
