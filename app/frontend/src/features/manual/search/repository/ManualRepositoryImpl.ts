/**
 * Manual Repository Implementation
 * ManualClientを使用した実装
 */

import type { ManualRepository } from './ManualRepository';
import { ManualClient } from '../../shared/manualClient';
import type { ManualSearchQuery, ManualSearchResult, ManualTocItem, ManualCategory } from '../../shared/model/types';

export class ManualRepositoryImpl implements ManualRepository {
  async search(query: ManualSearchQuery, signal?: AbortSignal): Promise<ManualSearchResult> {
    const raw = await ManualClient.search(query, signal);
    // API レスポンスを Domain モデルに変換
    // 必要に応じてDTO→Domainの変換ロジックをここに実装
    return raw as ManualSearchResult;
  }

  getDocUrl(docId: string, filename: string, query?: Record<string, string>): string {
    return ManualClient.docUrl(docId, filename, query);
  }

  async toc(signal?: AbortSignal): Promise<ManualTocItem[]> {
    const raw = await ManualClient.toc(signal);
    // API形状に応じて調整
    if (Array.isArray(raw)) {
      return raw as ManualTocItem[];
    }
    // オブジェクト形式の場合
    const result = raw as { items?: ManualTocItem[]; data?: ManualTocItem[] };
    return result.items ?? result.data ?? [];
  }

  async categories(signal?: AbortSignal): Promise<ManualCategory[]> {
    const raw = await ManualClient.categories(signal);
    // API形状に応じて調整
    if (Array.isArray(raw)) {
      return raw as ManualCategory[];
    }
    // オブジェクト形式の場合
    const result = raw as { items?: ManualCategory[]; data?: ManualCategory[] };
    return result.items ?? result.data ?? [];
  }
}
