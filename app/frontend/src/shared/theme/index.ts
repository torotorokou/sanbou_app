import type { ThemeConfig } from "antd";
import { customTokens } from "./tokens";

export const appTheme: ThemeConfig = {
  token: {
    ...customTokens,
  },
};

// テーマ関連のすべてのエクスポート
export { customTokens } from "./tokens";
export * from "./colorMaps";
export { generateCssVars } from "./cssVars";
