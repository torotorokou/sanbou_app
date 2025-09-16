// src/pages/manual/shogunManual.tsx
// 「環境将軍マニュアル」トップページ（React + TypeScript, Ant Design）
// このファイルは `ManualSearch.tsx` から移動されました。

/* eslint-disable react/prop-types */
import React, { memo, useMemo, useRef, useState } from "react";
import {
  Anchor,
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Flex,
  Grid,
  Input,
  Layout,
  Modal,
  Row,
  Space,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import { FileDoneOutlined } from "@ant-design/icons";
import styles from "./shogunManual.module.css";
import type { ManualItem, ManualSection } from "./types";
import { manualSections } from "./data/manualSections";

const { Title, Paragraph, Text } = Typography;
const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;


function useManualController() {
  const [query, setQuery] = useState("");
  const [activeItem, setActiveItem] = useState<ManualItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const filtered = useMemo(() => {
    if (!query.trim()) return manualSections;
    const q = query.trim().toLowerCase();
    return manualSections
      .map((sec) => ({
        ...sec,
        items: sec.items.filter((it) => {
          const inTitle = it.title.toLowerCase().includes(q);
          const inDesc = (it.description ?? "").toLowerCase().includes(q);
          const inTags = (it.tags ?? []).some((t) => t.toLowerCase().includes(q));
          return inTitle || inDesc || inTags;
        }),
      }))
      .filter((sec) => sec.items.length > 0);
  }, [query]);

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
    <Space direction="vertical" size={8} style={{ width: "100%" }}>
      <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
        {item.description ?? "説明は未設定です。"}
      </Paragraph>
      <Space size={[4, 4]} wrap>
        {(item.tags ?? []).map((t) => (
          <Tag key={t}>{t}</Tag>
        ))}
      </Space>
    </Space>
  </Card>
));
ItemCard.displayName = "ItemCard";

const SectionBlock: React.FC<{
  section: ManualSection;
  onOpen: (it: ManualItem) => void;
}> = ({ section, onOpen }) => {
  const screens = useBreakpoint();
  const colSpan = screens.xl ? 8 : screens.lg ? 12 : 24;

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
          <Col span={colSpan} key={item.id}>
            <ItemCard item={item} onOpen={onOpen} />
          </Col>
        ))}
      </Row>
    </div>
  );
};

function toYouTubeEmbed(url: string): string {
  if (/youtube\.com\/watch\?v=/.test(url)) {
    const id = new URL(url).searchParams.get("v");
    return id ? `https://www.youtube.com/embed/${id}` : url;
  }
  const m = url.match(/youtu\.be\/([^?&]+)/);
  if (m?.[1]) return `https://www.youtube.com/embed/${m[1]}`;
  return url;
}

const FlowPane: React.FC<{ src?: string; title: string }> = ({ src, title }) => {
  if (!src) return <div style={{ height: "100%" }}><Empty description="フローチャート未設定" /></div>;
  const lower = src.toLowerCase();
  if (lower.endsWith(".pdf"))
    return <iframe title={`${title}-flow`} src={src} className={styles.paneFrame} />;
  if (/\.(png|jpg|jpeg|svg|webp)$/.test(lower))
    return <img src={src} alt={`${title}-flow`} className={styles.paneImg} />;
  return <iframe title={`${title}-flow`} src={src} className={styles.paneFrame} />;
};

const VideoPane: React.FC<{ src?: string; title: string }> = ({ src, title }) => {
  if (!src) return <div style={{ height: "100%" }}><Empty description="動画未設定" /></div>;
  const lower = src.toLowerCase();
  const isMp4 = lower.endsWith(".mp4");
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
      cancelButtonProps={{ style: { display: "none" } }}
      title={item?.title ?? "マニュアル"}
      width="80vw"
      centered
      styles={{
        body: { height: "80vh", overflow: "hidden", paddingTop: 8 },
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", height: "100%", gap: 12 }}>
        <div style={{ maxHeight: "20vh", overflow: "auto" }}>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            {item?.description ?? "説明は未設定です。"}
          </Paragraph>
        </div>

        <div style={{ flex: 1, minHeight: 0 }}>
          <Row gutter={[16, 16]} style={{ height: "100%" }}>
            <Col xs={24} md={7} style={{ height: "100%" }}>
              <Title level={5} style={{ marginTop: 0 }}>フローチャート</Title>
              <div className={styles.flowPane}>
                <FlowPane src={item?.flowUrl} title={item?.title ?? "flow"} />
              </div>
            </Col>

            <Col xs={24} md={17} style={{ height: "100%" }}>
              <Title level={5} style={{ marginTop: 0 }}>動画</Title>
              <div className={styles.videoPane}>
                <VideoPane src={item?.videoUrl} title={item?.title ?? "video"} />
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

const ShogunManualHome: React.FC = () => {
  const ctrl = useManualController();
  const screens = useBreakpoint();
  const showSider = screens.lg;

  //

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

          <Space>
            <Tooltip title="全体検索（タイトル/説明/タグ）">
              <Input
                allowClear
                placeholder="キーワードで検索…（例：E票、見積、台帳）"
                style={{ width: screens.md ? 360 : 240 }}
                value={ctrl.query}
                onChange={(e) => ctrl.setQuery(e.target.value)}
              />
            </Tooltip>
          </Space>
        </Flex>
      </Header>

      <Layout>
        {showSider && (
          <Sider
            width={260}
            className={styles.sider}
          >
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
                    <Badge
                      size="small"
                      count={s.items.length}
                      style={{ backgroundColor: "var(--ant-color-primary)" }}
                    />
                  </Space>
                ),
              }))}
            />
            <div style={{ marginTop: 24 }}>
              <Paragraph type="secondary" style={{ margin: 0 }}>
                目次クリックで右の内容へスクロール。右のスクロールに合わせて目次が強調されます。
              </Paragraph>
            </div>
          </Sider>
        )}

        <Content className={styles.content}>
          <div
            ref={contentScrollRef}
            className={styles.contentScroll}
          >
            <div style={{ minHeight: 240 }}>
              <Space direction="vertical" size={24} style={{ display: "block" }}>
                {ctrl.filteredSections.length === 0 ? (
                  <Empty description="該当するマニュアルがありません" />
                ) : (
                  ctrl.filteredSections.map((sec) => (
                    <SectionBlock key={sec.id} section={sec} onOpen={ctrl.handleOpen} />
                  ))
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

export default ShogunManualHome;
