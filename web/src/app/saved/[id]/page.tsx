"use client";

/**
 * Saved Property Detail Page (Enriched Tier)
 *
 * This page displays a saved property with full analysis data,
 * location insights, and user customizations. It uses the shared
 * PropertyAnalysisView component for consistent display across
 * the deal detail and saved property pages.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Star,
  Trash2,
  Database,
  Edit3,
  Save,
  X,
} from "lucide-react";
import { api, SavedProperty } from "@/lib/api";
import { cn, formatCurrency } from "@/lib/utils";
import { LoadingPage } from "@/components/LoadingSpinner";
import {
  PropertyAnalysisView,
  PropertyData,
  ScoreData,
  FinancialData,
  LocationData,
  MarketData,
} from "@/components/PropertyAnalysisView";

export default function SavedPropertyDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const propertyId = params.id;

  const [savedProperty, setSavedProperty] = useState<SavedProperty | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [locationLoading, setLocationLoading] = useState(false);

  // Notes editing
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesValue, setNotesValue] = useState("");

  // Fetch saved property and analysis
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [property, analysisData] = await Promise.all([
          api.getSavedProperty(propertyId),
          api.getSavedPropertyAnalysis(propertyId).catch(() => null),
        ]);

        setSavedProperty(property);
        setAnalysis(analysisData);
        setNotesValue(property.notes || "");
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

  // Handle refresh location data
  const handleRefreshLocation = async () => {
    if (!savedProperty) return;
    try {
      setLocationLoading(true);
      const updated = await api.refreshPropertyLocationData(savedProperty.id);
      setSavedProperty(updated);
    } catch (err) {
      console.error("Failed to refresh location data:", err);
    } finally {
      setLocationLoading(false);
    }
  };

  // Handle reanalyze
  const handleReanalyze = async () => {
    if (!savedProperty) return;
    try {
      const updated = await api.reanalyzeProperty(savedProperty.id);
      setSavedProperty(updated);
      // Refresh analysis data too
      const newAnalysis = await api.getSavedPropertyAnalysis(savedProperty.id).catch(() => null);
      setAnalysis(newAnalysis);
    } catch (err) {
      console.error("Failed to reanalyze property:", err);
    }
  };

  // Handle save notes
  const handleSaveNotes = async () => {
    if (!savedProperty) return;
    try {
      const updated = await api.updateSavedProperty(savedProperty.id, {
        note: notesValue,
      });
      setSavedProperty(updated);
      setEditingNotes(false);
    } catch (err) {
      console.error("Failed to save notes:", err);
    }
  };

  if (loading) {
    return <LoadingPage />;
  }

  if (error || !savedProperty) {
    return (
      <div className="space-y-6">
        <Link
          href="/saved"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Saved Properties
        </Link>
        <div className="card border-red-200 bg-red-50 text-center py-8">
          <p className="text-red-700">{error || "Property not found"}</p>
          <Link href="/saved" className="btn-primary mt-4 inline-block">
            Go Back
          </Link>
        </div>
      </div>
    );
  }

  // Build data for PropertyAnalysisView from saved property + analysis
  const propertyData: PropertyData = {
    id: savedProperty.id,
    address: savedProperty.address,
    city: savedProperty.city,
    state: savedProperty.state,
    zip_code: savedProperty.zip_code,
    latitude: savedProperty.latitude,
    longitude: savedProperty.longitude,
    list_price: savedProperty.list_price,
    estimated_rent: savedProperty.estimated_rent,
    bedrooms: savedProperty.bedrooms,
    bathrooms: savedProperty.bathrooms,
    sqft: savedProperty.sqft,
    property_type: savedProperty.property_type,
    year_built: savedProperty.year_built,
    days_on_market: savedProperty.days_on_market,
    source: savedProperty.source,
    source_url: savedProperty.source_url,
    features: analysis?.property?.features,
  };

  const scoreData: ScoreData = {
    overall_score: savedProperty.overall_score,
    financial_score: savedProperty.financial_score,
    market_score: savedProperty.market_score,
    risk_score: savedProperty.risk_score,
    liquidity_score: savedProperty.liquidity_score,
  };

  // Build financial data from analysis or saved property
  const analysisFinancials = analysis?.financials || {};
  const financialData: FinancialData = {
    purchase_price: analysisFinancials.purchase_price || savedProperty.list_price,
    monthly_cash_flow: analysisFinancials.monthly_cash_flow || savedProperty.cash_flow,
    annual_cash_flow: analysisFinancials.annual_cash_flow || (savedProperty.cash_flow ? savedProperty.cash_flow * 12 : undefined),
    cash_on_cash_return: analysisFinancials.cash_on_cash_return || savedProperty.cash_on_cash,
    cap_rate: analysisFinancials.cap_rate || savedProperty.cap_rate,
    rent_to_price: analysisFinancials.rent_to_price,
    total_cash_invested: analysisFinancials.total_cash_invested,
    gross_rent_multiplier: analysisFinancials.gross_rent_multiplier,
    break_even_occupancy: analysisFinancials.break_even_occupancy,
    dscr: analysisFinancials.dscr,
    net_operating_income: analysisFinancials.net_operating_income,
    // Expense breakdown
    monthly_mortgage: analysisFinancials.monthly_mortgage,
    property_taxes: analysisFinancials.property_taxes,
    insurance: analysisFinancials.insurance,
    hoa: analysisFinancials.hoa,
    maintenance: analysisFinancials.maintenance,
    capex: analysisFinancials.capex,
    vacancy: analysisFinancials.vacancy,
    property_management: analysisFinancials.property_management,
    // Loan details
    down_payment: analysisFinancials.loan?.down_payment || analysisFinancials.down_payment,
    down_payment_pct: analysisFinancials.loan?.down_payment_pct,
    loan_amount: analysisFinancials.loan?.loan_amount || analysisFinancials.loan_amount,
    interest_rate: analysisFinancials.loan?.interest_rate,
    closing_costs: analysisFinancials.closing_costs,
  };

  // Use cached location data from saved property
  const locationData: LocationData | undefined = savedProperty.location_data;

  // Market data
  const marketData: MarketData | undefined = analysis?.market
    ? {
        id: analysis.market.id,
        name: analysis.market.name,
        state: analysis.market.state,
        metro: analysis.market.metro,
        overall_score: analysis.market.overall_score,
        cash_flow_score: analysis.market.cash_flow_score,
        growth_score: analysis.market.growth_score,
      }
    : undefined;

  const pros = analysis?.pros || [];
  const cons = analysis?.cons || [];
  const redFlags = analysis?.red_flags || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <Link
          href="/saved"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Saved Properties
        </Link>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-primary-600">
            <Database className="h-4 w-4" />
            <span>Saved Property</span>
            {savedProperty.last_analyzed && (
              <span className="text-gray-400">
                | Analyzed {new Date(savedProperty.last_analyzed).toLocaleDateString()}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleToggleFavorite}
              className={cn(
                "btn-outline text-sm flex items-center gap-1",
                savedProperty.is_favorite && "text-yellow-600 border-yellow-300"
              )}
            >
              <Star
                className={cn("h-4 w-4", savedProperty.is_favorite && "fill-current")}
              />
              {savedProperty.is_favorite ? "Favorited" : "Favorite"}
            </button>
            <button
              onClick={handleDelete}
              className="btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50 flex items-center gap-1"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Main Property Analysis View */}
      <PropertyAnalysisView
        property={propertyData}
        scores={scoreData}
        financials={financialData}
        locationData={locationData}
        market={marketData}
        pros={pros}
        cons={cons}
        redFlags={redFlags}
        locationLoading={locationLoading}
        onRefreshLocation={savedProperty.latitude && savedProperty.longitude ? handleRefreshLocation : undefined}
        onReanalyze={handleReanalyze}
        customScenarios={savedProperty.custom_scenarios}
        showReanalyzeButton={true}
        isSavedProperty={true}
      />

      {/* Notes Section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Edit3 className="h-5 w-5 text-primary-600" />
            Notes
          </h3>
          {!editingNotes ? (
            <button
              onClick={() => setEditingNotes(true)}
              className="btn-outline text-sm"
            >
              Edit Notes
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setNotesValue(savedProperty.notes || "");
                  setEditingNotes(false);
                }}
                className="btn-outline text-sm flex items-center gap-1"
              >
                <X className="h-4 w-4" />
                Cancel
              </button>
              <button
                onClick={handleSaveNotes}
                className="btn-primary text-sm flex items-center gap-1"
              >
                <Save className="h-4 w-4" />
                Save
              </button>
            </div>
          )}
        </div>
        {editingNotes ? (
          <textarea
            value={notesValue}
            onChange={(e) => setNotesValue(e.target.value)}
            className="w-full border rounded-lg p-3 text-sm min-h-[120px] focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Add notes about this property..."
          />
        ) : (
          <p className="text-gray-600 whitespace-pre-wrap">
            {savedProperty.notes || (
              <span className="text-gray-400 italic">No notes yet. Click "Edit Notes" to add some.</span>
            )}
          </p>
        )}
      </div>

      {/* Property Metadata */}
      <div className="card bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Property Info</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Status</span>
            <p className="font-medium capitalize">{savedProperty.pipeline_status}</p>
          </div>
          <div>
            <span className="text-gray-500">Saved</span>
            <p className="font-medium">
              {new Date(savedProperty.created_at).toLocaleDateString()}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Last Updated</span>
            <p className="font-medium">
              {new Date(savedProperty.updated_at).toLocaleDateString()}
            </p>
          </div>
          {savedProperty.location_data_fetched && (
            <div>
              <span className="text-gray-500">Location Data</span>
              <p className="font-medium">
                {new Date(savedProperty.location_data_fetched).toLocaleDateString()}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
