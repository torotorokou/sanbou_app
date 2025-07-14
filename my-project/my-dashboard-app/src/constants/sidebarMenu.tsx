// src/constants/sidebarMenu.tsx
import React from 'react';
import {
    DashboardOutlined,
    TableOutlined,
    ApartmentOutlined,
    FileTextOutlined,
    FileAddOutlined,
    FileDoneOutlined,
    BarChartOutlined,
    TeamOutlined,
    CompassOutlined,
    SettingOutlined,
    UserSwitchOutlined,
    CloudUploadOutlined,
    BookOutlined,
    SolutionOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { ROUTER_PATHS } from './router';

export const SIDEBAR_MENU = [
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
                key: ROUTER_PATHS.PRICING,
                icon: <FileTextOutlined />,
                label: <Link to={ROUTER_PATHS.PRICING}>単価表</Link>,
            },
        ],
    },
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
    {
        key: ROUTER_PATHS.NAVI,
        icon: <CompassOutlined />,
        label: <Link to={ROUTER_PATHS.NAVI}>参謀NAVI</Link>,
    },
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
    {
        key: ROUTER_PATHS.UPLOAD,
        icon: <CloudUploadOutlined />,
        label: <Link to={ROUTER_PATHS.UPLOAD}>データアップロード</Link>,
    },
    {
        key: ROUTER_PATHS.MANUAL_SEARCH,
        icon: <BookOutlined />,
        label: <Link to={ROUTER_PATHS.MANUAL_SEARCH}>マニュアル一覧</Link>,
    },
];
