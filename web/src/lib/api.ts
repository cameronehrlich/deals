/**
 * API client for Real Estate Deal Platform
 */

// Use relative URL - Next.js rewrites will proxy to the actual API
const API_URL = "";

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

  async reenrichProperty(propertyId: string): Promise<SavedProperty> {
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

export const api = new ApiClient();
