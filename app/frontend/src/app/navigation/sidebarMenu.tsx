// src/app/navigation/sidebarMenu.tsx
// サイドバー用定数・アイコン・ルーティング
import React from 'react';

// アイコン（Ant Design）
import {
    HomeOutlined, // ポータル
    DashboardOutlined, // ダッシュボード
    BarChartOutlined, // 売上分析
    BookOutlined, // 帳簿
    RobotOutlined, // AI
    FileTextOutlined, // マニュアル
    CloudUploadOutlined, // データベース
    SettingOutlined, // 設定
    FileSearchOutlined,
    NotificationOutlined,
    FileAddOutlined,
    SolutionOutlined,
    FileDoneOutlined,
    TeamOutlined,
    CompassOutlined,
    UserSwitchOutlined,
} from '@ant-design/icons';

// ルーティング
import { Link } from 'react-router-dom';
import { ROUTER_PATHS } from '@app/routes/routes';

// サイドバーのメニュー定義
export const SIDEBAR_MENU = [
    // ホーム（ポータル + お知らせ を統合）
    {
        key: 'home',
        icon: <DashboardOutlined />,
        label: 'ホーム',
        children: [
            {
                key: ROUTER_PATHS.PORTAL,
                icon: <DashboardOutlined />,
                label: <Link to={ROUTER_PATHS.PORTAL}>トップページ</Link>,
            },
            {
                key: ROUTER_PATHS.NEWS,
                icon: <NotificationOutlined />,
                label: <Link to={ROUTER_PATHS.NEWS}>お知らせ</Link>,
            },
        ],
    },
    // ダッシュボード
    {
        key: 'dashboardGroup',
        icon: <DashboardOutlined />,
        label: 'ダッシュボード',
        hidden: false,
        children: [
            {
                key: ROUTER_PATHS.DASHBOARD_UKEIRE,
                icon: <BarChartOutlined />,
                label: <Link to={ROUTER_PATHS.DASHBOARD_UKEIRE}>受入管理</Link>,
            },
            {
                key: ROUTER_PATHS.SALES_TREE,
                icon: <BarChartOutlined />,
                label: <Link to={ROUTER_PATHS.SALES_TREE}>営業・売上ツリー</Link>,
            },
            {
                key: ROUTER_PATHS.CUSTOMER_LIST,
                icon: <FileTextOutlined />,
                label: <Link to={ROUTER_PATHS.CUSTOMER_LIST}>顧客リスト</Link>,
                hidden: true,
            },
        ],
    },
    // 帳票作成
    {
        key: 'report',
        icon: <FileAddOutlined />,
        label: '帳票作成',
        children: [
            {
                key: ROUTER_PATHS.REPORT_MANAGE,
                icon: <SolutionOutlined />,
                label: <Link to={ROUTER_PATHS.REPORT_MANAGE}>管理業務</Link>,
            },
            {
                key: ROUTER_PATHS.REPORT_FACTORY,
                icon: <FileDoneOutlined />,
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
    // データ分析
    {
        key: 'analysis',
        icon: <BarChartOutlined />,
        label: 'データ分析',
        hidden: true,
        children: [
            {
                key: ROUTER_PATHS.ANALYSIS_CUSTOMERLIST,
                icon: <TeamOutlined />,
                label: (
                    <Link to={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}>
                        搬入顧客リストチェック
                    </Link>
                ),
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
            icon: <BookOutlined />,
            label: 'マニュアル',
            children: [
                {
                    key: `${ROUTER_PATHS.MANUALS}`,
                    icon: <BookOutlined />,
                    label: <Link to={ROUTER_PATHS.MANUALS}>全体検索</Link>,
                    hidden: true,
                },
                {
                    key: '/manuals/syogun',
                    icon: <BookOutlined />,
                    label: <Link to='/manuals/syogun'>将軍マニュアル一覧</Link>,
                },
            ],
        },
    // データベース
    {
        key: 'database',
        icon: <CloudUploadOutlined />,
        label: 'データベース',
        children: [
            {
                key: ROUTER_PATHS.DATASET_IMPORT,
                icon: <CloudUploadOutlined />,
                label: (
                    <Link to={ROUTER_PATHS.DATASET_IMPORT}>CSVインポート</Link>
                ),
            },
            {
                key: ROUTER_PATHS.RECORD_LIST,
                icon: <CloudUploadOutlined />,
                label: <Link to={ROUTER_PATHS.RECORD_LIST}>レコード一覧</Link>,
                hidden: true,
            },
        ],
    },

    // 管理機能
    {
        key: 'management',
        icon: <SettingOutlined />,
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
