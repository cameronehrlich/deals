"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Search,
  Building,
  Radio,
  ExternalLink,
  Bookmark,
  Database,
  TrendingUp,
  Trash2,
  Star,
  BarChart3,
  ArrowUpDown,
  ChevronDown,
} from "lucide-react";
import { ImageCarousel } from "@/components/ImageCarousel";
import { api, PropertyListing, ApiUsage, SavedProperty } from "@/lib/api";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";

// Markets for live search (location format: "City, ST")
const LIVE_MARKETS = [
  "Phoenix, AZ",
  "Tampa, FL",
  "Austin, TX",
  "Miami, FL",
  "Indianapolis, IN",
  "Cleveland, OH",
  "Memphis, TN",
  "Birmingham, AL",
  "Kansas City, MO",
  "Houston, TX",
];

// Sort options for investment analysis
type SortOption = {
  value: string;
  label: string;
  sortFn: (a: PropertyListing, b: PropertyListing) => number;
};

const SORT_OPTIONS: SortOption[] = [
  {
    value: "price_asc",
    label: "Price: Low to High",
    sortFn: (a, b) => a.price - b.price,
  },
  {
    value: "price_desc",
    label: "Price: High to Low",
    sortFn: (a, b) => b.price - a.price,
  },
  {
    value: "price_sqft_asc",
    label: "$/sqft: Low to High",
    sortFn: (a, b) => (a.price_per_sqft || 999999) - (b.price_per_sqft || 999999),
  },
  {
    value: "price_sqft_desc",
    label: "$/sqft: High to Low",
    sortFn: (a, b) => (b.price_per_sqft || 0) - (a.price_per_sqft || 0),
  },
  {
    value: "beds_desc",
    label: "Bedrooms: Most First",
    sortFn: (a, b) => b.bedrooms - a.bedrooms,
  },
  {
    value: "beds_asc",
    label: "Bedrooms: Fewest First",
    sortFn: (a, b) => a.bedrooms - b.bedrooms,
  },
  {
    value: "sqft_desc",
    label: "Size: Largest First",
    sortFn: (a, b) => (b.sqft || 0) - (a.sqft || 0),
  },
  {
    value: "sqft_asc",
    label: "Size: Smallest First",
    sortFn: (a, b) => (a.sqft || 999999) - (b.sqft || 999999),
  },
  {
    value: "year_desc",
    label: "Year: Newest First",
    sortFn: (a, b) => (b.year_built || 0) - (a.year_built || 0),
  },
  {
    value: "year_asc",
    label: "Year: Oldest First",
    sortFn: (a, b) => (a.year_built || 9999) - (b.year_built || 9999),
  },
];

// Constants for pagination
const INITIAL_LOAD = 10;
const LOAD_MORE_COUNT = 10;
const MAX_RESULTS = 42; // API free tier max

// Property card for live listings
function LivePropertyCard({
  property,
  onAnalyze,
}: {
  property: PropertyListing;
  onAnalyze: () => void;
}) {
  return (
    <div className="card hover:shadow-lg transition-shadow">
      {/* Photo Carousel */}
      <div className="relative h-48 -mx-4 -mt-4 mb-4 bg-gray-100 rounded-t-lg overflow-hidden">
        <ImageCarousel
          images={property.photos || []}
          alt={property.address}
        />
        {/* Live badge */}
        <div className="absolute top-2 left-2 px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-full flex items-center gap-1 z-10">
          <Radio className="h-3 w-3" />
          Live
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {/* Price */}
        <div className="flex justify-between items-start">
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(property.price)}
            </p>
            {property.price_per_sqft && (
              <p className="text-sm text-gray-500">
                ${property.price_per_sqft.toFixed(0)}/sqft
              </p>
            )}
          </div>
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded capitalize">
            {property.property_type.replace(/_/g, " ")}
          </span>
        </div>

        {/* Address */}
        <div>
          <p className="font-medium text-gray-900">{property.address}</p>
          <p className="text-sm text-gray-500">
            {property.city}, {property.state} {property.zip_code}
          </p>
        </div>

        {/* Details */}
        <div className="flex gap-4 text-sm text-gray-600">
          <span>{property.bedrooms} bd</span>
          <span>{property.bathrooms} ba</span>
          {property.sqft && <span>{property.sqft.toLocaleString()} sqft</span>}
          {property.year_built && <span>Built {property.year_built}</span>}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t border-gray-100">
          {property.source_url && (
            <a
              href={property.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-outline text-sm flex-1 flex items-center justify-center gap-1"
            >
              <ExternalLink className="h-4 w-4" />
              View Listing
            </a>
          )}
          <button
            onClick={onAnalyze}
            className="btn-primary text-sm flex-1 flex items-center justify-center gap-1"
          >
            <TrendingUp className="h-4 w-4" />
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
}

// Saved property card
function SavedPropertyCard({
  property,
  onDelete,
  onToggleFavorite,
  onViewAnalysis,
}: {
  property: SavedProperty;
  onDelete: () => void;
  onToggleFavorite: () => void;
  onViewAnalysis: () => void;
}) {
  const getCashFlowColor = (value: number) => {
    if (value >= 200) return "text-green-600";
    if (value >= 0) return "text-amber-600";
    return "text-red-600";
  };

  return (
    <div className="card hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="badge-blue text-xs">{property.source || "saved"}</span>
            {property.is_favorite && (
              <Star className="h-4 w-4 text-yellow-500 fill-current" />
            )}
          </div>
          <h3 className="font-semibold text-gray-900">{property.address}</h3>
          <p className="text-sm text-gray-500">
            {property.city}, {property.state} {property.zip_code}
          </p>
        </div>
        {property.overall_score && (
          <ScoreGauge score={property.overall_score} label="Score" size="sm" />
        )}
      </div>

      {/* Price & Details */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-sm text-gray-500">List Price</p>
          <p className="font-bold text-lg">
            {property.list_price ? formatCurrency(property.list_price) : "N/A"}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Est. Rent</p>
          <p className="font-bold text-lg">
            {property.estimated_rent ? formatCurrency(property.estimated_rent) + "/mo" : "N/A"}
          </p>
        </div>
      </div>

      {/* Details */}
      <div className="flex gap-4 text-sm text-gray-600 mb-3">
        {property.bedrooms && <span>{property.bedrooms} bd</span>}
        {property.bathrooms && <span>{property.bathrooms} ba</span>}
        {property.sqft && <span>{property.sqft.toLocaleString()} sqft</span>}
      </div>

      {/* Metrics */}
      {(property.cash_flow !== undefined || property.cap_rate !== undefined) && (
        <div className="flex gap-4 text-sm bg-gray-50 px-3 py-2 rounded mb-3">
          {property.cash_flow !== undefined && (
            <div>
              <span className="text-gray-500">Cash Flow: </span>
              <span className={cn("font-semibold", getCashFlowColor(property.cash_flow))}>
                {formatCurrency(property.cash_flow)}/mo
              </span>
            </div>
          )}
          {property.cap_rate !== undefined && (
            <div>
              <span className="text-gray-500">Cap Rate: </span>
              <span className="font-semibold">{formatPercent(property.cap_rate)}</span>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-3 border-t border-gray-100">
        <button
          onClick={onViewAnalysis}
          className="btn-primary text-sm flex-1 flex items-center justify-center gap-1"
        >
          <BarChart3 className="h-4 w-4" />
          View Analysis
        </button>
        <button
          onClick={onToggleFavorite}
          className={cn(
            "btn-outline text-sm px-3",
            property.is_favorite && "text-yellow-600 border-yellow-300"
          )}
        >
          <Star className={cn("h-4 w-4", property.is_favorite && "fill-current")} />
        </button>
        <button
          onClick={onDelete}
          className="btn-outline text-sm px-3 text-red-600 border-red-200 hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

// Empty state for saved properties
function SavedPropertiesEmpty() {
  return (
    <div className="card text-center py-16 animate-fade-in">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-6">
        <Bookmark className="h-8 w-8 text-primary-600" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">No Saved Properties</h3>
      <p className="text-gray-500 max-w-md mx-auto mb-6">
        Analyze properties and save them to track and compare your favorite deals.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <a href="/import" className="btn-primary inline-flex items-center gap-2">
          <BarChart3 className="h-4 w-4" />
          Analyze a Property
        </a>
      </div>
    </div>
  );
}

function DealsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Data mode: "live" (real listings) or "saved"
  const [dataMode, setDataMode] = useState<"live" | "saved">("live");

  // Live properties state
  const [allProperties, setAllProperties] = useState<PropertyListing[]>([]); // Full results from API
  const [displayCount, setDisplayCount] = useState(INITIAL_LOAD); // How many to show
  const [apiUsage, setApiUsage] = useState<ApiUsage | null>(null);
  const [sortBy, setSortBy] = useState<string>("price_asc");

  // Saved properties state
  const [savedProperties, setSavedProperties] = useState<SavedProperty[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(false);

  // Common state
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters - Live
  const [maxPrice, setMaxPrice] = useState<string>("400000");
  const [minBeds, setMinBeds] = useState("2");
  const [selectedLocation, setSelectedLocation] = useState(LIVE_MARKETS[0]);

  // Get sorted and paginated properties
  const sortedProperties = [...allProperties].sort(
    SORT_OPTIONS.find(opt => opt.value === sortBy)?.sortFn || ((a, b) => a.price - b.price)
  );
  const displayedProperties = sortedProperties.slice(0, displayCount);
  const hasMore = displayCount < allProperties.length;
  const canLoadMoreFromApi = allProperties.length < MAX_RESULTS && apiUsage?.requests_remaining && apiUsage.requests_remaining > 0;

  // Search live properties
  const searchLiveProperties = useCallback(async (append = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setSearching(true);
        setDisplayCount(INITIAL_LOAD);
      }
      setError(null);

      const currentCount = append ? allProperties.length : 0;
      const limit = append ? LOAD_MORE_COUNT : INITIAL_LOAD;

      const res = await api.searchLiveProperties({
        location: selectedLocation,
        max_price: maxPrice ? parseInt(maxPrice) : undefined,
        min_beds: minBeds ? parseInt(minBeds) : undefined,
        limit: Math.min(currentCount + limit, MAX_RESULTS),
      });

      if (append) {
        // Only add new properties we don't already have
        const existingIds = new Set(allProperties.map(p => p.property_id));
        const newProperties = res.properties.filter(p => !existingIds.has(p.property_id));
        setAllProperties(prev => [...prev, ...newProperties]);
        setDisplayCount(prev => prev + newProperties.length);
      } else {
        setAllProperties(res.properties);
      }

      setApiUsage(res.api_usage);

      if (res.properties.length === 0 && res.api_usage.warning === "limit_reached") {
        setError("API limit reached. Use Calculator for manual analysis.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
      setLoadingMore(false);
      setLoading(false);
    }
  }, [selectedLocation, maxPrice, minBeds, allProperties]);

  // Load more results (show more from cache or fetch from API)
  const handleLoadMore = useCallback(() => {
    if (hasMore) {
      // Show more from already fetched results
      setDisplayCount(prev => Math.min(prev + LOAD_MORE_COUNT, allProperties.length));
    } else if (canLoadMoreFromApi) {
      // Fetch more from API
      searchLiveProperties(true);
    }
  }, [hasMore, canLoadMoreFromApi, searchLiveProperties, allProperties.length]);

  // Analyze a property - navigate to analyze page with property data
  const handleAnalyze = (property: PropertyListing) => {
    // Encode property data in URL and navigate to analyze page
    const propertyData = encodeURIComponent(JSON.stringify(property));
    router.push(`/import?property=${propertyData}`);
  };

  // Fetch saved properties
  const fetchSavedProperties = useCallback(async () => {
    try {
      setLoadingSaved(true);
      setError(null);
      const properties = await api.getSavedProperties({ limit: 50 });
      setSavedProperties(properties);
    } catch (err) {
      console.error("Failed to fetch saved properties:", err);
      setSavedProperties([]);
    } finally {
      setLoadingSaved(false);
      setLoading(false);
    }
  }, []);

  // Handle delete saved property
  const handleDeleteProperty = async (propertyId: string) => {
    try {
      await api.deleteSavedProperty(propertyId);
      setSavedProperties(prev => prev.filter(p => p.id !== propertyId));
    } catch (err) {
      console.error("Failed to delete property:", err);
    }
  };

  // Handle toggle favorite
  const handleToggleFavorite = async (propertyId: string) => {
    try {
      const updated = await api.togglePropertyFavorite(propertyId);
      setSavedProperties(prev =>
        prev.map(p => p.id === propertyId ? updated : p)
      );
    } catch (err) {
      console.error("Failed to toggle favorite:", err);
    }
  };

  // View analysis for saved property
  const handleViewSavedAnalysis = async (propertyId: string) => {
    // Navigate to saved property detail (could be expanded later)
    const property = savedProperties.find(p => p.id === propertyId);
    if (property) {
      // For now, open in analyze page with property data
      const propertyData = encodeURIComponent(JSON.stringify({
        address: property.address,
        city: property.city,
        state: property.state,
        zip_code: property.zip_code,
        price: property.list_price,
        bedrooms: property.bedrooms,
        bathrooms: property.bathrooms,
        sqft: property.sqft,
        property_type: property.property_type,
        source: property.source,
        source_url: property.source_url,
      }));
      router.push(`/import?property=${propertyData}`);
    }
  };

  // Initial fetch based on mode
  useEffect(() => {
    if (dataMode === "live") {
      setLoading(true);
      searchLiveProperties();
    } else {
      setLoading(true);
      fetchSavedProperties();
    }
  }, [dataMode]);

  // Handle search button click
  const handleSearch = () => {
    searchLiveProperties();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Find Deals</h1>
          <p className="text-gray-500 mt-1">
            Search and analyze investment properties
          </p>
        </div>

        {/* Data Mode Toggle */}
        <div className="flex items-center gap-2 p-1 bg-gray-100 rounded-lg">
          <button
            onClick={() => setDataMode("live")}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2",
              dataMode === "live"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            )}
          >
            <Radio className="h-4 w-4 text-green-500" />
            Live Properties
          </button>
          <button
            onClick={() => setDataMode("saved")}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2",
              dataMode === "saved"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            )}
          >
            <Bookmark className="h-4 w-4" />
            Saved
          </button>
        </div>
      </div>

      {/* Saved Mode */}
      {dataMode === "saved" ? (
        loadingSaved || loading ? (
          <LoadingPage />
        ) : savedProperties.length === 0 ? (
          <SavedPropertiesEmpty />
        ) : (
          <div className="space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                {savedProperties.length} saved {savedProperties.length === 1 ? "property" : "properties"}
              </p>
              <div className="flex items-center gap-2 text-xs text-primary-600">
                <Database className="h-3 w-3" />
                <span>Saved to Database</span>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedProperties.map((property, index) => (
                <div
                  key={property.id}
                  className="animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <SavedPropertyCard
                    property={property}
                    onDelete={() => handleDeleteProperty(property.id)}
                    onToggleFavorite={() => handleToggleFavorite(property.id)}
                    onViewAnalysis={() => handleViewSavedAnalysis(property.id)}
                  />
                </div>
              ))}
            </div>
          </div>
        )
      ) : (
        <>
          {/* Search Controls */}
          <div className="card">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="label">Market</label>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="input"
                >
                  {LIVE_MARKETS.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>

              <div className="w-36">
                <label className="label">Max Price</label>
                <input
                  type="number"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  placeholder="Any"
                  className="input"
                />
              </div>

              <div className="w-32">
                <label className="label">Min Beds</label>
                <select
                  value={minBeds}
                  onChange={(e) => setMinBeds(e.target.value)}
                  className="input"
                >
                  <option value="1">1+</option>
                  <option value="2">2+</option>
                  <option value="3">3+</option>
                  <option value="4">4+</option>
                </select>
              </div>

              <button
                onClick={handleSearch}
                disabled={searching || (apiUsage?.warning === "limit_reached")}
                className="btn-primary flex items-center gap-2"
              >
                {searching ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Search
              </button>
            </div>

            {/* API Usage info */}
            {apiUsage && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Radio className="h-4 w-4 text-green-500" />
                    <span>Live data from {apiUsage.provider}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">API calls:</span>
                    <span className={cn(
                      "font-medium",
                      apiUsage.warning === "limit_reached" ? "text-red-600" :
                      apiUsage.warning === "approaching_limit" ? "text-amber-600" : "text-green-600"
                    )}>
                      {apiUsage.requests_remaining}/{apiUsage.requests_limit} remaining
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results */}
          {loading ? (
            <LoadingPage />
          ) : error ? (
            <div className="card text-center py-8">
              <p className="text-red-600">{error}</p>
              <button onClick={handleSearch} className="btn-primary mt-4">
                Try Again
              </button>
            </div>
          ) : allProperties.length === 0 ? (
            <div className="card text-center py-12 animate-fade-in">
              <Building className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No properties found</h3>
              <p className="text-gray-500 mt-1 max-w-md mx-auto">
                {apiUsage?.warning === "limit_reached"
                  ? "API limit reached. Use the Calculator for manual property analysis."
                  : "No active listings match your criteria. Try adjusting your filters."}
              </p>
              {apiUsage?.warning !== "limit_reached" && (
                <button onClick={handleSearch} className="btn-primary mt-4">
                  <Search className="h-4 w-4 inline mr-2" />
                  Try Again
                </button>
              )}
              <a href="/calculator" className="btn-outline mt-4 ml-2 inline-flex items-center gap-2">
                Use Calculator
              </a>
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {/* Results Header with Sort */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <p className="text-sm text-gray-500">
                    Showing {displayedProperties.length} of {allProperties.length} properties in {selectedLocation}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-green-600">
                    <Radio className="h-3 w-3" />
                    <span>Live</span>
                  </div>
                </div>

                {/* Sort Dropdown */}
                <div className="flex items-center gap-2">
                  <ArrowUpDown className="h-4 w-4 text-gray-400" />
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    {SORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Property Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {displayedProperties.map((property, index) => (
                  <div
                    key={property.property_id}
                    className="animate-slide-up"
                    style={{ animationDelay: `${Math.min(index, 5) * 50}ms` }}
                  >
                    <LivePropertyCard
                      property={property}
                      onAnalyze={() => handleAnalyze(property)}
                    />
                  </div>
                ))}
              </div>

              {/* Load More Button */}
              {(hasMore || canLoadMoreFromApi) && (
                <div className="flex justify-center pt-4">
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="btn-outline flex items-center gap-2 px-6"
                  >
                    {loadingMore ? (
                      <>
                        <LoadingSpinner size="sm" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        Load More
                        {hasMore && (
                          <span className="text-gray-400 text-sm">
                            ({allProperties.length - displayCount} more cached)
                          </span>
                        )}
                        {!hasMore && canLoadMoreFromApi && (
                          <span className="text-gray-400 text-sm">
                            (fetch from API)
                          </span>
                        )}
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* End of results indicator */}
              {!hasMore && !canLoadMoreFromApi && allProperties.length > 0 && (
                <p className="text-center text-sm text-gray-400 pt-4">
                  {allProperties.length >= MAX_RESULTS
                    ? `Showing maximum ${MAX_RESULTS} results`
                    : "All properties loaded"}
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function DealsPage() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <DealsContent />
    </Suspense>
  );
}
