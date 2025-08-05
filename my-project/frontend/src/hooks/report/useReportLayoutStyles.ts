import { useMemo } from 'react';
import { useDeviceType } from '../ui/useResponsive';
import { customTokens } from '../../theme';

/**
 * レイアウトとスタイリングのロジックを管理するフック - シンプル版
 *
 * 🎯 目的：
 * - 複雑なブレークポイントを3つに統合（Mobile, Tablet, Desktop）
 * - レスポンシブデザインの一元管理をより簡潔に
 * - 保守性を向上させるためのシンプルなサイズ体系
 */
export const useReportLayoutStyles = () => {
    const { isMobile, isTablet, isDesktop, isMobileOrTablet } = useDeviceType();

    // デバッグ情報（一時的）
    // console.log('useReportLayoutStyles - Device Info:', {
    //     isMobile,
    //     isTablet,
    //     isDesktop,
    //     isMobileOrTablet,
    //     windowWidth: typeof window !== 'undefined' ? window.innerWidth : 'undefined'
    // });

    const styles = useMemo(
        () => ({
            container: {
                padding: isMobile ? 12 : isTablet ? 16 : 24,
            },
            mainLayout: {
                display: 'flex',
                flexDirection: (isMobileOrTablet ? 'column' : 'row') as
                    | 'row'
                    | 'column',
                gap: isMobile ? 12 : isTablet ? 16 : 24,
                alignItems: isMobileOrTablet ? 'stretch' : 'flex-start',
                flexGrow: 1,
                marginTop: isMobile ? 8 : 16,
                minHeight: isMobileOrTablet ? 'auto' : '80vh',
                maxHeight: isMobileOrTablet ? 'none' : '80vh',
                overflowY: (isMobileOrTablet ? 'visible' : 'auto') as
                    | 'auto'
                    | 'visible',
                width: '100%',
                boxSizing: 'border-box' as const,
            },
            leftPanel: {
                display: 'flex',
                flexDirection: 'column' as const,
                gap: isMobile ? 12 : 16,
                // シンプルな3段階のサイズ設定
                width: isMobileOrTablet ? '100%' : '300px', // デスクトップは統一して300px
                minWidth: isMobileOrTablet ? 'auto' : '300px',
                maxWidth: isMobileOrTablet ? 'none' : '300px',
                flexShrink: isMobileOrTablet ? 1 : 0,
                flexGrow: isMobileOrTablet ? 1 : 0,
                order: isMobileOrTablet ? 3 : 1,
                boxSizing: 'border-box' as const,
            },
            centerPanel: {
                display: isMobileOrTablet ? 'none' : 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                width: '60px', // 統一して60px
                minWidth: '60px',
                maxWidth: '60px',
                flexShrink: 0,
                flexGrow: 0,
                order: 2,
                boxSizing: 'border-box' as const,
            },
            // モバイル・タブレット用のアクションセクション
            mobileActionsPanel: {
                display: isMobileOrTablet ? 'flex' : 'none',
                width: '100%',
                padding: isMobile ? 12 : 16,
                backgroundColor: customTokens.colorBgCard,
                borderRadius: 8,
                marginBottom: isMobile ? 12 : 16,
                boxShadow: `0 2px 8px ${customTokens.shadowLight}`,
                order: 3,
            },
            rightPanel: {
                // プレビューパネル - シンプルな3段階設定
                ...(isMobileOrTablet
                    ? {
                          width: '100%',
                          flex: '1 1 auto',
                          height: 'auto',
                          maxHeight: 'none',
                      }
                    : {
                          flex: '1 1 auto', // 残りのスペースを全て使用
                          minWidth: isTablet ? 500 : 600, // シンプルに2段階
                          height: '80vh',
                          maxHeight: '80vh',
                      }),
                display: 'flex',
                flexDirection: 'column' as const,
                order: isMobileOrTablet ? 1 : 3,
                overflowY: (isMobileOrTablet ? 'visible' : 'auto') as
                    | 'auto'
                    | 'visible',
            },
            previewContainer: {
                display: 'flex',
                flex: 1,
                gap: isMobile ? 8 : 16,
                alignItems: 'center',
                flexDirection: (isMobile ? 'column' : 'row') as
                    | 'row'
                    | 'column',
            },
            previewArea: {
                flex: 1,
                height: isMobile ? '50vh' : '100%',
                width: isMobile ? '100%' : 'auto',
                border: `1px solid ${customTokens.colorBorder}`,
                borderRadius: 8,
                boxShadow: `0 2px 8px ${customTokens.shadowLight}`,
                background: customTokens.colorBgCard,
                overflow: 'hidden',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
            },
            downloadSection: {
                display: 'flex',
                flexDirection: isMobile ? 'row' : 'column',
                justifyContent: 'center',
                alignItems: 'center',
                width: isMobile ? '100%' : 120,
                gap: 8,
                marginTop: isMobile ? 12 : 0,
            },
            sampleThumbnail: {
                className: 'sample-thumbnail',
            },
        }),
        [isMobile, isTablet, isMobileOrTablet] // シンプルな依存配列
    );

    return styles;
};
