// src/app/navigation/sidebarMenu.tsx
// サイドバー用定数・アイコン・ルーティング
import React from 'react';

// アイコン（Ant Design）
import {
  HomeOutlined, // ホーム
  DashboardOutlined, // ダッシュボード
  LineChartOutlined, // アナリティクス
  BookOutlined, // 帳簿・マニュアル
  FileTextOutlined, // 文書
  DatabaseOutlined, // データベース
  SettingOutlined, // 設定
  SolutionOutlined, // ソリューション
  TeamOutlined, // チーム・顧客
  CompassOutlined, // ナビゲーション
  UserSwitchOutlined, // ユーザー管理
  InboxOutlined, // 受入
  FundOutlined, // 売上ツリー
  UserDeleteOutlined, // 顧客チェック
  ContainerOutlined, // レポート
  ProfileOutlined, // 工場帳簿
  ReadOutlined, // マニュアル
  UploadOutlined, // アップロード
  UnorderedListOutlined, // リスト
  ControlOutlined, // 管理機能
} from '@ant-design/icons';

// ルーティング
import { Link } from 'react-router-dom';
import { ROUTER_PATHS } from '@app/routes/routes';
import { NewsMenuLabel, NewsMenuIcon } from '@features/announcements';

// サイドバーのメニュー定義
export const SIDEBAR_MENU = [
  // ホーム（ポータル + お知らせ を統合）
  {
    key: 'home',
    icon: <HomeOutlined />,
    label: 'ホーム',
    children: [
      {
        key: ROUTER_PATHS.PORTAL,
        icon: <HomeOutlined />,
        label: <Link to={ROUTER_PATHS.PORTAL}>トップページ</Link>,
      },
      {
        key: ROUTER_PATHS.NEWS,
        icon: <NewsMenuIcon />,
        label: <NewsMenuLabel />,
      },
    ],
  },
  // ダッシュボード
  {
    key: 'dashboardGroup',
    icon: <DashboardOutlined />,
    label: '速報ダッシュボード',
    hidden: false,
    children: [
      {
        key: ROUTER_PATHS.DASHBOARD_UKEIRE,
        icon: <InboxOutlined />,
        label: <Link to={ROUTER_PATHS.DASHBOARD_UKEIRE}>受入管理</Link>,
      },
      {
        key: ROUTER_PATHS.CUSTOMER_LIST,
        icon: <TeamOutlined />,
        label: <Link to={ROUTER_PATHS.CUSTOMER_LIST}>顧客リスト</Link>,
        hidden: true,
      },
    ],
  },
  // アナリティクス
  {
    key: 'analytics',
    icon: <LineChartOutlined />,
    label: 'アナリティクス',
    hidden: false,
    children: [
      {
        key: ROUTER_PATHS.SALES_TREE,
        icon: <FundOutlined />,
        label: <Link to={ROUTER_PATHS.SALES_TREE}>営業・売上ツリー</Link>,
      },
      {
        key: ROUTER_PATHS.ANALYSIS_CUSTOMERLIST,
        icon: <UserDeleteOutlined />,
        label: <Link to={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}>搬入なし顧客チェック</Link>,
      },
    ],
  },
  // 帳票作成
  {
    key: 'report',
    icon: <ContainerOutlined />,
    label: '帳票作成',
    children: [
      {
        key: ROUTER_PATHS.REPORT_MANAGE,
        icon: <SolutionOutlined />,
        label: <Link to={ROUTER_PATHS.REPORT_MANAGE}>管理業務</Link>,
      },
      {
        key: ROUTER_PATHS.REPORT_FACTORY,
        icon: <ProfileOutlined />,
        label: <Link to={ROUTER_PATHS.REPORT_FACTORY}>工場帳簿</Link>,
      },
      {
        key: ROUTER_PATHS.LEDGER_BOOK,
        icon: <BookOutlined />,
        label: <Link to={ROUTER_PATHS.LEDGER_BOOK}>帳簿</Link>,
        hidden: true,
      },
    ],
  },
  // 参謀NAVI（親はラベルのみ、子にリンクを持たせる）
  {
    key: 'navi',
    icon: <CompassOutlined />,
    label: '参謀NAVI',
    children: [
      {
        key: ROUTER_PATHS.NAVI,
        icon: <CompassOutlined />,
        label: <Link to={ROUTER_PATHS.NAVI}>SOLVEST成田工場</Link>,
      },
    ],
  },
  // マニュアル（親メニュー化：子に既存のマニュアル一覧を置く）
  {
    key: 'manual',
    icon: <ReadOutlined />,
    label: 'マニュアル',
    children: [
      {
        key: `${ROUTER_PATHS.MANUALS}`,
        icon: <FileTextOutlined />,
        label: <Link to={ROUTER_PATHS.MANUALS}>全体検索</Link>,
        hidden: true,
      },
      {
        key: '/manuals/shogun',
        icon: <BookOutlined />,
        label: <Link to="/manuals/shogun">将軍マニュアル一覧</Link>,
      },
    ],
  },
  // データベース
  {
    key: 'database',
    icon: <DatabaseOutlined />,
    label: 'データベース',
    children: [
      {
        key: ROUTER_PATHS.DATASET_IMPORT,
        icon: <UploadOutlined />,
        label: <Link to={ROUTER_PATHS.DATASET_IMPORT}>CSVインポート</Link>,
      },
      {
        key: ROUTER_PATHS.RECORD_LIST,
        icon: <UnorderedListOutlined />,
        label: <Link to={ROUTER_PATHS.RECORD_LIST}>レコード一覧</Link>,
        hidden: true,
      },
      {
        key: ROUTER_PATHS.RESERVATION_DAILY,
        icon: <FileTextOutlined />,
        label: <Link to={ROUTER_PATHS.RESERVATION_DAILY}>予約表</Link>,
      },
    ],
  },

  // 管理機能
  {
    key: 'management',
    icon: <ControlOutlined />,
    label: '管理機能',
    children: [
      {
        key: ROUTER_PATHS.SETTINGS,
        icon: <SettingOutlined />,
        label: <Link to={ROUTER_PATHS.SETTINGS}>設定</Link>,
      },
      {
        key: ROUTER_PATHS.ADMIN,
        icon: <UserSwitchOutlined />,
        label: <Link to={ROUTER_PATHS.ADMIN}>管理者メニュー</Link>,
        hidden: true,
      },
    ],
  },
];
