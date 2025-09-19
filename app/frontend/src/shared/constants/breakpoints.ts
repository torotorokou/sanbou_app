export const BREAKPOINTS = {
  sm: 767,
  mdMax: 1279,
} as const;

export type BreakpointKey = keyof typeof BREAKPOINTS;

export const media = {
  sm: `@media (max-width: ${BREAKPOINTS.sm}px)`,
  md: `@media (min-width: ${BREAKPOINTS.sm + 1}px) and (max-width: ${BREAKPOINTS.mdMax}px)`,
  lg: `@media (min-width: ${BREAKPOINTS.mdMax + 1}px)`,
};
