// src/shared/infrastructure/http/coreApiClient.ts
// @deprecated このファイルは非推奨です。代わりに coreApi.ts を使用してください。
// 唯一のHTTPクライアント - すべての通信は /core_api/... 経由

/**
 * @deprecated 代わりに coreApi.ts の coreApi を使用してください
 */
export type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface HttpOptions {
  method?: Method;
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeoutMs?: number;
}

/**
 * core_api への統一リクエスト関数
 * すべての通信は /core_api/... パスを通じて行う
 */
async function coreRequest<T>(path: string, opts: HttpOptions = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = opts.timeoutMs ?? 15000;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(opts.headers ?? {}),
    };

    const res = await fetch(path, {
      method: opts.method ?? 'GET',
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      signal: opts.signal ?? controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status} ${res.statusText} - ${text}`);
    }

    return (await res.json()) as T;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * core_api 統一クライアント
 * @deprecated このクライアントは非推奨です。代わりに @shared/infrastructure/http/coreApi の coreApi を使用してください
 * すべてのHTTP通信はこのクライアント経由で /core_api/... に送信
 */
export const coreApi = {
  get: <T>(p: string, o?: Omit<HttpOptions, 'method' | 'body'>) =>
    coreRequest<T>(p, { ...o, method: 'GET' }),

  post: <T>(p: string, body?: unknown, o?: Omit<HttpOptions, 'method'>) =>
    coreRequest<T>(p, { ...o, method: 'POST', body }),

  put: <T>(p: string, body?: unknown, o?: Omit<HttpOptions, 'method'>) =>
    coreRequest<T>(p, { ...o, method: 'PUT', body }),

  patch: <T>(p: string, body?: unknown, o?: Omit<HttpOptions, 'method'>) =>
    coreRequest<T>(p, { ...o, method: 'PATCH', body }),

  delete: <T>(p: string, o?: Omit<HttpOptions, 'method' | 'body'>) =>
    coreRequest<T>(p, { ...o, method: 'DELETE' }),
};
