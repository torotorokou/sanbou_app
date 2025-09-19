// src/layout/Sidebar.tsx
import React from 'react';
import { Layout, Menu, Button, Drawer } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useLocation } from 'react-router-dom';
import { SIDEBAR_MENU } from '@/constants/sidebarMenu';
import { customTokens } from '@/theme/tokens';
import { useSidebarResponsive, useSidebarAnimation } from '@/hooks/ui';
import { useSidebarDefault } from '@/hooks/ui/useSidebarDefault';

const { Sider } = Layout;

// メニュー項目に `hidden: true` を付けるとその項目（再帰的に）を除外するユーティリティ
interface RawMenuItem {
    key: string;
    label: React.ReactNode;
    icon?: React.ReactNode;
    hidden?: boolean;
    children?: RawMenuItem[];
    path?: string;
    [extra: string]: unknown;
}

function filterMenuItems(items: RawMenuItem[] = []): RawMenuItem[] {
    return items
        .filter(i => !i.hidden)
        .map(i => {
            const copy: RawMenuItem = { ...i };
            if (Array.isArray(i.children)) {
                const children = filterMenuItems(i.children);
                if (children.length) copy.children = children;
                else delete copy.children;
            }
            return copy;
        });
}

// UIは開閉ロジックを持たず、カスタムフックに委譲（MVCのV）
const Sidebar: React.FC = () => {
    const location = useLocation();
    const sidebarConfig = useSidebarResponsive();
    const animationStyles = useSidebarAnimation();
    // 画面幅に基づくデフォルト開閉制御（SOLID: 単一責任）
    const { collapsed, setCollapsed } = useSidebarDefault();
    // openKeys を管理して、サイドバーが開いているときは子メニューを展開する
    const [openKeys, setOpenKeys] = React.useState<string[]>([]);

    // visibleMenu は hidden フラグを除外したメニュー（親キーの決定にも使う）
    const visibleMenu = React.useMemo<RawMenuItem[]>(() => filterMenuItems(SIDEBAR_MENU as RawMenuItem[]), []);

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
                    width={sidebarConfig.width}
                    styles={{
                        body: { padding: 0 },
                    }}
                >
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
                height: '100%',
                overflow: 'auto',
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
                    paddingRight: collapsed ? 0 : (sidebarConfig.autoCollapse ? 12 : 16),
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
                        fontSize: sidebarConfig.autoCollapse ? 16 : 18,
                        color: customTokens.colorSiderText
                    }}
                />
            </div>

            <Menu
                theme='dark'
                mode='inline'
                selectedKeys={[location.pathname]}
                items={visibleMenu}
                openKeys={openKeys}
                onOpenChange={(keys: string[]) => setOpenKeys(keys)}
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
