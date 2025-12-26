/**
 * useResponsiveLayout - 受入ダッシュボード用レスポンシブレイアウトHook
 *
 * 責務：
 * - レスポンシブフラグからレイアウトモードを判定（mobile/laptopOrBelow/desktop）
 * - 各モードに応じたガッター・パディング・カラムspanを計算
 * - レイアウトモード変更時のResizeイベント発火（Recharts再描画用）
 *
 * レイアウトモード:
 * - mobile: ≤767px - 全て1列（縦積み）
 * - laptopOrBelow: 768-1280px - 上段2列（目標/カレンダー）、中段1列（日次）、下段1列（予測）
 * - desktop: ≥1280px - 上段3列（目標/日次/カレンダー）、下段1列（予測）
 */

import { useEffect } from 'react';
import { useResponsive } from '@/shared';

export type LayoutMode = 'mobile' | 'tablet' | 'desktop';

export type ResponsiveLayoutConfig = {
  /** レイアウトモード */
  mode: LayoutMode;
  /** グリッドガッター */
  gutter: number;
  /** パディング */
  padding: number;
  /** 各カードのCol span設定 */
  spans: {
    target: number;
    daily: number;
    cal: number;
  };
  /** カードの高さ設定 */
  heights: {
    target: {
      mobile: string | number;
      tablet: number;
      desktop: string | number;
    };
    daily: {
      mobile: number;
      tablet: number;
      desktop: string | number;
    };
    calendar: {
      mobile: number;
      tablet: number;
      desktop: string | number;
    };
    forecast: {
      mobile: number;
      tablet: number;
      desktop: string | number;
    };
  };
};

export const useResponsiveLayout = (): ResponsiveLayoutConfig => {
  const { flags } = useResponsive();

  // レイアウトモード判定（3段階統一）
  const mode: LayoutMode = flags.isMobile
    ? 'mobile' // ≤767px: 1列縦並び
    : flags.isTablet
      ? 'tablet' // 768-1280px: 上2列+下1列（1024-1279を含む）
      : 'desktop'; // ≥1280px: 上3列+下1列

  // ガッター・パディング（3段階統一）
  const gutter = flags.isMobile ? 4 : flags.isTablet ? 8 : 12;
  const padding = flags.isMobile ? 8 : flags.isTablet ? 16 : 16;

  // カラムspan定義
  const spans = {
    mobile: { target: 24, daily: 24, cal: 24 }, // 全て1列
    tablet: { target: 12, daily: 24, cal: 12 }, // 上段2列、中段1列
    desktop: { target: 7, daily: 12, cal: 5 }, // 上段3列
  }[mode];

  // カードの高さ設定（目標カードは内容量に応じて可変）
  const heights = {
    target: {
      mobile: 'auto', // 内容に応じて可変（最小320px程度確保）
      tablet: 380,
      desktop: '100%',
    },
    daily: {
      mobile: 280,
      tablet: 400,
      desktop: '100%',
    },
    calendar: {
      mobile: 0, // モバイルでは非表示
      tablet: 320,
      desktop: '100%',
    },
    forecast: {
      mobile: 480,
      tablet: 420,
      desktop: '100%',
    },
  };

  // レイアウトモード変更時にresizeイベントを発火（Recharts再描画用）
  useEffect(() => {
    const id = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 0);
    return () => clearTimeout(id);
  }, [mode]);

  return {
    mode,
    gutter,
    padding,
    spans,
    heights,
  };
};
