"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Bookmark,
  Database,
  Trash2,
  Star,
  BarChart3,
  ExternalLink,
  Building,
} from "lucide-react";
import { api, SavedProperty } from "@/lib/api";
import { LoadingPage } from "@/components/LoadingSpinner";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";

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
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {savedProperties.length} saved {savedProperties.length === 1 ? "property" : "properties"}
            </p>
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
      )}
    </div>
  );
}
