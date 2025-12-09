// src/layout/Sidebar.tsx
import React from 'react';
import { Layout, Menu, Button, Drawer } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { SIDEBAR_MENU } from '@app/navigation/sidebarMenu';
import { customTokens, useSidebar, useResponsive, ANT } from '@/shared';
import { type MenuItem, filterMenuItems } from '@features/navi';
import { UserInfoChip } from '@features/authStatus';

const { Sider } = Layout;

// UIは開閉ロジックを持たず、カスタムフックに委譲（MVCのV）
const Sidebar: React.FC = () => {
    const location = useLocation();
    const { collapsed, setCollapsed, config: sidebarConfig, style: animationStyles } = useSidebar();
    const { isTablet, width: windowWidth } = useResponsive();

    // 'xl以下' のときは幅を 0.9 倍にする（ANT.xl (1200px) を閾値として使用）
    const effectiveWidth = React.useMemo(() => {
        if (typeof windowWidth === 'number' && windowWidth < ANT.xl) {
            return Math.round(sidebarConfig.width * 0.9);
        }
        return sidebarConfig.width;
    }, [windowWidth, sidebarConfig.width]);
    // openKeys を管理して、サイドバーが開いているときは子メニューを展開する
    const [openKeys, setOpenKeys] = React.useState<string[]>([]);

    // visibleMenu は hidden フラグを除外したメニュー（親キーの決定にも使う）
    const visibleMenu = React.useMemo<MenuItem[]>(() => filterMenuItems(SIDEBAR_MENU as MenuItem[]), []);

    // visibleMenu から子を持つ親キーを収集
    const parentKeys = React.useMemo(() => {
        return visibleMenu
            .filter(item => Array.isArray(item.children) && item.children!.length > 0)
            .map(item => String(item.key));
    }, [visibleMenu]);

    React.useEffect(() => {
        // サイドバーが開いている（折りたたまれていない）ときに親メニューを展開する
        if (!collapsed) {
            setOpenKeys(parentKeys);
        } else {
            setOpenKeys([]);
        }
    }, [collapsed, parentKeys]);

    // モバイルではDrawerを使用
    if (sidebarConfig.drawerMode) {
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
                        width={effectiveWidth}
                    styles={{
                        body: { padding: 0 },
                    }}
                >
                    {/* ユーザー情報表示（Drawer版） */}
                    <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
                        <UserInfoChip />
                    </div>

                    <Menu
                        mode="inline"
                        selectedKeys={[location.pathname]}
                        items={visibleMenu}
                        openKeys={openKeys}
                        onOpenChange={(keys: string[]) => setOpenKeys(keys)}
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
            width={effectiveWidth}
            collapsible
            collapsed={collapsed}
            trigger={null}
            style={{
                backgroundColor: customTokens.colorSiderBg,
                borderRight: `1px solid ${customTokens.colorBorderSecondary}`,
                // 固定表示: 本文スクロール時にサイドバーが動かないようにする
                position: 'sticky',
                top: 0,
                // ビューポートの高さいっぱいに表示する（100dvh でモバイルのアドレスバー揺れを回避）
                            height: '100dvh',
                overflow: 'auto',
                // 幅が他要因で縮まないように明示
                minWidth: collapsed ? sidebarConfig.collapsedWidth : effectiveWidth,
                flex: '0 0 auto',
                ...animationStyles,
            }}
            breakpoint={sidebarConfig.breakpoint}
            collapsedWidth={sidebarConfig.collapsedWidth}
        >
            <div
                    style={{
                    display: 'flex',
                    justifyContent: collapsed ? 'center' : 'flex-end',
                    alignItems: 'center',
                    height: 64,
                    paddingRight: collapsed ? 0 : (isTablet ? 12 : 16),
                    ...animationStyles,
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
                    style={{
                        fontSize: isTablet ? 16 : 18,
                        color: customTokens.colorSiderText
                    }}
                />
            </div>

            {/* ユーザー情報表示（デスクトップ版・折りたたみ時非表示） */}
            {!collapsed && (
                <div style={{
                    padding: '12px 16px',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                }}>
                    <UserInfoChip />
                </div>
            )}

            <Menu
                theme='dark'
                mode='inline'
                selectedKeys={[location.pathname]}
                items={visibleMenu}
                openKeys={openKeys}
                onOpenChange={(keys: string[]) => setOpenKeys(keys)}
                style={{
                    // Sider を viewport 高さにしているため、ヘッダ分 + ユーザー情報分を差し引く
                    height: collapsed ? 'calc(100dvh - 64px)' : 'calc(100dvh - 64px - 60px)',
                    borderRight: 0,
                    backgroundColor: 'transparent',
                }}
            />
        </Sider>
    );
};

export default Sidebar;
