/**
 * Manual Domain Types
 * マニュアル機能のドメインモデル定義
 */

export type ManualDoc = {
  docId: string;
  title: string;
  mimeType: string;
  size?: number;
  updatedAt?: string;
  downloadUrl: string; // /core_api/manual/docs/...
  category?: string;
  tags?: string[];
};

export type ManualSearchQuery = {
  q: string;
  tags?: string[];
  category?: string;
  limit?: number;
  offset?: number;
};

export type ManualSearchResult = {
  items: ManualDoc[];
  total: number;
  query: ManualSearchQuery;
};

export type ManualTocItem = {
  id: string;
  title: string;
  docId?: string;
  children?: ManualTocItem[];
  level?: number;
};

export type ManualCategory = {
  id: string;
  name: string;
  description?: string;
  count?: number;
};

export type ManualSearchParams = {
  keyword?: string;
  tags?: string[];
  category?: string;
};
