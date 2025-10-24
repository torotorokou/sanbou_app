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
import { bp } from "@/shared/constants";

// eslint-disable-next-line no-restricted-syntax
export type Tier = "xs" | "sm" | "md" | "lg" | "xl";

export type ResponsiveFlags = {
  // 5段階詳細（Tailwind準拠）
  isXs: boolean;  // < 640
  isSm: boolean;  // 640–767
  isMd: boolean;  // 768–1023
  isLg: boolean;  // 1024–1279
  isXl: boolean;  // ≥1280
  tier: Tier;
  // グルーピング（Lean-3互換）
  isMobile: boolean;   // xs or sm (≤767)
  isTablet: boolean;   // md (768–1023)
  isLaptop: boolean;   // lg (1024–1279)
  isDesktop: boolean;  // xl (≥1280)
  isNarrow: boolean;   // <1280
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
  tier: Tier;
};

export function makeFlags(w: number): ResponsiveFlags {
  const isXs = w < bp.sm;
  const isSm = w >= bp.sm && w < bp.md;
  const isMd = w >= bp.md && w < bp.lg;
  const isLg = w >= bp.lg && w < bp.xl;
  const isXl = w >= bp.xl;
  // eslint-disable-next-line no-restricted-syntax
  const tier: Tier = isXs ? "xs" : isSm ? "sm" : isMd ? "md" : isLg ? "lg" : "xl";
  return {
    isXs, isSm, isMd, isLg, isXl, tier,
    isMobile: isXs || isSm,
    isTablet: isMd,
    isLaptop: isLg,
    isDesktop: isXl,
    isNarrow: w < bp.xl,
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
