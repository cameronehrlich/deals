"""Database layer."""

from src.db.repository import DealRepository, InMemoryRepository
from src.db.models import (
    MarketDB, SavedPropertyDB, SearchCacheDB, IncomeCacheDB,
    get_engine, get_session, init_database, DEFAULT_FAVORITE_MARKETS
)
from src.db.cache import CacheManager, CACHE_TTL
from src.db.sqlite_repository import SQLiteRepository, get_repository

__all__ = [
    # Repository pattern
    "DealRepository",
    "InMemoryRepository",
    "SQLiteRepository",
    "get_repository",
    # ORM models
    "MarketDB",
    "SavedPropertyDB",
    "SearchCacheDB",
    "IncomeCacheDB",
    # Cache
    "CacheManager",
    "CACHE_TTL",
    # Database utilities
    "get_engine",
    "get_session",
    "init_database",
    "DEFAULT_FAVORITE_MARKETS",
]
