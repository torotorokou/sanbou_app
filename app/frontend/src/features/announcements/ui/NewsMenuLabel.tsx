/**
 * NewsMenuLabel - お知らせメニュー用ラベル（未読バッジ付き）
 * 
 * サイドバーのお知らせメニューに未読数バッジを表示するコンポーネント。
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from 'antd';
import { ROUTER_PATHS } from '@app/routes/routes';
import { useUnreadCount } from './useUnreadCount';

interface NewsMenuLabelProps {
  /** サイドバーが閉じているかどうか */
  collapsed?: boolean;
}

export const NewsMenuLabel: React.FC<NewsMenuLabelProps> = ({ collapsed = false }) => {
  const unreadCount = useUnreadCount();

  // 常にバッジを表示（サイドバーの開閉状態に関わらず）
  const showBadge = unreadCount > 0;

  return (
    <Link to={ROUTER_PATHS.NEWS}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
        お知らせ
        {showBadge && (
          <Badge
            count={unreadCount}
            size="small"
            style={{ marginLeft: 4 }}
          />
        )}
      </span>
    </Link>
  );
};
