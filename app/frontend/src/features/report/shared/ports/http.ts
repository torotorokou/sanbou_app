/**
 * HTTP Client Port
 * @shared/infrastructure/http への依存を抽象化するインターフェース
 */

export interface IHttpClient {
  get<T = unknown>(url: string, config?: RequestConfig): Promise<T>;
  post<T = unknown>(
    url: string,
    data?: unknown,
    config?: RequestConfig,
  ): Promise<T>;
  put<T = unknown>(
    url: string,
    data?: unknown,
    config?: RequestConfig,
  ): Promise<T>;
  delete<T = unknown>(url: string, config?: RequestConfig): Promise<T>;
}

export interface RequestConfig {
  headers?: Record<string, string>;
  params?: Record<string, unknown>;
  responseType?: "json" | "blob" | "text";
  signal?: AbortSignal;
}

/**
 * API Post Function Type
 * coreApi, apiPost などの型定義
 */
export type ApiPostFn = <T = unknown>(
  url: string,
  data?: unknown,
  config?: RequestConfig,
) => Promise<T>;

export type ApiGetFn = <T = unknown>(
  url: string,
  config?: RequestConfig,
) => Promise<T>;
