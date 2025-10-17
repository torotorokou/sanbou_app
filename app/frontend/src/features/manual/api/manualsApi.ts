import type { ManualDetail, ManualListResponse, ManualCatalogResponse } from '@features/manual/model/manual.types';
import { apiGet } from '@shared/infrastructure/http';

export const manualsApi = {
  async list(params: { query?: string; tag?: string; category?: string; page?: number; size?: number } = {}) {
    const res = await apiGet<ManualListResponse>(`/core_api/manual/manuals`, { params });
    return res;
  },
  async get(id: string) {
    const res = await apiGet<ManualDetail>(`/core_api/manual/manuals/${id}`);
    return res;
  },
  async sections(id: string) {
    const res = await apiGet<ManualDetail['sections']>(`/core_api/manual/manuals/${id}/sections`);
    return res;
  },
  async catalog(params: { category?: string } = {}) {
    const res = await apiGet<ManualCatalogResponse>(`/core_api/manual/manuals/catalog`, { params });
    return res;
  },
};

export default manualsApi;
