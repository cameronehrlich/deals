"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.routes import markets, deals, analysis, import_property, properties, saved
from api.models import HealthResponse
from src.db import init_database, get_repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Real Estate Deal Platform API...")
    # Initialize database
    try:
        init_database()
        repo = get_repository()
        stats = await repo.get_stats()
        print(f"Database initialized: {stats['total_markets']} markets, {stats['total_saved_properties']} saved properties")
    except Exception as e:
        print(f"Database initialization warning: {e}")
    yield
    # Shutdown
    print("Shutting down API...")


app = FastAPI(
    title="Real Estate Deal Platform",
    description="API for sourcing, analyzing, and ranking real estate investment opportunities",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration - allow all origins for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
app.include_router(deals.router, prefix="/api/deals", tags=["Deals"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(import_property.router, prefix="/api/import", tags=["Import"])
app.include_router(properties.router, prefix="/api/properties", tags=["Properties"])
app.include_router(saved.router, prefix="/api/saved", tags=["Saved"])


@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="real-estate-deal-platform",
        version="1.0.0",
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """API health check."""
    return HealthResponse(
        status="healthy",
        service="real-estate-deal-platform",
        version="1.0.0",
    )
