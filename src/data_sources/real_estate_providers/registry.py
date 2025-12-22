"""
Provider registry for managing real estate API providers.

Allows switching between providers via environment config.
"""

import os
from typing import Optional

from .base import RealEstateProvider
from .us_real_estate_listings import USRealEstateListingsProvider


# Registry of available providers
PROVIDERS: dict[str, type[RealEstateProvider]] = {
    "us_real_estate_listings": USRealEstateListingsProvider,
}

# Default provider if not specified
DEFAULT_PROVIDER = "us_real_estate_listings"


def get_provider(name: Optional[str] = None) -> RealEstateProvider:
    """
    Get a real estate provider instance.

    Args:
        name: Provider name. If None, uses REAL_ESTATE_PROVIDER env var
              or falls back to DEFAULT_PROVIDER.

    Returns:
        Configured provider instance

    Raises:
        ValueError: If provider name is not registered

    Example:
        # Use default (from env or config)
        provider = get_provider()

        # Use specific provider
        provider = get_provider("us_real_estate_listings")
    """
    if name is None:
        name = os.environ.get("REAL_ESTATE_PROVIDER", DEFAULT_PROVIDER)

    if name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")

    provider_class = PROVIDERS[name]
    return provider_class()


def list_providers() -> list[dict]:
    """
    List all registered providers with their status.

    Returns:
        List of dicts with provider info
    """
    result = []
    for name, provider_class in PROVIDERS.items():
        try:
            instance = provider_class()
            result.append({
                "name": name,
                "display_name": instance.display_name,
                "configured": instance.is_configured,
                "is_default": name == DEFAULT_PROVIDER,
            })
        except Exception as e:
            result.append({
                "name": name,
                "display_name": name,
                "configured": False,
                "error": str(e),
            })
    return result


def register_provider(name: str, provider_class: type[RealEstateProvider]) -> None:
    """
    Register a new provider.

    Args:
        name: Unique provider name
        provider_class: Provider class implementing RealEstateProvider protocol
    """
    PROVIDERS[name] = provider_class
