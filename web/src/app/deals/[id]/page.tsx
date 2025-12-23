"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  MapPin,
  Bed,
  Bath,
  Square,
  Calendar,
  Clock,
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
} from "lucide-react";
import { api, WalkScoreResponse, LocationInsightsResponse, FloodZoneResponse } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  getCashFlowColor,
  getScoreBadge,
  getRiskBadge,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingPage } from "@/components/LoadingSpinner";

export default function DealDetailPage() {
  const params = useParams();
  const dealId = params.id as string;

  const [deal, setDeal] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [walkScore, setWalkScore] = useState<WalkScoreResponse | null>(null);
  const [walkScoreLoading, setWalkScoreLoading] = useState(false);
  const [locationInsights, setLocationInsights] = useState<LocationInsightsResponse | null>(null);
  const [locationInsightsLoading, setLocationInsightsLoading] = useState(false);
  const [floodZone, setFloodZone] = useState<FloodZoneResponse | null>(null);
  const [floodZoneLoading, setFloodZoneLoading] = useState(false);

  useEffect(() => {
    async function fetchDeal() {
      try {
        setLoading(true);
        const data = await api.getDeal(dealId);
        setDeal(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load deal");
      } finally {
        setLoading(false);
      }
    }

    if (dealId) {
      fetchDeal();
    }
  }, [dealId]);

  // Fetch Walk Score when we have property coordinates
  useEffect(() => {
    async function fetchWalkScore() {
      if (!deal?.property?.latitude || !deal?.property?.longitude) return;

      try {
        setWalkScoreLoading(true);
        const fullAddress = `${deal.property.address}, ${deal.property.city}, ${deal.property.state} ${deal.property.zip_code}`;
        const scores = await api.getWalkScore({
          address: fullAddress,
          latitude: deal.property.latitude,
          longitude: deal.property.longitude,
        });
        setWalkScore(scores);
      } catch (err) {
        console.error("Failed to fetch Walk Score:", err);
      } finally {
        setWalkScoreLoading(false);
      }
    }

    if (deal?.property) {
      fetchWalkScore();
    }
  }, [deal]);

  // Fetch Location Insights (noise score, schools) when we have property coordinates
  useEffect(() => {
    async function fetchLocationInsights() {
      if (!deal?.property?.latitude || !deal?.property?.longitude) return;

      try {
        setLocationInsightsLoading(true);
        const insights = await api.getLocationInsights({
          latitude: deal.property.latitude,
          longitude: deal.property.longitude,
          zip_code: deal.property.zip_code,
        });
        setLocationInsights(insights);
      } catch (err) {
        console.error("Failed to fetch location insights:", err);
      } finally {
        setLocationInsightsLoading(false);
      }
    }

    if (deal?.property) {
      fetchLocationInsights();
    }
  }, [deal]);

  // Fetch Flood Zone data when we have property coordinates
  useEffect(() => {
    async function fetchFloodZone() {
      if (!deal?.property?.latitude || !deal?.property?.longitude) return;

      try {
        setFloodZoneLoading(true);
        const flood = await api.getFloodZone({
          latitude: deal.property.latitude,
          longitude: deal.property.longitude,
        });
        setFloodZone(flood);
      } catch (err) {
        console.error("Failed to fetch flood zone:", err);
      } finally {
        setFloodZoneLoading(false);
      }
    }

    if (deal?.property) {
      fetchFloodZone();
    }
  }, [deal]);

  if (loading) return <LoadingPage />;
  if (error || !deal) {
    return (
      <div className="text-center py-12 animate-fade-in">
        <Home className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <p className="text-red-600 font-medium">{error || "Deal not found"}</p>
        <p className="text-gray-500 text-sm mt-2">The property you're looking for may have been removed or sold.</p>
        <Link href="/deals" className="btn-primary mt-4 inline-block">
          ← Back to deals
        </Link>
      </div>
    );
  }

  const { property, financials, score, market } = deal;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back link */}
      <Link
        href="/deals"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to deals
      </Link>

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {property.address}
          </h1>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            {property.full_address}
          </p>
          <div className="flex flex-wrap items-center gap-4 mt-3 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <Bed className="h-4 w-4" />
              {property.bedrooms} beds
            </span>
            <span className="flex items-center gap-1">
              <Bath className="h-4 w-4" />
              {property.bathrooms} baths
            </span>
            {property.sqft && (
              <span className="flex items-center gap-1">
                <Square className="h-4 w-4" />
                {formatNumber(property.sqft)} sqft
              </span>
            )}
            {property.year_built && (
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Built {property.year_built}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {property.days_on_market} days on market
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-3xl font-bold text-gray-900">
              {formatCurrency(property.list_price)}
            </p>
            {property.price_per_sqft && (
              <p className="text-sm text-gray-500">
                {formatCurrency(property.price_per_sqft)}/sqft
              </p>
            )}
          </div>
          {score && (
            <ScoreGauge score={score.overall_score} label="Score" size="md" />
          )}
        </div>
      </div>

      {/* Score Breakdown */}
      {score && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Investment Score Breakdown
          </h2>
          <div className="flex flex-wrap justify-around gap-6">
            <ScoreGauge score={score.overall_score} label="Overall" size="md" />
            <ScoreGauge score={score.financial_score} label="Financial" size="sm" />
            <ScoreGauge score={score.market_score} label="Market" size="sm" />
            <ScoreGauge score={score.risk_score} label="Risk" size="sm" />
            <ScoreGauge score={score.liquidity_score} label="Liquidity" size="sm" />
          </div>
          {score.rank && (
            <p className="text-center text-sm text-gray-500 mt-4">
              Ranked #{score.rank} • Top {score.percentile?.toFixed(0)}%
            </p>
          )}
        </div>
      )}

      {/* Financial Analysis */}
      {financials && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Key Returns */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Key Returns
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Monthly Cash Flow</span>
                <span className={cn(
                  "text-xl font-bold",
                  getCashFlowColor(financials.monthly_cash_flow)
                )}>
                  {formatCurrency(financials.monthly_cash_flow)}/mo
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Annual Cash Flow</span>
                <span className="font-semibold">
                  {formatCurrency(financials.annual_cash_flow)}/yr
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cash-on-Cash Return</span>
                <span className={cn(
                  "font-semibold",
                  financials.cash_on_cash_return >= 0.08 ? "text-green-600" :
                  financials.cash_on_cash_return >= 0.06 ? "text-yellow-600" : "text-red-600"
                )}>
                  {formatPercent(financials.cash_on_cash_return)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cap Rate</span>
                <span className="font-semibold">
                  {formatPercent(financials.cap_rate)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Rent-to-Price Ratio</span>
                <span className={cn(
                  "font-semibold",
                  financials.rent_to_price_ratio >= 1.0 ? "text-green-600" : "text-yellow-600"
                )}>
                  {financials.rent_to_price_ratio.toFixed(2)}%
                </span>
              </div>
              {financials.dscr && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">DSCR</span>
                  <span className={cn(
                    "font-semibold",
                    financials.dscr >= 1.25 ? "text-green-600" :
                    financials.dscr >= 1.0 ? "text-yellow-600" : "text-red-600"
                  )}>
                    {financials.dscr.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Investment Summary */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Investment Summary
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Purchase Price</span>
                <span className="font-semibold">
                  {formatCurrency(financials.purchase_price)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Down Payment ({formatPercent(financials.down_payment_pct)})</span>
                <span className="font-semibold">
                  {formatCurrency(financials.down_payment)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Loan Amount</span>
                <span className="font-semibold">
                  {formatCurrency(financials.loan_amount)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Closing Costs</span>
                <span className="font-semibold">
                  {formatCurrency(financials.closing_costs)}
                </span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-gray-900 font-medium">Total Cash Needed</span>
                <span className="text-lg font-bold text-gray-900">
                  {formatCurrency(financials.total_cash_invested)}
                </span>
              </div>
            </div>
          </div>

          {/* Monthly Expenses */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Monthly Expenses
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Mortgage (P&I)</span>
                <span>{formatCurrency(financials.monthly_mortgage)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Property Taxes</span>
                <span>{formatCurrency(financials.monthly_taxes)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Insurance</span>
                <span>{formatCurrency(financials.monthly_insurance)}</span>
              </div>
              {financials.monthly_hoa > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-600">HOA</span>
                  <span>{formatCurrency(financials.monthly_hoa)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Maintenance Reserve</span>
                <span>{formatCurrency(financials.monthly_maintenance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">CapEx Reserve</span>
                <span>{formatCurrency(financials.monthly_capex)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Vacancy Reserve</span>
                <span>{formatCurrency(financials.monthly_vacancy_reserve)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Property Management</span>
                <span>{formatCurrency(financials.monthly_property_management)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t">
                <span className="font-medium">Total Expenses</span>
                <span className="font-semibold">
                  {formatCurrency(financials.total_monthly_expenses)}
                </span>
              </div>
            </div>
          </div>

          {/* Income */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Income Analysis
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Monthly Rent</span>
                <span className="text-lg font-semibold text-green-600">
                  {formatCurrency(property.estimated_rent)}/mo
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Expenses</span>
                <span className="text-lg font-semibold text-red-600">
                  -{formatCurrency(financials.total_monthly_expenses)}/mo
                </span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="font-medium">Net Cash Flow</span>
                <span className={cn(
                  "text-xl font-bold",
                  getCashFlowColor(financials.monthly_cash_flow)
                )}>
                  {formatCurrency(financials.monthly_cash_flow)}/mo
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Break-even Occupancy</span>
                <span className={cn(
                  "font-semibold",
                  financials.break_even_occupancy <= 0.85 ? "text-green-600" : "text-yellow-600"
                )}>
                  {formatPercent(financials.break_even_occupancy)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pros, Cons, Red Flags */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {deal.pros && deal.pros.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-green-600 mb-3 flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Pros
            </h3>
            <ul className="space-y-2">
              {deal.pros.map((pro: string, i: number) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-green-500 mt-1">+</span>
                  {pro}
                </li>
              ))}
            </ul>
          </div>
        )}

        {deal.cons && deal.cons.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-semibold text-yellow-600 mb-3 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Cons
            </h3>
            <ul className="space-y-2">
              {deal.cons.map((con: string, i: number) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-yellow-500 mt-1">−</span>
                  {con}
                </li>
              ))}
            </ul>
          </div>
        )}

        {deal.red_flags && deal.red_flags.length > 0 && (
          <div className="card border-red-200">
            <h3 className="text-lg font-semibold text-red-600 mb-3 flex items-center gap-2">
              <XCircle className="h-5 w-5" />
              Red Flags
            </h3>
            <ul className="space-y-2">
              {deal.red_flags.map((flag: string, i: number) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-red-500 mt-1">!</span>
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Market Context */}
      {market && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Market Context: {market.name}, {market.state}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Median Price</p>
              <p className="font-semibold">{formatCurrency(market.median_home_price)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Median Rent</p>
              <p className="font-semibold">{formatCurrency(market.median_rent)}/mo</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Market Score</p>
              <p className="font-semibold">{market.overall_score.toFixed(1)}/100</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Cash Flow Score</p>
              <p className="font-semibold">{market.cash_flow_score.toFixed(1)}/100</p>
            </div>
          </div>
          <Link
            href={`/markets/${market.id}`}
            className="mt-4 inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            View full market analysis →
          </Link>
        </div>
      )}

      {/* Walk Score */}
      {(walkScore || walkScoreLoading) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Footprints className="h-5 w-5" />
            Location Scores
          </h3>
          {walkScoreLoading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <div className="animate-spin h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full mr-2" />
              Loading Walk Score...
            </div>
          ) : walkScore ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Walk Score */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Footprints className={cn(
                    "h-5 w-5",
                    walkScore.walk_score && walkScore.walk_score >= 70 ? "text-green-600" :
                    walkScore.walk_score && walkScore.walk_score >= 50 ? "text-yellow-600" : "text-gray-400"
                  )} />
                  <span className="text-sm font-medium text-gray-600">Walk Score</span>
                </div>
                <p className={cn(
                  "text-3xl font-bold",
                  walkScore.walk_score && walkScore.walk_score >= 70 ? "text-green-600" :
                  walkScore.walk_score && walkScore.walk_score >= 50 ? "text-yellow-600" : "text-gray-900"
                )}>
                  {walkScore.walk_score ?? "N/A"}
                </p>
                {walkScore.walk_description && (
                  <p className="text-sm text-gray-500 mt-1">{walkScore.walk_description}</p>
                )}
              </div>

              {/* Transit Score */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Train className={cn(
                    "h-5 w-5",
                    walkScore.transit_score && walkScore.transit_score >= 70 ? "text-blue-600" :
                    walkScore.transit_score && walkScore.transit_score >= 50 ? "text-yellow-600" : "text-gray-400"
                  )} />
                  <span className="text-sm font-medium text-gray-600">Transit Score</span>
                </div>
                <p className={cn(
                  "text-3xl font-bold",
                  walkScore.transit_score && walkScore.transit_score >= 70 ? "text-blue-600" :
                  walkScore.transit_score && walkScore.transit_score >= 50 ? "text-yellow-600" : "text-gray-900"
                )}>
                  {walkScore.transit_score ?? "N/A"}
                </p>
                {walkScore.transit_description && (
                  <p className="text-sm text-gray-500 mt-1">{walkScore.transit_description}</p>
                )}
              </div>

              {/* Bike Score */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Bike className={cn(
                    "h-5 w-5",
                    walkScore.bike_score && walkScore.bike_score >= 70 ? "text-green-600" :
                    walkScore.bike_score && walkScore.bike_score >= 50 ? "text-yellow-600" : "text-gray-400"
                  )} />
                  <span className="text-sm font-medium text-gray-600">Bike Score</span>
                </div>
                <p className={cn(
                  "text-3xl font-bold",
                  walkScore.bike_score && walkScore.bike_score >= 70 ? "text-green-600" :
                  walkScore.bike_score && walkScore.bike_score >= 50 ? "text-yellow-600" : "text-gray-900"
                )}>
                  {walkScore.bike_score ?? "N/A"}
                </p>
                {walkScore.bike_description && (
                  <p className="text-sm text-gray-500 mt-1">{walkScore.bike_description}</p>
                )}
              </div>
            </div>
          ) : null}
          <p className="text-xs text-gray-400 mt-4 text-center">
            Scores indicate walkability, public transit access, and bikeability (0-100)
          </p>
        </div>
      )}

      {/* Location Insights: Noise Score & Schools */}
      {(locationInsights || locationInsightsLoading) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            Location Insights
          </h3>
          {locationInsightsLoading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <div className="animate-spin h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full mr-2" />
              Loading location data...
            </div>
          ) : locationInsights ? (
            <div className="space-y-6">
              {/* Noise Score */}
              {locationInsights.noise && (
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <Volume2 className="h-4 w-4" />
                    Noise Level
                  </h4>
                  <div className="flex items-center gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg min-w-[100px]">
                      <p className={cn(
                        "text-3xl font-bold",
                        locationInsights.noise.noise_score !== undefined && locationInsights.noise.noise_score <= 30 ? "text-green-600" :
                        locationInsights.noise.noise_score !== undefined && locationInsights.noise.noise_score <= 60 ? "text-yellow-600" : "text-red-600"
                      )}>
                        {locationInsights.noise.noise_score ?? "N/A"}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {locationInsights.noise.description || "Noise Score"}
                      </p>
                    </div>
                    {locationInsights.noise.categories && Object.keys(locationInsights.noise.categories).length > 0 && (
                      <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {Object.entries(locationInsights.noise.categories).map(([category, value]) => (
                          <div key={category} className="text-center p-2 bg-gray-50 rounded">
                            <p className="text-xs text-gray-500 capitalize">{category.replace(/_/g, ' ')}</p>
                            <p className="text-sm font-medium">{value as number}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Schools */}
              {locationInsights.schools && locationInsights.schools.length > 0 && (
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <GraduationCap className="h-4 w-4" />
                    Nearby Schools
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {locationInsights.schools.slice(0, 6).map((school, i) => (
                      <div key={i} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 text-sm truncate">{school.name}</p>
                            <p className="text-xs text-gray-500">
                              {school.type && <span className="capitalize">{school.type}</span>}
                              {school.type && school.grades && " • "}
                              {school.grades}
                            </p>
                            {school.distance_miles !== undefined && (
                              <p className="text-xs text-gray-400 mt-1">
                                {school.distance_miles.toFixed(1)} mi away
                              </p>
                            )}
                          </div>
                          {school.rating !== undefined && school.rating !== null && (
                            <div className={cn(
                              "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium",
                              school.rating >= 8 ? "bg-green-100 text-green-700" :
                              school.rating >= 6 ? "bg-yellow-100 text-yellow-700" :
                              school.rating >= 4 ? "bg-orange-100 text-orange-700" : "bg-red-100 text-red-700"
                            )}>
                              <Star className="h-3 w-3" />
                              {school.rating}/10
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  {locationInsights.schools.length > 6 && (
                    <p className="text-xs text-gray-400 mt-2">
                      + {locationInsights.schools.length - 6} more schools nearby
                    </p>
                  )}
                </div>
              )}

              {!locationInsights.noise && (!locationInsights.schools || locationInsights.schools.length === 0) && (
                <p className="text-gray-500 text-center py-4">No location insights available for this property.</p>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* FEMA Flood Zone */}
      {(floodZone || floodZoneLoading) && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Droplets className="h-5 w-5" />
            FEMA Flood Zone
          </h3>
          {floodZoneLoading ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <div className="animate-spin h-5 w-5 border-2 border-primary-500 border-t-transparent rounded-full mr-2" />
              Loading flood zone data...
            </div>
          ) : floodZone ? (
            <div className="flex items-center gap-6">
              {/* Zone Badge */}
              <div className={cn(
                "text-center p-4 rounded-lg min-w-[120px]",
                floodZone.risk_level === "high" ? "bg-red-50" :
                floodZone.risk_level === "moderate" ? "bg-yellow-50" :
                floodZone.risk_level === "low" ? "bg-green-50" : "bg-gray-50"
              )}>
                <div className="flex items-center justify-center gap-2 mb-2">
                  {floodZone.risk_level === "high" ? (
                    <ShieldAlert className="h-5 w-5 text-red-600" />
                  ) : floodZone.risk_level === "low" ? (
                    <ShieldCheck className="h-5 w-5 text-green-600" />
                  ) : (
                    <Droplets className={cn(
                      "h-5 w-5",
                      floodZone.risk_level === "moderate" ? "text-yellow-600" : "text-gray-400"
                    )} />
                  )}
                  <span className="text-sm font-medium text-gray-600">Zone</span>
                </div>
                <p className={cn(
                  "text-2xl font-bold",
                  floodZone.risk_level === "high" ? "text-red-600" :
                  floodZone.risk_level === "moderate" ? "text-yellow-600" :
                  floodZone.risk_level === "low" ? "text-green-600" : "text-gray-600"
                )}>
                  {floodZone.flood_zone || "N/A"}
                </p>
                <p className={cn(
                  "text-xs font-medium capitalize mt-1",
                  floodZone.risk_level === "high" ? "text-red-600" :
                  floodZone.risk_level === "moderate" ? "text-yellow-600" :
                  floodZone.risk_level === "low" ? "text-green-600" : "text-gray-500"
                )}>
                  {floodZone.risk_level} Risk
                </p>
              </div>

              {/* Details */}
              <div className="flex-1 space-y-2">
                <p className="text-gray-700">{floodZone.description}</p>
                <div className="flex flex-wrap gap-4 text-sm">
                  {floodZone.annual_chance && (
                    <div>
                      <span className="text-gray-500">Annual Flood Chance:</span>{" "}
                      <span className="font-medium">{floodZone.annual_chance}</span>
                    </div>
                  )}
                  <div>
                    <span className="text-gray-500">Flood Insurance:</span>{" "}
                    <span className={cn(
                      "font-medium",
                      floodZone.requires_insurance ? "text-red-600" : "text-green-600"
                    )}>
                      {floodZone.requires_insurance ? "Required" : "Not Required"}
                    </span>
                  </div>
                  {floodZone.base_flood_elevation && (
                    <div>
                      <span className="text-gray-500">Base Flood Elev:</span>{" "}
                      <span className="font-medium">{floodZone.base_flood_elevation} ft</span>
                    </div>
                  )}
                </div>
                {floodZone.firm_panel && (
                  <p className="text-xs text-gray-400 mt-2">
                    FIRM Panel: {floodZone.firm_panel}
                    {floodZone.effective_date && ` (Effective: ${floodZone.effective_date})`}
                  </p>
                )}
              </div>
            </div>
          ) : null}
          <p className="text-xs text-gray-400 mt-4 text-center">
            Data from FEMA National Flood Hazard Layer (NFHL)
          </p>
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
            {property.features.map((feature: string) => (
              <span key={feature} className="badge-gray">
                {feature}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
