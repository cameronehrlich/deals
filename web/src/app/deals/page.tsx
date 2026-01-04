"use client";

import { Suspense, useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import {
  Search,
  Building,
  Radio,
  ExternalLink,
  ArrowUpDown,
  ChevronDown,
  Play,
  CheckCircle,
  Loader2,
  AlertCircle,
  Bookmark,
  Check,
  Link2,
  X,
  Clock,
  BookmarkCheck,
} from "lucide-react";
import { ImageCarousel } from "@/components/ImageCarousel";
import { api, PropertyListing, ApiUsage, JobStats } from "@/lib/api";
import { LoadingPage, LoadingSpinner } from "@/components/LoadingSpinner";
import { cn, formatCurrency } from "@/lib/utils";

// Session storage keys for persisting state
const STORAGE_KEY = "deals_page_state";

interface PersistedState {
  properties: PropertyListing[];
  displayCount: number;
  scrollY: number;
  apiUsage: ApiUsage | null;
  selectedLocation: string;
  maxPrice: string;
  minBeds: string;
  sortBy: string;
  timestamp: number;
}

// Save state to sessionStorage
function saveState(state: Omit<PersistedState, "timestamp">) {
  try {
    const data: PersistedState = { ...state, timestamp: Date.now() };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    console.warn("Failed to save deals page state:", e);
  }
}

// Load state from sessionStorage (max 10 min old)
function loadState(): PersistedState | null {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    const data: PersistedState = JSON.parse(stored);
    // Expire after 10 minutes
    if (Date.now() - data.timestamp > 10 * 60 * 1000) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return data;
  } catch (e) {
    return null;
  }
}

// Convert market ID (salt_lake_city_ut) to location format (Salt Lake City, UT)
function marketIdToLocation(marketId: string): string {
  const parts = marketId.split("_");
  const state = parts.pop()?.toUpperCase() || "";
  const city = parts.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
  return `${city}, ${state}`;
}

// Fallback markets if API fails
const DEFAULT_MARKETS = [
  "Phoenix, AZ",
  "Tampa, FL",
  "Austin, TX",
  "Indianapolis, IN",
  "Cleveland, OH",
  "Memphis, TN",
  "Birmingham, AL",
  "Kansas City, MO",
];

// Sort options for investment analysis
type SortOption = {
  value: string;
  label: string;
  sortFn: (a: PropertyListing, b: PropertyListing) => number;
};

const SORT_OPTIONS: SortOption[] = [
  {
    value: "price_asc",
    label: "Price: Low to High",
    sortFn: (a, b) => a.price - b.price,
  },
  {
    value: "price_desc",
    label: "Price: High to Low",
    sortFn: (a, b) => b.price - a.price,
  },
  {
    value: "price_sqft_asc",
    label: "$/sqft: Low to High",
    sortFn: (a, b) => (a.price_per_sqft || 999999) - (b.price_per_sqft || 999999),
  },
  {
    value: "price_sqft_desc",
    label: "$/sqft: High to Low",
    sortFn: (a, b) => (b.price_per_sqft || 0) - (a.price_per_sqft || 0),
  },
  {
    value: "beds_desc",
    label: "Bedrooms: Most First",
    sortFn: (a, b) => b.bedrooms - a.bedrooms,
  },
  {
    value: "beds_asc",
    label: "Bedrooms: Fewest First",
    sortFn: (a, b) => a.bedrooms - b.bedrooms,
  },
  {
    value: "sqft_desc",
    label: "Size: Largest First",
    sortFn: (a, b) => (b.sqft || 0) - (a.sqft || 0),
  },
  {
    value: "sqft_asc",
    label: "Size: Smallest First",
    sortFn: (a, b) => (a.sqft || 999999) - (b.sqft || 999999),
  },
  {
    value: "year_desc",
    label: "Year: Newest First",
    sortFn: (a, b) => (b.year_built || 0) - (a.year_built || 0),
  },
  {
    value: "year_asc",
    label: "Year: Oldest First",
    sortFn: (a, b) => (a.year_built || 9999) - (b.year_built || 9999),
  },
];

// Constants for pagination
const INITIAL_LOAD = 10;
const LOAD_MORE_COUNT = 10;
const MAX_RESULTS = 42; // API free tier max

// Card state type
type CardState = "default" | "saving" | "processing" | "saved";

// Property card for live listings
function LivePropertyCard({
  property,
  onSaveAndAnalyze,
  onViewSaved,
  isSelected,
  onToggleSelect,
  cardState,
  savedPropertyId,
}: {
  property: PropertyListing;
  onSaveAndAnalyze: () => void;
  onViewSaved: () => void;
  isSelected: boolean;
  onToggleSelect: () => void;
  cardState: CardState;
  savedPropertyId?: string;
}) {
  const isSaved = cardState === "saved";
  const isSaving = cardState === "saving";
  const isProcessing = cardState === "processing";

  return (
    <div className={cn(
      "card hover:shadow-lg transition-all duration-300",
      isSelected && "ring-2 ring-primary-500",
      isSaving && "animate-pulse-ring ring-2 ring-primary-400"
    )}>
      {/* Photo Carousel */}
      <div className="relative h-48 -mx-4 -mt-4 mb-4 bg-gray-100 rounded-t-lg overflow-hidden">
        <ImageCarousel
          images={property.photos || []}
          alt={property.address}
        />
        {/* Selection checkbox */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleSelect();
          }}
          className={cn(
            "absolute top-2 left-2 w-6 h-6 rounded border-2 flex items-center justify-center z-10 transition-colors",
            isSelected
              ? "bg-primary-600 border-primary-600 text-white"
              : "bg-white/90 border-gray-300 hover:border-primary-400"
          )}
        >
          {isSelected && <Check className="h-4 w-4" />}
        </button>
        {/* Status indicator */}
        {(isSaved || isProcessing) && (
          <div className={cn(
            "absolute top-2 right-2 px-2 py-1 text-white text-xs font-medium rounded-full flex items-center gap-1 z-10 transition-all",
            isSaved ? "bg-green-600" : "bg-amber-500"
          )}>
            {isProcessing ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <BookmarkCheck className="h-3 w-3" />
                Saved
              </>
            )}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="space-y-3">
        {/* Price */}
        <div className="flex justify-between items-start">
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(property.price)}
            </p>
            {property.price_per_sqft && (
              <p className="text-sm text-gray-500">
                ${property.price_per_sqft.toFixed(0)}/sqft
              </p>
            )}
          </div>
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded capitalize">
            {property.property_type.replace(/_/g, " ")}
          </span>
        </div>

        {/* Address */}
        <div>
          <p className="font-medium text-gray-900">{property.address}</p>
          <p className="text-sm text-gray-500">
            {property.city}, {property.state} {property.zip_code}
          </p>
        </div>

        {/* Details */}
        <div className="flex gap-4 text-sm text-gray-600">
          <span>{property.bedrooms} bd</span>
          <span>{property.bathrooms} ba</span>
          {property.sqft && <span>{property.sqft.toLocaleString()} sqft</span>}
          {property.year_built && <span>Built {property.year_built}</span>}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2 border-t border-gray-100">
          {property.source_url && (
            <a
              href={property.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-outline text-sm flex-1 flex items-center justify-center gap-1"
            >
              <ExternalLink className="h-4 w-4" />
              View Listing
            </a>
          )}
          {isSaved ? (
            <button
              onClick={onViewSaved}
              className="btn-primary text-sm flex-1 flex items-center justify-center gap-1 bg-green-600 hover:bg-green-700"
            >
              <Check className="h-4 w-4" />
              View Saved
            </button>
          ) : (
            <button
              onClick={onSaveAndAnalyze}
              disabled={isSaving || isProcessing}
              className={cn(
                "btn-primary text-sm flex-1 flex items-center justify-center gap-1",
                (isSaving || isProcessing) && "opacity-75 cursor-not-allowed"
              )}
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Bookmark className="h-4 w-4" />
                  Save & Analyze
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function DealsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const initialSearchDone = useRef(false);
  const restoredFromStorage = useRef(false);
  const scrollRestored = useRef(false);

  // Read initial values from URL params
  const urlMarket = searchParams.get("market") || searchParams.get("markets") || "";
  const urlMaxPrice = searchParams.get("maxPrice") || "200000";
  const urlMinBeds = searchParams.get("minBeds") || "2";
  const urlSortBy = searchParams.get("sortBy") || "price_asc";

  // Live properties state
  const [allProperties, setAllProperties] = useState<PropertyListing[]>([]); // Full results from API
  const [displayCount, setDisplayCount] = useState(INITIAL_LOAD); // How many to show
  const [apiUsage, setApiUsage] = useState<ApiUsage | null>(null);
  const [sortBy, setSortBy] = useState<string>(urlSortBy);

  // Common state
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bulk analyze state
  const [analyzingAll, setAnalyzingAll] = useState(false);
  const [analyzeProgress, setAnalyzeProgress] = useState<{
    total: number;
    processed: number;
    newJobs: number;
    alreadyAnalyzed: number;
    inProgress: number;
    errors: number;
  } | null>(null);
  const [analyzedInSession, setAnalyzedInSession] = useState<Set<string>>(new Set());

  // Selection state
  const [selectedPropertyIds, setSelectedPropertyIds] = useState<Set<string>>(new Set());
  const [savedPropertyIds, setSavedPropertyIds] = useState<Set<string>>(new Set());

  // Property save/analyze state tracking
  const [savingPropertyIds, setSavingPropertyIds] = useState<Set<string>>(new Set());
  const [processingPropertyIds, setProcessingPropertyIds] = useState<Map<string, string>>(new Map()); // property_id -> saved_property_id
  const [savedPropertyIdMap, setSavedPropertyIdMap] = useState<Map<string, string>>(new Map()); // property_id -> saved_property_id

  // Job queue state
  const [jobStats, setJobStats] = useState<JobStats | null>(null);

  // URL import state
  const [showUrlImport, setShowUrlImport] = useState(false);
  const [importUrl, setImportUrl] = useState("");
  const [importingUrl, setImportingUrl] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState(false);

  // Markets dropdown
  const [availableMarkets, setAvailableMarkets] = useState<string[]>(DEFAULT_MARKETS);
  const [loadingMarkets, setLoadingMarkets] = useState(true);

  // Filters - initialize from URL params
  const [maxPrice, setMaxPrice] = useState<string>(urlMaxPrice);
  const [minBeds, setMinBeds] = useState(urlMinBeds);
  const [selectedLocation, setSelectedLocation] = useState<string>("");

  // Update URL when filters change (without triggering navigation)
  const updateUrlParams = useCallback((params: Record<string, string>) => {
    const newParams = new URLSearchParams(searchParams.toString());
    Object.entries(params).forEach(([key, value]) => {
      if (value) {
        newParams.set(key, value);
      } else {
        newParams.delete(key);
      }
    });
    const newUrl = `${pathname}?${newParams.toString()}`;
    window.history.replaceState({}, "", newUrl);
  }, [pathname, searchParams]);

  // Save state to sessionStorage when results change
  useEffect(() => {
    if (allProperties.length > 0 && !loading && selectedLocation) {
      saveState({
        properties: allProperties,
        displayCount,
        scrollY: window.scrollY,
        apiUsage,
        selectedLocation,
        maxPrice,
        minBeds,
        sortBy,
      });
    }
  }, [allProperties, displayCount, apiUsage, loading, selectedLocation, maxPrice, minBeds, sortBy]);

  // Save scroll position before navigating away
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (allProperties.length > 0 && selectedLocation) {
        saveState({
          properties: allProperties,
          displayCount,
          scrollY: window.scrollY,
          apiUsage,
          selectedLocation,
          maxPrice,
          minBeds,
          sortBy,
        });
      }
    };

    // Save on any navigation
    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      // Save when component unmounts (navigation within app)
      handleBeforeUnload();
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [allProperties, displayCount, apiUsage, selectedLocation, maxPrice, minBeds, sortBy]);

  // Restore scroll position after content loads
  useEffect(() => {
    if (!loading && !scrollRestored.current && restoredFromStorage.current) {
      const stored = loadState();
      if (stored && stored.scrollY > 0) {
        // Small delay to ensure content is rendered
        setTimeout(() => {
          window.scrollTo(0, stored.scrollY);
        }, 100);
      }
      scrollRestored.current = true;
    }
  }, [loading]);

  // Get sorted and paginated properties
  const sortedProperties = [...allProperties].sort(
    SORT_OPTIONS.find(opt => opt.value === sortBy)?.sortFn || ((a, b) => a.price - b.price)
  );
  const displayedProperties = sortedProperties.slice(0, displayCount);
  const hasMore = displayCount < allProperties.length;
  const canLoadMoreFromApi = allProperties.length < MAX_RESULTS && apiUsage?.requests_remaining && apiUsage.requests_remaining > 0;

  // Search live properties
  const searchLiveProperties = useCallback(async (append = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setSearching(true);
        setDisplayCount(INITIAL_LOAD);
      }
      setError(null);

      const currentCount = append ? allProperties.length : 0;
      const limit = append ? LOAD_MORE_COUNT : INITIAL_LOAD;

      const res = await api.searchLiveProperties({
        location: selectedLocation,
        max_price: maxPrice ? parseInt(maxPrice) : undefined,
        min_beds: minBeds ? parseInt(minBeds) : undefined,
        limit: Math.min(currentCount + limit, MAX_RESULTS),
      });

      if (append) {
        // Only add new properties we don't already have
        const existingIds = new Set(allProperties.map(p => p.property_id));
        const newProperties = res.properties.filter(p => !existingIds.has(p.property_id));
        setAllProperties(prev => [...prev, ...newProperties]);
        setDisplayCount(prev => prev + newProperties.length);
      } else {
        setAllProperties(res.properties);
      }

      setApiUsage(res.api_usage);

      if (res.properties.length === 0 && res.api_usage.warning === "limit_reached") {
        setError("API limit reached. Import properties via URL on the Import page.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
      setLoadingMore(false);
      setLoading(false);
    }
  }, [selectedLocation, maxPrice, minBeds, allProperties]);

  // Load more results (show more from cache or fetch from API)
  const handleLoadMore = useCallback(() => {
    if (hasMore) {
      // Show more from already fetched results
      setDisplayCount(prev => Math.min(prev + LOAD_MORE_COUNT, allProperties.length));
    } else if (canLoadMoreFromApi) {
      // Fetch more from API
      searchLiveProperties(true);
    }
  }, [hasMore, canLoadMoreFromApi, searchLiveProperties, allProperties.length]);

  // Save and analyze a property - saves to database and queues enrichment job
  const handleSaveAndAnalyze = async (property: PropertyListing) => {
    const propertyId = property.property_id;

    // Mark as saving
    setSavingPropertyIds(prev => new Set(prev).add(propertyId));

    try {
      // Create property record (or get existing one) via API
      const response = await api.enqueuePropertyJob({
        address: property.address,
        city: property.city,
        state: property.state,
        zip_code: property.zip_code,
        latitude: property.latitude,
        longitude: property.longitude,
        list_price: property.price,
        bedrooms: property.bedrooms,
        bathrooms: property.bathrooms,
        sqft: property.sqft || undefined,
        property_type: property.property_type,
        source: property.source,
        source_url: property.source_url,
        photos: property.photos,
        description: property.description,
      });

      // Remove from saving
      setSavingPropertyIds(prev => {
        const next = new Set(prev);
        next.delete(propertyId);
        return next;
      });

      // Track saved property ID mapping
      setSavedPropertyIdMap(prev => new Map(prev).set(propertyId, response.property_id));

      if (response.status === "already_analyzed") {
        // Already saved and analyzed - mark as saved
        setSavedPropertyIds(prev => new Set(prev).add(propertyId));
        const key = `${property.address}|${property.city}|${property.state}`.toLowerCase();
        setSavedPropertyIds(prev => new Set(prev).add(key));
      } else {
        // Job is running - mark as processing
        setProcessingPropertyIds(prev => new Map(prev).set(propertyId, response.property_id));

        // Refresh job stats
        refreshJobStats();
      }
    } catch (err) {
      console.error("Failed to save property:", err);
      // Remove from saving on error
      setSavingPropertyIds(prev => {
        const next = new Set(prev);
        next.delete(propertyId);
        return next;
      });
    }
  };

  // Navigate to saved property detail
  const handleViewSaved = (property: PropertyListing) => {
    const savedId = savedPropertyIdMap.get(property.property_id);
    if (savedId) {
      router.push(`/saved/${savedId}`);
    } else {
      // Fallback: try to find by address-based lookup in saved properties
      router.push("/saved");
    }
  };

  // Refresh job stats
  const refreshJobStats = async () => {
    try {
      const stats = await api.getJobStats();
      setJobStats(stats);
    } catch (err) {
      console.error("Failed to fetch job stats:", err);
    }
  };

  // Handle URL import
  const handleUrlImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importUrl.trim()) return;

    setImportingUrl(true);
    setImportError(null);
    setImportSuccess(false);

    try {
      // For URL import, we need to first parse the URL to get property data
      // Then enqueue it just like Save & Analyze
      const response = await api.importFromUrl({
        url: importUrl.trim(),
        down_payment_pct: 0.2,
        interest_rate: 0.07,
      });

      if (response.success && response.saved_id) {
        setImportSuccess(true);
        setImportUrl("");
        refreshJobStats();

        // Auto-hide success message after 3 seconds
        setTimeout(() => {
          setImportSuccess(false);
          setShowUrlImport(false);
        }, 3000);
      } else {
        setImportError(response.message || "Failed to import property");
      }
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Failed to import. Try pasting the full property URL.");
    } finally {
      setImportingUrl(false);
    }
  };

  // Check if a property is saved
  const isPropertySaved = useCallback((property: PropertyListing) => {
    // Check by property_id
    if (savedPropertyIds.has(property.property_id)) return true;
    // Check by address-based key
    const key = `${property.address}|${property.city}|${property.state}`.toLowerCase();
    return savedPropertyIds.has(key);
  }, [savedPropertyIds]);

  // Get card state for a property
  const getCardState = useCallback((property: PropertyListing): CardState => {
    if (savingPropertyIds.has(property.property_id)) return "saving";
    if (processingPropertyIds.has(property.property_id)) return "processing";
    if (isPropertySaved(property)) return "saved";
    return "default";
  }, [savingPropertyIds, processingPropertyIds, isPropertySaved]);

  // Toggle property selection
  const togglePropertySelection = useCallback((propertyId: string) => {
    setSelectedPropertyIds(prev => {
      const next = new Set(prev);
      if (next.has(propertyId)) {
        next.delete(propertyId);
      } else {
        next.add(propertyId);
      }
      return next;
    });
  }, []);

  // Clear selection
  const clearSelection = useCallback(() => {
    setSelectedPropertyIds(new Set());
  }, []);

  // Save and analyze all visible properties (or selected ones) in bulk
  const handleSaveAll = async () => {
    if (analyzingAll) return;

    // If properties are selected, only save those; otherwise save all displayed
    const baseProperties = selectedPropertyIds.size > 0
      ? displayedProperties.filter(p => selectedPropertyIds.has(p.property_id))
      : displayedProperties;

    // Get properties to save - only those not already saved
    const propertiesToSave = baseProperties.filter(
      p => !isPropertySaved(p) && !savingPropertyIds.has(p.property_id) && !processingPropertyIds.has(p.property_id)
    );

    if (propertiesToSave.length === 0) {
      setAnalyzeProgress({
        total: baseProperties.length,
        processed: baseProperties.length,
        newJobs: 0,
        alreadyAnalyzed: baseProperties.length,
        inProgress: 0,
        errors: 0,
      });
      return;
    }

    setAnalyzingAll(true);
    setAnalyzeProgress({
      total: propertiesToSave.length,
      processed: 0,
      newJobs: 0,
      alreadyAnalyzed: 0,
      inProgress: 0,
      errors: 0,
    });

    let newJobs = 0;
    let alreadyAnalyzed = 0;
    let inProgress = 0;
    let errors = 0;
    const newlySaved = new Set<string>();
    const newProcessing = new Map<string, string>();
    const newSavedIds = new Map<string, string>();

    // Process properties sequentially to avoid rate limiting
    for (let i = 0; i < propertiesToSave.length; i++) {
      const property = propertiesToSave[i];

      try {
        const response = await api.enqueuePropertyJob({
          address: property.address,
          city: property.city,
          state: property.state,
          zip_code: property.zip_code,
          latitude: property.latitude,
          longitude: property.longitude,
          list_price: property.price,
          bedrooms: property.bedrooms,
          bathrooms: property.bathrooms,
          sqft: property.sqft || undefined,
          property_type: property.property_type,
          source: property.source,
          source_url: property.source_url,
          photos: property.photos,
        });

        // Track saved property ID mapping
        newSavedIds.set(property.property_id, response.property_id);

        // Track by response status
        if (response.status === "already_analyzed") {
          alreadyAnalyzed++;
          newlySaved.add(property.property_id);
        } else if (response.status === "running" || response.status === "pending") {
          if (response.job_id) {
            inProgress++;
          }
          newJobs++;
          newProcessing.set(property.property_id, response.property_id);
        }
      } catch (err) {
        console.error(`Failed to save property ${property.address}:`, err);
        errors++;
      }

      // Update progress
      setAnalyzeProgress({
        total: propertiesToSave.length,
        processed: i + 1,
        newJobs,
        alreadyAnalyzed,
        inProgress,
        errors,
      });
    }

    // Update state tracking
    setSavedPropertyIdMap(prev => {
      const updated = new Map(prev);
      newSavedIds.forEach((v, k) => updated.set(k, v));
      return updated;
    });

    // Mark already analyzed as saved
    if (newlySaved.size > 0) {
      setSavedPropertyIds(prev => {
        const updated = new Set(prev);
        newlySaved.forEach(id => updated.add(id));
        return updated;
      });
    }

    // Mark processing ones
    if (newProcessing.size > 0) {
      setProcessingPropertyIds(prev => {
        const updated = new Map(prev);
        newProcessing.forEach((v, k) => updated.set(k, v));
        return updated;
      });
    }

    // Clear selection after saving
    clearSelection();
    setAnalyzingAll(false);

    // Refresh job stats
    refreshJobStats();
  };

  // Load favorite markets for dropdown
  useEffect(() => {
    async function loadMarkets() {
      try {
        setLoadingMarkets(true);
        const markets = await api.getFavoriteMarkets();
        if (markets.length > 0) {
          // Convert to location format: "City, ST"
          const marketLocations = markets.map(m => `${m.name}, ${m.state}`);
          setAvailableMarkets(marketLocations);
        }
      } catch (err) {
        console.error("Failed to load markets, using defaults:", err);
      } finally {
        setLoadingMarkets(false);
      }
    }
    loadMarkets();
  }, []);

  // Load saved property IDs to show "Saved" indicators
  useEffect(() => {
    async function loadSavedPropertyIds() {
      try {
        const savedProperties = await api.getSavedProperties();
        // Create a set of identifiers we can match against
        // Match by address + city + state since property_id formats differ
        const savedSet = new Set<string>();
        const idMap = new Map<string, string>();

        savedProperties.forEach(p => {
          // Add the property ID directly
          if (p.id) {
            savedSet.add(p.id);
            // Also store in ID map for navigation
            idMap.set(p.id, p.id);
          }
          // Also add address-based key for matching
          const key = `${p.address}|${p.city}|${p.state}`.toLowerCase();
          savedSet.add(key);
        });
        setSavedPropertyIds(savedSet);
        setSavedPropertyIdMap(prev => {
          const merged = new Map(prev);
          idMap.forEach((v, k) => merged.set(k, v));
          return merged;
        });
      } catch (err) {
        console.error("Failed to load saved properties:", err);
      }
    }
    loadSavedPropertyIds();
  }, []);

  // Poll job stats periodically to update queue indicator
  useEffect(() => {
    // Initial fetch
    refreshJobStats();

    // Poll every 5 seconds if there are processing properties
    const interval = setInterval(() => {
      if (processingPropertyIds.size > 0) {
        refreshJobStats();

        // Check if any processing properties have completed
        // by fetching saved properties again
        api.getSavedProperties().then(savedProperties => {
          const completedIds: string[] = [];

          processingPropertyIds.forEach((savedId, propertyId) => {
            // Check if this property now has analysis data
            const savedProp = savedProperties.find(p => p.id === savedId);
            if (savedProp && savedProp.overall_score !== null && savedProp.overall_score !== undefined) {
              completedIds.push(propertyId);
            }
          });

          if (completedIds.length > 0) {
            // Move from processing to saved
            setProcessingPropertyIds(prev => {
              const next = new Map(prev);
              completedIds.forEach(id => next.delete(id));
              return next;
            });
            setSavedPropertyIds(prev => {
              const next = new Set(prev);
              completedIds.forEach(id => next.add(id));
              return next;
            });
          }
        }).catch(err => {
          console.error("Failed to check processing properties:", err);
        });
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [processingPropertyIds.size]);

  // Try to restore state from sessionStorage on mount
  useEffect(() => {
    if (restoredFromStorage.current) return;

    const stored = loadState();
    if (stored && stored.properties.length > 0) {
      // Restore from sessionStorage
      setAllProperties(stored.properties);
      setDisplayCount(stored.displayCount);
      setApiUsage(stored.apiUsage);
      setSelectedLocation(stored.selectedLocation);
      setMaxPrice(stored.maxPrice);
      setMinBeds(stored.minBeds);
      setSortBy(stored.sortBy);
      setLoading(false);
      restoredFromStorage.current = true;
      initialSearchDone.current = true;
    }
  }, []);

  // Set initial location from URL param or first available market
  useEffect(() => {
    if (loadingMarkets) return; // Wait for markets to load

    if (urlMarket && !initialSearchDone.current) {
      // Convert market ID to location format
      const location = marketIdToLocation(urlMarket);
      setSelectedLocation(location);

      // Add to available markets if not already there
      if (!availableMarkets.includes(location)) {
        setAvailableMarkets(prev => [location, ...prev]);
      }
    } else if (!selectedLocation && availableMarkets.length > 0) {
      // Default to first market if none selected
      setSelectedLocation(availableMarkets[0]);
    }
  }, [urlMarket, loadingMarkets, availableMarkets]);

  // Search when location is set (initial load only if not restored)
  useEffect(() => {
    if (selectedLocation && !initialSearchDone.current) {
      initialSearchDone.current = true;
      setLoading(true);
      searchLiveProperties();
    }
  }, [selectedLocation]);

  // Update URL when filters/sort change
  useEffect(() => {
    if (selectedLocation) {
      updateUrlParams({
        market: selectedLocation,
        maxPrice,
        minBeds,
        sortBy,
      });
    }
  }, [selectedLocation, maxPrice, minBeds, sortBy, updateUrlParams]);

  // Handle search button click
  const handleSearch = () => {
    searchLiveProperties();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Find Deals</h1>
          <p className="text-gray-500 mt-1">
            Search live property listings and save for analysis
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Job Queue Indicator */}
          {jobStats && (jobStats.pending > 0 || jobStats.running > 0) && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-full text-sm">
              <Clock className="h-4 w-4 text-amber-600 animate-pulse" />
              <span className="text-amber-700">
                Processing {jobStats.running} of {jobStats.pending + jobStats.running}
              </span>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-green-600">
            <Radio className="h-4 w-4" />
            <span>Live Data</span>
          </div>
        </div>
      </div>

      {/* URL Import Section */}
      <div className="flex items-center gap-4">
        {!showUrlImport ? (
          <button
            onClick={() => setShowUrlImport(true)}
            className="btn-outline text-sm flex items-center gap-2"
          >
            <Link2 className="h-4 w-4" />
            Import URL
          </button>
        ) : (
          <form onSubmit={handleUrlImport} className="flex-1 max-w-2xl">
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <input
                  type="url"
                  value={importUrl}
                  onChange={(e) => setImportUrl(e.target.value)}
                  placeholder="Paste Zillow, Redfin, or Realtor.com URL..."
                  className="input pr-10"
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => {
                    setShowUrlImport(false);
                    setImportUrl("");
                    setImportError(null);
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <button
                type="submit"
                disabled={importingUrl || !importUrl.trim()}
                className="btn-primary flex items-center gap-2"
              >
                {importingUrl ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Bookmark className="h-4 w-4" />
                    Import & Save
                  </>
                )}
              </button>
            </div>
            {importError && (
              <p className="text-sm text-red-600 mt-2 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {importError}
              </p>
            )}
            {importSuccess && (
              <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                <CheckCircle className="h-4 w-4" />
                Property imported! Check your Saved Properties.
              </p>
            )}
          </form>
        )}
      </div>

      {/* Search Controls */}
      <div className="card">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="label">Market</label>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="input"
                  disabled={loadingMarkets}
                >
                  {availableMarkets.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>

              <div className="w-40">
                <label className="label">Max Price</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="text"
                    value={maxPrice ? parseInt(maxPrice).toLocaleString() : ""}
                    onChange={(e) => {
                      const raw = e.target.value.replace(/[^0-9]/g, "");
                      setMaxPrice(raw);
                    }}
                    placeholder="Any"
                    className="input pl-7"
                  />
                </div>
              </div>

              <div className="w-32">
                <label className="label">Min Beds</label>
                <select
                  value={minBeds}
                  onChange={(e) => setMinBeds(e.target.value)}
                  className="input"
                >
                  <option value="1">1+</option>
                  <option value="2">2+</option>
                  <option value="3">3+</option>
                  <option value="4">4+</option>
                </select>
              </div>

              <button
                onClick={handleSearch}
                disabled={searching || (apiUsage?.warning === "limit_reached")}
                className="btn-primary flex items-center gap-2"
              >
                {searching ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
                Search
              </button>
            </div>

            {/* API Usage info */}
            {apiUsage && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Radio className="h-4 w-4 text-green-500" />
                    <span>Live data from {apiUsage.provider}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500">API calls:</span>
                    <span className={cn(
                      "font-medium",
                      apiUsage.warning === "limit_reached" ? "text-red-600" :
                      apiUsage.warning === "approaching_limit" ? "text-amber-600" : "text-green-600"
                    )}>
                      {apiUsage.requests_remaining}/{apiUsage.requests_limit} remaining
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results */}
          {loading || loadingMarkets ? (
            <LoadingPage />
          ) : error ? (
            <div className="card text-center py-8">
              <p className="text-red-600">{error}</p>
              <button onClick={handleSearch} className="btn-primary mt-4">
                Try Again
              </button>
            </div>
          ) : allProperties.length === 0 ? (
            <div className="card text-center py-12 animate-fade-in">
              <Building className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900">No properties found</h3>
              <p className="text-gray-500 mt-1 max-w-md mx-auto">
                {apiUsage?.warning === "limit_reached"
                  ? "API limit reached. Import properties via URL on the Import page."
                  : "No active listings match your criteria. Try adjusting your filters."}
              </p>
              {apiUsage?.warning !== "limit_reached" && (
                <button onClick={handleSearch} className="btn-primary mt-4">
                  <Search className="h-4 w-4 inline mr-2" />
                  Try Again
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4 animate-fade-in">
              {/* Results Header with Sort and Analyze */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <p className="text-sm text-gray-500">
                    {selectedPropertyIds.size > 0 ? (
                      <>
                        {selectedPropertyIds.size} selected of {displayedProperties.length} properties
                        <button
                          onClick={clearSelection}
                          className="ml-2 text-primary-600 hover:text-primary-700 underline"
                        >
                          Clear
                        </button>
                      </>
                    ) : (
                      <>Showing {displayedProperties.length} of {allProperties.length} properties in {selectedLocation}</>
                    )}
                  </p>
                </div>

                {/* Sort and Analyze */}
                <div className="flex items-center gap-3">
                  {/* Sort Dropdown */}
                  <div className="flex items-center gap-2">
                    <ArrowUpDown className="h-4 w-4 text-gray-400" />
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    >
                      {SORT_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Save All Button */}
                  <button
                    onClick={handleSaveAll}
                    disabled={analyzingAll || displayedProperties.length === 0}
                    className={cn(
                      "flex items-center gap-2 px-4 py-1.5 text-sm font-medium rounded-md transition-colors",
                      analyzingAll
                        ? "bg-gray-100 text-gray-500 cursor-not-allowed"
                        : "bg-primary-600 text-white hover:bg-primary-700"
                    )}
                  >
                    {analyzingAll ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Saving {analyzeProgress?.processed}/{analyzeProgress?.total}...
                      </>
                    ) : selectedPropertyIds.size > 0 ? (
                      <>
                        <Bookmark className="h-4 w-4" />
                        Save Selected ({selectedPropertyIds.size})
                      </>
                    ) : (
                      <>
                        <Bookmark className="h-4 w-4" />
                        Save All ({displayedProperties.length})
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Save Progress/Results Banner */}
              {analyzeProgress && !analyzingAll && analyzeProgress.processed > 0 && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <div className="flex items-center gap-3 text-sm">
                        {analyzeProgress.newJobs > 0 && (
                          <span className="text-primary-600 font-medium">
                            {analyzeProgress.newJobs} saved & queued for analysis
                          </span>
                        )}
                        {analyzeProgress.alreadyAnalyzed > 0 && (
                          <span className="text-gray-500">
                            {analyzeProgress.alreadyAnalyzed} already saved
                          </span>
                        )}
                        {analyzeProgress.errors > 0 && (
                          <span className="text-red-500 flex items-center gap-1">
                            <AlertCircle className="h-4 w-4" />
                            {analyzeProgress.errors} failed
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => setAnalyzeProgress(null)}
                      className="text-gray-400 hover:text-gray-600 text-sm"
                    >
                      Dismiss
                    </button>
                  </div>
                  {analyzeProgress.newJobs > 0 && (
                    <p className="mt-2 text-xs text-gray-500">
                      Properties are being analyzed in the background. Visit Saved Properties to see results.
                    </p>
                  )}
                </div>
              )}

              {/* Property Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {displayedProperties.map((property, index) => (
                  <div
                    key={property.property_id}
                    className="animate-slide-up"
                    style={{ animationDelay: `${Math.min(index, 5) * 50}ms` }}
                  >
                    <LivePropertyCard
                      property={property}
                      onSaveAndAnalyze={() => handleSaveAndAnalyze(property)}
                      onViewSaved={() => handleViewSaved(property)}
                      isSelected={selectedPropertyIds.has(property.property_id)}
                      onToggleSelect={() => togglePropertySelection(property.property_id)}
                      cardState={getCardState(property)}
                      savedPropertyId={savedPropertyIdMap.get(property.property_id)}
                    />
                  </div>
                ))}
              </div>

              {/* Load More Button */}
              {(hasMore || canLoadMoreFromApi) && (
                <div className="flex justify-center pt-4">
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="btn-outline flex items-center gap-2 px-6"
                  >
                    {loadingMore ? (
                      <>
                        <LoadingSpinner size="sm" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        Load More
                        {hasMore && (
                          <span className="text-gray-400 text-sm">
                            ({allProperties.length - displayCount} more cached)
                          </span>
                        )}
                        {!hasMore && canLoadMoreFromApi && (
                          <span className="text-gray-400 text-sm">
                            (fetch from API)
                          </span>
                        )}
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* End of results indicator */}
              {!hasMore && !canLoadMoreFromApi && allProperties.length > 0 && (
                <p className="text-center text-sm text-gray-400 pt-4">
                  {allProperties.length >= MAX_RESULTS
                    ? `Showing maximum ${MAX_RESULTS} results`
                    : "All properties loaded"}
                </p>
              )}
            </div>
          )}
    </div>
  );
}

export default function DealsPage() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <DealsContent />
    </Suspense>
  );
}
