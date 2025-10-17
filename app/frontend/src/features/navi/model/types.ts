// features/navi/model/types.ts
// ナビ機能のDomain型定義

/**
 * カテゴリとテンプレートのマッピング構造
 */
export interface CategoryTemplate {
  title: string;
  tag: string[];
}

export type CategoryDataMap = Record<string, CategoryTemplate[]>;

/**
 * チャットの状態
 */
export interface ChatState {
  category: string;
  tags: string[];
  template: string;
  question: string;
  answer: string;
  loading: boolean;
  pdfUrl: string | null;
  currentStep: number;
}

/**
 * PDF表示の状態
 */
export interface PdfPreviewState {
  pdfToShow: string | null;
  pdfModalVisible: boolean;
}

/**
 * チャット回答結果（Domain Model）
 */
export interface ChatAnswer {
  answer: string;
  pdfUrl?: string | null;
}

/**
 * ステップインジケーター用のアイテム
 */
export interface StepItem {
  title: string;
  description: string;
}
