/**
 * Manual Feature Public API
 * FSD: Feature層の公開インターフェース
 */

// ============================================================================
// Search Feature (BFF + FSD構造)
// ============================================================================

// Search Types
export type {
  ManualDoc,
  ManualSearchQuery,
  ManualSearchResult,
  ManualTocItem,
  ManualCategory,
  ManualSearchParams
} from './shared/model/types';

// Search Hooks (ViewModel)
export { useManualSearch } from './search/hooks/useManualSearch';

// Search UI Components
export { ManualViewer } from './search/ui/ManualViewer';
export { ManualSearchBox } from './search/ui/ManualSearchBox';
export { ManualResultList } from './search/ui/ManualResultList';

// ============================================================================
// Shogun Feature (将軍マニュアル)
// ============================================================================

// Shogun Types
export type {
  ManualItem,
  ManualSection,
  ManualSectionChunk,
  RagMetadata,
  ManualSummary,
  ManualDetail,
  ManualListResponse,
  ManualCatalogResponse,
} from './shogun/model/types';

// Shogun API
export { ShogunClient } from './shogun/api/client';
export { default as ShogunClientDefault } from './shogun/api/client';

// Shogun Hooks (ViewModel)
export { useShogunDetail } from './shogun/hooks/useShogunDetail';
export { useShogunCatalog } from './shogun/hooks/useShogunCatalog';

// Shogun UI Components
export { ItemCard } from './shogun/ui/ItemCard';
export { SectionBlock } from './shogun/ui/SectionBlock';
export { FlowPane } from './shogun/ui/FlowPane';
export { VideoPane } from './shogun/ui/VideoPane';
// Export UI-controlled modal as `ManualModal` for page usage
export { ManualModal } from './shogun/ui/ShogunModal';
// Export routing-backed detail page component as `ManualDetailPage`
// Export routing-backed detail page component under a route-specific name to avoid collision with pages' ManualDetailPage
export { default as ManualDetailRoute } from './shogun/ui/ManualDetailPage';
export { DetailContent } from './shogun/ui/DetailContent';

// ============================================================================
// Shared Utilities
// ============================================================================

// Shared Hooks
export { useManualDoc } from './shared/useManualDoc';
export { useManualToc } from './shared/useManualToc';
export { useManualCategories } from './shared/useManualCategories';
