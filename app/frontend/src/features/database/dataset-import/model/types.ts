/**
 * dataset-import 型定義
 */

import type { CsvValidationStatus } from '@features/csv-validation';
import type { TypeKey } from '../../shared/types/common';
import type { CsvPreviewData } from '../../dataset-preview/model/types';

/**
 * 左パネルに表示するファイルアイテム
 */
export interface PanelFileItem {
  typeKey: TypeKey;
  label: string;
  required: boolean;
  file: File | null;
  status: CsvValidationStatus;
  preview: CsvPreviewData | null;
  /** アップロードをスキップするか（チェックマークでスキップ指定） */
  skipped: boolean;
}

/**
 * データセットインポートVM用のオプション
 */
export interface DatasetImportVMOptions {
  activeTypes?: string[];
  datasetKey?: string;
  onUploadComplete?: () => void; // アップロード完了時のコールバック
}
