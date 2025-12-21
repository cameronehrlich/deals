"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  MapPin,
  TrendingUp,
  DollarSign,
  Building,
  ArrowRight,
  Search,
} from "lucide-react";
import { api, Market, Deal } from "@/lib/api";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { StatCard } from "@/components/StatCard";
import { MarketCard } from "@/components/MarketCard";
import { DealCard } from "@/components/DealCard";
import { LoadingPage } from "@/components/LoadingSpinner";

export default function DashboardPage() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [marketsRes, dealsRes] = await Promise.all([
          api.getMarkets({ sort_by: "overall", limit: 5 }),
          api.searchDeals({ limit: 5 }),
        ]);
        setMarkets(marketsRes.markets);
        setDeals(dealsRes.deals);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) return <LoadingPage />;

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <p className="text-gray-500">
          Unable to connect to the API server. Please try again later.
        </p>
      </div>
    );
  }

  // Calculate aggregate stats
  const avgScore = markets.length > 0
    ? markets.reduce((sum, m) => sum + m.overall_score, 0) / markets.length
    : 0;
  const avgCashFlow = deals.length > 0
    ? deals.reduce((sum, d) => sum + (d.financials?.monthly_cash_flow || 0), 0) / deals.length
    : 0;
  const topMarket = markets[0];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Real estate investment opportunity overview
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Markets Tracked"
          value={markets.length.toString()}
          subtitle="Active investment markets"
          icon={MapPin}
        />
        <StatCard
          title="Top Market"
          value={topMarket?.name || "N/A"}
          subtitle={`Score: ${topMarket?.overall_score.toFixed(1) || "N/A"}`}
          icon={TrendingUp}
        />
        <StatCard
          title="Avg Cash Flow"
          value={formatCurrency(avgCashFlow)}
          subtitle="Per month (top deals)"
          icon={DollarSign}
        />
        <StatCard
          title="Deals Found"
          value={deals.length.toString()}
          subtitle="Matching your criteria"
          icon={Building}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link href="/deals" className="card-hover flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Search className="h-6 w-6 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-900">Find Deals</h3>
            <p className="text-sm text-gray-500">
              Search properties across markets
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-400" />
        </Link>

        <Link href="/markets" className="card-hover flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-lg">
            <MapPin className="h-6 w-6 text-green-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-900">Explore Markets</h3>
            <p className="text-sm text-gray-500">
              Compare investment locations
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-400" />
        </Link>

        <Link href="/calculator" className="card-hover flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-lg">
            <DollarSign className="h-6 w-6 text-purple-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-900">Calculator</h3>
            <p className="text-sm text-gray-500">
              Analyze any property
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-400" />
        </Link>
      </div>

      {/* Top Markets */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Top Markets</h2>
          <Link
            href="/markets"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all →
          </Link>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {markets.slice(0, 4).map((market, index) => (
            <MarketCard key={market.id} market={market} rank={index + 1} />
          ))}
        </div>
      </div>

      {/* Recent Deals */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Top Deals</h2>
          <Link
            href="/deals"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Find more →
          </Link>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {deals.slice(0, 4).map((deal) => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </div>
      </div>
    </div>
  );
}
