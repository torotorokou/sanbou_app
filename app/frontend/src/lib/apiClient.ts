// src/lib/apiClient.ts
import axios, { type AxiosRequestConfig } from 'axios';
import type { ApiResponse } from '@/types/api';

function isObject(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null;
}

function isApiEnvelope<T = unknown>(value: unknown): value is ApiResponse<T> {
    return isObject(value) && 'status' in value;
}

const client = axios.create({ withCredentials: true });

// GET
export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.get(url, config);
    const d = res.data as unknown;
    if (isApiEnvelope<T>(d)) {
        const r = d as ApiResponse<T>;
        if ('result' in r) {
            if (r.status === 'success') return (r.result ?? null) as T;
            throw Object.assign(new Error(r?.detail ?? 'Unknown error'), {
                code: r?.code ?? 'UNKNOWN',
                hint: r?.hint ?? null,
                httpStatus: res.status,
            });
        }
        // "result" が無い場合はそのまま返す（既存APIの生形状を許容）
        return d as unknown as T;
    }
    return d as unknown as T;
}

// POST
export async function apiPost<T, B = unknown>(
    url: string,
    body?: B,
    config?: AxiosRequestConfig
): Promise<T> {
    const res = await client.post(url, body, config);
    const d = res.data as unknown;
    if (isApiEnvelope<T>(d)) {
        const r = d as ApiResponse<T>;
        if ('result' in r) {
            if (r.status === 'success') return (r.result ?? null) as T;
            throw Object.assign(new Error(r?.detail ?? 'Unknown error'), {
                code: r?.code ?? 'UNKNOWN',
                hint: r?.hint ?? null,
                httpStatus: res.status,
            });
        }
        return d as unknown as T;
    }
    return d as unknown as T;
}

// Blob系（ファイルダウンロードなど）
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
