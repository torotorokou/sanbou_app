/**
 * Manual Feature - Public API
 * MVVM+SOLID アーキテクチャに準拠した barrel export
 */

// Domain Types
export * from './domain/types/manual.types';
export * from './domain/types/shogun.types';

// Ports
export * from './ports/repository';

// Application (ViewModels)
export { useManualSearch } from './application/useManualSearchVM';
export { useManualCategories } from './application/useManualCategoriesVM';
export { useManualDoc } from './application/useManualDocVM';
export { useManualToc } from './application/useManualTocVM';
export { useShogunDetail } from './application/useShogunDetailVM';
export { useShogunCatalog } from './application/useShogunCatalogVM';

// Infrastructure
export { ManualRepositoryImpl } from './infrastructure/manual.repository';
export { ShogunClient } from './infrastructure/shogun.client';
export { ShogunClient as ShogunClientDefault } from './infrastructure/shogun.client'; // Legacy alias
export { ManualClient } from './infrastructure/manual.client';

// UI Components (re-export with original names)
export { ManualResultList } from './ui/components/ManualResultList';
export { ManualViewer } from './ui/components/ManualViewer';
export { ManualSearchBox } from './ui/components/ManualSearchBox';
export { default as ManualDetailPage } from './ui/components/ManualDetailPage';
export { default as ManualDetailRoute } from './ui/components/ManualDetailPage'; // Alias for routing
export { ManualModal } from './ui/components/ShogunModal';  // ManualModal is the named export
export { DetailContent } from './ui/components/DetailContent';
