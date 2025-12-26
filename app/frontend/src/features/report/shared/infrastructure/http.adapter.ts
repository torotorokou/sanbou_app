/**
 * HTTP Client Adapter
 * @shared の実装を report feature 用に適合させる
 */

import {
  coreApi,
  apiPost as sharedApiPost,
  client as httpClient,
} from "@/shared";
import type { ApiPostFn, ApiGetFn } from "../ports/http";

/**
 * coreApi adapter
 * @features/report 内で使用する統一的なAPI呼び出し関数
 */
export const apiPost: ApiPostFn = async (url, data, config) => {
  return coreApi.post(url, data, config);
};

export const apiGet: ApiGetFn = async (url, config) => {
  return coreApi.get(url, config);
};

/**
 * Legacy apiPost for compatibility
 */
export const legacyApiPost = sharedApiPost;

/**
 * HTTP Client for direct usage
 */
export const client = httpClient;

/**
 * Re-export coreApi for backward compatibility
 */
export { coreApi };
