"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Calculator,
  DollarSign,
  TrendingUp,
  Home,
  Percent,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
} from "lucide-react";
import { api, MacroDataResponse } from "@/lib/api";
import { cn, formatCurrency, formatPercent, getCashFlowColor } from "@/lib/utils";
import { LoadingSpinner, LoadingPage } from "@/components/LoadingSpinner";

function CalculatorContent() {
  const searchParams = useSearchParams();

  // Inputs from URL or defaults
  const [price, setPrice] = useState(searchParams.get("price") || "350000");
  const [rent, setRent] = useState(searchParams.get("rent") || "2000");
  const [downPaymentPct, setDownPaymentPct] = useState(searchParams.get("down") || "20");
  const [interestRate, setInterestRate] = useState(searchParams.get("rate") || "7");
  const [zipCode, setZipCode] = useState(searchParams.get("zip") || "");

  // Macro data for current rates
  const [macroData, setMacroData] = useState<MacroDataResponse | null>(null);
  const [loadingRates, setLoadingRates] = useState(true);

  // Fetch current rates
  useEffect(() => {
    async function fetchRates() {
      try {
        const data = await api.getMacroData();
        setMacroData(data);
        // Only set rate from macro if not provided in URL
        if (!searchParams.get("rate") && data.mortgage_30yr) {
          setInterestRate(data.mortgage_30yr.toFixed(2));
        }
      } catch (err) {
        console.error("Failed to fetch rates:", err);
      } finally {
        setLoadingRates(false);
      }
    }
    fetchRates();
  }, [searchParams]);

  // Helper function to calculate mortgage payment
  const calculateMortgagePayment = (principal: number, annualRate: number, years: number = 30) => {
    if (principal <= 0) return 0;
    const monthlyRate = annualRate / 12;
    const numPayments = years * 12;
    if (monthlyRate === 0) return principal / numPayments;
    return principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1);
  };

  // Calculate financials
  const financials = useMemo(() => {
    const purchasePrice = parseFloat(price) || 0;
    const monthlyRent = parseFloat(rent) || 0;
    const downPct = parseFloat(downPaymentPct) / 100;
    const rate = parseFloat(interestRate) / 100;

    if (purchasePrice <= 0) return null;

    // Calculate values
    const downPayment = purchasePrice * downPct;
    const closingCosts = purchasePrice * 0.03;
    const totalCashInvested = downPayment + closingCosts;
    const loanAmount = purchasePrice - downPayment;

    // Monthly mortgage payment (P&I)
    const monthlyMortgage = calculateMortgagePayment(loanAmount, rate);

    // Operating expenses (estimated)
    const monthlyTaxes = (purchasePrice * 0.012) / 12;
    const monthlyInsurance = (purchasePrice * 0.005) / 12;
    const vacancyRate = 0.08;
    const monthlyVacancy = monthlyRent * vacancyRate;
    const monthlyMaintenance = (purchasePrice * 0.01) / 12;
    const monthlyCapex = (purchasePrice * 0.01) / 12;
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
    const capRate = purchasePrice > 0 ? noi / purchasePrice : 0;
    const rentToPrice = purchasePrice > 0 ? monthlyRent / purchasePrice : 0;
    const grm = monthlyRent > 0 ? purchasePrice / (monthlyRent * 12) : 0;
    const breakEvenOccupancy =
      monthlyRent > 0 ? (totalMonthlyExpenses - monthlyVacancy) / monthlyRent : 1;

    // Calculate deal score
    let score = 50;
    if (cashOnCash >= 0.12) score += 15;
    else if (cashOnCash >= 0.08) score += 10;
    else if (cashOnCash >= 0.05) score += 5;
    else if (cashOnCash < 0) score -= 15;

    if (capRate >= 0.08) score += 10;
    else if (capRate >= 0.06) score += 5;
    else if (capRate < 0.04) score -= 10;

    if (rentToPrice >= 0.01) score += 10;
    else if (rentToPrice >= 0.008) score += 5;
    else if (rentToPrice < 0.006) score -= 10;

    if (monthlyCashFlow >= 500) score += 10;
    else if (monthlyCashFlow >= 200) score += 5;
    else if (monthlyCashFlow < 0) score -= 15;

    score = Math.max(0, Math.min(100, score));

    // Stress test
    const calcCashFlow = (customRate?: number, customVacancy?: number, customRent?: number) => {
      const r = customRate !== undefined ? customRate : rate;
      const v = customVacancy !== undefined ? customVacancy : vacancyRate;
      const rentAmt = customRent !== undefined ? customRent : monthlyRent;

      const mortgage = calculateMortgagePayment(loanAmount, r);
      const vacancy = rentAmt * v;
      const pm = rentAmt * 0.1;

      const expenses = mortgage + monthlyTaxes + monthlyInsurance + vacancy + monthlyMaintenance + monthlyCapex + pm;
      return rentAmt - expenses;
    };

    const moderateStress = calcCashFlow(rate + 0.01, 0.10, monthlyRent * 0.97);
    const severeStress = calcCashFlow(rate + 0.02, 0.15, monthlyRent * 0.90);

    let riskRating: 'low' | 'medium' | 'high' = 'low';
    if (severeStress < -500 || monthlyCashFlow < 0) {
      riskRating = 'high';
    } else if (moderateStress < 0 || monthlyCashFlow < 200) {
      riskRating = 'medium';
    }

    return {
      purchasePrice,
      downPayment,
      closingCosts,
      totalCashInvested,
      loanAmount,
      monthlyMortgage,
      monthlyTaxes,
      monthlyInsurance,
      monthlyVacancy,
      monthlyMaintenance,
      monthlyCapex,
      monthlyPM,
      totalMonthlyExpenses,
      monthlyCashFlow,
      annualCashFlow,
      noi,
      cashOnCash,
      capRate,
      rentToPrice,
      grm,
      breakEvenOccupancy,
      score,
      moderateStress,
      severeStress,
      riskRating,
    };
  }, [price, rent, downPaymentPct, interestRate]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Calculator className="h-8 w-8 text-purple-600" />
          Investment Calculator
        </h1>
        <p className="text-gray-500 mt-1">
          Analyze any property with custom financing assumptions
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Home className="h-5 w-5 text-gray-600" />
              Property Details
            </h2>
            <div className="space-y-4">
              <div>
                <label className="label">Purchase Price</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="input pl-9"
                    placeholder="350000"
                  />
                </div>
              </div>
              <div>
                <label className="label">Monthly Rent</label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="number"
                    value={rent}
                    onChange={(e) => setRent(e.target.value)}
                    className="input pl-9"
                    placeholder="2000"
                  />
                </div>
              </div>
              <div>
                <label className="label">ZIP Code (optional)</label>
                <input
                  type="text"
                  value={zipCode}
                  onChange={(e) => setZipCode(e.target.value)}
                  className="input"
                  placeholder="85001"
                  maxLength={5}
                />
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Percent className="h-5 w-5 text-gray-600" />
              Financing
            </h2>
            <div className="space-y-4">
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
                  step="0.125"
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
                    Use current rate ({macroData.mortgage_30yr.toFixed(2)}%)
                  </button>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2 space-y-6">
          {financials ? (
            <>
              {/* Key Metrics */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary-600" />
                    Key Metrics
                  </h2>
                  <div className={cn(
                    "px-3 py-1 rounded-full text-sm font-medium",
                    financials.score >= 70 ? "bg-green-100 text-green-700" :
                    financials.score >= 50 ? "bg-amber-100 text-amber-700" :
                    "bg-red-100 text-red-700"
                  )}>
                    Score: {financials.score}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Monthly Cash Flow</p>
                    <p className={cn("text-xl font-bold mt-1", getCashFlowColor(financials.monthlyCashFlow))}>
                      {formatCurrency(financials.monthlyCashFlow)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Cash-on-Cash</p>
                    <p className="text-xl font-bold mt-1">
                      {formatPercent(financials.cashOnCash)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Cap Rate</p>
                    <p className="text-xl font-bold mt-1">
                      {formatPercent(financials.capRate)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">Rent-to-Price</p>
                    <p className="text-xl font-bold mt-1">
                      {formatPercent(financials.rentToPrice)}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t">
                  <div>
                    <p className="text-sm text-gray-500">Total Cash Needed</p>
                    <p className="font-semibold">{formatCurrency(financials.totalCashInvested)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Annual Cash Flow</p>
                    <p className={cn("font-semibold", getCashFlowColor(financials.annualCashFlow))}>
                      {formatCurrency(financials.annualCashFlow)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">GRM</p>
                    <p className="font-semibold">{financials.grm.toFixed(1)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Break-even Occupancy</p>
                    <p className="font-semibold">{formatPercent(financials.breakEvenOccupancy)}</p>
                  </div>
                </div>
              </div>

              {/* Expense Breakdown */}
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Monthly Expense Breakdown</h2>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">Mortgage (P&I)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyMortgage)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">Property Taxes (est.)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyTaxes)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">Insurance (est.)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyInsurance)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">Vacancy (8%)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyVacancy)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">Maintenance (1%)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyMaintenance)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">CapEx (1%)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyCapex)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-gray-600">Property Management (10%)</span>
                    <span className="font-medium">{formatCurrency(financials.monthlyPM)}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 font-semibold">
                    <span>Total Expenses</span>
                    <span>{formatCurrency(financials.totalMonthlyExpenses)}</span>
                  </div>
                </div>
              </div>

              {/* Stress Test */}
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Stress Test
                  <span className={cn(
                    "ml-auto px-2 py-1 rounded text-sm font-medium capitalize",
                    financials.riskRating === "low" ? "bg-green-100 text-green-700" :
                    financials.riskRating === "medium" ? "bg-yellow-100 text-yellow-700" :
                    "bg-red-100 text-red-700"
                  )}>
                    {financials.riskRating} risk
                  </span>
                </h2>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500 mb-2">Base Case</p>
                    <p className={cn("text-xl font-bold", getCashFlowColor(financials.monthlyCashFlow))}>
                      {formatCurrency(financials.monthlyCashFlow)}
                    </p>
                    {financials.monthlyCashFlow >= 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mx-auto mt-2" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mx-auto mt-2" />
                    )}
                  </div>
                  <div className="text-center p-4 bg-yellow-50 rounded-lg">
                    <p className="text-sm text-gray-500 mb-2">Moderate Stress</p>
                    <p className={cn("text-xl font-bold", getCashFlowColor(financials.moderateStress))}>
                      {formatCurrency(financials.moderateStress)}
                    </p>
                    {financials.moderateStress >= 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mx-auto mt-2" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mx-auto mt-2" />
                    )}
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-gray-500 mb-2">Severe Stress</p>
                    <p className={cn("text-xl font-bold", getCashFlowColor(financials.severeStress))}>
                      {formatCurrency(financials.severeStress)}
                    </p>
                    {financials.severeStress >= 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mx-auto mt-2" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mx-auto mt-2" />
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-4">
                  <strong>Moderate:</strong> +1% rate, 10% vacancy, -3% rent | <strong>Severe:</strong> +2% rate, 15% vacancy, -10% rent
                </p>
              </div>
            </>
          ) : (
            <div className="card text-center py-16">
              <Calculator className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Enter a purchase price to see the analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CalculatorPage() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <CalculatorContent />
    </Suspense>
  );
}
