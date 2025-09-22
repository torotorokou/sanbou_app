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
            <Layout style={{ minHeight: '100dvh', height: '100dvh', overflow: 'hidden' }}>
                <Sidebar />
                <Layout style={{ minHeight: '100dvh', overflow: 'hidden' }}>
                    {(() => {
                        const paddingPx = isMobile ? 12 : isTablet ? 16 : shouldAutoCollapse ? 20 : 24;
                        type ContentStyle = React.CSSProperties & { ['--page-padding']?: string };
                        const contentStyle: ContentStyle = {
                            paddingInline: `${paddingPx}px`,
                            paddingBlock: 0,
                            ['--page-padding']: `${paddingPx}px`,
                            backgroundColor: customTokens.colorBgLayout,
                            transition: 'padding 0.3s ease-in-out',
                            height: '100%',
                            overflow: 'hidden',
                        };
                        return (
                            <Content style={contentStyle}>
                                {/**
                                  Grid/Flex骨子の方針：
                                  - ページ側では .container を最上位に置き、内部はFlex/Gridで組む
                                  - 固定幅禁止: .container は fluid + max width
                                */}
                                <div style={{ width: '100%', maxWidth: '100%', boxSizing: 'border-box', height: '100%', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                                    <AppRoutes />
                                </div>
                            </Content>
                        );
                    })()}
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
