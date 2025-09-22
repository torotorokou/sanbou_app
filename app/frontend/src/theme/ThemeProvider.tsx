import React from "react";
import { ConfigProvider } from "antd";
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from './tokens';
import { useWindowSize } from '@/hooks/ui';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width } = useWindowSize();
  const isMd = typeof width === 'number' ? width >= (BP.sm + 1) && width <= BP.mdMax : false;
  const isXlUp = typeof width === 'number' ? width >= 1200 : false; // 旧xl相当
  const componentSize = isXlUp ? "large" : isMd ? "middle" : "small";
  return (
    <ConfigProvider
      locale={jaJP}
      componentSize={componentSize}
      theme={{ token: { ...customTokens, borderRadius: isMd ? 10 : 8 } }}
    >
      {children}
    </ConfigProvider>
  );
};
