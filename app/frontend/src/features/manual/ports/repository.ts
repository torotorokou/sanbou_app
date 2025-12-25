/**
 * Manual Repository Interface
 * マニュアル機能のリポジトリインターフェース（DIP）
 */

import type {
  ManualSearchQuery,
  ManualSearchResult,
  ManualTocItem,
  ManualCategory,
} from "../domain/types/manual.types";

export interface ManualRepository {
  /**
   * マニュアルを検索
   */
  search(
    query: ManualSearchQuery,
    signal?: AbortSignal,
  ): Promise<ManualSearchResult>;

  /**
   * ドキュメントURLを取得
   */
  getDocUrl(
    docId: string,
    filename: string,
    query?: Record<string, string>,
  ): string;

  /**
   * マニュアル目次を取得
   */
  toc(signal?: AbortSignal): Promise<ManualTocItem[]>;

  /**
   * カテゴリ一覧を取得
   */
  categories(signal?: AbortSignal): Promise<ManualCategory[]>;
}
