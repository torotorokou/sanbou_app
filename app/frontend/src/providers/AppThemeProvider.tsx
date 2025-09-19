import React from "react";
import { ConfigProvider, Grid } from "antd";
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from "@/theme/tokens";

export const AppThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const screens = Grid.useBreakpoint();
  const componentSize = screens.xl ? "large" : screens.md ? "middle" : "small";
  return (
    <ConfigProvider
      locale={jaJP}
      componentSize={componentSize}
      theme={{ token: { ...customTokens, borderRadius: screens.md ? 10 : 8 } }}
    >
      {children}
    </ConfigProvider>
  );
};
