/**
 * dataset-import モジュールの型定義
 */

import type { ValidationStatus, TypeKey } from '../../shared/types/common';
import type { CsvPreviewData } from '../../dataset-preview/model/types';

/**
 * 左パネルに表示するファイルアイテム
 */
export interface PanelFileItem {
  typeKey: TypeKey;
  label: string;
  required: boolean;
  file: File | null;
  status: ValidationStatus;
  preview: CsvPreviewData | null;
}

/**
 * データセットインポートVM用のオプション
 */
export interface DatasetImportVMOptions {
  activeTypes?: string[];
}
