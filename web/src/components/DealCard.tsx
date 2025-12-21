import Link from "next/link";
import { MapPin, Bed, Bath, Square, Clock } from "lucide-react";
import { Deal } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  getCashFlowColor,
  getScoreBadge,
  cn
} from "@/lib/utils";
import { ScoreGauge } from "./ScoreGauge";

interface DealCardProps {
  deal: Deal;
}

export function DealCard({ deal }: DealCardProps) {
  const { property, financials, score } = deal;

  return (
    <Link href={`/deals/${deal.id}`}>
      <div className="card-hover">
        <div className="flex justify-between items-start gap-4">
          {/* Property Info */}
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">
              {property.address}
            </h3>
            <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
              <MapPin className="h-3.5 w-3.5" />
              {property.city}, {property.state} {property.zip_code}
            </div>

            {/* Property Details */}
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <Bed className="h-4 w-4" />
                {property.bedrooms}
              </span>
              <span className="flex items-center gap-1">
                <Bath className="h-4 w-4" />
                {property.bathrooms}
              </span>
              {property.sqft && (
                <span className="flex items-center gap-1">
                  <Square className="h-4 w-4" />
                  {property.sqft.toLocaleString()} sqft
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {property.days_on_market}d
              </span>
            </div>

            {/* Financials */}
            <div className="grid grid-cols-3 gap-4 mt-4">
              <div>
                <p className="text-xs text-gray-500">Price</p>
                <p className="font-semibold">
                  {formatCurrency(property.list_price)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Cash Flow</p>
                <p className={cn(
                  "font-semibold",
                  getCashFlowColor(financials?.monthly_cash_flow || 0)
                )}>
                  {financials
                    ? formatCurrency(financials.monthly_cash_flow) + "/mo"
                    : "N/A"
                  }
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">CoC Return</p>
                <p className="font-semibold">
                  {financials
                    ? formatPercent(financials.cash_on_cash_return)
                    : "N/A"
                  }
                </p>
              </div>
            </div>

            {/* Pros/Cons Preview */}
            {(deal.pros.length > 0 || deal.cons.length > 0) && (
              <div className="mt-4 flex flex-wrap gap-2">
                {deal.pros.slice(0, 2).map((pro, i) => (
                  <span key={i} className="badge-green text-xs truncate max-w-[150px]">
                    {pro}
                  </span>
                ))}
                {deal.cons.slice(0, 1).map((con, i) => (
                  <span key={i} className="badge-yellow text-xs truncate max-w-[150px]">
                    {con}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Score */}
          {score && (
            <div className="flex-shrink-0">
              <ScoreGauge
                score={score.overall_score}
                label="Score"
                size="sm"
              />
              {score.rank && (
                <p className="text-center text-xs text-gray-500 mt-1">
                  #{score.rank}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
