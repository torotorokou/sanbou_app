/**
 * NewsPage - お知らせ一覧ページ
 * 
 * お知らせ機能のメインページ。
 * ViewModelを使用して一覧取得・詳細表示を行う。
 */

import React from 'react';
import { Typography, Spin, Card } from 'antd';
import { useAuth } from '@features/authStatus';
import {
  useAnnouncementsListViewModel,
  AnnouncementList,
  AnnouncementDetailModal,
} from '@features/announcements';

const { Title } = Typography;

const NewsPage: React.FC = () => {
  // ユーザーキーを取得（未ログイン時は"local"）
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';

  const {
    announcements,
    isLoading,
    selectedAnnouncement,
    isDetailOpen,
    openDetail,
    closeDetail,
    isUnread,
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
      <Title level={2}>お知らせ一覧</Title>

      <Card>
        <AnnouncementList
          items={announcements}
          onOpen={openDetail}
          isUnread={isUnread}
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
