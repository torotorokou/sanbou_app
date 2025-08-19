import React from 'react';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';

// 共通ブレークポイントからメディアクエリ文字列を構築（既存API互換を維持）
export const BREAKPOINTS = {
    mobile: `(max-width: ${BP.mobile}px)`,
    tablet: `(min-width: ${BP.mobile + 1}px) and (max-width: ${BP.tablet}px)`,
    smallDesktop: `(min-width: ${BP.tablet + 1}px) and (max-width: ${BP.smallPC - 1}px)`,
    mediumDesktop: `(min-width: ${BP.smallPC}px) and (max-width: ${BP.fullHD - 1}px)`,
    largeDesktop: `(min-width: ${BP.fullHD}px)`,

    // サイドバー縮小用（しきい値は後方互換のため維持）
    autoCollapse: '(max-width: 1200px)',
    forceCollapse: '(max-width: 900px)',

    mobileOnly: `(max-width: ${BP.mobile}px)`,
    tabletUp: `(min-width: ${BP.mobile + 1}px)`,
    desktopUp: `(min-width: ${BP.tablet + 1}px)`,
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
