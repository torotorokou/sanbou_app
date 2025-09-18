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
