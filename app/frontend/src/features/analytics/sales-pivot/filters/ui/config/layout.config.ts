/**
 * FilterPanelのレイアウト定数定義
 * 
 * グリッドギャップ、マージン、グリッド設定など、
 * レイアウト関連のすべての定数を一元管理します。
 * 
 * 【保守性のポイント】
 * - レイアウト変更時はこのファイルのみ修正
 * - コンポーネント側はこの設定を参照するだけ
 * - 型安全性を確保（as const）
 */

/**
 * Ant Design Grid型定義
 */
export interface GridConfig {
  xs?: number;
  sm?: number;
  md?: number;
  lg?: number;
  xl?: number;
  xxl?: number;
}

/**
 * グリッドギャップ（gutter）設定
 */
export const GRID_GUTTER = {
  horizontal: 16,
  vertical: 16,
} as const;

/**
 * マージン設定
 */
export const MARGINS = {
  sectionTop: 16,
  divider: '16px 0',
} as const;

/**
 * ブレークポイントしきい値（参考値）
 * 実際のブレークポイントはuseResponsive内で管理されています
 */
export const BREAKPOINTS = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

/**
 * FilterPanel グリッド設定
 * 
 * 各要素のグリッド配置を定義します。
 * デスクトップ（xl以上）とモバイル（xl未満）で異なる設定が必要な要素は
 * 別々の設定を用意しています。
 * 
 * 【命名規則】
 * - 基本: [要素名]
 * - デスクトップ専用: [要素名]Desktop
 * - モバイル専用: [要素名]Mobile（必要に応じて）
 */
export const FILTER_GRID = {
  /**
   * 種別セレクター（廃棄物/有価物）
   * xl以上で1行配置（20.8%幅）、xl未満で全幅
   */
  category: {
    xs: 24,
    md: 24,
    xl: 5,
  },

  /**
   * モードセレクター（顧客/品名/日付）- デスクトップ
   * xl以上: 種別と同じ行に配置（20.8%幅）
   */
  modeDesktop: {
    xs: 24,
    md: 24,
    xl: 5,
  },

  /**
   * モードセレクター（顧客/品名/日付）- モバイル
   * xl未満: 2行目の左側に配置（33.3%幅）
   */
  modeMobile: {
    xs: 24,
    md: 8,
    xl: 5,
  },

  /**
   * TopN・ソートコントロール - デスクトップ
   * xl以上: 種別・モードと同じ行に配置（58.3%幅）
   */
  topNSortDesktop: {
    xs: 24,
    md: 24,
    xl: 14,
  },

  /**
   * TopN・ソートコントロール - モバイル
   * xl未満: 2行目の右側に配置（66.7%幅）
   */
  topNSortMobile: {
    xs: 24,
    md: 16,
    xl: 14,
  },

  /**
   * 期間セレクター（月次/日次、単一/期間）
   * 常に全幅
   */
  period: {
    xs: 24,
    lg: 24,
  },

  /**
   * 営業選択
   * 75%幅（md以上）
   */
  repSelect: {
    xs: 24,
    md: 18,
  },

  /**
   * 絞り込みフィルタ（顧客/品名/日付で絞る）
   * 25%幅（md以上）
   */
  filter: {
    xs: 24,
    md: 6,
  },
} as const satisfies Record<string, GridConfig>;

/**
 * レイアウトモード
 */
export type LayoutMode = 'desktop' | 'mobile';

/**
 * レイアウトモードの判定
 * xl以上（1280px~）をデスクトップとみなす
 */
export const getLayoutMode = (isDesktop: boolean): LayoutMode => 
  isDesktop ? 'desktop' : 'mobile';
