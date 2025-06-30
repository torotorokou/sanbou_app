import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Layout, Menu, Button } from 'antd';
import {
    DashboardOutlined,
    TableOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
} from '@ant-design/icons';
import ManagementDashboard from './pages/ManagementDashboard';
import FactoryDashboard from './pages/FactoryDashboard';

const { Sider, Content } = Layout;

const App: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);

    return (
        <BrowserRouter>
            <Layout style={{ minHeight: '100vh' }}>
                <Sider
                    theme="light"
                    width={250}
                    collapsible
                    collapsed={collapsed}
                    trigger={null} // 自動トリガーを無効にする
                >
                    {/* トグルボタン */}
                    <div style={{ padding: 16, textAlign: 'left' }}>
                        <Button
                            type="text"
                            icon={
                                collapsed ? (
                                    <MenuUnfoldOutlined />
                                ) : (
                                    <MenuFoldOutlined />
                                )
                            }
                            onClick={() => setCollapsed(!collapsed)}
                            style={{ fontSize: 18 }}
                        />
                    </div>

                    {/* メニュー */}
                    <Menu
                        mode="inline"
                        defaultSelectedKeys={['dashboard']}
                        style={{ height: '100%' }}
                    >
                        <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
                            <Link to="/dashboard">管理表ダッシュボード</Link>
                        </Menu.Item>
                        <Menu.Item key="factory" icon={<TableOutlined />}>
                            <Link to="/factory">工場管理ダッシュボード</Link>
                        </Menu.Item>
                    </Menu>
                </Sider>

                {/* コンテンツエリア */}
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
            </Layout>
        </BrowserRouter>
    );
};

export default App;
