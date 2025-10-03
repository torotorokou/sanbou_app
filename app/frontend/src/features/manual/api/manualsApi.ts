import type { ManualDetail, ManualListResponse, ManualCatalogResponse } from '@features/manual';
import { apiGet } from '@shared/infrastructure/http';

export const manualsApi = {
  async list(params: { query?: string; tag?: string; category?: string; page?: number; size?: number } = {}) {
    const res = await apiGet<ManualListResponse>(`/manual_api/api/manuals`, { params });
    return res;
  },
  async get(id: string) {
    const res = await apiGet<ManualDetail>(`/manual_api/api/manuals/${id}`);
    return res;
  },
  async sections(id: string) {
    const res = await apiGet<ManualDetail['sections']>(`/manual_api/api/manuals/${id}/sections`);
    return res;
  },
  async catalog(params: { category?: string } = {}) {
    const res = await apiGet<ManualCatalogResponse>(`/manual_api/api/manuals/catalog`, { params });
    return res;
  },
};

export default manualsApi;
