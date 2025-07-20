import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from '@/theme/tokens';
import MainLayout from './layout/MainLayout';

const App: React.FC = () => (
    <ConfigProvider
        locale={jaJP}
        theme={{
            token: {
                colorPrimary: customTokens.colorPrimary,
                colorSuccess: customTokens.colorSuccess,
                colorError: customTokens.colorError,
                colorWarning: customTokens.colorWarning,
                colorInfo: customTokens.colorInfo,
            },
        }}
    >
        <AntdApp>
            <BrowserRouter>
                <MainLayout />
            </BrowserRouter>
        </AntdApp>
    </ConfigProvider>
);

export default App;
