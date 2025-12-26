/**
 * Customer List - Domain Types
 *
 * 顧客リスト分析の共通型定義
 */

/**
 * 顧客データ型
 */
export type CustomerData = {
  /** 顧客キー（一意識別子） */
  key: string;
  /** 顧客名 */
  name: string;
  /** 合計重量 (kg) */
  weight: number;
  /** 合計金額 (円) */
  amount: number;
  /** 担当営業者 */
  sales: string;
  /** 最終搬入日 (YYYY-MM-DD形式) */
  lastDeliveryDate?: string;
};
