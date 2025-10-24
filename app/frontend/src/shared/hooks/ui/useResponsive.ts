/**
 * useResponsive - レスポンシブ判定の統一Hook
 * 
 * 【役割】
 * - window幅に基づくブレークポイント判定を提供
 * - useScreen と useWindowSize を統合（Single Source of Truth）
 * - SSR安全、requestAnimationFrame スロットル
 * 
 * 【使用例】
 * ```tsx
 * const { width, height, isMobile, isTablet, isDesktop } = useResponsive();
 * const { flags } = useResponsive();
 * if (flags.isMobile) {
 *   return <MobileView />;
 * }
 * ```
 */
import { useEffect, useRef, useState } from "react";
import {
  bp,
  isMobile as isMobileWidth,
  isTabletOrHalf as isTabletWidth,
  isDesktop as isDesktopWidth,
  type ViewportTier,
} from "@/shared/constants";

export type ResponsiveFlags = {
  // Lean-3
  isMobile: boolean;   // ≤767
  isTablet: boolean;   // 768–1279
  isDesktop: boolean;  // ≥1280
  // 補助
  isNarrow: boolean;   // <1280
  isSm: boolean;       // 640–767
  isMd: boolean;       // 768–1023
  isLg: boolean;       // 1024–1279
  isXl: boolean;       // ≥1280
  tier: ViewportTier;  // 'mobile' | 'tabletHalf' | 'desktop'
};

export type ResponsiveState = {
  width: number;
  height: number;
  flags: ResponsiveFlags;
  // 互換のためトップレベルでも返す（既存コード変更を最小化）
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isNarrow: boolean;
  isSm: boolean;
  isMd: boolean;
  isLg: boolean;
  isXl: boolean;
  tier: ViewportTier;
};

function makeFlags(w: number): ResponsiveFlags {
  const mobile  = isMobileWidth(w);
  const tablet  = isTabletWidth(w);
  const desktop = isDesktopWidth(w);
  return {
    isMobile: mobile,
    isTablet: tablet,
    isDesktop: desktop,
    isNarrow: w < bp.xl,
    isSm: w >= bp.sm && w < bp.md,
    isMd: w >= bp.md && w < bp.lg,
    isLg: w >= bp.lg && w < bp.xl,
    isXl: w >= bp.xl,
    tier: mobile ? "mobile" : tablet ? "tabletHalf" : "desktop",
  };
}

/**
 * useResponsive — ビューポート幅に基づく統一フック
 * - `useScreen` / `useWindowSize` を集約
 * - SSR安全、rAFスロットル
 */
export function useResponsive(): ResponsiveState {
  const getInitial = (): ResponsiveState => {
    const hasWindow = typeof window !== "undefined";
    const width  = hasWindow ? window.innerWidth  : bp.md;
    const height = hasWindow ? window.innerHeight : 0;
    const flags  = makeFlags(width);
    return { width, height, flags, ...flags };
  };

  const [state, setState] = useState<ResponsiveState>(getInitial);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    
    // 初回マウント時に即座に実際のサイズを設定
    const width = window.innerWidth;
    const height = window.innerHeight;
    const flags = makeFlags(width);
    setState({ width, height, flags, ...flags });
    
    const onResize = () => {
      if (frame.current != null) return;
      frame.current = window.requestAnimationFrame(() => {
        frame.current = null;
        const width = window.innerWidth;
        const height = window.innerHeight;
        const flags = makeFlags(width);
        setState({ width, height, flags, ...flags });
      });
    };
    window.addEventListener("resize", onResize, { passive: true });
    window.addEventListener("orientationchange", onResize, { passive: true });
    return () => {
      if (frame.current != null) window.cancelAnimationFrame(frame.current);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("orientationchange", onResize);
    };
  }, []);

  return state;
}

export default useResponsive;
