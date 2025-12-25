/**
 * PortalPageの定数定義
 */

// カードのサイズ定数
export const CARD_WIDTH = 320;
export const CARD_HEIGHT = 208;
export const BUTTON_WIDTH = 160;
export const BUTTON_HEIGHT = 36;
export const BUTTON_FONT_SIZE = 14;

// カラーパレット（8色 - 各カード専用の色）
// モダンで洗練された配色、視認性とアクセシビリティを考慮
export const PALETTE = {
  OCEAN: '#0284C7', // オーシャンブルー - ダッシュボード（メインカラー）
  LAVENDER: '#C4B5FD', // ラベンダー - アナリティクス（少し淡めの紫）
  MINT: '#10B981', // ミントグリーン - 帳簿作成（爽やかな緑）
  CORAL: '#FB7185', // コーラルピンク - 参謀 NAVI（柔らかいコーラル）
  GOLD: '#FBBF24', // ゴールド - マニュアル（アクセント用の黄）
  PURPLE: '#6366F1', // ロイヤルパープル - データベース（濃いめの青紫）
  CYAN: '#06B6D4', // シアン - 管理機能（すっきりしたシアン）
  GRAY: '#6B7280', // グレー - お知らせ（中間グレー）
} as const;
