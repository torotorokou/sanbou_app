// shared/infrastructure/http/httpClient.ts
// Central HTTP client implementation with axios + ProblemDetails support

import axios, { type AxiosRequestConfig, type AxiosError } from 'axios';
import type { ApiResponse } from '@shared/types';
import type { ProblemDetails } from '@features/notification/domain/types/contract';
import { message } from 'antd';

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

/**
 * エラー通知の重複排除用キャッシュ
 * 同じエラーを短時間に複数回通知しないようにする
 */
const recentErrorNotifications = new Map<string, number>();
const ERROR_NOTIFICATION_COOLDOWN = 3000; // 3秒間は同じエラーを通知しない

/**
 * コンソールログの重複排除用キャッシュ
 */
const recentConsoleErrors = new Map<string, number>();
const CONSOLE_ERROR_COOLDOWN = 1000; // 1秒間は同じエラーをコンソールに出力しない

/**
 * エラーを通知すべきかチェック（重複排除）
 */
function shouldNotifyError(status: number, message: string): boolean {
    const key = `${status}:${message}`;
    const now = Date.now();
    const lastNotification = recentErrorNotifications.get(key);
    
    if (lastNotification && now - lastNotification < ERROR_NOTIFICATION_COOLDOWN) {
        return false; // クールダウン期間中は通知しない
    }
    
    recentErrorNotifications.set(key, now);
    
    // 古いエントリをクリーンアップ（メモリリーク防止）
    if (recentErrorNotifications.size > 50) {
        const threshold = now - ERROR_NOTIFICATION_COOLDOWN;
        for (const [k, timestamp] of recentErrorNotifications.entries()) {
            if (timestamp < threshold) {
                recentErrorNotifications.delete(k);
            }
        }
    }
    
    return true;
}

/**
 * コンソールエラーを出力すべきかチェック（重複排除）
 */
function shouldLogConsoleError(status: number, url: string): boolean {
    const key = `${status}:${url}`;
    const now = Date.now();
    const lastLog = recentConsoleErrors.get(key);
    
    if (lastLog && now - lastLog < CONSOLE_ERROR_COOLDOWN) {
        return false; // クールダウン期間中はログを出力しない
    }
    
    recentConsoleErrors.set(key, now);
    
    // 古いエントリをクリーンアップ
    if (recentConsoleErrors.size > 100) {
        const threshold = now - CONSOLE_ERROR_COOLDOWN;
        for (const [k, timestamp] of recentConsoleErrors.entries()) {
            if (timestamp < threshold) {
                recentConsoleErrors.delete(k);
            }
        }
    }
    
    return true;
}

// レスポンスインターセプター: エラーを ApiError に変換 + グローバルエラー通知
client.interceptors.response.use(
    (response) => response,
    (error: unknown) => {
        // リクエストキャンセルの場合はエラー通知を表示しない
        if (axios.isCancel(error) || (typeof error === 'object' && error !== null && 'code' in error && error.code === 'ERR_CANCELED')) {
            throw error;
        }
        
        const axiosError = error as AxiosError;
        const apiError = ApiError.fromAxiosError(axiosError);
        const url = axiosError.config?.url || 'unknown';
        
        // コンソールエラーの重複排除（開発用）
        if (shouldLogConsoleError(apiError.status, url)) {
            console.error(`API Error [${apiError.status}] ${url}:`, apiError.userMessage);
        }
        
        // プロダクション環境でグローバルエラー通知を表示
        // 500系エラーと401/403認証エラーのみ通知（400系は各コンポーネントで処理）
        if (apiError.status >= 500 || apiError.status === 401 || apiError.status === 403) {
            const errorMessage = 
                apiError.status === 401 ? '認証エラー: ログインしてください' :
                apiError.status === 403 ? 'アクセス権限がありません' :
                apiError.status >= 500 ? `サーバーエラー: ${apiError.userMessage}` :
                apiError.userMessage;
            
            // 重複排除: 同じエラーを短時間に複数回通知しない
            if (shouldNotifyError(apiError.status, errorMessage)) {
                message.error(errorMessage, 5); // 5秒間表示
            }
        }
        
        throw apiError;
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
        // キャンセルエラーはそのまま throw（通知を表示しない）
        if (axios.isCancel(error) || (error as AxiosError).code === 'ERR_CANCELED') {
            throw error;
        }
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
        // キャンセルエラーはそのまま throw（通知を表示しない）
        if (axios.isCancel(error) || (error as AxiosError).code === 'ERR_CANCELED') {
            throw error;
        }
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
