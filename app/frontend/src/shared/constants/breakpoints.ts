/**
 * Breakpoints — single source of truth
 *
 * この定義をアプリ全体（JS/TS フック、CSS 変数、レイアウトロジック）で参照してください。
 * Ant Design の Grid/useBreakpoint は内部に独自ブレークポイント（lg=992px 等）を持ちます。
 * それらを使う場合は、本定義との違いに注意し、可能なら本定義に寄せたロジックを利用してください。
 */
export const BREAKPOINTS = {
  sm: 767,
  mdMax: 1279,
  // additional shared breakpoints for layout behaviors
  autoCollapse: 1280,
  forceCollapse: 900,
  tabletMax: 1023,
} as const;

export type BreakpointKey = keyof typeof BREAKPOINTS;

export const media = {
  sm: `@media (max-width: ${BREAKPOINTS.sm}px)`,
  md: `@media (min-width: ${BREAKPOINTS.sm + 1}px) and (max-width: ${BREAKPOINTS.mdMax}px)`,
  lg: `@media (min-width: ${BREAKPOINTS.mdMax + 1}px)`,
};
