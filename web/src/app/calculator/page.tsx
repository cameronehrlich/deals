"use client";

import { useState, useEffect } from "react";
import {
  Calculator,
  DollarSign,
  Percent,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Zap,
} from "lucide-react";
import { api, AnalysisResult, MacroDataResponse } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  getCashFlowColor,
  getRiskBadge,
  cn,
} from "@/lib/utils";
import { ScoreGauge } from "@/components/ScoreGauge";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function CalculatorPage() {
  // Inputs
  const [purchasePrice, setPurchasePrice] = useState("200000");
  const [monthlyRent, setMonthlyRent] = useState("1800");
  const [downPaymentPct, setDownPaymentPct] = useState("25");
  const [interestRate, setInterestRate] = useState("7");
  const [propertyTaxRate, setPropertyTaxRate] = useState("1.2");
  const [insuranceRate, setInsuranceRate] = useState("0.5");
  const [vacancyRate, setVacancyRate] = useState("8");
  const [maintenanceRate, setMaintenanceRate] = useState("1");
  const [propertyManagementRate, setPropertyManagementRate] = useState("10");
  const [hoaMonthly, setHoaMonthly] = useState("0");

  // State
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [macroData, setMacroData] = useState<MacroDataResponse | null>(null);
  const [loadingRates, setLoadingRates] = useState(true);

  // Fetch current market rates on load
  useEffect(() => {
    async function fetchRates() {
      try {
        const data = await api.getMacroData();
        setMacroData(data);
        // Auto-fill with current rate
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

  const calculate = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await api.calculateFinancials({
        purchase_price: parseFloat(purchasePrice),
        monthly_rent: parseFloat(monthlyRent),
        down_payment_pct: parseFloat(downPaymentPct) / 100,
        interest_rate: parseFloat(interestRate) / 100,
        property_tax_rate: parseFloat(propertyTaxRate) / 100,
        insurance_rate: parseFloat(insuranceRate) / 100,
        vacancy_rate: parseFloat(vacancyRate) / 100,
        maintenance_rate: parseFloat(maintenanceRate) / 100,
        property_management_rate: parseFloat(propertyManagementRate) / 100,
        hoa_monthly: parseFloat(hoaMonthly),
      });

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Calculation failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Calculator className="h-8 w-8 text-primary-600" />
          Investment Calculator
        </h1>
        <p className="text-gray-500 mt-1">
          Analyze any property with detailed financial projections and stress testing
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Property Details
            </h2>

            <div className="space-y-4">
              <div>
                <label className="label">Purchase Price ($)</label>
                <input
                  type="number"
                  value={purchasePrice}
                  onChange={(e) => setPurchasePrice(e.target.value)}
                  className="input"
                  min="0"
                />
              </div>

              <div>
                <label className="label">Monthly Rent ($)</label>
                <input
                  type="number"
                  value={monthlyRent}
                  onChange={(e) => setMonthlyRent(e.target.value)}
                  className="input"
                  min="0"
                />
              </div>

              <div>
                <label className="label">Monthly HOA ($)</label>
                <input
                  type="number"
                  value={hoaMonthly}
                  onChange={(e) => setHoaMonthly(e.target.value)}
                  className="input"
                  min="0"
                />
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
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
                <label className="label flex items-center justify-between">
                  <span>Interest Rate (%)</span>
                  {loadingRates ? (
                    <span className="text-xs text-gray-400">Loading rates...</span>
                  ) : macroData?.mortgage_30yr ? (
                    <button
                      type="button"
                      onClick={() => setInterestRate(macroData.mortgage_30yr!.toFixed(2))}
                      className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
                    >
                      <Zap className="h-3 w-3" />
                      Use current ({macroData.mortgage_30yr.toFixed(2)}%)
                    </button>
                  ) : null}
                </label>
                <input
                  type="number"
                  value={interestRate}
                  onChange={(e) => setInterestRate(e.target.value)}
                  className="input"
                  min="1"
                  max="20"
                  step="0.25"
                />
                {macroData && (
                  <p className="text-xs text-gray-500 mt-1">
                    Current 30yr: {macroData.mortgage_30yr?.toFixed(2)}% | 15yr: {macroData.mortgage_15yr?.toFixed(2)}%
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Expenses
            </h2>

            <div className="space-y-4">
              <div>
                <label className="label">Property Tax Rate (%)</label>
                <input
                  type="number"
                  value={propertyTaxRate}
                  onChange={(e) => setPropertyTaxRate(e.target.value)}
                  className="input"
                  min="0"
                  max="5"
                  step="0.1"
                />
              </div>

              <div>
                <label className="label">Insurance Rate (%)</label>
                <input
                  type="number"
                  value={insuranceRate}
                  onChange={(e) => setInsuranceRate(e.target.value)}
                  className="input"
                  min="0"
                  max="3"
                  step="0.1"
                />
              </div>

              <div>
                <label className="label">Vacancy Rate (%)</label>
                <input
                  type="number"
                  value={vacancyRate}
                  onChange={(e) => setVacancyRate(e.target.value)}
                  className="input"
                  min="0"
                  max="30"
                />
              </div>

              <div>
                <label className="label">Maintenance Reserve (%)</label>
                <input
                  type="number"
                  value={maintenanceRate}
                  onChange={(e) => setMaintenanceRate(e.target.value)}
                  className="input"
                  min="0"
                  max="5"
                  step="0.5"
                />
              </div>

              <div>
                <label className="label">Property Management (%)</label>
                <input
                  type="number"
                  value={propertyManagementRate}
                  onChange={(e) => setPropertyManagementRate(e.target.value)}
                  className="input"
                  min="0"
                  max="20"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={calculate}
              disabled={loading}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {loading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Calculator className="h-4 w-4" />
              )}
              Calculate
            </button>
            <button
              onClick={reset}
              className="btn-outline flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Reset
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-2 space-y-6">
          {error && (
            <div className="card border-red-200 bg-red-50">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {result && (
            <>
              {/* Verdict */}
              <div className={cn(
                "card",
                result.verdict.includes("STRONG") ? "border-green-200 bg-green-50" :
                result.verdict.includes("BUY") ? "border-green-200" :
                result.verdict.includes("CAUTION") || result.verdict.includes("NOT") ? "border-red-200 bg-red-50" :
                "border-yellow-200 bg-yellow-50"
              )}>
                <div className="flex items-start gap-4">
                  {result.verdict.includes("STRONG") || result.verdict.includes("BUY") ? (
                    <CheckCircle className="h-8 w-8 text-green-600 flex-shrink-0" />
                  ) : result.verdict.includes("NOT") || result.verdict.includes("CAUTION") ? (
                    <XCircle className="h-8 w-8 text-red-600 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="h-8 w-8 text-yellow-600 flex-shrink-0" />
                  )}
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">
                      {result.verdict}
                    </h2>
                    <div className="mt-3 space-y-2">
                      {result.recommendations.map((rec, i) => (
                        <p key={i} className="text-sm text-gray-700">{rec}</p>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Monthly Cash Flow</p>
                  <p className={cn(
                    "text-2xl font-bold mt-1",
                    getCashFlowColor(result.financials.monthly_cash_flow)
                  )}>
                    {formatCurrency(result.financials.monthly_cash_flow)}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Cash-on-Cash</p>
                  <p className="text-2xl font-bold mt-1 text-gray-900">
                    {formatPercent(result.financials.cash_on_cash_return)}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Cap Rate</p>
                  <p className="text-2xl font-bold mt-1 text-gray-900">
                    {formatPercent(result.financials.cap_rate)}
                  </p>
                </div>
                <div className="card text-center">
                  <p className="text-sm text-gray-500">Risk Rating</p>
                  <p className={cn(
                    "text-2xl font-bold mt-1 capitalize",
                    result.sensitivity.risk_rating === "low" ? "text-green-600" :
                    result.sensitivity.risk_rating === "medium" ? "text-yellow-600" : "text-red-600"
                  )}>
                    {result.sensitivity.risk_rating}
                  </p>
                </div>
              </div>

              {/* Financial Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Investment Summary
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Down Payment</span>
                      <span className="font-semibold">{formatCurrency(result.financials.down_payment)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Closing Costs</span>
                      <span className="font-semibold">{formatCurrency(result.financials.closing_costs)}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t">
                      <span className="font-medium">Total Cash Needed</span>
                      <span className="font-bold">{formatCurrency(result.financials.total_cash_invested)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Loan Amount</span>
                      <span className="font-semibold">{formatCurrency(result.financials.loan_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">GRM</span>
                      <span className="font-semibold">{result.financials.gross_rent_multiplier.toFixed(1)}</span>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Monthly Cash Flow
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between text-green-600">
                      <span>Rent Income</span>
                      <span className="font-semibold">+{formatCurrency(parseFloat(monthlyRent))}</span>
                    </div>
                    <div className="flex justify-between text-red-600">
                      <span>Mortgage (P&I)</span>
                      <span>-{formatCurrency(result.financials.monthly_mortgage)}</span>
                    </div>
                    <div className="flex justify-between text-red-600">
                      <span>Taxes & Insurance</span>
                      <span>-{formatCurrency(result.financials.monthly_taxes + result.financials.monthly_insurance)}</span>
                    </div>
                    <div className="flex justify-between text-red-600">
                      <span>Operating Expenses</span>
                      <span>-{formatCurrency(
                        result.financials.monthly_maintenance +
                        result.financials.monthly_vacancy_reserve +
                        result.financials.monthly_property_management +
                        result.financials.monthly_capex +
                        result.financials.monthly_hoa
                      )}</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t">
                      <span className="font-medium">Net Cash Flow</span>
                      <span className={cn(
                        "font-bold",
                        getCashFlowColor(result.financials.monthly_cash_flow)
                      )}>
                        {formatCurrency(result.financials.monthly_cash_flow)}/mo
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Stress Tests */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Stress Test Results
                </h3>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="table-header">Scenario</th>
                        <th className="table-header text-right">Cash Flow</th>
                        <th className="table-header text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="table-cell">Base Case</td>
                        <td className="table-cell text-right font-semibold">
                          {formatCurrency(result.sensitivity.base_cash_flow)}
                        </td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.base_cash_flow >= 0 ? "badge-green" : "badge-red"}>
                            {result.sensitivity.base_cash_flow >= 0 ? "OK" : "Negative"}
                          </span>
                        </td>
                      </tr>
                      <tr className="border-b">
                        <td className="table-cell">Interest Rate +1%</td>
                        <td className="table-cell text-right">{formatCurrency(result.sensitivity.rate_increase_1pct)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.rate_increase_1pct >= 0 ? "badge-green" : "badge-red"}>
                            {result.sensitivity.rate_increase_1pct >= 0 ? "OK" : "Negative"}
                          </span>
                        </td>
                      </tr>
                      <tr className="border-b">
                        <td className="table-cell">Interest Rate +2%</td>
                        <td className="table-cell text-right">{formatCurrency(result.sensitivity.rate_increase_2pct)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.rate_increase_2pct >= 0 ? "badge-green" : "badge-red"}>
                            {result.sensitivity.rate_increase_2pct >= 0 ? "OK" : "Negative"}
                          </span>
                        </td>
                      </tr>
                      <tr className="border-b">
                        <td className="table-cell">Vacancy 10%</td>
                        <td className="table-cell text-right">{formatCurrency(result.sensitivity.vacancy_10pct)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.vacancy_10pct >= 0 ? "badge-green" : "badge-red"}>
                            {result.sensitivity.vacancy_10pct >= 0 ? "OK" : "Negative"}
                          </span>
                        </td>
                      </tr>
                      <tr className="border-b">
                        <td className="table-cell">Vacancy 15%</td>
                        <td className="table-cell text-right">{formatCurrency(result.sensitivity.vacancy_15pct)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.vacancy_15pct >= 0 ? "badge-green" : "badge-red"}>
                            {result.sensitivity.vacancy_15pct >= 0 ? "OK" : "Negative"}
                          </span>
                        </td>
                      </tr>
                      <tr className="border-b">
                        <td className="table-cell">Rent -5%</td>
                        <td className="table-cell text-right">{formatCurrency(result.sensitivity.rent_decrease_5pct)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.rent_decrease_5pct >= 0 ? "badge-green" : "badge-red"}>
                            {result.sensitivity.rent_decrease_5pct >= 0 ? "OK" : "Negative"}
                          </span>
                        </td>
                      </tr>
                      <tr className="border-b bg-yellow-50">
                        <td className="table-cell font-medium">Moderate Stress</td>
                        <td className="table-cell text-right font-semibold">{formatCurrency(result.sensitivity.moderate_stress)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.survives_moderate ? "badge-green" : "badge-red"}>
                            {result.sensitivity.survives_moderate ? "Survives" : "Fails"}
                          </span>
                        </td>
                      </tr>
                      <tr className="bg-red-50">
                        <td className="table-cell font-medium">Severe Stress</td>
                        <td className="table-cell text-right font-semibold">{formatCurrency(result.sensitivity.severe_stress)}</td>
                        <td className="table-cell text-right">
                          <span className={result.sensitivity.survives_severe ? "badge-green" : "badge-red"}>
                            {result.sensitivity.survives_severe ? "Survives" : "Fails"}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Break-even points */}
                <div className="mt-4 pt-4 border-t grid grid-cols-3 gap-4 text-center">
                  {result.sensitivity.break_even_rate && (
                    <div>
                      <p className="text-sm text-gray-500">Break-even Rate</p>
                      <p className="font-semibold">{formatPercent(result.sensitivity.break_even_rate)}</p>
                    </div>
                  )}
                  {result.sensitivity.break_even_vacancy && (
                    <div>
                      <p className="text-sm text-gray-500">Break-even Vacancy</p>
                      <p className="font-semibold">{formatPercent(result.sensitivity.break_even_vacancy)}</p>
                    </div>
                  )}
                  {result.sensitivity.break_even_rent && (
                    <div>
                      <p className="text-sm text-gray-500">Break-even Rent</p>
                      <p className="font-semibold">{formatCurrency(result.sensitivity.break_even_rent)}/mo</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Empty state */}
          {!result && !error && (
            <div className="card text-center py-12">
              <Calculator className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">
                Enter property details
              </h3>
              <p className="text-gray-500 mt-1">
                Fill in the form and click Calculate to see detailed analysis
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
