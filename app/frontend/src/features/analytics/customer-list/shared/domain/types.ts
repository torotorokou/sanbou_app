/**
 * Customer List - Domain Types
 * 
 * 顧客リスト分析の共通型定義
 */

/**
 * 営業担当者データ型
 */
export type SalesRep = {
    /** 営業担当者ID */
    salesRepId: string;
    /** 営業担当者名 */
    salesRepName: string;
};

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

/**
 * 離脱顧客データ型
 */
export type LostCustomer = {
    /** 顧客ID */
    customerId: string;
    /** 顧客名 */
    customerName: string;
    /** 営業担当者ID */
    salesRepId: string | null;
    /** 営業担当者名 */
    salesRepName: string | null;
    /** 前期間の最終訪問日 */
    lastVisitDate: string; // YYYY-MM-DD
    /** 前期間の訪問日数 */
    prevVisitDays: number;
    /** 前期間の合計金額（円） */
    prevTotalAmountYen: number;
    /** 前期間の合計重量（kg） */
    prevTotalQtyKg: number;
};

/**
 * 顧客離脱分析リクエストパラメータ
 */
export type CustomerChurnAnalyzeParams = {
    /** 今期間の開始日 */
    currentStart: string; // YYYY-MM-DD
    /** 今期間の終了日 */
    currentEnd: string; // YYYY-MM-DD
    /** 前期間の開始日 */
    previousStart: string; // YYYY-MM-DD
    /** 前期間の終了日 */
    previousEnd: string; // YYYY-MM-DD
};
