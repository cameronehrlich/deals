"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Search, SlidersHorizontal, Zap, Database, TrendingUp, Building } from "lucide-react";
import { api, Deal, Market, MacroDataResponse } from "@/lib/api";
import { DealCard } from "@/components/DealCard";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";

const STRATEGIES = [
  { value: "cash_flow", label: "Cash Flow" },
  { value: "appreciation", label: "Appreciation" },
  { value: "value_add", label: "Value Add" },
];

function DealsContent() {
  const searchParams = useSearchParams();
  const initialMarket = searchParams.get("markets") || "";

  const [deals, setDeals] = useState<Deal[]>([]);
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [macroData, setMacroData] = useState<MacroDataResponse | null>(null);
  const [loadingRates, setLoadingRates] = useState(true);

  // Filters
  const [selectedMarkets, setSelectedMarkets] = useState(initialMarket);
  const [strategy, setStrategy] = useState("cash_flow");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [minBeds, setMinBeds] = useState("2");
  const [minCashFlow, setMinCashFlow] = useState<string>("");
  const [downPayment, setDownPayment] = useState("25");
  const [interestRate, setInterestRate] = useState("7");
  const [showFilters, setShowFilters] = useState(false);

  // Fetch markets for dropdown and current rates
  useEffect(() => {
    api.getMarkets({ limit: 20 }).then((res) => setMarkets(res.markets));

    // Fetch current rates
    async function fetchRates() {
      try {
        const data = await api.getMacroData();
        setMacroData(data);
        if (data.mortgage_30yr) {
          setInterestRate(data.mortgage_30yr.toFixed(2));
        }
      } catch (err) {
        console.error("Failed to fetch rates:", err);
      } finally {
        setLoadingRates(false);
      }
    }
    fetchRates();
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
                <label className="label flex items-center justify-between">
                  <span>Interest Rate (%)</span>
                  {loadingRates ? (
                    <LoadingSpinner size="sm" />
                  ) : macroData?.mortgage_30yr ? (
                    <button
                      type="button"
                      onClick={() => setInterestRate(macroData.mortgage_30yr!.toFixed(2))}
                      className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
                    >
                      <Zap className="h-3 w-3" />
                      Current
                    </button>
                  ) : null}
                </label>
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

            {/* Current Rate Info */}
            {macroData && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Database className="h-4 w-4 text-blue-500" />
                  <span>Live FRED data:</span>
                  <span className="font-medium">30yr: {macroData.mortgage_30yr?.toFixed(2)}%</span>
                  <span className="text-gray-400">|</span>
                  <span className="font-medium">15yr: {macroData.mortgage_15yr?.toFixed(2)}%</span>
                  <span className="text-gray-400">|</span>
                  <span className="font-medium">Fed: {macroData.fed_funds_rate?.toFixed(2)}%</span>
                </div>
              </div>
            )}
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
        <div className="card text-center py-12 animate-fade-in">
          <Building className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No deals found</h3>
          <p className="text-gray-500 mt-1 max-w-md mx-auto">
            No properties match your current criteria. Try adjusting your filters or selecting different markets.
          </p>
          <button onClick={searchDeals} className="btn-primary mt-4">
            <Search className="h-4 w-4 inline mr-2" />
            Try Again
          </button>
        </div>
      ) : (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {deals.length} deals found
            </p>
            {macroData && (
              <p className="text-xs text-gray-400">
                Using {macroData.mortgage_30yr?.toFixed(2)}% mortgage rate
              </p>
            )}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {deals.map((deal, index) => (
              <div key={deal.id} className="animate-slide-up" style={{ animationDelay: `${index * 50}ms` }}>
                <DealCard deal={deal} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function DealsPage() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <DealsContent />
    </Suspense>
  );
}
