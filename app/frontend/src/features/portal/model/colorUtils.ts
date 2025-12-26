/**
 * 色計算ユーティリティ関数
 */

/**
 * HEXカラーをRGBA形式に変換
 */
export const hexToRgba = (hex: string, alpha = 1): string => {
  try {
    let c = hex.replace('#', '');
    if (c.length === 8) c = c.substring(0, 6);
    if (c.length === 3)
      c = c
        .split('')
        .map((ch) => ch + ch)
        .join('');
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  } catch {
    return `rgba(0,0,0,${alpha})`;
  }
};

/**
 * グラデーション文字列を生成
 */
export const getGradient = (hex: string): string => {
  try {
    const stop1 = hexToRgba(hex, 0.18);
    const stop2 = hexToRgba(hex, 0.06);
    return `linear-gradient(135deg, ${stop1} 0%, ${stop2} 60%, transparent 100%)`;
  } catch {
    return 'rgba(0, 0, 0, 0.05)';
  }
};

/**
 * 背景色に対して読みやすいテキスト色を判定（白 or 黒）
 */
export const getReadableTextColor = (bg: string): string => {
  try {
    const c = bg.replace('#', '');
    const r = parseInt(c.substring(0, 2), 16);
    const g = parseInt(c.substring(2, 4), 16);
    const b = parseInt(c.substring(4, 6), 16);
    // 相対的輝度の簡易判定
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? '#000000' : '#ffffff';
  } catch {
    return '#ffffff';
  }
};
