// src/theme/colorMaps.ts
import { customTokens } from './tokens';

// CSV関連のカラーマップ
export const csvTypeColors = {
    shipment: customTokens.csvShipmentBg,
    receive: customTokens.csvReceiveBg,
    yard: customTokens.csvYardBg,
};

// チャートカラーパレット（5色構成）
export const chartColorPalette = [
    customTokens.chartGreen,
    customTokens.chartBlue,
    customTokens.chartOrange,
    customTokens.chartRed,
    customTokens.chartPurple,
];

// グラデーションマップ（レベニューパネル用）
export const revenueGradientMap = {
    売上: customTokens.colorInfo, // ブルー
    仕入: customTokens.chartRed, // レッド
    粗利: customTokens.colorSuccess, // グリーン
    ブロック: customTokens.colorWarning, // オレンジ
};

// 顧客分析カラーマップ（売上レベル別）
export const customerAnalysisColors = [
    { threshold: 300, color: customTokens.chartRed, label: '300万円以上' },
    { threshold: 100, color: customTokens.chartOrange, label: '100-300万円' },
    { threshold: 0, color: customTokens.chartBlue, label: '100万円未満' },
];

// 検証結果カラーマップ
export const validationStatusColors = {
    valid: customTokens.statusValid,
    invalid: customTokens.statusInvalid,
    unknown: customTokens.statusUnknown,
    ok: customTokens.statusValid, // validと統一
    ng: customTokens.statusInvalid, // invalidと統一
};

// アクションボタンカラーマップ
export const actionButtonColors = {
    generate: customTokens.colorWarning, // オレンジ
    download: customTokens.colorInfo, // ブルー
    preview: customTokens.colorSuccess, // グリーン
    delete: customTokens.colorError, // レッド
};

// カテゴリ別カラーマップ（円グラフ用）
export const categoryColors = [
    customTokens.chartGreen, // カテゴリA
    customTokens.chartBlue, // カテゴリB
    customTokens.chartPurple, // カテゴリC
    customTokens.chartOrange, // カテゴリD
    customTokens.chartRed, // カテゴリE
    customTokens.colorNeutral, // カテゴリF
];

// ファクトリーダッシュボード用チャートカラー
export const factoryChartColors = {
    revenue: customTokens.colorSuccess, // グリーン
    profit: customTokens.colorPrimary, // ブランドグリーン
    info: customTokens.colorInfo, // ブルー
    warning: customTokens.colorWarning, // オレンジ
    error: customTokens.colorError, // レッド
};
