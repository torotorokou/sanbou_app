import React from 'react';

// レスポンシブデザイン用のブレークポイント定義 - シンプル版
export const BREAKPOINTS = {
    // モバイル (0px - 767px)
    mobile: '(max-width: 767px)',

    // タブレット (768px - 1199px) - 範囲を拡大してシンプル化
    tablet: '(min-width: 768px) and (max-width: 1199px)',

    // デスクトップ (1200px以上) - 統合してシンプル化
    desktop: '(min-width: 1200px)',

    // 便利なヘルパー
    mobileOnly: '(max-width: 767px)',
    tabletUp: '(min-width: 768px)',
    desktopUp: '(min-width: 1200px)', // 1200px以上をデスクトップとする
} as const;

// メディアクエリフック用のヘルパー
export const useMediaQuery = (query: string): boolean => {
    if (typeof window === 'undefined') return false;

    const mediaQuery = window.matchMedia(query);
    const [matches, setMatches] = React.useState(mediaQuery.matches);

    React.useEffect(() => {
        const handler = (event: MediaQueryListEvent) =>
            setMatches(event.matches);
        mediaQuery.addListener(handler);
        return () => mediaQuery.removeListener(handler);
    }, [mediaQuery]);

    return matches;
};

// デバイスタイプ判定フック - シンプル版
export const useDeviceType = () => {
    const isMobile = useMediaQuery(BREAKPOINTS.mobile);
    const isTablet = useMediaQuery(BREAKPOINTS.tablet);
    const isDesktop = useMediaQuery(BREAKPOINTS.desktop);

    return {
        isMobile,
        isTablet,
        isDesktop,
        isMobileOrTablet: isMobile || isTablet,

        // 後方互換性のために残す（廃止予定）
        isSmallDesktop: isDesktop, // デスクトップに統合
        isMediumDesktop: isDesktop, // デスクトップに統合
        isLargeDesktop: isDesktop, // デスクトップに統合
        shouldAutoCollapse: isMobile || isTablet, // モバイル・タブレットで自動縮小
        shouldForceCollapse: isMobile, // モバイルで強制縮小
    };
};
