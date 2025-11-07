/**
 * データセット定義とヘルパー関数
 * 
 * 3種類のデータセット:
 * - 将軍_速報版
 * - 将軍_最終版
 * - マニフェスト（1次・2次）
 */

import { UPLOAD_CSV_DEFINITIONS, UPLOAD_CSV_TYPES } from './sampleCsvModel';

export type DatasetKey = 'shogun_flash' | 'shogun_final' | 'manifest';
export type DatasetSpec = { key: DatasetKey; label: string };

export const DATASETS: DatasetSpec[] = [
  { key: 'shogun_flash', label: '将軍_速報版' },
  { key: 'shogun_final', label: '将軍_最終版' },
  { key: 'manifest',     label: 'マニフェスト（1次・2次）' },
];

const norm = (s: string) => String(s).toLowerCase();

const getGroupDecl = (def: { bundle?: string; group?: string; dataset?: string }): string | null =>
  (def?.bundle || def?.group || def?.dataset || null) as string | null;

/**
 * label→dataset 推定（bundle/group/dataset が無い場合のフォールバック）
 */
function isBelongToDatasetByLabel(dataset: DatasetKey, label: string): boolean {
  const l = label.toLowerCase();
  if (dataset === 'shogun_flash') {
    return (l.includes('将軍') || l.includes('shogun')) && 
           (l.includes('速報') || l.includes('flash'));
  }
  if (dataset === 'shogun_final') {
    return (l.includes('将軍') || l.includes('shogun')) && 
           (l.includes('最終') || l.includes('final'));
  }
  if (dataset === 'manifest') {
    return l.includes('マニ') || l.includes('マニフェスト') || l.includes('manifest');
  }
  return false;
}

/**
 * dataset の active typeKeys を収集（定義優先 → ラベル推定）
 */
export function collectTypesForDataset(dataset: DatasetKey): string[] {
  // 1) bundle/group/dataset による判定（優先）
  const byDecl = (UPLOAD_CSV_TYPES as string[]).filter((t) => {
    const def = UPLOAD_CSV_DEFINITIONS[t];
    const g = getGroupDecl(def);
    return g ? norm(g) === dataset : false;
  });

  // 2) label による推定（フォールバック）
  const byLabel = (UPLOAD_CSV_TYPES as string[]).filter((t) => {
    const def = UPLOAD_CSV_DEFINITIONS[t];
    const label = def?.label ?? t;
    return isBelongToDatasetByLabel(dataset, label);
  });

  // 重複を除去
  return Array.from(new Set([...byDecl, ...byLabel]));
}

/**
 * 必須タイプ（dataset単位）
 * active な typeKey の中で required !== false のもの
 */
export function requiredTypesForDataset(dataset: DatasetKey, activeTypes: string[]): string[] {
  return activeTypes.filter((t) => {
    const def = UPLOAD_CSV_DEFINITIONS[t];
    return def?.required !== false;
  });
}

/**
 * カテゴリ順での並べ替え（オプショナル）
 * 将来的に実装する場合のプレースホルダー
 */
export const CATEGORY_ORDER_BY_DATASET: Record<DatasetKey, string[]> = {
  shogun_flash: ['出荷', '受入', 'ヤード'],
  shogun_final: ['出荷', '受入', 'ヤード'],
  manifest: ['1次', '2次'],
};
