/**
 * header/model/useHeaderVM.ts
 * ヘッダー機能のViewModel(CSV出力管理)
 *
 * 【概要】
 * ヘッダー部分のビジネスロジックを管理するViewModel
 * MVVM パターンの ViewModel 層として、View(SalesPivotHeader)とModel(Repository)を橋渡し
 *
 * 【責務】
 * 1. CSV出力オプションの状態管理
 * 2. localStorage への永続化
 * 3. CSV出力処理の実行
 *
 * 【使用例】
 * ```typescript
 * const { exportOptions, setExportOptions, handleExport, canExport } = useHeaderViewModel({
 *   repository: salesPivotRepository,
 *   query: summaryQuery,
 *   repIds: ['rep_a', 'rep_b'],
 *   periodLabel: '202511'
 * });
 *
 * // CSV出力
 * const blob = await handleExport();
 * // ... ファイルダウンロード処理
 * ```
 */

import { useState, useEffect, useCallback } from 'react';
import type { ExportOptions, SummaryQuery, ID } from '../../shared/model/types';
import { DEFAULT_EXPORT_OPTIONS } from '../../shared/model/types';
import type { SalesPivotRepository } from '../../shared/infrastructure/salesPivot.repository';

/**
 * ヘッダーViewModel入力パラメータ
 *
 * @property repository - データアクセス用Repository
 * @property query - サマリクエリ（CSV出力条件のベース）
 * @property repIds - 対象営業ID配列
 * @property periodLabel - 期間ラベル（表示用、CSV出力には影響しない）
 */
export interface UseHeaderViewModelParams {
  repository: SalesPivotRepository;
  query: SummaryQuery;
  repIds: ID[];
  periodLabel: string;
}

/**
 * ヘッダーViewModel出力
 *
 * @property exportOptions - 現在のCSV出力オプション
 * @property setExportOptions - 出力オプション更新関数
 * @property handleExport - CSV出力実行関数
 * @property canExport - 出力可能かどうか（営業が選択されているか）
 */
export interface UseHeaderViewModelResult {
  exportOptions: ExportOptions;
  setExportOptions: (options: ExportOptions | ((prev: ExportOptions) => ExportOptions)) => void;
  handleExport: () => Promise<Blob>;
  canExport: boolean;
}

/**
 * ヘッダーViewModel Hook
 *
 * @param params - ViewModel入力パラメータ
 * @returns ViewModel出力（状態と操作関数）
 *
 * @description
 * - Export options の状態管理とlocalStorage永続化
 * - CSV出力処理の実行
 */
export function useHeaderViewModel(params: UseHeaderViewModelParams): UseHeaderViewModelResult {
  const { repository, query, repIds } = params;

  // ========================================
  // Export options（localStorage永続化）
  // ========================================

  /**
   * CSV出力オプション状態
   *
   * 初期化時にlocalStorageから復元を試みる
   * 復元失敗時（初回起動 or JSONパースエラー）はデフォルト値を使用
   */
  const [exportOptions, setExportOptions] = useState<ExportOptions>(() => {
    try {
      const raw = localStorage.getItem('exportOptions_v1');
      return raw ? (JSON.parse(raw) as ExportOptions) : DEFAULT_EXPORT_OPTIONS;
    } catch {
      // JSON パースエラー時もデフォルト値で継続
      return DEFAULT_EXPORT_OPTIONS;
    }
  });

  /**
   * Export options が変更されたら localStorage に永続化
   *
   * ユーザーの設定を次回起動時にも引き継ぐ
   */
  useEffect(() => {
    localStorage.setItem('exportOptions_v1', JSON.stringify(exportOptions));
  }, [exportOptions]);

  // ========================================
  // CSV出力処理
  // ========================================

  /**
   * CSV出力実行
   *
   * @returns CSV形式のBlob（ファイルダウンロード用）
   *
   * @description
   * Repository に ExportQuery を渡してCSVデータを取得
   * 実際のファイルダウンロードはView側（SalesPivotHeader）で実行
   */
  const handleExport = useCallback(async (): Promise<Blob> => {
    const blob = await repository.exportModeCube({
      ...query,
      options: exportOptions,
      targetRepIds: repIds,
    });
    return blob;
  }, [repository, query, exportOptions, repIds]);

  /**
   * 出力可能かどうか
   *
   * 営業が1人以上選択されている場合のみ true
   * View側でボタンの disabled 制御に使用
   */
  const canExport = repIds.length > 0;

  return {
    exportOptions,
    setExportOptions,
    handleExport,
    canExport,
  };
}
