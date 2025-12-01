import { useResponsive } from '@/shared';

/**
 * FilterPanelのレイアウト設定を管理するカスタムフック
 * 
 * レスポンシブブレークポイントに基づいて、
 * 各要素の配置とグリッドレイアウトを決定します。
 */
export const useFilterLayout = () => {
  const { isDesktop } = useResponsive();

  return {
    /**
     * デスクトップレイアウト（xl以上: 1280px~）
     * 種別、モード、TopN・ソートを1行に配置
     */
    isDesktop,
    
    /**
     * 種別セレクターのグリッド設定
     */
    categoryGrid: {
      xs: 24,
      md: 24,
      xl: 5,
    },
    
    /**
     * モードセレクターのグリッド設定
     */
    modeGrid: {
      xs: 24,
      md: isDesktop ? 24 : 8,
      xl: 5,
    },
    
    /**
     * TopN・ソートコントロールのグリッド設定
     */
    topNSortGrid: {
      xs: 24,
      md: isDesktop ? 24 : 16,
      xl: 14,
    },
    
    /**
     * 期間セレクターのグリッド設定
     */
    periodGrid: {
      xs: 24,
      lg: 24,
    },
    
    /**
     * 営業選択のグリッド設定
     */
    repSelectGrid: {
      xs: 24,
      md: 18,
    },
    
    /**
     * 絞り込みフィルタのグリッド設定
     */
    filterGrid: {
      xs: 24,
      md: 6,
    },
  };
};
