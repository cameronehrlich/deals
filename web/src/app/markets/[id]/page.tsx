"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  MapPin,
  Users,
  Briefcase,
  Home,
  TrendingUp,
  TrendingDown,
  Building,
  DollarSign,
  Shield,
  Clock,
  Database,
  CheckCircle,
  RefreshCw,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { api, MarketDetail } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  formatPercentValue,
  formatNumber,
  getScoreBadge,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingPage } from "@/components/LoadingSpinner";

// Data source display info
const DATA_SOURCE_INFO: Record<string, { label: string; color: string; description: string }> = {
  redfin: { label: "Redfin", color: "bg-red-100 text-red-700", description: "Housing prices & trends" },
  bls: { label: "BLS", color: "bg-blue-100 text-blue-700", description: "Employment data" },
  census: { label: "Census", color: "bg-purple-100 text-purple-700", description: "Demographics" },
  hud: { label: "HUD", color: "bg-green-100 text-green-700", description: "Fair market rents" },
  fred: { label: "FRED", color: "bg-amber-100 text-amber-700", description: "Macro economics" },
  state_data: { label: "State", color: "bg-gray-100 text-gray-700", description: "Regulatory data" },
};

// Score to data source mapping
const SCORE_DATA_SOURCES: Record<string, string[]> = {
  cash_flow: ["hud", "redfin", "state_data"],
  growth: ["census", "bls"],
  affordability: ["census", "hud"],
  stability: ["redfin"],
  liquidity: ["redfin"],
  operating_cost: ["state_data"],
  regulatory: ["state_data"],
};

export default function MarketDetailPage() {
  const params = useParams();
  const marketId = params.id as string;

  const [market, setMarket] = useState<MarketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!marketId || refreshing) return;
    try {
      setRefreshing(true);
      setError(null);
      await api.refreshMarketData(marketId);
      // Re-fetch the market data after refresh
      const data = await api.getMarket(marketId);
      setMarket(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh market data");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    async function fetchMarket() {
      try {
        setLoading(true);
        const data = await api.getMarket(marketId);
        setMarket(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load market");
      } finally {
        setLoading(false);
      }
    }

    if (marketId) {
      fetchMarket();
    }
  }, [marketId]);

  if (loading) return <LoadingPage />;
  if (error || !market) {
    return (
      <div className="text-center py-12 animate-fade-in">
        <MapPin className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <p className="text-red-600">{error || "Market not found"}</p>
        <Link href="/markets" className="btn-primary mt-4 inline-block">
          ← Back to markets
        </Link>
      </div>
    );
  }

  // Helper function for score progress bar with data source indicators
  const ScoreBar = ({
    score,
    label,
    color,
    scoreKey,
    dataSources,
  }: {
    score: number;
    label: string;
    color: string;
    scoreKey?: string;
    dataSources?: string[];
  }) => {
    // Get which data sources contribute to this score
    const relevantSources = scoreKey ? SCORE_DATA_SOURCES[scoreKey] || [] : [];
    const availableSources = relevantSources.filter(s => dataSources?.includes(s));
    const hasAllData = relevantSources.length > 0 && availableSources.length === relevantSources.length;

    return (
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-600">{label}</span>
            {/* Show tiny data source pills */}
            {availableSources.length > 0 && (
              <div className="flex gap-0.5">
                {availableSources.map(source => {
                  const info = DATA_SOURCE_INFO[source];
                  return info ? (
                    <span
                      key={source}
                      className={cn(
                        "text-[9px] px-1 py-0 rounded font-medium opacity-70",
                        info.color
                      )}
                      title={`${info.label}: ${info.description}`}
                    >
                      {info.label}
                    </span>
                  ) : null;
                })}
              </div>
            )}
          </div>
          <span className="font-semibold">{score.toFixed(0)}</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${color}`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    );
  };

  // Data completeness indicator
  const DataCompletenessBar = ({ completeness, sources }: { completeness?: number; sources?: string[] }) => {
    const pct = (completeness || 0) * 100;
    return (
      <div className="flex items-center gap-3 text-xs text-gray-500">
        <Database className="h-3.5 w-3.5" />
        <div className="flex-1">
          <div className="flex justify-between mb-0.5">
            <span>Data Completeness</span>
            <span className="font-medium">{pct.toFixed(0)}%</span>
          </div>
          <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-amber-500" : "bg-red-400"
              )}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
        {sources && sources.length > 0 && (
          <div className="flex gap-1">
            {sources.map(source => {
              const info = DATA_SOURCE_INFO[source];
              return info ? (
                <span
                  key={source}
                  className={cn("text-[9px] px-1.5 py-0.5 rounded font-medium", info.color)}
                  title={info.description}
                >
                  {info.label}
                </span>
              ) : null;
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back link */}
      <Link
        href="/markets"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to markets
      </Link>

      {/* Enrichment Pending Banner */}
      {(market.enrichment_pending || (!market.data_sources || market.data_sources.length === 0)) && (
        <div className="card bg-amber-50 border-amber-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800">Market data incomplete</p>
              <p className="text-sm text-amber-600">
                Some data sources failed to load. Click refresh to retry.
              </p>
            </div>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-outline text-amber-700 border-amber-300 hover:bg-amber-100 flex items-center gap-2"
          >
            {refreshing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Refreshing...
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                Refresh Data
              </>
            )}
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {market.name}, {market.state}
          </h1>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            {market.metro || "Metro area"}
            {market.region && ` • ${market.region}`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-outline flex items-center gap-2"
            title="Refresh market data"
          >
            {refreshing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </button>
          <Link
            href={`/deals?markets=${market.id}`}
            className="btn-primary"
          >
            Find Deals in {market.name}
          </Link>
        </div>
      </div>

      {/* Scores - Visual Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overall Score */}
        <div className="card flex flex-col items-center justify-center py-8">
          <ScoreGauge score={market.overall_score} label="Overall Score" size="lg" />
          <p className="text-sm text-gray-500 mt-4 text-center">
            {market.overall_score >= 70 ? "Excellent investment market" :
             market.overall_score >= 50 ? "Good investment potential" :
             "Consider other markets"}
          </p>
        </div>

        {/* Score Breakdown */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              Score Breakdown
            </h2>
            {market.data_sources && market.data_sources.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                <span>{market.data_sources.length} data sources</span>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ScoreBar
              score={market.cash_flow_score}
              label="Cash Flow"
              color="bg-green-500"
              scoreKey="cash_flow"
              dataSources={market.data_sources}
            />
            <ScoreBar
              score={market.growth_score}
              label="Growth"
              color="bg-blue-500"
              scoreKey="growth"
              dataSources={market.data_sources}
            />
            <ScoreBar
              score={market.affordability_score}
              label="Affordability"
              color="bg-purple-500"
              scoreKey="affordability"
              dataSources={market.data_sources}
            />
            <ScoreBar
              score={market.stability_score}
              label="Stability"
              color="bg-orange-500"
              scoreKey="stability"
              dataSources={market.data_sources}
            />
            <ScoreBar
              score={market.liquidity_score}
              label="Liquidity"
              color="bg-cyan-500"
              scoreKey="liquidity"
              dataSources={market.data_sources}
            />
            <ScoreBar
              score={market.operating_cost_score || 50}
              label="Operating Costs"
              color="bg-rose-500"
              scoreKey="operating_cost"
              dataSources={market.data_sources}
            />
            <ScoreBar
              score={market.regulatory_score || 50}
              label="Regulatory"
              color="bg-indigo-500"
              scoreKey="regulatory"
              dataSources={market.data_sources}
            />
            {/* Data completeness indicator */}
            <div className="md:col-span-2 pt-4 border-t border-gray-100">
              <DataCompletenessBar
                completeness={market.data_completeness}
                sources={market.data_sources}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Demographics */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Demographics
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Users className="h-4 w-4" />
                Population
              </span>
              <span className="font-semibold">{market.population ? formatNumber(market.population) : "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">1Y Growth</span>
              <span className={cn(
                "font-semibold",
                (market.population_growth_1yr || 0) >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {market.population_growth_1yr != null ? formatPercentValue(market.population_growth_1yr, true) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">5Y Growth</span>
              <span className="font-semibold">
                {market.population_growth_5yr != null ? formatPercentValue(market.population_growth_5yr, true) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <DollarSign className="h-4 w-4" />
                Median Income
              </span>
              <span className="font-semibold">{market.median_household_income ? formatCurrency(market.median_household_income) : "N/A"}</span>
            </div>
            {market.median_household_income && (
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Income Tier</span>
                <span className={cn(
                  "text-xs px-2 py-0.5 rounded-full",
                  market.median_household_income >= 100000 ? "bg-green-100 text-green-700" :
                  market.median_household_income >= 60000 ? "bg-blue-100 text-blue-700" :
                  market.median_household_income >= 35000 ? "bg-amber-100 text-amber-700" :
                  "bg-red-100 text-red-700"
                )}>
                  {market.median_household_income >= 100000 ? "High Income" :
                   market.median_household_income >= 60000 ? "Middle Income" :
                   market.median_household_income >= 35000 ? "Low-Middle Income" :
                   "Low Income"}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Employment */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Employment
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Briefcase className="h-4 w-4" />
                Unemployment
              </span>
              <span className="font-semibold">
                {market.unemployment_rate != null ? formatPercentValue(market.unemployment_rate) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Job Growth (1Y)</span>
              <span className={cn(
                "font-semibold",
                (market.job_growth_1yr || 0) >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {market.job_growth_1yr != null ? formatPercentValue(market.job_growth_1yr, true) : "N/A"}
              </span>
            </div>
            {market.major_employers.length > 0 && (
              <div>
                <span className="text-gray-600 text-sm">Major Employers</span>
                <div className="flex flex-wrap gap-1 mt-2">
                  {market.major_employers.slice(0, 4).map((employer) => (
                    <span key={employer} className="badge-gray text-xs">
                      {employer}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Housing Market */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Housing Market
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Home className="h-4 w-4" />
                Median Price
              </span>
              <span className="font-semibold">{market.median_home_price ? formatCurrency(market.median_home_price) : "N/A"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Price Change (1Y)</span>
              <span className={cn(
                "font-semibold flex items-center gap-1",
                (market.price_change_1yr || 0) >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {(market.price_change_1yr || 0) >= 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                {market.price_change_1yr != null ? formatPercentValue(market.price_change_1yr, true) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Price Change (5Y)</span>
              <span className="font-semibold">
                {market.price_change_5yr != null ? formatPercentValue(market.price_change_5yr, true) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Clock className="h-4 w-4" />
                Days on Market
              </span>
              <span className="font-semibold">
                {market.days_on_market_avg ? `${market.days_on_market_avg} days` : "N/A"}
              </span>
            </div>
          </div>
        </div>

        {/* Rental Market */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Rental Market
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Building className="h-4 w-4" />
                Median Rent
              </span>
              <span className="font-semibold">{market.median_rent ? formatCurrency(market.median_rent) : "N/A"}/mo</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Rent Change (1Y)</span>
              <span className={cn(
                "font-semibold",
                (market.rent_change_1yr || 0) >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {market.rent_change_1yr != null ? formatPercentValue(market.rent_change_1yr, true) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Rent/Price Ratio</span>
              <span className={cn(
                "font-semibold",
                (market.rent_to_price_ratio || 0) >= 0.7 ? "text-green-600" : "text-yellow-600"
              )}>
                {market.rent_to_price_ratio != null ? formatPercentValue(market.rent_to_price_ratio) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Months Inventory</span>
              <span className="font-semibold">
                {market.months_of_inventory ? `${market.months_of_inventory.toFixed(1)} mo` : "N/A"}
              </span>
            </div>
            {market.median_rent && market.median_household_income && (() => {
              const monthlyIncome = market.median_household_income / 12;
              const rentToIncomeRatio = (market.median_rent / monthlyIncome) * 100;
              const isAffordable = rentToIncomeRatio <= 30;
              const affordableRent = monthlyIncome * 0.30;
              return (
                <>
                  <div className="pt-3 border-t border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-600">Rent-to-Income</span>
                      <span className={cn(
                        "font-semibold",
                        rentToIncomeRatio <= 25 ? "text-green-600" :
                        rentToIncomeRatio <= 30 ? "text-blue-600" :
                        rentToIncomeRatio <= 40 ? "text-amber-600" :
                        "text-red-600"
                      )}>
                        {rentToIncomeRatio.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">30% Affordable</span>
                      <span className="font-semibold">{formatCurrency(affordableRent)}/mo</span>
                    </div>
                    <div className={cn(
                      "mt-2 text-xs px-2 py-1 rounded text-center",
                      isAffordable ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"
                    )}>
                      {isAffordable
                        ? "Median rent is affordable for local households"
                        : "Median rent exceeds 30% affordability guideline"
                      }
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>

        {/* Regulatory & Costs */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Regulatory & Costs
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Shield className="h-4 w-4" />
                Landlord Friendly
              </span>
              <div className="flex items-center gap-2">
                {market.landlord_friendly_score && (
                  <span className="text-xs text-gray-500">{market.landlord_friendly_score}/10</span>
                )}
                <span className={cn(
                  "font-semibold",
                  market.landlord_friendly ? "text-green-600" : "text-red-600"
                )}>
                  {market.landlord_friendly ? "Yes" : "No"}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Property Tax Rate</span>
              <span className={cn(
                "font-semibold",
                market.property_tax_rate && market.property_tax_rate < 0.01 ? "text-green-600" :
                market.property_tax_rate && market.property_tax_rate > 0.02 ? "text-red-600" :
                "text-gray-900"
              )}>
                {market.property_tax_rate ? formatPercent(market.property_tax_rate) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">State Income Tax</span>
              <span className={cn(
                "font-semibold",
                market.has_state_income_tax === false ? "text-green-600" : "text-gray-600"
              )}>
                {market.has_state_income_tax === false ? "None" :
                 market.has_state_income_tax === true ? "Yes" : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Insurance Risk</span>
              <span className={cn(
                "badge",
                market.insurance_risk === "low" ? "badge-green" :
                market.insurance_risk === "medium" ? "badge-yellow" : "badge-red"
              )}>
                {market.insurance_risk || "N/A"}
              </span>
            </div>
            {market.insurance_risk_factors && market.insurance_risk_factors.length > 0 && (
              <div className="pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-500">Risk Factors:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {market.insurance_risk_factors.map((factor) => (
                    <span key={factor} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded capitalize">
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Market Trends */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Market Trends
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Price Trend</span>
              <span className={cn(
                "badge",
                market.price_trend.includes("growth") ? "badge-green" :
                market.price_trend.includes("decline") ? "badge-red" : "badge-gray"
              )}>
                {market.price_trend.replace(/_/g, " ")}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Rent Trend</span>
              <span className={cn(
                "badge",
                market.rent_trend.includes("growth") ? "badge-green" :
                market.rent_trend.includes("decline") ? "badge-red" : "badge-gray"
              )}>
                {market.rent_trend.replace(/_/g, " ")}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
