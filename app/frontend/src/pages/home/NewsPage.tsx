/**
 * NewsPage - お知らせ一覧ページ
 *
 * お知らせ機能のメインページ。
 * ViewModelを使用して一覧取得・詳細表示を行う。
 */

import React from 'react';
import { Typography, Spin, Card, Badge } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@features/authStatus';
import { useResponsive } from '@/shared';
import {
  useAnnouncementsListViewModel,
  AnnouncementList,
  AnnouncementDetailModal,
  AnnouncementFilterTabs,
  AnnouncementSortSelector,
} from '@features/announcements';

const { Title } = Typography;

const NewsPage: React.FC = () => {
  // ユーザーキーを取得（未ログイン時は"local"）
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';
  const navigate = useNavigate();
  const { isMobile, isTablet } = useResponsive();

  const {
    selectedTab,
    setSelectedTab,
    sortType,
    setSortType,
    importantItems,
    otherItems,
    unreadCount,
    isLoading,
    selectedAnnouncement,
    isDetailOpen,
    closeDetail,
  } = useAnnouncementsListViewModel(userKey);

  const handleOpenDetail = (id: string) => {
    navigate(`/news/${id}`);
  };

  if (isLoading) {
    return (
      <div className={`text-center ${isMobile ? 'p-4' : 'p-6'}`}>
        <Spin size="large" />
      </div>
    );
  }

  // レスポンシブコンテナスタイル
  const containerClass = isMobile
    ? 'px-3 pb-4 pt-20' // モバイルではサイドバーボタンと重ならないよう上部余白
    : isTablet
      ? 'px-6 py-5'
      : 'px-8 py-6';

  const maxWidthClass = isMobile ? 'max-w-full' : isTablet ? 'max-w-4xl' : 'max-w-5xl';

  return (
    <div className={`${containerClass} ${maxWidthClass} mx-auto`}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          marginBottom: 16,
        }}
      >
        <Title level={isMobile ? 3 : 2} style={{ margin: 0 }}>
          お知らせ一覧
        </Title>
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
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <AnnouncementFilterTabs
            selected={selectedTab}
            onChange={setSelectedTab}
            unreadCount={unreadCount}
          />
          <AnnouncementSortSelector
            selected={sortType}
            onChange={setSortType}
            isMobile={isMobile}
          />
        </div>
        <AnnouncementList
          importantItems={importantItems}
          otherItems={otherItems}
          onOpen={handleOpenDetail}
          isMobile={isMobile}
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
