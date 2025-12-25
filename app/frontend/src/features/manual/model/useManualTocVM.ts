/**
 * useManualToc Hook (ViewModel)
 * マニュアル目次取得のロジック
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import type { ManualRepository } from "../ports/repository";
import { ManualRepositoryImpl } from "../infrastructure/manual.repository";
import type { ManualTocItem } from "../domain/types/manual.types";

export function useManualToc() {
  const repo: ManualRepository = useMemo(() => new ManualRepositoryImpl(), []);

  const [toc, setToc] = useState<ManualTocItem[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await repo.toc();
      setToc(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [repo]);

  useEffect(() => {
    const controller = new AbortController();
    fetch();
    return () => controller.abort();
  }, [fetch]);

  return { toc, isLoading, error, refetch: fetch };
}
