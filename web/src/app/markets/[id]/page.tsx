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
} from "lucide-react";
import { api, MarketDetail } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  getScoreBadge,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingPage } from "@/components/LoadingSpinner";

export default function MarketDetailPage() {
  const params = useParams();
  const marketId = params.id as string;

  const [market, setMarket] = useState<MarketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  // Helper function for score progress bar
  const ScoreBar = ({ score, label, color }: { score: number; label: string; color: string }) => (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
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

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {market.name}, {market.state}
          </h1>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            <MapPin className="h-4 w-4" />
            {market.metro}
            {market.region && ` • ${market.region}`}
          </p>
        </div>

        <Link
          href={`/deals?markets=${market.id}`}
          className="btn-primary"
        >
          Find Deals in {market.name}
        </Link>
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
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Score Breakdown
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ScoreBar score={market.cash_flow_score} label="Cash Flow Potential" color="bg-green-500" />
            <ScoreBar score={market.growth_score} label="Growth Potential" color="bg-blue-500" />
            <ScoreBar score={market.affordability_score} label="Affordability" color="bg-purple-500" />
            <ScoreBar score={market.stability_score} label="Economic Stability" color="bg-orange-500" />
            <ScoreBar score={market.liquidity_score} label="Market Liquidity" color="bg-cyan-500" />
            {/* Investment Quick Stats */}
            <div className="md:col-span-2 pt-4 border-t border-gray-100">
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-gray-600">Cash Flow:</span>
                  <span className="font-medium">{market.rent_to_price_ratio?.toFixed(2)}% rent/price</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-gray-600">Growth:</span>
                  <span className="font-medium">{market.price_change_1yr ? `${market.price_change_1yr > 0 ? "+" : ""}${market.price_change_1yr}%` : "N/A"} YoY</span>
                </div>
              </div>
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
                {market.population_growth_1yr ? `${market.population_growth_1yr > 0 ? "+" : ""}${market.population_growth_1yr}%` : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">5Y Growth</span>
              <span className="font-semibold">
                {market.population_growth_5yr ? `${market.population_growth_5yr > 0 ? "+" : ""}${market.population_growth_5yr}%` : "N/A"}
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
                {market.unemployment_rate ? formatPercent(market.unemployment_rate) : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Job Growth (1Y)</span>
              <span className={cn(
                "font-semibold",
                (market.job_growth_1yr || 0) >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {market.job_growth_1yr ? `${market.job_growth_1yr > 0 ? "+" : ""}${market.job_growth_1yr}%` : "N/A"}
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
                {market.price_change_1yr ? `${market.price_change_1yr > 0 ? "+" : ""}${market.price_change_1yr}%` : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Price Change (5Y)</span>
              <span className="font-semibold">
                {market.price_change_5yr ? `+${market.price_change_5yr}%` : "N/A"}
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
                {market.rent_change_1yr ? `${market.rent_change_1yr > 0 ? "+" : ""}${market.rent_change_1yr}%` : "N/A"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Rent/Price Ratio</span>
              <span className={cn(
                "font-semibold",
                (market.rent_to_price_ratio || 0) >= 0.7 ? "text-green-600" : "text-yellow-600"
              )}>
                {market.rent_to_price_ratio ? `${market.rent_to_price_ratio.toFixed(2)}%` : "N/A"}
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

        {/* Regulatory */}
        <div className="card">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-4">
            Regulatory & Risk
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-gray-600">
                <Shield className="h-4 w-4" />
                Landlord Friendly
              </span>
              <span className={cn(
                "font-semibold",
                market.landlord_friendly ? "text-green-600" : "text-red-600"
              )}>
                {market.landlord_friendly ? "Yes" : "No"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Property Tax Rate</span>
              <span className="font-semibold">
                {market.property_tax_rate ? formatPercent(market.property_tax_rate) : "N/A"}
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
