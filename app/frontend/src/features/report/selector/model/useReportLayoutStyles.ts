import { useMemo } from "react";
import { useResponsive, customTokens, bp } from "@/shared";

/**
 * レイアウトとスタイリングのロジックを管理するフック - useResponsive(flags)統合版
 *
 * 🎯 目的：
 * - window.innerWidth、isTabletOrHalf、ANT直参照を全廃
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 4段階レスポンシブ（Mobile/Tablet/Laptop/Desktop）
 * - 値の決定はフック先頭で一元管理
 *
 * 🔄 リファクタリング内容：
 * - 複雑なブレークポイントを4段階に統一
 * - レスポンシブデザインの一元管理をより簡潔に
 * - 保守性を向上させるためのシンプルなサイズ体系
 */
export const useReportLayoutStyles = () => {
  // responsive: 3段階判定（Mobile/Tablet/Desktop）
  const { flags } = useResponsive();

  // responsive: 3段階ヘルパー
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile;       // ≤767px
    if (flags.isTablet) return tablet;       // 768-1279px
    return desktop;                          // ≥1280px
  };

  // responsive: 各種スタイル値を3段階で定義
  const padding = pickByDevice(12, 18, 20);
  const gap = pickByDevice(12, 20, 24);
  const gapSmall = pickByDevice(8, 12, 12);
  const leftPanelWidth = pickByDevice<string | number>('100%', '100%', 300);
  const leftPanelMinWidth = pickByDevice<string | number>('auto', 'auto', 300);
  const leftPanelMaxWidth = pickByDevice<string | number>('100%', '100%', 260, 300);
  const leftPanelFlex = pickByDevice<'1 1 auto' | '0 0 260px' | '0 0 300px'>('1 1 auto', '1 1 auto', '0 0 260px', '0 0 300px');
  const leftPanelOrder = pickByDevice(3, 3, 1, 1);
  
  const centerPanelDisplay = pickByDevice<'none' | 'flex'>('none', 'none', 'flex', 'flex');
  const centerPanelWidth = pickByDevice(48, 48, 48, 60);
  const centerPanelMinHeight = pickByDevice(320, 320, 320, 400);
  
  const rightPanelOrder = pickByDevice(1, 1, 3, 3);
  const rightPanelMinWidth = pickByDevice(0, 0, bp.xs, 600);
  // responsive: rightPanelはflexで残りの横幅を使用、maxWidthでサイドバーの幅を考慮して画面外はみ出しを防止
  const rightPanelFlex = pickByDevice<'1 1 auto'>('1 1 auto', '1 1 auto', '1 1 auto', '1 1 auto');
  const rightPanelMaxWidth = pickByDevice<string | undefined>('100%', '100%', undefined, undefined);
  
  const previewGap = pickByDevice(8, 10, 12, 16);
  const previewHeight = pickByDevice('50vh', '55vh', '100%', '100%');
  const previewWidth = pickByDevice('100%', '100%', 'auto', 'auto');
  
  const downloadWidth = pickByDevice<string | number>('100%', '100%', 100, 120);
  const downloadMarginTop = pickByDevice(12, 12, 0, 0);

  // responsive: レイアウト方向（Mobile/Tablet=縦、Laptop/Desktop=横）
  const mainLayoutDirection = pickByDevice<'column' | 'row'>('column', 'column', 'row', 'row');
  const previewDirection = pickByDevice<'column' | 'row'>('column', 'column', 'row', 'row');
  const downloadDirection = pickByDevice<'row' | 'column'>('row', 'row', 'column', 'column');

  const styles = useMemo(
    () => ({
      container: {
        padding,
        height: '100%',
        display: 'flex',
        flexDirection: 'column' as const,
        minHeight: 0,
        boxSizing: 'border-box' as const,
      },
      mainLayout: {
        display: "flex",
        flexDirection: mainLayoutDirection,
        gap,
        alignItems: "stretch",
        flex: 1,
        marginTop: pickByDevice(8, 10, 12, 12),
        minHeight: 0,
        overflow: 'hidden' as const,
        width: "100%",
        maxWidth: "100%",
        minWidth: 0,
        boxSizing: "border-box" as const,
      },
      leftPanel: {
        display: "flex",
        flexDirection: "column" as const,
        gap: gapSmall,
        width: leftPanelWidth,
        minWidth: leftPanelMinWidth,
        maxWidth: leftPanelMaxWidth,
        minHeight: 0,
        flex: leftPanelFlex,
        flexShrink: flags.isMobile || flags.isTablet ? 1 : 0,
        flexGrow: flags.isMobile || flags.isTablet ? 1 : 0,
        order: leftPanelOrder,
        boxSizing: "border-box" as const,
      },
      centerPanel: {
        display: centerPanelDisplay,
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        width: centerPanelWidth,
        minWidth: centerPanelWidth,
        maxWidth: centerPanelWidth,
        minHeight: centerPanelMinHeight,
        flexShrink: 0,
        flexGrow: 0,
        order: 2,
        boxSizing: "border-box" as const,
      },
      // モバイル・タブレット用のアクションセクション
      mobileActionsPanel: {
        display: flags.isMobile || flags.isTablet ? "flex" : "none",
        width: "100%",
        padding: pickByDevice(12, 14, 16, 16),
        backgroundColor: customTokens.colorBgCard,
        borderRadius: 8,
        marginBottom: pickByDevice(12, 14, 16, 16),
        boxShadow: `0 2px 8px ${customTokens.shadowLight}`,
        order: 3,
      },
      rightPanel: {
        width: flags.isMobile || flags.isTablet ? '100%' : undefined,
        maxWidth: rightPanelMaxWidth,
        flex: rightPanelFlex,
        minWidth: rightPanelMinWidth,
        display: "flex",
        flexDirection: "column" as const,
        order: rightPanelOrder,
        overflow: 'hidden' as const,
        overflowX: ("hidden" as unknown) as "visible" | "hidden" | "clip" | "scroll" | "auto",
        boxSizing: "border-box" as const,
      },
      previewContainer: {
        display: "flex",
        flex: 1,
        gap: previewGap,
        alignItems: "stretch",
        flexDirection: previewDirection,
        minHeight: 0,
        minWidth: 0,
        maxWidth: "100%",
        overflow: "hidden" as const,
        boxSizing: "border-box" as const,
      },
      previewArea: {
        flex: 1,
        height: previewHeight,
        width: previewWidth,
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
        flexDirection: downloadDirection,
        justifyContent: "center",
        alignItems: "center",
        width: downloadWidth,
        gap: 8,
        marginTop: downloadMarginTop,
      },
      sampleThumbnail: {
        className: "sample-thumbnail",
      },
    }),
    [
      flags.isMobile,
      flags.isTablet,
      flags.isDesktop,
      padding,
      gap,
      gapSmall,
      leftPanelWidth,
      leftPanelMinWidth,
      leftPanelMaxWidth,
      leftPanelFlex,
      leftPanelOrder,
      centerPanelDisplay,
      centerPanelWidth,
      centerPanelMinHeight,
      rightPanelOrder,
      rightPanelMinWidth,
      rightPanelMaxWidth,
      rightPanelFlex,
      previewGap,
      previewHeight,
      previewWidth,
      downloadWidth,
      downloadMarginTop,
      mainLayoutDirection,
      previewDirection,
      downloadDirection,
    ]
  );

  return styles;
};
