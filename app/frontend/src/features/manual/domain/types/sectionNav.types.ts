/**
 * Section Navigation Types
 * ページ内セクションナビゲーションの型定義
 */
import type { ReactNode } from "react";

/**
 * セクションナビゲーション項目の種別
 */
export type SectionNavKind = "scroll" | "route";

/**
 * セクションナビゲーション項目
 */
export interface SectionNavItem {
  /** 一意なID（例：'vendor', 'customer'） */
  id: string;
  /** 表示名 */
  label: string;
  /** 項目の種別（scroll: ページ内スクロール, route: ページ遷移） */
  kind: SectionNavKind;
  /** 対象（scroll: "#vendor", route: "/masters/vendor"） */
  target: string;
  /** アイコン（任意） */
  icon?: ReactNode;
  /** バッジカウント（任意） */
  count?: number;
}
