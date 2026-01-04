"""
AI Due Diligence Agent for Real Estate Properties.

Uses Claude with web search to perform comprehensive research on a property,
identifying potential issues, red flags, and gathering useful information.
"""

import os
import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from src.agents.base import BaseAgent, AgentResult


@dataclass
class DueDiligenceFindings:
    """Structured findings from due diligence research."""

    # Property History
    ownership_history: list[dict] = field(default_factory=list)
    sale_history: list[dict] = field(default_factory=list)
    permit_history: list[dict] = field(default_factory=list)

    # Legal & Title
    liens_found: list[dict] = field(default_factory=list)
    easements: list[str] = field(default_factory=list)
    hoa_info: Optional[dict] = None
    zoning_info: Optional[dict] = None

    # Environmental & Safety
    environmental_concerns: list[dict] = field(default_factory=list)
    flood_history: list[str] = field(default_factory=list)
    crime_info: Optional[dict] = None

    # Market Context
    neighborhood_trends: list[str] = field(default_factory=list)
    comparable_sales: list[dict] = field(default_factory=list)
    development_plans: list[str] = field(default_factory=list)

    # Professional Contacts
    listing_agent: Optional[dict] = None
    recommended_inspectors: list[dict] = field(default_factory=list)
    recommended_contractors: list[dict] = field(default_factory=list)
    title_companies: list[dict] = field(default_factory=list)

    # News & Media
    news_mentions: list[dict] = field(default_factory=list)
    community_sentiment: list[str] = field(default_factory=list)


@dataclass
class DueDiligenceReport:
    """Complete due diligence report for a property."""

    # Meta
    property_id: str
    property_address: str
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Findings
    findings: DueDiligenceFindings = field(default_factory=DueDiligenceFindings)

    # Summary
    executive_summary: str = ""
    red_flags: list[dict] = field(default_factory=list)  # [{severity, title, description}]
    yellow_flags: list[dict] = field(default_factory=list)
    green_flags: list[dict] = field(default_factory=list)  # Positive findings

    # Recommendations
    recommended_actions: list[str] = field(default_factory=list)
    questions_for_seller: list[str] = field(default_factory=list)
    inspection_focus_areas: list[str] = field(default_factory=list)

    # Raw research
    search_queries_used: list[str] = field(default_factory=list)
    sources_consulted: list[str] = field(default_factory=list)
    raw_research_notes: str = ""

    # Error tracking
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        result = asdict(self)
        return result


class DueDiligenceAgent(BaseAgent):
    """
    AI agent that performs comprehensive due diligence research on a property.

    Uses Claude with web search to:
    - Research property history and ownership
    - Find news articles and public records
    - Identify potential legal or environmental issues
    - Gather market context and neighborhood info
    - Find relevant professional contacts
    """

    agent_name = "due_diligence"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key and HAS_ANTHROPIC:
            self.log("ANTHROPIC_API_KEY not set - due diligence will be limited", "warning")

    async def run(
        self,
        property_address: str,
        city: str,
        state: str,
        zip_code: str,
        property_id: str,
        list_price: Optional[float] = None,
        property_type: Optional[str] = None,
        year_built: Optional[int] = None,
        **kwargs
    ) -> AgentResult:
        """
        Execute comprehensive due diligence research on a property.

        Args:
            property_address: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code
            property_id: Database ID for the property
            list_price: Listing price (optional, for context)
            property_type: Type of property (optional)
            year_built: Year built (optional)

        Returns:
            AgentResult with DueDiligenceReport in data field
        """
        start_time = datetime.utcnow()

        report = DueDiligenceReport(
            property_id=property_id,
            property_address=f"{property_address}, {city}, {state} {zip_code}",
            status="running",
            started_at=start_time.isoformat(),
        )

        self.log(f"Starting due diligence for {property_address}, {city}, {state}")

        if not HAS_ANTHROPIC:
            report.status = "failed"
            report.errors.append("anthropic package not installed. Run: pip install anthropic")
            return AgentResult(
                success=False,
                data=report.to_dict(),
                message="anthropic package not installed",
                timestamp=datetime.utcnow(),
                duration_ms=0,
                errors=report.errors,
            )

        if not self.api_key:
            report.status = "failed"
            report.errors.append("ANTHROPIC_API_KEY environment variable not set")
            return AgentResult(
                success=False,
                data=report.to_dict(),
                message="ANTHROPIC_API_KEY not configured",
                timestamp=datetime.utcnow(),
                duration_ms=0,
                errors=report.errors,
            )

        try:
            # Build context for the research
            property_context = self._build_property_context(
                property_address, city, state, zip_code,
                list_price, property_type, year_built
            )

            # Run the research using Claude with web search
            research_result = await self._run_research(property_context, report)

            # Parse and structure the findings
            await self._parse_findings(research_result, report)

            report.status = "completed"
            report.completed_at = datetime.utcnow().isoformat()

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            self.log(f"Due diligence completed with {len(report.red_flags)} red flags")

            return AgentResult(
                success=True,
                data=report.to_dict(),
                message=f"Due diligence completed. Found {len(report.red_flags)} red flags.",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                errors=report.errors,
            )

        except Exception as e:
            report.status = "failed"
            report.errors.append(str(e))
            report.completed_at = datetime.utcnow().isoformat()

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            self.log(f"Due diligence failed: {e}", "error")

            return AgentResult(
                success=False,
                data=report.to_dict(),
                message=f"Due diligence failed: {e}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                errors=report.errors,
            )

    def _build_property_context(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        list_price: Optional[float],
        property_type: Optional[str],
        year_built: Optional[int],
    ) -> str:
        """Build context string for the property."""
        lines = [
            f"Property Address: {address}",
            f"City: {city}",
            f"State: {state}",
            f"ZIP Code: {zip_code}",
        ]

        if list_price:
            lines.append(f"Listing Price: ${list_price:,.0f}")
        if property_type:
            lines.append(f"Property Type: {property_type}")
        if year_built:
            lines.append(f"Year Built: {year_built}")

        return "\n".join(lines)

    async def _run_research(self, property_context: str, report: DueDiligenceReport) -> str:
        """Run the main research using Claude with web search."""

        client = AsyncAnthropic(api_key=self.api_key)

        research_prompt = f"""You are a thorough real estate due diligence researcher acting as an expert combination of:
- A seasoned real estate attorney
- An experienced property inspector
- A local market analyst
- A title company researcher

Your task is to perform comprehensive due diligence research on this property:

{property_context}

Please research the following areas thoroughly using web search:

## 1. PROPERTY HISTORY & OWNERSHIP
- Search for property records, previous sales, ownership history
- Look for any tax liens, judgments, or encumbrances
- Find permit history and any unpermitted work
- Check for any code violations

## 2. LEGAL & REGULATORY
- Search for any lawsuits involving this address
- Check zoning classification and any variances
- Look for HOA information, rules, and any litigation
- Research any easements or restrictions

## 3. ENVIRONMENTAL & SAFETY
- Search for environmental hazards nearby (superfund sites, industrial contamination)
- Look for flood history and current flood zone status
- Research crime statistics for the neighborhood
- Check for any natural disaster history (fires, earthquakes, hurricanes)

## 4. MARKET & NEIGHBORHOOD
- Research recent comparable sales in the area
- Look for upcoming development projects that could affect value
- Search for neighborhood trends and news
- Find information about school districts

## 5. PROFESSIONAL CONTACTS
- Find the listing agent's contact information and reviews
- Look for recommended home inspectors in the area
- Find local contractors with good reviews
- Identify reputable title companies

## 6. NEWS & MEDIA
- Search for any news articles mentioning this address
- Look for neighborhood news that could affect the property
- Find community forum discussions about the area

For each finding, clearly state:
- The source of the information
- The relevance to the property
- Whether it's a red flag (serious concern), yellow flag (needs investigation), or green flag (positive)

At the end, provide:
1. An executive summary of your findings
2. A list of specific red flags with severity ratings
3. Recommended next steps for the buyer
4. Questions to ask the seller
5. Areas the home inspector should focus on

Be thorough but organized. Focus on actionable intelligence that would affect a buying decision."""

        # Use Claude with web search tool (async call with timeout)
        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    tools=[
                        {
                            "type": "web_search_20250305",
                            "name": "web_search",
                            "max_uses": 15,  # Reduced from 20 to speed up
                        }
                    ],
                    messages=[
                        {"role": "user", "content": research_prompt}
                    ]
                ),
                timeout=300.0,  # 5 minute timeout for web search phase
            )
        except asyncio.TimeoutError:
            raise Exception("Research phase timed out after 5 minutes")

        # Collect all text responses and track sources
        research_text = []
        for block in response.content:
            if hasattr(block, 'text'):
                research_text.append(block.text)
            # Track web search results for sources
            if hasattr(block, 'type') and block.type == 'web_search_tool_result':
                if hasattr(block, 'content'):
                    for result in block.content:
                        if hasattr(result, 'url'):
                            report.sources_consulted.append(result.url)

        return "\n".join(research_text)

    async def _parse_findings(self, research_text: str, report: DueDiligenceReport) -> None:
        """Parse the research text into structured findings."""

        report.raw_research_notes = research_text

        # Use Claude to structure the findings
        client = AsyncAnthropic(api_key=self.api_key)

        structure_prompt = f"""Based on this due diligence research, extract and structure the findings into JSON format.

Research Notes:
{research_text}

Please return a JSON object with this structure:
{{
    "executive_summary": "2-3 paragraph summary of findings",
    "red_flags": [
        {{"severity": "critical|high|medium", "title": "Short title", "description": "Details", "source": "Where this was found"}}
    ],
    "yellow_flags": [
        {{"severity": "medium|low", "title": "Short title", "description": "Details", "source": "Where this was found"}}
    ],
    "green_flags": [
        {{"title": "Short title", "description": "Positive finding details"}}
    ],
    "recommended_actions": ["Action 1", "Action 2"],
    "questions_for_seller": ["Question 1", "Question 2"],
    "inspection_focus_areas": ["Area 1", "Area 2"],
    "findings": {{
        "ownership_history": [{{"date": "", "owner": "", "sale_price": ""}}],
        "liens_found": [{{"type": "", "amount": "", "status": ""}}],
        "environmental_concerns": [{{"type": "", "description": "", "distance": ""}}],
        "listing_agent": {{"name": "", "phone": "", "email": "", "company": ""}},
        "neighborhood_trends": ["Trend 1", "Trend 2"],
        "development_plans": ["Plan 1", "Plan 2"]
    }}
}}

Only include sections where you found relevant information. Be precise and factual.
Return ONLY valid JSON, no markdown code blocks or other formatting."""

        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[
                        {"role": "user", "content": structure_prompt}
                    ]
                ),
                timeout=60.0,  # 1 minute timeout for parsing
            )
        except asyncio.TimeoutError:
            report.errors.append("Parsing phase timed out")
            report.executive_summary = research_text[:2000] if len(research_text) > 2000 else research_text
            return

        # Parse the JSON response
        response_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text

        try:
            # Clean up potential markdown code blocks
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            structured = json.loads(clean_text.strip())

            # Update report with structured findings
            report.executive_summary = structured.get("executive_summary", "")
            report.red_flags = structured.get("red_flags", [])
            report.yellow_flags = structured.get("yellow_flags", [])
            report.green_flags = structured.get("green_flags", [])
            report.recommended_actions = structured.get("recommended_actions", [])
            report.questions_for_seller = structured.get("questions_for_seller", [])
            report.inspection_focus_areas = structured.get("inspection_focus_areas", [])

            # Update findings structure
            findings_data = structured.get("findings", {})
            report.findings.ownership_history = findings_data.get("ownership_history", [])
            report.findings.liens_found = findings_data.get("liens_found", [])
            report.findings.environmental_concerns = findings_data.get("environmental_concerns", [])
            report.findings.listing_agent = findings_data.get("listing_agent")
            report.findings.neighborhood_trends = findings_data.get("neighborhood_trends", [])
            report.findings.development_plans = findings_data.get("development_plans", [])

        except json.JSONDecodeError as e:
            report.errors.append(f"Failed to parse structured findings: {e}")
            # Keep raw research notes as fallback
            report.executive_summary = research_text[:2000] if len(research_text) > 2000 else research_text


# Convenience function for running due diligence
async def run_due_diligence(
    property_address: str,
    city: str,
    state: str,
    zip_code: str,
    property_id: str,
    **kwargs
) -> DueDiligenceReport:
    """
    Convenience function to run due diligence on a property.

    Returns a DueDiligenceReport with findings.
    """
    agent = DueDiligenceAgent()
    result = await agent.run(
        property_address=property_address,
        city=city,
        state=state,
        zip_code=zip_code,
        property_id=property_id,
        **kwargs
    )
    return result.data
