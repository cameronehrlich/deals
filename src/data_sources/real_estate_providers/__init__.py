"""
Real Estate API Provider Abstraction Layer

This module provides a pluggable architecture for real estate data sources.
Add new providers by implementing the RealEstateProvider protocol.

Usage:
    from src.data_sources.real_estate_providers import get_provider

    provider = get_provider()  # Uses configured default
    properties = await provider.search_properties("Miami, FL", max_price=500000)
"""

from .base import RealEstateProvider, PropertyListing, PropertyDetail, ProviderUsage
from .registry import get_provider, list_providers, PROVIDERS

__all__ = [
    "RealEstateProvider",
    "PropertyListing",
    "PropertyDetail",
    "ProviderUsage",
    "get_provider",
    "list_providers",
    "PROVIDERS",
]
