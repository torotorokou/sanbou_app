/**
 * dataset-import モジュールの型定義
 */

import type { ValidationStatus, TypeKey } from '../../shared/types/common';

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
 * データセットインポートVM用のオプション
 */
export interface DatasetImportVMOptions {
  activeTypes?: string[];
}
