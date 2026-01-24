"""
AgTools Local Database

SQLite database for caching API data and enabling offline functionality.
Stores prices, pest/disease data, crop parameters, and user preferences.
"""

import sqlite3
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import threading

from config import USER_DATA_DIR


# Database file location
DB_PATH = USER_DATA_DIR / "agtools_cache.db"

# Schema version for migrations
SCHEMA_VERSION = 1


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    key: str
    data: Any
    cached_at: datetime
    expires_at: Optional[datetime]
    category: str

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class LocalDatabase:
    """
    SQLite database manager for offline caching.

    Features:
    - Thread-safe connection management
    - Automatic schema initialization
    - Cache invalidation by TTL
    - Category-based data organization

    Usage:
        db = get_local_db()
        db.cache_set("prices", "all_prices", price_data, ttl_hours=24)
        prices = db.cache_get("prices", "all_prices")
    """

    _local = threading.local()

    def __init__(self):
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._local.connection = sqlite3.connect(
                str(DB_PATH),
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create schema version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)

        # Check current version
        cursor.execute("SELECT version FROM schema_version LIMIT 1")
        row = cursor.fetchone()
        current_version = row[0] if row else 0

        if current_version < SCHEMA_VERSION:
            self._migrate_schema(cursor, current_version)
            cursor.execute("DELETE FROM schema_version")
            cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.commit()

    def _migrate_schema(self, cursor: sqlite3.Cursor, from_version: int) -> None:
        """Apply schema migrations."""
        if from_version < 1:
            # Initial schema
            self._create_tables(cursor)

    def _create_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create all database tables."""

        # General cache table for API responses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                cache_key TEXT NOT NULL,
                data TEXT NOT NULL,
                cached_at TEXT NOT NULL,
                expires_at TEXT,
                UNIQUE(category, cache_key)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_category ON cache(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")

        # Product prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                base_price REAL NOT NULL,
                current_price REAL,
                price_source TEXT DEFAULT 'default',
                region TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")

        # Custom user prices (from suppliers)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                price REAL NOT NULL,
                supplier TEXT,
                quote_date TEXT,
                expiry_date TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_custom_prices_synced ON custom_prices(synced)")

        # Pest/Disease knowledge base
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pests (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                scientific_name TEXT,
                crop TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                damage_symptoms TEXT,
                identification TEXT,
                economic_threshold TEXT,
                management TEXT,
                data_json TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pests_crop ON pests(crop)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diseases (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                scientific_name TEXT,
                crop TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                symptoms TEXT,
                favorable_conditions TEXT,
                management TEXT,
                data_json TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_diseases_crop ON diseases(crop)")

        # Crop parameters for yield response calculations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop_parameters (
                crop TEXT PRIMARY KEY,
                parameters_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # User's calculation history (for offline reference)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calculation_type TEXT NOT NULL,
                inputs_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                notes TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_calc_history_type ON calculation_history(calculation_type)")

        # Sync queue for offline changes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                payload_json TEXT,
                created_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_attempt TEXT,
                error_message TEXT
            )
        """)

        # User settings cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings_cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

    # -------------------------------------------------------------------------
    # General Cache Methods
    # -------------------------------------------------------------------------

    def cache_set(self, category: str, key: str, data: Any, ttl_hours: Optional[int] = None) -> None:
        """
        Store data in the cache.

        Args:
            category: Cache category (e.g., "prices", "pests", "yield_response")
            key: Unique key within the category
            data: Data to cache (will be JSON serialized)
            ttl_hours: Optional TTL in hours (None = never expires)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        expires_at = (now + timedelta(hours=ttl_hours)) if ttl_hours else None

        cursor.execute("""
            INSERT OR REPLACE INTO cache (category, cache_key, data, cached_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            category,
            key,
            json.dumps(data),
            now.isoformat(),
            expires_at.isoformat() if expires_at else None
        ))
        conn.commit()

    def cache_get(self, category: str, key: str) -> Optional[Any]:
        """
        Retrieve data from the cache.

        Args:
            category: Cache category
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data, expires_at FROM cache
            WHERE category = ? AND cache_key = ?
        """, (category, key))

        row = cursor.fetchone()
        if not row:
            return None

        # Check expiration
        if row['expires_at']:
            expires_at = datetime.fromisoformat(row['expires_at'])
            if datetime.now() > expires_at:
                # Expired - delete and return None
                cursor.execute("""
                    DELETE FROM cache WHERE category = ? AND cache_key = ?
                """, (category, key))
                conn.commit()
                return None

        return json.loads(row['data'])

    def cache_delete(self, category: str, key: Optional[str] = None) -> int:
        """
        Delete cache entries.

        Args:
            category: Cache category
            key: Optional specific key (if None, deletes all in category)

        Returns:
            Number of deleted entries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if key:
            cursor.execute("""
                DELETE FROM cache WHERE category = ? AND cache_key = ?
            """, (category, key))
        else:
            cursor.execute("DELETE FROM cache WHERE category = ?", (category,))

        conn.commit()
        return cursor.rowcount

    def cache_clear_expired(self) -> int:
        """Remove all expired cache entries."""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute("""
            DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (now,))

        conn.commit()
        return cursor.rowcount

    # -------------------------------------------------------------------------
    # Product/Price Methods
    # -------------------------------------------------------------------------

    def save_products(self, products: List[Dict]) -> int:
        """
        Save/update products in the database.

        Args:
            products: List of product dictionaries from the API

        Returns:
            Number of products saved
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        for product in products:
            cursor.execute("""
                INSERT OR REPLACE INTO products
                (id, name, category, unit, base_price, current_price, price_source, region, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.get('id', product.get('name', '').lower().replace(' ', '_')),
                product.get('name'),
                product.get('category'),
                product.get('unit', 'unit'),
                product.get('base_price', product.get('price', 0)),
                product.get('current_price', product.get('price')),
                product.get('source', 'default'),
                product.get('region'),
                now
            ))

        conn.commit()
        return len(products)

    def get_products(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get products from local database.

        Args:
            category: Optional category filter

        Returns:
            List of product dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if category:
            cursor.execute("""
                SELECT * FROM products WHERE category = ? ORDER BY name
            """, (category,))
        else:
            cursor.execute("SELECT * FROM products ORDER BY category, name")

        return [dict(row) for row in cursor.fetchall()]

    def get_product_price(self, product_id: str) -> Optional[Dict]:
        """Get a specific product with its current price."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def save_custom_price(self, product_id: str, price: float, supplier: str = None,
                          expiry_date: str = None, notes: str = None) -> int:
        """
        Save a custom supplier price.

        Args:
            product_id: Product identifier
            price: Custom price
            supplier: Supplier name
            expiry_date: Quote expiration date
            notes: Optional notes

        Returns:
            ID of the created record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO custom_prices
            (product_id, price, supplier, quote_date, expiry_date, notes, created_at, synced)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (product_id, price, supplier, now, expiry_date, notes, now))

        # Update current price in products table
        cursor.execute("""
            UPDATE products SET current_price = ?, price_source = 'custom', updated_at = ?
            WHERE id = ?
        """, (price, now, product_id))

        conn.commit()
        return cursor.lastrowid

    def get_unsynced_prices(self) -> List[Dict]:
        """Get custom prices that haven't been synced to the server."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cp.*, p.name as product_name
            FROM custom_prices cp
            JOIN products p ON cp.product_id = p.id
            WHERE cp.synced = 0
            ORDER BY cp.created_at
        """)

        return [dict(row) for row in cursor.fetchall()]

    def mark_price_synced(self, price_id: int) -> None:
        """Mark a custom price as synced."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE custom_prices SET synced = 1 WHERE id = ?", (price_id,))
        conn.commit()

    # -------------------------------------------------------------------------
    # Pest/Disease Methods
    # -------------------------------------------------------------------------

    def save_pests(self, pests: List[Dict]) -> int:
        """Save pest data to local database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        for pest in pests:
            cursor.execute("""
                INSERT OR REPLACE INTO pests
                (id, name, scientific_name, crop, category, description,
                 damage_symptoms, identification, economic_threshold, management, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pest.get('id', pest.get('name', '').lower().replace(' ', '_')),
                pest.get('name'),
                pest.get('scientific_name'),
                pest.get('crop'),
                pest.get('category', 'insect'),
                pest.get('description'),
                pest.get('damage_symptoms'),
                pest.get('identification'),
                pest.get('economic_threshold'),
                pest.get('management'),
                json.dumps(pest),
                now
            ))

        conn.commit()
        return len(pests)

    def get_pests(self, crop: Optional[str] = None) -> List[Dict]:
        """Get pests from local database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if crop:
            cursor.execute("SELECT data_json FROM pests WHERE crop = ?", (crop,))
        else:
            cursor.execute("SELECT data_json FROM pests")

        return [json.loads(row['data_json']) for row in cursor.fetchall()]

    def save_diseases(self, diseases: List[Dict]) -> int:
        """Save disease data to local database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        for disease in diseases:
            cursor.execute("""
                INSERT OR REPLACE INTO diseases
                (id, name, scientific_name, crop, category, description,
                 symptoms, favorable_conditions, management, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                disease.get('id', disease.get('name', '').lower().replace(' ', '_')),
                disease.get('name'),
                disease.get('scientific_name'),
                disease.get('crop'),
                disease.get('category', 'fungal'),
                disease.get('description'),
                disease.get('symptoms'),
                disease.get('favorable_conditions'),
                disease.get('management'),
                json.dumps(disease),
                now
            ))

        conn.commit()
        return len(diseases)

    def get_diseases(self, crop: Optional[str] = None) -> List[Dict]:
        """Get diseases from local database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if crop:
            cursor.execute("SELECT data_json FROM diseases WHERE crop = ?", (crop,))
        else:
            cursor.execute("SELECT data_json FROM diseases")

        return [json.loads(row['data_json']) for row in cursor.fetchall()]

    # -------------------------------------------------------------------------
    # Crop Parameters Methods
    # -------------------------------------------------------------------------

    def save_crop_parameters(self, crop: str, parameters: Dict) -> None:
        """Save crop agronomic parameters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO crop_parameters (crop, parameters_json, updated_at)
            VALUES (?, ?, ?)
        """, (crop, json.dumps(parameters), now))
        conn.commit()

    def get_crop_parameters(self, crop: str) -> Optional[Dict]:
        """Get crop parameters from local database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT parameters_json FROM crop_parameters WHERE crop = ?", (crop,))
        row = cursor.fetchone()
        return json.loads(row['parameters_json']) if row else None

    def get_all_crop_parameters(self) -> Dict[str, Dict]:
        """Get all crop parameters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT crop, parameters_json FROM crop_parameters")
        return {row['crop']: json.loads(row['parameters_json']) for row in cursor.fetchall()}

    # -------------------------------------------------------------------------
    # Calculation History Methods
    # -------------------------------------------------------------------------

    def save_calculation(self, calc_type: str, inputs: Dict, results: Dict, notes: str = None) -> int:
        """Save a calculation to history."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO calculation_history (calculation_type, inputs_json, results_json, created_at, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (calc_type, json.dumps(inputs), json.dumps(results), now, notes))

        conn.commit()
        return cursor.lastrowid

    def get_calculations(self, calc_type: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get calculation history."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if calc_type:
            cursor.execute("""
                SELECT * FROM calculation_history
                WHERE calculation_type = ?
                ORDER BY created_at DESC LIMIT ?
            """, (calc_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM calculation_history
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))

        results = []
        for row in cursor.fetchall():
            item = dict(row)
            item['inputs'] = json.loads(item['inputs_json'])
            item['results'] = json.loads(item['results_json'])
            del item['inputs_json']
            del item['results_json']
            results.append(item)

        return results

    # -------------------------------------------------------------------------
    # Sync Queue Methods
    # -------------------------------------------------------------------------

    def queue_sync_action(self, action: str, endpoint: str, payload: Dict = None) -> int:
        """Add an action to the sync queue for when online."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO sync_queue (action, endpoint, payload_json, created_at)
            VALUES (?, ?, ?, ?)
        """, (action, endpoint, json.dumps(payload) if payload else None, now))

        conn.commit()
        return cursor.lastrowid

    def get_pending_sync_actions(self) -> List[Dict]:
        """Get all pending sync actions."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sync_queue ORDER BY created_at
        """)

        results = []
        for row in cursor.fetchall():
            item = dict(row)
            item['payload'] = json.loads(item['payload_json']) if item['payload_json'] else None
            del item['payload_json']
            results.append(item)

        return results

    def mark_sync_attempted(self, sync_id: int, error: str = None) -> None:
        """Mark a sync action as attempted."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            UPDATE sync_queue
            SET attempts = attempts + 1, last_attempt = ?, error_message = ?
            WHERE id = ?
        """, (now, error, sync_id))
        conn.commit()

    def remove_sync_action(self, sync_id: int) -> None:
        """Remove a completed sync action."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_queue WHERE id = ?", (sync_id,))
        conn.commit()

    def get_sync_queue_count(self) -> int:
        """Get count of pending sync actions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sync_queue")
        return cursor.fetchone()['count']

    # -------------------------------------------------------------------------
    # Settings Cache Methods
    # -------------------------------------------------------------------------

    def save_setting(self, key: str, value: Any) -> None:
        """Save a setting to the cache."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO settings_cache (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, json.dumps(value), now))
        conn.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting from the cache."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM settings_cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        return json.loads(row['value']) if row else default

    # -------------------------------------------------------------------------
    # Database Maintenance
    # -------------------------------------------------------------------------

    def vacuum(self) -> None:
        """Optimize database file size."""
        conn = self._get_connection()
        conn.execute("VACUUM")

    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}
        tables = ['cache', 'products', 'custom_prices', 'pests', 'diseases',
                  'crop_parameters', 'calculation_history', 'sync_queue']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()['count']

        # Database file size
        if DB_PATH.exists():
            stats['file_size_mb'] = round(DB_PATH.stat().st_size / (1024 * 1024), 2)

        return stats

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None


# Singleton instance
_local_db: Optional[LocalDatabase] = None


def get_local_db() -> LocalDatabase:
    """Get the global LocalDatabase instance."""
    global _local_db
    if _local_db is None:
        _local_db = LocalDatabase()
    return _local_db


def reset_local_db() -> None:
    """Reset the database instance (useful for testing)."""
    global _local_db
    if _local_db:
        _local_db.close()
    _local_db = None
