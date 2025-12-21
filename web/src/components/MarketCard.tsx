import Link from "next/link";
import { TrendingUp, TrendingDown, Minus, Users, Briefcase } from "lucide-react";
import { Market } from "@/lib/api";
import {
  formatCurrency,
  formatPercent,
  getScoreBadge,
  cn
} from "@/lib/utils";
import { ScoreGauge } from "./ScoreGauge";

interface MarketCardProps {
  market: Market;
  rank?: number;
}

export function MarketCard({ market, rank }: MarketCardProps) {
  const getTrendIcon = (value?: number) => {
    if (!value) return <Minus className="h-4 w-4 text-gray-400" />;
    if (value > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    return <TrendingDown className="h-4 w-4 text-red-500" />;
  };

  return (
    <Link href={`/markets/${market.id}`}>
      <div className="card-hover">
        <div className="flex justify-between items-start gap-4">
          {/* Market Info */}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              {rank && (
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary-100 text-primary-700 text-xs font-bold">
                  {rank}
                </span>
              )}
              <h3 className="font-semibold text-gray-900">
                {market.name}, {market.state}
              </h3>
            </div>
            <p className="text-sm text-gray-500 mt-1">{market.metro}</p>

            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <p className="text-xs text-gray-500">Median Price</p>
                <p className="font-semibold">
                  {formatCurrency(market.median_home_price)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Median Rent</p>
                <p className="font-semibold">
                  {formatCurrency(market.median_rent)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Rent/Price Ratio</p>
                <p className="font-semibold">
                  {market.rent_to_price_ratio
                    ? `${market.rent_to_price_ratio.toFixed(2)}%`
                    : "N/A"
                  }
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Price Change (1Y)</p>
                <div className="flex items-center gap-1">
                  {getTrendIcon(market.price_change_1yr)}
                  <span className={cn(
                    "font-semibold",
                    (market.price_change_1yr || 0) >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  )}>
                    {market.price_change_1yr
                      ? `${market.price_change_1yr > 0 ? "+" : ""}${market.price_change_1yr.toFixed(1)}%`
                      : "N/A"
                    }
                  </span>
                </div>
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center gap-1">
                <span className={cn("badge", getScoreBadge(market.cash_flow_score))}>
                  Cash Flow: {market.cash_flow_score.toFixed(0)}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <span className={cn("badge", getScoreBadge(market.growth_score))}>
                  Growth: {market.growth_score.toFixed(0)}
                </span>
              </div>
            </div>
          </div>

          {/* Overall Score */}
          <div className="flex-shrink-0">
            <ScoreGauge
              score={market.overall_score}
              label="Overall"
              size="sm"
            />
          </div>
        </div>
      </div>
    </Link>
  );
}
