"""
Data source integrations for real market and property data.

Modules:
- redfin: Redfin Data Center CSV parsing
- fred: Federal Reserve Economic Data API
- hud_fmr: HUD Fair Market Rents
- rentcast: RentCast API for rent estimates
- url_parser: Extract property data from Zillow/Redfin URLs
- us_real_estate: US Real Estate API via RapidAPI (live listings)
- walkscore: Walk Score API (walkability, transit, bike scores)
- fema_flood: FEMA NFHL API (flood zone data)
- aggregator: Combine multiple data sources
"""

from src.data_sources.redfin import RedfinDataCenter
from src.data_sources.fred import FredClient
from src.data_sources.hud_fmr import HudFmrLoader
from src.data_sources.rentcast import RentCastClient
from src.data_sources.url_parser import PropertyUrlParser
from src.data_sources.us_real_estate import USRealEstateClient
from src.data_sources.walkscore import WalkScoreClient, WalkScoreResult
from src.data_sources.fema_flood import FEMAFloodClient, FloodZoneResult
from src.data_sources.aggregator import DataAggregator

__all__ = [
    "RedfinDataCenter",
    "FredClient",
    "HudFmrLoader",
    "RentCastClient",
    "PropertyUrlParser",
    "USRealEstateClient",
    "WalkScoreClient",
    "WalkScoreResult",
    "FEMAFloodClient",
    "FloodZoneResult",
    "DataAggregator",
]
