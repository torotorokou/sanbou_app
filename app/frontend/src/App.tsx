import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import AppShell from '@/layouts/AppShell';
import AppRoutes from '@/routes/AppRoutes';

const App: React.FC = () => (
    <ConfigProvider locale={jaJP}>
        <AntdApp>
            <BrowserRouter>
                <AppShell>
                    <AppRoutes />
                </AppShell>
            </BrowserRouter>
        </AntdApp>
    </ConfigProvider>
);

export default App;
