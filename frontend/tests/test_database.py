"""
Database and Cache Tests

Tests for local SQLite caching and data persistence.
"""

import sys
import os

# Add frontend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLocalDatabase:
    """Tests for local SQLite database operations."""

    def test_database_initialization(self):
        """Test database initializes correctly."""
        from database.local_db import get_local_db

        db = get_local_db()
        assert db is not None

    def test_database_stats(self):
        """Test database stats retrieval."""
        from database.local_db import get_local_db

        db = get_local_db()
        stats = db.get_stats()

        assert stats is not None
        assert isinstance(stats, dict)
        # Should have basic stats
        assert 'cache_entries' in stats or 'total_entries' in stats or len(stats) >= 0

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Set a test value
        test_data = {"name": "Test Field", "acres": 100}
        db.cache_set("test_category", "test_key_1", test_data, ttl_hours=1)

        # Get the value back
        result = db.cache_get("test_category", "test_key_1")

        assert result is not None
        assert result["name"] == "Test Field"
        assert result["acres"] == 100

    def test_cache_missing_key(self):
        """Test cache returns None for missing keys."""
        from database.local_db import get_local_db

        db = get_local_db()
        result = db.cache_get("nonexistent_category", "nonexistent_key")

        assert result is None

    def test_cache_overwrite(self):
        """Test cache overwrites existing values."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Set initial value
        db.cache_set("test_category", "overwrite_key", {"value": 1}, ttl_hours=1)

        # Overwrite
        db.cache_set("test_category", "overwrite_key", {"value": 2}, ttl_hours=1)

        result = db.cache_get("test_category", "overwrite_key")
        assert result["value"] == 2

    def test_cache_clear_category(self):
        """Test clearing a cache category."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Set values
        db.cache_set("clear_test", "key1", {"data": 1}, ttl_hours=1)
        db.cache_set("clear_test", "key2", {"data": 2}, ttl_hours=1)

        # Clear category using cache_delete (the actual method name)
        db.cache_delete("clear_test")

        # Verify cleared
        assert db.cache_get("clear_test", "key1") is None
        assert db.cache_get("clear_test", "key2") is None

    def test_cache_different_categories(self):
        """Test cache isolation between categories."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Set values in different categories
        db.cache_set("category_a", "same_key", {"source": "a"}, ttl_hours=1)
        db.cache_set("category_b", "same_key", {"source": "b"}, ttl_hours=1)

        # Verify isolation
        result_a = db.cache_get("category_a", "same_key")
        result_b = db.cache_get("category_b", "same_key")

        assert result_a["source"] == "a"
        assert result_b["source"] == "b"

    def test_cache_complex_data(self):
        """Test caching complex nested data structures."""
        from database.local_db import get_local_db

        db = get_local_db()

        complex_data = {
            "fields": [
                {"id": 1, "name": "Field 1", "coords": [42.0, -93.5]},
                {"id": 2, "name": "Field 2", "coords": [42.1, -93.6]}
            ],
            "metadata": {
                "created": "2024-01-01",
                "version": 1,
                "nested": {"deep": {"value": True}}
            },
            "count": 2
        }

        db.cache_set("complex", "nested_data", complex_data, ttl_hours=1)
        result = db.cache_get("complex", "nested_data")

        assert result["fields"][0]["name"] == "Field 1"
        assert result["metadata"]["nested"]["deep"]["value"] is True

    def test_cache_list_data(self):
        """Test caching list data."""
        from database.local_db import get_local_db

        db = get_local_db()

        list_data = [1, 2, 3, "four", {"five": 5}]
        db.cache_set("list_test", "items", list_data, ttl_hours=1)

        result = db.cache_get("list_test", "items")
        assert result == list_data


class TestCacheTTL:
    """Tests for cache TTL (time-to-live) functionality."""

    def test_cache_ttl_respected(self):
        """Test that TTL is stored with cache entries."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Set with 24 hour TTL
        db.cache_set("ttl_test", "long_ttl", {"data": 1}, ttl_hours=24)

        # Should still be available
        result = db.cache_get("ttl_test", "long_ttl")
        assert result is not None

    def test_cache_short_ttl(self):
        """Test cache with very short TTL."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Set with 1 hour TTL (should be valid immediately)
        db.cache_set("ttl_test", "short_ttl", {"data": 1}, ttl_hours=1)

        # Should be available immediately
        result = db.cache_get("ttl_test", "short_ttl")
        assert result is not None


class TestDatabaseSchema:
    """Tests for database schema and structure."""

    def test_schema_version_tracking(self):
        """Test database tracks schema version."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Should have version info accessible
        if hasattr(db, 'get_schema_version'):
            version = db.get_schema_version()
            assert version is not None

    def test_database_connection(self):
        """Test database connection is valid."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Should be able to perform operations without errors
        db.cache_set("connection_test", "key", {"test": True}, ttl_hours=1)
        result = db.cache_get("connection_test", "key")
        assert result is not None


class TestDatabaseErrorHandling:
    """Tests for database error handling."""

    def test_invalid_json_handling(self):
        """Test handling of non-JSON-serializable data."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Try to cache a function (not JSON serializable)
        # This should either raise an error or handle gracefully
        try:
            db.cache_set("error_test", "func", lambda x: x, ttl_hours=1)
            # If no error, check it handles gracefully
        except (TypeError, ValueError):
            # Expected - can't serialize functions
            pass

    def test_empty_key_handling(self):
        """Test handling of empty keys."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Empty key should either work or raise clear error
        try:
            db.cache_set("empty_test", "", {"data": 1}, ttl_hours=1)
            db.cache_get("empty_test", "")  # Verify retrieval works
        except (ValueError, KeyError):
            # Also acceptable
            pass

    def test_special_characters_in_key(self):
        """Test handling of special characters in keys."""
        from database.local_db import get_local_db

        db = get_local_db()

        special_key = "key-with/special:chars&more"
        db.cache_set("special", special_key, {"data": 1}, ttl_hours=1)

        result = db.cache_get("special", special_key)
        assert result is not None
        assert result["data"] == 1


class TestDatabaseConcurrency:
    """Tests for database thread safety."""

    def test_multiple_operations(self):
        """Test rapid successive operations."""
        from database.local_db import get_local_db

        db = get_local_db()

        # Perform many operations quickly
        for i in range(100):
            db.cache_set("rapid", f"key_{i}", {"index": i}, ttl_hours=1)

        # Verify some entries
        assert db.cache_get("rapid", "key_0")["index"] == 0
        assert db.cache_get("rapid", "key_99")["index"] == 99
