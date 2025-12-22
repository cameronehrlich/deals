"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
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
  Zap,
  Database,
  Monitor,
  BarChart3,
} from "lucide-react";
import { api, ImportUrlResponse, Deal, MacroDataResponse, PropertyListing } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  getCashFlowColor,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { isElectron, scrapePropertyLocally } from "@/lib/electron";

// Inner component that uses searchParams
function AnalyzePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Form state
  const [url, setUrl] = useState("");
  const [downPaymentPct, setDownPaymentPct] = useState("20");
  const [interestRate, setInterestRate] = useState("7");

  // Results state
  const [result, setResult] = useState<ImportUrlResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Macro data state
  const [macroData, setMacroData] = useState<MacroDataResponse | null>(null);
  const [loadingRates, setLoadingRates] = useState(true);

  // Offer price adjustment state
  const [offerPrice, setOfferPrice] = useState<number | null>(null);

  // Electron detection state
  const [isElectronApp, setIsElectronApp] = useState(false);

  // Property passed from search results
  const [passedProperty, setPassedProperty] = useState<PropertyListing | null>(null);
  const [autoAnalyzing, setAutoAnalyzing] = useState(false);

  // Check if running in Electron on mount
  useEffect(() => {
    setIsElectronApp(isElectron());
  }, []);

  // Check for property data in URL params
  useEffect(() => {
    const propertyParam = searchParams.get("property");
    if (propertyParam && !passedProperty && !result) {
      try {
        const property = JSON.parse(decodeURIComponent(propertyParam)) as PropertyListing;
        setPassedProperty(property);
      } catch (e) {
        console.error("Failed to parse property data:", e);
      }
    }
  }, [searchParams, passedProperty, result]);

  // Auto-analyze when property is passed
  useEffect(() => {
    if (passedProperty && !result && !loading && !autoAnalyzing) {
      analyzePassedProperty();
    }
  }, [passedProperty]);

  const analyzePassedProperty = async () => {
    if (!passedProperty) return;

    try {
      setAutoAnalyzing(true);
      setLoading(true);
      setError(null);
      setResult(null);
      setOfferPrice(null);
      setLoadingStep("Analyzing property...");

      const response = await api.importParsed({
        address: passedProperty.address,
        city: passedProperty.city,
        state: passedProperty.state,
        zip_code: passedProperty.zip_code,
        list_price: passedProperty.price,
        bedrooms: passedProperty.bedrooms,
        bathrooms: passedProperty.bathrooms,
        sqft: passedProperty.sqft || undefined,
        property_type: passedProperty.property_type,
        source: passedProperty.source,
        source_url: passedProperty.source_url,
        down_payment_pct: parseFloat(downPaymentPct) / 100,
        interest_rate: parseFloat(interestRate) / 100,
      });

      setResult(response);
      if (response.deal?.property.list_price) {
        setOfferPrice(response.deal.property.list_price);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
      setLoadingStep("");
      setAutoAnalyzing(false);
    }
  };

  // Fetch current rates on load
  useEffect(() => {
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

      let response: ImportUrlResponse;

      // If running in Electron, use local scraping
      if (isElectronApp) {
        setLoadingStep("Scraping property locally...");

        // Scrape locally using Puppeteer
        const scrapeResult = await scrapePropertyLocally(url.trim());

        if (!scrapeResult || !scrapeResult.success || !scrapeResult.data) {
          throw new Error(scrapeResult?.error || "Failed to scrape property locally");
        }

        setLoadingStep("Analyzing with API...");

        // Send parsed data to API for analysis
        response = await api.importParsed({
          address: scrapeResult.data.address,
          city: scrapeResult.data.city,
          state: scrapeResult.data.state,
          zip_code: scrapeResult.data.zip_code,
          list_price: scrapeResult.data.list_price,
          bedrooms: scrapeResult.data.bedrooms,
          bathrooms: scrapeResult.data.bathrooms,
          sqft: scrapeResult.data.sqft,
          property_type: scrapeResult.data.property_type,
          source: scrapeResult.data.source,
          source_url: url.trim(),
          down_payment_pct: parseFloat(downPaymentPct) / 100,
          interest_rate: parseFloat(interestRate) / 100,
        });
      } else {
        // Browser mode: use server-side scraping (may be blocked)
        setLoadingStep("Fetching property details...");

        // Simulate progress steps
        const stepTimer = setTimeout(() => setLoadingStep("Getting rent estimates..."), 2000);
        const stepTimer2 = setTimeout(() => setLoadingStep("Analyzing market data..."), 4000);
        const stepTimer3 = setTimeout(() => setLoadingStep("Calculating financials..."), 6000);

        response = await api.importFromUrl({
          url: url.trim(),
          down_payment_pct: parseFloat(downPaymentPct) / 100,
          interest_rate: parseFloat(interestRate) / 100,
        });

        clearTimeout(stepTimer);
        clearTimeout(stepTimer2);
        clearTimeout(stepTimer3);
      }

      setResult(response);
      if (response.deal?.property.list_price) {
        setOfferPrice(response.deal.property.list_price);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed. Try using the Calculator for manual entry.");
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  const reset = () => {
    setUrl("");
    setResult(null);
    setError(null);
    setOfferPrice(null);
    setPassedProperty(null);
    // Clear URL params
    router.replace("/import");
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

    // Use backend score as base, adjust proportionally for offer price changes
    const originalScore = result?.deal?.score?.overall_score || 50;
    const priceDiscount = (listPrice - offerPrice) / listPrice;
    // Boost score slightly for discounted offers (better returns), max +15 points
    const dealScore = Math.round(Math.min(100, originalScore + (priceDiscount * 50)));

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

  const listPrice = result?.deal?.property.list_price || 0;
  const minPrice = Math.round(listPrice * 0.7);
  const maxPrice = listPrice;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <BarChart3 className="h-8 w-8 text-primary-600" />
          Analyze Property
        </h1>
        <p className="text-gray-500 mt-1">
          {passedProperty
            ? "Analyzing property from search results"
            : "Paste a Zillow, Redfin, or Realtor.com URL to analyze any property"
          }
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
                    step="any"
                  />
                  {loadingRates ? (
                    <div className="mt-1"><LoadingSpinner size="sm" /></div>
                  ) : macroData?.mortgage_30yr ? (
                    <button
                      type="button"
                      onClick={() => setInterestRate(macroData.mortgage_30yr!.toFixed(2))}
                      className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1 mt-1"
                    >
                      <Zap className="h-3 w-3" />
                      Use current ({macroData.mortgage_30yr.toFixed(2)}%)
                    </button>
                  ) : null}
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

              {/* Mode indicator */}
              <div className={cn(
                "mt-3 p-2 rounded-lg text-xs flex items-center gap-2",
                isElectronApp ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-600"
              )}>
                <Monitor className="h-3 w-3" />
                {isElectronApp ? (
                  <span>Desktop App - Local scraping enabled</span>
                ) : (
                  <span>Browser Mode - Server-side scraping</span>
                )}
              </div>
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
          {/* Error with Manual Entry Option */}
          {error && (
            <div className="card border-red-200 bg-red-50">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-700 font-medium">{error}</p>
                  <p className="text-red-600 text-sm mt-2">
                    Listing sites often block automated requests. Try the Calculator for manual entry instead.
                  </p>
                  <button
                    onClick={() => router.push('/calculator')}
                    className="btn-primary mt-3"
                  >
                    Open Calculator
                  </button>
                </div>
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
                  </div>
                </div>
              )}

              {/* Financial Metrics */}
              {adjustedFinancials && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-primary-600" />
                    Financial Analysis
                    {offerPrice && offerPrice !== listPrice && (
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
                  Analyze Another
                </button>
                <button
                  onClick={() => {
                    const params = new URLSearchParams();
                    if (offerPrice) params.set('price', offerPrice.toString());
                    if (result.deal?.property.estimated_rent) params.set('rent', result.deal.property.estimated_rent.toString());
                    if (result.deal?.property.zip_code) params.set('zip', result.deal.property.zip_code);
                    params.set('down', downPaymentPct);
                    params.set('rate', interestRate);
                    router.push(`/calculator?${params.toString()}`);
                  }}
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
                {loadingStep || "Fetching property data and enriching with market insights"}
              </p>
              <div className="mt-6 max-w-xs mx-auto">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    loadingStep.includes("property") ? "bg-blue-500 animate-pulse" : "bg-gray-300"
                  )} />
                  <span>Property details</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    loadingStep.includes("rent") ? "bg-blue-500 animate-pulse" : "bg-gray-300"
                  )} />
                  <span>Rent estimates (RentCast)</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    loadingStep.includes("market") ? "bg-blue-500 animate-pulse" : "bg-gray-300"
                  )} />
                  <span>Market analysis</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <div className={cn(
                    "w-2 h-2 rounded-full",
                    loadingStep.includes("financials") ? "bg-blue-500 animate-pulse" : "bg-gray-300"
                  )} />
                  <span>Financial calculations</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Wrapper with Suspense for useSearchParams
export default function ImportPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    }>
      <AnalyzePageContent />
    </Suspense>
  );
}
