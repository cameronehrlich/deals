"""
Static state-level data for real estate investment analysis.

This module contains embedded data that doesn't change frequently:
- Landlord-friendly state rankings
- Average property tax rates by state
- Insurance risk levels (hurricane, tornado, flood zones)
- State income tax presence

Data sources:
- Landlord friendliness: Based on eviction laws, rent control, security deposit limits
- Property taxes: Tax Foundation, state averages
- Insurance risk: FEMA, NOAA historical data
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StateData:
    """Static data for a US state."""

    state_code: str
    state_name: str

    # Landlord-friendliness (1-10, 10 = most landlord friendly)
    landlord_friendly_score: int
    landlord_friendly: bool  # Score >= 6

    # Tax data
    avg_property_tax_rate: float  # As decimal (0.01 = 1%)
    has_state_income_tax: bool

    # Natural disaster risk
    insurance_risk: str  # "low", "medium", "high"
    risk_factors: list[str]  # ["hurricane", "tornado", "flood", "earthquake", "wildfire"]

    # Notes
    notes: Optional[str] = None


# Landlord-friendly rankings based on:
# - Eviction process speed and ease
# - Rent control restrictions (statewide bans = friendly)
# - Security deposit limits
# - Lease termination requirements
# - Tenant protection laws

STATE_DATA: dict[str, StateData] = {
    # Very Landlord Friendly (8-10)
    "TX": StateData(
        state_code="TX",
        state_name="Texas",
        landlord_friendly_score=9,
        landlord_friendly=True,
        avg_property_tax_rate=0.0180,
        has_state_income_tax=False,
        insurance_risk="medium",
        risk_factors=["hurricane", "tornado", "flood"],
        notes="No rent control, fast evictions, no security deposit limit",
    ),
    "FL": StateData(
        state_code="FL",
        state_name="Florida",
        landlord_friendly_score=8,
        landlord_friendly=True,
        avg_property_tax_rate=0.0089,
        has_state_income_tax=False,
        insurance_risk="high",
        risk_factors=["hurricane", "flood"],
        notes="No rent control, reasonable eviction process",
    ),
    "AZ": StateData(
        state_code="AZ",
        state_name="Arizona",
        landlord_friendly_score=9,
        landlord_friendly=True,
        avg_property_tax_rate=0.0062,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["wildfire"],
        notes="Statewide rent control ban, fast evictions",
    ),
    "IN": StateData(
        state_code="IN",
        state_name="Indiana",
        landlord_friendly_score=8,
        landlord_friendly=True,
        avg_property_tax_rate=0.0085,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["tornado"],
        notes="No rent control, landlord-favorable courts",
    ),
    "TN": StateData(
        state_code="TN",
        state_name="Tennessee",
        landlord_friendly_score=9,
        landlord_friendly=True,
        avg_property_tax_rate=0.0071,
        has_state_income_tax=False,
        insurance_risk="medium",
        risk_factors=["tornado", "flood"],
        notes="Statewide rent control ban, no income tax",
    ),
    "AL": StateData(
        state_code="AL",
        state_name="Alabama",
        landlord_friendly_score=9,
        landlord_friendly=True,
        avg_property_tax_rate=0.0041,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["hurricane", "tornado"],
        notes="Lowest property taxes, very landlord friendly",
    ),
    "GA": StateData(
        state_code="GA",
        state_name="Georgia",
        landlord_friendly_score=8,
        landlord_friendly=True,
        avg_property_tax_rate=0.0092,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["hurricane", "tornado"],
        notes="Statewide rent control ban",
    ),
    "NC": StateData(
        state_code="NC",
        state_name="North Carolina",
        landlord_friendly_score=8,
        landlord_friendly=True,
        avg_property_tax_rate=0.0084,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["hurricane", "flood"],
        notes="No rent control, reasonable regulations",
    ),
    "SC": StateData(
        state_code="SC",
        state_name="South Carolina",
        landlord_friendly_score=8,
        landlord_friendly=True,
        avg_property_tax_rate=0.0057,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["hurricane", "flood"],
        notes="Landlord-favorable laws",
    ),
    "MO": StateData(
        state_code="MO",
        state_name="Missouri",
        landlord_friendly_score=7,
        landlord_friendly=True,
        avg_property_tax_rate=0.0097,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["tornado", "flood"],
        notes="Generally landlord friendly",
    ),
    "OH": StateData(
        state_code="OH",
        state_name="Ohio",
        landlord_friendly_score=7,
        landlord_friendly=True,
        avg_property_tax_rate=0.0156,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["tornado"],
        notes="Fast eviction process, no rent control statewide",
    ),
    "NV": StateData(
        state_code="NV",
        state_name="Nevada",
        landlord_friendly_score=6,
        landlord_friendly=True,
        avg_property_tax_rate=0.0060,
        has_state_income_tax=False,
        insurance_risk="low",
        risk_factors=["wildfire"],
        notes="No income tax, but some tenant protections",
    ),
    "UT": StateData(
        state_code="UT",
        state_name="Utah",
        landlord_friendly_score=7,
        landlord_friendly=True,
        avg_property_tax_rate=0.0063,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["wildfire"],
        notes="Generally landlord friendly",
    ),
    "CO": StateData(
        state_code="CO",
        state_name="Colorado",
        landlord_friendly_score=5,
        landlord_friendly=False,
        avg_property_tax_rate=0.0051,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["wildfire"],
        notes="Some cities have rent control, increasing tenant protections",
    ),

    # Moderately Landlord Friendly (5-7)
    "PA": StateData(
        state_code="PA",
        state_name="Pennsylvania",
        landlord_friendly_score=5,
        landlord_friendly=False,
        avg_property_tax_rate=0.0153,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["flood"],
        notes="Philadelphia has strong tenant protections",
    ),
    "MI": StateData(
        state_code="MI",
        state_name="Michigan",
        landlord_friendly_score=6,
        landlord_friendly=True,
        avg_property_tax_rate=0.0154,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["flood"],
        notes="Generally balanced landlord-tenant laws",
    ),
    "MN": StateData(
        state_code="MN",
        state_name="Minnesota",
        landlord_friendly_score=5,
        landlord_friendly=False,
        avg_property_tax_rate=0.0112,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["tornado"],
        notes="Minneapolis has rent control, stricter tenant protections",
    ),
    "IL": StateData(
        state_code="IL",
        state_name="Illinois",
        landlord_friendly_score=4,
        landlord_friendly=False,
        avg_property_tax_rate=0.0227,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["tornado"],
        notes="Chicago has strong tenant protections, high taxes",
    ),
    "WA": StateData(
        state_code="WA",
        state_name="Washington",
        landlord_friendly_score=4,
        landlord_friendly=False,
        avg_property_tax_rate=0.0098,
        has_state_income_tax=False,
        insurance_risk="medium",
        risk_factors=["earthquake"],
        notes="Seattle has strong tenant protections, eviction restrictions",
    ),
    "OR": StateData(
        state_code="OR",
        state_name="Oregon",
        landlord_friendly_score=3,
        landlord_friendly=False,
        avg_property_tax_rate=0.0097,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["earthquake", "wildfire"],
        notes="Statewide rent control, strong tenant protections",
    ),

    # Least Landlord Friendly (1-4)
    "CA": StateData(
        state_code="CA",
        state_name="California",
        landlord_friendly_score=2,
        landlord_friendly=False,
        avg_property_tax_rate=0.0076,
        has_state_income_tax=True,
        insurance_risk="high",
        risk_factors=["earthquake", "wildfire"],
        notes="Statewide rent control, very strong tenant protections",
    ),
    "NY": StateData(
        state_code="NY",
        state_name="New York",
        landlord_friendly_score=2,
        landlord_friendly=False,
        avg_property_tax_rate=0.0172,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=["flood"],
        notes="NYC rent control, extensive tenant protections",
    ),
    "NJ": StateData(
        state_code="NJ",
        state_name="New Jersey",
        landlord_friendly_score=3,
        landlord_friendly=False,
        avg_property_tax_rate=0.0249,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["hurricane", "flood"],
        notes="Highest property taxes in nation, tenant-friendly courts",
    ),
    "MA": StateData(
        state_code="MA",
        state_name="Massachusetts",
        landlord_friendly_score=3,
        landlord_friendly=False,
        avg_property_tax_rate=0.0123,
        has_state_income_tax=True,
        insurance_risk="medium",
        risk_factors=["hurricane"],
        notes="Boston has strong tenant protections",
    ),
    "DC": StateData(
        state_code="DC",
        state_name="District of Columbia",
        landlord_friendly_score=2,
        landlord_friendly=False,
        avg_property_tax_rate=0.0056,
        has_state_income_tax=True,
        insurance_risk="low",
        risk_factors=[],
        notes="Rent control, very strong tenant protections",
    ),
}

# Default for unknown states
DEFAULT_STATE_DATA = StateData(
    state_code="XX",
    state_name="Unknown",
    landlord_friendly_score=5,
    landlord_friendly=False,
    avg_property_tax_rate=0.0100,
    has_state_income_tax=True,
    insurance_risk="medium",
    risk_factors=[],
    notes="No specific data available",
)


def get_state_data(state_code: str) -> StateData:
    """
    Get static data for a state.

    Args:
        state_code: Two-letter state code (e.g., "TX", "FL")

    Returns:
        StateData object with landlord friendliness, taxes, insurance risk
    """
    return STATE_DATA.get(state_code.upper(), DEFAULT_STATE_DATA)


def is_landlord_friendly(state_code: str) -> bool:
    """Check if a state is considered landlord-friendly."""
    return get_state_data(state_code).landlord_friendly


def get_property_tax_rate(state_code: str) -> float:
    """Get average property tax rate for a state."""
    return get_state_data(state_code).avg_property_tax_rate


def get_insurance_risk(state_code: str) -> str:
    """Get insurance risk level for a state."""
    return get_state_data(state_code).insurance_risk


def get_all_landlord_friendly_states() -> list[str]:
    """Get list of all landlord-friendly state codes."""
    return [code for code, data in STATE_DATA.items() if data.landlord_friendly]
