"""
AgTools Sync Manager

Manages synchronization between local database and API server.
Handles online/offline detection, data syncing, and conflict resolution.
"""

import httpx
from typing import Any, Optional, Callable, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading

from PyQt6.QtCore import QObject, pyqtSignal, QTimer

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_settings
from database.local_db import get_local_db


class ConnectionState(Enum):
    """Connection state enumeration."""
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"


class SyncStatus(Enum):
    """Sync operation status."""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    status: SyncStatus
    synced_items: int = 0
    failed_items: int = 0
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class SyncManager(QObject):
    """
    Manages data synchronization and online/offline state.

    Features:
    - Periodic connection checking
    - Automatic fallback to offline mode
    - Background sync when connection restored
    - Sync queue for offline changes
    - Conflict resolution (server wins by default)

    Signals:
        connection_changed: Emitted when connection state changes
        sync_started: Emitted when sync begins
        sync_completed: Emitted when sync completes with SyncResult
        sync_progress: Emitted during sync with (current, total) progress

    Usage:
        sync_manager = get_sync_manager()
        sync_manager.connection_changed.connect(on_connection_change)
        sync_manager.start_monitoring()
    """

    # Signals
    connection_changed = pyqtSignal(ConnectionState)
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(object)  # SyncResult
    sync_progress = pyqtSignal(int, int)  # current, total
    data_updated = pyqtSignal(str)  # category that was updated

    def __init__(self):
        super().__init__()
        self._settings = get_settings()
        self._db = get_local_db()

        self._state = ConnectionState.UNKNOWN
        self._last_check: Optional[datetime] = None
        self._last_sync: Optional[datetime] = None
        self._sync_in_progress = False

        # Connection monitoring
        self._check_interval_ms = 30000  # 30 seconds
        self._check_timer: Optional[QTimer] = None

        # Retry settings
        self._max_retries = 3
        self._retry_delay_seconds = 5

    @property
    def is_online(self) -> bool:
        """Check if currently online."""
        return self._state == ConnectionState.ONLINE

    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    @property
    def last_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync."""
        return self._last_sync

    @property
    def pending_sync_count(self) -> int:
        """Get number of items waiting to sync."""
        return self._db.get_sync_queue_count()

    def start_monitoring(self) -> None:
        """Start periodic connection monitoring."""
        if self._check_timer is None:
            self._check_timer = QTimer()
            self._check_timer.timeout.connect(self._periodic_check)
            self._check_timer.start(self._check_interval_ms)

        # Initial check
        self.check_connection()

    def stop_monitoring(self) -> None:
        """Stop connection monitoring."""
        if self._check_timer:
            self._check_timer.stop()
            self._check_timer = None

    def check_connection(self) -> bool:
        """
        Check if the API is reachable.

        Returns:
            True if online, False otherwise
        """
        previous_state = self._state

        try:
            response = httpx.get(
                f"{self._settings.api.base_url}/",
                timeout=5.0
            )
            if response.status_code == 200:
                self._set_state(ConnectionState.ONLINE)
                self._last_check = datetime.now()

                # Trigger sync if we just came online and have pending items
                if previous_state != ConnectionState.ONLINE:
                    pending = self.pending_sync_count
                    if pending > 0:
                        self._trigger_background_sync()

                return True
        except Exception:
            pass

        self._set_state(ConnectionState.OFFLINE)
        self._last_check = datetime.now()
        return False

    def _periodic_check(self) -> None:
        """Periodic connection check callback."""
        self.check_connection()

    def _set_state(self, new_state: ConnectionState) -> None:
        """Set connection state and emit signal if changed."""
        if self._state != new_state:
            self._state = new_state
            self.connection_changed.emit(new_state)

    def _trigger_background_sync(self) -> None:
        """Start a background sync operation."""
        if not self._sync_in_progress:
            threading.Thread(target=self._sync_pending, daemon=True).start()

    # -------------------------------------------------------------------------
    # Data Sync Methods
    # -------------------------------------------------------------------------

    def sync_all(self) -> SyncResult:
        """
        Perform a full sync operation.

        This syncs:
        1. Local changes to server (pending queue)
        2. Server data to local cache (prices, pests, etc.)

        Returns:
            SyncResult with status and counts
        """
        if self._sync_in_progress:
            return SyncResult(status=SyncStatus.FAILED, errors=["Sync already in progress"])

        if not self.is_online:
            return SyncResult(status=SyncStatus.FAILED, errors=["Not connected to server"])

        self._sync_in_progress = True
        self._set_state(ConnectionState.SYNCING)
        self.sync_started.emit()

        result = SyncResult(status=SyncStatus.SYNCING)

        try:
            # 1. Push pending changes
            push_result = self._sync_pending()
            result.synced_items += push_result.synced_items
            result.failed_items += push_result.failed_items
            result.errors.extend(push_result.errors)

            # 2. Pull fresh data from server
            pull_result = self._pull_data()
            result.synced_items += pull_result.synced_items
            result.failed_items += pull_result.failed_items
            result.errors.extend(pull_result.errors)

            # Determine final status
            if result.failed_items == 0:
                result.status = SyncStatus.SUCCESS
            elif result.synced_items > 0:
                result.status = SyncStatus.PARTIAL
            else:
                result.status = SyncStatus.FAILED

            self._last_sync = datetime.now()
            self._settings.last_sync = self._last_sync.isoformat()
            self._settings.save()

        except Exception as e:
            result.status = SyncStatus.FAILED
            result.errors.append(f"Sync error: {str(e)}")

        finally:
            self._sync_in_progress = False
            self._set_state(ConnectionState.ONLINE if self.check_connection() else ConnectionState.OFFLINE)
            self.sync_completed.emit(result)

        return result

    def _sync_pending(self) -> SyncResult:
        """Push pending local changes to server."""
        result = SyncResult(status=SyncStatus.SYNCING)
        pending_actions = self._db.get_pending_sync_actions()

        total = len(pending_actions)
        for i, action in enumerate(pending_actions):
            self.sync_progress.emit(i + 1, total)

            try:
                success = self._execute_sync_action(action)
                if success:
                    self._db.remove_sync_action(action['id'])
                    result.synced_items += 1
                else:
                    self._db.mark_sync_attempted(action['id'], "Request failed")
                    result.failed_items += 1
            except Exception as e:
                self._db.mark_sync_attempted(action['id'], str(e))
                result.errors.append(f"Failed to sync action {action['id']}: {str(e)}")
                result.failed_items += 1

        # Also sync custom prices
        unsynced_prices = self._db.get_unsynced_prices()
        for price in unsynced_prices:
            try:
                success = self._sync_custom_price(price)
                if success:
                    self._db.mark_price_synced(price['id'])
                    result.synced_items += 1
            except Exception as e:
                result.errors.append(f"Failed to sync price: {str(e)}")
                result.failed_items += 1

        return result

    def _execute_sync_action(self, action: Dict) -> bool:
        """Execute a queued sync action."""
        method = action['action'].upper()
        endpoint = action['endpoint']
        payload = action.get('payload')

        try:
            base_url = self._settings.api.full_url

            if method == 'POST':
                response = httpx.post(f"{base_url}{endpoint}", json=payload, timeout=30.0)
            elif method == 'PUT':
                response = httpx.put(f"{base_url}{endpoint}", json=payload, timeout=30.0)
            elif method == 'DELETE':
                response = httpx.delete(f"{base_url}{endpoint}", timeout=30.0)
            else:
                return False

            return response.is_success

        except Exception:
            return False

    def _sync_custom_price(self, price: Dict) -> bool:
        """Sync a custom price to the server."""
        try:
            base_url = self._settings.api.full_url
            payload = {
                "product_id": price['product_id'],
                "price": price['price'],
                "supplier": price.get('supplier'),
                "expiry_date": price.get('expiry_date'),
                "notes": price.get('notes')
            }

            response = httpx.post(
                f"{base_url}/pricing/set-price",
                json=payload,
                timeout=30.0
            )
            return response.is_success

        except Exception:
            return False

    def _pull_data(self) -> SyncResult:
        """Pull fresh data from server to local cache."""
        result = SyncResult(status=SyncStatus.SYNCING)
        categories = ['prices', 'pests', 'diseases', 'crop_parameters']

        total = len(categories)
        for i, category in enumerate(categories):
            self.sync_progress.emit(i + 1, total)

            try:
                if category == 'prices':
                    count = self._pull_prices()
                elif category == 'pests':
                    count = self._pull_pests()
                elif category == 'diseases':
                    count = self._pull_diseases()
                elif category == 'crop_parameters':
                    count = self._pull_crop_parameters()
                else:
                    count = 0

                result.synced_items += count
                self.data_updated.emit(category)

            except Exception as e:
                result.errors.append(f"Failed to pull {category}: {str(e)}")
                result.failed_items += 1

        return result

    def _pull_prices(self) -> int:
        """Pull product prices from server."""
        try:
            base_url = self._settings.api.full_url
            response = httpx.get(f"{base_url}/pricing/prices", timeout=30.0)

            if response.is_success:
                data = response.json()
                products = data if isinstance(data, list) else data.get('products', [])
                return self._db.save_products(products)
        except Exception:
            pass
        return 0

    def _pull_pests(self) -> int:
        """Pull pest data from server."""
        count = 0
        crops = ['corn', 'soybean', 'wheat']

        for crop in crops:
            try:
                base_url = self._settings.api.full_url
                response = httpx.post(
                    f"{base_url}/pests/identify",
                    json={"crop": crop, "symptoms": []},
                    timeout=30.0
                )

                if response.is_success:
                    data = response.json()
                    pests = data.get('possible_pests', [])
                    count += self._db.save_pests(pests)
            except Exception:
                pass

        return count

    def _pull_diseases(self) -> int:
        """Pull disease data from server."""
        count = 0
        crops = ['corn', 'soybean', 'wheat']

        for crop in crops:
            try:
                base_url = self._settings.api.full_url
                response = httpx.post(
                    f"{base_url}/diseases/identify",
                    json={"crop": crop, "symptoms": []},
                    timeout=30.0
                )

                if response.is_success:
                    data = response.json()
                    diseases = data.get('possible_diseases', [])
                    count += self._db.save_diseases(diseases)
            except Exception:
                pass

        return count

    def _pull_crop_parameters(self) -> int:
        """Pull crop parameters from server."""
        count = 0
        crops = ['corn', 'soybean', 'wheat']

        for crop in crops:
            try:
                base_url = self._settings.api.full_url
                response = httpx.get(
                    f"{base_url}/yield-response/crop-parameters/{crop}",
                    timeout=30.0
                )

                if response.is_success:
                    params = response.json()
                    self._db.save_crop_parameters(crop, params)
                    count += 1
            except Exception:
                pass

        return count

    # -------------------------------------------------------------------------
    # Queue Methods (for offline operations)
    # -------------------------------------------------------------------------

    def queue_action(self, action: str, endpoint: str, payload: Dict = None) -> int:
        """
        Queue an action for later sync.

        Use this when offline to queue changes that will be synced
        when connection is restored.

        Args:
            action: HTTP method (POST, PUT, DELETE)
            endpoint: API endpoint
            payload: Request payload

        Returns:
            Queue ID
        """
        return self._db.queue_sync_action(action, endpoint, payload)

    # -------------------------------------------------------------------------
    # Cache Helpers
    # -------------------------------------------------------------------------

    def get_cached_or_fetch(self, category: str, key: str, fetch_func: Callable,
                            ttl_hours: int = 24) -> Optional[Any]:
        """
        Get data from cache or fetch from API.

        Args:
            category: Cache category
            key: Cache key
            fetch_func: Function to call to fetch fresh data (returns the data)
            ttl_hours: Cache TTL in hours

        Returns:
            Data from cache or fresh fetch, or None if both fail
        """
        # Try cache first
        cached = self._db.cache_get(category, key)
        if cached is not None:
            return cached

        # Try to fetch if online
        if self.is_online:
            try:
                data = fetch_func()
                if data is not None:
                    self._db.cache_set(category, key, data, ttl_hours)
                    return data
            except Exception:
                pass

        return None

    def invalidate_cache(self, category: str, key: Optional[str] = None) -> None:
        """Invalidate cache entries."""
        self._db.cache_delete(category, key)


# Singleton instance
_sync_manager: Optional[SyncManager] = None


def get_sync_manager() -> SyncManager:
    """Get the global SyncManager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager


def reset_sync_manager() -> None:
    """Reset the sync manager instance."""
    global _sync_manager
    if _sync_manager:
        _sync_manager.stop_monitoring()
    _sync_manager = None
