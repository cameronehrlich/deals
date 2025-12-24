"""
Base protocol and data classes for real estate providers.

All providers must implement the RealEstateProvider protocol.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable


@dataclass
class PropertyListing:
    """Standardized property listing across all providers."""
    property_id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: Optional[int] = None
    property_type: str = "single_family"
    year_built: Optional[int] = None
    lot_sqft: Optional[int] = None
    days_on_market: Optional[int] = None
    photos: list[str] = field(default_factory=list)
    primary_photo: Optional[str] = None
    source_url: Optional[str] = None
    hoa_fee: Optional[float] = None
    price_per_sqft: Optional[float] = None

    # Location coordinates
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Provider metadata
    provider: str = ""
    raw_data: Optional[dict] = None


@dataclass
class PropertyDetail(PropertyListing):
    """Extended property details."""
    description: Optional[str] = None
    features: list[str] = field(default_factory=list)
    price_history: list[dict] = field(default_factory=list)
    tax_history: list[dict] = field(default_factory=list)
    schools: list[dict] = field(default_factory=list)
    last_sold_date: Optional[str] = None
    last_sold_price: Optional[float] = None
    annual_tax: Optional[float] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    broker_name: Optional[str] = None


@dataclass
class ProviderUsage:
    """API usage tracking for a provider."""
    provider_name: str
    requests_used: int
    requests_limit: int
    period: str  # "monthly", "daily", etc.

    @property
    def requests_remaining(self) -> int:
        return max(0, self.requests_limit - self.requests_used)

    @property
    def percent_used(self) -> float:
        if self.requests_limit <= 0:
            return 0
        return (self.requests_used / self.requests_limit) * 100

    @property
    def warning(self) -> Optional[str]:
        if self.percent_used >= 100:
            return "limit_reached"
        elif self.percent_used >= 80:
            return "approaching_limit"
        return None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider_name,
            "requests_used": self.requests_used,
            "requests_limit": self.requests_limit,
            "requests_remaining": self.requests_remaining,
            "percent_used": round(self.percent_used, 1),
            "warning": self.warning,
            "period": self.period,
        }


@runtime_checkable
class RealEstateProvider(Protocol):
    """
    Protocol defining the interface for real estate data providers.

    All providers must implement these methods to be compatible
    with the platform's property search and analysis features.
    """

    # Provider metadata
    name: str
    display_name: str

    @property
    def is_configured(self) -> bool:
        """Check if the provider has valid API credentials."""
        ...

    async def search_properties(
        self,
        location: str,
        max_price: Optional[int] = None,
        min_price: Optional[int] = None,
        min_beds: Optional[int] = None,
        min_baths: Optional[int] = None,
        property_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[PropertyListing]:
        """
        Search for properties in a location.

        Args:
            location: City, State (e.g., "Miami, FL") or zip code
            max_price: Maximum listing price
            min_price: Minimum listing price
            min_beds: Minimum bedrooms
            min_baths: Minimum bathrooms
            property_type: Filter by type (single_family, condo, etc.)
            limit: Maximum results to return

        Returns:
            List of PropertyListing objects
        """
        ...

    async def get_property_detail(
        self,
        property_id: str,
    ) -> Optional[PropertyDetail]:
        """
        Get detailed information for a specific property.

        Args:
            property_id: Provider-specific property ID

        Returns:
            PropertyDetail object or None if not found
        """
        ...

    def get_usage(self) -> ProviderUsage:
        """Get current API usage statistics."""
        ...

    async def close(self) -> None:
        """Clean up resources (close HTTP clients, etc.)."""
        ...


class BaseProvider(ABC):
    """
    Abstract base class for real estate providers.

    Provides common functionality like usage tracking and caching.
    Subclasses must implement the abstract methods.
    """

    name: str = "base"
    display_name: str = "Base Provider"

    def __init__(self):
        self._usage_count = 0

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        pass

    @abstractmethod
    async def search_properties(
        self,
        location: str,
        max_price: Optional[int] = None,
        min_price: Optional[int] = None,
        min_beds: Optional[int] = None,
        min_baths: Optional[int] = None,
        property_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[PropertyListing]:
        pass

    @abstractmethod
    async def get_property_detail(
        self,
        property_id: str,
    ) -> Optional[PropertyDetail]:
        pass

    @abstractmethod
    def get_usage(self) -> ProviderUsage:
        pass

    async def close(self) -> None:
        """Default implementation - override if needed."""
        pass
