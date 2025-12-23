// src/layout/Sidebar.tsx
import React from 'react';
import ReactDOM from 'react-dom';
import { Layout, Menu, Button, Drawer, Badge } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined, HomeOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { SIDEBAR_MENU } from '@app/navigation/sidebarMenu';
import { ROUTER_PATHS } from '@app/routes/routes';
import { customTokens, useSidebar, useResponsive } from '@/shared';
import { type MenuItem, filterMenuItems } from '@features/navi';
import { UserInfoChip } from '@features/authStatus';
import { useUnreadCount, NewsMenuLabel, NewsMenuIcon } from '@features/announcements';

const { Sider } = Layout;

// モバイル用メニューボタンのスタイル定数
const MOBILE_BUTTON_STYLE = {
    position: 'fixed' as const,
    top: 16,
    left: 16,
    zIndex: 10000,
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    transition: 'opacity 0.3s ease',
};

const SCROLL_THRESHOLD = 50; // スクロール検出の閾値（px）

/** スクロール位置を監視するカスタムフック */
const useScrollVisible = (threshold: number) => {
    const [visible, setVisible] = React.useState(false);
    
    React.useEffect(() => {
        const handleScroll = () => setVisible(window.scrollY > threshold);
        handleScroll(); // 初回チェック
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, [threshold]);
    
    return visible;
};

/** クライアントサイドマウント状態を管理するフック */
const useClientMounted = () => {
    const [mounted, setMounted] = React.useState(false);
    React.useEffect(() => setMounted(true), []);
    return mounted;
};

/** モバイル用メニューボタン（Portalでbodyに直接レンダリング） */
const MobileMenuButton: React.FC<{ onClick: () => void }> = ({ onClick }) => {
    const mounted = useClientMounted();
    const visible = useScrollVisible(SCROLL_THRESHOLD);
    
    if (!mounted || !visible) return null;
    
    return ReactDOM.createPortal(
        <Button
            type="primary"
            icon={<MenuUnfoldOutlined />}
            onClick={onClick}
            style={{ ...MOBILE_BUTTON_STYLE, opacity: visible ? 1 : 0 }}
            size="large"
            aria-label="メニューを開く"
        />,
        document.body
    );
};

/** メニューアイテムにアナウンス関連のアイコン/ラベルを追加 */
const useEnhancedMenu = (collapsed: boolean, unreadCount: number): MenuItem[] => {
    return React.useMemo<MenuItem[]>(() => {
        const filtered = filterMenuItems(SIDEBAR_MENU as MenuItem[]);
        
        return filtered.map(item => {
            if (item.key === 'home') {
                return {
                    ...item,
                    icon: (
                        <Badge dot={collapsed && unreadCount > 0} offset={[4, 4]}>
                            <HomeOutlined />
                        </Badge>
                    ),
                    children: item.children?.map(child =>
                        child.key === ROUTER_PATHS.NEWS
                            ? {
                                ...child,
                                icon: <NewsMenuIcon />,
                                label: <NewsMenuLabel collapsed={collapsed} />,
                            }
                            : child
                    ),
                };
            }
            return item;
        });
    }, [collapsed, unreadCount]);
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

/** メインSidebarコンポーネント */
const Sidebar: React.FC = () => {
    const location = useLocation();
    const { collapsed, setCollapsed, config: sidebarConfig, style: animationStyles } = useSidebar();
    const { isTablet } = useResponsive();
    const unreadCount = useUnreadCount();

    const visibleMenu = useEnhancedMenu(collapsed, unreadCount);
    const parentKeys = React.useMemo(() => extractParentKeys(visibleMenu), [visibleMenu]);
    
    const [openKeys, setOpenKeys] = React.useState<string[]>([]);

    // サイドバー開閉に応じて親メニューを展開/折りたたみ
    React.useEffect(() => {
        setOpenKeys(collapsed ? [] : parentKeys);
    }, [collapsed, parentKeys]);

    // モバイル: Drawerモード
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

    // デスクトップ/タブレット: Siderモード
    return (
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
                    onClick={() => setCollapsed(!collapsed)}
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
    );
};

export default Sidebar;
