/**
 * useResponsive - レスポンシブ判定の公開Hook
 * 
 * 【役割】
 * - window幅に基づくブレークポイント判定を提供
 * - 実装は useWindowSize に委譲（Single Responsibility）
 * 
 * 【使用例】
 * ```tsx
 * const { width, isSm, isMd, isLg, isXl, isNarrow } = useResponsive();
 * if (isNarrow) { // モバイル・タブレット判定
 *   return <MobileView />;
 * }
 * ```
 */
import { useEffect, useState } from "react";
import { bp } from "@/shared/constants/breakpoints";

export function useResponsive() {
  const [w, setW] = useState<number>(() => 
    typeof window !== "undefined" ? window.innerWidth : bp.md
  );

  useEffect(() => {
    const onResize = () => setW(window.innerWidth);
    window.addEventListener("resize", onResize, { passive: true });
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return {
    width: w,
    isSm: w >= bp.sm && w < bp.md,     // 576-767
    isMd: w >= bp.md && w < bp.xl,     // 768-1199（タブレット）
    isLg: w >= bp.lg && w < bp.xl,     // 992-1199（廃止予定）
    isXl: w >= bp.xl,                  // 1200+（デスクトップ）
    isNarrow: w < bp.xl,               // 1200未満（モバイル+タブレット）
  };
}
