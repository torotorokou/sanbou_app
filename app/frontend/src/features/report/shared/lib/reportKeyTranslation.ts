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
 * - 保守性: 既存のREPORT_KEYS設定から自動生成（単一の情報源）
 */

import { REPORT_KEYS } from '@features/report/shared/config';

/**
 * 帳票キーから日本語ラベルへの変換マップ
 * REPORT_KEYSから自動生成されるため、設定の重複なし
 */
export const REPORT_KEY_TO_JAPANESE: Record<string, string> = Object.entries(REPORT_KEYS).reduce(
  (acc, [key, config]) => {
    acc[key] = config.label;
    return acc;
  },
  {} as Record<string, string>
);

/**
 * 帳票キーを日本語ラベルに変換
 *
 * @param reportKey - 英語の帳票キー（例: 'factory_report'）
 * @returns 日本語ラベル（例: '工場日報'）、存在しない場合はreportKeyをそのまま返す
 *
 * @example
 * translateReportKeyToJapanese('factory_report') // => '工場日報'
 * translateReportKeyToJapanese('balance_sheet') // => '工場搬出入収支表'
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
 *
 * @example
 * generateJapaneseFilename('factory_report', '2024-12-03')
 * // => '工場日報-2024-12-03.xlsx'
 *
 * generateJapaneseFilename('balance_sheet', '2024-12-03', '.pdf')
 * // => '工場搬出入収支表-2024-12-03.pdf'
 */
export const generateJapaneseFilename = (
  reportKey: string,
  reportDate: string,
  extension: string = '.xlsx'
): string => {
  const japaneseLabel = translateReportKeyToJapanese(reportKey);
  return `${japaneseLabel}-${reportDate}${extension}`;
};
