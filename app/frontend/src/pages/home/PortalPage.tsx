// src/pages/portal/PortalPage.tsx
// リファクタリング済み: 小さなモジュールに分割して保守性を向上
// Feature-Sliced Design に従ったインポート構造
// React + TypeScript / Ant Design v5 前提。

import React from "react";
import { Typography, Modal, List, theme } from "antd";
import { useNavigate } from "react-router-dom";
import { useResponsive } from "@/shared";
import { ResponsiveNotice } from "@features/announcements";
import { useAuth } from "@features/authStatus";
import {
  useAnnouncementBannerViewModel,
  AnnouncementBanner,
} from "@features/announcements";
import {
  PortalCard,
  portalMenus,
  CARD_WIDTH,
  CARD_HEIGHT,
  BUTTON_WIDTH,
} from "@features/portal";
import type { Notice } from "@features/portal";
import "./PortalPage.css";

const { Title, Text } = Typography;

// サンプル通知データ
const sampleNotices: Notice[] = [
  {
    id: "n1",
    title: "システムメンテナンスのお知らせ",
    summary: "9/20 02:00-04:00 にシステムメンテナンスを実施します。",
    detail:
      "サービス安定化のため、上記時間帯でシステムメンテナンスを実施します。メンテナンス中は一部機能がご利用いただけません。",
    date: "2025-09-10",
  },
];

export const PortalPage: React.FC = () => {
  // レスポンシブフラグ
  const { flags } = useResponsive();
  const { token } = theme.useToken();
  const navigate = useNavigate();

  // 認証情報
  const { user } = useAuth();
  const userKey = user?.userId ?? "local";

  // お知らせバナー用ViewModel
  const {
    announcement: bannerAnnouncement,
    onAcknowledge: onBannerAcknowledge,
    onNavigateToDetail: onBannerNavigateToDetail,
  } = useAnnouncementBannerViewModel(userKey);

  // レスポンシブ判定ヘルパー
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile; // ≤767px
    if (flags.isTablet) return tablet; // 768-1280px
    return desktop; // ≥1281px
  };

  // レスポンシブフラグ
  const isCompact = flags.isMobile || flags.isTablet;
  const isNarrow = flags.isMobile;
  const isXs = flags.isXs;

  // カードスケール
  const cardScale = pickByDevice(0.9, 0.9, 1);

  // レスポンシブに関係なく全カードで同じボタン幅に統一
  const unifiedButtonWidth = BUTTON_WIDTH;

  // カード間のギャップ（行間・列間）
  const CARD_COLUMN_GAP = pickByDevice(0, 1, 1);
  const CARD_ROW_GAP = pickByDevice(0, 1, 1);

  const introText = isCompact
    ? "社内ポータルです。必要な機能を選択してください。"
    : "社内ポータルへようこそ。下記メニューから業務に必要な機能を選択してください。";

  // 通知管理
  const [notices] = React.useState<Notice[]>(sampleNotices);
  const [noticeVisible, setNoticeVisible] = React.useState<boolean>(false);
  const [modalOpen, setModalOpen] = React.useState<boolean>(false);
  const [activeNotice, setActiveNotice] = React.useState<Notice | null>(null);

  const openNoticeModal = (notice: Notice) => {
    setActiveNotice(notice);
    setModalOpen(true);
  };

  const closeNoticeModal = () => {
    setModalOpen(false);
    setActiveNotice(null);
  };

  // ヒーローセクションのCSS変数
  type PortalHeroVars = React.CSSProperties &
    Record<
      | "--portal-accent"
      | "--portal-hero-bg"
      | "--portal-hero-plate"
      | "--portal-text-secondary"
      | "--portal-border"
      | "--portal-shadow",
      string
    >;

  const heroVars: PortalHeroVars = {
    "--portal-accent": token.colorPrimary,
    "--portal-hero-bg": token.colorBgContainer,
    "--portal-hero-plate": token.colorFillQuaternary,
    "--portal-text-secondary": token.colorTextTertiary,
    "--portal-border": token.colorBorderSecondary,
    "--portal-shadow": token.boxShadowSecondary,
  };

  return (
    <div className="portal-page" style={{ minHeight: "100%" }}>
      <section className="portal-hero" style={heroVars}>
        <Title level={2} className="portal-title">
          参謀くん-社内ポータル
        </Title>
        {!isXs && <Text className="portal-subtitle">{introText}</Text>}
      </section>

      <main style={{ width: "100%", maxWidth: "1280px", margin: "0 auto" }}>
        {/* お知らせバナー（重要通知） */}
        {bannerAnnouncement && (
          <div
            style={{ width: "100%", margin: "0 0 16px 0", padding: "0 16px" }}
          >
            <AnnouncementBanner
              announcement={bannerAnnouncement}
              onClose={onBannerAcknowledge}
              onNavigateToDetail={onBannerNavigateToDetail}
              navigateFn={() => navigate(`/news/${bannerAnnouncement.id}`)}
            />
          </div>
        )}

        {/* 重要通知バナー */}
        {noticeVisible && notices.length > 0 && (
          <div
            style={{ width: "100%", margin: "0 0 24px 0", padding: "0 16px" }}
          >
            <ResponsiveNotice
              title={notices[0].title}
              description={notices[0].summary}
              detailContent={
                <div>
                  <div
                    style={{ marginBottom: 8, color: token.colorTextTertiary }}
                  >
                    {notices[0].date}
                  </div>
                  <div style={{ marginBottom: 12 }}>{notices[0].detail}</div>
                </div>
              }
              onClose={() => setNoticeVisible(false)}
              type="warning"
            />
          </div>
        )}

        {/* ポータルカード */}
        <div
          style={{
            display: "flex",
            gap: CARD_COLUMN_GAP,
            alignItems: "flex-start",
            padding: "0 16px",
          }}
        >
          <div
            style={{
              flex: "1 1 0",
              display: "flex",
              flexDirection: "column",
              gap: CARD_ROW_GAP,
            }}
          >
            <div
              aria-label="ポータルメニュー一覧"
              style={{
                display: "grid",
                columnGap: CARD_COLUMN_GAP,
                rowGap: CARD_ROW_GAP,
                gridAutoRows: `minmax(${Math.round(pickByDevice(64, 120, CARD_HEIGHT) * cardScale)}px, auto)`,
                gridTemplateColumns: flags.isMobile
                  ? "repeat(1, 1fr)"
                  : flags.isDesktop
                    ? "repeat(3, 1fr)"
                    : `repeat(auto-fit, minmax(${Math.round(CARD_WIDTH * cardScale)}px, 1fr))`,
                justifyContent: "center",
                alignItems: "stretch",
              }}
            >
              {portalMenus.map((menu) => (
                <PortalCard
                  key={menu.link}
                  {...menu}
                  buttonWidth={unifiedButtonWidth}
                  cardScale={cardScale}
                  compactLayout={isNarrow}
                  hideButton={false}
                  smallButton={isXs}
                  heightScale={isXs ? 0.7 : 1}
                />
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* 通知詳細モーダル */}
      <Modal
        title={activeNotice?.title ?? "通知詳細"}
        open={modalOpen}
        onCancel={closeNoticeModal}
        footer={null}
      >
        {activeNotice ? (
          <div>
            <div style={{ marginBottom: 8, color: token.colorTextTertiary }}>
              {activeNotice.date}
            </div>
            <div style={{ marginBottom: 12 }}>{activeNotice.detail}</div>
          </div>
        ) : (
          <List
            dataSource={notices}
            renderItem={(item: Notice) => (
              <List.Item
                key={item.title + item.date}
                onClick={() => openNoticeModal(item)}
                style={{ cursor: "pointer" }}
              >
                <List.Item.Meta title={item.title} description={item.summary} />
              </List.Item>
            )}
          />
        )}
      </Modal>
    </div>
  );
};

export default PortalPage;
