"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Search,
  Building,
  Radio,
  ExternalLink,
  Image as ImageIcon,
  Bookmark,
  Database,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import { api, PropertyListing, ApiUsage } from "@/lib/api";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";
import { cn, formatCurrency } from "@/lib/utils";

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

// Income data cache
type IncomeData = {
  median_income: number;
  income_tier: string;
  affordable_rent: number;
};

// Property card for live listings
function LivePropertyCard({
  property,
  incomeData,
  onAnalyze,
}: {
  property: PropertyListing;
  incomeData?: IncomeData;
  onAnalyze: () => void;
}) {
  const hasPhoto = property.photos && property.photos.length > 0;

  // Income tier colors
  const tierColors: Record<string, string> = {
    high: "bg-green-100 text-green-700",
    middle: "bg-blue-100 text-blue-700",
    "low-middle": "bg-amber-100 text-amber-700",
    low: "bg-gray-100 text-gray-600",
  };

  return (
    <div className="card hover:shadow-lg transition-shadow">
      {/* Photo */}
      <div className="relative h-48 -mx-4 -mt-4 mb-4 bg-gray-100 rounded-t-lg overflow-hidden">
        {hasPhoto ? (
          <img
            src={property.photos[0]}
            alt={property.address}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <ImageIcon className="h-12 w-12" />
          </div>
        )}
        {/* Live badge */}
        <div className="absolute top-2 left-2 px-2 py-1 bg-green-500 text-white text-xs font-medium rounded-full flex items-center gap-1">
          <Radio className="h-3 w-3" />
          Live
        </div>
        {/* Income tier badge */}
        {incomeData && (
          <div className={cn(
            "absolute top-2 right-2 px-2 py-1 text-xs font-medium rounded flex items-center gap-1",
            tierColors[incomeData.income_tier] || "bg-gray-100 text-gray-600"
          )}>
            <DollarSign className="h-3 w-3" />
            ${Math.round(incomeData.median_income / 1000)}K
          </div>
        )}
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

        {/* Income insight */}
        {incomeData && (
          <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 px-2 py-1.5 rounded">
            <TrendingUp className="h-3 w-3" />
            <span>
              Area median: ${(incomeData.median_income).toLocaleString()}/yr
              {" "}|{" "}
              Affordable rent: ${incomeData.affordable_rent.toLocaleString()}/mo
            </span>
          </div>
        )}

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

// Coming Soon UI for Saved tab
function SavedComingSoon() {
  return (
    <div className="card text-center py-16 animate-fade-in">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-6">
        <Bookmark className="h-8 w-8 text-primary-600" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">Saved Properties</h3>
      <p className="text-gray-500 max-w-md mx-auto mb-6">
        Save properties from search results or imports to track and compare your favorite deals.
        This feature is coming soon with full database persistence.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-600">
          <Database className="h-4 w-4" />
          PostgreSQL integration planned
        </div>
      </div>
      <div className="mt-8 pt-8 border-t border-gray-200">
        <p className="text-sm text-gray-400 mb-4">In the meantime, you can:</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a href="/deals" className="btn-primary inline-flex items-center gap-2">
            <Search className="h-4 w-4" />
            Search Live Properties
          </a>
          <a href="/import" className="btn-outline inline-flex items-center gap-2">
            Import a Listing
          </a>
        </div>
      </div>
    </div>
  );
}

function DealsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Data mode: "live" (real listings) or "saved" (coming soon)
  const [dataMode, setDataMode] = useState<"live" | "saved">("live");

  // Live properties state
  const [liveProperties, setLiveProperties] = useState<PropertyListing[]>([]);
  const [apiUsage, setApiUsage] = useState<ApiUsage | null>(null);
  const [incomeByZip, setIncomeByZip] = useState<Record<string, IncomeData>>({});

  // Common state
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters - Live
  const [maxPrice, setMaxPrice] = useState<string>("400000");
  const [minBeds, setMinBeds] = useState("2");
  const [selectedLocation, setSelectedLocation] = useState(LIVE_MARKETS[0]);

  // Fetch income data for unique zip codes
  const fetchIncomeData = async (properties: PropertyListing[]) => {
    const uniqueZips = Array.from(new Set(properties.map(p => p.zip_code).filter(Boolean)));
    const newIncomeData: Record<string, IncomeData> = { ...incomeByZip };

    // Only fetch zips we don't have
    const zipsToFetch = uniqueZips.filter(zip => !incomeByZip[zip]);

    for (const zip of zipsToFetch.slice(0, 5)) { // Limit to 5 to save API calls
      try {
        const data = await api.getIncomeData(zip);
        newIncomeData[zip] = {
          median_income: data.median_income,
          income_tier: data.income_tier,
          affordable_rent: data.affordable_rent,
        };
      } catch (err) {
        // Income data not available for this zip
      }
    }

    setIncomeByZip(newIncomeData);
  };

  // Search live properties
  const searchLiveProperties = useCallback(async () => {
    try {
      setSearching(true);
      setError(null);

      const res = await api.searchLiveProperties({
        location: selectedLocation,
        max_price: maxPrice ? parseInt(maxPrice) : undefined,
        min_beds: minBeds ? parseInt(minBeds) : undefined,
        limit: 20,
      });

      setLiveProperties(res.properties);
      setApiUsage(res.api_usage);

      // Fetch income data for results
      if (res.properties.length > 0) {
        fetchIncomeData(res.properties);
      }

      if (res.properties.length === 0 && res.api_usage.warning === "limit_reached") {
        setError("API limit reached. Use Calculator for manual analysis.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
      setLoading(false);
    }
  }, [selectedLocation, maxPrice, minBeds]);

  // Analyze a property - navigate to analyze page with property data
  const handleAnalyze = (property: PropertyListing) => {
    // Encode property data in URL and navigate to analyze page
    const propertyData = encodeURIComponent(JSON.stringify(property));
    router.push(`/import?property=${propertyData}`);
  };

  // Initial search when in live mode
  useEffect(() => {
    if (dataMode === "live") {
      setLoading(true);
      searchLiveProperties();
    } else {
      setLoading(false);
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

      {/* Saved Mode - Coming Soon */}
      {dataMode === "saved" ? (
        <SavedComingSoon />
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
          ) : liveProperties.length === 0 ? (
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
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  {liveProperties.length} live properties in {selectedLocation}
                </p>
                <div className="flex items-center gap-2 text-xs text-green-600">
                  <Radio className="h-3 w-3" />
                  <span>Live Data</span>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {liveProperties.map((property, index) => (
                  <div
                    key={property.property_id}
                    className="animate-slide-up"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <LivePropertyCard
                      property={property}
                      incomeData={incomeByZip[property.zip_code]}
                      onAnalyze={() => handleAnalyze(property)}
                    />
                  </div>
                ))}
              </div>
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
