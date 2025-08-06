import React from 'react';
import { useDeviceType } from './useResponsive';

export interface SidebarConfig {
    width: number;
    collapsedWidth: number;
    breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
    autoCollapse: boolean;
    forceCollapse: boolean;
    drawerMode: boolean;
}

export const useSidebarResponsive = (): SidebarConfig => {
    const { isMobile, isTablet, shouldAutoCollapse, shouldForceCollapse } =
        useDeviceType();

    return React.useMemo(() => {
        // モバイル設定
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

        // タブレット設定
        if (isTablet) {
            return {
                width: 200,
                collapsedWidth: 60,
                breakpoint: 'sm' as const,
                autoCollapse: true,
                forceCollapse: false,
                drawerMode: false,
            };
        }

        // 強制縮小（900px以下）
        if (shouldForceCollapse) {
            return {
                width: 220,
                collapsedWidth: 50,
                breakpoint: 'md' as const,
                autoCollapse: false,
                forceCollapse: true,
                drawerMode: false,
            };
        }

        // 自動縮小推奨（1200px以下）
        if (shouldAutoCollapse) {
            return {
                width: 220,
                collapsedWidth: 70,
                breakpoint: 'lg' as const,
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
    }, [isMobile, isTablet, shouldAutoCollapse, shouldForceCollapse]);
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
