/**
 * shared/tokens.ts
 * 共通トークン（ブレークポイント・余白など）
 * 
 * @deprecated このファイルのBREAKPOINTSは使用しないでください
 * 代わりに @shared/constants/breakpoints からインポートしてください
 */

import { bp } from '@shared';

/**
 * @deprecated 代わりに @shared から bp をインポートしてください
 * 
 * 例:
 * ```typescript
 * import { bp } from '@shared';
 * const isMobile = width < bp.md;
 * ```
 */
export const BREAKPOINTS = bp;

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};
