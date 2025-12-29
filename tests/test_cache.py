"""Tests for cache manager with TTL functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.db.cache import CacheManager, CACHE_TTL
from src.db.models import SearchCacheDB, IncomeCacheDB, ApiCallLogDB


class TestCacheManager:
    """Tests for CacheManager basic operations."""

    def test_cache_key_generation_consistent(self, test_session):
        """Test that cache keys are consistently generated."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix", "state": "AZ", "max_price": 300000}
        key1 = cache._make_cache_key("provider1", "search", params)
        key2 = cache._make_cache_key("provider1", "search", params)

        assert key1 == key2

    def test_cache_key_different_for_different_params(self, test_session):
        """Test that different params produce different keys."""
        cache = CacheManager(test_session)

        key1 = cache._make_cache_key("provider1", "search", {"city": "Phoenix"})
        key2 = cache._make_cache_key("provider1", "search", {"city": "Tampa"})

        assert key1 != key2

    def test_cache_key_different_for_different_providers(self, test_session):
        """Test that different providers produce different keys."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        key1 = cache._make_cache_key("provider1", "search", params)
        key2 = cache._make_cache_key("provider2", "search", params)

        assert key1 != key2

    def test_cache_key_param_order_independent(self, test_session):
        """Test that param order doesn't affect cache key."""
        cache = CacheManager(test_session)

        params1 = {"city": "Phoenix", "state": "AZ"}
        params2 = {"state": "AZ", "city": "Phoenix"}

        key1 = cache._make_cache_key("provider", "search", params1)
        key2 = cache._make_cache_key("provider", "search", params2)

        assert key1 == key2


class TestCacheSetAndGet:
    """Tests for cache set and get operations."""

    def test_set_and_get_cache(self, test_session):
        """Test basic cache set and get."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix", "state": "AZ"}
        results = {"properties": [{"id": "test1", "price": 250000}]}

        cache.set("test_provider", "search", params, results)
        retrieved = cache.get("test_provider", "search", params)

        assert retrieved is not None
        assert retrieved["properties"][0]["id"] == "test1"

    def test_get_nonexistent_cache(self, test_session):
        """Test getting a non-existent cache entry."""
        cache = CacheManager(test_session)

        result = cache.get("nonexistent", "search", {"city": "Phoenix"})

        assert result is None

    def test_cache_uses_default_ttl(self, test_session):
        """Test that cache uses default TTL from CACHE_TTL dict."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        results = {"properties": []}

        cache.set("test_provider", "search", params, results)

        # Verify the entry was created with correct TTL
        cache_key = cache._make_cache_key("test_provider", "search", params)
        entry = test_session.query(SearchCacheDB).filter_by(cache_key=cache_key).first()

        # Search TTL is 1 hour
        expected_ttl = CACHE_TTL["search"]
        actual_ttl = (entry.expires_at - entry.created_at).total_seconds() / 3600

        assert abs(actual_ttl - expected_ttl) < 0.01

    def test_cache_uses_custom_ttl(self, test_session):
        """Test that custom TTL is respected."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        results = {"properties": []}
        custom_ttl = 48  # 48 hours

        cache.set("test_provider", "search", params, results, ttl_hours=custom_ttl)

        cache_key = cache._make_cache_key("test_provider", "search", params)
        entry = test_session.query(SearchCacheDB).filter_by(cache_key=cache_key).first()

        actual_ttl = (entry.expires_at - entry.created_at).total_seconds() / 3600

        assert abs(actual_ttl - custom_ttl) < 0.01

    def test_cache_upsert(self, test_session):
        """Test that setting cache with same key updates the entry."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        results1 = {"properties": [{"id": "old"}]}
        results2 = {"properties": [{"id": "new"}]}

        cache.set("test_provider", "search", params, results1)
        cache.set("test_provider", "search", params, results2)

        retrieved = cache.get("test_provider", "search", params)

        assert retrieved["properties"][0]["id"] == "new"

        # Verify only one entry exists
        cache_key = cache._make_cache_key("test_provider", "search", params)
        count = test_session.query(SearchCacheDB).filter_by(cache_key=cache_key).count()
        assert count == 1


class TestCacheExpiration:
    """Tests for cache TTL and expiration."""

    def test_expired_cache_returns_none(self, test_session):
        """Test that expired cache entries return None."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        results = {"properties": []}

        # Create an already-expired entry
        cache_key = cache._make_cache_key("test_provider", "search", params)
        expired_entry = SearchCacheDB(
            cache_key=cache_key,
            provider="test_provider",
            endpoint="search",
            results=results,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        )
        test_session.add(expired_entry)
        test_session.commit()

        # Should return None and delete the expired entry
        retrieved = cache.get("test_provider", "search", params)

        assert retrieved is None

        # Verify entry was deleted
        entry = test_session.query(SearchCacheDB).filter_by(cache_key=cache_key).first()
        assert entry is None

    def test_cleanup_expired_entries(self, test_session):
        """Test cleanup of expired entries."""
        cache = CacheManager(test_session)

        # Create some expired entries
        for i in range(5):
            entry = SearchCacheDB(
                cache_key=f"expired_{i}",
                provider="test",
                endpoint="search",
                results={},
                expires_at=datetime.utcnow() - timedelta(hours=1),
            )
            test_session.add(entry)

        # Create some valid entries
        for i in range(3):
            entry = SearchCacheDB(
                cache_key=f"valid_{i}",
                provider="test",
                endpoint="search",
                results={},
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )
            test_session.add(entry)

        test_session.commit()

        # Run cleanup
        deleted_count = cache.cleanup_expired()

        assert deleted_count == 5

        # Verify valid entries still exist
        valid_count = test_session.query(SearchCacheDB).filter(
            SearchCacheDB.cache_key.like("valid_%")
        ).count()
        assert valid_count == 3


class TestCacheInvalidation:
    """Tests for cache invalidation."""

    def test_invalidate_by_provider(self, test_session):
        """Test invalidating all entries for a provider."""
        cache = CacheManager(test_session)

        # Create entries for different providers
        cache.set("provider1", "search", {"city": "Phoenix"}, {"data": 1})
        cache.set("provider1", "detail", {"id": "123"}, {"data": 2})
        cache.set("provider2", "search", {"city": "Tampa"}, {"data": 3})

        # Invalidate provider1
        deleted = cache.invalidate(provider="provider1")

        assert deleted == 2

        # provider2 should still exist
        result = cache.get("provider2", "search", {"city": "Tampa"})
        assert result is not None

    def test_invalidate_by_endpoint(self, test_session):
        """Test invalidating all entries for an endpoint."""
        cache = CacheManager(test_session)

        # Create entries for different endpoints
        cache.set("provider1", "search", {"city": "Phoenix"}, {"data": 1})
        cache.set("provider2", "search", {"city": "Tampa"}, {"data": 2})
        cache.set("provider1", "detail", {"id": "123"}, {"data": 3})

        # Invalidate all search entries
        deleted = cache.invalidate(endpoint="search")

        assert deleted == 2

        # detail should still exist
        result = cache.get("provider1", "detail", {"id": "123"})
        assert result is not None

    def test_invalidate_all(self, test_session):
        """Test invalidating all cache entries."""
        cache = CacheManager(test_session)

        # Create some entries
        cache.set("provider1", "search", {"city": "Phoenix"}, {"data": 1})
        cache.set("provider2", "detail", {"id": "123"}, {"data": 2})

        # Invalidate all
        deleted = cache.invalidate()

        assert deleted == 2
        assert test_session.query(SearchCacheDB).count() == 0


class TestIncomeCacheOperations:
    """Tests for income-specific cache operations."""

    def test_set_and_get_income_cache(self, test_session):
        """Test income cache set and get."""
        cache = CacheManager(test_session)

        zip_code = "85001"
        median_income = 65000
        income_tier = "middle"
        data = {"percentiles": {"25": 45000, "75": 95000}}

        cache.set_income(zip_code, median_income, income_tier, data)
        retrieved = cache.get_income(zip_code)

        assert retrieved is not None
        assert retrieved["zip_code"] == zip_code
        assert retrieved["median_income"] == median_income
        assert retrieved["income_tier"] == income_tier
        assert retrieved["percentiles"]["25"] == 45000

    def test_get_nonexistent_income(self, test_session):
        """Test getting non-existent income data."""
        cache = CacheManager(test_session)

        result = cache.get_income("00000")

        assert result is None

    def test_income_cache_upsert(self, test_session):
        """Test that setting income cache with same zip updates entry."""
        cache = CacheManager(test_session)

        zip_code = "85001"

        cache.set_income(zip_code, 50000, "middle", {"year": 2022})
        cache.set_income(zip_code, 55000, "upper_middle", {"year": 2023})

        retrieved = cache.get_income(zip_code)

        assert retrieved["median_income"] == 55000
        assert retrieved["income_tier"] == "upper_middle"
        assert retrieved["year"] == 2023

        # Verify only one entry exists
        count = test_session.query(IncomeCacheDB).filter_by(zip_code=zip_code).count()
        assert count == 1


class TestApiCallLogging:
    """Tests for API call logging functionality."""

    def test_log_api_call(self, test_session):
        """Test logging an API call."""
        cache = CacheManager(test_session)

        cache.log_api_call(
            provider="test_provider",
            endpoint="search",
            params={"city": "Phoenix"},
            success=True,
            response_code=200
        )

        log = test_session.query(ApiCallLogDB).first()

        assert log is not None
        assert log.provider == "test_provider"
        assert log.endpoint == "search"
        assert log.success is True
        assert log.cache_hit is False  # Logged via public method = cache miss

    def test_log_api_call_failure(self, test_session):
        """Test logging a failed API call."""
        cache = CacheManager(test_session)

        cache.log_api_call(
            provider="test_provider",
            endpoint="search",
            params={"city": "Phoenix"},
            success=False,
            response_code=500,
            error_message="Internal Server Error"
        )

        log = test_session.query(ApiCallLogDB).first()

        assert log.success is False
        assert log.response_code == 500
        assert log.error_message == "Internal Server Error"

    def test_cache_hit_logged_on_get(self, test_session):
        """Test that cache hits are logged when getting cached data."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        results = {"properties": []}

        cache.set("test_provider", "search", params, results)

        # Clear any existing logs
        test_session.query(ApiCallLogDB).delete()
        test_session.commit()

        # Get cached data - should log a cache hit
        cache.get("test_provider", "search", params)

        log = test_session.query(ApiCallLogDB).first()

        assert log is not None
        assert log.cache_hit is True


class TestCacheStats:
    """Tests for cache statistics."""

    def test_get_stats_empty_cache(self, test_session):
        """Test stats on empty cache."""
        cache = CacheManager(test_session)

        stats = cache.get_stats()

        assert stats["total_cache_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["income_cache_entries"] == 0
        assert stats["api_calls_24h"] == 0

    def test_get_stats_with_entries(self, test_session):
        """Test stats with cache entries."""
        cache = CacheManager(test_session)

        # Create some valid entries
        cache.set("provider1", "search", {"city": "Phoenix"}, {"data": 1})
        cache.set("provider2", "search", {"city": "Tampa"}, {"data": 2})

        # Create an expired entry
        expired_entry = SearchCacheDB(
            cache_key="expired_test",
            provider="test",
            endpoint="search",
            results={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        test_session.add(expired_entry)

        # Create income cache entry
        cache.set_income("85001", 65000, "middle", {})

        test_session.commit()

        stats = cache.get_stats()

        assert stats["total_cache_entries"] == 3
        assert stats["expired_entries"] == 1
        assert stats["valid_entries"] == 2
        assert stats["income_cache_entries"] == 1

    def test_get_stats_hit_rate(self, test_session):
        """Test hit rate calculation in stats."""
        cache = CacheManager(test_session)

        params = {"city": "Phoenix"}
        results = {"data": "test"}

        cache.set("provider", "search", params, results)

        # Generate some hits and misses
        cache.get("provider", "search", params)  # Hit
        cache.get("provider", "search", params)  # Hit
        cache.log_api_call("provider", "search", {"city": "Tampa"}, success=True)  # Miss

        stats = cache.get_stats()

        assert stats["api_calls_24h"] == 3
        assert stats["cache_hits_24h"] == 2
        assert stats["cache_misses_24h"] == 1
        assert stats["hit_rate_24h"] == pytest.approx(2/3)


class TestCacheTTLConfiguration:
    """Tests for cache TTL configuration."""

    def test_default_ttl_values(self):
        """Test that default TTL values are set correctly."""
        assert CACHE_TTL["search"] == 1
        assert CACHE_TTL["property_detail"] == 24
        assert CACHE_TTL["market_data"] == 168
        assert CACHE_TTL["income"] == 8760
        assert CACHE_TTL["walkscore"] == 720
        assert CACHE_TTL["flood"] == 8760

    def test_unknown_endpoint_uses_default_ttl(self, test_session):
        """Test that unknown endpoints use 1 hour default TTL."""
        cache = CacheManager(test_session)

        params = {"data": "test"}
        cache.set("provider", "unknown_endpoint", params, {"result": "test"})

        cache_key = cache._make_cache_key("provider", "unknown_endpoint", params)
        entry = test_session.query(SearchCacheDB).filter_by(cache_key=cache_key).first()

        actual_ttl = (entry.expires_at - entry.created_at).total_seconds() / 3600

        assert abs(actual_ttl - 1) < 0.01  # 1 hour default
