/**
 * Manual Pages Public API
 * FSD: ページ層の公開インターフェース
 */

// 検索ページ
export { default as ManualSearchPage } from "./search";

// 将軍マニュアルページ
export { default as ShogunManualListPage } from "./shogun";
export { default as ShogunManualDetailPage } from "./shogun/DetailPage";

// マスターページ
export { default as VendorMasterPage } from "./vendor";

// レガシーエイリアス (後方互換性のため)
export { default as GlobalManualSearchPage } from "./search";
export { default as ManualDetailPage } from "./shogun/DetailPage";

// モーダルはfeatures/manual/shogun/uiから直接エクスポート
export { ManualModal } from "@/features/manual";
// routing-backed detail component (used as overlay when backgroundLocation exists)
export { ManualDetailRoute } from "@/features/manual";
