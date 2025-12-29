"use client";

/**
 * Comparable Sales Panel
 *
 * Displays comparable sales (comps) for a property and shows
 * how the subject property's price compares to the market.
 */

import { useState, useEffect } from "react";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Home,
  DollarSign,
  Calendar,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  BarChart3,
} from "lucide-react";
import { api, CompsAnalysis, ComparableSale } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";

interface CompsPanelProps {
  propertyId: string;
  subjectPrice?: number | null;
  subjectSqft?: number;
}

function PricePositionBadge({ position, percentDiff }: { position: string; percentDiff?: number }) {
  const config = {
    below_market: {
      color: "bg-green-100 text-green-800 border-green-200",
      icon: TrendingDown,
      label: "Below Market",
    },
    above_market: {
      color: "bg-red-100 text-red-800 border-red-200",
      icon: TrendingUp,
      label: "Above Market",
    },
    at_market: {
      color: "bg-gray-100 text-gray-800 border-gray-200",
      icon: Minus,
      label: "At Market",
    },
    unknown: {
      color: "bg-gray-100 text-gray-500 border-gray-200",
      icon: Minus,
      label: "Unknown",
    },
  };

  const { color, icon: Icon, label } = config[position as keyof typeof config] || config.unknown;

  return (
    <div className={cn("inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-sm font-medium", color)}>
      <Icon className="h-4 w-4" />
      <span>{label}</span>
      {percentDiff !== undefined && percentDiff !== null && (
        <span className="ml-1">({percentDiff > 0 ? "+" : ""}{percentDiff.toFixed(1)}%)</span>
      )}
    </div>
  );
}

function CompCard({ comp }: { comp: ComparableSale }) {
  const soldDate = comp.sold_date ? new Date(comp.sold_date).toLocaleDateString() : "N/A";

  return (
    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex justify-between items-start mb-2">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">{comp.address}</p>
          <p className="text-sm text-gray-500">{comp.city}, {comp.state} {comp.zip_code}</p>
        </div>
        <div className="text-right ml-4">
          <p className="font-bold text-lg text-primary-600">{formatCurrency(comp.sold_price)}</p>
          {comp.price_per_sqft && (
            <p className="text-sm text-gray-500">${comp.price_per_sqft.toFixed(0)}/sqft</p>
          )}
        </div>
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
        <span>{comp.bedrooms} bed</span>
        <span>{comp.bathrooms} bath</span>
        {comp.sqft && <span>{comp.sqft.toLocaleString()} sqft</span>}
        <span className="flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          Sold {soldDate}
        </span>
        {comp.days_on_market && (
          <span>{comp.days_on_market} DOM</span>
        )}
      </div>
    </div>
  );
}

export function CompsPanel({ propertyId, subjectPrice, subjectSqft }: CompsPanelProps) {
  const [comps, setComps] = useState<CompsAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const fetchComps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCompsForProperty(propertyId, 20);
      setComps(data);
      if (data.comp_count > 0) {
        setExpanded(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load comps");
    } finally {
      setLoading(false);
    }
  };

  // Don't auto-fetch - let user trigger it to save API calls
  const hasComps = comps && comps.comp_count > 0;
  const displayedComps = showAll ? comps?.comparables : comps?.comparables.slice(0, 5);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-primary-600" />
          Comparable Sales
        </h3>
        {!comps && !loading && (
          <button
            onClick={fetchComps}
            className="btn-outline text-sm py-1.5 px-3 flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Load Comps
          </button>
        )}
        {hasComps && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary-600 mr-2" />
          <span className="text-gray-600">Loading comparable sales...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
          <button
            onClick={fetchComps}
            className="text-red-600 hover:text-red-800 text-sm mt-2 flex items-center gap-1"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
        </div>
      )}

      {!loading && !comps && !error && (
        <div className="text-center py-6 text-gray-500">
          <Home className="h-10 w-10 mx-auto mb-2 text-gray-300" />
          <p>Click "Load Comps" to see recent sales in this area</p>
          <p className="text-sm mt-1">Uses 1 API request</p>
        </div>
      )}

      {hasComps && expanded && (
        <div className="space-y-4">
          {/* Market Position Summary */}
          <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-500">Your Price Position</p>
              <PricePositionBadge
                position={comps.price_position}
                percentDiff={comps.price_vs_median}
              />
            </div>
            <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-500">Comps Found</p>
                <p className="font-bold text-lg">{comps.comp_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Median Price</p>
                <p className="font-bold text-lg">{comps.median_sold_price ? formatCurrency(comps.median_sold_price) : "N/A"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Median $/sqft</p>
                <p className="font-bold text-lg">{comps.median_price_per_sqft ? `$${comps.median_price_per_sqft.toFixed(0)}` : "N/A"}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Price Range</p>
                <p className="font-bold text-sm">
                  {comps.min_sold_price && comps.max_sold_price
                    ? `${formatCurrency(comps.min_sold_price)} - ${formatCurrency(comps.max_sold_price)}`
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Subject vs Market Comparison */}
          {subjectSqft && comps.median_price_per_sqft && (
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 border rounded-lg">
                <p className="text-sm text-gray-500 mb-1">Your $/sqft</p>
                <p className="text-2xl font-bold text-primary-600">
                  ${comps.subject_price_per_sqft?.toFixed(0) || "N/A"}
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <p className="text-sm text-gray-500 mb-1">Market Median $/sqft</p>
                <p className="text-2xl font-bold text-gray-700">
                  ${comps.median_price_per_sqft.toFixed(0)}
                </p>
                {comps.price_vs_median_psf !== undefined && (
                  <p className={cn(
                    "text-sm",
                    comps.price_vs_median_psf < 0 ? "text-green-600" : comps.price_vs_median_psf > 0 ? "text-red-600" : "text-gray-500"
                  )}>
                    {comps.price_vs_median_psf > 0 ? "+" : ""}{comps.price_vs_median_psf.toFixed(1)}% vs market
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Comparable Sales List */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900">Recent Sales</h4>
              <button
                onClick={fetchComps}
                className="text-primary-600 hover:text-primary-700 text-sm flex items-center gap-1"
              >
                <RefreshCw className="h-3 w-3" />
                Refresh
              </button>
            </div>
            <div className="space-y-3">
              {displayedComps?.map((comp) => (
                <CompCard key={comp.property_id} comp={comp} />
              ))}
            </div>
            {comps.comparables.length > 5 && (
              <button
                onClick={() => setShowAll(!showAll)}
                className="w-full mt-3 py-2 text-sm text-primary-600 hover:text-primary-700 flex items-center justify-center gap-1"
              >
                {showAll ? (
                  <>
                    <ChevronUp className="h-4 w-4" />
                    Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" />
                    Show all {comps.comparables.length} comps
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {comps && comps.comp_count === 0 && (
        <div className="text-center py-6 text-gray-500">
          <Home className="h-10 w-10 mx-auto mb-2 text-gray-300" />
          <p>No comparable sales found</p>
          <p className="text-sm mt-1">Try expanding your search criteria</p>
        </div>
      )}
    </div>
  );
}
