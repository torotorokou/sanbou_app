/**
 * データベースアップロード API クライアント
 */

import type { UploadResponseShape } from '../model/types';

export const DatabaseUploadClient = {
  /**
   * FormDataをPOSTする
   */
  async postFormData(
    path: string,
    form: FormData,
    options?: { timeout?: number; signal?: AbortSignal }
  ): Promise<UploadResponseShape> {
    const controller = new AbortController();
    const signal = options?.signal || controller.signal;
    
    let timeoutId: NodeJS.Timeout | undefined;
    if (options?.timeout) {
      timeoutId = setTimeout(() => controller.abort(), options.timeout);
    }

    try {
      const res = await fetch(path, {
        method: 'POST',
        body: form,
        signal,
      });

      if (timeoutId) clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`${path} failed: ${res.status}`);
      }

      return await res.json();
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId);
      throw error;
    }
  },
};
