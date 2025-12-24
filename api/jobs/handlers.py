"""Job handlers for background tasks."""

import asyncio
from typing import Optional
from src.db.sqlite_repository import SQLiteRepository
from src.db.models import JobDB


def get_fresh_repository() -> SQLiteRepository:
    """Get a fresh repository instance for worker processes."""
    return SQLiteRepository()


class JobHandlers:
    """Handlers for different job types."""

    @staticmethod
    async def enrich_market(job: JobDB) -> dict:
        """
        Enrich a single market with data from all sources.

        Payload:
            market_id: str - The market ID to enrich
        """
        from src.data_sources.aggregator import DataAggregator
        from src.models.market import MarketMetrics
        from src.db.models import MarketDB

        market_id = job.payload.get("market_id")
        if not market_id:
            raise ValueError("market_id is required in payload")

        # Use fresh repo for each job to avoid stale sessions
        repo = get_fresh_repository()

        try:
            # Find market
            market_db = repo.session.query(MarketDB).filter_by(id=market_id).first()
            if not market_db:
                raise ValueError(f"Market not found: {market_id}")

            market_name = f"{market_db.name}, {market_db.state}"
            print(f"[Job] Starting enrichment for {market_name}")

            # Update job progress
            repo.update_job_status(
                job.id,
                status="running",
                message=f"Fetching data for {market_name}...",
                progress=10,
            )

            aggregator = DataAggregator()
            try:
                # Fetch data from all sources with timeout
                print(f"[Job] Fetching market data for {market_name}...")
                enriched_data = await asyncio.wait_for(
                    aggregator.get_market_data(
                        city=market_db.name,
                        state=market_db.state,
                        metro=market_db.metro,
                    ),
                    timeout=45.0,  # Reduced timeout
                )

                repo.update_job_status(
                    job.id,
                    status="running",
                    message="Processing market data...",
                    progress=70,
                )

                if enriched_data:
                    print(f"[Job] Got data from: {enriched_data.data_sources}")

                    # Convert to Market model and calculate scores
                    market_model = enriched_data.to_market()
                    metrics = MarketMetrics.from_market(market_model)

                    # Refresh market_db in case it changed
                    repo.session.refresh(market_db)

                    # Update database
                    market_db.market_data = market_model.model_dump(mode="json")
                    market_db.overall_score = metrics.overall_score
                    market_db.cash_flow_score = metrics.cash_flow_score
                    market_db.growth_score = metrics.growth_score
                    market_db.api_support = {
                        "listings": True,
                        "income": True,
                        "redfin": bool(enriched_data.median_sale_price),
                        "bls": bool(enriched_data.job_growth_yoy),
                        "census": bool(enriched_data.population),
                        "hud": bool(enriched_data.fmr_2br),
                    }
                    repo.session.commit()

                    print(f"[Job] Completed {market_name}: score={metrics.overall_score:.1f}")

                    return {
                        "market_id": market_id,
                        "name": market_name,
                        "overall_score": metrics.overall_score,
                        "data_sources": enriched_data.data_sources,
                        "errors": enriched_data.enrichment_errors,
                    }
                else:
                    raise ValueError("No data returned from aggregator")

            except asyncio.TimeoutError:
                print(f"[Job] Timeout for {market_name}")
                raise ValueError(f"Timeout fetching data for {market_name}")
            finally:
                await aggregator.close()
        finally:
            repo.close()

    @staticmethod
    async def enrich_property(job: JobDB) -> dict:
        """
        Fully enrich a saved property with rent estimate, market data, analysis, and location data.

        Payload:
            property_id: str - The property ID to enrich
            down_payment_pct: float - Down payment percentage (default 0.25)
            interest_rate: float - Interest rate (default 0.07)
        """
        from src.data_sources.walkscore import WalkScoreClient
        from src.data_sources.fema_flood import FEMAFloodClient
        from src.data_sources.geocoder import get_geocoder
        from src.data_sources.aggregator import DataAggregator
        from src.models.property import Property, PropertyType, PropertyStatus
        from src.models.deal import Deal, DealPipeline
        from src.models.financials import Financials, LoanTerms
        from src.models.market import MarketMetrics
        from src.db.models import SavedPropertyDB
        from datetime import datetime

        property_id = job.payload.get("property_id")
        if not property_id:
            raise ValueError("property_id is required in payload")

        down_payment_pct = job.payload.get("down_payment_pct", 0.25)
        interest_rate = job.payload.get("interest_rate", 0.07)

        repo = get_fresh_repository()
        aggregator = DataAggregator()
        enrichment_errors = []

        try:
            prop = repo.session.query(SavedPropertyDB).filter_by(id=property_id).first()

            if not prop:
                raise ValueError(f"Property not found: {property_id}")

            print(f"[Job] Starting full property enrichment for {prop.address}")

            # Update status to show we're working
            repo.update_job_status(
                job.id,
                status="running",
                message=f"Enriching {prop.address}...",
                progress=5,
            )

            # Step 1: Geocode if needed
            latitude = prop.latitude
            longitude = prop.longitude

            if not latitude or not longitude:
                repo.update_job_status(
                    job.id, status="running", message="Geocoding address...", progress=10
                )
                geocoder = get_geocoder()
                try:
                    geo_result = await geocoder.geocode(
                        address=prop.address, city=prop.city, state=prop.state
                    )
                    if geo_result:
                        latitude = geo_result.latitude
                        longitude = geo_result.longitude
                        prop.latitude = latitude
                        prop.longitude = longitude
                except Exception as e:
                    print(f"[Job] Geocoding failed: {e}")
                    enrichment_errors.append(f"Geocoding: {e}")

            # Step 2: Get rent estimate (doesn't require coordinates)
            repo.update_job_status(
                job.id, status="running", message="Getting rent estimate...", progress=20
            )
            estimated_rent = prop.estimated_rent
            if not estimated_rent:
                try:
                    rent_result = await aggregator.rentcast.get_rent_estimate(
                        address=prop.address,
                        city=prop.city,
                        state=prop.state,
                        zip_code=prop.zip_code,
                        bedrooms=prop.bedrooms or 3,
                        bathrooms=prop.bathrooms or 2.0,
                        sqft=prop.sqft,
                    )
                    if rent_result:
                        estimated_rent = rent_result.rent_estimate
                        prop.estimated_rent = estimated_rent
                        print(f"[Job] Got rent estimate: ${estimated_rent}/mo")
                except Exception as e:
                    print(f"[Job] Rent estimate failed: {e}")
                    enrichment_errors.append(f"Rent estimate: {e}")

            # Step 3: Get market data
            repo.update_job_status(
                job.id, status="running", message="Fetching market data...", progress=35
            )
            market = None
            market_detail = None
            try:
                market_data = await aggregator.get_market_data(prop.city, prop.state)
                if market_data:
                    market = market_data.to_market()
                    if market:
                        metrics = MarketMetrics.from_market(market)
                        market_detail = {
                            "id": market.id,
                            "name": market.name,
                            "state": market.state,
                            "metro": market.metro,
                            "overall_score": metrics.overall_score,
                            "cash_flow_score": metrics.cash_flow_score,
                            "growth_score": metrics.growth_score,
                        }
                        print(f"[Job] Got market data: {market.name} (score: {metrics.overall_score})")
            except Exception as e:
                print(f"[Job] Market data failed: {e}")
                enrichment_errors.append(f"Market data: {e}")

            # Step 4: Run deal analysis
            repo.update_job_status(
                job.id, status="running", message="Analyzing financials...", progress=50
            )

            # Map property type
            type_mapping = {
                "single_family_home": PropertyType.SFH,
                "single_family": PropertyType.SFH,
                "condo": PropertyType.CONDO,
                "townhouse": PropertyType.TOWNHOUSE,
                "duplex": PropertyType.DUPLEX,
                "triplex": PropertyType.TRIPLEX,
                "fourplex": PropertyType.FOURPLEX,
                "multi_family": PropertyType.MULTI_FAMILY,
            }
            prop_type = type_mapping.get(
                (prop.property_type or "single_family").lower().replace("-", "_").replace(" ", "_"),
                PropertyType.SFH
            )

            # Create Property model
            property_model = Property(
                id=prop.id,
                address=prop.address,
                city=prop.city,
                state=prop.state,
                zip_code=prop.zip_code,
                latitude=latitude,
                longitude=longitude,
                list_price=prop.list_price,
                property_type=prop_type,
                bedrooms=prop.bedrooms or 3,
                bathrooms=prop.bathrooms or 2.0,
                sqft=prop.sqft,
                status=PropertyStatus.ACTIVE,
                source=prop.source,
                source_url=prop.source_url,
                estimated_rent=estimated_rent,
            )

            # Create Deal and run analysis
            deal = Deal(
                id=f"deal_{prop.id}",
                property=property_model,
                market=market,
                pipeline_status=DealPipeline.NEW,
                first_seen=datetime.now(),
            )

            deal.financials = Financials(
                property_id=property_model.id,
                purchase_price=prop.list_price,
                estimated_rent=estimated_rent or 0,
                loan=LoanTerms(
                    down_payment_pct=down_payment_pct,
                    interest_rate=interest_rate,
                ),
            )

            deal.analyze()

            # Update property with analysis results
            prop.overall_score = deal.score.overall_score if deal.score else None
            prop.financial_score = deal.score.financial_score if deal.score else None
            prop.market_score = deal.score.market_score if deal.score else None
            prop.risk_score = deal.score.risk_score if deal.score else None
            prop.liquidity_score = deal.score.liquidity_score if deal.score else None

            if deal.financials:
                prop.cash_flow = deal.financials.monthly_cash_flow

            if deal.financial_metrics:
                prop.cash_on_cash = deal.financial_metrics.cash_on_cash_return
                prop.cap_rate = deal.financial_metrics.cap_rate

            # Store full analysis data
            prop.analysis_data = {
                "property": property_model.model_dump(mode="json"),
                "financials": deal.financials.model_dump(mode="json") if deal.financials else None,
                "financial_metrics": deal.financial_metrics.model_dump(mode="json") if deal.financial_metrics else None,
                "score": deal.score.model_dump(mode="json") if deal.score else None,
                "pros": deal.pros,
                "cons": deal.cons,
                "market": market_detail,
            }
            prop.last_analyzed = datetime.utcnow()

            print(f"[Job] Analysis complete: score={prop.overall_score}, CoC={prop.cash_on_cash}")

            # Step 5: Get location data (Walk Score, Flood Zone)
            location_data = prop.location_data or {}

            if latitude and longitude:
                # Walk Score
                repo.update_job_status(
                    job.id, status="running", message="Fetching Walk Score...", progress=65
                )
                try:
                    walkscore = WalkScoreClient()
                    score_data = await walkscore.get_scores(
                        address=prop.address,
                        latitude=latitude,
                        longitude=longitude,
                    )
                    if score_data:
                        location_data["walk_score"] = score_data.walk_score
                        location_data["walk_description"] = score_data.walk_description
                        location_data["transit_score"] = score_data.transit_score
                        location_data["transit_description"] = score_data.transit_description
                        location_data["bike_score"] = score_data.bike_score
                        location_data["bike_description"] = score_data.bike_description
                        print(f"[Job] Walk Score: {score_data.walk_score}")
                    await walkscore.close()
                except Exception as e:
                    print(f"[Job] Walk Score failed: {e}")
                    enrichment_errors.append(f"Walk Score: {e}")

                # Flood Zone
                repo.update_job_status(
                    job.id, status="running", message="Checking flood zone...", progress=80
                )
                try:
                    fema = FEMAFloodClient()
                    flood_data = await fema.get_flood_zone(latitude=latitude, longitude=longitude)
                    if flood_data:
                        location_data["flood_zone"] = {
                            "zone": flood_data.flood_zone,
                            "zone_subtype": flood_data.zone_subtype,
                            "risk_level": flood_data.risk_level,
                            "description": flood_data.description,
                            "requires_insurance": flood_data.requires_insurance,
                            "annual_chance": flood_data.annual_chance,
                        }
                        print(f"[Job] Flood zone: {flood_data.flood_zone} ({flood_data.risk_level})")
                    await fema.close()
                except Exception as e:
                    print(f"[Job] Flood zone failed: {e}")
                    enrichment_errors.append(f"Flood zone: {e}")

            # Update location data
            prop.location_data = location_data
            prop.location_data_fetched = datetime.utcnow()

            # Update pipeline status
            prop.pipeline_status = "analyzed"

            # Commit all changes
            repo.session.commit()

            print(f"[Job] Completed full enrichment for {prop.address}")

            return {
                "property_id": property_id,
                "address": prop.address,
                "overall_score": prop.overall_score,
                "cash_on_cash": prop.cash_on_cash,
                "cash_flow": prop.cash_flow,
                "estimated_rent": estimated_rent,
                "market": market_detail,
                "location_data": location_data,
                "errors": enrichment_errors,
            }
        finally:
            await aggregator.close()
            repo.close()


# Map job types to handlers
JOB_HANDLERS = {
    "enrich_market": JobHandlers.enrich_market,
    "enrich_property": JobHandlers.enrich_property,
}


async def execute_job(job: JobDB) -> dict:
    """Execute a job based on its type."""
    handler = JOB_HANDLERS.get(job.job_type)
    if not handler:
        raise ValueError(f"Unknown job type: {job.job_type}")
    return await handler(job)
