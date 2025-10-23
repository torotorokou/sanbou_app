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
    isSm: w >= bp.sm && w < bp.md,     // 640-767（小型デバイス）
    isMd: w >= bp.md && w < bp.lg,     // 768-1023（タブレット）
    isLg: w >= bp.lg && w < bp.xl,     // 1024-1279（大型タブレット/小型PC）
    isXl: w >= bp.xl,                  // 1280+（デスクトップ）
    isNarrow: w < bp.lg,               // 1024未満（モバイル+タブレット）
  };
}
