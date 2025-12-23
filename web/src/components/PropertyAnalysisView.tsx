"use client";

/**
 * Shared PropertyAnalysisView component.
 *
 * This component provides a unified view for property analysis across:
 * - Deal detail page (/deals/[id])
 * - Saved property detail page (/saved/[id])
 *
 * It displays all the enriched data from the "Tier 3: Enriched" property journey.
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  MapPin,
  Bed,
  Bath,
  Square,
  Calendar,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Home,
  Footprints,
  Train,
  Bike,
  Volume2,
  GraduationCap,
  Star,
  Droplets,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Calculator,
} from "lucide-react";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  getCashFlowColor,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";

// ==================== Types ====================

export interface PropertyData {
  id: string;
  address: string;
  city: string;
  state: string;
  zip_code?: string;
  latitude?: number;
  longitude?: number;
  list_price?: number;
  estimated_rent?: number;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  property_type?: string;
  year_built?: number;
  days_on_market?: number;
  source?: string;
  source_url?: string;
  features?: string[];
}

export interface ScoreData {
  overall_score?: number;
  financial_score?: number;
  market_score?: number;
  risk_score?: number;
  liquidity_score?: number;
}

export interface FinancialData {
  purchase_price?: number;
  monthly_cash_flow?: number;
  annual_cash_flow?: number;
  cash_on_cash_return?: number;
  cap_rate?: number;
  rent_to_price?: number;
  total_cash_invested?: number;
  gross_rent_multiplier?: number;
  break_even_occupancy?: number;
  dscr?: number;
  net_operating_income?: number;
  // Expense breakdown
  monthly_mortgage?: number;
  property_taxes?: number;
  insurance?: number;
  hoa?: number;
  maintenance?: number;
  capex?: number;
  vacancy?: number;
  property_management?: number;
  // Loan details
  down_payment?: number;
  down_payment_pct?: number;
  loan_amount?: number;
  interest_rate?: number;
  closing_costs?: number;
}

export interface LocationData {
  // Walk Score
  walk_score?: number;
  walk_description?: string;
  transit_score?: number;
  transit_description?: string;
  bike_score?: number;
  bike_description?: string;
  // Noise
  noise?: {
    noise_score?: number;
    description?: string;
    categories?: Record<string, number>;
  };
  // Schools
  schools?: Array<{
    name: string;
    rating?: number;
    distance_miles?: number;
    grades?: string;
    type?: string;
  }>;
  // Flood Zone
  flood_zone?: {
    zone?: string;
    risk_level?: string;
    description?: string;
    requires_insurance?: boolean;
    annual_chance?: string;
    base_flood_elevation?: number;
  };
}

export interface MarketData {
  id?: string;
  name?: string;
  state?: string;
  metro?: string;
  overall_score?: number;
  cash_flow_score?: number;
  growth_score?: number;
}

export interface AnalysisViewProps {
  property: PropertyData;
  scores?: ScoreData;
  financials?: FinancialData;
  locationData?: LocationData;
  market?: MarketData;
  pros?: string[];
  cons?: string[];
  redFlags?: string[];
  // Loading states
  locationLoading?: boolean;
  // Actions
  onRefreshLocation?: () => Promise<void>;
  onReanalyze?: () => Promise<void>;
  // Custom scenarios
  customScenarios?: Array<{
    name: string;
    offer_price: number;
    monthly_cash_flow: number;
    cash_on_cash: number;
    cap_rate: number;
    total_cash_needed: number;
  }>;
  // Feature flags
  showOfferSlider?: boolean;
  showReanalyzeButton?: boolean;
  isSavedProperty?: boolean;
}

// ==================== Component ====================

export function PropertyAnalysisView({
  property,
  scores,
  financials,
  locationData,
  market,
  pros = [],
  cons = [],
  redFlags = [],
  locationLoading = false,
  onRefreshLocation,
  onReanalyze,
  customScenarios,
  showOfferSlider = false,
  showReanalyzeButton = false,
  isSavedProperty = false,
}: AnalysisViewProps) {
  const [refreshing, setRefreshing] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);

  const handleRefreshLocation = async () => {
    if (!onRefreshLocation) return;
    setRefreshing(true);
    try {
      await onRefreshLocation();
    } finally {
      setRefreshing(false);
    }
  };

  const handleReanalyze = async () => {
    if (!onReanalyze) return;
    setReanalyzing(true);
    try {
      await onReanalyze();
    } finally {
      setReanalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Property Header */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <span className="badge-blue">{property.source || "import"}</span>
              <span>{property.property_type?.replace(/_/g, " ")}</span>
              {property.days_on_market !== undefined && (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {property.days_on_market} days
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-gray-900">{property.address}</h2>
            <p className="text-gray-600 flex items-center gap-1 mt-1">
              <MapPin className="h-4 w-4" />
              {property.city}, {property.state} {property.zip_code}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t">
              <div>
                <p className="text-sm text-gray-500">List Price</p>
                <p className="font-bold text-lg">
                  {property.list_price ? formatCurrency(property.list_price) : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Est. Rent</p>
                <p className="font-bold text-lg">
                  {property.estimated_rent
                    ? formatCurrency(property.estimated_rent) + "/mo"
                    : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Beds / Baths</p>
                <p className="font-bold text-lg flex items-center gap-2">
                  <Bed className="h-4 w-4 text-gray-400" />
                  {property.bedrooms || "?"} / {property.bathrooms || "?"}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Sqft</p>
                <p className="font-bold text-lg flex items-center gap-2">
                  <Square className="h-4 w-4 text-gray-400" />
                  {property.sqft?.toLocaleString() || "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Score Gauges */}
          {scores?.overall_score && (
            <div className="flex flex-wrap gap-4 justify-center lg:justify-end">
              <ScoreGauge score={scores.overall_score} label="Overall" size="md" />
              {scores.financial_score && (
                <ScoreGauge score={scores.financial_score} label="Financial" size="sm" />
              )}
              {scores.market_score && (
                <ScoreGauge score={scores.market_score} label="Market" size="sm" />
              )}
              {scores.risk_score && (
                <ScoreGauge score={100 - scores.risk_score} label="Safety" size="sm" />
              )}
            </div>
          )}
        </div>

        {/* Action buttons for saved properties */}
        {isSavedProperty && (showReanalyzeButton || onRefreshLocation) && (
          <div className="flex gap-2 mt-4 pt-4 border-t">
            {showReanalyzeButton && onReanalyze && (
              <button
                onClick={handleReanalyze}
                disabled={reanalyzing}
                className="btn-outline text-sm flex items-center gap-2"
              >
                <RefreshCw className={cn("h-4 w-4", reanalyzing && "animate-spin")} />
                {reanalyzing ? "Re-analyzing..." : "Re-analyze with Current Rates"}
              </button>
            )}
            {onRefreshLocation && (
              <button
                onClick={handleRefreshLocation}
                disabled={refreshing}
                className="btn-outline text-sm flex items-center gap-2"
              >
                <MapPin className={cn("h-4 w-4", refreshing && "animate-spin")} />
                {refreshing ? "Refreshing..." : "Refresh Location Data"}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Key Financial Metrics */}
      {financials && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-primary-600" />
            Key Returns
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Monthly Cash Flow</p>
              <p
                className={cn(
                  "text-xl font-bold mt-1",
                  financials.monthly_cash_flow !== undefined
                    ? getCashFlowColor(financials.monthly_cash_flow)
                    : "text-gray-400"
                )}
              >
                {financials.monthly_cash_flow !== undefined
                  ? formatCurrency(financials.monthly_cash_flow)
                  : "N/A"}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Annual Cash Flow</p>
              <p
                className={cn(
                  "text-xl font-bold mt-1",
                  financials.annual_cash_flow !== undefined
                    ? getCashFlowColor(financials.annual_cash_flow)
                    : "text-gray-400"
                )}
              >
                {financials.annual_cash_flow !== undefined
                  ? formatCurrency(financials.annual_cash_flow)
                  : "N/A"}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Cash-on-Cash</p>
              <p className="text-xl font-bold mt-1">
                {financials.cash_on_cash_return !== undefined
                  ? formatPercent(financials.cash_on_cash_return)
                  : "N/A"}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Cap Rate</p>
              <p className="text-xl font-bold mt-1">
                {financials.cap_rate !== undefined
                  ? formatPercent(financials.cap_rate)
                  : "N/A"}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">Rent-to-Price</p>
              <p className="text-xl font-bold mt-1">
                {financials.rent_to_price !== undefined
                  ? formatPercent(financials.rent_to_price)
                  : property.list_price && property.estimated_rent
                  ? formatPercent(property.estimated_rent / property.list_price)
                  : "N/A"}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">DSCR</p>
              <p className="text-xl font-bold mt-1">
                {financials.dscr !== undefined ? financials.dscr.toFixed(2) : "N/A"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Investment Summary */}
      {financials && (financials.purchase_price || financials.total_cash_invested) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Calculator className="h-5 w-5 text-primary-600" />
            Investment Summary
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {financials.purchase_price && (
              <div>
                <p className="text-sm text-gray-500">Purchase Price</p>
                <p className="font-semibold">{formatCurrency(financials.purchase_price)}</p>
              </div>
            )}
            {financials.down_payment && (
              <div>
                <p className="text-sm text-gray-500">
                  Down Payment ({formatPercent(financials.down_payment_pct || 0.25)})
                </p>
                <p className="font-semibold">{formatCurrency(financials.down_payment)}</p>
              </div>
            )}
            {financials.loan_amount && (
              <div>
                <p className="text-sm text-gray-500">Loan Amount</p>
                <p className="font-semibold">{formatCurrency(financials.loan_amount)}</p>
              </div>
            )}
            {financials.closing_costs && (
              <div>
                <p className="text-sm text-gray-500">Closing Costs</p>
                <p className="font-semibold">{formatCurrency(financials.closing_costs)}</p>
              </div>
            )}
            {financials.total_cash_invested && (
              <div>
                <p className="text-sm text-gray-500">Total Cash Needed</p>
                <p className="font-semibold text-primary-600">
                  {formatCurrency(financials.total_cash_invested)}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Monthly Expenses Breakdown */}
      {financials && financials.monthly_mortgage && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Expenses</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {[
              { label: "Mortgage", value: financials.monthly_mortgage },
              { label: "Taxes", value: financials.property_taxes },
              { label: "Insurance", value: financials.insurance },
              { label: "HOA", value: financials.hoa },
              { label: "Maintenance", value: financials.maintenance },
              { label: "CapEx", value: financials.capex },
              { label: "Vacancy", value: financials.vacancy },
              { label: "Management", value: financials.property_management },
            ]
              .filter((item) => item.value !== undefined && item.value > 0)
              .map((item) => (
                <div key={item.label} className="text-center p-2 bg-gray-50 rounded">
                  <p className="text-xs text-gray-500">{item.label}</p>
                  <p className="text-sm font-medium">{formatCurrency(item.value!)}</p>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Pros, Cons, Red Flags */}
      {(pros.length > 0 || cons.length > 0 || redFlags.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Pros */}
          <div className={cn("card", pros.length > 0 ? "border-green-200" : "border-gray-200")}>
            <h3
              className={cn(
                "font-semibold mb-3 flex items-center gap-2",
                pros.length > 0 ? "text-green-800" : "text-gray-400"
              )}
            >
              <CheckCircle className="h-5 w-5" />
              Pros
            </h3>
            {pros.length > 0 ? (
              <ul className="space-y-2">
                {pros.map((pro, i) => (
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
          <div className={cn("card", cons.length > 0 ? "border-yellow-200" : "border-gray-200")}>
            <h3
              className={cn(
                "font-semibold mb-3 flex items-center gap-2",
                cons.length > 0 ? "text-yellow-800" : "text-gray-400"
              )}
            >
              <AlertTriangle className="h-5 w-5" />
              Cons
            </h3>
            {cons.length > 0 ? (
              <ul className="space-y-2">
                {cons.map((con, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    {con}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400 italic">No significant cons identified</p>
            )}
          </div>

          {/* Red Flags */}
          <div className={cn("card", redFlags.length > 0 ? "border-red-200" : "border-gray-200")}>
            <h3
              className={cn(
                "font-semibold mb-3 flex items-center gap-2",
                redFlags.length > 0 ? "text-red-800" : "text-gray-400"
              )}
            >
              <XCircle className="h-5 w-5" />
              Red Flags
            </h3>
            {redFlags.length > 0 ? (
              <ul className="space-y-2">
                {redFlags.map((flag, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                    <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                    {flag}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400 italic">No red flags identified</p>
            )}
          </div>
        </div>
      )}

      {/* Market Context */}
      {market && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary-600" />
            Market Context
          </h3>
          <div className="flex items-center gap-6">
            <div>
              <p className="font-medium text-lg">{market.name}, {market.state}</p>
              {market.metro && <p className="text-sm text-gray-500">{market.metro}</p>}
            </div>
            {market.overall_score && (
              <ScoreGauge score={market.overall_score} label="Market Score" size="sm" />
            )}
            {market.id && (
              <Link
                href={`/markets/${market.id}`}
                className="text-sm text-primary-600 hover:text-primary-700 ml-auto"
              >
                View Market Details
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Walk Score */}
      {(locationData?.walk_score || locationLoading) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Footprints className="h-5 w-5" />
            Walk Score
          </h3>
          {locationLoading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <div className="animate-spin h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full mr-2" />
              Loading walk scores...
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Footprints className="h-6 w-6 mx-auto mb-2 text-gray-600" />
                <p className="text-3xl font-bold text-primary-600">
                  {locationData?.walk_score ?? "N/A"}
                </p>
                <p className="text-sm text-gray-500">{locationData?.walk_description || "Walk Score"}</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Train className="h-6 w-6 mx-auto mb-2 text-gray-600" />
                <p className="text-3xl font-bold text-blue-600">
                  {locationData?.transit_score ?? "N/A"}
                </p>
                <p className="text-sm text-gray-500">{locationData?.transit_description || "Transit Score"}</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <Bike className="h-6 w-6 mx-auto mb-2 text-gray-600" />
                <p className="text-3xl font-bold text-green-600">
                  {locationData?.bike_score ?? "N/A"}
                </p>
                <p className="text-sm text-gray-500">{locationData?.bike_description || "Bike Score"}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Noise Score & Schools */}
      {(locationData?.noise || locationData?.schools) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Location Insights
          </h3>
          <div className="space-y-6">
            {/* Noise */}
            {locationData.noise && (
              <div>
                <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <Volume2 className="h-4 w-4" />
                  Noise Level
                </h4>
                <div className="flex items-center gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg min-w-[100px]">
                    <p
                      className={cn(
                        "text-3xl font-bold",
                        locationData.noise.noise_score !== undefined && locationData.noise.noise_score <= 30
                          ? "text-green-600"
                          : locationData.noise.noise_score !== undefined && locationData.noise.noise_score <= 60
                          ? "text-yellow-600"
                          : "text-red-600"
                      )}
                    >
                      {locationData.noise.noise_score ?? "N/A"}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {locationData.noise.description || "Noise Score"}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Schools */}
            {locationData.schools && locationData.schools.length > 0 && (
              <div>
                <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <GraduationCap className="h-4 w-4" />
                  Nearby Schools
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {locationData.schools.slice(0, 6).map((school, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 text-sm truncate">{school.name}</p>
                          <p className="text-xs text-gray-500">
                            {school.type && <span className="capitalize">{school.type}</span>}
                            {school.type && school.grades && " - "}
                            {school.grades}
                          </p>
                          {school.distance_miles !== undefined && (
                            <p className="text-xs text-gray-400 mt-1">
                              {school.distance_miles.toFixed(1)} mi away
                            </p>
                          )}
                        </div>
                        {school.rating !== undefined && school.rating !== null && (
                          <div
                            className={cn(
                              "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium",
                              school.rating >= 8
                                ? "bg-green-100 text-green-700"
                                : school.rating >= 6
                                ? "bg-yellow-100 text-yellow-700"
                                : school.rating >= 4
                                ? "bg-orange-100 text-orange-700"
                                : "bg-red-100 text-red-700"
                            )}
                          >
                            <Star className="h-3 w-3" />
                            {school.rating}/10
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Flood Zone */}
      {locationData?.flood_zone && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Droplets className="h-5 w-5" />
            FEMA Flood Zone
          </h3>
          <div className="flex items-center gap-6">
            <div
              className={cn(
                "text-center p-4 rounded-lg min-w-[120px]",
                locationData.flood_zone.risk_level === "high"
                  ? "bg-red-50"
                  : locationData.flood_zone.risk_level === "moderate"
                  ? "bg-yellow-50"
                  : locationData.flood_zone.risk_level === "low"
                  ? "bg-green-50"
                  : "bg-gray-50"
              )}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                {locationData.flood_zone.risk_level === "high" ? (
                  <ShieldAlert className="h-5 w-5 text-red-600" />
                ) : locationData.flood_zone.risk_level === "low" ? (
                  <ShieldCheck className="h-5 w-5 text-green-600" />
                ) : (
                  <Droplets className="h-5 w-5 text-gray-400" />
                )}
                <span className="text-sm font-medium text-gray-600">Zone</span>
              </div>
              <p
                className={cn(
                  "text-2xl font-bold",
                  locationData.flood_zone.risk_level === "high"
                    ? "text-red-600"
                    : locationData.flood_zone.risk_level === "moderate"
                    ? "text-yellow-600"
                    : locationData.flood_zone.risk_level === "low"
                    ? "text-green-600"
                    : "text-gray-600"
                )}
              >
                {locationData.flood_zone.zone || "N/A"}
              </p>
              <p
                className={cn(
                  "text-xs font-medium capitalize mt-1",
                  locationData.flood_zone.risk_level === "high"
                    ? "text-red-600"
                    : locationData.flood_zone.risk_level === "moderate"
                    ? "text-yellow-600"
                    : locationData.flood_zone.risk_level === "low"
                    ? "text-green-600"
                    : "text-gray-500"
                )}
              >
                {locationData.flood_zone.risk_level} Risk
              </p>
            </div>
            <div className="flex-1 space-y-2">
              <p className="text-gray-700">{locationData.flood_zone.description}</p>
              <div className="flex flex-wrap gap-4 text-sm">
                {locationData.flood_zone.annual_chance && (
                  <div>
                    <span className="text-gray-500">Annual Flood Chance:</span>{" "}
                    <span className="font-medium">{locationData.flood_zone.annual_chance}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Flood Insurance:</span>{" "}
                  <span
                    className={cn(
                      "font-medium",
                      locationData.flood_zone.requires_insurance ? "text-red-600" : "text-green-600"
                    )}
                  >
                    {locationData.flood_zone.requires_insurance ? "Required" : "Not Required"}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-4 text-center">
            Data from FEMA National Flood Hazard Layer (NFHL)
          </p>
        </div>
      )}

      {/* Custom Scenarios (What Should I Offer) */}
      {customScenarios && customScenarios.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Calculator className="h-5 w-5 text-primary-600" />
            Saved Scenarios
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 font-medium text-gray-500">Scenario</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-500">Offer Price</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-500">Cash Flow</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-500">CoC</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-500">Cap Rate</th>
                  <th className="text-right py-2 px-3 font-medium text-gray-500">Cash Needed</th>
                </tr>
              </thead>
              <tbody>
                {customScenarios.map((scenario, i) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-2 px-3 font-medium">{scenario.name}</td>
                    <td className="py-2 px-3 text-right">{formatCurrency(scenario.offer_price)}</td>
                    <td
                      className={cn(
                        "py-2 px-3 text-right font-medium",
                        getCashFlowColor(scenario.monthly_cash_flow)
                      )}
                    >
                      {formatCurrency(scenario.monthly_cash_flow)}
                    </td>
                    <td className="py-2 px-3 text-right">{formatPercent(scenario.cash_on_cash)}</td>
                    <td className="py-2 px-3 text-right">{formatPercent(scenario.cap_rate)}</td>
                    <td className="py-2 px-3 text-right">{formatCurrency(scenario.total_cash_needed)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Property Features */}
      {property.features && property.features.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Home className="h-5 w-5" />
            Property Features
          </h3>
          <div className="flex flex-wrap gap-2">
            {property.features.map((feature) => (
              <span key={feature} className="badge-gray">
                {feature}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Source Link */}
      {property.source_url && (
        <div className="text-center">
          <a
            href={property.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700"
          >
            <ExternalLink className="h-4 w-4" />
            View Original Listing on {property.source || "source"}
          </a>
        </div>
      )}
    </div>
  );
}
