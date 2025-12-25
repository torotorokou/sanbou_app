// features/navi/model/types.ts
// ナビ機能のDomain型定義

import type { ReactNode } from 'react';

/**
 * サイドバーメニュー項目の型定義
 */
export interface MenuItem {
  key: string;
  label: ReactNode;
  icon?: ReactNode;
  hidden?: boolean;
  children?: MenuItem[];
  path?: string;
  [extra: string]: unknown;
}

/**
 * メニュー項目のフィルタリング用ユーティリティ型
 * hidden: true のアイテムを再帰的に除外
 */
export function filterMenuItems(items: MenuItem[] = []): MenuItem[] {
  return items
    .filter((i) => !i.hidden)
    .map((i) => {
      const copy: MenuItem = { ...i };
      if (Array.isArray(i.children)) {
        const children = filterMenuItems(i.children);
        if (children.length) copy.children = children;
        else delete copy.children;
      }
      return copy;
    });
}

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

/**
 * RAGチャットエラークラス
 */
export class RagChatError extends Error {
  constructor(
    public code: string,
    public detail: string,
    public hint?: string
  ) {
    super(detail);
    this.name = 'RagChatError';
  }
}
