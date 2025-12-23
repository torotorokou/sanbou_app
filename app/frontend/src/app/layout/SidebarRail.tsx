/**
 * SidebarRail - 左端固定の付箋レール
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
import { Badge } from 'antd';
import { MenuUnfoldOutlined } from '@ant-design/icons';

interface SidebarRailProps {
  /** 未読通知があるか（ドット表示判定） */
  hasUnread: boolean;
  /** クリック時のハンドラ */
  onClick: () => void;
  /** レールの幅（px） */
  width?: number;
}

export const SidebarRail: React.FC<SidebarRailProps> = ({
  hasUnread,
  onClick,
  width = 16,
}) => {
  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label="サイドバーを開く"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        height: '100vh',
        width: `${width}px`,
        backgroundColor: '#001529',
        borderRight: '1px solid rgba(255, 255, 255, 0.1)',
        cursor: 'pointer',
        zIndex: 9998,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        paddingTop: '24px',
        transition: 'background-color 0.3s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#002140';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = '#001529';
      }}
    >
      {/* アイコン */}
      <div style={{ marginBottom: '16px' }}>
        <MenuUnfoldOutlined
          style={{
            fontSize: '18px',
            color: '#fff',
            display: 'block',
          }}
        />
      </div>

      {/* 未読ドット */}
      {hasUnread && (
        <Badge
          dot
          offset={[0, 0]}
          style={{
            boxShadow: '0 0 4px rgba(250, 173, 20, 0.5)',
          }}
        />
      )}
    </div>
  );
};
