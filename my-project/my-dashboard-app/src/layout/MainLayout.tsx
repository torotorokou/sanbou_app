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
            <Layout>
                <Content style={{ padding: '24px' }}>
                    <AppRoutes />
                </Content>
            </Layout>
        </Layout>
    );
};

export default MainLayout;
