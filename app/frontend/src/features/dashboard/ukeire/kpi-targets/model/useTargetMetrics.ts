/**
 * useTargetMetrics - Custom hook for fetching target metrics
 * Optimized with minimal re-renders and previous data retention
 */

import { useState, useEffect, useRef } from "react";
import {
  fetchTargetMetrics,
  type TargetMetricsDTO,
  type FetchMode,
} from "../infrastructure/targetMetrics.api";

export interface UseTargetMetricsResult {
  data: TargetMetricsDTO | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch target metrics for a specific date with optimized loading experience
 * @param date - ISO date string (YYYY-MM-DD). For monthly view, use first day of month.
 * @param mode - Fetch mode: 'daily' for specific date, 'monthly' for month-level view with day/week masking
 * @returns Target metrics state
 */
export function useTargetMetrics(
  date: string,
  mode: FetchMode = "monthly",
): UseTargetMetricsResult {
  const [data, setData] = useState<TargetMetricsDTO | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [refetchCounter, setRefetchCounter] = useState<number>(0);

  // Keep previous data during loading (similar to React Query's keepPreviousData)
  const previousDataRef = useRef<TargetMetricsDTO | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const result = await fetchTargetMetrics(date, mode);

        if (isMounted) {
          setData(result);
          previousDataRef.current = result;
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err : new Error("Unknown error"));
          // Keep previous data on error to avoid blank state
          if (previousDataRef.current) {
            setData(previousDataRef.current);
          }
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [date, mode, refetchCounter]);

  const refetch = () => {
    setRefetchCounter((prev) => prev + 1);
  };

  // Return data (current or previous if loading), loading state, error
  return {
    data: data || previousDataRef.current,
    loading,
    error,
    refetch,
  };
}
