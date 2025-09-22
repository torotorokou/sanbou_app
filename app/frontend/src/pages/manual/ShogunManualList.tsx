// 環境将軍マニュアル（一覧/検索）: 旧 shogunManual.tsx を統合
/* eslint-disable react/prop-types */
import React, { memo, useMemo, useRef, useState, useEffect } from 'react';
import {
  Anchor,
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Flex,
  Input,
  Layout,
  Modal,
  Row,
  Space,
  Tag,
  Tooltip,
  Typography,
} from 'antd';
import {
  FileDoneOutlined,
  FolderOpenOutlined,
  FileProtectOutlined,
  FileTextOutlined,
  FileSearchOutlined,
  CloudUploadOutlined,
  DollarOutlined,
  FileSyncOutlined,
} from '@ant-design/icons';
import { useWindowSize } from '@/hooks/ui';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';
import styles from './shogunManual.module.css';
import type { ManualItem, ManualSection } from './types';
import manualsApi from '@/services/api/manualsApi';

// Catalog DTO types from backend
type CatalogItemDTO = {
  id: string;
  title: string;
  description?: string;
  route?: string;
  tags: string[];
  flow_url?: string;
  video_url?: string;
};

type CatalogSectionDTO = {
  id: string;
  title: string;
  icon?: string;
  items: CatalogItemDTO[];
};

const { Title, Paragraph, Text } = Typography;
const { Header, Sider, Content } = Layout;

function useManualController() {
  const [query, setQuery] = useState('');
  const [activeItem, setActiveItem] = useState<ManualItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [sections, setSections] = useState<ManualSection[]>([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      const cat = await manualsApi.catalog({ category: 'syogun' });
      if (!alive) return;
      const iconMap: Record<string, React.ReactNode> = {
        FolderOpenOutlined: React.createElement(FolderOpenOutlined),
        FileProtectOutlined: React.createElement(FileProtectOutlined),
        FileTextOutlined: React.createElement(FileTextOutlined),
        FileDoneOutlined: React.createElement(FileDoneOutlined),
        FileSearchOutlined: React.createElement(FileSearchOutlined),
        CloudUploadOutlined: React.createElement(CloudUploadOutlined),
        DollarOutlined: React.createElement(DollarOutlined),
        FileSyncOutlined: React.createElement(FileSyncOutlined),
      };
  const s: ManualSection[] = (cat.sections as CatalogSectionDTO[] | undefined || []).map((sec) => ({
        id: sec.id,
        title: sec.title,
        icon: sec.icon ? iconMap[sec.icon] : undefined,
        items: (sec.items as CatalogItemDTO[] | undefined || []).map((it) => ({
          id: it.id,
          title: it.title,
          description: it.description,
          route: it.route,
          tags: it.tags || [],
          flowUrl: it.flow_url,
          videoUrl: it.video_url,
        })),
      }));
      setSections(s);
    })();
    return () => {
      alive = false;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return sections;
    const q = query.trim().toLowerCase();
    return sections
      .map((sec) => ({
        ...sec,
        items: sec.items.filter((it) => {
          const inTitle = it.title.toLowerCase().includes(q);
          const inDesc = (it.description ?? '').toLowerCase().includes(q);
          const inTags = (it.tags ?? []).some((t) => t.toLowerCase().includes(q));
          return inTitle || inDesc || inTags;
        }),
      }))
      .filter((sec) => sec.items.length > 0);
  }, [query, sections]);

  const handleOpen = (item: ManualItem) => {
    setActiveItem(item);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setActiveItem(null);
  };

  return {
    query,
    setQuery,
    filteredSections: filtered,
    activeItem,
    modalOpen,
    handleOpen,
    closeModal,
  };
}

const ItemCard: React.FC<{ item: ManualItem; onOpen: (it: ManualItem) => void }> = memo(({ item, onOpen }) => (
  <Card
    size="small"
    className={styles.itemCard}
    hoverable
    onClick={() => onOpen(item)}
    title={<Text strong>{item.title}</Text>}
  >
    <Space direction="vertical" size={8} style={{ width: '100%' }}>
      <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
        {item.description ?? '説明は未設定です。'}
      </Paragraph>
      <Space size={[4, 4]} wrap>
        {(item.tags ?? []).map((t) => (
          <Tag key={t}>{t}</Tag>
        ))}
      </Space>
    </Space>
  </Card>
));
ItemCard.displayName = 'ItemCard';

const SectionBlock: React.FC<{
  section: ManualSection;
  onOpen: (it: ManualItem) => void;
}> = ({ section, onOpen }) => {
  return (
    <div id={section.id} className={styles.sectionBlock}>
      <Space align="center" size="middle" className={styles.sectionHeader}>
        <Title level={3} style={{ margin: 0 }}>
          {section.icon} {section.title}
        </Title>
        <Badge count={section.items.length} />
      </Space>
      <Row gutter={[16, 16]}>
        {section.items.map((item) => (
          <Col xs={24} lg={12} xl={8} key={item.id}>
            <ItemCard item={item} onOpen={onOpen} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

function toYouTubeEmbed(url: string): string {
  if (/youtube\.com\/watch\?v=/.test(url)) {
    const id = new URL(url).searchParams.get('v');
    return id ? `https://www.youtube.com/embed/${id}` : url;
  }
  const m = url.match(/youtu\.be\/([^?&]+)/);
  if (m?.[1]) return `https://www.youtube.com/embed/${m[1]}`;
  return url;
}

const FlowPane: React.FC<{ src?: string; title: string }> = ({ src, title }) => {
  if (!src)
    return (
      <div style={{ height: '100%' }}>
        <Empty description="フローチャート未設定" />
      </div>
    );
  const lower = src.toLowerCase();
  if (lower.endsWith('.pdf')) return <iframe title={`${title}-flow`} src={src} className={styles.paneFrame} />;
  if (/\.(png|jpg|jpeg|svg|webp)$/.test(lower)) return <img src={src} alt={`${title}-flow`} className={styles.paneImg} />;
  return <iframe title={`${title}-flow`} src={src} className={styles.paneFrame} />;
};

const VideoPane: React.FC<{ src?: string; title: string }> = ({ src, title }) => {
  if (!src)
    return (
      <div style={{ height: '100%' }}>
        <Empty description="動画未設定" />
      </div>
    );
  const lower = src.toLowerCase();
  const isMp4 = lower.endsWith('.mp4');
  const isYouTube = /youtube\.com|youtu\.be/.test(lower);
  if (isMp4) return <video src={src} className={styles.paneVideo} controls />;
  if (isYouTube) {
    const embed = toYouTubeEmbed(src);
    return (
      <iframe
        title={`${title}-video`}
        src={embed}
        className={styles.paneFrame}
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
      />
    );
  }
  return <iframe title={`${title}-video`} src={src} className={styles.paneFrame} />;
};

const ManualModal: React.FC<{
  open: boolean;
  item: ManualItem | null;
  onClose: () => void;
}> = ({ open, item, onClose }) => {
  return (
    <Modal
      open={open}
      onCancel={onClose}
      onOk={onClose}
      okText="閉じる"
      cancelButtonProps={{ style: { display: 'none' } }}
      title={item?.title ?? 'マニュアル'}
      width="80vw"
      centered
      styles={{
        body: { height: '80vh', overflow: 'hidden', paddingTop: 8 },
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 12 }}>
        <div style={{ maxHeight: '20vh', overflow: 'auto' }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {item?.description ?? '説明は未設定です。'}
          </Paragraph>
        </div>

        <div style={{ flex: 1, minHeight: 0 }}>
          <Row gutter={[16, 16]} style={{ height: '100%' }}>
            <Col xs={24} md={7} style={{ height: '100%' }}>
              <Title level={5} style={{ marginTop: 0 }}>
                フローチャート
              </Title>
              <div className={styles.flowPane}>
                <FlowPane src={item?.flowUrl} title={item?.title ?? 'flow'} />
              </div>
            </Col>

            <Col xs={24} md={17} style={{ height: '100%' }}>
              <Title level={5} style={{ marginTop: 0 }}>
                動画
              </Title>
              <div className={styles.videoPane}>
                <VideoPane src={item?.videoUrl} title={item?.title ?? 'video'} />
              </div>
            </Col>
          </Row>
        </div>

        {item?.route && (
          <Flex justify="end">
            <Button type="link" href={item.route} target="_blank" rel="noreferrer">
              関連ページを開く
            </Button>
          </Flex>
        )}
      </div>
    </Modal>
  );
};

const ShogunManualList: React.FC = () => {
  const ctrl = useManualController();
  const { width } = useWindowSize();
  const showSider = typeof width === 'number' ? width >= (BP.sm + 1) : false; // md以上
  const showHeaderSearch = typeof width === 'number' ? width > BP.mdMax : true; // mdMax より大きい（より広い画面）ときだけヘッダー内に置く
  const contentScrollRef = useRef<HTMLDivElement | null>(null);

  return (
    <Layout className={styles.layoutRoot}>
      <Header className={styles.header}>
        <Flex align="center" justify="space-between" wrap gap={12} className={styles.headerInner}>
          <Space align="center" size="middle">
            <FileDoneOutlined />
          </Space>

          <div className={styles.titleWrap}>
            <Title level={3} className={styles.title}>
              環境将軍マニュアル
            </Title>
          </div>

          {showHeaderSearch && (
            <div style={{ marginLeft: 'auto', display: 'flex', justifyContent: 'flex-end' }}>
              <Tooltip title="全体検索（タイトル/説明/タグ）">
                <Input
                  allowClear
                  placeholder="キーワードで検索…（例：E票、見積、台帳）"
                  className={styles.headerSearchInput}
                  style={{ width: (typeof width === 'number' && width >= (BP.sm + 1) && width <= BP.mdMax) ? 360 : 240 }}
                  value={ctrl.query}
                  onChange={(e) => ctrl.setQuery(e.target.value)}
                />
              </Tooltip>
            </div>
          )}
        </Flex>
      </Header>

      <Layout>
        {showSider && (
          <Sider width={260} className={styles.sider}>
            <Anchor
              targetOffset={16}
              getContainer={() => contentScrollRef.current ?? window}
              items={ctrl.filteredSections.map((s) => ({
                key: s.id,
                href: `#${s.id}`,
                title: (
                  <Space>
                    {s.icon}
                    <span>{s.title}</span>
                    <Badge size="small" count={s.items.length} style={{ backgroundColor: 'var(--ant-color-primary)' }} />
                  </Space>
                ),
              }))}
            />
          </Sider>
        )}

        <Content className={styles.content}>
          {/* LG 以下ではタイトルの下に検索窓を表示して被らないようにする */}
          {(!showHeaderSearch) && (
            <div style={{ padding: '12px 0', display: 'flex', justifyContent: 'flex-end' }}>
              <Tooltip title="全体検索（タイトル/説明/タグ）">
                <Input
                  allowClear
                  placeholder="キーワードで検索…（例：E票、見積、台帳）"
                  className={styles.searchInput}
                  value={ctrl.query}
                  onChange={(e) => ctrl.setQuery(e.target.value)}
                  style={{ width: '100%', maxWidth: 640 }}
                />
              </Tooltip>
            </div>
          )}
          <div ref={contentScrollRef} className={styles.contentScroll}>
            <div style={{ minHeight: 240 }}>
              <Space direction="vertical" size={24} style={{ display: 'block' }}>
                {ctrl.filteredSections.length === 0 ? (
                  <Empty description="該当するマニュアルがありません" />
                ) : (
                  ctrl.filteredSections.map((sec) => <SectionBlock key={sec.id} section={sec} onOpen={ctrl.handleOpen} />)
                )}
              </Space>
            </div>
          </div>
        </Content>
      </Layout>

      <ManualModal open={ctrl.modalOpen} item={ctrl.activeItem} onClose={ctrl.closeModal} />
    </Layout>
  );
};

export default ShogunManualList;
