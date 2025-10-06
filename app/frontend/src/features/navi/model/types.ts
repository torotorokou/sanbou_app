// features/navi/model/types.ts
// ナビゲーション・メニュー関連の型定義

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
        .filter(i => !i.hidden)
        .map(i => {
            const copy: MenuItem = { ...i };
            if (Array.isArray(i.children)) {
                const children = filterMenuItems(i.children);
                if (children.length) copy.children = children;
                else delete copy.children;
            }
            return copy;
        });
}
