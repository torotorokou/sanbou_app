/**
 * 業者マスターページ
 * FSD: ページ層は組み立てのみ
 */
import React from 'react';
import { Breadcrumb, Card, Col, Divider, Layout, List, Row, Space, Spin, Tag, Typography } from 'antd';
import { 
  TruckOutlined, 
  ReconciliationOutlined, 
  SafetyOutlined,
  PhoneOutlined,
  EnvironmentOutlined,
  FileProtectOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useShogunCatalog } from '@features/manual';
import { FlowPane } from '@features/manual/ui/components/FlowPane';
import { VideoPane } from '@features/manual/ui/components/VideoPane';
import styles from './VendorMaster.module.css';

const { Title, Paragraph, Text } = Typography;

const VendorMasterPage: React.FC = () => {
  const nav = useNavigate();
  
  // カタログから業者マスター情報を取得
  const { sections, loading } = useShogunCatalog();
  const vendorItem = React.useMemo(() => {
    const masterSection = sections.find((s) => s.id === 'master');
    if (masterSection) {
      return masterSection.items.find((item) => item.id === 'vendor');
    }
    return null;
  }, [sections]);

  return (
    <Layout className={styles.detailLayout}>
      <Layout.Content className={styles.detailContent}>
        <Space direction='vertical' size={12} style={{ width: '100%', marginBottom: 16 }}>
          <Breadcrumb items={[
            { title: <a onClick={() => nav('/manuals')} className={styles.detailLink}>マニュアル</a> },
            { title: <a onClick={() => nav('/manuals/shogun')} className={styles.detailLink}>将軍</a> },
            { title: 'マスター情報' },
            { title: '業者' }
          ]} />
          <div className={styles.detailTitleBar}>
            <Title level={3} className={styles.detailTitle}>
              {vendorItem?.title || '業者マスター'}
            </Title>
          </div>
        </Space>

        {loading ? (
          <div className={styles.detailLoadingContainer}>
            <Spin size='large' />
          </div>
        ) : !vendorItem ? (
          <div style={{ padding: 24, textAlign: 'center' }}>
            <Typography.Text type="secondary">マニュアルが見つかりません</Typography.Text>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24, padding: 16 }}>
            {/* 概要セクション */}
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div>
                  <Title level={4} style={{ marginBottom: 8 }}>
                    <ReconciliationOutlined style={{ marginRight: 8 }} />
                    業者マスターについて
                  </Title>
                  <Paragraph>
                    環境将軍システムにおける運搬業者および処分業者の情報を一元管理するマスターデータです。
                    適切な業者情報の登録・管理により、マニフェスト作成や契約管理が効率化されます。
                  </Paragraph>
                </div>

                <Divider style={{ margin: '12px 0' }} />

                <div>
                  <Title level={5} style={{ marginBottom: 12 }}>主な管理項目</Title>
                  <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} md={8}>
                      <Card size="small" hoverable>
                        <Space>
                          <TruckOutlined style={{ fontSize: 20, color: '#1890ff' }} />
                          <div>
                            <Text strong>運搬業者情報</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              許可番号・有効期限
                            </Text>
                          </div>
                        </Space>
                      </Card>
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Card size="small" hoverable>
                        <Space>
                          <SafetyOutlined style={{ fontSize: 20, color: '#52c41a' }} />
                          <div>
                            <Text strong>処分業者情報</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              処分方法・施設情報
                            </Text>
                          </div>
                        </Space>
                      </Card>
                    </Col>
                    <Col xs={24} sm={12} md={8}>
                      <Card size="small" hoverable>
                        <Space>
                          <PhoneOutlined style={{ fontSize: 20, color: '#fa8c16' }} />
                          <div>
                            <Text strong>連絡先情報</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              担当者・電話番号
                            </Text>
                          </div>
                        </Space>
                      </Card>
                    </Col>
                  </Row>
                </div>

                <Divider style={{ margin: '12px 0' }} />

                <div>
                  <Title level={5} style={{ marginBottom: 12 }}>業者マスター登録の重要性</Title>
                  <List
                    size="small"
                    dataSource={[
                      { icon: <FileProtectOutlined />, text: 'マニフェスト作成時の入力作業を効率化' },
                      { icon: <EnvironmentOutlined />, text: '許可証の有効期限を一元管理し、期限切れを防止' },
                      { icon: <SafetyOutlined />, text: '適正な業者選定により、コンプライアンスを強化' },
                    ]}
                    renderItem={(item) => (
                      <List.Item>
                        <Space>
                          {item.icon}
                          <Text>{item.text}</Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                </div>
              </Space>
            </Card>

            {/* フロー・動画セクション */}
            <Card title={
              <Space>
                <Tag color="blue">デモコンテンツ</Tag>
                <Text strong>業者マスター登録・管理フロー</Text>
              </Space>
            }>
              <Paragraph type="secondary" style={{ marginBottom: 16 }}>
                以下のフローチャートと動画で、業者マスターの登録・更新・検索の手順をご確認いただけます。
              </Paragraph>
              
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={10}>
                  <div>
                    <Title level={5} style={{ marginTop: 0, marginBottom: 8 }}>
                      📊 フローチャート
                    </Title>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                      業者登録から検索までの全体フローを図解で確認できます
                    </Text>
                    <div className={styles.flowPane}>
                      <FlowPane
                        src={vendorItem.flowUrl}
                        title={vendorItem.title ?? '業者マスターフロー'}
                        frameClassName={styles.paneFrame}
                        imgClassName={styles.paneImg}
                      />
                    </div>
                  </div>
                </Col>

                <Col xs={24} lg={14}>
                  <div>
                    <Title level={5} style={{ marginTop: 0, marginBottom: 8 }}>
                      🎥 操作デモ動画
                    </Title>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                      実際の画面操作を動画で分かりやすく解説しています
                    </Text>
                    <div className={styles.videoPane}>
                      <VideoPane
                        src={vendorItem.videoUrl}
                        title={vendorItem.title ?? '業者マスター動画'}
                        frameClassName={styles.paneFrame}
                        videoClassName={styles.paneFrame}
                      />
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>

            {/* 補足情報 */}
            <Card size="small">
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text strong>💡 ポイント</Text>
                <List
                  size="small"
                  dataSource={[
                    '業者情報は定期的に更新し、最新の許可証情報を維持してください',
                    '複数の業者を比較検討する際は、検索機能を活用しましょう',
                    '許可期限が近づいている業者は、アラート機能で通知されます',
                  ]}
                  renderItem={(item) => (
                    <List.Item style={{ padding: '4px 0', border: 'none' }}>
                      <Text type="secondary">• {item}</Text>
                    </List.Item>
                  )}
                />
              </Space>
            </Card>
          </div>
        )}
      </Layout.Content>
    </Layout>
  );
};

export default VendorMasterPage;
