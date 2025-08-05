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

    // サイドバー縮小用の追加ブレークポイント
    autoCollapse: '(max-width: 1200px)', // 1200px以下でサイドバー自動縮小
    forceCollapse: '(max-width: 900px)', // 900px以下でサイドバー強制縮小

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
    const shouldAutoCollapse = useMediaQuery(BREAKPOINTS.autoCollapse);
    const shouldForceCollapse = useMediaQuery(BREAKPOINTS.forceCollapse);

    return {
        isMobile,
        isTablet,
        isSmallDesktop,
        isMediumDesktop,
        isLargeDesktop,
        isDesktop: isSmallDesktop || isMediumDesktop || isLargeDesktop,
        isMobileOrTablet: isMobile || isTablet,
        shouldAutoCollapse, // 1200px以下でサイドバー自動縮小推奨
        shouldForceCollapse, // 900px以下でサイドバー強制縮小
    };
};
