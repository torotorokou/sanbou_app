import { useMemo } from "react";
import { useWindowSize } from "@shared/hooks/ui/useWindowSize";
import { customTokens } from "@shared/theme";
import { isTabletOrHalf, ANT } from '@shared/constants/breakpoints';

/**
 * レイアウトとスタイリングのロジックを管理するフック - シンプル版
 *
 * 🎯 目的：
 * - 複雑なブレークポイントを3つに統合（Mobile, Tablet, Desktop）
 * - レスポンシブデザインの一元管理をより簡潔に
 * - 保守性を向上させるためのシンプルなサイズ体系
 */
export const useReportLayoutStyles = () => {
  const { isMobile, isTablet, width } = useWindowSize();
  const isMobileOrTablet = isMobile || isTablet;

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
        padding: isMobile ? 12 : isTablet ? 16 : 20,
        height: '100%',
        display: 'flex',
        flexDirection: 'column' as const,
        minHeight: 0,
        boxSizing: 'border-box' as const,
      },
      mainLayout: {
        display: "flex",
        flexDirection: (isMobileOrTablet ? "column" : "row") as
          | "row"
          | "column",
  gap: isMobile ? 12 : isTablet ? 16 : (typeof width === 'number' && width < ANT.xl ? 16 : 24),
        alignItems: "stretch", // 中央配置のために'stretch'に統一
        flex: 1,
        marginTop: isMobile ? 8 : 12,
        minHeight: 0,
        overflow: 'hidden' as const,
        width: "100%",
        minWidth: 0, // フレックス内の子要素でのはみ出しを防ぐ
        boxSizing: "border-box" as const,
      },
      leftPanel: {
        display: "flex",
        flexDirection: "column" as const,
        gap: isMobile ? 8 : 12, // gapも縮小してコンパクトに
        // シンプルな3段階のサイズ設定
  width: isMobileOrTablet ? "100%" : (typeof width === 'number' && width < ANT.xl ? "260px" : "300px"),
  minWidth: isMobileOrTablet ? "auto" : (typeof width === 'number' && width < ANT.xl ? "260px" : "300px"),
  maxWidth: isMobileOrTablet ? "100%" : (typeof width === 'number' && width < ANT.xl ? "260px" : "300px"),
        minHeight: 0,
        // デスクトップではサイドバー幅を固定（他ページと同様の挙動）
        flex: (isMobileOrTablet ? "1 1 auto" : (typeof width === 'number' && width < ANT.xl ? "0 0 260px" : "0 0 300px")) as
          | "1 1 auto"
          | "0 0 260px"
          | "0 0 300px",
        flexShrink: isMobileOrTablet ? 1 : 0,
        flexGrow: isMobileOrTablet ? 1 : 0,
        order: isMobileOrTablet ? 3 : 1,
        boxSizing: "border-box" as const,
      },
      centerPanel: {
        display: isMobileOrTablet ? "none" : "flex",
        flexDirection: "column", // 縦方向のflexコンテナ
        justifyContent: "center", // 垂直方向中央配置
        alignItems: "center", // 水平方向中央配置
        // NOTE: ここはアイコン/矢印等のセンター用で幅固定だが、将来はclampで可変化検討
  width: (typeof width === 'number' && isTabletOrHalf(width)) ? "48px" : "60px",
  minWidth: (typeof width === 'number' && isTabletOrHalf(width)) ? "48px" : "60px",
  maxWidth: (typeof width === 'number' && isTabletOrHalf(width)) ? "48px" : "60px",
  minHeight: (typeof width === 'number' && isTabletOrHalf(width)) ? "320px" : "400px", // 最小高さを設定して中央配置を確実に
        flexShrink: 0,
        flexGrow: 0,
        order: 2,
        boxSizing: "border-box" as const,
        // デバッグ用の背景色（一時的）
        // backgroundColor: 'rgba(255, 0, 0, 0.1)',
        // border: '1px solid red',
      },
      // モバイル・タブレット用のアクションセクション
      mobileActionsPanel: {
        display: isMobileOrTablet ? "flex" : "none",
        width: "100%",
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
              width: "100%",
              maxWidth: "100%",
              flex: "1 1 auto",
            }
          : {
              flex: "1 1 auto",
              minWidth: (typeof width === 'number' && width < ANT.xl) ? 480 : 600,
            }),
        display: "flex",
        flexDirection: "column" as const,
        order: isMobileOrTablet ? 1 : 3,
        minWidth: 0, // 右パネル自身も縮小可能に
        minHeight: 0,
        overflow: 'hidden' as const,
        overflowX: ("hidden" as unknown) as "visible" | "hidden" | "clip" | "scroll" | "auto",
      },
  previewContainer: {
    display: "flex",
    flex: 1,
  gap: isMobile ? 8 : (typeof width === 'number' && width < ANT.xl) ? 12 : 16,
    // プレビューを縦方向に伸ばして下部の余白を埋める
    alignItems: "stretch",
    flexDirection: (isMobile ? "column" : "row") as "row" | "column",
    minHeight: 0,
  },
  previewArea: {
    flex: 1,
  // flex レイアウトで縦に伸ばす。モバイルでは固定高さを残す。
  height: isMobile ? "50vh" : "100%",
    width: isMobile ? "100%" : "auto",
        border: `1px solid ${customTokens.colorBorder}`,
        borderRadius: 8,
        boxShadow: `0 2px 8px ${customTokens.shadowLight}`,
        background: customTokens.colorBgCard,
        overflow: "hidden",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      },
      downloadSection: {
        display: "flex",
        flexDirection: isMobile ? "row" : "column",
        justifyContent: "center",
        alignItems: "center",
  width: isMobile ? "100%" : (typeof width === 'number' && width < ANT.xl) ? 100 : 120,
        gap: 8,
        marginTop: isMobile ? 12 : 0,
      },
      sampleThumbnail: {
        className: "sample-thumbnail",
      },
    }),
  [isMobile, isTablet, isMobileOrTablet, width] // 幅変化でも再評価
  );

  return styles;
};
