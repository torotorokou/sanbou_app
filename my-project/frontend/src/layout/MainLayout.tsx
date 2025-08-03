import React, { useState } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import AppRoutes from '../routes/AppRoutes';
import NotificationContainer from '../components/common/NotificationContainer';
import { useDeviceType } from '../hooks/ui';
import { customTokens } from '../theme/tokens';

const { Content } = Layout;

const MainLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const { isMobile, isTablet } = useDeviceType();

    // モバイル・タブレットでは自動的にサイドバーを折りたたむ
    const shouldCollapse = isMobile || isTablet || collapsed;

    try {
        return (
            <Layout style={{ minHeight: '100vh' }}>
                <Sidebar
                    collapsed={shouldCollapse}
                    setCollapsed={setCollapsed}
                    isMobile={isMobile}
                    isTablet={isTablet}
                />
                <Layout style={{ height: '100%' }}>
                    <Content
                        style={{
                            flex: 1,
                            overflowY: 'auto',
                            overflowX: 'hidden',
                            padding: isMobile ? '12px' : isTablet ? '16px' : '24px',
                            backgroundColor: customTokens.colorBgLayout,
                            minHeight: 'calc(100vh - 64px)',
                            // 全画面以外ではスクロール可能にする
                            height: isMobile || isTablet ? 'auto' : 'calc(100vh - 64px)',
                        }}
                    >
                        <AppRoutes />
                    </Content>
                </Layout>
                {/* グローバル通知コンテナ */}
                <NotificationContainer />
            </Layout>
        );
    } catch (error) {
        console.error('MainLayout Error:', error);
        return (
            <div style={{ padding: '20px', textAlign: 'center' }}>
                <h1>アプリケーションエラー</h1>
                <p>ページの読み込み中にエラーが発生しました。</p>
                <p>エラー詳細: {String(error)}</p>
            </div>
        );
    }
};

export default MainLayout;
