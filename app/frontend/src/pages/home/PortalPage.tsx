// src/pages/portal/PortalPage.tsx
// シンプル & モダン見た目の“完全中央”カード。アクセシブル / 固定サイズ / レスポンシブグリッド。
// React + TypeScript / Ant Design v5 前提。

import React from 'react';
import {
  Card,
  Typography,
  Button,
  Popover,
  Alert,
  Modal,
  List,
  theme,
} from 'antd';
import {
  BookOutlined,
  DashboardOutlined,
  RobotOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  NotificationOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { ROUTER_PATHS } from '@/constants/router';
import { useWindowSize } from '@shared/hooks/ui';
import { ANT } from '@/shared/constants/breakpoints';
import './PortalPage.css';

const { Title, Paragraph, Text } = Typography;

const CARD_WIDTH = 320;
const CARD_HEIGHT = 208; // きっちり固定。中身は縦横センター配置。
const BUTTON_WIDTH = 160;
const BUTTON_HEIGHT = 36; // 画面サイズに依存しない固定高さ
const BUTTON_FONT_SIZE = 14; // 画面サイズに依存しない固定フォントサイズ

export interface PortalCardProps {
  title: string;
  description: string;
  // ホバーで表示する詳しい説明（省略可）
  detail?: string;
  icon: React.ReactNode;
  link: string;
  // 任意のアクセント色（例: '#52c41a'）
  color?: string;
  // ボタン幅を外から制御（単位: px）。未指定時はデフォルトを使用。
  buttonWidth?: number;
  // カード全体のスケール（1 = 100%）。PortalPage から渡す。
  cardScale?: number;
}

/** 単一責任：1メニューカードの表示と遷移のみ */
const PortalCard: React.FC<PortalCardProps> = ({
  title,
  description,
  icon,
  link,
  detail,
  color,
  buttonWidth,
  cardScale,
}) => {
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const accent = color ?? token.colorPrimary;
  // アクセントの淡色（アイコンプレート用）をグラデーションで生成
  const hexToRgba = (hex: string, alpha = 1) => {
    try {
      let c = hex.replace('#', '');
      if (c.length === 8) c = c.substring(0, 6);
      if (c.length === 3) c = c.split('').map((ch) => ch + ch).join('');
      const r = parseInt(c.substring(0, 2), 16);
      const g = parseInt(c.substring(2, 4), 16);
      const b = parseInt(c.substring(4, 6), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    } catch {
      return `rgba(0,0,0,${alpha})`;
    }
  };

  const getGradient = (hex: string) => {
    try {
      const stop1 = hexToRgba(hex, 0.18);
      const stop2 = hexToRgba(hex, 0.06);
      return `linear-gradient(135deg, ${stop1} 0%, ${stop2} 60%, transparent 100%)`;
    } catch {
      return token.colorPrimaryBg;
    }
  };

  const accentPlate = getGradient(accent);
  // 簡易的なコントラスト判定：背景色(accent)に対してテキストを白か黒で選ぶ
  const getReadableTextColor = (bg: string) => {
    try {
      const c = bg.replace('#', '');
      const r = parseInt(c.substring(0, 2), 16);
      const g = parseInt(c.substring(2, 4), 16);
      const b = parseInt(c.substring(4, 6), 16);
      // 相対的輝度の簡易判定
      const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      return luminance > 0.6 ? '#000000' : '#ffffff';
    } catch {
      return '#ffffff';
    }
  };
  const btnText = getReadableTextColor(accent);
  const appliedButtonWidth = buttonWidth ?? BUTTON_WIDTH;
  const scale = cardScale ?? 1;
  const appliedCardWidth = Math.round(CARD_WIDTH * scale);
  const appliedCardHeight = Math.round(CARD_HEIGHT * scale);
  const appliedButtonHeight = Math.round(BUTTON_HEIGHT * scale);
  const appliedButtonFontSize = Math.round(BUTTON_FONT_SIZE * scale);
  const appliedButtonWidthScaled = Math.round(appliedButtonWidth * scale);
  const appliedIconSize = Math.round(56 * scale);
  const appliedIconFontSize = Math.round(28 * scale);

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
      trigger={['hover']}
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
          width: appliedCardWidth,
          height: appliedCardHeight,
          borderRadius: 16,
          // 上辺にアクセントライン（モダンで控えめ）
          boxShadow: `inset 0 2px 0 0 ${accent}`,
          transition: 'transform 200ms ease, box-shadow 200ms ease',
        }}
        bodyStyle={{
          height: '100%',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center', // ← 縦方向も中央寄せ（“ど真ん中”）
          gap: 12 * scale,
          textAlign: 'center',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)';
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            `inset 0 2px 0 0 ${accent}, ${token.boxShadowSecondary}`;
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            `inset 0 2px 0 0 ${accent}`;
        }}
        onFocus={(e) => {
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            `inset 0 2px 0 0 ${accent}, 0 0 0 3px ${token.colorPrimaryBorder}`;
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            `inset 0 2px 0 0 ${accent}`;
        }}
      >
        {/* アイコン：円形の淡色プレートに収める */}
        <div
          aria-hidden
          style={{
            width: appliedIconSize,
            height: appliedIconSize,
            borderRadius: '50%',
              background: accentPlate,
              color: accent,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: appliedIconFontSize,
            lineHeight: 1,
          }}
        >
          {icon}
        </div>

        <Title level={4} style={{ margin: 0, lineHeight: 1.2 }}>
          {title}
        </Title>

        {/* 説明文：2行でクランプ、中央寄せ */}
        <Paragraph
          style={{
            margin: 0,
            maxWidth: 260,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            minHeight: '2.8em', // 2行相当で高さ安定
            color: token.colorTextSecondary,
          }}
          title={description}
        >
          {description}
        </Paragraph>

        <Button
          type="primary"
          size="middle"
          style={{
            width: appliedButtonWidthScaled,
            minWidth: appliedButtonWidthScaled,
            maxWidth: appliedButtonWidthScaled,
            height: appliedButtonHeight,
            lineHeight: `${appliedButtonHeight}px`,
            fontSize: appliedButtonFontSize,
            padding: 0,
            whiteSpace: 'nowrap',
            flex: '0 0 auto',
            alignSelf: 'center',
            background: accent,
            borderColor: 'transparent',
            color: btnText,
            backgroundImage: accentPlate,
            backgroundRepeat: 'no-repeat',
            backgroundSize: 'cover',
            boxShadow: 'none',
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-1px)';
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(0)';
          }}
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

/** メニュー定義（拡張・差し替え容易：OCP） */
// カラーパレット（カラー理論に基づくトライアド + 明暗バリエーション）
// 元の3色をベースに、ライト/ダークを追加して6色に拡張します。
// 各色は、UI上での用途（アイコンプレート / アクセントボタン等）を想定して選定しています。
const PALETTE = {
  BLUE: '#226cb6ff', // ベースブルー
  BLUE_DARK: '#22a114', // ダークブルー
  ORANGE: '#eb4848ff', // ベースオレンジ
  ORANGE_DARK: '#ecf023ff', // ダークオレンジ
  PURPLE: '#c6c08d', // ベースパープル
  PURPLE_DARK: '#555555', // ダークパープル
};

const portalMenus: PortalCardProps[] = [
  {
    title: 'ダッシュボード',
    description: '複数のダッシュボードをまとめて表示します。',
    detail:
      '工場別・顧客別・価格表などの管理ダッシュボードへアクセスできます。表示中のダッシュボードを切り替えて詳細を確認してください。',
    icon: <DashboardOutlined />,
    link: ROUTER_PATHS.DASHBOARD,
    color: PALETTE.BLUE_DARK,
  },
  {
    title: '帳簿作成',
    description: '各種帳簿の作成を行います。',
    detail:
      '工場日報や管理表などの帳簿作成とエクセル・PDFのエクスポートが可能です。テンプレートで入力を簡素化できます。',
    icon: <BookOutlined />,
    link: ROUTER_PATHS.REPORT_MANAGE,
    color: PALETTE.BLUE,
  },
  {
    title: '参謀 NAVI',
    description: 'AI アシスタントで業務を効率化します。',
    detail:
      '自然言語で質問 → マニュアル検索、帳簿補助、データ要約、定型処理の自動提案。内部データのみを安全に活用します。',
    icon: <RobotOutlined />,
    link: ROUTER_PATHS.NAVI,
    color: PALETTE.ORANGE,
  },
  {
    title: 'マニュアル',
    description: '社内手順書・運用ガイドを参照できます。',
    detail:
      '部署別の手順書、FAQ、オンボーディング資料を検索。更新履歴や担当者情報も確認できます。',
    icon: <FileTextOutlined />,
  link: ROUTER_PATHS.MANUALS,
    color: PALETTE.PURPLE,
  },
  {
    title: 'データベース',
    description: 'CSV アップロードや保存データの閲覧・管理。',
    detail:
      'CSVインポート、レコード検索・編集・エクスポート、インポート履歴のトラッキングを行えます。',
    icon: <CloudUploadOutlined />,
    link: ROUTER_PATHS.UPLOAD_PAGE,
    // 同一系統でも差し色としてダーク変種を交互に使用
    color: PALETTE.BLUE_DARK,
  },
  {
    title: '管理機能',
    description: 'システム設定や権限管理を行います。',
    detail:
      'ユーザー権限、システム構成、外部連携の設定。操作履歴やログの確認も可能です（管理者向け）。',
    icon: <SettingOutlined />,
    link: ROUTER_PATHS.SETTINGS,
    color: PALETTE.ORANGE_DARK,
  },
  {
    title: 'お知らせ',
    description: '最新のお知らせ・更新情報を確認。',
    detail:
      'メンテナンス情報、リリースノート、社内イベント、法令改正などを掲載します。',
    icon: <NotificationOutlined />,
    link: ROUTER_PATHS.NEWS,
    color: PALETTE.PURPLE_DARK,
  },
];

type Notice = {
  id: string;
  title: string;
  summary: string;
  detail: string;
  date: string;
};

export const PortalPage: React.FC = () => {
  const { width, isMobile } = useWindowSize(); // 明示的リサイズ検知（再レンダーで追従）
  const { token } = theme.useToken();

  const isCompact = isMobile || width < 900;

  // レスポンシブに関係なく全カードで同じボタン幅に統一する
  const unifiedButtonWidth = BUTTON_WIDTH;

  // カードスケール: ANT.xxl 以下では 0.9 倍にする
  const cardScale = width <= ANT.xxl ? 0.9 : 1;

  const introText = isCompact
    ? '社内ポータルです。必要な機能を選択してください。'
    : '社内ポータルへようこそ。下記メニューから業務に必要な機能を選択してください。';

  // --- 重要通知（サンプル） ---
  const sampleNotices: Notice[] = [
    {
      id: 'n1',
      title: 'システムメンテナンスのお知らせ',
      summary: '9/20 02:00-04:00 にシステムメンテナンスを実施します。',
      detail:
        'サービス安定化のため、上記時間帯でシステムメンテナンスを実施します。メンテナンス中は一部機能がご利用いただけません。',
      date: '2025-09-10',
    },
  ];

  const [notices] = React.useState<Notice[]>(sampleNotices);
  const [noticeVisible, setNoticeVisible] = React.useState<boolean>(true);
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

  type PortalHeroVars = React.CSSProperties & Record<
    '--portal-accent' | '--portal-hero-bg' | '--portal-hero-plate' | '--portal-text-secondary' | '--portal-border' | '--portal-shadow',
    string
  >;

  const heroVars: PortalHeroVars = {
    '--portal-accent': token.colorPrimary,
    '--portal-hero-bg': token.colorBgContainer,
    '--portal-hero-plate': token.colorFillQuaternary,
    '--portal-text-secondary': token.colorTextTertiary,
    '--portal-border': token.colorBorderSecondary,
    '--portal-shadow': token.boxShadowSecondary,
  };

  return (
    <div className="portal-page" style={{ minHeight: '100%' }}>
      <section className="portal-hero" style={heroVars}>
        <Title level={2} className="portal-title">
          社内ポータル
        </Title>
        <Text className="portal-subtitle">{introText}</Text>
      </section>

  <main style={{ width: '100%', maxWidth: 'none', margin: 0 }}>
        {/* 重要通知バナー */}
        {noticeVisible && notices.length > 0 && (
          <div style={{ width: '100%', margin: '0 0 24px 0' }}>
            <Alert
              type="warning"
              banner
              showIcon
              closable
              onClose={() => setNoticeVisible(false)}
              message={
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div>
                    <strong>{notices[0].title}</strong>
                    <div
                      style={{
                        fontSize: 12,
                        color: token.colorTextTertiary,
                      }}
                    >
                      {notices[0].summary}
                    </div>
                  </div>
                  <div>
                    <Button
                      size="small"
                      type="link"
                      onClick={() => openNoticeModal(notices[0])}
                      aria-label="重要通知の詳細を開く"
                    >
                      詳細
                    </Button>
                  </div>
                </div>
              }
            />
          </div>
        )}

        {/* メニュー：固定幅カードを中央寄せで折り返し
            レスポンシブ：利用可能幅に基づき列数を計算します。
            - 通常：利用可能幅に応じて列数を算出
            - 半画面（isCompact が真）では最大2列に制限する
        */}
        <div
          aria-label="ポータルメニュー一覧"
          style={{
            display: 'grid',
            columnGap: 24,
            rowGap: 24, // 画面サイズに関わらず縦の間隔を固定
            gridAutoRows: `${Math.round(CARD_HEIGHT * cardScale)}px`, // 各行の高さをカード固定高に合わせる
            // 利用可能幅に基づいて表示列数を調整します。
            // カード幅 + ギャップを考慮して列数を計算（最大 portalMenus.length）
            gridTemplateColumns: (() => {
              try {
                const containerPadding = 64; // 親左右パディング合計（32px 左右）
                const available = Math.max(0, width - containerPadding);
                const gap = 24;
                // 必要幅 per column
                const per = Math.round(CARD_WIDTH * cardScale) + gap;
                let cols = Math.floor((available + gap) / per);
                if (cols < 1) cols = 1;
                // compact（半画面等）では2列表示を優先する（ただし最大はメニュー数）
                if (isCompact) cols = Math.min(2, Math.max(1, cols));
                // 保険: 列数が多すぎる場合は最大3列、さらにメニュー数で制限
                cols = Math.min(cols, 3, portalMenus.length);
                return `repeat(${cols}, ${Math.round(CARD_WIDTH * cardScale)}px)`;
              } catch {
                return `repeat(auto-fit, ${Math.round(CARD_WIDTH * cardScale)}px)`;
              }
            })(),
            // カードを画面中央に寄せる
            justifyContent: 'center',
            alignItems: 'stretch',
          }}
        >
          {portalMenus.map((menu) => (
            <PortalCard key={menu.link} {...menu} buttonWidth={unifiedButtonWidth} cardScale={cardScale} />
          ))}
        </div>
      </main>

      {/* 通知一覧 / 詳細モーダル */}
      <Modal
        title={activeNotice?.title ?? '通知詳細'}
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
                onClick={() => openNoticeModal(item)}
                style={{ cursor: 'pointer' }}
              >
                <List.Item.Meta
                  title={item.title}
                  description={item.summary}
                />
              </List.Item>
            )}
          />
        )}
      </Modal>
    </div>
  );
};

export default PortalPage;
