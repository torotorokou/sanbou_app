// src/shared/infrastructure/http/coreApi.ts
// /core_api 専用のHTTPクライアント（axios ベース）

import type { AxiosRequestConfig } from "axios";
import { client } from "./httpClient";

/**
 * パスを正規化し、/core_api/* であることを保証
 */
function normalize(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  if (!p.startsWith("/core_api/")) {
    throw new Error(`coreApi must target "/core_api/**" but got "${p}"`);
  }
  return p;
}

/**
 * coreApi: フロントエンドの統一HTTPクライアント
 * すべてのAPI呼び出しは /core_api/... 経由で BFF にルーティングされる
 */
export const coreApi = {
  async get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.get<T>(normalize(path), config);
    return res.data as T;
  },

  async post<T, B = unknown>(path: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.post<T>(normalize(path), body, config);
    return res.data as T;
  },

  async put<T, B = unknown>(path: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.put<T>(normalize(path), body, config);
    return res.data as T;
  },

  async patch<T, B = unknown>(path: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.patch<T>(normalize(path), body, config);
    return res.data as T;
  },

  async delete<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.delete<T>(normalize(path), config);
    return res.data as T;
  },

  /**
   * FormData アップロード専用メソッド
   * Content-Type は boundary 自動付与のため指定しない
   * 
   * @param path - API パス（/core_api/... で開始）
   * @param form - アップロードする FormData
   * @param config - axios 設定 + onProgress コールバック
   * @returns レスポンスデータ
   */
  async uploadForm<T>(
    path: string,
    form: FormData,
    config?: AxiosRequestConfig & { onProgress?: (pct?: number) => void }
  ): Promise<T> {
    const res = await client.post<T>(normalize(path), form, {
      ...config,
      // Content-Type は boundary 自動付与のため指定しない
      headers: { ...(config?.headers ?? {}) },
      onUploadProgress: (e) => {
        if (config?.onProgress) {
          const pct = e.total ? Math.round((e.loaded * 100) / e.total) : undefined;
          config.onProgress(pct);
        }
      },
    });
    return res.data as T;
  },
};
