// shared/infrastructure/http/httpClient.ts
// Central HTTP client implementation with axios + ProblemDetails support

import axios, { type AxiosRequestConfig, type AxiosError } from 'axios';
import type { ApiResponse } from '@shared/types';
import type { ProblemDetails } from '@features/notification/model/contract';

/**
 * ApiError クラス（RFC 7807 ProblemDetails 準拠）
 * 
 * HTTPエラーレスポンスをアプリケーション層のエラーに変換
 */
export class ApiError extends Error {
    code: string;
    status: number;
    userMessage: string;
    title?: string;
    traceId?: string;

    constructor(
        code: string,
        status: number,
        userMessage: string,
        title?: string,
        traceId?: string
    ) {
        super(userMessage);
        this.name = 'ApiError';
        this.code = code;
        this.status = status;
        this.userMessage = userMessage;
        this.title = title;
        this.traceId = traceId;
    }

    /**
     * ProblemDetails から ApiError を生成
     */
    static fromProblemDetails(pd: ProblemDetails): ApiError {
        return new ApiError(
            pd.code,
            pd.status,
            pd.userMessage,
            pd.title,
            pd.traceId
        );
    }

    /**
     * AxiosError から ApiError を生成
     */
    static fromAxiosError(error: AxiosError): ApiError {
        // レスポンスボディが ProblemDetails の場合
        const data = error.response?.data;
        if (data && typeof data === 'object' && 'code' in data && 'userMessage' in data) {
            const pd = data as ProblemDetails;
            return ApiError.fromProblemDetails(pd);
        }

        // それ以外の場合
        const status = error.response?.status ?? 500;
        const code = error.code === 'ECONNABORTED' ? 'TIMEOUT' : 'INTERNAL_ERROR';
        const userMessage = error.message || '処理に失敗しました';

        return new ApiError(code, status, userMessage);
    }
}

function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null;
}

function isApiEnvelope<T = unknown>(value: unknown): value is ApiResponse<T> {
    return isObject(value) && 'status' in value;
}

const client = axios.create({ 
    withCredentials: true,
    timeout: 60000, // 60秒タイムアウト
});

// レスポンスインターセプター: エラーを ApiError に変換
client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        throw ApiError.fromAxiosError(error);
    }
);

/**
 * タイムアウト付きfetch（レガシー互換用）
 * 
 * @deprecated axios を使用してください
 */
export async function fetchWithTimeout(
    url: string,
    init?: RequestInit,
    timeoutMs = 60000
): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            ...init,
            signal: controller.signal,
        });

        if (!response.ok) {
            // ProblemDetails として解析
            try {
                const pd = await response.json() as ProblemDetails;
                throw ApiError.fromProblemDetails(pd);
            } catch (e) {
                // JSON解析に失敗した場合
                if (e instanceof ApiError) throw e;
                throw new ApiError(
                    'INTERNAL_ERROR',
                    response.status,
                    `HTTP ${response.status}: ${response.statusText}`
                );
            }
        }

        return response;
    } catch (error) {
        if ((error as Error).name === 'AbortError') {
            throw new ApiError('TIMEOUT', 408, 'リクエストがタイムアウトしました');
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

// GET
export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
        const res = await client.get(url, config);
        const d = res.data as unknown;
        if (isApiEnvelope<T>(d)) {
            const r = d as ApiResponse<T>;
            if ('result' in r) {
                if (r.status === 'success') return (r.result ?? null) as T;
                throw new ApiError(
                    r?.code ?? 'UNKNOWN',
                    res.status,
                    r?.detail ?? 'Unknown error',
                    r?.hint ?? undefined,
                    (r as { traceId?: string })?.traceId
                );
            }
            return d as unknown as T;
        }
        return d as unknown as T;
    } catch (error) {
        // ApiError はそのまま throw
        if (error instanceof ApiError) throw error;
        // その他のエラーは変換
        if (axios.isAxiosError(error)) {
            throw ApiError.fromAxiosError(error);
        }
        throw error;
    }
}

// POST
export async function apiPost<T, B = unknown>(
    url: string,
    body?: B,
    config?: AxiosRequestConfig
): Promise<T> {
    try {
        const res = await client.post(url, body, config);
        const d = res.data as unknown;
        if (isApiEnvelope<T>(d)) {
            const r = d as ApiResponse<T>;
            if ('result' in r) {
                if (r.status === 'success') return (r.result ?? null) as T;
                throw new ApiError(
                    r?.code ?? 'UNKNOWN',
                    res.status,
                    r?.detail ?? 'Unknown error',
                    r?.hint ?? undefined,
                    (r as { traceId?: string })?.traceId
                );
            }
            return d as unknown as T;
        }
        return d as unknown as T;
    } catch (error) {
        // ApiError はそのまま throw
        if (error instanceof ApiError) throw error;
        // その他のエラーは変換
        if (axios.isAxiosError(error)) {
            throw ApiError.fromAxiosError(error);
        }
        throw error;
    }
}

// Blob系(ファイルダウンロードなど)
export async function apiGetBlob(url: string, config?: AxiosRequestConfig): Promise<Blob> {
    const res = await client.get(url, { ...config, responseType: 'blob' });
    return res.data as Blob;
}

export async function apiPostBlob<B = unknown>(
    url: string,
    body?: B,
    config?: AxiosRequestConfig
): Promise<Blob> {
    const res = await client.post(url, body, { ...config, responseType: 'blob' });
    return res.data as Blob;
}

// ========================================
// coreApi: 唯一のHTTPクライアント（BFF統一）
// ========================================

export type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface HttpOptions {
    method?: Method;
    body?: unknown;
    headers?: Record<string, string>;
    signal?: AbortSignal;
    timeoutMs?: number;
}

async function coreRequest<T>(path: string, opts: HttpOptions = {}): Promise<T> {
    const controller = new AbortController();
    const timeoutMs = opts.timeoutMs ?? 15000;
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
        // パスの正規化: 必ず先頭/付きにする
        const normalizedPath = path.startsWith("/") ? path : `/${path}`;
        
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
            ...(opts.headers ?? {}),
        };
        
        const res = await fetch(normalizedPath, {
            method: opts.method ?? "GET",
            headers,
            body: opts.body ? JSON.stringify(opts.body) : undefined,
            signal: opts.signal ?? controller.signal,
            redirect: "manual", // 認証リダイレクト等の誤受信検出
        });

        // Content-Type チェック（HTML受信を早期検出）
        const contentType = res.headers.get("content-type") ?? "";
        if (!contentType.includes("application/json")) {
            const text = await res.text().catch(() => "");
            throw new Error(
                `Unexpected payload (content-type=${contentType}): ${text.slice(0, 200)}`
            );
        }

        if (!res.ok) {
            const text = await res.text().catch(() => "");
            throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
        }

        return (await res.json()) as T;
    } finally {
        clearTimeout(timer);
    }
}

/**
 * coreApi: フロントエンドの唯一のHTTPクライアント
 * すべてのAPI呼び出しは /core_api/... で始まる相対パスを使用
 */
export const coreApi = {
    get: <T>(p: string, o?: Omit<HttpOptions, "method" | "body">) =>
        coreRequest<T>(p, { ...o, method: "GET" }),
    post: <T>(p: string, body?: unknown, o?: Omit<HttpOptions, "method">) =>
        coreRequest<T>(p, { ...o, method: "POST", body }),
    put: <T>(p: string, body?: unknown, o?: Omit<HttpOptions, "method">) =>
        coreRequest<T>(p, { ...o, method: "PUT", body }),
    patch: <T>(p: string, body?: unknown, o?: Omit<HttpOptions, "method">) =>
        coreRequest<T>(p, { ...o, method: "PATCH", body }),
    delete: <T>(p: string, o?: Omit<HttpOptions, "method" | "body">) =>
        coreRequest<T>(p, { ...o, method: "DELETE" }),
};
