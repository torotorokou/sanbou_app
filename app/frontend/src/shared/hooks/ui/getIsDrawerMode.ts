/**
 * getIsDrawerMode - Drawerモード判定の集約関数
 *
 * 【役割】
 * - サイドバーがDrawer（オーバーレイ）表示かどうかを判定
 * - プロジェクト内で唯一のDrawerモード判定ロジック
 *
 * 【定義】
 * - Drawerモード = モバイル幅（≤767px）かつ drawerMode設定がtrue
 * - デスクトップ/タブレットでは常にfalse（常時表示Siderモード）
 *
 * 【使用例】
 * ```tsx
 * const isDrawer = getIsDrawerMode(isMobile, config.drawerMode);
 * if (isDrawer) closeDrawer();
 * ```
 */

/**
 * Drawerモードかどうかを判定する純粋関数
 *
 * @param isMobile - モバイル幅かどうか（≤767px）
 * @param drawerMode - サイドバー設定のdrawerModeフラグ
 * @returns Drawerモードならtrue
 */
export function getIsDrawerMode(
  isMobile: boolean,
  drawerMode: boolean,
): boolean {
  return isMobile && drawerMode;
}
