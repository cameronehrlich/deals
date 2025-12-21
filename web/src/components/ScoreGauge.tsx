"use client";

import { cn, getScoreColor } from "@/lib/utils";

interface ScoreGaugeProps {
  score: number;
  label: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function ScoreGauge({
  score,
  label,
  size = "md",
  showLabel = true
}: ScoreGaugeProps) {
  const sizes = {
    sm: { width: 60, height: 60, fontSize: "text-sm", strokeWidth: 6 },
    md: { width: 80, height: 80, fontSize: "text-lg", strokeWidth: 8 },
    lg: { width: 120, height: 120, fontSize: "text-2xl", strokeWidth: 10 },
  };

  const { width, height, fontSize, strokeWidth } = sizes[size];
  const radius = (width - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  const getColor = (score: number) => {
    if (score >= 70) return "#22c55e"; // green-500
    if (score >= 50) return "#eab308"; // yellow-500
    return "#ef4444"; // red-500
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width, height }}>
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={width / 2}
            cy={height / 2}
            r={radius}
            fill="none"
            stroke={getColor(score)}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div
          className={cn(
            "absolute inset-0 flex items-center justify-center font-bold",
            fontSize,
            getScoreColor(score)
          )}
        >
          {score.toFixed(0)}
        </div>
      </div>
      {showLabel && (
        <span className="text-xs text-gray-500 text-center">{label}</span>
      )}
    </div>
  );
}
