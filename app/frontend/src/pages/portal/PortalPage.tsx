// src/pages/portal/PortalPage.tsx
// 固定サイズカード（320x260）。アイコン/タイトル/説明/ボタンを“縦横ど真ん中”に配置。

import React from 'react';
import { Card, Typography, Button, Popover, Grid } from 'antd';
import {
  BookOutlined,
  RobotOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  NotificationOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ROUTER_PATHS } from '@/constants/router';
import { useWindowSize } from '@/hooks/ui';

const { Title, Paragraph, Text } = Typography;

const CARD_WIDTH = 320;
// 元の高さ 260 の 0.8 倍
const CARD_HEIGHT = 208;
const BUTTON_WIDTH = 160; // ボタンを中央に見せるため固定幅

export interface PortalCardProps {
  title: string;
  description: string;
  // ホバーで表示する詳しい説明（任意）。なければ `description` を表示
  detail?: string;
  icon: React.ReactNode;
  link: string;
}

const PortalCard: React.FC<PortalCardProps> = ({ title, description, icon, link, detail }) => {
  const navigate = useNavigate();

  const handleNavigate = () => navigate(link);
  const handleKeyDown: React.KeyboardEventHandler<HTMLDivElement> = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleNavigate();
    }
  };

  return (
    <Popover
      content={detail ?? description}
      trigger={["hover", "focus"]}
      placement="top"
      overlayStyle={{ maxWidth: 320, whiteSpace: 'normal' }}
    >
      <Card
        hoverable
        role="button"
        tabIndex={0}
        aria-label={`${title} カード`}
        onKeyDown={handleKeyDown}
        onClick={handleNavigate}
        style={{
          width: CARD_WIDTH,
          height: CARD_HEIGHT,
        }}
        // 中身を“完全中央”にする：Flexbox で縦横センター
        bodyStyle={{
          height: '100%',
          padding: 24,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center', // 横方向中央
          justifyContent: 'space-between', // 上部にアイコン/タイトル、下部にボタン
          gap: 8,
          textAlign: 'center',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
          <div aria-hidden style={{ fontSize: 36, lineHeight: 1, color: 'var(--ant-color-primary)' }}>
            {icon}
          </div>
          <Title level={4} style={{ margin: 0 }}>{title}</Title>
        </div>

        <Paragraph
          style={{
            margin: 0,
            maxWidth: 260, // 中央視覚効果を高めるため幅をやや絞る
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap', // 1行に制限
          }}
          title={description}
        >
          {description}
        </Paragraph>

        <Button
          type="primary"
          style={{ width: BUTTON_WIDTH }} // ボタンも中央・固定幅
          onClick={(e) => {
            e.stopPropagation();
            handleNavigate();
          }}
          aria-label={`${title} へ移動`}
        >
          開く
        </Button>
      </Card>
    </Popover>
  );
};

const portalMenus: PortalCardProps[] = [
  {
    title: '帳簿作成',
    description: '各種帳簿の作成を行います。',
    detail:
      '工場日報や管理表などの帳簿作成とエクセル・PDFなどのエクスポートが可能です。テンプレートを使って入力を簡単に行えます。',
    icon: <BookOutlined />,
    link: ROUTER_PATHS.LEDGER_BOOK,
  },
  {
    title: '参謀 NAVI',
    description: 'AI アシスタントで業務を効率化します。',
    detail:
      '自然言語で質問すると、マニュアル検索、帳簿作成補助、データ要約、定型処理の自動化などを提案します。セキュリティ保護された内部データのみを利用します。',
    icon: <RobotOutlined />,
    link: ROUTER_PATHS.NAVI,
  },
  // {
  //   title: 'KPIダッシュボード',
  // description: '主要指標を可視化して状況を素早く把握。',
  // detail: '売上、コスト、在庫、進捗などカスタム可能なウィジェットで経営指標をリアルタイムに表示します。期間比較やドリルダウンが可能です。',
  //   icon: <DashboardOutlined />,
  //   link: ROUTER_PATHS.DASHBOARD,
  // },
  {
    title: 'マニュアル',
    description: '社内手順書・運用ガイドを参照できます。',
    detail:
      '部署別の手順書、FAQ、オンボーディング資料を検索できます。更新履歴と担当者情報も確認可能です。',
    icon: <FileTextOutlined />,
    link: ROUTER_PATHS.MANUAL_SEARCH,
  },
  {
    title: 'データベース',
    description: 'CSV アップロードや保存済みレコードの閲覧・管理を行います。',
    detail:
      'CSV のアップロード、保存データの検索・編集・エクスポートが可能です。データのインポート履歴やレコード管理を行えます。',
    icon: <CloudUploadOutlined />,
    link: ROUTER_PATHS.RECORD_LIST,
  },
  {
    title: '管理機能',
    description: 'システム設定や権限管理、運用パラメータを編集できます。',
    detail:
      'ユーザー権限の設定、システム構成、外部連携設定などの管理操作を行います。管理者向けの操作履歴やログも確認可能です。',
    icon: <SettingOutlined />,
    link: ROUTER_PATHS.SETTINGS,
  },
  {
    title: 'お知らせ',
    description: '最新のお知らせ・更新情報を確認。',
    detail:
      'システムメンテナンス情報、リリースノート、社内イベント、法令改正などの重要なお知らせを掲載します。',
    icon: <NotificationOutlined />,
    link: ROUTER_PATHS.NEWS,
  },
];

export const PortalPage: React.FC = () => {
  // 1) 明示的なリサイズ検知（本件の肝）
  const { width, isMobile } = useWindowSize();
  // 2) Ant Design のブレークポイント検知（補助的）
  const screens = Grid.useBreakpoint();

  // width を使うことで、リサイズ時に再レンダーが必ず走り、判定が追従します。
  const isCompact = isMobile || !screens.lg || width < 900;

  const introText = isCompact
    ? '社内ポータルです。必要な機能を選択してください。'
    : '社内ポータルへようこそ。下記のメニューから業務に必要な機能を選択してください。';

  return (
    <div style={{ padding: '32px 32px 48px' }}>
      <header style={{ maxWidth: 960, margin: '0 auto 32px', textAlign: 'center' }}>
        <Title level={2} style={{ marginBottom: 8 }}>社内ポータル</Title>
        <Text type="secondary">{introText}</Text>
      </header>

      <main style={{ maxWidth: 1280, margin: '0 auto' }}>
        <div
          aria-label="ポータルメニュー一覧"
          style={{
            display: 'grid',
            gap: 24,
            // **カード幅は常に固定**。最終行も中央寄せ。
            gridTemplateColumns: `repeat(auto-fit, ${CARD_WIDTH}px)`,
            justifyContent: 'center',
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
