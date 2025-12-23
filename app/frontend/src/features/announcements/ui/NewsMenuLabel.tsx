/**
 * NewsMenuLabel - お知らせメニュー用ラベル（未読バッジ付き）
 * 
 * サイドバーのお知らせメニューに未読数バッジを表示するコンポーネント。
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from 'antd';
import { ROUTER_PATHS } from '@app/routes/routes';
import { useAuth } from '@features/authStatus';
import { useUnreadAnnouncementCountViewModel } from '@features/announcements';

export const NewsMenuLabel: React.FC = () => {
  // ユーザーキーを取得（未ログイン時は"local"）
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';

  const { unreadCount } = useUnreadAnnouncementCountViewModel(userKey);

  return (
    <Link to={ROUTER_PATHS.NEWS}>
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
        お知らせ
        {unreadCount > 0 && (
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
