/**
 * Drawerモード判定を集約
 * サイドバーがオーバーレイDrawerとして表示される状態かどうかを判定
 *
 * FSD + MVVM アーキテクチャに準拠:
 * - Shared Layer: プロジェクト全体で再利用可能なユーティリティ
 * - 状態管理フック（useSidebar）の戻り値から判定
 *
 * @description
 * Drawerモードは以下の条件で決定:
 * - モバイル（≤767px）: drawerMode = true
 * - タブレット（768-1280px）: drawerMode = false
 * - デスクトップ（≥1281px）: drawerMode = false
 *
 * この判定を集約することで、以下のメリット:
 * - 画面幅判定ロジックの一元化
 * - isDrawerMode の使用箇所での一貫性担保
 * - 将来的な判定条件変更への対応が容易
 */

import type { SidebarConfig } from "./useSidebar";

// 型の再エクスポート（互換性のため）
export type { SidebarConfig };

/**
 * Drawerモードかどうかを判定
 *
 * @param config - useSidebar()から取得したconfig
 * @returns true: オーバーレイDrawer表示、false: 常時表示Sider
 *
 * @example
 * ```tsx
 * const { config } = useSidebar();
 * const isDrawer = getIsDrawerMode(config);
 * if (isDrawer) {
 *   // Drawerモードの処理
 * }
 * ```
 */
export function getIsDrawerMode(config: SidebarConfig): boolean {
  return config.drawerMode;
}

/**
 * Drawerモードで開いているかどうかを判定
 *
 * @param config - useSidebar()から取得したconfig
 * @param isMobile - モバイル判定フラグ
 * @param drawerOpen - Drawer開閉状態
 * @returns true: Drawerモードで開いている、false: それ以外
 *
 * @example
 * ```tsx
 * const { config, isMobile, drawerOpen } = useSidebar();
 * const isOpen = getIsDrawerModeAndOpen(config, isMobile, drawerOpen);
 * ```
 */
export function getIsDrawerModeAndOpen(
  config: SidebarConfig,
  isMobile: boolean,
  drawerOpen: boolean,
): boolean {
  return getIsDrawerMode(config) && isMobile && drawerOpen;
}
