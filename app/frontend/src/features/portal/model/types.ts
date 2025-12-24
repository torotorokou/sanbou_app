/**
 * PortalPageの型定義
 */
import type React from 'react';

export interface PortalCardProps {
  title: string;
  description: string;
  // ホバーで表示する詳しい説明（省略可）
  detail?: string;
  icon: React.ReactNode;
  link: string;
  // 任意のアクセント色（例: '#52c41a'）
  color?: string;
  // ボタン幅を外から制御（単位: px）。未指定時はデフォルトを使用。
  buttonWidth?: number;
  // カード全体のスケール（1 = 100%）。PortalPage から渡す。
  cardScale?: number;
  // 狭い画面向けのコンパクトレイアウト（説明非表示、アイコン左寄せ、height 縮小）
  compactLayout?: boolean;
  // sm 未満でボタンを非表示にする指示
  hideButton?: boolean;
  // sm 未満で小さなボタンを表示する（ボタンを非表示にする代わりに小さいものを右側に表示）
  smallButton?: boolean;
  // 高さのみをスケールする（例: sm 未満で 0.9 を渡す）
  heightScale?: number;
}

export interface Notice {
  id: string;
  title: string;
  summary: string;
  detail: string;
  date: string;
}
