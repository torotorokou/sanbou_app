/**
 * データセット定義とヘルパー関数
 * 
 * @deprecated このファイルは config レジストリに移行済みです。
 * 新規コードでは @features/database/config を直接使用してください。
 * 
 * 3種類のデータセット:
 * - 将軍_速報版
 * - 将軍_最終版
 * - マニフェスト（1次・2次）
 */

import {
  getAllDatasets,
  getCsvTypeKeys,
  getRequiredCsvTypes,
  type DatasetKey,
} from '../../config';

export type { DatasetKey };
export type DatasetSpec = { key: DatasetKey; label: string };

/**
 * @deprecated config/selectors.getAllDatasets() を使用してください
 */
export const DATASETS: DatasetSpec[] = getAllDatasets().map((d) => ({
  key: d.key,
  label: d.label,
}));

/**
 * dataset の active typeKeys を収集（定義優先 → ラベル推定）
 * @deprecated config/selectors.getCsvTypeKeys() を使用してください
 */
export function collectTypesForDataset(dataset: DatasetKey): string[] {
  return getCsvTypeKeys(dataset);
}

/**
 * 必須タイプ（dataset単位）
 * @deprecated config/selectors.getRequiredCsvTypes() を使用してください
 */
export function requiredTypesForDataset(dataset: DatasetKey): string[] {
  return getRequiredCsvTypes(dataset);
}

/**
 * カテゴリ順での並べ替え（オプショナル）
 * @deprecated 順序は config/datasets.ts の order フィールドで管理されています
 */
export const CATEGORY_ORDER_BY_DATASET: Record<DatasetKey, string[]> = {
  shogun_flash: ['受入', '出荷', 'ヤード'],
  shogun_final: ['受入', '出荷', 'ヤード'],
  manifest: ['1次', '2次'],
};
