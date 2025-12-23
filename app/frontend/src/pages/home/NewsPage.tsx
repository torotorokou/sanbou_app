/**
 * NewsPage - お知らせ一覧ページ
 * 
 * お知らせ機能のメインページ。
 * ViewModelを使用して一覧取得・詳細表示を行う。
 */

import React from 'react';
import { Typography, Spin, Card, Badge } from 'antd';
import { useAuth } from '@features/authStatus';
import {
  useAnnouncementsListViewModel,
  AnnouncementList,
  AnnouncementDetailModal,
  AnnouncementFilterTabs,
} from '@features/announcements';

const { Title } = Typography;

const NewsPage: React.FC = () => {
  // ユーザーキーを取得（未ログイン時は"local"）
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';

  const {
    selectedTab,
    setSelectedTab,
    importantItems,
    otherItems,
    unreadCount,
    isLoading,
    selectedAnnouncement,
    isDetailOpen,
    openDetail,
    closeDetail,
  } = useAnnouncementsListViewModel(userKey);

  if (isLoading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <Title level={2} style={{ margin: 0 }}>お知らせ一覧</Title>
        {unreadCount > 0 && (
          <Badge
            count={`未読 ${unreadCount}`}
            style={{
              backgroundColor: '#1890ff',
              fontSize: 12,
              height: 22,
              lineHeight: '22px',
              borderRadius: 11,
            }}
          />
        )}
      </div>

      <Card className="no-hover">
        <AnnouncementFilterTabs
          selected={selectedTab}
          onChange={setSelectedTab}
          unreadCount={unreadCount}
        />
        <AnnouncementList
          importantItems={importantItems}
          otherItems={otherItems}
          onOpen={openDetail}
        />
      </Card>

      <AnnouncementDetailModal
        announcement={selectedAnnouncement}
        open={isDetailOpen}
        onClose={closeDetail}
      />
    </div>
  );
};

export default NewsPage;
