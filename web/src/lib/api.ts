/**
 * API client for Real Estate Deal Platform
 */

const API_URL = process.env.API_URL || "http://localhost:8000";

export interface Market {
  id: string;
  name: string;
  state: string;
  metro: string;
  population?: number;
  median_home_price?: number;
  median_rent?: number;
  rent_to_price_ratio?: number;
  price_change_1yr?: number;
  job_growth_1yr?: number;
  overall_score: number;
  cash_flow_score: number;
  growth_score: number;
  rank?: number;
}

export interface MarketDetail extends Market {
  region?: string;
  population_growth_1yr?: number;
  population_growth_5yr?: number;
  unemployment_rate?: number;
  major_employers: string[];
  median_household_income?: number;
  price_change_5yr?: number;
  rent_change_1yr?: number;
  months_of_inventory?: number;
  days_on_market_avg?: number;
  price_trend: string;
  rent_trend: string;
  landlord_friendly: boolean;
  property_tax_rate?: number;
  insurance_risk?: string;
  affordability_score: number;
  stability_score: number;
  liquidity_score: number;
}

export interface Property {
  id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  list_price: number;
  estimated_rent?: number;
  bedrooms: number;
  bathrooms: number;
  sqft?: number;
  property_type: string;
  days_on_market: number;
  price_per_sqft?: number;
}

export interface Financials {
  monthly_cash_flow: number;
  annual_cash_flow: number;
  cash_on_cash_return: number;
  cap_rate: number;
  gross_rent_multiplier: number;
  rent_to_price_ratio: number;
  total_cash_invested: number;
  break_even_occupancy: number;
  dscr?: number;
}

export interface DealScore {
  overall_score: number;
  financial_score: number;
  market_score: number;
  risk_score: number;
  liquidity_score: number;
  rank?: number;
  percentile?: number;
  strategy_scores: Record<string, number>;
}

export interface Deal {
  id: string;
  property: Property;
  score?: DealScore;
  financials?: Financials;
  market_name?: string;
  pipeline_status: string;
  pros: string[];
  cons: string[];
}

export interface SensitivityResult {
  base_cash_flow: number;
  base_coc: number;
  base_cap_rate: number;
  rate_increase_1pct: number;
  rate_increase_2pct: number;
  break_even_rate?: number;
  vacancy_10pct: number;
  vacancy_15pct: number;
  break_even_vacancy?: number;
  rent_decrease_5pct: number;
  rent_decrease_10pct: number;
  break_even_rent?: number;
  moderate_stress: number;
  severe_stress: number;
  survives_moderate: boolean;
  survives_severe: boolean;
  risk_rating: string;
}

export interface AnalysisResult {
  financials: Financials & {
    purchase_price: number;
    down_payment: number;
    loan_amount: number;
    closing_costs: number;
    monthly_mortgage: number;
    monthly_taxes: number;
    monthly_insurance: number;
    monthly_hoa: number;
    monthly_maintenance: number;
    monthly_capex: number;
    monthly_vacancy_reserve: number;
    monthly_property_management: number;
    total_monthly_expenses: number;
    net_operating_income: number;
  };
  sensitivity: SensitivityResult;
  verdict: string;
  recommendations: string[];
}

export interface ImportUrlRequest {
  url: string;
  down_payment_pct?: number;
  interest_rate?: number;
}

export interface ImportUrlResponse {
  success: boolean;
  deal?: Deal;
  source?: string;
  message: string;
  warnings: string[];
}

export interface RentEstimateRequest {
  address: string;
  city: string;
  state: string;
  zip_code: string;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
}

export interface RentEstimateResponse {
  estimate: number;
  low: number;
  high: number;
  source: string;
  comp_count: number;
}

export interface MacroDataResponse {
  mortgage_30yr?: number;
  mortgage_15yr?: number;
  unemployment?: number;
  fed_funds_rate?: number;
  treasury_10yr?: number;
  updated: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  }

  // Markets
  async getMarkets(params?: {
    sort_by?: string;
    limit?: number;
    landlord_friendly?: boolean;
  }): Promise<{ markets: Market[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.landlord_friendly !== undefined) {
      searchParams.set("landlord_friendly", params.landlord_friendly.toString());
    }

    return this.fetch(`/api/markets?${searchParams}`);
  }

  async getMarket(marketId: string): Promise<MarketDetail> {
    return this.fetch(`/api/markets/${marketId}`);
  }

  async compareMarkets(marketA: string, marketB: string): Promise<any> {
    return this.fetch(`/api/markets/${marketA}/compare/${marketB}`);
  }

  // Deals
  async searchDeals(params: {
    markets?: string;
    strategy?: string;
    min_price?: number;
    max_price?: number;
    min_beds?: number;
    max_beds?: number;
    min_cash_flow?: number;
    down_payment?: number;
    interest_rate?: number;
    limit?: number;
  }): Promise<{ deals: Deal[]; total: number; filters_applied: any }> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.set(key, value.toString());
      }
    });

    return this.fetch(`/api/deals/search?${searchParams}`);
  }

  async getDeal(dealId: string): Promise<any> {
    return this.fetch(`/api/deals/${dealId}`);
  }

  async analyzeMarket(
    city: string,
    state: string,
    params?: { max_price?: number; min_beds?: number; limit?: number }
  ): Promise<{ deals: Deal[]; total: number }> {
    const searchParams = new URLSearchParams();
    searchParams.set("city", city);
    searchParams.set("state", state);
    if (params?.max_price) searchParams.set("max_price", params.max_price.toString());
    if (params?.min_beds) searchParams.set("min_beds", params.min_beds.toString());
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    return this.fetch(`/api/deals/analyze?${searchParams}`, { method: "POST" });
  }

  // Analysis
  async calculateFinancials(params: {
    purchase_price: number;
    monthly_rent: number;
    down_payment_pct?: number;
    interest_rate?: number;
    property_tax_rate?: number;
    insurance_rate?: number;
    vacancy_rate?: number;
    maintenance_rate?: number;
    property_management_rate?: number;
    hoa_monthly?: number;
  }): Promise<AnalysisResult> {
    return this.fetch("/api/analysis/calculate", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.fetch("/api/health");
  }

  // Import
  async importFromUrl(params: ImportUrlRequest): Promise<ImportUrlResponse> {
    return this.fetch("/api/import/url", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getRentEstimate(params: RentEstimateRequest): Promise<RentEstimateResponse> {
    return this.fetch("/api/import/rent-estimate", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getMacroData(): Promise<MacroDataResponse> {
    return this.fetch("/api/import/macro");
  }

  async getMarketData(city: string, state: string): Promise<any> {
    return this.fetch(`/api/import/market-data/${encodeURIComponent(city)}/${encodeURIComponent(state)}`);
  }
}

export const api = new ApiClient();
