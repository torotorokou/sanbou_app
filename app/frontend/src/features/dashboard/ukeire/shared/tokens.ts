/**
 * shared/tokens.ts
 * 共通トークン（ブレークポイント・余白など）
 * TODO: 必要に応じてブレークポイントやスペーシングトークンを定義
 */

// 今後、共通のデザイントークンをここに配置
/**
 * ⚠️ 非推奨: このローカルBREAKPOINTSは使用しないでください。
 * SSOT: src/shared/constants/breakpoints.ts (md:768, lg:1024, xl:1280)
 */
export const BREAKPOINTS = {
  xs: 480,
  sm: 640,   // Tailwind準拠
  md: 768,
  lg: 1024,  // Tailwind準拠
  xl: 1280,  // Tailwind準拠
  xxl: 1600,
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
};
