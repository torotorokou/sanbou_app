import React from 'react';
import { Layout, Menu, Button } from 'antd';
import {
    DashboardOutlined,
    TableOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    FileTextOutlined,
    CompassOutlined,
    SettingOutlined,
    UploadOutlined,
    ToolOutlined,
    BookOutlined,
} from '@ant-design/icons';
import { Link, useLocation } from 'react-router-dom';
import { theme } from 'antd';

const { Sider } = Layout;

const Sidebar: React.FC<{
    collapsed: boolean;
    setCollapsed: (c: boolean) => void;
}> = ({ collapsed, setCollapsed }) => {
    const { token } = theme.useToken();
    const location = useLocation();

    const currentPath = location.pathname;
    const selectedKey = currentPath.replace(/^\//, '').replace(/\//g, '-');

    return (
        <Sider
            width={250}
            collapsible
            collapsed={collapsed}
            trigger={null}
            style={{
                backgroundColor: token.colorSiderBg,
                color: token.colorSiderText,
            }}
        >
            <div
                style={{
                    display: 'flex',
                    justifyContent: collapsed ? 'center' : 'flex-end',
                    alignItems: 'center',
                    height: 64,
                    paddingRight: collapsed ? 0 : 16,
                }}
            >
                <Button
                    type='text'
                    icon={
                        collapsed ? (
                            <MenuUnfoldOutlined />
                        ) : (
                            <MenuFoldOutlined />
                        )
                    }
                    onClick={() => setCollapsed(!collapsed)}
                    style={{ fontSize: 18, color: token.colorSiderText }}
                />
            </div>

            <Menu
                mode='inline'
                theme='dark'
                className='custom-sider-menu'
                selectedKeys={[selectedKey]}
                defaultOpenKeys={['dashboardGroup', 'report', 'management']}
                style={{
                    height: '100%',
                    backgroundColor: 'transparent',
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
                                label: <Link to='/dashboard'>管理表</Link>,
                            },
                            {
                                key: 'factory',
                                icon: <TableOutlined />,
                                label: <Link to='/factory'>工場管理</Link>,
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
                                label: <Link to='/report/daily'>工場日報</Link>,
                            },
                            {
                                key: 'report-balance',
                                icon: <FileTextOutlined />,
                                label: (
                                    <Link to='/report/balance'>
                                        工場搬出入収支表
                                    </Link>
                                ),
                            },
                            {
                                key: 'report-average',
                                icon: <FileTextOutlined />,
                                label: (
                                    <Link to='/report/average'>
                                        集計項目平均表
                                    </Link>
                                ),
                            },
                            {
                                key: 'report-price',
                                icon: <FileTextOutlined />,
                                label: (
                                    <Link to='/report/price'>
                                        ブロック単価表
                                    </Link>
                                ),
                            },
                            {
                                key: 'report-adminsheet',
                                icon: <FileTextOutlined />,
                                label: (
                                    <Link to='/report/adminsheet'>管理票</Link>
                                ),
                            },
                        ],
                    },
                    {
                        key: 'navi',
                        icon: <CompassOutlined />,
                        label: <Link to='/navi'>参謀NAVI</Link>,
                    },
                    {
                        key: 'management',
                        icon: <SettingOutlined />,
                        label: '管理機能',
                        children: [
                            {
                                key: 'settings',
                                icon: <SettingOutlined />,
                                label: <Link to='/settings'>設定</Link>,
                            },
                            {
                                key: 'admin',
                                icon: <ToolOutlined />,
                                label: <Link to='/admin'>管理者メニュー</Link>,
                            },
                        ],
                    },
                    {
                        key: 'upload',
                        icon: <UploadOutlined />,
                        label: <Link to='/upload'>データアップロード</Link>,
                    },
                    {
                        key: 'manual',
                        icon: <BookOutlined />,
                        label: <Link to='/manual'>マニュアル一覧</Link>,
                    },
                ]}
            />
        </Sider>
    );
};

export default Sidebar;
