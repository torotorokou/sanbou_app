export const ANT = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
} as const;

export type AntKey = keyof typeof ANT;

export type ViewportTier = 'mobile' | 'tabletHalf' | 'desktop';

export const tierOf = (w: number): ViewportTier =>
  w < ANT.md ? 'mobile' : w < ANT.xl ? 'tabletHalf' : 'desktop';

export const isMobile = (w: number) => w < ANT.md; // ～767
export const isTabletOrHalf = (w: number) => w >= ANT.md && w < ANT.xl; // 768–1199
export const isDesktop = (w: number) => w >= ANT.xl; // 1200+
