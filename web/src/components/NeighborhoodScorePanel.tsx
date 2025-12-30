"use client";

/**
 * Neighborhood Score Panel
 *
 * Displays composite neighborhood score with component breakdown.
 */

import { useState, useEffect } from "react";
import {
  MapPin,
  Footprints,
  Train,
  Bike,
  GraduationCap,
  ShieldCheck,
  Droplets,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
  Info,
} from "lucide-react";
import { api, NeighborhoodScore, LocationScore } from "@/lib/api";
import { cn } from "@/lib/utils";

interface NeighborhoodScorePanelProps {
  propertyId: string;
}

function GradeBadge({ grade, score }: { grade: string; score?: number }) {
  const colors: Record<string, string> = {
    A: "bg-green-100 text-green-800 border-green-300",
    B: "bg-blue-100 text-blue-800 border-blue-300",
    C: "bg-yellow-100 text-yellow-800 border-yellow-300",
    D: "bg-orange-100 text-orange-800 border-orange-300",
    F: "bg-red-100 text-red-800 border-red-300",
    "N/A": "bg-gray-100 text-gray-600 border-gray-300",
  };

  return (
    <div className={cn(
      "inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 font-bold",
      colors[grade] || colors["N/A"]
    )}>
      <span className="text-2xl">{grade}</span>
      {score !== undefined && (
        <span className="text-lg font-normal">({score})</span>
      )}
    </div>
  );
}

function ScoreBar({
  label,
  score,
  icon: Icon,
  description,
  weight,
}: {
  label: string;
  score?: number;
  icon: React.ElementType;
  description?: string;
  weight: number;
}) {
  const getScoreColor = (score?: number) => {
    if (score === undefined) return "bg-gray-200";
    if (score >= 80) return "bg-green-500";
    if (score >= 60) return "bg-blue-500";
    if (score >= 40) return "bg-yellow-500";
    if (score >= 20) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-gray-500" />
          <span className="font-medium text-gray-700">{label}</span>
          <span className="text-xs text-gray-400">({(weight * 100).toFixed(0)}%)</span>
        </div>
        <span className={cn(
          "font-bold",
          score === undefined ? "text-gray-400" : "text-gray-900"
        )}>
          {score !== undefined ? score : "N/A"}
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={cn("h-full transition-all duration-500", getScoreColor(score))}
          style={{ width: `${score ?? 0}%` }}
        />
      </div>
      {description && (
        <p className="text-xs text-gray-500 mt-0.5">{description}</p>
      )}
    </div>
  );
}

export function NeighborhoodScorePanel({ propertyId }: NeighborhoodScorePanelProps) {
  const [score, setScore] = useState<NeighborhoodScore | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  const fetchScore = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getNeighborhoodScoreForProperty(propertyId);
      setScore(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load neighborhood score");
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on mount
  useEffect(() => {
    fetchScore();
  }, [propertyId]);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <MapPin className="h-5 w-5 text-primary-600" />
          Neighborhood Score
        </h3>
        <div className="flex items-center gap-2">
          {score && !loading && (
            <button
              onClick={fetchScore}
              className="p-1.5 text-gray-400 hover:text-gray-600"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          )}
          {score && (
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
          <span className="text-gray-600">Calculating neighborhood score...</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
            <div>
              <p className="text-red-700">{error}</p>
              <button
                onClick={fetchScore}
                className="text-red-600 hover:text-red-800 text-sm mt-2 flex items-center gap-1"
              >
                <RefreshCw className="h-4 w-4" />
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {score && !loading && (
        <div className="space-y-4">
          {/* Overall Grade */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm text-gray-500 mb-1">Overall Grade</p>
              <GradeBadge grade={score.grade} score={score.overall_score} />
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Data Completeness</p>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500"
                    style={{ width: `${score.data_completeness}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {score.data_completeness.toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                {score.data_sources_used.length} of 6 sources
              </p>
            </div>
          </div>

          {expanded && (
            <>
              {/* Score Breakdown */}
              <div className="space-y-4">
                <ScoreBar
                  label="Walkability"
                  score={score.walkability.score}
                  icon={Footprints}
                  description={score.walkability.description}
                  weight={score.walkability.weight}
                />
                <ScoreBar
                  label="Transit Access"
                  score={score.transit.score}
                  icon={Train}
                  description={score.transit.description}
                  weight={score.transit.weight}
                />
                <ScoreBar
                  label="Bikeability"
                  score={score.bikeability.score}
                  icon={Bike}
                  description={score.bikeability.description}
                  weight={score.bikeability.weight}
                />
                <ScoreBar
                  label="Schools"
                  score={score.schools.score}
                  icon={GraduationCap}
                  description={score.schools.description}
                  weight={score.schools.weight}
                />
                <ScoreBar
                  label="Safety (Low Noise)"
                  score={score.safety.score}
                  icon={ShieldCheck}
                  description={score.safety.description}
                  weight={score.safety.weight}
                />
                <ScoreBar
                  label="Flood Risk (Low Risk)"
                  score={score.flood_risk.score}
                  icon={Droplets}
                  description={score.flood_risk.description}
                  weight={score.flood_risk.weight}
                />
              </div>

              {/* School Summary */}
              {score.school_summary.count > 0 && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-900 flex items-center gap-2 mb-2">
                    <GraduationCap className="h-4 w-4" />
                    Nearby Schools
                  </h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-blue-600">{score.school_summary.count}</span>
                      <span className="text-blue-700"> schools nearby</span>
                    </div>
                    {score.school_summary.avg_rating && (
                      <div>
                        <span className="text-blue-600">{score.school_summary.avg_rating.toFixed(1)}/10</span>
                        <span className="text-blue-700"> avg rating</span>
                      </div>
                    )}
                    {score.school_summary.public_count > 0 && (
                      <div>
                        <span className="text-blue-600">{score.school_summary.public_count}</span>
                        <span className="text-blue-700"> public</span>
                      </div>
                    )}
                    {score.school_summary.private_count > 0 && (
                      <div>
                        <span className="text-blue-600">{score.school_summary.private_count}</span>
                        <span className="text-blue-700"> private</span>
                      </div>
                    )}
                  </div>
                  {score.school_summary.top_rated && (
                    <p className="text-xs text-blue-600 mt-2">
                      Top rated: {score.school_summary.top_rated}
                    </p>
                  )}
                </div>
              )}

              {/* Data Sources */}
              <div className="flex flex-wrap gap-1.5">
                {score.data_sources_used.map((source) => (
                  <span
                    key={source}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full"
                  >
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    {source}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
