"use client";

import { useEffect, useState } from "react";
import { api, Market } from "@/lib/api";
import { MarketCard } from "@/components/MarketCard";
import { LoadingPage } from "@/components/LoadingSpinner";

type SortOption = "overall" | "cash_flow" | "growth" | "affordability";

export default function MarketsPage() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>("overall");
  const [landlordFriendlyOnly, setLandlordFriendlyOnly] = useState(false);

  useEffect(() => {
    async function fetchMarkets() {
      try {
        setLoading(true);
        const res = await api.getMarkets({
          sort_by: sortBy,
          limit: 20,
          landlord_friendly: landlordFriendlyOnly || undefined,
        });
        setMarkets(res.markets);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load markets");
      } finally {
        setLoading(false);
      }
    }

    fetchMarkets();
  }, [sortBy, landlordFriendlyOnly]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Investment Markets</h1>
        <p className="text-gray-500 mt-1">
          Compare and rank markets for real estate investment
        </p>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="label">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="input w-48"
            >
              <option value="overall">Overall Score</option>
              <option value="cash_flow">Cash Flow Potential</option>
              <option value="growth">Growth Potential</option>
              <option value="affordability">Affordability</option>
            </select>
          </div>

          <div className="flex items-center gap-2 pt-6">
            <input
              type="checkbox"
              id="landlord-friendly"
              checked={landlordFriendlyOnly}
              onChange={(e) => setLandlordFriendlyOnly(e.target.checked)}
              className="h-4 w-4 text-primary-600 rounded border-gray-300"
            />
            <label htmlFor="landlord-friendly" className="text-sm text-gray-700">
              Landlord-friendly states only
            </label>
          </div>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <LoadingPage />
      ) : error ? (
        <div className="card text-center py-8">
          <p className="text-red-600">{error}</p>
        </div>
      ) : (
        <div className="space-y-4 animate-fade-in">
          <p className="text-sm text-gray-500">
            {markets.length} markets found
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {markets.map((market, index) => (
              <div key={market.id} className="animate-slide-up" style={{ animationDelay: `${index * 50}ms` }}>
                <MarketCard market={market} rank={index + 1} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
