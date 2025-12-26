/**
 * 実験的ページ (Feature Flag で制御されるページ群)
 *
 * @module pages/experimental
 *
 * このディレクトリには VITE_FF_* フラグで制御される
 * 途中機能のページを配置します。
 *
 * 使用方法:
 * 1. ページコンポーネントをこのディレクトリに作成
 * 2. AppRoutes.tsx で isFeatureEnabled() を使ってルート接続
 * 3. フラグ OFF の環境では URL 直打ちでも 404 になる
 */

// New Report Page (VITE_FF_NEW_REPORT=true で有効)
export { NewReportPage } from "./NewReportPage";
