// src/components/Sidebar.tsx
import React from 'react';
import { Layout, Menu, Button } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { theme } from 'antd';
import { SIDEBAR_MENU } from '@/constants/sidebarMenu';

const { Sider } = Layout;

const Sidebar: React.FC<{
    collapsed: boolean;
    setCollapsed: (c: boolean) => void;
}> = ({ collapsed, setCollapsed }) => {
    const { token } = theme.useToken();
    const location = useLocation();

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
                selectedKeys={[location.pathname]}
                defaultOpenKeys={['dashboardGroup', 'report', 'management']}
                style={{
                    height: '100%',
                    backgroundColor: 'transparent',
                    color: token.colorText,
                }}
                items={SIDEBAR_MENU}
            />
        </Sider>
    );
};

export default Sidebar;
