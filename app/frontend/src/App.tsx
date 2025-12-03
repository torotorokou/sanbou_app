import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntdApp } from 'antd';
import MainLayout from '@app/layout/MainLayout';
import { useSystemHealth } from '@features/system/health';

const App: React.FC = () => {
    // システムヘルスチェックを自動実行（30秒ごと）
    useSystemHealth({
        enabled: true,
        interval: 30000,
        showNotifications: true,
    });

    return (
        <AntdApp>
            <BrowserRouter>
                <MainLayout />
            </BrowserRouter>
        </AntdApp>
    );
};

export default App;
