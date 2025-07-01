import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Layout, Menu, Button } from 'antd';
import {
    DashboardOutlined,
    TableOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    FileTextOutlined, // ← ✅ これがなかった
    CompassOutlined,
    SettingOutlined,
    UploadOutlined,
    ToolOutlined,
    BookOutlined,
} from '@ant-design/icons';
import ManagementDashboard from './pages/ManagementDashboard';
import FactoryDashboard from './pages/FactoryDashboard';
import { theme } from 'antd'; // 追加

const { Sider, Content } = Layout;

const App: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const { token } = theme.useToken(); // ✅ テーマトークン取得

    return (
        <BrowserRouter>
            <Layout style={{ minHeight: '100vh' }}>
                <Sider
                    width={250}
                    collapsible
                    collapsed={collapsed}
                    trigger={null}
                    style={{
                        backgroundColor: token.colorSiderBg, // ✅ 背景色をテーマに連動
                        color: token.colorSiderText, // ✅ テキスト色も連動（Menu用）
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: collapsed ? 'center' : 'flex-end', // ← 状態で切替
                            alignItems: 'center',
                            height: 64,
                            paddingRight: collapsed ? 0 : 16,
                        }}
                    >
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
                            style={{
                                fontSize: 18,
                                color: token.colorSiderText,
                            }}
                        />
                    </div>

                    <Menu
                        mode="inline"
                        theme="dark" // ✅ Siderのテーマをダークに統一
                        defaultSelectedKeys={['dashboard']}
                        defaultOpenKeys={[
                            'dashboardGroup',
                            'report',
                            'management',
                        ]} // ✅ 初期展開のみ
                        style={{
                            height: '100%',
                            backgroundColor: 'transparent', // ✅ Siderの背景を活かす
                            color: token.colorText,
                        }}
                        items={[
                            {
                                key: 'dashboardGroup',
                                icon: <DashboardOutlined />,
                                label: 'ダッシュボード',
                                children: [
                                    {
                                        key: 'dashboard',
                                        icon: <DashboardOutlined />,
                                        label: (
                                            <Link to="/dashboard">管理表</Link>
                                        ),
                                    },
                                    {
                                        key: 'factory',
                                        icon: <TableOutlined />,
                                        label: (
                                            <Link to="/factory">工場管理</Link>
                                        ),
                                    },
                                ],
                            },
                            {
                                key: 'report',
                                icon: <FileTextOutlined />,
                                label: '帳票作成',
                                children: [
                                    {
                                        key: 'report-daily',
                                        icon: <FileTextOutlined />,
                                        label: (
                                            <Link to="/report/daily">
                                                工場日報
                                            </Link>
                                        ),
                                    },
                                    {
                                        key: 'report-balance',
                                        icon: <FileTextOutlined />,
                                        label: (
                                            <Link to="/report/balance">
                                                工場搬出入収支表
                                            </Link>
                                        ),
                                    },
                                    {
                                        key: 'report-average',
                                        icon: <FileTextOutlined />,
                                        label: (
                                            <Link to="/report/average">
                                                集計項目平均表
                                            </Link>
                                        ),
                                    },
                                    {
                                        key: 'report-price',
                                        icon: <FileTextOutlined />,
                                        label: (
                                            <Link to="/report/price">
                                                ブロック単価表
                                            </Link>
                                        ),
                                    },
                                    {
                                        key: 'report-adminsheet',
                                        icon: <FileTextOutlined />,
                                        label: (
                                            <Link to="/report/adminsheet">
                                                管理票
                                            </Link>
                                        ),
                                    },
                                ],
                            },
                            {
                                key: 'navi',
                                icon: <CompassOutlined />,
                                label: <Link to="/navi">参謀NAVI</Link>,
                            },
                            {
                                key: 'management',
                                icon: <SettingOutlined />,
                                label: '管理機能',
                                children: [
                                    {
                                        key: 'settings',
                                        icon: <SettingOutlined />,
                                        label: <Link to="/settings">設定</Link>,
                                    },
                                    {
                                        key: 'admin',
                                        icon: <ToolOutlined />,
                                        label: (
                                            <Link to="/admin">
                                                管理者メニュー
                                            </Link>
                                        ),
                                    },
                                ],
                            },
                            {
                                key: 'upload',
                                icon: <UploadOutlined />,
                                label: (
                                    <Link to="/upload">データアップロード</Link>
                                ),
                            },

                            {
                                key: 'manual',
                                icon: <BookOutlined />,
                                label: <Link to="/manual">マニュアル</Link>,
                            },
                        ]}
                    />
                </Sider>

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
                                path="/report"
                                element={<div>帳票作成ページ</div>}
                            />
                            <Route
                                path="/navi"
                                element={<div>参謀NAVIページ</div>}
                            />
                            <Route
                                path="/settings"
                                element={<div>設定ページ</div>}
                            />
                            <Route
                                path="/upload"
                                element={<div>データアップロードページ</div>}
                            />
                            <Route
                                path="/admin"
                                element={<div>管理者メニューページ</div>}
                            />
                            <Route
                                path="/manual"
                                element={<div>マニュアルページ</div>}
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
