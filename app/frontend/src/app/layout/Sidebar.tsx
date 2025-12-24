// src/layout/Sidebar.tsx
import React from 'react';
import { Layout, Menu, Button, Drawer } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined, HomeOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { SIDEBAR_MENU } from '@app/navigation/sidebarMenu';
import { ROUTER_PATHS } from '@app/routes/routes';
import { customTokens, useSidebar, useResponsive } from '@/shared';
import { type MenuItem, filterMenuItems } from '@features/navi';
import { UserInfoChip } from '@features/authStatus';
import { useUnreadCount, NewsMenuLabel, NewsMenuIcon } from '@features/announcements';
import { SidebarRail } from './SidebarRail';

const { Sider } = Layout;

/** メニューアイテムにアナウンス関連のアイコン/ラベルを追加 */
const useEnhancedMenu = (
    isSidebarOpen: boolean // サイドバーが開いているか（未読数表示判定用）
): MenuItem[] => {
    return React.useMemo<MenuItem[]>(() => {
        const filtered = filterMenuItems(SIDEBAR_MENU as MenuItem[]);
        
        return filtered.map(item => {
            if (item.key === 'home') {
                return {
                    ...item,
                    icon: <HomeOutlined />,
                    children: item.children?.map(child =>
                        child.key === ROUTER_PATHS.NEWS
                            ? {
                                ...child,
                                icon: <NewsMenuIcon />,
                                // サイドバーが開いている時だけ未読数を表示
                                label: isSidebarOpen ? (
                                    <NewsMenuLabel />
                                ) : (
                                    'お知らせ'
                                ),
                            }
                            : child
                    ),
                };
            }
            return item;
        });
    }, [isSidebarOpen]);
};

/** メニューの親キー（子を持つ項目）を抽出 */
const extractParentKeys = (menu: MenuItem[]): string[] => {
    return menu
        .filter(item => item.children?.length)
        .map(item => String(item.key));
};

/** ユーザー情報エリア */
const UserInfoArea: React.FC<{ variant?: 'drawer' | 'desktop' }> = ({ variant = 'drawer' }) => {
    const style: React.CSSProperties =
        variant === 'drawer'
            ? { padding: '16px', borderBottom: '1px solid #f0f0f0' }
            : { padding: '12px 16px', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' };
    
    return (
        <div style={style}>
            <UserInfoChip />
        </div>
    );
};

/** サイドバーメニュー共通コンポーネント */
interface SidebarMenuProps {
    visibleMenu: MenuItem[];
    openKeys: string[];
    onOpenChange: (keys: string[]) => void;
    selectedPath: string;
    theme?: 'light' | 'dark';
    collapsed?: boolean;
}

const SidebarMenu: React.FC<SidebarMenuProps> = ({
    visibleMenu,
    openKeys,
    onOpenChange,
    selectedPath,
    theme = 'light',
    collapsed = false,
}) => {
    const menuHeight = theme === 'dark'
        ? (collapsed ? 'calc(100dvh - 64px)' : 'calc(100dvh - 64px - 60px)')
        : '100%';
    
    return (
        <Menu
            theme={theme}
            mode="inline"
            selectedKeys={[selectedPath]}
            items={visibleMenu}
            openKeys={openKeys}
            onOpenChange={onOpenChange}
            style={{
                height: menuHeight,
                borderRight: 0,
                backgroundColor: theme === 'dark' ? 'transparent' : undefined,
            }}
        />
    );
};

/** メインSidebarコンポーネント（2分岐構造） */
const Sidebar: React.FC = () => {
    const location = useLocation();
    const {
        isMobile,
        collapsed,
        drawerOpen,
        openDrawer,
        closeDrawer,
        toggleCollapsed,
        config: sidebarConfig,
        style: animationStyles,
    } = useSidebar();
    const { isTablet } = useResponsive();
    const unreadCount = useUnreadCount();
    const hasUnread = unreadCount > 0;
    // デバッグログ
    console.log('[Sidebar] unreadCount:', unreadCount, 'hasUnread:', hasUnread);

    // サイドバーが開いているかの判定（未読数表示用）
    const isSidebarOpen = isMobile ? drawerOpen : !collapsed;
    
    const visibleMenu = useEnhancedMenu(isSidebarOpen);
    const parentKeys = React.useMemo(() => extractParentKeys(visibleMenu), [visibleMenu]);
    
    const [openKeys, setOpenKeys] = React.useState<string[]>([]);

    // サイドバー開閉に応じて親メニューを展開/折りたたみ
    React.useEffect(() => {
        setOpenKeys(collapsed ? [] : parentKeys);
    }, [collapsed, parentKeys]);

    // ===== モバイル: Drawerモード =====
    if (isMobile) {
        return (
            <>
                {/* レール: drawerが閉じている時に常時表示 */}
                {!drawerOpen && (
                    <SidebarRail
                        hasUnread={hasUnread}
                        onClick={openDrawer}
                    />
                )}
                
                {/* Drawer */}
                <Drawer
                    title="メニュー"
                    placement="left"
                    open={drawerOpen}
                    onClose={closeDrawer}
                    width={sidebarConfig.width}
                    zIndex={9999}
                    styles={{ body: { padding: 0 } }}
                >
                    <UserInfoArea variant="drawer" />
                    <SidebarMenu
                        visibleMenu={visibleMenu}
                        openKeys={openKeys}
                        onOpenChange={setOpenKeys}
                        selectedPath={location.pathname}
                    />
                </Drawer>
            </>
        );
    }

    // ===== デスクトップ/タブレット: Siderモード =====
    return (
        <>
            {/* レール: collapsedの時に表示 */}
            {collapsed && (
                <SidebarRail
                    hasUnread={hasUnread}
                    onClick={toggleCollapsed}
                />
            )}
            
            <Sider
                width={sidebarConfig.width}
                collapsible
                collapsed={collapsed}
                trigger={null}
                style={{
                    backgroundColor: customTokens.colorSiderBg,
                    borderRight: `1px solid ${customTokens.colorBorderSecondary}`,
                    position: 'sticky',
                    top: 0,
                    height: '100dvh',
                    overflow: 'auto',
                    minWidth: collapsed ? sidebarConfig.collapsedWidth : sidebarConfig.width,
                    flex: '0 0 auto',
                    ...animationStyles,
                }}
                breakpoint={sidebarConfig.breakpoint}
                collapsedWidth={sidebarConfig.collapsedWidth}
            >
                {/* トグルボタン */}
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
                        type="text"
                        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                        onClick={toggleCollapsed}
                        style={{
                            fontSize: isTablet ? 16 : 18,
                            color: customTokens.colorSiderText,
                        }}
                        aria-label={collapsed ? 'サイドバーを開く' : 'サイドバーを閉じる'}
                    />
                </div>

                {/* ユーザー情報（デスクトップ版） */}
                {!collapsed && <UserInfoArea variant="desktop" />}

                {/* メニュー */}
                <SidebarMenu
                    visibleMenu={visibleMenu}
                    openKeys={openKeys}
                    onOpenChange={setOpenKeys}
                    selectedPath={location.pathname}
                    theme="dark"
                    collapsed={collapsed}
                />
            </Sider>
        </>
    );
};

export default Sidebar;
