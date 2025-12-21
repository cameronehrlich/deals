"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Link2,
  ArrowRight,
  Home,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Loader2,
  TrendingUp,
  MapPin,
} from "lucide-react";
import { api, ImportUrlResponse, Deal } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  getCashFlowColor,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function ImportPage() {
  const router = useRouter();

  // Form state
  const [url, setUrl] = useState("");
  const [downPaymentPct, setDownPaymentPct] = useState("25");
  const [interestRate, setInterestRate] = useState("7");

  // Results state
  const [result, setResult] = useState<ImportUrlResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setError("Please enter a property URL");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await api.importFromUrl({
        url: url.trim(),
        down_payment_pct: parseFloat(downPaymentPct) / 100,
        interest_rate: parseFloat(interestRate) / 100,
      });

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setUrl("");
    setResult(null);
    setError(null);
  };

  const exampleUrls = [
    "https://www.zillow.com/homedetails/...",
    "https://www.redfin.com/...",
    "https://www.realtor.com/...",
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Link2 className="h-8 w-8 text-primary-600" />
          Import Property
        </h1>
        <p className="text-gray-500 mt-1">
          Paste a Zillow, Redfin, or Realtor.com URL to analyze any property
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Import Form */}
        <div className="lg:col-span-1 space-y-6">
          <form onSubmit={handleImport} className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Property URL
            </h2>

            <div className="space-y-4">
              <div>
                <label className="label">Listing URL</label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="input"
                  placeholder="https://www.zillow.com/homedetails/..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Supports Zillow, Redfin, and Realtor.com
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Down Payment (%)</label>
                  <input
                    type="number"
                    value={downPaymentPct}
                    onChange={(e) => setDownPaymentPct(e.target.value)}
                    className="input"
                    min="5"
                    max="100"
                  />
                </div>
                <div>
                  <label className="label">Interest Rate (%)</label>
                  <input
                    type="number"
                    value={interestRate}
                    onChange={(e) => setInterestRate(e.target.value)}
                    className="input"
                    min="1"
                    max="20"
                    step="0.25"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !url.trim()}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <ArrowRight className="h-4 w-4" />
                    Import & Analyze
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Instructions */}
          <div className="card bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              How it works
            </h3>
            <ol className="space-y-2 text-sm text-gray-600">
              <li className="flex gap-2">
                <span className="font-semibold text-primary-600">1.</span>
                Find a property on Zillow, Redfin, or Realtor.com
              </li>
              <li className="flex gap-2">
                <span className="font-semibold text-primary-600">2.</span>
                Copy the listing URL from your browser
              </li>
              <li className="flex gap-2">
                <span className="font-semibold text-primary-600">3.</span>
                Paste it above and click Import
              </li>
              <li className="flex gap-2">
                <span className="font-semibold text-primary-600">4.</span>
                Get instant cash flow analysis
              </li>
            </ol>
          </div>

          {/* Data Sources */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Data Sources
            </h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Property details from listing
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Rent estimates (RentCast / HUD FMR)
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Market metrics (Redfin Data Center)
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-500" />
                Macro rates (FRED)
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Error */}
          {error && (
            <div className="card border-red-200 bg-red-50">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Success Result */}
          {result && result.success && result.deal && (
            <>
              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="card border-yellow-200 bg-yellow-50">
                  <h3 className="font-semibold text-yellow-800 mb-2">Warnings</h3>
                  <ul className="space-y-1">
                    {result.warnings.map((warning, i) => (
                      <li key={i} className="text-sm text-yellow-700 flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Property Overview */}
              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                      <span className="badge-blue">{result.source}</span>
                      <span>{result.deal.property.property_type.replace(/_/g, ' ')}</span>
                    </div>
                    <h2 className="text-xl font-bold text-gray-900">
                      {result.deal.property.address}
                    </h2>
                    <p className="text-gray-600 flex items-center gap-1 mt-1">
                      <MapPin className="h-4 w-4" />
                      {result.deal.property.city}, {result.deal.property.state} {result.deal.property.zip_code}
                    </p>
                  </div>
                  {result.deal.score && (
                    <ScoreGauge score={result.deal.score.overall_score} label="Deal Score" size="md" />
                  )}
                </div>

                {/* Property Details */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-gray-500">List Price</p>
                    <p className="font-bold text-lg">{formatCurrency(result.deal.property.list_price)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Est. Rent</p>
                    <p className="font-bold text-lg">
                      {result.deal.property.estimated_rent
                        ? formatCurrency(result.deal.property.estimated_rent) + '/mo'
                        : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Beds / Baths</p>
                    <p className="font-bold text-lg">
                      {result.deal.property.bedrooms} / {result.deal.property.bathrooms}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Sqft</p>
                    <p className="font-bold text-lg">
                      {result.deal.property.sqft?.toLocaleString() || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Financial Metrics */}
              {result.deal.financials && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-primary-600" />
                    Financial Analysis
                  </h3>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Monthly Cash Flow</p>
                      <p className={cn(
                        "text-xl font-bold mt-1",
                        getCashFlowColor(result.deal.financials.monthly_cash_flow)
                      )}>
                        {formatCurrency(result.deal.financials.monthly_cash_flow)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Cash-on-Cash</p>
                      <p className="text-xl font-bold mt-1">
                        {formatPercent(result.deal.financials.cash_on_cash_return)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Cap Rate</p>
                      <p className="text-xl font-bold mt-1">
                        {formatPercent(result.deal.financials.cap_rate)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Rent-to-Price</p>
                      <p className="text-xl font-bold mt-1">
                        {formatPercent(result.deal.financials.rent_to_price_ratio)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                    <div>
                      <p className="text-sm text-gray-500">Total Cash Needed</p>
                      <p className="font-semibold">
                        {formatCurrency(result.deal.financials.total_cash_invested)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Annual Cash Flow</p>
                      <p className={cn(
                        "font-semibold",
                        getCashFlowColor(result.deal.financials.annual_cash_flow)
                      )}>
                        {formatCurrency(result.deal.financials.annual_cash_flow)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">GRM</p>
                      <p className="font-semibold">
                        {result.deal.financials.gross_rent_multiplier.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Break-even Occupancy</p>
                      <p className="font-semibold">
                        {formatPercent(result.deal.financials.break_even_occupancy)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Pros and Cons */}
              {(result.deal.pros.length > 0 || result.deal.cons.length > 0) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.deal.pros.length > 0 && (
                    <div className="card border-green-200">
                      <h3 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                        <CheckCircle className="h-5 w-5" />
                        Pros
                      </h3>
                      <ul className="space-y-2">
                        {result.deal.pros.map((pro, i) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            {pro}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.deal.cons.length > 0 && (
                    <div className="card border-red-200">
                      <h3 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5" />
                        Cons
                      </h3>
                      <ul className="space-y-2">
                        {result.deal.cons.map((con, i) => (
                          <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                            <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                            {con}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={reset}
                  className="btn-outline"
                >
                  Import Another
                </button>
                <button
                  onClick={() => router.push('/calculator')}
                  className="btn-primary"
                >
                  Open in Calculator
                </button>
              </div>
            </>
          )}

          {/* Failed Import */}
          {result && !result.success && (
            <div className="card border-red-200 bg-red-50">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <p className="text-red-700">{result.message}</p>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!result && !error && !loading && (
            <div className="card text-center py-12">
              <Home className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Paste a property URL to get started
              </h3>
              <p className="text-gray-500 mt-1 max-w-md mx-auto">
                Import any listing from Zillow, Redfin, or Realtor.com to see
                detailed cash flow analysis and market data
              </p>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="card text-center py-12">
              <LoadingSpinner size="lg" />
              <h3 className="text-lg font-medium text-gray-900 mt-4">
                Importing property...
              </h3>
              <p className="text-gray-500 mt-1">
                Fetching property data and enriching with market insights
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
