import React from "react";
import { ConfigProvider } from "antd";
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from '@shared/theme/tokens';
import { useWindowSize } from '@shared/hooks/ui';
import { isTabletOrHalf, isDesktop } from '@/shared/constants/breakpoints';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width } = useWindowSize();
  const isMd = typeof width === 'number' ? isTabletOrHalf(width) : false;
  const isXlUp = typeof width === 'number' ? isDesktop(width) : false; // 新xl相当
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
