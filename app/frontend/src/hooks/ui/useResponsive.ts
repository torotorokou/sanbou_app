import React from "react";
import { BREAKPOINTS as BP } from "@/shared/constants/breakpoints";
import { useWindowSize } from "./useWindowSize";

// 共有ブレークポイントからメディアクエリを組み立てて公開（既存API互換のためのエイリアス）
export const BREAKPOINTS = {
  mobile: `(max-width: ${BP.mobile}px)`,
  tablet: `(min-width: ${BP.mobile + 1}px) and (max-width: ${BP.tablet}px)`,
  desktop: `(min-width: ${BP.tablet + 1}px)`,

  // helpers
  mobileOnly: `(max-width: ${BP.mobile}px)`,
  tabletUp: `(min-width: ${BP.mobile + 1}px)`,
  desktopUp: `(min-width: ${BP.tablet + 1}px)`,
} as const;

// メディアクエリフック用のヘルパー
export const useMediaQuery = (query: string): boolean => {
  if (typeof window === "undefined") return false;

  const mediaQuery = window.matchMedia(query);
  const [matches, setMatches] = React.useState(mediaQuery.matches);

  React.useEffect(() => {
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches);
    // modern API（後方互換のためのフォールバックも考慮）
    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }
    if ('addListener' in mediaQuery && 'removeListener' in mediaQuery) {
      // 古いブラウザ互換
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (mediaQuery as any).addListener(handler);
      return () => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (mediaQuery as any).removeListener(handler);
      };
    }
    return () => void 0;
  }, [mediaQuery]);

  return matches;
};

// デバイスタイプ判定フック - シンプル版
export const useDeviceType = () => {
  // 標準化: window 幅をソースオブトゥルースとし、即時追従
  const { isMobile, isTablet, isDesktop, width } = useWindowSize();

  return {
    isMobile,
    isTablet,
    isDesktop,
    isMobileOrTablet: isMobile || isTablet,
    // 旧フラグの互換（段階的削除予定）
    isSmallDesktop: isDesktop,
    isMediumDesktop: isDesktop,
    isLargeDesktop: isDesktop,
    shouldAutoCollapse: isMobile || isTablet,
    shouldForceCollapse: isMobile,
    // 便利情報
    width,
  } as const;
};
