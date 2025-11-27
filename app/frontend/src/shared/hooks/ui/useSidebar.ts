// src/shared/hooks/ui/useSidebar.ts
import { useEffect, useMemo, useState } from "react";
import { useResponsive } from "./useResponsive";

export type SidebarBreakpoint = "xs" | "md" | "xl";

export interface SidebarConfig {
  width: number;
  collapsedWidth: number;
  breakpoint: SidebarBreakpoint; // xs(≤767) / md(768-1279) / xl(≥1280)
  autoCollapse: boolean;
  forceCollapse: boolean;
  drawerMode: boolean;
}

export interface UseSidebarOptions {
  /** ユーザーによるトグルを優先するか（ブレークポイントを跨いだ時のみリセット） */
  respectUserToggleUntilBreakpointChange?: boolean;
}

/**
 * useSidebar — サイドバーの状態・設定・アニメーションを一元管理
 */
export function useSidebar(
  options: UseSidebarOptions = {}
): {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  config: SidebarConfig;
  style: React.CSSProperties;
} {
  const { isMobile, isTablet } = useResponsive();
  const { respectUserToggleUntilBreakpointChange = false } = options;

  const config = useMemo<SidebarConfig>(() => {
    if (isMobile) {
      return {
        width: 280,
        collapsedWidth: 0,
        breakpoint: "xs",
        autoCollapse: false,
        forceCollapse: true,
        drawerMode: true,
      };
    }
    if (isTablet) {
      return {
        width: 230,
        collapsedWidth: 60,
        breakpoint: "md",
        autoCollapse: true,
        forceCollapse: false,
        drawerMode: false,
      };
    }
    return {
      width: 250,
      collapsedWidth: 80,
      breakpoint: "xl",
      autoCollapse: false,
      forceCollapse: false,
      drawerMode: false,
    };
  }, [isMobile, isTablet]);

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    return config.forceCollapse || config.autoCollapse;
  });

  useEffect(() => {
    if (respectUserToggleUntilBreakpointChange) {
      setCollapsed(config.forceCollapse || config.autoCollapse);
    } else {
      setCollapsed(config.forceCollapse || config.autoCollapse);
    }
  }, [config.breakpoint, config.forceCollapse, config.autoCollapse, respectUserToggleUntilBreakpointChange]);

  const style = useMemo<React.CSSProperties>(
    () => ({
      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      willChange: "width, transform",
    }),
    []
  );

  return { collapsed, setCollapsed, config, style };
}

export default useSidebar;
