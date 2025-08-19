import React from "react";
import { BREAKPOINTS as BP } from "@/shared/constants/breakpoints";

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
    mediaQuery.addListener(handler);
    return () => mediaQuery.removeListener(handler);
  }, [mediaQuery]);

  return matches;
};

// デバイスタイプ判定フック - シンプル版
export const useDeviceType = () => {
  const isMobile = useMediaQuery(BREAKPOINTS.mobile);
  const isTablet = useMediaQuery(BREAKPOINTS.tablet);
  const isDesktop = useMediaQuery(BREAKPOINTS.desktop);

  return {
    isMobile,
    isTablet,
    isDesktop,
    isMobileOrTablet: isMobile || isTablet,

    // 後方互換性のために残す（廃止予定）
    isSmallDesktop: isDesktop, // デスクトップに統合
    isMediumDesktop: isDesktop, // デスクトップに統合
    isLargeDesktop: isDesktop, // デスクトップに統合
    shouldAutoCollapse: isMobile || isTablet, // モバイル・タブレットで自動縮小
    shouldForceCollapse: isMobile, // モバイルで強制縮小
  };
};
