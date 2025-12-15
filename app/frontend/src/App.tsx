import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { App as AntdApp } from 'antd';
import MainLayout from '@app/layout/MainLayout';
import { ErrorBoundary } from '@/shared';
import { AuthProvider } from '@app/providers/AuthProvider';

/**
 * アプリケーションルート
 * 
 * ヘルスチェックについて:
 * - Docker/Kubernetesレベルで自動実行されるため、フロントエンドからの定期実行は不要
 * - バックエンドエラーは各APIコール時にAxiosインターセプターで適切にハンドリング
 * - 管理者向けシステム監視は別途監視ツール(Grafana/Datadog等)で実施
 * - useSystemHealth は管理画面で手動実行する場合のみ使用
 * 
 * 認証について:
 * - AuthProviderでアプリケーション起動時に認証情報を取得
 * - 認証完了までローディング画面を表示し、ブックマークからの直接アクセスにも対応
 * - 認証エラー時は専用のエラー画面を表示
 */
const App: React.FC = () => {
    return (
        <ErrorBoundary>
            <AntdApp>
                <BrowserRouter>
                    <AuthProvider>
                        <MainLayout />
                    </AuthProvider>
                </BrowserRouter>
            </AntdApp>
        </ErrorBoundary>
    );
};

export default App;
