/**
 * Shogun Manual API Client
 * 将軍マニュアルのAPI クライアント
 */
import { apiGet } from '@/shared/infrastructure/http';
import type { ManualCatalogResponse } from '@/features/manual/model/manual.types';

export const ShogunClient = {
  async catalog(signal?: AbortSignal): Promise<ManualCatalogResponse> {
    return apiGet<ManualCatalogResponse>('/core_api/manual/manuals/catalog', {
      params: { category: 'syogun' },
      signal,
    });
  },
};
