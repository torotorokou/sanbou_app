/**
 * useScreen - Lean-3 レスポンシブ判定Hook（唯一の真実）
 * 
 * Ant Design Grid の useBreakpoint をラップし、
 * プロジェクト標準の3段階（Mobile/Tablet/Desktop）に正規化
 * 
 * 【Lean-3 ブレークポイント】
 * - isMobile:  ≤767px  (0-767)
 * - isTablet:  768-1199px
 * - isDesktop: ≥1200px
 * 
 * 【使用例】
 * ```tsx
 * const { isMobile, isTablet, isDesktop } = useScreen();
 * 
 * if (isMobile) {
 *   return <MobileView />;
 * }
 * ```
 * 
 * 【注意】
 * - Ant Design の md = 768px, xl = 1200px を利用
 * - lg (992px) は使用しない（プロジェクトbp.lgとズレるため）
 */

import { Grid } from "antd";

const { useBreakpoint } = Grid;

export interface ScreenInfo {
  /** Ant Design breakpoints (参考用) */
  xs?: boolean;
  sm?: boolean;
  md?: boolean;
  lg?: boolean;
  xl?: boolean;
  xxl?: boolean;
  
  /** Lean-3 正規化フラグ */
  isMobile: boolean;   // ≤767px
  isTablet: boolean;   // 768-1199px
  isDesktop: boolean;  // ≥1200px
  
  /** 補助フラグ */
  isNarrow: boolean;   // モバイル+タブレット（< 1200px）
}

export function useScreen(): ScreenInfo {
  const bp = useBreakpoint();
  
  // Lean-3 正規化
  const isDesktop = !!bp.xl;           // 1200px以上
  const isTablet = !!bp.md && !bp.xl;  // 768-1199px
  const isMobile = !bp.md;             // 0-767px
  const isNarrow = !bp.xl;             // 1200px未満

  return {
    // Ant Design 元データ
    ...bp,
    
    // Lean-3 正規化
    isMobile,
    isTablet,
    isDesktop,
    isNarrow,
  };
}
