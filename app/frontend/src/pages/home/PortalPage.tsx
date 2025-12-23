// src/pages/portal/PortalPage.tsx
// シンプル & モダン見た目の“完全中央”カード。アクセシブル / 固定サイズ / レスポンシブグリッド。
// React + TypeScript / Ant Design v5 前提。

import React from 'react';
import { Card, Typography, Button, Popover, Modal, List, theme } from 'antd';
import {
  BookOutlined,
  DashboardOutlined,
  RobotOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  NotificationOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
// CalendarCard removed: right column widgets trimmed
import { useNavigate } from 'react-router-dom';
import { ROUTER_PATHS } from '@app/routes/routes';
import { useResponsive } from '@/shared'; // responsive: flags
import ResponsiveNotice from '@/features/announcement-banner/ui/ResponsiveNotice';
import { useAuth } from '@features/authStatus';
import {
  useAnnouncementBannerViewModel,
  AnnouncementBanner,
} from '@features/announcements';
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
  // 狭い画面向けのコンパクトレイアウト（説明非表示、アイコン左寄せ、height 縮小）
  compactLayout?: boolean;
  // sm 未満でボタンを非表示にする指示
  hideButton?: boolean;
  // sm 未満で小さなボタンを表示する（ボタンを非表示にする代わりに小さいものを右側に表示）
  smallButton?: boolean;
  // 高さのみをスケールする（例: sm 未満で 0.9 を渡す）
  heightScale?: number;
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
  compactLayout,
  hideButton,
  smallButton,
  heightScale,
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
  // compactLayout の場合は高さを縮める
  const COMPACT_CARD_HEIGHT = 100; // compact 時のベース高さ（モバイル向けに縮小して縦詰め）
  const appliedCardHeight = Math.round((compactLayout ? COMPACT_CARD_HEIGHT : CARD_HEIGHT) * scale);
  const appliedButtonHeight = Math.round(BUTTON_HEIGHT * scale);
  const appliedButtonFontSize = Math.round(BUTTON_FONT_SIZE * scale);
  const appliedButtonWidthScaled = Math.round(appliedButtonWidth * scale);
  const appliedIconSize = Math.round((compactLayout ? 40 : 56) * scale);
  const appliedIconFontSize = Math.round((compactLayout ? 20 : 28) * scale);

  // smallButton: show a compact button on the right for very small screens
  const isSmallButton = !!smallButton;
  // If button is hidden (hideButton true and not smallButton), use the aggressive compact scale.
  // If smallButton is true, use a mild compact scale so contents still fit.
  const SMALL_SCREEN_SCALE = hideButton && !isSmallButton ? 0.7 : (isSmallButton ? 0.82 : 1);
  const hs = heightScale ?? 1;
  const finalCardHeight = Math.round(appliedCardHeight * SMALL_SCREEN_SCALE * hs);
  const finalIconSize = Math.round(appliedIconSize * SMALL_SCREEN_SCALE);
  const finalIconFontSize = Math.round(appliedIconFontSize * SMALL_SCREEN_SCALE);
  const finalButtonHeight = Math.round(appliedButtonHeight * SMALL_SCREEN_SCALE);
  const finalButtonWidth = Math.round(appliedButtonWidthScaled * SMALL_SCREEN_SCALE);

  const handleNavigate = () => navigate(link);
  const handleKeyDown: React.KeyboardEventHandler<HTMLDivElement> = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleNavigate();
    }
  };

  const isButtonHidden = !!hideButton && !isSmallButton;

  // Precompute title font-size to avoid complex inline ternaries that broke JSX parsing
  // For small screens, prefer a smooth clamp so the title scales down gracefully.
  const titleFontSize = isSmallButton
    ? `clamp(14px, 3.6vw, 18px)`
    : (hideButton
      ? '18px'
      : (compactLayout
        ? `clamp(${Math.max(12, Math.round(appliedButtonFontSize * SMALL_SCREEN_SCALE))}px, 3.2vw, ${Math.round(appliedButtonFontSize * SMALL_SCREEN_SCALE) + 6}px)`
        : `clamp(${Math.max(12, Math.round((appliedButtonFontSize + 2) * SMALL_SCREEN_SCALE))}px, 2.4vw, ${Math.round((appliedButtonFontSize + 6) * SMALL_SCREEN_SCALE)}px)`));

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
          width: '100%', // follow grid cell width
          height: finalCardHeight,
          borderRadius: 16,
          // 上辺にアクセントライン（sm未満では太く表示）
          boxShadow: hideButton ? `inset 0 4px 0 0 ${accent}` : `inset 0 2px 0 0 ${accent}`,
          transition: 'transform 200ms ease, box-shadow 200ms ease',
        }}
        styles={{
          body: {
            height: '100%',
            // モバイルではパディングを大幅に削減
            padding: compactLayout ? '1px 1px' : (isButtonHidden ? '8px 12px' : '12px 12px'),
            display: 'flex',
            // For small-screen cases (either smallButton or button-hidden), use horizontal layout
            flexDirection: (isButtonHidden || isSmallButton) ? 'row' : (compactLayout ? 'row' : 'column'),
            // center items vertically in row layout
            alignItems: 'center',
            // when we have a small button on the right, space-between ensures it sits to the far right
            justifyContent: isSmallButton ? 'space-between' : (isButtonHidden ? 'flex-start' : (compactLayout ? 'space-between' : 'center')),
            gap: compactLayout ? 6 * scale : 8 * scale,
            // text should be left-aligned when it's to the right of the icon
            textAlign: isButtonHidden ? 'left' : (compactLayout ? 'left' : 'center'),
          },
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-2px)';
          // lift above neighbors while hovered to avoid visual clipping
          (e.currentTarget as HTMLDivElement).style.zIndex = '2';
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            hideButton
              ? `inset 0 4px 0 0 ${accent}, ${token.boxShadowSecondary}`
              : `inset 0 2px 0 0 ${accent}, ${token.boxShadowSecondary}`;
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.transform = 'translateY(0)';
          (e.currentTarget as HTMLDivElement).style.zIndex = '0';
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            hideButton ? `inset 0 4px 0 0 ${accent}` : `inset 0 2px 0 0 ${accent}`;
        }}
        onFocus={(e) => {
          // make sure focused card is visually on top for keyboard users
          (e.currentTarget as HTMLDivElement).style.zIndex = '2';
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            hideButton
              ? `inset 0 4px 0 0 ${accent}, 0 0 0 3px ${token.colorPrimaryBorder}`
              : `inset 0 2px 0 0 ${accent}, 0 0 0 3px ${token.colorPrimaryBorder}`;
        }}
        onBlur={(e) => {
          (e.currentTarget as HTMLDivElement).style.zIndex = '0';
          (e.currentTarget as HTMLDivElement).style.boxShadow =
            hideButton ? `inset 0 4px 0 0 ${accent}` : `inset 0 2px 0 0 ${accent}`;
        }}
        >
        {/* アイコン */}
        <div
          aria-hidden
            style={{
            width: finalIconSize,
            height: finalIconSize,
            borderRadius: compactLayout ? 8 : '50%',
            background: accentPlate,
            color: accent,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            // fixed icon font size so it doesn't shrink unexpectedly on small screens
            fontSize: `${finalIconFontSize}px`,
            lineHeight: 1,
            flex: '0 0 auto',
            // add right margin when icon is left of text (compact or button-hidden)
            marginRight: (compactLayout || isButtonHidden) ? 12 : 0,
          }}
        >
          {icon}
        </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: (isButtonHidden || isSmallButton) ? 'flex-start' : (compactLayout ? 'flex-start' : 'center'), flex: (isButtonHidden || isSmallButton) ? '1 1 auto' : (hideButton ? 1.4 : 1) }}>
            <div style={{ maxWidth: isSmallButton ? 180 : 260 }}>
              <Title level={4} style={{
                margin: 0,
                lineHeight: 1.2,
                textAlign: isButtonHidden ? 'left' : undefined,
                fontSize: titleFontSize,
                fontWeight: (isButtonHidden || isSmallButton) ? 600 : undefined,
              }}>
                {title}
              </Title>
            </div>
          {/* sm未満では説明を非表示（タイトルを大きめに表示） */}
          {!isButtonHidden && !isSmallButton && (
            <Paragraph style={{
              margin: 0,
              maxWidth: isButtonHidden ? '100%' : 260,
              display: '-webkit-box',
              WebkitLineClamp: compactLayout ? 1 : 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              minHeight: compactLayout ? '1.4em' : '2.8em',
              color: token.colorTextSecondary,
              textAlign: isButtonHidden ? 'left' : undefined,
              // description also scales smoothly; enlarge on very small screens for readability
              fontSize: hideButton ? `clamp(12px, 2.6vw, 14px)` : `clamp(${Math.max(10, Math.round(12 * SMALL_SCREEN_SCALE))}px, 2.2vw, ${Math.round(14 * SMALL_SCREEN_SCALE)}px)`,
            }}
              title={description}
            >
              {description}
            </Paragraph>
          )}
        </div>

        {/* Render a button when not explicitly hidden. If isSmallButton is true, render a compact variant */}
        {!isButtonHidden && (
          <Button
          type="primary"
          size="middle"
          style={{
            width: isSmallButton ? Math.round((buttonWidth ?? BUTTON_WIDTH) * 0.5) : finalButtonWidth,
            minWidth: isSmallButton ? Math.round((buttonWidth ?? BUTTON_WIDTH) * 0.5) : finalButtonWidth,
            maxWidth: isSmallButton ? Math.round((buttonWidth ?? BUTTON_WIDTH) * 0.5) : finalButtonWidth,
            height: isSmallButton ? Math.round(BUTTON_HEIGHT * 0.78) : finalButtonHeight,
            lineHeight: `${isSmallButton ? Math.round(BUTTON_HEIGHT * 0.78) : finalButtonHeight}px`,
            // compact button uses a smaller fixed font
            fontSize: isSmallButton ? '12px' : `clamp(${Math.max(10, Math.round((appliedButtonFontSize - 2) * SMALL_SCREEN_SCALE))}px, 1.6vw, ${Math.round(appliedButtonFontSize * SMALL_SCREEN_SCALE)}px)`,
            padding: 0,
            whiteSpace: 'nowrap',
            flex: '0 0 auto',
            alignSelf: 'center',
            backgroundColor: accent,
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
        )}
      </Card>
    </Popover>
  );
};

/** メニュー定義（拡張・差し替え容易：OCP） */
// カラーパレット（8色 - 各カード専用の色）
// モダンで洗練された配色、視認性とアクセシビリティを考慮
const PALETTE = {
  OCEAN: '#0284C7',   // オーシャンブルー - ダッシュボード（メインカラー）
  LAVENDER: '#C4B5FD',// ラベンダー - アナリティクス（少し淡めの紫）
  MINT: '#10B981',    // ミントグリーン - 帳簿作成（爽やかな緑）
  CORAL: '#FB7185',   // コーラルピンク - 参謀 NAVI（柔らかいコーラル）
  GOLD: '#FBBF24',    // ゴールド - マニュアル（アクセント用の黄）
  PURPLE: '#6366F1',  // ロイヤルパープル - データベース（濃いめの青紫）
  CYAN: '#06B6D4',    // シアン - 管理機能（すっきりしたシアン）
  GRAY: '#6B7280',    // グレー - お知らせ（中間グレー）
};

const portalMenus: PortalCardProps[] = [
  {
    title: 'ダッシュボード',
    description: '複数のダッシュボードをまとめて表示します。',
    detail:
      '工場別・顧客別・価格表などの管理ダッシュボードへアクセスできます。表示中のダッシュボードを切り替えて詳細を確認してください。',
    icon: <DashboardOutlined />,
    link: ROUTER_PATHS.DASHBOARD_UKEIRE,
    color: PALETTE.OCEAN,
  },
  {
    title: 'アナリティクス',
    description: '売上・顧客データの多角的な分析を行います。',
    detail:
      '営業・売上ツリーや顧客リスト分析など、データに基づく洞察を得られます。経営判断や営業戦略の立案をサポートします。',
    icon: <BarChartOutlined />,
    link: ROUTER_PATHS.SALES_TREE,
    color: PALETTE.LAVENDER,
  },
  {
    title: '帳簿作成',
    description: '各種帳簿の作成を行います。',
    detail:
      '工場日報や管理表などの帳簿作成とエクセル・PDFのエクスポートが可能です。テンプレートで入力を簡素化できます。',
    icon: <BookOutlined />,
    link: ROUTER_PATHS.REPORT_MANAGE,
    color: PALETTE.MINT,
  },
  {
    title: '参謀 NAVI',
    description: 'AI アシスタントで業務を効率化します。',
    detail:
      '自然言語で質問 → マニュアル検索、帳簿補助、データ要約、定型処理の自動提案。内部データのみを安全に活用します。',
    icon: <RobotOutlined />,
    link: ROUTER_PATHS.NAVI,
    color: PALETTE.CORAL,
  },
  {
    title: 'マニュアル',
    description: '社内手順書・運用ガイドを参照できます。',
    detail:
      '部署別の手順書、FAQ、オンボーディング資料を検索。更新履歴や担当者情報も確認できます。',
    icon: <FileTextOutlined />,
  link: ROUTER_PATHS.MANUALS,
    color: PALETTE.GOLD,
  },
  {
    title: 'データベース',
    description: 'データセットのインポートや保存データの閲覧・管理。',
    detail:
      'データセットインポート、レコード検索・編集・エクスポート、インポート履歴のトラッキングを行えます。',
    icon: <CloudUploadOutlined />,
    link: ROUTER_PATHS.DATASET_IMPORT,
    color: PALETTE.PURPLE,
  },
  {
    title: '管理機能',
    description: 'システム設定や権限管理を行います。',
    detail:
      'ユーザー権限、システム構成、外部連携の設定。操作履歴やログの確認も可能です（管理者向け）。',
    icon: <SettingOutlined />,
    link: ROUTER_PATHS.SETTINGS,
    color: PALETTE.CYAN,
  },
  {
    title: 'お知らせ',
    description: '最新のお知らせ・更新情報を確認。',
    detail:
      'メンテナンス情報、リリースノート、社内イベント、法令改正などを掲載します。',
    icon: <NotificationOutlined />,
    link: ROUTER_PATHS.NEWS,
    color: PALETTE.GRAY,
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
  // responsive: useResponsive(flags)
  const { flags } = useResponsive();
  const { token } = theme.useToken();
  const navigate = useNavigate();

  // ユーザーキーを取得（未ログイン時は"local"）
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';

  // お知らせバナー用ViewModel
  const {
    announcement: bannerAnnouncement,
    onAcknowledge: onBannerAcknowledge,
  } = useAnnouncementBannerViewModel(userKey);

  // responsive: 3段階判定ヘルパー（Mobile/Tablet/Desktop）
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile;    // ≤767px
    if (flags.isTablet) return tablet;    // 768-1280px
    return desktop;                        // ≥1281px
  };

  // responsive: isCompact logic (Mobile | Tablet)
  const isCompact = flags.isMobile || flags.isTablet;

  // responsive: narrow判定 (Mobile only)
  const isNarrow = flags.isMobile;

  // responsive: isXs (width < 640px)
  const isXs = flags.isXs;

  // responsive: カードスケール
  const cardScale = pickByDevice(0.9, 0.9, 1);

  // レスポンシブに関係なく全カードで同じボタン幅に統一する
  const unifiedButtonWidth = BUTTON_WIDTH;

  // カード間のギャップ（行間・列間）を一元管理
  // モバイルは0px、Tablet/Desktopは1px
  const CARD_COLUMN_GAP = pickByDevice(0, 1, 1);
  const CARD_ROW_GAP = pickByDevice(0, 1, 1);

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
  // デフォルトでトップページの重要通知バナーは非表示にする
  // ここを切り替えて、通知を表示するか制御する
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

  // (weather sample removed)

  // Right column widgets removed. Keep page minimal.

  return (
    <div className="portal-page" style={{ minHeight: '100%' }}>
      <section className="portal-hero" style={heroVars}>
        <Title level={2} className="portal-title">
          参謀くん-社内ポータル
        </Title>
  {!isXs && <Text className="portal-subtitle">{introText}</Text>}
      </section>

      {/* 2カラムレイアウト: 左=カード群, 右=ウィジェット群 */}
      <main style={{ width: '100%', maxWidth: 'none', margin: 0 }}>
        {/* お知らせバナー（重要通知） */}
        {bannerAnnouncement && (
          <div style={{ width: '100%', margin: '0 0 16px 0', padding: '0 16px' }}>
            <AnnouncementBanner
              announcement={bannerAnnouncement}
              onClose={onBannerAcknowledge}
              onAcknowledge={onBannerAcknowledge}
              onNavigateToDetail={() => navigate(`/news/${bannerAnnouncement.id}`)}
            />
          </div>
        )}
        {/* 重要通知バナー */}
        {noticeVisible && notices.length > 0 && (
          <div style={{ width: '100%', margin: '0 0 24px 0' }}>
            <ResponsiveNotice
              title={notices[0].title}
              description={notices[0].summary}
              detailContent={
                <div>
                  <div style={{ marginBottom: 8, color: token.colorTextTertiary }}>
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

        {/* メニュー：固定幅カードを左カラムに表示（中央寄せ）
            レスポンシブ：利用可能幅に基づき列数を計算します。
            - 通常：利用可能幅に応じて列数を算出
            - 半画面（isCompact が真）では最大2列に制限する
        */}
  <div style={{ display: 'flex', gap: CARD_COLUMN_GAP, alignItems: 'flex-start' }}>
          {/* Left column: header + portal cards (keeps previous grid behavior) */}
          <div style={{ flex: '1 1 0', display: 'flex', flexDirection: 'column', gap: CARD_ROW_GAP }}>
            <div
              aria-label="ポータルメニュー一覧"
              style={{
                display: 'grid',
                // responsive: columnGap/rowGap - 一元管理された定数を使用
                columnGap: CARD_COLUMN_GAP,
                rowGap: CARD_ROW_GAP,
                // responsive: gridAutoRows
                // Use minmax(..., auto) so rows can grow if a card becomes taller (prevents overlap)
                // Lower the mobile minimum so cards sit closer vertically.
                gridAutoRows: `minmax(${Math.round(pickByDevice(64, 120, CARD_HEIGHT) * cardScale)}px, auto)`,
                // responsive: gridTemplateColumns (Mobile: 1col, Tablet: 2-3col auto-fit, Desktop: max 3col)
                gridTemplateColumns: flags.isMobile
                  ? 'repeat(1, 1fr)'
                  : flags.isDesktop  // ≥1281px: 最大3列に制限
                  ? `repeat(auto-fit, minmax(${Math.round(CARD_WIDTH * cardScale)}px, calc(100% / 3 - ${CARD_COLUMN_GAP}px)))`
                  : `repeat(auto-fit, minmax(${Math.round(CARD_WIDTH * cardScale)}px, 1fr))`,  // 768-1280px: auto-fit
              justifyContent: 'center',
              alignItems: 'stretch',
            }}
          >
            {portalMenus
              // トップページでは「お知らせ」カードは表示しない
              .filter((m) => m.link !== ROUTER_PATHS.NEWS && m.title !== 'お知らせ')
              .map((menu) => (
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

          {/* Right column removed: single-column layout for portal cards */}
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
                key={item.title + item.date}
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
