"""
Local US Metro Areas data for instant autocomplete.

This provides a comprehensive list of US metro areas for the market search
feature without requiring external API calls.

Data sources:
- BLS Metro Area Codes (employment data coverage)
- Census CBSA Codes (population data coverage)
- HUD FMR (rent data coverage)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MetroInfo:
    """Metro area information for search/autocomplete."""
    id: str  # e.g., "indianapolis_in"
    city: str  # e.g., "Indianapolis"
    state: str  # e.g., "IN"
    metro_name: str  # e.g., "Indianapolis-Carmel-Anderson"
    cbsa_code: str  # Census CBSA code
    has_bls_data: bool = True  # Has employment data
    has_census_data: bool = True  # Has population data
    has_hud_data: bool = False  # Has HUD FMR rent data
    has_redfin_data: bool = True  # Typically available for major metros


# Comprehensive list of US metros with data availability
# Metros are sorted by approximate population/importance
US_METROS: list[MetroInfo] = [
    # Top 10 metros
    MetroInfo("new_york_ny", "New York", "NY", "New York-Newark-Jersey City", "35620"),
    MetroInfo("los_angeles_ca", "Los Angeles", "CA", "Los Angeles-Long Beach-Anaheim", "31080"),
    MetroInfo("chicago_il", "Chicago", "IL", "Chicago-Naperville-Elgin", "16980"),
    MetroInfo("dallas_tx", "Dallas", "TX", "Dallas-Fort Worth-Arlington", "19100"),
    MetroInfo("houston_tx", "Houston", "TX", "Houston-The Woodlands-Sugar Land", "26420", has_hud_data=True),
    MetroInfo("washington_dc", "Washington", "DC", "Washington-Arlington-Alexandria", "47900"),
    MetroInfo("miami_fl", "Miami", "FL", "Miami-Fort Lauderdale-Pompano Beach", "33100", has_hud_data=True),
    MetroInfo("philadelphia_pa", "Philadelphia", "PA", "Philadelphia-Camden-Wilmington", "37980"),
    MetroInfo("atlanta_ga", "Atlanta", "GA", "Atlanta-Sandy Springs-Alpharetta", "12060"),
    MetroInfo("phoenix_az", "Phoenix", "AZ", "Phoenix-Mesa-Chandler", "38060", has_hud_data=True),

    # 11-25 metros
    MetroInfo("boston_ma", "Boston", "MA", "Boston-Cambridge-Newton", "14460"),
    MetroInfo("san_francisco_ca", "San Francisco", "CA", "San Francisco-Oakland-Berkeley", "41860"),
    MetroInfo("seattle_wa", "Seattle", "WA", "Seattle-Tacoma-Bellevue", "42660"),
    MetroInfo("detroit_mi", "Detroit", "MI", "Detroit-Warren-Dearborn", "19820"),
    MetroInfo("minneapolis_mn", "Minneapolis", "MN", "Minneapolis-St. Paul-Bloomington", "33460"),
    MetroInfo("san_diego_ca", "San Diego", "CA", "San Diego-Chula Vista-Carlsbad", "41740"),
    MetroInfo("tampa_fl", "Tampa", "FL", "Tampa-St. Petersburg-Clearwater", "45300", has_hud_data=True),
    MetroInfo("denver_co", "Denver", "CO", "Denver-Aurora-Lakewood", "19740"),
    MetroInfo("st_louis_mo", "St. Louis", "MO", "St. Louis", "41180"),
    MetroInfo("baltimore_md", "Baltimore", "MD", "Baltimore-Columbia-Towson", "12580"),
    MetroInfo("orlando_fl", "Orlando", "FL", "Orlando-Kissimmee-Sanford", "36740"),
    MetroInfo("charlotte_nc", "Charlotte", "NC", "Charlotte-Concord-Gastonia", "16740"),
    MetroInfo("san_antonio_tx", "San Antonio", "TX", "San Antonio-New Braunfels", "41700"),
    MetroInfo("portland_or", "Portland", "OR", "Portland-Vancouver-Hillsboro", "38900"),
    MetroInfo("sacramento_ca", "Sacramento", "CA", "Sacramento-Roseville-Folsom", "40900"),

    # 26-50 metros (investor-friendly markets)
    MetroInfo("pittsburgh_pa", "Pittsburgh", "PA", "Pittsburgh", "38300"),
    MetroInfo("las_vegas_nv", "Las Vegas", "NV", "Las Vegas-Henderson-Paradise", "29820"),
    MetroInfo("austin_tx", "Austin", "TX", "Austin-Round Rock-Georgetown", "12420", has_hud_data=True),
    MetroInfo("cincinnati_oh", "Cincinnati", "OH", "Cincinnati", "17140"),
    MetroInfo("kansas_city_mo", "Kansas City", "MO", "Kansas City", "28140", has_hud_data=True),
    MetroInfo("columbus_oh", "Columbus", "OH", "Columbus", "18140"),
    MetroInfo("indianapolis_in", "Indianapolis", "IN", "Indianapolis-Carmel-Anderson", "26900", has_hud_data=True),
    MetroInfo("cleveland_oh", "Cleveland", "OH", "Cleveland-Elyria", "17460", has_hud_data=True),
    MetroInfo("nashville_tn", "Nashville", "TN", "Nashville-Davidson-Murfreesboro-Franklin", "34980", has_hud_data=True),
    MetroInfo("jacksonville_fl", "Jacksonville", "FL", "Jacksonville", "27260"),
    MetroInfo("raleigh_nc", "Raleigh", "NC", "Raleigh-Cary", "39580"),
    MetroInfo("memphis_tn", "Memphis", "TN", "Memphis", "32820", has_hud_data=True),
    MetroInfo("salt_lake_city_ut", "Salt Lake City", "UT", "Salt Lake City", "41620"),
    MetroInfo("birmingham_al", "Birmingham", "AL", "Birmingham-Hoover", "13820", has_hud_data=True),
    MetroInfo("richmond_va", "Richmond", "VA", "Richmond", "40060"),
    MetroInfo("louisville_ky", "Louisville", "KY", "Louisville-Jefferson County", "31140"),
    MetroInfo("oklahoma_city_ok", "Oklahoma City", "OK", "Oklahoma City", "36420"),
    MetroInfo("hartford_ct", "Hartford", "CT", "Hartford-East Hartford-Middletown", "25540"),
    MetroInfo("milwaukee_wi", "Milwaukee", "WI", "Milwaukee-Waukesha", "33340"),
    MetroInfo("providence_ri", "Providence", "RI", "Providence-Warwick", "39300"),

    # Additional investor-friendly markets
    MetroInfo("huntsville_al", "Huntsville", "AL", "Huntsville", "26620"),
    MetroInfo("tucson_az", "Tucson", "AZ", "Tucson", "46060"),
    MetroInfo("tulsa_ok", "Tulsa", "OK", "Tulsa", "46140"),
    MetroInfo("fresno_ca", "Fresno", "CA", "Fresno", "23420"),
    MetroInfo("albuquerque_nm", "Albuquerque", "NM", "Albuquerque", "10740"),
    MetroInfo("omaha_ne", "Omaha", "NE", "Omaha-Council Bluffs", "36540"),
    MetroInfo("colorado_springs_co", "Colorado Springs", "CO", "Colorado Springs", "17820"),
    MetroInfo("reno_nv", "Reno", "NV", "Reno", "39900"),
    MetroInfo("boise_id", "Boise", "ID", "Boise City", "14260"),
    MetroInfo("spokane_wa", "Spokane", "WA", "Spokane-Spokane Valley", "44060"),
    MetroInfo("des_moines_ia", "Des Moines", "IA", "Des Moines-West Des Moines", "19780"),
    MetroInfo("little_rock_ar", "Little Rock", "AR", "Little Rock-North Little Rock-Conway", "30780"),
    MetroInfo("grand_rapids_mi", "Grand Rapids", "MI", "Grand Rapids-Kentwood", "24340"),
    MetroInfo("knoxville_tn", "Knoxville", "TN", "Knoxville", "28940"),
    MetroInfo("chattanooga_tn", "Chattanooga", "TN", "Chattanooga", "16860"),
    MetroInfo("wichita_ks", "Wichita", "KS", "Wichita", "48620"),
    MetroInfo("greenville_sc", "Greenville", "SC", "Greenville-Anderson", "24860"),
    MetroInfo("columbia_sc", "Columbia", "SC", "Columbia", "17900"),
    MetroInfo("charleston_sc", "Charleston", "SC", "Charleston-North Charleston", "16700"),
    MetroInfo("dayton_oh", "Dayton", "OH", "Dayton-Kettering", "19380"),
    MetroInfo("akron_oh", "Akron", "OH", "Akron", "10420"),
    MetroInfo("toledo_oh", "Toledo", "OH", "Toledo", "45780"),
    MetroInfo("lexington_ky", "Lexington", "KY", "Lexington-Fayette", "30460"),
    MetroInfo("greensboro_nc", "Greensboro", "NC", "Greensboro-High Point", "24660"),
    MetroInfo("winston_salem_nc", "Winston-Salem", "NC", "Winston-Salem", "49180"),
    MetroInfo("durham_nc", "Durham", "NC", "Durham-Chapel Hill", "20500"),
    MetroInfo("el_paso_tx", "El Paso", "TX", "El Paso", "21340"),
    MetroInfo("fort_worth_tx", "Fort Worth", "TX", "Fort Worth-Arlington-Grapevine", "23104"),
    MetroInfo("mcallen_tx", "McAllen", "TX", "McAllen-Edinburg-Mission", "32580"),
    MetroInfo("bakersfield_ca", "Bakersfield", "CA", "Bakersfield", "12540"),
    MetroInfo("stockton_ca", "Stockton", "CA", "Stockton", "44700"),
    MetroInfo("riverside_ca", "Riverside", "CA", "Riverside-San Bernardino-Ontario", "40140"),
    MetroInfo("new_orleans_la", "New Orleans", "LA", "New Orleans-Metairie", "35380"),
    MetroInfo("baton_rouge_la", "Baton Rouge", "LA", "Baton Rouge", "12940"),
    MetroInfo("shreveport_la", "Shreveport", "LA", "Shreveport-Bossier City", "43340"),
    MetroInfo("jackson_ms", "Jackson", "MS", "Jackson", "27140"),
    MetroInfo("mobile_al", "Mobile", "AL", "Mobile", "33660"),
    MetroInfo("montgomery_al", "Montgomery", "AL", "Montgomery", "33860"),
]


def search_metros(query: str, limit: int = 10) -> list[MetroInfo]:
    """
    Search metros by name (instant, no API call).

    Args:
        query: Search query (city name, state, or metro name)
        limit: Max results to return

    Returns:
        List of matching MetroInfo objects
    """
    if not query or len(query) < 2:
        return []

    query_lower = query.lower().strip()

    matches = []
    for metro in US_METROS:
        # Match against city, state, metro name, or id
        if (query_lower in metro.city.lower() or
            query_lower in metro.state.lower() or
            query_lower in metro.metro_name.lower() or
            query_lower in metro.id.lower()):
            matches.append(metro)

    # Sort by relevance (starts with query first, then alphabetically)
    matches.sort(key=lambda m: (
        not m.city.lower().startswith(query_lower),
        not m.metro_name.lower().startswith(query_lower),
        m.city.lower()
    ))

    return matches[:limit]


def get_metro_by_id(metro_id: str) -> Optional[MetroInfo]:
    """Get metro info by ID."""
    metro_id_lower = metro_id.lower()
    for metro in US_METROS:
        if metro.id == metro_id_lower:
            return metro
    return None


def get_supported_metros() -> list[MetroInfo]:
    """Get metros with full data support (HUD rent data)."""
    return [m for m in US_METROS if m.has_hud_data]
