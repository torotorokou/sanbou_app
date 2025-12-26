/**
 * 将軍マニュアル一覧ページ
 * FSD: ページ層はレイアウト・検索・状態管理を統合
 */
import React, { useMemo, useRef, useState } from "react";
import {
  Anchor,
  Badge,
  Button,
  Empty,
  Flex,
  Input,
  Layout,
  Space,
  Tooltip,
  Typography,
} from "antd";
import { FileDoneOutlined, UnorderedListOutlined } from "@ant-design/icons";
import { useResponsive } from "@/shared"; // responsive: flags
import { useShogunCatalog } from "@features/manual";
import { SectionBlock } from "@features/manual/ui/components/SectionBlock";
import { ManualModal } from "@features/manual/ui/components/ShogunModal";
import type { ManualItem } from "@features/manual";
import { useSectionNavViewModel } from "@features/manual/model/useSectionNavViewModel";
import { BottomSheet } from "@features/manual/ui/components/BottomSheet";
import { SectionList } from "@features/manual/ui/components/SectionList";
import type { SectionNavItem } from "@features/manual/domain/types/sectionNav.types";
import { useManualTitleSpyViewModel } from "@features/manual/model/useManualTitleSpyViewModel";
import { StickyManualTitleBar } from "@features/manual/ui/components/StickyManualTitleBar";
import styles from "./ShogunList.module.css";

const { Title } = Typography;
const { Header, Sider, Content } = Layout;

const ShogunManualListPage: React.FC = () => {
  const [query, setQuery] = useState("");
  const [activeItem, setActiveItem] = useState<ManualItem | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const contentScrollRef = useRef<HTMLDivElement | null>(null);

  const { sections, loading } = useShogunCatalog();
  // responsive: useResponsive(flags)
  const { flags } = useResponsive();

  // responsive: pickByDevice helper (3-tier unified)
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile; // ≤767px
    if (flags.isTablet) return tablet; // 768-1280px
    return desktop; // ≥1281px
  };

  // responsive: showSider logic (Tablet以上 = ≥768px)
  const showSider = !flags.isMobile;
  // responsive: showHeaderSearch logic (Tablet以上 = ≥768px)
  const showHeaderSearch = !flags.isMobile;

  // フィルタリング
  const filtered = useMemo(() => {
    if (!query.trim()) return sections;
    const q = query.trim().toLowerCase();
    return sections
      .map((sec) => ({
        ...sec,
        items: sec.items.filter((it: ManualItem) => {
          const inTitle = it.title.toLowerCase().includes(q);
          const inDesc = (it.description ?? "").toLowerCase().includes(q);
          const inTags = (it.tags ?? []).some((t: string) =>
            t.toLowerCase().includes(q),
          );
          return inTitle || inDesc || inTags;
        }),
      }))
      .filter((sec) => sec.items.length > 0);
  }, [query, sections]);

  // Section Navigation Items（PCサイドバー/モバイルBottomSheetで共通）
  const sectionNavItems = useMemo<SectionNavItem[]>(() => {
    return filtered.map((sec) => ({
      id: sec.id,
      label: sec.title,
      kind: "scroll" as const,
      target: `#${sec.id}`,
      icon: sec.icon,
      count: sec.items.length,
    }));
  }, [filtered]);

  // Section Navigation ViewModel
  const sectionNav = useSectionNavViewModel({ items: sectionNavItems });

  // Manual Title ScrollSpy ViewModel（モバイルのみ使用）
  const titleSpy = useManualTitleSpyViewModel({
    sections: filtered,
    scrollRoot: contentScrollRef.current,
    rootMargin: "-80px 0px -70% 0px",
  });

  const handleOpen = (item: ManualItem) => {
    setActiveItem(item);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setActiveItem(null);
  };

  return (
    <Layout className={styles.layoutRoot}>
      {/* ヘッダー */}
      <Header className={styles.header}>
        <Flex
          align="center"
          justify="space-between"
          wrap
          gap={12}
          className={styles.headerInner}
        >
          <Space align="center" size="middle">
            <FileDoneOutlined />
          </Space>

          <div className={styles.titleWrap}>
            <Title level={3} className={styles.title}>
              環境将軍マニュアル
            </Title>
          </div>

          {showHeaderSearch && (
            <div
              style={{
                marginLeft: "auto",
                display: "flex",
                justifyContent: "flex-end",
              }}
            >
              <Tooltip title="全体検索（タイトル/説明/タグ）">
                <Input
                  allowClear
                  placeholder="キーワードで検索…（例：E票、見積、台帳）"
                  className={styles.headerSearchInput}
                  // responsive: width
                  style={{ width: pickByDevice(240, 360, 360) }}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </Tooltip>
            </div>
          )}
        </Flex>
      </Header>

      <Layout>
        {/* サイドバー（PC/タブレット） */}
        {showSider && (
          <Sider width={260} className={styles.sider}>
            <Anchor
              targetOffset={16}
              getContainer={() => contentScrollRef.current ?? window}
              items={sectionNavItems.map((item) => ({
                key: item.id,
                href: item.target,
                title: (
                  <Space>
                    {item.icon}
                    <span>{item.label}</span>
                    {item.count !== undefined && (
                      <Badge
                        size="small"
                        count={item.count}
                        style={{ backgroundColor: "var(--ant-color-primary)" }}
                      />
                    )}
                  </Space>
                ),
              }))}
            />
          </Sider>
        )}

        {/* メインコンテンツ */}
        <Content className={styles.content}>
          {/* Sticky Title Bar（モバイルのみ） */}
          <StickyManualTitleBar
            title={titleSpy.activeTitle}
            show={flags.isMobile}
          />

          {!showHeaderSearch && (
            <div
              style={{
                padding: "12px 0",
                display: "flex",
                justifyContent: "flex-end",
              }}
            >
              <Tooltip title="全体検索（タイトル/説明/タグ）">
                <Input
                  allowClear
                  placeholder="キーワードで検索…（例：E票、見積、台帳）"
                  className={styles.searchInput}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  style={{ width: "100%", maxWidth: 640 }}
                />
              </Tooltip>
            </div>
          )}

          <div ref={contentScrollRef} className={styles.contentScroll}>
            <div style={{ minHeight: 240 }}>
              <Space
                direction="vertical"
                size={24}
                style={{ display: "block" }}
              >
                {loading ? (
                  <div>読み込み中...</div>
                ) : filtered.length === 0 ? (
                  <Empty description="該当するマニュアルがありません" />
                ) : (
                  filtered.map((sec) => (
                    <SectionBlock
                      key={sec.id}
                      section={sec}
                      onOpen={handleOpen}
                      sectionClassName={styles.sectionBlock}
                      headerClassName={styles.sectionHeader}
                      itemClassName={styles.itemCard}
                      sentinelRef={titleSpy.registerSentinel(sec.id)}
                    />
                  ))
                )}
              </Space>
            </div>
          </div>
        </Content>
      </Layout>

      {/* モバイル用目次ボタン（FAB） */}
      {!showSider && (
        <Button
          type="primary"
          shape="circle"
          size="large"
          icon={<UnorderedListOutlined />}
          onClick={sectionNav.open}
          className={styles.fabButton}
          aria-label="目次を開く"
        />
      )}

      {/* モバイル用BottomSheet */}
      <BottomSheet
        open={sectionNav.isOpen}
        onClose={sectionNav.close}
        title="目次"
      >
        <SectionList
          items={sectionNavItems}
          onItemClick={sectionNav.onSelect}
        />
      </BottomSheet>

      {/* モーダル */}
      <ManualModal
        open={modalOpen}
        item={activeItem}
        onClose={closeModal}
        flowPaneClassName={styles.flowPane}
        videoPaneClassName={styles.videoPane}
        paneFrameClassName={styles.paneFrame}
        paneImgClassName={styles.paneImg}
        paneVideoClassName={styles.paneVideo}
      />
    </Layout>
  );
};

export default ShogunManualListPage;
