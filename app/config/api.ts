// API configuration and types

export {}
const globalProcess = (globalThis as unknown as { process?: { env?: Record<string, string | undefined> } })?.process;
const API_BASE = globalProcess?.env?.NEXT_PUBLIC_API_BASE_URL ?? "";
const BLOCK_UNIT_PRICE_BASE = `${API_BASE}/ledger_api/block_unit_price_interactive`;

export interface TransportEntry {
	entry_id: string;
	vendor_code: string;
	vendor_name: string;
	item_name: string;
	detail: string;
	options: string[];
	initial: string | null;
}

export interface StartProcessResponse {
	status: string;
	step: number;
	message: string;
	session_id: string;
	session_expires_in: number;
	data: {
	step: number;
	message: string;
	transport_entries?: TransportEntry[];
		warnings?: string[];
		[key: string]: unknown;
	};
}

export interface ApplyResponse {
	status: string;
	step: number;
	message: string;
	session_id?: string;
	session_expires_in?: number;
	data: {
		selection_summary?: Record<string, unknown>;
		[key: string]: unknown;
	};
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
	selections: Record<string, string>;
	autoFinalize?: boolean;
	action?: string;
}

export async function applyTransportSelection(
	options: ApplyTransportSelectionOptions,
): Promise<ApplyResponse | Response> {
	const { sessionId, selections, autoFinalize = false, action = "select_transport" } = options;
	const response = ensureSuccess(
		await fetch(`${BLOCK_UNIT_PRICE_BASE}/apply`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				session_id: sessionId,
				user_input: {
					action,
					selections,
					auto_finalize: autoFinalize || undefined,
				},
			}),
		}),
	);

	const contentType = response.headers.get("content-type") ?? "";
	if (!autoFinalize && contentType.includes("application/json")) {
		return (await response.json()) as ApplyResponse;
	}
	return response;
}

export interface FinalizeOptions {
	sessionId: string;
	confirmed?: boolean;
}
export async function finalizeBlockUnitPrice({
	sessionId,
	confirmed = true,
}: FinalizeOptions): Promise<Response> {
	const response = ensureSuccess(
		await fetch(`${BLOCK_UNIT_PRICE_BASE}/finalize`, {
	method: "POST",
	headers: { "Content-Type": "application/json" },
	body: JSON.stringify({
				session_id: sessionId,
				confirmed,
			}),
		}),
	);
	return response;
}
