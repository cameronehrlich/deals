"""
Data source integrations for real market and property data.

Modules:
- redfin: Redfin Data Center CSV parsing (housing market data)
- fred: Federal Reserve Economic Data API (mortgage rates, macro)
- bls: Bureau of Labor Statistics (metro employment, job growth)
- hud_fmr: HUD Fair Market Rents
- census: Census Bureau API (population, demographics, income)
- rentcast: RentCast API for rent estimates
- income_data: Household income by zip code
- url_parser: Extract property data from Zillow/Redfin URLs
- us_real_estate: US Real Estate API via RapidAPI (live listings)
- walkscore: Walk Score API (walkability, transit, bike scores)
- fema_flood: FEMA NFHL API (flood zone data)
- geocoder: Census Geocoder API (address to lat/lon)
- state_data: Static state-level data (landlord friendliness, taxes, risk)
- aggregator: Combine multiple data sources for full market enrichment
"""

from src.data_sources.redfin import RedfinDataCenter
from src.data_sources.fred import FredClient
from src.data_sources.bls import BLSClient, MetroEmploymentData
from src.data_sources.hud_fmr import HudFmrLoader
from src.data_sources.census import CensusClient, MetroPopulationData
from src.data_sources.rentcast import RentCastClient
from src.data_sources.income_data import IncomeDataClient, IncomeData
from src.data_sources.url_parser import PropertyUrlParser
from src.data_sources.us_real_estate import USRealEstateClient
from src.data_sources.walkscore import WalkScoreClient, WalkScoreResult
from src.data_sources.fema_flood import FEMAFloodClient, FloodZoneResult
from src.data_sources.geocoder import CensusGeocoder, get_geocoder, GeocodingResult
from src.data_sources.state_data import get_state_data, StateData, is_landlord_friendly
from src.data_sources.aggregator import DataAggregator, EnrichedMarketData

__all__ = [
    # Housing/Redfin
    "RedfinDataCenter",
    # Macro/FRED
    "FredClient",
    # Employment/BLS
    "BLSClient",
    "MetroEmploymentData",
    # Rent
    "HudFmrLoader",
    "RentCastClient",
    # Demographics/Census
    "CensusClient",
    "MetroPopulationData",
    # Income
    "IncomeDataClient",
    "IncomeData",
    # Property Import
    "PropertyUrlParser",
    "USRealEstateClient",
    # Location
    "WalkScoreClient",
    "WalkScoreResult",
    "FEMAFloodClient",
    "FloodZoneResult",
    # Geocoding
    "CensusGeocoder",
    "get_geocoder",
    "GeocodingResult",
    # State Data
    "get_state_data",
    "StateData",
    "is_landlord_friendly",
    # Aggregator
    "DataAggregator",
    "EnrichedMarketData",
]
