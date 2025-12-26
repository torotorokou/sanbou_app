/**
 * サイドバーのナビゲーション処理を担当するViewModel hook
 *
 * FSD + MVVM アーキテクチャに準拠:
 * - Shared Layer: プロジェクト全体で再利用可能なViewModel hook
 * - ビジネスロジック: ナビゲーション後のDrawer自動クローズ
 * - 疎結合: UIコンポーネントから状態管理・遷移ロジックを分離
 *
 * @description
 * 責務:
 * 1. サイドバーメニューからのナビゲーション処理
 * 2. 遷移後、Drawerモードの場合のみサイドバーを閉じる
 * 3. デスクトップ/タブレットの常時表示サイドバーは閉じない
 *
 * 使用場面:
 * - サイドバーメニューのonClickハンドラ
 * - メニューアイテム内のカスタム遷移ボタン
 */

import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getIsDrawerMode } from "./getIsDrawerMode";
import type { SidebarConfig } from "./useSidebar";

export interface UseSidebarNavigationParams {
  /** useSidebar()から取得したconfig */
  config: SidebarConfig;
  /** モバイル判定（useSidebar()から取得） */
  isMobile: boolean;
  /** Drawerを閉じる関数（useSidebar()から取得） */
  closeDrawer: () => void;
}

export interface UseSidebarNavigationReturn {
  /**
   * メニューからのナビゲーション処理
   * @param to - 遷移先パス
   */
  navigateAndClose: (to: string) => void;
}

/**
 * サイドバーのナビゲーション処理hook
 *
 * @param params - config, isMobile, closeDrawer
 * @returns navigateAndClose - メニュークリック時の遷移関数
 *
 * @example
 * ```tsx
 * const { config, isMobile, closeDrawer } = useSidebar();
 * const { navigateAndClose } = useSidebarNavigation({
 *   config,
 *   isMobile,
 *   closeDrawer,
 * });
 *
 * // メニューアイテム内で使用
 * <button onClick={() => navigateAndClose('/path')}>ページへ</button>
 * ```
 */
export function useSidebarNavigation({
  config,
  isMobile,
  closeDrawer,
}: UseSidebarNavigationParams): UseSidebarNavigationReturn {
  const navigate = useNavigate();

  const navigateAndClose = useCallback(
    (to: string) => {
      // 1. ページ遷移を実行
      navigate(to);

      // 2. Drawerモードの場合のみサイドバーを閉じる
      const isDrawerMode = getIsDrawerMode(config);
      if (isDrawerMode && isMobile) {
        closeDrawer();
      }
    },
    [navigate, config, isMobile, closeDrawer],
  );

  return {
    navigateAndClose,
  };
}
