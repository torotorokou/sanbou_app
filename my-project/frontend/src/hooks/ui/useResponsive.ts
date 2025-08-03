import React from 'react';

// レスポンシブデザイン用のブレークポイント定義
export const BREAKPOINTS = {
    // スマートフォン (320px - 767px)
    mobile: '(max-width: 767px)',

    // タブレット (768px - 1023px)
    tablet: '(min-width: 768px) and (max-width: 1023px)',

    // 小さなデスクトップ・ラップトップ (1024px - 1365px)
    smallDesktop: '(min-width: 1024px) and (max-width: 1365px)',

    // 古いタイプのPC・半画面のPC (1366px - 1599px)
    mediumDesktop: '(min-width: 1366px) and (max-width: 1599px)',

    // フルHD以上のPC (1600px以上)
    largeDesktop: '(min-width: 1600px)',

    // 特定のサイズ
    mobileOnly: '(max-width: 767px)',
    tabletUp: '(min-width: 768px)',
    desktopUp: '(min-width: 1024px)',
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

// デバイスタイプ判定フック
export const useDeviceType = () => {
    const isMobile = useMediaQuery(BREAKPOINTS.mobile);
    const isTablet = useMediaQuery(BREAKPOINTS.tablet);
    const isSmallDesktop = useMediaQuery(BREAKPOINTS.smallDesktop);
    const isMediumDesktop = useMediaQuery(BREAKPOINTS.mediumDesktop);
    const isLargeDesktop = useMediaQuery(BREAKPOINTS.largeDesktop);

    return {
        isMobile,
        isTablet,
        isSmallDesktop,
        isMediumDesktop,
        isLargeDesktop,
        isDesktop: isSmallDesktop || isMediumDesktop || isLargeDesktop,
        isMobileOrTablet: isMobile || isTablet,
    };
};
