"""Base scraper interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.models.property import Property


@dataclass
class ScraperResult:
    """Result from a scraping operation."""

    properties: list[Property]
    total_found: int
    source: str
    query: dict
    timestamp: datetime
    errors: list[str]
    next_page: Optional[str] = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class BaseScraper(ABC):
    """Abstract base class for property scrapers."""

    source_name: str = "unknown"

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    @abstractmethod
    async def search(
        self,
        city: str,
        state: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_beds: Optional[int] = None,
        max_beds: Optional[int] = None,
        property_types: Optional[list[str]] = None,
        limit: int = 100,
    ) -> ScraperResult:
        """Search for properties matching criteria."""
        pass

    @abstractmethod
    async def get_property(self, property_id: str) -> Optional[Property]:
        """Get details for a specific property."""
        pass

    @abstractmethod
    async def get_rental_estimate(self, property: Property) -> Optional[float]:
        """Get rental estimate for a property."""
        pass
