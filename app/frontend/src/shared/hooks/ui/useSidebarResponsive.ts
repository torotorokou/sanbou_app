import React from 'react';
import { useWindowSize } from './useWindowSize';

export interface SidebarConfig {
    width: number;
    collapsedWidth: number;
    breakpoint: 'xs' | 'md' | 'xl';  // 3-tier only: xs(≤767) / md(768-1199) / xl(≥1200)
    autoCollapse: boolean;
    forceCollapse: boolean;
    drawerMode: boolean;
}

export const useSidebarResponsive = (): SidebarConfig => {
    const { isMobile, isTablet } = useWindowSize();

    return React.useMemo(() => {
        // モバイル: ドロワー
        if (isMobile) {
            return {
                width: 280,
                collapsedWidth: 0,
                breakpoint: 'xs' as const,
                autoCollapse: false,
                forceCollapse: true,
                drawerMode: true,
            };
        }

        // タブレット: 自動縮小
        if (isTablet) {
            return {
                width: 200,
                collapsedWidth: 60,
                breakpoint: 'md' as const,  // 768px = BP.tabletMin
                autoCollapse: true,
                forceCollapse: false,
                drawerMode: false,
            };
        }

        // デスクトップ（デフォルト）設定
        return {
            width: 250,
            collapsedWidth: 80,
            breakpoint: 'xl' as const,
            autoCollapse: false,
            forceCollapse: false,
            drawerMode: false,
        };
    }, [isMobile, isTablet]);
};

// サイドバー用のアニメーション設定
export const useSidebarAnimation = () => {
    return React.useMemo(
        () => ({
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            willChange: 'width, transform',
        }),
        []
    );
};
