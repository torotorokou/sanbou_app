// Single-source responsive hook wrapper
// このフックは、window幅の判定・監視を自前で行わず、
// `shared/hooks/ui/useWindowSize` に集約されたロジックを利用します。
// これにより、BREAKPOINTS の変更が全体に自動反映され、保守性が向上します。

import { useWindowSize } from "@shared/hooks/ui";

export type View = "mobile" | "tablet" | "desktop";

export const useBreakpoint = (): View => {
  const { isMobile, isTablet } = useWindowSize();
  if (isMobile) return "mobile";
  if (isTablet) return "tablet";
  return "desktop";
};
