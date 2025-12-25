/**
 * Shogun Manual Types
 * 将軍マニュアル機能の型定義
 */
import type { ReactNode } from 'react';

// ============================================================================
// Catalog / List Types (カタログ・一覧表示用)
// ============================================================================

export interface ManualItem {
  id: string;
  title: string;
  description?: string;
  flowUrl?: string;
  videoUrl?: string;
  thumbnailUrl?: string;
  route?: string;
  tags?: string[];
}

export interface ManualSection {
  id: string;
  title: string;
  icon?: ReactNode;
  items: ManualItem[];
}

// ============================================================================
// Detail Types (詳細表示用 - 旧 manual.types.ts から移動)
// ============================================================================

export type ManualSectionChunk = {
  title: string;
  anchor: string; // s-<n>
  html?: string;
  markdown?: string;
};

export type RagMetadata = {
  doc_id: string;
  page_title: string;
  section_id: string; // s-<n>
  url: string;
  category?: string;
  tags: string[];
  version: string;
  lang: string;
  breadcrumbs: string[];
};

export type ManualSummary = {
  id: string;
  title: string;
  description?: string;
  category?: string;
  tags: string[];
  version?: string;
};

export type ManualDetail = ManualSummary & {
  sections: ManualSectionChunk[];
  rag: RagMetadata[];
};

export type ManualListResponse = {
  items: ManualSummary[];
  page: number;
  size: number;
  total: number;
};

export type ManualCatalogResponse = {
  sections: Array<{
    id: string;
    title: string;
    icon?: string;
    items: Array<{
      id: string;
      title: string;
      description?: string;
      route?: string;
      tags: string[];
      flow_url?: string;
      video_url?: string;
    }>;
  }>;
};
