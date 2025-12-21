"""Repository pattern for deal storage."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.models.deal import Deal, DealPipeline
from src.models.property import Property
from src.models.market import Market


class DealRepository(ABC):
    """Abstract repository for deal storage."""

    @abstractmethod
    async def save_deal(self, deal: Deal) -> Deal:
        """Save or update a deal."""
        pass

    @abstractmethod
    async def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get a deal by ID."""
        pass

    @abstractmethod
    async def get_deals(
        self,
        status: Optional[DealPipeline] = None,
        market_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Deal]:
        """Get deals with optional filters."""
        pass

    @abstractmethod
    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal."""
        pass

    @abstractmethod
    async def save_property(self, property: Property) -> Property:
        """Save or update a property."""
        pass

    @abstractmethod
    async def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by ID."""
        pass

    @abstractmethod
    async def save_market(self, market: Market) -> Market:
        """Save or update market data."""
        pass

    @abstractmethod
    async def get_market(self, market_id: str) -> Optional[Market]:
        """Get market by ID."""
        pass

    @abstractmethod
    async def get_all_markets(self) -> list[Market]:
        """Get all markets."""
        pass


class InMemoryRepository(DealRepository):
    """In-memory repository for development and testing."""

    def __init__(self):
        self._deals: dict[str, Deal] = {}
        self._properties: dict[str, Property] = {}
        self._markets: dict[str, Market] = {}

    async def save_deal(self, deal: Deal) -> Deal:
        """Save or update a deal."""
        deal.status_updated = datetime.utcnow()
        self._deals[deal.id] = deal
        # Also save the property
        await self.save_property(deal.property)
        return deal

    async def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get a deal by ID."""
        return self._deals.get(deal_id)

    async def get_deals(
        self,
        status: Optional[DealPipeline] = None,
        market_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Deal]:
        """Get deals with optional filters."""
        deals = list(self._deals.values())

        # Apply filters
        if status:
            deals = [d for d in deals if d.pipeline_status == status]

        if market_id:
            deals = [d for d in deals if d.market and d.market.id == market_id]

        # Sort by score (descending) then by first seen (descending)
        deals.sort(
            key=lambda d: (
                d.score.overall_score if d.score else 0,
                d.first_seen.timestamp() if d.first_seen else 0,
            ),
            reverse=True,
        )

        # Apply pagination
        return deals[offset : offset + limit]

    async def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal."""
        if deal_id in self._deals:
            del self._deals[deal_id]
            return True
        return False

    async def save_property(self, property: Property) -> Property:
        """Save or update a property."""
        property.last_updated = datetime.utcnow()
        self._properties[property.id] = property
        return property

    async def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by ID."""
        return self._properties.get(property_id)

    async def save_market(self, market: Market) -> Market:
        """Save or update market data."""
        market.last_updated = datetime.utcnow()
        self._markets[market.id] = market
        return market

    async def get_market(self, market_id: str) -> Optional[Market]:
        """Get market by ID."""
        return self._markets.get(market_id)

    async def get_all_markets(self) -> list[Market]:
        """Get all markets."""
        return list(self._markets.values())

    async def get_stats(self) -> dict:
        """Get repository statistics."""
        status_counts = {}
        for deal in self._deals.values():
            status = deal.pipeline_status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_deals": len(self._deals),
            "total_properties": len(self._properties),
            "total_markets": len(self._markets),
            "deals_by_status": status_counts,
        }

    def clear(self) -> None:
        """Clear all data."""
        self._deals.clear()
        self._properties.clear()
        self._markets.clear()
