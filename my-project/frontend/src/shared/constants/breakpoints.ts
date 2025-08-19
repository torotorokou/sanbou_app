export const BREAKPOINTS = {
  mobile: 767,
  tablet: 1023,
  smallPC: 1366,
  fullHD: 1920,
} as const;

export type BreakpointKey = keyof typeof BREAKPOINTS;

export const media = {
  mobile: `@media (max-width: ${BREAKPOINTS.mobile}px)`,
  tablet: `@media (min-width: ${BREAKPOINTS.mobile + 1}px) and (max-width: ${
    BREAKPOINTS.tablet
  }px)`,
  desktop: `@media (min-width: ${BREAKPOINTS.tablet + 1}px)`,
};
