import React from "react";
import { ConfigProvider } from "antd";
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from '@shared/theme/tokens';
import { useWindowSize } from '@shared/hooks/ui';
import { isTabletOrHalf, isDesktop, BP } from '@/shared/constants/breakpoints';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { width } = useWindowSize();
  const isMd = typeof width === 'number' ? isTabletOrHalf(width) : false;
  const isXlUp = typeof width === 'number' ? isDesktop(width) : false; // 新xl相当
  const componentSize = isXlUp ? "large" : isMd ? "middle" : "small";
  return (
    <ConfigProvider
      locale={jaJP}
      componentSize={componentSize}
      theme={{
        token: {
          ...customTokens,
          borderRadius: isMd ? 10 : 8,
          // Grid breakpoints を3段階に統一（sm削除、lgをxlと同じにする）
          screenXS: 480,
          screenSM: BP.tabletMin,    // 576 → 768 (mdと同じにしてsm無効化)
          screenMD: BP.tabletMin,    // 768
          screenLG: BP.desktopMin,   // 992 → 1200 (xlと同じにしてlg無効化)
          screenXL: BP.desktopMin,   // 1200
          screenXXL: 1600,           // 使用しないが定義は残す
        }
      }}
    >
      {children}
    </ConfigProvider>
  );
};
