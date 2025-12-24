import { clsx, type ClassValue } from "clsx";

/**
 * Utility function to merge class names
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Format a number as currency
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format a decimal as a percentage (0.05 -> "5.0%")
 */
export function formatPercent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
}

/**
 * Format a value that is already in percentage form (5.123 -> "5.1%", -2.5 -> "-2.5%")
 * Optionally shows a + sign for positive values
 */
export function formatPercentValue(value: number, showPlus: boolean = false): string {
  const formatted = value.toFixed(1);
  if (showPlus && value > 0) {
    return `+${formatted}%`;
  }
  return `${formatted}%`;
}

/**
 * Get Tailwind color class based on cash flow value
 */
export function getCashFlowColor(cashFlow: number): string {
  if (cashFlow >= 200) return "text-green-600";
  if (cashFlow >= 0) return "text-yellow-600";
  return "text-red-600";
}

/**
 * Get Tailwind color class based on score
 */
export function getScoreColor(score: number): string {
  if (score >= 70) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-600";
}

/**
 * Get risk badge styling
 */
export function getRiskBadge(risk: string): string {
  switch (risk.toLowerCase()) {
    case "low":
      return "badge-green";
    case "medium":
      return "badge-yellow";
    case "high":
      return "badge-red";
    default:
      return "badge-gray";
  }
}

/**
 * Get score badge styling based on numeric score
 */
export function getScoreBadge(score: number): string {
  if (score >= 70) return "badge-green";
  if (score >= 50) return "badge-yellow";
  return "badge-red";
}

/**
 * Format a number with commas
 */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + "...";
}
