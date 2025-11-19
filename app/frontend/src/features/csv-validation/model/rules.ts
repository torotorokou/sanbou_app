/**
 * バリデーションルール定義
 * 
 * @deprecated このファイルの必須CSV定義は config/datasets.ts に移行済みです。
 * 新規コードでは config を直接使用してください。
 */

import { DATASETS } from '../../config';

export interface ValidationRule {
  field: string;
  required?: boolean;
  pattern?: RegExp;
  minLength?: number;
  maxLength?: number;
}

export const VALIDATION_RULES: Record<string, ValidationRule[]> = {
  // 将来的な拡張用
  // shogun_flash_ship: [
  //   { field: '伝票日付', required: true },
  //   { field: '荷主', required: true },
  // ],
};

/**
 * データセット別の必須CSV定義（UploadGuide 用）
 * @deprecated config/datasets.ts を使用してください
 */
export interface RequiredCsvSpec {
  typeKey: string;
  label: string;
  required: boolean;
  headers?: string[];
  filenameHints?: string[];
  sampleUrl?: string;
}

export interface DatasetRule {
  datasetKey: string;
  requiredCsv: RequiredCsvSpec[];
  globalNotes?: string[];
}

/**
 * config から DatasetRule を生成（互換性のため）
 * @deprecated config/datasets.ts を直接使用してください
 */
export const DATASET_RULES: Record<string, DatasetRule> = (() => {
  const result: Record<string, DatasetRule> = {};
  for (const dataset of Object.values(DATASETS)) {
    result[dataset.key] = {
      datasetKey: dataset.key,
      globalNotes: dataset.notes,
      requiredCsv: dataset.csv.map((csv) => ({
        typeKey: csv.typeKey,
        label: csv.label,
        required: csv.required,
        headers: csv.validate.requiredHeaders,
        filenameHints: csv.filenameHints,
      })),
    };
  }
  return result;
})();
