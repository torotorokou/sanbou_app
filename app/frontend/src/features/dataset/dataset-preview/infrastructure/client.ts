/**
 * PreviewClient - HTTP クライアント
 */

import { coreApi } from "@/shared";

export const PreviewClient = {
  async get<T = unknown>(path: string, signal?: AbortSignal): Promise<T> {
    return await coreApi.get<T>(path, { signal });
  },
};
