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
   * 受入系かどうか
   */
  isReceive: (kind: CsvKind): boolean => kind.split('_')[2] === 'receive',
  
  /**
   * 出荷系かどうか
   */
  isShipment: (kind: CsvKind): boolean => kind.split('_')[2] === 'shipment',
  
  /**
   * ヤード系かどうか
   */
  isYard: (kind: CsvKind): boolean => kind.split('_')[2] === 'yard',
  
  /**
   * 表示名を取得（日本語）
   */
  getDisplayName: (kind: CsvKind): string => {
    const version = CsvKindUtils.getVersion(kind);
    const direction = CsvKindUtils.getDirection(kind);
    const versionLabel = version === 'flash' ? '速報' : '確定';
    const directionLabel = 
      direction === 'receive' ? '受入' :
      direction === 'shipment' ? '出荷' :
      'ヤード';
    return `${versionLabel}${directionLabel}`;
  }
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

