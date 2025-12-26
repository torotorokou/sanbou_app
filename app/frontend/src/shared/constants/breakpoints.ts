// ===================================================
// Single Source of Truth: Breakpoints
// ===================================================
// 運用3段階統一（2025-12-22更新）
// mobile ≤767, tablet 768-1280（★1280含む）, desktop ≥1281

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
  sm: 640, // 小型デバイス（Tailwind準拠）
  md: 768, // タブレット開始
  lg: 1024, // 大型タブレット/小型ノートPC
  xl: 1280, // デスクトップ開始
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
    typeof window !== "undefined" &&
    window.matchMedia(`(min-width: ${bp[k]}px)`).matches,
  between: (a: BpKey, b: BpKey) =>
    typeof window !== "undefined" &&
    window.matchMedia(
      `(min-width: ${bp[a]}px) and (max-width: ${bp[b] - 0.02}px)`,
    ).matches,
} as const;

/**
 * 実運用の3段ブレークポイント（Lean-3）★2025-12-22更新
 * - mobile:  ≤767px
 * - tablet:  768–1280px（★1280を含む）
 * - desktop: ≥1281px（★1280は含まない）
 */
export const BP = {
  mobileMax: bp.md - 1, // 767
  tabletMin: bp.md, // 768
  tabletMax: bp.xl, // 1280 ★追加
  desktopMin: bp.xl + 1, // 1281 ★変更：1280→1281
} as const;

export type ViewportTier = "mobile" | "tabletHalf" | "desktop";

export const tierOf = (w: number): ViewportTier =>
  w <= BP.mobileMax ? "mobile" : w < BP.desktopMin ? "tabletHalf" : "desktop";

export const isMobile = (w: number) => w <= BP.mobileMax; // ≤767
export const isTabletOrHalf = (w: number) =>
  w >= BP.tabletMin && w <= BP.tabletMax; // 768–1280 ★変更
export const isDesktop = (w: number) => w >= BP.desktopMin; // ≥1281 ★変更
