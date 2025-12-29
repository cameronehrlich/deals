"use client";

/**
 * FinancingComparison Component
 *
 * Compares multiple financing scenarios for a property using loan product presets.
 * Shows side-by-side comparison of key metrics and DSCR qualification status.
 */

import { useState, useEffect } from "react";
import {
  DollarSign,
  Percent,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Info,
} from "lucide-react";
import { api, LoanProduct, FinancingScenario } from "@/lib/api";
import { cn, formatCurrency, formatPercent, getCashFlowColor } from "@/lib/utils";

interface FinancingComparisonProps {
  purchasePrice: number;
  monthlyRent: number;
  propertyTaxRate?: number;
  insuranceRate?: number;
  hoaMonthly?: number;
  onScenarioSelect?: (scenario: FinancingScenario, product: LoanProduct) => void;
}

export function FinancingComparison({
  purchasePrice,
  monthlyRent,
  propertyTaxRate = 0.012,
  insuranceRate = 0.005,
  hoaMonthly = 0,
  onScenarioSelect,
}: FinancingComparisonProps) {
  const [loanProducts, setLoanProducts] = useState<LoanProduct[]>([]);
  const [scenarios, setScenarios] = useState<FinancingScenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Fetch loan products and calculate scenarios
  useEffect(() => {
    async function fetchAndCalculate() {
      if (!purchasePrice || !monthlyRent) return;

      try {
        setLoading(true);
        setError(null);

        // Fetch default loan products
        const products = await api.getLoanProducts({ defaults_only: true });
        setLoanProducts(products);

        // Calculate scenarios for each product
        const calculatedScenarios = await api.compareFinancingScenarios({
          purchase_price: purchasePrice,
          monthly_rent: monthlyRent,
          property_tax_rate: propertyTaxRate,
          insurance_rate: insuranceRate,
          hoa_monthly: hoaMonthly,
        });

        setScenarios(calculatedScenarios);
      } catch (err) {
        console.error("Failed to fetch financing scenarios:", err);
        setError(err instanceof Error ? err.message : "Failed to load scenarios");
      } finally {
        setLoading(false);
      }
    }

    fetchAndCalculate();
  }, [purchasePrice, monthlyRent, propertyTaxRate, insuranceRate, hoaMonthly]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const calculatedScenarios = await api.compareFinancingScenarios({
        purchase_price: purchasePrice,
        monthly_rent: monthlyRent,
        property_tax_rate: propertyTaxRate,
        insurance_rate: insuranceRate,
        hoa_monthly: hoaMonthly,
      });
      setScenarios(calculatedScenarios);
    } catch (err) {
      console.error("Failed to refresh scenarios:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectScenario = (index: number) => {
    setSelectedIndex(index);
    if (onScenarioSelect && scenarios[index] && loanProducts[index]) {
      onScenarioSelect(scenarios[index], loanProducts[index]);
    }
  };

  // Find best scenario for each metric
  const bestCashFlow = scenarios.length > 0
    ? Math.max(...scenarios.map(s => s.monthly_cash_flow))
    : 0;
  const bestCoC = scenarios.length > 0
    ? Math.max(...scenarios.map(s => s.cash_on_cash_return))
    : 0;
  const lowestCashNeeded = scenarios.length > 0
    ? Math.min(...scenarios.map(s => s.total_cash_needed))
    : Infinity;

  if (!purchasePrice || !monthlyRent) {
    return null;
  }

  return (
    <div className="card">
      {/* Header */}
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-primary-600" />
          Financing Comparison
        </h3>
        <div className="flex items-center gap-2">
          {!loading && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleRefresh();
              }}
              className="p-1 text-gray-400 hover:text-gray-600"
              title="Refresh scenarios"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          )}
          {expanded ? (
            <ChevronUp className="h-5 w-5 text-gray-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-400" />
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
              <span className="ml-2 text-gray-600">Calculating scenarios...</span>
            </div>
          ) : error ? (
            <div className="text-center py-4 text-red-600">
              <AlertTriangle className="h-5 w-5 mx-auto mb-2" />
              {error}
            </div>
          ) : scenarios.length === 0 ? (
            <div className="text-center py-4 text-gray-500">
              No loan products configured
            </div>
          ) : (
            <>
              {/* Comparison Table */}
              <div className="overflow-x-auto -mx-4 sm:mx-0">
                <table className="w-full text-sm min-w-[600px]">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left py-2 px-3 font-medium text-gray-600">
                        Loan Type
                      </th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">
                        Down
                      </th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">
                        Rate
                      </th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">
                        Cash Needed
                      </th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">
                        Cash Flow
                      </th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">
                        CoC Return
                      </th>
                      <th className="text-right py-2 px-3 font-medium text-gray-600">
                        DSCR
                      </th>
                      <th className="text-center py-2 px-3 font-medium text-gray-600">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {scenarios.map((scenario, index) => {
                      const product = loanProducts[index];
                      if (!product) return null;

                      const isBestCashFlow = scenario.monthly_cash_flow === bestCashFlow && bestCashFlow > 0;
                      const isBestCoC = scenario.cash_on_cash_return === bestCoC && bestCoC > 0;
                      const isLowestCash = scenario.total_cash_needed === lowestCashNeeded;
                      const isSelected = selectedIndex === index;

                      return (
                        <tr
                          key={product.id}
                          onClick={() => handleSelectScenario(index)}
                          className={cn(
                            "border-b last:border-0 cursor-pointer transition-colors",
                            isSelected
                              ? "bg-primary-50 border-primary-200"
                              : "hover:bg-gray-50"
                          )}
                        >
                          <td className="py-3 px-3">
                            <div className="font-medium text-gray-900">
                              {product.name}
                            </div>
                            {product.description && (
                              <div className="text-xs text-gray-500 mt-0.5">
                                {product.description}
                              </div>
                            )}
                          </td>
                          <td className="py-3 px-3 text-right">
                            {formatPercent(product.down_payment_pct)}
                          </td>
                          <td className="py-3 px-3 text-right">
                            {formatPercent(product.interest_rate)}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span className={cn(isLowestCash && "text-green-600 font-medium")}>
                              {formatCurrency(scenario.total_cash_needed)}
                            </span>
                            {isLowestCash && (
                              <span className="ml-1 text-xs text-green-600">*</span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span
                              className={cn(
                                "font-medium",
                                getCashFlowColor(scenario.monthly_cash_flow),
                                isBestCashFlow && "underline"
                              )}
                            >
                              {formatCurrency(scenario.monthly_cash_flow)}
                            </span>
                            {isBestCashFlow && (
                              <span className="ml-1 text-xs text-green-600">*</span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span className={cn(isBestCoC && "text-green-600 font-medium")}>
                              {formatPercent(scenario.cash_on_cash_return)}
                            </span>
                            {isBestCoC && (
                              <span className="ml-1 text-xs text-green-600">*</span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span
                              className={cn(
                                "font-medium",
                                scenario.dscr >= 1.25
                                  ? "text-green-600"
                                  : scenario.dscr >= 1.0
                                  ? "text-yellow-600"
                                  : "text-red-600"
                              )}
                            >
                              {scenario.dscr.toFixed(2)}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-center">
                            {product.loan_type === "cash" ? (
                              <span className="badge-blue text-xs">Cash</span>
                            ) : scenario.monthly_cash_flow >= 0 ? (
                              scenario.dscr_status === "qualifies" ? (
                                <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                              ) : scenario.dscr_status === "borderline" ? (
                                <AlertTriangle className="h-4 w-4 text-yellow-500 mx-auto" />
                              ) : (
                                <span className="text-xs text-gray-400">-</span>
                              )
                            ) : (
                              <XCircle className="h-4 w-4 text-red-500 mx-auto" />
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Legend */}
              <div className="mt-3 pt-3 border-t flex flex-wrap gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-1">
                  <span className="text-green-600">*</span> Best in category
                </div>
                <div className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  DSCR qualifies (1.25+)
                </div>
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-yellow-500" />
                  Borderline (1.0-1.25)
                </div>
                <div className="flex items-center gap-1">
                  <XCircle className="h-3 w-3 text-red-500" />
                  Negative cash flow
                </div>
              </div>

              {/* Selected Scenario Details */}
              {selectedIndex !== null && scenarios[selectedIndex] && (
                <div className="mt-4 pt-4 border-t">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Info className="h-4 w-4 text-primary-600" />
                    {loanProducts[selectedIndex]?.name} - Details
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Down Payment</p>
                      <p className="font-semibold">
                        {formatCurrency(scenarios[selectedIndex].down_payment)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Loan Amount</p>
                      <p className="font-semibold">
                        {formatCurrency(scenarios[selectedIndex].loan_amount)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Monthly P&I</p>
                      <p className="font-semibold">
                        {formatCurrency(scenarios[selectedIndex].monthly_mortgage)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Cap Rate</p>
                      <p className="font-semibold">
                        {formatPercent(scenarios[selectedIndex].cap_rate)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Annual Cash Flow</p>
                      <p
                        className={cn(
                          "font-semibold",
                          getCashFlowColor(scenarios[selectedIndex].annual_cash_flow)
                        )}
                      >
                        {formatCurrency(scenarios[selectedIndex].annual_cash_flow)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">GRM</p>
                      <p className="font-semibold">
                        {scenarios[selectedIndex].gross_rent_multiplier.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Rent-to-Price</p>
                      <p className="font-semibold">
                        {formatPercent(scenarios[selectedIndex].rent_to_price_ratio)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">Break-even Occupancy</p>
                      <p className="font-semibold">
                        {formatPercent(scenarios[selectedIndex].break_even_occupancy)}
                      </p>
                    </div>
                  </div>

                  {/* DSCR Status for DSCR loans */}
                  {loanProducts[selectedIndex]?.is_dscr && (
                    <div
                      className={cn(
                        "mt-3 p-3 rounded-lg",
                        scenarios[selectedIndex].dscr_status === "qualifies"
                          ? "bg-green-50 border border-green-200"
                          : scenarios[selectedIndex].dscr_status === "borderline"
                          ? "bg-yellow-50 border border-yellow-200"
                          : "bg-red-50 border border-red-200"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        {scenarios[selectedIndex].dscr_status === "qualifies" ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : scenarios[selectedIndex].dscr_status === "borderline" ? (
                          <AlertTriangle className="h-5 w-5 text-yellow-600" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-600" />
                        )}
                        <div>
                          <p className="font-medium">
                            DSCR: {scenarios[selectedIndex].dscr.toFixed(2)}
                            {loanProducts[selectedIndex].min_dscr_required && (
                              <span className="text-gray-500 ml-1">
                                (min: {loanProducts[selectedIndex].min_dscr_required})
                              </span>
                            )}
                          </p>
                          <p className="text-sm text-gray-600">
                            {scenarios[selectedIndex].dscr_status === "qualifies"
                              ? "This property qualifies for a DSCR loan"
                              : scenarios[selectedIndex].dscr_status === "borderline"
                              ? "Borderline - may qualify with some lenders"
                              : "Does not meet minimum DSCR requirement"}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
