/**
 * useAutoCloseSidebarOnRouteChange - ルート変更時のサイドバー自動クローズ
 *
 * 【役割】
 * - ブラウザの戻る/進むなど、メニュークリック以外の遷移でもDrawerを閉じる
 * - 初回マウント時は閉じない（初回レンダリングで勝手に閉じるのを防止）
 *
 * 【使用例】
 * ```tsx
 * // Sidebarコンポーネント内で呼び出す
 * useAutoCloseSidebarOnRouteChange({ isDrawerMode, closeDrawer });
 * ```
 */
import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

export interface UseAutoCloseSidebarOnRouteChangeOptions {
  /** 現在Drawerモードかどうか */
  isDrawerMode: boolean;
  /** Drawerを閉じる関数（親のuseSidebarから渡す） */
  closeDrawer: () => void;
}

/**
 * ルート変更を検知してDrawerモード時にサイドバーを自動クローズ
 *
 * - 初回マウント時は閉じない（isFirstRender フラグで制御）
 * - pathname変更時、Drawerモードなら closeDrawer() を呼ぶ
 * - close は冪等（すでに閉じていても問題なし）
 */
export function useAutoCloseSidebarOnRouteChange({
  isDrawerMode,
  closeDrawer,
}: UseAutoCloseSidebarOnRouteChangeOptions): void {
  const location = useLocation();

  // 初回マウントを判定するためのref
  const isFirstRender = useRef(true);
  const prevPathname = useRef(location.pathname);

  useEffect(() => {
    // 初回マウント時はスキップ
    if (isFirstRender.current) {
      isFirstRender.current = false;
      prevPathname.current = location.pathname;
      return;
    }

    // パスが変わった場合のみ処理
    if (location.pathname !== prevPathname.current) {
      prevPathname.current = location.pathname;

      // Drawerモードの場合のみ閉じる
      if (isDrawerMode) {
        closeDrawer();
      }
    }
  }, [location.pathname, isDrawerMode, closeDrawer]);
}
