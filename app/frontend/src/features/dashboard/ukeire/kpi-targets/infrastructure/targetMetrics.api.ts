/**
 * Target Metrics API Client
 * Fetches monthly/weekly/daily target metrics and actuals from core_api
 * Optimized with client-side caching to prevent duplicate requests
 */

import { coreApi } from '@/shared';

export type FetchMode = "daily" | "monthly";

export interface TargetMetricsDTO {
  ddate: string | null;
  month_target_ton: number | null;
  week_target_ton: number | null;
  day_target_ton: number | null;
  month_actual_ton: number | null;
  week_actual_ton: number | null;
  day_actual_ton_prev: number | null;
  iso_year: number | null;
  iso_week: number | null;
  iso_dow: number | null;
  day_type: string | null;
  is_business: boolean | null;
  // New fields for achievement mode calculation (cumulative to yesterday vs. total at period end)
  month_target_to_date_ton: number | null;
  month_target_total_ton: number | null;
  week_target_to_date_ton: number | null;
  week_target_total_ton: number | null;
  month_actual_to_date_ton: number | null;
  week_actual_to_date_ton: number | null;
}

// Simple in-memory cache with 60-second TTL
interface CacheEntry {
  data: TargetMetricsDTO;
  timestamp: number;
}

const cache = new Map<string, CacheEntry>();
const CACHE_TTL = 60 * 1000; // 60 seconds

// In-flight request tracker to prevent duplicate concurrent requests
const inflightRequests = new Map<string, Promise<TargetMetricsDTO>>();

/**
 * Fetch target and actual metrics for a specific date
 * Uses client-side cache to prevent duplicate requests within 60 seconds
 * Prevents concurrent duplicate requests using in-flight request tracking
 * @param date - ISO date string (YYYY-MM-DD). For monthly view, use first day of month.
 * @param mode - Fetch mode: 'daily' for specific date, 'monthly' for month-level view with day/week masking
 * @returns Target and actual metrics (monthly, weekly, daily)
 */
export async function fetchTargetMetrics(
  date: string, 
  mode: FetchMode = "monthly"
): Promise<TargetMetricsDTO> {
  const cacheKey = `${date}-${mode}`;
  
  // Check cache first
  const cached = cache.get(cacheKey);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    console.log(`[fetchTargetMetrics] Cache hit for ${cacheKey}`);
    return cached.data;
  }
  
  // Check if there's already an in-flight request for this key
  const existingRequest = inflightRequests.get(cacheKey);
  if (existingRequest) {
    console.log(`[fetchTargetMetrics] Reusing in-flight request for ${cacheKey}`);
    return existingRequest;
  }
  
  // Create new request and track it
  const requestPromise = (async () => {
    try {
      // Use coreApi instead of fetch
      const data = await coreApi.get<TargetMetricsDTO>(
        `/core_api/dashboard/target?date=${date}&mode=${mode}`
      );
      
      // Store in cache
      cache.set(cacheKey, { data, timestamp: Date.now() });
      console.log(`[fetchTargetMetrics] Fetched and cached ${cacheKey}`);
      
      return data;
    } catch (error) {
      console.error(`[fetchTargetMetrics] Error fetching ${cacheKey}:`, error);
      throw error;
    } finally {
      // Clean up in-flight request tracker
      inflightRequests.delete(cacheKey);
    }
  })();
  
  // Track the in-flight request
  inflightRequests.set(cacheKey, requestPromise);
  
  return requestPromise;
}

/**
 * Clear the client-side cache and in-flight requests
 * Useful after data updates or for testing
 */
export function clearTargetMetricsCache(): void {
  cache.clear();
  inflightRequests.clear();
  console.log('[fetchTargetMetrics] Cache and in-flight requests cleared');
}


