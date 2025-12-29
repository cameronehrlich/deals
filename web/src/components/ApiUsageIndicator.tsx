"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, XCircle } from "lucide-react";
import { api, ApiUsage } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ApiUsageIndicatorProps {
  className?: string;
  compact?: boolean;
}

export function ApiUsageIndicator({ className, compact = false }: ApiUsageIndicatorProps) {
  const [usage, setUsage] = useState<ApiUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function fetchUsage() {
      try {
        const data = await api.getApiUsage();
        setUsage(data);
        setError(false);
      } catch (err) {
        console.error("Failed to fetch API usage:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    fetchUsage();
    // Refresh every 5 minutes
    const interval = setInterval(fetchUsage, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className={cn("flex items-center gap-2 text-sm text-gray-400", className)}>
        <Activity className="h-4 w-4 animate-pulse" />
        {!compact && <span>Loading...</span>}
      </div>
    );
  }

  if (error || !usage) {
    return (
      <div className={cn("flex items-center gap-2 text-sm text-gray-400", className)}>
        <Activity className="h-4 w-4" />
        {!compact && <span>API unavailable</span>}
      </div>
    );
  }

  // Determine status color and icon
  let statusColor = "text-green-600";
  let bgColor = "bg-green-100";
  let barColor = "bg-green-500";
  let Icon = Activity;

  if (usage.warning === "limit_reached") {
    statusColor = "text-red-600";
    bgColor = "bg-red-100";
    barColor = "bg-red-500";
    Icon = XCircle;
  } else if (usage.warning === "approaching_limit") {
    statusColor = "text-amber-600";
    bgColor = "bg-amber-100";
    barColor = "bg-amber-500";
    Icon = AlertTriangle;
  }

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Icon className={cn("h-4 w-4", statusColor)} />
        <span className={cn("text-sm font-medium", statusColor)}>
          {usage.requests_remaining}
        </span>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="flex items-center gap-2">
        <Icon className={cn("h-4 w-4", statusColor)} />
        <span className="text-sm text-gray-600">API:</span>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-2">
        <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={cn("h-full transition-all", barColor)}
            style={{ width: `${Math.min(usage.percent_used, 100)}%` }}
          />
        </div>
        <span className={cn("text-sm font-medium", statusColor)}>
          {usage.requests_remaining}/{usage.requests_limit}
        </span>
      </div>
    </div>
  );
}

// Banner component for warnings
export function ApiUsageBanner() {
  const [usage, setUsage] = useState<ApiUsage | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    async function fetchUsage() {
      try {
        const data = await api.getApiUsage();
        setUsage(data);
      } catch (err) {
        // Silently fail for banner
      }
    }
    fetchUsage();
  }, []);

  if (dismissed || !usage || !usage.warning) {
    return null;
  }

  const isLimitReached = usage.warning === "limit_reached";

  return (
    <div
      className={cn(
        "px-4 py-3 flex items-center justify-between",
        isLimitReached ? "bg-red-50 border-b border-red-200" : "bg-amber-50 border-b border-amber-200"
      )}
    >
      <div className="flex items-center gap-3">
        {isLimitReached ? (
          <XCircle className="h-5 w-5 text-red-600" />
        ) : (
          <AlertTriangle className="h-5 w-5 text-amber-600" />
        )}
        <p className={cn("text-sm", isLimitReached ? "text-red-800" : "text-amber-800")}>
          {isLimitReached ? (
            <>
              <strong>API limit reached</strong> ({usage.requests_used}/{usage.requests_limit} requests).
              Import properties via URL or upgrade your plan.
            </>
          ) : (
            <>
              <strong>API limit almost reached</strong> ({usage.requests_used}/{usage.requests_limit} requests).
              Consider upgrading for more searches.
            </>
          )}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <a
          href="https://rapidapi.com/datascraper/api/us-real-estate/pricing"
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "text-sm font-medium underline",
            isLimitReached ? "text-red-700 hover:text-red-800" : "text-amber-700 hover:text-amber-800"
          )}
        >
          Upgrade Plan
        </a>
        <button
          onClick={() => setDismissed(true)}
          className={cn(
            "text-sm font-medium",
            isLimitReached ? "text-red-600 hover:text-red-700" : "text-amber-600 hover:text-amber-700"
          )}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
