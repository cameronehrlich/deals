/**
 * Electron API bridge.
 *
 * This file provides typed access to Electron's IPC APIs exposed via preload.js.
 * When running in a browser (not Electron), these functions gracefully fall back.
 */

// Types for scraped property data
export interface ScrapedProperty {
  address: string;
  city: string;
  state: string;
  zip_code: string;
  list_price: number;
  bedrooms: number;
  bathrooms: number;
  sqft: number | null;
  property_type: string;
  source: string;
  source_url: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface ScrapeResult {
  success: boolean;
  data?: ScrapedProperty;
  error?: string;
}

// Electron API interface (exposed via preload.js)
interface ElectronAPI {
  scrapeProperty: (url: string) => Promise<ScrapeResult>;
  isElectron: () => Promise<boolean>;
  getApiUrl: () => Promise<string>;
  platform: string;
}

// Declare global window extension
declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

/**
 * Check if running in Electron.
 */
export function isElectron(): boolean {
  return typeof window !== 'undefined' && !!window.electronAPI;
}

/**
 * Scrape a property URL using local Puppeteer (Electron only).
 * Returns null if not in Electron.
 */
export async function scrapePropertyLocally(url: string): Promise<ScrapeResult | null> {
  if (!isElectron()) {
    return null;
  }

  try {
    return await window.electronAPI!.scrapeProperty(url);
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Get the API URL (may be different in Electron vs browser).
 */
export async function getApiUrl(): Promise<string> {
  if (isElectron()) {
    return await window.electronAPI!.getApiUrl();
  }
  // Browser mode: use the environment variable or default
  return process.env.NEXT_PUBLIC_API_URL || 'https://deals-api-swart.vercel.app';
}

/**
 * Get the platform (darwin, win32, linux).
 */
export function getPlatform(): string {
  if (isElectron()) {
    return window.electronAPI!.platform;
  }
  return 'browser';
}
