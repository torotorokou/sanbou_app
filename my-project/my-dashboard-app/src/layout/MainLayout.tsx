import React, { useState } from 'react';
import { Layout } from 'antd';
import Sidebar from './Sidebar';
import AppRoutes from '../routes/AppRoutes';
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
                        height: '95vh', // ✅ 画面全体を埋める
                        overflowY: 'auto', // ✅ Contentだけスクロール
                        padding: '24px',
                        backgroundColor: token.colorBgLayout,
                    }}
                >
                    <AppRoutes />
                </Content>
            </Layout>
        </Layout>
    );
};

export default MainLayout;
