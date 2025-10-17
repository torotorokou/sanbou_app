/**
 * Manual Feature Public API
 * FSD: Feature層の公開インターフェース
 */

// ============================================================================
// Legacy Exports (to be migrated)
// ============================================================================

export type {
  ManualSectionChunk,
  RagMetadata,
  ManualSummary,
  ManualDetail,
  ManualListResponse,
  ManualCatalogResponse,
} from './model/manual.types';

export { manualsApi } from './api/manualsApi';
export { default as manualsApiDefault } from './api/manualsApi';

// ============================================================================
// Search Feature (新しいBFF + FSD構造)
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
export type { ManualItem, ManualSection } from './shogun/model/types';

// Shogun UI Components
export { default as ShogunManualList } from './shogun/ui/ShogunManualList';
export { default as ManualModal } from './shogun/ui/ManualModal';
export { default as DetailModal } from './shogun/ui/DetailModal';

// ============================================================================
// Shared Utilities
// ============================================================================

// Shared Hooks
export { useManualDoc } from './shared/useManualDoc';
export { useManualToc } from './shared/useManualToc';
export { useManualCategories } from './shared/useManualCategories';
