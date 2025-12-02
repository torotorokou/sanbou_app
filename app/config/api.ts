// API configuration and types
// 
// ⚠️ DEPRECATION WARNING:
// このファイルは非推奨です。新しいコードでは @shared/config/apiEndpoints を使用してください。
// 
// 移行先:
// - エンドポイント定数: import { REPORT_ENDPOINTS } from '@shared/config/apiEndpoints'
// - HTTPクライアント: import { coreApi } from '@shared/infrastructure/http'
//
// このファイルは後方互換性のためにのみ残されています。
// 段階的に移行を進め、2025年1月以降に削除予定です。

export {}

import { REPORT_ENDPOINTS } from '@/shared/config/apiEndpoints';

const globalProcess = (globalThis as unknown as { process?: { env?: Record<string, string | undefined> } })?.process;
const API_BASE = globalProcess?.env?.NEXT_PUBLIC_API_BASE_URL ?? "";

/**
 * @deprecated 代わりに REPORT_ENDPOINTS.blockUnitPrice を使用してください
 */
const BLOCK_UNIT_PRICE_BASE = REPORT_ENDPOINTS.blockUnitPrice;

export interface TransportCandidateRow {
	entry_id: string;
	vendor_code: number | string;
	vendor_name: string;
	item_name: string;
	detail?: string | null;
	options: string[];
	initial_index: number;
}

export interface StartProcessResponse {
	session_id: string;
	rows: TransportCandidateRow[];
}

export interface ApplyResponse {
	session_id?: string;
	selection_summary?: Record<string, unknown>;
	message?: string;
	step?: number;
}

function ensureSuccess(response: Response): Response {
	if (!response.ok) {
		throw new Error(`API request failed (${response.status}): ${response.statusText}`);
	}
	return response;
}

/**
 * @deprecated 代わりに coreApi.post() を直接使用してください
 */
export async function startBlockUnitPriceProcess(formData: FormData): Promise<StartProcessResponse> {
	const response = ensureSuccess(
		await fetch(`${BLOCK_UNIT_PRICE_BASE}/initial`, {
			method: "POST",
			body: formData,
		}),
	);
	return (await response.json()) as StartProcessResponse;
}

export interface ApplyTransportSelectionOptions {
	sessionId: string;
/**
 * @deprecated 代わりに coreApi.post() を直接使用してください
 */
export async function applyTransportSelection(
	options: ApplyTransportSelectionOptions,
): Promise<ApplyResponse | Response> {
	const { sessionId, selections } = options;
	const response = ensureSuccess(
		await fetch(`${BLOCK_UNIT_PRICE_BASE}/apply`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				session_id: sessionId,
				selections,
			}),
		}),
	);

	const contentType = response.headers.get("content-type") ?? "";
	if (contentType.includes("application/json")) {
		return (await response.json()) as ApplyResponse;
	}
	return response;
}	return (await response.json()) as ApplyResponse;
	}
	return response;
}

export interface FinalizeOptions {
	sessionId: string;
}
/**
 * @deprecated 代わりに coreApi.post() を直接使用してください
 */
export async function finalizeBlockUnitPrice({
	sessionId,
}: FinalizeOptions): Promise<Response> {
	const response = ensureSuccess(
		await fetch(`${BLOCK_UNIT_PRICE_BASE}/finalize`, {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({
				session_id: sessionId,
			}),
		}),
	);
	return response;
}
