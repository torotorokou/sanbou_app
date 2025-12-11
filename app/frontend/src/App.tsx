import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntdApp } from 'antd';
import MainLayout from '@app/layout/MainLayout';
import { ErrorBoundary } from '@/shared';

/**
 * アプリケーションルート
 * 
 * ヘルスチェックについて:
 * - Docker/Kubernetesレベルで自動実行されるため、フロントエンドからの定期実行は不要
 * - バックエンドエラーは各APIコール時にAxiosインターセプターで適切にハンドリング
 * - 管理者向けシステム監視は別途監視ツール(Grafana/Datadog等)で実施
 * - useSystemHealth は管理画面で手動実行する場合のみ使用
 */
const App: React.FC = () => {
    return (
        <ErrorBoundary>
            <AntdApp>
                <BrowserRouter>
                    <MainLayout />
                </BrowserRouter>
            </AntdApp>
        </ErrorBoundary>
    );
};

export default App;
