import { useMemo } from 'react';
import { useDeviceType } from './useResponsive';

/**
 * レイアウトとスタイリングのロジックを管理するフック
 *
 * 🎯 目的：
 * - インラインスタイルの複雑性を分離
 * - レスポンシブデザインの一元管理
 * - デザインシステムの整合性を保つ
 */
export const useReportLayoutStyles = () => {
    const { isMobile, isTablet, isSmallDesktop, isMobileOrTablet } =
        useDeviceType();

    const styles = useMemo(
        () => ({
            container: {
                padding: isMobile ? 12 : isTablet ? 16 : 24,
            },
            mainLayout: {
                display: 'flex',
                flexDirection: isMobileOrTablet ? 'column' : 'row',
                gap: isMobile ? 12 : isTablet ? 16 : 24,
                alignItems: isMobileOrTablet ? 'stretch' : 'stretch',
                flexGrow: 1,
                marginTop: isMobile ? 8 : 16,
                minHeight: isMobileOrTablet ? 'auto' : '80vh',
                // スクロール可能にする
                maxHeight: isMobileOrTablet ? 'none' : '80vh',
                overflowY: isMobileOrTablet ? 'visible' : 'auto',
            },
            leftPanel: {
                display: 'flex',
                flexDirection: 'column' as const,
                gap: isMobile ? 12 : 16,
                width: isMobileOrTablet ? '100%' : isSmallDesktop ? 320 : 380,
                flexShrink: isMobileOrTablet ? 1 : 0,
                order: isMobileOrTablet ? 2 : 1,
            },
            centerPanel: {
                display: isMobileOrTablet ? 'none' : 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                width: isSmallDesktop ? '60px' : '100px',
                minWidth: isSmallDesktop ? '60px' : '100px',
                maxWidth: isSmallDesktop ? '60px' : '100px',
                minHeight: '100%',
                flexShrink: 0,
                flexGrow: 0,
                order: 2,
                boxSizing: 'border-box',
            },
            rightPanel: {
                flex: 1,
                minWidth: isMobile
                    ? '100%'
                    : isTablet
                    ? 400
                    : isSmallDesktop
                    ? 500
                    : 600,
                height: isMobileOrTablet ? 'auto' : '80vh',
                maxHeight: isMobileOrTablet ? 'none' : '80vh',
                display: 'flex',
                flexDirection: 'column' as const,
                order: isMobileOrTablet ? 1 : 3,
                overflowY: isMobileOrTablet ? 'visible' : 'auto',
            },
            previewContainer: {
                display: 'flex',
                flex: 1,
                gap: isMobile ? 8 : 16,
                alignItems: 'center',
                flexDirection: isMobile ? 'column' : 'row',
            },
            previewArea: {
                flex: 1,
                height: isMobile ? '50vh' : '100%',
                width: isMobile ? '100%' : 'auto',
                border: '1px solid #ccc',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
                background: '#fafafa',
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
        [isMobile, isTablet, isSmallDesktop, isMobileOrTablet]
    );

    return styles;
};
