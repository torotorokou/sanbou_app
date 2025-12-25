/**
 * 将軍マニュアル詳細ページ
 * FSD: ページ層は組み立てのみ + パフォーマンス最適化
 */
import React, { useEffect, useState } from 'react';
import { Breadcrumb, Button, Col, Layout, Row, Space, Spin, Typography } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { useShogunCatalog } from '@features/manual';
import { FlowPane } from '@features/manual/ui/components/FlowPane';
import { VideoPane } from '@features/manual/ui/components/VideoPane';
import { UnimplementedModal } from '@features/unimplemented-feature';
import styles from './ShogunDetail.module.css';

const { Title, Paragraph } = Typography;

const ShogunManualDetailPage: React.FC = () => {
  const { id } = useParams();
  const nav = useNavigate();
  const [showUnimplementedModal, setShowUnimplementedModal] = useState(false);

  // カタログから該当アイテムを取得
  const { sections, loading } = useShogunCatalog();
  const item = React.useMemo(() => {
    for (const section of sections) {
      const found = section.items.find((it) => it.id === id);
      if (found) return found;
    }
    return null;
  }, [sections, id]);

  useEffect(() => {
    // ページ読み込み時にモーダルを表示
    setShowUnimplementedModal(true);
  }, []);

  // ページ遷移を即座に行い、ローディングインジケーターを表示
  const showSkeleton = loading || !item;

  return (
    <Layout className={styles.detailLayout}>
      <Layout.Content className={styles.detailContent}>
        <Space direction="vertical" size={12} style={{ width: '100%', marginBottom: 16 }}>
          <Breadcrumb
            items={[
              {
                title: (
                  <a onClick={() => nav('/manuals')} className={styles.detailLink}>
                    マニュアル
                  </a>
                ),
              },
              {
                title: (
                  <a onClick={() => nav('/manuals/shogun')} className={styles.detailLink}>
                    将軍
                  </a>
                ),
              },
              { title: item?.title || '読み込み中...' },
            ]}
          />
          <div className={styles.detailTitleBar}>
            <Title level={3} className={styles.detailTitle}>
              {showSkeleton ? '読み込み中...' : item.title}
            </Title>
          </div>
        </Space>

        {showSkeleton ? (
          <div className={styles.detailLoadingContainer}>
            <Spin size="large" tip="データを読み込んでいます..." />
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 16,
              padding: 16,
            }}
          >
            {/* 概要 */}
            <div
              style={{
                maxHeight: '20vh',
                overflow: 'auto',
                padding: 16,
                background: '#fafafa',
                borderRadius: 8,
              }}
            >
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                {item.description ?? '説明は未設定です。'}
              </Paragraph>
            </div>

            {/* フロー・動画（遅延ロード） */}
            <Row gutter={[16, 16]}>
              <Col xs={24} md={7}>
                <Title level={5} style={{ marginTop: 0 }}>
                  フローチャート
                </Title>
                <div className={styles.flowPane}>
                  <FlowPane
                    src={item.flowUrl}
                    title={item.title ?? 'flow'}
                    frameClassName={styles.paneFrame}
                    imgClassName={styles.paneImg}
                    lazy={true}
                  />
                </div>
              </Col>

              <Col xs={24} md={17}>
                <Title level={5} style={{ marginTop: 0 }}>
                  動画
                </Title>
                <div className={styles.videoPane}>
                  <VideoPane
                    src={item.videoUrl}
                    title={item.title ?? 'video'}
                    frameClassName={styles.paneFrame}
                    videoClassName={styles.paneVideo}
                    lazy={true}
                  />
                </div>
              </Col>
            </Row>

            {/* 下中央に配置する戻るボタン */}
            <div className={styles.detailFooter}>
              <Button onClick={() => nav('/manuals/shogun')}>一覧に戻る</Button>
            </div>
          </div>
        )}

        {/* 未実装モーダル */}
        <UnimplementedModal
          visible={showUnimplementedModal}
          onClose={() => setShowUnimplementedModal(false)}
          featureName="環境将軍マニュアル"
          description="環境将軍マニュアル機能は現在開発中です。完成まで今しばらくお待ちください。リリース後は、環境将軍システムの詳細な操作方法や業務フローをご確認いただけます。"
        />
      </Layout.Content>
    </Layout>
  );
};

export default ShogunManualDetailPage;
