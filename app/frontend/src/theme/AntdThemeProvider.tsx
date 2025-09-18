import React from 'react';
import { ConfigProvider, App as AntdApp } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from './tokens';

type Props = { children: React.ReactNode };

const AntdThemeProvider: React.FC<Props> = ({ children }) => (
  <ConfigProvider locale={jaJP} theme={{ token: customTokens }}>
    <AntdApp>{children}</AntdApp>
  </ConfigProvider>
);

export default AntdThemeProvider;
