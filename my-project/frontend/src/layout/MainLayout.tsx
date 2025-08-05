import React, { useState, useEffect } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import AppRoutes from '../routes/AppRoutes';
import NotificationContainer from '../components/common/NotificationContainer';
import { useDeviceType } from '../hooks/ui';
import { customTokens } from '../theme/tokens';

const { Content } = Layout;

const MainLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const [userToggled, setUserToggled] = useState(false); // ユーザーが手動で切り替えたかどうか
    const {
        isMobile,
        isTablet,
        shouldAutoCollapse,
        shouldForceCollapse
    } = useDeviceType();

    // レスポンシブに応じたサイドバー制御
    useEffect(() => {
        if (shouldForceCollapse) {
            // 900px以下では強制的に縮小
            setCollapsed(true);
            setUserToggled(false); // ユーザー操作をリセット
        } else if (shouldAutoCollapse && !userToggled) {
            // 1200px以下で、ユーザーが手動操作していない場合は自動縮小
            setCollapsed(true);
        } else if (!shouldAutoCollapse && !userToggled) {
            // 1200px以上で、ユーザーが手動操作していない場合は自動展開
            setCollapsed(false);
        }
    }, [shouldAutoCollapse, shouldForceCollapse, userToggled]);

    // ユーザーがサイドバーを手動で切り替えた際の処理
    const handleSidebarToggle = (newCollapsed: boolean) => {
        if (!shouldForceCollapse) {
            setCollapsed(newCollapsed);
            setUserToggled(true);
            // 一定時間後にユーザー操作フラグをリセット（画面サイズ変更時の自動制御を再開）
            setTimeout(() => setUserToggled(false), 3000);
        }
    };

    // モバイル・タブレットでは特別な制御
    const shouldCollapse = shouldForceCollapse || (isMobile || isTablet ? true : collapsed);

    try {
        return (
            <Layout style={{ minHeight: '100vh' }}>
                <Sidebar
                    collapsed={shouldCollapse}
                    setCollapsed={handleSidebarToggle}
                />
                <Layout style={{ height: '100%' }}>
                    <Content
                        style={{
                            flex: 1,
                            overflowY: 'auto',
                            overflowX: 'hidden',
                            padding: isMobile ? '12px' : isTablet ? '16px' : shouldAutoCollapse ? '20px' : '24px',
                            backgroundColor: customTokens.colorBgLayout,
                            minHeight: 'calc(100vh - 64px)',
                            // 全画面以外ではスクロール可能にする
                            height: isMobile || isTablet ? 'auto' : 'calc(100vh - 64px)',
                            transition: 'padding 0.3s ease-in-out', // パディングの変更をスムーズに
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
