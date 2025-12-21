"""
Data source integrations for real market and property data.

Modules:
- redfin: Redfin Data Center CSV parsing
- fred: Federal Reserve Economic Data API
- hud_fmr: HUD Fair Market Rents
- rentcast: RentCast API for rent estimates
- url_parser: Extract property data from Zillow/Redfin URLs
- aggregator: Combine multiple data sources
"""

from src.data_sources.redfin import RedfinDataCenter
from src.data_sources.fred import FredClient
from src.data_sources.hud_fmr import HudFmrLoader
from src.data_sources.rentcast import RentCastClient
from src.data_sources.url_parser import PropertyUrlParser
from src.data_sources.aggregator import DataAggregator

__all__ = [
    "RedfinDataCenter",
    "FredClient",
    "HudFmrLoader",
    "RentCastClient",
    "PropertyUrlParser",
    "DataAggregator",
]
