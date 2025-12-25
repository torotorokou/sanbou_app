import { useResponsive } from '@/shared';
import { FILTER_GRID } from '../config/layout.config';

/**
 * FilterPanelのレイアウト設定を管理するカスタムフック
 *
 * 【責務】
 * - レスポンシブ判定（useResponsive）を呼び出す
 * - デスクトップ/モバイルに応じて適切なグリッド設定を返す
 *
 * 【設計方針】
 * - グリッド設定自体は layout.config.ts で一元管理
 * - このフックは設定の選択ロジックのみを担当
 * - 薄いラッパーとして保守性を確保
 *
 * @returns レスポンシブ判定結果と各要素のグリッド設定
 */
export const useFilterLayout = () => {
  const { isDesktop } = useResponsive();

  return {
    /**
     * デスクトップレイアウト判定（xl以上: 1280px~）
     */
    isDesktop,

    /**
     * 種別セレクターのグリッド設定
     * デスクトップ/モバイル共通
     */
    categoryGrid: FILTER_GRID.category,

    /**
     * モードセレクターのグリッド設定
     * デスクトップ: 種別と同じ行、モバイル: 2行目左側
     */
    modeGrid: isDesktop ? FILTER_GRID.modeDesktop : FILTER_GRID.modeMobile,

    /**
     * TopN・ソートコントロールのグリッド設定
     * デスクトップ: 種別・モードと同じ行、モバイル: 2行目右側
     */
    topNSortGrid: isDesktop ? FILTER_GRID.topNSortDesktop : FILTER_GRID.topNSortMobile,

    /**
     * 期間セレクターのグリッド設定
     * デスクトップ/モバイル共通（常に全幅）
     */
    periodGrid: FILTER_GRID.period,

    /**
     * 営業選択のグリッド設定
     * デスクトップ/モバイル共通
     */
    repSelectGrid: FILTER_GRID.repSelect,

    /**
     * 絞り込みフィルタのグリッド設定
     * デスクトップ/モバイル共通
     */
    filterGrid: FILTER_GRID.filter,
  } as const;
};

/**
 * useFilterLayoutの戻り値の型
 * 型安全性を確保するためexport
 */
export type FilterLayoutResult = ReturnType<typeof useFilterLayout>;
