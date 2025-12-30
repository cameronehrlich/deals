"""
Phase 6.3: Investment Risk Assessment API.

Evaluates property, market, location, and financial risks.
"""

from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/risk", tags=["risk"])


# ==================== Models ====================

class RiskFlag(BaseModel):
    """Individual risk flag."""
    category: str  # property, market, location, financial
    severity: str  # low, medium, high, critical
    title: str
    description: str
    recommendation: Optional[str] = None


class RiskAssessment(BaseModel):
    """Complete risk assessment for a property."""
    # Overall risk
    risk_level: str = Field("unknown", description="low, medium, high, critical")
    risk_score: int = Field(0, ge=0, le=100, description="0=low risk, 100=high risk")

    # Flags by category
    property_flags: list[RiskFlag] = Field(default_factory=list)
    market_flags: list[RiskFlag] = Field(default_factory=list)
    location_flags: list[RiskFlag] = Field(default_factory=list)
    financial_flags: list[RiskFlag] = Field(default_factory=list)

    # Summary
    total_flags: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # Categorized concerns
    deal_breakers: list[str] = Field(default_factory=list)
    investigate: list[str] = Field(default_factory=list)
    minor_concerns: list[str] = Field(default_factory=list)

    # Due diligence recommendations
    due_diligence_items: list[str] = Field(default_factory=list)


# ==================== Risk Analysis Logic ====================

def assess_property_risks(property_data: dict) -> list[RiskFlag]:
    """Assess property-specific risks."""
    flags = []

    # Days on market
    dom = property_data.get("days_on_market")
    if dom is not None:
        if dom > 120:
            flags.append(RiskFlag(
                category="property",
                severity="high",
                title="Extended Time on Market",
                description=f"Property has been listed for {dom} days, suggesting potential issues or overpricing.",
                recommendation="Request price history and ask about reasons for extended listing period.",
            ))
        elif dom > 60:
            flags.append(RiskFlag(
                category="property",
                severity="medium",
                title="Above Average Days on Market",
                description=f"Property has been listed for {dom} days, above typical market timeframes.",
                recommendation="Investigate pricing history and comparable sales.",
            ))

    # Price per sqft analysis
    price = property_data.get("list_price")
    sqft = property_data.get("sqft")
    if price and sqft and sqft > 0:
        price_per_sqft = price / sqft
        if price_per_sqft > 400:
            flags.append(RiskFlag(
                category="property",
                severity="medium",
                title="High Price Per Square Foot",
                description=f"${price_per_sqft:.0f}/sqft is on the higher end. Verify with comparable sales.",
                recommendation="Run comp analysis to validate pricing.",
            ))

    # Year built concerns
    year_built = property_data.get("year_built")
    if year_built:
        import datetime
        age = datetime.datetime.now().year - year_built
        if age > 50:
            flags.append(RiskFlag(
                category="property",
                severity="medium",
                title="Older Construction",
                description=f"Built in {year_built} ({age} years old). May have outdated systems or need significant repairs.",
                recommendation="Budget for major system replacements (roof, HVAC, plumbing, electrical).",
            ))
        elif age > 30:
            flags.append(RiskFlag(
                category="property",
                severity="low",
                title="Aging Property",
                description=f"Built in {year_built}. Consider age of major systems during inspection.",
                recommendation="Request maintenance records and age of major systems.",
            ))

    # No photos
    photos = property_data.get("photos", [])
    if not photos:
        flags.append(RiskFlag(
            category="property",
            severity="low",
            title="No Photos Available",
            description="Listing lacks photos which could indicate issues.",
            recommendation="Request photos or schedule viewing before proceeding.",
        ))

    return flags


def assess_financial_risks(property_data: dict, analysis: Optional[dict]) -> list[RiskFlag]:
    """Assess financial risks."""
    flags = []

    if not analysis:
        return flags

    financials = analysis.get("financials", {})

    # Cash flow
    monthly_cf = financials.get("monthly_cash_flow")
    if monthly_cf is not None:
        if monthly_cf < 0:
            flags.append(RiskFlag(
                category="financial",
                severity="critical",
                title="Negative Cash Flow",
                description=f"Property shows ${monthly_cf:.0f}/month negative cash flow at current assumptions.",
                recommendation="Re-evaluate rent estimates, reduce offer price, or increase down payment.",
            ))
        elif monthly_cf < 100:
            flags.append(RiskFlag(
                category="financial",
                severity="high",
                title="Thin Cash Flow Margins",
                description=f"Only ${monthly_cf:.0f}/month positive cash flow leaves little room for unexpected expenses.",
                recommendation="Stress test against vacancy and maintenance increases.",
            ))
        elif monthly_cf < 200:
            flags.append(RiskFlag(
                category="financial",
                severity="medium",
                title="Moderate Cash Flow",
                description=f"${monthly_cf:.0f}/month cash flow may be tight during vacancies or repairs.",
                recommendation="Build reserves before purchasing.",
            ))

    # Cash on cash return
    coc = financials.get("cash_on_cash_return")
    if coc is not None:
        if coc < 0:
            flags.append(RiskFlag(
                category="financial",
                severity="critical",
                title="Negative Returns",
                description=f"Cash-on-cash return is {coc:.1f}%, indicating a losing investment.",
                recommendation="This deal does not meet minimum investment criteria.",
            ))
        elif coc < 4:
            flags.append(RiskFlag(
                category="financial",
                severity="high",
                title="Below-Market Returns",
                description=f"Cash-on-cash return of {coc:.1f}% is below typical investment thresholds.",
                recommendation="Compare to alternative investments (REITs, stocks, etc.).",
            ))
        elif coc < 6:
            flags.append(RiskFlag(
                category="financial",
                severity="medium",
                title="Modest Returns",
                description=f"Cash-on-cash return of {coc:.1f}% is modest for a rental investment.",
                recommendation="Evaluate appreciation potential to justify lower cash returns.",
            ))

    # DSCR
    dscr = financials.get("dscr")
    if dscr is not None:
        if dscr < 1.0:
            flags.append(RiskFlag(
                category="financial",
                severity="critical",
                title="Inadequate Debt Service Coverage",
                description=f"DSCR of {dscr:.2f} means income doesn't cover debt payments.",
                recommendation="May not qualify for DSCR loans. Increase down payment or reduce offer.",
            ))
        elif dscr < 1.2:
            flags.append(RiskFlag(
                category="financial",
                severity="high",
                title="Low Debt Service Coverage",
                description=f"DSCR of {dscr:.2f} may not meet lender requirements (typically 1.2+).",
                recommendation="DSCR loans may require higher down payment or points.",
            ))

    # Break-even occupancy
    break_even = financials.get("break_even_occupancy")
    if break_even is not None:
        if break_even > 95:
            flags.append(RiskFlag(
                category="financial",
                severity="high",
                title="High Break-Even Occupancy",
                description=f"Need {break_even:.0f}% occupancy to break even. Any vacancy causes losses.",
                recommendation="Consider if you can sustain payments during vacancies.",
            ))
        elif break_even > 85:
            flags.append(RiskFlag(
                category="financial",
                severity="medium",
                title="Elevated Break-Even",
                description=f"Break-even at {break_even:.0f}% occupancy leaves limited vacancy buffer.",
                recommendation="Budget for 1-2 months vacancy per year.",
            ))

    return flags


def assess_location_risks(property_data: dict, location_data: Optional[dict]) -> list[RiskFlag]:
    """Assess location-based risks."""
    flags = []

    if not location_data:
        return flags

    # Flood zone
    flood_zone = location_data.get("flood_zone")
    if flood_zone:
        zone_upper = str(flood_zone).upper()
        if zone_upper.startswith("V"):
            flags.append(RiskFlag(
                category="location",
                severity="critical",
                title="High Flood Risk Zone",
                description=f"FEMA Zone {flood_zone} indicates coastal high-hazard flood area.",
                recommendation="Flood insurance required. May be very expensive or unavailable.",
            ))
        elif zone_upper.startswith("A"):
            flags.append(RiskFlag(
                category="location",
                severity="high",
                title="Special Flood Hazard Area",
                description=f"FEMA Zone {flood_zone} requires flood insurance if financed.",
                recommendation="Get flood insurance quotes before closing.",
            ))

    # Noise score
    noise_data = location_data.get("noise")
    if noise_data:
        noise_score = noise_data.get("noise_score")
        if noise_score is not None and noise_score > 80:
            flags.append(RiskFlag(
                category="location",
                severity="medium",
                title="High Noise Area",
                description=f"Noise score of {noise_score} indicates elevated ambient noise.",
                recommendation="Visit property at different times to assess noise impact on rentability.",
            ))

    # Walk score (very low)
    walk_score = location_data.get("walk_score")
    if walk_score is not None and walk_score < 30:
        flags.append(RiskFlag(
            category="location",
            severity="low",
            title="Car-Dependent Location",
            description=f"Walk Score of {walk_score} means almost all errands require a car.",
            recommendation="Factor in tenant demographics - families may be fine, but limits tenant pool.",
        ))

    # School ratings
    schools = location_data.get("schools", [])
    if schools:
        ratings = [s.get("rating") for s in schools if s.get("rating")]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            if avg_rating < 4:
                flags.append(RiskFlag(
                    category="location",
                    severity="medium",
                    title="Low School Ratings",
                    description=f"Average school rating is {avg_rating:.1f}/10, which may affect tenant quality and appreciation.",
                    recommendation="Consider impact on family tenant appeal and long-term value.",
                ))

    return flags


def calculate_risk_score(flags: list[RiskFlag]) -> int:
    """Calculate overall risk score from flags."""
    if not flags:
        return 0

    # Weight by severity
    weights = {"critical": 40, "high": 25, "medium": 10, "low": 5}
    total = sum(weights.get(f.severity, 0) for f in flags)

    # Cap at 100
    return min(100, total)


def determine_risk_level(score: int) -> str:
    """Determine risk level from score."""
    if score >= 60:
        return "critical"
    elif score >= 40:
        return "high"
    elif score >= 20:
        return "medium"
    return "low"


def categorize_concerns(flags: list[RiskFlag]) -> tuple[list[str], list[str], list[str]]:
    """Categorize flags into deal breakers, investigate, and minor concerns."""
    deal_breakers = []
    investigate = []
    minor = []

    for flag in flags:
        if flag.severity == "critical":
            deal_breakers.append(flag.title)
        elif flag.severity == "high":
            investigate.append(flag.title)
        else:
            minor.append(flag.title)

    return deal_breakers, investigate, minor


def generate_due_diligence(flags: list[RiskFlag]) -> list[str]:
    """Generate due diligence recommendations based on flags."""
    items = set()

    for flag in flags:
        if flag.recommendation:
            items.add(flag.recommendation)

    # Add standard items based on categories
    categories = {f.category for f in flags}

    if "property" in categories:
        items.add("Order professional home inspection")
        items.add("Request seller disclosures")

    if "financial" in categories:
        items.add("Verify rent estimates with local property managers")
        items.add("Get current tax and insurance quotes")

    if "location" in categories:
        items.add("Drive the neighborhood at different times of day")
        items.add("Research recent crime statistics")

    return sorted(list(items))


# ==================== Endpoints ====================

@router.get("/assessment/{property_id}", response_model=RiskAssessment)
async def get_risk_assessment(property_id: str):
    """
    Get comprehensive risk assessment for a saved property.

    Evaluates property, market, location, and financial risks.
    """
    from src.db import get_repository

    repo = get_repository()

    # Get property data
    property_data = repo.get_saved_property(property_id)
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    # Get analysis data if available
    analysis = property_data.get("analysis")
    location_data = property_data.get("location_data", {})

    # Assess risks by category
    property_flags = assess_property_risks(property_data)
    financial_flags = assess_financial_risks(property_data, analysis)
    location_flags = assess_location_risks(property_data, location_data)
    market_flags = []  # Would need market data integration

    # Combine all flags
    all_flags = property_flags + financial_flags + location_flags + market_flags

    # Count by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for flag in all_flags:
        severity_counts[flag.severity] = severity_counts.get(flag.severity, 0) + 1

    # Calculate overall risk
    risk_score = calculate_risk_score(all_flags)
    risk_level = determine_risk_level(risk_score)

    # Categorize concerns
    deal_breakers, investigate, minor = categorize_concerns(all_flags)

    # Generate due diligence
    dd_items = generate_due_diligence(all_flags)

    return RiskAssessment(
        risk_level=risk_level,
        risk_score=risk_score,
        property_flags=property_flags,
        market_flags=market_flags,
        location_flags=location_flags,
        financial_flags=financial_flags,
        total_flags=len(all_flags),
        critical_count=severity_counts["critical"],
        high_count=severity_counts["high"],
        medium_count=severity_counts["medium"],
        low_count=severity_counts["low"],
        deal_breakers=deal_breakers,
        investigate=investigate,
        minor_concerns=minor,
        due_diligence_items=dd_items,
    )
