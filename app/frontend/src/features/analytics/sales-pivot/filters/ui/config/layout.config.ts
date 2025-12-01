/**
 * FilterPanelのレイアウト定数定義
 * 
 * グリッドギャップ、マージン、その他のレイアウト関連の定数を管理します。
 */

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
 * レイアウトモード
 */
export type LayoutMode = 'desktop' | 'mobile';

/**
 * レイアウトモードの判定
 * xl以上（1280px~）をデスクトップとみなす
 */
export const getLayoutMode = (isDesktop: boolean): LayoutMode => 
  isDesktop ? 'desktop' : 'mobile';
