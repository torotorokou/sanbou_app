/**
 * Manual API Client
 * BFF (/core_api/manual/...) へのAPIクライアント
 */

export const ManualClient = {
  /**
   * マニュアル検索
   */
  async search(body: unknown, signal?: AbortSignal): Promise<unknown> {
    const res = await fetch(`/core_api/manual/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Manual search failed: ${res.status} - ${text}`);
    }
    return res.json();
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
    const res = await fetch(`/core_api/manual/toc`, { signal });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Manual toc failed: ${res.status} - ${text}`);
    }
    return res.json();
  },

  /**
   * カテゴリ一覧の取得
   */
  async categories(signal?: AbortSignal): Promise<unknown> {
    const res = await fetch(`/core_api/manual/categories`, { signal });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Manual categories failed: ${res.status} - ${text}`);
    }
    return res.json();
  },
};
