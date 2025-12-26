/**
 * Feature Flags ViewModel Hook
 *
 * @module shared/hooks/useFeatureFlags
 *
 * UI コンポーネントは直接 isFeatureEnabled を呼び出さず、
 * このフックを通じて Feature Flags の状態を取得する。
 * これにより MVVM パターンに準拠し、UI はステートレスに保たれる。
 *
 * @example
 * ```tsx
 * // ViewModel (コンポーネント内)
 * const { showNewReport, showExperimental } = useFeatureFlags();
 *
 * // UI
 * {showNewReport && <NavLink to="/experimental/new-report">新レポート</NavLink>}
 * ```
 */

import { useMemo } from "react";
import { isFeatureEnabled, type FeatureFlagKey } from "../config/featureFlags";

/**
 * Feature Flags の状態を返す ViewModel フック
 *
 * @returns 各機能の表示可否を示す boolean プロパティを持つオブジェクト
 */
export const useFeatureFlags = () => {
  return useMemo(
    () => ({
      /**
       * 新レポート機能を表示するか
       * VITE_FF_NEW_REPORT=true で有効
       */
      showNewReport: isFeatureEnabled("NEW_REPORT"),

      /**
       * 新サイドバー機能を表示するか
       * VITE_FF_NEW_SIDEBAR=true で有効
       */
      showNewSidebar: isFeatureEnabled("NEW_SIDEBAR"),

      /**
       * 実験的機能を表示するか
       * VITE_FF_EXPERIMENTAL=true で有効
       */
      showExperimental: isFeatureEnabled("EXPERIMENTAL"),

      // ===========================================================
      // ページ単位の未完成機能フラグ
      // ===========================================================

      /**
       * 工場帳簿ページを表示するか
       * VITE_FF_FACTORY_REPORT=true で有効
       */
      showFactoryReport: isFeatureEnabled("FACTORY_REPORT"),

      /**
       * 予約表ページを表示するか
       * VITE_FF_RESERVATION_DAILY=true で有効
       */
      showReservationDaily: isFeatureEnabled("RESERVATION_DAILY"),

      // ===========================================================
      // 部品単位の未完成機能フラグ
      // ===========================================================

      /**
       * マニュアル動画機能を表示するか
       * VITE_FF_MANUAL_VIDEO=true で有効
       */
      showManualVideo: isFeatureEnabled("MANUAL_VIDEO"),

      /**
       * 任意のフラグをチェック (動的に必要な場合)
       */
      isEnabled: (key: FeatureFlagKey) => isFeatureEnabled(key),
    }),
    [],
  );
};

export type FeatureFlagsViewModel = ReturnType<typeof useFeatureFlags>;
