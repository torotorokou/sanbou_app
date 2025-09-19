import React from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import AppRoutes from '../routes/AppRoutes';
import NotificationContainer from '../components/common/NotificationContainer';
import { customTokens } from '../theme/tokens';
import { useWindowSize } from '../hooks/ui';

const { Content } = Layout;

const MainLayout: React.FC = () => {
    // ページ全体のレイアウトは保持しつつ、サイドバー開閉はSidebar内部のフックに委譲
    const { isMobile, isTablet } = useWindowSize();
    const shouldAutoCollapse = isMobile || isTablet;

    try {
        return (
            <Layout style={{ minHeight: '100%', height: '100%' }}>
                <Sidebar />
                <Layout style={{ height: '100%' }}>
                    <Content
                        style={{
                            flex: 1,
                            overflowY: 'auto',
                            overflowX: 'hidden',
                            padding: isMobile ? '12px' : isTablet ? '16px' : shouldAutoCollapse ? '20px' : '24px',
                            backgroundColor: customTokens.colorBgLayout,
                            minHeight: 0,
                            height: 'auto',
                            transition: 'padding 0.3s ease-in-out',
                            display: 'block',
                        }}
                    >
                        {/*
                          Grid/Flex骨子の方針：
                          - ページ側では .container を最上位に置き、内部はFlex/Gridで組む
                          - 固定幅禁止: .container は fluid + max width
                        */}
                        <div className="container">
                            <AppRoutes />
                        </div>
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
