/**
 * useSidebarNavigation - サイドバーメニュークリック時のナビゲーション処理
 *
 * 【役割】
 * - メニュークリック時にDrawerモードなら自動でサイドバーを閉じる
 * - ViewModelとしてナビゲーション + サイドバー閉じる処理を一元管理
 *
 * 【使用例】
 * ```tsx
 * const { handleMenuClick } = useSidebarNavigation({ isDrawerMode, closeDrawer });
 * <Menu onClick={handleMenuClick} ... />
 * ```
 */
import { useCallback } from "react";

export interface UseSidebarNavigationOptions {
  /** 現在Drawerモードかどうか */
  isDrawerMode: boolean;
  /** Drawerを閉じる関数（親のuseSidebarから渡す） */
  closeDrawer: () => void;
}

export interface UseSidebarNavigationReturn {
  /** メニュークリック時のハンドラ（Drawerモード時に自動クローズ） */
  handleMenuClick: () => void;
}

/**
 * サイドバーメニューナビゲーション用ViewModel
 *
 * - メニュークリック時、Drawerモードなら自動でcloseDrawer()を呼ぶ
 * - Linkによる遷移は既存のまま（react-router-dom）
 * - このhookはクリック後の副作用（Drawer閉じる）のみ担当
 */
export function useSidebarNavigation({
  isDrawerMode,
  closeDrawer,
}: UseSidebarNavigationOptions): UseSidebarNavigationReturn {
  const handleMenuClick = useCallback(() => {
    if (isDrawerMode) {
      closeDrawer();
    }
  }, [isDrawerMode, closeDrawer]);

  return {
    handleMenuClick,
  };
}
