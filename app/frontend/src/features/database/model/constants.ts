/**
 * データベースアップロード機能の定数定義
 */

/**
 * UIカラー（CSV種別ごと）
 */
export const CSV_TYPE_COLORS: Record<string, string> = {
  shogun_flash_ship: '#3B82F6',
  shogun_flash_receive: '#0EA5E9',
  shogun_flash_yard: '#06B6D4',
  shogun_final_ship: '#10B981',
  shogun_final_receive: '#059669',
  shogun_final_yard: '#34D399',
  manifest_primary: '#F59E0B',
  manifest_secondary: '#F97316',
};

/**
 * デフォルトのカラー
 */
export const DEFAULT_CSV_COLOR = '#777777';

/**
 * 背景色に対して読みやすい文字色を返す
 */
export function readableTextColor(bg: string): string {
  try {
    const c = bg.replace('#', '');
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? '#111827' : '#ffffff';
  } catch {
    return '#ffffff';
  }
}
