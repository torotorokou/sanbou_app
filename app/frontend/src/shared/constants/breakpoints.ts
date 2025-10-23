// ===================================================
// Single Source of Truth: Breakpoints
// ===================================================
// ANT互換の実運用3段階（mobile ≤767, tablet 768-1199, desktop ≥1200）
// 将来的な4軸（sm:640, md:768, lg:1024, xl:1280）への移行は別PRで検討

/**
 * 統一ブレークポイント定義（ANT互換）
 * - xs: 0px（最小）
 * - sm: 576px（ANT互換・非推奨）
 * - md: 768px（タブレット開始）
 * - lg: 992px（ANT互換・非推奨）
 * - xl: 1200px（デスクトップ開始）
 */
export const bp = {
  xs: 0,
  sm: 576,  // @deprecated ANT互換。実運用では md を使用
  md: 768,
  lg: 992,  // @deprecated ANT互換。実運用では xl を使用
  xl: 1200,
} as const;

export type BpKey = keyof typeof bp;

/**
 * メディアクエリヘルパー（JS内でのstyle生成用）
 */
export const mq = {
  up: (k: BpKey) => `@media (min-width: ${bp[k]}px)`,
  down: (px: number) => `@media (max-width: ${px - 0.02}px)`,
  between: (a: BpKey, b: BpKey) => `@media (min-width: ${bp[a]}px) and (max-width: ${bp[b] - 0.02}px)`,
} as const;

/**
 * メディアクエリマッチング判定（クライアント側のみ）
 */
export const match = {
  up: (k: BpKey) => typeof window !== "undefined" && window.matchMedia(`(min-width: ${bp[k]}px)`).matches,
  between: (a: BpKey, b: BpKey) => typeof window !== "undefined" &&
    window.matchMedia(`(min-width: ${bp[a]}px) and (max-width: ${bp[b] - 0.02}px)`).matches,
} as const;

// ===================================================
// 互換レイヤー（既存コードの段階的移行用）
// ===================================================

/**
 * @deprecated ANT は bp に置き換えてください
 */
export const ANT = bp;
export type AntKey = BpKey;

/**
 * 実運用の3段ブレークポイント
 * - mobile: ≤767px
 * - tablet: 768-1199px
 * - desktop: ≥1200px
 */
export const BP = {
  mobileMax: bp.md - 1,  // 767
  tabletMin: bp.md,      // 768
  desktopMin: bp.xl,     // 1200
} as const;

export type ViewportTier = 'mobile' | 'tabletHalf' | 'desktop';

export const tierOf = (w: number): ViewportTier =>
  w <= BP.mobileMax ? 'mobile' : w < BP.desktopMin ? 'tabletHalf' : 'desktop';

export const isMobile = (w: number) => w <= BP.mobileMax; // ≤767
export const isTabletOrHalf = (w: number) => w >= BP.tabletMin && w < BP.desktopMin; // 768–1199
export const isDesktop = (w: number) => w >= BP.desktopMin; // ≥1200
