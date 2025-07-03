import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import { customTokens } from '@/theme/tokens';
import MainLayout from './layout/MainLayout';

const App: React.FC = () => {
    return (
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
            <BrowserRouter>
                <MainLayout />
            </BrowserRouter>
        </ConfigProvider>
    );
};

export default App;
