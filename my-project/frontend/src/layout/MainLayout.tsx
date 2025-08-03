import React, { useState } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import AppRoutes from '../routes/AppRoutes';
import NotificationContainer from '../components/common/NotificationContainer';
import { theme } from 'antd';

const { Content } = Layout;

const MainLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const { token } = theme.useToken();

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
            <Layout style={{ height: '100%' }}>
                <Content
                    style={{
                        flex: 1, // ✅ レイアウトの残りを埋める
                        overflowY: 'auto',
                        padding: '24px',
                        backgroundColor: token.colorBgLayout,
                    }}
                >
                    <AppRoutes />
                </Content>
            </Layout>
            {/* グローバル通知コンテナ */}
            <NotificationContainer />
        </Layout>
    );
};

export default MainLayout;
