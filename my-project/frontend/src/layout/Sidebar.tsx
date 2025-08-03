// src/layout/Sidebar.tsx
import React from 'react';
import { Layout, Menu, Button, Drawer } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { SIDEBAR_MENU } from '@/constants/sidebarMenu';
import { customTokens } from '@/theme/tokens';

const { Sider } = Layout;

const Sidebar: React.FC<{
    collapsed: boolean;
    setCollapsed: (c: boolean) => void;
    isMobile?: boolean;
    isTablet?: boolean;
}> = ({ collapsed, setCollapsed, isMobile = false, isTablet = false }) => {
    const location = useLocation();

    // モバイルではDrawerを使用
    if (isMobile) {
        return (
            <>
                <Button
                    type="primary"
                    icon={<MenuUnfoldOutlined />}
                    onClick={() => setCollapsed(false)}
                    style={{
                        position: 'fixed',
                        top: 16,
                        left: 16,
                        zIndex: 1000,
                        display: collapsed ? 'block' : 'none',
                    }}
                />
                <Drawer
                    title="メニュー"
                    placement="left"
                    open={!collapsed}
                    onClose={() => setCollapsed(true)}
                    width={280}
                    styles={{
                        body: { padding: 0 },
                    }}
                >
                    <Menu
                        mode="inline"
                        selectedKeys={[location.pathname]}
                        items={SIDEBAR_MENU}
                        style={{
                            height: '100%',
                            borderRight: 0,
                        }}
                    />
                </Drawer>
            </>
        );
    }

    return (
        <Sider
            width={isTablet ? 200 : 250}
            collapsible
            collapsed={collapsed}
            trigger={null}
            style={{
                backgroundColor: customTokens.colorSiderBg,
                borderRight: `1px solid ${customTokens.colorBorderSecondary}`,
            }}
            breakpoint={isTablet ? "md" : "lg"}
            collapsedWidth={isTablet ? 60 : 80}
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
                    style={{ fontSize: 18, color: customTokens.colorSiderText }}
                />
            </div>

            <Menu
                theme='dark'
                mode='inline'
                selectedKeys={[location.pathname]}
                items={SIDEBAR_MENU}
                style={{
                    height: 'calc(100% - 64px)',
                    borderRight: 0,
                    backgroundColor: 'transparent',
                }}
            />
        </Sider>
    );
};

export default Sidebar;
