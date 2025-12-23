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
import { useAnnouncementDetailViewModel, AnnouncementDetail } from '@features/announcements';

const AnnouncementDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';

  const { announcement, isLoading, notFound } = useAnnouncementDetailViewModel(
    id ?? '',
    userKey
  );

  if (isLoading) {
    return (
      <div style={{ padding: 48, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (notFound || !announcement) {
    return (
      <div style={{ padding: 48 }}>
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
    <div style={{ padding: 24 }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/news')}
        style={{ marginBottom: 16 }}
      >
        お知らせ一覧へ戻る
      </Button>
      <AnnouncementDetail announcement={announcement} />
    </div>
  );
};

export default AnnouncementDetailPage;
