/**
 * AnnouncementDetailPage - お知らせ詳細ページ
 *
 * お知らせの詳細を表示するページ。
 * URLパラメータからIDを取得して表示。
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Spin, Result } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useAuth } from '@features/authStatus';
import { useResponsive } from '@/shared';
import { useAnnouncementDetailViewModel, AnnouncementDetail } from '@features/announcements';

const AnnouncementDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';
  const { isMobile, isTablet } = useResponsive();

  const { announcement, isLoading, notFound } = useAnnouncementDetailViewModel(id ?? '', userKey);

  // レスポンシブコンテナスタイル
  const containerClass = isMobile
    ? 'px-3 pb-4 pt-4' // モバイルでは上部余白を最小化
    : isTablet
      ? 'px-6 py-5'
      : 'px-8 py-6';

  const maxWidthClass = isMobile ? 'max-w-full' : isTablet ? 'max-w-4xl' : 'max-w-5xl';

  if (isLoading) {
    return (
      <div className={`text-center ${isMobile ? 'p-4' : 'p-6'}`}>
        <Spin size="large" />
      </div>
    );
  }

  if (notFound || !announcement) {
    return (
      <div className={`${containerClass} ${maxWidthClass} mx-auto`}>
        <Result
          status="404"
          title="お知らせが見つかりません"
          subTitle="指定されたお知らせは存在しないか、公開期間が終了しています。"
          extra={
            <Button type="primary" onClick={() => navigate('/news')}>
              お知らせ一覧へ戻る
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className={`${containerClass} ${maxWidthClass} mx-auto`}>
      <div style={{ marginTop: isMobile ? 48 : 0 }}>
        <AnnouncementDetail announcement={announcement} isMobile={isMobile} showTags={!isMobile} />
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          marginTop: 32,
          marginBottom: 16,
        }}
      >
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/news')}
          size={isMobile ? 'middle' : 'large'}
        >
          お知らせ一覧へ戻る
        </Button>
      </div>
    </div>
  );
};

export default AnnouncementDetailPage;
