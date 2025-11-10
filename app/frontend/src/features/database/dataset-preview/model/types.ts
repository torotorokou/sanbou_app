/**
 * dataset-preview 型定義
 */

export type DatasetKey = 'shogun_flash' | 'shogun_final' | 'manifest';

export interface CsvPreviewData {
  columns: string[];
  rows: string[][];
}

export type ValidationStatus = 'valid' | 'invalid' | 'unknown';

export type FallbackMode = 'empty' | 'schema' | 'sample';

export type PreviewSource =
  | { kind: 'files'; datasetKey: DatasetKey; files: Record<string, File | null>; fallbackMode?: FallbackMode }
  | { kind: 'uploadId'; datasetKey: DatasetKey; uploadId: string; fallbackMode?: FallbackMode }
  | { kind: 'previews'; datasetKey: DatasetKey; data: Record<string, CsvPreviewData>; fallbackMode?: FallbackMode }
  | { kind: 'fallback'; datasetKey: DatasetKey; mode: FallbackMode };

export type TabDef = {
  key: string;            // typeKey
  label: string;          // タブラベル
  color?: string;
  required?: boolean;
  status?: ValidationStatus;
  preview: CsvPreviewData | null;
  fallbackColumns?: string[]; // CSV未アップロード時のヘッダー定義
};
