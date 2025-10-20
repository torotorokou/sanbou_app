/**
 * 受入量 - 共通HTTPクライアント
 * Repository層から使用する汎用fetch wrapper
 */

export class HttpError extends Error {
  constructor(
    public url: string,
    public status: number,
    public statusText: string,
    message?: string
  ) {
    super(message || `HTTP ${status}: ${url}`);
    this.name = "HttpError";
  }
}

export const http = {
  /**
   * GET リクエスト
   * @param url - リクエストURL
   * @param signal - AbortSignal for cancellation
   * @returns Promise<T>
   * @throws HttpError
   */
  async get<T>(url: string, signal?: AbortSignal): Promise<T> {
    const res = await fetch(url, { 
      method: "GET",
      signal, 
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    if (!res.ok) {
      throw new HttpError(url, res.status, res.statusText);
    }
    
    return res.json() as Promise<T>;
  },

  /**
   * POST リクエスト
   * @param url - リクエストURL
   * @param body - リクエストボディ
   * @param signal - AbortSignal for cancellation
   * @returns Promise<T>
   * @throws HttpError
   */
  async post<T>(url: string, body?: unknown, signal?: AbortSignal): Promise<T> {
    const res = await fetch(url, {
      method: "POST",
      signal,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      throw new HttpError(url, res.status, res.statusText);
    }

    return res.json() as Promise<T>;
  },
};
