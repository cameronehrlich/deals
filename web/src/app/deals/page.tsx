"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Search, Filter, SlidersHorizontal } from "lucide-react";
import { api, Deal, Market } from "@/lib/api";
import { DealCard } from "@/components/DealCard";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";

const STRATEGIES = [
  { value: "cash_flow", label: "Cash Flow" },
  { value: "appreciation", label: "Appreciation" },
  { value: "value_add", label: "Value Add" },
];

export default function DealsPage() {
  const searchParams = useSearchParams();
  const initialMarket = searchParams.get("markets") || "";

  const [deals, setDeals] = useState<Deal[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedMarkets, setSelectedMarkets] = useState(initialMarket);
  const [strategy, setStrategy] = useState("cash_flow");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [minBeds, setMinBeds] = useState("2");
  const [minCashFlow, setMinCashFlow] = useState<string>("");
  const [downPayment, setDownPayment] = useState("25");
  const [interestRate, setInterestRate] = useState("7");
  const [showFilters, setShowFilters] = useState(false);

  // Fetch markets for dropdown
  useEffect(() => {
    api.getMarkets({ limit: 20 }).then((res) => setMarkets(res.markets));
  }, []);

  const searchDeals = useCallback(async () => {
    try {
      setSearching(true);
      setError(null);

      const params: any = {
        strategy,
        min_beds: parseInt(minBeds),
        down_payment: parseFloat(downPayment) / 100,
        interest_rate: parseFloat(interestRate) / 100,
        limit: 20,
      };

      if (selectedMarkets) params.markets = selectedMarkets;
      if (maxPrice) params.max_price = parseFloat(maxPrice);
      if (minCashFlow) params.min_cash_flow = parseFloat(minCashFlow);

      const res = await api.searchDeals(params);
      setDeals(res.deals);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
      setLoading(false);
    }
  }, [selectedMarkets, strategy, maxPrice, minBeds, minCashFlow, downPayment, interestRate]);

  // Initial search
  useEffect(() => {
    searchDeals();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Find Deals</h1>
        <p className="text-gray-500 mt-1">
          Search and analyze investment properties
        </p>
      </div>

      {/* Search Controls */}
      <div className="card">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Market Select */}
          <div className="flex-1 min-w-[200px]">
            <label className="label">Market</label>
            <select
              value={selectedMarkets}
              onChange={(e) => setSelectedMarkets(e.target.value)}
              className="input"
            >
              <option value="">All Markets</option>
              {markets.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}, {m.state}
                </option>
              ))}
            </select>
          </div>

          {/* Strategy */}
          <div className="w-40">
            <label className="label">Strategy</label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="input"
            >
              {STRATEGIES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>

          {/* Max Price */}
          <div className="w-36">
            <label className="label">Max Price</label>
            <input
              type="number"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              placeholder="Any"
              className="input"
            />
          </div>

          {/* Toggle Filters */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-outline flex items-center gap-2"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
          </button>

          {/* Search Button */}
          <button
            onClick={searchDeals}
            disabled={searching}
            className="btn-primary flex items-center gap-2"
          >
            {searching ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </button>
        </div>

        {/* Extended Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="label">Min Bedrooms</label>
                <select
                  value={minBeds}
                  onChange={(e) => setMinBeds(e.target.value)}
                  className="input"
                >
                  <option value="1">1+</option>
                  <option value="2">2+</option>
                  <option value="3">3+</option>
                  <option value="4">4+</option>
                </select>
              </div>

              <div>
                <label className="label">Min Cash Flow ($/mo)</label>
                <input
                  type="number"
                  value={minCashFlow}
                  onChange={(e) => setMinCashFlow(e.target.value)}
                  placeholder="0"
                  className="input"
                />
              </div>

              <div>
                <label className="label">Down Payment (%)</label>
                <input
                  type="number"
                  value={downPayment}
                  onChange={(e) => setDownPayment(e.target.value)}
                  min="5"
                  max="100"
                  className="input"
                />
              </div>

              <div>
                <label className="label">Interest Rate (%)</label>
                <input
                  type="number"
                  value={interestRate}
                  onChange={(e) => setInterestRate(e.target.value)}
                  min="1"
                  max="20"
                  step="0.25"
                  className="input"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {loading ? (
        <LoadingPage />
      ) : error ? (
        <div className="card text-center py-8">
          <p className="text-red-600">{error}</p>
          <button onClick={searchDeals} className="btn-primary mt-4">
            Try Again
          </button>
        </div>
      ) : deals.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">No deals found matching your criteria</p>
          <p className="text-sm text-gray-400 mt-2">
            Try adjusting your filters or selecting different markets
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            {deals.length} deals found
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {deals.map((deal) => (
              <DealCard key={deal.id} deal={deal} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
