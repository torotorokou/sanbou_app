// shared/infrastructure/http/httpClient.ts
// Central HTTP client implementation with axios + ProblemDetails support

import axios, { type AxiosRequestConfig, type AxiosError } from 'axios';
import type { ApiResponse } from '@shared/types';
import type { ProblemDetails } from '@features/notification/domain/types/contract';

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
        if (data && typeof data === 'object' && 'code' in data) {
            // Backend レスポンス形式: {status: 'error', code: 'XXX', detail: 'message'}
            // または ProblemDetails 形式: {code: 'XXX', userMessage: 'message', status: 409}
            const pd = data as Record<string, unknown>;
            const userMessage = (pd.userMessage as string) || (pd.detail as string) || '処理に失敗しました';
            const status = pd.status || error.response?.status || 500;
            return new ApiError(
                pd.code as string,
                typeof status === 'number' ? status : error.response?.status || 500,
                userMessage,
                pd.title as string | undefined,
                pd.traceId as string | undefined
            );
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

export const client = axios.create({ 
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
