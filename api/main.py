"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from api.routes import markets, deals, analysis, import_property
from api.models import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Real Estate Deal Platform API...")
    yield
    # Shutdown
    print("Shutting down API...")


app = FastAPI(
    title="Real Estate Deal Platform",
    description="API for sourcing, analyzing, and ranking real estate investment opportunities",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
        "https://*.fly.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(markets.router, prefix="/api/markets", tags=["Markets"])
app.include_router(deals.router, prefix="/api/deals", tags=["Deals"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(import_property.router, prefix="/api/import", tags=["Import"])


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
