/**
 * データベースアップロード機能の型定義
 * - TypeKey: CSV種別の不変ID（UPLOAD_CSV_TYPESの要素）
 * - ValidationStatus: バリデーション状態
 */

export type TypeKey = string;
export type ValidationStatus = 'valid' | 'invalid' | 'unknown';

/**
 * 左パネルに表示するファイルアイテム
 */
export interface PanelFileItem {
  typeKey: TypeKey;
  label: string;
  required: boolean;
  file: File | null;
  status: ValidationStatus;
}

/**
 * CSV定義（種別ごとの設定）
 */
export interface CsvDefinition {
  label: string;
  required?: boolean;
  requiredHeaders?: string[]; // 簡易検証用：必須ヘッダ
  group?: string; // データセット分類（shogun_flash, shogun_final, manifest等）
  bundle?: string; // 旧互換性
  dataset?: string; // 旧互換性
}

/**
 * CSVプレビューデータ
 */
export interface CsvPreview {
  rows: Array<Record<string, string | number | null>>;
  columns: string[];
}

/**
 * アップロード応答の形状
 */
export interface UploadFileIssue {
  filename?: string;
  status?: string;
  detail?: string;
}

export interface UploadResponseShape {
  status?: string;
  detail?: string;
  hint?: string;
  result?: Record<string, UploadFileIssue>;
}
