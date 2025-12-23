/**
 * SidebarRail - 左端固定のボタン
 * 
 * 【役割】
 * - サイドバーが閉じている時の常時可視の「入口」
 * - クリックでサイドバー/Drawerを開く
 * - 未読通知ドットを表示（数値は表示しない）
 * 
 * 【表示条件】
 * - Mobile: drawerが閉じている時に表示
 * - Desktop: collapsedの時に表示
 */

import React from 'react';
import { Badge, Button } from 'antd';
import { MenuUnfoldOutlined } from '@ant-design/icons';

interface SidebarRailProps {
  /** 未読通知があるか（ドット表示判定） */
  hasUnread: boolean;
  /** クリック時のハンドラ */
  onClick: () => void;
}

export const SidebarRail: React.FC<SidebarRailProps> = ({
  hasUnread,
  onClick,
}) => {
  return (
    <Badge dot={hasUnread} offset={[0, 4]}>
      <Button
        type="primary"
        icon={<MenuUnfoldOutlined />}
        onClick={onClick}
        size="large"
        aria-label="サイドバーを開く"
        style={{
          position: 'fixed',
          left: 16,
          top: 16,
          zIndex: 9998,
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
        }}
      />
    </Badge>
  );
};
