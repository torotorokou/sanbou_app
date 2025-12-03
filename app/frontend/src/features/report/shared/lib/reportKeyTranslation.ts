/**
 * 帳票キーの英語・日本語変換ユーティリティ
 * 
 * アーキテクチャ設計:
 * - バックエンド: ASCII安全な英語キーでファイル保存（HTTPヘッダー制約回避）
 * - フロントエンド: ダウンロード時に日本語ファイル名に変換（ブラウザAPIで完全サポート）
 * 
 * メリット:
 * - バックエンド: latin-1エンコーディング制約なし、OS依存文字コード問題なし
 * - フロントエンド: 国際化（i18n）との統合容易、ユーザー言語設定に応じた切替可能
 */

/**
 * 帳票キーから日本語ラベルへの変換マップ
 * manage_report_masters.yaml の label と対応
 */
export const REPORT_KEY_TO_JAPANESE: Record<string, string> = {
    factory_report: '工場日報',
    balance_sheet: '収支表',
    average_sheet: '平均表',
    management_sheet: '管理表',
    block_unit_price: 'ブロック単価表',
    ledger_book: '台帳',
    factory_report2: '工場実績報告書',
} as const;

/**
 * 帳票キーを日本語ラベルに変換
 * 
 * @param reportKey - 英語の帳票キー（例: 'factory_report'）
 * @returns 日本語ラベル（例: '工場日報'）、存在しない場合はreportKeyをそのまま返す
 */
export const translateReportKeyToJapanese = (reportKey: string): string => {
    return REPORT_KEY_TO_JAPANESE[reportKey] || reportKey;
};

/**
 * 帳票キーと日付から日本語ファイル名を生成
 * 
 * @param reportKey - 英語の帳票キー
 * @param reportDate - 日付（YYYY-MM-DD形式）
 * @param extension - ファイル拡張子（デフォルト: '.xlsx'）
 * @returns 日本語ファイル名（例: '工場日報-2024-12-03.xlsx'）
 */
export const generateJapaneseFilename = (
    reportKey: string,
    reportDate: string,
    extension: string = '.xlsx'
): string => {
    const japaneseLabel = translateReportKeyToJapanese(reportKey);
    return `${japaneseLabel}-${reportDate}${extension}`;
};
