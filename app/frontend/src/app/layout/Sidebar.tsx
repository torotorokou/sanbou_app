// src/layout/Sidebar.tsx
import React from 'react';
import ReactDOM from 'react-dom';
import { Layout, Menu, Button, Drawer, Badge } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { SIDEBAR_MENU } from '@app/navigation/sidebarMenu';
import { ROUTER_PATHS } from '@app/routes/routes';
import { customTokens, useSidebar, useResponsive } from '@/shared';
import { type MenuItem, filterMenuItems } from '@features/navi';
import { UserInfoChip } from '@features/authStatus';
import { useAuth } from '@features/authStatus';
import { useUnreadCount, NewsMenuLabel, NewsMenuIcon } from '@features/announcements';
import { HomeOutlined } from '@ant-design/icons';

const { Sider } = Layout;

// モバイル用メニューボタン（Portalでbodyに直接レンダリング）
const MobileMenuButton: React.FC<{ onClick: () => void }> = ({ onClick }) => {
    const [mounted, setMounted] = React.useState(false);
    
    React.useEffect(() => {
        setMounted(true);
        console.log('[MobileMenuButton] mounted');
    }, []);
    
    console.log('[MobileMenuButton] render, mounted:', mounted);
    
    if (!mounted) return null;
    
    return ReactDOM.createPortal(
        <Button
            type="primary"
            icon={<MenuUnfoldOutlined />}
            onClick={() => {
                console.log('[MobileMenuButton] clicked');
                onClick();
            }}
            style={{
                position: 'fixed',
                top: 16,
                left: 16,
                zIndex: 10000,
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                pointerEvents: 'auto',
                width: 48,
                height: 48,
                backgroundColor: '#1890ff',
                border: '3px solid #ff0000', // デバッグ用: 赤枠で視認性確保
            }}
            size="large"
        />,
        document.body
    );
};

// UIは開閉ロジックを持たず、カスタムフックに委譲（MVCのV）
const Sidebar: React.FC = () => {
    const location = useLocation();
    const { collapsed, setCollapsed, config: sidebarConfig, style: animationStyles } = useSidebar();
    const { isTablet, isMobile } = useResponsive();
    const unreadCount = useUnreadCount();
    
    // デバッグログ
    React.useEffect(() => {
        console.log('[Sidebar] drawerMode:', sidebarConfig.drawerMode, 'collapsed:', collapsed, 'isMobile:', isMobile);
    }, [sidebarConfig.drawerMode, collapsed, isMobile]);

    // openKeys を管理して、サイドバーが開いているときは子メニューを展開する
    const [openKeys, setOpenKeys] = React.useState<string[]>([]);

    // visibleMenu は hidden フラグを除外したメニュー（親キーの決定にも使う）
    const visibleMenu = React.useMemo<MenuItem[]>(() => {
        const filtered = filterMenuItems(SIDEBAR_MENU as MenuItem[]);
        // NewsMenuLabel, NewsMenuIcon, HomeIcon に collapsed を渡すためにメニューを変換
        return filtered.map(item => {
            if (item.key === 'home') {
                const homeItem = {
                    ...item,
                    icon: (
                        <Badge dot={collapsed && unreadCount > 0} offset={[4, 4]}>
                            <HomeOutlined />
                        </Badge>
                    ),
                };
                if (item.children) {
                    homeItem.children = item.children.map(child => {
                        if (child.key === ROUTER_PATHS.NEWS) {
                            return {
                                ...child,
                                icon: <NewsMenuIcon />,
                                label: <NewsMenuLabel collapsed={collapsed} />,
                            };
                        }
                        return child;
                    });
                }
                return homeItem;
            }
            return item;
        });
    }, [collapsed, unreadCount]);

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
                {collapsed && <MobileMenuButton onClick={() => setCollapsed(false)} />}
                <Drawer
                    title="メニュー"
                    placement="left"
                    open={!collapsed}
                    onClose={() => setCollapsed(true)}
                    width={sidebarConfig.width}
                    zIndex={9999}
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
            width={sidebarConfig.width}
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
                minWidth: collapsed ? sidebarConfig.collapsedWidth : sidebarConfig.width,
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
