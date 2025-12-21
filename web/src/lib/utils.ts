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
 * Format a number as a percentage
 */
export function formatPercent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value);
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
