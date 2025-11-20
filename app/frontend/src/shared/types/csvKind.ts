/**
 * CsvKind - 将軍CSV種別の型定義
 * 
 * バックエンドの CsvKind Enum と完全に一致させています。
 * 命名規則: {system}_{version}_{direction}
 *   - system: shogun
 *   - version: flash (速報版) / final (確定版)
 *   - direction: receive (受入) / shipment (出荷) / yard (ヤード)
 * 
 * この論理名は以下の全レイヤーで統一されています:
 *   - log.upload_file.csv_type カラム
 *   - stg.{csv_kind} テーブル名
 *   - Python CsvKind Enum
 *   - API の csvKind フィールド
 */
export type CsvKind =
  | 'shogun_flash_receive'
  | 'shogun_flash_shipment'
  | 'shogun_flash_yard'
  | 'shogun_final_receive'
  | 'shogun_final_shipment'
  | 'shogun_final_yard';

/**
 * CsvKind のユーティリティ関数群
 */
export const CsvKindUtils = {
  /**
   * システム名を取得 (例: 'shogun')
   */
  getSystem: (kind: CsvKind): string => kind.split('_')[0],
  
  /**
   * バージョンを取得 (例: 'flash', 'final')
   */
  getVersion: (kind: CsvKind): 'flash' | 'final' => kind.split('_')[1] as 'flash' | 'final',
  
  /**
   * 方向を取得 (例: 'receive', 'shipment', 'yard')
   */
  getDirection: (kind: CsvKind): 'receive' | 'shipment' | 'yard' => kind.split('_')[2] as 'receive' | 'shipment' | 'yard',
  
  /**
   * 速報版かどうか
   */
  isFlash: (kind: CsvKind): boolean => kind.split('_')[1] === 'flash',
  
  /**
   * 確定版かどうか
   */
  isFinal: (kind: CsvKind): boolean => kind.split('_')[1] === 'final',
  
  /**
   * 対応するstgテーブル名を取得 (例: 'stg.shogun_flash_receive')
   */
  getTableName: (kind: CsvKind): string => `stg.${kind}`,
};

/**
 * 全CsvKind値の配列
 */
export const ALL_CSV_KINDS: readonly CsvKind[] = [
  'shogun_flash_receive',
  'shogun_flash_shipment',
  'shogun_flash_yard',
  'shogun_final_receive',
  'shogun_final_shipment',
  'shogun_final_yard',
] as const;
