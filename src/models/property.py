"""Property data model."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PropertyType(str, Enum):
    """Types of residential properties."""

    SFH = "single_family_home"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    DUPLEX = "duplex"
    TRIPLEX = "triplex"
    FOURPLEX = "fourplex"
    MULTI_FAMILY = "multi_family"
    # Types we track but typically filter out
    MOBILE_HOME = "mobile_home"
    MANUFACTURED = "manufactured"
    LAND = "land"
    OTHER = "other"


# Property types suitable for traditional rental investing
INVESTABLE_PROPERTY_TYPES = {
    PropertyType.SFH,
    PropertyType.CONDO,
    PropertyType.TOWNHOUSE,
    PropertyType.DUPLEX,
    PropertyType.TRIPLEX,
    PropertyType.FOURPLEX,
    PropertyType.MULTI_FAMILY,
}


class PropertyStatus(str, Enum):
    """Property listing status."""

    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    OFF_MARKET = "off_market"
    FORECLOSURE = "foreclosure"
    AUCTION = "auction"


class Property(BaseModel):
    """Core property data model."""

    id: str = Field(..., description="Unique property identifier")
    address: str = Field(..., description="Full street address")
    city: str = Field(..., description="City name")
    state: str = Field(..., max_length=2, description="State abbreviation")
    zip_code: str = Field(..., description="ZIP code")
    county: Optional[str] = Field(None, description="County name")

    # Location
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    # Pricing
    list_price: float = Field(..., gt=0, description="Current listing price")
    original_price: Optional[float] = Field(None, description="Original list price")
    price_per_sqft: Optional[float] = Field(None, description="Price per square foot")

    # Rental estimates
    estimated_rent: Optional[float] = Field(None, description="Estimated monthly rent")
    rent_zestimate: Optional[float] = Field(None, description="Zillow rent estimate")

    # Property details
    property_type: PropertyType = Field(default=PropertyType.SFH)
    bedrooms: int = Field(..., ge=0)
    bathrooms: float = Field(..., ge=0)
    sqft: Optional[int] = Field(None, gt=0, description="Living area in sqft")
    lot_size_sqft: Optional[int] = Field(None, description="Lot size in sqft")
    year_built: Optional[int] = Field(None, ge=1800, le=2030)
    stories: Optional[int] = Field(None, ge=1)
    parking_spaces: Optional[int] = Field(None, ge=0)
    units: int = Field(default=1, ge=1, description="Number of units")

    # Listing info
    status: PropertyStatus = Field(default=PropertyStatus.ACTIVE)
    days_on_market: int = Field(default=0, ge=0)
    source: str = Field(..., description="Data source (zillow, redfin, etc.)")
    source_url: Optional[str] = Field(None, description="URL to listing")
    mls_id: Optional[str] = Field(None, description="MLS listing ID")

    # Taxes and fees
    annual_taxes: Optional[float] = Field(None, ge=0)
    hoa_fee: Optional[float] = Field(None, ge=0, description="Monthly HOA fee")

    # Metadata
    description: Optional[str] = Field(None, description="Listing description")
    features: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list, description="Image URLs")

    # Timestamps
    listed_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def full_address(self) -> str:
        """Return full formatted address."""
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"

    @property
    def price_reduction_pct(self) -> Optional[float]:
        """Calculate price reduction percentage from original price."""
        if self.original_price and self.original_price > 0:
            return ((self.original_price - self.list_price) / self.original_price) * 100
        return None

    @property
    def gross_rent_multiplier(self) -> Optional[float]:
        """Calculate GRM if rent estimate available."""
        if self.estimated_rent and self.estimated_rent > 0:
            return self.list_price / (self.estimated_rent * 12)
        return None

    def model_post_init(self, __context) -> None:
        """Calculate derived fields after initialization."""
        if self.sqft and self.sqft > 0 and not self.price_per_sqft:
            self.price_per_sqft = self.list_price / self.sqft
