// src/shared/infrastructure/http/index.ts
// HTTP通信のエクスポート

// 🆕 推奨: coreApi統一クライアント（すべての通信は /core_api/... 経由）
export { coreApi } from "./coreApi";

// axios ベース（互換性のため残す）
export {
  apiGet,
  apiPost,
  apiGetBlob,
  apiPostBlob,
  fetchWithTimeout,
  ApiError,
  client,
} from "./httpClient";
