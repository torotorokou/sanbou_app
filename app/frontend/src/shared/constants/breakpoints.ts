// ===================================================
// Single Source of Truth: Breakpoints
// ===================================================
// Tailwind CSS準拠の4段階体系に移行完了
// mobile ≤767, tablet 768-1023, desktop-sm 1024-1279, desktop-xl ≥1280

/**
 * 統一ブレークポイント定義（Tailwind CSS準拠）
 * - xs: 0px（最小）
 * - sm: 640px（小型デバイス）
 * - md: 768px（タブレット開始）
 * - lg: 1024px（大型タブレット/小型ノートPC）
 * - xl: 1280px（デスクトップ開始）
 */
export const bp = {
  xs: 0,
  sm: 640,   // 小型デバイス（Tailwind準拠）
  md: 768,   // タブレット開始
  lg: 1024,  // 大型タブレット/小型ノートPC
  xl: 1280,  // デスクトップ開始
} as const;

export type BpKey = keyof typeof bp;

/**
 * メディアクエリヘルパー（JS内でのstyle生成用）
 */
export const mq = {
  up: (k: BpKey) => `@media (min-width: ${bp[k]}px)`,
  down: (px: number) => `@media (max-width: ${px - 0.02}px)`,
  between: (a: BpKey, b: BpKey) =>
    `@media (min-width: ${bp[a]}px) and (max-width: ${bp[b] - 0.02}px)`,
} as const;

/**
 * メディアクエリマッチング判定（クライアント側のみ）
 */
export const match = {
  up: (k: BpKey) =>
    typeof window !== "undefined" && window.matchMedia(`(min-width: ${bp[k]}px)`).matches,
  between: (a: BpKey, b: BpKey) =>
    typeof window !== "undefined" &&
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
 * 実運用の3段ブレークポイント（Lean-3）
 * - mobile:  ≤767px
 * - tablet:  768–1279px
 * - desktop: ≥1280px
 */
export const BP = {
  mobileMax: bp.md - 1,  // 767
  tabletMin: bp.md,      // 768
  desktopMin: bp.xl,     // 1280
} as const;

export type ViewportTier = 'mobile' | 'tabletHalf' | 'desktop';

export const tierOf = (w: number): ViewportTier =>
  w <= BP.mobileMax ? 'mobile' : w < BP.desktopMin ? 'tabletHalf' : 'desktop';

export const isMobile = (w: number) => w <= BP.mobileMax;                 // ≤767
export const isTabletOrHalf = (w: number) => w >= BP.tabletMin && w < BP.desktopMin; // 768–1279
export const isDesktop = (w: number) => w >= BP.desktopMin;               // ≥1280
