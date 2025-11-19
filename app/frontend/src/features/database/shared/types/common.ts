/**
 * 共通型定義
 * データベース機能全体で共有する基本的な型
 */

export type TypeKey = string;
export type ValidationStatus = 'valid' | 'invalid' | 'unknown';

/**
 * CSV定義（種別ごとの設定）
 */
export interface CsvDefinition {
  label: string;
  required?: boolean;
  requiredHeaders?: string[];
  group?: string;
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
  result?: Record<string, UploadFileIssue> | {
    upload_file_ids?: Record<string, number>;
    status?: string;
  };
}
