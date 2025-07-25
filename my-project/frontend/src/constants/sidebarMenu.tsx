// サイドバー用定数・アイコン・ルーティング
import React from 'react';

// アイコン（Ant Design）
import {
    DashboardOutlined, // ダッシュボード
    TableOutlined, // 管理表
    ApartmentOutlined, // 工場管理
    FileTextOutlined, // 単価表
    FileAddOutlined, // 帳票作成
    FileDoneOutlined, // 工場帳簿
    BarChartOutlined, // データ分析
    TeamOutlined, // 顧客リスト
    CompassOutlined, // 参謀NAVI
    SettingOutlined, // 設定
    UserSwitchOutlined, // 管理者
    CloudUploadOutlined, // アップロード/レコード
    BookOutlined, // マニュアル
    SolutionOutlined, // 管理業務
} from '@ant-design/icons';

// ルーティング
import { Link } from 'react-router-dom';
import { ROUTER_PATHS } from './router';

// サイドバーのメニュー定義
export const SIDEBAR_MENU = [
    // ダッシュボード
    {
        key: 'dashboardGroup',
        icon: <DashboardOutlined />,
        label: 'ダッシュボード',
        children: [
            {
                key: ROUTER_PATHS.DASHBOARD,
                icon: <TableOutlined />,
                label: <Link to={ROUTER_PATHS.DASHBOARD}>管理表</Link>,
            },
            {
                key: ROUTER_PATHS.FACTORY,
                icon: <ApartmentOutlined />,
                label: <Link to={ROUTER_PATHS.FACTORY}>工場管理</Link>,
            },
            {
                key: ROUTER_PATHS.CUSTOMER_LIST,
                icon: <FileTextOutlined />,
                label: <Link to={ROUTER_PATHS.CUSTOMER_LIST}>顧客リスト</Link>,
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
        ],
    },
    // データ分析
    {
        key: 'analysis',
        icon: <BarChartOutlined />,
        label: 'データ分析',
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
    // 参謀NAVI
    {
        key: ROUTER_PATHS.NAVI,
        icon: <CompassOutlined />,
        label: <Link to={ROUTER_PATHS.NAVI}>参謀NAVI</Link>,
    },
    // データベース
    {
        key: 'database',
        icon: <CloudUploadOutlined />,
        label: 'データベース',
        children: [
            {
                key: ROUTER_PATHS.UPLOAD_PAGE,
                icon: <CloudUploadOutlined />,
                label: (
                    <Link to={ROUTER_PATHS.UPLOAD_PAGE}>CSVアップロード</Link>
                ),
            },
            {
                key: ROUTER_PATHS.RECORD_LIST,
                icon: <CloudUploadOutlined />,
                label: <Link to={ROUTER_PATHS.RECORD_LIST}>レコード一覧</Link>,
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
            },
        ],
    },
    // マニュアル
    {
        key: ROUTER_PATHS.MANUAL_SEARCH,
        icon: <BookOutlined />,
        label: <Link to={ROUTER_PATHS.MANUAL_SEARCH}>マニュアル一覧</Link>,
    },
];
