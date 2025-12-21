"""Mock scraper with sample data for development and testing."""

import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

from src.models.property import Property, PropertyStatus, PropertyType
from src.scrapers.base import BaseScraper, ScraperResult


# Sample data for realistic property generation
STREET_NAMES = [
    "Oak", "Maple", "Cedar", "Pine", "Elm", "Main", "First", "Second",
    "Park", "Lake", "River", "Hill", "Valley", "Meadow", "Forest", "Spring",
]

STREET_TYPES = ["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Ct", "Pl", "Rd"]

MARKETS = {
    "austin_tx": {
        "city": "Austin",
        "state": "TX",
        "zip_codes": ["78701", "78702", "78703", "78704", "78745", "78748", "78759"],
        "price_range": (250000, 800000),
        "rent_range": (1500, 3500),
        "sqft_range": (1200, 3000),
    },
    "indianapolis_in": {
        "city": "Indianapolis",
        "state": "IN",
        "zip_codes": ["46201", "46202", "46203", "46205", "46220", "46226", "46250"],
        "price_range": (120000, 350000),
        "rent_range": (900, 1800),
        "sqft_range": (1000, 2500),
    },
    "cleveland_oh": {
        "city": "Cleveland",
        "state": "OH",
        "zip_codes": ["44102", "44103", "44104", "44106", "44108", "44109", "44111"],
        "price_range": (80000, 250000),
        "rent_range": (700, 1500),
        "sqft_range": (900, 2200),
    },
    "memphis_tn": {
        "city": "Memphis",
        "state": "TN",
        "zip_codes": ["38103", "38104", "38107", "38108", "38111", "38117", "38120"],
        "price_range": (100000, 300000),
        "rent_range": (800, 1600),
        "sqft_range": (1000, 2400),
    },
    "birmingham_al": {
        "city": "Birmingham",
        "state": "AL",
        "zip_codes": ["35203", "35204", "35205", "35206", "35209", "35213", "35222"],
        "price_range": (90000, 280000),
        "rent_range": (750, 1500),
        "sqft_range": (950, 2300),
    },
    "kansas_city_mo": {
        "city": "Kansas City",
        "state": "MO",
        "zip_codes": ["64101", "64102", "64108", "64109", "64110", "64111", "64112"],
        "price_range": (130000, 380000),
        "rent_range": (950, 1900),
        "sqft_range": (1050, 2600),
    },
    "tampa_fl": {
        "city": "Tampa",
        "state": "FL",
        "zip_codes": ["33602", "33603", "33604", "33606", "33609", "33611", "33629"],
        "price_range": (280000, 650000),
        "rent_range": (1600, 3200),
        "sqft_range": (1300, 2800),
    },
    "phoenix_az": {
        "city": "Phoenix",
        "state": "AZ",
        "zip_codes": ["85003", "85004", "85006", "85008", "85012", "85014", "85016"],
        "price_range": (300000, 600000),
        "rent_range": (1400, 2800),
        "sqft_range": (1200, 2700),
    },
}


class MockScraper(BaseScraper):
    """Mock scraper that generates realistic sample properties."""

    source_name = "mock"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self._generated: dict[str, Property] = {}

    def _generate_property(self, market_key: str) -> Property:
        """Generate a realistic mock property."""
        market = MARKETS.get(market_key, MARKETS["indianapolis_in"])

        # Generate address
        street_num = random.randint(100, 9999)
        street = f"{random.choice(STREET_NAMES)} {random.choice(STREET_TYPES)}"
        address = f"{street_num} {street}"

        # Property details
        beds = random.choices([2, 3, 4, 5], weights=[15, 45, 30, 10])[0]
        baths = random.choices([1, 1.5, 2, 2.5, 3], weights=[10, 20, 40, 20, 10])[0]

        min_price, max_price = market["price_range"]
        list_price = round(random.uniform(min_price, max_price), -3)

        min_sqft, max_sqft = market["sqft_range"]
        sqft = random.randint(min_sqft, max_sqft)

        min_rent, max_rent = market["rent_range"]
        # Correlate rent with price somewhat
        price_pct = (list_price - min_price) / (max_price - min_price)
        base_rent = min_rent + (max_rent - min_rent) * price_pct
        estimated_rent = round(base_rent * random.uniform(0.9, 1.1), -1)

        # Property type
        prop_type = random.choices(
            [PropertyType.SFH, PropertyType.DUPLEX, PropertyType.TOWNHOUSE, PropertyType.CONDO],
            weights=[60, 15, 15, 10],
        )[0]

        units = 2 if prop_type == PropertyType.DUPLEX else 1

        # Year built
        year_built = random.choices(
            [random.randint(1920, 1960), random.randint(1960, 1990), random.randint(1990, 2010), random.randint(2010, 2024)],
            weights=[15, 35, 35, 15],
        )[0]

        # Days on market (biased toward recent)
        dom = random.choices(
            [random.randint(1, 14), random.randint(15, 45), random.randint(46, 90), random.randint(91, 180)],
            weights=[30, 40, 20, 10],
        )[0]

        # Status
        status = random.choices(
            [PropertyStatus.ACTIVE, PropertyStatus.PENDING],
            weights=[85, 15],
        )[0]

        # Price reduction?
        original_price = None
        if random.random() < 0.3:
            reduction = random.uniform(0.03, 0.15)
            original_price = round(list_price / (1 - reduction), -3)

        # Taxes and HOA
        tax_rate = random.uniform(0.008, 0.025)
        annual_taxes = round(list_price * tax_rate, 0)

        hoa_fee = 0.0
        if prop_type in [PropertyType.CONDO, PropertyType.TOWNHOUSE]:
            hoa_fee = random.choice([150, 200, 250, 300, 350, 400])

        # Generate ID
        prop_id = f"mock_{uuid.uuid4().hex[:12]}"

        property = Property(
            id=prop_id,
            address=address,
            city=market["city"],
            state=market["state"],
            zip_code=random.choice(market["zip_codes"]),
            latitude=round(random.uniform(29.0, 42.0), 6),
            longitude=round(random.uniform(-123.0, -80.0), 6),
            list_price=list_price,
            original_price=original_price,
            estimated_rent=estimated_rent,
            property_type=prop_type,
            bedrooms=beds,
            bathrooms=baths,
            sqft=sqft,
            lot_size_sqft=random.randint(3000, 15000) if prop_type == PropertyType.SFH else None,
            year_built=year_built,
            stories=random.choice([1, 2]),
            units=units,
            status=status,
            days_on_market=dom,
            source=self.source_name,
            source_url=f"https://example.com/property/{prop_id}",
            annual_taxes=annual_taxes,
            hoa_fee=hoa_fee if hoa_fee > 0 else None,
            listed_date=datetime.utcnow() - timedelta(days=dom),
            features=self._generate_features(year_built, prop_type),
        )

        self._generated[prop_id] = property
        return property

    def _generate_features(self, year_built: int, prop_type: PropertyType) -> list[str]:
        """Generate random property features."""
        all_features = [
            "Central AC", "Forced Air Heating", "Hardwood Floors",
            "Updated Kitchen", "Stainless Appliances", "Granite Counters",
            "Open Floor Plan", "Fenced Yard", "Garage", "Basement",
            "Fireplace", "Patio", "Deck", "New Roof", "New Windows",
            "Smart Thermostat", "Washer/Dryer", "Storage",
        ]

        if year_built > 2000:
            all_features.extend(["Energy Efficient", "Modern Finishes"])
        if prop_type == PropertyType.SFH:
            all_features.extend(["Large Lot", "Mature Trees"])

        num_features = random.randint(3, 8)
        return random.sample(all_features, min(num_features, len(all_features)))

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
        """Generate mock properties matching search criteria."""
        # Find matching market
        market_key = f"{city.lower().replace(' ', '_')}_{state.lower()}"
        if market_key not in MARKETS:
            # Default to a generic market
            market_key = "indianapolis_in"

        # Generate properties
        properties = []
        for _ in range(limit):
            prop = self._generate_property(market_key)

            # Apply filters
            if min_price and prop.list_price < min_price:
                continue
            if max_price and prop.list_price > max_price:
                continue
            if min_beds and prop.bedrooms < min_beds:
                continue
            if max_beds and prop.bedrooms > max_beds:
                continue

            properties.append(prop)

            if len(properties) >= limit:
                break

        return ScraperResult(
            properties=properties,
            total_found=len(properties),
            source=self.source_name,
            query={
                "city": city,
                "state": state,
                "min_price": min_price,
                "max_price": max_price,
            },
            timestamp=datetime.utcnow(),
            errors=[],
        )

    async def get_property(self, property_id: str) -> Optional[Property]:
        """Get a previously generated property."""
        return self._generated.get(property_id)

    async def get_rental_estimate(self, property: Property) -> Optional[float]:
        """Return the existing rental estimate with slight variation."""
        if property.estimated_rent:
            # Add some variance
            return round(property.estimated_rent * random.uniform(0.95, 1.05), -1)
        return None
