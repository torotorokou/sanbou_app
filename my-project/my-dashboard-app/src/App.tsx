import React from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import { DashboardOutlined, TableOutlined } from '@ant-design/icons';
import ManagementDashboard from './pages/ManagementDashboard';
import FactoryDashboard from './pages/FactoryDashboard';

const { Sider, Content } = Layout;

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <Layout style={{ minHeight: '100vh' }}>
                {/* ✅ 開始タグ */}
                <Sider theme="light" width={200}>
                    <Menu
                        mode="inline"
                        defaultSelectedKeys={['dashboard']}
                        style={{ height: '100%' }}
                    >
                        <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
                            <Link to="/dashboard">ダッシュボード</Link>
                        </Menu.Item>
                        <Menu.Item key="factory" icon={<TableOutlined />}>
                            <Link to="/factory">工場管理ダッシュボード</Link>
                        </Menu.Item>
                    </Menu>
                </Sider>
                {/* ✅ 閉じタグはこのあとで良い */}

                <Layout>
                    <Content style={{ padding: '24px' }}>
                        <Routes>
                            <Route
                                path="/"
                                element={<Navigate to="/dashboard" replace />}
                            />
                            <Route
                                path="/dashboard"
                                element={<ManagementDashboard />}
                            />
                            <Route
                                path="/factory"
                                element={<FactoryDashboard />}
                            />
                            <Route
                                path="*"
                                element={<div>ページが見つかりません</div>}
                            />
                        </Routes>
                    </Content>
                </Layout>

                {/* ✅ この位置で <Sider> の閉じタグは不要です（自動で閉じている） */}
            </Layout>
        </BrowserRouter>
    );
};

export default App;
