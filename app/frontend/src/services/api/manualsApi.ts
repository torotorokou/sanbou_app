import axios from 'axios';
import type { ManualDetail, ManualListResponse } from '@/types/manuals';

const baseURL = import.meta.env.VITE_MANUAL_API_BASE_URL || '/manual_api';
const http = axios.create({ baseURL });

export const manualsApi = {
  async list(params: { query?: string; tag?: string; category?: string; page?: number; size?: number } = {}) {
    const res = await http.get<ManualListResponse>(`/api/manuals`, { params });
    return res.data;
  },
  async get(id: string) {
    const res = await http.get<ManualDetail>(`/api/manuals/${id}`);
    return res.data;
  },
  async sections(id: string) {
    const res = await http.get(`/api/manuals/${id}/sections`);
    return res.data as ManualDetail['sections'];
  },
};

export default manualsApi;
