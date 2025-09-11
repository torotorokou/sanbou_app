// src/pages/portal/PortalPage.tsx
// 社内ポータル（トップ "/")：カードの横幅・高さを揃え、タイトル・文言を中央配置

import React from 'react';
import { Card, Typography, Button, Grid } from 'antd';
import {
  BookOutlined,
  RobotOutlined,
  DashboardOutlined,
  FileTextOutlined,
  NotificationOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ROUTER_PATHS } from '@/constants/router';

const { Title, Paragraph, Text } = Typography;
const { useBreakpoint } = Grid;

// 固定サイズ（必要に応じて調整）
const CARD_WIDTH = 320;
const CARD_HEIGHT = 260;

export interface PortalCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  link: string;
}

/**
 * 単一責任：1つの機能リンクを表示（OCP: props追加で拡張）
 * - テキスト中央揃え
 * - 固定幅／固定高
 * - キーボード操作対応
 */
const PortalCard: React.FC<PortalCardProps> = ({ title, description, icon, link }) => {
  const navigate = useNavigate();
  const screens = useBreakpoint();
  const isLgUp = !!screens.lg;

  const handleNavigate = () => navigate(link);
  const handleKeyDown: React.KeyboardEventHandler<HTMLDivElement> = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleNavigate();
    }
  };

  return (
    <Card
      hoverable
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={handleNavigate}
      aria-label={`${title} カード`}
      style={{
        width: isLgUp ? CARD_WIDTH : '100%',
        height: CARD_HEIGHT,
        display: 'flex',
      }}
      bodyStyle={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',   // 中央寄せ（横）
        justifyContent: 'flex-start',
        gap: 12,
        height: '100%',
        textAlign: 'center',    // タイトル・文言を中央表示
      }}
    >
      <div
        aria-hidden
        style={{ fontSize: 36, lineHeight: 1, color: 'var(--ant-color-primary)' }}
      >
        {icon}
      </div>

      <Title level={4} style={{ margin: 0 }}>
        {title}
      </Title>

      {/* 説明は2行で省略して高さ超過を防止 */}
      <Paragraph
        style={{
          margin: 0,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical' as any,
          overflow: 'hidden',
        }}
        title={description}
      >
        {description}
      </Paragraph>

      {/* ボタンは最下部に固定配置 */}
      <div style={{ marginTop: 'auto', width: '100%' }}>
        <Button
          type="primary"
          block
          aria-label={`${title} へ移動`}
          onClick={(e) => {
            e.stopPropagation(); // Card onClickとの二重発火防止
            handleNavigate();
          }}
        >
          開く
        </Button>
      </div>
    </Card>
  );
};

// メニュー定義（追加・削除はここだけでOK）
const portalMenus: PortalCardProps[] = [
  {
    title: '帳簿作成',
    description: '各種帳簿の作成・参照を行います。',
    icon: <BookOutlined />,
    link: ROUTER_PATHS.LEDGER_BOOK,
  },
  {
    title: 'AI NAVI',
    description: 'AI アシスタントで業務を効率化します。',
    icon: <RobotOutlined />,
    link: ROUTER_PATHS.NAVI,
  },
  {
    title: 'KPIダッシュボード',
    description: '主要指標を可視化して状況を素早く把握。',
    icon: <DashboardOutlined />,
    link: ROUTER_PATHS.DASHBOARD,
  },
  {
    title: 'マニュアル',
    description: '社内手順書・運用ガイドを参照できます。',
    icon: <FileTextOutlined />,
    link: ROUTER_PATHS.MANUAL_SEARCH,
  },
  {
    title: 'お知らせ',
    description: '最新のお知らせ・更新情報を確認。',
    icon: <NotificationOutlined />,
    link: ROUTER_PATHS.NEWS,
  },
];

export const PortalPage: React.FC = () => {
  const screens = useBreakpoint();
  const isLgUp = !!screens.lg;

  const introText = screens.xs
    ? '社内ポータルです。必要な機能を選択してください。'
    : '社内ポータルへようこそ。下記のメニューから業務に必要な機能を選択してください。';

  return (
    <div style={{ padding: '32px 32px 48px' }}>
      {/* ヘッダ */}
      <header style={{ maxWidth: 960, margin: '0 auto 32px', textAlign: 'center' }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          社内ポータル
        </Title>
        <Text type="secondary">{introText}</Text>
      </header>

      {/* カード群（CSS Grid） */}
      <main style={{ maxWidth: 1280, margin: '0 auto' }}>
        <div
          aria-label="ポータルメニュー一覧"
          style={{
            display: 'grid',
            gap: 24,
            gridTemplateColumns: isLgUp
              ? `repeat(auto-fit, minmax(${CARD_WIDTH}px, ${CARD_WIDTH}px))`
              : '1fr',
            justifyContent: isLgUp ? 'center' : 'stretch', // 最終行も中央寄せ
            alignItems: 'stretch',
          }}
        >
          {portalMenus.map((menu) => (
            <PortalCard key={menu.link} {...menu} />
          ))}
        </div>
      </main>
    </div>
  );
};

export default PortalPage;

/**
 * ルーティング例:
 * <Route path="/" element={<PortalPage />} />
 */
