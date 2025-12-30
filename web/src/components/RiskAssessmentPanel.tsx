"use client";

/**
 * Risk Assessment Panel
 *
 * Displays investment risk analysis with flags and recommendations.
 */

import { useState, useEffect } from "react";
import {
  AlertTriangle,
  AlertCircle,
  AlertOctagon,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Loader2,
  RefreshCw,
  Shield,
  XCircle,
  ClipboardList,
  Home,
  DollarSign,
  MapPin,
  TrendingUp,
} from "lucide-react";
import { api, RiskAssessment, RiskFlag } from "@/lib/api";
import { cn } from "@/lib/utils";

interface RiskAssessmentPanelProps {
  propertyId: string;
}

function RiskLevelBadge({ level, score }: { level: string; score: number }) {
  const config: Record<string, { color: string; icon: React.ElementType; label: string }> = {
    critical: { color: "bg-red-100 text-red-800 border-red-300", icon: AlertOctagon, label: "Critical Risk" },
    high: { color: "bg-orange-100 text-orange-800 border-orange-300", icon: AlertTriangle, label: "High Risk" },
    medium: { color: "bg-yellow-100 text-yellow-800 border-yellow-300", icon: AlertCircle, label: "Medium Risk" },
    low: { color: "bg-green-100 text-green-800 border-green-300", icon: CheckCircle, label: "Low Risk" },
    unknown: { color: "bg-gray-100 text-gray-600 border-gray-300", icon: Info, label: "Unknown" },
  };

  const { color, icon: Icon, label } = config[level] || config.unknown;

  return (
    <div className={cn("inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 font-medium", color)}>
      <Icon className="h-5 w-5" />
      <span>{label}</span>
      <span className="text-sm font-normal">({score})</span>
    </div>
  );
}

function FlagCard({ flag }: { flag: RiskFlag }) {
  const [expanded, setExpanded] = useState(false);

  const severityColors: Record<string, string> = {
    critical: "border-red-300 bg-red-50",
    high: "border-orange-300 bg-orange-50",
    medium: "border-yellow-300 bg-yellow-50",
    low: "border-green-300 bg-green-50",
  };

  const severityIcons: Record<string, React.ElementType> = {
    critical: AlertOctagon,
    high: AlertTriangle,
    medium: AlertCircle,
    low: Info,
  };

  const categoryIcons: Record<string, React.ElementType> = {
    property: Home,
    financial: DollarSign,
    location: MapPin,
    market: TrendingUp,
  };

  const Icon = severityIcons[flag.severity] || Info;
  const CategoryIcon = categoryIcons[flag.category] || Info;

  return (
    <div className={cn("border rounded-lg p-3", severityColors[flag.severity] || "border-gray-200")}>
      <div
        className="flex items-start gap-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <Icon className={cn(
          "h-5 w-5 mt-0.5",
          flag.severity === "critical" ? "text-red-600" :
          flag.severity === "high" ? "text-orange-600" :
          flag.severity === "medium" ? "text-yellow-600" : "text-green-600"
        )} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900">{flag.title}</span>
            <span className="inline-flex items-center gap-1 text-xs text-gray-500">
              <CategoryIcon className="h-3 w-3" />
              {flag.category}
            </span>
          </div>
          {(expanded || flag.severity === "critical") && (
            <p className="text-sm text-gray-600 mt-1">{flag.description}</p>
          )}
          {expanded && flag.recommendation && (
            <p className="text-sm text-primary-700 mt-2 flex items-start gap-1">
              <ClipboardList className="h-4 w-4 mt-0.5 flex-shrink-0" />
              {flag.recommendation}
            </p>
          )}
        </div>
        <button className="text-gray-400">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}

export function RiskAssessmentPanel({ propertyId }: RiskAssessmentPanelProps) {
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  const fetchAssessment = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRiskAssessment(propertyId);
      setAssessment(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load risk assessment");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssessment();
  }, [propertyId]);

  const allFlags = assessment ? [
    ...assessment.property_flags,
    ...assessment.financial_flags,
    ...assessment.location_flags,
    ...assessment.market_flags,
  ].sort((a, b) => {
    const order = { critical: 0, high: 1, medium: 2, low: 3 };
    return (order[a.severity as keyof typeof order] || 4) - (order[b.severity as keyof typeof order] || 4);
  }) : [];

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary-600" />
          Risk Assessment
        </h3>
        <div className="flex items-center gap-2">
          {assessment && !loading && (
            <button
              onClick={fetchAssessment}
              className="p-1.5 text-gray-400 hover:text-gray-600"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          )}
          {assessment && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 text-gray-400 hover:text-gray-600"
            >
              {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary-600 mr-2" />
          <span className="text-gray-600">Analyzing risks...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
            <div>
              <p className="text-red-700">{error}</p>
              <button
                onClick={fetchAssessment}
                className="text-red-600 hover:text-red-800 text-sm mt-2 flex items-center gap-1"
              >
                <RefreshCw className="h-4 w-4" />
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {assessment && !loading && (
        <div className="space-y-4">
          {/* Risk Level */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <RiskLevelBadge level={assessment.risk_level} score={assessment.risk_score} />
            <div className="text-right text-sm">
              <div className="flex items-center gap-4">
                {assessment.critical_count > 0 && (
                  <span className="text-red-600 font-medium">
                    {assessment.critical_count} critical
                  </span>
                )}
                {assessment.high_count > 0 && (
                  <span className="text-orange-600 font-medium">
                    {assessment.high_count} high
                  </span>
                )}
                {assessment.medium_count > 0 && (
                  <span className="text-yellow-600 font-medium">
                    {assessment.medium_count} medium
                  </span>
                )}
                {assessment.low_count > 0 && (
                  <span className="text-green-600 font-medium">
                    {assessment.low_count} low
                  </span>
                )}
              </div>
              <p className="text-gray-500 mt-1">{assessment.total_flags} total flags</p>
            </div>
          </div>

          {expanded && (
            <>
              {/* Deal Breakers */}
              {assessment.deal_breakers.length > 0 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-medium text-red-800 flex items-center gap-2 mb-2">
                    <XCircle className="h-5 w-5" />
                    Deal Breakers
                  </h4>
                  <ul className="space-y-1">
                    {assessment.deal_breakers.map((item, i) => (
                      <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                        <span className="text-red-400">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Investigate */}
              {assessment.investigate.length > 0 && (
                <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <h4 className="font-medium text-orange-800 flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5" />
                    Needs Investigation
                  </h4>
                  <ul className="space-y-1">
                    {assessment.investigate.map((item, i) => (
                      <li key={i} className="text-sm text-orange-700 flex items-start gap-2">
                        <span className="text-orange-400">•</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* All Flags */}
              {allFlags.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">All Risk Flags</h4>
                  <div className="space-y-2">
                    {allFlags.map((flag, i) => (
                      <FlagCard key={i} flag={flag} />
                    ))}
                  </div>
                </div>
              )}

              {/* Due Diligence */}
              {assessment.due_diligence_items.length > 0 && (
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-800 flex items-center gap-2 mb-2">
                    <ClipboardList className="h-5 w-5" />
                    Recommended Due Diligence
                  </h4>
                  <ul className="space-y-1">
                    {assessment.due_diligence_items.map((item, i) => (
                      <li key={i} className="text-sm text-blue-700 flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* No Issues */}
              {allFlags.length === 0 && (
                <div className="text-center py-6">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-2" />
                  <p className="text-green-700 font-medium">No significant risks identified</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Always conduct your own due diligence before investing.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
