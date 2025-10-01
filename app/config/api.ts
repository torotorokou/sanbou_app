// API configuration and types

export {}
const globalProcess = (globalThis as unknown as { process?: { env?: Record<string, string | undefined> } })?.process;
const API_BASE = globalProcess?.env?.NEXT_PUBLIC_API_BASE_URL ?? "";
const BLOCK_UNIT_PRICE_BASE = `${API_BASE}/ledger_api/block_unit_price_interactive`;

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
	selections: Record<string, number | string>;
}

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
}

export interface FinalizeOptions {
	sessionId: string;
}
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
