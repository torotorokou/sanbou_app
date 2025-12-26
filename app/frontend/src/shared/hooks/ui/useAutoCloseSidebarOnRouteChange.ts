/**
 * ルート変更時にDrawerモードのサイドバーを自動で閉じるhook
 *
 * FSD + MVVM アーキテクチャに準拠:
 * - Shared Layer: プロジェクト全体で再利用可能なViewModel hook
 * - 副作用管理: useEffect でルート変更を監視
 * - ビジネスロジック: Drawerモード時の自動クローズ
 *
 * @description
 * 用途:
 * - ブラウザの戻る/進むボタンでルート変更した際の保険
 * - 外部からの遷移でもDrawerを閉じる
 *
 * 動作:
 * 1. useLocation() で pathname の変化を検知
 * 2. 初回マウントでは何もしない（初回レンダリングで勝手に閉じるのを防ぐ）
 * 3. 2回目以降の pathname 変更時、Drawerモードなら closeSidebar() を呼ぶ
 * 4. closeSidebar() は冪等性があるので、多重に呼ばれても問題なし
 */

import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { getIsDrawerMode } from "./getIsDrawerMode";
import type { SidebarConfig } from "./useSidebar";

export interface UseAutoCloseSidebarOnRouteChangeParams {
  /** useSidebar()から取得したconfig */
  config: SidebarConfig;
  /** モバイル判定（useSidebar()から取得） */
  isMobile: boolean;
  /** Drawerを閉じる関数（useSidebar()から取得） */
  closeDrawer: () => void;
}

/**
 * ルート変更時にDrawerモードのサイドバーを自動で閉じる
 *
 * @param params - config, isMobile, closeDrawer
 *
 * @example
 * ```tsx
 * // Layout または Sidebar 内で呼び出す
 * const { config, isMobile, closeDrawer } = useSidebar();
 * useAutoCloseSidebarOnRouteChange({ config, isMobile, closeDrawer });
 * ```
 */
export function useAutoCloseSidebarOnRouteChange({
  config,
  isMobile,
  closeDrawer,
}: UseAutoCloseSidebarOnRouteChangeParams): void {
  const location = useLocation();
  const isFirstMount = useRef(true);

  useEffect(() => {
    // 初回マウントでは何もしない
    if (isFirstMount.current) {
      isFirstMount.current = false;
      return;
    }

    // Drawerモードの場合のみ閉じる
    const isDrawerMode = getIsDrawerMode(config);
    if (isDrawerMode && isMobile) {
      closeDrawer();
    }
  }, [location.pathname, config, isMobile, closeDrawer]);
}
