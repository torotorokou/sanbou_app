/**
 * Feature Flags (機能フラグ) の型安全な管理
 *
 * @module shared/config/featureFlags
 *
 * 途中機能を本番から隔離しつつ、dev/stg環境では有効化できる仕組み。
 * フラグOFFの場合、該当ルートは Routes に含まれず URL直打ちでも404となる。
 *
 * ========================================
 * 使用方法
 * ========================================
 * 1. 新しいフラグを追加:
 *    - FEATURE_FLAGS オブジェクトにキーを追加
 *    - env ファイルに VITE_FF_<KEY>=true を追加
 *
 * 2. ルート未接続:
 *    - AppRoutes.tsx で isFeatureEnabled('NEW_FEATURE') を使用
 *    - falseの場合、該当 Route を配列に含めない
 *
 * 3. UI露出制御:
 *    - ViewModel で isFeatureEnabled を呼び出し、boolean を返す
 *    - UI は vm.showXXX && <Component /> で表示制御
 *
 * @example
 * ```tsx
 * // ルート定義での使用例
 * {isFeatureEnabled('NEW_REPORT') && (
 *   <Route path="/report/new" element={<NewReportPage />} />
 * )}
 *
 * // または配列スプレッドで
 * ...(isFeatureEnabled('NEW_REPORT') ? [{ path: '/report/new', element: <NewReportPage /> }] : [])
 * ```
 */

// ===========================================================
// 環境変数から読み取るフラグのプレフィックス
// Vite では VITE_ プレフィックスのみがクライアントに公開される
// ===========================================================
const FF_PREFIX = "VITE_FF_" as const;

// ===========================================================
// フラグ定義: as const で型安全性を確保
// 新しいフラグは必ずここに追加すること
// ===========================================================
export const FEATURE_FLAGS = {
  /**
   * 新レポート機能 (例: 実験的な帳票機能)
   * 環境変数: VITE_FF_NEW_REPORT=true
   */
  NEW_REPORT: "NEW_REPORT",

  /**
   * 新サイドバー機能 (例: サイドバーの新UIデザイン)
   * 環境変数: VITE_FF_NEW_SIDEBAR=true
   */
  NEW_SIDEBAR: "NEW_SIDEBAR",

  /**
   * 実験的機能 (例: テスト用の機能)
   * 環境変数: VITE_FF_EXPERIMENTAL=true
   */
  EXPERIMENTAL: "EXPERIMENTAL",

  // ===========================================================
  // ページ単位の未完成機能フラグ
  // OFF の場合はルート未接続となり、URL直打ちでも404
  // ===========================================================

  /**
   * 工場帳簿ページ
   * 環境変数: VITE_FF_FACTORY_REPORT=true
   * OFF: ルート未接続、ナビ非表示
   */
  FACTORY_REPORT: "FACTORY_REPORT",

  /**
   * 予約表ページ
   * 環境変数: VITE_FF_RESERVATION_DAILY=true
   * OFF: ルート未接続、ナビ非表示
   */
  RESERVATION_DAILY: "RESERVATION_DAILY",

  // ===========================================================
  // 部品単位の未完成機能フラグ
  // ページは表示されるが、該当部品は準備中パネルに差し替え
  // ===========================================================

  /**
   * マニュアル動画機能
   * 環境変数: VITE_FF_MANUAL_VIDEO=true
   * OFF: 動画セクションに準備中パネルを表示
   */
  MANUAL_VIDEO: "MANUAL_VIDEO",
} as const;

// ===========================================================
// 型定義: フラグキーのユニオン型
// ===========================================================
export type FeatureFlagKey = keyof typeof FEATURE_FLAGS;
export type FeatureFlagValue = (typeof FEATURE_FLAGS)[FeatureFlagKey];

// ===========================================================
// フラグ値の取得関数
// ===========================================================

/**
 * 環境変数から Feature Flag の値を取得
 *
 * @param key - FEATURE_FLAGS のキー (typo は型エラーになる)
 * @returns フラグが有効な場合 true、それ以外は false
 *
 * @example
 * ```tsx
 * if (isFeatureEnabled('NEW_REPORT')) {
 *   // NEW_REPORT 機能が有効な場合の処理
 * }
 * ```
 */
export const isFeatureEnabled = (key: FeatureFlagKey): boolean => {
  const flagName = FEATURE_FLAGS[key];
  const envKey = `${FF_PREFIX}${flagName}`;

  // import.meta.env から読み取り
  // Vite は string として埋め込むため、'true' 文字列と比較
  const value = import.meta.env[envKey];

  // 'true', '1', 'yes' を許容 (大文字小文字不問)
  if (typeof value === "string") {
    return ["true", "1", "yes"].includes(value.toLowerCase());
  }

  // デフォルトは OFF (安全側に倒す)
  return false;
};

/**
 * 全フラグの現在の状態を取得 (デバッグ用)
 *
 * @returns 全フラグの有効/無効状態のオブジェクト
 *
 * @example
 * ```tsx
 * console.log(getAllFeatureFlags());
 * // { NEW_REPORT: false, NEW_SIDEBAR: true, EXPERIMENTAL: false }
 * ```
 */
export const getAllFeatureFlags = (): Record<FeatureFlagKey, boolean> => {
  const flags = {} as Record<FeatureFlagKey, boolean>;

  for (const key of Object.keys(FEATURE_FLAGS) as FeatureFlagKey[]) {
    flags[key] = isFeatureEnabled(key);
  }

  return flags;
};

/**
 * フラグが有効な場合のみ値を返すヘルパー
 *
 * @param key - FEATURE_FLAGS のキー
 * @param value - フラグが有効な場合に返す値
 * @returns フラグが有効な場合は value、無効な場合は undefined
 *
 * @example
 * ```tsx
 * // 配列に条件付きで要素を追加
 * const routes = [
 *   { path: '/', element: <Home /> },
 *   ...whenEnabled('NEW_REPORT', [{ path: '/report/new', element: <NewReport /> }]) ?? [],
 * ];
 * ```
 */
export const whenEnabled = <T>(
  key: FeatureFlagKey,
  value: T,
): T | undefined => {
  return isFeatureEnabled(key) ? value : undefined;
};
