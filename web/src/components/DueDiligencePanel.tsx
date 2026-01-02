"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Search,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Phone,
  Mail,
  Building,
  FileText,
  Shield,
  Loader2,
} from "lucide-react";
import {
  api,
  DueDiligenceReportData,
  DueDiligenceFlag,
  DueDiligenceReportResponse,
} from "@/lib/api";

interface DueDiligencePanelProps {
  propertyId: string;
  propertyAddress: string;
}

export function DueDiligencePanel({
  propertyId,
  propertyAddress,
}: DueDiligencePanelProps) {
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [report, setReport] = useState<DueDiligenceReportData | null>(null);
  const [status, setStatus] = useState<string>("not_started");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState<string>("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["summary", "red_flags"])
  );

  const fetchReport = useCallback(async () => {
    try {
      const response = await api.getDueDiligenceReport(propertyId);
      setStatus(response.status);
      setProgress(response.progress || 0);
      setMessage(response.message || "");
      setJobId(response.job_id || null);

      if (response.report) {
        setReport(response.report);
      }
    } catch (err) {
      console.error("Failed to fetch due diligence report:", err);
    }
  }, [propertyId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  // Poll for updates if job is running
  useEffect(() => {
    if (status === "running" || status === "pending") {
      const interval = setInterval(fetchReport, 5000);
      return () => clearInterval(interval);
    }
  }, [status, fetchReport]);

  const handleStartResearch = async () => {
    setStarting(true);
    setError(null);

    try {
      const response = await api.startDueDiligence(propertyId);
      setStatus(response.status);
      setJobId(response.job_id);
      setMessage(response.message);

      // Start polling
      if (response.status === "pending") {
        fetchReport();
      }
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to start due diligence";
      setError(errorMessage);
    } finally {
      setStarting(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const renderFlag = (flag: DueDiligenceFlag, type: "red" | "yellow" | "green") => {
    const colors = {
      red: {
        bg: "bg-red-50",
        border: "border-red-200",
        icon: "text-red-600",
        title: "text-red-800",
      },
      yellow: {
        bg: "bg-yellow-50",
        border: "border-yellow-200",
        icon: "text-yellow-600",
        title: "text-yellow-800",
      },
      green: {
        bg: "bg-green-50",
        border: "border-green-200",
        icon: "text-green-600",
        title: "text-green-800",
      },
    };

    const c = colors[type];
    const Icon =
      type === "red"
        ? AlertTriangle
        : type === "yellow"
          ? AlertCircle
          : CheckCircle;

    return (
      <div
        key={flag.title}
        className={`${c.bg} ${c.border} border rounded-lg p-4`}
      >
        <div className="flex items-start gap-3">
          <Icon className={`h-5 w-5 ${c.icon} mt-0.5 flex-shrink-0`} />
          <div className="flex-1">
            <h4 className={`font-medium ${c.title}`}>
              {flag.title}
              {flag.severity && (
                <span className="ml-2 text-xs uppercase opacity-75">
                  ({flag.severity})
                </span>
              )}
            </h4>
            <p className="text-sm text-gray-700 mt-1">{flag.description}</p>
            {flag.source && (
              <p className="text-xs text-gray-500 mt-2">Source: {flag.source}</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderSectionHeader = (
    id: string,
    title: string,
    icon: React.ReactNode,
    count?: number
  ) => {
    const isExpanded = expandedSections.has(id);
    return (
      <button
        onClick={() => toggleSection(id)}
        className="w-full flex items-center justify-between py-3 px-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-gray-900">{title}</span>
          {count !== undefined && count > 0 && (
            <span className="bg-gray-200 text-gray-700 text-xs px-2 py-0.5 rounded-full">
              {count}
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>
    );
  };

  // Not started state
  if (status === "not_started" && !report) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600" />
            AI Due Diligence
          </h3>
        </div>

        <p className="text-gray-600 mb-4">
          Run a comprehensive AI-powered investigation of this property. The AI
          will research property history, legal issues, environmental concerns,
          market context, and gather professional contacts.
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <button
          onClick={handleStartResearch}
          disabled={starting}
          className="btn-primary flex items-center gap-2"
        >
          {starting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Starting Research...
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              Start Due Diligence Research
            </>
          )}
        </button>
      </div>
    );
  }

  // Running/pending state
  if (status === "running" || status === "pending") {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600" />
            AI Due Diligence
          </h3>
          <span className="flex items-center gap-2 text-blue-600">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Researching...
          </span>
        </div>

        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-800">
                AI Research in Progress
              </span>
            </div>
            <p className="text-blue-700 text-sm ml-8">
              {message || "Searching public records and gathering information..."}
            </p>
          </div>

          {progress > 0 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}

          <p className="text-sm text-gray-500 text-center">
            This may take 2-5 minutes. You can leave this page and come back.
          </p>
        </div>
      </div>
    );
  }

  // Failed state
  if (status === "failed" || report?.status === "failed") {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary-600" />
            AI Due Diligence
          </h3>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <div>
              <p className="font-medium text-red-800">Research Failed</p>
              <p className="text-red-700 text-sm">
                {report?.errors?.join(", ") || "An error occurred during research."}
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={handleStartResearch}
          disabled={starting}
          className="btn-primary flex items-center gap-2"
        >
          {starting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Retry Research
        </button>
      </div>
    );
  }

  // Completed state with report
  if (!report) {
    return null;
  }

  const redFlagCount = report.red_flags?.length || 0;
  const yellowFlagCount = report.yellow_flags?.length || 0;
  const greenFlagCount = report.green_flags?.length || 0;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary-600" />
          AI Due Diligence Report
        </h3>
        <div className="flex items-center gap-3 text-sm">
          {redFlagCount > 0 && (
            <span className="flex items-center gap-1 text-red-600">
              <AlertTriangle className="h-4 w-4" />
              {redFlagCount} Red Flags
            </span>
          )}
          {yellowFlagCount > 0 && (
            <span className="flex items-center gap-1 text-yellow-600">
              <AlertCircle className="h-4 w-4" />
              {yellowFlagCount} Investigate
            </span>
          )}
          {greenFlagCount > 0 && (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle className="h-4 w-4" />
              {greenFlagCount} Positive
            </span>
          )}
        </div>
      </div>

      <div className="space-y-4">
        {/* Executive Summary */}
        {report.executive_summary && (
          <div>
            {renderSectionHeader(
              "summary",
              "Executive Summary",
              <FileText className="h-5 w-5 text-gray-600" />
            )}
            {expandedSections.has("summary") && (
              <div className="mt-3 p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-700 whitespace-pre-wrap">
                  {report.executive_summary}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Red Flags */}
        {redFlagCount > 0 && (
          <div>
            {renderSectionHeader(
              "red_flags",
              "Red Flags",
              <AlertTriangle className="h-5 w-5 text-red-600" />,
              redFlagCount
            )}
            {expandedSections.has("red_flags") && (
              <div className="mt-3 space-y-3">
                {report.red_flags?.map((flag) => renderFlag(flag, "red"))}
              </div>
            )}
          </div>
        )}

        {/* Yellow Flags */}
        {yellowFlagCount > 0 && (
          <div>
            {renderSectionHeader(
              "yellow_flags",
              "Investigate Further",
              <AlertCircle className="h-5 w-5 text-yellow-600" />,
              yellowFlagCount
            )}
            {expandedSections.has("yellow_flags") && (
              <div className="mt-3 space-y-3">
                {report.yellow_flags?.map((flag) => renderFlag(flag, "yellow"))}
              </div>
            )}
          </div>
        )}

        {/* Green Flags */}
        {greenFlagCount > 0 && (
          <div>
            {renderSectionHeader(
              "green_flags",
              "Positive Findings",
              <CheckCircle className="h-5 w-5 text-green-600" />,
              greenFlagCount
            )}
            {expandedSections.has("green_flags") && (
              <div className="mt-3 space-y-3">
                {report.green_flags?.map((flag) => renderFlag(flag, "green"))}
              </div>
            )}
          </div>
        )}

        {/* Listing Agent Contact */}
        {report.findings?.listing_agent && (
          <div>
            {renderSectionHeader(
              "contacts",
              "Listing Agent",
              <Building className="h-5 w-5 text-gray-600" />
            )}
            {expandedSections.has("contacts") && (
              <div className="mt-3 p-4 bg-gray-50 rounded-lg">
                <div className="space-y-2">
                  {report.findings.listing_agent.name && (
                    <p className="font-medium text-gray-900">
                      {report.findings.listing_agent.name}
                    </p>
                  )}
                  {report.findings.listing_agent.company && (
                    <p className="text-gray-600 text-sm">
                      {report.findings.listing_agent.company}
                    </p>
                  )}
                  <div className="flex gap-4 mt-2">
                    {report.findings.listing_agent.phone && (
                      <a
                        href={`tel:${report.findings.listing_agent.phone}`}
                        className="flex items-center gap-1 text-primary-600 hover:underline"
                      >
                        <Phone className="h-4 w-4" />
                        {report.findings.listing_agent.phone}
                      </a>
                    )}
                    {report.findings.listing_agent.email && (
                      <a
                        href={`mailto:${report.findings.listing_agent.email}`}
                        className="flex items-center gap-1 text-primary-600 hover:underline"
                      >
                        <Mail className="h-4 w-4" />
                        {report.findings.listing_agent.email}
                      </a>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recommended Actions */}
        {report.recommended_actions && report.recommended_actions.length > 0 && (
          <div>
            {renderSectionHeader(
              "actions",
              "Recommended Actions",
              <CheckCircle className="h-5 w-5 text-blue-600" />,
              report.recommended_actions.length
            )}
            {expandedSections.has("actions") && (
              <div className="mt-3 p-4 bg-blue-50 rounded-lg">
                <ul className="space-y-2">
                  {report.recommended_actions.map((action, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <span className="text-blue-600 font-medium">{i + 1}.</span>
                      {action}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Questions for Seller */}
        {report.questions_for_seller && report.questions_for_seller.length > 0 && (
          <div>
            {renderSectionHeader(
              "questions",
              "Questions for Seller",
              <FileText className="h-5 w-5 text-purple-600" />,
              report.questions_for_seller.length
            )}
            {expandedSections.has("questions") && (
              <div className="mt-3 p-4 bg-purple-50 rounded-lg">
                <ul className="space-y-2">
                  {report.questions_for_seller.map((q, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <span className="text-purple-600">•</span>
                      {q}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Inspection Focus Areas */}
        {report.inspection_focus_areas && report.inspection_focus_areas.length > 0 && (
          <div>
            {renderSectionHeader(
              "inspection",
              "Inspection Focus Areas",
              <Search className="h-5 w-5 text-orange-600" />,
              report.inspection_focus_areas.length
            )}
            {expandedSections.has("inspection") && (
              <div className="mt-3 p-4 bg-orange-50 rounded-lg">
                <ul className="space-y-2">
                  {report.inspection_focus_areas.map((area, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <span className="text-orange-600">•</span>
                      {area}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Sources */}
        {report.sources_consulted && report.sources_consulted.length > 0 && (
          <div>
            {renderSectionHeader(
              "sources",
              "Sources Consulted",
              <ExternalLink className="h-5 w-5 text-gray-600" />,
              report.sources_consulted.length
            )}
            {expandedSections.has("sources") && (
              <div className="mt-3 p-4 bg-gray-50 rounded-lg">
                <ul className="space-y-1 text-sm">
                  {report.sources_consulted.slice(0, 10).map((source, i) => (
                    <li key={i}>
                      <a
                        href={source}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:underline truncate block"
                      >
                        {source}
                      </a>
                    </li>
                  ))}
                  {report.sources_consulted.length > 10 && (
                    <li className="text-gray-500">
                      ...and {report.sources_consulted.length - 10} more sources
                    </li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Report Metadata */}
        <div className="pt-4 border-t text-sm text-gray-500 flex justify-between">
          <span>
            Report generated:{" "}
            {report.completed_at
              ? new Date(report.completed_at).toLocaleString()
              : "N/A"}
          </span>
          <button
            onClick={handleStartResearch}
            disabled={starting}
            className="text-primary-600 hover:underline flex items-center gap-1"
          >
            <RefreshCw className="h-4 w-4" />
            Re-run Research
          </button>
        </div>
      </div>
    </div>
  );
}
