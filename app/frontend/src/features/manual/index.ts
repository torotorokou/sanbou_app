// src/features/manual/index.ts
// Public API for Manual Feature

// ============================================================================
// Model (Types)
// ============================================================================

export type {
  ManualSectionChunk,
  RagMetadata,
  ManualSummary,
  ManualDetail,
  ManualListResponse,
  ManualCatalogResponse,
} from './model/manual.types';

// ============================================================================
// API
// ============================================================================

export { manualsApi } from './api/manualsApi';
export { default as manualsApiDefault } from './api/manualsApi';
export { useManualsStore } from './model/manuals.store';
