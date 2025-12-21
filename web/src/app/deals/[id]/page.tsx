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
} from "lucide-react";
import { api } from "@/lib/api";
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
