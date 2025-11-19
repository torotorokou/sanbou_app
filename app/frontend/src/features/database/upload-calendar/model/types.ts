/**
 * アップロードカレンダー - 型定義
 */

/**
 * CSV種別（アップロード対象の種類）
 */
export type CsvUploadKind =
  | 'shogun_flash_receive'   // 将軍_速報版: 受入
  | 'shogun_flash_shipment'  // 将軍_速報版: 出荷
  | 'shogun_flash_yard'      // 将軍_速報版: ヤード
  | 'shogun_final_receive'   // 将軍_最終版: 受入
  | 'shogun_final_shipment'  // 将軍_最終版: 出荷
  | 'shogun_final_yard'      // 将軍_最終版: ヤード
  | 'manifest_stage1'        // マニフェスト: 1次
  | 'manifest_stage2';       // マニフェスト: 2次

/**
 * アップロードカレンダーのアイテム（1つのアップロード記録）
 */
export interface UploadCalendarItem {
  id: string;
  uploadFileId?: number; // log.upload_file.id（削除時に使用）
  date: string;      // 'YYYY-MM-DD'
  kind: CsvUploadKind;
  rowCount: number;  // データ数（行数）
  deleted: boolean;  // is_deleted のフロント側表現
}

/**
 * カレンダー上の1日分のデータ
 */
export interface CalendarDay {
  date: string; // 'YYYY-MM-DD'
  isCurrentMonth: boolean; // 表示中の月に含まれるかどうか
  uploadsByKind: Partial<Record<CsvUploadKind, UploadCalendarItem[]>>;
}

/**
 * カレンダー上の1週間分のデータ
 */
export interface CalendarWeek {
  days: CalendarDay[];
}

/**
 * CSV種別マスタ（ラベルと色クラスの定義）
 */
export interface CsvUploadKindMaster {
  kind: CsvUploadKind;
  label: string;
  color: string; // Ant Design の color プロパティ（success, processing, error, warning, default など）
  category: string; // カテゴリ（グループ化用）
}

/**
 * CSV種別マスタデータ
 */
export const CSV_UPLOAD_KIND_MASTER: CsvUploadKindMaster[] = [
  // 将軍速報版（緑系） - 種別ごとに明確に差をつける
  { kind: 'shogun_flash_receive',  label: '将軍速報版 受入',  color: '#16a34a', category: '将軍速報版' }, // 緑 (はっきり)
  { kind: 'shogun_flash_shipment', label: '将軍速報版 出荷',  color: '#a50e84ff', category: '将軍速報版' }, // ティール（緑と被らない）
  { kind: 'shogun_flash_yard',     label: '将軍速報版 ヤード', color: '#d4e635ff', category: '将軍速報版' }, // ライム（明るく識別しやすい）

  // 将軍最終版
  { kind: 'shogun_final_receive',  label: '将軍最終版 受入',  color: '#6b21a8', category: '将軍最終版' }, // 濃い紫
  { kind: 'shogun_final_shipment', label: '将軍最終版 出荷',  color: '#db2777', category: '将軍最終版' }, // マゼンタ（紫と被らない）
  { kind: 'shogun_final_yard',     label: '将軍最終版 ヤード', color: '#4338ca', category: '将軍最終版' }, // インディゴ（コントラスト良し）

  // マニフェスト
  { kind: 'manifest_stage1',       label: 'マニフェスト 1次', color: '#08d464ff', category: 'マニフェスト' }, // 濃いオレンジ
  { kind: 'manifest_stage2',       label: 'マニフェスト 2次', color: '#f97316', category: 'マニフェスト' }, // 明るめのオレンジ（識別しやすく調整）
];

/**
 * CSV種別からマスタ情報を取得
 */
export function getCsvUploadKindMaster(kind: CsvUploadKind): CsvUploadKindMaster | undefined {
  return CSV_UPLOAD_KIND_MASTER.find(m => m.kind === kind);
}

/**
 * データセットキーに応じたCSV種別のフィルタリング
 */
export function getKindsByDatasetKey(datasetKey: string): CsvUploadKind[] {
  const kindMap: Record<string, CsvUploadKind[]> = {
    'shogun_flash': [
      'shogun_flash_receive',
      'shogun_flash_shipment',
      'shogun_flash_yard',
    ],
    'shogun_final': [
      'shogun_final_receive',
      'shogun_final_shipment',
      'shogun_final_yard',
    ],
    'manifest': [
      'manifest_stage1',
      'manifest_stage2',
    ],
  };
  
  return kindMap[datasetKey] || [];
}

/**
 * データセットキーに応じたマスタ情報を取得
 */
export function getMasterByDatasetKey(datasetKey: string): CsvUploadKindMaster[] {
  const kinds = getKindsByDatasetKey(datasetKey);
  return CSV_UPLOAD_KIND_MASTER.filter(m => kinds.includes(m.kind));
}
