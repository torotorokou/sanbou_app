/**
 * dataset-import 型定義
 *
 * 機能:
 *   - データセットインポート画面の状態管理
 *   - 左パネルのファイル一覧表示
 *   - CSVバリデーション状態の管理
 *   - プレビューデータの保持
 *
 * 設計方針:
 *   - MVVMパターン: ViewModelで使用される型定義
 *   - Feature-Sliced Design: features/database/dataset-import 層
 *   - 他機能との結合度を低く保つ
 */

import type { CsvValidationStatus } from "@features/csv-validation";
import type { TypeKey } from "../../shared/types/common";
import type { CsvPreviewData } from "../../dataset-preview/model/types";

/**
 * 左パネルに表示するファイルアイテム
 *
 * 機能:
 *   - 各CSVファイルの状態を保持
 *   - バリデーション状態の表示
 *   - プレビューデータのキャッシュ
 *   - スキップ機能のサポート
 *
 * @example
 * const fileItem: PanelFileItem = {
 *   typeKey: 'receive',
 *   label: '受入一覧',
 *   required: true,
 *   file: new File(['...'], 'receive.csv'),
 *   status: 'valid',
 *   preview: { headers: [...], rows: [...] },
 *   skipped: false
 * };
 */
export interface PanelFileItem {
  /** CSVタイプキー（'receive', 'yard', 'shipment'等） */
  typeKey: TypeKey;
  /** 表示用ラベル（例: '受入一覧'） */
  label: string;
  /** 必須ファイルかどうか（trueの場合はスキップ不可） */
  required: boolean;
  /** アップロードされたファイル（未選択時はnull） */
  file: File | null;
  /** バリデーション状態（'idle', 'validating', 'valid', 'error'） */
  status: CsvValidationStatus;
  /** プレビューデータ（バリデーション成功時に設定） */
  preview: CsvPreviewData | null;
  /** アップロードをスキップするか（チェックマークでスキップ指定） */
  skipped: boolean;
}

/**
 * データセットインポートViewModel用のオプション
 *
 * ViewModeの初期化時に渡す設定。
 *
 * @example
 * const options: DatasetImportVMOptions = {
 *   activeTypes: ['receive', 'yard', 'shipment'],
 *   datasetKey: 'shogun',
 *   onUploadComplete: () => {
 *     notification.success({ message: 'アップロード完了' });
 *     navigate('/database/records');
 *   }
 * };
 */
export interface DatasetImportVMOptions {
  /** 有効なCSVタイプのリスト（省略時は全タイプ） */
  activeTypes?: string[];
  /** データセットキー（例: 'shogun', 'ledger'） */
  datasetKey?: string;
  /** アップロード完了時のコールバック（遷移処理等を実装） */
  onUploadComplete?: () => void;
}
