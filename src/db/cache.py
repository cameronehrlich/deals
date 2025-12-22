"""Cache manager for API responses."""

from datetime import datetime, timedelta
from typing import Optional, Any
import hashlib
import json

from sqlalchemy.orm import Session

from src.db.models import SearchCacheDB, IncomeCacheDB, ApiCallLogDB


# Cache TTLs (in hours)
CACHE_TTL = {
    "search": 1,           # Property search results - 1 hour
    "property_detail": 24, # Individual property details - 24 hours
    "market_data": 168,    # Market metrics - 1 week (168 hours)
    "income": 8760,        # Income data - 1 year (census data)
    "macro": 1,            # Macro rates - 1 hour
    "rent_estimate": 24,   # Rent estimates - 24 hours
}


class CacheManager:
    """Manages API response caching to minimize API calls."""

    def __init__(self, session: Session):
        self.session = session

    def _make_cache_key(self, provider: str, endpoint: str, params: dict) -> str:
        """Create a unique cache key from provider, endpoint, and params."""
        # Sort params for consistent hashing
        param_str = json.dumps(params, sort_keys=True, default=str)
        key_input = f"{provider}:{endpoint}:{param_str}"
        return hashlib.sha256(key_input.encode()).hexdigest()

    def get(
        self,
        provider: str,
        endpoint: str,
        params: dict
    ) -> Optional[dict]:
        """
        Get cached results if still valid.

        Args:
            provider: API provider name (e.g., "us_real_estate_listings")
            endpoint: Endpoint name (e.g., "search", "detail")
            params: Request parameters

        Returns:
            Cached results dict or None if not found/expired
        """
        cache_key = self._make_cache_key(provider, endpoint, params)

        cache_entry = (
            self.session.query(SearchCacheDB)
            .filter_by(cache_key=cache_key)
            .first()
        )

        if cache_entry and not cache_entry.is_expired():
            # Log cache hit
            self._log_api_call(
                provider=provider,
                endpoint=endpoint,
                params=params,
                cache_key=cache_key,
                cache_hit=True,
                success=True
            )
            return cache_entry.results

        # Clean up expired entry
        if cache_entry:
            self.session.delete(cache_entry)
            self.session.commit()

        return None

    def set(
        self,
        provider: str,
        endpoint: str,
        params: dict,
        results: dict,
        ttl_hours: Optional[int] = None
    ) -> None:
        """
        Cache API results.

        Args:
            provider: API provider name
            endpoint: Endpoint name
            params: Request parameters
            results: Response data to cache
            ttl_hours: Time to live in hours (uses default for endpoint type if not specified)
        """
        if ttl_hours is None:
            # Use endpoint-specific TTL or default to 1 hour
            ttl_hours = CACHE_TTL.get(endpoint, 1)

        cache_key = self._make_cache_key(provider, endpoint, params)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Upsert cache entry
        cache_entry = (
            self.session.query(SearchCacheDB)
            .filter_by(cache_key=cache_key)
            .first()
        )

        if cache_entry:
            cache_entry.results = results
            cache_entry.expires_at = expires_at
            cache_entry.created_at = datetime.utcnow()
        else:
            cache_entry = SearchCacheDB(
                cache_key=cache_key,
                provider=provider,
                endpoint=endpoint,
                results=results,
                expires_at=expires_at,
            )
            self.session.add(cache_entry)

        self.session.commit()

    def get_income(self, zip_code: str) -> Optional[dict]:
        """
        Get cached income data for a zip code.
        Income data is cached indefinitely (census data rarely changes).
        """
        cache_entry = (
            self.session.query(IncomeCacheDB)
            .filter_by(zip_code=zip_code)
            .first()
        )

        if cache_entry:
            return {
                "zip_code": cache_entry.zip_code,
                "median_income": cache_entry.median_income,
                "income_tier": cache_entry.income_tier,
                **cache_entry.data
            }
        return None

    def set_income(
        self,
        zip_code: str,
        median_income: int,
        income_tier: str,
        data: dict
    ) -> None:
        """Cache income data for a zip code."""
        cache_entry = (
            self.session.query(IncomeCacheDB)
            .filter_by(zip_code=zip_code)
            .first()
        )

        if cache_entry:
            cache_entry.median_income = median_income
            cache_entry.income_tier = income_tier
            cache_entry.data = data
            cache_entry.fetched_at = datetime.utcnow()
        else:
            cache_entry = IncomeCacheDB(
                zip_code=zip_code,
                median_income=median_income,
                income_tier=income_tier,
                data=data,
            )
            self.session.add(cache_entry)

        self.session.commit()

    def _log_api_call(
        self,
        provider: str,
        endpoint: str,
        params: dict,
        cache_key: str = None,
        cache_hit: bool = False,
        success: bool = True,
        response_code: int = None,
        error_message: str = None
    ) -> None:
        """Log an API call for tracking and debugging."""
        log_entry = ApiCallLogDB(
            provider=provider,
            endpoint=endpoint,
            params=params,
            cache_key=cache_key,
            cache_hit=cache_hit,
            success=success,
            response_code=response_code,
            error_message=error_message,
        )
        self.session.add(log_entry)
        self.session.commit()

    def log_api_call(
        self,
        provider: str,
        endpoint: str,
        params: dict,
        success: bool = True,
        response_code: int = None,
        error_message: str = None
    ) -> None:
        """Public method to log an API call (cache miss)."""
        cache_key = self._make_cache_key(provider, endpoint, params)
        self._log_api_call(
            provider=provider,
            endpoint=endpoint,
            params=params,
            cache_key=cache_key,
            cache_hit=False,
            success=success,
            response_code=response_code,
            error_message=error_message
        )

    def invalidate(
        self,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> int:
        """
        Invalidate cached entries.

        Args:
            provider: Invalidate all entries for this provider
            endpoint: Invalidate all entries for this endpoint

        Returns:
            Number of entries deleted
        """
        query = self.session.query(SearchCacheDB)

        if provider:
            query = query.filter_by(provider=provider)
        if endpoint:
            query = query.filter_by(endpoint=endpoint)

        count = query.delete()
        self.session.commit()
        return count

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries. Returns count deleted."""
        count = (
            self.session.query(SearchCacheDB)
            .filter(SearchCacheDB.expires_at < datetime.utcnow())
            .delete()
        )
        self.session.commit()
        return count

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_entries = self.session.query(SearchCacheDB).count()
        expired_entries = (
            self.session.query(SearchCacheDB)
            .filter(SearchCacheDB.expires_at < datetime.utcnow())
            .count()
        )
        income_entries = self.session.query(IncomeCacheDB).count()

        # API call stats from last 24 hours
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_calls = (
            self.session.query(ApiCallLogDB)
            .filter(ApiCallLogDB.created_at >= yesterday)
            .all()
        )

        cache_hits = sum(1 for c in recent_calls if c.cache_hit)
        cache_misses = sum(1 for c in recent_calls if not c.cache_hit)

        return {
            "total_cache_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "income_cache_entries": income_entries,
            "api_calls_24h": len(recent_calls),
            "cache_hits_24h": cache_hits,
            "cache_misses_24h": cache_misses,
            "hit_rate_24h": cache_hits / len(recent_calls) if recent_calls else 0,
        }
