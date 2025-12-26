"use client";

/**
 * Saved Property Detail Page (Enriched Tier)
 *
 * This page displays a saved property with full analysis data,
 * location insights, and user customizations. It provides FULL
 * feature parity with the Analyze page plus persistence.
 */

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Star,
  Trash2,
  Database,
  Edit3,
  Save,
  X,
  DollarSign,
  TrendingUp,
  MapPin,
  Bed,
  Bath,
  Square,
  Calendar,
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Zap,
  Loader2,
  Plus,
  RefreshCw,
  Footprints,
  Train,
  Bike,
  Volume2,
  GraduationCap,
  Droplets,
  ShieldAlert,
  ShieldCheck,
  Calculator,
  Home,
} from "lucide-react";
import { api, SavedProperty, MacroDataResponse } from "@/lib/api";
import {
  cn,
  formatCurrency,
  formatPercent,
  getCashFlowColor,
} from "@/lib/utils";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";
import { ScoreGauge } from "@/components/ScoreGauge";
import { ImageCarousel } from "@/components/ImageCarousel";

export default function SavedPropertyDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const propertyId = params.id;

  // Data state
  const [savedProperty, setSavedProperty] = useState<SavedProperty | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Macro data for current rates
  const [macroData, setMacroData] = useState<MacroDataResponse | null>(null);
  const [loadingRates, setLoadingRates] = useState(true);

  // Financing inputs (interactive!)
  const [downPaymentPct, setDownPaymentPct] = useState("20");
  const [interestRate, setInterestRate] = useState("7");

  // Offer price slider
  const [offerPrice, setOfferPrice] = useState<number | null>(null);

  // Action states
  const [locationLoading, setLocationLoading] = useState(false);
  const [reenriching, setReenriching] = useState(false);
  const [savingScenario, setSavingScenario] = useState(false);

  // Notes editing
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesValue, setNotesValue] = useState("");

  // Fetch current rates
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

  // Fetch saved property and analysis
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [property, analysisData] = await Promise.all([
          api.getSavedProperty(propertyId),
          api.getSavedPropertyAnalysis(propertyId).catch(() => null),
        ]);

        setSavedProperty(property);
        setAnalysis(analysisData);
        setNotesValue(property.notes || "");

        // Initialize offer price to list price
        if (property.list_price) {
          setOfferPrice(property.list_price);
        }

        // If analysis has financing data, use those values
        if (analysisData?.financials?.loan?.down_payment_pct) {
          setDownPaymentPct((analysisData.financials.loan.down_payment_pct * 100).toFixed(0));
        }
        if (analysisData?.financials?.loan?.interest_rate) {
          setInterestRate((analysisData.financials.loan.interest_rate * 100).toFixed(2));
        }
      } catch (err) {
        console.error("Failed to fetch saved property:", err);
        setError(err instanceof Error ? err.message : "Failed to load property");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [propertyId]);

  // Auto-fetch location data if property has no location data
  // The backend will geocode if coordinates are missing
  useEffect(() => {
    async function autoFetchLocationData() {
      if (!savedProperty) return;

      // Check if we already have location data
      const hasLocationData = savedProperty.location_data && (
        savedProperty.location_data.walk_score !== undefined ||
        savedProperty.location_data.flood_zone ||
        savedProperty.location_data.schools?.length
      );

      // Auto-fetch if no location data (backend will geocode if needed)
      if (!hasLocationData && !locationLoading) {
        try {
          setLocationLoading(true);
          const updated = await api.refreshPropertyLocationData(savedProperty.id);
          setSavedProperty(updated);
        } catch (err) {
          console.error("Failed to auto-fetch location data:", err);
          // Silently fail - user can manually refresh if needed
        } finally {
          setLocationLoading(false);
        }
      }
    }

    autoFetchLocationData();
  }, [savedProperty?.id, savedProperty?.location_data]);

  // Helper function to calculate mortgage payment
  const calculateMortgagePayment = (principal: number, annualRate: number, years: number = 30) => {
    if (principal <= 0) return 0;
    const monthlyRate = annualRate / 12;
    const numPayments = years * 12;
    if (monthlyRate === 0) return principal / numPayments;
    return principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1);
  };

  // Calculate adjusted financials based on offer price and financing inputs
  const adjustedFinancials = useMemo(() => {
    if (!savedProperty || offerPrice === null) return null;

    const listPrice = savedProperty.list_price || 0;
    const monthlyRent = savedProperty.estimated_rent || 0;
    const downPct = parseFloat(downPaymentPct) / 100;
    const rate = parseFloat(interestRate) / 100;

    // Calculate new values based on offer price
    const downPayment = offerPrice * downPct;
    const closingCosts = offerPrice * 0.03;
    const totalCashInvested = downPayment + closingCosts;
    const loanAmount = offerPrice - downPayment;

    // Monthly mortgage payment (P&I)
    const monthlyMortgage = calculateMortgagePayment(loanAmount, rate);

    // Operating expenses (estimated)
    const monthlyTaxes = (offerPrice * 0.012) / 12;
    const monthlyInsurance = (offerPrice * 0.005) / 12;
    const vacancyRate = 0.08;
    const monthlyVacancy = monthlyRent * vacancyRate;
    const monthlyMaintenance = (offerPrice * 0.01) / 12;
    const monthlyCapex = (offerPrice * 0.01) / 12;
    const monthlyPM = monthlyRent * 0.1;

    const totalMonthlyExpenses =
      monthlyMortgage +
      monthlyTaxes +
      monthlyInsurance +
      monthlyVacancy +
      monthlyMaintenance +
      monthlyCapex +
      monthlyPM;
    const monthlyCashFlow = monthlyRent - totalMonthlyExpenses;
    const annualCashFlow = monthlyCashFlow * 12;

    // NOI (before debt service)
    const annualRent = monthlyRent * 12;
    const annualOperatingExpenses =
      (monthlyTaxes +
        monthlyInsurance +
        monthlyVacancy +
        monthlyMaintenance +
        monthlyCapex +
        monthlyPM) *
      12;
    const noi = annualRent - annualOperatingExpenses;

    const cashOnCash = totalCashInvested > 0 ? annualCashFlow / totalCashInvested : 0;
    const capRate = offerPrice > 0 ? noi / offerPrice : 0;
    const rentToPrice = offerPrice > 0 ? monthlyRent / offerPrice : 0;
    const grm = monthlyRent > 0 ? offerPrice / (monthlyRent * 12) : 0;
    const breakEvenOccupancy =
      monthlyRent > 0 ? (totalMonthlyExpenses - monthlyVacancy) / monthlyRent : 1;

    // Adjust score based on discount
    const originalScore = savedProperty.overall_score || 50;
    const priceDiscount = (listPrice - offerPrice) / listPrice;
    const dealScore = Math.round(Math.min(100, originalScore + priceDiscount * 50));

    // ===== STRESS TEST / SENSITIVITY ANALYSIS =====
    // Helper to calculate cash flow with different params
    const calcCashFlow = (customRate?: number, customVacancy?: number, customRent?: number) => {
      const r = customRate !== undefined ? customRate : rate;
      const v = customVacancy !== undefined ? customVacancy : vacancyRate;
      const rent = customRent !== undefined ? customRent : monthlyRent;

      const mortgage = calculateMortgagePayment(loanAmount, r);
      const vacancy = rent * v;
      const pm = rent * 0.1;

      const expenses = mortgage + monthlyTaxes + monthlyInsurance + vacancy + monthlyMaintenance + monthlyCapex + pm;
      return rent - expenses;
    };

    // Base case
    const baseCashFlow = monthlyCashFlow;

    // Rate stress scenarios
    const rateIncrease1pct = calcCashFlow(rate + 0.01);
    const rateIncrease2pct = calcCashFlow(rate + 0.02);

    // Vacancy stress scenarios
    const vacancy10pct = calcCashFlow(undefined, 0.10);
    const vacancy15pct = calcCashFlow(undefined, 0.15);

    // Rent decrease scenario
    const rentDecrease5pct = calcCashFlow(undefined, undefined, monthlyRent * 0.95);

    // Combined stress scenarios
    const moderateStress = calcCashFlow(rate + 0.01, 0.10, monthlyRent * 0.97);
    const severeStress = calcCashFlow(rate + 0.02, 0.15, monthlyRent * 0.90);

    // Break-even calculations
    // Break-even interest rate (binary search)
    let breakEvenRate: number | null = null;
    if (baseCashFlow > 0) {
      let low = rate, high = rate + 0.20;
      for (let i = 0; i < 20; i++) {
        const mid = (low + high) / 2;
        const cf = calcCashFlow(mid);
        if (cf > 0) low = mid;
        else high = mid;
      }
      breakEvenRate = (low + high) / 2;
    }

    // Break-even vacancy
    let breakEvenVacancy: number | null = null;
    if (baseCashFlow > 0) {
      let low = vacancyRate, high = 1;
      for (let i = 0; i < 20; i++) {
        const mid = (low + high) / 2;
        const cf = calcCashFlow(undefined, mid);
        if (cf > 0) low = mid;
        else high = mid;
      }
      breakEvenVacancy = (low + high) / 2;
    }

    // Break-even rent
    let breakEvenRent: number | null = null;
    if (baseCashFlow > 0 && monthlyRent > 0) {
      let low = 0, high = monthlyRent;
      for (let i = 0; i < 20; i++) {
        const mid = (low + high) / 2;
        const cf = calcCashFlow(undefined, undefined, mid);
        if (cf > 0) high = mid;
        else low = mid;
      }
      breakEvenRent = (low + high) / 2;
    }

    // Determine risk rating
    let riskRating: 'low' | 'medium' | 'high' = 'low';
    if (severeStress < -500 || baseCashFlow < 0) {
      riskRating = 'high';
    } else if (moderateStress < 0 || baseCashFlow < 200) {
      riskRating = 'medium';
    }

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
      downPayment,
      loanAmount,
      monthlyMortgage,
      closingCosts,
      // Stress test results
      sensitivity: {
        baseCashFlow,
        rateIncrease1pct,
        rateIncrease2pct,
        vacancy10pct,
        vacancy15pct,
        rentDecrease5pct,
        moderateStress,
        severeStress,
        survivesModerate: moderateStress >= 0,
        survivesSevere: severeStress >= 0,
        breakEvenRate,
        breakEvenVacancy,
        breakEvenRent,
        riskRating,
      },
    };
  }, [savedProperty, offerPrice, downPaymentPct, interestRate]);

  // Handlers
  const handleToggleFavorite = async () => {
    if (!savedProperty) return;
    try {
      const updated = await api.togglePropertyFavorite(savedProperty.id);
      setSavedProperty(updated);
    } catch (err) {
      console.error("Failed to toggle favorite:", err);
    }
  };

  const handleDelete = async () => {
    if (!savedProperty) return;
    if (!confirm("Are you sure you want to delete this saved property?")) return;

    try {
      await api.deleteSavedProperty(savedProperty.id);
      router.push("/saved");
    } catch (err) {
      console.error("Failed to delete property:", err);
    }
  };

  const handleRefreshLocation = async () => {
    if (!savedProperty) return;
    try {
      setLocationLoading(true);
      const updated = await api.refreshPropertyLocationData(savedProperty.id);
      setSavedProperty(updated);
    } catch (err) {
      console.error("Failed to refresh location data:", err);
    } finally {
      setLocationLoading(false);
    }
  };

  const handleReenrich = async () => {
    if (!savedProperty) return;
    try {
      setReenriching(true);
      const updated = await api.reenrichProperty(savedProperty.id);
      setSavedProperty(updated);
      const newAnalysis = await api.getSavedPropertyAnalysis(savedProperty.id).catch(() => null);
      setAnalysis(newAnalysis);
    } catch (err) {
      console.error("Failed to re-enrich property:", err);
    } finally {
      setReenriching(false);
    }
  };

  const handleSaveScenario = async () => {
    if (!savedProperty || !adjustedFinancials || offerPrice === null) return;

    const discount = adjustedFinancials.discount;
    const scenarioName =
      discount > 0
        ? `${discount.toFixed(0)}% below asking`
        : discount < 0
        ? `${Math.abs(discount).toFixed(0)}% above asking`
        : "At asking price";

    try {
      setSavingScenario(true);
      // Backend calculates the financials from offer_price and loan terms
      const updated = await api.addPropertyScenario(savedProperty.id, {
        name: scenarioName,
        offer_price: offerPrice,
        down_payment_pct: parseFloat(downPaymentPct) / 100,
        interest_rate: parseFloat(interestRate) / 100,
      });
      setSavedProperty(updated);
    } catch (err) {
      console.error("Failed to save scenario:", err);
    } finally {
      setSavingScenario(false);
    }
  };

  const handleSaveNotes = async () => {
    if (!savedProperty) return;
    try {
      const updated = await api.updateSavedProperty(savedProperty.id, {
        note: notesValue,
      });
      setSavedProperty(updated);
      setEditingNotes(false);
    } catch (err) {
      console.error("Failed to save notes:", err);
    }
  };

  if (loading) {
    return <LoadingPage />;
  }

  if (error || !savedProperty) {
    return (
      <div className="space-y-6">
        <Link
          href="/saved"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Saved Properties
        </Link>
        <div className="card border-red-200 bg-red-50 text-center py-8">
          <p className="text-red-700">{error || "Property not found"}</p>
          <Link href="/saved" className="btn-primary mt-4 inline-block">
            Go Back
          </Link>
        </div>
      </div>
    );
  }

  const listPrice = savedProperty.list_price || 0;
  const minPrice = Math.round(listPrice * 0.7);
  const maxPrice = listPrice;

  // Extract pros/cons from analysis
  const pros = analysis?.pros || [];
  const cons = analysis?.cons || [];
  const redFlags = analysis?.red_flags || [];

  // Location data
  const locationData = savedProperty.location_data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <Link
          href="/saved"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Saved Properties
        </Link>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-primary-600">
            <Database className="h-4 w-4" />
            <span>Saved Property</span>
            {savedProperty.last_analyzed && (
              <span className="text-gray-400">
                | Analyzed {new Date(savedProperty.last_analyzed).toLocaleDateString()}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleReenrich}
              disabled={reenriching}
              className="btn-outline text-sm flex items-center gap-1"
            >
              {reenriching ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Re-enriching...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Re-enrich
                </>
              )}
            </button>
            <button
              onClick={handleToggleFavorite}
              className={cn(
                "btn-outline text-sm flex items-center gap-1",
                savedProperty.is_favorite && "text-yellow-600 border-yellow-300"
              )}
            >
              <Star
                className={cn("h-4 w-4", savedProperty.is_favorite && "fill-current")}
              />
              {savedProperty.is_favorite ? "Favorited" : "Favorite"}
            </button>
            <button
              onClick={handleDelete}
              className="btn-outline text-sm text-red-600 border-red-200 hover:bg-red-50 flex items-center gap-1"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Sidebar - Financing Controls */}
        <div className="lg:col-span-1 space-y-6">
          {/* Financing Inputs */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Financing Assumptions</h2>
            <div className="space-y-4">
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
                    <div className="mt-1">
                      <LoadingSpinner size="sm" />
                    </div>
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
            </div>
          </div>

          {/* What Should I Offer Slider */}
          {offerPrice !== null && listPrice > 0 && (
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

                {adjustedFinancials && adjustedFinancials.discount !== 0 && (
                  <p className="text-sm text-center text-primary-700 font-medium">
                    {adjustedFinancials.discount > 0
                      ? `${adjustedFinancials.discount.toFixed(0)}% below asking`
                      : `${Math.abs(adjustedFinancials.discount).toFixed(0)}% above asking`}
                  </p>
                )}

                <button
                  onClick={handleSaveScenario}
                  disabled={savingScenario}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {savingScenario ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      Save This Scenario
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Location Data Status */}
          <div className="card bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Location Data
            </h3>
            {locationLoading ? (
              <div className="flex items-center justify-center gap-2 py-3 text-sm text-gray-600">
                <Loader2 className="h-4 w-4 animate-spin text-primary-500" />
                <span>Loading location insights...</span>
              </div>
            ) : locationData ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Status</span>
                  <span className="text-green-600 font-medium flex items-center gap-1">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Loaded
                  </span>
                </div>
                {savedProperty.location_data_fetched && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Updated</span>
                    <span className="text-gray-700">
                      {new Date(savedProperty.location_data_fetched).toLocaleDateString()}
                    </span>
                  </div>
                )}
                <button
                  onClick={handleRefreshLocation}
                  disabled={locationLoading}
                  className="w-full text-xs text-gray-500 hover:text-primary-600 flex items-center justify-center gap-1 mt-2 pt-2 border-t"
                >
                  <RefreshCw className="h-3 w-3" />
                  Refresh data
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-gray-500">
                  {savedProperty.latitude && savedProperty.longitude
                    ? "Location data not yet fetched for this property."
                    : "Click to geocode address and fetch location data."}
                </p>
                <button
                  onClick={handleRefreshLocation}
                  disabled={locationLoading}
                  className="btn-outline w-full text-sm flex items-center justify-center gap-2"
                >
                  <MapPin className="h-4 w-4" />
                  Fetch Location Data
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Photo Carousel */}
          {savedProperty.photos && savedProperty.photos.length > 0 && (
            <div className="card p-0 overflow-hidden">
              <div className="h-64 sm:h-80">
                <ImageCarousel
                  images={savedProperty.photos}
                  alt={savedProperty.address}
                />
              </div>
            </div>
          )}

          {/* Property Header */}
          <div className="card">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                  <span className="badge-blue">{savedProperty.source || "import"}</span>
                  <span>{savedProperty.property_type?.replace(/_/g, " ")}</span>
                  {savedProperty.days_on_market !== undefined && (
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      {savedProperty.days_on_market} days
                    </span>
                  )}
                </div>
                <h2 className="text-xl font-bold text-gray-900">{savedProperty.address}</h2>
                <p className="text-gray-600 flex items-center gap-1 mt-1">
                  <MapPin className="h-4 w-4" />
                  {savedProperty.city}, {savedProperty.state} {savedProperty.zip_code}
                </p>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-gray-500">List Price</p>
                    <p className="font-bold text-lg">{formatCurrency(listPrice)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Est. Rent</p>
                    <p className="font-bold text-lg">
                      {savedProperty.estimated_rent
                        ? formatCurrency(savedProperty.estimated_rent) + "/mo"
                        : "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Beds / Baths</p>
                    <p className="font-bold text-lg flex items-center gap-2">
                      <Bed className="h-4 w-4 text-gray-400" />
                      {savedProperty.bedrooms || "?"} / {savedProperty.bathrooms || "?"}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Sqft</p>
                    <p className="font-bold text-lg flex items-center gap-2">
                      <Square className="h-4 w-4 text-gray-400" />
                      {savedProperty.sqft?.toLocaleString() || "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Score Gauge */}
              {adjustedFinancials && (
                <ScoreGauge score={adjustedFinancials.dealScore} label="Deal Score" size="md" />
              )}
            </div>
          </div>

          {/* Financial Analysis */}
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
                  <p
                    className={cn(
                      "text-xl font-bold mt-1",
                      getCashFlowColor(adjustedFinancials.monthlyCashFlow)
                    )}
                  >
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
                  <p className="font-semibold">{formatCurrency(adjustedFinancials.totalCashInvested)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Annual Cash Flow</p>
                  <p
                    className={cn("font-semibold", getCashFlowColor(adjustedFinancials.annualCashFlow))}
                  >
                    {formatCurrency(adjustedFinancials.annualCashFlow)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">GRM</p>
                  <p className="font-semibold">{adjustedFinancials.grm.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Break-even Occupancy</p>
                  <p className="font-semibold">{formatPercent(adjustedFinancials.breakEvenOccupancy)}</p>
                </div>
              </div>
            </div>
          )}

          {/* Stress Test / Sensitivity Analysis */}
          {adjustedFinancials?.sensitivity && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Stress Test Results
                <span className={cn(
                  "ml-auto px-2 py-1 rounded text-sm font-medium capitalize",
                  adjustedFinancials.sensitivity.riskRating === "low" ? "bg-green-100 text-green-700" :
                  adjustedFinancials.sensitivity.riskRating === "medium" ? "bg-yellow-100 text-yellow-700" :
                  "bg-red-100 text-red-700"
                )}>
                  {adjustedFinancials.sensitivity.riskRating} risk
                </span>
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-3 font-medium text-gray-500">Scenario</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">Cash Flow</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="py-2 px-3">Base Case</td>
                      <td className="py-2 px-3 text-right font-semibold">
                        {formatCurrency(adjustedFinancials.sensitivity.baseCashFlow)}
                      </td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.baseCashFlow >= 0 ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.baseCashFlow >= 0 ? "OK" : "Negative"}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-2 px-3">Interest Rate +1%</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(adjustedFinancials.sensitivity.rateIncrease1pct)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.rateIncrease1pct >= 0 ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.rateIncrease1pct >= 0 ? "OK" : "Negative"}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-2 px-3">Interest Rate +2%</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(adjustedFinancials.sensitivity.rateIncrease2pct)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.rateIncrease2pct >= 0 ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.rateIncrease2pct >= 0 ? "OK" : "Negative"}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-2 px-3">Vacancy 10%</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(adjustedFinancials.sensitivity.vacancy10pct)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.vacancy10pct >= 0 ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.vacancy10pct >= 0 ? "OK" : "Negative"}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-2 px-3">Vacancy 15%</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(adjustedFinancials.sensitivity.vacancy15pct)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.vacancy15pct >= 0 ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.vacancy15pct >= 0 ? "OK" : "Negative"}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-2 px-3">Rent -5%</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(adjustedFinancials.sensitivity.rentDecrease5pct)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.rentDecrease5pct >= 0 ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.rentDecrease5pct >= 0 ? "OK" : "Negative"}
                        </span>
                      </td>
                    </tr>
                    <tr className="border-b bg-yellow-50">
                      <td className="py-2 px-3 font-medium">Moderate Stress</td>
                      <td className="py-2 px-3 text-right font-semibold">{formatCurrency(adjustedFinancials.sensitivity.moderateStress)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.survivesModerate ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.survivesModerate ? "Survives" : "Fails"}
                        </span>
                      </td>
                    </tr>
                    <tr className="bg-red-50">
                      <td className="py-2 px-3 font-medium">Severe Stress</td>
                      <td className="py-2 px-3 text-right font-semibold">{formatCurrency(adjustedFinancials.sensitivity.severeStress)}</td>
                      <td className="py-2 px-3 text-right">
                        <span className={adjustedFinancials.sensitivity.survivesSevere ? "badge-green" : "badge-red"}>
                          {adjustedFinancials.sensitivity.survivesSevere ? "Survives" : "Fails"}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Break-even points */}
              <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4 text-center">
                {adjustedFinancials.sensitivity.breakEvenRate && (
                  <div>
                    <p className="text-sm text-gray-500">Break-even Rate</p>
                    <p className="font-semibold">{formatPercent(adjustedFinancials.sensitivity.breakEvenRate)}</p>
                  </div>
                )}
                {adjustedFinancials.sensitivity.breakEvenVacancy && (
                  <div>
                    <p className="text-sm text-gray-500">Break-even Vacancy</p>
                    <p className="font-semibold">{formatPercent(adjustedFinancials.sensitivity.breakEvenVacancy)}</p>
                  </div>
                )}
                {adjustedFinancials.sensitivity.breakEvenRent && (
                  <div>
                    <p className="text-sm text-gray-500">Break-even Rent</p>
                    <p className="font-semibold">{formatCurrency(adjustedFinancials.sensitivity.breakEvenRent)}/mo</p>
                  </div>
                )}
              </div>

              <p className="text-xs text-gray-500 mt-4">
                <strong>Moderate stress:</strong> +1% rate, 10% vacancy, -3% rent | <strong>Severe stress:</strong> +2% rate, 15% vacancy, -10% rent
              </p>
            </div>
          )}

          {/* Pros and Cons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Pros */}
            <div className={cn("card", pros.length > 0 ? "border-green-200" : "border-gray-200")}>
              <h3
                className={cn(
                  "font-semibold mb-3 flex items-center gap-2",
                  pros.length > 0 ? "text-green-800" : "text-gray-400"
                )}
              >
                <CheckCircle className="h-5 w-5" />
                Pros
              </h3>
              {pros.length > 0 ? (
                <ul className="space-y-2">
                  {pros.map((pro: string, i: number) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      {pro}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-400 italic">
                  {!analysis ? "Click 'Re-analyze' to generate pros/cons" : "No standout pros identified"}
                </p>
              )}
            </div>

            {/* Cons */}
            <div className={cn("card", cons.length > 0 ? "border-red-200" : "border-gray-200")}>
              <h3
                className={cn(
                  "font-semibold mb-3 flex items-center gap-2",
                  cons.length > 0 ? "text-red-800" : "text-gray-400"
                )}
              >
                <AlertTriangle className="h-5 w-5" />
                Cons
              </h3>
              {cons.length > 0 ? (
                <ul className="space-y-2">
                  {cons.map((con: string, i: number) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                      {con}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-400 italic">
                  {!analysis ? "Click 'Re-analyze' to generate pros/cons" : "No significant cons identified"}
                </p>
              )}
            </div>
          </div>

          {/* Red Flags */}
          {redFlags.length > 0 && (
            <div className="card border-red-300 bg-red-50">
              <h3 className="font-semibold mb-3 flex items-center gap-2 text-red-800">
                <XCircle className="h-5 w-5" />
                Red Flags
              </h3>
              <ul className="space-y-2">
                {redFlags.map((flag: string, i: number) => (
                  <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                    <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Saved Scenarios */}
          {savedProperty.custom_scenarios && savedProperty.custom_scenarios.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Calculator className="h-5 w-5 text-primary-600" />
                Saved Scenarios
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-3 font-medium text-gray-500">Scenario</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">Offer Price</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">Cash Flow</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">CoC</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">Cap Rate</th>
                      <th className="text-right py-2 px-3 font-medium text-gray-500">Cash Needed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {savedProperty.custom_scenarios.map((scenario, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                        <td className="py-2 px-3 font-medium">{scenario.name}</td>
                        <td className="py-2 px-3 text-right">{formatCurrency(scenario.offer_price)}</td>
                        <td
                          className={cn(
                            "py-2 px-3 text-right font-medium",
                            getCashFlowColor(scenario.monthly_cash_flow)
                          )}
                        >
                          {formatCurrency(scenario.monthly_cash_flow)}
                        </td>
                        <td className="py-2 px-3 text-right">{formatPercent(scenario.cash_on_cash)}</td>
                        <td className="py-2 px-3 text-right">{formatPercent(scenario.cap_rate)}</td>
                        <td className="py-2 px-3 text-right">
                          {formatCurrency(scenario.total_cash_needed)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Location Insights Loading State */}
          {locationLoading && !locationData && savedProperty.latitude && savedProperty.longitude && (
            <div className="card border-primary-200 bg-primary-50">
              <div className="flex items-center justify-center gap-3 py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                <div>
                  <p className="font-medium text-primary-900">Loading Location Insights</p>
                  <p className="text-sm text-primary-700">Fetching walk scores, schools, flood zone data...</p>
                </div>
              </div>
            </div>
          )}

          {/* Walk Score */}
          {locationData?.walk_score !== undefined && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Footprints className="h-5 w-5" />
                Walk Score
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <Footprints className="h-6 w-6 mx-auto mb-2 text-gray-600" />
                  <p className="text-3xl font-bold text-primary-600">
                    {locationData?.walk_score ?? "N/A"}
                  </p>
                  <p className="text-sm text-gray-500">
                    {locationData?.walk_description || "Walk Score"}
                  </p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <Train className="h-6 w-6 mx-auto mb-2 text-gray-600" />
                  <p className="text-3xl font-bold text-blue-600">
                    {locationData?.transit_score ?? "N/A"}
                  </p>
                  <p className="text-sm text-gray-500">
                    {locationData?.transit_description || "Transit Score"}
                  </p>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <Bike className="h-6 w-6 mx-auto mb-2 text-gray-600" />
                  <p className="text-3xl font-bold text-green-600">
                    {locationData?.bike_score ?? "N/A"}
                  </p>
                  <p className="text-sm text-gray-500">
                    {locationData?.bike_description || "Bike Score"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Noise & Schools */}
          {(locationData?.noise || locationData?.schools) && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Location Insights
              </h3>
              <div className="space-y-6">
                {/* Noise */}
                {locationData.noise && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center gap-2">
                      <Volume2 className="h-4 w-4" />
                      Noise Level
                    </h4>
                    <div className="flex items-center gap-4">
                      <div className="text-center p-4 bg-gray-50 rounded-lg min-w-[100px]">
                        <p
                          className={cn(
                            "text-3xl font-bold",
                            locationData.noise.noise_score !== undefined &&
                              locationData.noise.noise_score <= 30
                              ? "text-green-600"
                              : locationData.noise.noise_score !== undefined &&
                                locationData.noise.noise_score <= 60
                              ? "text-yellow-600"
                              : "text-red-600"
                          )}
                        >
                          {locationData.noise.noise_score ?? "N/A"}
                        </p>
                        <p className="text-sm text-gray-500 mt-1">
                          {locationData.noise.description || "Noise Score"}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Schools */}
                {locationData.schools && locationData.schools.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-gray-700 mb-3 flex items-center gap-2">
                      <GraduationCap className="h-4 w-4" />
                      Nearby Schools
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {locationData.schools.slice(0, 6).map((school: any, i: number) => (
                        <div key={i} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 text-sm truncate">
                                {school.name}
                              </p>
                              <p className="text-xs text-gray-500">
                                {school.type && <span className="capitalize">{school.type}</span>}
                                {school.type && school.grades && " - "}
                                {school.grades}
                              </p>
                              {school.distance_miles !== undefined && (
                                <p className="text-xs text-gray-400 mt-1">
                                  {school.distance_miles.toFixed(1)} mi away
                                </p>
                              )}
                            </div>
                            {school.rating !== undefined && school.rating !== null && (
                              <div
                                className={cn(
                                  "flex items-center gap-1 px-2 py-1 rounded text-xs font-medium",
                                  school.rating >= 8
                                    ? "bg-green-100 text-green-700"
                                    : school.rating >= 6
                                    ? "bg-yellow-100 text-yellow-700"
                                    : school.rating >= 4
                                    ? "bg-orange-100 text-orange-700"
                                    : "bg-red-100 text-red-700"
                                )}
                              >
                                <Star className="h-3 w-3" />
                                {school.rating}/10
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Flood Zone */}
          {locationData?.flood_zone && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Droplets className="h-5 w-5" />
                FEMA Flood Zone
              </h3>
              <div className="flex items-center gap-6">
                <div
                  className={cn(
                    "text-center p-4 rounded-lg min-w-[120px]",
                    locationData.flood_zone.risk_level === "high"
                      ? "bg-red-50"
                      : locationData.flood_zone.risk_level === "moderate"
                      ? "bg-yellow-50"
                      : locationData.flood_zone.risk_level === "low"
                      ? "bg-green-50"
                      : "bg-gray-50"
                  )}
                >
                  <div className="flex items-center justify-center gap-2 mb-2">
                    {locationData.flood_zone.risk_level === "high" ? (
                      <ShieldAlert className="h-5 w-5 text-red-600" />
                    ) : locationData.flood_zone.risk_level === "low" ? (
                      <ShieldCheck className="h-5 w-5 text-green-600" />
                    ) : (
                      <Droplets className="h-5 w-5 text-gray-400" />
                    )}
                    <span className="text-sm font-medium text-gray-600">Zone</span>
                  </div>
                  <p
                    className={cn(
                      "text-2xl font-bold",
                      locationData.flood_zone.risk_level === "high"
                        ? "text-red-600"
                        : locationData.flood_zone.risk_level === "moderate"
                        ? "text-yellow-600"
                        : locationData.flood_zone.risk_level === "low"
                        ? "text-green-600"
                        : "text-gray-600"
                    )}
                  >
                    {locationData.flood_zone.zone || "N/A"}
                  </p>
                  <p
                    className={cn(
                      "text-xs font-medium capitalize mt-1",
                      locationData.flood_zone.risk_level === "high"
                        ? "text-red-600"
                        : locationData.flood_zone.risk_level === "moderate"
                        ? "text-yellow-600"
                        : locationData.flood_zone.risk_level === "low"
                        ? "text-green-600"
                        : "text-gray-500"
                    )}
                  >
                    {locationData.flood_zone.risk_level} Risk
                  </p>
                </div>
                <div className="flex-1 space-y-2">
                  <p className="text-gray-700">{locationData.flood_zone.description}</p>
                  <div className="flex flex-wrap gap-4 text-sm">
                    {locationData.flood_zone.annual_chance && (
                      <div>
                        <span className="text-gray-500">Annual Flood Chance:</span>{" "}
                        <span className="font-medium">{locationData.flood_zone.annual_chance}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Flood Insurance:</span>{" "}
                      <span
                        className={cn(
                          "font-medium",
                          locationData.flood_zone.requires_insurance
                            ? "text-red-600"
                            : "text-green-600"
                        )}
                      >
                        {locationData.flood_zone.requires_insurance ? "Required" : "Not Required"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notes Section */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Edit3 className="h-5 w-5 text-primary-600" />
                Notes
              </h3>
              {!editingNotes ? (
                <button onClick={() => setEditingNotes(true)} className="btn-outline text-sm">
                  Edit Notes
                </button>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setNotesValue(savedProperty.notes || "");
                      setEditingNotes(false);
                    }}
                    className="btn-outline text-sm flex items-center gap-1"
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveNotes}
                    className="btn-primary text-sm flex items-center gap-1"
                  >
                    <Save className="h-4 w-4" />
                    Save
                  </button>
                </div>
              )}
            </div>
            {editingNotes ? (
              <textarea
                value={notesValue}
                onChange={(e) => setNotesValue(e.target.value)}
                className="w-full border rounded-lg p-3 text-sm min-h-[120px] focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Add notes about this property..."
              />
            ) : (
              <p className="text-gray-600 whitespace-pre-wrap">
                {savedProperty.notes || (
                  <span className="text-gray-400 italic">
                    No notes yet. Click "Edit Notes" to add some.
                  </span>
                )}
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3 justify-center">
            <button
              onClick={() => {
                const params = new URLSearchParams();
                if (offerPrice) params.set('price', offerPrice.toString());
                if (savedProperty.estimated_rent) params.set('rent', savedProperty.estimated_rent.toString());
                if (savedProperty.zip_code) params.set('zip', savedProperty.zip_code);
                params.set('down', downPaymentPct);
                params.set('rate', interestRate);
                router.push(`/calculator?${params.toString()}`);
              }}
              className="btn-outline flex items-center gap-2"
            >
              <Calculator className="h-4 w-4" />
              Open in Calculator
            </button>
            {savedProperty.source_url && (
              <a
                href={savedProperty.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-outline flex items-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                View Original Listing
              </a>
            )}
          </div>

          {/* Property Metadata */}
          <div className="card bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Property Info</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Status</span>
                <p className="font-medium capitalize">{savedProperty.pipeline_status}</p>
              </div>
              <div>
                <span className="text-gray-500">Saved</span>
                <p className="font-medium">
                  {new Date(savedProperty.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Last Updated</span>
                <p className="font-medium">
                  {new Date(savedProperty.updated_at).toLocaleDateString()}
                </p>
              </div>
              {savedProperty.location_data_fetched && (
                <div>
                  <span className="text-gray-500">Location Data</span>
                  <p className="font-medium">
                    {new Date(savedProperty.location_data_fetched).toLocaleDateString()}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
