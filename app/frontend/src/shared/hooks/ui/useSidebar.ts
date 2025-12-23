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
 * useSidebar — サイドバーの状態・設定・アニメーションを一元管理（2025-12-23更新）
 * 
 * 【動作】
 * - モバイル（≤767px）: Drawerモード、drawerOpenで開閉
 * - タブレット（768-1280px）: collapsedで開閉
 * - デスクトップ（≥1281px）: collapsedで開閉
 * 
 * 【状態分離】
 * - collapsed: デスクトップ/タブレット用の開閉状態
 * - drawerOpen: モバイルDrawer用の開閉状態
 * - ブレークポイント変更時に状態を正規化（モバイル強制値を保存しない）
 */
export function useSidebar(
  options: UseSidebarOptions = {}
): {
  isMobile: boolean;
  collapsed: boolean;
  drawerOpen: boolean;
  openDrawer: () => void;
  closeDrawer: () => void;
  toggleCollapsed: () => void;
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
        forceCollapse: false,
        drawerMode: true,
      };
    }
    if (isTablet) {
      return {
        width: 230,
        collapsedWidth: 60,
        breakpoint: "md",
        defaultCollapsed: true,
        forceCollapse: false,
        drawerMode: false,
      };
    }
    // デスクトップ（≥1281px）
    return {
      width: 250,
      collapsedWidth: 80,
      breakpoint: "xl",
      defaultCollapsed: false,
      forceCollapse: false,
      drawerMode: false,
    };
  }, [isMobile, isTablet, isDesktop]);

  // Desktop/Tablet用の折りたたみ状態
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    return config.defaultCollapsed;
  });

  // Mobile用のDrawer開閉状態
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);

  // 前回のブレークポイントを保持
  const [prevBreakpoint, setPrevBreakpoint] = useState(config.breakpoint);

  // ブレークポイントが変わったら状態をリセット
  useEffect(() => {
    if (config.breakpoint !== prevBreakpoint) {
      setPrevBreakpoint(config.breakpoint);
      
      if (isMobile) {
        // モバイルに移行: collapsedを強制的にtrueにし、drawerは閉じる
        setCollapsed(true);
        setDrawerOpen(false);
      } else {
        // デスクトップ/タブレットに移行: drawerを閉じ、collapsedはdefaultに戻す
        setDrawerOpen(false);
        setCollapsed(config.defaultCollapsed);
      }
    }
  }, [config.breakpoint, config.defaultCollapsed, prevBreakpoint, isMobile]);

  // モバイルDrawer操作
  const openDrawer = () => setDrawerOpen(true);
  const closeDrawer = () => setDrawerOpen(false);

  // Desktop/Tablet折りたたみ操作
  const toggleCollapsed = () => setCollapsed(prev => !prev);

  const style = useMemo<React.CSSProperties>(
    () => ({
      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      willChange: "width, transform",
    }),
    []
  );

  return { 
    isMobile,
    collapsed, 
    drawerOpen,
    openDrawer,
    closeDrawer,
    toggleCollapsed,
    config, 
    style 
  };
}

export default useSidebar;
