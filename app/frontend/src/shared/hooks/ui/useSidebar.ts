// src/shared/hooks/ui/useSidebar.ts
import { useEffect, useMemo, useState } from "react";
import { useResponsive } from "./useResponsive";

export type SidebarBreakpoint = "xs" | "md" | "xl";

export interface SidebarConfig {
  width: number;
  collapsedWidth: number;
  breakpoint: SidebarBreakpoint;
  /** 初期状態で閉じるか（ブレークポイント変更時にも適用） */
  defaultCollapsed: boolean;
  /** 強制的に閉じるか（ユーザー操作を無視） */
  forceCollapse: boolean;
  /** Drawerモードで表示するか */
  drawerMode: boolean;
}

export interface UseSidebarOptions {
  /** ユーザーによるトグルを優先するか（ブレークポイントを跨いだ時のみリセット） */
  respectUserToggleUntilBreakpointChange?: boolean;
}

/**
 * useSidebar — サイドバーの状態・設定・アニメーションを一元管理（2025-12-22更新）
 * 
 * 【動作】★境界値変更
 * - モバイル（≤767px）: Drawerモード、強制的に閉じる
 * - タブレット（768-1280px）: デフォルトで閉じる（ユーザーが開ける）★1280を含む
 * - デスクトップ（≥1281px）: デフォルトで開く（ユーザーが閉じられる）★1280は含まない
 * 
 * 【ブレークポイント間の移動】
 * - ブレークポイントが変わると、新しいブレークポイントのデフォルト状態にリセット
 */
export function useSidebar(
  options: UseSidebarOptions = {}
): {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  config: SidebarConfig;
  style: React.CSSProperties;
} {
  const { isMobile, isTablet, isDesktop } = useResponsive();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { respectUserToggleUntilBreakpointChange = false } = options;

  // デバイスタイプに応じた設定を決定
  const config = useMemo<SidebarConfig>(() => {
    if (isMobile) {
      return {
        width: 280,
        collapsedWidth: 0,
        breakpoint: "xs",
        defaultCollapsed: true,
        forceCollapse: true, // モバイルでは強制的に閉じる
        drawerMode: true,
      };
    }
    if (isTablet) {
      return {
        width: 230,
        collapsedWidth: 60,
        breakpoint: "md",
        defaultCollapsed: true, // タブレット（768-1280px）はデフォルトで閉じる ★更新
        forceCollapse: false,
        drawerMode: false,
      };
    }
    // デスクトップ（≥1281px）★更新
    return {
      width: 250,
      collapsedWidth: 80,
      breakpoint: "xl",
      defaultCollapsed: false, // デスクトップはデフォルトで開く
      forceCollapse: false,
      drawerMode: false,
    };
  }, [isMobile, isTablet, isDesktop]);

  // 初期状態を設定の defaultCollapsed または forceCollapse に基づいて決定
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    return config.forceCollapse || config.defaultCollapsed;
  });

  // ユーザーがトグルしたかどうかを追跡
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [userToggled, setUserToggled] = useState(false);
  
  // 前回のブレークポイントを保持
  const [prevBreakpoint, setPrevBreakpoint] = useState(config.breakpoint);

  // ブレークポイントが変わったら状態をリセット
  useEffect(() => {
    if (config.breakpoint !== prevBreakpoint) {
      setPrevBreakpoint(config.breakpoint);
      setUserToggled(false);
      
      // 強制折りたたみまたはデフォルト状態に設定
      const newCollapsed = config.forceCollapse || config.defaultCollapsed;
      setCollapsed(newCollapsed);
    }
  }, [config.breakpoint, config.forceCollapse, config.defaultCollapsed, prevBreakpoint]);

  // 強制折りたたみの場合は常に閉じる
  useEffect(() => {
    if (config.forceCollapse) {
      setCollapsed(true);
    }
  }, [config.forceCollapse]);

  // ユーザートグルをラップして追跡
  const handleSetCollapsed = (value: boolean) => {
    if (!config.forceCollapse) {
      setUserToggled(true);
      setCollapsed(value);
    }
  };

  const style = useMemo<React.CSSProperties>(
    () => ({
      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      willChange: "width, transform",
    }),
    []
  );

  return { 
    collapsed, 
    setCollapsed: handleSetCollapsed, 
    config, 
    style 
  };
}

export default useSidebar;
