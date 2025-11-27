import { coreApi } from '@/shared';

/**
 * Manual API Client
 * BFF (/core_api/manual/...) へのAPIクライアント
 */

export const ManualClient = {
  /**
   * マニュアル検索
   */
  async search(body: unknown, signal?: AbortSignal): Promise<unknown> {
    return coreApi.post('/core_api/manual/search', body, { signal });
  },

  /**
   * ドキュメントURLの生成
   */
  docUrl(docId: string, filename: string, query?: Record<string, string>): string {
    const params = query ? `?${new URLSearchParams(query).toString()}` : '';
    return `/core_api/manual/docs/${encodeURIComponent(docId)}/${encodeURIComponent(filename)}${params}`;
  },

  /**
   * マニュアル目次の取得
   */
  async toc(signal?: AbortSignal): Promise<unknown> {
    return coreApi.get('/core_api/manual/toc', { signal });
  },

  /**
   * カテゴリ一覧の取得
   */
  async categories(signal?: AbortSignal): Promise<unknown> {
    return coreApi.get('/core_api/manual/categories', { signal });
  },
};
