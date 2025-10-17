/**
 * Shogun Manual API Client
 * 将軍マニュアルのAPI クライアント
 */
import { apiGet } from '@/shared/infrastructure/http';
import type {
  ManualDetail,
  ManualListResponse,
  ManualCatalogResponse,
} from '../model/types';

export const ShogunClient = {
  /**
   * カタログ取得（将軍カテゴリ）
   */
  async catalog(signal?: AbortSignal): Promise<ManualCatalogResponse> {
    return apiGet<ManualCatalogResponse>('/core_api/manual/manuals/catalog', {
      params: { category: 'syogun' },
      signal,
    });
  },

  /**
   * マニュアル一覧取得
   */
  async list(params: {
    query?: string;
    tag?: string;
    category?: string;
    page?: number;
    size?: number;
  } = {}): Promise<ManualListResponse> {
    return apiGet<ManualListResponse>('/core_api/manual/manuals', { params });
  },

  /**
   * マニュアル詳細取得
   */
  async get(id: string): Promise<ManualDetail> {
    return apiGet<ManualDetail>(`/core_api/manual/manuals/${id}`);
  },

  /**
   * マニュアルセクション取得
   */
  async sections(id: string): Promise<ManualDetail['sections']> {
    return apiGet<ManualDetail['sections']>(`/core_api/manual/manuals/${id}/sections`);
  },
};

export default ShogunClient;
