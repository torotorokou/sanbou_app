/**
 * データセット設定セレクタ
 * 
 * UI/VMが使用する取得API。
 * DATASETS レジストリから必要な情報を取り出す関数群。
 */

import { DATASETS } from './datasets';
import type { DatasetKey, CsvTypeKey, DatasetConfig, CsvConfig } from './types';

/**
 * データセット設定を取得（存在しない場合はエラー）
 */
function assertDataset(key: DatasetKey): DatasetConfig {
  const conf = DATASETS[key as keyof typeof DATASETS];
  if (!conf) throw new Error(`Unknown dataset: ${key}`);
  return conf;
}

/**
 * データセット設定を取得
 */
export function getDatasetConfig(key: DatasetKey): DatasetConfig {
  return assertDataset(key);
}

/**
 * データセットの全CSV定義をorder順にソートして取得
 */
export function getCsvListSorted(key: DatasetKey): CsvConfig[] {
  return [...assertDataset(key).csv].sort((a, b) => a.order - b.order);
}

/**
 * 特定のCSV種別の設定を取得
 */
export function findCsv(key: DatasetKey, typeKey: CsvTypeKey): CsvConfig | undefined {
  return assertDataset(key).csv.find((c) => c.typeKey === typeKey);
}

/**
 * ファイル名からCSV種別を推定
 * 正規表現 → ヒント文字列の順で判定
 */
export function guessCsvTypeByFilename(key: DatasetKey, fileName: string): CsvTypeKey | null {
  const name = fileName.toLowerCase();
  for (const c of assertDataset(key).csv) {
    // 正規表現による判定（優先）
    if (c.filenameRegex) {
      try {
        const re = new RegExp(c.filenameRegex, 'i');
        if (re.test(fileName)) return c.typeKey;
      } catch {
        /* invalid regex - ignore */
      }
    }
    // ヒント文字列による部分一致
    if (c.filenameHints?.some((h) => name.includes(h.toLowerCase()))) {
      return c.typeKey;
    }
  }
  return null;
}

/**
 * アップロード設定を取得
 */
export function getUploadEndpoint(key: DatasetKey) {
  return assertDataset(key).upload;
}

/**
 * データセットの必須CSV種別のみを取得
 */
export function getRequiredCsvTypes(key: DatasetKey): CsvTypeKey[] {
  return assertDataset(key)
    .csv.filter((c) => c.required)
    .map((c) => c.typeKey);
}

/**
 * データセットのすべてのCSV種別キーを取得（order順）
 */
export function getCsvTypeKeys(key: DatasetKey): CsvTypeKey[] {
  return getCsvListSorted(key).map((c) => c.typeKey);
}

/**
 * 旧 collectTypesForDataset の互換実装
 * データセットに属するCSV種別のキー配列を返す
 */
export function collectTypesForDataset(key: DatasetKey): string[] {
  return getCsvTypeKeys(key);
}

/**
 * CSV種別のラベルを取得
 */
export function getCsvLabel(key: DatasetKey, typeKey: CsvTypeKey): string {
  const csv = findCsv(key, typeKey);
  return csv?.label ?? typeKey;
}

/**
 * CSV種別の色を取得
 */
export function getCsvColor(key: DatasetKey, typeKey: CsvTypeKey): string | undefined {
  const csv = findCsv(key, typeKey);
  return csv?.color;
}

/**
 * すべてのデータセット定義を配列で取得
 */
export function getAllDatasets(): DatasetConfig[] {
  return Object.values(DATASETS) as DatasetConfig[];
}

/**
 * データセットのラベルを取得
 */
export function getDatasetLabel(key: DatasetKey): string {
  return assertDataset(key).label;
}
