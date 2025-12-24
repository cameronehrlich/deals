"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Star,
  MapPin,
  Search,
  Plus,
  TrendingUp,
  TrendingDown,
  Minus,
  Building,
  ChevronRight,
  Loader2,
  X,
  Trash2,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  PlayCircle,
  ChevronDown,
} from "lucide-react";
import { api, SavedMarket, MetroSuggestion, Job, JobStats } from "@/lib/api";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";
import { ScoreGauge } from "@/components/ScoreGauge";
import { cn, formatCurrency, getScoreBadge } from "@/lib/utils";

// Debounce hook for search
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

// Compact market card for favorites
function FavoriteMarketCard({
  market,
  onToggleFavorite,
  onDelete,
}: {
  market: SavedMarket;
  onToggleFavorite: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="card hover:shadow-lg transition-all group">
      <div className="flex items-start justify-between gap-3">
        <Link href={`/markets/${market.id}`} className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 truncate group-hover:text-primary-600 transition-colors">
              {market.name}, {market.state}
            </h3>
          </div>
          {market.metro && (
            <p className="text-sm text-gray-500 truncate">{market.metro}</p>
          )}

          {/* Score badges */}
          <div className="flex items-center gap-2 mt-3">
            <span className={cn("badge text-xs", getScoreBadge(market.cash_flow_score))}>
              CF: {market.cash_flow_score.toFixed(0)}
            </span>
            <span className={cn("badge text-xs", getScoreBadge(market.growth_score))}>
              Growth: {market.growth_score.toFixed(0)}
            </span>
          </div>
        </Link>

        <div className="flex flex-col items-end gap-2">
          <ScoreGauge score={market.overall_score} label="" size="sm" />
          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.preventDefault();
                onToggleFavorite();
              }}
              className="p-1.5 rounded-full hover:bg-yellow-50 transition-colors"
              title="Remove from favorites"
            >
              <Star className="h-4 w-4 text-yellow-500 fill-current" />
            </button>
            <button
              onClick={(e) => {
                e.preventDefault();
                if (confirm(`Delete ${market.name}, ${market.state}? This cannot be undone.`)) {
                  onDelete();
                }
              }}
              className="p-1.5 rounded-full hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
              title="Delete market"
            >
              <Trash2 className="h-4 w-4 text-red-400 hover:text-red-600" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Full market card for explore section
function ExploreMarketCard({
  market,
  onToggleFavorite,
  onDelete,
}: {
  market: SavedMarket;
  onToggleFavorite: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="card hover:shadow-lg transition-all group">
      <div className="flex items-start justify-between gap-4">
        <Link href={`/markets/${market.id}`} className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <MapPin className="h-4 w-4 text-gray-400" />
            <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
              {market.name}, {market.state}
            </h3>
          </div>
          {market.metro && (
            <p className="text-sm text-gray-500 ml-6">{market.metro}</p>
          )}

          {/* Scores */}
          <div className="flex items-center gap-3 mt-3 ml-6">
            <div className="text-center">
              <p className="text-xs text-gray-500">Cash Flow</p>
              <p className={cn("font-semibold", getScoreBadge(market.cash_flow_score).replace("badge-", "text-").replace("bg-", ""))}>
                {market.cash_flow_score.toFixed(0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Growth</p>
              <p className={cn("font-semibold", getScoreBadge(market.growth_score).replace("badge-", "text-").replace("bg-", ""))}>
                {market.growth_score.toFixed(0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Overall</p>
              <p className="font-bold text-primary-600">
                {market.overall_score.toFixed(0)}
              </p>
            </div>
          </div>
        </Link>

        <div className="flex items-center gap-1">
          <button
            onClick={(e) => {
              e.preventDefault();
              onToggleFavorite();
            }}
            className={cn(
              "p-2 rounded-full transition-colors",
              market.is_favorite
                ? "bg-yellow-50 hover:bg-yellow-100"
                : "hover:bg-gray-100"
            )}
            title={market.is_favorite ? "Remove from favorites" : "Add to favorites"}
          >
            <Star className={cn(
              "h-5 w-5",
              market.is_favorite ? "text-yellow-500 fill-current" : "text-gray-300"
            )} />
          </button>
          <button
            onClick={(e) => {
              e.preventDefault();
              if (confirm(`Delete ${market.name}, ${market.state}? This cannot be undone.`)) {
                onDelete();
              }
            }}
            className="p-2 rounded-full hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100"
            title="Delete market"
          >
            <Trash2 className="h-5 w-5 text-red-400 hover:text-red-600" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Add market modal with autocomplete
function AddMarketModal({
  isOpen,
  onClose,
  onAdd,
}: {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (name: string, state: string, metro?: string) => Promise<void>;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState<MetroSuggestion[]>([]);
  const [selectedMetro, setSelectedMetro] = useState<MetroSuggestion | null>(null);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const debouncedQuery = useDebounce(searchQuery, 300);

  // Search for metros when query changes
  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      setSearching(true);
      api.searchMetros(debouncedQuery)
        .then(setSuggestions)
        .catch(console.error)
        .finally(() => setSearching(false));
    } else {
      setSuggestions([]);
    }
  }, [debouncedQuery]);

  const handleSelectMetro = (metro: MetroSuggestion) => {
    setSelectedMetro(metro);
    setSearchQuery(metro.name);
    setShowSuggestions(false);
  };

  const handleSubmit = async () => {
    if (!selectedMetro) return;

    try {
      setAdding(true);
      await onAdd(selectedMetro.name, selectedMetro.state, selectedMetro.metro);
      setSearchQuery("");
      setSelectedMetro(null);
      onClose();
    } finally {
      setAdding(false);
    }
  };

  const handleClose = () => {
    setSearchQuery("");
    setSelectedMetro(null);
    setSuggestions([]);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 animate-fade-in">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Add New Market</h3>
          <button onClick={handleClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Search input */}
          <div className="relative">
            <label className="label">Search Markets</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setSelectedMetro(null);
                  setShowSuggestions(true);
                }}
                onFocus={() => setShowSuggestions(true)}
                placeholder="Type to search metros (e.g. Dallas, Phoenix)..."
                className="input pl-10"
                autoFocus
              />
              {searching && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 animate-spin" />
              )}
            </div>

            {/* Suggestions dropdown */}
            {showSuggestions && suggestions.length > 0 && !selectedMetro && (
              <div className="absolute z-10 w-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 max-h-64 overflow-auto">
                {suggestions.map((metro, idx) => (
                  <button
                    key={`${metro.name}-${metro.state}-${idx}`}
                    type="button"
                    onClick={() => handleSelectMetro(metro)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start gap-3 border-b border-gray-100 last:border-b-0"
                  >
                    <MapPin className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 flex items-center gap-2">
                        {metro.name}, {metro.state}
                        {metro.has_full_support && (
                          <span className="badge badge-success text-xs">Supported</span>
                        )}
                      </div>
                      <div className="text-sm text-gray-500 truncate">
                        {metro.metro}
                      </div>
                      {metro.median_rent && (
                        <div className="text-xs text-gray-400 mt-1">
                          FMR 2BR: {formatCurrency(metro.median_rent)}/mo
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* No results message */}
            {showSuggestions && searchQuery.length >= 2 && !searching && suggestions.length === 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 p-4 text-center text-gray-500">
                No markets found for "{searchQuery}"
              </div>
            )}
          </div>

          {/* Selected metro display */}
          {selectedMetro && (
            <div className="p-4 bg-primary-50 rounded-lg border border-primary-200">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-primary-900 flex items-center gap-2">
                    {selectedMetro.name}, {selectedMetro.state}
                    {selectedMetro.has_full_support && (
                      <span className="badge badge-success text-xs">Supported</span>
                    )}
                  </div>
                  <div className="text-sm text-primary-700 mt-1">
                    {selectedMetro.metro}
                  </div>
                  {selectedMetro.median_rent && (
                    <div className="text-sm text-primary-600 mt-2">
                      FMR 2BR: {formatCurrency(selectedMetro.median_rent)}/mo
                    </div>
                  )}
                </div>
                <button
                  onClick={() => {
                    setSelectedMetro(null);
                    setSearchQuery("");
                  }}
                  className="p-1 hover:bg-primary-100 rounded text-primary-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="btn-outline flex-1"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!selectedMetro || adding}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {adding ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Add Market
                </>
              )}
            </button>
          </div>

          <p className="text-xs text-gray-500 text-center">
            Market data will be automatically fetched when added
          </p>
        </div>
      </div>
    </div>
  );
}

export default function MarketsPage() {
  // State
  const [favoriteMarkets, setFavoriteMarkets] = useState<SavedMarket[]>([]);
  const [allMarkets, setAllMarkets] = useState<SavedMarket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);

  // Job state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobStats, setJobStats] = useState<JobStats | null>(null);
  const [enqueuingJobs, setEnqueuingJobs] = useState(false);
  const [showRefreshMenu, setShowRefreshMenu] = useState(false);
  const [currentBatchIds, setCurrentBatchIds] = useState<Set<string>>(new Set());

  // Fetch job status
  const fetchJobStatus = useCallback(async () => {
    try {
      const [jobList, stats] = await Promise.all([
        api.getJobs({ job_type: "enrich_market", limit: 20 }),
        api.getJobStats(),
      ]);
      setJobs(jobList);
      setJobStats(stats);
    } catch (err) {
      console.error("Failed to fetch job status:", err);
    }
  }, []);

  // Fetch markets
  const fetchMarkets = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      // Fetch all markets (already sorted by favorites first, then score)
      const all = await api.getSavedMarkets();

      // Separate favorites from the rest
      const favorites = all.filter(m => m.is_favorite);
      const others = all.filter(m => !m.is_favorite);

      setFavoriteMarkets(favorites);
      setAllMarkets(others);
    } catch (err) {
      console.error("Failed to fetch markets:", err);
      setError(err instanceof Error ? err.message : "Failed to load markets");
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, []);

  // Poll for job updates when jobs are running
  useEffect(() => {
    if (jobStats && (jobStats.pending > 0 || jobStats.running > 0)) {
      const interval = setInterval(() => {
        fetchJobStatus();
        fetchMarkets(false); // Refresh markets silently (no loading spinner)
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [jobStats, fetchJobStatus, fetchMarkets]);

  // Enqueue jobs for markets
  const handleEnqueueJobs = async (favoritesOnly: boolean) => {
    try {
      setEnqueuingJobs(true);
      const result = await api.enqueueMarketJobs({ favorites_only: favoritesOnly });
      console.log(`Enqueued ${result.jobs_created} jobs`);
      // Track this batch's job IDs for accurate progress (only if jobs were created)
      if (result.job_ids.length > 0) {
        setCurrentBatchIds(new Set(result.job_ids));
      }
      // If no jobs created but there are pending jobs, track all active jobs
      fetchJobStatus();
    } catch (err) {
      console.error("Failed to enqueue jobs:", err);
    } finally {
      setEnqueuingJobs(false);
    }
  };

  // Cancel all pending market jobs
  const handleCancelJobs = async () => {
    try {
      await api.cancelJobsByType("enrich_market");
      setCurrentBatchIds(new Set()); // Clear batch tracking
      fetchJobStatus();
    } catch (err) {
      console.error("Failed to cancel jobs:", err);
    }
  };

  useEffect(() => {
    fetchMarkets();
    fetchJobStatus();
  }, [fetchMarkets, fetchJobStatus]);

  // Toggle favorite status
  const handleToggleFavorite = async (marketId: string) => {
    try {
      const updated = await api.toggleMarketFavorite(marketId);

      // Update local state
      if (updated.is_favorite) {
        // Add to favorites
        setFavoriteMarkets(prev => [...prev, updated]);
      } else {
        // Remove from favorites
        setFavoriteMarkets(prev => prev.filter(m => m.id !== marketId));
      }

      // Update in all markets list
      setAllMarkets(prev => prev.map(m => m.id === marketId ? updated : m));
    } catch (err) {
      console.error("Failed to toggle favorite:", err);
    }
  };

  // Add new market
  const handleAddMarket = async (name: string, state: string, metro?: string) => {
    const newMarket = await api.addMarket({
      name,
      state,
      metro,
      is_favorite: true, // Auto-favorite new markets
    });

    setFavoriteMarkets(prev => [...prev, newMarket]);
    setAllMarkets(prev => [...prev, newMarket]);
  };

  // Delete market
  const handleDeleteMarket = async (marketId: string) => {
    try {
      await api.deleteMarket(marketId);
      // Remove from both lists
      setFavoriteMarkets(prev => prev.filter(m => m.id !== marketId));
      setAllMarkets(prev => prev.filter(m => m.id !== marketId));
    } catch (err) {
      console.error("Failed to delete market:", err);
      alert("Failed to delete market. Please try again.");
    }
  };

  // Filter non-favorite markets by search
  const filteredMarkets = allMarkets.filter(market => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      market.name.toLowerCase().includes(query) ||
      market.state.toLowerCase().includes(query) ||
      market.metro?.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return <LoadingPage />;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Investment Markets</h1>
          <p className="text-gray-500 mt-1">
            Your researched markets and explore new opportunities
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Refresh dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowRefreshMenu(!showRefreshMenu)}
              disabled={enqueuingJobs || !!(jobStats && (jobStats.pending > 0 || jobStats.running > 0))}
              className="btn-outline flex items-center gap-2"
            >
              <RefreshCw className={cn("h-4 w-4", enqueuingJobs && "animate-spin")} />
              Refresh
              <ChevronDown className="h-4 w-4" />
            </button>
            {showRefreshMenu && (
              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                <button
                  onClick={() => {
                    handleEnqueueJobs(true);
                    setShowRefreshMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                >
                  <Star className="h-4 w-4 text-yellow-500" />
                  Favorites Only ({favoriteMarkets.length})
                </button>
                <button
                  onClick={() => {
                    handleEnqueueJobs(false);
                    setShowRefreshMenu(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                >
                  <MapPin className="h-4 w-4 text-primary-600" />
                  All Markets ({favoriteMarkets.length + allMarkets.length})
                </button>
              </div>
            )}
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Market
          </button>
        </div>
      </div>

      {/* Job Status Panel */}
      {jobStats && (jobStats.pending > 0 || jobStats.running > 0) && (() => {
        // Calculate progress - use batch IDs if available, otherwise use global stats
        let completedJobs: number;
        let totalJobs: number;
        let runningJob: typeof jobs[0] | undefined;

        if (currentBatchIds.size > 0) {
          // Track specific batch
          const batchJobs = jobs.filter(j => currentBatchIds.has(j.id));
          completedJobs = batchJobs.filter(j => j.status === "completed").length;
          const pendingJobs = batchJobs.filter(j => j.status === "pending").length;
          const runningJobs = batchJobs.filter(j => j.status === "running").length;
          totalJobs = completedJobs + pendingJobs + runningJobs;
          runningJob = batchJobs.find(j => j.status === "running");
        } else {
          // No batch tracking - use global stats (for resumed sessions or edge cases)
          completedJobs = 0; // We don't know how many completed in this session
          totalJobs = jobStats.pending + jobStats.running;
          runningJob = jobs.find(j => j.status === "running");
        }

        const overallProgress = totalJobs > 0 ? Math.round((completedJobs / totalJobs) * 100) : 0;

        return (
          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                <div>
                  <p className="font-medium text-blue-900">
                    Refreshing market data...
                  </p>
                  <p className="text-sm text-blue-700">
                    {currentBatchIds.size > 0
                      ? `${completedJobs} of ${totalJobs} markets completed`
                      : `${jobStats.pending} pending, ${jobStats.running} running`
                    }
                  </p>
                </div>
              </div>
              <button
                onClick={handleCancelJobs}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Cancel
              </button>
            </div>
            {/* Overall progress */}
            <div className="mt-3 pt-3 border-t border-blue-200">
              <div className="flex items-center justify-between text-sm">
                <span className="text-blue-800">
                  {runningJob?.message || "Processing..."}
                </span>
                <span className="text-blue-600">
                  {currentBatchIds.size > 0
                    ? `${overallProgress}%`
                    : `${jobStats.completed} done`
                  }
                </span>
              </div>
              <div className="mt-1 h-1.5 bg-blue-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{
                    width: currentBatchIds.size > 0
                      ? `${overallProgress}%`
                      : `${Math.round((jobStats.completed / (jobStats.total - (jobStats as any).failed || 0)) * 100)}%`
                  }}
                />
              </div>
            </div>
          </div>
        );
      })()}

      {error && (
        <div className="card border-red-200 bg-red-50">
          <p className="text-red-700">{error}</p>
          <button onClick={fetchMarkets} className="btn-primary mt-3">
            Retry
          </button>
        </div>
      )}

      {/* Your Markets (Favorites) */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Star className="h-5 w-5 text-yellow-500 fill-current" />
          <h2 className="text-xl font-semibold text-gray-900">Your Markets</h2>
          <span className="text-sm text-gray-500">({favoriteMarkets.length})</span>
        </div>

        {favoriteMarkets.length === 0 ? (
          <div className="card text-center py-8 bg-gray-50">
            <Star className="h-8 w-8 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              No favorite markets yet. Star markets below to add them here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {favoriteMarkets.map((market, index) => (
              <div
                key={market.id}
                className="animate-slide-up"
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <FavoriteMarketCard
                  market={market}
                  onToggleFavorite={() => handleToggleFavorite(market.id)}
                  onDelete={() => handleDeleteMarket(market.id)}
                />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* All Markets */}
      <section>
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-4">
          <div className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900">All Markets</h2>
            <span className="text-sm text-gray-500">({filteredMarkets.length})</span>
          </div>

          {/* Search */}
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search markets..."
                className="input pl-10"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                >
                  <X className="h-4 w-4 text-gray-400" />
                </button>
              )}
            </div>
          </div>
        </div>

        {filteredMarkets.length === 0 ? (
          <div className="card text-center py-8 bg-gray-50">
            <Building className="h-8 w-8 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">
              {searchQuery
                ? `No markets matching "${searchQuery}"`
                : "All markets are in your favorites!"
              }
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredMarkets.map((market, index) => (
              <div
                key={market.id}
                className="animate-slide-up"
                style={{ animationDelay: `${Math.min(index, 10) * 30}ms` }}
              >
                <ExploreMarketCard
                  market={market}
                  onToggleFavorite={() => handleToggleFavorite(market.id)}
                  onDelete={() => handleDeleteMarket(market.id)}
                />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Add Market Modal */}
      <AddMarketModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddMarket}
      />
    </div>
  );
}
