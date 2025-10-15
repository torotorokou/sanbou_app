export const ANT = {
  xs: 480,
  sm: 576,  // @deprecated 使用禁止。BP を使用してください
  md: 768,
  lg: 992,  // @deprecated 使用禁止。BP を使用してください
  xl: 1200,
  xxl: 1600, // @deprecated 使用禁止。BP を使用してください
} as const;

export type AntKey = keyof typeof ANT;

/**
 * 実運用の3段ブレークポイント
 * - mobile: ≤767px
 * - tablet: 768-1199px
 * - desktop: ≥1200px
 */
export const BP = {
  mobileMax: ANT.md - 1,  // 767
  tabletMin: ANT.md,      // 768
  desktopMin: ANT.xl,     // 1200
} as const;

export type ViewportTier = 'mobile' | 'tabletHalf' | 'desktop';

export const tierOf = (w: number): ViewportTier =>
  w <= BP.mobileMax ? 'mobile' : w < BP.desktopMin ? 'tabletHalf' : 'desktop';

export const isMobile = (w: number) => w <= BP.mobileMax; // ≤767
export const isTabletOrHalf = (w: number) => w >= BP.tabletMin && w < BP.desktopMin; // 768–1199
export const isDesktop = (w: number) => w >= BP.desktopMin; // ≥1200
