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
      <div className="text-center py-12">
        <p className="text-red-600">{error || "Market not found"}</p>
        <Link href="/markets" className="text-primary-600 hover:underline mt-4 inline-block">
          ← Back to markets
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        href="/markets"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
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

      {/* Scores */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Investment Scores
        </h2>
        <div className="flex flex-wrap justify-around gap-6">
          <ScoreGauge score={market.overall_score} label="Overall" size="lg" />
          <ScoreGauge score={market.cash_flow_score} label="Cash Flow" size="md" />
          <ScoreGauge score={market.growth_score} label="Growth" size="md" />
          <ScoreGauge score={market.affordability_score} label="Affordability" size="md" />
          <ScoreGauge score={market.stability_score} label="Stability" size="md" />
          <ScoreGauge score={market.liquidity_score} label="Liquidity" size="md" />
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
