/**
 * 将軍マニュアル詳細表示用 Hook (ViewModel)
 * - データ取得
 * - アンカー処理
 * - ローディング状態管理
 */
import { useEffect, useRef, useState } from 'react';
import { ShogunClient } from '../infrastructure/shogun.client';
import type { ManualDetail } from '../domain/types/shogun.types';
import { ensureSectionAnchors, smoothScrollToAnchor, type TocItem } from '@/shared/utils/anchors';

export interface UseShogunDetailResult {
  data: ManualDetail | null;
  loading: boolean;
  error: Error | null;
  toc: TocItem[];
  contentRef: React.RefObject<HTMLDivElement>;
}

export function useShogunDetail(id: string | undefined): UseShogunDetailResult {
  const [data, setData] = useState<ManualDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [toc, setToc] = useState<TocItem[]>([]);
  const contentRef = useRef<HTMLDivElement>(null);

  // データ取得
  useEffect(() => {
    if (!id) {
      setError(new Error('ID is required'));
      setLoading(false);
      return;
    }

    let alive = true;
    const controller = new AbortController();

    (async () => {
      try {
        setLoading(true);
        setError(null);
        const detail = await ShogunClient.get(id);
        if (!alive) return;
        setData(detail);
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err : new Error(String(err)));
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
      controller.abort();
    };
  }, [id]);

  // アンカー処理
  useEffect(() => {
    const container = contentRef.current;
    if (!container || !data) return;

    // セクションにアンカーIDを付与し、TOCを生成
    const generatedToc = ensureSectionAnchors(container);
    setToc(generatedToc);

    // URLハッシュがあればスクロール
    if (window.location.hash) {
      smoothScrollToAnchor(container, window.location.hash);
    }
  }, [data]);

  return { data, loading, error, toc, contentRef };
}
