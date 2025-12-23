"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Bookmark,
  Database,
  Trash2,
  Star,
  BarChart3,
  ExternalLink,
  Building,
  ArrowUpDown,
  Filter,
  X,
  ChevronDown,
} from "lucide-react";
import { api, SavedProperty } from "@/lib/api";
import { LoadingPage } from "@/components/LoadingSpinner";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";

// Sort options
type SortOption = "score_desc" | "price_asc" | "price_desc" | "cash_flow_desc" | "date_desc" | "city_asc";

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "score_desc", label: "Score (High to Low)" },
  { value: "cash_flow_desc", label: "Cash Flow (High to Low)" },
  { value: "price_asc", label: "Price (Low to High)" },
  { value: "price_desc", label: "Price (High to Low)" },
  { value: "date_desc", label: "Recently Saved" },
  { value: "city_asc", label: "City (A-Z)" },
];

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
        <a href="/deals" className="btn-outline inline-flex items-center gap-2">
          <Building className="h-4 w-4" />
          Find Properties
        </a>
      </div>
    </div>
  );
}

export default function SavedPage() {
  const router = useRouter();
  const [savedProperties, setSavedProperties] = useState<SavedProperty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Sort state
  const [sortBy, setSortBy] = useState<SortOption>("score_desc");
  const [filterCity, setFilterCity] = useState<string>("");
  const [filterFavoritesOnly, setFilterFavoritesOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Get unique cities from saved properties
  const uniqueCities = useMemo(() => {
    const cities = new Set(savedProperties.map(p => `${p.city}, ${p.state}`));
    return Array.from(cities).sort();
  }, [savedProperties]);

  // Filter and sort properties
  const filteredAndSortedProperties = useMemo(() => {
    let result = [...savedProperties];

    // Apply filters
    if (filterCity) {
      result = result.filter(p => `${p.city}, ${p.state}` === filterCity);
    }
    if (filterFavoritesOnly) {
      result = result.filter(p => p.is_favorite);
    }

    // Apply sort
    result.sort((a, b) => {
      switch (sortBy) {
        case "score_desc":
          return (b.overall_score || 0) - (a.overall_score || 0);
        case "price_asc":
          return (a.list_price || 0) - (b.list_price || 0);
        case "price_desc":
          return (b.list_price || 0) - (a.list_price || 0);
        case "cash_flow_desc":
          return (b.cash_flow || 0) - (a.cash_flow || 0);
        case "date_desc":
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case "city_asc":
          return `${a.city}, ${a.state}`.localeCompare(`${b.city}, ${b.state}`);
        default:
          return 0;
      }
    });

    return result;
  }, [savedProperties, sortBy, filterCity, filterFavoritesOnly]);

  // Active filter count
  const activeFilterCount = (filterCity ? 1 : 0) + (filterFavoritesOnly ? 1 : 0);

  // Clear all filters
  const clearFilters = () => {
    setFilterCity("");
    setFilterFavoritesOnly(false);
  };

  // Fetch saved properties
  const fetchSavedProperties = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const properties = await api.getSavedProperties({ limit: 50 });
      setSavedProperties(properties);
    } catch (err) {
      console.error("Failed to fetch saved properties:", err);
      setError(err instanceof Error ? err.message : "Failed to load saved properties");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSavedProperties();
  }, [fetchSavedProperties]);

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

  // View analysis for saved property - load from database
  const handleViewSavedAnalysis = (propertyId: string) => {
    // Navigate to saved property detail page with ID
    router.push(`/saved/${propertyId}`);
  };

  if (loading) {
    return <LoadingPage />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Saved Properties</h1>
          <p className="text-gray-500 mt-1">
            Your saved investment properties and analyses
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-primary-600">
          <Database className="h-4 w-4" />
          <span>Stored locally</span>
        </div>
      </div>

      {error && (
        <div className="card border-red-200 bg-red-50">
          <p className="text-red-700">{error}</p>
          <button onClick={fetchSavedProperties} className="btn-primary mt-3">
            Retry
          </button>
        </div>
      )}

      {savedProperties.length === 0 ? (
        <SavedPropertiesEmpty />
      ) : (
        <div className="space-y-4 animate-fade-in">
          {/* Sort & Filter Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <p className="text-sm text-gray-500">
              {filteredAndSortedProperties.length === savedProperties.length
                ? `${savedProperties.length} saved ${savedProperties.length === 1 ? "property" : "properties"}`
                : `Showing ${filteredAndSortedProperties.length} of ${savedProperties.length} properties`}
            </p>

            <div className="flex items-center gap-2">
              {/* Sort Dropdown */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="appearance-none bg-white border border-gray-300 rounded-lg px-3 py-2 pr-8 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent cursor-pointer"
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
              </div>

              {/* Filter Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={cn(
                  "btn-outline text-sm flex items-center gap-2",
                  showFilters && "bg-primary-50 border-primary-300"
                )}
              >
                <Filter className="h-4 w-4" />
                Filters
                {activeFilterCount > 0 && (
                  <span className="bg-primary-600 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="card bg-gray-50 p-4">
              <div className="flex flex-wrap items-center gap-4">
                {/* City Filter */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600">City:</label>
                  <select
                    value={filterCity}
                    onChange={(e) => setFilterCity(e.target.value)}
                    className="bg-white border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">All Cities</option>
                    {uniqueCities.map((city) => (
                      <option key={city} value={city}>
                        {city}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Favorites Only */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filterFavoritesOnly}
                    onChange={(e) => setFilterFavoritesOnly(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-600 flex items-center gap-1">
                    <Star className="h-4 w-4 text-yellow-500" />
                    Favorites only
                  </span>
                </label>

                {/* Clear Filters */}
                {activeFilterCount > 0 && (
                  <button
                    onClick={clearFilters}
                    className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1 ml-auto"
                  >
                    <X className="h-4 w-4" />
                    Clear filters
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Property Grid */}
          {filteredAndSortedProperties.length === 0 ? (
            <div className="card text-center py-12">
              <Filter className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No matching properties</h3>
              <p className="text-gray-500 mt-1">Try adjusting your filters</p>
              <button onClick={clearFilters} className="btn-primary mt-4">
                Clear Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAndSortedProperties.map((property, index) => (
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
          )}
        </div>
      )}
    </div>
  );
}
