/**
 * Block Unit Price Interactive API Client
 * ブロック単価計算の対話的フロー
 */

import { coreApi } from '@/shared';

// =============================
// Types
// =============================
export interface BlockUnitPriceInitialRequest {
  date?: string;
  factory_id?: string;
}

export interface BlockUnitPriceInitialResponse {
  session_id: string;
  factories: Array<{
    id: string;
    name: string;
  }>;
  [key: string]: unknown;
}

export interface BlockUnitPriceStartRequest {
  session_id: string;
  factory_id: string;
  date: string;
}

export interface BlockUnitPriceStartResponse {
  session_id: string;
  transport_options: Array<{
    id: string;
    name: string;
    price: number;
  }>;
  [key: string]: unknown;
}

export interface SelectTransportRequest {
  session_id: string;
  transport_id: string;
}

export interface SelectTransportResponse {
  session_id: string;
  selected_transport: {
    id: string;
    name: string;
  };
  [key: string]: unknown;
}

export interface ApplyPriceRequest {
  session_id: string;
}

export interface ApplyPriceResponse {
  session_id: string;
  preview: {
    affected_blocks: number;
    total_price: number;
  };
  [key: string]: unknown;
}

export interface FinalizePriceRequest {
  session_id: string;
}

export interface FinalizePriceResponse {
  success: boolean;
  message?: string;
  [key: string]: unknown;
}

// =============================
// API Functions
// =============================

/**
 * セッション初期化
 */
export async function initializeBlockUnitPrice(
  params: BlockUnitPriceInitialRequest = {}
): Promise<BlockUnitPriceInitialResponse> {
  return await coreApi.post<BlockUnitPriceInitialResponse>(
    '/core_api/block_unit_price_interactive/initial',
    params
  );
}

/**
 * セッション開始
 */
export async function startBlockUnitPrice(
  params: BlockUnitPriceStartRequest
): Promise<BlockUnitPriceStartResponse> {
  return await coreApi.post<BlockUnitPriceStartResponse>(
    '/core_api/block_unit_price_interactive/start',
    params
  );
}

/**
 * 運送方法選択
 */
export async function selectTransport(
  params: SelectTransportRequest
): Promise<SelectTransportResponse> {
  return await coreApi.post<SelectTransportResponse>(
    '/core_api/block_unit_price_interactive/select-transport',
    params
  );
}

/**
 * 価格適用プレビュー
 */
export async function applyPrice(params: ApplyPriceRequest): Promise<ApplyPriceResponse> {
  return await coreApi.post<ApplyPriceResponse>(
    '/core_api/block_unit_price_interactive/apply',
    params
  );
}

/**
 * 価格確定
 */
export async function finalizePrice(params: FinalizePriceRequest): Promise<FinalizePriceResponse> {
  return await coreApi.post<FinalizePriceResponse>(
    '/core_api/block_unit_price_interactive/finalize',
    params
  );
}
