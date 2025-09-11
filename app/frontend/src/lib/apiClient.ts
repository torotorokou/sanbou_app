// src/lib/apiClient.ts
import axios, { type AxiosRequestConfig } from 'axios';
import type { ApiResponse } from '@/types/api';

const client = axios.create({
    baseURL: '/rag_api', // Viteのproxyに合わせる（環境により調整）
    withCredentials: true,
});

// GET
export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const res = await client.get<ApiResponse<T>>(url, config);
    const d = res.data;
    if (d?.status === 'success') return (d.result ?? null) as T;
    throw Object.assign(new Error(d?.detail ?? 'Unknown error'), {
        code: d?.code ?? 'UNKNOWN',
        hint: d?.hint ?? null,
        httpStatus: res.status,
    });
}

// POST
export async function apiPost<T, B = unknown>(
    url: string,
    body?: B,
    config?: AxiosRequestConfig
): Promise<T> {
    const res = await client.post<ApiResponse<T>>(url, body, config);
    const d = res.data;
    if (d?.status === 'success') return (d.result ?? null) as T;
    throw Object.assign(new Error(d?.detail ?? 'Unknown error'), {
        code: d?.code ?? 'UNKNOWN',
        hint: d?.hint ?? null,
        httpStatus: res.status,
    });
}
