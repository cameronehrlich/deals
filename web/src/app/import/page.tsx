"use client";

import { useState, useMemo } from "react";
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
  Info,
  MinusCircle,
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

  // Offer price adjustment state
  const [offerPrice, setOfferPrice] = useState<number | null>(null);

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
      setOfferPrice(null);

      const response = await api.importFromUrl({
        url: url.trim(),
        down_payment_pct: parseFloat(downPaymentPct) / 100,
        interest_rate: parseFloat(interestRate) / 100,
      });

      setResult(response);
      if (response.deal?.property.list_price) {
        setOfferPrice(response.deal.property.list_price);
      }
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
    setOfferPrice(null);
  };

  // Calculate adjusted financials based on offer price
  const adjustedFinancials = useMemo(() => {
    if (!result?.deal?.financials || !result?.deal?.property || offerPrice === null) {
      return null;
    }

    const listPrice = result.deal.property.list_price;
    const monthlyRent = result.deal.property.estimated_rent || 0;
    const downPct = parseFloat(downPaymentPct) / 100;
    const rate = parseFloat(interestRate) / 100;

    // Calculate new values based on offer price
    const downPayment = offerPrice * downPct;
    const closingCosts = offerPrice * 0.03;
    const totalCashInvested = downPayment + closingCosts;
    const loanAmount = offerPrice - downPayment;

    // Monthly mortgage payment (P&I)
    const monthlyRate = rate / 12;
    const numPayments = 30 * 12;
    const monthlyMortgage = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / (Math.pow(1 + monthlyRate, numPayments) - 1);

    // Operating expenses (estimated)
    const monthlyTaxes = (offerPrice * 0.012) / 12;
    const monthlyInsurance = (offerPrice * 0.005) / 12;
    const monthlyVacancy = monthlyRent * 0.08;
    const monthlyMaintenance = (offerPrice * 0.01) / 12;
    const monthlyCapex = (offerPrice * 0.01) / 12;
    const monthlyPM = monthlyRent * 0.10;

    const totalMonthlyExpenses = monthlyMortgage + monthlyTaxes + monthlyInsurance + monthlyVacancy + monthlyMaintenance + monthlyCapex + monthlyPM;
    const monthlyCashFlow = monthlyRent - totalMonthlyExpenses;
    const annualCashFlow = monthlyCashFlow * 12;

    // NOI (before debt service)
    const annualRent = monthlyRent * 12;
    const annualOperatingExpenses = (monthlyTaxes + monthlyInsurance + monthlyVacancy + monthlyMaintenance + monthlyCapex + monthlyPM) * 12;
    const noi = annualRent - annualOperatingExpenses;

    const cashOnCash = totalCashInvested > 0 ? annualCashFlow / totalCashInvested : 0;
    const capRate = offerPrice > 0 ? noi / offerPrice : 0;
    const rentToPrice = offerPrice > 0 ? (monthlyRent / offerPrice) : 0;
    const grm = monthlyRent > 0 ? offerPrice / (monthlyRent * 12) : 0;
    const breakEvenOccupancy = monthlyRent > 0 ? (totalMonthlyExpenses - monthlyVacancy) / monthlyRent : 1;

    // Calculate deal score (simplified)
    const financialScore = Math.min(100, Math.max(0, 50 + (cashOnCash * 500)));
    const dealScore = Math.round(financialScore * 0.7 + (capRate > 0.08 ? 30 : capRate * 375));

    return {
      monthlyCashFlow,
      annualCashFlow,
      cashOnCash,
      capRate,
      rentToPrice,
      totalCashInvested,
      grm,
      breakEvenOccupancy,
      dealScore,
      discount: ((listPrice - offerPrice) / listPrice) * 100,
    };
  }, [result, offerPrice, downPaymentPct, interestRate]);

  // Calculate target price for 8% CoC
  const targetPriceFor8Pct = useMemo(() => {
    if (!result?.deal?.property.estimated_rent) return null;

    const monthlyRent = result.deal.property.estimated_rent;
    const downPct = parseFloat(downPaymentPct) / 100;
    const rate = parseFloat(interestRate) / 100;

    // Binary search for price that gives ~8% CoC
    let low = 50000;
    let high = result.deal.property.list_price * 1.5;

    for (let i = 0; i < 20; i++) {
      const mid = (low + high) / 2;
      const downPayment = mid * downPct;
      const closingCosts = mid * 0.03;
      const totalCash = downPayment + closingCosts;
      const loanAmount = mid - downPayment;

      const monthlyRate = rate / 12;
      const numPayments = 360;
      const monthlyMortgage = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / (Math.pow(1 + monthlyRate, numPayments) - 1);

      const expenses = monthlyMortgage + (mid * 0.012 / 12) + (mid * 0.005 / 12) + (monthlyRent * 0.08) + (mid * 0.01 / 12) + (mid * 0.01 / 12) + (monthlyRent * 0.10);
      const cashFlow = (monthlyRent - expenses) * 12;
      const coc = cashFlow / totalCash;

      if (coc < 0.08) {
        high = mid;
      } else {
        low = mid;
      }
    }

    return Math.round(low / 1000) * 1000;
  }, [result, downPaymentPct, interestRate]);

  const listPrice = result?.deal?.property.list_price || 0;
  const minPrice = Math.round(listPrice * 0.7);
  const maxPrice = listPrice;

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
                  {adjustedFinancials && (
                    <ScoreGauge score={adjustedFinancials.dealScore} label="Deal Score" size="md" />
                  )}
                </div>

                {/* Property Details */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-gray-500">List Price</p>
                    <p className="font-bold text-lg">{formatCurrency(result.deal.property.list_price)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 flex items-center gap-1">
                      Est. Rent
                      <span
                        className="cursor-help"
                        title="Source: HUD Fair Market Rent (FMR) - Based on local area median rents by bedroom count"
                      >
                        <Info className="h-3.5 w-3.5 text-gray-400 hover:text-gray-600" />
                      </span>
                    </p>
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

              {/* Offer Price Slider */}
              {offerPrice !== null && (
                <div className="card border-primary-200 bg-primary-50">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary-600" />
                    What Should I Offer?
                  </h3>

                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600">Offer Price</span>
                        <span className="font-bold text-lg">{formatCurrency(offerPrice)}</span>
                      </div>
                      <input
                        type="range"
                        min={minPrice}
                        max={maxPrice}
                        value={offerPrice}
                        onChange={(e) => setOfferPrice(parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>{formatCurrency(minPrice)} (-30%)</span>
                        <span>{formatCurrency(maxPrice)} (List)</span>
                      </div>
                    </div>

                    {adjustedFinancials && adjustedFinancials.discount > 0 && (
                      <div className="bg-white rounded-lg p-3 border border-primary-200">
                        <p className="text-sm text-gray-600">
                          At <span className="font-bold">{formatCurrency(offerPrice)}</span> ({adjustedFinancials.discount.toFixed(1)}% below list):
                        </p>
                        <div className="grid grid-cols-3 gap-4 mt-2">
                          <div className="text-center">
                            <p className="text-xs text-gray-500">Cash Flow</p>
                            <p className={cn("font-bold", getCashFlowColor(adjustedFinancials.monthlyCashFlow))}>
                              {formatCurrency(adjustedFinancials.monthlyCashFlow)}/mo
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-500">CoC Return</p>
                            <p className="font-bold">{formatPercent(adjustedFinancials.cashOnCash)}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-500">Cap Rate</p>
                            <p className="font-bold">{formatPercent(adjustedFinancials.capRate)}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {targetPriceFor8Pct && targetPriceFor8Pct < listPrice && (
                      <p className="text-sm text-primary-700">
                        <strong>Tip:</strong> Offer around {formatCurrency(targetPriceFor8Pct)} to hit 8% cash-on-cash return
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Financial Metrics */}
              {adjustedFinancials && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-primary-600" />
                    Financial Analysis
                    {offerPrice !== listPrice && (
                      <span className="text-sm font-normal text-primary-600 ml-2">
                        (at {formatCurrency(offerPrice)} offer)
                      </span>
                    )}
                  </h3>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Monthly Cash Flow</p>
                      <p className={cn(
                        "text-xl font-bold mt-1",
                        getCashFlowColor(adjustedFinancials.monthlyCashFlow)
                      )}>
                        {formatCurrency(adjustedFinancials.monthlyCashFlow)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Cash-on-Cash</p>
                      <p className="text-xl font-bold mt-1">
                        {formatPercent(adjustedFinancials.cashOnCash)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Cap Rate</p>
                      <p className="text-xl font-bold mt-1">
                        {formatPercent(adjustedFinancials.capRate)}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Rent-to-Price</p>
                      <p className="text-xl font-bold mt-1">
                        {formatPercent(adjustedFinancials.rentToPrice)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                    <div>
                      <p className="text-sm text-gray-500">Total Cash Needed</p>
                      <p className="font-semibold">
                        {formatCurrency(adjustedFinancials.totalCashInvested)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Annual Cash Flow</p>
                      <p className={cn(
                        "font-semibold",
                        getCashFlowColor(adjustedFinancials.annualCashFlow)
                      )}>
                        {formatCurrency(adjustedFinancials.annualCashFlow)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">GRM</p>
                      <p className="font-semibold">
                        {adjustedFinancials.grm.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Break-even Occupancy</p>
                      <p className="font-semibold">
                        {formatPercent(adjustedFinancials.breakEvenOccupancy)}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Pros and Cons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Pros - always show */}
                <div className={cn(
                  "card",
                  result.deal.pros.length > 0 ? "border-green-200" : "border-gray-200"
                )}>
                  <h3 className={cn(
                    "font-semibold mb-3 flex items-center gap-2",
                    result.deal.pros.length > 0 ? "text-green-800" : "text-gray-400"
                  )}>
                    <CheckCircle className="h-5 w-5" />
                    Pros
                  </h3>
                  {result.deal.pros.length > 0 ? (
                    <ul className="space-y-2">
                      {result.deal.pros.map((pro, i) => (
                        <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          {pro}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-400 italic">No standout pros identified</p>
                  )}
                </div>

                {/* Cons - always show */}
                <div className={cn(
                  "card",
                  result.deal.cons.length > 0 ? "border-red-200" : "border-gray-200"
                )}>
                  <h3 className={cn(
                    "font-semibold mb-3 flex items-center gap-2",
                    result.deal.cons.length > 0 ? "text-red-800" : "text-gray-400"
                  )}>
                    {result.deal.cons.length > 0 ? (
                      <AlertTriangle className="h-5 w-5" />
                    ) : (
                      <MinusCircle className="h-5 w-5" />
                    )}
                    Cons
                  </h3>
                  {result.deal.cons.length > 0 ? (
                    <ul className="space-y-2">
                      {result.deal.cons.map((con, i) => (
                        <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                          {con}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-400 italic">No significant cons identified</p>
                  )}
                </div>
              </div>

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
