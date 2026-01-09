/**
 * API client for Real Estate Deal Platform
 */

// Use NEXT_PUBLIC_API_URL for deployed environments, empty for local dev (uses Next.js rewrites)
// Fallback to devpush API deployment URL if env var not set
const API_URL = process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' && window.location.hostname.includes('devpush-vm.orb.local')
    ? "https://deals-api-cameron-ehrlich-id-2a89557.apps.devpush-vm.orb.local"
    : "");

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
  labor_force?: number;
  major_employers: string[];
  median_household_income?: number;
  price_change_5yr?: number;
  rent_change_1yr?: number;
  months_of_inventory?: number;
  days_on_market_avg?: number;
  sale_to_list_ratio?: number;
  pct_sold_above_list?: number;
  price_trend: string;
  rent_trend: string;
  landlord_friendly: boolean;
  landlord_friendly_score?: number;
  property_tax_rate?: number;
  has_state_income_tax?: boolean;
  insurance_risk?: string;
  insurance_risk_factors?: string[];
  // Score components
  affordability_score: number;
  stability_score: number;
  liquidity_score: number;
  operating_cost_score?: number;
  regulatory_score?: number;
  // Data quality
  data_completeness?: number;
  data_sources?: string[];
  enrichment_pending?: boolean;
}

export interface Property {
  id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  latitude?: number;
  longitude?: number;
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

export interface PropertyDetail extends Property {
  full_address?: string;
  year_built?: number;
  lot_size_sqft?: number;
  stories?: number;
  units?: number;
  status?: string;
  source?: string;
  source_url?: string;
  annual_taxes?: number;
  hoa_fee?: number;
  original_price?: number;
  price_reduction_pct?: number;
  gross_rent_multiplier?: number;
  features?: string[];
}

export interface FinancialsDetail extends Financials {
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
  interest_rate: number;
  down_payment_pct: number;
}

export interface DealDetail {
  id: string;
  property: PropertyDetail;
  score?: DealScore;
  financials?: FinancialsDetail;
  sensitivity?: SensitivityResult;
  market?: MarketDetail;
  pipeline_status: string;
  strategy?: string;
  verdict?: string;
  recommendations: string[];
  pros: string[];
  cons: string[];
  red_flags: string[];
  notes: string[];
  first_seen: string;
  last_analyzed?: string;
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
  saved_id?: string;
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
  mortgage_5yr_arm?: number;
  unemployment?: number;
  fed_funds_rate?: number;
  treasury_10yr?: number;
  updated: string;
}

// Real Estate Provider API Types
export interface ApiUsage {
  provider: string;
  requests_used: number;
  requests_limit: number;
  requests_remaining: number;
  percent_used: number;
  warning: "approaching_limit" | "limit_reached" | null;
  period: string;
}

export interface PropertyListing {
  property_id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  sqft?: number;
  property_type: string;
  days_on_market?: number;
  photos: string[];
  source: string;
  source_url?: string;
  year_built?: number;
  price_per_sqft?: number;
  latitude?: number;
  longitude?: number;
  description?: string;  // Listing description from agent/seller
}

export interface PropertySearchResponse {
  properties: PropertyListing[];
  total: number;
  api_usage: ApiUsage;
}

export interface PropertyDetailResponse extends PropertyListing {
  lot_sqft?: number;
  stories?: number;
  description?: string;
  features: string[];
  price_history: Array<{ date: string; event: string; price: number }>;
  tax_history: Array<{ year: number; tax: number; assessment?: number }>;
  hoa_fee?: number;
  annual_tax?: number;
  api_usage: ApiUsage;
}

export interface LiveRentEstimate {
  estimate: number;
  low: number;
  high: number;
  comp_count: number;
  source: string;
}

// Request for pre-parsed property data (from Electron local scraping)
export interface ImportParsedRequest {
  address: string;
  city: string;
  state: string;
  zip_code: string;
  list_price: number;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number | null;
  property_type?: string;
  source: string;
  source_url?: string;
  down_payment_pct?: number;
  interest_rate?: number;
  save?: boolean;
}

// Response with saved_id
export interface ImportParsedResponse extends ImportUrlResponse {
  saved_id?: string;
}

// Saved property from database (Enriched tier)
export interface SavedProperty {
  id: string;
  address: string;
  city: string;
  state: string;
  zip_code?: string;
  latitude?: number;
  longitude?: number;

  // Property details
  list_price?: number;
  estimated_rent?: number;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  property_type?: string;
  year_built?: number;
  days_on_market?: number;
  description?: string;  // Listing description
  photos?: string[];

  // Source
  source?: string;
  source_url?: string;

  // All score dimensions
  overall_score?: number;
  financial_score?: number;
  market_score?: number;
  risk_score?: number;
  liquidity_score?: number;

  // Financial metrics
  cash_flow?: number;
  cash_on_cash?: number;
  cap_rate?: number;

  // Location data (cached from external APIs)
  location_data?: {
    walk_score?: number;
    walk_description?: string;
    transit_score?: number;
    transit_description?: string;
    bike_score?: number;
    bike_description?: string;
    noise?: {
      noise_score?: number;
      description?: string;
      categories?: Record<string, number>;
    };
    schools?: Array<{
      name: string;
      rating?: number;
      distance_miles?: number;
      grades?: string;
      type?: string;
    }>;
    flood_zone?: {
      zone?: string;
      risk_level?: string;
      description?: string;
      requires_insurance?: boolean;
      annual_chance?: string;
    };
  };

  // Custom scenarios (What Should I Offer)
  custom_scenarios?: Array<{
    name: string;
    offer_price: number;
    down_payment_pct: number;
    interest_rate: number;
    loan_term_years: number;
    monthly_cash_flow: number;
    cash_on_cash: number;
    cap_rate: number;
    total_cash_needed: number;
    created_at: string;
  }>;

  // Full analysis data (JSON blob from job)
  analysis_data?: Record<string, unknown>;

  // Deal pipeline data
  deal_data?: {
    stage?: string;
    stage_updated_at?: string;
    stage_history?: Array<{
      stage: string;
      entered_at: string;
      notes?: string;
    }>;
    due_diligence?: Record<string, {
      completed: boolean;
      notes?: string;
      completed_date?: string;
    }>;
  };

  // Pipeline
  pipeline_status: string;
  is_favorite: boolean;
  notes?: string;
  tags?: string[];

  // Timestamps
  last_analyzed?: string;
  location_data_fetched?: string;
  created_at: string;
  updated_at: string;
}

// Database stats
export interface DatabaseStats {
  total_saved_properties: number;
  favorite_properties: number;
  total_markets: number;
  favorite_markets: number;
  properties_by_status: Record<string, number>;
  cache: {
    search_entries: number;
    income_entries: number;
    total_api_calls: number;
  };
}

// Saved market from database
export interface SavedMarket {
  id: string;
  name: string;
  state: string;
  metro?: string;
  region?: string;
  is_favorite: boolean;
  is_supported: boolean;
  api_support?: Record<string, boolean>;
  // Scores
  overall_score: number;
  cash_flow_score: number;
  growth_score: number;
  affordability_score?: number;
  stability_score?: number;
  liquidity_score?: number;
  operating_cost_score?: number;
  regulatory_score?: number;
  // Market data fields
  median_home_price?: number;
  median_rent?: number;
  rent_to_price_ratio?: number;
  price_change_1yr?: number;
  job_growth_1yr?: number;
  unemployment_rate?: number;
  days_on_market?: number;
  months_of_inventory?: number;
  population?: number;
  landlord_friendly_score?: number;
  property_tax_rate?: number;
  insurance_risk?: string;
  // Data quality
  data_completeness?: number;
  data_sources?: string[];
}

// Metro suggestion for autocomplete
export interface MetroSuggestion {
  name: string;
  state: string;
  metro: string;
  median_price?: number;
  median_rent?: number;
  has_full_support?: boolean;
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

  async getDeal(dealId: string): Promise<DealDetail> {
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

  // Import pre-parsed property (from local Electron scraping)
  async importParsed(params: ImportParsedRequest): Promise<ImportParsedResponse> {
    return this.fetch("/api/import/parsed", {
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

  // Live Property Search (Real Estate Provider API)
  async searchLiveProperties(params: {
    location: string;  // "City, ST" format e.g. "Miami, FL"
    max_price?: number;
    min_price?: number;
    min_beds?: number;
    min_baths?: number;
    property_type?: string;
    limit?: number;
  }): Promise<PropertySearchResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set("location", params.location);
    if (params.max_price) searchParams.set("max_price", params.max_price.toString());
    if (params.min_price) searchParams.set("min_price", params.min_price.toString());
    if (params.min_beds) searchParams.set("min_beds", params.min_beds.toString());
    if (params.min_baths) searchParams.set("min_baths", params.min_baths.toString());
    if (params.property_type) searchParams.set("property_type", params.property_type);
    if (params.limit) searchParams.set("limit", params.limit.toString());

    return this.fetch(`/api/properties/search?${searchParams}`);
  }

  async getPropertyDetail(propertyId: string): Promise<PropertyDetailResponse> {
    return this.fetch(`/api/properties/detail/${propertyId}`);
  }

  async getLiveRentEstimate(params: {
    city: string;
    state: string;
    bedrooms: number;
  }): Promise<LiveRentEstimate> {
    const searchParams = new URLSearchParams();
    searchParams.set("city", params.city);
    searchParams.set("state", params.state);
    searchParams.set("bedrooms", params.bedrooms.toString());

    return this.fetch(`/api/properties/rent-comps?${searchParams}`);
  }

  async getApiUsage(): Promise<ApiUsage> {
    return this.fetch("/api/properties/usage");
  }

  // Income Data
  async getIncomeData(zipCode: string): Promise<{
    zip_code: string;
    median_income: number;
    income_tier: string;
    monthly_income: number;
    affordable_rent: number;
  }> {
    return this.fetch(`/api/import/income/${zipCode}`);
  }

  async getIncomeAffordability(zipCode: string, monthlyRent: number): Promise<{
    zip_code: string;
    median_income: number;
    income_tier: string;
    monthly_income: number;
    monthly_rent: number;
    rent_to_income_pct: number;
    affordable_rent: number;
    is_affordable: boolean;
    affordability_rating: string;
  }> {
    return this.fetch(`/api/import/income/${zipCode}/affordability?monthly_rent=${monthlyRent}`);
  }

  // Saved Properties
  async getSavedProperties(params?: {
    status?: string;
    favorites_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<SavedProperty[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.favorites_only) searchParams.set("favorites_only", "true");
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());

    return this.fetch(`/api/saved/properties?${searchParams}`);
  }

  async getSavedProperty(propertyId: string): Promise<SavedProperty> {
    return this.fetch(`/api/saved/properties/${propertyId}`);
  }

  async getSavedPropertyAnalysis(propertyId: string): Promise<any> {
    return this.fetch(`/api/saved/properties/${propertyId}/analysis`);
  }

  async updateSavedProperty(
    propertyId: string,
    updates: {
      pipeline_status?: string;
      is_favorite?: boolean;
      note?: string;
    }
  ): Promise<SavedProperty> {
    return this.fetch(`/api/saved/properties/${propertyId}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });
  }

  async togglePropertyFavorite(propertyId: string): Promise<SavedProperty> {
    return this.fetch(`/api/saved/properties/${propertyId}/favorite`, {
      method: "POST",
    });
  }

  async deleteSavedProperty(propertyId: string): Promise<{ success: boolean }> {
    return this.fetch(`/api/saved/properties/${propertyId}`, {
      method: "DELETE",
    });
  }

  async saveProperty(params: {
    address: string;
    city: string;
    state: string;
    zip_code?: string;
    latitude?: number;
    longitude?: number;
    list_price: number;
    estimated_rent?: number;
    bedrooms?: number;
    bathrooms?: number;
    sqft?: number;
    property_type?: string;
    year_built?: number;
    days_on_market?: number;
    photos?: string[];
    source?: string;
    source_url?: string;
    description?: string;
    // All score dimensions
    overall_score?: number;
    financial_score?: number;
    market_score?: number;
    risk_score?: number;
    liquidity_score?: number;
    // Financial metrics
    cash_flow?: number;
    cash_on_cash?: number;
    cap_rate?: number;
    // Full analysis data (includes pros/cons)
    analysis_data?: Record<string, unknown>;
    // Location data (Walk Score, Flood Zone, Noise, Schools)
    location_data?: {
      walk_score?: number;
      walk_description?: string;
      transit_score?: number;
      transit_description?: string;
      bike_score?: number;
      bike_description?: string;
      noise?: Record<string, unknown>;
      schools?: Array<Record<string, unknown>>;
      flood_zone?: Record<string, unknown>;
    };
  }): Promise<SavedProperty> {
    return this.fetch("/api/saved/properties", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getDatabaseStats(): Promise<DatabaseStats> {
    return this.fetch("/api/saved/stats");
  }

  // Property enrichment - Re-analyze and refresh location data
  async refreshPropertyLocationData(propertyId: string): Promise<SavedProperty> {
    return this.fetch(`/api/saved/properties/${propertyId}/refresh-location`, {
      method: "POST",
    });
  }

  async reanalyzeProperty(propertyId: string): Promise<SavedProperty> {
    return this.fetch(`/api/saved/properties/${propertyId}/reanalyze`, {
      method: "POST",
    });
  }

  async reenrichProperty(propertyId: string): Promise<{ job_id: string; property_id: string; message: string }> {
    return this.fetch(`/api/saved/properties/${propertyId}/reenrich`, {
      method: "POST",
    });
  }

  async addPropertyScenario(
    propertyId: string,
    scenario: {
      name?: string;
      offer_price: number;
      down_payment_pct?: number;
      interest_rate?: number;
      loan_term_years?: number;
    }
  ): Promise<SavedProperty> {
    return this.fetch(`/api/saved/properties/${propertyId}/scenarios`, {
      method: "POST",
      body: JSON.stringify(scenario),
    });
  }

  // Saved Markets
  async getSavedMarkets(params?: {
    favorites_only?: boolean;
    supported_only?: boolean;
  }): Promise<SavedMarket[]> {
    const searchParams = new URLSearchParams();
    if (params?.favorites_only) searchParams.set("favorites_only", "true");
    if (params?.supported_only !== undefined) searchParams.set("supported_only", params.supported_only.toString());

    return this.fetch(`/api/saved/markets?${searchParams}`);
  }

  async getFavoriteMarkets(): Promise<SavedMarket[]> {
    return this.fetch("/api/saved/markets/favorites");
  }

  async addMarket(params: {
    name: string;
    state: string;
    metro?: string;
    is_favorite?: boolean;
  }): Promise<SavedMarket> {
    return this.fetch("/api/saved/markets", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async toggleMarketFavorite(marketId: string): Promise<SavedMarket> {
    return this.fetch(`/api/saved/markets/${marketId}/favorite`, {
      method: "POST",
    });
  }

  async deleteMarket(marketId: string): Promise<{ success: boolean; message: string }> {
    return this.fetch(`/api/saved/markets/${marketId}`, {
      method: "DELETE",
    });
  }

  async refreshMarketData(marketId: string): Promise<SavedMarket> {
    return this.fetch(`/api/saved/markets/${marketId}/refresh`, {
      method: "POST",
    });
  }

  async searchMetros(query: string, limit: number = 10): Promise<MetroSuggestion[]> {
    return this.fetch(`/api/saved/markets/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  // Walk Score
  async getWalkScore(params: {
    address: string;
    latitude: number;
    longitude: number;
  }): Promise<WalkScoreResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set("address", params.address);
    searchParams.set("latitude", params.latitude.toString());
    searchParams.set("longitude", params.longitude.toString());

    return this.fetch(`/api/import/walkscore?${searchParams}`);
  }

  // Location Insights (noise score + schools)
  async getLocationInsights(params: {
    latitude: number;
    longitude: number;
    zip_code?: string;
  }): Promise<LocationInsightsResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set("latitude", params.latitude.toString());
    searchParams.set("longitude", params.longitude.toString());
    if (params.zip_code) {
      searchParams.set("zip_code", params.zip_code);
    }

    return this.fetch(`/api/import/location-insights?${searchParams}`);
  }

  // FEMA Flood Zone
  async getFloodZone(params: {
    latitude: number;
    longitude: number;
  }): Promise<FloodZoneResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set("latitude", params.latitude.toString());
    searchParams.set("longitude", params.longitude.toString());

    return this.fetch(`/api/import/flood-zone?${searchParams}`);
  }

  async getAllLocationData(params: {
    address: string;
    latitude: number;
    longitude: number;
    zip_code?: string;
  }): Promise<AllLocationDataResponse> {
    const searchParams = new URLSearchParams();
    searchParams.set("address", params.address);
    searchParams.set("latitude", params.latitude.toString());
    searchParams.set("longitude", params.longitude.toString());
    if (params.zip_code) {
      searchParams.set("zip_code", params.zip_code);
    }

    return this.fetch(`/api/import/all-location-data?${searchParams}`);
  }

  // Background Jobs
  async createJob(params: {
    job_type: string;
    payload?: Record<string, unknown>;
    priority?: number;
  }): Promise<Job> {
    return this.fetch("/api/jobs", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async enqueueMarketJobs(params?: {
    market_ids?: string[];
    favorites_only?: boolean;
  }): Promise<{ jobs_created: number; job_ids: string[] }> {
    return this.fetch("/api/jobs/enqueue-markets", {
      method: "POST",
      body: JSON.stringify(params || {}),
    });
  }

  async getJobs(params?: {
    status?: string;
    job_type?: string;
    limit?: number;
  }): Promise<Job[]> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.job_type) searchParams.set("job_type", params.job_type);
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    return this.fetch(`/api/jobs?${searchParams}`);
  }

  async getJobStats(): Promise<JobStats> {
    return this.fetch("/api/jobs/stats");
  }

  async getJob(jobId: string): Promise<Job> {
    return this.fetch(`/api/jobs/${jobId}`);
  }

  async cancelJob(jobId: string): Promise<Job> {
    return this.fetch(`/api/jobs/${jobId}/cancel`, {
      method: "POST",
    });
  }

  async cancelJobsByType(jobType: string): Promise<{ cancelled: number }> {
    return this.fetch(`/api/jobs/cancel-by-type/${jobType}`, {
      method: "POST",
    });
  }

  /**
   * Create a property and enqueue enrichment job.
   * Returns immediately with property ID and job ID for polling.
   */
  async enqueuePropertyJob(params: EnqueuePropertyRequest): Promise<EnqueuePropertyResponse> {
    return this.fetch("/api/jobs/enqueue-property", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // ==================== Financing Methods ====================

  async getLoanProducts(params?: {
    defaults_only?: boolean;
    loan_type?: string;
  }): Promise<LoanProduct[]> {
    const searchParams = new URLSearchParams();
    if (params?.defaults_only) searchParams.set("defaults_only", "true");
    if (params?.loan_type) searchParams.set("loan_type", params.loan_type);
    return this.fetch(`/api/financing/loan-products?${searchParams}`);
  }

  async getLoanProduct(productId: string): Promise<LoanProduct> {
    return this.fetch(`/api/financing/loan-products/${productId}`);
  }

  async createLoanProduct(
    data: Omit<LoanProduct, "id" | "created_at" | "updated_at">
  ): Promise<LoanProduct> {
    return this.fetch("/api/financing/loan-products", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateLoanProduct(
    productId: string,
    data: Partial<LoanProduct>
  ): Promise<LoanProduct> {
    return this.fetch(`/api/financing/loan-products/${productId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteLoanProduct(
    productId: string
  ): Promise<{ success: boolean; message: string }> {
    return this.fetch(`/api/financing/loan-products/${productId}`, {
      method: "DELETE",
    });
  }

  async calculateFinancingScenario(params: {
    purchase_price: number;
    monthly_rent: number;
    down_payment_pct?: number;
    interest_rate?: number;
    loan_term_years?: number;
    closing_cost_pct?: number;
    points?: number;
    property_tax_rate?: number;
    insurance_rate?: number;
    vacancy_rate?: number;
    maintenance_rate?: number;
    capex_rate?: number;
    property_management_rate?: number;
    hoa_monthly?: number;
  }): Promise<FinancingScenario> {
    return this.fetch("/api/financing/calculate", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async compareFinancingScenarios(params: {
    purchase_price: number;
    monthly_rent: number;
    loan_product_ids?: string[];
    property_tax_rate?: number;
    insurance_rate?: number;
    vacancy_rate?: number;
    maintenance_rate?: number;
    capex_rate?: number;
    property_management_rate?: number;
    hoa_monthly?: number;
  }): Promise<FinancingScenario[]> {
    return this.fetch("/api/financing/compare", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async calculateBreakEven(params: {
    purchase_price: number;
    monthly_rent: number;
    down_payment_pct?: number;
    interest_rate?: number;
    loan_term_years?: number;
    closing_cost_pct?: number;
    target_cash_on_cash?: number;
    target_cash_flow?: number;
  }): Promise<BreakEvenAnalysis> {
    return this.fetch("/api/financing/break-even", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async checkDSCR(params: {
    purchase_price: number;
    monthly_rent: number;
    down_payment_pct?: number;
    interest_rate?: number;
    loan_term_years?: number;
    min_dscr_required?: number;
  }): Promise<DSCRCheck> {
    const searchParams = new URLSearchParams();
    searchParams.set("purchase_price", params.purchase_price.toString());
    searchParams.set("monthly_rent", params.monthly_rent.toString());
    if (params.down_payment_pct)
      searchParams.set("down_payment_pct", params.down_payment_pct.toString());
    if (params.interest_rate)
      searchParams.set("interest_rate", params.interest_rate.toString());
    if (params.loan_term_years)
      searchParams.set("loan_term_years", params.loan_term_years.toString());
    if (params.min_dscr_required)
      searchParams.set("min_dscr_required", params.min_dscr_required.toString());
    return this.fetch(`/api/financing/dscr-check?${searchParams}`);
  }

  // ==================== Contact Methods ====================

  async getContacts(params?: {
    contact_type?: string;
    property_id?: string;
    search?: string;
    has_followup?: boolean;
  }): Promise<Contact[]> {
    const searchParams = new URLSearchParams();
    if (params?.contact_type) searchParams.set("contact_type", params.contact_type);
    if (params?.property_id) searchParams.set("property_id", params.property_id);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.has_followup !== undefined)
      searchParams.set("has_followup", params.has_followup.toString());
    return this.fetch(`/api/contacts?${searchParams}`);
  }

  async getContact(contactId: string): Promise<Contact> {
    return this.fetch(`/api/contacts/${contactId}`);
  }

  async createContact(data: CreateContactRequest): Promise<Contact> {
    return this.fetch("/api/contacts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateContact(contactId: string, data: Partial<Contact>): Promise<Contact> {
    return this.fetch(`/api/contacts/${contactId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteContact(contactId: string): Promise<{ success: boolean; message: string }> {
    return this.fetch(`/api/contacts/${contactId}`, {
      method: "DELETE",
    });
  }

  async linkPropertyToContact(
    contactId: string,
    propertyId: string
  ): Promise<Contact> {
    return this.fetch(
      `/api/contacts/${contactId}/link-property?property_id=${propertyId}`,
      { method: "POST" }
    );
  }

  async getCommunications(params?: {
    contact_id?: string;
    property_id?: string;
    comm_type?: string;
    limit?: number;
  }): Promise<Communication[]> {
    const searchParams = new URLSearchParams();
    if (params?.contact_id) searchParams.set("contact_id", params.contact_id);
    if (params?.property_id) searchParams.set("property_id", params.property_id);
    if (params?.comm_type) searchParams.set("comm_type", params.comm_type);
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    return this.fetch(`/api/contacts/communications?${searchParams}`);
  }

  async createCommunication(data: CreateCommunicationRequest): Promise<Communication> {
    return this.fetch("/api/contacts/communications", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getEmailTemplates(): Promise<EmailTemplate[]> {
    return this.fetch("/api/contacts/templates");
  }

  async generateEmail(
    templateId: string,
    variables: Record<string, string>
  ): Promise<GeneratedEmail> {
    return this.fetch(`/api/contacts/templates/${templateId}/generate`, {
      method: "POST",
      body: JSON.stringify({ template_id: templateId, variables }),
    });
  }

  async getPropertyTimeline(propertyId: string): Promise<PropertyTimeline> {
    return this.fetch(`/api/contacts/properties/${propertyId}/timeline`);
  }

  // ==================== Pipeline Methods ====================

  async getOffers(params?: {
    property_id?: string;
    status?: string;
  }): Promise<Offer[]> {
    const searchParams = new URLSearchParams();
    if (params?.property_id) searchParams.set("property_id", params.property_id);
    if (params?.status) searchParams.set("status", params.status);
    return this.fetch(`/api/pipeline/offers?${searchParams}`);
  }

  async getOffer(offerId: string): Promise<Offer> {
    return this.fetch(`/api/pipeline/offers/${offerId}`);
  }

  async createOffer(data: CreateOfferRequest): Promise<Offer> {
    return this.fetch("/api/pipeline/offers", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateOffer(offerId: string, data: UpdateOfferRequest): Promise<Offer> {
    return this.fetch(`/api/pipeline/offers/${offerId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async submitOffer(offerId: string): Promise<Offer> {
    return this.fetch(`/api/pipeline/offers/${offerId}/submit`, {
      method: "POST",
    });
  }

  async logCounterOffer(
    offerId: string,
    counterPrice: number,
    notes?: string
  ): Promise<Offer> {
    return this.fetch(`/api/pipeline/offers/${offerId}/counter`, {
      method: "POST",
      body: JSON.stringify({ counter_price: counterPrice, notes }),
    });
  }

  async acceptOffer(offerId: string, finalPrice?: number): Promise<Offer> {
    const searchParams = new URLSearchParams();
    if (finalPrice) searchParams.set("final_price", finalPrice.toString());
    return this.fetch(`/api/pipeline/offers/${offerId}/accept?${searchParams}`, {
      method: "POST",
    });
  }

  async rejectOffer(offerId: string, notes?: string): Promise<Offer> {
    const searchParams = new URLSearchParams();
    if (notes) searchParams.set("notes", notes);
    return this.fetch(`/api/pipeline/offers/${offerId}/reject?${searchParams}`, {
      method: "POST",
    });
  }

  async withdrawOffer(offerId: string, notes?: string): Promise<Offer> {
    const searchParams = new URLSearchParams();
    if (notes) searchParams.set("notes", notes);
    return this.fetch(`/api/pipeline/offers/${offerId}/withdraw?${searchParams}`, {
      method: "POST",
    });
  }

  async deleteOffer(offerId: string): Promise<{ success: boolean }> {
    return this.fetch(`/api/pipeline/offers/${offerId}`, {
      method: "DELETE",
    });
  }

  async getDealStages(): Promise<DealStage[]> {
    return this.fetch("/api/pipeline/stages");
  }

  async getDueDiligenceItems(): Promise<DueDiligenceItem[]> {
    return this.fetch("/api/pipeline/due-diligence-items");
  }

  async updatePropertyStage(
    propertyId: string,
    stage: string,
    notes?: string
  ): Promise<{ success: boolean; property_id: string; stage: string }> {
    return this.fetch(`/api/pipeline/properties/${propertyId}/stage`, {
      method: "PATCH",
      body: JSON.stringify({ stage, notes }),
    });
  }

  async getPropertyDueDiligence(propertyId: string): Promise<DueDiligenceChecklist> {
    return this.fetch(`/api/pipeline/properties/${propertyId}/due-diligence`);
  }

  async updatePropertyDueDiligence(
    propertyId: string,
    itemId: string,
    completed: boolean,
    notes?: string
  ): Promise<{ success: boolean; item_id: string; completed: boolean }> {
    return this.fetch(`/api/pipeline/properties/${propertyId}/due-diligence`, {
      method: "PATCH",
      body: JSON.stringify({ item_id: itemId, completed, notes }),
    });
  }

  async getPipelineOverview(): Promise<PipelineOverview> {
    return this.fetch("/api/pipeline/overview");
  }

  // ==================== Financing Desk Methods ====================

  async getBorrowerProfile(): Promise<any> {
    return this.fetch("/api/financing-desk/borrower-profile");
  }

  async saveBorrowerProfile(data: Record<string, any>): Promise<any> {
    return this.fetch("/api/financing-desk/borrower-profile", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getLenders(params?: { lender_type?: string; is_active?: boolean }): Promise<any[]> {
    const searchParams = new URLSearchParams();
    if (params?.lender_type) searchParams.set("lender_type", params.lender_type);
    if (params?.is_active !== undefined) searchParams.set("is_active", String(params.is_active));
    return this.fetch(`/api/financing-desk/lenders?${searchParams}`);
  }

  async getLender(lenderId: string): Promise<any> {
    return this.fetch(`/api/financing-desk/lenders/${lenderId}`);
  }

  async createLender(data: {
    name: string;
    lender_type: string;
    contact_name?: string;
    contact_email?: string;
    contact_phone?: string;
    website?: string;
    loan_types?: string[];
    min_credit_score?: number;
    min_down_payment?: number;
    max_ltv?: number;
    rate_range_low?: number;
    rate_range_high?: number;
    notes?: string;
    is_active?: boolean;
  }): Promise<any> {
    return this.fetch("/api/financing-desk/lenders", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateLender(lenderId: string, data: Record<string, any>): Promise<any> {
    return this.fetch(`/api/financing-desk/lenders/${lenderId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteLender(lenderId: string): Promise<{ success: boolean }> {
    return this.fetch(`/api/financing-desk/lenders/${lenderId}`, {
      method: "DELETE",
    });
  }

  async getLenderQuotes(params?: {
    lender_id?: string;
    property_id?: string;
    status?: string;
  }): Promise<any[]> {
    const searchParams = new URLSearchParams();
    if (params?.lender_id) searchParams.set("lender_id", params.lender_id);
    if (params?.property_id) searchParams.set("property_id", params.property_id);
    if (params?.status) searchParams.set("status", params.status);
    return this.fetch(`/api/financing-desk/quotes?${searchParams}`);
  }

  async createLenderQuote(data: {
    lender_id: string;
    property_id?: string;
    loan_amount: number;
    interest_rate: number;
    loan_term_years: number;
    points?: number;
    origination_fee?: number;
    closing_costs?: number;
    monthly_payment?: number;
    apr?: number;
    rate_lock_days?: number;
    notes?: string;
  }): Promise<any> {
    return this.fetch("/api/financing-desk/quotes", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateLenderQuote(quoteId: string, data: Record<string, any>): Promise<any> {
    return this.fetch(`/api/financing-desk/quotes/${quoteId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteLenderQuote(quoteId: string): Promise<{ success: boolean }> {
    return this.fetch(`/api/financing-desk/quotes/${quoteId}`, {
      method: "DELETE",
    });
  }

  async compareQuotes(propertyId: string): Promise<any> {
    return this.fetch(`/api/financing-desk/quotes/compare/${propertyId}`);
  }

  // ==================== Comps Methods (Phase 6) ====================

  async getCompsForProperty(propertyId: string, maxResults?: number): Promise<CompsAnalysis> {
    const params = new URLSearchParams();
    if (maxResults) params.set("max_results", maxResults.toString());
    return this.fetch(`/api/comps/property/${propertyId}?${params}`);
  }

  async getCompsByCityState(params: {
    city: string;
    state_code: string;
    subject_price: number;
    subject_sqft?: number;
    bedrooms?: number;
    min_sqft?: number;
    max_sqft?: number;
    max_results?: number;
  }): Promise<CompsAnalysis> {
    const searchParams = new URLSearchParams();
    searchParams.set("city", params.city);
    searchParams.set("state_code", params.state_code);
    searchParams.set("subject_price", params.subject_price.toString());
    if (params.subject_sqft) searchParams.set("subject_sqft", params.subject_sqft.toString());
    if (params.bedrooms) searchParams.set("bedrooms", params.bedrooms.toString());
    if (params.min_sqft) searchParams.set("min_sqft", params.min_sqft.toString());
    if (params.max_sqft) searchParams.set("max_sqft", params.max_sqft.toString());
    if (params.max_results) searchParams.set("max_results", params.max_results.toString());
    return this.fetch(`/api/comps/sold?${searchParams}`);
  }

  // ==================== Neighborhood Score Methods (Phase 6.2) ====================

  async getNeighborhoodScoreForProperty(propertyId: string): Promise<NeighborhoodScore> {
    return this.fetch(`/api/neighborhood/score/${propertyId}`);
  }

  async getNeighborhoodScoreByLocation(
    latitude: number,
    longitude: number,
    zipCode?: string
  ): Promise<NeighborhoodScore> {
    const params = new URLSearchParams();
    params.set("latitude", latitude.toString());
    params.set("longitude", longitude.toString());
    if (zipCode) params.set("zip_code", zipCode);
    return this.fetch(`/api/neighborhood/score?${params}`);
  }

  // ==================== Risk Assessment Methods (Phase 6.3) ====================

  async getRiskAssessment(propertyId: string): Promise<RiskAssessment> {
    return this.fetch(`/api/risk/assessment/${propertyId}`);
  }

  // ==================== AI Due Diligence Methods ====================

  /**
   * Queue an AI due diligence research job for a property.
   * The AI will research property history, legal issues, environmental concerns,
   * market context, and gather professional contacts.
   */
  async startDueDiligence(propertyId: string): Promise<DueDiligenceJobResponse> {
    return this.fetch(`/api/jobs/enqueue-due-diligence?property_id=${propertyId}`, {
      method: "POST",
    });
  }

  /**
   * Get the due diligence report for a property.
   * Returns the full report if available, or status if still in progress.
   */
  async getDueDiligenceReport(propertyId: string): Promise<DueDiligenceReportResponse> {
    return this.fetch(`/api/jobs/due-diligence/${propertyId}`);
  }
}

// ==================== Comps Types (Phase 6) ====================

export interface ComparableSale {
  property_id: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  sold_price: number;
  list_price?: number;
  bedrooms: number;
  bathrooms: number;
  sqft?: number;
  sold_date?: string;
  days_on_market?: number;
  price_per_sqft?: number;
  distance_miles?: number;
}

export interface CompsAnalysis {
  subject_price: number;
  subject_sqft?: number;
  subject_price_per_sqft?: number;
  comp_count: number;
  median_sold_price?: number;
  median_price_per_sqft?: number;
  avg_sold_price?: number;
  avg_price_per_sqft?: number;
  min_sold_price?: number;
  max_sold_price?: number;
  price_vs_median?: number;
  price_vs_median_psf?: number;
  price_position: "above_market" | "below_market" | "at_market" | "unknown";
  comparables: ComparableSale[];
}

// ==================== Neighborhood Score Types (Phase 6.2) ====================

export interface LocationScore {
  score?: number;
  weight: number;
  description?: string;
  raw_value?: number;
}

export interface SchoolSummary {
  count: number;
  avg_rating?: number;
  top_rated?: string;
  public_count: number;
  private_count: number;
}

export interface NeighborhoodScore {
  overall_score?: number;
  grade: string;
  walkability: LocationScore;
  transit: LocationScore;
  bikeability: LocationScore;
  schools: LocationScore;
  safety: LocationScore;
  flood_risk: LocationScore;
  school_summary: SchoolSummary;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  data_sources_used: string[];
  data_completeness: number;
}

// ==================== Risk Assessment Types (Phase 6.3) ====================

export interface RiskFlag {
  category: "property" | "market" | "location" | "financial";
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  recommendation?: string;
}

export interface RiskAssessment {
  risk_level: "low" | "medium" | "high" | "critical" | "unknown";
  risk_score: number;
  property_flags: RiskFlag[];
  market_flags: RiskFlag[];
  location_flags: RiskFlag[];
  financial_flags: RiskFlag[];
  total_flags: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  deal_breakers: string[];
  investigate: string[];
  minor_concerns: string[];
  due_diligence_items: string[];
}

// Job types
export interface Job {
  id: string;
  job_type: string;
  payload: Record<string, unknown>;
  priority: number;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  message?: string;
  error?: string;
  result?: Record<string, unknown>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  attempts: number;
  max_attempts: number;
}

export interface JobStats {
  pending: number;
  running: number;
  completed: number;
  failed: number;
  total: number;
}

// Property enrichment job request/response
export interface EnqueuePropertyRequest {
  address: string;
  city: string;
  state: string;
  zip_code?: string;
  latitude?: number;
  longitude?: number;
  list_price: number;
  bedrooms?: number;
  bathrooms?: number;
  sqft?: number;
  property_type?: string;
  source?: string;
  source_url?: string;
  photos?: string[];
  description?: string;
  down_payment_pct?: number;
  interest_rate?: number;
}

export interface EnqueuePropertyResponse {
  property_id: string;
  job_id: string;
  status: string;
  message: string;
}

// Walk Score response
export interface WalkScoreResponse {
  address: string;
  latitude: number;
  longitude: number;
  walk_score?: number;
  walk_description?: string;
  transit_score?: number;
  transit_description?: string;
  bike_score?: number;
  bike_description?: string;
}

// Noise Score response
export interface NoiseScoreResponse {
  noise_score?: number;
  description?: string;
  categories: Record<string, number>;
  latitude: number;
  longitude: number;
}

// School Info
export interface SchoolInfo {
  name: string;
  rating?: number;
  distance_miles?: number;
  grades?: string;
  type?: string;
  student_count?: number;
}

// Location Insights response
export interface LocationInsightsResponse {
  noise?: NoiseScoreResponse;
  schools: SchoolInfo[];
}

// FEMA Flood Zone response
export interface FloodZoneResponse {
  latitude: number;
  longitude: number;
  flood_zone?: string;
  zone_subtype?: string;
  risk_level?: string;  // high, moderate, low, undetermined
  description?: string;
  requires_insurance: boolean;
  annual_chance?: string;
  base_flood_elevation?: number;
  firm_panel?: string;
  effective_date?: string;
}

// Combined location data from all sources
export interface AllLocationDataResponse {
  // Walk Score
  walk_score?: number;
  walk_description?: string;
  transit_score?: number;
  transit_description?: string;
  bike_score?: number;
  bike_description?: string;
  // Noise
  noise?: {
    noise_score?: number;
    description?: string;
    categories?: Record<string, number>;
  };
  // Schools
  schools: Array<{
    name: string;
    rating?: number;
    distance_miles?: number;
    grades?: string;
    type?: string;
    student_count?: number;
  }>;
  // Flood Zone
  flood_zone?: {
    zone?: string;
    zone_subtype?: string;
    risk_level?: string;
    description?: string;
    requires_insurance?: boolean;
    annual_chance?: string;
  };
  // Errors from individual API calls
  errors: string[];
}

// ==================== Financing Types ====================

export interface LoanProduct {
  id: string;
  name: string;
  description?: string;
  down_payment_pct: number;
  interest_rate: number;
  loan_term_years: number;
  points: number;
  closing_cost_pct: number;
  is_dscr: boolean;
  min_dscr_required?: number;
  loan_type?: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface FinancingScenario {
  // Loan product info (for reliable matching)
  product_id?: string;
  product_name?: string;
  loan_type?: string;
  is_dscr?: boolean;

  // Input summary
  purchase_price: number;
  monthly_rent: number;
  down_payment_pct: number;
  interest_rate: number;
  loan_term_years: number;

  // Cash needed
  down_payment: number;
  closing_costs: number;
  points_cost: number;
  total_cash_needed: number;

  // Loan details
  loan_amount: number;
  monthly_mortgage: number;

  // Operating expenses (monthly)
  monthly_taxes: number;
  monthly_insurance: number;
  monthly_vacancy: number;
  monthly_maintenance: number;
  monthly_capex: number;
  monthly_property_management: number;
  monthly_hoa: number;
  total_monthly_expenses: number;

  // Performance metrics
  monthly_cash_flow: number;
  annual_cash_flow: number;
  cash_on_cash_return: number;
  cap_rate: number;
  gross_rent_multiplier: number;
  rent_to_price_ratio: number;
  break_even_occupancy: number;

  // DSCR
  dscr: number;
  qualifies_for_dscr: boolean;
  dscr_status: 'qualifies' | 'borderline' | 'does_not_qualify';
}

export interface BreakEvenAnalysis {
  current_cash_flow: number;
  current_coc: number;
  break_even_rate?: number;
  rate_cushion?: number;
  break_even_vacancy?: number;
  vacancy_cushion?: number;
  break_even_rent?: number;
  rent_cushion_pct?: number;
  price_for_target_coc?: number;
  down_payment_for_target_coc?: number;
  rate_for_target_cash_flow?: number;
}

export interface DSCRCheck {
  dscr: number;
  min_required: number;
  qualifies: boolean;
  status: string;
  shortfall: number;
  monthly_cash_flow: number;
  suggestions: string[];
}

// ==================== Contact Types ====================

export interface Contact {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  contact_type?: string; // listing_agent, buyer_agent, seller, lender, other
  notes?: string;
  property_ids: string[];
  agent_id?: string;
  agent_photo_url?: string;
  agent_profile_data?: Record<string, unknown>;
  last_contacted?: string;
  next_followup?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateContactRequest {
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  contact_type?: string;
  notes?: string;
  property_ids?: string[];
  agent_id?: string;
  agent_photo_url?: string;
  agent_profile_data?: Record<string, unknown>;
}

export interface Communication {
  id: string;
  contact_id: string;
  property_id?: string;
  comm_type: string; // email, call, text, meeting, note
  direction?: string; // inbound, outbound, internal
  subject?: string;
  content?: string;
  template_used?: string;
  occurred_at: string;
  created_at: string;
}

export interface CreateCommunicationRequest {
  contact_id: string;
  property_id?: string;
  comm_type: string;
  direction?: string;
  subject?: string;
  content?: string;
  template_used?: string;
  occurred_at?: string;
}

export interface EmailTemplate {
  id: string;
  name: string;
  description: string;
  subject: string;
  body: string;
  variables: string[];
}

export interface GeneratedEmail {
  subject: string;
  body: string;
}

export interface PropertyTimeline {
  property_id: string;
  contacts: Contact[];
  communications: Communication[];
  total_contacts: number;
  total_communications: number;
}

// ==================== Pipeline Types ====================

export interface Offer {
  id: string;
  property_id: string;
  offer_price: number;
  down_payment_pct: number;
  financing_type?: string;
  earnest_money?: number;
  contingencies: string[];
  inspection_days?: number;
  financing_days?: number;
  closing_days?: number;
  status: 'draft' | 'submitted' | 'countered' | 'accepted' | 'rejected' | 'withdrawn' | 'expired';
  submitted_at?: string;
  expires_at?: string;
  response_deadline?: string;
  counter_history: Array<{
    price: number;
    date: string;
    notes?: string;
  }>;
  final_price?: number;
  outcome_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateOfferRequest {
  property_id: string;
  offer_price: number;
  down_payment_pct?: number;
  financing_type?: string;
  earnest_money?: number;
  contingencies?: string[];
  inspection_days?: number;
  financing_days?: number;
  closing_days?: number;
}

export interface UpdateOfferRequest {
  offer_price?: number;
  down_payment_pct?: number;
  financing_type?: string;
  earnest_money?: number;
  contingencies?: string[];
  inspection_days?: number;
  financing_days?: number;
  closing_days?: number;
  status?: string;
  expires_at?: string;
  response_deadline?: string;
  final_price?: number;
  outcome_notes?: string;
}

export interface DealStage {
  id: string;
  name: string;
  order: number;
}

export interface DueDiligenceItem {
  id: string;
  name: string;
  category: string;
  completed: boolean;
  notes?: string;
  completed_date?: string;
}

export interface DueDiligenceChecklist {
  property_id: string;
  items: DueDiligenceItem[];
  completed_count: number;
  total_count: number;
}

export interface PipelineProperty {
  id: string;
  address: string;
  city: string;
  state: string;
  list_price?: number;
  estimated_rent?: number;
  deal_stage?: string;
  deal_score?: number;
  days_in_stage?: number;
  has_active_offer: boolean;
  primary_photo?: string;
}

export interface PipelineOverview {
  stages: DealStage[];
  properties_by_stage: Record<string, PipelineProperty[]>;
  total_properties: number;
  active_offers: number;
  under_contract: number;
}

// ==================== AI Due Diligence Types ====================

export interface DueDiligenceJobResponse {
  property_id: string;
  job_id: string;
  status: string;
  message: string;
}

export interface DueDiligenceFlag {
  severity?: "critical" | "high" | "medium" | "low";
  title: string;
  description: string;
  source?: string;
}

export interface DueDiligenceFindings {
  ownership_history?: Array<{
    date?: string;
    owner?: string;
    sale_price?: string;
  }>;
  liens_found?: Array<{
    type?: string;
    amount?: string;
    status?: string;
  }>;
  environmental_concerns?: Array<{
    type?: string;
    description?: string;
    distance?: string;
  }>;
  listing_agent?: {
    name?: string;
    phone?: string;
    email?: string;
    company?: string;
  };
  neighborhood_trends?: string[];
  development_plans?: string[];
}

export interface DueDiligenceReportData {
  property_id: string;
  property_address: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at?: string;
  completed_at?: string;
  executive_summary?: string;
  red_flags?: DueDiligenceFlag[];
  yellow_flags?: DueDiligenceFlag[];
  green_flags?: DueDiligenceFlag[];
  recommended_actions?: string[];
  questions_for_seller?: string[];
  inspection_focus_areas?: string[];
  findings?: DueDiligenceFindings;
  sources_consulted?: string[];
  errors?: string[];
}

export interface DueDiligenceReportResponse {
  property_id: string;
  status: string;
  progress?: number;
  message?: string;
  job_id?: string;
  report?: DueDiligenceReportData;
}

export const api = new ApiClient();
