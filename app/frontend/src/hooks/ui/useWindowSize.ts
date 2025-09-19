// シンプルで分かりやすいリサイズ検知フック
// 役割: window の幅・高さを監視して返す（SOLID: 1フック=1責務）
// 実装ポイント: requestAnimationFrame で軽量に追従、SSR安全

import { useEffect, useRef, useState } from 'react';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';

export type WindowSize = {
  width: number;
  height: number;
  // よく使うブレークポイント判定も一緒に返す（使いやすさのため）
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
};

const getWindowSize = (): WindowSize => {
  if (typeof window === 'undefined') {
    // SSR/ビルド時の安全な初期値
    return {
      width: 0,
      height: 0,
      isMobile: true,
      isTablet: false,
      isDesktop: false,
    };
  }

  const width = window.innerWidth;
  const height = window.innerHeight;
  const isMobile = width <= BP.sm;
  const isTablet = width > BP.sm && width <= BP.mdMax;
  const isDesktop = width > BP.mdMax;

  return { width, height, isMobile, isTablet, isDesktop };
};

export const useWindowSize = (): WindowSize => {
  const [size, setSize] = useState<WindowSize>(getWindowSize());

  // リサイズ大量発火に対し、requestAnimationFrameで負荷を抑制
  const frame = useRef<number | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const onResize = () => {
      if (frame.current != null) return; // 既にフレーム予約済み
      frame.current = window.requestAnimationFrame(() => {
        frame.current = null;
        setSize(getWindowSize());
      });
    };

    // 画面回転も考慮
    window.addEventListener('resize', onResize);
    window.addEventListener('orientationchange', onResize);
    return () => {
      if (frame.current != null) window.cancelAnimationFrame(frame.current);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('orientationchange', onResize);
    };
  }, []);

  return size;
};

export default useWindowSize;
