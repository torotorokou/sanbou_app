/**
 * Customer Churn Repository Port
 *
 * 顧客離脱分析のためのRepository抽象インターフェース
 * FSD + Repository パターンに準拠
 */

import type { LostCustomer, CustomerChurnAnalyzeParams, SalesRep } from '../domain/types';

/**
 * 顧客離脱分析Repository
 */
export interface CustomerChurnRepository {
  /**
   * 営業担当者リストを取得
   *
   * @returns 営業担当者のリスト
   */
  getSalesReps(): Promise<SalesRep[]>;

  /**
   * 顧客離脱分析を実行
   *
   * @param params - 分析パラメータ（今期間・前期間の日付範囲）
   * @returns 離脱顧客のリスト
   */
  analyze(params: CustomerChurnAnalyzeParams): Promise<LostCustomer[]>;
}
