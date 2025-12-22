"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  MapPin,
  Info,
  MinusCircle,
  Database,
  BarChart3,
  Star,
  Trash2,
  ExternalLink,
} from "lucide-react";
import { api, SavedProperty } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  getCashFlowColor,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingPage } from "@/components/LoadingSpinner";

interface DealAnalysis {
  id: string;
  property: {
    id: string;
    address: string;
    city: string;
    state: string;
    zip_code: string;
    list_price: number;
    estimated_rent?: number;
    bedrooms: number;
    bathrooms: number;
    sqft?: number;
    property_type: string;
    source?: string;
    source_url?: string;
  };
  financials?: {
    purchase_price: number;
    monthly_cash_flow: number;
    annual_cash_flow: number;
    cash_on_cash_return?: number;
    cap_rate?: number;
    rent_to_price?: number;
    total_cash_needed?: number;
    gross_rent_multiplier?: number;
    break_even_occupancy?: number;
    net_operating_income?: number;
  };
  score?: {
    overall_score: number;
    financial_score?: number;
    market_score?: number;
    risk_score?: number;
  };
  market?: {
    id: string;
    name: string;
    state: string;
    metro?: string;
    overall_score?: number;
  };
  pros: string[];
  cons: string[];
  red_flags?: string[];
  pipeline_status: string;
  is_favorite?: boolean;
}

export default function SavedPropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [propertyId, setPropertyId] = useState<string | null>(null);
  const [savedProperty, setSavedProperty] = useState<SavedProperty | null>(null);
  const [analysis, setAnalysis] = useState<DealAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Unwrap params
  useEffect(() => {
    params.then(p => setPropertyId(p.id));
  }, [params]);

  // Fetch saved property and analysis
  useEffect(() => {
    if (!propertyId) return;

    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        // Fetch both the property info and the cached analysis
        const [property, analysisData] = await Promise.all([
          api.getSavedProperty(propertyId!),
          api.getSavedPropertyAnalysis(propertyId!).catch(() => null),
        ]);

        setSavedProperty(property);
        setAnalysis(analysisData);
      } catch (err) {
        console.error("Failed to fetch saved property:", err);
        setError(err instanceof Error ? err.message : "Failed to load property");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [propertyId]);

  // Handle toggle favorite
  const handleToggleFavorite = async () => {
    if (!savedProperty) return;
    try {
      const updated = await api.togglePropertyFavorite(savedProperty.id);
      setSavedProperty(updated);
    } catch (err) {
      console.error("Failed to toggle favorite:", err);
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!savedProperty) return;
    if (!confirm("Are you sure you want to delete this saved property?")) return;

    try {
      await api.deleteSavedProperty(savedProperty.id);
      router.push("/saved");
    } catch (err) {
      console.error("Failed to delete property:", err);
    }
  };

  // Calculate display values from analysis or saved property
  const displayData = useMemo(() => {
    if (analysis) {
      return {
        address: analysis.property.address,
        city: analysis.property.city,
        state: analysis.property.state,
        zip_code: analysis.property.zip_code,
        list_price: analysis.property.list_price,
        estimated_rent: analysis.property.estimated_rent,
        bedrooms: analysis.property.bedrooms,
        bathrooms: analysis.property.bathrooms,
        sqft: analysis.property.sqft,
        property_type: analysis.property.property_type,
        source: analysis.property.source,
        source_url: analysis.property.source_url,
        overall_score: analysis.score?.overall_score,
        monthly_cash_flow: analysis.financials?.monthly_cash_flow,
        annual_cash_flow: analysis.financials?.annual_cash_flow,
        cash_on_cash: analysis.financials?.cash_on_cash_return,
        cap_rate: analysis.financials?.cap_rate,
        rent_to_price: analysis.financials?.rent_to_price,
        total_cash_needed: analysis.financials?.total_cash_needed,
        grm: analysis.financials?.gross_rent_multiplier,
        break_even_occupancy: analysis.financials?.break_even_occupancy,
        pros: analysis.pros || [],
        cons: analysis.cons || [],
        market: analysis.market,
      };
    } else if (savedProperty) {
      return {
        address: savedProperty.address,
        city: savedProperty.city,
        state: savedProperty.state,
        zip_code: savedProperty.zip_code,
        list_price: savedProperty.list_price,
        estimated_rent: savedProperty.estimated_rent,
        bedrooms: savedProperty.bedrooms,
        bathrooms: savedProperty.bathrooms,
        sqft: savedProperty.sqft,
        property_type: savedProperty.property_type,
        source: savedProperty.source,
        source_url: savedProperty.source_url,
        overall_score: savedProperty.overall_score,
        monthly_cash_flow: savedProperty.cash_flow,
        annual_cash_flow: savedProperty.cash_flow ? savedProperty.cash_flow * 12 : undefined,
        cash_on_cash: savedProperty.cash_on_cash,
        cap_rate: savedProperty.cap_rate,
        rent_to_price: undefined,
        total_cash_needed: undefined,
        grm: undefined,
        break_even_occupancy: undefined,
        pros: [],
        cons: [],
        market: undefined,
      };
    }
    return null;
  }, [analysis, savedProperty]);

  if (loading) {
    return <LoadingPage />;
  }

  if (error || !displayData) {
    return (
      <div className="space-y-6">
        <Link href="/saved" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" />
          Back to Saved Properties
        </Link>
        <div className="card border-red-200 bg-red-50 text-center py-8">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-3" />
          <p className="text-red-700">{error || "Property not found"}</p>
          <Link href="/saved" className="btn-primary mt-4 inline-block">
            Go Back
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link href="/saved" className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" />
          Back to Saved Properties
        </Link>
        <div className="flex items-center gap-2 text-sm text-primary-600">
          <Database className="h-4 w-4" />
          <span>Loaded from cache</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Property Overview */}
          <div className="card">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                  <span className="badge-blue">{displayData.source || "saved"}</span>
                  <span>{displayData.property_type?.replace(/_/g, ' ')}</span>
                  {savedProperty?.is_favorite && (
                    <Star className="h-4 w-4 text-yellow-500 fill-current" />
                  )}
                </div>
                <h2 className="text-xl font-bold text-gray-900">
                  {displayData.address}
                </h2>
                <p className="text-gray-600 flex items-center gap-1 mt-1">
                  <MapPin className="h-4 w-4" />
                  {displayData.city}, {displayData.state} {displayData.zip_code}
                </p>
              </div>
              {displayData.overall_score && (
                <ScoreGauge score={displayData.overall_score} label="Deal Score" size="md" />
              )}
            </div>

            {/* Property Details */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t">
              <div>
                <p className="text-sm text-gray-500">List Price</p>
                <p className="font-bold text-lg">
                  {displayData.list_price ? formatCurrency(displayData.list_price) : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  Est. Rent
                  <span
                    className="cursor-help"
                    title="Source: HUD Fair Market Rent (FMR)"
                  >
                    <Info className="h-3.5 w-3.5 text-gray-400 hover:text-gray-600" />
                  </span>
                </p>
                <p className="font-bold text-lg">
                  {displayData.estimated_rent
                    ? formatCurrency(displayData.estimated_rent) + '/mo'
                    : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Beds / Baths</p>
                <p className="font-bold text-lg">
                  {displayData.bedrooms || "?"} / {displayData.bathrooms || "?"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Sqft</p>
                <p className="font-bold text-lg">
                  {displayData.sqft?.toLocaleString() || 'N/A'}
                </p>
              </div>
            </div>
          </div>

          {/* Financial Metrics */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-primary-600" />
              Financial Analysis
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Monthly Cash Flow</p>
                <p className={cn(
                  "text-xl font-bold mt-1",
                  displayData.monthly_cash_flow !== undefined
                    ? getCashFlowColor(displayData.monthly_cash_flow)
                    : "text-gray-400"
                )}>
                  {displayData.monthly_cash_flow !== undefined
                    ? formatCurrency(displayData.monthly_cash_flow)
                    : "N/A"}
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Cash-on-Cash</p>
                <p className="text-xl font-bold mt-1">
                  {displayData.cash_on_cash !== undefined
                    ? formatPercent(displayData.cash_on_cash)
                    : "N/A"}
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Cap Rate</p>
                <p className="text-xl font-bold mt-1">
                  {displayData.cap_rate !== undefined
                    ? formatPercent(displayData.cap_rate)
                    : "N/A"}
                </p>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Rent-to-Price</p>
                <p className="text-xl font-bold mt-1">
                  {displayData.rent_to_price !== undefined
                    ? formatPercent(displayData.rent_to_price)
                    : displayData.list_price && displayData.estimated_rent
                      ? formatPercent(displayData.estimated_rent / displayData.list_price)
                      : "N/A"}
                </p>
              </div>
            </div>

            {(displayData.total_cash_needed || displayData.annual_cash_flow || displayData.grm || displayData.break_even_occupancy) && (
              <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                {displayData.total_cash_needed && (
                  <div>
                    <p className="text-sm text-gray-500">Total Cash Needed</p>
                    <p className="font-semibold">
                      {formatCurrency(displayData.total_cash_needed)}
                    </p>
                  </div>
                )}
                {displayData.annual_cash_flow !== undefined && (
                  <div>
                    <p className="text-sm text-gray-500">Annual Cash Flow</p>
                    <p className={cn(
                      "font-semibold",
                      getCashFlowColor(displayData.annual_cash_flow)
                    )}>
                      {formatCurrency(displayData.annual_cash_flow)}
                    </p>
                  </div>
                )}
                {displayData.grm && (
                  <div>
                    <p className="text-sm text-gray-500">GRM</p>
                    <p className="font-semibold">
                      {displayData.grm.toFixed(1)}
                    </p>
                  </div>
                )}
                {displayData.break_even_occupancy && (
                  <div>
                    <p className="text-sm text-gray-500">Break-even Occupancy</p>
                    <p className="font-semibold">
                      {formatPercent(displayData.break_even_occupancy)}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Pros and Cons */}
          {(displayData.pros.length > 0 || displayData.cons.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Pros */}
              <div className={cn(
                "card",
                displayData.pros.length > 0 ? "border-green-200" : "border-gray-200"
              )}>
                <h3 className={cn(
                  "font-semibold mb-3 flex items-center gap-2",
                  displayData.pros.length > 0 ? "text-green-800" : "text-gray-400"
                )}>
                  <CheckCircle className="h-5 w-5" />
                  Pros
                </h3>
                {displayData.pros.length > 0 ? (
                  <ul className="space-y-2">
                    {displayData.pros.map((pro, i) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                        {pro}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-400 italic">No standout pros identified</p>
                )}
              </div>

              {/* Cons */}
              <div className={cn(
                "card",
                displayData.cons.length > 0 ? "border-red-200" : "border-gray-200"
              )}>
                <h3 className={cn(
                  "font-semibold mb-3 flex items-center gap-2",
                  displayData.cons.length > 0 ? "text-red-800" : "text-gray-400"
                )}>
                  {displayData.cons.length > 0 ? (
                    <AlertTriangle className="h-5 w-5" />
                  ) : (
                    <MinusCircle className="h-5 w-5" />
                  )}
                  Cons
                </h3>
                {displayData.cons.length > 0 ? (
                  <ul className="space-y-2">
                    {displayData.cons.map((con, i) => (
                      <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                        {con}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-400 italic">No significant cons identified</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              {displayData.source_url && (
                <a
                  href={displayData.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-outline w-full flex items-center justify-center gap-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  View Original Listing
                </a>
              )}
              <button
                onClick={handleToggleFavorite}
                className={cn(
                  "btn-outline w-full flex items-center justify-center gap-2",
                  savedProperty?.is_favorite && "text-yellow-600 border-yellow-300"
                )}
              >
                <Star className={cn("h-4 w-4", savedProperty?.is_favorite && "fill-current")} />
                {savedProperty?.is_favorite ? "Remove from Favorites" : "Add to Favorites"}
              </button>
              <button
                onClick={handleDelete}
                className="btn-outline w-full flex items-center justify-center gap-2 text-red-600 border-red-200 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
                Delete Property
              </button>
            </div>
          </div>

          {/* Market Info */}
          {displayData.market && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary-600" />
                Market
              </h3>
              <div className="space-y-2">
                <p className="font-medium">{displayData.market.name}, {displayData.market.state}</p>
                {displayData.market.metro && (
                  <p className="text-sm text-gray-500">{displayData.market.metro}</p>
                )}
                {displayData.market.overall_score && (
                  <div className="mt-3">
                    <ScoreGauge score={displayData.market.overall_score} label="Market Score" size="sm" />
                  </div>
                )}
                <Link
                  href={`/markets/${displayData.market.id}`}
                  className="text-sm text-primary-600 hover:text-primary-700 inline-flex items-center gap-1 mt-2"
                >
                  View Market Details
                  <ArrowLeft className="h-3 w-3 rotate-180" />
                </Link>
              </div>
            </div>
          )}

          {/* Property Notes */}
          {savedProperty?.notes && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Notes</h3>
              <p className="text-sm text-gray-600 whitespace-pre-wrap">{savedProperty.notes}</p>
            </div>
          )}

          {/* Metadata */}
          <div className="card bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Property Info</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <span className="font-medium capitalize">{savedProperty?.pipeline_status || "analyzed"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Saved</span>
                <span className="font-medium">
                  {savedProperty?.created_at
                    ? new Date(savedProperty.created_at).toLocaleDateString()
                    : "N/A"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Updated</span>
                <span className="font-medium">
                  {savedProperty?.updated_at
                    ? new Date(savedProperty.updated_at).toLocaleDateString()
                    : "N/A"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
